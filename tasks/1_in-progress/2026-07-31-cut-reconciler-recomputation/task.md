# Cut the reconciler's repeated recomputation so the pre-commit gate returns faster

**Claimed-by:** claude
**Filed:** 2026-07-31, by claude, from task `2026-07-30-cache-reconciler-git-object-reads`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Object-read caching removed most redundant Git spawns, but the reconciler still recomputes
the same pure answers over and over: every admitted Git edge re-derives Markdown semantics
for records it already parsed, every candidate artifact read scans the whole index to answer
a single-path question, and every consumer of one edge walk re-asks Git for the same commit
parents. Wall time is therefore still O(commits x repository size), which shows up directly as
the seconds a human waits at `automation/hooks/pre-commit`. This task removes the
recomputation without changing a single finding.

## Acceptance criteria

- [ ] THE SYSTEM SHALL answer a repeated pure text question (Markdown semantic blanking,
      task-record action-prose recognition) from a content-keyed cache instead of recomputing it.
- [ ] WHEN a caller needs one exact index entry, THE SYSTEM SHALL look that entry up directly
      rather than filtering the whole index by prefix.
- [ ] WHEN several consumers walk the same governed edge set, THE SYSTEM SHALL ask Git for a
      commit's parents at most once per revision, still through `git rev-list`.
- [ ] WHEN an immutable handover incarnation is read, THE SYSTEM SHALL read its bytes through
      the existing `cat-file --batch` reader instead of spawning `git show`.
- [ ] Reconciler behaviour is unchanged: the finding list is byte-identical before and after on
      `--check`, on a mid-size `--range`, and on `--range root:<head>`, evidenced by a
      differential harness that runs both versions against the same working tree.
- [ ] Wall time is recorded before and after for each scope, with the observed spread.

## Links

- Task `2026-07-29-reduce-reconciler-git-spawns` — the object-read caching this builds on
- `docs/designs/fast-local-test-feedback.md`
