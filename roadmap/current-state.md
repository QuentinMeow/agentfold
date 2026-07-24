# Current state

**Last-updated:** 2026-07-24

What is true today, mapped to the desired-state lines.

- **Structure**: all eleven top-level folders exist and follow their own contracts;
  `docs/designs/` holds durable proposals separately from principles and ADRs; the
  bootstrap task (`2026-07-22-bootstrap-the-harness`, in `tasks/4_done/`) is the worked
  example of the full lifecycle.
- **Enforcement**: `automation/reconcile/reconcile.py` checks queue/task/memory/handover
  schemas, queue timing names/fields, task↔queue links, new handover projections, link
  targets, line budgets (AGENTS.md, SKILL.md, root README), memory expiry, and
  dependency-aware stale items. Visible CommonMark is the evidence boundary; task
  admission rechecks every post-activation Git edge and task-local Markdown artifact
  for named transitions and newly introduced human asks. Queue deletion is bound to
  claims, distinct evidence, still-crossed task/merge receipts, withdrawn negative targets,
  displaced-ref continuity, and checked pickup/retry exceptions. UTC dates are checked;
  arbitrary event/transition/operation evidence is agent-attested unless an adapter
  validates the boundary. Empty
  queue-service removal remains modular but cannot erase a live action. It files
  collision-safe, aggregated retry projections while preserving actor notes. A separate
  Git boundary gate requires
  substitution evidence for core diffs and rejects obvious user-global access in
  tracked executables. Its token-expensive independent review mode is manually invoked
  outside the gate; `--require-review` validates a revision-bound receipt, while
  pre-commit and CI report that the manual review was not invoked by default. They still
  run repository tests across services, skills, and automation. A provider-neutral
  external-action gate binds PR prose to an immutable candidate, makes each declared
  action entry link one live human queue item, and rejects action-like prose outside
  that section. Provider sources always retain an actor-correct version binding even
  when their prose directly links the queue; the GitHub workflow is a thin event
  adapter. No template↔check drift detection yet.
- **Skills**: four portable skills ship (`ask-me-anything`, `session-handover`,
  `adversarial-review`, `memory-gardener`) as agent-agnostic SKILL.md protocols; the
  gardener is a protocol only — no script yet. Each treats the message queue as the
  canonical action surface and external prose as a linked projection.
- **Coordination**: every pending human action and durable cross-session agent action
  has one canonical queue file. Actor and message kind remain folder routes; filename
  prefixes expose blocking now, blocking at a future boundary, or never blocking.
  Tasks declare live queue actions, every unclaimed backlog task has an agent pickup
  message, and human items mechanically require differences, a concrete example, an
  unattended/boundary outcome, and a full-context pointer. Reviews cannot accept a
  response before their exact artifact exists. The superseded branch-local PR #7
  continuation action was claimed and retired during stacked-history preparation; the
  canonical main action owns the remaining review and exact-receipt work.
- **Example code**: `services/quote-api` + `services/quote-cli`, stdlib-only, tested,
  cross-linked contracts.
- **Design review (2026-07-22)**: a full grill of the harness — report in
  `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md` —
  found the eventual-consistency-vs-blocking-gate contradiction plus honesty and
  wording gaps. Wording gaps fixed on main; a ninth principle
  (`handbook/principles/provenance-over-position.md`) added; six hardening tasks
  filed in the backlog (desired-state line 7).
- **Guardrail proposal review (2026-07-22)**: the owner approved the provenance
  principle wording and narrowed the critical-obligations proposal to template-first,
  universally mode-configurable guards (`hard`, `soft`, `off`, `manual`);
  independent-agent review is manual by default and sandboxing is deferred. On
  2026-07-23 the owner confirmed the four universal semantics; the proposal now defines
  composable guard bindings, derived assurance reports per obligation and scope,
  template-first adoption, evidence authority, detector failure, and incident recovery
  with separate examples. Controlled egress is reference-only and requires a separate
  explicitly approved design.
- **Not yet real**: one-command adoption installer, eval canaries, packaged
  public/private overlay, queue viewer, design-review hardening — see
  `desired-state.md` lines 3–8.
