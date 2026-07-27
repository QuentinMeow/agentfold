# Handover — <session slug>

**Session:** <YYYY-MM-DD HH:MM–HH:MM TZ, local time>, <who>
**Task:** <task id, or "none — exploratory">
**Mode:** <autonomous | async | pair>
**Queue projection:** v1
**Queue action-entry schema:** v3

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

<This is a projection of every `Status: waiting` item under
`message-queue/needs-human/`, not a place to originate an ask. Do not include
`awaiting-artifact` or `folding` items: the human cannot act on them. Use one top-level
bullet per actionable item, ordered by `blocking-`, `future-blocking-`,
`non-blocking-`, then queue path. Use exact form:
`- [<rendered Action>](../../../message-queue/needs-human/<kind>/<prefixed-name>.md) <exact compact Why this matters paragraph> <exact compact If you do not respond paragraph>`
The link is the bullet's only link. Copy the two paragraphs from the same queue snapshot
with whitespace normalization only. Action and label may use different inline code,
emphasis, or escapes only when they render identically; every other rendered code point
is exact. Preserve terminal punctuation and any closing quote or bracket. The second
paragraph already begins `If you do not respond, `. Add no labels or other prose. The
relative link must resolve to the exact waiting queue file. In the final chat reply,
preserve the exact rendered label and both paragraphs, but replace the
handover-relative destination with
a chat-resolvable link to the same queue file. Write `None.` when no human items are
waiting.>

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
