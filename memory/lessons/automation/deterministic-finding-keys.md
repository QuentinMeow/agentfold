# Reconciler findings need deterministic keys

**Description:** Auto-filed retry items must be keyed by check+subject, or every rerun duplicates the queue
**Area:** automation
**Last-confirmed:** 2026-07-22
**Review-by:** 2027-01-22

## Failure

A checker that files a repair item per finding, named with a timestamp or counter,
creates a *new* file on every run for the *same* unfixed problem — the retry queue
fills with duplicates and agents burn sessions deduplicating.

## Root cause

The finding's identity was the run, not the broken invariant.

## Rule

Key every auto-filed item by `<check-id>-<subject-slug>` (e.g.
`reconcile-handover-present-2026-07-22-1500-bootstrap`). Re-runs then overwrite the
same file idempotently, and the same key lets the reconciler garbage-collect its item
the moment the finding clears. Applies to anything that writes queue items
mechanically.
