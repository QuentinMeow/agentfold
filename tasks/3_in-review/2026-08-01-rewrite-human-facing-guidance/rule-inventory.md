# Rule inventory — the acceptance test for the rewrite

Every normative statement in `handbook/human-action-guide.md` (rows 1–126) and in the
"Lifecycle and content" section of `message-queue/AGENTS.md` (rows 127–163).

Source line numbers are the pre-rewrite files: `handbook/human-action-guide.md` at 178
lines, `message-queue/AGENTS.md` at 60 lines.

Categories: `content-craft`, `schema`, `lifecycle`, `provider`, `timing`, `link/projection`.
`RESTATED: <file>` marks a rule whose owner is another file. `UNCLEAR: <why>` marks a rule
that is internally contradictory or that I could not read with confidence.

## `handbook/human-action-guide.md`

| # | Source file:line | The rule, in one sentence | Category |
|---|---|---|---|
| 1 | human-action-guide.md:3-4 | A human action succeeds only when a zero-context reader can tell what to do and what their answer changes. | content-craft |
| 2 | human-action-guide.md:4-5 | The canonical live identity of a human action is one file under `message-queue/needs-human/`. | lifecycle — RESTATED: `message-queue/AGENTS.md` |
| 3 | human-action-guide.md:5-6 | PRs, issues, chat, tasks, and handovers carry only a short linked projection of the action, never the action itself. | link/projection — RESTATED: `message-queue/AGENTS.md` |
| 4 | human-action-guide.md:6 | Exact schemas live in `templates/queue/`. | schema |
| 5 | human-action-guide.md:10 | Do not turn incomplete agent work into a vague request for approval. | content-craft |
| 6 | human-action-guide.md:12-13 | A claim checkable from code, text, tests, or a diff is agent-owned: the agent performs the check and records the evidence. | lifecycle |
| 7 | human-action-guide.md:13-14 | Ask for human review of a checkable claim only when judgment is left over after the check. | lifecycle |
| 8 | human-action-guide.md:14-15 | A preference, an authority decision, a one-way door, or an interpretation of human intent is human-owned. | lifecycle |
| 9 | human-action-guide.md:15 | Queue a human-owned judgment before mentioning it in any other channel. | link/projection — RESTATED: root `AGENTS.md` |
| 10 | human-action-guide.md:16 | Several independently answerable judgments become several files. | content-craft |
| 11 | human-action-guide.md:17 | One jargon-heavy checklist is not a substitute for several files. | content-craft |
| 12 | human-action-guide.md:26-27 | Copy the endpoint's exact schema from `templates/queue/`; this guide restates no field or heading. | schema |
| 13 | human-action-guide.md:27-28 | The filled item must let a zero-context reader identify one concrete response. | content-craft |
| 14 | human-action-guide.md:28 | The filled item must point at one durable source for depth. | content-craft |
| 15 | human-action-guide.md:28-29 | The filled item must make the meaningful dispositions and their differing consequences understandable. | content-craft |
| 16 | human-action-guide.md:29 | The filled item must show one small example. | content-craft |
| 17 | human-action-guide.md:29 | The filled item must state the boundary or the safe unattended result. | content-craft |
| 18 | human-action-guide.md:31 | Review-specific syntax follows `templates/queue/review.md`. | schema |
| 19 | human-action-guide.md:31-32 | `Review target` names exactly one repository file, Git commit/range, or HTTPS artifact. | schema — RESTATED: `templates/queue/review.md` |
| 20 | human-action-guide.md:32 | `Review revision` binds the target's bytes. | schema — RESTATED: `templates/queue/review.md` |
| 21 | human-action-guide.md:32-34 | A local or HTTPS target uses `sha256`; a Git target repeats the exact `git:<...>` revision. | schema — RESTATED: `templates/queue/review.md` |
| 22 | human-action-guide.md:34 | `pending` is valid only before publication. | schema — RESTATED: `templates/queue/review.md` |
| 23 | human-action-guide.md:34-35 | `Full context` explains the judgment and never substitutes for the target or its immutable revision. | schema — RESTATED: `templates/queue/review.md` |
| 24 | human-action-guide.md:35-36 | Task status paths move, so they are never durable context. | lifecycle — RESTATED: `tasks/AGENTS.md` |
| 25 | human-action-guide.md:36-37 | Only a task-pickup request may use a moving task path as live context, because its claim commit deletes that request. | lifecycle — RESTATED: `message-queue/AGENTS.md` |
| 26 | human-action-guide.md:37-38 | A retry record may quote a moving task path only as evidence of broken state. | lifecycle — RESTATED: `message-queue/AGENTS.md` |
| 27 | human-action-guide.md:42 | The human replaces one blank with one sentence and commits. | lifecycle |
| 28 | human-action-guide.md:42-43 | Nothing else on the page belongs to the human. | lifecycle |
| 29 | human-action-guide.md:43-44 | A repository path a human names inside their answer is prose the folding agent reads, never a link the commit must resolve. | lifecycle — RESTATED: `message-queue/AGENTS.md` |
| 30 | human-action-guide.md:44-45 | An item whose acceptance depends on a second hand-written human field is filed wrong. | schema |
| 31 | human-action-guide.md:45-46 | A wrongly filed item has no repair, because the first response is immutable and human text is not editable. | lifecycle |
| 32 | human-action-guide.md:48-49 | A review's `Reviewed revision` and `Review outcome` are supplied by the agent, never by the human. | lifecycle |
| 33 | human-action-guide.md:49 | Both fields are written in the one `waiting` → `folding` claim commit. | lifecycle — RESTATED: `message-queue/AGENTS.md` |
| 34 | human-action-guide.md:49-50 | Both fields may be written only over a response the parent commit already carried. | lifecycle |
| 35 | human-action-guide.md:50-51 | `Reviewed revision` repeats the frozen `Review revision`, so the classification can never be re-pointed at other bytes. | lifecycle |
| 36 | human-action-guide.md:51-52 | `Review outcome` is write-once and can never be amended. | lifecycle |
| 37 | human-action-guide.md:52-54 | `queue_deletion_problem` refuses to resolve a review that is unbound or lacks a terminal outcome. | lifecycle |
| 38 | human-action-guide.md:54 | A boundary still needs `approved`. | lifecycle |
| 39 | human-action-guide.md:56-58 | The reconciler cannot verify that an outcome truthfully reads the human's words, so it bounds rather than prevents a misclassification. | lifecycle |
| 40 | human-action-guide.md:58-60 | The outcome lands in a separate, attributable commit beside the human's immutable words, and cannot exist until their response is already committed. | lifecycle |
| 41 | human-action-guide.md:62 | The summary must be sufficient to act on by itself. | content-craft |
| 42 | human-action-guide.md:62-63 | The full-context link is depth, never a missing prerequisite. | content-craft |
| 43 | human-action-guide.md:63 | A recommendation is evidence, not permission to hide an alternative. | content-craft |
| 44 | human-action-guide.md:67-68 | The file is read top to bottom exactly once, so its order is the contract and the reconciler enforces it. | schema |
| 45 | human-action-guide.md:68-70 | The ask leads with exactly three sentences: what is asked, what it changes in the world, and what happens if it is never answered. | schema — RESTATED: `templates/queue/decision.md` |
| 46 | human-action-guide.md:70 | Nothing else stands above the first heading. | schema — RESTATED: `templates/queue/decision.md` |
| 47 | human-action-guide.md:70-71 | Those three sentences are the whole notification the owner sees. | content-craft |
| 48 | human-action-guide.md:71-73 | Today's real behaviour is separated from the proposed change and from the adjacent things a reader wrongly assumes are in scope. | content-craft — RESTATED: `templates/queue/decision.md` |
| 49 | human-action-guide.md:73-74 | Each choice sits under its own heading with its cost and one concrete consequence of picking it. | content-craft — RESTATED: `templates/queue/decision.md` |
| 50 | human-action-guide.md:74-75 | The recommendation comes after the choices so it cannot anchor them. | content-craft |
| 51 | human-action-guide.md:75 | The strongest case against the recommendation sits beside it. | content-craft |
| 52 | human-action-guide.md:75-76 | Confidence is graded and names what was not checked. | content-craft |
| 53 | human-action-guide.md:76 | The answer line comes after the recommendation. | schema |
| 54 | human-action-guide.md:76 | Everything a machine reads sits below the answer line, under `## For the record`. | schema — RESTATED: `templates/queue/decision.md` |
| 55 | human-action-guide.md:78 | Three of these rules are judgment rather than syntax, and review is their only control. | content-craft |
| 56 | human-action-guide.md:78-80 | The title is a question the owner can answer without knowing this repository, and it never states the verdict. | content-craft — RESTATED: `templates/queue/decision.md`, `skills/explain-to-human/scenarios/queue-item.md` |
| 57 | human-action-guide.md:80-82 | `Today` says what actually happens now — "nothing is implemented" when that is true — rather than describing the proposal twice. | content-craft |
| 58 | human-action-guide.md:82-83 | The counter-case is the strongest argument for a different answer, not a hedge. | content-craft |
| 59 | human-action-guide.md:85 | Never ask a person to copy a hash, a revision, or any offered vocabulary. | content-craft |
| 60 | human-action-guide.md:86 | A plain-English sentence is a complete answer. | content-craft |
| 61 | human-action-guide.md:86-87 | The folding agent does the bookkeeping and shows the person how it read their words before acting. | lifecycle |
| 62 | human-action-guide.md:87-88 | State the source once, as one clickable link in the prose. | content-craft |
| 63 | human-action-guide.md:88 | The machine-readable copy of the source belongs in `Full context`, below the answer line. | schema |
| 64 | human-action-guide.md:89-90 | A file that already carries a concrete response is a record: never reformatted, and it keeps the schema it was written under. | lifecycle |
| 65 | human-action-guide.md:92 | Field names, headings, and their exact order live in `templates/queue/`. | schema |
| 66 | human-action-guide.md:96 | `decisions/` is for choosing among alternatives only the human may authorize. | lifecycle — RESTATED: `message-queue/needs-human/decisions/README.md` |
| 67 | human-action-guide.md:97 | `clarifications/` corrects an interpretation or supplies missing intent. | lifecycle — RESTATED: `message-queue/needs-human/clarifications/README.md` |
| 68 | human-action-guide.md:98 | `reviews/` judges a named diff, artifact, or claim. | lifecycle — RESTATED: `message-queue/needs-human/reviews/README.md` |
| 69 | human-action-guide.md:100-103 | Timing is an independent second axis owned by `message-queue/AGENTS.md`, and this guide adds no timing rule of its own. | timing — UNCLEAR: contradicted by rows 106, 113, 114, 115, all of which are timing rules stated in this guide |
| 70 | human-action-guide.md:107 | Every other channel links the same live item. | link/projection |
| 71 | human-action-guide.md:107-109 | A PR "What to review" entry links its canonical item; one entry carries one link and its surrounding explanation stays declarative. | link/projection |
| 72 | human-action-guide.md:109-112 | A provider's checked no-action acknowledgement covers its whole selected actor surface, so a GitHub PR description uses exactly `No queued action requested.` only when neither a human nor an agent/bot assignment exposes an action. | provider |
| 73 | human-action-guide.md:112-114 | Each provider assignment gets a distinct queue item whose `External assignment` exactly copies the adapter's opaque provider, stable-artifact, role, actor-kind, and principal binding. | provider — RESTATED: `automation/AGENTS.md` |
| 74 | human-action-guide.md:114 | Another artifact or a generic review may not reuse an `External assignment` for a new assignee or reviewer. | provider |
| 75 | human-action-guide.md:115-116 | When a person writes provider prose with no queue link, the receiving agent transcribes it instead of asking that person to rewrite their words. | link/projection |
| 76 | human-action-guide.md:116-119 | On GitHub every open issue is a forced, directionless source: its projected or bound queue path chooses the concrete actor, and even informational wording needs at least a non-blocking triage item. | provider |
| 77 | human-action-guide.md:119-121 | Every non-empty conversation comment on an issue or PR, and every effective formal review, is structural `needs-agent` triage. | provider |
| 78 | human-action-guide.md:121-122 | These provider rules do not consult English, and no-action prose cannot waive them. | provider |
| 79 | human-action-guide.md:122-123 | A changes-requested review on the provider is forced even with an empty body. | provider |
| 80 | human-action-guide.md:123-124 | Whenever current state is replayed, unresolved diff threads remain forced action state. | provider |
| 81 | human-action-guide.md:124-127 | GitHub emits no Actions event for resolving or reopening a thread, so replay also runs when a PR enters a merge queue, and its evidence is only as fresh as the last supported event. | provider |
| 82 | human-action-guide.md:127-129 | A hard claim that a currently unresolved thread cannot merge requires GitHub's native "Require conversation resolution before merging" rule (`required_review_thread_resolution` in rulesets, `required_conversation_resolution` in classic protection). | provider |
| 83 | human-action-guide.md:129-130 | That rule does not prove that every transient reopen-then-resolve toggle was durably queued. | provider |
| 84 | human-action-guide.md:130-132 | Every active source has at least one item carrying the adapter's opaque, content-versioned `External source`. | provider |
| 85 | human-action-guide.md:132 | A direct provider link is a projection and never replaces the durable `External source` binding. | provider |
| 86 | human-action-guide.md:132 | One source may bind several items across actors. | provider |
| 87 | human-action-guide.md:132-135 | Bound items stay live while the provider still reports the source as current — on GitHub, an open artifact's current conversation comment, effective formal review, or unresolved diff thread at a replayed snapshot. | provider |
| 88 | human-action-guide.md:135-136 | A comment edit gets a new identity; comment deletion or artifact closure removes it. | provider |
| 89 | human-action-guide.md:136-138 | A superseded or dismissed review, or a resolved thread, leaves the next replayed snapshot and permits normal queue resolution. | provider |
| 90 | human-action-guide.md:138-140 | At controlled Git admission, removing the final binding also requires the trusted adapter to classify the exact old identity as released; current or unavailable provider state blocks. | provider — RESTATED: `automation/AGENTS.md` |
| 91 | human-action-guide.md:140-141 | That release check needs protected required-check admission, so a direct write cannot land before a post-push failure. | provider |
| 92 | human-action-guide.md:141-144 | One provider message may become several request files sharing one source binding with separate `Action` fields. | provider |
| 93 | human-action-guide.md:144-145 | The binding proves durable routing and source version, not transcription fidelity; ordinary review still judges that fidelity. | provider |
| 94 | human-action-guide.md:146 | A chat answer is transcribed into the item before it is used. | link/projection — RESTATED: root `AGENTS.md`, `message-queue/AGENTS.md` |
| 95 | human-action-guide.md:147-148 | Task and handover projections never carry a second status or answer slot. | link/projection — RESTATED: `history/AGENTS.md`, `tasks/AGENTS.md` |
| 96 | human-action-guide.md:149-150 | Commit the human's response while the item's status is `waiting`. | lifecycle — RESTATED: `message-queue/AGENTS.md` |
| 97 | human-action-guide.md:150-151 | Claim the response in a separate `Status: folding` commit that changes only the status plus, for a review, the two agent-owned binding fields. | lifecycle — RESTATED: root `AGENTS.md`, `message-queue/AGENTS.md` |
| 98 | human-action-guide.md:151-152 | Every item predeclares `Resolution evidence`. | schema — RESTATED: `message-queue/AGENTS.md` |
| 99 | human-action-guide.md:152 | A review's `Resolution evidence` path is distinct from its target. | schema — RESTATED: `message-queue/AGENTS.md`, `templates/queue/review.md` |
| 100 | human-action-guide.md:152 | The commit that deletes an item changes that predeclared evidence. | lifecycle |
| 101 | human-action-guide.md:152-154 | An unanswered review whose artifact changes first retracts to `awaiting-artifact` with pending binding and blank response fields. | lifecycle — RESTATED: `message-queue/AGENTS.md` |
| 102 | human-action-guide.md:154 | A later commit republishes the replacement binding. | lifecycle |
| 103 | human-action-guide.md:154-155 | Publication and retraction never add a response. | lifecycle — RESTATED: `message-queue/AGENTS.md` |
| 104 | human-action-guide.md:155 | The first response freezes the item's binding and its evidence. | lifecycle |
| 105 | human-action-guide.md:155 | `approved` accepts the exact revision. | lifecycle |
| 106 | human-action-guide.md:156-157 | For a `future-blocking-*` item a terminal outcome is response-terminal but not boundary-terminal, so the folding item stays live until the boundary is crossed. | timing — UNCLEAR: row 69 says this guide adds no timing rule |
| 107 | human-action-guide.md:157-159 | A task-lifecycle review binds a stable local artifact file, and its linked folding approval is the transition receipt. | lifecycle |
| 108 | human-action-guide.md:159 | The task must remain past that transition before cleanup. | lifecycle |
| 109 | human-action-guide.md:159-160 | A merge review binds the candidate Git range instead. | lifecycle |
| 110 | human-action-guide.md:160-162 | A merge review's approval stays fresh only through queue-only tail commits. | lifecycle |
| 111 | human-action-guide.md:162 | Cleaning up a merge review requires an exact two-parent merge carrying the receipt in previously admitted target history. | lifecycle |
| 112 | human-action-guide.md:162 | A candidate-local merge is not evidence. | lifecycle |
| 113 | human-action-guide.md:162 | A dated review closes at or after its date. | timing |
| 114 | human-action-guide.md:163 | Named events and custom transitions first escalate to blocking. | timing |
| 115 | human-action-guide.md:163 | Custom operations are already blocking. | timing |
| 116 | human-action-guide.md:163-166 | Without a controlled adapter, changed evidence records only the agent's acknowledgement. | provider |
| 117 | human-action-guide.md:168 | A rejected or abandoned review never authorizes crossing its boundary. | lifecycle |
| 118 | human-action-guide.md:168-169 | A task-bound rejection remains live until that task is removed. | lifecycle |
| 119 | human-action-guide.md:169-170 | A rejected Git candidate is restored path-for-path to its reviewed base. | lifecycle |
| 120 | human-action-guide.md:170 | A rejected local target changes or disappears. | lifecycle |
| 121 | human-action-guide.md:170-171 | Distinct cancellation evidence records the disposition without rewriting the reviewed bytes. | lifecycle |
| 122 | human-action-guide.md:172-175 | `changes-requested` creates one same-timing `needs-agent` action that solely owns the concrete repair, its context, and its resolution evidence. | lifecycle |
| 123 | human-action-guide.md:174-176 | `changes-requested` also creates one distinct `needs-human` re-review awaiting that artifact, depending on the repair action, so the boundary stays closed without duplicating the repair. | lifecycle |
| 124 | human-action-guide.md:176 | `rejected` and `abandoned` end pursuit. | lifecycle |
| 125 | human-action-guide.md:176 | Legacy `not-approved` is equivalent to `rejected`/`abandoned`. | lifecycle — UNCLEAR: "equivalent" does not say which of the two, and no other file defines `not-approved` |
| 126 | human-action-guide.md:176-178 | After valid cleanup Git history archives delivery; until then the queue is the only live dependency surface. | lifecycle |

## `message-queue/AGENTS.md` — "Lifecycle and content"

| # | Source file:line | The rule, in one sentence | Category |
|---|---|---|---|
| 127 | message-queue/AGENTS.md:42 | Copy the matching template, which is valid as shipped once its placeholders are filled. | schema — RESTATED: `templates/README.md` |
| 128 | message-queue/AGENTS.md:42 | Human fields follow `handbook/human-action-guide.md`. | schema |
| 129 | message-queue/AGENTS.md:42 | Under the `Human-attention format` marker, a live unanswered human item leads with the ask and keeps every machine field below its answer line. | schema — RESTATED: `handbook/human-action-guide.md` |
| 130 | message-queue/AGENTS.md:43 | Record an artifact-scoped `External assignment` or a versioned `External source`. | provider — RESTATED: `handbook/human-action-guide.md` |
| 131 | message-queue/AGENTS.md:43 | A direct provider link never replaces that binding. | provider — RESTATED: `handbook/human-action-guide.md` |
| 132 | message-queue/AGENTS.md:43 | Releasing the last binding needs trusted provider evidence. | provider — RESTATED: `handbook/human-action-guide.md` |
| 133 | message-queue/AGENTS.md:44 | An item of unknown authorship is reviewed, never executed. | lifecycle — RESTATED: `handbook/principles/provenance-over-position.md` |
| 134 | message-queue/AGENTS.md:45 | A human answers in one edit: one sentence in the response blank, committed while the status is `waiting`. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 135 | message-queue/AGENTS.md:45 | The human's response is immutable. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 136 | message-queue/AGENTS.md:45 | A repository path named inside that response is prose, not a link claim. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 137 | message-queue/AGENTS.md:46 | `Reviewed revision` and `Review outcome` are the agent's, written once on the `waiting` → `folding` claim edge and only over an already-committed response. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 138 | message-queue/AGENTS.md:46 | That claim commit changes nothing else and freezes the action. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 139 | message-queue/AGENTS.md:47-48 | Treat a counter-question as a disposition: claim and fold it, and answer it in durable evidence. | lifecycle — RESTATED: `handbook/decision-guide.md` |
| 140 | message-queue/AGENTS.md:48 | Create a same-timing successor that names the old item in `Supersedes`. | lifecycle — RESTATED: `handbook/decision-guide.md` |
| 141 | message-queue/AGENTS.md:48-49 | An unanswered review binding may retract to `awaiting-artifact` with a pending binding and then publish again. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 142 | message-queue/AGENTS.md:49 | Neither the retraction nor the publication edge may add a response. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 143 | message-queue/AGENTS.md:50 | An agent claim changes only `open` to `in-repair`. | lifecycle |
| 144 | message-queue/AGENTS.md:50 | That committed claim edge proves active repair. | lifecycle |
| 145 | message-queue/AGENTS.md:50 | Action identity never changes after the claim. | lifecycle |
| 146 | message-queue/AGENTS.md:51-52 | A task pickup is an explicit non-blocking request carrying `Request kind: task-pickup` and one reciprocal backlog `task.md` link. | schema — RESTATED: `tasks/AGENTS.md` |
| 147 | message-queue/AGENTS.md:52-53 | A pickup's atomic claim-and-move commit deletes it. | lifecycle — RESTATED: `tasks/AGENTS.md` |
| 148 | message-queue/AGENTS.md:53-54 | Only pickups use moving task paths as live context. | lifecycle |
| 149 | message-queue/AGENTS.md:54 | Retries may quote broken paths. | lifecycle |
| 150 | message-queue/AGENTS.md:55 | Every item predeclares a non-queue `Resolution evidence` path. | schema |
| 151 | message-queue/AGENTS.md:55-56 | A review keeps `Resolution evidence` distinct from its target. | schema |
| 152 | message-queue/AGENTS.md:56 | A review binds a stable local file. | lifecycle — UNCLEAR: `handbook/human-action-guide.md:159-160` says a merge review binds a Git range instead |
| 153 | message-queue/AGENTS.md:56-57 | A review is owned by one task — by boundary, or by the task its `Filed:` provenance names. | lifecycle |
| 154 | message-queue/AGENTS.md:57 | Future timing survives the response. | timing — RESTATED: `handbook/human-action-guide.md` (row 106) |
| 155 | message-queue/AGENTS.md:57-58 | Cleanup needs the crossed receipt for a start gate, and changed evidence otherwise. | lifecycle |
| 156 | message-queue/AGENTS.md:58 | UTC dates are clock-checked; other timing is agent-attested absent a validating adapter. | timing |
| 157 | message-queue/AGENTS.md:58 | Rejection withdraws its target. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 158 | message-queue/AGENTS.md:58 | Changes requested creates a re-review. | lifecycle — RESTATED: `handbook/human-action-guide.md` |
| 159 | message-queue/AGENTS.md:59 | A generated retry needs an exact identity and a cleared finding. | lifecycle |
| 160 | message-queue/AGENTS.md:59 | A pickup needs the atomic backlog-to-claimed move. | lifecycle — RESTATED: `tasks/AGENTS.md` |
| 161 | message-queue/AGENTS.md:59 | Git history archives resolutions. | lifecycle |
| 162 | message-queue/AGENTS.md:60 | Transcribe a chat response before using it. | link/projection — RESTATED: root `AGENTS.md` |
| 163 | message-queue/AGENTS.md:60 | Timing never changes after a concrete response. | timing — RESTATED: `message-queue/AGENTS.md:26` ("a concrete human response freezes timing") |

## Category tally

| Category | Rows |
|---|---|
| lifecycle | 73 |
| content-craft | 25 |
| provider | 25 |
| schema | 24 |
| link/projection | 8 |
| timing | 8 |
| **Total** | **163** |

Rows flagged `RESTATED`: 55. Rows flagged `UNCLEAR`: 4 (69, 106, 125, 152).
