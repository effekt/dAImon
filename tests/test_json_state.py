import json
import sys
import tempfile
import unittest
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import json_state  # noqa: E402


def run(*argv) -> str:
    buf = StringIO()
    with redirect_stdout(buf):
        json_state.main(list(argv))
    return buf.getvalue().strip()


class JsonStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "s.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_get_missing_file_returns_default(self):
        self.assertEqual(run("get", self.path, "level", "off"), "off")

    def _read(self) -> dict:
        with open(self.path) as f:
            return json.load(f)

    def test_incr_creates_and_counts(self):
        self.assertEqual(run("incr", self.path, "alpha"), "1")
        self.assertEqual(run("incr", self.path, "alpha"), "2")
        self.assertEqual(self._read(), {"alpha": 2})

    def test_set_coerces_json_else_string(self):
        run("set", self.path, "expires_at", "1719331200")
        run("set", self.path, "level", "halt")
        data = self._read()
        self.assertEqual(data["expires_at"], 1719331200)
        self.assertEqual(data["level"], "halt")
        self.assertEqual(run("get", self.path, "expires_at", "0"), "1719331200")

    def test_unknown_op_errors(self):
        self.assertEqual(json_state.main(["bogus", self.path, "k"]), 2)


if __name__ == "__main__":
    unittest.main()
