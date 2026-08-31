# Design notes — make a human question answerable from its own bytes

**Status:** decided

## Problem

Four live review items were rejected by the owner as unanswerable. The obvious repair —
tell agents to write more reasoning — is the best-replicated negative result in the
human-AI decision literature: explanations raise acceptance regardless of correctness
(Bansal 2021), and human+AI performed worse than AI alone (Buçinca 2021, N=199). The
constraint is to raise what a reader can *verify* without raising what an agent *asserts*.

## Options considered

### Option A — minimal: three surgical additions plus closing the checker's blind spot
Keep the template, add a verified quote, a third answer state, and a third branch in
`check_explanation_shape()`. *Example consequence:* an item that cites a design document
without quoting it reports one advisory line, and the ten frozen items become visible to
the checker for the first time without any of them being editable.

### Option B — structural: build a reader-competence gate
Add machinery that answers "can this reader answer this at all" before the item is filed.
*Example consequence:* an item whose question the owner cannot answer is caught at
authoring time — but the gate's own evidence is a field a weak author always fills "yes",
which R6 X1 and R9 backfire #7 both measure as producing empty boilerplate.

## Chosen

A, with B's byte-grounded substitute adopted in three of five parts. The competence
question is answered on the *read* side — by what sits in front of the reader — not by a
self-certification the author supplies. Vasconcelos 2023 is decisive: highlight and
excerpt beat written prose at every difficulty tested, and the most salient condition
reached zero over-reliance. So the rule demands the source's own bytes behind a resolving
anchor, never an agent's argument about them.

Rejected deliberately: dropping `"../"` from `LINK_SKIP_PREFIXES`, which looks like the
cheap fix. Measured: 816 `../` destinations repo-wide, none carrying a fragment, nearly
all in immutable history. The new check resolves anchors itself instead.

Left open and stated rather than hidden: the check verifies a quote is *real*, not that it
is *relevant*. A true, correctly-anchored, useless sentence passes. No mechanical answer
to that exists in this design.

## Core fit

**Agent substitution:** pass — the rules are text in `skills/` and `templates/`, and the
check is stdlib Python reading committed bytes. No runtime, model, or vendor is named.
**Provider substitution:** pass — nothing here touches a hosting provider; anchors are
resolved against the local tree, never a forge API.
**Repository substitution:** pass — any adopted repository whose agents ask its humans
questions has this failure mode; the rule references no AgentFold-specific artifact.
**User-global writes:** none
**Why AgentFold core:** the message queue is the repository's only channel to its owner,
and a question that cannot be answered from its own bytes is a coordination defect in that
channel, not a preference of one operator's setup.
**Thin adapter:** none
