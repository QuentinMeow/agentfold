# Give execution, cleanup, validation, and terminal delivery separate deadlines

**Description:** A single end-of-run reserve is not a deadline when cleanup, validation, filing, or a blocking control write can consume it
**Area:** automation
**Last-confirmed:** 2026-07-28
**Review-by:** 2027-01-24

## Failure

The routine gate stopped selected execution half a second before its maximum but allowed process
cleanup to continue until the absolute deadline. It then had no time to freeze and send its
terminal claim, so the supervisor returned a static blocked result after 60.26752 seconds. A first
repair still left final validation, timing-task filing, and the terminal socket write unbounded.

## Root cause

The implementation treated leftover time as one shared reserve instead of assigning independent
cutoffs to every operation required before the immutable decision reaches the supervisor.

## Rule

Derive separate absolute cutoffs for component execution, process cleanup, final identity
validation, and terminal delivery. Bound potentially blocking validation in a killable helper,
send the immutable claim through a nonblocking deadline-aware channel, and perform best-effort
filing and projection only after the claim. Unknown stability blocks and cannot publish receipt
identity. Test socket backpressure, exact-boundary arrival, slow filing, and both critical and
reversible timeout behavior.
