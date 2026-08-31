# Pin the Unicode data used to protect source bytes

**Description:** Supported Python versions bundle different Unicode data, so a source-integrity predicate needs an explicit version and behavioral controls for newer assignments
**Area:** automation
**Last-confirmed:** 2026-08-31
**Review-by:** 2027-02-27

## Failure

During the open-PR recovery, a raw U+13439 Egyptian format control and its complete numeric entity could be changed in retry diagnosis or mutable human-item metadata on Python 3.9, while Python 3.14 refused the same edit. Both full suites had passed before independent review added those cases. Visible neighboring characters needed to remain editable.

## Root cause

The new source-byte predicate asked the interpreter's `unicodedata` database whether a character had category `Cf`. Python 3.9.6 bundles Unicode 13; Python 3.14.6 bundles Unicode 16. A character assigned after the older database appears unassigned there, even though both interpreters execute the same repository code. Testing both interpreters alone did not expose this without inputs whose assignments differed.

## Rule

When a source-integrity boundary depends on Unicode membership, declare the data version and test version-sensitive characters through the real Git mutation path. Check both forbidden bytes and visible neighboring controls. The lower recovery uses the complete Unicode 16 `Cf` ranges for its new Boolean predicate, leaving the older prose normalizer unchanged; its tests cover raw and entity spellings on both supported interpreters. Future data assignments need a deliberate update and the same positive and negative checks.

The predicate's membership and exhaustive independent comparison are recorded with the recovery task `2026-08-30-rebuild-the-open-pr-stack`. This lesson does not claim that every general-purpose Unicode operation should use a frozen table.
