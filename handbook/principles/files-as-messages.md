# Files as messages

Agents and humans in this repo rarely share a live conversation. All coordination —
questions, decisions, work requests, repair jobs, reviews, handovers — is written as
files in `message-queue/` and `history/`, one file per message. Ant colonies coordinate
the same way (stigmergy): leave traces in the shared environment; whoever comes next
acts on the traces they find.

## Rules

- **One item, one file.** Never a shared list file that concurrent writers edit — two
  agents appending to one file conflict; two agents each creating their own file never do.
- **Self-contained items.** Every message is written so the reader can act from that
  file alone — no chat-history archaeology. Assume the reader has read the root
  `AGENTS.md` and nothing else.
- **Chat is a lossy channel.** Anything said in chat that matters later is written to a
  file in the same turn — an answer from the human, a discovered constraint, a promise.
- **Resolved means deleted.** A processed message is deleted in the same commit that
  resolves it; git history is the archive. Queues hold only live items, so a full queue
  is a real to-do list, not a landfill.
- **Consumers act, producers describe.** The writer of a message never assumes when it
  will be read; the reader never needs to ask the writer what it meant.

## Why

Files survive context compaction, session restarts, agent switches (Claude Code today,
Cursor tomorrow), and human vacations. They are greppable, diffable, reviewable, and
versioned. A message bus you can `cat` is one no agent can pretend not to have received
— the reconciler (`../principles/eventual-consistency.md`) checks queues mechanically.
