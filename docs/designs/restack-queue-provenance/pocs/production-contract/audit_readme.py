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


SCHEMA = "agentfold-production-contract-evidence/v4"
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
    ],
    "replacement_schema": SCHEMA,
}
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
PRECHARGE_P22_METRICS = {
    "authority_calls": 0,
    "batch_processes": 1,
    "carry_proof_edges": 1,
    "carry_proof_nodes": 2,
    "git_processes": 4,
    "graph_commits": 133,
    "graph_enumerations": 1,
    "graph_parent_edges": 132,
    "identity_calls": 32,
    "mutation_calls": 1,
    "object_cache_hits": 25,
    "object_reads": 134,
    "per_action_history_walks": 0,
    "queue_snapshots_requested": 59,
    "queue_subtree_reads": 3,
    "snapshot_cache_hits": 55,
    "support_adoption_checks": 0,
    "support_certificate_calls": 0,
    "support_paths_checked": 0,
}
POSTHOC_P22_METRICS = {
    "authority_calls": 32,
    "batch_processes": 1,
    "carry_proof_edges": 2080,
    "carry_proof_nodes": 2112,
    "git_processes": 135,
    "graph_commits": 133,
    "graph_enumerations": 1,
    "graph_parent_edges": 132,
    "identity_calls": 32,
    "mutation_calls": 2080,
    "object_cache_hits": 24736,
    "object_reads": 300,
    "per_action_history_walks": 0,
    "queue_snapshots_requested": 10973,
    "queue_subtree_reads": 3,
    "snapshot_cache_hits": 10970,
    "support_adoption_checks": 0,
    "support_certificate_calls": 16,
    "support_paths_checked": 0,
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
    "R17-wide-outside-C-boundary-budget",
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
    "unmetered-cone-work",
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

# Generated once from the closed v4 catalog after the semantic implementation
# was committed.  Each digest binds the complete recursive object-key, list,
# and scalar-type shape of one raw JSONL row.  Values remain observations; the
# grammar cannot learn new fields from the stream it is auditing.
RAW_SHAPE_SHA256 = {
    "aliases": "sha256:539a8708aebdaa2816ceb01ed2e091a849972b69700c444eeec8e566eaa9eed3",
    "control:broad-review-pending-normalization": "sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414",
    "control:first-parent-carry-proof": "sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4",
    "control:identity-multiplicity-collapsed-to-set": "sha256:1ac1b79c19942df728cefbeb0153aeb8b42f07ceffc5343fd5981b03e6048190",
    "control:ignore-absent-C-arm": "sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4",
    "control:ignore-invalid-N-root": "sha256:e6d8aa17fd995baf10e03163e020ab50afb5e1b5bfcc3ebf515a9c09dc66a8ab",
    "control:ignore-outside-C-carrier": "sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4",
    "control:ignore-persisted-absent-C-arm": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "control:ignore-persisted-outside-C-collision": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "control:literal-review-pending-treated-concrete": "sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414",
    "control:locale-git-error-stream-equality": "sha256:742dda0d750851fe1eaf99a187460279385d12aadb25de6479979cbea272c8e4",
    "control:missing-all-parent-direct-validation": "sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4",
    "control:missing-post-event-continuity": "sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4",
    "control:omit-old-tip-human-binding": "sha256:4d55407e4a51e86c40626e007d59ef9c33330a0f865fa8eee3fc5e490525b414",
    "control:omit-supplier-carrier-human-binding": "sha256:465ccf7bbd7c9fc49c2576a9974d06ef1c8ec5cf27711192ed3bb05d1b009deb",
    "control:omit-unanswered-published-review-binding": "sha256:465ccf7bbd7c9fc49c2576a9974d06ef1c8ec5cf27711192ed3bb05d1b009deb",
    "control:posthoc-budget-accounting": "sha256:d6614abe8fe0948afc2d92eee3ad3589110a23d9e90d919df0add5a5b42f8e19",
    "control:reopen-outside-C-boundary-ancestry": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "control:reopen-pre-C-genealogy": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "control:restore-universal-ancestor-carry-scan": "sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4",
    "control:skip-carry-compatibility": "sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4",
    "control:skip-old-side-continuity": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "control:skip-persisted-candidate-continuity": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "control:skip-persisted-frozen-skeleton": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "control:skip-preserved-state-validation": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "control:skip-supplier-support-certificate": "sha256:e6d8aa17fd995baf10e03163e020ab50afb5e1b5bfcc3ebf515a9c09dc66a8ab",
    "control:sole-valid-ignores-invalid-root": "sha256:2bb8d20021633274e28d6f0f50b220f5cf51f178b5a23154193f49719b1ca7b4",
    "control:supplier-authority-borrowing": "sha256:889c75da0848d6f89f4d98b22ac05d36d45c3a1d4888d64ae67d9316869049f4",
    "control:unmetered-cone-work": "sha256:71d2d9785c27add943a10650d72555da7af8ff0a38e127d8c3c2c1f6c9b70bc2",
    "parent-permutation": "sha256:ff2c5187a2f005aefb4e390ee296b9fb51f90077a07b7e52b90e26a54bcc27d6",
    "scenario:P1-direct-linear-valid": "sha256:4f57c411153ac91e0f28e3cc64dac2f23410bb94fc1c840713da76b0a93fa218",
    "scenario:P10-direct-invalid-parent": "sha256:01e6260085ff5eb2334602eb098ff771dc09269a8cb63a6200145ca4eef4a57e",
    "scenario:P11-direct-three-parent-valid": "sha256:1ee423dc5b8305ffccc4722d757c6371b0b19a7f1b5217e7aeb724367efe94f3",
    "scenario:P12-merge-supplier-valid": "sha256:00565c9d4a4a7d25da4e80f148302fef53f4c259ef64349144faf419eec02364",
    "scenario:P13-merge-supplier-invalid": "sha256:62da7d196d8bad9c166bfa2eafad724e1584b07e8d4a4e8eb7c40e2e4cb949b9",
    "scenario:P14-supplier-reintroduced": "sha256:310db656a21015f6567a328a7c64b2c3419e275b6d6774dc1fb40ed4f302ce27",
    "scenario:P15-competing-suppliers": "sha256:09c89a51aa5e43c70b659c1659cfe28b2e9a5ec47703a54e8087c135ef204bd1",
    "scenario:P16-PCX-08-invalid-supplier-claimed-carrier": "sha256:4488cd3c1a2c4d5994c6bb46cb824d6c68e6d58a2aa3abfd6eed76f68aaef5ce",
    "scenario:P17-post-event-reintroduction": "sha256:cda7200a0d7e880d074374340589fbe9d2997b6fc47b6ad737cbda83c6c51f14",
    "scenario:P18a-missing-tip": "sha256:3fe0878772693203523bd6e3b20f2ea446029febe6fe067507a847a619563014",
    "scenario:P18b-noncommit-tip": "sha256:3fe0878772693203523bd6e3b20f2ea446029febe6fe067507a847a619563014",
    "scenario:P18c-unrelated-tip": "sha256:3fe0878772693203523bd6e3b20f2ea446029febe6fe067507a847a619563014",
    "scenario:P18d-shallow-required-region": "sha256:3fe0878772693203523bd6e3b20f2ea446029febe6fe067507a847a619563014",
    "scenario:P18e-missing-queue-blob": "sha256:419b4356e1f0d1678126caf65937db1bd48e6a58ad64c664f42e378b44a1bdeb",
    "scenario:P18f-missing-queue-tree": "sha256:1806ccf6466ed9b923dde9fa4d8d3b137514c17184cb80ff24aaa438b4fe7d6e",
    "scenario:P18g-multiple-merge-bases": "sha256:26d72e01367fbc7cb11697d189ba4b627be68ca9441fc8b7c117c872ccaf78e6",
    "scenario:P19-production-identities": "sha256:3b8c74a04de8f6aa19ad2b1df9f36300ef1cfc5d896253cd26b67649a23e0895",
    "scenario:P2-direct-linear-invalid": "sha256:5e07c2f06a7385d29bfc4cd95d9452d283d6a9cab08e542f1b66d2a529b72ffd",
    "scenario:P20-lifecycle-types": "sha256:790b95cca795de94037a8733edbd66394e7bdc35e4bdefac71aeaecadf08a741",
    "scenario:P21-PCX-17c-squash-erasure": "sha256:93c8b68b97875346777b7b84de1224dd540b7c77d2ee3362e1291bd48aa7c8c2",
    "scenario:P22-PCX-18-one-pass-many-actions": "sha256:3eb7a914f658d0c7fd8d69bca1bbe6067d1a43df36e06016a7dbf6ebf87bb5ce",
    "scenario:P3-genuine-old-loss": "sha256:a097a6969d953ee800774c16742065afcf8a7e0076f37f4d04c4c43a9416c85a",
    "scenario:P4-pre-C-identical-origins": "sha256:f4e23b44a040c258896440326857f7725a87c4146f55d0575841fccedfe5a57a",
    "scenario:P5-duplicate-at-C": "sha256:95cc7ab17d7aca33d21dc7c590b899afb8edab5bf76c338662e9ae6ba02f7dd3",
    "scenario:P6a-old-delete-recreate": "sha256:9b77d06b33492cf733db6be995c8d2d6d190695154d469fad9686c9d15b202ed",
    "scenario:P6b-candidate-delete-recreate": "sha256:2f0ea2af2d4a5f4dcf4a9aa51b6a3f5bf0c9743f18f5d2730fc35905c3d3e2bb",
    "scenario:P7-immutable-payload-change": "sha256:6c68e56ba7b340e4e2b00e7cd2e6313411762a44c56044025aaf2ce0d34737fa",
    "scenario:P8-path-timing-move": "sha256:c6c94e4d9e9e39903bbc992112d4e9c05f25933fa9f2b56010023368337fc9f9",
    "scenario:P9-direct-two-parent-valid": "sha256:1122c4dcafa80445178261be2e8aae86edf3200d65598d0bca1a0c875a765922",
    "scenario:PCX-01-neutral-parent": "sha256:fe2e59559b9be8c45637262fd5208f402a9e7d8a3d21808f881981ba9a43e143",
    "scenario:PCX-02-neutral-plus-invalid-carrier": "sha256:b19bbd151828efe888d10aafabe4f2e4e29a7454f9b954bc038ebaf40b87d44e",
    "scenario:PCX-03-foreign-exact-identity": "sha256:9853e0ce9f9ac92b90c93c732f074fa2b97e7e0e51f268a2d0ac9045eeae3a28",
    "scenario:PCX-04-several-absent-one-supplier": "sha256:197755aff25d09a8ea136cc8ec93ecb853a176764fce34fc0cf450f4dd731a74",
    "scenario:PCX-05-competing-later-supplier": "sha256:85298e9b8db840e57d058dcf7e7539122ac790bbd87c1921134d2932cc50a0ef",
    "scenario:PCX-06-nested-supplier-over-direct": "sha256:d0d9b0eafcfca30ef00bd59475ef485f0475fab33dc56d145d6fffc62593619e",
    "scenario:PCX-07-overqualified-propagation": "sha256:e128695a0477b946986adcda4961cc1becb92fe0093d6020db51e79831a222a6",
    "scenario:PCX-09-recreated-claimed-bytes": "sha256:8c51b761094c1b31602eb7c12b4f70b920216b4e7891a28025206d944dbfd29b",
    "scenario:PCX-10-transient-multiplicity": "sha256:cf935303af710635a962719a21ac46a27192aa77b44e979d41a9dd40a0b079d6",
    "scenario:PCX-11-different-payload-same-path": "sha256:7682c4c604b83b9d03ef378a2115fc0da8863d6efcc69cfbe6208406a4b63523",
    "scenario:PCX-12-timing-rename-supplier": "sha256:ac9480dc82b0b2d963c2ba2a1aca74ba5860774274ba380f9369aef70f2aac84",
    "scenario:PCX-13-conflicting-human-response": "sha256:341d1d6491c2aceeddcbca08545b8e4946b81dc4d2d98d5e9ddda17e40076cf0",
    "scenario:PCX-14-valid-human-supplier": "sha256:d6c4cf6e8e0412edc029a17dcc079126191a51a8a87d725b5ae21fadf67dcc30",
    "scenario:PCX-15-generated-retry-supplier": "sha256:1d82c960d0ae56079ca0f67ee6a502a3059b6e62b0d82b5794257c0f9961d73d",
    "scenario:PCX-16-task-pickup-supplier": "sha256:ae56073e6626fa418b0eaa3dfdc47f5df86cfa12e8c1fd250c93a4f391051e8f",
    "scenario:PCX-17-complete-cherry-pick": "sha256:0f0fa982a491381f67eaba898f5a3a5040efacbe696de8e3a20e4c740bb65322",
    "scenario:PCX-17-deletion-only-cherry-pick": "sha256:93c8b68b97875346777b7b84de1224dd540b7c77d2ee3362e1291bd48aa7c8c2",
    "scenario:PCX-19-missing-claim-blob-recovery": "sha256:dcb05057ea8f97dc971659734c1523121d21ff5067a892aeed07e479342b4de8",
    "scenario:PCX-20a-budget-below-limit": "sha256:749fc3aa6ff630c31dc0660afb7529847bff9c004b3f45f9233376fafe660325",
    "scenario:PCX-20b-budget-overflow": "sha256:eecfab76b9cb1eb756c4ce5b185090b28ef3ff32636e2f05daefabdada64e20a",
    "scenario:R10-direct-review-target-backtick-dotless-rejected": "sha256:eaee6ac70be223bc9c06f1e6c60d3db0507fe7ae97c33e1badbcf2e7835f6280",
    "scenario:R10-supplier-review-revision-generic-placeholder-rejected": "sha256:003105c4970f78686dbbf6b8d8156609e6c04f3ea0434587d36e20f67afcfa40",
    "scenario:R13-direct-review-binding-identical": "sha256:02c4fbb02e15cc114e07af0c8fe7d6127426af458ff2a993cbb7c4ca8e11c0e1",
    "scenario:R13-direct-review-binding-revision": "sha256:2423eeae5e3c75f2a378dfd0f4c6fd8b60597df6508728614f60543c6218fcc6",
    "scenario:R13-direct-review-binding-target": "sha256:e0d718638a9333744e5a01da72747bc38f4706a89c05a4fa399da7ba64029073",
    "scenario:R13-direct-review-binding-terminal": "sha256:104db72d76b254600903259c6c7c528dec5e881d84bb1e8e40ea848373654117",
    "scenario:R13-persisted-claim-loss": "sha256:d1acd512cf5d33e1201fa9d3013799264a7efc04bd936985e13923447f246b0f",
    "scenario:R13-persisted-pending-fill": "sha256:b4ca4de60fbd3cf3a1c6bedbfb41a07d3383a7bdc06418273b6d227634cd78e2",
    "scenario:R13-persisted-response-change": "sha256:cd1fadee6fb0b335319a7b248058039500885d7b4e3e53fd8c4b118b13fd9083",
    "scenario:R13-persisted-response-removal": "sha256:af55228232f3fd868fdb24ecdb7db33c4ae3a2ecaa776788b536552e263b1b73",
    "scenario:R13-persisted-review-outcome-change": "sha256:e114232ad2ff4fa0930ee14714d2a0ad41a6c5a0b7eb1582ebcbd0093b2a3298",
    "scenario:R13-persisted-review-revision-change": "sha256:e114232ad2ff4fa0930ee14714d2a0ad41a6c5a0b7eb1582ebcbd0093b2a3298",
    "scenario:R13-persisted-review-target-change": "sha256:e114232ad2ff4fa0930ee14714d2a0ad41a6c5a0b7eb1582ebcbd0093b2a3298",
    "scenario:R13-persisted-same-state": "sha256:5789876e350a0b65dea7d7f1d32b3cdb774720c163913b848187fbcd6639d099",
    "scenario:R13-persisted-terminal-fill": "sha256:0cb17b65d0a617f1d65035996835ebb05e8ee3ba2de88cd07c52432ff832d5fe",
    "scenario:R13-supplier-review-binding-identical": "sha256:595e4d1fc5132756fdfdb57fc68f816bd54df3edbe5c6246e6e647bfe5f8f299",
    "scenario:R13-supplier-review-binding-revision": "sha256:bd502a2056f7af102fdfefb846f8f0bdc7fd5ccd5ef4bc362c4ce6c0d6616d6d",
    "scenario:R13-supplier-review-binding-target": "sha256:bd502a2056f7af102fdfefb846f8f0bdc7fd5ccd5ef4bc362c4ce6c0d6616d6d",
    "scenario:R13-supplier-review-binding-terminal": "sha256:d52d0ed325a22d955a0935cb120decf090d66ffbd0891ba1d76b5e5ab9e2df64",
    "scenario:R14-direct-old-unanswered-carrier-same": "sha256:51300b0922cdd5f2a96cfb2f4d817de7ff8f0fe4d422d7f4abacd663d1792825",
    "scenario:R14-direct-old-unanswered-carrier-target": "sha256:51300b0922cdd5f2a96cfb2f4d817de7ff8f0fe4d422d7f4abacd663d1792825",
    "scenario:R14-persisted-delete-recreate": "sha256:67bdeb1a089804f5250d8783f5d54828ea96d407e2569905ecc33dfc2b909b54",
    "scenario:R14-persisted-hidden-bytes-low-similarity": "sha256:2c1e1263df499554656e50b0982695179e4a42c0374fe8c1ef22e60180d7dde7",
    "scenario:R14-persisted-intermediate-claim-regression": "sha256:87e4b6dbde420a89905893ab03c43cfcfe2f9ce457127ef76d63b87e64d3942b",
    "scenario:R14-persisted-intermediate-review-regression": "sha256:67f47c44ed293296af1aaa69e2d86d62f3bb9adbd79c3684636dd486581542dc",
    "scenario:R14-persisted-merge-carrier-conflict": "sha256:e0b93f8a10cad2a02fec9334c53a067064984a0ad278c52940e43df6d10af5ce",
    "scenario:R14-persisted-merge-carrier-pending": "sha256:2ddd38d288e6c4b4530136d6335d6c4ad502363af270c117a39d266ec4eb812b",
    "scenario:R14-persisted-valid-first-response-low-similarity": "sha256:687af1371e90781fa0e39a6aa3aed534e1e87a63d5b09526060f5f830d865857",
    "scenario:R14-persisted-valid-review-retraction": "sha256:b6c65b358e94d1eb65bda1a91eb4bf0a4ea0eba808a22ce7fcb295014a532b64",
    "scenario:R14-supplier-old-answered-carrier-pending": "sha256:c8697ede5a532dfc45249823dc2dfa3c5c100da09ebfdbd29ded58673a3bc3a2",
    "scenario:R14-supplier-old-answered-carrier-revision": "sha256:c8697ede5a532dfc45249823dc2dfa3c5c100da09ebfdbd29ded58673a3bc3a2",
    "scenario:R14-supplier-old-answered-carrier-same": "sha256:c8697ede5a532dfc45249823dc2dfa3c5c100da09ebfdbd29ded58673a3bc3a2",
    "scenario:R14-supplier-old-answered-carrier-target": "sha256:c8697ede5a532dfc45249823dc2dfa3c5c100da09ebfdbd29ded58673a3bc3a2",
    "scenario:R14-supplier-old-unanswered-carrier-same": "sha256:0bec2193b838acdae28891d496208d05aacb5fbe1fc056a2a085e73f73956c18",
    "scenario:R14-supplier-old-unanswered-carrier-target": "sha256:0bec2193b838acdae28891d496208d05aacb5fbe1fc056a2a085e73f73956c18",
    "scenario:R15-old-continuous-preserved": "sha256:bae77b8a677a42073e15ae5658725e4fada94ab54e2bcb233ce30555afcf3134",
    "scenario:R15-old-hidden-bytes-restore": "sha256:86d14691b56c11bce08a523b6a0e6e32d35d288058b2cd4c0f86ce0590977b49",
    "scenario:R15-old-human-binding-restore": "sha256:d7ac26397564d28615a0d41ae0b68ca1ea96d8cc53871941dc53eb7adaf59cb8",
    "scenario:R15-old-invalid-delete-recreate": "sha256:eb90596b6ad0a878496032692dc5c3c189e7215049f3a10cba12732d15586068",
    "scenario:R15-old-valid-delete-recreate": "sha256:2d32f225c59dfa1b8de4355958c65e0686b127c0f9bbbee2e41b509f17aadab6",
    "scenario:R16-earlier-landed-evidence-reversal": "sha256:077b449fb3e8d73dcbd714f6c0188607b5796754f48b2cb9df5a1a5f1540778d",
    "scenario:R16-pickup-evolution-0-backlog": "sha256:1d950653f0896f02fea932383fdd8a8c4dabc0a3fcf1ae9b3bbc3ba097903912",
    "scenario:R16-pickup-evolution-2-blocked": "sha256:35c3ce120c33f21dcceb9ef41f29e584e4f77cd7de93af1f91e1b1d4bc951d2d",
    "scenario:R16-pickup-evolution-3-in-review": "sha256:d26737780d5ebb99a3ae0afc552af97c282e1605bbd23df3341ee9acd5c3730e",
    "scenario:R16-pickup-evolution-3-in-review-drop-artifact": "sha256:197a861f07746080595245007c358da0d1613c19d0f8a72fea91c085b9a3f872",
    "scenario:R16-pickup-evolution-4-done": "sha256:d26737780d5ebb99a3ae0afc552af97c282e1605bbd23df3341ee9acd5c3730e",
    "scenario:R16-support-adoption-drift": "sha256:33ef07dbb366437494a1247bce0444626aee60395a11df59d4fa73146fce4308",
    "scenario:R16-support-forward": "sha256:2eb7498e19ae8f6e6465e3b291fdce68498d7e90461ab0b7b4f1973b99c815d1",
    "scenario:R16-support-invalid-source": "sha256:ea29f88cfe864594d08adadc3c1d17406d2fe55f28af7fb767ae8f889e9c696d",
    "scenario:R16-support-nested-drop": "sha256:db17f56780ee0f42b76d0fd73732921b3153e7bba24a08b67459f85ea094a286",
    "scenario:R16-support-permutation-diamond": "sha256:51575a5d034d4971b8a4b0b63c7ffd315dfac66b8a259f3838206899a763adbc",
    "scenario:R16-support-reverse-drop": "sha256:9c9fb80a9a5bc32bd24461119a74fe3df417c6b996985962ec65972e1883ee60",
    "scenario:R16-support-reverse-preserved": "sha256:2eb7498e19ae8f6e6465e3b291fdce68498d7e90461ab0b7b4f1973b99c815d1",
    "scenario:R16-support-source-evolution": "sha256:2eb7498e19ae8f6e6465e3b291fdce68498d7e90461ab0b7b4f1973b99c815d1",
    "scenario:R17-carry-absent-arm": "sha256:2b36235d404f2e30de846c5ef434afe73bc7ce27b430dc48cd93062bc59c9403",
    "scenario:R17-carry-compatible": "sha256:4a0f93dc5e1fe684db1e62f38d5aea709a1eb086e5d36a0c1f57fb9faec10866",
    "scenario:R17-carry-compatible-reversed": "sha256:4a0f93dc5e1fe684db1e62f38d5aea709a1eb086e5d36a0c1f57fb9faec10866",
    "scenario:R17-carry-incompatible": "sha256:3d8bad52383985f3babc7220c73037474e80b36ea5333c15847024f9401202e0",
    "scenario:R17-carry-outside-duplicate": "sha256:46483c584c34860d9338b833bdc86937c67a4e2e8e01b9175f8c4b2316f5d230",
    "scenario:R17-carry-outside-single": "sha256:81c18794fb4209b8ae6cb2102eec4fb4f2b8b1e2ae8d61d1ef062f4cfd4dbc8b",
    "scenario:R17-outside-C-neutral-parent-valid-restack": "sha256:bda3673abdccea83e0a8ca4d22a4a3c1edc3c9e130a6bd7cfbf5250465806abb",
    "scenario:R17-persisted-outside-duplicate": "sha256:ff58edd51c5b1c689fee6f6221de0022adc49829287173d5ea58d04d9091fa35",
    "scenario:R17-persisted-outside-duplicate-reversed": "sha256:ff58edd51c5b1c689fee6f6221de0022adc49829287173d5ea58d04d9091fa35",
    "scenario:R17-persisted-outside-single": "sha256:d5a5cd78fc590781a325257a722e162c184046f7cb1266bb00a823d99a759501",
    "scenario:R17-persisted-outside-single-reversed": "sha256:d5a5cd78fc590781a325257a722e162c184046f7cb1266bb00a823d99a759501",
    "scenario:R17-persisted-unauthorized-absent-arm": "sha256:f4d241be4323e6dce40925b832f61714b2ac2153f6eaba225820c8a4218990cd",
    "scenario:R17-persisted-unauthorized-absent-arm-reversed": "sha256:f4d241be4323e6dce40925b832f61714b2ac2153f6eaba225820c8a4218990cd",
    "scenario:R17-persisted-valid-absent-arm": "sha256:e41aa6c81a7fa7e3c02c96e112c7d2e6fd01ed2918134676999b56d1df564241",
    "scenario:R17-persisted-valid-absent-arm-reversed": "sha256:e41aa6c81a7fa7e3c02c96e112c7d2e6fd01ed2918134676999b56d1df564241",
    "scenario:R17-precharge-P22-budget": "sha256:9c7bd9ae7aa964f30a7c4d0e577b6d57635feaaaaa71fb127f36e06215707b92",
    "scenario:R17-unreadable-outside-C-ancestor-stays-unopened": "sha256:17f6fd8afc206ca4e2b3964befab6447313e3770ecc5363974aa64dff65a3588",
    "scenario:R17-unreadable-outside-C-boundary": "sha256:e673018ad139d1a7f8ed888cc6c16f3c2e84e316fd4b059a68f3f29fabdff237",
    "scenario:R17-wide-outside-C-boundary-budget": "sha256:2867bc57efb2b0221bca74aafeaf358afc7a4d883b43c9bd073c476be3a904f9",
    "scenario:R3-01-two-invalid-causal-sources": "sha256:7c378db43468cac30ea7fce66d72d9de851c0f32b1d5c05bf24b1a8f93564d27",
    "scenario:R3-02-invalid-valid-causal-competition": "sha256:3b930f9cfb4fa87405f8ce377aa564122c3191280d9df81005e87fae4d4d5814",
    "scenario:R3-03-valid-supplier-plus-invalid-parent-at-N-blocks": "sha256:e3acfdb297fb6ce6c9d9a7d3c0baaa924cd6cac13bf459b55b488c0f43774ad6",
    "scenario:R4-01-same-root-valid-diamond": "sha256:891a1f2c942a00a5753b1d9d26147294e4ee5733ca1b7f3eadad38b27018f325",
    "scenario:R4-02-distinct-valid-root-diamond": "sha256:cb7fde6b9985018f94e8413ed82b19967247b87bbd7e13fc03072c6892acd208",
    "scenario:R4-03-equal-root-plus-invalid-diamond": "sha256:9c3a634056f76695bc84a64af33420a8b102899b7d6c29ffe2d3add9d000e55d",
    "scenario:R5-01-invalid-redelete-after-supplier-reintroduction": "sha256:da16e53f0f9ae04416789ee89801ec4a84edbb8a3655e92ea7a5795309f06fec",
    "scenario:R5-02-valid-redelete-after-supplier-reintroduction": "sha256:1acf1c491fd554e63c8d60a8b16dd2f82a22da4e7286f24b13c7042246f9f1b4",
    "scenario:R6-01-valid-plus-invalid-all-absent": "sha256:c429b988ca123c5143c4b2cbdaa146a01a4109cbf725157caa57bcd1d8310cdf",
    "scenario:R6-02-valid-plus-ambiguous-all-absent": "sha256:dd79df51b4a874bb0ded5274030b377219c00cd8ce2fd5e67cb0a0400ca6e731",
    "scenario:R6-03-two-invalid-all-absent": "sha256:5d9698b080641a9099a1866a566a72a523839ed6a99d5321e154d4c35a159d18",
    "scenario:R6-04-same-valid-root-all-absent-wrappers": "sha256:72ea57333c828a357c0a98edfd5ffc54efac83ca74c845e764f1a2c2593dc0a9",
    "scenario:R8-direct-human-response-conflict": "sha256:4bd8010dbf13661aa4d59be70c723e610674cd72764ba1d4b6ef6810a8b14f90",
    "scenario:R8-direct-human-response-identical": "sha256:4bd8010dbf13661aa4d59be70c723e610674cd72764ba1d4b6ef6810a8b14f90",
    "scenario:R8-review-binding-divergent": "sha256:96c0541d4d19623284d5dfddbe84a3c07712fd3ff697b3133bcf190661f45e07",
    "scenario:R8-review-binding-identical": "sha256:d5e167d6454eead0aa2a088556b0b86e996819181ccf79464b03f850822b01d7",
    "scenario:R8-review-binding-terminal-conflict": "sha256:e984e1d561ccdcf64edbaec1a63682f7caf0c2d8c6295b466163f28bb4ae89e4",
    "scenario:R8-supplier-human-response-conflict": "sha256:d8b11bd684f85a55b66ca1e6b140442d7c42c0dd131079a582957d92eb0b752a",
    "scenario:R8-supplier-human-response-identical": "sha256:ec79fc727033970fcf46b1fc8c58155967c630152b2efbe5e6db142bb52fe713",
    "scenario:R9-direct-review-revision-pending-fill": "sha256:c33593ea512f318b1ab2245804f0d06dcfae4761e14c6b619ffd37cc768af74e",
    "scenario:R9-direct-review-target-pending-fill": "sha256:c33593ea512f318b1ab2245804f0d06dcfae4761e14c6b619ffd37cc768af74e",
    "scenario:R9-supplier-review-revision-pending-fill": "sha256:d917492aa1b894b51e47ecce7aa3cc0757c60c8de1851328242aeddd11e97dde",
    "scenario:R9-supplier-review-target-pending-fill": "sha256:d917492aa1b894b51e47ecce7aa3cc0757c60c8de1851328242aeddd11e97dde",
    "scenario:W0-fast-forward-return": "sha256:edc44c732d297925125d6452e8bf153ed77fc230e40d502615297e011788f671",
    "scenario:W1-pre-PR-push-exact-endpoints": "sha256:942ab6af246282eabbbfe25bba5bec68790db7a1809dbf5a6f97e3c695b90574",
    "scenario:W2-base-advance-retarget-invariant": "sha256:461aecac9b5e2c60cd7230d2c88e6921e17c0963b8a0e21cce6ecabf847a8a91",
    "scenario:W3-multiple-PR-API-zero-calls": "sha256:a408175b54af46684a7ef5bf452f18597223c8ec93715b25b5dfcd51313b2572",
    "scenario:W4-stale-rerun-exact-inputs": "sha256:bc502957024f6c6be437996e2a4885a627fef4f0702963cb16e849117ff86c46",
    "scenario:W5-missing-O-coverage-unavailable": "sha256:0636fb6f185403300874dbe5800c7c32c1a91f5547d8c0fbfaf4652936993305",
    "scenario:W6-created-deleted-zero-endpoints": "sha256:19cbca9efc9f9260ed57f369cd02425dff1db1e4db458bde21b7f8ebb72a9396",
    "scenario:W7-PR-synchronize-top-level-endpoints": "sha256:cbdc63d66cdd0476712d63d55f891ed3f182bd71fb5eb795be1b62edd2e21cb4",
    "summary": "sha256:74a7f9e3ab72663556d8c067e825e9ac744fd232524bfcbd337a2e8fd7fce00b",
}


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
    if row["control"] == "posthoc-budget-accounting":
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
        "precharge_expected_metrics": row["details"][
            "precharge_expected_metrics"
        ],
        "record_sha256": record_digest(normalized_record(row)),
        "transactional_zero_results": zero_partial_result(row),
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
                        "graph_parent_edges",
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
                "locale-git-error-stream-equality",
                "posthoc-budget-accounting",
            }
            and row["damaged_classification"] == row["expected_baseline"]
        ):
            raise EvidenceError(f"{context} damage did not change verdict")
        if row["id"] == "posthoc-budget-accounting":
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
        "measured_budget", "parent_permutation", "persisted_carry",
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
            "graph_commits", "graph_parent_edges", "object_reads",
            "queue_snapshots_requested",
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
            "limit": 7,
            "overflow_classification": "budget-exceeded",
            "transactional_zero_results": True,
        }
        or wide["metrics"] != {
            "graph_commits": 4,
            "graph_parent_edges": 8,
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
        f"Evidence schemas v2 at commit `{core['evidence_supersession']['artifacts'][0]['commit']}` and v3 at commit `{core['evidence_supersession']['artifacts'][1]['commit']}` are superseded and burned by their later semantic/evidence blockers; both histories are preserved, neither identifier is reused, and this artifact closes `{core['evidence_supersession']['replacement_schema']}`.", "",
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
        f"The 64-parent outside-C octopus exits 2 transactionally and is record-bound by `{core['measured_budget']['wide_boundary']['record_sha256']}`; no action, edge, support, or carry-proof result leaks past the exceeded parent-edge budget.",
        f"The P22 pre-charge case stops exactly at `object_reads=134>133`, keeps Git processes at {core['measured_budget']['precharge_P22']['precharge_expected_metrics']['git_processes']}, freezes later counters, and is record-bound by `{core['measured_budget']['precharge_P22']['record_sha256']}`; its post-hoc damage reproduces the prior 10,973-snapshot/24,736-cache-hit full run.",
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
              f"The 64-parent boundary case measures {wide_budget['metrics']['graph_commits']} intrinsic graph commits and {wide_budget['metrics']['graph_parent_edges']} parent edges against limit {wide_budget['budget_contract']['limit']}; parent-edge work is therefore metered even while graph commits remain below the limit.", "",
              f"PCX-19 is replay-bound by `{p19['record_sha256']}`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.", "",
              "## Reproducible audit", "",
              "Use two fresh, empty scratch roots:", "", "```sh",
              "PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-v4-seed1 > /tmp/production-contract-r17-v4-seed1.jsonl",
              "PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-v4-seed777 > /tmp/production-contract-r17-v4-seed777.jsonl",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-v4-seed1.jsonl --compare /tmp/production-contract-r17-v4-seed777.jsonl",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-v4-seed1.jsonl --damage-test",
              "python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --old FULL_OID_O --new FULL_OID_N",
              "python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py",
              "python3 automation/run_tests.py", "python3 automation/reconcile/reconcile.py --check", "```", "",
              "The auditor requires raw and semantic equality for comparison, rejects",
              "duplicate keys/IDs, enforces a static recursive raw key/list/type grammar",
              "before projection, compares a fresh",
              "manifest byte-for-byte, and regenerates this README in full. Its damage",
              "matrix covers invented/duplicate/missing rows, same-region OID swaps, tuple",
              "relabels, false verdicts/counters, contradictory transcripts/digests,",
              "unknown raw fields/cost rows, locale error drift, post-hoc budget work,",
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
