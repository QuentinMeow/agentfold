#!/usr/bin/env python3
"""Run every repository test file, each in its own process.

Discovery covers services, canonical skills, and automation. Each child receives a
sanitized Git environment and a fresh metadata-free projection outside every existing
repository's discovery path. Subprocess-per-file keeps hyphenated folders
importable-free and any test crash isolated. This is not a sandbox against deliberate
absolute paths. Exit 0 only if every file passes.
"""
import os
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


def materialize_repository_view(
    destination,
    child_environment,
    repository=None,
    seen_repositories=None,
):
    """Copy versionable working-tree entries without Git metadata."""
    repository = (REPO if repository is None else Path(repository)).resolve()
    seen_repositories = (
        set() if seen_repositories is None else seen_repositories
    )
    if repository in seen_repositories:
        raise RuntimeError("repository test view contained a recursive repository")
    seen_repositories.add(repository)
    destination.mkdir(parents=True)
    for relative_path in repository_view_paths(child_environment, repository):
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RuntimeError("repository test view contained an unsafe path")
        source = repository / relative_path
        target = destination / relative_path
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
    seal_bare_repository_view(destination, child_environment)
    seen_repositories.remove(repository)


def main():
    child_environment = isolated_test_environment()
    test_files = sorted({test for pattern in TEST_GLOBS for test in REPO.glob(pattern)})
    if not test_files:
        print("no repository tests found")
        return 0
    failed = []
    with tempfile.TemporaryDirectory(prefix="agentfold-tests-") as scratch:
        scratch_root = Path(scratch).resolve()
        validate_scratch_root(scratch_root, child_environment)
        child_environment["GIT_CEILING_DIRECTORIES"] = str(scratch_root)
        for index, test in enumerate(test_files):
            rel = test.relative_to(REPO)
            test_cwd = scratch_root / f"{index:04d}"
            materialize_repository_view(test_cwd, child_environment)
            result = subprocess.run(
                [sys.executable, str(test)],
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
