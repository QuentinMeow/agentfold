# Build test fixture history by writing Git objects instead of spawning add and commit

**Claimed-by:** unclaimed
**Filed:** 2026-07-30, by claude, from `docs/designs/fast-local-test-feedback.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-write-fixture-git-objects-in-process.md`

## Goal

The suite is bound by process creation rather than computation: system time exceeds user
time, and a bare `git --version` costs 5.59ms on this machine, so roughly 74s of a 198s
run is process startup that no amount of Git cleverness removes.

Fixture setup is the largest remaining source of those spawns. The long-pole test file
makes about 450 `git commit` and 540 `git add` calls, purely to construct history the
test then reads back. Writing the loose objects directly from Python costs 2.35ms against
31.8ms for the add-and-commit pair, a measured 13.5x, and removes two spawns each time.

The repository already banked the neighbouring win: the `.git` skeleton is created once
with an empty template and copied per test, guarded by a test that byte-compares the copy
against a real `git init`. This task extends the same pattern, and inherits the same
guard requirement, to the history built inside those repositories.

## Acceptance criteria

- [ ] THE SYSTEM SHALL build fixture commits without spawning `git add` or `git commit`,
      producing objects real Git reads back identically.
- [ ] A conformance test SHALL byte-compare the written objects against the objects real
      `git add` and `git commit` produce for the same content, so a divergence fails
      rather than silently changing what the fixtures mean.
- [ ] Fixture object identifiers SHALL be deterministic, which requires a pinned author
      and committer identity and a pinned timestamp.
- [ ] Tests that depend on index semantics or on a non-default object format SHALL keep
      using real Git, and the boundary SHALL be stated where a reader will find it.
- [ ] Spawn counts before and after SHALL be recorded, alongside wall time measured with
      both variants interleaved inside one session.

## Links

- `docs/designs/fast-local-test-feedback.md`
