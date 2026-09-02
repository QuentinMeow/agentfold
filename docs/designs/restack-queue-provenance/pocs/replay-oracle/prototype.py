#!/usr/bin/env python3
"""Real-Git comparison of endpoint, arm-birth, birth-state, and scoped-delta witnesses.

This proof of concept is diagnostic. It deliberately does not authorize a queue
transition or infer intent from copyable Git data.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Sequence


SCHEMA = "agentfold-replay-oracle/v2"
GOVERNED_PREFIXES = ("queue/",)
ACTION_ROOTS = (
    "queue/needs-agent/requests/",
    "queue/needs-agent/retries/",
)
TIMING_PREFIXES = (
    "future-blocking-",
    "non-blocking-",
    "pick-up-",
    "retry-",
)
ACTION_KEY = "queue/actions/action.md"
ACTION_PATH = "queue/needs-agent/requests/non-blocking-action.md"
FUTURE_ACTION_PATH = "queue/needs-agent/requests/future-blocking-action.md"
RETRY_ACTION_PATH = "queue/needs-agent/retries/retry-pick-up-action.md"
SECOND_ACTION_PATH = "queue/needs-agent/requests/non-blocking-second.md"
ACTION = "Action: action\nBinding: bind-v1\nPayload: reconcile queue\n"
ACTION_MUTATED = "Action: action\nBinding: bind-v1\nPayload: reconcile queue safely\n"
ACTION_NO_BINDING = "Action: action\nPayload: reconcile queue\n"
OID_RE = re.compile(r"^[0-9a-f]{40,64}$")
CANDIDATES = ("E", "U", "B", "D")
MAX_COMMAND_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_GRAPH_LINE_BYTES = 64 * 1024


class GitError(RuntimeError):
    """A fixture or read-only Git operation failed."""


class Unavailable(RuntimeError):
    """The bounded classifier cannot produce complete evidence."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def stable_epoch(key: str) -> int:
    # Global construction order and the absolute fixture root are absent.
    return 978_307_200 + int(hashlib.sha256(key.encode("ascii")).hexdigest()[:7], 16)


def git_environment(*, timestamp: int | None = None) -> dict[str, str]:
    # Inherited Git routing can replace the repository's object and graph view.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        {
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
            "GIT_AUTHOR_NAME": "Replay Oracle",
            "GIT_AUTHOR_EMAIL": "replay-oracle@example.invalid",
            "GIT_COMMITTER_NAME": "Replay Oracle",
            "GIT_COMMITTER_EMAIL": "replay-oracle@example.invalid",
            "GIT_EDITOR": "true",
            "GIT_SEQUENCE_EDITOR": "true",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    if timestamp is not None:
        stamp = f"{timestamp} +0000"
        env["GIT_AUTHOR_DATE"] = stamp
        env["GIT_COMMITTER_DATE"] = stamp
    return env


class Repo:
    """Deterministic fixture writer; its metadata is never classifier authority."""

    def __init__(self, path: Path, key: str) -> None:
        self.path = path
        self.epoch = stable_epoch(key)
        self.clock = 0
        path.mkdir(parents=True)
        self.run("init", "-q", "--initial-branch=main")
        self.run("config", "user.name", "Replay Oracle")
        self.run("config", "user.email", "replay-oracle@example.invalid")
        self.run("config", "commit.gpgSign", "false")
        self.run("config", "core.autocrlf", "false")
        self.run("config", "core.hooksPath", ".git/no-hooks")
        self.run("config", "commit.cleanup", "verbatim")

    def run(
        self,
        *args: str,
        check: bool = True,
        commit: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        timestamp = None
        if commit:
            self.clock += 1
            timestamp = self.epoch + self.clock
        result = subprocess.run(
            ["git", *args],
            cwd=self.path,
            env=git_environment(timestamp=timestamp),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check and result.returncode:
            raise GitError(
                f"git {' '.join(args)} exited {result.returncode}: "
                f"{result.stderr.strip()}"
            )
        return result

    def write(self, path: str, value: str) -> None:
        target = self.path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")

    def delete(self, path: str) -> None:
        target = self.path / path
        if target.exists():
            target.unlink()

    def move(self, old: str, new: str) -> None:
        target = self.path / new
        target.parent.mkdir(parents=True, exist_ok=True)
        (self.path / old).rename(target)

    def commit(self, subject: str, *, body: str = "") -> str:
        self.run("add", "-A")
        return self.commit_staged(subject, body=body)

    def commit_staged(self, subject: str, *, body: str = "") -> str:
        args = ["commit", "-q", "-m", subject]
        if body:
            args.extend(("-m", body))
        self.run(*args, commit=True)
        return self.oid("HEAD")

    def oid(self, revision: str) -> str:
        return self.run("rev-parse", revision).stdout.strip()

    def branch(self, name: str, start: str) -> None:
        self.run("checkout", "-q", "-B", name, start)

    def cherry_pick(self, oid: str) -> str:
        self.run("cherry-pick", oid, commit=True)
        return self.oid("HEAD")

    def merge_no_commit(self, *branches: str) -> None:
        self.run("merge", "-q", "--no-ff", "--no-commit", *branches)


@dataclass(frozen=True)
class Entry:
    mode: str
    kind: str
    oid: str
    size: int | None
    digest: str | None
    bytes_hex: str | None

    def signature(self) -> dict[str, Any]:
        return {
            "blob": self.digest,
            "bytes_hex": self.bytes_hex,
            "kind": self.kind,
            "mode": self.mode,
            "object": self.oid,
            "size": self.size,
        }


@dataclass
class Budget:
    max_commits: int = 256
    max_unique_blob_bytes: int = 4 * 1024 * 1024
    commits: int = 0
    unique_blob_bytes: int = 0
    seen_blobs: set[str] = field(default_factory=set)
    seen_commits: set[str] = field(default_factory=set)

    def charge_commit(self, oid: str) -> None:
        if oid in self.seen_commits:
            return
        if len(self.seen_commits) + 1 > self.max_commits:
            raise Unavailable("commit-budget")
        self.seen_commits.add(oid)
        self.commits = len(self.seen_commits)

    def charge_blob(self, oid: str, size: int) -> None:
        if oid in self.seen_blobs:
            return
        if self.unique_blob_bytes + size > self.max_unique_blob_bytes:
            raise Unavailable("blob-budget")
        self.seen_blobs.add(oid)
        self.unique_blob_bytes += size


class Reader:
    """Bounded, read-only view of immutable Git objects."""

    def __init__(self, path: Path, budget: Budget) -> None:
        self.path = path
        self.budget = budget
        self._trees: dict[tuple[str, bool, bool], dict[str, Entry]] = {}
        self._graphs: dict[tuple[str, str], tuple[list[str], dict[str, list[str]]]] = {}

    def _popen(self, *args: str) -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            ["git", "--no-replace-objects", *args],
            cwd=self.path,
            env=git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

    @staticmethod
    def _stop(process: subprocess.Popen[bytes]) -> None:
        process.kill()
        process.wait()

    def run(
        self, *args: str, check: bool = True
    ) -> subprocess.CompletedProcess[bytes]:
        process = self._popen(*args)
        assert process.stdout is not None
        output = process.stdout.read(MAX_COMMAND_OUTPUT_BYTES + 1)
        if len(output) > MAX_COMMAND_OUTPUT_BYTES:
            self._stop(process)
            raise Unavailable("command-output-budget")
        returncode = process.wait()
        result = subprocess.CompletedProcess(args, returncode, output, b"")
        if check and returncode:
            raise Unavailable("unreadable-object")
        return result

    def require_commit(self, oid: str) -> None:
        if not OID_RE.fullmatch(oid):
            raise Unavailable("invalid-oid")
        if self.run("cat-file", "-e", f"{oid}^{{commit}}", check=False).returncode:
            raise Unavailable("unreadable-object")
        self.budget.charge_commit(oid)

    def graph(self, common: str, tip: str) -> tuple[list[str], dict[str, list[str]]]:
        key = (common, tip)
        if key in self._graphs:
            return self._graphs[key]
        process = self._popen(
            "rev-list", "--reverse", "--topo-order", "--parents", f"{common}..{tip}"
        )
        assert process.stdout is not None
        order: list[str] = []
        parents: dict[str, list[str]] = {}
        while True:
            line = process.stdout.readline(MAX_GRAPH_LINE_BYTES + 1)
            if not line:
                break
            if len(line) > MAX_GRAPH_LINE_BYTES or not line.endswith(b"\n"):
                self._stop(process)
                raise Unavailable("graph-line-budget")
            fields = line.decode("ascii").split()
            if fields:
                try:
                    for oid in fields:
                        self.budget.charge_commit(oid)
                except Unavailable:
                    self._stop(process)
                    raise
                order.append(fields[0])
                parents[fields[0]] = fields[1:]
        if process.wait():
            raise Unavailable("unreadable-object")
        self._graphs[key] = (order, parents)
        return self._graphs[key]

    def merge_base(self, old: str, new: str) -> list[str]:
        output = self.run("merge-base", "--all", old, new).stdout.decode("ascii")
        return [line for line in output.splitlines() if line]

    def object_format(self) -> str:
        return self.run("rev-parse", "--show-object-format").stdout.decode("ascii").strip()

    def is_shallow(self) -> bool:
        value = self.run("rev-parse", "--is-shallow-repository").stdout.decode("ascii").strip()
        if value not in {"true", "false"}:
            raise Unavailable("invalid-shallow-state")
        return value == "true"

    def message(self, oid: str) -> str:
        return self.run("show", "-s", "--format=%B", oid).stdout.decode("utf-8")

    def tree(
        self, oid: str, *, governed: bool, normalize: bool
    ) -> dict[str, Entry]:
        self.budget.charge_commit(oid)
        key = (oid, governed, normalize)
        if key in self._trees:
            return self._trees[key]
        args = ["ls-tree", "-rz", "--full-tree", oid]
        if governed:
            args.extend(("--", *GOVERNED_PREFIXES))
        raw = self.run(*args).stdout
        result: dict[str, Entry] = {}
        for record in raw.split(b"\0"):
            if not record:
                continue
            header, raw_path = record.split(b"\t", 1)
            mode, kind, object_oid = header.decode("ascii").split()
            path = raw_path.decode("utf-8")
            blob: bytes | None = None
            if kind == "blob":
                size_raw = self.run("cat-file", "-s", object_oid).stdout
                try:
                    size = int(size_raw)
                except ValueError as exc:
                    raise Unavailable("invalid-blob-size") from exc
                self.budget.charge_blob(object_oid, size)
                process = self._popen("cat-file", "blob", object_oid)
                assert process.stdout is not None
                blob = process.stdout.read(size + 1)
                if len(blob) != size:
                    self._stop(process)
                    raise Unavailable("blob-size-mismatch")
                if process.wait():
                    raise Unavailable("unreadable-object")
            else:
                size = None
            normalized = normalize_governed_path(path) if normalize else path
            if normalized in result:
                raise Unavailable("normalized-path-collision")
            result[normalized] = Entry(
                mode=mode,
                kind=kind,
                oid=object_oid,
                size=size,
                digest=None if blob is None else sha256(blob),
                bytes_hex=None if blob is None else blob.hex(),
            )
        self._trees[key] = result
        return result


def normalize_basename(name: str) -> str:
    changed = True
    while changed:
        changed = False
        for prefix in TIMING_PREFIXES:
            if name.startswith(prefix):
                name = name[len(prefix) :]
                changed = True
                break
    return name


def normalize_governed_path(path: str) -> str:
    for root in ACTION_ROOTS:
        if path.startswith(root):
            remainder = path[len(root) :]
            if "/" not in remainder:
                return "queue/actions/" + normalize_basename(remainder)
    return path


def action_entries(reader: Reader, oid: str) -> list[Entry]:
    try:
        tree = reader.tree(oid, governed=True, normalize=True)
    except Unavailable as exc:
        if str(exc) != "normalized-path-collision":
            raise
        raw = reader.tree(oid, governed=True, normalize=False)
        return [
            entry
            for path, entry in raw.items()
            if normalize_governed_path(path) == ACTION_KEY
        ]
    entry = tree.get(ACTION_KEY)
    return [] if entry is None else [entry]


def entry_state(entries: Sequence[Entry]) -> dict[str, Any]:
    return {
        "count": len(entries),
        "entries": [
            entry.signature() for entry in sorted(entries, key=lambda item: item.oid)
        ],
    }


def delta(
    reader: Reader,
    parent: str,
    child: str,
    *,
    governed: bool,
    normalize: bool,
) -> list[dict[str, Any]]:
    before = reader.tree(parent, governed=governed, normalize=normalize)
    after = reader.tree(child, governed=governed, normalize=normalize)
    records: list[dict[str, Any]] = []
    for path in sorted(set(before) | set(after), key=lambda item: item.encode("utf-8")):
        left = before.get(path)
        right = after.get(path)
        if left == right:
            continue
        records.append(
            {
                "after": None if right is None else right.signature(),
                "before": None if left is None else left.signature(),
                "path": path,
            }
        )
    return records


@dataclass
class Arm:
    result: str
    reason: str
    commits: int
    births: list[str]
    birth_state: dict[str, Any] | None
    birth_delta: list[list[dict[str, Any]]] | None
    full_birth_delta: list[list[dict[str, Any]]] | None
    endpoint: dict[str, Any]
    interruptions: int
    multiplicity_commits: int
    birth_parent_count: int


def inspect_arm(reader: Reader, common: str, tip: str) -> Arm:
    order, parents_by_commit = reader.graph(common, tip)
    all_oids = {common, *order}
    for commit in order:
        all_oids.update(parents_by_commit[commit])
    states = {oid: action_entries(reader, oid) for oid in sorted(all_oids)}
    origins: dict[str, set[str]] = {common: set()}
    seen: dict[str, set[str]] = {common: set()}
    outside = all_oids - set(order) - {common}
    outside_live_origins = 0
    for oid in outside:
        if len(states[oid]) == 1:
            outside_live_origins += 1
            token = "outside:" + oid
            origins[oid] = {token}
            seen[oid] = {token}
        else:
            origins[oid] = set()
            seen[oid] = set()
    births: list[str] = []
    deleted_origins: set[str] = set()
    interrupted_origins: set[str] = set()
    multiplicity = sum(len(states[oid]) > 1 for oid in outside)

    for commit in order:
        parents = parents_by_commit[commit]
        for parent in parents:
            origins.setdefault(parent, set())
            seen.setdefault(parent, set())
        current = states[commit]
        if len(current) > 1:
            multiplicity += 1
        parent_live = [parent for parent in parents if len(states[parent]) == 1]
        parent_origins = set().union(*(origins[parent] for parent in parent_live))
        parent_seen = set().union(*(seen[parent] for parent in parents))
        if len(current) == 1:
            if not parent_live:
                births.append(commit)
                origins[commit] = {commit}
            else:
                origins[commit] = set(parent_origins)
                for parent in parents:
                    if len(states[parent]) == 0:
                        interrupted_origins.update(seen[parent] & parent_origins)
            seen[commit] = parent_seen | origins[commit]
        else:
            origins[commit] = set()
            if not current:
                deleted_origins.update(parent_origins)
            seen[commit] = parent_seen

    endpoint_entries = states[tip]
    endpoint = entry_state(endpoint_entries)
    tip_origins = origins.get(tip, set())
    relevant_interruptions = (deleted_origins | interrupted_origins) & tip_origins
    reason = "one-unique-continuous-birth"
    result = "match"
    if len(endpoint_entries) != 1:
        result, reason = "block", "tip-occurrence-count"
    elif multiplicity:
        result, reason = "block", "arm-multiplicity"
    elif outside_live_origins:
        result, reason = "block", "outside-C-live-origin"
    elif len(births) != 1:
        result, reason = "block", "arm-birth-count"
    elif tip_origins != {births[0]}:
        result, reason = "block", "ambiguous-live-origin"
    elif relevant_interruptions:
        result, reason = "block", "inherited-origin-interrupted"

    birth_state: dict[str, Any] | None = None
    birth_delta: list[list[dict[str, Any]]] | None = None
    full_birth_delta: list[list[dict[str, Any]]] | None = None
    parent_count = 0
    if len(births) == 1:
        birth = births[0]
        parents = parents_by_commit[birth]
        parent_count = len(parents)
        birth_entries = states[birth]
        if len(birth_entries) == 1:
            birth_state = birth_entries[0].signature()
        try:
            birth_delta = sorted(
                [
                    delta(reader, parent, birth, governed=True, normalize=True)
                    for parent in parents
                ],
                key=canonical_bytes,
            )
            full_birth_delta = sorted(
                [
                    delta(reader, parent, birth, governed=False, normalize=False)
                    for parent in parents
                ],
                key=canonical_bytes,
            )
        except Unavailable as exc:
            if str(exc) != "normalized-path-collision":
                raise
            result, reason = "block", "normalized-path-collision"
            birth_delta = None
            full_birth_delta = None

    return Arm(
        result=result,
        reason=reason,
        commits=len(order),
        births=births,
        birth_state=birth_state,
        birth_delta=birth_delta,
        full_birth_delta=full_birth_delta,
        endpoint=endpoint,
        interruptions=len(relevant_interruptions),
        multiplicity_commits=multiplicity,
        birth_parent_count=parent_count,
    )


@dataclass
class Fixture:
    scenario: str
    repo: Path
    common: str
    old: str
    new: str
    expected: dict[str, str]
    premise: str
    lesson: str
    max_commits: int = 256
    intent_twin: str | None = None


def candidate(result: str, reason: str) -> dict[str, str]:
    return {"reason": reason, "result": result}


def finish_record(
    fixture: Fixture,
    observation: dict[str, Any],
    candidates: dict[str, dict[str, str]],
    cost: dict[str, Any],
    authority: str,
) -> dict[str, Any]:
    return {
        "authority": authority,
        "candidates": candidates,
        "check": "unchecked",
        "cost": cost,
        "expected": fixture.expected,
        "input": {
            "C": fixture.common,
            "N": fixture.new,
            "O": fixture.old,
            "action_key": ACTION_KEY,
            "governed_prefixes": list(GOVERNED_PREFIXES),
        },
        "lesson": fixture.lesson,
        "observation_digest": sha256(canonical_bytes(observation)),
        "off_object_intent_premise": fixture.premise,
        "scenario": fixture.scenario,
        "schema": SCHEMA,
        "twin": fixture.intent_twin,
    }


def unavailable_record(fixture: Fixture, reason: str) -> dict[str, Any]:
    candidates = {name: candidate("unavailable", reason) for name in CANDIDATES}
    observation = {
        "candidates": candidates,
        "input": {
            "C": fixture.common,
            "N": fixture.new,
            "O": fixture.old,
            "action_key": ACTION_KEY,
            "governed_prefixes": list(GOVERNED_PREFIXES),
        },
        "state": "unavailable",
    }
    return finish_record(fixture, observation, candidates, {}, "diagnostic-only")


def classify(fixture: Fixture, damage: str | None = None) -> dict[str, Any]:
    budget = Budget(max_commits=fixture.max_commits)
    reader = Reader(fixture.repo, budget)
    try:
        for oid in (fixture.common, fixture.old, fixture.new):
            reader.require_commit(oid)
        if reader.is_shallow():
            raise Unavailable("shallow-repository")
        merge_bases = reader.merge_base(fixture.old, fixture.new)
        if merge_bases != [fixture.common]:
            raise Unavailable("non-unique-or-wrong-merge-base")
        old_order, _ = reader.graph(fixture.common, fixture.old)
        new_order, _ = reader.graph(fixture.common, fixture.new)
        if action_entries(reader, fixture.common):
            raise Unavailable("action-present-at-common")
        old = inspect_arm(reader, fixture.common, fixture.old)
        new = inspect_arm(reader, fixture.common, fixture.new)
    except Unavailable as exc:
        return unavailable_record(fixture, str(exc))

    endpoints_match = (
        old.endpoint["count"] == 1
        and new.endpoint["count"] == 1
        and old.endpoint == new.endpoint
    )
    e_result = "match" if endpoints_match else "block"
    u_result = "match" if old.result == new.result == "match" else "block"
    b_result = (
        "match"
        if u_result == "match"
        and old.birth_state is not None
        and old.birth_state == new.birth_state
        else "block"
    )
    d_result = (
        "match"
        if b_result == "match"
        and old.birth_delta is not None
        and old.birth_delta == new.birth_delta
        else "block"
    )
    authority = "diagnostic-only"
    if damage == "endpoint-only":
        u_result = b_result = d_result = e_result
    elif damage == "ignore-arm-history":
        u_result = (
            "match" if old.endpoint["count"] == new.endpoint["count"] == 1 else "block"
        )
        b_result = (
            "match" if u_result == "match" and old.endpoint == new.endpoint else "block"
        )
        d_result = b_result
    elif damage == "full-commit-patch":
        d_result = (
            "match"
            if b_result == "match"
            and old.full_birth_delta is not None
            and old.full_birth_delta == new.full_birth_delta
            else "block"
        )
    elif damage == "trust-metadata":
        messages = "\n".join(reader.message(oid) for oid in old.births + new.births)
        if "Replay-Approved: true" in messages:
            authority = "unsafe-suppression"

    candidates = {
        "E": candidate(
            e_result,
            "equal-canonical-tip-state" if endpoints_match else "tip-state-differs",
        ),
        "U": candidate(u_result, f"old:{old.reason};new:{new.reason}"),
        "B": candidate(
            b_result,
            "equal-canonical-birth-state"
            if b_result == "match"
            else "birth-state-not-proven-equal",
        ),
        "D": candidate(
            d_result,
            "equal-normalized-governed-birth-delta"
            if d_result == "match"
            else "governed-birth-delta-not-proven-equal",
        ),
    }
    observation = {
        "arms": {
            "new": {
                "birth_delta": new.birth_delta,
                "birth_parent_count": new.birth_parent_count,
                "birth_state": new.birth_state,
                "births": new.births,
                "commits": new.commits,
                "endpoint": new.endpoint,
                "interruptions": new.interruptions,
                "multiplicity_commits": new.multiplicity_commits,
            },
            "old": {
                "birth_delta": old.birth_delta,
                "birth_parent_count": old.birth_parent_count,
                "birth_state": old.birth_state,
                "births": old.births,
                "commits": old.commits,
                "endpoint": old.endpoint,
                "interruptions": old.interruptions,
                "multiplicity_commits": old.multiplicity_commits,
            },
        },
        "candidates": candidates,
        "input": {
            "C": fixture.common,
            "N": fixture.new,
            "O": fixture.old,
            "action_key": ACTION_KEY,
            "governed_prefixes": list(GOVERNED_PREFIXES),
            "normalization": {
                "action_roots": list(ACTION_ROOTS),
                "timing_prefixes": list(TIMING_PREFIXES),
            },
            "object_format": reader.object_format(),
        },
        "state": "complete",
    }
    return finish_record(
        fixture,
        observation,
        candidates,
        {
            "commit_objects": budget.commits,
            "unique_blob_bytes": budget.unique_blob_bytes,
            "unique_blobs": len(budget.seen_blobs),
        },
        authority,
    )


def common(repo: Repo) -> str:
    repo.write("app/base.txt", "common\n")
    return repo.commit("common")


def branch_birth(
    repo: Repo,
    branch: str,
    start: str,
    *,
    path: str = ACTION_PATH,
    content: str = ACTION,
    subject: str = "birth action",
    body: str = "",
    extra: dict[str, str] | None = None,
) -> str:
    repo.branch(branch, start)
    repo.write(path, content)
    for extra_path, value in (extra or {}).items():
        repo.write(extra_path, value)
    return repo.commit(subject, body=body)


PASS = {name: "match" for name in CANDIDATES}
BLOCK = {name: "block" for name in CANDIDATES}
UNAVAILABLE = {name: "unavailable" for name in CANDIDATES}


def make_repo(root: Path, key: str) -> tuple[Repo, str]:
    repo = Repo(root / key, key)
    return repo, common(repo)


def build_normal(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "01-normal-restack")
    old_birth = branch_birth(repo, "old", c)
    repo.write("app/feature.txt", "old feature\n")
    o = repo.commit("feature")
    repo.branch("new", c)
    repo.write("app/base.txt", "new base\n")
    repo.commit("advance base")
    repo.cherry_pick(old_birth)
    repo.write("app/feature.txt", "old feature\n")
    n = repo.commit("feature adjusted")
    return [
        Fixture(
            "normal-restack",
            repo.path,
            c,
            o,
            n,
            PASS,
            "replay",
            "D sees the same scoped birth while ignoring base work",
        )
    ]


def build_o_only_loss(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "02-o-only-loss")
    o = branch_birth(repo, "old", c)
    repo.branch("new", c)
    repo.write("app/new.txt", "candidate\n")
    n = repo.commit("candidate omits action")
    return [
        Fixture(
            "O-only-loss",
            repo.path,
            c,
            o,
            n,
            BLOCK,
            "loss",
            "the damage baseline catches endpoint loss",
        )
    ]


def build_delete_recreate(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "block", "B": "block", "D": "block"}
    repo, c = make_repo(root, "03-delete-recreate")
    o = branch_birth(repo, "old", c)
    branch_birth(repo, "new", c)
    repo.delete(ACTION_PATH)
    repo.commit("delete action")
    repo.write(ACTION_PATH, ACTION)
    n = repo.commit("recreate identical action")
    return [
        Fixture(
            "delete-recreate",
            repo.path,
            c,
            o,
            n,
            expected,
            "not-continuous",
            "U blocks two arm-local births",
        )
    ]


def build_transient_mutation(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "match", "B": "block", "D": "block"}
    repo, c = make_repo(root, "04-transient-mutation")
    o = branch_birth(repo, "old", c)
    branch_birth(repo, "new", c, content=ACTION_MUTATED)
    repo.write(ACTION_PATH, ACTION)
    n = repo.commit("restore action bytes")
    return [
        Fixture(
            "transient-mutation-restored",
            repo.path,
            c,
            o,
            n,
            expected,
            "different-birth-restored",
            "B catches unequal birth state after U proves only continuous presence",
        )
    ]


def build_binding_restore(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "05-binding-restore")
    o = branch_birth(repo, "old", c)
    branch_birth(repo, "new", c)
    repo.write(ACTION_PATH, ACTION_NO_BINDING)
    repo.commit("remove binding")
    repo.write(ACTION_PATH, ACTION)
    n = repo.commit("restore binding")
    return [
        Fixture(
            "binding-removal-restoration",
            repo.path,
            c,
            o,
            n,
            PASS,
            "binding-was-removed",
            "none of E/U/B/D validates queue semantics",
        )
    ]


def build_multiplicity(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "06-multiplicity")
    extra = {FUTURE_ACTION_PATH: ACTION}
    o = branch_birth(repo, "old", c, extra=extra)
    n = branch_birth(repo, "new", c, extra=extra)
    return [
        Fixture(
            "collisions-multiplicity",
            repo.path,
            c,
            o,
            n,
            BLOCK,
            "ambiguous",
            "all candidates block a non-unique endpoint",
        )
    ]


def build_neutral_merge(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "07-neutral-merge")
    old_birth = branch_birth(repo, "old-carry", c)
    repo.branch("old-neutral", c)
    repo.write("app/old-neutral.txt", "neutral\n")
    repo.commit("old neutral")
    repo.branch("old", old_birth)
    repo.merge_no_commit("old-neutral")
    o = repo.commit("merge old neutral")
    new_birth = branch_birth(repo, "new-carry", c)
    repo.branch("new-neutral", c)
    repo.write("app/new-neutral.txt", "neutral\n")
    repo.commit("new neutral")
    repo.branch("new", new_birth)
    repo.merge_no_commit("new-neutral")
    n = repo.commit("merge new neutral")
    return [
        Fixture(
            "neutral-merge-arms",
            repo.path,
            c,
            o,
            n,
            PASS,
            "continuous",
            "U ignores a never-carrying merge parent",
        )
    ]


def build_inherited_deleted(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "block", "B": "block", "D": "block"}
    repo, c = make_repo(root, "08-inherited-deleted")
    o = branch_birth(repo, "old", c)
    new_birth = branch_birth(repo, "new-birth", c)
    repo.branch("deleted-side", new_birth)
    repo.delete(ACTION_PATH)
    repo.write("app/deleted-side.txt", "deleted\n")
    repo.commit("delete inherited action")
    repo.branch("new", new_birth)
    repo.write("app/carry-side.txt", "carry\n")
    repo.commit("carry action")
    repo.merge_no_commit("deleted-side")
    repo.write(ACTION_PATH, ACTION)
    n = repo.commit("merge and retain carrying side")
    return [
        Fixture(
            "inherited-then-deleted-arm",
            repo.path,
            c,
            o,
            n,
            expected,
            "interrupted",
            "U rejects deletion on a branch that inherited the live origin",
        )
    ]


def build_exact_cherry_pick(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "09-exact-cherry-pick")
    o = branch_birth(repo, "old", c, subject="portable action patch")
    repo.branch("new", c)
    repo.write("app/base.txt", "changed base\n")
    repo.commit("advance base")
    n = repo.cherry_pick(o)
    return [
        Fixture(
            "exact-cherry-pick",
            repo.path,
            c,
            o,
            n,
            PASS,
            "exact-patch-replay",
            "D matches the scoped creation delta",
        )
    ]


def build_squash(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "match", "B": "match", "D": "block"}
    repo, c = make_repo(root, "10-squash")
    branch_birth(repo, "old", c)
    repo.write("queue/support.txt", "support\n")
    o = repo.commit("support follows")
    n = branch_birth(
        repo,
        "new",
        c,
        extra={"queue/support.txt": "support\n"},
        subject="squash action and support",
    )
    return [
        Fixture(
            "squash",
            repo.path,
            c,
            o,
            n,
            expected,
            "equivalent-restack",
            "D false-blocks changed commit grouping",
        )
    ]


def build_path_move(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "11-path-move")
    branch_birth(repo, "old", c)
    repo.move(
        ACTION_PATH,
        "queue/needs-agent/requests/non-blocking-moved-action.md",
    )
    o = repo.commit("move action to arbitrary basename")
    n = branch_birth(
        repo,
        "new",
        c,
        path="queue/needs-agent/requests/non-blocking-moved-action.md",
    )
    return [
        Fixture(
            "rename-arbitrary-path-move",
            repo.path,
            c,
            o,
            n,
            BLOCK,
            "semantic-move",
            "all candidates conservatively block an untrusted identity mapping",
        )
    ]


def build_retries(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "12-retries")
    branch_birth(repo, "old", c, path=FUTURE_ACTION_PATH)
    repo.move(FUTURE_ACTION_PATH, RETRY_ACTION_PATH)
    o = repo.commit("move request to retry pickup")
    n = branch_birth(repo, "new", c, path=ACTION_PATH)
    return [
        Fixture(
            "retries-pickups",
            repo.path,
            c,
            o,
            n,
            PASS,
            "normalized-move",
            "the closed alias set preserves X",
        )
    ]


def make_merge_birth(
    repo: Repo, c: str, prefix: str, parent_count: int, reverse: bool = False
) -> str:
    branches: list[str] = []
    for index in range(parent_count):
        name = f"{prefix}-p{index}"
        repo.branch(name, c)
        repo.write(f"app/{prefix}-{index}.txt", f"{index}\n")
        repo.commit(f"{prefix} parent {index}")
        branches.append(name)
    if reverse:
        branches.reverse()
    repo.branch(prefix, branches[0])
    repo.merge_no_commit(*branches[1:])
    repo.write(ACTION_PATH, ACTION)
    return repo.commit(f"{prefix} merge birth")


def build_parent_order(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "13-parent-order")
    o = make_merge_birth(repo, c, "old", 2, reverse=False)
    n = make_merge_birth(repo, c, "new", 2, reverse=True)
    return [
        Fixture(
            "parent-order-invariance",
            repo.path,
            c,
            o,
            n,
            PASS,
            "equivalent-merge-birth",
            "parent delta ordering is canonical",
        )
    ]


def build_unreadable(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "14-unreadable-source")
    o = branch_birth(repo, "old", c)
    n = branch_birth(repo, "new", c)
    view = root / "14-unreadable-view"
    result = subprocess.run(
        [
            "git",
            "clone",
            "-q",
            "--no-local",
            "--depth=1",
            "--branch",
            "new",
            repo.path.resolve().as_uri(),
            str(view),
        ],
        env=git_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise GitError("could not construct shallow unreadable-history view")
    return [
        Fixture(
            "unreadable-history",
            view,
            c,
            o,
            n,
            UNAVAILABLE,
            "unknown",
            "the classifier returns unavailable",
        )
    ]


def build_resource(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "15-resource-refusal")
    o = branch_birth(repo, "old", c)
    for index in range(4):
        repo.write(f"app/old-{index}.txt", f"{index}\n")
        o = repo.commit(f"old {index}")
    n = branch_birth(repo, "new", c)
    for index in range(4):
        repo.write(f"app/new-{index}.txt", f"{index}\n")
        n = repo.commit(f"new {index}")
    return [
        Fixture(
            "resource-refusal",
            repo.path,
            c,
            o,
            n,
            UNAVAILABLE,
            "unknown",
            "the exact max_commits=3 bound refuses",
            max_commits=3,
        )
    ]


def build_outside_unrelated(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "16-outside-unrelated")
    o = branch_birth(repo, "old", c)
    n = branch_birth(
        repo, "new", c, extra={"app/unrelated.txt": "unrelated\n"}
    )
    return [
        Fixture(
            "unrelated-outside-same-commit",
            repo.path,
            c,
            o,
            n,
            PASS,
            "equivalent-restack",
            "D avoids full-commit false blocking",
        )
    ]


def build_governed_unrelated(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "match", "B": "match", "D": "block"}
    repo, c = make_repo(root, "17-governed-unrelated")
    o = branch_birth(repo, "old", c)
    n = branch_birth(
        repo, "new", c, extra={"queue/unrelated.txt": "unrelated\n"}
    )
    return [
        Fixture(
            "unrelated-governed-same-commit",
            repo.path,
            c,
            o,
            n,
            expected,
            "equivalent-restack",
            "D false-blocks unrelated governed work",
        )
    ]


def build_timing_move(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "18-timing-move")
    branch_birth(repo, "old", c, path=FUTURE_ACTION_PATH)
    repo.move(FUTURE_ACTION_PATH, ACTION_PATH)
    o = repo.commit("change timing prefix")
    n = branch_birth(repo, "new", c, path=ACTION_PATH)
    return [
        Fixture(
            "timing-prefix-move",
            repo.path,
            c,
            o,
            n,
            PASS,
            "normalized-move",
            "normalization prevents a known path-only false block",
        )
    ]


def build_merge_vs_linear(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "match", "B": "match", "D": "block"}
    repo, c = make_repo(root, "19-merge-vs-linear")
    o = branch_birth(repo, "old", c)
    n = make_merge_birth(repo, c, "new", 2)
    return [
        Fixture(
            "merge-birth-vs-linear",
            repo.path,
            c,
            o,
            n,
            expected,
            "equivalent-restack",
            "D false-blocks changed birth shape",
        )
    ]


def build_parent_shape(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "match", "B": "match", "D": "block"}
    repo, c = make_repo(root, "20-parent-shape")
    o = make_merge_birth(repo, c, "old", 2)
    n = make_merge_birth(repo, c, "new", 3)
    return [
        Fixture(
            "changed-parent-shape",
            repo.path,
            c,
            o,
            n,
            expected,
            "equivalent-restack",
            "D adds structural coupling without intent evidence",
        )
    ]


def build_independent(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "21-independent-bytes")
    o = branch_birth(repo, "old", c, subject="create old action")
    n = branch_birth(repo, "new", c, subject="create new action")
    return [
        Fixture(
            "equivalent-bytes-independent",
            repo.path,
            c,
            o,
            n,
            PASS,
            "independent",
            "E/U/B/D all match without proving replay",
        )
    ]


def build_forged_metadata(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "22-forged-metadata")
    body = "Replay-Approved: true\nOrigin: claimed-restack"
    o = branch_birth(repo, "old", c, subject="claimed replay", body=body)
    n = branch_birth(repo, "new", c, subject="claimed replay", body=body)
    return [
        Fixture(
            "forged-copyable-metadata",
            repo.path,
            c,
            o,
            n,
            PASS,
            "forged",
            "the sound candidates ignore copied metadata",
        )
    ]


def build_extra_identity(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "match", "B": "match", "D": "block"}
    repo, c = make_repo(root, "23-extra-identity")
    o = branch_birth(repo, "old", c)
    n = branch_birth(
        repo, "new", c, extra={SECOND_ACTION_PATH: "Action: second\n"}
    )
    return [
        Fixture(
            "extra-queue-identity",
            repo.path,
            c,
            o,
            n,
            expected,
            "equivalent-X",
            "D cannot tell context from provenance",
        )
    ]


def build_support(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "match", "B": "match", "D": "block"}
    repo, c = make_repo(root, "24-support-artifact")
    o = branch_birth(
        repo, "old", c, extra={"queue/evidence/action.txt": "proof A\n"}
    )
    n = branch_birth(
        repo, "new", c, extra={"queue/evidence/action.txt": "proof B\n"}
    )
    return [
        Fixture(
            "support-artifacts",
            repo.path,
            c,
            o,
            n,
            expected,
            "equivalent-X",
            "D false-blocks changed support bytes",
        )
    ]


def build_cross_c_origin(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "block", "B": "block", "D": "block"}
    repo = Repo(root / "25-cross-c-origin", "25-cross-c-origin")
    repo.write("app/base.txt", "before common\n")
    repo.write(ACTION_PATH, ACTION)
    before_c = repo.commit("pre-C action")
    repo.branch("common", before_c)
    repo.delete(ACTION_PATH)
    repo.write("app/base.txt", "common without action\n")
    c = repo.commit("C removes prehistory action")
    repo.branch("outside-side", before_c)
    repo.write("app/outside-side.txt", "carries pre-C origin\n")
    repo.commit("side carries pre-C action")
    old_birth = branch_birth(repo, "old", c)
    repo.branch("old-merge", old_birth)
    repo.merge_no_commit("outside-side")
    o = repo.commit("merge independent and pre-C origins")
    n = branch_birth(repo, "new", c)
    return [
        Fixture(
            "cross-C-side-origin",
            repo.path,
            c,
            o,
            n,
            expected,
            "ambiguous-origins",
            "U refuses a live origin entering through a parent outside C..tip",
        )
    ]


def build_cross_c_recreate(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "block", "B": "block", "D": "block"}
    repo = Repo(root / "25-cross-c-recreate", "25-cross-c-recreate")
    repo.write("app/base.txt", "before common\n")
    repo.write(ACTION_PATH, ACTION)
    before_c = repo.commit("pre-C action")
    repo.branch("common", before_c)
    repo.delete(ACTION_PATH)
    repo.write("app/base.txt", "common without action\n")
    c = repo.commit("C removes prehistory action")
    repo.branch("outside-side", before_c)
    repo.write("app/outside-side.txt", "carries pre-C origin\n")
    repo.commit("side carries pre-C action")
    repo.branch("old", c)
    repo.write("app/old.txt", "old arm\n")
    repo.commit("advance old arm")
    repo.merge_no_commit("outside-side")
    repo.write(ACTION_PATH, ACTION)
    repo.commit("import pre-C origin")
    repo.delete(ACTION_PATH)
    repo.commit("delete imported origin")
    repo.write(ACTION_PATH, ACTION)
    o = repo.commit("recreate local action")
    n = branch_birth(repo, "new", c)
    return [
        Fixture(
            "cross-C-import-delete-recreate",
            repo.path,
            c,
            o,
            n,
            expected,
            "outside-origin-replaced",
            "U remembers a deleted outside-C origin after local recreation",
        )
    ]


def build_governed_gitlink(root: Path) -> list[Fixture]:
    expected = {"E": "match", "U": "match", "B": "match", "D": "block"}
    repo, c = make_repo(root, "25-governed-gitlink")
    repo.branch("old", c)
    repo.write(ACTION_PATH, ACTION)
    repo.run("add", "-A")
    repo.run(
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        c,
        "queue/support",
    )
    o = repo.commit_staged("birth action with governed gitlink")
    n = branch_birth(repo, "new", c)
    return [
        Fixture(
            "governed-gitlink",
            repo.path,
            c,
            o,
            n,
            expected,
            "equivalent-X",
            "D includes non-blob governed tree entries",
        )
    ]


def build_reordering(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "26-reordering")
    branch_birth(repo, "old", c)
    repo.write("queue/support.txt", "support\n")
    o = repo.commit("support after birth")
    repo.branch("new", c)
    repo.write("queue/support.txt", "support\n")
    repo.commit("support before birth")
    repo.write(ACTION_PATH, ACTION)
    n = repo.commit("birth after support")
    return [
        Fixture(
            "reordering",
            repo.path,
            c,
            o,
            n,
            PASS,
            "changed-order",
            "D matches despite a different governed series order",
        )
    ]


def build_intent_twins(root: Path) -> list[Fixture]:
    repo, c = make_repo(root, "27-intent-twin")
    o = branch_birth(repo, "old", c, subject="same observable construction")
    n = branch_birth(repo, "new", c, subject="same observable construction")
    shared = {
        "repo": repo.path,
        "common": c,
        "old": o,
        "new": n,
        "expected": PASS,
        "lesson": "identical classifier inputs force identical results",
    }
    return [
        Fixture(
            "intent-twin-declared-replay",
            premise="declared-replay",
            intent_twin="intent-limit",
            **shared,
        ),
        Fixture(
            "intent-twin-declared-independent",
            premise="declared-independent",
            intent_twin="intent-limit",
            **shared,
        ),
    ]


BUILDERS = (
    build_normal,
    build_o_only_loss,
    build_delete_recreate,
    build_transient_mutation,
    build_binding_restore,
    build_multiplicity,
    build_neutral_merge,
    build_inherited_deleted,
    build_exact_cherry_pick,
    build_squash,
    build_path_move,
    build_retries,
    build_parent_order,
    build_unreadable,
    build_resource,
    build_outside_unrelated,
    build_governed_unrelated,
    build_timing_move,
    build_merge_vs_linear,
    build_parent_shape,
    build_independent,
    build_forged_metadata,
    build_extra_identity,
    build_support,
    build_cross_c_origin,
    build_cross_c_recreate,
    build_governed_gitlink,
    build_reordering,
    build_intent_twins,
)

DAMAGE_TARGET = {
    "endpoint-only": "delete-recreate",
    "ignore-arm-history": "inherited-then-deleted-arm",
    "trust-metadata": "forged-copyable-metadata",
    "full-commit-patch": "unrelated-outside-same-commit",
}


def build_all(root: Path, construction_order: str) -> list[Fixture]:
    builders = (
        BUILDERS if construction_order == "forward" else tuple(reversed(BUILDERS))
    )
    fixtures: list[Fixture] = []
    for builder in builders:
        fixtures.extend(builder(root))
    return sorted(fixtures, key=lambda item: item.scenario.encode("utf-8"))


def verify_records(
    records: list[dict[str, Any]], damage: str | None
) -> list[str]:
    failures: list[str] = []
    by_scenario = {record["scenario"]: record for record in records}
    for record in records:
        actual = {
            name: record["candidates"][name]["result"] for name in CANDIDATES
        }
        if actual != record["expected"]:
            failures.append(
                f"{record['scenario']}:expected={record['expected']}:actual={actual}"
            )
        if record["authority"] != "diagnostic-only":
            failures.append(
                f"{record['scenario']}:unsafe-authority={record['authority']}"
            )
        record["check"] = (
            "FAIL"
            if any(item.startswith(record["scenario"] + ":") for item in failures)
            else "PASS"
        )

    twins = [record for record in records if record["twin"] == "intent-limit"]
    if len(twins) != 2:
        failures.append("intent-limit:expected-two-records")
    elif twins[0]["observation_digest"] != twins[1]["observation_digest"]:
        failures.append("intent-limit:object-observations-differ")
    elif (
        twins[0]["off_object_intent_premise"]
        == twins[1]["off_object_intent_premise"]
    ):
        failures.append("intent-limit:external-premises-not-opposed")

    if damage is not None:
        target = DAMAGE_TARGET[damage]
        if by_scenario[target]["check"] != "FAIL":
            failures.append(f"damage-control:{damage}:target-stayed-green")
    return failures


def totals(
    records: list[dict[str, Any]],
    failures: list[str],
    damage: str | None,
) -> dict[str, Any]:
    candidate_totals: dict[str, dict[str, int]] = {}
    for name in CANDIDATES:
        counts = {"block": 0, "match": 0, "unavailable": 0}
        for record in records:
            counts[record["candidates"][name]["result"]] += 1
        candidate_totals[name] = counts
    d_extra_blocks = sum(
        record["candidates"]["B"]["result"] == "match"
        and record["candidates"]["D"]["result"] == "block"
        for record in records
    )
    return {
        "candidate_totals": candidate_totals,
        "damage_control": damage,
        "d_blocks_while_b_matches": d_extra_blocks,
        "failed": len(
            [record for record in records if record["check"] == "FAIL"]
        ),
        "failure_messages": len(failures),
        "information_limit_pairs": 1,
        "passed": len(
            [record for record in records if record["check"] == "PASS"]
        ),
        "schema": SCHEMA,
        "summary": "replay-oracle-poc",
        "total": len(records),
    }


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="construct and verify every real-Git scenario",
    )
    parser.add_argument(
        "--fixtures-dir",
        "--work-dir",
        dest="fixtures_dir",
        type=Path,
        help="new or empty directory in which to preserve fixtures",
    )
    parser.add_argument(
        "--construction-order",
        choices=("forward", "reverse"),
        default="forward",
    )
    parser.add_argument(
        "--negative-control",
        choices=tuple(DAMAGE_TARGET),
        help="run one named damaged classifier; expected to exit 1",
    )
    return parser.parse_args(list(argv))


def prepare_root(
    path: Path | None,
) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if path is None:
        temporary = tempfile.TemporaryDirectory(prefix="agentfold-replay-oracle-")
        return Path(temporary.name), temporary
    root = path.resolve()
    if root.exists() and not root.is_dir():
        raise GitError("refusing non-directory fixtures path")
    if root.exists() and any(root.iterdir()):
        raise GitError("refusing non-empty fixtures path")
    root.mkdir(parents=True, exist_ok=True)
    return root, None


def main(argv: Iterable[str] = ()) -> int:
    args = parse_args(argv)
    if not args.self_test and args.negative_control is None:
        print(
            "prototype.py requires --self-test or --negative-control",
            file=sys.stderr,
        )
        return 2
    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        root, temporary = prepare_root(args.fixtures_dir)
        fixtures = build_all(root, args.construction_order)
        records = [classify(item, args.negative_control) for item in fixtures]
        failures = verify_records(records, args.negative_control)
    except (GitError, OSError, UnicodeError) as exc:
        print(f"replay-oracle self-test failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()

    for record in records:
        print(canonical_bytes(record).decode("ascii"))
    summary = totals(records, failures, args.negative_control)
    print(canonical_bytes(summary).decode("ascii"))
    if failures:
        print(
            f"replay-oracle self-test failed: {summary['failed']}/"
            f"{summary['total']} scenario rows; {len(failures)} failure messages",
            file=sys.stderr,
        )
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        f"replay-oracle self-test: {summary['passed']}/"
        f"{summary['total']} scenario rows passed",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
