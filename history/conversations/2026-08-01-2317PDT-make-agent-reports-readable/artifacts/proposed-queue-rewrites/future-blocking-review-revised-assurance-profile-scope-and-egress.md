# Should a safety report describe only the protection it actually observed, instead of a label someone picked?

**Action:** Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.
**Why this matters:** Whatever gets built has to report the protection it genuinely observed, rather than letting the agent doing the work choose a reassuring label for its own output.
**If you do nothing:** Nothing stops elsewhere; the safety work stays parked at its starting line, the direction you already approved stays on record, and this rewritten version of it is never accepted.

## What you need to know

**Today:** nothing is implemented. You have already approved the shape in principle — each protection is switched on or off individually, and how well-protected something is gets worked out from what is actually switched on. This file is the rewritten design that puts that on paper; it has never been accepted.

**What this would change:** accepting the rewrite. It draws a hard line between the switches you set and the claims a report may make: a report lists, for each rule, the protections it observed and no more. Turning off a human review step does not erase a separately verified automatic gate that is still running, and does not let the report pretend the human step happened. It also states plainly that controlling what leaves the machine is *not* part of this work.

**What this does not decide:** nothing gets built by approving it, and approving does not re-open the direction you already agreed to; changing that would take a separate decision.

For example: one credential rule might be covered by a person reading the change, an automatic check before merging, and another before it reaches a remote server. The report names each separately. Switch off the human step and it drops that one and keeps the other two — it never averages them into one comfortable word. The rewrite is [the guardrail design](../../../docs/designs/risk-tiered-agent-guardrails.md).

## Your choices

The choices differ on whether the rewrite is accepted as it stands, sent back for one named wording repair, or refused.

### Approve
The rewrite becomes the accepted description, and the build task inherits it. The cost is that reports get longer and less quotable: there is no single word for "this is safe", only a list of what was observed.
*Example consequence:* you ask "is the secret-scanning covered?" and get three lines naming which of three gates ran, rather than "yes".

### Request changes
Something reads ambiguously — most likely which switches exist, what counts as observed, or where the boundary around network egress falls. Name it; an agent rewrites that part and brings it back. The cost is another round trip before any building starts.
*Example consequence:* you say "observed" needs a definition, the design comes back with one, and the build task starts a week later.

### Reject
The rewrite is the wrong description of what you approved. It is withdrawn and rewritten from a different starting point, at the cost of losing the work behind it.
*Example consequence:* the design goes back to the drawing board and the safety work stays parked until a version you recognise exists.

## What I recommend

**Recommendation:** Approve — a report that can only say what it observed is the whole point of the direction you already approved, and the alternatives all reintroduce a label somebody chooses.
**Strongest case against this:** a report with no summary line is a report people stop reading. If the practical effect is that nobody can tell at a glance whether a change is protected, the honesty is real but the safety benefit is not.
**Confidence:** low — I am reading the file a previous session wrote rather than the design itself; I confirmed nothing is implemented and that the build task has not started, but I did not check the rewrite against the wording of your original approval.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your review:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-07-24, by codex, from the owner's review of task `2026-07-22-universal-guard-mode-configuration`
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Resolution evidence:** `memory/decisions/2026-07-24-revised-assurance-report-review-disposition.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f
**Reviewed revision:** ______
**Review outcome:** pending
**Supersedes:** `message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md`
**Depends on:** `message-queue/needs-agent/requests/future-blocking-revise-assurance-profile-scope-and-egress.md`
**Answer by:** 2026-10-22
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
