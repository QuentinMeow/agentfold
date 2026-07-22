# services/ — the product code

One folder per service; each is independent and owns its own contract, tests, and
conventions (`handbook/principles/folder-as-a-service.md`). This file only routes.

| Service | What it does | Enter when |
|---------|--------------|------------|
| `quote-api/` | serves quotes as JSON (data + retrieval; the only owner of the quote store) | changing what quotes exist or how they're served |
| `quote-cli/` | human-friendly command line on top of quote-api | changing how quotes are presented to people |

Rules for every service here:

- Deliberately tiny and Python-stdlib-only — they exist to demonstrate the harness
  (`memory/facts/example-services-stay-stdlib-only.md`).
- Verify with the command in the service's own `AGENTS.md`; all of them must pass via
  `python3 automation/run_tests.py`.
- New service = new folder + `AGENTS.md` from `templates/service/AGENTS.md` + a row in
  this table.
