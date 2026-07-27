import importlib.util
import os
import subprocess
import tempfile
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
            ["git", "diff", "--cached", "--name-status", "-z", "-M"],
            run.call_args_list[1][0][0],
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

    def test_every_non_add_modify_status_falls_back_to_the_full_suite(self):
        cases = (
            b"D\0services/quote-cli/quote_cli.py\0",
            b"T\0services/quote-cli/quote_cli.py\0",
            (
                b"R100\0services/quote-cli/old.py\0"
                b"services/quote-cli/new.py\0"
            ),
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

    def test_cross_cutting_or_unknown_service_path_falls_back(self):
        for path in (
            b"automation/run_tests.py",
            b"services/unknown/service.py",
            b"services/quote-api",
            b"docs/speed.md",
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

    def test_default_interface_is_the_full_suite(self):
        options = RUN_TESTS.parse_arguments(())
        selection = RUN_TESTS.full_selection(self.all_tests, "full suite requested")

        self.assertFalse(options.staged)
        self.assertEqual("full", selection.lane)
        self.assertEqual(self.all_tests, selection.test_files)

    def test_pre_commit_requests_the_staged_lane(self):
        hook = (RUN_TESTS.REPO / "automation/hooks/pre-commit").read_text()

        self.assertIn('automation/run_test_gate.py" routine --staged', hook)

    def test_explicit_view_requires_safe_discovered_test_paths(self):
        with tempfile.TemporaryDirectory() as scratch:
            view = Path(scratch)
            (view / "automation/tests").mkdir(parents=True)
            test = view / "automation/tests/test_probe.py"
            test.write_text("pass\n")

            options = RUN_TESTS.parse_arguments(
                ("--view-root", str(view), "--test-file", "automation/tests/test_probe.py")
            )

            self.assertEqual(view, options.view_root)
            self.assertEqual(["automation/tests/test_probe.py"], options.test_file)

    def test_explicit_test_file_can_use_the_normal_isolated_runner_view(self):
        options = RUN_TESTS.parse_arguments(
            ("--test-file", "automation/tests/test_run_test_gate.py")
        )

        self.assertIsNone(options.view_root)
        self.assertEqual(["automation/tests/test_run_test_gate.py"], options.test_file)

    def test_provider_hard_requires_an_explicit_view_and_manifest(self):
        with self.assertRaises(SystemExit):
            RUN_TESTS.parse_arguments(("--provider-hard",))

        options = RUN_TESTS.parse_arguments(
            (
                "--provider-hard",
                "--view-root",
                "/tmp/candidate",
                "--test-file",
                "automation/tests/test_probe.py",
            )
        )
        self.assertTrue(options.provider_hard)

    def test_staged_and_explicit_view_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            RUN_TESTS.parse_arguments(("--staged", "--view-root", "/tmp/view"))

    def test_name_status_parser_handles_nul_delimited_special_paths(self):
        entries = RUN_TESTS.parse_staged_name_status(
            b"M\0services/quote-cli/line\nname.py\0"
        )

        self.assertEqual(
            (("M", (b"services/quote-cli/line\nname.py",)),),
            entries,
        )


class RunTestsIsolationTests(unittest.TestCase):
    def test_provider_view_is_made_nonwritable_without_changing_executability(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "view"
            root.mkdir()
            ordinary = root / "ordinary.py"
            executable = root / "executable.py"
            ordinary.write_text("pass\n")
            executable.write_text("pass\n")
            executable.chmod(0o755)

            RUN_TESTS.seal_provider_test_view(root)

            self.assertEqual(0o444, ordinary.stat().st_mode & 0o777)
            self.assertEqual(0o555, executable.stat().st_mode & 0o777)
            self.assertEqual(0o555, root.stat().st_mode & 0o777)

            RUN_TESTS.restore_provider_test_view(root)

            self.assertEqual(0o644, ordinary.stat().st_mode & 0o777)
            self.assertEqual(0o755, executable.stat().st_mode & 0o777)
            self.assertEqual(0o755, root.stat().st_mode & 0o777)

    def test_provider_scratch_does_not_require_the_absent_chown_capability(self):
        with tempfile.TemporaryDirectory() as scratch, mock.patch.object(
            RUN_TESTS.os,
            "chown",
            side_effect=AssertionError("provider root must not require CAP_CHOWN"),
        ):
            home, temporary = RUN_TESTS.prepare_provider_candidate_scratch(
                Path(scratch) / "state"
            )
            self.assertEqual(0o777, home.stat().st_mode & 0o777)
            self.assertEqual(0o777, temporary.stat().st_mode & 0o777)

    def test_provider_candidate_environment_is_explicitly_allowlisted(self):
        environment = RUN_TESTS.provider_candidate_environment(
            {
                "PATH": "/untrusted/path",
                "LANG": "C.UTF-8",
                "GITHUB_TOKEN": "secret",
                "PYTHONWARNINGS": "error",
                "PYTHON_CREDENTIAL": "also-secret",
                "UNRELATED": "secret",
            },
            Path("/work/view"),
            Path("/work/state/home"),
            Path("/work/state/tmp"),
        )

        self.assertEqual("/usr/local/bin:/usr/bin:/bin", environment["PATH"])
        self.assertEqual("/work/state/home", environment["HOME"])
        self.assertEqual("/work/state/tmp", environment["TMPDIR"])
        self.assertEqual("error", environment["PYTHONWARNINGS"])
        self.assertNotIn("GITHUB_TOKEN", environment)
        self.assertNotIn("PYTHON_CREDENTIAL", environment)
        self.assertNotIn("UNRELATED", environment)

    def test_provider_launcher_probes_identity_capabilities_and_no_new_privs(self):
        launcher = RUN_TESTS.PROVIDER_TEST_LAUNCHER
        self.assertIn("os.getuid() != 65532", launcher)
        self.assertIn('(\"CapEff\", \"CapPrm\", \"CapAmb\")', launcher)
        self.assertIn('status.get("NoNewPrivs") != "1"', launcher)
        self.assertIn('os.access(str(view), os.W_OK)', launcher)
        self.assertIn("pathlib.Path(sys.argv[2]).resolve()", launcher)
        self.assertIn("pathlib.Path(sys.argv[3]).resolve()", launcher)
        self.assertNotIn('os.environ["HOME"]', launcher)

    def test_provider_runner_uses_trusted_drop_and_fails_on_leaked_uid(self):
        process = mock.Mock(pid=123, args=["python"])
        process.wait.return_value = 0
        with mock.patch.object(
            RUN_TESTS.subprocess, "Popen", return_value=process
        ) as popen, mock.patch.object(
            RUN_TESTS, "cleanup_provider_candidate_processes", return_value={456}
        ), mock.patch.object(RUN_TESTS.os, "killpg"):
            result = RUN_TESTS.run_provider_test(
                Path("/view/test_probe.py"),
                Path("/view"),
                {"PATH": "/bin"},
                Path("/state/home"),
                Path("/state/tmp"),
            )

        self.assertEqual(1, result.returncode)
        self.assertIs(
            RUN_TESTS._drop_to_provider_candidate,
            popen.call_args[1]["preexec_fn"],
        )
        self.assertTrue(popen.call_args[1]["start_new_session"])
        self.assertEqual("/state/home", popen.call_args[0][0][-2])
        self.assertEqual("/state/tmp", popen.call_args[0][0][-1])

    def test_captured_view_drops_only_the_fixed_empty_root_git_sentinel(self):
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "source"
            destination = Path(scratch) / "destination"
            source.mkdir()
            (source / ".git").mkdir()
            (source / "candidate.txt").write_text("candidate\n")

            RUN_TESTS.materialize_captured_view(source, destination, {})

            self.assertEqual("candidate\n", (destination / "candidate.txt").read_text())
            self.assertFalse((destination / ".git").exists())

    def test_captured_view_rejects_nonempty_or_nested_git_metadata(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            for name in ("nonempty", "nested"):
                with self.subTest(name=name):
                    source = root / name
                    source.mkdir()
                    sentinel = (
                        source / ".git" if name == "nonempty" else source / "nested/.git"
                    )
                    sentinel.mkdir(parents=True)
                    (sentinel / "config").write_text("[core]\n")
                    with self.assertRaisesRegex(RuntimeError, "Git metadata"):
                        RUN_TESTS.materialize_captured_view(
                            source, root / f"{name}-destination", {}
                        )

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

    def test_nested_runner_wrapper_reuses_the_original_git_executable(self):
        with tempfile.TemporaryDirectory() as scratch:
            scratch_root = Path(scratch)
            first_environment = {"PATH": os.environ.get("PATH", "")}
            RUN_TESTS.install_isolated_git_wrapper(
                scratch_root / "first",
                first_environment,
            )
            original_git = first_environment[RUN_TESTS.REAL_GIT_ENVIRONMENT]
            first_wrapper = first_environment["PATH"].split(os.pathsep, 1)[0]

            second_environment = dict(first_environment)
            RUN_TESTS.install_isolated_git_wrapper(
                scratch_root / "second",
                second_environment,
            )

            self.assertEqual(
                original_git,
                second_environment[RUN_TESTS.REAL_GIT_ENVIRONMENT],
            )
            second_wrapper = second_environment["PATH"].split(os.pathsep, 1)[0]
            self.assertNotEqual(first_wrapper, second_wrapper)
            self.assertIn(
                original_git,
                (Path(second_wrapper) / "git").read_text(),
            )

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
                                    self.assertEqual(0, RUN_TESTS.main())

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
        self.assertEqual(os.devnull, child_environment["GIT_CONFIG_GLOBAL"])
        self.assertEqual("1", child_environment["GIT_CONFIG_NOSYSTEM"])
        self.assertEqual("/caller/home", child_environment["HOME"])
        self.assertEqual("/caller/xdg", child_environment["XDG_CONFIG_HOME"])

    def test_main_materializes_a_fresh_view_for_each_discovered_test(self):
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
                                    self.assertEqual(0, RUN_TESTS.main())

        self.assertEqual(2, materialize.call_count)
        for call in materialize.call_args_list:
            self.assertEqual(
                (
                    Path("automation/tests/test_first.py"),
                    Path("automation/tests/test_second.py"),
                ),
                call[1]["additional_paths"],
            )
        self.assertEqual(2, run.call_count)
        self.assertNotEqual(
            run.call_args_list[0][1]["cwd"],
            run.call_args_list[1][1]["cwd"],
        )

    def test_earlier_test_cannot_rewrite_later_test_input(self):
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "captured"
            tests = source / "automation/tests"
            tests.mkdir(parents=True)
            first = tests / "test_first.py"
            second = tests / "test_second.py"
            first.write_text(
                "from pathlib import Path\n"
                "Path('automation/tests/test_second.py').write_text('pass\\n')\n"
            )
            second.write_text("raise AssertionError('original failure must run')\n")

            result = RUN_TESTS.main(
                (
                    "--view-root",
                    str(source),
                    "--test-file",
                    "automation/tests/test_first.py",
                    "--test-file",
                    "automation/tests/test_second.py",
                )
            )

        self.assertEqual(1, result)

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
