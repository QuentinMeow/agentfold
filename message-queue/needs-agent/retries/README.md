# retries/ — an agent's move

The repair queue: broken invariants detected by the reconciler
(`automation/reconcile/reconcile.py`) and jobs that failed partway. Each file names the
broken invariant and the fix; repairs are idempotent. Agents handle items touching
their session's area; never delete one without fixing it or recording a rejection
reason in the file. Reconciler-filed items are garbage-collected automatically once
their finding clears.

Every current reconciler finding blocks repository admission, so generated files use
`blocking-reconcile-<check>-<subject>.md`; stable finding identity excludes the timing
prefix. File one manually with the appropriate prefix by copying
`templates/queue/retry.md`.
