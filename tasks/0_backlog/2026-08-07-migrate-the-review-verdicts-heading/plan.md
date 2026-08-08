# Plan — migrate the Review verdicts heading

- [ ] 1. List every tracked record carrying the old spelling; confirm the count is still 19.
- [ ] 2. Rename in the 18 that carry only the old spelling.
- [ ] 3. Handle the review-receipt task's own record by deleting its parenthesized section,
       so it keeps exactly one exact heading.
- [ ] 4. Parse every changed record with `review_receipt.parse_review_receipt` and confirm
       none reports a heading problem it did not report before.
- [ ] 5. Run the full suite and the reconciler; record real output in verification.md.
