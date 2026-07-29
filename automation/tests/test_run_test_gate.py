#!/usr/bin/env python3
"""Focused regression tests for exact, budgeted test-gate orchestration."""

import importlib.util
import io
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

if __package__:
    from .test_gate_generations import DEADLINE_GENERATION, gate_generation
else:
    from test_gate_generations import DEADLINE_GENERATION, gate_generation

AUTOMATION = Path(__file__).resolve().parents[1]
MODULE_PATH = AUTOMATION / "run_test_gate.py"
SPEC = importlib.util.spec_from_file_location("run_test_gate", MODULE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
MANIFEST = GATE.test_manifest
CONFIG = GATE.test_gate_config
GATE_GENERATION = gate_generation()


def final_policy(mode):
    """Build an explicit final-mode fixture independent of the starter mode."""
    policy = CONFIG.load_policy(GATE.REPO / "agentfold.toml")
    return CONFIG.TestGatePolicy(
        policy.schema_version,
        policy.routine,
        CONFIG.FinalGate(
            mode,
            "pull-request" if mode == "hard" else None,
            policy.final.budget,
        ),
        policy.on_budget_exceeded,
        policy.critical_bindings,
        policy.reversible_bindings,
        policy.unmatched_is_critical,
    )
class TestGateTests(unittest.TestCase):
    @staticmethod
    def _freeze_for_generation(repo, arguments, capture, started, source):
        if GATE_GENERATION == DEADLINE_GENERATION:
            # Discovery belongs to the supervisor process.  Restore this test
            # process's module table before exercising the separately loaded
            # controller, exactly mirroring that process boundary.
            prior_modules = dict(sys.modules)
            try:
                policy_frame, authoritative_index = GATE._discover_policy_frame(
                    repo, arguments, capture
                )
            finally:
                for name in tuple(sys.modules):
                    if name not in prior_modules:
                        sys.modules.pop(name, None)
                sys.modules.update(prior_modules)
            return GATE._freeze(
                repo,
                arguments,
                capture,
                started,
                source,
                policy_frame=policy_frame,
                absolute_deadline=(
                    started + float(policy_frame["maximum_seconds"])
                ),
                authoritative_index=authoritative_index,
            )
        return GATE._freeze(repo, arguments, capture, started, source)

    @staticmethod
    def _clock_handoff(started, source, deadline):
        handoff = {
            "started_monotonic": started,
            "started_monotonic_source": source,
        }
        if GATE_GENERATION == DEADLINE_GENERATION:
            handoff["absolute_deadline_monotonic"] = deadline
        return handoff

    @staticmethod
    def _publish_receipt_pair(binding):
        report = GATE._base_report("final", 0.0)
        report.pop("_started")
        report.update(
            {
                "outcome": "pass",
                "evidence": "executed",
                "reason": "passed",
                "candidate": {
                    "digest": binding["candidate_digest"],
                    "closure_digest": binding["candidate_closure_digest"],
                },
                "terminalized_pass": True,
                "gate_exit_code": 0,
                "publication_status": "success",
                "publication_reason": "required projections persisted",
                "command_outcome": "pass",
                "exit_code": 0,
                "publication_id": "d" * 64,
                "report_write": {"disposition": "written"},
                "duration_seconds": 0.0,
            }
        )
        if GATE_GENERATION == DEADLINE_GENERATION:
            report["decision"] = GATE._decision_value(report)
            report["decision_digest"] = MANIFEST.canonical_digest(
                report["decision"]
            )
        report_directory = GATE._safe_local_directory(
            Path("tmp/test-gate-reports")
        )
        report_path = report_directory / "latest-final.json"
        receipt_path = GATE.write_receipt(binding, report, report_path)
        GATE._atomic_json(report_path, report)
        marker_path = GATE._receipt_cache_paths(binding)[1]
        receipt = json.loads(receipt_path.read_text())
        GATE._atomic_json(
            marker_path,
            GATE._publication_marker_value(
                binding,
                receipt,
                report,
                receipt_path,
                report_path,
                marker_path,
            ),
        )
        return report

    def _make_gate_bootstrap_repository(self, destination):
        destination.mkdir()
        for relative in GATE.CONTROLLER_CLOSURE_PATHS:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(GATE.REPO / relative, target)
            target.chmod(stat.S_IMODE(target.stat().st_mode) | stat.S_IWUSR)
        target = destination / "agentfold.toml"
        shutil.copy2(GATE.REPO / "agentfold.toml", target)
        target.chmod(stat.S_IMODE(target.stat().st_mode) | stat.S_IWUSR)
        (destination / ".gitignore").write_text("tmp/\n")
        subprocess.run(["git", "init", "-q"], cwd=destination, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=destination, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=destination,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=destination, check=True)
        subprocess.run(["git", "commit", "-qm", "bootstrap floor"], cwd=destination, check=True)

    @staticmethod
    def _kill_exact_marked_fixture_pid(pid_file, marker):
        """Best-effort finalizer that can kill only the fixture's recorded process."""
        try:
            pid = int(pid_file.read_text())
        except (FileNotFoundError, OSError, ValueError):
            return
        try:
            result = subprocess.run(
                ["ps", "eww", "-p", str(pid), "-o", "uid=,command="],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=0.2,
            )
        except (OSError, subprocess.TimeoutExpired):
            return
        fields = result.stdout.strip().split(None, 1)
        if len(fields) != 2:
            return
        try:
            uid = int(fields[0])
        except ValueError:
            return
        if uid != os.getuid() or marker not in fields[1].split():
            return
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

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

    def test_manual_final_runs_explicitly_and_named_transition_fails_closed(self):
        policy = final_policy("manual")
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
        self.assertEqual("blocked-incomplete", GATE._final_disposition(named, policy)[0])
        self.assertIsNone(GATE._final_disposition(explicit, policy))

    def test_reserved_hard_transition_also_fails_closed(self):
        policy = final_policy("hard")
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
        self.assertEqual("blocked-incomplete", GATE._final_disposition(matching, policy)[0])
        if policy.final.trigger != "merge":
            self.assertEqual("blocked-incomplete", GATE._final_disposition(other, policy)[0])

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

    def test_group_permission_error_continues_root_and_owned_signals(self):
        process = mock.Mock(pid=101)
        self_pid = os.getpid()
        with mock.patch.object(
            GATE.os, "killpg", side_effect=PermissionError(1, "not permitted")
        ) as killpg, mock.patch.object(GATE.os, "kill") as kill:
            GATE._signal_processes(
                process, (self_pid, 202), GATE.signal.SIGTERM
            )

        killpg.assert_called_once_with(101, GATE.signal.SIGTERM)
        self.assertEqual(
            [
                mock.call(101, GATE.signal.SIGTERM),
                mock.call(202, GATE.signal.SIGTERM),
            ],
            kill.call_args_list,
        )

    def test_owned_permission_error_is_tolerated_and_cleanup_continues(self):
        process = mock.Mock(pid=101)

        def signal_pid(pid, _process_signal):
            if pid == 202:
                raise PermissionError(1, "not permitted")

        with mock.patch.object(GATE.os, "killpg") as killpg, mock.patch.object(
            GATE.os, "kill", side_effect=signal_pid
        ) as kill:
            GATE._signal_processes(process, (202, 303), GATE.signal.SIGKILL)

        killpg.assert_called_once_with(101, GATE.signal.SIGKILL)
        self.assertEqual(
            [
                mock.call(101, GATE.signal.SIGKILL),
                mock.call(202, GATE.signal.SIGKILL),
                mock.call(303, GATE.signal.SIGKILL),
            ],
            kill.call_args_list,
        )

    def test_portable_snapshot_discovers_ancestry_and_exact_same_user_token_once(self):
        token = "exact-token"
        marker = f"{GATE.PROCESS_TOKEN_ENV}={token}"
        output = "\n".join(
            (
                "101 1 999 root",
                f"202 101 {os.getuid()} ancestry-only",
                f"505 999 {os.getuid()} token-only {marker}",
                f"303 999 {os.getuid() + 1} foreign {marker}",
                f"404 999 {os.getuid()} near {marker}-suffix",
                f"{os.getpid()} 999 {os.getuid()} self {marker}",
            )
        )
        result = mock.Mock(stdout=output, returncode=0)
        process = mock.Mock(pid=101)
        with mock.patch.object(GATE.sys, "platform", "darwin"), mock.patch.object(
            GATE.subprocess, "run", return_value=result
        ) as run:
            discovery = GATE._contained_process_pids(
                process, token, time.monotonic() + 1.0
            )

        self.assertEqual(frozenset((202, 505)), discovery.pids)
        self.assertTrue(discovery.complete)
        run.assert_called_once()
        self.assertEqual(
            ["ps", "eww", "-axo", "pid=,ppid=,uid=,command="],
            run.call_args[0][0],
        )

    def test_portable_snapshot_is_capped_at_300ms(self):
        result = mock.Mock(stdout="", returncode=0)
        with mock.patch.object(GATE.subprocess, "run", return_value=result) as run:
            GATE._portable_process_snapshot(time.monotonic() + 1.0)

        self.assertEqual(0.3, run.call_args[1]["timeout"])

    def test_portable_snapshot_accepts_delayed_completion_within_budget(self):
        result = mock.Mock(
            stdout=f"202 101 {os.getuid()} delayed\n", returncode=0
        )

        def delayed_run(*_args, **_kwargs):
            time.sleep(0.16)
            return result

        started = time.monotonic()
        with mock.patch.object(GATE.subprocess, "run", side_effect=delayed_run):
            snapshot = GATE._portable_process_snapshot(started + 0.4)

        self.assertEqual(
            ((202, 101, os.getuid(), "delayed"),), snapshot.rows
        )
        self.assertTrue(snapshot.complete)
        self.assertGreaterEqual(time.monotonic() - started, 0.15)

    def test_portable_snapshot_timeout_returns_no_unbounded_discovery(self):
        with mock.patch.object(
            GATE.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(("ps",), 0.2),
        ):
            snapshot = GATE._portable_process_snapshot(time.monotonic() + 0.2)
        self.assertEqual((), snapshot.rows)
        self.assertFalse(snapshot.complete)

    def test_portable_snapshot_preserves_partial_rows_but_marks_nonzero_incomplete(self):
        result = mock.Mock(
            stdout=f"202 101 {os.getuid()} partial\n", returncode=1
        )
        with mock.patch.object(GATE.subprocess, "run", return_value=result):
            snapshot = GATE._portable_process_snapshot(time.monotonic() + 0.2)
        self.assertEqual(
            ((202, 101, os.getuid(), "partial"),), snapshot.rows
        )
        self.assertFalse(snapshot.complete)

    def test_completed_portable_snapshot_is_consumed_at_exact_deadline(self):
        token = "deadline-token"
        marker = f"{GATE.PROCESS_TOKEN_ENV}={token}"
        snapshot = (
            (202, 101, os.getuid(), "ancestry-only"),
            (505, 999, os.getuid(), f"token-only {marker}"),
        )
        clock = [0.0]

        def complete_at_deadline(_deadline):
            clock[0] = 1.0
            return GATE.ProcessSnapshot(snapshot, True)

        process = mock.Mock(pid=101)
        with mock.patch.object(GATE.sys, "platform", "darwin"), mock.patch.object(
            GATE.time, "monotonic", side_effect=lambda: clock[0]
        ), mock.patch.object(
            GATE, "_portable_process_snapshot", side_effect=complete_at_deadline
        ):
            discovery = GATE._contained_process_pids(process, token, 1.0)

        self.assertEqual(frozenset((202, 505)), discovery.pids)
        self.assertTrue(discovery.complete)
        with mock.patch.object(GATE.os, "killpg"), mock.patch.object(
            GATE.os, "kill"
        ) as kill:
            GATE._signal_processes(process, discovery.pids, GATE.signal.SIGKILL)
        self.assertIn(mock.call(202, GATE.signal.SIGKILL), kill.call_args_list)
        self.assertIn(mock.call(505, GATE.signal.SIGKILL), kill.call_args_list)

    def test_linux_discovery_does_not_use_portable_snapshot(self):
        process = mock.Mock(pid=os.getpid())
        proc = mock.Mock()
        proc.is_dir.return_value = True
        with mock.patch.object(GATE.sys, "platform", "linux"), mock.patch.object(
            GATE, "Path", return_value=proc
        ), mock.patch.object(
            GATE,
            "_descendant_pids",
            return_value=GATE.ProcessDiscovery(frozenset(), True),
        ), mock.patch.object(
            GATE,
            "_owned_process_pids",
            return_value=GATE.ProcessDiscovery(frozenset(), True),
        ), mock.patch.object(GATE, "_portable_process_snapshot") as portable:
            GATE._contained_process_pids(process, "token", time.monotonic() + 0.1)

        portable.assert_not_called()

    def test_cleanup_kills_first_owned_snapshot_before_rescanning(self):
        process = mock.Mock(pid=101)
        process.poll.return_value = 0
        events = []

        discoveries = iter(
            (
                GATE.ProcessDiscovery(frozenset((202,)), True),
                GATE.ProcessDiscovery(frozenset((303,)), True),
            )
        )

        def discover(*_args):
            found = next(discoveries)
            events.append(("discover", set(found.pids)))
            return found

        def signal_processes(_process, owned, process_signal):
            events.append(("signal", process_signal, set(owned)))

        with mock.patch.object(
            GATE,
            "_contained_process_pids",
            side_effect=discover,
        ), mock.patch.object(GATE, "_signal_processes", side_effect=signal_processes), mock.patch.object(
            GATE, "_reap_contained_processes"
        ), mock.patch.object(
            GATE.time,
            "monotonic",
            side_effect=(0.0, 0.0, 0.1, 0.1, 0.2, 0.96),
        ):
            cleaned, complete = GATE._kill_process_tree(process, 1.0, "token")

        self.assertEqual(
            [
                ("discover", {202}),
                ("signal", GATE.signal.SIGTERM, {202}),
                ("signal", GATE.signal.SIGKILL, {202}),
                ("discover", {303}),
                ("signal", GATE.signal.SIGKILL, {202, 303}),
                ("signal", GATE.signal.SIGKILL, {202, 303}),
            ],
            events,
        )
        self.assertEqual((303, 202), cleaned)
        self.assertTrue(complete)

    def test_cleanup_reserves_snapshot_and_final_kill_time(self):
        process = mock.Mock(pid=101)
        process.poll.return_value = 0
        deadlines = []

        def discover(_process, _token, deadline, *_args):
            deadlines.append(deadline)
            return GATE.ProcessDiscovery(frozenset(), True)

        started = time.monotonic()
        cleanup_deadline = started + 0.2
        with mock.patch.object(
            GATE, "_contained_process_pids", side_effect=discover
        ), mock.patch.object(GATE, "_signal_processes"), mock.patch.object(
            GATE, "_reap_contained_processes"
        ):
            GATE._kill_process_tree(process, cleanup_deadline, "token")

        self.assertLessEqual(deadlines[0], cleanup_deadline - 0.1)
        self.assertTrue(all(deadline <= cleanup_deadline - 0.05 for deadline in deadlines[1:]))
        self.assertTrue(all(call[2]["timeout"] <= 0.05 for call in process.wait.mock_calls))

    def test_direct_root_permission_error_propagates(self):
        process = mock.Mock(pid=101)
        with mock.patch.object(GATE.os, "killpg"), mock.patch.object(
            GATE.os, "kill", side_effect=PermissionError(1, "not permitted")
        ) as kill:
            with self.assertRaises(PermissionError):
                GATE._signal_processes(process, (202,), GATE.signal.SIGTERM)

        kill.assert_called_once_with(101, GATE.signal.SIGTERM)

    def test_unrelated_group_signal_error_propagates(self):
        process = mock.Mock(pid=101)
        with mock.patch.object(
            GATE.os, "killpg", side_effect=OSError(5, "input/output error")
        ), mock.patch.object(GATE.os, "kill") as kill:
            with self.assertRaises(OSError):
                GATE._signal_processes(process, (202,), GATE.signal.SIGTERM)

        kill.assert_not_called()

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

    def test_component_environment_strips_external_python_import_surfaces(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            external = root / "external"
            working = root / "working"
            external.mkdir()
            working.mkdir()
            (external / "mutable_external.py").write_text("VALUE = 'attacker'\n")
            probe = (
                "import json,os\n"
                "try:\n import mutable_external\n loaded=True\n"
                "except ImportError:\n loaded=False\n"
                "names=('PYTHONPATH','PYTHONHOME','PYTHONUSERBASE','PYTHONSTARTUP')\n"
                "print(json.dumps({'loaded':loaded,'python':{n:os.environ.get(n) for n in names},"
                "'dontwrite':os.environ.get('PYTHONDONTWRITEBYTECODE')}))\n"
            )
            result = GATE.run_component(
                "python-environment",
                [sys.executable, "-c", probe],
                2.0,
                cwd=working,
                environment={
                    "PATH": os.environ.get("PATH", ""),
                    "PYTHONPATH": str(external),
                    "PYTHONHOME": str(external),
                    "PYTHONUSERBASE": str(external),
                    "PYTHONSTARTUP": str(external / "startup.py"),
                },
            )
            self.assertEqual("pass", result.outcome, result.detail)
            observed = json.loads(result.detail)
            self.assertFalse(observed["loaded"])
            self.assertEqual(
                {name: None for name in observed["python"]}, observed["python"]
            )
            self.assertEqual("1", observed["dontwrite"])

    def test_successful_component_cleans_detached_child_before_pass(self):
        if not GATE.process_identity_discovery_available():
            self.skipTest("process environment discovery is unavailable")
        with tempfile.TemporaryDirectory() as scratch:
            pid_file = Path(scratch) / "child.pid"
            script = (
                "import pathlib,subprocess,sys\n"
                "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],"
                " start_new_session=True)\n"
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid))\n"
            )
            result = GATE.run_component(
                "detached-success",
                [sys.executable, "-c", script, str(pid_file)],
                2.0,
            )
            self.assertEqual("pass", result.outcome, result.detail)
            self.assertIn("cleaned", result.detail)
            pid = int(pid_file.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)

    def test_detached_child_with_unavailable_discovery_cannot_pass(self):
        scratch_manager = tempfile.TemporaryDirectory()
        self.addCleanup(scratch_manager.cleanup)
        pid_file = Path(scratch_manager.name) / "unobserved.pid"
        marker = "agentfold-unobserved-" + os.urandom(12).hex()
        self.addCleanup(self._kill_exact_marked_fixture_pid, pid_file, marker)
        script = (
            "import pathlib,subprocess,sys\n"
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)',"
            "sys.argv[2]],start_new_session=True)\n"
            "pathlib.Path(sys.argv[1]).write_text(str(child.pid))\n"
        )
        unavailable = GATE.ProcessDiscovery(frozenset(), False)
        with mock.patch.object(
            GATE, "_contained_process_pids", return_value=unavailable
        ):
            result = GATE.run_component(
                "unavailable-discovery",
                [sys.executable, "-c", script, str(pid_file), marker],
                2.0,
            )
        self.assertEqual("incomplete", result.outcome)
        self.assertIn("cleanup did not complete", result.detail)
        self.assertTrue(pid_file.is_file())

    def test_partial_discovery_cleans_known_pids_but_fails_closed(self):
        process = mock.Mock(pid=101)
        process.poll.return_value = 0
        discoveries = iter(
            (
                GATE.ProcessDiscovery(frozenset((202,)), False),
                GATE.ProcessDiscovery(frozenset(), False),
                GATE.ProcessDiscovery(frozenset(), True),
                GATE.ProcessDiscovery(frozenset(), True),
            )
        )
        with mock.patch.object(
            GATE, "_contained_process_pids", side_effect=lambda *_args: next(discoveries)
        ), mock.patch.object(GATE, "_signal_processes") as signal_processes, mock.patch.object(
            GATE, "_reap_contained_processes"
        ):
            cleaned, complete = GATE._cleanup_after_component_exit(
                process, "token", time.monotonic() + 1.0
            )
        self.assertEqual((202,), cleaned)
        self.assertFalse(complete)
        self.assertTrue(
            any(202 in call[0][1] for call in signal_processes.call_args_list)
        )

    def test_successful_root_with_incomplete_cleanup_cannot_pass(self):
        with mock.patch.object(
            GATE, "_cleanup_after_component_exit", return_value=((123,), False)
        ):
            result = GATE.run_component(
                "cleanup-failure",
                [sys.executable, "-c", "raise SystemExit(0)"],
                1.0,
            )
        self.assertEqual("incomplete", result.outcome)
        self.assertIn("cleanup did not complete", result.detail)

    def test_successful_component_without_children_remains_pass(self):
        result = GATE.run_component(
            "ordinary-success",
            [sys.executable, "-c", "print('ordinary')"],
            1.0,
        )
        self.assertEqual("pass", result.outcome, result.detail)
        self.assertEqual("ordinary", result.detail)

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
        scratch_manager = tempfile.TemporaryDirectory()
        self.addCleanup(scratch_manager.cleanup)
        pid_file = Path(scratch_manager.name) / "escaped.pid"
        marker = "agentfold-setsid-" + os.urandom(12).hex()
        self.addCleanup(self._kill_exact_marked_fixture_pid, pid_file, marker)
        child = (
            "import os,signal,time; os.setsid(); "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
        )
        parent = (
            "import pathlib,subprocess,sys,time; "
            f"p=subprocess.Popen([sys.executable,'-c',{child!r},{marker!r}]); "
            f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid)); "
            "time.sleep(30)"
        )
        started = time.monotonic()
        result = GATE.run_component(
            "probe",
            [sys.executable, "-c", parent],
            0.15,
            cleanup_deadline=started + 0.75,
        )
        self.assertEqual("incomplete", result.outcome)
        self.assertLess(time.monotonic() - started, 0.9)
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
        scratch_manager = tempfile.TemporaryDirectory()
        self.addCleanup(scratch_manager.cleanup)
        pid_file = Path(scratch_manager.name) / "daemon.pid"
        marker = "agentfold-daemon-" + os.urandom(12).hex()
        self.addCleanup(self._kill_exact_marked_fixture_pid, pid_file, marker)
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
            f"subprocess.Popen([sys.executable,'-c',{daemon!r},{marker!r}]); time.sleep(30)"
        )
        started = time.monotonic()
        result = GATE.run_component(
            "probe",
            [sys.executable, "-c", parent],
            0.2,
            cleanup_deadline=started + 1.15,
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

    def test_automatic_transition_blocks_before_candidate_execution_or_receipt(self):
        arguments = (
            "final",
            "--at-transition",
            "pull-request",
            "--base-revision",
            "a" * 40,
            "--head-revision",
            "b" * 40,
            "--candidate-revision",
            "c" * 40,
            "--branch",
            "task/example",
        )
        captured = {}

        def emit(report, *unused, **ignored):
            captured.update(report)
            return GATE.OUTCOME_EXIT[report["outcome"]]

        with mock.patch.object(
            GATE, "capture_candidate", side_effect=AssertionError("candidate executed")
        ), mock.patch.object(
            GATE, "run_component", side_effect=AssertionError("component executed")
        ), mock.patch.object(
            GATE, "write_receipt", side_effect=AssertionError("receipt written")
        ), mock.patch.object(GATE, "emit_report", side_effect=emit):
            self.assertEqual(1, GATE.main(arguments, started=time.monotonic()))

        self.assertEqual("blocked-incomplete", captured["outcome"])
        self.assertEqual("cooperative-same-interpreter", captured["evidence_authority"])
        self.assertFalse(captured["controlled_completion"])
        self.assertFalse(captured["enforcement_eligible"])
        self.assertEqual("not-enforced", captured["enforcement"])
        self.assertIn("controlled external completion oracle", captured["reason"])

    def test_provider_hard_blocks_at_the_same_pre_execution_boundary(self):
        arguments = (
            "final",
            "--provider-hard",
            "--at-transition",
            "pull-request",
            "--base-revision",
            "a" * 40,
            "--head-revision",
            "b" * 40,
            "--candidate-revision",
            "c" * 40,
            "--branch",
            "task/example",
        )
        with mock.patch.object(
            GATE, "capture_candidate", side_effect=AssertionError("candidate executed")
        ), mock.patch.object(GATE, "emit_report", return_value=1):
            self.assertEqual(1, GATE.main(arguments, started=time.monotonic()))

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
        self.assertEqual("not-enforced", report["enforcement"])
        self.assertEqual("cooperative-same-interpreter", report["evidence_authority"])
        self.assertFalse(report["controlled_completion"])
        self.assertFalse(report["enforcement_eligible"])

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

    def test_composite_plan_keeps_base_tests_and_support_while_preserving_candidate_product(self):
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
            product = repo / "services/example/product.py"
            tests = repo / "services/example/tests"
            tests.mkdir(parents=True)
            product.write_text("VALUE = 'base'\n")
            (repo / "services/example/legacy.py").write_text("legacy\n")
            (tests / "helper.py").write_text("EXPECTED = 'base'\n")
            (tests / "test_original.py").write_text("ORIGINAL = 'base'\n")
            (tests / "test_emptied.py").write_text("EMPTY = 'base'\n")
            (tests / "test_unchanged.py").write_text("UNCHANGED = True\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            base = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()

            product.write_text("VALUE = 'candidate'\n")
            (repo / "services/example/legacy.py").unlink()
            (tests / "helper.py").write_text("EXPECTED = 'candidate-shadow'\n")
            (tests / "test_original.py").rename(tests / "test_renamed.py")
            (tests / "test_emptied.py").write_text("")
            (tests / "test_added.py").write_text("ADDED = True\n")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

            capture = Path(scratch) / "capture"
            capture.mkdir()
            frozen = capture / "candidate.index"
            with mock.patch.object(GATE, "REPO", repo):
                MANIFEST.copy_staged_index(repo, frozen)
                candidate = MANIFEST.staged_candidate(repo, frozen)
                candidate_root = capture / "candidate"
                candidate_view = MANIFEST.materialize_staged_candidate(
                    repo, frozen, candidate_root
                )
                plan = GATE.composite_test_plan(
                    candidate, candidate_root, candidate_view, capture
                )

            floor = plan["floor_root"]
            self.assertEqual("VALUE = 'candidate'\n", product.read_text())
            self.assertEqual(
                "VALUE = 'candidate'\n",
                (floor / "services/example/product.py").read_text(),
            )
            self.assertFalse((floor / "services/example/legacy.py").exists())
            self.assertEqual(
                "EXPECTED = 'base'\n",
                (floor / "services/example/tests/helper.py").read_text(),
            )
            self.assertTrue(
                (floor / "services/example/tests/test_original.py").is_file()
            )
            self.assertEqual(
                "EMPTY = 'base'\n",
                (floor / "services/example/tests/test_emptied.py").read_text(),
            )
            self.assertFalse(
                (floor / "services/example/tests/test_renamed.py").exists()
            )
            self.assertEqual(
                (
                    "services/example/tests/test_added.py",
                    "services/example/tests/test_emptied.py",
                    "services/example/tests/test_renamed.py",
                    "services/example/tests/test_unchanged.py",
                ),
                plan["supplemental_tests"],
            )
            identity = plan["identity"]
            self.assertEqual(base, identity["trusted_base_revision"])
            self.assertEqual(
                GATE.TRUSTED_TEST_OVERLAY_ALGORITHM,
                identity["overlay_algorithm"],
            )
            self.assertTrue(identity["trusted_floor_records"])
            self.assertTrue(identity["supplemental_records"])
            self.assertEqual(
                ["services/example/tests"],
                identity["support_changed_namespaces"],
            )

    def test_composite_plan_selects_only_changed_tests_when_support_is_unchanged(self):
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
            tests = repo / "services/example/tests"
            tests.mkdir(parents=True)
            (tests / "helper.py").write_text("SUPPORT = 'unchanged'\n")
            (tests / "test_changed.py").write_text("VALUE = 'base'\n")
            (tests / "test_deleted.py").write_text("DELETED = False\n")
            (tests / "test_emptied.py").write_text("VALUE = 'base'\n")
            (tests / "test_renamed.py").write_text("RENAMED = False\n")
            (tests / "test_unchanged.py").write_text("UNCHANGED = True\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

            (tests / "test_changed.py").write_text("VALUE = 'candidate'\n")
            (tests / "test_deleted.py").unlink()
            (tests / "test_emptied.py").write_text("")
            (tests / "test_renamed.py").rename(tests / "test_renamed_new.py")
            (tests / "test_added.py").write_text("ADDED = True\n")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

            capture = Path(scratch) / "capture"
            capture.mkdir()
            frozen = capture / "candidate.index"
            with mock.patch.object(GATE, "REPO", repo):
                MANIFEST.copy_staged_index(repo, frozen)
                candidate = MANIFEST.staged_candidate(repo, frozen)
                candidate_root = capture / "candidate"
                candidate_view = MANIFEST.materialize_staged_candidate(
                    repo, frozen, candidate_root
                )
                plan = GATE.composite_test_plan(
                    candidate, candidate_root, candidate_view, capture
                )

            self.assertEqual(
                (
                    "services/example/tests/test_added.py",
                    "services/example/tests/test_changed.py",
                    "services/example/tests/test_emptied.py",
                    "services/example/tests/test_renamed_new.py",
                ),
                plan["supplemental_tests"],
            )
            self.assertEqual([], plan["identity"]["support_changed_namespaces"])
            self.assertTrue(
                (plan["floor_root"] / "services/example/tests/test_deleted.py").is_file()
            )
            self.assertTrue(
                (plan["floor_root"] / "services/example/tests/test_renamed.py").is_file()
            )

    def test_composite_plan_treats_candidate_only_test_helper_as_a_test(self):
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
            tests = repo / "automation/tests"
            tests.mkdir(parents=True)
            changed_test = "automation/tests/test_changed.py"
            helper_test = "automation/tests/test_helper_candidate.py"
            unchanged_test = "automation/tests/test_unchanged.py"
            (repo / changed_test).write_text("VALUE = 'base'\n")
            (repo / unchanged_test).write_text("UNCHANGED = True\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

            (repo / changed_test).write_text("VALUE = 'candidate'\n")
            (repo / helper_test).write_text("SNAPSHOT = 'candidate-only'\n")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

            capture = Path(scratch) / "capture"
            capture.mkdir()
            frozen = capture / "candidate.index"
            with mock.patch.object(GATE, "REPO", repo):
                MANIFEST.copy_staged_index(repo, frozen)
                candidate = MANIFEST.staged_candidate(repo, frozen)
                candidate_root = capture / "candidate"
                candidate_view = MANIFEST.materialize_staged_candidate(
                    repo, frozen, candidate_root
                )
                plan = GATE.composite_test_plan(
                    candidate, candidate_root, candidate_view, capture
                )

            self.assertEqual([], plan["identity"]["support_changed_namespaces"])
            self.assertNotIn(helper_test, plan["floor_tests"])
            self.assertFalse((plan["floor_root"] / helper_test).exists())
            self.assertEqual(
                (changed_test, helper_test),
                plan["supplemental_tests"],
            )
            self.assertNotIn(unchanged_test, plan["supplemental_tests"])

    def test_composite_plan_removes_candidate_only_namespace_from_floor(self):
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
            base_test = repo / "automation/tests/test_base.py"
            base_test.parent.mkdir(parents=True)
            base_test.write_text("BASE = True\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

            candidate_namespace = repo / "services/new-service/tests"
            candidate_namespace.mkdir(parents=True)
            helper = candidate_namespace / "helper.py"
            added_test = candidate_namespace / "test_added.py"
            helper.write_text("VALUE = 1\n")
            added_test.write_text("ADDED = True\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)

            capture = Path(scratch) / "capture"
            capture.mkdir()
            frozen = capture / "candidate.index"
            with mock.patch.object(GATE, "REPO", repo):
                MANIFEST.copy_staged_index(repo, frozen)
                candidate = MANIFEST.staged_candidate(repo, frozen)
                candidate_root = capture / "candidate"
                candidate_view = MANIFEST.materialize_staged_candidate(
                    repo, frozen, candidate_root
                )
                plan = GATE.composite_test_plan(
                    candidate, candidate_root, candidate_view, capture
                )

            relative_test = added_test.relative_to(repo).as_posix()
            relative_helper = helper.relative_to(repo).as_posix()
            self.assertEqual(("automation/tests/test_base.py",), plan["floor_tests"])
            self.assertFalse(
                (plan["floor_root"] / "services/new-service/tests").exists()
            )
            self.assertEqual((relative_test,), plan["supplemental_tests"])
            supplemental_paths = {
                record["path"] for record in plan["identity"]["supplemental_records"]
            }
            self.assertIn(relative_test, supplemental_paths)
            self.assertIn(relative_helper, supplemental_paths)
            self.assertIn(
                "services/new-service/tests",
                plan["identity"]["candidate_test_namespaces"],
            )

    def test_composite_plan_normalizes_nested_namespaces_and_sealed_modes(self):
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
            parent_test = repo / "automation/tests/test_parent.py"
            nested_test = repo / "automation/tests/nested/tests/test_nested.py"
            parent_test.parent.mkdir(parents=True)
            nested_test.parent.mkdir(parents=True)
            parent_test.write_text("PARENT = True\n")
            nested_test.write_text("NESTED = True\n")
            nested_test.chmod(0o755)
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "nested base"], cwd=repo, check=True)

            added = repo / "automation/tests/nested/tests/test_added.py"
            added.write_text("ADDED = True\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            capture = Path(scratch) / "capture"
            capture.mkdir()
            frozen = capture / "candidate.index"
            with mock.patch.object(GATE, "REPO", repo):
                MANIFEST.copy_staged_index(repo, frozen)
                candidate = MANIFEST.staged_candidate(repo, frozen)
                candidate_root = capture / "candidate"
                MANIFEST.materialize_staged_candidate(repo, frozen, candidate_root)
                parent_candidate = candidate_root / parent_test.relative_to(repo)
                nested_candidate = candidate_root / nested_test.relative_to(repo)
                added_candidate = candidate_root / added.relative_to(repo)
                parent_candidate.chmod(0o400)
                nested_candidate.chmod(0o500)
                added_candidate.chmod(0o400)
                candidate_view = MANIFEST.tree_manifest(candidate_root)
                plan = GATE.composite_test_plan(
                    candidate, candidate_root, candidate_view, capture
                )

            self.assertEqual(
                ["automation/tests"], plan["identity"]["overlay_namespaces"]
            )
            self.assertEqual(
                ["automation/tests"], plan["identity"]["base_namespace_roots"]
            )
            self.assertEqual(
                (
                    "automation/tests/nested/tests/test_added.py",
                ),
                plan["supplemental_tests"],
            )
            modes = {
                record["path"]: record.get("mode")
                for record in plan["identity"]["candidate_test_records"]
                if record.get("kind") == "file"
            }
            self.assertEqual("100644", modes["automation/tests/test_parent.py"])
            self.assertEqual(
                "100755", modes["automation/tests/nested/tests/test_nested.py"]
            )

    def test_composite_plan_identity_invalidates_prior_schema_and_changed_floor_receipts(self):
        candidate = MANIFEST.CandidateManifest(
            "revision-range", "candidate", "closure", (), (), "index", "base", "head"
        )
        view = {"digest": "candidate-view"}
        first_plan = {
            "schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA,
            "trusted_base_revision": "base",
            "trusted_floor_records": [{"path": "tests/test_a.py", "sha256": "one"}],
            "supplemental_records": [],
            "overlay_algorithm": GATE.TRUSTED_TEST_OVERLAY_ALGORITHM,
        }
        second_plan = dict(first_plan)
        second_plan["trusted_floor_records"] = [
            {"path": "tests/test_a.py", "sha256": "two"}
        ]
        with mock.patch.object(GATE, "runner_revision", return_value="runner"), \
                mock.patch.object(GATE, "environment_identity", return_value={"env": "one"}):
            first = GATE.receipt_binding(
                candidate,
                view,
                ("tests/test_a.py",),
                "policy",
                "repository-tests/full",
                composite_identity=first_plan,
            )
            second = GATE.receipt_binding(
                candidate,
                view,
                ("tests/test_a.py",),
                "policy",
                "repository-tests/full",
                composite_identity=second_plan,
            )
        self.assertNotEqual(first["binding_digest"], second["binding_digest"])
        expected_schema = (
            "agentfold.test-component-receipt/v6"
            if GATE_GENERATION == DEADLINE_GENERATION
            else "agentfold.test-component-receipt/v5"
        )
        self.assertEqual(expected_schema, GATE.RECEIPT_SCHEMA)
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            receipt_dir = repo / "tmp/test-gate-receipts"
            receipt_dir.mkdir(parents=True)
            with mock.patch.object(GATE, "REPO", repo):
                rejected_versions = (
                    (1, 2, 3, 4, 5)
                    if GATE_GENERATION == DEADLINE_GENERATION
                    else (1, 2, 3, 4)
                )
                for version in rejected_versions:
                    (receipt_dir / f"{first['binding_digest']}.json").write_text(
                        json.dumps(
                            {
                                "schema": "agentfold.test-component-receipt/v{}".format(version),
                                "outcome": "pass",
                                "terminalized_pass": True,
                                "binding": first,
                            }
                        )
                    )
                    self.assertIsNone(GATE.reusable_receipt(first))

    def test_receipt_without_cooperative_authority_is_invalid(self):
        candidate = MANIFEST.CandidateManifest(
            "staged-index", "candidate", "closure", (), (), "index"
        )
        view = {"digest": "view"}
        with mock.patch.object(GATE, "REPO", Path(tempfile.mkdtemp())):
            (GATE.REPO / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=GATE.REPO, check=True)
            binding = GATE.receipt_binding(
                candidate, view, ("test.py",), "policy", "repository-tests/full"
            )
            directory = GATE._safe_local_directory(Path("tmp/test-gate-receipts"))
            path = directory / f"{binding['binding_digest']}.json"
            path.write_text(json.dumps({
                "schema": GATE.RECEIPT_SCHEMA,
                "outcome": "pass",
                "binding": binding,
            }))
            self.assertIsNone(GATE.reusable_receipt(binding))

    def test_composite_plan_fails_closed_when_trusted_base_has_no_tests(self):
        candidate = MANIFEST.CandidateManifest(
            "revision-range", "candidate", "closure", (), (), "index", "base", "head"
        )
        with tempfile.TemporaryDirectory() as scratch:
            scratch_root = Path(scratch)
            candidate_root = scratch_root / "candidate"
            candidate_root.mkdir()
            (candidate_root / ".git").mkdir()
            candidate_view = MANIFEST.tree_manifest(candidate_root)
            base_root = scratch_root / "base"
            base_root.mkdir()
            with mock.patch.object(
                GATE,
                "_materialize_revision",
                return_value=(base_root, MANIFEST.tree_manifest(base_root)),
            ):
                with self.assertRaisesRegex(GATE.GateError, "no discoverable"):
                    GATE.composite_test_plan(
                        candidate, candidate_root, candidate_view, scratch_root
                    )

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
            self._publish_receipt_pair(first)
            self.assertIsNotNone(GATE.reusable_receipt(first))
            changed = dict(first)
            changed["policy_digest"] = "other"
            changed["binding_digest"] = MANIFEST.canonical_digest(changed)
            self.assertIsNone(GATE.reusable_receipt(changed))

    def test_stripped_pythonpath_does_not_change_a_full_pass_receipt(self):
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
            self._publish_receipt_pair(first)
            changed = GATE.receipt_binding(
                candidate,
                view,
                ("test.py",),
                "policy",
                "repository-tests/full",
                environment={"PATH": "/bin", "PYTHONPATH": "/second"},
            )

            self.assertEqual(first["binding_digest"], changed["binding_digest"])
            self.assertIsNotNone(GATE.reusable_receipt(changed))

    def test_final_full_prewarm_covers_routine_selected_commit_hook(self):
        source_repo = GATE.REPO
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=repo, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            for relative in GATE.CONTROLLER_CLOSURE_PATHS:
                destination = repo / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_repo / relative, destination)
            shutil.copy2(source_repo / "agentfold.toml", repo / "agentfold.toml")
            hook_source = source_repo / "automation/hooks/pre-commit"
            hook = repo / "automation/hooks/pre-commit"
            hook.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(hook_source, hook)
            self.assertEqual(hook_source.read_bytes(), hook.read_bytes())
            self.assertIn(
                'python3 -I -S "$ROOT/automation/run_test_gate.py" routine --staged',
                hook.read_text(),
            )
            for relative in (
                "automation/check_core_scope.py",
                "automation/reconcile/reconcile.py",
            ):
                script = repo / relative
                script.parent.mkdir(parents=True, exist_ok=True)
                script.write_text(
                    "#!/usr/bin/env python3\nraise SystemExit(0)\n"
                )
            (repo / ".gitignore").write_text("tmp/\n")
            smoke = repo / "automation/tests/test_smoke.py"
            smoke.parent.mkdir(parents=True)
            smoke.write_text(
                "import unittest\n\nclass Smoke(unittest.TestCase):\n    pass\n"
            )
            stable = repo / "automation/tests/test_stable.py"
            stable.write_text(
                "import unittest\n\nclass Stable(unittest.TestCase):\n    pass\n"
            )
            workflow = repo / ".github/workflows/harness.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "base controller closure"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "core.hooksPath", "automation/hooks"],
                cwd=repo,
                check=True,
            )
            configured_hook = subprocess.check_output(
                ["git", "config", "--get", "core.hooksPath"],
                cwd=repo,
                text=True,
            ).strip()
            self.assertEqual("automation/hooks", configured_hook)
            smoke.write_text(
                "import unittest\n\n"
                "class Smoke(unittest.TestCase):\n"
                "    def test_candidate(self):\n"
                "        self.assertTrue(True)\n"
            )
            subprocess.run(["git", "add", str(smoke)], cwd=repo, check=True)

            prewarm = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    str(repo / "automation/run_test_gate.py"),
                    "final",
                    "--explicit",
                    "--staged",
                ],
                cwd=repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.assertEqual(0, prewarm.returncode, prewarm.stdout)
            final_report = json.loads(
                (repo / "tmp/test-gate-reports/latest-final.json").read_text()
            )
            final_full = next(
                component
                for component in final_report["components"]
                if component["component_id"] == "repository-tests/full"
            )
            self.assertEqual("executed", final_full["evidence"], final_report)
            markers = list(
                (repo / "tmp/test-gate-receipts").glob("*.commit.json")
            )
            self.assertEqual(1, len(markers))
            self.assertEqual(
                GATE.PUBLICATION_COMMIT_SCHEMA,
                json.loads(markers[0].read_text())["schema"],
            )

            committed = subprocess.run(
                ["git", "commit", "-m", "exercise canonical routine hook"],
                cwd=repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.assertEqual(0, committed.returncode, committed.stdout)
            self.assertIn("pre-commit: routine test gate", committed.stdout)
            routine_report = json.loads(
                (repo / "tmp/test-gate-reports/latest-routine.json").read_text()
            )
            routine_full = next(
                component
                for component in routine_report["components"]
                if component["component_id"] == "repository-tests/full"
            )
            self.assertEqual("reused", routine_full["evidence"], routine_report)
            self.assertEqual("pass", routine_report["outcome"], routine_report)
            self.assertEqual(
                [
                    "automation/tests/test_smoke.py",
                    "automation/tests/test_stable.py",
                ],
                routine_report["selected"],
            )
            self.assertEqual([], routine_report["deferred"])
            self.assertFalse(
                any(
                    component["component_id"] == "repository-tests/selected"
                    for component in routine_report["components"]
                ),
                routine_report,
            )

    def test_routine_without_receipt_brokers_deferred_before_deadline(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            self._make_gate_bootstrap_repository(repo)
            policy = repo / "agentfold.toml"
            policy.write_text(
                policy.read_text()
                .replace("target_seconds = 60", "target_seconds = 10", 1)
                .replace("maximum_seconds = 60", "maximum_seconds = 10", 1)
            )
            for relative in (
                "automation/check_core_scope.py",
                "automation/reconcile/reconcile.py",
            ):
                script = repo / relative
                script.parent.mkdir(parents=True, exist_ok=True)
                script.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n")
            smoke = repo / "automation/tests/test_smoke.py"
            smoke.parent.mkdir(parents=True)
            smoke.write_text(
                "import unittest\n\n"
                "class Smoke(unittest.TestCase):\n"
                "    pass\n"
            )
            stable = repo / "automation/tests/test_stable.py"
            stable.write_text(
                "import unittest\n\nclass Stable(unittest.TestCase):\n    pass\n"
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "ten-second routine floor"],
                cwd=repo,
                check=True,
            )
            smoke.write_text(
                "import time\n"
                "import unittest\n\n"
                "class Smoke(unittest.TestCase):\n"
                "    def test_slow(self):\n"
                "        time.sleep(30)\n\n"
                "if __name__ == '__main__':\n"
                "    unittest.main()\n"
            )
            subprocess.run(["git", "add", str(smoke)], cwd=repo, check=True)

            started = time.monotonic()
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    str(repo / "automation/run_test_gate.py"),
                    "routine",
                    "--staged",
                ],
                cwd=repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            elapsed = time.monotonic() - started
            report = json.loads(
                (repo / "tmp/test-gate-reports/latest-routine.json").read_text()
            )
            self.assertEqual(0, result.returncode, result.stdout)
            self.assertLess(elapsed, 10.0, result.stdout)
            self.assertEqual("deferred", report["outcome"], report)
            self.assertLess(report["decision"]["duration_seconds"], 9.75)
            selected = next(
                component
                for component in report["components"]
                if component["component_id"] == "repository-tests/selected"
            )
            self.assertEqual("incomplete", selected["outcome"], report)
            self.assertTrue(
                "execution interval" in selected["detail"]
                or "execution window expired" in selected["detail"],
                report,
            )
            receipts = repo / "tmp/test-gate-receipts"
            self.assertFalse(receipts.exists() and any(receipts.iterdir()))

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
        summaries = []
        with mock.patch.object(
            GATE, "_atomic_json", side_effect=PermissionError(13, "read only")
        ), mock.patch.object(GATE, "_write_summary", side_effect=summaries.append):
            exit_code = GATE.emit_report(report)
        self.assertEqual(2, exit_code)
        self.assertEqual("pass", report["outcome"])
        self.assertEqual("passed", report["reason"])
        self.assertTrue(report["terminalized_pass"])
        self.assertEqual(0, report["gate_exit_code"])
        self.assertEqual("error", report["publication_status"])
        self.assertIn("read only", report["publication_reason"])
        self.assertEqual("error", report["command_outcome"])
        self.assertEqual({"disposition": "failed"}, report["report_write"])
        self.assertIn("outcome: pass", summaries[0])
        self.assertIn("publication: error", summaries[0])
        self.assertIn("command: error (exit 2)", summaries[0])

    def test_unsafe_report_path_still_fails_closed(self):
        report = GATE._base_report("routine", time.monotonic())
        report.update({"outcome": "pass", "evidence": "executed", "reason": "passed"})
        summaries = []
        with mock.patch.object(
            GATE, "_safe_local_directory", side_effect=GATE.GateError("unsafe report path")
        ), mock.patch.object(GATE, "_write_summary", side_effect=summaries.append):
            exit_code = GATE.emit_report(report)
        self.assertEqual(2, exit_code)
        self.assertEqual("pass", report["outcome"])
        self.assertEqual("passed", report["reason"])
        self.assertTrue(report["terminalized_pass"])
        self.assertEqual(0, report["gate_exit_code"])
        self.assertEqual("error", report["publication_status"])
        self.assertEqual("unsafe report path", report["publication_reason"])
        self.assertEqual("error", report["command_outcome"])
        self.assertEqual({"disposition": "refused"}, report["report_write"])
        self.assertIn("outcome: pass", summaries[0])
        self.assertIn("publication: error", summaries[0])
        self.assertIn("command: error (exit 2)", summaries[0])

    def test_report_failure_preserves_a_blocked_gate_decision(self):
        report = GATE._base_report("final", 0.0)
        report.update(
            {
                "outcome": "blocked-incomplete",
                "evidence": "none",
                "reason": "required coverage incomplete",
                "incomplete": ["repository-tests/full"],
            }
        )
        persisted = []
        summaries = []

        def fail_then_project(_path, value):
            if not persisted:
                persisted.append(json.loads(json.dumps(value)))
                raise OSError("injected report failure")
            persisted.append(json.loads(json.dumps(value)))

        with mock.patch.object(
            GATE.time, "monotonic", return_value=0.25
        ), mock.patch.object(
            GATE, "_atomic_json", side_effect=fail_then_project
        ), mock.patch.object(
            GATE, "_write_summary", side_effect=summaries.append
        ):
            exit_code = GATE.emit_report(report, maximum=1.0)

        self.assertEqual(2, exit_code)
        self.assertEqual(2, len(persisted))
        frozen, error_projection = persisted
        for field in (
            "outcome",
            "reason",
            "duration_seconds",
            "maximum_seconds",
            "maximum_exceeded",
            "terminalized_pass",
            "gate_exit_code",
        ):
            self.assertEqual(frozen[field], error_projection[field])
        self.assertEqual("blocked-incomplete", error_projection["outcome"])
        self.assertEqual(1, error_projection["gate_exit_code"])
        self.assertEqual("error", error_projection["publication_status"])
        self.assertEqual("error", error_projection["command_outcome"])
        self.assertEqual(2, error_projection["exit_code"])
        self.assertIn("outcome: blocked-incomplete", summaries[0])
        self.assertIn("command: error (exit 2)", summaries[0])

    def test_stdout_is_outside_the_frozen_measured_interval(self):
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
        ), mock.patch.object(GATE, "_atomic_json"), mock.patch.object(
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

        self.assertEqual(0, exit_code)
        self.assertEqual("pass", report["outcome"])
        self.assertFalse(report["maximum_exceeded"])
        self.assertNotIn("budget_filing", report)
        self.assertEqual(1, len(summaries))

    def test_projection_is_single_and_outside_terminal_accounting(self):
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

        def persist(_path, value):
            persisted.append(json.loads(json.dumps(value)))
            clock[0] += 0.8

        def output(_summary):
            clock[0] += 0.9

        def file_breach(*_arguments):
            clock[0] += 0.1
            return {"disposition": "filed", "mutated": True}

        clock[0] = 0.4
        with mock.patch.object(GATE.time, "monotonic", side_effect=lambda: clock[0]), mock.patch.object(
            GATE, "_atomic_json", side_effect=persist
        ), mock.patch.object(
            GATE, "_write_summary", side_effect=output
        ), mock.patch.object(GATE, "file_target_breach", side_effect=file_breach):
            exit_code = GATE.emit_report(
                report,
                target=0.5,
                maximum=1.0,
                policy_digest="policy",
                options=options,
            )

        self.assertEqual(0, exit_code)
        self.assertEqual("pass", report["outcome"])
        self.assertFalse(report["maximum_exceeded"])
        self.assertNotIn("budget_filing", report)
        self.assertEqual(1, len(persisted))
        self.assertTrue(persisted[0]["terminalized_pass"])

    def test_reserved_boundary_raw_guard_runs_before_imports_git_and_state(self):
        facade = AUTOMATION / "run_test_gate.py"
        python = sys.executable
        variants = (
            ("final", "--provider-hard"),
            ("final", "--provider-hard=malformed"),
            ("final", "--provider-h"),
            ("final", "--provider-hard-extra"),
            ("final", "--provider-hard", "--provider-hard"),
            ("final", "--at-transition"),
            ("final", "--at-transition=pull-request"),
            ("final", "--at-trans"),
            ("final", "--at-transition-extra"),
            ("final", "--at-transition", "pull-request", "--at-transition=again"),
        )
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            poison = root / "poison"
            poison.mkdir()
            marker = root / "imported"
            payload = "from pathlib import Path\nPath({!r}).write_text(__name__)\n".format(
                str(marker)
            )
            for name in (
                "sitecustomize.py",
                "run_tests.py",
                "test_manifest.py",
                "test_gate_config.py",
                "file_test_budget_task.py",
            ):
                (poison / name).write_text(payload)
            git_marker = root / "git-ran"
            git = poison / "git"
            git.write_text("#!/bin/sh\nprintf ran > \"{}\"\nexit 99\n".format(git_marker))
            git.chmod(0o755)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(poison)
            environment["PATH"] = str(poison) + os.pathsep + environment.get("PATH", "")
            for arguments in variants:
                result = subprocess.run(
                    [python, "-I", "-S", str(facade), *arguments],
                    cwd=GATE.REPO,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertEqual(1, result.returncode, (arguments, result.stderr))
                self.assertIn('"outcome":"blocked-incomplete"', result.stdout)
                self.assertFalse(marker.exists(), arguments)
                self.assertFalse(git_marker.exists(), arguments)

    def test_loaded_module_path_audit_rejects_outside_dependency(self):
        original = GATE.run_tests.__file__
        try:
            GATE.run_tests.__file__ = "/tmp/attacker/run_tests.py"
            with self.assertRaisesRegex(GATE.GateError, "outside the execution snapshot"):
                GATE.loaded_module_paths()
        finally:
            GATE.run_tests.__file__ = original

    def test_facade_executes_staged_controller_not_unstaged_drift(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            self._make_gate_bootstrap_repository(repo)
            controller = repo / "automation/test_gate_controller.py"
            controller.write_text("raise SystemExit(77)\n" + controller.read_text())
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    str(repo / "automation/run_test_gate.py"),
                    "routine",
                    "--staged",
                    "--unexpected",
                ],
                cwd=repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertIn("unrecognized arguments: --unexpected", result.stderr)

    def test_gate_interval_start_requires_valid_handoff_monotonic_time(self):
        with mock.patch.object(GATE, "_HANDOFF", None), mock.patch.object(
            GATE, "PROCESS_STARTED", 123.5
        ):
            self.assertEqual(123.5, GATE.gate_interval_started())

        source, now = GATE._bootstrap_monotonic_start()
        with mock.patch.object(
            GATE,
            "_HANDOFF",
            self._clock_handoff(now - 2.0, source, now + 60.0),
        ):
            translated = GATE.gate_interval_started()
            self.assertGreaterEqual(time.monotonic() - translated, 2.0)
            self.assertLess(time.monotonic() - translated, 2.1)

        invalid = (-1, True, "earlier", float("nan"), float("inf"), now + 60.0)
        for value in invalid:
            with self.subTest(value=value), mock.patch.object(
                GATE,
                "_HANDOFF",
                self._clock_handoff(value, source, now + 60.0),
            ), mock.patch.object(GATE, "emit_report", return_value=2) as emit, mock.patch.object(
                GATE, "capture_candidate"
            ) as capture:
                self.assertEqual(2, GATE.main(("routine", "--staged")))
                report = emit.call_args[0][0]
                self.assertEqual("error", report["outcome"])
                expected_reason = (
                    "test-gate bootstrap monotonic bounds are invalid"
                    if GATE_GENERATION == DEADLINE_GENERATION
                    else "monotonic start is invalid"
                )
                self.assertIn(expected_reason, report["reason"])
                capture.assert_not_called()

    def test_cross_process_clock_fallback_survives_different_monotonic_epochs(self):
        times = (mock.Mock(elapsed=500.0), mock.Mock(elapsed=502.0))
        with mock.patch.object(GATE.time, "clock_gettime", None), mock.patch.object(
            GATE.os, "times", side_effect=times
        ), mock.patch.object(GATE.time, "monotonic", return_value=-300.0):
            source, started = GATE._bootstrap_monotonic_start()
            self.assertEqual(GATE._BOOTSTRAP_OS_TIMES_SOURCE, source)
            with mock.patch.object(
                GATE,
                "_HANDOFF",
                self._clock_handoff(started, source, started + 60.0),
            ):
                self.assertEqual(-302.0, GATE.gate_interval_started())

    def test_cross_process_clock_mismatch_and_unavailability_block(self):
        with mock.patch.object(
            GATE,
            "_HANDOFF",
            {
                "started_monotonic": 10.0,
                "started_monotonic_source": GATE._HANDOFF_OS_TIMES_SOURCE,
            },
        ), mock.patch.object(
            GATE,
            "_controller_monotonic_sample",
            return_value=(GATE._HANDOFF_CLOCK_GETTIME_SOURCE, 11.0),
        ), mock.patch.object(GATE, "emit_report", return_value=2) as emit:
            self.assertEqual(2, GATE.main(("routine", "--staged")))
            self.assertIn("source mismatch", emit.call_args[0][0]["reason"])

        with mock.patch.object(GATE.time, "clock_gettime", None), mock.patch.object(
            GATE.os, "times", side_effect=OSError("unavailable")
        ), mock.patch.object(GATE, "_freeze") as freeze:
            with self.assertRaisesRegex(RuntimeError, "cross-process monotonic"):
                GATE._dispatch(("routine", "--staged"))
            freeze.assert_not_called()

        with mock.patch.object(
            GATE,
            "_HANDOFF",
            {
                "started_monotonic": 10.0,
                "started_monotonic_source": GATE._HANDOFF_OS_TIMES_SOURCE,
            },
        ), mock.patch.object(GATE.time, "clock_gettime", None), mock.patch.object(
            GATE.os, "times", side_effect=OSError("unavailable")
        ), mock.patch.object(GATE, "emit_report", return_value=2) as emit:
            self.assertEqual(2, GATE.main(("routine", "--staged")))
            self.assertIn("no supported cross-process", emit.call_args[0][0]["reason"])

    def test_bootstrap_elapsed_counts_toward_maximum_before_components(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            repo = root / "repo"
            self._make_gate_bootstrap_repository(repo)
            smoke = repo / "automation/tests/test_smoke.py"
            smoke.parent.mkdir(parents=True)
            smoke.write_text("import unittest\n\nclass Smoke(unittest.TestCase):\n    pass\n")
            workflow = repo / ".github/workflows/harness.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "test floor"], cwd=repo, check=True)
            workflow.write_text("name: candidate\n")
            subprocess.run(["git", "add", str(workflow)], cwd=repo, check=True)
            capture = root / "capture"
            capture.mkdir()
            bootstrap_source, bootstrap_now = GATE._bootstrap_monotonic_start()
            bootstrap_started = bootstrap_now - 901.0
            arguments = ("final", "--explicit", "--staged")
            handoff = self._freeze_for_generation(
                repo,
                arguments,
                capture,
                bootstrap_started,
                bootstrap_source,
            )
            snapshot = Path(handoff["execution_root"])
            handoff_path = capture / "handoff.json"
            handoff_path.write_text(json.dumps(handoff))
            handoff_path.chmod(0o400)
            environment = os.environ.copy()
            environment["AGENTFOLD_GATE_HANDOFF"] = str(handoff_path)
            environment["AGENTFOLD_GATE_SOURCE_REPO"] = str(repo)
            environment["AGENTFOLD_GATE_EXECUTION_ROOT"] = str(snapshot)
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    str(snapshot / "automation/test_gate_controller.py"),
                    "final",
                    "--explicit",
                    "--staged",
                ],
                cwd=snapshot,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            report = json.loads(
                (repo / "tmp/test-gate-reports/latest-final.json").read_text()
            )
            expected_returncode = (
                2 if GATE_GENERATION == DEADLINE_GENERATION else 1
            )
            self.assertEqual(
                expected_returncode,
                result.returncode,
                result.stdout + result.stderr,
            )
            self.assertGreaterEqual(report["duration_seconds"], 901.0)
            if GATE_GENERATION == DEADLINE_GENERATION:
                self.assertEqual("error", report["outcome"])
                self.assertEqual(
                    "configured absolute deadline expired during controller admission",
                    report["reason"],
                )
                self.assertEqual([], report["components"])
            else:
                self.assertTrue(report["maximum_exceeded"])
                self.assertEqual("blocked-incomplete", report["outcome"])
                self.assertEqual(
                    "core-scope", report["components"][0]["component_id"]
                )
                self.assertEqual("none", report["components"][0]["evidence"])
            self.assertFalse(
                (repo / "tmp/test-gate-receipts").exists()
                and any((repo / "tmp/test-gate-receipts").iterdir())
            )

    def test_snapshot_closure_mutation_blocks_before_component_execution(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            repo = root / "repo"
            self._make_gate_bootstrap_repository(repo)
            capture = root / "capture"
            capture.mkdir()
            source, started = GATE._bootstrap_monotonic_start()
            handoff = self._freeze_for_generation(
                repo, ("routine", "--staged"), capture, started, source
            )
            snapshot = Path(handoff["execution_root"])
            frozen_index = Path(handoff["frozen_index"])
            self.assertEqual(
                handoff["frozen_index_sha256"], MANIFEST.file_digest(frozen_index)
            )
            self.assertEqual(0o400, frozen_index.stat().st_mode & 0o777)
            GATE._unseal_snapshot(snapshot)
            runner = snapshot / "automation/run_tests.py"
            runner.write_text(runner.read_text() + "\n# closure mutation\n")
            handoff_path = capture / "handoff.json"
            handoff_path.write_text(json.dumps(handoff))
            environment = os.environ.copy()
            environment["AGENTFOLD_GATE_HANDOFF"] = str(handoff_path)
            environment["AGENTFOLD_GATE_SOURCE_REPO"] = str(repo)
            environment["AGENTFOLD_GATE_EXECUTION_ROOT"] = str(snapshot)
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    str(snapshot / "automation/test_gate_controller.py"),
                    "routine",
                    "--staged",
                ],
                cwd=snapshot,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertIn("controller closure changed after candidate capture", result.stdout)
            self.assertIn("component timings:\n  (none)", result.stdout)

    def test_source_index_drift_after_capture_blocks_before_components(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            repo = root / "repo"
            self._make_gate_bootstrap_repository(repo)
            capture = root / "capture"
            capture.mkdir()
            source, started = GATE._bootstrap_monotonic_start()
            handoff = self._freeze_for_generation(
                repo, ("routine", "--staged"), capture, started, source
            )
            snapshot = Path(handoff["execution_root"])
            handoff_path = capture / "handoff.json"
            handoff_path.write_text(json.dumps(handoff))
            (repo / "agentfold.toml").write_text(
                (repo / "agentfold.toml").read_text() + "\n# semantic source drift\n"
            )
            subprocess.run(["git", "add", "agentfold.toml"], cwd=repo, check=True)
            environment = os.environ.copy()
            environment["AGENTFOLD_GATE_HANDOFF"] = str(handoff_path)
            environment["AGENTFOLD_GATE_SOURCE_REPO"] = str(repo)
            environment["AGENTFOLD_GATE_EXECUTION_ROOT"] = str(snapshot)
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    str(snapshot / "automation/test_gate_controller.py"),
                    "routine",
                    "--staged",
                ],
                cwd=snapshot,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertIn("drifted before execution", result.stdout)
            self.assertIn("component timings:\n  (none)", result.stdout)

    def test_component_index_mutation_blocks_later_components_and_receipt(self):
        source_repo = GATE.REPO
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            self._make_gate_bootstrap_repository(repo)
            smoke = repo / "automation/tests/test_smoke.py"
            smoke.parent.mkdir(parents=True)
            smoke.write_text("import unittest\n\nclass Smoke(unittest.TestCase):\n    pass\n")
            workflow = repo / ".github/workflows/harness.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "test floor"], cwd=repo, check=True)
            workflow.write_text("name: candidate\n")
            subprocess.run(["git", "add", str(workflow)], cwd=repo, check=True)
            live_index = MANIFEST.selected_index_path(repo)
            live_before = MANIFEST.file_digest(live_index)
            later_marker = Path(scratch) / "later-component-ran"
            mutate_copy = [
                sys.executable,
                "-c",
                "import subprocess; subprocess.run(['git','read-tree','HEAD'],check=True)",
            ]
            later = [
                sys.executable,
                "-c",
                "from pathlib import Path; Path({!r}).write_text('ran')".format(
                    str(later_marker)
                ),
            ]
            admissions = (("core-scope", mutate_copy), ("reconcile", later))
            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE, "admission_commands", return_value=admissions
            ), mock.patch.object(GATE, "_write_summary"):
                exit_code = GATE.main(
                    ("final", "--explicit", "--staged"),
                    started=time.monotonic(),
                )
            report = json.loads(
                (repo / "tmp/test-gate-reports/latest-final.json").read_text()
            )
            self.assertEqual(1, exit_code, report)
            self.assertEqual("blocked-incomplete", report["outcome"])
            self.assertEqual(1, len(report["components"]))
            self.assertIn(
                "disposable component index changed",
                report["components"][0]["detail"],
            )
            self.assertFalse(later_marker.exists())
            self.assertEqual(live_before, MANIFEST.file_digest(live_index))
            receipts = repo / "tmp/test-gate-receipts"
            self.assertFalse(receipts.exists() and any(receipts.iterdir()))
        self.assertEqual(source_repo, GATE.REPO)

    def test_frozen_index_read_only_mode_chmod_and_replacement_are_detected(self):
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
            (repo / "tracked.txt").write_text("tracked\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            frozen = Path(scratch) / "candidate.index"
            MANIFEST.copy_staged_index(repo, frozen)
            base = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()
            with mock.patch.object(GATE, "REPO", repo):
                identity = GATE.seal_authoritative_frozen_index(frozen, base)
                self.assertEqual(0o400, frozen.stat().st_mode & 0o777)
                self.assertTrue(GATE.frozen_index_matches(frozen, base, identity))
                frozen.chmod(0o600)
                self.assertFalse(GATE.frozen_index_matches(frozen, base, identity))
                frozen.chmod(0o400)
                self.assertTrue(GATE.frozen_index_matches(frozen, base, identity))
                replacement = Path(scratch) / "replacement.index"
                replacement.write_bytes(frozen.read_bytes())
                replacement.chmod(0o400)
                os.replace(str(replacement), str(frozen))
                self.assertFalse(GATE.frozen_index_matches(frozen, base, identity))

    def test_environment_identity_strips_pythonpath_and_snapshot_paths(self):
        first = {
            "PATH": "/bin",
            "PYTHONPATH": "/one",
            "GIT_DIR": "/source/.git",
            "GIT_INDEX_FILE": "/private/random-one/index",
            "GIT_WORK_TREE": "/private/random-one/snapshot",
        }
        moved = dict(first)
        moved["GIT_INDEX_FILE"] = "/private/random-two/index"
        moved["GIT_WORK_TREE"] = "/private/random-two/snapshot"
        changed = dict(moved)
        changed["PYTHONPATH"] = "/two"
        self.assertEqual(
            GATE.environment_identity(first)["component_environment_digest"],
            GATE.environment_identity(moved)["component_environment_digest"],
        )
        self.assertEqual(
            GATE.environment_identity(first)["component_environment_digest"],
            GATE.environment_identity(changed)["component_environment_digest"],
        )
        identity = GATE.environment_identity(first)["interpreter_identity"]
        self.assertIn("controller", identity)
        self.assertIn("child", identity)
        self.assertEqual(1, identity["child"]["isolated"])
        self.assertEqual(1, identity["child"]["no_site"])
        self.assertEqual(1, identity["child"]["ignore_environment"])
        self.assertEqual(
            identity, GATE.controller_closure()["interpreter_identity"]
        )

    def test_exact_maximum_terminalizes_before_projection(self):
        report = GATE._base_report("final", 0.0)
        report.update(
            {
                "outcome": "pass",
                "evidence": "executed",
                "reason": "passed",
                "critical": {"is_critical": True},
            }
        )
        with mock.patch.object(GATE.time, "monotonic", return_value=1.0), mock.patch.object(
            GATE, "_atomic_json"
        ), mock.patch.object(GATE, "_write_summary"):
            exit_code = GATE.emit_report(report, maximum=1.0)
        self.assertEqual(1, exit_code)
        self.assertTrue(report["maximum_exceeded"])
        self.assertEqual("blocked-incomplete", report["outcome"])
        self.assertFalse(report["terminalized_pass"])

    def test_target_filing_accounts_once_then_freezes_without_correction(self):
        report = GATE._base_report("routine", 0.0)
        report.update(
            {
                "outcome": "pass",
                "evidence": "executed",
                "reason": "passed",
                "candidate": {"digest": "candidate"},
            }
        )
        options = mock.Mock(at_transition=None, explicit=False)
        with mock.patch.object(GATE.time, "monotonic", return_value=0.6), mock.patch.object(
            GATE, "file_target_breach", return_value={"disposition": "filed", "mutated": True}
        ) as filing, mock.patch.object(GATE, "_atomic_json") as persist, mock.patch.object(
            GATE, "_write_summary"
        ) as summary, mock.patch.object(
            GATE, "_bounded_json_call", side_effect=lambda call, _deadline: (True, call())
        ):
            exit_code = GATE.emit_report(
                report,
                target=0.5,
                maximum=1.0,
                policy_digest="policy",
                options=options,
            )
        self.assertEqual(0, exit_code)
        self.assertEqual(0.6, report["duration_seconds"])
        self.assertTrue(report["target_exceeded"])
        self.assertFalse(report["maximum_exceeded"])
        filing.assert_called_once()
        persist.assert_called_once()
        summary.assert_called_once()

    def test_receipt_projects_only_after_terminal_full_composite_pass(self):
        closure = GATE.controller_closure()
        binding = {
            "binding_digest": "a" * 64,
            "candidate_digest": "candidate",
            "candidate_closure_digest": "closure",
            "controller_closure": closure,
            "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
        }
        report = GATE._base_report("final", 0.0)
        report.update(
            {
                "outcome": "pass",
                "evidence": "executed",
                "reason": "passed",
                "candidate": {"digest": "candidate", "closure_digest": "closure"},
            }
        )
        persisted = []
        with mock.patch.object(GATE.time, "monotonic", return_value=0.1), mock.patch.object(
            GATE, "_atomic_json", side_effect=lambda path, value: persisted.append((path, value))
        ), mock.patch.object(GATE, "_write_summary"):
            exit_code = GATE.emit_report(
                report,
                receipt_binding_value=binding,
                receipt_stable=lambda: True,
            )
        self.assertEqual(0, exit_code)
        self.assertEqual(3, len(persisted))
        self.assertEqual(GATE.RECEIPT_SCHEMA, persisted[0][1]["schema"])
        self.assertEqual(GATE.REPORT_SCHEMA, persisted[1][1]["schema"])
        self.assertEqual(GATE.PUBLICATION_COMMIT_SCHEMA, persisted[2][1]["schema"])
        self.assertTrue(persisted[0][1]["terminalized_pass"])
        self.assertEqual("success", persisted[0][1]["publication"]["status"])
        self.assertEqual("pass", persisted[0][1]["command_outcome"])
        self.assertEqual("success", persisted[1][1]["publication_status"])
        self.assertEqual("pass", persisted[1][1]["command_outcome"])
        self.assertEqual(
            persisted[1][1]["publication_id"],
            persisted[0][1]["publication"]["id"],
        )
        self.assertEqual(
            MANIFEST.canonical_digest(persisted[1][1]),
            persisted[0][1]["publication"]["report_digest"],
        )
        self.assertEqual(
            MANIFEST.canonical_digest(persisted[0][1]),
            persisted[2][1]["receipt"]["digest"],
        )
        self.assertEqual(
            MANIFEST.canonical_digest(persisted[1][1]),
            persisted[2][1]["report"]["digest"],
        )

    def test_broken_stdout_never_commits_receipt_even_if_cleanup_and_rewrite_fail(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "1" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            report = GATE._base_report("final", 0.0)
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original = GATE._atomic_json
            report_writes = [0]

            def reject_error_rewrite(path, value):
                if "test-gate-reports" in str(path):
                    report_writes[0] += 1
                    if report_writes[0] > 1:
                        raise OSError("injected rewrite failure")
                original(path, value)

            stderr = io.StringIO()
            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE.time, "monotonic", return_value=0.25
            ), mock.patch.object(
                GATE, "_atomic_json", side_effect=reject_error_rewrite
            ), mock.patch.object(
                GATE, "_write_summary", side_effect=BrokenPipeError("closed")
            ), mock.patch.object(
                GATE, "_remove_projection", return_value=False
            ), mock.patch.object(GATE.sys, "stderr", stderr):
                exit_code = GATE.emit_report(
                    report,
                    maximum=1.0,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )

            receipt_path, marker_path = (
                repo / "tmp/test-gate-receipts" / ("1" * 64 + ".json"),
                repo / "tmp/test-gate-receipts" / ("1" * 64 + ".commit.json"),
            )
            self.assertEqual(2, exit_code)
            self.assertEqual("pass", report["outcome"])
            self.assertEqual("passed", report["reason"])
            self.assertEqual(0.25, report["duration_seconds"])
            self.assertFalse(report["maximum_exceeded"])
            self.assertTrue(report["terminalized_pass"])
            self.assertEqual(0, report["gate_exit_code"])
            self.assertEqual("error", report["publication_status"])
            self.assertEqual("error", report["command_outcome"])
            self.assertEqual(2, report["exit_code"])
            self.assertTrue(receipt_path.is_file())
            self.assertFalse(marker_path.exists())
            self.assertIn("stdout summary publication failed", stderr.getvalue())
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNone(GATE.reusable_receipt(binding))

    def test_marker_write_failure_invalidates_receipt_and_reports_command_error(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "2" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            report = GATE._base_report("final", 0.0)
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original = GATE._atomic_json

            def fail_marker(path, value):
                if str(path).endswith(".commit.json"):
                    raise OSError("injected marker failure")
                original(path, value)

            stderr = io.StringIO()
            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE.time, "monotonic", return_value=0.25
            ), mock.patch.object(
                GATE, "_atomic_json", side_effect=fail_marker
            ), mock.patch.object(GATE, "_write_summary"), mock.patch.object(
                GATE.sys, "stderr", stderr
            ):
                exit_code = GATE.emit_report(
                    report,
                    maximum=1.0,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )

            receipt_path, marker_path = (
                repo / "tmp/test-gate-receipts" / ("2" * 64 + ".json"),
                repo / "tmp/test-gate-receipts" / ("2" * 64 + ".commit.json"),
            )
            persisted = json.loads(
                (repo / "tmp/test-gate-reports/latest-final.json").read_text()
            )
            self.assertEqual(2, exit_code)
            self.assertEqual("pass", persisted["outcome"])
            self.assertEqual("passed", persisted["reason"])
            self.assertEqual(0.25, persisted["duration_seconds"])
            self.assertFalse(persisted["maximum_exceeded"])
            self.assertTrue(persisted["terminalized_pass"])
            self.assertEqual(0, persisted["gate_exit_code"])
            self.assertEqual("error", persisted["publication_status"])
            self.assertIn("commit marker failed", persisted["publication_reason"])
            self.assertEqual("error", persisted["command_outcome"])
            self.assertEqual(2, persisted["exit_code"])
            self.assertFalse(receipt_path.exists())
            self.assertFalse(marker_path.exists())
            self.assertIn("publication commit marker failed", stderr.getvalue())
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNone(GATE.reusable_receipt(binding))

    def test_marker_directory_fsync_failure_after_rename_keeps_committed_pass(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "5" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            report = GATE._base_report("final", 0.0)
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original_fsync = GATE.os.fsync
            calls = [0]

            def fail_marker_directory_sync(descriptor):
                calls[0] += 1
                if calls[0] == 6:
                    raise OSError("injected post-rename directory fsync failure")
                return original_fsync(descriptor)

            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE.time, "monotonic", return_value=0.25
            ), mock.patch.object(
                GATE.os, "fsync", side_effect=fail_marker_directory_sync
            ), mock.patch.object(GATE, "_write_summary"):
                exit_code = GATE.emit_report(
                    report,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )

            self.assertEqual(6, calls[0])
            self.assertEqual(0, exit_code)
            self.assertEqual("pass", report["outcome"])
            self.assertEqual("success", report["publication_status"])
            self.assertEqual("pass", report["command_outcome"])
            self.assertEqual(0, report["exit_code"])
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNotNone(GATE.reusable_receipt(binding))

    def test_marker_file_fsync_failure_before_rename_fails_publication(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "6" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            report = GATE._base_report("final", 0.0)
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original_fsync = GATE.os.fsync
            calls = [0]

            def fail_marker_file_sync(descriptor):
                calls[0] += 1
                if calls[0] == 5:
                    raise OSError("injected pre-rename file fsync failure")
                return original_fsync(descriptor)

            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE.time, "monotonic", return_value=0.25
            ), mock.patch.object(
                GATE.os, "fsync", side_effect=fail_marker_file_sync
            ), mock.patch.object(GATE, "_write_summary"), mock.patch.object(
                GATE, "_write_publication_error"
            ):
                exit_code = GATE.emit_report(
                    report,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )

            receipt_path = (
                repo / "tmp/test-gate-receipts" / ("6" * 64 + ".json")
            )
            marker_path = (
                repo / "tmp/test-gate-receipts" / ("6" * 64 + ".commit.json")
            )
            self.assertGreaterEqual(calls[0], 7)
            self.assertEqual(2, exit_code)
            self.assertEqual("pass", report["outcome"])
            self.assertEqual("error", report["publication_status"])
            self.assertEqual("error", report["command_outcome"])
            self.assertEqual(2, report["exit_code"])
            self.assertFalse(receipt_path.exists())
            self.assertFalse(marker_path.exists())
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNone(GATE.reusable_receipt(binding))

    def test_marker_directory_close_failure_after_rename_keeps_committed_pass(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "7" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            report = GATE._base_report("final", 0.0)
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original_close = GATE.os.close
            original_atomic = GATE._atomic_json
            close_calls = [0]
            atomic_calls = [0]
            (repo / "tmp/test-gate-reports").mkdir(parents=True)
            (repo / "tmp/test-gate-receipts").mkdir(parents=True)

            def fail_marker_directory_close(descriptor):
                close_calls[0] += 1
                result = original_close(descriptor)
                if close_calls[0] == 6:
                    raise OSError("injected post-rename directory close failure")
                return result

            def reject_any_error_rewrite(path, value):
                atomic_calls[0] += 1
                if atomic_calls[0] > 3:
                    raise OSError("injected report rewrite failure")
                return original_atomic(path, value)

            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE.time, "monotonic", return_value=0.25
            ), mock.patch.object(
                GATE,
                "_safe_local_directory",
                side_effect=lambda relative: repo / relative,
            ), mock.patch.object(
                GATE, "controller_closure", return_value=binding["controller_closure"]
            ), mock.patch.object(
                GATE.os, "close", side_effect=fail_marker_directory_close
            ), mock.patch.object(
                GATE, "_atomic_json", side_effect=reject_any_error_rewrite
            ), mock.patch.object(GATE, "_write_summary"), mock.patch.object(
                GATE, "_remove_projection", return_value=False
            ) as cleanup:
                exit_code = GATE.emit_report(
                    report,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )

            self.assertEqual(6, close_calls[0])
            self.assertEqual(3, atomic_calls[0])
            cleanup.assert_not_called()
            self.assertEqual(0, exit_code)
            self.assertEqual("pass", report["outcome"])
            self.assertEqual("success", report["publication_status"])
            self.assertEqual("pass", report["command_outcome"])
            self.assertEqual(0, report["exit_code"])
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNotNone(GATE.reusable_receipt(binding))

    def test_marker_file_close_failure_before_rename_fails_publication(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "8" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            report = GATE._base_report("final", 0.0)
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original_close = GATE.os.close
            close_calls = [0]
            (repo / "tmp/test-gate-reports").mkdir(parents=True)
            (repo / "tmp/test-gate-receipts").mkdir(parents=True)

            def fail_marker_file_close(descriptor):
                close_calls[0] += 1
                result = original_close(descriptor)
                if close_calls[0] == 5:
                    raise OSError("injected pre-rename file close failure")
                return result

            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE.time, "monotonic", return_value=0.25
            ), mock.patch.object(
                GATE,
                "_safe_local_directory",
                side_effect=lambda relative: repo / relative,
            ), mock.patch.object(
                GATE, "controller_closure", return_value=binding["controller_closure"]
            ), mock.patch.object(
                GATE.os, "close", side_effect=fail_marker_file_close
            ), mock.patch.object(GATE, "_write_summary"), mock.patch.object(
                GATE, "_write_publication_error"
            ):
                exit_code = GATE.emit_report(
                    report,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )

            receipt_path = (
                repo / "tmp/test-gate-receipts" / ("8" * 64 + ".json")
            )
            marker_path = (
                repo / "tmp/test-gate-receipts" / ("8" * 64 + ".commit.json")
            )
            self.assertGreaterEqual(close_calls[0], 8)
            self.assertEqual(2, exit_code)
            self.assertEqual("pass", report["outcome"])
            self.assertEqual("error", report["publication_status"])
            self.assertEqual("error", report["command_outcome"])
            self.assertEqual(2, report["exit_code"])
            self.assertFalse(receipt_path.exists())
            self.assertFalse(marker_path.exists())
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNone(GATE.reusable_receipt(binding))

    def test_receipt_requires_matching_publication_commit_marker(self):
        candidate = MANIFEST.CandidateManifest(
            "staged-index", "candidate", "closure", (), (), "index"
        )
        view = {"digest": "view"}
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            with mock.patch.object(GATE, "REPO", repo):
                binding = GATE.receipt_binding(
                    candidate,
                    view,
                    ("test.py",),
                    "policy",
                    "repository-tests/full",
                )
                self._publish_receipt_pair(binding)
                receipt_path, marker_path = GATE._receipt_cache_paths(binding)
                original_marker = json.loads(marker_path.read_text())
                self.assertIsNotNone(GATE.reusable_receipt(binding))

                marker_path.unlink()
                self.assertIsNone(GATE.reusable_receipt(binding))

                GATE._atomic_json(marker_path, original_marker)
                stale = dict(original_marker)
                stale["publication_id"] = "3" * 64
                GATE._atomic_json(marker_path, stale)
                self.assertIsNone(GATE.reusable_receipt(binding))

                GATE._atomic_json(marker_path, original_marker)
                tampered = dict(original_marker)
                tampered["receipt"] = dict(original_marker["receipt"])
                tampered["receipt"]["digest"] = "4" * 64
                GATE._atomic_json(marker_path, tampered)
                self.assertIsNone(GATE.reusable_receipt(binding))

                GATE._atomic_json(marker_path, original_marker)
                receipt = json.loads(receipt_path.read_text())
                receipt["publication"]["commit_marker_path"] = (
                    "tmp/test-gate-receipts/elsewhere.commit.json"
                )
                GATE._atomic_json(receipt_path, receipt)
                self.assertIsNone(GATE.reusable_receipt(binding))

    def test_receipt_publication_failure_never_publishes_pass_report(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "b" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            report = GATE._base_report("final", time.monotonic())
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original = GATE._atomic_json

            def fail_receipt(path, value):
                if "test-gate-receipts" in str(path):
                    raise OSError("injected receipt failure")
                original(path, value)

            summaries = []
            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE, "_atomic_json", side_effect=fail_receipt
            ), mock.patch.object(
                GATE, "_write_summary", side_effect=summaries.append
            ):
                exit_code = GATE.emit_report(
                    report,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )
            self.assertEqual(2, exit_code)
            persisted = json.loads(
                (repo / "tmp/test-gate-reports/latest-final.json").read_text()
            )
            self.assertEqual("pass", persisted["outcome"])
            self.assertEqual("passed", persisted["reason"])
            self.assertTrue(persisted["terminalized_pass"])
            self.assertEqual(0, persisted["gate_exit_code"])
            self.assertEqual("error", persisted["publication_status"])
            self.assertIn("receipt persistence failed", persisted["publication_reason"])
            self.assertEqual("error", persisted["command_outcome"])
            self.assertEqual(2, persisted["exit_code"])
            self.assertIn("publication_id", persisted)
            self.assertIn("outcome: pass", summaries[0])
            self.assertIn("publication: error", summaries[0])
            self.assertIn("command: error (exit 2)", summaries[0])
            self.assertFalse(
                (repo / "tmp/test-gate-receipts" / ("b" * 64 + ".json")).exists()
            )
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNone(GATE.reusable_receipt(binding))

    def test_report_publication_failure_rolls_back_new_receipt(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "c" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            receipt_path = repo / "tmp/test-gate-receipts" / ("c" * 64 + ".json")
            receipt_path.parent.mkdir(parents=True)
            receipt_path.write_text("invalid prior cache entry")
            report = GATE._base_report("final", time.monotonic())
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original = GATE._atomic_json
            report_writes = [0]

            def fail_first_report(path, value):
                if "test-gate-reports" in str(path):
                    report_writes[0] += 1
                    if report_writes[0] == 1:
                        raise OSError("injected pass-report failure")
                original(path, value)

            summaries = []
            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE, "_atomic_json", side_effect=fail_first_report
            ), mock.patch.object(
                GATE, "_write_summary", side_effect=summaries.append
            ):
                exit_code = GATE.emit_report(
                    report,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )
            self.assertEqual(2, exit_code)
            persisted = json.loads(
                (repo / "tmp/test-gate-reports/latest-final.json").read_text()
            )
            self.assertEqual("pass", persisted["outcome"])
            self.assertEqual("passed", persisted["reason"])
            self.assertTrue(persisted["terminalized_pass"])
            self.assertEqual(0, persisted["gate_exit_code"])
            self.assertEqual("error", persisted["publication_status"])
            self.assertIn("machine report persistence failed", persisted["publication_reason"])
            self.assertEqual("error", persisted["command_outcome"])
            self.assertEqual(2, persisted["exit_code"])
            self.assertIn("outcome: pass", summaries[0])
            self.assertIn("publication: error", summaries[0])
            self.assertIn("command: error (exit 2)", summaries[0])
            self.assertFalse(receipt_path.exists())
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNone(GATE.reusable_receipt(binding))

    def test_surviving_receipt_after_report_failure_is_not_reusable(self):
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch)
            (repo / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            binding = {
                "binding_digest": "e" * 64,
                "candidate_digest": "candidate",
                "candidate_closure_digest": "closure",
                "controller_closure": GATE.controller_closure(),
                "composite_test_plan": {"schema": GATE.COMPOSITE_TEST_PLAN_SCHEMA},
            }
            report = GATE._base_report("final", time.monotonic())
            report.update(
                {
                    "outcome": "pass",
                    "evidence": "executed",
                    "reason": "passed",
                    "candidate": {
                        "digest": "candidate",
                        "closure_digest": "closure",
                    },
                }
            )
            original = GATE._atomic_json
            report_writes = [0]

            def fail_pass_report(path, value):
                if "test-gate-reports" in str(path):
                    report_writes[0] += 1
                    if report_writes[0] == 1:
                        raise OSError("injected pass-report failure")
                original(path, value)

            with mock.patch.object(GATE, "REPO", repo), mock.patch.object(
                GATE, "_atomic_json", side_effect=fail_pass_report
            ), mock.patch.object(
                GATE, "_remove_projection", return_value=False
            ), mock.patch.object(GATE, "_write_summary"):
                exit_code = GATE.emit_report(
                    report,
                    receipt_binding_value=binding,
                    receipt_stable=lambda: True,
                )
            self.assertEqual(2, exit_code)
            receipt_path = repo / "tmp/test-gate-receipts" / ("e" * 64 + ".json")
            self.assertTrue(receipt_path.is_file())
            persisted_report = json.loads(
                (repo / "tmp/test-gate-reports/latest-final.json").read_text()
            )
            self.assertEqual("pass", persisted_report["outcome"])
            self.assertTrue(persisted_report["terminalized_pass"])
            self.assertEqual(0, persisted_report["gate_exit_code"])
            self.assertEqual("error", persisted_report["publication_status"])
            self.assertEqual("error", persisted_report["command_outcome"])
            self.assertEqual(2, persisted_report["exit_code"])
            options = mock.Mock(provider_hard=False)
            with mock.patch.object(GATE, "REPO", repo):
                self.assertIsNone(
                    GATE.reusable_full_receipt(
                        binding, "repository-tests/full", options
                    )
                )

    def test_stale_pass_report_publication_id_mismatch_rejects_receipt(self):
        candidate = MANIFEST.CandidateManifest(
            "staged-index", "candidate", "closure", (), (), "index"
        )
        view = {"digest": "view"}
        with mock.patch.object(GATE, "REPO", Path(tempfile.mkdtemp())):
            (GATE.REPO / ".gitignore").write_text("tmp/\n")
            subprocess.run(["git", "init", "-q"], cwd=GATE.REPO, check=True)
            binding = GATE.receipt_binding(
                candidate,
                view,
                ("test.py",),
                "policy",
                "repository-tests/full",
            )
            report = self._publish_receipt_pair(binding)
            self.assertIsNotNone(GATE.reusable_receipt(binding))
            report["publication_id"] = "f" * 64
            report_path = GATE.REPO / "tmp/test-gate-reports/latest-final.json"
            GATE._atomic_json(report_path, report)
            self.assertIsNone(GATE.reusable_receipt(binding))


if __name__ == "__main__":
    unittest.main()
