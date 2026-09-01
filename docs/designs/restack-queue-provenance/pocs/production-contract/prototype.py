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
    per_action_history_walks: int = 0

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
    C: str
    O: str
    M: str
    N: str
    expected: str
    details: dict = dataclasses.field(default_factory=dict)
    budget_limit: int | None = None


@dataclasses.dataclass
class Damage:
    validate_all_direct_parents: bool = True
    allow_supplier_borrow: bool = False
    collapse_multiplicity: bool = False
    reopen_pre_c_genealogy: bool = False
    enforce_post_event_absence: bool = True
    sole_valid_ignores_competitors: bool = False


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


def is_git_command(command) -> bool:
    return bool(
        isinstance(command, (tuple, list))
        and command
        and Path(str(command[0])).name in {"git", "git.exe"}
    )


@contextlib.contextmanager
def count_production_git(metrics: Metrics):
    """Count Git children spawned by imported production helpers."""

    def counted_run(command, *args, **kwargs):
        if is_git_command(command):
            metrics.git_processes += 1
        return REAL_RUN(command, *args, **kwargs)

    def counted_popen(command, *args, **kwargs):
        if is_git_command(command):
            metrics.git_processes += 1
        return REAL_POPEN(command, *args, **kwargs)

    original_run = subprocess.run
    original_popen = subprocess.Popen
    subprocess.run = counted_run
    subprocess.Popen = counted_popen
    try:
        yield
    finally:
        subprocess.run = original_run
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
    metrics.git_processes += 1
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
        C: str,
        O: str,
        N: str,
        objects: ObjectDatabase,
        metrics: Metrics,
    ):
        self.root = root
        self.C = C
        self.O = O
        self.N = N
        self.objects = objects
        self.metrics = metrics
        shallow = run_git(
            root, metrics, "rev-parse", "--is-shallow-repository"
        ).stdout.strip()
        if shallow == "true":
            raise Unreadable("required post-C history is shallow")
        for label, oid in (("C", C), ("O", O), ("N", N)):
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
        if merge_bases[0] != C:
            raise Unreadable(
                f"declared C {C} is not the unique merge base {merge_bases[0]}"
            )
        metrics.graph_enumerations += 1
        listing = run_git(
            root,
            metrics,
            "--no-replace-objects",
            "rev-list",
            "--parents",
            "--topo-order",
            "--reverse",
            O,
            N,
            f"^{C}",
        )
        self.order = [C]
        self.parents: dict[str, tuple[str, ...]] = {C: ()}
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
        if C not in self.old_nodes or C not in self.new_nodes:
            raise Unreadable("both tips must descend from C")
        self.candidate_nodes = self.new_nodes - self.old_nodes

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


class Classifier:
    """In-memory provenance over one enumerated graph and cached snapshots."""

    def __init__(self, fixture: Fixture, damage: Damage | None = None):
        self.fixture = fixture
        self.damage = damage or Damage()
        self.metrics = Metrics()
        self.objects: ObjectDatabase | None = None
        self.graph: Graph | None = None

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

    def selected_base_problem(self) -> str | None:
        """Validate declared M before any identity or authority work."""
        assert self.objects is not None
        assert self.graph is not None
        M = self.fixture.M
        try:
            tree = self.objects.commit_tree(M)
            self.objects.tree_entries(tree)
        except Unreadable as error:
            raise Unreadable(f"M {M}: {error}") from error
        if M not in self.graph.new_nodes:
            return (
                f"declared M {M} is outside the required C-rooted candidate "
                f"region: M must descend from or equal C {self.fixture.C} "
                f"and be an ancestor of or equal N {self.fixture.N}"
            )
        return None

    def unique_carry_problem(
        self, identity: tuple, tip: str
    ) -> str | None:
        assert self.graph is not None
        region = self.graph.ancestors(tip)
        if self.graph.C not in region:
            return f"carrying parent {tip} is not rooted at C"
        for commit in region:
            multiplicity = len(self.states(commit, identity))
            if multiplicity != 1:
                paths = [
                    state.path for state in self.states(commit, identity)
                ]
                return (
                    f"C-rooted carrying history is discontinuous at {commit}: "
                    f"multiplicity {multiplicity}, paths {paths}"
                )
        return None

    def absence_problem(
        self, identity: tuple, start: str, end: str
    ) -> str | None:
        assert self.graph is not None
        region = self.graph.between(start, end)
        if not region:
            return f"{start} is not on an ancestry path to {end}"
        for commit in region:
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
        return {
            "parent": parent,
            "child": child,
            "path": state.path,
            "problem": problem,
        }

    def parent_roles(self, identity: tuple, child: str):
        assert self.graph is not None
        carrying = []
        absent = []
        neutral = []
        duplicate = []
        for parent in self.graph.parents[child]:
            multiplicity = len(self.states(parent, identity))
            if multiplicity == 1:
                carrying.append(parent)
            elif multiplicity > 1:
                duplicate.append(parent)
            elif self.graph.reaches_C(parent):
                absent.append(parent)
            else:
                neutral.append(parent)
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
            if not carrying or absent:
                continue
            if duplicate:
                event = Event(
                    "ambiguous",
                    "direct",
                    child,
                    [],
                    [],
                    neutral,
                    [],
                    "direct-parent-multiplicity",
                    "a carrying parent has duplicate exact identities",
                )
                events.append(
                    self.attach_causal_metadata(
                        event, [self.synthetic_causal_root(event)]
                    )
                )
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
            continuity = next(
                (
                    problem
                    for problem in (
                        self.unique_carry_problem(identity, parent)
                        for parent in carrying
                    )
                    if problem
                ),
                None,
            )
            invalid = [edge for edge in edges if edge["problem"]]
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
                neutral,
                [],
                code,
                reason,
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
    def stable_oids(oids):
        return list(dict.fromkeys(oids))

    def response_conflict(
        self,
        identity: tuple,
        authority_edges: list[dict],
        carrying: list[str],
    ) -> str | None:
        if self.identity_view(identity)["actor"] != "needs-human":
            return None
        responses = set()
        revisions = [
            edge["parent"] for edge in authority_edges
        ] + carrying
        for revision in revisions:
            states = self.states(revision, identity)
            if len(states) != 1:
                continue
            fields = RECONCILE.human_response_fields(states[0].text)
            key = RECONCILE.first_concrete_response(fields)
            if key:
                responses.add((key, fields[key]))
        if len(responses) > 1:
            return (
                "carrying and supplier lineages contain conflicting concrete "
                "human responses"
            )
        return None

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
            carry_problem = next(
                (
                    problem
                    for problem in (
                        self.unique_carry_problem(identity, parent)
                        for parent in carrying
                    )
                    if problem
                ),
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
                    conflict = self.response_conflict(
                        identity, authority_edges, carrying
                    )
                    if conflict:
                        result = Event(
                            "invalid",
                            "supplier",
                            child,
                            authority_edges,
                            propagation_edges,
                            accumulated_neutral,
                            accumulated_absent,
                            "conflicting-human-response",
                            conflict,
                        )
                        result = self.attach_causal_metadata(
                            result,
                            self.retag_roots(causal_roots, "invalid"),
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
                                    "propagate"
                                )
                            ),
                        )
                        result = self.attach_causal_metadata(
                            result, causal_roots, prior_records
                        )
                        sources.append(result)
                        observed_sources.append(result)
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
                for commit in self.graph.between(
                    event.child, self.fixture.N
                )
            )
        )

    def final_absence_participants(
        self, identity: tuple, events: list[Event]
    ) -> list[Event]:
        """Find the event frontier at M, extended after reintroduction."""
        assert self.graph is not None
        boundary = (
            self.fixture.M
            if self.absence_problem(
                identity, self.fixture.M, self.fixture.N
            )
            is None
            else self.fixture.N
        )
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
        C_states = self.states(self.fixture.C, identity)
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
        C_states = self.states(self.fixture.C, identity)
        N_states = self.states(self.fixture.N, identity)
        if N_states:
            if len(N_states) == len(old_states):
                return {
                    **base,
                    "status": "none",
                    "finding": False,
                    "authoring_lineage": "preserved",
                    "reason_code": "identity-preserved",
                    "reason": "the exact production identity remains live",
                }
            return {
                **base,
                "status": "ambiguous",
                "finding": True,
                "authoring_lineage": "multiplicity-changed",
                "reason_code": "endpoint-multiplicity-change",
                "reason": "candidate multiplicity differs from the old tip",
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
        if self.damage.reopen_pre_c_genealogy:
            assert self.objects is not None
            parents = self.objects.commit_parents(self.fixture.C)
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
        old_problem = self.unique_carry_problem(identity, self.fixture.O)
        if old_problem:
            return {
                **base,
                "status": "invalid",
                "finding": True,
                "authoring_lineage": "old-side-discontinuous",
                "reason_code": "old-side-discontinuity",
                "reason": old_problem,
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
            for commit in self.graph.candidate_nodes
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
            "C": fixture.C,
            "O": fixture.O,
            "M": fixture.M,
            "N": fixture.N,
            "expected_result": fixture.expected,
            "range_base_validation": {
                "status": "unchecked",
                "M": fixture.M,
                "reason": "M validation has not run",
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
                    fixture.C,
                    fixture.O,
                    fixture.N,
                    objects,
                    self.metrics,
                )
                M_problem = self.selected_base_problem()
                if M_problem:
                    return {
                        **base,
                        "range_base_validation": {
                            "status": "ambiguous",
                            "M": fixture.M,
                            "reason": M_problem,
                        },
                        "classification": "blocking-finding",
                        "evidence_verdict": {
                            "status": "ambiguous",
                            "reason": M_problem,
                        },
                        "event_mode": "none",
                        "authority_edges": [],
                        "propagation_edges": [],
                        "actions": [],
                        "metrics": self.metrics.as_dict(),
                        "details": fixture.details,
                    }
                base["range_base_validation"] = {
                    "status": "valid",
                    "M": fixture.M,
                    "reason": (
                        f"M {fixture.M} is a readable commit in the "
                        f"C-rooted candidate ancestry through N {fixture.N}"
                    ),
                }
                if (
                    fixture.budget_limit is not None
                    and self.metrics.graph_commits > fixture.budget_limit
                ):
                    return {
                        **base,
                        "classification": "blocking-finding",
                        "evidence_verdict": {
                            "status": "ambiguous",
                            "reason": (
                                "measured fixture budget exceeded: "
                                f"{self.metrics.graph_commits}>"
                                f"{fixture.budget_limit}"
                            ),
                        },
                        "event_mode": "none",
                        "authority_edges": [],
                        "propagation_edges": [],
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
                for commit in self.graph.candidate_nodes:
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
                    "actions": actions,
                    "metrics": self.metrics.as_dict(),
                    "details": fixture.details,
                }
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
                "range_base_validation": {
                    "status": "unreadable",
                    "M": fixture.M,
                    "reason": str(error),
                },
                "classification": "unreadable",
                "evidence_verdict": {
                    "status": "unreadable",
                    "reason": str(error),
                },
                "event_mode": "none",
                "authority_edges": [],
                "propagation_edges": [],
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
        M = delete_with_evidence(repo, ((label, path),))
    else:
        repo.remove(path)
        M = repo.commit("delete without authority")
    N = feature(repo, f"{label}-old")
    return Fixture(
        scenario,
        repo,
        C,
        O,
        M,
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
    M = feature(repo, "p3-base")
    N = feature(repo, "p3-task")
    return Fixture(
        "P3-genuine-old-loss",
        repo,
        C,
        O,
        M,
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
    M = delete_with_evidence(repo, (("p4", path),))
    N = feature(repo, "p4-old")
    return Fixture(
        "P4-pre-C-identical-origins",
        repo,
        C,
        O,
        M,
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
    M = repo.commit("delete both duplicate paths")
    N = feature(repo, "p5-old")
    return Fixture(
        "P5-duplicate-at-C",
        repo,
        C,
        O,
        M,
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
    M = delete_with_evidence(repo, (("p6-old", path),))
    N = feature(repo, "p6-old-task")
    return Fixture(
        "P6a-old-delete-recreate",
        repo,
        C,
        O,
        M,
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
    M = delete_with_evidence(
        repo, (("p6-candidate", path),), "second deletion"
    )
    N = feature(repo, "p6-candidate-old")
    return Fixture(
        "P6b-candidate-delete-recreate",
        repo,
        C,
        O,
        M,
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
    M = delete_with_evidence(repo, (("p7", path),))
    N = feature(repo, "p7-old")
    return Fixture(
        "P7-immutable-payload-change",
        repo,
        C,
        O,
        M,
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
    M = repo.commit("perform one-to-one timing path move")
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
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.commit("delete recreated p17 without claim")
    N = feature(repo, "p17-old")
    return Fixture(
        "P17-post-event-reintroduction",
        repo,
        C,
        O,
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
        N,
        "no-finding",
        {
            "direct_event": deletion,
            "adoptions": [adoption_one, M],
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
    M = repo.merge_commit(
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
        M,
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
    M = delete_with_evidence(repo, (("pcx10", first),))
    N = feature(repo, "pcx10-old")
    return Fixture(
        "PCX-10-transient-multiplicity",
        repo,
        C,
        O,
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
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
        M = repo.merge_commit(
            (outer_invalid, carrier_three, neutral_three),
            "continue third-level invalid human supplier ancestry",
            removes=(path,),
        )
        details.update(
            {
                "inner_invalid": inner_invalid,
                "outer_invalid": outer_invalid,
                "adoptions": [inner_invalid, outer_invalid, M],
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
        M = repo.merge_commit(
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
        M,
        N,
        (
            "blocking-finding"
            if conflicting_carrier
            else "no-finding"
        ),
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
    M = repo.merge_commit(
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
        M,
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
            "adoptions": [first["adoption"], second["adoption"], M],
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
    M = repo.merge_commit(
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
        M,
        N,
        "blocking-finding",
        {
            "authority_events": [
                invalid["authority_event"],
                valid_deletion,
            ],
            "source_children": [invalid["adoption"], valid_deletion],
            "carriers": [invalid["carrier"], final_carrier],
            "adoptions": [invalid["adoption"], M],
            "neutral_parents": [invalid["neutral"], final_neutral],
            "absent_sources": [
                invalid["authority_event"],
                invalid["adoption"],
                valid_deletion,
            ],
        },
    )


def r3_unrelated_invalid_does_not_poison(root: Path) -> Fixture:
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
    M = repo.merge_commit(
        (supplier, carrier),
        "adopt only the causally relevant valid supplier",
        removes=(path,),
    )
    N = repo.merge_commit(
        (M, unrelated_invalid),
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
        "R3-03-unrelated-invalid-does-not-poison",
        repo,
        C,
        O,
        M,
        N,
        "no-finding",
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
    M = final["adoption"]
    N = feature(repo, "r4-same-root-diamond-old")
    return Fixture(
        "R4-01-same-root-valid-diamond",
        repo,
        C,
        O,
        M,
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
                M,
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
                M,
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
    M = final["adoption"]
    N = feature(repo, "r4-distinct-root-diamond-old")
    return Fixture(
        "R4-02-distinct-valid-root-diamond",
        repo,
        C,
        O,
        M,
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
                M,
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
                M,
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
    M = final["adoption"]
    N = feature(repo, "r4-equal-root-plus-invalid-old")
    return Fixture(
        "R4-03-equal-root-plus-invalid-diamond",
        repo,
        C,
        O,
        M,
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
                M,
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
                M,
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
    M = repo.merge_commit(
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
        M,
        N,
        "blocking-finding",
        {
            "initial_authority_parent": root_parent,
            "initial_authority_child": valid_root,
            "carrier": carrier,
            "supplier_adoption": M,
            "initial_absent_parent": valid_root,
            "reintroduction": reintroduction,
            "later_authority_parent": later_parent,
            "later_authority_child": redeletion,
            "later_authority_valid": later_valid,
            "reason_children": [valid_root, M, redeletion],
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
    M = repo.merge_commit(
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
        M,
        N,
        "blocking-finding",
        {
            "causal_events": roots,
            "causal_statuses": statuses,
            "expected_problem_count": sum(
                status != "valid" for status in statuses
            ),
            "legacy_sole_valid_false_green": first_valid,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
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
    M = repo.merge_commit(
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
        M,
        N,
        "no-finding",
        {"pickup_path": pickup, "active_task": active},
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
    M = feature(repo, "p19-base")
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
        M,
        N,
        "no-finding",
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
    M = repo.commit("resolve every lifecycle type")
    N = feature(repo, "p20-old")
    return Fixture(
        "P20-lifecycle-types",
        repo,
        C,
        O,
        M,
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
        repo.run("cherry-pick", K, D)
        M = repo.oid("HEAD")
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
        M = repo.oid("HEAD")
        expected = "blocking-finding"
    elif mode == "squash":
        final_tree = repo.oid(f"{D}^{{tree}}")
        M = repo.commit_tree(
            final_tree, "squash claim and deletion", C
        )
        repo.branch("candidate-squash", M)
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
        M,
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
    M = repo.commit("delete all sixteen actions")
    N = feature(repo, "many-old")
    return Fixture(
        "P22-PCX-18-one-pass-many-actions",
        repo,
        C,
        O,
        M,
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
    fixture.M = unrelated
    fixture.expected = "unreadable"
    return fixture


def p18_shallow(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18d-shallow-required-region", valid=True
    )
    (fixture.repo.root / ".git/shallow").write_text(
        fixture.C + "\n", encoding="ascii"
    )
    fixture.expected = "unreadable"
    return fixture


def p18_missing_blob(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18e-missing-queue-blob", valid=True
    )
    path = queue_path(fixture.scenario.lower())
    blob = fixture.repo.tree_entry_oid(fixture.C, path)
    fixture.repo.hide_loose_object(blob)
    fixture.expected = "unreadable"
    fixture.details["missing_blob_oid"] = blob
    return fixture


def p18_missing_tree(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18f-missing-queue-tree", valid=True
    )
    tree = fixture.repo.tree_entry_oid(fixture.C, "message-queue")
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
    M = feature(repo, "p18g-base")
    N = feature(repo, "p18g-old")
    return Fixture(
        "P18g-multiple-merge-bases",
        repo,
        R,
        O,
        M,
        N,
        "unreadable",
        {"expected_merge_bases": [A, B]},
    )


def p18_missing_M(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18h-missing-M", valid=True
    )
    fixture.M = "f" * len(fixture.M)
    fixture.expected = "unreadable"
    fixture.details["M_failure"] = "missing-object"
    return fixture


def p18_noncommit_M(root: Path, kind: str) -> Fixture:
    letter = {"blob": "i", "tree": "j", "tag": "k"}[kind]
    fixture = ordinary_linear_fixture(
        root, f"P18{letter}-noncommit-M-{kind}", valid=True
    )
    if kind == "blob":
        M = fixture.repo.run(
            "hash-object", "-w", "--stdin", input_text="not M\n"
        ).stdout.strip()
    elif kind == "tree":
        M = fixture.repo.run("mktree", input_text="").stdout.strip()
    elif kind == "tag":
        blob = fixture.repo.run(
            "hash-object", "-w", "--stdin", input_text="tag target\n"
        ).stdout.strip()
        M = fixture.repo.run(
            "mktag",
            input_text=(
                f"object {blob}\n"
                "type blob\n"
                "tag selected-base\n"
                "tagger Production Contract POC "
                "<production-contract@example.invalid> "
                "1800000000 +0000\n\n"
                "non-commit selected base\n"
            ),
        ).stdout.strip()
    else:
        raise ValueError(kind)
    fixture.M = M
    fixture.expected = "unreadable"
    fixture.details.update({"M_failure": "non-commit", "M_kind": kind})
    return fixture


def p18_unrelated_M(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18l-unrelated-M", valid=True
    )
    empty = fixture.repo.run("mktree", input_text="").stdout.strip()
    fixture.M = fixture.repo.commit_tree(empty, "unrelated M root")
    fixture.expected = "blocking-finding"
    fixture.details["M_failure"] = "unrelated-readable-commit"
    return fixture


def p18_M_after_N(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "P18m-M-after-N", valid=True
    )
    fixture.repo.branch("after-N", fixture.N)
    fixture.M = feature(fixture.repo, "p18m-after-N")
    fixture.expected = "blocking-finding"
    fixture.details["M_failure"] = "C-descendant-after-N"
    return fixture


def p18_M_endpoint(root: Path, endpoint: str) -> Fixture:
    scenario = f"P18{'n' if endpoint == 'C' else 'o'}-M-equals-{endpoint}"
    repo = GitRepository(root)
    initialize(repo)
    path = add_agent(repo, scenario.lower())
    C = repo.commit("create endpoint-equality action at C")
    repo.branch("old", C)
    O = feature(repo, f"{scenario.lower()}-old")
    repo.branch("candidate", C)
    N = feature(repo, f"{scenario.lower()}-candidate")
    M = C if endpoint == "C" else N
    return Fixture(
        scenario,
        repo,
        C,
        O,
        M,
        N,
        "no-finding",
        {
            "M_endpoint": endpoint,
            "preserved_path": path,
        },
    )


def pcx19_missing_claim_blob(root: Path) -> Fixture:
    fixture = ordinary_linear_fixture(
        root, "PCX-19-missing-claim-blob-recovery", valid=True
    )
    label = fixture.scenario.lower()
    path = queue_path(label)
    parents = fixture.repo.run(
        "rev-list", "--parents", "-n", "1", fixture.M
    ).stdout.split()
    claim_commit = parents[1]
    blob = fixture.repo.tree_entry_oid(claim_commit, path)
    hidden, restored = fixture.repo.hide_loose_object(blob)
    fixture.details.update(
        {
            "claim_commit": claim_commit,
            "missing_claim_blob_oid": blob,
            "restore_hidden": str(hidden),
            "restore_target": str(restored),
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
    M = delete_with_evidence(
        repo, ((scenario.lower(), path),), "budget fixture deletion"
    )
    N = feature(repo, "budget-old")
    measured = int(
        repo.run("rev-list", "--count", O, N, f"^{C}").stdout.strip()
    ) + 1
    limit = measured - 1 if overflow else measured
    return Fixture(
        scenario,
        repo,
        C,
        O,
        M,
        N,
        "blocking-finding" if overflow else "no-finding",
        {
            "measured_graph_commits": measured,
            "demonstration_limit": limit,
            "limit_is_launch_ceiling": False,
        },
        budget_limit=limit,
    )


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
        p18_missing_M,
        lambda root: p18_noncommit_M(root, "blob"),
        lambda root: p18_noncommit_M(root, "tree"),
        lambda root: p18_noncommit_M(root, "tag"),
        p18_unrelated_M,
        p18_M_after_N,
        lambda root: p18_M_endpoint(root, "C"),
        lambda root: p18_M_endpoint(root, "N"),
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
        lambda root: pcx17_cherry_pick(root, "complete"),
        lambda root: pcx17_cherry_pick(root, "deletion-only"),
        pcx19_missing_claim_blob,
        lambda root: budget_fixture(root, overflow=False),
        lambda root: budget_fixture(root, overflow=True),
        r3_two_invalid_sources,
        r3_invalid_valid_competition,
        r3_unrelated_invalid_does_not_poison,
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
    ]


CONTROL_NAMES = (
    "missing-all-parent-direct-validation",
    "supplier-authority-borrowing",
    "identity-multiplicity-collapsed-to-set",
    "reopen-pre-C-genealogy",
    "missing-post-event-continuity",
    "sole-valid-ignores-invalid-root",
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
        return Classifier(fixture, damage).run()
    if damage is not None:
        raise ValueError("recovery fixture does not accept damage mode")
    first = Classifier(fixture).run()
    hidden = Path(fixture.details["restore_hidden"])
    target = Path(fixture.details["restore_target"])
    if hidden.is_file():
        hidden.rename(target)
    second = Classifier(fixture).run()
    second["recovery"] = {
        "first_status": first["evidence_verdict"]["status"],
        "first_reason": first["evidence_verdict"]["reason"],
        "second_status": second["evidence_verdict"]["status"],
        "same_process": True,
        "missing_oid": fixture.details["missing_claim_blob_oid"],
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
    for name in ("C", "O", "M", "N"):
        oid = result[name]
        if len(oid) not in {40, 64} or any(
            char not in "0123456789abcdef" for char in oid
        ):
            errors.append(f"{name} is not a full OID")
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
        if not any("discontinu" in action["reason"] for action in actions):
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
    M_unreadable = {
        "P18h-missing-M",
        "P18i-noncommit-M-blob",
        "P18j-noncommit-M-tree",
        "P18k-noncommit-M-tag",
    }
    M_ambiguous = {
        "P18l-unrelated-M",
        "P18m-M-after-N",
    }
    M_endpoints = {
        "P18n-M-equals-C",
        "P18o-M-equals-N",
    }
    if (
        scenario.startswith("P18")
        and scenario not in M_ambiguous | M_endpoints
        and status != "unreadable"
    ):
        errors.append("P18 did not return structured unreadable")
    if scenario in M_unreadable | M_ambiguous:
        expected_M_status = (
            "unreadable" if scenario in M_unreadable else "ambiguous"
        )
        range_verdict = result["range_base_validation"]
        if (
            status != expected_M_status
            or range_verdict["status"] != expected_M_status
            or range_verdict["M"] != result["M"]
            or result["M"] not in range_verdict["reason"]
            or result["M"] not in result["evidence_verdict"]["reason"]
            or actions
            or result["event_mode"] != "none"
            or authority
            or propagation
            or result["metrics"]["identity_calls"] != 0
            or result["metrics"]["authority_calls"] != 0
        ):
            errors.append("P18 M gate did not fail before classification")
    if scenario in M_endpoints:
        endpoint = result["details"]["M_endpoint"]
        expected_M = result[endpoint]
        if (
            result["range_base_validation"]["status"] != "valid"
            or result["M"] != expected_M
            or result["classification"] != "no-finding"
            or status != "none"
            or authority
            or propagation
        ):
            errors.append("P18 rejected a permitted M endpoint equality")
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
            or "conflicting-human-response" not in action["reason"]
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
            f"conflicting-human-response@{source}"
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
            f"conflicting-human-response@{details['source_children'][0]}",
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
    if scenario == "R3-03-unrelated-invalid-does-not-poison":
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
            or status != "valid"
            or result["event_mode"] != "supplier"
            or len(authority) != 1
            or len(propagation) != 1
            or result["authority_edges"][0]["child"]
            != details["supplier"]
            or result["metrics"]["authority_calls"] < 4
        ):
            errors.append("R3-03 did not select the unique valid supplier")
        if details["unrelated_invalid"] in serialized_evidence:
            errors.append("R3-03 was poisoned by an unrelated invalid source")
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
    if scenario in {
        "R6-01-valid-plus-invalid-all-absent",
        "R6-02-valid-plus-ambiguous-all-absent",
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
        ):
            errors.append("PCX-19 missing object recovery failed")
    if scenario == "PCX-20b-budget-overflow":
        if (
            actions
            or status != "ambiguous"
            or result["metrics"]["authority_calls"] != 0
        ):
            errors.append("budget overflow selected an event")
    if scenario == "PCX-20a-budget-below-limit":
        if status != "valid" or not actions:
            errors.append("below-limit budget did not return normal verdict")
    return errors


def control_builder(name: str, root: Path):
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
        "C": fixture.C,
        "O": fixture.O,
        "M": fixture.M,
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


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--control", choices=CONTROL_NAMES)
    parser.add_argument("--fixtures-dir", type=Path)
    arguments = parser.parse_args(argv)
    if not arguments.self_test and not arguments.control:
        parser.error("choose --self-test or --control")

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
