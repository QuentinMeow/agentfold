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
    candidate_commits: int = 0
    candidate_parent_edges: int = 0
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


def queue_path(label: str) -> str:
    return (
        "message-queue/needs-agent/requests/"
        f"non-blocking-{label}.md"
    )


def evidence_path(label: str) -> str:
    return f"docs/evidence-{label}.md"


def action_text(label: str, status: str = "open", action=None) -> str:
    return (
        f"# Preserve {label}\n\n"
        f"**Status:** {status}\n"
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


def old_lineage(
    old_tip: str,
    merge_bases: Iterable[str],
    path: str,
    old_text: str,
    metrics: Metrics,
):
    old_identity = action_identity(path, old_text)
    bases = []
    for base in merge_bases:
        base_text = text_at(base, path, metrics)
        bases.append(None if base_text is None else action_identity(path, base_text))
    if not bases or all(identity is None for identity in bases):
        return "old-tip-authored"
    if all(identity == old_identity for identity in bases):
        return "inherited-unchanged-on-old-tip"
    return "old-tip-authored-or-mutated"


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


def deletion_witnesses(
    commits: Iterable[str], path: str, old_text: str, metrics: Metrics
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
            witnesses.append(
                {"parent": parent, "child": commit, "problem": problem}
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
        elif verdict == "different-incarnation-witness":
            parts.append(
                f"{path} has a valid candidate-side deletion edge for byte-identical "
                "content, but the old-tip action was authored after the shared boundary"
            )
        elif verdict == "ambiguous-real-edges":
            parts.append(f"{path} has multiple matching deletion edges, so the prototype fails closed")
        elif verdict == "rewritten-live-action":
            parts.append(f"{path} remains at the candidate path with a different action identity")
        else:
            parts.append(f"{path} has no matching candidate-side resolution edge")
    return "; ".join(parts) + "."


def classify(fixture: Fixture, enforce_incarnation_provenance=True):
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
                lineage = old_lineage(
                    fixture.O, merge_bases, path, old_text, metrics
                )
                if path in new_paths:
                    new_text = text_at(fixture.N, path, metrics)
                    if new_text is not None and action_identity(
                        path, new_text
                    ) == action_identity(path, old_text):
                        items[path] = {
                            "authoring_lineage": lineage,
                            "evidence_verdict": "candidate-carries-action",
                            "problem": None,
                            "witnesses": [],
                            "finding": False,
                        }
                    else:
                        items[path] = {
                            "authoring_lineage": lineage,
                            "evidence_verdict": "rewritten-live-action",
                            "problem": "candidate path carries a distinct action identity",
                            "witnesses": [],
                            "finding": True,
                        }
                    continue
                witnesses = deletion_witnesses(
                    commits, path, old_text, metrics
                )
                metrics.synthetic_control_calls += 1
                synthetic_edge_problem = RECONCILE.queue_deletion_problem(
                    path, old_text, fixture.O, fixture.N
                )
                valid = [witness for witness in witnesses if witness["problem"] is None]
                if len(witnesses) == 1 and len(valid) == 1:
                    if enforce_incarnation_provenance and lineage != (
                        "inherited-unchanged-on-old-tip"
                    ):
                        verdict = "different-incarnation-witness"
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
                    "evidence_verdict": verdict,
                    "problem": problem,
                    "witnesses": witnesses,
                    "synthetic_edge_problem": synthetic_edge_problem,
                    "finding": finding,
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
        "observed_red": 1,
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
