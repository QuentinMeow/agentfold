# Reconcile the merged stack's durable state

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-24, by codex, from the post-merge branch audit requested in chat
**Parent:** 2026-07-23-first-class-message-queue
**Repository scope:** records-only
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-reconcile-post-merge-stack-state.md`

## Goal

Bring the queue, task folders, verification records, and branch cleanup state into
agreement with the observed GitHub merges for PRs #7, #8, and #10. Preserve the
difference between “GitHub merged this PR” and an explicit human answer to a canonical
review item; do not invent approval language while closing obsolete publication state.

## Acceptance criteria

- [ ] Record the exact GitHub merge commits, bases, heads, and merge times for PRs #7,
      #8, and #10, including that #8 and #10 first landed on PR #7's branch after #7
      had already merged to `main`.
- [ ] After the consolidation branch reaches `main`, move each affected task only
      across lifecycle boundaries supported by committed merge and verification
      evidence.
- [ ] Resolve, replace, or retain every stack-related queue item according to its
      existing action identity and actual response/evidence; no merge is paraphrased
      into a human review answer.
- [ ] Refresh worklogs, verification records, and `roadmap/current-state.md` so they no
      longer claim an already completed publication step is pending.
- [ ] Delete local and remote publication branches only when their exact tips are
      reachable from the refreshed origin main branch; preserve rejected PR #5 as audit
      history unless a later owner decision changes that disposition.
- [ ] The reconciler and repository test runner pass with real output recorded.

## Links

- Parent task: `2026-07-23-first-class-message-queue`
- GitHub pull requests: `#7`, `#8`, and `#10`
- Git workflow: `handbook/git-workflow.md`
