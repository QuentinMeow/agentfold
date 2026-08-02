# Stop a wrapped sentence from being read as a command to the reader

**Claimed-by:** unclaimed
**Filed:** 2026-08-02, by claude, from a false positive hit while writing the pull-request body for task 2026-08-02-advise-on-explanation-shape
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-wrapped-line-from-reading-as-a-command.md`

## Goal

`automation/check_action_projection.py` refuses a pull-request body that instructs the
reader outside its `## What to review` section. That rule is right: a body that tells the
reader to do something is an ask, and an ask belongs in a queue item
(`handbook/git-workflow.md`).

The detector scans line-first, so it judges each physical line rather than each sentence.
A body wrapped at a normal column can therefore put an ordinary noun phrase at the start of
a line and have it read as a bare imperative. The reported instance: a sentence that wrapped
so a line began `repair for such a finding …` was scanned as the command "repair", and the
boundary check failed a body that instructed nobody.

The agent that hit it reworded two sentences to get its pull request open. That is the wrong
repair — it means the true rule is not "do not instruct the reader" but "do not instruct the
reader, and also do not let a wrap land on certain words", which nothing states and nobody
can follow. Line wrapping is invisible to the author's intent.

## What this is not

This is not a request to loosen the instruction rule. A body that genuinely commands the
reader must still fail. The defect is the unit of analysis, not the strictness.

## Acceptance criteria

- [ ] WHEN a pull-request body contains a declarative sentence that happens to wrap so that
      a continuation line begins with a word that is also a verb, THE BOUNDARY GATE SHALL
      NOT report it as an action. Prove it with the reported instance — a sentence wrapping
      onto a line beginning `repair for such a finding` — as a regression fixture.
- [ ] WHEN a pull-request body contains a real imperative aimed at the reader outside
      `## What to review`, THE BOUNDARY GATE SHALL still report it. Cover at least: an
      imperative that begins a physical line, and one that begins a sentence mid-line.
- [ ] Re-wrapping an accepted body at a different column SHALL NOT change the gate's verdict.
      This is the property the current detector lacks; a test that re-wraps one real body at
      two widths and asserts the same result is the honest way to show it.
- [ ] Every existing test in `automation/tests/test_check_action_projection.py` passes
      unmodified, or a modified expectation is justified in `design.md` as a fixed defect
      rather than a weakened rule.
- [ ] `python3 automation/run_tests.py` passes with real output in `verification.md`.
- [ ] `design.md` carries the completed core-fit receipt from `templates/task/design.md`.

## Links

- The detector: `automation/check_action_projection.py`
- The rule it enforces, and why a body may not carry an ask: `handbook/git-workflow.md`
- How a body is meant to be written: `skills/explain-to-human/scenarios/pull-request.md`
