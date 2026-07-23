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

## 2026-07-23 — contract hardening round three (codex subagent)

- Closed the terminal-review omission: `approved`, `rejected`, and `abandoned` now
  reject `Successor action`, while `changes-requested` and legacy `not-approved`
  require a same-timing successor. Staged schema, committed-range deletion, and exact
  synthetic-merge regressions cover approval.
- Added an independently activated, sticky handover action-entry schema. Human entries
  copy the linked creation-snapshot `Action`, `Why-you-might-care`, and
  `If-you-do-nothing` fields in a fixed suffix; agent entries contain only the exact
  Action-labeled link. Pre-activation v1 records are grandfathered, both schema markers
  resist partial removal, and deleting the whole history service still no-ops.
- Reconciled task/blocker semantics with the task contract. A reciprocal blocking item
  may remain linked to `1_in-progress` only after a committed one-line agent
  `open` → `in-repair` claim or an answered human `waiting` → `folding` claim;
  waiting, open, staged-only, preclaimed, and unanswered states still require
  `2_blocked`.
- Added creation-snapshot, link-borrowing, extra-ask, actor, duplicate, ordering,
  marker-removal, whole-service-removal, terminal-outcome, and active-claim regressions.
  The action-projection suite passed 49 tests, the queue suite passed 177 tests, the
  full runner passed 5/5 files, and the reconciler reported 0 findings.

## 2026-07-23 — merge-history and retry lifecycle hardening (codex subagent)

- Made queue-resolution and handover-schema activation discovery traverse full merge
  history and retain every incomparable marker-bearing activation. Each mutation or
  handover creation is governed when any activation is its ancestor, so an independently
  adopted side branch cannot escape while pre-adoption commits stay grandfathered.
- Kept merge simplification for handover `--diff-filter=A` incarnation selection and
  added `--no-replace-objects`; full-history there can select bytes from an unmerged
  competing add. Added a competing-add regression that preserves the selected lineage.
- Preserved first-response immutability. A human counter-question is claimed and folded
  into durable evidence, then continued through a new same-timing item whose
  `Supersedes` points to the resolved action; the folding claim remains status-only.
- Required every manual retry to declare non-queue `Resolution evidence` while live.
  Recognized reconciler-generated and legacy retries keep their finding-clearance
  exception, and a claimed manual retry resolves only with changed named evidence.
- Added independent-activation and exact TREESAME v1-to-v0 merge regressions for queue
  deletions, orphan handovers, and sticky marker removal. Nine focused regressions and
  the complete queue suite passed: 185 tests in 41.951 seconds. The system `python3`
  was Python 3.7 and could not parse an existing walrus expression, so verification
  used `/Users/quentinmiao/.local/bin/python3.13`.

## 2026-07-23 — external action-projection hardening (codex subagent)

- Moved action-token normalization into shared Markdown semantics. Inline-code
  contents, Unicode words, and symbols now survive normalization; only structural
  Markdown links lose their destinations, so `staging` cannot bind to `production`.
- Broadened orphan-action detection to ordinary `please <verb>`, let-me-know,
  keep-me-posted, modal, and first-person requests while preserving declarative and
  request-predicate-negated prose.
- Made rendered HTML detection include human-visible control and accessibility
  attributes. Strict handovers additionally reject raw HTML in action entries from
  the raw section source instead of interpreting arbitrary markup.
- Added provider-neutral external-action and additional-prose environment inputs.
  The thin workflow adapter now validates the pull-request title, requested reviewers,
  requested teams, and assignees on assignment and review-request state changes.
- `python3 -m unittest automation.tests.test_check_action_projection` passed 56 tests;
  seven focused strict-handover tests passed, and Ruby parsed the workflow YAML.

## 2026-07-23 — projection grammar and provider-comment boundary (codex subagent)

- Classified explicit human obligations such as “a maintainer should select” and the
  elliptical request “Feedback welcome” without treating descriptive system behavior
  as a human action.
- Replaced blanket question-mark detection with punctuation-aware detection, so actual
  questions remain actions while query tokens such as `?foo` do not make an ordinary
  title actionable.
- Exposed one rendered-prose action API for strict handover boundaries; it sees visible
  raw-HTML text and accessibility attributes while ignoring hidden elements and code.
- Added an opt-in provider boundary for issues, reviews, and comments: a missing action
  section is allowed only when body, additional prose, and external assignment state
  contain no action signal. Pull-request descriptions remain strict by default.
- `python3 automation/tests/test_check_action_projection.py` passed all 59 tests;
  `py_compile` and `git diff --check` passed for the focused projection files.
- A pre-freeze follow-up made action direction explicit. `needs-human` remains the
  default, `needs-agent` requires an exact canonical Action label, and `any` lets each
  canonical queue path declare its own actor for mixed issue/conversation surfaces.
- List-prefixed feedback invitations and “Feedback/Reviews are welcome” now count as
  asks. Query tokens and quoted literal question marks stay descriptive while terminal
  questions still count. The expanded projection suite passed all 63 tests.

## 2026-07-23 — GitHub durable-action surface adapter (codex subagent)

- Moved authoritative pull-request description, title, requested-reviewer, team, and
  assignee projection to `pull_request_target`. It executes default-branch/base code,
  fetches the event's merge ref only as Git data, and verifies the fetched object
  against the payload's immutable test-merge revision.
- Split `issue_comment` by artifact. Issue comments inspect the event's default-branch
  commit; pull-request conversation comments fetch the current merge candidate.
  Issue and conversation surfaces accept either queue actor because GitHub identity
  does not determine who acts next; formal reviews require `needs-agent`.
- GitHub exposes no `pull_request_review_target` or
  `pull_request_review_comment_target`. Those event checks are explicitly advisory:
  they check out base code and use read-only permissions, but a proposed workflow can
  evade dispatch. This is not admission proof. The provider boundary follows GitHub's
  documented [`pull_request_target` trust model](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target).
- A `changes_requested` review is external agent-action state; approval and comment
  reviews remain neutral unless their body contains an ask. Seven step-scoped static
  tests cover the event, candidate, actor, and assurance matrix.
- Formal review and review-comment bodies deliberately pass the repository default
  branch as a non-task scope. Each inbound surface validates only the actions it
  carries; the outbound pull-request description remains task-scoped and complete.
  A two-action task regression proves that one linked inbound agent action passes
  unscoped while the same subset fails under `task/<id>`.
- `python3 -m unittest automation.tests.test_check_action_projection
  automation.tests.test_github_action_projection_workflow` passed all 71 tests
  (64 projection and 7 provider-matrix tests). Ruby parsed all three workflow jobs,
  `py_compile` passed for both focused test files, and `git diff --check` was clean.

## 2026-07-23 — activation-join lifecycle hardening (codex subagent)

- Made displaced-tip continuity apply when queue v1 is active on either the old or new
  history. A force-pushed replacement can no longer activate v1 while discarding a
  still-live action filed on its pre-v1 old tip.
- Made newly admitted handovers governable when their creation and schema activation
  are parallel histories joined by the candidate. Same-lineage handovers created
  before activation remain legacy records.
- Required concrete `Why-you-might-care` and `If-you-do-nothing` fields on every live
  human item under queue v1. Existing items may gain them without changing identity
  only on the exact v0-to-v1 activation edge; later framing rewrites remain blocked.
- Applied the shared rendered-action grammar to strict handover prose outside
  `Needs your attention` and `Next steps`, including visible raw-HTML accessibility
  text that could otherwise hide an unqueued ask. Newly strict handovers now reject
  raw HTML outside code everywhere, because HTML-contained fake Markdown headings can
  desynchronize raw and semantic section boundaries.
- Bound every queue action identity to its next-actor folder and typed leaf. Exact
  path-only slug clarifications within the same actor and leaf remain valid; actor
  reassignment, leaf reclassification, and content-changing renames do not.
- Limited mutable `Agent notes` to retry items. Manual retries may append plain
  diagnostic prose through claim and resolution, but structured bold-key fields are
  rejected across every notes section, including duplicate sections and nested headings.
- The final focused boundary and lifecycle tests passed. The complete queue suite
  passed all 200 tests in 96.097 seconds; the expected fail-closed Git-snapshot
  diagnostics were emitted by negative-path tests.

## 2026-07-23 — root pre-freeze integration

- Rejected the first immutable candidate after three fresh adversarial reviewers found
  concrete provider, projection, and Git-lifecycle bypasses. Every repair invalidated
  that panel; none of its verdicts will be counted as approval.
- Ran two additional read-only repair audits before refreezing. They closed task-wide
  inbound-review overprojection, actor/leaf reassignment, structured retry-note hiding,
  and raw-HTML parser desynchronization. The final lifecycle audit passed 16 focused
  cases; the final provider audit found one subset bug, which was repaired and bound by
  the 71-case combined projection/provider suite.
- Root verification on the integrated unstaged tree passed 64 action-projection tests,
  seven GitHub adapter tests, and 200 queue/history tests. The repository-wide runner
  then passed all six discovered test files: the same automation suites, 55 core-scope
  cases with one intentional skip, five quote-api tests, and three quote-cli tests.
- Updated durable design and Git workflow guidance to distinguish actor direction and
  authoritative default/base-context checks from advisory direct-review event checks.

## 2026-07-23 — repair claim lineage (codex subagent)

- Preserved committed `open` → `in-repair` and `waiting` → `folding` receipts across a
  later identity-preserving slug rename in the same actor and typed leaf.
- Prevented a new identical action, an ambiguous duplicate, or a different merge parent
  from lending its claim history: rename inference now requires a unique disappeared
  path on a single-parent edge, while merge traversal follows exact paths only.
- Reused the existing negative actor, typed-leaf, and content-rewrite tests and added
  agent, human, duplicate, copy, and two-parent merge regressions. `py_compile`,
  `git diff --check`, and all 205 queue/history tests passed.
- Session handover:
  `history/conversations/2026-07-23-1130PDT-repair-claim-lineage/handover.md`.

## 2026-07-23 — provider action cardinality and command grammar (codex subagent)

- Replaced the external-action boolean with provider-neutral cardinality. Each material
  top-level array entry counts once, a material object or scalar counts once, and
  repeated environment inputs add their counts; distinct canonical queue paths must
  cover the result.
- Made present human-dependent boundary statements action-like, including blocked,
  pending, stop/wait, and cannot-continue forms with direct or reverse human-review
  complements. Historical and explicitly negated boundary descriptions remain prose.
- Recognized common base-form work imperatives on optional comment surfaces while
  preserving noun-like and third-person summaries such as “Audit logs,” “Review
  status,” “Adds support,” and “Fixes parsing.”
- Added array, repeated-input, duplicate-record, duplicate-link, object, scalar,
  nested-empty, two-reviewer CLI, boundary, imperative, and false-positive regressions.
- Made supporting-link classification structural: only declarative `Source:`,
  `Context:`, `Details:`, `Reference:`, or `For context:` fields whose link closes the
  line may exempt one ambiguous noun title. Questions, TODOs, unambiguous commands,
  imperative cues, and trailing actions remain queued actions.
- Closed noun-summary conjunction hiding: a finite summary followed by `and` plus an
  existing command is actionable, without treating plural-subject descriptions as
  commands. Queue-link labels use the same grammar and preserve action multiplicity.
- `python3 automation/tests/test_check_action_projection.py` passed all 72 tests;
  `python3 automation/tests/test_github_action_projection_workflow.py` passed all seven
  adapter tests; `py_compile` and `git diff --check` passed.
- Session handover:
  `history/conversations/2026-07-23-1131PDT-repair-provider-action-cardinality/handover.md`.

## 2026-07-23 — requested-change actor routing (codex subagent)

- Routed every `changes-requested` and legacy `not-approved` resolution through one
  newly introduced, same-timing `needs-agent` repair action. The repair alone owns the
  concrete `Action`, stable `Full context`, dependency boundary, and non-queue
  `Resolution evidence`, and points back to the resolved review with `Supersedes`.
- Preserved the unaccepted review boundary by requiring the repair to link one distinct
  newly introduced human review item. It starts `awaiting-artifact`, depends on
  the repair, retains the same context and timing, and cannot duplicate the repair
  action.
- Added regressions for a human-only successor, an agent-only successor that drops
  re-review, missing action/evidence, preclaimed repair, changed boundary/context,
  preexisting successor, legacy outcome, and duplicate repair/review actions.
- Recorded the correction in
  `memory/decisions/2026-07-23-requested-review-changes-route-through-agent-repair.md`;
  the prior decided ADR remains byte-for-byte unchanged.
- Six focused lifecycle test methods passed, then all 208 queue/history tests passed in
  98.178 seconds. `py_compile`, `git diff --check`, and the reconciler also passed with
  zero findings.
- Session handover:
  `history/conversations/2026-07-23-1200PDT-repair-requested-change-actor-routing/handover.md`.

## 2026-07-23 — final provider-projection gap repair (codex subagent)

- Treated every visible unchecked Markdown task-list item as an explicit pending
  action, independent of its verb. Checked historical items and task syntax inside
  fenced, inline, or indented code remain non-actions; existing noun-summary and
  third-person negatives remain accepted.
- Normalized detection-only visible prose with Unicode NFKC and removed format/default-
  ignorable characters after Markdown destinations and code were excluded. This closes
  the exact `Rev<U+200B>iew this change.` bypass without changing structural evidence
  or literal examples.
- Added provider-neutral external assignment envelopes with exact `needs-human` or
  `needs-agent` direction and opaque identity. Per-actor cardinality now requires one
  distinct actor-matching canonical queue link per assignment; directionless state on
  a mixed-actor surface fails closed.
- Updated the GitHub adapter to map `User` accounts and requested teams to
  `needs-human`, map `Bot` accounts such as
  `copilot-pull-request-reviewer[bot]` to `needs-agent`, and fail unknown account
  types or missing identities closed. PR task scope still requires its existing human
  actions, while the mixed surface uses exact `No queued action requested.` when empty.
- Updated provider guidance and added unchecked/checked task, Unicode
  obfuscation/literal, mixed assignment, malformed actor, distinct-cardinality,
  task-scope, command-line, and workflow mapping regressions.
- `python3 -m unittest automation.tests.test_check_action_projection
  automation.tests.test_github_action_projection_workflow` passed all 87 tests
  (79 projection and eight provider-adapter tests) in 27.777 seconds. System Python
  3.7 `py_compile`, Ruby workflow YAML parsing, exact jq actor mapping, and
  `git diff --check` also passed.
- Direct strict-handover validation returned no entry problems, projected the exact
  six-of-six live human queue paths in canonical order, and found no action prose
  outside the projection sections. The full reconciler could not read either untracked
  new handover from its Git candidate snapshot because this repair was required to
  remain unstaged; full reconciler evidence therefore belongs to the later staged
  integration snapshot.
- Session handover:
  `history/conversations/2026-07-23-1200PDT-repair-final-projection-gaps/handover.md`.

## 2026-07-23 — agent obligation and task projection repair (codex subagent)

- Extended the shared rendered-action grammar with provider-neutral direct obligations
  for agents, assistants, bots, and workers, including optional role descriptors.
  Present direct work remains actionable; negated, historical, automatic-system, and
  capability descriptions remain ordinary prose.
- Classified present first-person curiosity, interest, and wondering as indirect
  solicitations only when they target a recipient's thinking, approach, feedback,
  input, or opinion. The same grammar now rejects these asks outside the declared
  action section and as extra unlinked asks inside an otherwise linked entry.
- Made `Queue actions` a closed task projection: exactly lowercase `none`, or unique
  backticked canonical queue paths separated by semicolons or commas. Provider task
  scoping and the reconciler share one parser, and duplicate fields, bare paths,
  trailing delimiters, mixed `none`, and appended prose now fail closed.
- Updated the task contract and template to expose the enforced syntax. An independent
  bounded retest passed all 22 agent-obligation, solicitation, and task-integration
  cases.
- `python3 automation/tests/test_check_action_projection.py` passed all 83 tests;
  `python3 automation/tests/test_github_action_projection_workflow.py` passed all
  eight adapter tests; and `python3 automation/tests/test_reconcile_queue.py` passed
  all 209 queue/history tests with zero reconciler findings. `py_compile` and
  `git diff --check` also passed.
- Session handover:
  `history/conversations/2026-07-23-1312PDT-repair-agent-obligation-task-projection/handover.md`.

## 2026-07-23 — provider summary and task-scope repair (codex)

- Split provider title summaries from ordinary action prose: conventional change
  titles remain valid, while questions, TODOs, authority commands, explicit
  obligations, conjoined asks, and present courtesy requests still require queue
  projection.
- Made obligation parsing preserve capability/system descriptions while recognizing
  direct hard prohibitions and work requests after common modifiers. Reported
  historical courtesy prose remains non-actionable.
- Bound conventional branch names to the one task identified by changed task records
  or any embedded canonical `task:` commit token. A task-named branch is cross-checked
  against the same immutable base/candidate evidence; conflicts, multiple tasks,
  missing trusted range input, and ancestry errors fail closed.
- Made inbound issue/comment/review surfaces explicitly unscoped: they enforce every
  ask they carry without pretending to project a task's complete `Queue actions`.
- Two independent preflight reviewers reproduced the original bypasses, then passed
  the repaired scope, conjunction, modifier, reported-speech, and hyphen-separator
  cases.
- `python3 automation/run_tests.py` passed all six test files: 89 projection tests,
  55 core-scope tests (one skip), eight GitHub adapter tests, 209 queue/history tests,
  five quote API tests, and three quote CLI tests. Python compilation, Ruby workflow
  parsing, and `git diff --check` also passed.
- Session handover:
  `history/conversations/2026-07-23-1349PDT-repair-provider-summary-task-scope/handover.md`.

## 2026-07-23 — panel-ten provider and history repair (codex)

- Rejected visible action headings and common look/chime/weigh/ping requests outside
  the declared action section while preserving descriptive headings and PR summaries.
- Required every scoped external assignment to consume a distinct task-owned queue
  action of the matching actor; an unrelated global queue item no longer satisfies a
  PR assignment.
- Required immutable task evidence for every PR branch, including `task/<id>`, and
  rejected missing, conflicting, or multi-task scope before projection.
- Made governed v1 handover paths single-incarnation across staged, range, and
  parallel-history checks. Deletion remains allowed, and a pre-activation legacy
  incarnation may be reused after activation.
- The three blocking reviewers' exact heading, idiom, assignment, branch-evidence,
  and valid delete/re-add cases were reproduced. Bounded rechecks passed the provider
  repairs. `python3 automation/run_tests.py` passed all six files: 92 projection,
  55 core-scope (one skip), eight provider-adapter, 214 queue/history, five quote API,
  and three quote CLI tests.
- Session handover:
  `history/conversations/2026-07-23-1411PDT-repair-panel-ten-blockers/handover.md`.
