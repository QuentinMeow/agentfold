# Optional agent-adapter hooks that re-arm the rituals

**Claimed-by:** unclaimed
**Filed:** 2026-07-22, by claude (design review; owner directed in chat — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Parent:** none

## Goal

The boot ritual and the end-of-session ritual are the two least-enforced parts of
the harness, and research says they sit exactly where compliance decays: adherence
drops ~5.6% per step within a session, skills silently fail to trigger in half of
cases, and context compaction measurably erases prompted constraints. Apply
systems-over-instructions to the rituals themselves: extend `automation/install.py`
to optionally install per-agent hooks — for Claude Code, a SessionStart hook that
prints the message-queue ritual state (open queue counts, oldest items) and a Stop
hook that warns when the session touched `tasks/` but no conversation folder exists.
Keep the core agent-agnostic: hooks are adapters like the existing symlinks, other
agents get parity as their hook surfaces allow, and nothing in the harness may
*require* them.

## Acceptance criteria

- [ ] `python3 automation/install.py` (or an opt-in flag) installs working hooks for
      at least one agent, demonstrated with real output in `verification.md`
- [ ] A session in a hook-less agent still works exactly as today
- [ ] The hooks read repo state only — no duplicated rule text (single source of
      truth: they point at the ritual in the root `AGENTS.md`, never restate it)

## Links

- Design review, Part 2 (rituals sit where compliance decays): `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
