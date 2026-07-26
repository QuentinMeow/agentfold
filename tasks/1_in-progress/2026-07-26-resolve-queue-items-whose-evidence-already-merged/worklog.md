# Worklog — Let a queue item resolve when its resolution evidence landed in an earlier commit

## 2026-07-26 — claim-merged-evidence (codex)

- Claimed the task, moved it from backlog to `1_in-progress`, and removed its completed task-pickup request atomically.
- Recorded the converged implementation constraints in `plan.md`: the repair applies only to ordinary `needs-agent` requests; compares every resolution-evidence path against the unique current-incarnation creation snapshot; requires final readable surviving bytes to differ; retains the independent status-only claim; and preserves human, retry, pickup, and custom behavior.
- The task wording’s earlier `at or after claim edge` criterion is contradictory to the creation-snapshot baseline. The reviewed task branch will amend it openly to the intended post-creation criterion; this direct-main coordination commit intentionally does not alter substantive acceptance criteria.

## 2026-07-26 — implement-merged-evidence (codex)

- Limited historical evidence widening to ordinary agent requests. The implementation finds a unique current-incarnation creation root over the complete DAG, follows exact and unambiguous disappearing-path predecessors on every merge parent, detects shallow boundaries, and fails closed on ambiguous roots or Git reads.
- Required every declared evidence path to use a closed repository-local grammar and retain bytes different from its creation baseline at both the deletion event and final admission candidate. Captured staged index bytes, not working-tree bytes, are authoritative.
- Kept the status-only claim check separate and left human folding, reviews, retries, pickups, and custom leaves on their prior control paths.
- Adversarial preflight found and drove regressions for merge rename baseline reset, mixed exact/renamed merge parents, mixed malformed evidence, shallow history, index/worktree disagreement, deletion-then-revert laundering, and a post-deletion change that could otherwise retroactively justify cleanup.
- Corrected the task's claim-edge wording to the chosen post-creation rule and documented its byte-level false-positive/false-negative limits in `design.md`.
- The focused 19-test matrix passed, followed by all 315 queue reconciler tests in 148.879 seconds.
- Deleted the live resolved handover-projection request and changed only its reciprocal task's `Queue actions` field to `none`; final staged admission and full-suite evidence follow in `verification.md`.

## 2026-07-26 — repair-review-blockers (codex)

- The first independent panel blocked the implementation on three issues: an exact synthetic
  merge candidate could restore creation bytes without being checked; raw commit parsing
  decoded/scanned beyond the header block and the legacy diagnostic phrase had drifted; and
  the creation walk launched several Git processes per intervening commit.
- Added the actual captured candidate to the surviving-evidence proof and restored the
  `resolution evidence was not created or changed` diagnostic contract.
- Replaced per-commit process launches with one cached parent graph and one persistent batch
  object reader. Commit headers, trees, blobs, paths, and queue-subtree boundaries are parsed
  or cached invocation-locally; raw/effective parent disagreement detects shallow history;
  both 40- and 64-character object IDs are accepted.
- Added exact synthetic-merge, raw non-UTF-8 commit-body, malformed-header, and deterministic
  300-unrelated-commit regressions. The performance regression proves one bulk parent query,
  one batch object reader, no per-revision history/tree/show process, and no additional process
  calls on a repeated lookup.
- The first full queue run exposed that existing task-admission checks also pass a raw empty
  tree object to historical artifact reads. Generalized the cached path reader to accept a
  validated commit or tree root; the affected 13-test subset and the final 320-test queue suite
  then passed.

## 2026-07-26 — repair-replacement-ref-determinism (codex)

- The second independent panel unanimously blocked revision `6df6010` because the bulk graph
  walk disabled Git replacement refs while the persistent object reader honored them. A local
  replacement could therefore forge the action-creation tree and change the baseline/verdict.
  The contract reviewer also found that verification omitted the acceptance criterion's
  per-method pre-repair test matrix.
- Started the sole persistent object reader with `git --no-replace-objects cat-file --batch`,
  matching every history query used by the creation proof. No other admission semantics
  changed.
- Added a real replacement-ref regression that forges the action-creation tree while retaining
  the action and parent. It proves unchanged evidence rejects identically with and without the
  ref for a staged deletion, a direct range, and an exact synthetic-merge candidate.
- In isolated detached worktrees, the replacement test failed against blocked revision
  `6df6010` and passed after the one-line repair. All 24 test methods introduced by this task
  were also run against base checker `ab5a18e`; `verification.md` records every method verdict
  and distinguishes assertion failures from missing-new-helper errors and non-discriminating
  passes.

## 2026-07-26 — repair-candidate-provenance-and-audit-linkage (codex)

- The third independent panel unanimously blocked `e52cd9e`: candidate-parent discovery still
  honored replacement refs, so a raw one-parent/out-of-range checkout could advertise forged
  `{base, head}` parents and pass as an exact synthetic merge. The contract review also found
  missing task trailers on `6df6010`/`e52cd9e`, literal `\n\n` in `ee0f36e`'s message, and no
  durable final full-suite record for the repaired implementation.
- Preserved the original unpushed chain at local backup branch
  codex/pre-audit-linkage-e52cd9e. Rebuilt the three commits non-destructively from
  `ab5a18e` with identical tree objects and parent order, clean paragraph bodies, and exact
  `task: 2026-07-26-resolve-queue-items-whose-evidence-already-merged` trailers:
  `ee0f36e` → `af447435`, `6df6010` → `e5bf650f`, and `e52cd9e` → `6dc7d496`.
- Disabled replacement refs for candidate-parent discovery, candidate tree capture/comparison,
  and adjacent range-derived task history reads. Added a real exploit regression: an ordinary
  one-parent candidate remains rejected even when its replacement commit claims `{base, head}`
  parents.
- The exploit changed `(2, provenance error)` to `(0, no error)` on the old checker and passes
  after the repair. Its base-checker failure was added to the pre-repair matrix, bringing the
  explicit task-added method count to 25.
- A first complete-suite attempt exposed one stale argv assertion for cached HEAD tree reads;
  the expected command now includes `--no-replace-objects`. The focused cache/exploit pair and
  the subsequent 11-file repository suite passed. The code-repair hook and its exact evidence
  are recorded only after that commit exists.

## 2026-07-26 — close-raw-git-boundary-and-evidence-grammar (codex)

- The fourth independent panel unanimously blocked `2b6c269`. Replacement-aware staged diffs
  could hide queue, handover, and task changes; replacement-aware review validation could forge
  target type or common ancestry; and handover discovery/baseline reads could observe forged
  trees and bytes. The evidence parser also rejected schema-valid angle-bracket destinations
  containing spaces, and an earlier verification entry mislabeled the reconciler's success
  output as no output.
- Audited every Git invocation in the reconciler and introduced one raw-object argv prefix for
  all affected admission-verdict reads. Kept only index/worktree inventory, literal HEAD/ref
  lookup, merge-state path lookup, and content hashing on a documented replacement-insensitive
  allowlist. A source-level AST regression prevents new unprefixed Git reads from silently
  expanding that allowlist.
- Added real replacement forgeries covering staged queue deletion/mutation, staged handover
  mutation, staged task change/rename, Git-review object type and ancestry, root/range handover
  discovery, handover creation bytes and queue tree, current-incarnation baseline bytes, and an
  uncached staged blob read.
- Preserved the evidence grammar's closed-list behavior while accepting ASCII spaces only in
  angle-bracket Markdown destinations. Expanded the mixed-invalid matrix across traversal,
  absolute, URI, queue-local, whitespace code-span, and malformed-link entries.
- All seven focused fourth-round tests passed. The same tests against base checker `ab5a18e`
  produced five failing new methods, one passing compatibility case, and the already-existing
  mixed-invalid method failure, confirming the behavior change without overstating the
  non-discriminating angle-link acceptance case.
