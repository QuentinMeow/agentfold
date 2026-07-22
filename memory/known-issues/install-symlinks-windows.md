# install.py symlinks fail on Windows without developer mode

**Status:** open
**Severity:** low — affects setup on one platform, workaround exists
**Description:** Agent-adapter symlinks need Windows developer mode or admin; otherwise install.py falls back with a warning
**Review-by:** 2027-01-22

## Symptom

On Windows, `python3 automation/install.py` may raise `OSError: symbolic link
privilege not held` when creating `.claude/skills/` links.

## Impact

Agent-specific skill discovery dirs aren't created; everything reading `AGENTS.md`
directly still works.

## Workaround

Enable Windows developer mode (Settings → For developers), or run in WSL.

## Suggested fix

Teach `install.py` to fall back to directory junctions / copies with a drift note on
Windows. Small, self-contained; good first task for a contributor.
