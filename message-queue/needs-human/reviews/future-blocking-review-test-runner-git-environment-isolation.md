# Review needed: Should the already-merged test-runner isolation change be accepted?
<!-- human-action-presentation: v2 -->

> **Waiting for your response.**

## What I need from you

**Action:** Review the already-merged exact Git range, then accept it, request a named repair, or require rollback before task completion.

Judge whether the implemented boundary prevents ordinary tests from inheriting or
discovering the invoking checkout without breaking supported test behavior.

## Why this matters

This boundary protects every hook-launched repository test from accidentally redirecting Git operations into the checkout that invoked the test runner.

## If you do not respond

If you do not respond, the code remains on `main` without inferred human approval and the isolation review remains unresolved.

## What changed

**Before this change:** Hook-launched tests could inherit repository-selecting Git environment variables and accidentally operate on the invoking checkout.

**Current state:** The reviewed isolation code is already present on `main` after a provider merge, but its human review is unanswered and the task remains in review.

**Change under review:** The runner removes repository-local selectors, creates a metadata-free repository projection outside existing Git discovery paths, and starts each test from a fresh projected root.

**Not included:** This is not a sandbox against a test that deliberately targets the real repository through an explicit absolute path.

**Additional context:** The current implementation isolates ordinary relative Git discovery and
  inherited hook state. It does not claim to prevent intentionally hostile filesystem
  access.

## Review outcomes

### Approve

**What it means:** Accept the already-merged exact Git range as the repository-wide test-runner isolation boundary.

**Consequence:** This review may close with the exact range accepted as the current isolation boundary.

**Example:** A test initializes a temporary repository without inheriting `GIT_INDEX_FILE`, so its writes stay in the disposable projection rather than the invoking worktree.

### Request changes

**What it means:** Keep the isolation direction while naming a compatibility or escape-path repair against `main`.

**Consequence:** The task stays in review and the current bytes remain on `main` until the named repair is implemented and reviewed.

**Example:** Request changes if a supported linked-worktree test can no longer locate the fixture data it legitimately needs.

### Reject

**What it means:** Reject the already-live implementation as the test-runner boundary and require the reviewed range to be rolled back or replaced.

**Consequence:** Because the reviewed bytes are already on `main`, the task and review stay open until a rollback or reviewed replacement is present there.

**Example:** Reject if a metadata-free projection cannot preserve a required test invariant without exposing the invoking repository.

## Agent recommendation

**Evidence checked:** I reviewed the exact range's design and verification record; they document 19 focused tests, the full suite, a real linked-worktree state-preservation probe, and unanimous independent review of the final implementation.

**Assumptions:** The intended boundary is accidental Git discovery and inherited hook state, not a sandbox against a test that deliberately names the real checkout.

**Confidence:** High, because the exact implementation bytes have focused, full-suite, real-worktree, and independent-review evidence.

**Rationale:** The implemented boundary removes the ambient Git selectors that create accidental cross-repository writes while explicitly limiting its claim to ordinary discovery rather than full sandboxing.

**What could change this recommendation:** A reproducible leak into the invoking checkout, a missed repository-selecting variable, or a supported test broken by projection would justify requesting changes.

**Recommendation:** Approve.

## Your response

Write `approve`, `request changes`, or `reject`, followed by any reason or requested
changes. You may also write `I need clarification`. A plain-language answer is enough;
the agent manages revision tracking.

**Your review:** ______

## References

**Full context:** [current repository state](../../../roadmap/current-state.md)

**Exact review artifact:** [Open the immutable Git range](https://github.com/QuentinMeow/agentfold/compare/25d03257b5ee61753fa9bada609722c4e84a8064...fd2374d99796300ed4325c2961e696092c17875e)

<details>
<summary>Tracking details</summary>

**Status:** waiting
**Filed:** 2026-07-24, by codex, from task `2026-07-24-isolate-test-git-environment`
**Resolution evidence:** `roadmap/current-state.md`
**Review target:** git:25d03257b5ee61753fa9bada609722c4e84a8064...fd2374d99796300ed4325c2961e696092c17875e
**Review revision:** git:25d03257b5ee61753fa9bada609722c4e84a8064...fd2374d99796300ed4325c2961e696092c17875e
**Reviewed revision:** ______
**Review outcome:** pending
**Blocks at:** transition:merge task:2026-07-24-isolate-test-git-environment
**Until then:** The already-merged change remains present without inferred human approval; the task remains in review until it is accepted, repaired, or rolled back.

</details>
