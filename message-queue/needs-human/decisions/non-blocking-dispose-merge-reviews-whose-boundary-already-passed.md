# How should three merge reviews be disposed of, now that their merge already happened without them?

**Status:** waiting
**Filed:** 2026-07-31, by claude, from task `2026-07-30-clear-the-stuck-queue-items`
**Action:** Choose option A, B, or C for all three stranded merge reviews, or state another disposition.
**Full context:** `handbook/human-action-guide.md`; `memory/decisions/2026-07-23-live-queue-obligations-only-weaken-with-evidence.md`; `memory/decisions/2026-07-23-queue-resolution-preserves-review-intent.md`
**Why-you-might-care:** Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate.
**If-you-do-nothing:** The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
**Resolution evidence:** `memory/decisions/2026-07-31-merge-boundaries-crossed-unreviewed-disposition.md`
**Answer by:** 2026-10-29
**If unanswered:** The crossed boundaries are disposed of by the human-gating model: the reviews stay live and answerable, and their tasks complete without them.

## What you need to know

Three reviews under `message-queue/needs-human/reviews/` each say
`Blocks at: transition:merge`, each binds an exact Git range, and each is still `waiting`
with `Review outcome: pending` and an empty response line. All three ranges are already
ancestors of `main` — the merges happened outside the repository while the items sat
unanswered. Replaying the merge transition today reports all three as unresolved, which is
the repository proving its own gate was crossed.

Git evidence cannot un-cross a boundary. A merge-bound approval is only fresh at a merge
whose active base equals the reviewed base, so even a full approval written today has no
merge left to authorize. That is why these three cannot be closed the ordinary way, and it
is why an agent should not pick their disposition: the choice is between recording a
judgment that was never given, discarding the request for it, and asking a different
question instead.

The three, with the change each one governs:

- `future-blocking-review-first-class-message-queue.md` — the queue-ownership invariant,
  timing prefixes, and enforcement that every human and cross-session agent action now uses.
- `future-blocking-review-test-runner-git-environment-isolation.md` — the boundary that
  stops hook-launched tests from writing into the invoking checkout.
- `future-blocking-review-layered-development-workspace.md` — the layered workspace design
  and its read-only topology inspector.

Nothing about these three was changed by the session that filed this item. Their action
text, their bindings, and their blank response lines are exactly as they were.

## Differences

The three options differ in one thing: whether the judgment you were asked for is still
collected, and whether the three tasks can ever leave review.

- **Recording the judgment** matters if the merged designs might need revising or reverting;
  it is the only option that still gets your opinion into the repository.
- **Retiring the ask** matters if the code has since been exercised enough that a fresh
  opinion adds nothing, and the cost of carrying three permanently unsatisfiable items is
  the real problem.
- **Unsticking the tasks** is independent of both: only options that give the items a
  boundary a commit can actually cross let those three tasks reach done.

## Options

### Option A — Answer them exactly as written
Fill each blank review line with a real disposition and let the items become `folding`.
*Example consequence:* Your judgment is recorded and immutable, but the three items stay
live and the three tasks stay in review, because a merge-bound approval needs a future merge
to authorize and there is none. A negative answer would also require restoring the reviewed
base of code that is already live on main.

### Option B — Record that the boundary passed unreviewed, then retire the three
A new decision record states plainly that the pre-merge gate for these exact ranges was
crossed without an answer and that the merged code stands. An agent then deletes the three
items against that record and drops their task backlinks.
*Example consequence:* The queue stops carrying unsatisfiable asks and the three tasks reach
done, while the crossing itself stays permanently visible in that record and in Git history.
The specific judgment you were asked for is never given, so if one of these three designs is
wrong, it is found later by other means.

### Option C — Retract each one and refile it against the state that actually exists
Each unanswered review retracts to `awaiting-artifact` with pending binding — an edge the
queue contract already allows and which adds no response — and a replacement asks the
question that is still answerable: does this stay, get revised, or get reverted. The
replacement binds a stable local artifact and a boundary a commit can cross.
*Example consequence:* You still get to judge all three, and a "revise" or "revert" answer is
actionable because the code is on main and can be changed. The cost is three fresh reviews of
large landed changes, and the original question — may this merge — is retired unanswered
rather than answered.

## Recommendation

Option C, because it is the only one that neither invents your answer nor throws the request
away, and it is the only one that leaves the three tasks with a boundary the repository can
actually cross.

**Your answer:** ______
