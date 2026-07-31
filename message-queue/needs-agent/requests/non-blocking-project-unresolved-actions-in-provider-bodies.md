# Apply the unresolved-action rule to the provider projection surface too

**Status:** open
**Filed:** 2026-07-30, by claude, from task 2026-07-30-project-only-unresolved-human-actions
**Action:** Make the queue enumeration in `automation/check_action_projection.py` state-aware, so pull-request bodies and provider comments project the same unresolved set the handover and chat reply now project.
**Full context:** `history/AGENTS.md`
**Resolution evidence:** `automation/check_action_projection.py`
**If unanswered:** Handovers and chat replies stop repeating actions their owner already answered, while pull-request bodies keep repeating them — the noise is reduced but not removed, and the two surfaces disagree about what is pending.

## What you need to know

The reconciler's handover projection now selects only the `needs-human` items that still
await their owner: `folding`, `awaiting-artifact`, and a `waiting` item that already
carries a concrete committed response are an agent's turn, so they are no longer projected
(`history/AGENTS.md`, action-entry schema v3). `automation/check_action_projection.py`
validates the same kind of projection on a different surface — the body of a pull request
or a provider comment — and its own `live_human_queue_paths` still enumerates the queue by
path alone, exactly as the reconciler did before this change.

That surface is strictly easier to change than the handover was. Nothing about a pull-request
body is immutable, so there is no creation-commit snapshot to preserve and no schema version
to gate the rule behind; the predicate itself is one function. The reason it was not done in
the same task is scope: it is a second tool with its own contract and its own large test
suite, and the reported defect was about the handover and the chat reply.

Reuse the decided state split rather than re-deriving it. The rule itself is in the linked
contract; the reasoning behind it — which way it deliberately errs, and the one alternative
left open for the owner — is in the `design.md` of task
2026-07-30-project-only-unresolved-human-actions.

## Done when

`automation/check_action_projection.py` treats a resolved `needs-human` item as absent from
the projected set on the same three states, its tests cover each state plus the fail-open
cases (absent, empty, or unrecognised status), and `python3 automation/run_tests.py` passes
with real output recorded in the owning task's `verification.md`.
