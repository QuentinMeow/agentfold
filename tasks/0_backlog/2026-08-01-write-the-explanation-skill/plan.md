# Plan — write the explanation skill

- [ ] 1. Collect the external research: layered-explanation structures, plain-language
      rules, decision-brief and handover formats, and Agent Skill authoring guidance.
- [ ] 2. Write docs/designs/explaining-work-to-the-owner.md: the craft, the evidence
      behind each rule, and the routing decision (one skill, four scenario references).
- [ ] 3. Write skills/explain-to-human/SKILL.md — the router plus the rules an agent
      must apply on every surface. Keep it under the 70-line budget.
- [ ] 4. Write skills/explain-to-human/reference.md — the full craft: layering, jargon
      glossing, before/after framing, worked-example rules, anti-patterns, self-check.
- [ ] 5. Write the four scenario references under skills/explain-to-human/scenarios/.
- [ ] 6. Register the skill in `skills/AGENTS.md` and point the root `AGENTS.md` rituals
      at it.
- [ ] 7. Run the reconciler and the test suite; record real output in `verification.md`.
- [ ] 8. Open the pull request using the skill's own pull-request scenario as the test of
      whether the skill works.
