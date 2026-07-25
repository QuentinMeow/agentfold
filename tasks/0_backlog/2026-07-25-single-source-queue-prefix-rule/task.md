# Single-source the queue delivery-prefix rule out of the five queue templates

**Claimed-by:** unclaimed
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-single-source-queue-prefix-rule.md`

## Goal

All five queue templates open with a byte-identical HTML comment that restates a rule
`message-queue/AGENTS.md` owns. The comment occupies **lines 1 through 7** of each file
(`<!--` on line 1, `-->` on line 7), and lines 3, 4, and 5 are the three delivery-prefix
definitions. The five files are `templates/queue/clarification.md`,
`templates/queue/decision.md`, `templates/queue/request.md`, `templates/queue/retry.md`,
and `templates/queue/review.md`. Their lines 1-7 hash identically, and each of the five
contains **zero** occurrences of the string `message-queue` — so nothing in any template
points a reader at the contract that owns the rule, and `link-check` has no reference to
validate.

That duplication is already live drift. Commit aca7014, "harness: harden queue snapshot
boundaries", tightened the future-blocking boundary to require a UTC date. It updated the
owning contract — `message-queue/AGENTS.md` line 17 now reads "work continues until an
explicit UTC date, event, or" — and it updated the `Blocks at` field line inside every one
of the five templates, at `templates/queue/clarification.md` line 29,
`templates/queue/decision.md` line 29, `templates/queue/request.md` line 33,
`templates/queue/retry.md` line 28, and `templates/queue/review.md` line 57, each of which
now reads `<UTC YYYY-MM-DD | event:<name> | transition:<name>>`. In all five files line 4
was left behind and still reads "- future-blocking-: work may continue, but must stop at a
named date, event, or transition." Two lines of the same file disagree about the same rule,
in five files at once, right now.

The correct repair is **deletion, not declaration**. Replacing the restated comment with a
link to the routing section of the owning contract single-sources the rule, removes all
four sibling copies along with the original, and brings the reference inside `link-check`'s
reach — where the heading-anchor validation added by the Stage 0 mining task then keeps the
heading honest. Recording the coupling as a declared edge would instead preserve the
duplication and add a permanent maintenance duty on top of it.

The owning text is already complete. `message-queue/AGENTS.md` lines 16 through 20 give
the three prefix meanings under `## Routing: three independent axes`, and lines 22 through
24 give the canonical-filename and no-duplicate-`Blocking`-field rules. The kebab-slug
filename grammar the comment also restates is owned by `handbook/naming-conventions.md`
in its "Queue items" bullet. Both contracts are at or near their line budgets, so the
repair is a deletion in five files plus one short reference line in each, not new prose in
either contract.

This task changes template files only. It does not change any reconciler check, and the
set of findings `python3 automation/reconcile/reconcile.py --check` reports on this
repository is identical before and after.

## Acceptance criteria

- [ ] The delivery-prefix definitions appear in exactly one tracked file. Verified by
      `grep -rn "future-blocking-: " templates/` returning no matches, and by
      `grep -rln "future-blocking" message-queue/AGENTS.md` returning that one path
- [ ] Each of the five templates names `message-queue/AGENTS.md` at least once, so the
      reference is inside `link-check`'s reach rather than invisible to it
- [ ] No rule is lost, only relocated: the three prefix meanings, the "filename is
      canonical" rule, the "no separate `**Blocking:**` field" rule, and the kebab-slug
      filename grammar all remain readable from `message-queue/AGENTS.md` and
      `handbook/naming-conventions.md`, and `verification.md` records the before-and-after
      text of each rule so a reader can confirm none was dropped
- [ ] `message-queue/AGENTS.md` stays within its 60-line `agents-budget` ceiling and
      `handbook/naming-conventions.md` gains no rule it did not already state
- [ ] `python3 automation/reconcile/reconcile.py --check` exits 0, and it reports the same
      findings on this repository after the change as before it, with both runs recorded in
      `verification.md`
- [ ] `python3 automation/run_tests.py` passes with real output recorded in
      `verification.md`, and any test that asserts on the removed comment text is updated in
      the same change
- [ ] `design.md` carries a complete `## Core fit` receipt, because `templates/` is a core
      path

## Links

- Measured finding, including the fivefold restatement and the aca7014 drift:
  `docs/designs/markdown-edge-graph.md`
- Owning contract for the prefix rule: `message-queue/AGENTS.md`
- Owning contract for the queue-item filename grammar: `handbook/naming-conventions.md`
- Guardrail this repairs — single source of truth:
  `handbook/principles/single-source-of-truth.md`
