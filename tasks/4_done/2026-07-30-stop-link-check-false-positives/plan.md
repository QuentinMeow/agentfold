# Plan — stop link-check false positives

- [x] 1. Reproduce all five bugs against real repository content with the real
      `reconcile.py --check` command, capturing the actual output before any code
      change (probe files under `handbook/`, plus a real, temporarily-simulated
      resolution of a live queue item for bug 5).
- [x] 2. Fix bug 2: `semantic_text` (`automation/markdown_semantics.py`) now calls
      `strip_indented_code`, so an indented-code example can no longer satisfy a
      structural check; confirm a fenced block nested in a list item still blanks
      correctly (no regression).
- [x] 3. Fix bug 3: anchor `LINK_SKIP_PREFIXES` (`http://`, `https://`, `tmp/`,
      `private/`) and drop the bare `.` entry; keep `../` skipped deliberately (Git
      itself refuses that pathspec from the repository root, and every real
      repository citation of it needs the citing file's own directory to resolve).
- [x] 4. Fix bug 1: a candidate only counts as a path claim when it has a known file
      extension or its top-level segment already exists as tracked repository
      content (`LINK_PATH_EXTENSIONS`, new prefix check in `check_links`); guard the
      VCS-internals edge case (`.git/objects`) found while proving this against real
      content.
- [x] 5. Fix bug 4: `anchor_slugs` strips Markdown link syntax from a heading before
      slugifying it, keeping only the visible label.
- [x] 6. Fix bug 5: `check_links` skips existence-checking for any candidate under
      `message-queue/needs-human/` or `message-queue/needs-agent/`, from any citing
      file, not only from the queue's own predeclared fields.
- [x] 7. Add regression tests for all five bugs plus the two supporting units
      (`semantic_text`, `anchor_slugs`) in `automation/tests/test_reconcile_queue.py`,
      including the positive set (real broken links still caught) and the negative
      set (ordinary prose never reported).
- [x] 8. Run the full automation test suite and `reconcile.py --check` against the
      real repository; confirm zero behavior change on real content beyond the five
      intended fixes.
- [x] 9. Record `verification.md` with only commands actually run and their real
      output, then move the task to `3_in-review`.
