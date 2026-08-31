# May the published recovery code be sent to Claude for one independent review?

**Action:** Choose whether to authorize sending the published recovery code and diffs to Claude for one read-only review, or accept the five native reviews without that additional check.
**Why this matters:** Sending repository code to another service adds a recipient, and that disclosure cannot be undone by deleting a local file.
**If you do nothing:** No code is sent to Claude; the two prepared PRs remain available with their native reviews and passing checks.

## What you need to know

**Today:** Five independent native reviewers examined the recovery. The separate Claude review has not run because the execution security check refused the proposed transmission.
**What this would change:** One additional reviewer from another vendor would receive the published candidate code, diffs, repository contracts, and review criteria.
**What this does not decide:** This grants no permission to send ignored files, local uncommitted changes, credentials, or personal configuration, and no permission to merge either PR.

The requested agent-orchestration skill includes a cross-vendor refuter: a second service independently tries to find defects. Its attempted launcher was rejected before Claude started. The current disclosure limit is recorded separately from the completed local and GitHub checks.

> Running Claude with repository review inputs can transmit private code and diffs to an external, untrusted service; the user authorized PR research but did not authorize this specific sensitive payload to Claude.
>
> — [The execution check’s recorded refusal](../../../memory/facts/external-recovery-review-remains-unexecuted.md#execution-refusal)

## Your choices

The choice is whether the extra independent review is worth sending the published code to another service.

### Option A — Authorize the additional review
Claude receives only the published recovery candidates and their review inputs. Its available tools are restricted to reading and searching; the agent cannot edit or publish through that review session. This still sends code outside the existing service.
*Example consequence:* Claude may identify a bug missed by the native panel; an agent repairs it and reruns the affected checks before reporting the additional review complete.

### Option B — Keep the completed native review only
No code is transmitted to Claude. The existing five-lens review and tests remain the evidence for the prepared PRs, with the missing cross-vendor check disclosed.
*Example consequence:* The PRs stay available, but a blind spot shared by the native reviewers receives no second-vendor challenge.

## What I recommend

**Recommendation:** Option B — Keep the completed native review only — the available reviewers reproduced defects, the repairs have regression coverage, and a new disclosure is not necessary to keep the PRs available.
**Strongest case against this:** A different vendor may find a defect that reviewers using the same model family all miss.
**Confidence:** medium — the native reviews and actual candidate checks are recorded; no independent Claude result exists.

Answer in plain words — one sentence is enough. If this page does not give enough information, say what is missing.

**Your answer:** ______

## For the record

<details>
<summary>For the record — bookkeeping the reconciler reads. Nothing here needs you.</summary>

**Status:** waiting  
**Filed:** 2026-08-31, by codex, from task `2026-08-30-rebuild-the-open-pr-stack`  
**Full context:** `memory/facts/external-recovery-review-remains-unexecuted.md`  
**Resolution evidence:** `memory/facts/external-recovery-review-remains-unexecuted.md`  
**Answer by:** 2026-11-29  
**Blocks now:** operation:external-recovery-code-review  

</details>
