# history/ — conversation record

**Queue projection schema:** v1
**Queue action-entry schema:** v3
**Queue liveness schema:** v1

One folder per conversation/session that did work:
`conversations/YYYY-MM-DD-HHMM<TZ>-<kebab-slug>/` — session start as **local time
plus timezone abbreviation** (e.g. `2026-07-22-0014PDT-fix-cli-crash`; use `UTC` if
your zone has no letter abbreviation). Every folder **must** contain a `handover.md`
— the reconciler enforces this.

## handover.md (schema: `templates/handover.md`)

The handover is a one-screen, plain-language orientation for a human who was away. Copy
`templates/handover.md`; put depth in task worklogs, designs, and verification, then link
it. Follow `skills/session-handover/` and `skills/explain-to-human/`.

Under the three repository schema markers above, every new handover declares
`**Queue projection:** v1` and exactly projects the live unanswered
`message-queue/needs-human/` items in filename-timing order. It never originates an ask.
Each entry is one top-level bullet beginning with the exact Action as a link to one
actor-matching queue path, followed by the exact suffix labels `Why this matters:` and
`If you do nothing:`, copying those queue fields. `Next steps` is `None.` or links assigned
work to live `needs-agent/` items.

A concrete `Your answer` or `Your review` resolves an item for projection; `folding`
therefore stays out, and `awaiting-artifact` also stays out because no artifact is ready
for the human to judge. The reconciler evaluates queue and handover together at creation,
so later queue changes never rewrite a record. Committed handovers are immutable: never
edit or rename one; correct it in a new conversation folder. Older records keep the syntax
and liveness contract active at their creation revision.

## Other files in a conversation folder (optional)

- `transcript.md` — pointer to or export of the raw session log, when available
- `artifacts/` — files produced during the session worth keeping but belonging to no
  service (analysis notes, comparison tables)

## Retention

Conversation folders older than ~180 days are pruned by the memory gardener — durable
learnings get promoted into `memory/` first; git history archives the rest
(`handbook/principles/design-for-forgetting.md`).
