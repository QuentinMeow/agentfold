# Is the test-runner Git-isolation boundary safe and compatible enough to merge?

**Status:** awaiting-artifact
**Filed:** 2026-07-24, by codex, from task `2026-07-24-isolate-test-git-environment`
**Action:** After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.
**Full context:** `roadmap/current-state.md`
**Resolution evidence:** `roadmap/current-state.md`
**Review target:** pending
**Review revision:** pending
**Reviewed revision:** ______
**Review outcome:** pending
**Blocks at:** transition:merge task:2026-07-24-isolate-test-git-environment
**Until then:** The draft PR and later stack layers may be prepared, but this layer does not merge.
**Look-at:** `automation/run_tests.py`; the linked-worktree preservation evidence in `verification.md`
**Why-you-might-care:** Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout.
**If-you-do-nothing:** This PR and its dependent stack layers remain unmerged.

## What you need to know

Git exports repository-local variables to hooks. This change removes those selectors,
builds a metadata-free repository projection outside existing Git discovery paths, and
runs each test from a fresh projected root. It does not claim to sandbox tests that
deliberately target the real repository by an explicit absolute path.

## Differences

- **Approve:** accept the exact post-PR-#7 range as the repository-wide test boundary.
- **Request a named change:** keep this merge boundary closed while an agent repairs
  the specific compatibility or isolation issue and publishes a new revision.
- **Reject:** decline this implementation; the stack remains unmerged and the original
  blocking repair must be re-planned.

## Example

Without the boundary, a test that initializes a temporary repository can inherit the
hook's `GIT_INDEX_FILE` and write into the invoking worktree. With the boundary, the
child receives no repository-selecting Git variables and starts in a disposable
metadata-free projection, so ordinary relative Git discovery cannot reach that
worktree.

Do not answer this item while its status is `awaiting-artifact`. After PR #7 merges and
the exact base is bound, copy `Review revision` into `Reviewed revision` with the
answer.

**Your review:** ______
