# Writing human actions that can be decided

A **human action** is one file that asks this repository's owner for one thing. Its only
canonical home is `message-queue/needs-human/`. Every other surface carries a short link to
that file and never the ask itself. That covers pull requests, issues, chat, tasks, and
handovers.

**The one test:** could someone who has never seen this repository answer correctly, from
this file alone, without wanting to ask a question first? A human action succeeds only when
a zero-context reader can tell what to do and what their answer changes. If they would have
to open something else, the item is filed wrong.

This guide owns four things: who may be asked, what the file must contain, how the owner
answers, and how the item resolves afterwards.

## Where each rule lives

This guide never restates a field list. Copy the schema; never write one from memory.

| You need | Read |
|---|---|
| the exact fields, their spellings, and their order | `templates/queue/` |
| which filename prefix a timing earns, and how live timing may move | `message-queue/AGENTS.md` |
| decision-specific content rules | `handbook/decision-guide.md` |
| how to write the prose that fills each slot | `skills/explain-to-human/scenarios/queue-item.md` |
| what a queue leaf accepts | that leaf's own `README.md` |

## First decide whether the judgment is really the human's

Do not turn incomplete agent work into a vague request for approval.

| The judgment is | Test | What you do |
|---|---|---|
| agent-owned | it can be checked from code, text, tests, or a diff | run the check, record the evidence, and ask for human review only if judgment is left over afterwards |
| human-owned | it is a preference, an authority call, a one-way door (a change that cannot be undone cheaply), or a reading of what the human meant | file the queue item before you mention the question in any other channel |

Example. "Does every `block` statement apply only in hard mode?" is a text audit, so the
agent runs it. "May merge-protected deployments claim data never reached the remote?" is a
security promise whose alternatives need explaining, so it is the owner's.

## One file per answerable judgment

Several independently answerable judgments become several files. A single jargon-heavy
checklist is not a shortcut.

Example. "Please fix both the race and its missing regression" is two questions, so it
becomes two files. Filed as one, the owner answers one half and there is no repair. The
first concrete response is immutable, and no agent may edit it.

## What the filled item must let a stranger do

Copy the matching template from `templates/queue/`, then fill it so a zero-context reader
can do all five of these:

1. Identify one concrete response.
2. Read the decisive source wording here, with a durable link for depth when needed.
3. Understand the meaningful dispositions and how their consequences differ.
4. See one small example.
5. Know the boundary, or the safe result of leaving it unattended.

The summary must be enough to act on by itself. The link to full context is depth, never a
missing prerequisite. And a recommendation is evidence, not permission to hide an
alternative.

## Point every path at something that will still be there

A task's path is not durable, because a task's status is the folder it sits in and that
folder changes (`tasks/AGENTS.md`). The rule is the whole item, not one field: no
`tasks/<status>/…` path may appear anywhere in a queue item — not in `Full context`, not
in `Resolution evidence`, not in the prose. Name the durable artifact, and refer to a task
by its id. Two exceptions exist:

- A **task-pickup request** may name a moving task path as live context, because the commit
  that claims the task also deletes the request.
- A **retry record** may quote a moving path, but only as evidence of broken state.

`Full context` in particular names the durable source behind the ask, and it is the field
authors reach for a task path first.

## The order of the file is the contract

The owner reads the file top to bottom exactly once. Its order is therefore a rule, and the
reconciler enforces it. (The reconciler is the script that checks every repository
invariant before a commit is allowed.)

| Position | What sits there |
|---|---|
| above the first heading | three sentences and nothing else: what is asked, what it changes in the world, and what happens if it is never answered |
| next | today's real behaviour, kept separate from the proposed change and from the adjacent things a reader will wrongly assume are in scope |
| next | the choices, each under its own heading, each with its cost and one concrete consequence of picking it |
| next | the recommendation, with the strongest case against it beside it and a graded confidence that names what was not checked |
| next | the answer line |
| below the answer line | everything a machine reads, under `## For the record` |

Two of those positions carry a reason worth stating. The three opening sentences are the
whole notification the owner sees on a phone, which is why nothing may stand above them.
The recommendation sits after the choices so that it cannot anchor them.

Field names, headings, and their exact order live in `templates/queue/`.

## Three rules only a reviewer can enforce

These three are judgment, not syntax. No check can catch a violation, so review is their
only control.

- **The title is a question**, answerable by someone who does not know this repository, and
  it never states the verdict. Not `Fix the merge gate`. Yes: `Should a branch be allowed
  to merge while a review it filed itself is unanswered?`
- **`Today` says what actually happens now.** When nothing is implemented yet, `Today` says
  *nothing is implemented*. Describing the proposal twice — once as "today" and once as
  "the change" — leaves the owner with no state to judge the delta against.
- **The counter-case is the strongest argument for a different answer**, not a hedge. An
  agent can satisfy this slot with confidently-calibrated mush, and no check can tell.

## Never make the reader do bookkeeping

Never ask a person to copy a hash, a revision, a field name, or any vocabulary you offered
them. A plain-English sentence is a complete answer. The agent that folds the answer does
the bookkeeping. It also shows the person how it read their words before acting. (Folding
is the claim that turns a committed human response into repository change.)

When the answer depends on another source's wording, quote the decisive passage and link
its heading or selected lines. Optional background belongs below the answer, inside the
record fold. If no source wording determines the answer, use the template's explicit
no-source sentence; it never replaces a quotation from a local file being reviewed.
`Full context` still belongs below the answer line.

A file that already carries a concrete response is a record, not an ask. Never reformat it.
It keeps the schema it was written under.

## One edit is the whole answer

The owner replaces one blank with one sentence and commits. Nothing else on the page is
theirs. A repository path they name inside that sentence is prose for the folding agent to
read, never a link the commit has to resolve.

An item whose acceptance depends on a second hand-written human field is filed wrong. It
cannot be answered from a phone, and there is no repair: the first response is immutable
and human text is not editable.

## Choose the kind; timing is decided elsewhere

| Leaf | Use it for |
|---|---|
| `decisions/` | choosing among alternatives only the human may authorize |
| `clarifications/` | correcting an interpretation, or supplying missing intent |
| `reviews/` | judging a named diff, artifact, or claim |

Timing is the independent second axis, and `message-queue/AGENTS.md` owns it. Three things
live there, not here:

- which filename prefix each timing earns;
- which way a live action may move;
- what evidence a UTC date, a named event, or a custom transition can supply.

Choose the prefix there. The only timing rules stated in this guide are the ones below,
about when a review's outcome closes its boundary.

## Link the item from everywhere; fork it nowhere

Every other channel links the same live item.

- A pull request's "What to review" entry links its canonical item. One entry carries one
  link, and any surrounding explanation stays declarative.
- Task and handover projections never carry a second status or a second answer slot. A
  projection is a link plus a summary; it never owns state.
- A chat answer is transcribed into the item before anyone uses it.
- When a person writes prose on a provider — a GitHub comment, say — with no queue link,
  the receiving agent transcribes it. Never ask that person to rewrite their own words.

## Fold the answer, then delete the item

1. Commit the response while the item's status is `waiting`.
2. Claim it in a separate `Status: folding` commit. That commit changes only the status,
   plus — for a review — the two agent-owned binding fields described below.
3. Fold the answer into its durable source, then delete the item in the resolving commit.

Every item predeclares `Resolution evidence`: the durable non-queue file that folding this
answer will change. For a review, that path is distinct from the review's target. The
commit that deletes an item is the commit that changes that predeclared evidence.

The first response freezes the item's binding and its evidence. After valid cleanup, Git
history archives the delivery; until then the queue is the only live dependency surface.

## Reviews: the two fields the agent owns

The human fills only `**Your review:**`. `Reviewed revision` and `Review outcome` are the
agent's. The agent writes them in the one `waiting` → `folding` claim commit, and only over
a response the parent commit already carried.

Both are write-once.

- `Reviewed revision` repeats the frozen `Review revision`, so a classification can never
  be re-pointed at other bytes.
- `Review outcome` can never be amended.

Those fields still buy everything they bought before. `queue_deletion_problem` is the
reconciler's certificate that a queue file may be deleted. It refuses to resolve a review
that is unbound or that lacks a terminal outcome. A boundary still needs `approved`, and
`approved` accepts the exact revision.

**Why the fields are the agent's and not the human's.** The reconciler cannot read English,
so it cannot verify that `approved` is a truthful reading of "Looks good to me". It bounds
the lie instead of preventing it. The outcome lands in a separate, attributable commit,
beside the human's immutable words. It cannot exist at all until their response is already
committed (`memory/known-issues/2026-07-31-review-outcome-classification-is-attested.md`).

## Reviews: target, revision, and the retraction path

`templates/queue/review.md` owns what `Review target` and `Review revision` may hold, and
when `pending` is allowed. Two content rules are this guide's:

- `Full context` explains the judgment. It never substitutes for the target or its
  immutable revision.
- An unanswered review whose artifact changes first **retracts**. Its status becomes
  `awaiting-artifact`, its binding becomes pending, and its response fields go blank. A
  later commit republishes the replacement binding. Neither the retraction nor the
  publication may add a response.

## Reviews: when the outcome is not `approved`

A rejected or abandoned review never authorizes crossing its boundary.

| Outcome | What the agent must then do |
|---|---|
| `changes-requested` | Create two items. One same-timing `needs-agent` action solely owns the concrete repair, its context, and its resolution evidence. One distinct `needs-human` re-review awaits that artifact and depends on the repair action, so the boundary stays closed without duplicating the repair. |
| `rejected` | End pursuit. Restore a rejected Git candidate path-for-path to its reviewed base; a rejected local target changes or disappears. A task-bound rejection stays live until that task is removed. |
| `abandoned` | End pursuit, on the same terms as `rejected`. |
| `unanswerable` | The reader could not decide from what the item showed them. Create one new, distinct, unanswered `needs-human/reviews` item that supplies the missing context and keeps the same judgment, artifact, revision, and timing boundary. Nothing about the subject was decided; the replacement stays ready for review. Follow the binding and lineage rules in `templates/queue/review.md`. |

An unanswerable review follows the ordinary claim and evidence-changing resolution flow;
its human response is never rewritten. Re-asking repairs the explanation, not the artifact.
If the artifact later changes, use the retraction and publication path above.

Distinct cancellation evidence records the disposition without rewriting the reviewed
bytes. The legacy value `not-approved` is the old spelling of `changes-requested` and
carries exactly its obligations — the reconciler treats the two as one outcome.

---

# Depth — stop above this line unless you need it

Everything below is for two situations only. The first is a review that holds a repository
boundary open. The second is a queue item bound to an external provider such as GitHub. A
reader writing an ordinary decision or clarification never needs this section.

## A review that holds a boundary open

For a `future-blocking-*` item, a terminal outcome is response-terminal but not
boundary-terminal. Keep the folding item live until the boundary is actually crossed.

Two kinds of review bind two different things:

| Review kind | Binds | Its receipt | Cleanup requires |
|---|---|---|---|
| task-lifecycle | a stable local artifact file | the linked folding approval | the task still sitting past that transition |
| merge | the candidate Git range | the same folding approval | an exact two-parent merge carrying the receipt in previously admitted target history |

A merge review's approval stays fresh only through queue-only tail commits — commits
appended after the reviewed range that touch queue files and nothing else. A merge made
inside the candidate itself is not evidence.

Timing closes on its own terms. A dated review closes at or after its date. Named events
and custom transitions first escalate to blocking; custom operations are already blocking.
Without a controlled adapter (a trusted program that reports external state to the
repository), changed evidence records only the agent's acknowledgement, not a verified fact.

## Provider assignments each get their own item

Each provider assignment gets a distinct queue item. Its `External assignment` field
exactly copies the adapter's opaque binding of provider, stable artifact, role, actor kind,
and principal. Another artifact, or a generic review, may not reuse that binding for a new
assignee or reviewer. The adapter that enforces this is described in `automation/AGENTS.md`.

A provider's checked no-action acknowledgement covers its whole selected actor surface. So
a GitHub pull-request description uses exactly `No queued action requested.` only when
neither a human nor an agent/bot assignment exposes an action.

## Binding an item to an external source

Every active source has at least one item carrying the adapter's opaque, content-versioned
`External source`. A direct provider link is a projection; it never replaces that durable
binding. One source may bind several items across different actors.

Example. "Please fix both the race and its missing regression" may become two request
files that share one source binding and carry separate `Action` fields.

Keep bound items live while the provider still reports the source as current. On GitHub
that means an open artifact's current conversation comment, effective formal review, or
unresolved diff thread at a replayed snapshot. **Replay** is re-reading current provider
state instead of waiting for an event; the **snapshot** is what that re-read returns.

| Provider change | Effect on the binding |
|---|---|
| a comment is edited | it gets a new identity |
| a comment is deleted, or the artifact is closed | the source is removed |
| a review is superseded or dismissed, or a thread is resolved | it leaves the next replayed snapshot and permits normal queue resolution |

The binding proves durable routing and source version. It does not prove that the agent's
transcription captured every nuance — ordinary review still judges that fidelity.

## What a GitHub adapter forces into the queue

These rules do not consult English. No-action prose on the provider cannot waive them.

- Every open issue is a forced, directionless source. Its projected or bound queue path
  chooses the concrete actor, and even purely informational wording needs at least a
  non-blocking triage item.
- Every non-empty conversation comment on an issue or pull request, and every effective
  formal review, is structural `needs-agent` triage.
- A changes-requested review is forced even when its body is empty.
- Whenever current state is replayed, unresolved diff threads remain forced action state.

GitHub emits no Actions event for resolving or reopening a thread. Replay therefore also
runs when a pull request enters a merge queue, GitHub's serialized merge lane. Even so, the
evidence is only as fresh as the last supported event.

A hard claim that a currently unresolved thread cannot merge needs GitHub's own "Require
conversation resolution before merging" rule. That is `required_review_thread_resolution`
in a ruleset, or `required_conversation_resolution` in classic branch protection. Even that
rule does not prove that every transient reopen-then-resolve toggle was durably queued.

## Releasing the last source binding

At controlled Git admission, removing the final binding also requires the trusted adapter
to classify the exact old identity as released. Provider state that reads as current, or
that is unavailable, blocks the removal.

That check needs protected required-check admission. Without it, a direct write can land
before the post-push failure that would have caught it.
