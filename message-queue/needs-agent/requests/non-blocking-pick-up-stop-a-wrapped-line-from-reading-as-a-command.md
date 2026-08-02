# Pick up stopping a wrapped sentence from reading as a command

**Status:** open
**Filed:** 2026-08-02, by claude, from a false positive hit while publishing task 2026-08-02-advise-on-explanation-shape
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-stop-a-wrapped-line-from-reading-as-a-command/task.md`
**Request kind:** task-pickup
**If unanswered:** Agents keep hitting an unexplainable boundary-check failure and keep repairing it by rewording correct prose, so the gate silently teaches everyone to write around a bug rather than to stop instructing the reader.

## What you need to know

The pull-request boundary gate refuses a body that instructs the reader outside its
`## What to review` section. It scans line-first rather than sentence-first, so an ordinary
sentence that wraps onto a line beginning with a word that is also a verb reads as a bare
imperative.

The reported instance: a line beginning `repair for such a finding …` was scanned as the
command "repair" and failed a body that instructed nobody. The agent reworded its sentences
to get published, which means the effective rule is now "do not instruct the reader, and
also do not let a wrap land on certain words" — a rule nobody states and nobody can follow,
because wrapping is invisible to intent.

The strictness is not in question. A body that genuinely commands the reader must still
fail; the unit of analysis is the defect.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
