# Recovery inventory and final-content disposition

The useful implementation comes from current main and original PRs 88 and 89. The owner’s unfinished local merge and retained experiments contain no independent final behavior. Original objects, branches, worktrees, staged bytes, and merge metadata remain recoverable; temporary experiments are excluded as implementation sources.

The recovery request is recorded in `requirements.md`. Final test and publication evidence belongs in `verification.md`; this inventory records source identity and the content choices.

## Sources preserved

| Source | Immutable identity | Disposition |
|---|---|---|
| Current main | 326d8ed5fa4f89eaa1402a54d8377dba5946be12 | Base of the replacement stack; its seven newer completed-task moves and current contracts remain. |
| Original PR88 | af6a7438ed7e362de35fee825c70a767573e4fb6 | All ancestry and useful fold, visibility, lifecycle, word-count, and Python compatibility behavior are retained and repaired forward. |
| Original PR89 | f56084d61aeb24d1907b711de13b3ba8c86719e7 | All ancestry, including review retraction/publication, is retained; source evidence and unanswered-review successors are repaired in the upper layer. |
| Owner index / first probe | 63abfe0f3d979f586da744d4ae9fbf66bbda6f50; tree a00abde450fce43f591f32fa37733b6243a8abbc | All 718 indexed entries match the probe by path, mode, and blob. Preserved as recovery evidence; this older-main tree is not the new baseline. |
| Combined old probe | e327d61fa118003989e61588670f0ec9c99bcb89 | Automatic union of the first probe and original89; no manual-resolution delta or additional feature. Preserved only. |
| Pre-ceremony backup | a2ab98d6244212e855394b4173a7fde97f866a66 | Older fold implementation and 700-word budget, superseded by PR88; no extra queue-test method. The ref remains; older behavior is excluded. |
| Pre-rewrite backup | dc76159acaa6d07a1f31a0efcb6168ef6c032119 | Older records only; no code delta from PR88. The ref remains. |
| Ship-fix backup | e292b211218c360cb2b8718e82dd543bea7ae778 | Reconciler AST equals PR88; only a numerical-evidence comment and older records differ. The ref remains; superseded claims are excluded. |

No active stash exists. The preexisting Claude research worktree is clean at old main at 11cfaf31f0f6f7eaa31944ddfb39cc9c40d11d7d. Ignored adapters, bytecode, OS metadata, and private runtime configuration are not portable implementation inputs and remain untouched.

## Useful behavior retained and repaired

| Area | Final disposition and reason |
|---|---|
| Human question format | Retain one sanctioned metadata fold below the answer and hard-break rendering. Existing frozen questions are not reformatted. |
| Visibility and immutable bytes | Retain raw hidden-content protection, positional semantic views, record-swallow, and fold validation. Reversed tags, hidden fields, and invisible payloads remain refused. |
| Retry diagnosis | Keep ordinary actor-owned diagnostic prose editable through manual/generated claim and resolution; freeze hidden markup, reference definitions, code blocks, and structural boundaries. Visible Unicode is not mistaken for hidden content. |
| Human response | Preserve the person’s first free-text answer, including literal angle prose, while refusing later rewrites or hidden metadata changes. |
| Existing lifecycle details | Retain real Git revision binding, future-blocking task boundaries, date ordering, operation names with version dots, and whitespace-safe field parsing from PR88. |
| Authoring budget and templates | Retain the 800-word limit and word-count command. Move instruction comments into the authoring guide so genuinely filled templates pass without a new HTML exception. |
| Python compatibility | Retain88’s guarded AST string-node handling; no duplicate workaround or environment configuration. |
| Source excerpts | Keep every-length verification against captured regular-file bytes, supported hash headings and bounded physical lines, faithful identifiers/case/literals, and ordered omissions. Attributed links resolve to the same captured source in both checks. |
| No-source and external evidence | The exact no-source sentence remains usable for questions that do not depend on source wording; it never replaces a local review target excerpt. External content remains unfetched and unverified. |
| Unanswerable review | Keep the same timing, context, target and revision in a distinct unanswered waiting successor, with reciprocal lineage and changed declared resolution evidence. |
| Policy and records | Citation-quality findings remain advisory; existing link and lifecycle gates remain enforced. Preserve original historical records and newer main records; regenerate indexes from canonical files. |

The four original merge conflicts are resolved by retaining current main’s automation contract, regenerating memory and queue indexes, and retaining both relevant current-state sections. The final implementation does not import old probe counts or undo later task completion.

## Original local uncommitted files

This preserved checkout remains on task/2026-08-18-fold-the-queue-machine-record at af6a7438ed7e362de35fee825c70a767573e4fb6, with MERGE_HEAD 11cfaf31f0f6f7eaa31944ddfb39cc9c40d11d7d. There are 79 staged records: 49 additions, 22 modifications, 5 deletions and 3 renames (82 path identities). No unstaged tracked diff or nonignored untracked file was found. These are the original files, not uncommitted work in the replacement branches.

The index SHA-256 is 99397231c04f10e69e13dc7f62a2e761d30ef965105e317c120804ae80cd9589. The exact staged path listing follows; Git’s rename rows show both paths.

```text
M	.github/workflows/harness.yml
M	AGENTS.md
M	README.md
M	automation/AGENTS.md
M	automation/check_action_projection.py
M	automation/check_core_scope.py
M	automation/install.py
A	automation/review_receipt.py
M	automation/run_tests.py
M	automation/tests/test_check_action_projection.py
M	automation/tests/test_check_core_scope.py
M	automation/tests/test_github_action_projection_workflow.py
A	automation/tests/test_install.py
M	docs/designs/AGENTS.md
M	handbook/AGENTS.md
M	history/AGENTS.md
A	history/conversations/2026-08-04-0025PDT-fix-stale-base-admission/handover.md
A	history/conversations/2026-08-04-0110PDT-stale-base-candidate-ranges/handover.md
A	history/conversations/2026-08-04-0135PDT-stop-review-verdicts/handover.md
A	history/conversations/2026-08-04-0205PDT-repair-review-verdict-scope/handover.md
A	history/conversations/2026-08-04-0220PDT-repair-heading-boundaries/handover.md
A	history/conversations/2026-08-04-0429PDT-implement-closed-review-receipts/handover.md
A	history/conversations/2026-08-04-0445PDT-repair-closed-review-receipts/handover.md
A	history/conversations/2026-08-04-0504PDT-repair-review-receipt-normalization/handover.md
A	history/conversations/2026-08-04-0600PDT-repair-review-receipt-markdown-aliases/handover.md
A	history/conversations/2026-08-04-0601PDT-repair-review-receipt-source-allowlist/handover.md
A	history/conversations/2026-08-04-0626PDT-repair-review-receipt-raw-identity/handover.md
A	history/conversations/2026-08-04-0655PDT-repair-review-receipt-ascii-authority/handover.md
A	history/conversations/2026-08-04-0731PDT-repair-review-receipt-open-containers/handover.md
A	history/conversations/2026-08-04-0806PDT-repair-review-receipt-pending-html/handover.md
A	history/conversations/2026-08-04-0840PDT-repair-review-receipt-linear-mapping/handover.md
A	history/conversations/2026-08-04-0903PDT-repair-review-receipt-composite-claimants/handover.md
A	history/conversations/2026-08-04-0929PDT-checkpoint-review-receipt-claimant-precompute/handover.md
A	history/conversations/2026-08-05-1330PDT-continue-review-receipt-parser/handover.md
A	history/conversations/2026-08-09-1439PDT-agent-instruction-audit/handover.md
A	history/conversations/2026-08-09-2300PDT-apply-agent-instruction-defaults/handover.md
A	memory/decisions/2026-08-09-agent-instruction-defaults.md
M	memory/index.md
A	memory/known-issues/2026-08-07-withdrawn-panel-grammar-reopens-two-branch-edges.md
M	memory/known-issues/install-symlinks-windows.md
D	message-queue/needs-agent/requests/non-blocking-pick-up-make-linked-worktree-bootstrap-concurrency-safe.md
A	message-queue/needs-agent/requests/non-blocking-pick-up-migrate-the-review-verdicts-heading.md
A	message-queue/needs-agent/requests/non-blocking-pick-up-stop-workspace-boundary-tests-from-flaking-under-sharding.md
M	message-queue/open-actions.md
M	roadmap/current-state.md
M	services/quote-api/AGENTS.md
M	services/quote-cli/AGENTS.md
M	skills/adversarial-review/SKILL.md
A	tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/design.md
A	tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/plan.md
A	tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/task.md
A	tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/verification.md
A	tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/worklog.md
A	tasks/0_backlog/2026-08-16-stop-workspace-boundary-tests-from-flaking-under-sharding/task.md
D	tasks/1_in-progress/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/plan.md
D	tasks/1_in-progress/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/worklog.md
D	tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/plan.md
D	tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/worklog.md
A	tasks/3_in-review/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/design.md
A	tasks/3_in-review/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/plan.md
R100	tasks/1_in-progress/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/task.md	tasks/3_in-review/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/task.md
A	tasks/3_in-review/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/verification.md
A	tasks/3_in-review/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/worklog.md
A	tasks/3_in-review/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe/design.md
A	tasks/3_in-review/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe/plan.md
R067	tasks/0_backlog/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe/task.md	tasks/3_in-review/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe/task.md
A	tasks/3_in-review/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe/verification.md
A	tasks/3_in-review/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe/worklog.md
A	tasks/3_in-review/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/design.md
A	tasks/3_in-review/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/plan.md
R060	tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/task.md	tasks/3_in-review/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/task.md
A	tasks/3_in-review/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md
A	tasks/3_in-review/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/worklog.md
A	tasks/3_in-review/2026-08-09-refactor-agent-instructions/design.md
A	tasks/3_in-review/2026-08-09-refactor-agent-instructions/plan.md
A	tasks/3_in-review/2026-08-09-refactor-agent-instructions/task.md
A	tasks/3_in-review/2026-08-09-refactor-agent-instructions/verification.md
A	tasks/3_in-review/2026-08-09-refactor-agent-instructions/worklog.md
M	templates/task/verification.md
```
