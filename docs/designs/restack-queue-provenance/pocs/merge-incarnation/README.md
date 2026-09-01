# Merge-incarnation supplier-witness POC

This isolated proof of concept attacks the proposed candidate-side supplier witness
before any production reconciler code changes. It constructs real disposable Git DAGs
using only the Python standard library and the installed Git executable.

## Milestone-one question

Can exactly one concrete candidate-side deletion edge, validated against a committed
claim and changed non-queue evidence, distinguish a legitimate inherited resolution
from an invalid deletion and an old-tip-authored loss when merges and action identity
are involved?

The prototype deliberately fails closed when it sees zero or multiple causal deletion
witnesses. A merge result's synthetic parent edge is ignored only when a sibling
contains a prior validated deletion edge in its own ancestry. This is a hypothesis
under attack, not repository authority.

Run:

```sh
python3 docs/designs/restack-queue-provenance/pocs/merge-incarnation/prototype.py --self-test
```

The first executable milestone covers S1, S2, S3, S6, an unambiguous rename carry,
S12's merge-shaped base, a merge-commit-only deletion, and competing valid/invalid
supplier edges. The full common matrix, missing-history cases, repeated
incarnations, and the long-history cost probe are the next milestone.
