# Publish the hard gate through an external OIDC-backed App

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-27, by codex, from task `2026-07-27-configure-test-gates-and-time-budgets`
**Parent:** 2026-07-27-configure-test-gates-and-time-budgets
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-publish-hard-gate-through-external-oidc-app.md`

## Goal

After controlled external test completion exists, publish one exact-candidate hard-gate result
through an independently controlled OIDC-to-GitHub-App boundary. Candidate workflows receive no
publisher credential and cannot mint, replace, or replay the required status.

## Acceptance criteria

- [ ] Task `2026-07-27-control-external-test-oracle-and-stage-migration` is complete, and the
      publisher accepts only its exact enforcement-eligible completion record.
- [ ] The controller binds exact repository, base, head, ordered synthetic merge, branch,
      displaced tip, test-plan identity, and controlled completion before publication.
- [ ] A short-lived OIDC exchange authenticates a dedicated GitHub App installation; no
      long-lived App private key, installation token, or status credential is available to
      repository or candidate workflow code.
- [ ] The App has Metadata read, Actions read, Contents read, Pull requests read, and Commit
      statuses read/write for the one repository. It has no Checks, Workflows, administration,
      Issues, Deployments, or Contents write permission.
- [ ] The external controller admits only an allowlisted workflow blob digest read from the
      trusted base; repository or candidate workflow changes cannot select publisher code.
- [ ] Durable replay state rejects a reused OIDC identity, run, attempt, job set, artifact, or
      completion record even after process restart.
- [ ] Publication binds the exact workflow run and attempt, expected and observed jobs, artifact
      digest, and controlled-completion record, then re-queries the current pull request and
      synthetic merge identity immediately before posting status.
- [ ] Branch protection requires the exact status from the dedicated App source, requires
      current pull requests, and permits no direct push, force push, deletion, or bypass.
- [ ] Same-repository source-branch, fork, other-branch, and merge-queue behavior is explicit;
      unsupported sources fail closed or remain manual rather than reusing another result.
- [ ] Missing OIDC claims, stale identities, failed tests, incomplete stages, replayed receipts,
      wrong App installations, and publisher outages all withhold or fail the hard result.
- [ ] Canaries prove candidate `GITHUB_TOKEN` statuses, candidate workflows, stale merge SHAs,
      and copied completion records cannot satisfy the protected requirement.
- [ ] Provider setup and evidence are documented without turning unobserved repository-local
      JSON into an enforcement claim; the portable core remains provider-neutral.

## Links

- Parent design: task `2026-07-27-configure-test-gates-and-time-budgets`
- Required oracle task: `2026-07-27-control-external-test-oracle-and-stage-migration`
- Test-gate contract: `handbook/testing-gates.md`
