# retries/ — an agent's move

The repair queue: broken invariants detected by the reconciler
(`automation/reconcile/reconcile.py`) and jobs that failed partway. Each file names the
broken invariant and the fix; repairs are idempotent. Agents handle items touching
their session's area; never delete one without fixing it or recording a rejection
reason in the file. Reconciler-filed items are garbage-collected automatically once
their finding clears.

Generated files use `blocking-reconcile-<check>-<subject>.md`; stable finding identity
excludes the timing prefix. `--check` itself no longer fails on advisory findings
(`automation/AGENTS.md`), but retry filing does not yet tier its prefix, so an advisory
finding still files a blocking repair item — tracked by task
`2026-07-22-retry-filing-automation-and-waivers`. File one manually with the appropriate
prefix by copying `templates/queue/retry.md`.
