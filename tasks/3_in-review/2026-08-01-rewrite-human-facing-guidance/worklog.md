# Worklog — rewrite the human-facing guidance

## 2026-08-01 23:17 PDT — claude

Filed and claimed. Stacked on `task/2026-08-01-standardize-pull-request-bodies`, because
the rewrite applies the rules the skill and the PR schema define.

## 2026-08-02 01:45 PDT — claude

Inventoried every normative statement in both files first — 163 rows, committed as
`rule-inventory.md` — then rewrote against that inventory rather than by feel. An independent
agent audited the rewrite row by row: 151 kept, 9 moved to the file that owns them, 1 deleted,
2 corrected, and one constraint added that was in neither original.

The two corrections are the interesting part. The guide claimed it added no timing rule of
its own and then stated four; and a legacy review outcome was described as ending pursuit
when `automation/reconcile/reconcile.py` registers it as the legacy alias for
`changes-requested`, which carries the opposite obligation. Both are now stated correctly.

The audit also surfaced a duplication the rewrite did not resolve — the same timing rule in
two files — which belongs to the existing `2026-07-31-collapse-restated-contract-rules` task
rather than to a second live action.
