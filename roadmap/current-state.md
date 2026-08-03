# Current state

**Last-updated:** 2026-08-02

What is true today, mapped to the desired-state lines.

- **Structure**: all eleven top-level folders exist and follow their own contracts;
  `docs/designs/` holds durable proposals separately from principles and ADRs; the
  bootstrap task (`2026-07-22-bootstrap-the-harness`, in `tasks/4_done/`) is the worked
  example of the full lifecycle.
- **Enforcement**: `automation/reconcile/reconcile.py` checks queue/task/memory/handover
  schemas, queue timing names/fields, task↔queue links, new handover projections, link
  targets, line budgets (AGENTS.md, SKILL.md, root README), memory expiry, and
  dependency-aware stale items. Findings carry a severity derived from their check id:
  the age-driven ids in `ADVISORY_CHECKS` report visibly but never fail `--check`, so no
  calendar date can turn an unchanged clean tree red, and `--fail-on-advisory` is the
  opt-in for maintenance runs. A check that cannot run at all exits 2 with one line
  naming the file or check, and findings stream as they are produced, so one failure
  cannot discard the rest. Visible CommonMark is the evidence boundary; task
  admission rechecks every post-activation Git edge and task-local Markdown artifact
  for named transitions and newly introduced human asks. Queue deletion is bound to
  claims, distinct evidence, still-crossed task/merge receipts, withdrawn negative targets,
  displaced-ref continuity, and checked pickup/retry exceptions. UTC dates are checked;
  arbitrary event/transition/operation evidence is agent-attested unless an adapter
  validates the boundary. Empty
  queue-service removal remains modular but cannot erase a live action. It files
  collision-safe, aggregated retry projections while preserving actor notes. A separate
  Git boundary gate requires
  substitution evidence for core diffs and rejects obvious user-global access in
  tracked executables. Its token-expensive independent review mode is manually invoked
  outside the gate; `--require-review` validates a revision-bound receipt, while
  pre-commit and CI report that the manual review was not invoked by default. They still
  run repository tests across services, skills, and automation. A provider-neutral
  external-action gate binds PR prose to an immutable candidate, makes each declared
  action entry link one live human queue item, and rejects action-like prose outside
  that section. Provider sources always retain an actor-correct version binding even
  when their prose directly links the queue; the GitHub workflow is a thin event
  adapter. Its two admission jobs no longer read a merge revision the payload has not
  computed yet: each binds the candidate through the merge commit's own parents, whose
  object ids that commit's identifier already covers, so the binding is knowable on the
  first event. Pull requests opened after that merged are green on both.
  No template↔check drift detection yet.
- **Test gate cost (2026-07-30)**: three measured changes are merged. The runner no
  longer interposes a /bin/sh script named `git` on the child path, so a Git call is
  one process instead of two; the reconciler reads blob bytes through one reusable
  `git cat-file --batch` reader and caches facts under immutable object IDs; and
  `--staged` maps every staged path through an input-ownership table, so a records-only
  commit selects no test at all and names every file it skipped. A records-only
  pre-commit run measures 0.02s in the test step. The complete local suite is still
  ~120s serially, with system time above user time, so it remains bound by process
  creation rather than computation. Sharding below the file, background-maintenance
  isolation, in-process fixture history and a machine-independent link check are now
  merged too; measured together the complete suite ran in 38.31s against 124.77s serial
  in the same session, and later sessions on the same host measure it between 25s and
  50s, so only same-session pairs compare. Investigation, the levers, and the one
  approach ruled out by measurement: `docs/designs/fast-local-test-feedback.md`. The
  action-projection gate's own per-path Git reads are the open item, in review at 84
  processes down to 2 per run.
- **Skills**: five portable skills ship (`ask-me-anything`, `explain-to-human`,
  `session-handover`, `adversarial-review`, `memory-gardener`) as agent-agnostic SKILL.md
  protocols; the gardener is a protocol only — no script yet. Each treats the message queue
  as the canonical action surface and external prose as a linked projection.
- **Coordination**: every pending human action and durable cross-session agent action
  has one canonical queue file. Actor and message kind remain folder routes; filename
  prefixes expose blocking now, blocking at a future boundary, or never blocking.
  Tasks declare live queue actions, every unclaimed backlog task has an agent pickup
  message, and human items mechanically require differences, a concrete example, an
  unattended/boundary outcome, and a full-context pointer. Reviews cannot accept a
  response before their exact artifact exists.
- **Answering (2026-07-31)**: a human answers any item in one edit — one sentence in the
  response blank, committed while `waiting`, and a path named inside it is prose rather
  than a link claim. A review's `Reviewed revision` and `Review outcome` are supplied by
  the agent's `folding` claim, admitted only over an already-committed response, only on
  that edge, only once, and only repeating the frozen `Review revision`; both are still
  required before the item may resolve or cross a boundary. Whether the recorded outcome
  truthfully reads the human's sentence is an agent attestation, recorded as a known
  issue rather than implied. Every `templates/queue/` file is copy-and-fill valid, with
  no field a check reads left inside an HTML comment. PRs #7, #11, and #12 are admitted on
  main; their still-unanswered human review items are now bound to immutable ranges
  without treating those provider merges as review answers. PRs #8 and #10 landed on
  PR #7's already-merged branch and were superseded by the hardened main recoveries.
- **Stuck queue state (2026-07-31)**: the agent request whose repair merged before its
  deletion could be attempted is resolved, and its task
  (`2026-07-25-fix-handover-projection-code-span-copy`) is done. The three merge reviews
  whose ranges are already ancestors of main are measured, not forced: replaying
  `--at-transition merge` reports all three unresolved, a fresh approval cannot satisfy a
  merge that already happened, and deletion is refused. They stay live and unanswered, with
  one canonical item under `message-queue/needs-human/decisions/` carrying their
  disposition; their three tasks stay in `tasks/3_in-review/` with the measurement recorded
  in each worklog.
- **Contract text (2026-07-31)**: contract precedence is stated in exactly one file,
  `handbook/principles/folder-as-a-service.md`, after root `AGENTS.md` and
  `handbook/AGENTS.md` spent a while deferring to each other in a loop. The queue
  delivery-prefix rule was restated in thirteen live contracts and had already drifted in
  five; it now lives only in `message-queue/AGENTS.md` and every other file links there.
  Contracts no longer claim in the present tense that retries are auto-filed, that guard
  modes are configurable, that a third branch lane exists, or that link-check is
  unqualified — the same claim inside `handbook/principles/eventual-consistency.md` is
  waiting on a human decision, because principles are near-immutable. ADRs gained
  `**Amends:**`/`**Amended-by:**` for a partial reversal, and `memory/index.md` marks an
  amended decision `[amended]` so an overturned clause is no longer advertised as live.
- **Example code**: `services/quote-api` + `services/quote-cli`, stdlib-only, tested,
  cross-linked contracts.
- **Design review (2026-07-22)**: a full grill of the harness — report in
  `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md` —
  found the eventual-consistency-vs-blocking-gate contradiction plus honesty and
  wording gaps. Wording gaps fixed on main; a ninth principle
  (`handbook/principles/provenance-over-position.md`) added; six hardening tasks
  filed in the backlog (desired-state line 7).
- **Guardrail proposal review (2026-07-22)**: the owner approved the provenance
  principle wording and narrowed the critical-obligations proposal to template-first,
  universally mode-configurable guards (`hard`, `soft`, `off`, `manual`);
  independent-agent review is manual by default and sandboxing is deferred. On
  2026-07-23 the owner confirmed the four universal semantics; the proposal now defines
  composable guard bindings, derived assurance reports per obligation and scope,
  template-first adoption, evidence authority, detector failure, and incident recovery
  with separate examples. Controlled egress is reference-only and requires a separate
  explicitly approved design.
- **Stacked review publication (2026-07-24)**: authority and scope are recorded in
  [the direct-main coordination decision](../memory/decisions/2026-07-24-direct-main-coordination-push-authorized.md).
- **Layered workspace proposal (2026-07-24)**: the durable design in
  `docs/designs/layered-development-workspace.md` replaces the unsafe ignored nested
  mirror sketch with a private integration checkout, external no-Git zones, a clean
  distinct-object-store publisher, explicit provenance/failure states, and a separate
  capability-isolation requirement. A manually invoked read-only topology inspector
  now verifies only declared root/Git-metadata separation and reports every stronger
  claim as uninspected, unverified, or blocked. Its six follow-up tasks are now live in
  backlog with queue-owned pickups and mechanical start dependencies; manifest work
  remains blocked until the parent review is explicitly resolved and the parent task
  reaches done. Admitted sessions, mounts, export, and publication are not yet real.
- **Markdown edge graph (2026-07-25)**: the owner answered all eight open decisions and
  they are folded into three ADRs — the accepted architecture in
  [the edge-graph architecture decision](../memory/decisions/2026-07-25-markdown-edge-graph-architecture.md),
  plus the repo-root path-type default and the author-one-direction rule. The design is
  in `docs/designs/markdown-edge-graph.md`. Stage 0 is implemented on pull request 13 and
  not merged: heading anchors are now validated inside `link-check`, closing a hole where
  a link carrying a fragment had neither its path nor its anchor checked; a stdlib
  advisory co-change mining CLI walks git history and always exits 0; and an append-only
  accept/reject ledger beside it now holds 29 real verdicts. The gating experiment
  measured 3.4% effective false positives over 29 judged candidates but 10.0% over the
  default report's top ten, which is the probation trigger, so the verdict of record is
  to **narrow**: a reduced Stage 2, no Stage 3, half of Stage 4. The owner answered both
  narrowing decisions and they are folded into
  [the freshness-mode amendment](../memory/decisions/2026-07-25-edge-graph-freshness-modes-after-measurement.md)
  and [the artifact-storage amendment](../memory/decisions/2026-07-25-edge-graph-artifact-storage.md):
  the `each-run` freshness mode and the committed graph artifact are both recorded as not
  implemented rather than rejected, each with a stated revisit trigger. The two deferred
  stage requests that asserted those decisions were still open were retired and re-filed
  with corrected context, because a live queue item's action text cannot be edited in
  place. The Stage 0 transcripts are still owed, and mining also surfaced a live drift
  plus a fivefold restatement now filed as `2026-07-25-single-source-queue-prefix-rule`.
  The mining task reached `tasks/4_done/` on 2026-08-01 without closing that gap, so the
  ordering action that held the backfill task unclaimed is resolved on its own terms
  (2026-08-02): its verification file was re-read, and all four owed sections — the
  anchor-hole before-state, both new `link-check` findings, and the `agents-budget` run
  over `automation/AGENTS.md` — are still absent, so the backfill task's scope narrows to
  nothing and stands at four. `grep -n "agents-budget\|link-check"` over that file matches
  only the header sentence that says they are missing. The backfill task
  `2026-07-25-complete-stage-0-verification-transcripts` is now claimable through its
  pickup request alone, and no session can now collide in that file, because the task that
  owned it is done.
- **Task scope at the pull-request boundary (2026-08-01)**: the projection gate and the
  reconciler required opposite things of the same commit, and six open pull requests were
  stopped by it. `check_queue_task_reciprocity` requires a live queue item declaring
  `task:<id>` to appear in that task's `Queue actions`, so filing one edits a second task's
  record; the projection gate then refused the candidate outright — exit 2, not a finding —
  for mapping to more than one task folder. Plural scope is now ordinary: the gate binds
  every task the trusted range carries, a task-named branch must be among them, and the
  projection covers the union. The merge boundary had the same root and now skips an
  unanswered action the range itself filed, matched by action identity so a timing
  escalation still counts, and never an answered one. Replaying all six pull requests:
  three pass, two report a finding about their own description, and one is still refused
  because its branch names a task filed in no commit on any branch. Still over-broad, and
  written down rather than fixed: a `task:<id>` merge boundary activates for any non-task
  branch that edits that task's record.
- **Human-attention format (2026-07-31)**: the owner's review of the first-class
  message-queue contract is resolved. The contract was accepted and its presentation was
  answered `changes-requested` on 2026-07-26 — the files "read like a database record",
  putting machine bookkeeping ahead of the question and leaving past, current, and
  proposed behavior undistinguished. That response had been committed only onto
  the task/2026-07-23-first-class-message-queue branch, a branch never pushed and 77 commits behind
  `main`, so every copy reachable from `main` still read `pending` and handovers kept
  re-asking a question already answered. The response is now transcribed byte-exactly onto
  main-line, the review is folded, and the repair it demanded is live as
  `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md` with
  its promised re-review. An action-first format is designed but not adopted: the
  implementation on that stale branch is design input only, because its 1,849-line
  `automation/markdown_semantics.py` rewrite was blocked by its own adversarial parser lens
  three times and never tested against the current reconciler.
- **Human gating (2026-08-01)**: nothing a human owes holds a Git edge. A
  `needs-human/` item may withhold only the start of a task still in `0_backlog` or one
  act with no undo; `transition:merge|review|complete` and `Blocks now: task:<id>` are
  unspellable there, `4_done` tests the agent's obligation rather than the human's
  satisfaction, and every human item carries an advisory `Answer by:` date. `needs-agent/`
  timing is untouched. The repair was forced by a real deadlock: two reviews bound
  `transition:merge` on ranges already merged into `main`, and their cleanup required a
  merge that had already happened, so they could be neither resolved nor deleted — and the
  decision filed to dispose of them bound `transition:complete` on the same three tasks it
  asked about. Four live items were migrated on a one-time schema-activation edge, with
  every committed human response byte-identical afterwards; both stranded reviews are still
  unanswered and are now answerable at any time. What this does **not** do is make any of
  it enforceable: the `main-projection` ruleset is still `enforcement: disabled` with no
  required check, so every merge gate here remains advisory until the owner answers
  `message-queue/needs-human/decisions/non-blocking-turn-on-the-merge-gate-this-repository-already-runs.md`.
  Two known gaps stay written down rather than papered over: an agent `future-blocking`
  item bound to `transition:merge` still gates its own task's merge by design, and an
  immutable field on a live item has no legal repair (`memory/known-issues/`).
- **Handover entry grammar (2026-08-01)**: an immutable record is judged by the marker its
  own creation snapshot declared, so a schema version withdrawn before the record existed —
  or activated in parallel history and joined at the merge — no longer demands a spelling
  the record could not have used. Two live failures forced it: PR #44 reported nine blocking
  findings on a handover it could never legally repair, and one record already on `main`
  carried the same latent failure. The anti-dodge property survives as a separate ratchet:
  which *rejections* a record owes still comes from the highest version the admission edge
  reaches, so cutting a branch early evades none, and those rejections now fire at v2 *or
  later* rather than only at an exact v2 — a bug that had silently disabled the raw-HTML and
  origin checks the moment `main` moved to v3. All 66 handovers reachable from `main` already
  matched their own creation marker; no committed bytes changed
  (`memory/decisions/2026-08-01-immutable-records-are-judged-at-their-written-grammar.md`).
- **Enforcement (2026-08-02)**: the owner decided the merge gate stays advisory while the
  repository is immature — merging is possible with a red check, because the development cycle
  is mostly agents and speed matters more right now than a hard stop. Recorded in
  [the advisory-gate decision](../memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md),
  with the stated exit: require `reconcile-and-test` with a personal bypass once he judges the
  repository stable. Until then a green trunk is evidence about the last push window only, so
  the merged result is verified before landing rather than the branch alone. Approval
  classification stays attested by the same decision round.
- **Not yet real**: one-command adoption installer, eval canaries, packaged
  layered public/private workspace, queue viewer, design-review hardening — see
  `desired-state.md` lines 3–8.
- **Explaining the work (2026-08-02)**: `skills/explain-to-human/` states one standard for
  everything a human reads — three layers, effect before mechanism, a before and an after
  per change claim, glossed local vocabulary, one worked example, calibrated uncertainty,
  and self-containment on the decision with evidence linked — and routes to one scenario
  file per surface: pull-request body, chat reply, human queue item, handover. A
  pull-request body has a schema (`templates/pull-request.md`) projected into
  `.github/pull_request_template.md` and proven against the existing action-projection gate
  by ten tests. `handbook/human-action-guide.md`, `message-queue/AGENTS.md`, and
  `handbook/decision-guide.md` were rewritten to obey the rules they state; a rule-by-rule
  inventory and an independent audit of that rewrite are committed as task evidence.
  Publishing the branch and reporting to the owner are now steps 8 and 9 of the
  end-of-session ritual. None of the readability rules is machine-checked; whether any
  should be is a live decision under `message-queue/needs-human/decisions/`.
- **The two agent actions pinning the first-class-queue task (2026-08-02)**: one is
  disposed of and one is deliberately not, and the task stays in `tasks/3_in-review/`
  because of the second. The continuation action asked an agent to finish PR #7's review
  and record its independent panel *before merge*; PR #7 merged on 2026-07-24 as `2372e48`,
  an ancestor of `main`, seven days before the human review it was waiting on was even
  folded. Two of its three `Done when` clauses were met — the response is folded, and the
  review stayed bound to its exact candidate range — and the third can never be met. What
  was skipped is recorded rather than implied: **no final independent adversarial panel
  verdict was ever taken on PR #7**, the task's own `verification.md` says so in the words
  it was written in ("a fresh final immutable-revision panel is intentionally deferred
  until after the first human review"), and that deferral outlived the merge. The action is
  resolved against this file; the merge itself is not un-crossed by resolving it. The
  human-side twin of the same question, for three merge reviews rather than an agent
  request, is still the owner's and is still live under
  `message-queue/needs-human/decisions/`.
  The second action, the human-action redesign, stays live and is **not** satisfied by
  pull request 56. That pull request landed the format and its enforcement, but the
  action's `Done when` also requires "every live unanswered human-attention file is
  migrated to it", and PR #56 deliberately migrated none: its own task records "It does not
  touch a single live item", and an independent review had broken the fenced migration
  carve-out that would have allowed it — with every frozen field byte-identical and the
  reconciler clean, a rewrite could still change the question, invert a scope limit, delete
  a choice, and flip the recommendation. Ten of the thirteen live human-attention files are
  still in the format the owner rejected. So the promised re-review stays
  `awaiting-artifact` with a pending binding rather than being published against PR #56:
  the artifact still missing is the countersigned migration of those live files, which is
  owner-gated twice over, by backlog task `2026-08-01-countersign-the-live-human-item-migration`
  and by the live decision `non-blocking-re-ask-the-older-questions-in-plainer-words.md`.
  The redesign action's `Follow-up review` still names the pre-rename path of that review
  and cannot be corrected while the item lives — attempting it reports
  `queue-resolution: action identity changed while the queue item remained live`, which is
  instance 2 of `memory/known-issues/2026-08-01-an-immutable-field-cannot-be-repaired-on-a-live-item.md`.
- **The three pull requests the repaired scope gate refused (2026-08-02)**: all three are
  terminal, and the repair the request named can no longer be performed on any of them.
  `gh pr view` reports 41 `MERGED` at 2026-08-01T22:18:06Z as `84e3524`, 45 `CLOSED` at
  2026-08-02T00:10:37Z, and 46 `CLOSED` at 2026-08-02T03:25:14Z. Rewriting a "What to
  review" section on a merged or closed candidate changes no gate and reaches no reviewer,
  so the projection repair 41 and 45 needed is unreachable rather than outstanding. 45 was
  not abandoned: its head branch `harness/2026-07-31-fold-answered-queue-review` was
  republished as PR 53, which merged on 2026-08-02 — the rebuilt-pull-request half of the
  deleted-base-ref incident `handbook/git-workflow.md` records. 46 is the other half: its
  base was that same branch, and deleting the base on 53's merge closed it in the same
  second, unreopenably.
  The branch `task/2026-07-31-redo-stranded-review-disposition` no longer exists —
  `git branch -a` and `git ls-remote --heads origin` both fail to list it — so the request's
  first clause ("carries its own task record or no longer claims to be a task branch") is
  satisfied by the branch's absence rather than by filing anything. Its task record was
  never filed and still exists in no commit on any ref, and its single commit `694b26d` is
  not an ancestor of `main`. Nothing was lost with it: its purpose was to file the
  disposition decision for the stranded merge reviews, and that decision is live on `main`
  as `message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md`,
  filed instead by `4d2f8aa harness: activate human gating v1 and free four crossed boundaries`.
  The gate limitation recorded above is unchanged by any of this; what is resolved is the
  repair request, not the over-broad `task:<id>` merge boundary it was filed beside.
- **Six task branches published after an unplanned machine stop (2026-08-02)**: a crash left
  six branches in flight. Nothing was lost and every one is now on `origin` behind a pull
  request — 65 through 70. Two carried uncommitted worktree changes that are now committed
  with the design and verification records they lacked: the merge-ref bound's missing upper
  end (a bound above 2^63-1 made `[` report status 2, which `if` and `while` both read as
  false, so the step skipped its guard and every iteration and published an empty revision
  at exit 0) and the explanation-shape rule's imitation hole (a new agent item that copied
  one legacy field line from the single live legacy request switched the rule off for
  itself). Three of the six show one red `reconcile-and-test`, all three the same stale-base
  race and none of them the branch's own doing: on the identical commit the `push` and
  `pull_request_target` events pass and only `pull_request` fails, at the step that reads a
  `base.sha` GitHub has already moved past. That race is filed as
  `2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check` and is not repaired here.
- **Archive tags are no longer laptop-local (2026-08-02)**: of the six archive tags the
  2026-08-02 branch-clearing session created to preserve retired branch content, only one
  had ever been pushed. All six are now on `origin`, together with eight new
  `archive/2026-07-27-test-gate-stash-<0..7>-<slug>` tags holding intermediate states of the
  shelved test-gate task. Those eight were previously reachable only through the stash
  reflog — one `git gc` or one stray `git stash drop` from gone — and they carry files no
  other tag contains. The task they belong to stays in `0_backlog` with its
  re-measure-before-implementing notice intact; the tags are reference, not a starting point.
