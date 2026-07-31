# Pick up the contract-rule collapse task

**Status:** open
**Filed:** 2026-07-31, by claude, from an audit of restated and unenforced contract text
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-31-collapse-restated-contract-rules/task.md`
**Request kind:** task-pickup
**If unanswered:** The task stays unclaimed in backlog; contract precedence keeps citing itself in a loop, contracts keep describing unwired mechanisms in the present tense, and two ADR chains keep disagreeing with the generated memory index.

## What you need to know

Root `AGENTS.md` and `handbook/AGENTS.md` each defer precedence to the other, so for any
file under `handbook/` neither rule ever resolves. Separately, `README.md`,
`history/AGENTS.md`, `tasks/AGENTS.md`, `CONTRIBUTING.md`, `handbook/adoption-guide.md`,
and `handbook/naming-conventions.md` describe auto-filed retries, configurable guard
modes, a third branch lane, a deleted design sketch, and an unqualified link check —
none of which exists as described. Finally, one ADR is marked `decided` while its
successor claims to supersede it, and three edge-graph ADRs are all `decided` while two
of them overturn clauses of the first, so `memory/index.md` still advertises the
overturned mandates. The task file records the exact files and sentences, so no
re-derivation is needed.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
