# Design notes — multi-worktree safety remediation

**Status:** decided

## Problem

The repository assumes file-based coordination is safe across independent agents, but the
audit reproduced races in linked-worktree bootstrap, coordination publication, task-branch
restacks, and landing admission. The repair must preserve the repository's canonical task
and queue records while giving each behavior change an independently reviewable boundary.

## Options considered

### Option A — one broad safety pull request

Change the installer, reconciler, Git workflow, and admission mechanism together. This
shortens the branch list but makes intermediate invariants and regressions hard to isolate.

### Option B — serial vertical slices

Ship one complete behavior at a time: linked-worktree bootstrap; displaced-tip provenance;
explicit expected-OID publication; authoritative coordination publication; stale-base
admission; then lifecycle-reference repairs. Each slice carries its task, design, tests,
and safe stopping point.

## Chosen

Use serial vertical slices. Parallel agents may research and test, but implementation that
touches shared reconciler or workflow surfaces is serialized. GitHub issues are projections
only: each points back to one canonical task and a source-bound queue item. Server-side
landing enforcement remains deferred behind the accepted advisory-gate decision.

Keep AgentFold's repository records as the durable evidence kernel. External products may
own execution observations, workspace management, transport, or provider delivery only
through replaceable adapters. No external task database, message stream, or dashboard may
dual-write canonical tasks, decisions, verification, or admission state.

The owner requires all progress to arrive as pull requests, while the repository currently
requires atomic task claims and status changes directly on `main`. The case-specific 2026-07-24
authorization does not settle future claims. The first planned implementation task cannot
start until the owner chooses whether live coordination keeps a narrow direct-`main`
exception or first moves to a tested PR/ref compare-and-swap design. The canonical decision is
`message-queue/needs-human/decisions/future-blocking-choose-whether-task-claims-must-use-pull-requests.md`.

## Authority and identity model

One authority owns each fact family. Missing runtime evidence is `unknown`; it never means a
writer stopped.

| Identity or plane | Owns | Does not prove |
|---|---|---|
| Work item | Goal, acceptance, dependencies, risk, and durable owner intent | Branch topology or live process state |
| Change set | Repository, base/tip/displaced object IDs, branch/worktree binding, write scope, stack links, and delivery selection | That a writer process stopped or that a task is complete |
| Session observation | Runtime/session identity, observed state and expiry, capabilities, and raw provider state | Exclusive write authority, process termination, review approval, remote backup, or durable completion |
| Writer authority | A runtime or OS capability that grants, fences, and revokes one writer generation for one change set | Task completion or liveness when its own observation is stale |
| Integration run | Ordered immutable change-set inputs, constructed result, environment, checks, merge strategy, and outcome | Untested candidates or future provider state |

The common path remains one work item, one change set, one writer session, and one pull
request. The identities stay separate so replacement pull requests, stacked bases,
competing experiments, multi-task candidates, and landing batches do not become schema
exceptions. One active writer per writable change set is a hard claim only when an adapter
can prove grant, revocation, and fence behavior. Without that capability, exclusivity is an
advisory protocol, an expired observation is `unknown`, and takeover is refused. Read-only
reviewers may remain parallel.

The current one-agent/branch/PR-per-task contracts remain binding until a dedicated migration
task changes `tasks/AGENTS.md`, `handbook/git-workflow.md`, task/change-set templates, the
reconciler, and their tests in one reviewed sequence. The identity model is a proposed target,
not permission to violate today's cardinalities.

## Common development cycles

Each row is an acceptance scenario that must run in a disposable repository before this
parent can claim the workflow is implemented. A simulated edge proves only the named Git or
state-machine behavior; live agent messaging and liveness require real sessions.

| Cycle | Human-visible result | Agent boundary | Required proof |
|---|---|---|---|
| Create and claim | One ready task becomes owned; a competing claimant sees the winner | Compare-and-swap against one observed coordination tip; a loser does not write | Two claimers plus an unrelated concurrent coordination commit |
| Shared state refresh | Two sessions see the same task, owner, dependency, scope, and checkpoint after one changes it | Query before startup, recovery, scope expansion, and handoff; messages never substitute for refresh | One session updates; the other re-queries every boundary and observes the exact new bytes |
| Independent parallel edits | Two rows show disjoint scope, worktrees, resources, checkpoints, tests, and pull requests | One writer per change set; unique ports/databases/output paths | Two real sessions; no uncommitted-byte or resource collision |
| Overlapping scope | The second start names the owner, path, and available wait/narrow/stack choices | Scope reservation is advisory governance, never an OS sandbox claim | Overlap refused before mutation; succeeds after release/narrowing |
| Pause and takeover | The next reader sees exact local/remote checkpoint, unfinished work, and positive stop/revocation evidence | Preserve the old workspace; `live` and `unknown` refuse transfer; only adapter-confirmed stop/revocation or an OS writer fence permits takeover | Inject orphaned, live, unknown, and revoked writers; only the revoked/fenced case resumes from canonical artifacts without prior chat |
| Process, worktree, and machine loss | One report states the strongest recovered boundary and every lost local-only byte | Dirty bytes, local commits, remote commits, and task/message backup are separate | Kill process; remove disposable worktree; restore on a clean host |
| Prerequisite change | Shared refactor appears once; dependents become ready from the landed baseline | Task dependency and Git base dependency are distinct | R lands before B/C; B/C contain no repeated R implementation |
| Stacked change | Stack depth, bases/tips, restack owner, and landing order remain visible | Safe pause, exact expected-OID lease, displaced-tip evidence, child retarget | Intervening sibling update survives; false and genuine deletions differ |
| Integration failure | Individually green candidates display one combined-red result and named failing leg | One guarded integration entry pins every input and is the only operation allowed to advance the tested target ref | Attempted landing leaves the target ref unchanged on combined red; the same entry advances it only after repair and rerun |
| Merge and cleanup | Landed tasks, retained evidence, dirty/unknown worktrees, PR bases, and removable artifacts are distinguishable | Cleanup is dry-run first and only removes run-created, contained state | Refuse dirty/base/uncontained artifacts; recreate projections from authority |

## Verification ladder

1. Deterministic unit tests cover legal transitions, exact object-ID transactions, result
   algebra, corrupt state, duplicate operations, and protected evaluator surfaces.
2. Integration tests allocate isolated resources and inject crashes immediately before and
   after durable writes and external effects. Resume promises idempotent replay, not
   deterministic model tokens or exactly-once execution.
3. Disposable end-to-end scenarios cover the ten cycles above plus malicious peer
   messages, provider outage, schema migration, and rollback. Every new check is observed
   green, then red for its named damage, and appears in runner discovery output.
4. Held-out capability evaluation uses paired repeated trials, fresh/private tasks,
   controlled resources, deterministic outcome graders first, and calibrated model judges
   only where no mechanical oracle exists. A separate custodian QA-checks tasks/graders,
   quarantines ambiguity, and proves the agent cannot read answer-bearing remotes, refs,
   tags, reflogs, gold patches, grader source, or prior trajectories. Unresolved leakage or
   grader ambiguity is a hard denial. Public benchmark scores are diagnostics, not release
   authority.
5. Core or one-way-door changes receive a five-lens fresh-context panel and a different-
   provider refuter. An independently launched authoritative runner binds raw evidence to
   the candidate bytes: a trusted controller supplies the repository identity plus immutable
   commit and tree object IDs; the runner checks out that commit without replace refs,
   alternate object stores, or dirty bytes; and its manifest records the commit/tree, runner
   version, environment image, command/test digests, raw-output hashes, and result. Negative
   fixtures must refuse a branch moved after selection, a replace ref, a dirty worktree, a
   substituted candidate tree, and evidence copied from a different run. Self-evolving
   agents may propose isolated candidates but cannot
   access or alter hidden tests, grader source, runner credentials, secrets, the evaluator,
   evidence collector, policy, approvals, stable pointer, or rollback controls that judge
   them; self-authored logs are not evidence.
6. Runtime changes shadow without canonical write authority, then canary only reversible
   low-risk work with predeclared stop conditions and an already-tested rollback.

## External product disposition

The dated observations, official sources, maturity limits, and expected operator experience
behind these dispositions are in `research.md`.

- Gas Town receives the first full-stack scratch bake-off because it is the closest
  open-source task/worktree/message/recovery/merge system; its young history and operational
  surface bar direct core promotion.
- GitHub Agent HQ receives the first visibility and pull-request control-plane trial;
  partner agents remain preview and GitHub does not replace repository governance.
- Conductor and OpenHands are runtime/workspace candidates. Claude Agent Teams, Codex
  subagents, Codex worktree chats, and the Codex app-server are execution backends. Claude
  peer messages never become task completion or permission by prose alone; no verified
  Codex peer-to-peer messaging or durable shared task graph is assumed.
- Beads may become a disposable task index/claim projection only after duplicate-claim,
  outage, schema-upgrade, backup/restore, and deletion/rebuild tests. Vibe Kanban is not a
  core candidate because its company and remote plane shut down.

## Dependency order

1. Linked-worktree bootstrap.
2. Displaced-tip queue provenance.
3. Explicit expected-OID task-branch publishing.
4. Finalized coordination write rules and the already-implemented stale-base admission PR.
5. Handover references that survive task moves and merged-task status drift detection.
6. Identity relationships, then migration of the current one-task/branch/PR contracts.
7. Authority/freshness contract and a guarded integration entry that refuses combined red.
8. Read-only joined visibility plus checkpoint/recovery evidence.
9. Disposable fault-injection and live-session cycle proof.
10. External-product bake-offs and optional thin adapters.
11. Required server-side admission only after a superseding owner decision.

## Core fit

**Agent substitution:** pass — the protocol depends on Git and repository records, not a named runtime.
**Provider substitution:** pass — local correctness uses immutable Git object IDs and provider-neutral checks.
**Repository substitution:** pass — any repository using linked worktrees and concurrent agents needs these boundaries.
**User-global writes:** none
**Why AgentFold core:** these mechanisms protect the repository's own coordination and admission invariants.
**Thin adapter:** none
