# Finish the test-runner Git-environment isolation repair

**Status:** in-repair
**Filed:** 2026-07-24, by codex, from the linked-worktree corruption observed in this session
**Action:** Take over branch task/2026-07-24-isolate-test-git-environment, complete its TDD fix, and prove that hook-launched tests cannot mutate the invoking repository's config, refs, or worktree indexes.
**Full context:** [root-cause and recovery record](history/conversations/2026-07-24-0202PDT-layered-workspace-research-handoff/artifacts/test-runner-git-environment-isolation.md)
**Resolution evidence:** `automation/run_tests.py`
**Blocks now:** operation:linked-worktree-commit-and-test

## What you need to know

Git exports repository-local variables to hooks. In a linked worktree those variables
contain absolute paths into the real common Git directory. `automation/run_tests.py`
currently inherits them into every test subprocess, so tests that create temporary
repositories can instead commit into the real repository.

The real failure moved the main branch, set `core.bare=true`, injected the synthetic test
identity, and replaced the linked-worktree index. Recovery restored the main branch
and its remote-tracking ref to the prior base
(`acc23b6289f5ca66744718af379aba0468be93e2` at the time),
removed only the two injected config values, reset only the affected linked-worktree
index, and verified the PR #7 checkout stayed intact.

Preserved local work:

- worktree: `/private/tmp/2026-07-24-isolate-test-git-environment`;
- branch: task/2026-07-24-isolate-test-git-environment;
- uncommitted task/design/worklog records and a focused red test at
  automation/tests/test_run_tests.py;
- no production implementation has been written.

Required fix:

- ask Git for the complete current list from `git rev-parse --local-env-vars`;
- fail closed when that discovery fails;
- remove every returned name from a copy of the parent environment;
- pass the sanitized environment explicitly to every repository test subprocess;
- keep the boundary in the canonical runner, not only the current hook or each test.

The focused test was made Python 3.7-compatible except its last assertion still needs
`run.call_args[1]["env"]` rather than `run.call_args.kwargs["env"]`.

## Done when

The focused regression is red before and green after the minimal implementation; the
full repository suite and reconciler pass; and a real or equivalently contaminated
linked-worktree hook probe shows unchanged repository config, refs, primary worktree
state, and unrelated worktree indexes. Record exact commands/output, obtain independent
review, push the task branch, and only then delete this request.
