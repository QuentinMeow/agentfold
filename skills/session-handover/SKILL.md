---
name: session-handover
description: The end-of-session ritual — leave the repo so the next reader (human or agent) needs nothing from your head. Use when ending any session that did work, before the final reply.
---

# Session handover

Chat evaporates; files remain. Run this before ending any session that changed
anything.

## Steps

1. **Task state**: append this session to the task's `worklog.md`; check off completed
   `plan.md` steps; record real command output in `verification.md` if you verified;
   `git mv` the task if its status changed.
2. **Queue state**: `message-queue/` is the canonical live ledger. File every pending
   human action and every agent action that must survive this session using
   `templates/queue/` and `message-queue/AGENTS.md`; delete resolved items in the
   resolving commit.
3. **Delivery timing**: name each live item `blocking-<slug>.md` when named work cannot
   proceed now, `future-blocking-<slug>.md` when work may continue only until a stated
   date/event/transition, or `non-blocking-<slug>.md` when it never stops work. A human
   item briefly distinguishes the choices, gives a concrete example, states the safe
   result if unattended (remaining stopped is valid), and links the full context.
   Describe arbitrary event/transition/operation evidence as agent-attested unless a
   controlled adapter supplies hard assurance.
4. **Memory**: a decision folded → ADR in `memory/decisions/`; a failure understood →
   lesson in `memory/lessons/<area>/` (merge into an existing lesson first —
   `memory/AGENTS.md`); then `reconcile.py --fix-index`.
5. **Roadmap**: if reality changed, update `roadmap/current-state.md` (bump
   `Last-updated:`).
6. **Handover file**: copy `templates/handover.md` to
   `history/conversations/<YYYY-MM-DD-HHMM><TZ>-<slug>/handover.md` (session start,
   local time + timezone abbreviation). One screen, plain
   language, written for a teammate who was away: what happened, how it works now,
   what needs their attention, dead ends not to retry, links to depth. No invented
   shorthand.
7. **Project, do not originate**: handovers, task notes, chat, and external review
   surfaces only summarize and link live queue items; they never become a second action
   ledger. End the final reply with the handover's "Needs your attention" projections,
   each linking its queue item with enough context to act. Repeat still-open items.

## Skip conditions

There are none for existence — every session that did work leaves a handover
(`history/AGENTS.md`). `pair` mode sessions where the human watched everything live
may compress it to a few lines, but pending actions still get queue files.
