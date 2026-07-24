# Collaboration modes

How much human is in the loop is a dial, not a philosophy. The active mode is declared
in one line in the root `AGENTS.md` (`**Collaboration mode:** …`); a task's `task.md`
may override it for that task via a `**Mode:**` field.

| | `autonomous` | `async` (default) | `pair` |
|---|---|---|---|
| Who drives | agent | agent | human |
| Agent decides alone | everything | everything **reversible** | trivial steps only |
| Agent files & continues | optional `non-blocking-*` review | one-way door → `future-blocking-*` decision + path until boundary | — |
| Agent stops and waits | only a separately mandated trust gate | a `blocking-*` item, or unresolved item at its future boundary | before every meaningful step, after filing its `blocking-*` item |
| Human reviews | queue projections, usually non-blocking | queue items, ordered by timing prefix | live projections of queued actions |
| Merge gate | adversarial-review majority (`skills/adversarial-review/`) | tests + reconciler; panel for one-way doors | the human |
| Costs | most tokens, zero human time | balanced | fewest tokens, most control |

## One-way doors (what `async` mode must not decide alone)

A decision is a **one-way door** when reversing it later costs far more than pausing
now. File it in `message-queue/needs-human/decisions/` (format:
`decision-guide.md`). Use `future-blocking-*` while a safe path exists until a named
boundary; use `blocking-*` only when a named task, operation, or transition is stopped:

- Public API or schema changes others already depend on
- Adding a dependency, external service, or new tool to the stack
- Deleting or migrating data; anything without an undo
- Security boundaries: auth, secrets handling, permissions
- Spending money or calling paid APIs beyond an agreed budget
- Publishing anything outside the repo (releases, posts, emails)
- Changing a file in `handbook/principles/`

Everything else is a **two-way door**: decide, record the reasoning in the task's
`design.md` or an ADR, and keep moving. Wrong two-way calls are cheap — that's what
git revert and the retry queue are for.

## Mode-specific notes

- **`autonomous`**: ordinary work does not wait on a human. Optional questions become
  `non-blocking-*` clarifications/reviews; the agent self-reviews via the adversarial
  panel. A separately mandated trust-boundary review still uses its honest timing class.
- **`async`**: the contract is "never block silently, never proceed silently". Every
  queued action names its current or future boundary/unattended outcome; the session
  reply re-surfaces open human items every time (humans skim — repeat the ask).
  Naming an arbitrary event, transition, or operation supplies agent acknowledgement,
  not hard assurance, unless a controlled adapter observes and enforces that boundary.
- **`pair`**: the agent proposes, the human disposes. Optimize for short steps and
  cheap questions. Create the queue item before asking live; chat is a projection and
  the response is folded through the file before work resumes. Handover prose may stay
  brief, but no action or decision exists only in chat.
