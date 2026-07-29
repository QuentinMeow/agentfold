#!/usr/bin/env python3
"""Strict regressions for the supervised absolute-deadline gate protocol."""

import importlib.util
import json
import os
import shutil
import socket
import stat
import struct
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


AUTOMATION = Path(__file__).resolve().parents[1]
GENERATION_PATH = AUTOMATION / "tests" / "test_gate_generations.py"
GENERATION_SPEC = importlib.util.spec_from_file_location(
    "deadline_protocol_gate_generations", GENERATION_PATH
)
GATE_GENERATIONS = importlib.util.module_from_spec(GENERATION_SPEC)
GENERATION_SPEC.loader.exec_module(GATE_GENERATIONS)
GATE_GENERATIONS.gate_generation(AUTOMATION.parent)
PRODUCT_RECORDS = GATE_GENERATIONS.gate_generation_records(AUTOMATION.parent)
PARSER_COMPAT_ENDPOINT = "parser-compat"
REVIEW_REPAIR_ENDPOINT = "review-repair"
if PRODUCT_RECORDS == GATE_GENERATIONS.PARSER_COMPAT_RECORDS:
    PRODUCT_ENDPOINT = PARSER_COMPAT_ENDPOINT
elif PRODUCT_RECORDS == GATE_GENERATIONS.REVIEW_REPAIR_RECORDS:
    PRODUCT_ENDPOINT = REVIEW_REPAIR_ENDPOINT
elif PRODUCT_RECORDS == GATE_GENERATIONS.PANEL_REPAIR_RECORDS:
    PRODUCT_ENDPOINT = REVIEW_REPAIR_ENDPOINT
else:
    raise AssertionError(
        "deadline endpoint is neither exact parser-compat nor exact review-repair"
    )

SPEC = importlib.util.spec_from_file_location(
    "deadline_protocol_gate", AUTOMATION / "run_test_gate.py"
)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def signed_policy_frame(maximum=5.0, target=5.0):
    closure = [
        {"path": path, "mode": "100644", "sha256": "1" * 64}
        for path in GATE._POLICY_CLOSURE_PATHS
    ]
    frame = {
        "schema": GATE.POLICY_FRAME_SCHEMA,
        "gate_id": "routine",
        "target_seconds": target,
        "maximum_seconds": maximum,
        "budgets": {
            "routine": {"target_seconds": target, "maximum_seconds": maximum},
            "final": {"target_seconds": 300.0, "maximum_seconds": 900.0},
        },
        "discovery_ceiling_seconds": GATE.DISCOVERY_CEILING_SECONDS,
        "policy_digest": "2" * 64,
        "base_config_sha256": "3" * 64,
        "candidate_config_sha256": "4" * 64,
        "trusted_parser_closure": closure,
        "trusted_parser_closure_digest": GATE._sha256_bytes(GATE._canonical_json(closure)),
        "candidate_parser_closure_digest": "7" * 64,
        "authoritative_index": {
            "file_sha256": "8" * 64,
            "semantic_sha256": "9" * 64,
        },
        "launcher": {
            "path": "automation/run_test_gate.py",
            "sha256": "5" * 64,
        },
        "candidate_kind": "staged-index",
        "base_revision": "6" * 40,
        "candidate_revision": "",
    }
    frame["frame_digest"] = GATE._sha256_bytes(GATE._canonical_json(frame))
    return frame


class DeadlineProtocolTests(unittest.TestCase):
    @staticmethod
    def _controller_claim_report():
        return {
            "gate_id": "routine",
            "outcome": "deferred",
            "gate_exit_code": 0,
            "terminalized_pass": False,
            "policy_digest": "1" * 64,
            "decision_digest": "2" * 64,
            "receipt_binding_digest": None,
            "evidence_authority": GATE.EVIDENCE_AUTHORITY,
            "controlled_completion": False,
            "enforcement_eligible": False,
        }

    def test_work_cutoffs_preserve_execution_cleanup_and_terminal_windows(self):
        self.assertEqual(
            (96.0, 98.0, 99.0, 99.75),
            GATE.gate_work_cutoffs(100.0, 60.0),
        )
        self.assertEqual(
            (13.0, 14.0, 14.5, 14.75),
            GATE.gate_work_cutoffs(15.0, 5.0),
        )

    def test_bounded_helper_closes_the_terminal_control_descriptor(self):
        first, second = socket.socketpair()
        old_fd = os.environ.get(GATE._CONTROL_FD_ENV)
        os.environ[GATE._CONTROL_FD_ENV] = str(first.fileno())

        def control_is_open():
            try:
                os.fstat(first.fileno())
            except OSError:
                return False
            return True

        try:
            completed, control_open = GATE._bounded_json_call(
                control_is_open, GATE.time.monotonic() + 1.0
            )
            self.assertTrue(completed)
            self.assertFalse(control_open)
        finally:
            if old_fd is None:
                os.environ.pop(GATE._CONTROL_FD_ENV, None)
            else:
                os.environ[GATE._CONTROL_FD_ENV] = old_fd
            first.close()
            second.close()

    def test_terminal_send_is_bounded_when_socket_has_backpressure(self):
        first, second = socket.socketpair()
        old_fd = os.environ.get(GATE._CONTROL_FD_ENV)
        os.environ[GATE._CONTROL_FD_ENV] = str(first.fileno())
        first.setblocking(False)
        try:
            while True:
                try:
                    first.send(b"x" * 65536)
                except BlockingIOError:
                    break
            started = GATE.time.monotonic()
            with self.assertRaisesRegex(GATE.GateError, "missed its deadline"):
                GATE._send_terminal_decision(
                    self._controller_claim_report(), started + 0.02
                )
            self.assertLess(GATE.time.monotonic() - started, 0.2)
        finally:
            if old_fd is None:
                os.environ.pop(GATE._CONTROL_FD_ENV, None)
            else:
                os.environ[GATE._CONTROL_FD_ENV] = old_fd
            first.close()
            second.close()

    def test_terminal_send_retries_interruption_and_rejects_exact_deadline(self):
        old_fd = os.environ.get(GATE._CONTROL_FD_ENV)
        os.environ[GATE._CONTROL_FD_ENV] = "123"
        writes = []

        def interrupted_then_complete(_descriptor, data):
            writes.append(len(data))
            if len(writes) == 1:
                raise InterruptedError()
            return len(data)

        try:
            GATE._send_terminal_decision(
                self._controller_claim_report(),
                1.0,
                clock=lambda: 0.5,
                select_fn=lambda *_arguments: ((), (123,), ()),
                write_fn=interrupted_then_complete,
                get_blocking=lambda _descriptor: True,
                set_blocking=lambda *_arguments: None,
            )
            self.assertEqual(2, len(writes))

            clock = iter((0.0, 0.5, 1.0))
            with self.assertRaisesRegex(GATE.GateError, "completed at its deadline"):
                GATE._send_terminal_decision(
                    self._controller_claim_report(),
                    1.0,
                    clock=lambda: next(clock),
                    select_fn=lambda *_arguments: ((), (123,), ()),
                    write_fn=lambda _descriptor, data: len(data),
                    get_blocking=lambda _descriptor: True,
                    set_blocking=lambda *_arguments: None,
                )
        finally:
            if old_fd is None:
                os.environ.pop(GATE._CONTROL_FD_ENV, None)
            else:
                os.environ[GATE._CONTROL_FD_ENV] = old_fd

    def test_claim_precedes_best_effort_filing_and_timeout_is_unknown(self):
        report = GATE._base_report("routine", 0.0)
        report.update(
            {
                "outcome": "deferred",
                "reason": "reversible remainder",
                "candidate": {"digest": "candidate"},
            }
        )
        events = []

        def filing_timeout(_call, _deadline):
            events.append("filing")
            return False, None

        with mock.patch.object(
            GATE.time, "monotonic", return_value=0.6
        ), mock.patch.object(
            GATE,
            "_send_terminal_decision",
            side_effect=lambda *_arguments: events.append("claim"),
        ), mock.patch.object(
            GATE, "_bounded_json_call", side_effect=filing_timeout
        ), mock.patch.object(
            GATE,
            "_safe_local_directory",
            return_value=GATE.REPO / "tmp/test-gate-reports",
        ), mock.patch.object(GATE, "_atomic_json"), mock.patch.object(
            GATE, "_render_summary", return_value=""
        ), mock.patch.object(GATE, "_write_summary"):
            self.assertEqual(
                0,
                GATE.emit_report(
                    report,
                    target=0.5,
                    maximum=1.0,
                    policy_digest="policy",
                    options=mock.Mock(at_transition=None, explicit=False),
                    terminal_decision_deadline=0.75,
                ),
            )
        self.assertEqual(["claim", "filing"], events)
        self.assertEqual(
            {"disposition": "timed-out", "mutated": None},
            report["budget_filing"],
        )
        self.assertEqual(0.6, report["decision"]["duration_seconds"])

    def test_early_handoff_error_keeps_the_derived_claim_deadline(self):
        handoff = {
            "policy_frame": {"policy_digest": "1" * 64},
            "started_monotonic": 10.0,
            "absolute_deadline_monotonic": 70.0,
        }
        with mock.patch.object(GATE, "_HANDOFF", handoff), mock.patch.object(
            GATE, "gate_interval_bounds", return_value=(10.0, 70.0)
        ), mock.patch.object(
            GATE,
            "validate_bootstrap_handoff",
            side_effect=GATE.GateError("injected early failure"),
        ), mock.patch.object(GATE, "emit_report", return_value=2) as emit:
            self.assertEqual(2, GATE.main(("routine", "--staged")))
        self.assertEqual(69.75, emit.call_args[1]["terminal_decision_deadline"])

        with mock.patch.object(GATE, "_HANDOFF", handoff), mock.patch.object(
            GATE,
            "gate_interval_bounds",
            side_effect=GATE.GateError("injected handoff failure"),
        ), mock.patch.object(GATE, "emit_report", return_value=2) as emit:
            self.assertEqual(2, GATE.main(("routine", "--staged")))
        self.assertEqual(69.75, emit.call_args[1]["terminal_decision_deadline"])

    def test_unknown_final_stability_blocks_without_receipt_identity(self):
        report = GATE._base_report("routine", 0.0)
        component = GATE.ComponentResult(
            "repository-tests/selected", "incomplete", "executed", 1.0, ()
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
        report["components"] = [component.as_dict()]
        observed = []
        with mock.patch.object(
            GATE.time, "monotonic", return_value=0.5
        ), mock.patch.object(
            GATE,
            "_send_terminal_decision",
            side_effect=lambda value, _deadline=None: observed.append(dict(value)),
        ), mock.patch.object(
            GATE,
            "_safe_local_directory",
            return_value=GATE.REPO / "tmp/test-gate-reports",
        ), mock.patch.object(GATE, "_atomic_json"), mock.patch.object(
            GATE, "_render_summary", return_value=""
        ), mock.patch.object(GATE, "_write_summary"):
            self.assertEqual(1, GATE.emit_report(report, receipt_binding_value=None))
        self.assertEqual("blocked-incomplete", observed[0]["outcome"])
        self.assertIsNone(observed[0]["receipt_binding_digest"])

    def test_authoritative_discovery_never_imports_candidate_parser_with_outer_fd(self):
        first, second = socket.socketpair()
        old_outer = os.environ.get(GATE._OUTER_CONTROL_FD_ENV)
        try:
            os.environ[GATE._OUTER_CONTROL_FD_ENV] = str(first.fileno())
            with tempfile.TemporaryDirectory() as scratch:
                root = Path(scratch)
                trusted = root / "trusted"
                candidate = root / "candidate"
                (trusted / "automation").mkdir(parents=True)
                (candidate / "automation").mkdir(parents=True)
                (trusted / "automation/test_gate_config.py").write_text(
                    "def load_policy_union(base, candidate):\n"
                    "    return object()\n"
                )
                marker = root / "candidate-imported"
                (candidate / "automation/test_gate_config.py").write_text(
                    "import os\n"
                    "os.write(int(os.environ['AGENTFOLD_GATE_CONTROL_FD']), b'forged')\n"
                    "open({!r}, 'w').write('imported')\n".format(str(marker))
                )
                base = trusted / "agentfold.toml"
                config = candidate / "agentfold.toml"
                base.write_text("base")
                config.write_text("candidate")
                _module, policy = GATE._load_exact_policy(trusted, config, base)
                self.assertIsNotNone(policy)
                self.assertFalse(marker.exists())
                second.setblocking(False)
                with self.assertRaises(BlockingIOError):
                    second.recv(1)
        finally:
            if old_outer is None:
                os.environ.pop(GATE._OUTER_CONTROL_FD_ENV, None)
            else:
                os.environ[GATE._OUTER_CONTROL_FD_ENV] = old_outer
            first.close()
            second.close()

    def test_authoritative_base_parser_unions_and_rejects_candidate_config(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            trusted = root / "trusted"
            candidate = root / "candidate.toml"
            for relative in GATE._POLICY_CLOSURE_PATHS:
                destination = trusted / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(GATE.REPO / relative, destination)
            base = trusted / "agentfold.toml"
            text = (GATE.REPO / "agentfold.toml").read_text(encoding="utf-8")
            base.write_text(text, encoding="utf-8")
            candidate.write_text(
                text.replace("target_seconds = 60", "target_seconds = 30", 1)
                .replace("maximum_seconds = 60", "maximum_seconds = 30", 1),
                encoding="utf-8",
            )
            _module, policy = GATE._load_exact_policy(trusted, candidate, base)
            self.assertEqual(30.0, policy.routine.target_seconds)
            self.assertEqual(30.0, policy.routine.maximum_seconds)
            candidate.write_text("[testing.routine\n", encoding="utf-8")
            with self.assertRaisesRegex(Exception, "not valid TOML"):
                GATE._load_exact_policy(trusted, candidate, base)

    def test_discovery_blocks_parser_closure_mutation(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            trusted = root / "trusted"
            candidate_root = root / "candidate"
            for source_root in (trusted, candidate_root):
                for relative in GATE._POLICY_CLOSURE_PATHS:
                    destination = source_root / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(GATE.REPO / relative, destination)
            base = trusted / "agentfold.toml"
            candidate = candidate_root / "agentfold.toml"
            shutil.copy2(GATE.REPO / "agentfold.toml", base)
            shutil.copy2(GATE.REPO / "agentfold.toml", candidate)
            closures = {
                "trusted": GATE._policy_closure_records(trusted),
                "candidate": GATE._policy_closure_records(candidate_root),
            }
            index = root / "candidate.index"
            index.write_bytes(b"index")
            materialized = (
                {
                    "kind": "staged-index",
                    "base_revision": "1" * 40,
                    "candidate_revision": "",
                },
                index,
                trusted,
                candidate_root,
                base,
                candidate,
                closures,
                {"file_sha256": "2" * 64, "semantic_sha256": "3" * 64},
            )
            policy = mock.Mock()
            policy.routine.target_seconds = 60.0
            policy.routine.maximum_seconds = 60.0
            policy.final.target_seconds = 300.0
            policy.final.maximum_seconds = 900.0
            module = mock.Mock()
            module.canonical_policy_digest.return_value = "4" * 64

            def mutate_parser(*_arguments):
                parser = trusted / "automation/test_gate_config.py"
                parser.chmod(stat.S_IMODE(parser.stat().st_mode) | stat.S_IWUSR)
                with parser.open("ab") as stream:
                    stream.write(b"\n# drift\n")
                return module, policy

            with mock.patch.object(
                GATE, "_materialize_policy_inputs", return_value=materialized
            ), mock.patch.object(GATE, "_load_exact_policy", side_effect=mutate_parser):
                with self.assertRaisesRegex(RuntimeError, "closure changed"):
                    GATE._discover_policy_frame(GATE.REPO, ("routine", "--staged"), root)

    def test_freeze_reuses_authoritative_index_without_recapture(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            repo = root / "repo"
            repo.mkdir()
            for relative in ("agentfold.toml",) + GATE.CONTROLLER_CLOSURE_PATHS:
                source = GATE.REPO / relative
                destination = repo / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                destination.chmod(
                    stat.S_IMODE(destination.stat().st_mode) | stat.S_IWUSR
                )
            subprocess.run(("git", "init", "-q"), cwd=str(repo), check=True)
            subprocess.run(
                ("git", "config", "user.email", "gate-test@example.invalid"),
                cwd=str(repo),
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.name", "Gate Test"),
                cwd=str(repo),
                check=True,
            )
            subprocess.run(("git", "add", "."), cwd=str(repo), check=True)
            subprocess.run(
                ("git", "commit", "-q", "-m", "fixture"),
                cwd=str(repo),
                check=True,
            )
            index = root / "candidate.index"
            GATE._copy_index(GATE._selected_index(repo), index)
            identity = {
                "file_sha256": GATE._file_sha256(index),
                "semantic_sha256": GATE._sha256_bytes(
                    GATE._semantic_index(repo, index)
                ),
            }
            with mock.patch.object(GATE, "_copy_index") as recapture:
                handoff = GATE._freeze(
                    repo,
                    ("routine", "--staged"),
                    root,
                    10.0,
                    GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE,
                    {"authoritative_index": identity},
                    70.0,
                    index,
                )
            recapture.assert_not_called()
            self.assertEqual(str(index), handoff["frozen_index"])
            self.assertEqual(identity["file_sha256"], handoff["frozen_index_sha256"])
            self.assertEqual(
                identity["semantic_sha256"], handoff["index_semantic_sha256"]
            )
            GATE._unseal_snapshot(Path(handoff["execution_root"]))

    def test_policy_frame_allows_exact_five_second_maximum(self):
        self.assertEqual(5.0, GATE._validate_policy_frame(signed_policy_frame(), "routine"))

    def test_policy_frame_rejects_smaller_nonfinite_and_boolean_maximum(self):
        for maximum in (4.999, float("inf"), True):
            with self.subTest(maximum=maximum):
                frame = signed_policy_frame(maximum=5.0, target=1.0)
                frame["maximum_seconds"] = maximum
                if maximum != float("inf"):
                    unsigned = dict(frame)
                    unsigned.pop("frame_digest")
                    frame["frame_digest"] = GATE._sha256_bytes(
                        GATE._canonical_json(unsigned)
                    )
                with self.assertRaisesRegex(RuntimeError, "budget|at least 5|canonical JSON"):
                    GATE._validate_policy_frame(frame, "routine")

    def test_policy_frame_rejects_malformed_shape_and_wrong_digest(self):
        frame = signed_policy_frame()
        frame["extra"] = "unsafe"
        with self.assertRaisesRegex(RuntimeError, "shape"):
            GATE._validate_policy_frame(frame, "routine")
        frame = signed_policy_frame()
        frame["policy_digest"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "frame digest"):
            GATE._validate_policy_frame(frame, "routine")

    def test_control_frame_rejects_oversized_length_before_payload(self):
        first, second = socket.socketpair()
        try:
            first.sendall(struct.pack("!I", GATE.CONTROL_FRAME_MAX_BYTES + 1))
            with self.assertRaisesRegex(RuntimeError, "length"):
                GATE._receive_control_frame(second, GATE._clock_value() + 1.0)
        finally:
            first.close()
            second.close()

    def test_control_frame_before_deadline_is_accepted(self):
        first, second = socket.socketpair()
        try:
            GATE._send_control_frame(first, {"schema": "probe"})
            value = GATE._receive_control_frame(second, GATE._clock_value() + 1.0)
            self.assertEqual({"schema": "probe"}, value)
        finally:
            first.close()
            second.close()

    def test_control_frame_at_and_after_deadline_are_rejected(self):
        first, second = socket.socketpair()
        try:
            first.sendall(struct.pack("!I", 2) + b"{}")
            with mock.patch.object(GATE, "_clock_value", return_value=10.0):
                with self.assertRaisesRegex(TimeoutError, "deadline"):
                    GATE._receive_control_frame(second, 10.0)
                with self.assertRaisesRegex(TimeoutError, "deadline"):
                    GATE._receive_control_frame(second, 9.0)
        finally:
            first.close()
            second.close()

    def test_zero_exit_without_terminal_frame_is_not_success(self):
        class ExitedWorker:
            pid = 99999999

            @staticmethod
            def wait(timeout=None):
                del timeout
                return 0

        first, second = socket.socketpair()
        second.close()
        try:
            with self.assertRaisesRegex(EOFError, "closed"):
                GATE._receive_control_frame(first, GATE._clock_value() + 1.0)
            self.assertEqual(0, ExitedWorker.wait())
        finally:
            first.close()

    def test_pre_policy_hang_blocks_and_triggers_owned_cleanup(self):
        process = mock.Mock(pid=12345)
        process.poll.return_value = None
        process.wait.side_effect = [TimeoutError(), 1]
        with mock.patch.object(
            GATE, "_bootstrap_monotonic_start", return_value=(GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE, 10.0)
        ), mock.patch.object(GATE.subprocess, "Popen", return_value=process), mock.patch.object(
            GATE, "_receive_control_frame", side_effect=TimeoutError("policy discovery timed out")
        ), mock.patch.object(GATE, "_kill_worker_group") as cleanup, mock.patch.object(
            GATE, "_static_result", return_value=1
        ):
            self.assertEqual(1, GATE._dispatch(("routine", "--staged")))
        cleanup.assert_called_once_with(process, mock.ANY)

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == PARSER_COMPAT_ENDPOINT,
        "direct stdout static reporting belongs to the parser-compat endpoint",
    )
    def test_parser_compat_pre_policy_timeout_writes_direct_stdout(self):
        process = mock.Mock(pid=12345)
        cleanup = {
            "worker_started": True,
            "worker_result": "exited",
            "process_group_cleanup": {
                "attempted": True,
                "result": "signal-sent",
            },
            "ownership_token_cleanup": {
                "attempted": True,
                "result": "no-match",
                "discovery_completeness": "best-effort-portable",
            },
        }
        output = []
        with mock.patch.object(
            GATE,
            "_bootstrap_monotonic_start",
            side_effect=(
                (GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE, 10.0),
                (GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE, 15.25),
            ),
        ), mock.patch.object(GATE.subprocess, "Popen", return_value=process), mock.patch.object(
            GATE,
            "_receive_control_frame",
            side_effect=TimeoutError("test-gate control frame missed its deadline"),
        ), mock.patch.object(
            GATE, "_kill_worker_group", return_value=cleanup
        ) as cleanup_call, mock.patch.object(
            GATE.sys.stdout, "write", side_effect=output.append
        ), mock.patch.object(GATE.sys.stdout, "flush"):
            self.assertEqual(1, GATE._dispatch(("routine", "--staged")))
        report = json.loads(output[0])
        self.assertEqual(5.25, report["duration_seconds"])
        self.assertEqual(5.25, report["decision"]["duration_seconds"])
        self.assertTrue(report["process_containment"]["worker_started"])
        cleanup_call.assert_called_once_with(process, mock.ANY)

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "bounded static reporting belongs to the review-repair endpoint",
    )
    def test_pre_policy_frame_timeout_reports_real_elapsed_and_cleanup(self):
        process = mock.Mock(pid=12345)
        cleanup = {
            "worker_started": True,
            "worker_result": "exited",
            "process_group_cleanup": {
                "attempted": True,
                "result": "signal-sent",
            },
            "ownership_token_cleanup": {
                "attempted": True,
                "result": "no-match",
                "discovery_completeness": "best-effort-portable",
            },
        }
        output = []

        def deliver(payload, *_arguments, **_kwargs):
            output.append(payload.decode("utf-8") if isinstance(payload, bytes) else payload)
            return {"disposition": "written", "written": True}

        with mock.patch.object(
            GATE,
            "_bootstrap_monotonic_start",
            side_effect=(
                (GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE, 10.0),
                (GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE, 15.25),
            ),
        ), mock.patch.object(GATE.subprocess, "Popen", return_value=process), mock.patch.object(
            GATE,
            "_receive_control_frame",
            side_effect=TimeoutError("test-gate control frame missed its deadline"),
        ), mock.patch.object(
            GATE, "_kill_worker_group", return_value=cleanup
        ) as cleanup_call, mock.patch.object(
            GATE, "_deliver_static_output", side_effect=deliver
        ):
            self.assertEqual(1, GATE._dispatch(("routine", "--staged")))
        report = json.loads(output[0])
        self.assertEqual(5.25, report["duration_seconds"])
        self.assertEqual(5.25, report["decision"]["duration_seconds"])
        self.assertTrue(report["process_containment"]["worker_started"])
        self.assertEqual(
            {"attempted": True, "result": "signal-sent"},
            report["process_containment"]["process_group_cleanup"],
        )
        self.assertEqual(
            "best-effort-portable",
            report["process_containment"]["ownership_token_cleanup"][
                "discovery_completeness"
            ],
        )
        cleanup_call.assert_called_once_with(process, mock.ANY)

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == PARSER_COMPAT_ENDPOINT,
        "pre-static cleanup belongs to the parser-compat endpoint",
    )
    def test_parser_compat_post_policy_hang_triggers_cleanup(self):
        process = mock.Mock(pid=12345)
        frame = signed_policy_frame(maximum=5.0, target=5.0)
        with mock.patch.object(
            GATE, "_bootstrap_monotonic_start", return_value=(GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE, 10.0)
        ), mock.patch.object(GATE, "_clock_value", return_value=10.1), mock.patch.object(
            GATE.subprocess, "Popen", return_value=process
        ), mock.patch.object(
            GATE,
            "_receive_control_frame",
            side_effect=(frame, TimeoutError("terminal decision timed out")),
        ) as receive, mock.patch.object(GATE, "_send_control_frame"), mock.patch.object(
            GATE, "_kill_worker_group"
        ) as cleanup, mock.patch.object(GATE, "_static_result", return_value=1):
            self.assertEqual(1, GATE._dispatch(("routine", "--staged")))
        self.assertEqual(15.0, receive.call_args_list[1][0][1])
        cleanup.assert_called_once_with(process, mock.ANY)

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "post-claim cleanup belongs to the review-repair endpoint",
    )
    def test_post_policy_hang_uses_absolute_deadline_and_triggers_cleanup(self):
        process = mock.Mock(pid=12345)
        frame = signed_policy_frame(maximum=5.0, target=5.0)
        with mock.patch.object(
            GATE, "_bootstrap_monotonic_start", return_value=(GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE, 10.0)
        ), mock.patch.object(GATE, "_clock_value", return_value=10.1), mock.patch.object(
            GATE.subprocess, "Popen", return_value=process
        ), mock.patch.object(
            GATE,
            "_receive_control_frame",
            side_effect=(frame, TimeoutError("terminal decision timed out")),
        ) as receive, mock.patch.object(GATE, "_send_control_frame"), mock.patch.object(
            GATE, "_kill_worker_group"
        ) as cleanup, mock.patch.object(
            GATE,
            "_static_result",
            side_effect=lambda *args, **kwargs: (
                kwargs["post_claim_cleanup"](),
                1,
            )[1],
        ) as static:
            self.assertEqual(1, GATE._dispatch(("routine", "--staged")))
        self.assertEqual(15.0, receive.call_args_list[1][0][1])
        cleanup.assert_called_once_with(process, mock.ANY)
        self.assertEqual(frame, static.call_args[1]["policy_frame"])
        self.assertTrue(static.call_args[1]["deadline_reached"])
        self.assertNotIn("duration", static.call_args[1])

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "post-policy static facts belong to the review-repair endpoint",
    )
    def test_post_policy_timeout_claims_before_cleanup_and_files_known_breach(self):
        frame = signed_policy_frame(maximum=60.0, target=60.0)
        events = []
        output = []

        def cleanup():
            events.append("cleanup")
            return GATE._not_run_cleanup(True, "worker-killed")

        def filing(*_arguments):
            events.append("filing")
            return {"disposition": "created", "mutated": True}

        def deliver(payload, *_arguments, **_kwargs):
            value = payload.decode("utf-8") if isinstance(payload, bytes) else payload
            output.append(value)
            if len(output) == 1:
                events.append("claim")
            return {"disposition": "written", "written": True}

        with mock.patch.object(
            GATE, "_deliver_static_output", side_effect=deliver
        ), mock.patch.object(
            GATE, "_static_elapsed", return_value=61.75
        ) as elapsed, mock.patch.object(
            GATE, "_file_static_target_breach", side_effect=filing
        ):
            self.assertEqual(
                1,
                GATE._static_result(
                    "routine",
                    "blocked-incomplete",
                    "terminal decision timed out",
                    ("gate-interval",),
                    GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE,
                    10.0,
                    True,
                    policy_frame=frame,
                    deadline_reached=True,
                    post_claim_cleanup=cleanup,
                    arguments=("routine", "--staged"),
                ),
            )

        report = json.loads(output[0])
        self.assertEqual(["claim", "cleanup", "filing"], events)
        elapsed.assert_called_once_with(GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE, 10.0)
        self.assertEqual(61.75, report["duration_seconds"])
        self.assertEqual(60.0, report["target_seconds"])
        self.assertEqual(60.0, report["maximum_seconds"])
        self.assertTrue(report["target_exceeded"])
        self.assertTrue(report["maximum_exceeded"])
        self.assertEqual(frame["policy_digest"], report["policy_digest"])
        self.assertEqual(
            frame["authoritative_index"]["semantic_sha256"],
            report["decision"]["candidate_digest"],
        )

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "bounded static claims belong to the review-repair endpoint",
    )
    def test_failed_static_claim_cleans_worker_and_skips_filing(self):
        frame = signed_policy_frame(maximum=60.0, target=60.0)
        events = []

        def cleanup():
            events.append("cleanup")
            return GATE._not_run_cleanup(True, "worker-killed")

        with mock.patch.object(
            GATE,
            "_deliver_static_output",
            return_value={"disposition": "timed-out", "written": False},
        ) as deliver, mock.patch.object(
            GATE, "_static_elapsed", return_value=61.0
        ), mock.patch.object(
            GATE, "_file_static_target_breach"
        ) as filing:
            self.assertEqual(
                2,
                GATE._static_result(
                    "routine",
                    "blocked-incomplete",
                    "terminal decision timed out",
                    ("gate-interval",),
                    GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE,
                    10.0,
                    True,
                    policy_frame=frame,
                    deadline_reached=True,
                    post_claim_cleanup=cleanup,
                    arguments=("routine", "--staged"),
                ),
            )
        self.assertEqual(["cleanup"], events)
        self.assertEqual(1, deliver.call_count)
        filing.assert_not_called()

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "bounded static telemetry belongs to the review-repair endpoint",
    )
    def test_static_telemetry_is_bounded_after_successful_claim(self):
        frame = signed_policy_frame(maximum=60.0, target=60.0)
        events = []

        def cleanup():
            events.append("cleanup")
            return GATE._not_run_cleanup(True, "worker-killed")

        def filing(*_arguments):
            events.append("filing")
            return {"disposition": "created", "mutated": True}

        with mock.patch.object(
            GATE,
            "_deliver_static_output",
            side_effect=(
                {"disposition": "written", "written": True},
                {"disposition": "timed-out", "written": False},
            ),
        ), mock.patch.object(
            GATE, "_static_elapsed", return_value=61.0
        ), mock.patch.object(
            GATE, "_file_static_target_breach", side_effect=filing
        ):
            self.assertEqual(
                2,
                GATE._static_result(
                    "routine",
                    "blocked-incomplete",
                    "terminal decision timed out",
                    ("gate-interval",),
                    GATE._BOOTSTRAP_CLOCK_GETTIME_SOURCE,
                    10.0,
                    True,
                    policy_frame=frame,
                    deadline_reached=True,
                    post_claim_cleanup=cleanup,
                    arguments=("routine", "--staged"),
                ),
            )
        self.assertEqual(["cleanup", "filing"], events)

    @unittest.skipUnless(os.name == "posix", "static writer requires POSIX fork")
    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "bounded static writer belongs to the review-repair endpoint",
    )
    def test_static_output_writer_times_out_under_backpressure(self):
        reader, writer = os.pipe()
        os.set_blocking(writer, False)
        try:
            while True:
                try:
                    os.write(writer, b"x" * 65536)
                except BlockingIOError:
                    break
            os.set_blocking(writer, True)
            started = time.monotonic()
            delivery = GATE._deliver_static_output(b"claim\n", writer, timeout=0.02)
            self.assertEqual("timed-out", delivery["disposition"])
            self.assertFalse(delivery["written"])
            self.assertLess(time.monotonic() - started, 0.3)
        finally:
            os.close(writer)
            os.close(reader)

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "bounded static writer belongs to the review-repair endpoint",
    )
    def test_static_output_timeout_never_blocks_reaping_unresponsive_child(self):
        with mock.patch.object(GATE.os, "fork", return_value=12345), mock.patch.object(
            GATE.os, "waitpid", return_value=(0, 0)
        ) as waitpid, mock.patch.object(GATE.os, "kill") as kill, mock.patch.object(
            GATE.time, "monotonic", return_value=1.0
        ), mock.patch.object(GATE.time, "sleep") as sleep:
            delivery = GATE._deliver_static_output(b"claim\n", 9, timeout=0.0)

        self.assertEqual({"disposition": "timed-out", "written": False}, delivery)
        kill.assert_called_once_with(12345, GATE.signal.SIGKILL)
        self.assertEqual(
            [mock.call(12345, GATE.os.WNOHANG), mock.call(12345, GATE.os.WNOHANG)],
            waitpid.call_args_list,
        )
        sleep.assert_not_called()

    @unittest.skipUnless(os.name == "posix", "static writer requires POSIX fork")
    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "bounded static writer belongs to the review-repair endpoint",
    )
    def test_static_output_writer_delivers_exact_bytes(self):
        reader, writer = os.pipe()
        try:
            delivery = GATE._deliver_static_output(b"claim\n", writer, timeout=0.1)
            self.assertEqual({"disposition": "written", "written": True}, delivery)
            os.close(writer)
            writer = None
            self.assertEqual(b"claim\n", os.read(reader, 64))
        finally:
            if writer is not None:
                os.close(writer)
            os.close(reader)

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "static timeout filing belongs to the review-repair endpoint",
    )
    def test_static_filing_timeout_reports_unknown_mutation(self):
        frame = signed_policy_frame(maximum=60.0, target=60.0)
        report = {
            "gate_id": "routine",
            "duration_seconds": 60.0,
            "target_seconds": 60.0,
            "decision_digest": "a" * 64,
        }
        with mock.patch.object(
            GATE.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(("python3",), 1.0),
        ):
            filing = GATE._file_static_target_breach(
                report, frame, ("routine", "--staged")
            )
        self.assertEqual({"disposition": "timed-out", "mutated": None}, filing)

    def test_cleanup_targets_reparented_exact_token_processes(self):
        process = mock.Mock(pid=111)
        process.wait.return_value = 0
        with mock.patch.object(GATE.os, "killpg"), mock.patch.object(
            GATE, "_owned_worker_pids", side_effect=({222}, set())
        ), mock.patch.object(GATE.os, "kill") as kill:
            GATE._kill_worker_group(process, "a" * 64)
        kill.assert_any_call(222, GATE.signal.SIGKILL)

    def test_worker_exit_matrix_rejects_mismatch_and_allows_publication_error(self):
        for gate_exit in (0, 1, 2):
            claim = {"gate_exit_code": gate_exit}
            self.assertEqual(gate_exit, GATE._worker_exit_for_claim(claim, gate_exit))
        self.assertEqual(2, GATE._worker_exit_for_claim({"gate_exit_code": 0}, 2))
        self.assertEqual(2, GATE._worker_exit_for_claim({"gate_exit_code": 1}, 2))
        for gate_exit, worker_exit in ((2, 0), (2, 1), (1, 0), (0, 1), (0, -9)):
            with self.subTest(gate_exit=gate_exit, worker_exit=worker_exit):
                with self.assertRaisesRegex(RuntimeError, "contradicts"):
                    GATE._worker_exit_for_claim(
                        {"gate_exit_code": gate_exit}, worker_exit
                    )

    def test_component_environment_gets_neither_control_channel(self):
        environment = GATE.safe_process_environment(
            {
                "PATH": os.environ.get("PATH", "/bin"),
                GATE._OUTER_CONTROL_FD_ENV: "10",
                GATE._CONTROL_FD_ENV: "11",
            }
        )
        self.assertNotIn(GATE._OUTER_CONTROL_FD_ENV, environment)
        self.assertNotIn(GATE._CONTROL_FD_ENV, environment)

    def test_terminal_frame_outcome_and_exit_must_agree(self):
        frame = {
            "schema": GATE.TERMINAL_FRAME_SCHEMA,
            "gate_id": "routine",
            "outcome": "pass",
            "gate_exit_code": 1,
            "terminalized_pass": True,
            "policy_digest": "1" * 64,
            "policy_frame_digest": "2" * 64,
            "decision_digest": "3" * 64,
            "claim_digest": "4" * 64,
            "evidence_authority": "cooperative-same-interpreter",
            "controlled_completion": False,
            "enforcement_eligible": False,
        }
        with self.assertRaisesRegex(RuntimeError, "contradicts"):
            GATE._validate_terminal_frame(frame)

    def test_terminal_frame_is_sent_before_slow_publication(self):
        first, second = socket.socketpair()
        old_fd = os.environ.get(GATE._CONTROL_FD_ENV)
        os.environ[GATE._CONTROL_FD_ENV] = str(first.fileno())
        report = GATE._base_report("routine", 0.0)
        report.update({"outcome": "deferred", "reason": "bounded"})
        observed = []

        def publication(*_arguments, **_keywords):
            observed.append(
                GATE._receive_control_frame(second, GATE._clock_value() + 1.0)
            )

        try:
            with mock.patch.object(GATE.time, "monotonic", return_value=0.1), mock.patch.object(
                GATE, "_atomic_json", side_effect=publication
            ), mock.patch.object(GATE, "_write_summary"):
                self.assertEqual(0, GATE.emit_report(report, maximum=5.0))
            self.assertEqual("deferred", observed[0]["outcome"])
        finally:
            if old_fd is None:
                os.environ.pop(GATE._CONTROL_FD_ENV, None)
            else:
                os.environ[GATE._CONTROL_FD_ENV] = old_fd
            first.close()
            second.close()

    def test_report_contains_verifiable_immutable_decision(self):
        report = GATE._base_report("routine", 0.0)
        report.update({"outcome": "deferred", "reason": "bounded"})
        with mock.patch.object(GATE.time, "monotonic", return_value=0.1), mock.patch.object(
            GATE, "_atomic_json"
        ), mock.patch.object(GATE, "_write_summary"):
            self.assertEqual(0, GATE.emit_report(report, maximum=5.0))
        self.assertEqual(
            report["decision_digest"],
            GATE.test_manifest.canonical_digest(report["decision"]),
        )
        self.assertEqual("routine", report["decision"]["gate_id"])
        self.assertEqual("deferred", report["decision"]["outcome"])

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == PARSER_COMPAT_ENDPOINT,
        "direct stdout static reporting belongs to the parser-compat endpoint",
    )
    def test_parser_compat_static_reports_write_direct_stdout(self):
        for arguments, expected_gate in (
            (("routine", "--staged"), "routine"),
            (("final", "--explicit"), "final"),
            (("--malformed",), "unknown"),
        ):
            output = []
            with mock.patch.object(
                GATE.sys.stdout, "write", side_effect=output.append
            ), mock.patch.object(GATE.sys.stdout, "flush"):
                self.assertEqual(
                    2,
                    GATE._static_result(
                        GATE._raw_gate(arguments), "error", "protocol failure"
                    ),
                )
            report = json.loads(output[0])
            self.assertEqual(GATE.REPORT_SCHEMA, report["schema"])
            self.assertEqual(expected_gate, report["gate_id"])
            self.assertIsNone(report["duration_seconds"])
            self.assertIsNone(report["process_containment"]["worker_started"])

    @unittest.skipUnless(
        PRODUCT_ENDPOINT == REVIEW_REPAIR_ENDPOINT,
        "bounded static reporting belongs to the review-repair endpoint",
    )
    def test_static_reports_are_lane_correct_full_v4_objects(self):
        for arguments, expected_gate in (
            (("routine", "--staged"), "routine"),
            (("final", "--explicit"), "final"),
            (("--malformed",), "unknown"),
        ):
            output = []

            def deliver(payload, *_arguments, **_kwargs):
                output.append(payload.decode("utf-8") if isinstance(payload, bytes) else payload)
                return {"disposition": "written", "written": True}

            with mock.patch.object(GATE, "_deliver_static_output", side_effect=deliver):
                self.assertEqual(
                    2,
                    GATE._static_result(
                        GATE._raw_gate(arguments), "error", "protocol failure"
                    ),
                )
            report = json.loads(output[0])
            self.assertEqual(GATE.REPORT_SCHEMA, report["schema"])
            self.assertEqual(expected_gate, report["gate_id"])
            self.assertIsNone(report["duration_seconds"])
            self.assertIsNone(report["process_containment"]["worker_started"])
            self.assertIsNone(
                report["process_containment"]["process_group_cleanup"]["attempted"]
            )
            self.assertEqual(
                "unavailable",
                report["process_containment"]["ownership_token_cleanup"][
                    "discovery_completeness"
                ],
            )
            for field in (
                "decision",
                "decision_digest",
                "components",
                "selected",
                "deferred",
                "incomplete",
                "publication_status",
                "command_outcome",
            ):
                self.assertIn(field, report)

    def test_candidate_parser_policy_mismatch_blocks_controller_validation(self):
        policy = GATE.test_gate_config.load_policy(GATE.REPO / "agentfold.toml")
        frame = signed_policy_frame(maximum=60.0, target=60.0)
        frame["budgets"] = {
            "routine": {"target_seconds": 60.0, "maximum_seconds": 60.0},
            "final": {"target_seconds": 300.0, "maximum_seconds": 900.0},
        }
        unsigned = dict(frame)
        unsigned.pop("frame_digest")
        frame["frame_digest"] = GATE._sha256_bytes(GATE._canonical_json(unsigned))
        old_handoff = GATE._HANDOFF
        try:
            GATE._HANDOFF = {"policy_frame": frame}
            with tempfile.TemporaryDirectory() as scratch:
                candidate_root = Path(scratch)
                shutil.copy2(GATE.REPO / "agentfold.toml", candidate_root / "agentfold.toml")
                base_result = mock.Mock(
                    returncode=0,
                    stdout=(GATE.REPO / "agentfold.toml").read_bytes(),
                )
                with mock.patch.object(GATE.subprocess, "run", return_value=base_result):
                    with self.assertRaisesRegex(GATE.GateError, "policy_digest"):
                        GATE.validate_policy_frame(
                            policy,
                            "0" * 64,
                            candidate_root,
                            "1" * 40,
                            "routine",
                        )
        finally:
            GATE._HANDOFF = old_handoff

    def test_base_parser_rejects_unparseable_candidate_config(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            base = root / "base.toml"
            candidate = root / "candidate.toml"
            shutil.copy2(GATE.REPO / "agentfold.toml", base)
            candidate.write_text("[testing.routine\n")
            with self.assertRaises(GATE.test_gate_config.ConfigError):
                GATE.test_gate_config.load_policy_union(base, candidate)

    def test_v5_receipt_is_rejected_by_v6_reader(self):
        self.assertEqual("agentfold.test-component-receipt/v6", GATE.RECEIPT_SCHEMA)
        self.assertNotEqual("agentfold.test-component-receipt/v5", GATE.RECEIPT_SCHEMA)

    def test_receipt_protocol_identity_excludes_absolute_clock_values(self):
        source = GATE._HANDOFF
        frame = signed_policy_frame(maximum=60.0, target=60.0)
        try:
            bindings = []
            for started in (10.0, 5000.0):
                GATE._HANDOFF = {
                    "policy_frame": frame,
                    "started_monotonic": started,
                    "absolute_deadline_monotonic": started + 60.0,
                }
                candidate = mock.Mock(digest="candidate", closure_digest="closure")
                with mock.patch.object(
                    GATE,
                    "controller_closure",
                    return_value={"digest": "controller", "records": []},
                ), mock.patch.object(
                    GATE, "runner_revision", return_value="runner"
                ), mock.patch.object(
                    GATE,
                    "environment_identity",
                    return_value={"component_environment_digest": "environment"},
                ):
                    bindings.append(
                        GATE.receipt_binding(
                            candidate,
                            {"digest": "view"},
                            ("test.py",),
                            frame["policy_digest"],
                            "repository-tests/full",
                            composite_identity={"schema": "plan"},
                        )
                    )
            self.assertEqual(bindings[0], bindings[1])
        finally:
            GATE._HANDOFF = source

    def test_canonical_config_parser_rejects_below_five_and_accepts_five(self):
        text = (GATE.REPO / "agentfold.toml").read_text(encoding="utf-8")
        exact = text.replace("maximum_seconds = 60", "maximum_seconds = 5", 1).replace(
            "target_seconds = 60", "target_seconds = 5", 1
        )
        self.assertEqual(5.0, GATE.test_gate_config.parse_policy(exact).routine.maximum_seconds)
        too_small = exact.replace("maximum_seconds = 5", "maximum_seconds = 4.999", 1)
        with self.assertRaisesRegex(GATE.test_gate_config.ConfigError, "at least 5"):
            GATE.test_gate_config.parse_policy(too_small)

    def test_canonical_policy_union_uses_smaller_base_or_candidate_budget(self):
        text = (GATE.REPO / "agentfold.toml").read_text(encoding="utf-8")
        base = GATE.test_gate_config.parse_policy(
            text.replace("target_seconds = 60", "target_seconds = 30", 1).replace(
                "maximum_seconds = 60", "maximum_seconds = 30", 1
            )
        )
        candidate = GATE.test_gate_config.parse_policy(
            text.replace("target_seconds = 60", "target_seconds = 45", 1).replace(
                "maximum_seconds = 60", "maximum_seconds = 45", 1
            )
        )
        first = GATE.test_gate_config.union_policies(base, candidate)
        second = GATE.test_gate_config.union_policies(candidate, base)
        self.assertEqual((30.0, 30.0), (
            first.routine.target_seconds,
            first.routine.maximum_seconds,
        ))
        self.assertEqual(first.routine, second.routine)


if __name__ == "__main__":
    unittest.main()
