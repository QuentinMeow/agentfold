# Stop a human answer from holding any Git edge

**Claimed-by:** unclaimed
**Filed:** 2026-08-01, by claude, from a judged design over the queue's boundary grammar
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-human-answers-from-gating-git-edges.md`

## Goal

The repository owner answers durable questions late, never before a merge. The queue's
boundary grammar lets a `needs-human/` item bind `transition:merge|review|complete`, so an
unanswered question stops a revertible Git edge. Today that is a live deadlock: two reviews
whose reviewed ranges are already ancestors of `main` still fail
`reconcile --check --at-transition merge`, and the decision item filed to dispose of them
binds `transition:complete` on the same three tasks it asks about.

Make a human merge gate unspellable. A `needs-human/` item may withhold only the start of a
task still in `0_backlog` or one act with no undo (`operation:<name>`); everything else is
`non-blocking-` and merges with the question open. Give every human item an `Answer by:`
date so a late answer is visible rather than silent, and make `4_done` an agent-work test
so a task never waits on a person to reach its own `git mv`.

## Acceptance criteria

- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 blocking findings.
- [ ] `python3 automation/run_tests.py` reports 11/11 files passed.
- [ ] No live `needs-human/` item binds `transition:merge`, `transition:review`, or
      `transition:complete`, and the grammar refuses a new one.
- [ ] `--check --at-transition merge` reports no `needs-human/` queue-boundary finding.
- [ ] Every live `needs-human/` item carries a parseable `**Answer by:**` date, and a
      lapsed date is advisory, never blocking.
- [ ] A task reaches `4_done` while a live, unanswered `needs-human/` item stays listed in
      its `Queue actions`.
- [ ] Every committed human response is byte-identical to its state at `0e63bbe`.
- [ ] `transition:start` on a started task and an agent-owned merge boundary both still
      refuse, proven by a failing run before the change.

## Links

- `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`
- `memory/decisions/2026-07-23-live-queue-obligations-only-weaken-with-evidence.md`
- `roadmap/desired-state.md` — nothing blocks or waits silently
