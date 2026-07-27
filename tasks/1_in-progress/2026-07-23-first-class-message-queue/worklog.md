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
  used a local Python 3.13 interpreter.

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

## 2026-07-23 — assignment identity binding repair (codex)

- Preserved external assignment identity and role instead of reducing provider state
  to actor cardinality. Every assignment now consumes one distinct queue item whose
  `External assignment` field exactly matches the adapter's opaque binding.
- Made the GitHub adapter distinguish pull-request reviewer, requested team, PR
  assignee, and issue assignee bindings, including human/bot actor kind and login/slug.
  The canonical gate remains provider-neutral and treats the binding as opaque data.
- Classified present `Assigned to <identity>` and `Assignee: <identity>` prose as an
  action while preserving nobody, historical, and previously-assigned descriptions.
- Updated queue templates, contracts, human guidance, task design, workflow tests, and
  projection regressions. The blocking reviewer's exact unrelated-assignment and
  named-person prose cases passed bounded recheck; 93 projection and eight adapter
  tests passed with Python compilation, workflow parsing, and diff checks. The full
  runner then passed all six files, including 55 core-scope tests (one skip), 214
  queue/history tests, and both quote-service suites.
- Session handover:
  `history/conversations/2026-07-23-1428PDT-repair-assignment-identity-binding/handover.md`.

## 2026-07-23 — human-judgment vocabulary repair (codex)

- Extended the shared human-action noun grammar with advice, guidance, opinion,
  perspective, take, thoughts, and view so indirect “we need your …” judgments cannot
  remain only in provider prose.
- Added exact view/opinion/perspective/thought/take regressions while preserving
  descriptive view prose. All 93 projection tests and the blocking reviewer's bounded
  exact-case recheck passed.
- Session handover:
  `history/conversations/2026-07-23-1437PDT-repair-human-judgment-vocabulary/handover.md`.

## 2026-07-23 — review-event and courtesy-request repair (codex)

- Extended indirect-request detection so evaluative phrasing such as “it would be
  great/useful if …” cannot leave a durable action only in provider prose.
- A bounded recheck found that a failed review-event job could be bypassed by pushing
  an unrelated candidate because the next run did not replay earlier review state.
  Replaced one-event checking with current-state replay on direct events and every PR
  update, plus a trusted base-owned replay on PR target updates.
- Added opaque, content-versioned `External source` bindings so an agent can transcribe
  uneditable human review prose into one or more queue items. Effective formal reviews
  and unresolved diff threads remain active until provider state resolves them; the
  GitHub adapter paginates and fails closed using only its ephemeral workflow token.
- The workflow, automation contract, Git guidance, and task design state the remaining
  trust ceiling: candidate-context direct-event checks are not evidence against hostile
  workflow tampering without a separately controlled provider gate.
- Added exact request-phrasing and workflow-contract regressions. The focused suite
  passed 101 tests, Python compilation, Ruby workflow parsing, and `git diff --check`.
- Session handover:
  `history/conversations/2026-07-23-1445PDT-repair-review-state-replay/handover.md`.

## 2026-07-23 — named modal addressee repair (codex)

- The first exact-revision panel reviewer found that a modal request addressed to a
  named group, “Could the security team sanity-check this,” passed without queue
  projection because the actor grammar recognized only generic role names.
- Extended provider-neutral action addressees to named teams and organizational groups,
  explicit `@` handles, indefinite people, and one- or two-token named identities.
  Preserved declarative past-tense controls and added the exact reported regression.
- The repair invalidated the entire five-reviewer panel; a fresh panel is required on
  the next immutable commit.
- Session handover:
  `history/conversations/2026-07-23-1521PDT-repair-named-modal-addressees/handover.md`.

## 2026-07-23 — free-form modal addressee repair (codex)

- The next exact-revision panel reviewer showed that enumerating organizational suffixes
  was still incomplete: “platform engineers,” “security guild,” and “release managers”
  could carry review requests without queue projection.
- Replaced that suffix dependency for modal requests with a bounded free-form addressee
  followed by a recognized action verb. Expanded the narrow work vocabulary for common
  evaluation verbs and hyphenated check forms.
- Preserved negated requests and capability questions as negative controls. All 99
  projection tests passed, including the exact missed phrases and adjacent controls.
- This repair invalidated the entire panel again; no earlier verdict counts toward the
  required exact-revision review.
- Session handover:
  `history/conversations/2026-07-23-1544PDT-repair-freeform-modal-addressees/handover.md`.

## 2026-07-23 — hard obligation and explanatory-question repair (codex)

- The first reviewer of `bdbc3a94` found two opposed contract failures: a hard
  pre-merge obligation addressed to “the security guild” could remain issue-only, while
  a self-answered “Why this approach?” explanation was rejected as a human action.
- Added a bounded free-form fallback only for present hard obligations with a recognized
  action and an explicit lifecycle deadline. It excludes soft design language,
  capabilities, negation, past tense, and reported speech.
- Added a narrow exemption for immediately self-answered `how`/`what`/`why` explanations
  with non-action explanatory predicates. The answer remains in the classifier, so a
  later directive, approval requirement, decision question, or additional question
  still requires queue projection.
- All 100 projection tests passed, including both exact reviewer reproductions and the
  focused positive/negative matrix. The block invalidated the entire panel.
- Session handover:
  `history/conversations/2026-07-23-1612PDT-repair-obligation-explanation-boundary/handover.md`.

## 2026-07-23 — obligation synonym and CommonMark repair (codex)

- The first reviewer of `cd1e9341` found four adjacent failures: `has to` and
  `is required to` hard obligations escaped, `no longer needs to` and “the memo noted”
  descriptions were false positives, and a self-answered explanation failed when its
  answer used a CommonMark soft line break.
- Added the two hard-obligation forms, blocked `no longer` from being consumed as an
  actor name, and expanded the bounded reported-speech cues. The high-confidence
  lifecycle deadline and action-verb requirements remain unchanged.
- Accepted one soft line break before the allowlisted explanatory answer while keeping
  blank or standalone questions actionable. The answer continues through the ordinary
  action classifier.
- Added end-to-end projection checks for every new positive and negative case. All 100
  projection tests passed; the reviewer block invalidated the entire panel.
- Session handover:
  `history/conversations/2026-07-23-1629PDT-repair-obligation-synonyms-commonmark/handover.md`.

## 2026-07-23 — obligation modifier and clause-boundary repair (codex)

- The first reviewer of `1887449a` found that a modifier inside `is required to`, an
  article inside the lifecycle phrase, and an inflected lifecycle word could bypass the
  high-confidence obligation fallback.
- Reused the shared obligation-modifier grammar inside passive hard obligations and
  normalized common articles and lifecycle inflections.
- A reported statement split by a CommonMark soft line break was falsely classified
  because matching restarted at the second source line. Reported-speech evidence now
  carries across soft line breaks within the same clause, but not across a sentence or
  paragraph boundary.
- Added exact end-to-end cases for every reported failure plus an adjacent inflection.
  All 100 projection tests passed; the reviewer block invalidated the whole panel.
- Session handover:
  `history/conversations/2026-07-23-1643PDT-repair-obligation-modifiers-clauses/handover.md`.

## 2026-07-23 — passive review-obligation repair (codex)

- Contract lens 1 passed exact commit `34fdf3f7`; provider/projection lens 2 then found a
  `COMMENTED` formal review whose passive hard obligation was replayed as a non-forced
  source but skipped by the core classifier.
- Added a high-confidence passive hard-obligation form using the same subject, modifier,
  reported-speech, lifecycle, and clause boundaries as the active fallback. The passive
  verb vocabulary is restricted to recognized review/work actions.
- Closed an adjacent false positive where modal free-form parsing treated `should be
  repairable before merge` as an addressee plus a distant merge command.
- Added collector, action-classifier, end-to-end projection, and non-forced external
  source regressions for the exact `This needs to be repaired before merge` review.
  All 101 projection tests and nine collector tests passed. Lens 2's block invalidated
  the full panel, including the earlier lens 1 pass.
- Session handover:
  `history/conversations/2026-07-23-1702PDT-repair-passive-review-obligation/handover.md`.

## 2026-07-23 — lifecycle-obligation shape repair (codex)

- Two fresh reviewers of `90d346d6` independently found that finite passive vocabulary
  still missed ordinary current requirements: passive approval, `needs fixing`, and
  `should be fixed`.
- Added a voice- and verb-shape-independent fallback whose evidence is the present
  obligation marker plus an explicit lifecycle deadline. It recognizes active, passive,
  gerund, approval-noun, and `needs a fix` forms without enumerating every action word.
- Kept precision boundaries for reported speech, negative need, `no longer`, capability
  requirements, and `-able` or `-ible` property descriptions. Removed optional-token
  backtracking that initially let `needs to be able to` evade the capability exclusion.
- Expanded end-to-end provider-source cases for passive approval, gerund fixing, and
  soft passive obligations. All 101 projection tests passed. Both blocking verdicts
  invalidated the full panel.
- Session handover:
  `history/conversations/2026-07-23-1719PDT-lifecycle-obligation-shape-coverage/handover.md`.

## 2026-07-23 — requirement-predicate and explanation repair (codex)

- Two fresh reviewers of `bdb8ae1c` found three remaining semantic shapes: a hard
  recognized action without a lifecycle phrase, a requirement predicate placed after a
  gerund or noun, and self-answered explanations beginning with `We use` or `By storing`.
- Removed the lifecycle requirement from the narrower recognized-action fallback, so a
  direct `must review` or `needs to review` obligation remains high-confidence on its
  own.
- Added a lifecycle-bound requirement-predicate form for required, necessary, mandatory,
  needed, pending, or outstanding work. This covers gerund work and review/sign-off
  nouns without pretending every noun phrase is an action.
- Extended self-answered explanations only to non-action first-person use predicates and
  `By <gerund>` implementation descriptions. Questions involving `you`, choices, later
  asks, or non-allowlisted answers remain actionable.
- Added exact action, explanation, provider-source, negation, and reported-speech
  regressions. All 101 projection tests passed; both blocks invalidated the panel.
- Session handover:
  `history/conversations/2026-07-23-1734PDT-requirement-predicate-explanation-coverage/handover.md`.

## 2026-07-23 — structural formal-review triage and unsuffixed obligations (codex)

- Two fresh reviewers of `89f9cb1a` showed that prose inference remained an unsound
  prerequisite for replaying non-empty `COMMENTED` formal reviews. They also found
  unsuffixed passive, gerund, noun, predicate, imperative, and negative-imperative action
  forms plus four ordinary self-answered explanations.
- Made every non-empty GitHub `COMMENTED` formal review a forced agent-triage source.
  The resulting queue action may be non-blocking; empty comments remain neutral,
  changes-requested and unresolved threads remain forced action state, and approval
  prose still uses ordinary classification.
- Removed lifecycle suffixes from recognized passive actions, added bounded gerund/noun
  and action-predicate obligation forms, and recognized direct `Add` plus `Do not`
  commands. Reported, negative, capability, and property controls remain.
- Replaced the explanatory answer-verb allowlist with a structural rule: a short
  self-answered `how`/`what`/`why` lead is explanatory unless it carries human-choice
  cues such as `you`, `your`, `recommendation`, `choice`, or a modal ask. The complete
  answer still runs through action classification.
- Updated task design and human/Git guidance for structural formal-review triage. The
  focused projection, collector, and workflow run passed all 118 tests. Both reviewer
  blocks invalidated the panel.
- Session handover:
  `history/conversations/2026-07-23-1751PDT-structural-formal-review-triage/handover.md`.

## 2026-07-23 — effective-review triage and clause-terminal obligation repair (codex)

- Two fresh reviewers of `d14568a1` found that non-empty approved review prose still
  depended on classification and that a shape-valid disagreement between GitHub's
  latest-review connections could leave changes-requested state non-forced.
- Made every non-empty effective formal review structural triage, regardless of review
  state. Changes-requested is forced even with an empty body directly from either
  connection, so provider connection disagreement cannot silently weaken it.
- Tightened boundary-free gerund and noun obligations to cases where the action phrase
  completes its clause. This retains `migration needs fixing` and `plan requires
  approval` while allowing technical contracts such as an algorithm requiring element
  insertion or a function requiring cache checks.
- Updated task design and human/Git guidance to describe the provider rule. The focused
  projection, collector, and workflow run passed all 118 tests. Both reviewer blocks
  invalidated the panel.
- Session handover:
  `history/conversations/2026-07-23-1806PDT-effective-review-triage/handover.md`.

## 2026-07-23 — activation-join and effective-source repair (codex)

- Three fresh reviewers of `3af20145` found that a synthetic merge could hide an
  unresolved action created and deleted on history parallel to queue-v1 activation, an
  opinion-only approved review used a weaker force policy, and `Kindly review ...`
  escaped provider-prose classification.
- Reused the existing activation-join predicate when enumerating queue lifecycle edges.
  A candidate that admits parallel history with v1 now governs that history, while
  sequential commits ancestral to every activation remain legacy.
- Centralized effective formal-review force policy in the validated source constructor,
  so both GitHub review connections force every non-empty effective review and every
  changes-requested review. Identical provider records still deduplicate by versioned
  identity.
- Added a bounded `kindly` courtesy-command form that recognizes known action verbs
  without classifying descriptions such as `Kindly worded review comments`.
- Added exact parallel-history, opinion-only, duplicate-source, blank-opinion,
  polite-command, descriptive-control, merge-edge, and legacy-history regressions.
  The focused provider/projection run passed 119 tests and the three queue lifecycle
  cases passed. All three reviewer blocks invalidated the panel.
- Session handover:
  `history/conversations/2026-07-23-1831PDT-activation-join-source-repair/handover.md`.

## 2026-07-23 — structural conversations and versioned history (codex)

- Three fresh reviewers of `6f9dc284` found that the full task range retroactively
  applied the latest action grammar to 18 immutable handovers, post-adoption edits to
  legacy handovers were unobserved, and unstructured GitHub comments could evade the
  finite prose grammar.
- Upgraded the action-entry contract to v2. V1 keeps its creation-time structural
  semantics; v2 adds action-origin and raw-HTML checks. Future rejecting grammar changes
  require a new version rather than reinterpretation of accepted records.
- Added Git-edge mutation scanning for every existing handover after queue-projection
  adoption. Staged, intermediate, real/parallel, and exact synthetic-merge mutations are
  rejected even for unmarked legacy paths; deletion remains the retention mechanism.
- Added a thin GitHub conversation adapter. Every nonblank issue/PR conversation
  comment becomes a content-and-update-versioned `needs-agent` source without English
  inference. Direct events use a fresh immutable default or open-PR merge candidate;
  current open-PR comments replay in both trusted-target and candidate contexts.
- Documented source lifetime: comment edits create new identities, deletion or artifact
  closure resolves the provider source, and current open-artifact bindings remain live.
- Added exact bypass, bot, blank, deletion, edit/reversion, event/API parity,
  pagination, malformed-input, workflow trust/candidate, v1/v2 epoch, staged,
  modify/restore, and parallel synthetic-merge regressions. All 23 GitHub adapter tests
  and all 219 queue/history tests passed. The three reviewer blocks invalidated the
  panel.
- Session handover:
  `history/conversations/2026-07-23-1916PDT-conversation-history-results/handover.md`.

## 2026-07-23 — artifact identity and boundary-receipt repair (codex)

- Replayed the unpublished task history without the transient edit/revert of an
  immutable earlier handover. The repaired tip retained the exact original tree and
  the full `acc23b6...1b40239` range reconciled with zero findings.
- A fresh three-lens panel rejected `1b402391`: assignment bindings could collide
  across artifacts, GitHub emits no thread-reopen Actions event, and a Git-range review
  could disappear before later unreviewed candidate changes.
- GitHub assignment identities now include the provider's stable artifact node plus
  role, actor kind, and principal. A cross-artifact unscoped-binding regression proves
  exact reuse fails.
- Review-state replay now includes merge-queue enqueue and states its honest ceiling.
  GitHub's native conversation-resolution rule owns the hard merge guarantee because
  workflow checks only describe state at supported events.
- Future-blocking Git-range approval is now a two-phase receipt. Fresh approval may
  satisfy the named boundary only on the same base with queue-lifecycle-only tail
  changes; the item remains live, and post-merge deletion needs a two-parent merge that
  carried its exact folding receipt. Focused assignment/workflow tests and the new
  candidate-drift/merge-receipt tests passed. The rejected panel was invalidated.

## 2026-07-23 — structural issue, source-release, and admitted-receipt repair (codex)

- A fresh three-lens review of `52f5b046` found five related bypasses: polite issue
  phrasing still depended on finite English classification; issue comments replayed
  only the triggering delta; pushes did not check removal of a still-current provider
  binding; timing renames could erase a future dependency; and a candidate-local merge
  could imitate the expected boundary receipt.
- Open issue artifacts are now forced, content-versioned, actor-neutral sources. The
  canonical queue path chooses the actor, and neither unknown prose nor the no-action
  acknowledgement can waive structural routing.
- Issue/comment runs now fetch the complete current artifact snapshot and overlay the
  triggering event without dropping peer comments. API/event disagreement, malformed
  deletion, pagination failure, repository mismatch, and unknown state fail closed.
- A provider-neutral exact-tree release gate detects disappearance of the final
  `External source` binding. The thin GitHub adapter resolves opaque global node IDs
  from trusted base code; an unchanged source blocks, terminal provider state releases,
  and an edit/supersession releases only after the candidate binds the current version.
  Pull-request admission checks this before merge; default-branch push replay is
  detection only, so hard assurance still requires protected required checks.
- Live timing now escalates monotonically and freezes with the first human response.
  Deletion follows lineage so a historical future boundary survives escalation.
  Post-merge cleanup counts only a receipt-carrying merge already present in the
  adapter-supplied admission base; a root range or candidate-local topology fails.
- Recorded the two-way-door lifecycle decision in
  `memory/decisions/2026-07-23-live-queue-obligations-only-weaken-with-evidence.md`.
  The full runner passed all 8 test files: 112 projection tests, 55 core-scope tests
  (one skipped), 24 collector tests, 9 workflow tests, 224 queue tests, 9 source-release
  resolver tests, and 8 service tests.

## 2026-07-23 — task-edge, cancellation, and durable-source repair (codex)

- Four independent exact-SHA lenses rejected `70249643`. They reproduced a task-review
  lifecycle deadlock, direct provider
  links with no release identity, task prose absent from queue projection, and
  final-tree-only task checks that missed intermediate crossings. The lifecycle lens
  also found blocking review deletion without freshness or cancellation evidence.
- Approval now remains live through the exact internal task transition or admitted
  merge that consumes it. Internal cleanup searches committed status history for the
  exact folding receipt; merge cleanup retains the stronger pre-admission-base rule.
  Rejection and abandonment change predeclared non-queue cancellation evidence.
- Task admission has an explicit repository-local activation marker. Every governed
  Git edge rechecks task structure, so move-and-revert history remains visible.
  A second edge check compares multisets of newly introduced human-action units across
  all five task artifacts. Ordinary agent plan work remains free-form; exact task-owned
  queue links are the only human-action projection.
- Every active provider source now carries an exact actor-correct `External source`
  binding even when provider prose directly links the queue. Presentation and durable
  release identity are separate, so later exact-tree admission can classify the final
  binding as current or released.
- Added focused root, staged, intermediate, projection-ownership, transition-receipt,
  post-hoc approval, negative-cancellation, and blocking-range regressions. The shared
  action grammar suite passed 118 tests; the queue suite passed 234 tests before the
  final focused additions. The rejected panel remains invalidated pending a fresh
  immutable candidate.

## 2026-07-23 — receipt-state and task-admission hardening (codex)

- Two read-only audits found five flaws: receipt rollback, overly broad task rewrites,
  arbitrary-byte merge cancellation, no cleanup path for unsupported future
  boundaries, and local target/evidence collisions.
- Task-lifecycle review now binds a stable local artifact and cleanup requires the task
  to remain past the exact receipt. Merge review binds a candidate range; rejection
  restores every reviewed proposal path to its base. Other negative boundaries require
  a withdrawn local target, while task rejection remains live until the task is removed.
  Every review predeclares distinct evidence; dates, escalated events, and adapter-named
  transitions have explicit approved cleanup paths.
- Task admission now catches marker removal/restoration and intermediate asks even when
  the whole task service is later deleted. Action-origin scanning covers every nested
  task Markdown artifact, resolves only real source-relative links, accepts exact
  canonical labels, and recognizes direct human assignment/prohibition without treating
  ordinary future-tense agent work or self-answered headings as human obligations.
- Added seven lifecycle/admission tests plus expanded action-grammar cases. The queue
  suite passed 244 tests, the projection suite passed 118, and the full runner passed
  all 8 test files after these repairs.

## 2026-07-23 — first human-review boundary (codex)

- Stopped expanding implementation after the owner flagged the near-100-file review
  surface and requested a human-review round before more hardening.
- Closed only the already reproduced lifecycle and topology defects: deletion receipts
  now use exact descendant snapshots; boundary target kinds are enforced; receipt
  lineage survives same-timing renames; negative cleanup proves withdrawal; task
  action accounting covers `.md` and `.markdown` across renames; and active deletion,
  task-id rename, illegal lifecycle jumps, unrelated queue ownership, and marker
  downgrade are rejected.
- The focused lifecycle set passed 13 tests. The focused task-topology set passed 9
  tests, and the complete queue suite passed 259 tests in 140.135 seconds.
- Deferred first-adoption scanning of unchanged legacy task asks and task-history
  performance work to task
  `2026-07-23-post-review-task-admission-hardening`, with its own non-blocking agent
  pickup message. No implementation of that follow-up began.
- Refreshed origin/main at `acc23b6289f5ca66744718af379aba0468be93e2`;
  the merged heads of PRs #4 (`999a6c4`) and #6 (`9e24478`) are ancestors of that
  exact main revision.

## 2026-07-24 — derived-assurance review and handoff (codex)

- Retracted the stale PR #7 range review before changing non-queue artifacts, preserving
  the review-binding lifecycle while the human review continued in chat.
- Recorded the owner's response, claimed it separately, and folded it into
  `memory/decisions/2026-07-23-assurance-profile-review-disposition.md`.
- Replaced selectable assurance profiles with composable guard bindings and derived
  evidence reports across the guardrail design, implementation task, and roadmap.
  Controlled egress is reference-only and needs a separate explicit approval.
- Fixed the generic-link checker so structured successor lifecycle fields do not prevent
  the claimed predecessor from resolving; added focused regression coverage.
- Retracted four stale reviews before changing their target, then republished those and
  the derived-assurance follow-up against the exact revised design digest.
- The latest pre-commit run passed all eight repository suites, including 262 queue
  tests; reconciler checks reported zero findings. All commits through `ef0e520` are
  pushed to the PR #7 branch.
- Left the derived-assurance exact-byte review waiting. The next agent must continue the
  owner's one-question-at-a-time review before publishing the final PR range or running
  the final immutable-revision panel.
- Session handover:
  `history/conversations/2026-07-24-0012PDT-derived-assurance-review-handoff/handover.md`.

## 2026-07-24 — stacked-publication-coordination (codex)

- Reconstructed the task's in-review status and continuation action directly on the
  live coordination lane without copying reviewed-system code to `main`.
- Kept the merge review artifact-pending because the final coordination base is not
  authorized or published yet. A later queue-only edge will bind the exact range after
  the approved base is incorporated into PR #7.
- Preserved both rejected local coordination histories for audit; neither was pushed.

## 2026-07-25 — post-merge state reconciliation (codex)

- GitHub records PR #7 merged into main as `2372e48` at `2026-07-24T20:54:57Z`
  from base `00690e8` and head `d7eefce`.
- Bound the existing merge-review item to that exact provider range. The blank human
  review field remains blank; the merge event is admission evidence, not an inferred
  answer, so this task remains in review.
- PRs #8 and #10 subsequently merged into PR #7's already-merged head branch as
  `d515d28` and `7fa18ca`; their hardened replacements reached main through PRs #11
  and #12.

## 2026-07-26 — action-first human review repair (codex)

- Recorded the owner's first review as changes requested, claimed it in a separate
  coordination commit, reopened the task, and created an agent-owned repair plus a
  not-yet-actionable follow-up review.
- Three independent Sol/xhigh agents researched human–AI interaction, audited the
  repository, and designed the replacement. All three approved the same action-first
  model before implementation began.
- Added Human action presentation schema v2 and Queue action-entry schema v3. Waiting
  files now lead with one action, present-versus-proposed state, symmetric outcomes,
  a recommendation with assumptions and uncertainty, and the consequence of silence;
  tracking details are collapsed at the end.
- Migrated exactly the six unanswered waiting reviews. The two answered/folding
  receipts and the artifact-pending follow-up were not presented as human work; the
  detector-failure receipt remained byte-for-byte unchanged.
- Added deterministic enforcement for lifecycle notices, heading order, symmetric
  choices, recommendation evidence, plain responses, unique visible references,
  collapsed tracking, safe migration, and waiting-only handover projections. A legacy
  artifact-pending review may adopt v2 only on its existing publication transition.
- The complete repository runner passed all 11 test files. The queue suite reached 309
  tests; focused integration also caught and repaired mixed timing-state leakage and a
  hidden-heading false positive before publication.
- The first immutable repair revision, `5a6d21a`, was blocked by both fresh reviewers.
  Human-UX review found broken relative links, evidence-poor recommendations,
  contradictory future-tense actions, and missing direct review evidence. Lifecycle
  review reproduced stuck waiting/folding and awaiting/waiting transitions, a removable
  v2 activation edge, and a response-free folding action hidden from handovers.
- Reworked the candidate around those failures: relative references now resolve from
  the queue file; reviews distinguish before/current/reviewed/not-included state;
  recommendations name evidence actually checked; status-managed presentation changes
  have narrow lifecycle paths; folding requires a real response; and v2 removal is
  rejected on every governed Git edge.
- The replacement revision `dc315f7` was also rejected by both fresh reviewers. The
  zero-context reviewer found two already-merged changes still offering fictional
  pre-merge outcomes and no clickable immutable range; the lifecycle reviewer showed
  that a legacy-format blank response could still be hidden by changing Status to
  folding after v2 activation.
- The third immutable candidate, `ca50208`, passed the complete gate but all five
  adversarial lenses blocked it. They found recommendation anchoring, biased wording,
  stale dependency claims, ambiguous choices, direct-to-folding creation, wrong-field
  responses, publication scope injection, provider-dependent Git links, doubled
  handover punctuation, and an unsafe exception that rewrote crossed review identities.
- Replaced the keyword-based identity exception with deterministic, activation-only
  wording transforms. Neutralized review language preserves the same three outcomes;
  post-merge wording is available only when Git proves the bound head was already
  admitted, and it does not authorize that past merge. Recommendations now present
  evidence and uncertainty before the conclusion, and creation, publication, response,
  option, artifact-link, and handover grammars have explicit negative regressions.
- The next frozen candidate, `850c48c`, passed the complete 11-file pre-commit gate but
  the first three fresh review lenses all blocked it. The zero-context reviewer found
  two projected actions that were opaque or logically biased. Lifecycle review proved
  that a root commit could create a v2 action directly in folding. Parser review
  reproduced negated recommendations, open-ended review dispositions, fake exact-
  artifact links, path-spelled duplicate references, punctuation-changing handover
  projections, and rejection of ordinary dotted prose.
- Repaired every reproduced defect. Root commits now produce an empty-tree creation
  edge; live projected actions use neutral plain language; decision and clarification
  recommendations have exact positive conclusions; review answers are closed to the
  three outcomes plus clarification; exact Git links are verified against the same
  repository or a structured local artifact; visible references are canonicalized;
  handover labels preserve punctuation; and the sentence scanner accepts versions,
  filenames, abbreviations, and Unicode punctuation.
- Candidate `9341801` passed the complete gate. Its zero-context UX reviewer approved,
  but lifecycle and parser reviewers found four further defects: custom human-action
  kinds could originate with an agent-authored folding response, malformed local-
  artifact URLs could crash validation, quote-adjacent sentence boundaries were
  misread, and recommendation sections allowed contradictory trailing prose.
- Extended lifecycle admission conservatively to every human-action kind and hardened
  artifact parsing, sentence boundaries, and recommendation-section purity with exact
  reproductions. Because the panel was not unanimous, no approval from that cycle was
  carried forward.
- Candidate `fcefb5d` passed the complete gate and its UX reviewer approved. The two
  enforcement reviewers nevertheless blocked it: the promised generic v2 layout for
  adopter-defined human kinds conflicted with the repeatable-field allowlist; rendered
  fenced or raw-HTML response prose could disappear from closed-disposition checks;
  abbreviation and embedded-question sentence cases were misclassified; and exact
  recommendation purity rejected normal Markdown wrapping used by the templates.
- Kept the lifecycle protections while admitting the generic custom-kind layout, and
  moved response, sentence, and recommendation checks toward rendered-content-aware
  parsing that permits wrapping but rejects extra visible instructions. No approval
  from the split panel was carried forward.
- Candidate `8383317` passed the complete gate and its UX lens approved. Lifecycle and
  parser lenses still blocked it because custom kinds did not inherit the generic
  decision recommendation rule, a blank line failed to end a wrapped recommendation
  value, a common `U.S. Supreme Court` sentence was rejected, and handover punctuation
  did not recognize Unicode or quote-closed question endings.
- Extended the generic custom-kind contract through recommendation validation, made
  paragraph boundaries terminate field continuations, refined abbreviation handling,
  and centralized rendered terminal-punctuation recognition for projections. The
  split panel's approval was not carried forward.
- Candidate `e6011fa` passed the complete gate and its UX lens approved. Lifecycle
  review then reproduced a pre-activation, in-range addition that smuggled an agent-
  authored approved response through a later v2 activation. Parser review found free
  rendered prose in structured state sections, ambiguity in acronym-based sentence
  heuristics, and missing CommonMark reference-style links in duplicate detection.
- Tightened selected-range admission without retroactively governing legacy history,
  and reopened the sentence/structured-content design with independent UX and parser
  review instead of layering another unprincipled English heuristic onto the schema.
  The split panel's approval was not carried forward.
- Both independent reviewers chose a bounded rendered-paragraph contract over further
  English sentence heuristics. Replaced the heuristic with deterministic paragraph
  budgets, made state/choice/recommendation/reference sections field-pure, preserved
  review explanation under an explicit `Additional context` field, and resolved full,
  collapsed, shortcut, and image references before duplicate checking.
- Extended selected-range creation checks to pre-activation commits inside the range,
  while grandfathering legacy additions wholly before the selected range. This closes
  the reproduced response-smuggling sequence without retroactively governing old
  repository history.
- Candidate `8bbaff8` passed the complete gate, but all three first-wave reviewers
  blocked it. They found an undocumented combined paragraph budget, a pre-activation
  rename-origin variant of response smuggling, visually blank field values, missed
  CommonMark autolinks, compatibility normalization that weakened exact prefix and
  handover copying, and source-markup characters counted as rendered length.
- Split the repair by ownership: canonical templates now state every budget and
  punctuation rule; range admission treats an external rename/copy into `needs-human`
  as a new origin; and rendered-text validation keeps exact source contracts separate
  from Unicode-aware blank/length checks.
- Candidate `af607bd` passed the complete gate and its UX lens approved. Parser review
  found a valid angle-bracket inline URL misclassified as an autolink. Lifecycle review
  found that activating v2 and then removing the whole queue service made the final
  tree look ungoverned, allowing an earlier fabricated response to disappear after
  boundary authorization.
- Made selected-range provenance depend on any activation inside the range, not only
  the final tree, while leaving modular whole-service removal otherwise intact. The
  Markdown resolver now gives an enclosing inline link precedence over angle autolink
  recognition.
- Candidate `f803f5f` passed the complete gate and its UX lens approved. Lifecycle
  review found a divergent direct-head range whose trusted base had v2 but whose head
  did not; the base governance was not enabling origin scans on the head. Parser review
  found that a valid Action containing literal brackets could not be represented as an
  exact v3 Markdown link label.
- Extended selected-range governance from the trusted base as well as selected-edge
  activation, and made handover exactness compare rendered Markdown label text so
  escaped literal brackets preserve the Action rather than changing it.
- Candidate `dea25d0` passed the complete gate, but all three first-wave lenses blocked
  it. Inline code/emphasis in an Action exposed a source-versus-rendered comparison
  mismatch; a displaced old tip with active v2 did not govern a rewritten candidate;
  and malformed bracket floods made the balanced link scanner quadratic.
- Aligned v3 projection on rendered Action and label text, extended governance from a
  validated displaced tip only when v2 remains active in its final tree, and replaced
  repeated failed label scans with bounded linear progression.
- Candidate `60b5cc8` passed the complete gate, but all three first-wave lenses blocked
  it. The clarification template wrapped its Action placeholder contrary to the
  one-line contract; presentation-v2 could activate without queue-resolution-v1 and
  skip response/folding mutation enforcement; and an Action-looking line inside an
  HTML comment made raw Action safety validation skip the real unsafe Action.
- Made the canonical placeholder one line, bound presentation v2 mechanically to the
  queue lifecycle schema with defensive resolution enforcement, and validate one
  comment-stripped raw Action line followed by its required paragraph separator.
- Candidate `411a223` passed the complete gate and its UX lens approved. Parser review
  found a visually duplicate Action hidden behind a zero-width format character and a
  safe comment literal inside inline code removed as if it were an HTML comment.
  Lifecycle review found an exact backward rollback range whose empty rev-list omitted
  the candidate head from both v2 dependency and response/folding mutation checks.
- Made selected-range enumeration inspect the exact head once even when a rollback
  range has no forward commits, and separated visible-structure normalization from
  code-span-aware comment masking in raw Action validation.
- Kept exact Action source authoritative while adding a separate structural scan that
  blanks closed code spans and removes Unicode format controls before duplicate-field
  detection. Literal HTML-comment syntax inside code remains literal, while real
  comments still have to occupy standalone source lines.
- Extended compact-paragraph validation to reject unclosed inline markup in the
  explanation as well as the Action. Added regressions for code-contained Action-like
  text, standalone and inline-adjacent comments, exact Unicode preservation, and ZWSP,
  ZWJ, word-joiner, and BOM disguises before and inside an Action label.
- Candidate `a641dd8` passed the complete gate, but all three fresh first-wave lenses
  blocked it. Lifecycle review found that clean padding after an invalid intermediate
  edge hid the earlier transition in a backward rollback range. UX and parser review
  found duplicate Actions disguised by non-`Cf` default-ignorable characters. Parser
  review also found contradictory visible content accepted in an extra disclosure
  block and quadratic resolution of ordinary Markdown links.
- Split the next repair by subsystem: selected-range history must cover every relevant
  candidate-ancestry edge, while presentation parsing must admit exactly one final
  tracking disclosure, share the full default-ignorable definition, and bound link
  resolution without changing valid Markdown precedence or exact Action identity.
- Repaired the presentation parser after the `a641dd8` review. A human-action file now
  admits exactly one canonical final tracking disclosure; extra, nested, incomplete,
  or mixed-case disclosure/HTML markup is rejected, while literal tags in closed code
  and comments remain inert. Tracking content is limited to its fields and comments.
- Centralized default-ignorable character handling for the structural duplicate-Action
  scan, including non-`Cf` characters, while preserving the exact Action source and
  leaving code spans outside that scan. Replaced repeated Markdown overlap scans with
  indexed spans while retaining inline-link, image, autolink, and reference precedence.
- Backward selected ranges now replay the governed candidate ancestry instead of only
  the exact rollback head. Activation filtering keeps pre-v2 legacy origins outside the
  new contract, while padded invalid lifecycle and dependency edges can no longer hide
  behind a later clean commit.
- The repair passed all 393 queue tests and all 11 repository test files. Direct action
  projection, reconciliation, compilation, diff, and exact temporary-index core-scope
  checks also passed; ordinary-link stress timings stayed approximately linear through
  6,400 links.
- Candidate `3a7b8cc` passed the complete gate, but all three fresh first-wave lenses
  blocked it. Lifecycle review found that removing and later restoring queue-resolution
  v1 did not expose the downgrade edge. UX found arbitrary visible instruction fields
  accepted inside Tracking. Parser review found field-looking continuations and
  Unicode-indented duplicate Actions, plus quadratic malformed raw-HTML scanning.
- Split the next repair by subsystem. Queue-v1 must be sticky across every governed
  edge. Visible and tracking sections need explicit field ownership independent of
  indentation tricks, and raw-HTML recognition needs bounded scanning without changing
  code, comment, autolink, or angle-destination semantics.
- Added an edge-level queue-resolution-v1 anti-downgrade check. Once v1 activates, a
  governed edge that removes its marker while retaining any queue service file now
  fails even when a later commit restores v1; duplicate traversal of the same edge is
  collapsed. Complete removal of an empty or resolved queue service remains modular.
- Added six focused regressions covering forward and root ranges, staged state,
  synthetic and padded backward candidates, displaced-tip continuity, presentation-v2
  dependency, whole-service removal/restoration, duplicate suppression, and
  preactivation grandfathering.
- Reverified the combined lifecycle and parser repair after the parser stabilized. All
  402 queue tests and 55 core-scope tests passed, as did normal and disposable-index
  reconciliation, disposable-index core admission, compilation, and diff checks.
- Closed the parser findings with an endpoint/state/timing-specific Tracking allowlist,
  a whole-visible-presentation field scan that treats Unicode blank prefixes and
  default-ignorables as detection-only structure, and explicit rejection of bold-key
  continuation lines. Exact Action extraction and literals in closed code/comments are
  unchanged; `Follow-up review` is not admitted as human Tracking metadata.
- Made inline raw-HTML span recognition consume each owned source range once. Nested and
  quoted malformed opener floods now scale approximately linearly while valid quoted
  tags, comments, autolinks, angle link destinations, and code keep their precedence.
  The integrated repository runner passed all 11 test files.
- Candidate `69952df` passed the complete gate, but all three fresh first-wave lenses
  blocked it. Lifecycle review found remove-and-restore downgrade history for handover
  schema markers. Parser review found option fields accepted in the response section
  and character-reference-encoded directives. UX review found Unicode line separators
  bypassing both visible-instruction detection and the Tracking allowlist.
- Split the next repair by subsystem. Handover markers need the same edge-level
  stickiness as queue schemas, while structural detection needs one rendering-aware
  line and entity model that remains separate from exact source extraction and binds
  every field to its owning section.
- Added retained-history edge walkers for both handover schema markers. Projection v1
  removal and any action-entry downgrade now fail on the exact governed edge even when
  later restored; duplicate traversal is collapsed, whole-history removal remains
  modular, and a validated displaced tip preserves its active schema requirements.
- Bound every active action-entry schema version to Queue projection v1 in each
  admitted staged, selected-base, selected-commit, synthetic/backward, and displaced
  state. A later repair cannot hide an intermediate orphan entry grammar.
- Added eight focused regression methods for forward/root remove-and-restore,
  v3-to-v2-to-v3, staged and padded rollback candidates, synthetic/displaced history,
  whole-service removal/restoration, preactivation legacy history, all three entry
  versions, and dependency repair. The stabilized combined repair passed all 412 queue
  tests and the complete core/admission checks.
- Bound response fields to their owning section for decisions, clarifications, and
  reviews. A detection-only visual-line model covers physical and Unicode line breaks,
  character-reference-encoded layout and labels, default ignorables, indentation, and
  code/comment exclusions without changing exact Action or metadata values.
- Added regressions for named and numeric entities, NEL/Zl/Zp boundaries, encoded
  newlines, wrong-section choice fields, every response kind/status, Tracking and
  compact-paragraph injection, ordinary entity prose, and code/comment literals. The
  bounded detection stress matrix remained approximately linear through 8,000 cases.
- The first exact staged gate after that repair failed one existing invalid-fence test,
  so no commit was created. A stray backtick in invalid fence info was pairing with a
  later metadata backtick and hiding fields across the intervening heading.
- Replaced the narrow exception with block-aware inline-code shielding. Unmatched
  backticks cannot borrow a closer across headings, blank lines, lists, quotes, rules,
  fences, reference definitions, or indented code; valid same-inline-block multiline
  code and encoded-line literals remain inert. Ten focused cases and all 414 queue
  tests passed on the repaired worktree.
- Candidate `297c4b5` passed the complete gate and its lifecycle lens approved. UX and
  parser lenses blocked it: alternate CommonMark emphasis still rendered hidden field
  labels, inline-code pairing remained document-global before boundary filtering, two
  crossed-merge reviews called live behavior proposed, and one Full context link did
  not explain its review judgment. No approval carried forward.
- Split the repair by ownership. Visible-field parsing must recognize every equivalent
  raw emphasis form and parse code independently per inline block. The two live reviews
  must describe current behavior as current and link the actual review context without
  changing Action identity or available outcomes.
- Structural field detection now recognizes underscore, triple, and nested raw
  CommonMark emphasis when their leading rendered label is schema-shaped; entity-made
  delimiters remain literal. Inline-code runs are parsed independently within each
  conservative CommonMark inline block rather than globally paired and filtered.
- Reworded the two crossed-merge reviews to call live behavior implemented/current and
  make rejection require rollback or reviewed replacement on `main`. The test-runner
  review now links its immutable design, verification, and root-cause record instead of
  an unrelated roadmap page. Action text and judgment outcomes remain unchanged.
- The combined repair passed 73 focused parser/presentation tests, all 416 queue tests,
  all 11 repository test files, direct v2 audits of both live reviews, reconciliation,
  compilation, and exact diff checks. Stress matrices remained approximately linear.
- Candidate `7fb6ff0` passed the complete gate, but fresh UX and lifecycle lenses
  blocked it and the parser lens did not approve. GFM table body rows could masquerade
  as top-level queue fields, a divergent candidate could reuse a displaced immutable
  handover path with different bytes, and the test-runner recommendation's final proof
  was not reachable from its stable references.
- Split the repair across block parsing, displaced-history immutability, and evidence
  presentation. Table bodies must remain block content, old-tip handover incarnations
  must constrain replacements, and the stable current-state reference must lead to the
  exact immutable implementation evidence.
- Added GFM header/delimiter and cell-count recognition, escaped/code-pipe handling,
  body consumption through the actual termination boundary, and whole-table inline
  block isolation. Table rows cannot satisfy top-level queue fields or shift later
  inline-code pairing.
- Extended immutable-handover checks to the displaced tip and candidate intermediate
  history. Independently recreated, edited, or renamed old-tip paths fail across v1–v3;
  unchanged shared incarnations, explicit deletion, preactivation legacy, and modular
  whole-history removal remain allowed.
- Kept the review's stable Full context identity and made its evidence reachable by
  linking the exact immutable implementation commit from the current-state record and
  stating the final focused, full-suite, real-worktree, and independent-review proof.
- The combined tree passed nine GFM cases, 30 handover/topology cases, all 428 queue
  tests in the final repository run, all 11 repository test files, projection and core
  suites, exact-index reconciliation, core admission, compilation, and diff checks.
- Candidate `6ba38d5` passed the complete gate, but all three fresh first-wave lenses
  blocked it. Raw-HTML/comment shielding still paired backticks across blocks; GFM code
  pipes were miscounted; immutable handovers could be renamed outside history;
  intraword underscores changed rendered identity; and the layered-workspace review
  overstated the independent-review evidence present at its exact head.
- Split the repair across shared block-aware code semantics, exact GFM delimiter rules,
  rendered identity, whole-tree rename discovery, and evidence wording. No live Action,
  review outcome, or recommendation conclusion changes.
- Made raw HTML and comment masking share the same per-inline-block code semantics as
  field detection. Unmatched backticks cannot hide later blocks, and GFM table cells
  now split on every unescaped pipe, including pipes inside code spans.
- Preserved literal intraword double and triple underscores in rendered identity while
  retaining valid boundary emphasis. The corrected layered-workspace review now cites
  only evidence present at its exact revision.
- Detected rename and copy operations whose source is an immutable handover even when
  the destination leaves `history/conversations/`. Staged, direct, synthetic,
  displaced-tip, backward, modified-byte, and multi-copy cases are covered without
  rejecting genuine deletion, whole-service removal, or preactivation history.
- The integrated repair passed 11 focused parser cases, 14 focused lifecycle cases,
  all 118 action-projection tests, all 442 queue tests, core-scope checks, normal and
  disposable-index reconciliation, core admission, compilation, and diff checks.
- Candidate `b5edef6` passed the complete gate, but all three fresh first-wave lenses
  blocked it. One review headline invited a yes/no answer opposite to its Approve
  outcome; a new identical handover was mistaken for mutation of its source; and GFM
  emphasis, link destinations, inline comments, and nested-delimiter performance had
  concrete parser defects.
- Split the repair across question polarity, governed-to-governed copy semantics, and
  a bounded GFM renderer/link/comment model. The next panel restarts from zero against
  one new immutable commit.
- Reframed the authority review headline so its question and Approve outcome have the
  same polarity; the other five waiting headlines already passed the same audit.
- Allowed a copy to create a well-formed new conversation handover while continuing to
  reject governed renames, external or malformed copies, edits, type changes, retired
  path reuse, and divergent-history escapes.
- Replaced approximate emphasis stripping with bounded GFM delimiter flanking and the
  rule of three, added balanced and escaped link destinations, and rejected inline HTML
  comments in strict handover entries. Stress coverage makes nested emphasis linear.
- The integrated repair passed 10 focused parser cases, 26 focused lifecycle cases,
  all 118 action-projection tests, all 452 queue tests, core-scope checks,
  reconciliation, compilation, and diff checks.
- Candidate `ebfe7d5` passed the complete gate. Fresh UX and lifecycle lenses approved,
  but the parser lens blocked, so the panel was not unanimous. Exact integrated
  reproductions found later rule-of-three checks using consumed delimiter lengths,
  semicolonless entities decoded beyond CommonMark, user-collidable code placeholders,
  and quadratic per-span restoration.
- Routed the repair to a segment-based CommonMark renderer with original delimiter-run
  metadata, exact character-reference grammar, collision-free code-span preservation,
  and scaling assertions. The next five-review panel again restarts from zero.
- Preserved original emphasis run lengths independently from consumed characters,
  implemented CommonMark's exact character-reference grammar, and replaced private-use
  placeholders with opaque code-span and autolink segments restored in one linear pass.
- Added integrated handover and external-projection regressions for rule-of-three,
  semicolonless/numeric entities, private-use Unicode, autolink contents, and scaling.
  All 119 projection tests and all 456 queue tests passed on the final restarted tree.
- Candidate `60fabe3` passed the complete gate. Fresh UX and lifecycle lenses approved,
  but the parser lens blocked after a 13,701-source CommonMark label-context
  differential. Complete handover reproductions exposed bracket-dependent emphasis,
  autolink precedence over code, and backslash-parity escape handling.
- Routed the repair to context-aware label rendering, owned-range autolink precedence,
  and linear escape-parity detection. The next five-review panel again restarts from
  zero.
- Rendered handover labels within their actual brackets, resolved opaque autolink/code
  ownership in source order, and replaced fixed lookbehind with backslash-parity
  detection. A suffix opener index keeps escaped-run adversaries linear.
- Exact integrated v3 and live-GFM differential fixtures now cover bracket flanking,
  autolinks containing backticks, and even-parity URI/email escapes. All 119 projection
  tests and all 459 queue tests passed on the final restarted tree.
- Candidate `3d7ffa7` passed the complete gate. Fresh UX and lifecycle lenses approved,
  but the parser lens blocked because a URI or email autolink inside the apparent
  queue-link label makes GFM split the outer link while the gate still assigned its
  visible text to that queue link.
- Routed the repair to rendered link-ownership validation with exact URI/email,
  escaped-angle, and code-span controls. The next five-review panel again restarts from
  zero.
- Made autolinks inside an apparent queue-link label own their rendered source ranges,
  so GFM link splitting cannot leave an empty canonical anchor that claims adjacent
  visible text. Literal brackets, escaped angles, and code-span labels remain valid.
- Exact resolver and complete v3 fixtures passed with all 119 projection tests and all
  461 queue tests; nested-label resolution remained effectively linear.
- Candidate `74354ba` passed the complete gate. Fresh UX and lifecycle lenses approved,
  but the parser lens blocked after an official-GFM differential found one/two-tilde
  strikethrough could create visible Action/label collisions the gate accepted.
- Routed the repair to bounded GFM strikethrough semantics with complete v3,
  escaped-tilde, code-span, delimiter-interaction, and scaling controls. The next panel
  again restarts from zero.
- Implemented official GFM one/two-tilde strikethrough in standalone and bracketed
  contexts, including extension-aware underscore/star flanking, code/autolink
  ownership, escapes, intraword text, unmatched runs, and literal runs of three or more.
- An official-GitHub differential reported zero differences across 3,804 structured
  and seeded cases; all 119 projection tests and all 465 queue tests passed.
- Candidate `78538b5` passed the complete gate. Fresh UX and lifecycle lenses approved,
  but the parser lens blocked after a 9,767-source official-GFM differential found the
  bare URL, `www`, and email autolink extensions were absent from rendered identity and
  reference ownership.
- Routed the repair to context-aware extended-autolink recognition with exact
  punctuation, escape, code, existing-link, complete-v3, differential, and scaling
  controls. The next panel again restarts from zero.
- Added official cmark-gfm bare URL, `www`, and email autolink ownership with delimiter,
  entity, backslash, code, explicit/reference-link, and owning-label context. Strict
  Actions now fail closed whenever rendered text owns an external automatic link.
- Structured and seeded official-GFM differentials found no false accept, all 119
  projection tests passed, and all 469 queue tests passed on the final rerun.
- Candidate `112b441` passed the complete gate. Fresh UX and lifecycle lenses approved,
  but the parser lens blocked after a 22,591-source cmark-gfm differential found
  emphasized email autolinks missed because their closing underscore remained attached
  during domain scanning.
- Routed the repair to post-emphasis extended-email ownership with plain, `+`,
  `mailto:`, escaped/entity-at, Unicode-prefix, literal, intraword, complete-v3,
  differential, and scaling controls. The next panel again restarts from zero.
- Fixed post-emphasis ownership for extended email and URL autolinks, including
  cmark-gfm's byte-oriented UTF-8/backslash domain cursor. A 23,464-source differential
  found no remaining accepted external-link false negatives; all 119 projection tests
  and all 472 queue tests passed.
- Honored the owner's stopping boundary after the verified repair instead of starting
  another review loop. Rewrote the artifact-pending human re-review as a self-contained
  v2 status brief with the completed work, discovered problems, design decisions, and
  exact next steps; it explicitly requests no response until the panel publishes one
  immutable target.
