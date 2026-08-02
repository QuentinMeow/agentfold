# Pick up reporting the readability rules as advisory findings

**Status:** open
**Filed:** 2026-08-02, by claude, from the folded readability-enforcement answer — `memory/decisions/2026-08-02-readability-enforcement-disposition.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-advise-on-explanation-shape/task.md`
**Request kind:** task-pickup
**If unanswered:** The readability standard stays prose that nothing checks; agents that ignore it produce messages the owner only catches by reading them.

## What you need to know

The owner answered the readability-enforcement question with Option B: the structurally
visible rules become advisory reconciler findings that print and are counted but never fail
a commit. Nothing implements that yet.

Three rule families are in scope — required headings present and in template order, an
`*Example consequence:*` under every option in a decision, and a pull-request `## TL;DR`
holding three to six items. Queue items are repository files the reconciler already walks;
a pull-request body is not, so its rules belong to the gate that already parses one. Nothing
semantic is in scope.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
