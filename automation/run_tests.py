#!/usr/bin/env python3
"""Run selected repository test files, each in its own process.

Discovery covers services, canonical skills, and automation. Each child receives a
sanitized Git environment, an empty ``HOME`` and XDG config root so no caller Git
configuration is readable, and a fresh metadata-free projection outside every existing
repository's discovery path. Subprocess-per-file keeps hyphenated folders
importable-free and any test crash isolated. This is not a sandbox against deliberate
absolute paths. The default is always the full suite. ``--staged`` maps every staged
path through the input-ownership table below and runs only the tests those paths own:
record paths (`INERT_PATH_PREFIXES`, Markdown outside a test's own directory) own no
test, while a removed non-record path and any unregistered path own the full suite.
Uncertainty always falls back to full. Every narrow lane prunes the record paths out of
its projection, so a test that starts reading one fails instead of silently invalidating
the table. The projection contains working-tree bytes, not an index snapshot. Exit 0
only if every selected file passes.
"""
import argparse
import hashlib
import os
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
        "GIT_TERMINAL_PROMPT",
    )
)
GIT_IDENTITY_CONFIG = (
    ("user.name", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"),
    ("user.email", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"),
)
PROJECTED_REPOSITORY_ENVIRONMENT = "AGENTFOLD_TEST_VIEW_ROOT"
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
# Record paths: no test reads their content or their existence. The claim is enforced
# twice — statically by InputOwnershipTests and dynamically by pruning them out of every
# narrow lane's projection (`prune_inert_projection`).
INERT_PATH_PREFIXES = (
    b"docs/",
    b"handbook/",
    b"history/",
    b"memory/",
    b"message-queue/",
    b"roadmap/",
    b"tasks/",
    b"templates/",
)
INERT_ROOT_PATHS = (b"LICENSE",)
MARKDOWN_SUFFIX = b".md"
# Which discovered test files read each non-service repository input. Entries ending in
# "/" match a prefix, the rest match one exact path. Owners come from the paths a test
# declares it reads, the module import closure of those paths, and any test that names
# the input textually; a shared module owned by most of the suite (for example
# automation/markdown_semantics.py) is deliberately left out so that it lands on the
# coarse group fallback below.
INPUT_TEST_OWNERS = (
    (
        b".github/scripts/collect_conversation_actions.py",
        (
            "automation/tests/test_collect_github_review_actions.py",
            "automation/tests/test_github_action_projection_workflow.py",
            "automation/tests/test_resolve_github_external_sources.py",
        ),
    ),
    (
        b".github/scripts/collect_review_actions.py",
        (
            "automation/tests/test_check_core_scope.py",
            "automation/tests/test_collect_github_review_actions.py",
            "automation/tests/test_github_action_projection_workflow.py",
            "automation/tests/test_resolve_github_external_sources.py",
        ),
    ),
    (
        b".github/scripts/resolve_external_source_releases.py",
        (
            "automation/tests/test_github_action_projection_workflow.py",
            "automation/tests/test_resolve_github_external_sources.py",
        ),
    ),
    (
        b".github/workflows/harness.yml",
        (
            "automation/tests/test_check_core_scope.py",
            "automation/tests/test_github_action_projection_workflow.py",
            "automation/tests/test_reconcile_queue.py",
        ),
    ),
    (
        b"automation/check_action_projection.py",
        (
            "automation/tests/test_check_action_projection.py",
            "automation/tests/test_github_action_projection_workflow.py",
            "automation/tests/test_reconcile_queue.py",
            "automation/tests/test_resolve_github_external_sources.py",
        ),
    ),
    (
        b"automation/check_core_scope.py",
        ("automation/tests/test_check_core_scope.py",),
    ),
    (
        b"automation/cochange-ledger.txt",
        ("automation/tests/test_mine_cochange.py",),
    ),
    (
        b"automation/core-scope-paths.txt",
        ("automation/tests/test_check_core_scope.py",),
    ),
    (
        b"automation/hooks/pre-commit",
        ("automation/tests/test_run_tests.py",),
    ),
    (
        b"automation/inspect_workspace_boundaries.py",
        ("automation/tests/test_inspect_workspace_boundaries.py",),
    ),
    (
        b"automation/install.py",
        ("automation/tests/test_check_core_scope.py",),
    ),
    (
        b"automation/mine_cochange.py",
        ("automation/tests/test_mine_cochange.py",),
    ),
    (
        b"automation/reconcile/",
        ("automation/tests/test_reconcile_queue.py",),
    ),
    (
        b"automation/run_tests.py",
        ("automation/tests/test_run_tests.py",),
    ),
)
# Any other path under these groups owns every discovered test in the group: only that
# group's tests can read them, but which file owns which is not registered above.
GROUP_TEST_OWNERS = (
    (b".github/", "automation"),
    (b"automation/", "automation"),
    (b"skills/", "skills"),
)

def registered_top_level_names():
    """Return the top-level entries whose contents the tables above describe."""
    names = {prefix.split(b"/")[0] for prefix in INERT_PATH_PREFIXES}
    names.update(prefix.split(b"/")[0] for prefix, _group in GROUP_TEST_OWNERS)
    names.update(prefix.split(b"/")[0] for prefix, _services in SERVICE_TEST_DEPENDENCIES)
    return frozenset(names)


REGISTERED_TOP_LEVEL_NAMES = registered_top_level_names()
STAGED_PATH_REPORT_LIMIT = 12
INERT_PROBE_ENVIRONMENT = "AGENTFOLD_INERT_PROBE"
TestSelection = namedtuple("TestSelection", "lane reason test_files staged_paths")
TestSelection.__new__.__defaults__ = ((),)


def parse_arguments(arguments):
    """Parse the deliberately small runner interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="select a conservative staged-change lane, falling back to full",
    )
    return parser.parse_args(arguments)


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


def group_test_files(all_test_files, repository, group):
    """Return every discovered test under one top-level group folder."""
    owned = []
    for test in all_test_files:
        try:
            relative = test.relative_to(repository)
        except ValueError:
            continue
        parts = relative.parts
        if (
            len(parts) > 2
            and parts[0] == group
            and parts[-2] == "tests"
            and relative.name.startswith("test_")
            and relative.suffix == ".py"
        ):
            owned.append(test)
    return tuple(sorted(owned))


def named_test_files(names, all_test_files, repository):
    """Resolve ownership-table test names against discovery, failing closed."""
    discovered = {}
    for test in all_test_files:
        try:
            discovered[str(test.relative_to(repository))] = test
        except ValueError:
            continue
    resolved = []
    for name in names:
        test = discovered.get(name)
        if test is None:
            return None
        resolved.append(test)
    return tuple(sorted(resolved))


def test_path_owners(all_test_files, repository):
    """Map discovered test paths and their directories to the tests they own."""
    file_owners = {}
    directory_owners = {}
    for test in all_test_files:
        try:
            relative = test.relative_to(repository)
        except ValueError:
            continue
        file_owners[os.fsencode(str(relative))] = (test,)
        directory = os.fsencode(str(relative.parent)) + b"/"
        directory_owners.setdefault(directory, set()).add(test)
    return (
        file_owners,
        tuple(
            (directory, tuple(sorted(tests)))
            for directory, tests in sorted(directory_owners.items())
        ),
    )


def staged_path_owners(path, all_test_files, repository=None, owners=None):
    """Classify one staged path against the input-ownership table.

    Returns ``("tests", tests)`` for a path whose readers are known, ``("inert", ())``
    for a record path no test reads, and ``("unknown", ())`` when only the full suite
    is a safe answer — including for every unregistered top-level entry.
    """
    repository = REPO if repository is None else Path(repository)
    file_owners, directory_owners = (
        test_path_owners(all_test_files, repository) if owners is None else owners
    )
    if path in file_owners:
        return "tests", file_owners[path]
    for directory, tests in directory_owners:
        if path.startswith(directory):
            return "tests", tests
    for prefix, services in SERVICE_TEST_DEPENDENCIES:
        if path.startswith(prefix) and len(path) > len(prefix):
            selected = discovered_service_tests(all_test_files, services, repository)
            return ("tests", selected) if selected else ("unknown", ())
    for entry, names in INPUT_TEST_OWNERS:
        matched = (
            path.startswith(entry) and len(path) > len(entry)
            if entry.endswith(b"/")
            else path == entry
        )
        if matched:
            selected = named_test_files(names, all_test_files, repository)
            return ("tests", selected) if selected is not None else ("unknown", ())
    registered = (
        b"/" not in path or path.split(b"/")[0] in REGISTERED_TOP_LEVEL_NAMES
    )
    if registered and (path.endswith(MARKDOWN_SUFFIX) or path in INERT_ROOT_PATHS):
        return "inert", ()
    for prefix in INERT_PATH_PREFIXES:
        if path.startswith(prefix) and len(path) > len(prefix):
            return "inert", ()
    for prefix, group in GROUP_TEST_OWNERS:
        if path.startswith(prefix) and len(path) > len(prefix):
            return "tests", group_test_files(all_test_files, repository, group)
    return "unknown", ()


def staged_path_note(path, kind, tests):
    """Describe one staged path's ownership decision for the run's own report."""
    printable = os.fsdecode(path)
    if kind == "inert":
        return "{0} -> record path, no test reads it".format(printable)
    if not tests:
        return "{0} -> owned, but no such test is discovered".format(printable)
    names = ", ".join(sorted(test.name for test in tests))
    return "{0} -> {1}".format(printable, names)


def staged_entry_paths(status, paths):
    """Split one staged entry into paths that still exist and paths that are gone."""
    if status in ("A", "M", "T"):
        return (paths[0],), ()
    if status == "D":
        return (), (paths[0],)
    if status[0] == "R":
        return (paths[1],), (paths[0],)
    if status[0] == "C":
        return (paths[1],), ()
    return None, None


def staged_test_selection(all_test_files, repository=None):
    """Map every staged path to the tests it owns, or fall back to the full suite."""
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

    owners = test_path_owners(all_test_files, repository)
    selected = set()
    changed_paths = []
    notes = []
    for status, paths in entries:
        present, removed = staged_entry_paths(status, paths)
        if present is None:
            return full_selection(
                all_test_files,
                "staged change has an unmergeable status",
            )
        for path in removed:
            kind, _tests = staged_path_owners(
                path,
                all_test_files,
                repository,
                owners,
            )
            if kind != "inert":
                return full_selection(
                    all_test_files,
                    "a removed or renamed non-record path cannot be narrowed",
                )
            notes.append(
                "{0} -> removed record path, no test reads it".format(
                    os.fsdecode(path)
                )
            )
        for path in present:
            kind, tests = staged_path_owners(
                path,
                all_test_files,
                repository,
                owners,
            )
            if kind == "unknown":
                return full_selection(
                    all_test_files,
                    "staged path has no registered test owner",
                )
            notes.append(staged_path_note(path, kind, tests))
            if kind == "inert":
                continue
            changed_paths.append(path)
            selected.update(tests)

    if changed_paths:
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

    selected_tests = tuple(sorted(selected))
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
        (
            "every staged path maps to its registered test owners"
            if selected_tests
            else "every staged path is a record path no test reads"
        ),
        selected_tests,
        tuple(notes),
    )


def report_selection(selection, repository=None, all_test_files=()):
    """Print stable evidence for the lane chosen before tests begin."""
    repository = REPO if repository is None else Path(repository)
    print(f"test lane: {selection.lane}")
    print(f"test reason: {selection.reason}")
    if selection.staged_paths:
        print(f"staged paths: {len(selection.staged_paths)}")
        for note in selection.staged_paths[:STAGED_PATH_REPORT_LIMIT]:
            print(f"  {note}")
        hidden = len(selection.staged_paths) - STAGED_PATH_REPORT_LIMIT
        if hidden > 0:
            print(f"  ... {hidden} more staged path(s) with the same decisions")
    print("selected test files:")
    if selection.test_files:
        for test in selection.test_files:
            print(f"  {test.relative_to(repository)}")
    else:
        print("  (none)")
    selected = set(selection.test_files)
    skipped = tuple(test for test in all_test_files if test not in selected)
    if skipped:
        print(f"skipped test files: {len(skipped)} (no staged path owns them)")
        for test in skipped:
            print(f"  {test.relative_to(repository)}")
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


def install_isolated_git_configuration(scratch_root, child_environment):
    """Point child Git configuration at empty scratch state, not the caller's.

    Isolation is environment-only: empty ``HOME`` and ``XDG_CONFIG_HOME`` mean Git finds
    no global configuration on any version, ``GIT_CONFIG_NOSYSTEM`` blocks system
    configuration, and ``GIT_CONFIG_GLOBAL`` repeats the global block on Git 2.32+.
    ``git`` stays the real binary on ``PATH``: an interposed shell wrapper doubled the
    process count of every Git call the suite makes, which is most of its wall time.
    """
    git_executable = shutil.which("git", path=child_environment.get("PATH"))
    if (
        not git_executable
        or not Path(git_executable).is_file()
        or not os.access(git_executable, os.X_OK)
    ):
        raise RuntimeError("could not locate Git for the isolated test environment")
    isolated_home = scratch_root / "git-home"
    isolated_xdg_config = scratch_root / "git-xdg-config"
    isolated_home.mkdir(parents=True)
    isolated_xdg_config.mkdir()
    child_environment["HOME"] = str(isolated_home)
    child_environment["XDG_CONFIG_HOME"] = str(isolated_xdg_config)
    child_environment["GIT_CONFIG_GLOBAL"] = os.devnull
    child_environment["GIT_CONFIG_NOSYSTEM"] = "1"


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


def remove_projected_entry(target):
    """Delete one projected file, symlink, or subtree; return the files removed."""
    if target.is_symlink() or target.is_file():
        target.unlink()
        return 1
    if not target.is_dir():
        return 0
    removed = 0
    for _root, _directories, file_names in os.walk(str(target), followlinks=False):
        removed += len(file_names)
    shutil.rmtree(str(target))
    return removed


def prune_inert_projection(view, test_files=(), repository=None):
    """Strip record paths out of a narrow lane's projection.

    No selected test may read a record path, so deleting them makes a future
    undeclared read fail instead of silently invalidating ``INPUT_TEST_OWNERS``.
    A test's own directory keeps its Markdown fixtures.
    """
    view = Path(view)
    if not view.is_dir():
        return 0
    repository = REPO if repository is None else Path(repository)
    kept_directories = set()
    for test in test_files:
        try:
            relative = test.relative_to(repository)
        except ValueError:
            continue
        kept_directories.add(view / relative.parent)
    removed = 0
    for prefix in INERT_PATH_PREFIXES:
        removed += remove_projected_entry(view / os.fsdecode(prefix.rstrip(b"/")))
    for name in INERT_ROOT_PATHS:
        removed += remove_projected_entry(view / os.fsdecode(name))
    markdown_suffix = os.fsdecode(MARKDOWN_SUFFIX)
    for current_root, directory_names, file_names in os.walk(
        str(view),
        followlinks=False,
    ):
        current = Path(current_root)
        directory_names[:] = [
            name for name in directory_names if not (current / name).is_symlink()
        ]
        if any(
            kept == current or kept in current.parents for kept in kept_directories
        ):
            continue
        for file_name in file_names:
            if file_name.endswith(markdown_suffix):
                removed += remove_projected_entry(current / file_name)
    return removed


def main(arguments=()):
    started = time.monotonic()
    options = parse_arguments(arguments)
    all_test_files = repository_test_files()
    selection = (
        staged_test_selection(all_test_files)
        if options.staged
        else full_selection(all_test_files, "full suite requested")
    )
    report_selection(selection, all_test_files=all_test_files)
    test_files = selection.test_files
    if not test_files:
        print(
            "no repository tests found"
            if not all_test_files
            else "no discovered test file can be affected by the staged change"
        )
        print(f"test elapsed: {time.monotonic() - started:.2f}s")
        return 0
    configured_identity = configured_git_identity()
    child_environment = isolated_test_environment()
    for name, value in configured_identity.items():
        child_environment.setdefault(name, value)
    failed = []
    with tempfile.TemporaryDirectory(prefix="agentfold-tests-") as scratch:
        scratch_root = Path(scratch).resolve()
        validate_scratch_root(scratch_root, child_environment)
        install_isolated_git_configuration(scratch_root, child_environment)
        child_environment["GIT_CEILING_DIRECTORIES"] = str(scratch_root)
        test_cwd = scratch_root / "view"
        relative_tests = tuple(test.relative_to(REPO) for test in test_files)
        materialize_repository_view(
            test_cwd,
            child_environment,
            additional_paths=test_support_paths(test_files),
        )
        if selection.lane != "full":
            pruned = prune_inert_projection(test_cwd, test_files)
            print(f"pruned record paths from the narrow test view: {pruned}")
        child_environment[PROJECTED_REPOSITORY_ENVIRONMENT] = str(test_cwd)
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
    print(f"test elapsed: {time.monotonic() - started:.2f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
