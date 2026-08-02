# Split reconciler findings into blocking and advisory tiers

**Claimed-by:** unclaimed
**Filed:** 2026-07-22, by claude (design review; owner directed in chat — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-severity-tiers-for-reconciler-findings.md`

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

**Remaining scope (2026-07-30):** the tier split itself shipped under task
2026-07-30-report-check-failures-honestly, which rewrote the same exit-code path while
fixing three crash-reporting defects. What is left here is the determinism half,
criterion 4 below.

**Claimability (2026-08-02):** this task was previously unclaimable — deleting its pickup
request broke `link-check` in a live queue item naming that path, and repairing the
reference broke `queue-resolution`. That is fixed. `check_links` now exempts every
`message-queue/needs-human/` and `message-queue/needs-agent/` citation from any file,
because a queue action is resolved by deleting it and so names history rather than a live
link. A full simulated claim of this task on 2026-08-02 — folder moved, `Claimed-by:` set,
pickup deleted, `Queue actions` cleared, `plan.md` and `worklog.md` added — reported
`reconcile: 0 blocking finding(s)`. The task is claimable now.

The request itself is still live and now `in-repair`, for a bookkeeping reason rather than
a real one: its predeclared `Resolution evidence` is `automation/reconcile/reconcile.py`,
and `resolution_evidence_problem` requires that file to change in the deletion commit. The
exemption that actually fixed it landed under a different task, and
`resolution_evidence_landed_earlier` deliberately admits only evidence committed by a task
the item itself names — the wider lineage rule was considered and rejected by measurement
under 2026-07-31-finish-the-replacement-ref-boundary. So a standalone deletion is refused.
Whoever claims this task changes `reconcile.py` for criterion 4 anyway, and should delete
that request in the same commit; that is the designed path and needs no new mechanism.

## Acceptance criteria

- [x] A queue item with `Filed:` 40 days ago produces a warning, not a failed
      `--check` (shown with real output in `verification.md`)
- [x] An overdue `Review-by:` in `memory/` does not block commits
- [x] A missing required field still blocks, exactly as today
- [ ] `stale-task` returns identical results on a fresh clone and an old checkout
- [x] Docs updated in the same change: `automation/AGENTS.md` table names the two
      tiers; `handbook/principles/eventual-consistency.md` unchanged (it already
      describes the advisory model — this task makes the code match it)

## Links

- Design review, finding 1.1: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
- Roadmap: `roadmap/desired-state.md` (harness-hardening line)
- Tier split shipped by task 2026-07-30-report-check-failures-honestly
