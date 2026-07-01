import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load():
    spec = importlib.util.spec_from_file_location(
        "daimon_gen_docs", ROOT / "daimon" / "gen_docs.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen_docs = _load()


class DocsTest(unittest.TestCase):
    def test_daemon_readmes_are_up_to_date(self):
        for path, content in gen_docs._targets(gen_docs.INSTALL_ROOT):
            rel = path.relative_to(gen_docs.INSTALL_ROOT)
            with self.subTest(doc=str(rel)):
                self.assertTrue(path.exists(), f"{rel} missing — run `make docs`")
                self.assertEqual(path.read_text(), content, f"{rel} is stale — run `make docs`")


if __name__ == "__main__":
    unittest.main()
