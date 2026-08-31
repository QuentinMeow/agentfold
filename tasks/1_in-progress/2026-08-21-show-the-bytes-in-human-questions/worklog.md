# Worklog

## 2026-08-21 — claude

Claimed and completed in one session, stacked on `task/2026-08-18-fold-the-queue-machine-record`
because `templates/queue/*.md` and `automation/reconcile/reconcile.py` already differ from
`main` on that branch.

Measured first. The four rejected items are 241-297 words against an 800 budget — empty,
not cluttered, which inverted the framing the session started with. Across all 17 live
human items: 52 bare backtick paths in the frozen ten, 6 clickable links, and zero
anchor-precise pointers. `check_explanation_shape()` skips 10 of 70 items and those 10 are
exactly the ones the owner rejected.

Five research threads (~45 primary sources) settled the direction and one finding reversed
it: adding reasoning prose is measured to make human decisions worse, so the repair shows
verified bytes instead. Two designs were commissioned from opposing premises and judged;
each contained a load-bearing factual error the other did not, and the judge rejected 10 of
34 proposed mechanisms.

Verified rather than assumed: a wrong anchor in a queue item is silently accepted today,
because `LINK_SKIP_PREFIXES` contains `"../"` and the skip returns before the anchor
comparison. The tempting one-line fix is refused by measurement — 816 `../` destinations
repo-wide, none with a fragment.

Weak-author test: eight Sonnet runs over four scenarios. Kind routing 6/8, both trap
attempts correctly declined to file anything. One predicted failure fired — median words
above the answer line 783 against a predicted 740, failure threshold 760 — and was recorded
without retuning, because train-set signal already misled this project once and no item cut
a choice to fit.

Not done: the eval could not test the quote mechanism end-to-end. Three of four scenarios
name files this repository does not contain, and a grounded replacement turned out to
duplicate a live queue item, which both authors correctly detected and declined. The
mechanism claim rests on the five adversarial probes, which test it directly.

## 2026-08-30 — resume the upper PR during stack recovery

The owner authorized recovery of all useful local and open-PR changes. Codex resumes the inactive claim from 2026-08-21 as sole claimant; the original claim remains in Git history. The task and branch stay in progress. Recovery task `2026-08-30-rebuild-the-open-pr-stack` coordinates the two-layer stack. Existing code, human questions, review-rebinding transitions, and immutable records remain preserved. Reproduced defects in source verification and successor-review boundaries are being repaired before publication. No task was unstarted or started by this continuation.
