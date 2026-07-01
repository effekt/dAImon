import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load():
    spec = importlib.util.spec_from_file_location("daimon_init", ROOT / "daimon" / "init.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


init = _load()


class SetDisabledTest(unittest.TestCase):
    def test_replaces_in_place_preserving_comments(self):
        text = "[daemons]\n# keep me\ndisabled = []\n"
        out = init.set_disabled_text(text, ["a", "b"])
        self.assertIn("# keep me", out)
        self.assertIn('disabled = ["a", "b"]', out)
        self.assertEqual(out.count("disabled ="), 1)

    def test_preserves_other_sections(self):
        text = '[core]\nnamespace = "daimon"\n\n[daemons]\ndisabled = ["x"]\n\n[budget]\nhourly_cap = 12\n'
        out = init.set_disabled_text(text, [])
        self.assertIn('namespace = "daimon"', out)
        self.assertIn("hourly_cap = 12", out)
        self.assertIn("disabled = []", out)

    def test_adds_line_when_section_present_without_disabled(self):
        text = "[daemons]\n"
        out = init.set_disabled_text(text, ["a"])
        self.assertIn("[daemons]", out)
        self.assertIn('disabled = ["a"]', out)

    def test_adds_section_when_absent(self):
        text = '[core]\nnamespace = "daimon"\n'
        out = init.set_disabled_text(text, ["a"])
        self.assertIn("[daemons]", out)
        self.assertIn('disabled = ["a"]', out)

    def test_trailing_newline_preserved(self):
        self.assertTrue(init.set_disabled_text("[daemons]\ndisabled = []\n", []).endswith("\n"))
        self.assertFalse(init.set_disabled_text("[daemons]\ndisabled = []", []).endswith("\n"))


if __name__ == "__main__":
    unittest.main()
