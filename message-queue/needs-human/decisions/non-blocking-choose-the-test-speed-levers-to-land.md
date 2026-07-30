# Which measured test-speed levers should land, and in what shape?

**Status:** folding
**Filed:** 2026-07-29, by claude, from conversation `2026-07-29-1833PDT-fast-local-test-feedback`
**Action:** Choose Option A, B, or C for what lands from the five measured experiments.
**Full context:** `docs/designs/fast-local-test-feedback.md`
**Why-you-might-care:** Measurement removed the premise the in-progress design rests on, so building it unchanged would add policy machinery the repository no longer needs.
**If-you-do-nothing:** Nothing lands; every commit keeps paying the measured 219-225s gate and the five experiment branches stay unmerged.
**Resolution evidence:** `docs/designs/fast-local-test-feedback.md`

**If unanswered:** The status quo continues safely — the slow gate still proves the whole repository green, and no coverage changes.

## What you need to know

The pre-commit hook runs the whole test suite: measured at 219.16s, and 231.54s for a real
two-line commit. Task `2026-07-27-configure-test-gates-and-time-budgets` answered that with
a configuration file, budget deadlines, receipts, and auto-filed regression tasks.

Measurement found a simpler cause. The test runner wraps every Git call in a `/bin/sh`
shim, and the suite makes 13,261 Git calls; 92-93% of its wall time is inside those
subprocesses. Removing the shim and sharding the suite across cores runs **all 625 tests
in 26-30s**, verified twice. Nothing needs to be skipped to beat the 60-second goal, so the
selection-and-lanes half of the accepted design is now optional rather than required.

## Differences

The options differ in how much permanent machinery is kept once speed alone solves the
problem. More machinery makes record-only commits faster still, but every selection rule
is a correctness liability that must stay accurate forever. One experiment demonstrated the
hazard concretely: with the current selector an `automation/` change selects zero test
files, so the file every agent depends on would stop being tested locally.

## Options

### Option A — Speed only
Land the Git-isolation fix, add a parallel mode to the runner, and land the reconciler
spawn reduction on its own track. One lane; the full suite runs at every commit in ~26-30s
(~32-37s including core scope and the reconciler). No config file, no selection table.
*Example consequence:* every commit still proves the entire repository green, locally, in
about half a minute.

### Option B — Speed plus selection
Option A, plus the staged-path ownership map, so record-only commits run zero tests and
finish in ~13s. Adds a table that must stay correct as code moves, guarded by a test.
*Example consequence:* record commits get faster still, and a future ownership mistake
becomes a possible source of untested changes.

### Option C — Build the in-progress design as written
Configuration file, budgets, receipts, and auto-filed regression tasks.
*Example consequence:* the repository gains a policy language; note `tomllib` is absent on
both interpreters here, and the previous attempt produced no measured speedup.

## Recommendation

Option A, because it meets the goal with the smallest permanent surface and removes the
need to decide what not to test.

**Your answer:** Option B, extended — transcribed by claude from chat on 2026-07-30, not typed by the owner. The owner merged pull requests 20, 21 and 22, which is Option B exactly, then rejected 26-30s as a stopping point and asked for the parts of experiment C worth keeping to be rebuilt correctly. Verbatim wording and the consequences are recorded in the resolving decision record.
