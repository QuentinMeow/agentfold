#!/usr/bin/env python3
"""Run selected repository test files, each in its own process.

Discovery covers services, canonical skills, and automation. Each child receives a
sanitized Git environment, a scratch ``HOME`` and XDG config root carrying only the
runner's own configuration so no caller Git configuration is readable and no repository
a test builds runs background maintenance, a fresh metadata-free projection outside
every existing repository's discovery path, and a redirected ``TMPDIR`` so every fixture
repository a test builds lands under this run's own scratch root instead of the real
system temp directory (``install_isolated_scratch_tmpdir``); an interrupted run then
leaves at most one named directory behind, never hundreds of anonymous ones. Subprocess-
per-file keeps hyphenated folders importable-free and any test crash isolated. This is not
a sandbox against deliberate absolute paths. The default is always the full suite.
``--staged`` maps every staged path through the input-ownership table below and runs only
the tests those paths own:
record paths (`INERT_PATH_PREFIXES`, Markdown outside a test's own directory) own no
test, while a removed non-record path and any unregistered path own the full suite.
Uncertainty always falls back to full. Every narrow lane prunes the record paths out of
its projection, so a test that starts reading one fails instead of silently invalidating
the table. The projection contains working-tree bytes, not an index snapshot. Exit 0
only if every selected file passes.

``--jobs N`` runs N shards at once against that one shared projection. Shards are cut at
test-method granularity, because one file is most of the suite, and the method names come
from an ``ast`` walk that costs no subprocess; a file whose tests the walk cannot fully
see runs whole rather than partly. ``--jobs 1`` is the historical serial run, one
subprocess per file with inherited output and no added argument. Files listed in
``QUARANTINED_TEST_FILES`` are never sharded and run in a reported serial tail.
"""
import argparse
import ast
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEST_GLOBS = (
    "services/*/tests/test_*.py",
    "skills/*/tests/test_*.py",
    "automation/**/tests/test_*.py",
)
GIT_BOUNDARY_MARKER = "AgentFold isolated test view; not a Git repository.\n"
# Any Git read that compares the index against a committed tree goes through this
# prefix: without it a `refs/replace/*` entry can make the staged diff look empty and
# narrow the pre-commit lane down to no tests at all. Reads that only touch the index,
# the worktree, the config, or a repository location may stay bare, because a
# replacement entry has nothing to substitute in them. The source-level guard in
# `automation/tests/test_reconcile_queue.py` holds that line.
RAW_GIT = ("git", "--no-replace-objects")
# Written into the isolated scratch HOME by install_isolated_git_configuration(), which
# explains why. Both `auto` keys are needed: Git through 2.54 gates the background spawn
# on `maintenance.auto` alone, while newer Git falls back to `gc.auto` when
# `maintenance.auto` is unset, and `gc.auto` is also what stops Git 2.23 auto-gc. The
# `autoDetach` keys are the backstop: should either ever run, it stays in the foreground
# and cannot outlive the command that started it.
ISOLATED_GIT_CONFIGURATION = """\
# Written by automation/run_tests.py. No test may rely on background Git maintenance:
# it detaches and writes inside .git/objects after the foreground command has exited,
# which races temporary-directory teardown.
[gc]
\tauto = 0
\tautoDetach = false
[maintenance]
\tauto = false
\tautoDetach = false
"""
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
# narrow lane's projection (`prune_inert_projection`). A path registered in
# INPUT_TEST_OWNERS above wins over these prefixes, which is how the queue templates
# stay real test inputs while the rest of `templates/` remains inert.
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
    # The review parser's enforced claimant ceiling and fixed-size key contract are
    # documented in this canonical schema and pinned by the semantics tests.
    (
        b"templates/task/verification.md",
        ("automation/tests/test_markdown_semantics.py",),
    ),
    # Not a record either: the pull-request schema test reads both the schema and its
    # GitHub projection and asserts their shape, so editing one is a real input.
    (
        b".github/pull_request_template.md",
        ("automation/tests/test_pull_request_schema.py",),
    ),
    # The boundary gate derives the section order it reports on from this schema at run
    # time, so its own tests read it too: it is their input, not a record beside them.
    (
        b"templates/pull-request.md",
        (
            "automation/tests/test_check_action_projection.py",
            "automation/tests/test_pull_request_schema.py",
        ),
    ),
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
            "automation/tests/test_markdown_semantics.py",
            "automation/tests/test_pull_request_schema.py",
            "automation/tests/test_reconcile_queue.py",
            "automation/tests/test_resolve_github_external_sources.py",
        ),
    ),
    (
        b"automation/check_core_scope.py",
        (
            "automation/tests/test_check_core_scope.py",
            "automation/tests/test_reconcile_queue.py",
        ),
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
        b"automation/integrate.py",
        ("automation/tests/test_integrate.py",),
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
        (
            "automation/tests/test_markdown_semantics.py",
            "automation/tests/test_reconcile_open_actions.py",
            "automation/tests/test_reconcile_queue.py",
        ),
    ),
    (
        b"automation/run_tests.py",
        (
            "automation/tests/test_reconcile_queue.py",
            "automation/tests/test_run_tests.py",
        ),
    ),
    # Not records: the copy-and-fill test copies every queue template, fills it, and
    # requires the reconciler to accept the result, so a template edit is a real
    # input to that test rather than a document nothing reads.
    (
        b"templates/queue/",
        ("automation/tests/test_reconcile_queue.py",),
    ),
    (
        b"templates/README.md",
        ("automation/tests/test_reconcile_queue.py",),
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
# Files that may never share the machine with another shard, and why. Each runs whole,
# one at a time, after the parallel phase, and the run says so instead of hiding it.
QUARANTINED_TEST_FILES = (
    (
        "automation/tests/test_run_tests.py",
        "its tests re-run this whole runner, so a shard of it would nest a second "
        "worker pool inside the first",
    ),
)
# Enough shards per worker that a slow one cannot leave the others idle at the tail,
# but not so many that per-shard interpreter startup and module import dominate.
SHARD_UNITS_PER_WORKER = 6
MINIMUM_SHARD_TESTS = 4
TEST_METHOD_PREFIX = "test"
TEST_CASE_BASE_NAMES = frozenset(("TestCase", "IsolatedAsyncioTestCase"))
# Bases that provably contribute no test method, so a class using one stays readable.
INERT_BASE_NAMES = frozenset(("object",))
# Calls that can attach test methods no source-level walk can enumerate. ``type`` is
# only one of them in its three-argument class-building form; ``type(x)`` is a question.
HIDDEN_TEST_CALL_NAMES = frozenset(("globals", "setattr", "vars"))
DYNAMIC_CLASS_CALL_NAME = "type"
DYNAMIC_CLASS_ARGUMENT_COUNT = 3
VERBOSE_CHILD_ARGUMENTS = ("-v",)
TestSelection = namedtuple("TestSelection", "lane reason test_files staged_paths")
TestSelection.__new__.__defaults__ = ((),)
ShardUnit = namedtuple("ShardUnit", "relative names index count")
ShardPlan = namedtuple("ShardPlan", "units tail opaque")


def worker_count_argument(value):
    """Reject a worker count that cannot describe a run."""
    try:
        count = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("worker count must be an integer")
    if count < 1:
        raise argparse.ArgumentTypeError("worker count must be at least 1")
    return count


def parse_arguments(arguments):
    """Parse the deliberately small runner interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="select a conservative staged-change lane, falling back to full",
    )
    parser.add_argument(
        "--jobs",
        type=worker_count_argument,
        default=None,
        metavar="N",
        help=(
            "run N test shards at once against one shared projection; 1 keeps the "
            "historical serial subprocess-per-file run; default is physical cores"
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="pass -v to every child so every executed test name is printed",
    )
    return parser.parse_args(arguments)


def physical_core_count():
    """Report physical cores, or None where the platform cannot be asked cheaply."""
    if sys.platform == "darwin":
        sysctl = shutil.which("sysctl") or "/usr/sbin/sysctl"
        try:
            result = subprocess.run(
                [sysctl, "-n", "hw.physicalcpu"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except OSError:
            return None
        reported = (result.stdout or "").strip()
        if result.returncode or not reported.isdigit() or not int(reported):
            return None
        return int(reported)
    if sys.platform.startswith("linux"):
        try:
            info = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        cores = set()
        package = core = None
        for line in info.splitlines():
            key, separator, value = line.partition(":")
            if not separator:
                package = core = None
                continue
            key = key.strip()
            if key == "physical id":
                package = value.strip()
            elif key == "core id":
                core = value.strip()
            if package is not None and core is not None:
                cores.add((package, core))
                package = core = None
        return len(cores) or None
    return None


def default_worker_count():
    """Default to physical cores, not to ``os.cpu_count()``.

    The suite spends more system than user time: it is bound by process creation and
    Git calls, not by arithmetic. Simultaneous-multithreading siblings share one core's
    execution resources, so counting them oversubscribes the machine and adds
    contention without adding throughput. Where the physical count cannot be read, half
    the logical count is the closest safe guess, floored at two so a small
    two-thread runner still shards.
    """
    physical = physical_core_count()
    if physical:
        return physical
    logical = os.cpu_count() or 1
    return max(1, min(logical, max(2, logical // 2)))


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
            [*RAW_GIT, "diff", "--cached", "--name-status", "-z", "-M"],
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
        print(
            f"skipped test files: {len(skipped)} (no staged path owns them); "
            "the complete suite still runs on every push"
        )
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
    """Point child Git configuration at scratch state the runner owns, not the caller's.

    Isolation is environment-only: ``HOME`` and ``XDG_CONFIG_HOME`` point into a scratch
    root holding nothing of the caller's, so no caller global configuration is reachable
    on any Git version, and ``GIT_CONFIG_NOSYSTEM`` blocks system configuration. ``git``
    stays the real binary on ``PATH``: an interposed shell wrapper doubled the process
    count of every Git call the suite makes, which is most of its wall time.

    The one file placed in that scratch ``HOME`` turns off automatic maintenance for
    every repository any test builds. Since Git 2.30, ``git commit`` runs
    ``git maintenance run --auto --detach``; the detached grandchild outlives the
    foreground command and creates then removes ``<objects-dir>/maintenance.lock``, i.e.
    it writes *inside* ``.git/objects`` after ``subprocess.run`` has already returned.
    A fixture repository is far below the ``gc.auto`` threshold, so that lock is the only
    work it ever does — but it is enough to race ``TemporaryDirectory`` teardown and fail
    it with ``ENOTEMPTY`` on ``objects``. Disabling it also drops one spawned process per
    commit, which the suite makes hundreds of.

    Reaching Git of every vintage takes one file plus one variable, not two mechanisms.
    ``GIT_CONFIG_COUNT`` needs Git 2.31 and ``GIT_CONFIG_GLOBAL`` needs 2.32, so neither
    can carry a setting to the Git 2.23 some contributors run. Writing ``.gitconfig`` into
    the scratch ``HOME`` covers those older versions, and ``GIT_CONFIG_GLOBAL`` must then
    name that same file rather than ``os.devnull``: on 2.32+ it replaces the global scope
    outright, so leaving it at ``os.devnull`` would silently discard the settings on
    exactly the newer Git that needs them.
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
    isolated_global_config = isolated_home / ".gitconfig"
    isolated_global_config.write_text(ISOLATED_GIT_CONFIGURATION, encoding="utf-8")
    child_environment["HOME"] = str(isolated_home)
    child_environment["XDG_CONFIG_HOME"] = str(isolated_xdg_config)
    child_environment["GIT_CONFIG_GLOBAL"] = str(isolated_global_config)
    child_environment["GIT_CONFIG_NOSYSTEM"] = "1"


def install_isolated_scratch_tmpdir(scratch_root, child_environment):
    """Point ``TMPDIR``/``TMP``/``TEMP`` at scratch state this run owns and destroys.

    Every fixture that calls ``tempfile.mkdtemp()`` or ``tempfile.TemporaryDirectory()``
    without an explicit ``dir=`` resolves through ``tempfile.gettempdir()``, which reads
    these variables from its own process environment. Left inherited from the caller, a
    killed run -- the ordinary way a developer stops a slow suite mid-flight -- scatters
    its scratch Git repositories across the real system temp directory: one clone per test
    method, hundreds per run, none named in a way that says which run left them or whether
    they are safe to delete.

    Redirecting them under this run's own scratch root does not make interruption safe --
    a ``SIGKILL`` still skips every ``finally`` block and context-manager exit, so nothing
    here can run in response to it. What it changes is where the debris lands: every child
    process, and everything a child process spawns, inherits the same one scratch-relative
    directory. A completed run's outer ``TemporaryDirectory`` still removes it as a single
    recursive unit, exactly as before. An interrupted run leaves at most one predictable
    ``agentfold-tests-*`` directory in the real temp root instead of hundreds of anonymous
    ones, and a human (or the next run) can find and remove it with one ``rm -rf``.
    """
    isolated_tmp = scratch_root / "tmp"
    isolated_tmp.mkdir()
    location = str(isolated_tmp)
    for name in ("TMPDIR", "TMP", "TEMP"):
        child_environment[name] = location


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


def registered_input_path(relative):
    """Whether INPUT_TEST_OWNERS claims this path as a real test input.

    A path can sit under an inert prefix and still be something a test reads —
    `templates/queue/` is Markdown that the copy-and-fill test copies, fills, and
    feeds to the reconciler. The ownership table is the authority in both
    directions, so pruning asks it rather than assuming the prefix decides.
    """
    encoded = os.fsencode(str(relative))
    for entry, _names in INPUT_TEST_OWNERS:
        if entry.endswith(b"/"):
            if encoded.startswith(entry) and len(encoded) > len(entry):
                return True
        elif encoded == entry:
            return True
    return False


def prune_inert_projection(view, test_files=(), repository=None):
    """Strip record paths out of a narrow lane's projection.

    No selected test may read a record path, so deleting them makes a future
    undeclared read fail instead of silently invalidating ``INPUT_TEST_OWNERS``.
    A test's own directory keeps its Markdown fixtures, and so does any path the
    ownership table registers as an input.
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
        if any(entry.startswith(prefix) for entry, _names in INPUT_TEST_OWNERS):
            # Part of this tree is a registered input, so the per-file walk below
            # decides entry by entry instead of deleting the whole tree.
            continue
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
            if not file_name.endswith(markdown_suffix):
                continue
            path = current / file_name
            try:
                if registered_input_path(path.relative_to(view)):
                    continue
            except ValueError:
                pass
            removed += remove_projected_entry(path)
    return removed


def attribute_chain_name(node):
    """Return the dotted name of a class base, or None for a computed expression."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def hides_test_methods(tree):
    """Return whether this module can attach tests no source-level walk can see."""
    top_level = sum(1 for node in tree.body if isinstance(node, ast.ClassDef))
    nested = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    if top_level != nested:
        return True
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            called = attribute_chain_name(node.func)
            if called in HIDDEN_TEST_CALL_NAMES:
                return True
            if (
                called == DYNAMIC_CLASS_CALL_NAME
                and len(node.args) == DYNAMIC_CLASS_ARGUMENT_COUNT
            ):
                return True
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "load_tests":
                return True
    return False


def transitive_closure(direct, seeds):
    """Grow each key's value over its local bases until nothing changes."""
    closure = {name: set(value) for name, value in seeds.items()}
    for _pass in range(len(closure) + 1):
        changed = False
        for name, bases in direct.items():
            for base in bases:
                if base in closure and not closure[base] <= closure[name]:
                    closure[name] |= closure[base]
                    changed = True
        if not changed:
            return closure
    return None


def discovered_test_names(source):
    """Return every ``Class.test_method`` in one module, or None when unsure.

    None means the walk cannot prove it saw every test — a base class defined outside
    this file, the ``load_tests`` protocol, a class decorator or metaclass, a class
    built at import time, or a class nested inside other code. The caller must then run
    the whole file: a shard that silently drops the tests the walk missed would report
    a green suite that never executed them.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    if hides_test_methods(tree):
        return None
    own_methods = {}
    local_bases = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if node.decorator_list or node.keywords:
            return None
        bases = []
        for base in node.bases:
            name = attribute_chain_name(base)
            if name is None:
                return None
            bases.append(name)
        own_methods[node.name] = {
            child.name
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name.startswith(TEST_METHOD_PREFIX)
        }
        local_bases[node.name] = tuple(bases)
    for bases in local_bases.values():
        for base in bases:
            leaf = base.rsplit(".", 1)[-1]
            if leaf in TEST_CASE_BASE_NAMES or leaf in INERT_BASE_NAMES:
                continue
            if base not in local_bases:
                return None
    methods = transitive_closure(local_bases, own_methods)
    collected = transitive_closure(
        local_bases,
        {
            name: {name} if any(
                base.rsplit(".", 1)[-1] in TEST_CASE_BASE_NAMES for base in bases
            ) else set()
            for name, bases in local_bases.items()
        },
    )
    if methods is None or collected is None:
        return None
    names = tuple(sorted(
        "{0}.{1}".format(class_name, method)
        for class_name, own in collected.items()
        if own
        for method in methods[class_name]
    ))
    return names or None


def split_evenly(names, target):
    """Split one file's test names into near-equal chunks of about ``target``."""
    count = min(len(names), max(1, int(round(len(names) / float(target)))))
    chunks = []
    start = 0
    for index in range(count):
        stop = len(names) * (index + 1) // count
        chunks.append(tuple(names[start:stop]))
        start = stop
    return tuple(chunk for chunk in chunks if chunk)


def shard_plan(test_files, worker_count, repository=None, quarantined=None):
    """Cut the selected files into parallel shard units plus a reported serial tail."""
    repository = REPO if repository is None else Path(repository)
    quarantined = QUARANTINED_TEST_FILES if quarantined is None else quarantined
    quarantined_names = {name for name, _reason in quarantined}
    shardable = []
    tail = []
    opaque = []
    for test in test_files:
        relative = test.relative_to(repository)
        if relative.as_posix() in quarantined_names:
            tail.append(relative)
            continue
        try:
            names = discovered_test_names(test.read_text(encoding="utf-8"))
        except OSError:
            names = None
        if names is None:
            opaque.append(relative)
        shardable.append((relative, names))
    total = sum(len(names) for _relative, names in shardable if names)
    target = max(
        MINIMUM_SHARD_TESTS,
        -(-total // max(1, worker_count * SHARD_UNITS_PER_WORKER)),
    )
    units = []
    for relative, names in sorted(
        shardable,
        key=lambda entry: (-len(entry[1] or ()), entry[0].as_posix()),
    ):
        chunks = split_evenly(names, target) if names else ((),)
        for index, chunk in enumerate(chunks):
            units.append(ShardUnit(relative, chunk, index + 1, len(chunks)))
    return ShardPlan(tuple(units), tuple(tail), tuple(opaque))


def shard_header(unit, returncode):
    """Name one shard's file, position, and size above its buffered output."""
    size = "{0} test(s)".format(len(unit.names)) if unit.names else "whole file"
    return "--- {0} {1} shard {2}/{3}, {4}".format(
        "FAIL" if returncode else "pass",
        unit.relative,
        unit.index,
        unit.count,
        size,
    )


def run_shard_units(
    units,
    test_cwd,
    child_environment,
    worker_count,
    child_arguments=(),
    emit_passing=False,
):
    """Run shards concurrently, emitting each one's output as one atomic block."""
    lock = threading.Lock()
    failed = set()

    def execute(unit):
        command = [sys.executable, str(test_cwd / unit.relative)]
        command.extend(child_arguments)
        command.extend(unit.names)
        result = subprocess.run(
            command,
            cwd=test_cwd,
            env=child_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = result.stdout or b""
        with lock:
            if result.returncode:
                failed.add(unit.relative)
            if result.returncode or emit_passing:
                text = output.decode("utf-8", "replace")
                if text and not text.endswith("\n"):
                    text += "\n"
                sys.stdout.write(shard_header(unit, result.returncode) + "\n" + text)
                sys.stdout.flush()

    with ThreadPoolExecutor(max_workers=max(1, min(worker_count, len(units)))) as pool:
        tuple(pool.map(execute, units))
    return frozenset(failed)


def report_shard_plan(plan, quarantined=None):
    """Print the schedule, the whole-file fallbacks, and the quarantine reasons."""
    quarantined = QUARANTINED_TEST_FILES if quarantined is None else quarantined
    reasons = dict(quarantined)
    print("test shards: {0}".format(len(plan.units)))
    for relative in plan.opaque:
        print(
            "  whole file: {0} -> test discovery could not see every test".format(
                relative
            )
        )
    for relative in plan.tail:
        print(
            "  serial tail: {0} -> not concurrency-safe, {1}".format(
                relative,
                reasons.get(relative.as_posix(), "quarantined"),
            )
        )
    sys.stdout.flush()


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
        print(f"tests: {len(test_files)}/{len(test_files)} files passed")
        print(f"test elapsed: {time.monotonic() - started:.2f}s")
        return 0
    worker_count = (
        options.jobs if options.jobs is not None else default_worker_count()
    )
    child_arguments = VERBOSE_CHILD_ARGUMENTS if options.verbose else ()
    if worker_count > 1:
        print("test workers: {0}".format(worker_count))
    configured_identity = configured_git_identity()
    child_environment = isolated_test_environment()
    for name, value in configured_identity.items():
        child_environment.setdefault(name, value)
    failed = []
    with tempfile.TemporaryDirectory(prefix="agentfold-tests-") as scratch:
        scratch_root = Path(scratch).resolve()
        validate_scratch_root(scratch_root, child_environment)
        install_isolated_git_configuration(scratch_root, child_environment)
        install_isolated_scratch_tmpdir(scratch_root, child_environment)
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
        if worker_count == 1:
            for test, rel in zip(test_files, relative_tests):
                command = [sys.executable, str(test_cwd / rel)]
                command.extend(child_arguments)
                result = subprocess.run(
                    command,
                    cwd=test_cwd,
                    env=child_environment,
                )
                (print(f"PASS {rel}") if result.returncode == 0 else failed.append(rel))
        else:
            plan = shard_plan(test_files, worker_count)
            report_shard_plan(plan)
            failed_relatives = set(
                run_shard_units(
                    plan.units,
                    test_cwd,
                    child_environment,
                    worker_count,
                    child_arguments=child_arguments,
                    emit_passing=options.verbose,
                )
            )
            for rel in plan.tail:
                command = [sys.executable, str(test_cwd / rel)]
                command.extend(child_arguments)
                result = subprocess.run(
                    command,
                    cwd=test_cwd,
                    env=child_environment,
                )
                if result.returncode:
                    failed_relatives.add(rel)
            for rel in relative_tests:
                (
                    print(f"PASS {rel}")
                    if rel not in failed_relatives
                    else failed.append(rel)
                )
    for rel in failed:
        print(f"FAIL {rel}")
    print(f"tests: {len(test_files) - len(failed)}/{len(test_files)} files passed")
    print(f"test elapsed: {time.monotonic() - started:.2f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
