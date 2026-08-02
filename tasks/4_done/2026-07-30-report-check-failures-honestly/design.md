# Design notes — make the reconciler report its own failures honestly

**Status:** decided

## Problem

Four reproduced defects share one root: the reconciler does not distinguish between
"the repository is broken", "I could not look", and "time passed". All three come out
as exit 1, and exit 1 stops the pre-commit hook before the tests even run.

## Options considered

### Option A — Per-call severity argument on `Finding`

Add a fifth parameter and pass it at every emission site.
Consequence: several hundred call sites change, sibling branches editing any check
conflict on every line, and two emissions of the same check id can disagree about their
tier — which would make the `--check` exit code depend on which code path fired.

### Option B — Severity derived from the check id

One module-level `ADVISORY_CHECKS` set; `Finding.advisory` is a property over
`self.check`. Consequence: no call site changes, `aggregate_findings` keeps its
four-argument reconstruction, and a tier is a property of the invariant rather than of
one emission. The cost is that a check id cannot mix tiers, which is a feature: it is
the reason `stale-task` had to become its own registered check.

### Option C — Fail on advisory findings in CI, warn locally

Local commits stay unblocked; `main` stays clean.
Consequence: on 2027-01-23 every PR in the repository turns red with no change to any
branch — the same lockout, moved to the place where it blocks *everyone* rather than one
agent, and where the obvious repair (bump the `Filed:` date) is itself rejected by
`queue-resolution` identity rules.

## Chosen

**Option B, with advisory findings non-failing in CI as well as locally (rejecting
Option C).** The failure mode being fixed is "a green tree turns red because the clock
moved", and that is not less true on a runner than on a laptop — it is worse, because CI
gates merges for every agent at once. Advisory findings are therefore reported, never
fatal, on both paths:

- printed with an `(advisory)` marker so they cannot be mistaken for noise,
- counted separately in the summary line (`N blocking finding(s), M advisory`),
- still filed as durable repair items by `--file-retries`,
- and failable on demand through `--fail-on-advisory`, which is the lever a scheduled
  maintenance run or the memory-gardener uses. Nothing in the commit or merge path
  passes that flag.

`--fail-on-advisory` exists so the decision is reversible without another redesign: if
advisory drift is found to be ignored in practice, a periodic job can start failing on
it without putting the calendar back on the commit path.

### `stale-task`: registered, not renamed

`stale-task` was emitted from `check_task_structure` but was not a `CHECKS` key. That is
not cosmetic. `file_retries` garbage-collects a generated retry only when its `Check`
field is a `CHECKS` key, so every `stale-task` repair item ever filed was immortal —
it could never be cleared automatically even after the task moved. Renaming the finding
to `task-structure` would have destroyed that distinction and forced task staleness into
the blocking tier alongside genuine structural breakage. It is now its own check
function and its own registry entry, which also gives it exactly one severity tier.

### Existence gates read the index, not the worktree

`check_mode_valid`, `check_roadmap_fresh`, `check_stale_queue` and `check_memory_index`
all gated on `Path.is_file()`/`Path.is_dir()` in the worktree while reading their content
from the Git index. All four reproduced: deleting the worktree copy of a staged
violation made the reconciler report zero findings while the commit still carried it.
`candidate_has_file` answers "does the commit candidate — or untracked work — carry this
file", and it is a strict superset of the old worktree test, so no path that was checked
before stops being checked.

## Why the severity-tiers task could not be claimed

`tasks/AGENTS.md` requires a claim to delete the task's pickup request in the claim
commit. A live, immutable `needs-agent` request — the pre-commit mining advisory — names
that pickup request as a backticked path in its body. Deleting the pickup request
therefore breaks `link-check`, and repairing the reference breaks `queue-resolution`,
because a request's body outside the lifecycle fields is its action identity. Both
findings are reproduced with real output in `verification.md`. The severity work
therefore ships under this task, that task keeps its genuinely unfinished scope
(deterministic staleness from Git dates), and the conflict is filed as its own
non-blocking repair action rather than forced through.

## Deliberately not done here

- **Retry filing is not tiered.** `retry_text` and `retry_destination` still emit
  `blocking-reconcile-*` items with `Blocks now: transition:merge` for advisory findings.
  That code is owned by task 2026-07-22-retry-filing-automation-and-waivers; changing it
  here would collide. `message-queue/needs-agent/retries/README.md` now states the
  current truth rather than the old "every finding blocks merge".
- **`live_markdown_files` still yields untracked files**, so an untracked invalid-UTF-8
  scratch file still stops a commit — but now with one line naming it instead of a
  traceback, which is the actionable half of the defect.
- **Staleness is still measured from filesystem mtime**, so `stale-task` still answers
  differently on a fresh clone. Now that it is advisory, that non-determinism no longer
  blocks anything; it stays acceptance criterion 4 of the backlog task.

## Core fit

**Agent substitution:** pass — the change is entirely inside a stdlib Python checker and
its registry; no agent runtime, prompt, or product behaviour is involved, so any agent
that runs `reconcile.py` gets identical exit codes and identical output.
**Provider substitution:** pass — no provider is read or written. The CI decision is
expressed as a flag default in the checker itself, not in a GitHub workflow, so a
different forge inherits it unchanged.
**Repository substitution:** pass — every adopted repository ages: memory entries expire,
queue items sit, tasks go quiet. Without the tier split, adoption comes with a scheduled
outage on whatever date its first `Review-by:` lands, and with an exit-1 crash on the
first file that is not valid UTF-8. Both are properties of any repository, not of this
one.
**User-global writes:** none
**Why AgentFold core:** the reconciler is the referee named in the root `AGENTS.md`
guardrails; the meaning of its exit codes is part of the contract every adopter relies
on, not local configuration.
**Thin adapter:** none
