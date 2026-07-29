# Look up stronger cached evidence before narrowing the requested test set

**Description:** An exact complete-test receipt can satisfy a smaller routine test request only when lookup happens before narrow component identity hides it
**Area:** automation
**Last-confirmed:** 2026-07-28
**Review-by:** 2027-01-24

## Failure

An explicit final gate passed the complete suite and published a valid receipt for the exact
staged candidate. The following routine hook classified the same candidate as reversible,
constructed a selected-test component, ignored the stronger full receipt, and started slow tests
until the 60-second decision deadline expired.

## Root cause

Cache lookup was keyed from the narrower routine component after risk classification. The valid
complete receipt used a different component and manifest identity, so the lookup rejected it
without reading the evidence set.

## Rule

Before starting narrower routine tests, use one bounded fixed pointer to find complete evidence,
then validate its receipt, report, marker, candidate, policy, execution environment, full test
manifest, and composite plan exactly. A complete proof may cover its exact subset; a selected
proof must never be promoted to complete evidence. Any mismatch falls back to ordinary planning.
