# Naming conventions

The test for every name: **could a stranger guess the contents from the name alone,
without opening it?** Names are the cheapest documentation and the only documentation
everyone reads.

## Folders

- Full words, kebab-case, no abbreviations: `message-queue/`, not `mq/` or `msgq/`.
- Name by **role in the workflow**, not by artifact type:
  `message-queue/needs-human/decisions/` beats `inbox/` because it says whose move it
  is and what kind of move. Generic
  buckets (`misc/`, `stuff/`, `data/`, a catch-all `docs/`) are banned — if you can't
  name a folder's purpose, it doesn't have one yet.
- Numbered prefixes **only** for ordered pipelines where sorting is the point:
  `tasks/0_backlog/ … 4_done/`. Everywhere else, no numbers — they churn on insert.
- Route queue folders by stable properties: who acts next, then message kind. Dependency
  timing is not a folder — it lives in the filename, below.

## Files

- Kebab-case slugs; dates always ISO `YYYY-MM-DD`, prefixed when items need to sort by
  time: tasks `2026-07-22-add-quote-cache/`, conversations
  `2026-07-22-1430PDT-fix-cli-crash/` (times are local + timezone abbreviation —
  humans read wall clocks, not UTC).
- Queue items: exactly `blocking-<kebab-slug>.md`,
  `future-blocking-<kebab-slug>.md`, or `non-blocking-<kebab-slug>.md`; no date or
  numbering. The prefix says when unresolved work stops, not how severe it is. What each
  one means, and which way a live one may move, is stated once in
  `message-queue/AGENTS.md`.
- Reserved names, exact meaning: `AGENTS.md` (agent contract of its folder),
  `README.md` (human doc of its folder), `SKILL.md` (skill entry point), `task.md`,
  `plan.md`, `design.md`, `worklog.md`, `verification.md`, `handover.md`.
- A file that is one of a kind in its folder is named for its role (`index.md`,
  `current-state.md`), never `main.md` / `notes.md` / `new.md` / `final-v2.md`.

## Inside files

- Frontmatter is bold-key lines — `**Status:** in-progress` — not YAML. It renders on
  GitHub, survives any markdown editor, and parses with one regex (ADR:
  `memory/decisions/2026-07-22-bold-key-frontmatter.md`).
- Cross-references are paths in backticks or markdown links. Coded references
  ("see §6b", "rule R5") are banned; use the target's name.
- Two path conventions exist and are not interchangeable, so name which one you mean.
  **Root-relative** is from the repository root (`handbook/git-workflow.md`) and is what
  every machine-read field takes: a `Full context` written with `../` is dropped rather
  than resolved, and the item is reported as having no source. **File-relative** is from
  the file's own folder (`../../../message-queue/…`) and is required only where a link
  must be clickable from where it sits — the `Needs your attention` and `Next steps`
  projections in `templates/handover.md`. Prose links may use either; the link check
  tries both.
- The reconciler's link check verifies a cited path exists, and it exempts by target as
  well as by source, so knowing only the folder list will mislead you.
  - By source, whole files: `templates/`, `history/`, `memory/decisions/`,
    `message-queue/needs-agent/retries/`, and dot-directories. Inside any other
    `message-queue/` file it also skips the lifecycle fields (`Resolution evidence`,
    `Supersedes`, `Successor action`, `Follow-up review`, `Depends on`) and the human's
    own answer line, which name artifacts that need not exist yet.
  - By target, from anywhere: any path under `message-queue/needs-human/` or
    `message-queue/needs-agent/`, because resolving an action deletes its file; any
    `../`-relative link; and any candidate with no known file extension whose top-level
    entry is untracked, which is how prose like `and/or` escapes being read as a path.
  - A link in either class is a courtesy to the reader, not a checked claim. An absolute
    path is the one candidate reported rather than skipped: it names a machine, not this
    repository, so unquote it.

## Scratch

Anything throwaway lives under git-ignored `tmp/<purpose>/` (`tmp/probe-api/`,
`tmp/render-check/`) — never the repo root, never inside a tracked folder.
