# Worklog — machine-specific paths in the link check

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — fast-local-test-feedback continuation (claude)

- Claimed after the same failure shape broke CI twice in two days, on two different
  records, both times with a green local gate.
- The mechanism is one line: when a candidate resolves outside the repository,
  `relative_to` raises and existence falls back to a live probe of the host filesystem.
  That probe is the only part of the check whose answer depends on the machine.
