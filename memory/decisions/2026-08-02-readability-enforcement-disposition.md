# Structural readability rules become advisory findings, not commit gates

**Status:** decided
**Date:** 2026-08-02
**Decided-by:** owner (Quentin, in chat, transcribed into the queue item before this record was written)
**Description:** The reconciler reports the machine-visible readability rules — pull-request section presence and order, a missing example consequence on a choice, an out-of-range summary length — as advisory findings that print and are counted but never fail a commit
**Review-by:** 2027-02-02

## Context

`skills/explain-to-human/` is prose. Nothing stopped an agent from ignoring the whole
standard, so the quality of a message depended on which agent wrote it. Two rules near the
standard were already machine-checked — a pull-request body must list the owner's open
items with a real link each, and a queue item must stay under 700 words before its answer
line — and everything else was enforced only by a person noticing.

Some of the remaining rules have a shape a program can see: whether the pull-request
sections are present and in order, whether every choice ends with an example consequence,
whether a summary has three to six items. Others do not: whether an explanation is clear,
whether a counter-argument is real or hedged.

The owner was shown three dispositions — leave it to review, advisory checks on the
structural rules, or blocking checks on them — in
`message-queue/needs-human/decisions/non-blocking-check-the-readability-rules-or-leave-them-to-review.md`
(deleted by the commit that folded this answer; recover it from Git history). The agent
recommended the middle option.

## Decision

Option B. The structural readability rules become **advisory** reconciler findings.

The owner's answer, transcribed from chat: *"I want option B."* — given as the whole
response to that item, naming the option by its letter.

How that was read, concretely: the reconciler grows a check whose findings print with the
`(advisory)` marker and are counted separately, exactly like the existing age-driven
advisory ids. A violation never exits 1, so it never fails a commit or a pre-commit hook.
`--fail-on-advisory` still opts a maintenance run into failing on them, because that flag
is a property of the severity tier and not of any one check.

This decides the enforcement level only. It does not decide the rules themselves — whether
the standard is right is a separate question — and it does not promote any semantic rule
into a check.

## Alternatives considered

- **Option A — leave it to review.** Lost because it leaves the agent that broke a rule
  with no signal at all; the owner finds out by opening a bad body.
- **Option C — blocking checks.** Lost because the checks can see the shape and not the
  intent: an example consequence reading `none` passes, and correct-but-unusual messages
  get refused. It also trains agents to write for the checker.

The recorded case against B, which the owner accepted: advisory findings in this repository
are ignorable by construction, so B may buy little over A while costing a checker to build
and maintain.

## Consequences

- One new advisory check id enters `CHECKS` in `automation/reconcile/reconcile.py` and
  `ADVISORY_CHECKS` alongside `memory-expiry`, `roadmap-fresh`, `stale-queue`, and
  `stale-task`. That set is no longer purely age-driven, so `automation/AGENTS.md`'s
  description of the tier has to stop saying it is.
- `docs/designs/explaining-work-to-the-owner.md` said mechanical enforcement was rejected
  *for now*, with the note that a rule found to have a structural proxy becomes its own
  task. This is that task; the design's alternatives section now points here.
- The rule is put in front of the agent that broke it, and nothing stops an agent that
  ignores it. Occasional bad bodies remain reachable, which was stated in the question and
  is part of what was chosen.
- What would trigger revisiting: evidence that agents ignore the advisory line often enough
  that the owner still reads unusable messages. That is a measurement nobody has taken —
  the size of the problem was unmeasured when this was decided, and the honest exit
  condition is to measure it rather than to escalate on impression.
