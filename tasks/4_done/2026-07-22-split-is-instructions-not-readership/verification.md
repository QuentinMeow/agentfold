# Verification — The README/AGENTS split is about instructions, not readership

**Verified:** 2026-07-22 by claude (chat session)

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Reconciler clean, budgets still holding after the rewording

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
exit=0
$ wc -l AGENTS.md README.md
     105 AGENTS.md
     121 README.md
```

## Service tests

```
$ python3 automation/run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 2/2 files passed
```

## Legacy review notes (unbound)

- async-mode gate (tests + reconciler): pass — wording correction in two files, not a
  one-way door.
