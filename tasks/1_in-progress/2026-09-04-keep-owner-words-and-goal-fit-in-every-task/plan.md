# Plan — Keep the owner's words and a goal fit in every task

- [ ] 1. Templates: a task-requirements template and a roadmap-goal template exist under `templates/`; `templates/task/task.md` carries labelled criteria and a `## Fit` section; `templates/README.md` names both new templates.
- [ ] 2. Roadmap: rewrite `roadmap/desired-state.md` as `G1`–`G10` goal entries with provenance and owner quotes (G9 multi-agent workflow, G10 this feature); state the transcription-versus-proposal rule in `roadmap/README.md`; record the rule as an ADR.
- [ ] 3. Contracts: one guardrail line in the root `AGENTS.md`; the file row and claim rule in `tasks/AGENTS.md` within its line budget; the fit re-check in `skills/session-handover/SKILL.md`.
- [ ] 4. Reconciler: `task-provenance` and `roadmap-goals` (blocking), `task-provenance-advice` and `roadmap-goals-advice` (advisory), activated by task-id date; tests observed green then red; test inputs registered in `run_tests.py`.
- [ ] 5. Records: this task and the two other in-progress tasks carry honest `requirements.md`/`## Fit` where their sources allow; `roadmap/current-state.md` updated.
- [ ] 6. Verify: focused tests, serial full suite, reconciler, cold clone, fresh three-lens panel; real output in `verification.md`.
- [ ] 7. Publish: push the task branch, open the pull request, write the handover.
