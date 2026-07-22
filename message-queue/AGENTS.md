# message-queue/ — the async message bus

All human↔agent and agent↔agent coordination flows through here: one file per message,
routed by **who acts next**. Nothing in this folder blocks by default — every decision
states a default path, every review is safe to ignore. Principle:
`handbook/principles/files-as-messages.md`.

## Queues

| Queue | Who acts | Contents | Emptied when |
|-------|----------|----------|--------------|
| `needs-human/decisions/` | human | choices only the human may make; options + example consequences + default path | answer folded into docs, ADR recorded, file deleted |
| `needs-human/clarifications/` | human | questions that will shape future work; agent proceeding on stated assumption | answer folded, file deleted |
| `needs-human/reviews/` | human | optional human-eyes items; doing nothing must be safe | acknowledged, or swept when stale (>30 days) |
| `needs-agent/requests/` | agent | human's free-form drop box — the only queue with no required format | acted on or converted to a task, deleted same commit |
| `needs-agent/retries/` | agent | repair work filed by the reconciler or a failed job | invariant fixed (or rejected in-file), deleted |

## Universal rules

- Filenames: `<kebab-slug>.md`, no dates or numbers (slugs don't churn; filing date is
  the `**Filed:**` field). Schemas: copy from `templates/queue/` — never write from memory.
- Every item is self-contained: the reader acts from the file alone, assuming only the
  root `AGENTS.md` as context.
- **Items are projections, not sources.** Like a retryable API call, an item carries
  only the summary the reader needs to act; everything durable (background, artifacts,
  reasoning) lives in the linked task folder, `memory/`, or code — so a lost or stale
  item is simply regenerated from its sources. The one thing an item ever uniquely
  holds is a not-yet-folded human answer, which is why folding precedes deletion.
- **Claim before resolving**: commit a one-line `**Status:**` edit (`folding`,
  `in-repair`) before acting on an item, so parallel sessions don't double-process.
- Resolved items are **deleted in the resolving commit** — git history is the archive;
  the queues hold only live items.
- An answer the human gives in chat is written into the queue file in the same turn.
- Escalation without moving: a clarification that becomes urgent gets its `**Blocking:**`
  field updated — files never move between queues (links would break).
- Session ritual (when to read which queue): root `AGENTS.md`, "Message-queue ritual".
