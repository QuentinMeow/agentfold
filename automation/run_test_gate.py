#!/usr/bin/env python3
"""Freeze one gate candidate and dispatch its staged controller in isolation.

The executable path intentionally contains only standard-library code.  Reserved
automatic-boundary syntax is rejected from raw argv before this file reads Git,
configuration, candidate bytes, local reports, receipts, or budget state.
"""

import contextlib
import hashlib
import json
import math
import os
import secrets
import select
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path


REPORT_SCHEMA = "agentfold.test-gate-report/v4"
HANDOFF_SCHEMA = "agentfold.test-gate-bootstrap/v2"
POLICY_FRAME_SCHEMA = "agentfold.test-gate-policy-frame/v1"
DEADLINE_FRAME_SCHEMA = "agentfold.test-gate-deadline-frame/v1"
TERMINAL_FRAME_SCHEMA = "agentfold.test-gate-broker-decision/v1"
CONTROLLER_CLAIM_SCHEMA = "agentfold.test-gate-controller-claim/v1"
DISCOVERY_CEILING_SECONDS = 5.0
POST_CLAIM_FILING_TIMEOUT_SECONDS = 1.0
STATIC_OUTPUT_TIMEOUT_SECONDS = 0.25
CONTROL_FRAME_MAX_BYTES = 65536
_UNSET = object()
_HANDOFF_ENV = "AGENTFOLD_GATE_HANDOFF"
_SOURCE_REPO_ENV = "AGENTFOLD_GATE_SOURCE_REPO"
_EXECUTION_ROOT_ENV = "AGENTFOLD_GATE_EXECUTION_ROOT"
_OUTER_CONTROL_FD_ENV = "AGENTFOLD_GATE_CONTROL_FD"
_INNER_CONTROL_FD_ENV = "AGENTFOLD_GATE_INNER_CONTROL_FD"
_WORKER_ENV = "AGENTFOLD_GATE_INTERNAL_WORKER"
_OWNER_ENV = "AGENTFOLD_GATE_OWNER"
_BOOTSTRAP_CLOCK_GETTIME_SOURCE = "clock_gettime:CLOCK_MONOTONIC"
_BOOTSTRAP_OS_TIMES_SOURCE = "os.times:elapsed"
_GIT_NO_REPLACE_ENV = "GIT_NO_REPLACE_OBJECTS"
_CONTROLLER_CLOSURE_PATHS = (
    "automation/run_test_gate.py",
    "automation/test_gate_controller.py",
    "automation/run_tests.py",
    "automation/test_manifest.py",
    "automation/test_gate_config.py",
    "automation/file_test_budget_task.py",
    "automation/_vendor/__init__.py",
    "automation/_vendor/tomli/__init__.py",
    "automation/_vendor/tomli/_parser.py",
    "automation/_vendor/tomli/_re.py",
    "automation/_vendor/tomli/_types.py",
)
_POLICY_CLOSURE_PATHS = tuple(
    path
    for path in _CONTROLLER_CLOSURE_PATHS
    if path == "automation/test_gate_config.py"
    or path.startswith("automation/_vendor/")
)


def _canonical_json(value):
    return json.dumps(
        value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _valid_sha256(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _send_control_frame(control, value):
    payload = _canonical_json(value)
    if len(payload) > CONTROL_FRAME_MAX_BYTES:
        raise RuntimeError("test-gate control frame is oversized")
    control.sendall(struct.pack("!I", len(payload)) + payload)


def _receive_exact(control, length, deadline):
    chunks = []
    remaining = length
    while remaining:
        now = _clock_value()
        if now >= deadline:
            raise TimeoutError("test-gate control frame missed its deadline")
        readable, _, _ = select.select((control,), (), (), deadline - now)
        if not readable:
            raise TimeoutError("test-gate control frame missed its deadline")
        if _clock_value() >= deadline:
            raise TimeoutError("test-gate control frame arrived at its deadline")
        chunk = control.recv(remaining)
        if not chunk:
            raise EOFError("test-gate control pipe closed before a complete frame")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _receive_control_frame(control, deadline):
    header = _receive_exact(control, 4, deadline)
    length = struct.unpack("!I", header)[0]
    if length <= 0 or length > CONTROL_FRAME_MAX_BYTES:
        raise RuntimeError("test-gate control frame length is invalid")
    payload = _receive_exact(control, length, deadline)
    if _clock_value() >= deadline:
        raise TimeoutError("test-gate control frame completed at its deadline")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise RuntimeError("test-gate control frame is malformed") from error
    if not isinstance(value, dict):
        raise RuntimeError("test-gate control frame must be an object")
    return value


def _clock_value():
    source, value = _bootstrap_monotonic_start()
    del source
    return value


def _bootstrap_monotonic_start():
    """Read an identified monotonic source whose epoch survives exec."""
    clock_gettime = getattr(time, "clock_gettime", None)
    clock_id = getattr(time, "CLOCK_MONOTONIC", None)
    if callable(clock_gettime) and clock_id is not None:
        try:
            value = clock_gettime(clock_id)
        except (OSError, ValueError):
            pass
        else:
            if (
                not isinstance(value, bool)
                and isinstance(value, (int, float))
                and math.isfinite(value)
                and value >= 0
            ):
                return _BOOTSTRAP_CLOCK_GETTIME_SOURCE, float(value)
    times = getattr(os, "times", None)
    if os.name == "posix" and callable(times):
        try:
            value = times().elapsed
        except (AttributeError, OSError, ValueError):
            pass
        else:
            if (
                not isinstance(value, bool)
                and isinstance(value, (int, float))
                and math.isfinite(value)
                and value >= 0
            ):
                return _BOOTSTRAP_OS_TIMES_SOURCE, float(value)
    raise RuntimeError("no supported cross-process monotonic clock is available")


def _reserved_boundary_requested(arguments):
    """Recognize valid, malformed, and repeated reserved-boundary spellings."""
    for argument in arguments:
        name = argument.split("=", 1)[0]
        if (
            len(name) > 2
            and (
                name.startswith("--provider-hard")
                or "--provider-hard".startswith(name)
                or name.startswith("--at-transition")
                or "--at-transition".startswith(name)
            )
        ):
            return True
    return False


def _raw_gate(arguments):
    return arguments[0] if arguments and arguments[0] in ("routine", "final") else "unknown"


def _static_elapsed(started_source, started):
    if (
        started_source not in (
            _BOOTSTRAP_CLOCK_GETTIME_SOURCE,
            _BOOTSTRAP_OS_TIMES_SOURCE,
        )
        or isinstance(started, bool)
        or not isinstance(started, (int, float))
        or not math.isfinite(started)
        or started < 0
    ):
        return None
    try:
        current_source, current = _bootstrap_monotonic_start()
    except RuntimeError:
        return None
    if current_source != started_source or current < started:
        return None
    return float(current - started)


def _not_run_cleanup(worker_started, reason):
    attempted = False if worker_started is not None else None
    result = reason if worker_started is not None else "unavailable"
    return {
        "worker_started": worker_started,
        "process_group_cleanup": {
            "attempted": attempted,
            "result": result,
        },
        "ownership_token_cleanup": {
            "attempted": attempted,
            "result": result,
            "discovery_completeness": (
                "not-run" if worker_started is not None else "unavailable"
            ),
        },
    }


def _deliver_static_output(payload, descriptor=None, timeout=STATIC_OUTPUT_TIMEOUT_SECONDS):
    """Keep the supervisor responsive when its stdout sink stops reading."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8", "backslashreplace")
    if not isinstance(payload, bytes) or len(payload) > CONTROL_FRAME_MAX_BYTES:
        return {"disposition": "oversized", "written": False}
    try:
        output = sys.stdout.fileno() if descriptor is None else int(descriptor)
        writer = os.fork()
    except (AttributeError, OSError, TypeError, ValueError) as error:
        return {
            "disposition": "unavailable",
            "written": False,
            "reason": str(error),
        }
    if writer == 0:  # pragma: no branch - child exits through os._exit only
        try:
            offset = 0
            while offset < len(payload):
                try:
                    written = os.write(output, payload[offset:])
                except InterruptedError:
                    continue
                if written <= 0:
                    os._exit(1)
                offset += written
        except BaseException:
            os._exit(1)
        os._exit(0)

    deadline = time.monotonic() + max(0.0, float(timeout))
    while True:
        try:
            waited, status = os.waitpid(writer, os.WNOHANG)
        except InterruptedError:
            continue
        except OSError as error:
            return {
                "disposition": "wait-failed",
                "written": False,
                "reason": str(error),
            }
        if waited == writer:
            written = os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
            return {
                "disposition": "written" if written else "write-failed",
                "written": written,
            }
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            with contextlib.suppress(ProcessLookupError, OSError):
                os.kill(writer, signal.SIGKILL)
            # Reaping must not turn a bounded delivery failure into another
            # unbounded wait.  A still-running child is inherited and reaped by
            # the OS when this short-lived supervisor exits.
            with contextlib.suppress(ChildProcessError, OSError):
                os.waitpid(writer, os.WNOHANG)
            return {"disposition": "timed-out", "written": False}
        time.sleep(min(0.005, remaining))


def _static_result(
    gate,
    outcome,
    reason,
    incomplete=(),
    started_source=None,
    started=None,
    worker_started=None,
    cleanup=None,
    policy_frame=None,
    duration=_UNSET,
    deadline_reached=False,
    post_claim_cleanup=None,
    arguments=(),
):
    gate_exit = 1 if outcome in ("blocked-failed", "blocked-incomplete") else 2
    if duration is _UNSET:
        duration = _static_elapsed(started_source, started)
    target = policy_frame.get("target_seconds") if isinstance(policy_frame, dict) else None
    maximum = (
        policy_frame.get("maximum_seconds") if isinstance(policy_frame, dict) else None
    )
    policy_digest = (
        policy_frame.get("policy_digest") if isinstance(policy_frame, dict) else None
    )
    candidate_digest = None
    if isinstance(policy_frame, dict):
        candidate_digest = policy_frame.get("authoritative_index", {}).get(
            "semantic_sha256"
        )
    if (
        deadline_reached
        and duration is not None
        and maximum is not None
        and duration < maximum
    ):
        duration = None
    target_exceeded = target is not None and (
        deadline_reached or (duration is not None and duration >= target)
    )
    maximum_exceeded = maximum is not None and (
        deadline_reached or (duration is not None and duration >= maximum)
    )
    if not isinstance(cleanup, dict):
        cleanup = _not_run_cleanup(
            worker_started,
            "pending-after-claim" if post_claim_cleanup is not None else "not-needed",
        )
    containment = {"mode": "supervisor-static"}
    containment.update(cleanup)
    report = {
        "schema": REPORT_SCHEMA,
        "gate_id": gate,
        "outcome": outcome,
        "gate_exit_code": gate_exit,
        "command_outcome": outcome,
        "exit_code": gate_exit,
        "evidence": "none",
        "evidence_authority": "cooperative-same-interpreter",
        "controlled_completion": False,
        "enforcement_eligible": False,
        "enforcement": "not-enforced",
        "terminalized_pass": False,
        "reason": reason,
        "incomplete": list(incomplete),
        "candidate": None,
        "tested_view": None,
        "test_plan": None,
        "execution_identity": None,
        "decision_protocol": None,
        "policy_digest": policy_digest,
        "critical": {},
        "selected": [],
        "deferred": [],
        "components": [],
        "process_containment": containment,
        "target_exceeded": target_exceeded,
        "maximum_exceeded": maximum_exceeded,
        "target_seconds": target,
        "maximum_seconds": maximum,
        "invocation": {
            "kind": "supervisor-static",
            "started_monotonic_source": started_source,
            "started_monotonic": started,
            "worker_started": worker_started,
        },
        "duration_seconds": duration,
        "publication_status": "not-written",
        "publication_reason": "supervisor static result was not projected to a fixed report path",
        "report_write": {"disposition": "not-written"},
        "publication_id": None,
        "receipt_binding_digest": None,
    }
    decision = {
        "schema": "agentfold.test-gate-decision/v1",
        "gate_id": gate,
        "outcome": outcome,
        "gate_exit_code": gate_exit,
        "terminalized_pass": False,
        "reason": reason,
        "duration_seconds": duration,
        "target_seconds": target,
        "maximum_seconds": maximum,
        "policy_digest": policy_digest,
        "candidate_digest": candidate_digest,
        "incomplete": list(incomplete),
        "evidence_authority": "cooperative-same-interpreter",
        "controlled_completion": False,
        "enforcement_eligible": False,
        "enforcement": "not-enforced",
    }
    report["decision"] = decision
    report["decision_digest"] = _sha256_bytes(_canonical_json(decision))
    claim = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    claim_delivery = _deliver_static_output(claim)
    claim_sent = claim_delivery.get("written") is True
    observed_cleanup = None
    filing = None
    if post_claim_cleanup is not None:
        observed_cleanup = post_claim_cleanup()
        if claim_sent and target_exceeded and duration is not None:
            filing = _file_static_target_breach(
                report,
                policy_frame,
                arguments,
            )
        elif claim_sent and target_exceeded:
            filing = {
                "disposition": "not-filed",
                "mutated": False,
                "reason": "measured elapsed time is unavailable",
            }
    if not claim_sent:
        return 2

    telemetry = (
        "test gate: {gate}\n"
        "outcome: {outcome}\n"
        "reason: {reason}\n"
        "machine report: not written (supervisor static decision)\n".format(
            gate=gate, outcome=outcome, reason=reason
        )
    )
    if observed_cleanup is not None:
        telemetry += (
            "post-claim cleanup: "
            + json.dumps(observed_cleanup, sort_keys=True, separators=(",", ":"))
            + "\n"
        )
        if filing is not None:
            telemetry += (
                "budget filing: "
                + json.dumps(filing, sort_keys=True, separators=(",", ":"))
                + "\n"
            )
    telemetry_delivery = _deliver_static_output(telemetry)
    if telemetry_delivery.get("written") is not True:
        return 2
    return report["exit_code"]


def _file_static_target_breach(report, policy_frame, arguments):
    """File a post-claim timeout occurrence without importing candidate modules."""
    occurrence = {
        "schema_id": REPORT_SCHEMA,
        "gate_id": report["gate_id"],
        "config_slot": "testing.{}.target_seconds".format(report["gate_id"]),
        "actual_seconds": report["duration_seconds"],
        "target_seconds": report["target_seconds"],
        "components": {},
        "candidate": policy_frame["authoritative_index"]["semantic_sha256"],
        "receipt": report["decision_digest"],
        "command": "automation/run_test_gate.py " + " ".join(arguments),
        "trigger": (
            _option(arguments, "--at-transition")
            or ("explicit" if "--explicit" in arguments else "pre-commit")
        ),
        "environment": {},
    }
    filer = Path(__file__).resolve().parent / "file_test_budget_task.py"
    environment = os.environ.copy()
    environment[_GIT_NO_REPLACE_ENV] = "1"
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                str(filer),
                "--repo",
                str(Path(__file__).resolve().parents[1]),
                "--occurrence-json",
                json.dumps(occurrence, sort_keys=True, separators=(",", ":")),
                "--lock-timeout",
                "0.5",
            ],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=POST_CLAIM_FILING_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {"disposition": "timed-out", "mutated": None}
    except OSError as error:
        return {"disposition": "unavailable", "mutated": False, "reason": str(error)}
    try:
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        filing = json.loads(lines[-1])
    except (IndexError, TypeError, ValueError):
        return {"disposition": "invalid-result", "mutated": None}
    if result.returncode != 0 or not isinstance(filing, dict):
        return {"disposition": "failed", "mutated": None}
    return filing


def _git(repository, arguments, environment=None):
    environment = dict(os.environ if environment is None else environment)
    environment[_GIT_NO_REPLACE_ENV] = "1"
    result = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=str(repository),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError("Git candidate capture failed")
    return result.stdout


def _option(arguments, name):
    values = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == name:
            if index + 1 >= len(arguments):
                return None
            values.append(arguments[index + 1])
            index += 2
            continue
        prefix = name + "="
        if argument.startswith(prefix):
            values.append(argument[len(prefix):])
        index += 1
    return values[-1] if values else None


def _candidate_coordinates(repository, arguments):
    staged = "--staged" in arguments
    gate = arguments[0] if arguments else ""
    if staged:
        return {
            "kind": "staged-index",
            "base_revision": _bootstrap_resolve_commit(repository, "HEAD"),
            "candidate_revision": "",
        }
    if gate != "final":
        raise RuntimeError("routine candidate must be staged")
    candidate_name = _option(arguments, "--candidate-revision")
    base_name = _option(arguments, "--base-revision")
    if not candidate_name:
        status = _git(repository, ["status", "--porcelain=v1", "--untracked-files=all"])
        if status:
            raise RuntimeError(
                "explicit final without a revision range requires a clean checkout"
            )
        candidate_name = "HEAD"
    candidate_revision = _bootstrap_resolve_commit(repository, candidate_name)
    return {
        "kind": "revision-range",
        "base_revision": _bootstrap_resolve_commit(
            repository, base_name or candidate_revision + "^"
        ),
        "candidate_revision": candidate_revision,
    }


def _write_exact_file(root, relative, content, mode="100644"):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
    path.chmod(0o755 if mode == "100755" else 0o644)


def _policy_closure_records(root):
    records = []
    for relative in _POLICY_CLOSURE_PATHS:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("canonical policy parser closure is incomplete")
        records.append(
            {
                "path": relative,
                "sha256": _file_sha256(path),
                "mode": "100755" if path.stat().st_mode & stat.S_IXUSR else "100644",
            }
        )
    return records


def _revision_file(repository, revision, relative):
    environment = os.environ.copy()
    environment[_GIT_NO_REPLACE_ENV] = "1"
    result = subprocess.run(
        ["git", "--no-replace-objects", "show", "{}:{}".format(revision, relative)],
        cwd=str(repository),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        presence = subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "ls-tree",
                "-z",
                "--name-only",
                revision,
                "--",
                relative,
            ],
            cwd=str(repository),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if presence.returncode or presence.stdout:
            raise RuntimeError("policy discovery could not read an exact Git object")
        return None
    mode_result = subprocess.run(
        ["git", "--no-replace-objects", "ls-tree", revision, "--", relative],
        cwd=str(repository),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if mode_result.returncode or not mode_result.stdout.strip():
        raise RuntimeError("policy discovery could not identify an exact Git object")
    mode = mode_result.stdout.split(None, 1)[0]
    if mode not in ("100644", "100755"):
        raise RuntimeError("policy discovery encountered an unsupported Git mode")
    return result.stdout, mode


def _materialize_policy_inputs(repository, arguments, root):
    coordinates = _candidate_coordinates(repository, arguments)
    index = root / "candidate.index"
    if coordinates["kind"] == "staged-index":
        _copy_index(_selected_index(repository), index)
    else:
        environment = os.environ.copy()
        environment[_GIT_NO_REPLACE_ENV] = "1"
        environment["GIT_INDEX_FILE"] = str(index)
        _git(repository, ["read-tree", coordinates["candidate_revision"]], environment)

    candidate_root = root / "candidate-policy"
    candidate_root.mkdir(mode=0o700)
    environment = os.environ.copy()
    environment[_GIT_NO_REPLACE_ENV] = "1"
    environment["GIT_INDEX_FILE"] = str(index)
    for relative in ("agentfold.toml",) + _POLICY_CLOSURE_PATHS:
        result = subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "checkout-index",
                "--prefix=" + str(candidate_root) + os.sep,
                "--",
                relative,
            ],
            cwd=str(repository),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode:
            raise RuntimeError(
                "policy discovery could not materialize canonical candidate inputs"
            )

    trusted_root = root / "trusted-policy"
    trusted_root.mkdir(mode=0o700)
    for relative in ("agentfold.toml",) + _POLICY_CLOSURE_PATHS:
        value = _revision_file(repository, coordinates["base_revision"], relative)
        if value is None:
            raise RuntimeError(
                "trusted base policy or canonical parser closure is unavailable"
            )
        _write_exact_file(trusted_root, relative, value[0], value[1])

    base_path = trusted_root / "agentfold.toml"
    candidate_path = candidate_root / "agentfold.toml"
    if not candidate_path.is_file() or candidate_path.is_symlink():
        raise RuntimeError("candidate policy is unavailable: agentfold.toml")
    closures = {}
    for name, closure_root in (
        ("trusted", trusted_root),
        ("candidate", candidate_root),
    ):
        closures[name] = _policy_closure_records(closure_root)
    index_semantic = _semantic_index(repository, index)
    index_identity = {
        "file_sha256": _file_sha256(index),
        "semantic_sha256": _sha256_bytes(index_semantic),
    }
    return (
        coordinates,
        index,
        trusted_root,
        candidate_root,
        base_path,
        candidate_path,
        closures,
        index_identity,
    )


def _load_exact_policy(trusted_root, candidate_path, base_path):
    import importlib.util

    for name in tuple(sys.modules):
        if name == "_vendor" or name.startswith("_vendor."):
            sys.modules.pop(name, None)
    automation = trusted_root / "automation"
    sys.path.insert(0, str(automation))
    try:
        spec = importlib.util.spec_from_file_location(
            "_agentfold_discovery_test_gate_config",
            str(automation / "test_gate_config.py"),
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("canonical policy parser could not be loaded")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        policy = module.load_policy_union(base_path, candidate_path)
        return module, policy
    finally:
        try:
            sys.path.remove(str(automation))
        except ValueError:
            pass


def _discover_policy_frame(repository, arguments, root):
    (
        coordinates,
        index,
        trusted_root,
        _candidate_root,
        base_path,
        candidate_path,
        closures,
        index_identity,
    ) = _materialize_policy_inputs(repository, arguments, root)
    module, policy = _load_exact_policy(trusted_root, candidate_path, base_path)
    if (
        _policy_closure_records(trusted_root) != closures["trusted"]
        or _policy_closure_records(_candidate_root) != closures["candidate"]
    ):
        raise RuntimeError("policy parser closure changed during authoritative discovery")
    gate = arguments[0] if arguments else ""
    final = getattr(policy, "final", None)
    budgets = {
        "routine": {
            "target_seconds": float(policy.routine.target_seconds),
            "maximum_seconds": float(policy.routine.maximum_seconds),
        },
        "final": {
            "target_seconds": float(
                final.target_seconds
                if final is not None
                else policy.final_target_seconds
            ),
            "maximum_seconds": float(
                final.maximum_seconds
                if final is not None
                else policy.final_maximum_seconds
            ),
        },
    }
    target = budgets[gate]["target_seconds"]
    maximum = budgets[gate]["maximum_seconds"]
    trusted_parser_digest = _sha256_bytes(_canonical_json(closures["trusted"]))
    candidate_parser_digest = _sha256_bytes(_canonical_json(closures["candidate"]))
    launcher = {
        "path": "automation/run_test_gate.py",
        "sha256": _file_sha256(Path(__file__).resolve()),
    }
    frame = {
        "schema": POLICY_FRAME_SCHEMA,
        "gate_id": gate,
        "target_seconds": target,
        "maximum_seconds": maximum,
        "budgets": budgets,
        "discovery_ceiling_seconds": DISCOVERY_CEILING_SECONDS,
        "policy_digest": module.canonical_policy_digest(policy),
        "base_config_sha256": (
            _file_sha256(base_path) if base_path is not None else None
        ),
        "candidate_config_sha256": _file_sha256(candidate_path),
        "trusted_parser_closure": closures["trusted"],
        "trusted_parser_closure_digest": trusted_parser_digest,
        "candidate_parser_closure_digest": candidate_parser_digest,
        "authoritative_index": index_identity,
        "launcher": launcher,
        "candidate_kind": coordinates["kind"],
        "base_revision": coordinates["base_revision"],
        "candidate_revision": coordinates["candidate_revision"],
    }
    frame["frame_digest"] = _sha256_bytes(_canonical_json(frame))
    return frame, index


def _validate_policy_frame(frame, expected_gate):
    required = {
        "schema",
        "gate_id",
        "target_seconds",
        "maximum_seconds",
        "budgets",
        "discovery_ceiling_seconds",
        "policy_digest",
        "base_config_sha256",
        "candidate_config_sha256",
        "trusted_parser_closure",
        "trusted_parser_closure_digest",
        "candidate_parser_closure_digest",
        "authoritative_index",
        "launcher",
        "candidate_kind",
        "base_revision",
        "candidate_revision",
        "frame_digest",
    }
    if set(frame) != required:
        raise RuntimeError("test-gate policy frame has an invalid shape")
    supplied_digest = frame["frame_digest"]
    unsigned = dict(frame)
    unsigned.pop("frame_digest")
    try:
        computed_digest = _sha256_bytes(_canonical_json(unsigned))
    except (TypeError, ValueError) as error:
        raise RuntimeError("test-gate policy frame is not canonical JSON") from error
    if supplied_digest != computed_digest:
        raise RuntimeError("test-gate policy frame digest is invalid")
    if frame["schema"] != POLICY_FRAME_SCHEMA or frame["gate_id"] != expected_gate:
        raise RuntimeError("test-gate policy frame identity is invalid")
    if frame["discovery_ceiling_seconds"] != DISCOVERY_CEILING_SECONDS:
        raise RuntimeError("test-gate policy discovery ceiling is invalid")
    for name in ("target_seconds", "maximum_seconds"):
        value = frame[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            raise RuntimeError("test-gate policy budget is invalid")
    if frame["target_seconds"] > frame["maximum_seconds"]:
        raise RuntimeError("test-gate policy target exceeds its maximum")
    if frame["maximum_seconds"] < DISCOVERY_CEILING_SECONDS:
        raise RuntimeError("test-gate maximum must be at least 5 seconds")
    budgets = frame["budgets"]
    if not isinstance(budgets, dict) or set(budgets) != {"routine", "final"}:
        raise RuntimeError("test-gate policy budget set is invalid")
    for lane, budget in budgets.items():
        if not isinstance(budget, dict) or set(budget) != {
            "target_seconds",
            "maximum_seconds",
        }:
            raise RuntimeError("test-gate {} budget shape is invalid".format(lane))
        target_value = budget["target_seconds"]
        maximum_value = budget["maximum_seconds"]
        if (
            isinstance(target_value, bool)
            or isinstance(maximum_value, bool)
            or not isinstance(target_value, (int, float))
            or not isinstance(maximum_value, (int, float))
            or not math.isfinite(target_value)
            or not math.isfinite(maximum_value)
            or target_value <= 0
            or maximum_value < DISCOVERY_CEILING_SECONDS
            or target_value > maximum_value
        ):
            raise RuntimeError("test-gate {} budget is invalid".format(lane))
    if budgets[expected_gate] != {
        "target_seconds": frame["target_seconds"],
        "maximum_seconds": frame["maximum_seconds"],
    }:
        raise RuntimeError("test-gate active budget does not match its lane")
    for name in (
        "policy_digest",
        "candidate_config_sha256",
        "trusted_parser_closure_digest",
        "candidate_parser_closure_digest",
        "frame_digest",
    ):
        if not _valid_sha256(frame[name]):
            raise RuntimeError("test-gate policy frame contains an invalid digest")
    if not _valid_sha256(frame["base_config_sha256"]):
        raise RuntimeError("test-gate base policy digest is invalid")
    closure = frame["trusted_parser_closure"]
    if (
        not isinstance(closure, list)
        or [record.get("path") for record in closure] != list(_POLICY_CLOSURE_PATHS)
        or _sha256_bytes(_canonical_json(closure))
        != frame["trusted_parser_closure_digest"]
    ):
        raise RuntimeError("test-gate policy parser closure is invalid")
    if any(
        set(record) != {"path", "mode", "sha256"}
        or record["mode"] not in ("100644", "100755")
        or not _valid_sha256(record["sha256"])
        for record in closure
    ):
        raise RuntimeError("test-gate policy parser record is invalid")
    index_identity = frame["authoritative_index"]
    if (
        not isinstance(index_identity, dict)
        or set(index_identity) != {"file_sha256", "semantic_sha256"}
        or not _valid_sha256(index_identity["file_sha256"])
        or not _valid_sha256(index_identity["semantic_sha256"])
    ):
        raise RuntimeError("test-gate authoritative index identity is invalid")
    launcher = frame["launcher"]
    if (
        not isinstance(launcher, dict)
        or set(launcher) != {"path", "sha256"}
        or launcher["path"] != "automation/run_test_gate.py"
        or not _valid_sha256(launcher["sha256"])
    ):
        raise RuntimeError("test-gate launcher identity is invalid")
    return float(frame["maximum_seconds"])


def _bootstrap_resolve_commit(repository, revision):
    oid = _git(repository, ["rev-parse", "--verify", revision + "^{commit}"])
    value = os.fsdecode(oid).strip()
    if not value:
        raise RuntimeError("candidate revision is unavailable")
    return value


def _selected_index(repository):
    raw = _git(repository, ["rev-parse", "--git-path", "index"]).rstrip(b"\n")
    if not raw or b"\0" in raw or b"\n" in raw:
        raise RuntimeError("selected Git index path is malformed")
    path = Path(os.fsdecode(raw))
    return path if path.is_absolute() else repository / path


def _copy_index(source, destination):
    if source.is_symlink() or not source.is_file():
        raise RuntimeError("selected Git index is unavailable or unsafe")
    with source.open("rb") as reader, destination.open("xb") as writer:
        shutil.copyfileobj(reader, writer)
        writer.flush()
        os.fsync(writer.fileno())
    destination.chmod(0o600)


def _index_records(repository, frozen_index):
    environment = os.environ.copy()
    environment[_GIT_NO_REPLACE_ENV] = "1"
    environment["GIT_INDEX_FILE"] = str(frozen_index)
    output = _git(repository, ["ls-files", "--stage", "-z"], environment)
    records = []
    for raw in output[:-1].split(b"\0") if output else ():
        try:
            header, raw_path = raw.split(b"\t", 1)
            raw_mode, raw_oid, raw_stage = header.split(b" ")
            mode = raw_mode.decode("ascii")
            oid = raw_oid.decode("ascii").lower()
            path = os.fsdecode(raw_path)
        except (UnicodeDecodeError, ValueError) as error:
            raise RuntimeError("candidate index entry is malformed") from error
        relative = Path(path)
        if (
            mode not in ("100644", "100755")
            or raw_stage != b"0"
            or not oid
            or any(character not in "0123456789abcdef" for character in oid)
            or not path
            or relative.is_absolute()
            or ".." in relative.parts
            or any(part.casefold() == ".git" for part in relative.parts)
        ):
            raise RuntimeError("candidate index contains an unsupported entry")
        records.append({"path": path, "mode": mode, "object": oid})
    return tuple(sorted(records, key=lambda record: record["path"]))


def _semantic_index(repository, frozen_index):
    return json.dumps(
        _index_records(repository, frozen_index),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _controller_closure(snapshot, index_records):
    modes = {record["path"]: record["mode"] for record in index_records}
    records = []
    for relative in _CONTROLLER_CLOSURE_PATHS:
        path = snapshot / relative
        if relative not in modes or path.is_symlink() or not path.is_file():
            raise RuntimeError("controller closure is incomplete")
        records.append(
            {"path": relative, "mode": modes[relative], "sha256": _file_sha256(path)}
        )
    return records


def _seal_snapshot(snapshot):
    for current, directories, files in os.walk(str(snapshot), topdown=False):
        current_path = Path(current)
        for name in files:
            path = current_path / name
            mode = stat.S_IMODE(path.stat().st_mode)
            path.chmod(0o500 if mode & 0o111 else 0o400)
        for name in directories:
            (current_path / name).chmod(0o700)
        current_path.chmod(0o700)


def _unseal_snapshot(snapshot):
    for current, directories, files in os.walk(str(snapshot)):
        current_path = Path(current)
        current_path.chmod(0o700)
        for name in directories:
            (current_path / name).chmod(0o700)
        for name in files:
            (current_path / name).chmod(0o600)


def _freeze(
    repository,
    arguments,
    temporary_root,
    started,
    started_source,
    policy_frame=None,
    absolute_deadline=None,
    authoritative_index=None,
):
    frozen_index = (
        Path(authoritative_index)
        if authoritative_index is not None
        else temporary_root / "candidate.index"
    )
    coordinates = _candidate_coordinates(repository, arguments)
    staged = coordinates["kind"] == "staged-index"
    if staged:
        base_revision = coordinates["base_revision"]
        if authoritative_index is None:
            _copy_index(_selected_index(repository), frozen_index)
        candidate_revision = ""
        kind = "staged-index"
    else:
        candidate_revision = coordinates["candidate_revision"]
        base_revision = coordinates["base_revision"]
        if authoritative_index is None:
            environment = os.environ.copy()
            environment[_GIT_NO_REPLACE_ENV] = "1"
            environment["GIT_INDEX_FILE"] = str(frozen_index)
            _git(repository, ["read-tree", candidate_revision], environment)
        kind = "revision-range"

    frozen_semantic = _semantic_index(repository, frozen_index)
    if policy_frame is not None and policy_frame.get("authoritative_index") != {
        "file_sha256": _file_sha256(frozen_index),
        "semantic_sha256": _sha256_bytes(frozen_semantic),
    }:
        raise RuntimeError("authoritative policy index changed before full materialization")
    records = _index_records(repository, frozen_index)
    snapshot = temporary_root / "snapshot"
    snapshot.mkdir(mode=0o700)
    environment = os.environ.copy()
    environment[_GIT_NO_REPLACE_ENV] = "1"
    environment["GIT_INDEX_FILE"] = str(frozen_index)
    _git(
        repository,
        ["checkout-index", "--all", "--prefix=" + str(snapshot) + os.sep],
        environment,
    )
    # Candidate checks use this fixed empty sentinel with the separately frozen
    # GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE tuple. Git cannot track a .git entry.
    (snapshot / ".git").mkdir(mode=0o700)
    if staged:
        live_index = _selected_index(repository)
        if (
            _semantic_index(repository, live_index) != frozen_semantic
            or _bootstrap_resolve_commit(repository, "HEAD") != base_revision
        ):
            raise RuntimeError("selected Git index changed during candidate capture")
    closure = _controller_closure(snapshot, records)
    frozen_index_sha256 = _file_sha256(frozen_index)
    frozen_index.chmod(0o400)
    _seal_snapshot(snapshot)
    return {
        "schema": HANDOFF_SCHEMA,
        "started_monotonic": started,
        "started_monotonic_source": started_source,
        "absolute_deadline_monotonic": absolute_deadline,
        "policy_frame": policy_frame,
        "source_repository": str(repository),
        "execution_root": str(snapshot),
        "frozen_index": str(frozen_index),
        "candidate_kind": kind,
        "base_revision": base_revision,
        "candidate_revision": candidate_revision,
        "frozen_index_sha256": frozen_index_sha256,
        "index_semantic_sha256": hashlib.sha256(frozen_semantic).hexdigest(),
        "controller_closure": closure,
    }


def _expected_gate_exit(outcome):
    if outcome in ("pass", "deferred", "not-run"):
        return 0
    if outcome in ("blocked-failed", "blocked-incomplete"):
        return 1
    if outcome in ("invalid", "error"):
        return 2
    raise RuntimeError("test-gate outcome is invalid")


def _validate_controller_claim(claim, gate, policy_frame):
    required = {
        "schema",
        "gate_id",
        "outcome",
        "gate_exit_code",
        "terminalized_pass",
        "policy_digest",
        "decision_digest",
        "receipt_binding_digest",
        "evidence_authority",
        "controlled_completion",
        "enforcement_eligible",
        "claim_digest",
    }
    if not isinstance(claim, dict) or set(claim) != required:
        raise RuntimeError("controller terminal claim has an invalid shape")
    unsigned = dict(claim)
    claim_digest = unsigned.pop("claim_digest")
    if claim_digest != _sha256_bytes(_canonical_json(unsigned)):
        raise RuntimeError("controller terminal claim digest is invalid")
    if (
        claim["schema"] != CONTROLLER_CLAIM_SCHEMA
        or claim["gate_id"] != gate
        or claim["gate_exit_code"] != _expected_gate_exit(claim["outcome"])
        or claim["terminalized_pass"] != (claim["outcome"] == "pass")
        or claim["policy_digest"] != policy_frame["policy_digest"]
        or not _valid_sha256(claim["decision_digest"])
        or (
            claim["receipt_binding_digest"] is not None
            and not _valid_sha256(claim["receipt_binding_digest"])
        )
        or claim["evidence_authority"] != "cooperative-same-interpreter"
        or claim["controlled_completion"] is not False
        or claim["enforcement_eligible"] is not False
    ):
        raise RuntimeError("controller terminal claim is inconsistent")
    return claim_digest


def _broker_terminal_frame(claim, policy_frame):
    return {
        "schema": TERMINAL_FRAME_SCHEMA,
        "gate_id": claim["gate_id"],
        "outcome": claim["outcome"],
        "gate_exit_code": claim["gate_exit_code"],
        "terminalized_pass": claim["terminalized_pass"],
        "policy_digest": claim["policy_digest"],
        "policy_frame_digest": policy_frame["frame_digest"],
        "decision_digest": claim["decision_digest"],
        "claim_digest": claim["claim_digest"],
        "evidence_authority": claim["evidence_authority"],
        "controlled_completion": claim["controlled_completion"],
        "enforcement_eligible": claim["enforcement_eligible"],
    }


def _verify_controller_report(repository, gate, claim, controller_exit):
    path = repository / "tmp/test-gate-reports" / ("latest-" + gate + ".json")
    if not path.is_file() or path.is_symlink():
        if controller_exit == 2:
            return
        raise RuntimeError("controller did not publish the fixed-lane terminal report")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RuntimeError("controller terminal report is unreadable") from error
    decision = report.get("decision")
    if (
        report.get("schema") != REPORT_SCHEMA
        or report.get("gate_id") != gate
        or report.get("outcome") != claim["outcome"]
        or report.get("gate_exit_code") != claim["gate_exit_code"]
        or report.get("terminalized_pass") != claim["terminalized_pass"]
        or report.get("policy_digest") != claim["policy_digest"]
        or report.get("decision_digest") != claim["decision_digest"]
        or _sha256_bytes(_canonical_json(decision)) != claim["decision_digest"]
        or report.get("evidence_authority") != claim["evidence_authority"]
        or report.get("controlled_completion") != claim["controlled_completion"]
        or report.get("enforcement_eligible") != claim["enforcement_eligible"]
        or report.get("exit_code") != controller_exit
    ):
        raise RuntimeError("controller terminal report contradicts its immutable decision")
    binding = claim["receipt_binding_digest"]
    if report.get("receipt_binding_digest") != binding:
        raise RuntimeError("controller terminal report changed its receipt identity")
    if controller_exit == 2 and binding is not None:
        receipt_root = repository / "tmp/test-gate-receipts"
        if (receipt_root / (binding + ".json")).exists() or (
            receipt_root / (binding + ".commit.json")
        ).exists():
            raise RuntimeError("publication failure left reusable receipt evidence")


def _worker_exit_for_claim(claim, controller_exit):
    gate_exit = claim["gate_exit_code"]
    if controller_exit == gate_exit:
        return controller_exit
    if controller_exit == 2 and gate_exit in (0, 1):
        return 2
    raise RuntimeError("controller exit contradicts the terminal decision")


def _worker_dispatch(arguments):
    if os.name != "posix":
        raise RuntimeError("test-gate supervision requires POSIX process semantics")
    raw_fd = os.environ.get(_OUTER_CONTROL_FD_ENV, "")
    owner = os.environ.get(_OWNER_ENV, "")
    if not raw_fd.isdigit() or len(owner) != 64:
        raise RuntimeError("test-gate worker authority is invalid")
    control = socket.socket(fileno=int(raw_fd))
    repository = Path(__file__).resolve().parents[1]
    try:
        with tempfile.TemporaryDirectory(prefix="agentfold-gate-worker-") as temporary:
            temporary_root = Path(temporary).resolve()
            temporary_root.chmod(0o700)
            policy_frame, authoritative_index = _discover_policy_frame(
                repository, arguments, temporary_root
            )
            _send_control_frame(control, policy_frame)
            acknowledgment = _receive_control_frame(
                control, _clock_value() + DISCOVERY_CEILING_SECONDS
            )
            if (
                set(acknowledgment)
                != {
                    "schema",
                    "policy_frame_digest",
                    "started_monotonic",
                    "started_monotonic_source",
                    "absolute_deadline_monotonic",
                }
                or acknowledgment.get("schema") != DEADLINE_FRAME_SCHEMA
                or acknowledgment.get("policy_frame_digest")
                != policy_frame["frame_digest"]
            ):
                raise RuntimeError("test-gate deadline acknowledgment is invalid")
            started = acknowledgment["started_monotonic"]
            started_source = acknowledgment["started_monotonic_source"]
            absolute_deadline = acknowledgment["absolute_deadline_monotonic"]
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
                for value in (started, absolute_deadline)
            ) or absolute_deadline != started + float(policy_frame["maximum_seconds"]):
                raise RuntimeError("test-gate absolute deadline is invalid")

            handoff = _freeze(
                repository,
                arguments,
                temporary_root,
                started,
                started_source,
                policy_frame,
                absolute_deadline,
                authoritative_index,
            )
            handoff_path = temporary_root / "handoff.json"
            with handoff_path.open("x", encoding="utf-8") as stream:
                json.dump(handoff, stream, sort_keys=True, separators=(",", ":"))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            handoff_path.chmod(0o400)
            environment = os.environ.copy()
            environment[_GIT_NO_REPLACE_ENV] = "1"
            environment.pop(_OUTER_CONTROL_FD_ENV, None)
            environment.pop(_WORKER_ENV, None)
            environment[_HANDOFF_ENV] = str(handoff_path)
            environment[_SOURCE_REPO_ENV] = handoff["source_repository"]
            environment[_EXECUTION_ROOT_ENV] = handoff["execution_root"]
            controller = (
                Path(handoff["execution_root"])
                / "automation/test_gate_controller.py"
            )
            broker_control, controller_control = socket.socketpair()
            environment[_INNER_CONTROL_FD_ENV] = str(controller_control.fileno())
            try:
                process = subprocess.Popen(
                    [sys.executable, "-I", "-S", str(controller), *arguments],
                    cwd=handoff["execution_root"],
                    env=environment,
                    pass_fds=(controller_control.fileno(),),
                )
                controller_control.close()
                claim = _receive_control_frame(broker_control, absolute_deadline)
                _validate_controller_claim(
                    claim, policy_frame["gate_id"], policy_frame
                )
                _send_control_frame(
                    control, _broker_terminal_frame(claim, policy_frame)
                )
                controller_exit = process.wait()
                _verify_controller_report(
                    repository,
                    policy_frame["gate_id"],
                    claim,
                    controller_exit,
                )
                return _worker_exit_for_claim(claim, controller_exit)
            finally:
                broker_control.close()
                controller_control.close()
                _unseal_snapshot(Path(handoff["execution_root"]))
    finally:
        control.close()


def _owned_worker_pids(token):
    marker = "{}={}".format(_OWNER_ENV, token)
    owned = set()
    proc = Path("/proc")
    if sys.platform.startswith("linux") and proc.is_dir():
        try:
            entries = tuple(proc.iterdir())
        except OSError:
            entries = ()
        for entry in entries:
            if not entry.name.isdigit():
                continue
            try:
                if entry.stat().st_uid != os.getuid():
                    continue
                environment = (entry / "environ").read_bytes().split(b"\0")
            except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
                continue
            if marker.encode("ascii") in environment:
                owned.add(int(entry.name))
        return owned
    try:
        result = subprocess.run(
            ["ps", "eww", "-axo", "pid=,uid=,command="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=0.5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return owned
    if result.returncode:
        return owned
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3:
            continue
        try:
            pid, uid = int(fields[0]), int(fields[1])
        except ValueError:
            continue
        if uid == os.getuid() and marker in fields[2].split():
            owned.add(pid)
    return owned


def _kill_worker_group(process, token):
    group_result = "signal-sent"
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        group_result = "already-exited"
    except PermissionError:
        group_result = "permission-denied"
    except OSError:
        group_result = "error"
    matched = 0
    signaled = 0
    token_permission_denied = False
    discovery_result = (
        "best-effort-linux-proc"
        if sys.platform.startswith("linux") and Path("/proc").is_dir()
        else "best-effort-portable"
    )
    for _attempt in range(3):
        try:
            owned = _owned_worker_pids(token)
        except (OSError, RuntimeError, ValueError):
            owned = set()
            discovery_result = "unavailable"
        owned.discard(os.getpid())
        matched += len(owned)
        for pid in owned:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                continue
            except PermissionError:
                token_permission_denied = True
            except OSError:
                token_permission_denied = True
            else:
                signaled += 1
        if not owned:
            break
        try:
            process.wait(timeout=0.05)
        except subprocess.TimeoutExpired:
            pass
    try:
        process.wait(timeout=0.2)
    except subprocess.TimeoutExpired:
        worker_result = "still-running"
    else:
        worker_result = "exited"
    if discovery_result == "unavailable":
        token_result = "discovery-unavailable"
    elif token_permission_denied:
        token_result = "partial"
    elif matched:
        token_result = "signals-sent" if signaled else "already-exited"
    else:
        token_result = "no-match"
    return {
        "worker_started": True,
        "worker_result": worker_result,
        "process_group_cleanup": {
            "attempted": True,
            "result": group_result,
        },
        "ownership_token_cleanup": {
            "attempted": True,
            "result": token_result,
            "discovery_completeness": discovery_result,
        },
    }


def _validate_terminal_frame(frame):
    if set(frame) != {
        "schema",
        "gate_id",
        "outcome",
        "gate_exit_code",
        "terminalized_pass",
        "policy_digest",
        "policy_frame_digest",
        "decision_digest",
        "claim_digest",
        "evidence_authority",
        "controlled_completion",
        "enforcement_eligible",
    }:
        raise RuntimeError("test-gate terminal decision has an invalid shape")
    if (
        frame["schema"] != TERMINAL_FRAME_SCHEMA
        or frame["outcome"]
        not in (
            "pass",
            "deferred",
            "not-run",
            "blocked-failed",
            "blocked-incomplete",
            "invalid",
            "error",
        )
        or frame["gate_exit_code"] not in (0, 1, 2)
        or not isinstance(frame["terminalized_pass"], bool)
        or not _valid_sha256(frame["policy_digest"])
        or not _valid_sha256(frame["policy_frame_digest"])
        or not _valid_sha256(frame["decision_digest"])
        or not _valid_sha256(frame["claim_digest"])
        or frame["evidence_authority"] != "cooperative-same-interpreter"
        or frame["controlled_completion"] is not False
        or frame["enforcement_eligible"] is not False
    ):
        raise RuntimeError("test-gate terminal decision is invalid")
    if frame["gate_exit_code"] != _expected_gate_exit(frame["outcome"]) or frame["terminalized_pass"] != (
        frame["outcome"] == "pass"
    ):
        raise RuntimeError("test-gate terminal decision contradicts its outcome")


class _SupervisorTermination(Exception):
    """A termination request handled by the outer supervisor cleanup path."""

    def __init__(self, signal_number):
        super().__init__("test-gate supervisor was interrupted")
        self.signal_number = signal_number


def _raise_supervisor_termination(signal_number, _frame):
    raise _SupervisorTermination(signal_number)


@contextlib.contextmanager
def _ignore_cleanup_interrupts():
    """Keep repeated terminal signals from interrupting bounded descendant cleanup."""
    previous = {}
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        previous[signal_number] = signal.signal(signal_number, signal.SIG_IGN)
    try:
        yield
    finally:
        for signal_number, handler in previous.items():
            signal.signal(signal_number, handler)


@contextlib.contextmanager
def _supervisor_termination_scope():
    """Install and reliably restore the outer supervisor's SIGTERM handler."""
    previous = None
    try:
        previous = signal.signal(signal.SIGTERM, _raise_supervisor_termination)
        yield
    finally:
        if previous is not None:
            signal.signal(signal.SIGTERM, previous)


def _kill_worker_token(token):
    """Bound cleanup when launch was interrupted before Popen returned a handle."""
    for _attempt in range(3):
        try:
            owned = _owned_worker_pids(token)
        except (OSError, RuntimeError, ValueError):
            return
        owned.discard(os.getpid())
        for pid in owned:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        if not owned:
            return
        time.sleep(0.01)


def _supervise_worker(
    arguments,
    gate,
    started_source,
    started,
    owner,
    parent_control,
    child_control,
    environment,
    worker_path,
):
    process = None
    policy_frame = None
    maximum = None
    absolute_deadline = None
    try:
        try:
            process = subprocess.Popen(
                [sys.executable, "-I", "-S", str(worker_path), *arguments],
                cwd=str(worker_path.parents[1]),
                env=environment,
                pass_fds=(child_control.fileno(),),
                start_new_session=True,
            )
        except (OSError, ValueError) as error:
            return _static_result(
                gate,
                "error",
                "test-gate worker could not start: " + str(error),
                (),
                started_source,
                started,
                False,
                _not_run_cleanup(False, "not-needed-worker-not-started"),
            )
        child_control.close()
        discovery_deadline = started + DISCOVERY_CEILING_SECONDS
        policy_frame = _receive_control_frame(parent_control, discovery_deadline)
        maximum = _validate_policy_frame(policy_frame, gate)
        now = _clock_value()
        if now >= discovery_deadline:
            raise TimeoutError("test-gate policy discovery reached its 5-second ceiling")
        absolute_deadline = started + maximum
        acknowledgment = {
            "schema": DEADLINE_FRAME_SCHEMA,
            "policy_frame_digest": policy_frame["frame_digest"],
            "started_monotonic": started,
            "started_monotonic_source": started_source,
            "absolute_deadline_monotonic": absolute_deadline,
        }
        _send_control_frame(parent_control, acknowledgment)
        terminal = _receive_control_frame(parent_control, absolute_deadline)
        _validate_terminal_frame(terminal)
        if (
            terminal["gate_id"] != gate
            or terminal["policy_digest"] != policy_frame["policy_digest"]
            or terminal["policy_frame_digest"] != policy_frame["frame_digest"]
        ):
            raise RuntimeError("terminal decision used a different policy frame")
        worker_exit = process.wait()
        gate_exit = terminal["gate_exit_code"]
        if worker_exit == gate_exit:
            return worker_exit
        if worker_exit == 2 and gate_exit in (0, 1):
            return 2
        return _static_result(
            gate,
            "error",
            "worker exit {} contradicts terminal gate exit {}".format(
                worker_exit, gate_exit
            ),
            (),
            started_source,
            started,
            True,
            _not_run_cleanup(True, "not-needed-worker-exited"),
        )
    except (KeyboardInterrupt, _SupervisorTermination) as error:
        signal_number = (
            signal.SIGINT
            if isinstance(error, KeyboardInterrupt)
            else error.signal_number
        )
        with _ignore_cleanup_interrupts():
            if process is None:
                _kill_worker_token(owner)
            else:
                _kill_worker_group(process, owner)
        return 128 + signal_number
    except TimeoutError as error:
        if policy_frame is not None and absolute_deadline is not None:
            return _static_result(
                gate,
                "blocked-incomplete",
                str(error),
                ("gate-interval",),
                started_source,
                started,
                True,
                policy_frame=policy_frame,
                deadline_reached=True,
                post_claim_cleanup=lambda: _kill_worker_group(process, owner),
                arguments=arguments,
            )
        cleanup = _kill_worker_group(process, owner)
        return _static_result(
            gate,
            "blocked-incomplete",
            str(error),
            ("gate-interval",),
            started_source,
            started,
            True,
            cleanup,
        )
    except EOFError:
        returncode = process.poll()
        if returncode is None:
            try:
                returncode = process.wait(timeout=0.1)
            except subprocess.TimeoutExpired:
                pass
        cleanup = _kill_worker_group(process, owner)
        if returncode is None:
            returncode = process.poll()
        return _static_result(
            gate,
            "error",
            "test-gate worker exited without a terminal decision (exit {})".format(
                "unknown" if returncode is None else returncode
            ),
            (),
            started_source,
            started,
            True,
            cleanup,
        )
    except (OSError, RuntimeError, ValueError) as error:
        cleanup = _kill_worker_group(process, owner)
        return _static_result(
            gate,
            "error",
            str(error),
            (),
            started_source,
            started,
            True,
            cleanup,
        )
    finally:
        child_control.close()
        parent_control.close()


def _dispatch(arguments):
    started_source, started = _bootstrap_monotonic_start()
    gate = _raw_gate(arguments)
    if _reserved_boundary_requested(arguments):
        return _static_result(
            gate,
            "blocked-incomplete",
            "automatic final transitions are unavailable: the repository has no "
            "controlled external completion oracle and independently controlled publisher",
            (
                "controlled-external-completion-oracle",
                "independently-controlled-publisher",
            ),
            started_source,
            started,
            False,
            _not_run_cleanup(False, "not-needed-before-worker"),
        )
    if os.name != "posix":
        return _static_result(
            gate,
            "error",
            "test-gate supervision requires POSIX process semantics",
            (),
            started_source,
            started,
            False,
            _not_run_cleanup(False, "not-needed-before-worker"),
        )
    owner = secrets.token_hex(32)
    try:
        parent_control, child_control = socket.socketpair()
    except OSError as error:
        return _static_result(
            gate,
            "error",
            "test-gate control channel could not start: " + str(error),
            (),
            started_source,
            started,
            False,
            _not_run_cleanup(False, "not-needed-worker-not-started"),
        )
    environment = os.environ.copy()
    environment[_GIT_NO_REPLACE_ENV] = "1"
    environment[_WORKER_ENV] = "1"
    environment[_OUTER_CONTROL_FD_ENV] = str(child_control.fileno())
    environment[_OWNER_ENV] = owner
    worker_path = Path(__file__).resolve()
    try:
        with _supervisor_termination_scope():
            return _supervise_worker(
                arguments,
                gate,
                started_source,
                started,
                owner,
                parent_control,
                child_control,
                environment,
                worker_path,
            )
    except (KeyboardInterrupt, _SupervisorTermination) as error:
        signal_number = (
            signal.SIGINT
            if isinstance(error, KeyboardInterrupt)
            else error.signal_number
        )
        with _ignore_cleanup_interrupts():
            _kill_worker_token(owner)
        child_control.close()
        parent_control.close()
        return 128 + signal_number


if __name__ == "__main__":
    try:
        if os.environ.get(_WORKER_ENV) == "1":
            if _reserved_boundary_requested(sys.argv[1:]):
                raise RuntimeError("reserved automatic syntax reached the internal worker")
            raise SystemExit(_worker_dispatch(sys.argv[1:]))
        raise SystemExit(_dispatch(sys.argv[1:]))
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(_static_result(_raw_gate(sys.argv[1:]), "error", str(error)))
else:
    # Compatibility API: execute the controller in this module namespace so callers that
    # patch module globals retain the direct and package import behavior of the old module.
    _controller_path = Path(__file__).resolve().with_name("test_gate_controller.py")
    with _controller_path.open("rb") as _controller_stream:
        exec(
            compile(_controller_stream.read(), str(_controller_path), "exec"),
            globals(),
            globals(),
        )
