# history/ — conversation record
**Queue projection schema:** v1
**Queue action-entry schema:** v3
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

The schema field above activates checking without imposing AgentFold history on forks.
Existing unmarked records remain records; every new handover declares `**Queue projection:** v1`, projects exactly the waiting human actions in filename-timing order,
and never originates an ask. Git history archives resolved targets. Range-based checks evaluate the handover and queue together at its creation commit, so later queue additions
or resolutions never rewrite it. Once committed, v1 handover bytes are immutable; record corrections in a new handover.
`Next steps` is `None.` or links assigned work to live `needs-agent/` items; it never
originates a cross-session action.

The action-entry marker independently versions strict projection syntax. Versions 1
and 2 freeze the contracts that existing records passed when created. Version 3
projects only human items whose status is `waiting`; `awaiting-artifact` is not ready
and `folding` is already agent-owned. Each human entry is one top-level bullet in this
exact form:

`- [<rendered queue Action>](<one actor-matching live queue path>) <exact Why this matters paragraph> <exact If you do not respond paragraph>`

The bullet's one link points to one actor-matching waiting item. Both compact
paragraphs are copied with whitespace normalization only; the second already begins
“If you do not respond,”. Action and label may use different inline code, emphasis, or
escapes only when they render identically after whitespace reflow; every other rendered
code point is exact. The rendered label keeps the Action's terminal punctuation and
optional closing quote or bracket; projection never inserts punctuation. Project the
complete actionable queue in timing-then-path order. Agent entries contain only the
action link and may project just work assigned here. The creation/admission edge selects the highest active version;
parallel history joined with an activation uses that version. A rejecting grammar
expansion requires a new schema version instead of retroactively changing immutable
records. Both schema markers are sticky while `history/` remains. Queue-projection
adoption freezes every existing handover path, including an unmarked legacy record:
delete it when retention permits, but never edit or rename it; corrections use a new
conversation path.

The handover keeps its repository-relative destination. Final chat preserves its
rendered Action label and paragraphs but resolves the same queue file for the chat surface.
## Other files in a conversation folder (optional)

- `transcript.md` — pointer to or export of the raw session log, when available
- `artifacts/` — files produced during the session worth keeping but belonging to no
  service (analysis notes, comparison tables)

## Retention

Conversation folders older than ~180 days are pruned by the memory gardener; promote
durable learning first (`handbook/principles/design-for-forgetting.md`).
