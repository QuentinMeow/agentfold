import ast
import contextlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_tests.py"
SPEC = importlib.util.spec_from_file_location("run_tests", MODULE_PATH)
RUN_TESTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN_TESTS)


class StagedTestSelectionTests(unittest.TestCase):
    def setUp(self):
        self.all_tests = RUN_TESTS.repository_test_files()
        self.api_test = RUN_TESTS.REPO / "services/quote-api/tests/test_quote_api.py"
        self.cli_test = RUN_TESTS.REPO / "services/quote-cli/tests/test_quote_cli.py"
        self.index_path = MODULE_PATH

    @staticmethod
    def git_result(stdout=b"", returncode=0):
        return subprocess.CompletedProcess(
            ["git"],
            returncode,
            stdout=stdout,
            stderr=b"",
        )

    @staticmethod
    def index_output(*path_modes):
        object_id = b"0" * 40
        return b"".join(
            mode + b" " + object_id + b" 0\t" + path + b"\0"
            for path, mode in path_modes
        )

    def index_path_result(self, index_path=None):
        index_path = self.index_path if index_path is None else Path(index_path)
        return self.git_result(os.fsencode(str(index_path)) + b"\n")

    def selection(self, diff_output, *path_modes):
        responses = (
            self.index_path_result(),
            self.git_result(diff_output),
            self.git_result(self.index_output(*path_modes)),
        )
        with mock.patch.object(
            RUN_TESTS.subprocess,
            "run",
            side_effect=responses,
        ) as run:
            selection = RUN_TESTS.staged_test_selection(self.all_tests)
        return selection, run

    def test_cli_addition_selects_only_the_cli_test(self):
        path = b"services/quote-cli/quote_cli.py"

        selection, run = self.selection(b"A\0" + path + b"\0", (path, b"100644"))

        self.assertEqual("staged", selection.lane)
        self.assertEqual((self.cli_test,), selection.test_files)
        self.assertEqual(
            [
                "git", "--no-replace-objects",
                "diff", "--cached", "--name-status", "-z", "-M",
            ],
            run.call_args_list[1][0][0],
            "the staged diff compares the index against a committed tree, so a "
            "`refs/replace/*` entry must not be able to answer it",
        )
        self.assertEqual(
            ["git", "ls-files", "--stage", "-z"],
            run.call_args_list[2][0][0],
        )

    def test_api_modification_selects_api_and_dependent_cli_tests(self):
        path = b"services/quote-api/quotes.json"

        selection, _run = self.selection(b"M\0" + path + b"\0", (path, b"100644"))

        self.assertEqual("staged", selection.lane)
        self.assertEqual((self.api_test, self.cli_test), selection.test_files)

    def test_multiple_known_services_have_a_deterministic_dependency_union(self):
        api_path = b"services/quote-api/quote_api.py"
        cli_path = b"services/quote-cli/quote_cli.py"
        diff = b"M\0" + cli_path + b"\0A\0" + api_path + b"\0"

        selection, _run = self.selection(
            diff,
            (cli_path, b"100755"),
            (api_path, b"100644"),
        )

        self.assertEqual((self.api_test, self.cli_test), selection.test_files)

    def test_removing_or_renaming_a_non_record_path_falls_back(self):
        cases = (
            b"D\0services/quote-cli/quote_cli.py\0",
            b"D\0automation/run_tests.py\0",
            b"D\0.gitignore\0",
            (
                b"R100\0services/quote-cli/old.py\0"
                b"services/quote-cli/new.py\0"
            ),
            b"U\0services/quote-cli/quote_cli.py\0",
        )
        for diff in cases:
            with self.subTest(diff=diff):
                with mock.patch.object(
                    RUN_TESTS.subprocess,
                    "run",
                    side_effect=(
                        self.index_path_result(),
                        self.git_result(diff),
                    ),
                ) as run:
                    selection = RUN_TESTS.staged_test_selection(self.all_tests)
                self.assertEqual("full", selection.lane)
                self.assertEqual(self.all_tests, selection.test_files)
                self.assertEqual(2, run.call_count)

    def test_typechange_into_a_symlink_falls_back(self):
        path = b"services/quote-cli/quote_cli.py"

        selection, _run = self.selection(b"T\0" + path + b"\0", (path, b"120000"))

        self.assertEqual("full", selection.lane)
        self.assertEqual(self.all_tests, selection.test_files)

    def test_unregistered_paths_fall_back_to_the_full_suite(self):
        for path in (
            b"services/unknown/service.py",
            b"services/quote-api",
            b"brand-new-directory/module.py",
            b"brand-new-directory/README.md",
            b".gitignore",
            b"handbook",
        ):
            with self.subTest(path=path):
                with mock.patch.object(
                    RUN_TESTS.subprocess,
                    "run",
                    side_effect=(
                        self.index_path_result(),
                        self.git_result(b"M\0" + path + b"\0"),
                    ),
                ):
                    selection = RUN_TESTS.staged_test_selection(self.all_tests)
                self.assertEqual("full", selection.lane)
                self.assertEqual(self.all_tests, selection.test_files)

    def test_record_only_changes_select_no_test_at_all(self):
        diff = (
            b"M\0tasks/1_in-progress/2026-07-29-example/task.md\0"
            b"A\0history/conversations/2026-07-29-x/handover.md\0"
            b"D\0message-queue/needs-agent/requests/done.md\0"
            b"R100\0tasks/0_backlog/2026-07-29-example/task.md\0"
            b"tasks/1_in-progress/2026-07-29-example/design.md\0"
            b"M\0memory/index.md\0M\0docs/designs/speed.md\0"
            b"M\0roadmap/current-state.md\0M\0handbook/git-workflow.md\0"
            b"M\0templates/task/task.md\0M\0README.md\0M\0AGENTS.md\0"
            b"M\0LICENSE\0M\0automation/AGENTS.md\0"
        )

        with mock.patch.object(
            RUN_TESTS.subprocess,
            "run",
            side_effect=(self.index_path_result(), self.git_result(diff)),
        ) as run:
            selection = RUN_TESTS.staged_test_selection(self.all_tests)

        self.assertEqual("staged", selection.lane)
        self.assertEqual((), selection.test_files)
        self.assertIn("record path", selection.reason)
        self.assertEqual(2, run.call_count)
        self.assertEqual(14, len(selection.staged_paths))

    def test_automation_input_selects_only_its_registered_owners(self):
        cases = (
            (
                b"automation/run_tests.py",
                ("test_reconcile_queue.py", "test_run_tests.py"),
            ),
            (b"automation/hooks/pre-commit", ("test_run_tests.py",)),
            (
                b"automation/reconcile/reconcile.py",
                ("test_markdown_semantics.py", "test_reconcile_queue.py"),
            ),
            (b"automation/mine_cochange.py", ("test_mine_cochange.py",)),
            (b"automation/cochange-ledger.txt", ("test_mine_cochange.py",)),
            (
                b"automation/check_core_scope.py",
                ("test_check_core_scope.py", "test_reconcile_queue.py"),
            ),
            (
                b".github/workflows/harness.yml",
                (
                    "test_check_core_scope.py",
                    "test_github_action_projection_workflow.py",
                    "test_reconcile_queue.py",
                ),
            ),
        )
        for path, expected in cases:
            with self.subTest(path=path):
                selection, _run = self.selection(
                    b"M\0" + path + b"\0",
                    (path, b"100644"),
                )

                self.assertEqual("staged", selection.lane)
                self.assertEqual(
                    expected,
                    tuple(test.name for test in selection.test_files),
                )

    def test_unregistered_automation_path_selects_every_automation_test(self):
        path = b"automation/markdown_semantics.py"
        expected = tuple(
            test.name
            for test in RUN_TESTS.group_test_files(
                self.all_tests,
                RUN_TESTS.REPO,
                "automation",
            )
        )

        selection, _run = self.selection(
            b"M\0" + path + b"\0",
            (path, b"100644"),
        )

        self.assertEqual("staged", selection.lane)
        self.assertEqual(expected, tuple(test.name for test in selection.test_files))
        self.assertIn("test_reconcile_queue.py", expected)
        self.assertNotIn("test_quote_cli.py", expected)

    def test_a_test_file_change_selects_only_that_test(self):
        path = b"automation/tests/test_mine_cochange.py"

        selection, _run = self.selection(
            b"M\0" + path + b"\0",
            (path, b"100644"),
        )

        self.assertEqual("staged", selection.lane)
        self.assertEqual(
            ("test_mine_cochange.py",),
            tuple(test.name for test in selection.test_files),
        )

    def test_a_record_shaped_path_inside_a_test_directory_selects_its_tests(self):
        path = b"automation/tests/fixture-notes.md"
        expected = tuple(
            test.name
            for test in RUN_TESTS.group_test_files(
                self.all_tests,
                RUN_TESTS.REPO,
                "automation",
            )
        )
        kind, tests = RUN_TESTS.staged_path_owners(path, self.all_tests)

        self.assertEqual("tests", kind)
        self.assertEqual(expected, tuple(test.name for test in tests))

    def test_mixed_record_code_and_service_paths_select_the_union(self):
        record = b"tasks/1_in-progress/2026-07-29-example/worklog.md"
        automation_path = b"automation/reconcile/reconcile.py"
        service_path = b"services/quote-cli/quote_cli.py"
        diff = (
            b"M\0" + record + b"\0"
            b"M\0" + automation_path + b"\0"
            b"M\0" + service_path + b"\0"
        )

        selection, _run = self.selection(
            diff,
            (automation_path, b"100644"),
            (service_path, b"100644"),
        )

        self.assertEqual("staged", selection.lane)
        self.assertEqual(
            (
                "test_markdown_semantics.py",
                "test_reconcile_queue.py",
                "test_quote_cli.py",
            ),
            tuple(test.name for test in selection.test_files),
        )
        self.assertEqual(3, len(selection.staged_paths))

    def test_report_names_the_lane_the_reason_and_the_skipped_files(self):
        selection = RUN_TESTS.TestSelection(
            "staged",
            "every staged path is a record path no test reads",
            (),
            ("tasks/x/task.md -> record path, no test reads it",),
        )
        stream = io.StringIO()

        with contextlib.redirect_stdout(stream):
            RUN_TESTS.report_selection(selection, all_test_files=self.all_tests)
        output = stream.getvalue()

        self.assertIn("test lane: staged", output)
        self.assertIn("record path, no test reads it", output)
        self.assertIn(f"skipped test files: {len(self.all_tests)}", output)
        self.assertIn("automation/tests/test_run_tests.py", output)

    def test_an_empty_selection_still_prints_a_parseable_summary(self):
        """A proved-empty run and a run that died before summarizing must not look alike.

        Every run that selects at least one file ends with this line, and every
        verification record in the repository transcribes it as its evidence.
        """
        selection = RUN_TESTS.TestSelection(
            "staged", "every staged path is a record path no test reads", (), ()
        )
        stream = io.StringIO()

        with mock.patch.object(
            RUN_TESTS, "staged_test_selection", return_value=selection
        ):
            with contextlib.redirect_stdout(stream):
                code = RUN_TESTS.main(["--staged"])
        output = stream.getvalue()

        self.assertEqual(0, code)
        self.assertIn("tests: 0/0 files passed", output)
        self.assertIn(
            "no discovered test file can be affected by the staged change", output
        )

    def test_report_names_where_skipped_coverage_happens(self):
        """A named skip is evidence; an unnamed one asks the reader to trust us."""
        selection = RUN_TESTS.TestSelection(
            "staged",
            "every staged path is a record path no test reads",
            (),
            ("tasks/x/task.md -> record path, no test reads it",),
        )
        stream = io.StringIO()

        with contextlib.redirect_stdout(stream):
            RUN_TESTS.report_selection(selection, all_test_files=self.all_tests)

        self.assertIn("the complete suite still runs on every push", stream.getvalue())

    def test_empty_unavailable_and_malformed_diffs_fall_back(self):
        outcomes = (
            self.git_result(b""),
            self.git_result(b"M\0services/quote-cli/quote_cli.py"),
            self.git_result(b"", returncode=128),
        )
        for outcome in outcomes:
            with self.subTest(outcome=outcome):
                with mock.patch.object(
                    RUN_TESTS.subprocess,
                    "run",
                    side_effect=(self.index_path_result(), outcome),
                ):
                    selection = RUN_TESTS.staged_test_selection(self.all_tests)
                self.assertEqual("full", selection.lane)

    def test_symlink_and_gitlink_index_modes_fall_back(self):
        path = b"services/quote-cli/quote_cli.py"
        for mode in (b"120000", b"160000"):
            with self.subTest(mode=mode):
                selection, _run = self.selection(
                    b"M\0" + path + b"\0",
                    (path, mode),
                )
                self.assertEqual("full", selection.lane)

    def test_malformed_or_unavailable_index_listing_falls_back(self):
        path = b"services/quote-cli/quote_cli.py"
        diff = self.git_result(b"M\0" + path + b"\0")
        outcomes = (
            self.git_result(b"100644 malformed\0"),
            self.git_result(b"", returncode=128),
        )
        for outcome in outcomes:
            with self.subTest(outcome=outcome):
                with mock.patch.object(
                    RUN_TESTS.subprocess,
                    "run",
                    side_effect=(self.index_path_result(), diff, outcome),
                ):
                    selection = RUN_TESTS.staged_test_selection(self.all_tests)
                self.assertEqual("full", selection.lane)

    def test_working_tree_symlink_falls_back_because_projection_uses_its_bytes(self):
        with tempfile.TemporaryDirectory() as scratch:
            repository = Path(scratch) / "repository"
            service = repository / "services/quote-cli"
            api_tests = repository / "services/quote-api/tests"
            cli_tests = service / "tests"
            external = Path(scratch) / "external.py"
            service.mkdir(parents=True)
            api_tests.mkdir(parents=True)
            cli_tests.mkdir(parents=True)
            external.write_text("print('external')\n")
            try:
                os.symlink(str(external), str(service / "quote_cli.py"))
            except (NotImplementedError, OSError):
                self.skipTest("symlinks are unavailable")
            api_test = api_tests / "test_quote_api.py"
            cli_test = cli_tests / "test_quote_cli.py"
            api_test.write_text("pass\n")
            cli_test.write_text("pass\n")
            index_path = repository / "index.fixture"
            index_path.write_bytes(b"stable-index")
            path = b"services/quote-cli/quote_cli.py"
            responses = (
                self.index_path_result(index_path),
                self.git_result(b"M\0" + path + b"\0"),
                self.git_result(self.index_output((path, b"100644"))),
            )

            with mock.patch.object(
                RUN_TESTS.subprocess,
                "run",
                side_effect=responses,
            ):
                selection = RUN_TESTS.staged_test_selection(
                    (api_test, cli_test),
                    repository,
                )

            self.assertEqual("full", selection.lane)

    def test_missing_mapped_test_falls_back(self):
        path = b"services/quote-api/quote_api.py"

        responses = (
            self.index_path_result(),
            self.git_result(b"M\0" + path + b"\0"),
            self.git_result(self.index_output((path, b"100644"))),
        )
        with mock.patch.object(
            RUN_TESTS.subprocess,
            "run",
            side_effect=responses,
        ):
            selection = RUN_TESTS.staged_test_selection((self.api_test,))

        self.assertEqual("full", selection.lane)

    def test_newly_discovered_test_in_selected_service_is_not_skipped(self):
        with tempfile.TemporaryDirectory() as scratch:
            repository = Path(scratch) / "repository"
            service = repository / "services/quote-cli"
            tests = service / "tests"
            tests.mkdir(parents=True)
            changed = service / "quote_cli.py"
            existing = tests / "test_quote_cli.py"
            new_test = tests / "test_new_behavior.py"
            changed.write_text("pass\n")
            existing.write_text("pass\n")
            new_test.write_text("raise AssertionError('must be selected')\n")
            index_path = repository / "index.fixture"
            index_path.write_bytes(b"stable-index")
            raw_changed = b"services/quote-cli/quote_cli.py"
            responses = (
                self.index_path_result(index_path),
                self.git_result(b"M\0" + raw_changed + b"\0"),
                self.git_result(
                    self.index_output((raw_changed, b"100644"))
                ),
            )

            with mock.patch.object(
                RUN_TESTS.subprocess,
                "run",
                side_effect=responses,
            ):
                selection = RUN_TESTS.staged_test_selection(
                    (existing, new_test),
                    repository,
                )

            self.assertEqual("staged", selection.lane)
            self.assertEqual((new_test, existing), selection.test_files)

    def test_index_change_between_git_reads_falls_back_to_full(self):
        with tempfile.TemporaryDirectory() as scratch:
            repository = Path(scratch) / "repository"
            service = repository / "services/quote-cli"
            tests = service / "tests"
            tests.mkdir(parents=True)
            changed = service / "quote_cli.py"
            test = tests / "test_quote_cli.py"
            changed.write_text("pass\n")
            test.write_text("pass\n")
            index_path = repository / "index.fixture"
            index_path.write_bytes(b"before")
            raw_changed = b"services/quote-cli/quote_cli.py"
            responses = iter(
                (
                    self.index_path_result(index_path),
                    self.git_result(b"M\0" + raw_changed + b"\0"),
                    self.git_result(
                        self.index_output((raw_changed, b"100644"))
                    ),
                )
            )

            def run_with_index_change(*_args, **_kwargs):
                result = next(responses)
                if result.args == ["git"] and result.stdout.startswith(b"100644 "):
                    index_path.write_bytes(b"after")
                return result

            with mock.patch.object(
                RUN_TESTS.subprocess,
                "run",
                side_effect=run_with_index_change,
            ):
                selection = RUN_TESTS.staged_test_selection((test,), repository)

            self.assertEqual("full", selection.lane)
            self.assertIn("index changed", selection.reason)

    def test_replace_ref_cannot_swap_the_staged_diff_for_a_record_only_one(self):
        """A `refs/replace/*` entry must not choose the pre-commit test lane.

        `git diff --cached` compares the index against HEAD's tree, so a
        replacement for HEAD answers with whatever the attacker's commit
        contains. Point it at a commit that already holds the staged code but an
        older record, and the hook sees one record path, selects no test at all,
        and lets an unreviewed code change through with nothing run.
        """
        with tempfile.TemporaryDirectory() as scratch:
            repository = Path(scratch) / "repository"
            service = repository / "services/quote-cli"
            tests = service / "tests"
            tests.mkdir(parents=True)
            record = repository / "tasks/1_in-progress/2026-07-31-example"
            record.mkdir(parents=True)
            code = service / "quote_cli.py"
            test = tests / "test_quote_cli.py"
            task_record = record / "task.md"
            test.write_text("pass\n")

            def git(*arguments, **keywords):
                return subprocess.run(
                    ["git", *arguments], cwd=repository, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    check=True, **keywords
                ).stdout.strip()

            git("init", "-q")
            git("config", "user.email", "test@example.com")
            git("config", "user.name", "Test")
            # A decoy commit that already holds the final code, with an older record.
            code.write_text("print('unreviewed')\n")
            task_record.write_text("# older record\n")
            git("add", ".")
            git("commit", "-qm", "decoy")
            decoy = git("rev-parse", "HEAD")
            # The real HEAD: the old code and the current record.
            code.write_text("print('reviewed')\n")
            task_record.write_text("# current record\n")
            git("add", ".")
            git("commit", "-qm", "head")
            head = git("rev-parse", "HEAD")
            # Stage the real, unreviewed code change.
            code.write_text("print('unreviewed')\n")
            git("add", ".")

            honest = RUN_TESTS.staged_test_selection((test,), repository)
            git("replace", "-f", head, decoy)
            try:
                forged = RUN_TESTS.staged_test_selection((test,), repository)
            finally:
                git("replace", "-d", head)

            self.assertEqual("staged", honest.lane)
            self.assertEqual((test,), honest.test_files)
            self.assertEqual(honest.lane, forged.lane)
            self.assertEqual(
                honest.test_files, forged.test_files,
                "a replacement entry chose which tests the hook runs",
            )

    def test_default_interface_is_the_full_suite(self):
        options = RUN_TESTS.parse_arguments(())
        selection = RUN_TESTS.full_selection(self.all_tests, "full suite requested")

        self.assertFalse(options.staged)
        self.assertFalse(options.verbose)
        self.assertIsNone(
            options.jobs,
            "the worker count stays unresolved until a run needs it",
        )
        self.assertEqual("full", selection.lane)
        self.assertEqual(self.all_tests, selection.test_files)

    def test_pre_commit_requests_the_staged_lane(self):
        hook = (RUN_TESTS.REPO / "automation/hooks/pre-commit").read_text()

        self.assertIn('automation/run_tests.py" --staged', hook)

    def test_name_status_parser_handles_nul_delimited_special_paths(self):
        entries = RUN_TESTS.parse_staged_name_status(
            b"M\0services/quote-cli/line\nname.py\0"
        )

        self.assertEqual(
            (("M", (b"services/quote-cli/line\nname.py",)),),
            entries,
        )


REPOSITORY_BASE_FROM_DUNDER_FILE = re.compile(
    r"^([A-Z][A-Z_0-9]*)\s*=\s*\(?\s*Path\(__file__\)",
    re.MULTILINE,
)
REPOSITORY_BASE_FROM_BASE = re.compile(
    r"^([A-Z][A-Z_0-9]*)\s*=\s*\(?\s*([A-Za-z_][A-Za-z_0-9.]*)",
    re.MULTILINE,
)
REPOSITORY_PATH_CHAIN = re.compile(
    r"(?P<head>(?:Path\(__file__\)|[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*)"
    r"(?:\.[A-Za-z_][A-Za-z_0-9]*(?:\(\))?|\[\d+\])*)"
    r"(?P<segments>(?:\s*/\s*[\"'][^\"'\n]+[\"'])+)"
)
QUOTED_SEGMENT = re.compile(r"[\"']([^\"'\n]+)[\"']")
IDENTIFIER_TOKENS = re.compile(r"[.\[\]()]+")
MODULE_IMPORT = re.compile(
    r"^(?:from\s+([a-z_][a-z_0-9]*)\s+import|import\s+([a-z_][a-z_0-9]*))",
    re.MULTILINE,
)
IMPORTABLE_MODULE_GLOBS = ("automation/*.py", ".github/scripts/*.py")


def identifier_tokens(text):
    """Split a dotted or subscripted expression head into bare identifiers."""
    return tuple(token for token in IDENTIFIER_TOKENS.split(text) if token)


def repository_base_names(source):
    """Return the names a module binds to a real repository directory."""
    bases = {"REPO"}
    bases.update(REPOSITORY_BASE_FROM_DUNDER_FILE.findall(source))
    for _pass in range(3):
        for name, origin in REPOSITORY_BASE_FROM_BASE.findall(source):
            if any(token in bases for token in identifier_tokens(origin)):
                bases.add(name)
    return bases


def declared_repository_references(source):
    """Return the path literals a module joins onto a real repository directory."""
    bases = repository_base_names(source)
    references = set()
    for match in REPOSITORY_PATH_CHAIN.finditer(source):
        head = match.group("head")
        rooted = "Path(__file__)" in head or any(
            token in bases for token in identifier_tokens(head)
        )
        if not rooted:
            continue
        segments = QUOTED_SEGMENT.findall(match.group("segments"))
        joined = "/".join(segment.strip("/") for segment in segments if segment)
        if joined:
            references.add(joined)
    return tuple(sorted(references))


def matching_repository_paths(reference, repository_paths):
    """Return the real repository paths a declared reference can name."""
    return tuple(
        path
        for path in repository_paths
        if path == reference or path.endswith("/" + reference)
    )


def owning_test_files(relative_path, all_test_files):
    """Return the tests a repository path owns, reading the full suite as everything."""
    kind, owners = RUN_TESTS.staged_path_owners(
        os.fsencode(relative_path),
        all_test_files,
    )
    if kind == "unknown":
        return set(all_test_files)
    return set(owners)


class InputOwnershipTests(unittest.TestCase):
    """Keep INPUT_TEST_OWNERS honest about what the discovered tests actually read.

    Both checks are static and cost milliseconds, which is why they can run inside
    every suite. They only see repository reads written in this repository's idiom —
    a literal joined onto a directory derived from ``Path(__file__)`` — so they are
    the cheap half of the guard; ``prune_inert_projection`` is the half that catches
    a read the parser cannot see, by deleting record paths from every narrow lane.
    ``services/`` is excluded because it keeps its pre-existing dependency closure:
    test_run_tests.py names service paths to assert they exist, not to read them,
    and any removal there already falls back to the full suite.
    """

    def setUp(self):
        self.all_tests = RUN_TESTS.repository_test_files()
        environment = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith("GIT_")
        }
        try:
            paths = RUN_TESTS.repository_view_paths(environment, RUN_TESTS.REPO)
        except RuntimeError:
            paths = RUN_TESTS.filesystem_view_paths(RUN_TESTS.REPO)
        self.repository_paths = tuple(str(path) for path in paths)

    def test_every_runner_attribute_this_file_names_actually_exists(self):
        """Catch a rename whose only surviving caller sits behind an env-gated test.

        ``install_isolated_git_wrapper`` was renamed when the Git shell wrapper was
        removed, and the inert-probe call site kept the old name. That probe only runs
        under AGENTFOLD_INERT_PROBE, so the suite stayed green while the proof it
        performs raised AttributeError instead of running.
        """
        source = Path(__file__).read_text(encoding="utf-8")
        named = set()
        for node in ast.walk(ast.parse(source)):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "RUN_TESTS"
            ):
                named.add(node.attr)

        self.assertTrue(named, "no runner attributes found to check")
        missing = sorted(name for name in named if not hasattr(RUN_TESTS, name))
        self.assertEqual([], missing)

    def test_every_declared_repository_read_is_owned_by_the_reader(self):
        checked = 0
        for test in self.all_tests:
            source = test.read_text(encoding="utf-8")
            for reference in declared_repository_references(source):
                for candidate in matching_repository_paths(
                    reference,
                    self.repository_paths,
                ):
                    if candidate.startswith("services/"):
                        continue
                    checked += 1
                    owners = owning_test_files(candidate, self.all_tests)
                    self.assertIn(
                        test,
                        owners,
                        "{0} reads {1}, which the ownership table does not give "
                        "it; add the owner or make the path fall back to full"
                        .format(test.name, candidate),
                    )
        self.assertGreater(checked, 0, "the reference parser found nothing to check")

    def test_ownership_is_closed_under_module_imports(self):
        modules = {}
        for pattern in IMPORTABLE_MODULE_GLOBS:
            for path in RUN_TESTS.REPO.glob(pattern):
                modules[path.stem] = str(path.relative_to(RUN_TESTS.REPO))
        self.assertIn("markdown_semantics", modules)
        for name, relative in sorted(modules.items()):
            source = (RUN_TESTS.REPO / relative).read_text(encoding="utf-8")
            importer_owners = owning_test_files(relative, self.all_tests)
            for direct, plain in MODULE_IMPORT.findall(source):
                imported = direct or plain
                if imported == name or imported not in modules:
                    continue
                imported_owners = owning_test_files(
                    modules[imported],
                    self.all_tests,
                )
                self.assertLessEqual(
                    {test.name for test in importer_owners},
                    {test.name for test in imported_owners},
                    "{0} imports {1}, so every owner of {0} must own {1}"
                    .format(relative, modules[imported]),
                )

    def test_pruning_removes_record_paths_and_keeps_test_fixtures(self):
        with tempfile.TemporaryDirectory() as scratch:
            view = Path(scratch) / "view"
            (view / "tasks/0_backlog/example").mkdir(parents=True)
            (view / "tasks/0_backlog/example/task.md").write_text("task\n")
            (view / "automation/tests").mkdir(parents=True)
            (view / "automation/AGENTS.md").write_text("contract\n")
            (view / "automation/run_tests.py").write_text("code\n")
            (view / "automation/tests/test_probe.py").write_text("pass\n")
            (view / "automation/tests/fixture.md").write_text("fixture\n")
            (view / "LICENSE").write_text("license\n")
            (view / "README.md").write_text("readme\n")
            projected_test = view / "automation/tests/test_probe.py"

            removed = RUN_TESTS.prune_inert_projection(
                view,
                (projected_test,),
                view,
            )

            self.assertEqual(4, removed)
            self.assertFalse((view / "tasks").exists())
            self.assertFalse((view / "automation/AGENTS.md").exists())
            self.assertFalse((view / "LICENSE").exists())
            self.assertFalse((view / "README.md").exists())
            self.assertTrue((view / "automation/run_tests.py").exists())
            self.assertTrue((view / "automation/tests/fixture.md").exists())
            self.assertTrue(projected_test.exists())

    @unittest.skipUnless(
        os.environ.get(RUN_TESTS.INERT_PROBE_ENVIRONMENT),
        "set {0}=1 to run the whole suite against a record-free projection"
        .format(RUN_TESTS.INERT_PROBE_ENVIRONMENT),
    )
    def test_the_whole_suite_passes_against_a_record_free_projection(self):
        """The expensive half of the inert proof: delete the records, run everything.

        Opt-in because it costs a full suite run. It is the only check that covers a
        record read written outside this repository's path idiom, in a test the narrow
        lanes happen never to select.
        """
        all_tests = RUN_TESTS.repository_test_files()
        environment = RUN_TESTS.isolated_test_environment()
        for name, value in RUN_TESTS.configured_git_identity().items():
            environment.setdefault(name, value)
        failed = []
        with tempfile.TemporaryDirectory(prefix="agentfold-inert-probe-") as scratch:
            scratch_root = Path(scratch).resolve()
            RUN_TESTS.validate_scratch_root(scratch_root, environment)
            RUN_TESTS.install_isolated_git_configuration(scratch_root, environment)
            environment["GIT_CEILING_DIRECTORIES"] = str(scratch_root)
            view = scratch_root / "view"
            RUN_TESTS.materialize_repository_view(
                view,
                environment,
                additional_paths=RUN_TESTS.test_support_paths(all_tests),
            )
            removed = RUN_TESTS.prune_inert_projection(view, all_tests)
            environment[RUN_TESTS.PROJECTED_REPOSITORY_ENVIRONMENT] = str(view)
            # The projected copy of this file must not probe its own projection: its
            # records are already gone, so the nested probe would find nothing to prune.
            environment.pop(RUN_TESTS.INERT_PROBE_ENVIRONMENT, None)
            print("inert probe: removed {0} record path(s)".format(removed))
            self.assertGreater(removed, 0)
            for test in all_tests:
                relative = test.relative_to(RUN_TESTS.REPO)
                result = subprocess.run(
                    [sys.executable, str(view / relative)],
                    cwd=str(view),
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                print(
                    "inert probe: {0} {1}".format(
                        "PASS" if result.returncode == 0 else "FAIL",
                        relative,
                    ),
                    flush=True,
                )
                if result.returncode:
                    failed.append(
                        "{0}\n{1}".format(
                            relative,
                            result.stdout.decode("utf-8", "replace")[-2000:],
                        )
                    )
        self.assertEqual([], failed)


class ShardDiscoveryTests(unittest.TestCase):
    """Guard the one thing sharding can get silently wrong: dropping a test.

    Every check here is static and costs milliseconds. The rule the runner has to keep
    is that ``discovered_test_names`` either enumerates every test unittest would
    collect, or returns None so the file runs whole.
    """

    def test_methods_inherited_from_a_local_base_belong_to_the_child(self):
        names = RUN_TESTS.discovered_test_names(
            "import unittest\n"
            "\n"
            "class BaseCase(unittest.TestCase):\n"
            "    def test_shared(self):\n"
            "        pass\n"
            "\n"
            "class ChildCase(BaseCase):\n"
            "    def test_own(self):\n"
            "        pass\n"
        )

        self.assertEqual(
            (
                "BaseCase.test_shared",
                "ChildCase.test_own",
                "ChildCase.test_shared",
            ),
            names,
        )

    def test_a_mixin_that_is_not_a_case_still_contributes_its_methods(self):
        names = RUN_TESTS.discovered_test_names(
            "import unittest\n"
            "\n"
            "class SharedChecks(object):\n"
            "    def test_shared(self):\n"
            "        pass\n"
            "\n"
            "class ChildCase(SharedChecks, unittest.TestCase):\n"
            "    def test_own(self):\n"
            "        pass\n"
        )

        self.assertEqual(("ChildCase.test_own", "ChildCase.test_shared"), names)

    def test_discovery_falls_back_when_it_cannot_see_every_test(self):
        opaque_sources = {
            "base class from another module": (
                "from shared import BaseCase\n"
                "class ChildCase(BaseCase):\n"
                "    def test_own(self):\n"
                "        pass\n"
            ),
            "load_tests protocol": (
                "import unittest\n"
                "class Case(unittest.TestCase):\n"
                "    def test_own(self):\n"
                "        pass\n"
                "def load_tests(loader, tests, pattern):\n"
                "    return tests\n"
            ),
            "methods attached at import time": (
                "import unittest\n"
                "class Case(unittest.TestCase):\n"
                "    pass\n"
                "setattr(Case, 'test_generated', lambda self: None)\n"
            ),
            "class built by a three-argument type call": (
                "import unittest\n"
                "Case = type('Case', (unittest.TestCase,), "
                "{'test_one': lambda self: None})\n"
            ),
            "class built by a metaclass": (
                "import unittest\n"
                "class Case(unittest.TestCase, metaclass=type):\n"
                "    def test_own(self):\n"
                "        pass\n"
            ),
            "decorated class": (
                "import unittest\n"
                "@unittest.skipUnless(True, 'reason')\n"
                "class Case(unittest.TestCase):\n"
                "    def test_own(self):\n"
                "        pass\n"
            ),
            "class nested inside other code": (
                "import unittest\n"
                "if True:\n"
                "    class Case(unittest.TestCase):\n"
                "        def test_own(self):\n"
                "            pass\n"
            ),
            "unparseable source": "class Case(unittest.TestCase)\n",
            "no case at all": "value = 1\n",
        }
        for label, source in sorted(opaque_sources.items()):
            with self.subTest(label):
                self.assertIsNone(RUN_TESTS.discovered_test_names(source))

    def test_discovery_matches_what_unittest_collects_for_every_real_test_file(self):
        checked = 0
        for test in RUN_TESTS.repository_test_files():
            names = RUN_TESTS.discovered_test_names(test.read_text(encoding="utf-8"))
            self.assertIsNotNone(
                names,
                "{0} would run whole; that is safe but say so on purpose"
                .format(test.name),
            )
            spec = importlib.util.spec_from_file_location(
                "shard_probe_" + test.stem,
                test,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            loaded = set()
            for suite in unittest.defaultTestLoader.loadTestsFromModule(module):
                for case in suite:
                    loaded.add(
                        "{0}.{1}".format(
                            type(case).__name__,
                            case._testMethodName,
                        )
                    )
            self.assertEqual(loaded, set(names), test.name)
            checked += 1
        self.assertGreater(checked, 0)

    def test_every_discovered_test_lands_in_exactly_one_shard_or_the_tail(self):
        tests = RUN_TESTS.repository_test_files()
        plan = RUN_TESTS.shard_plan(tests, 8)
        quarantined = {name for name, _reason in RUN_TESTS.QUARANTINED_TEST_FILES}

        scheduled = []
        for unit in plan.units:
            self.assertTrue(unit.names, "a real test file must shard by test name")
            scheduled.extend(
                "{0}::{1}".format(unit.relative.as_posix(), name)
                for name in unit.names
            )
        expected = []
        for test in tests:
            relative = test.relative_to(RUN_TESTS.REPO).as_posix()
            if relative in quarantined:
                continue
            expected.extend(
                "{0}::{1}".format(relative, name)
                for name in RUN_TESTS.discovered_test_names(
                    test.read_text(encoding="utf-8")
                )
            )
        self.assertEqual(sorted(expected), sorted(scheduled))
        self.assertEqual(len(set(scheduled)), len(scheduled))
        self.assertEqual(
            sorted(Path(name) for name in quarantined),
            sorted(plan.tail),
        )
        self.assertEqual((), plan.opaque)

    def test_an_unreadable_file_runs_whole_instead_of_being_dropped(self):
        missing = RUN_TESTS.REPO / "automation/tests/test_absent_probe.py"
        plan = RUN_TESTS.shard_plan((missing,), 4)

        self.assertEqual(1, len(plan.units))
        self.assertEqual((), plan.units[0].names)
        self.assertEqual((Path("automation/tests/test_absent_probe.py"),), plan.opaque)

    def test_the_quarantined_file_is_reported_with_its_reason(self):
        tests = (RUN_TESTS.REPO / "automation/tests/test_run_tests.py",)
        plan = RUN_TESTS.shard_plan(tests, 4)
        report = io.StringIO()
        with contextlib.redirect_stdout(report):
            RUN_TESTS.report_shard_plan(plan)
        printed = report.getvalue()

        self.assertEqual((), plan.units)
        self.assertIn("serial tail: automation/tests/test_run_tests.py", printed)
        self.assertIn("not concurrency-safe", printed)
        self.assertIn("nest a second worker pool", printed)

    def test_worker_count_must_be_a_positive_integer(self):
        for rejected in ("0", "-1", "two", ""):
            with self.subTest(rejected):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        RUN_TESTS.parse_arguments(("--jobs", rejected))
        self.assertEqual(3, RUN_TESTS.parse_arguments(("--jobs", "3")).jobs)

    def test_the_default_worker_count_is_physical_cores_not_logical_ones(self):
        with mock.patch.object(RUN_TESTS, "physical_core_count", return_value=6):
            self.assertEqual(6, RUN_TESTS.default_worker_count())
        with mock.patch.object(RUN_TESTS, "physical_core_count", return_value=None):
            for logical, expected in ((16, 8), (4, 2), (2, 2), (1, 1)):
                with self.subTest(logical):
                    with mock.patch.object(RUN_TESTS.os, "cpu_count", return_value=logical):
                        self.assertEqual(expected, RUN_TESTS.default_worker_count())


class ShardExecutionTests(unittest.TestCase):
    def test_shard_output_is_emitted_as_one_uninterrupted_block(self):
        units = tuple(
            RUN_TESTS.ShardUnit(
                Path("automation/tests/test_probe.py"),
                ("Case.test_{0}".format(index),),
                index + 1,
                12,
            )
            for index in range(12)
        )

        def fake_run(command, **_keywords):
            index = command[-1].rsplit("_", 1)[1]
            time.sleep(0.005)
            body = "".join(
                "line {0} of shard {1}\n".format(line, index) for line in range(40)
            )
            return subprocess.CompletedProcess(
                command,
                1,
                stdout=body.encode("utf-8"),
            )

        report = io.StringIO()
        with mock.patch.object(RUN_TESTS.subprocess, "run", side_effect=fake_run):
            with contextlib.redirect_stdout(report):
                failed = RUN_TESTS.run_shard_units(
                    units,
                    Path("/view"),
                    {},
                    8,
                )

        self.assertEqual(
            frozenset((Path("automation/tests/test_probe.py"),)),
            failed,
        )
        blocks = report.getvalue().split("--- FAIL ")
        self.assertEqual(13, len(blocks))
        for block in blocks[1:]:
            shards = {
                line.rsplit(" ", 1)[1]
                for line in block.splitlines()
                if line.startswith("line ")
            }
            self.assertEqual(1, len(shards), block)
            self.assertEqual(40, len(block.splitlines()) - 1, block)

    def test_a_passing_shard_stays_quiet_unless_the_run_asked_for_names(self):
        unit = RUN_TESTS.ShardUnit(
            Path("automation/tests/test_probe.py"),
            ("Case.test_one",),
            1,
            1,
        )
        completed = subprocess.CompletedProcess(["python"], 0, stdout=b"ok\n")

        quiet = io.StringIO()
        with mock.patch.object(RUN_TESTS.subprocess, "run", return_value=completed):
            with contextlib.redirect_stdout(quiet):
                RUN_TESTS.run_shard_units((unit,), Path("/view"), {}, 2)
        loud = io.StringIO()
        with mock.patch.object(RUN_TESTS.subprocess, "run", return_value=completed):
            with contextlib.redirect_stdout(loud):
                RUN_TESTS.run_shard_units(
                    (unit,),
                    Path("/view"),
                    {},
                    2,
                    emit_passing=True,
                )

        self.assertEqual("", quiet.getvalue())
        self.assertIn("--- pass automation/tests/test_probe.py", loud.getvalue())
        self.assertIn("ok", loud.getvalue())

    def test_a_shard_command_carries_the_child_arguments_then_the_test_names(self):
        unit = RUN_TESTS.ShardUnit(
            Path("automation/tests/test_probe.py"),
            ("Case.test_one", "Case.test_two"),
            1,
            1,
        )
        completed = subprocess.CompletedProcess(["python"], 0, stdout=b"")

        with mock.patch.object(
            RUN_TESTS.subprocess,
            "run",
            return_value=completed,
        ) as run:
            RUN_TESTS.run_shard_units(
                (unit,),
                Path("/view"),
                {},
                2,
                child_arguments=("-v",),
            )

        self.assertEqual(
            [
                sys.executable,
                str(Path("/view/automation/tests/test_probe.py")),
                "-v",
                "Case.test_one",
                "Case.test_two",
            ],
            list(run.call_args[0][0]),
        )

    def test_parallel_main_shards_the_pool_and_leaves_the_tail_for_last(self):
        child_environment = {"PATH": os.environ.get("PATH", "")}
        shardable = RUN_TESTS.REPO / "services/quote-cli/tests/test_quote_cli.py"
        quarantined = RUN_TESTS.REPO / "automation/tests/test_run_tests.py"
        tests = (shardable, quarantined)
        expected_names = RUN_TESTS.discovered_test_names(
            shardable.read_text(encoding="utf-8")
        )
        completed = subprocess.CompletedProcess(["python"], 0, stdout=b"")
        report = io.StringIO()

        with mock.patch.object(
            RUN_TESTS,
            "isolated_test_environment",
            return_value=child_environment,
        ):
            with mock.patch.object(RUN_TESTS, "configured_git_identity", return_value={}):
                with mock.patch.object(
                    RUN_TESTS,
                    "repository_test_files",
                    return_value=tests,
                ):
                    with mock.patch.object(
                        RUN_TESTS,
                        "test_support_paths",
                        return_value=(),
                    ):
                        with mock.patch.object(RUN_TESTS, "validate_scratch_root"):
                            with mock.patch.object(
                                RUN_TESTS,
                                "materialize_repository_view",
                            ):
                                with mock.patch.object(
                                    RUN_TESTS.subprocess,
                                    "run",
                                    return_value=completed,
                                ) as run:
                                    with contextlib.redirect_stdout(report):
                                        self.assertEqual(
                                            0,
                                            RUN_TESTS.main(("--jobs", "4")),
                                        )

        printed = report.getvalue()
        commands = [list(call[0][0]) for call in run.call_args_list]
        self.assertIn("test workers: 4", printed)
        self.assertIn("test shards: 1", printed)
        self.assertIn("serial tail: automation/tests/test_run_tests.py", printed)
        self.assertIn("PASS services/quote-cli/tests/test_quote_cli.py", printed)
        self.assertIn("PASS automation/tests/test_run_tests.py", printed)
        self.assertIn("tests: 2/2 files passed", printed)
        self.assertEqual(2, len(commands))
        self.assertTrue(
            commands[0][1].endswith("services/quote-cli/tests/test_quote_cli.py"),
        )
        self.assertEqual(list(expected_names), commands[0][2:])
        self.assertTrue(
            commands[-1][1].endswith("automation/tests/test_run_tests.py"),
            "the quarantined file runs after every shard, never beside one",
        )
        self.assertEqual(
            2,
            len(commands[-1]),
            "the quarantined file runs whole, exactly as a serial run runs it",
        )

    def test_a_failing_shard_fails_the_file_and_the_process(self):
        child_environment = {"PATH": os.environ.get("PATH", "")}
        tests = (RUN_TESTS.REPO / "automation/tests/test_probe.py",)
        failure = subprocess.CompletedProcess(
            ["python"],
            1,
            stdout=b"FAIL: test_one (__main__.Case)\n",
        )
        report = io.StringIO()

        with mock.patch.object(
            RUN_TESTS,
            "isolated_test_environment",
            return_value=child_environment,
        ):
            with mock.patch.object(RUN_TESTS, "configured_git_identity", return_value={}):
                with mock.patch.object(
                    RUN_TESTS,
                    "repository_test_files",
                    return_value=tests,
                ):
                    with mock.patch.object(
                        RUN_TESTS,
                        "test_support_paths",
                        return_value=(),
                    ):
                        with mock.patch.object(RUN_TESTS, "validate_scratch_root"):
                            with mock.patch.object(
                                RUN_TESTS,
                                "materialize_repository_view",
                            ):
                                with mock.patch.object(
                                    RUN_TESTS.subprocess,
                                    "run",
                                    return_value=failure,
                                ):
                                    with contextlib.redirect_stdout(report):
                                        self.assertEqual(
                                            1,
                                            RUN_TESTS.main(("--jobs", "4")),
                                        )

        printed = report.getvalue()
        self.assertIn("FAIL: test_one (__main__.Case)", printed)
        self.assertIn("FAIL automation/tests/test_probe.py", printed)
        self.assertIn("tests: 0/1 files passed", printed)


class RunTestsIsolationTests(unittest.TestCase):
    def test_child_environment_removes_every_git_local_variable(self):
        factory = getattr(RUN_TESTS, "isolated_test_environment", None)
        self.assertIsNotNone(
            factory,
            "run_tests must expose the child-test environment boundary",
        )

        names = subprocess.check_output(
            ["git", "rev-parse", "--local-env-vars"],
            cwd=RUN_TESTS.REPO,
            text=True,
        ).splitlines()
        contaminated = {name: f"sentinel-{name}" for name in names}
        contaminated["GIT_CONFIG"] = "sentinel-config"
        contaminated["GIT_NAMESPACE"] = "sentinel-namespace"
        contaminated["GIT_PAGER"] = "sentinel-pager"
        contaminated["GIT_QUARANTINE_PATH"] = "sentinel-quarantine"
        contaminated["GIT_UNKNOWN_FUTURE_LOCAL"] = "sentinel-future"
        contaminated["AGENTFOLD_KEEP"] = "present"

        child = factory(contaminated)

        self.assertEqual("present", child["AGENTFOLD_KEEP"])
        self.assertTrue(names)
        self.assertFalse(
            any(
                name.startswith("GIT_")
                and name not in RUN_TESTS.SAFE_GIT_BEHAVIOR_VARIABLES
                for name in child
            )
        )

    def test_child_environment_sanitizes_the_real_ambient_environment(self):
        contaminated = {
            "GIT_DIR": "sentinel-dir",
            "GIT_INDEX_FILE": "sentinel-index",
            "AGENTFOLD_KEEP": "present",
        }

        with mock.patch.dict(os.environ, contaminated, clear=True):
            child = RUN_TESTS.isolated_test_environment()

        self.assertEqual("present", child["AGENTFOLD_KEEP"])
        self.assertNotIn("GIT_DIR", child)
        self.assertNotIn("GIT_INDEX_FILE", child)

    def test_child_environment_preserves_safe_git_behavior(self):
        contaminated = {
            "GIT_AUTHOR_NAME": "Test Author",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_DIR": "sentinel-dir",
        }

        child = RUN_TESTS.isolated_test_environment(contaminated)

        self.assertEqual("Test Author", child["GIT_AUTHOR_NAME"])
        self.assertEqual("test@example.invalid", child["GIT_COMMITTER_EMAIL"])
        self.assertEqual("0", child["GIT_TERMINAL_PROMPT"])
        self.assertNotIn("GIT_DIR", child)

    def test_configured_git_identity_resolves_only_name_and_email(self):
        responses = (
            subprocess.CompletedProcess(
                ["git", "config", "--get", "user.name"],
                0,
                stdout="Test Author\n",
                stderr="",
            ),
            subprocess.CompletedProcess(
                ["git", "config", "--get", "user.email"],
                0,
                stdout="test@example.invalid\n",
                stderr="",
            ),
        )

        with mock.patch.object(
            RUN_TESTS.subprocess,
            "run",
            side_effect=responses,
        ):
            identity = RUN_TESTS.configured_git_identity({"HOME": "/caller"})

        self.assertEqual(
            {
                "GIT_AUTHOR_NAME": "Test Author",
                "GIT_AUTHOR_EMAIL": "test@example.invalid",
                "GIT_COMMITTER_NAME": "Test Author",
                "GIT_COMMITTER_EMAIL": "test@example.invalid",
            },
            identity,
        )

    def test_git_local_variable_discovery_failure_stops_the_runner(self):
        discover = getattr(RUN_TESTS, "git_local_environment_names", None)
        self.assertIsNotNone(
            discover,
            "run_tests must expose fail-closed Git environment discovery",
        )
        failed = subprocess.CompletedProcess(
            ["git", "rev-parse", "--local-env-vars"],
            128,
            stdout="",
            stderr="fatal: not a git repository",
        )

        with mock.patch.object(RUN_TESTS.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "local environment variables"):
                discover()

    def test_empty_git_local_variable_discovery_stops_the_runner(self):
        empty = subprocess.CompletedProcess(
            ["git", "rev-parse", "--local-env-vars"],
            0,
            stdout="",
            stderr="",
        )

        with mock.patch.object(RUN_TESTS.subprocess, "run", return_value=empty):
            with self.assertRaisesRegex(RuntimeError, "discovery was empty"):
                RUN_TESTS.git_local_environment_names()

    def test_truncated_discovery_cannot_leak_unknown_git_variables(self):
        truncated = subprocess.CompletedProcess(
            ["git", "rev-parse", "--local-env-vars"],
            0,
            stdout="GIT_DIR\n",
            stderr="",
        )
        contaminated = {
            "GIT_CONFIG": "sentinel-config",
            "GIT_DIR": "sentinel-dir",
            "GIT_UNKNOWN_FUTURE_LOCAL": "sentinel-future",
            "KEEP": "present",
        }

        with mock.patch.object(RUN_TESTS.subprocess, "run", return_value=truncated):
            child = RUN_TESTS.isolated_test_environment(contaminated)

        self.assertEqual({"KEEP": "present"}, child)

    def test_scratch_root_rejects_a_path_separator(self):
        unsafe = Path(tempfile.gettempdir()) / f"agentfold{os.pathsep}unsafe"

        with self.assertRaisesRegex(RuntimeError, "discovery ceiling"):
            RUN_TESTS.validate_scratch_root(unsafe, {})

    def test_scratch_root_rejects_another_discovered_repository(self):
        with tempfile.TemporaryDirectory() as scratch:
            repository = Path(scratch) / "other-repository"
            child = repository / "test-scratch"
            repository.mkdir()
            child.mkdir()
            subprocess.run(
                ["git", "init", "-q", str(repository)],
                check=True,
                env={
                    name: value
                    for name, value in os.environ.items()
                    if not name.startswith("GIT_")
                },
            )

            with self.assertRaisesRegex(RuntimeError, "discover a Git repository"):
                RUN_TESTS.validate_scratch_root(
                    child,
                    {
                        name: value
                        for name, value in os.environ.items()
                        if not name.startswith("GIT_")
                    },
                )

    def test_scratch_root_fails_closed_on_an_unexpected_git_error(self):
        failed = subprocess.CompletedProcess(
            ["git", "rev-parse", "--git-dir"],
            1,
            stdout="",
            stderr="wrapper failure",
        )

        with tempfile.TemporaryDirectory() as scratch:
            with mock.patch.object(RUN_TESTS.subprocess, "run", return_value=failed):
                with self.assertRaisesRegex(RuntimeError, "could not verify"):
                    RUN_TESTS.validate_scratch_root(Path(scratch), {})

    def test_repository_view_preserves_paths_symlinks_and_ignores(self):
        with tempfile.TemporaryDirectory() as scratch:
            repository = Path(scratch) / "repository"
            destination = Path(scratch) / "view"
            global_home = Path(scratch) / "global-home"
            global_home.mkdir()
            global_excludes = global_home / "global-excludes"
            global_excludes.write_text("needed.fixture\n")
            (global_home / ".gitconfig").write_text(
                f"[core]\n\texcludesFile = {global_excludes}\n"
            )
            repository.mkdir()
            (repository / "fixtures/tmp").mkdir(parents=True)
            (repository / ".venv").mkdir()
            (repository / "generated/tests").mkdir(parents=True)
            nested_repository = repository / "vendor" / "nested \n"
            nested_repository.mkdir(parents=True)
            (repository / "objects/info").mkdir(parents=True)
            (repository / "refs/heads").mkdir(parents=True)
            (repository / ".gitignore").write_text(".venv/\ngenerated/\n")
            (repository / "HEAD").write_text("ref: refs/heads/main\n")
            (repository / "config").write_text("[core]\n\tbare = true\n")
            (repository / "objects/info/placeholder").write_text("bare-shaped\n")
            (repository / "refs/heads/main").write_text("0" * 40 + "\n")
            (repository / "fixtures/tmp/tracked.txt").write_text("tracked\n")
            (repository / "needed.fixture").write_text("needed\n")
            (repository / "untracked.txt").write_text("untracked\n")
            (repository / ".venv/ignored.txt").write_text("ignored\n")
            (repository / "generated/tests/test_ignored.py").write_text(
                "from helper import VALUE\nprint(VALUE)\n"
            )
            (repository / "generated/tests/helper.py").write_text(
                "VALUE = 'generated test'\n"
            )
            ignored_bare = repository / "generated/tests/bare-fixture"
            ignored_bare.mkdir()
            external_objects = Path(scratch) / "external-objects"
            external_objects.mkdir()
            bare_objects_symlinked = True
            try:
                os.symlink(
                    str(external_objects),
                    str(ignored_bare / "objects"),
                )
            except (NotImplementedError, OSError):
                bare_objects_symlinked = False
                (ignored_bare / "objects").mkdir()
            (ignored_bare / "refs").mkdir()
            (ignored_bare / "HEAD").write_text("ref: refs/heads/main\n")
            common_repository = Path(scratch) / "common-repository.git"
            subprocess.run(
                ["git", "init", "--bare", "-q", str(common_repository)],
                check=True,
                env={
                    name: value
                    for name, value in os.environ.items()
                    if not name.startswith("GIT_")
                },
            )
            linked_admin = repository / "generated/tests/linked-admin"
            linked_admin.mkdir()
            (linked_admin / "HEAD").write_text("ref: refs/heads/main\n")
            (linked_admin / "commondir").write_text(
                str(common_repository) + "\n"
            )
            (nested_repository / "tracked.txt").write_text("nested\n")
            symlinks_supported = True
            try:
                os.symlink("missing-target", str(repository / "broken-link"))
                os.symlink(".", str(repository / "loop"))
            except (NotImplementedError, OSError):
                symlinks_supported = False
            clean_environment = {
                name: value
                for name, value in os.environ.items()
                if not name.startswith("GIT_")
            }
            clean_environment["HOME"] = str(global_home)
            subprocess.run(
                ["git", "init", "-q", str(repository)],
                check=True,
                env=clean_environment,
            )
            subprocess.run(
                ["git", "init", "-q", str(nested_repository)],
                check=True,
                env=clean_environment,
            )
            subprocess.run(
                ["git", "-C", str(nested_repository), "add", "tracked.txt"],
                check=True,
                env=clean_environment,
            )
            tracked_paths = [
                ".gitignore",
                "HEAD",
                "config",
                "fixtures/tmp/tracked.txt",
                "objects/info/placeholder",
                "refs/heads/main",
            ]
            if symlinks_supported:
                tracked_paths.extend(("broken-link", "loop"))
            subprocess.run(
                ["git", "-C", str(repository), "add", *tracked_paths],
                check=True,
                env=clean_environment,
            )

            with mock.patch.object(RUN_TESTS, "REPO", repository):
                RUN_TESTS.materialize_repository_view(
                    destination,
                    clean_environment,
                    additional_paths=(
                        Path("generated/tests/bare-fixture/HEAD"),
                        Path("generated/tests/bare-fixture/objects"),
                        Path("generated/tests/bare-fixture/refs"),
                        Path("generated/tests/helper.py"),
                        Path("generated/tests/linked-admin/HEAD"),
                        Path("generated/tests/linked-admin/commondir"),
                        Path("generated/tests/test_ignored.py"),
                    ),
                )

            self.assertEqual(
                "tracked\n",
                (destination / "fixtures/tmp/tracked.txt").read_text(),
            )
            self.assertEqual("untracked\n", (destination / "untracked.txt").read_text())
            self.assertEqual(
                "needed\n",
                (destination / "needed.fixture").read_text(),
            )
            if symlinks_supported:
                self.assertTrue((destination / "broken-link").is_symlink())
                self.assertEqual(
                    "missing-target",
                    os.readlink(str(destination / "broken-link")),
                )
                self.assertTrue((destination / "loop").is_symlink())
                self.assertEqual(".", os.readlink(str(destination / "loop")))
            self.assertEqual(
                "nested\n",
                (destination / "vendor" / "nested \n" / "tracked.txt").read_text(),
            )
            nested_view = destination / "vendor" / "nested \n"
            self.assertFalse((nested_view / ".git").exists())
            subprocess.run(
                ["git", "init", "-q", str(nested_view)],
                check=True,
                env=clean_environment,
            )
            self.assertTrue((nested_view / ".git").is_dir())
            self.assertFalse((destination / ".venv").exists())
            self.assertEqual(
                "from helper import VALUE\nprint(VALUE)\n",
                (destination / "generated/tests/test_ignored.py").read_text(),
            )
            self.assertEqual(
                "VALUE = 'generated test'\n",
                (destination / "generated/tests/helper.py").read_text(),
            )
            self.assertEqual(
                RUN_TESTS.GIT_BOUNDARY_MARKER,
                (
                    destination
                    / "generated/tests/bare-fixture/.git"
                ).read_text(),
            )
            if bare_objects_symlinked:
                self.assertTrue(
                    (
                        destination
                        / "generated/tests/bare-fixture/objects"
                    ).is_symlink(),
                )
            nested_bare_git = subprocess.run(
                [
                    "git",
                    "-C",
                    str(destination / "generated/tests/bare-fixture"),
                    "rev-parse",
                    "--git-dir",
                ],
                env=clean_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, nested_bare_git.returncode)
            self.assertEqual(
                RUN_TESTS.GIT_BOUNDARY_MARKER,
                (
                    destination
                    / "generated/tests/linked-admin/.git"
                ).read_text(),
            )
            self.assertEqual(
                RUN_TESTS.GIT_BOUNDARY_MARKER,
                (destination / ".git").read_text(),
            )
            projected_git = subprocess.run(
                ["git", "-C", str(destination), "rev-parse", "--git-dir"],
                env=clean_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, projected_git.returncode)

    def test_symlinked_test_paths_cannot_escape_the_projected_view(self):
        with tempfile.TemporaryDirectory() as scratch:
            scratch_root = Path(scratch)
            repository = scratch_root / "repository"
            external = scratch_root / "external"
            destination = scratch_root / "view"
            repository.mkdir()
            external.mkdir()
            destination.mkdir()
            (external / "test_external.py").write_text("print('external')\n")
            try:
                os.symlink(str(external), str(repository / "linked-tests"))
                os.symlink(str(external), str(destination / "linked-tests"))
            except (NotImplementedError, OSError):
                self.skipTest("directory symlinks are unavailable")

            discovered = repository / "linked-tests" / "test_external.py"
            self.assertTrue(
                RUN_TESTS.path_crosses_symlink(discovered, repository),
            )
            with self.assertRaisesRegex(RuntimeError, "traversed a symlink"):
                RUN_TESTS.reject_projected_symlink_traversal(
                    destination,
                    Path("linked-tests/test_external.py"),
                )

    def test_ignored_test_support_includes_siblings_without_following_links(self):
        with tempfile.TemporaryDirectory() as scratch:
            repository = Path(scratch) / "repository"
            test_directory = repository / "automation/generated/tests"
            external = Path(scratch) / "external"
            test_directory.mkdir(parents=True)
            external.mkdir()
            test_file = test_directory / "test_generated.py"
            test_file.write_text("from helper import VALUE\n")
            (test_directory / "helper.py").write_text("VALUE = 1\n")
            (test_directory / ".GIT").write_text(
                "gitdir: /outside/original/worktree\n"
            )
            nested_git = test_directory / "fixture/.git"
            nested_git.mkdir(parents=True)
            (nested_git / "config").write_text("[core]\n\tbare = false\n")
            (external / "secret.py").write_text("SECRET = True\n")
            symlinks_supported = True
            try:
                os.symlink(str(external), str(test_directory / "linked"))
            except (NotImplementedError, OSError):
                symlinks_supported = False

            support = RUN_TESTS.test_support_paths(
                (test_file,),
                repository,
            )

            self.assertIn(
                Path("automation/generated/tests/test_generated.py"),
                support,
            )
            self.assertIn(
                Path("automation/generated/tests/helper.py"),
                support,
            )
            self.assertNotIn(
                Path("automation/generated/tests/.GIT"),
                support,
            )
            self.assertNotIn(
                Path("automation/generated/tests/fixture/.git/config"),
                support,
            )
            if symlinks_supported:
                self.assertIn(
                    Path("automation/generated/tests/linked"),
                    support,
                )
                self.assertNotIn(
                    Path("automation/generated/tests/linked/secret.py"),
                    support,
                )

    def test_nested_runner_isolation_stacks_no_interposed_git_on_path(self):
        with tempfile.TemporaryDirectory() as scratch:
            scratch_root = Path(scratch).resolve()
            caller_path = os.environ.get("PATH", "")
            first_environment = {"PATH": caller_path}
            RUN_TESTS.install_isolated_git_configuration(
                scratch_root / "first",
                first_environment,
            )
            original_git = shutil.which("git", path=first_environment["PATH"])

            second_environment = dict(first_environment)
            RUN_TESTS.install_isolated_git_configuration(
                scratch_root / "second",
                second_environment,
            )

            self.assertEqual(caller_path, first_environment["PATH"])
            self.assertEqual(caller_path, second_environment["PATH"])
            self.assertEqual(
                original_git,
                shutil.which("git", path=second_environment["PATH"]),
            )
            resolved = Path(original_git).resolve()
            self.assertTrue(os.access(str(resolved), os.X_OK))
            self.assertFalse(
                str(resolved).startswith(str(scratch_root)),
                "a nested runner must resolve Git outside every scratch root",
            )
            self.assertEqual([], sorted(scratch_root.rglob("git")))
            for name in ("HOME", "XDG_CONFIG_HOME"):
                first = Path(first_environment[name])
                second = Path(second_environment[name])
                self.assertNotEqual(first, second)
                self.assertEqual(scratch_root / "first", first.parent)
                self.assertEqual(scratch_root / "second", second.parent)
                self.assertEqual(
                    [],
                    [
                        entry
                        for entry in sorted(second.iterdir())
                        if str(entry) != second_environment["GIT_CONFIG_GLOBAL"]
                    ],
                    "only the runner's own global config may sit in a scratch config root",
                )

    def test_isolated_child_reads_no_caller_git_configuration(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch).resolve()
            caller_home = root / "caller-home"
            caller_xdg = root / "caller-xdg"
            (caller_xdg / "git").mkdir(parents=True)
            caller_home.mkdir()
            (caller_home / ".gitconfig").write_text(
                "[user]\n\tname = Caller Home Identity\n"
            )
            (caller_xdg / "git" / "config").write_text(
                "[user]\n\temail = caller-xdg@example.invalid\n"
            )
            caller_environment = {
                name: value
                for name, value in os.environ.items()
                if not name.startswith("GIT_")
            }
            caller_environment["HOME"] = str(caller_home)
            caller_environment["XDG_CONFIG_HOME"] = str(caller_xdg)
            child_environment = dict(caller_environment)
            RUN_TESTS.install_isolated_git_configuration(
                root / "runner-scratch",
                child_environment,
            )

            def read(*arguments, environment):
                return subprocess.run(
                    ["git", *arguments],
                    cwd=str(root),
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                )

            self.assertEqual(
                "Caller Home Identity",
                read(
                    "config",
                    "--get",
                    "user.name",
                    environment=caller_environment,
                ).stdout.strip(),
            )
            self.assertEqual(
                "caller-xdg@example.invalid",
                read(
                    "config",
                    "--get",
                    "user.email",
                    environment=caller_environment,
                ).stdout.strip(),
            )
            for key in ("user.name", "user.email"):
                isolated = read(
                    "config",
                    "--get",
                    key,
                    environment=child_environment,
                )
                self.assertEqual(1, isolated.returncode, isolated.stderr)
                self.assertEqual("", isolated.stdout)
            listing = read(
                "config",
                "--list",
                "--show-origin",
                environment=child_environment,
            )
            self.assertNotIn(str(caller_home), listing.stdout)
            self.assertNotIn(str(caller_xdg), listing.stdout)
            system = read("config", "--system", "--list", environment=caller_environment)
            names = [
                line.split("=", 1)[0]
                for line in system.stdout.splitlines()
                if "=" in line and not line.startswith("include.")
            ]
            for name in [name for name in names if names.count(name) == 1]:
                if read(
                    "config",
                    "--get",
                    name,
                    environment=caller_environment,
                ).returncode:
                    continue
                isolated = read(
                    "config",
                    "--get",
                    name,
                    environment=child_environment,
                )
                self.assertEqual(1, isolated.returncode, isolated.stderr)
                self.assertEqual("", isolated.stdout)
                break

    def test_isolated_child_git_runs_no_background_maintenance(self):
        """Every temp repository a test builds must inherit maintenance being off.

        Since Git 2.30 a commit detaches `git maintenance run --auto`, whose child
        creates `<objects-dir>/maintenance.lock` after the foreground command already
        returned — a writer inside `.git/objects` racing temp-directory teardown.
        Reading the keys back through Git itself is the only proof that carries: the
        settings live in a file that Git 2.32+ would ignore were `GIT_CONFIG_GLOBAL`
        still pointed at `os.devnull`.
        """
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch).resolve()
            child_environment = {
                name: value
                for name, value in os.environ.items()
                if not name.startswith("GIT_")
            }
            RUN_TESTS.install_isolated_git_configuration(
                root / "runner-scratch",
                child_environment,
            )
            self.assertIn(
                str(root / "runner-scratch"),
                child_environment["GIT_CONFIG_GLOBAL"],
                "the runner's global config must live inside its own scratch root",
            )
            for key, expected in (
                ("gc.auto", "0"),
                ("gc.autoDetach", "false"),
                ("maintenance.auto", "false"),
                ("maintenance.autoDetach", "false"),
            ):
                seen = subprocess.run(
                    ["git", "config", "--get", key],
                    cwd=str(root),
                    env=child_environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                )
                self.assertEqual(0, seen.returncode, f"{key}: {seen.stderr}")
                self.assertEqual(expected, seen.stdout.strip(), key)

    def test_isolated_scratch_tmpdir_redirects_child_fixture_repositories(self):
        """A killed run must leave at most one named directory, not hundreds.

        Every repository fixture a test builds calls ``tempfile.mkdtemp()`` or
        ``tempfile.TemporaryDirectory()`` with no ``dir=``, which resolves through
        ``tempfile.gettempdir()`` in that child process. Proving the dict carries the
        right keys is not enough -- a child process must actually honor them. Spawning
        real Python and asking it where fresh temp state lands is the only proof that
        a killed worker's fixture directories end up under this run's own scratch root
        instead of scattered anonymously across the real system temp directory.
        """
        with tempfile.TemporaryDirectory() as scratch:
            scratch_root = Path(scratch).resolve()
            child_environment = dict(os.environ)
            RUN_TESTS.install_isolated_scratch_tmpdir(scratch_root, child_environment)

            for name in ("TMPDIR", "TMP", "TEMP"):
                self.assertEqual(
                    str(scratch_root / "tmp"),
                    child_environment[name],
                    f"{name} must point inside this run's own scratch root",
                )
            self.assertTrue((scratch_root / "tmp").is_dir())

            seen = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import tempfile; print(tempfile.mkdtemp())",
                ],
                env=child_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(0, seen.returncode, seen.stderr)
            created = Path(seen.stdout.strip())
            self.assertEqual(scratch_root / "tmp", created.parent)
            shutil.rmtree(str(created))

    def test_main_passes_the_isolated_environment_to_each_test(self):
        child_environment = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": "/caller/home",
            "XDG_CONFIG_HOME": "/caller/xdg",
        }
        completed = subprocess.CompletedProcess(["python", "test.py"], 0)
        relative_test = Path("automation/tests/test_probe.py")

        with mock.patch.object(
            RUN_TESTS,
            "isolated_test_environment",
            return_value=child_environment,
            create=True,
        ):
            with mock.patch.object(RUN_TESTS, "configured_git_identity", return_value={}):
                with mock.patch.object(
                    RUN_TESTS,
                    "repository_test_files",
                    return_value=(
                        RUN_TESTS.REPO / "automation/tests/test_probe.py",
                    ),
                ):
                    with mock.patch.object(
                        RUN_TESTS,
                        "test_support_paths",
                        return_value=(relative_test,),
                    ):
                        with mock.patch.object(RUN_TESTS, "validate_scratch_root"):
                            with mock.patch.object(
                                RUN_TESTS,
                                "materialize_repository_view",
                            ):
                                with mock.patch.object(
                                    RUN_TESTS.subprocess,
                                    "run",
                                    return_value=completed,
                                ) as run:
                                    self.assertEqual(
                                        0,
                                        RUN_TESTS.main(("--jobs", "1")),
                                    )

        self.assertEqual(
            [sys.executable, run.call_args[0][0][1]],
            list(run.call_args[0][0]),
            "one worker must keep the historical argument-free invocation",
        )
        self.assertIs(child_environment, run.call_args[1]["env"])
        test_cwd = Path(run.call_args[1]["cwd"]).resolve()
        self.assertNotEqual(RUN_TESTS.REPO, test_cwd)
        self.assertNotIn(RUN_TESTS.REPO, test_cwd.parents)
        self.assertEqual(
            str(test_cwd.parent),
            child_environment["GIT_CEILING_DIRECTORIES"],
        )
        self.assertEqual(
            str(test_cwd / relative_test),
            run.call_args[0][0][1],
        )
        self.assertNotEqual(
            str(RUN_TESTS.REPO / relative_test),
            run.call_args[0][0][1],
        )
        scratch_root = test_cwd.parent
        self.assertEqual(
            str(scratch_root / "git-home" / ".gitconfig"),
            child_environment["GIT_CONFIG_GLOBAL"],
        )
        self.assertEqual("1", child_environment["GIT_CONFIG_NOSYSTEM"])
        self.assertEqual(
            str(scratch_root / "git-home"),
            child_environment["HOME"],
        )
        self.assertEqual(
            str(scratch_root / "git-xdg-config"),
            child_environment["XDG_CONFIG_HOME"],
        )
        for name in ("TMPDIR", "TMP", "TEMP"):
            self.assertEqual(
                str(scratch_root / "tmp"),
                child_environment[name],
                f"{name} must redirect fixture scratch dirs under the run's own root",
            )
        self.assertEqual(
            os.environ.get("PATH", ""),
            child_environment["PATH"],
            "Git must resolve from the caller's PATH, never an interposed wrapper",
        )

    def test_main_materializes_one_view_for_every_discovered_test(self):
        child_environment = {"PATH": os.environ.get("PATH", "")}
        tests = [
            RUN_TESTS.REPO / "automation/tests/test_first.py",
            RUN_TESTS.REPO / "automation/tests/test_second.py",
        ]
        completed = subprocess.CompletedProcess(["python", "test.py"], 0)

        with mock.patch.object(
            RUN_TESTS,
            "isolated_test_environment",
            return_value=child_environment,
        ):
            with mock.patch.object(RUN_TESTS, "configured_git_identity", return_value={}):
                with mock.patch.object(
                    RUN_TESTS,
                    "repository_test_files",
                    return_value=tuple(tests),
                ):
                    with mock.patch.object(
                        RUN_TESTS,
                        "test_support_paths",
                        return_value=tuple(
                            test.relative_to(RUN_TESTS.REPO) for test in tests
                        ),
                    ):
                        with mock.patch.object(RUN_TESTS, "validate_scratch_root"):
                            with mock.patch.object(
                                RUN_TESTS,
                                "materialize_repository_view",
                            ) as materialize:
                                with mock.patch.object(
                                    RUN_TESTS.subprocess,
                                    "run",
                                    return_value=completed,
                                ) as run:
                                    self.assertEqual(
                                        0,
                                        RUN_TESTS.main(("--jobs", "1")),
                                    )

        materialize.assert_called_once()
        self.assertEqual(
            (
                Path("automation/tests/test_first.py"),
                Path("automation/tests/test_second.py"),
            ),
            materialize.call_args[1]["additional_paths"],
        )
        self.assertEqual(2, run.call_count)
        self.assertEqual(
            run.call_args_list[0][1]["cwd"],
            run.call_args_list[1][1]["cwd"],
        )

    def test_main_does_not_run_hooks_from_the_callers_global_git_config(self):
        with tempfile.TemporaryDirectory() as scratch:
            scratch_root = Path(scratch)
            caller_home = scratch_root / "caller-home"
            hooks = scratch_root / "hooks"
            marker = scratch_root / "global-hook-ran"
            caller_home.mkdir()
            hooks.mkdir()
            pre_commit = hooks / "pre-commit"
            pre_commit.write_text(
                "#!/bin/sh\n"
                f"printf triggered > {marker}\n"
            )
            pre_commit.chmod(0o755)
            config_environment = {
                name: value
                for name, value in os.environ.items()
                if not name.startswith("GIT_")
            }
            config_environment["HOME"] = str(caller_home)
            subprocess.run(
                ["git", "config", "--global", "core.hooksPath", str(hooks)],
                check=True,
                env=config_environment,
            )
            subprocess.run(
                ["git", "config", "--global", "user.name", "Caller Identity"],
                check=True,
                env=config_environment,
            )
            subprocess.run(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "caller@example.invalid",
                ],
                check=True,
                env=config_environment,
            )
            child_environment = dict(config_environment)
            relative_test = Path("automation/tests/test_git_init_probe.py")
            discovered_test = RUN_TESTS.REPO / relative_test

            def materialize(destination, _environment, additional_paths=()):
                self.assertEqual((relative_test,), additional_paths)
                projected_test = destination / relative_test
                projected_test.parent.mkdir(parents=True)
                projected_test.write_text(
                    "import subprocess\n"
                    "from pathlib import Path\n"
                    "repository = Path('child-repository')\n"
                    "subprocess.run(['git', 'init', '-q', str(repository)], check=True)\n"
                    "subprocess.run([\n"
                    "    'git', '-C', str(repository),\n"
                    "    'commit', '--allow-empty', '-qm', 'probe',\n"
                    "], check=True)\n"
                )

            with mock.patch.dict(os.environ, child_environment, clear=True):
                with mock.patch.object(
                    RUN_TESTS,
                    "repository_test_files",
                    return_value=(discovered_test,),
                ):
                    with mock.patch.object(
                        RUN_TESTS,
                        "test_support_paths",
                        return_value=(relative_test,),
                    ):
                        with mock.patch.object(RUN_TESTS, "validate_scratch_root"):
                            with mock.patch.object(
                                RUN_TESTS,
                                "materialize_repository_view",
                                side_effect=materialize,
                            ):
                                self.assertEqual(0, RUN_TESTS.main())

            self.assertFalse(marker.exists())

    def test_metadata_probe_runs_only_for_directories_with_head_entries(self):
        with tempfile.TemporaryDirectory() as scratch:
            destination = Path(scratch) / "view"
            for index in range(100):
                (destination / f"ordinary-{index}").mkdir(parents=True)
            candidate = destination / "candidate"
            candidate.mkdir()
            (candidate / "HEAD").write_text("ref: refs/heads/main\n")

            with mock.patch.object(
                RUN_TESTS,
                "seal_bare_repository_view",
            ) as seal:
                RUN_TESTS.seal_bare_repository_views(destination, {})

            seal.assert_called_once_with(candidate, {})

    def test_runner_recurses_from_a_metadata_free_projected_view(self):
        with tempfile.TemporaryDirectory() as scratch:
            projection = Path(scratch) / "projection"
            automation = projection / "automation"
            test_directory = automation / "tests"
            test_directory.mkdir(parents=True)
            projected_runner = automation / "run_tests.py"
            projected_runner.write_text(MODULE_PATH.read_text())
            (test_directory / "test_probe.py").write_text(
                "from pathlib import Path\n"
                "assert not (Path(__file__).parents[2] / '.git').exists()\n"
            )
            environment = {
                name: value
                for name, value in os.environ.items()
                if not name.startswith("GIT_")
            }
            environment[RUN_TESTS.PROJECTED_REPOSITORY_ENVIRONMENT] = str(
                projection
            )

            result = subprocess.run(
                [os.sys.executable, str(projected_runner)],
                cwd=projection,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("tests: 1/1 files passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
