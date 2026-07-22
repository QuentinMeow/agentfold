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
  reports 36 changed files (+1,398/-15), both workflow runs pass, and the published
  summary puts boundary semantics, flexibility, evidence integrity, review policy, and
  absence of incident-specific artifacts at the top. Closed PR #5 now links to #6 as
  its clean replacement and remains intact as the rejected-design audit record.
