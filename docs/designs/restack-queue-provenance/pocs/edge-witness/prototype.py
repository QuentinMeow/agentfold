#!/usr/bin/env python3
"""Isolated proof of concept for exact restack deletion witnesses.

This file deliberately does not patch the production reconciler.  It builds real
Git histories, locates candidate-only parent/child deletion edges, and asks the
current reconciler's queue lifecycle validator about those exact edges.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
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
OID_LENGTHS = (40, 64)


def load_reconciler():
    spec = importlib.util.spec_from_file_location(
        "edge_witness_reconcile", RECONCILE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {RECONCILE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RECONCILE = load_reconciler()


@dataclasses.dataclass
class Metrics:
    git_processes: int = 0
    scanner_tree_entry_reads: int = 0
    old_commits_scanned: int = 0
    old_parent_edges_scanned: int = 0
    candidate_commits: int = 0
    candidate_parent_edges: int = 0
    witness_child_parent_edges_scanned: int = 0
    origin_proof_commits_scanned: int = 0
    origin_proof_parent_edges_scanned: int = 0
    pre_witness_commits_scanned: int = 0
    pre_witness_parent_edges_scanned: int = 0
    post_witness_commits_scanned: int = 0
    post_witness_parent_edges_scanned: int = 0
    semantic_validation_calls: int = 0
    synthetic_control_calls: int = 0

    def as_dict(self):
        return dataclasses.asdict(self)


def is_git_command(command) -> bool:
    if not isinstance(command, (list, tuple)) or not command:
        return False
    return Path(str(command[0])).name in {"git", "git.exe"}


@contextlib.contextmanager
def count_reconciler_git(metrics: Metrics):
    """Count actual Git children spawned by imported production helpers."""

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
    """Small real-Git fixture builder with deterministic commit identities."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True)
        self.clock = 0
        self.run("init", "-q", "-b", "main")
        self.run("config", "user.name", "Edge Witness POC")
        self.run("config", "user.email", "edge-witness@example.invalid")

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
            rendered = " ".join(("git", *arguments))
            raise RuntimeError(
                f"{rendered} failed ({result.returncode}): {result.stderr.strip()}"
            )
        return result

    def write(self, relative: str, text: str):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def read(self, relative: str) -> str:
        return (self.root / relative).read_text(encoding="utf-8")

    def remove(self, relative: str):
        (self.root / relative).unlink()

    def branch(self, name: str, start: str):
        self.run("checkout", "-q", "-B", name, start)

    def _commit_environment(self):
        self.clock += 1
        stamp = str(1_700_000_000 + self.clock * 60) + " +0000"
        environment = dict(os.environ)
        environment.update(
            {
                "GIT_AUTHOR_NAME": "Edge Witness POC",
                "GIT_AUTHOR_EMAIL": "edge-witness@example.invalid",
                "GIT_COMMITTER_NAME": "Edge Witness POC",
                "GIT_COMMITTER_EMAIL": "edge-witness@example.invalid",
                "GIT_AUTHOR_DATE": stamp,
                "GIT_COMMITTER_DATE": stamp,
            }
        )
        return environment

    def commit(self, message: str) -> str:
        self.run("add", "-A")
        self.run("commit", "-q", "-m", message, env=self._commit_environment())
        return self.oid("HEAD")

    def commit_tree(self, tree: str, message: str, *parents: str) -> str:
        arguments = ["commit-tree", tree]
        for parent in parents:
            arguments.extend(("-p", parent))
        result = self.run(
            *arguments,
            input_text=message + "\n",
            env=self._commit_environment(),
        )
        return result.stdout.strip()

    def oid(self, revision: str) -> str:
        return self.run(
            "--no-replace-objects", "rev-parse", "--verify", revision
        ).stdout.strip()


@dataclasses.dataclass
class Fixture:
    scenario_id: str
    repo: GitRepository
    C: str
    O: str
    M: str
    N: str
    expected_verdict: str
    expected_findings: tuple[str, ...] = ()
    old_resolution: str | None = None
    side_resolution: str | None = None
    merge_commit: str | None = None
    conflicting_parent: str | None = None
    shared_origin: str | None = None
    disconnected_origins: tuple[str, ...] = ()


def queue_path(label: str) -> str:
    return (
        "message-queue/needs-agent/requests/"
        f"non-blocking-{label}.md"
    )


def evidence_path(label: str) -> str:
    return f"docs/evidence-{label}.md"


def action_text(
    label: str,
    status: str = "open",
    action=None,
    action_id: str | None = None,
) -> str:
    action_id_line = f"**Action-ID:** {action_id}\n" if action_id else ""
    return (
        f"# Preserve {label}\n\n"
        f"**Status:** {status}\n"
        f"{action_id_line}"
        "**Filed:** 2026-08-31\n"
        f"**Action:** {action or f'resolve {label}'}\n"
        f"**Full context:** `{evidence_path(label)}`\n"
        f"**Resolution evidence:** `{evidence_path(label)}`\n"
        "**If unanswered:** keep the action live\n"
    )


def create_common(repo: GitRepository, labels=(), activated=True) -> str:
    repo.write("README.md", "# Disposable edge-witness fixture\n")
    repo.write(
        "message-queue/AGENTS.md",
        "**Queue resolution schema:** "
        + ("v1" if activated else "v0")
        + "\n",
    )
    for label in labels:
        repo.write(evidence_path(label), f"# Evidence {label}: pending\n")
        repo.write(queue_path(label), action_text(label))
    return repo.commit("create common fixture state")


def claim(repo: GitRepository, label: str) -> str:
    path = queue_path(label)
    repo.write(path, repo.read(path).replace(
        "**Status:** open", "**Status:** in-repair", 1
    ))
    return repo.commit(f"claim {label}")


def resolve(repo: GitRepository, label: str, message=None) -> str:
    repo.write(evidence_path(label), f"# Evidence {label}: repaired\n")
    repo.remove(queue_path(label))
    return repo.commit(message or f"resolve {label}")


def feature(repo: GitRepository, name: str, content=None) -> str:
    repo.write(f"features/{name}.md", content or f"# Feature {name}\n")
    return repo.commit(f"add feature {name}")


def fixture_s1(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("s1",))
    repo.branch("old", C)
    O = feature(repo, "s1-old")
    repo.branch("candidate", C)
    claim(repo, "s1")
    M = resolve(repo, "s1")
    N = feature(repo, "s1-old")
    return Fixture("S1-valid-base-resolution", repo, C, O, M, N, "no-finding")


def fixture_s2(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("s2",))
    repo.branch("old", C)
    O = feature(repo, "s2-old")
    repo.branch("candidate", C)
    repo.remove(queue_path("s2"))
    M = repo.commit("delete s2 without claim or evidence")
    N = feature(repo, "s2-old")
    return Fixture(
        "S2-invalid-base-deletion", repo, C, O, M, N,
        "blocking-finding", (queue_path("s2"),),
    )


def fixture_s3(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo)
    repo.branch("old", C)
    repo.write(evidence_path("s3"), "# Evidence s3: pending\n")
    repo.write(queue_path("s3"), action_text("s3"))
    O = feature(repo, "s3-task")
    repo.branch("candidate", C)
    M = feature(repo, "s3-base")
    N = feature(repo, "s3-task")
    return Fixture(
        "S3-branch-owned-action-loss", repo, C, O, M, N,
        "blocking-finding", (queue_path("s3"),),
    )


def fixture_s4(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("s4",))
    repo.branch("old", C)
    repo.write(
        queue_path("s4"),
        action_text("s4", action="resolve the branch-authored s4 incarnation"),
    )
    O = feature(repo, "s4-task")
    repo.branch("candidate", C)
    claim(repo, "s4")
    M = resolve(repo, "s4")
    N = feature(repo, "s4-task")
    return Fixture(
        "S4-changed-action", repo, C, O, M, N,
        "blocking-finding", (queue_path("s4"),),
    )


def fixture_s5(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("s5-q1",))
    repo.branch("old", C)
    repo.write(evidence_path("s5-q2"), "# Evidence s5-q2: pending\n")
    repo.write(queue_path("s5-q2"), action_text("s5-q2"))
    O = feature(repo, "s5-task")
    repo.branch("candidate", C)
    claim(repo, "s5-q1")
    M = resolve(repo, "s5-q1")
    N = feature(repo, "s5-task")
    return Fixture(
        "S5-mixed-actions", repo, C, O, M, N,
        "blocking-finding", (queue_path("s5-q2"),),
    )


def fixture_s7(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("s7",))
    repo.branch("old", C)
    O = feature(repo, "s7-old")
    repo.branch("candidate", C)
    M = feature(repo, "s7-base")
    N = feature(repo, "s7-old")
    return Fixture("S7-unrelated-restack", repo, C, O, M, N, "no-finding")


def fixture_s8(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("s8",))
    O = feature(repo, "s8-old")
    M = O
    N = feature(repo, "s8-extension")
    return Fixture("S8-fast-forward-replacement", repo, C, O, M, N, "no-finding")


def fixture_s9_unrelated(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo)
    O = feature(repo, "s9-old")
    empty_tree = repo.run("mktree", input_text="").stdout.strip()
    M = repo.commit_tree(empty_tree, "unrelated candidate root")
    N = repo.commit_tree(empty_tree, "unrelated candidate child", M)
    return Fixture(
        "S9-unrelated-tip", repo, C, O, M, N, "snapshot-error"
    )


def fixture_s9_not_commit(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo)
    blob = repo.run(
        "hash-object", "-w", "--stdin", input_text="not a commit\n"
    ).stdout.strip()
    return Fixture("S9-non-commit-tip", repo, C, blob, C, C, "snapshot-error")


def fixture_s9_missing(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo)
    missing = "f" * len(C)
    return Fixture("S9-missing-tip", repo, C, missing, C, C, "snapshot-error")


def fixture_s10(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, activated=False)
    repo.branch("old", C)
    repo.write(evidence_path("s10"), "# Evidence s10: pending\n")
    repo.write(queue_path("s10"), action_text("s10"))
    O = repo.commit("file pre-v1 s10 action")
    repo.branch("candidate", C)
    repo.write(
        "message-queue/AGENTS.md", "**Queue resolution schema:** v1\n"
    )
    M = repo.commit("activate queue v1 on replacement")
    N = feature(repo, "s10-task")
    return Fixture(
        "S10-pre-v1-old-tip-action", repo, C, O, M, N,
        "blocking-finding", (queue_path("s10"),),
    )


def fixture_compact_valid_at_n(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("compact",))
    repo.branch("old", C)
    O = feature(repo, "compact-old")
    repo.branch("candidate", C)
    M = claim(repo, "compact")
    repo.write(evidence_path("compact"), "# Evidence compact: repaired at N\n")
    repo.remove(queue_path("compact"))
    repo.write("features/compact-old.md", "# Feature compact-old\n")
    N = repo.commit("resolve compact action at candidate head")
    return Fixture(
        "compact-valid-deletion-at-N", repo, C, O, M, N, "no-finding"
    )


def fixture_activation_laundering(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("activation-launder",), activated=False)
    repo.branch("old", C)
    O = feature(repo, "activation-launder-old")
    repo.branch("candidate", C)
    repo.remove(queue_path("activation-launder"))
    M = repo.commit("delete live action before queue v1")
    repo.write(
        "message-queue/AGENTS.md", "**Queue resolution schema:** v1\n"
    )
    N = feature(repo, "activation-launder-old")
    return Fixture(
        "activation-laundering", repo, C, O, M, N,
        "blocking-finding", (queue_path("activation-launder"),),
    )


def fixture_claimed_tip_laundering(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("claimed-launder",))
    repo.branch("old", C)
    claim(repo, "claimed-launder")
    O = feature(repo, "claimed-launder-old")
    repo.branch("candidate", C)
    M = feature(repo, "claimed-launder-base")
    repo.write(
        evidence_path("claimed-launder"),
        "# Evidence claimed-launder: unrelated candidate bytes\n",
    )
    repo.remove(queue_path("claimed-launder"))
    repo.write("features/claimed-launder-old.md", "# Feature claimed-launder-old\n")
    N = repo.commit("drop claimed action with changed evidence")
    return Fixture(
        "claimed-tip-synthetic-evidence-laundering", repo, C, O, M, N,
        "blocking-finding", (queue_path("claimed-launder"),),
    )


def fixture_independent_identical_incarnation(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo)
    repo.branch("old", C)
    repo.write(evidence_path("independent"), "# Evidence independent: pending\n")
    repo.write(queue_path("independent"), action_text("independent"))
    O = repo.commit("old tip authors independent action")
    repo.branch("candidate", C)
    repo.write(evidence_path("independent"), "# Evidence independent: pending\n")
    repo.write(queue_path("independent"), action_text("independent"))
    repo.commit("candidate independently authors byte-identical action")
    M = claim(repo, "independent")
    N = resolve(repo, "independent")
    return Fixture(
        "independent-byte-identical-incarnation", repo, C, O, M, N,
        "blocking-finding", (queue_path("independent"),),
    )


def fixture_old_delete_recreate_identical(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("old-delete-recreate",))
    repo.branch("old", C)
    repo.remove(queue_path("old-delete-recreate"))
    repo.commit("old side deletes original action")
    repo.write(
        queue_path("old-delete-recreate"),
        action_text("old-delete-recreate"),
    )
    O = repo.commit("old side recreates byte-identical action")
    repo.branch("candidate", C)
    M = claim(repo, "old-delete-recreate")
    N = resolve(repo, "old-delete-recreate")
    return Fixture(
        "old-delete-recreate-identical-incarnation", repo, C, O, M, N,
        "blocking-finding", (queue_path("old-delete-recreate"),),
    )


def fixture_old_legal_resolve_recreate_identical(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("old-legal-recreate",))
    repo.branch("old", C)
    claim(repo, "old-legal-recreate")
    old_resolution = resolve(repo, "old-legal-recreate")
    repo.write(
        evidence_path("old-legal-recreate"),
        "# Evidence old-legal-recreate: pending\n",
    )
    repo.write(
        queue_path("old-legal-recreate"),
        action_text("old-legal-recreate"),
    )
    O = repo.commit("old side creates a new byte-identical action")
    repo.branch("candidate", C)
    M = claim(repo, "old-legal-recreate")
    N = resolve(repo, "old-legal-recreate")
    return Fixture(
        "old-legal-resolve-recreate-identical-incarnation",
        repo, C, O, M, N, "blocking-finding",
        (queue_path("old-legal-recreate"),),
        old_resolution=old_resolution,
    )


def fixture_old_rename_round_trip(root: Path) -> Fixture:
    repo = GitRepository(root)
    label = "old-rename-roundtrip"
    original = queue_path(label)
    alternate = queue_path("old-rename-roundtrip-alternate")
    C = create_common(repo, (label,))
    repo.branch("old", C)
    repo.write(alternate, action_text(label))
    repo.remove(original)
    repo.commit("old side renames action away from its canonical path")
    repo.write(original, action_text(label))
    repo.remove(alternate)
    O = repo.commit("old side renames action back to its original path")
    repo.branch("candidate", C)
    M = claim(repo, label)
    N = resolve(repo, label)
    return Fixture(
        "old-rename-round-trip-incarnation-ambiguity",
        repo, C, O, M, N, "blocking-finding", (original,),
    )


def fixture_old_identity_mutation_round_trip(root: Path) -> Fixture:
    repo = GitRepository(root)
    label = "old-mutation-roundtrip"
    path = queue_path(label)
    C = create_common(repo, (label,))
    repo.branch("old", C)
    repo.write(
        path,
        action_text(label, action="resolve a different old-side obligation"),
    )
    repo.commit("old side mutates the action identity")
    repo.write(path, action_text(label))
    O = repo.commit("old side reintroduces the original action identity")
    repo.branch("candidate", C)
    M = claim(repo, label)
    N = resolve(repo, label)
    return Fixture(
        "old-identity-mutation-round-trip-incarnation",
        repo, C, O, M, N, "blocking-finding", (path,),
    )


def fixture_candidate_side_delete_merge_undo_mutate_delete(
    root: Path,
) -> Fixture:
    repo = GitRepository(root)
    label = "candidate-merge-undo"
    path = queue_path(label)
    C = create_common(repo, (label,))
    repo.branch("old", C)
    O = feature(repo, "candidate-merge-undo-old")

    repo.branch("candidate-main", C)
    carrying_parent = feature(repo, "candidate-merge-undo-main")
    repo.branch("candidate-side", C)
    claim(repo, label)
    side_resolution = resolve(repo, label)

    carrying_tree = repo.oid(f"{carrying_parent}^{{tree}}")
    merge_commit = repo.commit_tree(
        carrying_tree,
        "merge resolved side while retaining main action",
        carrying_parent,
        side_resolution,
    )
    repo.branch("candidate", merge_commit)
    repo.write(
        path,
        action_text(label, action="resolve a mutated post-merge obligation"),
    )
    repo.commit("mutate the reintroduced candidate action")
    repo.remove(path)
    N = repo.commit("delete the mutated candidate action")
    return Fixture(
        "candidate-side-delete-merge-undo-mutate-delete",
        repo, C, O, merge_commit, N, "blocking-finding", (path,),
        side_resolution=side_resolution,
        merge_commit=merge_commit,
    )


def fixture_candidate_merge_occurrence_ambiguity(root: Path) -> Fixture:
    repo = GitRepository(root)
    label = "candidate-merge-occurrence"
    path = queue_path(label)
    C = create_common(repo, (label,))
    repo.branch("old", C)
    O = feature(repo, "candidate-merge-occurrence-old")

    repo.branch("original-occurrence", C)
    original_claim = claim(repo, label)
    repo.branch("independent-occurrence-staging", C)
    repo.write(path, action_text(label, status="in-repair"))
    repo.run("add", "-A")
    independent_tree = repo.run("write-tree").stdout.strip()
    independent_occurrence = repo.commit_tree(
        independent_tree, "create independent in-repair occurrence root"
    )
    merge_commit = repo.commit_tree(
        independent_tree,
        "merge two byte-identical in-repair occurrences",
        independent_occurrence,
        original_claim,
    )
    repo.branch("candidate", merge_commit)
    N = resolve(repo, label)
    return Fixture(
        "candidate-merge-parent-occurrence-ambiguity",
        repo, C, O, merge_commit, N, "blocking-finding", (path,),
        merge_commit=merge_commit,
    )


def fixture_witness_child_sibling_same_id_conflict(root: Path) -> Fixture:
    repo = GitRepository(root)
    action_id = "Q"
    inherited = "same-id-inherited-a"
    conflicting = "same-id-conflicting-b"
    inherited_path = queue_path(inherited)
    R = create_common(repo)

    repo.write(evidence_path(inherited), "# Evidence inherited A: pending\n")
    repo.write(
        inherited_path,
        action_text(inherited, action_id=action_id),
    )
    C = repo.commit("common side adds inherited action A with Action-ID Q")
    repo.branch("old", C)
    O = feature(repo, "same-id-old-tip")

    repo.branch("claimed-a", C)
    claimed_a = claim(repo, inherited)
    repo.branch("conflicting-b", R)
    repo.write(evidence_path(conflicting), "# Evidence conflicting B: pending\n")
    repo.write(
        queue_path(conflicting),
        action_text(
            conflicting,
            action="resolve the conflicting sibling payload B",
            action_id=action_id,
        ),
    )
    conflicting_b = repo.commit(
        "independently add conflicting unclaimed B with Action-ID Q"
    )

    repo.branch("merge-result-staging", claimed_a)
    repo.write(evidence_path(inherited), "# Evidence inherited A: repaired\n")
    repo.remove(inherited_path)
    repo.write("docs/merge-evidence.md", "# Merge evidence changed\n")
    repo.run("add", "-A")
    merge_tree = repo.run("write-tree").stdout.strip()
    merge_commit = repo.commit_tree(
        merge_tree,
        "merge claimed A with conflicting B and delete both",
        claimed_a,
        conflicting_b,
    )
    repo.branch("candidate", merge_commit)
    N = feature(repo, "same-id-candidate-descendant")
    return Fixture(
        "witness-child-sibling-same-id-conflict",
        repo, C, O, merge_commit, N, "blocking-finding",
        (inherited_path,), merge_commit=merge_commit,
        conflicting_parent=conflicting_b,
    )


def finish_merge_origin_fixture(
    repo: GitRepository,
    scenario_id: str,
    label: str,
    C: str,
    expected_verdict: str,
    shared_origin: str | None = None,
    disconnected_origins: tuple[str, ...] = (),
) -> Fixture:
    repo.branch("old", C)
    O = feature(repo, f"{label}-old-tip")
    repo.branch("candidate", C)
    claim(repo, label)
    M = resolve(repo, label)
    N = feature(repo, f"{label}-candidate-descendant")
    findings = (queue_path(label),) if expected_verdict == (
        "blocking-finding"
    ) else ()
    return Fixture(
        scenario_id,
        repo, C, O, M, N, expected_verdict, findings,
        merge_commit=C,
        shared_origin=shared_origin,
        disconnected_origins=disconnected_origins,
    )


def fixture_disconnected_identical_parent_origins(root: Path) -> Fixture:
    repo = GitRepository(root)
    label = "disconnected-parent-origins"
    path = queue_path(label)
    R = create_common(repo)

    repo.branch("independent-a", R)
    repo.write(evidence_path(label), f"# Evidence {label}: pending\n")
    repo.write(path, action_text(label))
    A = repo.commit("independent parent A adds Q")
    repo.branch("independent-b", R)
    repo.write(evidence_path(label), f"# Evidence {label}: pending\n")
    repo.write(path, action_text(label))
    B = repo.commit("independent parent B adds byte-identical Q")

    identical_tree = repo.oid(f"{A}^{{tree}}")
    C = repo.commit_tree(
        identical_tree,
        "merge disconnected byte-identical Q origins",
        A,
        B,
    )
    return finish_merge_origin_fixture(
        repo,
        "disconnected-identical-parent-origins",
        label,
        C,
        "blocking-finding",
        disconnected_origins=(A, B),
    )


def fixture_shared_continuous_parent_origin(root: Path) -> Fixture:
    repo = GitRepository(root)
    label = "shared-parent-origin"
    S = create_common(repo, (label,))

    repo.branch("carrying-a", S)
    A = feature(repo, "shared-origin-parent-a")
    repo.branch("carrying-b", S)
    B = feature(repo, "shared-origin-parent-b")

    repo.branch("shared-origin-merge-staging", A)
    repo.write(
        "features/shared-origin-parent-b.md",
        "# Feature shared-origin-parent-b\n",
    )
    repo.run("add", "-A")
    merge_tree = repo.run("write-tree").stdout.strip()
    C = repo.commit_tree(
        merge_tree,
        "merge parents carrying one shared continuous Q",
        A,
        B,
    )
    return finish_merge_origin_fixture(
        repo,
        "shared-continuous-parent-origin",
        label,
        C,
        "no-finding",
        shared_origin=S,
    )


def fixture_repeated_incarnation(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("repeated",))
    repo.branch("old", C)
    O = feature(repo, "repeated-old")
    repo.branch("candidate", C)
    claim(repo, "repeated")
    M = resolve(repo, "repeated", "resolve first repeated incarnation")
    repo.write(evidence_path("repeated"), "# Evidence repeated: pending again\n")
    repo.write(queue_path("repeated"), action_text("repeated"))
    repo.commit("recreate the identical repeated action")
    claim(repo, "repeated")
    repo.write(evidence_path("repeated"), "# Evidence repeated: repaired again\n")
    repo.remove(queue_path("repeated"))
    N = repo.commit("resolve second repeated incarnation")
    return Fixture(
        "repeated-incarnation-ambiguity", repo, C, O, M, N,
        "blocking-finding", (queue_path("repeated"),),
    )


def fixture_long_history(root: Path) -> Fixture:
    repo = GitRepository(root)
    C = create_common(repo, ("long",))
    repo.branch("old", C)
    O = feature(repo, "long-old")
    repo.branch("candidate", C)
    for index in range(32):
        feature(repo, f"long-base-{index:02d}")
    claim(repo, "long")
    M = resolve(repo, "long")
    N = feature(repo, "long-old")
    return Fixture("long-history-valid-resolution", repo, C, O, M, N, "no-finding")


BASE_FIXTURES = (
    fixture_s1,
    fixture_s2,
    fixture_s3,
    fixture_s4,
    fixture_s5,
    fixture_s7,
    fixture_s8,
    fixture_s9_unrelated,
    fixture_s9_not_commit,
    fixture_s9_missing,
    fixture_s10,
    fixture_compact_valid_at_n,
    fixture_activation_laundering,
    fixture_claimed_tip_laundering,
    fixture_independent_identical_incarnation,
    fixture_old_delete_recreate_identical,
    fixture_old_legal_resolve_recreate_identical,
    fixture_old_rename_round_trip,
    fixture_old_identity_mutation_round_trip,
    fixture_candidate_side_delete_merge_undo_mutate_delete,
    fixture_candidate_merge_occurrence_ambiguity,
    fixture_witness_child_sibling_same_id_conflict,
    fixture_disconnected_identical_parent_origins,
    fixture_shared_continuous_parent_origin,
    fixture_repeated_incarnation,
    fixture_long_history,
)


def measured_git(repo: GitRepository, metrics: Metrics, *arguments):
    metrics.git_processes += 1
    return repo.run(*arguments)


def queue_paths_at(repo: GitRepository, revision: str, metrics: Metrics):
    metrics.scanner_tree_entry_reads += 1
    result = measured_git(
        repo,
        metrics,
        "--no-replace-objects",
        "ls-tree",
        "-r",
        "--name-only",
        revision,
        "--",
        "message-queue/needs-agent/requests",
        "message-queue/needs-human",
    )
    return tuple(line for line in result.stdout.splitlines() if line.endswith(".md"))


def text_at(revision: str, path: str, metrics: Metrics):
    metrics.scanner_tree_entry_reads += 1
    artifact = RECONCILE.git_artifact_bytes_at(revision, path)
    if artifact is None:
        return None
    return RECONCILE.decode_utf8_artifact(artifact, f"`{path}` at {revision}")


def action_identity(path: str, text: str):
    return RECONCILE.queue_action_identity(path, text)


def declared_action_id(text: str):
    """Return the POC's explicit cross-path logical ID, when one exists."""

    return RECONCILE.text_fields(text).get("Action-ID", "").strip() or None


def same_id_occurrences(
    repo: GitRepository,
    revision: str,
    path: str,
    old_text: str,
    metrics: Metrics,
):
    action_id = declared_action_id(old_text)
    if action_id is None:
        return ()
    target_identity = action_identity(path, old_text)
    occurrences = []
    for candidate in queue_paths_at(repo, revision, metrics):
        candidate_text = text_at(revision, candidate, metrics)
        if candidate_text is None or declared_action_id(candidate_text) != action_id:
            continue
        occurrences.append({
            "action_id": action_id,
            "path": candidate,
            "payload": (
                "matching"
                if action_identity(candidate, candidate_text) == target_identity
                else "conflicting"
            ),
        })
    return tuple(occurrences)


def alternate_lineage_paths(
    repo: GitRepository,
    revision: str,
    path: str,
    old_text: str,
    metrics: Metrics,
):
    target = action_identity(path, old_text)
    matches = []
    for candidate in queue_paths_at(repo, revision, metrics):
        if candidate == path:
            continue
        candidate_text = text_at(revision, candidate, metrics)
        if candidate_text is not None and action_identity(
            candidate, candidate_text
        ) == target:
            matches.append(candidate)
    return tuple(matches)


def old_only_commits(
    repo: GitRepository,
    old_tip: str,
    merge_bases: Iterable[str],
    metrics: Metrics,
):
    bases = tuple(merge_bases)
    result = measured_git(
        repo,
        metrics,
        "--no-replace-objects",
        "rev-list",
        "--reverse",
        "--topo-order",
        old_tip,
        "--not",
        *bases,
    )
    commits = tuple(result.stdout.splitlines())
    metrics.old_commits_scanned += len(commits)
    return commits


def old_edge_event(before_state, after_state, before_alternates, after_alternates):
    if before_state == "matching" and after_state == "absent":
        return "rename-ambiguity" if after_alternates else "deletion"
    if before_state == "absent" and after_state == "matching":
        return "rename-ambiguity" if before_alternates else "reintroduction"
    if before_state == "matching" and after_state == "different":
        return "identity-mutation"
    if before_state == "different" and after_state == "matching":
        return "identity-reintroduction"
    if before_state == "absent" and after_state == "absent":
        return "lineage-absent"
    return "identity-divergence"


def old_lineage(
    repo: GitRepository,
    old_tip: str,
    merge_bases: Iterable[str],
    path: str,
    old_text: str,
    metrics: Metrics,
    enforce_edge_continuity: bool,
):
    old_identity = action_identity(path, old_text)
    bases_tuple = tuple(merge_bases)
    base_texts = []
    bases = []
    for base in bases_tuple:
        base_text = text_at(base, path, metrics)
        base_texts.append(base_text)
        bases.append(None if base_text is None else action_identity(path, base_text))
    if not bases or all(identity is None for identity in bases):
        endpoint_lineage = "old-tip-authored"
    elif all(identity == old_identity for identity in bases):
        endpoint_lineage = "inherited-unchanged-on-old-tip"
    else:
        endpoint_lineage = "old-tip-authored-or-mutated"

    commits = old_only_commits(repo, old_tip, bases_tuple, metrics)
    allowed_parents = set(commits) | set(bases_tuple)
    breaks = []
    for commit in commits:
        for parent in RECONCILE.revision_parents(
            commit, f"old-side parents of {commit}"
        ):
            if parent not in allowed_parents:
                continue
            metrics.old_parent_edges_scanned += 1
            before = text_at(parent, path, metrics)
            after = text_at(commit, path, metrics)
            before_state = (
                "absent" if before is None else
                "matching" if action_identity(path, before) == old_identity else
                "different"
            )
            after_state = (
                "absent" if after is None else
                "matching" if action_identity(path, after) == old_identity else
                "different"
            )
            if before_state == "matching" and after_state == "matching":
                continue
            before_alternates = alternate_lineage_paths(
                repo, parent, path, old_text, metrics
            )
            after_alternates = alternate_lineage_paths(
                repo, commit, path, old_text, metrics
            )
            breaks.append({
                "after": after_state,
                "before": before_state,
                "child": commit,
                "event": old_edge_event(
                    before_state, after_state,
                    before_alternates, after_alternates,
                ),
                "parent": parent,
                "possible_prior_paths": before_alternates,
                "possible_result_paths": after_alternates,
            })
    lineage = endpoint_lineage
    if enforce_edge_continuity and breaks and endpoint_lineage == (
        "inherited-unchanged-on-old-tip"
    ):
        lineage = "old-tip-discontinuous-incarnation"
    endpoint_blob_equal = bool(base_texts) and all(
        base_text == old_text for base_text in base_texts
    )
    return lineage, endpoint_lineage, endpoint_blob_equal, breaks


def candidate_commits(
    repo: GitRepository, old_tip: str, new_head: str, metrics: Metrics
):
    result = measured_git(
        repo,
        metrics,
        "--no-replace-objects",
        "rev-list",
        "--reverse",
        "--topo-order",
        new_head,
        "--not",
        old_tip,
    )
    commits = tuple(result.stdout.splitlines())
    metrics.candidate_commits = len(commits)
    return commits


def candidate_action_state(
    repo: GitRepository,
    revision: str,
    path: str,
    old_text: str,
    metrics: Metrics,
):
    target_identity = action_identity(path, old_text)
    current = text_at(revision, path, metrics)
    occurrences = same_id_occurrences(
        repo, revision, path, old_text, metrics
    )
    if declared_action_id(old_text) is not None:
        exact = [
            occurrence for occurrence in occurrences
            if occurrence["payload"] == "matching"
        ]
        conflicting = [
            occurrence for occurrence in occurrences
            if occurrence["payload"] == "conflicting"
        ]
        alternates = tuple(
            occurrence["path"] for occurrence in exact
            if occurrence["path"] != path
        )
        if len(occurrences) > 1:
            state = "ambiguous"
        elif conflicting:
            state = "conflicting-id"
        elif exact and exact[0]["path"] == path:
            state = "matching"
        elif exact:
            state = "renamed"
        elif current is None:
            state = "absent"
        else:
            state = "different"
        return {
            "alternate_paths": alternates,
            "same_id_occurrences": occurrences,
            "state": state,
        }
    alternates = alternate_lineage_paths(
        repo, revision, path, old_text, metrics
    )
    if alternates:
        state = "renamed" if current is None else "ambiguous"
    elif current is None:
        state = "absent"
    elif action_identity(path, current) == target_identity:
        state = "matching"
    else:
        state = "different"
    return {
        "alternate_paths": alternates,
        "same_id_occurrences": (),
        "state": state,
    }


def continuous_occurrence_origin(
    repo: GitRepository,
    revision: str,
    path: str,
    old_text: str,
    metrics: Metrics,
    cache,
):
    cached = cache.get(revision)
    if cached is not None:
        return cached
    metrics.origin_proof_commits_scanned += 1
    state = candidate_action_state(
        repo, revision, path, old_text, metrics
    )
    if state["state"] != "matching":
        result = {
            "origins": (),
            "problem": f"{revision} is {state['state']}, not one exact occurrence",
        }
        cache[revision] = result
        return result

    parents = RECONCILE.revision_parents(
        revision, f"continuous-origin parents of {revision}"
    )
    parent_occurrences = []
    for parent in parents:
        metrics.origin_proof_parent_edges_scanned += 1
        parent_occurrences.append({
            "oid": parent,
            **candidate_action_state(repo, parent, path, old_text, metrics),
        })
    hazards = [
        occurrence for occurrence in parent_occurrences
        if occurrence["state"] not in {"absent", "matching"}
    ]
    if hazards:
        result = {
            "origins": (),
            "problem": "an ancestor parent carries a conflicting or unproven occurrence",
        }
        cache[revision] = result
        return result
    carrying = [
        occurrence for occurrence in parent_occurrences
        if occurrence["state"] == "matching"
    ]
    if not carrying:
        result = {"origins": (revision,), "problem": None}
        cache[revision] = result
        return result

    parent_results = [
        continuous_occurrence_origin(
            repo, occurrence["oid"], path, old_text, metrics, cache
        )
        for occurrence in carrying
    ]
    if any(result["problem"] is not None for result in parent_results):
        result = {
            "origins": (),
            "problem": "an ancestor carrying parent has no continuous origin proof",
        }
        cache[revision] = result
        return result
    if len(parent_results) == 1:
        result = {
            "origins": parent_results[0]["origins"],
            "problem": None,
        }
        cache[revision] = result
        return result

    shared = set(parent_results[0]["origins"])
    for parent_result in parent_results[1:]:
        shared.intersection_update(parent_result["origins"])
    result = {
        "origins": tuple(sorted(shared)),
        "problem": (
            None if shared
            else "matching merge parents have disconnected occurrence origins"
        ),
    }
    cache[revision] = result
    return result


def shared_continuous_origin_proof(
    repo: GitRepository,
    parent_occurrences,
    path: str,
    old_text: str,
    metrics: Metrics,
    cache,
    enforce_shared_origin: bool,
):
    carrying = [
        occurrence for occurrence in parent_occurrences
        if occurrence["state"] == "matching"
    ]
    if not enforce_shared_origin:
        return {
            "mode": "endpoint-equality-only-disabled-guard",
            "parent_origins": [
                {"oid": occurrence["oid"], "origins": (), "problem": None}
                for occurrence in carrying
            ],
            "proven": True,
            "shared_origins": (),
        }
    parent_origins = []
    for occurrence in carrying:
        origin = continuous_occurrence_origin(
            repo, occurrence["oid"], path, old_text, metrics, cache
        )
        parent_origins.append({"oid": occurrence["oid"], **origin})
    shared = set(parent_origins[0]["origins"])
    for origin in parent_origins[1:]:
        shared.intersection_update(origin["origins"])
    proven = bool(shared) and all(
        origin["problem"] is None for origin in parent_origins
    )
    return {
        "mode": "continuous-origin-intersection",
        "parent_origins": parent_origins,
        "proven": proven,
        "shared_origins": tuple(sorted(shared)) if proven else (),
    }


def witness_child_parent_breaks(
    repo: GitRepository,
    witness_parent: str,
    witness_child: str,
    path: str,
    old_text: str,
    metrics: Metrics,
    origin_cache,
    enforce_shared_origin: bool,
):
    parents = RECONCILE.revision_parents(
        witness_child, f"witness-child parents of {witness_child}"
    )
    parent_occurrences = []
    for parent in parents:
        metrics.witness_child_parent_edges_scanned += 1
        parent_occurrences.append({
            "oid": parent,
            **candidate_action_state(repo, parent, path, old_text, metrics),
        })
    by_oid = {
        occurrence["oid"]: occurrence for occurrence in parent_occurrences
    }
    selected = by_oid.get(witness_parent)
    breaks = []
    proofs = []
    if selected is None or selected["state"] != "matching":
        breaks.append({
            "child": witness_child,
            "event": "witness-parent-occurrence-not-unique",
            "parent_occurrences": parent_occurrences,
            "selected_parent": witness_parent,
        })
    for occurrence in parent_occurrences:
        if occurrence["oid"] == witness_parent or occurrence["state"] == "absent":
            continue
        state = occurrence["state"]
        if state == "conflicting-id":
            event = "witness-child-sibling-same-id-conflict"
        elif state == "ambiguous":
            event = "witness-child-sibling-multiple-copies"
        elif state == "matching":
            continue
        elif state == "renamed":
            event = "witness-child-sibling-occurrence-ambiguity"
        else:
            event = "witness-child-sibling-unproven-occurrence"
        breaks.append({
            "child": witness_child,
            "event": event,
            "parent_occurrence": occurrence,
            "selected_parent": witness_parent,
        })
    carrying = [
        occurrence for occurrence in parent_occurrences
        if occurrence["state"] == "matching"
    ]
    if selected is not None and selected["state"] == "matching" and len(
        carrying
    ) > 1:
        proof = shared_continuous_origin_proof(
            repo,
            parent_occurrences,
            path,
            old_text,
            metrics,
            origin_cache,
            enforce_shared_origin,
        )
        proofs.append({"child": witness_child, **proof})
        if not proof["proven"]:
            breaks.append({
                "child": witness_child,
                "event": "witness-child-disconnected-occurrence-origins",
                "origin_proof": proof,
                "parent_occurrences": parent_occurrences,
                "selected_parent": witness_parent,
            })
    return breaks, proofs


def pre_witness_occurrence_breaks(
    repo: GitRepository,
    witness_parent: str,
    path: str,
    old_text: str,
    metrics: Metrics,
    origin_cache,
    enforce_shared_origin: bool,
):
    breaks = []
    proofs = []
    revision = witness_parent
    seen = set()
    while revision not in seen:
        seen.add(revision)
        metrics.pre_witness_commits_scanned += 1
        parents = RECONCILE.revision_parents(
            revision, f"pre-witness parents of {revision}"
        )
        if not parents:
            break
        parent_occurrences = []
        for parent in parents:
            metrics.pre_witness_parent_edges_scanned += 1
            state = candidate_action_state(
                repo, parent, path, old_text, metrics
            )
            parent_occurrences.append({"oid": parent, **state})
        hazards = [
            occurrence for occurrence in parent_occurrences
            if occurrence["state"] in {
                "ambiguous", "conflicting-id", "different", "renamed"
            }
        ]
        if hazards:
            breaks.append({
                "child": revision,
                "event": "pre-witness-parent-occurrence-not-proven",
                "parent_occurrences": parent_occurrences,
            })
            break
        matches = [
            occurrence for occurrence in parent_occurrences
            if occurrence["state"] == "matching"
        ]
        if len(matches) > 1:
            proof = shared_continuous_origin_proof(
                repo,
                parent_occurrences,
                path,
                old_text,
                metrics,
                origin_cache,
                enforce_shared_origin,
            )
            proofs.append({"child": revision, **proof})
            if not proof["proven"]:
                breaks.append({
                    "child": revision,
                    "event": "multi-parent-occurrence-ambiguity",
                    "origin_proof": proof,
                    "parent_occurrences": parent_occurrences,
                })
                break
            if proof["shared_origins"]:
                revision = proof["shared_origins"][0]
                continue
            break
        if not matches:
            break
        revision = matches[0]["oid"]
    return breaks, proofs


def post_witness_event(parent_state, child_state, merge):
    before = parent_state["state"]
    after = child_state["state"]
    if "conflicting-id" in (before, after):
        return "same-id-conflicting-incarnation"
    if "ambiguous" in (before, after):
        return "multiple-same-id-copies"
    if "renamed" in (before, after) or "ambiguous" in (before, after):
        return "rename-ambiguity"
    if merge and before != "absent":
        return "merge-sibling-carries-action"
    if after == "matching":
        return (
            "merge-result-reintroduction-or-survival"
            if merge else "reintroduction-or-survival"
        )
    if after == "different":
        return "identity-mutation-or-reintroduction"
    if after == "absent" and before != "absent":
        return "later-deletion"
    return "post-witness-continuity-unknown"


def post_witness_continuity_breaks(
    repo: GitRepository,
    witness_parent: str,
    witness_child: str,
    new_head: str,
    path: str,
    old_text: str,
    metrics: Metrics,
):
    breaks = []
    deletion_result = candidate_action_state(
        repo, witness_child, path, old_text, metrics
    )
    if deletion_result["state"] != "absent":
        breaks.append({
            "after": deletion_result,
            "before": candidate_action_state(
                repo, witness_parent, path, old_text, metrics
            ),
            "child": witness_child,
            "event": "deletion-result-rename-ambiguity",
            "parent": witness_parent,
        })

    result = measured_git(
        repo,
        metrics,
        "--no-replace-objects",
        "rev-list",
        "--reverse",
        "--topo-order",
        "--ancestry-path",
        f"{witness_child}..{new_head}",
    )
    descendants = tuple(result.stdout.splitlines())
    metrics.post_witness_commits_scanned += len(descendants)
    for commit in descendants:
        parents = RECONCILE.revision_parents(
            commit, f"post-witness parents of {commit}"
        )
        child_state = candidate_action_state(
            repo, commit, path, old_text, metrics
        )
        for parent in parents:
            metrics.post_witness_parent_edges_scanned += 1
            parent_state = candidate_action_state(
                repo, parent, path, old_text, metrics
            )
            if parent_state["state"] == "absent" and child_state["state"] == (
                "absent"
            ):
                continue
            breaks.append({
                "after": child_state,
                "before": parent_state,
                "child": commit,
                "event": post_witness_event(
                    parent_state, child_state, len(parents) > 1
                ),
                "parent": parent,
            })
    return breaks


def deletion_witnesses(
    repo: GitRepository,
    commits: Iterable[str],
    new_head: str,
    path: str,
    old_text: str,
    metrics: Metrics,
    enforce_shared_origin: bool,
):
    old_identity = action_identity(path, old_text)
    witnesses = []
    for commit in commits:
        parents = RECONCILE.revision_parents(commit, f"parents of {commit}")
        for parent in parents:
            metrics.candidate_parent_edges += 1
            before = text_at(parent, path, metrics)
            after = text_at(commit, path, metrics)
            if before is None or after is not None:
                continue
            if action_identity(path, before) != old_identity:
                continue
            metrics.semantic_validation_calls += 1
            problem = RECONCILE.queue_deletion_problem(
                path, before, parent, commit
            )
            origin_cache = {}
            witness_parent_breaks, witness_parent_origin_proofs = (
                witness_child_parent_breaks(
                    repo,
                    parent,
                    commit,
                    path,
                    old_text,
                    metrics,
                    origin_cache,
                    enforce_shared_origin,
                )
            )
            occurrence_breaks, pre_witness_origin_proofs = (
                pre_witness_occurrence_breaks(
                    repo,
                    parent,
                    path,
                    old_text,
                    metrics,
                    origin_cache,
                    enforce_shared_origin,
                )
            )
            continuity_breaks = post_witness_continuity_breaks(
                repo, parent, commit, new_head, path, old_text, metrics
            )
            witnesses.append(
                {
                    "causally_continuous_to_N": not continuity_breaks,
                    "child": commit,
                    "deletion_parent_unambiguous": not witness_parent_breaks,
                    "occurrence_unambiguous": not occurrence_breaks,
                    "parent": parent,
                    "post_witness_breaks": continuity_breaks,
                    "pre_witness_occurrence_breaks": occurrence_breaks,
                    "pre_witness_origin_proofs": pre_witness_origin_proofs,
                    "problem": problem,
                    "witness_child_parent_breaks": witness_parent_breaks,
                    "witness_child_parent_origin_proofs": (
                        witness_parent_origin_proofs
                    ),
                }
            )
    return witnesses


def classification_reason(items, fast_forward=False):
    if fast_forward:
        return "The displaced tip is an ancestor of the candidate; no divergent continuity edge exists."
    if not items:
        return "No live old-tip queue action disappeared across the replacement."
    parts = []
    for path, item in sorted(items.items()):
        verdict = item["evidence_verdict"]
        if verdict == "valid-real-edge":
            witness = item["witnesses"][0]
            parts.append(
                f"{path} is resolved by candidate-side edge "
                f"{witness['parent']}->{witness['child']}, which passes the existing lifecycle/evidence validator"
            )
        elif verdict == "candidate-carries-action":
            parts.append(f"{path} remains live at the candidate tip")
        elif verdict.startswith("invalid-real-edge"):
            parts.append(f"{path} has a real deletion edge but it is unauthorized: {item['problem']}")
        elif verdict == "invalid-post-witness-continuity":
            parts.append(
                f"{path} has a locally valid deletion edge, but a descendant "
                "edge reintroduces, rewrites, renames, or deletes the action "
                "before the candidate tip"
            )
        elif verdict == "invalid-witness-occurrence-ambiguity":
            parts.append(
                f"{path} has a locally valid deletion edge, but its claimed "
                "occurrence is ambiguous across multiple merge parents"
            )
        elif verdict == "invalid-witness-child-parent-ambiguity":
            parts.append(
                f"{path} has a locally valid deletion edge, but another parent "
                "of the deletion commit carries a conflicting or unproven "
                "incarnation"
            )
        elif verdict == "different-incarnation-witness":
            parts.append(
                f"{path} has a valid candidate-side deletion edge for byte-identical "
                "content, but the old-tip obligation is not one uninterrupted "
                "incarnation from the shared boundary"
            )
        elif verdict == "ambiguous-real-edges":
            parts.append(f"{path} has multiple matching deletion edges, so the prototype fails closed")
        elif verdict == "rewritten-live-action":
            parts.append(f"{path} remains at the candidate path with a different action identity")
        else:
            parts.append(f"{path} has no matching candidate-side resolution edge")
    return "; ".join(parts) + "."


def classify(
    fixture: Fixture,
    enforce_incarnation_provenance=True,
    enforce_old_edge_continuity=True,
    enforce_witness_child_parents=True,
    enforce_pre_witness_occurrence=True,
    enforce_post_witness_continuity=True,
    enforce_shared_occurrence_origin=True,
):
    metrics = Metrics()
    items = {}
    with reconciler_repository(fixture.repo.root), count_reconciler_git(metrics):
        try:
            RECONCILE.validate_displaced_tip(
                fixture.O, f"{fixture.C}...{fixture.N}"
            )
            ancestry_code, ancestry_detail = RECONCILE.git_ancestry_probe(
                fixture.O, fixture.N
            )
            if ancestry_code == 0:
                return {
                    "scenario": fixture.scenario_id,
                    "C": fixture.C,
                    "O": fixture.O,
                    "M": fixture.M,
                    "N": fixture.N,
                    "classification": "no-finding",
                    "authoring_lineage": "fast-forward-extension",
                    "evidence_verdict": "not-needed",
                    "expected_verdict": fixture.expected_verdict,
                    "findings": [],
                    "reason": classification_reason({}, fast_forward=True),
                    "metrics": metrics.as_dict(),
                }
            if ancestry_code != 1:
                raise RECONCILE.GitSnapshotError(
                    ancestry_detail or "could not compare the displaced tip"
                )

            merge_base_result = measured_git(
                fixture.repo,
                metrics,
                "--no-replace-objects",
                "merge-base",
                "--all",
                fixture.O,
                fixture.N,
            )
            merge_bases = tuple(merge_base_result.stdout.splitlines())
            if not merge_bases:
                raise RECONCILE.GitSnapshotError(
                    "displaced tip and candidate have no merge base"
                )

            old_paths = queue_paths_at(fixture.repo, fixture.O, metrics)
            new_paths = set(queue_paths_at(fixture.repo, fixture.N, metrics))
            commits = candidate_commits(
                fixture.repo, fixture.O, fixture.N, metrics
            )
            for path in old_paths:
                old_text = text_at(fixture.O, path, metrics)
                if old_text is None:
                    raise RECONCILE.GitSnapshotError(
                        f"could not read old-tip action `{path}`"
                    )
                (
                    lineage,
                    endpoint_lineage,
                    endpoint_blob_equal,
                    old_edge_breaks,
                ) = old_lineage(
                    fixture.repo,
                    fixture.O,
                    merge_bases,
                    path,
                    old_text,
                    metrics,
                    enforce_old_edge_continuity,
                )
                if path in new_paths:
                    new_text = text_at(fixture.N, path, metrics)
                    if new_text is not None and action_identity(
                        path, new_text
                    ) == action_identity(path, old_text):
                        items[path] = {
                            "authoring_lineage": lineage,
                            "endpoint_blob_equal": endpoint_blob_equal,
                            "endpoint_lineage": endpoint_lineage,
                            "evidence_verdict": "candidate-carries-action",
                            "old_edge_breaks": old_edge_breaks,
                            "problem": None,
                            "witnesses": [],
                            "finding": False,
                        }
                    else:
                        items[path] = {
                            "authoring_lineage": lineage,
                            "endpoint_blob_equal": endpoint_blob_equal,
                            "endpoint_lineage": endpoint_lineage,
                            "evidence_verdict": "rewritten-live-action",
                            "old_edge_breaks": old_edge_breaks,
                            "problem": "candidate path carries a distinct action identity",
                            "witnesses": [],
                            "finding": True,
                        }
                    continue
                witnesses = deletion_witnesses(
                    fixture.repo,
                    commits,
                    fixture.N,
                    path,
                    old_text,
                    metrics,
                    enforce_shared_occurrence_origin,
                )
                metrics.synthetic_control_calls += 1
                synthetic_edge_problem = RECONCILE.queue_deletion_problem(
                    path, old_text, fixture.O, fixture.N
                )
                valid = [witness for witness in witnesses if witness["problem"] is None]
                if len(witnesses) == 1 and len(valid) == 1:
                    witness = witnesses[0]
                    if enforce_witness_child_parents and witness[
                        "witness_child_parent_breaks"
                    ]:
                        verdict = "invalid-witness-child-parent-ambiguity"
                        problem = (
                            "a deletion-commit parent carries the same logical "
                            "Action-ID through a conflicting, duplicated, renamed, "
                            "or otherwise unproven occurrence"
                        )
                        finding = True
                    elif enforce_pre_witness_occurrence and witness[
                        "pre_witness_occurrence_breaks"
                    ]:
                        verdict = "invalid-witness-occurrence-ambiguity"
                        problem = (
                            "the candidate deletion's claim receipt is ambiguous "
                            "across multiple parent occurrences"
                        )
                        finding = True
                    elif enforce_post_witness_continuity and witness[
                        "post_witness_breaks"
                    ]:
                        verdict = "invalid-post-witness-continuity"
                        problem = (
                            "the candidate-side deletion does not remain causally "
                            "absent through every descendant edge to N"
                        )
                        finding = True
                    elif enforce_incarnation_provenance and lineage != (
                        "inherited-unchanged-on-old-tip"
                    ):
                        verdict = "different-incarnation-witness"
                        if lineage == "old-tip-discontinuous-incarnation":
                            problem = (
                                "old-tip action identity was deleted, recreated, "
                                "renamed ambiguously, or reintroduced after mutation"
                            )
                        else:
                            problem = (
                                "old-tip action was authored or changed after every "
                                "shared merge boundary"
                            )
                        finding = True
                    else:
                        verdict = "valid-real-edge"
                        problem = None
                        finding = False
                elif len(witnesses) > 1:
                    verdict = "ambiguous-real-edges"
                    problem = "multiple matching deletion witnesses"
                    finding = True
                elif witnesses:
                    problem = witnesses[0]["problem"]
                    verdict = "invalid-real-edge: " + str(problem)
                    finding = True
                else:
                    verdict = "no-matching-witness"
                    problem = "no candidate-side deletion edge resolved this action"
                    finding = True
                items[path] = {
                    "authoring_lineage": lineage,
                    "endpoint_blob_equal": endpoint_blob_equal,
                    "endpoint_lineage": endpoint_lineage,
                    "evidence_verdict": verdict,
                    "old_edge_breaks": old_edge_breaks,
                    "problem": problem,
                    "witnesses": witnesses,
                    "synthetic_edge_problem": synthetic_edge_problem,
                    "finding": finding,
                }
            if fixture.old_resolution is not None:
                path = fixture.expected_findings[0]
                parents = RECONCILE.revision_parents(
                    fixture.old_resolution,
                    f"old-side resolution parents of {fixture.old_resolution}",
                )
                if len(parents) != 1:
                    raise RECONCILE.GitSnapshotError(
                        "old-side resolution control is not a one-parent edge"
                    )
                prior = parents[0]
                before = text_at(prior, path, metrics)
                if before is None:
                    raise RECONCILE.GitSnapshotError(
                        "old-side resolution control lost its parent action"
                    )
                metrics.semantic_validation_calls += 1
                items[path]["old_resolution_witness"] = {
                    "child": fixture.old_resolution,
                    "parent": prior,
                    "problem": RECONCILE.queue_deletion_problem(
                        path, before, prior, fixture.old_resolution
                    ),
                }
            findings = sorted(
                path for path, item in items.items() if item["finding"]
            )
            classification = "blocking-finding" if findings else "no-finding"
            evidence = {
                path: item["evidence_verdict"] for path, item in sorted(items.items())
            }
            lineage = {
                path: item["authoring_lineage"] for path, item in sorted(items.items())
            }
            return {
                "scenario": fixture.scenario_id,
                "C": fixture.C,
                "O": fixture.O,
                "M": fixture.M,
                "N": fixture.N,
                "classification": classification,
                "authoring_lineage": lineage,
                "evidence_verdict": evidence,
                "expected_verdict": fixture.expected_verdict,
                "findings": findings,
                "reason": classification_reason(items),
                "items": items,
                "metrics": metrics.as_dict(),
            }
        except (RECONCILE.GitSnapshotError, RuntimeError, ValueError) as error:
            return {
                "scenario": fixture.scenario_id,
                "C": fixture.C,
                "O": fixture.O,
                "M": fixture.M,
                "N": fixture.N,
                "classification": "snapshot-error",
                "authoring_lineage": "unavailable",
                "evidence_verdict": "fail-closed",
                "expected_verdict": fixture.expected_verdict,
                "findings": [],
                "reason": str(error),
                "metrics": metrics.as_dict(),
            }


def assert_full_oids(result):
    for name in ("C", "O", "M", "N"):
        value = result[name]
        if len(value) not in OID_LENGTHS or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise AssertionError(f"{result['scenario']} emitted invalid {name}: {value}")


def verify_result(fixture: Fixture, result):
    assert_full_oids(result)
    problems = []
    if result["classification"] != fixture.expected_verdict:
        problems.append(
            f"expected {fixture.expected_verdict}, got {result['classification']}"
        )
    if tuple(result["findings"]) != tuple(sorted(fixture.expected_findings)):
        problems.append(
            f"expected findings {sorted(fixture.expected_findings)}, got {result['findings']}"
        )
    if fixture.scenario_id == "compact-valid-deletion-at-N":
        item = result["items"][queue_path("compact")]
        if len(item["witnesses"]) != 1 or item["witnesses"][0]["child"] != fixture.N:
            problems.append("compact deletion was not attributed to candidate head N")
    if fixture.scenario_id == "activation-laundering":
        item = result["items"][queue_path("activation-launder")]
        if "not committed as in-repair" not in str(item["problem"]):
            problems.append("pre-v1 supplier deletion was not force-validated")
    if fixture.scenario_id == "claimed-tip-synthetic-evidence-laundering":
        item = result["items"][queue_path("claimed-launder")]
        if item["synthetic_edge_problem"] is not None:
            problems.append("synthetic O->N control no longer demonstrates laundering")
        if "not committed as in-repair" not in str(item["problem"]):
            problems.append("real candidate deletion edge did not reject laundering")
    if fixture.scenario_id == "independent-byte-identical-incarnation":
        item = result["items"][queue_path("independent")]
        if item["authoring_lineage"] != "old-tip-authored":
            problems.append("independent old-tip action was not attributed after C")
        if item["evidence_verdict"] != "different-incarnation-witness":
            problems.append("byte-identical candidate incarnation borrowed authorization")
        if len(item["witnesses"]) != 1 or item["witnesses"][0]["problem"] is not None:
            problems.append("independent candidate lifecycle was not actually valid")
    old_break_expectations = {
        "old-delete-recreate-identical-incarnation": {
            "deletion", "reintroduction",
        },
        "old-legal-resolve-recreate-identical-incarnation": {
            "deletion", "reintroduction",
        },
        "old-rename-round-trip-incarnation-ambiguity": {
            "rename-ambiguity",
        },
        "old-identity-mutation-round-trip-incarnation": {
            "identity-mutation", "identity-reintroduction",
        },
    }
    if fixture.scenario_id in old_break_expectations:
        path = fixture.expected_findings[0]
        item = result["items"][path]
        if item["endpoint_lineage"] != "inherited-unchanged-on-old-tip":
            problems.append("old reincarnation endpoints did not remain identical")
        if not item["endpoint_blob_equal"]:
            problems.append("old reincarnation C/O queue blobs were not byte-identical")
        if item["authoring_lineage"] != "old-tip-discontinuous-incarnation":
            problems.append("old parent-edge continuity break was not binding")
        events = {event["event"] for event in item["old_edge_breaks"]}
        if not old_break_expectations[fixture.scenario_id].issubset(events):
            problems.append("expected old-side continuity breaks were not observed")
        if item["evidence_verdict"] != "different-incarnation-witness":
            problems.append("candidate lifecycle borrowed the recreated old obligation")
        if len(item["witnesses"]) != 1 or item["witnesses"][0]["problem"] is not None:
            problems.append("candidate lifecycle in reincarnation control was not valid")
    if fixture.scenario_id == (
        "old-legal-resolve-recreate-identical-incarnation"
    ):
        item = result["items"][fixture.expected_findings[0]]
        if item["old_resolution_witness"]["problem"] is not None:
            problems.append("old-side resolve-before-recreate lifecycle was not valid")
    if fixture.scenario_id == (
        "candidate-side-delete-merge-undo-mutate-delete"
    ):
        item = result["items"][fixture.expected_findings[0]]
        if item["evidence_verdict"] != "invalid-post-witness-continuity":
            problems.append("non-causal candidate deletion was accepted")
        if len(item["witnesses"]) != 1:
            problems.append("merge-undo fixture did not isolate one deletion witness")
        else:
            witness = item["witnesses"][0]
            if witness["child"] != fixture.side_resolution:
                problems.append("scanner did not select the valid side deletion")
            if witness["problem"] is not None:
                problems.append("side deletion lifecycle was not locally valid")
            if witness["causally_continuous_to_N"]:
                problems.append("side deletion incorrectly remained causal to N")
            events = {
                event["event"] for event in witness["post_witness_breaks"]
            }
            expected_events = {
                "merge-sibling-carries-action",
                "merge-result-reintroduction-or-survival",
                "identity-mutation-or-reintroduction",
                "later-deletion",
            }
            if not expected_events.issubset(events):
                problems.append("post-witness merge/rewrite/delete edges were missed")
            if fixture.merge_commit not in {
                event["child"] for event in witness["post_witness_breaks"]
            }:
                problems.append("merge result was not inspected after the witness")
    if fixture.scenario_id == "candidate-merge-parent-occurrence-ambiguity":
        item = result["items"][fixture.expected_findings[0]]
        if item["evidence_verdict"] != "invalid-witness-occurrence-ambiguity":
            problems.append("multi-parent occurrence ambiguity was accepted")
        if len(item["witnesses"]) != 1:
            problems.append("occurrence fixture did not isolate one deletion witness")
        else:
            witness = item["witnesses"][0]
            if witness["problem"] is not None:
                problems.append("raw production deletion helper did not false-green")
            if witness["occurrence_unambiguous"]:
                problems.append("merge parents were treated as one occurrence")
            events = {
                event["event"]
                for event in witness["pre_witness_occurrence_breaks"]
            }
            if "multi-parent-occurrence-ambiguity" not in events:
                problems.append("multi-parent occurrence event was not emitted")
            if not witness["causally_continuous_to_N"]:
                problems.append("occurrence fixture accidentally tested post-causality")
    if fixture.scenario_id == "witness-child-sibling-same-id-conflict":
        item = result["items"][fixture.expected_findings[0]]
        if item["evidence_verdict"] != (
            "invalid-witness-child-parent-ambiguity"
        ):
            problems.append("same-ID sibling-parent conflict was accepted")
        if len(item["witnesses"]) != 1:
            problems.append("same-ID fixture did not isolate one deletion witness")
        else:
            witness = item["witnesses"][0]
            if witness["problem"] is not None:
                problems.append("raw production deletion helper did not false-green")
            if witness["deletion_parent_unambiguous"]:
                problems.append("deletion child's parent set was treated as unambiguous")
            conflicts = [
                event for event in witness["witness_child_parent_breaks"]
                if event["event"] == (
                    "witness-child-sibling-same-id-conflict"
                )
            ]
            if len(conflicts) != 1:
                problems.append("same-ID sibling conflict event was not isolated")
            elif conflicts[0]["parent_occurrence"]["oid"] != (
                fixture.conflicting_parent
            ):
                problems.append("same-ID conflict was attributed to the wrong parent")
            elif conflicts[0]["parent_occurrence"][
                "same_id_occurrences"
            ] != ({
                "action_id": "Q",
                "path": queue_path("same-id-conflicting-b"),
                "payload": "conflicting",
            },):
                problems.append("same-ID conflict payload/path was not preserved")
            if result["metrics"]["witness_child_parent_edges_scanned"] != 2:
                problems.append("scanner did not inspect both deletion-child parents")
            if witness["pre_witness_occurrence_breaks"]:
                problems.append("fixture accidentally tested pre-witness continuity")
            if witness["post_witness_breaks"]:
                problems.append("fixture accidentally tested post-witness continuity")
    if fixture.scenario_id == "disconnected-identical-parent-origins":
        item = result["items"][fixture.expected_findings[0]]
        if item["evidence_verdict"] != "invalid-witness-occurrence-ambiguity":
            problems.append("disconnected identical origins were treated as one")
        if len(item["witnesses"]) != 1:
            problems.append("disconnected-origin fixture did not isolate one witness")
        else:
            witness = item["witnesses"][0]
            if witness["problem"] is not None:
                problems.append("raw production deletion helper did not false-green")
            proofs = witness["pre_witness_origin_proofs"]
            if len(proofs) != 1 or proofs[0]["proven"]:
                problems.append("disconnected origin proof did not fail closed")
            else:
                parent_origins = {
                    origin["oid"]: tuple(origin["origins"])
                    for origin in proofs[0]["parent_origins"]
                }
                expected = {
                    origin: (origin,) for origin in fixture.disconnected_origins
                }
                if parent_origins != expected:
                    problems.append("independent parent origins were not preserved")
                if proofs[0]["child"] != fixture.C:
                    problems.append("origin proof did not bind the shared boundary C")
    if fixture.scenario_id == "shared-continuous-parent-origin":
        path = queue_path("shared-parent-origin")
        item = result["items"][path]
        if item["evidence_verdict"] != "valid-real-edge":
            problems.append("shared continuous origin remained overblocked")
        if len(item["witnesses"]) != 1:
            problems.append("shared-origin fixture did not isolate one witness")
        else:
            witness = item["witnesses"][0]
            proofs = witness["pre_witness_origin_proofs"]
            if len(proofs) != 1 or not proofs[0]["proven"]:
                problems.append("shared parent origin was not proven")
            elif tuple(proofs[0]["shared_origins"]) != (
                fixture.shared_origin,
            ):
                problems.append("shared origin proof selected the wrong commit")
            if witness["pre_witness_occurrence_breaks"]:
                problems.append("proven shared origin still emitted an ambiguity")
    if fixture.scenario_id == "repeated-incarnation-ambiguity":
        item = result["items"][queue_path("repeated")]
        if len(item["witnesses"]) != 2:
            problems.append("repeated-incarnation fixture did not produce two witnesses")
    if problems:
        raise AssertionError(f"{fixture.scenario_id}: " + "; ".join(problems))


def replay_tree_signature(fixture: Fixture):
    probes = {
        "old_queue_delta_empty": (fixture.C, fixture.O, "message-queue"),
        "replay_queue_delta_empty": (fixture.M, fixture.N, "message-queue"),
    }
    signature = {}
    for name, (before, after, path) in probes.items():
        result = fixture.repo.run(
            "--no-replace-objects", "diff", "--quiet", before, after,
            "--", path, check=False,
        )
        if result.returncode not in (0, 1):
            raise AssertionError(f"replay control could not compare {name}")
        signature[name] = result.returncode == 0
    path = queue_path("s1") if fixture.scenario_id.startswith("S1-") else queue_path("s2")
    absent = fixture.repo.run(
        "--no-replace-objects", "ls-tree", fixture.N, "--", path
    )
    signature["candidate_path_absent"] = not absent.stdout.strip()
    return signature


def executable_controls(fixtures, results):
    controls = []

    independent = fixtures["independent-byte-identical-incarnation"]
    damaged = classify(independent, enforce_incarnation_provenance=False)
    if damaged["classification"] != "no-finding":
        raise AssertionError(
            "damaged incarnation control did not reproduce the false negative"
        )
    controls.append({
        "control": "observed-red-incarnation-provenance",
        "damaged_classification": damaged["classification"],
        "expected": independent.expected_verdict,
        "status": "OBSERVED_RED",
    })

    recreated = fixtures[
        "old-legal-resolve-recreate-identical-incarnation"
    ]
    damaged_old_walk = classify(
        recreated, enforce_old_edge_continuity=False
    )
    recreated_path = queue_path("old-legal-recreate")
    if damaged_old_walk["classification"] != "no-finding":
        raise AssertionError(
            "damaged old-edge control did not reproduce the endpoint false green"
        )
    damaged_item = damaged_old_walk["items"][recreated_path]
    if damaged_item["endpoint_lineage"] != (
        "inherited-unchanged-on-old-tip"
    ):
        raise AssertionError("old-edge control did not retain equal C/O endpoints")
    controls.append({
        "control": "observed-red-old-edge-continuity",
        "damaged_classification": damaged_old_walk["classification"],
        "endpoint_blob_equal": damaged_item["endpoint_blob_equal"],
        "endpoint_lineage": damaged_item["endpoint_lineage"],
        "expected": recreated.expected_verdict,
        "old_edge_events": [
            event["event"] for event in damaged_item["old_edge_breaks"]
        ],
        "status": "OBSERVED_RED",
    })

    merge_undo = fixtures[
        "candidate-side-delete-merge-undo-mutate-delete"
    ]
    damaged_post_witness = classify(
        merge_undo, enforce_post_witness_continuity=False
    )
    merge_undo_path = queue_path("candidate-merge-undo")
    if damaged_post_witness["classification"] != "no-finding":
        raise AssertionError(
            "damaged post-witness control did not reproduce the false green"
        )
    damaged_witness = damaged_post_witness["items"][merge_undo_path][
        "witnesses"
    ][0]
    controls.append({
        "control": "observed-red-post-witness-continuity",
        "damaged_classification": damaged_post_witness["classification"],
        "expected": merge_undo.expected_verdict,
        "merge_commit": merge_undo.merge_commit,
        "post_witness_events": [
            event["event"]
            for event in damaged_witness["post_witness_breaks"]
        ],
        "status": "OBSERVED_RED",
        "witness_child": damaged_witness["child"],
    })

    occurrence = fixtures["candidate-merge-parent-occurrence-ambiguity"]
    damaged_occurrence = classify(
        occurrence, enforce_pre_witness_occurrence=False
    )
    occurrence_path = queue_path("candidate-merge-occurrence")
    if damaged_occurrence["classification"] != "no-finding":
        raise AssertionError(
            "damaged occurrence control did not reproduce the merge false green"
        )
    occurrence_witness = damaged_occurrence["items"][occurrence_path][
        "witnesses"
    ][0]
    controls.append({
        "control": "observed-red-pre-witness-occurrence",
        "damaged_classification": damaged_occurrence["classification"],
        "expected": occurrence.expected_verdict,
        "merge_commit": occurrence.merge_commit,
        "occurrence_events": [
            event["event"]
            for event in occurrence_witness[
                "pre_witness_occurrence_breaks"
            ]
        ],
        "raw_production_problem": occurrence_witness["problem"],
        "status": "OBSERVED_RED",
    })

    sibling_conflict = fixtures[
        "witness-child-sibling-same-id-conflict"
    ]
    damaged_witness_parents = classify(
        sibling_conflict, enforce_witness_child_parents=False
    )
    sibling_path = queue_path("same-id-inherited-a")
    if damaged_witness_parents["classification"] != "no-finding":
        raise AssertionError(
            "damaged witness-child-parent control did not reproduce the false green"
        )
    sibling_witness = damaged_witness_parents["items"][sibling_path][
        "witnesses"
    ][0]
    controls.append({
        "conflicting_parent": sibling_conflict.conflicting_parent,
        "control": "observed-red-witness-child-same-id-conflict",
        "damaged_classification": damaged_witness_parents["classification"],
        "expected": sibling_conflict.expected_verdict,
        "merge_commit": sibling_conflict.merge_commit,
        "raw_production_problem": sibling_witness["problem"],
        "status": "OBSERVED_RED",
        "witness_child_parent_events": [
            event["event"]
            for event in sibling_witness["witness_child_parent_breaks"]
        ],
    })

    disconnected = fixtures["disconnected-identical-parent-origins"]
    damaged_origin_proof = classify(
        disconnected, enforce_shared_occurrence_origin=False
    )
    disconnected_path = queue_path("disconnected-parent-origins")
    if damaged_origin_proof["classification"] != "no-finding":
        raise AssertionError(
            "damaged origin proof did not union disconnected identical parents"
        )
    disconnected_witness = damaged_origin_proof["items"][
        disconnected_path
    ]["witnesses"][0]
    origin_proofs = disconnected_witness["pre_witness_origin_proofs"]
    if len(origin_proofs) != 1 or origin_proofs[0]["mode"] != (
        "endpoint-equality-only-disabled-guard"
    ):
        raise AssertionError("damaged origin proof did not expose its weak mode")
    controls.append({
        "control": "observed-red-disconnected-identical-parent-origins",
        "damaged_classification": damaged_origin_proof["classification"],
        "disconnected_origins": disconnected.disconnected_origins,
        "expected": disconnected.expected_verdict,
        "merge_commit": disconnected.C,
        "origin_mode": origin_proofs[0]["mode"],
        "raw_production_problem": disconnected_witness["problem"],
        "status": "OBSERVED_RED",
    })

    s2 = fixtures["S2-invalid-base-deletion"]
    with reconciler_repository(s2.repo.root):
        accepts_bad = RECONCILE.candidate_paths_match_other_parent(
            s2.O, s2.N, (queue_path("s2"),)
        )
    if not accepts_bad:
        raise AssertionError(
            "candidate_paths_match_other_parent no longer accepts the S2 control"
        )
    controls.append({
        "accepted_evidence_free_deletion": accepts_bad,
        "control": "production-other-parent-is-evidence-blind",
        "real_edge_problem": results["S2-invalid-base-deletion"]["items"][
            queue_path("s2")
        ]["problem"],
        "status": "PASS",
    })

    s1 = fixtures["S1-valid-base-resolution"]
    s1_signature = replay_tree_signature(s1)
    s2_signature = replay_tree_signature(s2)
    if s1_signature != s2_signature:
        raise AssertionError("S1 and S2 replay/tree signatures unexpectedly differ")
    controls.append({
        "control": "replay-tree-cannot-authorize",
        "s1_evidence": results["S1-valid-base-resolution"]["evidence_verdict"],
        "s2_evidence": results["S2-invalid-base-deletion"]["evidence_verdict"],
        "signature": s1_signature,
        "status": "PASS",
    })
    return controls


def run_self_test(fixtures_root: Path, factories=BASE_FIXTURES):
    results = []
    fixtures = {}
    results_by_scenario = {}
    for factory in factories:
        scenario_root = fixtures_root / factory.__name__
        fixture = factory(scenario_root)
        result = classify(fixture)
        verify_result(fixture, result)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        results.append(result)
        fixtures[fixture.scenario_id] = fixture
        results_by_scenario[fixture.scenario_id] = result
    controls = executable_controls(fixtures, results_by_scenario)
    for control in controls:
        print(json.dumps(control, sort_keys=True, separators=(",", ":")))
    summary = {
        "summary": "PASS",
        "passed": len(results),
        "total": len(results),
        "controls_passed": len(controls),
        "controls_total": len(controls),
        "observed_red": sum(
            control["status"] == "OBSERVED_RED" for control in controls
        ),
        "git": REAL_RUN(
            ["git", "--version"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip(),
        "python": sys.version.split()[0],
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test", action="store_true", help="construct and verify all POC DAGs"
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        help="retain new fixture repositories in this empty directory",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not args.self_test:
        raise SystemExit("--self-test is required")
    if args.fixtures_dir is not None:
        fixtures_root = args.fixtures_dir.resolve()
        if fixtures_root.exists() and any(fixtures_root.iterdir()):
            raise SystemExit(f"fixture directory is not empty: {fixtures_root}")
        fixtures_root.mkdir(parents=True, exist_ok=True)
        return run_self_test(fixtures_root)
    with tempfile.TemporaryDirectory(prefix="agentfold-edge-witness-") as temporary:
        return run_self_test(Path(temporary))


if __name__ == "__main__":
    raise SystemExit(main())
