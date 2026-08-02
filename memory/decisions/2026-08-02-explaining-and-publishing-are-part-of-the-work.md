# Explaining the work and publishing it are part of doing it, not extras

**Status:** decided
**Date:** 2026-08-02
**Decided-by:** agent (delegated by the owner in chat; two-way door — deleting one skill folder and reverting two ritual steps restores the previous behaviour)
**Description:** One skill states how to write anything a human reads, and every task now ends by opening its pull request and reporting what changed, what was decided, and what the owner owes
**Review-by:** 2027-01-29

## Context

This repository is built so that agents do effectively all the work and the human acts as a
manager: they read what was produced, approve or redirect it, and answer the questions only
they can answer. That division only works if the reports are good enough to decide from.

They were not. Three failures recurred across every human-facing surface. Reports described
mechanism ("`resolve_queue` now calls `freeze`") to a reader who cannot see either function.
Nothing was layered, so the decision sat wherever the agent happened to write it. And
decision files linked four other files instead of carrying the effect the owner needed to
choose. The rules that would have prevented each were spread across four documents that each
owned one surface, and none of them stated the craft all four need.

Separately, the end-of-session ritual listed six things to write and never said to publish
the branch or to tell anyone what happened. A finished task could sit unpushed and
unexplained indefinitely.

## Decision

Two things, both stated once and linked from everywhere else.

**One skill owns the craft.** `skills/explain-to-human/` states the rules that hold on every
surface — three layers, effect over mechanism, before and after, glossed jargon, one worked
example, calibrated uncertainty, self-contained on the decision and linked on the evidence —
and routes to one scenario file per surface: pull-request body, chat reply, human queue item,
handover. The scenario files restate no schema; `templates/` still owns the fields.

**Publishing and reporting end every task.** The ritual in the root `AGENTS.md` and in
`skills/session-handover/` now has two more steps: push the branch and open its pull request,
then close the session with a reply in the shape the chat-reply scenario defines. The reply
originates nothing — every open item in it projects a queue file that already exists.

Supporting this: `templates/pull-request.md` gives a pull-request body one schema, projected
into `.github/pull_request_template.md`; and `handbook/human-action-guide.md`,
`message-queue/AGENTS.md`, and `handbook/decision-guide.md` were rewritten to obey the rules
they had been stating.

## Alternatives considered

- **Four skills, one per surface** — lost because it restates the craft four times, which
  the single-source-of-truth guardrail forbids and which drifts on the first change.
- **Put the rules in the root `AGENTS.md`** — lost because that file is read in full by every
  agent on every boot, and this material is needed at one moment in a session.
- **Enforce readability mechanically** — lost for now because the available proxies are weak
  enough that a body can satisfy every one and still be unreadable, and a check that can be
  satisfied without achieving its goal trains agents to satisfy the check. Whether any of it
  should become checked is filed as a decision for the owner rather than assumed.
- **A single exemplar instead of rules** — lost because an exemplar cannot say why a choice
  was made, so an agent facing an uncovered case has nothing to reason from. Both are shipped
  instead: rules, plus worked examples in every scenario file.

## Consequences

Every human-facing artifact from now on is written to a stated standard, and a message that
fails is a defect that can be pointed at a rule rather than a matter of taste.

Nothing here is machine-checked. An agent that skips the skill produces exactly what the
repository produced before, and no check catches it — the standard's only enforcement is
review and the owner noticing.

Revisit if the owner reports still having to ask what a message means, or if a specific rule
turns out to have a structural proxy a check could hold. The first would mean the rules are
wrong; the second would move that rule out of prose and into `automation/`.
