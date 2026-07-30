# Design notes — parseable reporting for an empty selection

**Status:** decided

## Problem

Two runs that mean opposite things print nearly the same thing. A run that selected no
test file because nothing staged could affect one returns 0 after printing a sentence and
an elapsed time. A run that died before it could summarize also prints no summary. Every
other run ends with `tests: N/M files passed`, and every verification record in this
repository transcribes that line as its evidence, so the one shape a reader and a parser
both rely on is exactly the shape the empty case omits.

## Options considered

### Option A — Print the summary line unconditionally, keeping the existing sentence
The empty path prints `tests: 0/0 files passed` after the sentence that explains why
nothing was selected. One format, parsed one way, for every run.

### Option B — Adopt the rejected experiment's wording
Branch exp/c-tiered printed `tests: 0/0 selected files passed` and replaced the
diagnostic sentence. Two spellings of the summary line then exist, so anything parsing
the output has to know both, which defeats the reason for printing it.

## Chosen

Option A. The value of the line is that it is the same line every time; a second spelling
would reintroduce the ambiguity it exists to remove. The existing diagnostic sentence is
kept because it explains *why* the count is zero, which the count alone does not.

Two smaller changes travel with it. The skipped-file report already names every file that
did not run — that landed with the input-ownership selector — but it did not say where
that coverage happens, so a reader had to know the workflow to judge whether the skip was
safe. And the inert-probe call site still named the Git wrapper installer that was renamed
when the shell wrapper was removed, so the probe raised `AttributeError` instead of
running. That defect survived because the probe is gated behind an environment variable
the suite never sets, which is why the guard added for it is generic: it asserts that
every runner attribute this test file names actually exists, rather than checking the one
call site that happened to break.

The central rule of exp/c-tiered is deliberately not taken. It is rejected in
`memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`.

## Core fit

**Agent substitution:** pass — the runner prints to stdout and any agent runtime reads the same bytes; no behaviour depends on which agent invoked it
**Provider substitution:** not-applicable — nothing here reads or writes any external provider
**Repository substitution:** pass — an adopted repository running this gate gets the same one summary format for every run, which is what makes its verification records checkable
**User-global writes:** none
**Why AgentFold core:** The repository contract forbids fabricating test results, so a successful run that prints no parseable summary is a hole in that contract rather than a formatting preference
**Thin adapter:** none
