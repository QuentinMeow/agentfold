# Worklog — Make the message queue the first-class interaction surface

## 2026-07-23 — first-class-message-queue (codex)

- Verified from GitHub and Git ancestry that merged PRs #4 and #6, including their final
  heads, are present on the fast-forwarded local `main`.
- Began three independent read-only audits: historical review-question intent, queue
  schema/naming blast radius, and every path that can create an unqueued human action.
- Found the first concrete gap: the original queue item requested only a generic
  acknowledgement, while later PR-only questions introduced new judgments without the
  choice explanations, examples, or canonical queue links required by the decision guide.
- Transcribed the owner's answers into three queue items while they were waiting,
  claimed them in separate status-only commits before folding, and pushed those
  coordination commits directly to `main`.
- Completed independent audits of the historical agent reasoning, live-action surfaces,
  and naming/check blast radius. The “blocking claims” question was an agent-owned
  consistency audit; the other jargon-heavy prompt was at least three separate reviews.
- Chose queue-owned actions with actor/kind/timing encoded independently, recorded the
  superseding ADR, and split the unanswered guardrail judgments into five context-rich
  future-blocking review items. A sixth item owns review of this queue-contract change.
- Folded the confirmed universal four-mode semantics into the guardrail design and
  deleted the three resolved queue projections.
- Updated root/leaf contracts, all queue schemas, task and handover schemas, the
  operating guides, four portable skills, and the personal GitHub-summary skills.
  GitHub-specific action projection remains outside AgentFold core.
- Added mechanical checks for routed/prefixed queue files, class contradictions,
  zero-context human explanations, live task links, exact blocked-task reciprocity,
  dependency-aware staleness, and versioned handover projections. Generated retries
  preserve claimed/annotated state and only garbage-collect reconciler-owned files.
- Added 21 focused queue/handover tests. An independent automation review found seven
  first-pass gaps (including retry clobbering, rogue endpoints, and date-boundary
  behavior); all were repaired before the implementation commit.
- Audited 36 stop/reject claim units in the guardrail design. All 17 normative
  transition-stopping claims were correctly scoped to `hard`, a profile requiring hard
  controls, or provider authority; four excerpt-level ambiguities were clarified.
- A five-lens adversarial review began with three independent blockers. It found
  provider-date coupling, strict endpoint lock-in, hidden Markdown evidence, invalid
  date crashes, ambiguous task boundaries, retry collisions/staleness, an unqueued
  backlog action surface, a contradictory deletion ADR, premature reviewability, and
  unenforced future start boundaries.
- Reworked the implementation around a shared CommonMark semantic parser,
  repository-local handover adoption, extensible typed leaves, exact scoped transition
  tokens, reciprocal backlog pickup requests, artifact-gated reviews, and managed retry
  projections. Every reproduced failure now has a regression test.
- Confirmed the exact heads and merge commits of PRs #4 and #6 are ancestors of `main`;
  moved the completed core-portability task from review to done.
- A second hostile audit found ambiguous pickup inference, incomplete handover
  projection, symlink-backed evidence, mutable review targets, non-task branch failure,
  and several missing regression canaries. Pickup identity is now explicit; reviews
  bind to exact bytes/object ids; new handovers match the complete live human queue;
  queue/context evidence must be regular repository files.
- Added regressions for inline/escaped/indented/fenced Markdown disguises, invalid and
  oversized paths, broken symlinks, immediate transition blockers, non-task branches,
  legitimate active-task follow-ups, response revision binding, and exact new-handover
  projection. The full repository test runner passed 4/4 files (55 core-scope tests
  with one skip, 50 queue tests, 5 quote-api tests, and 3 quote-cli tests).
- Later adversarial rounds found that range checks were not bound to the checked-out
  candidate and that queue deletion trusted only the final label. Range mode now
  accepts only its exact head or exact two-parent synthetic merge, requires a clean
  candidate, and reads a captured index/HEAD snapshot.
- Made queue-resolution activation sticky and history-aware. Ordinary actions require
  a committed one-line claim plus changed non-queue evidence; review approval
  revalidates the target, non-approval leaves a same-boundary successor, pickups prove
  the atomic backlog move, and generated retries prove both exact identity and a
  cleared named finding. Malformed paths and unreadable historical state fail closed.
- Added the provider-neutral external action-projection gate and a thin GitHub adapter
  that reruns on PR-description edits. A missing “What to review” acknowledgement,
  an orphan question, a hidden link, or a dead/wrong-actor queue link now fails CI.
- Updated the personal `write-github-pr-summary` skill outside AgentFold so repositories
  that require an explicit no-action acknowledgement receive one; the repo contains no
  Codex-specific policy.
- Final hostile passes reproduced action-rewrite, response-rewrite, unrelated-successor,
  premature retry deletion, reserved-basename, projection-link, and timing-rename
  failures. The lifecycle now checks every committed mutation edge, follows a claim
  across identity-preserving timing renames, freezes the first response and review
  binding, requires a newly introduced same-context successor, and evaluates retry
  clearance at the exact deletion commit.
- The external projection gate now reads task and queue bytes from one explicit
  immutable candidate, accepts repo-relative links or explicitly bound absolute links,
  rejects hidden fenced/HTML evidence and action-like prose outside its declared
  section, and permits declarative context without treating it as another ask.
- Preserved adoption flexibility: custom typed-leaf `README.md` files remain
  documentation, non-task branches do not inherit unrelated actions, pending legacy
  reviews need no eager migration, and every action mechanism remains filesystem- and
  Git-based. The full runner passed 5/5 files: 33 projection tests, 55 core-scope tests
  (one skipped), 146 queue tests, 5 quote-api tests, and 3 quote-cli tests.
- The first immutable release panel blocked `8fcbd54` with three concrete cases:
  a first response could rebind an already-published review, a PR action could borrow
  an unrelated live queue link or hide in passive prose, and removing the entire
  optional queue service still triggered its historical anti-downgrade check.
- Review bindings are now write-once after the sole awaiting-artifact-to-waiting
  publication edge. External action labels use a deterministic canonical prefix or
  leaf-specific neutral label, and common passive, first-person, and actor-obligation
  asks are checked both outside and inside the declared action section.
- Whole-service removal now disables the queue lifecycle check, while removing or
  weakening the v1 marker inside a retained queue service still fails. Focused repairs
  raised the suites to 40 action-projection tests and 149 queue tests; the full
  repository runner again passed 5/5 files.

## 2026-07-23 — lifecycle hardening round two (codex subagent)

- Added the only safe review-binding reversal: an unanswered `waiting` review retracts
  to `awaiting-artifact` with pending/blank response fields, then publishes its new
  binding in a separate commit. Direct rebinds, publication-plus-answer, post-answer
  retraction, and same-edge rebind-plus-approval remain invalid.
- Split review outcomes into `approved`, `changes-requested`, `rejected`, and
  `abandoned`. Only requested changes require a same-timing successor; rejection and
  abandonment are terminal, while legacy `not-approved` retains requested-change
  behavior for historical compatibility.
- Added provider-neutral `--displaced-tip` admission. A divergent replaced ref now
  compares its old snapshot with the new range head as preservation-only continuity;
  ordinary PR base/head divergence is untouched, and GitHub push/PR-synchronize
  adapters fetch the old object or fail closed.
- Removed the empty-candidate early return from queue resolution. Deleting an
  empty/resolved queue service passes, deleting one with blocking, non-blocking, or
  malformed live actions fails, and partial v1-marker removal remains an anti-downgrade
  finding.
- Added focused lifecycle, outcome, force-push, adapter, and service-removal
  regressions. `python3 -m unittest automation.tests.test_reconcile_queue` passed all
  159 tests; Ruby parsed `.github/workflows/harness.yml` successfully.
