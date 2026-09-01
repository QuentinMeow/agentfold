# Worklog — multi-worktree safety remediation

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-03 — audit-and-publication (codex)

- Claimed the planning task after a multi-agent audit reproduced linked-worktree bootstrap,
  coordination, restack, and admission hazards.
- Two independent Sol reviewers converged on serial vertical slices and keeping provider
  merge enforcement behind the existing owner decision.
- Selected GitHub issues as non-canonical projections because the user explicitly requested
  them; every issue will be bound back to a repository queue item.
- Audit evidence: `history/conversations/2026-08-03-0730PDT-audit-multi-worktree-safety/handover.md`.
- Published draft planning pull request #73 and GitHub issue projections #74 through #78.
- Bound every issue's exact provider node/version identity to a task-owned queue item; the
  stable projection ledger is in the audit conversation's `artifacts/` folder.
- Claimed issue #74's bootstrap task in a separate pushed coordination commit and delegated
  its vertical implementation to a Sol high worker in a real linked worktree.
- Published stacked draft implementation pull request #79 with the task, plan, design,
  worklog, and real verification. Its exact implementation revision survived a Sol xhigh
  block/fix/re-review cycle and an independent Terra test rerun.
- Left the parent plan in progress: issue #75's displaced-tip repair is the next serial
  implementation slice, followed by explicit expected-OID publication in issue #76.
- Exact PR-candidate verification uncovered an unconditional-hook-`chmod` stat-cache
  interaction after the first handover. The child task was honestly reopened, repaired,
  given a red-on-parent/green-on-fix canary, independently re-reviewed, and returned to
  review; final task head is `4dbb2d04eacaa482d3c806406458b99a0428fdba`.
- PR #79's local exact merge candidate passes bootstrap, raw `git diff-files`, and the
  merge-transition reconciler. GitHub's latest `reconcile-and-test` remains red because
  its event carried stale base `4dbb22e...` while checkout used merge candidate `4bee4fc...`
  whose first parent is `73492c5...`; this is the pre-existing defect tracked by issue #78,
  not a bootstrap test failure. Planning PR #73 is green.

## 2026-08-31 — development-cycle implementation resumed (codex)

- Resumed the stale parent from its recorded handover for the owner's broader request to
  implement and prove the multi-agent Git workflow across common human/agent development
  cycles.
- Started S3 orchestration run `2026-08-31-prove-and-land-the-common-8dba` with isolated
  worktrees, a six-hour interactive-to-autonomous switch, research-first planning, a
  five-lens fresh-context panel, and cross-vendor refutation.
- Preserved the earlier pending recovery run and its uncontained branches after the
  orchestration sweep correctly refused to remove them.
- No implementation choice is recorded yet; the next edge is requirements interrogation,
  research, executable scenarios, and child-task decomposition.

## 2026-08-31 — workflow architecture adjudicated for publication (codex)

- Recovered the missing S3 integration worktree and deleted remote task branch from
  preserved commit `24c387b01c6178324d114fd2c35b1b31d488ba41`; merge commit
  `ed8761ca95a29008b22ba75a098da3d3ac0c9e1d` carries it onto the current baseline.
- Opened draft [pull request #94](https://github.com/QuentinMeow/agentfold/pull/94) so
  the recovery record and this design remain reviewable. `verification.md` records the
  checks actually run against the current candidate.
- The resulting design maps ten development cycles and a fault-injection/evaluation ladder.
  `research.md` records the dated official sources, unverified boundaries, maturity
  comparison, and expected operator experience. It does not claim any behavior
  implementation or completed disposable scenario.
- Adjudicated the architecture as a durable repository evidence kernel plus
  runtime-authoritative expiring observations and a rebuildable read-only view. It separates
  work items, change sets, session observations, writer authorities, and integration runs
  rather than treating one task/branch/session as one object.
- Replanned the serial implementation order around six existing correctness prerequisites:
  displaced-tip restack provenance, exact expected-OID publication, finalized coordination
  write rules, stale-base admission, handover durability, and merged-task status drift.
  Visibility and external-product bake-offs follow only after those source records are
  truthful and the current cardinality contract has an explicit migration.
- No behavior change or disposable cycle trial is complete yet. The next reviewed slice is
  the existing restack-provenance task after the owner resolves whether task claims keep a
  narrow direct-`main` exception or move to a PR/ref compare-and-swap protocol. Its worker
  must preserve genuine discarded-action detection while removing the inherited-base false
  accusation.

## 2026-08-31 — final design evidence recorded (codex)

- Repaired two fresh-context evidence blockers: source-linked every product maturity claim
  and added a single-use controller challenge plus authenticated runner receipt so an older
  success for the same candidate cannot be replayed.
- Five new Sol xhigh reviewers independently accepted the bytes integrated at
  `e0d2a70ef31efb09779ec5cb8f13686ffd22e6a9` across requirements, repository contract,
  human workflow/product effect, evidence, and adversarial blast radius.
- A no-local clean clone bound HEAD/tree to `e0d2a70ef31efb09779ec5cb8f13686ffd22e6a9`
  / `bbd00d6de9ee62c4798af0eec86fea4c0489c495`; bootstrap passed, the reconciler had
  0 blockers and 6 pre-existing advisories, and the full runner passed 16/16 files.
- The cross-provider refuter did not run: the external-publication boundary rejected the
  Claude invocation before execution, so no candidate bytes were sent and no cross-provider
  diversity is claimed.
