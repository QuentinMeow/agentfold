# Conversation timestamps are local time plus timezone abbreviation

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** human (owner, in chat — transcribed here; chat leaves no trace)
**Description:** history/conversations/ folders use YYYY-MM-DD-HHMM<TZ>-<slug> — wall-clock time a human recognizes, zone made explicit
**Review-by:** 2027-01-22

## Context

The bootstrap session stamped a conversation folder `…-1500-…` with no timezone. The
owner asked what 1500 meant — exactly the ambiguity a naming convention exists to
prevent: a bare HHMM forces every reader to guess the zone.

## Decision

Session-start timestamps in conversation folder names are **local time + timezone
abbreviation**: `2026-07-22-0014PDT-bootstrap-the-harness`. Zones without a letter
abbreviation use `UTC`. Enforced by the reconciler's conversation-name pattern.

## Alternatives considered

- **UTC everywhere** — unambiguous and globally sortable, but nobody remembers their
  sessions in UTC; readability for the repo's human loses.
- **Numeric offset** (`1500-0700`) — unambiguous but reads as more digits; worse at a
  glance than `1500PDT`.
- **No time, date only** — collides when two sessions share a day and a topic.

## Consequences

Sorting across timezones is only approximate (acceptable: one repo's sessions rarely
hop zones); DST makes abbreviations shift (PDT/PST) — fine, since the stamp records
what the wall clock said, which is the point.
