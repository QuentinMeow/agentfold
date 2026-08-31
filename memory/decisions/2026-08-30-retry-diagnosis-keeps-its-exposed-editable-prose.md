# Retry diagnosis may change exposed prose without changing the frozen record

**Status:** decided
**Date:** 2026-08-30
**Decided-by:** agent (delegated PR recovery; reversible repair to the existing retry workflow)
**Description:** Exposed diagnostic prose in a retry's Agent notes remains editable while hidden bytes, fields, and structural boundaries stay frozen
**Review-by:** 2027-02-26
**Amends:** `memory/decisions/2026-08-18-the-machine-record-is-folded-and-checked-by-position.md` — the queue-frozen-skeleton clause for exposed retry diagnosis

## Context

The folded-record change protects raw bytes that action identity intentionally omits.
Its first implementation also rejected ordinary diagnostic notes on claimed retries.
That prevented an agent from recording a failed command before repairing the finding,
although the retry template provides an Agent notes section for this purpose.

## Decision

Replace only the earlier decision's frozen-skeleton clause as it applies to exposed
retry diagnosis. A real Agent notes section may change its visible diagnostic prose and
the blank lines separating its paragraphs. A genuinely new final Agent notes section may
be introduced without reclassifying any existing bytes as mutable.

Headings, structured fields, reference definitions, comments, code, raw HTML, invisible
controls, and their protected boundaries remain frozen. The partition still accounts for
every byte; the retry lifecycle and action identity checks continue to apply separately.
All other clauses stand, including the exact sanctioned HTML fold and the prohibition
on rewriting existing human questions. Instructional comments were removed from the
three human templates and relocated to `templates/README.md`; no comment exception was
added to live-human admission.

## Alternatives considered

- Keep every retry-note byte frozen: breaks the template's ordinary diagnosis workflow.
- Exempt the entire notes section: permits hidden or structural changes that the raw-byte
  guard exists to reject.
- Loosen the shared HTML parser: unrelated to retry diagnosis and widens other boundaries.

## Consequences

Manual and generated retries can record diagnosis through their ordinary claim and
resolution transitions. Tests cover legal notes alongside hidden-content and boundary
counterexamples. Revisit if diagnosis needs a new structured field or a new mutable code
surface; that is a separate schema decision, not permission to broaden this exception.
