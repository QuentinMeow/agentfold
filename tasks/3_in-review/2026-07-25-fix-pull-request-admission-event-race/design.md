# Design notes — Make the two admission checks pass on a freshly opened pull request

**Status:** decided

## Problem

Both admission jobs read repository records at one revision and validate untrusted
external prose — pull-request body, review comments, assignments, external-source
bindings — against those records. That revision is what a green check is about, so the
job fetches refs/pull/N/merge and compares it against a revision the event payload
asserts. The merge ref is mutable: GitHub recomputes it on every head push and on every
base advance. The comparison existed to prove the ref had not moved out from under the
event, not to distinguish a trusted source from an untrusted one — both the ref and the
payload come from GitHub and are equally authentic. They differ in time: the payload is
a snapshot pinned to the event, the ref is live.

The field carrying that pin was `github.event.pull_request.merge_commit_sha`, which
GitHub computes asynchronously. On the `opened` event it arrives empty, after a
`synchronize` it is stale, and once the pull request closes it names the real merge
commit rather than the test merge. So the pin was unavailable exactly when it was
needed, and both required checks were red on arrival for every pull request.

Workflow run 30176317631 on pull request 13, fired by `opened`, recorded an empty
expected revision in the action-projection job and the tip of the default branch in the
source-release job, while the sibling `pull_request` run 30176317623 for the identical
event resolved the same merge commit through `github.sha` and passed. The merge
computation was therefore complete; only the `pull_request_target` payload field lagged.

## Options considered

### Option A — Merge-ref fallback when the payload field is empty

The job takes whatever refs/pull/N/merge resolves to whenever the payload carries no
revision. This drops the pin precisely in the state the pin exists for, so the check
fails open on the most common event, and it leaves the source-release job untouched,
whose field is never empty and merely wrong.

### Option B — Skipping the opened event

The jobs do not run on `opened` and rely on a later event. A skipped required check on
GitHub is neutral rather than failing, and no second event is guaranteed, so the author
of a pull request selects whether the gate runs at all. The failure is also not specific
to `opened`: pull request 14 hit it on `synchronize`.

### Option C — Bounded REST retry for merge_commit_sha

The job re-reads the field from the pull-request API until it is populated. The API
returns the same live, mutable quantity as the ref over a different transport, so the
comparison proves that two GitHub surfaces agree now rather than that either matches the
event; both can advance together. It also adds a network dependency and a retry budget
inside a gate whose only job is to fail closed.

### Option D — Corrected fallback with an explicit empty guard

The source-release job stops treating `github.sha` as a candidate and both jobs reject an
empty revision with a message. This is correct as far as it goes and is included in the
chosen option, but on its own it only makes the two jobs fail consistently instead of
making either pass.

### Option E — Parent-shape pin to the event head

The payload always carries `pull_request.head.sha` and `pull_request.base.sha`, which
never move for a given event. A merge commit's parent object ids are covered by its own
object id, so a candidate whose second parent equals this event's head cannot be a merge
of any other head.

## Chosen

Option E, with Option D folded in. Each job requires the fetched candidate to be a
two-parent merge commit whose second parent is this event's `head.sha` and whose first
parent contains this event's `base.sha`, and fails with a message on every other shape —
an unmergeable pull request, a vanished merge ref, a raced head, an unexpected parent
count, or an empty payload revision. The source-release job binds `github.sha` only on
`push`, where it is that event's own candidate.

The revision handed to `automation/check_action_projection.py` is the same immutable
merge commit as before; what changed is when the binding becomes knowable.

One relaxation is deliberate. The old equality also pinned the base side to the exact
base tip at event time, while the new check requires only that the event's base is
contained in the merge's first parent. GitHub recomputes the merge ref when the default
branch advances and the payload does not follow, so exact base equality reproduces the
same red-on-arrival failure. Advancing the default branch needs push access to it, which
already outranks opening a pull request, and `automation/check_action_projection.py`
independently re-verifies that the base revision is an ancestor of the candidate.

The `issue_comment` path of the action-projection job still takes the merge ref with no
pin, because that payload names no head revision. That trust ceiling predates this
change and is unchanged by it.

## Core fit

**Agent substitution:** pass — the jobs run provider-independent repository commands that any agent runtime reproduces locally
**Provider substitution:** pass — another provider supplies its own event head and merge candidate, and the parent-shape binding is plain Git
**Repository substitution:** pass — every adopted repository admitting pull requests needs its candidate pinned to the event that named it
**User-global writes:** none
**Why AgentFold core:** the admission gates bind external prose to an immutable repository revision, which is the boundary AgentFold enforces in every adopted repository rather than local setup or one product's workflow
**Thin adapter:** canonical=automation/check_action_projection.py; optional=yes; policy=none; writes=repo-only
