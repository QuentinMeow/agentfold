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
import time


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
    grouped_in_child_component: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "parent": self.parent,
            "child": self.child,
            "path": self.path,
            "valid": self.valid,
            "problem": self.problem,
            "supplied_by_sibling": self.supplied_by_sibling,
            "grouped_in_child_component": self.grouped_in_child_component,
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

    def commit_tree(self, tree: str, parents: tuple[str, ...], subject: str) -> str:
        self._clock += 1
        stamp = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(
            seconds=self._clock
        )
        date = stamp.isoformat()
        args = ["commit-tree", tree]
        for parent in parents:
            args.extend(("-p", parent))
        args.extend(("-m", subject))
        return self.run(
            *args,
            extra_env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date},
        ).stdout.decode().strip()

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
        bold = re.fullmatch(r"\*\*([A-Za-z][A-Za-z -]*):\*\*\s*(.*)", line)
        if bold:
            fields[bold.group(1)] = bold.group(2)
            continue
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


def normalize_action_status(raw: str) -> str:
    normalized = re.sub(
        r"^Status:.*$",
        "Status: <claim-status>",
        raw,
        flags=re.M,
    )
    return re.sub(
        r"^(\*\*Status:\*\*)[ \t]*.*$",
        r"\1 <claim-status>",
        normalized,
        flags=re.M,
    )


def disconnected_parent_origin_problem(
    repo: GitRepo,
    revisions: list[str],
    incarnation: str,
    action_id: str,
) -> str | None:
    """Require carrying merge parents to share an origin before their child.

    A merge child is not evidence that two byte-identical actions are the same
    occurrence.  Compute each carrying parent's continuous backwards component
    separately.  Multiple carrying parents are compatible only when those
    pre-merge components already intersect.
    """

    memo: dict[str, tuple[frozenset[str] | None, str | None]] = {}

    def component(revision: str) -> tuple[frozenset[str] | None, str | None]:
        if revision in memo:
            return memo[revision]
        snapshot = repo.snapshot(revision)
        matches = occurrences(snapshot, incarnation)
        identities = same_id(snapshot, action_id)
        if len(matches) != 1 or len(identities) != 1:
            result = (frozenset(), None)
            memo[revision] = result
            return result

        action = matches[0]
        parents = repo.parents(revision)
        carrying_components: list[frozenset[str]] = []
        for parent in parents:
            parent_snapshot = repo.snapshot(parent)
            parent_matches = occurrences(parent_snapshot, incarnation)
            parent_identities = same_id(parent_snapshot, action_id)
            if len(parent_matches) != 1 or len(parent_identities) != 1:
                continue
            parent_action = parent_matches[0]
            if parent_action.path != action.path:
                if len(parents) != 1 or parent_action.path in snapshot:
                    result = (
                        None,
                        "merge origin has ambiguous rename provenance on edge "
                        f"{parent}->{revision}",
                    )
                    memo[revision] = result
                    return result
            if (
                normalize_action_status(parent_action.raw)
                != normalize_action_status(action.raw)
            ):
                result = (
                    None,
                    "merge origin mutated outside status on edge "
                    f"{parent}->{revision}",
                )
                memo[revision] = result
                return result
            parent_component, problem = component(parent)
            if problem is not None or parent_component is None:
                result = (None, problem or "merge origin proof is unavailable")
                memo[revision] = result
                return result
            carrying_components.append(parent_component)

        if len(carrying_components) > 1:
            shared = set(carrying_components[0])
            for parent_component in carrying_components[1:]:
                shared.intersection_update(parent_component)
            if not shared:
                result = (
                    None,
                    "merge carrying parents have disconnected occurrence origins at "
                    f"{revision}",
                )
                memo[revision] = result
                return result

        connected = {revision}
        for parent_component in carrying_components:
            connected.update(parent_component)
        result = (frozenset(connected), None)
        memo[revision] = result
        return result

    for revision in dict.fromkeys(revisions):
        _component, problem = component(revision)
        if problem is not None:
            return problem
    return None


def dag_occurrence_continuity_problem(
    repo: GitRepo,
    deletion_parent: str,
    incarnation: str,
    action_id: str,
    origin_revisions: list[str] | None = None,
) -> str | None:
    """Require every carrying parent lineage to reach one shared claim edge."""

    origin_problem = disconnected_parent_origin_problem(
        repo,
        origin_revisions or [deletion_parent],
        incarnation,
        action_id,
    )
    if origin_problem is not None:
        return origin_problem

    ClaimEdge = tuple[str, str]
    memo: dict[str, tuple[frozenset[ClaimEdge] | None, str | None]] = {}

    def prove(child: str) -> tuple[frozenset[ClaimEdge] | None, str | None]:
        if child in memo:
            return memo[child]
        child_snapshot = repo.snapshot(child)
        child_matches = occurrences(child_snapshot, incarnation)
        child_same_id = same_id(child_snapshot, action_id)
        if len(child_matches) != 1 or len(child_same_id) != 1:
            result = (None, f"merge occurrence is ambiguous at {child}")
            memo[child] = result
            return result
        child_action = child_matches[0]
        parents = repo.parents(child)
        lineage_sources: list[frozenset[ClaimEdge]] = []
        carrying_parents = 0
        for parent in parents:
            parent_snapshot = repo.snapshot(parent)
            parent_matches = occurrences(parent_snapshot, incarnation)
            parent_same_id = same_id(parent_snapshot, action_id)
            if len(parent_matches) > 1 or len(parent_same_id) > 1:
                result = (
                    None,
                    f"merge occurrence has duplicate ancestry at {parent}",
                )
                memo[child] = result
                return result
            if not parent_matches:
                if parent_same_id:
                    result = (
                        None,
                        "merge occurrence crosses another incarnation on edge "
                        f"{parent}->{child}",
                    )
                    memo[child] = result
                    return result
                continue
            if len(parent_same_id) != 1:
                result = (
                    None,
                    f"merge occurrence identity is unreadable at {parent}",
                )
                memo[child] = result
                return result
            carrying_parents += 1
            parent_action = parent_matches[0]
            if parent_action.path != child_action.path:
                if len(parents) != 1 or parent_action.path in child_snapshot:
                    result = (
                        None,
                        "merge occurrence has ambiguous rename provenance on edge "
                        f"{parent}->{child}",
                    )
                    memo[child] = result
                    return result
            if (
                normalize_action_status(parent_action.raw)
                != normalize_action_status(child_action.raw)
            ):
                result = (
                    None,
                    "merge occurrence mutated outside status on edge "
                    f"{parent}->{child}",
                )
                memo[child] = result
                return result
            if (
                parent_action.status == "open"
                and child_action.status == "in-repair"
            ):
                lineage_sources.append(frozenset({(parent, child)}))
                continue
            parent_sources, problem = prove(parent)
            if problem is not None or parent_sources is None:
                result = (None, problem or "merge occurrence proof is unavailable")
                memo[child] = result
                return result
            lineage_sources.append(parent_sources)
        if carrying_parents == 0:
            # This is the occurrence boundary. The linear bounded-claim check
            # decides whether it is a legal new occurrence; the DAG guard only
            # adds the stronger all-carrying-parent requirement at merges.
            result = (frozenset(), None)
        elif carrying_parents > 1 and any(
            len(source) != 1 for source in lineage_sources
        ):
            result = (
                None,
                "merge occurrence has a carrying parent without one claim source",
            )
        else:
            sources = frozenset().union(*lineage_sources)
            if carrying_parents > 1 and len(sources) != 1:
                result = (
                    None,
                    f"merge occurrence has {len(sources)} competing claim sources",
                )
            else:
                result = (sources, None)
        memo[child] = result
        return result

    _sources, problem = prove(deletion_parent)
    return problem


def bounded_claim_transition_problem(
    repo: GitRepo,
    deletion_parent: str,
    incarnation: str,
    action_id: str,
) -> str | None:
    """Find a claim only inside the occurrence live at the deletion parent.

    A fingerprint can recur after an absence.  Walking every ancestor would let a
    later byte-identical occurrence borrow an earlier occurrence's claim.  Walk
    backward only while exactly one matching action remains continuously present;
    absence or another incarnation ends that branch, while duplicate identity or
    ambiguous rename state fails closed.
    """

    stack = [deletion_parent]
    seen: set[str] = set()
    claim_found = False
    while stack:
        child = stack.pop()
        if child in seen:
            continue
        seen.add(child)
        child_snapshot = repo.snapshot(child)
        child_matches = occurrences(child_snapshot, incarnation)
        child_same_id = same_id(child_snapshot, action_id)
        if len(child_matches) != 1 or len(child_same_id) != 1:
            return f"current occurrence is ambiguous at {child}"
        child_action = child_matches[0]
        parents = repo.parents(child)
        for parent in parents:
            parent_snapshot = repo.snapshot(parent)
            parent_matches = occurrences(parent_snapshot, incarnation)
            parent_same_id = same_id(parent_snapshot, action_id)
            if len(parent_matches) > 1 or len(parent_same_id) > 1:
                return f"current occurrence has ambiguous ancestry at {parent}"
            if len(parent_matches) != 1 or len(parent_same_id) != 1:
                # Absence, recreation, or another incarnation is the beginning of
                # this occurrence.  Do not inspect ancestors across that boundary.
                continue
            parent_action = parent_matches[0]
            if parent_action.path != child_action.path:
                if len(parents) != 1 or parent_action.path in child_snapshot:
                    return (
                        "current occurrence has ambiguous rename ancestry on edge "
                        f"{parent}->{child}"
                    )
            if (
                normalize_action_status(parent_action.raw)
                != normalize_action_status(child_action.raw)
            ):
                return (
                    "current occurrence mutated outside status on edge "
                    f"{parent}->{child}"
                )
            if (
                parent_action.status == "open"
                and child_action.status == "in-repair"
            ):
                claim_found = True
            stack.append(parent)
    if claim_found:
        return None
    return "no committed open-to-in-repair claim exists in the current occurrence"


def sibling_incarnation_problem(
    repo: GitRepo,
    candidate: list[str],
    boundary: str,
    incarnation: str,
    action_id: str,
) -> str | None:
    """Reject a same-ID sibling unless it shares C's continuous occurrence.

    A deletion edge names only one parent, but a merge can delete another action
    with the same Action-ID from a sibling parent.  Treat every candidate state and
    every one of its direct parents as relevant.  An exact occurrence is inherited
    only when its backwards chain of unique, byte-stable carries intersects the
    backwards chain of the occurrence at C.  This permits an occurrence that forked
    before C while rejecting an independently recreated byte-identical occurrence.
    """

    memo: dict[str, tuple[frozenset[str] | None, str | None]] = {}

    def component(revision: str) -> tuple[frozenset[str] | None, str | None]:
        if revision in memo:
            return memo[revision]
        snapshot = repo.snapshot(revision)
        matches = occurrences(snapshot, incarnation)
        identities = same_id(snapshot, action_id)
        if len(identities) > 1:
            result = (
                None,
                f"candidate occurrence duplicates Action-ID at {revision}",
            )
            memo[revision] = result
            return result
        if len(identities) != 1 or len(matches) != 1:
            result = (
                None,
                f"candidate occurrence is not the inherited incarnation at {revision}",
            )
            memo[revision] = result
            return result

        action = matches[0]
        parents = repo.parents(revision)
        connected = {revision}
        for parent in parents:
            parent_snapshot = repo.snapshot(parent)
            parent_matches = occurrences(parent_snapshot, incarnation)
            parent_identities = same_id(parent_snapshot, action_id)
            if len(parent_identities) > 1:
                result = (
                    None,
                    f"candidate occurrence duplicates Action-ID at parent {parent}",
                )
                memo[revision] = result
                return result
            if not parent_identities:
                continue
            if len(parent_matches) != 1:
                result = (
                    None,
                    "candidate parent carries conflicting same-ID incarnation on edge "
                    f"{parent}->{revision}",
                )
                memo[revision] = result
                return result
            parent_action = parent_matches[0]
            if parent_action.path != action.path:
                if len(parents) != 1 or parent_action.path in snapshot:
                    result = (
                        None,
                        "candidate occurrence has ambiguous rename provenance on edge "
                        f"{parent}->{revision}",
                    )
                    memo[revision] = result
                    return result
            if (
                normalize_action_status(parent_action.raw)
                != normalize_action_status(action.raw)
            ):
                result = (
                    None,
                    "candidate occurrence mutated outside status on edge "
                    f"{parent}->{revision}",
                )
                memo[revision] = result
                return result
            parent_component, problem = component(parent)
            if problem is not None or parent_component is None:
                result = (None, problem or "candidate occurrence proof is unavailable")
                memo[revision] = result
                return result
            connected.update(parent_component)
        result = (frozenset(connected), None)
        memo[revision] = result
        return result

    boundary_component, boundary_problem = component(boundary)
    if boundary_problem is not None or boundary_component is None:
        return boundary_problem or "common occurrence proof is unavailable"

    inspected = list(candidate)
    for child in candidate:
        inspected.extend(repo.parents(child))
    inspected = list(dict.fromkeys(inspected))
    for revision in inspected:
        snapshot = repo.snapshot(revision)
        identities = same_id(snapshot, action_id)
        if not identities:
            continue
        if len(identities) > 1:
            return f"candidate graph duplicates Action-ID at {revision}"
        matches = occurrences(snapshot, incarnation)
        if len(matches) != 1:
            return (
                "candidate graph contains conflicting same-ID incarnation at "
                f"{revision}"
            )
        revision_component, problem = component(revision)
        if problem is not None or revision_component is None:
            return problem or f"candidate occurrence proof is unavailable at {revision}"
        if boundary_component.isdisjoint(revision_component):
            return (
                "candidate same-ID action does not share the inherited occurrence at "
                f"{revision}"
            )
    return None


def validate_edge(
    repo: GitRepo,
    edge: Edge,
    incarnation: str,
    sibling_problem: str | None = None,
    origin_revisions: list[str] | None = None,
) -> None:
    parent_actions = occurrences(repo.snapshot(edge.parent), incarnation)
    if len(parent_actions) != 1:
        edge.problem = "deletion parent does not carry one exact incarnation"
        return
    action = parent_actions[0]
    if action.status != "in-repair":
        edge.problem = "action was not committed as in-repair before deletion"
        return
    if sibling_problem is not None:
        edge.problem = sibling_problem
        return
    occurrence_problem = dag_occurrence_continuity_problem(
        repo,
        edge.parent,
        incarnation,
        action.action_id,
        origin_revisions,
    )
    if occurrence_problem is not None:
        edge.problem = occurrence_problem
        return
    claim_problem = bounded_claim_transition_problem(
        repo,
        edge.parent,
        incarnation,
        action.action_id,
    )
    if claim_problem is not None:
        edge.problem = claim_problem
        return
    before = repo.blob(edge.parent, action.evidence_path)
    after = repo.blob(edge.child, action.evidence_path)
    if after is None or before == after:
        edge.problem = "declared non-queue evidence did not change on deletion edge"
        return
    edge.valid = True
    edge.problem = "lifecycle and deletion-edge evidence are valid"


def post_witness_absence_problem(
    repo: GitRepo,
    edge: Edge,
    new_head: str,
    incarnation: str,
    action_id: str,
) -> str | None:
    """Require the witnessed absence to stay continuous through N."""

    descendants = repo.revisions(
        "--topo-order",
        new_head,
        "--ancestry-path",
        f"{edge.child}..{new_head}",
    )
    for revision in descendants:
        snapshot = repo.snapshot(revision)
        if occurrences(snapshot, incarnation) or same_id(snapshot, action_id):
            return (
                "action reappears after the deletion witness at "
                f"{revision}"
            )
    return None


def group_valid_merge_deletion_components(
    repo: GitRepo,
    edges: list[Edge],
) -> None:
    """Count one merge-authored deletion child after every parent edge validates.

    Git exposes one deletion relative to each carrying parent, but a merge commit
    authors one resulting tree.  Group those edges into one witness only when every
    direct parent carries the deletion and every real parent edge independently
    passed lifecycle, occurrence, origin, sibling, evidence, and post-witness checks.
    """

    by_child: dict[str, list[Edge]] = {}
    for edge in edges:
        if not edge.supplied_by_sibling:
            by_child.setdefault(edge.child, []).append(edge)
    for child, component in by_child.items():
        parents = repo.parents(child)
        if len(parents) < 2 or len(component) != len(parents):
            continue
        if {edge.parent for edge in component} != set(parents):
            continue
        if not all(edge.valid for edge in component):
            continue
        for edge in component[1:]:
            edge.grouped_in_child_component = True


def old_lineage_continuity_problem(
    repo: GitRepo,
    boundary: str,
    old_tip: str,
    incarnation: str,
    action_id: str,
    expected_raw: str,
) -> str | None:
    """Prove the exact incarnation stayed continuously live from boundary to O.

    Final-tree equality is insufficient: delete/recreate can restore byte-identical
    content while changing the action incarnation.  Inspect every old-only parent
    edge and require one exact, byte-stable copy on both sides.  A unique path move
    is allowed because the incarnation remains present on the same edge.
    """

    for child in repo.revisions("--topo-order", old_tip, "--not", boundary):
        child_snapshot = repo.snapshot(child)
        child_matches = occurrences(child_snapshot, incarnation)
        child_same_id = same_id(child_snapshot, action_id)
        if len(child_matches) != 1:
            if len(child_same_id) == 1:
                return f"old lineage changed action identity at {child}"
            if len(child_same_id) > 1:
                return (
                    f"old lineage duplicated action identity at {child}"
                )
            return f"old lineage deleted the action incarnation at {child}"
        if len(child_same_id) != 1 or child_matches[0].raw != expected_raw:
            return f"old lineage mutated the action incarnation at {child}"
        for parent in repo.parents(child):
            parent_snapshot = repo.snapshot(parent)
            parent_matches = occurrences(parent_snapshot, incarnation)
            parent_same_id = same_id(parent_snapshot, action_id)
            if len(parent_matches) != 1:
                if len(parent_same_id) == 1:
                    return (
                        "old lineage changed action identity on edge "
                        f"{parent}->{child}"
                    )
                if len(parent_same_id) > 1:
                    return (
                        "old lineage duplicated action identity on edge "
                        f"{parent}->{child}"
                    )
                return (
                    "old lineage deleted or recreated the action on edge "
                    f"{parent}->{child}"
                )
            if len(parent_same_id) != 1 or parent_matches[0].raw != expected_raw:
                return (
                    "old lineage mutated the action on edge "
                    f"{parent}->{child}"
                )
    return None


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

        old_problem = old_lineage_continuity_problem(
            repo,
            boundary,
            old_tip,
            incarnation,
            old_action.action_id,
            old_action.raw,
        )
        if old_problem is not None:
            verdict = Verdict(
                "finding",
                "old-side discontinuous incarnation",
                "not-applicable",
                0,
                "The old tip has the same final bytes as the common action, but its "
                f"history does not prove continuous identity: {old_problem}.",
            )
            return with_metrics(repo, verdict)

        old_only = repo.revisions("--topo-order", old_tip, "--not", boundary)
        candidate = repo.revisions("--topo-order", new_head, "--not", old_tip)
        candidate_set = set(candidate)
        origin_revisions = [boundary, *old_only, *candidate]
        sibling_problem = sibling_incarnation_problem(
            repo,
            candidate,
            boundary,
            incarnation,
            old_action.action_id,
        )
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
            validate_edge(
                repo,
                edge,
                incarnation,
                sibling_problem,
                origin_revisions,
            )
            if edge.valid:
                absence_problem = post_witness_absence_problem(
                    repo,
                    edge,
                    new_head,
                    incarnation,
                    old_action.action_id,
                )
                if absence_problem is not None:
                    edge.valid = False
                    edge.problem = absence_problem

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

        group_valid_merge_deletion_components(repo, edges)
        effective = [
            edge
            for edge in edges
            if not edge.supplied_by_sibling
            and not edge.grouped_in_child_component
        ]
        new_snapshot = repo.snapshot(new_head)
        new_matches = occurrences(new_snapshot, incarnation)
        new_same_id = same_id(new_snapshot, old_action.action_id)

        if sibling_problem is not None:
            verdict = Verdict(
                "finding",
                "ambiguous candidate same-ID provenance",
                f"invalid: {sibling_problem}",
                len(effective),
                "The candidate graph contains a same-ID state that cannot be proved "
                f"to share the inherited occurrence: {sibling_problem}.",
                edges,
            )
            return with_metrics(repo, verdict)
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
        component_size = 1 + sum(
            edge.grouped_in_child_component and edge.child == witness.child
            for edge in edges
        )
        if component_size > 1:
            human_reason = (
                "The old branch left the action unchanged, and one merge-authored "
                f"deletion component contains {component_size} independently validated "
                "parent edges with a committed claim plus changed resolution evidence."
            )
        else:
            human_reason = (
                "The old branch left the action unchanged, and exactly one "
                "candidate-side deletion edge carries a committed claim plus changed "
                "resolution evidence."
            )
        verdict = Verdict(
            "exempt",
            "candidate-side validated resolution",
            "valid",
            1,
            human_reason,
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


def scenario_changed_action(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit(
        "old replaces action identity",
        {
            DEFAULT_PATH: action_text(
                action_id="Q-branch", payload="branch-authored replacement"
            )
        },
    )
    repo.switch_new("new", common)
    repo.commit("claim original", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "resolve original",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("new feature", {"feature.txt": "new\n"})
    return make_record(
        "S4-changed-action",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_mixed(root: Path) -> dict[str, object]:
    q1 = DEFAULT_PATH
    q2 = "message-queue/needs-agent/requests/non-blocking-second.md"
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit(
        "old adds second action",
        {q2: action_text(action_id="Q2", payload="branch obligation")},
    )
    repo.switch_new("new", common)
    repo.commit("claim first", {q1: action_text(status="in-repair")})
    new_base = repo.commit(
        "resolve first",
        {q1: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("new feature", {"feature.txt": "new\n"})
    first = classify(repo, old, new, q1)
    second = classify(repo, old, new, q2)
    combined = Verdict(
        "finding",
        "mixed inherited resolution and old-side loss",
        f"Q1={first.evidence_verdict}; Q2={second.evidence_verdict}",
        first.witness_cardinality + second.witness_cardinality,
        "Q1 is justified by exactly one valid candidate-side resolution, while Q2 "
        "was introduced only by the old task lineage and remains a blocking loss.",
        first.edges + second.edges,
        first.git_processes + second.git_processes,
        first.tree_reads + second.tree_reads,
    )
    record = make_record(
        "S5-mixed-actions",
        {"C": common, "O": old, "M": new_base, "N": new},
        combined,
        "finding",
    )
    record["path_results"] = {
        q1: first.result,
        q2: second.result,
    }
    return record


def scenario_unrelated_queue(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"old.txt": "old\n"})
    repo.switch_new("new", common)
    new_base = repo.commit("base feature", {"base.txt": "base\n"})
    new = repo.commit("replay old feature", {"old.txt": "old\n"})
    return make_record(
        "S7-unrelated-restack",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )


def scenario_fast_forward(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    old = repo.commit("old feature", {"old.txt": "old\n"})
    new = repo.commit("ordinary extension", {"next.txt": "next\n"})
    return make_record(
        "S8-fast-forward-replacement",
        {"C": common, "O": old, "M": old, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )


def scenario_missing_tip(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    repo.commit("old feature", {"old.txt": "old\n"})
    missing = "f" * 40
    repo.switch_new("new", common)
    new_base = repo.commit("base feature", {"base.txt": "base\n"})
    new = repo.commit("new head", {"head.txt": "head\n"})
    return make_record(
        "S9-missing-tip",
        {"C": common, "O": missing, "M": new_base, "N": new},
        classify(repo, missing, new, DEFAULT_PATH),
        "fail-closed",
    )


def scenario_unrelated_tip(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    old = repo.commit("old feature", {"old.txt": "old\n"})
    repo.run("switch", "-q", "--orphan", "unrelated")
    # Git 2.55 already empties the index and worktree for switch --orphan;
    # older versions may leave tracked paths staged for removal.
    repo.run("rm", "-r", "-q", ".", check=False)
    new_base = repo.commit(
        "unrelated root",
        {
            "README.md": "unrelated\n",
            EVIDENCE_PATH: "unrelated evidence\n",
        },
    )
    new = repo.commit("unrelated head", {"head.txt": "head\n"})
    return make_record(
        "S9-unrelated-tip",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "fail-closed",
    )


def scenario_non_commit_tip(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.write("loose-blob.txt", "this object is not a commit\n")
    blob = repo.run("hash-object", "-w", "loose-blob.txt").stdout.decode().strip()
    repo.switch_new("new", common)
    new_base = repo.commit("base feature", {"base.txt": "base\n"})
    new = repo.commit("new head", {"head.txt": "head\n"})
    return make_record(
        "S9-non-commit-tip",
        {"C": common, "O": blob, "M": new_base, "N": new},
        classify(repo, blob, new, DEFAULT_PATH),
        "fail-closed",
    )


def scenario_pre_v1(root: Path) -> dict[str, object]:
    repo, common = base_repo(root, live=False)
    repo.switch_new("old", common)
    old = repo.commit(
        "pre-v1 old action",
        {DEFAULT_PATH: action_text(), "old.txt": "old\n"},
    )
    repo.switch_new("new", common)
    new_base = repo.commit("activate v1", {"docs/queue-v1.txt": "active\n"})
    new = repo.commit("new head", {"head.txt": "head\n"})
    return make_record(
        "S10-pre-v1-old-tip-action",
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


def scenario_rename_then_delete(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    claimed = action_text(status="in-repair")
    repo.commit("claim", {DEFAULT_PATH: claimed})
    repo.commit("rename claimed action", {DEFAULT_PATH: None, RENAMED_PATH: claimed})
    new_base = repo.commit(
        "resolve renamed action",
        {RENAMED_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    return make_record(
        "S11-rename-then-delete",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )


def scenario_ambiguous_rename(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    new_base = repo.commit(
        "duplicate action during rename",
        {RENAMED_PATH: action_text()},
    )
    new = repo.commit("new head", {"head.txt": "head\n"})
    return make_record(
        "S11-ambiguous-rename",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
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


def scenario_merge_only_creation(root: Path) -> dict[str, object]:
    repo, common = base_repo(root, live=False)
    repo.switch_new("old-left", common)
    repo.commit("old left", {"left.txt": "left\n"})
    repo.switch_new("old-right", common)
    repo.commit("old right", {"right.txt": "right\n"})
    repo.switch("old-left")
    old = repo.merge_commit(
        "old-right",
        "merge creates action",
        {DEFAULT_PATH: action_text()},
    )
    repo.switch_new("new", common)
    new_base = repo.commit("new base", {"base.txt": "base\n"})
    new = repo.commit("new head", {"head.txt": "head\n"})
    return make_record(
        "A1-merge-commit-only-action-creation",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
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
        "no-finding",
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


def scenario_recreated_incarnation(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    repo.commit("first claim", {DEFAULT_PATH: action_text(status="in-repair")})
    repo.commit(
        "first resolution",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    repo.commit("recreate same bytes", {DEFAULT_PATH: action_text()})
    repo.commit("second claim", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "second resolution",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v2\n"},
    )
    new = repo.commit("new head", {"head.txt": "head\n"})
    return make_record(
        "A3-delete-recreate-delete",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_old_recreated_same_bytes(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    repo.commit("old deletes action", {DEFAULT_PATH: None})
    repo.commit("old recreates identical action", {DEFAULT_PATH: action_text()})
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    repo.commit("candidate claim", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "candidate resolution",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    return make_record(
        "A6-old-delete-recreate-identical",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_old_mutates_then_reverts(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    repo.commit(
        "old mutates identity",
        {DEFAULT_PATH: action_text(payload="temporary replacement")},
    )
    repo.commit("old restores bytes", {DEFAULT_PATH: action_text()})
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    repo.commit("candidate claim", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "candidate resolution",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    return make_record(
        "A7-old-identity-mutation-reverted",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_old_duplicate_then_collapses(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    repo.commit("old duplicates during rename", {RENAMED_PATH: action_text()})
    repo.commit("old removes duplicate", {RENAMED_PATH: None})
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    repo.commit("candidate claim", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "candidate resolution",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    return make_record(
        "A8-old-ambiguous-rename-collapsed",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )


def scenario_cross_boundary_claim_reuse(root: Path) -> dict[str, object]:
    repo, first_open = base_repo(root)
    first_claim = repo.commit(
        "claim first occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.commit("delete first occurrence", {DEFAULT_PATH: None})
    common = repo.commit(
        "recreate preclaimed occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    new_base = repo.commit(
        "delete second occurrence without its own claim",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    record = make_record(
        "A9-cross-boundary-claim-reuse",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )
    record["first_occurrence_open"] = first_open
    record["first_occurrence_claim"] = first_claim
    return record


def scenario_recreated_occurrence_own_claim(root: Path) -> dict[str, object]:
    repo, _first_open = base_repo(root)
    repo.commit(
        "claim first occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.commit("delete first occurrence", {DEFAULT_PATH: None})
    common = repo.commit(
        "recreate open occurrence",
        {DEFAULT_PATH: action_text()},
    )
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    own_claim = repo.commit(
        "claim second occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    new_base = repo.commit(
        "delete second occurrence after its own claim",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    record = make_record(
        "A10-recreated-occurrence-own-claim",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )
    record["current_occurrence_claim"] = own_claim
    return record


def scenario_ambiguous_merge_occurrence(root: Path) -> dict[str, object]:
    repo, first_open = base_repo(root)
    claimed = repo.commit(
        "claim shared occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.switch_new("parent-one", claimed)
    parent_one = repo.commit("carry original occurrence", {"one.txt": "one\n"})
    repo.switch_new("parent-two", claimed)
    repo.commit("delete on second parent", {DEFAULT_PATH: None})
    parent_two = repo.commit(
        "recreate preclaimed on second parent",
        {DEFAULT_PATH: action_text(status="in-repair"), "two.txt": "two\n"},
    )
    repo.switch("parent-one")
    common = repo.merge_commit(
        "parent-two",
        "merge ambiguous occurrence",
        {},
    )
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    new_base = repo.commit(
        "delete ambiguous merged occurrence",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    record = make_record(
        "A11-ambiguous-merge-occurrence",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )
    record.update({
        "first_open": first_open,
        "shared_claim": claimed,
        "merge_parent_one": parent_one,
        "merge_parent_two": parent_two,
    })
    return record


def scenario_shared_occurrence_merge(root: Path) -> dict[str, object]:
    repo, _first_open = base_repo(root)
    claimed = repo.commit(
        "claim shared occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.switch_new("parent-one", claimed)
    parent_one = repo.commit("carry on first parent", {"one.txt": "one\n"})
    repo.switch_new("parent-two", claimed)
    parent_two = repo.commit("carry on second parent", {"two.txt": "two\n"})
    repo.switch("parent-one")
    common = repo.merge_commit(
        "parent-two",
        "merge shared occurrence",
        {},
    )
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    new_base = repo.commit(
        "delete continuously shared occurrence",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    record = make_record(
        "A12-shared-occurrence-merge",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )
    record.update({
        "shared_claim": claimed,
        "merge_parent_one": parent_one,
        "merge_parent_two": parent_two,
    })
    return record


def scenario_post_witness_merge_reintroduction(root: Path) -> dict[str, object]:
    repo, _first_open = base_repo(root)
    common = repo.commit(
        "claim occurrence before fork",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("resolved", common)
    first_deletion = repo.commit(
        "first deletion",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    repo.switch_new("carrier", common)
    carrier = repo.commit("carry occurrence", {"carrier.txt": "carry\n"})
    repo.switch("resolved")
    reintroduction = repo.merge_commit(
        "carrier",
        "merge reintroduces occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    new_base = repo.commit(
        "final deletion",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v2\n"},
    )
    new = repo.commit("replay feature", {"feature.txt": "old\n"})
    record = make_record(
        "A13-post-witness-merge-reintroduction",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )
    if not any(
        edge["problem"].startswith("action reappears after the deletion witness")
        for edge in record["edges"]
    ):
        raise AssertionError("A13 did not collect post-witness absence continuity")
    record.update({
        "first_deletion": first_deletion,
        "carrier": carrier,
        "reintroduction": reintroduction,
    })
    return record


def scenario_conflicting_sibling_incarnation(root: Path) -> dict[str, object]:
    repo, root_before_common = base_repo(root, live=False)
    common = repo.commit(
        "common adds inherited action",
        {DEFAULT_PATH: action_text(payload="inherited A")},
    )
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"old.txt": "old\n"})

    repo.switch_new("valid-parent", common)
    valid_parent = repo.commit(
        "claim inherited action",
        {
            DEFAULT_PATH: action_text(
                status="in-repair",
                payload="inherited A",
            )
        },
    )

    repo.switch_new("foreign-parent", root_before_common)
    foreign_parent = repo.commit(
        "independently add conflicting same-ID action",
        {
            RENAMED_PATH: action_text(
                status="in-repair",
                payload="conflicting B",
            )
        },
    )

    repo.switch("valid-parent")
    merged = repo.merge_commit(
        "foreign-parent",
        "merge deletes inherited and conflicting actions",
        {
            DEFAULT_PATH: None,
            RENAMED_PATH: None,
            EVIDENCE_PATH: "evidence v1\n",
        },
    )
    new = repo.commit("new head", {"new.txt": "new\n"})
    record = make_record(
        "A14-conflicting-sibling-incarnation",
        {"C": common, "O": old, "M": merged, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )
    record.update({
        "root_before_C": root_before_common,
        "valid_parent": valid_parent,
        "foreign_parent": foreign_parent,
    })
    return record


def scenario_disconnected_identical_origins(root: Path) -> dict[str, object]:
    repo, root_without_action = base_repo(root, live=False)
    repo.switch_new("creator-a", root_without_action)
    creator_a = repo.commit(
        "independently create first identical action",
        {DEFAULT_PATH: action_text()},
    )
    repo.switch_new("creator-b", root_without_action)
    creator_b = repo.commit(
        "independently create second identical action",
        {DEFAULT_PATH: action_text()},
    )
    repo.switch("creator-a")
    common = repo.merge_commit(
        "creator-b",
        "collapse disconnected identical origins",
        {},
    )
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"old.txt": "old\n"})
    repo.switch_new("new", common)
    claim = repo.commit(
        "claim ambiguous boundary action",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    deletion = repo.commit(
        "delete after claim",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("new head", {"new.txt": "new\n"})
    record = make_record(
        "A15-disconnected-identical-origins-at-boundary",
        {"C": common, "O": old, "M": deletion, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )
    record.update({
        "root_without_action": root_without_action,
        "creator_a": creator_a,
        "creator_b": creator_b,
        "candidate_claim": claim,
    })
    return record


def scenario_shared_origin_boundary_merge(root: Path) -> dict[str, object]:
    repo, shared_origin = base_repo(root)
    repo.switch_new("carrier-a", shared_origin)
    carrier_a = repo.commit("carry shared occurrence A", {"a.txt": "a\n"})
    repo.switch_new("carrier-b", shared_origin)
    carrier_b = repo.commit("carry shared occurrence B", {"b.txt": "b\n"})
    repo.switch("carrier-a")
    common = repo.merge_commit(
        "carrier-b",
        "merge shared-origin occurrence",
        {},
    )
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"old.txt": "old\n"})
    repo.switch_new("new", common)
    claim = repo.commit(
        "claim shared-origin action",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    deletion = repo.commit(
        "delete shared-origin action",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("new head", {"new.txt": "new\n"})
    record = make_record(
        "A16-shared-origin-boundary-merge",
        {"C": common, "O": old, "M": deletion, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )
    record.update({
        "shared_origin": shared_origin,
        "carrier_a": carrier_a,
        "carrier_b": carrier_b,
        "candidate_claim": claim,
    })
    return record


def scenario_three_parent_valid_deletion(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    claim = repo.commit(
        "claim shared occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.switch_new("old", claim)
    old = repo.commit("old feature", {"old.txt": "old\n"})
    parents = []
    for branch in ("p1", "p2", "p3"):
        repo.switch_new(branch, claim)
        parents.append(
            repo.commit(
                f"carry shared occurrence on {branch}",
                {f"{branch}.txt": f"{branch}\n"},
            )
        )
    repo.switch("p1")
    tree_source = repo.commit(
        "prepare absent result tree",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    tree = repo.run("show", "-s", "--format=%T", tree_source).stdout.decode().strip()
    merged = repo.commit_tree(
        tree,
        tuple(parents),
        "three-parent merge deletes shared occurrence",
    )
    repo.run("update-ref", "refs/heads/merged", merged)
    repo.switch("merged")
    new = repo.commit("new head", {"new.txt": "new\n"})
    record = make_record(
        "A17-three-parent-valid-deletion-component",
        {"C": common, "O": old, "M": merged, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "no-finding",
    )
    record.update({
        "common_claim": claim,
        "merge_parents": parents,
        "grouped_edges": sum(
            edge["grouped_in_child_component"] for edge in record["edges"]
        ),
    })
    return record


def scenario_three_parent_invalid_parent(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    claim = repo.commit(
        "claim shared occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.switch_new("old", claim)
    old = repo.commit("old feature", {"old.txt": "old\n"})
    parents = []
    for branch in ("p1", "p2"):
        repo.switch_new(branch, claim)
        parents.append(
            repo.commit(
                f"carry claimed occurrence on {branch}",
                {f"{branch}.txt": f"{branch}\n"},
            )
        )
    repo.switch_new("p3", claim)
    invalid_parent = repo.commit(
        "reopen occurrence on invalid parent",
        {DEFAULT_PATH: action_text(status="open"), "p3.txt": "p3\n"},
    )
    parents.append(invalid_parent)
    repo.switch("p1")
    tree_source = repo.commit(
        "prepare absent result tree",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    tree = repo.run("show", "-s", "--format=%T", tree_source).stdout.decode().strip()
    merged = repo.commit_tree(
        tree,
        tuple(parents),
        "three-parent merge includes invalid deletion edge",
    )
    repo.run("update-ref", "refs/heads/merged", merged)
    repo.switch("merged")
    new = repo.commit("new head", {"new.txt": "new\n"})
    record = make_record(
        "A18-three-parent-invalid-parent",
        {"C": common, "O": old, "M": merged, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )
    record.update({
        "common_claim": claim,
        "merge_parents": parents,
        "invalid_parent": invalid_parent,
    })
    return record


def scenario_three_parent_disconnected_parent(root: Path) -> dict[str, object]:
    repo, root_without_action = base_repo(root, live=False)
    common = repo.commit("common creates action", {DEFAULT_PATH: action_text()})
    claim = repo.commit(
        "claim common occurrence",
        {DEFAULT_PATH: action_text(status="in-repair")},
    )
    repo.switch_new("old", claim)
    old = repo.commit("old feature", {"old.txt": "old\n"})
    parents = []
    for branch in ("p1", "p2"):
        repo.switch_new(branch, claim)
        parents.append(
            repo.commit(
                f"carry common occurrence on {branch}",
                {f"{branch}.txt": f"{branch}\n"},
            )
        )
    repo.switch_new("p3", root_without_action)
    disconnected_parent = repo.commit(
        "independently create byte-identical claimed action",
        {DEFAULT_PATH: action_text(status="in-repair"), "p3.txt": "p3\n"},
    )
    parents.append(disconnected_parent)
    repo.switch("p1")
    tree_source = repo.commit(
        "prepare absent result tree",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    tree = repo.run("show", "-s", "--format=%T", tree_source).stdout.decode().strip()
    merged = repo.commit_tree(
        tree,
        tuple(parents),
        "three-parent merge includes disconnected occurrence",
    )
    repo.run("update-ref", "refs/heads/merged", merged)
    repo.switch("merged")
    new = repo.commit("new head", {"new.txt": "new\n"})
    record = make_record(
        "A19-three-parent-disconnected-parent",
        {"C": common, "O": old, "M": merged, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "finding",
    )
    record.update({
        "root_without_action": root_without_action,
        "common_claim": claim,
        "merge_parents": parents,
        "disconnected_parent": disconnected_parent,
    })
    return record


def scenario_multiple_bases(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("a", common)
    a1 = repo.commit("a1", {"a.txt": "a\n"})
    repo.switch_new("b", common)
    b1 = repo.commit("b1", {"b.txt": "b\n"})
    tree_a = repo.run("show", "-s", "--format=%T", a1).stdout.decode().strip()
    tree_b = repo.run("show", "-s", "--format=%T", b1).stdout.decode().strip()
    a2 = repo.commit_tree(tree_a, (a1, b1), "synthetic merge a")
    b2 = repo.commit_tree(tree_b, (b1, a1), "synthetic merge b")
    repo.run("update-ref", "refs/heads/criss-old", a2)
    repo.run("update-ref", "refs/heads/criss-new", b2)
    repo.switch("criss-old")
    old = repo.commit("old criss-cross head", {"old.txt": "old\n"})
    repo.switch("criss-new")
    new_base = b2
    new = repo.commit("new criss-cross head", {"new.txt": "new\n"})
    bases = repo.merge_bases(old, new)
    if len(bases) != 2:
        raise AssertionError(f"fixture expected two merge bases, got {bases}")
    return make_record(
        "A4-criss-cross-multiple-bases",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(repo, old, new, DEFAULT_PATH),
        "fail-closed",
    )


def scenario_shallow(root: Path) -> dict[str, object]:
    source = root / "source"
    repo, common = base_repo(source)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    repo.commit("claim", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "resolve",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("new head", {"head.txt": "head\n"})

    clone_path = root / "shallow"
    subprocess.run(
        [
            "git",
            "clone",
            "-q",
            "--no-local",
            "--depth=1",
            "--branch",
            "new",
            source.resolve().as_uri(),
            str(clone_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    shallow = GitRepo(clone_path, initialize=False)
    if shallow.run("cat-file", "-e", f"{old}^{{commit}}", check=False).returncode:
        shallow.run(
            "fetch",
            "-q",
            "--depth=1",
            "origin",
            "refs/heads/old:refs/remotes/origin/old",
        )
    shallow.validate_commit(old)
    shallow.validate_commit(new)
    return make_record(
        "A5-shallow-both-tips-present",
        {"C": common, "O": old, "M": new_base, "N": new},
        classify(shallow, old, new, DEFAULT_PATH),
        "fail-closed",
    )


def scenario_long_history(root: Path) -> dict[str, object]:
    repo, common = base_repo(root)
    repo.switch_new("old", common)
    old = repo.commit("old feature", {"feature.txt": "old\n"})
    repo.switch_new("new", common)
    for index in range(128):
        repo.commit(
            f"unrelated history {index:03d}",
            {f"history/{index:03d}.txt": f"{index}\n"},
        )
    repo.commit("claim", {DEFAULT_PATH: action_text(status="in-repair")})
    new_base = repo.commit(
        "resolve",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    new = repo.commit("new head", {"head.txt": "head\n"})
    started = time.perf_counter()
    verdict = classify(repo, old, new, DEFAULT_PATH)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    record = make_record(
        "P1-long-history-cost",
        {"C": common, "O": old, "M": new_base, "N": new},
        verdict,
        "no-finding",
    )
    record["history_commits"] = 128
    record["elapsed_ms"] = elapsed_ms
    return record


INITIAL_SCENARIOS = (
    scenario_valid,
    scenario_invalid,
    scenario_old_loss,
    scenario_changed_action,
    scenario_mixed,
    scenario_same_path,
    scenario_unrelated_queue,
    scenario_fast_forward,
    scenario_missing_tip,
    scenario_non_commit_tip,
    scenario_unrelated_tip,
    scenario_pre_v1,
    scenario_rename_carry,
    scenario_rename_then_delete,
    scenario_ambiguous_rename,
    scenario_merge_base,
    scenario_merge_only_creation,
    scenario_merge_only_deletion,
    scenario_competing_edges,
    scenario_recreated_incarnation,
    scenario_old_recreated_same_bytes,
    scenario_old_mutates_then_reverts,
    scenario_old_duplicate_then_collapses,
    scenario_cross_boundary_claim_reuse,
    scenario_recreated_occurrence_own_claim,
    scenario_ambiguous_merge_occurrence,
    scenario_shared_occurrence_merge,
    scenario_post_witness_merge_reintroduction,
    scenario_conflicting_sibling_incarnation,
    scenario_disconnected_identical_origins,
    scenario_shared_origin_boundary_merge,
    scenario_three_parent_valid_deletion,
    scenario_three_parent_invalid_parent,
    scenario_three_parent_disconnected_parent,
    scenario_multiple_bases,
    scenario_shallow,
    scenario_long_history,
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
