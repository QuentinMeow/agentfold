# Reconcile merged stack records and obsolete branch state

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-25, by codex, from the owner's branch recovery and cleanup request in chat
**Parent:** none
**Repository scope:** records-only
**Queue actions:** none

## Goal

Bring live task, queue, roadmap, worktree, and branch state into agreement with the
observed GitHub merges for PRs #7, #8, #10, #11, and #12. Recover only the canonical
coordination records excluded from the reviewed implementation branches, preserve the
difference between provider merge evidence and an explicit human review answer, and
remove obsolete branch snapshots after their useful content is preserved.

## Acceptance criteria

- [x] Record the exact merged PR bases, heads, merge commits, and ordering, including
      that PRs #8 and #10 landed on PR #7's branch after PR #7 had already reached main.
- [x] Publish the six layered-workspace backlog tasks, six pickup requests, and six
      dependency actions from immutable source `9d7bb1d`, then resolve the publication
      request and its parent-task backlink.
- [x] Bind artifact-pending human review records to their admitted immutable ranges
      without inferring approval from a GitHub merge.
- [x] Refresh affected task worklogs and `roadmap/current-state.md` so they no longer
      describe completed publication or merge operations as pending.
- [x] Remove audited obsolete worktrees and local/remote branches while retaining
      the remote PR #5 branch as rejected-scope audit
      history.
- [x] The reconciler and repository test runner pass with real output recorded, and
      the primary checkout finishes clean on current `main`.

## Links

- Git workflow: `handbook/git-workflow.md`
- Layered workspace parent task: `2026-07-24-layered-development-workspace`
