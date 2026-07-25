#!/usr/bin/env python3
"""Run every repository test file, each in its own process.

Discovery covers services, canonical skills, and automation. Each child receives a
sanitized Git environment and a fresh metadata-free projection outside every existing
repository's discovery path. Subprocess-per-file keeps hyphenated folders
importable-free and any test crash isolated. This is not a sandbox against deliberate
absolute paths. Exit 0 only if every file passes.
"""
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEST_GLOBS = (
    "services/*/tests/test_*.py",
    "skills/*/tests/test_*.py",
    "automation/**/tests/test_*.py",
)
GIT_BOUNDARY_MARKER = "AgentFold isolated test view; not a Git repository.\n"
SAFE_GIT_BEHAVIOR_VARIABLES = frozenset(
    (
        "GIT_AUTHOR_DATE",
        "GIT_AUTHOR_EMAIL",
        "GIT_AUTHOR_NAME",
        "GIT_COMMITTER_DATE",
        "GIT_COMMITTER_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_TERMINAL_PROMPT",
    )
)
GIT_IDENTITY_CONFIG = (
    ("user.name", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"),
    ("user.email", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"),
)
REAL_GIT_ENVIRONMENT = "AGENTFOLD_TEST_REAL_GIT"


def git_local_environment_names():
    """Return every environment variable Git treats as repository-local."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--local-env-vars"],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
    except OSError as error:
        raise RuntimeError(
            "could not discover Git local environment variables"
        ) from error
    if result.returncode:
        detail = result.stderr.strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(
            f"could not discover Git local environment variables{suffix}"
        )
    names = tuple(name for name in result.stdout.splitlines() if name)
    if not names:
        raise RuntimeError("Git local environment variable discovery was empty")
    return names


def isolated_test_environment(parent_environment=None):
    """Copy an environment without pointers into the invoking Git repository."""
    child_environment = dict(
        os.environ if parent_environment is None else parent_environment
    )
    safe_behavior = {
        name: child_environment[name]
        for name in SAFE_GIT_BEHAVIOR_VARIABLES
        if name in child_environment
    }
    discovered = set(git_local_environment_names())
    discovered.update(name for name in child_environment if name.startswith("GIT_"))
    for name in discovered:
        child_environment.pop(name, None)
    child_environment.update(safe_behavior)
    return child_environment


def configured_git_identity(parent_environment=None):
    """Resolve safe identity values before removing caller Git configuration."""
    parent_environment = (
        os.environ if parent_environment is None else parent_environment
    )
    identity = {}
    for key, author_name, committer_name in GIT_IDENTITY_CONFIG:
        result = subprocess.run(
            ["git", "config", "--get", key],
            cwd=REPO,
            env=parent_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if result.returncode == 1:
            continue
        if result.returncode:
            detail = result.stderr.strip()
            suffix = f": {detail}" if detail else ""
            raise RuntimeError(f"could not resolve Git identity {key}{suffix}")
        value = result.stdout.rstrip("\n")
        if value:
            identity[author_name] = value
            identity[committer_name] = value
    return identity


def validate_scratch_root(scratch_root, child_environment):
    """Fail closed unless Git cannot discover a repository from the scratch root."""
    if os.pathsep in str(scratch_root):
        raise RuntimeError(
            "test scratch path cannot be represented as a Git discovery ceiling"
        )
    if scratch_root == REPO or REPO in scratch_root.parents:
        raise RuntimeError("test scratch directory must be outside the repository")
    check_environment = dict(child_environment)
    check_environment["LC_ALL"] = "C"
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=scratch_root,
        env=check_environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode == 0:
        raise RuntimeError("test scratch directory must not discover a Git repository")
    if result.returncode != 128 or "not a git repository" not in result.stderr:
        raise RuntimeError("could not verify the test scratch Git boundary")


def repository_view_paths(child_environment, repository=None):
    """List tracked and non-ignored untracked paths in the current working tree."""
    repository = REPO if repository is None else Path(repository)
    result = subprocess.run(
        [
            "git",
            "-c",
            f"core.excludesFile={os.devnull}",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        cwd=repository,
        env=child_environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        detail = os.fsdecode(result.stderr).strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"could not enumerate the repository test view{suffix}")
    return tuple(
        Path(os.fsdecode(raw_path))
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    )


def path_crosses_symlink(path, repository=None):
    """Return whether a repository path is or descends through a symlink."""
    repository = (REPO if repository is None else Path(repository)).absolute()
    relative_path = Path(path).absolute().relative_to(repository)
    current = repository
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def repository_test_files(repository=None):
    """Discover repository tests without following symlinked paths."""
    repository = REPO if repository is None else Path(repository)
    discovered = {
        test
        for pattern in TEST_GLOBS
        for test in repository.glob(pattern)
    }
    return tuple(
        sorted(
            test
            for test in discovered
            if not path_crosses_symlink(test, repository)
        )
    )


def test_support_paths(test_files, repository=None):
    """Include ignored sibling modules and fixtures without following symlinks."""
    repository = (REPO if repository is None else Path(repository)).absolute()
    support_paths = set()
    for parent in sorted({test.parent for test in test_files}):
        for current_root, directory_names, file_names in os.walk(
            str(parent),
            followlinks=False,
        ):
            current = Path(current_root)
            directory_names[:] = [
                name for name in directory_names if name.casefold() != ".git"
            ]
            for directory_name in tuple(directory_names):
                directory = current / directory_name
                if directory.is_symlink():
                    support_paths.add(directory.relative_to(repository))
                    directory_names.remove(directory_name)
            for file_name in file_names:
                if file_name.casefold() == ".git":
                    continue
                support_paths.add((current / file_name).relative_to(repository))
    return tuple(sorted(support_paths))


def reject_projected_symlink_traversal(destination, relative_path):
    """Fail before a later path can write through a projected directory symlink."""
    current = destination
    for part in relative_path.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(
                f"repository test-view path traversed a symlink: {relative_path}"
            )


def install_isolated_git_wrapper(scratch_root, child_environment):
    """Put Git behind a config-isolated wrapper without changing other tools' HOME."""
    git_executable = child_environment.get(REAL_GIT_ENVIRONMENT)
    if git_executable is None:
        git_executable = shutil.which(
            "git",
            path=child_environment.get("PATH"),
        )
    if (
        not git_executable
        or not Path(git_executable).is_file()
        or not os.access(git_executable, os.X_OK)
    ):
        raise RuntimeError("could not locate Git for the isolated test environment")
    git_executable = str(Path(git_executable).resolve())
    wrapper_directory = scratch_root / "git-wrapper"
    isolated_home = scratch_root / "git-home"
    isolated_xdg_config = scratch_root / "git-xdg-config"
    wrapper_directory.mkdir(parents=True)
    isolated_home.mkdir()
    isolated_xdg_config.mkdir()
    wrapper = wrapper_directory / "git"
    wrapper.write_text(
        "#!/bin/sh\n"
        f"HOME={shlex.quote(str(isolated_home))} "
        f"XDG_CONFIG_HOME={shlex.quote(str(isolated_xdg_config))} "
        "GIT_CONFIG_NOSYSTEM=1 "
        f"exec {shlex.quote(git_executable)} \"$@\"\n"
    )
    wrapper.chmod(0o700)
    original_path = child_environment.get("PATH", "")
    child_environment["PATH"] = (
        str(wrapper_directory)
        if not original_path
        else str(wrapper_directory) + os.pathsep + original_path
    )
    child_environment["GIT_CONFIG_GLOBAL"] = os.devnull
    child_environment["GIT_CONFIG_NOSYSTEM"] = "1"
    child_environment[REAL_GIT_ENVIRONMENT] = git_executable


def seal_bare_repository_view(destination, child_environment):
    """Block a projected root only when its files already form a bare repository."""
    check_environment = dict(child_environment)
    check_environment["LC_ALL"] = "C"
    result = subprocess.run(
        ["git", "--git-dir=.", "rev-parse", "--git-dir"],
        cwd=destination,
        env=check_environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode == 0:
        (destination / ".git").write_text(GIT_BOUNDARY_MARKER)
    elif result.returncode != 128 or "not a git repository" not in result.stderr:
        raise RuntimeError("could not verify the projected test-view Git boundary")


def seal_bare_repository_views(destination, child_environment):
    """Seal every bare repository shape without following projected symlinks."""
    for current_root, directory_names, file_names in os.walk(
        str(destination),
        followlinks=False,
    ):
        current = Path(current_root)
        directory_names[:] = [
            name
            for name in directory_names
            if not (current / name).is_symlink()
        ]
        if any(name.casefold() == "head" for name in file_names):
            seal_bare_repository_view(current, child_environment)


def materialize_repository_view(
    destination,
    child_environment,
    repository=None,
    seen_repositories=None,
    additional_paths=(),
):
    """Copy versionable working-tree entries without Git metadata."""
    is_root_repository = repository is None
    repository = (REPO if repository is None else Path(repository)).resolve()
    seen_repositories = (
        set() if seen_repositories is None else seen_repositories
    )
    if repository in seen_repositories:
        raise RuntimeError("repository test view contained a recursive repository")
    seen_repositories.add(repository)
    destination.mkdir(parents=True)
    relative_paths = set(repository_view_paths(child_environment, repository))
    if is_root_repository:
        relative_paths.update(additional_paths)
    for relative_path in sorted(relative_paths):
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RuntimeError("repository test view contained an unsafe path")
        if any(part.casefold() == ".git" for part in relative_path.parts):
            raise RuntimeError("repository test view contained Git metadata")
        source = repository / relative_path
        target = destination / relative_path
        reject_projected_symlink_traversal(destination, relative_path)
        if source.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(os.readlink(str(source)), str(target))
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(target))
        elif source.is_dir():
            nested_marker = source / ".git"
            if nested_marker.exists() or nested_marker.is_symlink():
                materialize_repository_view(
                    target,
                    child_environment,
                    repository=source,
                    seen_repositories=seen_repositories,
                )
            else:
                target.mkdir(parents=True, exist_ok=True)
        elif source.exists():
            raise RuntimeError(
                f"unsupported repository test-view entry: {relative_path}"
            )
    if is_root_repository:
        seal_bare_repository_views(destination, child_environment)
    seen_repositories.remove(repository)


def main():
    configured_identity = configured_git_identity()
    child_environment = isolated_test_environment()
    for name, value in configured_identity.items():
        child_environment.setdefault(name, value)
    test_files = repository_test_files()
    if not test_files:
        print("no repository tests found")
        return 0
    failed = []
    with tempfile.TemporaryDirectory(prefix="agentfold-tests-") as scratch:
        scratch_root = Path(scratch).resolve()
        validate_scratch_root(scratch_root, child_environment)
        install_isolated_git_wrapper(scratch_root, child_environment)
        child_environment["GIT_CEILING_DIRECTORIES"] = str(scratch_root)
        test_cwd = scratch_root / "view"
        relative_tests = tuple(test.relative_to(REPO) for test in test_files)
        materialize_repository_view(
            test_cwd,
            child_environment,
            additional_paths=test_support_paths(test_files),
        )
        for test, rel in zip(test_files, relative_tests):
            result = subprocess.run(
                [sys.executable, str(test_cwd / rel)],
                cwd=test_cwd,
                env=child_environment,
            )
            (print(f"PASS {rel}") if result.returncode == 0 else failed.append(rel))
    for rel in failed:
        print(f"FAIL {rel}")
    print(f"tests: {len(test_files) - len(failed)}/{len(test_files)} files passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
