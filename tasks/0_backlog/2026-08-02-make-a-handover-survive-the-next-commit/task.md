# Make a handover still be true one commit after it is written

**Claimed-by:** unclaimed
**Filed:** 2026-08-02, by claude, from a cold-boot trial that broke its own handover inside one session
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-make-a-handover-survive-the-next-commit.md`

## Goal

A handover is the record the next reader depends on. Two rules currently guarantee that a
correctly written one goes stale immediately, and nothing detects it.

**The links die by construction.** `templates/handover.md` asks for a task-folder link.
`tasks/AGENTS.md` says the opposite: "Reference tasks by id, never by full path — paths
change with status." An agent following the template writes deep links; the next status
move — which is usually the same session's next commit — kills them. A cold-boot trial did
exactly this and ended the session with three permanently dead links in its own handover.

Nothing catches it. `check_links` skips `history/` wholesale, and `history/AGENTS.md` says
committed bytes are immutable and are never edited or renamed. So the links are unverified
when written, broken a commit later, and unrepairable afterwards.

**The size is O(global queue), not O(session).** `templates/handover.md` says one screen,
then requires projecting every unresolved `needs-human/` item verbatim — its `Action`,
`Why this matters`, and `If you do nothing`. Today that is 11 items and roughly 750 words,
almost none of it related to whatever the session did. The trial's handover was about 40%
unrelated transcription, and its one hand-written entry was wrong, which is what a
transcription task does to anyone doing it by hand.

## The two questions this task must answer

**1. What a handover names a task by.** The obvious repair is an immutable task id rather
than a path, but the projection of `needs-human/` items deliberately requires real clickable
links, so "no links" is not the answer either. Work out which references must survive a
status move and which must be resolvable at write time, and make the template and
`tasks/AGENTS.md` agree. Whatever you choose, a check has to be able to see it — a rule that
only `history/`'s exemption hides is how this happened.

**2. Whether every handover really owes the whole live queue.** This one may be the owner's,
not yours. The rule exists so a reader who was away sees everything waiting on them, and the
root `AGENTS.md` already requires the same set in the chat reply — so the handover copy may
be redundant, or may be the durable half of a deliberately duplicated pair. Decide whether
you can settle it from the contracts; if it turns on what the owner wants from a handover,
file a `needs-human/decisions/` item from `templates/queue/decision.md` written per
`skills/explain-to-human/scenarios/queue-item.md`, list it in `Queue actions`, and do not
block this task on the answer.

## Acceptance criteria

- [ ] WHEN a handover is written and the session then moves its task to another status
      folder, EVERY reference in that handover SHALL still resolve. Demonstrate with the
      trial's exact sequence: write the handover, move the task, re-check.
- [ ] `templates/handover.md` and `tasks/AGENTS.md` state one rule about naming a task, not
      two. Quote both after the change and show they agree.
- [ ] A broken reference in a new handover is caught by something. If that means narrowing
      `check_links`'s `history/` exemption to pre-existing records rather than new ones,
      say so in `design.md` and show the check firing on a deliberately broken new handover
      and staying silent on the existing archive.
- [ ] Question 2 is either settled with its argument in `design.md`, or filed as a decision
      item listed in `Queue actions`. Not left unaddressed.
- [ ] Existing handovers under `history/` are unedited. They are immutable records, and a
      template change is not a licence to rewrite them.
- [ ] `python3 automation/reconcile/reconcile.py --check` passes and
      `python3 automation/run_tests.py` passes, real output in `verification.md`.
- [ ] `design.md` carries the completed core-fit receipt from `templates/task/design.md`.

## Links

- The template that asks for the dying link: `templates/handover.md`
- The rule it contradicts: `tasks/AGENTS.md`
- Immutability of records, and the `history/` exemption's justification: `history/AGENTS.md`
- What a handover is for, and how to write one: `skills/explain-to-human/scenarios/handover.md`
