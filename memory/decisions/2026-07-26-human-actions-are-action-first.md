# Human actions put the decision before tracking details

**Status:** decided
**Date:** 2026-07-26
**Decided-by:** human (requested a self-contained, action-first review interface)
**Description:** Human attention files lead with one clear action, present and proposed behavior, symmetric choices, recommendation rationale, and no-response consequences; machine tracking is collapsed at the end
**Review-by:** 2027-01-22
**Supersedes:** `memory/decisions/2026-07-22-bold-key-frontmatter.md`, `memory/decisions/2026-07-22-surfaced-asks-are-links-plus-context.md`

## Context

A rendered human review file exposed a wall of lifecycle metadata before explaining
the judgment. It mixed current and proposed behavior, described alternatives with
uneven fragments, repeated links to the same file, and projected an already answered
`folding` review as if the human still needed to act. Labels such as
hyphen-joined machine field names optimized parser convenience at the cost of natural
English.

The earlier frontmatter decision made every item lead with bold-key metadata. The
earlier surfaced-ask decision improved delivery by requiring a link plus context, but
its free-form two or three sentences did not reliably distinguish the requested
action, recommendation, and no-response behavior. Both decisions predated the queue's
strict lifecycle and now produce an interface that is mechanically complete but hard
to review.

## Decision

Human attention files use Human action presentation schema v2. They begin with one
plain lifecycle notice, one clear action, one sentence explaining why it matters, and
one sentence stating what happens without a response. The notice says whether the
action is waiting, not ready, or already received. The file then distinguishes current
state from future or proposed behavior. Decisions compare options, clarifications compare
interpretations, and reviews compare outcomes. Every choice uses the same labels and
level of detail. The agent's recommendation follows the choices and its calibration:
evidence actually checked, assumptions, confidence, rationale, and what could change
the recommendation appear in that order, with the recommended answer last. Showing the
basis and uncertainty before the conclusion reduces anchoring on agent authority. A
core fact the recommendation depends on cannot be left as an unverified assumption.

The file is self-contained. References add depth and each destination appears once as
a reader-facing link. A human supplies only a plain answer or review. Bold-key fields
remain the machine-readable syntax, but lifecycle-only metadata is no longer required
as top frontmatter: it appears in a collapsed `Tracking details` block at the end.
Reader-facing `Action` and `Full context` remain beside the prose they describe. A
review target remains literal beside its revision in tracking, avoiding a duplicate
visible link when it is also the full-context source. A Git commit or range also exposes
one exact-artifact link whose provider-neutral HTTPS or repository-relative destination
contains the full bound commit id or both range ids.

An unpublished review recommends waiting for the exact target. A waiting review
recommends one of its three presented human outcomes: approve, request changes, or
reject. A human may choose one or ask for clarification. `abandoned` remains an
agent-managed lifecycle state for pursuit that ends without a human review judgment;
it is not a hidden fourth human choice.

Only `Status: waiting` means the human can act. `awaiting-artifact` is not ready, and
`folding` is agent-owned. Queue action-entry schema v3 therefore projects every and
only waiting human item as one action link followed by its plain `Why this matters`
and `If you do not respond` sentences. It omits parser-style labels and technical
metadata. Queue resolution schema v1 and Queue projection schema v1 remain unchanged;
the new presentation and entry markers version only the human interface.

## Research basis

- Microsoft's validated [Guidelines for Human-AI Interaction](https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/)
  support setting expectations, making uncertainty visible, and enabling correction.
- Bansal and colleagues found in
  [Does the Whole Exceed its Parts?](https://www.microsoft.com/en-us/research/uploads/prod/2021/02/does_the_whole_exceed_its_parts-chi21.pdf)
  that explanations can increase overreliance rather than reliably improve judgment;
  this supports showing alternatives, assumptions, confidence, and contrary evidence
  instead of presenting the recommendation as authority.
- [NISTIR 8312](https://doi.org/10.6028/NIST.IR.8312) requires explanations to be
  meaningful to the intended audience and accurate to the system's process, supporting
  the explicit separation of today, proposal, and not-yet-implemented work.
- W3C's [Making Content Usable](https://www.w3.org/TR/coga-usable/) recommends a clear
  purpose, familiar hierarchy, clear words, succinct content, and processes that do not
  rely on memory.
- The GOV.UK Design System recommends
  [one clear question with valid uncertainty answers](https://design-system.service.gov.uk/patterns/question-pages/),
  [reviewable choices before commitment](https://design-system.service.gov.uk/patterns/check-answers/),
  and [an explicit account of what happens next](https://design-system.service.gov.uk/patterns/confirmation-pages/).

## Alternatives considered

- Keep all metadata visible at the top — simple to parse, but forces readers to decode
  lifecycle internals before knowing what they are being asked.
- Use free-form prose with no required comparison structure — visually lighter, but it
  permits hidden recommendations, asymmetric options, and ambiguity about current
  versus proposed behavior.
- Put technical details in a separate sidecar — removes clutter, but splits one action
  across files and weakens the queue's canonical identity.
- Project every unresolved status — comprehensive as a ledger, but presents unavailable
  reviews and already answered actions as human work.

## Consequences

Human reviews become longer only where explanation is necessary and shorter at the
point of action. Agents must write parallel, complete option descriptions and maintain
plain consequence sentences that can be projected verbatim. Reconciler checks must
understand bold-key fields inside the collapsed block and preserve legacy immutable
records through version markers. Technical details remain available on demand without
dominating the rendered page.

Revisit this decision if usability testing shows that zero-context readers still
cannot identify the requested action, present state, recommendation, or consequence of
silence without opening another file.
