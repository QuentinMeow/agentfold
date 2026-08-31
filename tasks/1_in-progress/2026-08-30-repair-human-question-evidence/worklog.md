# Worklog — preserve evidence and unanswered obligations

## 2026-08-30 — open-PR stack recovery (codex)

- The owner authorized replacement PRs and all useful final changes. This bounded child task owns the upper source-evidence repairs; the parent owns the overall stack and preserved local data.
- Filed and claimed from the recovered lower branch, which already contains current main. Direct-main coordination publication was rejected by auto-review earlier in this run, so coordination is published on the task branch before implementation.
- Importing current main into the old upper head replays two already-main historical transcripts under a withdrawn grammar. Independent scratch verification shows a lower-first merge retains identical bytes and all original PR89 commits while its trusted-base range passes. An ordinary push of that merge to the old upper branch still replays those records; a new claimed upper task starts from the valid current-main baseline without changing a gate.
