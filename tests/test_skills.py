import re
import sys
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import config  # noqa: E402

DAEMONS = Path(__file__).resolve().parent.parent / "daemons"

PLACEHOLDER = re.compile(r"\{\{inputs\.([a-zA-Z0-9_]+)\}\}")


def frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    _, fm, _ = text.split("---", 2)
    out = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


class SkillsTest(unittest.TestCase):
    def daemon_dirs(self):
        return [p.parent for p in DAEMONS.glob("*/daemon.toml")]

    def test_each_daemon_is_well_formed(self):
        dirs = self.daemon_dirs()
        self.assertTrue(dirs, "no daemons found")
        for d in dirs:
            cfg = tomllib.loads((d / "daemon.toml").read_text())
            daemon = cfg.get("daemon", {})
            with self.subTest(daemon=d.name):
                self.assertTrue(str(daemon.get("command", "")).startswith("/"),
                                f"{d.name}: command must start with /")
                self.assertIn("schedule", daemon, f"{d.name}: schedule required")
                skill = d / "skill" / "SKILL.md"
                self.assertTrue(skill.exists(), f"{d.name}: missing SKILL.md")
                fm = frontmatter(skill.read_text())
                self.assertTrue(fm.get("name"), f"{d.name}: SKILL.md needs a name")
                self.assertTrue(fm.get("description"), f"{d.name}: SKILL.md needs a description")
                self.assertTrue((d / "discover.sh").exists(), f"{d.name}: missing discover.sh")

    def test_placeholders_resolve(self):
        cfg = config.Config.load()
        for slug in cfg.discover():
            with self.subTest(daemon=slug):
                rendered = config.render_skill(cfg, slug)
                leftover = PLACEHOLDER.findall(rendered)
                self.assertEqual(leftover, [],
                                 f"{slug}: unresolved {{{{inputs.*}}}}: {leftover}")


if __name__ == "__main__":
    unittest.main()
