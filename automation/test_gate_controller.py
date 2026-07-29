#!/usr/bin/env python3
"""Execute a budgeted gate from one immutable repository snapshot."""

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import select
import secrets
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

PROCESS_STARTED = time.monotonic()
EXECUTION_ROOT = Path(
    os.environ.get("AGENTFOLD_GATE_EXECUTION_ROOT", Path(__file__).resolve().parents[1])
).resolve()
REPO = Path(os.environ.get("AGENTFOLD_GATE_SOURCE_REPO", EXECUTION_ROOT)).resolve()
AUTOMATION = EXECUTION_ROOT / "automation"
sys.dont_write_bytecode = True
sys.path.insert(0, str(AUTOMATION))

import run_tests  # noqa: E402
import test_manifest  # noqa: E402

try:
    import test_gate_config  # noqa: E402
except ImportError:  # pragma: no cover - integration supplies the policy module
    test_gate_config = None

try:
    import file_test_budget_task  # noqa: E402
except ImportError:  # pragma: no cover - the report remains complete without mutation
    file_test_budget_task = None


REPORT_SCHEMA = "agentfold.test-gate-report/v4"
RECEIPT_SCHEMA = "agentfold.test-component-receipt/v6"
PUBLICATION_COMMIT_SCHEMA = "agentfold.test-publication-commit/v1"
HANDOFF_SCHEMA = "agentfold.test-gate-bootstrap/v2"
POLICY_FRAME_SCHEMA = "agentfold.test-gate-policy-frame/v1"
TERMINAL_FRAME_SCHEMA = "agentfold.test-gate-broker-decision/v1"
CONTROLLER_CLAIM_SCHEMA = "agentfold.test-gate-controller-claim/v1"
DECISION_SCHEMA = "agentfold.test-gate-decision/v1"
CONTROL_FRAME_MAX_BYTES = 65536
POST_CLAIM_FILING_TIMEOUT_SECONDS = 1.0
DISCOVERY_CEILING_SECONDS = 5.0
COMPOSITE_TEST_PLAN_SCHEMA = "agentfold.composite-test-plan/v2"
TRUSTED_TEST_OVERLAY_ALGORITHM = "candidate-product-with-exact-union-test-namespaces/v3"
EVIDENCE_AUTHORITY = "cooperative-same-interpreter"
CANONICAL_CONFIG = Path("agentfold.toml")
CONTROLLER_CLOSURE_PATHS = (
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
_HANDOFF = None
_handoff_path = os.environ.get("AGENTFOLD_GATE_HANDOFF")
if _handoff_path:
    try:
        with Path(_handoff_path).open("r", encoding="utf-8") as _handoff_stream:
            _HANDOFF = json.load(_handoff_stream)
    except (OSError, ValueError) as _handoff_error:
        raise RuntimeError("test-gate bootstrap handoff is unavailable") from _handoff_error
LOCAL_STATE_DIRECTORIES = frozenset(
    (Path("tmp/test-gate-receipts"), Path("tmp/test-gate-reports"))
)
REPORT_PROJECTIONS = frozenset(
    (
        "tmp/test-gate-reports/latest-routine.json",
        "tmp/test-gate-reports/latest-final.json",
    )
)
_HANDOFF_CLOCK_GETTIME_SOURCE = "clock_gettime:CLOCK_MONOTONIC"
_HANDOFF_OS_TIMES_SOURCE = "os.times:elapsed"
_CONTROL_FD_ENV = "AGENTFOLD_GATE_INNER_CONTROL_FD"
_OWNER_ENV = "AGENTFOLD_GATE_OWNER"
OUTCOME_EXIT = {
    "pass": 0,
    "deferred": 0,
    "not-run": 0,
    "blocked-failed": 1,
    "blocked-incomplete": 1,
    "invalid": 2,
    "error": 2,
}
_STRONG_PROCESS_CONTAINMENT = None


class GateError(RuntimeError):
    """An operational gate failure that must not be mistaken for a test failure."""


def _controller_monotonic_sample():
    """Read the preferred identified monotonic source shared across processes."""
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
                return _HANDOFF_CLOCK_GETTIME_SOURCE, float(value)
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
                return _HANDOFF_OS_TIMES_SOURCE, float(value)
    raise GateError("no supported cross-process monotonic clock is available")


@dataclass(frozen=True)
class ProcessSnapshot:
    rows: tuple
    complete: bool


@dataclass(frozen=True)
class ProcessDiscovery:
    pids: frozenset
    complete: bool


def _relative_execution_path(path):
    try:
        return Path(path).resolve().relative_to(EXECUTION_ROOT).as_posix()
    except (OSError, ValueError) as error:
        raise GateError("repository-local module was loaded outside the execution snapshot") from error


def loaded_module_paths():
    """Return and audit the repository-local modules used by this controller."""
    paths = {"automation/test_gate_controller.py"}
    modules = (run_tests, test_manifest, test_gate_config, file_test_budget_task)
    for module in modules:
        if module is None:
            continue
        path = getattr(module, "__file__", None)
        if not path:
            raise GateError("a controller dependency has no auditable module path")
        paths.add(_relative_execution_path(path))
    for name, module in tuple(sys.modules.items()):
        if not (
            name == "_vendor"
            or name.startswith("_vendor.")
            or name == "automation._vendor"
            or name.startswith("automation._vendor.")
        ):
            continue
        path = getattr(module, "__file__", None)
        if path:
            paths.add(_relative_execution_path(path))
    required = set(CONTROLLER_CLOSURE_PATHS) - {"automation/run_test_gate.py"}
    if not required.issubset(paths):
        raise GateError("controller dependency closure was not fully loaded")
    return tuple(sorted(paths))


def interpreter_identity():
    child = run_tests.child_interpreter_identity()
    if (
        child.get("isolated") != 1
        or child.get("no_site") != 1
        or child.get("ignore_environment") != 1
    ):
        raise GateError("child test interpreter is not fixed to isolated no-site mode")
    return {
        "controller": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "isolated": int(bool(sys.flags.isolated)),
            "no_site": int(bool(sys.flags.no_site)),
            "ignore_environment": int(bool(sys.flags.ignore_environment)),
        },
        "child": child,
    }


def controller_closure():
    """Bind exact staged controller bytes without temporary-path identities."""
    expected = {
        record["path"]: record
        for record in (_HANDOFF or {}).get("controller_closure", ())
    }
    records = []
    for relative in CONTROLLER_CLOSURE_PATHS:
        path = EXECUTION_ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise GateError("controller closure is incomplete")
        mode = expected.get(relative, {}).get(
            "mode", "100755" if path.stat().st_mode & stat.S_IXUSR else "100644"
        )
        if mode not in ("100644", "100755"):
            raise GateError("controller closure contains an invalid Git mode")
        record = {
            "path": relative,
            "mode": mode,
            "sha256": test_manifest.file_digest(path),
        }
        if expected and expected.get(relative) != record:
            raise GateError("controller closure changed after candidate capture")
        records.append(record)
    if expected and set(expected) != set(CONTROLLER_CLOSURE_PATHS):
        raise GateError("controller closure manifest is not canonical")
    value = {
        "records": records,
        "loaded_module_paths": list(loaded_module_paths()),
        "interpreter_identity": interpreter_identity(),
    }
    value["digest"] = test_manifest.canonical_digest(value)
    return value


def frozen_index_identity(path, base_revision):
    path = Path(path)
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise GateError("authoritative frozen index is unsafe")
    candidate = test_manifest.staged_candidate(
        REPO, path, base_revision=base_revision
    )
    return {
        "file_sha256": test_manifest.file_digest(path),
        "semantic_sha256": candidate.closure_digest,
        "mode": stat.S_IMODE(metadata.st_mode),
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
    }


def frozen_index_matches(path, base_revision, expected):
    try:
        return frozen_index_identity(path, base_revision) == expected
    except (GateError, OSError, test_manifest.ManifestError):
        return False


def seal_authoritative_frozen_index(path, base_revision):
    path = Path(path)
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise GateError("authoritative frozen index is unsafe")
    path.chmod(0o400)
    identity = frozen_index_identity(path, base_revision)
    if identity["mode"] != 0o400:
        raise GateError("authoritative frozen index is not read-only")
    return identity


def copy_component_index(source, destination, base_revision):
    source = Path(source)
    destination = Path(destination)
    if source.is_symlink() or not source.is_file():
        raise GateError("authoritative frozen index is unsafe")
    with source.open("rb") as reader, destination.open("xb") as writer:
        shutil.copyfileobj(reader, writer)
        writer.flush()
        os.fsync(writer.fileno())
    destination.chmod(0o600)
    return frozen_index_identity(destination, base_revision)


def validate_bootstrap_handoff():
    if _HANDOFF is None:
        return controller_closure()
    if (
        _HANDOFF.get("schema") != HANDOFF_SCHEMA
        or Path(_HANDOFF.get("source_repository", "")).resolve() != REPO
        or Path(_HANDOFF.get("execution_root", "")).resolve() != EXECUTION_ROOT
    ):
        raise GateError("test-gate bootstrap handoff is invalid")
    gate_interval_started()
    frozen_index = Path(_HANDOFF.get("frozen_index", "")).resolve()
    if frozen_index.parent != EXECUTION_ROOT.parent:
        raise GateError("test-gate bootstrap frozen index is outside its snapshot")
    identity = frozen_index_identity(
        frozen_index, _HANDOFF.get("base_revision", "")
    )
    if (
        identity["mode"] != 0o400
        or identity["file_sha256"] != _HANDOFF.get("frozen_index_sha256")
        or identity["semantic_sha256"]
        != _HANDOFF.get("index_semantic_sha256")
    ):
        raise GateError("test-gate bootstrap frozen index changed after capture")
    return controller_closure()


def gate_interval_bounds():
    """Map supervisor clock values into this process's monotonic epoch."""
    if _HANDOFF is None:
        return PROCESS_STARTED, None
    source = _HANDOFF.get("started_monotonic_source")
    value = _HANDOFF.get("started_monotonic")
    deadline = _HANDOFF.get("absolute_deadline_monotonic")
    selected_source, now = _controller_monotonic_sample()
    if source != selected_source:
        raise GateError("test-gate bootstrap monotonic source mismatch")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
        or value > now
        or isinstance(deadline, bool)
        or not isinstance(deadline, (int, float))
        or not math.isfinite(deadline)
        or deadline <= value
    ):
        raise GateError("test-gate bootstrap monotonic bounds are invalid")
    bootstrap_elapsed = now - float(value)
    local_now = time.monotonic()
    return (
        local_now - bootstrap_elapsed,
        local_now + (float(deadline) - now),
    )


def gate_interval_started():
    return gate_interval_bounds()[0]


def _require_work_time(deadline, phase):
    if deadline is not None and time.monotonic() >= deadline:
        raise GateError("configured absolute deadline expired during " + phase)


def _bounded_json_call(call, deadline):
    """Run one potentially blocking local check in a killable helper process."""
    if deadline is None:
        return True, call()
    if os.name != "posix" or time.monotonic() >= deadline:
        return False, None
    read_fd, write_fd = os.pipe()
    try:
        pid = os.fork()
    except BaseException:
        os.close(read_fd)
        os.close(write_fd)
        raise
    if pid == 0:  # pragma: no cover - the parent verifies the framed result
        os.close(read_fd)
        try:
            try:
                os.setsid()
            except OSError:
                pass
            raw_control_fd = os.environ.get(_CONTROL_FD_ENV, "")
            if raw_control_fd.isdigit() and int(raw_control_fd) != write_fd:
                try:
                    os.close(int(raw_control_fd))
                except OSError:
                    pass
            value = call()
            payload = json.dumps(
                {"ok": True, "value": value},
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            if len(payload) > CONTROL_FRAME_MAX_BYTES:
                raise ValueError("bounded helper result is oversized")
            data = memoryview(struct.pack("!I", len(payload)) + payload)
            while data:
                written = os.write(write_fd, data)
                if written <= 0:
                    raise OSError("bounded helper result could not be sent")
                data = data[written:]
        except BaseException:
            pass
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    data = bytearray()
    expected = None
    completed = False
    value = None
    try:
        while expected is None or len(data) < expected + 4:
            now = time.monotonic()
            if now >= deadline:
                break
            readable, _, _ = select.select((read_fd,), (), (), deadline - now)
            if not readable or time.monotonic() >= deadline:
                break
            chunk = os.read(read_fd, 4096)
            if not chunk:
                break
            data.extend(chunk)
            if expected is None and len(data) >= 4:
                expected = struct.unpack("!I", data[:4])[0]
                if expected <= 0 or expected > CONTROL_FRAME_MAX_BYTES:
                    break
        if expected is not None and len(data) == expected + 4:
            frame = json.loads(bytes(data[4:]).decode("utf-8"))
            if isinstance(frame, dict) and frame.get("ok") is True:
                completed = True
                value = frame.get("value")
    except (OSError, ValueError, UnicodeDecodeError):
        completed = False
        value = None
    finally:
        os.close(read_fd)
        try:
            child, _status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            child = pid
        if child == 0:
            try:
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            # Reaping is deliberately nonblocking here.  A killed helper may remain
            # a zombie until the controller exits, but terminalization never waits
            # past its own deadline merely to collect it.
            try:
                os.waitpid(pid, os.WNOHANG)
            except (ChildProcessError, ProcessLookupError):
                pass
    return completed, value


@dataclass
class ComponentResult:
    component_id: str
    outcome: str
    evidence: str
    duration_seconds: float
    command: tuple
    detail: str = ""

    def as_dict(self):
        value = asdict(self)
        value["command"] = list(self.command)
        value["duration_seconds"] = round(self.duration_seconds, 6)
        return value


def parse_arguments(arguments):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("gate", choices=("routine", "final"))
    parser.add_argument(
        "--staged",
        action="store_true",
        help="bind routine or explicit final prewarming to an immutable Git index copy",
    )
    final_trigger = parser.add_mutually_exclusive_group()
    final_trigger.add_argument(
        "--explicit", action="store_true", help="explicitly request the final gate"
    )
    final_trigger.add_argument(
        "--at-transition", metavar="NAME", help="run at a named final transition"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CANONICAL_CONFIG,
        help="canonical repository policy path (agentfold.toml)",
    )
    parser.add_argument("--base-revision", help="immutable final range base")
    parser.add_argument("--head-revision", help="pull-request head bound to a merge candidate")
    parser.add_argument("--candidate-revision", help="immutable final range candidate")
    parser.add_argument("--branch", help="task branch bound to final admission")
    parser.add_argument("--displaced-tip", help="prior tip for synchronize admission")
    parser.add_argument(
        "--provider-hard",
        action="store_true",
        help="request the reserved provider-hard boundary (unavailable without an external oracle)",
    )
    options = parser.parse_args(arguments)
    if options.gate == "routine" and not options.staged:
        parser.error("the routine gate requires --staged")
    if options.gate == "routine" and (
        options.explicit or options.at_transition or options.provider_hard
    ):
        parser.error("final trigger options apply only to the final gate")
    if options.gate == "routine" and any(
        (
            options.base_revision,
            options.head_revision,
            options.candidate_revision,
            options.branch,
            options.displaced_tip,
        )
    ):
        parser.error("revision range options apply only to the final gate")
    if options.gate == "final" and options.staged and not options.explicit:
        parser.error("a staged final gate requires --explicit")
    if options.gate == "final" and options.staged and any(
        (
            options.at_transition,
            options.base_revision,
            options.head_revision,
            options.candidate_revision,
            options.branch,
            options.displaced_tip,
        )
    ):
        parser.error("a staged final gate cannot name a revision range or transition")
    if options.provider_hard and (
        options.gate != "final"
        or options.explicit
        or options.staged
        or options.at_transition != "pull-request"
    ):
        parser.error(
            "--provider-hard requires final --at-transition pull-request and an exact range"
        )
    if options.at_transition and not (
        options.base_revision
        and options.head_revision
        and options.candidate_revision
        and options.branch
    ):
        parser.error(
            "named final transitions require --base-revision, --head-revision, "
            "--candidate-revision, and --branch"
        )
    if options.config != CANONICAL_CONFIG:
        parser.error("--config cannot select a non-canonical policy; use agentfold.toml")
    return options


def _policy_digest(policy):
    canonical = getattr(test_gate_config, "canonical_policy_digest", None)
    if canonical is not None:
        return canonical(policy)
    digest = getattr(policy, "digest", None)
    if not digest:
        raise GateError("loaded test policy has no canonical digest")
    return digest


def load_candidate_policy(candidate_root, relative_config, scratch_root, base_revision):
    """Load a downgrade-resistant base/candidate policy union when possible."""
    if test_gate_config is None:
        raise GateError("automation/test_gate_config.py is unavailable")
    if Path(relative_config) != CANONICAL_CONFIG:
        raise GateError("the test-gate policy must be loaded from canonical agentfold.toml")
    candidate_path = candidate_root / CANONICAL_CONFIG
    if not candidate_path.is_file() or candidate_path.is_symlink():
        raise GateError(f"candidate policy is unavailable: {relative_config}")
    base_path = scratch_root / "base-agentfold.toml"
    base = subprocess.run(
        ["git", "show", f"{base_revision}:{CANONICAL_CONFIG.as_posix()}"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if base.returncode != 0:
        presence = subprocess.run(
            ["git", "ls-tree", "-z", "--name-only", base_revision, "--", CANONICAL_CONFIG.as_posix()],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if presence.returncode != 0 or presence.stdout:
            raise GateError("base-pinned policy could not be read at canonical agentfold.toml")
        policy = test_gate_config.load_policy(candidate_path)
        return policy, _policy_digest(policy)
    base_path.write_bytes(base.stdout)
    union_loader = getattr(test_gate_config, "load_policy_union", None)
    if union_loader is None:
        raise GateError("downgrade-resistant policy union support is unavailable")
    policy = union_loader(base_path, candidate_path)
    return policy, _policy_digest(policy)


def _protocol_parser_records(closure):
    wanted = {
        "automation/test_gate_config.py",
        "automation/_vendor/__init__.py",
        "automation/_vendor/tomli/__init__.py",
        "automation/_vendor/tomli/_parser.py",
        "automation/_vendor/tomli/_re.py",
        "automation/_vendor/tomli/_types.py",
    }
    return [
        {"path": record["path"], "mode": record["mode"], "sha256": record["sha256"]}
        for record in closure
        if record["path"] in wanted
    ]


def validate_policy_frame(policy, policy_digest, candidate_root, base_revision, gate):
    """Recompute discovery claims from the same frozen candidate and parser bytes."""
    if _HANDOFF is None:
        return None
    frame = _HANDOFF.get("policy_frame")
    if not isinstance(frame, dict) or frame.get("schema") != POLICY_FRAME_SCHEMA:
        raise GateError("test-gate policy frame is unavailable")
    unsigned = dict(frame)
    frame_digest = unsigned.pop("frame_digest", None)
    if frame_digest != test_manifest.canonical_digest(unsigned):
        raise GateError("test-gate policy frame digest is invalid")
    candidate_path = candidate_root / CANONICAL_CONFIG
    if candidate_path.is_symlink() or not candidate_path.is_file():
        raise GateError("candidate policy is unavailable: agentfold.toml")
    base = subprocess.run(
        ["git", "show", "{}:{}".format(base_revision, CANONICAL_CONFIG.as_posix())],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if base.returncode:
        raise GateError("base-pinned policy could not be revalidated")
    base_digest = hashlib.sha256(base.stdout).hexdigest()
    closure = _HANDOFF.get("controller_closure", ())
    parser_records = _protocol_parser_records(closure)
    budget = _budget_for(gate, policy)
    routine_budget = _budget_for("routine", policy)
    final_budget = _budget_for("final", policy)
    expected = {
        "gate_id": gate,
        "target_seconds": float(budget.target_seconds),
        "maximum_seconds": float(budget.maximum_seconds),
        "budgets": {
            "routine": {
                "target_seconds": float(routine_budget.target_seconds),
                "maximum_seconds": float(routine_budget.maximum_seconds),
            },
            "final": {
                "target_seconds": float(final_budget.target_seconds),
                "maximum_seconds": float(final_budget.maximum_seconds),
            },
        },
        "discovery_ceiling_seconds": DISCOVERY_CEILING_SECONDS,
        "policy_digest": policy_digest,
        "base_config_sha256": base_digest,
        "candidate_config_sha256": test_manifest.file_digest(candidate_path),
        "candidate_parser_closure_digest": test_manifest.canonical_digest(parser_records),
        "authoritative_index": {
            "file_sha256": _HANDOFF.get("frozen_index_sha256"),
            "semantic_sha256": _HANDOFF.get("index_semantic_sha256"),
        },
        "launcher": {
            "path": "automation/run_test_gate.py",
            "sha256": next(
                (
                    record["sha256"]
                    for record in closure
                    if record["path"] == "automation/run_test_gate.py"
                ),
                None,
            ),
        },
        "candidate_kind": _HANDOFF.get("candidate_kind"),
        "base_revision": _HANDOFF.get("base_revision"),
        "candidate_revision": _HANDOFF.get("candidate_revision"),
    }
    for name, value in expected.items():
        if frame.get(name) != value:
            raise GateError("test-gate policy frame disagrees with frozen " + name)
    return {
        "policy_frame_schema": frame["schema"],
        "policy_frame_digest": frame_digest,
        "discovery_ceiling_seconds": frame["discovery_ceiling_seconds"],
        "target_seconds": frame["target_seconds"],
        "maximum_seconds": frame["maximum_seconds"],
        "budgets": frame["budgets"],
        "policy_digest": frame["policy_digest"],
        "base_config_sha256": frame["base_config_sha256"],
        "candidate_config_sha256": frame["candidate_config_sha256"],
        "trusted_parser_closure_digest": frame["trusted_parser_closure_digest"],
        "candidate_parser_closure_digest": frame["candidate_parser_closure_digest"],
        "authoritative_index": frame["authoritative_index"],
        "launcher": frame["launcher"],
    }


def _resolve_commit(revision):
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    oid = result.stdout.strip()
    if result.returncode or not oid:
        raise GateError(f"final revision is unavailable: {revision}")
    return oid


def capture_revision_candidate(options, scratch_root):
    """Materialize an immutable committed range for final verification."""
    if bool(options.base_revision) != bool(options.candidate_revision):
        raise GateError("final --base-revision and --candidate-revision are required together")
    if not options.base_revision:
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if status.returncode or status.stdout:
            raise GateError(
                "explicit final without a revision range requires a clean checkout; "
                "commit the candidate or pass --base-revision and --candidate-revision"
            )
    base_revision = _resolve_commit(options.base_revision or "HEAD^")
    candidate_revision = _resolve_commit(options.candidate_revision or "HEAD")
    head_revision = (
        _resolve_commit(options.head_revision) if options.head_revision else None
    )
    if head_revision is not None:
        parents = subprocess.run(
            ["git", "rev-list", "--parents", "-n", "1", candidate_revision],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        parent_oids = tuple(parents.stdout.strip().split()[1:])
        if parents.returncode or parent_oids != (base_revision, head_revision):
            raise GateError(
                "final pull-request candidate is not the declared base/head synthetic merge"
            )
    frozen_index = scratch_root / "candidate.index"
    environment = os.environ.copy()
    environment["GIT_INDEX_FILE"] = str(frozen_index)
    result = subprocess.run(
        ["git", "read-tree", candidate_revision],
        cwd=REPO,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise GateError("could not create the immutable final candidate index")
    candidate = test_manifest.staged_candidate(
        REPO,
        frozen_index,
        base_revision=base_revision,
        candidate_revision=candidate_revision,
        kind="revision-range",
    )
    candidate_root = scratch_root / "candidate"
    tested_view = _semantic_tree_manifest(
        test_manifest.materialize_staged_candidate(
            REPO, frozen_index, candidate_root
        )
    )

    def unchanged():
        return (
            _resolve_commit(base_revision) == base_revision
            and _resolve_commit(candidate_revision) == candidate_revision
        )

    return candidate, tested_view, candidate_root, unchanged


def capture_candidate(options, scratch_root):
    """Capture one immutable candidate and return its manifest, view, and drift check."""
    if _HANDOFF is not None:
        frozen_index = Path(_HANDOFF["frozen_index"]).resolve()
        kind = _HANDOFF["candidate_kind"]
        if (
            (options.staged and kind != "staged-index")
            or (not options.staged and kind != "revision-range")
        ):
            raise GateError("bootstrap candidate kind does not match the invocation")
        candidate = test_manifest.staged_candidate(
            REPO,
            frozen_index,
            base_revision=_HANDOFF["base_revision"],
            candidate_revision=_HANDOFF["candidate_revision"],
            kind=kind,
        )
        if candidate.closure_digest != _HANDOFF.get("index_semantic_sha256"):
            raise GateError("bootstrap index closure changed after capture")
        tested_view = _semantic_tree_manifest(
            test_manifest.tree_manifest(EXECUTION_ROOT)
        )
        initial_view_digest = tested_view["digest"]
        initial_controller_digest = controller_closure()["digest"]
        initial_frozen_index_identity = frozen_index_identity(
            frozen_index, candidate.base_revision
        )

        def unchanged():
            try:
                if not frozen_index_matches(
                    frozen_index,
                    candidate.base_revision,
                    initial_frozen_index_identity,
                ):
                    return False
                if _semantic_tree_manifest(
                    test_manifest.tree_manifest(EXECUTION_ROOT)
                )["digest"] != initial_view_digest:
                    return False
                if controller_closure()["digest"] != initial_controller_digest:
                    return False
                if kind == "revision-range":
                    return (
                        _resolve_commit(candidate.base_revision) == candidate.base_revision
                        and _resolve_commit(candidate.candidate_revision)
                        == candidate.candidate_revision
                    )
                live = test_manifest.staged_candidate(
                    REPO,
                    test_manifest.selected_index_path(REPO),
                    base_revision=candidate.base_revision,
                )
                return live.digest == candidate.digest
            except (GateError, OSError, test_manifest.ManifestError):
                return False

        return candidate, tested_view, EXECUTION_ROOT, unchanged
    if options.gate == "final" and not options.staged:
        return capture_revision_candidate(options, scratch_root)
    candidate_root = scratch_root / "candidate"
    if options.staged:
        frozen_index = scratch_root / "candidate.index"
        test_manifest.copy_staged_index(REPO, frozen_index)
        candidate = test_manifest.staged_candidate(REPO, frozen_index)
        tested_view = _semantic_tree_manifest(
            test_manifest.materialize_staged_candidate(
                REPO, frozen_index, candidate_root
            )
        )

        def unchanged():
            return test_manifest.live_index_matches(
                REPO, candidate.source_fingerprint, candidate.base_revision
            )

        return candidate, tested_view, candidate_root, unchanged

    raise GateError("routine candidate must be staged")


def classify_candidate(paths, policy):
    classifier = getattr(test_gate_config, "classify_paths", None)
    if classifier is None:
        raise GateError("test policy module does not expose classify_paths")
    return classifier(paths, policy)


def admission_commands(options, candidate, candidate_root=REPO):
    """Bind admission and reconciliation to the same captured candidate shape."""
    automation = AUTOMATION if options.provider_hard else Path(candidate_root) / "automation"
    if candidate.kind == "staged-index":
        return (
            (
                "core-scope",
                [sys.executable, str(automation / "check_core_scope.py"), "--staged"],
            ),
            (
                "reconcile",
                [sys.executable, str(automation / "reconcile/reconcile.py"), "--check"],
            ),
        )
    branch = options.branch
    if not branch:
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    if not branch:
        raise GateError("final range admission requires --branch in a detached checkout")
    change_range = f"{candidate.base_revision}...{candidate.candidate_revision}"
    core = [
        sys.executable,
        str(automation / "check_core_scope.py"),
        "--range",
        change_range,
        "--branch",
        branch,
    ]
    reconcile = [
        sys.executable,
        str(automation / "reconcile/reconcile.py"),
        "--check",
        "--branch",
        branch,
        "--range",
        change_range,
    ]
    if options.at_transition:
        transition = (
            "merge" if options.at_transition == "pull-request" else options.at_transition
        )
        reconcile.extend(("--at-transition", transition))
    if options.displaced_tip:
        reconcile.extend(("--displaced-tip", _resolve_commit(options.displaced_tip)))
    return (("core-scope", core), ("reconcile", reconcile))


def candidate_git_environment(candidate_root, frozen_index):
    """Expose original history to checks while freezing all candidate-visible bytes."""
    result = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    git_directory = result.stdout.strip()
    if result.returncode or not git_directory:
        raise GateError("could not resolve repository metadata for candidate checks")
    return {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_DIR": git_directory,
        "GIT_WORK_TREE": str(Path(candidate_root).resolve()),
        "GIT_INDEX_FILE": str(Path(frozen_index).resolve()),
    }


def _all_relative_tests(candidate_root):
    return tuple(
        test.relative_to(candidate_root).as_posix()
        for test in run_tests.repository_test_files(candidate_root)
    )


def _canonical_git_mode(mode):
    if mode in ("100644", "100755"):
        return mode
    if not isinstance(mode, int):
        raise GateError("tested-view file mode is not a regular Git mode")
    return "100755" if mode & 0o111 else "100644"


def _semantic_tree_manifest(value):
    """Normalize seal chmods to the regular-file modes represented by Git."""
    records = []
    for original in value["records"]:
        record = dict(original)
        if record.get("kind") == "file":
            record["mode"] = _canonical_git_mode(record.get("mode"))
        records.append(record)
    records = tuple(sorted(records, key=lambda record: record["path"]))
    return {
        "schema": value["schema"],
        "digest": test_manifest.canonical_digest(records),
        "paths": [record["path"] for record in records],
        "records": records,
    }


def _materialize_revision(revision, scratch_root, name):
    """Materialize exact regular-file bytes for one trusted Git revision."""
    index = scratch_root / f"{name}.index"
    environment = os.environ.copy()
    environment["GIT_INDEX_FILE"] = str(index)
    result = subprocess.run(
        ["git", "read-tree", revision],
        cwd=REPO,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise GateError(f"could not create the immutable {name} index")
    root = scratch_root / name
    manifest = _semantic_tree_manifest(
        test_manifest.materialize_staged_candidate(REPO, index, root)
    )
    return root, manifest


def _records_below(manifest, namespaces):
    prefixes = tuple(namespace + "/" for namespace in namespaces)
    return tuple(
        record
        for record in manifest["records"]
        if record["path"] in namespaces or record["path"].startswith(prefixes)
    )


def _support_records_below(manifest, namespaces, test_paths):
    """Return exact regular non-test files below base-pinned test namespaces."""
    tests = set(test_paths)
    return tuple(
        record
        for record in _records_below(manifest, namespaces)
        if record.get("kind") == "file" and record["path"] not in tests
    )


def _file_record(root, relative):
    path = Path(root) / relative
    if not path.is_file() or path.is_symlink():
        raise GateError(f"declared test is unavailable or unsafe: {relative}")
    metadata = path.stat()
    return {
        "path": relative,
        "mode": _canonical_git_mode(stat.S_IMODE(metadata.st_mode)),
        "sha256": test_manifest.file_digest(path),
    }


def _normalized_namespace_roots(namespaces):
    ordered = tuple(sorted(set(namespaces), key=lambda value: (len(Path(value).parts), value)))
    roots = []
    for namespace in ordered:
        if any(Path(root) == Path(namespace) or Path(root) in Path(namespace).parents for root in roots):
            continue
        roots.append(namespace)
    return tuple(sorted(roots))


def composite_test_plan(candidate, candidate_root, candidate_view, scratch_root):
    """Build a trusted-base test floor plus candidate supplemental-test plan.

    The candidate copy first loses the normalized union of base and candidate test
    namespaces, then receives only exact base namespaces. Product paths elsewhere
    retain exact candidate bytes and candidate-only namespaces remain supplemental.
    """
    if not candidate.base_revision:
        raise GateError("composite full testing requires a base-pinned revision")
    candidate_view = _semantic_tree_manifest(candidate_view)
    base_root, base_view = _materialize_revision(
        candidate.base_revision, scratch_root, "trusted-base"
    )
    base_tests = _all_relative_tests(base_root)
    if not base_tests:
        raise GateError("base-pinned revision contains no discoverable repository tests")
    candidate_tests = _all_relative_tests(candidate_root)
    base_namespaces = tuple(sorted({Path(test).parent.as_posix() for test in base_tests}))
    candidate_namespaces = tuple(
        sorted({Path(test).parent.as_posix() for test in candidate_tests})
    )
    raw_namespaces = tuple(sorted(set(base_namespaces).union(candidate_namespaces)))
    namespaces = _normalized_namespace_roots(raw_namespaces)
    base_namespace_roots = _normalized_namespace_roots(base_namespaces)
    if not base_namespaces or any(
        namespace in ("", ".")
        or Path(namespace).is_absolute()
        or ".." in Path(namespace).parts
        or any(part.casefold() == ".git" for part in Path(namespace).parts)
        for namespace in raw_namespaces
    ):
        raise GateError("base-pinned test namespace topology is unsafe")

    floor_root = scratch_root / "trusted-floor"
    shutil.copytree(str(candidate_root), str(floor_root), symlinks=True)
    for namespace in namespaces:
        destination = floor_root / namespace
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(str(destination))
            else:
                destination.unlink()
    for namespace in base_namespace_roots:
        base_namespace = base_root / namespace
        if not base_namespace.is_dir() or base_namespace.is_symlink():
            raise GateError(f"base-pinned test namespace is unavailable: {namespace}")
        destination = floor_root / namespace
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(base_namespace), str(destination), symlinks=True)
    floor_view = _semantic_tree_manifest(test_manifest.tree_manifest(floor_root))
    floor_tests = _all_relative_tests(floor_root)
    if floor_tests != base_tests:
        raise GateError("base-pinned test floor changed during exact overlay")

    base_test_records = {
        path: _file_record(base_root, path) for path in base_tests
    }
    candidate_test_records = {
        path: _file_record(candidate_root, path) for path in candidate_tests
    }
    base_namespace_records = _records_below(base_view, base_namespaces)
    candidate_namespace_records = _records_below(candidate_view, candidate_namespaces)
    support_changed_namespaces = tuple(
        sorted(
            namespace
            for namespace in base_namespaces
            if _support_records_below(base_view, (namespace,), base_tests)
            != _support_records_below(candidate_view, (namespace,), candidate_tests)
        )
    )
    supplemental_tests = tuple(
        sorted(
            path
            for path, record in candidate_test_records.items()
            if Path(path).parent.as_posix() not in base_namespaces
            or base_test_records.get(path) != record
            or any(
                Path(namespace) in Path(path).parents
                for namespace in support_changed_namespaces
            )
        )
    )
    supplemental_namespaces = tuple(
        sorted({Path(path).parent.as_posix() for path in supplemental_tests})
    )
    supplemental_records = _records_below(
        candidate_view, supplemental_namespaces
    )
    identity = {
        "schema": COMPOSITE_TEST_PLAN_SCHEMA,
        "trusted_base_revision": candidate.base_revision,
        "overlay_algorithm": TRUSTED_TEST_OVERLAY_ALGORITHM,
        "base_test_namespaces": list(base_namespaces),
        "candidate_test_namespaces": list(candidate_namespaces),
        "base_namespace_roots": list(base_namespace_roots),
        "overlay_namespaces": list(namespaces),
        "trusted_floor_tests": list(floor_tests),
        "trusted_floor_records": list(base_namespace_records),
        "trusted_floor_view_digest": floor_view["digest"],
        "candidate_test_records": list(candidate_namespace_records),
        "support_changed_namespaces": list(support_changed_namespaces),
        "supplemental_tests": list(supplemental_tests),
        "supplemental_records": list(supplemental_records),
        "candidate_tested_view_digest": candidate_view["digest"],
    }
    identity["digest"] = test_manifest.canonical_digest(identity)
    return {
        "identity": identity,
        "floor_root": floor_root,
        "floor_view": floor_view,
        "floor_tests": floor_tests,
        "supplemental_root": candidate_root,
        "supplemental_tests": supplemental_tests,
    }


def _validated_service_dependencies(all_tests, policy):
    """Bind configured dependency names to discovered service test namespaces."""
    dependencies = {
        owner: tuple(downstream)
        for owner, downstream in getattr(policy, "service_dependencies", ())
    }
    discovered = {
        parts[1]
        for test in all_tests
        for parts in (Path(test).parts,)
        if len(parts) >= 4 and parts[0] == "services" and parts[2] == "tests"
    }
    unknown_owners = tuple(sorted(set(dependencies).difference(discovered)))
    unknown_targets = tuple(
        sorted(
            {
                downstream
                for targets in dependencies.values()
                for downstream in targets
            }.difference(discovered)
        )
    )
    if unknown_owners or unknown_targets:
        details = []
        if unknown_owners:
            details.append("unknown owner(s): " + ", ".join(unknown_owners))
        if unknown_targets:
            details.append(
                "unknown downstream target(s): " + ", ".join(unknown_targets)
            )
        raise GateError(
            "routine test planning configuration is invalid ({}); each configured "
            "service must have a discovered test under services/<name>/tests/, or "
            "the name must be corrected in testing.routine.service_dependencies".format(
                "; ".join(details)
            )
        )
    return dependencies


def _service_dependency_closure(service, dependencies):
    selected = set()
    pending = [service]
    while pending:
        current = pending.pop()
        if current in selected:
            continue
        selected.add(current)
        pending.extend(dependencies.get(current, ()))
    return tuple(sorted(selected))


def routine_test_manifest(changed_paths, all_tests, policy):
    """Map generic service ownership and configured dependencies to routine tests."""
    all_set = set(all_tests)
    dependencies = _validated_service_dependencies(all_tests, policy)
    selected = set()
    for changed in changed_paths:
        parts = Path(changed).parts
        if len(parts) >= 2 and parts[0] == "services":
            for service in _service_dependency_closure(parts[1], dependencies):
                prefix = f"services/{service}/tests/"
                selected.update(test for test in all_set if test.startswith(prefix))
        elif len(parts) == 2 and parts[0] == "automation" and parts[1].endswith(".py"):
            stem = Path(parts[1]).stem
            direct = f"automation/tests/test_{stem}.py"
            if direct in all_set:
                selected.add(direct)
        elif len(parts) >= 3 and parts[:2] == ("automation", "tests"):
            candidate = "/".join(parts)
            if candidate in all_set:
                selected.add(candidate)
    selected = tuple(sorted(selected))
    return selected, tuple(sorted(all_set.difference(selected)))


def _budget_for(gate, policy):
    if gate == "routine":
        return policy.routine
    final = getattr(policy, "final", None)
    if final is not None:
        return getattr(final, "budget", final)
    return test_gate_config.GateBudget(
        policy.final_target_seconds, policy.final_maximum_seconds
    )


def _final_disposition(options, policy):
    if options.gate != "final":
        return None
    final = getattr(policy, "final", None)
    if final is None:
        hard_triggers = tuple(policy.hard_triggers)
        mode = "hard" if hard_triggers else "manual"
        trigger = hard_triggers[0] if len(hard_triggers) == 1 else None
    else:
        mode = final.mode
        trigger = final.trigger
    if options.explicit:
        return None
    if options.at_transition:
        return (
            "blocked-incomplete",
            "automatic final transitions are unavailable: install a controlled "
            "external completion oracle and independently controlled publisher",
        )
    return (
        "not-run",
        "final verification requires --explicit or --at-transition NAME",
    )


def _portable_process_snapshot(deadline):
    """Return one bounded portable snapshot and whether it is authoritative."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return ProcessSnapshot((), False)
    try:
        result = subprocess.run(
            ["ps", "eww", "-axo", "pid=,ppid=,uid=,command="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=min(0.3, remaining),
        )
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", "replace")
        return ProcessSnapshot(_portable_process_rows(output)[0], False)
    except OSError:
        return ProcessSnapshot((), False)
    rows, parsed = _portable_process_rows(result.stdout)
    return ProcessSnapshot(rows, result.returncode == 0 and parsed)


def _portable_process_rows(output):
    rows = []
    complete = True
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = line.split(None, 3)
        if len(fields) != 4:
            complete = False
            continue
        try:
            rows.append((int(fields[0]), int(fields[1]), int(fields[2]), fields[3]))
        except ValueError:
            complete = False
            continue
    return tuple(rows), complete


def _descendant_pids(root_pid, deadline, portable_snapshot=None):
    """Snapshot direct and indirect descendants before the root can reparent them."""
    children = {}
    complete = True
    proc = Path("/proc")
    if sys.platform.startswith("linux") and proc.is_dir():
        if time.monotonic() >= deadline:
            return ProcessDiscovery(frozenset(), False)
        try:
            entries = tuple(proc.iterdir())
        except OSError:
            return ProcessDiscovery(frozenset(), False)
        for entry in entries:
            if not entry.name.isdigit():
                continue
            if time.monotonic() >= deadline:
                complete = False
                break
            try:
                fields = (entry / "stat").read_text().rsplit(") ", 1)[1].split()
                parent = int(fields[1])
                pid = int(entry.name)
            except (FileNotFoundError, ProcessLookupError):
                continue
            except (IndexError, OSError, ValueError):
                complete = False
                continue
            children.setdefault(parent, []).append(pid)
    else:
        if portable_snapshot is None:
            portable_snapshot = _portable_process_snapshot(deadline)
        complete = portable_snapshot.complete
        for pid, parent, _uid, _command in portable_snapshot.rows:
            children.setdefault(parent, []).append(pid)
    descendants = set()
    pending = [root_pid]
    while pending:
        parent = pending.pop()
        for child in children.get(parent, ()):
            if child not in descendants:
                descendants.add(child)
                pending.append(child)
    return ProcessDiscovery(frozenset(descendants), complete)


PROCESS_TOKEN_ENV = "AGENTFOLD_GATE_PROCESS_TOKEN"
SAFE_ENVIRONMENT_NAMES = frozenset(
    (
        "CI",
        "GITHUB_ACTIONS",
        "GIT_AUTHOR_EMAIL",
        "GIT_AUTHOR_NAME",
        "GIT_COMMITTER_EMAIL",
        "GIT_COMMITTER_NAME",
        "LANG",
        "LC_ALL",
        "PATH",
        "RUNNER_ARCH",
        "RUNNER_OS",
        "TEMP",
        "TMP",
        "TMPDIR",
        "TZ",
        _OWNER_ENV,
    )
)
FIXED_PYTHON_ENVIRONMENT = {"PYTHONDONTWRITEBYTECODE": "1"}
INTERNAL_COMPONENT_ENVIRONMENT_NAMES = frozenset(
    (
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
    )
)


def _canonical_git_hook_path(source, path):
    """Remove only Git's verified, hook-only exec-path prepend."""
    git_exec_path = source.get("GIT_EXEC_PATH")
    git_index_file = source.get("GIT_INDEX_FILE")
    git_prefix = source.get("GIT_PREFIX")
    if (
        not path
        or not git_exec_path
        or not os.path.isabs(git_exec_path)
        or not git_index_file
        or git_prefix is None
    ):
        return path
    parts = path.split(os.pathsep)
    if not parts or os.path.normpath(parts[0]) != os.path.normpath(git_exec_path):
        return path
    remaining = os.pathsep.join(parts[1:])
    git_binary = shutil.which("git", path=remaining)
    if not git_binary:
        return path
    probe_environment = dict(source)
    probe_environment.pop("GIT_EXEC_PATH", None)
    probe_environment.pop("GIT_INDEX_FILE", None)
    probe_environment["PATH"] = remaining
    probe_environment["GIT_CONFIG_GLOBAL"] = os.devnull
    probe_environment["GIT_CONFIG_NOSYSTEM"] = "1"
    try:
        configured = subprocess.run(
            [git_binary, "--exec-path"],
            env=probe_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
        )
        canonical_index = subprocess.run(
            [git_binary, "rev-parse", "--git-path", "index"],
            cwd=REPO,
            env=probe_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return path
    if configured.returncode != 0 or os.path.normpath(
        configured.stdout.strip()
    ) != os.path.normpath(git_exec_path):
        return path
    if canonical_index.returncode != 0:
        return path
    supplied_index = Path(git_index_file)
    expected_index = Path(canonical_index.stdout.strip())
    if not supplied_index.is_absolute():
        supplied_index = REPO / supplied_index
    if not expected_index.is_absolute():
        expected_index = REPO / expected_index
    if supplied_index.resolve() != expected_index.resolve():
        return path
    return remaining


def safe_process_environment(source=None):
    """Pass only non-secret execution context into candidate-controlled components."""
    source = os.environ if source is None else source
    environment = {
        name: value
        for name, value in source.items()
        if name in SAFE_ENVIRONMENT_NAMES
    }
    environment.update(FIXED_PYTHON_ENVIRONMENT)
    if "PATH" in environment:
        environment["PATH"] = _canonical_git_hook_path(source, environment["PATH"])
    return environment


def strong_process_containment_available():
    """Enable Linux orphan adoption or report that strong containment is absent."""
    global _STRONG_PROCESS_CONTAINMENT
    if _STRONG_PROCESS_CONTAINMENT is not None:
        return _STRONG_PROCESS_CONTAINMENT
    if not sys.platform.startswith("linux") or not Path("/proc/self/task").is_dir():
        _STRONG_PROCESS_CONTAINMENT = False
        return False
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        configured = ctypes.c_int()
        if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
            _STRONG_PROCESS_CONTAINMENT = False
            return False
        if libc.prctl(37, ctypes.byref(configured), 0, 0, 0) != 0:  # PR_GET_CHILD_SUBREAPER
            _STRONG_PROCESS_CONTAINMENT = False
            return False
        _STRONG_PROCESS_CONTAINMENT = configured.value == 1
    except (AttributeError, OSError):
        _STRONG_PROCESS_CONTAINMENT = False
    return _STRONG_PROCESS_CONTAINMENT


def process_containment_identity():
    if strong_process_containment_available():
        return {
            "mode": "linux-child-subreaper",
            "detached_descendants": "contained",
        }
    return {
        "mode": "portable-process-group",
        "detached_descendants": "best-effort",
    }


def _owned_process_pids(token, deadline, portable_snapshot=None):
    """Find same-user processes carrying the gate's unguessable ownership token."""
    marker = f"{PROCESS_TOKEN_ENV}={token}".encode("ascii")
    proc = Path("/proc")
    owned = set()
    complete = True
    if sys.platform.startswith("linux") and proc.is_dir():
        if time.monotonic() >= deadline:
            return ProcessDiscovery(frozenset(), False)
        try:
            entries = tuple(proc.iterdir())
        except OSError:
            return ProcessDiscovery(frozenset(), False)
        for entry in entries:
            if not entry.name.isdigit():
                continue
            if time.monotonic() >= deadline:
                complete = False
                break
            try:
                if entry.stat().st_uid != os.getuid():
                    continue
                environment = (entry / "environ").read_bytes().split(b"\0")
            except (FileNotFoundError, ProcessLookupError):
                continue
            except (PermissionError, OSError):
                complete = False
                continue
            if marker in environment:
                owned.add(int(entry.name))
        return ProcessDiscovery(frozenset(owned), complete)
    if portable_snapshot is None:
        portable_snapshot = _portable_process_snapshot(deadline)
    complete = portable_snapshot.complete
    exact_marker = marker.decode("ascii")
    for pid, _parent, uid, command in portable_snapshot.rows:
        if uid == os.getuid() and exact_marker in command.split():
            owned.add(pid)
    return ProcessDiscovery(frozenset(owned), complete)


def process_identity_discovery_available():
    if Path("/proc").is_dir():
        return True
    try:
        result = subprocess.run(
            ["ps", "eww", "-p", str(os.getpid()), "-o", "command="],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=0.2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _signal_processes(process, owned, process_signal):
    try:
        os.killpg(process.pid, process_signal)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        os.kill(process.pid, process_signal)
    except ProcessLookupError:
        pass
    for pid in owned:
        if pid == os.getpid():
            continue
        try:
            os.kill(pid, process_signal)
        except (ProcessLookupError, PermissionError):
            pass


def _contained_process_pids(
    process, token, deadline, containment_root=None, baseline_pids=()
):
    proc = Path("/proc")
    portable_snapshot = None
    if not (sys.platform.startswith("linux") and proc.is_dir()):
        portable_snapshot = _portable_process_snapshot(deadline)
    ancestry = _descendant_pids(process.pid, deadline, portable_snapshot)
    ownership = _owned_process_pids(token, deadline, portable_snapshot)
    owned = set(ancestry.pids)
    owned.update(ownership.pids)
    complete = ancestry.complete and ownership.complete
    if containment_root is not None:
        containment = _descendant_pids(containment_root, deadline)
        owned.update(set(containment.pids).difference(baseline_pids))
        complete = complete and containment.complete
    owned.discard(os.getpid())
    return ProcessDiscovery(frozenset(owned), complete)


def _reap_contained_processes(process, owned):
    for pid in owned:
        if pid == process.pid:
            continue
        try:
            os.waitpid(pid, os.WNOHANG)
        except (ChildProcessError, ProcessLookupError):
            pass


def _kill_process_tree(
    process,
    cleanup_deadline,
    token,
    containment_root=None,
    baseline_pids=(),
    known_pids=(),
):
    first_snapshot_deadline = min(cleanup_deadline - 0.1, time.monotonic() + 0.3)
    first = _contained_process_pids(
        process,
        token,
        first_snapshot_deadline,
        containment_root,
        baseline_pids,
    )
    owned = set(known_pids)
    owned.update(first.pids)
    complete = first.complete
    _signal_processes(process, owned, signal.SIGTERM)
    remaining = cleanup_deadline - 0.05 - time.monotonic()
    if remaining > 0:
        try:
            process.wait(timeout=min(0.05, remaining))
        except subprocess.TimeoutExpired:
            pass
    # Kill the initial owned set before any rescan: its root may already have exited.
    _signal_processes(process, owned, signal.SIGKILL)
    _reap_contained_processes(process, owned)
    rescan_deadline = cleanup_deadline - 0.05
    while time.monotonic() < rescan_deadline:
        discovered = _contained_process_pids(
            process,
            token,
            min(rescan_deadline, time.monotonic() + 0.3),
            containment_root,
            baseline_pids,
        )
        complete = complete and discovered.complete
        owned.update(discovered.pids)
        _signal_processes(process, owned, signal.SIGKILL)
        _reap_contained_processes(process, owned)
        if process.poll() is not None and not discovered.pids:
            break
        remaining = rescan_deadline - time.monotonic()
        if remaining > 0:
            try:
                process.wait(timeout=min(0.02, remaining))
            except subprocess.TimeoutExpired:
                pass
    _signal_processes(process, owned, signal.SIGKILL)
    _reap_contained_processes(process, owned)
    return tuple(sorted(owned, reverse=True)), complete


def _read_component_output(stream):
    stream.flush()
    stream.seek(0)
    return stream.read().decode("utf-8", "replace").strip()


def _cleanup_after_component_exit(
    process, token, cleanup_deadline, containment_root=None, baseline_pids=()
):
    """Reap token/ancestry-owned descendants even when the root exited cleanly."""
    if time.monotonic() >= cleanup_deadline - 0.05:
        return (), False
    initial = _contained_process_pids(
        process,
        token,
        min(cleanup_deadline - 0.05, time.monotonic() + 0.3),
        containment_root,
        baseline_pids,
    )
    if not initial.pids:
        return (), initial.complete
    cleaned, kill_complete = _kill_process_tree(
        process,
        cleanup_deadline,
        token,
        containment_root,
        baseline_pids,
        initial.pids,
    )
    if time.monotonic() >= cleanup_deadline:
        return cleaned, False
    survivors = _contained_process_pids(
        process,
        token,
        cleanup_deadline,
        containment_root,
        baseline_pids,
    )
    return (
        cleaned,
        initial.complete
        and kill_complete
        and survivors.complete
        and not survivors.pids,
    )


def run_component(
    component_id,
    command,
    remaining_seconds,
    cwd=REPO,
    cleanup_deadline=None,
    environment=None,
    internal_environment=None,
    effective_environment=None,
    require_strong_containment=False,
):
    if remaining_seconds <= 0:
        return ComponentResult(component_id, "incomplete", "none", 0.0, tuple(command))
    started = time.monotonic()
    run_deadline = started + remaining_seconds
    cleanup_deadline = (
        run_deadline + min(0.5, max(0.1, remaining_seconds * 0.2))
        if cleanup_deadline is None
        else cleanup_deadline
    )
    strong_containment = strong_process_containment_available()
    if require_strong_containment and not strong_containment:
        return ComponentResult(
            component_id,
            "incomplete",
            "none",
            time.monotonic() - started,
            tuple(command),
            "provider-hard component was not started because strong detached-process "
            f"containment is unavailable on {sys.platform}",
        )
    containment_root = os.getpid() if strong_containment else None
    baseline = (
        _descendant_pids(containment_root, cleanup_deadline)
        if containment_root is not None
        else ProcessDiscovery(frozenset(), True)
    )
    if not baseline.complete:
        return ComponentResult(
            component_id,
            "incomplete",
            "none",
            time.monotonic() - started,
            tuple(command),
            "component was not started because containment baseline discovery was incomplete",
        )
    baseline_pids = baseline.pids
    token = secrets.token_hex(32)
    if effective_environment is None:
        component_environment = safe_process_environment(environment)
        for name, value in (internal_environment or {}).items():
            if name not in INTERNAL_COMPONENT_ENVIRONMENT_NAMES:
                raise GateError(f"unsupported internal component environment name: {name}")
            component_environment[name] = value
    else:
        if environment is not None or internal_environment is not None:
            raise GateError("effective component environment cannot be combined with sources")
        component_environment = dict(effective_environment)
        for name in tuple(component_environment):
            if name.startswith("PYTHON"):
                component_environment.pop(name)
        component_environment.update(FIXED_PYTHON_ENVIRONMENT)
    component_environment[PROCESS_TOKEN_ENV] = token
    with tempfile.TemporaryFile(mode="w+b") as output_stream:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=output_stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=component_environment,
        )
        try:
            process.wait(timeout=max(0.0, run_deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            descendants, cleanup_complete = _kill_process_tree(
                process,
                cleanup_deadline,
                token,
                containment_root,
                baseline_pids,
            )
            captured = _read_component_output(output_stream)
            cleanup = "terminated component process group"
            if strong_containment:
                cleanup += " under Linux child-subreaper containment"
            else:
                cleanup += "; detached-process cleanup is best-effort on this platform"
            if not cleanup_complete:
                cleanup += "; descendant discovery or cleanup was incomplete"
            if descendants:
                cleanup += f" and {len(descendants)} gate-owned descendant(s)"
            output = "component exceeded its reserved execution interval; " + cleanup
            if captured:
                output += "\n" + captured
            return ComponentResult(
                component_id,
                "incomplete",
                "executed",
                time.monotonic() - started,
                tuple(command),
                output,
            )
        descendants, cleanup_complete = _cleanup_after_component_exit(
            process,
            token,
            cleanup_deadline,
            containment_root,
            baseline_pids,
        )
        output = _read_component_output(output_stream)
        if not cleanup_complete:
            detail = "component descendant cleanup did not complete"
            if output:
                detail += "\n" + output
            return ComponentResult(
                component_id,
                "incomplete",
                "executed",
                time.monotonic() - started,
                tuple(command),
                detail,
            )
        if descendants:
            cleanup_detail = "cleaned {} gate-owned descendant(s) after component exit".format(
                len(descendants)
            )
            output = cleanup_detail + ("\n" + output if output else "")
        outcome = "pass" if process.returncode == 0 else "failed"
        return ComponentResult(
            component_id,
            outcome,
            "executed",
            time.monotonic() - started,
            tuple(command),
            output,
        )


def gate_work_cutoffs(hard_deadline, maximum):
    """Reserve separate execution, cleanup, and terminal-decision windows."""
    cleanup_window = min(2.0, max(0.5, maximum * 0.2))
    report_window = min(2.0, max(0.5, maximum * 0.2))
    terminal_guard = min(0.25, max(0.05, maximum * 0.05))
    cleanup_deadline = hard_deadline - report_window
    execution_deadline = cleanup_deadline - cleanup_window
    terminal_decision_deadline = hard_deadline - terminal_guard
    validation_window = min(
        1.0,
        max(0.0, terminal_decision_deadline - cleanup_deadline) * (2.0 / 3.0),
    )
    final_validation_deadline = cleanup_deadline + validation_window
    return (
        execution_deadline,
        cleanup_deadline,
        final_validation_deadline,
        terminal_decision_deadline,
    )


def missing_required_checks(required_check_ids, components):
    passed = {
        component.component_id
        for component in components
        if component.outcome == "pass"
    }
    return tuple(sorted(set(required_check_ids).difference(passed)))


def apply_gate_outcome(
    report,
    gate_id,
    components,
    selected,
    deferred,
    critical,
    required_check_ids,
    candidate_stable,
):
    """Resolve functional, completeness, and drift evidence without weakening safety."""
    failed = next(
        (component for component in components if component.outcome == "failed"), None
    )
    incomplete = next(
        (component for component in components if component.outcome == "incomplete"),
        None,
    )
    missing_required = missing_required_checks(required_check_ids, components)
    if missing_required:
        report["incomplete"] = list(missing_required)
    if not candidate_stable:
        report["outcome"] = "blocked-incomplete"
        report["reason"] = "candidate source drifted during the gate"
        report["incomplete"] = sorted(
            set(report["incomplete"]).union(("candidate-stability",))
        )
    elif failed is not None:
        report["outcome"] = "blocked-failed"
        report["reason"] = f"{failed.component_id} failed"
    elif missing_required:
        report["outcome"] = "blocked-incomplete"
        report["reason"] = (
            "required critical checks did not complete successfully: "
            + ", ".join(missing_required)
        )
    elif incomplete is not None:
        report["incomplete"] = sorted(
            set(report["incomplete"]).union((incomplete.component_id,))
        )
        if (
            critical
            or gate_id == "final"
            or not incomplete.component_id.startswith("repository-tests/")
        ):
            report["outcome"] = "blocked-incomplete"
            report["reason"] = (
                f"{incomplete.component_id} did not complete before the maximum"
            )
        else:
            report["deferred"] = sorted(set(report["deferred"]).union(selected))
            report["outcome"] = "deferred"
            report["reason"] = (
                f"reversible remainder deferred after {incomplete.component_id}"
            )
    elif deferred:
        if critical:
            report["outcome"] = "blocked-incomplete"
            report["reason"] = "critical candidate retained deferred coverage"
        else:
            report["outcome"] = "deferred"
            report["reason"] = (
                "selected checks passed; reversible coverage remains for final"
            )
    else:
        report["outcome"] = "pass"
        report["reason"] = "every required check passed"


def runner_revision(candidate_root=REPO):
    del candidate_root
    return controller_closure()["digest"]


def environment_identity(source=None):
    if source is not None and {"GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"}.issubset(
        source
    ):
        effective = dict(source)
        for name in tuple(effective):
            if name.startswith("PYTHON"):
                effective.pop(name)
        effective.update(FIXED_PYTHON_ENVIRONMENT)
    else:
        effective = safe_process_environment(source)
    normalized = dict(effective)
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        if name in normalized:
            normalized[name] = "<" + name.lower().replace("_", "-") + ">"
    if _OWNER_ENV in normalized:
        normalized[_OWNER_ENV] = "<gate-owner-token>"
    git = subprocess.run(
        ["git", "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {
        "interpreter_identity": interpreter_identity(),
        "git_version": git.stdout.strip() if git.returncode == 0 else "unavailable",
        "component_environment_digest": test_manifest.canonical_digest(
            normalized
        ),
    }


def receipt_binding(
    candidate,
    tested_view,
    selected_tests,
    policy_digest,
    component_id,
    candidate_root=REPO,
    environment=None,
    composite_identity=None,
):
    protocol = None
    if _HANDOFF is not None:
        frame = _HANDOFF.get("policy_frame")
        if isinstance(frame, dict):
            protocol = {
                "handoff_schema": HANDOFF_SCHEMA,
                "policy_frame_schema": frame.get("schema"),
                "controller_claim_schema": CONTROLLER_CLAIM_SCHEMA,
                "terminal_frame_schema": TERMINAL_FRAME_SCHEMA,
                "discovery_ceiling_seconds": frame.get("discovery_ceiling_seconds"),
                "budgets": frame.get("budgets"),
                "base_config_sha256": frame.get("base_config_sha256"),
                "candidate_config_sha256": frame.get("candidate_config_sha256"),
                "trusted_parser_closure_digest": frame.get("trusted_parser_closure_digest"),
                "candidate_parser_closure_digest": frame.get("candidate_parser_closure_digest"),
                "authoritative_index_semantic_sha256": (
                    frame.get("authoritative_index") or {}
                ).get("semantic_sha256"),
                "launcher": frame.get("launcher"),
            }
    if protocol is None:
        launcher = next(
            (
                record
                for record in controller_closure()["records"]
                if record["path"] == "automation/run_test_gate.py"
            ),
            None,
        )
        protocol = {
            "handoff_schema": HANDOFF_SCHEMA,
            "policy_frame_schema": POLICY_FRAME_SCHEMA,
            "controller_claim_schema": CONTROLLER_CLAIM_SCHEMA,
            "terminal_frame_schema": TERMINAL_FRAME_SCHEMA,
            "discovery_ceiling_seconds": DISCOVERY_CEILING_SECONDS,
            "budgets": None,
            "base_config_sha256": None,
            "candidate_config_sha256": None,
            "trusted_parser_closure_digest": None,
            "candidate_parser_closure_digest": None,
            "authoritative_index_semantic_sha256": None,
            "launcher": (
                {"path": launcher["path"], "sha256": launcher["sha256"]}
                if launcher is not None
                else None
            ),
        }
    value = {
        "candidate_digest": candidate.digest,
        "candidate_closure_digest": candidate.closure_digest,
        "tested_view_digest": tested_view["digest"],
        "test_manifest_digest": test_manifest.canonical_digest(selected_tests),
        "policy_digest": policy_digest,
        "gate_protocol": protocol,
        "runner_revision": runner_revision(candidate_root),
        "controller_closure": controller_closure(),
        "environment": environment_identity(environment),
        "component_id": component_id,
        "composite_test_plan": composite_identity,
        "evidence_authority": EVIDENCE_AUTHORITY,
        "controlled_completion": False,
        "enforcement_eligible": False,
    }
    value["binding_digest"] = test_manifest.canonical_digest(value)
    return value


def _safe_local_directory(relative):
    """Return one allowed ignored local-state directory without path redirection.

    A metadata-free test projection deliberately has no Git metadata, so ``git
    check-ignore`` cannot operate there. It may still persist the report below
    its copied root only when Git confirms that there is no repository and the
    copied root has the exact ``tmp/`` ignore rule. The exception is deliberately
    narrower than the normal Git-backed path: it accepts only the two fixed
    state directories, never a caller-selected path.
    """
    relative = Path(relative)
    if relative not in LOCAL_STATE_DIRECTORIES:
        raise GateError("gate state directory is not an allowed repository-local path")
    root = REPO.resolve()
    if not root.is_dir() or root.is_symlink():
        raise GateError("repository root for gate state is unsafe")
    directory = root / relative
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(directory)],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ignore_file = root / ".gitignore"
    try:
        exact_tmp_ignore = (
            ignore_file.is_file()
            and not ignore_file.is_symlink()
            and "tmp/" in ignore_file.read_text(encoding="utf-8").splitlines()
        )
    except OSError:
        exact_tmp_ignore = False
    metadata_free_projection = (
        ignored.returncode == 128 and not (root / ".git").exists()
    )
    if ignored.returncode != 0 and not (
        metadata_free_projection and exact_tmp_ignore
    ):
        raise GateError("gate state directory must be ignored and repository-local")
    current = root
    for part in Path(relative).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            current.mkdir(mode=0o700)
            try:
                metadata = current.lstat()
            except OSError as error:
                raise GateError(
                    f"could not inspect newly created gate-state path: {current}"
                ) from error
        if stat.S_ISLNK(metadata.st_mode):
            raise GateError(f"ignored gate-state path is a symlink: {current}")
        if not stat.S_ISDIR(metadata.st_mode):
            raise GateError(f"ignored gate-state path is unsafe: {current}")
    return directory


def _atomic_json(path, value):
    path = Path(path)
    if path.exists() and path.is_symlink():
        raise GateError(f"refusing to replace symlinked gate state: {path}")
    temporary_name = f".{path.name}.{os.getpid()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory_descriptor = os.open(str(path.parent), directory_flags)
    committed = False
    try:
        payload = (
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        descriptor = os.open(
            temporary_name, flags, 0o600, dir_fd=directory_descriptor
        )
        try:
            remaining = memoryview(payload)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise GateError("could not finish writing gate state")
                remaining = remaining[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.rename(
            temporary_name,
            path.name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
        )
        committed = True
        # The rename is the logical publication commit. A later directory fsync
        # failure can affect crash durability, but cannot make the visible artifact
        # uncommitted. A future reuse fails closed if the artifact is lost.
        try:
            os.fsync(directory_descriptor)
        except Exception:
            pass
    finally:
        try:
            os.close(directory_descriptor)
        except Exception:
            if not committed:
                raise


def _receipt_cache_paths(binding):
    digest = binding.get("binding_digest")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise GateError("receipt binding digest is invalid")
    directory = _safe_local_directory(Path("tmp/test-gate-receipts"))
    return directory / f"{digest}.json", directory / f"{digest}.commit.json"


def reusable_receipt(binding):
    try:
        path, expected_marker_path = _receipt_cache_paths(binding)
    except (GateError, OSError, ValueError):
        return None
    if not path.is_file() or path.is_symlink():
        return None
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    if (
        value.get("schema") != RECEIPT_SCHEMA
        or value.get("outcome") != "pass"
        or value.get("terminalized_pass") is not True
        or value.get("command_outcome") != "pass"
        or value.get("command_exit_code") != 0
        or value.get("binding") != binding
        or value.get("evidence_authority") != EVIDENCE_AUTHORITY
        or value.get("controlled_completion") is not False
        or value.get("enforcement_eligible") is not False
    ):
        return None
    publication = value.get("publication")
    if not isinstance(publication, dict):
        return None
    publication_id = publication.get("id")
    report_relative = publication.get("report_path")
    report_digest = publication.get("report_digest")
    marker_relative = publication.get("commit_marker_path")
    expected_marker_relative = (
        "tmp/test-gate-receipts/{}.commit.json".format(binding["binding_digest"])
    )
    if (
        not isinstance(publication_id, str)
        or len(publication_id) != 64
        or any(character not in "0123456789abcdef" for character in publication_id)
        or publication.get("status") != "success"
        or report_relative not in REPORT_PROJECTIONS
        or marker_relative != expected_marker_relative
        or not isinstance(report_digest, str)
    ):
        return None
    report_directory = _safe_local_directory(Path("tmp/test-gate-reports"))
    report_path = report_directory / Path(report_relative).name
    if not report_path.is_file() or report_path.is_symlink():
        return None
    try:
        report = json.loads(report_path.read_text())
    except (OSError, ValueError):
        return None
    candidate = report.get("candidate")
    expected_report = "tmp/test-gate-reports/latest-{}.json".format(
        report.get("gate_id")
    )
    if (
        report.get("schema") != REPORT_SCHEMA
        or expected_report != report_relative
        or report.get("publication_id") != publication_id
        or test_manifest.canonical_digest(report) != report_digest
        or report.get("outcome") != "pass"
        or report.get("terminalized_pass") is not True
        or report.get("gate_exit_code") != 0
        or report.get("publication_status") != "success"
        or report.get("command_outcome") != "pass"
        or report.get("exit_code") != 0
        or report.get("evidence_authority") != EVIDENCE_AUTHORITY
        or report.get("controlled_completion") is not False
        or report.get("enforcement_eligible") is not False
        or report.get("decision_digest")
        != test_manifest.canonical_digest(report.get("decision"))
        or value.get("decision_digest") != report.get("decision_digest")
        or not isinstance(candidate, dict)
        or candidate.get("digest") != binding.get("candidate_digest")
        or candidate.get("closure_digest")
        != binding.get("candidate_closure_digest")
    ):
        return None
    if not expected_marker_path.is_file() or expected_marker_path.is_symlink():
        return None
    try:
        marker = json.loads(expected_marker_path.read_text())
        expected_marker = _publication_marker_value(
            binding,
            value,
            report,
            path,
            report_path,
            expected_marker_path,
        )
    except (GateError, OSError, ValueError):
        return None
    if marker != expected_marker:
        return None
    return value


def write_receipt(binding, terminal_report, report_path=None, marker_path=None):
    path, expected_marker_path = _receipt_cache_paths(binding)
    marker_path = expected_marker_path if marker_path is None else marker_path
    if report_path is None:
        report_directory = _safe_local_directory(Path("tmp/test-gate-reports"))
        report_path = report_directory / "latest-{}.json".format(
            terminal_report.get("gate_id")
        )
    _atomic_json(
        path, _receipt_value(binding, terminal_report, report_path, marker_path)
    )
    return path


def local_receipts_allowed(options):
    """Provider hard boundaries never trust or mutate checkout-local evidence."""
    return not options.provider_hard


def reusable_full_receipt(binding, component_id, options):
    if not component_id.endswith("/full") or not local_receipts_allowed(options):
        return None
    return reusable_receipt(binding)


def latest_reusable_full_receipt_binding(candidate, options):
    """Use the fixed final report only as a pointer to exact full evidence."""
    if not local_receipts_allowed(options):
        return None
    try:
        report_directory = _safe_local_directory(Path("tmp/test-gate-reports"))
        report_path = report_directory / "latest-final.json"
        if not report_path.is_file() or report_path.is_symlink():
            return None
        report = json.loads(report_path.read_text())
        if not isinstance(report, dict):
            return None
        report_candidate = report.get("candidate")
        binding_digest = report.get("receipt_binding_digest")
        if (
            not isinstance(report_candidate, dict)
            or report_candidate.get("digest") != candidate.digest
            or report_candidate.get("closure_digest") != candidate.closure_digest
            or report_candidate.get("base_revision") != candidate.base_revision
            or report_candidate.get("candidate_revision")
            != candidate.candidate_revision
            or not isinstance(binding_digest, str)
            or len(binding_digest) != 64
            or any(
                character not in "0123456789abcdef"
                for character in binding_digest
            )
        ):
            return None
        receipt_directory = _safe_local_directory(Path("tmp/test-gate-receipts"))
        receipt_path = receipt_directory / (binding_digest + ".json")
        if not receipt_path.is_file() or receipt_path.is_symlink():
            return None
        receipt = json.loads(receipt_path.read_text())
        if not isinstance(receipt, dict):
            return None
        binding = receipt.get("binding")
        if (
            not isinstance(binding, dict)
            or binding.get("binding_digest") != binding_digest
            or binding.get("component_id") != "repository-tests/full"
            or binding.get("candidate_digest") != candidate.digest
            or binding.get("candidate_closure_digest")
            != candidate.closure_digest
            or reusable_receipt(binding) is None
        ):
            return None
        return binding
    except (GateError, OSError, ValueError):
        return None


def full_receipt_current_identity_matches(binding, current_identity):
    """Compare every full binding input except its exact manifest and plan."""
    fields = (
        "candidate_digest",
        "candidate_closure_digest",
        "tested_view_digest",
        "policy_digest",
        "gate_protocol",
        "runner_revision",
        "controller_closure",
        "environment",
        "component_id",
        "evidence_authority",
        "controlled_completion",
        "enforcement_eligible",
    )
    return all(binding.get(name) == current_identity.get(name) for name in fields)


def persist_full_receipt(
    binding, result, candidate_stable, options, terminal_report=None
):
    if (
        result.outcome != "pass"
        or not candidate_stable
        or not local_receipts_allowed(options)
        or binding.get("composite_test_plan") is None
        or terminal_report is None
        or terminal_report.get("terminalized_pass") is not True
        or terminal_report.get("outcome") != "pass"
        or terminal_report.get("publication_status") != "success"
        or terminal_report.get("command_outcome") != "pass"
        or terminal_report.get("exit_code") != 0
    ):
        return False
    write_receipt(binding, terminal_report)
    return reusable_receipt(binding) is not None


def _write_report(report):
    directory = _safe_local_directory(Path("tmp/test-gate-reports"))
    path = directory / f"latest-{report['gate_id']}.json"
    _atomic_json(path, report)
    return path


def file_target_breach(
    report, target, policy_digest, options, actual_seconds=None, environment=None
):
    """Best-effort durable performance work; its disposition never changes the gate."""
    if file_test_budget_task is None:
        return {"disposition": "unavailable", "mutated": False}
    actual = (
        time.monotonic() - report["_started"]
        if actual_seconds is None
        else actual_seconds
    )
    components = {
        component["component_id"]: component["duration_seconds"]
        for component in report["components"]
    }
    occurrence = {
        "schema_id": REPORT_SCHEMA,
        "gate_id": report["gate_id"],
        "config_slot": f"testing.{report['gate_id']}.target_seconds",
        "actual_seconds": actual,
        "target_seconds": target,
        "components": components,
        "candidate": report["candidate"]["digest"],
        "receipt": test_manifest.canonical_digest(
            {
                "candidate": report["candidate"]["digest"],
                "components": components,
                "policy": policy_digest,
            }
        ),
        "command": "automation/run_test_gate.py " + " ".join(sys.argv[1:]),
        "trigger": options.at_transition or ("explicit" if options.explicit else "pre-commit"),
        "environment": environment_identity(environment),
    }
    return file_test_budget_task.file_budget_task(REPO, occurrence).as_dict()


def _account_maximum(report, maximum):
    if maximum is None:
        return
    report["maximum_seconds"] = maximum
    report["maximum_exceeded"] = report["duration_seconds"] >= maximum
    if not report["maximum_exceeded"]:
        return
    if report["outcome"] not in ("pass", "deferred"):
        return
    report["incomplete"] = sorted(
        set(report["incomplete"]).union(("gate-interval",))
    )
    if report["gate_id"] == "final" or report.get("critical", {}).get(
        "is_critical"
    ):
        report["outcome"] = "blocked-incomplete"
        report["reason"] = "whole gate interval exceeded the configured maximum"
    else:
        report["outcome"] = "deferred"
        report["reason"] = (
            "whole gate interval exceeded the maximum; reversible coverage remains deferred"
        )


def _account_elapsed(report, started, target, maximum, elapsed=None):
    elapsed = time.monotonic() - started if elapsed is None else elapsed
    report["duration_seconds"] = round(elapsed, 6)
    if target is not None:
        report["target_seconds"] = target
        report["target_exceeded"] = report["duration_seconds"] >= target
    _account_maximum(report, maximum)
    report["gate_exit_code"] = OUTCOME_EXIT[report["outcome"]]


def _render_summary(report, path):
    lines = [
        f"test gate: {report['gate_id']}",
        f"outcome: {report['outcome']}",
        f"gate exit: {report['gate_exit_code']}",
        f"evidence: {report['evidence']}",
        f"evidence_authority: {report['evidence_authority']}",
        f"controlled_completion: {str(report['controlled_completion']).lower()}",
        f"enforcement_eligible: {str(report['enforcement_eligible']).lower()}",
        f"enforcement: {report['enforcement']}",
        f"reason: {report['reason']}",
        "publication: {status} ({reason})".format(
            status=report["publication_status"],
            reason=report["publication_reason"],
        ),
        "command: {outcome} (exit {exit_code})".format(
            outcome=report["command_outcome"], exit_code=report["exit_code"]
        ),
    ]
    if report["candidate"] is not None:
        lines.append(f"candidate: {report['candidate']['digest']}")
    lines.append("component timings:")
    if report["components"]:
        for component in report["components"]:
            lines.append(
                "  {component_id}: {outcome} ({evidence}, {duration_seconds:.2f}s)".format(
                    **component
                )
            )
            if component["outcome"] != "pass" and component.get("detail"):
                lines.extend(f"    {line}" for line in component["detail"].splitlines())
    else:
        lines.append("  (none)")
    lines.append(
        "coverage: {selected} selected, {deferred} deferred, {incomplete} incomplete".format(
            selected=len(report["selected"]),
            deferred=len(report["deferred"]),
            incomplete=len(report["incomplete"]),
        )
    )
    lines.append(f"duration: {report['duration_seconds']:.2f}s")
    if report.get("target_exceeded"):
        filing = report.get("budget_filing", {})
        lines.append(
            "target: exceeded {target:.2f}s; budget filing {disposition}".format(
                target=report.get("target_seconds", 0.0),
                disposition=filing.get("disposition", "unavailable"),
            )
        )
    if path is None:
        disposition = report.get("report_write", {}).get("disposition", "unavailable")
        lines.append(f"machine report: {disposition}")
    else:
        lines.append(f"machine report: {path.resolve().relative_to(REPO.resolve())}")
    return "\n".join(lines) + "\n"


def _write_summary(summary):
    sys.stdout.write(summary)
    sys.stdout.flush()


def _write_publication_error(reason):
    try:
        sys.stderr.write("test gate publication error: {}\ncommand exit: 2\n".format(reason))
        sys.stderr.flush()
    except OSError:
        pass


def _repository_projection_path(path, expected):
    try:
        relative = Path(path).resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError as error:
        raise GateError("gate projection is outside the repository") from error
    if relative != expected:
        raise GateError("gate projection path does not match its fixed cache key")
    return relative


def _receipt_value(binding, terminal_report, report_path, marker_path=None):
    publication_id = terminal_report.get("publication_id")
    binding_digest = binding.get("binding_digest")
    receipt_path, expected_marker_path = _receipt_cache_paths(binding)
    marker_path = expected_marker_path if marker_path is None else marker_path
    report_expected = "tmp/test-gate-reports/latest-{}.json".format(
        terminal_report.get("gate_id")
    )
    report_relative = _repository_projection_path(report_path, report_expected)
    marker_relative = _repository_projection_path(
        marker_path,
        "tmp/test-gate-receipts/{}.commit.json".format(binding_digest),
    )
    _repository_projection_path(
        receipt_path, "tmp/test-gate-receipts/{}.json".format(binding_digest)
    )
    if (
        not isinstance(publication_id, str)
        or len(publication_id) != 64
        or report_relative not in REPORT_PROJECTIONS
        or terminal_report.get("outcome") != "pass"
        or terminal_report.get("terminalized_pass") is not True
        or terminal_report.get("gate_exit_code") != 0
        or terminal_report.get("publication_status") != "success"
        or terminal_report.get("command_outcome") != "pass"
        or terminal_report.get("exit_code") != 0
    ):
        raise GateError("receipt requires an attested terminal pass report")
    return {
        "schema": RECEIPT_SCHEMA,
        "outcome": "pass",
        "terminalized_pass": True,
        "command_outcome": "pass",
        "command_exit_code": 0,
        "evidence_authority": EVIDENCE_AUTHORITY,
        "controlled_completion": False,
        "enforcement_eligible": False,
        "binding": binding,
        "decision_digest": terminal_report["decision_digest"],
        "publication": {
            "id": publication_id,
            "status": "success",
            "report_path": report_relative,
            "report_digest": test_manifest.canonical_digest(terminal_report),
            "commit_marker_path": marker_relative,
        },
    }


def _publication_marker_value(
    binding, receipt, terminal_report, receipt_path, report_path, marker_path
):
    binding_digest = binding.get("binding_digest")
    receipt_relative = _repository_projection_path(
        receipt_path, "tmp/test-gate-receipts/{}.json".format(binding_digest)
    )
    marker_relative = _repository_projection_path(
        marker_path,
        "tmp/test-gate-receipts/{}.commit.json".format(binding_digest),
    )
    report_relative = _repository_projection_path(
        report_path,
        "tmp/test-gate-reports/latest-{}.json".format(
            terminal_report.get("gate_id")
        ),
    )
    publication = receipt.get("publication", {})
    if (
        receipt.get("schema") != RECEIPT_SCHEMA
        or publication.get("id") != terminal_report.get("publication_id")
        or publication.get("report_path") != report_relative
        or publication.get("report_digest")
        != test_manifest.canonical_digest(terminal_report)
        or publication.get("commit_marker_path") != marker_relative
    ):
        raise GateError("publication commit inputs do not match")
    return {
        "schema": PUBLICATION_COMMIT_SCHEMA,
        "publication_id": terminal_report["publication_id"],
        "binding_digest": binding_digest,
        "receipt": {
            "path": receipt_relative,
            "digest": test_manifest.canonical_digest(receipt),
        },
        "report": {
            "path": report_relative,
            "digest": test_manifest.canonical_digest(terminal_report),
        },
        "candidate": {
            "digest": binding.get("candidate_digest"),
            "closure_digest": binding.get("candidate_closure_digest"),
        },
        "evidence_authority": EVIDENCE_AUTHORITY,
    }


def _remove_projection(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        return False
    return True


def _decision_value(report):
    value = {
        "schema": DECISION_SCHEMA,
        "gate_id": report["gate_id"],
        "outcome": report["outcome"],
        "gate_exit_code": report["gate_exit_code"],
        "terminalized_pass": report["terminalized_pass"],
        "reason": report["reason"],
        "duration_seconds": report["duration_seconds"],
        "target_seconds": report.get("target_seconds"),
        "maximum_seconds": report.get("maximum_seconds"),
        "policy_digest": report.get("policy_digest"),
        "candidate_digest": (report.get("candidate") or {}).get("digest"),
        "incomplete": list(report.get("incomplete", ())),
        "evidence_authority": report["evidence_authority"],
        "controlled_completion": report["controlled_completion"],
        "enforcement_eligible": report["enforcement_eligible"],
        "enforcement": report["enforcement"],
    }
    return value


def _send_terminal_decision(
    report,
    deadline=None,
    *,
    clock=time.monotonic,
    select_fn=select.select,
    write_fn=os.write,
    get_blocking=os.get_blocking,
    set_blocking=os.set_blocking,
):
    raw_fd = os.environ.get(_CONTROL_FD_ENV)
    if raw_fd is None:
        return
    if not raw_fd.isdigit():
        raise GateError("test-gate control descriptor is invalid")
    frame = {
        "schema": CONTROLLER_CLAIM_SCHEMA,
        "gate_id": report["gate_id"],
        "outcome": report["outcome"],
        "gate_exit_code": report["gate_exit_code"],
        "terminalized_pass": report["terminalized_pass"],
        "policy_digest": report.get("policy_digest"),
        "decision_digest": report["decision_digest"],
        "receipt_binding_digest": report.get("receipt_binding_digest"),
        "evidence_authority": report["evidence_authority"],
        "controlled_completion": report["controlled_completion"],
        "enforcement_eligible": report["enforcement_eligible"],
    }
    frame["claim_digest"] = test_manifest.canonical_digest(frame)
    payload = json.dumps(
        frame,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(payload) > CONTROL_FRAME_MAX_BYTES:
        raise GateError("test-gate terminal decision is oversized")
    data = memoryview(struct.pack("!I", len(payload)) + payload)
    descriptor = int(raw_fd)
    original_blocking = get_blocking(descriptor)
    try:
        if deadline is not None:
            set_blocking(descriptor, False)
        while data:
            if deadline is not None:
                now = clock()
                if now >= deadline:
                    raise GateError("test-gate terminal decision missed its deadline")
                _, writable, _ = select_fn((), (descriptor,), (), deadline - now)
                if not writable or clock() >= deadline:
                    raise GateError("test-gate terminal decision missed its deadline")
            try:
                written = write_fn(descriptor, data)
            except (BlockingIOError, InterruptedError):
                continue
            if written <= 0:
                raise GateError("test-gate terminal decision could not be sent")
            data = data[written:]
        if deadline is not None and clock() >= deadline:
            raise GateError("test-gate terminal decision completed at its deadline")
    finally:
        if deadline is not None:
            set_blocking(descriptor, original_blocking)


def emit_report(
    report,
    target=None,
    maximum=None,
    policy_digest=None,
    options=None,
    receipt_binding_value=None,
    receipt_stable=None,
    component_environment=None,
    terminal_decision_deadline=None,
):
    """Terminalize once, then project the frozen report and one optional receipt.

    Atomic projection and stdout happen outside the measured interval. No clock sample
    after terminalization may mutate duration, threshold flags, outcome, reason, or the
    gate exit. Publication may independently fail the command.
    """
    started = report.pop("_started")
    publication_preparation_error = None
    publication_preparation_disposition = "failed"
    path = None
    receipt_path = None
    marker_path = None
    receipt_value = None
    elapsed = time.monotonic() - started
    _account_elapsed(report, started, target, maximum, elapsed)
    report["terminalized_pass"] = report["outcome"] == "pass"
    report["gate_exit_code"] = OUTCOME_EXIT[report["outcome"]]
    report["publication_status"] = "success"
    report["publication_reason"] = "required projections persisted"
    report["report_write"] = {"disposition": "written"}
    report["command_outcome"] = report["outcome"]
    report["exit_code"] = report["gate_exit_code"]
    report["publication_id"] = secrets.token_hex(32)
    report["receipt_binding_digest"] = (
        receipt_binding_value.get("binding_digest")
        if receipt_binding_value is not None
        else None
    )
    report["decision"] = _decision_value(report)
    report["decision_digest"] = test_manifest.canonical_digest(report["decision"])

    try:
        _send_terminal_decision(report, terminal_decision_deadline)
    except (GateError, OSError, ValueError) as error:
        _write_publication_error("terminal decision publication failed: " + str(error))
        return OUTCOME_EXIT["error"]

    if (
        report.get("target_exceeded")
        and target is not None
        and options is not None
        and "budget_filing" not in report
    ):
        filing_deadline = time.monotonic() + POST_CLAIM_FILING_TIMEOUT_SECONDS
        completed, filing = _bounded_json_call(
            lambda: file_target_breach(
                report,
                target,
                policy_digest,
                options,
                actual_seconds=elapsed,
                environment=component_environment,
            ),
            filing_deadline,
        )
        report["budget_filing"] = (
            filing
            if completed and isinstance(filing, dict)
            else {
                "disposition": "timed-out",
                # The helper may have crossed a mutation boundary before it was
                # killed.  A later deduplicated filing pass determines the truth.
                "mutated": None,
            }
        )

    # State-path checks and all filesystem projection happen after the immutable
    # terminal claim.  A projection error can change only the command/publication
    # status, never the already brokered gate decision.
    try:
        report_directory = _safe_local_directory(Path("tmp/test-gate-reports"))
        path = report_directory / f"latest-{report['gate_id']}.json"
        if receipt_binding_value is not None:
            if receipt_binding_value.get("composite_test_plan") is None:
                raise GateError("receipt persistence requires a full composite test plan")
            receipt_path, marker_path = _receipt_cache_paths(receipt_binding_value)
            if receipt_path.exists() and receipt_path.is_symlink():
                raise GateError("refusing to replace symlinked gate receipt")
            if marker_path.exists() and marker_path.is_symlink():
                raise GateError("refusing to replace symlinked publication marker")
            if receipt_stable is None or not receipt_stable:
                raise GateError("candidate or controller closure drifted before receipt persistence")
    except (GateError, OSError, ValueError) as error:
        path = None
        receipt_path = None
        marker_path = None
        publication_preparation_error = str(error)
        publication_preparation_disposition = "refused"

    if not report["terminalized_pass"]:
        receipt_path = None
        marker_path = None

    def publication_error(reason, remove_receipt=False, disposition="failed"):
        nonlocal path
        if remove_receipt and receipt_path is not None:
            _remove_projection(receipt_path)
        if marker_path is not None:
            _remove_projection(marker_path)
        report["report_write"] = {"disposition": disposition}
        report["publication_status"] = "error"
        report["publication_reason"] = reason
        report["command_outcome"] = "error"
        report["exit_code"] = OUTCOME_EXIT["error"]
        if path is None:
            return
        try:
            _atomic_json(path, report)
        except (GateError, OSError, ValueError):
            _remove_projection(path)
            path = None

    if publication_preparation_error is not None:
        publication_error(
            publication_preparation_error,
            disposition=publication_preparation_disposition,
        )
    elif receipt_path is not None:
        try:
            receipt_value = _receipt_value(
                receipt_binding_value, report, path, marker_path
            )
            _atomic_json(
                receipt_path,
                receipt_value,
            )
        except (GateError, OSError, ValueError) as error:
            publication_error(
                "receipt persistence failed: " + str(error), remove_receipt=True
            )
        else:
            try:
                _atomic_json(path, report)
            except (GateError, OSError, ValueError) as error:
                publication_error(
                    "machine report persistence failed: " + str(error),
                    remove_receipt=True,
                )
    elif path is not None:
        try:
            _atomic_json(path, report)
        except (GateError, OSError, ValueError) as error:
            publication_error("machine report persistence failed: " + str(error))

    try:
        _write_summary(_render_summary(report, path))
    except (BrokenPipeError, OSError) as error:
        reason = "stdout summary publication failed: " + str(error)
        publication_error(reason, remove_receipt=True)
        _write_publication_error(reason)
        return OUTCOME_EXIT["error"]

    if (
        marker_path is not None
        and receipt_path is not None
        and receipt_value is not None
        and report["publication_status"] == "success"
        and report["command_outcome"] == "pass"
    ):
        try:
            marker = _publication_marker_value(
                receipt_binding_value,
                receipt_value,
                report,
                receipt_path,
                path,
                marker_path,
            )
            _atomic_json(marker_path, marker)
        except (GateError, OSError, ValueError) as error:
            reason = "publication commit marker failed: " + str(error)
            publication_error(reason, remove_receipt=True)
            _write_publication_error(reason)
    return report["exit_code"]


def _base_report(gate, started):
    return {
        "schema": REPORT_SCHEMA,
        "gate_id": gate,
        "outcome": "error",
        "evidence": "none",
        "evidence_authority": EVIDENCE_AUTHORITY,
        "controlled_completion": False,
        "enforcement_eligible": False,
        "enforcement": "not-enforced",
        "reason": "gate did not complete",
        "candidate": None,
        "tested_view": None,
        "test_plan": None,
        "execution_identity": None,
        "decision_protocol": None,
        "policy_digest": None,
        "critical": {},
        "selected": [],
        "deferred": [],
        "incomplete": [],
        "components": [],
        "process_containment": process_containment_identity(),
        "target_exceeded": False,
        "maximum_exceeded": False,
        "terminalized_pass": False,
        "invocation": None,
        "receipt_binding_digest": None,
        "_started": started,
    }


def main(arguments=(), started=None):
    options = parse_arguments(arguments)
    absolute_deadline = None
    terminal_decision_deadline = None
    if _HANDOFF is not None:
        raw_started = _HANDOFF.get("started_monotonic")
        raw_deadline = _HANDOFF.get("absolute_deadline_monotonic")
        if (
            not isinstance(raw_started, bool)
            and isinstance(raw_started, (int, float))
            and math.isfinite(raw_started)
            and not isinstance(raw_deadline, bool)
            and isinstance(raw_deadline, (int, float))
            and math.isfinite(raw_deadline)
            and raw_deadline > raw_started
        ):
            # Even a later handoff-validation failure should use the supervisor's
            # raw absolute bound for a deadline-bounded error claim.
            terminal_decision_deadline = gate_work_cutoffs(
                float(raw_deadline), float(raw_deadline - raw_started)
            )[3]
        try:
            handoff_started, absolute_deadline = gate_interval_bounds()
        except GateError as error:
            report = _base_report(options.gate, PROCESS_STARTED)
            report["outcome"] = "error"
            report["reason"] = str(error)
            return emit_report(
                report, terminal_decision_deadline=terminal_decision_deadline
            )
        if started is None:
            started = handoff_started
        terminal_decision_deadline = gate_work_cutoffs(
            absolute_deadline, absolute_deadline - started
        )[3]
    elif started is None:
        started = PROCESS_STARTED
    report = _base_report(options.gate, started)
    if _HANDOFF is not None:
        frame = _HANDOFF.get("policy_frame")
        if isinstance(frame, dict):
            # The broker accepts only claims bound to its authoritative policy.
            # Preserve that identity even when candidate-side reproduction fails.
            report["policy_digest"] = frame.get("policy_digest")
    if options.at_transition or options.provider_hard:
        report["outcome"] = "blocked-incomplete"
        report["reason"] = (
            "automatic final transitions are unavailable: the repository has no "
            "controlled external completion oracle and independently controlled publisher"
        )
        report["incomplete"] = [
            "controlled-external-completion-oracle",
            "independently-controlled-publisher",
        ]
        report["invocation"] = {
            "kind": "transition",
            "transition": options.at_transition,
            "base_revision": options.base_revision,
            "head_revision": options.head_revision,
            "candidate_revision": options.candidate_revision,
            "provider_hard": options.provider_hard,
        }
        return emit_report(
            report, terminal_decision_deadline=terminal_decision_deadline
        )
    try:
        validated_closure = validate_bootstrap_handoff()
        _require_work_time(absolute_deadline, "controller admission")
        with tempfile.TemporaryDirectory(prefix="agentfold-test-gate-") as scratch:
            scratch_root = Path(scratch).resolve()
            candidate, tested_view, candidate_root, unchanged = capture_candidate(
                options, scratch_root
            )
            _require_work_time(absolute_deadline, "candidate capture")
            if not unchanged():
                raise GateError("candidate capture or controller closure drifted before execution")
            report["candidate"] = candidate.as_dict()
            report["tested_view"] = {
                "schema": tested_view["schema"],
                "digest": tested_view["digest"],
                "paths": tested_view["paths"],
            }
            policy, policy_digest = load_candidate_policy(
                candidate_root,
                options.config,
                scratch_root,
                candidate.base_revision,
            )
            protocol_identity = validate_policy_frame(
                policy,
                policy_digest,
                candidate_root,
                candidate.base_revision,
                options.gate,
            )
            _require_work_time(absolute_deadline, "policy validation")
            report["policy_digest"] = policy_digest
            report["decision_protocol"] = protocol_identity
            report["invocation"] = {
                "kind": (
                    "explicit"
                    if options.explicit
                    else "transition"
                    if options.at_transition
                    else "routine"
                ),
                "transition": options.at_transition,
                "base_revision": candidate.base_revision,
                "head_revision": options.head_revision,
                "candidate_revision": candidate.candidate_revision,
                "provider_hard": options.provider_hard,
            }
            disposition = _final_disposition(options, policy)
            if disposition is not None:
                report["outcome"], report["reason"] = disposition
                return emit_report(
                    report, terminal_decision_deadline=terminal_decision_deadline
                )

            classification = classify_candidate(candidate.changed_paths, policy)
            _require_work_time(absolute_deadline, "risk classification")
            required_critical = tuple(classification.required_check_ids)
            critical = bool(
                classification.critical_bindings
                or classification.unmatched_paths
                or required_critical
            )
            report["critical"] = {
                "is_critical": critical,
                "bindings": [
                    getattr(binding, "name", getattr(binding, "category", str(binding)))
                    for binding in classification.critical_bindings
                ],
                "unmatched_paths": list(classification.unmatched_paths),
                "required_check_ids": list(required_critical),
            }
            all_tests = _all_relative_tests(candidate_root)
            requires_full = (
                options.gate == "final"
                or "repository-tests/full" in required_critical
            )
            composite = None
            if requires_full:
                composite = composite_test_plan(
                    candidate, candidate_root, tested_view, scratch_root
                )
                report["test_plan"] = composite["identity"]
                selected = tuple(
                    sorted(
                        set(composite["floor_tests"]).union(
                            composite["supplemental_tests"]
                        )
                    )
                )
                deferred = ()
            else:
                selected, deferred = routine_test_manifest(
                    candidate.changed_paths, all_tests, policy
                )
            _require_work_time(absolute_deadline, "test planning")
            report["selected"] = list(selected)
            report["deferred"] = list(deferred)

            budget = _budget_for(options.gate, policy)
            maximum = float(budget.maximum_seconds)
            target = float(budget.target_seconds)
            hard_deadline = (
                absolute_deadline
                if absolute_deadline is not None
                else started + maximum
            )
            if absolute_deadline is not None and abs(
                (absolute_deadline - started) - maximum
            ) > 0.001:
                raise GateError("configured budget disagrees with supervisor deadline")
            (
                execution_deadline,
                cleanup_deadline,
                final_validation_deadline,
                terminal_decision_deadline,
            ) = gate_work_cutoffs(hard_deadline, maximum)
            components = []
            frozen_index = (
                Path(_HANDOFF["frozen_index"])
                if _HANDOFF is not None
                else scratch_root / "candidate.index"
            )
            if _HANDOFF is None:
                authoritative_index_identity = seal_authoritative_frozen_index(
                    frozen_index, candidate.base_revision
                )
            else:
                authoritative_index_identity = frozen_index_identity(
                    frozen_index, candidate.base_revision
                )

            def candidate_stable():
                return unchanged() and frozen_index_matches(
                    frozen_index,
                    candidate.base_revision,
                    authoritative_index_identity,
                )

            def candidate_stable_before(deadline):
                completed, stable = _bounded_json_call(candidate_stable, deadline)
                return completed and stable is True

            internal_component_environment = candidate_git_environment(
                candidate_root, frozen_index
            )
            component_environment = safe_process_environment()
            component_environment.update(internal_component_environment)
            report["execution_identity"] = {
                "runner_revision": validated_closure["digest"],
                "controller_closure": validated_closure,
                "environment": environment_identity(component_environment),
                "frozen_index_semantic_sha256": authoritative_index_identity[
                    "semantic_sha256"
                ],
            }

            def guarded_component(
                component_id,
                command,
                run_until,
                cwd,
                require_strong_containment=False,
            ):
                if time.monotonic() >= run_until:
                    return ComponentResult(
                        component_id,
                        "incomplete",
                        "none",
                        0.0,
                        tuple(command),
                        "component was not started because its execution window expired",
                    )
                if not candidate_stable_before(run_until):
                    return ComponentResult(
                        component_id,
                        "incomplete",
                        "none",
                        0.0,
                        tuple(command),
                        "authoritative frozen index or candidate changed before component execution",
                    )
                index_directory = Path(
                    tempfile.mkdtemp(
                        prefix="agentfold-component-index-", dir=str(scratch_root)
                    )
                ).resolve()
                component_index = index_directory / "candidate.index"
                try:
                    component_index_identity = copy_component_index(
                        frozen_index, component_index, candidate.base_revision
                    )
                    effective_environment = dict(component_environment)
                    effective_environment["GIT_INDEX_FILE"] = str(component_index)
                    result = run_component(
                        component_id,
                        command,
                        run_until - time.monotonic(),
                        cwd=cwd,
                        cleanup_deadline=cleanup_deadline,
                        effective_environment=effective_environment,
                        require_strong_containment=require_strong_containment,
                    )
                    completed, stability = _bounded_json_call(
                        lambda: {
                            "authoritative": candidate_stable(),
                            "component": frozen_index_matches(
                                component_index,
                                candidate.base_revision,
                                component_index_identity,
                            ),
                        },
                        cleanup_deadline,
                    )
                    authoritative_stable = bool(
                        completed and stability.get("authoritative")
                    )
                    component_index_stable = bool(
                        completed and stability.get("component")
                    )
                    if not authoritative_stable or not component_index_stable:
                        reasons = []
                        if not authoritative_stable:
                            reasons.append("authoritative frozen index or candidate changed")
                        if not component_index_stable:
                            reasons.append("disposable component index changed")
                        detail = "; ".join(reasons)
                        if result.detail:
                            detail += "\n" + result.detail
                        return ComponentResult(
                            component_id,
                            "incomplete",
                            result.evidence,
                            result.duration_seconds,
                            tuple(command),
                            detail,
                        )
                    return result
                finally:
                    # The enclosing scratch directory is removed only after emit_report
                    # has sent the immutable terminal claim.
                    pass

            commands = admission_commands(options, candidate, candidate_root)
            for component_id, command in commands:
                result = guarded_component(
                    component_id,
                    command,
                    execution_deadline,
                    cwd=candidate_root,
                    require_strong_containment=options.provider_hard,
                )
                components.append(result)
                if result.outcome != "pass":
                    break

            if (
                (not components or all(result.outcome == "pass" for result in components))
                and not candidate_stable_before(execution_deadline)
            ):
                components.append(
                    ComponentResult(
                        "candidate-stability",
                        "incomplete",
                        "none",
                        0.0,
                        (),
                        "candidate index or controller closure drifted before test execution",
                    )
                )

            pending_receipt_binding = None
            if not components or all(result.outcome == "pass" for result in components):
                if selected:
                    component_id = (
                        "repository-tests/full"
                        if composite is not None or selected == all_tests
                        else "repository-tests/selected"
                    )
                    binding = receipt_binding(
                        candidate,
                        tested_view,
                        selected,
                        policy_digest,
                        component_id,
                        REPO if options.provider_hard else candidate_root,
                        environment=component_environment,
                        composite_identity=(
                            composite["identity"] if composite is not None else None
                        ),
                    )
                    receipt = reusable_full_receipt(binding, component_id, options)
                    if receipt is None and composite is None:
                        cached_binding = latest_reusable_full_receipt_binding(
                            candidate, options
                        )
                        current_full_identity = receipt_binding(
                            candidate,
                            tested_view,
                            (),
                            policy_digest,
                            "repository-tests/full",
                            candidate_root,
                            environment=component_environment,
                            composite_identity=None,
                        )
                        if cached_binding is not None and (
                            full_receipt_current_identity_matches(
                                cached_binding, current_full_identity
                            )
                        ):
                            receipt_plan_root = scratch_root / "full-receipt-plan"
                            receipt_plan_root.mkdir()
                            receipt_composite = composite_test_plan(
                                candidate,
                                candidate_root,
                                tested_view,
                                receipt_plan_root,
                            )
                            receipt_tests = tuple(
                                sorted(
                                    set(receipt_composite["floor_tests"]).union(
                                        receipt_composite["supplemental_tests"]
                                    )
                                )
                            )
                            expected_full_binding = receipt_binding(
                                candidate,
                                tested_view,
                                receipt_tests,
                                policy_digest,
                                "repository-tests/full",
                                candidate_root,
                                environment=component_environment,
                                composite_identity=receipt_composite["identity"],
                            )
                            if cached_binding == expected_full_binding:
                                receipt = reusable_full_receipt(
                                    expected_full_binding,
                                    "repository-tests/full",
                                    options,
                                )
                                if receipt is not None:
                                    binding = expected_full_binding
                                    component_id = "repository-tests/full"
                                    selected = receipt_tests
                                    deferred = ()
                                    report["selected"] = list(selected)
                                    report["deferred"] = []
                                    report["test_plan"] = receipt_composite[
                                        "identity"
                                    ]
                    if receipt is not None:
                        components.append(
                            ComponentResult(
                                component_id,
                                "pass",
                                "reused",
                                0.0,
                                (),
                                f"reused {binding['binding_digest']}",
                            )
                        )
                    else:
                        runner = (
                            AUTOMATION / "run_tests.py"
                            if options.provider_hard
                            else candidate_root / "automation/run_tests.py"
                        )

                        def execute_tests(lane_id, view_root, tests):
                            command = [
                                sys.executable,
                                "-I",
                                "-S",
                                str(runner),
                                "--view-root",
                                str(view_root),
                            ]
                            if options.provider_hard:
                                command.append("--provider-hard")
                            for test in tests:
                                command.extend(("--test-file", test))
                            return guarded_component(
                                lane_id,
                                command,
                                execution_deadline,
                                cwd=view_root,
                                require_strong_containment=options.provider_hard,
                            )

                        if composite is None:
                            result = execute_tests(
                                component_id, candidate_root, selected
                            )
                            components.append(result)
                            receipt_result = result
                        else:
                            floor_result = execute_tests(
                                "repository-tests/base-pinned-floor",
                                composite["floor_root"],
                                composite["floor_tests"],
                            )
                            components.append(floor_result)
                            supplemental_result = None
                            if (
                                floor_result.outcome == "pass"
                                and composite["supplemental_tests"]
                            ):
                                supplemental_result = execute_tests(
                                    "repository-tests/candidate-supplemental",
                                    composite["supplemental_root"],
                                    composite["supplemental_tests"],
                                )
                                components.append(supplemental_result)
                            lanes_passed = floor_result.outcome == "pass" and (
                                supplemental_result is None
                                or supplemental_result.outcome == "pass"
                            )
                            receipt_result = ComponentResult(
                                component_id,
                                "pass" if lanes_passed else "incomplete",
                                "executed" if lanes_passed else "none",
                                0.0,
                                (),
                                (
                                    "base-pinned floor and candidate supplemental lanes passed; "
                                    f"plan {composite['identity']['digest']}"
                                    if lanes_passed
                                    else "composite full-test lanes did not all pass"
                                ),
                            )
                            if lanes_passed:
                                components.append(receipt_result)
                        if (
                            receipt_result.outcome == "pass"
                            and composite is not None
                            and local_receipts_allowed(options)
                        ):
                            pending_receipt_binding = binding
                elif "repository-tests/full" in required_critical:
                    components.append(
                        ComponentResult(
                            "repository-tests/full",
                            "incomplete",
                            "none",
                            0.0,
                            (),
                            "critical full-test evidence is unavailable because no tests were discovered",
                        )
                    )
                else:
                    components.append(
                        ComponentResult(
                            "repository-tests/selected",
                            "pass",
                            "none",
                            0.0,
                            (),
                            "no changed path mapped to a routine test",
                        )
                    )

            if (
                time.monotonic() >= terminal_decision_deadline
                and not any(result.outcome == "incomplete" for result in components)
            ):
                components.append(
                    ComponentResult(
                        "repository-tests/reporting-reserve",
                        "incomplete",
                        "none",
                        0.0,
                        (),
                        "component work consumed the interval reserved for terminal decision",
                    )
                )
            report["components"] = [result.as_dict() for result in components]
            def terminal_stability():
                if not candidate_stable():
                    return False
                if pending_receipt_binding is None:
                    return True
                return (
                    pending_receipt_binding.get("controller_closure")
                    == controller_closure()
                )

            completed, stable = _bounded_json_call(
                terminal_stability, final_validation_deadline
            )
            final_candidate_stable = completed and stable is True
            apply_gate_outcome(
                report,
                options.gate,
                components,
                selected,
                deferred,
                critical,
                required_critical,
                final_candidate_stable,
            )
            if not completed:
                report["reason"] = (
                    "candidate stability could not be verified before the terminal deadline"
                )
            report["evidence"] = (
                "executed"
                if any(result.evidence == "executed" for result in components)
                else "reused"
                if any(result.evidence == "reused" for result in components)
                else "none"
            )
            return emit_report(
                report,
                target,
                maximum,
                policy_digest,
                options,
                receipt_binding_value=(
                    pending_receipt_binding if final_candidate_stable else None
                ),
                receipt_stable=final_candidate_stable,
                component_environment=component_environment,
                terminal_decision_deadline=terminal_decision_deadline,
            )
    except getattr(test_gate_config, "ConfigError", ()) as error:
        report["outcome"] = "invalid"
        report["reason"] = str(error)
        return emit_report(
            report, terminal_decision_deadline=terminal_decision_deadline
        )
    except (GateError, test_manifest.ManifestError, OSError, ValueError) as error:
        report["outcome"] = "error"
        report["reason"] = str(error)
        return emit_report(
            report, terminal_decision_deadline=terminal_decision_deadline
        )
    except Exception as error:  # keep unexpected operational failures machine-visible
        report["outcome"] = "error"
        report["reason"] = f"unexpected gate error: {error}"
        return emit_report(
            report, terminal_decision_deadline=terminal_decision_deadline
        )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
