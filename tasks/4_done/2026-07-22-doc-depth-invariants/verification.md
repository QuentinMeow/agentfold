# Verification — Codify queue-message disposability and README depth rules

**Verified:** 2026-07-22 by claude (chat session)

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Reconciler clean on the changed tree

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
exit=0
```

## Service tests

```
$ python3 automation/run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 2/2 files passed
exit=0
```

## New README budget check fires when exceeded

Padded the README past 140 lines (uncommitted), ran the check, restored:

```
$ for i in $(seq 1 30); do echo "padding line $i to push the README over budget" >> README.md; done
$ wc -l README.md
     151 README.md
$ python3 automation/reconcile/reconcile.py --check
[agents-budget] README.md: 151 lines exceeds the 140-line budget
    fix: move depth into a linked doc (handbook/principles/progressive-disclosure.md)
reconcile: 1 finding(s)
exit=1
$ git checkout -- README.md
$ wc -l README.md
     121 README.md
```

## Legacy review notes (unbound)

- async-mode gate (tests + reconciler): pass — no adversarial panel needed; the change
  is additive docs plus one additive check, not a one-way door.
