# Design notes — Make the message queue the first-class interaction surface

**Status:** decided

## Problem

PR #4 asked the owner to judge terms such as “assurance profile,” “template-first,”
and several security evidence roles without explaining their differences or linking
each question to its source. Those asks existed only in the PR body after the original
generic queue review had been resolved. Current contracts require surfaced queue items
to appear in replies, but do not require the converse: every human ask to originate as
a queue item.

History explains the phrasing, but does not excuse it. The agent compressed its own
end-of-design audit into reviewer prompts: one prompt was actually a consistency check
the agent should have completed itself, while the others assumed the reader already
knew vocabulary introduced deep in the design. Optimizing the PR body for a short
reviewer checklist erased the alternatives, concrete consequences, and source pointers.
Because the generic queue review was already closed, treating GitHub as a separate
discussion channel also let those new asks bypass the queue entirely.

## Options considered

### Option A — Improve prose only

Tell agents to write clearer questions while leaving PRs and chat as independent action
channels. This is cheap but another agent can still omit context or lose the ask.

### Option B — Prefix queue files only

Add visible delivery prefixes without changing ask ownership. This improves scanning,
but an excellent filename cannot help when the question never enters the queue.

### Option C — Queue-owned actions with channel projections

Make one live queue file own each pending action. Other channels may summarize and link
it, while templates require a distinction, example, unattended outcome, and full-context
pointer. Enforce delivery prefixes and structural contradictions mechanically.

## Chosen

Option C. It addresses both failures: discoverability in filenames and lossless
delivery across PR, chat, task, and agent-session boundaries.

The path encodes three independent properties: who acts next in the actor folder, what
kind of action it is in the leaf folder, and when it blocks in the filename prefix.
`blocking-*` stops a named boundary now; `future-blocking-*` stops only at a named future
date, event, or transition; `non-blocking-*` never stops work and names the safe
unattended outcome. The filename is canonical, so no `Blocking` field can drift.

PRs, issues, chat, tasks, and handovers are projections. They may summarize and link a
live queue item, but cannot originate a pending durable action. A task declares its
live queue actions explicitly. `2_blocked` broadens from human decisions to any
reciprocally linked `blocking-*` human or agent dependency; a task stays in progress
while an active agent is repairing that dependency.

Human messages compare meaningful dispositions, show a concrete example, state the
unattended result, and link the durable source. This structure constrains delivery and
evidence, not how a future agent completes the work.

## Hardening after independent review

The first adversarial pass found that authority also requires conservative parsing and
portable adoption:

- Queue evidence is read from visible CommonMark, never fenced examples or HTML
  comments; angle-bracket link destinations preserve valid paths containing spaces.
- Standard message leaves have specialized schemas, while any repository may add a
  one-level typed leaf that inherits the actor's generic schema.
- Handover projection enforcement activates from a repository-local schema and exact
  legacy folder, not an AgentFold calendar date.
- Unclaimed backlog tasks have reciprocal, explicitly typed non-blocking pickup
  messages; ordinary follow-up requests may still link active tasks.
  Task status enforces start/review/complete boundaries; Git admission names external
  boundaries such as merge and scopes them to the task being admitted. A blocking task
  remains in progress only after a committed agent repair or answered-action folding
  claim proves that work is active.
- A review is unanswerable while its artifact is pending. A waiting review binds to
  exact file bytes or full Git object ids, and the response repeats that revision;
  mutable PR URLs remain navigation only.
- Every newly added handover must exactly project the complete live human queue.
  Post-activation human entries copy `Action`, `Why-you-might-care`, and
  `If-you-do-nothing` from the creation snapshot; agent entries are Action-labeled
  links only. Both repository-local schema markers are sticky, while pre-marker and
  later-resolved records remain immutable history.
- Reconciler retries aggregate by full check/subject identity, use collision-safe names,
  and refresh a marked machine projection without overwriting actor status or notes.
- Queue resolution is a Git-backed lifecycle, not a status label: the first concrete
  human response is immutable. A counter-question is folded into durable evidence and
  continued in a new same-timing item that names its predecessor; agents never rewrite
  human text. An answered/open item is claimed separately; ordinary deletion changes predeclared
  evidence files and approved reviews revalidate the exact target. Requested changes
  leave a same-boundary agent repair plus a dependent artifact-pending human re-review;
  approval/rejection/abandonment forbid either successor. An
  unanswered stale binding retracts to pending before a separate republication. Pickup
  and generated-retry exceptions prove their own state transitions, and activation
  cannot be removed to disable history checks. A governed v1 handover path has one
  immutable incarnation; deletion is allowed, but correction or parallel re-entry uses
  a new conversation path.
- Force-ref admission names the displaced old tip explicitly, so continuity compares it
  with the new range head without treating ordinary PR divergence as a force push.
  Whole queue-service removal remains modular only when its edge erases no live action.
- External action prose crosses a provider-neutral projection gate. Outbound task PR
  descriptions require immutable task-scope evidence and project every `needs-human`
  action in `Queue actions`; inbound review sources project only the `needs-agent`
  actions carried by that surface; issues and
  conversation comments may link either actor because the path owns direction. Allowed
  absolute links bind to an adapter-supplied immutable prefix. A provider assignment
  requires a distinct actor-correct queue item whose opaque binding preserves provider,
  role, actor kind, and identity; body headings are classified as visible prose. When
  provider prose cannot be edited by the receiving agent, one or more queue items may
  instead copy its exact opaque, versioned `External source` binding. Those items stay
  live while the source remains effective; an edit changes identity, a superseding or
  dismissed formal review removes the old source, and resolving a diff thread removes
  that source. GitHub routes every non-empty `COMMENTED` formal review as agent triage
  rather than making English classification a prerequisite; that triage may be
  non-blocking. Changes-requested reviews and unresolved threads remain forced action
  state, while approval prose uses the ordinary classifier. This binding proves routing
  and version continuity, not semantic
  completeness of an agent-authored transcription; artifact review owns that judgment.
  GitHub's default/base context makes PR-description, issue, conversation, and
  PR-update review-state checks authoritative. A candidate-context job also replays
  current formal reviews and unresolved diff threads on direct events and every PR
  update, preventing an unrelated push from clearing a failure. GitHub has no
  target-context review event, so hostile direct-event tampering still requires a
  separately controlled provider gate.

The live queue owns unresolved delivery state even though its background stays
elsewhere. The correcting ADR is
`memory/decisions/2026-07-23-unresolved-queue-delivery-state-is-not-regenerable.md`.

Accepted decision:
`memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`.

Refined actor-correct resolution lifecycle:
`memory/decisions/2026-07-23-requested-review-changes-route-through-agent-repair.md`.

## Core fit

**Agent substitution:** pass — files, links, and deterministic checks work with any agent runtime
**Provider substitution:** pass — any provider can forward branch, immutable diff, and reached-transition context into the canonical local reconciler
**Repository substitution:** pass — any adopted repository needs durable human and agent action routing
**User-global writes:** none
**Why AgentFold core:** interaction delivery is a framework lifecycle concern, not personal configuration or product behavior
**Thin adapter:** canonical=automation/check_action_projection.py; optional=yes; policy=none; writes=repo-only

The registered `.github/` adapter only maps GitHub event/API context into those
canonical gates; it owns no queue policy, uses an ephemeral workflow token rather than
developer authentication, never executes candidate files from trusted target context,
and does not claim that a candidate-context review-event run resists hostile workflow
tampering.
