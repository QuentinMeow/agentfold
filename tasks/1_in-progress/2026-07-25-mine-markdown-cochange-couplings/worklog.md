# Worklog — mine markdown co-change couplings and validate heading anchors

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-25 — file-stage-0-and-1 (claude)

- Filed the task record for Stage 0 and Stage 1 of the approved markdown edge graph, with
  the canonical pickup request in the same coordination commit. No feature code written.
- Confirmed the anchor hole is live before planning around it: `check_links` in
  `automation/reconcile/reconcile.py` guards candidates with
  `re.fullmatch(r"[\w./-]+", cand)`, which rejects every candidate containing `#`, so a
  link with a bad path *and* a bad anchor produces no finding at all today.
- Confirmed the repository has no heading-extraction or slugification helper, so both are
  new code in step 3 rather than a reuse.
- Recorded three narrow choices in `design.md`: mining as a standalone advisory CLI rather
  than a `CHECKS` entry (findings have no severity, so every finding blocks), the ledger as
  a tracked text file beside the tool rather than a `memory/` entry (verdicts are permanent,
  memory entries expire), and anchor validation inside the existing `check_links` rather
  than a new check id (retry filenames embed check ids).
- Left the four obstacles the next session would otherwise rediscover in `plan.md`: the
  zero-line `automation/AGENTS.md` budget, the core-scope receipt and branch requirement,
  the quadratic cost of a history walk inside a reconciler check, and the ~205-second test
  suite that runs on every commit.
- Decision this task implements: `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`.
