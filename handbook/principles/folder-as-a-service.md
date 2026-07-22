# Folder as a service

Every folder is an independent service. Its `AGENTS.md` is its API for agents: what the
folder does, how to work inside it, and where its boundaries are. Subfolders are the
service's endpoints — named so clearly that a stranger can guess what each does without
opening it (rules: `../naming-conventions.md`).

## Rules

- **Self-contained.** A service owns its code, tests, docs, and conventions. It never
  imports another service's internals. Shared code is either duplicated deliberately
  (vendored, with a drift check) or promoted into a service of its own.
- **Link, don't reach.** When service A needs service B, A's `AGENTS.md` says so with a
  link to B's `AGENTS.md` — the agent follows the link and works through B's declared
  interface. No folder ever documents another folder's internals.
- **A parent folder routes.** A folder containing sub-services lists each one with one
  line — what it does and when to enter it — like an API gateway listing endpoints.
- **Contracts nest, closest wins.** Per the [AGENTS.md standard](https://agents.md/),
  the nearest `AGENTS.md` up the tree applies. Child files add local context only; they
  never restate or contradict an ancestor — a conflict is a bug in the child.

## Why

Independent folders are what let multiple agents work in parallel without stepping on
each other: each agent stays inside one service's boundary, and cross-service needs
become explicit link-following instead of accidental coupling. The same boundary is
what makes context cheap — an agent loads one folder's contract, not the whole repo.

## Example

`services/quote-cli/AGENTS.md` says: "Quotes come from the quote-api service — read
`../quote-api/AGENTS.md` and call its public function; never import its internals."
An agent fixing the CLI never needs to understand the API's storage format.
