# Desired state

**Last-updated:** 2026-07-24

In priority order. Each line is specific enough to spawn tasks against.

1. **A stranger's agent can work here on first clone.** Boot from `AGENTS.md`, pass the
   reconciler, complete a task end-to-end with no human explanation. *(Largely true —
   needs outside validation.)*
2. **Every schema mechanically enforced.** Each file format in `templates/` has a
   matching reconciler check; drift between a template and its check is itself a
   finding. *(Checks exist for queue, tasks, memory, handover; template↔check drift
   detection does not exist yet.)*
3. **One-command adoption.** An `npx`/`pipx`-style installer that drops the harness
   folders into an existing repo, asks three questions (name, mode, first service), and
   wires the hooks — the claude-code-templates playbook. *(Not started.)*
4. **Per-skill eval canaries.** 3–6 scripted scenarios per skill with expected
   behaviors; behavioral skill edits must pass them before merge. *(Not started.)*
5. **Public/private overlay as a packaged module.** The mirror-structure pattern from
   `handbook/adoption-guide.md` shipped as tooling: mount script + config indirection +
   token-derived leak guard. *(Pattern documented; tooling not started.)*
6. **A queue/task viewer.** Read-only board rendered from the folders (the folders stay
   the source of truth). *(Not started.)*
7. **The harness survives its own design review.** Finding severity tiers so advisory
   drift never blocks commits; automated retry filing with waivers; coordination
   write rules that match practice; a de-minimis path for micro-changes; mechanical
   provenance checks; optional ritual hooks for agent adapters; a core-admission gate
   that rejects personal or provider-specific scope. *(The core-admission gate is
   implemented; six design-review tasks remain in `tasks/0_backlog/`.)*
8. **Critical obligations survive agent forgetfulness and detector failure.** A
   consequence-based policy separates preferences, repairable invariants, required
   deliberation, and critical boundaries; PII/secret controls layer redacted local
   feedback, content-bound evidence, detector canaries, protected exceptions, and
   remote authority where available. Every guard is selected through one `hard`,
   `soft`, `off`, or `manual` configuration surface; starter mechanisms are
   templates, costly agent review is manual by default, and assurance is derived per
   obligation and scope from observed coverage, health, and enforcement rather than
   configured labels. Sandboxing and controlled egress are excluded unless a separate
   design receives explicit human approval.
   *(Human-reviewed design in `docs/designs/risk-tiered-agent-guardrails.md`;
   implementation task `2026-07-22-universal-guard-mode-configuration` filed but not
   started.)*
