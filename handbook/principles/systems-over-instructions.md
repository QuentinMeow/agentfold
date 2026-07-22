# Systems over instructions

An instruction in a contract file is followed most of the time. A hook, test, or check
runs every time. Whenever a rule matters, encode it in something that executes —
instructions are for judgment calls, systems are for invariants.

## Rules

- **Every "always/never" earns a check.** If you write "always X" in an `AGENTS.md`,
  either add a mechanical check (reconciler rule, hook, test, CI step) or accept that X
  is a preference, not a guarantee. The escalation ladder: instruction → checklist in a
  template → reconciler finding → pre-commit block.
- **Verification is part of the work.** Every task ends with `verification.md` listing
  commands actually run and their real output. A change an agent cannot verify
  mechanically (test, build, render, screenshot) needs a human review item filed.
- **Hooks are tracked and installed idempotently.** `automation/hooks/` is versioned;
  `automation/install.py` wires it up. A quality gate that lives only on one person's
  machine doesn't exist.
- **Budgets fight entropy.** Line budgets on contract files (enforced by the
  reconciler) force curation — every addition must beat something it displaces.
- **Bypasses are loud.** `--no-verify` and its cousins are never used silently; a
  bypass is reported in the handover with a reason.

## Why

Agents don't reliably follow instructions, and neither do humans. A repo whose quality
bar lives in prose degrades with every session; a repo whose quality bar lives in
executable checks stays at the bar no matter who — or what — is typing. Write
instructions for taste; write systems for truth.
