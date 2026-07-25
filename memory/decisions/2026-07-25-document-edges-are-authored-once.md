# Document edges are authored once, in the forward direction only

**Status:** decided
**Date:** 2026-07-25
**Decided-by:** human (explicit queue answer recorded in commit 2abead8)
**Description:** Only the forward direction of a document edge is ever written in a file; no reverse side is authored, and a generated graph artifact is the mechanism for finding related pieces
**Review-by:** 2027-02-08

## Context

The markdown edge graph design (`docs/designs/markdown-edge-graph.md`) had to settle who
writes an edge. The owner had originally asked for double-ended links whose metadata lives
inside both files, so each file states its side of the relationship.

Measuring the repository showed that shape is not reachable here. `tasks/AGENTS.md`,
`message-queue/AGENTS.md`, and `automation/AGENTS.md` each sit at exactly 60 of 60 lines
permitted by the reconciler's budget check, and the root `AGENTS.md` is referenced by 53
files with 21 lines of headroom, so writing reciprocal blocks into targets produces a budget
failure fixable only by deleting contract prose. It would also mean one folder writing into
another folder's files, against the isolation rule in
`handbook/principles/folder-as-a-service.md`.

## Decision

Links stay one-directional. Only the forward direction is ever written in a file, by the
file that would become wrong if the target changed; a reverse side is not merely derived but
does not exist as authored text, so there is nothing to keep in sync. A CLI generates the
full graph artifact holding both directions, and that artifact — not a reciprocal block in
each file — is the mechanism an agent uses to find the pieces relevant to a change. The
owner's answer strengthened the recommended option rather than accepting it: a bidirectional
link is not preferred at all.

Nothing is ever written into another folder's files by this mechanism. The design document
remains the single home of the relation vocabulary, the authoring rule's one exception, and
the artifact's format.

## Alternatives considered

- Author both sides and cross-check them for proper inverse relations — rejected because the
  highest-traffic contracts would have to be exempted from receiving reciprocals or have
  their budgets raised, which excludes exactly the files most worth linking and inverts a
  deliberate one-way dependency.
- Author one side and *display* the reverse in each file — rejected for the same budget
  reason: the reverse still has to be written somewhere in the file to be visible there.
- Keep the reverse direction only in memory at query time, with no committed artifact —
  rejected as a separate decision (see the architecture record for the committed artifact),
  because a bare clone would then answer nothing without running a command.

## Consequences

Opening a file does not show what depends on it; the impact query and the generated graph
artifact answer that instead, and their honesty is now load-bearing for the whole feature.
Every later choice about the edge schema, the checker, and the query tool follows from this
one, and reversing it means rewriting every declared edge — so a future proposal for
reciprocal metadata must first resolve the line budgets and the folder-isolation rule that
killed it here.

Revisit if the budgeted contracts gain enough headroom that reciprocal blocks become
writable, or if the generated artifact proves unusable as the only reverse-direction surface.
