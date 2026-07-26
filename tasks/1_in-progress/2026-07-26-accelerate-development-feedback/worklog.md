# Worklog — accelerate the local development feedback loop

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-26 — development-feedback-investigation-and-claim (codex)

- Measured the clean-tree reconciler at a 5.28-second median and the isolated repository
  suite at 219.97 seconds; two Git-heavy automation test files accounted for about 89%
  of suite time.
- Filed and claimed this umbrella task for one bounded pull request. A read-only scope
  review recommended a service-only staged-path selector with fail-closed full-suite
  fallback and warned that the current isolated view contains working-tree bytes, so the
  fast lane must not be described as staged-snapshot verification.

## 2026-07-26 — conservative-staged-test-lane (codex)

- Kept the no-argument test runner as the complete isolated suite and added a
  `--staged` selector for regular quote-service additions and modifications. Quote API
  changes select API and CLI coverage; quote CLI changes select CLI coverage.
- Made empty, malformed, unavailable, cross-cutting, unknown-service, non-add/modify,
  non-regular-index, symlinked, and missing-test cases fall back to the full suite.
- Updated pre-commit to request the staged lane, documented that selection reads the
  index while execution uses working-tree bytes, and added deterministic lane, reason,
  file-list, and elapsed-time reporting.
- Added focused selector and isolation regression coverage. A temporary-index command
  exercised the real narrow path in 1.15 seconds and the reconciler reported zero
  findings before the implementation commit.
