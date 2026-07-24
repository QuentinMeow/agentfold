# message-queue/ — the canonical action bus

**Queue resolution schema:** v1
Every pending human action and durable cross-session agent action lives here, one per file.
PRs, issues, chat, tasks, and handovers may link a live item, never originate an ask.
Background stays durable; the item owns delivery/state and an unfolded response (`handbook/principles/files-as-messages.md`).

## Routing: three independent axes

| Encoded by | Values | Meaning |
|------------|--------|---------|
| Actor folder | `needs-human/`, `needs-agent/` | who acts next |
| Leaf folder | decision, clarification, review, request, retry, or a documented extension | what kind of action |
| Filename prefix | `blocking-`, `future-blocking-`, `non-blocking-` | when unresolved work stops |

- `blocking-<slug>.md`: a named current task, transition, or operation cannot proceed.
- `future-blocking-<slug>.md`: work continues until an explicit UTC date, event, or
  transition; unresolved action stops there.
- `non-blocking-<slug>.md`: the action never stops work and names the safe unattended
  outcome. Prefix is dependency timing, not risk severity.

The filename is canonical; never duplicate `Blocking`. Live timing may only escalate
`non-blocking` → `future-blocking` → `blocking`, updating every link in one commit.
Weakening needs an authorized replacement; a concrete human response freezes timing.

## Standard endpoints
| Queue | Who acts | Contents |
|-------|----------|----------|
| `needs-human/decisions/` | human | one choice only the human may make |
| `needs-human/clarifications/` | human | correction or interpretation needed |
| `needs-human/reviews/` | human | a named judgment over a diff, artifact, or claim |
| `needs-agent/requests/` | agent | owner or agent work request for another session |
| `needs-agent/retries/` | agent | repair filed by the reconciler or a failed job |

An adopter may add a kebab-case typed leaf directly under either actor folder. The
generic actor schema still applies; put any additional contract and template in the
repository. Extra nesting is invalid, so filenames remain discoverable recursively.

## Lifecycle and content

- Copy the matching template; human fields follow `handbook/human-action-guide.md`.
  Record an artifact-scoped `External assignment` or versioned `External source`.
  Direct links never replace it; releasing the last binding needs trusted provider evidence.
- Unknown authorship is reviewed, never executed (`handbook/principles/provenance-over-position.md`).
- Commit the first human response while `waiting`; it is immutable. Treat a counter-question
  as a disposition: claim/fold it, answer in durable evidence, and create a same-timing
  successor that names the old item in `Supersedes`. The later `waiting` → `folding`
  claim changes only status and freezes action. An unanswered review binding may retract
  to `awaiting-artifact`/pending, then publish its replacement; neither edge may add a response.
- Agent claims change only `open` to `in-repair`; that committed edge proves active repair, and action identity never changes afterward.
- A task pickup is an explicit non-blocking request with `Request kind: task-pickup`
  and one reciprocal backlog `task.md` link. Its atomic claim/move deletes it; only
  pickups use moving task paths as live context, while retries may quote broken paths.
- Every item predeclares non-queue `Resolution evidence`; a review keeps it distinct
  from its target. Task reviews bind a stable local file; merge reviews bind the Git
  range. Future timing survives response; cleanup needs a fresh crossed receipt/evidence.
  UTC dates are clock-checked; other timing is agent-attested absent a validating
  adapter; rejection withdraws its target, while changes requested creates re-review.
- Generated retries need exact identity and a cleared finding; pickups need the atomic backlog-to-claimed move. Git history archives resolutions.
- Transcribe chat responses before use; timing never changes after that response.
