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
                    str(ignored_bare / "OBJECTS"),
                )
            except (NotImplementedError, OSError):
                bare_objects_symlinked = False
                (ignored_bare / "OBJECTS").mkdir()
            (ignored_bare / "refs").mkdir()
            (ignored_bare / "head").write_text("ref: refs/heads/main\n")
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
                        Path("generated/tests/bare-fixture/OBJECTS"),
                        Path("generated/tests/bare-fixture/head"),
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
                        / "generated/tests/bare-fixture/OBJECTS"
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
                                    self.assertEqual(0, RUN_TESTS.main())

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


if __name__ == "__main__":
    unittest.main()
