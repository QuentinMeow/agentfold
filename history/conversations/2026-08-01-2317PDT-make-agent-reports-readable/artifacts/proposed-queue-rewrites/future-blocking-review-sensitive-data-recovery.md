# If a secret has already leaked, does this plan for cleaning it up cover everything it should?

**Action:** Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.
**Why this matters:** Deleting the file that leaked a password does not un-leak it — copies survive in clones, forks, build logs, and caches you do not control.
**If you do nothing:** Nothing stops elsewhere, but the safety work stays parked at its starting line and this cleanup procedure stays a proposal nobody must follow.

## What you need to know

**Today:** nothing is implemented and no cleanup procedure is in force. If a credential leaked right now, what happened next would be whatever whoever noticed it decided to do. The task that would build this has not started.

**What this would change:** the design fixes two things. First, a boundary: stopping something getting out, permitting one narrow exception in advance, and cleaning up afterwards are three different activities, and cleanup never retroactively makes the first one have worked. Second, an order. A leaked credential is replaced *first*, before anyone tidies the history, and a test is added so the same leak is caught next time. Leaked personal data goes the other way: cut off access and write down every place it could have reached before deleting anything, because deleting first destroys the evidence of where it went.

**What this does not decide:** what counts as sensitive, and when any of this gets built. Approving does not start implementation.

Concretely: once an API key reaches a shared server, a commit deleting the file is not the fix. The key gets replaced, and only then does anyone search clones, forks, build logs, artifacts, mirrors, and caches. Rewriting history is one step of that, not the whole of it. The proposal is [the guardrail design](../../../docs/designs/risk-tiered-agent-guardrails.md), in its section on exceptions and recovery.

## Your choices

The choices differ on whether this cleanup boundary and its ordering are accepted as written, sent back because something is missing, or refused.

### Approve
The sequence becomes the accepted procedure and the build task inherits it. The cost is that it is deliberately heavy: any leak triggers a full sweep, which is slow and often finds nothing.
*Example consequence:* a test key with no real access leaks, and the procedure still asks for a replacement and a sweep before anyone calls it closed.

### Request changes
The shape is right but something is missing — a place data hides that is not listed, or a step in the wrong order. Name it; an agent repairs the design and brings it back, at the cost of a round trip before anything is built.
*Example consequence:* you point out that nobody checks the chat history where agents paste output, that gets added, and every future sweep is one step longer.

### Reject
Cleanup should not be specified here at all, or separating it from prevention is the wrong idea. The design restarts from a different premise, losing the work behind it.
*Example consequence:* leaks are handled ad hoc — fast when whoever is handling one knows what they are doing, unreliable when they do not.

## What I recommend

**Recommendation:** Approve — the ordering is what people get wrong under pressure, and "replace the credential before you tidy anything" is worth writing down before it is needed.
**Strongest case against this:** a procedure nothing enforces is just a document, and leaks happen at the worst moment, when whoever is there follows instinct rather than a file. If it will not be read in the moment, approving it buys the feeling of coverage without the coverage.
**Confidence:** low — I am reading a file a previous session wrote rather than the design itself; I confirmed nothing is implemented and the build task has not started, but did not check the recovery list against external incident-response guidance.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your review:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Resolution evidence:** `memory/decisions/2026-07-23-sensitive-data-recovery-review-disposition.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f
**Reviewed revision:** ______
**Review outcome:** pending
**Answer by:** 2026-10-21
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
