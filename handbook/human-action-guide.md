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

For review-specific target and revision syntax, follow `templates/queue/review.md`.
Conceptually, one exact Git commit/range, repository file, or HTTPS artifact is bound
to immutable bytes; navigation is not revision authority, and an older response cannot
apply after the target changes. Task status paths move and are not durable context;
only a pickup may use one as live context because its claim commit deletes that request.
Retry repair records may quote one only as evidence of broken state.

The summary must be sufficient to act; the full-context link is for depth, not a missing
prerequisite. A recommendation is evidence, not permission to hide an alternative.

## Choose kind and timing independently

- `decisions/`: choose among alternatives only the human may authorize.
- `clarifications/`: correct an interpretation or supply missing intent.
- `reviews/`: judge a named diff, artifact, or claim.

Then choose the filename prefix from `message-queue/AGENTS.md`: `blocking-` only when a
named boundary is stopped now; `future-blocking-` when work stops at an explicit future
boundary; `non-blocking-` only when it can remain unanswered forever. Risk severity does
not determine the prefix.

## Project without forking the action

Every other channel links the same live item. A PR “What to review” entry links its
canonical item; one entry carries one link and keeps any surrounding explanation
declarative. A provider's checked no-action acknowledgement covers its whole selected
actor surface: GitHub PR descriptions use exact `No queued action requested.` only
when neither a human nor an agent/bot assignment exposes an action. Each provider
assignment gets a distinct queue item whose `External assignment` field exactly copies
the adapter's opaque provider, role, actor-kind, and identity binding; an existing
generic review cannot stand in for a new assignee or requested reviewer.
When a person writes an actionable review or diff thread without a queue link, the
receiving agent transcribes it instead of asking that person to rewrite their words.
On GitHub, every non-empty issue or PR conversation comment and every non-empty
effective formal review is routed to `needs-agent` for triage even when its wording
looks informational; this structural rule keeps durable interaction from depending on
English inference. The triage action may be non-blocking. Changes-requested reviews
are forced even with an empty body and unresolved diff threads remain forced action
state.
Each resulting `needs-agent/` item copies the adapter's opaque, content-versioned
`External source`; one source may bind several items when it contains several asks.
Keep those items live while the provider still reports the source as current—on
GitHub, an open artifact's current conversation comment, effective formal review, or
unresolved diff thread. A comment edit gets a new identity; comment deletion or
artifact closure removes it. A superseded/dismissed review or resolved thread likewise
leaves the active snapshot and permits normal queue resolution. Example: “Please fix
both the race and its missing regression” may become two request files with the same
source binding and separate `Action` fields. The binding proves durable routing and
source version, not that an agent's transcription captured every nuance; ordinary
review still judges that semantic fidelity.
Chat answers are first transcribed into the item. Task and handover projections never
carry a second status or answer slot.

Commit the response while status is `waiting`, then claim it in a separate one-line
`Status: folding` commit. Fold into the predeclared `Resolution evidence` file(s);
deletion requires those files to change in that commit. An unanswered waiting review
whose artifact changes first retracts to `awaiting-artifact` with pending binding and
blank response fields; a later commit republishes the replacement as `waiting`.
Publication and retraction never add a response, and the first response freezes its
binding. `approved` accepts the exact revision. `changes-requested` creates one
same-timing `needs-agent` action that solely owns the concrete repair, context, and
resolution evidence, plus one distinct `needs-human` re-review awaiting that artifact;
the latter depends on the former, so the review boundary stays closed without duplicating
the repair. `rejected` and `abandoned` end pursuit. Legacy `not-approved` is equivalent.
Git history archives delivery; the changed durable source preserves the result.
