# Worklog — write the explanation skill

## 2026-08-01 23:17 PDT — claude

Filed and claimed. The owner asked for message and PR-description readability: layered
explanation, self-contained files, glossed jargon, and a default of reporting finished
work back in chat with the decisions it needs. Four research subagents were dispatched to
gather external prior art before any prose is written.

## 2026-08-01 23:50 PDT — claude

Four research subagents returned: layered-explanation structures and plain-language
thresholds; GitHub-flavoured Markdown behaviour verified against GitHub's own rendering
API; decision-brief and clinical-handover formats; and Agent Skill authoring practice.
Two findings changed the design rather than merely supporting it, and both are recorded in
`docs/designs/explaining-work-to-the-owner.md`: written handovers survive where verbal ones
do not, and a decision request that omits any one of seven properties comes back as a
question instead of an answer.

Wrote the skill: a 70-line router, a reference file holding the craft, and four scenario
files. Registered it in `skills/AGENTS.md` — which also gained permission for the
`scenarios/` layout — and pointed the two root rituals at it.

Two GitHub behaviours found by research contradicted what the repository's existing pull
requests do, and both are now written into the pull-request scenario: a `> [!NOTE]` alert
does not render inside a `<details>` block, and a relative link in a pull-request body is
not rewritten by GitHub, so it 404s. The action-projection check already required the
absolute commit-pinned form, so the two agree.
