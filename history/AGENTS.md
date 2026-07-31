# history/ — conversation record

**Queue projection schema:** v1
**Queue action-entry schema:** v2
**Queue liveness schema:** v1

One folder per conversation/session that did work:
`conversations/YYYY-MM-DD-HHMM<TZ>-<kebab-slug>/` — session start as **local time
plus timezone abbreviation** (e.g. `2026-07-22-0014PDT-fix-cli-crash`; use `UTC` if
your zone has no letter abbreviation). Every folder **must** contain a `handover.md`
— missing one is a blocking reconciler finding; only `--file-retries` would queue it.

## handover.md (schema: `templates/handover.md`)

The handover is for a human who was away: what happened, how it works now, what needs
their attention — one screen maximum, plain language, no invented shorthand. Depth
never goes in the handover; it goes in the task folder (worklog, design, verification)
and the handover links there. End-of-session ritual: root `AGENTS.md`;
`skills/session-handover/` walks through it.

The repository-local schema field above activates checking without imposing an
AgentFold date or retained legacy folder on forks. Existing unmarked records remain
records; every newly added handover must declare `**Queue projection:** v1` and exactly
project the `message-queue/needs-human/` actions its liveness version selects, in
filename-timing order. It never originates an ask. Resolved targets may later disappear
because git history archives past delivery. Range-based checks evaluate the handover and
queue together at its creation commit, so later additions or resolutions never rewrite it.
Once committed, v1 handover bytes are immutable; record corrections in a new handover.
`Next steps` is `None.` or links assigned work to live `needs-agent/` items; it never
originates a cross-session action.

The action-entry marker versions strict projection syntax: version 1 freezes the entry
contract existing records passed when created; version 2 adds raw-HTML and origin checks.
The liveness marker separately versions *which* human actions any projection contains —
this section and the chat reply alike. Version 1 selects only **unresolved** ones: an
action awaits its owner until a concrete `**Your answer:**` or `**Your review:**` is
committed; `folding` only moves an answered item on, `awaiting-artifact` binds nothing to
judge, and every other state — unreadable or unrecognised — stays projected.
Each post-activation entry is one top-level bullet whose first content is
`[<exact queue Action>](<one actor-matching live queue path>)`. Human entries append
` — Why-you-might-care: <field> || If-you-do-nothing: <field>`, copying both from that
snapshot, in timing-then-path order; agent entries hold only the link and may project
just work assigned here. The creation/admission edge selects the highest active version;
parallel history joined with an activation uses that version. A rejecting grammar
expansion requires a new schema version instead of retroactively changing immutable
records. All three schema markers are sticky while `history/` remains. Queue-projection adoption
freezes every existing handover path, including an unmarked legacy record: delete it when
retention permits, but never edit or rename it; corrections use a new conversation path.

## Other files in a conversation folder (optional)

- `transcript.md` — pointer to or export of the raw session log, when available
- `artifacts/` — files produced during the session worth keeping but belonging to no
  service (analysis notes, comparison tables)

## Retention

Conversation folders older than ~180 days are pruned by the memory gardener — durable
learnings get promoted into `memory/` first; git history archives the rest
(`handbook/principles/design-for-forgetting.md`).
