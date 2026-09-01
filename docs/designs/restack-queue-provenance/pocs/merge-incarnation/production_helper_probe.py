#!/usr/bin/env python3
"""Probe the production claim helper on the cross-occurrence counterexample."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True

from prototype import (
    DEFAULT_PATH,
    EVIDENCE_PATH,
    GitRepo,
    RENAMED_PATH,
    dag_occurrence_continuity_problem,
    sibling_incarnation_problem,
)


def action_text(status: str, payload: str = "base obligation") -> str:
    return (
        "Action-ID: Q\n"
        "Evidence: docs/evidence.md\n"
        f"Payload: {payload}\n\n"
        "# Repair the source\n\n"
        f"**Status:** {status}\n"
        "**Filed:** 2026-08-31\n"
        "**Action:** repair the source\n"
        "**Full context:** `docs/evidence.md`\n"
        "**Resolution evidence:** `docs/evidence.md`\n"
        "**Blocks now:** transition:merge\n"
    )


def load_reconciler():
    repo_root = Path(__file__).resolve().parents[5]
    source = repo_root / "automation/reconcile/reconcile.py"
    spec = importlib.util.spec_from_file_location("merge_poc_reconciler", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def probe_cross_boundary(root: Path, reconciler) -> dict[str, object]:
    repo = GitRepo(root)
    first_open = repo.commit(
        "file first occurrence",
        {DEFAULT_PATH: action_text("open"), EVIDENCE_PATH: "evidence v0\n"},
    )
    first_claim = repo.commit(
        "claim first occurrence",
        {DEFAULT_PATH: action_text("in-repair")},
    )
    absent = repo.commit("delete first occurrence", {DEFAULT_PATH: None})
    current = repo.commit(
        "recreate already claimed occurrence",
        {DEFAULT_PATH: action_text("in-repair")},
    )
    deletion = repo.commit(
        "delete recreated occurrence with changed evidence",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    reconciler.REPO = repo.root
    problem = reconciler.claimed_lifecycle_problem(
        DEFAULT_PATH,
        action_text("in-repair"),
        current,
        "needs-agent",
        "requests",
    )
    return {
        "scenario": "production-helper-cross-boundary-claim-reuse",
        "first_open": first_open,
        "first_claim": first_claim,
        "absence": absent,
        "current_occurrence": current,
        "deletion_candidate": deletion,
        "actual_result": "rejected" if problem else "accepted",
        "expected_result": "rejected",
        "problem": problem,
    }


def probe_own_claim(root: Path, reconciler) -> dict[str, object]:
    repo = GitRepo(root)
    repo.commit(
        "file first occurrence",
        {DEFAULT_PATH: action_text("open"), EVIDENCE_PATH: "evidence v0\n"},
    )
    repo.commit(
        "claim first occurrence",
        {DEFAULT_PATH: action_text("in-repair")},
    )
    repo.commit("delete first occurrence", {DEFAULT_PATH: None})
    current_open = repo.commit(
        "recreate open occurrence",
        {DEFAULT_PATH: action_text("open")},
    )
    current_claim = repo.commit(
        "claim current occurrence",
        {DEFAULT_PATH: action_text("in-repair")},
    )
    deletion = repo.commit(
        "delete current occurrence with changed evidence",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    reconciler.REPO = repo.root
    problem = reconciler.claimed_lifecycle_problem(
        DEFAULT_PATH,
        action_text("in-repair"),
        current_claim,
        "needs-agent",
        "requests",
    )
    return {
        "scenario": "production-helper-current-occurrence-own-claim",
        "current_open": current_open,
        "current_claim": current_claim,
        "deletion_candidate": deletion,
        "actual_result": "accepted" if problem is None else "rejected",
        "expected_result": "accepted",
        "problem": problem,
    }


def probe_ambiguous_merge(root: Path, reconciler) -> dict[str, object]:
    repo = GitRepo(root)
    first_open = repo.commit(
        "file shared occurrence",
        {DEFAULT_PATH: action_text("open"), EVIDENCE_PATH: "evidence v0\n"},
    )
    shared_claim = repo.commit(
        "claim shared occurrence",
        {DEFAULT_PATH: action_text("in-repair")},
    )
    repo.switch_new("parent-one", shared_claim)
    parent_one = repo.commit("carry original occurrence", {"one.txt": "one\n"})
    repo.switch_new("parent-two", shared_claim)
    repo.commit("delete on second parent", {DEFAULT_PATH: None})
    parent_two = repo.commit(
        "recreate preclaimed on second parent",
        {DEFAULT_PATH: action_text("in-repair"), "two.txt": "two\n"},
    )
    repo.switch("parent-one")
    merged = repo.merge_commit(
        "parent-two",
        "merge ambiguous occurrence",
        {},
    )
    deletion = repo.commit(
        "delete ambiguous merged occurrence",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    reconciler.REPO = repo.root
    raw_problem = reconciler.claimed_lifecycle_problem(
        DEFAULT_PATH,
        action_text("in-repair"),
        merged,
        "needs-agent",
        "requests",
    )
    merged_action = repo.snapshot(merged)[DEFAULT_PATH]
    guard_problem = dag_occurrence_continuity_problem(
        repo,
        merged,
        merged_action.incarnation,
        merged_action.action_id,
    )
    actual = (
        "raw-accepted-guard-blocked"
        if raw_problem is None and guard_problem is not None
        else "unexpected"
    )
    return {
        "scenario": "production-helper-ambiguous-merge-occurrence",
        "first_open": first_open,
        "shared_claim": shared_claim,
        "parent_one": parent_one,
        "parent_two": parent_two,
        "merged": merged,
        "deletion_candidate": deletion,
        "raw_helper_result": "accepted" if raw_problem is None else "rejected",
        "raw_helper_problem": raw_problem,
        "guard_result": "blocked" if guard_problem is not None else "accepted",
        "guard_problem": guard_problem,
        "actual_result": actual,
        "expected_result": "raw-accepted-guard-blocked",
    }


def probe_shared_merge(root: Path, reconciler) -> dict[str, object]:
    repo = GitRepo(root)
    repo.commit(
        "file shared occurrence",
        {DEFAULT_PATH: action_text("open"), EVIDENCE_PATH: "evidence v0\n"},
    )
    shared_claim = repo.commit(
        "claim shared occurrence",
        {DEFAULT_PATH: action_text("in-repair")},
    )
    repo.switch_new("parent-one", shared_claim)
    parent_one = repo.commit("carry on first parent", {"one.txt": "one\n"})
    repo.switch_new("parent-two", shared_claim)
    parent_two = repo.commit("carry on second parent", {"two.txt": "two\n"})
    repo.switch("parent-one")
    merged = repo.merge_commit(
        "parent-two",
        "merge shared occurrence",
        {},
    )
    deletion = repo.commit(
        "delete shared merged occurrence",
        {DEFAULT_PATH: None, EVIDENCE_PATH: "evidence v1\n"},
    )
    reconciler.REPO = repo.root
    raw_problem = reconciler.claimed_lifecycle_problem(
        DEFAULT_PATH,
        action_text("in-repair"),
        merged,
        "needs-agent",
        "requests",
    )
    merged_action = repo.snapshot(merged)[DEFAULT_PATH]
    guard_problem = dag_occurrence_continuity_problem(
        repo,
        merged,
        merged_action.incarnation,
        merged_action.action_id,
    )
    actual = (
        "raw-accepted-guard-accepted"
        if raw_problem is None and guard_problem is None
        else "unexpected"
    )
    return {
        "scenario": "production-helper-shared-merge-occurrence",
        "shared_claim": shared_claim,
        "parent_one": parent_one,
        "parent_two": parent_two,
        "merged": merged,
        "deletion_candidate": deletion,
        "raw_helper_result": "accepted" if raw_problem is None else "rejected",
        "raw_helper_problem": raw_problem,
        "guard_result": "accepted" if guard_problem is None else "blocked",
        "guard_problem": guard_problem,
        "actual_result": actual,
        "expected_result": "raw-accepted-guard-accepted",
    }


def probe_conflicting_sibling(root: Path, reconciler) -> dict[str, object]:
    repo = GitRepo(root)
    root_before_common = repo.commit(
        "root without action",
        {EVIDENCE_PATH: "evidence v0\n"},
    )
    common = repo.commit(
        "common adds inherited action",
        {DEFAULT_PATH: action_text("open", "inherited A")},
    )
    repo.switch_new("valid-parent", common)
    valid_parent = repo.commit(
        "claim inherited action",
        {DEFAULT_PATH: action_text("in-repair", "inherited A")},
    )
    repo.switch_new("foreign-parent", root_before_common)
    foreign_parent = repo.commit(
        "independently add conflicting same-ID action",
        {RENAMED_PATH: action_text("in-repair", "conflicting B")},
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
    reconciler.REPO = repo.root
    raw_problem = reconciler.claimed_lifecycle_problem(
        DEFAULT_PATH,
        action_text("in-repair", "inherited A"),
        valid_parent,
        "needs-agent",
        "requests",
    )
    inherited = repo.snapshot(valid_parent)[DEFAULT_PATH]
    candidate = repo.revisions("--topo-order", merged, "--not", common)
    guard_problem = sibling_incarnation_problem(
        repo,
        candidate,
        common,
        inherited.incarnation,
        inherited.action_id,
    )
    actual = (
        "raw-accepted-sibling-guard-blocked"
        if raw_problem is None and guard_problem is not None
        else "unexpected"
    )
    return {
        "scenario": "production-helper-conflicting-sibling-incarnation",
        "root_before_C": root_before_common,
        "common": common,
        "valid_parent": valid_parent,
        "foreign_parent": foreign_parent,
        "merged": merged,
        "raw_helper_result": "accepted" if raw_problem is None else "rejected",
        "raw_helper_problem": raw_problem,
        "guard_result": "blocked" if guard_problem is not None else "accepted",
        "guard_problem": guard_problem,
        "actual_result": actual,
        "expected_result": "raw-accepted-sibling-guard-blocked",
    }


def main() -> int:
    reconciler = load_reconciler()
    try:
        with tempfile.TemporaryDirectory(
            prefix="agentfold-production-claim-probe-"
        ) as tmp:
            base = Path(tmp)
            records = [
                probe_cross_boundary(base / "cross-boundary", reconciler),
                probe_own_claim(base / "own-claim", reconciler),
                probe_ambiguous_merge(base / "ambiguous-merge", reconciler),
                probe_shared_merge(base / "shared-merge", reconciler),
                probe_conflicting_sibling(base / "conflicting-sibling", reconciler),
            ]
    finally:
        reconciler.close_git_cat_file()
    failures = sum(
        record["actual_result"] != record["expected_result"]
        for record in records
    )
    for record in records:
        print(json.dumps(record, sort_keys=True))
    print(json.dumps({
        "summary": "production-claim-helper-probe",
        "passed": len(records) - failures,
        "total": len(records),
        "failed": failures,
    }, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
