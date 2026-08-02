# Verification — Let a queue item resolve when its resolution evidence landed in an earlier commit

**Verified:** 2026-08-02 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

This task shipped no code. It is closed as **superseded**, and what is verified below is
the supersession itself: that another task fixed the defect, that the live instance is
gone, that the dependent task is unstuck, and that this task's own approach was
deliberately not taken. Nothing here claims that this task's acceptance criteria were met —
they were not, and `plan.md` records that instead of checking its boxes.

## The defect was fixed by a different task

`2026-07-30-admit-evidence-that-landed-earlier` shipped the repair as pull request 38.

```
$ git log --oneline -1 c824e0e
c824e0e Merge pull request #38 from QuentinMeow/task/2026-07-30-admit-evidence-that-landed-earlier
```

That task chose a deliberately narrower rule than this one. Its `task.md` states the
measurement that decided it: widening the window to "the evidence changed at some point"
"was measured to make 14 of 14 live ordinary requests deletable with no work at all,
including gates whose stated precondition is a task still unclaimed in `tasks/0_backlog/`."
The shipped rule instead admits evidence that landed earlier only in a commit the
repository already attributes, by a `task:<id>` token in its own message, to a task that
linked the exact queue path, was already past pickup at that commit, and is not the task
the item's own boundary gates.

The replacement rule's own tests are present:

```
$ grep -n "def test_earlier_evidence_admission\|def test_evidence_a_linked_task_already_committed" automation/tests/test_reconcile_queue.py
4186:    def test_evidence_a_linked_task_already_committed_resolves_the_item(self):
4192:    def test_earlier_evidence_admission_refuses_every_weaker_history(self):
4233:    def test_earlier_evidence_admission_needs_the_exact_queue_link(self):
```

## The live instance this task existed for is gone

The stuck request named throughout `task.md` was
`blocking-repair-handover-projection-code-span-copy.md`.

```
$ ls message-queue/needs-agent/requests/ | grep code-span
(exit 1; no output — no code-span request remains)
```

The command exits 1 with no output, which is the expected result and is recorded here as
what actually happened rather than as a claim.

## The task this one was pinning is unstuck

```
$ ls -d tasks/*/2026-07-25-fix-handover-projection-code-span-copy
tasks/4_done/2026-07-25-fix-handover-projection-code-span-copy
```

`task.md` predicted this task would stay at `1_in-progress` "for as long as the item
does". The item is gone and the task is done, so that consequence has cleared.

## This task's own approach was rejected, not merely overtaken

Its unmerged branch was read twice by later work and kept only in part. The caching task's
`design.md` records the split:

```
$ sed -n '22,24p' tasks/4_done/2026-07-30-cache-reconciler-git-object-reads/design.md
An unmerged branch, task/2026-07-26-resolve-queue-items-whose-evidence-already-merged,
already batched these reads. Its resolution-evidence rule was found harmful and is being
discarded; its caching is not, and this task extracts only the caching.
```

And the replacement-ref task recorded the same verdict as a checked acceptance line:

```
$ grep -n "NOT ported" tasks/4_done/2026-07-31-finish-the-replacement-ref-boundary/task.md
49:- [x] The creation-baseline rule, `ordinary_request_resolution_evidence_problem`, and the 24 evidence-lineage tests are NOT ported — they were rejected by measurement.
```

The creation-snapshot baseline this task's `plan.md` step 2 chose is exactly the rule those
two records discard. So this is a supersession with a negative verdict on the approach, not
a duplicate of finished work.

## What was not run

No test suite run and no reconciler run is recorded as evidence *for this task*, because
this task changed no code and its branch was never merged. The suite that covers the
replacement rule belongs to `2026-07-30-admit-evidence-that-landed-earlier` and is recorded
in that task's own `verification.md`. The reconciler run that admits the commits closing
this task is the pre-commit hook's, in those commits.
