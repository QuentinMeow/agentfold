#!/usr/bin/env python3
"""Freeze one gate candidate and dispatch its staged controller in isolation.

The executable path intentionally contains only standard-library code.  Reserved
automatic-boundary syntax is rejected from raw argv before this file reads Git,
configuration, candidate bytes, local reports, receipts, or budget state.
"""

import hashlib
import json
import math
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


REPORT_SCHEMA = "agentfold.test-gate-report/v3"
_HANDOFF_ENV = "AGENTFOLD_GATE_HANDOFF"
_SOURCE_REPO_ENV = "AGENTFOLD_GATE_SOURCE_REPO"
_EXECUTION_ROOT_ENV = "AGENTFOLD_GATE_EXECUTION_ROOT"
_BOOTSTRAP_CLOCK_GETTIME_SOURCE = "clock_gettime:CLOCK_MONOTONIC"
_BOOTSTRAP_OS_TIMES_SOURCE = "os.times:elapsed"
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


def _static_result(outcome, reason, incomplete=()):
    report = {
        "schema": REPORT_SCHEMA,
        "gate_id": "final",
        "outcome": outcome,
        "exit_code": 1 if outcome == "blocked-incomplete" else 2,
        "evidence": "none",
        "evidence_authority": "cooperative-same-interpreter",
        "controlled_completion": False,
        "enforcement_eligible": False,
        "enforcement": "not-enforced",
        "terminalized_pass": False,
        "reason": reason,
        "incomplete": list(incomplete),
    }
    sys.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.write(
        "test gate: final\n"
        "outcome: {outcome}\n"
        "reason: {reason}\n"
        "machine report: not written (pre-import bootstrap decision)\n".format(
            outcome=outcome, reason=reason
        )
    )
    sys.stdout.flush()
    return report["exit_code"]


def _git(repository, arguments, environment=None):
    result = subprocess.run(
        ["git", *arguments],
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


def _freeze(repository, arguments, temporary_root, started, started_source):
    frozen_index = temporary_root / "candidate.index"
    staged = "--staged" in arguments
    gate = arguments[0] if arguments else ""
    if staged:
        base_revision = _bootstrap_resolve_commit(repository, "HEAD")
        _copy_index(_selected_index(repository), frozen_index)
        candidate_revision = ""
        kind = "staged-index"
    else:
        if gate != "final":
            raise RuntimeError("routine candidate must be staged")
        candidate_name = _option(arguments, "--candidate-revision")
        base_name = _option(arguments, "--base-revision")
        if not candidate_name:
            status = _git(
                repository, ["status", "--porcelain=v1", "--untracked-files=all"]
            )
            if status:
                raise RuntimeError(
                    "explicit final without a revision range requires a clean checkout"
                )
            candidate_name = "HEAD"
        candidate_revision = _bootstrap_resolve_commit(repository, candidate_name)
        base_revision = _bootstrap_resolve_commit(
            repository, base_name or candidate_revision + "^"
        )
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(frozen_index)
        _git(repository, ["read-tree", candidate_revision], environment)
        kind = "revision-range"

    frozen_semantic = _semantic_index(repository, frozen_index)
    records = _index_records(repository, frozen_index)
    snapshot = temporary_root / "snapshot"
    snapshot.mkdir(mode=0o700)
    environment = os.environ.copy()
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
        "schema": "agentfold.test-gate-bootstrap/v1",
        "started_monotonic": started,
        "started_monotonic_source": started_source,
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


def _dispatch(arguments):
    started_source, started = _bootstrap_monotonic_start()
    repository = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="agentfold-gate-snapshot-") as temporary:
        temporary_root = Path(temporary).resolve()
        temporary_root.chmod(0o700)
        handoff = _freeze(
            repository, arguments, temporary_root, started, started_source
        )
        handoff_path = temporary_root / "handoff.json"
        with handoff_path.open("x", encoding="utf-8") as stream:
            json.dump(handoff, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        handoff_path.chmod(0o400)
        environment = os.environ.copy()
        environment[_HANDOFF_ENV] = str(handoff_path)
        environment[_SOURCE_REPO_ENV] = handoff["source_repository"]
        environment[_EXECUTION_ROOT_ENV] = handoff["execution_root"]
        controller = Path(handoff["execution_root"]) / "automation/test_gate_controller.py"
        try:
            result = subprocess.run(
                ["python3", "-I", "-S", str(controller), *arguments],
                cwd=handoff["execution_root"],
                env=environment,
            )
        finally:
            _unseal_snapshot(Path(handoff["execution_root"]))
        return result.returncode


if __name__ == "__main__":
    if _reserved_boundary_requested(sys.argv[1:]):
        raise SystemExit(
            _static_result(
                "blocked-incomplete",
                "automatic final transitions are unavailable: the repository has no "
                "controlled external completion oracle and independently controlled publisher",
                (
                    "controlled-external-completion-oracle",
                    "independently-controlled-publisher",
                ),
            )
        )
    try:
        raise SystemExit(_dispatch(sys.argv[1:]))
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(_static_result("error", str(error)))
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
