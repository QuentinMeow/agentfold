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

<This is a projection of every open `message-queue/needs-human/` item, not a place to
originate an ask. Order entries by filename class: `blocking-`, then
`future-blocking-`, then `non-blocking-`. Never use a bare name: write a clickable
markdown link plus enough context to act without opening anything —
`[short name](../../../message-queue/needs-human/<kind>/<prefixed-name>.md)` followed
by 2–3 sentences explaining the choice, why it arose, and the named boundary or
unattended outcome. New handovers must use a relative link that resolves to the exact
queue file; an external URL or a path copied from another folder does not count. The
queue file remains canonical and links to the full source. Repeat this section
verbatim in the session's final chat reply. Write `None.` when no items are open.>

## Dead ends

<What was tried and abandoned, and why — so the next session doesn't retry it.
Failed approaches are exactly what compaction and chat lose. "None" is fine.>

## Next steps

<What the next session should probably do first. Any action assigned to a human or
another session must already have a canonical queue item linked here; do not create an
orphan ask in a handover.>

## Deep links

- Task folder: <link> · Worklog: <link> · Verification: <link>
- Commits: <range or list>
