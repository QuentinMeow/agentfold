# Make the reconciler report its own failures honestly

**Claimed-by:** claude (worktree agent-a08cc597c4b8c87c6)
**Filed:** 2026-07-30, by claude, from a reconciler audit that reproduced four defects
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`automation/reconcile/reconcile.py` is the referee every commit passes through, and it
currently misreports its own state three ways. An unreadable file raises a bare
`UnicodeDecodeError`, which exits 1 — indistinguishable from "the repository has
findings" — and because the finding list is built eagerly, that one crash discards every
finding already found. `check_roadmap_fresh` raises `TypeError` on a task id whose date
is impossible, such as an id starting `2026-02-30`, because `TASK_ID_RE` accepts it while
`parse_date` returns `None`. Several checks gate on `Path.is_file()` in the worktree but
read their content from the Git index, so deleting the worktree copy of a staged
violation makes the reconciler report zero findings while the commit still carries it.
Fix all three so a failed check is always reported as a failed check, naming what could
not be read. Severity tiering, the fourth defect the same audit found, belongs to task
2026-07-22-severity-tiers-for-reconciler-findings, which this task tracks as a child.

## Acceptance criteria

- [ ] An invalid-UTF-8 Markdown file, staged or untracked, exits 2 with one line naming
      the file, no traceback, and every finding found before it still printed
- [ ] A `tasks/4_done/` id with an impossible calendar date produces no exception and
      does not suppress the freshness comparison against valid ids
- [ ] A staged `**Collaboration mode:**` violation is still reported when the worktree
      copy of `AGENTS.md` is deleted
- [ ] The same worktree-gate pattern is audited at `check_stale_queue`,
      `check_roadmap_fresh`, and `check_memory_index`, and every site that reproduces is
      fixed and covered by a test
- [ ] A regression test exists for each defect and the full suite passes

## Links

- Child task carrying the severity split: 2026-07-22-severity-tiers-for-reconciler-findings
- Contract updated in the same change: `automation/AGENTS.md`
- Deterministic finding keys this must not break: `memory/lessons/automation/deterministic-finding-keys.md`
