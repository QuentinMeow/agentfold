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
