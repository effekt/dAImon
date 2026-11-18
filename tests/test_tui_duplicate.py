"""The TUI's duplicate (`y`): a catalog daemon is forked through `daimon eject
--as`, so it is renamed throughout and tracked like a CLI fork; a daemon of
your own is copied in daemons/ with its command renamed."""

import sys
from pathlib import Path
from unittest.mock import patch

from test_catalog import make_daemon
from test_eject import EjectBase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tui"))
import ops  # noqa: E402


class TuiDuplicateTest(EjectBase):
    def test_a_catalog_daemon_is_forked_with_eject_as(self):
        with patch.object(ops.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertIsNone(ops.duplicate(self.cfg(), "alpha", "omega"))
        argv = run.call_args.args[0]
        self.assertEqual(argv[1:], ["eject", "alpha", "--as", "omega"])
        self.assertTrue(argv[0].endswith("bin/daimon"))
        self.assertTrue(run.call_args.kwargs["capture_output"])

    def test_a_failed_fork_reports_its_last_line(self):
        with patch.object(ops.subprocess, "run") as run:
            run.return_value.returncode = 1
            run.return_value.stderr = "daimon eject: omega already exists: x\n"
            run.return_value.stdout = ""
            err = ops.duplicate(self.cfg(), "alpha", "omega")
        self.assertEqual(err, "daimon eject: omega already exists: x")

    def test_your_own_daemon_is_copied_with_its_command_renamed(self):
        make_daemon(self.root / "daemons" / "mine", "mine")
        cfg = self.cfg()
        self.assertNotIn("mine", cfg.catalog())
        with patch.object(ops.subprocess, "run") as run:
            self.assertIsNone(ops.duplicate(cfg, "mine", "mine-two"))
        run.assert_not_called()
        copy = self.root / "daemons" / "mine-two"
        self.assertIn('command = "/mine-two"', (copy / "daemon.toml").read_text())
        self.assertIn("mine-two", self.cfg().discover())
