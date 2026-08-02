# Verification — admit resolution evidence that landed earlier

**Verified:** 2026-07-31 by claude

Only commands actually run and their real output. Where output is long, the elision is
marked and everything else is verbatim.

Two clones under a scratch /tmp/agentfold-probe/ directory carry the comparison, so both checker builds run
against byte-identical repository content:

- `after/` — this branch, tip `767fd554afc8e7f84031ac2a7e3e22b55da2ab32`
- `before/` — the stack base task/2026-07-30-cache-reconciler-git-object-reads, tip
  `a5e81751c1ec66c02b134ceb835717a043dc8677`

Six scratch scripts produced the measurements. They are not committed, so each is described
where it is used:

- `stage_stuck_deletion.sh` — hard-resets a clone, deletes the stuck request, drops its
  reciprocal task backlink, stages both, and prints whether `reconcile.py` is in the edit.
- `verdict.py` — loads one repository's `reconcile.py` and prints
  `resolution_evidence_problem` and `queue_deletion_problem` for one staged deletion.
- `table.py` — runs `verdict.py` once per live ordinary request, hard-resetting between.
- `diag.py` — prints the rule's internals for one staged deletion: `L`, `A`, and each
  candidate commit's task status at that commit.
- `laundering.py` — escalates one real backlog gate four ways, reporting the verdict after
  each step.
- `replay.py` / `spawncount.py` — run one checker build against one repository (rebinding
  `REPO`), the second counting Git spawns per check.

## 1. The acceptance test: the stuck item becomes deletable, and only it

`automation/reconcile/reconcile.py` is never in the staged edit — the script asserts that.

```
$ sh stage_stuck_deletion.sh /tmp/agentfold-probe/before
D  message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
M  tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md
reconcile.py in this edit: NONE STAGED
$ python3 automation/reconcile/reconcile.py --check
[queue-resolution] message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md: deleted unresolved queue item: resolution evidence was not created or changed in the deletion commit: `automation/reconcile/reconcile.py`
    fix: commit the required claim/response evidence before deleting it
reconcile: 1 finding(s)
EXIT_PARENT=1
```

The same edit on this branch:

```
$ sh stage_stuck_deletion.sh /tmp/agentfold-probe/after
D  message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
M  tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md
reconcile.py in this edit: NONE STAGED
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
EXIT_PATCHED=0
```

Not just `queue-resolution` — the whole reconciler is green on that deletion.

## 2. All 14 live ordinary requests: exactly one admitted

`table.py` stages each live non-pickup request's deletion in turn, together with its
reciprocal task backlinks, and reports `resolution_evidence_problem`. Tabs are the field
separator; the fourth column, `queue_deletion_problem`, is shown where it differs.

This branch:

```
$ python3 -u table.py /tmp/agentfold-probe/after
item	verdict	evidence problem
blocking-repair-handover-projection-code-span-copy.md	ADMIT	-	-
future-blocking-add-the-pre-commit-mining-advisory.md	REFUSE	... `automation/AGENTS.md`	agent action was not committed as in-repair before deletion
future-blocking-complete-parent-before-workspace-manifest.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
future-blocking-continue-first-class-message-queue-review.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
future-blocking-finish-mining-task-before-transcript-backfill.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
future-blocking-resolve-lineage-and-instruction-before-publication-review.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
future-blocking-resolve-lineage-and-provenance-before-instruction-admission.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
future-blocking-resolve-manifest-before-cross-zone-operations.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
future-blocking-resolve-manifest-before-override-lineage.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
future-blocking-resolve-manifest-before-recovery-evidence.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
non-blocking-build-the-edge-graph-viewer-within-measured-constraints.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
non-blocking-build-the-stage-2-edge-schema.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
non-blocking-build-the-stage-4-edge-join.md	REFUSE	... `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
non-blocking-detect-lexical-restatement-across-contracts.md	REFUSE	... `automation/AGENTS.md`	agent action was not committed as in-repair before deletion
```

`...` stands for the literal prefix `resolution evidence was not created or changed in the
deletion commit:`, printed in full on every one of those thirteen lines.

The stack base, same 14 items, same script:

```
$ python3 -u table.py /tmp/agentfold-probe/before
blocking-repair-handover-projection-code-span-copy.md	REFUSE	resolution evidence was not created or changed in the deletion commit: `automation/reconcile/reconcile.py`	resolution evidence was not created or changed in the deletion commit: `automation/reconcile/reconcile.py`
[the other thirteen lines are byte-identical to the run above]
```

**1 of 14 admitted, 13 refused, and every refusal message is byte-identical to the base
branch's.** The design measured the naive widening at 14 of 14.

## 3. Gate laundering stays refused through all four escalations

Target: `future-blocking-resolve-manifest-before-recovery-evidence.md`. Its stated
precondition is task `2026-07-24-declare-layered-workspace-manifest`, still unclaimed in
`tasks/0_backlog/`; its evidence is `roadmap/current-state.md`; its boundary is
`Blocks at: transition:start task:2026-07-24-record-layered-recovery-evidence`, and that
same task is the only one linking it.

```
$ python3 -u laundering.py /tmp/agentfold-probe/after
--- step 1 — plain delete
future-blocking-resolve-manifest-before-recovery-evidence.md	REFUSE	resolution evidence was not created or changed in the deletion commit: `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
--- step 2 — forged task: trailer commit touching the evidence
future-blocking-resolve-manifest-before-recovery-evidence.md	REFUSE	resolution evidence was not created or changed in the deletion commit: `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
--- escalated item header
# Resolve the manifest prerequisite before recovery-evidence work starts

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After `2026-07-24-declare-layered-workspace-manifest` is done, verify its completion evidence and remove this dependency action and its reciprocal task link before claiming recovery-evidence work.
**Full context:** `docs/designs/layered-development-workspace.md`
**Resolution evidence:** `roadmap/current-state.md`
**Blocks now:** transition:start

--- step 3 — boundary token stripped by the escalation
blocking-resolve-manifest-before-recovery-evidence.md	REFUSE	resolution evidence was not created or changed in the deletion commit: `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
--- step 4 — task moved to in-progress after the forged commit
blocking-resolve-manifest-before-recovery-evidence.md	REFUSE	resolution evidence was not created or changed in the deletion commit: `roadmap/current-state.md`	agent action was not committed as in-repair before deletion
--- task status now
f40a754ca8cac1bc91d6886ae494f64f816bce13 harness: claim the gated task after the fact

tasks/1_in-progress/2026-07-24-record-layered-recovery-evidence/plan.md
tasks/1_in-progress/2026-07-24-record-layered-recovery-evidence/task.md
tasks/1_in-progress/2026-07-24-record-layered-recovery-evidence/worklog.md
```

The refusal at step 4 is not incidental. `diag.py` on that exact state shows the escalation
did put the task back into the admitted set, and that only the status *at the forged commit*
refuses it:

```
$ python3 -u diag.py /tmp/agentfold-probe/after message-queue/needs-agent/requests/blocking-resolve-manifest-before-recovery-evidence.md
timing prefix        : blocking
Blocks now           : transition:start
Blocks at            : <absent>
L (tasks linking it) : ['2026-07-24-record-layered-recovery-evidence']
A (admitted = L - B) : ['2026-07-24-record-layered-recovery-evidence']
evidence             : roadmap/current-state.md
  candidate 540bacd258 task:2026-07-24-record-layered-recovery-evidence status-at-that-commit=0_backlog admits=False
  verdict: REFUSE
```

Positive control, so the refusal is not vacuous — one further commit touching the evidence
*after* the pickup does admit, which is the rule working, not failing:

```
$ git commit -m "chore: touch the evidence again" -m "task: 2026-07-24-record-layered-recovery-evidence"
$ python3 -u diag.py /tmp/agentfold-probe/after message-queue/needs-agent/requests/blocking-resolve-manifest-before-recovery-evidence.md
L (tasks linking it) : ['2026-07-24-record-layered-recovery-evidence']
A (admitted = L - B) : ['2026-07-24-record-layered-recovery-evidence']
evidence             : roadmap/current-state.md
  candidate 62c5963ca4 task:2026-07-24-record-layered-recovery-evidence status-at-that-commit=1_in-progress admits=True
  candidate 540bacd258 task:2026-07-24-record-layered-recovery-evidence status-at-that-commit=0_backlog admits=False
  verdict: ADMIT
```

## 4. The gate's legitimate positive path still passes

`future-blocking-add-the-pre-commit-mining-advisory.md`, evidence `automation/AGENTS.md`,
claimed `open` -> `in-repair` in one commit and then deleted in an edit that really changes
that file:

```
$ git commit -m "harness: claim the mining advisory request"     # status open -> in-repair
$ printf '\n<!-- advisory tier landed -->\n' >> automation/AGENTS.md
$ rm message-queue/needs-agent/requests/future-blocking-add-the-pre-commit-mining-advisory.md
$ git add -A
$ python3 -u verdict.py /tmp/agentfold-probe/after message-queue/needs-agent/requests/future-blocking-add-the-pre-commit-mining-advisory.md
future-blocking-add-the-pre-commit-mining-advisory.md	ADMIT	-	-
```

That is the same item the table refuses when the evidence is untouched, so the
deletion-edge rule is intact and is still the ordinary way to pass.

## 5. Shallow clone: identical findings and exit code

A depth-1 clone of this branch, where every commit before the boundary is a missing object.
`replay.py` runs each checker build against that same clone.

```
$ git clone --depth 1 --branch task/2026-07-30-admit-evidence-that-landed-earlier file://<this worktree> shallow
$ cd shallow && git rev-parse --is-shallow-repository
true
$ git log --oneline | wc -l
       1
```

```
$ python3 replay.py after/automation/reconcile/reconcile.py shallow
[queue-schema] message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md: **Review revision:** is not a reviewable Git artifact: 00690e89b53573aff4ca90929cc96852d00f7293 is unavailable; d7eefcee521ad319bbf428c796c96740833f2a17 is unavailable
    fix: use available literal commit ids with a shared history
[queue-schema] message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md: **Review revision:** is not a reviewable Git artifact: d87b755e6259101bf76b0a2783b35dfb3f163fb0 is unavailable; 8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b is unavailable
    fix: use available literal commit ids with a shared history
[queue-schema] message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md: **Review revision:** is not a reviewable Git artifact: 25d03257b5ee61753fa9bada609722c4e84a8064 is unavailable; fd2374d99796300ed4325c2961e696092c17875e is unavailable
    fix: use available literal commit ids with a shared history
reconcile: 3 finding(s)
EXIT_PATCHED=1
```

Both builds, redirected to files and diffed, on the clean shallow clone and again with the
stuck deletion staged so `queue-resolution` really runs its deletion path:

```
$ python3 replay.py after/.../reconcile.py shallow > shallow-new.txt ; echo EXIT_PATCHED=$?
EXIT_PATCHED=1
$ python3 replay.py before/.../reconcile.py shallow > shallow-old.txt ; echo EXIT_PARENT=$?
EXIT_PARENT=1
$ diff shallow-old.txt shallow-new.txt && echo IDENTICAL
IDENTICAL

$ sh stage_stuck_deletion.sh shallow
D  message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
M  tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md
reconcile.py in this edit: NONE STAGED
$ python3 replay.py after/.../reconcile.py shallow > shallow-del-new.txt ; echo EXIT_PATCHED=$?
EXIT_PATCHED=1
$ python3 replay.py before/.../reconcile.py shallow > shallow-del-old.txt ; echo EXIT_PARENT=$?
EXIT_PARENT=1
$ diff shallow-del-old.txt shallow-del-new.txt && echo IDENTICAL
IDENTICAL
$ cat shallow-del-new.txt
[... the identical three queue-schema findings ...]
[queue-resolution] message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md: deleted unresolved queue item: no committed one-line open -> in-repair claim transition exists
    fix: commit the required claim/response evidence before deleting it
[link-check] tasks/1_in-progress/2026-07-30-admit-evidence-that-landed-earlier/task.md: `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md` does not exist
    fix: fix the path, create the target, or unquote if not a path
reconcile: 5 finding(s)
```

A depth-1 clone cannot see the claim commit, so the deletion is refused earlier and the
earlier-work rule is never consulted. Both builds report it identically, exit 1 in every
scenario, no `exit 2`, no silenced checks. The `link-check` line was the state of the task
record at that moment and is fixed in `767fd55`.

## 6. The subset property, over this repository's whole history

**Structural.** The rule is one added `continue` inside `resolution_evidence_problem`. A
path is appended to `unchanged` only when it was appended before *and* the new rule also
declines it, so `unchanged_new` is a subset of `unchanged_old` for every input. The message
and the `Finding` construction are untouched, so the `(check, subject)` identity that
`finding_key` and `retry_identity_matches` use is unchanged, and a green verdict can never
become red. The only way the two messages can differ at all is an item declaring more than
one evidence path where some are admitted and some are not — see the census below.

**Empirical.** Every commit of this branch replayed through both builds, against the same
clone:

```
$ git rev-list --count HEAD
325
$ python3 replay.py after/.../reconcile.py after --range root:767fd554afc8e7f84031ac2a7e3e22b55da2ab32 > new-history.txt ; echo new exit=$?
new exit=1
$ tail -1 new-history.txt
reconcile: 55 finding(s)
$ python3 replay.py before/.../reconcile.py after --range root:767fd554afc8e7f84031ac2a7e3e22b55da2ab32 > old-history.txt ; echo old exit=$?
old exit=1
$ tail -1 old-history.txt
reconcile: 55 finding(s)
$ diff old-history.txt new-history.txt && echo IDENTICAL FINDING LISTS
IDENTICAL FINDING LISTS
```

`--range root:<head>` walks every commit, so every queue deletion edge in the repository's
history was evaluated by both builds and reported identically — including the one
pre-existing `queue-resolution` finding in that replay, which stays exactly as it was.

**The multi-path case cannot arise here.** Every distinct `(path, content)` version of every
queue item in the whole history, run through `resolution_evidence_paths`:

```
$ python3 - <<'PY'   # walks git rev-list HEAD, every message-queue item version
[...]
PY
distinct (path, content) queue items with evidence: 96 with >1 path: 0
```

No item has ever declared more than one evidence path, so on every input this repository has
produced, the subset is exact down to the message bytes.

## 7. Suite, `--check`, and Git spawn counts

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 52.07s
```

Trimmed: the runner prints its inert-probe and lane preamble above these lines.

The four new tests fail against the stack base exactly where they must — the admission test
fails, and every refusal test passes on both builds, which is the subset property in
miniature:

```
$ git checkout -- automation/reconcile/reconcile.py    # the stack base's checker
$ python3 -m unittest ...test_evidence_a_linked_task_already_committed_resolves_the_item \
                      ...test_earlier_evidence_admission_refuses_every_weaker_history
F.
======================================================================
FAIL: test_evidence_a_linked_task_already_committed_resolves_the_item
The stuck case: the repair merged before the deletion could be made.
----------------------------------------------------------------------
AssertionError: Lists differ: [] != [<reconcile_queue.Finding object at 0x104baaf90>]

Ran 2 tests in 2.926s

FAILED (failures=1)
```

**Clean tree: zero spawn delta.** Five interleaved rounds, both builds, same clone:

```
$ python3 spawncount.py before/.../reconcile.py after   # and after/.../reconcile.py
parent  queue-resolution              0.092s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
patched queue-resolution              0.094s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
parent  queue-resolution              0.090s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
patched queue-resolution              0.093s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
parent  queue-resolution              0.101s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
patched queue-resolution              0.097s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
parent  queue-resolution              0.096s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
patched queue-resolution              0.102s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
parent  queue-resolution              0.105s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
patched queue-resolution              0.098s findings=0 spawns=9 TOTAL git spawns: 248  findings: 0
```

`spawncount.py` runs the check registry once but the harness counts the whole run twice, so
every number below is two evaluations of one staged deletion.

**Deletion staged: +6 spawns, all three shapes accounted for.**

```
$ sh stage_stuck_deletion.sh after
$ python3 spawncount.py before/.../reconcile.py after
queue-resolution              0.815s findings=1 spawns=143
TOTAL git spawns: 386  findings: 2
$ python3 spawncount.py after/.../reconcile.py after
queue-resolution              0.995s findings=0 spawns=149
TOTAL git spawns: 392  findings: 1

    2  queue-resolution  git --no-replace-objects ls-tree -r -z <oid> -- tasks
    2  queue-resolution  git --no-replace-objects log --format=%H%n%B%x00 <oid> -- automation/reconcile/reconcile.py
    2  queue-resolution  git --no-replace-objects ls-tree -r --name-only <oid> -- tasks
```

Three spawns per evaluated evidence path: the task-link listing, the reachability log, and
the one `task_status_at` for the one candidate commit that named an admitted task.

**What the `task_ids_linking_queue_at` optimisation actually buys.** With the base branch's
object reader available, the pre-optimisation body costs the same spawns, because the tree
cache already answers its per-task lookups, and the times overlap:

```
$ for i in 1..5; do spawncount.py unopt/.../reconcile.py after ; spawncount.py after/.../reconcile.py after ; done
unoptimised queue-resolution              1.035s findings=0 spawns=149
optimised   queue-resolution              0.945s findings=0 spawns=149
unoptimised queue-resolution              0.927s findings=0 spawns=149
optimised   queue-resolution              0.943s findings=0 spawns=149
unoptimised queue-resolution              0.950s findings=0 spawns=149
optimised   queue-resolution              0.936s findings=0 spawns=149
unoptimised queue-resolution              0.955s findings=0 spawns=149
optimised   queue-resolution              0.919s findings=0 spawns=149
unoptimised queue-resolution              0.951s findings=0 spawns=149
optimised   queue-resolution              0.948s findings=0 spawns=149
```

`unopt/` is this branch's `automation/` with only `task_ids_linking_queue_at` reverted to
the `--name-only` plus per-task `git_artifact_bytes_at` body.

The optimisation is load-bearing on the fallback path — a repository where the raw object
reader cannot start, or a stream Git left unusable, after which every tree lookup is an
`ls-tree` again. `--no-raw-reader` forces `read_raw_git_object` to answer `None`:

```
$ python3 spawncount.py after/.../reconcile.py after --no-raw-reader
queue-resolution              2.764s findings=0 spawns=348
TOTAL git spawns: 755  findings: 1
$ python3 spawncount.py unopt/.../reconcile.py after --no-raw-reader
queue-resolution              2.303s findings=0 spawns=444
TOTAL git spawns: 849  findings: 1
```

96 spawns for two evaluations: **48 saved per `task_ids_linking_queue_at` call**, one per
task record at that revision. Without it, the change would cost 51 spawns per deletion on
that path instead of 3.

## 8. Re-run at `b1895c6d7f17820630da3b1a4c1f073443f6e9c6`

The transcripts above were taken at `767fd554afc8e7f84031ac2a7e3e22b55da2ab32`, before this
file and the worklog were committed. Repeated at the commit that carries them:

```
$ python3 automation/reconcile/reconcile.py --check ; echo check exit=$?
reconcile: 0 finding(s)
check exit=0

$ python3 automation/run_tests.py
[... the same 11 PASS lines ...]
tests: 11/11 files passed
test elapsed: 26.12s

$ sh stage_stuck_deletion.sh after
D  message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
M  tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md
reconcile.py in this edit: NONE STAGED
$ python3 automation/reconcile/reconcile.py --check ; echo FINAL_ACCEPTANCE_EXIT=$?
reconcile: 0 finding(s)
FINAL_ACCEPTANCE_EXIT=0

$ python3 replay.py after/.../reconcile.py after --range root:b1895c6d7f17820630da3b1a4c1f073443f6e9c6 > f-new.txt ; echo new exit=$?
new exit=1
$ python3 replay.py before/.../reconcile.py after --range root:b1895c6d7f17820630da3b1a4c1f073443f6e9c6 > f-old.txt ; echo old exit=$?
old exit=1
$ tail -1 f-new.txt
reconcile: 55 finding(s)
$ diff f-old.txt f-new.txt && echo IDENTICAL AT FINAL TIP
IDENTICAL AT FINAL TIP
```

## Review verdicts (when a review was explicitly run)

No independent review was invoked for this change; `--require-review` was not selected.
