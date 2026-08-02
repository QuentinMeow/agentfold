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

## 2026-08-02 01:10 PDT — claude

Tested the skill by having an independent agent use it blind: it read only the skill and a
real commit, wrote a pull-request body, and then critiqued the skill rather than its own
output. That found four defects that reading the skill could not, all now fixed and
recorded in the repair commit. The largest was structural — the section-order table and the
folding instruction described two incompatible layouts — and it would have produced a body
the boundary check refuses.

The critique's most useful complaint was that the skill shows fragments and never one whole
body, so every remaining question was about the seams between fragments. One complete
worked body now closes the file.

Two of its complaints were rejected. The 25-word sentence ceiling stands, restated as
per-sentence rather than per-item, because the agent measured whole multi-sentence bullets
against it. And the ban on bullets for causally linked facts stands, clarified so that
lists of independent items are explicitly fine.
