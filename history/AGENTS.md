# history/ — conversation record

**Queue projection schema:** v1

One folder per conversation/session that did work:
`conversations/YYYY-MM-DD-HHMM<TZ>-<kebab-slug>/` — session start as **local time
plus timezone abbreviation** (e.g. `2026-07-22-0014PDT-fix-cli-crash`; use `UTC` if
your zone has no letter abbreviation). Every folder **must** contain a `handover.md`
— the reconciler files a repair item for any that doesn't.

## handover.md (schema: `templates/handover.md`)

The handover is for a human who was away: what happened, how it works now, what needs
their attention — one screen maximum, plain language, no invented shorthand. Depth
never goes in the handover; it goes in the task folder (worklog, design, verification)
and the handover links there. End-of-session ritual: root `AGENTS.md`;
`skills/session-handover/` walks through it.

The repository-local schema field above activates checking without imposing an
AgentFold date or retained legacy folder on forks. Existing unmarked records remain
records; every newly added handover must declare `**Queue projection:** v1` and exactly
project all live `message-queue/needs-human/` actions in filename-timing order. It never
originates an ask. Resolved targets may later disappear because git history archives
past delivery. Range-based checks evaluate the handover and queue together at the
handover's creation commit, so later queue additions or resolutions never rewrite it.
Once committed, v1 handover bytes are immutable; record corrections in a new handover.
`Next steps` is `None.` or links assigned work to live `needs-agent/` items; it never
originates a cross-session action.

## Other files in a conversation folder (optional)

- `transcript.md` — pointer to or export of the raw session log, when available
- `artifacts/` — files produced during the session worth keeping but belonging to no
  service (analysis notes, comparison tables)

## Retention

Conversation folders older than ~180 days are pruned by the memory gardener — durable
learnings get promoted into `memory/` first; git history archives the rest
(`handbook/principles/design-for-forgetting.md`).
