# Pick up the layered development workspace task

**Status:** open
**Filed:** 2026-07-24, by codex, from the owner's handoff in chat
**Action:** Claim task `2026-07-24-layered-development-workspace`, finish the live branch/status audit and evidence-based design, obtain independent adversarial review, then implement and verify only the safest reversible first slice.
**Full context:** [task specification](tasks/0_backlog/2026-07-24-layered-development-workspace/task.md)
**Resolution evidence:** `tasks/0_backlog/2026-07-24-layered-development-workspace/worklog.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog, existing repository layouts remain unchanged, and PR #7 remains in review; no current work is blocked.

## What you need to know

AgentFold is an agent-native harness for vibe coding: agents should need minimal human
intervention, evolve the harness through evidence, and use the message queue as the
human-control surface. The developer experience must give humans and agents one
central, provenance-aware local view without requiring routine multi-repository Git
choreography or allowing private material to enter public history.

The design must cover all five operational classes:

1. public files versioned in a public repository;
2. private/customized files versioned in a private repository, including same-path
   changes to public instructions or any other file;
3. disposable temporary files that never enter Git;
4. sensitive or personally identifiable files that use private Git only when retention
   is explicitly appropriate and otherwise never enter Git; and
5. durable local raw data outside Git, with explicit backup/loss state because the
   local copy may disappear.

Required UX and policy:

- One logical status view must show the effective tree, source zone, physical origin,
  Git destination/state, backup evidence, scan coverage, and instruction provenance.
  Sensitive filenames may need redaction.
- Normal edits inside a classified zone should not prompt. Human attention is reserved
  for unclassified imports, private-to-public export, scanner failure/incomplete
  coverage, trusted instruction conflict, protected-policy changes, and destructive
  action on unbacked data.
- Same-path private customization must be reviewable beside the admitted public base.
  Textual merge success is not authorization: instruction-bearing changes and stale
  private overrides require semantic review.
- Provenance binds authority before filesystem position. Hard public safety constraints
  cannot be weakened privately; specialization is allowed only for declared
  overridable keys; unresolved trusted conflicts block admission.
- Missing private state must produce an explicit unavailable/conflict state, never
  silently reveal the public lower layer. Public-only operation is an explicit mode.
- Public publication must occur from a boundary that cannot reach private objects or
  restricted/raw roots. Do not treat `.gitignore`, hooks, worktrees, sparse checkout,
  symlinks, Git LFS, encryption filters, or a private branch as that boundary.
- Secrets and erasure-sensitive PII do not belong in Git merely because a repository
  is private. Raw data stays outside every worktree. Backup displays must report
  observed commit/push/snapshot/restore evidence, not infer safety from configuration.
- Compare private integration history, manifested/materialized sibling roots,
  resolver-native layering, private patch stacks, nested repositories/symlinks, and
  union filesystems with explicit pros, cons, conflicts, recovery, editor/search,
  portability, and leak paths.
- Cover create/import, reads and tool output, cross-zone copy/move/link, stage, stash,
  commit, push, CI, cleanup, backup/restore, and incident recovery. A detector error or
  unsupported input is never a clean result.
- macOS and Linux are the baseline. Add Windows support only when simple and when it
  does not complicate or weaken those platforms.

The strongest research hypothesis is a hybrid: a non-Git workspace envelope; one
ordinary private integration checkout for public plus private versioned content;
separate sibling restricted/raw/temp roots; a provenance manifest and status board; and
a physically separate clean public publisher. Challenge this hypothesis rather than
treating it as decided.

Current constraints:

- Do not merge or rewrite PR #7 on branch
  task/2026-07-23-first-class-message-queue; its
  queue-owned human reviews remain open.
- Complete the separately filed Git test-environment repair before trusting linked
  worktree hook runs.
- One-way-door architecture, destructive migration, automatic publication, mount
  providers, and creation of real private repositories require later reviewed tasks.
  The first implementation slice must be reversible, repository-local, and tested.

## Done when

The task is claimed through the normal coordination commit, the immutable reviewed
design and real verification evidence exist, the smallest reversible slice passes the
reconciler and relevant tests, and every deferred implementation or human judgment has
its own canonical queue-owned action before this request is deleted.
