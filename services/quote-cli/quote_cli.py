"""quote-cli: human-friendly quote printer on top of quote-api.

Talks to quote-api only through its public CLI contract (see
services/quote-api/AGENTS.md) — a real service boundary, demonstrated small.
"""
import json
import subprocess
import sys
from pathlib import Path

QUOTE_API = Path(__file__).resolve().parents[1] / "quote-api" / "quote_api.py"


def fetch(args):
    result = subprocess.run(
        [sys.executable, str(QUOTE_API), *args], capture_output=True, text=True
    )
    return result.returncode, json.loads(result.stdout)


def format_quote(quote):
    return f'“{quote["text"]}”\n    — {quote["author"]} ({quote["topic"]})'


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    api_args = ["--topic", argv[0]] if argv else []
    code, payload = fetch(api_args)
    if code != 0:
        _, topics = fetch(["--list-topics"])
        print(f"{payload['error']}. Try one of: {', '.join(topics['topics'])}")
        return 1
    print(format_quote(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
