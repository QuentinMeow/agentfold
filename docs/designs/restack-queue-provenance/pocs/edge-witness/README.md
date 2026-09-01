# Exact candidate-side deletion witness POC

This POC proves that a restack can stop blaming a task for a base-owned resolution
without excusing an unauthorized deletion; nobody needs to act on this POC alone,
because it changes no production behavior.

Before this prototype, the continuity check saw only the synthetic displaced-tip to
candidate edge, so a legitimate base resolution and a lost action both looked like one
path deletion. The prototype now finds the candidate-only parent/child edge that actually
deleted the same action, then asks the reconciler (the script that checks repository
invariants) to validate the claim and evidence on that real edge. Twenty-three real-Git
scenarios passed, including the reported good restack, three missing-history failures,
deletion at the candidate head, activation laundering, and synthetic-edge evidence
laundering. Six executable controls also passed, including four observed-red reproductions
of verifier-found incarnation bugs. The prototype deliberately fails closed on repeated
incarnations, so it is evidence for a design direction rather than production code.

## Result

**VERIFIED:** the exact command below exited 0 on 2026-08-31 in the unit worktree with
Python 3.14.7 and Git 2.55.0:

```sh
python3 docs/designs/restack-queue-provenance/pocs/edge-witness/prototype.py --self-test
```

The command printed one JSON object per scenario, followed by this exact summary:

```json
{"controls_passed":6,"controls_total":6,"git":"git version 2.55.0","observed_red":4,"passed":23,"python":"3.14.7","summary":"PASS","total":23}
```

I also retained a fresh set of all 23 disposable repositories with this exact command:

```sh
python3 docs/designs/restack-queue-provenance/pocs/edge-witness/prototype.py --self-test --fixtures-dir /Users/quentinmiao/code/agentfold/.git/agents/runs/2026-08-31-prove-the-correct-restack-queue-201c/scratch/edge-witness-poc/verified-23-scenarios
```

That retained run also ended with the same 23/23 and 6/6 summary. The scratch path is run
evidence, not a durable PR artifact; a reviewer can regenerate the deterministic object IDs
with the first command.

## Worked example: the distinction this POC proves

S1 starts with one live action at `C`. The old task tip `O` changes only a feature file.
The candidate side commits a claim, changes the declared non-queue evidence, deletes the
action at `M`, and replays the feature at `N`.

```text
C 3f07eff257fe21311d0da2b1ca1fe57fb6e34f6a
O 97db2eff747dbe84c3119b3bca4410bef3c43ef2
M 11128f74e4636c8288a7dcf00b9527b0af6bd3c0
N 9b53f36b908350c62e749529b7745da31945baa3
real deletion edge fe3c76ea75a08ad636256c11694b9d307be16d8a
                -> 11128f74e4636c8288a7dcf00b9527b0af6bd3c0
real-edge lifecycle/evidence problem: null
verdict: no finding
```

S2 has the same old-side ownership shape, but the candidate deletes the action while it is
still `open` and changes no evidence. The prototype locates the deletion but returns
`agent action was not committed as in-repair before deletion`, so the push remains blocked.
This is why ancestry can locate a supplier but cannot authorize it.

## Scenario evidence

Every row below is **VERIFIED** by an executable assertion in `--self-test`.

| Scenario | Result | Deciding evidence |
|---|---|---|
| S1 valid base resolution | no finding | exactly one matching candidate-side deletion edge passes the existing validator |
| S2 invalid base deletion | blocking finding | the real deletion edge has no committed `open -> in-repair` claim |
| S3 branch-owned action loss | blocking finding | the old tip authored the action and the candidate side has no matching deletion edge |
| S4 changed action | blocking finding | the candidate resolves the base incarnation, not the branch-authored identity |
| S5 mixed actions | exactly one finding, for Q2 | Q1 has a valid witness; old-tip-authored Q2 has none |
| S7 unrelated restack | no finding | the same action identity remains live at `N` |
| S8 fast-forward replacement | no finding | `O` is an ancestor of `N`, so no divergent continuity edge exists |
| S9 unrelated tip | snapshot error | `O` and `N` have no merge base |
| S9 non-commit tip | snapshot error | the supplied full OID names a blob, not a commit |
| S9 missing tip | snapshot error | the supplied full OID is unavailable |
| S10 pre-v1 old-tip action | blocking finding | activation on the new history cannot erase an old-tip obligation |
| compact valid deletion at N | no finding | the only valid witness child is exactly `N` |
| activation laundering | blocking finding | the pre-v1 real deletion edge is force-validated and lacks a claim |
| claimed-tip synthetic laundering | blocking finding | synthetic `O -> N` validation returns `null`, while the real edge lacks a claim |
| independent byte-identical incarnation | blocking finding | the old-tip action was authored after `C`, so a separate candidate lifecycle cannot borrow it |
| old delete/recreate with equal endpoints | blocking finding | the old-side parent walk sees both the deletion and byte-identical reintroduction |
| legal old resolve/recreate with equal endpoints | blocking finding | both side resolutions pass the lifecycle validator, but they resolve different incarnations |
| old rename away and back | blocking finding | two old edges expose the alternate path, so rename ambiguity cannot borrow authorization |
| old identity mutation and reintroduction | blocking finding | equal `C`/`O` blobs cannot hide the intervening action rewrite |
| candidate side delete, merge undo, mutate, delete | blocking finding | the only locally valid deletion is undone before `N`, so it is not causally responsible for final absence |
| merge-parent occurrence ambiguity | blocking finding | the raw production helper returns `null`, but two parent occurrences can supply the claim receipt |
| repeated incarnation | blocking finding | two valid deletion edges match, so the prototype refuses to pick one |
| 35-commit candidate history | no finding | one valid witness survives a multi-commit rewrite |

The claimed-tip case is the strongest security control. A claim reachable only from `O`
plus unrelated evidence bytes at `N` makes the synthetic edge look valid. The actual
candidate parent still carries the action as `open`, so real-edge validation refuses the
deletion. Replacing the current constant continuity finding with a synthetic-edge call
would therefore create a bypass.

The fresh verifier found a second bypass after the first milestone. `O` could author Q after
`C`, while the candidate independently authored byte-identical Q, claimed it, resolved it,
and omitted it at `N`. Real-edge validation passed, but that lifecycle belonged to a separate
incarnation. The repaired classifier now requires the old-tip action identity to equal its
state at every merge base before a valid candidate-side edge can authorize disappearance:

```text
C 5bc182839c03e7486d81839160129e86e325bd75
O 9dc0b5af6a1d047534d1a8cf8f64bff3332f873e
M 21bc63d1c4fac0fc724623d868c8474c9d1ea01e
N 507e8703b953c2dfc8262c5fe3b7c0c0f0b43840
candidate real-edge problem: null
old-tip provenance: old-tip-authored
verdict: blocking finding (different-incarnation-witness)
```

The next fresh verifier showed that endpoint identity is still insufficient. Q can exist
unchanged at both `C` and `O` while the old side legally claims and resolves the `C`
incarnation, then creates a new byte-identical Q at `O`. The candidate can also legally
resolve the original `C` incarnation. Both deletion edges pass the current lifecycle
validator, but the candidate must not resolve the new old-tip obligation. The classifier
now walks every old-only parent edge from each merge base to `O`; any deletion/recreation,
rename ambiguity, or identity mutation/reintroduction makes provenance discontinuous:

```text
C bfe9ba307457ca45cea3d6aa1b7dc9875481d8d4
O 4b0fecd47ab9f67692473c86a8312ab570c3cb98
M 22eba505f87e5883ba71a409e9c7f617eb4da8d9
N 2601032ebd3fb339533035bac0e69486957535cb
C/O queue blobs equal: true
old valid deletion f8162fbfd11a7476c816ab6ba48b1de0b1d6d064
                -> 1a18d1cade6246832c5cbee36c507faf7079af00
candidate valid deletion 22eba505f87e5883ba71a409e9c7f617eb4da8d9
                      -> 2601032ebd3fb339533035bac0e69486957535cb
old-edge events: deletion, reintroduction
verdict: blocking finding (different-incarnation-witness)
```

The third fresh verifier found the candidate-side mirror of that bug. A reachable side
branch can validly resolve Q, while a later merge keeps a carrying main parent's Q. The
merge therefore undoes the side deletion. A later commit mutates Q and `N` deletes that
different identity, so the earlier valid edge exists but did not cause final absence. The
repaired classifier now requires every state on every ancestry path after a witness child
to remain absent, and inspects every parent of a descendant merge rather than only the
parent on which the witness was found:

```text
C 97c4da1d6eed422292d5b4681834ac7671b2f9ab
O bd98e58c620c645505f4d3570b04f30443bcc773
M 0041220d2132c884410884e3e2f0f64fdee16a78 (merge)
N cd9d4ad48498a943489fcbc94fdd583b6f042486
locally valid side deletion 712c41ccf8426376a0c4d0848acf1c9b7479daf4
                         -> b6de978a29f87a1357c22d53c798feff7837b65f
carrying merge sibling a53107b2bd466461eb3b7f4dac0d7fd3125be834
post-witness events: merge-sibling-carries-action,
                     merge-result-reintroduction-or-survival,
                     identity-mutation-or-reintroduction,
                     later-deletion
verdict: blocking finding (invalid-post-witness-continuity)
```

A second merge attack showed that post-witness continuity is not enough if the claim receipt
before the witness is ambiguous. The merge result can carry byte-identical `in-repair` bytes
from an independently created root while another parent carries the original occurrence's
valid claim transition. The current production deletion helper walks both parents and returns
`null`, even though it cannot prove which occurrence the merge result selected. The POC now
walks backward from each witness parent and fails closed whenever more than one merge parent
can supply the same action occurrence:

```text
C 1910c07f289cecedd06775d194f40812b438de5d
O 4e70a05a587ecfc99638f6f472a49f3604150cc0
M fe6b8cae47062c5ba03d2b8d136adef30077082f (ambiguous merge)
N bdf696ec206e8a396f13508e7a670046a892f59b
independent in-repair parent c9614f211fa9e9be2f6b1ad3a3a5a1ceecc8ef26
original claimed parent      3e3b8857e3690b809f5e70fe6793a00529d4ecee
raw production deletion problem: null
pre-witness event: multi-parent-occurrence-ambiguity
verdict: blocking finding (invalid-witness-occurrence-ambiguity)
```

## Executable negative controls

These controls run inside `--self-test`; they do not rely on another POC's summary.

The first control disables only the new incarnation-provenance condition. The new fixture
then returns the former `no-finding` false negative, so the run records one observed red:

```json
{"control":"observed-red-incarnation-provenance","damaged_classification":"no-finding","expected":"blocking-finding","status":"OBSERVED_RED"}
```

The second disables only the old-edge continuity guard. Despite byte-identical `C`/`O`
blobs and valid deletion edges on both sides, the stronger reincarnation fixture becomes
false-green. The emitted deletion and reintroduction events show the evidence the damaged
classifier ignored:

```json
{"control":"observed-red-old-edge-continuity","damaged_classification":"no-finding","endpoint_blob_equal":true,"endpoint_lineage":"inherited-unchanged-on-old-tip","expected":"blocking-finding","old_edge_events":["deletion","reintroduction"],"status":"OBSERVED_RED"}
```

The third disables only post-witness continuity. The scanner still emits the merge sibling,
merge-result survival, identity mutation, and later deletion, but the damaged classifier
accepts the earlier side deletion and becomes false-green:

```json
{"control":"observed-red-post-witness-continuity","damaged_classification":"no-finding","expected":"blocking-finding","merge_commit":"0041220d2132c884410884e3e2f0f64fdee16a78","post_witness_events":["merge-sibling-carries-action","merge-result-reintroduction-or-survival","identity-mutation-or-reintroduction","later-deletion"],"status":"OBSERVED_RED","witness_child":"b6de978a29f87a1357c22d53c798feff7837b65f"}
```

The fourth disables only pre-witness occurrence provenance. The raw production helper still
returns `null`, the scanner still emits `multi-parent-occurrence-ambiguity`, and the damaged
classifier becomes false-green:

```json
{"control":"observed-red-pre-witness-occurrence","damaged_classification":"no-finding","expected":"blocking-finding","merge_commit":"fe6b8cae47062c5ba03d2b8d136adef30077082f","occurrence_events":["multi-parent-occurrence-ambiguity"],"raw_production_problem":null,"status":"OBSERVED_RED"}
```

The fifth calls the current production `candidate_paths_match_other_parent` helper against
S2. The helper accepts the evidence-free supplied deletion, while real-edge validation names
the missing claim:

```json
{"accepted_evidence_free_deletion":true,"control":"production-other-parent-is-evidence-blind","real_edge_problem":"agent action was not committed as in-repair before deletion","status":"PASS"}
```

The sixth computes its own queue-tree replay signature for S1 and S2. Both old deltas avoid
the queue, both replay deltas avoid the queue, and both candidates omit the path; only the
real-edge evidence verdict distinguishes them:

```json
{"control":"replay-tree-cannot-authorize","s1_evidence":{"message-queue/needs-agent/requests/non-blocking-s1.md":"valid-real-edge"},"s2_evidence":{"message-queue/needs-agent/requests/non-blocking-s2.md":"invalid-real-edge: agent action was not committed as in-repair before deletion"},"signature":{"candidate_path_absent":true,"old_queue_delta_empty":true,"replay_queue_delta_empty":true},"status":"PASS"}
```

## Cost

The prototype counts actual Git child processes and logical path-entry reads during
classification; fixture construction is excluded.

| Fixture | Old c/e | Candidate c/e | Pre-witness c/e | Post-witness c/e | Path reads | Git processes |
|---|---:|---:|---:|---:|---:|---:|
| S1, one action | 1 / 1 | 3 / 3 | 2 / 1 | 1 / 1 | 20 | 38 |
| S5, two actions | 2 / 2 | 3 / 6 | 2 / 1 | 1 / 1 | 34 | 44 |
| legal old resolve/recreate | 3 / 3 | 2 / 2 | 2 / 1 | 0 / 0 | 23 | 44 |
| candidate merge undo | 1 / 1 | 6 / 7 | 2 / 1 | 3 / 4 | 38 | 54 |
| merge occurrence ambiguity | 1 / 1 | 4 / 4 | 1 / 2 | 0 / 0 | 20 | 36 |
| long history, one action | 1 / 1 | 35 / 35 | 34 / 33 | 1 / 1 | 148 | 166 |

**VERIFIED:** these numbers came from the JSON emitted by the retained 23/23 run. Here `c/e`
means commits/parent edges scanned in that phase. **INFERENCE:** this straightforward
prototype costs `O(B + Hc + Q*(Ec + Eo + Epre + Epost))` logical reads, where `B` is merge
bases, `Hc` is candidate-only commits, `Q` is disappeared actions, and the `E` terms are
candidate, old, pre-witness, and post-witness parent edges. The process count is linear in
the histories but repeats ancestry scans per candidate witness. A production implementation
should enumerate commit/parent pairs once and cache immutable `(commit, path)` entries; this
POC did not measure that optimized form.

## Strongest self-counterexample

The repeated-incarnation fixture legally claims and resolves one action, recreates the
same bytes, then legally claims and resolves it again. Both real deletion edges pass the
current validator:

```text
d8a34e362a57409cfe77b629e7e978579df92926
  -> fbbf7be8f8ee6810fa5dd60e9c2035df4eacc407
ff20bf79a817ce9fb7898f2e83aebfb49ac3b25a
  -> 99f867bc57f23dbb4de7b995a265bf4a732d1832
```

The prototype reports `ambiguous-real-edges` instead of choosing the final incarnation.
That conservative false positive is intentional, but it is also the clearest reason this
code must not move into production unchanged. Production selection needs an explicit
incarnation-causality rule and a fresh-agent attack against delete/recreate/delete histories.

## What is verified, inferred, and proposed

**VERIFIED:** this prototype works for linear restacks, fast-forward extensions, candidate
histories with 35 commits, mixed actions, full-OID object failures, a valid deletion at `N`,
the two laundering controls, a byte-identical cross-lineage incarnation, old-side legal
resolve/recreate, rename round trips, identity mutation/reintroduction, and one two-parent
candidate merge that undoes a valid side deletion. It also reproduces a raw production
false-green where two merge-parent occurrences can lend one claim receipt to another. It
imports the current `queue_deletion_problem` authority instead of paraphrasing its lifecycle
and evidence rules. It emits full `C`, `O`, `M`, and `N` OIDs, every candidate witness, old
continuity edge, pre-witness parent occurrence, and post-witness parent edge, plus the
evidence verdict, expected verdict, human-readable reason, and measured cost as JSON lines.
Any mismatch exits nonzero.

**INFERENCE:** an exact candidate-side witness is a smaller and safer production boundary
than replay, patch similarity, or direct-parent state because it explains the result from
immutable Git objects and reuses the repository's existing authority. Confidence is high
for the linear scenarios and the two exact two-parent merge attacks; general merge causality
remains unknown because I did not measure criss-cross merges or multiple merge bases here.

**PROPOSAL:** a production helper should validate object availability, require the old-tip
action/path identity to match every shared boundary and remain uninterrupted over every
old-only parent edge, enumerate every candidate-only parent edge, match the complete old-tip
action incarnation, force the existing validator over the causal deletion edge even before
schema activation, prove the witness parent has one unambiguous occurrence lineage across
every ancestor merge, and require that occurrence to remain absent on every descendant result
and every parent of descendant merges through `N`. It should return a structured witness for
the human-facing finding and fail closed on unreadable, ambiguous, or unproven history.
The selection rule for multiple valid witnesses remains open and must be settled by the
merge/incarnation POC plus fresh-context review before implementation starts.

## What this does not establish

- It does not alter or test the production continuity call site.
- It proves a rename away and back fails closed; it does not prove an authorized one-way
  timing-prefix move.
- It proves one merge-parent survival attack fails closed; it does not prove merge-only
  deletion, criss-cross, octopus, or multiple-merge-base behavior.
- It does not choose the correct witness across repeated action incarnations.
- It does not simulate a shallow clone with both tips present but intermediate objects missing;
  it covers unavailable, non-commit, and unrelated supplied tips.
- It does not benchmark a production cache or representative large repository.
- It proves structural claim/evidence transitions, not the truth of evidence prose.

Before production implementation, a fresh verifier must reproduce this 23/23 command and all
six controls, then attack the repeated-incarnation false positive and broader merge cases.
