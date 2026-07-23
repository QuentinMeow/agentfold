# Split reconciler findings into blocking and advisory tiers

**Claimed-by:** unclaimed
**Filed:** 2026-07-22, by claude (design review; owner directed in chat — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Parent:** none
**Repository scope:** core

## Goal

The repo preaches eventual consistency but the pre-commit gate enforces immediate
consistency: `automation/reconcile/reconcile.py` exits 1 on *any* finding, so
time-based findings (a >30-day unanswered decision, an overdue memory entry, a
>14-day quiet task) block every commit repo-wide — and 13 memory entries all come
due 2027-01-18..22, a scheduled lockout. Split the `CHECKS` registry into `block`
(schema, links, budgets, structure, mode, index) and `advise` (stale-queue,
stale-task, memory-expiry, roadmap-fresh). Only `block` fails `--check`; advisory
findings print as warnings and surface through retry filing. While in there, make
the checks deterministic: staleness from git commit dates (subprocess `git log`,
still stdlib), not filesystem mtime, which resets on every fresh checkout so CI and
local clones currently disagree; and compare roadmap freshness against the git date
a task *reached* `tasks/4_done/`, not its filed date.

## Acceptance criteria

- [ ] A queue item with `Filed:` 40 days ago produces a warning, not a failed
      `--check` (shown with real output in `verification.md`)
- [ ] An overdue `Review-by:` in `memory/` does not block commits
- [ ] A missing required field still blocks, exactly as today
- [ ] `stale-task` returns identical results on a fresh clone and an old checkout
- [ ] Docs updated in the same change: `automation/AGENTS.md` table names the two
      tiers; `handbook/principles/eventual-consistency.md` unchanged (it already
      describes the advisory model — this task makes the code match it)

## Links

- Design review, finding 1.1: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
- Roadmap: `roadmap/desired-state.md` (harness-hardening line)
