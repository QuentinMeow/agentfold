# Merge-incarnation supplier-witness POC

## Result

**VERIFIED:** the supplier-witness shape survived the 12 common scenarios and 20
additional merge, incarnation, object-boundary, and cost attacks: 32 of 32 expected
verdicts matched. It correctly accepted a legitimate linear resolution and an inherited
resolution behind a merge, while it blocked an invalid base deletion, a genuine old-tip
loss, mixed valid/invalid supplier edges, delete/recreate/delete ambiguity, merge-only
action creation, byte-identical old-side delete/recreate, cross-occurrence claim reuse,
ambiguous merge provenance, a conflicting same-ID merge sibling, post-witness
reintroduction, duplicate rename state, criss-cross history, and incomplete objects.

A fresh verifier rejected the earlier 23/23 version because it compared only the common
and old-tip snapshots. A branch could delete the action and recreate identical bytes
before `O`; final snapshots matched, so a candidate resolution of the common incarnation
was incorrectly accepted. The repaired prototype now proves continuous old-side identity
across every parent edge from the boundary to `O`.

A second fresh verifier rejected the repaired 26/26 version because claim discovery
still scanned every ancestor carrying the same fingerprint. An earlier occurrence could
be claimed and deleted, then a byte-identical action could be recreated already
`in-repair`; deleting the second occurrence borrowed the first occurrence's claim. The
prototype now walks backward only through the occurrence continuously present at the
deletion parent and stops at absence, recreation, another incarnation, or ambiguous
identity.

A third fresh verifier rejected the repaired 28/28 version because its bounded walk
still accepted a claim from any merge parent. One parent continuously carried the
claimed occurrence; another deleted it and recreated byte-identical `in-repair` bytes
without a claim. The merge looked identical, and the first parent's receipt excused the
second parent's reincarnation. The prototype now requires every carrying parent lineage
to reach one shared claim edge, and it requires a witnessed absence to stay absent on
every descendant path to `N`.

A fourth fresh verifier rejected the repaired 31/31 version because edge validation
looked only at the selected deletion parent. A second merge parent independently created
a different payload and path under the same Action-ID, then the merge deleted both. The
selected parent had a legal claim, so the conflicting sibling was mistaken for absence.
The prototype now scans every candidate commit and every direct parent, including after
a witness. Every same-ID state must belong to the continuously inherited occurrence;
different content, duplication, recreation, or disconnected provenance fails closed.

The safe rule is narrower than “find any valid deletion.” It is:

1. establish that the old task lineage left one exact action incarnation unchanged;
2. prove that incarnation stayed present, unique, and byte-stable on every old-only
   parent edge;
3. inspect every parent edge in candidate-only history;
4. prove every same-ID state in the candidate graph and every merge sibling is either
   the same continuously inherited occurrence or a real absence;
5. prove every carrying parent of the deletion-parent occurrence reaches the same claim
   edge without absence, recreation, mutation, duplicate identity, or ambiguous rename;
6. validate the concrete deletion edge against changed non-queue evidence;
7. prove the action stays absent on every descendant path from that witness to `N`;
8. collapse a merge's synthetic parent deletion only when an absent sibling contains a
   prior validated deletion in its ancestry; and
9. accept only one unambiguous effective witness.

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
- walks every old-only parent edge and rejects a missing, duplicated, mutated, or
  discontinuous incarnation even when the final bytes match;
- scans commits reachable from `N` but not `O`, including every merge-parent edge;
- follows an incarnation across an unambiguous rename;
- bounds claim discovery to the exact continuously present occurrence at the deletion
  parent, then requires a committed `open -> in-repair` edge inside that occurrence and
  evidence bytes changed on the real deletion edge;
- recursively proves all carrying merge parents converge on one shared claim source;
- rejects a same-ID candidate or sibling state unless its continuous backwards component
  intersects the inherited occurrence at `C`;
- invalidates a witness if the action reappears anywhere on a descendant path to `N`;
  and
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
b66cc1e26e14a57eca709dc35115bce710f0e435f4f480c523e99a627dbf75c3  docs/designs/restack-queue-provenance/pocs/merge-incarnation/prototype.py
8eab83888d7f614783213e57e182336c9eaa610965a538139a2883d0f3931361  docs/designs/restack-queue-provenance/pocs/merge-incarnation/production_helper_probe.py
```

The clean run printed 32 scenario JSON objects and ended exactly with:

```json
{"failed": 0, "git": "git version 2.55.0", "passed": 32, "python": "3.14.7", "summary": "merge-incarnation-poc", "total": 32}
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
| A6 old delete/recreate | finding | 0 | equal final bytes do not prove continuous incarnation |
| A7 old mutation/revert | finding | 0 | restoring bytes does not erase an identity mutation |
| A8 old duplicate/collapse | finding | 0 | restoring one path does not erase earlier ambiguity |
| A9 cross-occurrence claim reuse | finding | 1 invalid | a prior occurrence's claim cannot authorize this deletion |
| A10 recreated occurrence own claim | no finding | 1 valid | a claim after recreation authorizes only the current occurrence |
| A11 ambiguous merge occurrence | finding | 1 invalid | one carrying parent's claim cannot authorize a reincarnated sibling |
| A12 shared occurrence merge | no finding | 1 valid | both carrying parents converge on the same claim edge |
| A13 post-witness reintroduction | finding | 2, first invalid | the first absence did not remain continuous to `N` |
| A14 conflicting same-ID sibling | finding | 1 invalid | a claimed parent cannot hide a different sibling incarnation |

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

### Observed-red controls

The run-scratch driver disables `old_lineage_continuity_problem` and runs only A6.
It leaves A6's expected `finding` unchanged, so the runner must collect the new
old-lineage assertion to stay green:

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

The second run-scratch driver restores the rejected unbounded ancestor scan and runs
only A9:

```sh
python3 /Users/quentinmiao/code/agentfold/.git/agents/runs/2026-08-31-prove-the-correct-restack-queue-201c/scratch/merge-incarnation-poc/claim_negative_control.py \
  docs/designs/restack-queue-provenance/pocs/merge-incarnation/prototype.py
```

It changed A9 from the expected `finding` to `actual_result=no-finding`, then ended:

```json
{"failed": 1, "git": "git version 2.55.0", "passed": 0, "python": "3.14.7", "summary": "merge-incarnation-poc", "total": 1}
```

Exit status: `1`. This is the observed-red proof that the current-occurrence boundary,
not merely the scenario expectation, prevents cross-boundary claim reuse.

The third run-scratch driver disables only `dag_occurrence_continuity_problem` and runs
only A11:

```sh
python3 /Users/quentinmiao/code/agentfold/.git/agents/runs/2026-08-31-prove-the-correct-restack-queue-201c/scratch/merge-incarnation-poc/merge_negative_control.py \
  docs/designs/restack-queue-provenance/pocs/merge-incarnation/prototype.py
```

The unchanged bounded any-parent lookup borrowed parent one's claim, changed A11 from
the expected `finding` to `actual_result=no-finding`, and ended:

```json
{"failed": 1, "git": "git version 2.55.0", "passed": 0, "python": "3.14.7", "summary": "merge-incarnation-poc", "total": 1}
```

Exit status: `1`. This proves the DAG-wide shared-occurrence guard, rather than the
linear occurrence boundary, blocks the ambiguous merge.

The fourth run-scratch driver disables only `sibling_incarnation_problem` and runs only
A14:

```sh
python3 /Users/quentinmiao/code/agentfold/.git/agents/runs/2026-08-31-prove-the-correct-restack-queue-201c/scratch/merge-incarnation-poc/sibling_negative_control.py \
  docs/designs/restack-queue-provenance/pocs/merge-incarnation/prototype.py
```

The legal selected parent again hid the conflicting same-ID sibling, changing A14 from
the expected `finding` to `actual_result=no-finding`. It ended exactly with:

```json
{"failed": 1, "git": "git version 2.55.0", "passed": 0, "python": "3.14.7", "summary": "merge-incarnation-poc", "total": 1}
```

Exit status: `1`. This proves the candidate-wide sibling-incarnation guard, not the
claim, evidence, or witness-cardinality checks, blocks the counterexample.

### Production-helper probe

This command invokes the unchanged production `claimed_lifecycle_problem` on the linear,
ambiguous-merge, and conflicting-sibling attacks, then applies the POC guards:

```sh
python3 docs/designs/restack-queue-provenance/pocs/merge-incarnation/production_helper_probe.py
```

It ended exactly with:

```json
{"failed": 0, "passed": 5, "summary": "production-claim-helper-probe", "total": 5}
```

Exit status: `0`. **VERIFIED:** the production helper rejected the already-claimed
recreation with `no committed one-line open -> in-repair claim transition exists`, and
accepted the control whose recreated occurrence had its own claim. But the raw helper
also **accepted the ambiguous merge attack**: it borrowed the continuously carrying
parent's claim and ignored the sibling's delete/recreate boundary. The new guard blocked
that same fixture; both helper and guard accepted the shared-occurrence merge control.
The raw helper also accepted the selected parent in A14 without inspecting the conflicting
sibling; the candidate-wide sibling guard blocked that fixture.

Therefore the raw production helper is necessary but insufficient for merge provenance.
Production integration must wrap it with both an all-carrying-parent shared-occurrence
proof and a candidate-wide same-ID sibling proof, or fix the helper to provide those
proofs itself, and must also verify post-witness absence continuity to `N`. This probe
does not claim the surrounding production restack path has any of those guards today.

## Strongest counterexamples

### A selected deletion parent cannot hide a conflicting sibling

**VERIFIED:** `R` had no action. `C` added inherited A under Action-ID Q; the old feature
and a valid candidate parent descended from `C`, and the valid parent claimed A. A foreign
parent forked from `R` and independently added B under Q with another path and payload but
no claim. The merge deleted both and changed evidence. Before the repair, validating only
the selected A parent returned `no-finding`; the sibling guard now rejects B:

```text
R=9234a60704facc86562706d53e7c8e219b7dd130
C=66f01e656d385f24dd4df2d11f21291d6f191610
O=40c9a7458bc6bc8b9949211e601f16fcbe8baa50
valid parent=fcb3fcda5b864eb9a65538c6f8730e37b9c61d6a
foreign parent=df1979f625e5e0432b3468e815e10e6b6119038d
M=1bb5633400e0648c566c4b993a4bdeb864fdcea9
N=a49ef6fe815940f2e093c570391e6cb9aa836422
result=finding: candidate graph contains conflicting same-ID incarnation at foreign parent
```

Disabling only the sibling guard produced the original valid witness and `no-finding`
for the same OIDs. Existing S12 and A12 are positive controls: an absent sibling is
allowed, and exact siblings sharing the inherited continuous occurrence remain accepted.

### A merge needs one claim shared by every carrying parent

**VERIFIED:** Q was claimed, then forked. Parent one continuously carried that
occurrence. Parent two deleted it and recreated byte-identical `in-repair` bytes without
its own claim. The merge carried Q, and a later commit changed evidence and deleted it.
An any-parent walk accepted parent one's receipt; the DAG guard rejected parent two's
unclaimed boundary:

```text
shared claim=98c78762d2e4a3e02cd038bf7874ca7672637ba1
parent one=48ce8253c26ecfcb0e92a41cda69a6d2067bdbed
parent two=94ec28b3d90ec297842cc3d4c6279f643e7f8875
C=48297b46a0e8a3681644f3ed4cb27855cd05f362
O=16920ae68ebbbe034d9a19131ae25d58367d29af
M=db9a4ce826e9fe47916b2a23b5ee8f123971aa23
N=f268f32f6978b6ca033b8cdc26d974f189932ab7
result=finding: merge occurrence has a carrying parent without one claim source
```

Disabling only the DAG guard made those same OIDs false-green. A12 is the positive
control: both carrying parents remained continuous from the same claim and the deletion
stayed valid.

### A claim receipt belongs to one continuously present occurrence

**VERIFIED:** occurrence 1 moved `open -> in-repair -> absent`. Occurrence 2 was
recreated at `C` already `in-repair` with the same fingerprint and exact claimed bytes.
The candidate changed evidence and deleted occurrence 2. The bounded classifier stopped
at the absent parent of `C` and rejected the candidate deletion:

```text
occurrence-1 open=547e3492f1cd1090959668805b9df6e8d0ca490c
occurrence-1 claim=043bc81eb1487728652d3a3b20b599afa2585f0d
C=7ba9b8f974e9f602d500edd31976005ba4fb7345
O=99c6bf0d84d0fe90a63f19fe75957d01664bbbef
M=4b2acd176b7aa0cb9b05240fb702903f935cb46f
N=65d45a46288c9f002841711e454d39c96d04ab42
result=finding: no committed open-to-in-repair claim exists in the current occurrence
```

Restoring the old all-ancestor fingerprint scan made the same OIDs false-green. A10 is
the positive control: after the recreation, its own `open -> in-repair` commit was found
and the deletion remained valid.

### Equal endpoint bytes do not prove continuity

**VERIFIED:** `C` carried Q; the old lineage deleted Q, recreated byte-identical Q,
and then produced `O`. The candidate legally resolved the original common incarnation.
Before the repair, matching endpoint snapshots produced a false exemption. After the
repair, the classifier found this old-only edge and blocked before candidate evidence:

```text
C=547e3492f1cd1090959668805b9df6e8d0ca490c
O=f2771df701311f93a85e16caaec8a9e592c3a7c8
M=4cfa643a038fef4d32673fffad19bc93c6d4e83b
N=c60e59f9d0b2e90f1c464570140b95f1557bbfad
discontinuous edge=b70bfb02d360132d08d977c6270a5d414ffc1bc4->beafabb544e3cf6aae68b77455eb73a9341ce10a
result=finding: old-side discontinuous incarnation
```

With the guard disabled, the same OIDs produced `actual_result=no-finding` against
`expected_result=finding`, and the observed-red driver exited 1.

### Any-valid-witness is unsafe

**VERIFIED:** delete/recreate/delete produced two deletion edges for the same
byte-identical fingerprint. The later edge validated; the earlier edge was invalidated
because its absence did not remain continuous. Accepting because at least one reachable
valid edge exists would let an older resolution excuse a later incarnation. The exact
record was:

```json
{"C": "547e3492f1cd1090959668805b9df6e8d0ca490c", "M": "bee01bc98754157028b6b77026f8cf4ceda22f63", "N": "d912b50f5d97175444e459d1526534af2775f372", "O": "d762fd79f0f6a9d4e08d84511b86a359e2b4c63b", "actual_result": "finding", "authoring_lineage": "candidate resolution is absent or ambiguous", "classification": "finding", "evidence_verdict": "ambiguous: 1 valid of 2 witnesses", "expected_result": "finding", "scenario": "A3-delete-recreate-delete", "witness_cardinality": 2}
```

**VERIFIED post-witness case:** A13 made a valid deletion, then a merge reintroduced the
action before a final deletion. The first edge was explicitly invalidated with `action
reappears after the deletion witness`; an earlier reachable valid edge therefore cannot
serve as authority unless its absence stays continuous to `N`.

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

The small S12 merge case used 29 Git processes and 7 cached queue-tree reads. The
128-unrelated-commit probe used 407 Git processes and 133 cached queue-tree reads, taking
1749.303 ms in the recorded run:

```json
{"actual_result": "no-finding", "elapsed_ms": 1749.303, "git_processes": 407, "history_commits": 128, "scenario": "P1-long-history-cost", "tree_reads": 133, "witness_cardinality": 1}
```

**INFERENCE:** the prototype is linear in old and candidate history for one item, but its
one-process-per-parent/tree/blob implementation has an unacceptable constant factor.
With `L` old-only commits, `H` candidate commits, `Q` queue items per tree, and
`W` candidate witnesses, the naive work is `O((L+H)*Q + W*H)`; immutable caches avoid
rereading parsed snapshots but do not avoid subprocess creation. A production
implementation should reuse the
reconciler's object/parent/blob caches, path-filter early without hiding merges, and use
batched Git object reads. No performance shortcut may turn unreadable history into
absence.

## Independent comparison

No neighboring POC was executed from this isolated worktree. Their prototype files are
not present here. These exact checks both returned exit status `1`:

```sh
test -f docs/designs/restack-queue-provenance/pocs/edge-witness/prototype.py
test -f docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py
```

The main agent relayed earlier results from the owning worktrees:

```text
{"git":"git version 2.55.0","passed":16,"python":"3.14.7","summary":"PASS","total":16}
replay-oracle self-test: 7/7 scenarios passed
```

**RELAYED, NOT REVERIFIED HERE:** the earlier production-shaped edge-witness POC and this
independent model reportedly agree on S1/S2/S3/S5/S7/S8/S9/S10. Its relayed 16/16 run is
not sufficient evidence for the later merge-reintroduction or conflicting-sibling cases.
This POC independently exercises those guards alongside the merge-parent, S6, S11, S12,
competing-supplier, criss-cross, and longer cost attacks.

**RELAYED, NOT REVERIFIED HERE:** the replay-oracle owner reported that both S1 and S2
replay cleanly and match their candidate trees even though their evidence verdicts
differ, and that non-merge patch comparison omits a merge-commit-only action. If retained
after integration verification, replay is operator diagnosis, not resolution authority.

## Inference and proposal

**INFERENCE:** the best surviving production direction is the production-shaped
edge-witness approach augmented with this POC's incarnation cardinality and merge-sibling
rules. It has stronger fidelity to AgentFold's actual parser and lifecycle validator than
this standalone model and measured fewer Git processes on its shorter long-history case.
The verified production-helper probe means its linear occurrence boundary remains
useful, but its any-parent merge result and selected-parent scope are not sufficient.
Integration must wrap or fix it with the shared-claim DAG proof and the candidate-wide
same-ID sibling proof, then select the causal deletion parent, prove old-side continuity,
prove post-witness absence, and retain witness cardinality.

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
- The 32/32 self-test is POC evidence only. It does not establish integration with
  `check_queue_resolution`, production regression discovery, full-suite correctness,
  cold-clone behavior, or acceptable production performance.
