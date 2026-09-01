#!/usr/bin/env python3
"""Probe the production claim helper on the cross-occurrence counterexample."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True

from prototype import DEFAULT_PATH, EVIDENCE_PATH, GitRepo


def action_text(status: str) -> str:
    return (
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
