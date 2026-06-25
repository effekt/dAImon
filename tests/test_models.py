import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import models  # noqa: E402


class ModelsTest(unittest.TestCase):
    def test_claude_nonempty(self):
        self.assertTrue(models.list_models("claude"))

    def test_codex_nonempty(self):
        self.assertTrue(models.list_models("codex"))

    def test_unknown_backend_raises(self):
        with self.assertRaises(ValueError):
            models.list_models("gemini")


if __name__ == "__main__":
    unittest.main()
