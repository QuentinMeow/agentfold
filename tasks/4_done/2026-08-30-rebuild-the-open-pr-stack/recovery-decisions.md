# Decisions and discarded approaches in the PR recovery

The exact owner request is in `requirements.md`; source identities and the complete original staged-file inventory are in `recovery-inventory.md`. This record preserves the adjudications that matter after the temporary orchestration worktrees are retired.

| Decision | Chosen result and reason | Rejected alternative or limit |
|---|---|---|
| C1 — history | Preserve both original PR histories through normal merges and repair forward. Task claims and review retraction/publication remain attached to their actual edges. | One reconstructed snapshot loses lifecycle evidence and can give old handovers a new creation context. |
| C2 — local leftovers | Retain original index, unfinished merge metadata, probes and backup refs as recovery data. Their useful implementation is already in current main or the two PR histories. | Old probes omit newer main task moves; copying their whole trees would regress current state. |
| C3 — publication lane | Publish task filing and claims on the recovery branch; main remains unchanged. | Auto-review refused a direct-main coordination push. No alternate route or hook bypass was used. |
| C4 — validation boundaries | Permit exposed retry diagnosis while preserving hidden source and structural identity; preserve a successor review's exact unmet obligation. | Rendered-value equality alone can hide raw-byte edits and cannot prove the source field is exposed. |
| C5 — worker isolation | Use exclusive checkout leases of real task branches in separate worktrees. The parent owns shared records and publication. | Generic worker branch names fail this repository's core-admission task rule. Ownership was not widened to hide inherited paths. |
| C6 — upper replacement | Start a genuine bounded repair task from the current-main lower layer, then merge original PR89 intact. | Updating the old upper branch replays two withdrawn transcript edges already in main. Reversing merge parents gives the same tree but does not repair its displaced-tip range. |
| C7 — usable templates | Move authoring comments into the canonical guide; genuine copied and filled human templates retain the sanctioned fold. | Adding an HTML-comment exception would enlarge the grammar to accommodate instructions that need not appear in the filed question. |
| C8 — raw-source protection | Validate actual source exposure, ordered fold tags, references and complete entity spellings. A narrow first-response comparison preserves every other byte. | Globally masking response text or applying NFKC to decide whether a character is invisible can hide metadata changes or freeze visible prose. |
| C9 — citation consistency | Use one captured lexical source target and physical-line grammar across source and link checks. | Unstaged symlink resolution and Unicode `splitlines()` boundaries can select bytes the candidate never contains. |
| C10 — independent refutations | Pin lower format-control membership to Unicode 16 and preserve quote token/literal boundaries in the upper layer. | Green full suites did not establish these properties; independent counterexamples were converted into failing regression controls. |
| C11 — final quote repair | Protect signed/decimal/exponent spellings and Unicode identifiers; distinguish prose apostrophes from actual string literals on every presentation route. | Treating all apostrophe pairs as strings blocks contractions and can consume the opener of a later real literal, hiding changed literal spaces. This remains a bounded fidelity check, not a language interpreter. |
| C12 — complete literals and ambiguity | Protect an entire triple-quoted literal even when its body contains quotes or apostrophes. State the exact-excerpt fallback for prefix-shaped prose. | Loosening prefix recognition to accept every prose wrapping would admit altered valid raw strings. Exact source spelling remains the safe outcome for ambiguous text. |
| C13 — portable quote boundaries | Recognize the Unicode 16 identifier assignments missing from older supported interpreters, while leaving newer visible symbols as boundaries. Supplement newer decimal digits in the existing number class across the same versions. | Blanket treatment of every unassigned code point as an identifier produces false mismatch advisories near newer emoji. Removing all unknown protection instead would expose newer real identifier characters. |

The lower implementation and its native-review evidence are recorded in `verification.md`. The upper implementation and its own verification are delivered in [PR91](https://github.com/QuentinMeow/agentfold/pull/91), stacked on [PR90](https://github.com/QuentinMeow/agentfold/pull/90). Citation quality remains advisory; lifecycle and source-identity boundaries retain their existing enforcement.

## Unexecuted external review

The execution check refused sending repository review inputs to Claude before process creation. The refusal was respected and no indirect transmission was attempted. `review-limit.md` records the missing cross-vendor verdict and links the sole authorization question. Native reviewers and local/GitHub checks are not presented as a Claude result.

## Retention

The delivered PRs remain open for the owner. The run's cleanup therefore retains any open-PR base or implementation not yet contained in main, using its manifest and backup references. No pre-existing owner branch, worktree, probe, staged byte, or backup is a cleanup target. Reopening the original PRs remains possible; code repairs can be reverted through ordinary new commits. No force rewrite or product merge to main is part of this delivery.
