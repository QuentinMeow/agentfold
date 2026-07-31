# The edge graph ships two freshness modes; `each-run` is measured, deferred, and not implemented

**Status:** decided
**Date:** 2026-07-25
**Decided-by:** human (explicit queue answer recorded in commit 5d315f9, claimed in 1a54c4c)
**Description:** Amends one third of N5 in the edge-graph architecture decision: `review-window` (default, 7 days) and `advisory` ship, `each-run` is recorded as not implemented rather than rejected after measuring zero filed items across the whole history of the design's strongest case, and returns only when two recorded window misses meet a stated four-part test
**Review-by:** 2027-03-08
**Amends:** `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md` — the `each-run` third of N5; the 7-day default and per-folder choice stand

## Context

`memory/decisions/2026-07-25-markdown-edge-graph-architecture.md` recorded the owner's
answer to question N5: all three freshness mechanisms exist — `each-run` (review debt
derived from git on every run), `review-window` (an absolute re-review date, default 7
days), and `advisory` (nothing mechanical) — each folder picks its own mode, and the
default is the 7-day window. That ADR is decided and immutable, so this file amends it
rather than editing it.

Stage 0 of `docs/designs/markdown-edge-graph.md` then shipped the mined co-change layer
and ran the gating experiment the plan required, which measured what `each-run` would
actually have filed over the recorded history of the design's single decisive example —
the delivery-prefix rule owned by `message-queue/AGENTS.md` and restated in all five queue
templates. The answer was zero, and the reason it was zero also makes the mode blind to
the one real drift in its own domain. The measurement was put back to the owner as a
keep-or-drop decision.

The owner answered, verbatim:

> choose B for now, but keep A in mind (or mark as not implemented), we might review it
> later.

## Decision

**Two freshness modes ship, not three.** `review-window` stays the default at 7 days,
`advisory` stays the cheap opt-out, and the per-folder configuration surface shrinks to a
two-way choice. The clause anchor stays, because it earned its place on the impact query
independently of any freshness mode. Field schema and mode semantics are not restated
here; they live in `docs/designs/markdown-edge-graph.md`.

**`each-run` is recorded as not implemented — deferred, not rejected.** No clause-to-line-
range intersection, no per-run git history pass, and no derived review debt are built. The
mode remains a live option with a stated trigger below, and reinstating it is a new ADR,
not a re-reading of this one.

**What this supersedes, precisely.** In the architecture ADR it supersedes exactly the
`each-run` third of N5: the existence of a git-derived per-run debt mechanism, and the
three-way per-folder mode set that existed largely to switch that mechanism off. It
supersedes nothing else. The rest of N5 stands untouched — freshness is still chosen per
folder, no folder's mode constrains another's, and the mode a folder gets when it says
nothing is still the 7-day review window. N1 (mine first), N2 (the three-way join), N3
(the non-optional ledger), N4 (`references` reinstated as graph-only), N7 (the per-file
edge cap with its two-part justified exception), and N8 (retry closure plus discharged-by-
filing) all stand exactly as decided. N6 is amended separately by
`memory/decisions/2026-07-25-edge-graph-artifact-storage.md`.

## Alternatives considered

- **Option A — keep all three modes, exactly as answered in N5.** Not rejected: deferred
  and revisitable, with the trigger below. It lost now because it was measured to file
  zero items across the entire recorded history of the strongest case available, and to be
  silent on the only live drift inside that history.
- **Drop `each-run` with no revisit condition.** Rejected: the owner's answer was "keep A
  in mind", and a deferral that depends on someone remembering is not a deferral.
- **Drop clause anchoring along with the mode it was introduced to serve.** Rejected: on
  `message-queue/AGENTS.md` clause scoping is worth about 4.7× on the impact query — an
  edge anchored at the routing clause fires on 3 revisions rather than 14 — which is value
  the anchor earns without any freshness mechanism behind it.
- **Rewrite the N5 answer inside the architecture ADR.** Rejected: a decided ADR is never
  rewritten; a reversal is a new file linking the old one (`memory/AGENTS.md`).

## Consequences

**What gets built.** A dated re-review field per edge and the prose mode, both of which
this repository already runs successfully on memory entries. No git history pass runs per
invocation, and `Update-when:` stays prose the impact query prints. The aca7014 class of
drift is now caught by whoever reviews a dated edge when its window comes due, rather than
by a derived intersection that closes on an unrelated touch.

**The measurement this rests on, carried so the revisit has a baseline.** Over the 14
in-scope revisions of `message-queue/AGENTS.md`, the prefix definitions themselves changed
in exactly 2 — commits aca7014 and 3f4f1df. In both of those commits every restating
template was edited in the same commit: aca7014 touched all five queue templates, and
3f4f1df touched all five plus `templates/handover.md`. Derived debt closes on a touch, so
across that entire history `each-run` would have filed **0 items**. Worse, the one live
drift the mechanism exists to catch happened *inside* aca7014, which propagated "UTC" into
the owning contract at `message-queue/AGENTS.md` line 17, into the check summary in
`automation/AGENTS.md`, and into all five templates' `Blocks at` field lines while leaving
line 4 of each template reading "a named date" — an inconsistency still live in the
repository today. Two supporting figures bound the shape of the surface: `automation/AGENTS.md`
is the hottest markdown file at 19 in-scope revisions with exactly one heading, so clause
anchoring degenerates to file scoping there and 12 of the 29 judged candidates (41%) point
at it; on `message-queue/AGENTS.md` clause scoping is real and worth about 4.7×.

**Revisit trigger — checkable, not remembered.** `each-run` returns as a new decision when
**two or more** independent instances are on record, each written as an entry under
`memory/known-issues/` that names all four of:

1. the target file and the clause whose lines changed, with the introducing commit id;
2. evidence that the introducing commit did **not** touch the declaring dependent — the
   condition under which clause-scoped derived debt would have fired instead of closing;
3. the declaring edge's `review-window` due date, already passed, with the drift still
   live at that date;
4. how the drift was actually found — a reader, a review, or another check — rather than
   by the window.

The count is answerable with one `git grep` over `memory/known-issues/`, so the trigger is
a number rather than a judgment. Two, rather than one, because the finding that killed the
mode was not that it is small but that it is empty over an entire history — 0 of 14
revisions, and blind to the only real drift in that history — while the design's own
caveat is that four days and 107 in-scope commits will move every mined number in an
unknown direction; one counter-example sits inside that noise, two independent ones do
not. Condition 2 is the load-bearing clause: it excludes exactly the case the measurement
found, where the dependent was touched in the drifting commit and `each-run` would have
been silent too, so an instance only counts when derived debt would genuinely have caught
what the window missed. Condition 3 is what makes the instance evidence against
`review-window` rather than merely evidence that drift exists.

**What this commits us to in the meantime.** A folder that wants mechanical freshness gets
a date, and a folder that wants none gets prose; there is no third answer to give, and the
per-folder configuration is a two-way switch. If the trigger above is met, the returning
decision inherits a real baseline — the numbers above — instead of a projection of one.
