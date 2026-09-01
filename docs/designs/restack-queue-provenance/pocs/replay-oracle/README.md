# Replay oracle proof of concept

Result: replay, stable patch ids, range-diff, and final-tree ownership are useful
operator diagnostics, but none can authorize a queue-action disappearance. The executable
counterexamples fail in both directions: an invalid base deletion can look perfectly
replayed, while a legitimate conflict-adjusted replay can lose patch identity. This POC
therefore labels every record `diagnostic-only; never authorizes suppression`.

The shared requirements and scenario matrix live in orchestration run
`2026-08-31-prove-the-correct-restack-queue-201c`. This directory changes no production
reconciler or test behavior and uses only the Python standard library plus the installed
Git executable.

## What is verified

**VERIFIED — seven real DAGs.** `prototype.py` creates a separate disposable Git
repository for each case, makes real commits/merges/cherry-picks, reads immutable objects
with `--no-replace-objects`, and emits one JSON object per scenario. Every object contains
full `C`, `O`, `M`, and `N` object IDs, all observed heuristic signals, the independently
declared expected verdict, and a plain-language explanation.

**VERIFIED — the mandatory failure cases are executable.** The self-test exits nonzero if
any of these observations changes:

- S1 and S2 both have `old_path_matches_common=true`, a shared feature patch id, and a clean
  replay whose tree equals `N`; S1 is valid and S2 still requires a finding because S2 has
  no claim/evidence lifecycle.
- X1 performs a cherry-pick that really conflicts, resolves it with the feature preserved,
  and proves the adjusted commit has a different stable patch id.
- X2 creates distinct independently authored commits with the same stable patch id and
  shows range-diff pairing them as corresponding work despite different metadata.
- X3 introduces the live action only in a merge commit. Both ordinary side patches replay
  cleanly and range-diff reports them as equal, but `--no-merges` finds no action commit;
  the full-history query finds the merge and the expected result remains a finding.

**VERIFIED — simple controls.** S3 keeps the genuine branch-owned loss red: replaying the
whole old series retains the action and does not match `N`. S7 keeps an unrelated restack
green because the queue tree does not change.

## Exact run and captured output

Environment captured on 2026-08-31:

```text
Python 3.14.7
git version 2.55.0
Git object format: sha1
```

Exact verification command from the repository root:

```sh
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py --self-test
```

Captured stderr:

```text
replay-oracle self-test: 7/7 scenarios passed
```

**VERIFIED — observed red:** a scratch copy changed only X3's authoritative expected
verdict from `finding` to `no-finding`. Running that copy exited 1 with:

```text
replay-oracle self-test failed: X3 authoritative live-action-loss verdict drifted
```

The damaged copy is run-local evidence under `scratch/replay-oracle-poc/`; it is not part of
this deliverable or production code.

Captured stdout contained exactly seven JSON lines. These are the stable full OID fields
and claimed properties from that run; the JSON also carried the range-diff lines, patch ids,
tree/replay signals, cost counters, evidence verdict, and explanation shown by the command.

| Scenario | C | O | M | N | Executable property |
|---|---|---|---|---|---|
| S1-valid-base-resolution | `090519dae17c744db639d0317d8914aa15a14938` | `0781e680cc68b1b29376b60b0113c8482bd923f1` | `78c41b0267a3d9d0b04078db4c70ffcf8e2f853e` | `eb6bdafadb03a8a4465d06ea74cc820e92f1afad` | replay matches; expected no finding only because real-edge evidence is valid |
| S2-invalid-base-deletion | `090519dae17c744db639d0317d8914aa15a14938` | `0781e680cc68b1b29376b60b0113c8482bd923f1` | `f8e78141cb2bfcdc64a524d2cd66fb5fe43377f2` | `974110c92f6e0f1e0206452c501b8a428fbb9045` | replay also matches; expected finding because evidence is invalid |
| S3-branch-owned-action-loss | `66c380be0a256b2257ad4b4e3b824dd14224663c` | `2032dae744dfefa2f14b9d53186023dae1890f99` | `72b6c5f242c4d97ef5982ec2fe88a5c21c61c06b` | `3ab54b5fa670ef473bf436784393bc6a40124f09` | full replay does not match; expected finding |
| S7-unrelated-restack | `090519dae17c744db639d0317d8914aa15a14938` | `b1f63b8f6a6b8dbb7c25e450d00b8638d7ef6d27` | `cfba093ff8b2b79ecc9827d018f480d6ada74935` | `104c8d389d346d8e391b4c5f1e0be87f224f5fc8` | queue unchanged; replay matches; expected no finding |
| X1-conflict-adjusted-replay | `090519dae17c744db639d0317d8914aa15a14938` | `a8a87300cb0dc24866d590fa7fc34b850cd1254e` | `e6584efe04ee0d09a79c2549d23a1e7c1873519b` | `beee6a7087fb9b465234da9f6a4f6a526466bfb6` | conflict resolution preserves feature but loses patch-id match |
| X2-independent-patch-collision | `090519dae17c744db639d0317d8914aa15a14938` | `8c51e08c3548c64ae2890c49366d58e99b3fe15d` | `c722d7e4e46ed6d1a1362297878b66448d3f3656` | `db4415f4ea616749cdaad9104266f0a9c4509a9c` | distinct authorship collides at patch id `c88789270f7363bf07a6ab97660acc88090d7ec6` |
| X3-merge-commit-only-action | `66c380be0a256b2257ad4b4e3b824dd14224663c` | `91e0745883ad0844c6b218f8b47192a93a1aaf83` | `3ee3b2e1b59600d4533e29a3fa6b8ef0cccbec0e` | `4dd780cc0b57d4acc3035b4477e94288cc3a1f35` | no-merge replay matches while the merge-authored live action is lost |

To retain the repositories behind those OIDs for manual inspection, pass a new or empty
directory. The script refuses a non-empty target instead of deleting or overwriting it:

```sh
python3 docs/designs/restack-queue-provenance/pocs/replay-oracle/prototype.py \
  --self-test --work-dir /private/tmp/agentfold-replay-oracle-inspection
```

## Strongest counterexample

**VERIFIED:** X3 is the strongest counterexample to patch-series authority. `O` is a merge
whose two parents contain only `side-a.txt` and `side-b.txt`; the live queue action first
appears in the merge tree. `N` carries both side patches and omits the action. The observed
range-diff is:

```text
1:  099a5f2 = 1:  5e28afb add side A
2:  7747e4b = 2:  4dd780c add side B
```

The merge OID `91e0745883ad0844c6b218f8b47192a93a1aaf83` is absent from that output,
`no_merge_queue_commits` is `[]`, full history returns that exact OID, and no-merge replay
still reports `tree_matches_candidate=true`. A policy based on “all patches survived” would
miss a genuine live-action loss.

## Cost and operator effect

**VERIFIED — measured process counts.** Each JSON line reports the total processes used to
construct and diagnose its fixture. This run observed 37–56 Git processes per scenario and
18–27 read-only inspection processes. The count intentionally includes fixture construction,
so it is a reproducibility cost, not a production benchmark.

**INFERENCE — asymptotic diagnostic cost.** With `k_old` and `k_new` non-merge commits and
`P` total patch bytes, this implementation performs `O(k_old + k_new)` external Git calls
and streams `O(P)` patch bytes for per-commit patch ids. Full replay adds `O(k_old)`
cherry-picks. Final path ownership itself uses a constant number of `cat-file`/`diff`
commands; Git's internal tree-walk and range-diff algorithms are treated as opaque rather
than assigned an unsupported bound. Production should not pay this cost in the authority
gate.

**INFERENCE — actual human effect.** These signals can explain “the feature patches were
preserved,” “the old lineage introduced this action,” “the path absence came from the base,”
or “the replay needed conflict adjustment.” That reduces the amount of DAG inspection a
developer must do. It cannot explain whether a deletion satisfied AgentFold's claim and
evidence contract; that still requires an exact real-edge authority check.

## Inference, proposal, and non-claims

**INFERENCE:** replay diagnostics are most useful after an authoritative classifier has
already decided the queue outcome. They help a person understand a finding or exemption,
but disagreement between replay and authority should make the explanation more cautious,
not change the verdict.

**PROPOSAL:** if the winning production design wants operator visibility, expose only cheap
tree-ownership facts by default and make patch/range diagnostics an explicit offline command.
Never parse range-diff prose inside the reconciler and never let a replay match suppress a
continuity finding.

This POC does **not** establish production integration, queue lifecycle validity, rename or
action-incarnation safety, shallow-object handling, provider behavior, performance on a long
repository, or the semantic truth of evidence text. It does not select the winning authority
algorithm and does not modify the reconciler. Those questions belong to the supplier-edge
and merge/incarnation POCs plus fresh-agent adjudication.
