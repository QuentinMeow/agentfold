# Eventual consistency

Design as if every agent does the right thing only half the time. That is fine — the
repo doesn't need every action to be correct; it needs every *inconsistency* to be
detected and queued for repair, so the whole system converges to correct.

## The reconciliation loop

```
agent forgets a step  →  invariant broken  →  reconciler detects it
       ↑                                              ↓
repair done, item deleted  ←  next session picks it up  ←  retry item auto-filed
```

`automation/reconcile/reconcile.py` checks every mechanical invariant (schemas, links,
required files, budgets, expiry dates). Findings become one file each in
`message-queue/needs-agent/retries/`, keyed deterministically so re-runs never
duplicate. The queue ritual in the root `AGENTS.md` makes the next agent pick them up.
When a finding clears, the reconciler garbage-collects its own item.

## Rules

- **Invariants, not procedures.** State what must be true ("every conversation folder
  contains handover.md"), never how it got that way. The reconciler checks end states,
  so it doesn't matter which agent, session, or human broke or fixes them.
- **Repairs are idempotent.** A retry item describes the broken invariant and the fix;
  running the fix twice is harmless.
- **Detection is cheap and constant.** The reconciler runs at pre-commit and in CI —
  drift is caught within one commit, not one month.
- **Graceful, not perfect.** A missed update is a queued repair, not a crisis. The only
  unforgivable failure is *silent* inconsistency: two sources of truth with no check
  between them (see `single-source-of-truth.md`).

## Why

This is how distributed systems survive unreliable nodes, and a multi-agent repo *is* a
distributed system with unreliable nodes. Demanding perfect discipline from agents
fails quietly; demanding convergence from the system fails loudly, once, and then heals.
