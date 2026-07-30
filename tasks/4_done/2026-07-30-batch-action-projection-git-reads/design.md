# Design notes — read each repository view once per action-projection run

**Status:** decided

## Problem

`automation/check_action_projection.py` asked Git about one path at a time.
`candidate_record` ran one `ls-files --stage` per path, `candidate_paths` one `ls-files`
per prefix, `tracked_regular_file` one `cat-file -s` per object, and `candidate_text` one
`show` per read — and several checks read the same queue item for different fields, so the
same blob was fetched repeatedly inside a single run.

The measurement came first, and it moved the target. A prior handover named this module as
the next candidate for in-process fixture history, on a static count of 96 `add` and 23
`commit` call sites. Counting at runtime instead:

| Source | Spawns |
|---|---|
| `git_output` inside the gate under test | 1,288 |
| the test module's own fixture helper | 161 |
| the shared fixture skeleton | 6 |

The fixture work the handover proposed would have addressed 11% of the cost. The gate's own
per-path reads were 86%.

## Options considered

### Option A — a per-path cache keyed by path
Memoise each `ls-files -- <path>` answer. Removes only repeat questions about the same
path, and still pays one process for every distinct path a run inspects.

### Option B — one process-global snapshot
Read the index once per process. Cheapest, and wrong: a long-lived caller, and every test
that mutates a repository between two calls, would be answered from a view the repository
has moved past.

### Option C — one snapshot per run, discarded at the end
Read each view once inside an explicit scope that the entry points open and close. Within
one run the index and the candidate tree cannot change, so the snapshot is exact; across
runs nothing is retained, so nothing can go stale.

## Chosen

Option C. `RepositoryView` holds one read of one view; `repository_views()` is a reentrant
scope that the four entry points open through the `within_one_repository_view` decorator.
A nested scope joins the open one rather than creating a second view that could disagree
with it. Outside every scope each lookup reads Git again, which keeps the old behaviour for
any caller that has not opted in.

Equivalence rests on three cases where a whole-view read could have differed from a
pathspec read, all of them now tested against both implementations:

- a path that names a **directory** — the per-path read returned a single record whose path
  was not the requested one, or a tree entry rejected for not being a blob; the snapshot
  simply has no such key. Both answer "not a tracked file".
- a path recorded at **several merge stages** — the per-path read saw more than one record
  and refused; the snapshot holds more than one record for that key and refuses.
- an **empty prefix** — Git refuses it outright. The snapshot refuses it too, with a
  `ValueError`, rather than quietly starting to mean "the whole repository". This is the
  one deliberate behavioural difference, and it converts a case that used to raise into a
  case that still raises.

Blob sizes moved from one `cat-file -s` per object to one `cat-file --batch-check` per
view, filled on first use so a run that never asks for a size never pays for one.

## Core fit

**Agent substitution:** pass — the change is inside a stdlib Python gate with no agent
runtime, prompt, or model surface; any agent that could run the gate before runs the same
gate with the same verdicts.
**Provider substitution:** pass — no provider name, API, or payload shape is read; the
altered code only asks Git about the repository it was already asking about.
**Repository substitution:** pass — an adopted repository gets the same gate at O(1) reads
per run instead of O(paths), which matters more the more queue items it carries.
**User-global writes:** none
**Why AgentFold core:** the action-projection gate is the mechanism that binds provider
prose to live queue items; its cost is paid by every adopter on every pull request, and
this is a change to that mechanism, not to any local setup.
**Thin adapter:** none

## What this does not do

It does not speed up the complete test suite. Measured interleaved, the sharded suite is
unchanged, because this module is not the critical path — `test_reconcile_queue.py` is. The
gain is in the gate itself and in the module's own serial time, recorded in
`verification.md`.
