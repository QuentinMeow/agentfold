---
name: adversarial-review
description: Get a trustworthy verdict on a change by majority vote of independent adversarial reviewers. Use before merging in autonomous mode, for one-way-door changes in async mode, or whenever a single agent's judgment isn't enough.
---

# Adversarial review

One agent's approval is one sample. This protocol takes N independent samples and
trusts the majority (`handbook/principles/majority-over-single-agent.md`).

## Protocol

1. **Panel**: spawn 3 reviewers (5 for one-way doors), each with **fresh context** —
   they see the diff, the task's `task.md`/`plan.md`, and nothing of each other or of
   the author's self-assessment.
2. **Distinct lenses**, one per reviewer, e.g.: *correctness* (find an input where this
   breaks), *contract* (does it match plan and acceptance criteria; did it restate a
   schema instead of linking), *blast radius* (what else could this affect; is it
   reversible). Never the same prompt N times.
3. **Adversarial framing**: instruct each to *refute* — report only findings with a
   concrete failure scenario. No style opinions, no praise, no severity inflation;
   "I couldn't break it" is a valid, useful verdict.
4. **Verdicts**: each returns `approve` or `block` + findings. Majority decides.
   - approve-majority with deferred repair → file each pending agent action in
     `message-queue/needs-agent/`; tasks and known-issues may record and link it.
   - block-majority → back to `1_in-progress`; if repair survives this session, file a
     live agent item that names the blocked merge or transition.
   - split → file a human review item with all verdicts and evidence linked.
5. **Record**: one line per verdict in the task's `verification.md` (who, lens,
   verdict) — the merge gate's audit trail, whose shape `templates/task/verification.md`
   owns. Every lens other than `core-fit` writes its verdict as a code span —
   `` `approve` `` — because a bare one reads as a new human ask and refuses the commit.
   A `core-fit` line is never decorated: inside the receipt that refuses it, and outside
   it belongs in the fenced transcript of the panel it came from.
   Records and external review surfaces are projections; every still-pending action links
   its live queue item.

## Queue discipline

Use `templates/queue/` and `message-queue/AGENTS.md`, never an improvised schema; that
contract owns the delivery prefixes and what each one means. A human review must explain
how the verdicts or choices differ, give a concrete consequence, state the safe
unattended result (normally do not merge), and link the diff, task, and complete
evidence. The queue is canonical for pending human and durable cross-session agent
actions; other tools project it.

## Costs and calibration

A panel costs ~3× a solo review — reserve it for the merge gates listed in
`handbook/collaboration-modes.md`, not typo fixes. If panels approve >95% over time,
the lenses have gone soft; sharpen the refute framing.
