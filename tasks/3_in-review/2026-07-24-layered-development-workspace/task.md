# Design the layered development workspace and prove its first safe slice

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-24, by codex, from the owner's layered-workspace request in chat
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md`

## Goal

Give humans and agents one coherent local development experience across public,
private/customized, restricted, temporary, and raw-data files without turning Git
ignores, hooks, symlinks, or a private repository into false confidentiality
boundaries. The design must preserve AgentFold's product intent: agents do most work
autonomously, the message queue is the interaction-design surface, and humans spend
little time while retaining maximum control and context.

The task includes the evidence-based design, independent adversarial review, and only
the smallest reversible implementation slice justified by that design. One-way-door
architecture or publication-boundary changes remain proposals until the required human
review is recorded.

## Acceptance criteria

- [x] The current message queue, handovers, tasks, local branches, remote branches,
      worktrees, open pull requests, and branch-only progress are audited from live
      evidence; PR #7 remains unmerged and unmodified while its reviews are open.
- [x] A durable design compares at least: private integration history, sibling
      repositories plus a materialized view, resolver-native layering, a private patch
      stack, nested repositories/symlinks, and union/overlay filesystems.
- [x] The design explicitly classifies public Git, private Git, restricted/no-Git,
      raw durable local/no-Git, and temporary data, including allowed sinks, agent
      access, backup evidence, loss assumptions, and filename/metadata sensitivity.
- [x] The durable design specifies one provenance-aware status view showing logical
      path, physical origin, publication zone, Git state, backup state, scan coverage,
      and the effective instruction stack without copying private content into public
      Git.
- [x] The first slice implements and tests only bounded topology fields; all content,
      capability, detached-worktree association, Git-executable/configuration
      authority, atomic snapshot, publisher cleanliness, backup, scan, instruction,
      and publication claims remain explicitly uninspected/unverified, and publication
      via the inspector remains unavailable.
- [x] Same-path customization and upstream update semantics are specified, including
      textual conflicts, semantic instruction conflicts, stale overrides, provenance,
      explicit read-only public-only mode, and the rule that missing private state never
      causes a silent fallback in the supported layered entrypoint.
- [x] The durable design requires public publication to use a boundary that cannot
      reach private Git objects or external restricted/raw roots; `.gitignore`, local
      hooks, sparse checkout, linked worktrees, Git LFS, and private branches are not
      treated as that boundary. The first slice does not claim this capability.
- [x] Normal within-zone editing is interruption-free. Human attention is reserved for
      unclassified imports, public export, scan failures requiring judgment or separate
      authority, trusted instruction conflicts, protected-policy changes, and
      destructive operations without required recovery evidence.
- [x] The design covers create/import, read/tool output, copy/move/link, stage, stash,
      commit, push, CI, cleanup, backup/restore, and incident-recovery failure paths,
      with redacted evidence and no claim that automated PII detection is proof.
- [x] macOS and Linux define the supported baseline. Windows is included only where
      support is simple and does not complicate or weaken the macOS/Linux design.
- [x] Independent adversarial reviewers evaluate developer ergonomics, confidentiality
      boundaries, instruction authority, recovery, portability, and human-interruption
      cost against one immutable candidate.
- [x] Only a small reversible first slice is implemented and tested after the design
      is coherent; mounts, destructive migrations, private-repository creation, and
      automatic public publication are out of scope for that first slice.
- [x] Reconciler and relevant tests pass with real output in `verification.md`, and
      remaining work is published as separately claimable queue-owned tasks through
      the live coordination lane after this PR is admitted.
- [ ] [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md)

## Links

- Research and transfer context:
  `history/conversations/2026-07-24-0202PDT-layered-workspace-research-handoff/handover.md`
- Provisional design notes: `design.md`
- Live follow-up backlog begins with task
  `2026-07-24-declare-layered-workspace-manifest`.
