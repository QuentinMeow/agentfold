# Plan — standardize pull request bodies

- [ ] 1. Establish exactly what `check_action_projection.py` accepts inside and around a
      `What to review` section, so the schema is compatible by construction.
- [ ] 2. Write templates/pull-request.md with the section order, the fold rules, and the
      file-change table grammar (one row per folder when the reason is shared).
- [ ] 3. Add the row to `templates/README.md`.
- [ ] 4. Write .github/pull_request_template.md as the GitHub projection of that schema.
- [ ] 5. Register the adapter path in `automation/core-scope-paths.txt`.
- [ ] 6. Add a test that runs the projection check over a filled example body.
- [ ] 7. Replace the body-shape prose in `handbook/git-workflow.md` with a pointer.
- [ ] 8. Run the reconciler and the suite; record real output in `verification.md`.
