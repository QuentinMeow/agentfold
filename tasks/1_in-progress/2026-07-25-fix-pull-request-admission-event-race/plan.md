# Plan — pinning the admission candidate to the event

- [x] 1. Establish what the equality against the payload's merge revision was actually
      protecting, rather than assuming it compared a trusted value against an untrusted one.
- [x] 2. Choose a binding that is knowable on the first event and still refuses a
      candidate belonging to a different head.
- [x] 3. Rebind both admission jobs to it, and correct the second job's fallback, which
      named the base tip on the event where the base tip is not the candidate.
- [x] 4. Cover the admission and every rejection with executable tests that run the
      workflow's own shell, not a paraphrase of it.
- [ ] 5. Record real workflow runs on a pull request opened from this branch, since the
      failure only reproduces against a live event payload.
