#!/usr/bin/env python3
"""File or refresh nonblocking investigation work for a test-gate budget breach.

The filer is deliberately best-effort: every operational failure is returned as a
machine-readable ``FilingResult`` and never raises into the gate that called it.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import errno
import hashlib
import json
import os
import re
import shlex
import stat
import sys
import time
from collections.abc import Mapping
from pathlib import Path

try:  # POSIX advisory process coordination.
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - exercised by capability simulation
    _fcntl = None

try:  # Windows advisory process coordination.
    import msvcrt as _msvcrt
except ImportError:  # pragma: no cover - exercised by capability simulation
    _msvcrt = None


GENERATOR = "automation/file_test_budget_task.py"
JOURNAL_NAME = "timing-evidence.jsonl"
JOURNAL_SCHEMA = "agentfold.test-budget-evidence/v1"
MAX_JOURNAL_RECORD_BYTES = 32768
TASK_STATUSES = ("0_backlog", "1_in-progress", "2_blocked", "3_in-review")
TASK_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
DIGEST_ID = re.compile(
    r"^(?:(?:sha1|sha256|sha512|blake2b):)?(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64}|[0-9a-fA-F]{128})$"
)
IDENTITY_VALUE = re.compile(r"^[a-z0-9][a-z0-9._/-]{0,159}$")
SENSITIVE_LABEL = re.compile(
    r"(?:^|[._/-])(?:auth|cookie|credential|password|secret|session|token)(?:[._/-]|$)"
)
SAFE_TRIGGERS = frozenset(
    ("explicit", "manual", "merge", "pre-commit", "pull-request", "task-review")
)
ACTION_LABELS = {
    "check_core_scope.py": "core-scope",
    "pre-commit": "pre-commit",
    "pytest": "pytest",
    "reconcile.py": "reconciler",
    "run_test_gate.py": "test-gate",
    "run_tests.py": "test-runner",
    "unittest": "unittest",
}
PYTHON_EXECUTABLE = re.compile(r"^(?:python|python\d+(?:\.\d+)*)$")


@dataclasses.dataclass(frozen=True)
class FilingResult(Mapping):
    """Stable result surface used by local gates and thin provider adapters."""

    disposition: str
    task_path: str | None
    request_path: str | None
    finding_key: str
    message: str
    mutated: bool

    def as_dict(self):
        return dataclasses.asdict(self)

    def __getitem__(self, key):
        return self.as_dict()[key]

    def __iter__(self):
        return iter(self.as_dict())

    def __len__(self):
        return 6


@dataclasses.dataclass(frozen=True)
class _Occurrence:
    schema_id: str
    gate_id: str
    config_slot: str
    actual_seconds: float
    target_seconds: float
    components: dict[str, float]
    candidate: str
    receipt: str
    command: str
    trigger: str
    environment: dict[str, str]


@dataclasses.dataclass(frozen=True)
class _Record:
    status: str
    task_dir: Path
    text: str
    digest: str

    @property
    def task_id(self):
        return self.task_dir.name


@dataclasses.dataclass(frozen=True)
class _JournalSnapshot:
    device: int
    inode: int
    data: bytes
    records: tuple
    directory_signature: tuple


class _PublicationFailure(Exception):
    """Canonical publication failed, possibly after creating durable paths."""

    def __init__(self, cause, mutated, task_path=None, request_path=None):
        super().__init__(str(cause))
        self.cause = cause
        self.mutated = bool(mutated)
        self.task_path = task_path
        self.request_path = request_path


def _descriptor_signature(descriptor):
    metadata = os.fstat(descriptor)
    return metadata.st_dev, metadata.st_ino


def _require_descriptor_topology():
    required = (
        os.name == "posix",
        bool(getattr(os, "O_NOFOLLOW", 0)),
        bool(getattr(os, "O_DIRECTORY", 0)),
        os.open in getattr(os, "supports_dir_fd", ()),
        os.mkdir in getattr(os, "supports_dir_fd", ()),
        os.rmdir in getattr(os, "supports_dir_fd", ()),
        os.listdir in getattr(os, "supports_fd", ()),
    )
    if not all(required):
        raise OSError(
            getattr(errno, "ENOTSUP", errno.EPERM),
            "safe repository access requires POSIX descriptor-relative no-follow support",
        )


def _relative_parts(relative):
    relative = Path(relative)
    if relative.is_absolute():
        raise ValueError("repository path must be relative")
    parts = relative.parts
    if any(part in ("", ".", "..") or "/" in part for part in parts):
        raise ValueError("repository path contains an unsafe component")
    return parts


class _PinnedDirectory:
    """One repository directory reached through a pinned no-follow chain."""

    def __init__(self, repository, relative, descriptor, signatures):
        self.repository = repository
        self.relative = Path(relative)
        self.descriptor = descriptor
        self.signatures = tuple(signatures)

    def close(self):
        if self.descriptor is not None:
            descriptor, self.descriptor = self.descriptor, None
            os.close(descriptor)

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()

    def verify(self):
        _verify_pinned_directory(self)


class _PinnedRepository:
    """Repository root and all durable mutation state for one filing attempt."""

    def __init__(self, root):
        _require_descriptor_topology()
        self.root = Path(root)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        self.descriptor = os.open(str(self.root), flags)
        self.signature = _descriptor_signature(self.descriptor)
        self.mutated = False

    def close(self):
        if self.descriptor is not None:
            descriptor, self.descriptor = self.descriptor, None
            os.close(descriptor)

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()

    def verify(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(str(self.root), flags)
        try:
            if _descriptor_signature(descriptor) != self.signature:
                raise OSError(
                    getattr(errno, "ESTALE", errno.EIO),
                    "repository root changed after it was pinned",
                )
        finally:
            os.close(descriptor)

    def open_dir(self, relative=Path(), *, create=False):
        parts = _relative_parts(relative)
        self.verify()
        descriptor = os.dup(self.descriptor)
        signatures = []
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        try:
            for part in parts:
                try:
                    child = os.open(part, flags, dir_fd=descriptor)
                except FileNotFoundError:
                    if not create:
                        raise
                    os.mkdir(part, mode=0o755, dir_fd=descriptor)
                    self.mutated = True
                    child = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
                signatures.append(_descriptor_signature(descriptor))
            pinned = _PinnedDirectory(self, Path(*parts), descriptor, signatures)
            pinned.verify()
            return pinned
        except Exception:
            with contextlib.suppress(OSError):
                os.close(descriptor)
            raise

    def listdir(self, relative, *, missing_ok=False):
        try:
            directory = self.open_dir(relative)
        except FileNotFoundError:
            if missing_ok:
                return ()
            raise
        with directory:
            names = tuple(sorted(os.listdir(directory.descriptor)))
            directory.verify()
            return names

    def read_bytes(self, relative):
        relative = Path(relative)
        with self.open_dir(relative.parent) as directory:
            descriptor, _metadata = _open_regular_at(
                directory, relative.name, os.O_RDONLY
            )
            try:
                before = os.fstat(descriptor)
                data = _read_descriptor_bytes(descriptor)
                after = os.fstat(descriptor)
                if (
                    _journal_stat_signature(before) != _journal_stat_signature(after)
                    or after.st_size != len(data)
                ):
                    raise ValueError("repository file changed while it was being read")
                directory.verify()
                return data
            finally:
                os.close(descriptor)

    def read_text(self, relative):
        return self.read_bytes(relative).decode("utf-8")


def _verify_pinned_directory(directory):
    repository = directory.repository
    repository.verify()
    descriptor = os.dup(repository.descriptor)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    observed = []
    try:
        for part in _relative_parts(directory.relative):
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
            observed.append(_descriptor_signature(descriptor))
        if (
            tuple(observed) != directory.signatures
            or _descriptor_signature(directory.descriptor)
            != (observed[-1] if observed else repository.signature)
        ):
            raise OSError(
                getattr(errno, "ESTALE", errno.EIO),
                "repository directory chain changed after it was pinned",
            )
    finally:
        os.close(descriptor)


def _open_regular_at(directory, name, flags, mode=0o644, mutation_owner=None):
    if tuple(Path(name).parts) != (name,) or name in ("", ".", ".."):
        raise ValueError("repository filename contains an unsafe component")
    flags |= os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(name, flags, mode, dir_fd=directory.descriptor)
    if mutation_owner is not None and flags & os.O_CREAT:
        mutation_owner.mutated = True
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError(errno.EINVAL, "repository file is not a regular file")
    except Exception:
        with contextlib.suppress(OSError):
            os.close(descriptor)
        raise
    return descriptor, metadata


def _value(source, *names, default=None):
    if isinstance(source, Mapping):
        for name in names:
            if name in source:
                return source[name]
    else:
        for name in names:
            if hasattr(source, name):
                return getattr(source, name)
    return default


def _plain(value, limit=240):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = " ".join(str(part) for part in value)
    value = " ".join(str(value).split())
    return value[:limit]


def _validated_identity(value, name, limit=160):
    value = _plain(value, limit)
    if not IDENTITY_VALUE.fullmatch(value) or SENSITIVE_LABEL.search(value):
        raise ValueError(f"{name} must be a bounded lowercase identifier")
    return value


def _validated_digest(value, name):
    value = _plain(value, 140)
    if not DIGEST_ID.fullmatch(value):
        raise ValueError(f"{name} must be a bounded hexadecimal digest identifier")
    return value.lower()


def _positive_number(value, name):
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a number") from error
    if not (number >= 0 and number < float("inf")):
        raise ValueError(f"{name} must be a finite nonnegative number")
    return number


def _sanitize_environment(environment, repo):
    if not isinstance(environment, Mapping):
        return {}
    sanitized = {}
    implementation = environment.get("python_implementation")
    if implementation in {"CPython", "PyPy", "GraalPython", "Jython", "IronPython"}:
        sanitized["python_implementation"] = implementation
    python_version = _plain(environment.get("python_version"), 32)
    match = re.fullmatch(r"\d+\.\d+(?:\.\d+)?(?:[A-Za-z0-9.+-]{0,16})", python_version)
    if match:
        sanitized["python_version"] = match.group(0)
    git_version = _plain(environment.get("git_version"), 64)
    match = re.fullmatch(r"git version ([0-9A-Za-z.+-]{1,40})", git_version)
    if match:
        sanitized["git_version"] = match.group(1)
    elif git_version == "unavailable":
        sanitized["git_version"] = "unavailable"
    return sanitized


def _sanitized_action(command):
    """Reduce untrusted argv to a fixed action label; never retain arguments."""
    if isinstance(command, (list, tuple)):
        tokens = [str(token) for token in command]
    else:
        try:
            tokens = shlex.split(str(command or ""))
        except ValueError:
            tokens = []
    if not tokens:
        return "not-reported"
    basenames = [Path(token).name for token in tokens[:3] if token and not token.startswith("-")]
    for basename in basenames:
        if basename in ACTION_LABELS:
            return ACTION_LABELS[basename]
    if basenames and PYTHON_EXECUTABLE.fullmatch(basenames[0]):
        return "python"
    return "unrecognized-action"


def _sanitized_trigger(trigger):
    trigger = _plain(trigger, 32)
    return trigger if trigger in SAFE_TRIGGERS else "unrecognized-trigger"


def _normalize_occurrence(source, repo):
    schema_id = _validated_identity(
        _value(source, "schema_id", "schema", "schema_version"), "schema_id", 80
    )
    gate_id = _validated_identity(
        _value(source, "gate_id", "gate", "name"), "gate_id", 80
    )
    config_slot = _validated_identity(
        _value(source, "config_slot", "config_slot_identity", "slot"),
        "config_slot",
        160,
    )
    candidate = _validated_digest(
        _value(source, "candidate", "candidate_fingerprint"), "candidate"
    )
    receipt = _validated_digest(
        _value(source, "receipt", "receipt_id", "receipt_digest"), "receipt"
    )
    raw_components = _value(source, "components", "component_timings", default={})
    if raw_components is None:
        raw_components = {}
    if not isinstance(raw_components, Mapping):
        raise ValueError("components must be a mapping")
    components = {}
    for raw_name, raw_value in raw_components.items():
        name = _validated_identity(raw_name, "component name", 80)
        components[name] = _positive_number(raw_value, f"component {name}")
    return _Occurrence(
        schema_id=schema_id,
        gate_id=gate_id,
        config_slot=config_slot,
        actual_seconds=_positive_number(
            _value(source, "actual_seconds", "actual", "elapsed_seconds"),
            "actual_seconds",
        ),
        target_seconds=_positive_number(
            _value(source, "target_seconds", "target", "budget_seconds"),
            "target_seconds",
        ),
        components=dict(sorted(components.items())),
        candidate=candidate,
        receipt=receipt,
        command=_sanitized_action(_value(source, "command", default="")),
        trigger=_sanitized_trigger(_value(source, "trigger", default="")),
        environment=_sanitize_environment(
            _value(source, "environment", "env", default={}), repo
        ),
    )


def finding_identity(occurrence):
    """Return stable finding identity independent of report/evidence schema versions."""
    return hashlib.sha256(
        (occurrence.gate_id + "\0" + occurrence.config_slot).encode("utf-8")
    ).hexdigest()


def _slug(value, limit=32):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "gate"
    return slug[:limit].rstrip("-")


def finding_key(occurrence):
    digest = finding_identity(occurrence)[:12]
    return (
        f"test-budget-{_slug(occurrence.gate_id)}-"
        f"{_slug(occurrence.config_slot)}-{digest}"
    )


def _result(disposition, key, message, task=None, request=None, mutated=False, repo=None):
    def relative(path):
        if path is None:
            return None
        try:
            return path.relative_to(repo).as_posix()
        except ValueError:
            return str(path)

    return FilingResult(
        disposition, relative(task), relative(request), key, message, mutated
    )


def _state_for(occurrence, previous=None):
    previous = previous or {}
    old_worst = float(previous.get("worst_actual_seconds", -1))
    worst_components = {}
    for name, value in previous.get("worst_components", {}).items():
        try:
            safe_name = _validated_identity(name, "component name", 80)
            worst_components[safe_name] = _positive_number(value, "component timing")
        except (TypeError, ValueError):
            continue
    for name, value in occurrence.components.items():
        worst_components[name] = max(value, worst_components.get(name, value))
    return {
        "count": int(previous.get("count", 0)) + 1,
        "latest_actual_seconds": occurrence.actual_seconds,
        "worst_actual_seconds": max(occurrence.actual_seconds, old_worst),
        "target_seconds": occurrence.target_seconds,
        "latest_components": occurrence.components,
        "worst_components": dict(sorted(worst_components.items())),
        "candidate": occurrence.candidate,
        "receipt": occurrence.receipt,
        "command": occurrence.command,
        "trigger": occurrence.trigger,
        "environment": occurrence.environment,
    }


def _field(text, name):
    match = re.search(rf"^\*\*{re.escape(name)}:\*\*\s*(.*?)\s*$", text, re.M)
    return match.group(1) if match else ""


def _generated_record(record, identity):
    return (
        _field(record.text, "Generated by") == GENERATOR
        and _field(record.text, "Finding identity") == f"sha256:{identity}"
        and _field(record.text, "Timing evidence") == f"`{JOURNAL_NAME}`"
    )


def _generated_backlog_request(repository, record, request_relative):
    if request_relative is None:
        return False
    try:
        text = repository.read_text(request_relative)
        task_rel = record.task_dir.relative_to(repository.root).as_posix()
    except (OSError, UnicodeError, ValueError):
        return False
    return (
        _field(text, "Status") == "open"
        and _field(text, "Filed")
        == f"{record.task_id[:10]}, by test-budget filer, from task `{record.task_id}`"
        and _field(text, "Full context") == f"`{task_rel}/task.md`"
        and _field(text, "Request kind") == "task-pickup"
    )


def _scan(repository, identity, include_done=True):
    records = []
    statuses = TASK_STATUSES + (("4_done",) if include_done else ())
    for status in statuses:
        folder_relative = Path("tasks") / status
        for task_id in repository.listdir(folder_relative, missing_ok=True):
            task_relative = folder_relative / task_id / "task.md"
            try:
                text = repository.read_text(task_relative)
            except (FileNotFoundError, NotADirectoryError):
                continue
            except UnicodeError:
                continue
            if _field(text, "Finding identity") != f"sha256:{identity}":
                continue
            task_dir = repository.root / folder_relative / task_id
            records.append(
                _Record(
                    status,
                    task_dir,
                    text,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
            )
    return tuple(records)


def _records_signature(records):
    return tuple((record.status, str(record.task_dir), record.digest) for record in records)


def _validate_templates(repository):
    task = repository.read_text("templates/task/task.md")
    request = repository.read_text("templates/queue/request.md")
    for token in ("**Claimed-by:**", "**Filed:**", "**Repository scope:**", "**Queue actions:**"):
        if token not in task:
            raise ValueError(f"task template lacks {token}")
    for token in ("**Status:**", "**Filed:**", "**Action:**", "**Full context:**"):
        if token not in request:
            raise ValueError(f"request template lacks {token}")
    return task, request


def _replace_once(text, pattern, replacement, label, flags=0):
    rendered, count = re.subn(pattern, lambda _match: replacement, text, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"canonical template lacks one replaceable {label}")
    return rendered


def _replace_section(text, heading, next_heading, body):
    pattern = (
        rf"(?ms)^## {re.escape(heading)}\n.*?"
        rf"(?=^## {re.escape(next_heading)}\n)"
    )
    return _replace_once(
        text,
        pattern,
        f"## {heading}\n\n{body.rstrip()}\n\n",
        f"{heading} section",
    )


def _render_task(template, occurrence, key, task_id, request_rel, prior_task_id=None):
    identity = finding_identity(occurrence)
    metadata = (
        f"**Generated by:** {GENERATOR}\n"
        f"**Finding identity:** sha256:{identity}\n"
        f"**Finding key:** {key}\n"
        f"**Timing evidence:** `{JOURNAL_NAME}`"
    )
    if prior_task_id:
        metadata += f"\n**Recurs after:** `{prior_task_id}`"
    rendered = _replace_once(template, r"(?m)^# .*?$", f"# Investigate the {occurrence.gate_id} test-gate time-budget regression", "title")
    rendered = _replace_once(rendered, r"(?m)^\*\*Claimed-by:\*\*.*$", "**Claimed-by:** unclaimed", "Claimed-by field")
    rendered = _replace_once(rendered, r"(?m)^\*\*Mode:\*\*.*\n", "", "optional Mode field")
    rendered = _replace_once(rendered, r"(?m)^\*\*Filed:\*\*.*$", f"**Filed:** {task_id[:10]}, by test-budget filer, from gate `{occurrence.gate_id}`", "Filed field")
    rendered = _replace_once(rendered, r"(?m)^\*\*Parent:\*\*.*$", "**Parent:** none", "Parent field")
    rendered = _replace_once(rendered, r"(?m)^\*\*Repository scope:\*\*.*$", "**Repository scope:** core", "Repository scope field")
    rendered = _replace_once(
        rendered,
        r"(?m)^\*\*Queue actions:\*\*.*$",
        f"**Queue actions:** `{request_rel}`\n{metadata}",
        "Queue actions field",
    )
    rendered = _replace_section(
        rendered,
        "Goal",
        "Acceptance criteria",
        f"Find and reduce the measured `{occurrence.gate_id}` gate regression without "
        "weakening its checks. The task body remains stable after filing; sanitized "
        f"append-only occurrences live in `{JOURNAL_NAME}` so actor edits are never replaced.",
    )
    rendered = _replace_section(
        rendered,
        "Acceptance criteria",
        "Links",
        f"- [ ] The `{occurrence.gate_id}` gate completes within its configured target on "
        "a representative candidate, with actual component timings recorded.\n"
        "- [ ] The functional test obligation remains unchanged or any intentional policy "
        "change is reviewed through its owning task.\n"
        "- [ ] Focused regression coverage and real verification output explain the repaired "
        "bottleneck.",
    )
    rendered = _replace_once(
        rendered,
        r"(?ms)^## Links\n.*\Z",
        "## Actor notes\n\nNone yet.\n\n"
        "## Links\n\n"
        "- Test-gate policy: `agentfold.toml`\n"
        f"- Append-only timing evidence: `{JOURNAL_NAME}`\n"
        f"- Finding key: `{key}`\n",
        "Links section",
    )
    return rendered


def _render_request(template, occurrence, task_id, task_rel):
    rendered = _replace_once(template, r"(?m)^# .*?$", f"# Pick up the {occurrence.gate_id} test-budget investigation", "title")
    values = {
        "Status": "open",
        "Filed": f"{task_id[:10]}, by test-budget filer, from task `{task_id}`",
        "Action": "Claim the time-budget investigation, preserve its generated evidence, and remove this pickup request in the same coordination commit.",
        "Full context": f"`{task_rel}/task.md`",
        "Resolution evidence": f"`tasks/1_in-progress/{task_id}/task.md`",
    }
    for name, value in values.items():
        rendered = _replace_once(rendered, rf"(?m)^\*\*{re.escape(name)}:\*\*.*$", f"**{name}:** {value}", f"{name} field")
    rendered = _replace_once(
        rendered,
        r"(?ms)<!-- Replace this comment with exactly one block matching the filename:.*?-->",
        "**Request kind:** task-pickup\n"
        "**If unanswered:** The investigation remains unclaimed in backlog; the gate result and its functional exit status are unchanged.",
        "delivery block",
    )
    rendered = _replace_section(
        rendered,
        "What you need to know",
        "Done when",
        f"The `{occurrence.gate_id}` gate exceeded the target stored in "
        f"`{occurrence.config_slot}`. The linked task owns the timing evidence and updates.",
    )
    rendered = _replace_once(
        rendered,
        r"(?ms)^## Done when\n.*\Z",
        "## Done when\n\nThe task has a claimant, has moved to `1_in-progress`, and this request and its `Queue actions` link have been removed in the claim commit.\n",
        "Done when section",
    )
    return rendered


def _task_id(repository, occurrence, today, done):
    base = f"{today}-investigate-{_slug(occurrence.gate_id, 24)}-test-budget-{finding_identity(occurrence)[:10]}"
    used = {record.task_id for record in done}
    all_statuses = TASK_STATUSES + ("4_done",)
    for status in all_statuses:
        used.update(repository.listdir(Path("tasks") / status, missing_ok=True))
    if base not in used:
        return base
    suffix = 1
    while f"{base}-r{suffix}" in used:
        suffix += 1
    return f"{base}-r{suffix}"


def _recurrence_order(record):
    match = re.search(r"-r(\d+)$", record.task_id)
    recurrence = int(match.group(1)) if match else 0
    return record.task_id[:10], recurrence, record.task_id


def _journal_line(identity, state):
    payload = {
        "schema": JOURNAL_SCHEMA,
        "finding_identity": "sha256:" + identity,
        "state": state,
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_JOURNAL_RECORD_BYTES:
        raise ValueError("timing evidence record exceeds the bounded journal size")
    return encoded


def _parse_journal_bytes(data, identity):
    records = []
    for number, raw_line in enumerate(data.splitlines(), 1):
        if not raw_line:
            continue
        try:
            record = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError(f"timing evidence journal line {number} is invalid") from error
        if (
            not isinstance(record, dict)
            or record.get("schema") != JOURNAL_SCHEMA
            or record.get("finding_identity") != "sha256:" + identity
            or not isinstance(record.get("state"), dict)
        ):
            raise ValueError(f"timing evidence journal line {number} has the wrong identity or schema")
        records.append(record["state"])
    return tuple(records)


def _open_pinned_journal(repository, relative, flags):
    relative = Path(relative)
    directory = repository.open_dir(relative.parent)
    try:
        descriptor, metadata = _open_regular_at(directory, relative.name, flags)
        directory.verify()
        return descriptor, metadata, directory
    except Exception:
        directory.close()
        raise


def _journal_stat_signature(metadata):
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _read_descriptor_bytes(descriptor):
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks = []
    while True:
        chunk = os.read(descriptor, 64 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _snapshot_open_journal(descriptor, identity, directory_signature=()):
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode):
        raise OSError(errno.EINVAL, "timing evidence journal is not a regular file")
    data = _read_descriptor_bytes(descriptor)
    after = os.fstat(descriptor)
    if (
        _journal_stat_signature(before) != _journal_stat_signature(after)
        or after.st_size != len(data)
    ):
        raise ValueError("timing evidence journal changed while it was being read")
    return _JournalSnapshot(
        after.st_dev,
        after.st_ino,
        data,
        _parse_journal_bytes(data, identity),
        tuple(directory_signature),
    )


def _read_journal_snapshot(repository, relative, identity):
    try:
        descriptor, _metadata, directory = _open_pinned_journal(
            repository, relative, os.O_RDONLY
        )
    except FileNotFoundError:
        return None
    try:
        snapshot = _snapshot_open_journal(
            descriptor, identity, directory.signatures
        )
        directory.verify()
        return snapshot
    finally:
        os.close(descriptor)
        directory.close()


def _read_journal(repository, relative, identity):
    snapshot = _read_journal_snapshot(repository, relative, identity)
    return () if snapshot is None else snapshot.records


def _same_journal(left, right):
    return (
        left.device == right.device
        and left.inode == right.inode
        and left.data == right.data
        and left.directory_signature == right.directory_signature
    )


def _append_journal_record(repository, relative, identity, state, expected):
    """Append one bounded record without ever replacing actor-owned task bytes.

    The append descriptor is validated against the exact snapshot used to prepare
    ``state`` before any write. Once a write is attempted, every uncertain outcome is
    reported as a mutation and no canonical pathname is removed or replaced.
    """
    if not isinstance(expected, _JournalSnapshot):
        raise ValueError("timing evidence append requires a validated journal snapshot")
    line = _journal_line(identity, state)
    descriptor, _opened, directory = _open_pinned_journal(
        repository, relative, os.O_RDWR | os.O_APPEND
    )
    write_attempted = False
    result = None
    observed = None
    body_error = None
    try:
        current = _snapshot_open_journal(
            descriptor, identity, directory.signatures
        )
        if not _same_journal(current, expected):
            result = False
        else:
            directory.verify()
            write_attempted = True
            repository.mutated = True
            written = os.write(descriptor, line)
            if written != len(line):
                raise OSError("short atomic append to timing evidence journal")
            os.fsync(descriptor)
            observed = _snapshot_open_journal(
                descriptor, identity, directory.signatures
            )
            if (
                observed.device != expected.device
                or observed.inode != expected.inode
                or observed.data != expected.data + line
                or not observed.records
                or observed.records[-1] != state
            ):
                raise ValueError("timing evidence append could not be verified exactly")
            result = True
    except Exception as error:
        body_error = error
    close_error = None
    try:
        os.close(descriptor)
    except OSError as error:
        close_error = error
    try:
        directory.close()
    except OSError as error:
        if close_error is None:
            close_error = error

    if body_error is not None:
        if write_attempted and not isinstance(body_error, _PublicationFailure):
            raise _PublicationFailure(body_error, True) from body_error
        raise body_error
    if close_error is not None:
        if write_attempted:
            raise _PublicationFailure(close_error, True) from close_error
        raise close_error
    if result is False:
        return False

    try:
        current = _read_journal_snapshot(repository, relative, identity)
        if current is None or observed is None or not _same_journal(current, observed):
            raise ValueError("timing evidence journal path changed after append")
    except Exception as error:
        raise _PublicationFailure(error, True) from error
    return True


def _publish_exclusive_file(repository, parent_relative, name, payload, mode=0o644):
    """Publish bytes exclusively beneath one pinned canonical directory."""
    directory = repository.open_dir(parent_relative)
    descriptor = None
    try:
        directory.verify()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        descriptor, _metadata = _open_regular_at(
            directory, name, flags, mode, repository
        )
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset : offset + 64 * 1024])
            if written <= 0:
                raise OSError("short exclusive write")
            offset += written
        os.fsync(descriptor)
        directory.verify()
    except Exception as error:
        mutated = descriptor is not None or repository.mutated
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
            descriptor = None
        directory.close()
        if isinstance(error, _PublicationFailure):
            raise
        raise _PublicationFailure(error, mutated) from error
    try:
        os.close(descriptor)
    except OSError as error:
        directory.close()
        raise _PublicationFailure(error, True) from error
    directory.close()


def _create_pair(repository, occurrence, key, task_id, prior_task_id):
    task_rel = Path("tasks/0_backlog") / task_id
    request_rel = (
        Path("message-queue/needs-agent/requests")
        / f"non-blocking-pick-up-{task_id[11:]}.md"
    )
    task_path = repository.root / task_rel
    request_path = repository.root / request_rel
    task_template, request_template = _validate_templates(repository)
    initial_state = _state_for(occurrence)
    task_payload = _render_task(
        task_template,
        occurrence,
        key,
        task_id,
        request_rel.as_posix(),
        prior_task_id,
    ).encode("utf-8")
    journal_payload = _journal_line(finding_identity(occurrence), initial_state)
    request_payload = _render_request(
        request_template, occurrence, task_id, task_rel.as_posix()
    ).encode("utf-8")
    task_parent = repository.open_dir(task_rel.parent, create=True)
    task_parent.close()
    request_parent = repository.open_dir(request_rel.parent, create=True)
    request_parent.close()
    mutated = False
    try:
        with repository.open_dir(task_rel.parent) as parent:
            parent.verify()
            os.mkdir(task_id, mode=0o755, dir_fd=parent.descriptor)
            repository.mutated = True
            mutated = True
            parent.verify()
        _publish_exclusive_file(
            repository, task_rel, "task.md", task_payload
        )
        _publish_exclusive_file(
            repository, task_rel, JOURNAL_NAME, journal_payload
        )
        _publish_exclusive_file(
            repository,
            request_rel.parent,
            request_rel.name,
            request_payload,
        )
    except _PublicationFailure as error:
        raise _PublicationFailure(
            error.cause,
            mutated or error.mutated or repository.mutated,
            task_path,
            request_path,
        ) from error
    except Exception as error:
        raise _PublicationFailure(
            error,
            mutated or repository.mutated,
            task_path,
            request_path,
        ) from error
    return task_path, request_path


@contextlib.contextmanager
def _lock(repository, timeout):
    scratch = repository.open_dir("tmp", create=True)
    path_name = ".file-test-budget-task.lock"
    descriptor = None
    directory_lock_name = path_name + ".d"
    owns_directory = False
    deadline = time.monotonic() + max(0.0, timeout)
    try:
        if _fcntl is not None or _msvcrt is not None:
            flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
            try:
                descriptor, _metadata = _open_regular_at(
                    scratch, path_name, flags, mutation_owner=repository
                )
            except FileExistsError:
                descriptor, _metadata = _open_regular_at(
                    scratch, path_name, os.O_RDWR
                )
            scratch.verify()
            if _fcntl is None and _msvcrt is not None:
                if os.fstat(descriptor).st_size == 0:
                    repository.mutated = True
                    os.write(descriptor, b"\0")
                    os.fsync(descriptor)
                os.lseek(descriptor, 0, os.SEEK_SET)
        while True:
            try:
                if _fcntl is not None:
                    _fcntl.flock(descriptor, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
                elif _msvcrt is not None:
                    _msvcrt.locking(descriptor, _msvcrt.LK_NBLCK, 1)
                else:
                    scratch.verify()
                    os.mkdir(directory_lock_name, mode=0o700, dir_fd=scratch.descriptor)
                    repository.mutated = True
                    owns_directory = True
                    scratch.verify()
                break
            except (BlockingIOError, FileExistsError, OSError) as error:
                if isinstance(error, OSError) and getattr(error, "errno", None) not in (
                    None, errno.EACCES, errno.EAGAIN, errno.EEXIST,
                ):
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError("test-budget filer lock timed out")
                time.sleep(min(0.02, max(0.0, deadline - time.monotonic())))
        scratch.verify()
        yield
    finally:
        topology_error = None
        try:
            scratch.verify()
        except OSError as error:
            topology_error = error
        with contextlib.suppress(OSError):
            if descriptor is not None and _fcntl is not None:
                _fcntl.flock(descriptor, _fcntl.LOCK_UN)
            elif descriptor is not None and _msvcrt is not None:
                os.lseek(descriptor, 0, os.SEEK_SET)
                _msvcrt.locking(descriptor, _msvcrt.LK_UNLCK, 1)
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        if owns_directory:
            if topology_error is None:
                with contextlib.suppress(OSError):
                    os.rmdir(directory_lock_name, dir_fd=scratch.descriptor)
        scratch.close()
        if topology_error is not None:
            raise topology_error


def _classify_os_error(error):
    if isinstance(error, PermissionError) or getattr(error, "errno", None) in {
        errno.EACCES,
        errno.EPERM,
        errno.EROFS,
    }:
        return "read-only"
    return "error"


def _request_relative(queue_value):
    match = re.search(r"`([^`]+)`", queue_value)
    if not match:
        return None
    relative = Path(match.group(1))
    parts = _relative_parts(relative)
    if parts[:3] != ("message-queue", "needs-agent", "requests"):
        raise ValueError("generated pickup request path is outside its canonical queue")
    return Path(*parts)


def _file_locked(repository, occurrence, today, key):
    repo = repository.root
    identity = finding_identity(occurrence)
    for _attempt in range(3):
        records = _scan(repository, identity)
        if _records_signature(records) != _records_signature(
            _scan(repository, identity)
        ):
            continue
        open_records = tuple(record for record in records if record.status in TASK_STATUSES)
        done = tuple(record for record in records if record.status == "4_done")
        if len(open_records) > 1:
            return _result(
                "conflict", key,
                f"multiple open tasks carry finding key {key}; no files were changed",
                mutated=False, repo=repo,
            )
        if len(open_records) == 1:
            record = open_records[0]
            task_file = record.task_dir / "task.md"
            queue_value = _field(record.text, "Queue actions")
            try:
                request_relative = _request_relative(queue_value)
            except ValueError as error:
                return _result(
                    "conflict", key, str(error), task_file, None, False, repo
                )
            request = (
                repo / request_relative if request_relative is not None else None
            )
            if not _generated_record(record, identity):
                return _result(
                    "conflict", key,
                    f"open task {record.task_id} is not safely owned by the filer",
                    task_file, request, False, repo,
                )
            if record.status == "0_backlog" and not _generated_backlog_request(
                repository, record, request_relative
            ):
                return _result(
                    "conflict", key,
                    f"backlog task {record.task_id} lacks its generated pickup request",
                    task_file, request, False, repo,
                )
            journal_relative = record.task_dir.relative_to(repo) / JOURNAL_NAME
            journal = repo / journal_relative
            try:
                snapshot = _read_journal_snapshot(
                    repository, journal_relative, identity
                )
                if snapshot is None or not snapshot.records:
                    raise ValueError("timing evidence journal is empty")
                prior = snapshot.records[-1]
            except (OSError, ValueError) as error:
                return _result("conflict", key, str(error), task_file, request, False, repo)
            if prior.get("receipt") == occurrence.receipt:
                return _result(
                    "unchanged", key,
                    f"receipt {occurrence.receipt} is already recorded",
                    task_file, request, False, repo,
                )
            state = _state_for(occurrence, prior)
            try:
                appended = _append_journal_record(
                    repository, journal_relative, identity, state, snapshot
                )
            except _PublicationFailure as error:
                cause = error.cause
                disposition = (
                    _classify_os_error(cause)
                    if isinstance(cause, OSError)
                    else "error"
                )
                return _result(
                    disposition,
                    key,
                    "timing evidence append stopped without deleting canonical paths: "
                    + str(cause),
                    task_file,
                    request,
                    error.mutated,
                    repo,
                )
            except (OSError, ValueError) as error:
                return _result(
                    "conflict",
                    key,
                    str(error),
                    task_file,
                    request,
                    False,
                    repo,
                )
            if appended:
                return _result(
                    "updated", key,
                    f"appended generated evidence in task {record.task_id}",
                    task_file, request, True, repo,
                )
            continue

        _validate_templates(repository)
        prior = max(done, key=_recurrence_order, default=None)
        task_id = _task_id(repository, occurrence, today, done)
        try:
            task_path, request_path = _create_pair(
                repository,
                occurrence,
                key,
                task_id,
                prior.task_id if prior else None,
            )
        except _PublicationFailure as error:
            cause = error.cause
            if isinstance(cause, FileExistsError):
                disposition = "conflict"
            elif isinstance(cause, OSError):
                disposition = _classify_os_error(cause)
            else:
                disposition = "error"
            return _result(
                disposition,
                key,
                "test-budget pair publication stopped without deleting canonical paths: "
                + str(cause),
                (
                    error.task_path / "task.md"
                    if error.task_path is not None
                    else None
                ),
                error.request_path,
                error.mutated,
                repo,
            )
        print(
            "Test budget investigation filed. Stage the generated task and pickup request "
            "with your next coordination commit; the matching gate receipt may be reused.",
            file=sys.stderr,
        )
        return _result(
            "created", key,
            f"filed backlog task {task_id} and its pickup request",
            task_path / "task.md", request_path, True, repo,
        )
    return _result(
        "conflict", key,
        "task records changed repeatedly while the filer was preparing an update; no files were changed",
        mutated=False, repo=repo,
    )


def file_budget_task(repo, occurrence, *, today=None, lock_timeout=1.0):
    """Best-effort filing entry point; never changes the gate's functional outcome."""
    supplied_root = Path(repo).absolute()
    root = supplied_root.parent.resolve() / supplied_root.name
    fallback_key = "test-budget-invalid-occurrence"
    repository = None
    try:
        normalized = _normalize_occurrence(occurrence, root)
        key = finding_key(normalized)
        if today is None:
            filed_date = dt.date.today().isoformat()
        elif isinstance(today, dt.date):
            filed_date = today.isoformat()
        else:
            filed_date = str(today)
            dt.date.fromisoformat(filed_date)
        with _PinnedRepository(root) as repository:
            with _lock(repository, float(lock_timeout)):
                return _file_locked(repository, normalized, filed_date, key)
    except TimeoutError as error:
        return _result(
            "lock-timeout",
            key,
            str(error),
            mutated=bool(repository and repository.mutated),
            repo=root,
        )
    except OSError as error:
        disposition = _classify_os_error(error)
        return _result(
            disposition, locals().get("key", fallback_key),
            f"test-budget task filing failed: {error}",
            mutated=bool(repository and repository.mutated),
            repo=root,
        )
    except Exception as error:  # the performance side effect may never break the gate
        return _result(
            "error", locals().get("key", fallback_key),
            f"test-budget task filing failed: {error}",
            mutated=bool(repository and repository.mutated),
            repo=root,
        )


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--occurrence-json", required=True)
    parser.add_argument("--lock-timeout", type=float, default=1.0)
    args = parser.parse_args(argv)
    try:
        occurrence = json.loads(args.occurrence_json)
    except json.JSONDecodeError as error:
        occurrence = {"invalid_json": str(error)}
    result = file_budget_task(
        args.repo, occurrence, lock_timeout=args.lock_timeout
    )
    print(json.dumps(result.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
