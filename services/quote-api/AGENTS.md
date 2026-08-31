# quote-api/ — agent contract

Serves programming quotes as JSON over a command-line interface. This service is the
**only** owner of the quote data; anything that wants a quote calls the interface
below — never reads `quotes.json` directly.

## Verify changes

```bash
python3 services/quote-api/tests/test_quote_api.py
```

## Public interface (the API other services rely on)

```bash
python3 services/quote-api/quote_api.py                 # random quote as JSON
python3 services/quote-api/quote_api.py --topic <t>     # random quote on a topic
python3 services/quote-api/quote_api.py --list-topics   # {"topics": [...]}
```

Output is always a single JSON object on stdout; unknown topic exits 1 with
`{"error": ...}`. Changing this interface is a **one-way door** (consumers depend on
it) — file a decision per `handbook/collaboration-modes.md`.

## Boundaries

- Owns `quotes.json` and its format; may change both freely (the JSON *stdout*
  contract above is what's frozen, not the storage).
- No network access.

## Endpoints (subfolders)

| Subfolder | What it is | Enter when |
|-----------|------------|------------|
| `tests/` | unit tests for the public interface | any change here |
