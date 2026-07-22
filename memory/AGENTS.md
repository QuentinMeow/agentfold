# memory/ — long-term project memory

What the project must not forget, in four zones — plus a hard rule that memory expires
(`handbook/principles/design-for-forgetting.md`). Schemas: `templates/memory/`.

| Zone | Contents | Read when | Written when |
|------|----------|-----------|--------------|
| `facts/` | durable constraints & context not derivable from code or git | task touches the fact's area (via `index.md`) | a non-obvious truth surfaces |
| `decisions/` | ADRs — what was decided, alternatives, consequences | before revisiting any settled question | every decision fold-in; significant agent calls |
| `lessons/<area>/` | what failure taught us, by area | **only** when working in that area (boot sequence rule) | a failure's root cause is understood |
| `known-issues/` | reproducible problems we've accepted or not yet fixed | before debugging anything that smells familiar | a bug is understood but not fixed now |

## Rules

- `index.md` is **generated** — one line per entry from each file's `**Description:**`
  field. Rebuild with `python3 automation/reconcile/reconcile.py --fix-index`; never
  hand-edit.
- Every entry carries `**Review-by:**` (defaults are set by each template — the only
  home of that number). Stagger dates a few weeks when writing several entries at
  once, so reviews don't all come due together. Overdue entries become reconciler
  findings; the `skills/memory-gardener/` pass re-verifies, compacts, or deletes.
- **Merge before adding**: search the zone for an existing entry about the same
  subject; update it instead of duplicating.
- ADRs are immutable: reversal = new ADR + `**Superseded-by:**` link on the old one.
  All other zones are freely editable — they state *current* truth, and git remembers.
- Lessons stay scoped. If a lesson applies everywhere, it doesn't belong here — promote
  it into the relevant `AGENTS.md` and delete the lesson file (one home per fact).
- Everything here is plain markdown so any agent, human, or grep can read it.
