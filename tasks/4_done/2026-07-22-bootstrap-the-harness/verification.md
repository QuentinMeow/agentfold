# Verification — bootstrap

**Verified:** 2026-07-22 by claude (bootstrap session)

## Service tests

```
$ python3 automation/run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 2/2 files passed
```

## Installer (after git init)

```
$ python3 automation/install.py
git hooks: core.hooksPath -> automation/hooks
CLAUDE.md shims: 10 in place
skill adapters: .claude, .cursor, .agents -> skills/
install: done (idempotent — re-run whenever skills or AGENTS.md files change)
```

## Reconciler — checks bite, then pass

The first full run surfaced three real defects (this file missing; a non-repo-relative
path in `tasks/AGENTS.md`; the task-structure check tripping over installer-created
`CLAUDE.md` shims). All fixed:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## Self-healing loop — break → auto-file → fix → auto-clear

```
$ mkdir history/conversations/2026-07-22-1600-retry-demo   # violate an invariant
$ python3 automation/reconcile/reconcile.py --file-retries
retries: 1 filed/refreshed, 0 cleared
$ rmdir history/conversations/2026-07-22-1600-retry-demo   # fix it
$ python3 automation/reconcile/reconcile.py --file-retries
retries: 0 filed/refreshed, 1 cleared
reconcile: 0 finding(s)
```

The demo also exposed a cascade bug (retries filed about retry items citing dead
paths) — fixed, and recorded as
`memory/lessons/automation/repair-records-cite-broken-state.md`.

## Review verdicts

- No panel — bootstrap ran solo by owner instruction; first outside-agent session is
  the real review (`roadmap/desired-state.md`, line 1).
