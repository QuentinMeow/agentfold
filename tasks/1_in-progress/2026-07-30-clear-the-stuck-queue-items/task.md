# Clear the four stuck queue items against real repository state

**Claimed-by:** claude
**Filed:** 2026-07-30, by claude, from chat
**Parent:** none
**Repository scope:** records-only
**Queue actions:** none

## Goal

Four live queue items have been stuck on `main` for days, and the widened
`resolution_evidence_problem` shipped by task 2026-07-30-admit-evidence-that-landed-earlier
only unsticks one of them. This task applies that rule to the real state and diagnoses the
other three instead of forcing them, so the repository's records match what actually
happened.

The four are not one shape.

**One agent request whose repair already merged.** The item
message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
sits at `in-repair`, declares `automation/reconcile/reconcile.py` as its resolution
evidence, and its repair merged in `6d4e337` carrying the trailer
`task: 2026-07-25-fix-handover-projection-code-span-copy`. That is exactly the shape the
widened rule admits. Task 2026-07-25-fix-handover-projection-code-span-copy has been pinned
at `1_in-progress` by that link ever since, even though its own work merged through pull
request 14.

**Three human merge reviews the boundary already passed.** These three items name
`Blocks at: transition:merge task:<id>` boundaries whose bound Git ranges are already
ancestors of `main`:

- `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md`
- `message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md`
- `message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md`

Each is `waiting` with `Review outcome: pending` and a blank response slot, and each names a
task now sitting in `tasks/3_in-review/` whose code is on `main`. Git evidence cannot
un-cross a boundary, so no agent action can turn these into resolved items, and the
disposition they need is not a checker question. This task diagnoses their exact mechanical
state, records it, and leaves the unanswered items intact.

## Acceptance criteria

- [ ] The merged code-span repair request is deleted in a commit that carries its reciprocal
      task backlink removal, with `python3 automation/reconcile/reconcile.py --check` at
      0 findings and no evidence file touched in that commit
- [ ] Task 2026-07-25-fix-handover-projection-code-span-copy reaches `Queue actions: none`,
      and moves to `4_done` only if its recorded work is genuinely complete — its plan, its
      acceptance criteria, and its `verification.md` are checked against the merged commit
      before the move, one lifecycle edge per commit
- [ ] The three stranded merge reviews keep their unanswered human response slots and their
      immutable action text; no response, retraction, or deletion is invented for them
- [ ] The mechanical claim that no agent action can resolve those three is demonstrated with
      real command output rather than asserted, and recorded in `verification.md`
- [ ] Exactly one canonical `message-queue/needs-human/decisions/` item carries the
      disposition choice for all three, is reciprocally linked from all three task records,
      and names the tasks by id only
- [ ] Each of the three task records gains a worklog entry stating the measured state, so a
      later reader does not have to re-derive it
- [ ] `python3 automation/reconcile/reconcile.py --check` exits 0 and
      `python3 automation/run_tests.py` passes, with both outputs recorded in
      `verification.md`

## Links

- The rule that admits the first item: `automation/reconcile/reconcile.py`
- The task that shipped it: 2026-07-30-admit-evidence-that-landed-earlier
- Queue lifecycle and resolution rules: `message-queue/AGENTS.md`
- What a human action needs before it may be resolved: `handbook/human-action-guide.md`
- Live obligations weaken only with evidence:
  `memory/decisions/2026-07-23-live-queue-obligations-only-weaken-with-evidence.md`
