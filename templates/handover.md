# Handover — <session slug>

**Session:** <YYYY-MM-DD HH:MM–HH:MM TZ, local time>, <who>
**Task:** <task id, or "none — exploratory">
**Mode:** <autonomous | async | pair>
**Queue projection:** v1

One screen max, plain language, for a teammate who was away. Depth goes in the task
folder; this file links to it.

## What happened

<3–5 bullets, outcomes not process. "Added X; it now does Y." Spell things out —
no shorthand invented mid-session.>

## How it works now

<2–4 sentences on the state of the thing you touched, as it stands right now.>

## Decisions made for you

<One line each + link to the ADR or design.md section. "None" is a fine answer.>

## Needs your attention

<This is a projection of the `message-queue/needs-human/` items that still await the
human — `history/AGENTS.md` defines which states those are — and never a place to
originate an ask. Use one top-level bullet per such item, ordered by `blocking-`,
`future-blocking-`, `non-blocking-`, then queue path. The bullet's first content is
`[<the queue item's exact Action text>](../../../message-queue/needs-human/<kind>/<prefixed-name>.md)`.
That is the bullet's only link. Append exactly
` — Why-you-might-care: <copied field> || If-you-do-nothing: <copied field>`,
copying both values from the same queue snapshot with only whitespace reflow allowed.
No other prose can appear. The relative link must resolve to the exact live queue
file. Repeat this section verbatim in the final chat reply. Write `None.` when no
human item is awaiting the human — an item an agent has claimed or already has a
committed answer for is resolved, so it belongs here in neither file nor chat.>

## Dead ends

<What was tried and abandoned, and why — so the next session doesn't retry it.
Failed approaches are exactly what compaction and chat lose. "None" is fine.>

## Next steps

<Write `None.` or one top-level bullet per assigned `needs-agent/` action. Use the
same strict link form as above, but make that one relative queue link the bullet's only
content; its label exactly copies the item's `Action`. Do not add prose or another
link. This section may project a scoped subset of live agent actions; it need not list
unrelated global agent work.>

## Deep links

- Task folder: <link> · Worklog: <link> · Verification: <link>
- Commits: <range or list>
