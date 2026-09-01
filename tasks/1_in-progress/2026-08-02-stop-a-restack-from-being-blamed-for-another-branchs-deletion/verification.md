# Verification — Stop a restack from being blamed for another branch's deletion

**Verified:** 2026-09-01 by codex

Only commands actually run and their real output are recorded here. Design reviews name
their immutable revision and remain explicitly superseded when a later correction exists.

## Superseded five-lens design review

**Reviewed revision:** `09b9e08cfbe127ebdb886a5a4438c0ba3391e1ce`

- semantic/DAG / r17-final-semantic-verifier: `block` — the design omitted the POC's old-side graph and did not project persisted proof failures to Findings.
- workflow/adapter/human / r17-production-seam-audit: `block` — normal synthetic PR checkouts, deletion, fork-conflict coverage, transport security, standalone CLI use, and the repair push were underspecified or contradictory.
- budgets/transaction/composition / r16-composition-verifier: `block` — retained results, imported authority, the pre-parse snapshot, and several measured work families had no exact pre-work limits.
- core-fit/substitution / receipt-blast: `approve` — immutable Git inputs, repository authority, no global writes, and the optional policy-free adapter satisfy core admission.
- CLI/contracts/testability / integration-receipt: `block` — standalone and duplicate argument shapes, writer checkout binding, retired-option tests, and executable live canaries were not closed.

The four-to-one panel rejected the revision. No production implementation began from it.

## Superseded corrected-design review

**Reviewed revision:** `30c9cc0f9a71a3ae5f82cefb7928a818c383f421`

- semantic/DAG / r18-semantic-design: `block` — the graph command omitted `--ancestry-path`, reopened neutral outside ancestry, and could spend the intrinsic budget on irrelevant history.
- budgets/transaction/composition / receipt-contract: `block` — outside ancestry, arbitrary historical checker dispatch, and stalled children remained unbounded.
- workflow/adapter/human / r18-workflow-design: `block` — the trusted lane lacked a separate historical entrypoint, coverage could be laundered, required-check and evaluator binding claims were unsound, and canary/push lifecycle identities were incomplete.

The panel stopped after three independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.

## Superseded edge-scoped design review

**Reviewed revision:** `db720d3321ee25f09c82def46d77fd418735e904`

- semantic/DAG / r18-semantic-design: `approve` — fresh fixtures matched the accepted POC and its complete 167/167 scenario, 34/34 damage-control, and 4/4 alias suite.
- budgets/transaction/composition / receipt-contract: `block` — integrated candidate code and the pinned trusted evaluator did not bind one authority-policy version.
- workflow/adapter/human / r18-workflow-design: `block` — default-branch workflow authority, a closed PR matrix, fixture installation, cleanup authentication, bounded run discovery, and the concrete manual lifecycle remained incomplete.

The panel stopped after two independent blocks. The two remaining lenses were not run,
and no production implementation began from this revision.
