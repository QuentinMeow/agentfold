# Design notes — project only the human actions that still await the human

**Status:** decided

## Problem

`live_human_queue_paths()` in `automation/reconcile/reconcile.py` defined the set a
projection must contain as every readable regular file under `message-queue/needs-human/`.
Nothing in that definition looks at the item's state. The handover template and the root
`AGENTS.md` chat-reply rule both consume that set, so the owner's inbox repeated items
they had already answered — 19+ repetitions of one approved review — while the checker
reported the projection as exact.

Three things had to be settled: exactly which queue states still owe the human an action;
how to change the rule without retroactively reddening immutable handover records; and
where the rule lives so that contract and checker cannot drift apart.

## Options considered

### Option A — filter on status alone (`waiting` is pending, everything else is not)

Simple, but wrong in both directions. It keeps projecting a `waiting` item the human has
already answered — the exact case the ritual in the root `AGENTS.md` tells the next agent
to claim — and it silently drops any item whose `**Status:**` is missing or misspelled,
which is precisely when a real ask is most likely to be lost.

### Option B — state machine walk, fail-open on anything unrecognised (chosen)

Drop an item only when the repository's own lifecycle says the ball is in the agent's
court, and project everything else, including malformed items.

### Option C — change the rule for every handover, past and present

Rejected. `history/AGENTS.md` makes committed v1 handovers immutable and the reconciler
re-evaluates each one against the queue snapshot of its creation commit. Tightening the
rule unconditionally would turn correct historical records into findings, which the same
contract forbids: "A rejecting grammar expansion requires a new schema version instead of
retroactively changing immutable records."

### Option D — version the rule inside the existing action-entry schema (rejected on evidence)

Tried first, then withdrawn: the version number it needed is already claimed on an
unmerged branch. See "The immutability mechanism" below.

## Chosen

**The state split.** A `needs-human` item is *unresolved* — and therefore projected —
unless one of these is true, each of which the repository's own contract already names as
the agent's turn:

| State | Why it is not the human's turn |
|-------|-------------------------------|
| `Status: waiting` **with** a concrete `**Your answer:**`/`**Your review:**` | `message-queue/AGENTS.md`: "Commit the first human response while `waiting`; it is immutable" and "a concrete human response freezes timing". The root `AGENTS.md` ritual step 2 tells the *agent* to scan for exactly these filled lines and claim them. The human has acted; repeating it back is the noise this task removes. A counter-question is not lost — the contract requires a same-timing successor item, which is itself live and projected. |
| `Status: folding` **with** that same concrete response | The claim edge cannot add a response: `queue-resolution` rejects a `waiting` → `folding` transition that "changed more than status", and `active_blocking_repair_problem()` refuses a `folding` item with no "concrete committed human response". So a well-formed `folding` item is an already-answered one whose next move (fold, then delete) belongs to an agent. |
| `Status: awaiting-artifact` | Reviews only, and `check_queue_schema` already enforces that such an item carries `Review target: pending`, `Review revision: pending`, and `Review outcome: pending`. There is literally nothing bound for the human to judge; publishing the target is agent work. |

The predicate collapses to one sentence: an item awaits its owner until a concrete
response is committed, except that `awaiting-artifact` is an agent's turn from the start.
Everything else stays projected — the rule **fails open**:

- `waiting` or `folding` with `______`, an empty value, or no response field → projected.
- `**Status:**` absent, empty, or an unrecognised value → projected.
- The item cannot be read or decoded at the creation snapshot → projected.

The first bullet is why `folding` alone does not resolve an item: a `folding` claim with
no committed response contradicts its own meaning, and the safe reading of a
self-contradictory item is that its owner should still see it.

**Which way this errs: permissive.** Only the three states above drop out, and each is
one the reconciler independently validates elsewhere (`check_queue_schema` restricts the
allowed status values per actor and leaf, and rejects `awaiting-artifact` outside
the reviews leaf). A malformed item is *more* likely to be projected under the new
rule than a well-formed one, because an unparseable state is treated as pending. This was
deliberate: a redundant line in the owner's inbox costs one line, and a withheld ask can
cost the decision itself.

The one case worth naming is a genuinely stuck `folding` item — an agent claims a
response and never folds it. Under the old rule the owner saw it forever (as noise
indistinguishable from a real ask); under the new rule they do not see it at all. That is
a *stalled agent action*, not a pending human one, and the honest fix is a staleness
finding against the queue item rather than permanent noise in a human inbox. It is not in
this task's scope — see "Deliberately not done".

**The immutability mechanism.** `history/AGENTS.md` already carried a
`**Queue action-entry schema:**` marker, and `handover_action_entry_version_for()` already
resolved the highest version whose activation commit is an ancestor of a given handover's
*creation* commit. That machinery is exactly right; the version *namespace* was not.

The rule ships under a **new, separate marker**, `**Queue liveness schema:** v1`:

- Handovers created before its activation carry no liveness marker and keep the old
  path-only liveness, byte for byte.
- Handovers created at or after it must project only unresolved items.
- If the version cannot be resolved (an error path), the code falls back to the old
  behavior, so a failure can never invent retroactive redness.

The first attempt reused the action-entry namespace and called the rule `v3`. Measurement
caught that as a real defect before it shipped: the unmerged branch
task/2026-07-23-first-class-message-queue **already declares
`Queue action-entry schema: v3`** for its own in-flight meaning. Because `main`'s
reconciler did not recognise `v3`, that branch's handovers had been resolving to the
highest *recognised* version (v2); teaching `main` that `v3` means "unresolved only"
silently changed one of those records' verdicts. It happened to go greener, which is luck,
not safety — a record that projected a resolved action would have gone red instead.

Two lessons are baked into the shipped shape. Syntax and membership are genuinely
different dimensions and now version independently, so neither can move the other. And a
schema version number is a shared namespace across every in-flight branch, not just the
one in front of you: claiming the next integer is a merge conflict waiting to happen.

The "sticky schema" guard was generalised over both markers, so removing or downgrading
either after activation is a finding and adding a future version needs no edit there.

**Where the rule lives.** In `history/AGENTS.md`, immediately beside the schema marker
that versions it. That file already owned the sentence the change replaces ("exactly
project all live `message-queue/needs-human/` actions"), and a versioned rule has to sit
with its version marker or the two can be changed independently.
`templates/handover.md` (schema for the `Needs your attention` section) and the root
`AGENTS.md` chat-reply sentence both name the same set and link there; neither restates
the states.

## Deliberately not done (for the owner to decide)

- **`automation/check_action_projection.py` has the same defect.** Its own
  `live_human_queue_paths()` (line 1962) is also path-only, and it validates the queue
  projection in pull-request bodies and GitHub comments. Fixing it means the same rule
  applied to a mutable external surface with no immutability constraint, so it is
  strictly easier — but it is a second surface with its own contract and 4k lines of
  tests, and it is not what the owner reported. Filed as a follow-up rather than folded
  in here.
- **A staleness finding for a queue item left in `folding`.** The aggressive version
  would be a reconciler check ("item has been `folding` for more than N days") so a
  stalled fold surfaces as a *finding* instead of as inbox noise. `STALE_QUEUE_DAYS` (30)
  is the precedent, but not the coverage: `check_stale_queue` today reaches `blocking-*`
  items by age and `future-blocking-*` items with a clock-checkable date, and nothing
  else — so a `future-blocking` item parked in `folding` on an `event:`/`transition:`
  boundary, which is exactly the item that prompted this task, is reached by neither that
  check nor (now) the human projection. Not implemented here: it changes what the
  reconciler blocks on, which is the owner's call rather than a velocity fix's.
- **Dropping `awaiting-artifact` was the closest call.** The conservative reading is that
  an item parked in `needs-human/` should stay visible so the owner knows something is
  coming. It is excluded because the contract makes the state mean "no artifact is bound
  yet" and the reconciler enforces `pending` target, revision, and outcome — the owner
  cannot act on it even if they read it. If the owner disagrees, the aggressive/permissive
  alternative is a one-line change: remove `awaiting-artifact` from
  `QUEUE_AGENT_TURN_STATUSES`.

## Core fit

**Agent substitution:** pass — the rule is a property of the repository's queue files and
is enforced by `reconcile.py`; any agent runtime that writes a handover from
`templates/handover.md` is bound by the same check, and none of it reads agent-specific
state.
**Provider substitution:** not-applicable — no provider, API, or external service is
involved; the inputs are tracked Markdown files and Git objects.
**Repository substitution:** pass — an adopted repository gets the same benefit the moment
it declares `**Queue action-entry schema:** v3`, and gets the old behavior until it does;
nothing here names AgentFold's own tasks, dates, or items.
**User-global writes:** none
**Why AgentFold core:** the queue-to-projection contract is the mechanism that makes
"nothing blocks or waits silently" survivable; without a state-aware definition of which
actions are live, every adopter's human inbox degrades into a list its owner learns to
ignore, which defeats the guardrail rather than enforcing it.
**Thin adapter:** none
