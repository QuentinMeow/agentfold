# Judge a handover by the entry grammar its own creation snapshot declared

**Claimed-by:** claude (worktree agent-a3dd7926a22a81287)
**Filed:** 2026-08-01, by claude, from a reproduced merge failure on PR #44 and a latent one on `main`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`automation/AGENTS.md` says entry schema versions preserve creation-time grammar and that a
newly rejecting grammar needs a new version instead of retroactive validation.
`handover_action_entry_version_for` does the opposite: it governs an immutable handover by the
highest entry version it can reach, including a version withdrawn before the record existed and
a version activated in parallel history afterwards. The only repair the resulting finding names
is a byte change, which `history/AGENTS.md` forbids, so any branch cut before a version bump
becomes permanently unmergeable.

Two failures are live. PR #44 merges cleanly and passes `--check` and the suite, but its merge
probe reports nine blocking findings on one handover, all demanding v3 suffix labels invented
after the record was written. The same defect already sits on `main`: the
`2026-08-01-1522PDT-admit-a-candidates-whole-task-scope` handover fails identically in any
future range containing its creation commit.

Judge the record's suffix spelling by the marker in its own creation snapshot, and keep the
admission-edge ratchet for the rejecting clauses so branching early still cannot evade them.

## Acceptance criteria

- [x] `python3 automation/reconcile/reconcile.py --check` reports 0 blocking findings.
- [x] `python3 automation/run_tests.py` reports 11/11 files passed.
- [x] The PR #44 merge probe (`--check --at-transition merge --branch
      task/2026-07-31-let-a-human-answer-in-one-edit` over a merge of `6c723ef` onto main with
      main as first parent) reports 0 blocking findings.
- [x] A range containing `b98621f` no longer reports the nine latent findings on the
      `2026-08-01-1522PDT-admit-a-candidates-whole-task-scope` handover.
- [x] A version withdrawn before a record was written does not govern that record.
- [x] A version activated only in parallel history does not change a record's required suffix.
- [x] A branch cut before a rejecting grammar activated still cannot evade that rejection,
      proven by a test.
- [x] Every handover reachable from `main` is accepted under the marker its own creation
      snapshot declared.
- [x] No committed handover bytes change.

## Links

- `automation/AGENTS.md` — entry schema versions preserve creation-time grammar
- `history/AGENTS.md` — committed bytes are immutable; correct in a new conversation path
- `memory/lessons/automation/deterministic-finding-keys.md`
