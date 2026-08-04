"""Real linked-worktree tests for the repository bootstrap installer."""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


INSTALLER = Path(__file__).resolve().parents[1] / "install.py"
INSTALLER_SPEC = importlib.util.spec_from_file_location("agentfold_install", INSTALLER)
INSTALL = importlib.util.module_from_spec(INSTALLER_SPEC)
INSTALLER_SPEC.loader.exec_module(INSTALL)
STARTER = """\
import os
import pathlib
import sys
import time

ready = pathlib.Path(sys.argv[1])
start = pathlib.Path(sys.argv[2])
script = sys.argv[3]
ready.touch()
while not start.exists():
    time.sleep(0.001)
os.execv(sys.executable, [sys.executable, script])
"""


def clean_environment():
    return {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("GIT_")
    }


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.scratch_context = tempfile.TemporaryDirectory(
            prefix="agentfold-install-"
        )
        self.scratch = Path(self.scratch_context.name).resolve()
        self.repository = self.scratch / "repository"
        self.initialize_repository()

    def tearDown(self):
        self.scratch_context.cleanup()

    def git(self, root, *arguments, check=True):
        return subprocess.run(
            ["git", *map(str, arguments)],
            cwd=str(root),
            check=check,
            env=clean_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    def initialize_repository(self):
        self.repository.mkdir()
        self.git(self.repository, "init", "-q")

        files = {
            ".gitignore": "CLAUDE.md\n.claude/\n.cursor/\n.agents/\n",
            "AGENTS.md": "# Root contract\n",
            "component/AGENTS.md": "# Component contract\n",
            "skills/example/SKILL.md": "# Example skill\n",
            "automation/hooks/pre-commit": "#!/bin/sh\nexit 0\n",
        }
        for name, body in files.items():
            path = self.repository / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        shutil.copy2(str(INSTALLER), str(self.repository / "automation/install.py"))
        (self.repository / "automation/hooks/pre-commit").chmod(0o755)
        self.git(self.repository, "add", "-A")
        self.git(
            self.repository,
            "-c", "user.name=Bootstrap Test",
            "-c", "user.email=bootstrap@example.invalid",
            "-c", "core.hooksPath=.git/no-hooks",
            "commit", "-qm", "fixture",
        )

    def add_worktrees(self, count):
        worktrees = []
        for index in range(count):
            worktree = self.scratch / "worktree-{0}".format(index)
            self.git(
                self.repository,
                "worktree", "add", "-q", "--detach", worktree,
            )
            worktrees.append(worktree)
        return worktrees

    def run_installer(self, root, environment=None):
        return subprocess.run(
            [sys.executable, str(root / "automation/install.py")],
            cwd=str(root),
            env=clean_environment() if environment is None else environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    def run_concurrently(self, roots):
        gate = self.scratch / "gate-{0}".format(time.time_ns())
        gate.mkdir()
        start = gate / "start"
        processes = []
        for index, root in enumerate(roots):
            ready = gate / "ready-{0}".format(index)
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    STARTER,
                    str(ready),
                    str(start),
                    str(root / "automation/install.py"),
                ],
                cwd=str(root),
                env=clean_environment(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            processes.append(process)

        deadline = time.monotonic() + 10
        while len(list(gate.glob("ready-*"))) != len(processes):
            if time.monotonic() >= deadline:
                self.fail("concurrent installer processes did not reach the start gate")
            time.sleep(0.005)
        start.touch()
        return [process.communicate(timeout=15) + (process.returncode,)
                for process in processes]

    def git_path(self, root, argument):
        value = self.git(root, "rev-parse", argument).stdout.strip()
        path = Path(value)
        if not path.is_absolute():
            path = root / path
        return path.resolve()

    def assert_valid_adapters(self, root):
        claude = root / "component/CLAUDE.md"
        self.assertTrue(claude.is_symlink())
        self.assertEqual("AGENTS.md", os.readlink(str(claude)))
        self.assertEqual(
            (root / "component/AGENTS.md").resolve(),
            claude.resolve(),
        )
        for adapter in (".claude", ".cursor", ".agents"):
            link = root / adapter / "skills/example"
            self.assertTrue(link.is_symlink())
            self.assertEqual("../../skills/example", os.readlink(str(link)))
            self.assertEqual((root / "skills/example").resolve(), link.resolve())

    def test_six_fresh_and_twelve_repeated_concurrent_linked_worktree_installs(self):
        worktrees = self.add_worktrees(6)
        common_dirs = {self.git_path(root, "--git-common-dir") for root in worktrees}
        local_dirs = {self.git_path(root, "--git-dir") for root in worktrees}
        self.assertEqual({(self.repository / ".git").resolve()}, common_dirs)
        self.assertEqual(6, len(local_dirs))
        self.assertTrue(all(path.parent == self.repository / ".git/worktrees"
                            for path in local_dirs))

        fresh_results = self.run_concurrently(worktrees)
        for stdout, stderr, returncode in fresh_results:
            self.assertEqual(0, returncode, stdout + stderr)
        self.assertEqual(
            "automation/hooks",
            self.git(worktrees[0], "config", "--local", "--get",
                     "core.hooksPath").stdout.strip(),
        )
        for root in worktrees:
            self.assert_valid_adapters(root)
        self.assertTrue(all(not (path / "config.worktree").exists()
                            for path in local_dirs))

        repeated_results = self.run_concurrently([worktrees[0]] * 12)
        for stdout, stderr, returncode in repeated_results:
            self.assertEqual(0, returncode, stdout + stderr)
            self.assertIn("already configured; no write", stdout)
        self.assert_valid_adapters(worktrees[0])

    def test_correct_shared_hook_config_is_not_rewritten(self):
        [worktree] = self.add_worktrees(1)
        self.git(
            worktree, "config", "--local", "core.hooksPath", "automation/hooks"
        )
        config_lock = self.repository / ".git/config.lock"
        config_lock.write_text("held by test\n", encoding="utf-8")
        try:
            result = self.run_installer(worktree)
        finally:
            config_lock.unlink()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("already configured; no write", result.stdout)
        self.assert_valid_adapters(worktree)

    def test_already_executable_hook_keeps_git_index_stat_cache_clean(self):
        [worktree] = self.add_worktrees(1)
        hook = worktree / "automation/hooks/pre-commit"
        self.assertEqual(0o111, hook.stat().st_mode & 0o111)
        self.assertEqual(
            0,
            self.git(worktree, "diff-files", "--quiet", check=False).returncode,
        )

        result = self.run_installer(worktree)

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        dirty = self.git(worktree, "diff-files", "--quiet", check=False)
        self.assertEqual(0, dirty.returncode, dirty.stdout + dirty.stderr)

    def test_worktree_hook_override_is_converged_without_rewriting_common_config(self):
        [worktree] = self.add_worktrees(1)
        self.git(
            self.repository,
            "config", "--local", "extensions.worktreeConfig", "yes",
        )
        self.git(
            worktree,
            "config", "--worktree", "core.hooksPath", "disabled/hooks",
        )

        first = self.run_installer(worktree)
        common_config = (self.repository / ".git/config").read_bytes()
        common_lock = self.repository / ".git/config.lock"
        common_lock.write_text("held by test\n", encoding="utf-8")
        try:
            second = self.run_installer(worktree)
        finally:
            common_lock.unlink()

        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        self.assertEqual(0, second.returncode, second.stdout + second.stderr)
        self.assertEqual(
            "automation/hooks",
            self.git(worktree, "config", "--get", "core.hooksPath").stdout.strip(),
        )
        self.assertEqual(
            "automation/hooks",
            self.git(worktree, "config", "--local", "--get",
                     "core.hooksPath").stdout.strip(),
        )
        self.assertEqual(
            "automation/hooks",
            self.git(worktree, "config", "--worktree", "--get",
                     "core.hooksPath").stdout.strip(),
        )
        self.assertEqual(common_config, (self.repository / ".git/config").read_bytes())
        self.assertIn("configured override", first.stdout)
        self.assertIn("already effective; no write", second.stdout)

    def test_temporary_shared_config_lock_is_retried_until_config_is_verified(self):
        [worktree] = self.add_worktrees(1)
        config_lock = self.repository / ".git/config.lock"
        config_lock.write_text("held by test\n", encoding="utf-8")
        process = subprocess.Popen(
            [sys.executable, str(worktree / "automation/install.py")],
            cwd=str(worktree),
            env=clean_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        time.sleep(0.15)
        try:
            self.assertIsNone(process.poll(), "installer did not retry config.lock")
        finally:
            config_lock.unlink()
        stdout, stderr = process.communicate(timeout=10)

        self.assertEqual(0, process.returncode, stdout + stderr)
        self.assertEqual(
            "automation/hooks",
            self.git(worktree, "config", "--local", "--get",
                     "core.hooksPath").stdout.strip(),
        )
        self.assert_valid_adapters(worktree)

    def test_persistent_shared_config_lock_never_reports_success(self):
        [worktree] = self.add_worktrees(1)
        config_lock = self.repository / ".git/config.lock"
        config_lock.write_text("held by test\n", encoding="utf-8")
        try:
            result = self.run_installer(worktree)
        finally:
            config_lock.unlink()

        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        missing = self.git(
            worktree,
            "config", "--local", "--get", "core.hooksPath",
            check=False,
        )
        self.assertEqual(1, missing.returncode, missing.stdout + missing.stderr)
        self.assertNotIn("git hooks (common repository)", result.stdout)
        self.assertNotIn("install: done", result.stdout)
        self.assertEqual(1, result.stderr.count("ERROR:"), result.stderr)
        self.assertIn("config.lock", result.stderr)

    def test_real_adapter_path_is_preserved_and_fails_with_one_actionable_error(self):
        [worktree] = self.add_worktrees(1)
        collision = worktree / "component/CLAUDE.md"
        collision.write_text("keep this user file\n", encoding="utf-8")

        result = self.run_installer(worktree)

        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual("keep this user file\n", collision.read_text(encoding="utf-8"))
        self.assertFalse(collision.is_symlink())
        self.assertEqual(1, result.stderr.count("ERROR:"), result.stderr)
        self.assertIn("component/CLAUDE.md", result.stderr)
        self.assertIn("move or remove", result.stderr)

    def test_stale_symlink_replaced_by_real_file_during_observation_is_preserved(self):
        link = self.scratch / "racing-adapter"
        link.symlink_to("stale-target")

        def replace_with_real_file(_link):
            link.unlink()
            link.write_text("actor-owned file\n", encoding="utf-8")
            return "stale-target"

        with mock.patch.object(
                INSTALL, "symlink_target", side_effect=replace_with_real_file):
            result = INSTALL.ensure_symlink(link, "correct-target")

        self.assertEqual(
            "symlink points to an unexpected target and was preserved",
            result,
        )
        self.assertFalse(link.is_symlink())
        self.assertEqual("actor-owned file\n", link.read_text(encoding="utf-8"))

    def test_symlink_creation_marks_only_skill_targets_as_directories(self):
        claude = self.scratch / "claude-link"
        skill = self.scratch / "skill-link"
        with mock.patch.object(Path, "symlink_to", autospec=True) as create:
            self.assertEqual(
                "ok",
                INSTALL.ensure_symlink(
                    claude, "AGENTS.md", target_is_directory=False
                ),
            )
            self.assertEqual(
                "ok",
                INSTALL.ensure_symlink(
                    skill, "../../skills/example", target_is_directory=True
                ),
            )

        self.assertEqual(
            [
                mock.call(claude, "AGENTS.md", target_is_directory=False),
                mock.call(
                    skill,
                    "../../skills/example",
                    target_is_directory=True,
                ),
            ],
            create.call_args_list,
        )


if __name__ == "__main__":
    unittest.main()
