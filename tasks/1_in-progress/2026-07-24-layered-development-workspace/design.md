# Design notes — layered development workspace

**Status:** exploring

## Problem

A normal AgentFold workspace may contain public project files, private team or personal
customizations, sensitive material, disposable outputs, and durable local raw data.
Putting these in separate directories makes origin obvious but makes same-path
customization and instruction review awkward. Overlaying them naively improves browsing
but can silently hide upstream changes, confuse Git ownership, or leak private content
into a public repository.

The design must optimize both human and agent development UX while keeping publication
and authority boundaries honest.

## Options considered

### Option A — nested private repository and symlinked customizations

Keep the public repository at the workspace root and an ignored private repository
under `private/` or `customized/`, with links for convenient navigation. Setup is
simple, but ignores are bypassable, nested repositories can become gitlinks, links do
not merge same-path content, and private metadata can still leak. This is a convenience
layout, not a confidentiality or conflict-resolution boundary.

### Option B — sibling repositories with a manifested materialized view

Keep public and private repositories physically separate, plus external raw and
temporary roots. Generate a read-only or carefully synchronized logical view with
per-path provenance and base digests. This gives the strongest explicit separation and
can treat stale overrides as conflicts, but editing, rename/delete routing, regeneration,
watchers, and source-control UX require significant custom machinery.

### Option C — private integration history with a sealed public publisher

Use one ordinary private integration checkout whose history contains the admitted
public base plus private commits. Same-path customizations, search, editors, tests,
three-way merges, blame, and review all work natively. Publish public changes only
through a physically separate clean clone/object store that receives sanitized content
or patches, never by pushing the private integration branch. This has the best everyday
UX, but requires strict destination identity and a semantic instruction-admission gate
because Git can auto-merge authoritative changes without a textual conflict.

### Option D — resolver-native layering

Teach AgentFold-aware tools to merge public and private configuration by schema while
editors use a multi-root workspace. This is excellent for structured configuration and
explicit authority, but generic shell tools, language servers, and runtimes that
discover files such as `AGENTS.md` do not see one effective tree.

### Option E — private patch stack or union filesystem

A patch series is portable and delta-only but makes bidirectional editing, binaries,
renames, and team collaboration cumbersome. A union mount gives a compelling filesystem
illusion, but upper-layer shadowing is not conflict resolution, Git ownership is
ambiguous, and portable macOS/Linux behavior becomes provider-specific.

## Provisional direction

Carry Option C forward as the everyday versioned-content model, inside a non-Git
workspace envelope with physically separate restricted/raw/temp sibling roots. Add the
provenance manifest and status-board ideas from Option B, use resolver-native merging
only for schemas that declare it, and use a physically separate clean public publisher.
This is a research hypothesis, not an accepted one-way-door decision.

The effective-instruction algorithm must apply provenance before position. Hard safety
constraints compose monotonically; a private customization cannot weaken the public
safety floor. A trusted narrower source may specialize only declared overridable keys.
Every other trusted conflict blocks admission and shows both sources. A clean textual
merge is not semantic authorization, and unavailable private state must never silently
expose a public fallback.

## Core fit

**Agent substitution:** pass — the model classifies workspace state and authority independently of agent runtime
**Provider substitution:** pass — local layout and publication rules do not depend on GitHub or one remote provider
**Repository substitution:** pass — any adopted public/private project faces the same local composition and leak problem
**User-global writes:** none
**Why AgentFold core:** folder-as-a-service, instruction provenance, queue interaction, and safe autonomous publication are harness-wide concerns
**Thin adapter:** none; platform-specific mounts or sandboxes, if ever added, remain optional adapters

## Research anchors

- Git ignores are tracking hints, not access controls:
  https://git-scm.com/docs/gitignore
- Worktrees share one repository and most refs:
  https://git-scm.com/docs/git-worktree
- Git merge supplies native three-way conflict behavior:
  https://git-scm.com/docs/git-merge
- Separate fetch and push destinations:
  https://git-scm.com/docs/git-config
- VS Code multi-root navigation and search:
  https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces
- OverlayFS shadowing and copy-up semantics:
  https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html
- Sensitive-data history-removal limitations:
  https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- PII detection is incomplete by design:
  https://microsoft.github.io/presidio/
