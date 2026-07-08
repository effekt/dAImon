import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import claude_trust  # noqa: E402


class ClaudeTrustTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = self.tmp.name
        self._orig_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        if self._orig_home is not None:
            os.environ["HOME"] = self._orig_home
        self.tmp.cleanup()

    def _write(self, projects: dict):
        Path(self.home, ".claude.json").write_text(json.dumps({"projects": projects}))

    def test_trusted_dir(self):
        self._write({"/repo": {"hasTrustDialogAccepted": True}})
        self.assertTrue(claude_trust.is_trusted("/repo"))

    def test_untrusted_dir(self):
        self._write({"/repo": {"hasTrustDialogAccepted": False}})
        self.assertFalse(claude_trust.is_trusted("/repo"))

    def test_unknown_dir(self):
        self._write({"/other": {"hasTrustDialogAccepted": True}})
        self.assertFalse(claude_trust.is_trusted("/repo"))

    def test_trusted_parent_does_not_trust_child(self):
        self._write({"/repo": {"hasTrustDialogAccepted": True}})
        self.assertFalse(claude_trust.is_trusted("/repo/child"))

    def test_exact_child_trust(self):
        self._write(
            {
                "/repo": {"hasTrustDialogAccepted": True},
                "/repo/child": {"hasTrustDialogAccepted": True},
            }
        )
        self.assertTrue(claude_trust.is_trusted("/repo/child"))

    def test_untrusted_parent_does_not_trust_child(self):
        self._write({"/repo": {"hasTrustDialogAccepted": False}})
        self.assertFalse(claude_trust.is_trusted("/repo/child"))

    def test_missing_file(self):
        self.assertFalse(claude_trust.is_trusted("/repo"))


if __name__ == "__main__":
    unittest.main()
