# Handover — PR summary standard

**Session:** 2026-07-23 00:26–00:34 PDT, codex
**Task:** 2026-07-22-protect-core-portability
**Mode:** async

## What happened

- Installed a generic personal `write-github-pr-summary` Codex skill outside AgentFold;
  no GitHub- or Codex-specific integration was added to framework core.
- Added the requested `Feature | File / folder changes | Description` table to draft
  PRs #4 and #6 as the final subsection inside each collapsed `Changes` block.
- Audited the remote diffs before publication: the table covers all 21 files in PR #4
  and the 44-file substantive diff in PR #6 exactly once, using folder rows only for
  coherent groups; this records-only handover is added to PR #6 afterward.
- Corrected two stale phrases in PR #4, validated and forward-tested the skill, and
  verified both published bodies and green check states from GitHub.

## How it works now

The personal skill gathers the real remote base, head, full diff, changed-path list, and
verification evidence before drafting a reviewer-focused description. It keeps the
summary and review questions visible, collapses detail, and ends `Changes` with the
three-column coverage table. AgentFold stores only this historical record; the
GitHub-specific skill itself remains user-global.

## Decisions made for you

- The standard stays outside core under the existing
  [core-portability decision](../../../memory/decisions/2026-07-22-core-portability-review-is-manually-selected.md);
  this session did not change framework policy.

## Needs your attention

None.

## Dead ends

- The official skill validator could not run under the default Python because PyYAML
  was absent. A temporary dependency environment ran the unchanged validator instead;
  skipping validation was unnecessary.

## Next steps

Use the updated review maps for draft PR #4, then its stacked draft PR #6. Future GitHub
PR-authoring tasks can invoke `$write-github-pr-summary` from the personal skill set.

## Deep links

- Task folder: [`tasks/3_in-review/2026-07-22-protect-core-portability/`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/) · Worklog: [`worklog.md`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/worklog.md) · Verification: [`verification.md`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/verification.md)
- Pull requests: https://github.com/QuentinMeow/agentfold/pull/4 and https://github.com/QuentinMeow/agentfold/pull/6
