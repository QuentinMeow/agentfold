# Make every pending human or durable agent action a queue-owned message

**Status:** waiting
**Blocking:** yes — this coordination-contract change waits for owner direction
**Filed:** 2026-07-23, by codex, from the owner's architecture correction in chat

## What you need to know

Today a PR, chat reply, task, or handover can ask for action without creating a
`message-queue/` item. That is how PR #4 gained five review questions after its generic
queue review was already resolved. The current queue routes by who acts next, but its
filenames do not reveal when that action becomes blocking.

## Options

### Option A — Queue owns every pending action

Every human action and every durable cross-session agent action gets one queue file.
Other channels only summarize and link it. Filenames begin with `blocking-`,
`future-blocking-`, or `non-blocking-`.
*Example consequence:* a PR can show “review the PII guarantee,” but the text links to a
queue file that explains the alternatives, a leak scenario, the unattended outcome,
and the full design section.

### Option B — Keep independent action channels

PRs, chat, tasks, and queue files may each introduce their own asks.
*Example consequence:* a reviewer answers a PR checklist, but the next agent never sees
the response because no durable queue item owned it.

## Recommendation

Option A, because it preserves actor-first folders while making delivery class visible
and every external ask traceable to one durable projection.

**Your answer:** Yes — queue everything requiring human review, action, or decision;
make the queue first-class for human↔agent and agent↔agent interaction, and prefix every
message by whether it blocks now, blocks later, or is non-blocking.
