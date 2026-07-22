# Adopting AgentFold

Two paths: start a new project on the structure, or retrofit an existing repo. Either
way, adopt incrementally — each piece works alone, and the reconciler only checks the
folders that exist.

## Starting a new project

1. Copy this repo, delete `services/` contents, and write your own first service under
   `services/<name>/` with an `AGENTS.md` from `templates/service/AGENTS.md`.
2. Edit the root `AGENTS.md`: one-paragraph purpose, your repo map rows, pick a
   collaboration mode. Delete example content in `memory/` and `roadmap/`; write your
   own `roadmap/desired-state.md` first — it seeds the backlog.
3. Run `python3 automation/install.py`, then `reconcile.py --check` until clean.
4. Open the repo in your agent and give it a task; the structure does the rest.

## Retrofitting an existing repo

Add in this order — each step pays for itself before the next:

1. **Root `AGENTS.md`** (worth it alone). Purpose paragraph, repo map, guardrails,
   read order. Keep it under the line budget; move depth into linked docs.
2. **`message-queue/` + the queue ritual.** This is the async-collaboration core:
   copy the folder, add the ritual section to your `AGENTS.md`.
3. **`tasks/` + `history/`.** Start filing new work as task folders; require
   `handover.md` per session. Don't backfill old work.
4. **Per-folder `AGENTS.md`** for the 2-3 directories agents touch most. Write each as
   that folder's API: what it does, boundaries, links to its dependencies. Reactive
   rule: a folder earns a contract after the second time an agent gets it wrong there.
5. **`automation/`** — installer, hooks, reconciler. Delete the checks for folders you
   haven't adopted; the check registry in `reconcile.py` is a plain dict.
6. **`memory/` + `roadmap/`** once cross-session amnesia actually hurts.

## Making your code folders agent-native

For each real service/module folder, its `AGENTS.md` answers exactly four things: what
this service does (one paragraph), how to verify changes (the test command), what its
boundaries are (what it must never import/touch), and where its dependencies' contracts
live (links). See `services/quote-api/AGENTS.md` for the shape at its smallest.

## Advanced: public/private overlay

To open-source tooling while personal or company data stays private: keep a second git
repo mounted at a git-ignored `private/` path that mirrors the public folder structure
(`private/message-queue/`, `private/memory/`, …), point config at it, and add a leak
check that scans commits for tokens derived from config (never hardcoded). It's on
`roadmap/desired-state.md` as a packaged module; until then, the pattern description
above is the spec.
