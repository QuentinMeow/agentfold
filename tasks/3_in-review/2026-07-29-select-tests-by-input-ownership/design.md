# Design notes — select repository tests from the staged paths that can affect them

**Status:** decided

## Problem

The commit gate runs every test for every change. The existing `--staged` lane narrows only
changes confined to the two example services, and replaying it over the repository's history
shows it never once selected a narrow lane.

## Options considered

### Option A — Keep escalating to the full suite

No new risk and no benefit; this is the current behaviour and the reason a records-only
commit costs 219s.

### Option B — Coverage-based selection

Rejected on evidence: `coverage.py` cannot observe subprocesses, and this suite's behaviour
lives almost entirely inside Git subprocesses.

### Option C — Gate on change size

Rejected. No credible engineering source gates test depth on lines changed, and published
risk signals are path- and domain-based. Size may add tests, never subtract them.

### Option D — An explicit, fail-closed ownership table

Chosen. Record paths own nothing, code paths own the tests that read them, and anything
unrecognised selects everything.

## Chosen

Option D. The justification for excluding record paths is input independence demonstrated by
perturbation, not a judgement about risk appetite — which is what makes it safe to skip
tests rather than merely fast.

Two deliberate calls: removals and renames of non-record paths fall back to the full suite,
because tests assert that specific files exist; and Markdown outside a test's own directory
only owns nothing when it sits under an already registered top-level entry, so a brand new
top-level directory still selects everything.

## Core fit

**Agent substitution:** pass — path ownership and staged-path parsing are repository mechanisms independent of the agent runtime
**Provider substitution:** pass — selection is local and needs no provider; CI continues to run the complete suite
**Repository substitution:** pass — adopted repositories carry records that cannot affect their code tests, and need the same fail-closed default
**User-global writes:** none
**Why AgentFold core:** which tests a commit must run is part of the harness contract every adopter inherits, and a fail-closed default is what keeps that contract safe
**Thin adapter:** none
