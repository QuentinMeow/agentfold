# Handover — doc-depth-invariants

**Session:** 2026-07-22 01:00–01:22 PDT, claude (chat session with the repo owner)
**Task:** 2026-07-22-doc-depth-invariants, then 2026-07-22-linked-asks-in-replies,
then 2026-07-22-split-is-instructions-not-readership
**Mode:** async

One screen max, plain language, for a teammate who was away. Depth goes in the task
folder; this file links to it.

## What happened

- The owner asked (in chat) whether two ideas were baked into the design: queue
  messages as simple, disposable, *regenerable* summaries — like retryable API calls —
  with the durable background living in task/design folders; and the README as a
  human-only landing page free of deep technical detail.
- Both were mostly implicit. Made them explicit: `message-queue/AGENTS.md` now states
  items are projections of state that lives elsewhere; `handbook/decision-guide.md`
  tells writers durable background belongs in the task folder; the root `AGENTS.md`
  states the README depth rule.
- Made the README rule mechanical: `reconcile.py` now budgets the root `README.md` at
  140 lines (same `agents-budget` check as contract files); verified the check fires.
- Chose not to add a `references/` folder — `handbook/` already plays that role and
  the naming conventions ban generic buckets.
- Second chat rule, same conversation: a surfaced `needs-human/` item is a clickable
  link plus a few sentences of context, never a bare name. Format pinned in
  `templates/handover.md`; ritual step 4 and the session-handover skill now require it
  (task 2026-07-22-linked-asks-in-replies).
- Third chat rule: the README/AGENTS split is about instructions, not readership —
  agents write and may skim the README, but it never carries agent instructions, and
  the root `AGENTS.md` is self-contained. Reworded the root contract intro and the
  README tour line (task 2026-07-22-split-is-instructions-not-readership).

## How it works now

Queue items are documented as regenerable: they carry only an acting summary plus
links, so deleting or rewriting one is always safe; the sole unique content an item
ever holds is a not-yet-folded human answer. The README is capped like a contract
file — additions must displace something or push depth into `handbook/`.

## Decisions made for you

- All four rules were directed by you in chat; recorded as ADRs:
  `memory/decisions/2026-07-22-queue-items-are-regenerable-projections.md`,
  `memory/decisions/2026-07-22-root-readme-line-budget.md`,
  `memory/decisions/2026-07-22-surfaced-asks-are-links-plus-context.md`, and
  `memory/decisions/2026-07-22-readme-carries-no-agent-instructions.md`.

## Needs your attention

- Nothing is open in `message-queue/needs-human/` — no decisions, clarifications, or
  reviews are waiting.

## Next steps

- Nothing pending from this session. Commits are local only — push to origin when you
  want them published.

## Deep links

- Task folders: `tasks/4_done/2026-07-22-doc-depth-invariants/`,
  `tasks/4_done/2026-07-22-linked-asks-in-replies/`, and
  `tasks/4_done/2026-07-22-split-is-instructions-not-readership/` (each holds its
  worklog and verification)
- Commits: 10f9279 (claim + ADRs), c464740 (branch work), merge + 72426ab, 04e975d;
  second task: claim + ADR, branch work, merge, review/done moves (see git log)
