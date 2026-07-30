# Flag a backticked absolute path instead of resolving it against the host filesystem

**Claimed-by:** unclaimed
**Filed:** 2026-07-30, by claude, from the second CI failure of this shape in two days
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-flag-machine-specific-paths-in-link-check.md`

## Goal

The link check resolves any backticked whitespace-free token containing a slash as a
repository path. When that path lies outside the repository, `relative_to` raises and the
check falls back to probing the host filesystem, so the result depends on the machine
running it rather than on the repository contents.

An absolute path in prose therefore passes on the machine that wrote it and fails on the
Linux runner. This has now broken CI twice: once on a wrapper-removal record naming the
Git binary's install path, and once on a maintenance record naming two Git binaries. Both
times the record was accurate, the local gate was green, and the failure appeared only
after the push.

A backticked absolute path cannot be a repository link, so probing for it answers a
question the check is not asking. Flagging it directly makes the outcome identical on
every machine and moves the failure to the commit that introduces it.

## Acceptance criteria

- [ ] WHEN a backticked candidate is an absolute path, THE SYSTEM SHALL report it as
      machine-specific rather than probing the filesystem for it.
- [ ] The finding SHALL name unquoting as the fix, since prose about a real binary is
      legitimate content and only its backticks are wrong.
- [ ] THE SYSTEM SHALL produce the same verdict for the same repository contents on macOS
      and on Linux, verified by a test that does not depend on which paths exist locally.
- [ ] Existing records that legitimately name absolute paths SHALL be surveyed, and the
      count reported, so the change does not silently invalidate history.

## Links

- `automation/reconcile/reconcile.py`
