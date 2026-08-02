# Record the missing Stage 0 verification transcripts as real command output

**Claimed-by:** unclaimed
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Parent:** none
**Repository scope:** records-only
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-complete-stage-0-verification-transcripts.md`

## Goal

Stage 0 of the markdown edge graph — heading-anchor validation inside `check_links`, the
mining CLI, and the append-only ledger — landed in commit e52f68e without recording its own
transcripts. The gating-experiment session that followed recorded its own commands in full
and stated the gap explicitly: the sections steps 1 through 8 owe are still missing. Those
sections are recorded today as conclusions in prose rather than as pasted command output,
which is exactly what the repository's never-fabricate guardrail exists to prevent.

Four transcripts are missing from the `verification.md` of task
2026-07-25-mine-markdown-cochange-couplings, and the file's own header already names them:

1. **The anchor-hole before-state.** A markdown link of the form `<absent-path>.md#<absent-anchor>`
   passed `python3 automation/reconcile/reconcile.py --check` before the fix, because
   `check_links` matched candidates against `re.fullmatch(r"[\w./-]+", cand)` and any
   candidate containing `#` was skipped whole — neither its path nor its anchor examined.
2. **`link-check`: a missing path carried behind a fragment.** After the fix, the same
   fixture yields a finding naming the missing path.
3. **`link-check`: an unknown fragment in a file that exists.** After the fix, a second and
   distinct finding names the fragment.
4. **The `agents-budget` run over `automation/AGENTS.md`.** That file sat at exactly 60 of
   its 60 permitted lines, and Stage 0's step 8 bought its new tool-table row by tightening
   prose rather than by dropping a rule. The check's real output is what confirms it.

This task runs those commands and pastes their real output. Nothing may be fabricated,
paraphrased, reconstructed from memory, or written as expected output. Where a command's
output no longer reproduces at the current commit — the before-state of item 1 is the
obvious case, since the hole it demonstrates is now fixed — the honest record is the real
output obtained today plus a plain statement of what changed and which commit range the
original behaviour belongs to. A reconstruction of what the command "would have printed"
is not an acceptable substitute for either.

The work is mechanical and lengthy. It reads and appends to one file, changes no code, and
adds no mechanism. It is scoped `records-only` for that reason.

## Acceptance criteria

- [ ] The `verification.md` of task 2026-07-25-mine-markdown-cochange-couplings contains
      one section per item above, each holding the exact command that was run and the real
      output it printed, inside a fenced block, pasted rather than summarised
- [ ] The before-state section demonstrates the pre-fix behaviour at a named commit, and
      records the real output of the run that produced it together with the exact commit or
      range that run was made against
- [ ] WHEN a command's output no longer reproduces at the current commit, THE FILE SHALL
      record the output actually obtained plus a one-line statement that the behaviour
      changed and where, rather than a reconstruction of the historical output
- [ ] Every fenced block added by this task is terminal output. No block is expected,
      paraphrased, or invented, and no conclusion is stated in place of a transcript
- [ ] The file's existing gating-experiment sections are left byte-identical; this task
      appends and does not rewrite another session's recorded output
- [ ] `python3 automation/reconcile/reconcile.py --check` exits 0 with the result staged,
      and its output is itself recorded in the file

## Links

- Stage 0 and Stage 1 of the staged plan: `docs/designs/markdown-edge-graph.md`
- Accepted architecture: `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`
- Guardrail this repairs — never fabricate, `verification.md` holds only commands actually
  run and their real output: `AGENTS.md`
- The task whose verification file this completes: 2026-07-25-mine-markdown-cochange-couplings
