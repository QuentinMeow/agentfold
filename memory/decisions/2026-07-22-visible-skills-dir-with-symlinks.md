# Skills live in a visible skills/ dir; agent dirs are generated symlinks

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** agent
**Description:** skills/ is canonical; install.py symlinks it into .claude/, .cursor/, .agents/; symlinks are git-ignored
**Review-by:** 2027-01-22

## Context

Skills must work across agents (Claude Code reads `.claude/skills/`, Cursor
`.cursor/skills/`, an emerging convention uses `.agents/skills/`) without duplicating
content, and the repo optimizes for human guessability of every top-level name.

## Decision

One canonical, **visible** `skills/` directory. `automation/install.py` creates
relative symlinks from each agent's conventional dir into it; the symlinks and the
dot-dirs are git-ignored (generated, machine-local).

## Alternatives considered

- **Canonical `.agents/skills/`** (source project): follows the emerging dot-dir
  convention but hides a core folder from the browsing human — against the repo's
  guessability-first rule.
- **Committed symlinks**: work on macOS/Linux, break silently on Windows checkouts
  without `core.symlinks`; generating them keeps clones portable.
- **Copies per agent dir**: needs a drift check for self-inflicted duplication.

## Consequences

A fresh clone must run `install.py` before agent-specific skill discovery works —
accepted, and the README quickstart makes it step one. Tools that read `AGENTS.md`
natively work with no install at all.
