# Desired state

**Last-updated:** 2026-07-22

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
