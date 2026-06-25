import sys
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import toml_emit  # noqa: E402


class TomlEmitTest(unittest.TestCase):
    def test_scalars(self):
        self.assertEqual(toml_emit.emit_value(True), "true")
        self.assertEqual(toml_emit.emit_value(False), "false")
        self.assertEqual(toml_emit.emit_value(7), "7")
        self.assertEqual(toml_emit.emit_value("hi"), '"hi"')

    def test_inline_table_and_array(self):
        self.assertEqual(toml_emit.emit_value({"interval": 60}), "{ interval = 60 }")
        self.assertEqual(toml_emit.emit_value([1, 2]), "[1, 2]")
        self.assertEqual(toml_emit.emit_value(["a", "b"]), '["a", "b"]')

    def test_dump_sections_roundtrips(self):
        sections = {
            "daemon": {"backend": "claude", "schedule": {"minutes": [8, 38]}, "danger": True},
            "inputs": {"repo": "me/x", "labels": ["a", "b"]},
        }
        text = toml_emit.dump_sections(sections)
        parsed = tomllib.loads(text)
        self.assertEqual(parsed["daemon"]["backend"], "claude")
        self.assertEqual(parsed["daemon"]["schedule"], {"minutes": [8, 38]})
        self.assertEqual(parsed["daemon"]["danger"], True)
        self.assertEqual(parsed["inputs"]["labels"], ["a", "b"])

    def test_empty_section_skipped(self):
        text = toml_emit.dump_sections({"daemon": {"x": 1}, "inputs": {}})
        self.assertNotIn("[inputs]", text)


if __name__ == "__main__":
    unittest.main()
