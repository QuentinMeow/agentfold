# Does the first-class message-queue contract preserve the right amount of freedom?

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** Review the queue-ownership invariant, timing prefixes, and enforcement before this task merges.
**Full context:** `tasks/1_in-progress/2026-07-23-first-class-message-queue/design.md`
**Blocks at:** transition:merge task:2026-07-23-first-class-message-queue
**Until then:** Implementation, tests, and independent review may continue.
**Look-at:** task branch diff against `main`; the PR link will be added after publication
**Why-you-might-care:** This changes every human and durable cross-session agent action surface in AgentFold.
**If-you-do-nothing:** The task may be reviewed and revised, but it does not merge.

## Context

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

**Your review:** ______
