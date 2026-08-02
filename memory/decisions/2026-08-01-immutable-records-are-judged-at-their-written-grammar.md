# An immutable record is judged by the grammar it was written under

**Status:** decided
**Date:** 2026-08-01
**Decided-by:** agent (two-way door: the split is one function and can be re-joined; it restores a rule two contracts already stated)
**Description:** A committed record's spelling is fixed by the schema marker in its own creation snapshot; only its rejections ratchet at the admission edge.
**Review-by:** 2027-02-01

## Context

`handover_action_entry_version_for` governed a handover by the highest entry-schema version
reachable from the candidate. Two things could raise that number without the record's own
history saying anything: a version **withdrawn** before the record existed (`v3` was activated
at `03ec388`, withdrawn at `b4c6627`, then the number was reused at `219ae1f` for an unrelated
label rename), and a version activated in **parallel history** and joined at the admitting merge.

Both made an already-committed record fail a grammar that did not exist when it was written.
`history/AGENTS.md` forbids editing committed handover bytes, so the only repair the finding
named was one the repository refuses — the check was unsatisfiable, and it made any branch cut
before a version bump permanently unmergeable. PR #44 was stuck on exactly this, and one
handover on `main` carried the same latent failure.

## Decision

An obligation may be placed on an already-committed record only if the record's author could
have satisfied it at the moment of writing. That splits one version number into two:

- **Written grammar** — the marker in `history/AGENTS.md` at the record's own creation commit.
  It fixes how the record is spelled. Nothing later or parallel may raise it. A declared marker
  already accounts for every activation and withdrawal on that line of history, so a reused
  withdrawn number governs nothing in between.
- **Rejection floor** — the highest version the admission edge reaches, parallel history joined
  with an activation included. It selects which rejecting clauses apply. It only ratchets up, so
  it can never demand bytes a record lacks, and cutting a branch early escapes none of it.

A newer version therefore may add rejections and may rename its rendering, but a rename binds
only records written after it. A rejection, once added, is never switched off by a later version.

## Alternatives considered

- Renumber the label rename off the burned `v3` — rejected on evidence: a handover already on
  `main` (created at `9c0c7e6`) declares `v3` in its creation snapshot and uses the new labels,
  so renumbering would break it. All 65 other reachable handovers likewise match their own
  creation-snapshot marker exactly.
- Drop the parallel-history join outright — rejected: it is what stops an agent cutting a branch
  before a rejecting version to escape it.
- Keep the join and rewrite the record's bytes — forbidden by `history/AGENTS.md`.

## Consequences

- Every schema marker on a record path now means "what this record was written under", and every
  check over such a record must ask which of its two jobs it is doing.
- A rejecting change may still be shipped by bumping the version; a rendering change binds
  forward only, so the repository will carry both spellings for as long as the old records live.
- Revisit if a version ever needs to reject something in records already written — that is a
  deliberate breaking migration and needs its own decision, not a silent floor raise.
- `handover_liveness_version_for` still uses the floor alone. It is exposed to the same
  unsatisfiability in principle; nothing reproduces it today, so it was left untouched.
