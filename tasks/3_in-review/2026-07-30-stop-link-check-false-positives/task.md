# Stop link-check false positives without weakening real checking

**Claimed-by:** claude
**Mode:** async
**Filed:** 2026-07-30, by claude, from a link-check false-positive audit
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`check_links` in `automation/reconcile/reconcile.py` reports ordinary English prose
containing a slash (`24/7`, `and/or`, `s/foo/bar/`) as a broken repository path, and
because one finding blocks every commit repo-wide, writing such a sentence in any
document bricks the checkout. An audit reproduced five confirmed defects in the same
mechanism:

1. Prose false positives (above).
2. A path inside a 4-space indented code block is treated as a live link:
   `strip_indented_code` (`automation/markdown_semantics.py`) exists but `semantic_text`
   never calls it.
3. `LINK_SKIP_PREFIXES` uses unanchored `str.startswith` on `"http"` and `"."`, so two
   genuinely broken example paths (one prefixed `httpd`, one prefixed `./`) are skipped
   as if they were a URL or a dot-relative reference, and fail open.
4. `anchor_slugs` does not strip Markdown link syntax from headings, so
   `## See [the design](docs/AGENTS.md)` slugifies to `see-the-designdocsagentsmd`,
   reporting a correct anchor link as broken.
5. Resolving (deleting) a queue item under `message-queue/needs-human/` or
   `message-queue/needs-agent/` breaks link-check in every document that cites it as
   evidence, even though queue items are deleted by design on resolution
   (`message-queue/AGENTS.md`).

## Acceptance criteria

- [ ] WHEN a backticked or linked candidate has no recognized file extension and its
      top-level segment names no known repository entry, THE SYSTEM SHALL treat it as
      prose, not a path (fixes 1).
- [ ] WHEN a candidate lives inside a 4-space/tab indented code block, THE SYSTEM SHALL
      NOT treat it as a live link, while a fenced block nested in a list item SHALL
      remain correctly blanked (fixes 2, no regression).
- [ ] WHEN a candidate begins `httpd` or `./`, THE SYSTEM SHALL still check it normally
      rather than skipping it as `http://`/dot-relative (fixes 3).
- [ ] WHEN a heading contains Markdown link syntax, THE SYSTEM SHALL slugify only its
      visible label (fixes 4).
- [ ] WHEN a document cites a `message-queue/needs-human/**` or
      `message-queue/needs-agent/**` path that no longer exists, THE SYSTEM SHALL NOT
      report it as broken, from any citing file (fixes 5).
- [ ] A genuinely broken repository-relative path in normal prose SHALL still be
      reported after every change above (no weakened real checking).
- [ ] Every fix is proven with a reproduction (before) and a passing regression test
      (after); the full automation test suite and `reconcile.py --check` are green on
      the real repository with no unexplained behavior change.

## Links

- None (audit findings transcribed directly into this task; no separate audit artifact
  is tracked in the repository).
