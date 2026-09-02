#!/usr/bin/env python3
"""Executable POC for semantic-result and execution-receipt separation.

The existing edge-witness prototype proves which queue disappearance is authorized.
This sibling POC proves the next boundary: only the resulting semantic rows are
canonical authority.  Implementation-specific work counters and cleanup evidence live
in a separate, run-scoped receipt that binds (but never changes) the semantic bytes.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from types import MappingProxyType
from typing import Callable, Iterable

import prototype as edge_witness


RESULT_SCHEMA = "restack-queue-semantic-result/v1"
RECEIPT_SCHEMA = "restack-queue-execution-receipt/v1"
RESULT_KEYS = ("schema", "old", "new", "common", "state", "rows")
ROW_KEYS = ("identity", "paths", "status", "reasons", "finding")
ROW_IDENTITY_KEYS = ("kind", "path", "old_blob", "new_blob")
ROW_FINDING_KEYS = ("check", "subject", "message", "fix")
RECEIPT_KEYS = (
    "schema",
    "result_sha256",
    "implementation",
    "runtime",
    "budget",
    "exit",
    "incomplete_reason",
    "cleanup",
)
RUNTIME_KEYS = ("python", "git", "platform")
BUDGET_KEYS = ("profile", "limits", "used")
BUDGET_COUNTERS = (
    "snapshot_requests",
    "reads",
    "allocations",
    "spawns",
    "retained_bytes",
    "writes",
    "written_bytes",
)
OPERATIONAL_COUNTERS = BUDGET_COUNTERS + ("cache_hits",)
CLEANUP_KEYS = (
    "caches_cleared",
    "children_terminated",
    "children_reaped",
    "descriptors_closed",
    "repository_unchanged",
    "worktree_unchanged",
    "index_unchanged",
)
IMPLEMENTATIONS = ("identity-node-cache", "shared-object-batch")
DEFAULT_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_RECEIPT_BYTES = DEFAULT_MAX_BYTES
DEFAULT_MAX_ROWS = 4096
OID_LENGTHS = (40, 64)
FINDING_CHECK = "restack-queue-semantic-boundary-poc"
TYPED_U_FINDING_CHECK = "restack-queue-production-contract-strategy-u"
ROW_CHANGE_KINDS = ("unauthorized-deletion", "unauthorized-rewrite")
ROW_STATUSES = ("preserved", "valid", "none", "invalid", "ambiguous")
TYPED_U_IDENTITY_KEYS = (
    "actor",
    "kind",
    "leaf",
    "production_tuple",
    "production_tuple_sha256",
)
ROW_REASON_CODES = {
    "unauthorized-deletion": "old-action-absent-without-matching-deletion-proof",
    "unauthorized-rewrite": "old-action-identity-changed-without-matching-proof",
}
ROW_MESSAGES = {
    "unauthorized-deletion": "old action absent without matching deletion proof",
    "unauthorized-rewrite": "old action identity changed without matching proof",
}
ROW_FIXES = {
    "unauthorized-deletion": "provide an accepted deletion proof before removing the action",
    "unauthorized-rewrite": "preserve the exact action identity or provide an accepted rewrite proof",
}
ROW_STATUS_BY_KIND = {
    "unauthorized-deletion": "none",
    "unauthorized-rewrite": "invalid",
}


class ContractError(ValueError):
    """The bytes are not the one accepted transport representation."""


class BudgetExceeded(RuntimeError):
    """An operation was refused before its callback could run."""

    def __init__(self, counter: str, limit: int, used: int, requested: int):
        self.counter = counter
        self.limit = limit
        self.used = used
        self.requested = requested
        super().__init__(
            f"budget:{counter}:limit={limit}:used={used}:requested={requested}"
        )


class InjectedFault(RuntimeError):
    """A deterministic test fault."""


class CleanupFailed(RuntimeError):
    """Cleanup could not prove its postconditions within the receipt budget."""

    def __init__(self, reason: str, cleanup):
        self.cleanup = cleanup
        super().__init__(reason)


class JsonObject(list):
    """A parsed JSON object that preserves pairs and can expose duplicates."""


def _object_pairs(pairs):
    seen = set()
    for key, _value in pairs:
        if key in seen:
            raise ContractError(f"duplicate JSON key: {key}")
        seen.add(key)
    return JsonObject(pairs)


def _reject_constant(token):
    raise ContractError(f"non-finite JSON number: {token}")


def _pairs(value, context: str):
    if isinstance(value, JsonObject):
        return list(value)
    if type(value) is dict:
        return list(value.items())
    raise ContractError(f"{context} must be an object")


def _schema_object(value, keys, context: str):
    pairs = _pairs(value, context)
    actual = tuple(key for key, _item in pairs)
    expected = set(keys)
    actual_set = set(actual)
    if len(actual) != len(actual_set):
        raise ContractError(f"{context} has duplicate keys")
    if actual_set != expected:
        raise ContractError(
            f"{context} keys must be exactly {tuple(keys)!r}, got {actual!r}"
        )
    return {key: item for key, item in pairs}


def _native(value):
    if isinstance(value, JsonObject):
        return {key: _native(item) for key, item in value}
    if type(value) is list:
        return [_native(item) for item in value]
    return value


def _is_oid(value):
    return type(value) is str and len(value) in OID_LENGTHS and all(
        character in "0123456789abcdef" for character in value
    )


def _require_oid(value, context: str):
    if not _is_oid(value):
        raise ContractError(f"{context} must be one full lowercase hex object ID")


def _require_exact_int(value, context: str, minimum=0):
    if type(value) is not int or value < minimum:
        raise ContractError(
            f"{context} must be an integer (JSON booleans are not integers here)"
        )


@dataclasses.dataclass(frozen=True)
class CodecLimits:
    max_bytes: int = DEFAULT_MAX_BYTES
    max_rows: int = DEFAULT_MAX_ROWS

    def __post_init__(self):
        _require_exact_int(self.max_bytes, "max_bytes", 1)
        _require_exact_int(self.max_rows, "max_rows", 0)


@dataclasses.dataclass(frozen=True)
class ReceiptLimits:
    max_bytes: int = DEFAULT_MAX_RECEIPT_BYTES

    def __post_init__(self):
        _require_exact_int(self.max_bytes, "receipt max_bytes", 0)


def _require_path(value, context: str):
    if type(value) is not str or not value or "\x00" in value:
        raise ContractError(f"{context} must be a nonempty NUL-free string")


def _validate_sorted_string_list(value, allowed, context: str):
    if type(value) is not list:
        raise ContractError(f"{context} must be an array")
    for position, item in enumerate(value):
        _require_path(item, f"{context}[{position}]")
        if allowed is not None and item not in allowed:
            raise ContractError(f"{context}[{position}] is not an accepted value")
    if value != sorted(set(value), key=lambda item: item.encode("utf-8")):
        raise ContractError(f"{context} must be sorted and duplicate-free")
    return value


def _require_sha256(value, context: str):
    if not (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    ):
        raise ContractError(f"{context} must be one lowercase SHA-256 digest")


def _canonical_json_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def _row_identity_sort_key(row):
    return _canonical_json_bytes(row["identity"])


def _row_for_change(path: str, kind: str, old_blob: str, new_blob: str | None):
    if kind not in ROW_CHANGE_KINDS:
        raise ContractError(f"unknown illustrative row kind: {kind}")
    reason = ROW_REASON_CODES[kind]
    message = ROW_MESSAGES[kind]
    return {
        "identity": {
            "kind": kind,
            "path": path,
            "old_blob": old_blob,
            "new_blob": new_blob,
        },
        "paths": [path],
        "status": ROW_STATUS_BY_KIND[kind],
        "reasons": [reason],
        "finding": {
            "check": FINDING_CHECK,
            "subject": path,
            "message": message,
            "fix": ROW_FIXES[kind],
        },
    }


def _validate_finding(value, position: int):
    finding = _schema_object(value, ROW_FINDING_KEYS, f"row {position} finding")
    if finding["check"] not in {FINDING_CHECK, TYPED_U_FINDING_CHECK}:
        raise ContractError(f"row {position} finding check is inconsistent")
    for key in ("subject", "message", "fix"):
        if type(finding[key]) is not str or not finding[key] or "\x00" in finding[key]:
            raise ContractError(f"row {position} finding.{key} must be nonempty text")
    return finding


def _validate_edge_row(row, identity, position: int):
    kind = identity["kind"]
    if kind not in ROW_CHANGE_KINDS:
        raise ContractError(f"row {position} has an unknown illustrative kind")
    path = identity["path"]
    _require_path(path, f"row {position} identity.path")
    _require_oid(identity["old_blob"], f"row {position} identity.old_blob")
    if identity["new_blob"] is not None:
        _require_oid(identity["new_blob"], f"row {position} identity.new_blob")
    if kind == "unauthorized-deletion" and identity["new_blob"] is not None:
        raise ContractError(f"row {position} deletion must have null new_blob")
    if kind == "unauthorized-rewrite" and (
        identity["new_blob"] is None or identity["new_blob"] == identity["old_blob"]
    ):
        raise ContractError(f"row {position} rewrite must name a different new_blob")
    paths = _validate_sorted_string_list(row["paths"], None, f"row {position} paths")
    if paths != [path]:
        raise ContractError(f"row {position} illustrative evaluator supports one path")
    status = row["status"]
    if status not in ROW_STATUSES:
        raise ContractError(f"row {position} has an unknown status")
    if status != ROW_STATUS_BY_KIND[kind]:
        raise ContractError(f"row {position} status is inconsistent with its kind")
    reasons = _validate_sorted_string_list(
        row["reasons"],
        set(ROW_REASON_CODES.values()),
        f"row {position} reasons",
    )
    if reasons != [ROW_REASON_CODES[kind]]:
        raise ContractError(f"row {position} reasons are inconsistent with its kind")
    if status in {"preserved", "valid"}:
        if row["finding"] is not None:
            raise ContractError(f"row {position} preserved/valid rows require null finding")
    else:
        finding = _validate_finding(row["finding"], position)
        if finding["check"] != FINDING_CHECK:
            raise ContractError(f"row {position} finding check is inconsistent")
        if finding["subject"] != path:
            raise ContractError(f"row {position} finding subject is inconsistent")
        if finding["message"] != ROW_MESSAGES[kind]:
            raise ContractError(f"row {position} finding message is inconsistent")
        if finding["fix"] != ROW_FIXES[kind]:
            raise ContractError(f"row {position} finding fix is inconsistent")
    return row


def _validate_typed_u_row(row, identity, position: int):
    for key in ("actor", "kind", "leaf"):
        _require_path(identity[key], f"row {position} identity.{key}")
    production_tuple = identity["production_tuple"]
    if type(production_tuple) is not list or not production_tuple:
        raise ContractError(f"row {position} identity.production_tuple must be a nonempty array")
    for index, item in enumerate(production_tuple):
        if type(item) is not str or not item or "\x00" in item:
            raise ContractError(
                f"row {position} identity.production_tuple[{index}] must be nonempty text"
            )
    _require_sha256(
        identity["production_tuple_sha256"],
        f"row {position} identity.production_tuple_sha256",
    )
    paths = _validate_sorted_string_list(row["paths"], None, f"row {position} paths")
    if not paths:
        raise ContractError(f"row {position} typed-U finding must name at least one path")
    status = row["status"]
    if status not in ROW_STATUSES:
        raise ContractError(f"row {position} has an unknown status")
    reasons = _validate_sorted_string_list(row["reasons"], None, f"row {position} reasons")
    if not reasons:
        raise ContractError(f"row {position} typed-U finding must name at least one reason")
    if status in {"preserved", "valid"}:
        if row["finding"] is not None:
            raise ContractError(f"row {position} preserved/valid rows require null finding")
    else:
        finding = _validate_finding(row["finding"], position)
        if finding["check"] != TYPED_U_FINDING_CHECK:
            raise ContractError(f"row {position} typed-U finding check is inconsistent")
        if finding["subject"] != identity["production_tuple_sha256"]:
            raise ContractError(f"row {position} typed-U finding subject is inconsistent")
    return row


def _validate_row(value, position: int):
    row = _schema_object(value, ROW_KEYS, f"row {position}")
    identity_pairs = _pairs(row["identity"], f"row {position} identity")
    identity_keys = tuple(key for key, _item in identity_pairs)
    if set(identity_keys) == set(ROW_IDENTITY_KEYS):
        identity = _schema_object(
            row["identity"],
            ROW_IDENTITY_KEYS,
            f"row {position} identity",
        )
        return _validate_edge_row(row, identity, position)
    if set(identity_keys) == set(TYPED_U_IDENTITY_KEYS):
        identity = _schema_object(
            row["identity"],
            TYPED_U_IDENTITY_KEYS,
            f"row {position} identity",
        )
        return _validate_typed_u_row(row, identity, position)
    raise ContractError(
        f"row {position} identity is neither illustrative edge shape nor typed-U shape"
    )


def validate_result(value, limits=CodecLimits()):
    if type(limits) is not CodecLimits:
        raise ContractError("limits must be CodecLimits")
    result = _schema_object(value, RESULT_KEYS, "semantic result")
    if result["schema"] != RESULT_SCHEMA:
        raise ContractError(f"semantic result schema must be {RESULT_SCHEMA}")
    _require_oid(result["old"], "old")
    _require_oid(result["new"], "new")
    common = result["common"]
    _require_oid(common, "common")
    if len(common) != len(result["old"]):
        raise ContractError("old, new, and common object IDs must use one format")
    if len(result["new"]) != len(result["old"]):
        raise ContractError("old and new object IDs must use one format")
    if result["state"] not in {"clean", "blocked"}:
        raise ContractError("state must be clean or blocked; incomplete has no result")
    if type(result["rows"]) is not list:
        raise ContractError("rows must be an array")
    if len(result["rows"]) > limits.max_rows:
        raise ContractError(
            f"rows exceeds serialization bound {limits.max_rows}"
        )
    rows = [_validate_row(row, position) for position, row in enumerate(result["rows"])]
    row_order = [_row_identity_sort_key(row) for row in rows]
    if row_order != sorted(row_order):
        raise ContractError("rows must be in canonical identity order")
    if len(row_order) != len(set(row_order)):
        raise ContractError("rows must contain at most one finding per identity")
    paths = [path for row in rows for path in row["paths"]]
    if len(paths) != len(set(paths)):
        raise ContractError("rows must contain at most one finding per path")
    if (result["state"] == "clean") != (not rows):
        raise ContractError("clean requires zero rows and blocked requires at least one")
    return result


def _validate_counter_object(value, keys, context: str, allow_null=False):
    counters = _schema_object(value, keys, context)
    for key, item in counters.items():
        if allow_null and item is None:
            continue
        _require_exact_int(item, f"{context}.{key}")
    return counters


def validate_receipt(value):
    receipt = _schema_object(value, RECEIPT_KEYS, "execution receipt")
    if receipt["schema"] != RECEIPT_SCHEMA:
        raise ContractError(f"execution receipt schema must be {RECEIPT_SCHEMA}")
    digest = receipt["result_sha256"]
    if digest is not None and not (
        type(digest) is str
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    ):
        raise ContractError("result_sha256 must be null or lowercase sha256")
    if type(receipt["implementation"]) is not str or not receipt["implementation"]:
        raise ContractError("implementation must be a nonempty string")
    runtime = _schema_object(receipt["runtime"], RUNTIME_KEYS, "runtime")
    if any(type(value) is not str or not value for value in runtime.values()):
        raise ContractError("runtime values must be nonempty strings")
    budget = _schema_object(receipt["budget"], BUDGET_KEYS, "budget")
    if type(budget["profile"]) is not str or not budget["profile"]:
        raise ContractError("budget.profile must be a nonempty string")
    limits = _validate_counter_object(
        budget["limits"], BUDGET_COUNTERS, "budget.limits", allow_null=True
    )
    used = _validate_counter_object(
        budget["used"], OPERATIONAL_COUNTERS, "budget.used"
    )
    for counter in BUDGET_COUNTERS:
        limit = limits[counter]
        if limit is not None and used[counter] > limit:
            raise ContractError(f"budget.used.{counter} exceeds budget.limits.{counter}")
    _require_exact_int(receipt["exit"], "exit")
    if receipt["exit"] not in {0, 2}:
        raise ContractError("exit must be 0 (complete) or 2 (incomplete)")
    if receipt["incomplete_reason"] is not None and (
        type(receipt["incomplete_reason"]) is not str
        or not receipt["incomplete_reason"]
    ):
        raise ContractError("incomplete_reason must be null or a nonempty string")
    cleanup = _schema_object(receipt["cleanup"], CLEANUP_KEYS, "cleanup")
    if any(type(value) is not bool for value in cleanup.values()):
        raise ContractError("cleanup observations must be JSON booleans")
    complete = receipt["exit"] == 0
    if complete != (digest is not None and receipt["incomplete_reason"] is None):
        raise ContractError("exit/result digest/incomplete reason are inconsistent")
    if complete and not all(cleanup.values()):
        raise ContractError("a complete receipt requires every cleanup observation")
    if not complete and digest is not None:
        raise ContractError("an incomplete receipt cannot bind a partial result")
    return receipt


def _json_string_size(value: str):
    size = 2
    short_escapes = {8, 9, 10, 12, 13}
    for character in value:
        codepoint = ord(character)
        if character in {'"', "\\"} or codepoint in short_escapes:
            size += 2
        elif codepoint < 0x20 or codepoint <= 0xFFFF and codepoint >= 0x80:
            size += 6
        elif codepoint > 0xFFFF:
            size += 12
        else:
            size += 1
    return size


def _json_size(value):
    if value is None:
        return 4
    if value is True:
        return 4
    if value is False:
        return 5
    if type(value) is int:
        return len(str(value))
    if type(value) is str:
        return _json_string_size(value)
    if type(value) is list:
        return 2 + max(0, len(value) - 1) + sum(_json_size(item) for item in value)
    if type(value) is dict:
        return 2 + max(0, len(value) - 1) + sum(
            _json_string_size(key) + 1 + _json_size(item)
            for key, item in value.items()
        )
    raise ContractError(f"unsupported canonical JSON type: {type(value).__name__}")


def _dump(value):
    return _canonical_json_bytes(value) + b"\n"


def _dump_insertion_order_for_test(value):
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii") + b"\n"


def encode_result(value, limits=CodecLimits()):
    validate_result(value, limits)
    native = _native(value)
    size = _json_size(native) + 1
    if size > limits.max_bytes:
        raise ContractError(f"semantic result exceeds byte bound {limits.max_bytes}")
    encoded = _dump(native)
    if len(encoded) != size:
        raise AssertionError("canonical JSON size preflight drifted from encoder")
    return encoded


def encode_receipt(value, limits=ReceiptLimits()):
    if type(limits) is not ReceiptLimits:
        raise ContractError("receipt limits must be ReceiptLimits")
    validate_receipt(value)
    native = _native(value)
    size = _json_size(native) + 1
    if size > limits.max_bytes:
        raise ContractError(f"execution receipt exceeds byte bound {limits.max_bytes}")
    encoded = _dump(native)
    if len(encoded) != size:
        raise AssertionError("receipt size preflight drifted from encoder")
    return encoded


def _parse_exact(data, context: str):
    if type(data) is not bytes:
        raise ContractError(f"{context} transport must be bytes")
    if not data.endswith(b"\n"):
        raise ContractError(f"{context} must end with one LF")
    if data.endswith(b"\n\n"):
        raise ContractError(f"{context} must end with exactly one LF")
    if b"\r" in data:
        raise ContractError(f"{context} forbids CR bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError(f"{context} is not UTF-8") from error
    try:
        return json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_constant=_reject_constant,
        )
    except ContractError:
        raise
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ContractError(f"{context} is not one JSON value plus LF") from error


def decode_result(
    data,
    invocation_old: str,
    invocation_new: str,
    invocation_common: str,
    limits=CodecLimits(),
):
    if type(limits) is not CodecLimits:
        raise ContractError("limits must be CodecLimits")
    if type(data) is bytes and len(data) > limits.max_bytes:
        raise ContractError(f"semantic result exceeds byte bound {limits.max_bytes}")
    parsed = _parse_exact(data, "semantic result")
    result = validate_result(parsed, limits)
    native = _native(parsed)
    if _dump(native) != data:
        raise ContractError("semantic result is valid JSON but not exact canonical bytes")
    _require_oid(invocation_old, "invocation old")
    _require_oid(invocation_new, "invocation new")
    _require_oid(invocation_common, "invocation common")
    if (
        result["old"] != invocation_old
        or result["new"] != invocation_new
        or result["common"] != invocation_common
    ):
        raise ContractError(
            "semantic result old/new/common do not match invocation O/N/C"
        )
    return native


def decode_receipt(data, limits=ReceiptLimits()):
    if type(limits) is not ReceiptLimits:
        raise ContractError("receipt limits must be ReceiptLimits")
    if type(data) is bytes and len(data) > limits.max_bytes:
        raise ContractError(f"execution receipt exceeds byte bound {limits.max_bytes}")
    parsed = _parse_exact(data, "execution receipt")
    validate_receipt(parsed)
    native = _native(parsed)
    if _dump(native) != data:
        raise ContractError("execution receipt is valid JSON but not exact canonical bytes")
    return native


class Budget:
    """Deterministic pre-charge meter; rejected work never calls its callback."""

    def __init__(self, limits=None, profile="poc-default"):
        supplied = {} if limits is None else dict(limits)
        if set(supplied) - set(BUDGET_COUNTERS):
            raise ValueError("unknown budget counter")
        self.profile = profile
        self.limits = {}
        self.used = {counter: 0 for counter in OPERATIONAL_COUNTERS}
        for counter in BUDGET_COUNTERS:
            limit = supplied.get(counter)
            if limit is not None:
                _require_exact_int(limit, f"limit {counter}")
            self.limits[counter] = limit

    def charge(self, counter: str, amount=1):
        if counter not in BUDGET_COUNTERS:
            raise ValueError(f"not a charged counter: {counter}")
        _require_exact_int(amount, f"charge {counter}")
        current = self.used[counter]
        limit = self.limits[counter]
        if limit is not None and current + amount > limit:
            raise BudgetExceeded(counter, limit, current, amount)
        self.used[counter] = current + amount

    def perform(self, counter: str, amount: int, callback: Callable):
        self.charge(counter, amount)
        return callback()

    def observe_cache_hit(self):
        self.used["cache_hits"] += 1

    def receipt_limits(self):
        return {counter: self.limits[counter] for counter in BUDGET_COUNTERS}

    def receipt_used(self):
        return {counter: self.used[counter] for counter in OPERATIONAL_COUNTERS}


@dataclasses.dataclass(frozen=True)
class Snapshot:
    object_oid: str
    entries: tuple[tuple[str, str], ...]

    @property
    def retained_size(self):
        return len(self.object_oid) + sum(
            len(path.encode("utf-8")) + len(blob)
            for path, blob in self.entries
        )


class SyntheticSnapshotStore:
    def __init__(self, snapshots):
        self._snapshots = MappingProxyType(dict(snapshots))
        self.load_calls = 0

    def load(self, object_oid: str, transaction):
        self.load_calls += 1
        try:
            return self._snapshots[object_oid]
        except KeyError as error:
            raise ContractError(f"unavailable synthetic snapshot {object_oid}") from error

    @property
    def repository_root(self):
        return None


class GitSnapshotStore:
    """Read one immutable Git tree without exposing its absolute repository root."""

    def __init__(self, repository_root: Path):
        self._root = repository_root
        self.load_calls = 0

    def load(self, object_oid: str, transaction):
        self.load_calls += 1
        output = transaction.git_output(
            self._root,
            "--no-replace-objects",
            "ls-tree",
            "-r",
            "-z",
            object_oid,
        )
        entries = []
        for record in output.split(b"\x00"):
            if not record:
                continue
            try:
                header, raw_path = record.split(b"\t", 1)
                _mode, object_type, raw_blob = header.split(b" ", 2)
                path = raw_path.decode("utf-8")
                blob = raw_blob.decode("ascii")
            except (ValueError, UnicodeError) as error:
                raise ContractError("Git tree entry is not the expected byte form") from error
            full_path = "message-queue/" + path
            if object_type == b"blob" and (
                full_path.startswith("message-queue/needs-agent/")
                or full_path.startswith("message-queue/needs-human/")
            ) and full_path.endswith(".md") and not full_path.endswith("/README.md"):
                _require_oid(blob, f"blob for {full_path}")
                entries.append((full_path, blob))
        entries.sort(key=lambda item: item[0].encode("utf-8"))
        return Snapshot(object_oid, tuple(entries))

    @property
    def repository_root(self):
        return self._root


@dataclasses.dataclass(frozen=True)
class TypedUComposition:
    """Narrow imported Strategy-U result source for the semantic boundary."""

    scenario: str
    classification: str
    evidence_status: str
    origin_strategy: str
    common: str
    state: str
    rows: tuple[dict, ...]

    def __post_init__(self):
        for field in ("scenario", "classification", "evidence_status", "origin_strategy"):
            value = getattr(self, field)
            if type(value) is not str or not value:
                raise ContractError(f"typed-U {field} must be a nonempty string")
        if self.origin_strategy != "U":
            raise ContractError("typed-U composition must be produced by Strategy U")
        _require_oid(self.common, "typed-U common")
        if self.state not in {"clean", "blocked"}:
            raise ContractError("typed-U state must be clean or blocked")


@dataclasses.dataclass(frozen=True)
class ProofInput:
    label: str
    old: str
    new: str
    common: str
    revision_objects: tuple[tuple[str, str], ...]
    authorized_deletions: tuple[tuple[str, str], ...]
    store: object
    typed_u: TypedUComposition | None = None

    def __post_init__(self):
        _require_oid(self.old, "proof old")
        _require_oid(self.new, "proof new")
        _require_oid(self.common, "proof common")
        revisions = dict(self.revision_objects)
        if set((self.old, self.new, self.common)) - set(revisions):
            raise ContractError("proof does not bind every old/new/common revision")
        if len(revisions) != len(self.revision_objects):
            raise ContractError("proof revision map contains duplicates")
        if self.typed_u is not None:
            if self.typed_u.common != self.common:
                raise ContractError("typed-U composition common does not match proof")
            validate_result(
                {
                    "schema": RESULT_SCHEMA,
                    "old": self.old,
                    "new": self.new,
                    "common": self.common,
                    "state": self.typed_u.state,
                    "rows": list(self.typed_u.rows),
                }
            )

    def object_for(self, revision: str):
        return dict(self.revision_objects)[revision]


def _single_common(merge_bases):
    bases = tuple(merge_bases)
    if len(bases) != 1:
        raise ContractError(f"expected exactly one merge base, got {len(bases)}")
    _require_oid(bases[0], "common")
    return bases[0]


@dataclasses.dataclass(frozen=True)
class RepositoryFingerprint:
    refs: bytes
    status: bytes
    index_sha256: str

    @classmethod
    def capture(cls, root: Path, transaction):
        refs = transaction.git_output(root, "show-ref", "--head", "--dereference")
        status = transaction.git_output(
            root,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        )
        index_path_text = transaction.git_output(
            root, "rev-parse", "--git-path", "index"
        ).decode("utf-8").strip()
        index_path = Path(index_path_text)
        if not index_path.is_absolute():
            index_path = root / index_path
        index_bytes = transaction.path_bytes(index_path) if index_path.exists() else b""
        return cls(refs, status, hashlib.sha256(index_bytes).hexdigest())


class EvaluationTransaction:
    def __init__(self, proof: ProofInput, budget: Budget, fault=None):
        self.proof = proof
        self.budget = budget
        self.fault = fault
        self.cache = {}
        self.children = []
        self.descriptors = []
        self.snapshot_calls = 0
        self.before = None

    def capture_before(self):
        root = self.proof.store.repository_root
        self.before = RepositoryFingerprint.capture(root, self) if root is not None else None

    def path_bytes(self, path: Path):
        def read():
            return path.read_bytes()

        data = self.budget.perform("reads", 1, read)
        self.budget.charge("retained_bytes", len(data))
        return data

    def _load_snapshot(self, object_oid: str):
        def load():
            return self.proof.store.load(object_oid, self)

        self.budget.charge("allocations", 1)
        snapshot = self.budget.perform("reads", 1, load)
        self.budget.charge("retained_bytes", snapshot.retained_size)
        self.cache[object_oid] = snapshot
        return snapshot

    def request_snapshot(self, object_oid: str):
        self.budget.charge("snapshot_requests", 1)
        self.snapshot_calls += 1
        if object_oid in self.cache:
            self.budget.observe_cache_hit()
            snapshot = self.cache[object_oid]
        else:
            snapshot = self._load_snapshot(object_oid)
        if self.fault == "after-first-snapshot" and self.snapshot_calls == 1:
            raise InjectedFault("fault:after-first-snapshot")
        return snapshot

    def request_snapshot_batch(self, object_oids: Iterable[str]):
        snapshots = {}
        for object_oid in dict.fromkeys(object_oids):
            snapshots[object_oid] = self.request_snapshot(object_oid)
        return snapshots

    def git_output(self, root: Path, *arguments):
        self.budget.charge("spawns", 1)
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode:
            raise ContractError(
                f"Git snapshot read failed ({result.returncode}): "
                + result.stderr.decode("utf-8", "replace").strip()
            )
        return result.stdout

    def spawn_probe(self):
        def spawn():
            child = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.children.append(child)
            return child

        return self.budget.perform("spawns", 1, spawn)

    def open_probe_descriptor(self):
        self.budget.charge("allocations", 1)
        self.budget.charge("reads", 1)
        descriptor = open(os.devnull, "rb")
        self.descriptors.append(descriptor)
        return descriptor

    def cleanup(self):
        children_terminated = True
        children_reaped = True
        descriptors_closed = True
        for child in self.children:
            if child.poll() is None:
                try:
                    child.terminate()
                except OSError:
                    children_terminated = False
            try:
                child.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                children_reaped = False
                try:
                    child.kill()
                    child.wait(timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    children_reaped = False
            for stream in (child.stdout, child.stderr):
                if stream is not None:
                    stream.close()
                    if not stream.closed:
                        descriptors_closed = False
        for descriptor in self.descriptors:
            descriptor.close()
            if not descriptor.closed:
                descriptors_closed = False
        self.cache.clear()
        root = self.proof.store.repository_root
        cleanup_error = None
        if root is None:
            repository_unchanged = worktree_unchanged = index_unchanged = True
        elif self.before is None:
            repository_unchanged = worktree_unchanged = index_unchanged = False
        else:
            try:
                after = RepositoryFingerprint.capture(root, self)
            except (BudgetExceeded, ContractError) as error:
                cleanup_error = str(error)
                repository_unchanged = worktree_unchanged = index_unchanged = False
            else:
                repository_unchanged = self.before.refs == after.refs
                worktree_unchanged = self.before.status == after.status
                index_unchanged = self.before.index_sha256 == after.index_sha256
        cleanup = {
            "caches_cleared": not self.cache,
            "children_terminated": children_terminated,
            "children_reaped": children_reaped,
            "descriptors_closed": descriptors_closed,
            "repository_unchanged": repository_unchanged,
            "worktree_unchanged": worktree_unchanged,
            "index_unchanged": index_unchanged,
        }
        if cleanup_error is not None:
            raise CleanupFailed(cleanup_error, cleanup)
        return cleanup


def _result_from_snapshots(proof: ProofInput, snapshots, budget: Budget):
    # One charged semantic-workspace allocation precedes all lookup tables and the
    # result-row container created by this evaluator phase.
    budget.charge("allocations", 1)
    if proof.typed_u is not None:
        rows = [dict(_native(row)) for row in proof.typed_u.rows]

        def make_typed_result():
            return {
                "schema": RESULT_SCHEMA,
                "old": proof.old,
                "new": proof.new,
                "common": proof.common,
                "state": proof.typed_u.state,
                "rows": rows,
            }

        return budget.perform("allocations", 1, make_typed_result)

    old_entries = dict(snapshots[proof.old].entries)
    new_entries = dict(snapshots[proof.new].entries)
    authorized = set(proof.authorized_deletions)
    rows = []
    for path, old_blob in sorted(old_entries.items(), key=lambda item: item[0].encode("utf-8")):
        new_blob = new_entries.get(path)
        if new_blob == old_blob:
            continue
        if new_blob is None and (path, old_blob) in authorized:
            continue
        if new_blob is None:
            kind = "unauthorized-deletion"
        else:
            kind = "unauthorized-rewrite"

        def make_row():
            return _row_for_change(path, kind, old_blob, new_blob)

        rows.append(budget.perform("allocations", 1, make_row))
    rows.sort(key=_row_identity_sort_key)

    def make_result():
        return {
            "schema": RESULT_SCHEMA,
            "old": proof.old,
            "new": proof.new,
            "common": proof.common,
            "state": "blocked" if rows else "clean",
            "rows": rows,
        }

    return budget.perform("allocations", 1, make_result)


def evaluate_identity_node_cache(proof: ProofInput, transaction: EvaluationTransaction):
    revisions = (proof.old, proof.new, proof.common)
    transaction.budget.charge("allocations", 1)
    snapshots = {}
    for revision in revisions:
        snapshots[revision] = transaction.request_snapshot(proof.object_for(revision))
    for revision in revisions:
        snapshots[revision] = transaction.request_snapshot(proof.object_for(revision))
    return _result_from_snapshots(proof, snapshots, transaction.budget)


def evaluate_shared_object_batch(proof: ProofInput, transaction: EvaluationTransaction):
    revisions = (proof.old, proof.new, proof.common)
    transaction.budget.charge("allocations", 1)
    object_ids = [proof.object_for(revision) for revision in revisions]
    by_object = transaction.request_snapshot_batch(object_ids)
    snapshots = {
        revision: by_object[proof.object_for(revision)] for revision in revisions
    }
    return _result_from_snapshots(proof, snapshots, transaction.budget)


@dataclasses.dataclass
class Execution:
    result: bytes | None
    receipt: bytes

    @property
    def decoded_receipt(self):
        return decode_receipt(self.receipt)


def _runtime():
    return {
        "python": sys.version.split()[0],
        "git": "not-spawned-by-semantic-boundary-runtime",
        "platform": f"{platform.system().lower()}/{platform.machine().lower()}",
    }


def execute(
    proof: ProofInput,
    implementation: str,
    limits=None,
    profile="poc-default",
    fault=None,
    codec_limits=CodecLimits(),
):
    if implementation not in IMPLEMENTATIONS:
        raise ValueError(f"unknown implementation {implementation}")
    budget = Budget(limits=limits, profile=profile)
    transaction = EvaluationTransaction(proof, budget, fault=fault)
    staged = None
    incomplete_reason = None
    cleanup_error = None
    cleanup = {
        "caches_cleared": False,
        "children_terminated": False,
        "children_reaped": False,
        "descriptors_closed": False,
        "repository_unchanged": False,
        "worktree_unchanged": False,
        "index_unchanged": False,
    }
    try:
        transaction.capture_before()
        if fault == "after-child-spawn":
            transaction.spawn_probe()
            raise InjectedFault("fault:after-child-spawn")
        if fault == "after-descriptor-open":
            transaction.open_probe_descriptor()
            raise InjectedFault("fault:after-descriptor-open")
        evaluator = {
            "identity-node-cache": evaluate_identity_node_cache,
            "shared-object-batch": evaluate_shared_object_batch,
        }[implementation]
        result = evaluator(proof, transaction)
        if fault == "after-result-construction":
            raise InjectedFault("fault:after-result-construction")
        # The charge precedes validation's normalized object and the encoder's
        # canonical byte allocation. The retained-byte charge follows the allocation-
        # free size preflight and precedes materializing the transport bytes.
        budget.charge("allocations", 1)
        validate_result(result, codec_limits)
        native = _native(result)
        predicted_size = _json_size(native) + 1
        if predicted_size > codec_limits.max_bytes:
            raise ContractError(
                f"semantic result exceeds byte bound {codec_limits.max_bytes}"
            )
        budget.charge("retained_bytes", predicted_size)
        staged = _dump(native)
        if len(staged) != predicted_size:
            raise AssertionError("result size preflight drifted")
        decode_result(staged, proof.old, proof.new, proof.common, codec_limits)
    except (BudgetExceeded, ContractError, InjectedFault) as error:
        incomplete_reason = str(error)
        staged = None
    except Exception as error:  # fail closed for unexpected evaluator/provider faults
        incomplete_reason = f"unexpected:{type(error).__name__}:{error}"
        staged = None
    finally:
        try:
            cleanup = transaction.cleanup()
        except CleanupFailed as error:
            cleanup = error.cleanup
            cleanup_error = str(error)
        except (BudgetExceeded, ContractError) as error:
            cleanup_error = str(error)
    if cleanup_error is not None:
        incomplete_reason = cleanup_error
        staged = None
    if staged is not None and not all(cleanup.values()):
        incomplete_reason = "cleanup:one-or-more-postconditions-failed"
        staged = None
    if staged is not None and fault == "after-cleanup":
        incomplete_reason = "fault:after-cleanup"
        staged = None
    if staged is not None and fault == "before-result-commit":
        incomplete_reason = "fault:before-result-commit"
        staged = None

    accepted = None
    if staged is not None:
        try:
            budget.charge("writes", 1)
            accepted = budget.perform("written_bytes", len(staged), lambda: staged)
        except BudgetExceeded as error:
            incomplete_reason = str(error)
            accepted = None
    digest = hashlib.sha256(accepted).hexdigest() if accepted is not None else None
    receipt_value = {
        "schema": RECEIPT_SCHEMA,
        "result_sha256": digest,
        "implementation": implementation,
        "runtime": _runtime(),
        "budget": {
            "profile": profile,
            "limits": budget.receipt_limits(),
            "used": budget.receipt_used(),
        },
        "exit": 0 if accepted is not None else 2,
        "incomplete_reason": None if accepted is not None else (
            incomplete_reason or "incomplete:result-not-produced"
        ),
        "cleanup": cleanup,
    }
    return Execution(accepted, encode_receipt(receipt_value))


def provider_projection(
    result_bytes: bytes | None,
    receipt_bytes: bytes,
    invocation_old: str,
    invocation_new: str,
    invocation_common: str,
    result_limits=CodecLimits(),
    receipt_limits=ReceiptLimits(),
):
    _require_oid(invocation_common, "invocation common")
    receipt = decode_receipt(receipt_bytes, receipt_limits)
    if result_bytes is None:
        if receipt["exit"] == 0 or receipt["result_sha256"] is not None:
            raise ContractError("missing result conflicts with a complete receipt")
        return {"conclusion": "incomplete", "rows": []}
    result = decode_result(
        result_bytes,
        invocation_old,
        invocation_new,
        invocation_common,
        result_limits,
    )
    digest = hashlib.sha256(result_bytes).hexdigest()
    if receipt["exit"] != 0 or receipt["result_sha256"] != digest:
        raise ContractError("execution receipt does not bind these semantic result bytes")
    return {"conclusion": result["state"], "rows": result["rows"]}


def _oid(label: str):
    return hashlib.sha1(label.encode("utf-8")).hexdigest()


def _snapshot(label: str, entries):
    normalized = tuple(sorted(entries, key=lambda item: item[0].encode("utf-8")))
    return Snapshot(_oid("tree:" + label), normalized)


def synthetic_proof(
    label: str,
    old_entries,
    new_entries,
    authorized=(),
    shared_subtree=False,
):
    old = _oid(label + ":old")
    new = _oid(label + ":new")
    common = _oid(label + ":common")
    old_snapshot = _snapshot(label + ":old", tuple(old_entries))
    new_snapshot = old_snapshot if shared_subtree else _snapshot(
        label + ":new", tuple(new_entries)
    )
    common_snapshot = old_snapshot
    snapshots = {
        old_snapshot.object_oid: old_snapshot,
        new_snapshot.object_oid: new_snapshot,
        common_snapshot.object_oid: common_snapshot,
    }
    store = SyntheticSnapshotStore(snapshots)
    return ProofInput(
        label=label,
        old=old,
        new=new,
        common=common,
        revision_objects=(
            (old, old_snapshot.object_oid),
            (new, new_snapshot.object_oid),
            (common, common_snapshot.object_oid),
        ),
        authorized_deletions=tuple(sorted(authorized)),
        store=store,
    )


def real_git_proof(root: Path, factory):
    fixture = factory(root)
    classification = edge_witness.classify(fixture)
    edge_witness.verify_result(fixture, classification)
    merge_bases = tuple(sorted(fixture.repo.run(
        "--no-replace-objects", "merge-base", "--all", fixture.O, fixture.N
    ).stdout.splitlines()))
    common = _single_common(merge_bases)
    revisions = tuple(dict.fromkeys((fixture.O, fixture.N, common)))
    revision_objects = tuple(
        (
            revision,
            fixture.repo.run(
                "--no-replace-objects",
                "rev-parse",
                "--verify",
                f"{revision}:message-queue",
            ).stdout.strip(),
        )
        for revision in revisions
    )
    authorized = []
    for path, item in classification.get("items", {}).items():
        if item["evidence_verdict"] != "valid-real-edge":
            continue
        blob = fixture.repo.run(
            "--no-replace-objects",
            "rev-parse",
            "--verify",
            f"{fixture.O}:{path}",
        ).stdout.strip()
        authorized.append((path, blob))
    return ProofInput(
        label=fixture.scenario_id,
        old=fixture.O,
        new=fixture.N,
        common=common,
        revision_objects=revision_objects,
        authorized_deletions=tuple(sorted(authorized)),
        store=GitSnapshotStore(root),
    )


_PRODUCTION_CONTRACT_MODULE = None
PRODUCTION_EVENT_ADAPTER_SYMBOLS = ("event_endpoints", "audit_event")
TYPED_U_CASES = {
    "typed-u-normal-restack": {
        "fallback_case": "normal-base-advance-replay",
        "expected_state": "clean",
    },
    "typed-u-illegal-birth": {
        "fallback_case": "agent-born-claimed",
        "expected_state": "blocked",
    },
}


def _production_contract_module():
    global _PRODUCTION_CONTRACT_MODULE
    if _PRODUCTION_CONTRACT_MODULE is not None:
        return _PRODUCTION_CONTRACT_MODULE
    module_name = "_agentfold_production_contract_prototype"
    if module_name in sys.modules:
        _PRODUCTION_CONTRACT_MODULE = sys.modules[module_name]
        return _PRODUCTION_CONTRACT_MODULE
    module_path = Path(__file__).resolve().parents[1] / "production-contract" / "prototype.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ContractError("production-contract prototype is not importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    _PRODUCTION_CONTRACT_MODULE = module
    return module


def _has_production_event_adapter(module):
    return all(callable(getattr(module, name, None)) for name in PRODUCTION_EVENT_ADAPTER_SYMBOLS)


def _revision_objects_from_repo(repo, revisions: tuple[str, ...]):
    return tuple(
        (
            revision,
            repo.run(
                "--no-replace-objects",
                "rev-parse",
                "--verify",
                f"{revision}:message-queue",
            ).stdout.strip(),
        )
        for revision in revisions
    )


def _typed_u_row_from_action(action, position: int):
    if action.get("finding") is not True:
        return None
    identity = action.get("identity")
    if type(identity) is not dict:
        raise ContractError(f"typed-U action {position} missing production identity")
    row_identity = {key: identity[key] for key in TYPED_U_IDENTITY_KEYS}
    path_map = action.get("paths")
    if type(path_map) is not dict:
        raise ContractError(f"typed-U action {position} missing endpoint paths")
    paths = []
    for endpoint in ("C", "O", "N"):
        values = path_map.get(endpoint, [])
        if type(values) is not list:
            raise ContractError(f"typed-U action {position} paths.{endpoint} must be an array")
        paths.extend(values)
    paths = sorted(set(paths), key=lambda item: item.encode("utf-8"))
    reason_code = action.get("reason_code")
    reason = action.get("reason")
    if type(reason_code) is not str or not reason_code:
        raise ContractError(f"typed-U action {position} missing reason code")
    if type(reason) is not str or not reason:
        raise ContractError(f"typed-U action {position} missing reason")
    row = {
        "identity": row_identity,
        "paths": paths,
        "status": action.get("status"),
        "reasons": [reason_code],
        "finding": {
            "check": TYPED_U_FINDING_CHECK,
            "subject": row_identity["production_tuple_sha256"],
            "message": reason,
            "fix": (
                "preserve one typed legal live incarnation on each required arm "
                "or leave the action blocked"
            ),
        },
    }
    return _validate_row(row, position)


def _typed_u_composition_from_audit(audit: dict, expected_common: str):
    _require_oid(expected_common, "typed-U expected common")
    if audit.get("audit_exit") == 2:
        raise ContractError("typed-U audit was unreadable")
    if audit.get("C") != expected_common:
        raise ContractError("typed-U audit common does not match merge-base proof")
    input_contract = audit.get("input_contract")
    if type(input_contract) is not dict or input_contract.get("origin_strategy") != "U":
        raise ContractError("typed-U audit was not run with Strategy U")
    classification = audit.get("classification")
    if classification == "no-finding":
        state = "clean"
    elif classification == "blocking-finding":
        state = "blocked"
    else:
        raise ContractError(f"typed-U audit is not a semantic clean/blocked result: {classification}")
    rows = []
    for position, action in enumerate(audit.get("actions", [])):
        row = _typed_u_row_from_action(action, position)
        if row is not None:
            rows.append(row)
    rows.sort(key=_row_identity_sort_key)
    if (state == "clean") != (not rows):
        raise ContractError("typed-U classification and finding rows disagree")
    evidence = audit.get("evidence_verdict")
    if type(evidence) is not dict or type(evidence.get("status")) is not str:
        raise ContractError("typed-U audit missing evidence status")
    return TypedUComposition(
        scenario=audit["scenario"],
        classification=classification,
        evidence_status=evidence["status"],
        origin_strategy="U",
        common=expected_common,
        state=state,
        rows=tuple(rows),
    )


def production_typed_u_proof(root: Path, name: str):
    if name not in TYPED_U_CASES:
        raise ValueError(f"unknown typed-U case {name}")
    module = _production_contract_module()
    # The integration target is the production-contract event boundary:
    # event_endpoints(event_kind, payload) + audit_event(root, event_kind, payload).
    # This immutable branch does not yet expose deterministic event payload builders,
    # so the compatibility path below asks the current production fixture builder and
    # Classifier for a Strategy-U result without copying classifier logic here.
    _has_production_event_adapter(module)
    fixture_case = TYPED_U_CASES[name]["fallback_case"]
    fixture = module.r18_origin_fixture(root, case=fixture_case, strategy="U")
    audit = module.Classifier(fixture).run()
    if audit["classification"] != fixture.expected:
        raise ContractError("typed-U fixture did not produce its expected classification")
    merge_bases = tuple(sorted(fixture.repo.run(
        "--no-replace-objects", "merge-base", "--all", fixture.O, fixture.N
    ).stdout.splitlines()))
    common = _single_common(merge_bases)
    composition = _typed_u_composition_from_audit(audit, common)
    if composition.state != TYPED_U_CASES[name]["expected_state"]:
        raise ContractError("typed-U fixture state did not match semantic case")
    revisions = tuple(dict.fromkeys((fixture.O, fixture.N, common)))
    return ProofInput(
        label=name,
        old=fixture.O,
        new=fixture.N,
        common=common,
        revision_objects=_revision_objects_from_repo(fixture.repo, revisions),
        authorized_deletions=(),
        store=GitSnapshotStore(root),
        typed_u=composition,
    )


class CheckBook:
    def __init__(self):
        self.checks = []
        self.damage_controls = []

    def check(self, name: str, condition, damage=False):
        if not condition:
            raise AssertionError(name)
        self.checks.append(name)
        if damage:
            self.damage_controls.append(name)

    def raises(self, name: str, exception_type, callback, damage=True):
        try:
            callback()
        except exception_type:
            self.check(name, True, damage=damage)
            return
        raise AssertionError(f"{name}: did not raise {exception_type.__name__}")


def _manual_result(result, **changes):
    changed = dict(result)
    changed.update(changes)
    return changed


def _without_subprocess_spawns(callback: Callable):
    original_run = subprocess.run
    original_popen = subprocess.Popen
    calls = []

    def forbidden_run(*_args, **_kwargs):
        calls.append("run")
        raise AssertionError("subprocess.run was called in zero-spawn control")

    def forbidden_popen(*_args, **_kwargs):
        calls.append("Popen")
        raise AssertionError("subprocess.Popen was called in zero-spawn control")

    subprocess.run = forbidden_run
    subprocess.Popen = forbidden_popen
    try:
        result = callback()
    finally:
        subprocess.run = original_run
        subprocess.Popen = original_popen
    if calls:
        raise AssertionError(f"zero-spawn control observed subprocess calls: {calls}")
    return result


def _strict_damage_controls(book: CheckBook, clean_bytes: bytes, clean_result, receipt):
    old = clean_result["old"]
    new = clean_result["new"]
    common = clean_result["common"]
    prefix = b'{"schema":"' + RESULT_SCHEMA.encode("ascii") + b'","schema":"x",'
    duplicate = prefix + clean_bytes.split(b",", 1)[1]
    book.raises("reject-duplicate-keys", ContractError, lambda: decode_result(duplicate, old, new, common))
    book.raises("reject-whitespace", ContractError, lambda: decode_result(clean_bytes.replace(b"{", b"{ ", 1), old, new, common))
    book.raises("reject-crlf", ContractError, lambda: decode_result(clean_bytes[:-1] + b"\r\n", old, new, common))
    book.raises("reject-prefix", ContractError, lambda: decode_result(b"x" + clean_bytes, old, new, common))
    book.raises("reject-suffix", ContractError, lambda: decode_result(clean_bytes + b"x", old, new, common))
    book.raises("reject-missing-lf", ContractError, lambda: decode_result(clean_bytes[:-1], old, new, common))
    escaped = clean_bytes.replace(b"restack", b"\\u0072estack", 1)
    book.raises("reject-alternate-escape", ContractError, lambda: decode_result(escaped, old, new, common))
    reordered = {
        "old": old,
        "schema": RESULT_SCHEMA,
        "new": new,
        "common": clean_result["common"],
        "state": "clean",
        "rows": [],
    }
    book.check("encode-accepts-unordered-result-dicts", encode_result(reordered) == clean_bytes)
    book.raises(
        "observed-red-unsorted-result-key-order-refuses",
        ContractError,
        lambda: decode_result(_dump_insertion_order_for_test(reordered), old, new, common),
    )
    receipt_value = decode_receipt(receipt)
    book.check(
        "receipt-decode-exact-byte-bound-succeeds",
        decode_receipt(receipt, ReceiptLimits(max_bytes=len(receipt))) == receipt_value,
        damage=True,
    )
    book.raises(
        "observed-red-receipt-byte-limit-plus-one-refuses",
        ContractError,
        lambda: decode_receipt(receipt, ReceiptLimits(max_bytes=len(receipt) - 1)),
    )
    book.raises(
        "observed-red-receipt-zero-byte-budget-refuses",
        ContractError,
        lambda: decode_receipt(receipt, ReceiptLimits(max_bytes=0)),
    )
    reordered_receipt = {key: receipt_value[key] for key in RECEIPT_KEYS}
    book.raises(
        "reject-unsorted-receipt-key-order",
        ContractError,
        lambda: decode_receipt(_dump_insertion_order_for_test(reordered_receipt)),
    )
    book.raises(
        "observed-red-common-array-refuses",
        ContractError,
        lambda: encode_result(_manual_result(clean_result, common=[clean_result["common"]])),
    )
    book.raises(
        "observed-red-multiple-bases-refuse",
        ContractError,
        lambda: _single_common((_oid("base:1"), _oid("base:2"))),
    )
    book.raises(
        "reject-zero-bases-refuse",
        ContractError,
        lambda: _single_common(()),
    )
    book.raises(
        "observed-red-decode-byte-limit-refuses",
        ContractError,
        lambda: decode_result(
            clean_bytes,
            old,
            new,
            common,
            CodecLimits(max_bytes=len(clean_bytes) - 1, max_rows=0),
        ),
    )
    book.raises("reject-wrong-type", ContractError, lambda: encode_result(_manual_result(clean_result, old=7)))
    unknown = dict(clean_result)
    unknown["extra"] = None
    book.raises("reject-unknown-key", ContractError, lambda: encode_result(unknown))
    legacy = dict(clean_result)
    legacy["metrics"] = {"snapshot_requests": 6}
    book.raises("reject-legacy-counter-key", ContractError, lambda: encode_result(legacy))
    legacy_row = {
        "path": "message-queue/needs-agent/requests/non-blocking-x.md",
        "kind": "unauthorized-deletion",
        "old_blob": _oid("blob:x"),
        "new_blob": None,
        "reason": "old action absent without matching deletion proof",
    }
    book.raises(
        "reject-legacy-row-shape",
        ContractError,
        lambda: encode_result(_manual_result(clean_result, state="blocked", rows=[legacy_row])),
    )
    row = _row_for_change(
        "message-queue/needs-agent/requests/non-blocking-x.md",
        "unauthorized-deletion",
        _oid("blob:x"),
        None,
    )
    book.raises(
        "reject-clean-with-rows",
        ContractError,
        lambda: encode_result(_manual_result(clean_result, rows=[row])),
    )
    book.raises(
        "reject-blocked-without-rows",
        ContractError,
        lambda: encode_result(_manual_result(clean_result, state="blocked")),
    )
    book.raises(
        "reject-invocation-old-new-mismatch",
        ContractError,
        lambda: decode_result(clean_bytes, _oid("wrong-old"), new, common),
    )
    book.raises(
        "observed-red-invocation-common-mismatch-refuses",
        ContractError,
        lambda: decode_result(clean_bytes, old, new, _oid("wrong-common")),
    )
    forged_result = _manual_result(clean_result, common=_oid("forged-common"))
    forged_bytes = encode_result(forged_result)
    forged_receipt = decode_receipt(receipt)
    forged_receipt["result_sha256"] = hashlib.sha256(forged_bytes).hexdigest()
    forged_receipt_bytes = encode_receipt(forged_receipt)
    book.raises(
        "observed-red-forged-common-recomputed-receipt-refuses",
        ContractError,
        lambda: provider_projection(
            forged_bytes,
            forged_receipt_bytes,
            old,
            new,
            common,
        ),
    )
    receipt_value["exit"] = True
    book.raises("reject-bool-as-int-exit", ContractError, lambda: encode_receipt(receipt_value))
    receipt_value = decode_receipt(receipt)
    receipt_value["budget"]["used"]["reads"] = False
    book.raises("reject-bool-as-int-counter", ContractError, lambda: encode_receipt(receipt_value))
    exact_counter_receipt = decode_receipt(receipt)
    for counter in BUDGET_COUNTERS:
        exact_counter_receipt["budget"]["limits"][counter] = (
            exact_counter_receipt["budget"]["used"][counter]
        )
    book.check(
        "receipt-used-equals-non-null-limits-succeeds",
        decode_receipt(encode_receipt(exact_counter_receipt))["budget"]["limits"]
        == exact_counter_receipt["budget"]["limits"],
        damage=True,
    )
    zero_counter_receipt = decode_receipt(receipt)
    for counter in BUDGET_COUNTERS:
        zero_counter_receipt["budget"]["limits"][counter] = 0
        zero_counter_receipt["budget"]["used"][counter] = 0
    book.check(
        "receipt-zero-used-zero-limits-succeeds",
        decode_receipt(encode_receipt(zero_counter_receipt))["budget"]["used"]["spawns"]
        == 0,
        damage=True,
    )
    for counter in BUDGET_COUNTERS:
        exceeded = decode_receipt(receipt)
        exceeded["budget"]["limits"][counter] = 0
        exceeded["budget"]["used"][counter] = 1
        book.raises(
            f"observed-red-receipt-used-{counter}-exceeds-limit-refuses",
            ContractError,
            lambda exceeded=exceeded: encode_receipt(exceeded),
        )
    book.raises(
        "reject-bool-as-int-codec-bound",
        ContractError,
        lambda: CodecLimits(max_bytes=True, max_rows=1),
    )
    book.raises(
        "reject-bool-as-int-receipt-bound",
        ContractError,
        lambda: ReceiptLimits(max_bytes=True),
    )


def _budget_controls(book: CheckBook, proof: ProofInput, baseline: Execution):
    baseline_receipt = baseline.decoded_receipt
    observed = baseline_receipt["budget"]["used"]
    exact_limits = {counter: observed[counter] for counter in BUDGET_COUNTERS}
    exact = execute(proof, "identity-node-cache", limits=exact_limits, profile="exact-observed")
    book.check("exact-observed-limits-succeed", exact.result == baseline.result)
    for counter in BUDGET_COUNTERS:
        if observed[counter] <= 0:
            raise AssertionError(f"observed maximum for {counter} was not reachable")
        limits = dict(exact_limits)
        limits[counter] = observed[counter] - 1
        refused = execute(
            proof,
            "identity-node-cache",
            limits=limits,
            profile=f"observed-minus-one-{counter}",
        )
        book.check(
            f"observed-minus-one-{counter}-incomplete",
            refused.result is None
            and refused.decoded_receipt["exit"] == 2
            and refused.decoded_receipt["result_sha256"] is None,
            damage=True,
        )
    for counter in BUDGET_COUNTERS:
        meter = Budget({counter: 1})
        calls = []
        meter.perform(counter, 1, lambda: calls.append("first"))
        book.raises(
            f"n-plus-one-{counter}-precharge",
            BudgetExceeded,
            lambda counter=counter, meter=meter, calls=calls: meter.perform(
                counter, 1, lambda: calls.append("forbidden")
            ),
        )
        book.check(
            f"n-plus-one-{counter}-callback-not-run",
            calls == ["first"],
            damage=True,
        )


def _fault_controls(book: CheckBook, proof: ProofInput):
    for fault, required in (
        ("after-first-snapshot", "caches_cleared"),
        ("after-child-spawn", "children_reaped"),
        ("after-descriptor-open", "descriptors_closed"),
        ("after-result-construction", "caches_cleared"),
        ("after-cleanup", "repository_unchanged"),
        ("before-result-commit", "caches_cleared"),
    ):
        execution = execute(proof, "identity-node-cache", fault=fault)
        receipt = execution.decoded_receipt
        book.check(
            f"fault-{fault}-has-no-partial-result",
            execution.result is None
            and receipt["result_sha256"] is None
            and receipt["exit"] == 2,
            damage=True,
        )
        book.check(
            f"fault-{fault}-cleanup",
            receipt["cleanup"][required]
            and receipt["cleanup"]["repository_unchanged"]
            and receipt["cleanup"]["worktree_unchanged"]
            and receipt["cleanup"]["index_unchanged"],
            damage=True,
        )
        if fault == "after-child-spawn":
            book.check(
                "fault-child-terminated-and-reaped",
                receipt["cleanup"]["children_terminated"]
                and receipt["cleanup"]["children_reaped"],
                damage=True,
            )


def _large_proof(row_count=2048):
    entries = tuple(
        (
            f"message-queue/needs-agent/requests/non-blocking-large-{index:04d}.md",
            _oid(f"large-blob-{index:04d}"),
        )
        for index in range(row_count)
    )
    return synthetic_proof("large", entries, ())


def run_self_test():
    book = CheckBook()
    shared_path = "message-queue/needs-agent/requests/non-blocking-shared.md"
    shared_blob = _oid("shared-blob")
    shared = synthetic_proof(
        "shared-subtree",
        ((shared_path, shared_blob),),
        ((shared_path, shared_blob),),
        shared_subtree=True,
    )
    granular = execute(shared, "identity-node-cache")
    batch = execute(shared, "shared-object-batch")
    book.check("synthetic-cross-implementation-byte-parity", granular.result == batch.result)
    granular_receipt = granular.decoded_receipt
    batch_receipt = batch.decoded_receipt
    zero_spawn_synthetic = _without_subprocess_spawns(
        lambda: execute(
            shared,
            "identity-node-cache",
            limits={"spawns": 0},
            profile="zero-spawn-synthetic",
        )
    )
    zero_spawn_synthetic_receipt = zero_spawn_synthetic.decoded_receipt
    book.check(
        "synthetic-zero-spawns-accepts-no-spawn",
        zero_spawn_synthetic.result == granular.result
        and zero_spawn_synthetic_receipt["exit"] == 0
        and zero_spawn_synthetic_receipt["budget"]["used"]["spawns"] == 0,
        damage=True,
    )
    book.check(
        "synthetic-granular-counterexample-is-6-5",
        granular_receipt["budget"]["used"]["snapshot_requests"] == 6
        and granular_receipt["budget"]["used"]["cache_hits"] == 5,
    )
    book.check(
        "synthetic-batch-counterexample-is-1-0",
        batch_receipt["budget"]["used"]["snapshot_requests"] == 1
        and batch_receipt["budget"]["used"]["cache_hits"] == 0,
    )
    book.check("receipts-may-differ", granular.receipt != batch.receipt)
    book.check(
        "receipts-bind-one-semantic-digest",
        granular_receipt["result_sha256"] == batch_receipt["result_sha256"]
        == hashlib.sha256(granular.result).hexdigest(),
    )
    clean_result = decode_result(granular.result, shared.old, shared.new, shared.common)
    book.check("strict-result-byte-round-trip", encode_result(clean_result) == granular.result)
    book.check("strict-receipt-byte-round-trip", encode_receipt(granular_receipt) == granular.receipt)
    _strict_damage_controls(book, granular.result, clean_result, granular.receipt)

    blocked_path = "message-queue/needs-agent/requests/non-blocking-blocked.md"
    blocked_blob = _oid("blocked-blob")
    synthetic_blocked = synthetic_proof(
        "synthetic-blocked", ((blocked_path, blocked_blob),), ()
    )
    blocked_granular = execute(synthetic_blocked, "identity-node-cache")
    blocked_batch = execute(synthetic_blocked, "shared-object-batch")
    decoded_blocked = decode_result(
        blocked_granular.result,
        synthetic_blocked.old,
        synthetic_blocked.new,
        synthetic_blocked.common,
    )
    book.check("synthetic-divergent-blocked-parity", blocked_granular.result == blocked_batch.result)
    book.check(
        "synthetic-divergent-blocked-row",
        decoded_blocked["state"] == "blocked" and len(decoded_blocked["rows"]) == 1,
    )
    synthetic_fast_forward = synthetic_proof(
        "synthetic-fast-forward",
        ((shared_path, shared_blob),),
        ((shared_path, shared_blob),),
        shared_subtree=True,
    )
    fast_forward = execute(synthetic_fast_forward, "shared-object-batch")
    book.check(
        "synthetic-fast-forward-clean",
        decode_result(
            fast_forward.result,
            synthetic_fast_forward.old,
            synthetic_fast_forward.new,
            synthetic_fast_forward.common,
        )["state"] == "clean",
    )

    large = _large_proof()
    large_granular = execute(large, "identity-node-cache")
    large_batch = execute(large, "shared-object-batch")
    large_result = decode_result(large_granular.result, large.old, large.new, large.common)
    book.check("large-2048-row-parity", large_granular.result == large_batch.result)
    book.check("large-2048-row-state", len(large_result["rows"]) == 2048 and large_result["state"] == "blocked")
    exact_codec = CodecLimits(max_bytes=len(large_granular.result), max_rows=2048)
    book.check(
        "serialization-exact-byte-and-row-bounds-succeed",
        encode_result(large_result, exact_codec) == large_granular.result,
    )
    book.raises(
        "serialization-byte-bound-minus-one-refuses",
        ContractError,
        lambda: encode_result(
            large_result,
            CodecLimits(max_bytes=len(large_granular.result) - 1, max_rows=2048),
        ),
    )
    book.raises(
        "serialization-row-bound-minus-one-refuses",
        ContractError,
        lambda: encode_result(
            large_result,
            CodecLimits(max_bytes=len(large_granular.result), max_rows=2047),
        ),
    )

    with tempfile.TemporaryDirectory(prefix="edge-semantic-real-") as temporary:
        fixture_root = Path(temporary)
        real_proofs = {
            "divergent-clean": real_git_proof(fixture_root / "s1", edge_witness.fixture_s1),
            "divergent-blocked": real_git_proof(fixture_root / "s2", edge_witness.fixture_s2),
            "shared-subtree": real_git_proof(fixture_root / "s7", edge_witness.fixture_s7),
            "fast-forward": real_git_proof(fixture_root / "s8", edge_witness.fixture_s8),
        }
        executions = {}
        for name, proof in real_proofs.items():
            left = execute(proof, "identity-node-cache")
            right = execute(proof, "shared-object-batch")
            executions[name] = left
            book.check(f"real-git-{name}-byte-parity", left.result == right.result)
            book.check(
                f"real-git-{name}-repository-cleanup",
                all(left.decoded_receipt["cleanup"].values())
                and all(right.decoded_receipt["cleanup"].values()),
            )
        book.check(
            "real-git-divergent-clean-state",
            decode_result(
                executions["divergent-clean"].result,
                real_proofs["divergent-clean"].old,
                real_proofs["divergent-clean"].new,
                real_proofs["divergent-clean"].common,
            )["state"] == "clean",
        )
        book.check(
            "real-git-divergent-blocked-state",
            decode_result(
                executions["divergent-blocked"].result,
                real_proofs["divergent-blocked"].old,
                real_proofs["divergent-blocked"].new,
                real_proofs["divergent-blocked"].common,
            )["state"] == "blocked",
        )
        book.check(
            "real-git-fast-forward-clean-state",
            decode_result(
                executions["fast-forward"].result,
                real_proofs["fast-forward"].old,
                real_proofs["fast-forward"].new,
                real_proofs["fast-forward"].common,
            )["state"] == "clean",
        )
        real_left = executions["shared-subtree"].decoded_receipt
        real_right = execute(
            real_proofs["shared-subtree"], "shared-object-batch"
        ).decoded_receipt
        book.check(
            "real-git-counterexample-is-6-5-versus-1-0",
            (
                real_left["budget"]["used"]["snapshot_requests"],
                real_left["budget"]["used"]["cache_hits"],
                real_right["budget"]["used"]["snapshot_requests"],
                real_right["budget"]["used"]["cache_hits"],
            ) == (6, 5, 1, 0),
        )
        _budget_controls(book, real_proofs["divergent-blocked"], executions["divergent-blocked"])
        _fault_controls(book, real_proofs["divergent-blocked"])
        zero_spawn_real = _without_subprocess_spawns(
            lambda: execute(
                real_proofs["divergent-blocked"],
                "identity-node-cache",
                limits={"spawns": 0},
                profile="zero-spawn-real",
            )
        )
        zero_spawn_real_receipt = zero_spawn_real.decoded_receipt
        book.check(
            "observed-red-real-zero-spawns-no-result",
            zero_spawn_real.result is None
            and zero_spawn_real_receipt["exit"] == 2
            and zero_spawn_real_receipt["result_sha256"] is None
            and zero_spawn_real_receipt["budget"]["used"]["spawns"] == 0
            and zero_spawn_real_receipt["incomplete_reason"].startswith("budget:spawns:"),
            damage=True,
        )

        typed_u_proofs = {
            name: production_typed_u_proof(fixture_root / name, name)
            for name in TYPED_U_CASES
        }
        for name, proof in typed_u_proofs.items():
            left = execute(proof, "identity-node-cache")
            right = execute(proof, "shared-object-batch")
            projection = provider_projection(
                left.result,
                left.receipt,
                proof.old,
                proof.new,
                proof.common,
            )
            decoded = decode_result(left.result, proof.old, proof.new, proof.common)
            book.check(f"{name}-typed-u-byte-parity", left.result == right.result)
            book.check(
                f"{name}-typed-u-provider-projection",
                projection["conclusion"] == proof.typed_u.state == decoded["state"],
            )
            book.check(
                f"{name}-typed-u-separate-receipt",
                left.decoded_receipt["implementation"] != right.decoded_receipt["implementation"]
                and left.decoded_receipt["result_sha256"]
                == right.decoded_receipt["result_sha256"]
                == hashlib.sha256(left.result).hexdigest(),
            )
        book.check(
            "typed-u-normal-restack-clean",
            typed_u_proofs["typed-u-normal-restack"].typed_u.state == "clean",
        )
        illegal = typed_u_proofs["typed-u-illegal-birth"]
        book.check(
            "typed-u-illegal-birth-blocked-row-shape",
            illegal.typed_u.state == "blocked"
            and len(illegal.typed_u.rows) == 1
            and set(illegal.typed_u.rows[0]) == set(ROW_KEYS)
            and set(illegal.typed_u.rows[0]["identity"]) == set(TYPED_U_IDENTITY_KEYS),
        )

        clean_projection = provider_projection(
            executions["divergent-clean"].result,
            executions["divergent-clean"].receipt,
            real_proofs["divergent-clean"].old,
            real_proofs["divergent-clean"].new,
            real_proofs["divergent-clean"].common,
        )
        blocked_projection = provider_projection(
            executions["divergent-blocked"].result,
            executions["divergent-blocked"].receipt,
            real_proofs["divergent-blocked"].old,
            real_proofs["divergent-blocked"].new,
            real_proofs["divergent-blocked"].common,
        )
        incomplete_execution = execute(
            real_proofs["divergent-blocked"],
            "identity-node-cache",
            limits={"snapshot_requests": 0},
            profile="provider-incomplete",
        )
        incomplete_projection = provider_projection(
            None,
            incomplete_execution.receipt,
            real_proofs["divergent-blocked"].old,
            real_proofs["divergent-blocked"].new,
            real_proofs["divergent-blocked"].common,
        )
        book.check("provider-projects-clean", clean_projection["conclusion"] == "clean")
        book.check("provider-projects-blocked", blocked_projection["conclusion"] == "blocked")
        book.check(
            "provider-missing-result-remains-incomplete",
            incomplete_projection["conclusion"] == "incomplete",
            damage=True,
        )
        forged = executions["divergent-clean"].decoded_receipt
        forged["result_sha256"] = "0" * 64
        forged_bytes = encode_receipt(forged)
        book.raises(
            "provider-rejects-receipt-digest-mismatch",
            ContractError,
            lambda: provider_projection(
                executions["divergent-clean"].result,
                forged_bytes,
                real_proofs["divergent-clean"].old,
                real_proofs["divergent-clean"].new,
                real_proofs["divergent-clean"].common,
            ),
        )

    with tempfile.TemporaryDirectory(prefix="edge-semantic-root-a-") as root_a, tempfile.TemporaryDirectory(prefix="edge-semantic-root-b-") as root_b:
        proof_a = real_git_proof(Path(root_a) / "fixture", edge_witness.fixture_s7)
        proof_b = real_git_proof(Path(root_b) / "fixture", edge_witness.fixture_s7)
        bytes_a = execute(proof_a, "identity-node-cache").result
        bytes_b = execute(proof_b, "identity-node-cache").result
        book.check("absolute-root-does-not-change-semantic-bytes", bytes_a == bytes_b)
        book.check(
            "absolute-root-not-serialized",
            root_a.encode("utf-8") not in bytes_a and root_b.encode("utf-8") not in bytes_b,
        )

    book.check(
        "proof-cardinality-excluded-from-authority",
        set(clean_result) == set(RESULT_KEYS)
        and all("count" not in key and "metric" not in key for key in clean_result)
        and all("count" not in key and "metric" not in key for key in ROW_KEYS),
    )

    for name in book.damage_controls:
        print(json.dumps({"control": name, "status": "PASS"}, sort_keys=True, separators=(",", ":")))
    summary = {
        "summary": "PASS",
        "checks_passed": len(book.checks),
        "checks_total": len(book.checks),
        "damage_controls_passed": len(book.damage_controls),
        "damage_controls_total": len(book.damage_controls),
        "real_git_cases": 4,
        "synthetic_cases": 4,
        "typed_u_cases": len(TYPED_U_CASES),
        "large_rows": 2048,
        "counterexample": "6/5-vs-1/0",
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


def semantic_suite(implementation: str):
    shared_path = "message-queue/needs-agent/requests/non-blocking-shared.md"
    shared_blob = _oid("shared-blob")
    proofs = [
        synthetic_proof(
            "shared-subtree",
            ((shared_path, shared_blob),),
            ((shared_path, shared_blob),),
            shared_subtree=True,
        ),
        synthetic_proof(
            "suite-blocked",
            (("message-queue/needs-agent/requests/non-blocking-suite.md", _oid("suite")),),
            (),
        ),
    ]
    with tempfile.TemporaryDirectory(prefix="edge-semantic-suite-") as temporary:
        root = Path(temporary)
        proofs.extend((
            real_git_proof(root / "s1", edge_witness.fixture_s1),
            real_git_proof(root / "s2", edge_witness.fixture_s2),
            real_git_proof(root / "s7", edge_witness.fixture_s7),
            real_git_proof(root / "s8", edge_witness.fixture_s8),
        ))
        proofs.extend(
            production_typed_u_proof(root / name, name)
            for name in TYPED_U_CASES
        )
        for proof in proofs:
            execution = execute(proof, implementation)
            if execution.result is None:
                raise SystemExit(execution.decoded_receipt["incomplete_reason"])
            sys.stdout.buffer.write(execution.result)
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--emit-semantic-suite", action="store_true")
    parser.add_argument("--implementation", choices=IMPLEMENTATIONS)
    args = parser.parse_args(argv)
    if args.emit_semantic_suite and args.implementation is None:
        parser.error("--emit-semantic-suite requires --implementation")
    if args.self_test and args.implementation is not None:
        parser.error("--implementation is only valid with --emit-semantic-suite")
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.self_test:
        return run_self_test()
    return semantic_suite(args.implementation)


if __name__ == "__main__":
    raise SystemExit(main())
