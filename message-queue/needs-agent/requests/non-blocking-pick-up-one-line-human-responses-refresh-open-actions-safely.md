# Pick up safe one-line human-response projection refreshes

**Status:** open
**Filed:** 2026-08-04, by codex, from task `2026-08-04-let-one-line-human-responses-refresh-open-actions-safely`
**Action:** Claim the one-line human-response projection task and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-04-let-one-line-human-responses-refresh-open-actions-safely/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-08-04-let-one-line-human-responses-refresh-open-actions-safely/plan.md`
**Request kind:** task-pickup
**If unanswered:** Humans can still supply answers, but agents must manually include a generated companion that the literal one-edit contract currently forbids.

## What you need to know

Commit `a2310ce6f0104c2235ce2ea322102c7022b0f6d5` changed one answer line but required a
second 20-line generated-file diff to pass the blocking reconciler. Existing tests prove
the response rule and digest transition separately, but never compose them through the
installed commit hook or a linked-worktree candidate index.

## Done when

The task has one claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal task link have been removed in the claim commit.
