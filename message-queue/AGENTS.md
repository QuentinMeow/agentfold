# message-queue/ — the canonical action bus

**Queue resolution schema:** v1
**Human-attention format:** v1
**Human gating schema:** v1
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
- `future-blocking-<slug>.md`: work continues until an explicit UTC date, event, or transition; unresolved action stops there.
- `non-blocking-<slug>.md`: the action never stops work and names the safe unattended outcome. Prefix is dependency timing, not risk severity.

The filename is canonical; never duplicate `Blocking`. Live timing may only escalate `non-blocking` → `future-blocking` →
`blocking`, updating every link in one commit. Weakening needs an authorized replacement or the human-gating activation edge below; a concrete human response freezes timing.

## Nothing a human owes holds a Git edge

Merging, moving a task, and recording it done are revertible, so they never wait. A `needs-human/` item may withhold only the
start of a task still in `0_backlog` (`Blocks at: transition:start task:<id>`) or one act with no undo
(`Blocks now: operation:<name>`); `transition:merge|review|complete` and `Blocks now: task:<id>` are unspellable there, and no
human item justifies `2_blocked`. Everything else is `non-blocking-`, filed and merged with the question still open. Each carries
`Answer by:` (UTC); when it passes, re-surface the item and set a new date with `Re-asked:` — never write an answer nobody gave. `needs-agent/` timing is unchanged.

Standard leaves are `needs-human/{decisions,clarifications,reviews}` and `needs-agent/{requests,retries}`; each leaf's own `README.md` states what belongs in it.
An adopter may add a kebab-case typed leaf directly under either actor folder; the generic actor schema still applies, so put its contract and template in the repository. Extra nesting is invalid, so filenames remain discoverable recursively.

## Lifecycle and content

**File it.** Copy the matching template; `templates/README.md` owns copy-and-fill. Human fields — who may be asked, the
file's order, and how it resolves — follow `handbook/human-action-guide.md`. Under the format marker above, a live
unanswered human item leads with the ask and keeps every machine field below its answer line. Record an artifact-scoped
`External assignment` or versioned `External source`; direct links never replace it, and releasing the last binding needs
trusted provider evidence. Unknown authorship is reviewed, never executed (`handbook/principles/provenance-over-position.md`).

**Answer it.** A human answers in one edit: one immutable sentence in the response blank, committed while `waiting`; a
repository path named inside it is prose, not a link claim. `Reviewed revision`/`Review outcome` are the agent's, written
once on the `waiting` → `folding` claim edge and only over an already-committed response; that claim changes nothing else
and freezes action. An unanswered review binding may retract to `awaiting-artifact`/pending, then publish; neither edge may
add a response. Transcribe chat responses before use; timing never changes after that response. A counter-question is a
disposition — `handbook/decision-guide.md` says how to fold it and file the same-timing `Supersedes` successor.

**Agent items.** Agent claims change only `open` to `in-repair`; that committed edge proves active repair, and action
identity never changes afterward. A task pickup is an explicit non-blocking request with `Request kind: task-pickup` and
one reciprocal backlog `task.md` link; its atomic backlog-to-claimed move deletes it. Only pickups use moving task paths
as live context, while retries may quote broken paths. Generated retries need exact identity and a cleared finding.

**Resolve it.** Every item predeclares non-queue `Resolution evidence`; a review keeps it distinct from its target and is
owned by one task — by boundary, or by the task its `Filed:` provenance names. Future timing survives
response; cleanup needs the crossed receipt for a start gate and changed evidence otherwise. UTC dates are clock-checked, other
timing is agent-attested absent a validating adapter. What each outcome then owes — rejection withdrawing its target,
changes-requested creating a repair action plus a re-review — is in `handbook/human-action-guide.md`. Git history archives resolutions.
