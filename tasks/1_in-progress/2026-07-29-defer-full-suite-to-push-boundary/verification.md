# Verification — give the commit gate a routine lane

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output.

This task's central premise did not survive measurement, so it closes without its
implementation landing. What follows is what was actually established and where the
one surviving acceptance criterion shipped instead. The reasoning is recorded in
`memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`; the branch that
carried the experiment is preserved on the remote as exp/c-tiered.

## The premise is unsound once input-ownership selection exists

The routine lane's rule was written against a selector that escalated to the full
suite for almost every path, so declining to escalate looked cheap. After input
ownership landed, escalation survives only in the selector's fail-closed branches —
a crossed symlink, an index that moves during selection, a removed non-record source
file. The rule converts each of those into an empty selection, so deleting a service
source file would satisfy the gate having run nothing.

## Acceptance criterion 1 shipped under a different task

The deferred-coverage report is on main through
`2026-07-30-report-unrun-coverage-honestly`, justified by proof rather than by
deferral. A records-only commit names every skipped file before any test starts:

```
$ git commit -F - < ...     # commit d8c4c06, pre-commit hook output
pre-commit: staged-path repository tests
test lane: staged
test reason: every staged path is a record path no test reads
staged paths: 1
  tasks/1_in-progress/2026-07-30-stop-background-git-maintenance/design.md -> record path, no test reads it
selected test files:
  (none)
skipped test files: 11 (no staged path owns them); the complete suite still runs on every push
  automation/tests/test_check_action_projection.py
  ...
  services/quote-cli/tests/test_quote_cli.py
no discovered test file can be affected by the staged change
tests: 0/0 files passed
test elapsed: 0.02s
pre-commit: OK
```

## Criteria 2 to 4 close with the premise

Criterion 2 holds unchanged on main: the bare runner invocation still runs the full
suite, and its own help text states that the default is always the full suite.

```
$ python3 automation/run_tests.py --jobs 8
...
tests: 11/11 files passed
test elapsed: 46.41s
```

Criteria 3 and 4 described configuration and a guard for a lane that does not exist,
so nothing implements them. The cost problem they targeted was answered instead by
sharding the suite below the file, which needs no skip rule at all.
