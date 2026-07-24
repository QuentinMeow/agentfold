# Detector failures remain distinct from clean results and findings

**Status:** decided
**Date:** 2026-07-24
**Decided-by:** human (revision-bound review recorded in commit 487d640)
**Description:** Detector failures and incomplete coverage remain explicit result states; guard mode controls the transition response without relabeling the evidence
**Review-by:** 2027-01-20

## Context

The guardrail design distinguishes a detector finding from incomplete coverage,
runtime failure, and a clean result. The owner reviewed the detector-state question
against `docs/designs/risk-tiered-agent-guardrails.md` at
`sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f`
and answered “partially reviewed, mostly correct, continue.” The queue lifecycle
records that narrow disposition as approval of this question only; it does not approve
the other guardrail reviews or PR #7.

## Decision

Incomplete coverage and detector runtime errors remain explicit result states. They
must not be reported as either clean evidence or a prohibited-content finding. A
configured guard mode may determine whether work blocks, reports and continues, waits
for manual invocation, or skips an off guard, but it does not rewrite the detector's
observed result.

## Alternatives considered

- Collapse detector failure into a finding — rejected because it claims prohibited
  content was detected when the detector instead failed to produce complete evidence.
- Collapse detector failure into clean — rejected because an outage would silently
  become positive safety evidence.
- Treat this response as approval of the whole guardrail proposal — rejected because
  the owner explicitly described the review as partial and answered only this queue
  item's detector-state question.

## Consequences

The universal guard-mode implementation must preserve distinct clean, finding,
incomplete-coverage, runtime-error, and not-applicable evidence where relevant. This
review item remains live in `folding` state until that task actually crosses its start
boundary; the other guardrail review items remain independent prerequisites.
