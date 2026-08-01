# Current state

**Last-updated:** 2026-07-31

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
- **Skills**: four portable skills ship (`ask-me-anything`, `session-handover`,
  `adversarial-review`, `memory-gardener`) as agent-agnostic SKILL.md protocols; the
  gardener is a protocol only — no script yet. Each treats the message queue as the
  canonical action surface and external prose as a linked projection.
- **Coordination**: every pending human action and durable cross-session agent action
  has one canonical queue file. Actor and message kind remain folder routes; filename
  prefixes expose blocking now, blocking at a future boundary, or never blocking.
  Tasks declare live queue actions, every unclaimed backlog task has an agent pickup
  message, and human items mechanically require differences, a concrete example, an
  unattended/boundary outcome, and a full-context pointer. Reviews cannot accept a
  response before their exact artifact exists. PRs #7, #11, and #12 are admitted on
  main; their still-unanswered human review items are now bound to immutable ranges
  without treating those provider merges as review answers. PRs #8 and #10 landed on
  PR #7's already-merged branch and were superseded by the hardened main recoveries.
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
- **Not yet real**: one-command adoption installer, eval canaries, packaged
  layered public/private workspace, queue viewer, design-review hardening — see
  `desired-state.md` lines 3–8.
