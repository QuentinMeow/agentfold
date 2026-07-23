# Handover — publish guardrails PR

**Session:** 2026-07-22 10:12–11:00 PDT, codex
**Task:** 2026-07-22-design-critical-agent-guardrails
**Mode:** async

## What happened

- Verified that the GitHub CLI credential is healthy in macOS Keychain; the apparent
  expiration was caused by restricted keychain access, so no reauthentication was
  needed.
- Committed the user's acknowledgement of the earlier design-review wording, pushed
  the complete local branch, and opened draft PR #4.
- Put five high-impact review questions at the top of the PR summary: obligation tiers,
  assurance profiles, evidence authority, PII sink coverage, and design lifecycle.
- Archived the acknowledged review item by removing it from the live queue after its
  answer was safely recorded in Git history.

## How it works now

Draft PR #4 contains every local commit on the task branch and remains a proposal: it
does not activate guardrail enforcement. GitHub CLI can continue using the existing
keychain credential; commands that need it must run with access outside the restricted
execution environment.

## Decisions made for you

- Published the requested PR as a draft so the unresolved security and lifecycle
  choices are explicit review gates rather than accepted repository policy.

## Needs your attention

- [Risk-tiered guardrails proposal](https://github.com/QuentinMeow/agentfold/blob/task/2026-07-22-design-critical-agent-guardrails/message-queue/needs-human/reviews/risk-tiered-agent-guardrails.md): review the proposed PII/security boundary and the new docs routing contracts. If you do nothing, the design remains proposed and no guardrail implementation begins.
- [Provenance principle wording](https://github.com/QuentinMeow/agentfold/blob/task/2026-07-22-design-critical-agent-guardrails/message-queue/needs-human/reviews/provenance-principle-wording.md): decide whether the five instruction-bearing paths and mandatory human review in autonomous mode are the right trust boundary. If you do nothing, the principle stands as written and mechanical enforcement remains backlog work.

## Dead ends

- `gh auth status` inside the restricted environment reported the keychain credential as
  invalid. Running the same status check plus an authenticated API request with normal
  keychain access succeeded, proving that re-running login would only mask the sandbox
  boundary and was unnecessary.

## Next steps

Review PR #4 using its highlighted checklist. If the design is accepted, record that
decision in an ADR before beginning the proposed staged implementation.

## Deep links

- Task folder: `tasks/4_done/2026-07-22-design-critical-agent-guardrails/` · Worklog: `tasks/4_done/2026-07-22-design-critical-agent-guardrails/worklog.md` · Verification: `tasks/4_done/2026-07-22-design-critical-agent-guardrails/verification.md`
- Pull request: `https://github.com/QuentinMeow/agentfold/pull/4` · Commits: `7fee36b` plus this publication handover commit
