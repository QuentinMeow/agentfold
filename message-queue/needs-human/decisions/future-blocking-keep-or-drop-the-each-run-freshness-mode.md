# Keep all three freshness modes as answered, or drop `each-run` and ship two?

**Status:** waiting
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** keep all three freshness modes as answered in N5, or drop `each-run` and ship review-window plus advisory-only
**Full context:** `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`
**Resolution evidence:** `memory/decisions/2026-07-25-edge-graph-freshness-modes-after-measurement.md`
**Why-you-might-care:** `each-run` is the most expensive third of the freshness surface — a git history pass on every run plus the per-folder configuration that exists mainly to switch it off — and the measurement says it would have produced nothing at all on the design's own strongest case.
**If-you-do-nothing:** No freshness mechanism is implemented and `Update-when:` stays prose a reader acts on, which is the `advisory` mode by default; at the named boundary the mode set cannot be fixed and the freshness work stops there.
**Blocks at:** transition:start-edge-graph-freshness-modes
**Until then:** No freshness mode is built. Edges, once they exist, carry `Update-when:` as prose only, and no review debt is derived or dated.

## What you need to know

You answered question N5 with: all three freshness mechanisms exist — `each-run` (review
debt derived from git on every run), `review-window` (an absolute re-review date, default
7 days), and `advisory` (nothing mechanical) — each folder picks its own mode
independently, and the default is the 7-day review window. That answer is recorded in
`memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`, and this item asks you
to keep or amend one third of it after measurement.

Stage 0 shipped the mined co-change layer and then ran the gating experiment the plan
required. The experiment measured what `each-run` would actually have filed over the whole
recorded history of the design's single decisive example — the delivery-prefix rule owned by
`message-queue/AGENTS.md` and restated in all five queue templates. The answer is zero, and
the reason it is zero also makes it blind to the one real drift in its own domain.

`each-run` derives review debt by intersecting a target's changed line ranges with the
clause an edge names, and that debt closes automatically when the declaring file is next
modified. Over the 14 in-scope revisions of `message-queue/AGENTS.md`, the prefix
definitions themselves changed in exactly **2** — commits aca7014 and 3f4f1df. In **both**
of those commits every restating template was edited in the same commit: aca7014 touched
all five templates, and 3f4f1df touched all five plus `templates/handover.md`. Touched is
what closes derived debt, so across that entire history the mode would have filed **0
items**.

Worse, the one live drift the mechanism exists to catch happened *inside* aca7014. That
commit ("harness: harden queue snapshot boundaries") propagated "UTC" into the owning
contract at `message-queue/AGENTS.md` line 17, into the check summary in
`automation/AGENTS.md`, and into all five templates' `Blocks at` field lines — while
leaving line 4 of each template reading "a named date". The dependents were touched for a
neighbouring reason in the very commit that caused the drift, so the debt would have closed
instead of firing. That inconsistency is still live in the repository today.

Two further measurements bear on the same surface. `automation/AGENTS.md` is the hottest
markdown file in the repository at 19 in-scope revisions, and it has exactly one heading, so
clause anchoring — the thing that makes `each-run` precise rather than noisy — degenerates
to file scoping there; 12 of the 29 judged candidates (41%) point at that file. On
`message-queue/AGENTS.md`, by contrast, clause scoping is real and worth about 4.7×: an edge
anchored at the routing clause fires on 3 revisions rather than 14. Clause anchoring
survives the experiment. The derived-debt mode built on top of it does not.

## Differences

The choice is whether the repository maintains a mechanism that has been measured firing
zero times on the best available case and missing the only real failure in that case, in
exchange for keeping an answered decision intact. Keeping it costs a history pass per run,
a per-folder configuration surface whose main purpose is choosing whether to pay that cost,
and a tested clause-to-line-range intersection. Dropping it removes all three and leaves the
two mechanisms that were measured to work or to cost nothing: the dated review window you
already made the default, and advisory prose.

The other direction of the trade is real and worth naming. This repository holds four days
and roughly 107 in-scope markdown-touching commits, and the published work this technique
borrows from discards the first few hundred change records as warm-up. A mechanism that
fires zero times on four days of history is not proven useless on four years of it. The
counter-argument is that the zero is not a volume artifact: it comes from the debt-closing
rule asking whether the dependent was *touched* rather than whether it was *updated*, and
that rule does not improve with more history.

## Options

### Option A — keep all three modes, exactly as answered in N5
`each-run`, `review-window` (default, 7 days), and `advisory` all ship, each folder
configures its own independently, and the answered decision stands unamended.
*Example consequence:* A future session building the freshness surface implements the
clause-to-line-range intersection, the per-folder mode selector, and tests for all three
modes. On today's history the `each-run` folders file no debt items, and a repeat of the
aca7014 drift still goes unreported, because the templates would again be touched in the
same commit. The mode is available for a history that behaves differently from this one.

### Option B — drop `each-run`; ship `review-window` and `advisory`
Two modes instead of three. `review-window` stays the default at 7 days, `advisory` stays
the cheap opt-out, and the per-folder configuration surface shrinks to a two-way choice.
The clause anchor stays, because it earned its place on the impact query independently.
*Example consequence:* A future session building the freshness surface implements a dated
re-review field and the prose mode, both of which the repository already runs successfully
on memory entries. No git history pass runs per invocation. The aca7014 class of drift is
caught by whoever reviews the dated edge when its window comes due, rather than by a
derived intersection that closes on an unrelated touch. If later history shows derived debt
would have fired, the mode returns as a new decision.

## Recommendation

Option B. Be explicit about what it costs procedurally: this reverses one third of an
answered decision, and because a decided ADR is never rewritten, choosing B means a new ADR
recording the measurement and linking
`memory/decisions/2026-07-25-markdown-edge-graph-architecture.md` as the record it amends —
not an edit to that file. The recommendation rests on two measured facts rather than on a
preference: zero items filed across the whole history of the strongest case, and silence on
the one live drift inside that history.

**Your answer:** choose B for now, but keep A in mind (or mark as not implemented), we might review it later.

<!-- A concrete response is immutable. If it is a counter-question, fold the answer into
Resolution evidence and create a same-timing successor with **Supersedes:** `<this path>`. -->
