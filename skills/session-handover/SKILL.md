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
2. **Queue state**: file every unresolved question as a proper queue item
   (`templates/queue/`); delete every item you resolved, in the resolving commit.
3. **Memory**: a decision folded → ADR in `memory/decisions/`; a failure understood →
   lesson in `memory/lessons/<area>/` (merge into an existing lesson first —
   `memory/AGENTS.md`); then `reconcile.py --fix-index`.
4. **Roadmap**: if reality changed, update `roadmap/current-state.md` (bump
   `Last-updated:`).
5. **Handover file**: copy `templates/handover.md` to
   `history/conversations/<YYYY-MM-DD-HHMM><TZ>-<slug>/handover.md` (session start,
   local time + timezone abbreviation). One screen, plain
   language, written for a teammate who was away: what happened, how it works now,
   what needs their attention, links to depth. No invented shorthand.
6. **Final reply**: end with the handover's "Needs your attention" entries, formatted
   per `templates/handover.md` — each a clickable link to the queue item plus 2–3
   sentences of context, never a bare name. Repeat items from previous sessions that
   are still open; humans skim, so polite repetition is the delivery mechanism.

## Skip conditions

`pair` mode sessions may skip steps 5–6 ceremony *only* if the human watched everything
live — but decisions still get files (chat is the only channel with no trace), and the
reconciler still expects a handover for any conversation folder you created.
