# Writing human actions that can be decided

A human action succeeds only when a zero-context reader can answer confidently from
the file itself. The reader should immediately see what they need to do, why it
matters, what is true today, what would change, the available choices, the agent's
recommendation, and the consequence of silence. Background links add depth; they do
not make the reader reconstruct the question.

The canonical live identity is a file under `message-queue/needs-human/`. PRs, issues,
chat, tasks, and handovers only surface a short linked projection. Exact presentation
and lifecycle schemas live in `templates/queue/`.

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

## Put the action before the recordkeeping

Copy the endpoint's exact schema from `templates/queue/`; this guide does not restate
its headings. Begin with the requested action and practical stakes. Put lifecycle
identifiers and machine-managed fields in the collapsed `Tracking details` block at
the end. `Action` and `Full context` stay beside the reader-facing content they
describe. A review's exact target stays with its revision in tracking so a target that
is also the full-context source does not create a duplicate visible link.

Write `Action` as one safe inline Markdown line. Closed emphasis and code spans, plus
escaped punctuation, are allowed. Links, images, autolinks, reference syntax, raw HTML,
block Markdown, unbalanced brackets, and unclosed emphasis or code are not. This gives
the action one unambiguous rendered identity wherever it is projected. Make it the first
visible construct in its section, then add one blank line and one compact explanatory
paragraph that tells the reader what their answer must decide.

Immediately below the presentation marker, show the template's exact plain lifecycle
notice. `Waiting for your response` means the human can act. `Not ready yet` and
`Response received` explicitly remove the prompt when the artifact is unavailable or
the answer is already being recorded. The notice mirrors tracking status; it does not
create another status field.

Write the body as a self-contained explanation:

- Separate present state from future behavior. Use “Today” only for behavior that is
  true now. Call a proposal a proposal, and say when it is not implemented.
- Give every option the same labels and level of detail. Compare benefits, costs,
  risks, and concrete consequences on the same basis. Do not make the recommended
  choice look stronger by describing it more fully.
- Put the recommendation after all options and after its calibration. In exact order,
  name the evidence actually checked, assumptions, confidence, rationale, and what
  would reverse the recommendation; state the recommended answer last. This reduces
  anchoring on the agent's conclusion before the reader sees its basis and uncertainty.
  Decisions conclude with exact `Choose Option X.` and clarifications with exact `Use
  Interpretation X.`; negation or merely mentioning an option is not a recommendation.
  Never hide an unverified core claim in `Assumptions` while recommending approval.
- State the no-response behavior near the top. It is a consequence, not a threat: say
  exactly what continues, stops, or happens by default.
- Use complete sentences and familiar words. Expand repository shorthand on first use
  and avoid machine-field names in explanatory prose.

`Why this matters` and `If you do not respond` are each one nonempty compact
paragraph, not one machine-counted sentence. They may contain several sentences and
soft line wraps; inline emphasis and code are fine. Each paragraph is at most 240
Unicode code points after normalization, and together they are at most 400. Each ends
in `.`, `?`, `!`, `。`, `！`, or `？`, optionally before its balanced closing quote or
bracket. The second begins exactly “If you do not respond,”. Headings, lists, quotes,
tables, rules, code blocks, raw HTML, links, images, and reference definitions do not
belong in these compact paragraphs. This makes them safe to reuse in a handover while
allowing normal abbreviations, filenames, decimals, and internal punctuation.

The state, each option or review outcome, the recommendation, and References contain
only their template's fields in the declared order. Wrap a long value only on the
immediately following source line with exactly two spaces; a blank line or standalone
comment ends that value. Free prose belongs in a declared field—reviews use
`Additional context`—and template-writing instructions stay in comments. References
may additionally contain reference definitions. No heading, list, quote, table, code,
HTML, or undeclared prose may masquerade as a field continuation.
The response section asks only for a plain-language answer and explicitly accepts “I
need clarification.” Decisions and clarifications also accept another option,
interpretation, or correction in the reader's own words. Reviews accept approve,
request changes, reject, or a clarification question. Revision binding and status
changes are agent- or adapter-managed.

For review-specific syntax, follow `templates/queue/review.md`. `Review target` names
exactly one repository file, Git commit/range, or HTTPS artifact; `Review revision`
binds its bytes. Local/HTTPS targets use `sha256`, while a Git target repeats the exact
`git:<...>` revision. `pending` is valid only before publication. Full context explains
the judgment but never substitutes for its target or immutable revision. Task status
paths move and are not durable context; only a pickup may use one as live context
because its claim commit deletes that request. Retry records may quote one only as
evidence of broken state.

A Git review also exposes one human-readable exact artifact. An HTTPS link must use a
supported provider's exact commit or range grammar for this repository's configured
remote. A repository-relative alternative is a regular readable text artifact whose
content, not filename, contains exact field `**Git review target:** git:<bound target>`.

An unpublished review recommends exact sentence `Wait for the exact target before
deciding.` A published waiting review recommends exactly one presented outcome:
approve, request changes, or reject. `abandoned` is agent-managed lifecycle state for a
pursuit that ends without a human review judgment, not another displayed choice. A Git
commit or range also has one visible exact-artifact link. Its destination is a
provider-neutral HTTPS URL or an existing repository-relative artifact and contains
the full bound commit id, or both full base and head ids for a range.

The explanation must be sufficient to act; references are for depth, not a missing
prerequisite. Every rendered Markdown link or image, and every definition used by a
reference-style link, lives in References. Full, collapsed, and shortcut reference
labels match case-insensitively and use their first definition; duplicate definitions
and unresolved or ambiguous reference syntax are invalid. Link each canonical destination only
once. A recommendation is evidence, not permission to hide an alternative.

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

## Project only actions the human can take now

Only `Status: waiting` is human-actionable. `awaiting-artifact` means there is nothing
ready to review, and `folding` means an agent is already recording the response.
Handovers and final replies project every and only waiting human item. This prevents a
completed answer or an unavailable artifact from being presented as another request.

Each handover projection has one queue link followed by the queue item's plain `Why
this matters` and `If you do not respond` paragraphs. It never exposes hashes, lifecycle
labels, or parser field names. The exact entry grammar lives in
`templates/handover.md`. The handover keeps its repository-relative destination. Final
chat preserves the exact rendered Action label and both paragraphs but resolves that
same queue destination for the chat surface. Inline emphasis, code, or escapes may
differ between Action and label only when the rendered text is identical after
whitespace reflow; case, punctuation, negation, brackets, and Unicode width stay exact.

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

Commit the response while status is `waiting`, then claim it in a separate one-line
`Status: folding` commit. The human changes only the plain response; an agent or
adapter manages `Reviewed revision` and all other tracking fields. Every item
predeclares `Resolution evidence`; a review's path is distinct from its target.
Deletion changes that evidence in its commit. An
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
