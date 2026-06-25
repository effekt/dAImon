import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tui"))
import schedule_input  # noqa: E402


class ScheduleInputTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(schedule_input.parse("20m"), {"interval": 1200})
        self.assertEqual(schedule_input.parse(":8,38"), {"minutes": [8, 38]})
        self.assertEqual(schedule_input.parse("09:02"), {"daily": "09:02"})

    def test_parse_bad(self):
        with self.assertRaises(ValueError):
            schedule_input.parse("whenever")

    def test_display_roundtrips(self):
        for text in ("1200s", ":8,38", "09:02"):
            self.assertEqual(schedule_input.display(schedule_input.parse(text)), text)


if __name__ == "__main__":
    unittest.main()
