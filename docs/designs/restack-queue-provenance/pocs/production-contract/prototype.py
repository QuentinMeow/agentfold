#!/usr/bin/env python3
"""Real-Git POC for the C-rooted production restack contract.

This executable imports AgentFold's current queue identity and deletion
validator.  It changes no production behavior.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Iterable


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[5]
RECONCILE_PATH = REPOSITORY / "automation/reconcile/reconcile.py"
REAL_RUN = subprocess.run
REAL_POPEN = subprocess.Popen


def load_reconciler():
    spec = importlib.util.spec_from_file_location(
        "production_contract_reconcile", RECONCILE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {RECONCILE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RECONCILE = load_reconciler()


class Unreadable(RuntimeError):
    """Required immutable Git evidence could not be read."""


@dataclasses.dataclass
class Metrics:
    git_processes: int = 0
    graph_enumerations: int = 0
    graph_commits: int = 0
    graph_parent_edges: int = 0
    batch_processes: int = 0
    object_reads: int = 0
    object_cache_hits: int = 0
    queue_snapshots_requested: int = 0
    queue_subtree_reads: int = 0
    snapshot_cache_hits: int = 0
    identity_calls: int = 0
    authority_calls: int = 0
    support_certificate_calls: int = 0
    support_adoption_checks: int = 0
    support_paths_checked: int = 0
    mutation_calls: int = 0
    per_action_history_walks: int = 0
    carry_proof_nodes: int = 0
    carry_proof_edges: int = 0

    def as_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ActionState:
    path: str
    text: str
    blob_oid: str


@dataclasses.dataclass
class Fixture:
    scenario: str
    repo: "GitRepository"
    expected_C: str
    O: str
    candidate_landmark: str
    N: str
    expected: str
    details: dict = dataclasses.field(default_factory=dict)
    budget_limit: int | None = None


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
    reopen_outside_c_boundary_ancestry: bool = False


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


def is_git_command(command) -> bool:
    return bool(
        isinstance(command, (tuple, list))
        and command
        and Path(str(command[0])).name in {"git", "git.exe"}
    )


@contextlib.contextmanager
def count_production_git(metrics: Metrics):
    """Count each Git child spawned by imported production helpers once."""

    def counted_popen(command, *args, **kwargs):
        if is_git_command(command):
            metrics.git_processes += 1
        return REAL_POPEN(command, *args, **kwargs)

    original_popen = subprocess.Popen
    subprocess.Popen = counted_popen
    try:
        yield
    finally:
        subprocess.Popen = original_popen


@contextlib.contextmanager
def reconciler_repository(root: Path):
    names = {
        "REPO": root,
        "QUEUE": root / "message-queue",
        "TASKS": root / "tasks",
        "CONVERSATIONS": root / "history/conversations",
        "MEMORY": root / "memory",
        "CHANGE_RANGE": None,
        "DISPLACED_TIP": None,
    }
    saved = {name: getattr(RECONCILE, name) for name in names}
    for name, value in names.items():
        setattr(RECONCILE, name, value)
    RECONCILE.scope_immutable_git_caches()
    try:
        yield
    finally:
        RECONCILE.close_git_cat_file()
        for name, value in saved.items():
            setattr(RECONCILE, name, value)
        RECONCILE.scope_immutable_git_caches()


class GitRepository:
    """Deterministic disposable real-Git fixture builder."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.clock = 0
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
            env=env,
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


def run_git(root: Path, metrics: Metrics, *arguments, check=True):
    # count_production_git observes this subprocess at the Popen boundary.
    result = REAL_RUN(
        ["git", *arguments],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        raise Unreadable(
            result.stderr.strip()
            or f"git {' '.join(arguments)} failed ({result.returncode})"
        )
    return result


class ObjectDatabase:
    """One cat-file process plus immutable object/tree/snapshot caches."""

    def __init__(self, root: Path, metrics: Metrics):
        self.root = root
        self.metrics = metrics
        self.process = REAL_POPEN(
            ["git", "--no-replace-objects", "cat-file", "--batch"],
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        metrics.git_processes += 1
        metrics.batch_processes += 1
        self.objects: dict[str, tuple[str, bytes]] = {}
        self.trees: dict[str, dict[str, tuple[str, str]]] = {}
        self.flat_trees: dict[str, dict[str, tuple[str, str]]] = {}
        self.snapshots: dict[
            str | None, dict[tuple, tuple[ActionState, ...]]
        ] = {}

    def close(self):
        if self.process.stdin:
            self.process.stdin.close()
        if self.process.stdout:
            self.process.stdout.close()
        self.process.wait(timeout=5)

    def read(self, oid: str) -> tuple[str, bytes]:
        if oid in self.objects:
            self.metrics.object_cache_hits += 1
            return self.objects[oid]
        self.metrics.object_reads += 1
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.write(oid.encode("ascii") + b"\n")
        self.process.stdin.flush()
        header = self.process.stdout.readline().rstrip(b"\n").split()
        if len(header) == 2 and header[1] == b"missing":
            raise Unreadable(f"required Git object {oid} is missing")
        if len(header) != 3:
            raise Unreadable(f"malformed cat-file frame for {oid}")
        try:
            size = int(header[2])
        except ValueError as error:
            raise Unreadable(f"malformed cat-file size for {oid}") from error
        payload = self.process.stdout.read(size)
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
            self.metrics.object_cache_hits += 1
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
            mode = payload[offset:space].decode("ascii")
            name = payload[space + 1:nul].decode(
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
            self.metrics.object_cache_hits += 1
            return self.flat_trees[root]
        flattened: dict[str, tuple[str, str]] = {}

        def walk(tree_oid: str, prefix: str):
            for name, (mode, child) in sorted(
                self.tree_entries(tree_oid).items()
            ):
                path = f"{prefix}/{name}" if prefix else name
                if mode in {"40000", "040000"}:
                    walk(child, path)
                else:
                    flattened[path] = (mode, child)

        walk(root, "")
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
        self.metrics.queue_snapshots_requested += 1
        queue_tree = self.queue_tree(commit)
        if queue_tree in self.snapshots:
            self.metrics.snapshot_cache_hits += 1
            return self.snapshots[queue_tree]
        self.metrics.queue_subtree_reads += 1
        by_identity: dict[tuple, list[ActionState]] = {}

        def walk(tree_oid: str, prefix: str):
            for name, (mode, child) in sorted(
                self.tree_entries(tree_oid).items()
            ):
                path = f"{prefix}/{name}"
                if mode in {"40000", "040000"}:
                    walk(child, path)
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
                    text = payload.decode("utf-8")
                except UnicodeDecodeError as error:
                    raise Unreadable(
                        f"queue item {path} is not UTF-8"
                    ) from error
                self.metrics.identity_calls += 1
                identity = RECONCILE.queue_action_identity(path, text)
                by_identity.setdefault(identity, []).append(
                    ActionState(path, text, child)
                )

        if queue_tree is not None:
            walk(queue_tree, "message-queue")
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
        root: Path,
        O: str,
        N: str,
        objects: ObjectDatabase,
        metrics: Metrics,
        *,
        reopen_outside_c_boundary_ancestry: bool = False,
    ):
        self.root = root
        self.O = O
        self.N = N
        self.objects = objects
        self.metrics = metrics
        shallow = run_git(
            root, metrics, "rev-parse", "--is-shallow-repository"
        ).stdout.strip()
        if shallow == "true":
            raise Unreadable("required post-C history is shallow")
        for label, oid in (("O", O), ("N", N)):
            try:
                objects.commit_tree(oid)
            except Unreadable as error:
                raise Unreadable(f"{label}: {error}") from error
        bases = run_git(
            root,
            metrics,
            "--no-replace-objects",
            "merge-base",
            "--all",
            O,
            N,
            check=False,
        )
        if bases.returncode:
            raise Unreadable(
                bases.stderr.strip() or "could not determine the merge base"
            )
        merge_bases = tuple(line for line in bases.stdout.splitlines() if line)
        if len(merge_bases) != 1:
            raise Unreadable(
                f"expected exactly one merge base C; found {len(merge_bases)}"
            )
        self.C = merge_bases[0]
        try:
            objects.commit_tree(self.C)
        except Unreadable as error:
            raise Unreadable(f"derived C: {error}") from error
        metrics.graph_enumerations += 1
        listing_arguments = [
            "--no-replace-objects",
            "rev-list",
            "--parents",
            "--topo-order",
            "--reverse",
        ]
        if not reopen_outside_c_boundary_ancestry:
            listing_arguments.append("--ancestry-path")
        listing = run_git(
            root, metrics, *listing_arguments, O, N, f"^{self.C}"
        )
        self.order = [self.C]
        self.parents: dict[str, tuple[str, ...]] = {self.C: ()}
        for line in listing.stdout.splitlines():
            fields = line.split()
            if not fields:
                continue
            commit, raw_parents = fields[0], tuple(fields[1:])
            self.order.append(commit)
            self.parents[commit] = raw_parents
        self.order = list(dict.fromkeys(self.order))
        metrics.graph_commits = len(self.order)
        metrics.graph_parent_edges = sum(
            len(value) for value in self.parents.values()
        )
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


class Classifier:
    """In-memory provenance over one enumerated graph and cached snapshots."""

    def __init__(self, fixture: Fixture, damage: Damage | None = None):
        self.fixture = fixture
        self.damage = damage or Damage()
        self.metrics = Metrics()
        self.objects: ObjectDatabase | None = None
        self.graph: Graph | None = None
        self.carry_proof_cache: dict[tuple[tuple, str], dict] = {}

    def budget_overflows(self) -> list[tuple[str, int]]:
        limit = self.fixture.budget_limit
        if limit is None or self.damage.unmetered_cone_work:
            return []
        return sorted(
            (name, value)
            for name, value in self.metrics.as_dict().items()
            if value > limit
        )

    def budget_result(self, base: dict) -> dict | None:
        overflows = self.budget_overflows()
        if not overflows:
            return None
        limit = self.fixture.budget_limit
        reason = "; ".join(
            f"{name}={value}>{limit}" for name, value in overflows
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
            visiting.add(child)
            self.metrics.carry_proof_nodes += 1
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
                self.metrics.carry_proof_edges += 1
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
    def canonical_digest(domain: str, value: dict) -> str:
        payload = json.dumps(
            {"domain": domain, "value": value},
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
        declared = sorted(set(RECONCILE.context_path_candidates(state.text)))
        obligations: list[dict] = [
            {
                "kind": "production-deletion-postcondition",
                "authority_parent": parent,
                "authority_child": child,
            }
        ]
        obligations.extend(
            {"kind": "declared-path-anchor", "path": path}
            for path in declared
            if path != state.path
        )
        if actor == "needs-agent" and leaf == "requests":
            if fields.get("Request kind", "").strip() == "task-pickup":
                task_paths = [
                    path for path in declared if path.startswith("tasks/")
                ]
                if len(task_paths) != 1:
                    return obligations, "task pickup has no unique task path"
                obligations.append(
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
            obligations.append({"kind": "agent-evidence-lineage"})
            return obligations, None
        if actor == "needs-agent" and leaf == "retries":
            item = self.fixture.repo.root / state.path
            if not RECONCILE.reconciler_owned_retry(item, state.text):
                return obligations, "retry is not a production-owned retry"
            check = fields.get("Check", "").strip()
            if check not in RECONCILE.CHECKS:
                return obligations, "retry names an unknown checker"
            obligations.append(
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
            obligations.append({"kind": "terminal-human-response"})
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
            obligations.append(
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
        self.metrics.support_certificate_calls += 1
        before = self.objects.flat_tree(parent)
        after = self.objects.flat_tree(child)
        changed = sorted(
            path
            for path in set(before).union(after)
            if before.get(path) != after.get(path) and path != state.path
        )
        referenced = sorted(
            path
            for path in set(RECONCILE.context_path_candidates(state.text))
            if path != state.path
        )
        support_paths = sorted(set(changed).union(referenced))
        raw_delta = [
            {
                "path": path,
                "before": self.objects.path_entry(parent, path),
                "after": self.objects.path_entry(child, path),
            }
            for path in changed
        ]
        anchors = [
            {
                "path": path,
                "entry": self.objects.path_entry(child, path),
                "changed_on_authority_edge": path in changed,
            }
            for path in support_paths
        ]
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
        self.metrics.authority_calls += 1
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
        self.metrics.support_adoption_checks += 1
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
        paths = []
        for obligation in certificate["obligations"]:
            if obligation["kind"] == "task-pickup-postcondition":
                try:
                    incarnations = RECONCILE.task_incarnations_at(
                        revision, obligation["task_id"]
                    )
                except (
                    RECONCILE.GitSnapshotError,
                    OSError,
                    ValueError,
                    UnicodeError,
                ) as error:
                    raise Unreadable(
                        "pickup dynamic support projection could not read "
                        f"{revision}: {error}"
                    ) from error
                paths.extend(incarnations)
                assert self.objects is not None
                tree_paths = self.objects.flat_tree(revision)
                for task_path in incarnations:
                    task_dir = Path(task_path).parent
                    paths.extend(
                        path
                        for path in tree_paths
                        if Path(path).parent == task_dir
                        and Path(path).name
                        in RECONCILE.TASK_ARTIFACT_NAMES
                    )
            elif obligation["kind"] == "generated-retry-clear":
                subject = obligation["subject"].strip("`")
                if RECONCILE.valid_queue_item_path(subject) or (
                    subject
                    and not subject.startswith("/")
                    and ".." not in Path(subject).parts
                ):
                    paths.append(subject)
        return sorted(set(paths))

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
            fixed_support_paths = [
                anchor["path"] for anchor in certificate["support_paths"]
            ]
            support_paths = sorted(
                set(fixed_support_paths).union(
                    path
                    for revision in [*source_parents, child]
                    for path in self.dynamic_support_paths(
                        certificate, revision
                    )
                )
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
            self.metrics.support_paths_checked += len(support_paths) * (
                len(source_parents) + 1
            )
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

    def mutation_edge(
        self,
        identity: tuple,
        parent: str,
        child: str,
        before: ActionState,
        after: ActionState,
    ) -> dict:
        """Call both production mutation authorities for a real Git edge."""
        self.metrics.mutation_calls += 1
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
        base = {
            "scenario": fixture.scenario,
            "C": None,
            "O": fixture.O,
            "N": fixture.N,
            "expected_result": fixture.expected,
            "input_contract": {
                "schema": "restack-provenance-input/v2",
                "authoritative_endpoints": ["O", "N"],
            },
        }
        objects = None
        try:
            with reconciler_repository(
                fixture.repo.root
            ), count_production_git(self.metrics):
                objects = ObjectDatabase(fixture.repo.root, self.metrics)
                self.objects = objects
                self.graph = Graph(
                    fixture.repo.root,
                    fixture.O,
                    fixture.N,
                    objects,
                    self.metrics,
                    reopen_outside_c_boundary_ancestry=(
                        self.damage.reopen_outside_c_boundary_ancestry
                    ),
                )
                base["C"] = self.graph.C
                if fixture.expected_C:
                    base["derived_C_matches_fixture"] = (
                        self.graph.C == fixture.expected_C
                    )
                budget_result = self.budget_result(base)
                if budget_result is not None:
                    return budget_result
                if self.graph.C == fixture.O:
                    return {
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
                    return budget_result
                return result
        except (
            Unreadable,
            RECONCILE.GitSnapshotError,
            OSError,
            ValueError,
            UnicodeError,
        ) as error:
            return {
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
        finally:
            if objects is not None:
                objects.close()


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
        if Classifier.explicit_review_pending(target)
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
) -> Fixture:
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
    return Fixture(
        scenario,
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding" if valid else "blocking-finding",
    )


def p3_old_loss(root: Path) -> Fixture:
    repo = GitRepository(root)
    initialize(repo)
    C = repo.commit("create action-free C")
    repo.branch("old", C)
    path = add_agent(repo, "p3")
    O = feature(repo, "p3-task")
    repo.branch("candidate", C)
    candidate_landmark = feature(repo, "p3-base")
    N = feature(repo, "p3-task")
    return Fixture(
        "P3-genuine-old-loss",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"lost_path": path},
    )


def p4_pre_c_origins(root: Path) -> Fixture:
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
    return Fixture(
        "P4-pre-C-identical-origins",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {"pre_C_origins": [A, B], "pre_C_root": R},
    )


def p5_duplicate_at_c(root: Path) -> Fixture:
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
    return Fixture(
        "P5-duplicate-at-C",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
    )


def p6_old_recreate(root: Path) -> Fixture:
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
    return Fixture(
        "P6a-old-delete-recreate",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
    )


def p6_candidate_recreate(root: Path) -> Fixture:
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
    return Fixture(
        "P6b-candidate-delete-recreate",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
    )


def p7_payload_change(root: Path) -> Fixture:
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
    return Fixture(
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


def p8_timing_move(root: Path) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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


def pcx03_foreign_identity(root: Path) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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


def p14_supplier_reintroduced(root: Path) -> Fixture:
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
    return Fixture(
        "P14-supplier-reintroduced",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"first_deletion": first, "second_deletion": second},
    )


def p15_competing_suppliers(root: Path) -> Fixture:
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
    return Fixture(
        "P15-competing-suppliers",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"supplier_events": suppliers},
    )


def p17_post_event_reintroduction(root: Path) -> Fixture:
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
    return Fixture(
        "P17-post-event-reintroduction",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"early_authority_event": first},
    )


def pcx04_shared_supplier(root: Path) -> Fixture:
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
    return Fixture(
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


def pcx05_competing_later_supplier(root: Path) -> Fixture:
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
    return Fixture(
        "PCX-05-competing-later-supplier",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"D1": first, "D2": second},
    )


def pcx06_nested_supplier(root: Path) -> Fixture:
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
    return Fixture(
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


def pcx09_recreated_claimed_bytes(root: Path) -> Fixture:
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
    return Fixture(
        "PCX-09-recreated-claimed-bytes",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"D1": first, "D2": second},
    )


def pcx10_transient_multiplicity(root: Path) -> Fixture:
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
    return Fixture(
        "PCX-10-transient-multiplicity",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"duplicate_commit": duplicate, "duplicate_path": second},
    )


def pcx11_distinct_payload(root: Path) -> Fixture:
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
    return Fixture(
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


def pcx12_timing_supplier(root: Path) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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


def r8_review_binding(root: Path, *, divergent: bool) -> Fixture:
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
    return Fixture(
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


def r8_review_terminal_binding_conflict(root: Path) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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


def r13_persisted_state(root: Path, variant: str) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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


def r14_persisted_hidden_bytes(root: Path) -> Fixture:
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
    return Fixture(
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


def r14_persisted_intermediate_claim(root: Path) -> Fixture:
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
    return Fixture(
        "R14-persisted-intermediate-claim-regression",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"bad": bad, "expected_problem": "committed in-repair"},
    )


def r14_persisted_intermediate_review(root: Path) -> Fixture:
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
    return Fixture(
        "R14-persisted-intermediate-review-regression",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"bad": bad, "expected_problem": "immutable review binding"},
    )


def r14_persisted_delete_recreate(root: Path) -> Fixture:
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
    return Fixture(
        "R14-persisted-delete-recreate",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding",
        {"gap": gap, "old_path": path, "new_path": moved},
    )


def r14_persisted_review_retraction(root: Path) -> Fixture:
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
    return Fixture(
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


def r14_persisted_first_response_move(root: Path) -> Fixture:
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
    return Fixture(
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


def r14_persisted_merge_carriers(root: Path, *, conflict: bool) -> Fixture:
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
    return Fixture(
        f"R14-persisted-merge-carrier-{slug}",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "blocking-finding" if conflict else "no-finding",
        {"source": source, "carrier": carrier, "merge": candidate_landmark, "conflict": conflict},
    )


def r17_outside_c_neutral_parent(root: Path) -> Fixture:
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
    with reconciler_repository(repo.root):
        deletion_problem = RECONCILE.queue_deletion_problem(
            path,
            repo.run("show", f"{K}:{path}").stdout,
            K,
            deletion,
        )
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
        f"R17-persisted-{variant}{suffix}",
        repo,
        C,
        O,
        P,
        N,
        "blocking-finding",
        details,
    )


def r17_boundary_budget_fixture(root: Path) -> Fixture:
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
    return Fixture(
        "R17-wide-outside-C-boundary-budget",
        repo,
        C,
        O,
        P,
        N,
        "blocking-finding",
        {
            "A": A,
            "P": P,
            "outside_parents": outside,
            "budget_contract": {
                "limit": 7,
                "overflow_classification": "budget-exceeded",
                "transactional_zero_results": True,
            },
            "review_reference_oids": {
                "C": "b066accf737c901fd1ee314fcf310afb70c8fe87",
                "O": "ba894e5a1c019e3b2c29ee8319eebfb4b0aaa9a3",
                "P": "b79ff7a4036270fed4a70d82ad226817ae94e662",
                "N": "412c2f8c5a8be93d1e0ffc5983d607bf750bb2f0",
            },
        },
        budget_limit=7,
    )


def r17_workflow_input_case(root: Path, case: str) -> Fixture:
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
        fixture = Fixture(
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


def r17_unreadable_boundary(root: Path) -> Fixture:
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


def r17_unopened_outside_c_ancestor(root: Path) -> Fixture:
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
    return Fixture(
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


def r15_old_side_continuity(root: Path, variant: str) -> Fixture:
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
        with reconciler_repository(repo.root):
            details["deletion_problem"] = RECONCILE.queue_deletion_problem(
                path,
                repo.run(
                    "show", f"{details['authority_parent']}:{path}"
                ).stdout,
                details["authority_parent"],
                details["authority_child"],
            )
    return Fixture(
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


def r3_two_invalid_sources(root: Path) -> Fixture:
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
    return Fixture(
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


def r3_invalid_valid_competition(root: Path) -> Fixture:
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
    return Fixture(
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


def r3_valid_plus_invalid_at_N(root: Path) -> Fixture:
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
    return Fixture(
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


def r4_same_root_diamond(root: Path) -> Fixture:
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
    return Fixture(
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


def r4_distinct_root_diamond(root: Path) -> Fixture:
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
    return Fixture(
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


def r4_equal_root_plus_invalid(root: Path) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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


def r6_same_root_all_absent_wrappers(root: Path) -> Fixture:
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
    return Fixture(
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
    repo.write(path, RECONCILE.retry_text(finding))
    return path


def pcx15_generated_retry(root: Path) -> Fixture:
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
        RECONCILE.retry_text(
            RECONCILE.Finding(
                "queue-name", Path(bad), "bad name", "rename it"
            )
        ),
    )
    return Fixture(
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


def pcx16_task_pickup(root: Path) -> Fixture:
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
    return Fixture(
        "PCX-16-task-pickup-supplier",
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
        {"pickup_path": pickup, "active_task": active},
    )


def r16_supplier_support_fixture(root: Path, variant: str) -> Fixture:
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
    with reconciler_repository(repo.root):
        source_problem = RECONCILE.queue_deletion_problem(
            path,
            repo.run("show", f"{authority_parent}:{path}").stdout,
            authority_parent,
            authority_child,
        )
    return Fixture(
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


def r16_earlier_evidence_reversal(root: Path) -> Fixture:
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
    with reconciler_repository(repo.root):
        source_problem = RECONCILE.queue_deletion_problem(
            path,
            authority_text,
            authority_parent,
            authority_child,
        )
        replay_problem = RECONCILE.queue_deletion_problem(
            path, authority_text, authority_parent, candidate_landmark
        )
    return Fixture(
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
) -> Fixture:
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
    return Fixture(
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


def p19_identities(root: Path) -> Fixture:
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
    return Fixture(
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


def p20_lifecycle_types(root: Path) -> Fixture:
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
    return Fixture(
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


def pcx17_cherry_pick(root: Path, mode: str) -> Fixture:
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
    return Fixture(
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


def pcx18_many_actions(root: Path) -> Fixture:
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
    return Fixture(
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


def p18_missing_tip(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18a-missing-tip", valid=True
    )
    fixture.O = "f" * len(fixture.O)
    fixture.expected = "unreadable"
    return fixture


def p18_noncommit_tip(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18b-noncommit-tip", valid=True
    )
    fixture.O = fixture.repo.run(
        "hash-object", "-w", "--stdin", input_text="not a commit\n"
    ).stdout.strip()
    fixture.expected = "unreadable"
    return fixture


def p18_unrelated_tip(root: Path) -> Fixture:
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


def p18_shallow(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18d-shallow-required-region", valid=True
    )
    (fixture.repo.root / ".git/shallow").write_text(
        fixture.expected_C + "\n", encoding="ascii"
    )
    fixture.expected = "unreadable"
    return fixture


def p18_missing_blob(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18e-missing-queue-blob", valid=True
    )
    path = queue_path(fixture.scenario.lower())
    blob = fixture.repo.tree_entry_oid(fixture.expected_C, path)
    fixture.repo.hide_loose_object(blob)
    fixture.expected = "unreadable"
    fixture.details["missing_blob_oid"] = blob
    return fixture


def p18_missing_tree(root: Path) -> Fixture:
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


def p18_multiple_bases(root: Path) -> Fixture:
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
    return Fixture(
        "P18g-multiple-merge-bases",
        repo,
        R,
        O,
        candidate_landmark,
        N,
        "unreadable",
        {"expected_merge_bases": [A, B]},
    )


def pcx19_missing_claim_blob(root: Path) -> Fixture:
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


def budget_fixture(root: Path, *, overflow: bool) -> Fixture:
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
    fixture = Fixture(
        scenario,
        repo,
        C,
        O,
        candidate_landmark,
        N,
        "no-finding",
    )
    probe = Classifier(fixture).run()
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


def scenario_builders():
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
    "restore-universal-ancestor-carry-scan",
    "ignore-outside-C-carrier",
    "ignore-absent-C-arm",
    "ignore-persisted-outside-C-collision",
    "ignore-persisted-absent-C-arm",
    "first-parent-carry-proof",
    "skip-carry-compatibility",
    "unmetered-cone-work",
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


def run_fixture(fixture: Fixture, damage: Damage | None = None):
    if "restore_hidden" not in fixture.details:
        result = Classifier(fixture, damage).run()
        workflow = fixture.details.get("workflow_contract", {})
        if workflow.get("repeat_exact_inputs") and damage is None:
            repeated = Classifier(fixture).run()
            result["workflow_input_evidence"] = {
                "exact_O_N_repeated": [fixture.O, fixture.N],
                "raw_results_equal": result == repeated,
            }
        return result
    if damage is not None:
        raise ValueError("recovery fixture does not accept damage mode")
    missing_oid = fixture.details["missing_claim_blob_oid"]
    reader_metrics = Metrics()
    reader = ObjectDatabase(fixture.repo.root, reader_metrics)
    first_reader_reason = None
    try:
        reader.read(missing_oid)
    except Unreadable as error:
        first_reader_reason = str(error)
    missing_cached = missing_oid in reader.objects
    first = Classifier(fixture).run()
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
        reader.close()
    second = Classifier(fixture).run()
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
            or result["metrics"]["graph_parent_edges"] <= 7
            or "graph_parent_edges" not in result["evidence_verdict"]["reason"]
        ):
            errors.append("R17 wide boundary escaped transactional budget")
        if details["review_reference_oids"] != {
            "C": "b066accf737c901fd1ee314fcf310afb70c8fe87",
            "O": "ba894e5a1c019e3b2c29ee8319eebfb4b0aaa9a3",
            "P": "b79ff7a4036270fed4a70d82ad226817ae94e662",
            "N": "412c2f8c5a8be93d1e0ffc5983d607bf750bb2f0",
        }:
            errors.append("R17 wide-boundary reviewer OIDs changed")
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
    if scenario == "R17-unreadable-outside-C-boundary" and (
        status != "unreadable"
        or result["audit_exit"] != 2
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
            or not Classifier.explicit_review_pending(
                details["old_pending_value"]
            )
            or Classifier.explicit_review_pending(
                details["candidate_value"]
            )
            or not all(
                Classifier.explicit_review_pending(value)
                for value in pending_presentations
            )
            or any(
                Classifier.explicit_review_pending(value)
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
            or Classifier.explicit_review_pending(details["old_value"])
            or not Classifier.broad_review_pending(details["old_value"])
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
        if (
            actions
            or status != "ambiguous"
            or result["audit_exit"] != 2
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
    return errors


def control_builder(name: str, root: Path):
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
    raise ValueError(name)


def run_control(name: str, root: Path):
    fixture, damage, damaged_expected = control_builder(name, root)
    baseline = Classifier(fixture).run()
    damaged = Classifier(fixture, damage).run()
    observed = bool(
        baseline["classification"] == fixture.expected
        and damaged["classification"] == damaged_expected
        and damaged["classification"] != fixture.expected
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
    }


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


def run_suite(root: Path):
    failures = []
    results = []
    for index, builder in enumerate(scenario_builders(), start=1):
        fixture_root = root / f"{index:02d}"
        fixture = builder(fixture_root)
        result = run_fixture(fixture)
        errors = validate_result(result)
        if errors:
            failures.append({"scenario": result["scenario"], "errors": errors})
        results.append(result)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
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
    print(
        json.dumps(
            {
                "r17_parent_permutation": permutation_signatures,
                "r17_persisted_parent_permutations": (
                    persisted_permutations
                ),
                "status": "PASS" if permutation_ok else "FAIL",
            },
            sort_keys=True,
        )
    )
    alias_inventory, alias_failures = validate_scenario_aliases(results)
    failures.extend(alias_failures)
    print(
        json.dumps(
            {
                "scenario_alias_inventory": alias_inventory,
                "status": "PASS" if not alias_failures else "FAIL",
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    controls = []
    for index, name in enumerate(CONTROL_NAMES, start=1):
        result = run_control(name, root / f"control-{index:02d}")
        controls.append(result)
        if result["status"] != "OBSERVED_RED":
            failures.append({"control": name, "errors": [result["status"]]})
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
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
        "python": sys.version.split()[0],
        "git": REAL_RUN(
            ["git", "--version"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip(),
        "failures": failures,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if not failures else 1


def ordinary_audit(
    root: Path, O: str, N: str, budget_limit: int | None
) -> dict:
    """Audit exactly two immutable O,N commit IDs in an existing repository."""
    valid_oid = lambda value: (
        len(value) in {40, 64}
        and all(char in "0123456789abcdef" for char in value)
    )
    if not valid_oid(O) or not valid_oid(N) or (
        budget_limit is not None and budget_limit <= 0
    ):
        reason = (
            "O and N must be full lowercase hexadecimal object IDs"
            if not valid_oid(O) or not valid_oid(N)
            else "budget must be a positive integer"
        )
        return {
            "scenario": "ordinary-audit",
            "C": None,
            "O": O,
            "N": N,
            "input_contract": {
                "schema": "restack-provenance-input/v2",
                "authoritative_endpoints": ["O", "N"],
            },
            "audit_exit": 2,
            "classification": "unreadable",
            "evidence_verdict": {"status": "unreadable", "reason": reason},
            "event_mode": "none",
            "authority_edges": [],
            "propagation_edges": [],
            "mutation_edges": [],
            "support_checks": [],
            "carry_proofs": [],
            "actions": [],
            "metrics": Metrics().as_dict(),
        }
    fixture = Fixture(
        "ordinary-audit",
        RepositoryView(root),
        "",
        O,
        "",
        N,
        "",
        budget_limit=budget_limit,
    )
    result = Classifier(fixture).run()
    result.pop("expected_result", None)
    result.pop("details", None)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--control", choices=CONTROL_NAMES)
    parser.add_argument("--fixtures-dir", type=Path)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--old", metavar="O")
    parser.add_argument("--new", metavar="N")
    parser.add_argument("--budget", type=int)
    arguments = parser.parse_args(argv)
    ordinary = any(
        value is not None
        for value in (arguments.repo, arguments.old, arguments.new)
    )
    selected = int(arguments.self_test) + int(arguments.control is not None) + int(
        ordinary
    )
    if selected != 1:
        parser.error("choose exactly one of --self-test, --control, or --repo/--old/--new")
    if ordinary and None in (arguments.repo, arguments.old, arguments.new):
        parser.error("ordinary audit requires --repo, --old O, and --new N")
    if ordinary:
        result = ordinary_audit(
            arguments.repo.resolve(),
            arguments.old,
            arguments.new,
            arguments.budget,
        )
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
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
            return run_suite(root)
        result = run_control(arguments.control, root / "control")
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 0 if result["status"] == "OBSERVED_RED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
