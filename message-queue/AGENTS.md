# message-queue/ — the canonical action bus

**Queue resolution schema:** v1
**Human action presentation schema:** v2

Every pending human action and durable cross-session agent action lives here, one per
file. Other surfaces link an item but never originate its ask. Background stays in a
durable source; the item owns live delivery, state, and an unfolded response
(`handbook/principles/files-as-messages.md`).

## Routing

The path carries three independent axes: actor (`needs-human/` or `needs-agent/`),
kind, and filename timing. Standard human kinds are `decisions/`, `clarifications/`,
and `reviews/`; standard agent kinds are `requests/` and `retries/`. An adopter may add
one documented kebab-case kind directly under either actor. Extra nesting is invalid.

- `blocking-<slug>.md`: a named current task, transition, or operation cannot proceed.
- `future-blocking-<slug>.md`: work continues until a named UTC date, event, or
  transition, then stops if the action is unresolved.
- `non-blocking-<slug>.md`: the action never stops work and names the safe unattended
  outcome. Timing is not risk severity.

The filename is canonical; never duplicate `Blocking`. Timing may only escalate
`non-blocking` → `future-blocking` → `blocking`, updating every link in one commit.
Weakening needs an authorized replacement; a concrete human response freezes timing.

## Lifecycle and content

- Copy the matching template. New human items carry exact comment
  `<!-- human-action-presentation: v2 -->` and follow
  `handbook/human-action-guide.md`; exact headings and fields live only in the template.
- Only `waiting` is human-actionable and projected. `awaiting-artifact` is not ready;
  `folding` is agent-owned. A human edits only `Your answer` or `Your review`; agents
  and controlled adapters manage tracking.
- Keep the action self-contained. `Action` and `Full context` precede collapsed
  tracking (with a blank line after its summary); review targets and revisions stay there. Use
  ordered fields and exact two-space immediate wraps; reviews use `Additional context`.
  All rendered references and used definitions live in References and each links once.
- Record each artifact-scoped `External assignment` or versioned `External source`.
  A direct link never replaces it; releasing the last binding needs trusted provider
  evidence. Unknown authorship is reviewed, never executed
  (`handbook/principles/provenance-over-position.md`).
- Commit the first human response while `waiting`; it is immutable. A counter-question
  is a disposition: claim and fold it, answer in durable evidence, then create a
  same-timing successor naming the old item in `Supersedes`. The later status-only
  `waiting` → `folding` claim freezes action. Unanswered reviews may retract to
  `awaiting-artifact`/pending and later publish; neither edge adds a response.
- Agent claims change only `open` to `in-repair`; action identity never changes.
  On the v2 activation edge, a legacy review may use only deterministic neutral or
  ancestry-proven post-merge wording for the same judgment. After activation, human
  identity never changes. Transcribe chat responses before use; timing then freezes.
- A task pickup is a non-blocking request with `Request kind: task-pickup` and one
  reciprocal backlog `task.md` link. Its atomic claim/move deletes it. Only pickups use
  moving task paths as live context; retries may quote them as broken-state evidence.
- Every item predeclares non-queue `Resolution evidence`; a review keeps it distinct
  from its target. Future timing survives response; cleanup needs fresh boundary
  evidence. UTC dates are clock-checked; other timing is agent-attested absent a
  validating adapter. Rejection withdraws its target; changes requested creates
  re-review. Retries need a cleared finding; pickups need the atomic move. Git archives resolutions.
