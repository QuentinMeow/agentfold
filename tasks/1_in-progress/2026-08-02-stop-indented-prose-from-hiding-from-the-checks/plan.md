# Plan — Stop indented prose from hiding from every repository check

- [x] 1. Build failing fixtures for the three reproductions (queue mutation, task action
      origin, link check) plus the `semantic_text("- a\n    b\n")` regression, and record
      their pre-change output
- [x] 2. Write `design.md` with the two routes, the chosen one, and a complete
      `## Core fit` receipt
- [x] 3. Move `indentation_width` into `automation/markdown_semantics.py` so one
      implementation of CommonMark column arithmetic serves both gates
- [x] 4. Rewrite `strip_indented_code` as a paragraph-aware, container-aware walk, and
      correct the `semantic_text` docstring
- [x] 5. Add a new markdown-semantics test file under `automation/tests/` covering every
      reproduction, every named consumer, and the legitimate indented-code case
- [x] 6. Register the new test file's owning inputs in the input-ownership table in
      `automation/run_tests.py`
- [x] 7. Run `automation/reconcile/reconcile.py --check` on the whole tree before and
      after, and diff the finding sets so the narrower rule adds no false positive
- [x] 8. Run the full `automation/run_tests.py` suite, record real output in
      `verification.md`, append the worklog entry, and open the pull request
