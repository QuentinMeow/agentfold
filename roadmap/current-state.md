# Current state

**Last-updated:** 2026-07-22

What is true today, mapped to the desired-state lines.

- **Structure**: all eleven top-level folders exist and follow their own contracts;
  `docs/designs/` holds durable proposals separately from principles and ADRs; the
  bootstrap task (`2026-07-22-bootstrap-the-harness`, in `tasks/4_done/`) is the worked
  example of the full lifecycle.
- **Enforcement**: `automation/reconcile/reconcile.py` checks queue/task/memory/handover
  schemas, link targets, line budgets (AGENTS.md, SKILL.md, root README), memory
  expiry, and stale items; it
  files and garbage-collects retry-queue items. Installed as pre-commit hook and CI
  (`.github/workflows/harness.yml`). No template↔check drift detection yet.
- **Skills**: four portable skills ship (`ask-me-anything`, `session-handover`,
  `adversarial-review`, `memory-gardener`) as agent-agnostic SKILL.md protocols; the
  gardener is a protocol only — no script yet.
- **Example code**: `services/quote-api` + `services/quote-cli`, stdlib-only, tested,
  cross-linked contracts.
- **Design review (2026-07-22)**: a full grill of the harness — report in
  `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md` —
  found the eventual-consistency-vs-blocking-gate contradiction plus honesty and
  wording gaps. Wording gaps fixed on main; a ninth principle
  (`handbook/principles/provenance-over-position.md`) added; six hardening tasks
  filed in the backlog (desired-state line 7).
- **Not yet real**: one-command adoption installer, eval canaries, packaged
  public/private overlay, queue viewer, design-review hardening — see
  `desired-state.md` lines 3–8.
