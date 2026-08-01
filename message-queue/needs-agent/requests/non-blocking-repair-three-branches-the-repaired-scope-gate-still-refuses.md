# Repair the three pull-request branches the repaired scope gate still refuses

**Status:** open
**Filed:** 2026-08-01, by claude, from replaying every blocked pull request against the repaired projection gate — task 2026-08-01-admit-a-candidates-whole-task-scope
**Action:** File the missing task record for the branch named task/2026-07-31-redo-stranded-review-disposition (or rename that branch), and rewrite the "What to review" section of pull requests 41 and 45 to project every live human queue action their scope now binds.
**Full context:** `automation/AGENTS.md`
**Resolution evidence:** `roadmap/current-state.md`
**If unanswered:** Those three pull requests stay red. The other three the same gate refused — 36, 42 and 48 — pass without any change, and nothing else in the repository is affected.

## What you need to know

The projection gate used to refuse any candidate whose diff mapped to more than one task
folder, with a hard input error. It now binds every task the candidate carries and requires
the projection to cover all of them. Replaying all six blocked pull requests against the
repaired gate leaves three that are genuinely wrong, and they are wrong in two different ways.

The branch behind pull request 46 names a task whose record exists in **no commit on any
branch**. It was never filed. The gate is right to refuse it: a branch that declares a task
must carry that task's evidence. Either file the task record and claim it, or move the work
onto a non-task branch whose scope is the two tasks it actually edits.

Pull requests 41 and 45 both say `No queued action requested.` while the tasks their
candidates carry own live human actions — four for 41, one for 45. That is the projection
invariant doing its job: a reviewer of 41 should be told that the three in-review tasks it
edits still owe the human three reviews and a decision. The repair is in the pull-request
description, not in the gate.

The exact replay output for all six is in the verification record of task
2026-08-01-admit-a-candidates-whole-task-scope.

## Done when

The task/2026-07-31-redo-stranded-review-disposition branch either carries its own task
record or no longer claims to be a task branch, and the descriptions of pull requests 41 and
45 project every live human queue action their bound scope reports.
