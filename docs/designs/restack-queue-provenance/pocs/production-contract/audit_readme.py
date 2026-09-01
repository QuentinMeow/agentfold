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


SCHEMA = "agentfold-production-contract-evidence/v5"
SUPERSEDED_EVIDENCE = {
    "artifacts": [
        {
            "commit": "0b80c342feb310d73de6564aab2224a899f42486",
            "disposition": (
                "superseded and burned after later persisted-carry and "
                "measured-budget semantic blockers; history is preserved "
                "and v2 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v2",
        },
        {
            "commit": "7f4a1ffacd1cf8163f597daa186f801e9ce06a3a",
            "disposition": (
                "superseded and burned after pre-charge budget, localized "
                "Git diagnostic, and permissive raw-grammar blockers; "
                "history is preserved and v3 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v3",
        },
        {
            "commit": "cce76a037f1584ff7d37048cb4411bdf0f5aa907",
            "disposition": (
                "superseded and burned after the true execution-bound "
                "composition blocker; history is preserved and v4 is "
                "never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v4",
        },
    ],
    "replacement_schema": SCHEMA,
}
METRIC_KEYS = (
    "git_processes", "graph_enumerations", "graph_commits",
    "graph_parent_edges", "graph_output_bytes", "graph_line_bytes",
    "graph_line_peak_bytes", "graph_lines", "graph_commit_tokens",
    "graph_parent_tokens", "graph_process_terminations",
    "graph_process_reaps", "graph_process_cleanup_checks",
    "graph_buffered_bytes", "graph_stream_chunks",
    "graph_stream_peak_chunk_bytes", "merge_base_output_bytes",
    "merge_base_line_bytes", "merge_base_line_peak_bytes",
    "merge_base_lines", "merge_base_tokens",
    "merge_base_process_terminations", "merge_base_process_reaps",
    "shallow_output_bytes", "shallow_line_bytes",
    "shallow_line_peak_bytes", "shallow_lines", "shallow_tokens",
    "shallow_process_terminations", "shallow_process_reaps",
    "batch_processes", "object_reads", "object_cache_hits",
    "object_header_bytes", "object_payload_bytes",
    "object_payload_peak_bytes", "object_process_terminations",
    "object_process_reaps", "tree_entries", "tree_entry_name_bytes",
    "flattened_paths", "flattened_path_bytes", "flat_tree_peak_paths",
    "queue_snapshots_requested", "queue_subtree_reads",
    "snapshot_cache_hits", "queue_paths", "queue_path_bytes",
    "queue_blob_bytes", "identity_calls", "authority_calls",
    "support_certificate_calls", "support_adoption_checks",
    "support_paths_checked", "support_delta_candidates",
    "support_delta_rows", "support_referenced_paths",
    "support_anchor_rows", "support_obligations",
    "support_serialized_bytes", "dynamic_support_paths_traversed",
    "dynamic_support_paths_discovered", "dynamic_support_path_bytes",
    "mutation_calls", "per_action_history_walks", "carry_proof_nodes",
    "carry_proof_edges", "production_helper_calls",
    "production_helper_input_bytes", "production_parent_queries",
    "git_stderr_bytes",
)
RUNTIME_MILESTONE_COMMITS = (
    "c32f470977735a63feaf377ca9290353d1520e0e",
    "850d02587f7f812b7dde9667a39da80b4ce48764",
)
EXECUTION_BOUND_CASES = (
    (
        "graph_parent_tokens", "graph_parent_tokens", 68,
        "R17-graph-parent-tokens-exact",
        "R17-graph-parent-tokens-plus-one-refused",
    ),
    (
        "graph_output_bytes", "graph_output_bytes", 2952,
        "R17-graph-output-bytes-exact",
        "R17-graph-output-bytes-plus-one-refused",
    ),
    (
        "graph_line_peak_bytes", "graph_line_peak_bytes", 2705,
        "R17-graph-line-peak-bytes-exact",
        "R17-graph-line-peak-bytes-plus-one-refused",
    ),
    (
        "object_payload_peak_bytes", "object_payload_peak_bytes", 1_000_000,
        "R17-object-payload-peak-exact",
        "R17-object-payload-peak-plus-one-refused",
    ),
    (
        "flat_tree_peak_paths", "flat_tree_peak_paths", 1004,
        "R17-flat-tree-peak-exact",
        "R17-flat-tree-peak-plus-one-refused",
    ),
    (
        "dynamic_support_paths_traversed",
        "dynamic_support_paths_traversed", 12,
        "R17-dynamic-support-traversal-exact",
        "R17-dynamic-support-traversal-plus-one-refused",
    ),
    (
        "support_serialized_bytes", "support_serialized_bytes", 2920,
        "R17-support-serialized-exact",
        "R17-support-serialized-plus-one-refused",
    ),
)
PRECHARGE_P22_METRICS = {
    "authority_calls": 0,
    "batch_processes": 1,
    "carry_proof_edges": 1,
    "carry_proof_nodes": 2,
    "dynamic_support_path_bytes": 0,
    "dynamic_support_paths_discovered": 0,
    "dynamic_support_paths_traversed": 0,
    "flat_tree_peak_paths": 0,
    "flattened_path_bytes": 0,
    "flattened_paths": 0,
    "git_processes": 4,
    "git_stderr_bytes": 0,
    "graph_buffered_bytes": 0,
    "graph_commit_tokens": 132,
    "graph_commits": 133,
    "graph_enumerations": 1,
    "graph_line_bytes": 10692,
    "graph_line_peak_bytes": 81,
    "graph_lines": 132,
    "graph_output_bytes": 10824,
    "graph_parent_edges": 132,
    "graph_parent_tokens": 132,
    "graph_process_cleanup_checks": 3,
    "graph_process_reaps": 1,
    "graph_process_terminations": 0,
    "graph_stream_chunks": 132,
    "graph_stream_peak_chunk_bytes": 82,
    "identity_calls": 32,
    "merge_base_line_bytes": 40,
    "merge_base_line_peak_bytes": 40,
    "merge_base_lines": 1,
    "merge_base_output_bytes": 41,
    "merge_base_process_reaps": 1,
    "merge_base_process_terminations": 0,
    "merge_base_tokens": 1,
    "mutation_calls": 1,
    "object_cache_hits": 25,
    "object_header_bytes": 6747,
    "object_payload_bytes": 29421,
    "object_payload_peak_bytes": 816,
    "object_process_reaps": 0,
    "object_process_terminations": 0,
    "object_reads": 134,
    "per_action_history_walks": 0,
    "production_helper_calls": 0,
    "production_helper_input_bytes": 0,
    "production_parent_queries": 0,
    "queue_blob_bytes": 7208,
    "queue_path_bytes": 2043,
    "queue_paths": 39,
    "queue_snapshots_requested": 59,
    "queue_subtree_reads": 3,
    "shallow_line_bytes": 5,
    "shallow_line_peak_bytes": 5,
    "shallow_lines": 1,
    "shallow_output_bytes": 6,
    "shallow_process_reaps": 1,
    "shallow_process_terminations": 0,
    "shallow_tokens": 1,
    "snapshot_cache_hits": 55,
    "support_adoption_checks": 0,
    "support_anchor_rows": 0,
    "support_certificate_calls": 0,
    "support_delta_candidates": 0,
    "support_delta_rows": 0,
    "support_obligations": 0,
    "support_paths_checked": 0,
    "support_referenced_paths": 0,
    "support_serialized_bytes": 0,
    "tree_entries": 242,
    "tree_entry_name_bytes": 2575,
}
POSTHOC_P22_METRICS = {
    "authority_calls": 32,
    "batch_processes": 1,
    "carry_proof_edges": 2080,
    "carry_proof_nodes": 2112,
    "dynamic_support_path_bytes": 0,
    "dynamic_support_paths_discovered": 0,
    "dynamic_support_paths_traversed": 0,
    "flat_tree_peak_paths": 162,
    "flattened_path_bytes": 6223,
    "flattened_paths": 316,
    "git_processes": 135,
    "git_stderr_bytes": 0,
    "graph_buffered_bytes": 0,
    "graph_commit_tokens": 132,
    "graph_commits": 133,
    "graph_enumerations": 1,
    "graph_line_bytes": 10692,
    "graph_line_peak_bytes": 81,
    "graph_lines": 132,
    "graph_output_bytes": 10824,
    "graph_parent_edges": 132,
    "graph_parent_tokens": 132,
    "graph_process_cleanup_checks": 3,
    "graph_process_reaps": 1,
    "graph_process_terminations": 0,
    "graph_stream_chunks": 132,
    "graph_stream_peak_chunk_bytes": 82,
    "identity_calls": 32,
    "merge_base_line_bytes": 40,
    "merge_base_line_peak_bytes": 40,
    "merge_base_lines": 1,
    "merge_base_output_bytes": 41,
    "merge_base_process_reaps": 1,
    "merge_base_process_terminations": 0,
    "merge_base_tokens": 1,
    "mutation_calls": 2080,
    "object_cache_hits": 24736,
    "object_header_bytes": 15262,
    "object_payload_bytes": 71081,
    "object_payload_peak_bytes": 4480,
    "object_process_reaps": 0,
    "object_process_terminations": 0,
    "object_reads": 300,
    "per_action_history_walks": 0,
    "production_helper_calls": 163,
    "production_helper_input_bytes": 18111,
    "production_parent_queries": 129,
    "queue_blob_bytes": 7208,
    "queue_path_bytes": 2043,
    "queue_paths": 39,
    "queue_snapshots_requested": 10973,
    "queue_subtree_reads": 3,
    "shallow_line_bytes": 5,
    "shallow_line_peak_bytes": 5,
    "shallow_lines": 1,
    "shallow_output_bytes": 6,
    "shallow_process_reaps": 1,
    "shallow_process_terminations": 0,
    "shallow_tokens": 1,
    "snapshot_cache_hits": 10970,
    "support_adoption_checks": 0,
    "support_anchor_rows": 496,
    "support_certificate_calls": 16,
    "support_delta_candidates": 2592,
    "support_delta_rows": 496,
    "support_obligations": 48,
    "support_paths_checked": 0,
    "support_referenced_paths": 32,
    "support_serialized_bytes": 204000,
    "tree_entries": 730,
    "tree_entry_name_bytes": 6949,
}
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
    "R17-dynamic-support-traversal-exact",
    "R17-dynamic-support-traversal-plus-one-refused",
    "R17-flat-tree-peak-exact",
    "R17-flat-tree-peak-plus-one-refused",
    "R17-graph-line-peak-bytes-exact",
    "R17-graph-line-peak-bytes-plus-one-refused",
    "R17-graph-output-bytes-exact",
    "R17-graph-output-bytes-plus-one-refused",
    "R17-object-payload-peak-exact",
    "R17-object-payload-peak-plus-one-refused",
    "R17-outside-C-neutral-parent-valid-restack",
    "R17-precharge-P22-budget",
    "R17-persisted-outside-duplicate",
    "R17-persisted-outside-duplicate-reversed",
    "R17-persisted-outside-single",
    "R17-persisted-outside-single-reversed",
    "R17-persisted-unauthorized-absent-arm",
    "R17-persisted-unauthorized-absent-arm-reversed",
    "R17-persisted-valid-absent-arm",
    "R17-persisted-valid-absent-arm-reversed",
    "R17-unreadable-outside-C-ancestor-stays-unopened",
    "R17-unreadable-outside-C-boundary",
    "R17-support-serialized-exact",
    "R17-support-serialized-plus-one-refused",
    "R17-wide-outside-C-boundary-budget",
    "R17-graph-parent-tokens-exact",
    "R17-graph-parent-tokens-plus-one-refused",
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
    "buffered-graph-output",
    "broad-review-pending-normalization",
    "first-parent-carry-proof",
    "ignore-absent-C-arm",
    "ignore-invalid-N-root",
    "ignore-outside-C-carrier",
    "ignore-persisted-absent-C-arm",
    "ignore-persisted-outside-C-collision",
    "identity-multiplicity-collapsed-to-set",
    "literal-review-pending-treated-concrete",
    "locale-git-error-stream-equality",
    "missing-all-parent-direct-validation",
    "missing-post-event-continuity",
    "omit-old-tip-human-binding",
    "omit-supplier-carrier-human-binding",
    "omit-unanswered-published-review-binding",
    "posthoc-budget-accounting",
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
    "stream-malformed-truncated-final-line",
    "unmetered-cone-work",
    "unmetered-dynamic-support",
    "unmetered-object-payload",
    "unmetered-support-construction",
    "unmetered-tree-paths",
)))
ALIAS_IDS = ("S1", "S12", "S2", "S3")
PERSISTED_VARIANTS = (
    "outside-duplicate",
    "outside-single",
    "unauthorized-absent-arm",
    "valid-absent-arm",
)
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
PERSISTED_OUTSIDE_REFERENCE_OIDS = {
    "A": "426b485efa3b5f85a678600795a20b1e91c6049f",
    "C": "843634959ac1156ef81ee7ccbf1f703261bbde1f",
    "F": "e10a4eb3208c44000e7363c2894e2a77b74828fa",
    "N": "af48cf172570a08d65c12dc467b2226dfbe8981a",
    "O": "c0ec07829f6aa4e1207a680a0354deb8a8f0c162",
    "P": "60f5448337b6f9a114c0231b86242474dd34873b",
}
PERSISTED_ABSENT_REFERENCE_OIDS = {
    "A": "90de0b5af2ad8baec036ddaed2842eda86c2c556",
    "C": "0ddb561a40c84c0590d9abe8a3036521b239de25",
    "D": "161d7ed2d7bc121ce5331fed2e1ecb0dd650041e",
    "K": "f03d61cc931d7c860e7fd6f166c60d09596b48e5",
    "N": "76cf3354a913effec09cac7b183684159dfd0b84",
    "O": "17ef4a3d8c518778d62c635864670319efd03754",
    "P": "1847cdbe8298d5895ad566c03abc870064ca711b",
}
WIDE_BUDGET_REFERENCE_OIDS = {
    "C": "b066accf737c901fd1ee314fcf310afb70c8fe87",
    "N": "412c2f8c5a8be93d1e0ffc5983d607bf750bb2f0",
    "O": "ba894e5a1c019e3b2c29ee8319eebfb4b0aaa9a3",
    "P": "b79ff7a4036270fed4a70d82ad226817ae94e662",
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


# Generated once from both byte-identical fresh v5 streams after runtime commits
# c32f470977735a63feaf377ca9290353d1520e0e and
# 850d02587f7f812b7dde9667a39da80b4ce48764.  Every row kind has one
# exact recursive shape digest, checked before any projection.
RAW_SHAPE_CATALOG_V5 = """
aliases sha256:539a8708aebdaa2816ceb01ed2e091a849972b69700c444eeec8e566eaa9eed3
control:broad-review-pending-normalization sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414
control:buffered-graph-output sha256:a5c9687fc28f115ffb25a46739950c0bff58f1297ed55d7d953845957b91b5d5
control:first-parent-carry-proof sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:identity-multiplicity-collapsed-to-set sha256:1ac1b79c19942df728cefbeb0153aeb8b42f07ceffc5343fd5981b03e6048190
control:ignore-absent-C-arm sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:ignore-invalid-N-root sha256:e6d8aa17fd995baf10e03163e020ab50afb5e1b5bfcc3ebf515a9c09dc66a8ab
control:ignore-outside-C-carrier sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:ignore-persisted-absent-C-arm sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:ignore-persisted-outside-C-collision sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:literal-review-pending-treated-concrete sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414
control:locale-git-error-stream-equality sha256:742dda0d750851fe1eaf99a187460279385d12aadb25de6479979cbea272c8e4
control:missing-all-parent-direct-validation sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:missing-post-event-continuity sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:omit-old-tip-human-binding sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414
control:omit-supplier-carrier-human-binding sha256:465ccf7bbd7c9fc49c2576a9974d06ef1c8ec5cf27711192ed3bb05d1b009deb
control:omit-unanswered-published-review-binding sha256:465ccf7bbd7c9fc49c2576a9974d06ef1c8ec5cf27711192ed3bb05d1b009deb
control:posthoc-budget-accounting sha256:7bcaf5e278473e8ac6ac3a3968001fd52cfccf97005b51dbbbae8ff2189d9a7d
control:reopen-outside-C-boundary-ancestry sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:reopen-pre-C-genealogy sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:restore-universal-ancestor-carry-scan sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:skip-carry-compatibility sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:skip-old-side-continuity sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-persisted-candidate-continuity sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-persisted-frozen-skeleton sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-preserved-state-validation sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-supplier-support-certificate sha256:e6d8aa17fd995baf10e03163e020ab50afb5e1b5bfcc3ebf515a9c09dc66a8ab
control:sole-valid-ignores-invalid-root sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:stream-malformed-truncated-final-line sha256:cae48a249e054657a20bde2e2d8f3010169570bb307263fee4f1f7c7adfb4f48
control:supplier-authority-borrowing sha256:889c75da0848d6f89f4d98b22ac05d36d45c3a1d4888d64ae67d9316869049f4
control:unmetered-cone-work sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:unmetered-dynamic-support sha256:247979e72c21e06ce04516c2b72a803d84b46428a0b274ce922a32c60821c96a
control:unmetered-object-payload sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:unmetered-support-construction sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:unmetered-tree-paths sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
parent-permutation sha256:ff2c5187a2f005aefb4e390ee296b9fb51f90077a07b7e52b90e26a54bcc27d6
scenario:P1-direct-linear-valid sha256:4c33f5d3242af6e21b6cd10cfa38c814d852afe62e88105aafa861afc65c428d
scenario:P10-direct-invalid-parent sha256:4ab8178a32e9442bea7d45567d2faeefbe4581806154507e260919856479da02
scenario:P11-direct-three-parent-valid sha256:f238ab9c5fa4767b6188b113a38f92946121ae1e97a06b82ba5b3281d36f69ab
scenario:P12-merge-supplier-valid sha256:74e5dece1ca1ed4aa928f4738ab5e1e891eb1527e4919c2b2459e27cfc5f6d0a
scenario:P13-merge-supplier-invalid sha256:f3d3af68be6b7f29828923e3a798d3c195ab88a6791c749a7014370a95a63788
scenario:P14-supplier-reintroduced sha256:74fef2526e0336c1988560a682eb7cde85bce9c26e75e9b6525914569127e15f
scenario:P15-competing-suppliers sha256:82c564265fb903f01cc80169313095c30f0fcbcebb95bf7e076a5cd123910447
scenario:P16-PCX-08-invalid-supplier-claimed-carrier sha256:78fa5408e6681c1c4974eaf955df19485d3413fdc2091efe7a954f5644fd0571
scenario:P17-post-event-reintroduction sha256:06e7e2cac59217fdeac748abd5c400db289b156323ad2b28de6341618d595bcc
scenario:P18a-missing-tip sha256:83e94c26e047764cb8aefd3e39242b306e770c00d394224291dc93877f7404ae
scenario:P18b-noncommit-tip sha256:83e94c26e047764cb8aefd3e39242b306e770c00d394224291dc93877f7404ae
scenario:P18c-unrelated-tip sha256:83e94c26e047764cb8aefd3e39242b306e770c00d394224291dc93877f7404ae
scenario:P18d-shallow-required-region sha256:83e94c26e047764cb8aefd3e39242b306e770c00d394224291dc93877f7404ae
scenario:P18e-missing-queue-blob sha256:0cea7e00f363eaa29b0e139cf4d04f1c504437bf3cefe99c3d0405ad21e660a5
scenario:P18f-missing-queue-tree sha256:f97e8d42c44b3002eceed0b6f4ba2c5087944d7d7901e5904ceaaa0b08ee0edd
scenario:P18g-multiple-merge-bases sha256:596fff1132b2e97914e385a58524499674c8b10965d7514f2a33398418ec7077
scenario:P19-production-identities sha256:c1a954ab7b5da32c5242bd452728eae046056844a76002a60e658cd6e1ebf1d4
scenario:P2-direct-linear-invalid sha256:f0c8e5bd95470227d429658eb7c4d9317f31817d129e4d1a0511a878ec8c0d9e
scenario:P20-lifecycle-types sha256:076ced0c964e2ca3e5eccb947b29c8a481ccfa64c9eeecd92fd27f1c0c7679b9
scenario:P21-PCX-17c-squash-erasure sha256:f59ab60e938b4ed01343762e33d3e48c28d74c4a80c61ed4be4d386066a93ad8
scenario:P22-PCX-18-one-pass-many-actions sha256:eb57ffad401fb37889906e4a6996f69aa46c50e2ed0f1b3e600ca920fa5f7cb2
scenario:P3-genuine-old-loss sha256:08884a7b66dd4858183d0fdb2b0ebb34daed57ad33fde7606963d723a581686b
scenario:P4-pre-C-identical-origins sha256:dc6d830026cfca449cb2b5784f5399d6d9c3259c5ebde45749d2bd9ef5a84535
scenario:P5-duplicate-at-C sha256:739abf63e89be455172a5a2ed1b56419d395d0f98aaf652af34c540ce6674611
scenario:P6a-old-delete-recreate sha256:3b889f79641d54ac9af069637bf8d9083d57bb42b54e7bcae475f87a640956ef
scenario:P6b-candidate-delete-recreate sha256:407c21fc3f2aa76a11abe28625744d01ef132ce2d6af8a5ecc8235e15189e1e6
scenario:P7-immutable-payload-change sha256:0d488725608626ae386c46d5c6bd1713e725428108f1413062250e295c5d78b4
scenario:P8-path-timing-move sha256:845ec8bcb99bb323553fb11b9bf3c6fd981e5402b8e9edb25c17128a63ab9b04
scenario:P9-direct-two-parent-valid sha256:f696566cef9dd09dd7e9e9d6de45e76f4fe674dbaf75765ea934acbc10fa2084
scenario:PCX-01-neutral-parent sha256:a9751c3fca804974dd37c2f1fb12b8870604a6ba2711644261813b9f15cc26a8
scenario:PCX-02-neutral-plus-invalid-carrier sha256:6b45a26c3cb2d193e7ddab5c86e0dd5c8667772a72790d512616fca14328dbd0
scenario:PCX-03-foreign-exact-identity sha256:6e3cfe16dc586784b359e1ab9722863868d210bae3490283e2519a05acfc00f2
scenario:PCX-04-several-absent-one-supplier sha256:8d9c6aea83d71615334d8a4fc7024fad1b4a1a4b0b19b7fe8572456655744770
scenario:PCX-05-competing-later-supplier sha256:ed216702648fffe54b60b9a73757c448cc49c147840a70c8e29a2e63bf2e470b
scenario:PCX-06-nested-supplier-over-direct sha256:bdb83b6a691e43d8e4b3b5e03ba24633a58a5b235905403741e2da2beb2a688b
scenario:PCX-07-overqualified-propagation sha256:bed885b0e1f7bd2489daa7e59a072768d7c768e47cab770a63a44c521af350c5
scenario:PCX-09-recreated-claimed-bytes sha256:942fc71c9f16fd9cc008925da67cc65f5f1971e31f3d7a1fdfab643e36ff4409
scenario:PCX-10-transient-multiplicity sha256:3c52e2e05077bc7b017c26b3b981bed9891afd40bb137f7cf3e731d5f2117edf
scenario:PCX-11-different-payload-same-path sha256:3b1b51660586e86a581c1a223bf254cc7f9dad51142477eff06b91ff67920fee
scenario:PCX-12-timing-rename-supplier sha256:aa1c877dc0f7b8b71b7f0a1e623a954a89cfeb43fd4f87816259e5958ca9435e
scenario:PCX-13-conflicting-human-response sha256:737a0d3ce9018db9765d69d9590f94fe5b6081548a95c15face8d8fc2bcea802
scenario:PCX-14-valid-human-supplier sha256:33c72a7b22a5e80d641bb8489e04f76edbb5887fa740e4bb9da1f30692e2bab5
scenario:PCX-15-generated-retry-supplier sha256:56dc30bf018b588b278f82b2222dd030476392aff7db869d677fdb83178a8894
scenario:PCX-16-task-pickup-supplier sha256:143388e2a630084b96a4e0b4eb85d208fa18228b9ca1c9c33823fdbe3012de96
scenario:PCX-17-complete-cherry-pick sha256:4cec14353ade0a710de581f0f9628f30a7720624a6a65fe86d2dad44ed780c10
scenario:PCX-17-deletion-only-cherry-pick sha256:f59ab60e938b4ed01343762e33d3e48c28d74c4a80c61ed4be4d386066a93ad8
scenario:PCX-19-missing-claim-blob-recovery sha256:129f309e070e0a81b0e6c37a1ae81be7f1a0cc9c1b18262d7e010b0fae75162c
scenario:PCX-20a-budget-below-limit sha256:0f815b51de9227cb6408d56587e8e6ce2575fcfa0b973fd665d649f127651eae
scenario:PCX-20b-budget-overflow sha256:3c01d9a534f635d15afe37744b92ca48c71173955617e600377d7ed5ca12ea17
scenario:R10-direct-review-target-backtick-dotless-rejected sha256:37febd376cf79f90f88e993e5ce0981251ec8b2e5378fc12fb8e9175dbda3404
scenario:R10-supplier-review-revision-generic-placeholder-rejected sha256:a004f6504fe4ef6114853bae0a9b4a368549ac561c1e2b0a9b99140e17e051a2
scenario:R13-direct-review-binding-identical sha256:e592f189a7b8f6722079c9692db21a34a61cd7f97f94dd773544c4500f198290
scenario:R13-direct-review-binding-revision sha256:6f677e3e1ff447c599f7da38213e1c1a45173c963c2918ad0a820c366cf355cc
scenario:R13-direct-review-binding-target sha256:733f41dbf6377a865835eb55ce6c022ccd88c96e8e0997b85dad7ec7e4ddb399
scenario:R13-direct-review-binding-terminal sha256:dc6d5a95db791d45a43f26363bee4fb7c6d56940025d6aa7c926bcbeda9cb5cb
scenario:R13-persisted-claim-loss sha256:ca8eac25f0dce5c04e34e2bdd00207a01a24b19ba89ef0804727bf991cc37289
scenario:R13-persisted-pending-fill sha256:a343c1b24e34bb5ee580ea5a03269d514dfe243be67c2d490089171aae73e939
scenario:R13-persisted-response-change sha256:6067c932dcf3ce4649223242a45c3425c7678469d802dbe59d8135ddf8d3e05c
scenario:R13-persisted-response-removal sha256:76268ef573b5ad4f6ce6a70abacf6626dd9b24d7d2b82a50b7484ad0fd406c66
scenario:R13-persisted-review-outcome-change sha256:063f8b7872bbc916413b7541710ab91f94dcb4c5f9c8fc39023ce382ff82f4c7
scenario:R13-persisted-review-revision-change sha256:063f8b7872bbc916413b7541710ab91f94dcb4c5f9c8fc39023ce382ff82f4c7
scenario:R13-persisted-review-target-change sha256:063f8b7872bbc916413b7541710ab91f94dcb4c5f9c8fc39023ce382ff82f4c7
scenario:R13-persisted-same-state sha256:4260557612f68c1156b79e43d919a085591095a812ea5e95e2030eb27dd3b27c
scenario:R13-persisted-terminal-fill sha256:0c152df7faa58c3490b237cc0efcd0a9a24238ab8a127903eae546527bdb5b16
scenario:R13-supplier-review-binding-identical sha256:07c9a4fb8872de5ba41e205b9ebfbfea0d4217ddfe5a09d9e95b687a240b0b11
scenario:R13-supplier-review-binding-revision sha256:2485e7948a29253a801283695695e2d8e83a61e7f6463539dac3b578959ac813
scenario:R13-supplier-review-binding-target sha256:2485e7948a29253a801283695695e2d8e83a61e7f6463539dac3b578959ac813
scenario:R13-supplier-review-binding-terminal sha256:a8e999360a87fc76d41bbc7206ef1820c2f1086adb976ffe26ff28cd260662de
scenario:R14-direct-old-unanswered-carrier-same sha256:f1971ec63a2a4aabb3183e603b85a6a195cfa8c2eaa6f0dcce2e6604189ff981
scenario:R14-direct-old-unanswered-carrier-target sha256:f1971ec63a2a4aabb3183e603b85a6a195cfa8c2eaa6f0dcce2e6604189ff981
scenario:R14-persisted-delete-recreate sha256:0899d2c7965d477568400ff1da18fb539079c5094f25da5abd721ec48574219c
scenario:R14-persisted-hidden-bytes-low-similarity sha256:b6dfa410dc5a1a66185f18c0b6cdf19f257d4ab0bb50abeb0c6a39c678491ac4
scenario:R14-persisted-intermediate-claim-regression sha256:6c171d221307821466717a04ae8740e88447bae9d67f96bc8486fd3823a6369f
scenario:R14-persisted-intermediate-review-regression sha256:b0c2ba5c97ff8ea4a2ffc5e7003b5fa85f73ce96cb2bb4d16fb09275c887c10b
scenario:R14-persisted-merge-carrier-conflict sha256:969f70695d906112281fdcb05e606d5a9da4f8bb932ff3b3b10fcd3ceffc8a18
scenario:R14-persisted-merge-carrier-pending sha256:3bf28372712ef266906503f5a853456f235273fd3c6e73e7949a24b827f9a8e6
scenario:R14-persisted-valid-first-response-low-similarity sha256:c023efb63e51b35a0fb1ce39a56ff2ab920ad232e9c24603bfacf69de9eb503e
scenario:R14-persisted-valid-review-retraction sha256:8958c100d5c2fd0727757caca1cf027d64fe44fd5d7dd815191ac9bb169df244
scenario:R14-supplier-old-answered-carrier-pending sha256:411b093178458cde7454ea7f71db1e5e589566b94122a52243f87e8ac83d672e
scenario:R14-supplier-old-answered-carrier-revision sha256:411b093178458cde7454ea7f71db1e5e589566b94122a52243f87e8ac83d672e
scenario:R14-supplier-old-answered-carrier-same sha256:411b093178458cde7454ea7f71db1e5e589566b94122a52243f87e8ac83d672e
scenario:R14-supplier-old-answered-carrier-target sha256:411b093178458cde7454ea7f71db1e5e589566b94122a52243f87e8ac83d672e
scenario:R14-supplier-old-unanswered-carrier-same sha256:b246f62954d78df745c437ea77b01ab55f82022f05f9172a05977e1da1b5d0d0
scenario:R14-supplier-old-unanswered-carrier-target sha256:b246f62954d78df745c437ea77b01ab55f82022f05f9172a05977e1da1b5d0d0
scenario:R15-old-continuous-preserved sha256:433bc809971dfd4f8bcc2c555a9c6c00d37999bc981aec537a785f6ca58d2c36
scenario:R15-old-hidden-bytes-restore sha256:efda2c716f2482bf4618b1568eea0c8e6b8c23db5d31c6fcf920f035e1afc872
scenario:R15-old-human-binding-restore sha256:650b562bc81176c26e941b8fb08cadd162643c99a5c0a6cd78072e4821a60775
scenario:R15-old-invalid-delete-recreate sha256:19a975770df1601deeffc96bf47523931ac96f147f6730f277b806a0877bb3b6
scenario:R15-old-valid-delete-recreate sha256:c740b89979f12ae3cd20210ff5865c1679987e0966d7a53b9ea897aee7e339ff
scenario:R16-earlier-landed-evidence-reversal sha256:7ff53b4e5f5d5261b15274561d416cfb0ef07dfc33716508ae0318da15dfcd04
scenario:R16-pickup-evolution-0-backlog sha256:9c862c2f23aaf4032f137011a18b7dc041f488da788084c00ddcd4ded2a52fff
scenario:R16-pickup-evolution-2-blocked sha256:35f4c94b1dc0dad12a0355f61f53a45420e38fe187ce924ab257748665cc24b5
scenario:R16-pickup-evolution-3-in-review sha256:27bdc420e35c9db3ac75605a153d36fa17a147fb916c9c123b93301579d6e28f
scenario:R16-pickup-evolution-3-in-review-drop-artifact sha256:b2ae60a59bdbced287811d37d0710e529eda1c744d00ba35a37c77380c9a523a
scenario:R16-pickup-evolution-4-done sha256:27bdc420e35c9db3ac75605a153d36fa17a147fb916c9c123b93301579d6e28f
scenario:R16-support-adoption-drift sha256:e85053853088bb6bda4b969192e5b147f77d68392c7caae9cee1c89ac5ac1a81
scenario:R16-support-forward sha256:850522388cde6e4ad3a1d60c5add1c4cbc239910f63a266da1604fc4c237442d
scenario:R16-support-invalid-source sha256:c50cc32b3f0491fb7a8ae00fc2729fcc95ddad2910a318dafb2d4d301a1988d5
scenario:R16-support-nested-drop sha256:0d958da37cfbaa783eed433cbaae32d1b1961a7bfbc6c9ea6a1553f81f5103e2
scenario:R16-support-permutation-diamond sha256:5032fa4d0b6a1dd0dcbd3dfeb338051bea2eae17ee4b21e9f41aa27d474042e3
scenario:R16-support-reverse-drop sha256:4f920588787aea0a3376e11421f5d29c580f02b593ce5c890c5476ddcffe5802
scenario:R16-support-reverse-preserved sha256:850522388cde6e4ad3a1d60c5add1c4cbc239910f63a266da1604fc4c237442d
scenario:R16-support-source-evolution sha256:850522388cde6e4ad3a1d60c5add1c4cbc239910f63a266da1604fc4c237442d
scenario:R17-carry-absent-arm sha256:7b9425750527dd92a3cd6271546564bf8573fd50d0997bd7a18617c18cf06f0c
scenario:R17-carry-compatible sha256:b33fc74978aa0236bdfd0c8ce59ea27f869cc8467570e40821b95102127a0067
scenario:R17-carry-compatible-reversed sha256:b33fc74978aa0236bdfd0c8ce59ea27f869cc8467570e40821b95102127a0067
scenario:R17-carry-incompatible sha256:022ccb9a30113ef442826e2c1ed5652b10b72d1db778e653a8a4261f8a2b7dee
scenario:R17-carry-outside-duplicate sha256:ae0bcb614239f0f3719a47aa7fd1778748fa8efb2abdffa14a164135d5a65e27
scenario:R17-carry-outside-single sha256:837732f6b827d46706313b13660ef039cc79e13a79dadc97e444e9d5c44c3b5a
scenario:R17-dynamic-support-traversal-exact sha256:0de4dfcd8beef66200231630600becfb70d73518dd527aff0221060c58536f20
scenario:R17-dynamic-support-traversal-plus-one-refused sha256:d49fb869a26e3c3867d24a79b0a34ed4f67c9fff14b0662e578124a4099fd87a
scenario:R17-flat-tree-peak-exact sha256:e606dc84af59b478121374efe63263cd164468dc75a14905bdae5850662a2976
scenario:R17-flat-tree-peak-plus-one-refused sha256:d4a95635554890fe846a1265c1c7fc65b1e2cf42bb830b9bab785018e6cf27d7
scenario:R17-graph-line-peak-bytes-exact sha256:474d5e22c7e03f502f8ee785d3552a8e602aba3b64625f33b6943276c75b24b0
scenario:R17-graph-line-peak-bytes-plus-one-refused sha256:c29a0c7214bb9e1cd3ac50497199e13eabb4f385c894bf04d96c137d0f12783b
scenario:R17-graph-output-bytes-exact sha256:474d5e22c7e03f502f8ee785d3552a8e602aba3b64625f33b6943276c75b24b0
scenario:R17-graph-output-bytes-plus-one-refused sha256:c29a0c7214bb9e1cd3ac50497199e13eabb4f385c894bf04d96c137d0f12783b
scenario:R17-graph-parent-tokens-exact sha256:474d5e22c7e03f502f8ee785d3552a8e602aba3b64625f33b6943276c75b24b0
scenario:R17-graph-parent-tokens-plus-one-refused sha256:c29a0c7214bb9e1cd3ac50497199e13eabb4f385c894bf04d96c137d0f12783b
scenario:R17-object-payload-peak-exact sha256:028988f232b02e34ebcd93c4883da2cb83ca4703c8e562035c6f27aa0cdd2acd
scenario:R17-object-payload-peak-plus-one-refused sha256:9402e6f329401b56739a773a7142c9411629f6411854f636f9cf9d332a0c4611
scenario:R17-outside-C-neutral-parent-valid-restack sha256:7efe001e3c7b246ab395d4897d4e3b978cb5ef2cd2e880e77f075782fddef0ce
scenario:R17-persisted-outside-duplicate sha256:4a2d2d7e23e4798340a752e4708e85992bd6713a01cfe6979895345953fa9e37
scenario:R17-persisted-outside-duplicate-reversed sha256:4a2d2d7e23e4798340a752e4708e85992bd6713a01cfe6979895345953fa9e37
scenario:R17-persisted-outside-single sha256:641588d58a38957047cd98d2463bc9877700196ea38288972ff67d9ea37152fe
scenario:R17-persisted-outside-single-reversed sha256:641588d58a38957047cd98d2463bc9877700196ea38288972ff67d9ea37152fe
scenario:R17-persisted-unauthorized-absent-arm sha256:81dc63fe3b7e52b66bec9dbb5d6074cd20c605599fa9f0538e67e6704a1684c4
scenario:R17-persisted-unauthorized-absent-arm-reversed sha256:81dc63fe3b7e52b66bec9dbb5d6074cd20c605599fa9f0538e67e6704a1684c4
scenario:R17-persisted-valid-absent-arm sha256:fc2ebf334280a31bf395aa1df0720709f64e5d5703680b0f403b8a9222a0368b
scenario:R17-persisted-valid-absent-arm-reversed sha256:fc2ebf334280a31bf395aa1df0720709f64e5d5703680b0f403b8a9222a0368b
scenario:R17-precharge-P22-budget sha256:3cd8d7c46e548416920999e7fcf21fc47f23636b5c71481fc4f24cb20f7b8135
scenario:R17-support-serialized-exact sha256:181ba0d0170b0f61cab3034cb97a826122be1063643eea93b85155dade68de39
scenario:R17-support-serialized-plus-one-refused sha256:58d48a0d4c80fbb019c7607e3363e9b1e2869ef2b1195530e696f124afbf5f38
scenario:R17-unreadable-outside-C-ancestor-stays-unopened sha256:9485768cd536a68596fd0b9b01237a116d88401a50e19733412f81821e1d003f
scenario:R17-unreadable-outside-C-boundary sha256:599eced072e2f19d2078d01241fc5a599d87898a3b57f4ca9ad733cda5e1ce11
scenario:R17-wide-outside-C-boundary-budget sha256:19bea2720bce2722accc7ce1ccccd34ff10c277db487fd3cb136a775b1f80bef
scenario:R3-01-two-invalid-causal-sources sha256:1b4b5774a1bd551021a8891633f5d974d1330ad36101c8b9edf972605704f79f
scenario:R3-02-invalid-valid-causal-competition sha256:3a56adced0b47c217679b3e66fe118c8e9fb6a40e52807b0314d5af00ec5bcc4
scenario:R3-03-valid-supplier-plus-invalid-parent-at-N-blocks sha256:4c88a11cc1bd3f265fc2e0f811a8048eb95578cc62beba5c247b1fff40995caf
scenario:R4-01-same-root-valid-diamond sha256:4f377fb34ff2ccd977457fa828c076828597d6ba30d8127eca749065413fc3ea
scenario:R4-02-distinct-valid-root-diamond sha256:7e2ba91e253d23b760a15fca45e83f15b9413a3461db475880aa23a4eaeba8d6
scenario:R4-03-equal-root-plus-invalid-diamond sha256:7cd9bedf89776ea5ac98e8dff87f9407421f4e016d1cd55189b2cc6d37d47104
scenario:R5-01-invalid-redelete-after-supplier-reintroduction sha256:487a1c84014e36892c19027dc3575952921bf06b1bc29c394dde3dbe627d34cf
scenario:R5-02-valid-redelete-after-supplier-reintroduction sha256:d5c3936f0f32e0446677432e333a33a3699e251c840d689bc49f1822cd778d71
scenario:R6-01-valid-plus-invalid-all-absent sha256:d88f0f503a72fe038a645088fb47f49fb2621de0358f5054271fa596282318cf
scenario:R6-02-valid-plus-ambiguous-all-absent sha256:eeaccb31b66ef1bdb92916c7eedf12906f71e66d0630a3399a613521e879c08c
scenario:R6-03-two-invalid-all-absent sha256:9a3fce5b58c75d37838f42d98c26dd93ad2db81fcda1f1b52628ca2df36defdd
scenario:R6-04-same-valid-root-all-absent-wrappers sha256:9660ae1d8ccf79a99e8407a7123c9bdbc1e5612a38d0139827a1055d5e8d1b94
scenario:R8-direct-human-response-conflict sha256:ede74125c9adb379268febd01ebc1ca16d6f54c587aeb881297592564b4e9dfc
scenario:R8-direct-human-response-identical sha256:ede74125c9adb379268febd01ebc1ca16d6f54c587aeb881297592564b4e9dfc
scenario:R8-review-binding-divergent sha256:a7e76821fdd1e0642071d45b6d239d1e99cd07e6f641aa577c80c9278269cae3
scenario:R8-review-binding-identical sha256:b36d4c923d1041edb2141b069c0656db0d605cb8e226a36d91e0685f06df898b
scenario:R8-review-binding-terminal-conflict sha256:d327426e2a12ba2c08d12fc01bad2f86d4eca0d12a5c42830cbbc935d140bafd
scenario:R8-supplier-human-response-conflict sha256:a7a88e387c8ae0beea99c98d679fa137463c0136886a462cedfb9980e93cea43
scenario:R8-supplier-human-response-identical sha256:7c1db6f2084fc6ab17bb59b796ade8f1721e9f4d87bbd07f637d6011a37b2477
scenario:R9-direct-review-revision-pending-fill sha256:76eeb95f024390200d2b30a16581975f6b56396436d255d89e71de24d451e3bb
scenario:R9-direct-review-target-pending-fill sha256:76eeb95f024390200d2b30a16581975f6b56396436d255d89e71de24d451e3bb
scenario:R9-supplier-review-revision-pending-fill sha256:eed70bb61607d49a48e42a018cdd926e62c7231ea74d9a29884f6a3713929d38
scenario:R9-supplier-review-target-pending-fill sha256:eed70bb61607d49a48e42a018cdd926e62c7231ea74d9a29884f6a3713929d38
scenario:W0-fast-forward-return sha256:f842e5ef0b147b9005d1834b5a67d3b742f6fc45e584094cc839d3da9520c761
scenario:W1-pre-PR-push-exact-endpoints sha256:715801d19e7b22038c2c09b805c3c13d856c58b12261225f80614fe50f319a22
scenario:W2-base-advance-retarget-invariant sha256:34d6200aa75b7e483cd9f223876451beedc3c4cfddd85d2b4a92ee9bcfec8211
scenario:W3-multiple-PR-API-zero-calls sha256:335aaaf5250846599ba647a056a906d84733b19c8a8f3706c0252da17705c02e
scenario:W4-stale-rerun-exact-inputs sha256:b81af0987f98c9e5c6e6107d634b2371050f39651449988430bf43c002137c2f
scenario:W5-missing-O-coverage-unavailable sha256:0cc6cd8a6445c686471ba197dbb1c2c6b9f09b36812460ac9028bc1060d48406
scenario:W6-created-deleted-zero-endpoints sha256:110c4f48a71cf41b70cdeda64e057224092a4e443a9a1d98be6afae72c1bf94c
scenario:W7-PR-synchronize-top-level-endpoints sha256:a6c4c9dffcc53b1b997f90cdac676c7af4facd9d089a8e5db119c003816ce2a3
summary sha256:74a7f9e3ab72663556d8c067e825e9ac744fd232524bfcbd337a2e8fd7fce00b
"""
RAW_SHAPE_SHA256 = dict(
    line.split(" ", 1)
    for line in RAW_SHAPE_CATALOG_V5.splitlines()
    if " " in line
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


def raw_shape(value: Any) -> Any:
    """Return the exact recursive key/type grammar of a raw JSON value."""

    if isinstance(value, dict):
        return [
            "object",
            [[key, raw_shape(value[key])] for key in sorted(value)],
        ]
    if isinstance(value, list):
        return ["array", [raw_shape(item) for item in value]]
    if value is None:
        return "null"
    if type(value) is bool:
        return "boolean"
    if type(value) is int:
        return "integer"
    if type(value) is float:
        return "number"
    if isinstance(value, str):
        return "string"
    raise EvidenceError(f"raw value has unsupported type {type(value).__name__}")


def raw_shape_digest(value: Any) -> str:
    return digest_bytes(canonical_bytes(raw_shape(value)))


def raw_record_key(value: dict) -> str:
    candidates = []
    if "scenario" in value:
        candidates.append(f"scenario:{value['scenario']}")
    if "control" in value:
        candidates.append(f"control:{value['control']}")
    if "scenario_alias_inventory" in value:
        candidates.append("aliases")
    if "summary" in value:
        candidates.append("summary")
    elif "r17_parent_permutation" in value:
        candidates.append("parent-permutation")
    if len(candidates) != 1:
        raise EvidenceError(
            f"raw row kind is missing or ambiguous: {sorted(candidates)}"
        )
    return candidates[0]


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


def validate_permutation_record(value: Any, context: str):
    require_keys(
        value,
        (
            "r17_parent_permutation",
            "r17_persisted_parent_permutations",
            "status",
        ),
        context,
    )
    signatures = value["r17_parent_permutation"]
    if (
        value["status"] != "PASS"
        or not isinstance(signatures, list)
        or len(signatures) != 2
        or signatures[0] != signatures[1]
    ):
        raise EvidenceError(f"{context} carry-parent pair differs")
    for index, signature in enumerate(signatures):
        require_keys(
            signature,
            (
                "absent_arm_count",
                "classification",
                "event_mode",
                "evidence_status",
                "merge_role_multiset",
                "outside_collision_multiplicities",
            ),
            f"{context}.r17_parent_permutation[{index}]",
        )
    persisted = value["r17_persisted_parent_permutations"]
    if not isinstance(persisted, dict) or tuple(sorted(persisted)) != PERSISTED_VARIANTS:
        raise EvidenceError(f"{context} persisted permutation catalog differs")
    for variant in PERSISTED_VARIANTS:
        pair = persisted[variant]
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or pair[0] != pair[1]
        ):
            raise EvidenceError(
                f"{context} persisted permutation differs for {variant}"
            )
        for index, signature in enumerate(pair):
            require_keys(
                signature,
                (
                    "absent_arm_count",
                    "classification",
                    "evidence_status",
                    "outside_collision_multiplicities",
                    "reason_code",
                ),
                f"{context}.r17_persisted_parent_permutations."
                f"{variant}[{index}]",
            )


def normalized_record(value: dict) -> dict:
    result = copy.deepcopy(value)
    if "summary" in result:
        result.pop("git", None)
        result.pop("python", None)
    if result.get("control") == "locale-git-error-stream-equality":
        observation = result["locale_observation"]
        ambient = observation.pop("ambient_reasons")
        observation["ambient_reasons_differ"] = (
            ambient["C"] != ambient["fr_FR.UTF-8"]
        )
    return result


class Stream:
    def __init__(self, path: Path):
        self.path = path
        self.raw = path.read_bytes()
        self._load()

    @classmethod
    def from_bytes(cls, raw: bytes, label: str):
        stream = cls.__new__(cls)
        stream.path = Path(label)
        stream.raw = raw
        stream._load()
        return stream

    def _load(self):
        self.objects = []
        for number, line in enumerate(self.raw.splitlines(), start=1):
            if not line:
                raise EvidenceError(f"blank JSONL line {number}")
            value = load_json(line)
            if not isinstance(value, dict):
                raise EvidenceError(f"JSONL line {number} is not an object")
            key = raw_record_key(value)
            expected_shape = RAW_SHAPE_SHA256.get(key)
            if expected_shape is None:
                raise EvidenceError(
                    f"raw row {number} {key!r} is outside the closed grammar"
                )
            observed_shape = raw_shape_digest(value)
            if observed_shape != expected_shape:
                raise EvidenceError(
                    f"raw row {number} {key!r} grammar differs: "
                    f"expected {expected_shape}, observed {observed_shape}"
                )
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
        expected_shape_keys = {
            *(f"scenario:{name}" for name in SCENARIO_IDS),
            *(f"control:{name}" for name in CONTROL_IDS),
            "aliases",
            "parent-permutation",
            "summary",
        }
        if set(RAW_SHAPE_SHA256) != expected_shape_keys:
            raise EvidenceError(
                "raw grammar catalog differs from the closed row inventory"
            )
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
        validate_permutation_record(self.permutation, "stream permutation")

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
    observation = None
    if row["control"] == "buffered-graph-output":
        observation = {
            **row["budget_observation"],
            "kind": "buffered-graph-output",
        }
    elif row["control"] == "stream-malformed-truncated-final-line":
        observation = {
            "kind": "stream-grammar-cleanup",
            "variants": row["stream_observation"],
        }
    elif row["control"] == "posthoc-budget-accounting":
        observation = {
            "baseline_metrics": row["budget_observation"][
                "baseline_metrics"
            ],
            "baseline_overflows": row["budget_observation"][
                "baseline_overflows"
            ],
            "damaged_metrics": row["budget_observation"][
                "damaged_metrics"
            ],
            "kind": "precharge-budget",
            "limit": row["budget_observation"]["limit"],
            "posthoc_reference_metrics": row["budget_observation"][
                "posthoc_reference_metrics"
            ],
        }
    elif row["control"] == "locale-git-error-stream-equality":
        locale = normalized_record(row)["locale_observation"]
        observation = {
            "ambient_reasons_differ": locale["ambient_reasons_differ"],
            "kind": "locale-git-diagnostics",
            "stable_full_results_equal": locale[
                "stable_full_results_equal"
            ],
            "stable_reasons": locale["stable_reasons"],
        }
    return {
        "authority_edges": [edge_projection(x) for x in row["authority_edges"]],
        "baseline_classification": row["baseline_classification"],
        "damaged_classification": row["damaged_classification"],
        "endpoints": endpoints(row), "expected_baseline": row["expected_baseline"],
        "id": row["control"], "observation": observation,
        "propagation_edges": [propagation_projection(x) for x in row["propagation_edges"]],
        "record_sha256": record_digest(normalized_record(row)),
        "status": row["status"],
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


def zero_partial_result(row):
    return not any(
        row[key]
        for key in (
            "actions",
            "authority_edges",
            "carry_proofs",
            "mutation_edges",
            "propagation_edges",
            "support_checks",
        )
    )


def persisted_case_projection(row):
    return {
        "absent_arm_count": sum(
            len(proof["absent_c_parents"])
            for proof in row["carry_proofs"]
        ),
        "audit_exit": row["audit_exit"],
        "classification": row["classification"],
        "collision_multiplicities": sorted(
            collision["multiplicity"]
            for proof in row["carry_proofs"]
            for collision in proof["outside_collisions"]
        ),
        "evidence_status": row["evidence_verdict"]["status"],
        "id": row["scenario"],
        "reason_codes": [action["reason_code"] for action in row["actions"]],
        "record_sha256": record_digest(normalized_record(row)),
        "reverse_parents": row["details"]["reverse_parents"],
        "variant": row["details"]["variant"],
    }


def budget_case_projection(row):
    return {
        "audit_exit": row["audit_exit"],
        "classification": row["classification"],
        "counter_policy": row["details"]["budget_counter_policy"],
        "evidence_status": row["evidence_verdict"]["status"],
        "limit": row["details"]["demonstration_limit"],
        "max_work_counter_names": row["details"]["max_work_counter_names"],
        "measured_max_work": row["details"]["measured_max_work"],
        "measured_work_counters": row["details"]["measured_work_counters"],
        "overflow_by_one": row["details"]["overflow_by_one"],
        "record_sha256": record_digest(normalized_record(row)),
        "transactional_zero_results": zero_partial_result(row),
    }


def precharge_budget_projection(row):
    return {
        "audit_exit": row["audit_exit"],
        "classification": row["classification"],
        "counter_policy": row["details"]["budget_counter_policy"],
        "evidence_reason": row["evidence_verdict"]["reason"],
        "evidence_status": row["evidence_verdict"]["status"],
        "limit": row["details"]["budget_limit"],
        "posthoc_reference_metrics": row["details"][
            "posthoc_reference_metrics"
        ],
        "precharge_expected_metrics": row["metrics"],
        "record_sha256": record_digest(normalized_record(row)),
        "transactional_zero_results": zero_partial_result(row),
    }


def execution_bound_side_projection(row, counter):
    return {
        "audit_exit": row["audit_exit"],
        "classification": row["classification"],
        "counter_value": row["metrics"][counter],
        "evidence_status": row["evidence_verdict"]["status"],
        "limit": row["details"]["typed_budget_limit"],
        "metrics": {
            key: row["metrics"][key]
            for key in (
                "git_processes", "graph_buffered_bytes",
                "graph_process_cleanup_checks", "graph_process_reaps",
                "graph_process_terminations",
                "graph_stream_peak_chunk_bytes", "object_process_reaps",
                "object_process_terminations", "queue_snapshots_requested",
                "support_certificate_calls",
            )
        },
        "overflow_by_one": row["details"]["overflow_by_one"],
        "record_sha256": record_digest(normalized_record(row)),
        "transactional_zero_results": zero_partial_result(row),
    }


def execution_bounds_projection(stream):
    pairs = {}
    for label, counter, _value, exact_id, overflow_id in EXECUTION_BOUND_CASES:
        pairs[label] = {
            "counter": counter,
            "exact": execution_bound_side_projection(
                stream.scenarios[exact_id], counter
            ),
            "limit_plus_one": execution_bound_side_projection(
                stream.scenarios[overflow_id], counter
            ),
            "scenario_ids": {
                "exact": exact_id,
                "limit_plus_one": overflow_id,
            },
        }
    p22 = stream.scenarios["P22-PCX-18-one-pass-many-actions"]
    graph = stream.scenarios["R17-graph-parent-tokens-exact"]
    return {
        "composition_observation": {
            "git_processes": p22["metrics"]["git_processes"],
            "production_parent_queries": p22["metrics"][
                "production_parent_queries"
            ],
            "record_sha256": record_digest(normalized_record(p22)),
        },
        "pairs": pairs,
        "runtime_milestone_commits": list(RUNTIME_MILESTONE_COMMITS),
        "streaming_graph_contract": {
            "bounded_chunk_bytes": 256,
            "raw_graph_bytes": graph["details"]["budget_contract"][
                "raw_graph_bytes"
            ],
            "raw_graph_fields": graph["details"]["budget_contract"][
                "raw_graph_fields"
            ],
            "raw_graph_lines": graph["details"]["budget_contract"][
                "raw_graph_lines"
            ],
        },
    }


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
    persisted_ids = [
        name for name in SCENARIO_IDS if name.startswith("R17-persisted-")
    ]
    exact_budget = stream.scenarios["PCX-20a-budget-below-limit"]
    overflow_budget = stream.scenarios["PCX-20b-budget-overflow"]
    precharge_budget = stream.scenarios["R17-precharge-P22-budget"]
    wide_budget = stream.scenarios["R17-wide-outside-C-boundary-budget"]
    locale_control = stream.controls["locale-git-error-stream-equality"]
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
        "evidence_supersession": SUPERSEDED_EVIDENCE,
        "execution_bounds": execution_bounds_projection(stream),
        "measured_budget": {
            "exact": budget_case_projection(exact_budget),
            "limit_plus_one": budget_case_projection(overflow_budget),
            "precharge_P22": precharge_budget_projection(
                precharge_budget
            ),
            "wide_boundary": {
                "audit_exit": wide_budget["audit_exit"],
                "budget_contract": wide_budget["details"]["budget_contract"],
                "classification": wide_budget["classification"],
                "evidence_status": wide_budget["evidence_verdict"]["status"],
                "metrics": {
                    key: wide_budget["metrics"][key]
                    for key in (
                        "graph_commits",
                        "graph_lines",
                        "graph_output_bytes",
                        "graph_parent_edges",
                        "graph_parent_tokens",
                        "graph_process_cleanup_checks",
                        "graph_process_reaps",
                        "graph_process_terminations",
                        "graph_stream_peak_chunk_bytes",
                        "object_reads",
                        "queue_snapshots_requested",
                    )
                },
                "outside_parent_count": len(
                    wide_budget["details"]["outside_parents"]
                ),
                "record_sha256": record_digest(
                    normalized_record(wide_budget)
                ),
                "reference_oids": wide_budget["details"][
                    "review_reference_oids"
                ],
                "transactional_zero_results": zero_partial_result(
                    wide_budget
                ),
            },
        },
        "parent_permutation": stream.permutation,
        "persisted_carry": {
            "cases": [
                persisted_case_projection(stream.scenarios[name])
                for name in persisted_ids
            ],
            "parent_permutations": stream.permutation[
                "r17_persisted_parent_permutations"
            ],
            "reference_oids": {
                "outside_single": stream.scenarios[
                    "R17-persisted-outside-single"
                ]["details"]["review_reference_oids"],
                "valid_absent_arm": stream.scenarios[
                    "R17-persisted-valid-absent-arm"
                ]["details"]["review_reference_oids"],
            },
        },
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
        "raw_grammar": {
            "catalog_sha256": digest_bytes(
                canonical_bytes(RAW_SHAPE_SHA256)
            ),
            "enforcement": "recursive exact key/list/type shape before projection",
            "record_kinds": len(RAW_SHAPE_SHA256),
            "unknown_field_exit": 1,
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
        "stable_git_diagnostics": {
            "ambient_reasons_differ": normalized_record(locale_control)[
                "locale_observation"
            ]["ambient_reasons_differ"],
            "forced_environment": {
                "LANG": "C",
                "LANGUAGE": "C",
                "LC_ALL": "C",
                "TZ": "UTC",
            },
            "record_sha256": record_digest(
                normalized_record(locale_control)
            ),
            "stable_full_results_equal": locale_control[
                "locale_observation"
            ]["stable_full_results_equal"],
            "stable_reasons": locale_control["locale_observation"][
                "stable_reasons"
            ],
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
        "endpoints", "expected_baseline", "id", "observation", "propagation_edges",
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
        if (
            row["id"] not in {
                "buffered-graph-output",
                "locale-git-error-stream-equality",
                "posthoc-budget-accounting",
            }
            and row["damaged_classification"] == row["expected_baseline"]
        ):
            raise EvidenceError(f"{context} damage did not change verdict")
        if row["id"] == "buffered-graph-output":
            observation = row["observation"]
            require_keys(
                observation,
                (
                    "baseline_graph_metrics", "damaged_graph_metrics",
                    "kind", "raw_graph_bytes",
                ),
                f"{context}.observation",
            )
            if (
                observation["kind"] != "buffered-graph-output"
                or observation["raw_graph_bytes"] != 2952
                or observation["baseline_graph_metrics"][
                    "graph_output_bytes"
                ] >= 2952
                or observation["damaged_graph_metrics"][
                    "graph_buffered_bytes"
                ] != 2952
                or observation["baseline_graph_metrics"][
                    "graph_process_reaps"
                ] != 1
                or observation["damaged_graph_metrics"][
                    "graph_process_reaps"
                ] != 1
            ):
                raise EvidenceError(
                    f"{context} buffered graph observation changed"
                )
        elif row["id"] == "stream-malformed-truncated-final-line":
            observation = row["observation"]
            require_keys(
                observation, ("kind", "variants"),
                f"{context}.observation",
            )
            require_keys(
                observation["variants"], ("malformed", "truncated"),
                f"{context}.observation.variants",
            )
            for variant, item in observation["variants"].items():
                require_keys(
                    item,
                    (
                        "local_rows_before_failure", "metrics",
                        "published_rows", "reason",
                    ),
                    f"{context}.observation.variants.{variant}",
                )
                require_keys(
                    item["metrics"], METRIC_KEYS,
                    f"{context}.observation.variants.{variant}.metrics",
                )
                if (
                    observation["kind"] != "stream-grammar-cleanup"
                    or item["reason"] != f"{variant} graph line"
                    or item["local_rows_before_failure"] != 1
                    or item["published_rows"] != 0
                    or item["metrics"]["graph_process_reaps"] != 1
                    or item["metrics"]["graph_process_cleanup_checks"] != 1
                ):
                    raise EvidenceError(
                        f"{context} stream cleanup observation changed"
                    )
        elif row["id"] == "posthoc-budget-accounting":
            observation = row["observation"]
            require_keys(
                observation,
                (
                    "baseline_metrics", "baseline_overflows",
                    "damaged_metrics", "kind", "limit",
                    "posthoc_reference_metrics",
                ),
                f"{context}.observation",
            )
            if (
                row["baseline_classification"] != "blocking-finding"
                or row["damaged_classification"] != "blocking-finding"
                or observation != {
                    "baseline_metrics": PRECHARGE_P22_METRICS,
                    "baseline_overflows": [["object_reads", 134]],
                    "damaged_metrics": POSTHOC_P22_METRICS,
                    "kind": "precharge-budget",
                    "limit": 133,
                    "posthoc_reference_metrics": POSTHOC_P22_METRICS,
                }
            ):
                raise EvidenceError(
                    f"{context} post-hoc budget observation changed"
                )
        elif row["id"] == "locale-git-error-stream-equality":
            observation = row["observation"]
            require_keys(
                observation,
                (
                    "ambient_reasons_differ", "kind",
                    "stable_full_results_equal", "stable_reasons",
                ),
                f"{context}.observation",
            )
            require_keys(
                observation["stable_reasons"],
                ("C", "fr_FR.UTF-8"),
                f"{context}.observation.stable_reasons",
            )
            stable_reasons = observation["stable_reasons"]
            if (
                row["baseline_classification"] != "unreadable"
                or row["damaged_classification"] != "unreadable"
                or observation["kind"] != "locale-git-diagnostics"
                or observation["ambient_reasons_differ"] is not True
                or observation["stable_full_results_equal"] is not True
                or stable_reasons["C"] != stable_reasons["fr_FR.UTF-8"]
                or not stable_reasons["C"].startswith(
                    "missing-or-malformed-commit:"
                )
            ):
                raise EvidenceError(
                    f"{context} stable Git diagnostic observation changed"
                )
        elif row["observation"] is not None:
            raise EvidenceError(f"{context} has an unknown observation")
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
        "boundary_ancestry", "endpoint_contract", "evidence_supersession",
        "execution_bounds", "measured_budget", "parent_permutation",
        "persisted_carry",
        "raw_grammar",
        "r3_full_frontier", "r6_outside_boundary_disposition",
        "retired_catalog", "reviewer_dag", "stable_git_diagnostics",
        "workflow_input_matrix",
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
    if core["evidence_supersession"] != SUPERSEDED_EVIDENCE:
        raise EvidenceError("evidence schema supersession changed")
    require_keys(
        core["evidence_supersession"],
        ("artifacts", "replacement_schema"),
        "evidence_supersession",
    )
    for index, artifact in enumerate(
        core["evidence_supersession"]["artifacts"]
    ):
        require_keys(
            artifact,
            ("commit", "disposition", "schema"),
            f"evidence_supersession.artifacts[{index}]",
        )
        require_oid(
            artifact["commit"],
            f"evidence_supersession.artifacts[{index}].commit",
        )
    bounds = core["execution_bounds"]
    require_keys(
        bounds,
        (
            "composition_observation", "pairs", "runtime_milestone_commits",
            "streaming_graph_contract",
        ),
        "execution_bounds",
    )
    if bounds["runtime_milestone_commits"] != list(
        RUNTIME_MILESTONE_COMMITS
    ):
        raise EvidenceError("execution-bound runtime commits changed")
    for index, commit in enumerate(bounds["runtime_milestone_commits"]):
        require_oid(commit, f"execution_bounds.runtime_milestone_commits[{index}]")
    require_keys(
        bounds["streaming_graph_contract"],
        (
            "bounded_chunk_bytes", "raw_graph_bytes", "raw_graph_fields",
            "raw_graph_lines",
        ),
        "execution_bounds.streaming_graph_contract",
    )
    if bounds["streaming_graph_contract"] != {
        "bounded_chunk_bytes": 256,
        "raw_graph_bytes": 2952,
        "raw_graph_fields": [2, 2, 66, 2],
        "raw_graph_lines": 4,
    }:
        raise EvidenceError("streaming graph contract changed")
    require_keys(
        bounds["composition_observation"],
        ("git_processes", "production_parent_queries", "record_sha256"),
        "execution_bounds.composition_observation",
    )
    p22_row = by_id["P22-PCX-18-one-pass-many-actions"]
    if bounds["composition_observation"] != {
        "git_processes": 135,
        "production_parent_queries": 129,
        "record_sha256": p22_row["record_sha256"],
    }:
        raise EvidenceError("P22 production-helper composition changed")
    require_digest(
        bounds["composition_observation"]["record_sha256"],
        "execution_bounds.composition_observation.record_sha256",
    )
    if set(bounds["pairs"]) != {case[0] for case in EXECUTION_BOUND_CASES}:
        raise EvidenceError("execution-bound pair inventory changed")
    side_keys = (
        "audit_exit", "classification", "counter_value", "evidence_status",
        "limit", "metrics", "overflow_by_one", "record_sha256",
        "transactional_zero_results",
    )
    selected_metric_keys = (
        "git_processes", "graph_buffered_bytes",
        "graph_process_cleanup_checks", "graph_process_reaps",
        "graph_process_terminations", "graph_stream_peak_chunk_bytes",
        "object_process_reaps", "object_process_terminations",
        "queue_snapshots_requested", "support_certificate_calls",
    )
    for label, counter, value, exact_id, overflow_id in EXECUTION_BOUND_CASES:
        pair = bounds["pairs"][label]
        context = f"execution_bounds.pairs.{label}"
        require_keys(
            pair, ("counter", "exact", "limit_plus_one", "scenario_ids"),
            context,
        )
        if pair["counter"] != counter or pair["scenario_ids"] != {
            "exact": exact_id,
            "limit_plus_one": overflow_id,
        }:
            raise EvidenceError(f"{context} identity changed")
        require_keys(
            pair["scenario_ids"], ("exact", "limit_plus_one"),
            f"{context}.scenario_ids",
        )
        for side_name, scenario_id in (
            ("exact", exact_id), ("limit_plus_one", overflow_id)
        ):
            side = pair[side_name]
            side_context = f"{context}.{side_name}"
            require_keys(side, side_keys, side_context)
            require_keys(side["metrics"], selected_metric_keys, f"{side_context}.metrics")
            row = by_id[scenario_id]
            if side["record_sha256"] != row["record_sha256"]:
                raise EvidenceError(f"{side_context} record changed")
            if side["metrics"] != {
                key: row["metrics"][key] for key in selected_metric_keys
            }:
                raise EvidenceError(f"{side_context} selected metrics changed")
            require_digest(side["record_sha256"], f"{side_context}.record_sha256")
        exact = pair["exact"]
        overflow = pair["limit_plus_one"]
        if (
            exact["audit_exit"] != 0
            or exact["classification"] != "no-finding"
            or exact["counter_value"] != value
            or exact["limit"] != value
            or exact["overflow_by_one"] is not False
            or exact["transactional_zero_results"] is not False
            or overflow["audit_exit"] != 2
            or overflow["classification"] != "blocking-finding"
            or overflow["evidence_status"] != "ambiguous"
            or overflow["counter_value"] != value
            or overflow["limit"] != value - 1
            or overflow["overflow_by_one"] is not True
            or overflow["transactional_zero_results"] is not True
        ):
            raise EvidenceError(f"{context} exact/+1 contract changed")
        if label.startswith("graph_") and (
            exact["metrics"]["graph_buffered_bytes"] != 0
            or overflow["metrics"]["graph_buffered_bytes"] != 0
            or exact["metrics"]["graph_process_reaps"] != 1
            or overflow["metrics"]["graph_process_reaps"] != 1
            or exact["metrics"]["graph_stream_peak_chunk_bytes"] > 256
            or overflow["metrics"]["graph_stream_peak_chunk_bytes"] > 256
        ):
            raise EvidenceError(f"{context} streaming cleanup bound changed")
        if label == "object_payload_peak_bytes" and (
            overflow["metrics"]["object_process_terminations"] != 1
            or overflow["metrics"]["object_process_reaps"] != 1
        ):
            raise EvidenceError(f"{context} object cleanup bound changed")
    permutation = core["parent_permutation"]
    validate_permutation_record(
        permutation, "core_claims.parent_permutation"
    )
    persisted = core["persisted_carry"]
    require_keys(
        persisted, ("cases", "parent_permutations", "reference_oids"),
        "persisted_carry",
    )
    persisted_ids = [
        name for name in SCENARIO_IDS if name.startswith("R17-persisted-")
    ]
    cases = persisted["cases"]
    if [case.get("id") for case in cases] != persisted_ids:
        raise EvidenceError("persisted carry case catalog changed")
    require_keys(
        persisted["reference_oids"],
        ("outside_single", "valid_absent_arm"),
        "persisted_carry.reference_oids",
    )
    if persisted["reference_oids"] != {
        "outside_single": PERSISTED_OUTSIDE_REFERENCE_OIDS,
        "valid_absent_arm": PERSISTED_ABSENT_REFERENCE_OIDS,
    }:
        raise EvidenceError("persisted carry reviewer OID catalog changed")
    for group, references in persisted["reference_oids"].items():
        for label, oid in references.items():
            require_oid(oid, f"persisted_carry.reference_oids.{group}.{label}")
    expected_persisted_permutations = permutation[
        "r17_persisted_parent_permutations"
    ]
    if persisted["parent_permutations"] != expected_persisted_permutations:
        raise EvidenceError("persisted carry parent permutations changed")
    for index, case in enumerate(cases):
        context = f"persisted_carry.cases[{index}]"
        require_keys(
            case,
            (
                "absent_arm_count", "audit_exit", "classification",
                "collision_multiplicities", "evidence_status", "id",
                "reason_codes", "record_sha256", "reverse_parents",
                "variant",
            ),
            context,
        )
        row = by_id[case["id"]]
        variant = case["id"][len("R17-persisted-"):]
        reversed_case = variant.endswith("-reversed")
        if reversed_case:
            variant = variant[:-len("-reversed")]
        expected_reason = (
            "persisted-outside-C-collision"
            if variant.startswith("outside-")
            else "persisted-delete-recreate"
        )
        expected_collisions = {
            "outside-duplicate": [2],
            "outside-single": [1],
            "unauthorized-absent-arm": [],
            "valid-absent-arm": [],
        }[variant]
        expected_absent = int(variant.endswith("absent-arm"))
        if (
            case["classification"] != "blocking-finding"
            or case["audit_exit"] != 1
            or case["evidence_status"] != "ambiguous"
            or case["reason_codes"] != [expected_reason]
            or case["collision_multiplicities"] != expected_collisions
            or case["absent_arm_count"] != expected_absent
            or case["reverse_parents"] is not reversed_case
            or case["variant"] != variant
            or case["record_sha256"] != row["record_sha256"]
        ):
            raise EvidenceError(f"{context} semantic claim changed")
        require_digest(case["record_sha256"], f"{context}.record_sha256")

    measured = core["measured_budget"]
    require_keys(
        measured,
        ("exact", "limit_plus_one", "precharge_P22", "wide_boundary"),
        "measured_budget",
    )
    for name, scenario in (
        ("exact", "PCX-20a-budget-below-limit"),
        ("limit_plus_one", "PCX-20b-budget-overflow"),
    ):
        claim = measured[name]
        context = f"measured_budget.{name}"
        require_keys(
            claim,
            (
                "audit_exit", "classification", "counter_policy",
                "evidence_status", "limit", "max_work_counter_names",
                "measured_max_work", "measured_work_counters",
                "overflow_by_one", "record_sha256",
                "transactional_zero_results",
            ),
            context,
        )
        require_keys(
            claim["measured_work_counters"], METRIC_KEYS,
            f"{context}.measured_work_counters",
        )
        for key, value in claim["measured_work_counters"].items():
            require_nonnegative_int(
                value, f"{context}.measured_work_counters.{key}"
            )
        require_nonnegative_int(claim["limit"], f"{context}.limit")
        require_nonnegative_int(
            claim["measured_max_work"], f"{context}.measured_max_work"
        )
        maximum = max(claim["measured_work_counters"].values())
        names = sorted(
            key
            for key, value in claim["measured_work_counters"].items()
            if value == maximum
        )
        expected = {
            "exact": {
                "audit_exit": 0,
                "classification": "no-finding",
                "evidence_status": "valid",
                "overflow_by_one": False,
                "transactional_zero_results": False,
            },
            "limit_plus_one": {
                "audit_exit": 2,
                "classification": "blocking-finding",
                "evidence_status": "ambiguous",
                "overflow_by_one": True,
                "transactional_zero_results": True,
            },
        }[name]
        if (
            any(claim[key] != value for key, value in expected.items())
            or claim["counter_policy"] != "every emitted work counter"
            or claim["measured_max_work"] != maximum
            or claim["max_work_counter_names"] != names
            or claim["measured_max_work"]
            != claim["limit"] + int(claim["overflow_by_one"])
            or claim["record_sha256"] != by_id[scenario]["record_sha256"]
        ):
            raise EvidenceError(f"{context} exact/+1 claim changed")
        require_digest(claim["record_sha256"], f"{context}.record_sha256")
    precharge = measured["precharge_P22"]
    require_keys(
        precharge,
        (
            "audit_exit", "classification", "counter_policy",
            "evidence_reason", "evidence_status", "limit",
            "posthoc_reference_metrics", "precharge_expected_metrics",
            "record_sha256", "transactional_zero_results",
        ),
        "measured_budget.precharge_P22",
    )
    require_keys(
        precharge["precharge_expected_metrics"],
        METRIC_KEYS,
        "measured_budget.precharge_P22.precharge_expected_metrics",
    )
    require_keys(
        precharge["posthoc_reference_metrics"],
        METRIC_KEYS,
        "measured_budget.precharge_P22.posthoc_reference_metrics",
    )
    precharge_row = by_id["R17-precharge-P22-budget"]
    if (
        precharge["audit_exit"] != 2
        or precharge["classification"] != "blocking-finding"
        or precharge["counter_policy"] != "charge before measured work"
        or precharge["evidence_reason"]
        != "measured work budget exceeded: object_reads=134>133"
        or precharge["evidence_status"] != "ambiguous"
        or precharge["limit"] != 133
        or precharge["precharge_expected_metrics"]
        != PRECHARGE_P22_METRICS
        or precharge["posthoc_reference_metrics"]
        != POSTHOC_P22_METRICS
        or precharge["transactional_zero_results"] is not True
        or precharge["record_sha256"] != precharge_row["record_sha256"]
    ):
        raise EvidenceError("pre-charge P22 budget claim changed")
    require_digest(
        precharge["record_sha256"],
        "measured_budget.precharge_P22.record_sha256",
    )
    wide = measured["wide_boundary"]
    require_keys(
        wide,
        (
            "audit_exit", "budget_contract", "classification",
            "evidence_status", "metrics", "outside_parent_count",
            "record_sha256", "reference_oids",
            "transactional_zero_results",
        ),
        "measured_budget.wide_boundary",
    )
    require_keys(
        wide["metrics"],
        (
            "graph_commits", "graph_lines", "graph_output_bytes",
            "graph_parent_edges", "graph_parent_tokens",
            "graph_process_cleanup_checks", "graph_process_reaps",
            "graph_process_terminations", "graph_stream_peak_chunk_bytes",
            "object_reads", "queue_snapshots_requested",
        ),
        "measured_budget.wide_boundary.metrics",
    )
    for key, value in wide["metrics"].items():
        require_nonnegative_int(
            value, f"measured_budget.wide_boundary.metrics.{key}"
        )
    wide_row = by_id["R17-wide-outside-C-boundary-budget"]
    if (
        wide["audit_exit"] != 2
        or wide["classification"] != "blocking-finding"
        or wide["evidence_status"] != "ambiguous"
        or wide["outside_parent_count"] != 64
        or wide["budget_contract"] != {
            "counter": "graph_parent_tokens",
            "limit": 7,
            "overflow_classification": "budget-exceeded",
            "raw_graph_bytes": 2952,
            "raw_graph_fields": [2, 2, 66, 2],
            "raw_graph_lines": 4,
            "transactional_zero_results": True,
        }
        or wide["metrics"] != {
            "graph_commits": 3,
            "graph_lines": 3,
            "graph_output_bytes": 2870,
            "graph_parent_edges": 2,
            "graph_parent_tokens": 8,
            "graph_process_cleanup_checks": 3,
            "graph_process_reaps": 1,
            "graph_process_terminations": 0,
            "graph_stream_peak_chunk_bytes": 256,
            "object_reads": 3,
            "queue_snapshots_requested": 0,
        }
        or wide["reference_oids"] != WIDE_BUDGET_REFERENCE_OIDS
        or wide["transactional_zero_results"] is not True
        or wide["record_sha256"] != wide_row["record_sha256"]
    ):
        raise EvidenceError("wide outside-C boundary budget claim changed")
    for label, oid in wide["reference_oids"].items():
        require_oid(oid, f"measured_budget.wide_boundary.reference_oids.{label}")
    require_digest(
        wide["record_sha256"], "measured_budget.wide_boundary.record_sha256"
    )
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
    raw_grammar_claim = core["raw_grammar"]
    require_keys(
        raw_grammar_claim,
        (
            "catalog_sha256", "enforcement", "record_kinds",
            "unknown_field_exit",
        ),
        "raw_grammar",
    )
    if raw_grammar_claim != {
        "catalog_sha256": digest_bytes(canonical_bytes(RAW_SHAPE_SHA256)),
        "enforcement": "recursive exact key/list/type shape before projection",
        "record_kinds": len(RAW_SHAPE_SHA256),
        "unknown_field_exit": 1,
    }:
        raise EvidenceError("raw stream grammar claim changed")
    require_digest(
        raw_grammar_claim["catalog_sha256"],
        "raw_grammar.catalog_sha256",
    )
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
    stable_git = core["stable_git_diagnostics"]
    require_keys(
        stable_git,
        (
            "ambient_reasons_differ", "forced_environment",
            "record_sha256", "stable_full_results_equal",
            "stable_reasons",
        ),
        "stable_git_diagnostics",
    )
    require_keys(
        stable_git["forced_environment"],
        ("LANG", "LANGUAGE", "LC_ALL", "TZ"),
        "stable_git_diagnostics.forced_environment",
    )
    require_keys(
        stable_git["stable_reasons"],
        ("C", "fr_FR.UTF-8"),
        "stable_git_diagnostics.stable_reasons",
    )
    locale_control = next(
        row
        for row in controls
        if row["id"] == "locale-git-error-stream-equality"
    )
    expected_stable_reason = stable_git["stable_reasons"]["C"]
    if (
        stable_git["ambient_reasons_differ"] is not True
        or stable_git["forced_environment"] != {
            "LANG": "C",
            "LANGUAGE": "C",
            "LC_ALL": "C",
            "TZ": "UTC",
        }
        or stable_git["stable_full_results_equal"] is not True
        or stable_git["stable_reasons"]["fr_FR.UTF-8"]
        != expected_stable_reason
        or not expected_stable_reason.startswith(
            "missing-or-malformed-commit:"
        )
        or stable_git["record_sha256"]
        != locale_control["record_sha256"]
    ):
        raise EvidenceError("stable Git diagnostic claim changed")
    require_digest(
        stable_git["record_sha256"],
        "stable_git_diagnostics.record_sha256",
    )
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
    bounds = core["execution_bounds"]
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
        "The raw JSONL stream is ephemeral and has no stored hash claim.",
        f"Evidence schemas v2 at commit `{core['evidence_supersession']['artifacts'][0]['commit']}`, v3 at commit `{core['evidence_supersession']['artifacts'][1]['commit']}`, and v4 at commit `{core['evidence_supersession']['artifacts'][2]['commit']}` are superseded and burned by their later blockers; all histories are preserved, no identifier is reused, and this artifact closes `{core['evidence_supersession']['replacement_schema']}`.",
        f"The execution-bound runtime landed in commits `{bounds['runtime_milestone_commits'][0]}` and `{bounds['runtime_milestone_commits'][1]}`; the latter binds literal refusal at the 68th parent token.", "",
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
        "All eight persisted-state attacker cases block in both parent orders: outside-C exact carriers retain multiplicity 1 or 2 as collisions, while valid and unauthorized absent C-descendant arms both remain deletion/reintroduction competitors.",
        f"The 64-parent outside-C octopus exits 2 transactionally and is record-bound by `{core['measured_budget']['wide_boundary']['record_sha256']}`; no action, edge, support, or carry-proof result leaks past the exceeded parent-token budget.",
        f"The P22 pre-charge case stops exactly at `object_reads=134>133`, keeps Git processes at {core['measured_budget']['precharge_P22']['precharge_expected_metrics']['git_processes']}, freezes later counters, and is record-bound by `{core['measured_budget']['precharge_P22']['record_sha256']}`; its post-hoc damage reproduces the prior 10,973-snapshot/24,736-cache-hit full run.",
        f"Seven runtime exact/+1 pairs bind streaming graph bytes/lines/tokens, object payloads, flattened trees, dynamic support traversal, and certificate serialization. Every +1 refusal exits 2 with zero partial results; graph reads peak at {bounds['streaming_graph_contract']['bounded_chunk_bytes']} bytes per chunk and publish nothing on refusal. P22 separately observes exactly {bounds['composition_observation']['production_parent_queries']} imported production parent queries and {bounds['composition_observation']['git_processes']} Git processes.",
        f"Unreadable Git objects use the stable typed reason `{core['stable_git_diagnostics']['stable_reasons']['C']}`. Every Git child is forced to C locale and UTC; the stable C/French results are equal even though the independent ambient diagnostic streams differ.",
        f"Before any projection or digest, all {core['raw_grammar']['record_kinds']} raw rows must match the static recursive key/list/type grammar catalog `{core['raw_grammar']['catalog_sha256']}`; an unknown top-level or nested field exits {core['raw_grammar']['unknown_field_exit']}.",
        "The parent-order pair has identical verdicts and the same role multiset:",
        f"`{core['parent_permutation']['r17_parent_permutation'][0]['merge_role_multiset']}`. The four persisted parent-order pairs are also byte-equal by semantic signature.", "",
        "Reviewer-supplied reference OIDs (bound as review input, not regenerated fixture IDs):", "",
        "| Role | OID |", "|---|---|",
    ]
    for label, oid in core["reviewer_dag"]["reference_oids"].items():
        lines.append(f"| `{label}` | `{oid}` |")
    lines += ["", "Boundary-attacker reference OIDs (bound review input):", "",
              "| Role | OID |", "|---|---|"]
    for label, oid in core["boundary_ancestry"]["reference_oids"].items():
        lines.append(f"| `{label}` | `{oid}` |")
    lines += ["", "Persisted outside-C collision reference OIDs (bound review input):", "",
              "| Role | OID |", "|---|---|"]
    for label, oid in core["persisted_carry"]["reference_oids"]["outside_single"].items():
        lines.append(f"| `{label}` | `{oid}` |")
    lines += ["", "Persisted absent-arm reference OIDs (bound review input):", "",
              "| Role | OID |", "|---|---|"]
    for label, oid in core["persisted_carry"]["reference_oids"]["valid_absent_arm"].items():
        lines.append(f"| `{label}` | `{oid}` |")
    lines += ["", "Wide-boundary budget reference OIDs (bound review input):", "",
              "| Role | OID |", "|---|---|"]
    for label, oid in core["measured_budget"]["wide_boundary"]["reference_oids"].items():
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
    exact_budget = core["measured_budget"]["exact"]
    overflow_budget = core["measured_budget"]["limit_plus_one"]
    precharge_budget = core["measured_budget"]["precharge_P22"]
    wide_budget = core["measured_budget"]["wide_boundary"]
    lines += ["", "## Measured cost and object recovery", "",
              f"P22 measured {m['graph_commits']} graph commits and 16 disappeared actions with exactly {m['graph_enumerations']} POC graph enumeration, {m['per_action_history_walks']} POC-owned per-action history walks, {m['queue_snapshots_requested']} snapshot requests, {m['snapshot_cache_hits']} snapshot-cache hits, and {m['git_processes']} actual Git processes.",
              "The process count includes imported production `git rev-list --parents -n 1` queries; zero applies only to POC-owned per-action walks. The POC's single budget consistently caps every emitted work counter.",
              f"PCX-20a passes at its exact measured maximum {exact_budget['measured_max_work']} with limit {exact_budget['limit']}; PCX-20b exits 2 with zero partial results when measured maximum {overflow_budget['measured_max_work']} exceeds limit {overflow_budget['limit']} by one.",
              f"R17-precharge-P22-budget charges before work and aborts on `{precharge_budget['evidence_reason']}` with exact bounded counters; the post-hoc reference vector is retained only as a damaged control.",
              f"The 64-parent boundary case stops at parent token {wide_budget['metrics']['graph_parent_tokens']} against limit {wide_budget['budget_contract']['limit']} after {wide_budget['metrics']['graph_output_bytes']} of {wide_budget['budget_contract']['raw_graph_bytes']} raw bytes; the graph child is reaped and no graph is published.",
              "The closed runtime matrix additionally admits/refuses exact/+1 values for total graph bytes, peak graph-line bytes, a 1,000,000-byte object, 1,004 flattened paths, 12 dynamic support paths, and 2,920 serialized certificate bytes.", "",
              f"PCX-19 is replay-bound by `{p19['record_sha256']}`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.", "",
              "## Reproducible audit", "",
              "Use two fresh, empty scratch roots:", "", "```sh",
              "PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-v5-seed1 > /tmp/production-contract-r17-v5-seed1.jsonl",
              "PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-v5-seed777 > /tmp/production-contract-r17-v5-seed777.jsonl",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-v5-seed1.jsonl --compare /tmp/production-contract-r17-v5-seed777.jsonl",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-v5-seed1.jsonl --damage-test",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --old FULL_OID_O --new FULL_OID_N",
              "python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py",
              "python3 automation/run_tests.py", "python3 automation/reconcile/reconcile.py --check", "```", "",
              "The auditor requires raw and semantic equality for comparison, rejects",
              "duplicate keys/IDs, enforces a static recursive raw key/list/type grammar",
              "before projection, compares a fresh",
              "manifest byte-for-byte, and regenerates this README in full. Its damage",
              "matrix covers invented/duplicate/missing rows, same-region OID swaps, tuple",
              "relabels, false verdicts/counters, contradictory transcripts/digests,",
              "unknown raw fields/cost rows, locale error drift, post-hoc or unmetered runtime work,",
              "noncanonical ordering, BOM, CRLF, and missing newline.", "",
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


def damage_matrix(expected, stream):
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
        "persisted-outside-false-clean",
        lambda d: d["core_claims"]["persisted_carry"]["cases"][
            next(
                index for index, row in enumerate(
                    d["core_claims"]["persisted_carry"]["cases"]
                )
                if row["id"] == "R17-persisted-outside-single"
            )
        ].update(classification="no-finding"),
        "semantic claim changed",
    )
    manifest_case(
        "persisted-outside-collapse-multiplicity",
        lambda d: d["core_claims"]["persisted_carry"]["cases"][
            next(
                index for index, row in enumerate(
                    d["core_claims"]["persisted_carry"]["cases"]
                )
                if row["id"] == "R17-persisted-outside-duplicate"
            )
        ].update(collision_multiplicities=[1]),
        "semantic claim changed",
    )
    manifest_case(
        "persisted-absent-arm-false-clean",
        lambda d: d["core_claims"]["persisted_carry"]["cases"][
            next(
                index for index, row in enumerate(
                    d["core_claims"]["persisted_carry"]["cases"]
                )
                if row["id"] == "R17-persisted-valid-absent-arm"
            )
        ].update(classification="no-finding"),
        "semantic claim changed",
    )
    manifest_case(
        "persisted-absent-arm-reason-erased",
        lambda d: d["core_claims"]["persisted_carry"]["cases"][
            next(
                index for index, row in enumerate(
                    d["core_claims"]["persisted_carry"]["cases"]
                )
                if row["id"]
                == "R17-persisted-unauthorized-absent-arm"
            )
        ].update(reason_codes=[]),
        "semantic claim changed",
    )
    manifest_case(
        "persisted-parent-permutation-first-parent",
        lambda d: d["core_claims"]["parent_permutation"][
            "r17_persisted_parent_permutations"
        ]["outside-single"][1].update(
            outside_collision_multiplicities=[]
        ),
        "persisted permutation differs",
    )
    manifest_case(
        "wide-budget-false-clean",
        lambda d: d["core_claims"]["measured_budget"][
            "wide_boundary"
        ].update(classification="no-finding"),
        "wide outside-C boundary budget claim changed",
    )
    manifest_case(
        "wide-budget-unmetered-parent-edges",
        lambda d: d["core_claims"]["measured_budget"][
            "wide_boundary"
        ]["metrics"].update(graph_parent_edges=7),
        "wide outside-C boundary budget claim changed",
    )
    manifest_case(
        "exact-budget-only-graph-commits",
        lambda d: d["core_claims"]["measured_budget"]["exact"].update(
            counter_policy="graph_commits only"
        ),
        "exact/+1 claim changed",
    )
    manifest_case(
        "budget-plus-one-leaks-partial-result",
        lambda d: d["core_claims"]["measured_budget"][
            "limit_plus_one"
        ].update(transactional_zero_results=False),
        "exact/+1 claim changed",
    )
    manifest_case(
        "precharge-P22-restored-posthoc",
        lambda d: d["core_claims"]["measured_budget"][
            "precharge_P22"
        ].update(counter_policy="post hoc measured work"),
        "pre-charge P22 budget claim changed",
    )
    manifest_case(
        "precharge-P22-later-work-leaks",
        lambda d: d["core_claims"]["measured_budget"][
            "precharge_P22"
        ]["precharge_expected_metrics"].update(
            snapshot_cache_hits=56
        ),
        "pre-charge P22 budget claim changed",
    )
    for label, _counter, _value, _exact_id, _overflow_id in (
        EXECUTION_BOUND_CASES
    ):
        manifest_case(
            f"execution-bound-{label}-leaks-partial-result",
            lambda d, label=label: d["core_claims"]["execution_bounds"][
                "pairs"
            ][label]["limit_plus_one"].update(
                transactional_zero_results=False
            ),
            "exact/+1 contract changed",
        )
    manifest_case(
        "execution-bound-stream-chunk-expanded",
        lambda d: d["core_claims"]["execution_bounds"][
            "streaming_graph_contract"
        ].update(bounded_chunk_bytes=257),
        "streaming graph contract changed",
    )
    manifest_case(
        "execution-bound-composition-query-erased",
        lambda d: d["core_claims"]["execution_bounds"][
            "composition_observation"
        ].update(production_parent_queries=128),
        "P22 production-helper composition changed",
    )
    manifest_case(
        "execution-bound-runtime-milestone-erased",
        lambda d: d["core_claims"]["execution_bounds"][
            "runtime_milestone_commits"
        ].__setitem__(1, "0" * 40),
        "execution-bound runtime commits changed",
    )
    manifest_case(
        "superseded-v2-reused",
        lambda d: d["core_claims"]["evidence_supersession"].update(
            replacement_schema="agentfold-production-contract-evidence/v2"
        ),
        "evidence schema supersession changed",
    )
    manifest_case(
        "superseded-v2-commit-erased",
        lambda d: d["core_claims"]["evidence_supersession"][
            "artifacts"
        ][0].update(commit="0" * 40),
        "evidence schema supersession changed",
    )
    manifest_case(
        "superseded-v3-commit-erased",
        lambda d: d["core_claims"]["evidence_supersession"][
            "artifacts"
        ][1].update(commit="0" * 40),
        "evidence schema supersession changed",
    )
    manifest_case(
        "superseded-v4-commit-erased",
        lambda d: d["core_claims"]["evidence_supersession"][
            "artifacts"
        ][2].update(commit="0" * 40),
        "evidence schema supersession changed",
    )
    manifest_case(
        "locale-stable-error-drift",
        lambda d: d["core_claims"]["stable_git_diagnostics"][
            "stable_reasons"
        ].update(**{"fr_FR.UTF-8": "localized raw Git stderr"}),
        "stable Git diagnostic claim changed",
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
        "carry-parent pair differs",
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
    raw_lines = stream.raw.splitlines()
    unknown = load_json(raw_lines[0])
    unknown["unknown_machine_claim"] = True
    unknown_raw = canonical_bytes(unknown) + b"\n".join(raw_lines[1:]) + b"\n"
    observed_failure = None
    observed_exit = 0
    try:
        Stream.from_bytes(unknown_raw, "<raw-unknown-field-damage>")
    except EvidenceError as error:
        observed_failure = str(error)
        observed_exit = 1
    matched = (
        observed_exit == 1
        and observed_failure is not None
        and "grammar differs" in observed_failure
    )
    results.append(
        {
            "damage": "raw-unknown-machine-claim",
            "expected_exit": 1,
            "expected_failure": "grammar differs",
            "observed_exit": observed_exit,
            "observed_failure": observed_failure,
            "status": "OBSERVED_RED" if matched else "FALSE_GREEN",
        }
    )
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
            damaged = damage_matrix(expected, first)
            print(json.dumps(damaged, sort_keys=True))
            if damaged["audit_damage"] != "PASS":
                failures.append("audit damage matrix false-greened")
        return int(bool(failures))
    except (EvidenceError, OSError, KeyError, TypeError, IndexError) as error:
        print(json.dumps({"audit": "FAIL", "failures": [str(error)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
