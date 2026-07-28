#!/usr/bin/env python3
"""Run selected repository test files, each in its own process.

Discovery covers services, canonical skills, and automation. Each child receives a
sanitized Git environment and a fresh metadata-free projection outside every existing
repository's discovery path. Subprocess-per-file keeps hyphenated folders
importable-free and any test crash isolated. Local mode is not a sandbox against
deliberate absolute paths. Provider-hard mode requires its documented Linux container
boundary, retains a root judge, and runs only each candidate test as the dedicated
unprivileged UID. The default is always the full suite. ``--staged`` selects a narrow
service lane only when every staged entry is known-safe; uncertainty falls back to the
full suite. The projection contains working-tree bytes, not an index snapshot. Exit 0
only if every selected file passes.
"""
import argparse
import ctypes
import hashlib
import os
import signal
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from collections import namedtuple
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
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_TERMINAL_PROMPT",
    )
)
GIT_IDENTITY_CONFIG = (
    ("user.name", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"),
    ("user.email", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"),
)
REAL_GIT_ENVIRONMENT = "AGENTFOLD_TEST_REAL_GIT"
PROJECTED_REPOSITORY_ENVIRONMENT = "AGENTFOLD_TEST_VIEW_ROOT"
PROVIDER_CANDIDATE_UID = 65532
PROVIDER_CANDIDATE_GID = 65532
PROVIDER_CAPABILITIES = frozenset((5, 6, 7))  # KILL, SETGID, SETUID
REGULAR_INDEX_MODES = frozenset((b"100644", b"100755"))
SERVICE_TEST_DEPENDENCIES = (
    (
        b"services/quote-api/",
        ("quote-api", "quote-cli"),
    ),
    (
        b"services/quote-cli/",
        ("quote-cli",),
    ),
)
TestSelection = namedtuple("TestSelection", "lane reason test_files")


def parse_arguments(arguments):
    """Parse the deliberately small runner interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="select a conservative staged-change lane, falling back to full",
    )
    parser.add_argument(
        "--view-root",
        type=Path,
        help="run from this already captured metadata-free tested view",
    )
    parser.add_argument(
        "--test-file",
        action="append",
        default=[],
        help="repository-relative test file to run (repeatable)",
    )
    parser.add_argument(
        "--provider-hard",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    options = parser.parse_args(arguments)
    if options.staged and (options.view_root or options.test_file):
        parser.error("--staged cannot be combined with --view-root or --test-file")
    if options.provider_hard and not (options.view_root and options.test_file):
        parser.error("--provider-hard requires an explicit view and test manifest")
    return options


def parse_staged_name_status(output):
    """Parse ``git diff --name-status -z`` output without line delimiters."""
    if not output or not output.endswith(b"\0"):
        raise ValueError("empty or unterminated staged diff")
    fields = output[:-1].split(b"\0")
    entries = []
    index = 0
    while index < len(fields):
        raw_status = fields[index]
        index += 1
        try:
            status = raw_status.decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError("non-ASCII staged status") from error
        if status in ("A", "D", "M", "T", "U", "X", "B"):
            path_count = 1
        elif (
            len(status) > 1
            and status[0] in ("C", "R")
            and status[1:].isdigit()
            and 0 <= int(status[1:]) <= 100
        ):
            path_count = 2
        else:
            raise ValueError("unknown staged status")
        if index + path_count > len(fields):
            raise ValueError("staged status is missing a path")
        paths = tuple(fields[index:index + path_count])
        if any(not path for path in paths):
            raise ValueError("staged path is empty")
        entries.append((status, paths))
        index += path_count
    return tuple(entries)


def parse_index_entries(output):
    """Parse ``git ls-files --stage -z`` into path-to-entry mappings."""
    if output and not output.endswith(b"\0"):
        raise ValueError("unterminated index listing")
    entries = {}
    for record in output[:-1].split(b"\0") if output else ():
        try:
            header, path = record.split(b"\t", 1)
            mode, object_id, stage = header.split(b" ")
        except ValueError as error:
            raise ValueError("malformed index entry") from error
        if (
            not path
            or len(mode) != 6
            or any(byte not in b"01234567" for byte in mode)
            or not object_id
            or any(byte not in b"0123456789abcdefABCDEF" for byte in object_id)
            or stage not in (b"0", b"1", b"2", b"3")
        ):
            raise ValueError("malformed index entry")
        entries.setdefault(path, []).append((mode, stage))
    return entries


def full_selection(all_test_files, reason):
    """Return the fail-closed full-suite choice."""
    return TestSelection("full", reason, tuple(all_test_files))


def selected_git_index_path(repository, environment):
    """Resolve the exact index file used by selector Git commands."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "index"],
        cwd=repository,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError("could not resolve the selected Git index")
    raw_path = result.stdout.rstrip(b"\n")
    if not raw_path or b"\0" in raw_path or b"\n" in raw_path:
        raise RuntimeError("selected Git index path is malformed")
    path = Path(os.fsdecode(raw_path))
    return path if path.is_absolute() else repository / path


def index_fingerprint(index_path):
    """Hash the selected index so mixed Git reads cannot approve a narrow lane."""
    try:
        return hashlib.sha256(index_path.read_bytes()).digest()
    except OSError as error:
        raise RuntimeError("could not fingerprint the selected Git index") from error


def discovered_service_tests(all_test_files, services, repository):
    """Return every discovered test owned by the requested service closure."""
    tests_by_service = {service: [] for service in services}
    for test in all_test_files:
        try:
            relative = test.relative_to(repository)
        except ValueError:
            continue
        if (
            len(relative.parts) == 4
            and relative.parts[0] == "services"
            and relative.parts[1] in tests_by_service
            and relative.parts[2] == "tests"
            and relative.name.startswith("test_")
            and relative.suffix == ".py"
        ):
            tests_by_service[relative.parts[1]].append(test)
    if any(not tests for tests in tests_by_service.values()):
        return ()
    return tuple(sorted({test for tests in tests_by_service.values() for test in tests}))


def staged_test_selection(all_test_files, repository=None):
    """Map a wholly known staged service diff to its conservative test closure."""
    repository = REPO if repository is None else Path(repository)
    selector_environment = dict(os.environ)
    try:
        index_path = selected_git_index_path(repository, selector_environment)
        initial_index_fingerprint = index_fingerprint(index_path)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--name-status", "-z", "-M"],
            cwd=repository,
            env=selector_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, RuntimeError):
        return full_selection(all_test_files, "staged index or diff unavailable")
    if diff.returncode:
        return full_selection(all_test_files, "staged diff unavailable")
    try:
        entries = parse_staged_name_status(diff.stdout)
    except (TypeError, ValueError):
        return full_selection(all_test_files, "staged diff empty or malformed")

    selected_services = set()
    changed_paths = []
    for status, paths in entries:
        if status not in ("A", "M"):
            return full_selection(
                all_test_files,
                "staged change has a non-add/modify status",
            )
        path = paths[0]
        dependencies = None
        for prefix, services in SERVICE_TEST_DEPENDENCIES:
            if path.startswith(prefix) and len(path) > len(prefix):
                dependencies = services
                break
        if dependencies is None:
            return full_selection(
                all_test_files,
                "staged path is outside the known narrow service scopes",
            )
        changed_paths.append(path)
        selected_services.update(dependencies)

    try:
        index_result = subprocess.run(
            ["git", "ls-files", "--stage", "-z"],
            cwd=repository,
            env=selector_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        return full_selection(all_test_files, "index entry types unavailable")
    if index_result.returncode:
        return full_selection(all_test_files, "index entry types unavailable")
    try:
        index_entries = parse_index_entries(index_result.stdout)
    except (TypeError, ValueError):
        return full_selection(all_test_files, "index entry listing is malformed")
    for raw_path in sorted(changed_paths):
        path_entries = index_entries.get(raw_path)
        if (
            path_entries is None
            or len(path_entries) != 1
            or path_entries[0][0] not in REGULAR_INDEX_MODES
            or path_entries[0][1] != b"0"
        ):
            return full_selection(
                all_test_files,
                "staged path is not one regular index entry",
            )
        working_path = repository / Path(os.fsdecode(raw_path))
        try:
            unsafe_working_path = (
                path_crosses_symlink(working_path, repository)
                or not working_path.is_file()
            )
        except (OSError, ValueError):
            unsafe_working_path = True
        if unsafe_working_path:
            return full_selection(
                all_test_files,
                "working-tree bytes are unavailable or cross a symlink",
            )

    selected_tests = discovered_service_tests(
        all_test_files,
        selected_services,
        repository,
    )
    if not selected_tests:
        return full_selection(
            all_test_files,
            "a mapped service has no complete discovered test scope",
        )
    for test in selected_tests:
        try:
            unavailable_test = (
                path_crosses_symlink(test, repository)
                or not test.is_file()
            )
        except (OSError, ValueError):
            unavailable_test = True
        if unavailable_test:
            return full_selection(
                all_test_files,
                "a mapped test is unavailable or crosses a symlink",
            )
    try:
        stable_index = index_fingerprint(index_path) == initial_index_fingerprint
    except RuntimeError:
        stable_index = False
    if not stable_index:
        return full_selection(
            all_test_files,
            "Git index changed while selecting staged tests",
        )
    return TestSelection(
        "staged",
        "all staged paths map to known service dependencies",
        selected_tests,
    )


def report_selection(selection, repository=None):
    """Print stable evidence for the lane chosen before tests begin."""
    repository = REPO if repository is None else Path(repository)
    print(f"test lane: {selection.lane}")
    print(f"test reason: {selection.reason}")
    print("evidence authority: cooperative-same-interpreter")
    print("controlled completion: false")
    print("enforcement eligible: false")
    print("selected test files:")
    if selection.test_files:
        for test in selection.test_files:
            print(f"  {test.relative_to(repository)}")
    else:
        print("  (none)")
    sys.stdout.flush()


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
        projected_root = child_environment.get(PROJECTED_REPOSITORY_ENVIRONMENT)
        if (
            result.returncode == 128
            and projected_root
            and Path(projected_root).resolve() == repository.resolve()
        ):
            return filesystem_view_paths(repository)
        detail = os.fsdecode(result.stderr).strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"could not enumerate the repository test view{suffix}")
    return tuple(
        Path(os.fsdecode(raw_path))
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    )


def filesystem_view_paths(repository):
    """Enumerate an already sanitized projection without following symlinks."""
    repository = Path(repository).resolve()
    relative_paths = set()
    for current_root, directory_names, file_names in os.walk(
        str(repository),
        followlinks=False,
    ):
        current = Path(current_root)
        for directory_name in tuple(directory_names):
            directory = current / directory_name
            if directory_name.casefold() == ".git":
                directory_names.remove(directory_name)
            elif directory.is_symlink():
                relative_paths.add(directory.relative_to(repository))
                directory_names.remove(directory_name)
        for file_name in file_names:
            if file_name.casefold() != ".git":
                relative_paths.add(
                    (current / file_name).relative_to(repository)
                )
    return tuple(sorted(relative_paths))


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


def materialize_captured_view(source, destination, child_environment):
    """Copy an exact gate view, dropping its fixed empty reconciler sentinel."""
    source = Path(source).resolve()
    for current_root, directory_names, file_names in os.walk(
        str(source), followlinks=False
    ):
        current = Path(current_root)
        git_directories = [
            name for name in directory_names if name.casefold() == ".git"
        ]
        git_files = [name for name in file_names if name.casefold() == ".git"]
        root_sentinel = current == source and git_directories == [".git"]
        if git_files or git_directories and not root_sentinel:
            raise RuntimeError("explicit tested view contained Git metadata")
        if root_sentinel:
            sentinel = current / ".git"
            if sentinel.is_symlink() or not sentinel.is_dir() \
                    or any(sentinel.iterdir()):
                raise RuntimeError("explicit tested view contained Git metadata")
            directory_names.remove(".git")

    def ignore_reconciler_sentinel(path, names):
        if Path(path).resolve() == source and ".git" in names:
            return {".git"}
        return set()

    shutil.copytree(
        str(source),
        str(destination),
        symlinks=True,
        ignore=ignore_reconciler_sentinel,
    )
    seal_bare_repository_views(destination, child_environment)


def _linux_process_status(pid="self"):
    try:
        lines = Path(f"/proc/{pid}/status").read_text().splitlines()
    except OSError as error:
        raise RuntimeError("provider-hard process status is unavailable") from error
    return {
        name: value.strip()
        for line in lines
        if ":" in line
        for name, value in (line.split(":", 1),)
    }


def _capability_mask(capabilities):
    return sum(1 << capability for capability in capabilities)


def provider_hard_preflight():
    """Verify and acquire the trusted Linux root judge boundary."""
    if not sys.platform.startswith("linux") or not Path("/proc/self/status").is_file():
        raise RuntimeError("provider-hard test isolation requires Linux procfs")
    if os.getuid() != 0 or os.getgid() != 0:
        raise RuntimeError("provider-hard test materializer must run as root")
    status = _linux_process_status()
    expected = _capability_mask(PROVIDER_CAPABILITIES)
    for name in ("CapEff", "CapPrm", "CapBnd"):
        try:
            observed = int(status[name], 16)
        except (KeyError, ValueError) as error:
            raise RuntimeError("provider-hard capability evidence is malformed") from error
        if observed != expected:
            raise RuntimeError(
                "provider-hard root judge must have only KILL, SETGID, and SETUID"
            )
    if status.get("NoNewPrivs") != "1":
        raise RuntimeError("provider-hard root judge requires no-new-privileges")
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        configured = ctypes.c_int()
        if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
            raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER failed")
        if libc.prctl(37, ctypes.byref(configured), 0, 0, 0) != 0:  # PR_GET_CHILD_SUBREAPER
            raise OSError(ctypes.get_errno(), "PR_GET_CHILD_SUBREAPER failed")
    except (AttributeError, OSError) as error:
        raise RuntimeError("provider-hard child subreaper is unavailable") from error
    if configured.value != 1:
        raise RuntimeError("provider-hard child subreaper did not activate")


def seal_provider_test_view(root):
    """Make one root-owned candidate input view non-writable to candidate UID."""
    root = Path(root)
    for current_root, directory_names, file_names in os.walk(
        str(root), topdown=False, followlinks=False
    ):
        current = Path(current_root)
        for name in file_names:
            path = current / name
            if path.is_symlink():
                raise RuntimeError("provider-hard test view contains a symlink")
            executable = path.stat().st_mode & 0o111
            path.chmod(0o555 if executable else 0o444)
        for name in directory_names:
            path = current / name
            if path.is_symlink():
                raise RuntimeError("provider-hard test view contains a symlink")
            path.chmod(0o555)
        current.chmod(0o555)


def restore_provider_test_view(root):
    """Restore root-owned view modes after every candidate process is gone."""
    root = Path(root)
    for current_root, directory_names, file_names in os.walk(
        str(root), topdown=False, followlinks=False
    ):
        current = Path(current_root)
        for name in file_names:
            path = current / name
            if path.is_symlink():
                raise RuntimeError("provider-hard test view contains a symlink")
            executable = path.stat().st_mode & 0o111
            path.chmod(0o755 if executable else 0o644)
        for name in directory_names:
            path = current / name
            if path.is_symlink():
                raise RuntimeError("provider-hard test view contains a symlink")
            path.chmod(0o755)
        current.chmod(0o755)


def prepare_provider_candidate_scratch(state):
    """Create fresh writable scratch without requiring the absent CHOWN capability."""
    state = Path(state)
    state.mkdir(parents=True)
    home = state / "home"
    temporary = state / "tmp"
    home.mkdir()
    temporary.mkdir()
    for path in (home, temporary):
        path.chmod(0o777)
    return home, temporary


def _provider_candidate_pids():
    owned = set()
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            status = _linux_process_status(entry.name)
            effective_uid = int(status["Uid"].split()[1])
        except (KeyError, RuntimeError, ValueError):
            continue
        if effective_uid == PROVIDER_CANDIDATE_UID:
            owned.add(int(entry.name))
    return owned


def cleanup_provider_candidate_processes(deadline):
    """Kill and reap every process running as the dedicated candidate UID."""
    observed = set()
    while time.monotonic() < deadline:
        owned = _provider_candidate_pids()
        observed.update(owned)
        for pid in owned:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        while True:
            try:
                waited, _status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if waited == 0:
                break
        if not _provider_candidate_pids():
            return observed
        time.sleep(0.01)
    if _provider_candidate_pids():
        raise RuntimeError("provider-hard candidate processes survived cleanup")
    return observed


def _drop_to_provider_candidate():
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise OSError(ctypes.get_errno(), "PR_SET_NO_NEW_PRIVS failed")
    os.setgroups([])
    os.setgid(PROVIDER_CANDIDATE_GID)
    os.setuid(PROVIDER_CANDIDATE_UID)


PROVIDER_TEST_LAUNCHER = r'''import os
import pathlib
import runpy
import sys

status = {
    name: value.strip()
    for line in pathlib.Path("/proc/self/status").read_text().splitlines()
    if ":" in line
    for name, value in (line.split(":", 1),)
}
if os.getuid() != 65532 or os.getgid() != 65532 or os.getgroups():
    raise SystemExit("provider-hard candidate identity is not isolated")
if any(int(status[name], 16) != 0 for name in ("CapEff", "CapPrm", "CapAmb")):
    raise SystemExit("provider-hard candidate retained capabilities")
if status.get("NoNewPrivs") != "1":
    raise SystemExit("provider-hard candidate can gain privileges")
test = pathlib.Path(sys.argv[1]).resolve()
view = pathlib.Path(os.environ["AGENTFOLD_TEST_VIEW_ROOT"]).resolve()
home = pathlib.Path(sys.argv[2]).resolve()
temporary = pathlib.Path(sys.argv[3]).resolve()
if view not in test.parents or os.access(str(view), os.W_OK):
    raise SystemExit("provider-hard candidate input view is writable")
if not os.access(str(home), os.W_OK) or not os.access(str(temporary), os.W_OK):
    raise SystemExit("provider-hard candidate scratch is unavailable")
sys.path.insert(0, str(test.parent))
runpy.run_path(str(test), run_name="__main__")
'''


def provider_candidate_environment(child_environment, view, home, temporary):
    allowed = {
        "CI",
        "GITHUB_ACTIONS",
        "LANG",
        "LC_ALL",
        "PATH",
        "RUNNER_ARCH",
        "RUNNER_OS",
        "TZ",
        "PYTHONWARNINGS",
    }.union(SAFE_GIT_BEHAVIOR_VARIABLES)
    environment = {
        name: value
        for name, value in child_environment.items()
        if name in allowed
    }
    environment.update(
        {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(home),
            "TMPDIR": str(temporary),
            PROJECTED_REPOSITORY_ENVIRONMENT: str(view),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
        }
    )
    return environment


def run_provider_test(test_path, cwd, environment, home, temporary):
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-c",
            PROVIDER_TEST_LAUNCHER,
            str(test_path),
            str(home),
            str(temporary),
        ],
        cwd=cwd,
        env=environment,
        start_new_session=True,
        preexec_fn=_drop_to_provider_candidate,
    )
    returncode = process.wait()
    cleanup_deadline = time.monotonic() + 1.0
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    leaked = cleanup_provider_candidate_processes(cleanup_deadline)
    if leaked:
        print(
            f"provider-hard cleanup: killed {len(leaked)} candidate process(es)",
            file=sys.stderr,
        )
        returncode = 1
    return subprocess.CompletedProcess(process.args, returncode)


def main(arguments=()):
    started = time.monotonic()
    options = parse_arguments(arguments)
    if options.provider_hard:
        print(
            "provider-hard testing is unavailable: install a controlled external "
            "completion oracle and independently controlled publisher",
            file=sys.stderr,
        )
        return 1
    source_repository = (
        options.view_root.resolve() if options.view_root else REPO
    )
    if options.view_root and not source_repository.is_dir():
        raise RuntimeError("explicit tested view is unavailable")
    all_test_files = repository_test_files(source_repository)
    if options.test_file:
        discovered = {
            test.relative_to(source_repository).as_posix(): test
            for test in all_test_files
        }
        requested = []
        for raw_path in options.test_file:
            path = Path(raw_path)
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError("explicit test path is unsafe")
            test = discovered.get(path.as_posix())
            if test is None:
                raise RuntimeError(f"explicit test was not discovered: {raw_path}")
            requested.append(test)
        selection = TestSelection(
            "explicit-view",
            "gate supplied an exact tested view and manifest",
            tuple(sorted(set(requested))),
        )
    else:
        selection = (
            staged_test_selection(all_test_files)
            if options.staged
            else full_selection(all_test_files, "full suite requested")
        )
    report_selection(selection, source_repository)
    test_files = selection.test_files
    if not test_files:
        print("no repository tests found")
        print(f"test elapsed: {time.monotonic() - started:.2f}s")
        return 0
    configured_identity = configured_git_identity()
    child_environment = isolated_test_environment()
    for name, value in configured_identity.items():
        child_environment.setdefault(name, value)
    failed = []
    with tempfile.TemporaryDirectory(prefix="agentfold-tests-") as scratch:
        scratch_root = Path(scratch).resolve()
        if options.provider_hard:
            scratch_root.chmod(0o755)
        validate_scratch_root(scratch_root, child_environment)
        install_isolated_git_wrapper(scratch_root, child_environment)
        child_environment["GIT_CEILING_DIRECTORIES"] = str(scratch_root)
        relative_tests = tuple(
            test.relative_to(source_repository) for test in test_files
        )
        support_paths = test_support_paths(test_files, source_repository)
        for index, rel in enumerate(relative_tests):
            test_cwd = scratch_root / f"view-{index}"
            if source_repository == REPO and not options.view_root:
                materialize_repository_view(
                    test_cwd,
                    child_environment,
                    additional_paths=support_paths,
                )
            else:
                child_environment[PROJECTED_REPOSITORY_ENVIRONMENT] = str(
                    source_repository
                )
                materialize_captured_view(
                    source_repository, test_cwd, child_environment
                )
            child_environment[PROJECTED_REPOSITORY_ENVIRONMENT] = str(test_cwd)
            if options.provider_hard:
                seal_provider_test_view(test_cwd)
                state = scratch_root / f"state-{index}"
                home, temporary = prepare_provider_candidate_scratch(state)
                result = run_provider_test(
                    test_cwd / rel,
                    test_cwd,
                    provider_candidate_environment(
                        child_environment, test_cwd, home, temporary
                    ),
                    home,
                    temporary,
                )
                restore_provider_test_view(test_cwd)
            else:
                result = subprocess.run(
                    [sys.executable, str(test_cwd / rel)],
                    cwd=test_cwd,
                    env=child_environment,
                )
            (print(f"PASS {rel}") if result.returncode == 0 else failed.append(rel))
    for rel in failed:
        print(f"FAIL {rel}")
    print(f"tests: {len(test_files) - len(failed)}/{len(test_files)} files passed")
    print(f"test elapsed: {time.monotonic() - started:.2f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
