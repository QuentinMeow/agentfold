# Design notes — stop link-check false positives

**Status:** decided

## Problem

`check_links` treats any backticked or Markdown-linked, slash-containing token as a
repository path claim. That single rule has to serve two different kinds of text —
real repository paths and ordinary prose that happens to contain a slash — with no
signal to tell them apart, plus two independent, unrelated bugs (an unstripped
indented-code block, an unstripped Markdown-link heading) and one structural gap
(queue actions are deleted by design, but citing one anywhere still asserts it must
exist forever).

## Options considered — bug 1 (prose vs. path)

### Option A — known file extension only
Require a recognized extension (`.md`, `.py`, …) before treating a candidate as a
path. Simple, and it catches both required bug-3 examples (an `httpd`-prefixed and a
`./`-prefixed example, both ending in `.md`) since both end in a recognized
extension. It does not catch a genuinely broken *extensionless* path (e.g. a typo'd top-level directory with no file
extension), which the repository has exactly two real examples of (`LICENSE`,
`automation/hooks/pre-commit`) and neither is ever cited as a two-segment candidate.

### Option B — known file extension OR known top-level entry
Add a second, independent test: the first path segment already names real,
tracked repository content. This is what the audit suggested and what was built.
It keeps option A's coverage and additionally lets an extensionless-but-real
citation (`automation/hooks/pre-commit`, a bare service directory) pass through to
the real existence check instead of being dropped as prose.

## Chosen

Option B. `LINK_PATH_EXTENSIONS` lists extensions actually used in the repository
today (`md`, `py`, `sh`, `txt`, `json`, `yml`) plus a few common ones no current file
uses but a future document plausibly would (`yaml`, `toml`, `cfg`, `ini`, `js`, `ts`,
`html`, `css`). The top-level-entry test mirrors `repo_artifact_bytes`'s own Git-index-
vs-filesystem split (tracked content when `.git` exists, real filesystem otherwise, so
the existing test fixtures that never call `init_git` still work) rather than a second
hardcoded list, so it never drifts from the repository's actual top-level shape. A
first run of this rule against every live Markdown file in the repository turned up
one second-order false positive — `.git/objects`, cited in a verification record — that
demonstrated why "does this exist on disk" is the wrong question for the prefix test
too: `.git` is never tracked content, so the fix narrows the prefix test to Git-tracked
paths, closing the same class of bug for the prefix check that bug 3 closed for the
skip-prefix check.

**Trade-off accepted:** a typo'd, extensionless, unrecognized top-level segment (e.g.
`sevices/quote-service`, misspelling `services`) will now silently read as prose
instead of being reported broken. No such case exists in the repository today (verified
by running the new rule against every live Markdown file with zero unexplained
findings), and the alternative — reporting every slash-containing sentence as broken —
is the defect this task exists to fix.

## Options considered — bug 3 (`./` vs `../`)

The audit's suggested fix anchored both `./` and `../` as skip prefixes. Doing that
literally would still skip the required dot-slash-relative reproduction, so the two
forms needed different treatment:

- **`./` is not skipped.** `pathlib` normalizes a leading `./` away when joined to the
  repository root, so a `./`-prefixed candidate already resolves and checks exactly
  like the same path without the prefix; skipping it serves no purpose and would fail
  the required reproduction. Confirmed no real repository content uses `./`-relative
  notation today (a single, this-task's-own probe file was the only hit).
- **`../` stays skipped.** Read from the repository root — what `check_links`'s
  existence probes actually do — a leading `../` names a path outside the repository.
  `git ls-files -- ../x` fails outright with `fatal: ../x: '../x' is outside
  repository` (verified directly), which would abort the whole reconciler rather than
  report one broken link; a crash is a worse failure mode than one missed check. Real
  repository content also already relies on this being unchecked in both directions:
  several live `../`-relative citations exist (`handbook/principles/folder-as-a-
  service.md`, `roadmap/current-state.md`) that resolve correctly only relative to the
  citing file's own directory, and at least one dead one exists on purpose (a claimed
  pickup request cited from a done task's worklog, the same "moving/resolved path"
  shape as bug 5 but via a relative link instead of a root-relative one).
  Resolving `../` correctly would need doc-relative resolution wired into the
  root-relative existence probe, which no case here currently exercises; left as a
  known, pre-existing limitation rather than introduced as a new false positive.

## Options considered — bug 5 (queue citation exemption)

### Option A — exempt `docs/designs/` entirely
Add `docs/designs` to the folder-level skip list (`LINK_SKIP_DIRS`-style). Simple, but
it stops checking *every* link in every design document, including ordinary citations
of `handbook/`, `automation/`, and `memory/decisions/` paths that should keep being
checked. `docs/designs/queue-resolution-order-independence.md` itself cites several
such paths alongside the one queue action.

### Option B — treat a `message-queue/needs-*/**` citation as history-resolvable,
from any file
Skip only the existence check for that specific path shape, wherever it is cited. A
queue action is deleted by design on resolution (`message-queue/AGENTS.md`), so citing
one is inherently citing history, not asserting a permanent link — the same reasoning
already applied to `memory/decisions/`, `history/`, `templates/`, and
`needs-agent/retries/`, just scoped to the cited path instead of the citing folder.
Every other link in the same document keeps being checked normally.

## Chosen

Option B. It fixes exactly the reported defect (42 live citation edges, per the
audit) without weakening any other link check in `docs/` or elsewhere. Scoped to
`message-queue/needs-human/` and `message-queue/needs-agent/` specifically (the actual
queue-action leaves per `message-queue/AGENTS.md`'s routing table), not the bare
`message-queue/` prefix, so a broken citation of a permanent file such as
`message-queue/AGENTS.md` itself is still caught.

## Core fit

**Agent substitution:** pass — pure Python stdlib logic inside a tracked check; no agent-specific behavior anywhere in the change.
**Provider substitution:** not-applicable — no provider is involved in a link-existence check.
**Repository substitution:** pass — the known-prefix test reads the adopting repository's own tracked top level at run time; nothing is hardcoded to AgentFold's specific folder names.
**User-global writes:** none
**Why AgentFold core:** `check_links` is a tracked repository invariant enforced by the pre-commit hook for every adopter of this harness; a false positive in it blocks every adopter's commits the same way, so the fix belongs in the same core file as the original check.
**Thin adapter:** none
