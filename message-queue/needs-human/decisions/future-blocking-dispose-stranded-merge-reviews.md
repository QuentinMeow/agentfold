# Two merge reviews can no longer be answered — change the rule, request changes, or leave them open?

**Action:** Pick A, B, or C at the bottom of this file, or describe a different disposition.
**Status:** waiting
**Filed:** 2026-07-31, by claude, from the message-queue ritual
**Why-you-might-care:** Two core changes have run on main for a week without the review each of them declared mandatory, and the repository will now accept only one answer from you — which may not be the true one.
**If-you-do-nothing:** Both reviews stay open forever and their two tasks can never reach done, because no commit an agent can make will close them.

## What you need to know

Two review files are still sitting unanswered in `message-queue/needs-human/reviews/`:

- **Test-runner Git isolation.** Stops hook-launched tests from redirecting Git writes
  into the checkout that launched them. Lives in `automation/run_tests.py`.
- **Layered development workspace.** The zone/authority design plus a read-only topology
  inspector: `docs/designs/layered-development-workspace.md` and
  `automation/inspect_workspace_boundaries.py`.

Each says "do not merge until reviewed." Both merged anyway on 2026-07-25, as PR #11 and
PR #12, with the review lines still blank. Only the review lapsed — the code itself has
been on main ever since, and both tasks have sat in review since then.

This is not last week's problem. The queue-format review you answered on 2026-07-31 was a
third stranded item; it is resolved and is not part of this decision.

The constraint on your choice comes from the reconciler, and I traced it in the current
code rather than trusting the earlier write-up:

- **Approving them does nothing.** A merge review closes only if the approval text is
  present *inside* the merge commit that crossed the boundary. Those commits are
  `d87b755` and `c9f5244`; both are permanent, and both contain the review file blank.
  You can type "approved" — the file would then sit in `folding` forever.
- **Rejecting or abandoning them is blocked too.** That path requires the task record to
  be deleted, and a task in review may not be deleted; it can only reach done, which in
  turn requires the review to be gone first. It is a closed loop.
- **"Changes requested" is the only answer the repository will accept.** It replaces each
  review with a repair request plus a fresh review bound to the repaired code — a
  boundary a future merge can honestly satisfy.

So of the four dispositions the contract defines, the mechanism now permits exactly one —
whether or not it is the one you mean. That is what this decision is really about.

One fact worth having: `automation/run_tests.py` has changed by roughly 1,100 lines since
the version you were asked to approve, so that review is stale on its merits as well. The
workspace inspector and its design doc are byte-identical to what you were asked to
approve.

## Differences

The three options differ in what gets recorded and what it costs.

Only option A lets the repository state what actually happened — the gate lapsed, the
code stands — and it is the only one that also fixes the next occurrence. Option B is
available immediately with no rule change, but it is honest only if you genuinely want
something changed; picking it to unstick the queue would be manufacturing a complaint,
which is the exact dishonesty the gate exists to prevent. Option C costs nothing today
and leaves two items and two tasks permanently stuck.

## Options

### Option A — Add an honest way to close a gate that already lapsed, then use it
You authorize a new review disposition meaning "this merge boundary was crossed without
review; the merged artifact stands; the request is retired." It approves nothing. It is
offered only when the reviewed commit range is already an ancestor of the target branch,
which Git can check mechanically, so it can never pre-authorize a merge that has not
happened. An agent implements it in the queue contract and the reconciler, then applies
it to these two.
*Example consequence:* Both reviews close against a written record that the gate lapsed,
both tasks move to done, and the next time a merge outruns its review the repository
handles it instead of escalating to you. Cost: a real implementation task on the
reconciler's most delicate area, and one hard invariant becomes slightly weaker — a merge
review can now be retired without a merge, under a machine-checked condition.

### Option B — Answer "changes requested" on both, naming a real change you want
You read the two landed changes and write what should be different. Each review is
replaced by a repair item plus a re-review bound to the repaired code. This is the path
your 2026-07-31 answer on the queue-format review took, and it worked.
*Example consequence:* The tasks stay in review until the repair merges, then finish
normally, and you get the judgment you originally asked for. Cost: you have to read about
1,500 lines of test-runner change and about 2,500 lines of workspace design and inspector
well enough to name a genuine defect — and if you have no complaint, this option is not
honestly open to you.

### Option C — Leave both open and carry the debt
Nothing is answered and nothing is changed.
*Example consequence:* The two items keep appearing at the end of every reply to you and
in every handover, the two tasks stay in review indefinitely, and the fourth occurrence
of this failure lands on your desk the same way. Nothing is lost that A or B cannot still
recover later.

## Recommendation

**Option A.** The question you were actually asked — "may this merge" — has no merge left
to authorize, so no answer you give can be the true one; the only truthful record left is
that the gate lapsed and the code stands. A is also the only option that stops this
recurring, and its weakening is narrow: the escape applies only when Git can already
prove the range is on main, so no future merge can be waved through with it.

What would change this: if you already have a concrete complaint about either change,
choose B and say what it is — that is strictly better than A, because it gets the
judgment as well as the closure. If you would rather not touch the queue lifecycle at all
right now, C is defensible; the cost is visible and reversible.

**Your answer:** ______

## Record

**Full context:** `message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md`; `message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md`
**Resolution evidence:** `memory/decisions/2026-07-31-stranded-merge-review-disposition.md`
**Blocks at:** transition:complete task:2026-07-24-isolate-test-git-environment task:2026-07-24-layered-development-workspace
**Until then:** Every other task, queue item, and merge proceeds normally; only these two tasks are held short of done.
