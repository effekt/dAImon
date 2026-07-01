import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load():
    spec = importlib.util.spec_from_file_location(
        "daimon_check_links", ROOT / "daimon" / "check_links.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check_links = _load()


class LinksTest(unittest.TestCase):
    def test_all_relative_markdown_links_resolve(self):
        for md in check_links._md_files(check_links.INSTALL_ROOT):
            broken = check_links._broken_links(md)
            with self.subTest(doc=str(md.relative_to(check_links.INSTALL_ROOT))):
                self.assertEqual(broken, [], f"broken links in {md.name}: {broken}")


if __name__ == "__main__":
    unittest.main()
