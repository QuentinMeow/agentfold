# Worklog — Let a queue item resolve when its resolution evidence landed in an earlier commit

## 2026-07-26 — claim-merged-evidence (codex)

- Claimed the task, moved it from backlog to `1_in-progress`, and removed its completed task-pickup request atomically.
- Recorded the converged implementation constraints in `plan.md`: the repair applies only to ordinary `needs-agent` requests; compares every resolution-evidence path against the unique current-incarnation creation snapshot; requires final readable surviving bytes to differ; retains the independent status-only claim; and preserves human, retry, pickup, and custom behavior.
- The task wording’s earlier `at or after claim edge` criterion is contradictory to the creation-snapshot baseline. The reviewed task branch will amend it openly to the intended post-creation criterion; this direct-main coordination commit intentionally does not alter substantive acceptance criteria.

## 2026-08-02 — close as superseded (claude)

- The `codex` claim of 2026-07-26 was never worked again: no branch, no pull request, no `verification.md`, and `plan.md` at 0 of 8. Six days later the claim is abandoned, so it is cleared rather than left implying an owner.
- The defect was repaired by a different task. `2026-07-30-admit-evidence-that-landed-earlier` merged as pull request 38 (`c824e0e`) with a narrower rule, chosen because widening the window to "the evidence changed at some point" measured 14 of 14 live ordinary requests as deletable with no work at all.
- This task's own approach did not survive that comparison. `tasks/4_done/2026-07-30-cache-reconciler-git-object-reads/design.md` records its resolution-evidence rule as "found harmful and is being discarded" while taking only its caching, and `2026-07-31-finish-the-replacement-ref-boundary` records the creation-baseline rule and its 24 evidence-lineage tests as "NOT ported — rejected by measurement". That is a negative verdict on the design, not an overtaking.
- The live instance is gone (`ls … | grep code-span` matches nothing) and the task it pinned, `2026-07-25-fix-handover-projection-code-span-copy`, is in `tasks/4_done/`. Nothing is left for this task to do.
- Closed through `3_in-review` rather than straight to `4_done`, because the reconciler's lifecycle topology refuses a `1_in-progress` → `4_done` jump. `plan.md` keeps all eight boxes unchecked and carries a supersession note instead; `verification.md` records the commands behind every claim above.
