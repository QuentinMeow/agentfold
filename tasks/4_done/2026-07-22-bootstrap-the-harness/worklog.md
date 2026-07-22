# Worklog — bootstrap

Append-only; newest at the bottom.

## 2026-07-22 — bootstrap session (claude)

- Fanned out two research subagents: one deep-read of the source project's harness,
  one public prior-art survey with name-availability checks. Both reports folded into
  `design.md` and the ADRs.
- Chose the name **AgentFold** and the who-acts-next queue naming; recorded all
  significant calls as ADRs in `memory/decisions/` rather than filing decisions,
  since the owner delegated these calls explicitly.
- Built the full tree in one pass (plan steps 3–13), templates first-class as the
  single source of truth for every schema.
- Wrote the reconciler with a plain-dict check registry so adopters can delete checks
  for folders they haven't adopted.
- Ran installer, reconciler, and service tests; recorded real output in
  `verification.md`. Left the initial git commit to the owner.

## 2026-07-22 — publish session (claude)

- Owner flagged the bare `1500` conversation timestamp; convention changed to local
  time + timezone abbreviation (ADR:
  `memory/decisions/2026-07-22-conversation-timestamps-local-time.md`), folder renamed
  to `2026-07-22-0014PDT-bootstrap-the-harness`, validator regex updated.
- Created the GitHub repo `agentfold` (public, MIT) and opened the bootstrap PR at the
  owner's request.
