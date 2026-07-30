# Spawn fewer Git processes in the reconciler and its test fixtures

**Claimed-by:** unclaimed
**Filed:** 2026-07-29, by claude, from `docs/designs/fast-local-test-feedback.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-2026-07-29-reduce-reconciler-git-spawns.md`

## Goal

The reconciler read one blob per `git show` and re-derived immutable object facts per
invocation, which dominated a suite that spends 92-93% of its wall time inside Git
subprocesses. A reusable `git cat-file --batch` reader and caching keyed on object IDs remove
thousands of spawns. This also speeds up CI, where local cores cannot help.

## Acceptance criteria

- [ ] THE SYSTEM SHALL read blob bytes through one reusable batch reader rather than one
      process per artifact.
- [ ] WHEN a fact is keyed by a full object ID, THE SYSTEM MAY cache it per repository, and
      SHALL NOT cache failures.
- [ ] Reconciler behaviour is byte-identical, evidenced by an equivalence harness.
- [ ] The spawn count and wall time are recorded before and after.

## Links

- `docs/designs/fast-local-test-feedback.md`
