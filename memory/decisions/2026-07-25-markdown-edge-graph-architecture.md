# The markdown edge graph ships mined co-change first, with per-folder freshness and a capped edge budget

**Status:** decided
**Date:** 2026-07-25
**Decided-by:** human (2026-07-25 review of `docs/designs/markdown-edge-graph-decisions.md` at sha256:f66ef620df17a07499d9389df1626f3ea01b00cf7a9cc9321e91d006976c27af, approved with two named modifications; response recorded in commit 2abead8)
**Description:** The edge-graph architecture is approved: mine git co-change before building the schema, join it three ways, keep a decision ledger, reinstate graph-only references, commit the generated artifact, offer three per-folder freshness modes defaulting to a 7-day window, cap edges per file with a justified exception, and add discharged-by-filing as a third gate state
**Review-by:** 2027-02-22

## Context

`docs/designs/markdown-edge-graph.md` (v3) proposes a portable way to record why two
documents are related and when changing one obliges revisiting the other. Its owner-facing
summary, `docs/designs/markdown-edge-graph-decisions.md`, put eight numbered questions (N1
to N8) to the owner and recorded the design's recommendation for each.

The revision under review also corrected an earlier conclusion of its own: co-change mining
had been dismissed on a precision figure measured against a reference set of files that
textually cite the target. Re-measurement showed mention-derived and co-change-derived edges
are roughly 95% disjoint on this repository, so that figure scored the technique against the
wrong yardstick, and mining became layer zero.

The owner wrote answers to all eight questions by hand into the decision list and directed
the session to build an execution plan and implement the most important pieces. Six answers
took the recommendation. Two did not, and those two are recorded explicitly below because
they change what gets built. The path-type default and the one-directional authoring model
were settled separately in `memory/decisions/2026-07-25-document-edge-path-types.md` and
`memory/decisions/2026-07-25-document-edges-are-authored-once.md`.

## Decision

The revised architecture is approved. Answers, in the order they were asked:

- **N1 — ship the mined co-change layer first: yes.** The mined layer plus heading-anchor
  validation ships before any schema, migration, or activation, followed by a written
  experiment over two hot files recording whether each top-ranked mined coupling is real and
  whether a hand-authored edge would add anything the mined pair plus its shared commit
  subjects did not. If the mined list is already sufficient, the project stops there and the
  advisory is the whole feature.
- **N2 — adopt the three-way join as the product: yes.** `confirmed`, `undeclared`, and
  `suspect` are reported as one joined result rather than two separate reports the reader
  joins.
- **N3 — the accepted/rejected ledger: in,** and non-optional. A dismissal is durable and
  never re-surfaces, and the rejection rate is reported as the effective-false-positive rate.
- **N4 — reinstate `references`: yes,** as graph-only: never in "must review", and
  `Update-when` forbidden on it. This reverses the earlier D4.
- **N5 — freshness: all three mechanisms, configurable per folder, defaulting to a 7-day
  review window.** *This diverges from the recommendation.* The owner's reasoning, in
  substance: if deriving freshness automatically costs a lot of AI tokens, it should not be
  done automatically — a re-review date, or nothing mechanical, must remain available,
  because the user gets to choose. So all three mechanisms must exist — derived each run,
  an absolute re-review window, and advisory-only — and each folder configures its own mode
  independently of every other folder. The default is a review window of **7 days**. The
  clause-scoped git-derived debt the design recommended is therefore one selectable mode
  ("each run"), not the sole mechanism.
- **N6 — commit the generated graph file: yes.** One committed text projection, marked
  generated, verified byte-exact, with conflicts resolved by regeneration rather than by
  hand-merging.
- **N7 — cap edges per file, plus a justified exception path.** *This diverges from the
  recommendation.* The cap holds as recommended, but a file may go beyond the regular limit
  when the agent supplies a written justification naming **both** why that file needs to
  exceed the cap **and** why decoupling it would be worse. Neither half alone admits the
  exception; an exception without both is a finding, not a judgment call.
- **N8 — retry closure and the third gate state: both.** Review debt closes automatically
  when the dependent is next edited and explicitly when an agent records "checked, nothing
  needed." Blocking findings gain a third state, **discharged by filing**, which clears once
  a queue item names the finding — so a finding whose fix belongs to another task never
  strands an agent into bypassing the hook.

Approval covers the direction and these eight answers. It is not an implementation receipt:
the design document remains a proposal, and every mechanism above still has to be built,
verified against real recorded output, and admitted through the normal task lifecycle.

## Alternatives considered

- Build the typed schema first and judge its value after it exists (N1's alternative) —
  rejected because the mined layer costs no annotation and can prove the schema unnecessary
  in an afternoon.
- Report mined and declared edges separately (N2) — rejected because the delta between
  declared intent and mined reality is the informative part.
- Omit the ledger and accept re-proposals every run (N3) — rejected because the first run's
  `undeclared` list is then unusable and the mechanism dies in week one.
- Keep `references` dropped (N4) — rejected because one-way edges make a mis-typed
  `references` inert in impact output, so its original cost is gone.
- A single freshness mechanism, whichever one (N5) — rejected by the owner: each mechanism
  trades tokens against detection differently, and the choice belongs to whoever owns the
  folder.
- Generate the graph on demand and git-ignore it (N6) — rejected because a bare clone would
  answer nothing, in-edges would never reach a human reviewer, and a stale ignored copy can
  silently answer for a different commit.
- Chase coverage instead of capping (N7) — rejected because fluent filler defeats every
  deterministic prose check, and volume low enough for a human to read each entry is the only
  real defence.
- A hard cap with no exception (N7) — rejected by the owner: a genuinely central file should
  be able to exceed the cap when it can say why, rather than being decoupled artificially.
- Require blocking findings to always be fixed in place (N8) — rejected because it turns the
  blocking tier into a hook-bypass factory.

## Consequences

The next implementation stage is the mined check plus anchor validation and the written
experiment, and it may legitimately end the project. The freshness mechanism is now three
mechanisms plus per-folder configuration and a default, which is more surface than the design
priced; the 7-day window is the behaviour a folder gets when it says nothing. The per-file cap
now needs an exception record with two named justifications, and the exception's prose is
subject to the same "fluent filler defeats deterministic checks" caveat the cap exists to
answer — so the exception count is worth watching as its own signal.

Revisit if the mined experiment shows the typed schema is unwarranted, if per-folder freshness
configuration proves more expensive to maintain than the token cost it was chosen to avoid, or
if cap exceptions become routine rather than rare.
