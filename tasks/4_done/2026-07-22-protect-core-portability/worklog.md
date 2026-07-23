# Worklog — protect AgentFold core portability

## 2026-07-22 — architecture correction (codex)

- Closed draft PR #5 without deleting or rewriting its branch after the owner identified
  that personal Codex setup and GitHub authentication policy do not belong in AgentFold.
- Started a clean branch at the exact remote tip of the guardrails-design branch; no
  incident-specific commit is an ancestor of this task.
- Added a substitution-based core receipt, an independent-review gate, repository-local
  executable checks, and a registry for thin adapter files. The mechanism deliberately
  avoids vendor-name bans and leaves product/service paths outside core.
- Three adversarial reviewers found and drove fixes for index-versus-working-tree
  evidence, deletion and rename coverage, claimant aliases, historical review verdicts,
  generated adapter paths, product `.gitignore` freedom, raw examples in skill prose,
  hidden Markdown evidence, and Python 3.9 compatibility.
- A final review round rejected a root-Markdown catch-all and raw HTML evidence. The
  gate now targets instruction-named root/hidden paths plus explicitly registered
  unusual adapters, leaves ordinary product docs alone, and strips fenced, commented,
  and raw-HTML evidence before parsing.
- The correctness reviewer continued probing Markdown rendering boundaries. Every
  reproduced bypass became a canary: CommonMark HTML types and partial tags, source
  ordering between HTML and fences, exact type-one terminators, blank-line whitespace,
  CommonMark-only line endings, and CRLF receipts. The final focused suite has 41 tests
  and all three independent lenses approve the resulting branch.
- Pushed the clean branch and opened draft PR #6 stacked directly on draft PR #4. GitHub
  verified the full file list, both workflow runs pass, and the published summary puts
  boundary semantics, flexibility, evidence integrity, review policy, and absence of
  incident-specific artifacts at the top. Closed PR #5 now links to #6 as its clean
  replacement and remains intact as the rejected-design audit record.

## 2026-07-22 — human guard-mode review (codex)

- Folded the owner's review that expensive agent review must not run automatically.
  Deterministic core admission remains active in hooks and CI; independent core-fit
  verdict validation now runs only when `--require-review` is explicitly selected,
  pending the universal hard/soft/off/manual guard-mode configuration.
- Superseded the earlier always-review consequence without weakening its portability
  boundary. The replacement ADR keeps substitution evidence automatic and makes the
  semantic panel an explicitly invoked, revision-bound check.
- A manually invoked three-lens panel found stale historical receipts, ambiguous
  reviewer identity handling, unbound task inputs, abbreviated SHA-256 object IDs, and
  status-move invalidation. Each reproduced failure became a canary; all three lenses
  approved exact commit `7247638` after the fixes.
- Bound the final receipt to the full reviewed commit, migrated historical verdicts to
  explicit legacy/unbound notes, and verified that later core or task-input edits stale
  the receipt while unchanged status moves and records-only follow-up remain possible.
- Merged the reviewed PR #4 response fold into the stacked branch, pushed all commits,
  updated PR #6's reviewer checklist and verification counts, and confirmed both GitHub
  Actions runs pass.

## 2026-07-23 — PR summary standard (codex)

- Kept the GitHub-specific authoring standard outside AgentFold core by installing the
  generic `write-github-pr-summary` skill in the user's personal Codex skills directory.
- Updated draft PRs #4 and #6 with a three-column file/folder change table as the final
  section inside `Changes`; independent coverage audits account for all 21 files in
  PR #4 and all 44 files in PR #6's substantive diff before this session record.
- Corrected two stale PR #4 phrases so its summary distinguishes active routing
  contracts from records and accurately names the service-test runner available on that
  branch.
- Forward-tested and validated the skill, read both published bodies back exactly, and
  confirmed their remote heads, bases, file totals, draft state, and green checks.

## 2026-07-23 — merge confirmation (codex)

- Confirmed the exact reviewed heads and GitHub merge commits for PRs #4 and #6 are
  ancestors of `main`, then moved this completed task from review to done.
