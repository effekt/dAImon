import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import schedule_fmt  # noqa: E402


class ScheduleFmtTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(schedule_fmt.parse("20m"), {"interval": 1200})
        self.assertEqual(schedule_fmt.parse(":8,38"), {"minutes": [8, 38]})
        self.assertEqual(schedule_fmt.parse("09:02"), {"daily": "09:02"})

    def test_parse_bad(self):
        with self.assertRaises(ValueError):
            schedule_fmt.parse("whenever")

    def test_display_roundtrips(self):
        for text in ("1200s", ":8,38", "09:02"):
            self.assertEqual(schedule_fmt.display(schedule_fmt.parse(text)), text)

    def test_descriptor(self):
        self.assertEqual(schedule_fmt.descriptor({"interval": 1200}), "interval 1200")
        self.assertEqual(schedule_fmt.descriptor({"minutes": [17, 47]}), "minutes 17 47")
        self.assertEqual(
            schedule_fmt.descriptor({"daily": "13:02", "tz": "UTC"}), "daily 13:02 UTC"
        )

    def test_to_plist(self):
        self.assertIn("StartInterval", schedule_fmt.to_plist({"interval": 1200}))
        self.assertIn("StartCalendarInterval", schedule_fmt.to_plist({"minutes": [8]}))
        self.assertIn(
            "<key>Hour</key><integer>13</integer>", schedule_fmt.to_plist({"daily": "13:02"})
        )


if __name__ == "__main__":
    unittest.main()
