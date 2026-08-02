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

## 2026-08-02 03:20 PDT — claude

Opening the first pull requests against this schema found the rule the schema had stated
wrongly. A body's queue links must sit under the candidate's own
`blob/<full-sha>/` prefix, and the candidate is not the branch head: it is the commit GitHub
computes at `refs/pull/<number>/merge`, which does not exist until the pull request does.
The schema, its GitHub projection, and the skill's scenario now all say so, and the working
order is push, open, read the merge ref, then write the body.

Two further gate behaviours showed up while writing those bodies, both worth knowing before
the next one. A line that begins with the word "document," is classified as an imperative
and refused outside the action section — the repair is to reflow the line. And a queue-link
label must be the item's `Action` text verbatim or a leading prefix of it containing exactly
one action verb; a shortened label that drops the second clause is refused.
