# Worklog — stop link-check false positives

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — stop-link-check-false-positives (claude)

- Reproduced all five audited bugs against real repository content before changing
  anything: throwaway probe files under `handbook/` (deleted before the final commit,
  never made part of any commit) for bugs 1–4, and a real, temporarily-staged
  deletion/restore of
  `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`
  for bug 5 (the exact item `docs/designs/queue-resolution-order-independence.md`
  already cites). Restored the queue item byte-identical afterward (`git diff main --
  <path>` empty).
- Fixed `semantic_text` to call `strip_indented_code` (bug 2), anchored
  `LINK_SKIP_PREFIXES` and dropped the bare `.` entry (bug 3), added a known-extension-
  or-known-prefix gate before treating a candidate as a path claim (bug 1), stripped
  Markdown link syntax from headings in `anchor_slugs` before slugifying (bug 4), and
  exempted `message-queue/needs-human/**` / `message-queue/needs-agent/**` citations
  from existence-checking regardless of the citing file (bug 5).
- Deliberately kept `../` in `LINK_SKIP_PREFIXES` rather than anchoring it alongside
  `./`: a raw `../`-prefixed candidate passed to Git as a repo-root pathspec fails
  with "is outside repository" (verified directly with `git ls-files -- ../x`), which
  would abort the whole reconciler rather than report one broken link, and real
  repository content already relies on several live `../`-relative citations
  (`handbook/principles/folder-as-a-service.md`, `roadmap/current-state.md`, tasks'
  own worklogs) as well as at least one deliberately dead one (a claimed pickup
  request cited from a done task's worklog). Resolving those correctly needs the
  citing file's own directory, which no case here currently exercises; left as a
  known limitation rather than a new false positive.
- While proving bug 1's fix against every real Markdown file in the repository, found
  and fixed one second-order false positive: `.git/objects`, cited in
  `tasks/4_done/2026-07-30-stop-background-git-maintenance/verification.md`, was
  treated as a "known prefix" because that directory exists on disk. Scoped the known-
  prefix check to tracked content (matching `repo_artifact_bytes`'s own Git-index-vs-
  filesystem split) so VCS internals no longer count.
- Added regression tests for all five bugs plus `semantic_text`/`anchor_slugs` units in
  `automation/tests/test_reconcile_queue.py` (24 tests in the `link_check`/
  `anchor_slugs`/`semantic_text` subset, all passing). Ran the full automation suite
  (`python3 automation/run_tests.py`): 11/11 files passed. Ran
  `automation/reconcile/reconcile.py --check` on the real repository: 0 findings, no
  behavior change on real content beyond the five intended fixes.
- Stayed inside the assigned regions (`BACKTICK_RE`, `LINK_SKIP_PREFIXES`,
  `LINK_SKIP_DIRS`, `check_links`, `anchor_slugs` in `reconcile.py`; `semantic_text` /
  `strip_indented_code` in `markdown_semantics.py`) plus the shared test file; did not
  touch `main()`, `repo_text`, `claim_identity`, `retry_text`, or
  `resolution_evidence_problem`.
