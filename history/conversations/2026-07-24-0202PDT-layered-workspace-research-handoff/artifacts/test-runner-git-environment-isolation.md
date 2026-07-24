# Test-runner Git-environment isolation — root cause and recovery

## Failure

A commit from the linked `main` worktree invoked the repository pre-commit hook. Git
exported its repository-local environment, including absolute linked-worktree/common
Git paths. `automation/run_tests.py` forwarded that environment unchanged to tests.
Temporary-repository commands in `automation/tests/test_check_core_scope.py` therefore
targeted the real repository rather than their temporary repositories.

Observed effects:

- `main` advanced through synthetic test commits;
- repository-local `core.bare` became `true`;
- repository-local `user.name=Test` and `user.email=test@example.com` were injected;
- the linked `main` worktree index was replaced;
- the active PR #7 worktree and branch tip remained intact.

## Recovery performed

The prior `main` tip was established from the remote-tracking ref and reflog as
`acc23b6289f5ca66744718af379aba0468be93e2`. Recovery:

1. restored `core.bare=false`;
2. removed only the exact synthetic `Test` and `test@example.com` local values;
3. used compare-and-swap ref repair to move `main` from the known synthetic tip back to
   the verified prior tip;
4. rebuilt only the affected linked-worktree index from that commit; and
5. verified branch tips, worktree status, configuration, and the PR #7 checkout.

Do not repeat broad reset/config cleanup: it would risk unrelated user state.

## Preserved repair state

`/private/tmp/2026-07-24-isolate-test-git-environment` is a linked worktree on
`task/2026-07-24-isolate-test-git-environment`. It contains uncommitted task records and
`automation/tests/test_run_tests.py`. The latest focused run reached the intended two
missing-function failures and one Python 3.7 mock-call assertion error. Production
`automation/run_tests.py` is unchanged.

The last test error is mechanical: Python 3.7 exposes keyword arguments as
`run.call_args[1]`; change the assertion to
`run.call_args[1]["env"]`.

## Required implementation and proof

Implement `git_local_environment_names()` using
`git rev-parse --local-env-vars` from the repository root and raise a clear
`RuntimeError` on nonzero status. Implement `isolated_test_environment()` by copying
the supplied/current environment and removing every discovered name. Compute that
environment once in `main()` and pass it as `env=` to every test process.

Verification must include:

- focused unit test;
- all repository tests;
- `automation/reconcile/reconcile.py --check`;
- snapshots of relevant refs, local config, and worktree/index identity before and
  after a runner invocation carrying realistic hook-local Git variables; and
- independent review of the immutable candidate.

The temporary `/private/tmp/agentfold-safe-python/sitecustomize.py` shim was used only
to avoid another corrupting hook run during recovery. It is not the product fix and
must not become a dependency.
