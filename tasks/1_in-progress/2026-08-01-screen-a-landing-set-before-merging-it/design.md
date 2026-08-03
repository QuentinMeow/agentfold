# Design notes — Screen a set of branches for collisions before any of them merges

**Status:** decided

## Problem

A pull request's green light is evidence about that branch, not about the trunk it is
about to join. On 2026-08-01 five individually green branches merged and the trunk went
red immediately, because a check added on one leg met text added on another for the first
time in the merge commit (`memory/lessons/automation/green-branches-can-merge-to-red.md`).
`handbook/git-workflow.md` answered that by telling agents to screen a landing set before
merging any of it, and nothing screened anything.

The constraints are hard ones. Python standard library and Git only, so the screen runs on
a bare clone with no network. It has to work on the Git that is actually on `PATH`, which
on this machine is 2.23.0 while the system one is 2.50.1. And the checks it runs are the
repository's own gates, which have opinions about what they may be pointed at.

Four choices had to be made.

## Options considered

### Option A — where the pairwise conflict screen gets its answer

`git merge-tree --write-tree` performs a full three-way merge without a working tree and
reports conflicts by exit status. It arrived in Git 2.38. Under Git 2.23 the same argument
list means something else entirely: `merge-tree` there takes three tree-ish arguments, so
`--write-tree` is read as a revision and the command dies with `fatal: unknown rev
--write-tree`, exit 128. A screen that treats any nonzero exit as "these two collide"
therefore reports every pair as conflicting on the older Git, which is worse than having no
screen at all — it is a tool whose whole job is to say "this set is safe" answering
"nothing is ever safe" in a voice indistinguishable from a real finding.

Version-string parsing was rejected: it answers a question about spelling, not about
behaviour, and a vendor build can carry either. The screen instead runs a **capability
probe** — the exact command it intends to use, with the exact flags, merging the pinned
trunk with itself, which must succeed and print a tree object id. Anything else (nonzero
exit, no tree id, `git` missing) means the capability is absent.

The fallback is a real merge in a scratch worktree: check out leg A detached, `git merge
--no-commit --no-ff` leg B, read the unmerged index entries, `git merge --abort`. It is
slower and needs a writable scratch directory, and both were verified to work under Git
2.23. `--conflict-probe merge-tree|worktree|auto` forces either path, which is what makes
"the two agree" a claim anyone can re-check rather than an assertion.

An index-only fallback (`read-tree -m --aggressive` into a temporary index) was rejected:
it resolves only trivial cases, so two non-overlapping edits to one file come back
unmerged, and the screen would report false collisions instead of no collisions.

### Option B — running the reconciler against a merge

`validate_range_candidate` in `automation/reconcile/reconcile.py` binds `--range` to the
committed candidate: the captured `_GIT_HEAD_OID` must be the range head or the exact
synthetic merge of base and head, and it refuses a candidate carrying staged changes. A
`git merge --no-commit` leaves HEAD at the pre-merge tip with the whole merge staged, which
fails both halves at once. The merge must therefore be **committed** before the reconciler
sees it. Committed as an ordinary two-parent merge of the previous integration head and the
leg tip, it satisfies the synthetic-merge branch exactly, and
`--range <previous-head>...<leg-tip>` is accepted.

That collides with the narrow test lane. `run_tests.py --staged` reads `git diff --cached`,
which is empty once the merge is committed, so ordering the merge as commit-then-check
turns the per-leg test lane into zero tests. The order per leg is therefore: merge with
`--no-commit`, run the staged test lane against exactly the bytes a pre-commit hook would
see, commit the merge, then run the reconciler at the merge transition. Each gate is run
where its own contract can answer.

The commit is made with `core.hooksPath` pointed at an empty directory. This is not a
`--no-verify` bypass of a gate the work owes: the hook's three checks are core scope, the
reconciler, and the staged test lane, and `build` runs the reconciler and the test lane
itself, with the `--at-transition merge --range` arguments the hook cannot supply. Letting
the hook run would double the cost of every leg and, worse, would surface a merge-boundary
failure as an opaque failed commit instead of a named finding with its bracketing commits.
The commits are scratch: they live in a git-ignored workspace and are never pushed.

### Option C — where the integration happens, and what survives it

`build` needs a working tree it can merge into without touching the caller's checkout,
because agents run in parallel worktrees and a landing screen must never move anyone's
branch. Three candidates: a second clone (correct but copies the object store and cannot
see refs created after it), a branch in the caller's checkout (moves shared ref state), or
a detached `git worktree` under the ignored `tmp/` scratch root.

The detached worktree wins: no ref in `refs/heads/` is created or moved, the object store is
shared so nothing is copied, and the merge commits stay reachable from that worktree's HEAD,
which is what keeps them from being garbage collected between `build` and `verify`. The
price is that the workspace must survive until `verify` runs; `build` prints its path and
`verify` fails with the "cannot run" status, not a finding, when the recorded head is gone.

`plan` writes `tmp/integration/<stamp>/manifest.json` and never rewrites it; `build` writes
`build.json` beside it. Two files rather than one because the manifest is the pinned record
of what was screened, and a tool that edits its own evidence after the fact is a tool whose
evidence proves less. `verify` reads both from the same directory.

### Option D — what a failing leg reports

The failure that motivated this task belonged to no branch, so "leg 3 failed" is not enough
to act on: the reader needs to know which two commits the failure sits between. Every
failure `build` reports therefore names its bracket — the integration head before the merge
and the leg tip being merged in, plus the merge commit itself once one exists — and `build`
stops there rather than continuing, because every later leg's result would be conditioned on
a broken tree.

## Chosen

A, B, C and D as described: a capability-probed conflict screen with a forced-fallback
option, a per-leg order of `--no-commit` merge → staged tests → commit → reconciler at the
merge transition, a detached scratch worktree under `tmp/`, and a first-failure report that
names its bracketing commits. None of these is a one-way door: the script is new, nothing
else reads its output, and its manifest lives in a scratch directory.

Two things stay deliberately out. A `land` verb would be `gh` calls end to end and fails the
core-admission guardrail; that procedure is prose in `handbook/git-workflow.md`. Bisect-style
failure attribution is not built: both real incidents in this repository's history were
resolved by two `git log` calls, and the honest worst case for delta debugging over a landing
set is dozens of full gate evaluations ending in "unattributed".

## Core fit

**Agent substitution:** pass — the tool is invoked as `python3 automation/integrate.py …` and reads only Git refs and repository files; no agent runtime, prompt, or product name appears in it, and any runtime that can spawn a process gets identical output.
**Provider substitution:** pass — it never contacts a forge. It screens Git refs, which exist on GitHub, GitLab, Gerrit or a bare remote alike; the provider-specific half of landing a set was deliberately left as prose rather than code for exactly this reason.
**Repository substitution:** pass — any adopted repository with more than one branch in flight has the cross-leg problem, and the gates `build` runs are the adopter's own copies of the AgentFold gates, discovered by path inside the merged tree rather than configured per repository.
**User-global writes:** none
**Why AgentFold core:** the repository's own contract instructs every agent to screen a landing set before merging it, and until now nothing could. A rule that no mechanism enforces is the failure mode the harness exists to remove, so the mechanism belongs beside the reconciler and the test runner it invokes, not in one adopter's local configuration.
**Thin adapter:** none
