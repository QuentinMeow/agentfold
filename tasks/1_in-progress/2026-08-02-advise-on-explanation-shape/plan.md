# Plan — Report the structurally visible readability rules as advisory findings

- [ ] 1. Read `check_queue_schema` and `check_human_attention` in
      `automation/reconcile/reconcile.py`; list the helpers that already read a queue
      item (comment blanking, heading extraction, leaf/kind detection) so the new check
      reuses them instead of parsing a second time.
- [ ] 2. Decide and record in `design.md` where each rule family runs — reconciler for
      repository files, `automation/check_action_projection.py` for the pull-request body
      it alone ever sees — with the completed core-fit receipt.
- [ ] 3. Derive the required headings and their order from the files in `templates/queue/`
      rather than restating a schema in code; confirm the derivation on every existing
      item under `message-queue/`.
- [ ] 4. Add the advisory reconciler check: a `check_*` function returning `Finding`s,
      one new id in `CHECKS`, the same id in `ADVISORY_CHECKS`.
- [ ] 5. Add the pull-request body rules (section presence, section order, `## TL;DR`
      item count) to `check_action_projection.py` as advisory output that never changes
      its exit status.
- [ ] 6. Update `automation/AGENTS.md` so the advisory tier is no longer described as
      age-driven only, and register the new test file's inputs in `run_tests.py`.
- [ ] 7. Add tests in `automation/tests/`: one violation per rule family, a correct file
      emitting nothing, and the `--check` / `--fail-on-advisory` exit-code contract.
- [ ] 8. Record real command output in `verification.md`; run the reconciler against the
      tree as it stands and confirm `0 blocking finding(s)` with no new advisory noise.
- [ ] 9. Push the branch, open the pull request, append the worklog entry.
