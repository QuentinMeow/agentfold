# Worklog — layered development workspace

## 2026-07-24 — layered-workspace-research-handoff (codex)

- Read the queue, relevant handovers, roadmap, current task branch, and live GitHub
  state; PR #7 remains in review and must not merge before its queue-owned reviews.
- Delegated independent research on workspace composition and privacy/developer UX.
  Both reviews rejected ignores, hooks, linked worktrees, symlinks, LFS, and a private
  branch as confidentiality boundaries.
- Recorded the owner's platform answer: macOS and Linux are the baseline; Windows is
  included only when cheap and non-distorting.
- A linked-worktree pre-commit test exposed a separate Git-environment isolation bug.
  The repository was restored exactly, and the repair is filed independently so the
  workspace task does not hide an urgent safety prerequisite.
- Filed the task pickup and full requirements for another agent; no architecture or
  first-slice implementation was committed in this session.

## 2026-07-24 — stacked-publication-preflight (codex)

- Audited and preserved every source branch before rebuilding the work as three
  bottom-up review layers.
- An exact three-lens preflight blocked the first reconstructed workspace candidate
  on coordination placement, durable follow-up ownership, verdict grammar,
  publication-envelope authority, attached-worktree metadata, and Git-config parsing.
- The executable and design repairs are in progress. The task remains in progress and
  no blocked candidate is being presented as ready for human review.

## 2026-07-24 — consolidated-layered-workspace (codex)

- Audited every local branch, remote-tracking ref, stash, and worktree. The message
  queue branch and current `main` had disjoint changed-path sets, so they were joined
  on branch task/2026-07-24-layered-development-workspace without modifying the PR #7
  source branch. Redundant snapshot branches/stash were left intact; the older mixed
  backup and personal Git-auth branch were deliberately not merged.
- Live GitHub evidence showed one open PR: #7 at `6ddac44`, unmerged, mergeable, and
  still carrying the already-recorded trusted-check/link-check failures. No PR metadata,
  review, branch, or remote state for PR #7 was changed.
- Finished the blocking test-runner isolation repair first. The canonical runner now
  strips inherited repository-selecting Git state, validates an external discovery
  boundary, and gives each test a versionable metadata-free view. Eleven focused tests,
  all nine repository test files, repeated linked-worktree state probes, and a final
  unanimous adversarial panel passed; the independent task is done.
- Claimed and pushed this task only after that blocker was resolved.
- Wrote the durable hybrid proposal in
  `docs/designs/layered-development-workspace.md` and corrected the adoption guide and
  roadmap. A separate stress pass narrowed the first-slice claim from content isolation
  to declared storage topology, removed path-derived pseudonyms, split backup evidence
  into independent dimensions, and kept export/capability implementation behind a
  future human architecture review.
- Three independent reviewers evaluated immutable candidate `feddac1` through
  ergonomics, authority/portability, and confidentiality/recovery lenses. All three
  blocked it with concrete counterexamples: same-path public intent was not separately
  representable; layered-tool admission was unenforced; instruction tombstones and
  free-form authority were ambiguous; textual canonical paths aliased on macOS; a
  broad Git push could escape the reviewed candidate; runtime sinks and incident
  revocation were incomplete; and backup observation could authorize unsafe deletion.
- Repaired those blockers by separating public-candidate and private-effective
  identities, defining short-lived manifest-bound admission leases, making
  instruction-bearing tombstones conflicts, binding free-form instruction receipts,
  using filesystem identity comparisons, enumerating protected runtime sinks, binding
  publication to one epoch/ref/object closure, and requiring exact recovery evidence
  or explicit loss acceptance. A fresh immutable candidate and fresh panel remain the
  acceptance gate.
- A fresh three-lens panel unanimously blocked repaired candidate `7fc3bca`. Concrete
  counterexamples covered two-result authoring, direct-tool fallback, writable
  public-only ambiguity, per-layer status, queue dedup identity, receipt scope,
  rollback of the private control plane, ambient Git configuration and scanner sinks,
  remote ref/epoch races, hidden server state, ambient capability channels, and
  same-failure-domain backups.
- The next candidate makes public intent an atomic two-result private transaction;
  scopes the supported experience to supervised leased sessions; makes public-only
  non-executing/read-only; records per-layer and monotonic witnessed state; binds
  authority to path/scope/delegation/epoch; uses hermetic Git and scanners; requires a
  destination-side ref-and-epoch transaction; reports hidden server state unknown;
  attests the ambient capability graph; and revalidates failure-domain recovery
  evidence immediately before any destructive action.
- Implemented the first reversible slice as
  `automation/inspect_workspace_boundaries.py`. It verifies declared filesystem
  identity/ancestor separation, exact non-bare Git worktree roots, distinct metadata
  and object stores, publisher alternates, and no-Git zone ancestry while reporting
  content, object-file sharing, Git configuration authority, capabilities, scan,
  backup, instruction provenance, and publication limits explicitly. Thirty-five
  focused cases pass on macOS, with the non-UTF-8 path-byte case skipped because local
  Git rejects that path before inspection.
- Filed six queue-owned backlog tasks for manifest/status, override lineage, review-first
  instruction admission, dry-run cross-zone operations, recovery evidence, and a
  review-only publication/capability boundary. No exporter, credential, public push,
  repository creation, mount, migration, or destructive operation was introduced.
- The fresh implementation/confidentiality/contract panel unanimously blocked
  `a46b391`. It reproduced permission-denied false passes for Git markers and
  alternates, plus design failures around legitimate lease mutations, public-only
  private-root reads, unenforced task dependencies, publisher-cleanliness wording,
  retry dedup, private-session direct pushes, rejected-upload disclosure, expanding
  capabilities, and deletion time-of-check/time-of-use.
- Repaired those findings by accepting only `ENOENT` as marker absence, adding
  permission regressions and bounded non-atomic/detached-worktree claims, defining
  authorized lease renewal, rejecting private zones in public-only mode, reporting
  publisher cleanliness uninspected, adding transition-start dependency actions,
  stabilizing dedup keys, gating private-session egress, reserving publication before
  upload with durable indeterminate outcomes, requiring operation-lifetime capability
  enforcement, and quarantining identity-bound destructive targets atomically.
- A fourth exact-revision panel unanimously blocked candidate `31a5ff1`. The executable
  review showed that local Git includes could block on an external FIFO, Git queries
  had no timeout, and malformed argparse input echoed a sensitive path. The
  confidentiality review showed that a same-user source process could bypass a global
  publication-block claim, received-object evidence omitted unreachable extras,
  capability receipts were replayable across process trees, backup policy could be
  mistaken for observed failure-domain evidence, and quarantine did not fence open
  writers or mappings. The contract review found one prose-only parent dependency,
  incomplete lease/CAS and crash-recovery semantics, conflicting lineage state names,
  incomplete free-form instruction ancestry, and an underspecified retry-dedup key.
- The next candidate binds every Git control query to a canonical installer/policy
  executable outside declared roots and a minimal environment, bounds and redacts it,
  proves direct repository shape before Git parses configuration, rejects local
  includes and external worktrees, and narrows
  publication output to what the inspector actually establishes. The design now
  requires whole-source capability
  isolation before any global block claim, exact destination object-set equality,
  process-generation-bound capability receipts, observed recovery properties, an
  exclusive deletion writer fence, single-use mutation/CAS receipts, idempotent
  witnessed-generation recovery, one canonical lineage enum, whole-ancestor
  instruction compatibility, atomic queue-key uniqueness, and a mechanical parent
  completion dependency for manifest work.
- The next immutable panel unanimously blocked `710578b`. The executable reviewer
  reproduced a UTF-8-BOM include-section bypass. The contract reviewer found the
  pre-witness staged crash state missing, lease renewal possible before witness commit,
  compatibility checked against public but not private ancestors, and role-only dedup
  capable of merging unrelated workspaces. The confidentiality reviewer found that a
  human loss receipt could waive target safety, temporary cleanup could cross a
  descendant mount, publication lacked authenticated immutable destination identity,
  and destination verification omitted the pre-existing base side of the candidate
  closure.
- The repair strips a leading Git-config BOM before preflight; makes the full
  staged/prepare/CAS/commit matrix normative and witness commit a lease prerequisite;
  binds free-form compatibility to every ancestor and retry keys to stable opaque
  decision-subject identities; makes mount/target/writer/quarantine safety non-waivable
  for every recursive deletion; and binds publication to authenticated destination
  identities plus a destination-hashed complete base-and-received candidate closure.
- A fresh three-lens review unanimously approved immutable candidate `2fa68ce` after
  retesting the executable, control-plane, confidentiality, publication, and recovery
  counterexamples. The 35 focused cases, all 10 repository test files, range-level
  core-scope check, diff hygiene, and reconciler passed with real output recorded in
  `verification.md`.
