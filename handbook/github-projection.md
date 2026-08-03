# GitHub projection

What a GitHub adapter forces into `message-queue/` from the provider side, and how far
that assurance actually reaches. `handbook/git-workflow.md` owns the two write lanes, the
pull-request body, and merging, including what the `What to review` check requires of a
candidate; this file owns only the inbound side. Neither restates the other.

## What a GitHub adapter forces into the queue

- Every open GitHub issue is a structurally forced, content-versioned external source;
  neither English phrasing nor `No queued action requested.` can suppress it. The issue
  body may project a canonical link directly, or an agent may transcribe its prose.
  In both cases at least one actor-correct item carries the exact `External source`;
  a presentation link never replaces the durable binding. Each path selects
  `needs-human/` or `needs-agent/`; an informational issue may select a non-blocking
  triage item. Assignment adapters map GitHub `User` accounts and teams to `needs-human`, map
  `Bot` accounts to `needs-agent`, and fail closed on unknown account types or missing
  identities. Every non-empty conversation comment on an issue or PR is structural
  `needs-agent` triage, regardless of author or wording. Comment edits version identity;
  deletion or artifact closure ends it. Open issues replay on issue and non-PR comment
  events, while open-PR comments replay on candidate updates. These inbound sources are
  unscoped: they carry only their own action and cannot stand in for a task's complete
  set. Removing a source's final live binding is a separate exact-tree admission check:
  a trusted provider adapter must classify that exact version as released; current or
  unavailable state fails closed. GitHub resolves global node IDs from trusted base
  code and replays review/thread state as needed. This required check prevents a
  candidate-local deletion from waiting for a later comment event to rediscover the
  orphan. Direct pushes can land before their post-push result, so hard enforcement also
  requires rules that admit changes only through the protected required check. Current
  formal reviews and unresolved diff threads also enforce `needs-agent/`.
  Every non-empty effective formal review creates an agent-triage source instead of
  asking a prose heuristic whether the human meant work; its queue item may be
  non-blocking. `CHANGES_REQUESTED` is forced even with an empty body, directly from
  either review connection; unresolved threads remain forced when current state replays.
  Provider-authored prose may project canonical links directly; every active source
  still has one or more live items with the adapter's exact versioned `External source`
  binding. Editing the source creates a new identity. A bound item
  stays live until the effective review is superseded/dismissed or the thread resolves.
  `pull_request_target`, issue, and issue-comment checks run trusted default/base
  workflow code. Candidate and target jobs replay current review/conversation state on
  supported PR/review events, including merge-queue enqueue, so a later push cannot
  clear an unqueued request. GitHub emits no Actions event for thread resolve/unresolve:
  hard assurance that a currently unresolved thread cannot merge requires native
  “Require conversation resolution before merging”; without it, the ceiling is “state
  projected at the last supported event.” Neither mechanism proves every transient
  reopen-then-resolve toggle was queued. Direct review events also lack a target-context
  variant, so a separately controlled provider gate remains necessary against hostile
  workflow tampering. The workflow uses only its token, never a local CLI login.
