# Design notes — machine-specific paths in the link check

**Status:** decided

## Problem

The link check treats any backticked whitespace-free token containing a slash as a claim
that the repository contains that path. When the candidate resolves outside the
repository, `relative_to` raises and the check answers the existence question by probing
the filesystem it happens to be running on. That probe is the only part of the check
whose verdict depends on the machine rather than on the repository.

The consequence is a gate that disagrees with itself across machines. A record naming a
real local binary passes for its author and fails on the Linux runner, and the author
learns about it only from a red push. This shape broke CI twice in two days.

## Options considered

### Option A — Decide the absolute case before resolving, and report it
An absolute path cannot name a repository artifact, so the existence question is not
worth asking. Report it as machine-specific and name unquoting as the fix.

### Option B — Keep probing, but only for paths that exist on every supported platform
Requires a maintained list of universally present paths, which is a second thing to keep
correct forever and still guesses about platforms nobody has tested.

### Option C — Drop the outside-the-repository probe and treat those candidates as valid
Silently accepts every absolute path, including genuine typos in repository links that
happen to begin with a slash.

## Chosen

Option A. It removes a machine dependency rather than papering over it, needs no list,
and turns a class of failure that could only be discovered after pushing into one the
local gate reports on the commit that introduces it.

The finding names unquoting rather than deletion, because prose about a real binary is
legitimate content. Only the backticks are wrong: they assert a repository path, and that
assertion is what the check is entitled to test.

Surveyed before changing behaviour: three distinct absolute paths appear in five live
records. All three exist on both platforms, so all five pass today by luck rather than by
construction. They are unquoted in the same change.

## Core fit

**Agent substitution:** pass — the check reads repository markdown and reports findings; no behaviour depends on which agent runtime wrote the record
**Provider substitution:** not-applicable — nothing here reads or writes any external provider
**Repository substitution:** pass — any adopted repository whose contributors use different machines gets the same verdict from the same contents, which is the property the check was missing
**User-global writes:** none
**Why AgentFold core:** A repository invariant whose answer changes with the host filesystem is not an invariant, and the reconciler is the referee that every adopter relies on for a machine-independent verdict
**Thin adapter:** none
