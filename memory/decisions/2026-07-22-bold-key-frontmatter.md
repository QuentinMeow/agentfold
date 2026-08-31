# Frontmatter is bold-key markdown lines, not YAML

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** agent
**Description:** All item metadata uses `**Key:** value` lines; renders on GitHub, parses with one stdlib regex
**Review-by:** 2027-02-21
**Amended-by:** `memory/decisions/2026-08-18-bold-key-metadata-stays-on-corrected-grounds.md` — the "invisible on rendered GitHub pages" premise under Alternatives considered, and the "Renders as readable bold text everywhere markdown renders" clause under Consequences

## Context

Queue items, tasks, and memory entries need machine-checkable metadata, and the
reconciler must run with zero dependencies (Python stdlib has no YAML parser).

## Decision

Metadata is bold-key lines at the top of each file — `**Status:** decided` — parsed by
the reconciler with a single regex (`^\*\*(Key):\*\*\s*(value)$`). Templates define
which keys each file type requires.

## Alternatives considered

- **YAML frontmatter** (`---` blocks): the ecosystem convention (SKILL.md, Jekyll), but
  invisible on rendered GitHub pages, needs PyYAML or a fragile hand parser, and
  tempts nested structures that don't belong in prose files. Kept only where an
  external convention demands it (`SKILL.md` headers).
- **JSON sidecars**: two files per item breaks "one item, one file".

## Consequences

Metadata stays flat key→string by design — anything needing structure belongs in the
body or a real data file. Renders as readable bold text everywhere markdown renders.
