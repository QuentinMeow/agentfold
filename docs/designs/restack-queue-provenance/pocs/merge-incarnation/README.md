# Merge-incarnation supplier-witness POC

## Result

**VERIFIED:** the supplier-witness shape survived the 12 common scenarios and 11
additional merge, incarnation, object-boundary, and cost attacks: 23 of 23 expected
verdicts matched. It correctly accepted a legitimate linear resolution and an inherited
resolution behind a merge, while it blocked an invalid base deletion, a genuine old-tip
loss, mixed valid/invalid supplier edges, delete/recreate/delete ambiguity, merge-only
action creation, duplicate rename state, criss-cross history, and incomplete objects.

The safe rule is narrower than “find any valid deletion.” It is:

1. establish that the old task lineage left one exact action incarnation unchanged;
2. inspect every parent edge in candidate-only history;
3. validate the concrete deletion edge against its committed claim and changed
   non-queue evidence;
4. collapse a merge's synthetic parent deletion only when an absent sibling contains a
   prior validated deletion in its ancestry; and
5. accept only one unambiguous effective witness.

This POC deliberately fails closed on a merge commit that authors a deletion relative to
two carrying parents, even if both parent edges validate. That conservative result is a
real product tradeoff, not proof that such a merge is invalid.

## Method

The prototype is independent of AgentFold's production reconciler. It uses the Python
standard library and Git 2.55.0 to create disposable repositories with deterministic
commit dates. Every Git inspection uses `--no-replace-objects`. Queue actions in the
fixtures have an explicit immutable fingerprint over a synthetic action id, evidence
binding, and payload; status is mutable. The classifier:

- rejects shallow repositories, unavailable/non-commit tips, unrelated tips, and
  multiple merge bases before attribution;
- compares the old action with the unique common-boundary incarnation;
- scans commits reachable from `N` but not `O`, including every merge-parent edge;
- follows an incarnation across an unambiguous rename;
- requires a committed `open -> in-repair` edge and evidence bytes changed on the
  real deletion edge; and
- prints one JSON line per scenario with full `C`, `O`, `M`, and `N` OIDs,
  edge OIDs, witness cardinality, evidence verdict, expected result, measured work, and
  a human explanation.

## Verified evidence

Exact command, run from the unit worktree:

```sh
python3 docs/designs/restack-queue-provenance/pocs/merge-incarnation/prototype.py --self-test
```

Environment and source:

```text
Python 3.14.7
git version 2.55.0
a15d65ab52037f41d0363fc1cdfd2c8a2c08c48d5641632405cf641b13680c45  docs/designs/restack-queue-provenance/pocs/merge-incarnation/prototype.py
```

The clean run printed 23 scenario JSON objects and ended exactly with:

```json
{"failed": 0, "git": "git version 2.55.0", "passed": 23, "python": "3.14.7", "summary": "merge-incarnation-poc", "total": 23}
```

Exit status: `0`.

The common matrix produced these outcomes:

| Scenario | Result | Witnesses | Operator meaning |
|---|---|---:|---|
| S1 valid base resolution | no finding | 1 valid | selected base resolved the unchanged action |
| S2 invalid base deletion | finding | 1 invalid | base deleted it without a committed claim |
| S3 branch-owned loss | finding | 0 | old task lineage introduced the action |
| S4 changed action | finding | 0 | base resolution addressed a different incarnation |
| S5 mixed actions | exactly Q2 finds | 1 for Q1 | inherited Q1 resolution and old-side Q2 loss stay independent |
| S6 same-path concurrency | finding | 0 | identical path does not erase changed identity |
| S7 unrelated restack | no finding | 0 | one exact live incarnation remains |
| S8 fast-forward | no finding | 0 | no divergent continuity edge exists |
| S9 missing, non-commit, unrelated | fail closed | 0 | provenance cannot be attested |
| S10 pre-v1 old action | finding | 0 | later activation cannot erase old-side authorship |
| S11 rename carry / delete | no finding | 0 / 1 | one fingerprint follows the permitted successor path |
| S11 duplicate rename | finding | 0 | two copies make identity ambiguous |
| S12 merge-shaped new base | no finding | 1 valid | the absent sibling contains the real valid resolution |

The important S12 OIDs and edge result were:

```text
C=547e3492f1cd1090959668805b9df6e8d0ca490c
O=d762fd79f0f6a9d4e08d84511b86a359e2b4c63b
M=d1e3864423cdd4df1b0b9ba7759c60df9d1eede0
N=2b523657e28d9b668e2a7dbdee129aa7c0e1027f
real valid edge=838cd8c1e4b26f9f3767884b2209398268e72ffa->e3aed5c9f4f71f05e11fb71d4f456c48e17ae553
synthetic merge edge=ae6b09b0ae577679be695d7b5eb2f31a0b13ad09->d1e3864423cdd4df1b0b9ba7759c60df9d1eede0
synthetic edge verdict=invalid, ignored only because the valid edge is an ancestor of the absent sibling
```

### Observed-red control

The run-scratch driver changes S1's expected result from `no-finding` to
`finding` without changing the classifier:

```sh
python3 /Users/quentinmiao/code/agentfold/.git/agents/runs/2026-08-31-prove-the-correct-restack-queue-201c/scratch/merge-incarnation-poc/negative_control.py \
  docs/designs/restack-queue-provenance/pocs/merge-incarnation/prototype.py
```

It ended exactly with:

```json
{"failed": 1, "git": "git version 2.55.0", "passed": 0, "python": "3.14.7", "summary": "merge-incarnation-poc", "total": 1}
```

Exit status: `1`. This verifies mismatch detection; it does not verify production test
discovery.

## Strongest counterexamples

### Any-valid-witness is unsafe

**VERIFIED:** delete/recreate/delete produced two independently valid deletion edges for
the same byte-identical fingerprint. Accepting because at least one valid edge exists
would allow an older resolution to excuse a later incarnation. The exact record was:

```json
{"C": "547e3492f1cd1090959668805b9df6e8d0ca490c", "M": "bee01bc98754157028b6b77026f8cf4ceda22f63", "N": "d912b50f5d97175444e459d1526534af2775f372", "O": "d762fd79f0f6a9d4e08d84511b86a359e2b4c63b", "actual_result": "finding", "authoring_lineage": "candidate resolution is absent or ambiguous", "classification": "finding", "evidence_verdict": "ambiguous: 2 valid of 2 witnesses", "expected_result": "finding", "scenario": "A3-delete-recreate-delete", "witness_cardinality": 2}
```

### Parent-edge cardinality can be conservatively noisy

**VERIFIED:** a merge commit that deleted the action relative to two parents produced two
valid edges to the same child and therefore failed closed. Grouping them into one
merge-authored event could reduce the false positive, but no authority for that grouping
has been proven. Until it is, exact-one parent-edge cardinality is safe and conservative.

### A valid sibling must not hide an invalid competitor

**VERIFIED:** merging one valid-deletion branch and one invalid-deletion branch produced
two effective witnesses, one valid and one missing the claim. The result stayed blocking.
Only the S12 synthetic merge edge was collapsed, because its absent sibling contained a
prior validated edge; the competing invalid edge was never collapsed.

### Final bytes do not identify an incarnation

**VERIFIED:** two successor paths containing the same fingerprint were ambiguous, and a
delete/recreate sequence stayed ambiguous even when the final bytes matched. Path absence,
final-tree equality, and a content hash alone are therefore insufficient.

## Cost

The small S12 merge case used 26 Git processes and 7 cached queue-tree reads. The
128-unrelated-commit probe used 404 Git processes and 133 cached queue-tree reads, taking
2164.316 ms in the recorded run:

```json
{"actual_result": "no-finding", "elapsed_ms": 2164.316, "git_processes": 404, "history_commits": 128, "scenario": "P1-long-history-cost", "tree_reads": 133, "witness_cardinality": 1}
```

**INFERENCE:** the prototype is linear in candidate history for one item, but its
one-process-per-parent/tree/blob implementation has an unacceptable constant factor.
With `H` candidate commits, `Q` queue items per tree, and `W` candidate witnesses,
the naive work is `O(H*Q + W*H)`; immutable caches avoid rereading parsed snapshots but
do not avoid subprocess creation. A production implementation should reuse the
reconciler's object/parent/blob caches, path-filter early without hiding merges, and use
batched Git object reads. No performance shortcut may turn unreadable history into
absence.

## Independent comparison

These neighboring commands were independently rerun from their isolated worktrees:

```sh
python3 docs/designs/restack-queue-provenance/pocs/edge-witness/prototype.py --self-test
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py --self-test
```

Observed summaries:

```text
{"git":"git version 2.55.0","passed":16,"python":"3.14.7","summary":"PASS","total":16}
replay-oracle self-test: 7/7 scenarios passed
```

**VERIFIED:** the production-shaped edge-witness POC and this independent model agree on
S1/S2/S3/S5/S7/S8/S9/S10 and repeated-incarnation fail-closed behavior. This POC adds
the merge-parent, S6, S11, S12, competing-supplier, criss-cross, and longer cost attacks.

**VERIFIED negative control:** the replay oracle showed both S1 and S2 replay cleanly and
match their candidate trees even though their evidence verdicts differ. It also showed
that non-merge patch comparison omits a merge-commit-only action. Replay is useful
operator diagnosis, not resolution authority.

## Inference and proposal

**INFERENCE:** the best surviving production direction is the production-shaped
edge-witness approach augmented with this POC's incarnation cardinality and merge-sibling
rules. It has stronger fidelity to AgentFold's actual parser and lifecycle validator than
this standalone model and measured fewer Git processes on its shorter long-history case.

**PROPOSAL:** production return values should be explicit:

- `valid(edge, reason)`: exactly one real edge resolves the inherited incarnation;
- `invalid(edge, problem)`: a real deletion exists but fails lifecycle/evidence;
- `none`: the old-side obligation has no candidate resolution;
- `ambiguous(edges, reason)`: duplicates, repeated incarnation, competing suppliers, or
  unproven merge grouping;
- `unreadable(error)`: missing, shallow, unrelated, or multiple-base history.

Human-facing findings can then say whether the task authored the loss, the base deleted
without authority, two histories compete, or more Git history is required. This is more
actionable than always accusing the restacked task.

## Non-claims

- This POC changes no production reconciler, hook, test, queue item, or task record.
- Its synthetic `Action-ID` and payload fingerprint are not an AgentFold schema proposal.
  Production must reuse the repository's real queue identity, timing-move, review, and
  mutation rules; an arbitrary rename must not become permitted because this fixture can
  follow it.
- Changed evidence bytes prove structural change, not truthful or sufficient human
  evidence. This POC does not solve semantic evidence laundering.
- S12 proves one constructed sibling-supplied merge. It does not prove every octopus,
  criss-cross, replace-object, or partial-clone topology. Multiple merge bases and shallow
  history intentionally fail closed here.
- The merge-only deletion false positive is not resolved. Grouping multiple parent edges
  into one event requires a separately proven authority rule.
- The 23/23 self-test is POC evidence only. It does not establish integration with
  `check_queue_resolution`, production regression discovery, full-suite correctness,
  cold-clone behavior, or acceptable production performance.
