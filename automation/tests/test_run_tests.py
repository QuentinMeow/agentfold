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
            nested_repository = repository / "vendor" / "nested \n"
            nested_repository.mkdir(parents=True)
            (repository / "objects/info").mkdir(parents=True)
            (repository / "refs/heads").mkdir(parents=True)
            (repository / ".gitignore").write_text(".venv/\n")
            (repository / "HEAD").write_text("ref: refs/heads/main\n")
            (repository / "config").write_text("[core]\n\tbare = true\n")
            (repository / "objects/info/placeholder").write_text("bare-shaped\n")
            (repository / "refs/heads/main").write_text("0" * 40 + "\n")
            (repository / "fixtures/tmp/tracked.txt").write_text("tracked\n")
            (repository / "needed.fixture").write_text("needed\n")
            (repository / "untracked.txt").write_text("untracked\n")
            (repository / ".venv/ignored.txt").write_text("ignored\n")
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

    def test_main_passes_the_isolated_environment_to_each_test(self):
        child_environment = {"PATH": os.environ.get("PATH", "")}
        completed = subprocess.CompletedProcess(["python", "test.py"], 0)

        with mock.patch.object(
            RUN_TESTS,
            "isolated_test_environment",
            return_value=child_environment,
            create=True,
        ):
            with mock.patch.object(
                RUN_TESTS.Path,
                "glob",
                return_value=[RUN_TESTS.REPO / "automation/tests/test_probe.py"],
            ):
                with mock.patch.object(RUN_TESTS, "validate_scratch_root"):
                    with mock.patch.object(RUN_TESTS, "materialize_repository_view"):
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


if __name__ == "__main__":
    unittest.main()
