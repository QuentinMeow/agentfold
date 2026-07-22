import json
import subprocess
import sys
import unittest
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))
import quote_api  # noqa: E402


class TestQuoteApi(unittest.TestCase):
    def test_get_quote_returns_required_fields(self):
        quote = quote_api.get_quote()
        self.assertIn("text", quote)
        self.assertIn("author", quote)
        self.assertIn("topic", quote)

    def test_topic_filter(self):
        for topic in quote_api.list_topics():
            self.assertEqual(quote_api.get_quote(topic)["topic"], topic)

    def test_unknown_topic_raises(self):
        with self.assertRaises(KeyError):
            quote_api.get_quote("no-such-topic")

    def test_cli_contract_json_on_stdout(self):
        result = subprocess.run(
            [sys.executable, str(SERVICE_DIR / "quote_api.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("text", json.loads(result.stdout))

    def test_cli_contract_unknown_topic_exits_1(self):
        result = subprocess.run(
            [sys.executable, str(SERVICE_DIR / "quote_api.py"), "--topic", "nope"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("error", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
