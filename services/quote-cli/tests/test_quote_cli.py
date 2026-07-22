import subprocess
import sys
import unittest
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))
import quote_cli  # noqa: E402


class TestQuoteCli(unittest.TestCase):
    def test_format_quote(self):
        quote = {"text": "Keep it simple.", "author": "Anon", "topic": "simplicity"}
        formatted = quote_cli.format_quote(quote)
        self.assertIn("Keep it simple.", formatted)
        self.assertIn("Anon", formatted)

    def test_end_to_end_random_quote(self):
        result = subprocess.run(
            [sys.executable, str(SERVICE_DIR / "quote_cli.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("—", result.stdout)

    def test_unknown_topic_suggests_topics(self):
        result = subprocess.run(
            [sys.executable, str(SERVICE_DIR / "quote_cli.py"), "no-such-topic"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Try one of:", result.stdout)


if __name__ == "__main__":
    unittest.main()
