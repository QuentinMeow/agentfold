# Example services are Python-stdlib-only, on purpose

**Description:** services/ examples must never gain dependencies — they exist to demo the harness, not to be good software
**Source:** bootstrap task `2026-07-22-bootstrap-the-harness` (design.md)
**Review-by:** 2026-10-22

The `services/quote-api` and `services/quote-cli` examples are deliberately trivial and
dependency-free so that `python3 -m pytest services/` works on any machine and the code
never distracts from the harness. Improving them into "real" software is
scope creep — reject such tasks unless the owner asks.
