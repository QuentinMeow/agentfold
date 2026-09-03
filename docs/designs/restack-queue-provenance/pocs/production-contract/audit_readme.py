#!/usr/bin/env python3
"""Generate and verify the production-contract POC evidence artifact.

``evidence.json`` is the sole machine-observation artifact. This stdlib-only
program derives it from a fresh prototype JSONL stream, enforces a closed
schema and exact record catalog, and renders README.md in full. Verification
compares bytes, never prose fragments or an OID pool.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import errno
import fcntl
import functools
import hashlib
import json
import operator
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any


SCHEMA = "agentfold-production-contract-evidence/v13"
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
        {
            "commit": "9ab61c416be1911e44c6bce2b3d711b6f2abef15",
            "disposition": (
                "superseded and burned after fresh-replay, deterministic "
                "merge-carrier, descriptor-lifecycle, and executable "
                "event-adapter blockers; history is preserved and v6 is "
                "never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v6",
        },
        {
            "commit": "820ae1a788f5b24493a4277fb4d79981e0be202f",
            "disposition": (
                "superseded and burned after endpoint/budget pre-validation, "
                "duplicate-parent, startup-authority, artifact-pair, and "
                "post-cleanup resource-accounting blockers; history is "
                "preserved and v7 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v7",
        },
        {
            "commit": "c3793ec53c9b6aebe03b6e1b1cfa7badf3d4828a",
            "disposition": (
                "superseded and burned after verified-descriptor-closure and "
                "externally observable transaction-accounting blockers; "
                "history is preserved and v8 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v8",
        },
        {
            "commit": "8abc908840191185e222a29132e72630ebf73a21",
            "disposition": (
                "superseded and burned after arbitrary-throwable cleanup, "
                "attempt-versus-child accounting, non-reentrant spawn, "
                "runtime-input, and recoverable pair-publication blockers; "
                "history is preserved and v9 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v9",
        },
        {
            "commit": "5872446ad4ed1e9940f96b6e28b8f7042fccf6d1",
            "disposition": (
                "superseded and burned after same-process overlap, broad "
                "factory-throwable, stale owning-pipe, independent cleanup, "
                "and hostile artifact-target blockers; history is preserved "
                "and v10 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v10",
        },
        {
            "commit": "1e1b81adae4cba13d29fac221a3de6ea78612ce7",
            "disposition": (
                "superseded and burned after duplicate-module session, "
                "construction-close ambiguity, live-date replay, and "
                "single-descriptor journal/artifact race blockers; history "
                "is preserved and v11 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v11",
        },
        {
            "commit": "62b5715bb7d34cda32dfc71329e58680c3efb3b1",
            "disposition": (
                "superseded and burned after exact event-kind typing and "
                "JSON-domain invalid-value projection blockers; history is "
                "preserved and v12 is never reused"
            ),
            "schema": "agentfold-production-contract-evidence/v12",
        },
    ],
    "replacement_schema": SCHEMA,
}
METRIC_KEYS = (
    "git_processes", "git_process_attempts", "graph_enumerations", "graph_commits",
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
    "git_process_attempts": 4,
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
    "object_process_reaps": 1,
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
    "git_process_attempts": 135,
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
    "object_process_reaps": 1,
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
    "R18-U-review-compatible-merge",
    "R18-U-review-compatible-merge-reversed",
    "R18-U-review-compatible-source-high",
    "R18-U-review-compatible-source-high-reversed",
    "R18-U-review-compatible-source-low",
    "R18-U-review-compatible-source-low-reversed",
    "R18-U-review-duplicate-parent-header",
    "R18-U-review-incompatible-carrier",
    "R18-U-review-publication-equivalence",
    "R18-U-review-three-carrying-parents",
    "R18-U-review-two-valid-sources",
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
    "R19-WF-local-blocking-attack",
    "R19-WF-local-missing-old",
    "R19-WF-local-normal-restack",
    "R19-WF-pre-push-blocking-attack",
    "R19-WF-pre-push-normal-restack",
    "R19-WF-pull-request-synchronize-blocking-attack",
    "R19-WF-pull-request-synchronize-head-mismatch",
    "R19-WF-pull-request-synchronize-normal-restack",
    "R19-WF-push-blocking-attack",
    "R19-WF-push-normal-restack",
    "R19-WF-push-zero-before",
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
    "event-adapter-cli-entrypoint",
    "literal-review-pending-treated-concrete",
    "locale-git-error-stream-equality",
    "leak-object-database-pipes",
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
    "reject-all-origin-invalid-carriers",
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


# Generated from a byte-identical forward/reverse v13 pair. Every row kind has
# one exact recursive shape digest, checked before any projection.
RAW_SHAPE_CATALOG_V13 = """
scenario:P1-direct-linear-valid sha256:3f69e6eb45b0e39682e27340f52f906139997a9ddcde927478e17a9239b6d8e4
scenario:P10-direct-invalid-parent sha256:b188bdde0c472555a55ccba6a06e6c5dd562240bb94d5056aad98d6405595122
scenario:P11-direct-three-parent-valid sha256:15b54ce5edfc83f16f307df8bba037da1cb471246757eb9ad33f93e8dd8cc001
scenario:P12-merge-supplier-valid sha256:fbd4c9e963a970a68828ae90c4c20a1b12eda60babc0b3270cd8f155252960a1
scenario:P13-merge-supplier-invalid sha256:25fe82f029f2079f6a0de875b53004b3fbc4926d9dcdc0b9a35c93df8884a564
scenario:P14-supplier-reintroduced sha256:10de26e94ab6bd97d7b766bed8c8f07a182806dae5b61b9e620039648350c3b1
scenario:P15-competing-suppliers sha256:0418c41afbdb72a61ea269041e2fc26a5eb37f25ad536167a6a14f1987723fbc
scenario:P16-PCX-08-invalid-supplier-claimed-carrier sha256:ea39c7361468c88045fcc53ac45dcdb313cc428fc1bb2ce9de059795f6b8be55
scenario:P17-post-event-reintroduction sha256:5f7067af07cb015f4e097b13795e3f9a37bae5e650781456423e3b4096ece06d
scenario:P18a-missing-tip sha256:484c42d290a80c37a6620eba4a72f4da8a8c6432f8ed710ae152bde9b12d2195
scenario:P18b-noncommit-tip sha256:484c42d290a80c37a6620eba4a72f4da8a8c6432f8ed710ae152bde9b12d2195
scenario:P18c-unrelated-tip sha256:484c42d290a80c37a6620eba4a72f4da8a8c6432f8ed710ae152bde9b12d2195
scenario:P18d-shallow-required-region sha256:484c42d290a80c37a6620eba4a72f4da8a8c6432f8ed710ae152bde9b12d2195
scenario:P18e-missing-queue-blob sha256:7df8b7135b3a8de4317277c1bfe63cccd1b463c7aec4074973dd61f091e3eef8
scenario:P18f-missing-queue-tree sha256:791ee1dfe7a2b0d2788c5931e102e84752022329f84200556be981d8e59ddb54
scenario:P18g-multiple-merge-bases sha256:d374a6473a0b910213d95ce00b82f001b5607bebc2de66676d9f99399665f9b1
scenario:P19-production-identities sha256:3b83346e5ca576e0228cf74dedf2d77e215c20f1b790f2deedc08c73a00cb12a
scenario:P2-direct-linear-invalid sha256:66641222d8afa414d54f059fd2bb0e2b78f30d42a90c265bc26402ad575e79e1
scenario:P20-lifecycle-types sha256:2eac97da65250eb6710600ce712954fcaedc8cb6f8571ec420b93dbdaa2cd255
scenario:P21-PCX-17c-squash-erasure sha256:dc5b7e2ba67e0aaa9a68d72ac865d4288cf5a51cbaefe76c910eff001a219592
scenario:P22-PCX-18-one-pass-many-actions sha256:d13c8a464621f7ce7ba141061d8a3df36fa4c723eaede9eafac22ded16769b3e
scenario:P3-genuine-old-loss sha256:f1a8c5423510dd9868dcede08d5e540d4912ee0ea0c1d0d49e30c4101d0d3585
scenario:P4-pre-C-identical-origins sha256:312e9557a8bd1c4e75941f6fd083f41beb65a275a65216b0237f35068a3fd570
scenario:P5-duplicate-at-C sha256:6dea6d63720af1d2220a43f13b0cb91f86bea5d96c5de511c2d9f290185f9186
scenario:P6a-old-delete-recreate sha256:288bfdd6500bdd7e2c0a670c7cb7ea38c08aae7302b1b8a98d137f4b84acd78a
scenario:P6b-candidate-delete-recreate sha256:522722143a989e4ecf8f1f3c5bd33c9c3ee48cb5ae33eaed01d3368862786635
scenario:P7-immutable-payload-change sha256:6573fc8c3f900533ddd09b556ceccaf7f6afadbba62e89dbfeb24122228a26cf
scenario:P8-path-timing-move sha256:37e654bdc671b610065e3ea1e8366dc50181d09d5eaa6cede769b3aaba9974c4
scenario:P9-direct-two-parent-valid sha256:68558110d70a367fe284ebf49cac7d1272c2175c89dd607123cf63d95d90bfc7
scenario:PCX-01-neutral-parent sha256:ed1febc3a16bbbd1346730e9d4eb3b93f0e999c2bddb17a6c0f694f80cb98d1d
scenario:PCX-02-neutral-plus-invalid-carrier sha256:d56ad2f2170044f04bf07fc0ba6eb0f748cc0cbda8b425f0ea665482155d70c4
scenario:PCX-03-foreign-exact-identity sha256:bdf0c63f151675b1f5f68572c2c572eacfc92f650d59b03eb5942d038fa28c47
scenario:PCX-04-several-absent-one-supplier sha256:3f61176a016964d8c6c5728c1f37ead51854cde5ef55fb72dd9b4622f8b99626
scenario:PCX-05-competing-later-supplier sha256:6081c2bed21d25f8f4701791989bcadb553940b2d28d4392803df6fab7762637
scenario:PCX-06-nested-supplier-over-direct sha256:d78623672b2bca7dc0308c45fda53e6026f2d1bd2df685a0fc63a8ef76592a6a
scenario:PCX-07-overqualified-propagation sha256:aea340d7522c13a414299c4c9a8b7805164308c7aa16c7de813ed9934efde39e
scenario:PCX-09-recreated-claimed-bytes sha256:76d98eb4b3ced9e1db04cda6d832f82caa346d63710e64fe7c2d583a9bb59fbf
scenario:PCX-10-transient-multiplicity sha256:3e8a6aee31d42e90c014a4abe73d77e5aa01af42f4ff6aa794808929998719c1
scenario:PCX-11-different-payload-same-path sha256:a9478143128bd39525f2874293fb6f0ae30e4ba1267b2c58af57c718e1e5398c
scenario:PCX-12-timing-rename-supplier sha256:e6a0b4295f5d500d35364227072155c9e0521306e346ffe2da0fef68b0519a35
scenario:PCX-13-conflicting-human-response sha256:ab4f193c8702ab6f27a8829afd2386ed6c6aee545a09aebf3cdc324401a2fe45
scenario:PCX-14-valid-human-supplier sha256:a91e2209c7671f6385ff8b2714ee2d0f3296f7e4f816c0402b0b8c9f8501f0d9
scenario:PCX-15-generated-retry-supplier sha256:1de5f83af467772c545840e32eba80da4fd881f6c130041d791a47a258ed332e
scenario:PCX-16-task-pickup-supplier sha256:a7a058bfd19c10048bee5a2212cbe03b7d8f0614c8f391ad7dda658b11a24bde
scenario:PCX-17-complete-cherry-pick sha256:0db4896b882ec810042deaf693f8417c9bcb8c9441764bae5518d656a512e1eb
scenario:PCX-17-deletion-only-cherry-pick sha256:dc5b7e2ba67e0aaa9a68d72ac865d4288cf5a51cbaefe76c910eff001a219592
scenario:PCX-19-missing-claim-blob-recovery sha256:4d4a6e4c8fdf964d77394a57e88fe1d38e136958615fa7ea2d1201c3494cdc13
scenario:PCX-20a-budget-below-limit sha256:b2da7f333431b67f0026113417e6e253f6ae3024b73bbb128ab13fe1b715ffd2
scenario:PCX-20b-budget-overflow sha256:d7174e4850658921c1b673f9388769775c83309bdb7e8f5cae575e9a3818d4e3
scenario:R10-direct-review-target-backtick-dotless-rejected sha256:2c2d9f34a8cb401e99c6c45c80218710bd3d131211fc0c8b20d5b0d752d76bad
scenario:R10-supplier-review-revision-generic-placeholder-rejected sha256:0ebdb560c7a4bc9e5fecd31c5a74a648b7766ba4f1fb30c366578c919ab95eae
scenario:R13-direct-review-binding-identical sha256:3ca820ee8b80fec5e495a91d7fb8a910ca14da940772e4a0ed7c23b09435ce51
scenario:R13-direct-review-binding-revision sha256:3266b24531144ed00d5a517de0b15b76837dc0b8445f55ac919981302032db8e
scenario:R13-direct-review-binding-target sha256:3a1bb8d07f0b6bbc2af0fc8f85998cc2a0f2ef0efd16649330f4a0b2c00cd6d7
scenario:R13-direct-review-binding-terminal sha256:5bf55e37ddb987c57777a585e609ccacaf605c2dcadcaad0bed1a7f912b87df8
scenario:R13-persisted-claim-loss sha256:5c4a6b99a37b3f290125a5994ef61f4f05dcaf5e29feb6eaba1c53cd5d8a8d7f
scenario:R13-persisted-pending-fill sha256:3f76ef2c8115027fb269c2c60cb881cd2964d6c86f7d719b4f101dd2451c3eef
scenario:R13-persisted-response-change sha256:1c57f571e2a3a9209301ad0a910998489ce8d7577db25f480505b555ae58035c
scenario:R13-persisted-response-removal sha256:e42ff0be3aac429af8d062d0cb33b77e139e8d568638e66ceaa0e3b4f6a2f977
scenario:R13-persisted-review-outcome-change sha256:22e04703a6a2c68978e65b2b702e5b9f562dfca4b821f4ec494b23709d0df5ef
scenario:R13-persisted-review-revision-change sha256:22e04703a6a2c68978e65b2b702e5b9f562dfca4b821f4ec494b23709d0df5ef
scenario:R13-persisted-review-target-change sha256:22e04703a6a2c68978e65b2b702e5b9f562dfca4b821f4ec494b23709d0df5ef
scenario:R13-persisted-same-state sha256:aba596e0fcdc4e5a9ae3fc9f39484a11bf1514504e1b5b234a2250a137de9fb4
scenario:R13-persisted-terminal-fill sha256:f1c7e89077d0699e16437ce1d42d65673fdd162a5848f69d100593ad3c3fdb81
scenario:R13-supplier-review-binding-identical sha256:6ffcc3bb44ea4dfa7219715b69282553de9ac5104125b79655e39e0946b24586
scenario:R13-supplier-review-binding-revision sha256:2c0bddfd75f98631287b158566e6b51656156f68cac77eb77b85041e88173c1e
scenario:R13-supplier-review-binding-target sha256:2c0bddfd75f98631287b158566e6b51656156f68cac77eb77b85041e88173c1e
scenario:R13-supplier-review-binding-terminal sha256:c6daf64dabd6d7b0255435593c09e2e8250f80bee5565e25a19d47b29dbc24f7
scenario:R14-direct-old-unanswered-carrier-same sha256:918ea84715bb0b32df96259d5566b1db55f6bc0523f73764c093b551aa808ac6
scenario:R14-direct-old-unanswered-carrier-target sha256:918ea84715bb0b32df96259d5566b1db55f6bc0523f73764c093b551aa808ac6
scenario:R14-persisted-delete-recreate sha256:5dfaca2b79751cc3126964613f584a0a3ad246bede3c08ec7b347dd4f627c564
scenario:R14-persisted-hidden-bytes-low-similarity sha256:e2456bc170b0f5a61657078e678c4554e3c4a0e4e939f5e41df3058114ae9b6c
scenario:R14-persisted-intermediate-claim-regression sha256:5c1fe888325e4bc39b1a2be4c340d6ad557a6af57927569774f2e7aaf0180f38
scenario:R14-persisted-intermediate-review-regression sha256:145f91b45365895b3765f329b0c7049db593808c302875d4741f3b9310932a56
scenario:R14-persisted-merge-carrier-conflict sha256:41eba755810b3cb2626ab3f3f9acb4df0bbbcc12272dce9da23e45b3425b5359
scenario:R14-persisted-merge-carrier-pending sha256:35e47a25dd40b017af417312d366238c42bc99360a2f61f8e0aa2020e218f9b5
scenario:R14-persisted-valid-first-response-low-similarity sha256:e87591ff675bdced7b84562a8e2331c05da55ceeeedd95b237725988f32e49b0
scenario:R14-persisted-valid-review-retraction sha256:3d7b323caf8a3049f896ced5bd312349de1868c2fe12a152a4abee9c76a31db0
scenario:R14-supplier-old-answered-carrier-pending sha256:be3b876678e3dac0813253ae2ebd7b15ba030da06340ae8e5988dad6421864f9
scenario:R14-supplier-old-answered-carrier-revision sha256:be3b876678e3dac0813253ae2ebd7b15ba030da06340ae8e5988dad6421864f9
scenario:R14-supplier-old-answered-carrier-same sha256:be3b876678e3dac0813253ae2ebd7b15ba030da06340ae8e5988dad6421864f9
scenario:R14-supplier-old-answered-carrier-target sha256:be3b876678e3dac0813253ae2ebd7b15ba030da06340ae8e5988dad6421864f9
scenario:R14-supplier-old-unanswered-carrier-same sha256:fc6e9017bc66a41a14e6f079da05ac30556746190fcae3dae31ec9301ed4afd0
scenario:R14-supplier-old-unanswered-carrier-target sha256:fc6e9017bc66a41a14e6f079da05ac30556746190fcae3dae31ec9301ed4afd0
scenario:R15-old-continuous-preserved sha256:4173f700b26cb83acd6c684159da24b747395c9f4bcfe40403ec61f58306c69b
scenario:R15-old-hidden-bytes-restore sha256:82420c05a8f5b368a61ba11f305a2e9c6ede050c303d4aba8d17394fd44b277b
scenario:R15-old-human-binding-restore sha256:1da313e07ec89a8df54c0e70116c18353568f4c619b0a2b833cd77ebcf9fe294
scenario:R15-old-invalid-delete-recreate sha256:03e37773ed910c375d55c1cb853912bb48c088f5eb898da11c90024c726677c1
scenario:R15-old-valid-delete-recreate sha256:667598c93f7b22a4370cb3ad51ee1a6a48c03e8555c0c00b8e3f9447d5f720cf
scenario:R16-earlier-landed-evidence-reversal sha256:68286b0cba8c1163bed1db8cc078dde0927e063bb8e4801cb3cd088237cca039
scenario:R16-pickup-evolution-0-backlog sha256:ba18b96fcf36bf7ac72046ef33f42cbc46f105b0282859294d7e25b694320dfd
scenario:R16-pickup-evolution-2-blocked sha256:cbb484f2ba02f44c245368a8862ace647a43b5e8e64f9475064e21920d105e6a
scenario:R16-pickup-evolution-3-in-review sha256:aa373863b086f9065dd904b9fcd4fbcb005d85072c89f6c7855c1e7f34225752
scenario:R16-pickup-evolution-3-in-review-drop-artifact sha256:1701e5b227ab4a01cfd2f6b3501d66c0c8366aea851cd5992051cd2df14f0c83
scenario:R16-pickup-evolution-4-done sha256:aa373863b086f9065dd904b9fcd4fbcb005d85072c89f6c7855c1e7f34225752
scenario:R16-support-adoption-drift sha256:0c9aa42e7be89458f99a8472f7de80580cc368924c4594f9bfbe7f1ef9fec4b9
scenario:R16-support-forward sha256:70cb04bcff501623ab2fd0d9633d7d7b33eaae130c2a0bc0dcdf2c0df86a5bb9
scenario:R16-support-invalid-source sha256:0191162de44e312505d9dcce4924f6da17abafede09c014a7cd29f46b5e336d6
scenario:R16-support-nested-drop sha256:e0399cc530d6f1bab7b19e97dc1935f7b96f123386cbe29f051e28ba0d8b4011
scenario:R16-support-permutation-diamond sha256:aa93e6f5ac75bce09b3ec6b2b46f85e4ce5655685564d5265e1905a47ae5501e
scenario:R16-support-reverse-drop sha256:304cc43ffdda502cbd47fa9fdba7a062cea00345b7f782dca15da9143991f754
scenario:R16-support-reverse-preserved sha256:70cb04bcff501623ab2fd0d9633d7d7b33eaae130c2a0bc0dcdf2c0df86a5bb9
scenario:R16-support-source-evolution sha256:70cb04bcff501623ab2fd0d9633d7d7b33eaae130c2a0bc0dcdf2c0df86a5bb9
scenario:R17-carry-absent-arm sha256:fea4f9e5124d0e6d6e497ad92ed53adb01cddcb573551bf66c9676f2218f4592
scenario:R17-carry-compatible sha256:64498ee1ab780ed3eb6c345f742d66c51a38c75f4fe5461ed299da2f2efe63e6
scenario:R17-carry-compatible-reversed sha256:64498ee1ab780ed3eb6c345f742d66c51a38c75f4fe5461ed299da2f2efe63e6
scenario:R17-carry-incompatible sha256:d441015743f5ce839280e4b955dc6a526a616c56f885baed94dc665c79ef8f22
scenario:R17-carry-outside-duplicate sha256:0bc901be0854638fad0c75f68b34ea8426d4ae1dc76c8a674764d1bb7278bdbd
scenario:R17-carry-outside-single sha256:3e41f6b960cb8175b01f4a789d8243e90472076f9b1ef0931a1e8747eb2086ba
scenario:R17-dynamic-support-traversal-exact sha256:89846322fbf57ca0e9d34668bccba51a2cced8b1d41a4ca2427d4686dada2425
scenario:R17-dynamic-support-traversal-plus-one-refused sha256:1bb9716e4ed10e296fdf73dc8769edcfd31549ca71078e65c0d9552ba2a44d30
scenario:R17-flat-tree-peak-exact sha256:be87a3ce95d6e221c3a0debcfb012a80cbb001fd0e7f1f618a7c18f69ca3d40b
scenario:R17-flat-tree-peak-plus-one-refused sha256:d75d8fafcc79a39ce3a650d79763c9f78a4d5dfa0a7bdc7893cd5024e610b00b
scenario:R17-graph-line-peak-bytes-exact sha256:eeac98c4b11ca9c95f578aa4c6a998aa0edaa9c98200730740d9dc496b0f62dd
scenario:R17-graph-line-peak-bytes-plus-one-refused sha256:f409cac529ae21afa505fd3decf9e8bcf7c3381ec2b6c030cd571b7813db83e7
scenario:R17-graph-output-bytes-exact sha256:eeac98c4b11ca9c95f578aa4c6a998aa0edaa9c98200730740d9dc496b0f62dd
scenario:R17-graph-output-bytes-plus-one-refused sha256:f409cac529ae21afa505fd3decf9e8bcf7c3381ec2b6c030cd571b7813db83e7
scenario:R17-graph-parent-tokens-exact sha256:eeac98c4b11ca9c95f578aa4c6a998aa0edaa9c98200730740d9dc496b0f62dd
scenario:R17-graph-parent-tokens-plus-one-refused sha256:f409cac529ae21afa505fd3decf9e8bcf7c3381ec2b6c030cd571b7813db83e7
scenario:R17-object-payload-peak-exact sha256:588f6da569d694253c02a5a698f3752d1930969378a3717367be15397ec241a1
scenario:R17-object-payload-peak-plus-one-refused sha256:f57b0ccac0b9a0651bfe37c002a572849e91e9099c8162a288d687c0c7703da2
scenario:R17-outside-C-neutral-parent-valid-restack sha256:697ad6591c20b837314dcebe1fc1293e85ea84695049cc7d74c5abcd378354c6
scenario:R17-persisted-outside-duplicate sha256:2b651744df31dd71962f2ee066fbb7deae8cec12147f6e2c80dc198a29496a0c
scenario:R17-persisted-outside-duplicate-reversed sha256:2b651744df31dd71962f2ee066fbb7deae8cec12147f6e2c80dc198a29496a0c
scenario:R17-persisted-outside-single sha256:7bd50aabdbb1d806cc50d654e02e1207ad80609cb443a0d484dcccb91455a35a
scenario:R17-persisted-outside-single-reversed sha256:7bd50aabdbb1d806cc50d654e02e1207ad80609cb443a0d484dcccb91455a35a
scenario:R17-persisted-unauthorized-absent-arm sha256:06156b1103cc00e3eea55684092d206c24fc55972cde49084bf058588d44b58d
scenario:R17-persisted-unauthorized-absent-arm-reversed sha256:06156b1103cc00e3eea55684092d206c24fc55972cde49084bf058588d44b58d
scenario:R17-persisted-valid-absent-arm sha256:bc5b6383f600810e03fce70b41c10bbec56c0478e2695f4172dd06fa12deaf37
scenario:R17-persisted-valid-absent-arm-reversed sha256:bc5b6383f600810e03fce70b41c10bbec56c0478e2695f4172dd06fa12deaf37
scenario:R17-precharge-P22-budget sha256:c98bda20ba4579580fbb5914202ccb3fb50126e94d58c46662fb6ad832014d4a
scenario:R17-support-serialized-exact sha256:6e617bebb11e485fecdbfed2aca4597faf45d675d01a697e72e61a6629263a53
scenario:R17-support-serialized-plus-one-refused sha256:9c0b65bcf4007050bf3b4ad88ab769d9de787e2bbf083f299313092b9303c8ae
scenario:R17-unreadable-outside-C-ancestor-stays-unopened sha256:b49f8635daee3559f84ff2f2211e0d2457db98b280f351124164f617beda120b
scenario:R17-unreadable-outside-C-boundary sha256:9535e1af85a816a24de09ab718f77b5b3db5b7f1d9bab10b5d4e8dd3b74ad74c
scenario:R17-wide-outside-C-boundary-budget sha256:6e3a3e4848f2c486021bb2ae5a745c790afcc405c2266ab8dfbef61388f6be6d
scenario:R18-B-exact-cherry-pick sha256:af343c9f43f7a728521c8159dc270bf8834b1af961e0d6db1f75f44e7995eab2
scenario:R18-B-agent-born-claimed sha256:44381522677eccc795de461021e53f898c83f567701251ae4dac83e8b90e0820
scenario:R18-B-generated-retry sha256:87cf794e219fca49bf26d83af2bb1a1b3b29c84fa86d0872864dc6c2c61d5ccc
scenario:R18-B-human-born-answered sha256:dac54fd3c0731deaff043257984d6befc9e4f07e4d2e1db8a3ca5c9a9806ed4b
scenario:R18-B-independent-birth sha256:af343c9f43f7a728521c8159dc270bf8834b1af961e0d6db1f75f44e7995eab2
scenario:R18-B-normal-base-advance-replay sha256:af343c9f43f7a728521c8159dc270bf8834b1af961e0d6db1f75f44e7995eab2
scenario:R18-B-rename-timing-move sha256:f5e7b6ad1ef86652d06662ce65b8d819e5bd2b8276aba51bfd587fc18e122f11
scenario:R18-B-review-publication-equivalence sha256:e9eefcf87c9b76cb1f39288d8a19da744c4b9824f4119560a474dc679dc491c4
scenario:R18-B-task-pickup sha256:965495da2581c01aff03d9ce1117942c3af86660f6bde25641535b6ef00084f9
scenario:R18-U-O-only-post-C-loss sha256:bdc88e19a0a54a9acec647764aae261fcbeebd2ff0e845d8c600ff56bb630547
scenario:R18-U-agent-born-claimed sha256:44381522677eccc795de461021e53f898c83f567701251ae4dac83e8b90e0820
scenario:R18-U-claim-restoration sha256:61123e2efc9fcc84b6d5a5d8e7e2c02ab10c935f056392a5063a2a7df5940dc5
scenario:R18-U-delete-recreate-N sha256:e8b7e3a8f5aba84e8e9a6f3d3749895abdaaa715eff2f4e47dc90be2437b8199
scenario:R18-U-delete-recreate-O sha256:8c56b7fa8d784c71b8daaa99f282dbe148733d07cceccfc6c6c289bf7e9450d4
scenario:R18-U-endpoint-regression sha256:32a6838b4d494d7fa0d51a9c3949d0a6fd587a3976a9f56dc6cbceefb1952338
scenario:R18-U-exact-cherry-pick sha256:af343c9f43f7a728521c8159dc270bf8834b1af961e0d6db1f75f44e7995eab2
scenario:R18-U-generated-retry sha256:87cf794e219fca49bf26d83af2bb1a1b3b29c84fa86d0872864dc6c2c61d5ccc
scenario:R18-U-human-born-answered sha256:dac54fd3c0731deaff043257984d6befc9e4f07e4d2e1db8a3ca5c9a9806ed4b
scenario:R18-U-human-response-restoration sha256:8d2dbedf3794323dc72ea16d3ba7cf61e940a14c0caa2261e0e6966ba7d308d2
scenario:R18-U-independent-birth sha256:af343c9f43f7a728521c8159dc270bf8834b1af961e0d6db1f75f44e7995eab2
scenario:R18-U-inherited-then-deleted-merge-arm sha256:4c5e7cbc15c8b00c7d4ef31f93b7719bce6c373fe61452d99f6e6774d62afb18
scenario:R18-U-multiplicity sha256:efe96cd6df1d6ce37c7e9a4aa1c76efe9c004aa4437434b4510606ee74b22d72
scenario:R18-U-neutral-pre-origin-merge sha256:092fda6dbb736771765b78e17d108ed769e15b178d6c078029c961b231951cee
scenario:R18-U-normal-base-advance-replay sha256:af343c9f43f7a728521c8159dc270bf8834b1af961e0d6db1f75f44e7995eab2
scenario:R18-U-outside-collision sha256:1cc1a714baa01ea1531959dd0e51de0826b8d10a7ce4fb6c0ee29dcfc2bd9ffc
scenario:R18-U-parent-order sha256:600b4b0bfb4c8f20e8923cff47316854bf8f0eb2f985ccbf93625a2ee5b4e849
scenario:R18-U-parent-order-reversed sha256:600b4b0bfb4c8f20e8923cff47316854bf8f0eb2f985ccbf93625a2ee5b4e849
scenario:R18-U-rename-timing-move sha256:f5e7b6ad1ef86652d06662ce65b8d819e5bd2b8276aba51bfd587fc18e122f11
scenario:R18-U-review-binding-restoration sha256:7129072ea64d1e81d1609284f9811d72202a01218af287ab7f41b483f505c78f
scenario:R18-U-review-compatible-merge sha256:d86467491c90ce97dad0b152b4530cb3a02b35a2975319e641be5ddccecfcc53
scenario:R18-U-review-compatible-merge-reversed sha256:d86467491c90ce97dad0b152b4530cb3a02b35a2975319e641be5ddccecfcc53
scenario:R18-U-review-compatible-source-high sha256:3ae55b02db4b89c3a01385da717ce35a1afb78846a5500b8be2db29dca456715
scenario:R18-U-review-compatible-source-high-reversed sha256:3ae55b02db4b89c3a01385da717ce35a1afb78846a5500b8be2db29dca456715
scenario:R18-U-review-compatible-source-low sha256:3ae55b02db4b89c3a01385da717ce35a1afb78846a5500b8be2db29dca456715
scenario:R18-U-review-compatible-source-low-reversed sha256:3ae55b02db4b89c3a01385da717ce35a1afb78846a5500b8be2db29dca456715
scenario:R18-U-review-duplicate-parent-header sha256:43a9007946da1fdfdcd39cb659d17028f54f4a54e34fccd042d32ed89e895332
scenario:R18-U-review-incompatible-carrier sha256:3c16d0a464b8627e8509d9ba1111a1eadcf9bb1691b6f34e5146a449b721d239
scenario:R18-U-review-publication-equivalence sha256:e9eefcf87c9b76cb1f39288d8a19da744c4b9824f4119560a474dc679dc491c4
scenario:R18-U-review-three-carrying-parents sha256:8ce074baaba52dd4a6141959ea6abea323af253bc807e5de0408dc2e2c860131
scenario:R18-U-review-two-valid-sources sha256:dd45d83e3cd02c324128444f0b119eba31bb9d14e7de66379121b93e4420e64b
scenario:R18-U-schema-invalid-birth sha256:156b92e05a0174f78efe58c56b5c5d0e4c8a72e17df554acadc6d023416d047b
scenario:R18-U-second-birth sha256:c60355dcacc3fa9d6b80164e9fb708aea0e432295ae7a5c8f014f5864ace9e05
scenario:R18-U-transient-protected-mutation sha256:b765a643a407e9098f740e67d2d003288873a4969e6394384a5923d00a83064a
scenario:R18-U-task-pickup sha256:965495da2581c01aff03d9ce1117942c3af86660f6bde25641535b6ef00084f9
scenario:R18-U-unreadable-object sha256:b542ce78d60d61bccca5edf9af75696c01ab39a9816f57baf1142d5813bde396
scenario:R18-origin-arm-nodes-exact sha256:93872d850a02056453e5d8519e91780553ae2bdee2636c9ff2e36a4bd0de8518
scenario:R18-origin-arm-nodes-plus-one-refused sha256:d25e08fb8268d3abf32936ef6e4ef38948128dd7f6e8edfd7c5d91efb49ed2ee
scenario:R18-origin-parent-edges-exact sha256:93872d850a02056453e5d8519e91780553ae2bdee2636c9ff2e36a4bd0de8518
scenario:R18-origin-parent-edges-plus-one-refused sha256:d25e08fb8268d3abf32936ef6e4ef38948128dd7f6e8edfd7c5d91efb49ed2ee
scenario:R18-origin-witness-bytes-exact sha256:93872d850a02056453e5d8519e91780553ae2bdee2636c9ff2e36a4bd0de8518
scenario:R18-origin-witness-bytes-plus-one-refused sha256:d25e08fb8268d3abf32936ef6e4ef38948128dd7f6e8edfd7c5d91efb49ed2ee
scenario:R19-WF-local-blocking-attack sha256:0d29d77e75f5466076f762c28b9f4817f3ac5647e0fc2e9d1ee5406b5df05a3f
scenario:R19-WF-local-missing-old sha256:22e73ea40c62a7c50bb43879fd98bd32673d1980ba8b2807afb22780a2f2a408
scenario:R19-WF-local-normal-restack sha256:b45d325027b0f12f91765ba6c546917b2ffea5575510c5d3d65cd9d41183489c
scenario:R19-WF-pre-push-blocking-attack sha256:0d29d77e75f5466076f762c28b9f4817f3ac5647e0fc2e9d1ee5406b5df05a3f
scenario:R19-WF-pre-push-normal-restack sha256:b45d325027b0f12f91765ba6c546917b2ffea5575510c5d3d65cd9d41183489c
scenario:R19-WF-pull-request-synchronize-blocking-attack sha256:1fa0f71c2024c4c3471fa3dc71414471d160b3f6c01636f677ae0f4db41b36d7
scenario:R19-WF-pull-request-synchronize-head-mismatch sha256:a7757d25d1ffbef8456be28dc3e6be7b7db8c98fa975a5ecc01894fe25afb954
scenario:R19-WF-pull-request-synchronize-normal-restack sha256:b735c1bf397f9b57bf2a58e062fb9fa1a6a22dfced8065608bac0552f677d149
scenario:R19-WF-push-blocking-attack sha256:e4bcb4850631075df3ff4db55267130ae062d4b921d63d342caa870ce92e7ff8
scenario:R19-WF-push-normal-restack sha256:1ef564f2c61e4e2bd072c18cebb984cf7f7d1a603652a1fe824cecd773934fc1
scenario:R19-WF-push-zero-before sha256:27e0760a8f73a497b78c8ef55419d3f6302fbd1674bf74c5e0fcacd0b5aa4eae
scenario:R3-01-two-invalid-causal-sources sha256:172ba471e8508ce7aa89e3a090aabb1b0d8aecc83917f8a45f2b243a6e148f00
scenario:R3-02-invalid-valid-causal-competition sha256:34523843ae383db05e90e5a51c67fe41763e6ffe1f15adb8a6953e650d23bf5b
scenario:R3-03-valid-supplier-plus-invalid-parent-at-N-blocks sha256:ed75fbedcbb145584e5157db361895b67fe3768aa6eae9c2678cd79a4c1b3e7f
scenario:R4-01-same-root-valid-diamond sha256:9bea75dd0b378d1d84c67faf0ed46edd8ac13e1c4f87ea76bcd69a0a4d0803d4
scenario:R4-02-distinct-valid-root-diamond sha256:314484920297d014a2cbdad899beda0d32ce3750e52109fb0a2b3feef99814a2
scenario:R4-03-equal-root-plus-invalid-diamond sha256:bc6f5b2313eca0b1b41da64d83bd1e35f8c5c7326bee53ade743cf17c8667740
scenario:R5-01-invalid-redelete-after-supplier-reintroduction sha256:d60fd9a5ef28030624b3b8e782dd0d877dd48dcf47cd32369c4872b8f5028c28
scenario:R5-02-valid-redelete-after-supplier-reintroduction sha256:ea2fe1102c4311a7facff9b91c80f16d1f9844032b212d74729c37ef25c6a352
scenario:R6-01-valid-plus-invalid-all-absent sha256:43d01d2ab561c1f52e8fe20156d7aa8e2aeb22a3a8bc84f33a1c891ff9ebc8fe
scenario:R6-02-valid-plus-ambiguous-all-absent sha256:91b62b05ce59e24429bb26a205d8ddec5c8da3b94b58407de885522a067f6127
scenario:R6-03-two-invalid-all-absent sha256:943b00a8dde6495acfdc51b83353136d4eaf0f70e82e5a4c5feaf394a113ab6a
scenario:R6-04-same-valid-root-all-absent-wrappers sha256:b95cd13b9fecc8e5d9940aa06f50231b95da47081ce266c8bb0e6e8eb82e2532
scenario:R8-direct-human-response-conflict sha256:4caf58b8fb6192b8324a85f25073898c298933501c94f800da1d44bf9c9ef053
scenario:R8-direct-human-response-identical sha256:4caf58b8fb6192b8324a85f25073898c298933501c94f800da1d44bf9c9ef053
scenario:R8-review-binding-divergent sha256:9a7dbdbe2aaefec267625261b749ee644a12fe0bfd4fb992d13b4ad2ccd5a951
scenario:R8-review-binding-identical sha256:5055f312bbbafa422fb5737167de2d31cfdde36b4924fa47a0d08523bf79dc2a
scenario:R8-review-binding-terminal-conflict sha256:4b9c7ab7862f3f518367190e38d31dc1fda8bedbabe603e58bbb5782d26892c4
scenario:R8-supplier-human-response-conflict sha256:ef42ce10fd9d72527c6d25b5eeb48ac3d42d557ee060ff4fbc96852276f5f2c8
scenario:R8-supplier-human-response-identical sha256:6a850c500149fd70e2fe037ab8dcbb3e43dd85ac5d7de941fb6e3306441100a8
scenario:R9-direct-review-revision-pending-fill sha256:749099a16e681caf9236fcb3707258a1420999efb8e054419f196ebf15887bae
scenario:R9-direct-review-target-pending-fill sha256:749099a16e681caf9236fcb3707258a1420999efb8e054419f196ebf15887bae
scenario:R9-supplier-review-revision-pending-fill sha256:7e2e7d29e371e15e093aca36c3be8621c81c7cfcf4b59fbf69018e63410451ca
scenario:R9-supplier-review-target-pending-fill sha256:7e2e7d29e371e15e093aca36c3be8621c81c7cfcf4b59fbf69018e63410451ca
scenario:W0-fast-forward-return sha256:a2b47c0501cfc5c17fee2537d822adeaa6b5f919f88e97a8ce4414591df18975
scenario:W1-pre-PR-push-exact-endpoints sha256:b1d8e2c838c0ca10b157dad28aec2a144fd3832d2d72c567ef3702d6960ac725
scenario:W2-base-advance-retarget-invariant sha256:b67a2dbfc59b35ec5c915e32a90e3927f6b163483531d990a3758423791743d7
scenario:W3-multiple-PR-API-zero-calls sha256:6cda6762ba0e83a92c1d4c8c6c1183c1074f561e8684e7ca8d66b7653383ef54
scenario:W4-stale-rerun-exact-inputs sha256:da4533c33b0244206bcb6adf7321dff7ceedd98907e32e1765041ff5f62d47d2
scenario:W5-missing-O-coverage-unavailable sha256:a1f745627934c577144fc71afdbf977811d5fb0e27a7cc4ca5eaee9163a27a2e
scenario:W6-created-deleted-zero-endpoints sha256:3a1d69f7e5666cc1c4bb25f7799f79fdcc1922f3a4762fcd78a8f5195b3efd2a
scenario:W7-PR-synchronize-top-level-endpoints sha256:36a41fbd13d0ef7ba5124c467c10a1c2bef8d2b0151dcf42e9070420346f2c9d
parent-permutation sha256:4eb67669a07e806e1078f6638453877ac49ad2a4ab0b4dd1594c9615e38cde6a
aliases sha256:539a8708aebdaa2816ceb01ed2e091a849972b69700c444eeec8e566eaa9eed3
control:broad-review-pending-normalization sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414
control:buffered-graph-output sha256:a5c9687fc28f115ffb25a46739950c0bff58f1297ed55d7d953845957b91b5d5
control:endpoint-only-origin-equality sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:event-adapter-cli-entrypoint sha256:1e054af68b87ccb8a2a41e8534e37124819d00ddbae1f5465154cb98a515e286
control:first-parent-carry-proof sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:identity-multiplicity-collapsed-to-set sha256:1ac1b79c19942df728cefbeb0153aeb8b42f07ceffc5343fd5981b03e6048190
control:ignore-absent-C-arm sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:ignore-invalid-N-root sha256:e6d8aa17fd995baf10e03163e020ab50afb5e1b5bfcc3ebf515a9c09dc66a8ab
control:ignore-outside-C-carrier sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:ignore-persisted-absent-C-arm sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:ignore-persisted-outside-C-collision sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:leak-object-database-pipes sha256:eb14c3a1780702a8a7977554588cab2c9fb7e6231aba19297700dc031c1b5691
control:literal-review-pending-treated-concrete sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414
control:locale-git-error-stream-equality sha256:742dda0d750851fe1eaf99a187460279385d12aadb25de6479979cbea272c8e4
control:missing-all-parent-direct-validation sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:missing-post-event-continuity sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:omit-old-tip-human-binding sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414
control:omit-supplier-carrier-human-binding sha256:465ccf7bbd7c9fc49c2576a9974d06ef1c8ec5cf27711192ed3bb05d1b009deb
control:omit-unanswered-published-review-binding sha256:465ccf7bbd7c9fc49c2576a9974d06ef1c8ec5cf27711192ed3bb05d1b009deb
control:posthoc-budget-accounting sha256:fb64818ed04662ec2013d149a95dd883f3521e2915bc716edd49c4f629ce331a
control:reject-all-origin-invalid-carriers sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
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
control:stream-malformed-truncated-final-line sha256:1f4a29ab671f9498ddb20451c04603151f4ee2a5ea11d2983616e623370be409
control:supplier-authority-borrowing sha256:889c75da0848d6f89f4d98b22ac05d36d45c3a1d4888d64ae67d9316869049f4
control:unmetered-cone-work sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2
control:unmetered-dynamic-support sha256:247979e72c21e06ce04516c2b72a803d84b46428a0b274ce922a32c60821c96a
control:unmetered-object-payload sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:unmetered-support-construction sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
control:unmetered-tree-paths sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4
summary sha256:b957b61b2a27224040772a4629d78ad28a6877450d639808664ac078929a351e
"""
RAW_SHAPE_SHA256 = dict(
    line.split(" ", 1)
    for line in RAW_SHAPE_CATALOG_V13.splitlines()
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
            "r19_review_merge_parent_permutations",
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
    review = value["r19_review_merge_parent_permutations"]
    expected_cases = (
        "review-compatible-merge",
        "review-compatible-source-high",
        "review-compatible-source-low",
    )
    if not isinstance(review, dict) or tuple(sorted(review)) != expected_cases:
        raise EvidenceError(f"{context} review merge permutation catalog differs")
    for case in expected_cases:
        pair = review[case]
        if not isinstance(pair, list) or len(pair) != 2 or pair[0] != pair[1]:
            raise EvidenceError(
                f"{context} review merge permutation differs for {case}"
            )
        for index, signature in enumerate(pair):
            require_keys(
                signature,
                (
                    "classification", "compatible_carriers",
                    "evidence_status", "invalid_edges", "reason_code",
                    "role_multiset", "selected_source_is_canonical",
                ),
                f"{context}.r19_review_merge_parent_permutations."
                f"{case}[{index}]",
            )
            if (
                signature["classification"] != "no-finding"
                or signature["evidence_status"] != "valid"
                or signature["invalid_edges"] != 0
                or signature["selected_source_is_canonical"] is not True
                or signature["compatible_carriers"] < 1
            ):
                raise EvidenceError(
                    f"{context} review merge signature is not clean for {case}"
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
        if not self.raw:
            raise EvidenceError("JSONL stream is empty")
        if b"\r" in self.raw:
            raise EvidenceError("JSONL stream contains CR bytes")
        if not self.raw.endswith(b"\n"):
            raise EvidenceError("JSONL stream has no final LF")
        self.objects = []
        for number, line in enumerate(self.raw[:-1].split(b"\n"), start=1):
            if not line:
                raise EvidenceError(f"blank JSONL line {number}")
            value = load_json(line)
            if canonical_bytes(value) != line + b"\n":
                raise EvidenceError(
                    f"JSONL line {number} is not canonical sorted-key JSON+LF"
                )
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
        failure_scenarios = {
            row.get("scenario")
            for row in self.summary.get("failures", [])
            if isinstance(row, dict) and "scenario" in row
        }
        failure_controls = {
            row.get("control")
            for row in self.summary.get("failures", [])
            if isinstance(row, dict) and "control" in row
        }
        observed_controls = sum(
            row.get("status") == "OBSERVED_RED"
            for row in self.controls.values()
        )
        alias_rows = self.aliases["scenario_alias_inventory"]
        observed_aliases = sum(
            row.get("status") == "PASS" for row in alias_rows
        )
        recomputed_summary = (
            "PASS"
            if (
                not self.summary.get("failures")
                and observed_controls == len(CONTROL_IDS)
                and observed_aliases == len(ALIAS_IDS)
            )
            else "FAIL"
        )
        expected = {
            "summary": recomputed_summary,
            "passed": len(SCENARIO_IDS) - len(failure_scenarios),
            "total": len(SCENARIO_IDS),
            "controls_passed": observed_controls,
            "controls_total": len(CONTROL_IDS),
            "aliases_passed": observed_aliases,
            "aliases_total": len(ALIAS_IDS),
            "r17_parent_permutation": "PASS",
            "r18_origin_parent_permutation": "PASS",
            "r19_review_merge_parent_permutation": "PASS",
        }
        for key, value in expected.items():
            if self.summary.get(key) != value:
                raise EvidenceError(f"stream summary {key} is not {value!r}")
        if failure_controls - set(self.controls):
            raise EvidenceError("stream summary names an unknown failed control")
        self._validate_aliases()
        validate_permutation_record(self.permutation, "stream permutation")

    def _validate_aliases(self):
        contracts = {
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
        by_alias = {
            row["alias"]: row
            for row in self.aliases["scenario_alias_inventory"]
        }
        if set(by_alias) != set(contracts):
            raise EvidenceError("alias inventory differs from static contracts")
        for alias, expected in contracts.items():
            source = self.scenarios[expected["scenario"]]
            observed = {
                "scenario": source["scenario"],
                "classification": source["classification"],
                "evidence_status": source["evidence_verdict"]["status"],
                "event_mode": source["event_mode"],
                "finding": any(x["finding"] for x in source["actions"]),
                "authority_edges": len(source["authority_edges"]),
                "invalid_authority_edges": sum(
                    edge["problem"] is not None
                    for edge in source["authority_edges"]
                ),
                "propagation_edges": len(source["propagation_edges"]),
            }
            row = by_alias[alias]
            if row != {
                "alias": alias,
                "maps_to": expected["scenario"],
                "expected": expected,
                "observed": observed,
                "status": "PASS" if observed == expected else "FAIL",
            }:
                raise EvidenceError(
                    f"alias {alias} differs from recomputed scenario projection"
                )

    def semantic_bytes(self):
        return b"".join(canonical_bytes(normalized_record(x)) for x in self.objects)


def trusted_git_executable() -> Path:
    """Select Git from fixed system prefixes, never from caller PATH."""
    candidates = (
        Path("/opt/homebrew/bin/git"),
        Path("/usr/local/bin/git"),
        Path("/usr/bin/git"),
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise EvidenceError(
        "isolated replay found no Git executable in the fixed trusted paths"
    )


def internal_replay_stream() -> Stream:
    """Run the sibling prototype without caller Python or Git startup state."""
    prototype = Path(__file__).resolve().with_name("prototype.py")
    git_executable = trusted_git_executable()
    git_directory = str(git_executable.parent)
    with tempfile.TemporaryDirectory(prefix="production-contract-audit-replay-") as raw:
        scratch = Path(raw)
        isolated_home = scratch / "home"
        isolated_home.mkdir()
        environment = {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "HOME": str(isolated_home),
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": os.pathsep.join((git_directory, os.defpath)),
            "TZ": "UTC",
            "XDG_CONFIG_HOME": str(isolated_home / "xdg"),
        }
        git_smoke = subprocess.run(
            ["git", "--version"],
            check=False,
            env=environment,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            timeout=10,
        )
        if git_smoke.returncode != 0:
            diagnostic = git_smoke.stderr.decode(
                "utf-8", errors="replace"
            ).strip()
            raise EvidenceError(
                "isolated replay Git smoke test failed"
                + (f": {diagnostic}" if diagnostic else "")
            )
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                "-X",
                "utf8",
                str(prototype),
                "--self-test",
                "--fixtures-dir",
                str(scratch / "fixtures"),
            ],
            check=False,
            env=environment,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            timeout=900,
        )
    if completed.returncode != 0:
        diagnostic = completed.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceError(
            "fresh internal prototype replay failed"
            + (f": {diagnostic}" if diagnostic else "")
        )
    return Stream.from_bytes(completed.stdout, "<fresh-internal-replay>")


def require_fresh_replay(
    supplied: Stream,
    fresh: Stream,
    comparison: Stream | None = None,
):
    if supplied.raw != fresh.raw:
        raise EvidenceError(
            "generation input differs byte-for-byte from fresh internal replay"
        )
    if comparison is not None and comparison.raw != fresh.raw:
        raise EvidenceError(
            "generation comparison differs byte-for-byte from fresh internal replay"
        )


MAX_EXISTING_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_PAIR_JOURNAL_BYTES = 8 * 1024


def publish_call_result(target: list, callback) -> None:
    """Append a returned resource before control reaches Python bytecode."""
    tuple(map(target.append, map(operator.call, (callback,))))


class PublishedDescriptor:
    """One raw fd published before Python resumes after its factory call."""

    def __init__(self):
        self._slot: list[int] = []

    @property
    def descriptor(self) -> int:
        if len(self._slot) != 1:
            raise EvidenceError("descriptor ownership is not open")
        return self._slot[0]

    def acquire(self, callback) -> int:
        if self._slot:
            raise EvidenceError("descriptor ownership is already open")
        # Both map iterators and tuple consumption execute in C.  The returned
        # fd is appended to the pre-existing slot before Python can observe a
        # post-CALL/pre-STORE_FAST cancellation boundary.
        publish_call_result(self._slot, callback)
        return self.descriptor

    def close(self) -> None:
        descriptor = self.descriptor
        # Clear the only retryable token and invoke close in one C-consumed
        # callback sequence.  A normal return is closed; any throwable is
        # ambiguous and the numeric fd is never retried after possible reuse.
        operations = (
            functools.partial(self._slot.clear),
            functools.partial(os.close, descriptor),
        )
        tuple(map(operator.call, operations))

    def __del__(self):
        # Last-resort cleanup if cancellation interrupts a caller before it
        # enters its explicit close block.  Explicit close always consumes the
        # slot first, so this cannot retry an ambiguous numeric descriptor.
        if not self._slot:
            return
        try:
            descriptor = self._slot[0]
            operations = (
                functools.partial(self._slot.clear),
                functools.partial(os.close, descriptor),
            )
            tuple(map(operator.call, operations))
        except BaseException:
            pass


class PublishedTemporaryFile:
    """One mkstemp result published before Python resumes after creation."""

    def __init__(self):
        self._slot: list[tuple[int, str]] = []

    @property
    def resource(self) -> tuple[int, str]:
        if len(self._slot) != 1:
            raise EvidenceError("temporary-file ownership is not open")
        value = self._slot[0]
        if (
            not isinstance(value, tuple)
            or len(value) != 2
            or type(value[0]) is not int
            or type(value[1]) is not str
        ):
            raise EvidenceError("temporary-file factory returned an invalid resource")
        return value

    @property
    def descriptor(self) -> int:
        return self.resource[0]

    @property
    def raw_path(self) -> str:
        return self.resource[1]

    def acquire(self, callback) -> tuple[int, str]:
        if self._slot:
            raise EvidenceError("temporary-file ownership is already open")
        publish_call_result(self._slot, callback)
        return self.resource

    def close(self) -> None:
        descriptor = self.descriptor
        operations = (
            functools.partial(self._slot.clear),
            functools.partial(os.close, descriptor),
        )
        tuple(map(operator.call, operations))

    def __del__(self):
        if not self._slot:
            return
        try:
            descriptor = self.descriptor
            operations = (
                functools.partial(self._slot.clear),
                functools.partial(os.close, descriptor),
            )
            tuple(map(operator.call, operations))
        except BaseException:
            pass


def read_bounded_regular(
    target: Path,
    label: str,
    limit: int,
    missing_ok: bool,
    *,
    checkpoint=None,
) -> tuple[bytes, int, dict[str, int]] | None:
    """Read one stable regular-file identity through one bounded descriptor."""
    required_flags = ("O_NONBLOCK", "O_NOFOLLOW", "O_CLOEXEC")
    if any(
        not hasattr(os, flag) or getattr(os, flag) == 0
        for flag in required_flags
    ):
        raise EvidenceError(
            f"{label} requires O_NONBLOCK, O_NOFOLLOW, and O_CLOEXEC"
        )
    if type(limit) is not int or limit < 0:
        raise EvidenceError(f"{label} has an invalid byte bound")

    def notify(stage, descriptor=None):
        if checkpoint is not None:
            checkpoint(stage, target, descriptor)

    def fingerprint(value):
        return {
            "mode": value.st_mode,
            "dev": value.st_dev,
            "ino": value.st_ino,
            "size": value.st_size,
            "mtime_ns": value.st_mtime_ns,
            "ctime_ns": value.st_ctime_ns,
        }

    try:
        observed = target.lstat()
    except FileNotFoundError:
        if missing_ok:
            return None
        raise EvidenceError(f"{label} is missing")
    except OSError as error:
        raise EvidenceError(f"{label} is unavailable: {error}") from error
    notify("after-lstat")
    if not stat.S_ISREG(observed.st_mode):
        raise EvidenceError(f"{label} must be a non-symlink regular file")
    if observed.st_size > limit:
        raise EvidenceError(
            f"{label} exceeds the {limit}-byte bound"
        )
    flags = (
        os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    ownership = PublishedDescriptor()
    primary_error = None
    result = None
    try:
        try:
            descriptor = ownership.acquire(
                functools.partial(os.open, target, flags)
            )
        except OSError as error:
            raise EvidenceError(
                f"{label} could not be opened safely: {error}"
            ) from error
        notify("after-open", descriptor)
        before = os.fstat(descriptor)
        notify("after-pre-fstat", descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise EvidenceError(f"{label} must be a non-symlink regular file")
        if fingerprint(before) != fingerprint(observed):
            raise EvidenceError(f"{label} changed during bounded validation")
        if before.st_size > limit:
            raise EvidenceError(f"{label} exceeds the {limit}-byte bound")
        chunks = []
        remaining = limit + 1
        first_chunk = True
        while remaining:
            try:
                chunk = os.read(
                    descriptor, min(1024 * 1024, remaining)
                )
            except BlockingIOError as error:
                raise EvidenceError(
                    f"{label} produced a nonblocking read refusal"
                ) from error
            if first_chunk:
                notify("after-first-chunk", descriptor)
                first_chunk = False
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > limit:
            raise EvidenceError(f"{label} exceeds the {limit}-byte bound")
        notify("before-post-fstat", descriptor)
        after = os.fstat(descriptor)
        if fingerprint(after) != fingerprint(before):
            raise EvidenceError(f"{label} changed during bounded read")
        try:
            final_path = target.lstat()
        except OSError as error:
            raise EvidenceError(f"{label} changed during bounded read") from error
        if fingerprint(final_path) != fingerprint(before):
            raise EvidenceError(f"{label} changed during bounded read")
        if len(payload) != before.st_size:
            raise EvidenceError(f"{label} changed during bounded read")
        result = (
            payload,
            stat.S_IMODE(before.st_mode),
            fingerprint(before),
        )
    except BaseException as error:
        primary_error = error
    close_error = None
    if ownership._slot:
        try:
            ownership.close()
        except BaseException as error:
            close_error = error
    cancellation = next(
        (
            error
            for error in (primary_error, close_error)
            if isinstance(error, (KeyboardInterrupt, SystemExit))
        ),
        None,
    )
    if cancellation is not None:
        raise cancellation
    if close_error is not None:
        raise EvidenceError(
            f"{label} descriptor close state is unknown: "
            f"{type(close_error).__name__}"
        ) from close_error
    if primary_error is not None:
        raise primary_error
    return result


def stage_artifact_bytes(
    target: Path,
    payload: bytes,
    label: str,
    *,
    mode: int = 0o644,
    checkpoint=None,
) -> Path:
    """Write and fsync one same-directory staging file without publication."""
    ownership = PublishedTemporaryFile()
    staged = None
    failures: list[BaseException] = []
    try:
        descriptor, raw_path = ownership.acquire(
            functools.partial(
                tempfile.mkstemp,
                dir=target.parent,
                prefix=f".{target.name}.{label}.",
                suffix=".tmp",
            )
        )
        staged = Path(raw_path)
        if checkpoint is not None:
            checkpoint("after-mkstemp-publication", staged, descriptor)
        os.fchmod(descriptor, mode)
        view = memoryview(payload)
        written = 0
        while written < len(view):
            count = os.write(descriptor, view[written:])
            if count <= 0:
                raise OSError("staging descriptor made no write progress")
            written += count
        os.fsync(descriptor)
    except BaseException as error:
        failures.append(error)
    if staged is None and ownership._slot:
        try:
            staged = Path(ownership.raw_path)
        except BaseException as error:
            failures.append(error)
    if ownership._slot:
        try:
            # Clear the sole fd token before the only close attempt.  A
            # throwable is ambiguous and can never trigger an unsafe retry.
            ownership.close()
        except BaseException as error:
            failures.append(error)
    if failures:
        if staged is not None:
            try:
                staged.unlink(missing_ok=True)
            except BaseException as error:
                failures.append(error)
        cancellation = next(
            (
                error for error in failures
                if isinstance(error, (KeyboardInterrupt, SystemExit))
            ),
            None,
        )
        if cancellation is not None:
            secondary = [
                f"{type(error).__name__} during staging cleanup"
                for error in failures
                if error is not cancellation
            ]
            if secondary:
                cancellation.add_note("; ".join(dict.fromkeys(secondary)))
            raise cancellation
        raise EvidenceError(
            f"{label} staging failed: "
            + ", ".join(
                dict.fromkeys(type(error).__name__ for error in failures)
            )
        ) from failures[0]
    if staged is None:
        raise EvidenceError(f"{label} staging path was not published")
    return staged


PAIR_JOURNAL_SCHEMA = "production-contract-artifact-pair-journal/v1"
PAIR_JOURNAL_NAME = ".production-contract-artifact-pair-journal.json"


def fsync_directory(directory: Path):
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_CLOEXEC"):
        raise EvidenceError("directory fsync requires O_DIRECTORY and O_CLOEXEC")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    ownership = PublishedDescriptor()
    primary_error = None
    try:
        descriptor = ownership.acquire(
            functools.partial(os.open, directory, flags)
        )
        os.fsync(descriptor)
    except BaseException as error:
        primary_error = error
    close_error = None
    if ownership._slot:
        try:
            ownership.close()
        except BaseException as error:
            close_error = error
    cancellation = next(
        (
            error
            for error in (primary_error, close_error)
            if isinstance(error, (KeyboardInterrupt, SystemExit))
        ),
        None,
    )
    if cancellation is not None:
        raise cancellation
    if close_error is not None:
        raise EvidenceError(
            "directory fsync descriptor close state is unknown: "
            + type(close_error).__name__
        ) from close_error
    if primary_error is not None:
        raise primary_error


def artifact_pair_journal_path(
    evidence_path: Path, readme_path: Path
) -> Path:
    if evidence_path.parent.resolve() != readme_path.parent.resolve():
        raise EvidenceError(
            "artifact pair targets must share one journal directory"
        )
    return evidence_path.parent / PAIR_JOURNAL_NAME


def bounded_artifact_digest(path: Path, label: str) -> str | None:
    prior = read_bounded_regular(
        path,
        label,
        MAX_EXISTING_ARTIFACT_BYTES,
        True,
    )
    return digest_bytes(prior[0]) if prior is not None else None


def path_entry_exists(path: Path) -> bool:
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


@contextlib.contextmanager
def artifact_pair_publication_lock(directory: Path, *, checkpoint=None):
    """Serialize publishers on the stable directory inode without lock debris."""
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_CLOEXEC"):
        raise EvidenceError("publication lock requires O_DIRECTORY and O_CLOEXEC")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    ownership = PublishedDescriptor()
    primary_error = None
    boundary_error = None
    close_error = None
    try:
        descriptor = ownership.acquire(
            functools.partial(os.open, directory, flags)
        )
        if checkpoint is not None:
            checkpoint("after-open-publication", descriptor)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise EvidenceError(
                "artifact pair generation already active in this directory"
            ) from error
        yield descriptor
    except BaseException as error:
        primary_error = error
    if ownership._slot:
        if checkpoint is not None:
            try:
                checkpoint("before-close", ownership.descriptor)
            except BaseException as error:
                boundary_error = error
        try:
            # Closing is the single lock-release operation.  There is no
            # cancellation-visible Python opcode between token consumption
            # and fd close, and no separate unlock to leave half-finished.
            ownership.close()
        except BaseException as error:
            close_error = error
    cancellation = next(
        (
            error
            for error in (primary_error, boundary_error, close_error)
            if isinstance(error, (KeyboardInterrupt, SystemExit))
        ),
        None,
    )
    if cancellation is not None:
        raise cancellation
    if close_error is not None:
        raise EvidenceError(
            "publication lock descriptor close state is unknown: "
            + type(close_error).__name__
        ) from close_error
    if boundary_error is not None:
        raise boundary_error
    if primary_error is not None:
        raise primary_error


def validate_pair_journal(
    journal: dict, evidence_path: Path, readme_path: Path
) -> list[dict]:
    if not isinstance(journal, dict) or set(journal) != {"schema", "targets"}:
        raise EvidenceError("artifact pair recovery journal shape changed")
    if journal["schema"] != PAIR_JOURNAL_SCHEMA:
        raise EvidenceError("artifact pair recovery journal schema changed")
    targets = journal["targets"]
    if not isinstance(targets, list) or len(targets) != 2:
        raise EvidenceError("artifact pair recovery journal target count changed")
    expected_names = [evidence_path.name, readme_path.name]
    for index, (entry, expected_name) in enumerate(
        zip(targets, expected_names, strict=True)
    ):
        if not isinstance(entry, dict) or set(entry) != {
            "backup", "existed", "new", "old_sha256", "target"
        }:
            raise EvidenceError(
                f"artifact pair recovery journal target {index} shape changed"
            )
        names = [entry["new"]]
        if entry["backup"] is not None:
            names.append(entry["backup"])
        if (
            entry["target"] != expected_name
            or not isinstance(entry["existed"], bool)
            or not isinstance(entry["new"], str)
            or not entry["new"].startswith(f".{expected_name}.new.")
            or not entry["new"].endswith(".tmp")
            or (
                entry["existed"]
                and (
                    not isinstance(entry["backup"], str)
                    or not entry["backup"].startswith(
                        f".{expected_name}.old."
                    )
                    or not entry["backup"].endswith(".tmp")
                    or not isinstance(entry["old_sha256"], str)
                    or len(entry["old_sha256"]) != 71
                    or not entry["old_sha256"].startswith("sha256:")
                    or any(
                        character not in "0123456789abcdef"
                        for character in entry["old_sha256"][7:]
                    )
                )
            )
            or (
                not entry["existed"]
                and (
                    entry["backup"] is not None
                    or entry["old_sha256"] is not None
                )
            )
            or any(
                not isinstance(name, str)
                or Path(name).name != name
                or "/" in name
                or "\\" in name
                for name in names
            )
        ):
            raise EvidenceError(
                f"artifact pair recovery journal target {index} is invalid"
            )
    return targets


def recover_generated_artifact_pair(
    evidence_path: Path, readme_path: Path
) -> bool:
    """Restore the old pair from a prior incomplete publication journal."""
    journal_path = artifact_pair_journal_path(evidence_path, readme_path)
    try:
        journal_record = read_bounded_regular(
            journal_path,
            "artifact pair recovery journal",
            MAX_PAIR_JOURNAL_BYTES,
            True,
        )
    except (EvidenceError, OSError) as error:
        raise EvidenceError(
            "artifact pair recovery incomplete; journal and recoverable "
            f"backups retained: {error}"
        ) from error
    if journal_record is None:
        return False
    try:
        raw = journal_record[0]
        journal = load_json(raw)
        if canonical_bytes(journal) != raw:
            raise EvidenceError(
                "artifact pair recovery journal is not canonical JSON+LF"
            )
        entries = validate_pair_journal(
            journal, evidence_path, readme_path
        )
        directory = journal_path.parent
        for entry, target in zip(
            entries, (evidence_path, readme_path), strict=True
        ):
            if entry["existed"]:
                try:
                    current_digest = bounded_artifact_digest(
                        target,
                        f"current recovery target {target.name}",
                    )
                except EvidenceError:
                    # An untrusted crash-era replacement that is special,
                    # race-changed, or oversized is never read to completion;
                    # the verified bounded backup remains recovery authority.
                    current_digest = None
                if current_digest == entry["old_sha256"]:
                    continue
                backup = directory / entry["backup"]
                backup_record = read_bounded_regular(
                    backup,
                    f"artifact pair recovery backup for {target.name}",
                    MAX_EXISTING_ARTIFACT_BYTES,
                    False,
                )
                backup_digest = digest_bytes(backup_record[0])
                if backup_digest != entry["old_sha256"]:
                    raise EvidenceError(
                        f"artifact pair recovery backup digest failed for {target.name}"
                    )
                restore_stage = stage_artifact_bytes(
                    target,
                    backup_record[0],
                    "restore",
                    mode=backup_record[1],
                )
                os.replace(restore_stage, target)
                restored_record = read_bounded_regular(
                    target,
                    f"restored artifact pair target {target.name}",
                    MAX_EXISTING_ARTIFACT_BYTES,
                    False,
                )
                if (
                    restored_record[0] != backup_record[0]
                    or digest_bytes(restored_record[0])
                    != entry["old_sha256"]
                ):
                    raise EvidenceError(
                        f"artifact pair recovery digest failed for {target.name}"
                    )
            else:
                target.unlink(missing_ok=True)
                if path_entry_exists(target):
                    raise EvidenceError(
                        f"artifact pair recovery could not remove {target.name}"
                    )
        fsync_directory(directory)
        journal_path.unlink()
        fsync_directory(directory)
        for entry in entries:
            for name in (entry["new"], entry["backup"]):
                if name is not None:
                    with contextlib.suppress(OSError):
                        (directory / name).unlink()
        return True
    except (EvidenceError, OSError) as error:
        raise EvidenceError(
            "artifact pair recovery incomplete; journal and recoverable "
            f"backups retained: {error}"
        ) from error


def publish_generated_artifacts(
    supplied: Stream,
    fresh: Stream,
    evidence_path: Path,
    readme_path: Path,
    *,
    comparison: Stream | None = None,
) -> dict:
    """Publish a serialized, journaled pair or retain recovery authority."""
    journal_path = artifact_pair_journal_path(evidence_path, readme_path)
    with artifact_pair_publication_lock(journal_path.parent):
        return publish_generated_artifacts_locked(
            supplied,
            fresh,
            evidence_path,
            readme_path,
            comparison=comparison,
        )


def publish_generated_artifacts_locked(
    supplied: Stream,
    fresh: Stream,
    evidence_path: Path,
    readme_path: Path,
    *,
    comparison: Stream | None = None,
) -> dict:
    """Validate/stage while the caller owns the directory publication lock."""
    recover_generated_artifact_pair(evidence_path, readme_path)
    require_fresh_replay(supplied, fresh, comparison)
    expected = manifest_from_stream(fresh)
    targets = (
        (evidence_path, canonical_bytes(expected)),
        (readme_path, render_readme(expected)),
    )
    prior_artifacts = tuple(
        read_bounded_regular(
            target,
            f"existing artifact target {target.name}",
            MAX_EXISTING_ARTIFACT_BYTES,
            True,
        )
        for target, _payload in targets
    )
    staged: list[Path] = []
    backups: list[tuple[bool, Path | None]] = []
    journal_path = artifact_pair_journal_path(evidence_path, readme_path)
    journal_stage = None
    try:
        for (target, payload), prior in zip(
            targets, prior_artifacts, strict=True
        ):
            staged.append(
                stage_artifact_bytes(
                    target,
                    payload,
                    "new",
                    mode=prior[1] if prior is not None else 0o644,
                )
            )
        for (target, _payload), prior in zip(
            targets, prior_artifacts, strict=True
        ):
            backups.append(
                (
                    prior is not None,
                    stage_artifact_bytes(
                        target, prior[0], "old", mode=prior[1]
                    )
                    if prior is not None
                    else None,
                )
            )
        journal = {
            "schema": PAIR_JOURNAL_SCHEMA,
            "targets": [
                {
                    "backup": backup.name if backup is not None else None,
                    "existed": existed,
                    "new": staged_path.name,
                    "old_sha256": (
                        digest_bytes(prior[0])
                        if prior is not None
                        else None
                    ),
                    "target": target.name,
                }
                for staged_path, (target, _payload), (existed, backup), prior
                in zip(
                    staged,
                    targets,
                    backups,
                    prior_artifacts,
                    strict=True,
                )
            ],
        }
        journal_bytes = canonical_bytes(journal)
        if len(journal_bytes) > MAX_PAIR_JOURNAL_BYTES:
            raise EvidenceError(
                "artifact pair recovery journal exceeds its explicit bound"
            )
        journal_stage = stage_artifact_bytes(
            journal_path, journal_bytes, "new"
        )
        os.replace(journal_stage, journal_path)
        journal_stage = None
        persisted_journal = read_bounded_regular(
            journal_path,
            "new artifact pair recovery journal",
            MAX_PAIR_JOURNAL_BYTES,
            False,
        )
        if persisted_journal[0] != journal_bytes:
            raise EvidenceError(
                "new artifact pair recovery journal bytes changed"
            )
        fsync_directory(journal_path.parent)
    except BaseException as error:
        if not path_entry_exists(journal_path):
            for path in [
                *staged,
                *(item[1] for item in backups),
                journal_stage,
            ]:
                if path is not None:
                    with contextlib.suppress(OSError):
                        path.unlink()
            detail = ""
        else:
            detail = "; recovery journal and staged pair retained"
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        raise EvidenceError(
            f"artifact pair staging failed before publication: {error}{detail}"
        ) from error

    try:
        for staged_path, (target, _payload) in zip(
            staged, targets, strict=True
        ):
            os.replace(staged_path, target)
        for target, intended_payload in targets:
            published = read_bounded_regular(
                target,
                f"newly published artifact target {target.name}",
                MAX_EXISTING_ARTIFACT_BYTES,
                False,
            )
            if published[0] != intended_payload:
                raise EvidenceError(
                    f"newly published artifact bytes changed for {target.name}"
                )
    except BaseException as error:
        try:
            recover_generated_artifact_pair(evidence_path, readme_path)
            detail = "; old pair restored and recovery journal cleared"
        except EvidenceError as rollback_error:
            detail = f"; {rollback_error}"
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            if detail:
                error.add_note(detail.lstrip("; "))
            raise
        raise EvidenceError(
            f"artifact pair publication failed: {error}{detail}"
        ) from error
    fsync_directory(journal_path.parent)
    journal_path.unlink()
    fsync_directory(journal_path.parent)
    for path in [*staged, *(item[1] for item in backups)]:
        if path is not None:
            with contextlib.suppress(OSError):
                path.unlink()
    return expected


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
    elif row["control"] == "leak-object-database-pipes":
        observation = {
            **row["object_database_observation"],
            "kind": "object-database-descriptor-lifecycle",
        }
    elif row["control"] == "event-adapter-cli-entrypoint":
        observation = {
            **row["event_adapter_cli_observation"],
            "kind": "immutable-event-adapter-cli",
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
                "git_processes", "git_process_attempts", "graph_buffered_bytes",
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
            "git_process_attempts": p22["metrics"][
                "git_process_attempts"
            ],
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
        "R18-U-review-compatible-merge",
        "R18-U-review-compatible-merge-reversed",
        "R18-U-review-compatible-source-low",
        "R18-U-review-compatible-source-low-reversed",
        "R18-U-review-compatible-source-high",
        "R18-U-review-compatible-source-high-reversed",
        "R18-U-review-duplicate-parent-header",
        "R18-U-review-three-carrying-parents",
        "R18-U-review-two-valid-sources",
        "R18-U-review-incompatible-carrier",
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
    duplicate_row = stream.scenarios[
        "R18-U-review-duplicate-parent-header"
    ]
    duplicate_landmarks = duplicate_row["details"]["landmarks"]
    duplicate_merge = duplicate_landmarks["merge"]
    duplicate_edges = [
        edge
        for proof in cases[
            "R18-U-review-duplicate-parent-header"
        ]["origin_proofs"]
        for edge in proof["edges"]
        if edge["child"] == duplicate_merge
    ]
    bound_controls = (
        "endpoint-only-origin-equality",
        "skip-origin-birth-uniqueness",
        "skip-origin-post-birth-absence",
        "skip-origin-endpoint-non-regression",
        "reject-all-origin-invalid-carriers",
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
        "duplicate_parent_header": {
            "compatible_carrier_count": sum(
                edge["role"] == "compatible-carrier"
                for edge in duplicate_edges
            ),
            "fsck_returncode": duplicate_landmarks["fsck_returncode"],
            "logical_parent_count": len(
                duplicate_landmarks["logical_parent_oids"]
            ),
            "raw_parent_header_count": len(
                duplicate_landmarks["raw_parent_headers"]
            ),
            "source_count": sum(
                edge["role"] == "source" for edge in duplicate_edges
            ),
        },
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
        "review_merge_parent_permutations": stream.permutation[
            "r19_review_merge_parent_permutations"
        ],
    }


def generation_contract_projection():
    git_executable = trusted_git_executable()
    return {
        "artifact_reader": {
            "artifact_limit_bytes": MAX_EXISTING_ARTIFACT_BYTES,
            "journal_limit_bytes": MAX_PAIR_JOURNAL_BYTES,
            "required_flags": ["O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"],
            "stable_fields": [
                "type", "dev", "ino", "size", "mtime_ns", "ctime_ns"
            ],
        },
        "caller_rows_authoritative": False,
        "comparison_requires_exact_bytes": True,
        "fresh_internal_replay": True,
        "fresh_replay_environment": (
            "isolated -I/-S Python with an explicit Git/Python environment "
            "allowlist"
        ),
        "fixture_date": "2026-09-02",
        "trusted_git": {
            "path": str(git_executable),
            "sha256": digest_bytes(git_executable.read_bytes()),
        },
        "pre_generation_damage_cases": [
            "pre-generation-nonexistent-OID",
            "pre-generation-contradictory-result",
            "pre-generation-CRLF",
            "pre-generation-missing-final-LF",
            "pre-generation-duplicate-key",
            "pre-generation-unsorted-json",
        ],
        "publication_order": (
            "parse canonical raw JSONL, recompute aliases/permutations/summary, "
            "compare exact fresh bytes, and stage/fsync both files before "
            "namespace publication"
        ),
        "publication_pair_rollback": True,
        "publication_crash_boundary": (
            "portable filesystems cannot atomically exchange two paths; an "
            "unreported process or machine crash can temporarily expose a "
            "mixed pair, but the retained fsynced journal/backups make the "
            "next locked invocation restore or refuse it; hostile replacement "
            "of the parent directory inode is outside this POC"
        ),
        "publication_requires_exact_bytes": True,
        "raw_jsonl": {
            "compact_sorted_json": True,
            "duplicate_keys_rejected": True,
            "exactly_one_LF_per_record": True,
            "final_LF_required": True,
            "CR_rejected": True,
        },
        "same_file_stream_and_compare_is_not_a_bypass": True,
        "sentinels_unchanged_on_rejection": True,
    }


def event_workflow_projection(stream):
    ids = [name for name in SCENARIO_IDS if name.startswith("R19-WF-")]
    cases = {}
    for name in ids:
        row = stream.scenarios[name]
        details = row["details"]
        action = next(
            (item for item in row["actions"] if item["origin_proofs"]),
            None,
        )
        cases[name] = {
            "adapter": row["event_adapter"],
            "audit_exit": row["audit_exit"],
            "classification": row["classification"],
            "finding": bool(action and action["finding"]),
            "non_fast_forward": details["workflow_non_fast_forward"],
            "reason_code": action["reason_code"] if action else None,
            "record_sha256": record_digest(normalized_record(row)),
            "transport": details["workflow_transport"],
            "workflow_attack": details["workflow_attack"],
            "workflow_failure": details["workflow_failure"],
        }
    return {
        "cases": cases,
        "claim": (
            "immutable event endpoint extraction and typed Strategy U make no "
            "claim about provider authority, user intent, or github.sha"
        ),
        "cli_control": control_projection(
            stream.controls["event-adapter-cli-entrypoint"]
        ),
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
        "evidence_generation": generation_contract_projection(),
        "evidence_supersession": SUPERSEDED_EVIDENCE,
        "immutable_event_workflows": event_workflow_projection(stream),
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
        "object_database_lifecycle": control_projection(
            stream.controls["leak-object-database-pipes"]
        ),
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
            "r19_review_merge_parent_permutation": stream.summary[
                "r19_review_merge_parent_permutation"
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
        "r19_review_merge_parent_permutation",
        "scenario_passed", "scenario_total", "status",
    ), "summary")
    summary = manifest["summary"]
    require_digest(summary["canonical_stream_sha256"], "summary stream digest")
    counts = {
        "aliases_passed": len(ALIAS_IDS), "aliases_total": len(ALIAS_IDS),
        "controls_passed": len(CONTROL_IDS), "controls_total": len(CONTROL_IDS),
        "r17_parent_permutation": "PASS",
        "r18_origin_parent_permutation": "PASS",
        "r19_review_merge_parent_permutation": "PASS",
        "scenario_passed": len(SCENARIO_IDS), "scenario_total": len(SCENARIO_IDS),
        "status": "PASS",
    }
    for key, expected in counts.items():
        if summary[key] != expected:
            raise EvidenceError(f"summary {key} is not {expected!r}")
        if key not in {
            "status", "r17_parent_permutation",
            "r18_origin_parent_permutation",
            "r19_review_merge_parent_permutation",
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
        elif row["id"] == "event-adapter-cli-entrypoint":
            observation = row["observation"]
            require_keys(
                observation,
                (
                    "cases", "entrypoint", "execution_seam",
                    "importable_api", "kind", "payload_grammar",
                    "typed_cli_inputs",
                ),
                f"{context}.observation",
            )
            if (
                observation["kind"] != "immutable-event-adapter-cli"
                or observation["entrypoint"]
                != (
                    "prototype.py --repo ROOT --event-kind KIND "
                    "--event-payload EVENT.json"
                )
                or observation["payload_grammar"]
                != {
                    "local": ["old", "new"],
                    "pre-push": ["old", "new"],
                    "pull-request-synchronize": [
                        "before", "after", "pull_request.head.sha"
                    ],
                    "push": ["before", "after"],
                }
                or observation["importable_api"]
                != {
                    "endpoint_derivation": (
                        "event_endpoints(event_kind: str, payload: "
                        "Mapping[str, Any]) -> EventEndpoints"
                    ),
                    "typed_U_audit": (
                        "audit_event(root: Path, event_kind: str, payload: "
                        "Mapping[str, Any], *, git_runner: TrustedGitRunner, "
                        "budget_limit: int | None = None, transaction: "
                        "Callable[[], ContextManager[GitSpawnObserver | None]] "
                        "| None = None) -> dict"
                    ),
                }
            ):
                raise EvidenceError(f"{context} event adapter contract changed")
            cases = observation["cases"]
            require_keys(
                cases, ("blocking", "clean", "unavailable"),
                f"{context}.observation.cases",
            )
            expected_cases = {
                "blocking": ("accepted", "blocking-finding", 1),
                "clean": ("accepted", "no-finding", 0),
                "unavailable": ("coverage-unavailable", "unreadable", 2),
            }
            for name, item in cases.items():
                require_keys(
                    item,
                    (
                        "adapter_status", "classification", "exit",
                        "stdout_canonical", "typed_origin_strategy",
                        "typed_results_equal",
                    ),
                    f"{context}.observation.cases.{name}",
                )
                if (
                    (
                        item["adapter_status"],
                        item["classification"],
                        item["exit"],
                    )
                    != expected_cases[name]
                    or item["stdout_canonical"] is not True
                    or item["typed_origin_strategy"] != "U"
                    or item["typed_results_equal"] is not True
                ):
                    raise EvidenceError(
                        f"{context} event CLI/import result contract changed"
                    )
            typed_cli = observation["typed_cli_inputs"]
            require_keys(
                typed_cli,
                ("non-mapping-payload", "unsupported-event-kind"),
                f"{context}.observation.typed_cli_inputs",
            )
            for name, item in typed_cli.items():
                if item != {
                    "adapter_status": "coverage-unavailable",
                    "audit_exit": 2,
                    "classification": "unreadable",
                    "stdout_canonical": True,
                }:
                    raise EvidenceError(
                        f"{context} typed CLI input {name} escaped JSON"
                    )

            seam = observation["execution_seam"]
            require_keys(
                seam,
                (
                    "cache_isolation", "duplicate_module_concurrency",
                    "fixture_date_replay", "hostile_ambient_subprocess",
                    "identical_endpoint_rejections", "invalid",
                    "invalid_budget_rejections", "invalid_runtime_inputs",
                    "nested_reentry", "noncallable_runner",
                    "observer_throwables", "runner_cancellation",
                    "runner_ordinal_failures", "runner_throwables",
                    "same_module_concurrency", "static_contract",
                    "session_setup_cancellation_boundaries",
                    "spawn_construction_cancellation_boundaries",
                    "trace_cancellation_boundaries",
                    "transaction_cancellations",
                    "transaction_throwables", "truthy_exit_ignored",
                    "valid",
                ),
                f"{context}.execution_seam",
            )
            probe_keys = (
                "adapter_status", "after", "all_pids_reaped",
                "all_runner_pids_reaped",
                "attempts", "audit_exit", "before",
                "canonical_json_serializable", "caught", "classification",
                "commands_match", "created", "fd_delta", "lifecycle",
                "private_modules_leaked", "projected_event_kind", "reason",
                "runner_calls", "runner_created",
                "typed_origin_strategy",
            )

            def validate_probe(name, item):
                require_keys(
                    item, probe_keys,
                    f"{context}.execution_seam.{name}",
                )
                require_keys(
                    item["lifecycle"],
                    (
                        "enter", "exit", "exit_after_reap",
                        "exit_exception", "factory",
                    ),
                    f"{context}.execution_seam.{name}.lifecycle",
                )
                if item["private_modules_leaked"]:
                    raise EvidenceError(
                        f"{context} {name} leaked private reconciler modules"
                    )

            valid = seam["valid"]
            validate_probe("valid", valid)
            if (
                valid["adapter_status"] != "accepted"
                or valid["audit_exit"] != 0
                or valid["classification"] != "no-finding"
                or valid["created"] <= 0
                or valid["attempts"] != valid["created"]
                or valid["before"] != valid["created"]
                or valid["after"] != valid["created"]
                or valid["runner_calls"] != valid["created"]
                or valid["runner_created"] != valid["created"]
                or valid["commands_match"] is not True
                or valid["all_pids_reaped"] is not True
                or valid["all_runner_pids_reaped"] is not True
                or valid["canonical_json_serializable"] is not True
                or valid["fd_delta"] != 0
                or valid["projected_event_kind"] != "push"
                or valid["typed_origin_strategy"] != "U"
                or valid["lifecycle"]
                != {
                    "enter": 1,
                    "exit": 1,
                    "exit_after_reap": True,
                    "exit_exception": None,
                    "factory": 1,
                }
            ):
                raise EvidenceError(
                    f"{context} valid audit escaped session accounting"
                )

            def validate_rejection(name, item, reason):
                validate_probe(name, item)
                if (
                    item["adapter_status"] != "coverage-unavailable"
                    or item["audit_exit"] != 2
                    or item["classification"] != "unreadable"
                    or item["attempts"] != 0
                    or item["created"] != 0
                    or item["before"] != 0
                    or item["after"] != 0
                    or item["runner_calls"] != 0
                    or item["runner_created"] != 0
                    or item["canonical_json_serializable"] is not True
                    or item["lifecycle"]
                    != {
                        "enter": 0,
                        "exit": 0,
                        "exit_after_reap": None,
                        "exit_exception": None,
                        "factory": 0,
                    }
                    or item["typed_origin_strategy"] != "U"
                    or reason not in item["reason"]
                ):
                    raise EvidenceError(
                        f"{context} {name} entered execution or escaped "
                        "canonical JSON"
                    )

            validate_rejection(
                "invalid", seam["invalid"], "local.old is missing"
            )
            rejection_groups = (
                (
                    seam["identical_endpoint_rejections"],
                    {"local", "pre-push", "push",
                     "pull-request-synchronize"},
                    "O and N must be distinct Git OIDs",
                ),
                (
                    seam["invalid_budget_rejections"],
                    {"zero", "negative", "bool-false", "bool-true",
                     "float", "string"},
                    "budget must be an exact positive integer",
                ),
            )
            for group, expected_names, reason in rejection_groups:
                if set(group) != expected_names:
                    raise EvidenceError(
                        f"{context} rejection catalog changed"
                    )
                for name, item in group.items():
                    validate_rejection(name, item, reason)
            expected_runtime = {
                "event-kind-dict": "event kind must be a string",
                "event-kind-list": "event kind must be a string",
                "event-kind-plain-object": "event kind must be a string",
                "event-kind-unhashable-str-subclass": (
                    "event kind must be a string"
                ),
                "payload-int": "event payload must be a mapping",
                "payload-list": "event payload must be a mapping",
                "payload-none": "event payload must be a mapping",
            }
            if set(seam["invalid_runtime_inputs"]) != set(expected_runtime):
                raise EvidenceError(
                    f"{context} runtime input rejection catalog changed"
                )
            for name, reason in expected_runtime.items():
                item = seam["invalid_runtime_inputs"][name]
                validate_rejection(name, item, reason)
                expected_projection = (
                    None if name.startswith("event-kind") else "local"
                )
                if item["projected_event_kind"] != expected_projection:
                    raise EvidenceError(
                        f"{context} {name} event-kind projection changed"
                    )

            ordinal = seam["runner_ordinal_failures"]
            if set(ordinal) != {"1", "2", "3", "4"}:
                raise EvidenceError(
                    f"{context} runtime launch ordinal catalog changed"
                )
            for name, item in ordinal.items():
                validate_probe(f"runner-ordinal-{name}", item)
                number = int(name)
                if (
                    item["audit_exit"] != 2
                    or item["attempts"] != number
                    or item["created"] != number - 1
                    or item["before"] != number
                    or item["after"] != number - 1
                    or item["runner_calls"] != number
                    or item["runner_created"] != number - 1
                    or item["all_pids_reaped"] is not True
                    or "Git process factory failed" not in item["reason"]
                ):
                    raise EvidenceError(
                        f"{context} runner ordinal {name} false-greened"
                    )
            require_keys(
                seam["runner_throwables"],
                ("direct-base", "runtime", "subprocess"),
                f"{context}.runner_throwables",
            )
            for name, item in seam["runner_throwables"].items():
                validate_probe(f"runner-throwable-{name}", item)
                if (
                    item["audit_exit"] != 2
                    or item["attempts"] != 1
                    or item["created"] != 0
                    or item["before"] != 1
                    or item["after"] != 0
                    or item["caught"] is not None
                    or item["all_pids_reaped"] is not True
                ):
                    raise EvidenceError(
                        f"{context} runner throwable {name} escaped"
                    )
            validate_probe(
                "runner-cancellation", seam["runner_cancellation"]
            )
            if (
                seam["runner_cancellation"]["caught"]
                != "KeyboardInterrupt"
                or seam["runner_cancellation"]["all_pids_reaped"] is not True
            ):
                raise EvidenceError(
                    f"{context} runner cancellation escaped cleanup"
                )

            require_keys(
                seam["observer_throwables"],
                ("direct-base", "keyboard", "runtime"),
                f"{context}.observer_throwables",
            )
            for name, item in seam["observer_throwables"].items():
                validate_probe(f"observer-{name}", item)
                if item["all_pids_reaped"] is not True:
                    raise EvidenceError(
                        f"{context} observer {name} left a child"
                    )
            if (
                seam["observer_throwables"]["runtime"]["audit_exit"] != 2
                or seam["observer_throwables"]["direct-base"]["audit_exit"]
                != 2
                or seam["observer_throwables"]["keyboard"]["caught"]
                != "KeyboardInterrupt"
            ):
                raise EvidenceError(
                    f"{context} observer throwable typing changed"
                )

            transaction_throwables = seam["transaction_throwables"]
            expected_transaction_throwables = {
                f"{stage}-{kind}"
                for stage in ("factory", "enter", "exit")
                for kind in ("runtime", "direct-base")
            }
            if set(transaction_throwables) != expected_transaction_throwables:
                raise EvidenceError(
                    f"{context} transaction throwable catalog changed"
                )
            for name, item in transaction_throwables.items():
                validate_probe(f"transaction-{name}", item)
                stage = name.split("-", 1)[0]
                if (
                    item["audit_exit"] != 2
                    or item["caught"] is not None
                    or item["lifecycle"]["exit"]
                    != int(stage == "exit")
                    or (item["attempts"] == 0)
                    is not (stage in {"factory", "enter"})
                    or stage not in item["reason"]
                    or item["all_pids_reaped"] is not True
                ):
                    raise EvidenceError(
                        f"{context} transaction {name} typing changed"
                    )
            require_keys(
                seam["transaction_cancellations"],
                ("enter", "exit", "factory"),
                f"{context}.transaction_cancellations",
            )
            for stage, item in seam["transaction_cancellations"].items():
                validate_probe(f"transaction-cancellation-{stage}", item)
                if (
                    item["caught"] != "KeyboardInterrupt"
                    or item["all_pids_reaped"] is not True
                    or item["lifecycle"]["exit"] != int(stage == "exit")
                ):
                    raise EvidenceError(
                        f"{context} transaction cancellation {stage} changed"
                    )
            trace_boundaries = seam["trace_cancellation_boundaries"]
            require_keys(
                trace_boundaries,
                ("after-enter", "after-session-close"),
                f"{context}.trace_cancellation_boundaries",
            )
            for stage, item in trace_boundaries.items():
                validate_probe(f"transaction-boundary-{stage}", item)
                if (
                    item["caught"] != "KeyboardInterrupt"
                    or item["all_runner_pids_reaped"] is not True
                    or item["fd_delta"] != 0
                    or item["lifecycle"]
                    != {
                        "enter": 1,
                        "exit": 1,
                        "exit_after_reap": True,
                        "exit_exception": "KeyboardInterrupt",
                        "factory": 1,
                    }
                ):
                    raise EvidenceError(
                        f"{context} transaction boundary {stage} leaked"
                    )
            if (
                trace_boundaries["after-enter"]["after"] != 0
                or trace_boundaries["after-session-close"]["after"]
                != valid["after"]
            ):
                raise EvidenceError(
                    f"{context} transaction boundary work changed"
                )
            session_boundaries = seam[
                "session_setup_cancellation_boundaries"
            ]
            require_keys(
                session_boundaries,
                ("after-context-set", "after-reconciler-load"),
                f"{context}.session_setup_cancellation_boundaries",
            )
            for stage, item in session_boundaries.items():
                validate_probe(f"session-boundary-{stage}", item)
                if (
                    item["caught"] != "KeyboardInterrupt"
                    or item["all_runner_pids_reaped"] is not True
                    or item["fd_delta"] != 0
                    or item["lifecycle"]["factory"] != 0
                ):
                    raise EvidenceError(
                        f"{context} session boundary {stage} leaked"
                    )
            spawn_boundaries = seam[
                "spawn_construction_cancellation_boundaries"
            ]
            require_keys(
                spawn_boundaries,
                (
                    "after-pipe-attachment",
                    "after-runner-publication",
                    "after-runner-return",
                ),
                f"{context}.spawn_construction_cancellation_boundaries",
            )
            for stage, item in spawn_boundaries.items():
                validate_probe(f"spawn-boundary-{stage}", item)
                if (
                    item["caught"] != "KeyboardInterrupt"
                    or item["all_runner_pids_reaped"] is not True
                    or item["fd_delta"] != 0
                    or item["runner_created"] != 1
                    or item["lifecycle"]
                    != {
                        "enter": 1,
                        "exit": 1,
                        "exit_after_reap": True,
                        "exit_exception": "KeyboardInterrupt",
                        "factory": 1,
                    }
                ):
                    raise EvidenceError(
                        f"{context} spawn boundary {stage} leaked"
                    )
            validate_probe(
                "truthy-exit", seam["truthy_exit_ignored"]
            )
            if seam["truthy_exit_ignored"]["audit_exit"] != 0:
                raise EvidenceError(
                    f"{context} truthy transaction exit suppressed result"
                )
            validate_probe(
                "noncallable-runner", seam["noncallable_runner"]
            )
            if (
                seam["noncallable_runner"]["audit_exit"] != 2
                or "repository session construction failed: TypeError"
                not in seam["noncallable_runner"]["reason"]
            ):
                raise EvidenceError(
                    f"{context} noncallable runner was not typed"
                )

            hostile = seam["hostile_ambient_subprocess"]
            require_keys(
                hostile,
                (*probe_keys, "popen_identity_unchanged"),
                f"{context}.hostile_ambient_subprocess",
            )
            if (
                hostile["audit_exit"] != 0
                or hostile["popen_identity_unchanged"] is not True
                or hostile["runner_calls"] != hostile["created"]
            ):
                raise EvidenceError(
                    f"{context} ambient subprocess leaked into audit"
                )

            def validate_concurrency(name, item, shared):
                expected_keys = {
                    "ambient_popen_identity_unchanged", "calls",
                    "failures", "shared_runner_calls",
                    "threads_completed",
                }
                if name == "duplicate-module":
                    expected_keys.add("private_modules_leaked")
                require_keys(
                    item, expected_keys,
                    f"{context}.concurrency.{name}",
                )
                if (
                    item["threads_completed"] is not True
                    or item["failures"] != [None, None]
                    or item["ambient_popen_identity_unchanged"] is not True
                    or (
                        name == "duplicate-module"
                        and item["private_modules_leaked"]
                    )
                    or len(item["calls"]) != 2
                ):
                    raise EvidenceError(
                        f"{context} {name} concurrency did not complete"
                    )
                for call in item["calls"]:
                    require_keys(
                        call,
                        (
                            "adapter_status", "after", "attempts",
                            "audit_exit", "before", "created",
                            "pids_unique",
                        ),
                        f"{context}.concurrency.{name}.call",
                    )
                    if (
                        call["adapter_status"] != "accepted"
                        or call["audit_exit"] != 0
                        or call["attempts"] != call["created"]
                        or call["before"] != call["created"]
                        or call["after"] != call["created"]
                        or call["created"] <= 0
                        or call["pids_unique"] is not True
                    ):
                        raise EvidenceError(
                            f"{context} {name} cross-accounted an audit"
                        )
                expected_shared = (
                    sum(call["created"] for call in item["calls"])
                    if shared
                    else None
                )
                if item["shared_runner_calls"] != expected_shared:
                    raise EvidenceError(
                        f"{context} {name} shared runner count changed"
                    )

            same_module = seam["same_module_concurrency"]
            require_keys(
                same_module, ("different-root", "same-root"),
                f"{context}.same_module_concurrency",
            )
            validate_concurrency(
                "same-root", same_module["same-root"], False
            )
            validate_concurrency(
                "different-root", same_module["different-root"], True
            )
            validate_concurrency(
                "duplicate-module",
                seam["duplicate_module_concurrency"],
                True,
            )

            if (
                seam["cache_isolation"]
                != {
                    "carry_cache_distinct": True,
                    "carry_cache_unshared": True,
                    "private_modules_removed": True,
                    "reconcile_cache_distinct": True,
                    "reconcile_cache_unshared": True,
                    "reconcile_modules_distinct": True,
                    "subprocess_facades_distinct": True,
                }
                or seam["nested_reentry"]
                != {
                    "nested_actual": 4,
                    "nested_attempts": 4,
                    "nested_status": "accepted",
                    "outer_actual": 4,
                    "outer_attempts": 4,
                    "outer_status": "accepted",
                }
            ):
                raise EvidenceError(
                    f"{context} nested or cache session isolation changed"
                )
            static = seam["static_contract"]
            require_keys(
                static,
                (
                    "active_reconciler_has_no_default",
                    "ambient_popen_assignment_absent",
                    "ambient_run_assignment_absent",
                    "audit_runner_has_no_default",
                    "audit_paths_have_no_real_fallback",
                    "bounded_git_has_no_fixture_launcher",
                    "classifier_session_has_no_default",
                    "event_kind_exact_type_boundary",
                    "facade_has_no_ambient_delegate",
                    "facade_public_surface_closed",
                    "internal_sessions_have_no_default",
                    "main_runner_has_no_default", "ordinary_cli_absent",
                    "public_ordinary_audit_absent",
                    "public_strategy_surface_u_only",
                    "pipe_result_publication_bridge",
                    "repository_session_owns_metrics",
                    "repository_session_runner_has_no_default",
                    "reconciler_launch_sites",
                    "runner_result_publication_bridge",
                    "spawn_metrics_derived_from_session",
                    "transaction_wrapper_absent",
                ),
                f"{context}.static_contract",
            )
            if (
                any(
                    value is not True
                    for key, value in static.items()
                    if key != "reconciler_launch_sites"
                )
                or static["reconciler_launch_sites"]
                != {"Popen": 2, "run": 65, "total": 67}
            ):
                raise EvidenceError(
                    f"{context} static session boundary changed"
                )
            date_replay = seam["fixture_date_replay"]
            require_keys(
                date_replay,
                (
                    "fixed_date", "opposite_ambient_dates",
                    "private_modules_removed", "private_modules_unique",
                    "replays",
                    "stable_bytes_oid_identity_and_filed_date",
                ),
                f"{context}.fixture_date_replay",
            )
            if (
                date_replay["fixed_date"] != "2026-09-02"
                or date_replay["opposite_ambient_dates"]
                != ["1999-12-31", "2099-01-01"]
                or date_replay["private_modules_removed"] is not True
                or date_replay["private_modules_unique"] is not True
                or date_replay[
                    "stable_bytes_oid_identity_and_filed_date"
                ]
                is not True
                or len(date_replay["replays"]) != 2
            ):
                raise EvidenceError(
                    f"{context} immutable fixture date changed"
                )
            comparable = []
            for replay in date_replay["replays"]:
                require_keys(
                    replay,
                    (
                        "ambient_date", "ambient_date_unchanged",
                        "bytes_sha256", "filed", "fixed_session_date",
                        "git_blob_oid", "identity", "path", "payload",
                    ),
                    f"{context}.fixture_date_replay.replay",
                )
                if (
                    replay["ambient_date_unchanged"] is not True
                    or replay["fixed_session_date"] != "2026-09-02"
                    or not replay["filed"].startswith("2026-09-02")
                ):
                    raise EvidenceError(
                        f"{context} replay used ambient UTC date"
                    )
                comparable.append(
                    {
                        key: value
                        for key, value in replay.items()
                        if key != "ambient_date"
                    }
                )
            if comparable[0] != comparable[1]:
                raise EvidenceError(
                    f"{context} fixed-date replay bytes changed"
                )

        elif row["id"] == "leak-object-database-pipes":
            observation = row["observation"]
            require_keys(
                observation,
                (
                    "baseline", "immutable_backing_bypasses_mutable_view",
                    "cancellation_cleanup_completed",
                    "cancellation_cleanup_notes",
                    "cancellation_cleanup_state",
                    "cleanup_failure_closed", "damaged", "kind",
                    "forced_fd_reuse_safe",
                    "metrics_published_after_close",
                    "pipe_return_publication_observations",
                    "pipe_return_publication_safe",
                    "raw_token_observations",
                    "raw_token_state_machine_safe",
                    "rollback_failure_safe", "rollback_observations",
                    "substituted_pipe_observations",
                    "unclosed_descriptor_failed_closed",
                ),
                f"{context}.observation",
            )
            if observation["kind"] != "object-database-descriptor-lifecycle":
                raise EvidenceError(
                    f"{context} descriptor lifecycle kind changed"
                )
            baseline = observation["baseline"]
            if set(baseline) != {
                "abort", "after-exit", "base-close", "close-live",
                "fileno-base-close", "fileno-keyboard-close",
                "fileno-runtime-close", "fileno-system-exit-abort",
                "keyboard-after-close", "keyboard-close",
                "raising-abort", "raising-close", "runtime-abort",
                "runtime-after-close", "runtime-close",
                "stubborn-after-kill", "stubborn-close",
                "system-exit-abort",
            }:
                raise EvidenceError(
                    f"{context} descriptor baseline modes changed"
                )
            lifecycle_keys = (
                "cleanup_failures", "kill_requested", "killed", "mode",
                "process_reaps", "process_terminations", "returncode_is_set",
                "stdin_closed", "stdin_object_closed", "stdout_closed",
                "stdout_object_closed", "owned_states",
                "wrapper_fileno_calls",
            )
            for mode, item in baseline.items():
                require_keys(
                    item, lifecycle_keys,
                    f"{context}.observation.baseline.{mode}",
                )
                if mode == "stubborn-after-kill":
                    valid_lifecycle = bool(
                        item["process_reaps"] == 0
                        and item["returncode_is_set"] is False
                        and len(item["cleanup_failures"]) == 2
                        and all(
                            failure.endswith(
                                "cat-file child was not reaped after kill"
                            )
                            for failure in item["cleanup_failures"]
                        )
                        and item["process_terminations"] == 1
                        and item["kill_requested"] is True
                        and item["killed"] is True
                    )
                else:
                    failures = item["cleanup_failures"]
                    # Every injected object/view callback is untrusted and is
                    # never invoked.  Cleanup uses the immutable closefd=False
                    # backing plus the tombstoned raw ownership token.
                    failure_valid = not failures
                    valid_lifecycle = bool(
                        item["process_reaps"] == 1
                        and item["returncode_is_set"] is True
                        and failure_valid
                        and item["killed"] is (mode == "stubborn-close")
                        and item["process_terminations"]
                        == int(mode in {"abort", "stubborn-close"})
                        and item["stdin_object_closed"] is True
                        and item["stdout_object_closed"] is True
                        and item["owned_states"]["stdout"] == "CLOSED"
                        and item["owned_states"]["stdin"] == "CLOSED"
                        and item["wrapper_fileno_calls"] == 0
                    )
                if (
                    item["mode"] != mode
                    or item["stdin_closed"] is not True
                    or item["stdout_closed"] is not True
                    or item["owned_states"]["stdout"] != "CLOSED"
                    or item["owned_states"]["stdin"] != "CLOSED"
                    or item["wrapper_fileno_calls"] != 0
                    or not valid_lifecycle
                ):
                    raise EvidenceError(
                        f"{context} baseline descriptor closure changed"
                    )
            raw_tokens = observation["raw_token_observations"]
            substituted = observation["substituted_pipe_observations"]
            require_keys(
                substituted,
                ("close-reuse-return", "close-reuse-throw"),
                f"{context}.observation.substituted_pipe_observations",
            )
            for name, item in substituted.items():
                require_keys(
                    item,
                    (
                        "cleanup_failure", "descriptor_reused",
                        "owned_state", "repeated_failures",
                        "replacement_close_calls", "replacement_survived",
                        "sentinel_created",
                    ),
                    f"{context}.observation.substituted_pipe_observations.{name}",
                )
                if (
                    "cleanup ended closed" not in item["cleanup_failure"]
                    or item["descriptor_reused"] is not True
                    or item["owned_state"] != "CLOSED"
                    or item["repeated_failures"]
                    or item["replacement_close_calls"] != 0
                    or item["replacement_survived"] is not True
                    or item["sentinel_created"] is not False
                ):
                    raise EvidenceError(
                        f"{context} substituted pipe {name} gained close authority"
                    )
            expected_raw_tokens = {
                "success": None,
                "success-reuse": None,
                "pre-runtime": "RuntimeError",
                "post-runtime": "RuntimeError",
                "pre-keyboard": "KeyboardInterrupt",
                "post-keyboard": "KeyboardInterrupt",
                "pre-system-exit": "SystemExit",
                "post-system-exit": "SystemExit",
            }
            require_keys(
                raw_tokens,
                expected_raw_tokens,
                f"{context}.observation.raw_token_observations",
            )
            raw_token_keys = (
                "caught", "close_calls", "descriptor_tombstoned",
                "replacement_bytes", "replacement_survived",
                "repeated_failures", "state",
            )
            for name, expected_throwable in expected_raw_tokens.items():
                item = raw_tokens[name]
                require_keys(
                    item,
                    raw_token_keys,
                    f"{context}.observation.raw_token_observations.{name}",
                )
                if name in {"success", "success-reuse"}:
                    valid_raw = item == {
                        "caught": None,
                        "close_calls": 1,
                        "descriptor_tombstoned": True,
                        "replacement_bytes": (
                            "before-repeat-after-repeat"
                            if name == "success-reuse"
                            else ""
                        ),
                        "replacement_survived": (
                            True if name == "success-reuse" else None
                        ),
                        "repeated_failures": [],
                        "state": "CLOSED",
                    }
                else:
                    valid_raw = bool(
                        item["caught"] == expected_throwable
                        and item["close_calls"] == 1
                        and item["descriptor_tombstoned"] is True
                        and item["replacement_bytes"]
                        == "before-repeat-after-repeat"
                        and item["replacement_survived"] is True
                        and item["state"] == "UNKNOWN"
                        and len(item["repeated_failures"]) == 2
                        and all(
                            "descriptor state remains unknown" in failure
                            for failure in item["repeated_failures"]
                        )
                    )
                if not valid_raw:
                    raise EvidenceError(
                        f"{context} raw token {name} ownership changed"
                    )
            rollbacks = observation["rollback_observations"]
            require_keys(
                rollbacks,
                (
                    "post-keyboard", "post-runtime",
                    "post-system-exit", "pre-keyboard", "pre-runtime",
                    "pre-system-exit",
                ),
                f"{context}.observation.rollback_observations",
            )
            for name, item in rollbacks.items():
                require_keys(
                    item,
                    (
                        "caught", "close_calls", "replacement_bytes",
                        "replacement_survived", "write_end_closed",
                    ),
                    f"{context}.observation.rollback_observations.{name}",
                )
                if (
                    item["caught"]
                    != (
                        "KeyboardInterrupt"
                        if name.endswith("keyboard")
                        else (
                            "SystemExit"
                            if name.endswith("system-exit")
                            else "Unreadable"
                        )
                    )
                    or len(item["close_calls"]) != 2
                    or item["replacement_bytes"]
                    != "rollback-survived"
                    or item["replacement_survived"] is not True
                    or item["write_end_closed"] is not True
                ):
                    raise EvidenceError(
                        f"{context} setup rollback {name} changed"
                    )
            pipe_publication = observation[
                "pipe_return_publication_observations"
            ]
            require_keys(
                pipe_publication,
                ("KeyboardInterrupt", "SystemExit"),
                f"{context}.observation.pipe_return_publication_observations",
            )
            for name, item in pipe_publication.items():
                require_keys(
                    item,
                    ("caught", "closed"),
                    f"{context}.observation.pipe_return_publication_observations.{name}",
                )
                require_keys(
                    item["closed"],
                    ("read", "write"),
                    f"{context}.observation.pipe_return_publication_observations.{name}.closed",
                )
                if (
                    item["caught"] != name
                    or item["closed"] != {"read": True, "write": True}
                ):
                    raise EvidenceError(
                        f"{context} pipe return publication {name} leaked"
                    )
            damaged = observation["damaged"]
            require_keys(
                damaged, lifecycle_keys,
                f"{context}.observation.damaged",
            )
            if (
                damaged["mode"] != "after-exit"
                or damaged["process_reaps"] != 1
                or damaged["returncode_is_set"] is not True
                or damaged["stdin_closed"] is not False
                or damaged["stdout_closed"] is not False
                or damaged["killed"] is not False
                or damaged["process_terminations"] != 0
                or damaged["cleanup_failures"]
                or damaged["stdin_object_closed"] is not False
                or damaged["stdout_object_closed"] is not False
                or set(damaged["owned_states"].values()) != {"OPEN"}
                or damaged["wrapper_fileno_calls"] != 0
                or observation[
                    "immutable_backing_bypasses_mutable_view"
                ] is not True
                or observation["forced_fd_reuse_safe"] is not True
                or observation["raw_token_state_machine_safe"] is not True
                or observation["rollback_failure_safe"] is not True
                or observation["pipe_return_publication_safe"] is not True
                or observation["cancellation_cleanup_completed"] is not True
                or observation["cancellation_cleanup_notes"]
                != [
                    "cat-file cleanup failed: RuntimeError during resource cleanup"
                ]
                or observation["cancellation_cleanup_state"]
                != {
                    "kill_calls": 1,
                    "owned_states": {"stdin": "CLOSED", "stdout": "CLOSED"},
                    "process_reaps": 1,
                    "returncode_is_set": True,
                }
                or observation["cleanup_failure_closed"] is not True
                or observation["metrics_published_after_close"] is not True
                or observation["unclosed_descriptor_failed_closed"] is not True
            ):
                raise EvidenceError(
                    f"{context} leak mutant did not remain observed red"
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
        "boundary_ancestry", "endpoint_contract", "evidence_generation",
        "evidence_supersession", "execution_bounds",
        "immutable_event_workflows", "measured_budget", "origin_strategies",
        "object_database_lifecycle",
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
    if core["evidence_generation"] != generation_contract_projection():
        raise EvidenceError("fresh evidence generation contract changed")
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
    lifecycle_control = next(
        row for row in controls if row["id"] == "leak-object-database-pipes"
    )
    if core["object_database_lifecycle"] != lifecycle_control:
        raise EvidenceError("object database lifecycle projection changed")
    event_workflows = core["immutable_event_workflows"]
    require_keys(
        event_workflows, ("cases", "claim", "cli_control"),
        "immutable_event_workflows",
    )
    expected_event_ids = [
        name for name in SCENARIO_IDS if name.startswith("R19-WF-")
    ]
    if list(event_workflows["cases"]) != expected_event_ids:
        raise EvidenceError("immutable event workflow catalog changed")
    cli_control = next(
        row for row in controls if row["id"] == "event-adapter-cli-entrypoint"
    )
    if event_workflows["cli_control"] != cli_control:
        raise EvidenceError("immutable event CLI projection changed")
    expected_transports = {
        "local", "pre-push", "pull-request-synchronize", "push"
    }
    observed_normal = set()
    observed_blocking = set()
    for name, case in event_workflows["cases"].items():
        require_keys(
            case,
            (
                "adapter", "audit_exit", "classification", "finding",
                "non_fast_forward", "reason_code", "record_sha256",
                "transport", "workflow_attack", "workflow_failure",
            ),
            f"immutable_event_workflows.cases.{name}",
        )
        require_digest(case["record_sha256"], f"{name}.record_sha256")
        if case["record_sha256"] != by_id[name]["record_sha256"]:
            raise EvidenceError(f"{name} record binding changed")
        adapter = case["adapter"]
        require_keys(
            adapter,
            (
                "N", "O", "endpoint_sources", "event_kind",
                "github_sha_used", "mutable_metadata_invariant",
                "mutable_state_reads", "provider_api_calls", "reason",
                "status", "typed_origin_strategy",
            ),
            f"immutable_event_workflows.cases.{name}.adapter",
        )
        if (
            adapter["event_kind"] != case["transport"]
            or adapter["github_sha_used"] is not False
            or adapter["mutable_metadata_invariant"] is not True
            or adapter["mutable_state_reads"] != 0
            or adapter["provider_api_calls"] != 0
            or adapter["typed_origin_strategy"] != "U"
        ):
            raise EvidenceError(f"{name} escaped immutable typed-U event input")
        if case["workflow_failure"] is not None:
            if (
                case["audit_exit"] != 2
                or case["classification"] != "unreadable"
                or case["finding"] is not False
                or adapter["status"] != "coverage-unavailable"
                or adapter["O"] != "0" * 40
                or adapter["N"] != "0" * 40
            ):
                raise EvidenceError(f"{name} event failure did not fail closed")
        elif case["workflow_attack"]:
            observed_blocking.add(case["transport"])
            if (
                case["audit_exit"] != 1
                or case["classification"] != "blocking-finding"
                or case["finding"] is not True
                or case["non_fast_forward"] is not True
                or adapter["status"] != "accepted"
            ):
                raise EvidenceError(f"{name} blocking workflow changed")
        else:
            observed_normal.add(case["transport"])
            if (
                case["audit_exit"] != 0
                or case["classification"] != "no-finding"
                or case["finding"] is not False
                or case["non_fast_forward"] is not True
                or adapter["status"] != "accepted"
            ):
                raise EvidenceError(f"{name} normal restack workflow changed")
    if observed_normal != expected_transports or observed_blocking != expected_transports:
        raise EvidenceError("event workflows do not cover every transport")
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
        (
            "git_process_attempts", "git_processes",
            "production_parent_queries", "record_sha256",
        ),
        "execution_bounds.composition_observation",
    )
    p22_row = by_id["P22-PCX-18-one-pass-many-actions"]
    if bounds["composition_observation"] != {
        "git_process_attempts": 135,
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
        "git_process_attempts", "git_processes", "graph_buffered_bytes",
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
            "duplicate_parent_header", "parent_permutation",
            "review_merge_parent_permutations", "selection_boundary",
        ),
        "origin_strategies",
    )
    if origins["decision"] != "U":
        raise EvidenceError("origin strategy decision changed")
    if origins["duplicate_parent_header"] != {
        "compatible_carrier_count": 1,
        "fsck_returncode": 0,
        "logical_parent_count": 2,
        "raw_parent_header_count": 3,
        "source_count": 1,
    }:
        raise EvidenceError(
            "duplicate parent header source/carrier proof changed"
        )
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
        "R18-U-review-compatible-merge",
        "R18-U-review-compatible-merge-reversed",
        "R18-U-review-compatible-source-low",
        "R18-U-review-compatible-source-low-reversed",
        "R18-U-review-compatible-source-high",
        "R18-U-review-compatible-source-high-reversed",
        "R18-U-review-duplicate-parent-header",
        "R18-U-review-three-carrying-parents",
        "R18-U-review-two-valid-sources",
        "R18-U-review-incompatible-carrier",
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
        "R18-U-review-compatible-merge": "no-finding",
        "R18-U-review-compatible-merge-reversed": "no-finding",
        "R18-U-review-compatible-source-low": "no-finding",
        "R18-U-review-compatible-source-low-reversed": "no-finding",
        "R18-U-review-compatible-source-high": "no-finding",
        "R18-U-review-compatible-source-high-reversed": "no-finding",
        "R18-U-review-duplicate-parent-header": "no-finding",
        "R18-U-review-three-carrying-parents": "no-finding",
        "R18-U-review-two-valid-sources": "no-finding",
        "R18-U-review-incompatible-carrier": "blocking-finding",
    }
    for scenario, expected in expected_classifications.items():
        if origins["cases"][scenario]["classification"] != expected:
            raise EvidenceError(f"origin strategy verdict changed for {scenario}")
    clean_review_merges = {
        name for name in required_origin_cases
        if "review-compatible" in name
        or name in {
            "R18-U-review-three-carrying-parents",
            "R18-U-review-two-valid-sources",
            "R18-U-review-duplicate-parent-header",
        }
    }
    for scenario in clean_review_merges:
        child_edges = {}
        for proof in origins["cases"][scenario]["origin_proofs"]:
            for edge in proof["edges"]:
                child_edges.setdefault(edge["child"], []).append(edge)
        merge_groups = [edges for edges in child_edges.values() if len(edges) > 1]
        if len(merge_groups) != 1:
            raise EvidenceError(f"{scenario} merge edge group changed")
        merge_edges = merge_groups[0]
        if (
            sum(edge["role"] == "source" for edge in merge_edges) != 1
            or sum(
                edge["role"] == "compatible-carrier" for edge in merge_edges
            ) != len(merge_edges) - 1
            or any(
                edge[key] is not None
                for edge in merge_edges
                for key in (
                    "production_problem", "frozen_problem",
                    "regression_problem", "problem",
                )
            )
        ):
            raise EvidenceError(
                f"{scenario} production-valid source/carrier contract changed"
            )
    incompatible_review = origins["cases"][
        "R18-U-review-incompatible-carrier"
    ]
    incompatible_edges = [
        edge
        for proof in incompatible_review["origin_proofs"]
        for edge in proof["edges"]
    ]
    incompatible_groups = {}
    for edge in incompatible_edges:
        incompatible_groups.setdefault(edge["child"], []).append(edge)
    incompatible_merge = [
        edges for edges in incompatible_groups.values() if len(edges) > 1
    ]
    if (
        len(incompatible_merge) != 1
        or sum(edge["problem"] is not None for edge in incompatible_merge[0]) != 1
        or incompatible_review["reason_code"] != "origin-incompatible-carrier"
    ):
        raise EvidenceError("incompatible review carrier false-greened")
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
        "reject-all-origin-invalid-carriers",
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
    if origins["review_merge_parent_permutations"] != core[
        "parent_permutation"
    ]["r19_review_merge_parent_permutations"]:
        raise EvidenceError("review merge parent permutation projection changed")
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
        f"Evidence schemas v2 at commit `{core['evidence_supersession']['artifacts'][0]['commit']}`, v3 at commit `{core['evidence_supersession']['artifacts'][1]['commit']}`, v4 at commit `{core['evidence_supersession']['artifacts'][2]['commit']}`, v5 at commit `{core['evidence_supersession']['artifacts'][3]['commit']}`, v6 at commit `{core['evidence_supersession']['artifacts'][4]['commit']}`, v7 at commit `{core['evidence_supersession']['artifacts'][5]['commit']}`, v8 at commit `{core['evidence_supersession']['artifacts'][6]['commit']}`, v9 at commit `{core['evidence_supersession']['artifacts'][7]['commit']}`, v10 at commit `{core['evidence_supersession']['artifacts'][8]['commit']}`, v11 at commit `{core['evidence_supersession']['artifacts'][9]['commit']}`, and v12 at commit `{core['evidence_supersession']['artifacts'][10]['commit']}` are superseded and burned by their later blockers; all histories are preserved, no identifier is reused, and this artifact closes `{core['evidence_supersession']['replacement_schema']}`.",
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
        "All four transports reject identical O/N before the transaction factory or",
        "any Git child. A budget is likewise admitted before execution only when it is",
        "`None` or an exact positive integer; zero, negative, Boolean, float, and string",
        "values fail closed with zero transaction entries and zero Git children. Non-mapping",
        "payloads and event kinds whose runtime type is not exactly built-in `str`",
        "have the same stable pre-execution refusal. Rejected event-kind runtime values",
        "project to JSON `null`, never the caller object; an unhashable `str` subclass",
        "and a plain object both serialize canonically with zero transaction or runner work.", "",
        "The stable executable adapter entrypoint is",
        "`prototype.py --repo ROOT --event-kind KIND --event-payload EVENT.json`.",
        "Exits 0, 1, and 2 mean clean, blocking, and coverage-unavailable. Importers",
        "use `event_endpoints(event_kind, payload)` and typed-U-only",
        "`audit_event(root, event_kind, payload, *, git_runner, budget_limit=None, transaction=None)`.",
        "The required keyword-only `git_runner` has no default, `None`, ambient, or",
        "process-global fallback. There is no advertised ordinary O/N CLI and no",
        "selectable non-U production route.",
        "Each valid audit creates a private `RepositorySession` that owns its resolved",
        "root, metrics, observer, children, descriptors, object database and caches,",
        "carry-proof cache, and uniquely named reconciler module. The reconciler's",
        "repository roots, mutable caches, persistent readers, active transition state,",
        f"and date are session-local; retry rendering is pinned to `{core['evidence_generation']['fixture_date']}`.",
        "Its closed module-local subprocess facade exposes only Git `run`/`Popen` and",
        "routes every imported child through the injected runner. It never patches or",
        "delegates to the process-global `subprocess.Popen`.",
        "A valid event calls the optional transaction seam once around the complete",
        "Git-backed audit and its resource cleanup. Its context may yield a `GitSpawnObserver`;",
        "production calls `before_spawn(exact_command)` before creating every Git",
        "child and `after_spawn(exact_command, pid)` afterward. Thus an external",
        "evaluator precharges every attempt while `git_processes` counts only children",
        "actually created and delivered to `after_spawn`. Factory/entry failures create",
        "no attempts; launch or callback throwables retain exact attempt/actual/before/after",
        "counts. Callback throwables clean up",
        "the child before returning unreadable or re-raising cancellation, and attach a",
        "stable cleanup-failure note if cancellation cleanup cannot be proven. Session",
        "cleanup finishes while the transaction remains active; `__exit__` is called once",
        "after cleanup, cannot suppress the audit result, and final metrics are taken after",
        "exit. Non-cancellation factory/enter/exit failures are typed unreadable, while",
        "cancellation is deferred until independent cleanup and the permitted exit call finish.",
        "Deterministic cancellation at the first line after reconciler load, after the",
        "session ContextVar changes, after the runner result is published, after its local",
        "binding, after pipe attachment,",
        "after transaction entry, and before transaction exit leaves no private module,",
        "child, or descriptor behind. The caller context manager is entered and exited",
        "directly; no Python wrapper adds a delegate-entry or delegate-exit gap.",
        "Concurrent and nested sessions, including duplicate prototype imports sharing one",
        "immutable runner, remain isolated for the same or different repository roots; all",
        "private module names are removed on cleanup and ambient Popen identity is unchanged.",
        "The caller receives neither",
        "the operation nor its result, so O/N, Strategy U, and classification remain",
        "owned by the audit. Local, pre-push, push, and PR",
        "synchronize each run a real non-fast-forward clean restack and genuine blocking",
        "attack. Endpoint extraction never consults provider state, an API, a current",
        "ref, or `github.sha`, and makes no claim about provider authority or intent.", "",
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
        "At a carrying merge, U gathers every production-valid source edge, selects",
        "the lexically smallest `(parent, child, path)` deterministically, and validates",
        "every remaining edge as a compatible carrier. Real-Git controls vary source",
        "OID order and parent order, cover three carrying parents and two explicit valid",
        "sources, reject a truly incompatible carrier, and observe the old reject-all",
        "mutant red. Parent-header multiplicity is deduplicated by logical parent OID",
        "before classification: a manually encoded, `git fsck`-accepted commit with",
        "three raw headers and two logical parents produces exactly one source and one",
        "compatible carrier. Every accepted edge is checked by production mutation semantics.", "",
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
        "## Evidence publication and process cleanup", "",
        "`python3 -I -S audit_readme.py --generate` requires its own isolated/no-site",
        "startup and runs the prototype the same way with an allowlisted environment",
        "and fresh temporary fixture root. Git is selected only from fixed system",
        "prefixes, smoke-tested after the scrub, and its resolved path and executable",
        "digest are bound in evidence; caller PATH and Python/Git startup variables are",
        "not inherited. Caller-supplied JSONL and optional comparison input must match",
        "that replay byte-for-byte before either output file is touched. Raw records are",
        "compact sorted-key JSON, one LF per row, with a final LF and no CR; duplicate",
        "keys, unsorted rows, CRLF, and missing final LF are rejected. The auditor",
        "recomputes aliases, permutations, and summary invariants from scenario/control",
        "rows. Nonexistent-OID and contradictory-result forgeries remain red even when",
        "the same forged file is both `--stream` and `--compare`; all six pre-generation",
        "damage probes preserve output sentinels. Both output files and their old backups",
        "are staged and fsynced before a canonical same-directory recovery journal is",
        "published and directory-fsynced. A directory-inode lock serializes publishers;",
        "a concurrent publisher refuses before staging. Cancellation immediately after",
        "the directory fd is published or immediately before close releases the lock, and",
        "a following publisher reacquires it. An ordinary late failure restores",
        "the old pair. If that recovery also persistently fails, the journal and verified",
        "regular-file backups remain, every invocation refuses or restores the old pair",
        "before generating, and a later successful invocation recovers deterministically.",
        "Forged traversal names, malformed digests, symlink journals/backups, and symlink",
        "targets are never accepted as recovery authority. One bounded descriptor reader",
        "uses required `O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC`, compares lstat/pre-fstat/post-fstat",
        "type, device, inode, size, mtime_ns, and ctime_ns, and reads no more than limit+1",
        f"bytes. Artifacts/backups use a {MAX_EXISTING_ARTIFACT_BYTES}-byte cap; journals use",
        f"the separate {MAX_PAIR_JOURNAL_BYTES}-byte cap. Exact-limit files pass; plus-one, FIFO, device,",
        "directory, symlink, lstat/open replacement, growth, shrinkage, and same-inode/same-size",
        "mutation refuse. Bytes become visible only after the one raw descriptor close succeeds.",
        "Recovery stages verified backup bytes to a distinct restore file, preserves the sole",
        "backup until the restored target validates, and validates both newly published targets",
        "against intended bytes before deleting the journal.",
        "Portable filesystems still",
        "cannot atomically exchange two paths: a process or machine crash may expose a",
        "temporary mixed namespace, but the fsynced journal keeps it non-authoritative and",
        "recoverable on the next invocation. This does not claim atomic pair visibility or",
        "survival of storage loss/corruption beyond the filesystem's fsync guarantees. The",
        "lock pins and serializes one directory inode, but pathname operations are not yet",
        "dirfd-relative; hostile replacement of the parent directory during publication is",
        "explicitly outside this POC's claim.", "",
        "Every production `PIPE` pair is published into a construction registry before",
        "Python regains control, converted to one raw parent-fd ownership token before",
        "Popen, and exposed through a non-owning Python view. Immediately before",
        "the sole raw close call, cleanup tombstones the numeric descriptor and changes OPEN",
        "to durable UNKNOWN; only a normal return upgrades it to CLOSED. Every throwable is",
        "therefore ambiguous and fail-closed; cleanup never retries an UNKNOWN token, so later fd",
        "reuse cannot be closed by a stale object. The object database closes stdin and",
        "stdout on success, abort, an already-exited child, and a stubborn child that",
        "requires timeout then kill. Public process replacements and mutations of the",
        "non-owning view are never granted a close callback; cleanup uses its immutable",
        "closefd-false backing reference only after the raw token is consumed. A raw closer",
        "that closes first and then throws is propagated as UNKNOWN, never claimed as",
        "verified cleanup; cancellation is never swallowed. An",
        "unclosable descriptor likewise fails closed with no action. Even an unproved",
        "post-kill reap closes both descriptors and returns unreadable without recording",
        "a false reap. Repeated close or abort is idempotent, and published metrics are",
        "snapshotted only after final cleanup. The observed-red leak mutant leaves both",
        "descriptors open after the child has already exited.", "",
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
        f"Ten runtime exact/+1 pairs bind streaming graph bytes/lines/tokens, object payloads, flattened trees, dynamic support traversal, certificate serialization, origin-arm nodes/parent edges, and canonical birth-witness bytes. Every +1 refusal exits 2 with zero partial results; graph reads peak at {bounds['streaming_graph_contract']['bounded_chunk_bytes']} bytes per chunk and publish nothing on refusal. P22 separately observes exactly {bounds['composition_observation']['production_parent_queries']} imported production parent queries, {bounds['composition_observation']['git_process_attempts']} Git spawn attempts, and {bounds['composition_observation']['git_processes']} actual Git children.",
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
              f"P22 measured {m['graph_commits']} graph commits and 16 disappeared actions with exactly {m['graph_enumerations']} POC graph enumeration, {m['per_action_history_walks']} POC-owned per-action history walks, {m['queue_snapshots_requested']} snapshot requests, {m['snapshot_cache_hits']} snapshot-cache hits, {m['git_process_attempts']} precharged Git spawn attempts, and {m['git_processes']} actual Git processes.",
              "The process count includes imported production `git rev-list --parents -n 1` queries; zero applies only to POC-owned per-action walks. The POC's single budget consistently caps every emitted work counter.",
              f"PCX-20a passes at its exact measured maximum {exact_budget['measured_max_work']} with limit {exact_budget['limit']}; PCX-20b exits 2 with zero partial results when measured maximum {overflow_budget['measured_max_work']} exceeds limit {overflow_budget['limit']} by one.",
              f"R17-precharge-P22-budget charges before work and aborts on `{precharge_budget['evidence_reason']}` with exact bounded counters; the post-hoc reference vector is retained only as a damaged control.",
              f"The 64-parent boundary case stops at parent token {wide_budget['metrics']['graph_parent_tokens']} against limit {wide_budget['budget_contract']['limit']} after {wide_budget['metrics']['graph_output_bytes']} of {wide_budget['budget_contract']['raw_graph_bytes']} raw bytes; the graph child is reaped and no graph is published.",
              "The closed runtime matrix additionally admits/refuses exact/+1 values for total graph bytes, peak graph-line bytes, a 1,000,000-byte object, 1,004 flattened paths, 12 dynamic support paths, 2,920 serialized certificate bytes, five origin-arm nodes, three origin parent edges, and 1,042 canonical birth-witness bytes.", "",
              f"PCX-19 is replay-bound by `{p19['record_sha256']}`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.", "",
              "## Reproducible audit", "",
              "Use two fresh, empty scratch roots:", "", "```sh",
              "PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r27-v13-seed1 > /tmp/production-contract-r27-v13-seed1.jsonl",
              "PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --reverse-construction --fixtures-dir /tmp/production-contract-r27-v13-seed777 > /tmp/production-contract-r27-v13-seed777.jsonl",
              "python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r27-v13-seed1.jsonl --compare /tmp/production-contract-r27-v13-seed777.jsonl",
              "python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r27-v13-seed1.jsonl --damage-test",
              "python3 -I -S docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r27-v13-seed1.jsonl --compare /tmp/production-contract-r27-v13-seed777.jsonl --generate",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --event-kind push --event-payload /path/to/event.json",
              "python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py",
              "python3 automation/run_tests.py --jobs 1", "python3 automation/reconcile/reconcile.py --check", "```", "",
              "The auditor requires a fresh internal replay and raw byte equality before generation, rejects",
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
              "- Uncatchable process termination and native failure inside a resource-creating syscall are outside this Python POC; Python-level `KeyboardInterrupt`/`SystemExit` after resource return is covered by pre-bytecode ownership publication.",
              "- Hostile replacement of the artifact parent directory inode during publication is excluded until every pathname operation is dirfd-relative.",
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
        "superseded-v6-commit-erased",
        lambda d: d["core_claims"]["evidence_supersession"][
            "artifacts"
        ][4].update(commit="0" * 40),
        "evidence schema supersession changed",
    )
    for superseded_index, superseded_version in enumerate(
        range(7, 13), start=5
    ):
        manifest_case(
            f"superseded-v{superseded_version}-commit-erased",
            lambda d, index=superseded_index: d["core_claims"]
            ["evidence_supersession"]["artifacts"][index].update(
                commit="0" * 40
            ),
            "evidence schema supersession changed",
        )
    manifest_case(
        "fresh-generation-caller-authoritative",
        lambda d: d["core_claims"]["evidence_generation"].update(
            caller_rows_authoritative=True
        ),
        "fresh evidence generation contract changed",
    )
    manifest_case(
        "event-workflow-provider-api",
        lambda d: d["core_claims"]["immutable_event_workflows"][
            "cases"
        ]["R19-WF-push-normal-restack"]["adapter"].update(
            provider_api_calls=1
        ),
        "escaped immutable typed-U event input",
    )
    manifest_case(
        "event-invalid-invokes-transaction",
        lambda d: d["core_claims"]["immutable_event_workflows"][
            "cli_control"
        ]["observation"]["execution_seam"]["invalid"]["lifecycle"].update(
            factory=1
        ),
        "invalid entered execution",
    )
    manifest_case(
        "event-valid-observer-misses-child",
        lambda d: d["core_claims"]["immutable_event_workflows"][
            "cli_control"
        ]["observation"]["execution_seam"]["valid"].update(
            after=3
        ),
        "valid audit escaped session accounting",
    )
    manifest_case(
        "descriptor-after-exit-leak",
        lambda d: d["core_claims"]["object_database_lifecycle"][
            "observation"
        ]["baseline"]["after-exit"].update(stdout_closed=False),
        "baseline descriptor closure changed",
    )
    manifest_case(
        "descriptor-wrapper-recovery-misreported-clean",
        lambda d: d["core_claims"]["object_database_lifecycle"][
            "observation"
        ].update(immutable_backing_bypasses_mutable_view=False),
        "object database lifecycle projection changed",
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
    pre_generation = []

    def generation_probe(
        name,
        damaged_raw,
        expected_failure,
        *,
        same_file_compare=False,
    ):
        observed_failure = None
        sentinel = b"DO-NOT-OVERWRITE\n"
        with tempfile.TemporaryDirectory(
            prefix="production-contract-generation-damage-"
        ) as raw:
            evidence_path = Path(raw) / "evidence.json"
            readme_path = Path(raw) / "README.md"
            evidence_path.write_bytes(sentinel)
            readme_path.write_bytes(sentinel)
            try:
                damaged_stream = Stream.from_bytes(
                    damaged_raw, f"<pre-generation-{name}>"
                )
                publish_generated_artifacts(
                    damaged_stream,
                    stream,
                    evidence_path,
                    readme_path,
                    comparison=(
                        damaged_stream if same_file_compare else None
                    ),
                )
            except EvidenceError as error:
                observed_failure = str(error)
            sentinels_unchanged = (
                evidence_path.read_bytes() == sentinel
                and readme_path.read_bytes() == sentinel
            )
        pre_generation.append(
            {
                "damage": name,
                "expected_failure": expected_failure,
                "observed_failure": observed_failure,
                "same_file_stream_and_compare": same_file_compare,
                "sentinels_unchanged": sentinels_unchanged,
                "status": (
                    "OBSERVED_RED"
                    if observed_failure is not None
                    and expected_failure in observed_failure
                    and sentinels_unchanged
                    else "FALSE_GREEN"
                ),
            }
        )

    stale_rows = copy.deepcopy(stream.objects)
    stale_row = next(
        row
        for row in stale_rows
        if row.get("scenario") == "R18-U-normal-base-advance-replay"
    )
    stale_row["O"] = "f" * 40
    generation_probe(
        "pre-generation-nonexistent-OID",
        b"".join(canonical_bytes(row) for row in stale_rows),
        "differs byte-for-byte from fresh internal replay",
        same_file_compare=True,
    )

    contradictory_rows = copy.deepcopy(stream.objects)
    contradictory = next(
        row
        for row in contradictory_rows
        if row.get("scenario") == "R18-U-normal-base-advance-replay"
    )
    contradictory["classification"] = "blocking-finding"
    contradictory["expected_result"] = "blocking-finding"
    generation_probe(
        "pre-generation-contradictory-result",
        b"".join(canonical_bytes(row) for row in contradictory_rows),
        "differs byte-for-byte from fresh internal replay",
        same_file_compare=True,
    )
    generation_probe(
        "pre-generation-CRLF",
        stream.raw.replace(b"\n", b"\r\n"),
        "contains CR bytes",
        same_file_compare=True,
    )
    generation_probe(
        "pre-generation-missing-final-LF",
        stream.raw[:-1],
        "has no final LF",
        same_file_compare=True,
    )
    strict_lines = stream.raw[:-1].split(b"\n")
    duplicate_first = strict_lines[0].replace(
        b'{"C":', b'{"C":"duplicate","C":', 1
    )
    generation_probe(
        "pre-generation-duplicate-key",
        b"\n".join([duplicate_first, *strict_lines[1:]]) + b"\n",
        "duplicate JSON key",
        same_file_compare=True,
    )
    first_value = load_json(strict_lines[0])
    reversed_value = {
        key: first_value[key] for key in reversed(tuple(first_value))
    }
    unsorted_first = json.dumps(
        reversed_value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("utf-8")
    generation_probe(
        "pre-generation-unsorted-json",
        b"\n".join([unsorted_first, *strict_lines[1:]]) + b"\n",
        "not canonical sorted-key JSON+LF",
        same_file_compare=True,
    )
    results.extend(pre_generation)

    with tempfile.TemporaryDirectory(
        prefix="production-contract-startup-hook-damage-"
    ) as raw:
        hook_root = Path(raw)
        marker = hook_root / "startup-hook-ran"
        hook = hook_root / "sitecustomize.py"
        hook.write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('ran', encoding='utf-8')\n"
            "print('{\"startup_hook_substituted_replay\":true}')\n",
            encoding="utf-8",
        )
        inherited = {
            name: os.environ.get(name)
            for name in ("PYTHONPATH", "PYTHONSTARTUP", "PYTHONWARNINGS")
        }
        os.environ.update(
            {
                "PYTHONPATH": str(hook_root),
                "PYTHONSTARTUP": str(hook),
                "PYTHONWARNINGS": "error",
            }
        )
        startup_failure = None
        try:
            isolated_replay = internal_replay_stream()
        except EvidenceError as error:
            startup_failure = str(error)
            isolated_replay = None
        finally:
            for name, value in inherited.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        cli_stream = hook_root / "stream.jsonl"
        cli_evidence = hook_root / "evidence.json"
        cli_readme = hook_root / "README.md"
        cli_stream.write_bytes(stream.raw)
        cli_expected = manifest_from_stream(stream)
        cli_evidence.write_bytes(canonical_bytes(cli_expected))
        cli_readme.write_bytes(render_readme(cli_expected))
        hook_environment = os.environ.copy()
        hook_environment.update(
            {
                "PYTHONPATH": str(hook_root),
                "PYTHONSTARTUP": str(hook),
            }
        )
        cli_arguments = [
            str(Path(__file__).resolve()),
            "--stream",
            str(cli_stream),
            "--evidence",
            str(cli_evidence),
            "--readme",
            str(cli_readme),
        ]
        ordinary_cli = subprocess.run(
            [sys.executable, *cli_arguments],
            check=False,
            env=hook_environment,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            timeout=30,
        )
        ordinary_hook_executed = marker.exists()
        marker.unlink(missing_ok=True)
        isolated_cli = subprocess.run(
            [sys.executable, "-I", "-S", *cli_arguments],
            check=False,
            env=hook_environment,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            timeout=30,
        )
        isolated_hook_ignored = not marker.exists()
        ordinary_cli_refused = bool(
            ordinary_cli.returncode != 0
            and b'"audit": "PASS"' not in ordinary_cli.stdout
            and b"requires isolated no-site Python" in ordinary_cli.stdout
        )
        isolated_cli_passed = bool(
            isolated_cli.returncode == 0
            and b'"audit": "PASS"' in isolated_cli.stdout
            and isolated_hook_ignored
        )
        startup_isolated = bool(
            startup_failure is None
            and isolated_replay is not None
            and isolated_replay.raw == stream.raw
            and ordinary_hook_executed
            and ordinary_cli_refused
            and isolated_cli_passed
        )
        startup_hook_executed = marker.exists()
    results.append(
        {
            "damage": "isolated-replay-startup-hook",
            "expected_failure": "ambient startup hook excluded",
            "observed_failure": startup_failure,
            "isolated_cli_passed": isolated_cli_passed,
            "ordinary_cli_refused": ordinary_cli_refused,
            "ordinary_hook_executed": ordinary_hook_executed,
            "startup_hook_executed": startup_hook_executed,
            "status": (
                "OBSERVED_RED" if startup_isolated else "FALSE_GREEN"
            ),
        }
    )

    with tempfile.TemporaryDirectory(
        prefix="production-contract-pair-publication-damage-"
    ) as raw:
        output_root = Path(raw)
        evidence_path = output_root / "evidence.json"
        readme_path = output_root / "README.md"
        old_evidence = b"OLD-EVIDENCE\n"
        old_readme = b"OLD-README\n"
        evidence_path.write_bytes(old_evidence)
        readme_path.write_bytes(old_readme)
        replace_calls = 0
        refused_readme_once = False
        real_replace = os.replace

        def fail_second_replace(source, destination):
            nonlocal replace_calls, refused_readme_once
            replace_calls += 1
            if (
                Path(destination) == readme_path
                and not refused_readme_once
            ):
                refused_readme_once = True
                raise OSError("injected second artifact replace failure")
            return real_replace(source, destination)

        publication_failure = None
        os.replace = fail_second_replace
        try:
            publish_generated_artifacts(
                stream,
                stream,
                evidence_path,
                readme_path,
                comparison=stream,
            )
        except EvidenceError as error:
            publication_failure = str(error)
        finally:
            os.replace = real_replace
        old_pair_restored = bool(
            evidence_path.read_bytes() == old_evidence
            and readme_path.read_bytes() == old_readme
        )
    results.append(
        {
            "damage": "late-pair-publication-io-failure",
            "expected_failure": "artifact pair publication failed",
            "observed_failure": publication_failure,
            "old_pair_restored": old_pair_restored,
            "replace_calls": replace_calls,
            "status": (
                "OBSERVED_RED"
                if publication_failure is not None
                and "artifact pair publication failed" in publication_failure
                and "old pair restored" in publication_failure
                and old_pair_restored
                and replace_calls >= 4
                else "FALSE_GREEN"
            ),
        }
    )

    with tempfile.TemporaryDirectory(
        prefix="production-contract-persistent-publication-damage-"
    ) as raw:
        output_root = Path(raw)
        evidence_path = output_root / "evidence.json"
        readme_path = output_root / "README.md"
        journal_path = artifact_pair_journal_path(
            evidence_path, readme_path
        )
        old_evidence = b"OLD-EVIDENCE\n"
        old_readme = b"OLD-README\n"
        evidence_path.write_bytes(old_evidence)
        readme_path.write_bytes(old_readme)
        real_replace = os.replace
        persistent_calls = 0
        publication_started = False

        def fail_from_second_target(source, destination):
            nonlocal persistent_calls, publication_started
            persistent_calls += 1
            if Path(destination) == readme_path:
                publication_started = True
            if publication_started:
                raise OSError("injected persistent artifact replace failure")
            return real_replace(source, destination)

        persistent_failure = None
        os.replace = fail_from_second_target
        try:
            publish_generated_artifacts(
                stream,
                stream,
                evidence_path,
                readme_path,
                comparison=stream,
            )
        except EvidenceError as error:
            persistent_failure = str(error)
        finally:
            os.replace = real_replace
        journal_retained = journal_path.is_file()
        retained_journal_record = (
            read_bounded_regular(
                journal_path,
                "retained artifact pair recovery journal",
                MAX_PAIR_JOURNAL_BYTES,
                False,
            )
            if journal_retained
            else None
        )
        retained_journal = (
            load_json(retained_journal_record[0])
            if retained_journal_record is not None
            else {}
        )
        retained_backups = bool(
            journal_retained
            and all(
                entry["backup"] is None
                or (output_root / entry["backup"]).is_file()
                for entry in retained_journal.get("targets", [])
            )
        )
        with artifact_pair_publication_lock(output_root):
            recovered = recover_generated_artifact_pair(
                evidence_path, readme_path
            )
        old_pair_recovered_next_run = bool(
            recovered
            and evidence_path.read_bytes() == old_evidence
            and readme_path.read_bytes() == old_readme
            and not journal_path.exists()
        )
        recovered_publication = publish_generated_artifacts(
            stream,
            stream,
            evidence_path,
            readme_path,
            comparison=stream,
        )
        final_pair_published = bool(
            evidence_path.read_bytes()
            == canonical_bytes(recovered_publication)
            and readme_path.read_bytes()
            == render_readme(recovered_publication)
            and not journal_path.exists()
        )
    results.append(
        {
            "damage": "persistent-pair-publication-io-failure",
            "expected_failure": "artifact pair recovery incomplete",
            "observed_failure": persistent_failure,
            "journal_retained": journal_retained,
            "backups_retained": retained_backups,
            "old_pair_recovered_next_run": old_pair_recovered_next_run,
            "final_pair_published": final_pair_published,
            "replace_calls_before_refusal": persistent_calls,
            "status": (
                "OBSERVED_RED"
                if persistent_failure is not None
                and "artifact pair recovery incomplete" in persistent_failure
                and journal_retained
                and retained_backups
                and old_pair_recovered_next_run
                and final_pair_published
                else "FALSE_GREEN"
            ),
        }
    )

    def hostile_journal_probe(name, mutate):
        with tempfile.TemporaryDirectory(
            prefix=f"production-contract-{name}-damage-"
        ) as raw:
            output_root = Path(raw)
            evidence_path = output_root / "evidence.json"
            readme_path = output_root / "README.md"
            journal_path = artifact_pair_journal_path(
                evidence_path, readme_path
            )
            evidence_path.write_bytes(b"NEW-EVIDENCE\n")
            readme_path.write_bytes(b"OLD-README\n")
            evidence_backup = output_root / ".evidence.json.old.safe.tmp"
            readme_backup = output_root / ".README.md.old.safe.tmp"
            evidence_backup.write_bytes(b"OLD-EVIDENCE\n")
            readme_backup.write_bytes(b"OLD-README\n")
            journal = {
                "schema": PAIR_JOURNAL_SCHEMA,
                "targets": [
                    {
                        "backup": evidence_backup.name,
                        "existed": True,
                        "new": ".evidence.json.new.safe.tmp",
                        "old_sha256": digest_bytes(b"OLD-EVIDENCE\n"),
                        "target": evidence_path.name,
                    },
                    {
                        "backup": readme_backup.name,
                        "existed": True,
                        "new": ".README.md.new.safe.tmp",
                        "old_sha256": digest_bytes(b"OLD-README\n"),
                        "target": readme_path.name,
                    },
                ],
            }
            sentinel = output_root / "outside-sentinel"
            sentinel.write_bytes(b"DO-NOT-TOUCH\n")
            mutate(
                journal,
                journal_path,
                evidence_backup,
                sentinel,
            )
            if not journal_path.exists() and not journal_path.is_symlink():
                journal_path.write_bytes(canonical_bytes(journal))
            hostile_failure = None
            try:
                recover_generated_artifact_pair(
                    evidence_path, readme_path
                )
            except EvidenceError as error:
                hostile_failure = str(error)
            sentinel_unchanged = sentinel.read_bytes() == b"DO-NOT-TOUCH\n"
            targets_unchanged = bool(
                evidence_path.read_bytes() == b"NEW-EVIDENCE\n"
                and readme_path.read_bytes() == b"OLD-README\n"
            )
        results.append(
            {
                "damage": name,
                "expected_failure": "artifact pair recovery incomplete",
                "observed_failure": hostile_failure,
                "sentinel_unchanged": sentinel_unchanged,
                "targets_unchanged": targets_unchanged,
                "status": (
                    "OBSERVED_RED"
                    if hostile_failure is not None
                    and "artifact pair recovery incomplete"
                    in hostile_failure
                    and sentinel_unchanged
                    and targets_unchanged
                    else "FALSE_GREEN"
                ),
            }
        )

    def inject_path_traversal(journal, _journal_path, _backup, _sentinel):
        journal["targets"][0]["backup"] = (
            ".evidence.json.old.safe.tmp/../../outside-sentinel"
        )

    hostile_journal_probe(
        "recovery-journal-path-traversal", inject_path_traversal
    )

    def inject_symlink_journal(journal, journal_path, _backup, sentinel):
        carrier = journal_path.parent / "outside-journal"
        carrier.write_bytes(canonical_bytes(journal))
        journal_path.symlink_to(carrier)

    hostile_journal_probe(
        "recovery-journal-symlink", inject_symlink_journal
    )

    def inject_symlink_backup(journal, journal_path, backup, sentinel):
        backup.unlink()
        backup.symlink_to(sentinel)
        journal_path.write_bytes(canonical_bytes(journal))

    hostile_journal_probe(
        "recovery-backup-symlink", inject_symlink_backup
    )

    def inject_invalid_digest(journal, journal_path, _backup, _sentinel):
        journal["targets"][0]["old_sha256"] = "sha256:not-a-digest"
        journal_path.write_bytes(canonical_bytes(journal))

    hostile_journal_probe(
        "recovery-journal-invalid-digest", inject_invalid_digest
    )

    with tempfile.TemporaryDirectory(
        prefix="production-contract-target-symlink-recovery-damage-"
    ) as raw:
        output_root = Path(raw)
        evidence_path = output_root / "evidence.json"
        readme_path = output_root / "README.md"
        journal_path = artifact_pair_journal_path(
            evidence_path, readme_path
        )
        sentinel = output_root / "outside-sentinel"
        sentinel.write_bytes(b"OLD-EVIDENCE\n")
        evidence_path.symlink_to(sentinel)
        readme_path.write_bytes(b"OLD-README\n")
        evidence_backup = output_root / ".evidence.json.old.safe.tmp"
        readme_backup = output_root / ".README.md.old.safe.tmp"
        evidence_backup.write_bytes(b"OLD-EVIDENCE\n")
        readme_backup.write_bytes(b"OLD-README\n")
        journal_path.write_bytes(
            canonical_bytes(
                {
                    "schema": PAIR_JOURNAL_SCHEMA,
                    "targets": [
                        {
                            "backup": evidence_backup.name,
                            "existed": True,
                            "new": ".evidence.json.new.safe.tmp",
                            "old_sha256": digest_bytes(b"OLD-EVIDENCE\n"),
                            "target": evidence_path.name,
                        },
                        {
                            "backup": readme_backup.name,
                            "existed": True,
                            "new": ".README.md.new.safe.tmp",
                            "old_sha256": digest_bytes(b"OLD-README\n"),
                            "target": readme_path.name,
                        },
                    ],
                }
            )
        )
        target_symlink_recovered = recover_generated_artifact_pair(
            evidence_path, readme_path
        )
        target_is_regular = stat.S_ISREG(evidence_path.lstat().st_mode)
        sentinel_unchanged = sentinel.read_bytes() == b"OLD-EVIDENCE\n"
    results.append(
        {
            "damage": "recovery-target-symlink-not-accepted",
            "expected_failure": "symlink replaced from verified backup",
            "observed_failure": None,
            "sentinel_unchanged": sentinel_unchanged,
            "target_is_regular": target_is_regular,
            "status": (
                "OBSERVED_RED"
                if target_symlink_recovered
                and target_is_regular
                and sentinel_unchanged
                else "FALSE_GREEN"
            ),
        }
    )

    with tempfile.TemporaryDirectory(
        prefix="production-contract-target-oversized-recovery-damage-"
    ) as raw:
        output_root = Path(raw)
        evidence_path = output_root / "evidence.json"
        readme_path = output_root / "README.md"
        journal_path = artifact_pair_journal_path(
            evidence_path, readme_path
        )
        with evidence_path.open("wb") as stream_handle:
            stream_handle.truncate(MAX_EXISTING_ARTIFACT_BYTES + 1)
        readme_path.write_bytes(b"OLD-README\n")
        evidence_backup = output_root / ".evidence.json.old.safe.tmp"
        readme_backup = output_root / ".README.md.old.safe.tmp"
        evidence_backup.write_bytes(b"OLD-EVIDENCE\n")
        readme_backup.write_bytes(b"OLD-README\n")
        journal_path.write_bytes(
            canonical_bytes(
                {
                    "schema": PAIR_JOURNAL_SCHEMA,
                    "targets": [
                        {
                            "backup": evidence_backup.name,
                            "existed": True,
                            "new": ".evidence.json.new.safe.tmp",
                            "old_sha256": digest_bytes(b"OLD-EVIDENCE\n"),
                            "target": evidence_path.name,
                        },
                        {
                            "backup": readme_backup.name,
                            "existed": True,
                            "new": ".README.md.new.safe.tmp",
                            "old_sha256": digest_bytes(b"OLD-README\n"),
                            "target": readme_path.name,
                        },
                    ],
                }
            )
        )
        oversized_target_recovered = recover_generated_artifact_pair(
            evidence_path, readme_path
        )
        restored_bytes = evidence_path.read_bytes()
        oversized_journal_cleared = not journal_path.exists()
    results.append(
        {
            "damage": "recovery-target-oversized-not-read-unbounded",
            "expected_failure": "oversized target replaced from bounded backup",
            "observed_failure": None,
            "journal_cleared": oversized_journal_cleared,
            "restored_old_bytes": restored_bytes == b"OLD-EVIDENCE\n",
            "status": (
                "OBSERVED_RED"
                if oversized_target_recovered
                and oversized_journal_cleared
                and restored_bytes == b"OLD-EVIDENCE\n"
                else "FALSE_GREEN"
            ),
        }
    )

    with tempfile.TemporaryDirectory(
        prefix="production-contract-concurrent-publication-damage-"
    ) as raw:
        output_root = Path(raw)
        evidence_path = output_root / "evidence.json"
        readme_path = output_root / "README.md"
        evidence_path.write_bytes(b"OLD-EVIDENCE\n")
        readme_path.write_bytes(b"OLD-README\n")
        staging_cancellation_observations = {}
        for cancellation_type in (KeyboardInterrupt, SystemExit):
            caught = None
            captured_descriptor = None

            def cancel_staging_boundary(
                stage, _path, descriptor, exception=cancellation_type
            ):
                nonlocal captured_descriptor
                if stage == "after-mkstemp-publication":
                    captured_descriptor = descriptor
                    raise exception(
                        "injected staging-file publication cancellation"
                    )

            try:
                stage_artifact_bytes(
                    output_root / "cancel-target",
                    b"CANCELLED-STAGE\n",
                    cancellation_type.__name__,
                    checkpoint=cancel_staging_boundary,
                )
            except BaseException as error:
                caught = type(error).__name__
            descriptor_closed = False
            if captured_descriptor is not None:
                try:
                    os.fstat(captured_descriptor)
                except OSError as error:
                    descriptor_closed = error.errno == errno.EBADF
            staging_free = {
                path.name for path in output_root.iterdir()
            } == {"evidence.json", "README.md"}
            staging_cancellation_observations[cancellation_type.__name__] = {
                "caught": caught,
                "descriptor_closed": descriptor_closed,
                "staging_free": staging_free,
            }
        staging_cancellation_safe = all(
            item
            == {
                "caught": name,
                "descriptor_closed": True,
                "staging_free": True,
            }
            for name, item in staging_cancellation_observations.items()
        )
        lock_cancellation_observations = {}
        for cancellation_stage in (
            "after-open-publication",
            "before-close",
        ):
            caught = None

            def cancel_lock_boundary(
                stage, _descriptor, target=cancellation_stage
            ):
                if stage == target:
                    raise KeyboardInterrupt(
                        "injected publication lock cancellation"
                    )

            try:
                with artifact_pair_publication_lock(
                    output_root, checkpoint=cancel_lock_boundary
                ):
                    pass
            except BaseException as error:
                caught = type(error).__name__
            reacquired = False
            try:
                with artifact_pair_publication_lock(output_root):
                    reacquired = True
            except EvidenceError:
                pass
            lock_cancellation_observations[cancellation_stage] = {
                "caught": caught,
                "reacquired": reacquired,
            }
        lock_cancellation_safe = all(
            item == {"caught": "KeyboardInterrupt", "reacquired": True}
            for item in lock_cancellation_observations.values()
        )
        concurrent_failure = None
        with artifact_pair_publication_lock(output_root):
            try:
                publish_generated_artifacts(
                    stream,
                    stream,
                    evidence_path,
                    readme_path,
                    comparison=stream,
                )
            except EvidenceError as error:
                concurrent_failure = str(error)
        refused_pair_unchanged = bool(
            evidence_path.read_bytes() == b"OLD-EVIDENCE\n"
            and readme_path.read_bytes() == b"OLD-README\n"
        )
        after_release = publish_generated_artifacts(
            stream,
            stream,
            evidence_path,
            readme_path,
            comparison=stream,
        )
        serialized_pair_published = bool(
            evidence_path.read_bytes() == canonical_bytes(after_release)
            and readme_path.read_bytes() == render_readme(after_release)
        )
    results.append(
        {
            "damage": "concurrent-artifact-pair-publisher",
            "expected_failure": "artifact pair generation already active",
            "observed_failure": concurrent_failure,
            "lock_cancellation_observations": (
                lock_cancellation_observations
            ),
            "lock_cancellation_safe": lock_cancellation_safe,
            "staging_cancellation_observations": (
                staging_cancellation_observations
            ),
            "staging_cancellation_safe": staging_cancellation_safe,
            "refused_pair_unchanged": refused_pair_unchanged,
            "serialized_pair_published": serialized_pair_published,
            "status": (
                "OBSERVED_RED"
                if concurrent_failure is not None
                and "artifact pair generation already active"
                in concurrent_failure
                and lock_cancellation_safe
                and staging_cancellation_safe
                and refused_pair_unchanged
                and serialized_pair_published
                else "FALSE_GREEN"
            ),
        }
    )

    def hostile_existing_target_probe(name, prepare_target, reason):
        with tempfile.TemporaryDirectory(
            prefix=f"production-contract-{name}-damage-"
        ) as raw:
            output_root = Path(raw)
            evidence_path = output_root / "evidence.json"
            readme_path = output_root / "README.md"
            sentinel = output_root / "outside-sentinel"
            sentinel.write_bytes(b"DO-NOT-TOUCH\n")
            readme_path.write_bytes(b"OLD-README\n")
            prepare_target(evidence_path, sentinel)
            refusal = None
            try:
                publish_generated_artifacts(
                    stream,
                    stream,
                    evidence_path,
                    readme_path,
                    comparison=stream,
                )
            except EvidenceError as error:
                refusal = str(error)
            journal_free = not artifact_pair_journal_path(
                evidence_path, readme_path
            ).exists()
            staging_free = not any(
                path.name.endswith(".tmp") for path in output_root.iterdir()
            )
            sentinel_unchanged = sentinel.read_bytes() == b"DO-NOT-TOUCH\n"
            readme_unchanged = readme_path.read_bytes() == b"OLD-README\n"
        results.append(
            {
                "damage": name,
                "expected_failure": reason,
                "observed_failure": refusal,
                "journal_free": journal_free,
                "staging_free": staging_free,
                "sentinel_unchanged": sentinel_unchanged,
                "other_target_unchanged": readme_unchanged,
                "status": (
                    "OBSERVED_RED"
                    if refusal is not None
                    and reason in refusal
                    and journal_free
                    and staging_free
                    and sentinel_unchanged
                    and readme_unchanged
                    else "FALSE_GREEN"
                ),
            }
        )

    def make_symlink(target, sentinel):
        target.symlink_to(sentinel)

    def make_fifo(target, _sentinel):
        os.mkfifo(target)

    def make_directory(target, _sentinel):
        target.mkdir()

    def make_oversized(target, _sentinel):
        with target.open("wb") as stream_handle:
            stream_handle.truncate(MAX_EXISTING_ARTIFACT_BYTES + 1)

    for target_name, prepare_target, reason in (
        (
            "existing-artifact-target-symlink",
            make_symlink,
            "must be a non-symlink regular file",
        ),
        (
            "existing-artifact-target-fifo",
            make_fifo,
            "must be a non-symlink regular file",
        ),
        (
            "existing-artifact-target-directory",
            make_directory,
            "must be a non-symlink regular file",
        ),
        (
            "existing-artifact-target-oversized",
            make_oversized,
            f"exceeds the {MAX_EXISTING_ARTIFACT_BYTES}-byte bound",
        ),
    ):
        hostile_existing_target_probe(target_name, prepare_target, reason)

    device_failure = None
    try:
        read_bounded_regular(
            Path(os.devnull),
            "existing artifact target device",
            MAX_EXISTING_ARTIFACT_BYTES,
            False,
        )
    except EvidenceError as error:
        device_failure = str(error)
    results.append(
        {
            "damage": "existing-artifact-target-device",
            "expected_failure": "must be a non-symlink regular file",
            "observed_failure": device_failure,
            "journal_free": True,
            "status": (
                "OBSERVED_RED"
                if device_failure is not None
                and "must be a non-symlink regular file" in device_failure
                else "FALSE_GREEN"
            ),
        }
    )

    # Exercise the one bounded descriptor reader directly.  The same helper is
    # used for journals, ordinary artifacts, backups, restored targets, and
    # final published-artifact verification, so each role repeats the complete
    # hostile identity/type matrix rather than relying on one representative.
    reader_stages = (
        "after-lstat",
        "after-open",
        "after-pre-fstat",
        "after-first-chunk",
        "before-post-fstat",
    )

    def bounded_reader_probe(role, variant):
        limit = 8
        observed_failure = None
        observed_payload = None
        stage_counts = {stage: 0 for stage in reader_stages}
        mutation_stage = {
            "lstat-open-swap": "after-lstat",
            "growth": "after-pre-fstat",
            "shrink": "after-pre-fstat",
            "same-inode-same-size-mutation": "after-first-chunk",
        }.get(variant)
        with tempfile.TemporaryDirectory(
            prefix=f"production-contract-{role}-{variant}-reader-"
        ) as raw:
            directory = Path(raw)
            target = directory / f"{role}.dat"
            sentinel = directory / "sentinel.dat"
            sentinel.write_bytes(b"SENTINEL")
            if variant == "exact-limit":
                target.write_bytes(b"12345678")
            elif variant == "plus-one":
                target.write_bytes(b"123456789")
            elif variant == "symlink":
                target.symlink_to(sentinel)
            elif variant == "fifo":
                os.mkfifo(target)
            elif variant == "directory":
                target.mkdir()
            elif variant == "device":
                target = Path(os.devnull)
            elif variant == "growth":
                target.write_bytes(b"1234")
            else:
                target.write_bytes(b"12345678")

            def checkpoint(stage, checked_target, _descriptor):
                stage_counts[stage] += 1
                if stage != mutation_stage or stage_counts[stage] != 1:
                    return
                if variant == "lstat-open-swap":
                    replacement = directory / "replacement.dat"
                    replacement.write_bytes(b"ABCDEFGH")
                    os.replace(replacement, checked_target)
                elif variant == "growth":
                    write_descriptor = os.open(checked_target, os.O_WRONLY)
                    try:
                        os.lseek(write_descriptor, 0, os.SEEK_END)
                        os.write(write_descriptor, b"56789")
                    finally:
                        os.close(write_descriptor)
                elif variant == "shrink":
                    write_descriptor = os.open(checked_target, os.O_WRONLY)
                    try:
                        os.ftruncate(write_descriptor, 3)
                    finally:
                        os.close(write_descriptor)
                elif variant == "same-inode-same-size-mutation":
                    original = checked_target.stat()
                    write_descriptor = os.open(checked_target, os.O_WRONLY)
                    try:
                        os.pwrite(write_descriptor, b"ABCDEFGH", 0)
                    finally:
                        os.close(write_descriptor)
                    os.utime(
                        checked_target,
                        ns=(original.st_atime_ns, original.st_mtime_ns),
                    )

            try:
                record = read_bounded_regular(
                    target,
                    f"{role} reader probe",
                    limit,
                    False,
                    checkpoint=checkpoint,
                )
                observed_payload = record[0]
            except EvidenceError as error:
                observed_failure = str(error)
            sentinel_unchanged = sentinel.read_bytes() == b"SENTINEL"

        exact = variant == "exact-limit"
        expected_stages = all(
            stage_counts[stage] == 1 for stage in reader_stages
        )
        mutation_fired = (
            mutation_stage is None or stage_counts[mutation_stage] == 1
        )
        rejected = observed_failure is not None
        passed = (
            observed_failure is None
            and observed_payload == b"12345678"
            and expected_stages
            if exact
            else rejected and mutation_fired
        )
        results.append(
            {
                "damage": f"bounded-reader-{role}-{variant}",
                "expected_failure": (
                    None if exact else "bounded reader refusal"
                ),
                "observed_failure": observed_failure,
                "hook_counts": stage_counts,
                "mutation_hook_fired_once": mutation_fired,
                "sentinel_unchanged": sentinel_unchanged,
                "status": "OBSERVED_RED" if passed else "FALSE_GREEN",
            }
        )

    for reader_role in (
        "journal", "artifact", "backup", "restored-target"
    ):
        for reader_variant in (
            "exact-limit",
            "plus-one",
            "symlink",
            "fifo",
            "directory",
            "device",
            "lstat-open-swap",
            "growth",
            "shrink",
            "same-inode-same-size-mutation",
        ):
            bounded_reader_probe(reader_role, reader_variant)

    return {"audit_damage": "PASS" if all(x["status"] == "OBSERVED_RED" for x in results) else "FAIL",
            "cases": results, "observed_red": sum(x["status"] == "OBSERVED_RED" for x in results), "total": len(results)}


def main(argv=None):
    if not sys.flags.isolated or not sys.flags.no_site:
        print(
            json.dumps(
                {
                    "audit": "FAIL",
                    "failures": [
                        "auditor requires isolated no-site Python; invoke "
                        "python3 -I -S audit_readme.py"
                    ],
                },
                sort_keys=True,
            )
        )
        return 1
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
        supplied = Stream(args.stream)
        second = Stream(args.compare) if args.compare else None
        fresh = None
        if args.generate or args.damage_test:
            fresh = internal_replay_stream()
            require_fresh_replay(
                supplied,
                fresh,
                second if args.generate else None,
            )
        first = fresh or supplied
        expected = manifest_from_stream(first)
        if args.generate:
            expected = publish_generated_artifacts(
                supplied,
                fresh,
                args.evidence,
                args.readme,
                comparison=second,
            )
        evidence_record = read_bounded_regular(
            args.evidence,
            "final evidence artifact",
            MAX_EXISTING_ARTIFACT_BYTES,
            False,
        )
        readme_record = read_bounded_regular(
            args.readme,
            "final README artifact",
            MAX_EXISTING_ARTIFACT_BYTES,
            False,
        )
        failures = audit_artifacts(
            evidence_record[0], readme_record[0], expected
        )
        comparison = None
        if second is not None:
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
