# A new check and its first violation can arrive on separate green branches

**Description:** Independent stack legs are only ever tested apart, so a check on one and violating text on the other produce a failure that existed on neither
**Area:** automation
**Last-confirmed:** 2026-07-30
**Review-by:** 2027-01-30

## Failure

Five pull requests merged, each green on its own head, and main went red immediately. One
leg had taught `link-check` that a backticked absolute path names a machine rather than a
repository artifact. Another leg, not descended from it, had written such a path in prose.
The finding existed on no branch: the rule and its violation met for the first time in the
merge commit.

## Root cause

Branch protection was absent and no merge queue was configured, so every gate ran against
a branch head and nothing ever ran against the merged result. Stacked work makes this
routine rather than rare: legs that share a base but not each other are guaranteed to be
tested only apart, and a check added on one leg cannot see text added on another.

Sequencing does not help. The violating prose was written before the rule existed, so no
ordering of the two branches would have caught it.

## Rule

Treat a pull request's green as evidence about that branch, not about main. When a change
adds a check rather than only satisfying one, expect the first violations to arrive from
work already in flight, and grep the whole tree — not the diff — for what the new rule
would now reject. Where the repository can carry the cost, a merge queue that tests the
merged result is the mechanism that removes the class; until then, whoever merges a stack
owns re-running the gates on main afterwards and repairing forward.

The repair itself is ordinary: fix the text on main in a records-only commit rather than
weakening the check that correctly fired.
