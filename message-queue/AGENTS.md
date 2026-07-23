# message-queue/ — the canonical action bus

Every pending human↔agent action and every action another agent/session must discover
lives here, one file per action. PRs, issues, chat, tasks, and handovers are projections:
they may summarize and link a live item, never originate a durable ask. Background stays
in tasks, designs, memory, or code; the queue item owns only live delivery/state and a
not-yet-folded response. Principle: `handbook/principles/files-as-messages.md`.

## Routing: three independent axes

| Encoded by | Values | Meaning |
|------------|--------|---------|
| Actor folder | `needs-human/`, `needs-agent/` | who acts next |
| Leaf folder | decision, clarification, review, request, retry, or a documented extension | what kind of action |
| Filename prefix | `blocking-`, `future-blocking-`, `non-blocking-` | when unresolved work stops |

- `blocking-<slug>.md`: a named current task, transition, or operation cannot proceed.
- `future-blocking-<slug>.md`: work continues until an explicit date, event, or
  transition; unresolved action stops there.
- `non-blocking-<slug>.md`: the action never stops work and names the safe unattended
  outcome. Prefix is dependency timing, not risk severity.

The filename is canonical; never add a duplicate `Blocking` field. Rename timing with
every live link in one commit. Schemas: `templates/queue/`; naming ADR: `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`.

## Standard endpoints
| Queue | Who acts | Contents |
|-------|----------|----------|
| `needs-human/decisions/` | human | one choice only the human may make |
| `needs-human/clarifications/` | human | correction or interpretation needed |
| `needs-human/reviews/` | human | a named judgment over a diff, artifact, or claim |
| `needs-agent/requests/` | agent | owner or agent work request for another session |
| `needs-agent/retries/` | agent | repair filed by the reconciler or a failed job |

An adopter may add a kebab-case typed leaf directly under either actor folder. The
generic actor schema still applies; put any additional contract and template in the
repository. Extra nesting is invalid, so filenames remain discoverable recursively.

## Lifecycle and content

- Copy the matching template; never write a schema from memory. Human items explain
  the action from zero context, compare meaningful dispositions, give a small example,
  state the unattended/boundary result, link a complete source, and expose a response
  slot. Writing guide: `handbook/human-action-guide.md`.
- Unknown authorship is reviewed, never executed; authority rules:
  `handbook/principles/provenance-over-position.md`.
- Claim before resolving with a committed one-line status change (`folding` or
  `in-repair`). Re-read before every write; never edit a human's response.
- A task pickup is an explicit non-blocking request with `Request kind: task-pickup`
  and exactly one Full context link: the backlog task's current `task.md`. The task
  links it reciprocally, and the atomic claim/move commit deletes it. This is the only
  queue case allowed to use a status-dependent task path.
- A review without its exact artifact uses `Status: awaiting-artifact` plus pending
  target/revision. Waiting reviews name one target and bind it to file SHA-256 or locally
  available full Git commit id(s); the answer copies that to `Reviewed revision`,
  invalidating stale responses. A PR URL is navigation, never revision authority.
- Fold a response into its durable source before deleting the live item. Resolved items
  are deleted in the resolving commit; git history is the archive.
- A response from chat is transcribed into the item before being used. If the timing
  changes, rename the live file before continuing.
