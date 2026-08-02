# Verification — record that a format migration is one-way

**Verified:** 2026-08-02 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

This task was folded into its parent rather than performed, so what needed verifying is
the fold's two preconditions and the fact that nothing was dropped in it. The task's own
acceptance criteria — the `git revert` reproduction, the design choice, the fixture — are
deliberately **not** ticked: they were not done, they were moved, and they are now the
parent's to discharge.

## Precondition 1 — the task says to close it if the migration does not proceed

```
$ grep -n "only worth doing" tasks/1_in-progress/2026-08-01-record-that-a-format-migration-is-one-way/task.md
This task is only worth doing if that migration proceeds. If the eight legacy items age
```

The sentence continues: "out and no live item is ever rewritten, close it as not-needed
with that reason recorded."

## Precondition 2 — the parent really did bind the requirement

Before the fold, the parent's acceptance criteria contained the link that made this task
its dependency:

```
$ git show 814e4ad~1:tasks/0_backlog/2026-08-01-countersign-the-live-human-item-migration/task.md | grep -n -A1 "one-way property"
- [ ] `design.md` accounts for the one-way property recorded in task
      `2026-08-01-record-that-a-format-migration-is-one-way`
```

That is the condition the brief set for folding rather than reporting a mismatch, and it
held.

## The migration has not begun, so the trigger condition is unmet

```
$ grep -n "Claimed-by" tasks/0_backlog/2026-08-01-countersign-the-live-human-item-migration/task.md
**Claimed-by:** unclaimed

$ ls -R message-queue/needs-human/
clarifications
decisions
reviews

message-queue/needs-human//clarifications:
README.md

message-queue/needs-human//decisions:
non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md
non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md
non-blocking-re-ask-the-older-questions-in-plainer-words.md
README.md

message-queue/needs-human//reviews:
future-blocking-review-detector-failure-state.md
future-blocking-review-guardrail-authority-boundary.md
future-blocking-review-revised-assurance-profile-scope-and-egress.md
future-blocking-review-sensitive-data-recovery.md
non-blocking-rereview-human-action-files.md
non-blocking-review-layered-development-workspace.md
non-blocking-review-template-first-explanation.md
non-blocking-review-test-runner-git-environment-isolation.md
non-blocking-review-the-explanation-standard.md
non-blocking-review-the-pull-request-shape.md
README.md
```

Ten live review items and three live decisions, all still in their original format.

No live item has been rewritten; the legacy items are still the originals. Closing is the
author's own stated instruction rather than this session's judgement.

## Nothing was dropped in the fold

The parent now carries both the property and the obligations:

```
$ grep -n "one-way\|queue_mutation_problem\|supersede-based" tasks/0_backlog/2026-08-01-countersign-the-live-human-item-migration/task.md
14:carve-out in `queue_mutation_problem`, and the carve-out was proven exploitable.
46:## The migration is one-way, and the recovery path has to be chosen here
48:Folded in on 2026-08-02 from task `2026-08-01-record-that-a-format-migration-is-one-way`,
56:`queue_mutation_problem` refuses it as "action identity changed while the queue item
80:- [ ] `design.md` states how `queue_mutation_problem` admits the rewrite, and why that
83:      supersede-based recovery path for the one-way property stated above, says why the
```

Lines 46–56 are the folded property; line 83 is the criterion that replaced the link to
this task, now stating the choice, the rejected alternative, the fixture, and the revert
reproduction in its own words.

## The repository is still green after the fold

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
exit=0

$ python3 automation/run_tests.py
tests: 12/12 files passed
test elapsed: 121.11s
```

## Review verdicts (when a review was explicitly run)

No review panel was run. This is a records-only fold; no behaviour changed and no core path
was touched, so no `## Core fit` receipt is owed.
