# Design notes — migrate the Review verdicts heading

**Status:** proposed

## Problem

A mechanical `sed` over all nineteen files is the obvious move and is wrong for one of
them. Everything else about the change is uniform.

## Chosen

Rename in every file except the review-receipt task's own verification record, which
already carries both spellings; there, delete the parenthesized section (it records that
no review was run against the heading-boundary repair) rather than renaming it, so the one
exact heading stays unique. Verify by parsing each record afterwards rather than by
trusting the rename.

## Core fit

Not applicable: `**Repository scope:** records-only`.
