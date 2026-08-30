# Design notes — Stop the merge-ref recompute race from failing every stacked pull request

**Status:** decided

## Problem

`review-state-action-projection` in `.github/workflows/harness.yml` needs an immutable
revision to hand the canonical checker as `--candidate-revision`. GitHub only offers a
*mutable* one: `refs/pull/<number>/merge`, the commit it computes by merging the pull
request's head into its base. The job fetched that ref and then asserted bare equality
against `github.sha`, the value the same ref had when the event fired.

Those two agree only while nothing moves the base. Merging the parent of a stack moves
every child's base — GitHub retargets the child and recomputes its merge ref onto the new
base — so the fetched value is a *different, equally valid* commit and the assertion
fails. Stacked pull requests are this repository's normal way to sequence dependent work
(`handbook/git-workflow.md`), so the check failed on its own characteristic event, for a
reason with nothing to do with the change under review. That is the named reason the job
cannot become a required merge check today.

The constraint that cannot be traded away is fail-closed: a candidate the job cannot bind
to this event must still fail. The projection decides whether human and agent actions were
declared for a specific revision, so admitting the wrong revision is worse than failing.

## Options considered

### Option A — retry until the fetched value equals `github.sha`
Re-fetch on mismatch and compare again, up to some bound. This is the shape the wording
"recompute race" invites, and it is wrong. After a recompute the two values will never
agree, because `github.sha` names a merge onto a base that no longer exists as the pull
request's base. The loop would burn its whole bound and then fail anyway — a slow failure
in the recompute case, and a slow failure in the genuine case. It also turns a real
mismatch into something that *looks* transient, which is the failure mode most likely to
be waived by a future reader.

### Option B — drop the equality check and trust the fetched merge ref
One line, no race, no binding: any commit the ref happened to point at would be projected
as this event's candidate, including a merge of a head someone pushed after the event.
Fails open.

### Option C — bind the candidate through the merge commit's own parents
Keep `github.sha` as a fast path, and admit a *differing* candidate only when its own
object proves it belongs to this event: exactly two parents, second parent equal to
`github.event.pull_request.head.sha`, first parent containing
`github.event.pull_request.base.sha`. A merge commit's parent ids are covered by its
object id, so this is a property of the candidate itself rather than of a payload field
that may be stale. Re-resolve a bounded number of times, and fail when the bound is spent.

## Chosen

Option C. It is not a new mechanism: the sibling job
`authoritative-external-action-projection` in the same file already binds its
`pull_request_target` candidate exactly this way, with the same four checks and the same
failure messages, and it was repaired for the same class of defect (a payload revision
that GitHub computes asynchronously cannot pin anything). Reusing that binding keeps one
answer to "which revision is this event's candidate" in the file instead of two.

What changes about the recompute case is that it is no longer a mismatch at all. The
recomputed merge still merges this event's head, and its first parent still contains this
event's base, so it *is* this event's code and the job proceeds with it under its new
revision. Nothing waits for the two values to agree, so there is no race left to lose.

The re-resolution loop stays because a fetch can still lose: GitHub removes the merge ref
while a pull request is unmergeable, and can leave it briefly holding the previous value
after a push. The bound is **5 attempts, 5 seconds apart** — at most 20 seconds of added
latency, and only on the path that is about to fail anyway. It is set to cover a
provider-side recompute, which is seconds, without turning a genuinely broken pull request
into a job that looks hung. Both numbers are declared in the step's `env:` block, the loop
is a counted `while` rather than `while :`, non-numeric or zero bounds fail the step
before the loop starts, and exhausting the bound exits 1 with the last rejection reason.
There is no path on which running out of attempts produces a pass.

One thing deliberately *not* changed: the job still checks out
`github.event.pull_request.base.sha`, and still never checks out the candidate. The
candidate is read as data — parent ids and ancestry — and never executed.

## The bound had only a lower end, and that was a fail-open

The sentence above — "non-numeric or zero bounds fail the step before the loop starts" —
was true and insufficient. Re-reading this branch against its own fail-closed constraint
found the missing half, and the hole it left was not cosmetic.

`[` does not report false when an operand overflows `intmax_t`. It reports **status 2** and
writes a diagnostic, and `if` and `while` both read any non-zero status as false. So a
bound above 2^63-1 was false at the lower guard, which skipped it, and false again at the
loop condition, which skipped every iteration. The step then fell out of the loop having
bound nothing and printed whatever `ACTION_PROJECTION_CANDIDATE_REVISION` happened to
hold — the empty string. Exit 0, `revision=`, and a downstream `--candidate-revision ""`.
That is precisely the fail-open this design exists to prevent, reached without a single
guard rejecting anything. `verification.md` records the run: the pre-repair step publishing
an empty revision at exit 0.

Two changes close it, and they are deliberately independent:

- **An upper bound**, `-gt 100`, beside the existing `-lt 1`. This is not only about the
  overflow value: 9223372036854775807 is a whole number `[` compares happily, and a loop
  that would run that many times is `while :` with extra steps, which the test beside it
  already forbids. A range is what the guard meant from the start.
- **A positive check after the loop.** Reaching the `printf` has to *mean* a `break` bound
  a candidate. Inferring that from the absence of a failure is what let the overflow
  through, because every guard inside the loop is a way to **reject** a candidate, so a
  path that skips the loop skips all of them at once. An `[ -z ... ]` test and exit 1
  establishes the candidate positively instead of trusting the control flow that reached
  it.

The second is the load-bearing one. The first closes this specific value; the second closes
the class, whatever future edit or unanticipated `[` status produces it. Keeping both is
cheap, and a reader who deletes either should have to argue with a test.

The upper bound is 100 rather than a number derived from the delay. The two are set
independently in `env:`, and a cap that moved with the delay would be a second thing to
reason about for no gain — 100 attempts is already far past any provider-side recompute,
and any value above it fails in the same microsecond that 101 does.

## Core fit

**Agent substitution:** pass — the change is the shell of one CI step and the static test
that reads it. No agent runtime, prompt, transcript format, or agent-specific file is
involved; any runtime that opens a pull request gets the identical result, because nothing
here reads who produced the branch.
**Provider substitution:** pass — the pull merge ref is GitHub's name for the result of
merging a pull request, and every forge computes an equivalent. This step is the adapter
that turns that mutable provider handle into one immutable revision; the policy it feeds,
which is what must be projected for that revision, stays entirely in
`automation/check_action_projection.py`, which is unchanged. Another provider's adapter
substitutes by resolving its own equivalent handle and passing `--candidate-revision`.
**Repository substitution:** pass — any adopted repository that sequences dependent work
as stacked pull requests hits this race on every parent merge. Nothing in the step names
AgentFold content: it reads the event payload and the repository's own Git objects.
**User-global writes:** none
**Why AgentFold core:** `.github/workflows/harness.yml` is registered in
`automation/core-scope-paths.txt` as a thin provider adapter, and this is the correctness
of a gate every adopter's CI runs on every pull request. It is not local configuration, not
product code, and not separable into an overlay — the binding has to live in the step that
resolves the revision.
**Thin adapter:** canonical=automation/check_action_projection.py; optional=yes; policy=none; writes=repo-only

## What this does not settle

Whether `review-state-action-projection` becomes a *required* check is not decided here.
`memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md`
records that no check is required today and that the owner's stated next step is requiring
`reconcile-and-test` with a personal bypass once he judges the repository stable. This task
removes the technical reason this job could not be a candidate later; it does not change
the provider settings, which no file in the tree can.
