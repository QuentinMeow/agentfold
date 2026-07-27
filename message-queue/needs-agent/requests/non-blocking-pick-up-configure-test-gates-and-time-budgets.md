# Pick up the configurable test-gates and time-budgets task

**Status:** open
**Filed:** 2026-07-27, by codex, from task 2026-07-27-configure-test-gates-and-time-budgets
**Action:** Claim the linked backlog task, then implement its configuration, routine/final gates, timing evidence, and deterministic performance-task filing as one bounded workstream.
**Full context:** `tasks/0_backlog/2026-07-27-configure-test-gates-and-time-budgets/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/worklog.md`
**Request kind:** task-pickup
**If unanswered:** Existing acceleration work may continue, but automation and cross-cutting changes keep paying the current multi-minute full-suite cost and no configured timing regression automatically creates investigation work.

## What you need to know

The current commit hook runs admission, reconciliation, and the full isolated test suite in
sequence. Recorded clean full-suite runs take about 215–221 seconds, and two Git-heavy test files
account for about 89% of that time. A narrow service selector is already fast, but it does not
solve automation and cross-cutting changes.

The linked task chooses a two-lane design. Routine feedback has a repository-configured 60-second
starter budget and may defer only reversible coverage. Complete verification runs manually or at
one configured final-stage boundary. Credentials, PII, authorization, destructive operations,
publication, deployment, and other configured one-way-door scopes cannot be weakened to meet the
clock. Any gate that exceeds its configured target must create one deduplicated investigation
task with real timing evidence.

Read `design.md` before implementation. It explains the alternatives, recommended configuration,
gate sequence, exact-evidence cache boundary, task-filing durability, and consequences. `plan.md`
is the eight-step implementation order.

## Done when

The task is claimed and moved to `tasks/1_in-progress/` in the same coordination commit that
removes this pickup request, and the claimant has recorded the start in its worklog.
