# Does the first-class message-queue contract preserve the right amount of freedom?

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.
**Full context:** `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`; `message-queue/AGENTS.md`; `handbook/principles/files-as-messages.md`
**Resolution evidence:** `memory/decisions/2026-07-23-first-class-queue-review-disposition.md`
**Review target:** git:acc23b6289f5ca66744718af379aba0468be93e2...932ff80bf0ab9d9d813f821c46d271f664744360
**Review revision:** git:acc23b6289f5ca66744718af379aba0468be93e2...932ff80bf0ab9d9d813f821c46d271f664744360
**Reviewed revision:** ______
**Review outcome:** pending
**Blocks at:** transition:merge task:2026-07-23-first-class-message-queue
**Until then:** Implementation, tests, and independent review may continue.
**Look-at:** `message-queue/AGENTS.md`; `handbook/principles/files-as-messages.md`
**Why-you-might-care:** This changes every human and durable cross-session agent action surface in AgentFold.
**If-you-do-nothing:** The task may be reviewed and revised, but it does not merge.

## What you need to know

PR #4 created detailed human questions only in GitHub after its generic queue review was
resolved. The proposed repair makes one queue file own every pending action; PRs, chat,
issues, tasks, and handovers may summarize and link that file but cannot invent an ask.

## Differences

- **Queue-owned actions:** survive sessions and are mechanically named/linked, at the
  cost of a small file for every durable action.
- **Independent channel asks:** are cheaper to write, but can disappear from the
  repository or disagree with a handover.
- **Timing prefixes:** expose “blocks now,” “blocks at a named boundary,” and “never
  blocks” in filenames without prescribing how an agent completes the action.

## Example

A PR may say “Review assurance claims” only by linking its self-contained queue item.
If the PR body is later edited or the agent session disappears, the owner still sees the
same action, explanation, example, and source pointer in `needs-human/`.

Do not answer this item while its status is `awaiting-artifact`; the exact implementation
diff is not yet published. The publication step replaces the pending target with the PR.

When this becomes waiting, copy `Review revision` into `Reviewed revision` with the
answer.

**Your review:** ______
