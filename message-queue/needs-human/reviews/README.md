# reviews/ — your judgment

Named judgments over a diff, artifact, claim, or proposed boundary. Reviews are not
implicitly optional: the filename declares whether review blocks now, blocks at a
future boundary, or never blocks. Each item explains possible dispositions, shows a
concrete difference, links the full source, and states what happens without review.
The target and immutable revision are separate from explanatory context. Use
`Status: awaiting-artifact` plus pending target/revision until the artifact exists.
A local file binds to its SHA-256; a commit or diff binds to full Git object id(s).
The answer copies that value into `Reviewed revision`, so a stale response cannot be
folded after the target changes.

File one with a timing-prefixed name by copying `templates/queue/review.md`; answer
after `**Your review:**`.
