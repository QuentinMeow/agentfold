# Scenario — the handover

A handover is written for whoever arrives next — another agent, or the owner a week later
— and it is the only thing that survives the session. Chat evaporates, context windows are
compacted, and the reasoning that felt obvious while you were working is gone by morning.

**This file does not define the format.** The schema is `templates/handover.md`; where the
file lives, which queue items it projects, and the exact link grammar of the
"Needs your attention" section are owned by `history/AGENTS.md`. The end-of-session ritual
that produces it is `skills/session-handover/`.

What this file owns is how to write the prose so the next reader needs nothing from your
head. Read `../reference.md` for the craft.

## Lead with how alarming the situation is

The first thing the next reader needs is not what you did — it is whether anything is on
fire. Medicine solved this with a one-word triage state at the top of every shift handover,
and it works here for the same reason: it tells the reader how carefully to read the rest.

Open "What happened" with the state of the world, in one line:

- *Nothing is in flight; every branch is pushed and every check is green.*
- *One branch is half-migrated: the schema change is applied on staging and not on
  production, and staging deploys will fail until it is finished.*

Then the outcomes. Never open a handover with process narration.

## Outcomes, not activity

Each bullet says what is different now and what it was before. "Added X; it now does Y" is
the shape. A list of files touched is not a handover — the next reader can get that from
`git log`, and what they cannot get is why any of it mattered.

Spell everything out. Shorthand you invented during the session is exactly what the next
reader cannot decode, and abbreviations that felt obvious at 2am are the first thing to
misread.

## Write the contingencies you are carrying in your head

This is the part that is always lost and never missed until it hurts. Before you stop, ask:
*what do I currently know that would change what the next person does?*

Write those as `if X then Y` lines:

> If the reconciler reports `queue-schema` findings on the three older items, that is
> expected — they were written under the previous format and are records, so they are never
> reformatted. Do not "fix" them.

> If the test run hangs on `test_reconcile_queue`, it is waiting on a Git lock left by an
> interrupted run. Delete `.git/index.lock` and rerun; do not force-kill the suite, which
> leaves fixture repositories behind.

## Dead ends are the highest-value section

What you tried and abandoned, and why, is precisely what compaction and chat destroy — and
without it the next session spends its first hour rediscovering your worst hour.

One line each: what was tried, what happened, and what it means.

> Tried resolving the three stuck reviews by re-pointing their `Review revision` at the new
> bytes. The response field is write-once, so the commit is refused; there is no repair
> path on a live item. The only routes are retract-and-refile or an explicit disposition.

"None" is a fine answer. An empty section that should not be empty is not.

## Needs your attention is a projection, not an ask

Every entry already exists as a file. The handover copies the link and the two fields the
entry schema requires and adds nothing — no second answer slot, no restated question, no
new request that exists only here. `history/AGENTS.md` owns which items appear and exactly
how each entry is written; follow it literally, because it is machine-checked.

If an item has been claimed or already carries a committed answer, it is resolved and does
not belong here — in the file or in the chat reply that repeats it.

## One screen

A handover longer than a screen is a handover nobody reads. Depth lives in the task folder
— `design.md` for the choices, `worklog.md` for the narrative, `verification.md` for the
evidence — and the handover links there. If a paragraph is explaining rather than
orienting, it belongs in one of those files.

## Before you commit it

- [ ] The first line says whether anything is in flight or broken.
- [ ] Every bullet names a difference, not an activity.
- [ ] No shorthand or abbreviation appears that was invented this session.
- [ ] Every `if X then Y` you are carrying is written down.
- [ ] Dead ends are recorded, or the section honestly says there were none.
- [ ] "Needs your attention" projects live items only, in the exact required grammar.
- [ ] It fits on one screen, and the depth is linked rather than inlined.
