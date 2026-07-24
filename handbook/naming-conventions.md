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
  timing is visible in the filename and may only escalate with `git mv`; update every
  live link in that coordination commit. Weakening resolves the old identity and creates
  an authorized replacement (ADR:
  `memory/decisions/2026-07-23-live-queue-obligations-only-weaken-with-evidence.md`).

## Files

- Kebab-case slugs; dates always ISO `YYYY-MM-DD`, prefixed when items need to sort by
  time: tasks `2026-07-22-add-quote-cache/`, conversations
  `2026-07-22-1430PDT-fix-cli-crash/` (times are local + timezone abbreviation —
  humans read wall clocks, not UTC).
- Queue items: exactly `blocking-<kebab-slug>.md`,
  `future-blocking-<kebab-slug>.md`, or `non-blocking-<kebab-slug>.md`; no date or
  numbering. The prefix says when unresolved work stops, not how severe it is.
- Reserved names, exact meaning: `AGENTS.md` (agent contract of its folder),
  `README.md` (human doc of its folder), `SKILL.md` (skill entry point), `task.md`,
  `plan.md`, `design.md`, `worklog.md`, `verification.md`, `handover.md`.
- A file that is one of a kind in its folder is named for its role (`index.md`,
  `current-state.md`), never `main.md` / `notes.md` / `new.md` / `final-v2.md`.

## Inside files

- Frontmatter is bold-key lines — `**Status:** in-progress` — not YAML. It renders on
  GitHub, survives any markdown editor, and parses with one regex (ADR:
  `memory/decisions/2026-07-22-bold-key-frontmatter.md`).
- Cross-references are repo-relative paths in backticks or markdown links — the
  reconciler verifies they exist. Coded references ("see §6b", "rule R5") are banned;
  use the target's name.

## Scratch

Anything throwaway lives under git-ignored `tmp/<purpose>/` (`tmp/probe-api/`,
`tmp/render-check/`) — never the repo root, never inside a tracked folder.
