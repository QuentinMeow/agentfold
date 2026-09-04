# Adopting AgentFold

Two paths: start a new project on the structure, or retrofit an existing repo. Either
way, adopt incrementally — each piece works alone, and the reconciler only checks the
folders that exist.

## Starting a new project

1. Copy this repo, delete `services/` contents, and write your own first service under
   `services/<name>/` with an `AGENTS.md` from `templates/service/AGENTS.md`.
2. Edit the root `AGENTS.md`: one-paragraph purpose, your repo map rows, pick a
   collaboration mode. Delete example content in `memory/` and `roadmap/`; write your
   own `roadmap/desired-state.md` first, one entry per goal from `templates/roadmap/goal.md` —
   it seeds the backlog.
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

## Advanced: layered public/private workspace

An ignored nested repository, symlinked mirror, hook, or private branch is a navigation
convention, not a confidentiality or publication boundary — so none of them is a
specification you can build a privacy claim on.

The current proposal is
`docs/designs/layered-development-workspace.md`: a non-Git envelope, private integration
source plus supervised admitted sessions for public-base and private versioned work,
separate no-Git restricted/raw/temporary siblings, and a clean public publisher with a
distinct object store. Even that topology proves only separation of declared storage
locations; it does not inspect file bytes, hard-link sharing, undeclared mounts, Git
configuration authority, or content admission. A claim that the publisher cannot read
private roots requires a separately attested capability boundary.

Until the packaged workflow exists, keep sensitive/raw material outside every worktree,
keep public publication manual and blocked by explicit review, and report missing
private state rather than silently falling back to public content.
