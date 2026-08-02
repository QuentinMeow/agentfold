# reviews/ — your judgment

Named judgments over a diff, artifact, claim, or proposed boundary. Reviews are not
implicitly optional: the filename declares the review's delivery timing, and
`message-queue/AGENTS.md` owns what each prefix means. Each item explains possible
dispositions, shows a concrete difference, links the full source, and states what
happens without review.
The target and immutable revision are separate from explanatory context. Use
`Status: awaiting-artifact` plus pending target/revision until the artifact exists.
A local file or HTTPS artifact binds to its SHA-256; a commit or diff repeats its full
Git object id(s) as the revision.
The folding agent copies that value into `Reviewed revision` on its claim, so a stale
response cannot be folded after the target changes — you only fill
`**Your review:**` (`handbook/human-action-guide.md`).
`Resolution evidence` is a different non-queue file
that records crossing or cancellation; it never doubles as the reviewed target.

File one with a timing-prefixed name by copying `templates/queue/review.md`; answer
after `**Your review:**`.
