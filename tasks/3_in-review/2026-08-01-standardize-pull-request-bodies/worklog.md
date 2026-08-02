# Worklog — standardize pull request bodies

## 2026-08-01 23:17 PDT — claude

Filed and claimed. Stacked on `task/2026-08-01-write-the-explanation-skill`, because the
PR scenario reference in that skill is what this schema is the machine-side half of.

## 2026-08-02 00:35 PDT — claude

Wrote the schema, its GitHub projection, and ten tests that run the real boundary check
over bodies in the schema's shape. The tests rejected the first draft three times, and each
rejection was a real defect rather than a test artifact: folded sections with no heading
above them are swallowed by the machine-read action section; a GitHub alert renders as
literal text inside a fold; and "can now merge" is classified as a directive outside the
action section while "is no longer blocked by" is not. All three are now schema rules, and
the third is a table in the skill's pull-request scenario.

`test_run_tests.py` then failed because the new test reads two tracked files the input
ownership table did not give it — the repository catching an unregistered input exactly as
`automation/AGENTS.md` says it should. Registered both.
