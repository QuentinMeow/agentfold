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

Every other channel links the same live item. A PR “What to review” section may summarize
the action and source, but cannot add a new reviewer question. A chat answer is first
transcribed into the item. A task's `Queue actions` field and a handover's “Needs your
attention” section link it; neither carries a second status or answer slot.

After a response, claim the item, fold the answer into its durable source, record an ADR
when it decides architecture or policy, and delete the item in the same resolving commit.
Git history archives delivery; the durable source preserves the result.
