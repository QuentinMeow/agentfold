# Design notes — let a handover project a queue field that contains an inline code span

**Status:** decided

## Problem

The handover projection's context comparison builds its expected value from a queue item's
raw field bytes, which keep their backticks, and compares it against handover entry prose
read through `prose_without_links`, which blanks every closed inline code span. The two
sides are normalised differently, so a `needs-human` item whose `Why-you-might-care` or
`If-you-do-nothing` carries a code span can never be copied into a conforming entry. One
live item does, which blocked the end-of-session ritual repository-wide.

An earlier same-session diagnosis attributed the failure to the two-element loop over
`prose_without_links(entry)` and `prose_without_links(rendered_human_text(entry))`, reading
it as a raw-versus-rendered choice that wrongly demanded both. That reading was wrong.
Both elements run `prose_without_links`, so both blank code spans, and the two forms are
byte-identical unless the entry contains raw HTML. Measured on the live item, both branches
fail, so accepting either instead of both changes nothing:

```
form1 raw-semantic: matches=False
form2 rendered:     matches=False
require BOTH (current): False
accept EITHER (proposed): False
form1 == form2 : True
```

The tuple is the rendered-HTML guard — `- [x](y) — <p>Why…</p>` is the only shape where the
two forms differ — and it is not the defect. The defect is the asymmetry between the two
sides of the comparison.

## Options considered

### Option A — source-identical comparison
Compare the entry's source spelling against the queue field's raw bytes, backticks included,
by dropping the code-span stripping from the copy check entirely.
*Example consequence:* A handover author must reproduce every backtick exactly. The context
check becomes stricter than the action-label check on the very same queue item, since
`normalized_action_tokens` renders code spans away before comparing labels. An author who
copies the item's rendered text passes the label check and fails the context check.

### Option B — symmetric `render_inline_code` on both sides
Normalise both sides through `render_inline_code`, which removes code-span delimiters while
retaining their contents, and leave the two-element rendered-HTML guard intact.
*Example consequence:* `` `each-run` `` and `each-run` both project, and a reworded or
content-swapped span still fails because the span's contents survive the normalisation on
both sides.

## Chosen

Option B. The decisive argument is consistency with the immediately adjacent check: the
action-label comparison three lines above already normalises through
`normalized_action_tokens`, which calls `render_inline_code`. That is exactly why the live
item's backticked `Action` projects while its context cannot. The context comparison is the
lone outlier, so making it consistent with its neighbour is a repair rather than a new
policy, and it weakens nothing — span contents are preserved on both sides.

The normalisation is named explicitly: **both sides of the copy comparison are rendered
through `render_inline_code`**, applied in the same pipeline position where the code-span
blanking used to sit, i.e. after `semantic_text` has already blanked fenced blocks. The new
`copied_prose_without_links` helper in `automation/check_action_projection.py` expresses
that view; `prose_without_links` is unchanged and still serves every detection-only caller.

### Ruling 1 — backticks are optional, not required

Render-equality means `` `each-run` `` and `each-run` compare equal, so a handover author may
write either spelling. Source-identical comparison (Option A) was rejected because it would
make the context check stricter than the action check on the same item, which is precisely
the inconsistency that produced this defect. The check still rejects any difference other
than whitespace reflow and code-span delimiters: reworded prose fails, and a span whose
contents differ fails.

### Ruling 2 — the `needs-agent` tightening, decided by measurement

Rendering instead of blanking also closes a hole on the `needs-agent` branch, where an entry
whose link is supposed to be its entire content could previously pass by carrying a stray
code span that blanked to the empty string. The choice between taking that tightening and
guarding the repair to `needs-human` was settled by measurement rather than from first
principles; the numbers are recorded in `verification.md`.

Exactly one committed handover entry carries a code span in a projected section
(`2026-07-25-0749PDT-reconcile-post-merge-branches`, a `Next steps` entry). Its span sits
inside the link label, which both the old and the new view remove with the link, so its
residue is `-` before and after and its verdict is unchanged. No handover the checks evaluate
produces a new finding, on the newly-added-handover path or over the range path, and the
full test suite passes unchanged.

The tightening is therefore taken rather than guarded. Leaving a known hole open inside a
check-repair task is the wrong trade in a repository whose rule is
`automation/AGENTS.md`'s "Never weaken a check to pass", and an agent entry whose link must
be its entire content should not pass by having extra content blanked away. It is pinned by
a regression test so the behaviour cannot silently revert.

### The link-label comparison and the `needs-agent` entry path

The task asked whether the same asymmetry exists in the link-label comparison and the
`needs-agent` entry path. The label comparison is already safe: it runs both sides through
`normalized_action_tokens`, which renders code spans on both sides. The `needs-agent` entry
path shares the repaired comparison and is covered by Ruling 2.

## Core fit

**Agent substitution:** pass — the repair is a normalisation inside a repository invariant check that any agent runtime invokes as a subprocess, with no runtime-specific behaviour.
**Provider substitution:** not-applicable — the handover projection reads repository files only and never contacts a provider.
**Repository substitution:** pass — any adopted repository whose queue items name files, fields, or commands in their human-facing context fields hits the identical block, since backticks are the ordinary way to write those.
**User-global writes:** none
**Why AgentFold core:** the end-of-session handover ritual is a root contract obligation and the reconciler is its referee, so a defect that makes the ritual unsatisfiable for every session in every adopting repository is a core check repair, not local configuration.
**Thin adapter:** none
