# Worklog — in-process fixture Git objects

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — fast-local-test-feedback continuation (claude)

- Filed and claimed from external research that measured the two approaches on this
  machine: 36.09ms for a skeleton copy plus spawned add and commit, against 6.60ms for
  the same copy plus a pure-Python commit, so the commit itself falls from about 31.8ms
  to about 2.35ms.
- The research also verified that real Git resolves hand-written objects: `rev-parse HEAD`
  returned the same identifier the writer computed.
- The neighbouring optimization is already banked and is the precedent to follow: the
  `.git` skeleton is built once with an empty template and copied per test, guarded by a
  byte-comparison against a real `git init`.

## 2026-07-30 — implementation (claude, branch task/2026-07-30-write-fixture-git-objects-in-process)

- Added `automation/tests/fixture_git.py`: loose blob, tree and commit writing, plus
  reading and rewriting a version 2 index with the same truncated stat data Git records.
  The index turned out not to be optional — the reconciler under test queries it through
  `git ls-files --stage`, `git diff-index` and `git diff-files`, and the fixtures run
  real `git checkout`, `git merge` and `git rm` between commits.
- The helper serves `add` and `commit` only, and declines anything it does not speak for
  exactly, so the invocation falls through to real Git unchanged. Declines observed in a
  full run: one intent-to-add, and the two adds of the one fixture that writes ignore
  rules. Everything else in that file is untouched.
- Objects match real Git byte for byte, compressed as well as decompressed, once the
  writer compresses at Git's own default loose-object level rather than zlib's. The
  conformance test asserts the durable half of that — identifiers and decompressed bytes
  — and deliberately does not assert zlib framing, which belongs to the compressor.
- Commit timestamps are derived rather than stored: a root commit sits on a pinned epoch
  and every later commit sits a minute past its newest parent, which is deterministic
  without keeping per-repository state anywhere.
- `automation/tests/test_check_action_projection.py` is the next candidate, at roughly
  96 adds and 23 commits against this file's 541 and 452. It was left alone to keep this
  change to one file while other branches are in flight.
