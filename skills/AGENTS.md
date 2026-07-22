# skills/ — portable skills

One folder per skill; `SKILL.md` is the entry point. Skills are **agent-agnostic
protocols** written in plain markdown — no tool-specific syntax — so Claude Code,
Cursor, Codex, or a human can follow them. Agent-specific discovery dirs
(`.claude/skills/`, `.cursor/skills/`, `.agents/skills/`) are git-ignored symlinks
created by `automation/install.py`; edit only here (ADR:
`memory/decisions/2026-07-22-visible-skills-dir-with-symlinks.md`).

## SKILL.md header (YAML — the one external-convention exception to bold-key metadata)

```yaml
---
name: <slug, must equal the folder name>
description: <what it does + "Use when …" trigger phrases>
---
```

## Layout inside a skill

`SKILL.md` (short, routine path first) → optional `reference.md` (depth, linked from
SKILL.md) → optional `scripts/` (self-contained; never imports from outside the skill).

## The shipped skills

| Skill | Use when |
|-------|----------|
| `ask-me-anything/` | anyone asks how AgentFold works or where something lives |
| `session-handover/` | ending any session that did work |
| `adversarial-review/` | a merge or claim needs a trustworthy verdict |
| `memory-gardener/` | reconciler reports overdue memory, or on a maintenance pass |
| `github-auth-guard/` | `gh` authentication fails or an agent considers reauthentication |
