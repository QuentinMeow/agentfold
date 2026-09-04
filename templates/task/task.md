# <What this task achieves, one line>

**Claimed-by:** unclaimed
**Mode:** <optional — overrides the repo collaboration mode for this task>
**Filed:** <YYYY-MM-DD>, by <who>, from <chat | request item | roadmap goal — link>
**Parent:** <parent task id, or "none">
**Repository scope:** <core | service:<name> | records-only>
**Queue actions:** <exactly none, or backticked live queue paths separated by ; or , with no prose>
<!-- Human asks and durable cross-session agent asks in any task artifact must be exact
action-labeled links to paths above. Plain questions or requests are not projections. -->

## Goal

<2–5 sentences. Write for a reader who knows the root AGENTS.md and nothing else:
what to build/fix/change, and why it matters. Link the relevant service contracts.>

## Acceptance criteria

<Checkable statements — each verifiable by a command, a test, or a concrete
observation. "WHEN <condition>, THE SYSTEM SHALL <behavior>" phrasing works well.
Every line opens with its provenance: `[user <YYYY-MM-DD>]` traces to the entry of that
date in `requirements.md`; `[derived]` is the agent's own addition and says, after the
dash, why the owner's words need it. Tick each box when its criterion is actually met,
so the list reads as progress. By `3_in-review` every box is ticked, or
`verification.md` names the one that was dropped and why. No check reads the boxes;
`task-provenance` reads the labels.>

- [ ] [user <YYYY-MM-DD>] <criterion>
- [ ] [derived] <criterion> — <why the owner's words need this>

## Fit

<Filled by the agent that starts the task, before work: required from `1_in-progress`
for `core` and `service:` scope, optional for `records-only`. Compare the full picture
(`roadmap/desired-state.md`), what is true today (`roadmap/current-state.md`), and this
request. `aligned`: inside the goal as written. `extends`: consistent with the goal but not
covered by its text, so the same commit updates the goal entry. `conflicts`: contradicts a
confirmed goal or a current-state fact. `unclear`: two plausible readings, or a fit that does
not feel intuitive. A `conflicts` or `unclear` fit files a needs-human clarification or
decision, lists it in Queue actions, and is never worked around.>

**Serves:** <G<n> — the goal's title copied exactly | none — `<needs-human clarification path>`>
**Today:** <the current-state fact this task changes, one sentence>
**Fit:** <aligned | extends | conflicts | unclear> — <one sentence on how the request meets the goal and today>

## Links

- <roadmap goal / decision / issue this traces to>
