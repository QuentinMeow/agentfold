# Should task claims keep their direct-main exception or move into pull requests?

**Action:** Choose whether atomic task claims keep a narrow direct-main exception or must use a new pull-request transaction.
**Why this matters:** Parallel agents need one immediate winner, while you asked for every piece of progress to remain reviewable as a pull request.
**If you do nothing:** Parent design and research continue, but the first planned implementation task cannot start; the current task remains safely claimed under the old rule.

## What you need to know

**Today:** AgentFold writes task claims and status changes directly to `main`; design, code, tests, and evidence use one task branch and pull request.
**What this would change:** The choice either preserves that narrow exception or requires a new atomic claim protocol whose transaction is also represented by a pull request.
**What this does not decide:** This does not choose an agent runtime, task database, dashboard, merge queue, or branch-protection policy.

You wrote, “In the end, I want all progress in the form of PRs.” The existing repository rule was designed for a different constraint: every agent must see one claim winner before implementation starts. An ordinary delayed pull request cannot provide that exclusivity by itself.

> This split keeps the action bus real-time while behavioral and descriptive changes stay reviewable.
>
> — [what the current Git workflow requires](../../../handbook/git-workflow.md#two-kinds-of-writes)

## Your choices

The choices differ in whether “all progress” includes the short-lived coordination transaction that assigns a task before implementation.

### Option A — Keep the narrow exception
Task claims and status transitions remain atomic `harness:` commits on `main`; every design, code, test, and evidence change still uses one task pull request. The cost is that a small class of progress has no pull request of its own.
*Example consequence:* two agents race for one task, one direct push wins immediately, and only the winner opens the implementation pull request.

### Option B — Require a claim pull request
No task claim writes directly to `main`. Before the first planned implementation task starts, a separate design must provide one-winner compare-and-swap semantics, define whether claim refs or pull requests are authoritative, and migrate the current one-task/one-PR contract. The cost is delay and a larger coordination redesign before implementation resumes.
*Example consequence:* two agents race for one task, but neither edits code until the new claim transaction selects one winner and its pull-request-visible state becomes authoritative.

## What I recommend

**Recommendation:** Option A — it preserves the already-tested atomic claim path while keeping every substantive result in a pull request, and a later reviewed task can still replace it.
**Strongest case against this:** Your wording says “all progress,” and silently excluding claims weakens a clear requirement even if the exception is technically safer today.
**Confidence:** medium — three independent reviewers confirmed the conflict, but no PR-based atomic claim design has been built or failure-tested.

Answer in plain words — one sentence is enough. You never need to copy anything; the agent that folds it shows you how it read your words before acting. If this page did not give you enough to decide, say so and say what is missing — that is a complete answer, not a rejection.

**Your answer:** ______

## For the record

<details>
<summary>For the record — bookkeeping the reconciler reads. Nothing here needs you.</summary>

**Status:** waiting  
**Filed:** 2026-08-31, by codex, from task `2026-08-03-plan-multi-worktree-safety-remediation`  
**Full context:** `handbook/git-workflow.md`  
**Resolution evidence:** `memory/decisions/2026-08-31-task-claim-publication.md`  
**Answer by:** 2026-11-29  
**Blocks at:** transition:start task:2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion  

</details>
