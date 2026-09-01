#!/usr/bin/env python3
"""Generate and verify the production-contract POC evidence artifact.

``evidence.json`` is the sole machine-observation artifact. This stdlib-only
program derives it from a fresh prototype JSONL stream, enforces a closed
schema and exact record catalog, and renders README.md in full. Verification
compares bytes, never prose fragments or an OID pool.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "agentfold-production-contract-evidence/v2"
METRIC_KEYS = (
    "authority_calls", "batch_processes", "git_processes", "graph_commits",
    "graph_enumerations", "graph_parent_edges", "identity_calls",
    "carry_proof_edges", "carry_proof_nodes",
    "mutation_calls", "object_cache_hits", "object_reads",
    "per_action_history_walks", "queue_snapshots_requested",
    "queue_subtree_reads", "snapshot_cache_hits",
    "support_adoption_checks", "support_certificate_calls",
    "support_paths_checked",
)
SCENARIO_IDS = tuple(sorted((
    "P1-direct-linear-valid",
    "P2-direct-linear-invalid",
    "P3-genuine-old-loss",
    "P4-pre-C-identical-origins",
    "P5-duplicate-at-C",
    "P6a-old-delete-recreate",
    "P6b-candidate-delete-recreate",
    "P7-immutable-payload-change",
    "P8-path-timing-move",
    "P9-direct-two-parent-valid",
    "P10-direct-invalid-parent",
    "P11-direct-three-parent-valid",
    "P12-merge-supplier-valid",
    "P13-merge-supplier-invalid",
    "P14-supplier-reintroduced",
    "P15-competing-suppliers",
    "P16-PCX-08-invalid-supplier-claimed-carrier",
    "P17-post-event-reintroduction",
    "P18a-missing-tip",
    "P18b-noncommit-tip",
    "P18c-unrelated-tip",
    "P18d-shallow-required-region",
    "P18e-missing-queue-blob",
    "P18f-missing-queue-tree",
    "P18g-multiple-merge-bases",
    "P19-production-identities",
    "P20-lifecycle-types",
    "P21-PCX-17c-squash-erasure",
    "P22-PCX-18-one-pass-many-actions",
    "PCX-01-neutral-parent",
    "PCX-02-neutral-plus-invalid-carrier",
    "PCX-03-foreign-exact-identity",
    "PCX-04-several-absent-one-supplier",
    "PCX-05-competing-later-supplier",
    "PCX-06-nested-supplier-over-direct",
    "PCX-07-overqualified-propagation",
    "PCX-09-recreated-claimed-bytes",
    "PCX-10-transient-multiplicity",
    "PCX-11-different-payload-same-path",
    "PCX-12-timing-rename-supplier",
    "PCX-13-conflicting-human-response",
    "PCX-14-valid-human-supplier",
    "PCX-15-generated-retry-supplier",
    "PCX-16-task-pickup-supplier",
    "PCX-17-complete-cherry-pick",
    "PCX-17-deletion-only-cherry-pick",
    "PCX-19-missing-claim-blob-recovery",
    "PCX-20a-budget-below-limit",
    "PCX-20b-budget-overflow",
    "R3-01-two-invalid-causal-sources",
    "R3-02-invalid-valid-causal-competition",
    "R3-03-valid-supplier-plus-invalid-parent-at-N-blocks",
    "R4-01-same-root-valid-diamond",
    "R4-02-distinct-valid-root-diamond",
    "R4-03-equal-root-plus-invalid-diamond",
    "R5-01-invalid-redelete-after-supplier-reintroduction",
    "R5-02-valid-redelete-after-supplier-reintroduction",
    "R6-01-valid-plus-invalid-all-absent",
    "R6-02-valid-plus-ambiguous-all-absent",
    "R6-03-two-invalid-all-absent",
    "R6-04-same-valid-root-all-absent-wrappers",
    "R8-direct-human-response-conflict",
    "R8-direct-human-response-identical",
    "R8-review-binding-divergent",
    "R8-review-binding-identical",
    "R8-review-binding-terminal-conflict",
    "R8-supplier-human-response-conflict",
    "R8-supplier-human-response-identical",
    "R9-direct-review-revision-pending-fill",
    "R9-direct-review-target-pending-fill",
    "R9-supplier-review-revision-pending-fill",
    "R9-supplier-review-target-pending-fill",
    "R10-direct-review-target-backtick-dotless-rejected",
    "R10-supplier-review-revision-generic-placeholder-rejected",
    "R13-direct-review-binding-identical",
    "R13-direct-review-binding-revision",
    "R13-direct-review-binding-target",
    "R13-direct-review-binding-terminal",
    "R13-persisted-claim-loss",
    "R13-persisted-pending-fill",
    "R13-persisted-response-change",
    "R13-persisted-response-removal",
    "R13-persisted-review-outcome-change",
    "R13-persisted-review-revision-change",
    "R13-persisted-review-target-change",
    "R13-persisted-same-state",
    "R13-persisted-terminal-fill",
    "R13-supplier-review-binding-identical",
    "R13-supplier-review-binding-revision",
    "R13-supplier-review-binding-target",
    "R13-supplier-review-binding-terminal",
    "R14-direct-old-unanswered-carrier-same",
    "R14-direct-old-unanswered-carrier-target",
    "R14-persisted-delete-recreate",
    "R14-persisted-hidden-bytes-low-similarity",
    "R14-persisted-intermediate-claim-regression",
    "R14-persisted-intermediate-review-regression",
    "R14-persisted-merge-carrier-conflict",
    "R14-persisted-merge-carrier-pending",
    "R14-persisted-valid-first-response-low-similarity",
    "R14-persisted-valid-review-retraction",
    "R14-supplier-old-answered-carrier-pending",
    "R14-supplier-old-answered-carrier-revision",
    "R14-supplier-old-answered-carrier-same",
    "R14-supplier-old-answered-carrier-target",
    "R14-supplier-old-unanswered-carrier-same",
    "R14-supplier-old-unanswered-carrier-target",
    "R15-old-continuous-preserved",
    "R15-old-hidden-bytes-restore",
    "R15-old-human-binding-restore",
    "R15-old-invalid-delete-recreate",
    "R15-old-valid-delete-recreate",
    "R16-earlier-landed-evidence-reversal",
    "R16-pickup-evolution-0-backlog",
    "R16-pickup-evolution-2-blocked",
    "R16-pickup-evolution-3-in-review",
    "R16-pickup-evolution-3-in-review-drop-artifact",
    "R16-pickup-evolution-4-done",
    "R16-support-adoption-drift",
    "R16-support-forward",
    "R16-support-invalid-source",
    "R16-support-nested-drop",
    "R16-support-permutation-diamond",
    "R16-support-reverse-drop",
    "R16-support-reverse-preserved",
    "R16-support-source-evolution",
    "R17-carry-absent-arm",
    "R17-carry-compatible",
    "R17-carry-compatible-reversed",
    "R17-carry-incompatible",
    "R17-carry-outside-duplicate",
    "R17-carry-outside-single",
    "R17-outside-C-neutral-parent-valid-restack",
    "R17-unreadable-outside-C-ancestor-stays-unopened",
    "R17-unreadable-outside-C-boundary",
    "W0-fast-forward-return",
    "W1-pre-PR-push-exact-endpoints",
    "W2-base-advance-retarget-invariant",
    "W3-multiple-PR-API-zero-calls",
    "W4-stale-rerun-exact-inputs",
    "W5-missing-O-coverage-unavailable",
    "W6-created-deleted-zero-endpoints",
    "W7-PR-synchronize-top-level-endpoints",
)))
CONTROL_IDS = tuple(sorted((
    "broad-review-pending-normalization",
    "first-parent-carry-proof",
    "ignore-absent-C-arm",
    "ignore-invalid-N-root",
    "ignore-outside-C-carrier",
    "identity-multiplicity-collapsed-to-set",
    "literal-review-pending-treated-concrete",
    "missing-all-parent-direct-validation",
    "missing-post-event-continuity",
    "omit-old-tip-human-binding",
    "omit-supplier-carrier-human-binding",
    "omit-unanswered-published-review-binding",
    "reopen-outside-C-boundary-ancestry",
    "reopen-pre-C-genealogy",
    "restore-universal-ancestor-carry-scan",
    "skip-carry-compatibility",
    "skip-old-side-continuity",
    "skip-persisted-candidate-continuity",
    "skip-persisted-frozen-skeleton",
    "skip-preserved-state-validation",
    "skip-supplier-support-certificate",
    "sole-valid-ignores-invalid-root",
    "supplier-authority-borrowing",
    "unmetered-cone-work",
)))
ALIAS_IDS = ("S1", "S12", "S2", "S3")
RETIRED_SCENARIO_IDS = (
    "P18h-missing-M",
    "P18i-noncommit-M-blob",
    "P18j-noncommit-M-tree",
    "P18k-noncommit-M-tag",
    "P18l-unrelated-M",
    "P18m-M-after-N",
    "P18n-M-equals-C",
    "P18o-M-equals-N",
    "R8-adapter-M-N-frontier-counterexample",
    "R8-adapter-M-input-variants",
)
RETIRED_DISPOSITION = (
    "removed because candidate-base endpoint authority no longer exists in "
    "the O,N-only classifier API"
)
REVIEWER_REFERENCE_OIDS = {
    "C": "030fe92b832b1bd2790182cab030b9dfd46ec6dc",
    "F": "233e9c9821300b9a1579c261a37b3829d0459250",
    "K": "920d63682562575383ac5adbaf33c5855d24a554",
    "N": "3a60d2c225bbcdf0619135111af9bc0a1120dbce",
    "O": "07418610247abbde975bd54ac937acf75ca02500",
    "P": "bda691d6bc1759421cc55925e8c350edea7d42be",
    "deletion": "d45b8657259492bbc12f6c32a2e81a7944357ce4",
}
ATTACKER_REFERENCE_OIDS = {
    "C": "52c16e3ace5b2fb945b2e8fc42b7485536ea1a47",
    "D": "595acd03b0c0f5cee214599587247d1115b2fc40",
    "F": "4afa966344cb99e6a72a10997b10572072e7cccb",
    "G": "b838a677f5753a45bff2d33f6e94b3a80cc92905",
    "G_blob": "88ce173dddc1914b0e7ccd52f5b89fb4742a713d",
    "K": "245d7de3ef54645d32fbcf8bbda7d69f426ce6d2",
    "N": "61d97651036a8cc9da10662ca7560bce14ce9ce5",
    "O": "5ff93e594d8689fe44774a9728a882c846e1833e",
    "P": "6564e680097653cebcc008a0bfee8587c644057f",
}
R6_OUTSIDE_BOUNDARY_DISPOSITION = (
    "outside-C all-absent boundary is neutral at multiplicity zero; its "
    "ambiguous ancestor root stays unopened"
)
INPUT_PATHS = (
    "docs/AGENTS.md",
    "docs/designs/AGENTS.md",
    "docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py",
    "docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py",
    "automation/check_action_projection.py",
    "automation/markdown_semantics.py",
    "automation/reconcile/reconcile.py",
)
FIXTURE_CLAIMS = (
    ("r8-divergent-old-target", "R8-review-binding-divergent", ("details", "old_binding", 1)),
    ("r8-divergent-candidate-target", "R8-review-binding-divergent", ("details", "candidate_binding", 1)),
    ("r8-identical-target", "R8-review-binding-identical", ("details", "old_binding", 1)),
    ("r8-terminal-reviewed-revision", "R8-review-binding-terminal-conflict", ("details", "old_binding", 1)),
    ("r9-direct-filled-revision", "R9-direct-review-revision-pending-fill", ("details", "candidate_value")),
    ("r9-supplier-filled-revision", "R9-supplier-review-revision-pending-fill", ("details", "candidate_value")),
    ("r10-malformed-bound-revision", "R10-supplier-review-revision-generic-placeholder-rejected", ("details", "candidate_value")),
)


class EvidenceError(ValueError):
    pass


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_json(raw: bytes) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (UnicodeDecodeError, json.JSONDecodeError, EvidenceError) as error:
        raise EvidenceError(f"invalid JSON: {error}") from error


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def record_digest(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "automation/reconcile/reconcile.py").is_file():
            return candidate
    raise EvidenceError("could not locate repository root")


def require_keys(value: Any, keys, context: str):
    if not isinstance(value, dict):
        raise EvidenceError(f"{context} is not an object")
    observed, expected = set(value), set(keys)
    if observed != expected:
        raise EvidenceError(
            f"{context} keys differ: missing={sorted(expected-observed)}, "
            f"extra={sorted(observed-expected)}"
        )


def require_digest(value: Any, context: str):
    if not (
        isinstance(value, str) and len(value) == 71
        and value.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in value[7:])
    ):
        raise EvidenceError(f"{context} is not a canonical SHA-256")


def require_oid(value: Any, context: str):
    if not (
        isinstance(value, str) and len(value) == 40
        and all(char in "0123456789abcdef" for char in value)
    ):
        raise EvidenceError(f"{context} is not a full Git OID")


def require_nonnegative_int(value: Any, context: str):
    if type(value) is not int or value < 0:
        raise EvidenceError(f"{context} is not an exact nonnegative integer")


def normalized_record(value: dict) -> dict:
    result = copy.deepcopy(value)
    if "summary" in result:
        result.pop("git", None)
        result.pop("python", None)
    return result


class Stream:
    def __init__(self, path: Path):
        self.path = path
        self.raw = path.read_bytes()
        self.objects = []
        for number, line in enumerate(self.raw.splitlines(), start=1):
            if not line:
                raise EvidenceError(f"blank JSONL line {number}")
            value = load_json(line)
            if not isinstance(value, dict):
                raise EvidenceError(f"JSONL line {number} is not an object")
            self.objects.append(value)
        self.scenarios = self._unique("scenario")
        self.controls = self._unique("control")
        aliases = [x for x in self.objects if "scenario_alias_inventory" in x]
        permutations = [
            x for x in self.objects
            if "r17_parent_permutation" in x and "summary" not in x
        ]
        summaries = [x for x in self.objects if "summary" in x]
        if len(aliases) != 1 or len(permutations) != 1 or len(summaries) != 1:
            raise EvidenceError(
                "stream needs exactly one permutation, alias, and summary row"
            )
        if len(self.objects) != len(self.scenarios) + len(self.controls) + 3:
            raise EvidenceError("stream contains an unknown record kind")
        self.aliases = aliases[0]
        self.permutation = permutations[0]
        self.summary = summaries[0]
        self._validate()

    def _unique(self, key):
        result = {}
        for row in (x for x in self.objects if key in x):
            if row[key] in result:
                raise EvidenceError(f"duplicate {key} {row[key]!r}")
            result[row[key]] = row
        return result

    def _validate(self):
        if tuple(sorted(self.scenarios)) != SCENARIO_IDS:
            raise EvidenceError("scenario catalog differs from closed inventory")
        if tuple(sorted(self.controls)) != CONTROL_IDS:
            raise EvidenceError("control catalog differs from closed inventory")
        inventory = self.aliases.get("scenario_alias_inventory")
        names = [row.get("alias") for row in inventory or []]
        if tuple(sorted(names)) != ALIAS_IDS or len(set(names)) != 4:
            raise EvidenceError("alias catalog differs from closed inventory")
        expected = {
            "summary": "PASS", "passed": len(SCENARIO_IDS),
            "total": len(SCENARIO_IDS), "controls_passed": len(CONTROL_IDS),
            "controls_total": len(CONTROL_IDS),
            "aliases_passed": len(ALIAS_IDS), "aliases_total": len(ALIAS_IDS),
            "r17_parent_permutation": "PASS",
            "failures": [],
        }
        for key, value in expected.items():
            if self.summary.get(key) != value:
                raise EvidenceError(f"stream summary {key} is not {value!r}")
        signatures = self.permutation.get("r17_parent_permutation")
        if (
            self.permutation.get("status") != "PASS"
            or not isinstance(signatures, list)
            or len(signatures) != 2
            or signatures[0] != signatures[1]
        ):
            raise EvidenceError("r17 parent permutation evidence differs")

    def semantic_bytes(self):
        return b"".join(canonical_bytes(normalized_record(x)) for x in self.objects)


def pointer(value, parts):
    for part in parts:
        value = value[part]
    return value


def edge_projection(edge):
    certificate = edge.get("support_certificate")
    return {
        "child": edge["child"], "parent": edge["parent"],
        "path": edge.get("path"), "problem": edge.get("problem"),
        "support_certificate": certificate.get("certificate_digest") if certificate else None,
    }


def propagation_projection(edge):
    return {
        "child": edge["child"], "parent": edge["parent"],
        "path": edge.get("path"), "role": edge.get("role"),
    }


def support_projection(check):
    return {
        "absent_source_parents": check["absent_source_parents"],
        "adoption_child": check["adoption_child"],
        "authority_child": check["authority_child"],
        "authority_parent": check["authority_parent"],
        "certificate_digest": check["certificate_digest"],
        "postcondition_status": check["postcondition_status"],
        "status": check["status"],
        "tree_projection_status": check["tree_projection_status"],
    }


def carry_projection(proof):
    return {
        "absent_c_parents": proof["absent_c_parents"],
        "edges": [
            {
                "child": edge["child"],
                "parent": edge["parent"],
                "problem": edge["problem"],
                "role": edge["role"],
            }
            for edge in proof["edges"]
        ],
        "outside_collisions": proof["outside_collisions"],
        "outside_neutral": proof["outside_neutral"],
        "reason": proof["reason"],
        "status": proof["status"],
        "tip": proof["tip"],
    }


def endpoints(row):
    return {
        "C": {"oid": row["C"], "role": "derived-unique-merge-base"},
        "N": {"oid": row["N"], "role": "immutable-new-tip"},
        "O": {"oid": row["O"], "role": "immutable-old-tip"},
    }


def scenario_projection(row, failed):
    return {
        "audit_exit": row["audit_exit"],
        "authority_edges": [edge_projection(x) for x in row["authority_edges"]],
        "carry_proofs": [carry_projection(x) for x in row["carry_proofs"]],
        "classification": row["classification"],
        "endpoints": endpoints(row),
        "event_mode": row["event_mode"],
        "evidence_status": row["evidence_verdict"]["status"],
        "expected_result": row["expected_result"],
        "finding_count": sum(bool(x.get("finding")) for x in row["actions"]),
        "id": row["scenario"],
        "input_contract": row["input_contract"],
        "metrics": {key: row["metrics"][key] for key in METRIC_KEYS},
        "mutation_edge_count": len(row["mutation_edges"]),
        "propagation_edges": [propagation_projection(x) for x in row["propagation_edges"]],
        "reason_codes": [x.get("reason_code") for x in row["actions"]],
        "record_sha256": record_digest(normalized_record(row)),
        "support_checks": [support_projection(x) for x in row["support_checks"]],
        "validation_status": "FAIL" if row["scenario"] in failed else "PASS",
    }


def control_projection(row):
    return {
        "authority_edges": [edge_projection(x) for x in row["authority_edges"]],
        "baseline_classification": row["baseline_classification"],
        "damaged_classification": row["damaged_classification"],
        "endpoints": endpoints(row), "expected_baseline": row["expected_baseline"],
        "id": row["control"],
        "propagation_edges": [propagation_projection(x) for x in row["propagation_edges"]],
        "record_sha256": record_digest(row), "status": row["status"],
    }


def alias_projection(row):
    return {
        "expected": row["expected"], "id": row["alias"],
        "maps_to": row["maps_to"], "observed": row["observed"],
        "record_sha256": record_digest(row), "status": row["status"],
    }


def input_projection():
    root = repo_root()
    return [
        {"path": path, "sha256": digest_bytes((root / path).read_bytes()),
         "size": (root / path).stat().st_size}
        for path in INPUT_PATHS
    ]


def core_claim_projection(stream):
    boundary = stream.scenarios[
        "R17-unreadable-outside-C-ancestor-stays-unopened"
    ]
    reviewer = stream.scenarios[
        "R17-outside-C-neutral-parent-valid-restack"
    ]
    r6 = stream.scenarios[
        "R6-02-valid-plus-ambiguous-all-absent"
    ]
    r3 = stream.scenarios[
        "R3-03-valid-supplier-plus-invalid-parent-at-N-blocks"
    ]
    workflow_ids = [name for name in SCENARIO_IDS if name.startswith("W")]
    return {
        "boundary_ancestry": {
            "actual_oids": {
                "C": boundary["C"],
                "D": boundary["details"]["D"],
                "F": boundary["details"]["F"],
                "G": boundary["details"]["G"],
                "K": boundary["details"]["K"],
                "N": boundary["N"],
                "O": boundary["O"],
                "P": boundary["details"]["P"],
                "R": boundary["details"]["R"],
            },
            "ancestor_blob": boundary["details"]["ancestor_blob"],
            "ancestor_blob_is_unique": boundary["details"][
                "ancestor_blob_is_unique"
            ],
            "audit_exit": boundary["audit_exit"],
            "classification": boundary["classification"],
            "graph_commits": boundary["metrics"]["graph_commits"],
            "hidden_ancestor_blob": boundary["details"][
                "hidden_ancestor_blob"
            ],
            "neutral_parent": boundary["details"]["F"],
            "record_sha256": record_digest(normalized_record(boundary)),
            "reference_oids": boundary["details"][
                "attacker_reference_oids"
            ],
            "same_identity": boundary["details"]["same_identity"],
            "status": boundary["evidence_verdict"]["status"],
        },
        "endpoint_contract": {
            "authoritative_inputs": ["O", "N"],
            "derived": ["C"],
            "frontier": "N",
            "schema": "restack-provenance-input/v2",
        },
        "parent_permutation": stream.permutation,
        "r6_outside_boundary_disposition": {
            "ambiguous_ancestor_root": r6["details"]["causal_events"][1],
            "classification": r6["classification"],
            "disposition": r6["details"]["r17_disposition"],
            "record_sha256": record_digest(normalized_record(r6)),
            "status": r6["evidence_verdict"]["status"],
        },
        "r3_full_frontier": {
            "authority_children": [
                edge["child"] for edge in r3["authority_edges"]
            ],
            "classification": r3["classification"],
            "event_mode": r3["event_mode"],
            "invalid_authority_edges": sum(
                edge["problem"] is not None
                for edge in r3["authority_edges"]
            ),
            "reason_codes": [
                action["reason_code"] for action in r3["actions"]
            ],
            "record_sha256": record_digest(normalized_record(r3)),
        },
        "retired_catalog": {
            "disposition": RETIRED_DISPOSITION,
            "scenario_ids": list(RETIRED_SCENARIO_IDS),
        },
        "reviewer_dag": {
            "classification": reviewer["classification"],
            "derived_C": reviewer["C"],
            "neutral_parent": reviewer["details"]["F"],
            "production_deletion_problem": reviewer["details"][
                "production_deletion_problem"
            ],
            "record_sha256": record_digest(normalized_record(reviewer)),
            "reference_oids": reviewer["details"][
                "reviewer_counterexample_oids"
            ],
            "task_patch_equal": reviewer["details"]["task_patch_equal"],
            "unique_merge_base": reviewer["details"]["unique_merge_base"],
        },
        "workflow_input_matrix": {
            name: stream.scenarios[name]["details"]["workflow_contract"]
            for name in workflow_ids
        },
    }


def manifest_from_stream(stream):
    failed = {x["scenario"] for x in stream.summary["failures"] if "scenario" in x}
    aliases = {x["alias"]: x for x in stream.aliases["scenario_alias_inventory"]}
    claims = []
    for claim_id, scenario, path in FIXTURE_CLAIMS:
        claims.append({
            "id": claim_id, "scenario": scenario,
            "json_pointer": "/" + "/".join(map(str, path)),
            "sha256": pointer(stream.scenarios[scenario], path),
        })
    manifest = {
        "aliases": [alias_projection(aliases[x]) for x in ALIAS_IDS],
        "controls": [control_projection(stream.controls[x]) for x in CONTROL_IDS],
        "core_claims": core_claim_projection(stream),
        "fixture_sha_claims": claims,
        "inputs": input_projection(),
        "scenarios": [scenario_projection(stream.scenarios[x], failed) for x in SCENARIO_IDS],
        "schema": SCHEMA,
        "summary": {
            "aliases_passed": stream.summary["aliases_passed"],
            "aliases_total": stream.summary["aliases_total"],
            "canonical_stream_sha256": digest_bytes(stream.semantic_bytes()),
            "controls_passed": stream.summary["controls_passed"],
            "controls_total": stream.summary["controls_total"],
            "r17_parent_permutation": stream.summary[
                "r17_parent_permutation"
            ],
            "scenario_passed": stream.summary["passed"],
            "scenario_total": stream.summary["total"],
            "status": stream.summary["summary"],
        },
    }
    validate_manifest(manifest)
    return manifest


def validate_endpoints(value, context):
    require_keys(value, ("C", "N", "O"), context)
    roles = {
        "C": "derived-unique-merge-base",
        "N": "immutable-new-tip",
        "O": "immutable-old-tip",
    }
    for label, role in roles.items():
        require_keys(value[label], ("oid", "role"), f"{context}.{label}")
        if label != "C" or value[label]["oid"] is not None:
            require_oid(value[label]["oid"], f"{context}.{label}.oid")
        if value[label]["role"] != role:
            raise EvidenceError(f"{context}.{label} role changed")


def validate_edge(value, context):
    require_keys(value, ("child", "parent", "path", "problem", "support_certificate"), context)
    require_oid(value["parent"], f"{context}.parent")
    require_oid(value["child"], f"{context}.child")
    if value["support_certificate"] is not None:
        require_digest(value["support_certificate"], f"{context}.support_certificate")


def validate_propagation(value, context):
    require_keys(value, ("child", "parent", "path", "role"), context)
    require_oid(value["parent"], f"{context}.parent")
    require_oid(value["child"], f"{context}.child")
    if value["role"] != "propagation-only":
        raise EvidenceError(f"{context} is not propagation-only")


def validate_support(value, context):
    require_keys(value, (
        "absent_source_parents", "adoption_child", "authority_child",
        "authority_parent", "certificate_digest", "postcondition_status",
        "status", "tree_projection_status",
    ), context)
    for key in ("adoption_child", "authority_child", "authority_parent"):
        require_oid(value[key], f"{context}.{key}")
    for index, oid in enumerate(value["absent_source_parents"]):
        require_oid(oid, f"{context}.absent_source_parents[{index}]")
    require_digest(value["certificate_digest"], f"{context}.certificate_digest")
    for key in ("postcondition_status", "status", "tree_projection_status"):
        if value[key] not in {"valid", "invalid"}:
            raise EvidenceError(f"{context}.{key} is not structured")


def validate_carry(value, context):
    require_keys(value, (
        "absent_c_parents", "edges", "outside_collisions",
        "outside_neutral", "reason", "status", "tip",
    ), context)
    require_oid(value["tip"], f"{context}.tip")
    if value["status"] not in {"valid", "ambiguous"}:
        raise EvidenceError(f"{context}.status is not structured")
    for key in ("absent_c_parents", "outside_neutral"):
        for index, oid in enumerate(value[key]):
            require_oid(oid, f"{context}.{key}[{index}]")
    for index, edge in enumerate(value["edges"]):
        edge_context = f"{context}.edges[{index}]"
        require_keys(edge, ("child", "parent", "problem", "role"), edge_context)
        require_oid(edge["child"], f"{edge_context}.child")
        require_oid(edge["parent"], f"{edge_context}.parent")
        if edge["role"] not in {"source", "compatible-carrier", "unselected"}:
            raise EvidenceError(f"{edge_context}.role is invalid")
    for index, collision in enumerate(value["outside_collisions"]):
        collision_context = f"{context}.outside_collisions[{index}]"
        require_keys(
            collision,
            ("multiplicity", "parent", "paths", "scope"),
            collision_context,
        )
        require_oid(collision["parent"], f"{collision_context}.parent")
        if collision["scope"] != "outside-C":
            raise EvidenceError(f"{collision_context}.scope changed")
        require_nonnegative_int(
            collision["multiplicity"], f"{collision_context}.multiplicity"
        )


def validate_manifest(manifest):
    require_keys(manifest, (
        "aliases", "controls", "core_claims", "fixture_sha_claims", "inputs",
        "scenarios", "schema", "summary",
    ), "manifest")
    if manifest["schema"] != SCHEMA:
        raise EvidenceError("manifest schema differs")
    require_keys(manifest["summary"], (
        "aliases_passed", "aliases_total", "canonical_stream_sha256",
        "controls_passed", "controls_total", "r17_parent_permutation",
        "scenario_passed", "scenario_total", "status",
    ), "summary")
    summary = manifest["summary"]
    require_digest(summary["canonical_stream_sha256"], "summary stream digest")
    counts = {
        "aliases_passed": len(ALIAS_IDS), "aliases_total": len(ALIAS_IDS),
        "controls_passed": len(CONTROL_IDS), "controls_total": len(CONTROL_IDS),
        "r17_parent_permutation": "PASS",
        "scenario_passed": len(SCENARIO_IDS), "scenario_total": len(SCENARIO_IDS),
        "status": "PASS",
    }
    for key, expected in counts.items():
        if summary[key] != expected:
            raise EvidenceError(f"summary {key} is not {expected!r}")
        if key not in {"status", "r17_parent_permutation"}:
            require_nonnegative_int(summary[key], f"summary.{key}")

    scenarios = manifest["scenarios"]
    if [x.get("id") for x in scenarios] != list(SCENARIO_IDS):
        raise EvidenceError("manifest scenario inventory/order differs")
    scenario_keys = (
        "audit_exit", "authority_edges", "carry_proofs", "classification",
        "endpoints", "event_mode",
        "evidence_status", "expected_result", "finding_count", "id",
        "input_contract", "metrics", "mutation_edge_count", "propagation_edges",
        "reason_codes", "record_sha256",
        "support_checks", "validation_status",
    )
    for index, row in enumerate(scenarios):
        context = f"scenarios[{index}]"
        require_keys(row, scenario_keys, context)
        validate_endpoints(row["endpoints"], f"{context}.endpoints")
        if row["classification"] not in {
            "no-finding", "blocking-finding", "unreadable"
        }:
            raise EvidenceError(f"{context} classification is invalid")
        if row["expected_result"] != row["classification"]:
            raise EvidenceError(f"{context} did not meet expected result")
        if row["evidence_status"] not in {"valid", "invalid", "none", "ambiguous", "unreadable"}:
            raise EvidenceError(f"{context} evidence status is invalid")
        if row["event_mode"] not in {
            "direct", "supplier", "none", "ambiguous", "mixed"
        }:
            raise EvidenceError(f"{context} event mode is invalid")
        if row["validation_status"] != "PASS":
            raise EvidenceError(f"{context} validation did not pass")
        if row["audit_exit"] not in {0, 1, 2}:
            raise EvidenceError(f"{context}.audit_exit is invalid")
        require_keys(
            row["input_contract"],
            ("authoritative_endpoints", "schema"),
            f"{context}.input_contract",
        )
        if row["input_contract"] != {
            "authoritative_endpoints": ["O", "N"],
            "schema": "restack-provenance-input/v2",
        }:
            raise EvidenceError(f"{context} input contract changed")
        require_keys(row["metrics"], METRIC_KEYS, f"{context}.metrics")
        for key, value in row["metrics"].items():
            require_nonnegative_int(value, f"{context}.metrics.{key}")
        require_nonnegative_int(row["finding_count"], f"{context}.finding_count")
        require_nonnegative_int(
            row["mutation_edge_count"], f"{context}.mutation_edge_count"
        )
        require_digest(row["record_sha256"], f"{context}.record_sha256")
        for i, edge in enumerate(row["authority_edges"]):
            validate_edge(edge, f"{context}.authority_edges[{i}]")
        for i, edge in enumerate(row["propagation_edges"]):
            validate_propagation(edge, f"{context}.propagation_edges[{i}]")
        for i, check in enumerate(row["support_checks"]):
            validate_support(check, f"{context}.support_checks[{i}]")
        for i, proof in enumerate(row["carry_proofs"]):
            validate_carry(proof, f"{context}.carry_proofs[{i}]")

    controls = manifest["controls"]
    if [x.get("id") for x in controls] != list(CONTROL_IDS):
        raise EvidenceError("manifest control inventory/order differs")
    control_keys = (
        "authority_edges", "baseline_classification", "damaged_classification",
        "endpoints", "expected_baseline", "id", "propagation_edges",
        "record_sha256", "status",
    )
    for index, row in enumerate(controls):
        context = f"controls[{index}]"
        require_keys(row, control_keys, context)
        validate_endpoints(row["endpoints"], f"{context}.endpoints")
        if row["status"] != "OBSERVED_RED":
            raise EvidenceError(f"{context} did not observe red")
        if row["baseline_classification"] != row["expected_baseline"]:
            raise EvidenceError(f"{context} baseline differs")
        if row["damaged_classification"] == row["expected_baseline"]:
            raise EvidenceError(f"{context} damage did not change verdict")
        require_digest(row["record_sha256"], f"{context}.record_sha256")
        for i, edge in enumerate(row["authority_edges"]):
            validate_edge(edge, f"{context}.authority_edges[{i}]")
        for i, edge in enumerate(row["propagation_edges"]):
            validate_propagation(edge, f"{context}.propagation_edges[{i}]")

    aliases = manifest["aliases"]
    if [x.get("id") for x in aliases] != list(ALIAS_IDS):
        raise EvidenceError("manifest alias inventory/order differs")
    alias_fields = (
        "authority_edges", "classification", "event_mode", "evidence_status",
        "finding", "invalid_authority_edges", "propagation_edges", "scenario",
    )
    for index, row in enumerate(aliases):
        context = f"aliases[{index}]"
        require_keys(row, ("expected", "id", "maps_to", "observed", "record_sha256", "status"), context)
        require_keys(row["expected"], alias_fields, f"{context}.expected")
        require_keys(row["observed"], alias_fields, f"{context}.observed")
        if row["status"] != "PASS" or row["expected"] != row["observed"]:
            raise EvidenceError(f"{context} alias assertion did not pass")
        for view_name in ("expected", "observed"):
            view = row[view_name]
            if type(view["finding"]) is not bool:
                raise EvidenceError(f"{context}.{view_name}.finding is not boolean")
            for key in (
                "authority_edges", "invalid_authority_edges",
                "propagation_edges",
            ):
                require_nonnegative_int(
                    view[key], f"{context}.{view_name}.{key}"
                )
        require_digest(row["record_sha256"], f"{context}.record_sha256")

    if [x.get("path") for x in manifest["inputs"]] != list(INPUT_PATHS):
        raise EvidenceError("manifest input inventory/order differs")
    for index, row in enumerate(manifest["inputs"]):
        require_keys(row, ("path", "sha256", "size"), f"inputs[{index}]")
        require_digest(row["sha256"], f"inputs[{index}].sha256")
        if type(row["size"]) is not int or row["size"] <= 0:
            raise EvidenceError(f"inputs[{index}] size is invalid")

    claims = manifest["fixture_sha_claims"]
    if [x.get("id") for x in claims] != [x[0] for x in FIXTURE_CLAIMS]:
        raise EvidenceError("fixture SHA claim inventory/order differs")
    for index, row in enumerate(claims):
        require_keys(row, ("id", "json_pointer", "scenario", "sha256"), f"fixture_sha_claims[{index}]")
        require_digest(row["sha256"], f"fixture_sha_claims[{index}].sha256")

    by_id = {x["id"]: x for x in scenarios}
    core = manifest["core_claims"]
    require_keys(core, (
        "boundary_ancestry", "endpoint_contract", "parent_permutation",
        "r3_full_frontier", "r6_outside_boundary_disposition",
        "retired_catalog", "reviewer_dag", "workflow_input_matrix",
    ), "core_claims")
    boundary = core["boundary_ancestry"]
    require_keys(boundary, (
        "actual_oids", "ancestor_blob", "ancestor_blob_is_unique",
        "audit_exit", "classification", "graph_commits",
        "hidden_ancestor_blob", "neutral_parent", "record_sha256",
        "reference_oids", "same_identity", "status",
    ), "boundary_ancestry")
    boundary_row = by_id[
        "R17-unreadable-outside-C-ancestor-stays-unopened"
    ]
    require_keys(
        boundary["actual_oids"],
        ("C", "D", "F", "G", "K", "N", "O", "P", "R"),
        "boundary_ancestry.actual_oids",
    )
    for label, oid in boundary["actual_oids"].items():
        require_oid(oid, f"boundary_ancestry.actual_oids.{label}")
    require_oid(boundary["ancestor_blob"], "boundary_ancestry.ancestor_blob")
    require_oid(boundary["neutral_parent"], "boundary_ancestry.neutral_parent")
    require_digest(boundary["record_sha256"], "boundary_ancestry.record_sha256")
    expected_hidden = (
        f".git/objects/{boundary['ancestor_blob'][:2]}/"
        f"{boundary['ancestor_blob'][2:]}.missing"
    )
    if (
        boundary["reference_oids"] != ATTACKER_REFERENCE_OIDS
        or boundary["classification"] != "no-finding"
        or boundary["audit_exit"] != 0
        or boundary["status"] != "valid"
        or boundary["same_identity"] is not True
        or boundary["ancestor_blob_is_unique"] is not True
        or boundary["hidden_ancestor_blob"] != expected_hidden
        or boundary["neutral_parent"] != boundary["actual_oids"]["F"]
        or boundary["actual_oids"]["C"]
        != boundary_row["endpoints"]["C"]["oid"]
        or boundary["actual_oids"]["O"]
        != boundary_row["endpoints"]["O"]["oid"]
        or boundary["actual_oids"]["N"]
        != boundary_row["endpoints"]["N"]["oid"]
        or boundary["record_sha256"] != boundary_row["record_sha256"]
        or boundary["graph_commits"]
        != boundary_row["metrics"]["graph_commits"]
        or boundary["neutral_parent"] not in {
            oid
            for proof in boundary_row["carry_proofs"]
            for oid in proof["outside_neutral"]
        }
    ):
        raise EvidenceError("outside-C boundary ancestry claim changed")
    if core["endpoint_contract"] != {
        "authoritative_inputs": ["O", "N"],
        "derived": ["C"],
        "frontier": "N",
        "schema": "restack-provenance-input/v2",
    }:
        raise EvidenceError("core endpoint contract changed")
    permutation = core["parent_permutation"]
    require_keys(
        permutation, ("r17_parent_permutation", "status"),
        "core_claims.parent_permutation",
    )
    signatures = permutation["r17_parent_permutation"]
    if (
        permutation["status"] != "PASS"
        or len(signatures) != 2
        or signatures[0] != signatures[1]
    ):
        raise EvidenceError("core parent permutation claim changed")
    r6 = core["r6_outside_boundary_disposition"]
    require_keys(r6, (
        "ambiguous_ancestor_root", "classification", "disposition",
        "record_sha256", "status",
    ), "r6_outside_boundary_disposition")
    r6_row = by_id["R6-02-valid-plus-ambiguous-all-absent"]
    require_oid(
        r6["ambiguous_ancestor_root"],
        "r6_outside_boundary_disposition.ambiguous_ancestor_root",
    )
    if (
        r6["classification"] != "no-finding"
        or r6["status"] != "valid"
        or r6["disposition"] != R6_OUTSIDE_BOUNDARY_DISPOSITION
        or r6["record_sha256"] != r6_row["record_sha256"]
    ):
        raise EvidenceError("R6 outside-C boundary disposition changed")
    retired = core["retired_catalog"]
    require_keys(retired, ("disposition", "scenario_ids"), "retired_catalog")
    if (
        retired["disposition"] != RETIRED_DISPOSITION
        or retired["scenario_ids"] != list(RETIRED_SCENARIO_IDS)
    ):
        raise EvidenceError("retired endpoint scenario disposition changed")
    reviewer = core["reviewer_dag"]
    require_keys(reviewer, (
        "classification", "derived_C", "neutral_parent",
        "production_deletion_problem", "record_sha256", "reference_oids",
        "task_patch_equal", "unique_merge_base",
    ), "reviewer_dag")
    if reviewer["reference_oids"] != REVIEWER_REFERENCE_OIDS:
        raise EvidenceError("reviewer DAG reference OID catalog changed")
    for label, oid in reviewer["reference_oids"].items():
        require_oid(oid, f"reviewer_dag.reference_oids.{label}")
    reviewer_row = by_id["R17-outside-C-neutral-parent-valid-restack"]
    reviewer_neutral = {
        oid
        for proof in reviewer_row["carry_proofs"]
        for oid in proof["outside_neutral"]
    }
    reviewer_collisions = [
        collision
        for proof in reviewer_row["carry_proofs"]
        for collision in proof["outside_collisions"]
    ]
    if (
        reviewer["classification"] != "no-finding"
        or reviewer["derived_C"] != reviewer_row["endpoints"]["C"]["oid"]
        or reviewer["neutral_parent"] not in reviewer_neutral
        or reviewer_collisions
        or reviewer["production_deletion_problem"] is not None
        or not reviewer["task_patch_equal"]
        or reviewer["unique_merge_base"] != [reviewer["derived_C"]]
        or reviewer["record_sha256"] != reviewer_row["record_sha256"]
    ):
        raise EvidenceError("reviewer DAG result claim changed")
    require_oid(reviewer["neutral_parent"], "reviewer_dag.neutral_parent")
    r3 = core["r3_full_frontier"]
    require_keys(r3, (
        "authority_children", "classification", "event_mode",
        "invalid_authority_edges", "reason_codes", "record_sha256",
    ), "r3_full_frontier")
    r3_row = by_id["R3-03-valid-supplier-plus-invalid-parent-at-N-blocks"]
    if (
        r3["classification"] != "blocking-finding"
        or r3["event_mode"] != "ambiguous"
        or r3["invalid_authority_edges"] != 1
        or r3["reason_codes"] != ["competing-final-absence-roots"]
        or r3["record_sha256"] != r3_row["record_sha256"]
    ):
        raise EvidenceError("R3 fixed-N frontier claim changed")
    for index, oid in enumerate(r3["authority_children"]):
        require_oid(oid, f"r3_full_frontier.authority_children[{index}]")
    workflow_ids = [name for name in SCENARIO_IDS if name.startswith("W")]
    workflow = core["workflow_input_matrix"]
    if list(workflow) != workflow_ids:
        raise EvidenceError("workflow input matrix catalog changed")
    for name, contract in workflow.items():
        if (
            contract.get("classifier_parameters") != ["O", "N"]
            or contract.get("provider_api_calls") != 0
            or set(contract.get("authoritative_inputs", {})) != {"O", "N"}
            or contract.get("fallback", object()) is not None
        ):
            raise EvidenceError(f"workflow input contract changed for {name}")
    if (
        workflow["W0-fast-forward-return"].get("fast_forward_return") is not True
        or workflow["W1-pre-PR-push-exact-endpoints"].get("N_source")
        != "immutable event.after"
        or workflow["W1-pre-PR-push-exact-endpoints"].get(
            "github_sha_is_authoritative"
        ) is not False
        or workflow["W2-base-advance-retarget-invariant"].get(
            "variants_keep_exact_O_N"
        ) is not True
        or workflow["W3-multiple-PR-API-zero-calls"].get("PR_lookup")
        is not False
        or workflow["W4-stale-rerun-exact-inputs"].get(
            "repeat_exact_inputs"
        ) is not True
        or workflow["W5-missing-O-coverage-unavailable"].get(
            "coverage_classification"
        ) != "coverage-unavailable"
        or workflow["W5-missing-O-coverage-unavailable"].get(
            "old_object_fetch_exit"
        ) != 2
        or {
            row.get("event"): row.get("classification")
            for row in workflow["W6-created-deleted-zero-endpoints"].get(
                "event_classifications", []
            )
        } != {"created": "coverage-unavailable", "deleted": "coverage-unavailable"}
        or workflow["W7-PR-synchronize-top-level-endpoints"].get("PR_lookup")
        is not False
        or workflow["W7-PR-synchronize-top-level-endpoints"].get(
            "after_matches_head"
        ) is not True
        or workflow["W7-PR-synchronize-top-level-endpoints"].get("N_source")
        != "top-level after"
    ):
        raise EvidenceError("workflow endpoint seam claim changed")
    p22 = by_id["P22-PCX-18-one-pass-many-actions"]["metrics"]
    if p22["graph_enumerations"] != 1 or p22["graph_commits"] < 128 or p22["per_action_history_walks"] != 0:
        raise EvidenceError("P22 one-pass cost invariant differs")


def render_readme(manifest):
    validate_manifest(manifest)
    evidence_sha = digest_bytes(canonical_bytes(manifest))
    summary = manifest["summary"]
    core = manifest["core_claims"]
    by_id = {x["id"]: x for x in manifest["scenarios"]}
    p22, p19 = by_id["P22-PCX-18-one-pass-many-actions"], by_id["PCX-19-missing-claim-blob-recovery"]
    lines = [
        "# Production-contract provenance POC", "",
        "This file is generated in full by `audit_readme.py` from the closed",
        "`evidence.json` manifest. Do not edit observations here by hand.", "",
        "## Result", "",
        f"The real-Git self-test passed {summary['scenario_passed']}/{summary['scenario_total']} scenarios, {summary['aliases_passed']}/{summary['aliases_total']} executable aliases, and {summary['controls_passed']}/{summary['controls_total']} damaged-mode controls.",
        "It imports and calls the worktree's actual `queue_action_identity` and",
        "`queue_deletion_problem`; it never invents an Action-ID or lifecycle verdict.", "",
        f"Canonical evidence artifact: `{evidence_sha}`.",
        f"Canonical semantic stream: `{summary['canonical_stream_sha256']}`.",
        "The raw JSONL stream is ephemeral and has no stored hash claim.", "",
        "## Contract exercised", "",
        "The classifier accepts exactly two immutable inputs, old tip `O` and new tip",
        "`N`, and derives the unique merge base `C`. It enumerates the full C-rooted",
        "`C..N` ancestry-path frontier once. Immediate outside-`C` parents remain",
        "identity-discovery boundaries, never event children. A boundary parent with no matching identity is",
        "neutral and its ancestors remain unopened; any matching identity there is a",
        "collision. Production identities map to exact",
        "path lists, so multiplicity cannot collapse to membership. O-side and C-descendant",
        "carrying paths require one continuously valid `C`-rooted occurrence. Every",
        "linear carry edge calls production mutation authority and its frozen-byte",
        "complement; a carrying merge chooses one source and checks every other parent",
        "as a binding/frozen-compatible carrier.", "",
        "Direct mode requires every carrying parent-to-child deletion edge to pass",
        "production deletion authority independently. Supplier mode requires one earlier",
        "real deletion root, continuous absence to absent parents, live carrying parents,",
        "and merge adoption. Carrying-to-merge edges remain propagation-only.", "",
        "A supplier root carries a domain-separated `queue-supplier-support/v1` certificate",
        "binding the real authority edge, raw non-action tree delta, every concrete path",
        "referenced by the authoritative action, typed lifecycle obligations, and a",
        "canonical digest. Adoption exact-copies the closest absent source's current",
        "support projection. Earlier source-lineage evolution is allowed; adoption drift,",
        "dropped evidence, conflicting projections, incomplete leaf coverage, or a failed",
        "typed obligation blocks. Pickup accepts one uniquely claimed resolving task with",
        "no pickup backlink; retry reruns its checker. Unsupported successor/reask and",
        "boundary-review support dependencies fail closed.", "",
        "Concrete human response/review binding is anchored at `O` and unified across",
        "every real authority or propagation parent. Only outer-trimmed plain `pending`",
        "is the Review target/revision pending sentinel. Final absence remains continuous",
        "to the fixed `N` frontier; reintroduction and every invalid, ambiguous, or",
        "additional causal root reaching `N` aggregate complete evidence and block.", "",
        "Workflow transport is non-authoritative metadata around exact `O,N`: push uses",
        "immutable event `before`/`after` and never `github.sha`; PR synchronize uses",
        "top-level `before`/`after`, requires `after == pull_request.head.sha`, and makes",
        "no API lookup. Created/deleted zero endpoints and an unavailable old `O` are",
        "explicit coverage-unavailable results; the latter exits 2 with no fallback.", "",
        "The ten former candidate-base endpoint/adapter scenarios are retired because",
        "that endpoint no longer exists in the classifier API. Fixture-internal commits",
        "remain landmarks only and cannot steer attribution.", "",
        "## Bound r17 review outcomes", "",
        f"The exact reviewer DAG is clean and record-bound by `{core['reviewer_dag']['record_sha256']}`; its outside-C parent is neutral, its task patch replays exactly, and production deletion authority returns no problem.",
        f"R3-03 is blocking at the fixed N frontier with one invalid authority edge and is record-bound by `{core['r3_full_frontier']['record_sha256']}`.",
        f"The hidden-G attacker is clean at exit 0 and record-bound by `{core['boundary_ancestry']['record_sha256']}`: F is the neutral boundary, G carries the same identity in a unique missing blob, and G ancestry remains unopened.",
        f"R6-02 is explicitly dispositioned clean and record-bound by `{core['r6_outside_boundary_disposition']['record_sha256']}` because its outside-C boundary is absent; the ambiguous ancestor behind it is not reopened.",
        "The parent-order pair has identical verdicts and the same role multiset:",
        f"`{core['parent_permutation']['r17_parent_permutation'][0]['merge_role_multiset']}`.", "",
        "Reviewer-supplied reference OIDs (bound as review input, not regenerated fixture IDs):", "",
        "| Role | OID |", "|---|---|",
    ]
    for label, oid in core["reviewer_dag"]["reference_oids"].items():
        lines.append(f"| `{label}` | `{oid}` |")
    lines += ["", "Boundary-attacker reference OIDs (bound review input):", "",
              "| Role | OID |", "|---|---|"]
    for label, oid in core["boundary_ancestry"]["reference_oids"].items():
        lines.append(f"| `{label}` | `{oid}` |")
    lines += ["",
        "## Input byte identities", "",
        "| Path | Bytes | SHA-256 |", "|---|---:|---|",
    ]
    for row in manifest["inputs"]:
        lines.append(f"| `{row['path']}` | {row['size']} | `{row['sha256']}` |")
    lines += ["", "## Seven fixture SHA bindings", "",
              "| Claim | Scenario | JSON pointer | SHA-256 |", "|---|---|---|---|"]
    for row in manifest["fixture_sha_claims"]:
        lines.append(f"| `{row['id']}` | `{row['scenario']}` | {row['json_pointer']} | `{row['sha256']}` |")
    lines += ["", "## Scenario evidence inventory", "",
              "Each record digest binds its complete canonical scenario JSON, including",
              "all nested OIDs, verdicts, reasons, paths, counters, certificates, and",
              "carry proofs, and workflow input contracts. It is not an OID-pool membership check.", "",
              "| Scenario | C | O | N | Exit | Classification | Evidence | Mode | A/P/U/S | Validation | Record SHA-256 |",
              "|---|---|---|---|---:|---|---|---|---:|---|---|"]
    for row in manifest["scenarios"]:
        e = row["endpoints"]
        counts = f"{len(row['authority_edges'])}/{len(row['propagation_edges'])}/{row['mutation_edge_count']}/{len(row['support_checks'])}"
        lines.append(f"| `{row['id']}` | `{e['C']['oid']}` | `{e['O']['oid']}` | `{e['N']['oid']}` | {row['audit_exit']} | `{row['classification']}` | `{row['evidence_status']}` | `{row['event_mode']}` | {counts} | `{row['validation_status']}` | `{row['record_sha256']}` |")
    lines += ["", "A/P/U/S means authority, propagation, persisted mutation, and supplier-support checks.", "",
              "## Executable S aliases", "",
              "| Alias | Maps to | Classification | Evidence | Mode | Authority | Invalid authority | Propagation | Status | Record SHA-256 |",
              "|---|---|---|---|---|---:|---:|---:|---|---|"]
    for row in manifest["aliases"]:
        o = row["observed"]
        lines.append(f"| `{row['id']}` | `{row['maps_to']}` | `{o['classification']}` | `{o['evidence_status']}` | `{o['event_mode']}` | {o['authority_edges']} | {o['invalid_authority_edges']} | {o['propagation_edges']} | `{row['status']}` | `{row['record_sha256']}` |")
    lines += ["", "## Damaged-mode controls", "",
              "| Control | C | O | N | Baseline | Damaged | Status | Record SHA-256 |",
              "|---|---|---|---|---|---|---|---|"]
    for row in manifest["controls"]:
        e = row["endpoints"]
        lines.append(f"| `{row['id']}` | `{e['C']['oid']}` | `{e['O']['oid']}` | `{e['N']['oid']}` | `{row['baseline_classification']}` | `{row['damaged_classification']}` | `{row['status']}` | `{row['record_sha256']}` |")
    m = p22["metrics"]
    lines += ["", "## Measured cost and object recovery", "",
              f"P22 measured {m['graph_commits']} graph commits and 16 disappeared actions with exactly {m['graph_enumerations']} POC graph enumeration, {m['per_action_history_walks']} POC-owned per-action history walks, {m['queue_snapshots_requested']} snapshot requests, {m['snapshot_cache_hits']} snapshot-cache hits, and {m['git_processes']} actual Git processes.",
              "The process count includes imported production `git rev-list --parents -n 1` queries; zero applies only to POC-owned per-action walks. Production must reuse its parent cache and set a measured process budget. This POC sets no guessed ceiling.", "",
              f"PCX-19 is replay-bound by `{p19['record_sha256']}`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.", "",
              "## Reproducible audit", "",
              "Use two fresh, empty scratch roots:", "", "```sh",
              "PYTHONHASHSEED=1 LC_ALL=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-seed1 > /tmp/production-contract-r17-seed1.jsonl",
              "PYTHONHASHSEED=777 LC_ALL=en_US.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-seed777 > /tmp/production-contract-r17-seed777.jsonl",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-seed1.jsonl --compare /tmp/production-contract-r17-seed777.jsonl",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-seed1.jsonl --damage-test",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --old FULL_OID_O --new FULL_OID_N",
              "python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py",
              "python3 automation/run_tests.py", "python3 automation/reconcile/reconcile.py --check", "```", "",
              "The auditor requires raw and semantic equality for comparison, rejects",
              "duplicate keys/IDs, enforces exact catalogs/key sets, compares a fresh",
              "manifest byte-for-byte, and regenerates this README in full. Its damage",
              "matrix covers invented/duplicate/missing rows, same-region OID swaps, tuple",
              "relabels, false verdicts/counters, contradictory transcripts/digests,",
              "unknown cost rows, noncanonical ordering, BOM, CRLF, and missing newline.", "",
              "## Nonclaims and integration gates", "",
              "- This POC changes no production reconciler, restack adapter, workflow input, schema, task, or run record.",
              "- A post-push check can only be advisory; prevention requires a pre-push or server-side production gate.",
              "- Squash/deletion-only provenance is unsupported and blocks; only complete cherry-pick preserves authority.",
              "- No candidate-base or provider base field participates in attribution.",
              "- Fork/pre-PR transport without a trusted old O is coverage-unavailable; no reflog guess is permitted.",
              "- Local pre-push uses remote old/local new; an offline wrapper must capture O before rewriting.",
              "- Certificates intentionally overbind non-action authority delta and referenced paths until production exposes a validator-owned support receipt.",
              "- Review successor/reask and boundary-review supplier leaves fail closed rather than simulate semantics.",
              "- The one-pass claim excludes imported production parent queries; production integration must cache/eliminate them.",
              "- PCX-21/22 remain production-integration gates, not isolated-POC completion claims.", "",
              "## Tests not represented by this artifact", "",
              "This artifact does not claim deployment, a real remote push, production",
              "adapter wiring, server enforcement, or unsupported review-successor coverage.", ""]
    return "\n".join(lines).encode("utf-8")


def audit_artifacts(evidence_raw, readme_raw, expected):
    try:
        manifest = load_json(evidence_raw)
        validate_manifest(manifest)
    except (EvidenceError, KeyError, TypeError, IndexError) as error:
        return [str(error)]
    failures = []
    if evidence_raw != canonical_bytes(manifest):
        failures.append("evidence.json is not canonical UTF-8 JSON+LF")
    if manifest != expected:
        failures.append("evidence.json differs from fresh replay manifest")
    if readme_raw != render_readme(manifest):
        failures.append("README.md differs from exact generated rendering")
    return failures


def stream_differences(first, second):
    def keyed(stream):
        result = {}
        for row in stream.objects:
            key = ("scenario:" + row["scenario"] if "scenario" in row else
                   "control:" + row["control"] if "control" in row else
                   "parent-permutation" if (
                       "r17_parent_permutation" in row and "summary" not in row
                   ) else
                   "aliases" if "scenario_alias_inventory" in row else "summary")
            result[key] = normalized_record(row)
        return result
    left, right = keyed(first), keyed(second)
    def diff(a, b):
        if type(a) is not type(b):
            return 1
        if isinstance(a, dict):
            sentinel = object()
            return sum(diff(a.get(k, sentinel), b.get(k, sentinel)) for k in set(a) | set(b))
        if isinstance(a, list):
            sentinel = object()
            return sum(diff(a[i] if i < len(a) else sentinel, b[i] if i < len(b) else sentinel) for i in range(max(len(a), len(b))))
        return int(a != b)
    fields = records = 0
    sentinel = object()
    for name in set(left) | set(right):
        count = diff(left.get(name, sentinel), right.get(name, sentinel))
        fields += count
        records += bool(count)
    return {"canonical_equal": first.semantic_bytes() == second.semantic_bytes(),
            "differing_fields": fields, "differing_records": records,
            "raw_equal": first.raw == second.raw}


def damage_matrix(expected):
    evidence, readme = canonical_bytes(expected), render_readme(expected)
    cases = []
    def append(name, text):
        cases.append(
            (name, evidence, readme + text.encode(), "README.md differs")
        )
    oid = expected["scenarios"][0]["endpoints"]["C"]["oid"]
    append("invented-real-oids-false-verdict", f"| `invented` | `{oid}` | no-finding valid direct |\n")
    append("invented-no-oid-row", "| invented-cost | Graph commits=999 |\n")
    p1 = next(x for x in readme.splitlines(keepends=True) if x.startswith(b"| `P1-direct-linear-valid`"))
    cases += [
        ("duplicate-real-row", evidence, readme + p1, "README.md differs"),
        (
            "missing-real-row", evidence, readme.replace(p1, b"", 1),
            "README.md differs",
        ),
    ]
    append("count-transcript-only", "PASS 999/999 Graph commits=999\n")
    append("r5-verdict-oid-substitution", "R5 no-finding valid deadbeef\n")
    append("r9-prose-counter", "R9 passed 9 cells\n")
    append("contradictory-pass-digest-graph999", "PASS 1/1 sha256:" + "0"*64 + " Graph commits=999\n")
    append("unknown-no-oid-cost-row", "| unknown-cost | no-finding | 999 |\n")
    def manifest_case(name, mutate, expected_failure="fresh replay manifest"):
        changed = copy.deepcopy(expected)
        mutate(changed)
        raw = canonical_bytes(changed)
        try:
            rendered = render_readme(changed)
        except EvidenceError:
            rendered = readme
        cases.append((name, raw, rendered, expected_failure))
    def swap_endpoint(data):
        e = data["scenarios"][0]["endpoints"]
        e["C"], e["O"] = e["O"], e["C"]
    manifest_case("same-region-endpoint-swap", swap_endpoint, "role changed")
    def swap_oid_under_label(data):
        e = data["scenarios"][0]["endpoints"]
        e["C"]["oid"], e["O"]["oid"] = e["O"]["oid"], e["C"]["oid"]
    manifest_case("same-region-oid-under-label-swap", swap_oid_under_label)
    def pcx_swap(data):
        by = {x["id"]: x for x in data["scenarios"]}
        by["PCX-05-competing-later-supplier"]["endpoints"]["N"] = by["R5-01-invalid-redelete-after-supplier-reintroduction"]["endpoints"]["N"]
    manifest_case("pcx05-same-region-oid-substitution", pcx_swap)
    def relabel(data):
        by = {x["id"]: x for x in data["scenarios"]}
        a, b = by["R5-01-invalid-redelete-after-supplier-reintroduction"], by["R5-02-valid-redelete-after-supplier-reintroduction"]
        a["id"], b["id"] = b["id"], a["id"]
    manifest_case("exact-tuple-relabel", relabel, "inventory/order differs")
    def reviewer_false_block(data):
        data["core_claims"]["reviewer_dag"]["classification"] = \
            "blocking-finding"
    manifest_case(
        "reviewer-dag-false-block", reviewer_false_block,
        "reviewer DAG result claim changed",
    )
    manifest_case(
        "reviewer-dag-neutral-parent-lost",
        lambda d: d["core_claims"]["reviewer_dag"].update(
            neutral_parent=d["core_claims"]["reviewer_dag"]["derived_C"]
        ),
        "reviewer DAG result claim changed",
    )
    manifest_case(
        "reviewer-reference-oid-substitution",
        lambda d: d["core_claims"]["reviewer_dag"]["reference_oids"].update(
            C="0" * 40
        ),
        "reviewer DAG reference OID catalog changed",
    )
    manifest_case(
        "boundary-attacker-false-unreadable",
        lambda d: d["core_claims"]["boundary_ancestry"].update(
            classification="unreadable", audit_exit=2, status="unreadable"
        ),
        "outside-C boundary ancestry claim changed",
    )
    manifest_case(
        "boundary-attacker-reference-oid-substitution",
        lambda d: d["core_claims"]["boundary_ancestry"][
            "reference_oids"
        ].update(G="0" * 40),
        "outside-C boundary ancestry claim changed",
    )
    manifest_case(
        "boundary-attacker-reopen-hidden-blob",
        lambda d: d["core_claims"]["boundary_ancestry"].update(
            hidden_ancestor_blob="opened"
        ),
        "outside-C boundary ancestry claim changed",
    )
    manifest_case(
        "r6-outside-boundary-false-block",
        lambda d: d["core_claims"][
            "r6_outside_boundary_disposition"
        ].update(classification="blocking-finding"),
        "R6 outside-C boundary disposition changed",
    )
    manifest_case(
        "r3-fixed-frontier-false-clean",
        lambda d: d["core_claims"]["r3_full_frontier"].update(
            classification="no-finding"
        ),
        "R3 fixed-N frontier claim changed",
    )
    manifest_case(
        "external-base-restored",
        lambda d: d["core_claims"]["endpoint_contract"][
            "authoritative_inputs"
        ].append("B"),
        "core endpoint contract changed",
    )
    manifest_case(
        "frontier-steered-away-from-N",
        lambda d: d["core_claims"]["endpoint_contract"].update(frontier="B"),
        "core endpoint contract changed",
    )
    manifest_case(
        "parent-permutation-first-parent",
        lambda d: d["core_claims"]["parent_permutation"][
            "r17_parent_permutation"
        ][1].update(merge_role_multiset=["source"]),
        "core parent permutation claim changed",
    )
    manifest_case(
        "push-github-sha-authoritative",
        lambda d: d["core_claims"]["workflow_input_matrix"][
            "W1-pre-PR-push-exact-endpoints"
        ].update(github_sha_is_authoritative=True),
        "workflow endpoint seam claim changed",
    )
    manifest_case(
        "pr-synchronize-api-lookup",
        lambda d: d["core_claims"]["workflow_input_matrix"][
            "W7-PR-synchronize-top-level-endpoints"
        ].update(provider_api_calls=1),
        "workflow input contract changed",
    )
    manifest_case(
        "missing-O-fallback",
        lambda d: d["core_claims"]["workflow_input_matrix"][
            "W5-missing-O-coverage-unavailable"
        ].update(fallback="reflog"),
        "workflow input contract changed",
    )
    def counter(data):
        next(x for x in data["scenarios"] if x["id"] == "P22-PCX-18-one-pass-many-actions")["metrics"]["graph_commits"] = 999
    manifest_case("counter-substitution", counter)
    manifest_case(
        "duplicate-scenario-id",
        lambda d: d["scenarios"][1].update(id=d["scenarios"][0]["id"]),
        "inventory/order differs",
    )
    manifest_case(
        "unknown-scenario-id",
        lambda d: d["scenarios"][0].update(id="UNKNOWN"),
        "inventory/order differs",
    )
    manifest_case(
        "missing-scenario-id", lambda d: d["scenarios"].pop(),
        "inventory/order differs",
    )
    manifest_case(
        "unknown-scenario-field",
        lambda d: d["scenarios"][0].update(unknown_machine_claim=1),
        "keys differ",
    )
    def missing_field(data):
        data["scenarios"][0].pop("classification")
    manifest_case("missing-scenario-field", missing_field, "keys differ")
    def duplicate_fixture_claim(data):
        data["fixture_sha_claims"].append(
            copy.deepcopy(data["fixture_sha_claims"][0])
        )
    manifest_case(
        "duplicate-fixture-claim", duplicate_fixture_claim,
        "inventory/order differs",
    )
    def fixture_target_swap(data):
        data["fixture_sha_claims"][0]["scenario"] = \
            data["fixture_sha_claims"][1]["scenario"]
        data["fixture_sha_claims"][0]["json_pointer"] = \
            data["fixture_sha_claims"][1]["json_pointer"]
    manifest_case("fixture-digest-target-swap", fixture_target_swap)
    manifest_case(
        "boolean-as-integer",
        lambda d: next(
            x for x in d["scenarios"]
            if x["id"] == "P22-PCX-18-one-pass-many-actions"
        )["metrics"].update(graph_enumerations=True),
        "exact nonnegative integer",
    )
    cases.append((
        "duplicate-json-key",
        evidence.replace(
            b'{"aliases":', b'{"schema":"duplicate","aliases":', 1
        ),
        readme,
        "duplicate JSON key",
    ))
    cases.append((
        "noncanonical-json-ordering",
        (json.dumps(expected, indent=2, sort_keys=True)+"\n").encode(),
        readme,
        "not canonical",
    ))
    cases.append((
        "utf8-bom", b"\xef\xbb\xbf" + evidence, readme, "invalid JSON"
    ))
    cases.append((
        "crlf-json", evidence.replace(b"\n", b"\r\n"), readme,
        "not canonical",
    ))
    cases.append((
        "missing-final-newline", evidence.rstrip(b"\n"), readme,
        "not canonical",
    ))
    results = []
    for name, damaged_evidence, damaged_readme, expected_failure in cases:
        failures = audit_artifacts(
            damaged_evidence, damaged_readme, expected
        )
        matched = any(expected_failure in failure for failure in failures)
        results.append({
            "damage": name,
            "expected_failure": expected_failure,
            "observed_failure": failures[0] if failures else None,
            "status": "OBSERVED_RED" if matched else "FALSE_GREEN",
        })
    return {"audit_damage": "PASS" if all(x["status"] == "OBSERVED_RED" for x in results) else "FAIL",
            "cases": results, "observed_red": sum(x["status"] == "OBSERVED_RED" for x in results), "total": len(results)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", required=True, type=Path)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--damage-test", action="store_true")
    here = Path(__file__).resolve().parent
    parser.add_argument("--evidence", type=Path, default=here / "evidence.json")
    parser.add_argument("--readme", type=Path, default=here / "README.md")
    args = parser.parse_args(argv)
    try:
        first = Stream(args.stream)
        expected = manifest_from_stream(first)
        if args.generate:
            args.evidence.write_bytes(canonical_bytes(expected))
            args.readme.write_bytes(render_readme(expected))
        failures = audit_artifacts(args.evidence.read_bytes(), args.readme.read_bytes(), expected)
        comparison = None
        if args.compare:
            second = Stream(args.compare)
            second_manifest = manifest_from_stream(second)
            comparison = stream_differences(first, second)
            comparison["manifest_equal"] = expected == second_manifest
            if not (comparison["raw_equal"] and comparison["canonical_equal"] and comparison["manifest_equal"] and comparison["differing_records"] == 0 and comparison["differing_fields"] == 0):
                failures.append("compared streams are not byte/semantic equal")
        result = {"aliases": len(expected["aliases"]), "audit": "PASS" if not failures else "FAIL",
                  "comparison": comparison, "controls": len(expected["controls"]),
                  "evidence_sha256": digest_bytes(canonical_bytes(expected)),
                  "failures": failures, "fixture_sha_claims": len(expected["fixture_sha_claims"]),
                  "inputs": len(expected["inputs"]), "scenarios": len(expected["scenarios"])}
        print(json.dumps(result, sort_keys=True))
        if args.damage_test:
            damaged = damage_matrix(expected)
            print(json.dumps(damaged, sort_keys=True))
            if damaged["audit_damage"] != "PASS":
                failures.append("audit damage matrix false-greened")
        return int(bool(failures))
    except (EvidenceError, OSError, KeyError, TypeError, IndexError) as error:
        print(json.dumps({"audit": "FAIL", "failures": [str(error)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
