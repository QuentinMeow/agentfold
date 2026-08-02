# Decide what happens when a queue-format migration has to be undone

**Claimed-by:** claude
**Filed:** 2026-08-01, by claude, from the human-action format redesign — `message-queue/AGENTS.md`
**Parent:** 2026-08-01-countersign-the-live-human-item-migration
**Repository scope:** core
**Queue actions:** none

## Goal

Any mechanism that lets one commit rewrite live queue items — the kind
`2026-08-01-countersign-the-live-human-item-migration` will need — is one-way, and nothing
currently says so.

The reason is symmetry. Such a mechanism admits exactly one edge: the one that turns the
format marker on. Reverting that commit is a second rewrite of the same live items, on an
edge where the marker is already active in the parent, so `queue_mutation_problem` refuses
it as "action identity changed while the queue item remained live". A migration can be
performed and cannot be undone by `git revert`. The ordinary escape from a bad commit does
not exist here.

This is not a defect to fix by loosening the identity rule; the rule is what protects a
live ask. It is a property to state, and to design the migration around: either the
migration mechanism admits its own reversal edge under the same countersigned evidence, or
the recovery path is "supersede the items rather than restore them" and is written down
before anyone needs it at three in the morning.

This task is only worth doing if that migration proceeds. If the eight legacy items age
out and no live item is ever rewritten, close it as not-needed with that reason recorded.

## Acceptance criteria

- [ ] `verification.md` reproduces the refusal: a migration commit, a `git revert` of it,
      and the real finding the reconciler emits on the revert
- [ ] `design.md` chooses between admitting a countersigned reversal edge and defining a
      supersede-based recovery path, and says why the other was rejected
- [ ] The chosen recovery path is exercised end to end in a fixture, not argued in prose
- [ ] Whatever is decided is stated once in `message-queue/AGENTS.md` or in the migration
      task's own design, linked rather than restated
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 findings and
      `python3 automation/run_tests.py` passes every file, with both real outputs in
      `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt if any core path changes

## Links

- The migration this constrains: task `2026-08-01-countersign-the-live-human-item-migration`
- The identity rule that makes the revert illegal: `automation/reconcile/reconcile.py`
- The queue contract and its lifecycle: `message-queue/AGENTS.md`
- The redesign that found it: task `2026-07-31-redesign-human-action-files`
