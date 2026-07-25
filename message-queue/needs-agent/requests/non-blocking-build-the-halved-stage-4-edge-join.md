# Build the surviving half of Stage 4 — the three-way join and undeclared repair filing

**Status:** open
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** Build the confirmed/undeclared/suspect join as one report over declared edges and mined candidates, and file one repair item per `undeclared` result; leave clause-scoped review debt and its repair filing out.
**Full context:** `docs/designs/markdown-edge-graph.md`
**Resolution evidence:** `roadmap/current-state.md`
**If unanswered:** Declared edges and mined candidates stay two separate reports that a reader joins by hand, and an omitted edge leaves no durable trace anywhere.

## What you need to know

Stage 4 was scoped as four things: the joined report, the `impact` query contract,
clause-scoped review debt, and repair-item filing for both. The gating experiment supports
half of that.

**What survives.** The three-way join — `confirmed`, `undeclared`, `suspect` as one result
rather than two reports — is nearly free once declared edges exist, and it is the mechanism
that surfaced the fivefold restatement of the queue delivery-prefix rule during the
experiment. Repair-item filing for the `undeclared` list survives with it, because an
omission that leaves no durable item is an omission nobody picks up later.

**What is excluded, and why.** Clause-scoped review debt derived on every run is out of
this action, and so is repair-item filing for that debt, because the debt it would file was
measured not to exist: over the 14 in-scope revisions of `message-queue/AGENTS.md` the
prefix definitions changed in exactly 2, and in both of those commits every restating
template was edited in the same commit, so debt that closes on a touch would have filed
zero items across the whole history of the strongest case. Whether the mode ships at all is
an open owner decision at
`message-queue/needs-human/decisions/future-blocking-keep-or-drop-the-each-run-freshness-mode.md`,
and this action stays scoped to the join regardless of how that decision lands.

One reading note for whoever builds the join: an accept line in the co-change ledger that
Stage 0 ships beside its mining CLI means *judged a real dependency, to be declared if and
when the schema ships* — not *an edge was declared*. Stage 0 recorded 28 accepts with no declared
edge behind any of them, so the first join run finds them all `undeclared` by construction,
and that is the correct answer rather than a bug.

## Done when

One command prints the joined `confirmed` / `undeclared` / `suspect` result over the
activated directories, each `undeclared` result has a durable repair item, unit tests cover
the join's three classifications, and `python3 automation/reconcile/reconcile.py --check`
plus `python3 automation/run_tests.py` both pass with real output recorded in the task's
`verification.md`.
