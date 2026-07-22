# Verification — protect AgentFold core portability

**Verified:** 2026-07-22 by codex

Only commands actually run and their real output are recorded below.

## Clean replacement ancestry and scope

```
$ git merge-base --is-ancestor origin/task/2026-07-22-design-critical-agent-guardrails HEAD
(no output; exit 0)

$ python3 -c 'import subprocess; names=subprocess.check_output(["git","diff","--name-only","origin/task/2026-07-22-design-critical-agent-guardrails...HEAD"], text=True).splitlines(); markers=("github-auth-guard","install_codex","codex_hook","codex-github"); found=[name for name in names if any(marker in name for marker in markers)]; print("incident-specific paths:", ", ".join(found) if found else "none"); raise SystemExit(bool(found))'
incident-specific paths: none
```

## Core-scope range gate on both available Python runtimes

```
$ python3 --version
Python 3.7.6
$ python3 automation/check_core_scope.py --range origin/task/2026-07-22-design-critical-agent-guardrails...HEAD --branch task/2026-07-22-protect-core-portability
core-scope: pass (15 core path(s), task 2026-07-22-protect-core-portability)

$ /usr/bin/python3 --version
Python 3.9.6
$ /usr/bin/python3 automation/check_core_scope.py --range origin/task/2026-07-22-design-critical-agent-guardrails...HEAD --branch task/2026-07-22-protect-core-portability
core-scope: pass (15 core path(s), task 2026-07-22-protect-core-portability)
```

## Repository invariants

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## Explicitly invoked review gate

```
$ python3 automation/check_core_scope.py --range origin/task/2026-07-22-design-critical-agent-guardrails...HEAD --branch task/2026-07-22-protect-core-portability --require-review
core-scope: pass (15 core path(s), task 2026-07-22-protect-core-portability)

$ /usr/bin/python3 automation/check_core_scope.py --range origin/task/2026-07-22-design-critical-agent-guardrails...HEAD --branch task/2026-07-22-protect-core-portability --require-review
core-scope: pass (15 core path(s), task 2026-07-22-protect-core-portability)
```

## Repository tests

```
$ python3 automation/run_tests.py
.........................................
----------------------------------------------------------------------
Ran 41 tests in 0.345s

OK
.....
----------------------------------------------------------------------
Ran 5 tests in 0.177s

OK
...
----------------------------------------------------------------------
Ran 3 tests in 0.413s

OK
PASS automation/tests/test_check_core_scope.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 3/3 files passed
```

## Legacy review notes (unbound)

- core-fit / core-fit-review: approve — the substitutable core-scope model remains unchanged.
- core-fit / flexibility-review: approve — changes remain limited to CommonMark evidence parsing, preserve the approved flexibility boundaries, and all 41 scope tests pass.
- core-fit / gate-correctness-review: approve — the source-order parser now preserves CommonMark line and block boundaries, and all targeted regressions plus both full-runtime suites pass.

## Review verdicts

**Reviewed revision:** 72476380d0acfa5190a845efff09277bf821abce

- core-fit / manual-review-correctness: approve — full object IDs, identity parsing, revision binding, and status-move canaries resisted the final counterexamples.
- core-fit / manual-review-contract: approve — the human decision, superseding ADR, canonical schema, migrated legacy records, and current documentation agree.
- core-fit / manual-review-blast-radius: approve — records-only follow-up and identical status moves remain possible while later core or task-input changes stale the receipt.

## Manual-by-default review verification

```
$ python3 automation/check_core_scope.py --staged --branch task/2026-07-22-protect-core-portability --require-review
core-scope: pass (no later core changes, task 2026-07-22-protect-core-portability; independent review verified)

$ python3 automation/run_tests.py
......................................s..............
----------------------------------------------------------------------
Ran 53 tests in 1.271s

OK (skipped=1)
.....
----------------------------------------------------------------------
Ran 5 tests in 0.156s

OK
...
----------------------------------------------------------------------
Ran 3 tests in 0.328s

OK
PASS automation/tests/test_check_core_scope.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 3/3 files passed

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --cached --check
(no output; exit 0)
```

The skipped scope canary creates a real SHA-256 Git repository and runs only when the
installed Git supports that object format. Full 40- and 64-character receipt parsing is
covered in every run; the exact resolved-object check remains active regardless of
repository format.
