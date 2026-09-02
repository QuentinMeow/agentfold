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


SCHEMA = "agentfold-production-contract-evidence/v6"
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
        {
            "commit": "d12b799a2fa27b05a5ee2af1b422131856296b41",
            "disposition": (
                "superseded and burned after the absent-at-C normal-restack "
                "false block; history is preserved and v5 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v5",
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
    "carry_proof_edges", "origin_arm_nodes", "origin_parent_edges",
    "origin_births", "origin_witness_bytes", "production_helper_calls",
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
    (
        "origin_arm_nodes", "origin_arm_nodes", 5,
        "R18-origin-arm-nodes-exact",
        "R18-origin-arm-nodes-plus-one-refused",
    ),
    (
        "origin_parent_edges", "origin_parent_edges", 3,
        "R18-origin-parent-edges-exact",
        "R18-origin-parent-edges-plus-one-refused",
    ),
    (
        "origin_witness_bytes", "origin_witness_bytes", 1042,
        "R18-origin-witness-bytes-exact",
        "R18-origin-witness-bytes-plus-one-refused",
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
    "origin_arm_nodes": 0,
    "origin_births": 0,
    "origin_parent_edges": 0,
    "origin_witness_bytes": 0,
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
    "origin_arm_nodes": 0,
    "origin_births": 0,
    "origin_parent_edges": 0,
    "origin_witness_bytes": 0,
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
    "R18-B-exact-cherry-pick",
    "R18-B-agent-born-claimed",
    "R18-B-generated-retry",
    "R18-B-human-born-answered",
    "R18-B-independent-birth",
    "R18-B-normal-base-advance-replay",
    "R18-B-rename-timing-move",
    "R18-B-review-publication-equivalence",
    "R18-B-task-pickup",
    "R18-U-O-only-post-C-loss",
    "R18-U-agent-born-claimed",
    "R18-U-claim-restoration",
    "R18-U-delete-recreate-N",
    "R18-U-delete-recreate-O",
    "R18-U-endpoint-regression",
    "R18-U-exact-cherry-pick",
    "R18-U-generated-retry",
    "R18-U-human-response-restoration",
    "R18-U-human-born-answered",
    "R18-U-independent-birth",
    "R18-U-inherited-then-deleted-merge-arm",
    "R18-U-multiplicity",
    "R18-U-neutral-pre-origin-merge",
    "R18-U-normal-base-advance-replay",
    "R18-U-outside-collision",
    "R18-U-parent-order",
    "R18-U-parent-order-reversed",
    "R18-U-rename-timing-move",
    "R18-U-review-binding-restoration",
    "R18-U-review-publication-equivalence",
    "R18-U-schema-invalid-birth",
    "R18-U-second-birth",
    "R18-U-transient-protected-mutation",
    "R18-U-task-pickup",
    "R18-U-unreadable-object",
    "R18-origin-arm-nodes-exact",
    "R18-origin-arm-nodes-plus-one-refused",
    "R18-origin-parent-edges-exact",
    "R18-origin-parent-edges-plus-one-refused",
    "R18-origin-witness-bytes-exact",
    "R18-origin-witness-bytes-plus-one-refused",
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
    "endpoint-only-origin-equality",
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
    "skip-origin-birth-uniqueness",
    "skip-origin-endpoint-non-regression",
    "skip-origin-post-birth-absence",
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


# Generated from both byte-identical corrected v6 streams after runtime commits
# c32f470977735a63feaf377ca9290353d1520e0e and
# 850d02587f7f812b7dde9667a39da80b4ce48764. Every row kind has one exact
# recursive shape digest, checked before any projection.
RAW_SHAPE_CATALOG_V6 = """
scenario:P1-direct-linear-valid sha256:356e5e2f5b906e2609dce7643c46eb3802ab376b1994aaac48c90cdacd35b660
scenario:P10-direct-invalid-parent sha256:243adfd610241a33198cd863fe6b3bf8838e0f1249417cd02d785958e9b00db2
scenario:P11-direct-three-parent-valid sha256:08cbb263eae6a1b25dd5c0a43993f762cf5e5e609e224e060e033aff4c7a6d8e
scenario:P12-merge-supplier-valid sha256:62a0422e4abc3f2f30a8c92e80403730975d2a9a857ad68d5be835320416f79d
scenario:P13-merge-supplier-invalid sha256:ff94228192a8d68de73542c2a091d31cb14c3a8486395c321345cc43ecb8d59d
scenario:P14-supplier-reintroduced sha256:7454ea144eeb97e42fdec49a5c871b156e4eab36cf458fc9e323bc21d75d038d
scenario:P15-competing-suppliers sha256:bfc196880866b433782f091ea315a59ff4da15a378395e84f9031019a03bae6b
scenario:P16-PCX-08-invalid-supplier-claimed-carrier sha256:5e3b453421a76eb12e98e49e70e9676b7f3161982bd3ac2bfbbbfdd4c4f2266e
scenario:P17-post-event-reintroduction sha256:1bf728538f3f9b2f8039ea328a14e9ac854f611096c8e6d7215f593ac9c94bd0
scenario:P18a-missing-tip sha256:da6495cae1725367fa0e7f6396a28bec7aeaa81e0184c4e548af68cd513935a7
scenario:P18b-noncommit-tip sha256:da6495cae1725367fa0e7f6396a28bec7aeaa81e0184c4e548af68cd513935a7
scenario:P18c-unrelated-tip sha256:da6495cae1725367fa0e7f6396a28bec7aeaa81e0184c4e548af68cd513935a7
scenario:P18d-shallow-required-region sha256:da6495cae1725367fa0e7f6396a28bec7aeaa81e0184c4e548af68cd513935a7
scenario:P18e-missing-queue-blob sha256:7edae0c78d59593a52d89129162656692360731d908fdd3729fe88cf611fcada
scenario:P18f-missing-queue-tree sha256:b1d54297d776a89060609e1bc66d4692ca003f5b80e55e59c155a4062224eb1f
scenario:P18g-multiple-merge-bases sha256:c32fba6de342591595d0c401021cf433fd1c2cef2676c72ce200ce1b944bd09f
scenario:P19-production-identities sha256:033f90ccb071f6497a6844de276b6ae6e2559959e0611bc935b941041a29f69c
scenario:P2-direct-linear-invalid sha256:56e05ec0a91851229bdfc89505fb07b455c5db59bcc096a2afed3da4504329d9
scenario:P20-lifecycle-types sha256:15226253f334121e1f257d75526897dcc78067b59fee96e184b54b47b1532b1f
scenario:P21-PCX-17c-squash-erasure sha256:5993dcb6ca9c35cd6e45648b28820218e122476427ce873ae12fbb1b77a8109e
scenario:P22-PCX-18-one-pass-many-actions sha256:90b3c3fc63a63438171db8ec1a7f2ae6a0f8b0fa2111cb7e69b9cad4599a8862
scenario:P3-genuine-old-loss sha256:f4d7aa0fea3c8209656e6637fdfd573a6306a24b8674d952e46ca4e54733326c
scenario:P4-pre-C-identical-origins sha256:e9f07454f5aa06ca57513a645d35048804ae714fd3d44fdae2448abded89abd2
scenario:P5-duplicate-at-C sha256:b22089ba1ce2aa3f1c8cc2a33210522606ebb175bede2b00ee7a1ea031b1ded2
scenario:P6a-old-delete-recreate sha256:60b5df621433e1b12b73476ce4ae391f3d9e9ec85f2b63d673ee4bd6870082f9
scenario:P6b-candidate-delete-recreate sha256:6719d297697ea5c79dd16730a64abb4abf4908dcd4ff7d1f462cb438489db612
scenario:P7-immutable-payload-change sha256:8d12cccc2e70200a62a42c5f14b315083dee5be4a74ccb687bf143ea926b679d
scenario:P8-path-timing-move sha256:399f1049ee64053a8132821b61ca823265ee98aa8a605902c789ff923a65791a
scenario:P9-direct-two-parent-valid sha256:0c16c29d76f9d816cdd9bc9d67e19b4219eaea44022ca7240c7fdd836f22d9bc
scenario:PCX-01-neutral-parent sha256:d736acff2c56506f54240b5a594a50463d328ba29c8278d14548af1f4c7ee72a
scenario:PCX-02-neutral-plus-invalid-carrier sha256:ecadc87ad361a6bbb5db07b28ae0e61a9eb37d2cb736090d6f064c338f26ec3a
scenario:PCX-03-foreign-exact-identity sha256:3488004ff1af764e8b0a2edbba4be9ccefdbdb5a58e7a37776ac62a656e58390
scenario:PCX-04-several-absent-one-supplier sha256:c96957004dcd2f030928e4070e46969bb99cf42e0e1444f82a95b675ddf41025
scenario:PCX-05-competing-later-supplier sha256:28e09a02e1755faa58d92b0cd78b4fdcd3209f2da0cc32c68f3ba7ddba9b6b34
scenario:PCX-06-nested-supplier-over-direct sha256:8ab1d9303f703dcdf363a1b145b592f641f2f23a64f0cb6f62da71bc34f59001
scenario:PCX-07-overqualified-propagation sha256:b3ee1c7480548139bab197b7bed05bd75ac670dae35a28ec505bd1f040cc6675
scenario:PCX-09-recreated-claimed-bytes sha256:83748512668326da86521cab5557fdf322a7eb3803554023eb537ef922e3cb9c
scenario:PCX-10-transient-multiplicity sha256:524af5360b1d42f51d4c25d3146547fae4262b08c40d0f37b543bbe19f8eef09
scenario:PCX-11-different-payload-same-path sha256:749f3f19e37bcc4010fdf1bf107b56be80ca4f559aeb14ec94884d02d88fff21
scenario:PCX-12-timing-rename-supplier sha256:a4625e978c779f7042615f0d26b07f59fa3014a05a13c1a442f1e5e5f7d2f195
scenario:PCX-13-conflicting-human-response sha256:35897b16a6c5e8ef91c1bf907b3c8970f28c71337080b03e1ad50f8a7bc14616
scenario:PCX-14-valid-human-supplier sha256:2429b312c3b3243ef1a2d803a2b5a3d6e623c81e34268da37fd8bd6774feb425
scenario:PCX-15-generated-retry-supplier sha256:c1f2b106dc21fb76201c699f8cc1f12e0ee25f5a3c0f782659683a223036c5bf
scenario:PCX-16-task-pickup-supplier sha256:6182683fe92618dcecb781ec8ead254fb40017172d213acc855af473b3ffef47
scenario:PCX-17-complete-cherry-pick sha256:2e1d93695d3d4ffa7756a1fdea89e83f761c2b58c8f10f3b255b5bb6dccd839d
scenario:PCX-17-deletion-only-cherry-pick sha256:5993dcb6ca9c35cd6e45648b28820218e122476427ce873ae12fbb1b77a8109e
scenario:PCX-19-missing-claim-blob-recovery sha256:d317b3dcc295468280621715e7cacad36a99b0036d1eb528d9e27c12311ed300
scenario:PCX-20a-budget-below-limit sha256:8ecbbc1472471962bfd53a642d1d26291fdc770f413a00886dff2043e76d7cc7
scenario:PCX-20b-budget-overflow sha256:e3aa1682a02c1ca646f8c83337b6cc79eabdae7a2a3c77d993bc9e6f2da6ee1a
scenario:R10-direct-review-target-backtick-dotless-rejected sha256:d8be11e83431dfc36866311e3890655b9a5d9d7efdd67d809c6d09ae3630ff85
scenario:R10-supplier-review-revision-generic-placeholder-rejected sha256:ecb56e3e83ae60f96c0a210c694a4cb69bc2d252b15bb177a58838d55581a4de
scenario:R13-direct-review-binding-identical sha256:b5cab6e10850f3413195e2eef9dce3738a7f20fa93bc98ef250790a87d71b6b3
scenario:R13-direct-review-binding-revision sha256:736bb81c9833b99212d07e9ddbcdd31e47f0df00991b508f14cbd4d7dc1bbe64
scenario:R13-direct-review-binding-target sha256:820e749b156129f0be4a131f4e6281af0925596c8d9ff2a7f614aa534cc300b7
scenario:R13-direct-review-binding-terminal sha256:7cd0bda0b5ad360ab8a1a7fc5c8ce0eeed5d8004c5e33838301dce745e6ef1ea
scenario:R13-persisted-claim-loss sha256:f896875860ccce06186035a8b00a569c0b950825bb68ab0e6998535fbb5084f5
scenario:R13-persisted-pending-fill sha256:5989193bdae5a33b1204ac55234c178ab309951b8ddb4694e74fcab207a42335
scenario:R13-persisted-response-change sha256:80e4893742dc769ab7e2a52144981420689073904b0d387e5e89483ae854af73
scenario:R13-persisted-response-removal sha256:cf177839f3205bc41739a5db21b6fb74e9a98282f00d91313e59e8126463cf50
scenario:R13-persisted-review-outcome-change sha256:66d8e36f4944282e0ae94d460cfae38e8807464e363a4bab8a062e457bc257e5
scenario:R13-persisted-review-revision-change sha256:66d8e36f4944282e0ae94d460cfae38e8807464e363a4bab8a062e457bc257e5
scenario:R13-persisted-review-target-change sha256:66d8e36f4944282e0ae94d460cfae38e8807464e363a4bab8a062e457bc257e5
scenario:R13-persisted-same-state sha256:4bf3284ce339183796fbed1f9b1b6ed7f369d2184196c66b00407e1abda8f113
scenario:R13-persisted-terminal-fill sha256:b52150e8d4329770952bbfe8557a4a9d581181e140d6656f519f3dfa1c8ed3aa
scenario:R13-supplier-review-binding-identical sha256:9c508b087b3556a4592aa81c0777a5de377c950d7253dfc494f67e3cd2045560
scenario:R13-supplier-review-binding-revision sha256:f5e8cbc9e1e58d774a899b45689c45a2702537b548652ee30c81c77eecb7e7f9
scenario:R13-supplier-review-binding-target sha256:f5e8cbc9e1e58d774a899b45689c45a2702537b548652ee30c81c77eecb7e7f9
scenario:R13-supplier-review-binding-terminal sha256:da0cabf1112daa9863d2b8626a93d1965944aed0a46f455fb0ea59b5050b72c3
scenario:R14-direct-old-unanswered-carrier-same sha256:84a12bb2a756db2024e15c6d7d3b862cf270878cc57adec4b7c3b619bb198c2a
scenario:R14-direct-old-unanswered-carrier-target sha256:84a12bb2a756db2024e15c6d7d3b862cf270878cc57adec4b7c3b619bb198c2a
scenario:R14-persisted-delete-recreate sha256:e339e21594b24b4faf15ed7579c661125a1b1845c637ecf51a89ffb3364ba203
scenario:R14-persisted-hidden-bytes-low-similarity sha256:3702263506c6ce6b247d003a927951423761805d2bcf77fc00b5041b2c0b00f4
scenario:R14-persisted-intermediate-claim-regression sha256:2e8cb2d7f3976814f53a2ffd84a5d97b719f003573bfb1b75b2cff83f6885a30
scenario:R14-persisted-intermediate-review-regression sha256:cacd3fae26aeba3d22a53fac9a16834a27add144edac278b67253943fb0206c4
scenario:R14-persisted-merge-carrier-conflict sha256:3e67eaa0201ad35b25f31bf2f16919533c4f0077ba4df0304960ad357fe4792b
scenario:R14-persisted-merge-carrier-pending sha256:9490dda4ca97b62534d890175fe7ba368fccaad791ddfba54a294f363ef3e535
scenario:R14-persisted-valid-first-response-low-similarity sha256:0f5eacfe4037ec067e90ef38552884008c55df64c3ce17c33947973b861b0ca5
scenario:R14-persisted-valid-review-retraction sha256:3a0d22644fbd0da30337acf2f9eeb4cb5d5f1af12ac524b057342c5ccf572493
scenario:R14-supplier-old-answered-carrier-pending sha256:69bdc800cd638c02a41d490e06aad60e8d02ffedb7d82499db815c8dc5f60f44
scenario:R14-supplier-old-answered-carrier-revision sha256:69bdc800cd638c02a41d490e06aad60e8d02ffedb7d82499db815c8dc5f60f44
scenario:R14-supplier-old-answered-carrier-same sha256:69bdc800cd638c02a41d490e06aad60e8d02ffedb7d82499db815c8dc5f60f44
scenario:R14-supplier-old-answered-carrier-target sha256:69bdc800cd638c02a41d490e06aad60e8d02ffedb7d82499db815c8dc5f60f44
scenario:R14-supplier-old-unanswered-carrier-same sha256:134fa675fe7f107b764577e90701cb24c30d979c6cb47ef3cc2df69427e833aa
scenario:R14-supplier-old-unanswered-carrier-target sha256:134fa675fe7f107b764577e90701cb24c30d979c6cb47ef3cc2df69427e833aa
scenario:R15-old-continuous-preserved sha256:d3397f00b9037680c51ef01c72d11b507c2f46f2c1a55cf9ba704919f7501529
scenario:R15-old-hidden-bytes-restore sha256:11113e0859bcbfce1b8f81b6fd751fc63c04f3d39cfb485af61d50d213f0e22e
scenario:R15-old-human-binding-restore sha256:80d4ea528981647d205a199317b03ef85f7b4b3ac04cb12945d01794634be919
scenario:R15-old-invalid-delete-recreate sha256:582d6e28a4e2d0263ec68023449075ff1a618272385101deff81f0daf3897eae
scenario:R15-old-valid-delete-recreate sha256:bc8a6cf13657304237b1f30c889a84d4e00bc9c6ea9a19e9b920e32e971f778b
scenario:R16-earlier-landed-evidence-reversal sha256:fd7d4e334bc3cf6957bc6ccaaa73f0bb7b70bd546974479fe61128a2adf12521
scenario:R16-pickup-evolution-0-backlog sha256:d55968e52c3b0e88e0a603e4393f7d7d77b131f5a1e20b6101668f859f5548dd
scenario:R16-pickup-evolution-2-blocked sha256:b8e2af65bfee4e7d41e297698fd99041a01751e9ddcc43d157fc3f8e5089f5bb
scenario:R16-pickup-evolution-3-in-review sha256:599eb8d9c50528def23b934622207299a0b49748891a57c17252a242061c35fb
scenario:R16-pickup-evolution-3-in-review-drop-artifact sha256:c3577bc62d959f83cb035f10343323fa2902268adb298aa0363a309223f2ae31
scenario:R16-pickup-evolution-4-done sha256:599eb8d9c50528def23b934622207299a0b49748891a57c17252a242061c35fb
scenario:R16-support-adoption-drift sha256:5d945b0adeb0454895bdf174e6131e06083882cf503385d03386fa4e32b52482
scenario:R16-support-forward sha256:9beac548b3e3e143501b112801d4dd43352f50fe3f3948f6a9fcf98e7805b761
scenario:R16-support-invalid-source sha256:1de3f5e5813cba37191d136d4ff91a52a0fa0f6ec977fa3e3d81b6a739867e09
scenario:R16-support-nested-drop sha256:3d1c63c6acfeed8a799f80891488a3e91b423e6d1c3e2dfac14a4ca2c6608616
scenario:R16-support-permutation-diamond sha256:0fef45e9b55e1e016e3746caa19f81702a952aaaccdb8ba35d8b3e94c0b49d69
scenario:R16-support-reverse-drop sha256:70ed37b05252a515f3d895ed3a31cccf5b767477dfae0f0dfd2953b62072917c
scenario:R16-support-reverse-preserved sha256:9beac548b3e3e143501b112801d4dd43352f50fe3f3948f6a9fcf98e7805b761
scenario:R16-support-source-evolution sha256:9beac548b3e3e143501b112801d4dd43352f50fe3f3948f6a9fcf98e7805b761
scenario:R17-carry-absent-arm sha256:cb68aa216619389cc10a93a8e6177823a89df16cbe34f2e31a982ad8f371d8ee
scenario:R17-carry-compatible sha256:1455b8d4c4466b49cc2cefd7db4ab220c0fea2644dba8d09c3abd70966ba7a95
scenario:R17-carry-compatible-reversed sha256:1455b8d4c4466b49cc2cefd7db4ab220c0fea2644dba8d09c3abd70966ba7a95
scenario:R17-carry-incompatible sha256:1919a765d1ce09ccfacd7b810a12c657a4ef8cd260c2ac8041583817626be056
scenario:R17-carry-outside-duplicate sha256:3e52733c565eb82c5d6397a90dea0ee683b1402e0257d63438fff256e8c4e2fd
scenario:R17-carry-outside-single sha256:60074052b84e6ccf791d9168decb4ef37b761ceda6ccab9e4691dc247a0f1076
scenario:R17-dynamic-support-traversal-exact sha256:ef4619f11c28320e082e13e8ef683abcaa1421f5926b53ef0f0e9c1a7fbc580b
scenario:R17-dynamic-support-traversal-plus-one-refused sha256:f441ced389c87e5dcb3b98be678d9081ff6c1a6ede2db4bacae1e52d7c3af746
scenario:R17-flat-tree-peak-exact sha256:246f10366de76fec0c82571b605173c52dfb7dcb35aa7cdd5697786c25bd6853
scenario:R17-flat-tree-peak-plus-one-refused sha256:4ca1afcf841f08c30563a04668a2ad7dd9ef65c2e706b4cea487adedeca47955
scenario:R17-graph-line-peak-bytes-exact sha256:d7716f71b0e5aae92cfe3e824bd86f8a8bacaf1bb27fe3ad91dbd46b0d15a300
scenario:R17-graph-line-peak-bytes-plus-one-refused sha256:76bfa429aee08d4b9c3d9e940d601a2c4114d5199c676e2d25b685195fbabf6d
scenario:R17-graph-output-bytes-exact sha256:d7716f71b0e5aae92cfe3e824bd86f8a8bacaf1bb27fe3ad91dbd46b0d15a300
scenario:R17-graph-output-bytes-plus-one-refused sha256:76bfa429aee08d4b9c3d9e940d601a2c4114d5199c676e2d25b685195fbabf6d
scenario:R17-graph-parent-tokens-exact sha256:d7716f71b0e5aae92cfe3e824bd86f8a8bacaf1bb27fe3ad91dbd46b0d15a300
scenario:R17-graph-parent-tokens-plus-one-refused sha256:76bfa429aee08d4b9c3d9e940d601a2c4114d5199c676e2d25b685195fbabf6d
scenario:R17-object-payload-peak-exact sha256:d0ee37c4dac44680ff4d440e6ed3dcbcfad6b980ac89235d8613b83d8ff8d6bb
scenario:R17-object-payload-peak-plus-one-refused sha256:6924687d230997ddceef1f585e682d08718b2aebce819fae598b490cf88bd8f3
scenario:R17-outside-C-neutral-parent-valid-restack sha256:72fbc022fb34f2b12f49b8e88800fbacdd4707164cb78bae517f9bfc4bf8dd0d
scenario:R17-persisted-outside-duplicate sha256:073ce80fa4c48086cff9343a917237b1abbc971e2eb02e90db2355392ba26636
scenario:R17-persisted-outside-duplicate-reversed sha256:073ce80fa4c48086cff9343a917237b1abbc971e2eb02e90db2355392ba26636
scenario:R17-persisted-outside-single sha256:f46d8e9c071fe75934e54886c21437dd261cb0f499e5f2fbd03f0cef9783078b
scenario:R17-persisted-outside-single-reversed sha256:f46d8e9c071fe75934e54886c21437dd261cb0f499e5f2fbd03f0cef9783078b
scenario:R17-persisted-unauthorized-absent-arm sha256:7fb46f08805fc14e39185bacf835d5a1f39b8dac4ec7f117f8f2d32ba1044e98
scenario:R17-persisted-unauthorized-absent-arm-reversed sha256:7fb46f08805fc14e39185bacf835d5a1f39b8dac4ec7f117f8f2d32ba1044e98
scenario:R17-persisted-valid-absent-arm sha256:42f29b9e931e2e3fd97be6366a1b2de95a330e87140a2ab8cc06e59a80a92575
scenario:R17-persisted-valid-absent-arm-reversed sha256:42f29b9e931e2e3fd97be6366a1b2de95a330e87140a2ab8cc06e59a80a92575
scenario:R17-precharge-P22-budget sha256:af867027af07d4d30502af5bd89064e13cc600c58fd57df6dde5a6c11df5bfaf
scenario:R17-support-serialized-exact sha256:7f80e4bd5e84d20c3e1846dd52c82551659a4201c37f118c64c4ed2db06a29e9
scenario:R17-support-serialized-plus-one-refused sha256:89d80ccc3f2e78f623401d3082eefa6652025a583078c11035fce1a0aab21349
scenario:R17-unreadable-outside-C-ancestor-stays-unopened sha256:e9ed187cc5a55d6bbd0875aa4b9ce7ec045ad5e1b74bb944370d8412a0ad3ba3
scenario:R17-unreadable-outside-C-boundary sha256:7cbe67ddaa1daadcb6e73ccaa1a4112b47b1777ea78f36fe9ee8d5bdf1a50f2d
scenario:R17-wide-outside-C-boundary-budget sha256:72e514c5037ca9568a28cb598a830f21108a4d0808272547f49fa30dc0ca17ea
scenario:R18-B-exact-cherry-pick sha256:7b268fd9caafbc07e49588422fcbb5f8cee83ba7dcafdbaf2f102a7dc5052be8
scenario:R18-B-agent-born-claimed sha256:b9de2a3e33fdedf3ea442576859b3a0e7784e5257932cc431610ff6cd134de82
scenario:R18-B-generated-retry sha256:70666ee5201a0b426320c3cd558fd58cc3bf2088a8d5bbdf5ef2a723182b8a3f
scenario:R18-B-human-born-answered sha256:39a1f9769daafe958f211e6da9f0d8116fe21a2f88962cfa6b7265f02b813b3f
scenario:R18-B-independent-birth sha256:7b268fd9caafbc07e49588422fcbb5f8cee83ba7dcafdbaf2f102a7dc5052be8
scenario:R18-B-normal-base-advance-replay sha256:7b268fd9caafbc07e49588422fcbb5f8cee83ba7dcafdbaf2f102a7dc5052be8
scenario:R18-B-rename-timing-move sha256:93225d0766eeb06577b676234c702278f400f6f7268d082494a23007181145f5
scenario:R18-B-review-publication-equivalence sha256:7aaad893c08f170dd9d55cad5c947acb67bd580e2d8a4c5ae972e12473964521
scenario:R18-B-task-pickup sha256:c5ea471772034b67f0e0c0dd5ad8ac6dd5ba75a8d12c9498acabb017669683b0
scenario:R18-U-O-only-post-C-loss sha256:857c3f32e8a2aa13f8093d002551117df32a84b59292f44b4b2d9ed59d7bac85
scenario:R18-U-agent-born-claimed sha256:b9de2a3e33fdedf3ea442576859b3a0e7784e5257932cc431610ff6cd134de82
scenario:R18-U-claim-restoration sha256:56fafce867c7fb0d4ca5d465ba8751a97a3b11fc1dbee36c761ba3c6784087f2
scenario:R18-U-delete-recreate-N sha256:cb5bdd57b38679f60cf68476109afc7bab8306c612dde2c2ad3b8c094e9d3899
scenario:R18-U-delete-recreate-O sha256:b019324b6ce9d0b8918260ce93bdce8ed108260feb0e213d5b565784d39c15bd
scenario:R18-U-endpoint-regression sha256:3b863bb38425d4471f8aae4a25cef3ec21980bc3e0de4dc4232fa9b43c83a646
scenario:R18-U-exact-cherry-pick sha256:7b268fd9caafbc07e49588422fcbb5f8cee83ba7dcafdbaf2f102a7dc5052be8
scenario:R18-U-generated-retry sha256:70666ee5201a0b426320c3cd558fd58cc3bf2088a8d5bbdf5ef2a723182b8a3f
scenario:R18-U-human-born-answered sha256:39a1f9769daafe958f211e6da9f0d8116fe21a2f88962cfa6b7265f02b813b3f
scenario:R18-U-human-response-restoration sha256:a0e8ca13dd6ca8864c046f29efb6466aa7d87f81af2a799b4c150fb7703f9056
scenario:R18-U-independent-birth sha256:7b268fd9caafbc07e49588422fcbb5f8cee83ba7dcafdbaf2f102a7dc5052be8
scenario:R18-U-inherited-then-deleted-merge-arm sha256:c7cbd4b92b36410a81045e284cc306179dbf1e7b1c3f7311d099bac715eb6744
scenario:R18-U-multiplicity sha256:b1b95a8b94c7d8e2e2ded3586277fd225997312de4660f3437c4efc59ad012f1
scenario:R18-U-neutral-pre-origin-merge sha256:519b895d5d4d03f153b0650f6362c5f8a0dd7329ecf8b6798c87eebc13016d92
scenario:R18-U-normal-base-advance-replay sha256:7b268fd9caafbc07e49588422fcbb5f8cee83ba7dcafdbaf2f102a7dc5052be8
scenario:R18-U-outside-collision sha256:bb180f3ff58253b57dd6776d634133d10c1fb669b2d850cb145e8b684d0bf7eb
scenario:R18-U-parent-order sha256:9094e5c9990b922d9231796fa45e2944a5b455f71eca17ddafb32ce92d93ad6d
scenario:R18-U-parent-order-reversed sha256:9094e5c9990b922d9231796fa45e2944a5b455f71eca17ddafb32ce92d93ad6d
scenario:R18-U-rename-timing-move sha256:93225d0766eeb06577b676234c702278f400f6f7268d082494a23007181145f5
scenario:R18-U-review-binding-restoration sha256:c1009ffb93da27c30c1ca25fea26f30a7d376d437ffd79051696d18cac108e53
scenario:R18-U-review-publication-equivalence sha256:7aaad893c08f170dd9d55cad5c947acb67bd580e2d8a4c5ae972e12473964521
scenario:R18-U-schema-invalid-birth sha256:b1b052933ab5797075ee5b3cab2607e04f975e3639aa19d64d53de6a0cebf437
scenario:R18-U-second-birth sha256:5ab541a901c3d8973a650c18bbae8e5d54e17184a58f9dfdb23b375a27153fef
scenario:R18-U-transient-protected-mutation sha256:6356d37c4ade35ad68f3d150bdc06a2f3983c9297ac6bc419be36cdaf362f835
scenario:R18-U-task-pickup sha256:c5ea471772034b67f0e0c0dd5ad8ac6dd5ba75a8d12c9498acabb017669683b0
scenario:R18-U-unreadable-object sha256:58225cfa35c7268d95a3515352c9a78363d9edffcdfb9fd55710c37eff82ce17
scenario:R18-origin-arm-nodes-exact sha256:f4da25de95ba1de681d3a368e4a915e8350a0d231be38e392fe20c225b4ba9ef
scenario:R18-origin-arm-nodes-plus-one-refused sha256:92d157ab0770f813c2b89532785d76ded427184635790e65c929b7092e445720
scenario:R18-origin-parent-edges-exact sha256:f4da25de95ba1de681d3a368e4a915e8350a0d231be38e392fe20c225b4ba9ef
scenario:R18-origin-parent-edges-plus-one-refused sha256:92d157ab0770f813c2b89532785d76ded427184635790e65c929b7092e445720
scenario:R18-origin-witness-bytes-exact sha256:f4da25de95ba1de681d3a368e4a915e8350a0d231be38e392fe20c225b4ba9ef
scenario:R18-origin-witness-bytes-plus-one-refused sha256:92d157ab0770f813c2b89532785d76ded427184635790e65c929b7092e445720
scenario:R3-01-two-invalid-causal-sources sha256:a53104abe8ddc00a54de65fd93fc6679f248668793703081f3e53e5f5145cbb6
scenario:R3-02-invalid-valid-causal-competition sha256:278833b57aa902bcc3306c875adb1c0edf9cd6b09730b88f71e1f803b9e725e5
scenario:R3-03-valid-supplier-plus-invalid-parent-at-N-blocks sha256:42f1a09cdbcc797aea03e212090f31b98c5094dfbfc4f154d005d0c52d7a9f6c
scenario:R4-01-same-root-valid-diamond sha256:f91457d4984bc5d87546cc20e5f28f852dc364edc5e8a0fde2a6d2843390622d
scenario:R4-02-distinct-valid-root-diamond sha256:ce323651f427049b2389bbcf4ba55c227c120389704ae31e0061a1e0bf5b60ac
scenario:R4-03-equal-root-plus-invalid-diamond sha256:52bc694ab0bfb67fcdcd15c3f3cba276e8c9cce8a6a1ab2068d98c78ce6fda4f
scenario:R5-01-invalid-redelete-after-supplier-reintroduction sha256:e427d23cee74532869333f57a6a0df7226c8369782d44527b1a889014b46be89
scenario:R5-02-valid-redelete-after-supplier-reintroduction sha256:61a96397af440f17761df075c0219c62a7821b924aa3c3d35e5ae3135ee297b1
scenario:R6-01-valid-plus-invalid-all-absent sha256:9624e9467d01531c6d07bd7672a82353b3957065b9af3054c338fb24ed5653fb
scenario:R6-02-valid-plus-ambiguous-all-absent sha256:0634e1ba483a795867e8e33288a7f06d0a9c80eb195ed8df01e84733622db148
scenario:R6-03-two-invalid-all-absent sha256:4da64bb6eddda9ebca2bfa81bf6277c5778cbebf0ec15a2fc2eb9be26f68ff9c
scenario:R6-04-same-valid-root-all-absent-wrappers sha256:6f30ffd79c9f4f6c43037e5e1f269b1bd6e774ee7cb051e61a6984182911ca67
scenario:R8-direct-human-response-conflict sha256:cb4a507fa9f5ecf7d8bfd4eacb625484099aae8864a87d2c577741022843ccc5
scenario:R8-direct-human-response-identical sha256:cb4a507fa9f5ecf7d8bfd4eacb625484099aae8864a87d2c577741022843ccc5
scenario:R8-review-binding-divergent sha256:39465146932db98de812b38109cc96c4d42270872f51556f88e3e836c7ad201a
scenario:R8-review-binding-identical sha256:501f950ea7aea69d613cbf07e042a920de53cc782fa07c74f91ed0d6b98540c5
scenario:R8-review-binding-terminal-conflict sha256:64a91e5845f8534db3d1bb9362c0cfde8b9b59be8446c66510f95a2ae36f9e4c
scenario:R8-supplier-human-response-conflict sha256:c746a52e7cac498ab3cfa5c017585bd809bf40b89e391166c1d55e2a5e1efad5
scenario:R8-supplier-human-response-identical sha256:4818b25d2d279d0e5ad79cc155c14e30ced78af7e41a4cbd1a5079b3db6adb7b
scenario:R9-direct-review-revision-pending-fill sha256:e5148f2dffe3d589b2bb0b06a9f09b27f20fad2c5ed196c8403a6f7be25e29fd
scenario:R9-direct-review-target-pending-fill sha256:e5148f2dffe3d589b2bb0b06a9f09b27f20fad2c5ed196c8403a6f7be25e29fd
scenario:R9-supplier-review-revision-pending-fill sha256:5a62eb234b309010057eb613a6be716b48a9222f9b65c91a84b3d03e34b3ed6d
scenario:R9-supplier-review-target-pending-fill sha256:5a62eb234b309010057eb613a6be716b48a9222f9b65c91a84b3d03e34b3ed6d
scenario:W0-fast-forward-return sha256:1dfcde10e7b57e1905d25276d464665bd422aa79d25005430e203e3643aa8985
scenario:W1-pre-PR-push-exact-endpoints sha256:621ac415c58492828f2d9c40d9791fe782f5bb767be36a97af26279bb5ef250b
scenario:W2-base-advance-retarget-invariant sha256:184c52aae71d6ee24532c319f43313bae60a391c06851349ecd161b1d6a200fe
scenario:W3-multiple-PR-API-zero-calls sha256:0e70c77ed9716af5314322786706051fd971306263fd5b26232d049672dc6443
scenario:W4-stale-rerun-exact-inputs sha256:6461d566aa2f5203949f906ef30e3455ca778af13f99e3244aae015cab8277aa
scenario:W5-missing-O-coverage-unavailable sha256:ee917ef118937c57c4508dcf43c05feb874d1d5c23560caa2a1d98ef30c18c34
scenario:W6-created-deleted-zero-endpoints sha256:d30a2ba7092135979715101e2788f40a9c9774df00927c1f65d997f36d8d281b
scenario:W7-PR-synchronize-top-level-endpoints sha256:036b6126668bc82fbbe148144c2202c1e302e991648cb9709d46e014942fe3ba
parent-permutation sha256:96d2728c54be6458bedd52e4717ab16328e95a1f6874e1e56156dd931088d64d
aliases sha256:539a8708aebdaa2816ceb01ed2e091a849972b69700c444eeec8e566eaa9eed3
control:broad-review-pending-normalization sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414
control:buffered-graph-output sha256:a5c9687fc28f115ffb25a46739950c0bff58f1297ed55d7d953845957b91b5d5
control:endpoint-only-origin-equality sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
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
control:posthoc-budget-accounting sha256:34d3a59cb23be03b3687a5e44a27da906e1181389e054e98f6788474cb5e6e83
control:reopen-outside-C-boundary-ancestry sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:reopen-pre-C-genealogy sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:restore-universal-ancestor-carry-scan sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:skip-carry-compatibility sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:skip-old-side-continuity sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-origin-birth-uniqueness sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-origin-endpoint-non-regression sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-origin-post-birth-absence sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-persisted-candidate-continuity sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-persisted-frozen-skeleton sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-preserved-state-validation sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:skip-supplier-support-certificate sha256:e6d8aa17fd995baf10e03163e020ab50afb5e1b5bfcc3ebf515a9c09dc66a8ab
control:sole-valid-ignores-invalid-root sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:stream-malformed-truncated-final-line sha256:5f7ac68015df2e7b44146aa7b76438d931bd11e2682d67f3cbabc8a25b7e1c18
control:supplier-authority-borrowing sha256:889c75da0848d6f89f4d98b22ac05d36d45c3a1d4888d64ae67d9316869049f4
control:unmetered-cone-work sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:unmetered-dynamic-support sha256:247979e72c21e06ce04516c2b72a803d84b46428a0b274ce922a32c60821c96a
control:unmetered-object-payload sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:unmetered-support-construction sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:unmetered-tree-paths sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
summary sha256:076e24673c34bc6dcb5896b23fcf5c2134316e04ed3546b3fec9d7e28d0ee840
"""
RAW_SHAPE_SHA256 = dict(
    line.split(" ", 1)
    for line in RAW_SHAPE_CATALOG_V6.splitlines()
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
            "r18_origin_parent_permutation",
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
    origin = value["r18_origin_parent_permutation"]
    if (
        not isinstance(origin, list)
        or len(origin) != 2
        or origin[0] != origin[1]
    ):
        raise EvidenceError(f"{context} origin parent pair differs")
    for index, signature in enumerate(origin):
        require_keys(
            signature,
            (
                "birth_counts",
                "birth_witness_match",
                "classification",
                "edge_role_multiset",
                "evidence_status",
                "reason_code",
            ),
            f"{context}.r18_origin_parent_permutation[{index}]",
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
            "r18_origin_parent_permutation": "PASS",
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


def origin_proof_projection(proof):
    return {
        "birth_commits": proof["birth_commits"],
        "birth_schema_problems": proof["birth_schema_problems"],
        "birth_witness": proof["birth_witness"],
        "edges": [
            {
                "binding_problem": edge["binding_problem"],
                "child": edge["child"],
                "frozen_problem": edge["frozen_problem"],
                "parent": edge["parent"],
                "problem": edge["problem"],
                "production_problem": edge["production_problem"],
                "regression_problem": edge["regression_problem"],
                "role": edge["role"],
            }
            for edge in proof["edges"]
        ],
        "multiplicities": proof["multiplicities"],
        "outside_collisions": proof["outside_collisions"],
        "outside_neutral": proof["outside_neutral"],
        "post_birth_absent": proof["post_birth_absent"],
        "prebirth_neutral": proof["prebirth_neutral"],
        "reason": proof["reason"],
        "reason_code": proof["reason_code"],
        "status": proof["status"],
        "tip": proof["tip"],
    }


def origin_action_projection(action):
    return {
        "authoring_lineage": action["authoring_lineage"],
        "birth_witness_match": action["birth_witness_match"],
        "endpoint_checks": action["endpoint_checks"],
        "origin_proofs": [
            origin_proof_projection(proof)
            for proof in action["origin_proofs"]
        ],
        "reason_code": action["reason_code"],
        "strategy": action["origin_strategy"],
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
        "origin_actions": [
            origin_action_projection(action)
            for action in row["actions"]
            if action["origin_proofs"]
            or action["event_mode"].startswith("origin-")
        ],
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


def origin_case_projection(row):
    origin_actions = [
        action
        for action in row["actions"]
        if action["origin_proofs"]
        or action["event_mode"].startswith("origin-")
    ]
    action = origin_actions[0] if len(origin_actions) == 1 else None
    return {
        "audit_exit": row["audit_exit"],
        "birth_witness_match": (
            action["birth_witness_match"] if action is not None else None
        ),
        "classification": row["classification"],
        "endpoint_checks": (
            action["endpoint_checks"] if action is not None else {
                "binding": None,
                "frozen": None,
                "regression": None,
            }
        ),
        "evidence_status": row["evidence_verdict"]["status"],
        "origin_proofs": (
            [origin_proof_projection(x) for x in action["origin_proofs"]]
            if action is not None
            else []
        ),
        "reason_code": action["reason_code"] if action is not None else None,
        "record_sha256": record_digest(normalized_record(row)),
        "strategy": row["input_contract"]["origin_strategy"],
    }


def origin_strategy_projection(stream):
    case_ids = (
        "R18-U-normal-base-advance-replay",
        "R18-B-normal-base-advance-replay",
        "R18-U-independent-birth",
        "R18-B-independent-birth",
        "R18-U-exact-cherry-pick",
        "R18-B-exact-cherry-pick",
        "R18-U-generated-retry",
        "R18-B-generated-retry",
        "R18-U-task-pickup",
        "R18-B-task-pickup",
        "R18-U-agent-born-claimed",
        "R18-B-agent-born-claimed",
        "R18-U-human-born-answered",
        "R18-B-human-born-answered",
        "R18-U-review-publication-equivalence",
        "R18-B-review-publication-equivalence",
        "R18-U-rename-timing-move",
        "R18-B-rename-timing-move",
        "R18-U-delete-recreate-O",
        "R18-U-delete-recreate-N",
        "R18-U-transient-protected-mutation",
        "R18-U-human-response-restoration",
        "R18-U-review-binding-restoration",
        "R18-U-schema-invalid-birth",
        "R18-U-claim-restoration",
        "R18-U-second-birth",
        "R18-U-multiplicity",
        "R18-U-outside-collision",
        "R18-U-neutral-pre-origin-merge",
        "R18-U-inherited-then-deleted-merge-arm",
        "R18-U-unreadable-object",
    )
    cases = {
        scenario: origin_case_projection(stream.scenarios[scenario])
        for scenario in case_ids
    }
    legal_publication = cases[
        "R18-B-review-publication-equivalence"
    ]
    legal_publication_edges = [
        edge
        for proof in legal_publication["origin_proofs"]
        for edge in proof["edges"]
    ]
    bound_controls = (
        "endpoint-only-origin-equality",
        "skip-origin-birth-uniqueness",
        "skip-origin-post-birth-absence",
        "skip-origin-endpoint-non-regression",
    )
    return {
        "cases": cases,
        "damage_controls": {
            name: control_projection(stream.controls[name])
            for name in bound_controls
        },
        "decision": "U",
        "decision_basis": (
            "U already rejects claimed and answered births; B adds no safety "
            "for those illegal origins and falsely blocks two production-legal "
            "histories that converge on the same unanswered review"
        ),
        "selection_boundary": {
            "B_false_blocks_legal_review_publication": (
                legal_publication["classification"] == "blocking-finding"
                and legal_publication["reason_code"]
                == "origin-birth-witness-mismatch"
            ),
            "legal_publication_edges_all_production_valid": bool(
                legal_publication_edges
            ) and all(
                edge["production_problem"] is None
                and edge["frozen_problem"] is None
                and edge["regression_problem"] is None
                and edge["problem"] is None
                for edge in legal_publication_edges
            ),
            "legal_publication_endpoints_equal": all(
                problem is None
                for problem in legal_publication["endpoint_checks"].values()
            ),
            "U_rejects_agent_born_claimed": (
                cases["R18-U-agent-born-claimed"]["classification"]
                == "blocking-finding"
                and cases["R18-U-agent-born-claimed"]["reason_code"]
                == "origin-birth-schema-invalid"
            ),
            "U_rejects_human_born_answered": (
                cases["R18-U-human-born-answered"]["classification"]
                == "blocking-finding"
                and cases["R18-U-human-born-answered"]["reason_code"]
                == "origin-birth-schema-invalid"
            ),
            "claim": (
                "neither U nor B proves intent, replay provenance, or a "
                "relationship between independently identical legal births"
            ),
        },
        "parent_permutation": stream.permutation[
            "r18_origin_parent_permutation"
        ],
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
        "origin_strategies": origin_strategy_projection(stream),
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
            "r18_origin_parent_permutation": stream.summary[
                "r18_origin_parent_permutation"
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


def validate_origin_proof(value, context):
    require_keys(value, (
        "birth_commits", "birth_schema_problems", "birth_witness", "edges",
        "multiplicities", "outside_collisions", "outside_neutral",
        "post_birth_absent", "prebirth_neutral", "reason", "reason_code",
        "status", "tip",
    ), context)
    require_oid(value["tip"], f"{context}.tip")
    if value["status"] not in {"valid", "ambiguous"}:
        raise EvidenceError(f"{context}.status is not structured")
    for key in (
        "birth_commits", "outside_neutral", "post_birth_absent",
        "prebirth_neutral",
    ):
        for index, oid in enumerate(value[key]):
            require_oid(oid, f"{context}.{key}[{index}]")
    for index, edge in enumerate(value["edges"]):
        edge_context = f"{context}.edges[{index}]"
        require_keys(
            edge,
            (
                "binding_problem", "child", "frozen_problem", "parent",
                "problem", "production_problem", "regression_problem",
                "role",
            ),
            edge_context,
        )
        require_oid(edge["child"], f"{edge_context}.child")
        require_oid(edge["parent"], f"{edge_context}.parent")
        if edge["role"] not in {"source", "compatible-carrier", "unselected"}:
            raise EvidenceError(f"{edge_context}.role is invalid")
    for index, item in enumerate(value["birth_schema_problems"]):
        item_context = f"{context}.birth_schema_problems[{index}]"
        require_keys(item, ("commit", "problem"), item_context)
        require_oid(item["commit"], f"{item_context}.commit")
        if not isinstance(item["problem"], str) or not item["problem"]:
            raise EvidenceError(f"{item_context}.problem is not concrete")
    for index, item in enumerate(value["multiplicities"]):
        item_context = f"{context}.multiplicities[{index}]"
        require_keys(item, ("commit", "multiplicity", "paths"), item_context)
        require_oid(item["commit"], f"{item_context}.commit")
        require_nonnegative_int(item["multiplicity"], f"{item_context}.multiplicity")
    for index, collision in enumerate(value["outside_collisions"]):
        item_context = f"{context}.outside_collisions[{index}]"
        require_keys(
            collision, ("multiplicity", "parent", "paths", "scope"),
            item_context,
        )
        require_oid(collision["parent"], f"{item_context}.parent")
        require_nonnegative_int(
            collision["multiplicity"], f"{item_context}.multiplicity"
        )
        if collision["scope"] != "outside-C":
            raise EvidenceError(f"{item_context}.scope changed")
    witness = value["birth_witness"]
    if witness is not None:
        require_keys(witness, ("digest", "state"), f"{context}.birth_witness")
        require_digest(witness["digest"], f"{context}.birth_witness.digest")
        state = witness["state"]
        require_keys(state, (
            "actor", "delivery_class", "frozen_skeleton",
            "initial_lifecycle_review_binding", "leaf",
            "production_identity_transcript", "schema",
        ), f"{context}.birth_witness.state")
        if state["schema"] != "queue-birth-state-witness/v1":
            raise EvidenceError(f"{context} birth witness schema changed")
        if "path" in state or "metrics" in state or "diagnostics" in state:
            raise EvidenceError(f"{context} birth witness admitted excluded data")
        lifecycle = state["initial_lifecycle_review_binding"]
        if "status" not in lifecycle:
            raise EvidenceError(f"{context} birth witness lost lifecycle status")


def validate_origin_action(value, context):
    require_keys(value, (
        "authoring_lineage", "birth_witness_match", "endpoint_checks",
        "origin_proofs", "reason_code", "strategy",
    ), context)
    if value["strategy"] not in {"U", "B"}:
        raise EvidenceError(f"{context}.strategy is invalid")
    if value["birth_witness_match"] not in {True, False, None}:
        raise EvidenceError(f"{context}.birth_witness_match is invalid")
    require_keys(
        value["endpoint_checks"], ("binding", "frozen", "regression"),
        f"{context}.endpoint_checks",
    )
    for index, proof in enumerate(value["origin_proofs"]):
        validate_origin_proof(proof, f"{context}.origin_proofs[{index}]")


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
        "r18_origin_parent_permutation",
        "scenario_passed", "scenario_total", "status",
    ), "summary")
    summary = manifest["summary"]
    require_digest(summary["canonical_stream_sha256"], "summary stream digest")
    counts = {
        "aliases_passed": len(ALIAS_IDS), "aliases_total": len(ALIAS_IDS),
        "controls_passed": len(CONTROL_IDS), "controls_total": len(CONTROL_IDS),
        "r17_parent_permutation": "PASS",
        "r18_origin_parent_permutation": "PASS",
        "scenario_passed": len(SCENARIO_IDS), "scenario_total": len(SCENARIO_IDS),
        "status": "PASS",
    }
    for key, expected in counts.items():
        if summary[key] != expected:
            raise EvidenceError(f"summary {key} is not {expected!r}")
        if key not in {
            "status", "r17_parent_permutation",
            "r18_origin_parent_permutation",
        }:
            require_nonnegative_int(summary[key], f"summary.{key}")

    scenarios = manifest["scenarios"]
    if [x.get("id") for x in scenarios] != list(SCENARIO_IDS):
        raise EvidenceError("manifest scenario inventory/order differs")
    scenario_keys = (
        "audit_exit", "authority_edges", "carry_proofs", "classification",
        "endpoints", "event_mode",
        "evidence_status", "expected_result", "finding_count", "id",
        "input_contract", "metrics", "mutation_edge_count", "propagation_edges",
        "origin_actions", "reason_codes", "record_sha256",
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
            "direct", "supplier", "none", "ambiguous", "mixed",
            "origin-U", "origin-B",
        }:
            raise EvidenceError(f"{context} event mode is invalid")
        if row["validation_status"] != "PASS":
            raise EvidenceError(f"{context} validation did not pass")
        if row["audit_exit"] not in {0, 1, 2}:
            raise EvidenceError(f"{context}.audit_exit is invalid")
        require_keys(
            row["input_contract"],
            ("authoritative_endpoints", "origin_strategy", "schema"),
            f"{context}.input_contract",
        )
        if row["input_contract"] != {
            "authoritative_endpoints": ["O", "N"],
            "origin_strategy": row["input_contract"]["origin_strategy"],
            "schema": "restack-provenance-input/v2",
        }:
            raise EvidenceError(f"{context} input contract changed")
        if row["input_contract"]["origin_strategy"] not in {"U", "B"}:
            raise EvidenceError(f"{context} origin strategy changed")
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
        for i, action in enumerate(row["origin_actions"]):
            validate_origin_action(action, f"{context}.origin_actions[{i}]")

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
        "execution_bounds", "measured_budget", "origin_strategies",
        "parent_permutation",
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
    origins = core["origin_strategies"]
    require_keys(
        origins,
        (
            "cases", "damage_controls", "decision", "decision_basis",
            "parent_permutation", "selection_boundary",
        ),
        "origin_strategies",
    )
    if origins["decision"] != "U":
        raise EvidenceError("origin strategy decision changed")
    required_origin_cases = {
        "R18-U-normal-base-advance-replay",
        "R18-B-normal-base-advance-replay",
        "R18-U-independent-birth",
        "R18-B-independent-birth",
        "R18-U-exact-cherry-pick",
        "R18-B-exact-cherry-pick",
        "R18-U-generated-retry",
        "R18-B-generated-retry",
        "R18-U-task-pickup",
        "R18-B-task-pickup",
        "R18-U-agent-born-claimed",
        "R18-B-agent-born-claimed",
        "R18-U-human-born-answered",
        "R18-B-human-born-answered",
        "R18-U-review-publication-equivalence",
        "R18-B-review-publication-equivalence",
        "R18-U-rename-timing-move",
        "R18-B-rename-timing-move",
        "R18-U-delete-recreate-O",
        "R18-U-delete-recreate-N",
        "R18-U-transient-protected-mutation",
        "R18-U-human-response-restoration",
        "R18-U-review-binding-restoration",
        "R18-U-schema-invalid-birth",
        "R18-U-claim-restoration",
        "R18-U-second-birth",
        "R18-U-multiplicity",
        "R18-U-outside-collision",
        "R18-U-neutral-pre-origin-merge",
        "R18-U-inherited-then-deleted-merge-arm",
        "R18-U-unreadable-object",
    }
    if set(origins["cases"]) != required_origin_cases:
        raise EvidenceError("origin strategy case inventory changed")
    origin_case_keys = (
        "audit_exit", "birth_witness_match", "classification",
        "endpoint_checks", "evidence_status", "origin_proofs", "reason_code",
        "record_sha256", "strategy",
    )
    for scenario, case in origins["cases"].items():
        context = f"origin_strategies.cases.{scenario}"
        require_keys(case, origin_case_keys, context)
        require_keys(
            case["endpoint_checks"],
            ("binding", "frozen", "regression"),
            f"{context}.endpoint_checks",
        )
        if case["record_sha256"] != by_id[scenario]["record_sha256"]:
            raise EvidenceError(f"{context} record binding changed")
        require_digest(case["record_sha256"], f"{context}.record_sha256")
        for index, proof in enumerate(case["origin_proofs"]):
            validate_origin_proof(proof, f"{context}.origin_proofs[{index}]")
    expected_classifications = {
        "R18-U-normal-base-advance-replay": "no-finding",
        "R18-B-normal-base-advance-replay": "no-finding",
        "R18-U-generated-retry": "no-finding",
        "R18-B-generated-retry": "no-finding",
        "R18-U-task-pickup": "no-finding",
        "R18-B-task-pickup": "no-finding",
        "R18-U-agent-born-claimed": "blocking-finding",
        "R18-B-agent-born-claimed": "blocking-finding",
        "R18-U-human-born-answered": "blocking-finding",
        "R18-B-human-born-answered": "blocking-finding",
        "R18-U-review-publication-equivalence": "no-finding",
        "R18-B-review-publication-equivalence": "blocking-finding",
        "R18-U-schema-invalid-birth": "blocking-finding",
    }
    for scenario, expected in expected_classifications.items():
        if origins["cases"][scenario]["classification"] != expected:
            raise EvidenceError(f"origin strategy verdict changed for {scenario}")
    boundary = origins["selection_boundary"]
    require_keys(
        boundary,
        (
            "B_false_blocks_legal_review_publication",
            "U_rejects_agent_born_claimed",
            "U_rejects_human_born_answered", "claim",
            "legal_publication_edges_all_production_valid",
            "legal_publication_endpoints_equal",
        ),
        "origin_strategies.selection_boundary",
    )
    if any(
        boundary[key] is not True
        for key in (
            "B_false_blocks_legal_review_publication",
            "U_rejects_agent_born_claimed",
            "U_rejects_human_born_answered",
            "legal_publication_edges_all_production_valid",
            "legal_publication_endpoints_equal",
        )
    ):
        raise EvidenceError("origin strategy selection boundary changed")
    legal_case = origins["cases"][
        "R18-B-review-publication-equivalence"
    ]
    legal_edges = [
        edge
        for proof in legal_case["origin_proofs"]
        for edge in proof["edges"]
    ]
    if (
        boundary["B_false_blocks_legal_review_publication"]
        is not (
            legal_case["classification"] == "blocking-finding"
            and legal_case["reason_code"]
            == "origin-birth-witness-mismatch"
        )
        or boundary["legal_publication_edges_all_production_valid"]
        is not (
            bool(legal_edges)
            and all(
                edge[key] is None
                for edge in legal_edges
                for key in (
                    "production_problem", "frozen_problem",
                    "regression_problem", "problem",
                )
            )
        )
        or boundary["legal_publication_endpoints_equal"]
        is not all(
            problem is None
            for problem in legal_case["endpoint_checks"].values()
        )
        or boundary["U_rejects_agent_born_claimed"]
        is not (
            origins["cases"]["R18-U-agent-born-claimed"][
                "reason_code"
            ] == "origin-birth-schema-invalid"
        )
        or boundary["U_rejects_human_born_answered"]
        is not (
            origins["cases"]["R18-U-human-born-answered"][
                "reason_code"
            ] == "origin-birth-schema-invalid"
        )
    ):
        raise EvidenceError("origin strategy selection evidence disagrees")
    origin_control_ids = {
        "endpoint-only-origin-equality",
        "skip-origin-birth-uniqueness",
        "skip-origin-post-birth-absence",
        "skip-origin-endpoint-non-regression",
    }
    if set(origins["damage_controls"]) != origin_control_ids:
        raise EvidenceError("origin damage-control inventory changed")
    if any(
        row["status"] != "OBSERVED_RED"
        for row in origins["damage_controls"].values()
    ):
        raise EvidenceError("origin damage control false-greened")
    if origins["parent_permutation"] != core["parent_permutation"][
        "r18_origin_parent_permutation"
    ]:
        raise EvidenceError("origin parent permutation projection changed")
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
    origins = core["origin_strategies"]
    by_id = {x["id"]: x for x in manifest["scenarios"]}
    p22, p19 = by_id["P22-PCX-18-one-pass-many-actions"], by_id["PCX-19-missing-claim-blob-recovery"]
    lines = [
        "# Production-contract provenance POC", "",
        "This file is generated in full by `audit_readme.py` from the closed",
        "`evidence.json` manifest. Do not edit observations here by hand.", "",
        "## Result", "",
        f"The real-Git self-test passed {summary['scenario_passed']}/{summary['scenario_total']} scenarios, {summary['aliases_passed']}/{summary['aliases_total']} executable aliases, and {summary['controls_passed']}/{summary['controls_total']} damaged-mode controls.",
        "It imports and calls the worktree's actual `queue_action_identity` and",
        "`queue_deletion_problem`, and `queue_mutation_problem`; it never invents",
        "an Action-ID or lifecycle verdict.", "",
        f"Canonical evidence artifact: `{evidence_sha}`.",
        f"Canonical semantic stream: `{summary['canonical_stream_sha256']}`.",
        "The raw JSONL stream is ephemeral and has no stored hash claim.",
        f"Evidence schemas v2 at commit `{core['evidence_supersession']['artifacts'][0]['commit']}`, v3 at commit `{core['evidence_supersession']['artifacts'][1]['commit']}`, v4 at commit `{core['evidence_supersession']['artifacts'][2]['commit']}`, and v5 at commit `{core['evidence_supersession']['artifacts'][3]['commit']}` are superseded and burned by their later blockers; all histories are preserved, no identifier is reused, and this artifact closes `{core['evidence_supersession']['replacement_schema']}`.",
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
        "## Absent-at-C strategy comparison", "",
        "Strategy U is selected for this POC. When an identity is absent at C but live",
        "once at O and N, it independently proves exactly one all-parents-absent legal",
        "birth on each arm, followed by uninterrupted production-valid carriage. An",
        "all-parents-absent candidate is legal only when its historical queue header",
        "passes the production path/actor/leaf, delivery, field, lifecycle, context,",
        "and exact identity-round-trip projection; repository-global reciprocity and",
        "current-template presentation remain separate admission gates. Agent actions,",
        "including generated retries and task pickups, must be born `open`; human",
        "decisions and clarifications must be born `waiting` and unanswered; reviews",
        "must be born unanswered in `awaiting-artifact` or `waiting`, never `folding`.",
        "An outside-C carrier collides; a second birth, multiplicity, post-birth absence,",
        "delete/recreate, invalid or frozen mutation, binding regression, incompatible",
        "merge carrier, unreadable object, or endpoint non-regression failure blocks.",
        "Absent merge parents that do not descend from the birth are neutral.", "",
        "Strategy B layers a canonical birth-state witness on U. Its witness contains",
        "only the production identity transcript, actor, leaf, production delivery",
        "class, frozen skeleton, and initial lifecycle/review-binding projection. It",
        "contains no queue path, commit, timestamp, mutable retry diagnosis, or operational",
        "counter. Both strategies clean exact cherry-pick, independently identical birth,",
        "generated retry, task pickup, and rename/timing-move fixtures.", "",
        "U's typed birth gate rejects an agent action born `in-repair` and a human",
        "decision born with a concrete answer under both strategies. B therefore adds",
        "no protection for those former claim-at-birth examples. B does, however, block",
        "a fully legal pair: one review is born `awaiting-artifact` and reaches `waiting`",
        "through the exact production publication transition, while the other is born",
        "`waiting` with the same binding and endpoint state. Every production mutation",
        f"check accepts that edge: `{origins['selection_boundary']['legal_publication_edges_all_production_valid']}`; every endpoint non-regression check is also clean: `{origins['selection_boundary']['legal_publication_endpoints_equal']}`. U stays clean and B blocks only on `origin-birth-witness-mismatch`, so B is redundant for illegal births and false-blocking for a legal restack; U is selected.",
        "Both strategies claim only equivalent valid live incarnations. Neither claims",
        "human intent, replay/cherry-pick provenance, or a relationship between independently",
        "identical legal births. Equal B witnesses would still not prove that one birth",
        "came from the other. Endpoint-only equality exists only in the",
        "`endpoint-only-origin-equality` observed-red damaged mutant; it is not a normal",
        "strategy branch.", "",
        "| Fixture | U | B | Witness match |", "|---|---|---|---|",
        f"| Normal base advance + replayed addition | `{origins['cases']['R18-U-normal-base-advance-replay']['classification']}` | `{origins['cases']['R18-B-normal-base-advance-replay']['classification']}` | `{origins['cases']['R18-B-normal-base-advance-replay']['birth_witness_match']}` |",
        f"| Independently identical birth | `{origins['cases']['R18-U-independent-birth']['classification']}` | `{origins['cases']['R18-B-independent-birth']['classification']}` | `{origins['cases']['R18-B-independent-birth']['birth_witness_match']}` |",
        f"| Agent action born claimed (illegal) | `{origins['cases']['R18-U-agent-born-claimed']['classification']}` | `{origins['cases']['R18-B-agent-born-claimed']['classification']}` | `{origins['cases']['R18-B-agent-born-claimed']['birth_witness_match']}` |",
        f"| Human decision born answered (illegal) | `{origins['cases']['R18-U-human-born-answered']['classification']}` | `{origins['cases']['R18-B-human-born-answered']['classification']}` | `{origins['cases']['R18-B-human-born-answered']['birth_witness_match']}` |",
        f"| Legal review publication equivalence | `{origins['cases']['R18-U-review-publication-equivalence']['classification']}` | `{origins['cases']['R18-B-review-publication-equivalence']['classification']}` | `{origins['cases']['R18-B-review-publication-equivalence']['birth_witness_match']}` |", "",
        "## Bound r17 review outcomes", "",
        f"The exact reviewer DAG is clean and record-bound by `{core['reviewer_dag']['record_sha256']}`; its outside-C parent is neutral, its task patch replays exactly, and production deletion authority returns no problem.",
        f"R3-03 is blocking at the fixed N frontier with one invalid authority edge and is record-bound by `{core['r3_full_frontier']['record_sha256']}`.",
        f"The hidden-G attacker is clean at exit 0 and record-bound by `{core['boundary_ancestry']['record_sha256']}`: F is the neutral boundary, G carries the same identity in a unique missing blob, and G ancestry remains unopened.",
        f"R6-02 is explicitly dispositioned clean and record-bound by `{core['r6_outside_boundary_disposition']['record_sha256']}` because its outside-C boundary is absent; the ambiguous ancestor behind it is not reopened.",
        "All eight persisted-state attacker cases block in both parent orders: outside-C exact carriers retain multiplicity 1 or 2 as collisions, while valid and unauthorized absent C-descendant arms both remain deletion/reintroduction competitors.",
        f"The 64-parent outside-C octopus exits 2 transactionally and is record-bound by `{core['measured_budget']['wide_boundary']['record_sha256']}`; no action, edge, support, or carry-proof result leaks past the exceeded parent-token budget.",
        f"The P22 pre-charge case stops exactly at `object_reads=134>133`, keeps Git processes at {core['measured_budget']['precharge_P22']['precharge_expected_metrics']['git_processes']}, freezes later counters, and is record-bound by `{core['measured_budget']['precharge_P22']['record_sha256']}`; its post-hoc damage reproduces the prior 10,973-snapshot/24,736-cache-hit full run.",
        f"Ten runtime exact/+1 pairs bind streaming graph bytes/lines/tokens, object payloads, flattened trees, dynamic support traversal, certificate serialization, origin-arm nodes/parent edges, and canonical birth-witness bytes. Every +1 refusal exits 2 with zero partial results; graph reads peak at {bounds['streaming_graph_contract']['bounded_chunk_bytes']} bytes per chunk and publish nothing on refusal. P22 separately observes exactly {bounds['composition_observation']['production_parent_queries']} imported production parent queries and {bounds['composition_observation']['git_processes']} Git processes.",
        f"Unreadable Git objects use the stable typed reason `{core['stable_git_diagnostics']['stable_reasons']['C']}`. Every Git child is forced to C locale and UTC; the stable C/French results are equal even though the independent ambient diagnostic streams differ.",
        f"Before any projection or digest, all {core['raw_grammar']['record_kinds']} raw rows must match the static recursive key/list/type grammar catalog `{core['raw_grammar']['catalog_sha256']}`; an unknown top-level or nested field exits {core['raw_grammar']['unknown_field_exit']}.",
        "The parent-order pair has identical verdicts and the same role multiset:",
        f"`{core['parent_permutation']['r17_parent_permutation'][0]['merge_role_multiset']}`. The four persisted parent-order pairs and the origin-birth parent-order pair are also equal by semantic signature.", "",
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
              "The closed runtime matrix additionally admits/refuses exact/+1 values for total graph bytes, peak graph-line bytes, a 1,000,000-byte object, 1,004 flattened paths, 12 dynamic support paths, 2,920 serialized certificate bytes, five origin-arm nodes, three origin parent edges, and 1,042 canonical birth-witness bytes.", "",
              f"PCX-19 is replay-bound by `{p19['record_sha256']}`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.", "",
              "## Reproducible audit", "",
              "Use two fresh, empty scratch roots:", "", "```sh",
              "PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r18-v6-seed1 > /tmp/production-contract-r18-v6-seed1.jsonl",
              "PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --reverse-construction --fixtures-dir /tmp/production-contract-r18-v6-seed777 > /tmp/production-contract-r18-v6-seed777.jsonl",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r18-v6-seed1.jsonl --compare /tmp/production-contract-r18-v6-seed777.jsonl",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r18-v6-seed1.jsonl --damage-test",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --old FULL_OID_O --new FULL_OID_N --origin-strategy U",
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
              "- This executable comparison is not production-ready and does not authorize production integration.",
              "- This POC changes no production reconciler, restack adapter, workflow input, schema, task, queue, memory, or history record.",
              "- A post-push check can only be advisory; prevention requires a pre-push or server-side production gate.",
              "- Strategy U accepts only typed legal live-incarnation births and does not prove squash, replay, or cherry-pick provenance; a squash that creates claimed or answered state at birth is illegal, and deletion-only resolution provenance remains unsupported and blocks.",
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
        "superseded-v5-commit-erased",
        lambda d: d["core_claims"]["evidence_supersession"][
            "artifacts"
        ][3].update(commit="0" * 40),
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
        "origin-normal-restack-false-block",
        lambda d: d["core_claims"]["origin_strategies"]["cases"][
            "R18-U-normal-base-advance-replay"
        ].update(classification="blocking-finding"),
        "origin strategy verdict changed",
    )
    manifest_case(
        "origin-illegal-agent-birth-false-clean",
        lambda d: d["core_claims"]["origin_strategies"]["cases"][
            "R18-U-agent-born-claimed"
        ].update(classification="no-finding"),
        "origin strategy verdict changed",
    )
    manifest_case(
        "origin-illegal-human-birth-false-clean",
        lambda d: d["core_claims"]["origin_strategies"]["cases"][
            "R18-U-human-born-answered"
        ].update(classification="no-finding"),
        "origin strategy verdict changed",
    )
    manifest_case(
        "origin-decision-flipped-to-B",
        lambda d: d["core_claims"]["origin_strategies"].update(
            decision="B"
        ),
        "origin strategy decision changed",
    )
    manifest_case(
        "origin-legal-publication-false-block-erased",
        lambda d: d["core_claims"]["origin_strategies"][
            "selection_boundary"
        ].update(B_false_blocks_legal_review_publication=False),
        "origin strategy selection boundary changed",
    )
    manifest_case(
        "origin-legal-publication-production-edge-corrupted",
        lambda d: d["core_claims"]["origin_strategies"]["cases"][
            "R18-B-review-publication-equivalence"
        ]["origin_proofs"][0]["edges"][0].update(
            production_problem="injected production rejection"
        ),
        "origin strategy selection evidence disagrees",
    )
    manifest_case(
        "origin-parent-permutation-first-parent",
        lambda d: d["core_claims"]["parent_permutation"][
            "r18_origin_parent_permutation"
        ][1].update(edge_role_multiset=["source"]),
        "origin parent pair differs",
    )
    manifest_case(
        "origin-damage-control-false-green",
        lambda d: d["core_claims"]["origin_strategies"][
            "damage_controls"
        ]["skip-origin-birth-uniqueness"].update(status="FALSE_GREEN"),
        "origin damage control false-greened",
    )
    manifest_case(
        "origin-witness-path-injected",
        lambda d: d["scenarios"][
            next(
                index for index, row in enumerate(d["scenarios"])
                if row["id"] == "R18-B-normal-base-advance-replay"
            )
        ]["origin_actions"][0]["origin_proofs"][0]["birth_witness"][
            "state"
        ].update(path="message-queue/injected.md"),
        "keys differ",
    )
    manifest_case(
        "origin-witness-counter-injected",
        lambda d: d["scenarios"][
            next(
                index for index, row in enumerate(d["scenarios"])
                if row["id"] == "R18-B-normal-base-advance-replay"
            )
        ]["origin_actions"][0]["origin_proofs"][0]["birth_witness"][
            "state"
        ].update(metrics={"origin_arm_nodes": 1}),
        "keys differ",
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
