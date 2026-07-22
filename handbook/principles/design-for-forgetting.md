# Design for forgetting

A memory system that only accumulates becomes noise, and stale "facts" are worse than
no facts — an agent that trusts an outdated constraint confidently does the wrong
thing. Forgetting is therefore a first-class operation: every memory entry carries an
expiry, and the system re-verifies, compacts, or deletes on schedule.

## Rules

- **Every entry has a `Review-by` date.** Set at write time (default 90 days; shorter
  for anything time-sensitive). The reconciler flags overdue entries; the
  `skills/memory-gardener/` pass re-verifies (bump the date), rewrites (compact), or
  deletes them.
- **Lessons are scoped, not global.** A lesson learned from a failure lives in
  `memory/lessons/<area>/` and is read only when working in that area (the root
  `AGENTS.md` boot sequence says so). Global lesson lists grow unbounded and get
  skipped; scoped lessons stay short and get read.
- **Merge before adding.** Before writing a new lesson or fact, look for an existing
  entry covering the same problem; update it rather than duplicating. Two entries about
  one problem eventually contradict each other.
- **Promotion is deliberate.** Repeatedly-confirmed lessons graduate into the relevant
  `AGENTS.md` (and the lesson is deleted — one home per fact); untouched entries age
  out. Both moves are visible commits, never silent.
- **Deletion is safe by construction.** Git history archives everything, so the
  gardener moves and deletes without ceremony. What earns deletion: superseded facts,
  lessons about code that no longer exists, decisions replaced by newer ADRs
  (the ADR file itself is immutable — it gets a `Superseded-by` link instead).

## Why

Agents rebuild their worldview from files every session, so the files *are* the mind.
Curating what to forget is the same job as curating what to remember — the memory map
and zones live in `memory/AGENTS.md`.
