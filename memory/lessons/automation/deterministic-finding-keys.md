# Reconciler findings need deterministic keys

**Description:** Auto-filed retries use full check+subject identity, digest-bearing names, and refreshable machine projections that preserve actor notes
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

Key every auto-filed finding by the full `<check-id>, <subject>` identity. A readable
slug may be truncated only when a digest of that full identity remains, or two long
subjects can collide. Aggregate all same-identity violations into one generated block
and refresh that block on rerun while preserving actor-owned status and notes. Put
dependency timing outside the identity: a timing change can rename the message without
duplicating the finding, and the stable key garbage-collects it when all violations
clear. Applies to any mechanical queue writer.
