# The commit gate skips a test only on proof, never on deferral

**Status:** decided
**Date:** 2026-07-30
**Decided-by:** human (the owner merged pull requests 20, 21 and 22, then directed the remaining work in chat)
**Description:** A local gate may skip a test only when nothing the test reads has changed; "a later boundary will run it" is not a reason to skip
**Review-by:** 2027-01-30

## Context

The pre-commit gate ran the whole suite: 219.16s measured, 231.54s for a real two-line
commit. Task `2026-07-27-configure-test-gates-and-time-budgets` answered that with a
configuration file, budget deadlines, receipts and auto-filed regression tasks, and
merged no speedup.

Measurement found the cause instead of inferring it. The suite made 13,261 Git
subprocess calls with 92-93% of wall time inside them, and the runner wrapped every one
of them in a `/bin/sh` script named `git`, so each call cost two processes. Removing that
shim, batching the reconciler's blob reads, and selecting tests by staged input ownership
landed as pull requests 20, 21 and 22.

Two experiments proposed to stop running the whole suite at commit time, and they
justified it differently. The selector that merged skips a test when the staged change
cannot reach it. The experiment that did not merge, on branch exp/c-tiered, skipped
whenever a narrow scope could not be proven, on the grounds that the pushed workflow runs
the full suite anyway.

## Decision

A local gate may skip a test only on evidence that running it cannot change the answer.
It may not skip a test on the grounds that some later boundary will run it.

The distinction is not stylistic. Deferral is a promise about the future and it weakens
exactly where it is least affordable: the change whose blast radius nobody has registered
is the change whose coverage gets deferred. Proof is a receipt about the present, it is
checkable locally, and it does not decay as the suite grows.

Every uncertainty resolves toward running the test. An unreadable index, an unmergeable
status, a removed or renamed source path, a symlink crossing, an index that moved while
the selector was reading it, and a path with no registered owner all select the full
suite. That list is the mechanism, not an implementation detail: a selector that fails
open converts a hazard detector into silence.

## Consequences

A records-only commit selects no test and its test step measures 0.02s, while a change to
`automation/reconcile/reconcile.py` still selects the file that is 68-79% of the suite.
Selection is already correct in that second case; the selected unit is simply too large,
so further speed has to come from making tests cheaper and running them concurrently
rather than from skipping more of them.

Branch exp/c-tiered is not merged. Its `routine_selection` would have converted eleven
distinct fail-closed branches of the selector into an empty selection, including the
symlink, index-race and removed-source-path guards — deleting a service source file would
have passed the gate with no test run. Its reporting improvements were largely already
delivered by the selector that merged. What survives from it is recorded in
`tasks/1_in-progress/2026-07-30-report-unrun-coverage-honestly/task.md`.

The complete suite still runs on every push of every branch, unfiltered, and the push
boundary is deliberately not allowed to consult any local skip evidence — that is where a
flaky green gets caught rather than cached.

## Alternatives considered

Speed alone, with no selection table, was the standing recommendation and was rejected by
the owner in favour of keeping selection: a table guarded by a test that fails when a test
reads a path the table withholds from it is a smaller permanent liability than paying the
whole suite on every records-only commit.

Building the configuration-file design as written was rejected by measurement. `tomllib`
exists on neither interpreter here, and a policy language makes nothing faster.
