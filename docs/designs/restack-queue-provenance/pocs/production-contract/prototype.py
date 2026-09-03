#!/usr/bin/env python3
"""Real-Git POC for the C-rooted production restack contract.

This executable imports AgentFold's current queue identity and deletion
validator.  It changes no production behavior.
"""

from __future__ import annotations

import argparse
import contextlib
import contextvars
import dataclasses
import datetime
import errno
import functools
import gc
import hashlib
import importlib.util
import inspect
import io
import json
import operator
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
from typing import Any, Callable, ContextManager, Iterable, Mapping, Protocol
import uuid


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[5]
RECONCILE_PATH = REPOSITORY / "automation/reconcile/reconcile.py"
REAL_RUN = subprocess.run
REAL_POPEN = subprocess.Popen
FIXTURE_DATE = datetime.date(2026, 9, 2)
INVALID_EVENT_KIND_EVIDENCE = None


class GitSpawnObserver(Protocol):
    """Result-blind notifications around each production-owned Git spawn."""

    def before_spawn(self, command: tuple[str, ...]) -> None:
        """Precharge one exact immutable command before process creation."""

    def after_spawn(
        self, command: tuple[str, ...], pid: int | None
    ) -> None:
        """Observe that production created the process with this PID."""


class TrustedGitRunner(Protocol):
    """Explicit authority that creates one Git process without ambient lookup."""

    def __call__(self, command, *args, **kwargs) -> subprocess.Popen:
        """Create exactly the requested Git child."""


def emit_json(value: Any):
    """Write one canonical sorted-key UTF-8 JSONL record."""
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    sys.stdout.buffer.write(encoded + b"\n")


def load_reconciler(owner=None):
    name = (
        __name__.replace(".", "_")
        + "_private_reconcile_"
        + uuid.uuid4().hex
    )
    spec = importlib.util.spec_from_file_location(
        name, RECONCILE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {RECONCILE_PATH}")
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules[spec.name] = module
        if owner is not None:
            # Publish module ownership before executing imported code.  The
            # loader removes its own registration on every throwable before
            # this publication, and RepositorySession.close owns every
            # throwable after it.
            owner._reconcile_registration = (spec.name, module)
            owner._reconcile_name = spec.name
            owner.reconcile = module
        spec.loader.exec_module(module)
        # Fixture bytes must not expire when wall-clock UTC crosses midnight.
        module.TODAY = FIXTURE_DATE
    except BaseException:
        if sys.modules.get(spec.name) is module:
            sys.modules.pop(spec.name, None)
        if (
            owner is not None
            and owner._reconcile_registration == (spec.name, module)
        ):
            owner._reconcile_registration = None
            owner._reconcile_name = None
            owner.reconcile = None
        raise
    return module


ACTIVE_RECONCILE = contextvars.ContextVar(
    "production_contract_active_reconciler", default=None
)


class ReconcilerProxy:
    """Resolve reconciler state from the currently active repository session."""

    def __getattr__(self, name):
        reconcile = ACTIVE_RECONCILE.get()
        if reconcile is None:
            raise Unreadable(
                "production reconciler used outside a repository session"
            )
        return getattr(reconcile, name)


RECONCILE = ReconcilerProxy()


def _trusted_git_runner() -> TrustedGitRunner:
    """Return the immutable process factory used by POC-owned CLI/tests."""
    return REAL_POPEN


class Unreadable(RuntimeError):
    """Required immutable Git evidence could not be read."""


class BudgetExceeded(RuntimeError):
    """A measured operation was refused before its work began."""

    def __init__(self, counter: str, value: int, limit: int):
        super().__init__(f"{counter}={value}>{limit}")
        self.counter = counter
        self.value = value
        self.limit = limit
        self.C: str | None = None


@dataclasses.dataclass
class Metrics:
    git_process_attempts: int = 0
    git_processes: int = 0
    graph_enumerations: int = 0
    graph_commits: int = 0
    graph_parent_edges: int = 0
    graph_output_bytes: int = 0
    graph_line_bytes: int = 0
    graph_line_peak_bytes: int = 0
    graph_lines: int = 0
    graph_commit_tokens: int = 0
    graph_parent_tokens: int = 0
    graph_process_terminations: int = 0
    graph_process_reaps: int = 0
    graph_process_cleanup_checks: int = 0
    graph_buffered_bytes: int = 0
    graph_stream_chunks: int = 0
    graph_stream_peak_chunk_bytes: int = 0
    merge_base_output_bytes: int = 0
    merge_base_line_bytes: int = 0
    merge_base_line_peak_bytes: int = 0
    merge_base_lines: int = 0
    merge_base_tokens: int = 0
    merge_base_process_terminations: int = 0
    merge_base_process_reaps: int = 0
    shallow_output_bytes: int = 0
    shallow_line_bytes: int = 0
    shallow_line_peak_bytes: int = 0
    shallow_lines: int = 0
    shallow_tokens: int = 0
    shallow_process_terminations: int = 0
    shallow_process_reaps: int = 0
    batch_processes: int = 0
    object_reads: int = 0
    object_cache_hits: int = 0
    object_header_bytes: int = 0
    object_payload_bytes: int = 0
    object_payload_peak_bytes: int = 0
    object_process_terminations: int = 0
    object_process_reaps: int = 0
    tree_entries: int = 0
    tree_entry_name_bytes: int = 0
    flattened_paths: int = 0
    flattened_path_bytes: int = 0
    flat_tree_peak_paths: int = 0
    queue_snapshots_requested: int = 0
    queue_subtree_reads: int = 0
    snapshot_cache_hits: int = 0
    queue_paths: int = 0
    queue_path_bytes: int = 0
    queue_blob_bytes: int = 0
    identity_calls: int = 0
    authority_calls: int = 0
    support_certificate_calls: int = 0
    support_adoption_checks: int = 0
    support_paths_checked: int = 0
    support_delta_candidates: int = 0
    support_delta_rows: int = 0
    support_referenced_paths: int = 0
    support_anchor_rows: int = 0
    support_obligations: int = 0
    support_serialized_bytes: int = 0
    dynamic_support_paths_traversed: int = 0
    dynamic_support_paths_discovered: int = 0
    dynamic_support_path_bytes: int = 0
    mutation_calls: int = 0
    per_action_history_walks: int = 0
    carry_proof_nodes: int = 0
    carry_proof_edges: int = 0
    origin_arm_nodes: int = 0
    origin_parent_edges: int = 0
    origin_births: int = 0
    origin_witness_bytes: int = 0
    production_helper_calls: int = 0
    production_helper_input_bytes: int = 0
    production_parent_queries: int = 0
    git_stderr_bytes: int = 0
    _budget_limit: int | None = dataclasses.field(
        default=None, repr=False
    )
    _posthoc_budget_accounting: bool = dataclasses.field(
        default=False, repr=False
    )
    _budget_limits: dict[str, int] = dataclasses.field(
        default_factory=dict, repr=False
    )

    HARD_LIMITS = {
        "graph_output_bytes": 8 * 1024 * 1024,
        "graph_line_bytes": 8 * 1024 * 1024,
        "graph_line_peak_bytes": 1024 * 1024,
        "graph_lines": 200_000,
        "graph_commit_tokens": 200_000,
        "graph_parent_tokens": 1_000_000,
        "merge_base_output_bytes": 1024 * 1024,
        "merge_base_line_bytes": 1024 * 1024,
        "merge_base_line_peak_bytes": 1024,
        "merge_base_lines": 20_000,
        "merge_base_tokens": 20_000,
        "shallow_output_bytes": 64,
        "shallow_line_bytes": 63,
        "shallow_line_peak_bytes": 16,
        "shallow_lines": 2,
        "shallow_tokens": 2,
        "object_header_bytes": 64 * 1024 * 1024,
        "object_payload_bytes": 64 * 1024 * 1024,
        "object_payload_peak_bytes": 8 * 1024 * 1024,
        "tree_entries": 1_000_000,
        "tree_entry_name_bytes": 64 * 1024 * 1024,
        "flattened_paths": 1_000_000,
        "flattened_path_bytes": 64 * 1024 * 1024,
        "flat_tree_peak_paths": 1_000_000,
        "queue_paths": 1_000_000,
        "queue_path_bytes": 64 * 1024 * 1024,
        "queue_blob_bytes": 64 * 1024 * 1024,
        "support_delta_candidates": 1_000_000,
        "support_delta_rows": 1_000_000,
        "support_referenced_paths": 1_000_000,
        "support_anchor_rows": 1_000_000,
        "support_obligations": 1_000_000,
        "support_serialized_bytes": 64 * 1024 * 1024,
        "dynamic_support_paths_traversed": 1_000_000,
        "dynamic_support_paths_discovered": 1_000_000,
        "dynamic_support_path_bytes": 64 * 1024 * 1024,
        "production_helper_input_bytes": 64 * 1024 * 1024,
        "origin_arm_nodes": 1_000_000,
        "origin_parent_edges": 1_000_000,
        "origin_births": 1_000_000,
        "origin_witness_bytes": 64 * 1024 * 1024,
        "git_stderr_bytes": 1024 * 1024,
    }

    def configure_budget(
        self,
        limit: int | None,
        *,
        limits: dict[str, int] | None = None,
        posthoc_budget_accounting: bool = False,
    ):
        self._budget_limit = limit
        self._budget_limits = dict(limits or {})
        self._posthoc_budget_accounting = posthoc_budget_accounting

    def limit_for(self, counter: str) -> int | None:
        if counter in self._budget_limits:
            return self._budget_limits[counter]
        if self._budget_limit is not None:
            return self._budget_limit
        return self.HARD_LIMITS.get(counter)

    def charge(self, counter: str, amount: int = 1):
        """Charge before work; record only limit+1 when refusing a batch."""
        if amount < 0 or not hasattr(self, counter) or counter.startswith("_"):
            raise ValueError(f"invalid metric charge {counter}={amount}")
        current = getattr(self, counter)
        attempted = current + amount
        limit = self.limit_for(counter)
        if (
            limit is not None
            and not self._posthoc_budget_accounting
            and attempted > limit
        ):
            refused = limit + 1
            setattr(self, counter, refused)
            raise BudgetExceeded(counter, refused, limit)
        setattr(self, counter, attempted)

    def observe(self, counter: str, amount: int = 1):
        """Record cleanup already performed; cleanup itself is never refused."""
        if amount < 0 or not hasattr(self, counter) or counter.startswith("_"):
            raise ValueError(f"invalid metric observation {counter}={amount}")
        setattr(self, counter, getattr(self, counter) + amount)

    def admit_peak(self, counter: str, value: int):
        """Refuse an individual allocation before it exceeds its peak cap."""
        if value < 0 or not hasattr(self, counter) or counter.startswith("_"):
            raise ValueError(f"invalid metric peak {counter}={value}")
        limit = self.limit_for(counter)
        if (
            limit is not None
            and not self._posthoc_budget_accounting
            and value > limit
        ):
            setattr(self, counter, limit + 1)
            raise BudgetExceeded(counter, limit + 1, limit)
        setattr(self, counter, max(getattr(self, counter), value))

    def as_dict(self):
        return {
            field.name: getattr(self, field.name)
            for field in dataclasses.fields(self)
            if not field.name.startswith("_")
        }


@dataclasses.dataclass(frozen=True)
class ActionState:
    path: str
    text: str
    blob_oid: str


@dataclasses.dataclass
class _Fixture:
    scenario: str
    repo: "GitRepository"
    expected_C: str
    O: str
    candidate_landmark: str
    N: str
    expected: str
    details: dict = dataclasses.field(default_factory=dict)
    budget_limit: int | None = None
    budget_limits: dict[str, int] = dataclasses.field(default_factory=dict)
    origin_strategy: str = "U"


@dataclasses.dataclass(frozen=True)
class RepositoryView:
    root: Path


@dataclasses.dataclass
class Damage:
    validate_all_direct_parents: bool = True
    allow_supplier_borrow: bool = False
    collapse_multiplicity: bool = False
    reopen_pre_c_genealogy: bool = False
    enforce_post_event_absence: bool = True
    sole_valid_ignores_competitors: bool = False
    omit_old_tip_human_binding: bool = False
    treat_review_pending_as_concrete: bool = False
    broad_review_pending_normalization: bool = False
    omit_supplier_carrier_human_binding: bool = False
    omit_unanswered_published_review_binding: bool = False
    skip_preserved_state_validation: bool = False
    skip_persisted_frozen_skeleton: bool = False
    skip_persisted_candidate_continuity: bool = False
    skip_old_side_continuity: bool = False
    skip_supplier_support_certificate: bool = False
    universal_ancestor_carry_scan: bool = False
    ignore_outside_c_collision: bool = False
    ignore_absent_c_arm: bool = False
    first_parent_carry_only: bool = False
    skip_carry_compatibility: bool = False
    unmetered_cone_work: bool = False
    posthoc_budget_accounting: bool = False
    ambient_git_diagnostics: bool = False
    reopen_outside_c_boundary_ancestry: bool = False
    buffered_graph_output: bool = False
    unmetered_object_bytes: bool = False
    unmetered_tree_paths: bool = False
    unmetered_dynamic_support: bool = False
    unmetered_support_construction: bool = False
    endpoint_only_origin_equality: bool = False
    skip_origin_birth_uniqueness: bool = False
    skip_origin_post_birth_absence: bool = False
    skip_origin_endpoint_non_regression: bool = False
    reject_all_origin_invalid_carriers: bool = False
    leak_object_database_pipes: bool = False


@dataclasses.dataclass
class Event:
    status: str
    mode: str
    child: str | None
    authority_edges: list[dict]
    propagation_edges: list[dict]
    neutral_parents: list[str]
    absent_parents: list[str]
    reason_code: str
    reason: str
    causal_roots: list[dict] = dataclasses.field(default_factory=list)
    reason_records: list[dict] = dataclasses.field(default_factory=list)
    support_checks: list[dict] = dataclasses.field(default_factory=list)
    carry_proofs: list[dict] = dataclasses.field(default_factory=list)


class EventInputError(ValueError):
    """An immutable event does not contain usable restack endpoints."""


@dataclasses.dataclass(frozen=True)
class EventEndpoints:
    """Exact immutable old/new endpoints derived without mutable state."""

    O: str
    N: str
    event_kind: str
    endpoint_sources: tuple[str, str]

    def evidence(self) -> dict:
        return {
            "N": self.N,
            "O": self.O,
            "endpoint_sources": list(self.endpoint_sources),
            "event_kind": self.event_kind,
            "github_sha_used": False,
            "mutable_metadata_invariant": True,
            "mutable_state_reads": 0,
            "provider_api_calls": 0,
            "reason": None,
            "status": "accepted",
            "typed_origin_strategy": "U",
        }


def event_endpoints(
    event_kind: str,
    payload: Mapping[str, Any],
) -> EventEndpoints:
    """Derive exact O/N from one explicit immutable transport payload.

    Supported local and pre-push calls provide ``old``/``new`` directly.
    Push uses immutable ``before``/``after``.  Pull-request synchronize uses
    top-level ``before``/``after`` and requires ``after`` to equal the embedded
    head SHA.  This pure function has no repository, provider API, current-ref,
    environment, or ``github.sha`` input.
    """

    if type(event_kind) is not str:
        raise EventInputError(
            "coverage-unavailable: event kind must be a string"
        )
    if not isinstance(payload, Mapping):
        raise EventInputError(
            "coverage-unavailable: event payload must be a mapping"
        )

    def field(container: Mapping[str, Any], name: str, label: str) -> str:
        value = container.get(name)
        if not isinstance(value, str) or not value:
            raise EventInputError(
                f"coverage-unavailable: {label} is missing"
            )
        return value

    if event_kind in {"local", "pre-push"}:
        O = field(payload, "old", f"{event_kind}.old")
        N = field(payload, "new", f"{event_kind}.new")
        sources = ("explicit old", "explicit new")
    elif event_kind == "push":
        O = field(payload, "before", "push.before")
        N = field(payload, "after", "push.after")
        sources = ("immutable push.before", "immutable push.after")
    elif event_kind == "pull-request-synchronize":
        O = field(payload, "before", "pull_request.synchronize.before")
        N = field(payload, "after", "pull_request.synchronize.after")
        pull_request = payload.get("pull_request")
        if not isinstance(pull_request, Mapping):
            raise EventInputError(
                "coverage-unavailable: pull_request object is missing"
            )
        head = pull_request.get("head")
        if not isinstance(head, Mapping):
            raise EventInputError(
                "coverage-unavailable: pull_request.head is missing"
            )
        head_sha = field(
            head, "sha", "pull_request.synchronize.pull_request.head.sha"
        )
        if N != head_sha:
            raise EventInputError(
                "coverage-unavailable: pull_request.synchronize after "
                "does not equal pull_request.head.sha"
            )
        sources = (
            "immutable pull_request.synchronize.before",
            "immutable pull_request.synchronize.after",
        )
    else:
        raise EventInputError(
            f"coverage-unavailable: unsupported event kind {event_kind!r}"
        )

    for label, oid in (("O", O), ("N", N)):
        if not (
            len(oid) in {40, 64}
            and all(char in "0123456789abcdef" for char in oid)
        ):
            raise EventInputError(
                f"coverage-unavailable: {label} is not a full lowercase Git OID"
            )
        if not oid.strip("0"):
            raise EventInputError(
                f"coverage-unavailable: {label} is the zero OID"
            )
    if O == N:
        raise EventInputError(
            "coverage-unavailable: O and N must be distinct Git OIDs"
        )
    return EventEndpoints(O, N, event_kind, sources)


def valid_budget_limit(value: Any) -> bool:
    """Accept only an exact positive integer or the unbounded sentinel."""
    return value is None or (type(value) is int and value > 0)


def is_git_command(command) -> bool:
    return bool(
        isinstance(command, (tuple, list))
        and command
        and Path(str(command[0])).name in {"git", "git.exe"}
    )


def stable_git_environment(environment=None):
    result = dict(os.environ if environment is None else environment)
    result.update(
        {
            "LANG": "C",
            "LANGUAGE": "C",
            "LC_ALL": "C",
            "TZ": "UTC",
        }
    )
    return result


def stable_git_failure(arguments, stderr: str) -> str:
    oids = re.findall(r"(?<![0-9a-f])[0-9a-f]{40,64}(?![0-9a-f])", stderr)
    if oids:
        return f"missing-or-malformed-commit:{oids[0]}"
    operation = next(
        (argument for argument in arguments if not argument.startswith("-")),
        "unknown",
    )
    return f"git-command-failed:{operation}"


def descriptor_is_closed(descriptor: int) -> bool:
    """Prove that one captured OS descriptor is no longer open."""
    try:
        os.fstat(descriptor)
    except OSError as error:
        if error.errno == errno.EBADF:
            return True
        raise
    return False


def is_cancellation(error: BaseException) -> bool:
    return isinstance(error, (KeyboardInterrupt, SystemExit))


def cleanup_failure_text(error: BaseException) -> str:
    if isinstance(error, Unreadable):
        return str(error)
    return f"{type(error).__name__} during resource cleanup"


def _spawn_boundary(_name: str) -> None:
    """Named no-op used by deterministic construction cancellation controls."""


def _session_boundary(_name: str) -> None:
    """Named no-op used by deterministic session cancellation controls."""


def _pipe_boundary(_name: str) -> None:
    """Named no-op used by deterministic pipe-publication controls."""


def publish_call_result(target: list, callback: Callable[[], Any]) -> None:
    """Call and publish a returned resource before Python regains control.

    The nested C iterators close the CPython opcode gap between a resource
    factory's return and ``STORE_FAST`` in its caller: the inner map invokes
    the callback and the outer map appends its result to the already-published
    list before either iterator returns to Python bytecode.  The caller still
    owns ordinary exception cleanup once the list contains the result.
    """
    tuple(map(target.append, map(operator.call, (callback,))))


def raise_deferred_cleanup(
    failures: list[BaseException], prefix: str
) -> None:
    """Raise cancellation after cleanup, otherwise one stable unreadable."""
    cancellation = next(
        (error for error in failures if is_cancellation(error)), None
    )
    if cancellation is not None:
        cleanup_failures = [
            cleanup_failure_text(error)
            for error in failures
            if error is not cancellation
        ]
        if cleanup_failures:
            cancellation.add_note(
                prefix
                + ": "
                + "; ".join(dict.fromkeys(cleanup_failures))
            )
        raise cancellation
    if failures:
        raise Unreadable(
            prefix
            + ": "
            + "; ".join(
                dict.fromkeys(cleanup_failure_text(error) for error in failures)
            )
        ) from failures[0]


@dataclasses.dataclass
class OwnedPipe:
    """One captured process pipe whose ownership is consumed exactly once."""

    label: str
    object_ref: Any | None
    descriptor: int | None
    state: str = "OPEN"
    backing_ref: Any | None = None


class OwnedPipeView:
    """A non-owning Python view whose close consumes one raw-fd token."""

    def __init__(self, file_object: Any, ownership: OwnedPipe):
        self._file_object = file_object
        self._ownership = ownership

    def __getattr__(self, name):
        return getattr(self._file_object, name)

    @property
    def closed(self):
        return self._file_object.closed

    def fileno(self):
        return self._file_object.fileno()

    def _close_nonowning(self):
        self._file_object.close()

    def close(self):
        close_owned_pipe(self._ownership, self, os.close)


def close_raw_owned_pipe(
    ownership: OwnedPipe,
    raw_close: Callable[[int], None],
) -> None:
    """Consume one raw descriptor token before its only close attempt.

    A throwing close is inherently ambiguous: the delegate may have closed the
    descriptor before it threw.  The token therefore becomes UNKNOWN and is
    never retried, even if the numeric descriptor is subsequently reused.
    """
    if ownership.state == "CLOSED":
        return
    if ownership.state == "UNKNOWN":
        raise Unreadable(
            f"Git child {ownership.label} descriptor state remains unknown"
        )
    descriptor = ownership.descriptor
    if descriptor is None:
        ownership.state = "UNKNOWN"
        raise Unreadable(
            f"Git child {ownership.label} lost its owned descriptor"
        )
    # UNKNOWN is durable before delegation.  A callback may close and then
    # throw, so retaining the numeric fd would make a later pass unsafe after
    # descriptor reuse.
    ownership.state = "UNKNOWN"
    ownership.descriptor = None
    try:
        raw_close(descriptor)
    except BaseException:
        raise
    ownership.state = "CLOSED"


def close_owned_pipe(
    ownership: OwnedPipe,
    current_pipe,
    raw_close: Callable[[int], None],
):
    """Consume captured ownership without granting authority to a replacement.

    ``current_pipe`` is only an identity check.  A caller may have replaced the
    public process attribute with arbitrary code that retains the captured
    integer, closes it, reuses it, and then returns or throws.  Invoking that
    replacement before the raw close would make the local integer unsafe, so
    cleanup operates only on the internally captured non-owning view.
    """
    if ownership.state == "CLOSED":
        return
    if ownership.state == "UNKNOWN":
        raise Unreadable(
            f"Git child {ownership.label} descriptor state remains unknown"
        )
    descriptor = ownership.descriptor
    original = ownership.object_ref
    if original is None or descriptor is None:
        ownership.state = "UNKNOWN"
        ownership.descriptor = None
        raise Unreadable(
            f"Git child {ownership.label} has no captured pipe view"
        )

    # Consume the integer before *any* close callback.  The captured view was
    # created with closefd=False, so closing it cannot consume or later reuse
    # the OS descriptor.  Only raw_close receives the local integer, exactly
    # once; any throwable from it leaves durable UNKNOWN ownership.
    ownership.state = "UNKNOWN"
    ownership.descriptor = None
    failures: list[BaseException] = []
    if current_pipe is not None and current_pipe is not original:
        failures.append(
            Unreadable(
                f"Git child {ownership.label} public pipe no longer matches "
                "captured ownership"
            )
        )
    # The sole raw close precedes object cleanup.  Even an adversarial test
    # double in the object slot therefore cannot close the old integer, reuse
    # it, and trick the raw fallback into closing unrelated storage.
    try:
        raw_close(descriptor)
    except BaseException as error:
        failures.append(error)
    else:
        ownership.state = "CLOSED"
    backing = ownership.backing_ref
    if backing is None:
        failures.append(
            Unreadable(
                f"Git child {ownership.label} lost its captured backing view"
            )
        )
    else:
        try:
            # The immutable backing reference was captured before a public
            # process attribute or the view's mutable delegate could be
            # replaced.  Calling the built-in type implementation bypasses
            # per-instance substitution.  The backing is closefd=False, so
            # this can never consume a reused OS descriptor.
            type(backing).close(backing)
        except BaseException as error:
            failures.append(error)

    cancellation = next(
        (error for error in failures if is_cancellation(error)), None
    )
    if cancellation is not None:
        raise cancellation
    if failures:
        raise Unreadable(
            f"Git child {ownership.label} cleanup ended "
            f"{ownership.state.lower()}"
        ) from failures[0]


def cleanup_unclaimed_process(
    process: subprocess.Popen,
    owned_pipes: dict[str, OwnedPipe],
    explicit_resources=None,
) -> None:
    """Reap and close a spawned child that an observer refused to accept."""
    failures: list[BaseException] = []
    try:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        if process.poll() is None:
            failures.append(Unreadable("child was not reaped"))
    except BaseException as error:
        failures.append(error)
        try:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
        except BaseException as cleanup_error:
            failures.append(cleanup_error)
    for label in ("stdin", "stdout", "stderr"):
        ownership = owned_pipes.get(label)
        if ownership is None:
            continue
        try:
            close_owned_pipe(
                ownership, getattr(process, label, None), os.close
            )
        except BaseException as error:
            failures.append(error)
    try:
        close_explicit_pipe_resources(explicit_resources)
    except BaseException as error:
        failures.append(error)
    raise_deferred_cleanup(failures, "Git spawn observer cleanup failed")


def retire_process_pipes(process: subprocess.Popen) -> None:
    """Consume every production pipe token once after normal child use."""
    failures: list[BaseException] = []
    owned_pipes = getattr(process, "_agentfold_owned_pipes", {})
    for label in ("stdin", "stdout", "stderr"):
        ownership = owned_pipes.get(label)
        if ownership is None:
            continue
        try:
            close_owned_pipe(
                ownership, getattr(process, label, None), os.close
            )
        except BaseException as error:
            failures.append(error)
    raise_deferred_cleanup(failures, "Git child pipe cleanup failed")


def prepare_explicit_parent_pipes(
    labels: tuple[str, ...],
    *,
    pipe_factory: Callable[[], tuple[int, int]] = os.pipe,
    raw_close: Callable[[int], None] = os.close,
    publication_boundary: Callable[[str], None] = _pipe_boundary,
):
    """Create parent-owned fds and child-side ints without Popen PIPE owners."""
    resources = {}
    opened: list[OwnedPipe] = []
    # Each raw pair is published by the C bridge before Python can receive a
    # cancellation.  It remains a construction registry until return; the
    # rollback path deduplicates it against any OwnedPipe tokens already made.
    raw_pairs: list[tuple[int, int]] = []
    try:
        for label in labels:
            publish_call_result(raw_pairs, pipe_factory)
            publication_boundary("after-pipe-return-publication")
            read_fd, write_fd = raw_pairs[-1]
            read = OwnedPipe(f"{label}-read", None, read_fd)
            write = OwnedPipe(f"{label}-write", None, write_fd)
            opened.extend((read, write))
            if label == "stdin":
                resources[label] = {
                    "child": read, "parent": write, "mode": "wb"
                }
            elif label in {"stdout", "stderr"}:
                resources[label] = {
                    "child": write, "parent": read, "mode": "rb"
                }
            else:
                raise ValueError(f"unsupported explicit pipe {label}")
        return resources
    except BaseException as primary:
        failures: list[BaseException] = [primary]
        by_descriptor = {
            ownership.descriptor: ownership
            for ownership in opened
            if ownership.descriptor is not None
        }
        for pair in raw_pairs:
            if (
                not isinstance(pair, tuple)
                or len(pair) != 2
                or any(type(item) is not int for item in pair)
            ):
                failures.append(
                    Unreadable("Git pipe factory returned an invalid pair")
                )
                continue
            for descriptor in pair:
                if descriptor not in by_descriptor:
                    ownership = OwnedPipe(
                        "construction-unpublished", None, descriptor
                    )
                    opened.append(ownership)
                    by_descriptor[descriptor] = ownership
        for ownership in by_descriptor.values():
            try:
                close_raw_owned_pipe(ownership, raw_close)
            except BaseException as error:
                failures.append(error)
        raise_deferred_cleanup(failures, "Git pipe setup rollback failed")


def attach_explicit_parent_pipes(
    process,
    resources,
    process_options=None,
    *,
    raw_close: Callable[[int], None] = os.close,
    owned=None,
):
    """Close child-side parent copies and expose non-owning raw views."""
    if owned is None:
        owned = {}
    process_options = process_options or {}
    text_mode = bool(
        process_options.get("text")
        or process_options.get("universal_newlines")
        or process_options.get("encoding") is not None
        or process_options.get("errors") is not None
    )
    for label, resource in resources.items():
        close_raw_owned_pipe(resource["child"], raw_close)
        buffering = process_options.get("bufsize", -1)
        if text_mode and buffering == 1:
            buffering = -1
        file_object = io.open(
            resource["parent"].descriptor,
            resource["mode"],
            buffering=buffering,
            closefd=False,
        )
        if text_mode:
            file_object = io.TextIOWrapper(
                file_object,
                encoding=(
                    process_options.get("encoding")
                    or getattr(process, "encoding", None)
                ),
                errors=(
                    process_options.get("errors")
                    or getattr(process, "errors", None)
                ),
                write_through=label == "stdin",
                line_buffering=(
                    label == "stdin"
                    and process_options.get("bufsize") == 1
                ),
            )
        ownership = resource["parent"]
        ownership.label = label
        view = OwnedPipeView(file_object, ownership)
        ownership.object_ref = view
        ownership.backing_ref = file_object
        # Publish raw ownership before exposing the view on the process.  A
        # cancellation or adversarial __setattr__ after this point therefore
        # still leaves the session with the one token that may close the fd.
        owned[label] = ownership
        setattr(process, label, view)
    return owned


def close_explicit_pipe_resources(
    resources,
    *,
    raw_close: Callable[[int], None] = os.close,
):
    failures: list[BaseException] = []
    for resource in (resources or {}).values():
        for name in ("child", "parent"):
            ownership = resource.get(name)
            if ownership is not None:
                try:
                    close_raw_owned_pipe(ownership, raw_close)
                except BaseException as error:
                    failures.append(error)
    raise_deferred_cleanup(failures, "Git pipe construction cleanup failed")


def spawn_git_process(
    session: "RepositorySession",
    command,
    *args,
    **kwargs,
) -> subprocess.Popen:
    """Create one production-owned Git child with result-blind observation."""
    metrics = session.metrics
    if not is_git_command(command):
        raise ValueError("spawn_git_process accepts only Git commands")
    if kwargs.get("shell"):
        raise Unreadable("trusted Git runner refuses shell execution")
    requested_cwd = Path(kwargs.get("cwd", session.root)).resolve()
    if requested_cwd != session.root:
        raise Unreadable("trusted Git runner refuses a foreign working tree")
    kwargs["cwd"] = session.root
    if session._spawn_active:
        raise Unreadable("recursive Git process creation refused")
    exact_command = tuple(str(argument) for argument in command)
    observer = session.observer
    session._spawn_active = True
    explicit_resources = None
    process = None
    try:
        metrics.charge("git_process_attempts")
        if observer is not None:
            before = getattr(observer, "before_spawn", None)
            after = getattr(observer, "after_spawn", None)
            if not callable(before) or not callable(after):
                raise Unreadable(
                    "Git spawn observer must provide before_spawn and after_spawn"
                )
            try:
                before(exact_command)
            except BaseException as error:
                if is_cancellation(error):
                    raise
                raise Unreadable(
                    "Git spawn observer failed before process creation"
                ) from error
        explicit_parent_pipes = tuple(
            label
            for label in ("stdin", "stdout", "stderr")
            if kwargs.get(label) is subprocess.PIPE
        )
        if explicit_parent_pipes:
            try:
                explicit_resources = prepare_explicit_parent_pipes(
                    explicit_parent_pipes
                )
                # Keep construction-time ownership in the session before the
                # runner can create a child.  These are the same tokens later
                # published on the process, so repeated cleanup is idempotent.
                session.explicit_pipe_resources.append(explicit_resources)
                for label, resource in explicit_resources.items():
                    kwargs[label] = resource["child"].descriptor
            except BaseException as error:
                if is_cancellation(error):
                    raise
                raise Unreadable(
                    "Git child pipe setup failed: " + type(error).__name__
                ) from error
        process_index = len(session.processes)
        try:
            # The C-backed publication bridge appends the returned child to
            # the session registry before Python can execute the STORE_FAST
            # that would otherwise lose it under opcode-level cancellation.
            publish_call_result(
                session.processes,
                functools.partial(
                    session.git_runner, command, *args, **kwargs
                ),
            )
            _spawn_boundary("after-runner-publication")
            process = session.processes[process_index]
            _spawn_boundary("after-runner-return")
        except BaseException as error:
            failures: list[BaseException] = [error]
            owned_process = process
            if (
                owned_process is None
                and len(session.processes) > process_index
            ):
                owned_process = session.processes[process_index]
            try:
                if owned_process is None:
                    close_explicit_pipe_resources(explicit_resources)
                else:
                    cleanup_unclaimed_process(
                        owned_process,
                        getattr(
                            owned_process, "_agentfold_owned_pipes", {}
                        ),
                        explicit_resources,
                    )
            except BaseException as cleanup_error:
                failures.append(cleanup_error)
            cancellation = next(
                (item for item in failures if is_cancellation(item)), None
            )
            if cancellation is not None:
                cleanup_notes = [
                    cleanup_failure_text(item)
                    for item in failures
                    if item is not cancellation
                ]
                if cleanup_notes:
                    cancellation.add_note(
                        "Git process factory cleanup failed: "
                        + "; ".join(dict.fromkeys(cleanup_notes))
                    )
                raise cancellation
            raise Unreadable(
                "Git process factory failed: "
                + "; ".join(
                    dict.fromkeys(
                        type(item).__name__ for item in failures
                    )
                )
            ) from error
        metrics.observe("git_processes")
        if observer is not None:
            try:
                observer.after_spawn(
                    exact_command, getattr(process, "pid", None)
                )
            except BaseException as error:
                cleanup_error = None
                try:
                    cleanup_unclaimed_process(
                        process, {}, explicit_resources
                    )
                except BaseException as observed_cleanup_error:
                    cleanup_error = observed_cleanup_error
                if is_cancellation(error):
                    if cleanup_error is not None:
                        error.add_note(
                            "Git spawn observer cleanup failed after "
                            "cancellation: "
                            + cleanup_failure_text(cleanup_error)
                        )
                    raise error
                if cleanup_error is not None:
                    if is_cancellation(cleanup_error):
                        raise cleanup_error
                    raise Unreadable(
                        "Git spawn observer failed after process creation and "
                        f"cleanup failed: {cleanup_failure_text(cleanup_error)}"
                    ) from error
                raise Unreadable(
                    "Git spawn observer failed after process creation"
                ) from error
        owned_pipes = {}
        try:
            # Publish the map before attachment begins.  Each token is added
            # before its public view, and the session also retains the source
            # resource map, closing both cancellation gaps without a second
            # numeric owner.
            process._agentfold_owned_pipes = owned_pipes
            attach_explicit_parent_pipes(
                process,
                explicit_resources or {},
                kwargs,
                owned=owned_pipes,
            )
            _spawn_boundary("after-pipe-attachment")
        except BaseException as error:
            failures = [error]
            try:
                cleanup_unclaimed_process(
                    process, owned_pipes, explicit_resources
                )
            except BaseException as cleanup_error:
                failures.append(cleanup_error)
            raise_deferred_cleanup(
                failures, "Git child pipe attachment failed"
            )
        return process
    finally:
        session._spawn_active = False


@contextlib.contextmanager
def temporary_environment(**updates):
    saved = {key: os.environ.get(key) for key in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class SessionSubprocess:
    """Per-session subprocess facade for the imported production helper."""

    def __init__(self, session: "RepositorySession"):
        self._session = session

    PIPE = subprocess.PIPE
    DEVNULL = subprocess.DEVNULL
    TimeoutExpired = subprocess.TimeoutExpired

    def __getattr__(self, name):
        raise AttributeError(
            f"session subprocess facade does not expose {name!r}"
        )

    def Popen(self, command, *args, **kwargs):
        return self._session.spawn_production_helper(
            command, *args, **kwargs
        )

    def run(self, command, **kwargs):
        return self._session.run_production_helper(command, **kwargs)


class RepositorySession:
    """All mutable state and child ownership for exactly one repository audit."""

    def __init__(
        self,
        root: Path,
        *,
        git_runner: TrustedGitRunner,
        stable_git_diagnostics: bool = True,
    ):
        if not callable(git_runner):
            raise TypeError("trusted Git runner must be callable")
        self.root = Path(root).resolve()
        self.git_runner = git_runner
        self.metrics = Metrics()
        self.stable_git_diagnostics = stable_git_diagnostics
        self.observer: GitSpawnObserver | None = None
        self.object_database: ObjectDatabase | None = None
        self.carry_proof_cache: dict[tuple[tuple, str], dict] = {}
        self.processes: list[subprocess.Popen] = []
        self.explicit_pipe_resources: list[dict] = []
        self._spawn_active = False
        self._active = False
        self._closed = False
        self._reconcile_name: str | None = None
        self._reconcile_registration = None
        self.reconcile = None
        self._reconcile_token = None
        self._prior_reconcile = None

    def open(self) -> "RepositorySession":
        if self._active:
            return self
        if self._closed:
            raise Unreadable("repository session cannot be reopened")
        try:
            # load_reconciler publishes the sys.modules registration to this
            # session before executing the imported module.  A cancellation
            # after its return therefore cannot orphan the UUID entry.
            reconcile = load_reconciler(self)
            _session_boundary("after-reconciler-load")
            reconcile.REPO = self.root
            reconcile.QUEUE = self.root / "message-queue"
            reconcile.RETRIES = reconcile.QUEUE / "needs-agent" / "retries"
            reconcile.TASKS = self.root / "tasks"
            reconcile.CONVERSATIONS = self.root / "history/conversations"
            reconcile.MEMORY = self.root / "memory"
            reconcile.CHANGE_RANGE = None
            reconcile.DISPLACED_TIP = None
            reconcile.ACTIVE_TRANSITIONS = set()
            reconcile.ACTIVE_TASK_ID = None
            reconcile.TODAY = FIXTURE_DATE
            reconcile.subprocess = SessionSubprocess(self)
            reconcile.scope_immutable_git_caches()
            self._prior_reconcile = ACTIVE_RECONCILE.get()
            # Mark the fallback owner before ContextVar.set.  If cancellation
            # lands after set but before its token is published, close() can
            # restore the captured prior value without the lost token.
            self._active = True
            token = ACTIVE_RECONCILE.set(reconcile)
            _session_boundary("after-context-set")
            self._reconcile_token = token
            return self
        except BaseException as primary:
            failures: list[BaseException] = [primary]
            try:
                self.close()
            except BaseException as cleanup_error:
                failures.append(cleanup_error)
            raise_deferred_cleanup(
                failures, "repository session setup failed"
            )

    def __enter__(self) -> "RepositorySession":
        return self.open()

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return False

    def _precharge_production_helper(self, command, kwargs):
        if not is_git_command(command):
            raise Unreadable(
                "imported production helper requested a non-Git child"
            )
        encoded = sum(
            len(str(argument).encode("utf-8", errors="surrogateescape"))
            for argument in command
        )
        self.metrics.charge("production_helper_calls")
        self.metrics.charge("production_helper_input_bytes", encoded)
        command_text = tuple(str(argument) for argument in command)
        if (
            "rev-list" in command_text
            and "--parents" in command_text
            and "-n" in command_text
            and "1" in command_text
        ):
            self.metrics.charge("production_parent_queries")
        if self.stable_git_diagnostics:
            kwargs["env"] = stable_git_environment(kwargs.get("env"))

    def spawn_production_helper(self, command, *args, **kwargs):
        self._precharge_production_helper(command, kwargs)
        return spawn_git_process(
            self,
            command,
            *args,
            **kwargs,
        )

    def run_production_helper(self, command, **kwargs):
        self._precharge_production_helper(command, kwargs)
        return self.run_git_process(command, **kwargs)

    def run_git_process(self, command, **kwargs):
        """A subprocess.run-compatible path built on the injected runner."""
        input_value = kwargs.pop("input", None)
        capture_output = kwargs.pop("capture_output", False)
        timeout = kwargs.pop("timeout", None)
        check = kwargs.pop("check", False)
        if input_value is not None:
            if kwargs.get("stdin") is not None:
                raise ValueError("stdin and input arguments may not both be used")
            kwargs["stdin"] = subprocess.PIPE
        if capture_output:
            if kwargs.get("stdout") is not None or kwargs.get("stderr") is not None:
                raise ValueError(
                    "stdout and stderr arguments may not be used with capture_output"
                )
            kwargs["stdout"] = subprocess.PIPE
            kwargs["stderr"] = subprocess.PIPE
        process = spawn_git_process(
            self,
            command,
            **kwargs,
        )
        primary_error = None
        cleanup_failures: list[BaseException] = []
        stdout = None
        stderr = None
        try:
            stdout, stderr = process.communicate(input_value, timeout=timeout)
        except BaseException as error:
            primary_error = error
            try:
                cleanup_unclaimed_process(
                    process,
                    getattr(process, "_agentfold_owned_pipes", {}),
                )
            except BaseException as cleanup_error:
                cleanup_failures.append(cleanup_error)
        else:
            try:
                retire_process_pipes(process)
            except BaseException as cleanup_error:
                cleanup_failures.append(cleanup_error)

        failures = (
            ([primary_error] if primary_error is not None else [])
            + cleanup_failures
        )
        cancellation = next(
            (error for error in failures if is_cancellation(error)), None
        )
        if cancellation is not None:
            secondary = [
                cleanup_failure_text(error)
                for error in failures
                if error is not cancellation
            ]
            if secondary:
                cancellation.add_note(
                    "Git child communication cleanup: "
                    + "; ".join(dict.fromkeys(secondary))
                )
            raise cancellation
        if primary_error is not None:
            if cleanup_failures:
                raise Unreadable(
                    "Git child communication cleanup failed after "
                    f"{type(primary_error).__name__}: "
                    + "; ".join(
                        dict.fromkeys(
                            cleanup_failure_text(error)
                            for error in cleanup_failures
                        )
                    )
                ) from primary_error
            raise primary_error
        raise_deferred_cleanup(
            cleanup_failures, "Git child communication cleanup failed"
        )
        returncode = process.poll()
        if check and returncode:
            raise subprocess.CalledProcessError(
                returncode, command, output=stdout, stderr=stderr
            )
        return subprocess.CompletedProcess(
            command, returncode, stdout, stderr
        )

    def create_object_database(
        self,
        *,
        damage: Damage | None = None,
        stable_git_diagnostics: bool = True,
    ) -> "ObjectDatabase":
        if self.object_database is not None:
            raise Unreadable("repository session already owns an object database")
        database = ObjectDatabase(
            self,
            damage=damage,
            stable_git_diagnostics=stable_git_diagnostics,
        )
        self.object_database = database
        return database

    def close_object_database(self) -> None:
        database = self.object_database
        self.object_database = None
        if database is not None:
            database.close()

    def close(self) -> None:
        if self._closed:
            return
        failures: list[BaseException] = []
        try:
            try:
                self.close_object_database()
            except BaseException as error:
                failures.append(error)
            if self.reconcile is not None:
                for cleanup in (
                    self.reconcile.close_git_cat_file,
                    self.reconcile.stop_git_snapshot_cache,
                ):
                    try:
                        cleanup()
                    except BaseException as error:
                        failures.append(error)
            for process in self.processes:
                try:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
                except BaseException as error:
                    failures.append(error)
                    try:
                        if process.poll() is None:
                            process.kill()
                        process.wait(timeout=5)
                    except BaseException as cleanup_error:
                        failures.append(cleanup_error)
                try:
                    retire_process_pipes(process)
                except BaseException as error:
                    failures.append(error)
            # Construction resource maps use the same one-shot tokens as the
            # process maps.  Keeping both references until final cleanup makes
            # cancellation before or during attachment safe and idempotent.
            for resources in self.explicit_pipe_resources:
                try:
                    close_explicit_pipe_resources(resources)
                except BaseException as error:
                    failures.append(error)
        finally:
            self._closed = True
            try:
                if self._active and self._reconcile_token is not None:
                    ACTIVE_RECONCILE.reset(self._reconcile_token)
                elif (
                    self._active
                    and self.reconcile is not None
                    and ACTIVE_RECONCILE.get() is self.reconcile
                ):
                    # ContextVar.set completed but its token was interrupted
                    # before publication.  Restore the exact captured value;
                    # no later session can share this execution context.
                    ACTIVE_RECONCILE.set(self._prior_reconcile)
            except BaseException as error:
                failures.append(error)
            self._active = False
            self._closed = True
            try:
                registration = self._reconcile_registration
                if registration is not None:
                    name, module = registration
                    if sys.modules.get(name) is module:
                        sys.modules.pop(name, None)
                elif (
                    self._reconcile_name is not None
                    and sys.modules.get(self._reconcile_name) is self.reconcile
                ):
                    sys.modules.pop(self._reconcile_name, None)
            except BaseException as error:
                failures.append(error)
            self.processes.clear()
            self.explicit_pipe_resources.clear()
            self.carry_proof_cache.clear()
            self._reconcile_registration = None
            self._reconcile_name = None
            self._reconcile_token = None
            self._prior_reconcile = None
            self.reconcile = None
        raise_deferred_cleanup(failures, "repository session cleanup failed")


@contextlib.contextmanager
def _fixture_repository_session(root: Path):
    """Give fixture-only direct reconciler probes the same isolated boundary."""
    session = RepositorySession(root, git_runner=_trusted_git_runner())
    with session:
        yield session


class GitRepository:
    """Deterministic disposable real-Git fixture builder."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.clock = 0
        self.rendered_retries: dict[str, str] = {}
        self.run("init", "-q", "-b", "main")
        self.run("config", "user.name", "Production Contract POC")
        self.run("config", "user.email", "production-contract@example.invalid")

    def run(self, *arguments, input_text=None, env=None, check=True):
        result = REAL_RUN(
            ["git", *arguments],
            cwd=self.root,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=stable_git_environment(env),
            check=False,
        )
        if check and result.returncode:
            raise RuntimeError(
                f"git {' '.join(arguments)} failed ({result.returncode}): "
                f"{result.stderr.strip()}"
            )
        return result

    def write(self, relative: str, text: str):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def read(self, relative: str) -> str:
        return (self.root / relative).read_text(encoding="utf-8")

    def remove(self, relative: str):
        target = self.root / relative
        if target.exists():
            target.unlink()

    def move(self, source: str, destination: str):
        target = self.root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        (self.root / source).rename(target)

    def branch(self, name: str, start: str):
        self.run("checkout", "-q", "-B", name, start)

    def _commit_environment(self):
        self.clock += 1
        stamp = str(1_800_000_000 + self.clock * 60) + " +0000"
        environment = dict(os.environ)
        environment.update(
            {
                "GIT_AUTHOR_NAME": "Production Contract POC",
                "GIT_AUTHOR_EMAIL": "production-contract@example.invalid",
                "GIT_COMMITTER_NAME": "Production Contract POC",
                "GIT_COMMITTER_EMAIL": "production-contract@example.invalid",
                "GIT_AUTHOR_DATE": stamp,
                "GIT_COMMITTER_DATE": stamp,
                "GIT_EDITOR": "true",
            }
        )
        return environment

    def commit(self, message: str) -> str:
        self.run("add", "-A")
        self.run("commit", "-q", "-m", message, env=self._commit_environment())
        return self.oid("HEAD")

    def oid(self, revision: str) -> str:
        return self.run(
            "--no-replace-objects", "rev-parse", "--verify", revision
        ).stdout.strip()

    def commit_tree(self, tree: str, message: str, *parents: str) -> str:
        arguments = ["commit-tree", tree]
        for parent in parents:
            arguments.extend(("-p", parent))
        return self.run(
            *arguments,
            input_text=message + "\n",
            env=self._commit_environment(),
        ).stdout.strip()

    def raw_commit_with_parent_headers(
        self, tree: str, message: str, *parents: str
    ) -> str:
        """Write one commit object without commit-tree parent deduplication."""
        environment = self._commit_environment()
        stamp = environment["GIT_AUTHOR_DATE"]
        identity = (
            "Production Contract POC "
            "<production-contract@example.invalid>"
        )
        payload = "\n".join(
            [
                f"tree {tree}",
                *(f"parent {parent}" for parent in parents),
                f"author {identity} {stamp}",
                f"committer {identity} {stamp}",
                "",
                message,
                "",
            ]
        )
        result = self.run(
            "hash-object",
            "-t",
            "commit",
            "-w",
            "--stdin",
            input_text=payload,
        ).stdout.strip()
        self.run("checkout", "-q", "--detach", result)
        return result

    def merge_commit(
        self,
        parents: Iterable[str],
        message: str,
        writes: dict[str, str] | None = None,
        removes: Iterable[str] = (),
    ) -> str:
        parents = tuple(parents)
        if len(parents) < 2:
            raise ValueError("a merge fixture needs at least two parents")
        self.run("checkout", "-q", "--detach", parents[0])
        for path, text in (writes or {}).items():
            self.write(path, text)
        for path in removes:
            self.remove(path)
        self.run("add", "-A")
        tree = self.run("write-tree").stdout.strip()
        result = self.commit_tree(tree, message, *parents)
        self.run("checkout", "-q", "--detach", result)
        return result

    def tree_entry_oid(self, revision: str, path: str) -> str:
        output = self.run(
            "--no-replace-objects", "ls-tree", revision, "--", path
        ).stdout.strip()
        if not output:
            raise RuntimeError(f"no tree entry for {path} at {revision}")
        return output.split()[2]

    def hide_loose_object(self, oid: str) -> tuple[Path, Path]:
        source = self.root / ".git/objects" / oid[:2] / oid[2:]
        if not source.is_file():
            raise RuntimeError(f"expected loose object {oid}")
        hidden = source.with_name(source.name + ".missing")
        source.rename(hidden)
        return hidden, source


def run_git(
    session: RepositorySession,
    *arguments,
    check=True,
    stable_git_diagnostics=True,
):
    result = session.run_git_process(
        ["git", *arguments],
        cwd=session.root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=(stable_git_environment() if stable_git_diagnostics else None),
        check=False,
    )
    if check and result.returncode:
        raise Unreadable(
            stable_git_failure(arguments, result.stderr)
            if stable_git_diagnostics
            else (
                result.stderr.strip()
                or f"git {' '.join(arguments)} failed ({result.returncode})"
            )
        )
    return result


def _terminate_and_reap(
    process: subprocess.Popen,
    session: RepositorySession,
    *,
    counter_prefix: str,
):
    """Terminate a refused Git child and prove that it was reaped."""
    metrics = session.metrics
    failures: list[BaseException] = []
    try:
        if process.poll() is None:
            process.terminate()
            metrics.observe(f"{counter_prefix}_process_terminations")
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        metrics.observe(f"{counter_prefix}_process_reaps")
        metrics.observe("graph_process_cleanup_checks")
        if process.poll() is None:
            failures.append(RuntimeError("bounded Git child was not reaped"))
    except BaseException as error:
        failures.append(error)
    try:
        retire_process_pipes(process)
    except BaseException as error:
        failures.append(error)
    raise_deferred_cleanup(failures, "bounded Git child cleanup failed")


def bounded_git_lines(
    session: RepositorySession,
    arguments: tuple[str, ...],
    *,
    counter_prefix: str,
    buffered_damage: bool = False,
    stable_git_diagnostics: bool = True,
    line_callback: Callable[[bytes], None] | None = None,
) -> tuple[int, tuple[bytes, ...], bytes]:
    """Read one Git command with bounded chunks and transactional output."""
    root = session.root
    metrics = session.metrics
    stream_chunk_bytes = 256
    output_counter = f"{counter_prefix}_output_bytes"
    line_counter = f"{counter_prefix}_line_bytes"
    line_peak_counter = f"{counter_prefix}_line_peak_bytes"
    lines_counter = f"{counter_prefix}_lines"
    if buffered_damage:
        result = run_git(
            session,
            *arguments,
            check=False,
            stable_git_diagnostics=stable_git_diagnostics,
        )
        raw = result.stdout.encode("utf-8", errors="surrogateescape")
        metrics.observe("graph_buffered_bytes", len(raw))
        metrics.charge(output_counter, len(raw))
        metrics.charge(line_counter, len(raw.replace(b"\n", b"")))
        lines = tuple(raw.splitlines())
        metrics.admit_peak(
            line_peak_counter, max((len(line) for line in lines), default=0)
        )
        metrics.charge(lines_counter, len(lines))
        metrics.observe(f"{counter_prefix}_process_reaps")
        if line_callback is not None:
            for line in lines:
                line_callback(line)
        return (
            result.returncode,
            lines,
            result.stderr.encode("utf-8", errors="surrogateescape"),
        )

    command = ["git", *arguments]
    process_arguments = {
        "cwd": root,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "env": stable_git_environment() if stable_git_diagnostics else None,
    }
    process = (
        spawn_git_process(session, command, **process_arguments)
    )
    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    line = bytearray()
    stderr = bytearray()

    def bounded_read_size(counter: str) -> int:
        if metrics._posthoc_budget_accounting:
            return stream_chunk_bytes
        limit = metrics.limit_for(counter)
        if limit is None:
            return stream_chunk_bytes
        return max(
            1,
            min(
                stream_chunk_bytes,
                limit - getattr(metrics, counter) + 1,
            ),
        )

    try:
        while selector.get_map():
            for key, _events in selector.select():
                stream = key.fileobj
                if key.data == "stdout":
                    peak_limit = metrics.limit_for(line_peak_counter)
                    peak_room = (
                        stream_chunk_bytes
                        if peak_limit is None
                        else max(1, peak_limit - len(line) + 1)
                    )
                    size = min(
                        bounded_read_size(output_counter),
                        bounded_read_size(line_counter),
                        (
                            stream_chunk_bytes
                            if metrics._posthoc_budget_accounting
                            else peak_room
                        ),
                    )
                else:
                    size = bounded_read_size("git_stderr_bytes")
                chunk = (
                    stream.readline(size)
                    if key.data == "stdout"
                    else os.read(stream.fileno(), size)
                )
                if not chunk:
                    selector.unregister(stream)
                    continue
                if key.data == "stderr":
                    metrics.charge("git_stderr_bytes", len(chunk))
                    stderr.extend(chunk)
                    continue
                if counter_prefix == "graph":
                    metrics.observe("graph_stream_chunks")
                    metrics.admit_peak(
                        "graph_stream_peak_chunk_bytes", len(chunk)
                    )
                metrics.charge(output_counter, len(chunk))
                metrics.charge(line_counter, len(chunk) - chunk.count(b"\n"))
                start = 0
                while True:
                    newline = chunk.find(b"\n", start)
                    if newline < 0:
                        metrics.admit_peak(
                            line_peak_counter,
                            len(line) + len(chunk[start:]),
                        )
                        line.extend(chunk[start:])
                        break
                    metrics.admit_peak(
                        line_peak_counter,
                        len(line) + newline - start,
                    )
                    line.extend(chunk[start:newline])
                    metrics.charge(lines_counter)
                    completed = bytes(line)
                    if line_callback is not None:
                        line_callback(completed)
                    line.clear()
                    start = newline + 1
        if line:
            metrics.charge(lines_counter)
            completed = bytes(line)
            if line_callback is not None:
                line_callback(completed)
        returncode = process.wait(timeout=5)
        metrics.observe(f"{counter_prefix}_process_reaps")
        metrics.observe("graph_process_cleanup_checks")
        return returncode, (), bytes(stderr)
    except (BudgetExceeded, Unreadable):
        _terminate_and_reap(
            process, session, counter_prefix=counter_prefix
        )
        raise
    finally:
        selector.close()
        retire_process_pipes(process)


class ObjectDatabase:
    """One cat-file process plus immutable object/tree/snapshot caches."""

    def __init__(
        self,
        session: RepositorySession,
        *,
        damage: Damage | None = None,
        stable_git_diagnostics: bool = True,
    ):
        self.session = session
        self.root = session.root
        self.metrics = session.metrics
        self.damage = damage or Damage()
        self.metrics.charge("batch_processes")
        self.process = spawn_git_process(
            session,
            ["git", "--no-replace-objects", "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=self.root,
            stderr=subprocess.DEVNULL,
            env=(
                stable_git_environment()
                if stable_git_diagnostics
                else None
            ),
        )
        self._owned_pipes = self.process._agentfold_owned_pipes
        self.objects: dict[str, tuple[str, bytes]] = {}
        self.trees: dict[str, dict[str, tuple[str, str]]] = {}
        self.flat_trees: dict[str, dict[str, tuple[str, str]]] = {}
        self.snapshots: dict[
            str | None, dict[tuple, tuple[ActionState, ...]]
        ] = {}
        self._reaped = False
        self._termination_requested = False
        self._kill_requested = False
        self.wait_timeout = 5.0

    def _close_pipes(self):
        """Close and verify both owned descriptors after any child outcome."""
        if self.damage.leak_object_database_pipes:
            return
        failures: list[BaseException] = []
        for label, pipe in (
            ("stdin", self.process.stdin),
            ("stdout", self.process.stdout),
        ):
            ownership = self._owned_pipes.get(label)
            if ownership is None:
                continue
            try:
                close_owned_pipe(
                    ownership, pipe, self._raw_close_owned_fd
                )
            except BaseException as error:
                failures.append(error)
        raise_deferred_cleanup(
            failures, "cat-file descriptor cleanup failed"
        )

    def _raw_close_owned_fd(self, descriptor: int):
        """Fallback closure seam retained for a real failure control."""
        os.close(descriptor)

    def _record_reap(self):
        if self.process.poll() is None:
            return False
        if not self._reaped:
            self.metrics.observe("object_process_reaps")
            self._reaped = True
        return True

    def _terminate_once(self):
        if self._termination_requested or self.process.poll() is not None:
            return
        self.process.terminate()
        self._termination_requested = True
        self.metrics.observe("object_process_terminations")

    def _kill_once(self):
        if self._kill_requested or self.process.poll() is not None:
            return
        self.process.kill()
        self._kill_requested = True

    def _shutdown(self, *, graceful: bool):
        failures: list[BaseException] = []

        def child_is_live() -> bool:
            try:
                return self.process.poll() is None
            except BaseException as error:
                failures.append(error)
                return True

        try:
            # Closing stdin delivers EOF to cat-file.  Pipe closure is
            # independent of liveness: poll() may already report an exited
            # child while Python still owns both descriptor objects.
            if graceful and not self.damage.leak_object_database_pipes:
                try:
                    close_owned_pipe(
                        self._owned_pipes["stdin"],
                        self.process.stdin,
                        self._raw_close_owned_fd,
                    )
                except BaseException as error:
                    failures.append(error)
            if not graceful:
                try:
                    self._terminate_once()
                except BaseException as error:
                    failures.append(error)
            if child_is_live():
                try:
                    self.process.wait(timeout=self.wait_timeout)
                except subprocess.TimeoutExpired:
                    pass
                except BaseException as error:
                    failures.append(error)
            # Each remaining cleanup transition is independent.  A throwable
            # in terminate or wait cannot suppress kill, the final wait, or
            # descriptor closure below.
            if child_is_live() and not self._termination_requested:
                try:
                    self._terminate_once()
                except BaseException as error:
                    failures.append(error)
            if child_is_live():
                try:
                    self.process.wait(timeout=self.wait_timeout)
                except subprocess.TimeoutExpired:
                    pass
                except BaseException as error:
                    failures.append(error)
            if child_is_live():
                try:
                    self._kill_once()
                except BaseException as error:
                    failures.append(error)
            if child_is_live():
                try:
                    self.process.wait(timeout=self.wait_timeout)
                except subprocess.TimeoutExpired:
                    pass
                except BaseException as error:
                    failures.append(error)
            try:
                reaped = self._record_reap()
            except BaseException as error:
                failures.append(error)
                reaped = False
            if not reaped:
                failures.append(
                    Unreadable("cat-file child was not reaped after kill")
                )
        finally:
            # Descriptor ownership ends even when wait still times out after
            # kill.  The leak mutant alone deliberately skips this guarantee.
            try:
                self._close_pipes()
            except BaseException as error:
                failures.append(error)
        raise_deferred_cleanup(failures, "cat-file cleanup failed")

    def close(self):
        self._shutdown(graceful=True)

    def abort(self):
        self._shutdown(graceful=False)

    def read(self, oid: str) -> tuple[str, bytes]:
        if oid in self.objects:
            self.metrics.charge("object_cache_hits")
            return self.objects[oid]
        self.metrics.charge("object_reads")
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        try:
            self.process.stdin.write(oid.encode("ascii") + b"\n")
            self.process.stdin.flush()
            header_limit = self.metrics.limit_for("object_header_bytes")
            header_room = (
                4096
                if header_limit is None
                else max(
                    1,
                    header_limit - self.metrics.object_header_bytes + 1,
                )
            )
            raw_header = self.process.stdout.readline(header_room)
            self.metrics.charge("object_header_bytes", len(raw_header))
            if not raw_header.endswith(b"\n"):
                raise Unreadable(f"malformed cat-file frame for {oid}")
            header = raw_header.rstrip(b"\n").split()
        except BudgetExceeded:
            self.abort()
            raise
        if len(header) == 2 and header[1] == b"missing":
            raise Unreadable(f"required Git object {oid} is missing")
        if len(header) != 3:
            raise Unreadable(f"malformed cat-file frame for {oid}")
        try:
            size = int(header[2])
        except ValueError as error:
            raise Unreadable(f"malformed cat-file size for {oid}") from error
        try:
            if not self.damage.unmetered_object_bytes:
                self.metrics.admit_peak("object_payload_peak_bytes", size)
                self.metrics.charge("object_payload_bytes", size)
            payload = self.process.stdout.read(size)
        except BudgetExceeded:
            self.abort()
            raise
        if len(payload) != size or self.process.stdout.read(1) != b"\n":
            raise Unreadable(f"truncated cat-file frame for {oid}")
        result = (header[1].decode("ascii"), payload)
        self.objects[oid] = result
        return result

    def commit_tree(self, oid: str) -> str:
        kind, payload = self.read(oid)
        if kind != "commit":
            raise Unreadable(f"required tip {oid} is a {kind}, not a commit")
        first = payload.split(b"\n", 1)[0]
        if not first.startswith(b"tree "):
            raise Unreadable(f"commit {oid} has no readable tree header")
        return first[5:].decode("ascii")

    def commit_parents(self, oid: str) -> tuple[str, ...]:
        kind, payload = self.read(oid)
        if kind != "commit":
            raise Unreadable(f"required object {oid} is not a commit")
        parents = []
        for line in payload.split(b"\n"):
            if line.startswith(b"parent "):
                parents.append(line[7:].decode("ascii"))
            elif line == b"":
                break
        return tuple(parents)

    def tree_entries(self, oid: str) -> dict[str, tuple[str, str]]:
        if oid in self.trees:
            self.metrics.charge("object_cache_hits")
            return self.trees[oid]
        kind, payload = self.read(oid)
        if kind != "tree":
            raise Unreadable(f"required tree {oid} is a {kind}")
        width = len(oid) // 2
        entries = {}
        offset = 0
        while offset < len(payload):
            space = payload.find(b" ", offset)
            nul = payload.find(b"\0", space + 1)
            if space <= offset or nul < 0 or nul + 1 + width > len(payload):
                raise Unreadable(f"malformed tree {oid}")
            raw_name = payload[space + 1:nul]
            if not self.damage.unmetered_tree_paths:
                self.metrics.charge("tree_entries")
                self.metrics.charge("tree_entry_name_bytes", len(raw_name))
            mode = payload[offset:space].decode("ascii")
            name = raw_name.decode(
                "utf-8", errors="surrogateescape"
            )
            child = payload[nul + 1:nul + 1 + width].hex()
            entries[name] = (mode, child)
            offset = nul + 1 + width
        self.trees[oid] = entries
        return entries

    def flat_tree(self, commit: str) -> dict[str, tuple[str, str]]:
        """Return every leaf path with its exact mode and object OID."""
        root = self.commit_tree(commit)
        if root in self.flat_trees:
            self.metrics.charge("object_cache_hits")
            return self.flat_trees[root]
        flattened: dict[str, tuple[str, str]] = {}
        leaf_count = 0

        def walk(tree_oid: str, prefix: str, prefix_bytes: int):
            nonlocal leaf_count
            for name, (mode, child) in self.tree_entries(tree_oid).items():
                path_bytes = len(
                    name.encode("utf-8", errors="surrogateescape")
                ) + (prefix_bytes + 1 if prefix else 0)
                if not self.damage.unmetered_tree_paths:
                    self.metrics.charge("flattened_paths")
                    self.metrics.charge("flattened_path_bytes", path_bytes)
                path = f"{prefix}/{name}" if prefix else name
                if mode in {"40000", "040000"}:
                    walk(child, path, path_bytes)
                else:
                    leaf_count += 1
                    if not self.damage.unmetered_tree_paths:
                        self.metrics.admit_peak(
                            "flat_tree_peak_paths", leaf_count
                        )
                    flattened[path] = (mode, child)

        walk(root, "", 0)
        self.flat_trees[root] = flattened
        return flattened

    def path_entry(self, commit: str, path: str) -> dict:
        """Return one typed exact tree entry or an explicit absence."""
        entry = self.flat_tree(commit).get(path)
        if entry is None:
            return {"state": "absent"}
        mode, oid = entry
        if mode == "160000":
            kind = "commit"
        elif mode == "120000" or mode.startswith("100"):
            kind = "blob"
        else:
            kind = "unknown"
        return {
            "state": "present",
            "mode": mode,
            "type": kind,
            "oid": oid,
        }

    def queue_tree(self, commit: str) -> str | None:
        root = self.commit_tree(commit)
        entry = self.tree_entries(root).get("message-queue")
        if entry is None:
            return None
        mode, oid = entry
        if mode not in {"40000", "040000"}:
            raise Unreadable(f"message-queue at {commit} is not a tree")
        return oid

    def snapshot(self, commit: str):
        self.metrics.charge("queue_snapshots_requested")
        queue_tree = self.queue_tree(commit)
        if queue_tree in self.snapshots:
            self.metrics.charge("snapshot_cache_hits")
            return self.snapshots[queue_tree]
        self.metrics.charge("queue_subtree_reads")
        by_identity: dict[tuple, list[ActionState]] = {}

        def walk(tree_oid: str, prefix: str, prefix_bytes: int):
            for name, (mode, child) in self.tree_entries(tree_oid).items():
                path_bytes = (
                    prefix_bytes
                    + 1
                    + len(name.encode("utf-8", errors="surrogateescape"))
                )
                self.metrics.charge("queue_paths")
                self.metrics.charge("queue_path_bytes", path_bytes)
                path = f"{prefix}/{name}"
                if mode in {"40000", "040000"}:
                    walk(child, path, path_bytes)
                    continue
                parts = Path(path).parts
                if (
                    len(parts) != 4
                    or parts[0] != "message-queue"
                    or parts[1] not in {"needs-agent", "needs-human"}
                    or not name.endswith(".md")
                ):
                    continue
                kind, payload = self.read(child)
                if kind != "blob":
                    raise Unreadable(f"queue item {path} is a {kind}")
                try:
                    self.metrics.charge("queue_blob_bytes", len(payload))
                    text = payload.decode("utf-8")
                except UnicodeDecodeError as error:
                    raise Unreadable(
                        f"queue item {path} is not UTF-8"
                    ) from error
                self.metrics.charge("identity_calls")
                identity = RECONCILE.queue_action_identity(path, text)
                by_identity.setdefault(identity, []).append(
                    ActionState(path, text, child)
                )

        if queue_tree is not None:
            walk(queue_tree, "message-queue", len(b"message-queue"))
        frozen = {
            identity: tuple(sorted(states, key=lambda state: state.path))
            for identity, states in by_identity.items()
        }
        self.snapshots[queue_tree] = frozen
        return frozen


class Graph:
    """One bounded post-C DAG enumeration shared by every action."""

    def __init__(
        self,
        session: RepositorySession,
        O: str,
        N: str,
        objects: ObjectDatabase,
        *,
        reopen_outside_c_boundary_ancestry: bool = False,
        buffered_graph_output: bool = False,
        stable_git_diagnostics: bool = True,
    ):
        root = session.root
        metrics = session.metrics
        self.root = root
        self.O = O
        self.N = N
        self.objects = objects
        self.metrics = metrics
        shallow_values: list[str] = []

        def receive_shallow(line: bytes):
            if not line:
                return
            metrics.charge("shallow_tokens")
            try:
                value = line.decode("ascii")
            except UnicodeDecodeError as error:
                raise Unreadable("shallow probe emitted non-ASCII data") from error
            if value not in {"true", "false"}:
                raise Unreadable("shallow probe emitted malformed data")
            shallow_values.append(value)

        shallow_returncode, _shallow_lines, shallow_stderr = bounded_git_lines(
            session,
            ("rev-parse", "--is-shallow-repository"),
            counter_prefix="shallow",
            stable_git_diagnostics=stable_git_diagnostics,
            line_callback=receive_shallow,
        )
        if shallow_returncode or len(shallow_values) != 1:
            diagnostic = shallow_stderr.decode(
                "utf-8", errors="surrogateescape"
            )
            raise Unreadable(
                stable_git_failure(
                    ("rev-parse", "--is-shallow-repository"), diagnostic
                )
                if stable_git_diagnostics
                else diagnostic.strip() or "could not inspect shallow state"
            )
        shallow = shallow_values[0]
        if shallow == "true":
            raise Unreadable("required post-C history is shallow")
        for label, oid in (("O", O), ("N", N)):
            try:
                objects.commit_tree(oid)
            except Unreadable as error:
                raise Unreadable(f"{label}: {error}") from error
        base_arguments = (
            "--no-replace-objects",
            "merge-base",
            "--all",
            O,
            N,
        )
        merge_bases: list[str] = []

        def receive_base(line: bytes):
            if not line:
                return
            metrics.charge("merge_base_tokens")
            try:
                oid = line.decode("ascii")
            except UnicodeDecodeError as error:
                raise Unreadable(
                    "merge-base emitted a non-ASCII object ID"
                ) from error
            if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid):
                raise Unreadable("merge-base emitted a malformed object ID")
            merge_bases.append(oid)

        base_returncode, _base_lines, base_stderr = bounded_git_lines(
            session,
            base_arguments,
            counter_prefix="merge_base",
            stable_git_diagnostics=stable_git_diagnostics,
            line_callback=receive_base,
        )
        if base_returncode:
            decoded_stderr = base_stderr.decode(
                "utf-8", errors="surrogateescape"
            )
            raise Unreadable(
                stable_git_failure(
                    ("merge-base", "--all", O, N), decoded_stderr
                )
                if stable_git_diagnostics
                else (
                    decoded_stderr.strip()
                    or "could not determine the merge base"
                )
            )
        merge_bases = tuple(merge_bases)
        if len(merge_bases) != 1:
            raise Unreadable(
                f"expected exactly one merge base C; found {len(merge_bases)}"
            )
        self.C = merge_bases[0]
        try:
            objects.commit_tree(self.C)
        except Unreadable as error:
            raise Unreadable(f"derived C: {error}") from error
        listing_arguments = [
            "--no-replace-objects",
            "rev-list",
            "--parents",
            "--topo-order",
            "--reverse",
        ]
        if not reopen_outside_c_boundary_ancestry:
            listing_arguments.append("--ancestry-path")
        metrics.charge("graph_enumerations")
        local_order = [self.C]
        local_parents: dict[str, tuple[str, ...]] = {self.C: ()}
        seen = {self.C}
        metrics.charge("graph_commits")

        def receive_graph_line(raw_line: bytes):
            if not raw_line:
                return
            token_count = raw_line.count(b" ") + 1
            metrics.charge("graph_commit_tokens")
            metrics.charge("graph_parent_tokens", token_count - 1)
            metrics.charge("graph_parent_edges", token_count - 1)
            try:
                fields = raw_line.decode("ascii").split()
            except UnicodeDecodeError as error:
                raise Unreadable("rev-list emitted non-ASCII graph data") from error
            if len(fields) != token_count or any(
                not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", field)
                for field in fields
            ):
                raise Unreadable("rev-list emitted a malformed graph line")
            commit, raw_parents = fields[0], tuple(fields[1:])
            if commit in seen:
                return
            metrics.charge("graph_commits")
            seen.add(commit)
            local_order.append(commit)
            local_parents[commit] = raw_parents

        try:
            listing_returncode, _listing_lines, listing_stderr = (
                bounded_git_lines(
                    session,
                    tuple([*listing_arguments, O, N, f"^{self.C}"]),
                    counter_prefix="graph",
                    buffered_damage=buffered_graph_output,
                    stable_git_diagnostics=stable_git_diagnostics,
                    line_callback=receive_graph_line,
                )
            )
        except BudgetExceeded as error:
            error.C = self.C
            raise
        if listing_returncode:
            decoded_stderr = listing_stderr.decode(
                "utf-8", errors="surrogateescape"
            )
            raise Unreadable(
                stable_git_failure(tuple(listing_arguments), decoded_stderr)
                if stable_git_diagnostics
                else decoded_stderr.strip() or "could not enumerate post-C graph"
            )
        self.order = local_order
        self.parents = local_parents
        self.children: dict[str, list[str]] = {
            commit: [] for commit in self.order
        }
        for child, parents in self.parents.items():
            for parent in parents:
                if parent in self.parents:
                    self.children.setdefault(parent, []).append(child)
        self.old_nodes = self.ancestors(O)
        self.new_nodes = self.ancestors(N)
        if self.C not in self.old_nodes or self.C not in self.new_nodes:
            raise Unreadable("both tips must descend from C")
        self.c_descendants = self.descendants(self.C)
        self.intrinsic_candidate_nodes = self.new_nodes.intersection(
            self.c_descendants
        )
        self.boundary_parents = {
            parent
            for child in self.intrinsic_candidate_nodes
            for parent in self.parents.get(child, ())
            if parent not in self.c_descendants
        }
        self.identity_nodes = (
            self.intrinsic_candidate_nodes | self.boundary_parents
        )
        self.candidate_nodes = set(self.intrinsic_candidate_nodes)
        if reopen_outside_c_boundary_ancestry:
            self.candidate_nodes.update(self.boundary_parents)

    def ancestors(self, tip: str) -> set[str]:
        seen = set()
        stack = [tip]
        while stack:
            commit = stack.pop()
            if commit in seen or commit not in self.parents:
                continue
            seen.add(commit)
            if commit != self.C:
                stack.extend(self.parents[commit])
        return seen

    def reaches_C(self, tip: str) -> bool:
        return self.C in self.ancestors(tip)

    def descendants(self, start: str) -> set[str]:
        seen = set()
        stack = [start]
        while stack:
            commit = stack.pop()
            if commit in seen:
                continue
            seen.add(commit)
            stack.extend(self.children.get(commit, ()))
        return seen

    def between(self, start: str, end: str) -> set[str]:
        return self.descendants(start).intersection(self.ancestors(end))

    def ordered(self, commits: Iterable[str]) -> list[str]:
        """Return a commit set in the one enumerated topological order."""
        selected = set(commits)
        return [commit for commit in self.order if commit in selected]

    def ordered_identity_nodes(self) -> list[str]:
        """Enumerate intrinsic nodes, then immediate boundaries, never ancestors."""
        intrinsic = self.ordered(self.intrinsic_candidate_nodes)
        return intrinsic + sorted(self.boundary_parents)


class _Classifier:
    """In-memory provenance over one enumerated graph and cached snapshots."""

    def __init__(
        self,
        fixture: _Fixture,
        damage: Damage | None = None,
        *,
        session: RepositorySession,
    ):
        self.fixture = fixture
        self.damage = damage or Damage()
        self.session = session
        self.metrics = session.metrics
        self.metrics.configure_budget(
            None if self.damage.unmetered_cone_work else fixture.budget_limit,
            limits=(
                {}
                if self.damage.unmetered_cone_work
                else fixture.budget_limits
            ),
            posthoc_budget_accounting=(
                self.damage.posthoc_budget_accounting
            ),
        )
        self.objects: ObjectDatabase | None = None
        self.graph: Graph | None = None
        self.carry_proof_cache = session.carry_proof_cache
        if fixture.origin_strategy not in {"U", "B"}:
            raise ValueError(
                f"unsupported origin strategy {fixture.origin_strategy!r}"
            )
        self.origin_strategy = fixture.origin_strategy

    def budget_overflows(self) -> list[tuple[str, int]]:
        if self.damage.unmetered_cone_work:
            return []
        return sorted(
            (name, value)
            for name, value in self.metrics.as_dict().items()
            if (
                self.metrics.limit_for(name) is not None
                and value > self.metrics.limit_for(name)
            )
        )

    def budget_result(self, base: dict) -> dict | None:
        overflows = self.budget_overflows()
        if not overflows:
            return None
        reason = "; ".join(
            f"{name}={value}>{self.metrics.limit_for(name)}"
            for name, value in overflows
        )
        return {
            **base,
            "audit_exit": 2,
            "classification": "blocking-finding",
            "evidence_verdict": {
                "status": "ambiguous",
                "reason": f"measured work budget exceeded: {reason}",
            },
            "event_mode": "none",
            "authority_edges": [],
            "propagation_edges": [],
            "mutation_edges": [],
            "support_checks": [],
            "carry_proofs": [],
            "actions": [],
            "metrics": self.metrics.as_dict(),
            "details": self.fixture.details,
        }

    def states(
        self, revision: str, identity: tuple
    ) -> tuple[ActionState, ...]:
        assert self.objects is not None
        states = self.objects.snapshot(revision).get(identity, ())
        return states[:1] if self.damage.collapse_multiplicity else states

    def identity_view(self, identity: tuple) -> dict:
        values = list(identity)
        payload = json.dumps(
            values[3:], sort_keys=True, ensure_ascii=False
        ).encode("utf-8")
        return {
            "kind": values[0] if values else "unknown",
            "actor": values[1] if len(values) > 1 else "",
            "leaf": values[2] if len(values) > 2 else "",
            "production_tuple": values,
            "production_tuple_sha256": hashlib.sha256(payload).hexdigest(),
        }

    def charge_production_helper_input(self, *values: str):
        """Bound imported helper inputs before calling production code."""
        self.metrics.charge("production_helper_calls")
        self.metrics.charge(
            "production_helper_input_bytes",
            sum(
                len(value.encode("utf-8", errors="surrogateescape"))
                for value in values
            ),
        )

    def carry_proof(self, identity: tuple, tip: str) -> dict:
        """Prove one live occurrence by C-rooted edges, not all ancestors."""
        assert self.graph is not None
        key = (identity, tip)
        if key in self.carry_proof_cache:
            return self.carry_proof_cache[key]

        if self.damage.universal_ancestor_carry_scan:
            region = self.graph.ancestors(tip)
            problem = None
            for commit in self.graph.ordered(region):
                multiplicity = len(self.states(commit, identity))
                if multiplicity != 1:
                    paths = [state.path for state in self.states(commit, identity)]
                    problem = (
                        "DAMAGED universal ancestor scan rejected "
                        f"{commit}: multiplicity {multiplicity}, paths {paths}"
                    )
                    break
            result = {
                "tip": tip,
                "status": "valid" if problem is None else "ambiguous",
                "reason": problem,
                "edges": [],
                "outside_neutral": [],
                "outside_collisions": [],
                "absent_c_parents": [],
            }
            self.carry_proof_cache[key] = result
            return result

        visiting: set[str] = set()
        memo: dict[str, str | None] = {}
        edges: list[dict] = []
        outside_neutral: list[str] = []
        outside_collisions: list[dict] = []
        absent_c_parents: list[str] = []

        def fail(message: str) -> str:
            return message

        def trace(child: str) -> str | None:
            if child in memo:
                return memo[child]
            if child in visiting:
                return fail(f"C-rooted carry graph cycles at {child}")
            if child not in self.graph.c_descendants:
                return fail(f"carrying node {child} is outside the C-rooted cone")
            self.metrics.charge("carry_proof_nodes")
            visiting.add(child)
            child_states = self.states(child, identity)
            if len(child_states) != 1:
                problem = fail(
                    f"C-rooted carrying node {child} has multiplicity "
                    f"{len(child_states)}"
                )
                visiting.remove(child)
                memo[child] = problem
                return problem
            if child == self.graph.C:
                visiting.remove(child)
                memo[child] = None
                return None

            after = child_states[0]
            carrying: list[tuple[str, ActionState]] = []
            local_absent: list[str] = []
            local_collisions: list[dict] = []
            local_neutral: list[str] = []
            if self.damage.first_parent_carry_only:
                parents = list(self.graph.parents.get(child, ()))[:1]
            else:
                parents = sorted(self.graph.parents.get(child, ()))
            for parent in parents:
                self.metrics.charge("carry_proof_edges")
                states = self.states(parent, identity)
                if parent in self.graph.c_descendants:
                    if len(states) == 1:
                        carrying.append((parent, states[0]))
                    elif len(states) == 0:
                        local_absent.append(parent)
                    else:
                        local_collisions.append(
                            {
                                "parent": parent,
                                "multiplicity": len(states),
                                "paths": [state.path for state in states],
                                "scope": "C-descendant",
                            }
                        )
                elif len(states) == 0:
                    local_neutral.append(parent)
                elif not self.damage.ignore_outside_c_collision:
                    local_collisions.append(
                        {
                            "parent": parent,
                            "multiplicity": len(states),
                            "paths": [state.path for state in states],
                            "scope": "outside-C",
                        }
                    )
            outside_neutral.extend(local_neutral)
            outside_collisions.extend(
                item for item in local_collisions if item["scope"] == "outside-C"
            )
            absent_c_parents.extend(local_absent)
            if local_collisions:
                problem = fail(
                    f"carrying node {child} has identity collision(s): "
                    + "; ".join(
                        f"{item['scope']} parent {item['parent']} "
                        f"multiplicity {item['multiplicity']}, "
                        f"paths {item['paths']}"
                        for item in local_collisions
                    )
                )
            elif local_absent and not self.damage.ignore_absent_c_arm:
                problem = fail(
                    f"carrying node {child} has absent C-descendant arm(s) "
                    f"{sorted(local_absent)}; deletion/reintroduction competes"
                )
            elif not carrying:
                problem = fail(
                    f"carrying node {child} has no C-rooted carrying parent"
                )
            else:
                upstream = [trace(parent) for parent, _ in carrying]
                problem = next((item for item in upstream if item), None)
                candidate_edges = [
                    self.mutation_edge(identity, parent, child, before, after)
                    for parent, before in carrying
                ]
                edges.extend(candidate_edges)
                if problem is None and not self.damage.skip_carry_compatibility:
                    sources = [
                        index for index, edge in enumerate(candidate_edges)
                        if edge["problem"] is None
                    ]
                    if not sources:
                        problem = (
                            f"no carrying edge into {child} passes production "
                            "mutation and frozen-byte authority: "
                            + "; ".join(
                                f"{edge['parent']}->{edge['child']}: "
                                + " | ".join(
                                    dict.fromkeys(
                                        item
                                        for item in (
                                            edge["production_problem"],
                                            edge["frozen_problem"],
                                            edge["binding_problem"],
                                        )
                                        if item is not None
                                    )
                                )
                                for edge in candidate_edges
                            )
                        )
                    else:
                        source_index = sources[0]
                        for index, ((_, before), edge) in enumerate(
                            zip(carrying, candidate_edges, strict=True)
                        ):
                            if index == source_index:
                                edge["role"] = "source"
                            else:
                                edge["role"] = "compatible-carrier"
                                edge["problem"] = self.merge_compatible_problem(
                                    identity, edge, before, after
                                )
                                if edge["problem"] and problem is None:
                                    problem = (
                                        f"carrying merge edge into {child} is incompatible: "
                                        f"{edge['problem']}"
                                    )
            visiting.remove(child)
            memo[child] = problem
            return problem

        problem = trace(tip)
        result = {
            "tip": tip,
            "status": "valid" if problem is None else "ambiguous",
            "reason": problem,
            "edges": self.stable_edges(edges),
            "outside_neutral": sorted(set(outside_neutral)),
            "outside_collisions": sorted(
                {json.dumps(item, sort_keys=True): item for item in outside_collisions}.values(),
                key=lambda item: (item["parent"], item["multiplicity"]),
            ),
            "absent_c_parents": sorted(set(absent_c_parents)),
        }
        self.carry_proof_cache[key] = result
        return result

    def unique_carry_problem(self, identity: tuple, tip: str) -> str | None:
        """Compatibility shim for callers while authority uses carry_proof."""
        return self.carry_proof(identity, tip)["reason"]

    def absence_problem(
        self, identity: tuple, start: str, end: str
    ) -> str | None:
        assert self.graph is not None
        region = self.graph.between(start, end)
        if not region:
            return f"{start} is not on an ancestry path to {end}"
        for commit in self.graph.ordered(region):
            multiplicity = len(self.states(commit, identity))
            if multiplicity:
                return (
                    f"identity reappears at {commit} with multiplicity "
                    f"{multiplicity}"
                )
            if commit == start:
                continue
            for parent in self.graph.parents[commit]:
                if parent not in self.graph.parents:
                    continue
                multiplicity = len(self.states(parent, identity))
                if multiplicity:
                    return (
                        f"contributing parent {parent} carries the identity "
                        f"into {commit}"
                    )
        return None

    @staticmethod
    def canonical_json_size(value) -> int:
        """Compute canonical JSON bytes without constructing the full JSON."""
        if value is None:
            return 4
        if value is True:
            return 4
        if value is False:
            return 5
        if isinstance(value, (int, float)):
            return len(str(value).encode("ascii"))
        if isinstance(value, str):
            return len(
                json.dumps(value, ensure_ascii=False).encode("utf-8")
            )
        if isinstance(value, (list, tuple)):
            return 2 + max(0, len(value) - 1) + sum(
                _Classifier.canonical_json_size(item) for item in value
            )
        if isinstance(value, dict):
            return 2 + max(0, len(value) - 1) + sum(
                _Classifier.canonical_json_size(str(key))
                + 1
                + _Classifier.canonical_json_size(value[key])
                for key in sorted(value)
            )
        raise TypeError(f"unsupported canonical JSON value {type(value)!r}")

    def canonical_digest(self, domain: str, value: dict) -> str:
        wrapped = {"domain": domain, "value": value}
        if not self.damage.unmetered_support_construction:
            self.metrics.charge(
                "support_serialized_bytes",
                self.canonical_json_size(wrapped),
            )
        payload = json.dumps(
            wrapped,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(payload).hexdigest()

    def support_leaf_obligations(
        self,
        state: ActionState,
        parent: str,
        child: str,
    ) -> tuple[list[dict], str | None]:
        """Describe only production leaves this POC can certify completely."""
        fields = RECONCILE.text_fields(state.text)
        parts = Path(state.path).parts
        actor = parts[1] if len(parts) > 1 else ""
        leaf = parts[2] if len(parts) > 2 else ""
        self.charge_production_helper_input(state.text)
        declared_candidates = RECONCILE.context_path_candidates(state.text)
        declared_set: dict[str, None] = {}
        for path in declared_candidates:
            if path in declared_set:
                continue
            if not self.damage.unmetered_support_construction:
                self.metrics.charge("support_referenced_paths")
            declared_set[path] = None
        declared = sorted(declared_set)
        obligations: list[dict] = []

        def add_obligation(obligation: dict):
            if not self.damage.unmetered_support_construction:
                self.metrics.charge("support_obligations")
            obligations.append(obligation)

        add_obligation(
            {
                "kind": "production-deletion-postcondition",
                "authority_parent": parent,
                "authority_child": child,
            }
        )
        for path in declared:
            if path != state.path:
                add_obligation(
                    {"kind": "declared-path-anchor", "path": path}
                )
        if actor == "needs-agent" and leaf == "requests":
            if fields.get("Request kind", "").strip() == "task-pickup":
                task_paths = [
                    path for path in declared if path.startswith("tasks/")
                ]
                if len(task_paths) != 1:
                    return obligations, "task pickup has no unique task path"
                add_obligation(
                    {
                        "kind": "task-pickup-postcondition",
                        "task_path": task_paths[0],
                        "task_id": Path(task_paths[0]).parts[2],
                        "pickup_path": state.path,
                    }
                )
                return obligations, None
            if fields.get("Status", "").strip() != "in-repair":
                return obligations, "ordinary agent action is not in-repair"
            add_obligation({"kind": "agent-evidence-lineage"})
            return obligations, None
        if actor == "needs-agent" and leaf == "retries":
            item = self.fixture.repo.root / state.path
            if not RECONCILE.reconciler_owned_retry(item, state.text):
                return obligations, "retry is not a production-owned retry"
            check = fields.get("Check", "").strip()
            if check not in RECONCILE.CHECKS:
                return obligations, "retry names an unknown checker"
            add_obligation(
                {
                    "kind": "generated-retry-clear",
                    "check": check,
                    "subject": fields.get("Subject", "").strip(),
                }
            )
            return obligations, None
        if actor == "needs-human" and leaf in {
            "decisions",
            "clarifications",
        }:
            if fields.get("Status", "").strip() != "folding":
                return obligations, "human action is not folding"
            add_obligation({"kind": "terminal-human-response"})
            return obligations, None
        if actor == "needs-human" and leaf == "reviews":
            outcome = fields.get("Review outcome", "").strip()
            if outcome in (
                set(RECONCILE.REVIEW_SUCCESSOR_OUTCOMES)
                | set(RECONCILE.REVIEW_REASK_OUTCOMES)
            ):
                return (
                    obligations,
                    "review successor/reask support certificate is unsupported",
                )
            if RECONCILE.delivery_class(Path(state.path).name) != "non-blocking":
                return obligations, "boundary review receipt is unsupported"
            if outcome not in RECONCILE.REVIEW_TERMINAL_OUTCOMES:
                return obligations, "review has no supported terminal outcome"
            add_obligation(
                {
                    "kind": "terminal-review-binding",
                    "outcome": outcome,
                    "review_target": fields.get("Review target", "").strip(),
                    "review_revision": fields.get(
                        "Review revision", ""
                    ).strip(),
                }
            )
            return obligations, None
        return obligations, f"unsupported authority leaf {actor}/{leaf}"

    def build_support_certificate(
        self,
        identity: tuple,
        state: ActionState,
        parent: str,
        child: str,
    ) -> dict:
        """Bind one real authority root to its complete support projection."""
        assert self.objects is not None
        self.metrics.charge("support_certificate_calls")
        before = self.objects.flat_tree(parent)
        after = self.objects.flat_tree(child)
        candidates: dict[str, None] = {}
        for mapping in (before, after):
            for path in mapping:
                if path in candidates:
                    continue
                if not self.damage.unmetered_support_construction:
                    self.metrics.charge("support_delta_candidates")
                candidates[path] = None
        changed = sorted(
            path
            for path in candidates
            if before.get(path) != after.get(path) and path != state.path
        )
        referenced_set: dict[str, None] = {}
        self.charge_production_helper_input(state.text)
        for path in RECONCILE.context_path_candidates(state.text):
            if path == state.path or path in referenced_set:
                continue
            if not self.damage.unmetered_support_construction:
                self.metrics.charge("support_referenced_paths")
            referenced_set[path] = None
        referenced = sorted(referenced_set)
        support_paths = sorted(set(changed).union(referenced))
        raw_delta = []
        for path in changed:
            if not self.damage.unmetered_support_construction:
                self.metrics.charge("support_delta_rows")
            raw_delta.append(
                {
                "path": path,
                "before": self.objects.path_entry(parent, path),
                "after": self.objects.path_entry(child, path),
                }
            )
        anchors = []
        for path in support_paths:
            if not self.damage.unmetered_support_construction:
                self.metrics.charge("support_anchor_rows")
            anchors.append(
                {
                "path": path,
                "entry": self.objects.path_entry(child, path),
                "changed_on_authority_edge": path in changed,
                }
            )
        obligations, incomplete = self.support_leaf_obligations(
            state, parent, child
        )
        unknown_entry = next(
            (
                entry
                for delta in raw_delta
                for entry in (delta["before"], delta["after"])
                if entry.get("type") == "unknown"
            ),
            None,
        )
        if unknown_entry is not None:
            incomplete = "support projection contains an unknown object type"
        body = {
            "support_schema": "queue-supplier-support/v1",
            "authority_parent": parent,
            "authority_child": child,
            "action": {
                "identity": list(identity),
                "path": state.path,
                "blob_oid": state.blob_oid,
            },
            "raw_delta": raw_delta,
            "support_paths": anchors,
            "obligations": obligations,
            "completeness": "complete" if incomplete is None else "incomplete",
            "incomplete_reason": incomplete,
        }
        return {
            **body,
            "certificate_digest": self.canonical_digest(
                "queue-supplier-support/v1", body
            ),
        }

    def authority_edge(
        self, identity: tuple, parent: str, child: str
    ) -> dict:
        states = self.states(parent, identity)
        if len(states) != 1:
            return {
                "parent": parent,
                "child": child,
                "path": None,
                "problem": (
                    f"authority parent multiplicity is {len(states)}"
                ),
            }
        state = states[0]
        self.metrics.charge("authority_calls")
        try:
            problem = RECONCILE.queue_deletion_problem(
                state.path, state.text, parent, child
            )
        except (
            RECONCILE.GitSnapshotError,
            OSError,
            ValueError,
            UnicodeError,
        ) as error:
            raise Unreadable(
                "production deletion authority could not read "
                f"{parent}->{child}: {error}"
            ) from error
        certificate = (
            self.build_support_certificate(
                identity, state, parent, child
            )
            if problem is None
            else None
        )
        return {
            "parent": parent,
            "child": child,
            "path": state.path,
            "problem": problem,
            "support_certificate": certificate,
        }

    def human_response_binding(
        self, identity: tuple, revision: str
    ) -> tuple[tuple[str, str], ...] | None:
        states = self.states(revision, identity)
        if len(states) != 1:
            return None
        return self.human_response_binding_for_state(identity, states[0])

    def human_response_binding_for_state(
        self, identity: tuple, state: ActionState
    ) -> tuple[tuple[str, str], ...] | None:
        if self.identity_view(identity)["actor"] != "needs-human":
            return None
        fields = RECONCILE.human_response_fields(state.text)
        response_key = RECONCILE.first_concrete_response(fields)
        binding = []
        if self.identity_view(identity)["leaf"] == "reviews":
            for key in ("Review target", "Review revision"):
                value = fields[key]
                pending = (
                    self.broad_review_pending(value)
                    if self.damage.broad_review_pending_normalization
                    else self.explicit_review_pending(value)
                )
                concrete = not pending
                if (
                    self.damage.treat_review_pending_as_concrete
                    and self.explicit_review_pending(value)
                ):
                    concrete = True
                if concrete:
                    binding.append((key, value))
        if response_key is not None:
            binding.extend(
                (
                    ("response_field", response_key),
                    ("response", fields[response_key]),
                )
            )
        if self.identity_view(identity)["leaf"] == "reviews":
            for key in ("Reviewed revision", "Review outcome"):
                value = fields[key]
                concrete = (
                    RECONCILE.review_outcome_value(value) != "pending"
                    if key == "Review outcome"
                    else RECONCILE.has_concrete_value(value)
                )
                if concrete:
                    binding.append((key, value))
        return tuple(binding) or None

    @staticmethod
    def explicit_review_pending(value: str) -> bool:
        return (value or "").strip().lower() == "pending"

    @staticmethod
    def broad_review_pending(value: str) -> bool:
        """Deliberately damaged normalizer used only by an observed-red."""
        value = (value or "").strip()
        normalized = value.strip("`").casefold().replace("\u0131", "i")
        return (
            not RECONCILE.has_concrete_value(value)
            or normalized == "pending"
        )

    def implicated_human_binding_problem(
        self,
        identity: tuple,
        revisions: Iterable[str],
        parent_role: str,
        *,
        optional_revisions: Iterable[str] = (),
    ) -> str | None:
        expected = self.human_response_binding(identity, self.fixture.O)
        if (
            expected is None
            and self.identity_view(identity)["actor"] != "needs-human"
        ):
            return None
        expected_fields = dict(expected or ())
        optional = set(optional_revisions)
        observed_by_revision = {}
        for revision in self.stable_oids(revisions):
            observed = self.human_response_binding(
                identity, revision
            )
            if observed is None and revision in optional:
                continue
            observed_fields = dict(observed or ())
            observed_by_revision[revision] = observed_fields
            mismatches = {
                key: {
                    "expected": value,
                    "observed": observed_fields.get(key),
                }
                for key, value in expected_fields.items()
                if observed_fields.get(key) != value
                and not (
                    revision in optional
                    and key not in observed_fields
                )
            }
            if mismatches:
                return (
                    f"{parent_role} parent {revision} does not preserve "
                    f"every concrete O-anchored human response/review "
                    f"binding field at "
                    f"O {self.fixture.O}: expected "
                    f"{json.dumps(expected_fields, sort_keys=True)}, "
                    f"observed {json.dumps(observed_fields, sort_keys=True)}, "
                    f"mismatches {json.dumps(mismatches, sort_keys=True)}"
                )
        field_values: dict[str, dict[str, list[str]]] = {}
        for revision, observed_fields in observed_by_revision.items():
            for key, value in observed_fields.items():
                field_values.setdefault(key, {}).setdefault(
                    value, []
                ).append(revision)
        conflicts = {
            key: values
            for key, values in field_values.items()
            if len(values) > 1
        }
        if conflicts:
            return (
                f"{parent_role} parents do not unify concrete human "
                f"response/review binding fields implicated in the event: "
                f"O {self.fixture.O} expected "
                f"{json.dumps(expected_fields, sort_keys=True)}, observed "
                f"{json.dumps(observed_by_revision, sort_keys=True)}, "
                f"conflicts {json.dumps(conflicts, sort_keys=True)}"
            )
        return None

    def old_tip_human_binding_problem(
        self, identity: tuple, authority_edges: list[dict]
    ) -> str | None:
        if self.damage.omit_old_tip_human_binding:
            return None
        return self.implicated_human_binding_problem(
            identity,
            (edge["parent"] for edge in authority_edges),
            "authority",
        )

    def supplier_carrier_human_binding_problem(
        self,
        identity: tuple,
        authority_edges: list[dict],
        propagation_edges: list[dict],
    ) -> str | None:
        revisions = [edge["parent"] for edge in authority_edges]
        optional_revisions = []
        if not self.damage.omit_supplier_carrier_human_binding:
            for edge in propagation_edges:
                parent = edge["parent"]
                observed = self.human_response_binding(identity, parent)
                if (
                    self.damage.omit_unanswered_published_review_binding
                    and observed is not None
                    and "response" not in dict(observed)
                ):
                    continue
                revisions.append(parent)
                optional_revisions.append(parent)
        return self.implicated_human_binding_problem(
            identity,
            revisions,
            "supplier authority/propagation",
            optional_revisions=optional_revisions,
        )

    def parent_roles(self, identity: tuple, child: str):
        assert self.graph is not None
        carrying = []
        absent = []
        neutral = []
        duplicate = []
        for parent in self.graph.parents[child]:
            multiplicity = len(self.states(parent, identity))
            if parent in self.graph.c_descendants:
                if multiplicity == 1:
                    carrying.append(parent)
                elif multiplicity > 1:
                    duplicate.append(parent)
                else:
                    absent.append(parent)
            elif multiplicity == 0 or self.damage.ignore_outside_c_collision:
                neutral.append(parent)
            else:
                duplicate.append(parent)
        return carrying, absent, neutral, duplicate

    def raw_direct_events(self, identity: tuple) -> list[Event]:
        """Validate direct authority, without final-absence selection."""
        assert self.graph is not None
        events = []
        for child in self.graph.order:
            if (
                child not in self.graph.candidate_nodes
                or self.states(child, identity)
            ):
                continue
            carrying, absent, neutral, duplicate = self.parent_roles(
                identity, child
            )
            if absent:
                continue
            if duplicate:
                collision_edges = []
                for parent in duplicate:
                    states = self.states(parent, identity)
                    if (
                        parent not in self.graph.c_descendants
                        and len(states) == 1
                    ):
                        edge = self.authority_edge(
                            identity, parent, child
                        )
                        edge["problem"] = (
                            "outside-C parent carries a matching identity; "
                            "its provenance is an unresolved collision"
                        )
                        edge["support_certificate"] = None
                        collision_edges.append(edge)
                event = Event(
                    "ambiguous",
                    "direct",
                    child,
                    collision_edges,
                    [],
                    neutral,
                    [],
                    "direct-parent-multiplicity",
                    "a parent has colliding exact identity provenance",
                )
                events.append(
                    self.attach_causal_metadata(
                        event,
                        (
                            self.direct_causal_roots(event)
                            if collision_edges
                            else [self.synthetic_causal_root(event)]
                        ),
                    )
                )
                continue
            if not carrying:
                continue
            selected = (
                carrying
                if self.damage.validate_all_direct_parents
                else carrying[:1]
            )
            edges = [
                self.authority_edge(identity, parent, child)
                for parent in selected
            ]
            carry_proofs = [
                self.carry_proof(identity, parent) for parent in carrying
            ]
            continuity = next(
                (proof["reason"] for proof in carry_proofs if proof["reason"]),
                None,
            )
            invalid = [edge for edge in edges if edge["problem"]]
            old_human_problem = self.old_tip_human_binding_problem(
                identity, edges
            )
            if continuity:
                status = "ambiguous"
                code = "foreign-or-discontinuous-carrier"
                reason = continuity
            elif invalid:
                status = "invalid"
                code = "invalid-direct-authority"
                reason = "; ".join(
                    f"{edge['parent']}: {edge['problem']}"
                    for edge in invalid
                )
            elif old_human_problem:
                status = "invalid"
                code = "old-tip-human-binding-conflict"
                reason = old_human_problem
            else:
                status = "valid"
                code = "valid-direct-authority"
                reason = (
                    f"all {len(selected)} carrying parent edge(s) passed "
                    "production deletion authority"
                )
            event = Event(
                status,
                "direct",
                child,
                edges,
                [],
                sorted(
                    set(neutral).union(
                        parent
                        for proof in carry_proofs
                        for parent in proof["outside_neutral"]
                    )
                ),
                [],
                code,
                reason,
                carry_proofs=carry_proofs,
            )
            events.append(
                self.attach_causal_metadata(
                    event, self.direct_causal_roots(event)
                )
            )
        return events

    def direct_events(self, identity: tuple) -> list[Event]:
        events = []
        for event in self.raw_direct_events(identity):
            post = (
                self.absence_problem(
                    identity, event.child, self.fixture.N
                )
                if (
                    event.status == "valid"
                    and event.child
                    and self.damage.enforce_post_event_absence
                )
                else None
            )
            if post:
                prior = event.reason_records
                event = dataclasses.replace(
                    event,
                    status="invalid",
                    reason_code="post-event-reintroduction",
                    reason="post-event absence is not continuous: " + post,
                )
                event = self.attach_causal_metadata(
                    event,
                    self.retag_roots(event.causal_roots, "invalid"),
                    prior,
                )
            events.append(event)
        return events

    @staticmethod
    def event_key(event: Event):
        return tuple(
            sorted(
                (edge["parent"], edge["child"])
                for edge in event.authority_edges
            )
        )

    def causal_source_key(self, event: Event):
        return (event.child, event.status, self.event_key(event))

    @staticmethod
    def causal_root_key(root: dict):
        return (
            root["status"],
            root["root_child"],
            tuple(
                (edge["parent"], edge["child"])
                for edge in root["component_edges"]
            ),
        )

    def direct_causal_roots(self, event: Event) -> list[dict]:
        return [
            {
                "status": event.status,
                "root_child": event.child,
                "component_edges": [
                    {"parent": parent, "child": child}
                    for parent, child in self.event_key(event)
                ],
            }
        ]

    def stable_roots(self, roots):
        ordered = {}
        for root in roots:
            ordered.setdefault(self.causal_root_key(root), root)
        return list(ordered.values())

    def retag_roots(self, roots, status: str):
        return self.stable_roots(
            {
                **root,
                "status": status,
            }
            for root in roots
        )

    @staticmethod
    def stable_reason_records(records):
        ordered = {}
        for record in records:
            key = (
                record["reason_code"],
                record["source_child"],
                record["reason"],
                json.dumps(record["root_keys"], sort_keys=True),
            )
            ordered.setdefault(key, record)
        return list(ordered.values())

    def attach_causal_metadata(
        self,
        event: Event,
        roots,
        prior_records=(),
    ) -> Event:
        event.causal_roots = self.stable_roots(roots)
        root_keys = [
            list(self.causal_root_key(root))
            for root in event.causal_roots
        ]
        event.reason_records = self.stable_reason_records(
            [*prior_records]
            + [
                {
                    "reason_code": event.reason_code,
                    "source_child": event.child,
                    "reason": event.reason,
                    "root_keys": root_keys,
                }
            ]
        )
        return event

    def synthetic_causal_root(self, event: Event) -> dict:
        return {
            "status": event.status,
            "root_child": event.child,
            "component_edges": [],
        }

    @staticmethod
    def stable_edges(edges):
        return list(
            {
                (edge["parent"], edge["child"]): edge
                for edge in edges
            }.values()
        )

    @staticmethod
    def stable_support_checks(checks):
        ordered = {}
        for check in checks:
            key = (
                check["certificate_digest"],
                check["adoption_child"],
                tuple(check["absent_source_parents"]),
            )
            ordered.setdefault(key, check)
        return list(ordered.values())

    def replay_support_postcondition(
        self,
        identity: tuple,
        certificate: dict,
        revision: str,
    ) -> str | None:
        """Re-evaluate the root action at one source/adoption projection."""
        states = [
            state
            for state in self.states(
                certificate["authority_parent"], identity
            )
            if state.path == certificate["action"]["path"]
            and state.blob_oid == certificate["action"]["blob_oid"]
        ]
        if len(states) != 1:
            return "authority root action bytes are not uniquely readable"
        self.metrics.charge("support_adoption_checks")
        try:
            return RECONCILE.queue_deletion_problem(
                states[0].path,
                states[0].text,
                certificate["authority_parent"],
                revision,
            )
        except (
            RECONCILE.GitSnapshotError,
            OSError,
            ValueError,
            UnicodeError,
        ) as error:
            raise Unreadable(
                "supplier support postcondition could not read "
                f"{certificate['authority_parent']}->{revision}: {error}"
            ) from error

    def evaluate_support_obligations(
        self,
        identity: tuple,
        certificate: dict,
        revision: str,
    ) -> dict:
        """Evaluate complete typed obligations; generic replay is diagnostic."""
        states = [
            state
            for state in self.states(
                certificate["authority_parent"], identity
            )
            if state.path == certificate["action"]["path"]
            and state.blob_oid == certificate["action"]["blob_oid"]
        ]
        generic_problem = self.replay_support_postcondition(
            identity, certificate, revision
        )
        if len(states) != 1:
            return {
                "revision": revision,
                "generic_replay_problem": generic_problem,
                "problem": "authority root action bytes are not unique",
            }
        state = states[0]
        obligations = certificate["obligations"]
        pickup = next(
            (
                item
                for item in obligations
                if item["kind"] == "task-pickup-postcondition"
            ),
            None,
        )
        retry = next(
            (
                item
                for item in obligations
                if item["kind"] == "generated-retry-clear"
            ),
            None,
        )
        problem = None
        if pickup is not None:
            try:
                status, task = RECONCILE.task_status_at(
                    revision, pickup["task_id"]
                )
            except (
                RECONCILE.GitSnapshotError,
                OSError,
                ValueError,
                UnicodeError,
            ) as error:
                raise Unreadable(
                    "pickup support obligation could not read "
                    f"{revision}: {error}"
                ) from error
            claimant = (task or {}).get("Claimed-by", "").strip()
            queue_paths = RECONCILE.task_queue_paths(
                (task or {}).get("Queue actions", "")
            )
            if (
                status not in RECONCILE.RESOLVING_TASK_STATUSES
                or not RECONCILE.has_concrete_value(claimant)
                or claimant == "unclaimed"
                or pickup["pickup_path"] in queue_paths
            ):
                problem = (
                    "pickup task is not one uniquely claimed monotone "
                    f"incarnation at {revision}"
                )
        elif retry is not None:
            try:
                clear = RECONCILE.generated_retry_clear(
                    state.text, revision
                )
            except (
                RECONCILE.GitSnapshotError,
                OSError,
                ValueError,
                UnicodeError,
            ) as error:
                raise Unreadable(
                    "retry support obligation could not read "
                    f"{revision}: {error}"
                ) from error
            if not clear:
                problem = (
                    f"retry checker {retry['check']} still reports subject "
                    f"{retry['subject']} at {revision}"
                )
        else:
            problem = generic_problem
        return {
            "revision": revision,
            "generic_replay_problem": generic_problem,
            "problem": problem,
        }

    def dynamic_support_paths(
        self, certificate: dict, revision: str
    ) -> list[str]:
        """Resolve typed monotone obligations to their current exact paths."""
        assert self.objects is not None
        paths: dict[str, None] = {}

        def discover(path: str):
            if path in paths:
                return
            if not self.damage.unmetered_dynamic_support:
                self.metrics.charge("dynamic_support_paths_discovered")
                self.metrics.charge(
                    "dynamic_support_path_bytes",
                    len(path.encode("utf-8", errors="surrogateescape")),
                )
            paths[path] = None

        def traverse(path: str):
            if not self.damage.unmetered_dynamic_support:
                self.metrics.charge("dynamic_support_paths_traversed")

        for obligation in certificate["obligations"]:
            if obligation["kind"] == "task-pickup-postcondition":
                tree_paths = self.objects.flat_tree(revision)
                task_pattern = re.compile(
                    rf"tasks/(?:{'|'.join(RECONCILE.TASK_STATUSES)})/"
                    + re.escape(obligation["task_id"])
                    + r"/task\.md"
                )
                incarnations = []
                for path in tree_paths:
                    traverse(path)
                    if task_pattern.fullmatch(path):
                        discover(path)
                        incarnations.append(path)
                for task_path in incarnations:
                    task_dir = Path(task_path).parent
                    for path in tree_paths:
                        traverse(path)
                        if (
                            Path(path).parent == task_dir
                            and Path(path).name
                            in RECONCILE.TASK_ARTIFACT_NAMES
                        ):
                            discover(path)
            elif obligation["kind"] == "generated-retry-clear":
                subject = obligation["subject"].strip("`")
                if RECONCILE.valid_queue_item_path(subject) or (
                    subject
                    and not subject.startswith("/")
                    and ".." not in Path(subject).parts
                ):
                    discover(subject)
        return sorted(paths)

    def supplier_support_checks(
        self,
        identity: tuple,
        authority_edges: list[dict],
        absent_parents: list[str],
        child: str,
    ) -> tuple[list[dict], str | None]:
        """Require adoption to copy each root's current source projection."""
        assert self.objects is not None
        if self.damage.skip_supplier_support_certificate:
            return [], None
        certificates = {
            edge["support_certificate"]["certificate_digest"]: edge[
                "support_certificate"
            ]
            for edge in authority_edges
            if edge.get("support_certificate") is not None
        }
        checks = []
        problems = []
        if len(certificates) != len(
            {
                (edge["parent"], edge["child"])
                for edge in authority_edges
                if edge.get("problem") is None
            }
        ):
            problems.append("a valid authority edge has no support certificate")
        for digest, certificate in sorted(certificates.items()):
            source_parents = sorted(set(absent_parents))
            support_path_set: dict[str, None] = {}

            def add_support_path(path: str):
                if path in support_path_set:
                    return
                self.metrics.charge("support_paths_checked")
                support_path_set[path] = None

            for anchor in certificate["support_paths"]:
                add_support_path(anchor["path"])
            for revision in [*source_parents, child]:
                for path in self.dynamic_support_paths(
                    certificate, revision
                ):
                    add_support_path(path)
            support_paths = sorted(support_path_set)
            self.metrics.charge(
                "support_paths_checked",
                len(support_paths) * len(source_parents),
            )
            source_projections = [
                {
                    "parent": parent,
                    "entries": [
                        {
                            "path": path,
                            "entry": self.objects.path_entry(parent, path),
                        }
                        for path in support_paths
                    ],
                }
                for parent in source_parents
            ]
            child_projection = [
                {
                    "path": path,
                    "entry": self.objects.path_entry(child, path),
                }
                for path in support_paths
            ]
            agreed = bool(source_projections) and all(
                projection["entries"] == source_projections[0]["entries"]
                for projection in source_projections[1:]
            )
            copied = bool(source_projections) and (
                child_projection == source_projections[0]["entries"]
            )
            replay = [
                self.evaluate_support_obligations(
                    identity, certificate, revision
                )
                for revision in [*source_parents, child]
            ]
            replay_valid = all(item["problem"] is None for item in replay)
            complete = certificate["completeness"] == "complete"
            local_problems = []
            if not complete:
                local_problems.append(
                    "incomplete certificate: "
                    + str(certificate["incomplete_reason"])
                )
            if not agreed:
                local_problems.append(
                    "absent source parents disagree on support projection"
                )
            if not copied:
                local_problems.append(
                    "supplier adoption did not copy source support projection"
                )
            if not replay_valid:
                local_problems.append(
                    "root deletion postcondition failed at source/adoption: "
                    + "; ".join(
                        f"{item['revision']}: {item['problem']}"
                        for item in replay
                        if item["problem"] is not None
                    )
                )
            check = {
                "support_schema": "queue-supplier-support/v1",
                "certificate_digest": digest,
                "authority_parent": certificate["authority_parent"],
                "authority_child": certificate["authority_child"],
                "adoption_child": child,
                "absent_source_parents": source_parents,
                "source_projections": source_projections,
                "adoption_projection": child_projection,
                "tree_projection_status": (
                    "valid" if agreed and copied else "invalid"
                ),
                "postcondition_status": (
                    "valid" if replay_valid else "invalid"
                ),
                "obligation_evaluations": replay,
                "status": "valid" if not local_problems else "invalid",
                "problem": (
                    None if not local_problems else "; ".join(local_problems)
                ),
            }
            checks.append(check)
            problems.extend(local_problems)
        if not certificates:
            problems.append("supplier root has no support certificate")
        return checks, (None if not problems else "; ".join(problems))

    @staticmethod
    def stable_oids(oids):
        return list(dict.fromkeys(oids))

    def frozen_skeleton_problem(
        self, before: ActionState, after: ActionState
    ) -> tuple[str | None, str | None]:
        """Mirror the production frozen-byte complement for one real edge."""
        if self.damage.skip_persisted_frozen_skeleton:
            return None, "DAMAGED-skipped"
        if RECONCILE.queue_frozen_skeleton(
            before.path, before.text
        ) == RECONCILE.queue_frozen_skeleton(after.path, after.text):
            return None, None
        if RECONCILE.introduces_final_retry_notes(
            before.path, before.text, after.path, after.text
        ):
            return None, "final-retry-notes"
        if RECONCILE.pure_first_human_response(
            before.path, before.text, after.path, after.text
        ):
            return None, "pure-first-human-response"
        return (
            "protected queue bytes changed while the exact production "
            "identity remained live",
            None,
        )

    def binding_subset_problem(
        self,
        identity: tuple,
        before: ActionState,
        after: ActionState,
    ) -> str | None:
        """Require every concrete earlier human field in the later state."""
        prior = dict(
            self.human_response_binding_for_state(identity, before) or ()
        )
        current = dict(
            self.human_response_binding_for_state(identity, after) or ()
        )
        mismatches = {
            key: {"before": value, "after": current.get(key)}
            for key, value in prior.items()
            if current.get(key) != value
        }
        if not mismatches:
            return None
        return (
            "concrete human response/review binding changed or disappeared: "
            f"{json.dumps(mismatches, sort_keys=True)}"
        )

    def birth_state_witness(
        self, identity: tuple, state: ActionState
    ) -> dict:
        """Bind canonical production-visible birth state, never Git provenance.

        The witness deliberately excludes the queue path, commit identity,
        timestamps, operational counters, and retry diagnostics that production
        sanctions as mutable.  It can compare state, not prove that one commit
        was replayed from another.
        """
        view = self.identity_view(identity)
        fields = RECONCILE.text_fields(state.text)
        lifecycle_projection = {
            "status": fields.get("Status", "").strip(),
        }
        if view["actor"] == "needs-human":
            response = RECONCILE.human_response_fields(state.text)
            lifecycle_projection["human_response_review_binding"] = {
                key: response[key]
                for key in (
                    "Your answer",
                    "Your review",
                    "Review target",
                    "Review revision",
                    "Reviewed revision",
                    "Review outcome",
                )
            }
        witness = {
            "actor": view["actor"],
            "delivery_class": RECONCILE.delivery_class(
                Path(state.path).name
            ),
            "frozen_skeleton": RECONCILE.queue_frozen_skeleton(
                state.path, state.text
            ),
            "initial_lifecycle_review_binding": lifecycle_projection,
            "leaf": view["leaf"],
            "production_identity_transcript": list(identity[3:]),
            "schema": "queue-birth-state-witness/v1",
        }
        size = self.canonical_json_size(witness)
        self.metrics.charge("origin_witness_bytes", size)
        payload = json.dumps(
            witness,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        if len(payload) != size:
            raise AssertionError("birth witness canonical size drift")
        digest = hashlib.sha256(
            b"queue-birth-state-witness/v1\0" + payload
        ).hexdigest()
        return {
            "digest": f"sha256:{digest}",
            "state": witness,
        }

    def birth_schema_problem(
        self,
        identity: tuple,
        commit: str,
        state: ActionState,
    ) -> str | None:
        """Replay the context-free production queue schema at one birth.

        ``check_queue_schema`` itself reads the candidate index and repository
        worktree, so calling it for a historical commit would validate the wrong
        bytes.  This projection instead composes the production parser,
        constants, and pure predicates that are meaningful at an arbitrary Git
        snapshot.  Context links are resolved from that snapshot.  Repository-
        global reciprocity and current-template presentation remain independent
        admission gates; this POC does not pretend to replay them historically.
        """
        assert self.objects is not None
        parts = Path(state.path).parts
        if not RECONCILE.valid_queue_item_path(state.path):
            return "birth path is not a valid production queue-item path"
        actor, leaf = parts[1], parts[2]
        if len(identity) < 3 or (actor, leaf) != identity[1:3]:
            return "birth path actor/leaf disagrees with production identity"
        if RECONCILE.queue_action_identity(state.path, state.text) != identity:
            return "birth does not round-trip to the production identity"

        timing = RECONCILE.delivery_class(parts[3])
        if timing not in RECONCILE.QUEUE_TIMING_FIELDS:
            return "birth filename has no production delivery class"
        fields = RECONCILE.text_fields(state.text)
        duplicates = sorted(
            key
            for key, count in RECONCILE.field_counts(state.text).items()
            if count != 1
        )
        if duplicates:
            return "birth has duplicate structured fields: " + ", ".join(
                duplicates
            )

        expected_timing = set(RECONCILE.QUEUE_TIMING_FIELDS[timing])
        all_timing = {
            key
            for values in RECONCILE.QUEUE_TIMING_FIELDS.values()
            for key in values
        }
        missing_timing = sorted(expected_timing - set(fields))
        contradictory_timing = sorted(
            (all_timing - expected_timing).intersection(fields)
        )
        empty_timing = sorted(
            key
            for key in expected_timing
            if key in fields
            and not RECONCILE.has_concrete_value(fields[key])
        )
        if missing_timing or contradictory_timing or empty_timing:
            return (
                "birth delivery header is not schema-valid: "
                f"missing={missing_timing}, contradictory="
                f"{contradictory_timing}, empty={empty_timing}"
            )

        required = list(
            RECONCILE.QUEUE_SCHEMAS.get(
                f"{actor}/{leaf}",
                ["Status", "Filed", "Action", "Full context"],
            )
        )
        missing = sorted(set(required) - set(fields))
        if missing:
            return "birth is missing required fields: " + ", ".join(missing)
        status = fields.get("Status", "").strip()
        is_generated_retry = identity[0] == "generated-retry"
        is_pickup = (
            actor == "needs-agent"
            and leaf == "requests"
            and fields.get("Request kind", "").strip() == "task-pickup"
        )
        if actor == "needs-agent":
            if leaf not in {"requests", "retries"}:
                return "birth is not a typed production agent action"
            if status != "open":
                return "agent action birth is not open"
            if is_generated_retry and leaf != "retries":
                return "generated retry birth is outside the retry leaf"
            if is_pickup:
                backlog = RECONCILE.pickup_task_path(state.text)
                entry = (
                    self.objects.path_entry(commit, backlog)
                    if backlog is not None
                    else {"state": "absent"}
                )
                if entry["state"] != "present" or entry["type"] != "blob":
                    return "task-pickup birth has no live backlog origin"
                _kind, backlog_bytes = self.objects.read(entry["oid"])
                try:
                    backlog_text = backlog_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    return "task-pickup birth backlog is not UTF-8"
                backlog_fields = RECONCILE.text_fields(backlog_text)
                if (
                    backlog_fields.get("Claimed-by", "").strip()
                    != "unclaimed"
                    or state.path
                    not in RECONCILE.task_queue_paths(
                        backlog_fields.get("Queue actions", "")
                    )
                ):
                    return "task-pickup birth has no unclaimed task backlink"
        elif actor == "needs-human":
            response = RECONCILE.human_response_fields(state.text)
            if leaf in {"decisions", "clarifications"}:
                if status != "waiting":
                    return (
                        "human decision/clarification birth is not waiting"
                    )
                if RECONCILE.first_concrete_response(response) is not None:
                    return "human decision/clarification is answered at birth"
            elif leaf == "reviews":
                if status not in {"awaiting-artifact", "waiting"}:
                    return "review birth is neither awaiting-artifact nor waiting"
                if not RECONCILE.unanswered_review(response):
                    return "review is answered or terminally bound at birth"
                target = response["Review target"]
                revision = response["Review revision"]
                if status == "awaiting-artifact":
                    if not (
                        self.explicit_review_pending(target)
                        and self.explicit_review_pending(revision)
                    ):
                        return (
                            "awaiting-artifact review birth has a concrete binding"
                        )
                else:
                    parsed_target = RECONCILE.review_target(target)
                    if parsed_target is None:
                        return "waiting review birth has no concrete target"
                    if not RECONCILE.REVIEW_REVISION_RE.fullmatch(revision):
                        return "waiting review birth has no immutable revision"
                    target_kind, target_value = parsed_target
                    if target_kind == "git" and revision != target_value:
                        return "waiting review birth Git binding disagrees"
                    if target_kind == "https" and not revision.startswith(
                        "sha256:"
                    ):
                        return "waiting HTTPS review birth is not SHA-bound"
                    if target_kind == "local":
                        entry = self.objects.path_entry(commit, target_value)
                        if (
                            entry["state"] != "present"
                            or entry["type"] != "blob"
                        ):
                            return "waiting review birth target is absent"
                        _kind, target_bytes = self.objects.read(entry["oid"])
                        expected = "sha256:" + hashlib.sha256(
                            target_bytes
                        ).hexdigest()
                        if revision != expected:
                            return "waiting review birth target digest disagrees"
            else:
                return "birth is not a typed production human action"
        else:
            return "birth actor is outside the production queue lifecycle"
        if RECONCILE.parse_leading_date(fields.get("Filed", "")) is None:
            return "birth has no valid Filed calendar date"
        if not RECONCILE.has_concrete_value(fields.get("Action", "")):
            return "birth has no concrete Action"

        needs_resolution_evidence = actor == "needs-human" or (
            actor == "needs-agent"
            and not (is_pickup or is_generated_retry)
        )
        if needs_resolution_evidence and not RECONCILE.resolution_evidence_paths(
            state.text
        ):
            return "birth has no production resolution-evidence declaration"

        if "Full context" in fields:
            candidates = RECONCILE.context_path_candidates(
                fields["Full context"]
            )
            if not candidates or not any(
                self.objects.path_entry(commit, candidate)["state"]
                == "present"
                for candidate in candidates
            ):
                return "birth Full context is absent from its Git snapshot"
        if actor == "needs-human":
            responses = (
                ("Your review",)
                if leaf == "reviews"
                else ("Your answer",)
                if leaf in {"decisions", "clarifications"}
                else ("Your answer", "Your review")
            )
            if not any(response in fields for response in responses):
                return "birth has no production human-response slot"
        return None

    def origin_arm_proof(self, identity: tuple, tip: str) -> dict:
        """Prove exactly one legal C-local birth and continuous arm carriage."""
        assert self.graph is not None
        region = self.graph.between(self.graph.C, tip)
        ordered = self.graph.ordered(region)
        births: list[tuple[str, ActionState]] = []
        edges: list[dict] = []
        outside_neutral: set[str] = set()
        outside_collisions: list[dict] = []
        prebirth_neutral: set[str] = set()
        multiplicities: list[dict] = []
        child_parents: dict[str, list[tuple[str, ActionState]]] = {}
        birth_schema_problems: list[dict] = []

        for child in ordered:
            self.metrics.charge("origin_arm_nodes")
            child_states = self.states(child, identity)
            if len(child_states) > 1:
                multiplicities.append(
                    {
                        "commit": child,
                        "multiplicity": len(child_states),
                        "paths": [state.path for state in child_states],
                    }
                )
            if child == self.graph.C:
                continue
            carrying: list[tuple[str, ActionState]] = []
            absent: list[str] = []
            # A commit object may contain the same parent header more than
            # once and still be accepted by Git.  Parent identity is logical,
            # not header multiplicity: classify each parent OID exactly once
            # so a repeated header cannot turn the selected source into a
            # later compatible-carrier record during stable serialization.
            for parent in sorted(set(self.graph.parents.get(child, ()))):
                self.metrics.charge("origin_parent_edges")
                parent_states = self.states(parent, identity)
                if len(parent_states) > 1:
                    multiplicities.append(
                        {
                            "commit": parent,
                            "multiplicity": len(parent_states),
                            "paths": [state.path for state in parent_states],
                        }
                    )
                if parent not in self.graph.c_descendants:
                    if parent_states:
                        outside_collisions.append(
                            {
                                "parent": parent,
                                "multiplicity": len(parent_states),
                                "paths": [
                                    state.path for state in parent_states
                                ],
                                "scope": "outside-C",
                            }
                        )
                    else:
                        outside_neutral.add(parent)
                    continue
                if len(parent_states) == 1:
                    carrying.append((parent, parent_states[0]))
                elif not parent_states:
                    absent.append(parent)
            child_parents[child] = carrying
            if len(child_states) != 1:
                continue
            if not carrying:
                self.metrics.charge("origin_births")
                births.append((child, child_states[0]))
                prebirth_neutral.update(absent)
                schema_problem = self.birth_schema_problem(
                    identity, child, child_states[0]
                )
                if schema_problem is not None:
                    birth_schema_problems.append(
                        {"commit": child, "problem": schema_problem}
                    )

        unique_multiplicities = sorted(
            {
                json.dumps(item, sort_keys=True): item
                for item in multiplicities
            }.values(),
            key=lambda item: item["commit"],
        )
        unique_collisions = sorted(
            {
                json.dumps(item, sort_keys=True): item
                for item in outside_collisions
            }.values(),
            key=lambda item: (item["parent"], item["multiplicity"]),
        )
        post_birth_absent: set[str] = set()
        if births and not self.damage.skip_origin_post_birth_absence:
            birth_commits = {commit for commit, _state in births}
            for commit in ordered:
                if commit == self.graph.C or self.states(commit, identity):
                    continue
                ancestors = self.graph.ancestors(commit)
                if birth_commits.intersection(ancestors):
                    post_birth_absent.add(commit)

        problem = None
        reason_code = "origin-arm-valid"
        if len(self.states(self.graph.C, identity)) != 0:
            problem = "origin proof requires the identity to be absent at C"
            reason_code = "origin-present-at-C"
        elif len(self.states(tip, identity)) != 1:
            problem = (
                f"origin arm tip {tip} has multiplicity "
                f"{len(self.states(tip, identity))}"
            )
            reason_code = "origin-endpoint-multiplicity"
        elif unique_multiplicities:
            problem = (
                "origin arm contains identity multiplicity: "
                f"{json.dumps(unique_multiplicities, sort_keys=True)}"
            )
            reason_code = "origin-arm-multiplicity"
        elif unique_collisions:
            problem = (
                "origin arm has outside-C identity collision(s): "
                f"{json.dumps(unique_collisions, sort_keys=True)}"
            )
            reason_code = "origin-outside-C-collision"
        elif not births:
            problem = "origin arm has no legal all-parents-absent birth"
            reason_code = "origin-missing-birth"
        elif birth_schema_problems:
            problem = (
                "origin arm has schema-invalid birth(s): "
                f"{json.dumps(birth_schema_problems, sort_keys=True)}"
            )
            reason_code = "origin-birth-schema-invalid"
        elif (
            len(births) != 1
            and not self.damage.skip_origin_birth_uniqueness
        ):
            problem = (
                f"origin arm has {len(births)} legal births instead of one"
            )
            reason_code = "origin-birth-multiplicity"
        elif post_birth_absent:
            problem = (
                "origin arm has post-birth absent descendant(s): "
                f"{sorted(post_birth_absent)}"
            )
            reason_code = "origin-post-birth-absence"

        if problem is None:
            for child in ordered:
                child_states = self.states(child, identity)
                if len(child_states) != 1:
                    continue
                carrying = child_parents.get(child, [])
                candidate_edges = [
                    self.mutation_edge(
                        identity,
                        parent,
                        child,
                        before,
                        child_states[0],
                    )
                    for parent, before in carrying
                ]
                edges.extend(candidate_edges)
                if candidate_edges:
                    valid_sources = sorted(
                        (
                            edge
                            for edge in candidate_edges
                            if edge["problem"] is None
                        ),
                        key=lambda edge: (
                            edge["parent"], edge["child"], edge["path"]
                        ),
                    )
                    if not valid_sources:
                        problem = (
                            "origin arm has no production-valid source "
                            f"mutation into {child}: "
                            + "; ".join(
                                edge["problem"] for edge in candidate_edges
                            )
                        )
                        reason_code = "origin-invalid-mutation"
                        break
                    source = valid_sources[0]
                    source["role"] = "source"
                    for (parent, before), edge in zip(
                        carrying, candidate_edges, strict=True
                    ):
                        if edge is source:
                            continue
                        edge["role"] = "compatible-carrier"
                        if self.damage.reject_all_origin_invalid_carriers:
                            # Historical reject-all logic treated every
                            # non-selected carrying parent as an invalid
                            # competing source, even when it was a compatible
                            # carrier.  Keep that exact false-positive as the
                            # damage mutant for the R19 proof obligation.
                            carrier_problem = (
                                "reject-all mutant rejects a compatible "
                                "non-source carrying parent"
                            )
                        else:
                            carrier_problem = self.merge_compatible_problem(
                                identity, edge, before, child_states[0]
                            )
                        edge["problem"] = carrier_problem
                        if carrier_problem is not None:
                            problem = (
                                "origin arm has incompatible merge carrier "
                                f"{parent} into {child}: {carrier_problem}"
                            )
                            reason_code = "origin-incompatible-carrier"
                            break
                    if problem is not None:
                        break

        witness = (
            self.birth_state_witness(identity, births[0][1])
            if births
            else None
        )
        return {
            "birth_commits": [commit for commit, _state in births],
            "birth_schema_problems": birth_schema_problems,
            "birth_witness": witness,
            "edges": self.stable_edges(edges),
            "multiplicities": unique_multiplicities,
            "outside_collisions": unique_collisions,
            "outside_neutral": sorted(outside_neutral),
            "post_birth_absent": sorted(post_birth_absent),
            "prebirth_neutral": sorted(prebirth_neutral),
            "reason": problem,
            "reason_code": reason_code,
            "status": "valid" if problem is None else "ambiguous",
            "tip": tip,
        }

    def equivalent_origin_problem(
        self,
        identity: tuple,
        old_state: ActionState,
        new_state: ActionState,
    ) -> tuple[str | None, str, list[dict], dict, bool | None]:
        """Compare two valid live incarnations without claiming replay intent."""
        if self.damage.endpoint_only_origin_equality:
            return (
                None,
                "DAMAGED-endpoint-only-origin-equality",
                [],
                {"binding": None, "frozen": None, "regression": None},
                None,
            )
        proofs = [
            self.origin_arm_proof(identity, self.fixture.O),
            self.origin_arm_proof(identity, self.fixture.N),
        ]
        failed = next(
            (proof for proof in proofs if proof["reason"] is not None), None
        )
        if failed is not None:
            return (
                failed["reason"],
                failed["reason_code"],
                proofs,
                {"binding": None, "frozen": None, "regression": None},
                None,
            )

        regression = None
        frozen = None
        binding = None
        if not self.damage.skip_origin_endpoint_non_regression:
            regression = RECONCILE.queue_parent_state_regression_problem(
                old_state.text, new_state.text
            )
            frozen, _exception = self.frozen_skeleton_problem(
                old_state, new_state
            )
            binding = self.binding_subset_problem(
                identity, old_state, new_state
            )
        endpoint_checks = {
            "binding": binding,
            "frozen": frozen,
            "regression": regression,
        }
        endpoint_problem = regression or frozen or binding
        if endpoint_problem is not None:
            return (
                endpoint_problem,
                "origin-endpoint-regression",
                proofs,
                endpoint_checks,
                None,
            )

        witnesses = [proof["birth_witness"] for proof in proofs]
        witness_match = witnesses[0] == witnesses[1]
        if (
            self.origin_strategy == "B"
            and not witness_match
        ):
            return (
                "Strategy B birth-state witnesses differ",
                "origin-birth-witness-mismatch",
                proofs,
                endpoint_checks,
                False,
            )
        return (
            None,
            f"origin-strategy-{self.origin_strategy}-equivalent-live-incarnation",
            proofs,
            endpoint_checks,
            witness_match,
        )

    def mutation_edge(
        self,
        identity: tuple,
        parent: str,
        child: str,
        before: ActionState,
        after: ActionState,
    ) -> dict:
        """Call both production mutation authorities for a real Git edge."""
        self.metrics.charge("mutation_calls")
        try:
            production_problem = RECONCILE.queue_mutation_problem(
                before.path,
                after.path,
                before.text,
                after.text,
                parent,
                child,
            )
            frozen_problem, frozen_exception = self.frozen_skeleton_problem(
                before, after
            )
            regression_problem = (
                RECONCILE.queue_parent_state_regression_problem(
                    before.text, after.text
                )
            )
        except (
            RECONCILE.GitSnapshotError,
            OSError,
            ValueError,
            UnicodeError,
        ) as error:
            raise Unreadable(
                "production mutation authority could not read "
                f"{parent}->{child}: {error}"
            ) from error
        binding_problem = self.binding_subset_problem(
            identity, before, after
        )
        if (
            self.damage.broad_review_pending_normalization
            and binding_problem is None
            and production_problem is not None
            and production_problem.startswith(
                "immutable review binding changed outside"
            )
        ):
            production_problem = None
        # Production mutation authority owns ordinary linear transitions,
        # including its exact unanswered review retraction exception.  The
        # subset comparison is evidence for O anchoring and for non-authoring
        # merge carriers; it must not narrow a production-valid real edge.
        full_problem = production_problem or frozen_problem
        return {
            "parent": parent,
            "child": child,
            "source_path": before.path,
            "path": after.path,
            "production_problem": production_problem,
            "frozen_problem": frozen_problem,
            "frozen_exception": frozen_exception,
            "regression_problem": regression_problem,
            "binding_problem": binding_problem,
            "role": "unselected",
            "problem": full_problem,
        }

    def merge_compatible_problem(
        self,
        identity: tuple,
        edge: dict,
        before: ActionState,
        after: ActionState,
    ) -> str | None:
        """Validate a non-authoring merge carrier without borrowed mutation."""
        if edge["regression_problem"]:
            return edge["regression_problem"]
        if edge["frozen_problem"]:
            return edge["frozen_problem"]
        if edge["binding_problem"]:
            return edge["binding_problem"]
        if edge["production_problem"] is None:
            return None

        # A merge may receive a production-valid review publication/fold from
        # another live carrying parent.  A completely pending parent is
        # compatible with that child, but it is never itself the authoring
        # edge.  No other production mutation failure is waived.
        identity_view = self.identity_view(identity)
        prior_binding = self.human_response_binding_for_state(
            identity, before
        )
        publication_gap = (
            identity_view["actor"] == "needs-human"
            and identity_view["leaf"] == "reviews"
            and prior_binding is None
            and edge["production_problem"].startswith(
                "immutable review binding changed outside"
            )
        )
        if publication_gap:
            return None
        return edge["production_problem"]

    def persisted_occurrence_problem(
        self,
        identity: tuple,
        old_state: ActionState,
        new_state: ActionState | None,
    ) -> tuple[str | None, str, list[dict], list[dict]]:
        """Trace the admitted occurrence from each implicated tip to C."""
        assert self.graph is not None

        C_states = self.states(self.graph.C, identity)
        if len(C_states) != 1:
            return (
                f"C carries exact identity multiplicity {len(C_states)}",
                "persisted-C-multiplicity",
                [],
                [],
            )
        proofs = []
        if not self.damage.skip_old_side_continuity:
            proofs.append(self.carry_proof(identity, self.fixture.O))
        if (
            new_state is not None
            and not self.damage.skip_persisted_candidate_continuity
        ):
            proofs.append(self.carry_proof(identity, self.fixture.N))
        ordered_edges = self.stable_edges(
            edge for proof in proofs for edge in proof["edges"]
        )
        failed_proof = next(
            (proof for proof in proofs if proof["reason"] is not None), None
        )
        if failed_proof is not None:
            reason = failed_proof["reason"]
            if failed_proof["outside_collisions"]:
                code = "persisted-outside-C-collision"
            elif failed_proof["absent_c_parents"]:
                code = "persisted-delete-recreate"
            elif "identity collision" in reason:
                code = "persisted-parent-multiplicity"
            elif "multiplicity" in reason:
                code = "persisted-intermediate-multiplicity"
            elif "no C-rooted carrying parent" in reason:
                code = "persisted-delete-recreate"
            elif "incompatible" in reason:
                code = "persisted-merge-carrier-conflict"
            elif "no carrying edge" in reason:
                code = "persisted-invalid-mutation"
            else:
                code = "persisted-upstream-discontinuity"
            return reason, code, ordered_edges, proofs
        C_state = C_states[0]
        old_anchor_regression = (
            RECONCILE.queue_parent_state_regression_problem(
                C_state.text, old_state.text
            )
        )
        old_anchor_binding = self.binding_subset_problem(
            identity, C_state, old_state
        )
        if (
            not self.damage.skip_old_side_continuity
            and (old_anchor_regression or old_anchor_binding)
        ):
            return (
                old_anchor_binding or old_anchor_regression,
                "persisted-old-endpoint-regression",
                ordered_edges,
                proofs,
            )
        if new_state is None or self.damage.skip_persisted_candidate_continuity:
            return (
                None,
                "persisted-old-C-rooted-continuity",
                ordered_edges,
                proofs,
            )
        endpoint_regression = RECONCILE.queue_parent_state_regression_problem(
            old_state.text, new_state.text
        )
        endpoint_binding = self.binding_subset_problem(
            identity, old_state, new_state
        )
        if endpoint_regression or endpoint_binding:
            return (
                endpoint_binding or endpoint_regression,
                "persisted-endpoint-regression",
                ordered_edges,
                proofs,
            )
        return None, "persisted-C-rooted-continuity", ordered_edges, proofs

    def supplier_base_events(self, identity: tuple) -> list[Event]:
        """Build nested supplier events while preserving original authority."""
        assert self.graph is not None
        raw_direct = self.raw_direct_events(identity)
        sources = [event for event in raw_direct if event.status == "valid"]
        observed_sources = [
            event for event in raw_direct if event.causal_roots
        ]
        results = []
        for child in self.graph.order:
            if (
                child not in self.graph.candidate_nodes
                or self.states(child, identity)
            ):
                continue
            carrying, absent, neutral, duplicate = self.parent_roles(
                identity, child
            )
            if not carrying or not absent:
                continue
            propagation = [
                {
                    "parent": parent,
                    "child": child,
                    "path": self.states(parent, identity)[0].path,
                    "role": "propagation-only",
                }
                for parent in carrying
            ]
            if duplicate:
                result = Event(
                    "ambiguous",
                    "supplier",
                    child,
                    [],
                    propagation,
                    neutral,
                    absent,
                    "supplier-parent-multiplicity",
                    "a supplier merge parent has duplicate identities",
                )
                result = self.attach_causal_metadata(
                    result, [self.synthetic_causal_root(result)]
                )
                observed_sources.append(result)
                results.append(result)
                continue
            carry_proofs = [
                self.carry_proof(identity, parent) for parent in carrying
            ]
            carry_problem = next(
                (proof["reason"] for proof in carry_proofs if proof["reason"]),
                None,
            )
            per_absent: list[list[Event]] = []
            for absent_parent in absent:
                traceable = [
                    source
                    for source in observed_sources
                    if (
                        source.child is not None
                        and self.absence_problem(
                            identity, source.child, absent_parent
                        )
                        is None
                    )
                ]
                closest_sources = [
                    source
                    for source in traceable
                    if not any(
                        source.child != other.child
                        and source.child in self.graph.ancestors(other.child)
                        for other in traceable
                    )
                ]
                per_absent.append(closest_sources)
            per_absent_root_keys = [
                {
                    self.causal_root_key(root)
                    for source in candidates
                    for root in source.causal_roots
                }
                for candidates in per_absent
            ]
            common = (
                set.intersection(
                    *per_absent_root_keys
                )
                if per_absent_root_keys
                else set()
            )
            ordered_sources = {}
            ordered_roots = {}
            for candidates in per_absent:
                for source in candidates:
                    ordered_sources.setdefault(
                        self.causal_source_key(source), source
                    )
                    for root in source.causal_roots:
                        ordered_roots.setdefault(
                            self.causal_root_key(root), root
                        )
            participating = list(ordered_sources.values())
            causal_roots = list(ordered_roots.values())
            unique_authorizing = bool(
                len(causal_roots) == 1
                and len(common) == 1
                and next(iter(common)) in ordered_roots
                and causal_roots[0]["status"] == "valid"
                and participating
                and all(
                    source.status == "valid" and source in sources
                    for source in participating
                )
            )
            borrowed_event = None
            if (
                not unique_authorizing
                and self.damage.allow_supplier_borrow
            ):
                borrowed = [
                    self.authority_edge(identity, parent, child)
                    for parent in carrying
                ]
                if any(edge["problem"] is None for edge in borrowed):
                    borrowed_event = Event(
                        "valid",
                        "damaged-borrow",
                        child,
                        borrowed,
                        propagation,
                        neutral,
                        absent,
                        "damaged-propagation-borrow",
                        "DAMAGED: propagation borrowed lifecycle authority",
                    )
                    borrowed_event = self.attach_causal_metadata(
                        borrowed_event,
                        self.direct_causal_roots(borrowed_event),
                    )
                    key = self.causal_root_key(
                        borrowed_event.causal_roots[0]
                    )
                    common = {key}
                    participating = [borrowed_event]
                    causal_roots = borrowed_event.causal_roots
                    unique_authorizing = True
            authority_edges = self.stable_edges(
                edge
                for source in participating
                for edge in source.authority_edges
            )
            propagation_edges = self.stable_edges(
                [
                    edge
                    for source in participating
                    for edge in source.propagation_edges
                ]
                + propagation
            )
            accumulated_neutral = self.stable_oids(
                [
                    parent
                    for source in participating
                    for parent in source.neutral_parents
                ]
                + neutral
                + [
                    parent
                    for proof in carry_proofs
                    for parent in proof["outside_neutral"]
                ]
            )
            accumulated_absent = self.stable_oids(
                [
                    parent
                    for source in participating
                    for parent in source.absent_parents
                ]
                + absent
            )
            prior_records = self.stable_reason_records(
                record
                for source in participating
                for record in source.reason_records
            )
            inherited_support_checks = self.stable_support_checks(
                check
                for source in participating
                for check in source.support_checks
            )
            current_support_checks: list[dict] = []
            support_problem = None
            if unique_authorizing and borrowed_event is None:
                current_support_checks, support_problem = (
                    self.supplier_support_checks(
                        identity, authority_edges, absent, child
                    )
                )
            if not participating:
                result = Event(
                    "invalid",
                    "supplier",
                    child,
                    [],
                    propagation,
                    neutral,
                    absent,
                    "competing-or-missing-supplier",
                    "no causal supplier source reaches every absent parent",
                )
                result = self.attach_causal_metadata(
                    result, [self.synthetic_causal_root(result)]
                )
                observed_sources.append(result)
            elif len(causal_roots) != 1 or len(common) != 1:
                result = Event(
                    "ambiguous",
                    "supplier",
                    child,
                    authority_edges,
                    propagation_edges,
                    accumulated_neutral,
                    accumulated_absent,
                    "competing-causal-suppliers",
                    (
                        f"{len(causal_roots)} canonical roots compete at "
                        f"adoption {child}: "
                        + "; ".join(
                            f"{source.reason_code}@{source.child}: "
                            f"{source.reason}"
                            for source in participating
                        )
                    ),
                )
                result = self.attach_causal_metadata(
                    result, causal_roots, prior_records
                )
                observed_sources.append(result)
            elif carry_problem:
                source_lineage = "; ".join(
                    f"{source.reason_code}@{source.child}: {source.reason}"
                    for source in participating
                )
                result = Event(
                    "invalid",
                    "supplier",
                    child,
                    authority_edges,
                    propagation_edges,
                    accumulated_neutral,
                    accumulated_absent,
                    "invalid-supplier-carrier",
                    f"{carry_problem}; causal sources: {source_lineage}",
                )
                result = self.attach_causal_metadata(
                    result,
                    self.retag_roots(causal_roots, "invalid"),
                    prior_records,
                )
                observed_sources.append(result)
            else:
                root_status = causal_roots[0]["status"]
                source_lineage = "; ".join(
                    f"{source.reason_code}@{source.child}: {source.reason}"
                    for source in participating
                )
                if root_status == "invalid":
                    result = Event(
                        "invalid",
                        "supplier",
                        child,
                        authority_edges,
                        propagation_edges,
                        accumulated_neutral,
                        accumulated_absent,
                        "upstream-invalid-supplier",
                        (
                            f"upstream invalid root via {source_lineage}; "
                            f"invalid "
                            f"supplier ancestry adopted at {child}"
                        ),
                    )
                    result = self.attach_causal_metadata(
                        result, causal_roots, prior_records
                    )
                    observed_sources.append(result)
                elif not unique_authorizing:
                    result = Event(
                        "ambiguous",
                        "supplier",
                        child,
                        authority_edges,
                        propagation_edges,
                        accumulated_neutral,
                        accumulated_absent,
                        "upstream-ambiguous-supplier",
                        (
                            f"upstream causal source via {source_lineage}; "
                            f"ambiguous supplier ancestry "
                            f"adopted at {child}"
                        ),
                    )
                    result = self.attach_causal_metadata(
                        result,
                        self.retag_roots(causal_roots, "ambiguous"),
                        prior_records,
                    )
                    observed_sources.append(result)
                else:
                    if support_problem:
                        result = Event(
                            "invalid",
                            "supplier",
                            child,
                            authority_edges,
                            propagation_edges,
                            accumulated_neutral,
                            accumulated_absent,
                            "supplier-support-certificate-invalid",
                            support_problem,
                        )
                        result = self.attach_causal_metadata(
                            result,
                            self.retag_roots(causal_roots, "invalid"),
                            prior_records,
                        )
                        observed_sources.append(result)
                    else:
                        binding_problem = (
                            self.supplier_carrier_human_binding_problem(
                                identity,
                                authority_edges,
                                propagation_edges,
                            )
                        )
                        conflict = binding_problem
                        if conflict:
                            result = Event(
                                "invalid",
                                "supplier",
                                child,
                                authority_edges,
                                propagation_edges,
                                accumulated_neutral,
                                accumulated_absent,
                                "old-tip-human-binding-conflict",
                                conflict,
                            )
                            result = self.attach_causal_metadata(
                                result,
                                self.retag_roots(
                                    causal_roots, "invalid"
                                ),
                                prior_records,
                            )
                            observed_sources.append(result)
                        else:
                            result = Event(
                                "valid",
                                "supplier",
                                child,
                                authority_edges,
                                propagation_edges,
                                accumulated_neutral,
                                accumulated_absent,
                                (
                                    "damaged-propagation-borrow"
                                    if borrowed_event
                                    else "valid-supplier-authority"
                                ),
                                (
                                    "DAMAGED: propagation borrowed lifecycle "
                                    "authority"
                                    if borrowed_event
                                    else (
                                        "one prior real deletion event supplies "
                                        "all absent parents; carrying edges only "
                                        "propagate and copy its support projection"
                                    )
                                ),
                            )
                            result = self.attach_causal_metadata(
                                result, causal_roots, prior_records
                            )
                            sources.append(result)
                            observed_sources.append(result)
            result.support_checks = self.stable_support_checks(
                [*inherited_support_checks, *current_support_checks]
            )
            result.carry_proofs = carry_proofs
            results.append(result)
        return results

    def supplier_events(self, identity: tuple) -> list[Event]:
        results = []
        for event in self.supplier_base_events(identity):
            post = (
                self.absence_problem(
                    identity, event.child, self.fixture.N
                )
                if (
                    event.status == "valid"
                    and event.child
                    and self.damage.enforce_post_event_absence
                )
                else None
            )
            if post:
                prior = event.reason_records
                event = dataclasses.replace(
                    event,
                    status="invalid",
                    reason_code="post-supplier-reintroduction",
                    reason="post-adoption absence is not continuous: " + post,
                )
                event = self.attach_causal_metadata(
                    event,
                    self.retag_roots(event.causal_roots, "invalid"),
                    prior,
                )
            results.append(event)
        return results

    def has_reintroduction(
        self, identity: tuple, event: Event
    ) -> bool:
        assert self.graph is not None
        marked_post_event = any(
            record["reason_code"]
            in {
                "post-event-reintroduction",
                "post-supplier-reintroduction",
            }
            for record in (
                event.reason_records
                or [
                    {
                        "reason_code": event.reason_code,
                        "reason": event.reason,
                    }
                ]
            )
        )
        return bool(
            marked_post_event
            and event.child is not None
            and any(
                commit != event.child and self.states(commit, identity)
                for commit in self.graph.ordered(
                    self.graph.between(event.child, self.fixture.N)
                )
            )
        )

    def final_absence_participants(
        self, identity: tuple, events: list[Event]
    ) -> list[Event]:
        """Find every causal event that reaches the fixed N frontier."""
        assert self.graph is not None
        boundary = self.fixture.N
        continuous = [
            event
            for event in events
            if (
                event.child is not None
                and self.absence_problem(
                    identity, event.child, boundary
                )
                is None
            )
        ]
        if not continuous:
            return []
        participating = list(continuous)
        for event in events:
            if event in participating or not self.has_reintroduction(
                identity, event
            ):
                continue
            if any(
                event.child is not None
                and terminal.child is not None
                and event.child in self.graph.ancestors(terminal.child)
                for terminal in continuous
            ):
                participating.append(event)
        order = {
            commit: index for index, commit in enumerate(self.graph.order)
        }
        return sorted(
            participating,
            key=lambda event: (
                order.get(event.child, len(order)),
                0 if event.mode == "direct" else 1,
                event.reason_code,
            ),
        )

    def aggregate_blocking_history(
        self, identity: tuple, events: list[Event]
    ) -> Event:
        """Merge one root's wrappers or block competing causal roots."""
        assert events
        authority_edges = self.stable_edges(
            edge for event in events for edge in event.authority_edges
        )
        propagation_edges = self.stable_edges(
            edge for event in events for edge in event.propagation_edges
        )
        neutral_parents = self.stable_oids(
            parent for event in events for parent in event.neutral_parents
        )
        absent_parents = self.stable_oids(
            parent for event in events for parent in event.absent_parents
        )
        causal_roots = self.stable_roots(
            root for event in events for root in event.causal_roots
        )
        prior_records = self.stable_reason_records(
            record for event in events for record in event.reason_records
        )
        support_checks = self.stable_support_checks(
            check for event in events for check in event.support_checks
        )
        carry_proofs = list(
            {
                proof["tip"]: proof
                for event in events
                for proof in event.carry_proofs
            }.values()
        )
        reintroduced = any(
            self.has_reintroduction(identity, event) for event in events
        )
        root_roles_compete = len(causal_roots) != 1
        unique_valid_root = bool(
            len(causal_roots) == 1
            and causal_roots[0]["status"] == "valid"
            and all(event.status == "valid" for event in events)
        )
        ambiguous = not unique_valid_root and (
            reintroduced
            or root_roles_compete
            or any(event.status == "ambiguous" for event in events)
            or any(event.status == "valid" for event in events)
            or len({event.status for event in events}) != 1
        )
        status = (
            "valid"
            if unique_valid_root
            else ("ambiguous" if ambiguous else events[-1].status)
        )
        if unique_valid_root:
            reason_code = "valid-shared-causal-root"
            reason = (
                "all final-absence wrappers share exactly one canonical "
                "valid root: "
            )
        elif reintroduced:
            reason_code = "reintroduced-competing-occurrences"
            reason = "final absence has multiple causal occurrences: "
        else:
            reason_code = "competing-final-absence-roots"
            reason = "final absence has competing causal roots: "
        reason += "; ".join(
            f"{event.reason_code}@{event.child}: {event.reason}"
            for event in events
        )
        modes = {event.mode for event in events}
        result = Event(
            status,
            (
                "ambiguous"
                if status == "ambiguous" or len(modes) != 1
                else events[-1].mode
            ),
            events[-1].child,
            authority_edges,
            propagation_edges,
            neutral_parents,
            absent_parents,
            reason_code,
            reason,
            support_checks=support_checks,
            carry_proofs=carry_proofs,
        )
        return self.attach_causal_metadata(
            result, causal_roots, prior_records
        )

    def select_event(self, identity: tuple) -> Event:
        events = self.direct_events(identity) + self.supplier_events(identity)
        valid = [event for event in events if event.status == "valid"]
        if (
            self.damage.sole_valid_ignores_competitors
            or not self.damage.enforce_post_event_absence
        ) and len(valid) == 1:
            return valid[0]
        participants = self.final_absence_participants(identity, events)
        if participants:
            chosen = (
                self.aggregate_blocking_history(identity, participants)
                if len(participants) > 1
                else participants[0]
            )
            if chosen.status == "valid" and not (
                len(chosen.causal_roots) == 1
                and chosen.causal_roots[0]["status"] == "valid"
            ):
                chosen = self.aggregate_blocking_history(
                    identity, [chosen]
                )
            authority = {
                (edge["parent"], edge["child"])
                for edge in chosen.authority_edges
            }
            propagation = {
                (edge["parent"], edge["child"])
                for edge in chosen.propagation_edges
            }
            if (
                chosen.status == "valid"
                and authority.intersection(propagation)
                and not self.damage.allow_supplier_borrow
            ):
                return dataclasses.replace(
                    chosen,
                    status="ambiguous",
                    reason_code="mode-edge-overlap",
                    reason="authority and propagation edge sets overlap",
                )
            return chosen
        if len(valid) == 1:
            chosen = valid[0]
            authority = {
                (edge["parent"], edge["child"])
                for edge in chosen.authority_edges
            }
            propagation = {
                (edge["parent"], edge["child"])
                for edge in chosen.propagation_edges
            }
            if (
                authority.intersection(propagation)
                and not self.damage.allow_supplier_borrow
            ):
                return dataclasses.replace(
                    chosen,
                    status="ambiguous",
                    reason_code="mode-edge-overlap",
                    reason=(
                        "authority and propagation edge sets overlap"
                    ),
                )
            return chosen
        if len(valid) > 1:
            result = Event(
                "ambiguous",
                "ambiguous",
                None,
                [
                    edge
                    for event in valid
                    for edge in event.authority_edges
                ],
                [
                    edge
                    for event in valid
                    for edge in event.propagation_edges
                ],
                [],
                [],
                "competing-events",
                f"{len(valid)} causal events compete",
            )
            return self.attach_causal_metadata(
                result,
                (
                    root
                    for event in valid
                    for root in event.causal_roots
                ),
                (
                    record
                    for event in valid
                    for record in event.reason_records
                ),
            )
        if events:
            ambiguous = [
                event for event in events if event.status == "ambiguous"
            ]
            chosen = (ambiguous or events)[-1]
            return chosen
        return Event(
            "none",
            "none",
            None,
            [],
            [],
            [],
            [],
            "no-event",
            "no candidate-side event resolves the C-rooted occurrence",
        )

    def action_base(
        self,
        identity: tuple,
        old_states: tuple[ActionState, ...],
    ) -> dict:
        assert self.graph is not None
        C_states = self.states(self.graph.C, identity)
        N_states = self.states(self.fixture.N, identity)
        return {
            "identity": self.identity_view(identity),
            "multiplicity": {
                "C": len(C_states),
                "O": len(
                    old_states[:1]
                    if self.damage.collapse_multiplicity
                    else old_states
                ),
                "N": len(N_states),
            },
            "paths": {
                "C": [state.path for state in C_states],
                "O": [state.path for state in old_states],
                "N": [state.path for state in N_states],
            },
            "authority_edges": [],
            "propagation_edges": [],
            "mutation_edges": [],
            "support_checks": [],
            "carry_proofs": [],
            "neutral_parents": [],
            "absent_parents": [],
            "causal_roots": [],
            "reason_records": [],
            "origin_strategy": self.origin_strategy,
            "origin_proofs": [],
            "birth_witness_match": None,
            "endpoint_checks": {
                "binding": None,
                "frozen": None,
                "regression": None,
            },
            "event_mode": "none",
            "reason_code": "none",
        }

    def classify_old_action(
        self,
        identity: tuple,
        old_states: tuple[ActionState, ...],
    ) -> dict:
        assert self.graph is not None
        base = self.action_base(identity, old_states)
        C_states = self.states(self.graph.C, identity)
        N_states = self.states(self.fixture.N, identity)
        if N_states:
            if len(N_states) != len(old_states) or len(N_states) != 1:
                return {
                    **base,
                    "status": "ambiguous",
                    "finding": True,
                    "authoring_lineage": "multiplicity-changed",
                    "reason_code": "endpoint-multiplicity-change",
                    "reason": (
                        "persisted production identity does not have one "
                        "unambiguous O-to-N occurrence"
                    ),
                }
            if len(C_states) == 0:
                (
                    origin_problem,
                    origin_code,
                    origin_proofs,
                    endpoint_checks,
                    witness_match,
                ) = self.equivalent_origin_problem(
                    identity, old_states[0], N_states[0]
                )
                mutation_edges = self.stable_edges(
                    edge
                    for proof in origin_proofs
                    for edge in proof["edges"]
                )
                if origin_problem is not None:
                    ambiguous_codes = {
                        "origin-arm-multiplicity",
                        "origin-birth-multiplicity",
                        "origin-endpoint-multiplicity",
                        "origin-missing-birth",
                        "origin-outside-C-collision",
                        "origin-post-birth-absence",
                        "origin-birth-witness-mismatch",
                    }
                    return {
                        **base,
                        "status": (
                            "ambiguous"
                            if origin_code in ambiguous_codes
                            else "invalid"
                        ),
                        "finding": True,
                        "authoring_lineage": (
                            "non-equivalent-live-incarnation"
                        ),
                        "birth_witness_match": witness_match,
                        "endpoint_checks": endpoint_checks,
                        "event_mode": f"origin-{self.origin_strategy}",
                        "mutation_edges": mutation_edges,
                        "origin_proofs": origin_proofs,
                        "reason_code": origin_code,
                        "reason": (
                            "the absent-at-C identity does not prove one "
                            "equivalent valid live incarnation on each arm: "
                            f"{origin_problem}"
                        ),
                    }
                return {
                    **base,
                    "status": "valid",
                    "finding": False,
                    "authoring_lineage": (
                        "equivalent-valid-live-incarnation"
                    ),
                    "birth_witness_match": witness_match,
                    "endpoint_checks": endpoint_checks,
                    "event_mode": f"origin-{self.origin_strategy}",
                    "mutation_edges": mutation_edges,
                    "origin_proofs": origin_proofs,
                    "reason_code": origin_code,
                    "reason": (
                        f"Strategy {self.origin_strategy} proves one legal "
                        "arm-local birth and uninterrupted valid carriage "
                        "to each endpoint; this claims equivalent live "
                        "incarnations, not intent or replay provenance"
                    ),
                }
            if self.damage.skip_preserved_state_validation:
                state_problem = None
                state_code = "DAMAGED-skipped"
                mutation_edges = []
                persisted_proofs = []
            else:
                (
                    state_problem,
                    state_code,
                    mutation_edges,
                    persisted_proofs,
                ) = (
                    self.persisted_occurrence_problem(
                        identity, old_states[0], N_states[0]
                    )
                )
            if state_problem:
                status = (
                    "ambiguous"
                    if state_code
                    in {
                        "persisted-C-multiplicity",
                        "persisted-intermediate-multiplicity",
                        "persisted-parent-multiplicity",
                        "persisted-delete-recreate",
                        "persisted-upstream-discontinuity",
                        "persisted-outside-C-collision",
                    }
                    else "invalid"
                )
                return {
                    **base,
                    "status": status,
                    "finding": True,
                    "authoring_lineage": "persisted-state-regression",
                    "mutation_edges": mutation_edges,
                    "carry_proofs": persisted_proofs,
                    "reason_code": state_code,
                    "reason": (
                        "the production identity remains live but its one "
                        "C-rooted occurrence is not continuously valid: "
                        f"{state_problem}"
                    ),
                }
            return {
                **base,
                "status": "none",
                "finding": False,
                "authoring_lineage": "preserved",
                "mutation_edges": mutation_edges,
                "carry_proofs": persisted_proofs,
                "reason_code": "identity-preserved",
                "reason": (
                    "the exact production identity remains live through "
                    "continuous C-rooted production-valid mutations"
                ),
            }
        effective_old = (
            old_states[:1]
            if self.damage.collapse_multiplicity
            else old_states
        )
        if len(effective_old) != 1:
            return {
                **base,
                "status": "ambiguous",
                "finding": True,
                "authoring_lineage": "old-tip-duplicate",
                "reason_code": "old-tip-multiplicity",
                "reason": (
                    f"old tip carries multiplicity {len(effective_old)}"
                ),
            }
        if len(C_states) == 0:
            return {
                **base,
                "status": "none",
                "finding": True,
                "authoring_lineage": "old-tip-authored",
                "reason_code": "not-present-at-C",
                "reason": "the disappeared identity was not present at C",
            }
        if len(C_states) != 1:
            return {
                **base,
                "status": "ambiguous",
                "finding": True,
                "authoring_lineage": "duplicate-at-C",
                "reason_code": "C-multiplicity",
                "reason": (
                    f"C carries exact identity multiplicity {len(C_states)}"
                ),
            }
        (
            old_problem,
            old_code,
            old_mutation_edges,
            old_carry_proofs,
        ) = (
            self.persisted_occurrence_problem(
                identity, effective_old[0], None
            )
        )
        if old_problem:
            status = (
                "ambiguous"
                if old_code
                in {
                    "persisted-C-multiplicity",
                    "persisted-intermediate-multiplicity",
                    "persisted-parent-multiplicity",
                    "persisted-delete-recreate",
                    "persisted-upstream-discontinuity",
                    "persisted-outside-C-collision",
                }
                else "invalid"
            )
            return {
                **base,
                "status": status,
                "finding": True,
                "authoring_lineage": "old-side-discontinuous",
                "mutation_edges": old_mutation_edges,
                "carry_proofs": old_carry_proofs,
                "reason_code": old_code,
                "reason": (
                    "the old tip identity does not retain one continuously "
                    "valid C-rooted occurrence: "
                    f"{old_problem}"
                ),
            }
        if self.damage.reopen_pre_c_genealogy:
            assert self.objects is not None
            parents = self.objects.commit_parents(self.graph.C)
            carrying = [
                parent for parent in parents if self.states(parent, identity)
            ]
            if len(carrying) > 1:
                return {
                    **base,
                    "status": "ambiguous",
                    "finding": True,
                    "authoring_lineage": "DAMAGED-pre-C-genealogy",
                    "reason_code": "damaged-pre-C-genealogy",
                    "reason": (
                        "DAMAGED: reopened genealogy before admitted C"
                    ),
                }
        event = self.select_event(identity)
        return {
            **base,
            "status": event.status,
            "finding": event.status != "valid",
            "authoring_lineage": "inherited-from-C",
            "event_mode": event.mode,
            "authority_edges": event.authority_edges,
            "propagation_edges": event.propagation_edges,
            "mutation_edges": old_mutation_edges,
            "support_checks": event.support_checks,
            "carry_proofs": old_carry_proofs + event.carry_proofs,
            "neutral_parents": event.neutral_parents,
            "absent_parents": event.absent_parents,
            "causal_roots": event.causal_roots,
            "reason_records": event.reason_records,
            "event_child": event.child,
            "reason_code": event.reason_code,
            "reason": event.reason,
        }

    def classify_candidate_only(
        self, identity: tuple
    ) -> dict | None:
        """Retain normal production findings for non-old candidate actions."""
        assert self.graph is not None
        if self.states(self.fixture.N, identity):
            return None
        candidate_states = [
            commit
            for commit in self.graph.ordered_identity_nodes()
            if self.states(commit, identity)
        ]
        if not candidate_states:
            return None
        edges = []
        for child in self.graph.order:
            if child not in self.graph.candidate_nodes:
                continue
            if self.states(child, identity):
                continue
            for parent in self.graph.parents[child]:
                if len(self.states(parent, identity)) == 1:
                    edges.append(
                        self.authority_edge(identity, parent, child)
                    )
        invalid = [edge for edge in edges if edge["problem"]]
        if invalid or not edges:
            base = self.action_base(
                identity,
                self.states(candidate_states[-1], identity),
            )
            return {
                **base,
                "status": "invalid" if invalid else "none",
                "finding": True,
                "authoring_lineage": "candidate-other-parent",
                "event_mode": "direct",
                "authority_edges": edges,
                "reason_code": "candidate-side-unresolved-deletion",
                "reason": (
                    "; ".join(
                        edge["problem"] for edge in invalid
                    )
                    if invalid
                    else "candidate-side action has no authority edge"
                ),
            }
        return None

    def run(self) -> dict:
        fixture = self.fixture
        session = self.session
        base = {
            "scenario": fixture.scenario,
            "C": None,
            "O": fixture.O,
            "N": fixture.N,
            "expected_result": fixture.expected,
            "input_contract": {
                "schema": "restack-provenance-input/v2",
                "authoritative_endpoints": ["O", "N"],
                "origin_strategy": self.origin_strategy,
            },
        }
        objects = None
        published_result = None
        try:
            objects = session.create_object_database(
                damage=self.damage,
                stable_git_diagnostics=(
                    not self.damage.ambient_git_diagnostics
                ),
            )
            self.objects = objects
            self.graph = Graph(
                session,
                fixture.O,
                fixture.N,
                objects,
                reopen_outside_c_boundary_ancestry=(
                    self.damage.reopen_outside_c_boundary_ancestry
                ),
                buffered_graph_output=self.damage.buffered_graph_output,
                stable_git_diagnostics=(
                    not self.damage.ambient_git_diagnostics
                ),
            )
            base["C"] = self.graph.C
            if self.graph is not None:
                if fixture.expected_C:
                    base["derived_C_matches_fixture"] = (
                        self.graph.C == fixture.expected_C
                    )
                budget_result = self.budget_result(base)
                if budget_result is not None:
                    published_result = budget_result
                    return published_result
                if self.graph.C == fixture.O:
                    published_result = {
                        **base,
                        "audit_exit": 0,
                        "classification": "no-finding",
                        "evidence_verdict": {
                            "status": "none",
                            "reason": (
                                "O is the unique merge base of O and N; "
                                "the update is a fast-forward, not a restack"
                            ),
                        },
                        "event_mode": "none",
                        "authority_edges": [],
                        "propagation_edges": [],
                        "mutation_edges": [],
                        "support_checks": [],
                        "carry_proofs": [],
                        "actions": [],
                        "metrics": self.metrics.as_dict(),
                        "details": fixture.details,
                    }
                    return published_result
                old_snapshot = objects.snapshot(fixture.O)
                actions = [
                    self.classify_old_action(identity, states)
                    for identity, states in sorted(
                        old_snapshot.items(), key=lambda item: repr(item[0])
                    )
                ]
                seen = set(old_snapshot)
                candidate_identities = set()
                for commit in self.graph.ordered_identity_nodes():
                    candidate_identities.update(objects.snapshot(commit))
                for identity in sorted(
                    candidate_identities - seen, key=repr
                ):
                    action = self.classify_candidate_only(identity)
                    if action is not None:
                        actions.append(action)
                findings = [
                    action for action in actions if action["finding"]
                ]
                classification = (
                    "blocking-finding" if findings else "no-finding"
                )
                if findings:
                    for preferred in ("ambiguous", "invalid", "none"):
                        if preferred in [
                            action["status"] for action in findings
                        ]:
                            evidence_status = preferred
                            break
                elif any(action["status"] == "valid" for action in actions):
                    evidence_status = "valid"
                else:
                    evidence_status = "none"
                modes = sorted(
                    {
                        action["event_mode"]
                        for action in actions
                        if action["event_mode"] != "none"
                    }
                )
                result = {
                    **base,
                    "audit_exit": 1 if findings else 0,
                    "classification": classification,
                    "evidence_verdict": {
                        "status": evidence_status,
                        "reason": "; ".join(
                            action["reason"]
                            for action in (findings or actions)
                        ),
                    },
                    "event_mode": (
                        modes[0]
                        if len(modes) == 1
                        else ("mixed" if modes else "none")
                    ),
                    "authority_edges": [
                        edge
                        for action in actions
                        for edge in action["authority_edges"]
                    ],
                    "propagation_edges": [
                        edge
                        for action in actions
                        for edge in action["propagation_edges"]
                    ],
                    "mutation_edges": [
                        edge
                        for action in actions
                        for edge in action["mutation_edges"]
                    ],
                    "support_checks": [
                        check
                        for action in actions
                        for check in action["support_checks"]
                    ],
                    "carry_proofs": [
                        proof
                        for action in actions
                        for proof in action["carry_proofs"]
                    ],
                    "actions": actions,
                    "metrics": self.metrics.as_dict(),
                    "details": fixture.details,
                }
                budget_result = self.budget_result(base)
                if budget_result is not None:
                    published_result = budget_result
                    return published_result
                published_result = result
                return published_result
        except BudgetExceeded as error:
            if error.C is not None:
                base["C"] = error.C
                if fixture.expected_C:
                    base["derived_C_matches_fixture"] = (
                        error.C == fixture.expected_C
                    )
            result = self.budget_result(base)
            if result is None:
                raise AssertionError(
                    "pre-charge budget exception lost its overflow"
                ) from error
            published_result = result
            return published_result
        except (
            Unreadable,
            RECONCILE.GitSnapshotError,
            OSError,
            ValueError,
            UnicodeError,
        ) as error:
            published_result = {
                **base,
                "audit_exit": 2,
                "classification": "unreadable",
                "evidence_verdict": {
                    "status": "unreadable",
                    "reason": str(error),
                },
                "event_mode": "none",
                "authority_edges": [],
                "propagation_edges": [],
                "mutation_edges": [],
                "support_checks": [],
                "carry_proofs": [],
                "actions": [],
                "metrics": self.metrics.as_dict(),
                "details": fixture.details,
            }
            return published_result
        finally:
            cleanup_failures: list[BaseException] = []
            if objects is not None:
                try:
                    session.close_object_database()
                except BaseException as error:
                    cleanup_failures.append(error)
            cleanup_error = (
                cleanup_failures[0] if cleanup_failures else None
            )
            if published_result is not None:
                if cleanup_error is not None:
                    if is_cancellation(cleanup_error):
                        raise cleanup_error
                    published_result.clear()
                    published_result.update(
                        {
                            **base,
                            "audit_exit": 2,
                            "classification": "unreadable",
                            "evidence_verdict": {
                                "status": "unreadable",
                                "reason": (
                                    "object database cleanup failed: "
                                    f"{cleanup_error}"
                                ),
                            },
                            "event_mode": "none",
                            "authority_edges": [],
                            "propagation_edges": [],
                            "mutation_edges": [],
                            "support_checks": [],
                            "carry_proofs": [],
                            "actions": [],
                            "details": fixture.details,
                        }
                    )
                # This is the only authoritative metrics publication.  It is
                # deliberately after descriptor closure and proven child reap.
                published_result["metrics"] = self.metrics.as_dict()
            elif cleanup_error is not None:
                raise cleanup_error


def _run_classifier(fixture: _Fixture, damage: Damage | None = None) -> dict:
    """Run a fixture in one explicit, fully cleaned repository session."""
    session = RepositorySession(
        fixture.repo.root,
        git_runner=_trusted_git_runner(),
        stable_git_diagnostics=(
            not (damage or Damage()).ambient_git_diagnostics
        ),
    )
    metrics = session.metrics
    result = None
    body_error = None
    cleanup_error = None
    session.open()
    try:
        result = _Classifier(fixture, damage, session=session).run()
    except BaseException as error:
        body_error = error
    try:
        session.close()
    except BaseException as error:
        cleanup_error = error
    cancellation = next(
        (
            error
            for error in (body_error, cleanup_error)
            if error is not None and is_cancellation(error)
        ),
        None,
    )
    if cancellation is not None:
        raise cancellation
    if body_error is not None:
        raise body_error
    if cleanup_error is not None:
        base = {
            key: value
            for key, value in (result or {}).items()
            if key
            in {
                "scenario",
                "C",
                "O",
                "N",
                "expected_result",
                "input_contract",
                "details",
            }
        }
        result = {
            **base,
            "audit_exit": 2,
            "classification": "unreadable",
            "evidence_verdict": {
                "status": "unreadable",
                "reason": (
                    "repository session cleanup failed: "
                    + cleanup_failure_text(cleanup_error)
                ),
            },
            "event_mode": "none",
            "authority_edges": [],
            "propagation_edges": [],
            "mutation_edges": [],
            "support_checks": [],
            "carry_proofs": [],
            "actions": [],
        }
    if result is not None:
        result["metrics"] = metrics.as_dict()
    return result


def queue_path(
    label: str,
    *,
    actor: str = "needs-agent",
    leaf: str = "requests",
    timing: str = "non-blocking",
):
    return f"message-queue/{actor}/{leaf}/{timing}-{label}.md"


def evidence_path(label: str):
    return f"docs/evidence-{label}.md"


def agent_text(
    label: str, status: str = "open", action: str | None = None
):
    return (
        f"# Preserve {label}\n\n"
        f"**Status:** {status}\n"
        "**Filed:** 2026-08-31\n"
        f"**Action:** {action or f'resolve {label}'}\n"
        f"**Full context:** `{evidence_path(label)}`\n"
        f"**Resolution evidence:** `{evidence_path(label)}`\n"
        "**If unanswered:** keep the action live\n"
    )


def human_text(label: str, status: str = "waiting", answer="______"):
    return (
        f"# Decide {label}\n\n"
        f"**Status:** {status}\n"
        "**Filed:** 2026-08-31\n"
        f"**Action:** decide {label}\n"
        f"**Full context:** `{evidence_path(label)}`\n"
        f"**Resolution evidence:** `{evidence_path(label)}`\n"
        "**If unanswered:** keep the decision live\n"
        f"**Your answer:** {answer}\n"
    )


def review_text(
    label: str,
    *,
    status: str = "waiting",
    response: str = "______",
    target: str,
    revision: str,
    reviewed_revision: str = "______",
    outcome: str = "pending",
):
    rendered_target = (
        target
        if _Classifier.explicit_review_pending(target)
        else f"`{target}`"
    )
    return (
        f"# Review {label}\n\n"
        f"**Status:** {status}\n"
        "**Filed:** 2026-08-31\n"
        f"**Action:** review {label}\n"
        f"**Full context:** `{evidence_path(label)}`\n"
        f"**Resolution evidence:** `{evidence_path(label)}`\n"
        "**If unanswered:** keep the review live\n"
        f"**Your review:** {response}\n"
        f"**Review target:** {rendered_target}\n"
        f"**Review revision:** {revision}\n"
        f"**Reviewed revision:** {reviewed_revision}\n"
        f"**Review outcome:** {outcome}\n"
    )


def review_revision(payload: str) -> str:
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def initialize(repo: GitRepository):
    repo.write("README.md", "# Disposable production-contract fixture\n")
    repo.write(
        "message-queue/AGENTS.md",
        "**Queue resolution schema:** v1\n",
    )


def add_agent(
    repo: GitRepository,
    label: str,
    *,
    path: str | None = None,
    text: str | None = None,
):
    path = path or queue_path(label)
    repo.write(evidence_path(label), f"# Evidence {label}: pending\n")
    repo.write(path, text or agent_text(label))
    return path


def add_human(repo: GitRepository, label: str):
    path = queue_path(label, actor="needs-human", leaf="decisions")
    repo.write(evidence_path(label), f"# Evidence {label}: pending\n")
    repo.write(path, human_text(label))
    return path


def add_review(
    repo: GitRepository,
    label: str,
    *,
    status: str,
    target: str,
    revision: str,
):
    path = queue_path(label, actor="needs-human", leaf="reviews")
    repo.write(evidence_path(label), f"# Evidence {label}: pending\n")
    repo.write(
        path,
        review_text(
            label,
            status=status,
            target=target,
            revision=revision,
        ),
    )
    return path


def claim(repo: GitRepository, paths: Iterable[str], message="claim action"):
    for path in paths:
        text = repo.read(path)
        text = text.replace(
            "**Status:** open", "**Status:** in-repair", 1
        )
        text = text.replace(
            "**Status:** waiting", "**Status:** folding", 1
        )
        repo.write(path, text)
    return repo.commit(message)


def answer(repo: GitRepository, path: str, value: str):
    repo.write(
        path,
        repo.read(path).replace(
            "**Your answer:** ______",
            f"**Your answer:** {value}",
            1,
        ),
    )
    return repo.commit(f"record human answer {value}")


def answer_review(repo: GitRepository, path: str, value: str):
    repo.write(
        path,
        repo.read(path).replace(
            "**Your review:** ______",
            f"**Your review:** {value}",
            1,
        ),
    )
    return repo.commit(f"record human review {value}")


def publish_review(
    repo: GitRepository, path: str, target: str, revision: str
):
    text = repo.read(path)
    text = text.replace(
        "**Status:** awaiting-artifact", "**Status:** waiting", 1
    )
    text = text.replace(
        "**Review target:** pending",
        f"**Review target:** `{target}`",
        1,
    )
    text = text.replace(
        "**Review revision:** pending",
        f"**Review revision:** {revision}",
        1,
    )
    repo.write(path, text)
    return repo.commit(f"publish review target {target}")


def fill_review_pending(
    repo: GitRepository,
    path: str,
    *,
    field: str,
    target: str,
    revision: str,
):
    text = repo.read(path)
    if field == "Review target":
        before = "**Review target:** pending"
        after = f"**Review target:** `{target}`"
    elif field == "Review revision":
        before = "**Review revision:** pending"
        after = f"**Review revision:** {revision}"
    else:
        raise ValueError(f"unsupported review pending field: {field}")
    if before not in text:
        raise RuntimeError(f"missing expected pending field: {before}")
    repo.write(path, text.replace(before, after, 1))
    return repo.commit(f"fill pending {field.lower()}")


def replace_review_binding(
    repo: GitRepository,
    path: str,
    *,
    field: str,
    old_value: str,
    target: str,
    revision: str,
):
    text = repo.read(path)
    if field == "Review target":
        before = f"**Review target:** {old_value}"
        after = f"**Review target:** `{target}`"
    elif field == "Review revision":
        before = f"**Review revision:** {old_value}"
        after = f"**Review revision:** {revision}"
    else:
        raise ValueError(f"unsupported review binding field: {field}")
    if before not in text:
        raise RuntimeError(f"missing expected review field: {before}")
    repo.write(path, text.replace(before, after, 1))
    return repo.commit(f"replace malformed {field.lower()}")


def claim_review(
    repo: GitRepository,
    path: str,
    *,
    outcome: str = "approved",
):
    text = repo.read(path)
    revision = RECONCILE.human_response_fields(text)["Review revision"]
    text = text.replace("**Status:** waiting", "**Status:** folding", 1)
    text = text.replace(
        "**Reviewed revision:** ______",
        f"**Reviewed revision:** {revision}",
        1,
    )
    text = text.replace(
        "**Review outcome:** pending",
        f"**Review outcome:** {outcome}",
        1,
    )
    repo.write(path, text)
    return repo.commit(f"bind human review as {outcome}")


def delete_with_evidence(
    repo: GitRepository,
    labeled_paths: Iterable[tuple[str, str]],
    message="resolve queue action",
):
    for label, path in labeled_paths:
        repo.write(
            evidence_path(label), f"# Evidence {label}: resolved\n"
        )
        repo.remove(path)
    return repo.commit(message)


def feature(repo: GitRepository, label: str):
    repo.write(f"features/{label}.md", f"# Feature {label}\n")
    return repo.commit(f"add feature {label}")


def ordinary_linear_fixture(
    root: Path, scenario: str, *, valid: bool
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = scenario.lower()
    path = add_agent(repo, label)
    C = repo.commit("create C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    if valid:
        claim(repo, (path,))
        candidate_landmark = delete_with_evidence(repo, ((label, path),))
    else:
        repo.remove(path)
        candidate_landmark = repo.commit("delete without authority")
    N = feature(repo, f"{label}-old")
    return _Fixture(
        scenario,
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding" if valid else "blocking-finding",
    )


def p3_old_loss(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    C = repo.commit("create action-free C")
    repo.branch("old", C)
    path = add_agent(repo, "p3")
    O = feature(repo, "p3-task")
    repo.branch("candidate", C)
    candidate_landmark = feature(repo, "p3-base")
    N = feature(repo, "p3-task")
    return _Fixture(
        "P3-genuine-old-loss",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"lost_path": path},
    )


def p4_pre_c_origins(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create pre-C root")
    text = agent_text("p4")
    path = queue_path("p4")
    repo.branch("origin-a", R)
    add_agent(repo, "p4", path=path, text=text)
    A = repo.commit("independently add p4 on A")
    repo.branch("origin-b", R)
    add_agent(repo, "p4", path=path, text=text)
    B = repo.commit("independently add p4 on B")
    tree = repo.oid(f"{A}^{{tree}}")
    C = repo.commit_tree(tree, "admit unique p4 at C", A, B)
    repo.branch("old", C)
    O = feature(repo, "p4-old")
    repo.branch("candidate", C)
    claim(repo, (path,))
    candidate_landmark = delete_with_evidence(repo, (("p4", path),))
    N = feature(repo, "p4-old")
    return _Fixture(
        "P4-pre-C-identical-origins",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {"pre_C_origins": [A, B], "pre_C_root": R},
    )


def p5_duplicate_at_c(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    text = agent_text("p5")
    first = add_agent(repo, "p5", path=queue_path("p5-a"), text=text)
    second = queue_path("p5-b")
    repo.write(second, text)
    C = repo.commit("create duplicate identity at C")
    repo.branch("old", C)
    O = feature(repo, "p5-old")
    repo.branch("candidate", C)
    claim(repo, (first, second))
    repo.write(evidence_path("p5"), "# Evidence p5: resolved\n")
    repo.remove(first)
    repo.remove(second)
    candidate_landmark = repo.commit("delete both duplicate paths")
    N = feature(repo, "p5-old")
    return _Fixture(
        "P5-duplicate-at-C",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
    )


def p6_old_recreate(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "p6-old")
    original = repo.read(path)
    C = repo.commit("create p6 at C")
    repo.branch("old", C)
    repo.remove(path)
    repo.commit("old side temporarily deletes p6")
    repo.write(path, original)
    repo.commit("old side recreates identical p6")
    O = feature(repo, "p6-old-task")
    repo.branch("candidate", C)
    claim(repo, (path,))
    candidate_landmark = delete_with_evidence(repo, (("p6-old", path),))
    N = feature(repo, "p6-old-task")
    return _Fixture(
        "P6a-old-delete-recreate",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
    )


def p6_candidate_recreate(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "p6-candidate")
    original = repo.read(path)
    C = repo.commit("create p6 candidate at C")
    repo.branch("old", C)
    O = feature(repo, "p6-candidate-old")
    repo.branch("candidate", C)
    claim(repo, (path,))
    delete_with_evidence(repo, (("p6-candidate", path),), "first deletion")
    repo.write(path, original)
    repo.commit("recreate byte-identical p6")
    claim(repo, (path,), "fresh claim after recreation")
    candidate_landmark = delete_with_evidence(
        repo, (("p6-candidate", path),), "second deletion"
    )
    N = feature(repo, "p6-candidate-old")
    return _Fixture(
        "P6b-candidate-delete-recreate",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
    )


def p7_payload_change(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "p7")
    original = repo.read(path)
    C = repo.commit("create p7 at C")
    repo.branch("old", C)
    changed = agent_text("p7", action="resolve changed payload")
    repo.write(path, changed)
    O = feature(repo, "p7-old")
    repo.branch("candidate", C)
    claim(repo, (path,))
    candidate_landmark = delete_with_evidence(repo, (("p7", path),))
    N = feature(repo, "p7-old")
    return _Fixture(
        "P7-immutable-payload-change",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "production_identity_equal": (
                RECONCILE.queue_action_identity(path, original)
                == RECONCILE.queue_action_identity(path, changed)
            )
        },
    )


def p8_timing_move(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    old_path = add_agent(
        repo,
        "p8",
        path=queue_path("p8-before", timing="future-blocking"),
    )
    new_path = queue_path("p8-after", timing="blocking")
    C = repo.commit("create p8 at C")
    repo.branch("old", C)
    repo.move(old_path, new_path)
    O = feature(repo, "p8-old")
    repo.branch("candidate", C)
    repo.move(old_path, new_path)
    candidate_landmark = repo.commit("perform one-to-one timing path move")
    N = feature(repo, "p8-old")
    before = agent_text("p8")
    details = {
        "production_identity_equal": (
            RECONCILE.queue_action_identity(old_path, before)
            == RECONCILE.queue_action_identity(new_path, before)
        ),
        "paired_payload_change_identity_equal": (
            RECONCILE.queue_action_identity(old_path, before)
            == RECONCILE.queue_action_identity(
                new_path,
                agent_text("p8", action="different immutable action"),
            )
        ),
    }
    return _Fixture(
        "P8-path-timing-move",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        details,
    )


def direct_merge_fixture(
    root: Path,
    scenario: str,
    *,
    parent_count: int,
    invalid_parent: int | None = None,
    neutral_parent: bool = False,
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = scenario.lower()
    R = repo.commit("create pre-C root")
    path = add_agent(repo, label)
    C = repo.commit("create C-rooted action")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    parents = []
    for index in range(parent_count):
        repo.branch(f"carrier-{index}", C)
        if invalid_parent != index:
            claim(repo, (path,), f"claim on carrier {index}")
        parents.append(feature(repo, f"{label}-carrier-{index}"))
    neutral = None
    if neutral_parent:
        repo.branch("neutral", R)
        neutral = feature(repo, f"{label}-neutral")
        parents.append(neutral)
    candidate_landmark = repo.merge_commit(
        parents,
        f"direct merge deletion for {label}",
        writes={evidence_path(label): f"# Evidence {label}: resolved\n"},
        removes=(path,),
    )
    N = feature(repo, f"{label}-old")
    expected = (
        "blocking-finding"
        if invalid_parent is not None
        else "no-finding"
    )
    return _Fixture(
        scenario,
        repo,
        C,
        O,
        candidate_landmark,
        N,
        expected,
        {
            "merge_parents": parents,
            "neutral_parent": neutral,
            "invalid_parent": (
                parents[invalid_parent]
                if invalid_parent is not None
                else None
            ),
        },
    )


def pcx03_foreign_identity(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create pre-C root")
    text = agent_text("pcx03")
    path = queue_path("pcx03")
    add_agent(repo, "pcx03", path=path, text=text)
    C = repo.commit("create C-rooted pcx03")
    repo.branch("old", C)
    O = feature(repo, "pcx03-old")
    repo.branch("valid-carrier", C)
    claim(repo, (path,), "claim C-rooted occurrence")
    valid_parent = feature(repo, "pcx03-valid")
    repo.branch("foreign", R)
    add_agent(repo, "pcx03", path=path, text=text)
    claim(repo, (path,), "claim independent occurrence")
    foreign_parent = feature(repo, "pcx03-foreign")
    candidate_landmark = repo.merge_commit(
        (valid_parent, foreign_parent),
        "delete disconnected exact identities",
        writes={evidence_path("pcx03"): "# Evidence pcx03: resolved\n"},
        removes=(path,),
    )
    N = feature(repo, "pcx03-old")
    return _Fixture(
        "PCX-03-foreign-exact-identity",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "valid_parent": valid_parent,
            "foreign_parent": foreign_parent,
            "pre_C_root": R,
        },
    )


def supplier_fixture(
    root: Path,
    scenario: str,
    *,
    supplier_valid: bool,
    carrier_claimed: bool = False,
    merge_changes_evidence: bool = False,
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = scenario.lower()
    path = add_agent(repo, label)
    C = repo.commit("create supplier C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("supplier", C)
    if supplier_valid:
        claim(repo, (path,), "claim supplier occurrence")
        supplier = delete_with_evidence(
            repo, ((label, path),), "supplier deletes with authority"
        )
    else:
        repo.remove(path)
        supplier = repo.commit("supplier deletes without authority")
    repo.branch("carrier", C)
    if carrier_claimed:
        claim(repo, (path,), "claim carrier occurrence")
    carrier = feature(repo, f"{label}-carrier")
    writes = (
        {evidence_path(label): f"# Evidence {label}: resolved\n"}
        if merge_changes_evidence
        else {}
    )
    candidate_landmark = repo.merge_commit(
        (supplier, carrier),
        "adopt supplier absence",
        writes=writes,
        removes=(path,),
    )
    N = feature(repo, f"{label}-old")
    return _Fixture(
        scenario,
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding" if supplier_valid else "blocking-finding",
        {
            "supplier_parent": supplier,
            "carrier_parent": carrier,
            "carrier_claimed": carrier_claimed,
        },
    )


def p14_supplier_reintroduced(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "p14")
    original = repo.read(path)
    C = repo.commit("create p14 at C")
    repo.branch("old", C)
    O = feature(repo, "p14-old")
    repo.branch("supplier", C)
    claim(repo, (path,))
    first = delete_with_evidence(
        repo, (("p14", path),), "first valid supplier deletion"
    )
    repo.write(path, original)
    repo.commit("reintroduce identical p14")
    claim(repo, (path,), "fresh claim after reintroduction")
    second = delete_with_evidence(
        repo, (("p14", path),), "second valid deletion"
    )
    repo.branch("carrier", C)
    carrier = feature(repo, "p14-carrier")
    candidate_landmark = repo.merge_commit(
        (second, carrier),
        "merge after supplier reintroduction",
        removes=(path,),
    )
    N = feature(repo, "p14-old")
    return _Fixture(
        "P14-supplier-reintroduced",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"first_deletion": first, "second_deletion": second},
    )


def p15_competing_suppliers(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "p15")
    C = repo.commit("create p15 at C")
    repo.branch("old", C)
    O = feature(repo, "p15-old")
    suppliers = []
    for index in range(2):
        repo.branch(f"supplier-{index}", C)
        claim(repo, (path,), f"claim supplier {index}")
        suppliers.append(
            delete_with_evidence(
                repo,
                (("p15", path),),
                f"valid supplier deletion {index}",
            )
        )
    repo.branch("carrier", C)
    carrier = feature(repo, "p15-carrier")
    candidate_landmark = repo.merge_commit(
        (*suppliers, carrier),
        "merge competing suppliers",
        removes=(path,),
    )
    N = feature(repo, "p15-old")
    return _Fixture(
        "P15-competing-suppliers",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"supplier_events": suppliers},
    )


def p17_post_event_reintroduction(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "p17")
    original = repo.read(path)
    C = repo.commit("create p17 at C")
    repo.branch("old", C)
    O = feature(repo, "p17-old")
    repo.branch("candidate", C)
    claim(repo, (path,))
    first = delete_with_evidence(
        repo, (("p17", path),), "valid early deletion"
    )
    repo.write(path, original)
    repo.commit("reintroduce p17 after valid event")
    repo.remove(path)
    candidate_landmark = repo.commit("delete recreated p17 without claim")
    N = feature(repo, "p17-old")
    return _Fixture(
        "P17-post-event-reintroduction",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"early_authority_event": first},
    )


def pcx04_shared_supplier(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "pcx04")
    C = repo.commit("create pcx04 at C")
    repo.branch("old", C)
    O = feature(repo, "pcx04-old")
    repo.branch("supplier", C)
    claim(repo, (path,))
    deletion = delete_with_evidence(
        repo, (("pcx04", path),), "one shared supplier deletion"
    )
    absent = []
    for index in range(2):
        repo.branch(f"absent-{index}", deletion)
        absent.append(feature(repo, f"pcx04-absent-{index}"))
    repo.branch("carrier", C)
    carrier = feature(repo, "pcx04-carrier")
    candidate_landmark = repo.merge_commit(
        (*absent, carrier),
        "adopt one supplier through two absent parents",
        removes=(path,),
    )
    N = feature(repo, "pcx04-old")
    return _Fixture(
        "PCX-04-several-absent-one-supplier",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "authority_event": deletion,
            "absent_parents": absent,
            "carrier_parent": carrier,
        },
    )


def pcx05_competing_later_supplier(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "pcx05")
    original = repo.read(path)
    C = repo.commit("create pcx05 at C")
    repo.branch("old", C)
    O = feature(repo, "pcx05-old")
    repo.branch("supplier", C)
    claim(repo, (path,))
    first = delete_with_evidence(
        repo, (("pcx05", path),), "supplier D1"
    )
    repo.branch("absent-one", first)
    absent_one = feature(repo, "pcx05-absent-one")
    repo.branch("later", first)
    repo.write(path, original)
    repo.commit("reintroduce pcx05")
    claim(repo, (path,), "fresh claim for later occurrence")
    repo.remove(path)
    repo.write(
        evidence_path("pcx05"),
        "# Evidence pcx05: second occurrence resolved\n",
    )
    second = repo.commit("supplier D2")
    repo.branch("carrier", C)
    carrier = feature(repo, "pcx05-carrier")
    candidate_landmark = repo.merge_commit(
        (absent_one, second, carrier),
        "merge competing D1 and D2",
        removes=(path,),
    )
    N = feature(repo, "pcx05-old")
    return _Fixture(
        "PCX-05-competing-later-supplier",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"D1": first, "D2": second},
    )


def pcx06_nested_supplier(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create pcx06 pre-C root")
    path = add_agent(repo, "pcx06")
    C = repo.commit("create pcx06 at C")
    repo.branch("old", C)
    O = feature(repo, "pcx06-old")
    repo.branch("direct", C)
    claim(repo, (path,))
    direct_parent = feature(repo, "pcx06-direct-parent")
    repo.branch("direct-two", C)
    claim(repo, (path,))
    direct_two = feature(repo, "pcx06-direct-two")
    deletion = repo.merge_commit(
        (direct_parent, direct_two),
        "two-parent direct deletion",
        writes={evidence_path("pcx06"): "# Evidence pcx06: resolved\n"},
        removes=(path,),
    )
    repo.branch("carrier-one", C)
    carrier_one = feature(repo, "pcx06-carrier-one")
    repo.branch("neutral-one", R)
    neutral_one = feature(repo, "pcx06-neutral-one")
    adoption_one = repo.merge_commit(
        (deletion, carrier_one, neutral_one),
        "first supplier adoption",
        removes=(path,),
    )
    repo.branch("carrier-two", C)
    carrier_two = feature(repo, "pcx06-carrier-two")
    repo.branch("neutral-two", R)
    neutral_two = feature(repo, "pcx06-neutral-two")
    candidate_landmark = repo.merge_commit(
        (adoption_one, carrier_two, neutral_two),
        "second supplier adoption",
        removes=(path,),
    )
    N = feature(repo, "pcx06-old")
    return _Fixture(
        "PCX-06-nested-supplier-over-direct",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "direct_event": deletion,
            "adoptions": [adoption_one, candidate_landmark],
            "carriers": [carrier_one, carrier_two],
            "neutral_parents": [neutral_one, neutral_two],
            "absent_sources": [deletion, adoption_one],
        },
    )


def pcx09_recreated_claimed_bytes(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, "pcx09")
    C = repo.commit("create pcx09 at C")
    repo.branch("old", C)
    O = feature(repo, "pcx09-old")
    repo.branch("supplier", C)
    claim(repo, (path,))
    first = delete_with_evidence(
        repo, (("pcx09", path),), "valid D1"
    )
    recreated = agent_text("pcx09", status="in-repair")
    repo.write(path, recreated)
    repo.commit("recreate already-claimed bytes")
    repo.remove(path)
    second = repo.commit("delete recreated bytes without fresh claim")
    repo.branch("carrier", C)
    carrier = feature(repo, "pcx09-carrier")
    candidate_landmark = repo.merge_commit(
        (second, carrier),
        "adopt recreated deletion",
        removes=(path,),
    )
    N = feature(repo, "pcx09-old")
    return _Fixture(
        "PCX-09-recreated-claimed-bytes",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"D1": first, "D2": second},
    )


def pcx10_transient_multiplicity(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    first = add_agent(repo, "pcx10")
    text = repo.read(first)
    second = queue_path("pcx10-copy")
    C = repo.commit("create unique pcx10 at C")
    repo.branch("old", C)
    O = feature(repo, "pcx10-old")
    repo.branch("candidate", C)
    claim(repo, (first,))
    repo.write(second, repo.read(first))
    duplicate = repo.commit("transiently duplicate exact identity")
    repo.remove(second)
    repo.commit("collapse transient duplicate")
    candidate_landmark = delete_with_evidence(repo, (("pcx10", first),))
    N = feature(repo, "pcx10-old")
    return _Fixture(
        "PCX-10-transient-multiplicity",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"duplicate_commit": duplicate, "duplicate_path": second},
    )


def pcx11_distinct_payload(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create pcx11 pre-C root")
    path = add_agent(
        repo, "pcx11-a", path=queue_path("pcx11")
    )
    C = repo.commit("create Q-A at C")
    repo.branch("old", C)
    O = feature(repo, "pcx11-old")
    repo.branch("supplier", C)
    claim(repo, (path,))
    supplier = delete_with_evidence(
        repo, (("pcx11-a", path),), "valid Q-A supplier"
    )
    repo.branch("carrier", C)
    carrier = feature(repo, "pcx11-carrier")
    repo.branch("foreign-b", R)
    add_agent(
        repo,
        "pcx11-b",
        path=path,
        text=agent_text(
            "pcx11-b", action="different immutable Q-B action"
        ),
    )
    foreign = feature(repo, "pcx11-foreign-b")
    candidate_landmark = repo.merge_commit(
        (supplier, carrier, foreign),
        "merge absent Q-A and delete unresolved Q-B",
        removes=(path,),
    )
    N = feature(repo, "pcx11-old")
    return _Fixture(
        "PCX-11-different-payload-same-path",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "Q-A_supplier": supplier,
            "Q-B_foreign_parent": foreign,
        },
    )


def pcx12_timing_supplier(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    old_path = add_agent(
        repo,
        "pcx12",
        path=queue_path("pcx12-before", timing="future-blocking"),
    )
    moved = queue_path("pcx12-after", timing="blocking")
    C = repo.commit("create pcx12 at C")
    repo.branch("old", C)
    O = feature(repo, "pcx12-old")
    repo.branch("supplier", C)
    claim(repo, (old_path,))
    supplier = delete_with_evidence(
        repo, (("pcx12", old_path),), "supplier deletes original path"
    )
    repo.branch("carrier", C)
    repo.move(old_path, moved)
    carrier = feature(repo, "pcx12-moved-carrier")
    candidate_landmark = repo.merge_commit(
        (supplier, carrier),
        "adopt supplier after identity-preserving move",
        removes=(old_path, moved),
    )
    N = feature(repo, "pcx12-old")
    return _Fixture(
        "PCX-12-timing-rename-supplier",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {"moved_path": moved, "carrier": carrier},
    )


def human_supplier_fixture(
    root: Path, scenario: str, *, conflicting_carrier: bool
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create human supplier pre-C root")
    label = scenario.lower()
    path = add_human(repo, label)
    C = repo.commit("create unanswered human action at C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("supplier", C)
    answer(repo, path, "approve")
    claim(repo, (path,), "fold approved human action")
    supplier = delete_with_evidence(
        repo, ((label, path),), "resolve approved human action"
    )
    repo.branch("carrier", C)
    if conflicting_carrier:
        answer(repo, path, "reject")
    carrier = feature(repo, f"{label}-carrier")
    details = {
        "supplier_parent": supplier,
        "carrier_parent": carrier,
        "carrier_response": (
            "reject" if conflicting_carrier else "unanswered"
        ),
    }
    if conflicting_carrier:
        repo.branch("human-neutral-one", R)
        neutral_one = feature(repo, f"{label}-neutral-one")
        inner_invalid = repo.merge_commit(
            (supplier, carrier, neutral_one),
            "adopt conflicting human supplier",
            removes=(path,),
        )
        repo.branch("human-carrier-two", C)
        carrier_two = feature(repo, f"{label}-carrier-two")
        repo.branch("human-neutral-two", R)
        neutral_two = feature(repo, f"{label}-neutral-two")
        outer_invalid = repo.merge_commit(
            (inner_invalid, carrier_two, neutral_two),
            "continue invalid human supplier ancestry",
            removes=(path,),
        )
        repo.branch("human-carrier-three", C)
        carrier_three = feature(repo, f"{label}-carrier-three")
        repo.branch("human-neutral-three", R)
        neutral_three = feature(repo, f"{label}-neutral-three")
        candidate_landmark = repo.merge_commit(
            (outer_invalid, carrier_three, neutral_three),
            "continue third-level invalid human supplier ancestry",
            removes=(path,),
        )
        details.update(
            {
                "inner_invalid": inner_invalid,
                "outer_invalid": outer_invalid,
                "adoptions": [inner_invalid, outer_invalid, candidate_landmark],
                "carriers": [carrier, carrier_two, carrier_three],
                "neutral_parents": [
                    neutral_one,
                    neutral_two,
                    neutral_three,
                ],
                "absent_sources": [
                    supplier,
                    inner_invalid,
                    outer_invalid,
                ],
            }
        )
    else:
        candidate_landmark = repo.merge_commit(
            (supplier, carrier),
            "adopt human supplier absence",
            removes=(path,),
        )
    N = feature(repo, f"{label}-old")
    return _Fixture(
        scenario,
        repo,
        C,
        O,
        candidate_landmark,
        N,
        (
            "blocking-finding"
            if conflicting_carrier
            else "no-finding"
        ),
        details,
    )


def r8_human_response_binding(
    root: Path, *, mode: str, conflict: bool
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    disposition = "conflict" if conflict else "identical"
    label = f"r8-{mode}-{disposition}-response"
    path = add_human(repo, label)
    C = repo.commit("create unanswered human response at C")
    repo.branch("old", C)
    old_response = "reject" if conflict else "approve"
    answer(repo, path, old_response)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate-authority", C)
    answer(repo, path, "approve")
    authority_parent = claim(
        repo, (path,), "fold candidate human response"
    )
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve candidate human response",
    )
    carrier = None
    if mode == "supplier":
        repo.branch("candidate-carrier", C)
        carrier = feature(repo, f"{label}-carrier")
        candidate_landmark = repo.merge_commit(
            (deletion, carrier),
            "adopt human response supplier absence",
            removes=(path,),
        )
    else:
        candidate_landmark = deletion
    N = feature(repo, f"{label}-old")
    return _Fixture(
        f"R8-{mode}-human-response-{disposition}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding" if conflict else "no-finding",
        {
            "old_response": old_response,
            "candidate_response": "approve",
            "authority_parent": authority_parent,
            "authority_child": deletion,
            "carrier": carrier,
            "mode": mode,
            "binding_conflict": conflict,
        },
    )


def r8_review_binding(root: Path, *, divergent: bool) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    disposition = "divergent" if divergent else "identical"
    label = f"r8-review-{disposition}"
    target_A = f"docs/{label}-target-a.md"
    target_B = f"docs/{label}-target-b.md"
    payload_A = f"# {label} target A\n"
    payload_B = f"# {label} target B\n"
    repo.write(target_A, payload_A)
    repo.write(target_B, payload_B)
    revision_A = review_revision(payload_A)
    revision_B = review_revision(payload_B)
    path = add_review(
        repo,
        label,
        status="awaiting-artifact" if divergent else "waiting",
        target="pending" if divergent else target_A,
        revision="pending" if divergent else revision_A,
    )
    C = repo.commit("create unanswered review at C")
    repo.branch("old", C)
    if divergent:
        publish_review(repo, path, target_A, revision_A)
    answer_review(repo, path, "approve")
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    if divergent:
        publish_review(repo, path, target_B, revision_B)
    answer_review(repo, path, "approve")
    authority_parent = claim_review(repo, path)
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve candidate human review",
    )
    candidate_landmark = deletion
    N = feature(repo, f"{label}-old")
    return _Fixture(
        f"R8-review-binding-{disposition}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding" if divergent else "no-finding",
        {
            "old_binding": [target_A, revision_A],
            "candidate_binding": [
                target_B if divergent else target_A,
                revision_B if divergent else revision_A,
            ],
            "authority_parent": authority_parent,
            "authority_child": deletion,
            "binding_conflict": divergent,
        },
    )


def r8_review_terminal_binding_conflict(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r8-review-terminal-conflict"
    target = f"docs/{label}-target.md"
    payload = f"# {label} target\n"
    repo.write(target, payload)
    revision = review_revision(payload)
    path = add_review(
        repo,
        label,
        status="waiting",
        target=target,
        revision=revision,
    )
    C = repo.commit("create unanswered terminal-binding review at C")
    repo.branch("old", C)
    answer_review(repo, path, "recorded review")
    claim_review(repo, path, outcome="rejected")
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    answer_review(repo, path, "recorded review")
    authority_parent = claim_review(repo, path, outcome="approved")
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve candidate terminal-binding review",
    )
    N = feature(repo, f"{label}-old")
    return _Fixture(
        "R8-review-binding-terminal-conflict",
        repo,
        C,
        O,
        deletion,
        N,
        "blocking-finding",
        {
            "old_binding": [target, revision, revision, "rejected"],
            "candidate_binding": [
                target,
                revision,
                revision,
                "approved",
            ],
            "old_terminal_fields": {
                "Reviewed revision": revision,
                "Review outcome": "rejected",
            },
            "candidate_terminal_fields": {
                "Reviewed revision": revision,
                "Review outcome": "approved",
            },
            "authority_parent": authority_parent,
            "authority_child": deletion,
            "binding_conflict": True,
        },
    )


def r9_review_pending_binding(
    root: Path, *, mode: str, pending_field: str
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    field_slug = (
        "target" if pending_field == "Review target" else "revision"
    )
    label = f"r9-{mode}-{field_slug}-pending"
    target = f"docs/{label}-target.md"
    payload = f"# {label} target\n"
    repo.write(target, payload)
    revision = review_revision(payload)
    path = add_review(
        repo,
        label,
        status="awaiting-artifact",
        target="pending",
        revision="pending",
    )
    C = repo.commit(f"create review with pending {field_slug} at C")
    repo.branch("old", C)
    answer_review(repo, path, "approve")
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    publish_review(repo, path, target, revision)
    answer_review(repo, path, "approve")
    authority_parent = claim_review(repo, path)
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        f"resolve candidate review with filled {field_slug}",
    )
    carrier = None
    if mode == "supplier":
        repo.branch("candidate-carrier", C)
        carrier = feature(repo, f"{label}-carrier")
        candidate_landmark = repo.merge_commit(
            (deletion, carrier),
            f"adopt review {field_slug} supplier absence",
            removes=(path,),
        )
    else:
        candidate_landmark = deletion
    N = feature(repo, f"{label}-old")
    old_pending_value = "pending"
    candidate_value = (
        f"`{target}`"
        if pending_field == "Review target"
        else revision
    )
    return _Fixture(
        f"R9-{mode}-review-{field_slug}-pending-fill",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "pending_field": pending_field,
            "old_pending_value": old_pending_value,
            "candidate_value": candidate_value,
            "authority_parent": authority_parent,
            "authority_child": deletion,
            "carrier": carrier,
            "mode": mode,
        },
    )


def r10_malformed_review_binding(
    root: Path,
    *,
    mode: str,
    field: str,
    malformed_value: str,
    slug: str,
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    field_slug = "target" if field == "Review target" else "revision"
    label = f"r10-{mode}-{field_slug}-{slug}"
    target = f"docs/{label}-target.md"
    payload = f"# {label} target\n"
    repo.write(target, payload)
    revision = review_revision(payload)
    path = add_review(
        repo,
        label,
        status="waiting",
        target=malformed_value if field_slug == "target" else target,
        revision=(
            malformed_value if field_slug == "revision" else revision
        ),
    )
    old_value = RECONCILE.human_response_fields(repo.read(path))[field]
    C = repo.commit(f"create review with malformed {field_slug} at C")
    repo.branch("old", C)
    answer_review(repo, path, "approve")
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    replace_review_binding(
        repo,
        path,
        field=field,
        old_value=old_value,
        target=target,
        revision=revision,
    )
    answer_review(repo, path, "approve")
    authority_parent = claim_review(repo, path)
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        f"resolve candidate review after replacing malformed {field_slug}",
    )
    carrier = None
    if mode == "supplier":
        repo.branch("candidate-carrier", C)
        carrier = feature(repo, f"{label}-carrier")
        candidate_landmark = repo.merge_commit(
            (deletion, carrier),
            f"adopt malformed {field_slug} review supplier absence",
            removes=(path,),
        )
    else:
        candidate_landmark = deletion
    N = feature(repo, f"{label}-old")
    candidate_value = (
        f"`{target}`" if field == "Review target" else revision
    )
    return _Fixture(
        f"R10-{mode}-review-{field_slug}-{slug}-rejected",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "binding_field": field,
            "old_value": old_value,
            "candidate_value": candidate_value,
            "authority_parent": authority_parent,
            "authority_child": deletion,
            "carrier": carrier,
            "mode": mode,
        },
    )


def r13_review_parent_binding(
    root: Path, *, mode: str, variant: str
) -> _Fixture:
    """Bind every direct/supplier carrying parent to O's concrete review."""
    if mode not in {"direct", "supplier"}:
        raise ValueError(mode)
    if variant not in {"identical", "target", "revision", "terminal"}:
        raise ValueError(variant)
    repo = GitRepository(root)
    initialize(repo)
    label = f"r13-{mode}-review-{variant}"
    target_A = f"docs/{label}-target-a.md"
    target_B = f"docs/{label}-target-b.md"
    payload_A = f"# {label} target A\n"
    payload_B = f"# {label} target B\n"
    repo.write(target_A, payload_A)
    repo.write(target_B, payload_B)
    revision_A = review_revision(payload_A)
    revision_B = review_revision(payload_B)
    path = add_review(
        repo,
        label,
        status="awaiting-artifact",
        target="pending",
        revision="pending",
    )
    C = repo.commit("create awaiting-artifact carrier-binding review")

    response = "recorded review" if variant == "terminal" else "approve"
    old_outcome = "approved"
    concrete_terminal = variant in {"identical", "terminal"}
    repo.branch("old", C)
    publish_review(repo, path, target_A, revision_A)
    answer_review(repo, path, response)
    if concrete_terminal:
        claim_review(repo, path, outcome=old_outcome)
    O = feature(repo, f"{label}-old")

    repo.branch("candidate-authority", C)
    publish_review(repo, path, target_A, revision_A)
    answer_review(repo, path, response)
    authority_parent = claim_review(
        repo, path, outcome=old_outcome if concrete_terminal else "approved"
    )
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve matching candidate review authority",
    )

    carrier_target = target_B if variant == "target" else target_A
    carrier_revision = revision_B if variant in {"target", "revision"} else revision_A
    carrier_outcome = "rejected" if variant == "terminal" else "approved"
    repo.branch("candidate-carrier", C)
    if variant == "revision":
        repo.write(target_A, payload_B)
    publish_review(repo, path, carrier_target, carrier_revision)
    answer_review(repo, path, response)
    if mode == "direct" or concrete_terminal:
        carrier = claim_review(repo, path, outcome=carrier_outcome)
    else:
        carrier = feature(repo, f"{label}-live-carrier")

    if mode == "direct":
        candidate_landmark = repo.merge_commit(
            (authority_parent, carrier),
            "directly delete review from both carrying parents",
            writes={
                evidence_path(label): f"# Evidence {label}: resolved\n"
            },
            removes=(path,),
        )
    else:
        candidate_landmark = repo.merge_commit(
            (deletion, carrier),
            "adopt review supplier absence with carrying parent",
            removes=(path,),
        )
    N = feature(repo, f"{label}-new-tip")
    conflict = variant != "identical"
    changed_field = {
        "identical": None,
        "target": "Review target",
        "revision": "Review revision",
        "terminal": "Review outcome",
    }[variant]
    return _Fixture(
        f"R13-{mode}-review-binding-{variant}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding" if conflict else "no-finding",
        {
            "mode": mode,
            "variant": variant,
            "binding_conflict": conflict,
            "changed_field": changed_field,
            "response": response,
            "old_binding": [
                target_A,
                revision_A,
                revision_A if concrete_terminal else "pending",
                old_outcome if concrete_terminal else "pending",
            ],
            "carrier_binding": [
                carrier_target,
                carrier_revision,
                (
                    carrier_revision
                    if mode == "direct" or concrete_terminal
                    else "pending"
                ),
                (
                    carrier_outcome
                    if mode == "direct" or concrete_terminal
                    else "pending"
                ),
            ],
            "authority_parent": authority_parent,
            "authority_child": candidate_landmark if mode == "direct" else deletion,
            "carrier": carrier,
            "merge": candidate_landmark,
        },
    )


def low_similarity_delivery_text(text: str, marker: str) -> str:
    """Fixture helper retained for independent D+A endpoint probes."""
    replacement = f"**Resolution evidence:** {marker * 4096}"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("**Resolution evidence:**"):
            lines[index] = replacement
            return "\n".join(lines) + "\n"
    raise RuntimeError("fixture has no Resolution evidence field")


def r13_persisted_state(root: Path, variant: str) -> _Fixture:
    """Check O/N mutable state without relying on Git rename similarity."""
    variants = {
        "same-state",
        "response-removal",
        "response-change",
        "review-target-change",
        "review-revision-change",
        "review-outcome-change",
        "claim-loss",
        "pending-fill",
        "terminal-fill",
    }
    if variant not in variants:
        raise ValueError(variant)
    repo = GitRepository(root)
    initialize(repo)
    label = f"r13-persisted-{variant}"
    target_A = f"docs/{label}-target-a.md"
    target_B = f"docs/{label}-target-b.md"
    payload_A = f"# {label} target A\n"
    payload_B = f"# {label} target B\n"
    revision_A = review_revision(payload_A)
    revision_B = review_revision(payload_B)
    if variant in {
        "review-target-change",
        "review-revision-change",
        "pending-fill",
    }:
        repo.write(target_A, payload_A)
        repo.write(target_B, payload_B)
        path = add_review(
            repo,
            label,
            status="awaiting-artifact",
            target="pending",
            revision="pending",
        )
    elif variant in {"review-outcome-change", "terminal-fill"}:
        repo.write(target_A, payload_A)
        path = add_review(
            repo,
            label,
            status="waiting",
            target=target_A,
            revision=revision_A,
        )
    elif variant in {"response-removal", "response-change"}:
        path = add_human(repo, label)
    else:
        path = add_agent(repo, label)
    decision_variant = variant in {"response-removal", "response-change"}
    C = repo.commit(f"create persisted-state {variant} at C")

    repo.branch("old", C)
    if variant in {"response-removal", "response-change"}:
        answer(repo, path, "old-response-" * 4096)
    elif variant == "review-target-change":
        publish_review(repo, path, target_A, revision_A)
        answer_review(repo, path, "approve")
    elif variant == "review-revision-change":
        publish_review(repo, path, target_A, revision_A)
        answer_review(repo, path, "approve")
    elif variant == "review-outcome-change":
        answer_review(repo, path, "recorded review")
        claim_review(repo, path, outcome="rejected")
    elif variant == "claim-loss":
        claim(repo, (path,), "claim persisted action on old tip")
    elif variant == "terminal-fill":
        answer_review(repo, path, "approve")
    O = feature(repo, f"{label}-old-tip")

    repo.branch("candidate", C)
    if variant == "response-change":
        answer(repo, path, "new-response-" * 4096)
    elif variant == "review-target-change":
        publish_review(repo, path, target_B, revision_B)
        answer_review(repo, path, "approve")
    elif variant == "review-revision-change":
        repo.write(target_A, payload_B)
        publish_review(repo, path, target_A, revision_B)
        answer_review(repo, path, "approve")
    elif variant == "review-outcome-change":
        answer_review(repo, path, "recorded review")
        claim_review(repo, path, outcome="approved")
    elif variant == "pending-fill":
        publish_review(repo, path, target_A, revision_A)
    elif variant == "terminal-fill":
        answer_review(repo, path, "approve")
        claim_review(repo, path, outcome="approved")
    moved = str(
        Path(path).with_name(f"non-blocking-{label}-moved.md")
    )
    repo.move(path, moved)
    candidate_landmark = repo.commit(f"move low-similarity persisted-state {variant}")
    N = feature(repo, f"{label}-new-tip")

    old_text = repo.run("show", f"{O}:{path}").stdout
    new_text = repo.run("show", f"{N}:{moved}").stdout
    identity_equal = RECONCILE.queue_action_identity(
        path, old_text
    ) == RECONCILE.queue_action_identity(moved, new_text)
    name_status = repo.run(
        "diff", "--name-status", "-M", O, N, "--", path, moved
    ).stdout.splitlines()
    expected_problem = variant in {
        "response-removal",
        "response-change",
        "review-target-change",
        "review-revision-change",
        "review-outcome-change",
        "claim-loss",
    }
    return _Fixture(
        f"R13-persisted-{variant}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding" if expected_problem else "no-finding",
        {
            "variant": variant,
            "old_path": path,
            "new_path": moved,
            "production_identity_equal": identity_equal,
            "git_name_status": name_status,
            "low_similarity_delete_add": (
                f"D\t{path}" in name_status
                and f"A\t{moved}" in name_status
            ),
            "expected_low_similarity": decision_variant,
            "expected_state_problem": expected_problem,
        },
    )


def r14_review_carrier_binding(
    root: Path,
    *,
    mode: str,
    carrier_variant: str,
    old_answered: bool,
) -> _Fixture:
    """Exercise concrete published review state even when unanswered."""
    if mode not in {"direct", "supplier"}:
        raise ValueError(mode)
    if carrier_variant not in {"pending", "same", "target", "revision"}:
        raise ValueError(carrier_variant)
    if mode == "direct" and carrier_variant not in {"same", "target"}:
        raise ValueError("direct mode binds its one authority parent")

    repo = GitRepository(root)
    initialize(repo)
    answered_slug = "answered" if old_answered else "unanswered"
    label = f"r14-{mode}-{answered_slug}-{carrier_variant}"
    target_A = f"docs/{label}-target-a.md"
    target_B = f"docs/{label}-target-b.md"
    payload_A = f"# {label} A\n"
    payload_B = f"# {label} B\n"
    revision_A = review_revision(payload_A)
    revision_B = review_revision(payload_B)
    repo.write(target_A, payload_A)
    repo.write(target_B, payload_B)
    path = add_review(
        repo,
        label,
        status="awaiting-artifact",
        target="pending",
        revision="pending",
    )
    C = repo.commit("create pending review for unanswered binding matrix")

    repo.branch("old", C)
    publish_review(repo, path, target_A, revision_A)
    if old_answered:
        answer_review(repo, path, "approve")
    O = feature(repo, f"{label}-old")

    repo.branch("candidate-authority", C)
    authority_target = (
        target_B
        if mode == "direct" and carrier_variant == "target"
        else target_A
    )
    authority_revision = (
        revision_B
        if mode == "direct" and carrier_variant == "target"
        else revision_A
    )
    publish_review(repo, path, authority_target, authority_revision)
    answer_review(repo, path, "approve")
    authority_parent = claim_review(repo, path, outcome="approved")
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve review authority for unanswered binding matrix",
    )

    carrier = None
    carrier_binding = None
    if mode == "supplier":
        repo.branch("candidate-carrier", C)
        if carrier_variant == "pending":
            carrier = feature(repo, f"{label}-pending-carrier")
            carrier_binding = ["pending", "pending"]
        else:
            carrier_target = (
                target_B if carrier_variant == "target" else target_A
            )
            carrier_revision = (
                revision_B
                if carrier_variant in {"target", "revision"}
                else revision_A
            )
            carrier = publish_review(
                repo, path, carrier_target, carrier_revision
            )
            carrier_binding = [carrier_target, carrier_revision]
        candidate_landmark = repo.merge_commit(
            (deletion, carrier),
            "adopt absence with an unanswered published review carrier",
            removes=(path,),
        )
    else:
        candidate_landmark = deletion
        carrier_binding = [authority_target, authority_revision]
    N = feature(repo, f"{label}-new")

    conflict = carrier_variant in {"target", "revision"}
    return _Fixture(
        f"R14-{mode}-old-{answered_slug}-carrier-{carrier_variant}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding" if conflict else "no-finding",
        {
            "mode": mode,
            "old_answered": old_answered,
            "variant": carrier_variant,
            "binding_conflict": conflict,
            "old_binding": [target_A, revision_A],
            "carrier_binding": carrier_binding,
            "authority_parent": authority_parent,
            "authority_child": deletion,
            "carrier": carrier,
        },
    )


def r14_persisted_hidden_bytes(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r14-persisted-hidden-bytes"
    path = add_human(repo, label)
    hidden_A = "\n".join(
        f"protected-A-{index:04d}" for index in range(512)
    )
    hidden_B = "\n".join(
        f"protected-B-{index:04d}" for index in range(512)
    )
    original = repo.read(path) + f"\n<!--\n{hidden_A}\n-->\n"
    repo.write(path, original)
    C = repo.commit("create persisted action with protected hidden bytes")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    moved = str(Path(path).with_name(f"non-blocking-{label}-moved.md"))
    repo.move(path, moved)
    repo.write(moved, original.replace(hidden_A, hidden_B))
    candidate_landmark = repo.commit("move action while replacing protected hidden bytes")
    N = feature(repo, f"{label}-new")
    before = repo.run("show", f"{O}:{path}").stdout
    after = repo.run("show", f"{N}:{moved}").stdout
    name_status = repo.run(
        "diff", "--name-status", "-M", O, N, "--", path, moved
    ).stdout.splitlines()
    return _Fixture(
        "R14-persisted-hidden-bytes-low-similarity",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "old_path": path,
            "new_path": moved,
            "identity_equal": RECONCILE.queue_action_identity(
                path, before
            )
            == RECONCILE.queue_action_identity(moved, after),
            "frozen_equal": RECONCILE.queue_frozen_skeleton(
                path, before
            )
            == RECONCILE.queue_frozen_skeleton(moved, after),
            "git_name_status": name_status,
            "low_similarity_delete_add": (
                f"D\t{path}" in name_status
                and f"A\t{moved}" in name_status
            ),
        },
    )


def r14_persisted_intermediate_claim(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r14-persisted-intermediate-claim"
    path = add_agent(repo, label)
    C = repo.commit("create action for intermediate claim regression")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    claim(repo, (path,), "claim action in candidate history")
    before_bad = repo.read(path)
    repo.write(
        path,
        before_bad.replace("**Status:** in-repair", "**Status:** open", 1),
    )
    bad = repo.commit("regress candidate claim in intermediate commit")
    repo.write(path, before_bad)
    candidate_landmark = repo.commit("restore candidate claim before endpoint")
    N = feature(repo, f"{label}-new")
    return _Fixture(
        "R14-persisted-intermediate-claim-regression",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"bad": bad, "expected_problem": "committed in-repair"},
    )


def r14_persisted_intermediate_review(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r14-persisted-intermediate-review"
    target_A = f"docs/{label}-a.md"
    target_B = f"docs/{label}-b.md"
    payload_A = "# target A\n"
    payload_B = "# target B\n"
    revision_A = review_revision(payload_A)
    repo.write(target_A, payload_A)
    repo.write(target_B, payload_B)
    path = add_review(
        repo,
        label,
        status="waiting",
        target=target_A,
        revision=revision_A,
    )
    repo.commit("file concrete review")
    answer_review(repo, path, "approve")
    C = claim_review(repo, path, outcome="approved")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    original = repo.read(path)
    repo.write(
        path,
        original.replace(
            f"**Review target:** `{target_A}`",
            f"**Review target:** `{target_B}`",
            1,
        ),
    )
    bad = repo.commit("mutate review binding in intermediate commit")
    repo.write(path, original)
    candidate_landmark = repo.commit("restore review binding before endpoint")
    N = feature(repo, f"{label}-new")
    return _Fixture(
        "R14-persisted-intermediate-review-regression",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"bad": bad, "expected_problem": "immutable review binding"},
    )


def r14_persisted_delete_recreate(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r14-persisted-delete-recreate"
    path = add_agent(repo, label)
    original = repo.read(path)
    C = repo.commit("create action for delete-recreate continuity")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    repo.remove(path)
    gap = repo.commit("temporarily delete exact persisted identity")
    moved = str(Path(path).with_name(f"non-blocking-{label}-moved.md"))
    repo.write(moved, original)
    candidate_landmark = repo.commit("recreate exact persisted identity")
    N = feature(repo, f"{label}-new")
    return _Fixture(
        "R14-persisted-delete-recreate",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"gap": gap, "old_path": path, "new_path": moved},
    )


def r14_persisted_review_retraction(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r14-persisted-review-retraction"
    target_A = f"docs/{label}-a.md"
    target_B = f"docs/{label}-b.md"
    payload_A = "# first artifact\n"
    payload_B = "# replacement artifact\n"
    revision_A = review_revision(payload_A)
    revision_B = review_revision(payload_B)
    repo.write(target_A, payload_A)
    repo.write(target_B, payload_B)
    path = add_review(
        repo,
        label,
        status="awaiting-artifact",
        target="pending",
        revision="pending",
    )
    C = repo.commit("create pending review for valid retraction")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    published_A = publish_review(repo, path, target_A, revision_A)
    text = repo.read(path)
    text = text.replace("**Status:** waiting", "**Status:** awaiting-artifact", 1)
    text = text.replace(f"**Review target:** `{target_A}`", "**Review target:** pending", 1)
    text = text.replace(f"**Review revision:** {revision_A}", "**Review revision:** pending", 1)
    repo.write(path, text)
    retracted = repo.commit("retract unanswered review publication")
    published_B = publish_review(repo, path, target_B, revision_B)
    candidate_landmark = published_B
    N = feature(repo, f"{label}-new")
    return _Fixture(
        "R14-persisted-valid-review-retraction",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "published_A": published_A,
            "retracted": retracted,
            "published_B": published_B,
        },
    )


def r14_persisted_first_response_move(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r14-persisted-first-response-move"
    path = add_human(repo, label)
    C = repo.commit("create decision for low-similarity first response")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate", C)
    answer_commit = answer(repo, path, "first-response-" * 4096)
    moved = str(Path(path).with_name(f"non-blocking-{label}-moved.md"))
    repo.move(path, moved)
    candidate_landmark = repo.commit("move decision after valid first response")
    N = feature(repo, f"{label}-new")
    name_status = repo.run(
        "diff", "--name-status", "-M", O, N, "--", path, moved
    ).stdout.splitlines()
    return _Fixture(
        "R14-persisted-valid-first-response-low-similarity",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "answer_commit": answer_commit,
            "old_path": path,
            "new_path": moved,
            "git_name_status": name_status,
            "low_similarity_delete_add": (
                f"D\t{path}" in name_status
                and f"A\t{moved}" in name_status
            ),
        },
    )


def r14_persisted_merge_carriers(root: Path, *, conflict: bool) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    slug = "conflict" if conflict else "pending"
    label = f"r14-persisted-merge-{slug}-carrier"
    target_A = f"docs/{label}-a.md"
    target_B = f"docs/{label}-b.md"
    payload_A = "# source artifact\n"
    payload_B = "# carrier artifact\n"
    revision_A = review_revision(payload_A)
    revision_B = review_revision(payload_B)
    repo.write(target_A, payload_A)
    repo.write(target_B, payload_B)
    path = add_review(
        repo,
        label,
        status="awaiting-artifact",
        target="pending",
        revision="pending",
    )
    C = repo.commit("create pending review for persisted merge carriers")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("candidate-source", C)
    publish_review(repo, path, target_A, revision_A)
    answer_review(repo, path, "approve")
    source = claim_review(repo, path, outcome="approved")
    source_text = repo.read(path)
    repo.branch("candidate-carrier", C)
    if conflict:
        carrier = publish_review(repo, path, target_B, revision_B)
    else:
        carrier = feature(repo, f"{label}-pending")
    candidate_landmark = repo.merge_commit(
        (source, carrier),
        "merge persisted source with compatible or conflicting carrier",
        writes={path: source_text},
    )
    N = feature(repo, f"{label}-new")
    return _Fixture(
        f"R14-persisted-merge-carrier-{slug}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding" if conflict else "no-finding",
        {"source": source, "carrier": carrier, "merge": candidate_landmark, "conflict": conflict},
    )


def r17_outside_c_neutral_parent(root: Path) -> _Fixture:
    """Exact legal-restack DAG from the r17 blocking core review."""
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create root before the reviewed action exists")
    repo.branch("reviewed-C-line", R)
    label = "r17-outside-c-neutral-parent"
    path = add_agent(repo, label)
    C = repo.commit("create reviewed action at C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-task-patch")
    repo.branch("outside-C", R)
    F = feature(repo, f"{label}-outside-parent")
    P = repo.merge_commit(
        (C, F),
        "merge outside-C action-free parent while retaining Q",
    )
    repo.branch("candidate", P)
    K = claim(repo, (path,), "claim reviewed action after neutral merge")
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        "validly resolve reviewed action after neutral merge",
    )
    N = feature(repo, f"{label}-task-patch")
    old_patch = repo.run("diff", "--binary", C, O).stdout
    replayed_patch = repo.run("diff", "--binary", deletion, N).stdout
    bases = repo.run("merge-base", "--all", O, N).stdout.splitlines()
    with _fixture_repository_session(repo.root):
        deletion_problem = RECONCILE.queue_deletion_problem(
            path,
            repo.run("show", f"{K}:{path}").stdout,
            K,
            deletion,
        )
    return _Fixture(
        "R17-outside-C-neutral-parent-valid-restack",
        repo,
        C,
        O,
        deletion,
        N,
        "no-finding",
        {
            "R": R,
            "F": F,
            "P": P,
            "K": K,
            "deletion": deletion,
            "unique_merge_base": bases,
            "task_patch_equal": old_patch == replayed_patch,
            "production_deletion_problem": deletion_problem,
            "reviewer_counterexample_oids": {
                "C": "030fe92b832b1bd2790182cab030b9dfd46ec6dc",
                "O": "07418610247abbde975bd54ac937acf75ca02500",
                "F": "233e9c9821300b9a1579c261a37b3829d0459250",
                "P": "bda691d6bc1759421cc55925e8c350edea7d42be",
                "K": "920d63682562575383ac5adbaf33c5855d24a554",
                "deletion": "d45b8657259492bbc12f6c32a2e81a7944357ce4",
                "N": "3a60d2c225bbcdf0619135111af9bc0a1120dbce",
            },
        },
    )


def r17_carry_merge_fixture(
    root: Path, *, variant: str, reverse_parents: bool = False
) -> _Fixture:
    """Exercise one retained live occurrence across a post-C merge."""
    if variant not in {
        "compatible",
        "incompatible",
        "absent-arm",
        "outside-single",
        "outside-duplicate",
    }:
        raise ValueError(variant)
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit(f"create {variant} carry root")
    label = f"r17-carry-{variant}"
    path = add_agent(repo, label)
    text = repo.read(path)
    C = repo.commit(f"create {variant} carried action at C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-task-patch")

    repo.branch("primary-carrier", C)
    primary = feature(repo, f"{label}-primary")
    repo.branch("second-carrier", R if variant.startswith("outside-") else C)
    if variant == "incompatible":
        claim(repo, (path,), "claim incompatible carry arm")
        second = feature(repo, f"{label}-incompatible")
    elif variant == "absent-arm":
        repo.remove(path)
        second = repo.commit("remove action on competing C-descendant arm")
    elif variant == "outside-single":
        add_agent(repo, label, path=path, text=text)
        second = feature(repo, f"{label}-outside-single")
    elif variant == "outside-duplicate":
        add_agent(repo, label, path=path, text=text)
        duplicate_path = queue_path(f"{label}-duplicate")
        add_agent(repo, label, path=duplicate_path, text=text)
        second = feature(repo, f"{label}-outside-duplicate")
    else:
        second = feature(repo, f"{label}-compatible")
    parents = (second, primary) if reverse_parents else (primary, second)
    merge = repo.merge_commit(
        parents,
        f"retain action across {variant} carry merge",
        writes={path: text},
        removes=(
            (queue_path(f"{label}-duplicate"),)
            if variant == "outside-duplicate"
            else ()
        ),
    )
    repo.branch("candidate", merge)
    authority_parent = claim(repo, (path,), "claim retained carried action")
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve retained carried action",
    )
    N = feature(repo, f"{label}-task-patch")
    expected = "no-finding" if variant == "compatible" else "blocking-finding"
    suffix = "-reversed" if reverse_parents else ""
    return _Fixture(
        f"R17-carry-{variant}{suffix}",
        repo,
        C,
        O,
        deletion,
        N,
        expected,
        {
            "variant": variant,
            "merge": merge,
            "primary": primary,
            "second": second,
            "merge_parents": list(parents),
            "authority_parent": authority_parent,
            "authority_child": deletion,
            "reverse_parents": reverse_parents,
        },
    )


def r17_persisted_carry_fixture(
    root: Path, *, variant: str, reverse_parents: bool = False
) -> _Fixture:
    """Persist Q across a merge whose second arm must still compete."""
    if variant not in {
        "outside-single",
        "outside-duplicate",
        "valid-absent-arm",
        "unauthorized-absent-arm",
    }:
        raise ValueError(variant)
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit(f"create persisted {variant} root")
    label = f"r17-persisted-{variant}"
    text = agent_text(label)
    path = add_agent(repo, label, text=text)
    C = repo.commit(f"admit persisted {variant} action at C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-task-patch")
    repo.branch("primary-carrier", C)
    A = feature(repo, f"{label}-carrier")

    duplicate_path = None
    if variant.startswith("outside-"):
        repo.branch("competing-arm", R)
        add_agent(repo, label, path=path, text=text)
        if variant == "outside-duplicate":
            duplicate_path = queue_path(f"{label}-duplicate")
            add_agent(repo, label, path=duplicate_path, text=text)
        second = feature(repo, f"{label}-outside")
        K = D = None
    else:
        repo.branch("competing-arm", C)
        if variant == "valid-absent-arm":
            K = claim(repo, (path,), "claim persisted absent arm")
            D = delete_with_evidence(
                repo,
                ((label, path),),
                "validly delete persisted absent arm",
            )
        else:
            K = None
            repo.remove(path)
            D = repo.commit("delete persisted absent arm without authority")
        second = D
    parents = (second, A) if reverse_parents else (A, second)
    P = repo.merge_commit(
        parents,
        f"explicitly retain persisted action across {variant}",
        writes={path: text},
        removes=((duplicate_path,) if duplicate_path else ()),
    )
    N = feature(repo, f"{label}-task-patch")
    details = {
        "R": R,
        "A": A,
        "second": second,
        "P": P,
        "K": K,
        "D": D,
        "variant": variant,
        "reverse_parents": reverse_parents,
        "merge_parents": list(parents),
        "duplicate_path": duplicate_path,
    }
    if variant == "outside-single":
        details["review_reference_oids"] = {
            "C": "843634959ac1156ef81ee7ccbf1f703261bbde1f",
            "O": "c0ec07829f6aa4e1207a680a0354deb8a8f0c162",
            "A": "426b485efa3b5f85a678600795a20b1e91c6049f",
            "F": "e10a4eb3208c44000e7363c2894e2a77b74828fa",
            "P": "60f5448337b6f9a114c0231b86242474dd34873b",
            "N": "af48cf172570a08d65c12dc467b2226dfbe8981a",
        }
    elif variant == "valid-absent-arm":
        details["review_reference_oids"] = {
            "C": "0ddb561a40c84c0590d9abe8a3036521b239de25",
            "O": "17ef4a3d8c518778d62c635864670319efd03754",
            "A": "90de0b5af2ad8baec036ddaed2842eda86c2c556",
            "K": "f03d61cc931d7c860e7fd6f166c60d09596b48e5",
            "D": "161d7ed2d7bc121ce5331fed2e1ecb0dd650041e",
            "P": "1847cdbe8298d5895ad566c03abc870064ca711b",
            "N": "76cf3354a913effec09cac7b183684159dfd0b84",
        }
    suffix = "-reversed" if reverse_parents else ""
    return _Fixture(
        f"R17-persisted-{variant}{suffix}",
        repo,
        C,
        O,
        P,
        N,
        "blocking-finding",
        details,
    )


def r17_boundary_budget_fixture(
    root: Path,
    *,
    counter: str = "graph_parent_tokens",
    limit: int = 7,
    exact: bool = False,
) -> _Fixture:
    """Meter a small intrinsic cone with a wide outside-C boundary."""
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create wide-boundary budget root")
    label = "r17-boundary-budget"
    path = add_agent(repo, label)
    C = repo.commit("admit wide-boundary budget action at C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-task-patch")
    repo.branch("primary-carrier", C)
    A = feature(repo, f"{label}-carrier")
    outside = []
    for index in range(64):
        repo.branch(f"outside-{index:02d}", R)
        outside.append(feature(repo, f"{label}-outside-{index:02d}"))
    P = repo.merge_commit(
        (A, *outside),
        "retain action across 64 immediate outside-C boundary parents",
    )
    N = feature(repo, f"{label}-task-patch")
    scenario = (
        f"R17-wide-graph-{counter}-exact"
        if exact
        else "R17-wide-outside-C-boundary-budget"
    )
    return _Fixture(
        scenario,
        repo,
        C,
        O,
        P,
        N,
        "no-finding" if exact else "blocking-finding",
        {
            "A": A,
            "P": P,
            "outside_parents": outside,
            "budget_contract": {
                "counter": counter,
                "limit": limit,
                "overflow_classification": "budget-exceeded",
                "transactional_zero_results": True,
                "raw_graph_bytes": 2952,
                "raw_graph_lines": 4,
                "raw_graph_fields": [2, 2, 66, 2],
            },
            "review_reference_oids": {
                "C": "b066accf737c901fd1ee314fcf310afb70c8fe87",
                "O": "ba894e5a1c019e3b2c29ee8319eebfb4b0aaa9a3",
                "P": "b79ff7a4036270fed4a70d82ad226817ae94e662",
                "N": "412c2f8c5a8be93d1e0ffc5983d607bf750bb2f0",
            },
        },
        budget_limits={counter: limit},
    )


def r17_graph_parent_tokens_exact(root: Path) -> _Fixture:
    fixture = r17_boundary_budget_fixture(
        root, counter="graph_parent_tokens", limit=68, exact=True
    )
    fixture.scenario = "R17-graph-parent-tokens-exact"
    fixture.details["typed_budget_counter"] = "graph_parent_tokens"
    fixture.details["typed_budget_limit"] = 68
    fixture.details["overflow_by_one"] = False
    return fixture


def r17_graph_parent_tokens_plus_one(root: Path) -> _Fixture:
    fixture = r17_boundary_budget_fixture(
        root, counter="graph_parent_tokens", limit=67
    )
    fixture.scenario = "R17-graph-parent-tokens-plus-one-refused"
    fixture.details["typed_budget_counter"] = "graph_parent_tokens"
    fixture.details["typed_budget_limit"] = 67
    fixture.details["overflow_by_one"] = True
    return fixture


def r17_graph_dimension_budget(
    root: Path,
    *,
    counter: str,
    limit: int,
    overflow: bool,
) -> _Fixture:
    fixture = r17_boundary_budget_fixture(
        root, counter=counter, limit=limit, exact=not overflow
    )
    dimension = {
        "graph_output_bytes": "output-bytes",
        "graph_line_peak_bytes": "line-peak-bytes",
    }[counter]
    fixture.scenario = (
        f"R17-graph-{dimension}-plus-one-refused"
        if overflow
        else f"R17-graph-{dimension}-exact"
    )
    fixture.expected = "blocking-finding" if overflow else "no-finding"
    fixture.details["typed_budget_counter"] = counter
    fixture.details["typed_budget_limit"] = limit
    fixture.details["overflow_by_one"] = overflow
    return fixture


def r17_workflow_input_case(root: Path, case: str) -> _Fixture:
    """Bind non-core transport claims to the exact O,N-only API."""
    cases = {
        "fast-forward",
        "pre-pr-push",
        "base-advance-retarget",
        "multiple-pr-api-race",
        "stale-rerun",
        "missing-old",
        "zero-endpoints",
        "pr-synchronize",
    }
    if case not in cases:
        raise ValueError(case)
    if case == "fast-forward":
        repo = GitRepository(root)
        initialize(repo)
        path = add_agent(repo, "r17-workflow-fast-forward")
        C = repo.commit("create fast-forward input action")
        O = feature(repo, "r17-workflow-fast-forward-old")
        N = feature(repo, "r17-workflow-fast-forward-new")
        fixture = _Fixture(
            "W0-fast-forward-return",
            repo,
            O,
            O,
            N,
            N,
            "no-finding",
            {"preserved_path": path},
        )
    else:
        fixture = ordinary_linear_fixture(
            root,
            f"W-{case}",
            valid=True,
        )
        fixture.scenario = {
            "pre-pr-push": "W1-pre-PR-push-exact-endpoints",
            "base-advance-retarget": "W2-base-advance-retarget-invariant",
            "multiple-pr-api-race": "W3-multiple-PR-API-zero-calls",
            "stale-rerun": "W4-stale-rerun-exact-inputs",
            "missing-old": "W5-missing-O-coverage-unavailable",
            "zero-endpoints": "W6-created-deleted-zero-endpoints",
            "pr-synchronize": "W7-PR-synchronize-top-level-endpoints",
        }[case]
    O = fixture.O
    N = fixture.N
    contract = {
        "authoritative_inputs": {"O": O, "N": N},
        "classifier_parameters": ["O", "N"],
        "provider_api_calls": 0,
        "fallback": None,
    }
    if case == "pre-pr-push":
        fixture.repo.branch("workflow-default-tip", fixture.expected_C)
        default_tip = feature(fixture.repo, "workflow-default-tip")
        contract.update(
            {
                "transport": "push",
                "O_source": "immutable event.before",
                "N_source": "immutable event.after",
                "event_before": O,
                "event_after": N,
                "github_sha": default_tip,
                "github_sha_is_authoritative": False,
                "pre_PR": True,
            }
        )
    elif case == "base-advance-retarget":
        contract["provider_state_variants"] = [
            "base-advanced",
            "retargeted",
            "base-equals-new-tip",
        ]
        contract["variants_keep_exact_O_N"] = True
    elif case == "multiple-pr-api-race":
        contract.update(
            {
                "provider_states": [
                    "pre-PR",
                    "closed-PR",
                    "multiple-PRs",
                    "fork",
                    "API-race",
                ],
                "PR_lookup": False,
            }
        )
    elif case == "stale-rerun":
        contract.update(
            {
                "repeat_exact_inputs": True,
                "stale_rerun_policy": "reuse immutable O,N",
            }
        )
    elif case == "missing-old":
        missing = "f" * len(O)
        fixture.O = missing
        fixture.expected = "unreadable"
        contract["authoritative_inputs"]["O"] = missing
        contract.update(
            {
                "coverage_classification": "coverage-unavailable",
                "old_object_fetch_exit": 2,
                "fallback": None,
            }
        )
    elif case == "zero-endpoints":
        zero = "0" * len(O)
        contract["event_classifications"] = [
            {
                "event": "created",
                "before": zero,
                "classification": "coverage-unavailable",
            },
            {
                "event": "deleted",
                "after": zero,
                "classification": "coverage-unavailable",
            },
        ]
    elif case == "pr-synchronize":
        contract.update(
            {
                "transport": "pull_request.synchronize",
                "O_source": "top-level before",
                "N_source": "top-level after",
                "top_level_before": O,
                "top_level_after": N,
                "pull_request_head_sha": N,
                "after_matches_head": True,
                "mismatch_classification": "coverage-unavailable",
                "PR_lookup": False,
            }
        )
    elif case == "fast-forward":
        contract["fast_forward_return"] = True
    fixture.details["workflow_contract"] = contract
    return fixture


def r17_unreadable_boundary(root: Path) -> _Fixture:
    fixture = r17_outside_c_neutral_parent(root)
    boundary = fixture.details["F"]
    hidden, _target = fixture.repo.hide_loose_object(boundary)
    fixture.scenario = "R17-unreadable-outside-C-boundary"
    fixture.expected = "unreadable"
    fixture.details.update(
        {
            "unreadable_boundary": boundary,
            "hidden_boundary_object": hidden.relative_to(
                fixture.repo.root
            ).as_posix(),
        }
    )
    return fixture


def r17_unopened_outside_c_ancestor(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r17-unopened-outside-c-ancestor"
    R = repo.commit("create shared root")
    repo.branch("outside", R)
    outside_text = agent_text(label, status="blocked")
    outside_path = add_agent(repo, label, text=outside_text)
    G = repo.commit("create outside-C ancestor with matching identity")
    ancestor_blob = repo.tree_entry_oid(G, outside_path)
    repo.remove(outside_path)
    F = repo.commit("drop matching identity before outside-C boundary")
    repo.branch("reviewed", R)
    c_text = agent_text(label)
    path = add_agent(repo, label, text=c_text)
    C = repo.commit("admit matching identity independently at C")
    c_blob = repo.tree_entry_oid(C, path)
    repo.branch("old", C)
    O = feature(repo, f"{label}-task-patch")
    P = repo.merge_commit(
        (C, F),
        "retain action across neutral outside-C boundary",
    )
    repo.branch("candidate", P)
    K = claim(repo, (path,), "claim action after neutral boundary")
    D = delete_with_evidence(
        repo, ((label, path),), "resolve action after neutral boundary"
    )
    N = feature(repo, f"{label}-task-patch")
    hidden, _target = repo.hide_loose_object(ancestor_blob)
    return _Fixture(
        "R17-unreadable-outside-C-ancestor-stays-unopened",
        repo,
        C,
        O,
        D,
        N,
        "no-finding",
        {
            "R": R,
            "G": G,
            "F": F,
            "P": P,
            "K": K,
            "D": D,
            "ancestor_blob": ancestor_blob,
            "C_blob": c_blob,
            "same_identity": (
                RECONCILE.queue_action_identity(outside_path, outside_text)
                == RECONCILE.queue_action_identity(path, c_text)
            ),
            "ancestor_blob_is_unique": ancestor_blob != c_blob,
            "hidden_ancestor_blob": hidden.relative_to(repo.root).as_posix(),
            "attacker_reference_oids": {
                "G": "b838a677f5753a45bff2d33f6e94b3a80cc92905",
                "G_blob": "88ce173dddc1914b0e7ccd52f5b89fb4742a713d",
                "C": "52c16e3ace5b2fb945b2e8fc42b7485536ea1a47",
                "O": "5ff93e594d8689fe44774a9728a882c846e1833e",
                "F": "4afa966344cb99e6a72a10997b10572072e7cccb",
                "P": "6564e680097653cebcc008a0bfee8587c644057f",
                "K": "245d7de3ef54645d32fbcf8bbda7d69f426ce6d2",
                "D": "595acd03b0c0f5cee214599587247d1115b2fc40",
                "N": "61d97651036a8cc9da10662ca7560bce14ce9ce5",
            },
        },
    )


def r15_old_side_continuity(root: Path, variant: str) -> _Fixture:
    """Exercise occurrence integrity on the C-to-O side of the split."""
    variants = {
        "invalid-delete-recreate",
        "valid-delete-recreate",
        "human-binding-restore",
        "hidden-bytes-restore",
        "continuous-preserved",
    }
    if variant not in variants:
        raise ValueError(variant)
    repo = GitRepository(root)
    initialize(repo)
    label = f"r15-old-{variant}"

    if variant == "human-binding-restore":
        path = add_human(repo, label)
        C = answer(repo, path, "approve")
        original = repo.read(path)
    else:
        path = add_agent(repo, label)
        if variant == "hidden-bytes-restore":
            repo.write(path, repo.read(path) + "\n<!-- protected-A -->\n")
        C = repo.commit("admit old-side continuity action at C")
        original = repo.read(path)

    repo.branch("old", C)
    details: dict[str, Any] = {"path": path, "variant": variant}
    if variant == "invalid-delete-recreate":
        repo.remove(path)
        details["gap"] = repo.commit("old side deletes without authority")
        repo.write(path, original)
        details["recreated"] = repo.commit(
            "old side recreates identical occurrence"
        )
    elif variant == "valid-delete-recreate":
        details["authority_parent"] = claim(
            repo, (path,), "old side claims occurrence"
        )
        details["authority_child"] = delete_with_evidence(
            repo,
            ((label, path),),
            "old side validly deletes claimed occurrence",
        )
        repo.write(path, original)
        details["recreated"] = repo.commit(
            "old side recreates after valid deletion"
        )
    elif variant == "human-binding-restore":
        repo.write(
            path,
            original.replace("**Your answer:** approve", "**Your answer:** reject", 1),
        )
        details["bad"] = repo.commit("change concrete old-side answer")
        repo.write(path, original)
        details["restored"] = repo.commit("restore concrete old-side answer")
    elif variant == "hidden-bytes-restore":
        repo.write(path, original.replace("protected-A", "protected-B", 1))
        details["bad"] = repo.commit("change protected old-side bytes")
        repo.write(path, original)
        details["restored"] = repo.commit("restore protected old-side bytes")
    else:
        details["old_step"] = feature(repo, f"{label}-old-step")
    O = feature(repo, f"{label}-old-tip")

    repo.branch("candidate", C)
    candidate_landmark = feature(repo, f"{label}-candidate-base")
    N = feature(repo, f"{label}-candidate-tip")
    expected = "no-finding" if variant == "continuous-preserved" else "blocking-finding"
    details["old_text_equals_C"] = (
        repo.run("show", f"{C}:{path}").stdout
        == repo.run("show", f"{O}:{path}").stdout
    )
    details["new_text_equals_C"] = (
        repo.run("show", f"{C}:{path}").stdout
        == repo.run("show", f"{N}:{path}").stdout
    )
    if variant == "valid-delete-recreate":
        with _fixture_repository_session(repo.root):
            details["deletion_problem"] = RECONCILE.queue_deletion_problem(
                path,
                repo.run(
                    "show", f"{details['authority_parent']}:{path}"
                ).stdout,
                details["authority_parent"],
                details["authority_child"],
            )
    return _Fixture(
        f"R15-old-{variant}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        expected,
        details,
    )


def conflicting_human_source(
    repo: GitRepository,
    *,
    C: str,
    R: str,
    path: str,
    label: str,
    suffix: str,
) -> dict:
    """Create one real invalid human supplier with its own ancestry."""
    repo.branch(f"{suffix}-supplier", C)
    answer(repo, path, "approve")
    claim(repo, (path,), f"{suffix} fold approved human action")
    deletion = delete_with_evidence(
        repo,
        ((label, path),),
        f"{suffix} resolve approved human action",
    )
    repo.branch(f"{suffix}-carrier", C)
    answer(repo, path, "reject")
    carrier = feature(repo, f"{suffix}-carrier")
    repo.branch(f"{suffix}-neutral", R)
    neutral = feature(repo, f"{suffix}-neutral")
    adoption = repo.merge_commit(
        (deletion, carrier, neutral),
        f"{suffix} adopt conflicting human supplier",
        removes=(path,),
    )
    return {
        "authority_event": deletion,
        "carrier": carrier,
        "neutral": neutral,
        "adoption": adoption,
    }


def r3_two_invalid_sources(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create two-invalid pre-C root")
    label = "r3-two-invalid"
    path = add_human(repo, label)
    C = repo.commit("create two-invalid human action at C")
    repo.branch("old", C)
    O = feature(repo, "r3-two-invalid-old")
    first = conflicting_human_source(
        repo,
        C=C,
        R=R,
        path=path,
        label=label,
        suffix="r3-invalid-one",
    )
    second = conflicting_human_source(
        repo,
        C=C,
        R=R,
        path=path,
        label=label,
        suffix="r3-invalid-two",
    )
    repo.branch("r3-two-invalid-final-carrier", C)
    final_carrier = feature(repo, "r3-two-invalid-final-carrier")
    repo.branch("r3-two-invalid-final-neutral", R)
    final_neutral = feature(repo, "r3-two-invalid-final-neutral")
    candidate_landmark = repo.merge_commit(
        (
            first["adoption"],
            second["adoption"],
            final_carrier,
            final_neutral,
        ),
        "merge two independent invalid causal sources",
        removes=(path,),
    )
    N = feature(repo, "r3-two-invalid-old")
    return _Fixture(
        "R3-01-two-invalid-causal-sources",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "authority_events": [
                first["authority_event"],
                second["authority_event"],
            ],
            "source_children": [first["adoption"], second["adoption"]],
            "carriers": [
                first["carrier"],
                second["carrier"],
                final_carrier,
            ],
            "adoptions": [first["adoption"], second["adoption"], candidate_landmark],
            "neutral_parents": [
                first["neutral"],
                second["neutral"],
                final_neutral,
            ],
            "absent_sources": [
                first["authority_event"],
                second["authority_event"],
                first["adoption"],
                second["adoption"],
            ],
        },
    )


def r3_invalid_valid_competition(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create mixed-source pre-C root")
    label = "r3-invalid-valid"
    path = add_human(repo, label)
    C = repo.commit("create mixed-source human action at C")
    repo.branch("old", C)
    O = feature(repo, "r3-invalid-valid-old")
    invalid = conflicting_human_source(
        repo,
        C=C,
        R=R,
        path=path,
        label=label,
        suffix="r3-mixed-invalid",
    )
    repo.branch("r3-mixed-valid-supplier", C)
    answer(repo, path, "approve")
    claim(repo, (path,), "r3 mixed valid fold approved human action")
    valid_deletion = delete_with_evidence(
        repo,
        ((label, path),),
        "r3 mixed valid resolve approved human action",
    )
    repo.branch("r3-mixed-final-carrier", C)
    final_carrier = feature(repo, "r3-mixed-final-carrier")
    repo.branch("r3-mixed-final-neutral", R)
    final_neutral = feature(repo, "r3-mixed-final-neutral")
    candidate_landmark = repo.merge_commit(
        (
            invalid["adoption"],
            valid_deletion,
            final_carrier,
            final_neutral,
        ),
        "merge invalid and valid causal sources",
        removes=(path,),
    )
    N = feature(repo, "r3-invalid-valid-old")
    return _Fixture(
        "R3-02-invalid-valid-causal-competition",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "authority_events": [
                invalid["authority_event"],
                valid_deletion,
            ],
            "source_children": [invalid["adoption"], valid_deletion],
            "carriers": [invalid["carrier"], final_carrier],
            "adoptions": [invalid["adoption"], candidate_landmark],
            "neutral_parents": [invalid["neutral"], final_neutral],
            "absent_sources": [
                invalid["authority_event"],
                invalid["adoption"],
                valid_deletion,
            ],
        },
    )


def r3_valid_plus_invalid_at_N(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r3-unrelated-invalid"
    path = add_agent(repo, label)
    C = repo.commit("create unrelated-invalid action at C")
    repo.branch("old", C)
    O = feature(repo, "r3-unrelated-invalid-old")
    repo.branch("unrelated-invalid", C)
    repo.remove(path)
    unrelated_invalid = repo.commit("delete action without authority")
    repo.branch("r3-positive-supplier", C)
    claim(repo, (path,), "claim positive supplier action")
    supplier = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve positive supplier action",
    )
    repo.branch("r3-positive-carrier", C)
    carrier = feature(repo, "r3-positive-carrier")
    candidate_landmark = repo.merge_commit(
        (supplier, carrier),
        "adopt only the causally relevant valid supplier",
        removes=(path,),
    )
    N = repo.merge_commit(
        (candidate_landmark, unrelated_invalid),
        "retain unrelated invalid source in candidate graph",
        writes={
            "features/r3-unrelated-invalid-old.md": (
                "# Feature r3-unrelated-invalid-old\n"
            )
        },
        removes=(path,),
    )
    unrelated_reachable = (
        repo.run(
            "merge-base",
            "--is-ancestor",
            unrelated_invalid,
            N,
            check=False,
        ).returncode
        == 0
    )
    unrelated_ancestor_of_supplier = (
        repo.run(
            "merge-base",
            "--is-ancestor",
            unrelated_invalid,
            supplier,
            check=False,
        ).returncode
        == 0
    )
    return _Fixture(
        "R3-03-valid-supplier-plus-invalid-parent-at-N-blocks",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "unrelated_invalid": unrelated_invalid,
            "supplier": supplier,
            "carrier": carrier,
            "unrelated_reachable_from_N": unrelated_reachable,
            "unrelated_ancestor_of_supplier": unrelated_ancestor_of_supplier,
        },
    )


def r4_supplier_wrapper(
    repo: GitRepository,
    *,
    C: str,
    R: str,
    path: str,
    absent_parents: Iterable[str],
    suffix: str,
) -> dict:
    repo.branch(f"{suffix}-carrier", C)
    carrier = feature(repo, f"{suffix}-carrier")
    repo.branch(f"{suffix}-neutral", R)
    neutral = feature(repo, f"{suffix}-neutral")
    adoption = repo.merge_commit(
        (*absent_parents, carrier, neutral),
        f"{suffix} adopt supplier envelope",
        removes=(path,),
    )
    return {
        "adoption": adoption,
        "carrier": carrier,
        "neutral": neutral,
    }


def r4_final_wrapper(
    repo: GitRepository,
    *,
    C: str,
    R: str,
    path: str,
    absent_parents: Iterable[str],
    suffix: str,
) -> dict:
    repo.branch(f"{suffix}-carrier", C)
    carrier = feature(repo, f"{suffix}-carrier")
    repo.branch(f"{suffix}-neutral", R)
    neutral = feature(repo, f"{suffix}-neutral")
    adoption = repo.merge_commit(
        (*absent_parents, carrier, neutral),
        f"{suffix} merge supplier envelopes",
        removes=(path,),
    )
    return {
        "adoption": adoption,
        "carrier": carrier,
        "neutral": neutral,
    }


def r4_same_root_diamond(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create same-root diamond pre-C root")
    label = "r4-same-root-diamond"
    path = add_agent(repo, label)
    C = repo.commit("create same-root diamond action at C")
    repo.branch("old", C)
    O = feature(repo, "r4-same-root-diamond-old")
    repo.branch("r4-shared-valid-root", C)
    claim(repo, (path,), "claim shared diamond root")
    valid_root = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve shared diamond root",
    )
    first = r4_supplier_wrapper(
        repo,
        C=C,
        R=R,
        path=path,
        absent_parents=(valid_root,),
        suffix="r4-same-first",
    )
    second = r4_supplier_wrapper(
        repo,
        C=C,
        R=R,
        path=path,
        absent_parents=(valid_root,),
        suffix="r4-same-second",
    )
    final = r4_final_wrapper(
        repo,
        C=C,
        R=R,
        path=path,
        absent_parents=(first["adoption"], second["adoption"]),
        suffix="r4-same-final",
    )
    candidate_landmark = final["adoption"]
    N = feature(repo, "r4-same-root-diamond-old")
    return _Fixture(
        "R4-01-same-root-valid-diamond",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "authority_events": [valid_root],
            "root_statuses": ["valid"],
            "carriers": [
                first["carrier"],
                second["carrier"],
                final["carrier"],
            ],
            "adoptions": [
                first["adoption"],
                second["adoption"],
                candidate_landmark,
            ],
            "neutral_parents": [
                first["neutral"],
                second["neutral"],
                final["neutral"],
            ],
            "absent_sources": [
                valid_root,
                first["adoption"],
                second["adoption"],
            ],
            "reason_children": [
                valid_root,
                first["adoption"],
                second["adoption"],
                candidate_landmark,
            ],
        },
    )


def r4_distinct_root_diamond(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create distinct-root diamond pre-C root")
    label = "r4-distinct-root-diamond"
    path = add_agent(repo, label)
    C = repo.commit("create distinct-root diamond action at C")
    repo.branch("old", C)
    O = feature(repo, "r4-distinct-root-diamond-old")
    valid_roots = []
    wrappers = []
    for index in (1, 2):
        repo.branch(f"r4-distinct-valid-root-{index}", C)
        claim(repo, (path,), f"claim distinct diamond root {index}")
        valid_root = delete_with_evidence(
            repo,
            ((label, path),),
            f"resolve distinct diamond root {index}",
        )
        valid_roots.append(valid_root)
        wrappers.append(
            r4_supplier_wrapper(
                repo,
                C=C,
                R=R,
                path=path,
                absent_parents=(valid_root,),
                suffix=f"r4-distinct-{index}",
            )
        )
    final = r4_final_wrapper(
        repo,
        C=C,
        R=R,
        path=path,
        absent_parents=tuple(
            wrapper["adoption"] for wrapper in wrappers
        ),
        suffix="r4-distinct-final",
    )
    candidate_landmark = final["adoption"]
    N = feature(repo, "r4-distinct-root-diamond-old")
    return _Fixture(
        "R4-02-distinct-valid-root-diamond",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "authority_events": valid_roots,
            "root_statuses": ["valid", "valid"],
            "carriers": [
                wrappers[0]["carrier"],
                wrappers[1]["carrier"],
                final["carrier"],
            ],
            "adoptions": [
                wrappers[0]["adoption"],
                wrappers[1]["adoption"],
                candidate_landmark,
            ],
            "neutral_parents": [
                wrappers[0]["neutral"],
                wrappers[1]["neutral"],
                final["neutral"],
            ],
            "absent_sources": [
                valid_roots[0],
                valid_roots[1],
                wrappers[0]["adoption"],
                wrappers[1]["adoption"],
            ],
            "reason_children": [
                valid_roots[0],
                wrappers[0]["adoption"],
                valid_roots[1],
                wrappers[1]["adoption"],
                candidate_landmark,
            ],
        },
    )


def r4_equal_root_plus_invalid(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    R = repo.commit("create mixed diamond pre-C root")
    label = "r4-equal-root-plus-invalid"
    path = add_agent(repo, label)
    C = repo.commit("create mixed diamond action at C")
    repo.branch("old", C)
    O = feature(repo, "r4-equal-root-plus-invalid-old")
    repo.branch("r4-equal-valid-root", C)
    claim(repo, (path,), "claim equal diamond root")
    valid_root = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve equal diamond root",
    )
    repo.branch("r4-additional-invalid-root", C)
    repo.remove(path)
    invalid_root = repo.commit("delete additional root without authority")
    first = r4_supplier_wrapper(
        repo,
        C=C,
        R=R,
        path=path,
        absent_parents=(valid_root,),
        suffix="r4-equal-first",
    )
    second = r4_supplier_wrapper(
        repo,
        C=C,
        R=R,
        path=path,
        absent_parents=(valid_root, invalid_root),
        suffix="r4-equal-second",
    )
    final = r4_final_wrapper(
        repo,
        C=C,
        R=R,
        path=path,
        absent_parents=(first["adoption"], second["adoption"]),
        suffix="r4-equal-final",
    )
    candidate_landmark = final["adoption"]
    N = feature(repo, "r4-equal-root-plus-invalid-old")
    return _Fixture(
        "R4-03-equal-root-plus-invalid-diamond",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "authority_events": [valid_root, invalid_root],
            "root_statuses": ["valid", "invalid"],
            "carriers": [
                first["carrier"],
                second["carrier"],
                final["carrier"],
            ],
            "adoptions": [
                first["adoption"],
                second["adoption"],
                candidate_landmark,
            ],
            "neutral_parents": [
                first["neutral"],
                second["neutral"],
                final["neutral"],
            ],
            "absent_sources": [
                valid_root,
                invalid_root,
                first["adoption"],
                second["adoption"],
            ],
            "reason_children": [
                valid_root,
                first["adoption"],
                invalid_root,
                second["adoption"],
                candidate_landmark,
            ],
        },
    )


def r5_reintroduced_supplier_history(
    root: Path, *, later_valid: bool
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    suffix = "valid" if later_valid else "invalid"
    label = f"r5-reintroduced-supplier-{suffix}"
    path = add_agent(repo, label)
    original = repo.read(path)
    C = repo.commit(f"create {label} action at C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch(f"{label}-supplier", C)
    root_parent = claim(repo, (path,), "claim initial supplier occurrence")
    valid_root = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve initial supplier occurrence",
    )
    repo.branch(f"{label}-carrier", C)
    carrier = feature(repo, f"{label}-carrier")
    candidate_landmark = repo.merge_commit(
        (valid_root, carrier),
        "adopt initial supplier absence",
        removes=(path,),
    )
    repo.write(path, original)
    if later_valid:
        repo.write(evidence_path(label), f"# Evidence {label}: pending\n")
    reintroduction = repo.commit("reintroduce the queue occurrence")
    later_parent = reintroduction
    if later_valid:
        later_parent = claim(
            repo, (path,), "claim reintroduced queue occurrence"
        )
        redeletion = delete_with_evidence(
            repo,
            ((label, path),),
            "resolve reintroduced queue occurrence",
        )
    else:
        repo.remove(path)
        redeletion = repo.commit(
            "delete reintroduced queue occurrence without authority"
        )
    N = feature(repo, f"{label}-old")
    return _Fixture(
        (
            "R5-02-valid-redelete-after-supplier-reintroduction"
            if later_valid
            else "R5-01-invalid-redelete-after-supplier-reintroduction"
        ),
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "initial_authority_parent": root_parent,
            "initial_authority_child": valid_root,
            "carrier": carrier,
            "supplier_adoption": candidate_landmark,
            "initial_absent_parent": valid_root,
            "reintroduction": reintroduction,
            "later_authority_parent": later_parent,
            "later_authority_child": redeletion,
            "later_authority_valid": later_valid,
            "reason_children": [valid_root, candidate_landmark, redeletion],
        },
    )


def r6_all_absent_roots(
    root: Path, *, first_valid: bool, second_kind: str
) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = f"r6-{first_valid}-{second_kind}"
    R = repo.commit(f"create {label} pre-C root")
    path = add_agent(repo, label)
    text = repo.read(path)
    C = repo.commit(f"create {label} action at C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    roots = []
    statuses = []
    for index, valid in enumerate((first_valid, False), start=1):
        kind = "valid" if valid else second_kind
        if index == 1 and not first_valid:
            kind = "invalid"
        if kind == "ambiguous":
            repo.branch(f"{label}-foreign-{index}", R)
            add_agent(repo, label, path=path, text=text)
            claim(repo, (path,), f"claim foreign occurrence {index}")
            deletion = delete_with_evidence(
                repo,
                ((label, path),),
                f"delete foreign occurrence {index}",
            )
        else:
            repo.branch(f"{label}-root-{index}", C)
            if kind == "valid":
                claim(repo, (path,), f"claim valid occurrence {index}")
                deletion = delete_with_evidence(
                    repo,
                    ((label, path),),
                    f"delete valid occurrence {index}",
                )
            else:
                repo.remove(path)
                deletion = repo.commit(
                    f"delete invalid occurrence {index} without authority"
                )
        roots.append(deletion)
        statuses.append(kind)
    candidate_landmark = repo.merge_commit(
        tuple(roots),
        "join all-absent causal roots",
        removes=(path,),
    )
    N = feature(repo, f"{label}-old")
    scenario = {
        (True, "invalid"): "R6-01-valid-plus-invalid-all-absent",
        (True, "ambiguous"): "R6-02-valid-plus-ambiguous-all-absent",
        (False, "invalid"): "R6-03-two-invalid-all-absent",
    }[(first_valid, second_kind)]
    return _Fixture(
        scenario,
        repo,
        C,
        O,
        candidate_landmark,
        N,
        (
            "no-finding"
            if first_valid and second_kind == "ambiguous"
            else "blocking-finding"
        ),
        {
            "causal_events": roots,
            "causal_statuses": statuses,
            "expected_problem_count": sum(
                status != "valid" for status in statuses
            ),
            "legacy_sole_valid_false_green": first_valid,
            "r17_disposition": (
                "outside-C all-absent boundary is neutral at multiplicity "
                "zero; its ambiguous ancestor root stays unopened"
                if first_valid and second_kind == "ambiguous"
                else None
            ),
        },
    )


def r6_same_root_all_absent_wrappers(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r6-same-root-all-absent"
    R = repo.commit("create same-root all-absent pre-C root")
    path = add_agent(repo, label)
    C = repo.commit("create same-root all-absent action at C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("r6-shared-root", C)
    claim(repo, (path,), "claim shared all-absent root")
    valid_root = delete_with_evidence(
        repo,
        ((label, path),),
        "resolve shared all-absent root",
    )
    wrappers = [
        r4_supplier_wrapper(
            repo,
            C=C,
            R=R,
            path=path,
            absent_parents=(valid_root,),
            suffix=f"r6-wrapper-{index}",
        )
        for index in (1, 2)
    ]
    candidate_landmark = repo.merge_commit(
        tuple(wrapper["adoption"] for wrapper in wrappers),
        "join equal-root all-absent wrappers",
        removes=(path,),
    )
    N = feature(repo, f"{label}-old")
    return _Fixture(
        "R6-04-same-valid-root-all-absent-wrappers",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "causal_events": [valid_root],
            "wrapper_events": [
                wrapper["adoption"] for wrapper in wrappers
            ],
            "carriers": [wrapper["carrier"] for wrapper in wrappers],
            "neutral_parents": [
                wrapper["neutral"] for wrapper in wrappers
            ],
            "absent_parents": [valid_root],
            "reason_children": [
                valid_root,
                *(wrapper["adoption"] for wrapper in wrappers),
            ],
        },
    )


def generated_retry(repo: GitRepository, bad_path: str):
    finding = RECONCILE.Finding(
        "queue-name", Path(bad_path), "bad name", "rename it"
    )
    path = (
        "message-queue/needs-agent/retries/"
        f"blocking-{RECONCILE.finding_key(finding)}.md"
    )
    payload = RECONCILE.retry_text(finding)
    repo.rendered_retries[path] = payload
    repo.write(path, payload)
    return path


def pcx15_generated_retry(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    bad = "message-queue/needs-agent/requests/bad.md"
    add_agent(repo, "pcx15-bad", path=bad)
    retry = generated_retry(repo, bad)
    C = repo.commit("file generated retry at C")
    repo.branch("old", C)
    O = feature(repo, "pcx15-old")
    repo.branch("supplier", C)
    fixed = queue_path("pcx15-bad")
    repo.move(bad, fixed)
    repo.remove(retry)
    supplier = repo.commit("fix finding and clear generated retry")
    repo.branch("carrier", C)
    carrier = feature(repo, "pcx15-carrier")
    candidate_landmark = repo.merge_commit(
        (supplier, carrier),
        "adopt generated retry clearance",
        removes=(retry,),
    )
    N = feature(repo, "pcx15-old")
    retry_identity = RECONCILE.queue_action_identity(
        retry,
        repo.rendered_retries[retry],
    )
    return _Fixture(
        "PCX-15-generated-retry-supplier",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "retry_path": retry,
            "production_retry_identity": list(retry_identity),
            "fixture_date": FIXTURE_DATE.isoformat(),
            "retry_payload_sha256": hashlib.sha256(
                repo.rendered_retries[retry].encode("utf-8")
            ).hexdigest(),
        },
    )


def pickup_text(task_path: str):
    return (
        "# Pick up task\n\n"
        "**Status:** open\n"
        "**Filed:** 2026-08-31\n"
        "**Action:** claim the task\n"
        f"**Full context:** `{task_path}`\n"
        "**Request kind:** task-pickup\n"
        "**If unanswered:** leave it in backlog\n"
    )


def add_pickup(repo: GitRepository, label: str):
    task_id = f"2026-08-31-{label}"
    backlog = f"tasks/0_backlog/{task_id}/task.md"
    active = f"tasks/1_in-progress/{task_id}/task.md"
    pickup = queue_path(f"pick-up-{label}")
    repo.write(pickup, pickup_text(backlog))
    repo.write(
        backlog,
        "# Task\n\n"
        "**Claimed-by:** unclaimed\n"
        f"**Queue actions:** `{pickup}`\n",
    )
    return pickup, backlog, active


def complete_pickup(
    repo: GitRepository, pickup: str, backlog: str, active: str
):
    repo.move(backlog, active)
    repo.write(
        active,
        repo.read(active)
        .replace("**Claimed-by:** unclaimed", "**Claimed-by:** poc-agent")
        .replace(f"**Queue actions:** `{pickup}`", "**Queue actions:** none"),
    )
    repo.remove(pickup)


def pcx16_task_pickup(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    pickup, backlog, active = add_pickup(repo, "pcx16")
    C = repo.commit("file task pickup at C")
    repo.branch("old", C)
    O = feature(repo, "pcx16-old")
    repo.branch("supplier", C)
    complete_pickup(repo, pickup, backlog, active)
    supplier = repo.commit("atomically claim task and delete pickup")
    repo.branch("carrier", C)
    carrier = feature(repo, "pcx16-carrier")
    candidate_landmark = repo.merge_commit(
        (supplier, carrier),
        "adopt task-pickup supplier",
        removes=(pickup,),
    )
    N = feature(repo, "pcx16-old")
    return _Fixture(
        "PCX-16-task-pickup-supplier",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {"pickup_path": pickup, "active_task": active},
    )


def r16_supplier_support_fixture(root: Path, variant: str) -> _Fixture:
    """Exercise exact source support copying without carrier authority."""
    variants = {
        "forward": "no-finding",
        "reverse-drop": "blocking-finding",
        "reverse-preserved": "no-finding",
        "invalid-source": "blocking-finding",
        "source-evolution": "no-finding",
        "adoption-drift": "blocking-finding",
        "nested-drop": "blocking-finding",
        "permutation-diamond": "no-finding",
    }
    if variant not in variants:
        raise ValueError(variant)
    repo = GitRepository(root)
    initialize(repo)
    label = f"r16-support-{variant}"
    path = add_agent(repo, label)
    evidence = evidence_path(label)
    C = repo.commit("create r16 supplier support action")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")

    repo.branch("support-source", C)
    if variant == "invalid-source":
        authority_parent = C
        repo.remove(path)
        authority_child = repo.commit("delete without production authority")
    else:
        authority_parent = claim(repo, (path,), "claim support source")
        authority_child = delete_with_evidence(
            repo, ((label, path),), "delete with support authority"
        )
    source_parent = authority_child
    if variant == "source-evolution":
        repo.write(evidence, f"# Evidence {label}: evolved-source\n")
        source_parent = repo.commit("evolve support on absent source lineage")

    repo.branch("support-carrier", C)
    carrier = claim(repo, (path,), "overqualified support carrier")
    resolved = f"# Evidence {label}: resolved\n"
    if variant == "forward":
        parents = (authority_child, carrier)
        candidate_landmark = repo.merge_commit(
            parents, "forward supplier support adoption", removes=(path,)
        )
    elif variant == "reverse-preserved":
        parents = (carrier, authority_child)
        candidate_landmark = repo.merge_commit(
            parents,
            "reverse supplier support adoption with projection",
            writes={evidence: resolved},
            removes=(path,),
        )
    elif variant == "source-evolution":
        parents = (carrier, source_parent)
        candidate_landmark = repo.merge_commit(
            parents,
            "copy evolved source support at adoption",
            writes={
                evidence: f"# Evidence {label}: evolved-source\n"
            },
            removes=(path,),
        )
    elif variant == "adoption-drift":
        parents = (authority_child, carrier)
        candidate_landmark = repo.merge_commit(
            parents,
            "invent support state in adoption commit",
            writes={evidence: f"# Evidence {label}: adoption-drift\n"},
            removes=(path,),
        )
    elif variant == "nested-drop":
        first = repo.merge_commit(
            (authority_child, carrier),
            "first support-preserving adoption",
            removes=(path,),
        )
        repo.branch("second-support-carrier", C)
        second_carrier = claim(repo, (path,), "second support carrier")
        candidate_landmark = repo.merge_commit(
            (second_carrier, first),
            "nested adoption drops source support",
            removes=(path,),
        )
        parents = (second_carrier, first)
    elif variant == "permutation-diamond":
        first = repo.merge_commit(
            (authority_child, carrier),
            "first parent-order support adoption",
            removes=(path,),
        )
        repo.branch("reverse-support-carrier", C)
        reverse_carrier = claim(
            repo, (path,), "reverse parent-order support carrier"
        )
        second = repo.merge_commit(
            (reverse_carrier, authority_child),
            "reverse parent-order support adoption",
            writes={evidence: resolved},
            removes=(path,),
        )
        repo.branch("diamond-support-carrier", C)
        final_carrier = claim(
            repo, (path,), "final diamond support carrier"
        )
        parents = (second, final_carrier, first)
        candidate_landmark = repo.merge_commit(
            parents,
            "join equal support roots through both parent orders",
            writes={evidence: resolved},
            removes=(path,),
        )
    else:
        parents = (carrier, authority_child)
        candidate_landmark = repo.merge_commit(
            parents,
            "reverse supplier support adoption",
            removes=(path,),
        )
    N = feature(repo, f"{label}-new")
    with _fixture_repository_session(repo.root):
        source_problem = RECONCILE.queue_deletion_problem(
            path,
            repo.run("show", f"{authority_parent}:{path}").stdout,
            authority_parent,
            authority_child,
        )
    return _Fixture(
        f"R16-support-{variant}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        variants[variant],
        {
            "variant": variant,
            "authority_parent": authority_parent,
            "authority_child": authority_child,
            "source_parent": source_parent,
            "carrier": carrier,
            "merge_parents": list(parents),
            "source_problem": source_problem,
        },
    )


def r16_earlier_evidence_reversal(root: Path) -> _Fixture:
    """Prove generic root replay cannot authorize an evidence reversal."""
    repo = GitRepository(root)
    initialize(repo)
    label = "r16-earlier-evidence-reversal"
    path = queue_path(label, timing="blocking")
    evidence = evidence_path(label)
    task_id = "2026-08-31-r16-earlier-evidence"
    task_path = f"tasks/1_in-progress/{task_id}/task.md"
    repo.write(evidence, "# Evidence v0\n")
    repo.write(
        path,
        "# Earlier evidence\n\n"
        "**Status:** open\n"
        "**Filed:** 2026-08-31\n"
        "**Action:** repair earlier evidence\n"
        f"**Full context:** `{evidence}`\n"
        f"**Resolution evidence:** `{evidence}`\n"
        "**Blocks now:** operation:release\n",
    )
    repo.write(
        task_path,
        "# Task\n\n"
        "**Claimed-by:** r16-agent\n"
        f"**Queue actions:** `{path}`\n",
    )
    repo.write(str(Path(task_path).with_name("plan.md")), "# Plan\n")
    repo.write(str(Path(task_path).with_name("worklog.md")), "# Worklog\n")
    C = repo.commit("create earlier evidence supplier root")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("earlier-evidence-source", C)
    repo.write(evidence, "# Evidence v1\n")
    repo.commit(f"repair evidence\n\ntask: {task_id}")
    authority_parent = claim(repo, (path,), "claim earlier evidence action")
    repo.remove(path)
    authority_child = repo.commit("delete using admitted earlier evidence")
    repo.branch("earlier-evidence-carrier", C)
    carrier = claim(repo, (path,), "claim stale evidence carrier")
    candidate_landmark = repo.merge_commit(
        (carrier, authority_child),
        "reverse adoption reverts earlier evidence",
        removes=(path,),
    )
    N = feature(repo, f"{label}-new")
    authority_text = repo.run(
        "show", f"{authority_parent}:{path}"
    ).stdout
    with _fixture_repository_session(repo.root):
        source_problem = RECONCILE.queue_deletion_problem(
            path,
            authority_text,
            authority_parent,
            authority_child,
        )
        replay_problem = RECONCILE.queue_deletion_problem(
            path, authority_text, authority_parent, candidate_landmark
        )
    return _Fixture(
        "R16-earlier-landed-evidence-reversal",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "authority_parent": authority_parent,
            "authority_child": authority_child,
            "source_problem": source_problem,
            "replay_problem": replay_problem,
            "expected_evidence": repo.tree_entry_oid(
                authority_child, evidence
            ),
            "reverted_evidence": repo.tree_entry_oid(candidate_landmark, evidence),
        },
    )


def r16_pickup_evolution(
    root: Path, target_status: str, *, drop_artifact: bool = False
) -> _Fixture:
    """Exercise typed monotone pickup support beyond 1_in-progress."""
    allowed = {"2_blocked", "3_in-review", "4_done", "0_backlog"}
    if target_status not in allowed:
        raise ValueError(target_status)
    if drop_artifact and target_status != "3_in-review":
        raise ValueError("artifact-drop control uses the in-review receipt")
    repo = GitRepository(root)
    initialize(repo)
    slug = target_status.replace("_", "-")
    pickup, backlog, active = add_pickup(repo, f"r16-{slug}")
    task_id = Path(backlog).parts[2]
    C = repo.commit("create pickup evolution root")
    repo.branch("old", C)
    O = feature(repo, f"r16-pickup-{slug}-old")
    repo.branch("pickup-source", C)
    complete_pickup(repo, pickup, backlog, active)
    authority_child = repo.commit("complete pickup authority edge")
    destination = f"tasks/{target_status}/{task_id}/task.md"
    repo.move(active, destination)
    if target_status in {"3_in-review", "4_done"}:
        repo.write(
            str(Path(destination).with_name("verification.md")),
            "# Verification\n",
        )
    source_parent = repo.commit("evolve picked-up task monotonically")
    task_dir = Path(destination).parent
    task_writes = {
        path.relative_to(repo.root).as_posix(): path.read_text()
        for path in sorted((repo.root / task_dir).iterdir())
        if path.is_file()
        and path.name in RECONCILE.TASK_ARTIFACT_NAMES
    }
    adoption_writes = dict(task_writes)
    if drop_artifact:
        adoption_writes.pop(
            str(task_dir / "verification.md"), None
        )
    repo.branch("pickup-carrier", C)
    carrier = feature(repo, f"r16-pickup-{slug}-carrier")
    candidate_landmark = repo.merge_commit(
        (carrier, source_parent),
        "copy current pickup support projection",
        writes=adoption_writes,
        removes=(pickup, backlog, active),
    )
    N = feature(repo, f"r16-pickup-{slug}-new")
    return _Fixture(
        f"R16-pickup-evolution-{slug}"
        + ("-drop-artifact" if drop_artifact else ""),
        repo,
        C,
        O,
        candidate_landmark,
        N,
        (
            "blocking-finding"
            if target_status == "0_backlog" or drop_artifact
            else "no-finding"
        ),
        {
            "target_status": target_status,
            "authority_child": authority_child,
            "source_parent": source_parent,
            "carrier": carrier,
            "task_path": destination,
            "task_artifacts": sorted(task_writes),
            "drop_artifact": drop_artifact,
        },
    )


def p19_identities(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    text = agent_text("p19")
    first = add_agent(
        repo, "p19", path=queue_path("p19-first"), text=text
    )
    second = queue_path("p19-second")
    repo.write(second, text)
    bad = "message-queue/needs-agent/requests/p19-bad.md"
    add_agent(repo, "p19-bad", path=bad)
    retry = generated_retry(repo, bad)
    C = repo.commit("create production identity fixtures")
    repo.branch("old", C)
    O = feature(repo, "p19-old")
    repo.branch("candidate", C)
    candidate_landmark = feature(repo, "p19-base")
    N = feature(repo, "p19-old")
    ordinary_first = RECONCILE.queue_action_identity(first, text)
    ordinary_second = RECONCILE.queue_action_identity(second, text)
    changed = RECONCILE.queue_action_identity(
        second,
        agent_text("p19", action="different immutable payload"),
    )
    retry_text = repo.read(retry)
    retry_identity = RECONCILE.queue_action_identity(retry, retry_text)
    return _Fixture(
        "P19-production-identities",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "ordinary_identity_path_independent": (
                ordinary_first == ordinary_second
            ),
            "ordinary_payload_change_distinct": (
                ordinary_first != changed
            ),
            "ordinary_identity": list(ordinary_first),
            "generated_retry_identity": list(retry_identity),
            "duplicate_paths": [first, second],
            "duplicate_multiplicity": 2,
        },
    )


def p20_lifecycle_types(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    agent_label = "p20-agent"
    human_label = "p20-human"
    agent = add_agent(repo, agent_label)
    human = add_human(repo, human_label)
    bad = "message-queue/needs-agent/requests/p20-bad.md"
    add_agent(repo, "p20-bad", path=bad)
    retry = generated_retry(repo, bad)
    pickup, backlog, active = add_pickup(repo, "p20")
    C = repo.commit("create lifecycle-type actions at C")
    repo.branch("old", C)
    O = feature(repo, "p20-old")
    repo.branch("candidate", C)
    answer(repo, human, "approve")
    claim(repo, (agent, human), "claim agent and human actions")
    fixed = queue_path("p20-bad")
    repo.move(bad, fixed)
    complete_pickup(repo, pickup, backlog, active)
    repo.write(
        evidence_path(agent_label),
        "# Evidence p20-agent: resolved\n",
    )
    repo.write(
        evidence_path(human_label),
        "# Evidence p20-human: resolved\n",
    )
    repo.remove(agent)
    repo.remove(human)
    repo.remove(retry)
    candidate_landmark = repo.commit("resolve every lifecycle type")
    N = feature(repo, "p20-old")
    return _Fixture(
        "P20-lifecycle-types",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {
            "validator_leaves": [
                "ordinary-agent",
                "human-decision",
                "generated-retry-special",
                "task-pickup-special",
            ],
            "pickup_path": pickup,
            "retry_path": retry,
        },
    )


def pcx17_cherry_pick(root: Path, mode: str) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, f"pcx17-{mode}")
    label = f"pcx17-{mode}"
    C = repo.commit("create cherry-pick C")
    repo.branch("old", C)
    O = feature(repo, f"{label}-old")
    repo.branch("source", C)
    K = claim(repo, (path,), "K claim")
    D = delete_with_evidence(repo, ((label, path),), "D deletion")
    repo.branch("candidate", C)
    if mode == "complete":
        repo.run(
            "cherry-pick", K, D, env=repo._commit_environment()
        )
        candidate_landmark = repo.oid("HEAD")
        expected = "no-finding"
    elif mode == "deletion-only":
        conflicted = repo.run("cherry-pick", D, check=False)
        if conflicted.returncode == 0:
            raise AssertionError("deletion-only replay must conflict with C")
        repo.remove(path)
        repo.write(evidence_path(label), "resolved deletion-only replay\n")
        repo.run("add", "-A")
        repo.run(
            "cherry-pick",
            "--continue",
            env=repo._commit_environment(),
        )
        candidate_landmark = repo.oid("HEAD")
        expected = "blocking-finding"
    elif mode == "squash":
        final_tree = repo.oid(f"{D}^{{tree}}")
        candidate_landmark = repo.commit_tree(
            final_tree, "squash claim and deletion", C
        )
        repo.branch("candidate-squash", candidate_landmark)
        expected = "blocking-finding"
    else:
        raise ValueError(mode)
    N = feature(repo, f"{label}-old")
    return _Fixture(
        (
            "P21-PCX-17c-squash-erasure"
            if mode == "squash"
            else f"PCX-17-{mode}-cherry-pick"
        ),
        repo,
        C,
        O,
        candidate_landmark,
        N,
        expected,
        {"source_K": K, "source_D": D, "mode": mode},
    )


def pcx18_many_actions(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    actions = []
    for index in range(16):
        label = f"many-{index:02d}"
        actions.append((label, add_agent(repo, label)))
    C = repo.commit("create sixteen actions at C")
    repo.branch("old", C)
    O = feature(repo, "many-old")
    repo.branch("candidate", C)
    claim(
        repo,
        tuple(path for _label, path in actions[:8]),
        "claim eight of sixteen actions",
    )
    for index in range(128):
        repo.write(
            f"unrelated/{index:03d}.txt", f"unrelated {index}\n"
        )
        repo.commit(f"unrelated commit {index:03d}")
    for label, path in actions:
        repo.write(
            evidence_path(label), f"# Evidence {label}: resolved\n"
        )
        repo.remove(path)
    candidate_landmark = repo.commit("delete all sixteen actions")
    N = feature(repo, "many-old")
    return _Fixture(
        "P22-PCX-18-one-pass-many-actions",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {
            "history_commits": 128,
            "disappeared_actions": 16,
            "expected_authorized": 8,
            "expected_findings": 8,
        },
    )


def r17_precharge_many_actions_budget(root: Path) -> _Fixture:
    """Refuse P22's first over-budget operation before later work starts."""
    fixture = pcx18_many_actions(root)
    reference = _run_classifier(fixture)["metrics"]
    fixture.scenario = "R17-precharge-P22-budget"
    fixture.expected = "blocking-finding"
    fixture.budget_limits = {"object_reads": 133}
    fixture.details.update(
        {
            "budget_counter_policy": "charge before measured work",
            "budget_limit": 133,
            "budget_counter": "object_reads",
            "later_counters_unchanged": [
                "authority_calls",
                "support_adoption_checks",
                "support_certificate_calls",
                "support_serialized_bytes",
            ],
            "posthoc_reference_metrics": reference,
            "transactional_zero_results": True,
        }
    )
    return fixture


def p18_missing_tip(root: Path) -> _Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18a-missing-tip", valid=True
    )
    fixture.O = "f" * len(fixture.O)
    fixture.expected = "unreadable"
    return fixture


def p18_noncommit_tip(root: Path) -> _Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18b-noncommit-tip", valid=True
    )
    fixture.O = fixture.repo.run(
        "hash-object", "-w", "--stdin", input_text="not a commit\n"
    ).stdout.strip()
    fixture.expected = "unreadable"
    return fixture


def p18_unrelated_tip(root: Path) -> _Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18c-unrelated-tip", valid=True
    )
    empty = fixture.repo.run("mktree", input_text="").stdout.strip()
    unrelated = fixture.repo.commit_tree(empty, "unrelated root")
    fixture.N = fixture.repo.commit_tree(
        empty, "unrelated child", unrelated
    )
    fixture.candidate_landmark = unrelated
    fixture.expected = "unreadable"
    return fixture


def p18_shallow(root: Path) -> _Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18d-shallow-required-region", valid=True
    )
    (fixture.repo.root / ".git/shallow").write_text(
        fixture.expected_C + "\n", encoding="ascii"
    )
    fixture.expected = "unreadable"
    return fixture


def p18_missing_blob(root: Path) -> _Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18e-missing-queue-blob", valid=True
    )
    path = queue_path(fixture.scenario.lower())
    blob = fixture.repo.tree_entry_oid(fixture.expected_C, path)
    fixture.repo.hide_loose_object(blob)
    fixture.expected = "unreadable"
    fixture.details["missing_blob_oid"] = blob
    return fixture


def p18_missing_tree(root: Path) -> _Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18f-missing-queue-tree", valid=True
    )
    tree = fixture.repo.tree_entry_oid(
        fixture.expected_C, "message-queue"
    )
    fixture.repo.hide_loose_object(tree)
    fixture.expected = "unreadable"
    fixture.details["missing_tree_oid"] = tree
    return fixture


def p18_multiple_bases(root: Path) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    add_agent(repo, "p18g")
    R = repo.commit("create criss-cross root")
    repo.branch("a", R)
    A = feature(repo, "p18g-a")
    repo.branch("b", R)
    B = feature(repo, "p18g-b")
    repo.branch("combined", A)
    repo.write("features/p18g-b.md", "# Feature p18g-b\n")
    repo.run("add", "-A")
    tree = repo.run("write-tree").stdout.strip()
    X = repo.commit_tree(tree, "criss-cross X", A, B)
    Y = repo.commit_tree(tree, "criss-cross Y", B, A)
    repo.branch("old", X)
    O = feature(repo, "p18g-old")
    repo.branch("candidate", Y)
    candidate_landmark = feature(repo, "p18g-base")
    N = feature(repo, "p18g-old")
    return _Fixture(
        "P18g-multiple-merge-bases",
        repo,
        R,
        O,
        candidate_landmark,
        N,
        "unreadable",
        {"expected_merge_bases": [A, B]},
    )


def pcx19_missing_claim_blob(root: Path) -> _Fixture:
    fixture = ordinary_linear_fixture(
        root, "PCX-19-missing-claim-blob-recovery", valid=True
    )
    label = fixture.scenario.lower()
    path = queue_path(label)
    parents = fixture.repo.run(
        "rev-list", "--parents", "-n", "1", fixture.candidate_landmark
    ).stdout.split()
    claim_commit = parents[1]
    blob = fixture.repo.tree_entry_oid(claim_commit, path)
    hidden, restored = fixture.repo.hide_loose_object(blob)
    fixture.details.update(
        {
            "claim_commit": claim_commit,
            "missing_claim_blob_oid": blob,
            "restore_hidden": hidden.relative_to(
                fixture.repo.root
            ).as_posix(),
            "restore_target": restored.relative_to(
                fixture.repo.root
            ).as_posix(),
        }
    )
    fixture.expected = "no-finding"
    return fixture


def budget_fixture(root: Path, *, overflow: bool) -> _Fixture:
    scenario = (
        "PCX-20b-budget-overflow"
        if overflow
        else "PCX-20a-budget-below-limit"
    )
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, scenario.lower())
    C = repo.commit("create budget C")
    repo.branch("old", C)
    O = feature(repo, "budget-old")
    repo.branch("candidate", C)
    claim(repo, (path,))
    for index in range(5 + int(overflow)):
        feature(repo, f"budget-unrelated-{index}")
    candidate_landmark = delete_with_evidence(
        repo, ((scenario.lower(), path),), "budget fixture deletion"
    )
    N = feature(repo, "budget-old")
    fixture = _Fixture(
        scenario,
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
    )
    probe = _run_classifier(fixture)
    measured = probe["metrics"]
    max_work = max(measured.values())
    fixture.expected = "blocking-finding" if overflow else "no-finding"
    fixture.budget_limit = max_work - 1 if overflow else max_work
    fixture.details = {
        "measured_work_counters": measured,
        "measured_max_work": max_work,
        "max_work_counter_names": sorted(
            name for name, value in measured.items() if value == max_work
        ),
        "demonstration_limit": fixture.budget_limit,
        "overflow_by_one": overflow,
        "budget_counter_policy": "every emitted work counter",
    }
    return fixture


def _configure_typed_budget_fixture(
    fixture: _Fixture,
    *,
    scenario: str,
    counter: str,
    overflow: bool,
) -> _Fixture:
    """Derive one deterministic exact or exact-minus-one typed work cap."""
    probe = _run_classifier(fixture)
    if probe["classification"] != fixture.expected:
        raise AssertionError(
            f"unbudgeted probe for {scenario} changed classification"
        )
    measured = probe["metrics"][counter]
    if measured <= 0:
        raise AssertionError(f"{scenario} did not exercise {counter}")
    limit = measured - int(overflow)
    fixture.scenario = scenario
    fixture.expected = "blocking-finding" if overflow else fixture.expected
    fixture.budget_limits = {counter: limit}
    fixture.details.update(
        {
            "typed_budget_counter": counter,
            "typed_budget_limit": limit,
            "unbudgeted_counter_value": measured,
            "overflow_by_one": overflow,
            "transactional_zero_results": overflow,
        }
    )
    return fixture


def r17_large_object_budget(root: Path, *, overflow: bool) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r17-large-object"
    path = add_agent(repo, label)
    text = repo.read(path)
    initial_bytes = 999_995
    target_bytes = 1_000_000
    padding = initial_bytes - len(text.encode("utf-8"))
    if padding <= 0:
        raise AssertionError("large-object fixture base unexpectedly large")
    repo.write(path, text + ("x" * padding))
    if len(repo.read(path).encode("utf-8")) != initial_bytes:
        raise AssertionError("large-object fixture initial size drifted")
    C = repo.commit("create one million byte queue object")
    repo.branch("old", C)
    O = feature(repo, "r17-large-object-old")
    repo.branch("candidate", C)
    claim(repo, (path,))
    candidate_landmark = delete_with_evidence(
        repo, ((label, path),), "delete large queue object"
    )
    N = feature(repo, "r17-large-object-old")
    fixture = _Fixture(
        "probe-large-object",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {"largest_queue_blob_bytes": target_bytes},
    )
    return _configure_typed_budget_fixture(
        fixture,
        scenario=(
            "R17-object-payload-peak-plus-one-refused"
            if overflow
            else "R17-object-payload-peak-exact"
        ),
        counter="object_payload_peak_bytes",
        overflow=overflow,
    )


def r17_wide_tree_budget(root: Path, *, overflow: bool) -> _Fixture:
    repo = GitRepository(root)
    initialize(repo)
    label = "r17-wide-tree"
    path = add_agent(repo, label)
    for index in range(1000):
        repo.write(f"wide-tree/{index:04d}.txt", f"{index}\n")
    C = repo.commit("create one thousand path tree")
    repo.branch("old", C)
    O = feature(repo, "r17-wide-tree-old")
    repo.branch("candidate", C)
    claim(repo, (path,))
    candidate_landmark = delete_with_evidence(
        repo, ((label, path),), "delete action beside wide tree"
    )
    N = feature(repo, "r17-wide-tree-old")
    fixture = _Fixture(
        "probe-wide-tree",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {"fixture_leaf_paths": 1000},
    )
    return _configure_typed_budget_fixture(
        fixture,
        scenario=(
            "R17-flat-tree-peak-plus-one-refused"
            if overflow
            else "R17-flat-tree-peak-exact"
        ),
        counter="flat_tree_peak_paths",
        overflow=overflow,
    )


def r17_support_serialization_budget(
    root: Path, *, overflow: bool
) -> _Fixture:
    fixture = ordinary_linear_fixture(
        root, "probe-support-serialization", valid=True
    )
    return _configure_typed_budget_fixture(
        fixture,
        scenario=(
            "R17-support-serialized-plus-one-refused"
            if overflow
            else "R17-support-serialized-exact"
        ),
        counter="support_serialized_bytes",
        overflow=overflow,
    )


def r17_dynamic_support_budget(root: Path, *, overflow: bool) -> _Fixture:
    fixture = pcx16_task_pickup(root)
    return _configure_typed_budget_fixture(
        fixture,
        scenario=(
            "R17-dynamic-support-traversal-plus-one-refused"
            if overflow
            else "R17-dynamic-support-traversal-exact"
        ),
        counter="dynamic_support_paths_traversed",
        overflow=overflow,
    )


def _r18_origin_fixture(
    root: Path,
    *,
    case: str,
    strategy: str = "U",
    reverse_parents: bool = False,
    interpretation: str | None = None,
) -> _Fixture:
    """Build one absent-at-C, live-incarnation Strategy U/B fixture."""
    repo = GitRepository(root)
    initialize(repo)
    label = "r18-origin-action"
    path = queue_path(label)
    action_text = agent_text(label)
    target = evidence_path(label)

    if case == "generated-retry":
        bad = "message-queue/needs-agent/requests/bad.md"
        add_agent(repo, "r18-origin-bad", path=bad)
    C = repo.commit("create origin-comparison C without target identity")

    landmarks: dict[str, str] = {}

    def add_plain_action(*, status: str = "open", at_path: str = path):
        repo.write(target, f"# Evidence {label}: pending\n")
        repo.write(at_path, agent_text(label, status=status))
        return at_path

    def add_kind(kind: str):
        if kind == "agent":
            return add_plain_action()
        if kind == "human":
            return add_human(repo, label)
        if kind == "review":
            review_target = evidence_path("r18-review-target")
            review_payload = "# Review target\n"
            repo.write(review_target, review_payload)
            return add_review(
                repo,
                label,
                status="waiting",
                target=review_target,
                revision=review_revision(review_payload),
            )
        if kind == "generated-retry":
            return generated_retry(
                repo, "message-queue/needs-agent/requests/bad.md"
            )
        if kind == "task-pickup":
            pickup, _backlog, _active = add_pickup(repo, label)
            return pickup
        raise ValueError(f"unsupported origin fixture kind {kind}")

    def simple_arm(branch: str, kind: str = "agent"):
        repo.branch(branch, C)
        action_path = add_kind(kind)
        birth = repo.commit(f"birth target identity on {branch}")
        landmarks[f"{branch}_birth"] = birth
        landmarks[f"{branch}_path"] = action_path
        return action_path, birth

    def claimed_arm(branch: str, *, transient: str | None = None):
        action_path, birth = simple_arm(branch)
        claim_oid = claim(
            repo, (action_path,), f"claim target identity on {branch}"
        )
        landmarks[f"{branch}_claim"] = claim_oid
        if transient == "claim-removal":
            claimed_text = repo.read(action_path)
            repo.write(
                action_path,
                claimed_text.replace(
                    "**Status:** in-repair", "**Status:** open", 1
                ),
            )
            landmarks[f"{branch}_regression"] = repo.commit(
                f"remove claim on {branch}"
            )
            repo.write(action_path, claimed_text)
            landmarks[f"{branch}_restoration"] = repo.commit(
                f"restore claim on {branch}"
            )
        return action_path, birth

    if case == "O-only-post-C-loss":
        simple_arm("old")
        O = repo.oid("HEAD")
        repo.branch("candidate", C)
        N = feature(repo, "origin-candidate-without-old-only-action")
    elif case == "agent-born-claimed":
        claimed_arm("old")
        O = repo.oid("HEAD")
        repo.branch("candidate", C)
        add_plain_action(status="in-repair")
        candidate_birth = repo.commit(
            "illegally birth claimed agent action"
        )
        landmarks["candidate_birth"] = candidate_birth
        N = candidate_birth
    elif case == "human-born-answered":
        old_path, _birth = simple_arm("old", "human")
        answer(repo, old_path, "approve")
        O = repo.oid("HEAD")
        repo.branch("candidate", C)
        candidate_path = add_human(repo, label)
        repo.write(
            candidate_path,
            repo.read(candidate_path).replace(
                "**Your answer:** ______",
                "**Your answer:** approve",
                1,
            ),
        )
        candidate_birth = repo.commit(
            "illegally birth answered human action"
        )
        landmarks["candidate_birth"] = candidate_birth
        N = candidate_birth
    elif case == "review-publication-equivalence":
        review_target = evidence_path("r18-review-target")
        review_payload = "# Review target\n"
        revision = review_revision(review_payload)
        repo.branch("old", C)
        old_path = add_review(
            repo,
            label,
            status="awaiting-artifact",
            target="pending",
            revision="pending",
        )
        old_birth = repo.commit(
            "birth review before its artifact is published"
        )
        repo.write(review_target, review_payload)
        old_publication = publish_review(
            repo, old_path, review_target, revision
        )
        O = old_publication
        repo.branch("candidate", C)
        repo.write(review_target, review_payload)
        add_review(
            repo,
            label,
            status="waiting",
            target=review_target,
            revision=revision,
        )
        candidate_birth = repo.commit(
            "birth same unanswered review after artifact publication"
        )
        landmarks.update(
            {
                "old_birth": old_birth,
                "old_publication": old_publication,
                "candidate_birth": candidate_birth,
            }
        )
        N = candidate_birth
    elif case in {
        "review-compatible-merge",
        "review-compatible-source-low",
        "review-compatible-source-high",
        "review-three-carrying-parents",
        "review-two-valid-sources",
        "review-duplicate-parent-header",
        "review-incompatible-carrier",
    }:
        review_target = evidence_path("r19-review-merge-target")
        review_payload = "# R19 review merge target\n"
        revision = review_revision(review_payload)
        incompatible = case == "review-incompatible-carrier"
        carrier_count = 2 if case == "review-three-carrying-parents" else 1
        explicit_source_count = (
            2 if case == "review-two-valid-sources" else 1
        )
        lexical_relation = (
            "source-low"
            if case in {
                "review-compatible-source-low",
                "review-duplicate-parent-header",
            }
            else "source-high"
            if case == "review-compatible-source-high"
            else None
        )

        repo.branch("old", C)
        repo.write(review_target, review_payload)
        add_review(
            repo,
            label,
            status="waiting",
            target=review_target,
            revision=revision,
        )
        O = repo.commit("birth published review on old arm")

        repo.branch("candidate-birth", C)
        candidate_path = add_review(
            repo,
            label,
            status="awaiting-artifact",
            target="pending",
            revision="pending",
        )
        candidate_birth = repo.commit(
            "birth pending review before compatible merge"
        )
        repo.branch("candidate-source", candidate_birth)
        repo.write(review_target, review_payload)
        source = publish_review(
            repo, candidate_path, review_target, revision
        )
        source_text = repo.read(candidate_path)
        source_tree = repo.oid(f"{source}^{{tree}}")
        sources = [source]
        if explicit_source_count == 2:
            sources.append(
                repo.commit_tree(
                    source_tree,
                    "independent second valid review publication source",
                    candidate_birth,
                )
            )

        birth_tree = repo.oid(f"{candidate_birth}^{{tree}}")
        carriers = []
        conflicting_target = evidence_path("r19-review-merge-conflict")
        if incompatible:
            conflicting_payload = "# Conflicting review target\n"
            repo.branch("candidate-incompatible-carrier", candidate_birth)
            repo.write(conflicting_target, conflicting_payload)
            carriers.append(
                publish_review(
                    repo,
                    candidate_path,
                    conflicting_target,
                    review_revision(conflicting_payload),
                )
            )
        else:
            # Each carrier is a distinct real commit with the unchanged pending
            # review tree.  Canonical selection, rather than fixture position,
            # decides which production-valid edge is the source.
            for carrier_index in range(carrier_count):
                selected = None
                for nonce in range(4096):
                    candidate = repo.commit_tree(
                        birth_tree,
                        "carry pending review without authoring publication "
                        f"{carrier_index}:{nonce}",
                        candidate_birth,
                    )
                    if lexical_relation is None or (
                        lexical_relation == "source-low" and source < candidate
                    ) or (
                        lexical_relation == "source-high" and source > candidate
                    ):
                        selected = candidate
                        break
                if selected is None:
                    raise AssertionError(
                        "could not construct requested source/carrier OID order"
                    )
                carriers.append(selected)

        parents = tuple(sources + carriers)
        if case == "review-duplicate-parent-header":
            # A duplicate source parent header is a real, Git-readable commit
            # shape.  The proof treats it as one logical parent edge rather
            # than allowing the repeated edge to erase the source role.
            parents = (source, source, *carriers)
        if reverse_parents:
            parents = tuple(reversed(parents))
        if case == "review-duplicate-parent-header":
            merge = repo.raw_commit_with_parent_headers(
                source_tree,
                "merge duplicate source headers with compatible carrier",
                *parents,
            )
        else:
            merge = repo.merge_commit(
                parents,
                "merge published source with compatible pending carrier",
                writes={
                    candidate_path: source_text,
                    review_target: review_payload,
                },
                removes=((conflicting_target,) if incompatible else ()),
            )
        if repo.oid(f"{merge}^{{tree}}") != source_tree:
            raise AssertionError("review compatible merge tree drifted")
        raw_parent_headers = [
            line[7:]
            for line in repo.run("cat-file", "commit", merge).stdout.splitlines()
            if line.startswith("parent ")
        ]
        fsck = repo.run(
            "fsck", "--strict", "--no-dangling", merge, check=False
        )
        if fsck.returncode:
            raise AssertionError(
                "duplicate-parent fixture is not accepted by git fsck: "
                + fsck.stderr.strip()
            )
        if case == "review-duplicate-parent-header" and not (
            len(raw_parent_headers) == 3
            and len(set(raw_parent_headers)) == 2
            and raw_parent_headers.count(source) == 2
        ):
            raise AssertionError(
                "raw duplicate-parent fixture lost header multiplicity"
            )
        N = merge
        landmarks.update(
            {
                "candidate_birth": candidate_birth,
                "source": source,
                "sources": sources,
                "carriers": carriers,
                "merge": merge,
                "lexical_relation": lexical_relation,
                "incompatible": incompatible,
                "duplicate_parent_header": (
                    case == "review-duplicate-parent-header"
                ),
                "fsck_returncode": fsck.returncode,
                "raw_parent_headers": raw_parent_headers,
                "logical_parent_oids": sorted(set(raw_parent_headers)),
            }
        )
    elif case == "exact-cherry-pick":
        _old_path, old_birth = simple_arm("old")
        O = old_birth
        repo.branch("candidate", C)
        feature(repo, "origin-base-advance-before-cherry-pick")
        result = repo.run(
            "cherry-pick", old_birth, env=repo._commit_environment()
        )
        if result.returncode:
            raise RuntimeError(result.stderr)
        N = repo.oid("HEAD")
        landmarks["candidate_birth"] = N
    elif case in {"normal-base-advance-replay", "independent-birth"}:
        simple_arm("old")
        O = repo.oid("HEAD")
        repo.branch("candidate", C)
        if case == "normal-base-advance-replay":
            feature(repo, "origin-normal-base-advance")
        add_plain_action()
        candidate_birth = repo.commit(
            "independently reproduce target addition"
        )
        landmarks["candidate_birth"] = candidate_birth
        N = candidate_birth
    elif case == "schema-invalid-birth":
        endpoints = {}
        for arm in ("old", "candidate"):
            repo.branch(arm, C)
            repo.write(target, f"# Evidence {label}: pending\n")
            repo.write(
                path,
                action_text.replace(
                    "**Filed:** 2026-08-31",
                    "**Filed:** not-a-calendar-date",
                    1,
                ),
            )
            endpoints[arm] = repo.commit(
                f"birth schema-invalid target on {arm}"
            )
            landmarks[f"{arm}_birth"] = endpoints[arm]
        O, N = endpoints["old"], endpoints["candidate"]
    elif case == "delete-recreate-O":
        old_path, _birth = simple_arm("old")
        saved = repo.read(old_path)
        repo.remove(old_path)
        landmarks["old_loss"] = repo.commit("delete old-arm incarnation")
        repo.write(old_path, saved)
        landmarks["old_rebirth"] = repo.commit(
            "recreate old-arm incarnation"
        )
        O = repo.oid("HEAD")
        simple_arm("candidate")
        N = repo.oid("HEAD")
    elif case == "delete-recreate-N":
        simple_arm("old")
        O = repo.oid("HEAD")
        candidate_path, _birth = simple_arm("candidate")
        saved = repo.read(candidate_path)
        repo.remove(candidate_path)
        landmarks["candidate_loss"] = repo.commit(
            "delete candidate-arm incarnation"
        )
        repo.write(candidate_path, saved)
        landmarks["candidate_rebirth"] = repo.commit(
            "recreate candidate-arm incarnation"
        )
        N = repo.oid("HEAD")
    elif case == "transient-protected-mutation":
        old_path, _birth = simple_arm("old")
        saved = repo.read(old_path)
        repo.write(old_path, saved + "<!-- protected transient bytes -->\n")
        landmarks["old_mutation"] = repo.commit(
            "transiently mutate frozen bytes"
        )
        repo.write(old_path, saved)
        landmarks["old_restoration"] = repo.commit(
            "restore frozen bytes"
        )
        O = repo.oid("HEAD")
        simple_arm("candidate")
        N = repo.oid("HEAD")
    elif case == "human-response-restoration":
        old_path, _birth = simple_arm("old", "human")
        answer(repo, old_path, "keep this exact response")
        answered = repo.read(old_path)
        repo.write(
            old_path,
            answered.replace(
                "**Your answer:** keep this exact response",
                "**Your answer:** ______",
                1,
            ),
        )
        landmarks["old_response_loss"] = repo.commit(
            "remove concrete human response"
        )
        repo.write(old_path, answered)
        landmarks["old_response_restoration"] = repo.commit(
            "restore concrete human response"
        )
        O = repo.oid("HEAD")
        candidate_path, _birth = simple_arm("candidate", "human")
        answer(repo, candidate_path, "keep this exact response")
        N = repo.oid("HEAD")
    elif case == "review-binding-restoration":
        old_path, _birth = simple_arm("old", "review")
        answer_review(repo, old_path, "approve exact target")
        claim_review(repo, old_path)
        bound = repo.read(old_path)
        repo.write(
            old_path,
            bound.replace(
                f"**Review target:** `{evidence_path('r18-review-target')}`",
                "**Review target:** `docs/different-target.md`",
                1,
            ),
        )
        landmarks["old_binding_loss"] = repo.commit(
            "replace concrete review target"
        )
        repo.write(old_path, bound)
        landmarks["old_binding_restoration"] = repo.commit(
            "restore concrete review target"
        )
        O = repo.oid("HEAD")
        candidate_path, _birth = simple_arm("candidate", "review")
        answer_review(repo, candidate_path, "approve exact target")
        claim_review(repo, candidate_path)
        N = repo.oid("HEAD")
    elif case == "claim-restoration":
        claimed_arm("old", transient="claim-removal")
        O = repo.oid("HEAD")
        claimed_arm("candidate")
        N = repo.oid("HEAD")
    elif case == "endpoint-regression":
        claimed_arm("old")
        O = repo.oid("HEAD")
        simple_arm("candidate")
        N = repo.oid("HEAD")
    elif case == "second-birth":
        simple_arm("old")
        O = repo.oid("HEAD")
        repo.branch("candidate-left", C)
        add_plain_action(at_path=path)
        left = repo.commit("first candidate-arm birth")
        repo.branch("candidate-right", C)
        second_path = queue_path("r18-origin-action-copy")
        repo.write(second_path, action_text)
        repo.write(target, f"# Evidence {label}: pending\n")
        right = repo.commit("second candidate-arm birth")
        parents = (right, left) if reverse_parents else (left, right)
        N = repo.merge_commit(parents, "merge two independently born carriers")
        landmarks.update({"candidate_birth": left, "second_birth": right})
    elif case == "multiplicity":
        simple_arm("old")
        O = repo.oid("HEAD")
        candidate_path, _birth = simple_arm("candidate")
        duplicate_path = queue_path("r18-origin-action-copy")
        repo.write(duplicate_path, repo.read(candidate_path))
        landmarks["candidate_multiplicity"] = repo.commit(
            "temporarily duplicate production identity"
        )
        repo.remove(duplicate_path)
        landmarks["candidate_singleton_restored"] = repo.commit(
            "restore singleton production identity"
        )
        N = repo.oid("HEAD")
    elif case == "outside-collision":
        simple_arm("old")
        O = repo.oid("HEAD")
        simple_arm("candidate")
        local = repo.oid("HEAD")
        tree = repo.run("write-tree").stdout.strip()
        outside = repo.commit_tree(
            tree, "unrelated outside-C carrier with same identity"
        )
        N = repo.merge_commit(
            (local, outside), "merge outside-C identity collision"
        )
        landmarks.update({"outside": outside, "candidate_birth": local})
    elif case == "neutral-pre-origin-merge":
        endpoints = {}
        for arm in ("old", "candidate"):
            repo.branch(f"{arm}-neutral-left", C)
            left = feature(repo, f"{arm}-neutral-left")
            repo.branch(f"{arm}-neutral-right", C)
            right = feature(repo, f"{arm}-neutral-right")
            parents = (right, left) if reverse_parents else (left, right)
            merge = repo.merge_commit(
                parents, f"merge {arm} pre-origin neutral parents"
            )
            add_plain_action()
            birth = repo.commit(f"birth target after {arm} neutral merge")
            endpoints[arm] = birth
            landmarks[f"{arm}_prebirth_merge"] = merge
            landmarks[f"{arm}_birth"] = birth
        O, N = endpoints["old"], endpoints["candidate"]
    elif case == "inherited-then-deleted-merge-arm":
        simple_arm("old")
        O = repo.oid("HEAD")
        candidate_path, birth = simple_arm("candidate")
        live = feature(repo, "origin-live-inherited-arm")
        repo.branch("candidate-lost", birth)
        repo.remove(candidate_path)
        lost = repo.commit("delete inherited candidate-arm incarnation")
        N = repo.merge_commit(
            (live, lost), "merge live and inherited-then-deleted arms"
        )
        landmarks.update({"candidate_live": live, "candidate_loss": lost})
    elif case == "rename-timing-move":
        endpoints = {}
        for arm in ("old", "candidate"):
            action_path, _birth = simple_arm(arm)
            moved = queue_path(label, timing="future-blocking")
            repo.move(action_path, moved)
            endpoints[arm] = repo.commit(
                f"rename {arm} delivery timing path"
            )
            landmarks[f"{arm}_moved_path"] = moved
        O, N = endpoints["old"], endpoints["candidate"]
    elif case in {"generated-retry", "task-pickup"}:
        kind = case
        simple_arm("old", kind)
        O = repo.oid("HEAD")
        simple_arm("candidate", kind)
        N = repo.oid("HEAD")
    elif case == "parent-order":
        simple_arm("old")
        O = repo.oid("HEAD")
        _candidate_path, birth = simple_arm("candidate")
        repo.branch("candidate-left", birth)
        left = feature(repo, "origin-parent-order-left")
        repo.branch("candidate-right", birth)
        right = feature(repo, "origin-parent-order-right")
        parents = (right, left) if reverse_parents else (left, right)
        N = repo.merge_commit(parents, "merge equivalent origin carriers")
        landmarks.update({"candidate_left": left, "candidate_right": right})
    elif case == "unreadable-object":
        simple_arm("old")
        O = repo.oid("HEAD")
        candidate_path, _birth = simple_arm("candidate")
        N = repo.oid("HEAD")
        missing_oid = repo.tree_entry_oid(N, candidate_path)
        repo.hide_loose_object(missing_oid)
        landmarks["missing_oid"] = missing_oid
    else:
        raise ValueError(f"unsupported origin fixture case {case}")

    clean_cases = {
        "normal-base-advance-replay",
        "independent-birth",
        "exact-cherry-pick",
        "neutral-pre-origin-merge",
        "rename-timing-move",
        "generated-retry",
        "task-pickup",
        "parent-order",
        "review-compatible-merge",
        "review-compatible-source-low",
        "review-compatible-source-high",
        "review-three-carrying-parents",
        "review-two-valid-sources",
        "review-duplicate-parent-header",
    }
    if case in clean_cases:
        expected = "no-finding"
        expected_code = f"origin-strategy-{strategy}-equivalent-live-incarnation"
        expected_witness = (
            False if case.startswith("review-compatible-")
            or case in {
                "review-three-carrying-parents",
                "review-two-valid-sources",
                "review-duplicate-parent-header",
            }
            else True
        )
    elif case == "review-publication-equivalence":
        expected = "no-finding" if strategy == "U" else "blocking-finding"
        expected_code = (
            "origin-strategy-U-equivalent-live-incarnation"
            if strategy == "U"
            else "origin-birth-witness-mismatch"
        )
        expected_witness = False
    elif case in {"agent-born-claimed", "human-born-answered"}:
        expected = "blocking-finding"
        expected_code = "origin-birth-schema-invalid"
        expected_witness = None
    elif case == "unreadable-object":
        expected = "unreadable"
        expected_code = None
        expected_witness = None
    elif case == "O-only-post-C-loss":
        expected = "blocking-finding"
        expected_code = "not-present-at-C"
        expected_witness = None
    else:
        expected = "blocking-finding"
        expected_code = {
            "delete-recreate-O": "origin-birth-multiplicity",
            "delete-recreate-N": "origin-birth-multiplicity",
            "transient-protected-mutation": "origin-invalid-mutation",
            "human-response-restoration": "origin-invalid-mutation",
            "review-binding-restoration": "origin-invalid-mutation",
            "claim-restoration": "origin-invalid-mutation",
            "endpoint-regression": "origin-endpoint-regression",
            "second-birth": "origin-birth-multiplicity",
            "multiplicity": "origin-arm-multiplicity",
            "outside-collision": "origin-outside-C-collision",
            "schema-invalid-birth": "origin-birth-schema-invalid",
            "inherited-then-deleted-merge-arm": (
                "origin-post-birth-absence"
            ),
            "review-incompatible-carrier": "origin-incompatible-carrier",
        }[case]
        expected_witness = None
    scenario = (
        f"R18-{strategy}-{case}"
        + ("-reversed" if reverse_parents else "")
    )
    return _Fixture(
        scenario,
        repo,
        C,
        O,
        landmarks.get("candidate_birth", N),
        N,
        expected,
        {
            "case": case,
            "expected_origin_code": expected_code,
            "expected_witness_match": expected_witness,
            "interpretation": interpretation,
            "landmarks": landmarks,
            "reverse_parents": reverse_parents,
            "strategy": strategy,
        },
        origin_strategy=strategy,
    )


def _r18_origin_budget_fixture(
    root: Path,
    *,
    counter: str,
    overflow: bool,
) -> _Fixture:
    strategy = "B" if counter == "origin_witness_bytes" else "U"
    fixture = _r18_origin_fixture(
        root,
        case="normal-base-advance-replay",
        strategy=strategy,
    )
    probe = _run_classifier(fixture)
    measured = probe["metrics"][counter]
    if measured <= 0:
        raise AssertionError(f"origin budget counter {counter} was not exercised")
    fixture.scenario = (
        f"R18-{counter.replace('_', '-')}-"
        + ("plus-one-refused" if overflow else "exact")
    )
    fixture.expected = "blocking-finding" if overflow else "no-finding"
    fixture.budget_limits = {counter: measured - int(overflow)}
    fixture.details = {
        "case": "origin-execution-bound",
        "counter": counter,
        "measured": measured,
        "overflow_by_one": overflow,
        "strategy": strategy,
        "typed_budget_limit": measured - int(overflow),
    }
    return fixture


def r19_event_workflow_fixture(
    root: Path,
    *,
    transport: str,
    attack: bool = False,
    failure: str | None = None,
) -> _Fixture:
    """Drive a real typed-U restack from one immutable event payload."""
    if transport not in {
        "local", "pre-push", "push", "pull-request-synchronize"
    }:
        raise ValueError(transport)
    if failure is not None and attack:
        raise ValueError("a workflow fixture cannot be attack and input failure")

    if failure is None:
        fixture = _r18_origin_fixture(
            root,
            case="delete-recreate-N" if attack else "normal-base-advance-replay",
            strategy="U",
        )
    else:
        fixture = ordinary_linear_fixture(
            root,
            f"r19-event-{transport}-{failure}",
            valid=True,
        )
        fixture.expected = "unreadable"

    if transport in {"local", "pre-push"}:
        payload: dict[str, Any] = {"old": fixture.O, "new": fixture.N}
    elif transport == "push":
        payload = {
            "before": fixture.O,
            "after": fixture.N,
            # Deliberately contradictory mutable metadata.  The adapter has no
            # code path that reads this field.
            "github_sha": "1" * 40,
        }
    else:
        payload = {
            "before": fixture.O,
            "after": fixture.N,
            "pull_request": {"head": {"sha": fixture.N}},
            "github_sha": "1" * 40,
        }

    if failure == "missing-old":
        payload.pop("old", None)
        expected_reason = "coverage-unavailable: local.old is missing"
    elif failure == "zero-before":
        payload["before"] = "0" * 40
        expected_reason = "coverage-unavailable: O is the zero OID"
    elif failure == "head-mismatch":
        payload["pull_request"]["head"]["sha"] = fixture.O
        expected_reason = (
            "coverage-unavailable: pull_request.synchronize after does not "
            "equal pull_request.head.sha"
        )
    elif failure is None:
        expected_reason = None
    else:
        raise ValueError(failure)

    disposition = failure or ("blocking-attack" if attack else "normal-restack")
    fixture.scenario = f"R19-WF-{transport}-{disposition}"
    fixture.details = {
        "event_adapter_input": {
            "event_kind": transport,
            "payload": payload,
        },
        "expected_adapter_reason": expected_reason,
        "expected_event_endpoints": {
            "O": fixture.O,
            "N": fixture.N,
        },
        "workflow_attack": attack,
        "workflow_failure": failure,
        "workflow_non_fast_forward": failure is None,
        "workflow_transport": transport,
    }
    return fixture


def _scenario_builders():
    return [
        lambda root: ordinary_linear_fixture(
            root, "P1-direct-linear-valid", valid=True
        ),
        lambda root: ordinary_linear_fixture(
            root, "P2-direct-linear-invalid", valid=False
        ),
        p3_old_loss,
        p4_pre_c_origins,
        p5_duplicate_at_c,
        p6_old_recreate,
        p6_candidate_recreate,
        p7_payload_change,
        p8_timing_move,
        lambda root: direct_merge_fixture(
            root,
            "P9-direct-two-parent-valid",
            parent_count=2,
        ),
        lambda root: direct_merge_fixture(
            root,
            "P10-direct-invalid-parent",
            parent_count=2,
            invalid_parent=1,
        ),
        lambda root: direct_merge_fixture(
            root,
            "P11-direct-three-parent-valid",
            parent_count=3,
        ),
        lambda root: supplier_fixture(
            root,
            "P12-merge-supplier-valid",
            supplier_valid=True,
        ),
        lambda root: supplier_fixture(
            root,
            "P13-merge-supplier-invalid",
            supplier_valid=False,
        ),
        p14_supplier_reintroduced,
        p15_competing_suppliers,
        lambda root: supplier_fixture(
            root,
            "P16-PCX-08-invalid-supplier-claimed-carrier",
            supplier_valid=False,
            carrier_claimed=True,
            merge_changes_evidence=True,
        ),
        p17_post_event_reintroduction,
        p18_missing_tip,
        p18_noncommit_tip,
        p18_unrelated_tip,
        p18_shallow,
        p18_missing_blob,
        p18_missing_tree,
        p18_multiple_bases,
        p19_identities,
        p20_lifecycle_types,
        lambda root: pcx17_cherry_pick(root, "squash"),
        pcx18_many_actions,
        r17_precharge_many_actions_budget,
        lambda root: direct_merge_fixture(
            root,
            "PCX-01-neutral-parent",
            parent_count=2,
            neutral_parent=True,
        ),
        lambda root: direct_merge_fixture(
            root,
            "PCX-02-neutral-plus-invalid-carrier",
            parent_count=2,
            invalid_parent=1,
            neutral_parent=True,
        ),
        pcx03_foreign_identity,
        pcx04_shared_supplier,
        pcx05_competing_later_supplier,
        pcx06_nested_supplier,
        lambda root: supplier_fixture(
            root,
            "PCX-07-overqualified-propagation",
            supplier_valid=True,
            carrier_claimed=True,
        ),
        pcx09_recreated_claimed_bytes,
        pcx10_transient_multiplicity,
        pcx11_distinct_payload,
        pcx12_timing_supplier,
        lambda root: human_supplier_fixture(
            root,
            "PCX-13-conflicting-human-response",
            conflicting_carrier=True,
        ),
        lambda root: human_supplier_fixture(
            root,
            "PCX-14-valid-human-supplier",
            conflicting_carrier=False,
        ),
        pcx15_generated_retry,
        pcx16_task_pickup,
        *[
            (
                lambda root, variant=variant:
                r16_supplier_support_fixture(root, variant)
            )
            for variant in (
                "forward",
                "reverse-drop",
                "reverse-preserved",
                "invalid-source",
                "source-evolution",
                "adoption-drift",
                "nested-drop",
                "permutation-diamond",
            )
        ],
        lambda root: r16_pickup_evolution(
            root, "3_in-review", drop_artifact=True
        ),
        r16_earlier_evidence_reversal,
        *[
            (
                lambda root, target_status=target_status:
                r16_pickup_evolution(root, target_status)
            )
            for target_status in (
                "2_blocked",
                "3_in-review",
                "4_done",
                "0_backlog",
            )
        ],
        lambda root: pcx17_cherry_pick(root, "complete"),
        lambda root: pcx17_cherry_pick(root, "deletion-only"),
        pcx19_missing_claim_blob,
        lambda root: budget_fixture(root, overflow=False),
        lambda root: budget_fixture(root, overflow=True),
        *[
            lambda root, overflow=overflow: r17_large_object_budget(
                root, overflow=overflow
            )
            for overflow in (False, True)
        ],
        *[
            lambda root, overflow=overflow: r17_wide_tree_budget(
                root, overflow=overflow
            )
            for overflow in (False, True)
        ],
        *[
            lambda root, overflow=overflow: r17_support_serialization_budget(
                root, overflow=overflow
            )
            for overflow in (False, True)
        ],
        *[
            lambda root, overflow=overflow: r17_dynamic_support_budget(
                root, overflow=overflow
            )
            for overflow in (False, True)
        ],
        r3_two_invalid_sources,
        r3_invalid_valid_competition,
        r3_valid_plus_invalid_at_N,
        r4_same_root_diamond,
        r4_distinct_root_diamond,
        r4_equal_root_plus_invalid,
        lambda root: r5_reintroduced_supplier_history(
            root, later_valid=False
        ),
        lambda root: r5_reintroduced_supplier_history(
            root, later_valid=True
        ),
        lambda root: r6_all_absent_roots(
            root, first_valid=True, second_kind="invalid"
        ),
        lambda root: r6_all_absent_roots(
            root, first_valid=True, second_kind="ambiguous"
        ),
        lambda root: r6_all_absent_roots(
            root, first_valid=False, second_kind="invalid"
        ),
        r6_same_root_all_absent_wrappers,
        lambda root: r8_human_response_binding(
            root, mode="direct", conflict=True
        ),
        lambda root: r8_human_response_binding(
            root, mode="direct", conflict=False
        ),
        lambda root: r8_human_response_binding(
            root, mode="supplier", conflict=True
        ),
        lambda root: r8_human_response_binding(
            root, mode="supplier", conflict=False
        ),
        lambda root: r8_review_binding(root, divergent=True),
        lambda root: r8_review_binding(root, divergent=False),
        r8_review_terminal_binding_conflict,
        lambda root: r9_review_pending_binding(
            root, mode="direct", pending_field="Review target"
        ),
        lambda root: r9_review_pending_binding(
            root, mode="direct", pending_field="Review revision"
        ),
        lambda root: r9_review_pending_binding(
            root, mode="supplier", pending_field="Review target"
        ),
        lambda root: r9_review_pending_binding(
            root, mode="supplier", pending_field="Review revision"
        ),
        lambda root: r10_malformed_review_binding(
            root,
            mode="direct",
            field="Review target",
            malformed_value="pend\u0131ng",
            slug="backtick-dotless",
        ),
        lambda root: r10_malformed_review_binding(
            root,
            mode="supplier",
            field="Review revision",
            malformed_value="______",
            slug="generic-placeholder",
        ),
        *[
            (
                lambda root, mode=mode, variant=variant:
                r13_review_parent_binding(
                    root, mode=mode, variant=variant
                )
            )
            for mode in ("direct", "supplier")
            for variant in ("identical", "target", "revision", "terminal")
        ],
        *[
            (
                lambda root, variant=variant:
                r13_persisted_state(root, variant)
            )
            for variant in (
                "same-state",
                "response-removal",
                "response-change",
                "review-target-change",
                "review-revision-change",
                "review-outcome-change",
                "claim-loss",
                "pending-fill",
                "terminal-fill",
            )
        ],
        lambda root: r14_review_carrier_binding(
            root,
            mode="direct",
            carrier_variant="same",
            old_answered=False,
        ),
        lambda root: r14_review_carrier_binding(
            root,
            mode="direct",
            carrier_variant="target",
            old_answered=False,
        ),
        lambda root: r14_review_carrier_binding(
            root,
            mode="supplier",
            carrier_variant="pending",
            old_answered=True,
        ),
        lambda root: r14_review_carrier_binding(
            root,
            mode="supplier",
            carrier_variant="same",
            old_answered=True,
        ),
        lambda root: r14_review_carrier_binding(
            root,
            mode="supplier",
            carrier_variant="target",
            old_answered=True,
        ),
        lambda root: r14_review_carrier_binding(
            root,
            mode="supplier",
            carrier_variant="revision",
            old_answered=True,
        ),
        lambda root: r14_review_carrier_binding(
            root,
            mode="supplier",
            carrier_variant="same",
            old_answered=False,
        ),
        lambda root: r14_review_carrier_binding(
            root,
            mode="supplier",
            carrier_variant="target",
            old_answered=False,
        ),
        r14_persisted_hidden_bytes,
        r14_persisted_intermediate_claim,
        r14_persisted_intermediate_review,
        r14_persisted_delete_recreate,
        r14_persisted_review_retraction,
        r14_persisted_first_response_move,
        lambda root: r14_persisted_merge_carriers(
            root, conflict=False
        ),
        lambda root: r14_persisted_merge_carriers(
            root, conflict=True
        ),
        r17_outside_c_neutral_parent,
        lambda root: r17_carry_merge_fixture(
            root, variant="compatible"
        ),
        lambda root: r17_carry_merge_fixture(
            root, variant="compatible", reverse_parents=True
        ),
        lambda root: r17_carry_merge_fixture(
            root, variant="incompatible"
        ),
        lambda root: r17_carry_merge_fixture(
            root, variant="absent-arm"
        ),
        lambda root: r17_carry_merge_fixture(
            root, variant="outside-single"
        ),
        lambda root: r17_carry_merge_fixture(
            root, variant="outside-duplicate"
        ),
        *[
            (
                lambda root, variant=variant, reverse=reverse:
                r17_persisted_carry_fixture(
                    root,
                    variant=variant,
                    reverse_parents=reverse,
                )
            )
            for variant in (
                "outside-single",
                "outside-duplicate",
                "valid-absent-arm",
                "unauthorized-absent-arm",
            )
            for reverse in (False, True)
        ],
        r17_boundary_budget_fixture,
        r17_graph_parent_tokens_exact,
        r17_graph_parent_tokens_plus_one,
        *[
            (
                lambda root, counter=counter, limit=limit, overflow=overflow:
                r17_graph_dimension_budget(
                    root,
                    counter=counter,
                    limit=limit - int(overflow),
                    overflow=overflow,
                )
            )
            for counter, limit in (
                ("graph_output_bytes", 2952),
                ("graph_line_peak_bytes", 2705),
            )
            for overflow in (False, True)
        ],
        *[
            (
                lambda root, case=case:
                r17_workflow_input_case(root, case)
            )
            for case in (
                "fast-forward",
                "pre-pr-push",
                "base-advance-retarget",
                "multiple-pr-api-race",
                "stale-rerun",
                "missing-old",
                "zero-endpoints",
                "pr-synchronize",
            )
        ],
        r17_unreadable_boundary,
        r17_unopened_outside_c_ancestor,
        *[
            (
                lambda root, strategy=strategy:
                _r18_origin_fixture(
                    root,
                    case="normal-base-advance-replay",
                    strategy=strategy,
                )
            )
            for strategy in ("U", "B")
        ],
        *[
            (
                lambda root, strategy=strategy:
                _r18_origin_fixture(
                    root,
                    case="independent-birth",
                    strategy=strategy,
                )
            )
            for strategy in ("U", "B")
        ],
        lambda root: _r18_origin_fixture(
            root, case="O-only-post-C-loss"
        ),
        *[
            (
                lambda root, case=case:
                _r18_origin_fixture(root, case=case)
            )
            for case in (
                "delete-recreate-O",
                "delete-recreate-N",
                "transient-protected-mutation",
                "human-response-restoration",
                "review-binding-restoration",
                "claim-restoration",
                "endpoint-regression",
                "second-birth",
                "multiplicity",
                "outside-collision",
                "schema-invalid-birth",
                "neutral-pre-origin-merge",
                "inherited-then-deleted-merge-arm",
            )
        ],
        *[
            (
                lambda root, strategy=strategy:
                _r18_origin_fixture(
                    root, case="exact-cherry-pick", strategy=strategy
                )
            )
            for strategy in ("U", "B")
        ],
        *[
            (
                lambda root, case=case, strategy=strategy:
                _r18_origin_fixture(
                    root,
                    case=case,
                    strategy=strategy,
                    interpretation=(
                        "illegal claimed state at an agent-action birth"
                        if case == "agent-born-claimed"
                        else "illegal concrete answer at a human-action birth"
                    ),
                )
            )
            for case in ("agent-born-claimed", "human-born-answered")
            for strategy in ("U", "B")
        ],
        *[
            (
                lambda root, strategy=strategy:
                _r18_origin_fixture(
                    root,
                    case="review-publication-equivalence",
                    strategy=strategy,
                    interpretation=(
                        "production-valid awaiting-artifact to waiting "
                        "publication versus a waiting birth"
                    ),
                )
            )
            for strategy in ("U", "B")
        ],
        *[
            (
                lambda root, strategy=strategy:
                _r18_origin_fixture(
                    root, case="rename-timing-move", strategy=strategy
                )
            )
            for strategy in ("U", "B")
        ],
        *[
            (
                lambda root, case=case, strategy=strategy:
                _r18_origin_fixture(root, case=case, strategy=strategy)
            )
            for case in ("generated-retry", "task-pickup")
            for strategy in ("U", "B")
        ],
        lambda root: _r18_origin_fixture(
            root, case="review-compatible-merge"
        ),
        lambda root: _r18_origin_fixture(
            root,
            case="review-compatible-merge",
            reverse_parents=True,
        ),
        *[
            (
                lambda root, case=case, reverse=reverse:
                _r18_origin_fixture(
                    root,
                    case=case,
                    reverse_parents=reverse,
                )
            )
            for case in (
                "review-compatible-source-low",
                "review-compatible-source-high",
            )
            for reverse in (False, True)
        ],
        lambda root: _r18_origin_fixture(
            root, case="review-three-carrying-parents"
        ),
        lambda root: _r18_origin_fixture(
            root, case="review-two-valid-sources"
        ),
        lambda root: _r18_origin_fixture(
            root, case="review-duplicate-parent-header"
        ),
        lambda root: _r18_origin_fixture(
            root, case="review-incompatible-carrier"
        ),
        lambda root: _r18_origin_fixture(root, case="parent-order"),
        lambda root: _r18_origin_fixture(
            root, case="parent-order", reverse_parents=True
        ),
        lambda root: _r18_origin_fixture(root, case="unreadable-object"),
        *[
            (
                lambda root, transport=transport, attack=attack:
                r19_event_workflow_fixture(
                    root,
                    transport=transport,
                    attack=attack,
                )
            )
            for transport in (
                "local",
                "pre-push",
                "push",
                "pull-request-synchronize",
            )
            for attack in (False, True)
        ],
        lambda root: r19_event_workflow_fixture(
            root, transport="local", failure="missing-old"
        ),
        lambda root: r19_event_workflow_fixture(
            root, transport="push", failure="zero-before"
        ),
        lambda root: r19_event_workflow_fixture(
            root,
            transport="pull-request-synchronize",
            failure="head-mismatch",
        ),
        *[
            (
                lambda root, counter=counter, overflow=overflow:
                _r18_origin_budget_fixture(
                    root, counter=counter, overflow=overflow
                )
            )
            for counter in (
                "origin_arm_nodes",
                "origin_parent_edges",
                "origin_witness_bytes",
            )
            for overflow in (False, True)
        ],
        *[
            (
                lambda root, variant=variant:
                r15_old_side_continuity(root, variant)
            )
            for variant in (
                "invalid-delete-recreate",
                "valid-delete-recreate",
                "human-binding-restore",
                "hidden-bytes-restore",
                "continuous-preserved",
            )
        ],
    ]


CONTROL_NAMES = (
    "buffered-graph-output",
    "stream-malformed-truncated-final-line",
    "unmetered-object-payload",
    "unmetered-tree-paths",
    "unmetered-dynamic-support",
    "unmetered-support-construction",
    "restore-universal-ancestor-carry-scan",
    "ignore-outside-C-carrier",
    "ignore-absent-C-arm",
    "ignore-persisted-outside-C-collision",
    "ignore-persisted-absent-C-arm",
    "first-parent-carry-proof",
    "skip-carry-compatibility",
    "unmetered-cone-work",
    "posthoc-budget-accounting",
    "locale-git-error-stream-equality",
    "reopen-outside-C-boundary-ancestry",
    "ignore-invalid-N-root",
    "missing-all-parent-direct-validation",
    "supplier-authority-borrowing",
    "identity-multiplicity-collapsed-to-set",
    "reopen-pre-C-genealogy",
    "missing-post-event-continuity",
    "sole-valid-ignores-invalid-root",
    "omit-old-tip-human-binding",
    "literal-review-pending-treated-concrete",
    "broad-review-pending-normalization",
    "omit-supplier-carrier-human-binding",
    "skip-preserved-state-validation",
    "omit-unanswered-published-review-binding",
    "skip-persisted-frozen-skeleton",
    "skip-persisted-candidate-continuity",
    "skip-old-side-continuity",
    "skip-supplier-support-certificate",
    "endpoint-only-origin-equality",
    "skip-origin-birth-uniqueness",
    "skip-origin-post-birth-absence",
    "skip-origin-endpoint-non-regression",
    "reject-all-origin-invalid-carriers",
    "leak-object-database-pipes",
    "event-adapter-cli-entrypoint",
)


SCENARIO_ALIASES = {
    "S1": {
        "scenario": "P1-direct-linear-valid",
        "classification": "no-finding",
        "evidence_status": "valid",
        "event_mode": "direct",
        "finding": False,
        "authority_edges": 1,
        "invalid_authority_edges": 0,
        "propagation_edges": 0,
    },
    "S2": {
        "scenario": "P2-direct-linear-invalid",
        "classification": "blocking-finding",
        "evidence_status": "invalid",
        "event_mode": "direct",
        "finding": True,
        "authority_edges": 1,
        "invalid_authority_edges": 1,
        "propagation_edges": 0,
    },
    "S3": {
        "scenario": "P3-genuine-old-loss",
        "classification": "blocking-finding",
        "evidence_status": "none",
        "event_mode": "none",
        "finding": True,
        "authority_edges": 0,
        "invalid_authority_edges": 0,
        "propagation_edges": 0,
    },
    "S12": {
        "scenario": "P12-merge-supplier-valid",
        "classification": "no-finding",
        "evidence_status": "valid",
        "event_mode": "supplier",
        "finding": False,
        "authority_edges": 1,
        "invalid_authority_edges": 0,
        "propagation_edges": 1,
    },
}


def _run_fixture(fixture: _Fixture, damage: Damage | None = None):
    adapter_input = fixture.details.get("event_adapter_input")
    if adapter_input is not None:
        if damage is not None:
            raise ValueError("event workflow fixture does not accept damage mode")
        result = audit_event(
            fixture.repo.root,
            adapter_input["event_kind"],
            adapter_input["payload"],
            git_runner=_trusted_git_runner(),
        )
        result["scenario"] = fixture.scenario
        result["expected_result"] = fixture.expected
        result["details"] = fixture.details
        return result
    if "restore_hidden" not in fixture.details:
        result = _run_classifier(fixture, damage)
        workflow = fixture.details.get("workflow_contract", {})
        if workflow.get("repeat_exact_inputs") and damage is None:
            repeated = _run_classifier(fixture)
            result["workflow_input_evidence"] = {
                "exact_O_N_repeated": [fixture.O, fixture.N],
                "raw_results_equal": result == repeated,
            }
        return result
    if damage is not None:
        raise ValueError("recovery fixture does not accept damage mode")
    missing_oid = fixture.details["missing_claim_blob_oid"]
    reader_session = RepositorySession(
        fixture.repo.root,
        git_runner=_trusted_git_runner(),
    )
    reader_metrics = reader_session.metrics
    reader_session.open()
    reader = reader_session.create_object_database()
    first_reader_reason = None
    try:
        reader.read(missing_oid)
    except Unreadable as error:
        first_reader_reason = str(error)
    missing_cached = missing_oid in reader.objects
    first = _run_classifier(fixture)
    hidden = fixture.repo.root / fixture.details["restore_hidden"]
    target = fixture.repo.root / fixture.details["restore_target"]
    if hidden.is_file():
        hidden.rename(target)
    try:
        restored_kind, restored_payload = reader.read(missing_oid)
        success_cached = missing_oid in reader.objects
        cache_hits_before = reader_metrics.object_cache_hits
        cached_kind, cached_payload = reader.read(missing_oid)
        cache_hit_after_restore = (
            reader_metrics.object_cache_hits == cache_hits_before + 1
        )
    finally:
        reader_session.close()
    second = _run_classifier(fixture)
    second["recovery"] = {
        "first_status": first["evidence_verdict"]["status"],
        "first_reason": first["evidence_verdict"]["reason"],
        "second_status": second["evidence_verdict"]["status"],
        "same_process": True,
        "same_reader": True,
        "first_reader_reason": first_reader_reason,
        "missing_cached": missing_cached,
        "restored_kind": restored_kind,
        "restored_payload_size": len(restored_payload),
        "success_cached": success_cached,
        "cache_hit_after_restore": cache_hit_after_restore,
        "cached_bytes_equal": (
            cached_kind == restored_kind
            and cached_payload == restored_payload
        ),
        "reader_metrics": dataclasses.asdict(reader_metrics),
        "missing_oid": missing_oid,
    }
    return second


def validate_result(result: dict):
    scenario = result["scenario"]
    errors = []
    if result["classification"] != result["expected_result"]:
        errors.append(
            f"classification {result['classification']} != "
            f"{result['expected_result']}"
        )
    status = result["evidence_verdict"]["status"]
    if status not in {"valid", "invalid", "none", "ambiguous", "unreadable"}:
        errors.append(f"unstructured evidence status {status}")
    for name in ("O", "N"):
        oid = result[name]
        if len(oid) not in {40, 64} or any(
            char not in "0123456789abcdef" for char in oid
        ):
            errors.append(f"{name} is not a full OID")
    if result["C"] is not None and (
        len(result["C"]) not in {40, 64}
        or any(char not in "0123456789abcdef" for char in result["C"])
    ):
        errors.append("derived C is not a full OID")
    authority = {
        (edge["parent"], edge["child"])
        for edge in result["authority_edges"]
    }
    propagation = {
        (edge["parent"], edge["child"])
        for edge in result["propagation_edges"]
    }
    if authority.intersection(propagation):
        errors.append("authority and propagation edges overlap")
    actions = result["actions"]
    if scenario == "P1-direct-linear-valid":
        if result["event_mode"] != "direct" or len(authority) != 1:
            errors.append("P1 did not select one direct authority edge")
    if scenario == "R17-outside-C-neutral-parent-valid-restack":
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        if (
            details["unique_merge_base"] != [result["C"]]
            or not details["task_patch_equal"]
            or details["production_deletion_problem"] is not None
            or status != "valid"
            or result["event_mode"] != "direct"
            or len(authority) != 1
            or action is None
            or details["F"] not in action["neutral_parents"]
        ):
            errors.append(
                "R17 legal outside-C neutral-parent restack did not stay clean"
            )
    if scenario.startswith("R17-carry-"):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        proofs = action["carry_proofs"] if action is not None else []
        merge_edges = [
            edge
            for proof in proofs
            for edge in proof["edges"]
            if edge["child"] == details["merge"]
        ]
        collisions = [
            collision
            for proof in proofs
            for collision in proof["outside_collisions"]
        ]
        absent = {
            parent
            for proof in proofs
            for parent in proof["absent_c_parents"]
        }
        if details["variant"] == "compatible":
            if (
                status != "valid"
                or len(merge_edges) != 2
                or sorted(edge["role"] for edge in merge_edges)
                != ["compatible-carrier", "source"]
                or any(edge["problem"] for edge in merge_edges)
            ):
                errors.append(
                    "R17 compatible carry merge lost canonical edge roles"
                )
        elif details["variant"] == "incompatible":
            if (
                status != "ambiguous"
                or len(merge_edges) != 2
                or sum(edge["problem"] is not None for edge in merge_edges)
                != 1
            ):
                errors.append("R17 incompatible carry merge false-greened")
        elif details["variant"] == "absent-arm":
            if status != "ambiguous" or details["second"] not in absent:
                errors.append("R17 absent C-descendant arm false-greened")
        else:
            expected_multiplicity = (
                2 if details["variant"] == "outside-duplicate" else 1
            )
            if (
                status != "ambiguous"
                or len(collisions) != 1
                or collisions[0]["parent"] != details["second"]
                or collisions[0]["multiplicity"] != expected_multiplicity
            ):
                errors.append("R17 outside-C collision false-greened")
    if scenario.startswith("R17-persisted-"):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        proofs = action["carry_proofs"] if action is not None else []
        collisions = [
            collision
            for proof in proofs
            for collision in proof["outside_collisions"]
        ]
        absent = {
            parent
            for proof in proofs
            for parent in proof["absent_c_parents"]
        }
        if (
            result["classification"] != "blocking-finding"
            or status != "ambiguous"
            or result["audit_exit"] != 1
            or action is None
            or len(proofs) != 2
        ):
            errors.append("R17 persisted carry competitor false-greened")
        elif details["variant"].startswith("outside-"):
            expected = (
                2 if details["variant"] == "outside-duplicate" else 1
            )
            if (
                action["reason_code"] != "persisted-outside-C-collision"
                or len(collisions) != 1
                or collisions[0]["parent"] != details["second"]
                or collisions[0]["multiplicity"] != expected
            ):
                errors.append("R17 persisted outside-C collision was lost")
        elif (
            action["reason_code"] != "persisted-delete-recreate"
            or details["D"] not in absent
        ):
            errors.append("R17 persisted absent C arm was lost")
        references = details.get("review_reference_oids")
        if details["variant"] == "outside-single" and references != {
            "C": "843634959ac1156ef81ee7ccbf1f703261bbde1f",
            "O": "c0ec07829f6aa4e1207a680a0354deb8a8f0c162",
            "A": "426b485efa3b5f85a678600795a20b1e91c6049f",
            "F": "e10a4eb3208c44000e7363c2894e2a77b74828fa",
            "P": "60f5448337b6f9a114c0231b86242474dd34873b",
            "N": "af48cf172570a08d65c12dc467b2226dfbe8981a",
        }:
            errors.append("R17 persisted outside-C reviewer OIDs changed")
        if details["variant"] == "valid-absent-arm" and references != {
            "C": "0ddb561a40c84c0590d9abe8a3036521b239de25",
            "O": "17ef4a3d8c518778d62c635864670319efd03754",
            "A": "90de0b5af2ad8baec036ddaed2842eda86c2c556",
            "K": "f03d61cc931d7c860e7fd6f166c60d09596b48e5",
            "D": "161d7ed2d7bc121ce5331fed2e1ecb0dd650041e",
            "P": "1847cdbe8298d5895ad566c03abc870064ca711b",
            "N": "76cf3354a913effec09cac7b183684159dfd0b84",
        }:
            errors.append("R17 persisted absent-arm reviewer OIDs changed")
    if scenario == "R17-wide-outside-C-boundary-budget":
        details = result["details"]
        if (
            status != "ambiguous"
            or result["audit_exit"] != 2
            or actions
            or authority
            or propagation
            or len(details["outside_parents"]) != 64
            or result["metrics"]["graph_commits"] > 7
            or result["metrics"]["graph_parent_tokens"] != 8
            or "graph_parent_tokens" not in result["evidence_verdict"]["reason"]
            or result["metrics"]["graph_output_bytes"]
            >= details["budget_contract"]["raw_graph_bytes"]
            or result["metrics"]["graph_process_reaps"] != 1
            or result["metrics"]["graph_process_cleanup_checks"] < 2
        ):
            errors.append("R17 wide boundary escaped transactional budget")
        if details["review_reference_oids"] != {
            "C": "b066accf737c901fd1ee314fcf310afb70c8fe87",
            "O": "ba894e5a1c019e3b2c29ee8319eebfb4b0aaa9a3",
            "P": "b79ff7a4036270fed4a70d82ad226817ae94e662",
            "N": "412c2f8c5a8be93d1e0ffc5983d607bf750bb2f0",
        }:
            errors.append("R17 wide-boundary reviewer OIDs changed")
    if scenario == "R17-graph-parent-tokens-exact":
        details = result["details"]["budget_contract"]
        if (
            status != "none"
            or result["audit_exit"] != 0
            or result["metrics"]["graph_parent_tokens"] != 68
            or result["metrics"]["graph_output_bytes"] != details["raw_graph_bytes"]
            or result["metrics"]["graph_lines"] != 4
        ):
            errors.append("R17 exact graph parent-token budget did not pass")
    if scenario.startswith("W"):
        contract = result["details"]["workflow_contract"]
        if (
            result["input_contract"]["authoritative_endpoints"]
            != ["O", "N"]
            or contract["classifier_parameters"] != ["O", "N"]
            or contract["provider_api_calls"] != 0
            or contract["authoritative_inputs"]
            != {"O": result["O"], "N": result["N"]}
        ):
            errors.append("workflow case escaped the exact O,N input API")
        if scenario == "W0-fast-forward-return" and (
            result["C"] != result["O"]
            or status != "none"
            or actions
            or result["metrics"]["identity_calls"] != 0
        ):
            errors.append("W0 did not return before provenance attribution")
        if scenario == "W1-pre-PR-push-exact-endpoints" and (
            contract["event_before"] != result["O"]
            or contract["event_after"] != result["N"]
            or contract["github_sha"] == result["N"]
            or contract["github_sha_is_authoritative"]
            or not contract["pre_PR"]
        ):
            errors.append("W1 push transport selected a mutable endpoint")
        if scenario == "W2-base-advance-retarget-invariant" and (
            not contract["variants_keep_exact_O_N"]
            or len(contract["provider_state_variants"]) != 3
        ):
            errors.append("W2 provider state changed classifier endpoints")
        if scenario == "W3-multiple-PR-API-zero-calls" and (
            contract["PR_lookup"]
            or len(contract["provider_states"]) != 5
        ):
            errors.append("W3 retained provider lookup authority")
        if scenario == "W4-stale-rerun-exact-inputs":
            repeat = result.get("workflow_input_evidence", {})
            if (
                not repeat.get("raw_results_equal")
                or repeat.get("exact_O_N_repeated")
                != [result["O"], result["N"]]
            ):
                errors.append("W4 stale rerun did not reuse exact O,N")
        if scenario == "W5-missing-O-coverage-unavailable" and (
            status != "unreadable"
            or contract["coverage_classification"]
            != "coverage-unavailable"
            or contract["old_object_fetch_exit"] != 2
            or contract["fallback"] is not None
            or actions
        ):
            errors.append("W5 missing O guessed a fallback endpoint")
        if scenario == "W6-created-deleted-zero-endpoints" and any(
            item["classification"] != "coverage-unavailable"
            for item in contract["event_classifications"]
        ):
            errors.append("W6 zero endpoint was not coverage-unavailable")
        if scenario == "W7-PR-synchronize-top-level-endpoints" and (
            contract["top_level_before"] != result["O"]
            or contract["top_level_after"] != result["N"]
            or contract["top_level_after"]
            != contract["pull_request_head_sha"]
            or not contract["after_matches_head"]
            or contract["PR_lookup"]
            or contract["mismatch_classification"]
            != "coverage-unavailable"
        ):
            errors.append("W7 synchronize endpoints are not self-contained")
    if scenario.startswith("R19-WF-"):
        details = result["details"]
        adapter = result.get("event_adapter", {})
        common_adapter = bool(
            adapter.get("event_kind") == details["workflow_transport"]
            and adapter.get("github_sha_used") is False
            and adapter.get("mutable_metadata_invariant") is True
            and adapter.get("mutable_state_reads") == 0
            and adapter.get("provider_api_calls") == 0
            and adapter.get("typed_origin_strategy") == "U"
            and result["input_contract"]["origin_strategy"] == "U"
        )
        if not common_adapter:
            errors.append("R19 workflow escaped the immutable typed-U adapter")
        if details["workflow_failure"] is not None:
            if (
                result["audit_exit"] != 2
                or result["classification"] != "unreadable"
                or adapter.get("status") != "coverage-unavailable"
                or adapter.get("reason")
                != details["expected_adapter_reason"]
                or result["evidence_verdict"]["reason"]
                != details["expected_adapter_reason"]
                or actions
            ):
                errors.append("R19 event failure did not fail closed explicitly")
        else:
            expected_endpoints = details["expected_event_endpoints"]
            origin_actions = [
                action for action in actions if action["origin_proofs"]
            ]
            if (
                result["O"] != expected_endpoints["O"]
                or result["N"] != expected_endpoints["N"]
                or result["C"] == result["O"]
                or adapter.get("O") != result["O"]
                or adapter.get("N") != result["N"]
                or adapter.get("status") != "accepted"
                or adapter.get("reason") is not None
                or len(origin_actions) != 1
                or origin_actions[0]["event_mode"] != "origin-U"
                or bool(origin_actions[0]["finding"])
                is not details["workflow_attack"]
            ):
                errors.append(
                    "R19 immutable event did not drive the real non-fast-forward typed-U result"
                )
    if scenario == "R17-unreadable-outside-C-boundary" and (
        status != "unreadable"
        or result["audit_exit"] != 2
        or result["evidence_verdict"]["reason"]
        != "missing-or-malformed-commit:"
        + result["details"]["unreadable_boundary"]
        or actions
        or authority
        or propagation
        or result["metrics"]["identity_calls"] != 0
        or result["metrics"]["authority_calls"] != 0
    ):
        errors.append("R17 unreadable boundary returned partial results")
    if scenario == "R17-unreadable-outside-C-ancestor-stays-unopened":
        action = actions[0] if len(actions) == 1 else None
        references = result["details"]["attacker_reference_oids"]
        if (
            status != "valid"
            or result["audit_exit"] != 0
            or action is None
            or result["details"]["F"] not in action["neutral_parents"]
            or not result["details"]["same_identity"]
            or not result["details"]["ancestor_blob_is_unique"]
            or references != {
                "G": "b838a677f5753a45bff2d33f6e94b3a80cc92905",
                "G_blob": "88ce173dddc1914b0e7ccd52f5b89fb4742a713d",
                "C": "52c16e3ace5b2fb945b2e8fc42b7485536ea1a47",
                "O": "5ff93e594d8689fe44774a9728a882c846e1833e",
                "F": "4afa966344cb99e6a72a10997b10572072e7cccb",
                "P": "6564e680097653cebcc008a0bfee8587c644057f",
                "K": "245d7de3ef54645d32fbcf8bbda7d69f426ce6d2",
                "D": "595acd03b0c0f5cee214599587247d1115b2fc40",
                "N": "61d97651036a8cc9da10662ca7560bce14ce9ce5",
            }
        ):
            errors.append("R17 reopened an outside-C neutral ancestor")
    if scenario == "P2-direct-linear-invalid" and status != "invalid":
        errors.append("P2 did not name invalid production authority")
    if scenario == "P3-genuine-old-loss" and status != "none":
        errors.append("P3 did not report no candidate event")
    if scenario == "P4-pre-C-identical-origins":
        if result["metrics"]["graph_enumerations"] != 1:
            errors.append("P4 did not use one post-C enumeration")
    if scenario == "P5-duplicate-at-C":
        if not any(
            action["multiplicity"]["C"] == 2 for action in actions
        ):
            errors.append("P5 lost exact multiplicity two")
        if not any(len(action["paths"]["C"]) == 2 for action in actions):
            errors.append("P5 did not expose both C-root paths")
    if scenario.startswith("P6"):
        if not any(
            action["reason_code"]
            in {"persisted-delete-recreate", "post-event-reintroduction"}
            or "discontinu" in action["reason"]
            for action in actions
        ):
            errors.append("P6 did not fail on occurrence discontinuity")
    if scenario == "P7-immutable-payload-change":
        if result["details"]["production_identity_equal"]:
            errors.append("P7 collapsed distinct immutable payloads")
    if scenario == "P8-path-timing-move":
        details = result["details"]
        if not details["production_identity_equal"]:
            errors.append("P8 move changed production identity")
        if details["paired_payload_change_identity_equal"]:
            errors.append("P8 payload mutation collapsed into the move")
    if scenario == "P9-direct-two-parent-valid" and len(authority) != 2:
        errors.append("P9 did not validate both carrying parents")
    if scenario == "P10-direct-invalid-parent":
        if len(authority) != 2 or sum(
            edge["problem"] is not None
            for edge in result["authority_edges"]
        ) != 1:
            errors.append("P10 did not retain each parent verdict")
    if scenario == "P11-direct-three-parent-valid" and len(authority) != 3:
        errors.append("P11 did not validate all three carrying parents")
    if scenario == "P12-merge-supplier-valid":
        if result["event_mode"] != "supplier":
            errors.append("P12 did not remain supplier mode")
        if len(authority) != 1 or len(propagation) != 1:
            errors.append("P12 edge roles are incomplete")
    if scenario == "P13-merge-supplier-invalid":
        if status != "invalid" or len(propagation) != 1:
            errors.append("P13 did not preserve invalid supplier structure")
        if not any(
            edge["problem"] for edge in result["authority_edges"]
        ):
            errors.append("P13 did not name the invalid supplier edge")
    if scenario == "P14-supplier-reintroduced":
        if status != "ambiguous" or "discontinu" not in (
            result["evidence_verdict"]["reason"]
        ):
            errors.append("P14 did not fail on reintroduction")
    if scenario == "P15-competing-suppliers":
        if status != "ambiguous" or len(authority) != 2:
            errors.append("P15 did not expose both competing suppliers")
    if scenario == "P16-PCX-08-invalid-supplier-claimed-carrier":
        if (
            status != "invalid"
            or result["event_mode"] != "supplier"
            or len(propagation) != 1
            or not any(
                edge["problem"] for edge in result["authority_edges"]
            )
        ):
            errors.append("P16/PCX-08 borrowed carrier authority")
    if scenario == "P17-post-event-reintroduction":
        if status != "ambiguous" or "discontinu" not in (
            result["evidence_verdict"]["reason"]
        ):
            errors.append("P17 did not fail on post-event reintroduction")
    if scenario.startswith("P18") and status != "unreadable":
        errors.append("P18 did not return structured unreadable")
    if scenario == "P19-production-identities":
        details = result["details"]
        for key in (
            "ordinary_identity_path_independent",
            "ordinary_payload_change_distinct",
        ):
            if not details[key]:
                errors.append(f"P19 identity assertion failed: {key}")
        if details["generated_retry_identity"][0] != "generated-retry":
            errors.append("P19 did not use typed generated retry identity")
    if scenario == "P20-lifecycle-types":
        if result["metrics"]["authority_calls"] < 4:
            errors.append("P20 did not exercise all four validator leaves")
        if any(edge["problem"] for edge in result["authority_edges"]):
            errors.append("P20 special authority returned a problem")
        expected_leaves = {
            "ordinary-agent",
            "human-decision",
            "generated-retry-special",
            "task-pickup-special",
        }
        if set(result["details"]["validator_leaves"]) != expected_leaves:
            errors.append("P20 did not exercise every promised validator leaf")
    if scenario == "P21-PCX-17c-squash-erasure":
        if status != "invalid" or not any(
            edge["problem"] for edge in result["authority_edges"]
        ):
            errors.append("P21 squash unexpectedly preserved authority")
    if scenario == "PCX-01-neutral-parent":
        neutral = {
            oid
            for action in actions
            for oid in action["neutral_parents"]
        }
        if result["details"]["neutral_parent"] not in neutral:
            errors.append("PCX-01 did not list the neutral parent")
        if len(authority) != 2:
            errors.append("PCX-01 did not validate both carrying parents")
    if scenario == "PCX-02-neutral-plus-invalid-carrier":
        neutral = {
            oid
            for action in actions
            for oid in action["neutral_parents"]
        }
        if (
            result["details"]["neutral_parent"] not in neutral
            or len(authority) != 2
            or sum(
                edge["problem"] is not None
                for edge in result["authority_edges"]
            ) != 1
        ):
            errors.append("PCX-02 hid a carrier verdict behind neutral parent")
    if scenario == "PCX-03-foreign-exact-identity":
        if status != "ambiguous":
            errors.append("PCX-03 did not fail on foreign occurrence")
    if scenario == "PCX-04-several-absent-one-supplier":
        absent_count = len(actions[0]["absent_parents"]) if actions else 0
        if (
            len(authority) != 1
            or len(propagation) != 1
            or absent_count != 2
        ):
            errors.append("PCX-04 did not collapse to one supplier event")
    if scenario == "PCX-05-competing-later-supplier":
        event_children = {edge["child"] for edge in result["authority_edges"]}
        if (
            status != "ambiguous"
            or len(authority) != 2
            or event_children
            != {result["details"]["D1"], result["details"]["D2"]}
        ):
            errors.append("PCX-05 did not expose competing D1/D2 suppliers")
    if scenario == "PCX-06-nested-supplier-over-direct":
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        authority_events = {
            edge["child"] for edge in result["authority_edges"]
        }
        propagation_sequence = [
            (edge["parent"], edge["child"])
            for edge in result["propagation_edges"]
        ]
        expected_propagation = list(
            zip(details["carriers"], details["adoptions"], strict=True)
        )
        fixture_oids = (
            [details["direct_event"]]
            + details["adoptions"]
            + details["carriers"]
            + details["neutral_parents"]
            + details["absent_sources"]
        )
        if (
            len(authority) != 2
            or len(propagation) != 2
            or authority_events != {details["direct_event"]}
        ):
            errors.append("PCX-06 lost nested supplier edge roles")
        if action is None:
            errors.append("PCX-06 did not return exactly one action")
        elif (
            action["neutral_parents"] != details["neutral_parents"]
            or action["absent_parents"] != details["absent_sources"]
        ):
            errors.append("PCX-06 lost accumulated neutral/absent ancestry")
        if propagation_sequence != expected_propagation:
            errors.append("PCX-06 lost stable nested propagation order")
        if any(
            len(oid) not in {40, 64}
            or any(char not in "0123456789abcdef" for char in oid)
            for oid in fixture_oids
        ):
            errors.append("PCX-06 emitted a non-full ancestry OID")
    if scenario == "PCX-07-overqualified-propagation":
        if (
            result["event_mode"] != "supplier"
            or len(authority) != 1
            or len(propagation) != 1
        ):
            errors.append("PCX-07 reclassified propagation as authority")
    if scenario == "PCX-09-recreated-claimed-bytes":
        if status != "ambiguous" or "discontinu" not in (
            result["evidence_verdict"]["reason"]
        ):
            errors.append("PCX-09 let an old claim cross reintroduction")
    if scenario == "PCX-10-transient-multiplicity":
        reason = result["evidence_verdict"]["reason"]
        expected_paths = {
            result["authority_edges"][0]["path"],
            result["details"]["duplicate_path"],
        }
        if (
            "multiplicity 2" not in reason
            or not all(path in reason for path in expected_paths)
        ):
            errors.append("PCX-10 did not expose transient multiplicity")
    if scenario == "PCX-11-different-payload-same-path":
        if not any(
            action["status"] == "valid" for action in actions
        ) or not any(action["finding"] for action in actions):
            errors.append("PCX-11 did not separate Q-A from Q-B")
        identities = {
            tuple(action["identity"]["production_tuple"])
            for action in actions
        }
        if len(identities) != 2:
            errors.append("PCX-11 collapsed distinct immutable payloads")
    if scenario == "PCX-12-timing-rename-supplier":
        if (
            status != "valid"
            or result["event_mode"] != "supplier"
            or len(authority) != 1
            or len(propagation) != 1
        ):
            errors.append("PCX-12 did not preserve identity through timing move")
    if scenario == "PCX-13-conflicting-human-response":
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        propagation_sequence = [
            (edge["parent"], edge["child"])
            for edge in result["propagation_edges"]
        ]
        expected_propagation = list(
            zip(details["carriers"], details["adoptions"], strict=True)
        )
        lineage_oids = (
            [details["supplier_parent"]]
            + details["adoptions"]
            + details["carriers"]
            + details["neutral_parents"]
            + details["absent_sources"]
        )
        if (
            action is None
            or status != "invalid"
            or result["event_mode"] != "supplier"
            or action["reason_code"] != "upstream-invalid-supplier"
            or "old-tip-human-binding-conflict" not in action["reason"]
            or not all(
                adoption in action["reason"]
                for adoption in details["adoptions"]
            )
        ):
            errors.append("PCX-13 did not preserve response conflict")
        if action is not None and (
            action["neutral_parents"] != details["neutral_parents"]
            or action["absent_parents"] != details["absent_sources"]
        ):
            errors.append("PCX-13 lost invalid supplier parent ancestry")
        if (
            len(authority) != 1
            or any(
                edge["problem"] for edge in result["authority_edges"]
            )
            or propagation_sequence != expected_propagation
        ):
            errors.append("PCX-13 lost invalid supplier causal edges")
        if any(
            len(oid) not in {40, 64}
            or any(char not in "0123456789abcdef" for char in oid)
            for oid in lineage_oids
        ):
            errors.append("PCX-13 emitted a non-full ancestry OID")
    if scenario == "R3-01-two-invalid-causal-sources":
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        authority_events = {
            edge["child"] for edge in result["authority_edges"]
        }
        propagation_sequence = [
            (edge["parent"], edge["child"])
            for edge in result["propagation_edges"]
        ]
        expected_propagation = list(
            zip(details["carriers"], details["adoptions"], strict=True)
        )
        expected_reason_tokens = [
            f"old-tip-human-binding-conflict@{source}"
            for source in details["source_children"]
        ]
        all_oids = (
            details["authority_events"]
            + details["source_children"]
            + details["carriers"]
            + details["adoptions"]
            + details["neutral_parents"]
            + details["absent_sources"]
        )
        if (
            action is None
            or status != "ambiguous"
            or result["event_mode"] != "supplier"
            or action["reason_code"] != "competing-causal-suppliers"
            or not all(
                token in action["reason"] for token in expected_reason_tokens
            )
        ):
            errors.append("R3-01 did not retain both invalid source lineages")
        if (
            authority_events != set(details["authority_events"])
            or len(authority) != 2
            or propagation_sequence != expected_propagation
        ):
            errors.append("R3-01 lost ordered authority/propagation evidence")
        if action is not None and (
            action["neutral_parents"] != details["neutral_parents"]
            or action["absent_parents"] != details["absent_sources"]
        ):
            errors.append("R3-01 lost neutral/absent source ancestry")
        if any(
            len(oid) not in {40, 64}
            or any(char not in "0123456789abcdef" for char in oid)
            for oid in all_oids
        ):
            errors.append("R3-01 emitted a non-full causal OID")
    if scenario == "R3-02-invalid-valid-causal-competition":
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        authority_events = {
            edge["child"] for edge in result["authority_edges"]
        }
        propagation_sequence = [
            (edge["parent"], edge["child"])
            for edge in result["propagation_edges"]
        ]
        expected_propagation = list(
            zip(details["carriers"], details["adoptions"], strict=True)
        )
        expected_reason_tokens = (
            f"old-tip-human-binding-conflict@{details['source_children'][0]}",
            f"valid-direct-authority@{details['source_children'][1]}",
        )
        all_oids = (
            details["authority_events"]
            + details["source_children"]
            + details["carriers"]
            + details["adoptions"]
            + details["neutral_parents"]
            + details["absent_sources"]
        )
        if (
            action is None
            or status != "ambiguous"
            or result["event_mode"] != "supplier"
            or action["reason_code"] != "competing-causal-suppliers"
            or not all(
                token in action["reason"] for token in expected_reason_tokens
            )
        ):
            errors.append("R3-02 did not retain invalid+valid lineages")
        if (
            authority_events != set(details["authority_events"])
            or len(authority) != 2
            or propagation_sequence != expected_propagation
        ):
            errors.append("R3-02 lost mixed causal edge evidence")
        if action is not None and (
            action["neutral_parents"] != details["neutral_parents"]
            or action["absent_parents"] != details["absent_sources"]
        ):
            errors.append("R3-02 lost mixed neutral/absent ancestry")
        if any(
            len(oid) not in {40, 64}
            or any(char not in "0123456789abcdef" for char in oid)
            for oid in all_oids
        ):
            errors.append("R3-02 emitted a non-full causal OID")
    if scenario == "R3-03-valid-supplier-plus-invalid-parent-at-N-blocks":
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        serialized_evidence = json.dumps(
            {
                "authority": result["authority_edges"],
                "propagation": result["propagation_edges"],
                "reason": result["evidence_verdict"]["reason"],
                "absent": (
                    action["absent_parents"] if action is not None else []
                ),
            },
            sort_keys=True,
        )
        if (
            action is None
            or status != "ambiguous"
            or result["event_mode"] != "ambiguous"
            or action["reason_code"] != "competing-final-absence-roots"
            or len(authority) != 2
            or len(propagation) != 1
            or {
                edge["child"] for edge in result["authority_edges"]
            }
            != {details["supplier"], details["unrelated_invalid"]}
            or sum(
                edge["problem"] is not None
                for edge in result["authority_edges"]
            )
            != 1
            or result["metrics"]["authority_calls"] < 4
        ):
            errors.append("R3-03 did not retain valid and invalid N roots")
        if details["unrelated_invalid"] not in serialized_evidence:
            errors.append("R3-03 hid the invalid root that reaches N")
        if (
            not details["unrelated_reachable_from_N"]
            or details["unrelated_ancestor_of_supplier"]
        ):
            errors.append("R3-03 did not place the invalid source off ancestry")
        for oid in (
            details["unrelated_invalid"],
            details["supplier"],
            details["carrier"],
        ):
            if len(oid) not in {40, 64} or any(
                char not in "0123456789abcdef" for char in oid
            ):
                errors.append("R3-03 emitted a non-full causal OID")
    if scenario.startswith("R4-"):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        expected_propagation = list(
            zip(details["carriers"], details["adoptions"], strict=True)
        )
        propagation_sequence = [
            (edge["parent"], edge["child"])
            for edge in result["propagation_edges"]
        ]
        authority_events = [
            edge["child"] for edge in result["authority_edges"]
        ]
        roots = action["causal_roots"] if action is not None else []
        root_children = [root["root_child"] for root in roots]
        root_statuses = [root["status"] for root in roots]
        reason_children = [
            record["source_child"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        ]
        all_oids = (
            details["authority_events"]
            + details["carriers"]
            + details["adoptions"]
            + details["neutral_parents"]
            + details["absent_sources"]
            + details["reason_children"]
        )
        if (
            action is None
            or result["event_mode"] != "supplier"
            or propagation_sequence != expected_propagation
            or action["neutral_parents"] != details["neutral_parents"]
            or action["absent_parents"] != details["absent_sources"]
            or authority_events != details["authority_events"]
            or root_children != details["authority_events"]
            or root_statuses != details["root_statuses"]
            or reason_children != details["reason_children"]
        ):
            errors.append("R4 diamond lost a canonical-root envelope")
        if any(
            len(oid) not in {40, 64}
            or any(char not in "0123456789abcdef" for char in oid)
            for oid in all_oids
        ):
            errors.append("R4 diamond emitted a non-full causal OID")
    if scenario == "R4-01-same-root-valid-diamond":
        if (
            status != "valid"
            or len(authority) != 1
            or len(propagation) != 3
            or action is None
            or action["reason_code"] != "valid-supplier-authority"
        ):
            errors.append("R4-01 falsely blocked the equal-root diamond")
    if scenario == "R4-02-distinct-valid-root-diamond":
        if (
            status != "ambiguous"
            or len(authority) != 2
            or len(propagation) != 3
            or action is None
            or action["reason_code"] != "competing-causal-suppliers"
            or not all(
                adoption in action["reason"]
                for adoption in details["adoptions"][:2]
            )
        ):
            errors.append("R4-02 collapsed distinct valid roots")
    if scenario == "R4-03-equal-root-plus-invalid-diamond":
        invalid_edges = [
            edge for edge in result["authority_edges"] if edge["problem"]
        ]
        if (
            status != "ambiguous"
            or len(authority) != 2
            or len(invalid_edges) != 1
            or len(propagation) != 3
            or action is None
            or action["reason_code"] != "competing-causal-suppliers"
            or details["authority_events"][1] not in action["reason"]
        ):
            errors.append("R4-03 hid the additional invalid root")
    if scenario.startswith("R5-"):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        expected_authority = {
            (
                details["initial_authority_parent"],
                details["initial_authority_child"],
            ),
            (
                details["later_authority_parent"],
                details["later_authority_child"],
            ),
        }
        expected_propagation = {
            (details["carrier"], details["supplier_adoption"])
        }
        reason_children = {
            record["source_child"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        }
        root_children = {
            root["root_child"]
            for root in (
                action["causal_roots"] if action is not None else []
            )
        }
        later_edge = next(
            (
                edge
                for edge in result["authority_edges"]
                if edge["child"] == details["later_authority_child"]
            ),
            None,
        )
        if (
            result["classification"] != "blocking-finding"
            or status != "ambiguous"
            or result["event_mode"] != "ambiguous"
            or action is None
            or action["event_child"]
            != details["later_authority_child"]
            or action["reason_code"]
            != "reintroduced-competing-occurrences"
            or authority != expected_authority
            or propagation != expected_propagation
            or details["initial_absent_parent"]
            not in action["absent_parents"]
            or {
                details["initial_authority_child"],
                details["later_authority_child"],
            }
            - root_children
            or set(details["reason_children"]) - reason_children
            or later_edge is None
            or bool(later_edge["problem"])
            == details["later_authority_valid"]
        ):
            errors.append(
                "R5 reintroduction history lost a causal occurrence"
            )
    if scenario == "R6-02-valid-plus-ambiguous-all-absent":
        if (
            result["classification"] != "no-finding"
            or status != "valid"
            or result["details"]["r17_disposition"]
            != (
                "outside-C all-absent boundary is neutral at multiplicity "
                "zero; its ambiguous ancestor root stays unopened"
            )
        ):
            errors.append("R6 outside-C zero boundary reopened ancestry")
    if scenario in {
        "R6-01-valid-plus-invalid-all-absent",
        "R6-03-two-invalid-all-absent",
    }:
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        root_children = [
            root["root_child"]
            for root in (
                action["causal_roots"] if action is not None else []
            )
        ]
        root_statuses = [
            root["status"]
            for root in (
                action["causal_roots"] if action is not None else []
            )
        ]
        reason_children = {
            record["source_child"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        }
        if (
            result["classification"] != "blocking-finding"
            or status != "ambiguous"
            or result["event_mode"] != "ambiguous"
            or action is None
            or action["reason_code"]
            != "competing-final-absence-roots"
            or [
                edge["child"] for edge in result["authority_edges"]
            ]
            != details["causal_events"]
            or root_children != details["causal_events"]
            or root_statuses != details["causal_statuses"]
            or set(details["causal_events"]) - reason_children
            or len(propagation) != 0
            or sum(
                edge["problem"] is not None
                for edge in result["authority_edges"]
            )
            != details["expected_problem_count"]
        ):
            errors.append("R6 competing all-absent roots false-greened")
        if any(
            len(oid) not in {40, 64}
            or any(char not in "0123456789abcdef" for char in oid)
            for oid in (
                details["causal_events"]
                + [
                    edge[key]
                    for edge in result["authority_edges"]
                    for key in ("parent", "child")
                ]
            )
        ):
            errors.append("R6 competing roots emitted a non-full OID")
    if scenario == "R6-04-same-valid-root-all-absent-wrappers":
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        roots = action["causal_roots"] if action is not None else []
        reason_children = [
            record["source_child"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        ]
        if (
            result["classification"] != "no-finding"
            or status != "valid"
            or result["event_mode"] != "supplier"
            or action is None
            or action["reason_code"] != "valid-shared-causal-root"
            or [edge["child"] for edge in result["authority_edges"]]
            != details["causal_events"]
            or [
                (edge["parent"], edge["child"])
                for edge in result["propagation_edges"]
            ]
            != list(
                zip(
                    details["carriers"],
                    details["wrapper_events"],
                    strict=True,
                )
            )
            or action["neutral_parents"] != details["neutral_parents"]
            or action["absent_parents"] != details["absent_parents"]
            or len(roots) != 1
            or roots[0]["status"] != "valid"
            or roots[0]["root_child"] != details["causal_events"][0]
            or reason_children[:3] != details["reason_children"]
        ):
            errors.append("R6 collapsed or blocked equal-root wrappers")
        if any(
            len(oid) not in {40, 64}
            or any(char not in "0123456789abcdef" for char in oid)
            for oid in (
                details["causal_events"]
                + details["wrapper_events"]
                + details["carriers"]
                + details["neutral_parents"]
                + details["absent_parents"]
                + details["reason_children"]
            )
        ):
            errors.append("R6 equal-root wrappers emitted a non-full OID")
    if scenario.startswith("R8-direct-human-response-") or scenario.startswith(
        "R8-supplier-human-response-"
    ):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        reason_codes = {
            record["reason_code"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        }
        expected_status = (
            "invalid" if details["binding_conflict"] else "valid"
        )
        expected_classification = (
            "blocking-finding"
            if details["binding_conflict"]
            else "no-finding"
        )
        if (
            action is None
            or status != expected_status
            or result["classification"] != expected_classification
            or result["event_mode"] != details["mode"]
            or len(result["authority_edges"]) != 1
            or result["authority_edges"][0]["parent"]
            != details["authority_parent"]
            or result["authority_edges"][0]["child"]
            != details["authority_child"]
            or result["authority_edges"][0]["problem"] is not None
            or len(propagation) != (1 if details["mode"] == "supplier" else 0)
            or (
                details["binding_conflict"]
                and (
                    "old-tip-human-binding-conflict" not in reason_codes
                    or result["O"] not in action["reason"]
                    or details["old_response"] not in action["reason"]
                    or details["candidate_response"] not in action["reason"]
                )
            )
            or (
                not details["binding_conflict"]
                and "old-tip-human-binding-conflict" in reason_codes
            )
        ):
            errors.append("R8 O-anchored human response binding drifted")
    if scenario.startswith("R8-review-binding-"):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        terminal_tokens = [
            f'"{key}": "{value}"'
            for fields in (
                details.get("old_terminal_fields", {}),
                details.get("candidate_terminal_fields", {}),
            )
            for key, value in fields.items()
        ]
        reason_codes = {
            record["reason_code"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        }
        expected_status = (
            "invalid" if details["binding_conflict"] else "valid"
        )
        if (
            action is None
            or status != expected_status
            or result["classification"]
            != (
                "blocking-finding"
                if details["binding_conflict"]
                else "no-finding"
            )
            or result["event_mode"] != "direct"
            or len(result["authority_edges"]) != 1
            or result["authority_edges"][0]["parent"]
            != details["authority_parent"]
            or result["authority_edges"][0]["child"]
            != details["authority_child"]
            or result["authority_edges"][0]["problem"] is not None
            or (
                details["binding_conflict"]
                and (
                    "old-tip-human-binding-conflict" not in reason_codes
                    or not all(
                        value in action["reason"]
                        for value in (
                            details["old_binding"]
                            + details["candidate_binding"]
                        )
                    )
                    or not all(
                        token in action["reason"]
                        for token in terminal_tokens
                    )
                )
            )
            or (
                not details["binding_conflict"]
                and (
                    details["old_binding"] != details["candidate_binding"]
                    or "old-tip-human-binding-conflict" in reason_codes
                )
            )
        ):
            errors.append("R8 O-anchored review binding drifted")
    if scenario.startswith("R9-") and "review" in scenario:
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        reason_codes = {
            record["reason_code"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        }
        pending_presentations = (
            "pending",
            "PENDING",
            " PeNdInG ",
        )
        concrete_or_invalid_values = (
            "",
            "______",
            "`pending`",
            "``PENDING``",
            "pend\u0131ng",
            "`pend\u0131ng`",
            "pending-extra",
            "`pending",
            "pending`",
            "`not-pending`",
            "invalid-review-binding",
        )
        if (
            action is None
            or status != "valid"
            or result["classification"] != "no-finding"
            or result["event_mode"] != details["mode"]
            or len(result["authority_edges"]) != 1
            or result["authority_edges"][0]["parent"]
            != details["authority_parent"]
            or result["authority_edges"][0]["child"]
            != details["authority_child"]
            or result["authority_edges"][0]["problem"] is not None
            or len(propagation)
            != (1 if details["mode"] == "supplier" else 0)
            or "old-tip-human-binding-conflict" in reason_codes
            or not _Classifier.explicit_review_pending(
                details["old_pending_value"]
            )
            or _Classifier.explicit_review_pending(
                details["candidate_value"]
            )
            or not all(
                _Classifier.explicit_review_pending(value)
                for value in pending_presentations
            )
            or any(
                _Classifier.explicit_review_pending(value)
                for value in concrete_or_invalid_values
            )
        ):
            errors.append("R9 review pending normalization drifted")
    if scenario.startswith("R10-") and "review" in scenario:
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        old_reason_token = json.dumps(details["old_value"])[1:-1]
        reason_codes = {
            record["reason_code"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        }
        edge_proof_code = "foreign-or-discontinuous-carrier"
        binding_blocked = (
            status == "invalid"
            and "old-tip-human-binding-conflict" in reason_codes
        ) or (
            status == "ambiguous"
            and edge_proof_code in reason_codes
        )
        if (
            action is None
            or not binding_blocked
            or result["classification"] != "blocking-finding"
            or result["event_mode"] != details["mode"]
            or len(result["authority_edges"]) != 1
            or result["authority_edges"][0]["parent"]
            != details["authority_parent"]
            or result["authority_edges"][0]["child"]
            != details["authority_child"]
            or result["authority_edges"][0]["problem"] is not None
            or len(propagation)
            != (1 if details["mode"] == "supplier" else 0)
            or old_reason_token not in action["reason"]
            or details["candidate_value"] not in action["reason"]
            or _Classifier.explicit_review_pending(details["old_value"])
            or not _Classifier.broad_review_pending(details["old_value"])
        ):
            errors.append("R10 malformed review binding was normalized")
    if scenario.startswith("R13-") and "review-binding" in scenario:
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        reason_codes = {
            record["reason_code"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        }
        expected_status = (
            "invalid" if details["binding_conflict"] else "valid"
        )
        expected_authority = 2 if details["mode"] == "direct" else 1
        expected_propagation = 1 if details["mode"] == "supplier" else 0
        authority_pairs = {
            (edge["parent"], edge["child"])
            for edge in result["authority_edges"]
        }
        authority_by_parent = {
            edge["parent"]: edge for edge in result["authority_edges"]
        }
        source_edge = authority_by_parent.get(
            details["authority_parent"]
        )
        carrier_edge = authority_by_parent.get(details["carrier"])
        binding_reason = (
            "old-tip-human-binding-conflict" in reason_codes
        )
        binding_reason_complete = (
            result["O"] in action["reason"]
            and details["changed_field"] in action["reason"]
            and all(
                value in action["reason"]
                for value in (
                    details["old_binding"]
                    + details["carrier_binding"]
                )
                if value != "pending"
            )
        ) if action is not None and details["binding_conflict"] else True
        if (
            action is None
            or status != expected_status
            or result["classification"]
            != (
                "blocking-finding"
                if details["binding_conflict"]
                else "no-finding"
            )
            or result["event_mode"] != details["mode"]
            or len(authority) != expected_authority
            or source_edge is None
            or source_edge["problem"] is not None
            or len(propagation) != expected_propagation
            or (
                details["authority_parent"],
                details["authority_child"],
            )
            not in authority_pairs
            or (
                details["mode"] == "direct"
                and (details["carrier"], details["merge"])
                not in authority_pairs
            )
            or (
                details["mode"] == "supplier"
                and (details["carrier"], details["merge"])
                not in propagation
            )
            or (
                details["binding_conflict"]
                and (
                    (
                        details["mode"] == "supplier"
                        and not binding_reason
                    )
                    or (
                        details["mode"] == "direct"
                        and not binding_reason
                        and (
                            carrier_edge is None
                            or carrier_edge["problem"] is None
                        )
                    )
                    or (binding_reason and not binding_reason_complete)
                )
            )
            or (
                not details["binding_conflict"]
                and (
                    binding_reason
                    or any(
                        edge["problem"] is not None
                        for edge in result["authority_edges"]
                    )
                )
            )
        ):
            errors.append(
                "R13 direct/supplier parent review binding drifted"
            )
    if scenario.startswith("R13-persisted-"):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        expected_problem = details["expected_state_problem"]
        if (
            action is None
            or not details["production_identity_equal"]
            or details["low_similarity_delete_add"]
            != details["expected_low_similarity"]
            or action["paths"]["O"] != [details["old_path"]]
            or action["paths"]["N"] != [details["new_path"]]
            or action["multiplicity"]["O"] != 1
            or action["multiplicity"]["N"] != 1
            or authority
            or propagation
            or not action["mutation_edges"]
            or any(
                edge["problem"] is not None
                for edge in action["mutation_edges"]
            )
            or result["event_mode"] != "none"
            or status != ("invalid" if expected_problem else "none")
            or result["classification"]
            != ("blocking-finding" if expected_problem else "no-finding")
            or action["reason_code"]
            != (
                "persisted-endpoint-regression"
                if expected_problem
                else "identity-preserved"
            )
            or (
                expected_problem
                and "C-rooted occurrence is not continuously valid"
                not in action["reason"]
            )
        ):
            errors.append(
                "R13 persisted identity mutable-state gate drifted"
            )
    if scenario.startswith("R14-") and "carrier-" in scenario \
            and not scenario.startswith("R14-persisted-"):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        reason_codes = {
            record["reason_code"]
            for record in (
                action["reason_records"] if action is not None else []
            )
        }
        conflict = details["binding_conflict"]
        if (
            action is None
            or status != ("invalid" if conflict else "valid")
            or result["event_mode"] != details["mode"]
            or len(result["authority_edges"]) != 1
            or result["authority_edges"][0]["problem"] is not None
            or len(result["propagation_edges"])
            != (1 if details["mode"] == "supplier" else 0)
            or (
                conflict
                and "old-tip-human-binding-conflict" not in reason_codes
            )
            or (
                not conflict
                and "old-tip-human-binding-conflict" in reason_codes
            )
            or not all(
                value in action["reason"]
                for value in (
                    details["old_binding"] + details["carrier_binding"]
                )
                if value != "pending"
            )
            and conflict
        ):
            errors.append(
                "R14 unanswered published review carrier binding drifted"
            )
    if scenario.startswith("R14-persisted-"):
        action = actions[0] if len(actions) == 1 else None
        mutation_edges = action["mutation_edges"] if action else []
        if action is None or not mutation_edges:
            errors.append("R14 persisted fixture omitted mutation evidence")
        elif any(
            len(edge[key]) not in {40, 64}
            or any(
                char not in "0123456789abcdef" for char in edge[key]
            )
            for edge in mutation_edges
            for key in ("parent", "child")
        ):
            errors.append("R14 persisted fixture emitted a non-full OID")
    if scenario == "R14-persisted-hidden-bytes-low-similarity":
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        if (
            action is None
            or status != "invalid"
            or action["reason_code"] != "persisted-invalid-mutation"
            or not details["identity_equal"]
            or details["frozen_equal"]
            or not details["low_similarity_delete_add"]
            or not any(
                edge["frozen_problem"] for edge in action["mutation_edges"]
            )
        ):
            errors.append("R14 hidden protected bytes false-greened")
    if scenario in {
        "R14-persisted-intermediate-claim-regression",
        "R14-persisted-intermediate-review-regression",
    }:
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        if (
            action is None
            or status != "invalid"
            or action["reason_code"] != "persisted-invalid-mutation"
            or not any(
                edge["child"] == details["bad"]
                and details["expected_problem"]
                in (edge["production_problem"] or "")
                for edge in action["mutation_edges"]
            )
        ):
            errors.append("R14 transient candidate regression false-greened")
    if scenario == "R14-persisted-delete-recreate":
        action = actions[0] if len(actions) == 1 else None
        if (
            action is None
            or status != "ambiguous"
            or action["reason_code"] != "persisted-delete-recreate"
            or result["details"]["gap"] not in action["reason"]
        ):
            errors.append("R14 delete-recreate continuity false-greened")
    if scenario == "R14-persisted-valid-review-retraction":
        action = actions[0] if len(actions) == 1 else None
        details = result["details"]
        children = {
            edge["child"] for edge in (action["mutation_edges"] if action else [])
        }
        if (
            action is None
            or status != "none"
            or action["reason_code"] != "identity-preserved"
            or {details["published_A"], details["retracted"], details["published_B"]}
            - children
            or any(edge["problem"] for edge in action["mutation_edges"])
        ):
            errors.append("R14 production-valid review retraction blocked")
    if scenario == "R14-persisted-valid-first-response-low-similarity":
        action = actions[0] if len(actions) == 1 else None
        if (
            action is None
            or status != "none"
            or not result["details"]["low_similarity_delete_add"]
            or not any(
                edge["child"] == result["details"]["answer_commit"]
                for edge in action["mutation_edges"]
            )
            or any(edge["problem"] for edge in action["mutation_edges"])
        ):
            errors.append("R14 valid low-similarity first response blocked")
    if scenario in {
        "R14-persisted-merge-carrier-pending",
        "R14-persisted-merge-carrier-conflict",
    }:
        action = actions[0] if len(actions) == 1 else None
        conflict = result["details"]["conflict"]
        carrier_edges = [
            edge
            for edge in (action["mutation_edges"] if action else [])
            if edge["child"] == result["details"]["merge"]
            and edge["parent"] == result["details"]["carrier"]
        ]
        if (
            action is None
            or len(carrier_edges) != 1
            or carrier_edges[0]["role"] != "compatible-carrier"
            or bool(carrier_edges[0]["problem"]) != conflict
            or status != ("invalid" if conflict else "none")
            or action["reason_code"]
            != (
                "persisted-merge-carrier-conflict"
                if conflict
                else "identity-preserved"
            )
        ):
            errors.append("R14 persisted merge carrier compatibility drifted")
    if scenario.startswith("R15-old-"):
        details = result["details"]
        action = actions[0] if len(actions) == 1 else None
        negative = details["variant"] != "continuous-preserved"
        if (
            action is None
            or not details["old_text_equals_C"]
            or not details["new_text_equals_C"]
            or result["event_mode"] != "none"
            or result["classification"]
            != ("blocking-finding" if negative else "no-finding")
        ):
            errors.append("R15 old-side endpoint fixture drifted")
        elif details["variant"] in {
            "invalid-delete-recreate",
            "valid-delete-recreate",
        }:
            causal_oid = details.get("gap", details.get("authority_child"))
            if (
                status != "ambiguous"
                or action["reason_code"] != "persisted-delete-recreate"
                or causal_oid not in action["reason"]
                or details["recreated"] not in action["reason"]
                or (
                    details["variant"] == "valid-delete-recreate"
                    and details["deletion_problem"] is not None
                )
            ):
                errors.append("R15 old-side deletion/recreation false-greened")
        elif details["variant"] == "human-binding-restore":
            bad_edges = [
                edge
                for edge in action["mutation_edges"]
                if edge["child"] == details["bad"]
            ]
            if (
                status != "invalid"
                or action["reason_code"] != "persisted-invalid-mutation"
                or len(bad_edges) != 1
                or not bad_edges[0]["problem"]
            ):
                errors.append("R15 old-side human binding restore false-greened")
        elif details["variant"] == "hidden-bytes-restore":
            bad_edges = [
                edge
                for edge in action["mutation_edges"]
                if edge["child"] == details["bad"]
            ]
            if (
                status != "invalid"
                or action["reason_code"] != "persisted-invalid-mutation"
                or len(bad_edges) != 1
                or not bad_edges[0]["frozen_problem"]
            ):
                errors.append("R15 old-side hidden-byte restore false-greened")
        elif (
            status != "none"
            or action["reason_code"] != "identity-preserved"
            or any(edge["problem"] for edge in action["mutation_edges"])
            or details["old_step"]
            not in {edge["child"] for edge in action["mutation_edges"]}
        ):
            errors.append("R15 continuous old-side occurrence was blocked")
    if scenario.startswith("R16-support-"):
        variant = result["details"]["variant"]
        positive = variant in {
            "forward",
            "reverse-preserved",
            "source-evolution",
            "permutation-diamond",
        }
        support_checks = result["support_checks"]
        if result["details"]["source_problem"] is not None and variant \
                != "invalid-source":
            errors.append("R16 fixture authority edge was not production-valid")
        if variant == "invalid-source":
            if (
                status != "invalid"
                or result["details"]["source_problem"] is None
                or support_checks
            ):
                errors.append("R16 invalid source gained a certificate")
        elif (
            result["event_mode"] != "supplier"
            or not support_checks
            or any(
                len(check["authority_parent"]) not in {40, 64}
                or len(check["authority_child"]) not in {40, 64}
                or len(check["adoption_child"]) not in {40, 64}
                or not check["certificate_digest"].startswith("sha256:")
                or len(check["certificate_digest"]) != 71
                for check in support_checks
            )
            or (
                positive
                and (
                    status != "valid"
                    or any(
                        check["status"] != "valid"
                        for check in support_checks
                    )
                )
            )
            or (
                not positive
                and (
                    status != "invalid"
                    or not any(
                        check["status"] == "invalid"
                        for check in support_checks
                    )
                    or not any(
                        action["reason_code"]
                        == "supplier-support-certificate-invalid"
                        for action in actions
                    )
                )
            )
        ):
            errors.append("R16 supplier support certificate drifted")
        if variant == "source-evolution" and (
            result["details"]["source_parent"]
            == result["details"]["authority_child"]
        ):
            errors.append("R16 source evolution fixture did not evolve")
        if variant == "adoption-drift" and not any(
            check["tree_projection_status"] == "invalid"
            and check["postcondition_status"] == "valid"
            for check in support_checks
        ):
            errors.append("R16 adoption drift did not isolate projection gate")
        if variant == "permutation-diamond" and (
            len(support_checks) != 3
            or len(
                {
                    check["certificate_digest"]
                    for check in support_checks
                }
            )
            != 1
            or len(
                {check["adoption_child"] for check in support_checks}
            )
            != 3
        ):
            errors.append("R16 equal-root parent permutation drifted")
    if scenario == "R16-earlier-landed-evidence-reversal":
        support_checks = result["support_checks"]
        if (
            result["details"]["source_problem"] is not None
            or result["details"]["replay_problem"] is not None
            or result["details"]["expected_evidence"]
            == result["details"]["reverted_evidence"]
            or status != "invalid"
            or not support_checks
            or not any(
                check["tree_projection_status"] == "invalid"
                and check["postcondition_status"] == "valid"
                for check in support_checks
            )
            or not any(
                action["reason_code"]
                == "supplier-support-certificate-invalid"
                for action in actions
            )
        ):
            errors.append("R16 replay-only evidence reversal false-greened")
    if scenario.startswith("R16-pickup-evolution-"):
        target_status = result["details"]["target_status"]
        resolving = target_status in RECONCILE.RESOLVING_TASK_STATUSES
        expected_valid = resolving and not result["details"]["drop_artifact"]
        support_checks = result["support_checks"]
        evaluations = [
            evaluation
            for check in support_checks
            for evaluation in check["obligation_evaluations"]
        ]
        if (
            not support_checks
            or not evaluations
            or (
                expected_valid
                and (
                    status != "valid"
                    or any(
                        evaluation["problem"] is not None
                        for evaluation in evaluations
                    )
                )
            )
            or (
                not expected_valid
                and not result["details"]["drop_artifact"]
                and (
                    status != "invalid"
                    or not any(
                        evaluation["problem"] is not None
                        for evaluation in evaluations
                    )
                )
            )
            or (
                result["details"]["drop_artifact"]
                and (
                    status != "invalid"
                    or not any(
                        check["tree_projection_status"] == "invalid"
                        for check in support_checks
                    )
                )
            )
        ):
            errors.append("R16 typed pickup status obligation drifted")
        if target_status in {"3_in-review", "4_done"}:
            verification = next(
                (
                    path for path in result["details"]["task_artifacts"]
                    if path.endswith("/verification.md")
                ),
                None,
            )
            source_paths = {
                entry["path"]
                for check in support_checks
                for projection in check["source_projections"]
                for entry in projection["entries"]
            }
            adoption_paths = {
                entry["path"]
                for check in support_checks
                for entry in check["adoption_projection"]
            }
            if (
                verification is None
                or verification not in source_paths
                or verification not in adoption_paths
                or (
                    result["details"]["drop_artifact"]
                    and not any(
                        check["tree_projection_status"] == "invalid"
                        for check in support_checks
                    )
                )
            ):
                errors.append("R16 pickup receipt projection is incomplete")
    if scenario == "PCX-14-valid-human-supplier":
        if result["event_mode"] != "supplier" or status != "valid":
            errors.append("PCX-14 did not validate human supplier")
    if scenario == "PCX-15-generated-retry-supplier":
        if result["details"]["production_retry_identity"][0] != (
            "generated-retry"
        ):
            errors.append("PCX-15 did not use generated retry identity")
        if status != "valid" or result["event_mode"] != "supplier":
            errors.append("PCX-15 did not validate generated retry supplier")
    if scenario == "PCX-16-task-pickup-supplier":
        if result["event_mode"] != "supplier" or status != "valid":
            errors.append("PCX-16 did not use pickup authority")
    if scenario == "PCX-17-complete-cherry-pick":
        if status != "valid" or len(authority) != 1:
            errors.append("PCX-17 complete replay lost lifecycle authority")
    if scenario == "PCX-17-deletion-only-cherry-pick":
        if status != "invalid" or not any(
            edge["problem"] for edge in result["authority_edges"]
        ):
            errors.append("PCX-17 deletion-only replay borrowed a claim")
    if scenario == "P22-PCX-18-one-pass-many-actions":
        valid = sum(action["status"] == "valid" for action in actions)
        findings = sum(action["finding"] for action in actions)
        metrics = result["metrics"]
        if valid != 8 or findings != 8:
            errors.append(
                f"many-action split is {valid} valid/{findings} findings"
            )
        if metrics["graph_enumerations"] != 1:
            errors.append("many-action case enumerated the graph more than once")
        if metrics["per_action_history_walks"] != 0:
            errors.append("many-action case used per-action history walks")
        if metrics["graph_commits"] < 128:
            errors.append("many-action graph is shorter than 128 commits")
        if metrics["snapshot_cache_hits"] < 128:
            errors.append("many-action case did not reuse snapshots")
        if metrics["production_parent_queries"] != 129:
            errors.append(
                "many-action composition did not preserve 129 parent queries"
            )
    if scenario.startswith(
        (
            "R17-object-payload-peak-",
            "R17-flat-tree-peak-",
            "R17-support-serialized-",
            "R17-dynamic-support-traversal-",
            "R17-graph-output-bytes-",
            "R17-graph-line-peak-bytes-",
            "R17-graph-parent-tokens-",
        )
    ):
        counter = result["details"]["typed_budget_counter"]
        limit = result["details"]["typed_budget_limit"]
        overflow = result["details"]["overflow_by_one"]
        empty_result = not any(
            result[key]
            for key in (
                "actions",
                "authority_edges",
                "carry_proofs",
                "mutation_edges",
                "propagation_edges",
                "support_checks",
            )
        )
        if overflow:
            if (
                result["audit_exit"] != 2
                or status != "ambiguous"
                or result["metrics"][counter] != limit + 1
                or not empty_result
                or counter not in result["evidence_verdict"]["reason"]
            ):
                errors.append(
                    f"{scenario} did not refuse exact-plus-one work transactionally"
                )
        elif (
            result["audit_exit"] != 0
            or result["classification"] != "no-finding"
            or result["metrics"][counter] != limit
        ):
            errors.append(f"{scenario} did not admit its exact work budget")
        if scenario.startswith("R17-object-payload-peak-") and (
            result["details"]["largest_queue_blob_bytes"] != 1_000_000
            or result["details"]["unbudgeted_counter_value"] != 1_000_000
        ):
            errors.append("one-million-byte object admission fixture drifted")
        if scenario.startswith("R17-graph-") and (
            result["metrics"]["graph_stream_peak_chunk_bytes"] > 256
            or result["metrics"]["graph_buffered_bytes"] != 0
            or result["metrics"]["graph_process_reaps"] != 1
        ):
            errors.append("graph budget did not retain its streaming bound")
    if scenario == "R17-precharge-P22-budget":
        metrics = result["metrics"]
        limit = result["details"]["budget_limit"]
        counter = result["details"]["budget_counter"]
        if (
            result["audit_exit"] != 2
            or result["classification"] != "blocking-finding"
            or status != "ambiguous"
            or metrics[counter] != limit + 1
            or metrics["git_processes"] > 4
            or actions
            or authority
            or result["carry_proofs"]
            or result["mutation_edges"]
            or result["propagation_edges"]
            or result["support_checks"]
            or counter not in result["evidence_verdict"]["reason"]
            or any(
                metrics[name] != 0
                for name in result["details"]["later_counters_unchanged"]
            )
        ):
            errors.append("P22 budget did not refuse the first excess work")
    if scenario == "PCX-19-missing-claim-blob-recovery":
        recovery = result.get("recovery", {})
        if (
            recovery.get("first_status") != "unreadable"
            or recovery.get("second_status") != "valid"
            or not recovery.get("same_process")
            or not recovery.get("same_reader")
            or "missing" not in (recovery.get("first_reader_reason") or "")
            or recovery.get("missing_cached")
            or recovery.get("restored_kind") != "blob"
            or recovery.get("restored_payload_size", 0) <= 0
            or not recovery.get("success_cached")
            or not recovery.get("cache_hit_after_restore")
            or not recovery.get("cached_bytes_equal")
        ):
            errors.append("PCX-19 missing object recovery failed")
    if scenario == "PCX-20b-budget-overflow":
        limit = result["details"]["demonstration_limit"]
        overflows = sorted(
            (key, value)
            for key, value in result["metrics"].items()
            if value > limit
        )
        if (
            actions
            or status != "ambiguous"
            or result["audit_exit"] != 2
            or len(overflows) != 1
            or overflows[0][1] != limit + 1
            or result["authority_edges"]
            or result["propagation_edges"]
            or result["mutation_edges"]
            or result["support_checks"]
            or result["carry_proofs"]
        ):
            errors.append("budget overflow leaked a partial result")
    if scenario == "PCX-20a-budget-below-limit":
        if status != "valid" or not actions:
            errors.append("below-limit budget did not return normal verdict")
    if scenario.startswith("R18-"):
        details = result["details"]
        if details.get("case") == "origin-execution-bound":
            counter = details["counter"]
            if details["overflow_by_one"]:
                if (
                    result["audit_exit"] != 2
                    or result["classification"] != "blocking-finding"
                    or result["metrics"][counter]
                    != details["typed_budget_limit"] + 1
                    or any(
                        result[key]
                        for key in (
                            "actions",
                            "authority_edges",
                            "carry_proofs",
                            "mutation_edges",
                            "propagation_edges",
                            "support_checks",
                        )
                    )
                ):
                    errors.append(
                        "R18 origin +1 bound leaked partial semantic results"
                    )
            elif (
                result["audit_exit"] != 0
                or result["metrics"][counter] != details["measured"]
            ):
                errors.append("R18 exact origin bound did not pass")
        elif details.get("case") == "unreadable-object":
            if status != "unreadable" or actions:
                errors.append("R18 unreadable birth object leaked a result")
        else:
            expected_code = details.get("expected_origin_code")
            matching = [
                action
                for action in actions
                if action["reason_code"] == expected_code
            ]
            if expected_code is not None and not matching:
                errors.append(
                    f"R18 did not expose expected reason {expected_code}"
                )
            origin_actions = [
                action
                for action in actions
                if action["origin_proofs"]
                or action["event_mode"].startswith("origin-")
            ]
            if details.get("case") != "O-only-post-C-loss":
                if len(origin_actions) != 1:
                    errors.append("R18 did not isolate one target origin action")
                else:
                    action = origin_actions[0]
                    expected_witness = details.get(
                        "expected_witness_match"
                    )
                    if (
                        expected_witness is not None
                        and action["birth_witness_match"]
                        is not expected_witness
                    ):
                        errors.append("R18 birth witness comparison drifted")
                    if len(action["origin_proofs"]) != 2:
                        errors.append("R18 did not inspect both C..O/C..N arms")
                    if details.get("case") == (
                        "review-publication-equivalence"
                    ):
                        mutation_edges = [
                            edge
                            for proof in action["origin_proofs"]
                            for edge in proof["edges"]
                        ]
                        if (
                            any(
                                proof["status"] != "valid"
                                for proof in action["origin_proofs"]
                            )
                            or details["landmarks"]["old_publication"]
                            not in {
                                edge["child"] for edge in mutation_edges
                            }
                            or any(
                                edge["production_problem"] is not None
                                or edge["frozen_problem"] is not None
                                or edge["regression_problem"] is not None
                                or edge["problem"] is not None
                                for edge in mutation_edges
                            )
                            or any(action["endpoint_checks"].values())
                        ):
                            errors.append(
                                "R18 legal review publication edge was not "
                                "accepted by every production mutation check"
                            )
                    if details.get("case") in {
                        "agent-born-claimed",
                        "human-born-answered",
                    } and not any(
                        proof["birth_schema_problems"]
                        for proof in action["origin_proofs"]
                    ):
                        errors.append(
                            "R18 illegal typed birth escaped the birth schema"
                        )
                    if (
                        details.get("case", "").startswith("review-")
                        and "merge" in details["landmarks"]
                    ):
                        candidate = action["origin_proofs"][1]
                        merge_landmarks = details["landmarks"]
                        merge = merge_landmarks["merge"]
                        merge_edges = [
                            edge
                            for edge in candidate["edges"]
                            if edge["child"] == merge
                        ]
                        sources = merge_landmarks["sources"]
                        carriers = merge_landmarks["carriers"]
                        selected_sources = [
                            edge["parent"]
                            for edge in merge_edges
                            if edge["role"] == "source"
                        ]
                        compatible = [
                            edge
                            for edge in merge_edges
                            if edge["role"] == "compatible-carrier"
                        ]
                        incompatible = merge_landmarks["incompatible"]
                        valid_source_candidates = [
                            edge["parent"]
                            for edge in merge_edges
                            if edge["production_problem"] is None
                            and edge["frozen_problem"] is None
                            and edge["regression_problem"] is None
                        ]
                        lexical_relation = merge_landmarks[
                            "lexical_relation"
                        ]
                        duplicate_parent_header = merge_landmarks[
                            "duplicate_parent_header"
                        ]
                        if (
                            len(merge_edges) != len(sources) + len(carriers)
                            or not valid_source_candidates
                            or selected_sources != [min(valid_source_candidates)]
                            or len(compatible) != len(merge_edges) - 1
                            or (
                                not incompatible
                                and (
                                    action["reason_code"]
                                    != "origin-strategy-U-equivalent-live-incarnation"
                                    or any(edge["problem"] for edge in merge_edges)
                                )
                            )
                            or (
                                incompatible
                                and (
                                    action["reason_code"]
                                    != "origin-incompatible-carrier"
                                    or sum(
                                        edge["problem"] is not None
                                        for edge in merge_edges
                                    )
                                    != 1
                                )
                            )
                            or (
                                lexical_relation == "source-low"
                                and not all(sources[0] < oid for oid in carriers)
                            )
                            or (
                                lexical_relation == "source-high"
                                and not all(sources[0] > oid for oid in carriers)
                            )
                            or (
                                duplicate_parent_header
                                and (
                                    merge_landmarks["fsck_returncode"] != 0
                                    or len(
                                        merge_landmarks["raw_parent_headers"]
                                    )
                                    != 3
                                    or merge_landmarks[
                                        "raw_parent_headers"
                                    ].count(sources[0])
                                    != 2
                                    or len(
                                        merge_landmarks[
                                            "logical_parent_oids"
                                        ]
                                    )
                                    != 2
                                    or len(selected_sources) != 1
                                    or len(compatible) != 1
                                )
                            )
                        ):
                            errors.append(
                                "R19 review merge lost deterministic source/carrier roles"
                            )
            if (
                details.get("case") == "neutral-pre-origin-merge"
                and origin_actions
                and not all(
                    proof["prebirth_neutral"]
                    for proof in origin_actions[0]["origin_proofs"]
                )
            ):
                errors.append("R18 rejected or hid neutral pre-birth parents")
            if details.get("case") == "rename-timing-move" and (
                not origin_actions
                or origin_actions[0]["birth_witness_match"] is not True
            ):
                errors.append("R18 birth witness accidentally included path")
    return errors


def control_builder(name: str, root: Path):
    if name == "buffered-graph-output":
        return (
            r17_boundary_budget_fixture(root),
            Damage(buffered_graph_output=True),
            "blocking-finding",
        )
    if name == "unmetered-object-payload":
        return (
            r17_large_object_budget(root, overflow=True),
            Damage(unmetered_object_bytes=True),
            "no-finding",
        )
    if name == "unmetered-tree-paths":
        return (
            r17_wide_tree_budget(root, overflow=True),
            Damage(unmetered_tree_paths=True),
            "no-finding",
        )
    if name == "unmetered-dynamic-support":
        return (
            r17_dynamic_support_budget(root, overflow=True),
            Damage(unmetered_dynamic_support=True),
            "no-finding",
        )
    if name == "unmetered-support-construction":
        return (
            r17_support_serialization_budget(root, overflow=True),
            Damage(unmetered_support_construction=True),
            "no-finding",
        )
    if name == "restore-universal-ancestor-carry-scan":
        return (
            r17_outside_c_neutral_parent(root),
            Damage(
                universal_ancestor_carry_scan=True,
                reopen_outside_c_boundary_ancestry=True,
            ),
            "blocking-finding",
        )
    if name == "ignore-outside-C-carrier":
        return (
            r17_carry_merge_fixture(root, variant="outside-single"),
            Damage(ignore_outside_c_collision=True),
            "no-finding",
        )
    if name == "ignore-absent-C-arm":
        return (
            r17_carry_merge_fixture(root, variant="absent-arm"),
            Damage(ignore_absent_c_arm=True),
            "no-finding",
        )
    if name == "ignore-persisted-outside-C-collision":
        return (
            r17_persisted_carry_fixture(root, variant="outside-single"),
            Damage(ignore_outside_c_collision=True),
            "no-finding",
        )
    if name == "ignore-persisted-absent-C-arm":
        return (
            r17_persisted_carry_fixture(root, variant="valid-absent-arm"),
            Damage(ignore_absent_c_arm=True),
            "no-finding",
        )
    if name == "first-parent-carry-proof":
        return (
            r17_carry_merge_fixture(root, variant="incompatible"),
            Damage(first_parent_carry_only=True),
            "no-finding",
        )
    if name == "skip-carry-compatibility":
        return (
            r17_carry_merge_fixture(root, variant="incompatible"),
            Damage(skip_carry_compatibility=True),
            "no-finding",
        )
    if name == "unmetered-cone-work":
        return (
            r17_boundary_budget_fixture(root),
            Damage(unmetered_cone_work=True),
            "no-finding",
        )
    if name == "posthoc-budget-accounting":
        return (
            r17_precharge_many_actions_budget(root),
            Damage(posthoc_budget_accounting=True),
            "blocking-finding",
        )
    if name == "reopen-outside-C-boundary-ancestry":
        return (
            r17_unopened_outside_c_ancestor(root),
            Damage(reopen_outside_c_boundary_ancestry=True),
            "unreadable",
        )
    if name == "ignore-invalid-N-root":
        return (
            r3_valid_plus_invalid_at_N(root),
            Damage(sole_valid_ignores_competitors=True),
            "no-finding",
        )
    if name == "missing-all-parent-direct-validation":
        return (
            direct_merge_fixture(
                root,
                "CONTROL-missing-all-parent-direct-validation",
                parent_count=2,
                invalid_parent=1,
                neutral_parent=True,
            ),
            Damage(validate_all_direct_parents=False),
            "no-finding",
        )
    if name == "supplier-authority-borrowing":
        return (
            supplier_fixture(
                root,
                "CONTROL-supplier-authority-borrowing",
                supplier_valid=False,
                carrier_claimed=True,
                merge_changes_evidence=True,
            ),
            Damage(allow_supplier_borrow=True),
            "no-finding",
        )
    if name == "identity-multiplicity-collapsed-to-set":
        return (
            p5_duplicate_at_c(root),
            Damage(collapse_multiplicity=True),
            "no-finding",
        )
    if name == "reopen-pre-C-genealogy":
        return (
            p4_pre_c_origins(root),
            Damage(reopen_pre_c_genealogy=True),
            "blocking-finding",
        )
    if name == "missing-post-event-continuity":
        return (
            p17_post_event_reintroduction(root),
            Damage(enforce_post_event_absence=False),
            "no-finding",
        )
    if name == "sole-valid-ignores-invalid-root":
        return (
            r6_all_absent_roots(
                root, first_valid=True, second_kind="invalid"
            ),
            Damage(sole_valid_ignores_competitors=True),
            "no-finding",
        )
    if name == "omit-old-tip-human-binding":
        return (
            r8_review_terminal_binding_conflict(root),
            Damage(omit_old_tip_human_binding=True),
            "no-finding",
        )
    if name == "literal-review-pending-treated-concrete":
        return (
            r9_review_pending_binding(
                root, mode="direct", pending_field="Review target"
            ),
            Damage(treat_review_pending_as_concrete=True),
            "blocking-finding",
        )
    if name == "broad-review-pending-normalization":
        return (
            r10_malformed_review_binding(
                root,
                mode="direct",
                field="Review target",
                malformed_value="pend\u0131ng",
                slug="backtick-dotless",
            ),
            Damage(broad_review_pending_normalization=True),
            "no-finding",
        )
    if name == "omit-supplier-carrier-human-binding":
        return (
            r13_review_parent_binding(
                root, mode="supplier", variant="target"
            ),
            Damage(omit_supplier_carrier_human_binding=True),
            "no-finding",
        )
    if name == "skip-preserved-state-validation":
        return (
            r13_persisted_state(root, "claim-loss"),
            Damage(skip_preserved_state_validation=True),
            "no-finding",
        )
    if name == "omit-unanswered-published-review-binding":
        return (
            r14_review_carrier_binding(
                root,
                mode="supplier",
                carrier_variant="target",
                old_answered=True,
            ),
            Damage(omit_unanswered_published_review_binding=True),
            "no-finding",
        )
    if name == "skip-persisted-frozen-skeleton":
        return (
            r14_persisted_hidden_bytes(root),
            Damage(skip_persisted_frozen_skeleton=True),
            "no-finding",
        )
    if name == "skip-persisted-candidate-continuity":
        return (
            r14_persisted_intermediate_claim(root),
            Damage(skip_persisted_candidate_continuity=True),
            "no-finding",
        )
    if name == "skip-old-side-continuity":
        return (
            r15_old_side_continuity(root, "invalid-delete-recreate"),
            Damage(skip_old_side_continuity=True),
            "no-finding",
        )
    if name == "skip-supplier-support-certificate":
        return (
            r16_supplier_support_fixture(root, "reverse-drop"),
            Damage(skip_supplier_support_certificate=True),
            "no-finding",
        )
    if name == "endpoint-only-origin-equality":
        return (
            _r18_origin_fixture(
                root, case="transient-protected-mutation"
            ),
            Damage(endpoint_only_origin_equality=True),
            "no-finding",
        )
    if name == "skip-origin-birth-uniqueness":
        return (
            _r18_origin_fixture(root, case="second-birth"),
            Damage(skip_origin_birth_uniqueness=True),
            "no-finding",
        )
    if name == "skip-origin-post-birth-absence":
        return (
            _r18_origin_fixture(
                root, case="inherited-then-deleted-merge-arm"
            ),
            Damage(skip_origin_post_birth_absence=True),
            "no-finding",
        )
    if name == "skip-origin-endpoint-non-regression":
        return (
            _r18_origin_fixture(root, case="endpoint-regression"),
            Damage(skip_origin_endpoint_non_regression=True),
            "no-finding",
        )
    if name == "reject-all-origin-invalid-carriers":
        return (
            _r18_origin_fixture(root, case="review-compatible-merge"),
            Damage(reject_all_origin_invalid_carriers=True),
            "blocking-finding",
        )
    raise ValueError(name)


_INTENDED_PUBLIC_API = (
    "EventEndpoints",
    "EventInputError",
    "GitSpawnObserver",
    "TrustedGitRunner",
    "audit_event",
    "event_endpoints",
    "main",
)


def _public_strategy_exposures(namespace: Mapping[str, Any]) -> list[str]:
    """Name public local callables exposing Strategy B selection."""
    exposed = []
    for name, subject in namespace.items():
        if name.startswith("_") or not callable(subject):
            continue
        if getattr(subject, "__module__", None) != __name__:
            continue
        try:
            parameters = inspect.signature(subject).parameters
            source = inspect.getsource(subject)
        except (OSError, TypeError, ValueError):
            continue
        if (
            "origin_strategy" in parameters
            or any(
                parameter.annotation in {"_Fixture", _Fixture}
                for parameter in parameters.values()
            )
            or '"B"' in source
            or "'B'" in source
        ):
            exposed.append(name)
    return sorted(exposed)


def _public_private_aliases(
    namespace: Mapping[str, Any], private_subjects: tuple[Any, ...]
) -> list[str]:
    """Name public aliases of private Strategy B diagnostic surfaces."""
    return sorted(
        name
        for name, subject in namespace.items()
        if not name.startswith("_")
        and any(subject is private for private in private_subjects)
    )


def _event_adapter_control(root: Path) -> dict:
    """Prove the public event boundary is session-local and result-owning."""
    fixtures = {
        "clean": r19_event_workflow_fixture(
            root / "clean", transport="push"
        ),
        "blocking": r19_event_workflow_fixture(
            root / "blocking", transport="pre-push", attack=True
        ),
        "unavailable": r19_event_workflow_fixture(
            root / "unavailable",
            transport="pull-request-synchronize",
            failure="head-mismatch",
        ),
    }
    clean_input = fixtures["clean"].details["event_adapter_input"]
    blocking_input = fixtures["blocking"].details["event_adapter_input"]

    def process_is_gone(pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        return False

    def open_descriptor_count():
        for directory in (Path("/dev/fd"), Path("/proc/self/fd")):
            try:
                return len(tuple(directory.iterdir()))
            except OSError:
                continue
        return None

    class RecordingRunner:
        def __init__(
            self,
            delegate=REAL_POPEN,
            *,
            fail_ordinal=None,
            failure=None,
        ):
            self.delegate = delegate
            self.fail_ordinal = fail_ordinal
            self.failure = failure
            self.calls = []
            self.created = []

        def __call__(self, command, *args, **kwargs):
            self.calls.append(tuple(str(value) for value in command))
            if len(self.calls) == self.fail_ordinal:
                raise self.failure or RuntimeError(
                    "injected runner ordinal failure"
                )
            process = self.delegate(command, *args, **kwargs)
            self.created.append(process.pid)
            return process

    class ObserverBaseException(BaseException):
        pass

    def seam_probe(
        event_kind: Any,
        payload: Any,
        *,
        budget_limit: Any = None,
        repository: Path | None = None,
        runner=None,
        runner_fail_ordinal=None,
        runner_failure=None,
        observer_failure=None,
        observer_fail_ordinal=1,
        transaction_stage=None,
        transaction_failure=None,
        truthy_exit=False,
        trace_cancellation_boundary=None,
        trace_session_boundary=None,
        trace_spawn_boundary=None,
    ):
        before_spawns = []
        after_spawns = []
        observed_sessions = []
        observation_order = []
        lifecycle = {
            "factory": 0,
            "enter": 0,
            "exit": 0,
            "exit_after_reap": None,
            "exit_exception": None,
        }
        private_prefix = (
            __name__.replace(".", "_") + "_private_reconcile_"
        )
        private_before = {
            key for key in sys.modules if key.startswith(private_prefix)
        }
        active_reconciler_before = ACTIVE_RECONCILE.get()
        active_runner = (
            runner
            if runner is not None
            else RecordingRunner(
                fail_ordinal=runner_fail_ordinal,
                failure=runner_failure,
            )
        )

        def arm_cancellation(target, boundary, stage):
            source_lines, source_start = inspect.getsourcelines(target)
            marker = boundary.__name__ + '("' + stage + '")'
            matches = [
                source_start + index
                for index, line in enumerate(source_lines)
                if marker in line
            ]
            if len(matches) != 1:
                raise AssertionError(
                    f"{target.__name__} boundary marker is not unique"
                )
            target_line = matches[0]

            def cancel_at_boundary(frame, event, _argument):
                if (
                    frame.f_code is target.__code__
                    and event == "line"
                    and frame.f_lineno == target_line
                ):
                    sys.settrace(None)
                    raise KeyboardInterrupt(
                        "injected cancellation at " + stage
                    )
                return cancel_at_boundary

            frame = sys._getframe()
            while frame is not None:
                if frame.f_code is target.__code__:
                    frame.f_trace = cancel_at_boundary
                    break
                frame = frame.f_back
            sys.settrace(cancel_at_boundary)

        class AccountingObserver:
            def before_spawn(self, command):
                before_spawns.append(command)
                active_reconciler = ACTIVE_RECONCILE.get()
                active_session = getattr(
                    getattr(active_reconciler, "subprocess", None),
                    "_session",
                    None,
                )
                if active_session is not None and all(
                    active_session is not item for item in observed_sessions
                ):
                    observed_sessions.append(active_session)

            def after_spawn(self, command, pid):
                after_spawns.append((command, pid))
                if (
                    observer_failure is not None
                    and len(after_spawns) == observer_fail_ordinal
                ):
                    raise observer_failure

        class Transaction:
            def __enter__(self):
                observation_order.append("transaction-enter")
                lifecycle["enter"] += 1
                if transaction_stage == "enter":
                    raise transaction_failure
                if trace_cancellation_boundary is not None:
                    arm_cancellation(
                        audit_event,
                        _transaction_boundary,
                        trace_cancellation_boundary,
                    )
                return AccountingObserver()

            def __exit__(self, exc_type, exc, traceback):
                observation_order.append("transaction-exit")
                lifecycle["exit"] += 1
                lifecycle["exit_exception"] = (
                    exc_type.__name__ if exc_type is not None else None
                )
                lifecycle["exit_after_reap"] = all(
                    process_is_gone(pid) for _command, pid in after_spawns
                )
                if transaction_stage == "exit":
                    raise transaction_failure
                return truthy_exit

        def transaction():
            observation_order.append("transaction-factory")
            lifecycle["factory"] += 1
            if transaction_stage == "factory":
                raise transaction_failure
            return Transaction()

        result = None
        caught = None
        gc.collect()
        descriptors_before = open_descriptor_count()
        try:
            if trace_session_boundary is not None:
                arm_cancellation(
                    RepositorySession.open,
                    _session_boundary,
                    trace_session_boundary,
                )
            if trace_spawn_boundary is not None:
                arm_cancellation(
                    spawn_git_process,
                    _spawn_boundary,
                    trace_spawn_boundary,
                )
            result = audit_event(
                repository or fixtures["clean"].repo.root,
                event_kind,
                payload,
                git_runner=active_runner,
                budget_limit=budget_limit,
                transaction=transaction,
            )
            observation_order.append("audit-returned")
        except BaseException as error:
            caught = error
            observation_order.append("audit-raised")
        finally:
            sys.settrace(None)
        gc.collect()
        descriptors_after = open_descriptor_count()
        private_after = {
            key for key in sys.modules if key.startswith(private_prefix)
        }
        observed_pids = [pid for _command, pid in after_spawns]
        metrics = result.get("metrics", {}) if result is not None else {}
        observation_order.append("metrics-read")
        runner_calls = getattr(active_runner, "calls", ())
        runner_created = getattr(active_runner, "created", ())
        canonical_json_serializable = False
        projected_event_kind = None
        if result is not None:
            projected_event_kind = result.get("event_adapter", {}).get(
                "event_kind"
            )
            try:
                json.dumps(
                    result,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
            except (TypeError, ValueError):
                pass
            else:
                canonical_json_serializable = True
        return {
            "adapter_status": (
                result.get("event_adapter", {}).get("status")
                if result is not None
                else None
            ),
            "after": len(after_spawns),
            "all_pids_reaped": all(
                process_is_gone(pid) for pid in observed_pids
            ),
            "all_runner_pids_reaped": all(
                process_is_gone(pid)
                for pid in getattr(active_runner, "created", ())
            ),
            "attempts": metrics.get("git_process_attempts"),
            "actual": metrics.get("git_processes"),
            "audit_exit": (
                result.get("audit_exit") if result is not None else None
            ),
            "before": len(before_spawns),
            "canonical_json_serializable": canonical_json_serializable,
            "caught": type(caught).__name__ if caught is not None else None,
            "classification": (
                result.get("classification") if result is not None else None
            ),
            "commands_match": (
                before_spawns
                == [command for command, _pid in after_spawns]
            ),
            "created": metrics.get("git_processes"),
            "cache_state": {
                "active_reconciler_restored": (
                    ACTIVE_RECONCILE.get() is active_reconciler_before
                ),
                "carry_cache_entries": sum(
                    len(session.carry_proof_cache)
                    for session in observed_sessions
                ),
                "object_databases_detached": all(
                    session.object_database is None
                    for session in observed_sessions
                ),
                "owners": len(observed_sessions),
                "owners_closed": all(
                    session._closed for session in observed_sessions
                ),
                "pipe_registries_empty": all(
                    not session.explicit_pipe_resources
                    for session in observed_sessions
                ),
                "process_registries_empty": all(
                    not session.processes for session in observed_sessions
                ),
                "reconciler_modules_detached": all(
                    session.reconcile is None
                    for session in observed_sessions
                ),
            },
            "fd_delta": (
                descriptors_after - descriptors_before
                if descriptors_before is not None
                and descriptors_after is not None
                else None
            ),
            "lifecycle": lifecycle,
            "observation_order": observation_order,
            "private_modules_leaked": sorted(
                private_after - private_before
            ),
            "projected_event_kind": projected_event_kind,
            "reason": (
                result.get("evidence_verdict", {}).get("reason")
                if result is not None
                else None
            ),
            "runner_calls": len(runner_calls),
            "runner_created": len(runner_created),
            "typed_origin_strategy": (
                result.get("input_contract", {}).get("origin_strategy")
                if result is not None
                else None
            ),
        }

    observations = {}
    for label, fixture in fixtures.items():
        adapter_input = fixture.details["event_adapter_input"]
        payload_path = root / f"{label}-event.json"
        payload_path.write_bytes(
            json.dumps(
                adapter_input["payload"],
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )
        completed = REAL_RUN(
            [
                sys.executable,
                str(HERE),
                "--repo",
                str(fixture.repo.root),
                "--event-kind",
                adapter_input["event_kind"],
                "--event-payload",
                str(payload_path),
            ],
            check=False,
            env=stable_git_environment(),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        try:
            cli_result = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            cli_result = {}
        imported_result = audit_event(
            fixture.repo.root,
            adapter_input["event_kind"],
            adapter_input["payload"],
            git_runner=_trusted_git_runner(),
        )
        imported_bytes = json.dumps(
            imported_result,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8") + b"\n"
        observations[label] = {
            "adapter_status": cli_result.get("event_adapter", {}).get(
                "status"
            ),
            "classification": cli_result.get("classification"),
            "cli_bytes_sha256": "sha256:" + hashlib.sha256(
                completed.stdout
            ).hexdigest(),
            "exit": completed.returncode,
            "import_bytes_sha256": "sha256:" + hashlib.sha256(
                imported_bytes
            ).hexdigest(),
            "import_cli_bytes_equal": completed.stdout == imported_bytes,
            "stdout_canonical": (
                bool(cli_result)
                and completed.stdout
                == json.dumps(
                    cli_result,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            ),
            "typed_origin_strategy": cli_result.get(
                "input_contract", {}
            ).get("origin_strategy"),
            "typed_results_equal": cli_result == imported_result,
        }

    typed_cli_inputs = {}
    for label, event_kind, payload in (
        ("non-mapping-payload", "local", []),
        ("unsupported-event-kind", "not-a-transport", {}),
    ):
        payload_path = root / f"{label}.json"
        payload_path.write_bytes(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )
        completed = REAL_RUN(
            [
                sys.executable,
                str(HERE),
                "--repo",
                str(fixtures["clean"].repo.root),
                "--event-kind",
                event_kind,
                "--event-payload",
                str(payload_path),
            ],
            check=False,
            env=stable_git_environment(),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        result = json.loads(completed.stdout.decode("utf-8"))
        typed_cli_inputs[label] = {
            "adapter_status": result["event_adapter"]["status"],
            "audit_exit": completed.returncode,
            "classification": result["classification"],
            "stdout_canonical": completed.stdout == (
                json.dumps(
                    result,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            ),
        }

    execution_seam = {
        "valid": seam_probe(
            clean_input["event_kind"], clean_input["payload"]
        ),
        "blocking": seam_probe(
            blocking_input["event_kind"],
            blocking_input["payload"],
            repository=fixtures["blocking"].repo.root,
        ),
        "invalid": seam_probe("local", {"new": "1" * 40}),
    }
    execution_seam["blocking"]["cli_import_byte_parity"] = {
        "bytes_equal": observations["blocking"][
            "import_cli_bytes_equal"
        ],
        "cli_sha256": observations["blocking"]["cli_bytes_sha256"],
        "import_sha256": observations["blocking"][
            "import_bytes_sha256"
        ],
    }
    same_oid = fixtures["clean"].O
    execution_seam["identical_endpoint_rejections"] = {
        transport: seam_probe(transport, payload)
        for transport, payload in {
            "local": {"old": same_oid, "new": same_oid},
            "pre-push": {"old": same_oid, "new": same_oid},
            "push": {"before": same_oid, "after": same_oid},
            "pull-request-synchronize": {
                "before": same_oid,
                "after": same_oid,
                "pull_request": {"head": {"sha": same_oid}},
            },
        }.items()
    }
    execution_seam["invalid_budget_rejections"] = {
        label: seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            budget_limit=value,
        )
        for label, value in (
            ("zero", 0),
            ("negative", -1),
            ("bool-false", False),
            ("bool-true", True),
            ("float", 1.0),
            ("string", "1"),
        )
    }

    class UnhashableString(str):
        __hash__ = None

        def __eq__(self, _other):
            raise AssertionError("event-kind equality reached")

        def __repr__(self):
            raise AssertionError("event-kind repr reached")

        def __str__(self):
            raise AssertionError("event-kind str reached")

    execution_seam["invalid_runtime_inputs"] = {
        label: seam_probe(event_kind, payload)
        for label, event_kind, payload in (
            ("payload-none", "local", None),
            ("payload-list", "local", []),
            ("payload-int", "local", 7),
            ("event-kind-list", ["local"], clean_input["payload"]),
            (
                "event-kind-dict",
                {"kind": "local"},
                clean_input["payload"],
            ),
            (
                "event-kind-unhashable-str-subclass",
                UnhashableString("local"),
                clean_input["payload"],
            ),
            (
                "event-kind-plain-object",
                object(),
                clean_input["payload"],
            ),
        )
    }

    baseline_attempts = execution_seam["valid"]["attempts"] or 0
    execution_seam["runner_ordinal_failures"] = {
        str(ordinal): seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            runner_fail_ordinal=ordinal,
            runner_failure=RuntimeError(
                f"injected runner failure {ordinal}"
            ),
        )
        for ordinal in range(1, baseline_attempts + 1)
    }

    class DirectBaseException(BaseException):
        pass

    execution_seam["runner_throwables"] = {
        label: seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            runner_fail_ordinal=1,
            runner_failure=error,
        )
        for label, error in (
            ("runtime", RuntimeError("runner runtime")),
            ("subprocess", subprocess.SubprocessError("runner subprocess")),
            ("direct-base", DirectBaseException("runner direct base")),
        )
    }
    execution_seam["runner_cancellation"] = seam_probe(
        clean_input["event_kind"],
        clean_input["payload"],
        runner_fail_ordinal=1,
        runner_failure=KeyboardInterrupt("runner cancellation"),
    )
    execution_seam["observer_throwables"] = {
        "runtime": seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            observer_failure=RuntimeError("observer runtime"),
        ),
        "direct-base": seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            observer_failure=ObserverBaseException("observer base"),
        ),
        "keyboard": seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            observer_failure=KeyboardInterrupt("observer cancellation"),
        ),
    }

    transaction_throwables = {}
    for stage in ("factory", "enter", "exit"):
        for label, error in (
            ("runtime", RuntimeError(f"{stage} runtime")),
            ("direct-base", DirectBaseException(f"{stage} base")),
        ):
            transaction_throwables[f"{stage}-{label}"] = seam_probe(
                clean_input["event_kind"],
                clean_input["payload"],
                transaction_stage=stage,
                transaction_failure=error,
            )
    execution_seam["transaction_throwables"] = transaction_throwables
    execution_seam["transaction_cancellations"] = {
        stage: seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            transaction_stage=stage,
            transaction_failure=KeyboardInterrupt(
                f"{stage} cancellation"
            ),
        )
        for stage in ("factory", "enter", "exit")
    }
    execution_seam["trace_cancellation_boundaries"] = {
        stage: seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            trace_cancellation_boundary=stage,
        )
        for stage in ("after-enter", "after-session-close")
    }
    execution_seam["session_setup_cancellation_boundaries"] = {
        stage: seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            trace_session_boundary=stage,
        )
        for stage in ("after-reconciler-load", "after-context-set")
    }
    execution_seam["spawn_construction_cancellation_boundaries"] = {
        stage: seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            trace_spawn_boundary=stage,
        )
        for stage in (
            "after-runner-publication",
            "after-runner-return",
            "after-pipe-attachment",
        )
    }
    execution_seam["truthy_exit_ignored"] = seam_probe(
        clean_input["event_kind"],
        clean_input["payload"],
        truthy_exit=True,
    )
    execution_seam["noncallable_runner"] = seam_probe(
        clean_input["event_kind"],
        clean_input["payload"],
        runner=object(),
    )

    ambient_module = subprocess
    ambient_popen_identity = ambient_module.Popen

    class PoisonAmbientSubprocess:
        PIPE = ambient_module.PIPE
        DEVNULL = ambient_module.DEVNULL
        TimeoutExpired = ambient_module.TimeoutExpired
        CalledProcessError = ambient_module.CalledProcessError
        CompletedProcess = ambient_module.CompletedProcess
        SubprocessError = ambient_module.SubprocessError

        @staticmethod
        def Popen(*_args, **_kwargs):
            raise AssertionError("ambient Popen reached")

        @staticmethod
        def run(*_args, **_kwargs):
            raise AssertionError("ambient run reached")

    poison_runner = RecordingRunner()
    globals()["subprocess"] = PoisonAmbientSubprocess
    try:
        poison_probe = seam_probe(
            clean_input["event_kind"],
            clean_input["payload"],
            runner=poison_runner,
        )
    finally:
        globals()["subprocess"] = ambient_module
    execution_seam["hostile_ambient_subprocess"] = {
        **poison_probe,
        "popen_identity_unchanged": (
            ambient_module.Popen is ambient_popen_identity
            and subprocess.Popen is ambient_popen_identity
        ),
    }

    def concurrency_probe(modules, selected_fixtures, shared_runner):
        barrier = threading.Barrier(2)
        results = [None, None]
        failures = [None, None]
        observations_by_index = [([], []), ([], [])]

        class ConcurrentObserver:
            def __init__(self, index):
                self.index = index

            def before_spawn(self, command):
                observations_by_index[self.index][0].append(command)

            def after_spawn(self, command, pid):
                observations_by_index[self.index][1].append(
                    (command, pid)
                )

        class ConcurrentTransaction:
            def __init__(self, index):
                self.index = index

            def __enter__(self):
                barrier.wait(timeout=20)
                return ConcurrentObserver(self.index)

            def __exit__(self, exc_type, exc, traceback):
                return False

        def worker(index):
            module = modules[index]
            fixture = selected_fixtures[index]
            adapter = fixture.details["event_adapter_input"]
            runner = shared_runner or RecordingRunner(
                delegate=module.REAL_POPEN
            )
            try:
                results[index] = module.audit_event(
                    fixture.repo.root,
                    adapter["event_kind"],
                    adapter["payload"],
                    git_runner=runner,
                    transaction=lambda: ConcurrentTransaction(index),
                )
            except BaseException as error:
                failures[index] = f"{type(error).__name__}:{error}"

        threads = [
            threading.Thread(
                target=worker,
                args=(index,),
                name=f"production-contract-concurrent-{index}",
            )
            for index in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)
        calls = []
        for index, result in enumerate(results):
            before, after = observations_by_index[index]
            calls.append(
                {
                    "adapter_status": (
                        result["event_adapter"]["status"]
                        if result is not None
                        else None
                    ),
                    "after": len(after),
                    "attempts": (
                        result["metrics"]["git_process_attempts"]
                        if result is not None
                        else None
                    ),
                    "audit_exit": (
                        result["audit_exit"] if result is not None else None
                    ),
                    "before": len(before),
                    "created": (
                        result["metrics"]["git_processes"]
                        if result is not None
                        else None
                    ),
                    "pids_unique": (
                        len({pid for _command, pid in after}) == len(after)
                    ),
                }
            )
        return {
            "ambient_popen_identity_unchanged": (
                subprocess.Popen is ambient_popen_identity
            ),
            "calls": calls,
            "failures": failures,
            "shared_runner_calls": (
                len(shared_runner.calls)
                if shared_runner is not None
                else None
            ),
            "threads_completed": all(
                not thread.is_alive() for thread in threads
            ),
        }

    different_fixture = r19_event_workflow_fixture(
        root / "concurrent-different", transport="push"
    )
    this_module = sys.modules[__name__]
    execution_seam["same_module_concurrency"] = {
        "same-root": concurrency_probe(
            (this_module, this_module),
            (fixtures["clean"], fixtures["clean"]),
            None,
        ),
        "different-root": concurrency_probe(
            (this_module, this_module),
            (fixtures["clean"], different_fixture),
            RecordingRunner(),
        ),
    }

    def load_prototype_copy(label):
        module_name = (
            f"production_contract_copy_{label}_{uuid.uuid4().hex}"
        )
        spec = importlib.util.spec_from_file_location(module_name, HERE)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not create duplicate prototype spec")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            if sys.modules.get(module_name) is module:
                sys.modules.pop(module_name, None)
            raise
        return module_name, module

    copy_records = [load_prototype_copy(str(index)) for index in range(2)]
    shared_runner = RecordingRunner()
    try:
        duplicate_probe = concurrency_probe(
            tuple(module for _name, module in copy_records),
            (fixtures["clean"], different_fixture),
            shared_runner,
        )
        copy_private_prefixes = [
            module.__name__.replace(".", "_") + "_private_reconcile_"
            for _name, module in copy_records
        ]
        duplicate_probe["private_modules_leaked"] = sorted(
            key
            for key in sys.modules
            if any(
                key.startswith(prefix) for prefix in copy_private_prefixes
            )
        )
    finally:
        for module_name, module in copy_records:
            if sys.modules.get(module_name) is module:
                sys.modules.pop(module_name, None)
    execution_seam["duplicate_module_concurrency"] = duplicate_probe

    cache_sessions = [
        RepositorySession(
            fixture.repo.root,
            git_runner=_trusted_git_runner(),
        )
        for fixture in (fixtures["clean"], different_fixture)
    ]
    cache_module_names = []
    try:
        for session in cache_sessions:
            session.open()
            cache_module_names.append(session.reconcile.__name__)
        cache_sessions[0].reconcile._GIT_BLOB_CACHE["sentinel"] = b"one"
        cache_sessions[0].carry_proof_cache[("sentinel", "one")] = {
            "owner": "one"
        }
        cache_isolation = {
            "carry_cache_distinct": (
                cache_sessions[0].carry_proof_cache
                is not cache_sessions[1].carry_proof_cache
            ),
            "carry_cache_unshared": (
                ("sentinel", "one")
                not in cache_sessions[1].carry_proof_cache
            ),
            "reconcile_cache_distinct": (
                cache_sessions[0].reconcile._GIT_BLOB_CACHE
                is not cache_sessions[1].reconcile._GIT_BLOB_CACHE
            ),
            "reconcile_cache_unshared": (
                "sentinel"
                not in cache_sessions[1].reconcile._GIT_BLOB_CACHE
            ),
            "reconcile_modules_distinct": (
                cache_sessions[0].reconcile
                is not cache_sessions[1].reconcile
            ),
            "subprocess_facades_distinct": (
                cache_sessions[0].reconcile.subprocess
                is not cache_sessions[1].reconcile.subprocess
            ),
        }
    finally:
        for session in reversed(cache_sessions):
            session.close()
    cache_isolation["private_modules_removed"] = all(
        module_name not in sys.modules for module_name in cache_module_names
    )
    execution_seam["cache_isolation"] = cache_isolation

    ambient_reconcilers = [load_reconciler(), load_reconciler()]
    poisoned_dates = (
        datetime.date(1999, 12, 31),
        datetime.date(2099, 1, 1),
    )
    for reconcile, poisoned_date in zip(
        ambient_reconcilers, poisoned_dates, strict=True
    ):
        reconcile.TODAY = poisoned_date

    def render_retry_in_private_session(index):
        session = RepositorySession(
            fixtures["clean"].repo.root,
            git_runner=_trusted_git_runner(),
        )
        module_name = None
        session.open()
        try:
            module_name = session.reconcile.__name__
            finding = session.reconcile.Finding(
                "queue-name",
                Path("message-queue/needs-agent/requests/bad.md"),
                "bad name",
                "rename it",
            )
            path = (
                "message-queue/needs-agent/retries/blocking-"
                + session.reconcile.finding_key(finding)
                + ".md"
            )
            text = session.reconcile.retry_text(finding)
            payload = text.encode("utf-8")
            identity = list(
                session.reconcile.queue_action_identity(path, text)
            )
            filed = session.reconcile.text_fields(text)["Filed"]
            return {
                "ambient_date": poisoned_dates[index].isoformat(),
                "ambient_date_unchanged": (
                    ambient_reconcilers[index].TODAY
                    == poisoned_dates[index]
                ),
                "bytes_sha256": hashlib.sha256(payload).hexdigest(),
                "filed": filed,
                "fixed_session_date": (
                    session.reconcile.TODAY.isoformat()
                ),
                "git_blob_oid": hashlib.sha1(
                    b"blob "
                    + str(len(payload)).encode("ascii")
                    + b"\0"
                    + payload
                ).hexdigest(),
                "identity": identity,
                "path": path,
                "payload": text,
                "private_module": module_name,
            }
        finally:
            session.close()

    try:
        retry_replays = [
            render_retry_in_private_session(index) for index in range(2)
        ]
    finally:
        for reconcile in ambient_reconcilers:
            if sys.modules.get(reconcile.__name__) is reconcile:
                sys.modules.pop(reconcile.__name__, None)
    retry_module_names = [
        replay.pop("private_module") for replay in retry_replays
    ]
    comparable_retry_replays = [
        {
            key: value
            for key, value in replay.items()
            if key != "ambient_date"
        }
        for replay in retry_replays
    ]
    execution_seam["fixture_date_replay"] = {
        "fixed_date": FIXTURE_DATE.isoformat(),
        "opposite_ambient_dates": [
            value.isoformat() for value in poisoned_dates
        ],
        "private_modules_removed": all(
            module_name not in sys.modules
            for module_name in retry_module_names
        ),
        "private_modules_unique": len(set(retry_module_names)) == 2,
        "replays": retry_replays,
        "stable_bytes_oid_identity_and_filed_date": (
            comparable_retry_replays[0] == comparable_retry_replays[1]
            and retry_replays[0]["filed"].startswith(
                FIXTURE_DATE.isoformat()
            )
        ),
    }

    nested_result = None

    def nested_factory():
        nonlocal nested_result
        nested_result = audit_event(
            fixtures["clean"].repo.root,
            clean_input["event_kind"],
            clean_input["payload"],
            git_runner=_trusted_git_runner(),
        )
        return contextlib.nullcontext()

    nested_outer = audit_event(
        fixtures["clean"].repo.root,
        clean_input["event_kind"],
        clean_input["payload"],
        git_runner=_trusted_git_runner(),
        transaction=nested_factory,
    )
    execution_seam["nested_reentry"] = {
        "nested_actual": nested_result["metrics"]["git_processes"],
        "nested_attempts": nested_result["metrics"]["git_process_attempts"],
        "nested_status": nested_result["event_adapter"]["status"],
        "outer_actual": nested_outer["metrics"]["git_processes"],
        "outer_attempts": nested_outer["metrics"]["git_process_attempts"],
        "outer_status": nested_outer["event_adapter"]["status"],
    }

    source = HERE.read_text("utf-8")
    reconcile_source = RECONCILE_PATH.read_text("utf-8")
    audit_launch_sources = "\n".join(
        inspect.getsource(subject)
        for subject in (
            audit_event,
            _ordinary_audit,
            RepositorySession,
            SessionSubprocess,
            spawn_git_process,
            run_git,
            bounded_git_lines,
            ObjectDatabase,
            Graph,
            _Classifier,
        )
    )
    private_strategy_surfaces = (
        _Fixture,
        _Classifier,
        _run_classifier,
        _r18_origin_fixture,
        _r18_origin_budget_fixture,
        _scenario_builders,
        _configure_typed_budget_fixture,
        _run_fixture,
        _run_suite,
    )
    intended_public_namespace = {
        name: globals()[name] for name in _INTENDED_PUBLIC_API
    }

    def public_origin_selector(origin_strategy="U"):
        return origin_strategy

    def public_b_selector(strategy="B"):
        return strategy

    def public_fixture_runner(fixture: _Fixture):
        return fixture

    public_guard_probe = _public_strategy_exposures(
        {
            "public_b_selector": public_b_selector,
            "public_fixture_runner": public_fixture_runner,
            "public_origin_selector": public_origin_selector,
        }
    )
    execution_seam["static_contract"] = {
        "ambient_popen_assignment_absent": re.search(
            r"subprocess\.Popen\s*=", source
        )
        is None,
        "ambient_run_assignment_absent": re.search(
            r"subprocess\.run\s*=", source
        )
        is None,
        "audit_runner_has_no_default": (
            "git_runner" not in (audit_event.__kwdefaults__ or {})
        ),
        "audit_paths_have_no_real_fallback": all(
            name not in audit_launch_sources
            for name in ("REAL_" + "POPEN", "REAL_" + "RUN")
        ),
        "classifier_session_has_no_default": (
            "session" not in (_Classifier.__init__.__kwdefaults__ or {})
        ),
        "active_reconciler_has_no_default": (
            ("BASE_" + "RECONCILE") not in source
            and "ACTIVE_RECONCILE = contextvars.ContextVar("
            in source
        ),
        "bounded_git_has_no_fixture_launcher": (
            "command_prefix"
            not in inspect.signature(bounded_git_lines).parameters
            and "REAL_POPEN"
            not in inspect.getsource(bounded_git_lines)
            and "REAL_RUN" not in inspect.getsource(bounded_git_lines)
        ),
        "facade_has_no_ambient_delegate": (
            "getattr(subprocess" not in inspect.getsource(SessionSubprocess)
            and "return getattr" not in inspect.getsource(
                SessionSubprocess.__getattr__
            )
        ),
        "facade_public_surface_closed": {
            name
            for name in SessionSubprocess.__dict__
            if not name.startswith("_")
        }
        == {"DEVNULL", "PIPE", "Popen", "TimeoutExpired", "run"},
        "event_kind_exact_type_boundary": (
            "type(event_kind) is not str"
            in inspect.getsource(event_endpoints)
            and "INVALID_EVENT_KIND_EVIDENCE"
            in inspect.getsource(_typed_event_failure)
        ),
        "internal_sessions_have_no_default": all(
            inspect.signature(subject).parameters["session"].default
            is inspect.Parameter.empty
            for subject in (_Classifier, Graph, ObjectDatabase, spawn_git_process)
        ),
        "main_runner_has_no_default": (
            "git_runner" not in (main.__kwdefaults__ or {})
        ),
        "ordinary_cli_absent": (
            ("--" + "old") not in source
            and ("--" + "new") not in source
            and ("--origin-" + "strategy") not in source
        ),
        "public_ordinary_audit_absent": re.search(
            r"^def ordinary_audit\(", source, re.MULTILINE
        )
        is None,
        "intended_public_api_strategy_u_only": (
            tuple(sorted(intended_public_namespace))
            == tuple(sorted(_INTENDED_PUBLIC_API))
            and not _public_strategy_exposures(
                intended_public_namespace
            )
        ),
        "private_strategy_surface_no_public_aliases": not (
            _public_private_aliases(
                globals(), private_strategy_surfaces
            )
        ),
        "public_strategy_guard_observed_red": public_guard_probe
        == [
            "public_b_selector",
            "public_fixture_runner",
            "public_origin_selector",
        ],
        "public_strategy_selector_absent": not (
            _public_strategy_exposures(globals())
        ),
        "public_strategy_surface_u_only": (
            "origin_strategy" not in inspect.signature(audit_event).parameters
            and "origin_strategy" not in inspect.signature(main).parameters
            and "origin_strategy" not in inspect.signature(
                _ordinary_audit
            ).parameters
            and 'origin_strategy="U"' in inspect.getsource(_ordinary_audit)
        ),
        "transaction_wrapper_absent": (
            ("_ResultBlind" + "Transaction") not in source
        ),
        "repository_session_owns_metrics": (
            "metrics"
            not in inspect.signature(RepositorySession).parameters
        ),
        "repository_session_runner_has_no_default": (
            inspect.signature(RepositorySession).parameters[
                "git_runner"
            ].default
            is inspect.Parameter.empty
        ),
        "runner_result_publication_bridge": (
            "publish_call_result(" in inspect.getsource(spawn_git_process)
            and "session.processes," in inspect.getsource(spawn_git_process)
            and "session.git_runner(command" not in inspect.getsource(
                spawn_git_process
            )
        ),
        "pipe_result_publication_bridge": (
            "publish_call_result(raw_pairs, pipe_factory)"
            in inspect.getsource(prepare_explicit_parent_pipes)
            and 'publication_boundary("after-pipe-return-publication")'
            in inspect.getsource(prepare_explicit_parent_pipes)
        ),
        "spawn_metrics_derived_from_session": (
            "metrics"
            not in inspect.signature(spawn_git_process).parameters
        ),
        "reconciler_launch_sites": {
            "Popen": reconcile_source.count("subprocess.Popen("),
            "run": reconcile_source.count("subprocess.run("),
            "total": (
                reconcile_source.count("subprocess.Popen(")
                + reconcile_source.count("subprocess.run(")
            ),
        },
    }

    def is_pre_execution_rejection(item, reason_fragment):
        return (
            item["audit_exit"] == 2
            and item["adapter_status"] == "coverage-unavailable"
            and item["before"] == 0
            and item["after"] == 0
            and item["runner_calls"] == 0
            and item["runner_created"] == 0
            and item["canonical_json_serializable"]
            and item["lifecycle"]
            == {
                "factory": 0,
                "enter": 0,
                "exit": 0,
                "exit_after_reap": None,
                "exit_exception": None,
            }
            and reason_fragment in item["reason"]
        )

    def concurrency_green(probe):
        return bool(
            probe["threads_completed"]
            and probe["failures"] == [None, None]
            and probe["ambient_popen_identity_unchanged"]
            and all(
                call["adapter_status"] == "accepted"
                and call["audit_exit"] == 0
                and call["attempts"] == call["created"]
                == call["before"] == call["after"]
                and call["created"] > 0
                and call["pids_unique"]
                for call in probe["calls"]
            )
            and (
                probe["shared_runner_calls"] is None
                or probe["shared_runner_calls"]
                == sum(call["created"] for call in probe["calls"])
            )
        )

    valid = execution_seam["valid"]
    blocking = execution_seam["blocking"]
    clean_cache_state = {
        "active_reconciler_restored": True,
        "carry_cache_entries": 0,
        "object_databases_detached": True,
        "owners": 1,
        "owners_closed": True,
        "pipe_registries_empty": True,
        "process_registries_empty": True,
        "reconciler_modules_detached": True,
    }
    observed = bool(
        observations["clean"]["exit"] == 0
        and observations["clean"]["classification"] == "no-finding"
        and observations["clean"]["adapter_status"] == "accepted"
        and observations["blocking"]["exit"] == 1
        and observations["blocking"]["classification"] == "blocking-finding"
        and observations["blocking"]["adapter_status"] == "accepted"
        and observations["unavailable"]["exit"] == 2
        and observations["unavailable"]["classification"] == "unreadable"
        and observations["unavailable"]["adapter_status"]
        == "coverage-unavailable"
        and all(
            item["stdout_canonical"]
            and item["import_cli_bytes_equal"]
            and item["cli_bytes_sha256"]
            == item["import_bytes_sha256"]
            and item["typed_origin_strategy"] == "U"
            and item["typed_results_equal"]
            for item in observations.values()
        )
        and all(
            item == {
                "adapter_status": "coverage-unavailable",
                "audit_exit": 2,
                "classification": "unreadable",
                "stdout_canonical": True,
            }
            for item in typed_cli_inputs.values()
        )
        and valid["audit_exit"] == 0
        and valid["adapter_status"] == "accepted"
        and valid["attempts"] == valid["actual"] == valid["created"]
        == valid["before"] == valid["after"]
        == valid["runner_calls"] == valid["runner_created"]
        and valid["created"] > 0
        and valid["commands_match"]
        and valid["all_pids_reaped"]
        and valid["all_runner_pids_reaped"]
        and valid["fd_delta"] == 0
        and valid["cache_state"] == clean_cache_state
        and valid["observation_order"]
        == [
            "transaction-factory",
            "transaction-enter",
            "transaction-exit",
            "audit-returned",
            "metrics-read",
        ]
        and valid["lifecycle"] == {
            "factory": 1,
            "enter": 1,
            "exit": 1,
            "exit_after_reap": True,
            "exit_exception": None,
        }
        and not valid["private_modules_leaked"]
        and blocking["audit_exit"] == 1
        and blocking["classification"] == "blocking-finding"
        and blocking["adapter_status"] == "accepted"
        and blocking["attempts"] == blocking["actual"]
        == blocking["created"] == blocking["before"]
        == blocking["after"] == blocking["runner_calls"]
        == blocking["runner_created"]
        and blocking["created"] > 0
        and blocking["commands_match"]
        and blocking["all_pids_reaped"]
        and blocking["all_runner_pids_reaped"]
        and blocking["fd_delta"] == 0
        and blocking["cache_state"] == clean_cache_state
        and not blocking["private_modules_leaked"]
        and blocking["lifecycle"]
        == {
            "factory": 1,
            "enter": 1,
            "exit": 1,
            "exit_after_reap": True,
            "exit_exception": None,
        }
        and blocking["observation_order"]
        == [
            "transaction-factory",
            "transaction-enter",
            "transaction-exit",
            "audit-returned",
            "metrics-read",
        ]
        and blocking["cli_import_byte_parity"]
        == {
            "bytes_equal": True,
            "cli_sha256": observations["blocking"][
                "cli_bytes_sha256"
            ],
            "import_sha256": observations["blocking"][
                "import_bytes_sha256"
            ],
        }
        and blocking["cli_import_byte_parity"]["cli_sha256"]
        == blocking["cli_import_byte_parity"]["import_sha256"]
        and is_pre_execution_rejection(
            execution_seam["invalid"], "local.old is missing"
        )
        and all(
            is_pre_execution_rejection(item, "O and N must be distinct")
            for item in execution_seam[
                "identical_endpoint_rejections"
            ].values()
        )
        and all(
            is_pre_execution_rejection(
                item, "budget must be an exact positive integer"
            )
            for item in execution_seam[
                "invalid_budget_rejections"
            ].values()
        )
        and all(
            is_pre_execution_rejection(
                item,
                (
                    "event payload must be a mapping"
                    if label.startswith("payload")
                    else "event kind must be a string"
                ),
            )
            for label, item in execution_seam[
                "invalid_runtime_inputs"
            ].items()
        )
        and all(
            item["projected_event_kind"]
            == (
                None
                if label.startswith("event-kind")
                else "local"
            )
            for label, item in execution_seam[
                "invalid_runtime_inputs"
            ].items()
        )
        and all(
            item["audit_exit"] == 2
            and item["attempts"] == int(ordinal)
            and item["created"] == int(ordinal) - 1
            and item["before"] == int(ordinal)
            and item["after"] == int(ordinal) - 1
            and item["runner_calls"] == int(ordinal)
            and item["runner_created"] == int(ordinal) - 1
            and item["all_pids_reaped"]
            and "Git process factory failed" in item["reason"]
            for ordinal, item in execution_seam[
                "runner_ordinal_failures"
            ].items()
        )
        and all(
            item["audit_exit"] == 2
            and item["attempts"] == 1
            and item["created"] == 0
            and item["before"] == 1
            and item["after"] == 0
            and item["caught"] is None
            for item in execution_seam["runner_throwables"].values()
        )
        and execution_seam["runner_cancellation"]["caught"]
        == "KeyboardInterrupt"
        and execution_seam["runner_cancellation"]["all_pids_reaped"]
        and execution_seam["observer_throwables"]["runtime"]["audit_exit"]
        == 2
        and execution_seam["observer_throwables"]["direct-base"]["audit_exit"]
        == 2
        and execution_seam["observer_throwables"]["keyboard"]["caught"]
        == "KeyboardInterrupt"
        and all(
            item["all_pids_reaped"]
            for item in execution_seam["observer_throwables"].values()
        )
        and all(
            item["audit_exit"] == 2
            and item["caught"] is None
            and (
                (stage.startswith("factory") or stage.startswith("enter"))
                == (item["attempts"] == 0)
            )
            and item["lifecycle"]["exit"]
            == (1 if stage.startswith("exit") else 0)
            and stage.split("-")[0] in item["reason"]
            for stage, item in execution_seam[
                "transaction_throwables"
            ].items()
        )
        and all(
            item["caught"] == "KeyboardInterrupt"
            and item["all_pids_reaped"]
            and item["lifecycle"]["exit"]
            == (1 if stage == "exit" else 0)
            for stage, item in execution_seam[
                "transaction_cancellations"
            ].items()
        )
        and all(
            item["caught"] == "KeyboardInterrupt"
            and item["all_pids_reaped"]
            and item["lifecycle"]["factory"] == 1
            and item["lifecycle"]["enter"] == 1
            and item["lifecycle"]["exit"] == 1
            and item["lifecycle"]["exit_exception"]
            == "KeyboardInterrupt"
            and not item["private_modules_leaked"]
            for item in execution_seam[
                "trace_cancellation_boundaries"
            ].values()
        )
        and all(
            item["caught"] == "KeyboardInterrupt"
            and item["all_runner_pids_reaped"]
            and item["fd_delta"] == 0
            and item["lifecycle"]["factory"] == 0
            and not item["private_modules_leaked"]
            for item in execution_seam[
                "session_setup_cancellation_boundaries"
            ].values()
        )
        and all(
            item["caught"] == "KeyboardInterrupt"
            and item["all_runner_pids_reaped"]
            and item["fd_delta"] == 0
            and item["runner_created"] == 1
            and item["lifecycle"]["factory"] == 1
            and item["lifecycle"]["enter"] == 1
            and item["lifecycle"]["exit"] == 1
            and item["lifecycle"]["exit_exception"]
            == "KeyboardInterrupt"
            and not item["private_modules_leaked"]
            for item in execution_seam[
                "spawn_construction_cancellation_boundaries"
            ].values()
        )
        and execution_seam["trace_cancellation_boundaries"][
            "after-enter"
        ]["after"] == 0
        and execution_seam["trace_cancellation_boundaries"][
            "after-session-close"
        ]["after"] == valid["after"]
        and execution_seam["truthy_exit_ignored"]["audit_exit"] == 0
        and execution_seam["noncallable_runner"]["audit_exit"] == 2
        and "repository session construction failed: TypeError"
        in execution_seam["noncallable_runner"]["reason"]
        and execution_seam["hostile_ambient_subprocess"]["audit_exit"] == 0
        and execution_seam["hostile_ambient_subprocess"][
            "popen_identity_unchanged"
        ]
        and execution_seam["hostile_ambient_subprocess"]["runner_calls"]
        == execution_seam["hostile_ambient_subprocess"]["created"]
        and all(
            concurrency_green(item)
            for item in execution_seam["same_module_concurrency"].values()
        )
        and concurrency_green(
            execution_seam["duplicate_module_concurrency"]
        )
        and not execution_seam["duplicate_module_concurrency"][
            "private_modules_leaked"
        ]
        and all(execution_seam["cache_isolation"].values())
        and execution_seam["fixture_date_replay"][
            "private_modules_removed"
        ]
        and execution_seam["fixture_date_replay"][
            "stable_bytes_oid_identity_and_filed_date"
        ]
        and all(
            replay["ambient_date_unchanged"]
            and replay["fixed_session_date"] == FIXTURE_DATE.isoformat()
            for replay in execution_seam["fixture_date_replay"]["replays"]
        )
        and execution_seam["nested_reentry"]["nested_status"] == "accepted"
        and execution_seam["nested_reentry"]["outer_status"] == "accepted"
        and execution_seam["nested_reentry"]["nested_attempts"]
        == execution_seam["nested_reentry"]["nested_actual"]
        and execution_seam["nested_reentry"]["outer_attempts"]
        == execution_seam["nested_reentry"]["outer_actual"]
        and all(
            value is True
            for key, value in execution_seam["static_contract"].items()
            if key != "reconciler_launch_sites"
        )
        and execution_seam["static_contract"]["reconciler_launch_sites"]
        == {"Popen": 2, "run": 65, "total": 67}
        and subprocess.Popen is ambient_popen_identity
    )
    return {
        "control": "event-adapter-cli-entrypoint",
        "status": "OBSERVED_RED" if observed else "CONTROL_FAILED",
        "C": "0" * 40,
        "O": "0" * 40,
        "N": "0" * 40,
        "baseline_classification": "three-exit-adapter-contract",
        "damaged_classification": "ambient-or-shared-session-boundary",
        "expected_baseline": "three-exit-adapter-contract",
        "authority_edges": [],
        "propagation_edges": [],
        "event_adapter_cli_observation": {
            "cases": observations,
            "entrypoint": (
                "prototype.py --repo ROOT --event-kind KIND "
                "--event-payload EVENT.json"
            ),
            "execution_seam": execution_seam,
            "importable_api": {
                "endpoint_derivation": (
                    "event_endpoints(event_kind: str, payload: "
                    "Mapping[str, Any]) -> EventEndpoints"
                ),
                "typed_U_audit": (
                    "audit_event(root: Path, event_kind: str, payload: "
                    "Mapping[str, Any], *, git_runner: TrustedGitRunner, "
                    "budget_limit: int | None = None, transaction: "
                    "Callable[[], ContextManager[GitSpawnObserver | None]] "
                    "| None = None) -> dict"
                ),
            },
            "payload_grammar": {
                "local": ["old", "new"],
                "pre-push": ["old", "new"],
                "pull-request-synchronize": [
                    "before", "after", "pull_request.head.sha"
                ],
                "push": ["before", "after"],
            },
            "typed_cli_inputs": typed_cli_inputs,
        },
    }


def _run_control(name: str, root: Path):
    if name == "event-adapter-cli-entrypoint":
        return _event_adapter_control(root)
    if name == "leak-object-database-pipes":
        repo = GitRepository(root)
        initialize(repo)
        repo.commit("initialize descriptor lifecycle fixture")

        class CloseRaisesBeforeDelegate:
            """Keep the real fd open while making the object close fail."""

            def __init__(self, delegate, error_type=OSError):
                self.delegate = delegate
                self.error_type = error_type
                self.close_calls = 0

            def __getattr__(self, name):
                return getattr(self.delegate, name)

            def close(self):
                self.close_calls += 1
                if self.error_type is OSError:
                    raise OSError(
                        errno.EIO, "injected close-before-delegate"
                    )
                raise self.error_type("injected close-before-delegate")

        class CloseRaisesAfterDelegate(CloseRaisesBeforeDelegate):
            """Release the real fd, then inject an object-level throwable."""

            def close(self):
                self.close_calls += 1
                self.delegate.close()
                if self.error_type is OSError:
                    raise OSError(
                        errno.EIO, "injected close-after-delegate"
                    )
                raise self.error_type("injected close-after-delegate")

        class FilenoAndCloseRaiseBeforeDelegate(
            CloseRaisesBeforeDelegate
        ):
            """Prove cleanup never re-queries an adversarial wrapper fd."""

            def __init__(self, delegate, error_type=OSError):
                super().__init__(delegate, error_type)
                self.fileno_calls = 0

            def fileno(self):
                self.fileno_calls += 1
                raise self.error_type("injected fileno failure")

        class PipeBaseException(BaseException):
            pass

        def pipe_return_publication_probe(error_type):
            read_fd, write_fd = os.pipe()
            supplied = False

            def pipe_factory():
                nonlocal supplied
                if supplied:
                    raise AssertionError("pipe factory called twice")
                supplied = True
                return read_fd, write_fd

            def cancel_after_publication(stage):
                if stage != "after-pipe-return-publication":
                    raise AssertionError("unexpected pipe publication stage")
                raise error_type("injected after pipe return publication")

            caught = None
            try:
                prepare_explicit_parent_pipes(
                    ("stdin",),
                    pipe_factory=pipe_factory,
                    publication_boundary=cancel_after_publication,
                )
            except BaseException as error:
                caught = type(error).__name__
            closed = {
                "read": descriptor_is_closed(read_fd),
                "write": descriptor_is_closed(write_fd),
            }
            for descriptor in (read_fd, write_fd):
                if not descriptor_is_closed(descriptor):
                    os.close(descriptor)
            return {"caught": caught, "closed": closed}

        pipe_return_publication_observations = {
            error_type.__name__: pipe_return_publication_probe(error_type)
            for error_type in (KeyboardInterrupt, SystemExit)
        }
        pipe_return_publication_safe = all(
            item["caught"] == error_type
            and item["closed"] == {"read": True, "write": True}
            for error_type, item in (
                pipe_return_publication_observations.items()
            )
        )

        raising_modes = {
            "raising-close": ("close", OSError, "before"),
            "raising-abort": ("abort", OSError, "before"),
            "runtime-close": ("close", RuntimeError, "before"),
            "runtime-abort": ("abort", RuntimeError, "before"),
            "keyboard-close": ("close", KeyboardInterrupt, "before"),
            "system-exit-abort": ("abort", SystemExit, "before"),
            "base-close": ("close", PipeBaseException, "before"),
            "runtime-after-close": ("close", RuntimeError, "after"),
            "keyboard-after-close": (
                "close", KeyboardInterrupt, "after"
            ),
            "fileno-runtime-close": (
                "close", RuntimeError, "fileno"
            ),
            "fileno-keyboard-close": (
                "close", KeyboardInterrupt, "fileno"
            ),
            "fileno-system-exit-abort": (
                "abort", SystemExit, "fileno"
            ),
            "fileno-base-close": (
                "close", PipeBaseException, "fileno"
            ),
        }

        def observe(mode: str, damage: Damage | None = None):
            resource_session = RepositorySession(
                root,
                git_runner=_trusted_git_runner(),
            )
            metrics = resource_session.metrics
            cleanup_failures = []
            underlying_process = None
            if mode in {"stubborn-close", "stubborn-after-kill"}:
                database = ObjectDatabase.__new__(ObjectDatabase)
                database.root = root
                database.metrics = metrics
                database.session = resource_session
                database.damage = damage or Damage()
                resources = prepare_explicit_parent_pipes(
                    ("stdin", "stdout")
                )
                underlying_process = REAL_POPEN(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import os,signal,time;"
                            "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                            "os.write(1,b'R');"
                            "time.sleep(60)"
                        ),
                    ],
                    stdin=resources["stdin"]["child"].descriptor,
                    stdout=resources["stdout"]["child"].descriptor,
                    stderr=subprocess.DEVNULL,
                )
                underlying_process._agentfold_owned_pipes = (
                    attach_explicit_parent_pipes(
                        underlying_process, resources
                    )
                )
                database.process = underlying_process
                database._owned_pipes = (
                    underlying_process._agentfold_owned_pipes
                )
                database._reaped = False
                database._termination_requested = False
                database._kill_requested = False
                database.wait_timeout = 0.1
                if database.process.stdout.read(1) != b"R":
                    raise RuntimeError("stubborn child did not become ready")
                if mode == "stubborn-after-kill":
                    class UnprovableReap:
                        def __init__(self, child):
                            self.child = child
                            self.stdin = child.stdin
                            self.stdout = child.stdout

                        @property
                        def returncode(self):
                            return self.child.returncode

                        def poll(self):
                            # Simulate a platform that cannot prove the reap
                            # even after kill; the real child is reaped below.
                            return None

                        def wait(self, timeout=None):
                            raise subprocess.TimeoutExpired(
                                "cat-file-stubborn-after-kill", timeout
                            )

                        def terminate(self):
                            self.child.terminate()

                        def kill(self):
                            self.child.kill()

                    database.process = UnprovableReap(underlying_process)
            else:
                database = ObjectDatabase(resource_session, damage=damage)
            if mode == "after-exit" or mode in raising_modes:
                database.process.terminate()
                database.process.wait(timeout=5)
            if mode in raising_modes:
                wrapper = {
                    "after": CloseRaisesAfterDelegate,
                    "fileno": FilenoAndCloseRaiseBeforeDelegate,
                }.get(
                    raising_modes[mode][2],
                    CloseRaisesBeforeDelegate,
                )
                captured_view = database._owned_pipes["stdin"].object_ref
                captured_view._file_object = wrapper(
                    captured_view._file_object, raising_modes[mode][1]
                )
            owned_descriptors = {
                label: ownership.descriptor
                for label, ownership in database._owned_pipes.items()
            }
            if mode == "after-exit":
                database.close()
                database.close()
            elif mode == "abort":
                database.abort()
                database.abort()
            elif mode in raising_modes:
                operation = (
                    database.close
                    if raising_modes[mode][0] == "close"
                    else database.abort
                )
                for _index in range(2):
                    try:
                        operation()
                    except BaseException as error:
                        cleanup_failures.append(
                            f"{type(error).__name__}:{error}"
                        )
            elif mode == "close-live":
                database.close()
                database.close()
            elif mode == "stubborn-close":
                database.close()
                database.close()
            elif mode == "stubborn-after-kill":
                for operation in (database.close, database.abort):
                    try:
                        operation()
                    except Unreadable as error:
                        cleanup_failures.append(str(error))
            else:
                raise ValueError(mode)
            if underlying_process is not None:
                if underlying_process.poll() is None:
                    underlying_process.kill()
                underlying_process.wait(timeout=5)
            result = {
                "killed": (
                    mode in {"stubborn-close", "stubborn-after-kill"}
                    and underlying_process is not None
                    and underlying_process.returncode == -signal.SIGKILL
                ),
                "cleanup_failures": cleanup_failures,
                "kill_requested": database._kill_requested,
                "mode": mode,
                "process_reaps": metrics.object_process_reaps,
                "process_terminations": metrics.object_process_terminations,
                "returncode_is_set": database.process.poll() is not None,
                "stdin_closed": descriptor_is_closed(
                    owned_descriptors["stdin"]
                ),
                "stdout_closed": descriptor_is_closed(
                    owned_descriptors["stdout"]
                ),
                "stdin_object_closed": bool(
                    database.process.stdin.closed
                ),
                "stdout_object_closed": bool(
                    database.process.stdout.closed
                ),
                "owned_states": {
                    label: ownership.state
                    for label, ownership in database._owned_pipes.items()
                },
                "wrapper_fileno_calls": getattr(
                    database.process.stdin, "fileno_calls", 0
                )
                + getattr(database.process.stdin, "close_calls", 0),
            }
            # The damaged instance intentionally skips its closure path.  Close
            # the observed descriptors directly after recording the leak so the
            # control itself does not leak resources.
            for label, ownership in database._owned_pipes.items():
                with contextlib.suppress(BaseException):
                    close_owned_pipe(
                        ownership,
                        getattr(database.process, label, None),
                        os.close,
                    )
            for pipe in (database.process.stdin, database.process.stdout):
                file_object = getattr(pipe, "_file_object", pipe)
                if isinstance(file_object, CloseRaisesBeforeDelegate):
                    with contextlib.suppress(BaseException):
                        file_object.delegate.close()
                else:
                    with contextlib.suppress(
                        BrokenPipeError, OSError, ValueError
                    ):
                        pipe.close()
            return result

        baseline = {
            mode: observe(mode)
            for mode in (
                "close-live",
                "after-exit",
                "abort",
                "raising-close",
                "raising-abort",
                "runtime-close",
                "runtime-abort",
                "keyboard-close",
                "system-exit-abort",
                "base-close",
                "runtime-after-close",
                "keyboard-after-close",
                "fileno-runtime-close",
                "fileno-keyboard-close",
                "fileno-system-exit-abort",
                "fileno-base-close",
                "stubborn-close",
                "stubborn-after-kill",
            )
        }
        damaged = observe(
            "after-exit", Damage(leak_object_database_pipes=True)
        )
        baseline_closed = all(
            item["stdin_closed"]
            and item["stdout_closed"]
            and item["owned_states"]["stdout"] == "CLOSED"
            and item["owned_states"]["stdin"] == "CLOSED"
            and (
                len(item["cleanup_failures"]) == 2
                and all(
                    failure.endswith(
                        "cat-file child was not reaped after kill"
                    )
                    for failure in item["cleanup_failures"]
                )
                and item["process_reaps"] == 0
                and item["process_terminations"] == 1
                and item["kill_requested"]
                if mode == "stubborn-after-kill"
                else (
                    item["returncode_is_set"]
                    and item["process_reaps"] == 1
                    and not item["cleanup_failures"]
                    and (
                        item["killed"]
                        if mode == "stubborn-close"
                        else not item["killed"]
                    )
                    and item["stdout_object_closed"]
                    and item["stdin_object_closed"]
                    and (
                        item["wrapper_fileno_calls"] == 0
                        if mode in raising_modes
                        else True
                    )
                )
            )
            for item in baseline.values()
            for mode in (item["mode"],)
        )
        damaged_leaked = bool(
            not damaged["stdin_closed"]
            and not damaged["stdout_closed"]
            and damaged["returncode_is_set"]
            and damaged["process_reaps"] == 1
        )
        classification_fixture = ordinary_linear_fixture(
            root / "metrics-publication", "metrics-publication", valid=True
        )
        classification = _run_classifier(classification_fixture)
        metrics_published_after_close = bool(
            classification["metrics"]["object_process_reaps"] == 1
        )
        original_init = ObjectDatabase.__init__
        wrapped_classifier_descriptors = []
        wrapped_classifier_pipes = []

        def init_with_raising_close(database, *args, **kwargs):
            original_init(database, *args, **kwargs)
            wrapped_classifier_descriptors.append(
                database._owned_pipes["stdin"].descriptor
            )
            captured_view = database._owned_pipes["stdin"].object_ref
            wrapper = CloseRaisesBeforeDelegate(
                captured_view._file_object, RuntimeError
            )
            wrapped_classifier_pipes.append(wrapper)
            captured_view._file_object = wrapper

        ObjectDatabase.__init__ = init_with_raising_close
        try:
            recovered_close_result = _run_classifier(
                ordinary_linear_fixture(
                    root / "raising-close-classifier",
                    "raising-close-classifier",
                    valid=True,
                )
            )
        finally:
            ObjectDatabase.__init__ = original_init
            for wrapper in wrapped_classifier_pipes:
                with contextlib.suppress(
                    BrokenPipeError, OSError, ValueError, Unreadable
                ):
                    wrapper.delegate.close()
        immutable_backing_bypasses_mutable_view = bool(
            recovered_close_result["audit_exit"] == 0
            and recovered_close_result["classification"] == "no-finding"
            and all(
                wrapper.close_calls == 0
                for wrapper in wrapped_classifier_pipes
            )
            and wrapped_classifier_descriptors
            and all(
                descriptor_is_closed(descriptor)
                for descriptor in wrapped_classifier_descriptors
            )
        )

        original_raw_close = ObjectDatabase._raw_close_owned_fd
        unclosed_classifier_descriptors = []

        def init_with_unclosable_pipe(database, *args, **kwargs):
            init_with_raising_close(database, *args, **kwargs)
            database.wait_timeout = 0.1
            unclosed_classifier_descriptors.append(
                wrapped_classifier_descriptors[-1]
            )

        def refuse_raw_close(_database, _descriptor):
            raise OSError(errno.EIO, "injected raw close failure")

        ObjectDatabase.__init__ = init_with_unclosable_pipe
        ObjectDatabase._raw_close_owned_fd = refuse_raw_close
        try:
            unclosed_result = _run_classifier(
                ordinary_linear_fixture(
                    root / "unclosed-classifier",
                    "unclosed-classifier",
                    valid=True,
                )
            )
            unclosed_before_control_cleanup = bool(
                unclosed_classifier_descriptors
                and not descriptor_is_closed(
                    unclosed_classifier_descriptors[-1]
                )
            )
        finally:
            ObjectDatabase.__init__ = original_init
            ObjectDatabase._raw_close_owned_fd = original_raw_close
            for descriptor in unclosed_classifier_descriptors:
                if not descriptor_is_closed(descriptor):
                    os.close(descriptor)
            for wrapper in wrapped_classifier_pipes:
                with contextlib.suppress(
                    BrokenPipeError, OSError, ValueError, Unreadable
                ):
                    wrapper.delegate.close()
        unclosed_descriptor_failed_closed = bool(
            unclosed_before_control_cleanup
            and unclosed_result["audit_exit"] == 2
            and unclosed_result["classification"] == "unreadable"
            and not unclosed_result["actions"]
            and "descriptor state remains unknown"
            in unclosed_result["evidence_verdict"]["reason"]
        )

        def install_replacement(descriptor: int, sentinel: Path) -> int:
            donor = os.open(
                sentinel,
                os.O_RDWR | os.O_CREAT | os.O_TRUNC,
                0o600,
            )
            if donor != descriptor:
                os.dup2(donor, descriptor)
                os.close(donor)
            return descriptor

        class CloseAndReuseIfInvoked:
            """A public replacement that must never receive close authority."""

            def __init__(self, delegate, descriptor, sentinel, *, throws):
                self.delegate = delegate
                self.descriptor = descriptor
                self.sentinel = sentinel
                self.throws = throws
                self.calls = 0
                self.replacement = None

            def __getattr__(self, name):
                return getattr(self.delegate, name)

            def close(self):
                self.calls += 1
                os.close(self.descriptor)
                self.replacement = install_replacement(
                    self.descriptor, self.sentinel
                )
                os.write(self.replacement, b"hostile-callback")
                if self.throws:
                    raise RuntimeError("injected replacement close failure")

        def substituted_pipe_probe(label: str, *, throws: bool):
            session = RepositorySession(
                root,
                git_runner=_trusted_git_runner(),
            )
            database = ObjectDatabase(session)
            database.process.terminate()
            database.process.wait(timeout=5)
            descriptor = database._owned_pipes["stdin"].descriptor
            sentinel = root / f"substituted-{label}"
            wrapper = CloseAndReuseIfInvoked(
                database.process.stdin,
                descriptor,
                sentinel,
                throws=throws,
            )
            database.process.stdin = wrapper
            failure = None
            try:
                database.close()
            except BaseException as error:
                failure = f"{type(error).__name__}:{error}"
            replacement_descriptors = []
            try:
                for _index in range(8):
                    candidate = os.open(os.devnull, os.O_RDWR)
                    replacement_descriptors.append(candidate)
                    if candidate == descriptor:
                        break
                repeated_failures = []
                for operation in (database.close, database.abort):
                    try:
                        operation()
                    except BaseException as error:
                        repeated_failures.append(
                            f"{type(error).__name__}:{error}"
                        )
                gc.collect()
                return {
                    "cleanup_failure": failure,
                    "descriptor_reused": descriptor in replacement_descriptors,
                    "owned_state": database._owned_pipes["stdin"].state,
                    "replacement_close_calls": wrapper.calls,
                    "replacement_survived": (
                        descriptor in replacement_descriptors
                        and not descriptor_is_closed(descriptor)
                    ),
                    "repeated_failures": repeated_failures,
                    "sentinel_created": sentinel.exists(),
                }
            finally:
                for candidate in replacement_descriptors:
                    with contextlib.suppress(OSError):
                        os.close(candidate)

        substituted_pipe_observations = {
            "close-reuse-return": substituted_pipe_probe(
                "return", throws=False
            ),
            "close-reuse-throw": substituted_pipe_probe(
                "throw", throws=True
            ),
        }
        forced_fd_reuse_safe = all(
            item["cleanup_failure"] is not None
            and "cleanup ended closed" in item["cleanup_failure"]
            and item["descriptor_reused"]
            and item["owned_state"] == "CLOSED"
            and item["replacement_close_calls"] == 0
            and item["replacement_survived"]
            and not item["repeated_failures"]
            and not item["sentinel_created"]
            for item in substituted_pipe_observations.values()
        )

        def raw_token_probe(stage: str, error_type=None):
            read_fd, write_fd = os.pipe()
            os.close(write_fd)
            token = OwnedPipe(f"raw-{stage}", None, read_fd)
            sentinel = root / (
                "raw-token-"
                + stage
                + "-"
                + (error_type.__name__ if error_type else "success")
            )
            calls = 0
            replacement = None

            def raw_close(descriptor):
                nonlocal calls, replacement
                calls += 1
                if stage == "pre":
                    raise error_type("injected raw pre-delegate failure")
                os.close(descriptor)
                if stage in {"post", "success-reuse"}:
                    replacement = install_replacement(
                        descriptor, sentinel
                    )
                    os.write(replacement, b"before-repeat")
                if stage == "post":
                    raise error_type("injected raw post-delegate failure")

            caught = None
            try:
                close_raw_owned_pipe(token, raw_close)
            except BaseException as error:
                caught = type(error).__name__
            state_after_first = token.state
            descriptor_tombstoned = token.descriptor is None
            if stage == "pre":
                # The injected callback did not close the original fd.  The
                # control owns that deliberate leak, closes it externally,
                # then forces the same integer to name unrelated storage.
                os.close(read_fd)
                replacement = install_replacement(read_fd, sentinel)
                os.write(replacement, b"before-repeat")
            repeated = []
            for _index in range(2):
                try:
                    close_raw_owned_pipe(token, raw_close)
                except BaseException as error:
                    repeated.append(f"{type(error).__name__}:{error}")
            gc.collect()
            replacement_survived = None
            if replacement is not None:
                try:
                    os.write(replacement, b"-after-repeat")
                    replacement_survived = not descriptor_is_closed(
                        replacement
                    )
                finally:
                    os.close(replacement)
            return {
                "caught": caught,
                "close_calls": calls,
                "descriptor_tombstoned": descriptor_tombstoned,
                "replacement_bytes": (
                    sentinel.read_bytes() if sentinel.exists() else b""
                ).decode("ascii"),
                "replacement_survived": replacement_survived,
                "repeated_failures": repeated,
                "state": state_after_first,
            }

        raw_token_observations = {
            "success": raw_token_probe("success"),
            "success-reuse": raw_token_probe("success-reuse"),
            "pre-runtime": raw_token_probe("pre", RuntimeError),
            "post-runtime": raw_token_probe("post", RuntimeError),
            "pre-keyboard": raw_token_probe("pre", KeyboardInterrupt),
            "post-keyboard": raw_token_probe("post", KeyboardInterrupt),
            "pre-system-exit": raw_token_probe("pre", SystemExit),
            "post-system-exit": raw_token_probe("post", SystemExit),
        }
        raw_token_state_machine_safe = bool(
            raw_token_observations["success"] == {
                "caught": None,
                "close_calls": 1,
                "descriptor_tombstoned": True,
                "replacement_bytes": "",
                "replacement_survived": None,
                "repeated_failures": [],
                "state": "CLOSED",
            }
            and raw_token_observations["success-reuse"] == {
                "caught": None,
                "close_calls": 1,
                "descriptor_tombstoned": True,
                "replacement_bytes": "before-repeat-after-repeat",
                "replacement_survived": True,
                "repeated_failures": [],
                "state": "CLOSED",
            }
            and all(
                item["state"] == "UNKNOWN"
                and item["descriptor_tombstoned"]
                and item["close_calls"] == 1
                and item["replacement_survived"] is True
                and item["replacement_bytes"]
                == "before-repeat-after-repeat"
                and len(item["repeated_failures"]) == 2
                and all(
                    "descriptor state remains unknown" in failure
                    for failure in item["repeated_failures"]
                )
                for label, item in raw_token_observations.items()
                if label not in {"success", "success-reuse"}
            )
        )

        def rollback_probe(stage: str, error_type):
            read_fd, write_fd = os.pipe()
            supplied = False
            calls = []
            sentinel = root / (
                f"rollback-{stage}-{error_type.__name__}"
            )
            replacement = None

            def pipe_factory():
                nonlocal supplied
                if supplied:
                    raise AssertionError("pipe factory called twice")
                supplied = True
                return read_fd, write_fd

            def raw_close(descriptor):
                nonlocal replacement
                calls.append(descriptor)
                if descriptor == read_fd:
                    if stage == "post":
                        os.close(descriptor)
                        replacement = install_replacement(
                            descriptor, sentinel
                        )
                        os.write(replacement, b"rollback")
                    raise error_type("injected rollback close failure")
                os.close(descriptor)

            caught = None
            try:
                prepare_explicit_parent_pipes(
                    ("invalid",),
                    pipe_factory=pipe_factory,
                    raw_close=raw_close,
                )
            except BaseException as error:
                caught = type(error).__name__
            if stage == "pre":
                os.close(read_fd)
                replacement = install_replacement(read_fd, sentinel)
                os.write(replacement, b"rollback")
            gc.collect()
            os.write(replacement, b"-survived")
            replacement_survived = not descriptor_is_closed(replacement)
            os.close(replacement)
            return {
                "caught": caught,
                "close_calls": calls,
                "replacement_bytes": sentinel.read_text("ascii"),
                "replacement_survived": replacement_survived,
                "write_end_closed": descriptor_is_closed(write_fd),
            }

        rollback_observations = {
            "pre-runtime": rollback_probe("pre", RuntimeError),
            "post-runtime": rollback_probe("post", RuntimeError),
            "pre-keyboard": rollback_probe("pre", KeyboardInterrupt),
            "post-keyboard": rollback_probe("post", KeyboardInterrupt),
            "pre-system-exit": rollback_probe("pre", SystemExit),
            "post-system-exit": rollback_probe("post", SystemExit),
        }
        rollback_failure_safe = all(
            item["caught"]
            == (
                "KeyboardInterrupt"
                if label.endswith("keyboard")
                else (
                    "SystemExit"
                    if label.endswith("system-exit")
                    else "Unreadable"
                )
            )
            and len(item["close_calls"]) == 2
            and item["replacement_bytes"] == "rollback-survived"
            and item["replacement_survived"]
            and item["write_end_closed"]
            for label, item in rollback_observations.items()
        )

        cancellation_resources = prepare_explicit_parent_pipes(
            ("stdin", "stdout")
        )
        cancellation_child = REAL_POPEN(
            [
                sys.executable,
                "-c",
                (
                    "import os,signal,time;"
                    "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                    "os.write(1,b'R');time.sleep(60)"
                ),
            ],
            stdin=cancellation_resources["stdin"]["child"].descriptor,
            stdout=cancellation_resources["stdout"]["child"].descriptor,
            stderr=subprocess.DEVNULL,
        )
        cancellation_child._agentfold_owned_pipes = (
            attach_explicit_parent_pipes(
                cancellation_child, cancellation_resources
            )
        )
        if cancellation_child.stdout.read(1) != b"R":
            raise RuntimeError("cancellation child did not become ready")

        class ThrowableCleanupProcess:
            def __init__(self, child):
                self.child = child
                self.stdin = child.stdin
                self.stdout = child.stdout
                self.wait_calls = 0
                self.terminate_calls = 0
                self.kill_calls = 0

            @property
            def returncode(self):
                return self.child.returncode

            def poll(self):
                return self.child.poll()

            def wait(self, timeout=None):
                self.wait_calls += 1
                if self.wait_calls == 1:
                    raise KeyboardInterrupt(
                        "injected cancellation during wait"
                    )
                return self.child.wait(timeout=timeout)

            def terminate(self):
                self.terminate_calls += 1
                raise RuntimeError("injected terminate failure")

            def kill(self):
                self.kill_calls += 1
                return self.child.kill()

        cancellation_database = ObjectDatabase.__new__(ObjectDatabase)
        cancellation_database.root = root
        cancellation_database.session = RepositorySession(
            root,
            git_runner=_trusted_git_runner(),
        )
        cancellation_database.metrics = (
            cancellation_database.session.metrics
        )
        cancellation_database.damage = Damage()
        cancellation_database.process = ThrowableCleanupProcess(
            cancellation_child
        )
        cancellation_database._owned_pipes = (
            cancellation_child._agentfold_owned_pipes
        )
        cancellation_database._reaped = False
        cancellation_database._termination_requested = False
        cancellation_database._kill_requested = False
        cancellation_database.wait_timeout = 0.1
        cancellation_failure = None
        cancellation_notes = []
        try:
            cancellation_database.abort()
        except BaseException as error:
            cancellation_failure = type(error).__name__
            cancellation_notes = list(getattr(error, "__notes__", ()))
        cancellation_cleanup_completed = bool(
            cancellation_failure == "KeyboardInterrupt"
            and cancellation_database.process.kill_calls == 1
            and cancellation_child.poll() is not None
            and cancellation_database.metrics.object_process_reaps == 1
            and all(
                ownership.state == "CLOSED"
                for ownership in cancellation_database._owned_pipes.values()
            )
            and any(
                "RuntimeError during resource cleanup" in note
                for note in cancellation_notes
            )
        )
        original_close = ObjectDatabase.close

        def close_then_report_unproved_reap(database):
            original_close(database)
            raise Unreadable("injected unproved post-kill reap")

        ObjectDatabase.close = close_then_report_unproved_reap
        try:
            cleanup_failure_result = _run_classifier(
                ordinary_linear_fixture(
                    root / "cleanup-failure",
                    "cleanup-failure",
                    valid=True,
                )
            )
        finally:
            ObjectDatabase.close = original_close
        cleanup_failure_closed = bool(
            cleanup_failure_result["audit_exit"] == 2
            and cleanup_failure_result["classification"] == "unreadable"
            and not cleanup_failure_result["actions"]
            and cleanup_failure_result["metrics"]["object_process_reaps"] == 1
            and "object database cleanup failed" in cleanup_failure_result[
                "evidence_verdict"
            ]["reason"]
        )
        observed = (
            baseline_closed
            and damaged_leaked
            and metrics_published_after_close
            and immutable_backing_bypasses_mutable_view
            and unclosed_descriptor_failed_closed
            and forced_fd_reuse_safe
            and raw_token_state_machine_safe
            and rollback_failure_safe
            and pipe_return_publication_safe
            and cancellation_cleanup_completed
            and cleanup_failure_closed
        )
        return {
            "control": name,
            "status": "OBSERVED_RED" if observed else "CONTROL_FAILED",
            "C": "0" * 40,
            "O": "0" * 40,
            "N": "0" * 40,
            "baseline_classification": "closed-descriptors",
            "damaged_classification": "leaked-descriptors",
            "expected_baseline": "closed-descriptors",
            "authority_edges": [],
            "propagation_edges": [],
            "object_database_observation": {
                "baseline": baseline,
                "damaged": damaged,
                "metrics_published_after_close": (
                    metrics_published_after_close
                ),
                "immutable_backing_bypasses_mutable_view": (
                    immutable_backing_bypasses_mutable_view
                ),
                "unclosed_descriptor_failed_closed": (
                    unclosed_descriptor_failed_closed
                ),
                "forced_fd_reuse_safe": forced_fd_reuse_safe,
                "substituted_pipe_observations": (
                    substituted_pipe_observations
                ),
                "raw_token_observations": raw_token_observations,
                "raw_token_state_machine_safe": (
                    raw_token_state_machine_safe
                ),
                "rollback_observations": rollback_observations,
                "rollback_failure_safe": rollback_failure_safe,
                "pipe_return_publication_observations": (
                    pipe_return_publication_observations
                ),
                "pipe_return_publication_safe": (
                    pipe_return_publication_safe
                ),
                "cancellation_cleanup_completed": (
                    cancellation_cleanup_completed
                ),
                "cancellation_cleanup_notes": cancellation_notes,
                "cancellation_cleanup_state": {
                    "kill_calls": cancellation_database.process.kill_calls,
                    "process_reaps": (
                        cancellation_database.metrics.object_process_reaps
                    ),
                    "returncode_is_set": (
                        cancellation_child.poll() is not None
                    ),
                    "owned_states": {
                        label: ownership.state
                        for label, ownership in (
                            cancellation_database._owned_pipes.items()
                        )
                    },
                },
                "cleanup_failure_closed": cleanup_failure_closed,
            },
        }
    if name == "stream-malformed-truncated-final-line":
        root.mkdir(parents=True, exist_ok=True)
        observations = {}
        for variant, payload in {
            "malformed": (b"a" * 40) + b"\nnot-an-oid\n",
            "truncated": (b"a" * 40) + b"\n" + (b"b" * 39),
        }.items():
            local_rows = []

            def receive(line: bytes):
                if not re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", line):
                    raise Unreadable(f"{variant} graph line")
                local_rows.append(line.decode("ascii"))

            script = (
                "import sys;sys.stdout.buffer.write("
                + repr(payload)
                + ");sys.stdout.flush()"
            )
            reason = None

            def fixture_stream_runner(_command, *args, **kwargs):
                return REAL_POPEN(
                    [sys.executable, "-c", script], *args, **kwargs
                )

            stream_session = RepositorySession(
                root,
                git_runner=fixture_stream_runner,
            )
            metrics = stream_session.metrics
            try:
                bounded_git_lines(
                    stream_session,
                    ("fixture-bounded-output",),
                    counter_prefix="graph",
                    line_callback=receive,
                )
            except Unreadable as error:
                reason = str(error)
            finally:
                stream_session.close()
            observations[variant] = {
                "reason": reason,
                "local_rows_before_failure": len(local_rows),
                "published_rows": 0,
                "metrics": metrics.as_dict(),
            }
        observed = all(
            item["reason"] == f"{variant} graph line"
            and item["local_rows_before_failure"] == 1
            and item["published_rows"] == 0
            and item["metrics"]["graph_process_reaps"] == 1
            and item["metrics"]["graph_process_cleanup_checks"] == 1
            for variant, item in observations.items()
        )
        return {
            "control": name,
            "status": "OBSERVED_RED" if observed else "CONTROL_FAILED",
            "C": "0" * 40,
            "O": "0" * 40,
            "N": "0" * 40,
            "baseline_classification": "unreadable",
            "damaged_classification": "partial-graph",
            "expected_baseline": "unreadable",
            "authority_edges": [],
            "propagation_edges": [],
            "stream_observation": observations,
        }
    if name == "locale-git-error-stream-equality":
        fixture = r17_unreadable_boundary(root)
        stable = {}
        ambient = {}
        for locale in ("C", "fr_FR.UTF-8"):
            with temporary_environment(
                LANG=locale, LANGUAGE=locale, LC_ALL=locale, TZ="UTC"
            ):
                stable[locale] = _run_classifier(fixture)
                ambient[locale] = _run_classifier(
                    fixture, Damage(ambient_git_diagnostics=True)
                )
        stable_reasons = {
            locale: result["evidence_verdict"]["reason"]
            for locale, result in stable.items()
        }
        ambient_reasons = {
            locale: result["evidence_verdict"]["reason"]
            for locale, result in ambient.items()
        }
        baseline = stable["C"]
        damaged = ambient["fr_FR.UTF-8"]
        observed = bool(
            stable["C"] == stable["fr_FR.UTF-8"]
            and len(set(stable_reasons.values())) == 1
            and stable_reasons["C"].startswith(
                "missing-or-malformed-commit:"
            )
            and len(set(ambient_reasons.values())) == 2
        )
        return {
            "control": name,
            "status": "OBSERVED_RED" if observed else "CONTROL_FAILED",
            "C": baseline["C"],
            "O": fixture.O,
            "N": fixture.N,
            "baseline_classification": baseline["classification"],
            "damaged_classification": damaged["classification"],
            "expected_baseline": fixture.expected,
            "authority_edges": damaged["authority_edges"],
            "propagation_edges": damaged["propagation_edges"],
            "locale_observation": {
                "ambient_reasons": ambient_reasons,
                "stable_full_results_equal": (
                    stable["C"] == stable["fr_FR.UTF-8"]
                ),
                "stable_reasons": stable_reasons,
            },
        }
    fixture, damage, damaged_expected = control_builder(name, root)
    baseline = _run_classifier(fixture)
    damaged = _run_classifier(fixture, damage)
    budget_observation = None
    if name == "buffered-graph-output":
        raw_bytes = fixture.details["budget_contract"]["raw_graph_bytes"]
        budget_observation = {
            "baseline_graph_metrics": {
                key: value
                for key, value in baseline["metrics"].items()
                if key.startswith("graph_")
            },
            "damaged_graph_metrics": {
                key: value
                for key, value in damaged["metrics"].items()
                if key.startswith("graph_")
            },
            "raw_graph_bytes": raw_bytes,
        }
        observed = bool(
            baseline["audit_exit"] == 2
            and damaged["audit_exit"] == 2
            and baseline["metrics"]["graph_parent_tokens"] == 8
            and damaged["metrics"]["graph_parent_tokens"] == 8
            and baseline["metrics"]["graph_output_bytes"] < raw_bytes
            and damaged["metrics"]["graph_output_bytes"] == raw_bytes
            and baseline["metrics"]["graph_process_reaps"] == 1
            and damaged["metrics"]["graph_process_reaps"] == 1
            and not baseline["actions"]
            and not damaged["actions"]
        )
    elif name == "posthoc-budget-accounting":
        limit = fixture.details["budget_limit"]
        counter = fixture.details["budget_counter"]
        baseline_overflows = [(counter, baseline["metrics"][counter])]
        reference = fixture.details["posthoc_reference_metrics"]
        budget_observation = {
            "baseline_metrics": baseline["metrics"],
            "baseline_overflows": baseline_overflows,
            "damaged_metrics": damaged["metrics"],
            "limit": limit,
            "posthoc_reference_metrics": reference,
        }
        observed = bool(
            baseline["classification"] == fixture.expected
            and damaged["classification"] == damaged_expected
            and baseline["audit_exit"] == 2
            and damaged["audit_exit"] == 2
            and len(baseline_overflows) == 1
            and baseline_overflows[0][1] == limit + 1
            and damaged["metrics"] == reference
            and baseline["metrics"][counter] == limit + 1
            and all(
                baseline["metrics"][metric] == 0
                for metric in fixture.details["later_counters_unchanged"]
            )
            and not any(
                baseline[key]
                for key in (
                    "actions",
                    "authority_edges",
                    "carry_proofs",
                    "mutation_edges",
                    "propagation_edges",
                    "support_checks",
                )
            )
        )
    else:
        observed = bool(
            baseline["classification"] == fixture.expected
            and damaged["classification"] == damaged_expected
            and damaged["classification"] != fixture.expected
        )
    result = {
        "control": name,
        "status": "OBSERVED_RED" if observed else "CONTROL_FAILED",
        "C": baseline["C"],
        "O": fixture.O,
        "N": fixture.N,
        "baseline_classification": baseline["classification"],
        "damaged_classification": damaged["classification"],
        "expected_baseline": fixture.expected,
        "authority_edges": damaged["authority_edges"],
        "propagation_edges": damaged["propagation_edges"],
    }
    if budget_observation is not None:
        result["budget_observation"] = budget_observation
    return result


def run_control(name: str, root: Path):
    """Construct each control under a private reconciler fixture session."""
    with _fixture_repository_session(root):
        return _run_control(name, root)


def prepare_root(path: Path):
    if path.exists() and any(path.iterdir()):
        raise RuntimeError(f"fixture directory is not empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def validate_scenario_aliases(results: list[dict]):
    """Verify named adjudication scenarios without duplicating fixtures."""
    by_scenario = {result["scenario"]: result for result in results}
    inventory = []
    failures = []
    for alias, expected in SCENARIO_ALIASES.items():
        result = by_scenario.get(expected["scenario"])
        if result is None:
            observed = {"scenario": None}
            errors = [f"missing mapped scenario {expected['scenario']}"]
        else:
            observed = {
                "scenario": result["scenario"],
                "classification": result["classification"],
                "evidence_status": result["evidence_verdict"]["status"],
                "event_mode": result["event_mode"],
                "finding": any(
                    action["finding"] for action in result["actions"]
                ),
                "authority_edges": len(result["authority_edges"]),
                "invalid_authority_edges": sum(
                    edge["problem"] is not None
                    for edge in result["authority_edges"]
                ),
                "propagation_edges": len(result["propagation_edges"]),
            }
            errors = [
                f"{field}: observed {observed.get(field)!r}, "
                f"expected {value!r}"
                for field, value in expected.items()
                if observed.get(field) != value
            ]
        entry = {
            "alias": alias,
            "maps_to": expected["scenario"],
            "expected": expected,
            "observed": observed,
            "status": "PASS" if not errors else "FAIL",
        }
        if errors:
            entry["errors"] = errors
            failures.append({"alias": alias, "errors": errors})
        inventory.append(entry)
    return inventory, failures


def _run_suite(root: Path, *, reverse_construction: bool = False):
    failures = []
    results = []
    builders = list(_scenario_builders())
    if reverse_construction:
        builders.reverse()
    for index, builder in enumerate(builders, start=1):
        fixture_root = root / f"{index:02d}"
        with _fixture_repository_session(fixture_root):
            fixture = builder(fixture_root)
        result = _run_fixture(fixture)
        # Result validation uses reconciler parsing predicates but performs no
        # production audit.  Give even this fixture-only phase a fresh private
        # module rather than reopening an ambient reconciler fallback.
        with _fixture_repository_session(fixture_root):
            errors = validate_result(result)
        if errors:
            failures.append({"scenario": result["scenario"], "errors": errors})
        results.append(result)
    results.sort(key=lambda item: item["scenario"])
    for result in results:
        emit_json(result)
    by_scenario = {result["scenario"]: result for result in results}
    permutation_results = [
        by_scenario.get("R17-carry-compatible"),
        by_scenario.get("R17-carry-compatible-reversed"),
    ]
    permutation_signatures = []
    for result in permutation_results:
        if result is None:
            continue
        merge = result["details"]["merge"]
        permutation_signatures.append(
            {
                "classification": result["classification"],
                "evidence_status": result["evidence_verdict"]["status"],
                "event_mode": result["event_mode"],
                "merge_role_multiset": sorted(
                    edge["role"]
                    for proof in result["carry_proofs"]
                    for edge in proof["edges"]
                    if edge["child"] == merge
                ),
                "outside_collision_multiplicities": sorted(
                    collision["multiplicity"]
                    for proof in result["carry_proofs"]
                    for collision in proof["outside_collisions"]
                ),
                "absent_arm_count": sum(
                    len(proof["absent_c_parents"])
                    for proof in result["carry_proofs"]
                ),
            }
        )
    permutation_ok = (
        len(permutation_signatures) == 2
        and permutation_signatures[0] == permutation_signatures[1]
    )
    persisted_permutations = {}
    for variant in (
        "outside-single",
        "outside-duplicate",
        "valid-absent-arm",
        "unauthorized-absent-arm",
    ):
        signatures = []
        for suffix in ("", "-reversed"):
            result = by_scenario.get(f"R17-persisted-{variant}{suffix}")
            if result is None:
                continue
            action = result["actions"][0] if result["actions"] else None
            signatures.append(
                {
                    "classification": result["classification"],
                    "evidence_status": result["evidence_verdict"]["status"],
                    "reason_code": (
                        action["reason_code"] if action is not None else None
                    ),
                    "outside_collision_multiplicities": sorted(
                        collision["multiplicity"]
                        for proof in result["carry_proofs"]
                        for collision in proof["outside_collisions"]
                    ),
                    "absent_arm_count": sum(
                        len(proof["absent_c_parents"])
                        for proof in result["carry_proofs"]
                    ),
                }
            )
        persisted_permutations[variant] = signatures
    persisted_permutation_ok = all(
        len(signatures) == 2 and signatures[0] == signatures[1]
        for signatures in persisted_permutations.values()
    )
    permutation_ok = permutation_ok and persisted_permutation_ok
    if not permutation_ok:
        failures.append(
            {
                "scenario": "R17-parent-permutation-invariance",
                "errors": ["verdict or carry role multiset changed"],
            }
        )
    origin_permutation_signatures = []
    for scenario in (
        "R18-U-parent-order",
        "R18-U-parent-order-reversed",
    ):
        result = by_scenario.get(scenario)
        if result is None:
            continue
        action = next(
            (
                item for item in result["actions"]
                if item["origin_proofs"]
            ),
            None,
        )
        origin_permutation_signatures.append(
            {
                "birth_counts": (
                    [
                        len(proof["birth_commits"])
                        for proof in action["origin_proofs"]
                    ]
                    if action is not None
                    else []
                ),
                "birth_witness_match": (
                    action["birth_witness_match"]
                    if action is not None
                    else None
                ),
                "classification": result["classification"],
                "edge_role_multiset": sorted(
                    edge["role"]
                    for proof in (
                        action["origin_proofs"] if action is not None else []
                    )
                    for edge in proof["edges"]
                ),
                "evidence_status": result["evidence_verdict"]["status"],
                "reason_code": (
                    action["reason_code"] if action is not None else None
                ),
            }
        )
    origin_permutation_ok = (
        len(origin_permutation_signatures) == 2
        and origin_permutation_signatures[0]
        == origin_permutation_signatures[1]
    )
    if not origin_permutation_ok:
        failures.append(
            {
                "scenario": "R18-origin-parent-permutation-invariance",
                "errors": ["origin verdict or semantic roles changed"],
            }
        )
    review_merge_permutations = {}
    for case in (
        "review-compatible-merge",
        "review-compatible-source-low",
        "review-compatible-source-high",
    ):
        signatures = []
        for suffix in ("", "-reversed"):
            result = by_scenario.get(f"R18-U-{case}{suffix}")
            if result is None:
                continue
            action = next(
                (item for item in result["actions"] if item["origin_proofs"]),
                None,
            )
            landmarks = result["details"]["landmarks"]
            merge_edges = [
                edge
                for proof in (
                    action["origin_proofs"] if action is not None else []
                )
                for edge in proof["edges"]
                if edge["child"] == landmarks["merge"]
            ]
            signatures.append(
                {
                    "classification": result["classification"],
                    "compatible_carriers": sum(
                        edge["role"] == "compatible-carrier"
                        for edge in merge_edges
                    ),
                    "evidence_status": result["evidence_verdict"]["status"],
                    "invalid_edges": sum(
                        edge["problem"] is not None for edge in merge_edges
                    ),
                    "reason_code": (
                        action["reason_code"] if action is not None else None
                    ),
                    "role_multiset": sorted(
                        edge["role"] for edge in merge_edges
                    ),
                    "selected_source_is_canonical": (
                        [
                            edge["parent"]
                            for edge in merge_edges
                            if edge["role"] == "source"
                        ]
                        == [
                            min(
                                edge["parent"]
                                for edge in merge_edges
                                if edge["production_problem"] is None
                                and edge["frozen_problem"] is None
                                and edge["regression_problem"] is None
                            )
                        ]
                    ),
                }
            )
        review_merge_permutations[case] = signatures
    review_merge_permutation_ok = all(
        len(signatures) == 2 and signatures[0] == signatures[1]
        for signatures in review_merge_permutations.values()
    )
    if not review_merge_permutation_ok:
        failures.append(
            {
                "scenario": "R19-review-merge-parent-permutation-invariance",
                "errors": [
                    "review source/carrier semantics changed with parent order"
                ],
            }
        )
    emit_json(
            {
                "r17_parent_permutation": permutation_signatures,
                "r17_persisted_parent_permutations": (
                    persisted_permutations
                ),
                "r18_origin_parent_permutation": (
                    origin_permutation_signatures
                ),
                "r19_review_merge_parent_permutations": (
                    review_merge_permutations
                ),
                "status": (
                    "PASS"
                    if (
                        permutation_ok
                        and origin_permutation_ok
                        and review_merge_permutation_ok
                    )
                    else "FAIL"
                ),
            }
        )
    alias_inventory, alias_failures = validate_scenario_aliases(results)
    failures.extend(alias_failures)
    emit_json(
            {
                "scenario_alias_inventory": alias_inventory,
                "status": "PASS" if not alias_failures else "FAIL",
            }
        )
    controls = []
    control_names = list(CONTROL_NAMES)
    if reverse_construction:
        control_names.reverse()
    for index, name in enumerate(control_names, start=1):
        result = run_control(name, root / f"control-{index:02d}")
        controls.append(result)
        if result["status"] != "OBSERVED_RED":
            failures.append({"control": name, "errors": [result["status"]]})
    controls.sort(key=lambda item: item["control"])
    for result in controls:
        emit_json(result)
    summary = {
        "summary": "PASS" if not failures else "FAIL",
        "passed": len(results) - sum("scenario" in item for item in failures),
        "total": len(results),
        "controls_passed": sum(
            item["status"] == "OBSERVED_RED" for item in controls
        ),
        "controls_total": len(controls),
        "aliases_passed": sum(
            item["status"] == "PASS" for item in alias_inventory
        ),
        "aliases_total": len(alias_inventory),
        "r17_parent_permutation": "PASS" if permutation_ok else "FAIL",
        "r18_origin_parent_permutation": (
            "PASS" if origin_permutation_ok else "FAIL"
        ),
        "r19_review_merge_parent_permutation": (
            "PASS" if review_merge_permutation_ok else "FAIL"
        ),
        "python": sys.version.split()[0],
        "git": REAL_RUN(
            ["git", "--version"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip(),
        "failures": failures,
    }
    emit_json(summary)
    return 0 if not failures else 1


def _typed_event_failure(
    event_kind: Any,
    reason: str,
    metrics: Metrics,
    endpoints: EventEndpoints | None = None,
) -> dict:
    zero = "0" * 40
    O = endpoints.O if endpoints is not None else zero
    N = endpoints.N if endpoints is not None else zero
    event_adapter = (
        endpoints.evidence()
        if endpoints is not None
        else {
            "N": zero,
            "O": zero,
            "endpoint_sources": [],
            "event_kind": (
                event_kind
                if type(event_kind) is str
                else INVALID_EVENT_KIND_EVIDENCE
            ),
            "github_sha_used": False,
            "mutable_metadata_invariant": True,
            "mutable_state_reads": 0,
            "provider_api_calls": 0,
            "reason": reason,
            "status": "coverage-unavailable",
            "typed_origin_strategy": "U",
        }
    )
    return {
        "scenario": "ordinary-event-audit",
        "C": None,
        "O": O,
        "N": N,
        "input_contract": {
            "schema": "restack-provenance-input/v2",
            "authoritative_endpoints": ["O", "N"],
            "origin_strategy": "U",
        },
        "audit_exit": 2,
        "classification": "unreadable",
        "evidence_verdict": {
            "status": "unreadable",
            "reason": reason,
        },
        "event_mode": "none",
        "authority_edges": [],
        "propagation_edges": [],
        "mutation_edges": [],
        "support_checks": [],
        "carry_proofs": [],
        "actions": [],
        "metrics": metrics.as_dict(),
        "event_adapter": event_adapter,
    }


def _ordinary_audit(
    session: RepositorySession,
    O: str,
    N: str,
    budget_limit: int | None,
) -> dict:
    """Private Strategy-U classifier behind the typed event boundary."""
    fixture = _Fixture(
        "ordinary-event-audit",
        RepositoryView(session.root),
        "",
        O,
        "",
        N,
        "",
        budget_limit=budget_limit,
        origin_strategy="U",
    )
    result = _Classifier(fixture, session=session).run()
    result.pop("expected_result", None)
    result.pop("details", None)
    return result


def _transaction_boundary(_name: str) -> None:
    """Named no-op used by deterministic cancellation boundary controls."""


def audit_event(
    root: Path,
    event_kind: str,
    payload: Mapping[str, Any],
    *,
    git_runner: TrustedGitRunner,
    budget_limit: int | None = None,
    transaction: Callable[
        [], ContextManager[GitSpawnObserver | None]
    ] | None = None,
) -> dict:
    """Run typed Strategy U from exact endpoints in an immutable event.

    ``git_runner`` is mandatory launch authority; ambient ``subprocess.Popen``
    is never consulted. ``transaction`` is a result-blind accounting seam.
    Invalid input enters neither a session nor a transaction.
    """
    try:
        if not valid_budget_limit(budget_limit):
            raise EventInputError(
                "coverage-unavailable: budget must be an exact positive integer"
            )
        endpoints = event_endpoints(event_kind, payload)
    except EventInputError as error:
        return _typed_event_failure(
            event_kind, str(error), Metrics(), None
        )

    metrics = Metrics()
    try:
        session = RepositorySession(
            root,
            git_runner=git_runner,
        )
    except BaseException as error:
        if is_cancellation(error):
            raise
        return _typed_event_failure(
            event_kind,
            "repository session construction failed: "
            + type(error).__name__,
            metrics,
            endpoints,
        )
    metrics = session.metrics

    failures: list[tuple[str, BaseException]] = []
    result = None
    transaction_scope = None
    transaction_entered = False
    unexpected = None
    try:
        try:
            session.open()
        except BaseException as error:
            failures.append(("repository session setup", error))
        if not failures:
            try:
                transaction_scope = (
                    contextlib.nullcontext()
                    if transaction is None
                    else transaction()
                )
            except BaseException as error:
                failures.append(("transaction factory", error))
        if not failures:
            propagated = None
            try:
                # Use the caller's context manager directly.  A Python wrapper
                # around __enter__/__exit__ creates cancellation gaps after
                # delegate entry and before delegate exit.  Retaining primary
                # failures in our own list prevents a truthy __exit__ from
                # erasing the audit or cleanup result.
                with transaction_scope as observer:
                    transaction_entered = True
                    try:
                        _transaction_boundary("after-enter")
                        session.observer = observer
                        try:
                            result = _ordinary_audit(
                                session,
                                endpoints.O,
                                endpoints.N,
                                budget_limit,
                            )
                        except BaseException as error:
                            failures.append(("audit execution", error))
                    finally:
                        # Cleanup remains inside the accounting context.  The
                        # nested finally makes the close-to-exit handoff safe
                        # even when cancellation arrives at a line boundary.
                        try:
                            session.close()
                        except BaseException as error:
                            failures.append(
                                ("repository session cleanup", error)
                            )
                        finally:
                            _transaction_boundary("after-session-close")
                            session.observer = None
                    primary_error = failures[0][1] if failures else None
                    if primary_error is not None:
                        # Raise inside the with so the delegate receives the
                        # real primary tuple.  The retained failure remains
                        # authoritative even if the delegate returns true.
                        raise primary_error
            except BaseException as error:
                propagated = error
            if propagated is not None and not any(
                propagated is error for _stage, error in failures
            ):
                failures.append(
                    (
                        (
                            "transaction enter"
                            if not transaction_entered
                            else (
                                "transaction exit"
                                if session._closed
                                and not failures
                                else "audit execution"
                            )
                        ),
                        propagated,
                    )
                )
    except BaseException as error:
        unexpected = error
    finally:
        # Factory/enter failure has no entered context, so this is the required
        # fallback cleanup.  On an entered path close is already idempotently
        # complete before __exit__.
        if not session._closed:
            try:
                session.close()
            except BaseException as error:
                failures.append(
                    ("repository session cleanup", error)
                )
        session.observer = None
    if unexpected is not None and not any(
        unexpected is error for _stage, error in failures
    ):
        failures.append(("audit execution", unexpected))

    cancellation = next(
        (
            error
            for _stage, error in failures
            if is_cancellation(error)
        ),
        None,
    )
    if cancellation is not None:
        notes = [
            f"{stage} failed: {cleanup_failure_text(error)}"
            for stage, error in failures
            if error is not cancellation
        ]
        if notes:
            cancellation.add_note("; ".join(dict.fromkeys(notes)))
        raise cancellation
    if failures:
        reason = "; ".join(
            dict.fromkeys(
                f"{stage} failed: {type(error).__name__}"
                for stage, error in failures
            )
        )
        return _typed_event_failure(
            event_kind, reason, metrics, endpoints
        )
    if result is None:
        return _typed_event_failure(
            event_kind,
            "audit execution failed: no result",
            metrics,
            endpoints,
        )
    result["metrics"] = metrics.as_dict()
    result["event_adapter"] = endpoints.evidence()
    return result


def main(argv=None, *, git_runner: TrustedGitRunner):
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--reverse-construction", action="store_true")
    parser.add_argument("--control", choices=CONTROL_NAMES)
    parser.add_argument("--fixtures-dir", type=Path)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--event-kind")
    parser.add_argument("--event-payload", type=Path)
    parser.add_argument("--budget", type=int)
    arguments = parser.parse_args(argv)
    event_mode = any(
        value is not None
        for value in (arguments.event_kind, arguments.event_payload)
    )
    selected = (
        int(arguments.self_test)
        + int(arguments.control is not None)
        + int(event_mode)
    )
    if selected != 1:
        parser.error(
            "choose exactly one of --self-test, --control, or "
            "--repo/--event-kind/--event-payload"
        )
    if event_mode and None in (
        arguments.repo,
        arguments.event_kind,
        arguments.event_payload,
    ):
        parser.error(
            "event audit requires --repo, --event-kind, and --event-payload"
        )
    if arguments.reverse_construction and not arguments.self_test:
        parser.error("--reverse-construction requires --self-test")
    if event_mode:
        try:
            payload = json.loads(arguments.event_payload.read_text("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            result = _typed_event_failure(
                arguments.event_kind,
                "coverage-unavailable: event payload could not be read: "
                + type(error).__name__,
                Metrics(),
            )
        else:
            result = audit_event(
                arguments.repo.resolve(),
                arguments.event_kind,
                payload,
                git_runner=git_runner,
                budget_limit=arguments.budget,
            )
        emit_json(result)
        return result["audit_exit"]

    if arguments.fixtures_dir is not None:
        prepare_root(arguments.fixtures_dir)
        root_context = contextlib.nullcontext(arguments.fixtures_dir)
    else:
        root_context = tempfile.TemporaryDirectory(
            prefix="agentfold-production-contract-"
        )
    with root_context as raw_root:
        root = Path(raw_root)
        if arguments.self_test:
            return _run_suite(
                root,
                reverse_construction=arguments.reverse_construction,
            )
        result = run_control(arguments.control, root / "control")
        emit_json(result)
        return 0 if result["status"] == "OBSERVED_RED" else 1


if __name__ == "__main__":
    raise SystemExit(main(git_runner=_trusted_git_runner()))
