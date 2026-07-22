"""quote-api: serves quotes as JSON. Public interface: see AGENTS.md in this folder."""
import argparse
import json
import random
import sys
from pathlib import Path

QUOTES_FILE = Path(__file__).parent / "quotes.json"


def load_quotes():
    return json.loads(QUOTES_FILE.read_text())["quotes"]


def get_quote(topic=None):
    quotes = load_quotes()
    if topic is not None:
        quotes = [q for q in quotes if q["topic"] == topic]
        if not quotes:
            raise KeyError(topic)
    return random.choice(quotes)


def list_topics():
    return sorted({q["topic"] for q in load_quotes()})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Serve quotes as JSON on stdout.")
    parser.add_argument("--topic")
    parser.add_argument("--list-topics", action="store_true")
    args = parser.parse_args(argv)

    if args.list_topics:
        print(json.dumps({"topics": list_topics()}))
        return 0
    try:
        print(json.dumps(get_quote(args.topic)))
        return 0
    except KeyError:
        print(json.dumps({"error": f"unknown topic: {args.topic}"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
