import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))
from daimon import Daimon  # noqa: E402
from daimon.app import parse_schedule  # noqa: E402
from daimon import sync  # noqa: E402


class ScheduleParseTest(unittest.TestCase):
    def test_interval_units(self):
        self.assertEqual(parse_schedule("30s"), {"interval": 30})
        self.assertEqual(parse_schedule("20m"), {"interval": 1200})
        self.assertEqual(parse_schedule("1h"), {"interval": 3600})

    def test_daily_and_dict(self):
        self.assertEqual(parse_schedule("09:02"), {"daily": "09:02"})
        self.assertEqual(parse_schedule({"minutes": [8, 38]}), {"minutes": [8, 38]})

    def test_bad_raises(self):
        with self.assertRaises(ValueError):
            parse_schedule("soon")


class RegistrationTest(unittest.TestCase):
    def test_decorator_registers_with_defaults(self):
        app = Daimon()

        @app.daemon(slug="rev", backend="claude", schedule="20m",
                    inputs={"repo": "me/x"})
        def rev(ctx):
            return True

        spec = app.specs["rev"]
        self.assertEqual(spec.command, "/rev")
        self.assertEqual(spec.schedule, {"interval": 1200})
        self.assertIs(spec.fn, rev)

    def test_spec_to_toml_roundtrips(self):
        app = Daimon()

        @app.daemon(slug="wq", backend="both", schedule={"minutes": [8, 38]},
                    working_dir="~/code", inputs={"base": "main", "repos": ["a", "b"]})
        def wq(ctx):
            return False

        parsed = tomllib.loads(sync.spec_to_toml(app.specs["wq"]))
        self.assertEqual(parsed["daemon"]["backend"], "both")
        self.assertEqual(parsed["daemon"]["command"], "/wq")
        self.assertEqual(parsed["daemon"]["working_dir"], "~/code")
        self.assertEqual(parsed["inputs"]["repos"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
