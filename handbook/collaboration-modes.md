# Collaboration modes

How much human is in the loop is a dial, not a philosophy. The active mode is declared
in one line in the root `AGENTS.md` (`**Collaboration mode:** …`); a task's `task.md`
may override it for that task via a `**Mode:**` field.

| | `autonomous` | `async` (default) | `pair` |
|---|---|---|---|
| Who drives | agent | agent | human |
| Agent decides alone | everything | everything **reversible** | trivial steps only |
| Agent files & continues | — | one-way doors → decision file + **default path** | — |
| Agent stops and waits | never | only `Blocking: yes` decisions | before every meaningful step |
| Human reviews | if they feel like it; nothing waits | queue items, at their own pace | live, step by step |
| Merge gate | adversarial-review majority (`skills/adversarial-review/`) | tests + reconciler; panel for one-way doors | the human |
| Costs | most tokens, zero human time | balanced | fewest tokens, most control |

## One-way doors (what `async` mode must not decide alone)

A decision is a **one-way door** when reversing it later costs far more than pausing
now. File these in `message-queue/needs-human/decisions/` (format:
`decision-guide.md`), then continue on the stated default path — or stop, if truly
blocking:

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

- **`autonomous`**: nothing may wait on a human. Questions become `clarifications/` or
  `reviews/` items with safe defaults; the agent self-reviews via the adversarial panel.
- **`async`**: the contract is "never block silently, never proceed silently". Every
  filed decision states its default path and when the default activates; the session
  reply re-surfaces open items every time (humans skim — repeat the ask).
- **`pair`**: the agent proposes, the human disposes. Optimize for short steps and
  cheap questions; skip handover ceremony the human already witnessed — but decisions
  made in chat still get written to files (chat leaves no trace).
