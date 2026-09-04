# An owner statement becomes a confirmed goal entry without a decision item

**Status:** decided
**Date:** 2026-09-04
**Decided-by:** agent (delegated by the owner's 2026-09-04 instruction to keep one full picture of the repository's end goals; two-way door — it changes a `roadmap/README.md` rule, not a principle, and the README can be changed back)
**Description:** Owner-authored goals are transcribed straight into `roadmap/desired-state.md` as confirmed; agent-proposed goals enter unconfirmed with a clarification; removing or re-prioritising a confirmed goal still needs a decision item
**Review-by:** 2027-03-03

## Context

`roadmap/desired-state.md` was last changed on 2026-07-24. `roadmap/README.md` made every
change to it a one-way door needing a decision item in `message-queue/needs-human/decisions/`,
with a direct owner request transcribed into that item before folding. The cost was high
enough that the rule was not followed: the owner's 2026-08-31 request for a multi-agent
workflow produced two live tasks and no goal line, and on 2026-09-04 the owner asked for one
full picture of the repository's end goals so that agents cannot drift toward goals they
generated themselves. A picture that goes stale whenever the owner speaks in chat cannot
serve that purpose.

## Decision

- An owner statement — in chat, in an answer to a queue item, or in a request document — is
  transcribed directly into a goal entry (`templates/roadmap/goal.md`) marked
  `Confirmed: <date> by owner`, quoting the owner's words. No decision item is filed,
  because the owner authored the statement; the transcription is agent-attested like every
  other transcription in this repository.
- A goal an agent believes is missing is added as `Confirmed: no — agent-proposed` together
  with a non-blocking clarification in `message-queue/needs-human/clarifications/` asking the
  owner to confirm it.
- Removing or re-prioritising a confirmed goal stays a one-way door that needs a decision
  item first; a retired goal keeps its heading and gains `Retired:`, so old task records
  still resolve.
- Every task's `## Fit` names the goal it serves or the clarification asking which goal
  should.

## Alternatives considered

- A decision item per transcription (the previous rule) — rejected: it is why the roadmap
  went stale; the owner was being asked to approve their own words.
- A separate owner-statements ledger beside the roadmap — rejected: a second file holding
  the same words as the goal entries and the task requirements files, against
  `handbook/principles/single-source-of-truth.md`.
- Blocking `reconcile.py --check` until an agent-proposed goal is confirmed — rejected:
  nothing a human owes holds a Git edge
  (`memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md`); the reconciler
  reports an unconfirmed goal older than 30 days as advisory instead.

## Consequences

- The full picture stays current at the cost of one dated entry per owner statement; the
  owner's words appear in the roadmap verbatim, and the `roadmap-goals` check refuses an
  entry without provenance or a confirmation state.
- Agents can no longer add a goal silently: an unconfirmed goal carries its clarification
  path on its face, and `roadmap-goals-advice` reports one left unconfirmed for more than
  30 days.
- Revisit if the owner asks to approve transcriptions before they land, or if a
  transcription is found to misquote the owner; the append-only rule makes a misquote
  visible in Git history.
