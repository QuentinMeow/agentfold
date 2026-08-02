# Never reuse a schema version number that was activated and withdrawn

**Description:** A version number that ever reached a commit is burned; reuse it and old records get judged by the new meaning.
**Area:** automation
**Last-confirmed:** 2026-08-01
**Review-by:** 2027-02-01

## Failure

`Queue action-entry schema: v3` was activated at `03ec388` (it meant the unresolved-projection
rule), withdrawn at `b4c6627` when that rule moved to its own `Queue liveness schema` marker,
and the entry marker rolled back to `v2`. `HANDOVER_ENTRY_VERSIONS` shrank to `("v1", "v2")` in
the same commit, so the withdrawal passed every check. `219ae1f` then re-added `"v3"` for an
unrelated suffix-label rename.

Both `v3` meanings now live in reachable history under one string. Every record written after
`03ec388` descends from a commit that once declared `v3`, so a reachability-based lookup judged
records written under `v2` by the rename that arrived months later. PR #44 could not merge, and
one handover on `main` was already latently broken the same way.

## Root cause

Withdrawing a version removed the *code* that recognised the string, not the *commits* that
carry it. Shrinking the recognised-version tuple hides a burned number only until someone
re-adds it.

## Rule

Treat every version string that has ever been committed on a marker as permanently spent, even
if it was rolled back. Reuse means the next number, never the withdrawn one. When you must judge
an existing record against a marker, read the marker in that record's own creation snapshot
rather than searching reachable history: a declared value already accounts for every activation
and withdrawal on its own line, and reachability cannot tell the two meanings apart.
