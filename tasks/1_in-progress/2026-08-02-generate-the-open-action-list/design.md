# Design notes — generate one ordered list of every open action

**Status:** decided

## Problem

The repository already guarantees that every pending human action and every durable
cross-session agent action has exactly one file, and that its filename says when unresolved
work stops. Two things are still missing for the person who has to act on them.

The first is aggregation. Nothing shows all open actions together. The owner's only view is
the "Needs your attention" block an agent writes at the end of a session reply, which is
correct but ephemeral — it exists in a chat log, is rebuilt by hand every time, and is
absent between sessions. Fifty-five live items across two actor folders and five leaves
cannot be held in a head.

The second is ordering. The queue encodes urgency in filename prefixes and dates, but a
directory listing sorts alphabetically, so `future-blocking-` sorts before `non-blocking-`
by accident rather than by meaning, and `blocking-` items would be scattered among them.

Three constraints shape every option below.

- **The digest may not become a second source of truth.** `handbook/principles/single-source-of-truth.md`
  is a hard invariant, and a hand-maintained summary of files that change every session is
  the textbook way to violate it.
- **It must be readable without running anything.** The owner reads on a phone, on GitHub,
  between sessions. An artifact that only exists after a command is an artifact they will
  not have when they want it.
- **A calendar date cannot be allowed to fail it.** The reconciler's advisory tier exists
  because age-driven checks would otherwise make an unchanged clean tree start failing when a
  day passes (`automation/AGENTS.md`). Any generated content derived from today's date
  inherits that defect.

## What the practice outside this repository says

Two bodies of practice bear on this, and they agree with each other.

**Generated artifacts are committed, and a check proves they are current.** The pattern is
routine in build tooling: run the generator, then `git diff --exit-code`, and fail the build
if the tracked output moved. It exists to stop a reader from trusting a file that no longer
matches its inputs, which is precisely the failure a hand-written digest of a live queue
would have. The counter-argument in that literature — don't commit generated files, let CI
build them — assumes the artifact's only consumer is a build. Here the consumer is a person
who will not run a build, so the argument does not reach this case.

**A summary view leads with a status answer, then discloses depth on demand.** The
dashboard-design literature is consistent that the top of the view is a status answer, that
the most important item goes first, and that details belong behind an expansion rather than
on the initial screen. Its warning is equally consistent: the common failure is metric
overload and missing context — a wall of numbers nobody can act on. That maps directly onto
this repository's own `handbook/principles/progressive-disclosure.md`, which already says
"Repeat the ask ... one line each, with links" and "Always link the source." So the digest is
not a new idea here; it is the existing principle given a durable home instead of a
per-reply one.

## Options considered

### Where it lives

**Option A — `message-queue/open-actions.md`.** The digest sits beside the items it summarizes, so a
reader who opens the queue folder finds the map before the territory. Cost: `message-queue/`
has a strict three-axis structure and a check that every file under it is an action item, so
the file has to be registered as a queue root document, next to `AGENTS.md`.

**Option B — a file at the repository root.** Maximum discoverability; GitHub shows root
files first. Cost: the root is the landing page for the whole repository, and a churning
generated file there competes with `README.md` for the first thing a stranger reads, while
saying nothing about the product. It also separates the digest from its inputs, so the
single-source relationship stops being visible from either side.

**Option C — untracked, under `tmp/`.** Zero merge conflicts and zero staleness risk,
because nothing is stored. Cost: it fails the constraint that made this task worth doing —
the owner cannot read it without a checkout and a command.

*Chosen: A.* It satisfies discoverability and keeps the projection adjacent to its source.
The registration cost is one entry in `QUEUE_ROOT_DOCUMENT_PATHS`, which is the same
mechanism that already exempts `message-queue/AGENTS.md`.

### What generates it

**Option A — a new mode on the reconciler: `--fix-open-actions`, checked by a `open-actions` entry in
`CHECKS`.** `automation/AGENTS.md` states the rule directly: a new repository-state
invariant is a `CHECKS` entry plus the rule where agents read it. "The digest matches the
queue" is exactly such an invariant. The reconciler already reads and parses every queue
item for six other checks, so the parsing is free, and `memory/index.md` proves the shape
end to end — `--fix-index` writes it, `check_memory_index` refuses a commit when it drifts.

**Option B — a standalone generator of its own under `automation/`.** Keeps `reconcile.py` from growing. Cost:
a second program that reads the same files with a second copy of the queue-field parser, a
second thing to remember to run, and no commit-time enforcement unless the hook learns about
it too — at which point it is the reconciler with extra steps. The repository reserves
standalone gates for *external artifact* boundaries (pull-request bodies, provider state);
this is repository state.

**Option C — an agent writes and updates it by hand.** Cost: it is the single-source
violation stated in the problem, and it decays the first time a session ends early.

*Chosen: A.*

### Whether the content may depend on the date

**Option A — render dates as the item wrote them.** A bullet shows `answer by 2026-10-31`
and nothing more.

**Option B — render computed urgency: "overdue", "due in 9 days", a sorted-by-lateness
list.** More useful at a glance. Cost that disqualifies it: the tracked bytes would then be
a function of today, so a clean tree that nobody touched would start failing the check the
morning a deadline passed, and every commit for the rest of that day would carry an
unrelated digest diff. That is the exact defect the advisory tier exists to prevent, and
here it would arrive in a blocking check.

*Chosen: A.* Lateness is already reported, correctly and advisorily, by the existing
`stale-queue` check. The digest states the date; the reconciler states whether it has
passed. Neither restates the other.

### How the explanation folds

**Option A — one `<details>` per item, nested under its bullet.** Each item shows one
sentence by default and expands to its own consequence lines. Chosen. GitHub renders a
`<details>` block inside a list item when it is indented to the item's content column and a
blank line follows `<summary>`; `templates/pull-request.md` already relies on the same
element, so the convention is not new here. Verified by rendering the real file through
GitHub's own Markdown API rather than by assumption.

**Option B — one `<details>` per section, holding every explanation together.** Fewer
elements, but the reader loses the correspondence between a bullet and its expansion, which
is the whole point of the fold.

### Whether repeated actions are listed individually

Thirty-two of the forty agent-side items are task pickups whose `**Action:**` is the same
sentence with a different task name. Listing them one per line would push the owner's own
questions off the first screen — the "metric overload" failure the dashboard literature
names. They collapse into one counted line that links the folder. Every other agent item is
listed individually, because each says something different.

## Chosen

`message-queue/open-actions.md`, generated by `reconcile.py --fix-open-actions`, enforced by a blocking
`open-actions` check, containing only facts the queue files already carry, ordered
deterministically, with per-item folds and collapsed pickups.

The file opens by saying it is generated and that answers go in the linked item, never here.
That sentence is load-bearing: it is what keeps a convenient summary from quietly becoming
the place people write things down.

## Core fit

**Agent substitution:** pass — the generator is stdlib Python over Markdown files in the
repository. No agent runtime participates in producing or checking it, and any runtime that
can run `python3` regenerates identical bytes from an identical tree.

**Provider substitution:** not-applicable — nothing here reads or writes a provider. The
inputs are tracked files; the output is a tracked file.

**Repository substitution:** pass — an adopted repository with a `message-queue/` gets the
same digest with no configuration, and the check no-ops when the folder is absent, which is
the rule every reconciler check already follows so adopters can take pieces.

**User-global writes:** none

**Why AgentFold core:** the queue is a core mechanism, and this is the queue's own stated
principle — surface every unanswered ask, one line each, with links — moved from a surface
an agent has to remember to write into a file a system produces. It names no agent runtime,
no provider, and no person, and it holds no preference an adopter would have to strip.

**Thin adapter:** none
