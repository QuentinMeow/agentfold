# Stop a moved base from failing the reconciler check on a pull request

**Claimed-by:** codex planner / sol-high implementer
**Filed:** 2026-08-02, by claude, reproduced on three separate pushes to pull request #65
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-track-github-issue-78-stale-base.md`

## Goal

The `reconcile-and-test` job fails on a pull request when the base branch moves between the
event being emitted and the job resolving the candidate. Observed on pull request #65,
reproducing on three separate pushes:

```
Git snapshot error: captured candidate is neither the --range head nor an exact
base+head synthetic merge
```

exiting 2. GitHub had computed `refs/pull/65/merge` against `main` at one commit while the
same event payload named an earlier commit as the base. The `push`-event run of the same
job stayed green throughout, so the failure is specific to resolving a pull request's merge
ref against a base that has since advanced.

This is the same stale-base race that task
`2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack` fixed for
`review-state-action-projection`, reached through a different job. That task deliberately
stayed in its own scope and did not touch this one.

Two consequences make it worth fixing rather than tolerating. A check that goes red for a
reason unrelated to the change trains everyone to ignore it, and this repository already
records a case of a pull request merging with checks red for 47 minutes
(`memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md`).
And the owner's stated exit from that decision is to make `reconcile-and-test` a required
check once the repository is stable — which cannot happen while it fails on ordinary
concurrent merges.

## What the fix probably looks like, and what to check first

`review-state-action-projection` now interrogates the fetched merge commit instead of
comparing revisions: exactly two parents, second parent equal to the event's head sha, first
parent containing the event's base sha. A merge commit's parent ids are covered by its own
object id, so that binds the candidate to the event rather than to a payload field. Read
that solution in `.github/workflows/harness.yml` before designing a second one — the
repository's rule is that a new external-artifact boundary uses a canonical gate and thin
adapters, not a parallel mechanism.

Establish first whether the right repair is in the workflow, in `validate_range_candidate`,
or in both. Exit 2 means "this check could not run", which is the correct code for an
unreadable candidate; the defect may be that the candidate is readable and the acceptance
rule is too narrow, rather than that the error handling is wrong.

## Acceptance criteria

- [ ] WHEN a pull request's base advances between the event and the job, THE
      `reconcile-and-test` JOB SHALL resolve the recomputed merge candidate and check it,
      rather than exiting 2. Demonstrate with a fixture reproducing the observed state, not
      by describing it.
- [ ] WHEN the candidate genuinely is neither the range head nor an exact base-plus-head
      merge, THE JOB SHALL still fail. Prove the guard still bites by removing the new
      admission in a copy and showing the test go red.
- [ ] The repair reuses the parent-interrogation approach already in the workflow, or
      `design.md` argues why a second mechanism is correct here.
- [ ] Any retry is counted and bounded, and exhaustion fails. No path where running out of
      attempts produces a pass.
- [ ] `python3 automation/run_tests.py` passes, real output in `verification.md`.
- [ ] `design.md` carries the completed core-fit receipt from `templates/task/design.md`.

## A second, smaller finding to judge — do not assume it is real

While restacking pull request #65 onto current `main`, a force-push produced
`[queue-resolution] ... divergent update discarded a live old-tip action` for a queue item
another agent had properly deleted on `main` between the two bases. The next ordinary push
cleared it. That looks like a false-positive class in the displaced-tip comparison — the
old tip's live action was resolved legitimately, not discarded. Reproduce it before
treating it as a defect; if it is real and separable, file it rather than widening this task.

## Links

- The sibling repair to read first: task `2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack`
- Why a red check currently costs nothing, and the owner's stated exit: `memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md`
- Why a green trunk is not proof: `memory/lessons/automation/green-branches-can-merge-to-red.md`
