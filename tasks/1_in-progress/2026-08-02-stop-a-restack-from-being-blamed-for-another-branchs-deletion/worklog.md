# Worklog — Stop a restack from being blamed for another branch's deletion

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-31 — Strategy A claim (codex)

- Claimed the task through the repository's atomic direct-`main` coordination lane after the human explicitly selected Strategy A.
- Kept substantive proof-of-concept work, implementation, tests, design evidence, and verification assigned to the task pull request.
- Linked decision receipt: `message-queue/needs-human/decisions/future-blocking-choose-whether-task-claims-must-use-pull-requests.md`.

## 2026-09-01 — Proof-of-concept gate and production contract (codex)

- Ran four isolated POC branches before production work: replay diagnostics, exact edge
  witness, merge/incarnation analysis, and a final production-identity contract.
- Fresh verifiers repeatedly rejected unsafe or incomplete designs: synthetic-edge evidence
  laundering, delete/recreate claim borrowing, merge-parent claim borrowing, disconnected
  origins, parent-edge/event miscounting, incomplete supplier ancestry, wrapper false
  competition, unvalidated `M`, reintroduction evidence loss, and a sole-valid false green
  in the presence of an invalid final-absence root.
- Closed the POC gate only after the production contract passed 69/69 real-Git scenarios,
  4/4 S1/S2/S3/S12 aliases, 6/6 observed-red controls, an independent 8/8 review, and a
  49-DAG frontier matrix reconstructed twice with 98/98 oracle/exact comparisons.
- Selected a no-schema C-rooted design using production `queue_action_identity`, explicit
  direct/supplier modes, canonical causal roots, identity multiplicity, complete structured
  evidence, and one bounded graph enumeration. Production implementation remains pending.
