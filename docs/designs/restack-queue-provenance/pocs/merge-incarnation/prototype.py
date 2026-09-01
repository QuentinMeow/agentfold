#!/usr/bin/env python3
"""Adversarial supplier-witness POC over disposable real Git DAGs.

This is deliberately independent of AgentFold's production reconciler.  It tests
whether an exact candidate-side deletion witness can remain conservative across
merge parents and action incarnations.  It is a POC, not queue authority.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable


QUEUE_ROOT = "message-queue/"
DEFAULT_PATH = "message-queue/needs-agent/requests/non-blocking-action.md"
RENAMED_PATH = "message-queue/needs-agent/requests/non-blocking-action-renamed.md"
EVIDENCE_PATH = "docs/evidence.md"
FULL_OID = re.compile(r"^[0-9a-f]{40,64}$")


class GitFailure(RuntimeError):
    """A Git object or topology could not be inspected completely."""


@dataclasses.dataclass(frozen=True)
class Action:
    path: str
    action_id: str
    status: str
    evidence_path: str
    payload: str
    raw: str

    @property
    def incarnation(self) -> str:
        immutable = "\0".join((self.action_id, self.evidence_path, self.payload))
        return hashlib.sha256(immutable.encode()).hexdigest()


@dataclasses.dataclass
class Edge:
    parent: str
    child: str
    path: str
    valid: bool = False
    problem: str = "not validated"
    supplied_by_sibling: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "parent": self.parent,
            "child": self.child,
            "path": self.path,
            "valid": self.valid,
            "problem": self.problem,
            "supplied_by_sibling": self.supplied_by_sibling,
        }


@dataclasses.dataclass
class Verdict:
    classification: str
    authoring_lineage: str
    evidence_verdict: str
    witness_cardinality: int
    human_reason: str
    edges: list[Edge] = dataclasses.field(default_factory=list)
    git_processes: int = 0
    tree_reads: int = 0

    @property
    def result(self) -> str:
        if self.classification in {"exempt", "carried", "no-divergent-edge"}:
            return "no-finding"
        if self.classification == "snapshot-error":
            return "fail-closed"
        return "finding"


class GitRepo:
    """Small deterministic Git fixture plus immutable-object read caches."""

    def __init__(self, root: Path, *, initialize: bool = True) -> None:
        self.root = root
        self.git_processes = 0
        self.tree_reads = 0
        self._clock = 0
        self._snapshots: dict[str, dict[str, Action]] = {}
        self._parents: dict[str, tuple[str, ...]] = {}
        self._blobs: dict[tuple[str, str], bytes | None] = {}
        if initialize:
            root.mkdir(parents=True)
            self._outside_git("init", "-q", str(root))
            self.run("config", "user.name", "POC")
            self.run("config", "user.email", "poc@example.invalid")

    @staticmethod
    def _outside_git(*args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "--no-replace-objects", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def run(
        self,
        *args: str,
        check: bool = True,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        self.git_processes += 1
        env = os.environ.copy()
        env.update(
            {
                "LC_ALL": "C",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        if extra_env:
            env.update(extra_env)
        proc = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(self.root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        if check and proc.returncode:
            stderr = proc.stderr.decode(errors="replace").strip()
            raise GitFailure(f"git {' '.join(args)} failed ({proc.returncode}): {stderr}")
        return proc

    def reset_metrics(self) -> None:
        self.git_processes = 0
        self.tree_reads = 0
        self._snapshots.clear()
        self._parents.clear()
        self._blobs.clear()

    def write(self, relative: str, text: str) -> None:
        destination = self.root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)

    def remove(self, relative: str) -> None:
        destination = self.root / relative
        if destination.exists():
            destination.unlink()

    def commit(self, subject: str, changes: dict[str, str | None]) -> str:
        for relative, content in changes.items():
            if content is None:
                self.remove(relative)
            else:
                self.write(relative, content)
        self.run("add", "-A")
        self._clock += 1
        stamp = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(
            seconds=self._clock
        )
        date = stamp.isoformat()
        self.run(
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            subject,
            extra_env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date},
        )
        return self.oid("HEAD")

    def switch_new(self, branch: str, start: str) -> None:
        self.run("switch", "-q", "-c", branch, start)

    def switch(self, branch: str) -> None:
        self.run("switch", "-q", branch)

    def merge_commit(
        self, other: str, subject: str, changes: dict[str, str | None]
    ) -> str:
        merge = self.run("merge", "--no-ff", "--no-commit", other, check=False)
        if merge.returncode:
            stderr = merge.stderr.decode(errors="replace").strip()
            raise GitFailure(f"fixture merge failed ({merge.returncode}): {stderr}")
        for relative, content in changes.items():
            if content is None:
                self.remove(relative)
            else:
                self.write(relative, content)
        self.run("add", "-A")
        self._clock += 1
        stamp = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(
            seconds=self._clock
        )
        date = stamp.isoformat()
        self.run(
            "commit",
            "-q",
            "-m",
            subject,
            extra_env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date},
        )
        return self.oid("HEAD")

    def oid(self, revision: str) -> str:
        return self.run("rev-parse", f"{revision}^{{commit}}").stdout.decode().strip()

    def validate_commit(self, oid: str) -> None:
        probe = self.run("cat-file", "-e", f"{oid}^{{commit}}", check=False)
        if probe.returncode:
            raise GitFailure(f"required commit is unavailable: {oid}")

    def is_ancestor(self, older: str, newer: str) -> bool:
        probe = self.run("merge-base", "--is-ancestor", older, newer, check=False)
        if probe.returncode == 0:
            return True
        if probe.returncode == 1:
            return False
        raise GitFailure(
            "ancestry inspection failed: "
            + probe.stderr.decode(errors="replace").strip()
        )

    def merge_bases(self, left: str, right: str) -> tuple[str, ...]:
        probe = self.run("merge-base", "--all", left, right, check=False)
        if probe.returncode not in {0, 1}:
            raise GitFailure(
                "merge-base inspection failed: "
                + probe.stderr.decode(errors="replace").strip()
            )
        bases = tuple(line for line in probe.stdout.decode().splitlines() if line)
        if not bases:
            raise GitFailure("tips have no available common history")
        return bases

    def parents(self, oid: str) -> tuple[str, ...]:
        if oid not in self._parents:
            text = self.run("show", "-s", "--format=%P", oid).stdout.decode().strip()
            self._parents[oid] = tuple(text.split()) if text else ()
        return self._parents[oid]

    def revisions(self, *args: str) -> list[str]:
        text = self.run("rev-list", *args).stdout.decode()
        return [line for line in text.splitlines() if line]

    def snapshot(self, oid: str) -> dict[str, Action]:
        if oid in self._snapshots:
            return self._snapshots[oid]
        self.tree_reads += 1
        listing = self.run(
            "ls-tree", "-r", "-z", "--name-only", oid, "--", QUEUE_ROOT
        ).stdout
        result: dict[str, Action] = {}
        for encoded in listing.split(b"\0"):
            if not encoded:
                continue
            path = encoded.decode()
            raw = self.run("show", f"{oid}:{path}").stdout.decode()
            result[path] = parse_action(path, raw)
        self._snapshots[oid] = result
        return result

    def blob(self, oid: str, path: str) -> bytes | None:
        key = (oid, path)
        if key not in self._blobs:
            probe = self.run("show", f"{oid}:{path}", check=False)
            if probe.returncode == 0:
                self._blobs[key] = probe.stdout
            elif b"does not exist" in probe.stderr or b"exists on disk" in probe.stderr:
                self._blobs[key] = None
            else:
                raise GitFailure(
                    f"blob inspection failed for {oid}:{path}: "
                    + probe.stderr.decode(errors="replace").strip()
                )
        return self._blobs[key]


def parse_action(path: str, raw: str) -> Action:
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            fields[key] = value
    required = ("Action-ID", "Status", "Evidence", "Payload")
    missing = [field for field in required if field not in fields]
    if missing:
        raise GitFailure(f"unparseable queue fixture {path}: missing {', '.join(missing)}")
    return Action(
        path=path,
        action_id=fields["Action-ID"],
        status=fields["Status"],
        evidence_path=fields["Evidence"],
        payload=fields["Payload"],
        raw=raw,
    )


def action_text(
    *,
    action_id: str = "Q",
    status: str = "open",
    payload: str = "base obligation",
    evidence: str = EVIDENCE_PATH,
) -> str:
    return (
        f"Action-ID: {action_id}\n"
        f"Status: {status}\n"
        f"Evidence: {evidence}\n"
        f"Payload: {payload}\n"
    )


def occurrences(snapshot: dict[str, Action], incarnation: str) -> list[Action]:
    return [action for action in snapshot.values() if action.incarnation == incarnation]


def same_id(snapshot: dict[str, Action], action_id: str) -> list[Action]:
    return [action for action in snapshot.values() if action.action_id == action_id]


def claim_transition_exists(
    repo: GitRepo, deletion_parent: str, incarnation: str
) -> bool:
    for child in repo.revisions("--topo-order", deletion_parent):
        child_actions = occurrences(repo.snapshot(child), incarnation)
        if len(child_actions) != 1:
            continue
        for parent in repo.parents(child):
            parent_actions = occurrences(repo.snapshot(parent), incarnation)
            if (
                len(parent_actions) == 1
                and parent_actions[0].status == "open"
                and child_actions[0].status == "in-repair"
            ):
                return True
    return False


def validate_edge(repo: GitRepo, edge: Edge, incarnation: str) -> None:
    parent_actions = occurrences(repo.snapshot(edge.parent), incarnation)
    if len(parent_actions) != 1:
        edge.problem = "deletion parent does not carry one exact incarnation"
        return
    action = parent_actions[0]
    if action.status != "in-repair":
        edge.problem = "action was not committed as in-repair before deletion"
        return
    if not claim_transition_exists(repo, edge.parent, incarnation):
        edge.problem = "no committed open-to-in-repair claim edge"
        return
    before = repo.blob(edge.parent, action.evidence_path)
    after = repo.blob(edge.child, action.evidence_path)
    if after is None or before == after:
        edge.problem = "declared non-queue evidence did not change on deletion edge"
        return
    edge.valid = True
    edge.problem = "lifecycle and deletion-edge evidence are valid"


def classify(repo: GitRepo, old_tip: str, new_head: str, old_path: str) -> Verdict:
    repo.reset_metrics()
    try:
        shallow = repo.run("rev-parse", "--is-shallow-repository").stdout.decode().strip()
        if shallow == "true":
            raise GitFailure("repository is shallow; candidate history may be incomplete")
        repo.validate_commit(old_tip)
        repo.validate_commit(new_head)
        if repo.is_ancestor(old_tip, new_head):
            verdict = Verdict(
                "no-divergent-edge",
                "ordinary extension",
                "not-applicable",
                0,
                "The displaced tip is an ancestor of the candidate, so no history "
                "replacement occurred.",
            )
            return with_metrics(repo, verdict)

        old_snapshot = repo.snapshot(old_tip)
        if old_path not in old_snapshot:
            raise GitFailure(f"old tip does not carry requested action path: {old_path}")
        old_action = old_snapshot[old_path]
        incarnation = old_action.incarnation

        bases = repo.merge_bases(old_tip, new_head)
        if len(bases) != 1:
            raise GitFailure(f"ambiguous common history: {len(bases)} merge bases")
        boundary = bases[0]
        boundary_matches = occurrences(repo.snapshot(boundary), incarnation)
        if (
            len(boundary_matches) != 1
            or boundary_matches[0].path != old_path
            or boundary_matches[0].raw != old_action.raw
        ):
            verdict = Verdict(
                "finding",
                "old-side authored or changed",
                "not-applicable",
                0,
                "The old task lineage introduced, moved, claimed, or changed this action "
                "after the common boundary; candidate-side evidence cannot resolve that "
                "distinct old-tip state.",
            )
            return with_metrics(repo, verdict)

        candidate = repo.revisions("--topo-order", new_head, "--not", old_tip)
        candidate_set = set(candidate)
        edges: list[Edge] = []
        ambiguous_state = False
        identity_mutation = False
        for child in candidate:
            child_snapshot = repo.snapshot(child)
            child_matches = occurrences(child_snapshot, incarnation)
            if len(child_matches) > 1:
                ambiguous_state = True
            for parent in repo.parents(child):
                parent_snapshot = repo.snapshot(parent)
                parent_matches = occurrences(parent_snapshot, incarnation)
                if len(parent_matches) > 1:
                    ambiguous_state = True
                if len(parent_matches) == 1 and not child_matches:
                    if same_id(child_snapshot, old_action.action_id):
                        identity_mutation = True
                    edges.append(
                        Edge(parent, child, parent_matches[0].path)
                    )

        for edge in edges:
            validate_edge(repo, edge, incarnation)

        # A merge result may appear to delete relative to one parent even though an
        # absent sibling supplies a prior, real deletion.  Ignore only when that
        # sibling contains a validated deletion in its own ancestry.
        for edge in edges:
            parents = repo.parents(edge.child)
            if len(parents) < 2:
                continue
            for sibling in parents:
                if sibling == edge.parent:
                    continue
                if occurrences(repo.snapshot(sibling), incarnation):
                    continue
                if any(
                    other is not edge
                    and other.valid
                    and other.child in candidate_set
                    and repo.is_ancestor(other.child, sibling)
                    for other in edges
                ):
                    edge.supplied_by_sibling = True
                    break

        effective = [edge for edge in edges if not edge.supplied_by_sibling]
        new_snapshot = repo.snapshot(new_head)
        new_matches = occurrences(new_snapshot, incarnation)
        new_same_id = same_id(new_snapshot, old_action.action_id)

        if ambiguous_state or len(new_matches) > 1:
            verdict = Verdict(
                "finding",
                "ambiguous candidate incarnation",
                "ambiguous",
                len(effective),
                "The candidate graph contains duplicate copies of the same action "
                "incarnation, so no unique carry or resolution can be attested.",
                edges,
            )
            return with_metrics(repo, verdict)
        if identity_mutation or (new_same_id and not new_matches):
            verdict = Verdict(
                "finding",
                "candidate changed action identity",
                "invalid: identity changed",
                len(effective),
                "The candidate reused the action id with different immutable content; "
                "a witness for the old incarnation cannot authorize that mutation.",
                edges,
            )
            return with_metrics(repo, verdict)
        if len(new_matches) == 1:
            if effective:
                verdict = Verdict(
                    "finding",
                    "delete-and-recreate candidate history",
                    "ambiguous",
                    len(effective),
                    "The final tree carries the action, but candidate history deleted and "
                    "recreated its incarnation; final-tree equality is not continuity.",
                    edges,
                )
            else:
                verdict = Verdict(
                    "carried",
                    "candidate carries one exact incarnation",
                    "not-applicable",
                    0,
                    f"The live obligation is preserved unambiguously at "
                    f"{new_matches[0].path}.",
                    edges,
                )
            return with_metrics(repo, verdict)
        if len(effective) != 1:
            valid_count = sum(edge.valid for edge in effective)
            verdict = Verdict(
                "finding",
                "candidate resolution is absent or ambiguous",
                f"ambiguous: {valid_count} valid of {len(effective)} witnesses",
                len(effective),
                "Exactly one causal deletion witness is required; zero or competing "
                "candidate-side deletions fail closed.",
                edges,
            )
            return with_metrics(repo, verdict)
        witness = effective[0]
        if not witness.valid:
            verdict = Verdict(
                "finding",
                "candidate-side deletion",
                f"invalid: {witness.problem}",
                1,
                "The candidate lineage deleted the inherited action, but its concrete "
                f"edge is unauthorized: {witness.problem}.",
                edges,
            )
            return with_metrics(repo, verdict)
        verdict = Verdict(
            "exempt",
            "candidate-side validated resolution",
            "valid",
            1,
            "The old branch left the action unchanged, and exactly one candidate-side "
            "deletion edge carries a committed claim plus changed resolution evidence.",
            edges,
        )
        return with_metrics(repo, verdict)
    except GitFailure as error:
        verdict = Verdict(
            "snapshot-error",
            "unattested",
            f"unreadable: {error}",
            0,
            f"Git provenance is incomplete or ambiguous, so the POC fails closed: {error}.",
        )
        return with_metrics(repo, verdict)


def with_metrics(repo: GitRepo, verdict: Verdict) -> Verdict:
    verdict.git_processes = repo.git_processes
    verdict.tree_reads = repo.tree_reads
    return verdict


def make_record(
    scenario: str,
    refs: dict[str, str],
    verdict: Verdict,
    expected: str,
) -> dict[str, object]:
    for name in ("C", "O", "M", "N"):
        if name not in refs or not FULL_OID.match(refs[name]):
            raise AssertionError(f"{scenario}: {name} is not a full object id")
    return {
        "scenario": scenario,
        "C": refs["C"],
        "O": refs["O"],
        "M": refs["M"],
        "N": refs["N"],
        "classification": verdict.classification,
        "authoring_lineage": verdict.authoring_lineage,
        "witness_cardinality": verdict.witness_cardinality,
        "evidence_verdict": verdict.evidence_verdict,
        "expected_result": expected,
        "actual_result": verdict.result,
        "human_reason": verdict.human_reason,
        "git_processes": verdict.git_processes,
        "tree_reads": verdict.tree_reads,
        "edges": [edge.as_dict() for edge in verdict.edges],
    }


def base_repo(root: Path, *, live: bool = True) -> tuple[GitRepo, str]:
    repo = GitRepo(root)
    changes = {"README.md": "fixture\n", EVIDENCE_PATH: "evidence v0\n"}
    if live:
        changes[DEFAULT_PATH] = action_text()
    return repo, repo.commit("common", changes)


def scenario_valid(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old feature\n"})
    repo.switch_new("new", common)
    repo.commit("claim", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "resolve",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old feature\n"})
    return make_record(
        "S1-valid-base-resolution",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )


def scenario_invalid(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old feature\n"})
    repo.switch_new("new", common)
    new_base = repo.commit("delete without claim", {DEFAULT_PATH: None})
    new = repo.commit("replay feature", {"feature.txt": "old feature\n"})
    return make_record(
        "S2-invalid-base-deletion",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_old_loss(root: Path) -> dict[str, object]:
    repo, common = base_repo(root, live=False)
    repo.switch_new("old", common)
    old = repo.commit(
        "old adds action",
        {DEFAULT_PATH: action_text(), "feature.txt": "old feature\n"},
    )
    repo.switch_new("new", common)
    new_base = repo.commit("new base", {"base.txt": "base\n"})
    new = repo.commit("replay feature", {"feature.txt": "old feature\n"})
    return make_record(
        "S3-branch-owned-action-loss",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_same_path(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit(
        "old changes action",
        {DEFAULT_PATH: action_text(payload="branch-authored obligation")},
    )
    repo.switch_new("new", common)
    repo.commit("claim original", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "resolve original",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("new feature", {"feature.txt": "new\n"})
    return make_record(
        "S6-same-path-concurrency",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_rename_carry(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    text = action_text()
    new_base = repo.commit(
        "rename action", {DEFAULT_PATH: None, RENAMED_PATH: text}
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    return make_record(
        "S11-rename-carry",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )


def scenario_merge_base(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("resolved", common)
    repo.commit("claim", {DEFAULT_PATH: action_text(status="in-repair")})
    resolved = repo.commit(
        "resolve on side",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    repo.switch_new("base", common)
    repo.commit("base feature", {"base.txt": "base\n"})
    new_base = repo.merge_commit("resolved", "merge resolved base", {})
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    assert repo.is_ancestor(resolved, new_base)
    return make_record(
        "S12-merge-shaped-new-base",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )


def scenario_merge_only_deletion(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("left", common)
    repo.commit(
        "left claims",
        {DEFAULT_PATH: action_text(status="in-repair"), "left.txt": "left\n"},
    )
    repo.switch_new("right", common)
    repo.commit(
        "right claims",
        {DEFAULT_PATH: action_text(status="in-repair"), "right.txt": "right\n"},
    )
    repo.switch("left")
    new_base = repo.merge_commit(
        "right",
        "merge deletes action",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "merge evidence\n"},
    )
    new = repo.commit("new head", {"head.txt": "head\n"})
    return make_record(
        "A1-merge-commit-only-deletion",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_competing_edges(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("valid", common)
    repo.commit("valid claim", {DEFAULT_PATH: action_text(status="in-repair")})
    repo.commit(
        "valid deletion",
        {
            DEFAULT_PATH: None,
            EVIDENCE_PATH: "valid evidence\n",
            "valid.txt": "valid\n",
        },
    )
    repo.switch_new("invalid", common)
    repo.commit(
        "invalid deletion",
        {DEFAULT_PATH: None, "invalid.txt": "invalid\n"},
    )
    repo.switch("valid")
    new_base = repo.merge_commit("invalid", "merge competing deletions", {})
    new = repo.commit("new head", {"head.txt": "head\n"})
    return make_record(
        "A2-valid-and-invalid-competing-edges",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


INITIAL_SCENARIOS = (
    scenario_valid,
    scenario_invalid,
    scenario_old_loss,
    scenario_same_path,
    scenario_rename_carry,
    scenario_merge_base,
    scenario_merge_only_deletion,
    scenario_competing_edges,
)


def run_self_test() -> int:
    records: list[dict[str, object]] = []
    failures = 0
    with tempfile.TemporaryDirectory(prefix="agentfold-merge-incarnation-poc-") as tmp:
        base = Path(tmp)
        for index, builder in enumerate(INITIAL_SCENARIOS):
            record = builder(base / f"case-{index:02d}")
            if record["actual_result"] != record["expected_result"]:
                failures += 1
            records.append(record)
            print(json.dumps(record, sort_keys=True))
    summary = {
        "summary": "merge-incarnation-poc",
        "passed": len(records) - failures,
        "total": len(records),
        "failed": failures,
        "python": sys.version.split()[0],
        "git": subprocess.run(
            ["git", "--version"],
            stdout=subprocess.PIPE,
            check=True,
            text=True,
        ).stdout.strip(),
    }
    print(json.dumps(summary, sort_keys=True))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="construct disposable Git DAGs and check every expected verdict",
    )
    args = parser.parse_args()
    if not args.self_test:
        parser.error("--self-test is required")
    if shutil.which("git") is None:
        print("git is required", file=sys.stderr)
        return 2
    return run_self_test()


if __name__ == "__main__":
    raise SystemExit(main())
