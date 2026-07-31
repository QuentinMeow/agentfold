# Writing human actions that can be decided

A human action is successful only when a zero-context reader can tell what to do and
what their answer changes. Its canonical live identity is a file under
`message-queue/needs-human/`; PRs, issues, chat, tasks, and handovers only surface a
short linked projection. Exact schemas live in `templates/queue/`.

## First decide whether judgment is actually human-owned

Do not turn incomplete agent work into a vague request for approval.

- A claim that can be checked from code, text, tests, or a diff is agent-owned: perform
  the check, record evidence, and ask for human review only if residual judgment matters.
- A preference, authority decision, one-way door, or interpretation of human intent is
  human-owned: queue it before mentioning it in another channel.
- Several independently answerable judgments become several files. One jargon-heavy
  checklist is not a shortcut.

Example: “Does every `block` statement apply only in hard mode?” is a text audit the
agent should perform. “May merge-protected deployments claim data never reached the
remote?” is a human-reviewed security promise whose alternatives need explanation.

## Give the reader a real choice

Copy the endpoint's exact schema from `templates/queue/`; this guide does not restate
its fields or headings. Fill that schema so a zero-context reader can identify one
concrete response, follow one durable source for depth, understand the meaningful
dispositions and their different consequences, see one small example, and know the
boundary or safe unattended result.

For review-specific syntax, follow `templates/queue/review.md`. `Review target` names
exactly one repository file, Git commit/range, or HTTPS artifact; `Review revision`
binds its bytes. Local/HTTPS targets use `sha256`, while a Git target repeats the exact
`git:<...>` revision. `pending` is valid only before publication. Full context explains
the judgment but never substitutes for its target or immutable revision. Task status
paths move and are not durable context; only a pickup may use one as live context
because its claim commit deletes that request. Retry records may quote one only as
evidence of broken state.

## One edit is the whole answer

The reader replaces one blank with one sentence and commits. Nothing else on the page is
theirs, and a repository path they name inside that sentence is prose the folding agent
reads, never a link the commit must resolve. Any item whose acceptance depends on a
second hand-written field is filed wrong: it cannot be answered from a phone, and there
is no repair, because the first response is immutable and human text is not editable.

A review's `Reviewed revision` and `Review outcome` are therefore supplied by the agent,
in the one `waiting` → `folding` claim commit, and only over a response the parent commit
already carried. Both are write-once: the binding repeats the frozen `Review revision`, so
the classification can never be re-pointed at other bytes, and the outcome can never be
amended. Everything those fields buy survives — `queue_deletion_problem` still refuses to
resolve a review that is unbound or lacks a terminal outcome, and a boundary still needs
`approved`. What moved is who writes them and when.

The reconciler cannot read English, so it cannot verify that `approved` is a truthful
reading of "Looks good to me". It bounds the lie instead of preventing it: the outcome
lands in a separate, attributable commit, beside the human's immutable words, and cannot
exist at all until their response is already committed
(`memory/known-issues/2026-07-31-review-outcome-classification-is-attested.md`).

The summary must be sufficient to act; the full-context link is for depth, not a missing
prerequisite. A recommendation is evidence, not permission to hide an alternative.

## Choose kind and timing independently

- `decisions/`: choose among alternatives only the human may authorize.
- `clarifications/`: correct an interpretation or supply missing intent.
- `reviews/`: judge a named diff, artifact, or claim.

Then choose the filename prefix from `message-queue/AGENTS.md`: `blocking-` only when a
named boundary is stopped now; `future-blocking-` when work stops at an explicit future
boundary; `non-blocking-` only when it can remain unanswered forever. Risk severity does
not determine the prefix. A live action may move only toward an earlier dependency:
`non-blocking` → `future-blocking` → `blocking`. Weakening creates an authorized
replacement, and no human timing changes with or after the first concrete response.
UTC dates can be checked against the repository clock. An arbitrary named event,
transition, or operation is only an agent-attested acknowledgement when its Resolution
evidence changes; hard assurance requires a controlled adapter that observes and
enforces that boundary.

## Project without forking the action

Every other channel links the same live item. A PR “What to review” entry links its
canonical item; one entry carries one link and keeps any surrounding explanation
declarative. A provider's checked no-action acknowledgement covers its whole selected
actor surface: GitHub PR descriptions use exact `No queued action requested.` only
when neither a human nor an agent/bot assignment exposes an action. Each provider
assignment gets a distinct queue item whose `External assignment` field exactly copies
the adapter's opaque provider, stable-artifact, role, actor-kind, and principal binding;
another artifact or generic review cannot reuse it for a new assignee or reviewer.
When a person writes provider prose without a queue link, the receiving agent
transcribes it instead of asking that person to rewrite their words. On GitHub, every
open issue is a forced, directionless source: its projected or bound queue path chooses
the concrete actor, and even informational wording needs at least a
non-blocking triage item. Every non-empty conversation comment on an issue/PR and every
effective formal review is structural `needs-agent` triage. These rules do not consult
English, and no-action prose cannot waive them. Changes-requested reviews are forced
even with an empty body; whenever current state is replayed, unresolved diff threads
remain forced action state. GitHub emits no Actions event for resolving or
reopening a thread, so replay also runs when a PR enters a merge queue, but its evidence
is only as fresh as the last supported event. A hard claim that a currently unresolved
thread cannot merge requires GitHub's native “Require conversation resolution before
merging” rule (`required_review_thread_resolution` in rulesets or
`required_conversation_resolution` in classic protection). That rule does not prove
that every transient reopen-then-resolve toggle was durably queued.
Every active source has at least one item carrying the adapter's opaque,
content-versioned `External source`; a direct provider link remains a projection and
never replaces that durable binding. One source may bind several items across actors.
Keep those items live while the provider still reports the source as current—on
GitHub, an open artifact's current conversation comment, effective formal review, or
unresolved diff thread at a replayed snapshot. A comment edit gets a new identity;
comment deletion or artifact closure removes it. A superseded/dismissed review or
resolved thread likewise leaves the next replayed snapshot and permits normal queue
resolution. At controlled Git admission, removing the final binding also requires the
trusted adapter to classify the exact old identity as released; current or unavailable
provider state blocks. That check needs protected required-check admission to prevent
direct writes from landing before a post-push failure. Example: “Please fix
both the race and its missing regression” may become two request files with the same
source binding and separate `Action` fields. The binding proves durable routing and
source version, not that an agent's transcription captured every nuance; ordinary
review still judges that semantic fidelity.
Chat answers are first transcribed into the item. Task and handover projections never
carry a second status or answer slot.

Commit the response while status is `waiting`, then claim it in a separate `Status:
folding` commit that changes only the status and, for a review, the two agent-owned
binding fields above. Every item predeclares `Resolution evidence`; a review's
path is distinct from its target. Deletion changes that evidence in its commit. An
unanswered review whose artifact changes first retracts to `awaiting-artifact` with
pending binding and blank response fields; a later commit republishes the replacement.
Publication and retraction never add a response, and the first response freezes its
binding and evidence. `approved` accepts the exact revision. For `future-blocking-*`,
that outcome is response-terminal but not boundary-terminal: keep the folding item
live until the boundary is crossed. A task-lifecycle review binds a stable local artifact
file; its linked folding approval is the transition receipt, and the task must remain
past that transition before cleanup. A merge review instead binds the candidate Git
range. Its approval stays fresh only through queue-only tail commits; cleanup requires
an exact two-parent merge carrying the receipt in previously admitted target history.
A candidate-local merge is not evidence. A dated review closes at or after its date.
Named events/custom transitions first escalate to blocking; custom operations are
already blocking. Without a controlled adapter, changed evidence records only the
agent's acknowledgement.

Rejected or abandoned review never authorizes crossing. A task-bound rejection remains
live until that task is removed. A rejected Git candidate is restored path-for-path to
its reviewed base; a rejected local target changes or disappears. Distinct cancellation
evidence records the disposition without rewriting the reviewed bytes.
`changes-requested` creates one
same-timing `needs-agent` action that solely owns the concrete repair, context, and
resolution evidence, plus one distinct `needs-human` re-review awaiting that artifact;
the latter depends on the former, so the review boundary stays closed without duplicating
the repair. `rejected` and `abandoned` end pursuit. Legacy `not-approved` is equivalent.
After valid cleanup, Git history archives delivery; until then the queue remains the
only live dependency surface.
