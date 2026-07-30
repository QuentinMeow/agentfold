# Worklog — pinning the admission candidate to the event

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — fast-local-test-feedback continuation (claude)

- Claimed while clearing the red checks that fired on pull requests 20, 21 and 22.
- The premise recorded when this task was filed held up, and one detail sharpened it: on
  the same `opened` event, the `pull_request` run resolved the merge revision correctly
  while the `pull_request_target` run saw an empty payload field. GitHub had computed the
  merge; only that payload field lagged.
- The comparison being repaired was not trusted-against-untrusted. Both sides came from
  GitHub and were equally authentic. It was a temporal pin: proof that the mutable merge
  ref had not moved since the event fired. Reading it as a trust comparison is what makes
  the naive repair look acceptable, and that repair drops the pin on the one event the
  pin exists for.
- The replacement pins through the merge commit's own parents, which its object id
  already covers, so a candidate whose second parent is this event's head cannot be a
  merge of any other head.
- One relaxation is deliberate and recorded in the design: the base side is now required
  to be contained in the merge's first parent rather than equal to the base tip, because
  exact equality reproduces the same red-on-arrival failure whenever main advances.
