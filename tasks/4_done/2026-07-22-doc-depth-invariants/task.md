# Codify queue-message disposability and README depth rules

**Claimed-by:** claude (chat session)
**Mode:** async
**Filed:** 2026-07-22, by the repo owner (chat request, transcribed here — chat leaves no trace)
**Parent:** none
**Repository scope:** core

## Goal

Two design clarifications from the human, given in chat. First: a queue message should
be like a retryable API call — simple, self-contained, disposable, and *regenerable*,
because everything durable (background, artifacts, design reasoning) lives in the task
folder or `memory/`, and the message only carries the summary a reader needs to act.
Second: `README.md` is the human landing page and must stay a short pitch + map, with
technical depth living in `handbook/` and linked — and that should be enforced, not
hoped for. Both ideas are mostly implicit in the current design; this task makes them
explicit and mechanical.

## Acceptance criteria

- [x] `message-queue/AGENTS.md` states that items are regenerable projections of state
      that lives elsewhere, and names the one exception (an unfolded human answer)
- [x] `handbook/decision-guide.md` tells writers durable background belongs in the task
      folder, never only in the queue file
- [x] Root `AGENTS.md` states the README depth rule (short pitch + map, depth in `handbook/`)
- [x] `reconcile.py` enforces a line budget on the root `README.md`; the check fires
      when the budget is exceeded (demonstrated in `verification.md`)
- [x] `automation/reconcile/reconcile.py --check` and `automation/run_tests.py` pass

## Links

- Chat request (this file is the transcription; chat leaves no trace)
