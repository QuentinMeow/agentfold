# quote-cli/ — agent contract

The human-friendly face of the quote system: prints one nicely formatted quote.
Presentation only — this service owns no quote data.

## Verify changes

```bash
python3 services/quote-cli/tests/test_quote_cli.py
```

## Depends on

- **quote-api** — the only source of quotes. Read `../quote-api/AGENTS.md` and use
  only its public interface (invoking `quote_api.py` as a subprocess). Never import
  its Python internals, never read `quotes.json` directly — if the CLI needs data the
  interface doesn't offer, that's a quote-api task, not a workaround here.

## Usage

```bash
python3 services/quote-cli/quote_cli.py            # random quote, formatted
python3 services/quote-cli/quote_cli.py <topic>    # on a topic; lists topics on miss
```

## Boundaries

- Formatting decisions live here; data decisions live in quote-api.
- No network access.

## Endpoints (subfolders)

| Subfolder | What it is | Enter when |
|-----------|------------|------------|
| `tests/` | unit tests for formatting + the dependency seam | any change here |
