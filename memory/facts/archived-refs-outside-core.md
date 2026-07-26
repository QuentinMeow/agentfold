# Work refused by Core admission is preserved as an `archive/*` annotated tag, not a branch

**Description:** Rejected-but-reusable work lives on annotated `archive/*` tags whose message carries the reasoning — check there before rebuilding something that looks unprecedented
**Source:** task 2026-07-22-prevent-false-github-reauth; decision `memory/decisions/2026-07-26-agent-specific-guidance-stays-out-of-core.md`
**Review-by:** 2026-11-05

Work that is well built but fails **Core admission** is not deleted and not left on a
branch. It is preserved as an annotated tag under `archive/`, and the tag message states
why it was refused, which files are portable, and which are runtime-specific. Branches are
swept by routine merged-branch cleanup and tags are not; the first such ref was nearly lost
that way.

List them with `git tag -l 'archive/*'` and read one with `git show <tag>` — the message is
the record, so no other file needs to restate it. Current refs:

- archive/2026-07-22-prevent-false-github-reauth at `f4cc1a2` — an evidence-gated guard
  stopping agents from prescribing `gh auth login` after a sandboxed `gh auth status`
  failure (upstream openai/codex issue 19262). Portable half: the classifier at
  skills/github-auth-guard/scripts/check.py on that ref, and its tests. Refused half: the
  Codex hook and the Codex installer, which writes under `~/.codex`.

Paths and refs above are deliberately unquoted: they resolve on the archived ref, not on
`main`, and backticking them would make `link-check` read them as live repository paths.

Do two things differently because of this. Before designing a mechanism that feels
unprecedented here, check these refs — the analysis may already exist, including the reason
it was refused. And when proposing a runtime guard, split it: the portable mechanism can be
proposed with a complete `## Core fit` receipt, while the runtime adapter belongs in that
runtime's own configuration, outside this repository.
