# Pick up the development-cycle acceleration continuation

**Status:** open
**Filed:** 2026-07-26, by codex, from the owner's continuation request in chat
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-26-continue-development-cycle-acceleration/task.md`
**Request kind:** task-pickup
**If unanswered:** The existing service-only fast lane remains the only acceleration; small harness changes continue to pay a multi-minute full-suite cost, and the broader bottleneck investigation waits.

## What you need to know

The current test suite is green in its latest recorded complete runs, but it is too slow and
variable for an inner development loop. Draft pull request 16 gives known service-only changes
roughly one-second feedback, while automation and repository-record changes still trigger the
roughly three-to-four-minute complete suite. The task defines a strict sub-60-second small-change
budget and an eventual-correctness model: focused local checks now, required complete CI on every
pull request, and one deliberate full run at publication or merge boundaries.

The task also carries the exact starting state of the separate unpushed queue-resolution branch,
including five fifth-panel blockers. After the test policy is working for harness changes, it
asks independent agents to inspect and debate the repository's remaining development bottlenecks
before the main agent chooses and publishes one bounded development-speed pull request.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this request
and its reciprocal `Queue actions` link have been removed in the claim commit.
