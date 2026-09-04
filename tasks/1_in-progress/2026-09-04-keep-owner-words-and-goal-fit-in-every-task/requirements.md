# Requirements — Keep the owner's words and a goal fit in every task

Owner words only, verbatim and dated. Agents append new dated entries; they never edit,
reorder, or delete an existing one. Interpretation lives in `task.md` as labelled criteria.

## 2026-09-04 — chat, the owner to the main agent (Claude Code session)

```text
Another thing I want to highlight is, we also need to persist the user's idea for ALL TASKS. We MUST DIFFERENTIATE USER'S REQUIREMENT and agent's self-added requirements, and we need a place to document the desired features /end goals for each repo, the full picture, so that we don't miss the goal half way due to AI generated fake goals. At the start of every non-trivial task, agent must compare the end goal, current state and how does the new requirement fits (and let human decide if there's any conflicts, anything doesn't seem intuitive, instead of hacking around and make compromise). Implement this human requirements / agent supplied requirements documentation efficiently (search online for any solid open source light weight implementation and learn from them), then continue working on the task showed below (make sure you find the work correctly from the worktree / branches):
```

## 2026-08-28 — standing preference, stated when commissioning the agent-orchestration skill (recorded in the main agent's memory; paraphrase of the owner's rule, not a quotation)

```text
Store the user's original requirements VERBATIM in a separate file agents never edit (except appending new user words from direct conversation) — they must always be able to tell their idea from the agent's. Label derived items [derived].
```
