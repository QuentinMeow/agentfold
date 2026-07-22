# Design notes — bootstrap

**Status:** decided (per-decision records: `memory/decisions/`)

## Inputs

- Deep read of the source project's harness (two-tier agent contract, four-queue todo
  system, skills-with-symlinks portability, gardener-based forgetting, tracked hooks).
- Survey of public prior art: AGENTS.md standard, superpowers, spec-kit, OpenSpec,
  Backlog.md, Cline Memory Bank, compound engineering, ACE-FCA (lineage links:
  `README.md`, "Design lineage").

## Shape of the solution

Ten top-level folders, each an independent service with its own contract; all schemas
centralized in `templates/`; all invariants centralized in the reconciler. The queue is
named by who-acts-next; task status is folder location; memory carries expiry dates.

## One-way doors filed

None blocking — the repo owner delegated naming and structure ("you get the call").
The significant calls were recorded as ADRs instead, so they can be revisited with
their reasoning intact:

- Repo name → `memory/decisions/2026-07-22-repo-name-agentfold.md`
- Queue naming → `memory/decisions/2026-07-22-queue-folders-named-by-who-acts-next.md`
- Task status as folders → `memory/decisions/2026-07-22-task-status-as-folders.md`
- Bold-key frontmatter → `memory/decisions/2026-07-22-bold-key-frontmatter.md`
- Visible `skills/` + adapter symlinks → `memory/decisions/2026-07-22-visible-skills-dir-with-symlinks.md`

## Deliberately left out (roadmap, not scope creep)

Per-skill eval canaries, the public/private overlay as a packaged module, an `npx`-style
installer, a queue web viewer — all recorded in `roadmap/desired-state.md`.
