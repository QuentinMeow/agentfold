# Design notes — give the commit gate a routine lane and let the push boundary own completeness

**Status:** decided

## Problem

The commit gate runs the complete suite, measured at 219-231s even for a two-line change.

## Options considered

### Option A — Keep the complete suite at every commit

Correct but slow, and duplicated: the push boundary already runs the same suite.

### Option B — A configuration file with budgets, receipts and generated regression tasks

Rejected on evidence. A prior attempt built this and merged no speedup; `tomllib` exists on
neither interpreter available here; and a budget that stops tests at a deadline leaks the
repositories each run creates, which then slows every later run.

### Option C — A routine lane, with the push boundary owning completeness

Chosen. The complete suite already runs on every push with no filter, so removing the local
copy removes a duplicate rather than coverage.

## Chosen

Option C, kept deliberately small: three lanes chosen by a flag, an environment variable as
the only knob, an honest deferred-coverage report instead of a manifest and receipts, and an
optional pre-push hook that is inert until enabled.

### Dependency, and the reason for it

Landing this before input-ownership selection would be unsafe. With the current selector an
`automation/` change selects no test files, so the reconciler — the one component every agent
depends on — would stop being tested locally. A printed deferral is loud, but it is not a
tracked obligation. The task ordering therefore places selection first.

## What the experiment held, and where each part went

Recorded here because the branch that carried it is deleted, so this is the only place the
inventory survives.

| Part of the experiment | Where it is now |
|---|---|
| The routine lane's skip rule | Rejected. `memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md` |
| Naming every unrun file before any test starts | On main, from task `2026-07-30-report-unrun-coverage-honestly` |
| An `AGENTFOLD_TEST_LANE` knob and a `--lane` flag | Unneeded. The bare runner invocation is already the complete suite and `--staged` is already the narrow lane |
| Its measurements | Superseded. Taken on a contended host beside other benchmarks; `docs/designs/fast-local-test-feedback.md` carries later same-session pairs |
| Its own strongest objection, that the lane deletes signal for the changes most likely to break | Folded into the decision above, which is the durable form |
| An optional pre-push hook running the complete suite, inert until a repository-local Git setting enables it | Not taken — see below |

The pre-push hook was 23 lines: read a repository-local boolean setting, exit 0 with a
one-line notice when unset, otherwise run the complete suite. It existed to cover the gap
the routine lane deliberately opened. On main the commit gate skips only what it can prove
is unreachable, so there is no deferred coverage for a local pre-push run to catch, and the
pushed workflow already runs the complete suite on every branch. Rebuilding it later is a
short exercise if earlier local feedback is ever wanted; it is not a loss carried by
deleting the branch.

## Core fit

**Agent substitution:** pass — lanes and their reporting are repository mechanisms with no agent-runtime dependency
**Provider substitution:** pass — the routine lane works offline; a provider only needs to keep running the complete suite it already runs
**Repository substitution:** pass — adopted repositories need a fast commit gate and a named boundary that owns completeness
**User-global writes:** none
**Why AgentFold core:** where completeness is proved, and how honestly a fast lane reports what it skipped, is part of the harness contract every adopter inherits
**Thin adapter:** none
