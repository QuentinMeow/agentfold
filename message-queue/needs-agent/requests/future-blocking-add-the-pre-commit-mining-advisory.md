# Move the mined report into the reconciler as an advisory-tier check

**Status:** open
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** Once reconciler findings carry severity tiers, move the mined co-change report into the reconciler as an advisory-tier finding that never fails `--check`, and record the pre-commit cost of its history walk before wiring it in.
**Full context:** `docs/designs/markdown-edge-graph.md`
**Resolution evidence:** `automation/AGENTS.md`
**Blocks at:** event:reconciler-finding-severity-tiers-shipped
**Until then:** The miner stays a standalone CLI whose report verb always exits 0, invoked by an agent or by CI on request; nothing mined touches the pre-commit path.

## What you need to know

Stage 0 deliberately kept mining out of the reconciler's `CHECKS` registry. Every finding
in `automation/reconcile/reconcile.py` blocks the commit today, because findings carry no
severity, and a mined coupling is a suggestion whose measured effective-false-positive rate
lands on the probation band over the default report's top ten — 1 rejection in 10, exactly
the 10.0% trigger. Shipping suggestions through a blocking gate turns an advisory into hard
stops on unrelated commits, which is the failure mode the rejected digest-pin mechanism died
of. There is a second cost: a whole-history `git log` walk inside a check is quadratic here,
because `check_task_admission_history` re-enters the check registry once per admitted Git
edge.

The blocking dependency is finding severity tiers, and that work is **already filed** — the
canonical action is
`message-queue/needs-agent/requests/non-blocking-pick-up-severity-tiers-for-reconciler-findings.md`,
whose backlog task splits the registry into blocking and advisory tiers. This action links
that one and does not restate or duplicate it. When the tiers exist, the mining advisory has
a place to live and this action becomes actionable.

The advisory tier is not a free upgrade even then: it moves a history walk onto the
pre-commit path that currently costs nothing there, so the cost measurement belongs in the
same change rather than after it.

## Done when

Severity tiers exist, the mined report is reachable from the reconciler as an advisory-tier
finding that never fails `--check`, the pre-commit wall-clock cost of the added history walk
is recorded as real measured output, and `automation/AGENTS.md` names the advisory tier and
the check that uses it.
