# Plan — project only the human actions that still await the human

- [x] 1. Record the baseline: re-run the projection check at the creation commit of every
      handover in `history/` and store the finding set (`tmp/before.json`).
- [x] 2. Add the liveness predicate to `reconcile.py`: `human_action_unresolved()` plus a
      creation-snapshot reader, both failing open on anything unreadable.
- [x] 3. Version the rule under its own `**Queue liveness schema:**` marker, generalising
      the activation resolver and sticky downgrade guard over both markers. (First
      attempt reused `action-entry v3`; the sweep in step 7 caught that an unmerged
      branch already owns that number, so the rule moved to its own marker.)
- [x] 4. Filter the creation-snapshot human queue through the predicate, but only for
      handovers governed by the liveness schema.
- [x] 5. Move the definition of the projected set into `history/AGENTS.md` next to the
      schema markers; point `templates/handover.md` and the root `AGENTS.md` chat-reply
      sentence at it without restating the states.
- [x] 6. Tests: v3 rejects a projected resolved item, requires every unresolved one,
      accepts `None.` when all are resolved, fails open on a missing status, and leaves
      v1/v2 handovers unchanged.
- [x] 7. Re-run the same history sweep and diff the finding set against the baseline;
      run the full suite and `reconcile.py --check`; record real output in
      `verification.md`.
- [x] 8. File the follow-up for the second projection surface
      (`automation/check_action_projection.py`).
