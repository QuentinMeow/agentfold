#!/usr/bin/env python3
"""Focused regression tests for exact, budgeted test-gate orchestration."""

import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


AUTOMATION = Path(__file__).resolve().parents[1]
MODULE_PATH = AUTOMATION / "run_test_gate.py"
SPEC = importlib.util.spec_from_file_location("run_test_gate", MODULE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
MANIFEST = GATE.test_manifest
CONFIG = GATE.test_gate_config


class TestGateTests(unittest.TestCase):
    def _make_reconciler_topology_repository(self, destination):
        environment = {
            name: value for name, value in os.environ.items() if not name.startswith("GIT_")
        }
        destination.mkdir()
        for relative in (
            "automation/check_action_projection.py",
            "automation/markdown_semantics.py",
            "automation/reconcile/reconcile.py",
        ):
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(GATE.REPO / relative, target)
        linked_directories = []
        for index in range(84):
            relative = Path(f"schema/leaves/leaf-{index:03d}")
            linked_directories.append(relative)
            marker = destination / relative / "marker.txt"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("tracked structure\n")
        (destination / "README.md").write_text(
            "# Candidate topology fixture\n\n"
            + "\n".join(f"- `{path.as_posix()}/`" for path in linked_directories)
            + "\n"
        )
        service = destination / "services/example/data.txt"
        service.parent.mkdir(parents=True)
        service.write_text("base\n")
        subprocess.run(
            ["git", "init", "-q"],
            cwd=destination,
            env=environment,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=destination, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=destination,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=destination, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "valid harness baseline"],
            cwd=destination,
            check=True,
        )

    def _run_frozen_candidate_reconcile(self, repo, capture):
        options = mock.Mock(gate="routine", staged=True, provider_hard=False)
        with mock.patch.object(GATE, "REPO", repo):
            candidate, tested_view, candidate_root, _stable = GATE.capture_candidate(
                options, capture
            )
            command = GATE.admission_commands(options, candidate, candidate_root)[1][1]
            component_environment = GATE.candidate_git_environment(
                candidate_root, capture / "candidate.index"
            )
            result = GATE.run_component(
                "reconcile",
                command,
                15.0,
                cwd=candidate_root,
                internal_environment=component_environment,
            )
        return result, tested_view, candidate_root

    def test_cli_requires_staged_routine_and_explicit_final_trigger(self):
        with self.assertRaises(SystemExit):
            GATE.parse_arguments(("routine",))
        routine = GATE.parse_arguments(("routine", "--staged"))
        final = GATE.parse_arguments(("final", "--explicit"))
        staged_final = GATE.parse_arguments(("final", "--explicit", "--staged"))
        self.assertTrue(routine.staged)
        self.assertTrue(final.explicit)
        self.assertTrue(staged_final.staged)

    def test_routine_manifest_selects_owned_service_and_automation_tests(self):
        tests = (
            "services/quote-api/tests/test_quote_api.py",
            "services/quote-cli/tests/test_quote_cli.py",
            "automation/tests/test_run_tests.py",
            "automation/tests/test_reconcile_queue.py",
        )

        selected, deferred = GATE.routine_test_manifest(
            ("services/quote-api/quote_api.py", "automation/run_tests.py"), tests
        )

        self.assertEqual(
            (
                "automation/tests/test_run_tests.py",
                "services/quote-api/tests/test_quote_api.py",
                "services/quote-cli/tests/test_quote_cli.py",
            ),
            selected,
        )
        self.assertEqual(("automation/tests/test_reconcile_queue.py",), deferred)

    def test_unknown_routine_path_defers_every_test(self):
        selected, deferred = GATE.routine_test_manifest(
            ("unknown/file.py",), ("automation/tests/test_run_tests.py",)
        )
        self.assertEqual((), selected)
        self.assertEqual(("automation/tests/test_run_tests.py",), deferred)

    def test_manual_final_runs_only_when_explicit(self):
        policy = CONFIG.load_policy(GATE.REPO / "agentfold.toml")
        policy = CONFIG.TestGatePolicy(
            policy.schema_version,
            policy.routine,
            CONFIG.FinalGate("manual", None, policy.final.budget),
            policy.on_budget_exceeded,
            policy.critical_bindings,
            policy.reversible_bindings,
            policy.unmatched_is_critical,
        )
        named = GATE.parse_arguments(
            (
                "final",
                "--at-transition",
                "pull-request",
                "--base-revision",
                "base",
                "--head-revision",
                "head",
                "--candidate-revision",
                "candidate",
                "--branch",
                "task/example",
            )
        )
        explicit = GATE.parse_arguments(("final", "--explicit"))
        self.assertEqual("not-run", GATE._final_disposition(named, policy)[0])
        self.assertIsNone(GATE._final_disposition(explicit, policy))

    def test_hard_final_runs_only_at_its_named_transition(self):
        policy = CONFIG.load_policy(GATE.REPO / "agentfold.toml")
        matching = GATE.parse_arguments(
            (
                "final",
                "--at-transition",
                policy.final.trigger,
                "--base-revision",
                "base",
                "--head-revision",
                "head",
                "--candidate-revision",
                "candidate",
                "--branch",
                "task/example",
            )
        )
        other = GATE.parse_arguments(
            (
                "final",
                "--at-transition",
                "merge",
                "--base-revision",
                "base",
                "--head-revision",
                "head",
                "--candidate-revision",
                "candidate",
                "--branch",
                "task/example",
            )
        )
        self.assertIsNone(GATE._final_disposition(matching, policy))
        if policy.final.trigger != "merge":
            self.assertEqual("not-run", GATE._final_disposition(other, policy)[0])

    def test_final_admission_uses_exact_range_and_never_staged_scope(self):
        options = mock.Mock(
            gate="final",
            branch="task/example",
            at_transition="pull-request",
            displaced_tip=None,
            provider_hard=False,
        )
        candidate = MANIFEST.CandidateManifest(
            "revision-range",
            "candidate",
            "closure",
            (),
            (),
            "index",
            "a" * 40,
            "b" * 40,
        )

        commands = GATE.admission_commands(options, candidate)

        core = commands[0][1]
        reconcile = commands[1][1]
        self.assertNotIn("--staged", core)
        self.assertEqual("a" * 40 + "..." + "b" * 40, core[core.index("--range") + 1])
        self.assertEqual("a" * 40 + "..." + "b" * 40, reconcile[reconcile.index("--range") + 1])
        self.assertEqual("merge", reconcile[reconcile.index("--at-transition") + 1])

    def test_named_final_transition_requires_exact_range_and_branch(self):
        with self.assertRaises(SystemExit):
            GATE.parse_arguments(("final", "--at-transition", "pull-request"))

    def test_noncanonical_config_override_is_rejected(self):
        with self.assertRaises(SystemExit):
            GATE.parse_arguments(
                ("final", "--explicit", "--config", "candidate-policy.toml")
            )

    def test_real_git_base_policy_cannot_be_discarded_by_config_rename(self):
        policy_text = (GATE.REPO / "agentfold.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            repo = root / "repo"
            candidate = root / "candidate"
            policy_scratch = root / "policy-scratch"
            repo.mkdir()
            candidate.mkdir()
            policy_scratch.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            (repo / "agentfold.toml").write_text(policy_text, encoding="utf-8")
            subprocess.run(["git", "add", "agentfold.toml"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base policy"], cwd=repo, check=True)
            base = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()
            (candidate / "agentfold.toml").write_text(policy_text, encoding="utf-8")
            (candidate / "renamed.toml").write_text(policy_text, encoding="utf-8")
            with mock.patch.object(GATE, "REPO", repo):
                with self.assertRaisesRegex(GATE.GateError, "canonical agentfold.toml"):
                    GATE.load_candidate_policy(
                        candidate, Path("renamed.toml"), policy_scratch, base
                    )
                policy, digest = GATE.load_candidate_policy(
                    candidate, Path("agentfold.toml"), policy_scratch, base
                )
            self.assertIsInstance(policy, CONFIG.PolicyUnion)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_real_git_first_adoption_is_canonical_and_later_deletion_fails(self):
        policy_text = (GATE.REPO / "agentfold.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            repo = root / "repo"
            candidate = root / "candidate"
            empty_candidate = root / "empty-candidate"
            policy_scratch = root / "policy-scratch"
            for path in (repo, candidate, empty_candidate, policy_scratch):
                path.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            (repo / "README.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "pre-adoption"], cwd=repo, check=True)
            pre_adoption = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()
            (candidate / "agentfold.toml").write_text(policy_text, encoding="utf-8")
            with mock.patch.object(GATE, "REPO", repo):
                policy, _digest = GATE.load_candidate_policy(
                    candidate, Path("agentfold.toml"), policy_scratch, pre_adoption
                )
            self.assertIsInstance(policy, CONFIG.TestGatePolicy)

            (repo / "agentfold.toml").write_text(policy_text, encoding="utf-8")
            subprocess.run(["git", "add", "agentfold.toml"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "adopt policy"], cwd=repo, check=True)
            adopted = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()
            with mock.patch.object(GATE, "REPO", repo):
                with self.assertRaisesRegex(GATE.GateError, "candidate policy is unavailable"):
                    GATE.load_candidate_policy(
                        empty_candidate,
                        Path("agentfold.toml"),
                        policy_scratch,
                        adopted,
                    )

    def test_maximum_terminates_the_whole_component_process_group(self):
        with tempfile.TemporaryDirectory() as scratch:
            pid_file = Path(scratch) / "grandchild.pid"
            script = (
                "import pathlib,subprocess,sys,time; "
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid)); "
                "time.sleep(30)"
            )
            result = GATE.run_component(
                "probe", [sys.executable, "-c", script], 0.2
            )
            self.assertEqual("incomplete", result.outcome)
            self.assertIn("process group", result.detail)
            deadline = time.monotonic() + 2
            while pid_file.exists() and time.monotonic() < deadline:
                pid = int(pid_file.read_text())
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.02)
            else:
                if pid_file.exists():
                    self.fail("grandchild survived component process-group cleanup")

    def test_sigterm_ignoring_component_cleanup_stays_inside_hard_bound(self):
        script = (
            "import signal,time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "time.sleep(30)"
        )
        started = time.monotonic()
        result = GATE.run_component(
            "probe",
            [sys.executable, "-c", script],
            0.1,
            cleanup_deadline=started + 0.35,
        )
        self.assertEqual("incomplete", result.outcome)
        self.assertLess(time.monotonic() - started, 0.5)

    def test_component_environment_drops_sensitive_values(self):
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "GITHUB_ACTIONS": "true",
            "GITHUB_TOKEN": "sensitive",
            "GH_TOKEN": "sensitive",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "sensitive",
            "UNRELATED_SECRET": "sensitive",
        }
        result = GATE.run_component(
            "probe",
            [
                sys.executable,
                "-c",
                "import json,os; print(json.dumps(dict(os.environ), sort_keys=True))",
            ],
            2.0,
            environment=environment,
        )
        self.assertEqual("pass", result.outcome, result.detail)
        observed = json.loads(result.detail)
        self.assertEqual("true", observed["GITHUB_ACTIONS"])
        self.assertNotIn("GITHUB_TOKEN", observed)
        self.assertNotIn("GH_TOKEN", observed)
        self.assertNotIn("ACTIONS_ID_TOKEN_REQUEST_TOKEN", observed)
        self.assertNotIn("UNRELATED_SECRET", observed)

    def test_only_verified_git_hook_exec_path_prefix_is_canonicalized(self):
        base_path = os.environ.get("PATH", "")
        git_exec_path = subprocess.check_output(
            ["git", "--exec-path"], text=True
        ).strip()
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            git_index_file = subprocess.check_output(
                ["git", "rev-parse", "--git-path", "index"],
                cwd=repo,
                text=True,
            ).strip()
            hook_environment = {
                "PATH": git_exec_path + os.pathsep + base_path,
                "GIT_EXEC_PATH": git_exec_path,
                "GIT_INDEX_FILE": git_index_file,
                "GIT_PREFIX": "",
            }

            with mock.patch.object(GATE, "REPO", repo):
                normalized = GATE.safe_process_environment(hook_environment)

                self.assertEqual(base_path, normalized["PATH"])
                self.assertEqual(
                    GATE.environment_identity({"PATH": base_path})[
                        "component_environment_digest"
                    ],
                    GATE.environment_identity(hook_environment)[
                        "component_environment_digest"
                    ],
                )

                attacker_prefix = "/tmp/not-the-configured-git-exec-path"
                attacker_environment = dict(hook_environment)
                attacker_environment["PATH"] = attacker_prefix + os.pathsep + base_path
                attacker_environment["GIT_EXEC_PATH"] = attacker_prefix
                observed = GATE.safe_process_environment(attacker_environment)

                self.assertEqual(attacker_environment["PATH"], observed["PATH"])
                self.assertNotEqual(
                    GATE.environment_identity({"PATH": base_path})[
                        "component_environment_digest"
                    ],
                    GATE.environment_identity(attacker_environment)[
                        "component_environment_digest"
                    ],
                )

                mismatched_prefix = dict(hook_environment)
                mismatched_prefix["PATH"] = "/tmp/not-git" + os.pathsep + base_path
                self.assertEqual(
                    mismatched_prefix["PATH"],
                    GATE.safe_process_environment(mismatched_prefix)["PATH"],
                )

                mismatched_index = dict(hook_environment)
                mismatched_index["GIT_INDEX_FILE"] = "/tmp/not-this-repository.index"
                self.assertEqual(
                    mismatched_index["PATH"],
                    GATE.safe_process_environment(mismatched_index)["PATH"],
                )

    def test_setsid_escaped_child_holding_output_cannot_block_cleanup(self):
        if not GATE.process_identity_discovery_available():
            self.skipTest("process environment inspection is sandbox-restricted")
        with tempfile.TemporaryDirectory() as scratch:
            pid_file = Path(scratch) / "escaped.pid"
            child = (
                "import os,signal,time; os.setsid(); "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
            )
            parent = (
                "import pathlib,subprocess,sys,time; "
                f"p=subprocess.Popen([sys.executable,'-c',{child!r}]); "
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid)); "
                "time.sleep(30)"
            )
            started = time.monotonic()
            result = GATE.run_component(
                "probe",
                [sys.executable, "-c", parent],
                0.15,
                cleanup_deadline=started + 0.45,
            )
            self.assertEqual("incomplete", result.outcome)
            self.assertLess(time.monotonic() - started, 0.6)
            self.assertIn("reserved execution interval", result.detail)
            pid = int(pid_file.read_text())
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.02)
            else:
                self.fail("setsid descendant survived gate-owned cleanup")

    def test_reparented_daemon_is_found_by_gate_ownership_token(self):
        if not GATE.process_identity_discovery_available():
            self.skipTest("process environment inspection is sandbox-restricted")
        with tempfile.TemporaryDirectory() as scratch:
            pid_file = Path(scratch) / "daemon.pid"
            daemon = (
                "import os,pathlib,signal,time; "
                "pid=os.fork(); "
                "os._exit(0) if pid else None; "
                "os.setsid(); pid=os.fork(); "
                "os._exit(0) if pid else None; "
                f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid())); "
                "signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)"
            )
            parent = (
                "import subprocess,sys,time; "
                f"subprocess.Popen([sys.executable,'-c',{daemon!r}]); time.sleep(30)"
            )
            started = time.monotonic()
            result = GATE.run_component(
                "probe",
                [sys.executable, "-c", parent],
                0.2,
                cleanup_deadline=started + 1.0,
            )
            self.assertEqual("incomplete", result.outcome)
            self.assertTrue(pid_file.is_file())
            pid = int(pid_file.read_text())
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.02)
            else:
                self.fail("reparented daemon survived gate-owned cleanup")

    @unittest.skipUnless(
        sys.platform.startswith("linux"),
        "Linux child-subreaper containment is platform-specific",
    )
    def test_linux_subreaper_kills_reexeced_daemon_after_environment_scrub(self):
        if not GATE.strong_process_containment_available():
            self.skipTest("Linux child-subreaper containment is unavailable")
        with tempfile.TemporaryDirectory() as scratch:
            pid_file = Path(scratch) / "scrubbed-daemon.pid"
            survivor = (
                "import os,pathlib,signal,time; "
                f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid())); "
                "signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)"
            )
            daemon = (
                "import os,sys; pid=os.fork(); "
                "os._exit(0) if pid else None; os.setsid(); pid=os.fork(); "
                "os._exit(0) if pid else None; "
                f"os.execve(sys.executable,[sys.executable,'-c',{survivor!r}],"
                "{'PATH':os.environ.get('PATH','')})"
            )
            parent = (
                "import subprocess,sys,time; "
                f"subprocess.Popen([sys.executable,'-c',{daemon!r}]); time.sleep(30)"
            )
            started = time.monotonic()
            result = GATE.run_component(
                "probe",
                [sys.executable, "-c", parent],
                0.2,
                cleanup_deadline=started + 1.0,
                require_strong_containment=True,
            )
            self.assertEqual("incomplete", result.outcome)
            self.assertIn("Linux child-subreaper containment", result.detail)
            self.assertTrue(pid_file.is_file())
            pid = int(pid_file.read_text())
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.02)
            else:
                self.fail("scrubbed double-fork descendant survived containment")

    def test_provider_hard_refuses_unsupported_process_containment(self):
        with mock.patch.object(
            GATE, "strong_process_containment_available", return_value=False
        ), mock.patch.object(GATE.subprocess, "Popen") as popen:
            result = GATE.run_component(
                "probe",
                [sys.executable, "-c", "raise AssertionError('must not run')"],
                1.0,
                require_strong_containment=True,
            )

        self.assertEqual("incomplete", result.outcome)
        self.assertEqual("none", result.evidence)
        self.assertIn("was not started", result.detail)
        popen.assert_not_called()

    def test_report_states_best_effort_detached_cleanup_when_strong_is_absent(self):
        with mock.patch.object(
            GATE, "strong_process_containment_available", return_value=False
        ):
            report = GATE._base_report("routine", time.monotonic())

        self.assertEqual(
            {
                "mode": "portable-process-group",
                "detached_descendants": "best-effort",
            },
            report["process_containment"],
        )

    def test_timeout_plus_candidate_drift_can_never_defer_with_exit_zero(self):
        report = GATE._base_report("routine", time.monotonic())
        component = GATE.ComponentResult(
            "repository-tests/selected", "incomplete", "executed", 0.1, ()
        )
        GATE.apply_gate_outcome(
            report,
            "routine",
            (component,),
            ("test.py",),
            (),
            False,
            (),
            False,
        )
        self.assertEqual("blocked-incomplete", report["outcome"])
        self.assertIn("candidate-stability", report["incomplete"])

    def test_index_drift_during_selected_test_timeout_blocks(self):
        environment = {
            name: value for name, value in os.environ.items() if not name.startswith("GIT_")
        }
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, env=environment, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            changed = repo / "file.txt"
            changed.write_text("base\n")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            changed.write_text("candidate\n")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            frozen = Path(scratch) / "frozen.index"
            MANIFEST.copy_staged_index(repo, frozen)
            candidate = MANIFEST.staged_candidate(repo, frozen)

            def drift():
                changed.write_text("drift\n")
                subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)

            timer = threading.Timer(0.05, drift)
            timer.start()
            started = time.monotonic()
            component = GATE.run_component(
                "repository-tests/selected",
                [sys.executable, "-c", "import time; time.sleep(30)"],
                0.15,
                cleanup_deadline=started + 0.35,
            )
            timer.join()
            stable = MANIFEST.live_index_matches(
                repo, candidate.source_fingerprint, candidate.base_revision
            )
            report = GATE._base_report("routine", started)
            GATE.apply_gate_outcome(
                report,
                "routine",
                (component,),
                ("test.py",),
                (),
                False,
                (),
                stable,
            )
            self.assertEqual("blocked-incomplete", report["outcome"])

    def test_adopted_empty_critical_repo_blocks_missing_full_test_evidence(self):
        report = GATE._base_report("routine", time.monotonic())
        components = (
            GATE.ComponentResult("core-scope", "pass", "executed", 0.1, ()),
            GATE.ComponentResult("reconcile", "pass", "executed", 0.1, ()),
            GATE.ComponentResult(
                "repository-tests/full",
                "incomplete",
                "none",
                0.0,
                (),
                "no tests discovered",
            ),
        )
        GATE.apply_gate_outcome(
            report,
            "routine",
            components,
            (),
            (),
            True,
            ("core-scope", "reconcile", "repository-tests/full"),
            True,
        )
        self.assertEqual("blocked-incomplete", report["outcome"])
        self.assertIn("repository-tests/full", report["incomplete"])

    def test_deleting_last_critical_test_does_not_create_synthetic_pass(self):
        components = (
            GATE.ComponentResult("core-scope", "pass", "executed", 0.1, ()),
            GATE.ComponentResult("reconcile", "pass", "executed", 0.1, ()),
        )
        self.assertEqual(
            ("repository-tests/full",),
            GATE.missing_required_checks(
                ("core-scope", "reconcile", "repository-tests/full"),
                components,
            ),
        )

    def test_target_only_breach_does_not_fail_but_maximum_overrun_does(self):
        routine = GATE._base_report("routine", 0.0)
        routine.update(
            {"outcome": "pass", "reason": "passed", "critical": {"is_critical": False}}
        )
        with mock.patch.object(GATE.time, "monotonic", return_value=2.0):
            GATE._account_elapsed(routine, 0.0, 1.0, 3.0)
        self.assertTrue(routine["target_exceeded"])
        self.assertEqual("pass", routine["outcome"])
        final = GATE._base_report("final", 0.0)
        final.update(
            {"outcome": "pass", "reason": "passed", "critical": {"is_critical": False}}
        )
        with mock.patch.object(GATE.time, "monotonic", return_value=4.0):
            GATE._account_elapsed(final, 0.0, 1.0, 3.0)
        self.assertEqual("blocked-incomplete", final["outcome"])
        self.assertTrue(final["maximum_exceeded"])

    def test_budget_finding_uses_stable_gate_slot_across_policy_edits(self):
        report = GATE._base_report("routine", time.monotonic())
        report.update(
            {
                "candidate": {"digest": "candidate"},
                "components": [],
            }
        )
        options = mock.Mock(at_transition=None, explicit=False)
        captured = []

        def file_task(_repo, occurrence):
            captured.append(occurrence)
            return mock.Mock(as_dict=lambda: {"disposition": "filed"})

        with mock.patch.object(
            GATE.file_test_budget_task, "file_budget_task", side_effect=file_task
        ):
            GATE.file_target_breach(report, 60, "policy-one", options)
            GATE.file_target_breach(report, 60, "policy-two", options)
        self.assertEqual(
            ["testing.routine.target_seconds", "testing.routine.target_seconds"],
            [item["config_slot"] for item in captured],
        )

    def test_transition_invocation_is_not_independent_enforcement_evidence(self):
        report = GATE._base_report("final", time.monotonic())
        report["invocation"] = {
            "kind": "transition",
            "transition": "pull-request",
        }
        self.assertEqual("unobserved", report["enforcement"])

    def test_staged_manifest_uses_frozen_index_and_detects_live_drift(self):
        environment = {
            name: value for name, value in os.environ.items() if not name.startswith("GIT_")
        }
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, env=environment, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=repo, env=environment, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                env=environment,
                check=True,
            )
            (repo / "file.txt").write_text("base\n")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, env=environment, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, env=environment, check=True)
            (repo / "file.txt").write_text("candidate\n")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, env=environment, check=True)
            frozen = Path(scratch) / "frozen.index"
            MANIFEST.copy_staged_index(repo, frozen)
            candidate = MANIFEST.staged_candidate(repo, frozen)
            view = Path(scratch) / "view"
            MANIFEST.materialize_staged_candidate(repo, frozen, view)
            self.assertEqual("candidate\n", (view / "file.txt").read_text())
            self.assertTrue(MANIFEST.live_index_matches(repo, candidate.source_fingerprint))
            (repo / "file.txt").write_text("drift\n")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, env=environment, check=True)
            self.assertFalse(MANIFEST.live_index_matches(repo, candidate.source_fingerprint))
            self.assertEqual("candidate\n", (view / "file.txt").read_text())

    def test_reconcile_reads_frozen_staged_view_not_masking_worktree_bytes(self):
        environment = {
            name: value for name, value in os.environ.items() if not name.startswith("GIT_")
        }
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, env=environment, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            reconcile = repo / "automation/reconcile/reconcile.py"
            reconcile.parent.mkdir(parents=True)
            reconcile.write_text(
                "#!/usr/bin/env python3\n"
                "from pathlib import Path\n"
                "root = Path(__file__).resolve().parents[2]\n"
                "raise SystemExit(0 if (root / 'marker.txt').read_text() == 'staged\\n' else 9)\n"
            )
            marker = repo / "marker.txt"
            marker.write_text("base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            marker.write_text("staged\n")
            subprocess.run(["git", "add", "marker.txt"], cwd=repo, check=True)
            marker.write_text("masking-worktree\n")
            capture = Path(scratch) / "capture"
            capture.mkdir()
            options = mock.Mock(gate="routine", staged=True, provider_hard=False)
            with mock.patch.object(GATE, "REPO", repo):
                candidate, _view, candidate_root, _stable = GATE.capture_candidate(
                    options, capture
                )
                command = GATE.admission_commands(
                    options, candidate, candidate_root
                )[1][1]
                component_environment = GATE.candidate_git_environment(
                    candidate_root, capture / "candidate.index"
                )
                result = GATE.run_component(
                    "reconcile",
                    command,
                    2.0,
                    cwd=candidate_root,
                    internal_environment=component_environment,
                )
            self.assertEqual("pass", result.outcome, result.detail)
            self.assertEqual("staged\n", (candidate_root / "marker.txt").read_text())
            self.assertEqual("masking-worktree\n", marker.read_text())

    def test_real_frozen_service_candidate_preserves_reconciler_git_topology(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            self._make_reconciler_topology_repository(repo)
            service_data = repo / "services/example/data.txt"
            service_data.write_text("candidate\n", encoding="utf-8")
            subprocess.run(["git", "add", str(service_data)], cwd=repo, check=True)

            frozen = Path(scratch) / "plain.index"
            MANIFEST.copy_staged_index(repo, frozen)
            plain = Path(scratch) / "plain"
            plain.mkdir()
            plain_environment = os.environ.copy()
            plain_environment["GIT_INDEX_FILE"] = str(frozen)
            subprocess.run(
                ["git", "checkout-index", "--all", f"--prefix={plain}{os.sep}"],
                cwd=repo,
                env=plain_environment,
                check=True,
            )
            with mock.patch.object(GATE, "REPO", repo):
                before = GATE.run_component(
                    "reconcile",
                    [sys.executable, str(plain / "automation/reconcile/reconcile.py"), "--check"],
                    15.0,
                    cwd=plain,
                    internal_environment=GATE.candidate_git_environment(plain, frozen),
                )
            self.assertEqual("failed", before.outcome)
            self.assertIn("reconcile: 84 finding(s)", before.detail)

            capture = Path(scratch) / "capture"
            capture.mkdir()

            result, tested_view, candidate_root = self._run_frozen_candidate_reconcile(
                repo, capture
            )

            self.assertEqual("pass", result.outcome, result.detail)
            self.assertTrue((candidate_root / ".git").is_dir())
            self.assertIn(".git", tested_view["paths"])
            self.assertIn(
                {"path": ".git", "kind": "directory"}, tested_view["records"]
            )

    def test_real_frozen_candidate_still_rejects_missing_required_structure(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            self._make_reconciler_topology_repository(repo)
            subprocess.run(
                ["git", "rm", "-q", "--", "schema/leaves/leaf-000/marker.txt"],
                cwd=repo,
                check=True,
            )
            capture = Path(scratch) / "capture"
            capture.mkdir()

            result, _tested_view, candidate_root = self._run_frozen_candidate_reconcile(
                repo, capture
            )

            self.assertEqual("failed", result.outcome)
            self.assertFalse((candidate_root / "schema/leaves/leaf-000").exists())
            self.assertIn("`schema/leaves/leaf-000/` does not exist", result.detail)

    def test_final_candidate_view_is_the_declared_synthetic_merge_not_head(self):
        environment = {
            name: value for name, value in os.environ.items() if not name.startswith("GIT_")
        }
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, env=environment, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=repo, env=environment, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                env=environment,
                check=True,
            )
            (repo / "base.txt").write_text("base\n")
            subprocess.run(["git", "add", "base.txt"], cwd=repo, env=environment, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, env=environment, check=True)
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            default_branch = subprocess.check_output(
                ["git", "branch", "--show-current"], cwd=repo, text=True
            ).strip()
            subprocess.run(["git", "checkout", "-qb", "feature"], cwd=repo, check=True)
            (repo / "head.txt").write_text("head\n")
            subprocess.run(["git", "add", "head.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "head"], cwd=repo, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            subprocess.run(["git", "checkout", "-q", default_branch], cwd=repo, check=True)
            subprocess.run(["git", "merge", "--no-ff", "-qm", "merge", head], cwd=repo, check=True)
            merge = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            options = mock.Mock(
                base_revision=base,
                head_revision=head,
                candidate_revision=merge,
            )
            capture_root = Path(scratch) / "capture"
            capture_root.mkdir()
            with mock.patch.object(GATE, "REPO", repo):
                candidate, _manifest, view, stable = GATE.capture_revision_candidate(
                    options, capture_root
                )
                self.assertTrue(stable())
            self.assertEqual("revision-range", candidate.kind)
            self.assertEqual(merge, candidate.candidate_revision)
            self.assertEqual("head\n", (view / "head.txt").read_text())

    def test_full_receipt_reuse_requires_every_binding_input(self):
        candidate = MANIFEST.CandidateManifest(
            "staged-index", "candidate", "closure", (), (), "index"
        )
        view = {"digest": "view"}
        with mock.patch.object(GATE, "REPO", Path(tempfile.mkdtemp())):
            (GATE.REPO / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=GATE.REPO, check=True)
            first = GATE.receipt_binding(
                candidate, view, ("test.py",), "policy", "repository-tests/full"
            )
            GATE.write_receipt(first)
            self.assertIsNotNone(GATE.reusable_receipt(first))
            changed = dict(first)
            changed["policy_digest"] = "other"
            changed["binding_digest"] = MANIFEST.canonical_digest(changed)
            self.assertIsNone(GATE.reusable_receipt(changed))

    def test_pythonpath_change_cannot_reuse_a_full_pass_receipt(self):
        candidate = MANIFEST.CandidateManifest(
            "staged-index", "candidate", "closure", (), (), "index"
        )
        view = {"digest": "view"}
        with mock.patch.object(GATE, "REPO", Path(tempfile.mkdtemp())):
            (GATE.REPO / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=GATE.REPO, check=True)
            first = GATE.receipt_binding(
                candidate,
                view,
                ("test.py",),
                "policy",
                "repository-tests/full",
                environment={"PATH": "/bin", "PYTHONPATH": "/first"},
            )
            GATE.write_receipt(first)
            changed = GATE.receipt_binding(
                candidate,
                view,
                ("test.py",),
                "policy",
                "repository-tests/full",
                environment={"PATH": "/bin", "PYTHONPATH": "/second"},
            )

            self.assertNotEqual(first["binding_digest"], changed["binding_digest"])
            self.assertIsNone(GATE.reusable_receipt(changed))

    def test_final_prewarm_is_reused_by_actual_git_commit_hook(self):
        source_repo = GATE.REPO
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            for relative in (
                "automation/run_test_gate.py",
                "automation/run_tests.py",
                "automation/test_manifest.py",
            ):
                destination = repo / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_repo / relative, destination)
            shutil.copy2(source_repo / "agentfold.toml", repo / "agentfold.toml")
            (repo / ".gitignore").write_text("tmp/\n")
            smoke = repo / "automation/tests/test_smoke.py"
            smoke.parent.mkdir(parents=True)
            smoke.write_text("import unittest\n\nclass Smoke(unittest.TestCase):\n    pass\n")
            workflow = repo / ".github/workflows/harness.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            workflow.write_text("name: critical-candidate\n")
            subprocess.run(["git", "add", str(workflow)], cwd=repo, check=True)

            noop = [sys.executable, "-c", "raise SystemExit(0)"]
            admissions = (("core-scope", noop), ("reconcile", noop))
            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE, "admission_commands", return_value=admissions
            ), mock.patch.object(GATE, "_write_summary"):
                self.assertEqual(
                    0,
                    GATE.main(
                        ("final", "--explicit", "--staged"),
                        started=time.monotonic(),
                    ),
                )

            hook = repo / ".git/hooks/pre-commit"
            hook.write_text(
                "#!/usr/bin/env python3\n"
                "import importlib.util,json,os,sys\n"
                "from pathlib import Path\n"
                f"path=Path({str(MODULE_PATH)!r})\n"
                "spec=importlib.util.spec_from_file_location('hook_gate',str(path))\n"
                "gate=importlib.util.module_from_spec(spec)\n"
                "spec.loader.exec_module(gate)\n"
                "gate.REPO=Path.cwd().resolve()\n"
                "noop=[sys.executable,'-c','raise SystemExit(0)']\n"
                "gate.admission_commands=lambda *args: (('core-scope',noop),('reconcile',noop))\n"
                "original=gate.reusable_receipt\n"
                "def probe(binding):\n"
                " payload={'binding':binding,'git_environment':{name:os.environ.get(name) for name in ('GIT_EXEC_PATH','GIT_INDEX_FILE','GIT_PREFIX')},'safe_environment':gate.safe_process_environment()}\n"
                " Path('hook-binding.json').write_text(json.dumps(payload,sort_keys=True))\n"
                " return original(binding)\n"
                "gate.reusable_receipt=probe\n"
                "raise SystemExit(gate.main(('routine','--staged')))\n"
            )
            hook.chmod(0o755)

            committed = subprocess.run(
                ["git", "commit", "-m", "exercise real routine hook"],
                cwd=repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            self.assertEqual(0, committed.returncode, committed.stdout)
            report = json.loads(
                (repo / "tmp/test-gate-reports/latest-routine.json").read_text()
            )
            full = next(
                component
                for component in report["components"]
                if component["component_id"] == "repository-tests/full"
            )
            diagnostic = {
                "report": report,
                "hook_probe": json.loads((repo / "hook-binding.json").read_text()),
                "receipts": [
                    json.loads(path.read_text())
                    for path in (repo / "tmp/test-gate-receipts").glob("*.json")
                ],
            }
            self.assertEqual("reused", full["evidence"], diagnostic)

    def test_provider_hard_boundary_disallows_local_receipts(self):
        provider = mock.Mock(provider_hard=True)
        local = mock.Mock(provider_hard=False)
        self.assertFalse(GATE.local_receipts_allowed(provider))
        self.assertTrue(GATE.local_receipts_allowed(local))
        passed = GATE.ComponentResult("repository-tests/full", "pass", "executed", 1, ())
        with mock.patch.object(
            GATE, "reusable_receipt", side_effect=AssertionError("forged receipt was read")
        ), mock.patch.object(
            GATE, "write_receipt", side_effect=AssertionError("provider wrote a receipt")
        ):
            self.assertIsNone(
                GATE.reusable_full_receipt(
                    {"binding_digest": "forged"}, "repository-tests/full", provider
                )
            )
            self.assertFalse(
                GATE.persist_full_receipt(
                    {"binding_digest": "forged"}, passed, True, provider
                )
            )

    def test_provider_hard_commands_use_trusted_controller_binaries(self):
        options = mock.Mock(
            provider_hard=True,
            gate="final",
            branch="task/example",
            at_transition="pull-request",
            displaced_tip=None,
        )
        candidate = MANIFEST.CandidateManifest(
            "revision-range",
            "candidate",
            "closure",
            (),
            (),
            "index",
            "a" * 40,
            "b" * 40,
        )
        candidate_root = Path(tempfile.mkdtemp()) / "candidate"
        commands = GATE.admission_commands(options, candidate, candidate_root)
        self.assertEqual(str(GATE.AUTOMATION / "check_core_scope.py"), commands[0][1][1])
        self.assertEqual(
            str(GATE.AUTOMATION / "reconcile/reconcile.py"), commands[1][1][1]
        )
        self.assertNotIn(str(candidate_root), " ".join(commands[0][1] + commands[1][1]))

    def test_explicit_staged_final_survives_commit_index_refresh_and_rejects_semantic_drift(self):
        source_repo = GATE.REPO
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            for relative in (
                "automation/run_test_gate.py",
                "automation/run_tests.py",
                "automation/test_manifest.py",
            ):
                destination = repo / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_repo / relative, destination)
            shutil.copy2(source_repo / "agentfold.toml", repo / "agentfold.toml")
            (repo / ".gitignore").write_text("tmp/\n")
            smoke = repo / "automation/tests/test_smoke.py"
            smoke.parent.mkdir(parents=True, exist_ok=True)
            smoke.write_text("import unittest\n\nclass Smoke(unittest.TestCase):\n    pass\n")
            workflow = repo / ".github/workflows/harness.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            workflow.write_text("name: critical-candidate\n")
            subprocess.run(["git", "add", str(workflow)], cwd=repo, check=True)

            noop = [sys.executable, "-c", "raise SystemExit(0)"]
            admissions = (("core-scope", noop), ("reconcile", noop))
            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE, "admission_commands", return_value=admissions
            ), mock.patch.object(GATE, "_write_summary"):
                final_exit = GATE.main(
                    ("final", "--explicit", "--staged"),
                    started=time.monotonic(),
                )
                final_report = json.loads(
                    (repo / "tmp/test-gate-reports/latest-final.json").read_text()
                )
                self.assertEqual(0, final_exit, final_report)

                # `git commit` refreshes index stat/cache bytes before invoking the
                # hook.  That storage-only rewrite must not invalidate evidence for
                # unchanged object ids, modes, paths, base, or tested-view bytes.
                hook = repo / ".git/hooks/pre-commit"
                hook.write_text("#!/bin/sh\nexit 1\n")
                hook.chmod(0o755)
                blocked_commit = subprocess.run(
                    ["git", "commit", "-qm", "exercise real pre-commit refresh"],
                    cwd=repo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertNotEqual(0, blocked_commit.returncode)
                refreshed_index = Path(scratch) / "refreshed.index"
                MANIFEST.copy_staged_index(repo, refreshed_index)
                refreshed_candidate = MANIFEST.staged_candidate(repo, refreshed_index)
                self.assertNotEqual(
                    final_report["candidate"]["source_fingerprint"],
                    refreshed_candidate.source_fingerprint,
                )
                self.assertEqual(
                    final_report["candidate"]["closure_digest"],
                    refreshed_candidate.closure_digest,
                )
                self.assertEqual(
                    final_report["candidate"]["digest"], refreshed_candidate.digest
                )
                self.assertEqual(
                    0,
                    GATE.main(("routine", "--staged"), started=time.monotonic()),
                )
                unchanged = json.loads(
                    (repo / "tmp/test-gate-reports/latest-routine.json").read_text()
                )
                full = next(
                    component
                    for component in unchanged["components"]
                    if component["component_id"] == "repository-tests/full"
                )
                self.assertEqual("reused", full["evidence"])

                workflow.write_text("name: drifted-candidate\n")
                subprocess.run(["git", "add", str(workflow)], cwd=repo, check=True)
                drifted_index = Path(scratch) / "drifted.index"
                MANIFEST.copy_staged_index(repo, drifted_index)
                drifted_candidate = MANIFEST.staged_candidate(repo, drifted_index)
                self.assertNotEqual(
                    final_report["candidate"]["closure_digest"],
                    drifted_candidate.closure_digest,
                )
                self.assertNotEqual(
                    final_report["candidate"]["digest"], drifted_candidate.digest
                )
                self.assertEqual(
                    0,
                    GATE.main(("routine", "--staged"), started=time.monotonic()),
                )
                drifted = json.loads(
                    (repo / "tmp/test-gate-reports/latest-routine.json").read_text()
                )
                full = next(
                    component
                    for component in drifted["components"]
                    if component["component_id"] == "repository-tests/full"
                )
                self.assertEqual("executed", full["evidence"])

    def test_receipt_directory_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            outside = Path(scratch) / "outside"
            repo.mkdir()
            outside.mkdir()
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "tmp").mkdir()
            try:
                os.symlink(str(outside), str(repo / "tmp/test-gate-receipts"))
            except (NotImplementedError, OSError):
                self.skipTest("symlinks are unavailable")
            with mock.patch.object(GATE, "REPO", repo):
                with self.assertRaisesRegex(GATE.GateError, "symlink"):
                    GATE._safe_local_directory(Path("tmp/test-gate-receipts"))

    def test_report_directory_is_created_in_metadata_free_runner_projection(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "projection"
            repo.mkdir()
            (repo / ".gitignore").write_text("tmp/\n", encoding="utf-8")
            report = GATE._base_report("routine", time.monotonic())
            report.update(
                {"outcome": "pass", "evidence": "executed", "reason": "passed"}
            )
            with mock.patch.object(GATE, "REPO", repo):
                path = GATE._write_report(report)
            self.assertEqual(
                (repo / "tmp/test-gate-reports/latest-routine.json").resolve(),
                path.resolve(),
            )
            self.assertTrue(path.is_file())
            self.assertFalse((repo / "tmp").is_symlink())
            self.assertFalse(path.parent.is_symlink())

    def test_metadata_free_projection_without_exact_tmp_ignore_is_rejected(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "projection"
            repo.mkdir()
            (repo / ".gitignore").write_text("other/\n", encoding="utf-8")
            with mock.patch.object(GATE, "REPO", repo):
                with self.assertRaisesRegex(GATE.GateError, "must be ignored"):
                    GATE._safe_local_directory(Path("tmp/test-gate-reports"))

    def test_report_schema_and_outcome_exit_codes_are_stable(self):
        report = GATE._base_report("routine", time.monotonic())
        report.update(
            {
                "outcome": "deferred",
                "evidence": "executed",
                "reason": "reversible remainder",
            }
        )
        expected = GATE.REPO / "tmp/test-gate-reports/latest-routine.json"
        with mock.patch.object(GATE, "_write_report", return_value=expected):
            self.assertEqual(0, GATE.emit_report(report))
        self.assertEqual(GATE.REPORT_SCHEMA, report["schema"])
        self.assertEqual(0, report["exit_code"])
        self.assertEqual(1, GATE.OUTCOME_EXIT["blocked-incomplete"])
        self.assertEqual(2, GATE.OUTCOME_EXIT["invalid"])

    def test_accounted_report_recreates_its_missing_projection_parent(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "projection"
            repo.mkdir()
            (repo / ".gitignore").write_text("tmp/\n", encoding="utf-8")
            report = GATE._base_report("routine", time.monotonic())
            report.update(
                {"outcome": "pass", "evidence": "executed", "reason": "passed"}
            )
            expected = repo / "tmp/test-gate-reports/latest-routine.json"
            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE, "_write_report", return_value=expected
            ), mock.patch.object(GATE, "_write_summary"):
                self.assertEqual(0, GATE.emit_report(report))
            self.assertTrue(expected.is_file())

    def test_read_only_report_path_preserves_functional_exit_and_summary(self):
        report = GATE._base_report("routine", time.monotonic())
        report.update({"outcome": "pass", "evidence": "executed", "reason": "passed"})
        with mock.patch.object(GATE, "_write_report", side_effect=PermissionError(13, "read only")):
            exit_code = GATE.emit_report(report)
        self.assertEqual(0, exit_code)
        self.assertEqual({"disposition": "unavailable"}, report["report_write"])

    def test_unsafe_report_path_still_fails_closed(self):
        report = GATE._base_report("routine", time.monotonic())
        report.update({"outcome": "pass", "evidence": "executed", "reason": "passed"})
        with mock.patch.object(GATE, "_write_report", side_effect=GATE.GateError("unsafe report path")):
            exit_code = GATE.emit_report(report)
        self.assertEqual(2, exit_code)
        self.assertEqual("error", report["outcome"])
        self.assertEqual({"disposition": "refused"}, report["report_write"])

    def test_read_only_output_crossing_maximum_still_blocks_and_files(self):
        clock = [0.0]
        summaries = []
        report = GATE._base_report("final", 0.0)
        report.update(
            {
                "outcome": "pass",
                "evidence": "executed",
                "reason": "passed",
                "candidate": {"digest": "candidate"},
                "critical": {"is_critical": True},
            }
        )
        options = mock.Mock(at_transition=None, explicit=True)

        def output(summary):
            summaries.append(summary)
            clock[0] += 1.1

        with mock.patch.object(
            GATE.time, "monotonic", side_effect=lambda: clock[0]
        ), mock.patch.object(
            GATE, "_write_report", side_effect=PermissionError(13, "read only")
        ), mock.patch.object(
            GATE, "_write_summary", side_effect=output
        ), mock.patch.object(
            GATE,
            "file_target_breach",
            return_value={"disposition": "unavailable", "mutated": False},
        ):
            exit_code = GATE.emit_report(
                report,
                target=0.5,
                maximum=1.0,
                policy_digest="policy",
                options=options,
            )

        self.assertEqual(1, exit_code)
        self.assertEqual("blocked-incomplete", report["outcome"])
        self.assertIn("budget_filing", report)
        self.assertEqual(2, len(summaries))

    def test_output_and_report_persistence_count_toward_maximum_and_filing(self):
        clock = [0.0]
        persisted = []
        report = GATE._base_report("final", 0.0)
        report.update(
            {
                "outcome": "pass",
                "evidence": "executed",
                "reason": "passed",
                "candidate": {"digest": "candidate"},
                "critical": {"is_critical": True},
            }
        )
        options = mock.Mock(at_transition=None, explicit=True)

        def initial_write(_report):
            clock[0] += 0.1
            return GATE.REPO / "tmp/test-gate-reports/latest-final.json"

        def persist(_path, value):
            persisted.append(json.loads(json.dumps(value)))
            clock[0] += 0.1

        def output(_summary):
            clock[0] += 0.9

        def file_breach(*_arguments):
            clock[0] += 0.1
            return {"disposition": "filed", "mutated": True}

        with mock.patch.object(GATE.time, "monotonic", side_effect=lambda: clock[0]), mock.patch.object(
            GATE, "_write_report", side_effect=initial_write
        ), mock.patch.object(GATE, "_atomic_json", side_effect=persist), mock.patch.object(
            GATE, "_write_summary", side_effect=output
        ), mock.patch.object(GATE, "file_target_breach", side_effect=file_breach):
            exit_code = GATE.emit_report(
                report,
                target=0.5,
                maximum=1.0,
                policy_digest="policy",
                options=options,
            )

        self.assertEqual(1, exit_code)
        self.assertEqual("blocked-incomplete", report["outcome"])
        self.assertTrue(report["maximum_exceeded"])
        self.assertEqual("filed", report["budget_filing"]["disposition"])
        self.assertTrue(any(item.get("maximum_exceeded") for item in persisted))


if __name__ == "__main__":
    unittest.main()
