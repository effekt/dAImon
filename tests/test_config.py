import io
import os
import shlex
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import config  # noqa: E402


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text))


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.root = root
        write(root / "config" / "daimon.toml", f"""
            [core]
            install_root = "{root}"
            state_dir = "{root}/state"
            namespace = "testns"
            [defaults]
            backend = "claude"
            model = "opus"
            danger = true
            stuck_after = 2700
            ready_timeout = 20
            [throttle]
            exempt = ["alpha"]
            moderate_mod = 2
            severe_mod = 4
            severe_critical = ["beta"]
            [budget]
            hourly_cap = 12
            defer_at_pct = 80
            [daemons]
            disabled = ["delta"]
        """)
        write(root / "daemons" / "alpha" / "daemon.toml", """
            [daemon]
            schedule = { interval = 1200 }
            command = "/alpha"
            stuck_after = 600
            [inputs]
            repo = "me/alpha"
            filter = "is:open"
        """)
        write(root / "daemons" / "alpha" / "skill" / "SKILL.md",
              "---\nname: alpha\ndescription: a\n---\nRepo {{inputs.repo}} filter {{inputs.filter}}.\n")
        write(root / "daemons" / "beta" / "daemon.toml", """
            [daemon]
            backend = "both"
            model = { claude = "opus", codex = "gpt-5-codex" }
            schedule = { minutes = [17, 47] }
            command = "/beta"
        """)
        write(root / "daemons" / "beta" / "skill" / "SKILL.md",
              "---\nname: beta\ndescription: b\n---\nHi.\n")
        write(root / "daemons" / "gamma" / "daemon.toml", """
            [daemon]
            schedule = { daily = "13:02", tz = "UTC" }
            command = "/gamma"
        """)
        write(root / "daemons" / "gamma" / "skill" / "SKILL.md",
              "---\nname: gamma\ndescription: c\n---\nHi.\n")
        write(root / "daemons" / "delta" / "daemon.toml", """
            [daemon]
            schedule = { interval = 900 }
            command = "/delta"
        """)
        write(root / "daemons" / "delta" / "skill" / "SKILL.md",
              "---\nname: delta\ndescription: d\n---\nHi.\n")
        os.environ["DAIMON_CONFIG"] = str(root / "config" / "daimon.toml")
        self.cfg = config.Config.load()

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("DAIMON_CONFIG", None)

    def test_discovery_excludes_disabled(self):
        self.assertEqual(set(self.cfg.discover()), {"alpha", "beta", "gamma"})

    def test_defaults_inherited(self):
        self.assertEqual(self.cfg.daemon("beta")["danger"], True)
        self.assertEqual(self.cfg.daemon("beta")["stuck_after"], 2700)

    def test_per_daemon_override(self):
        self.assertEqual(self.cfg.daemon("alpha")["stuck_after"], 600)

    def test_backends(self):
        self.assertEqual(self.cfg.backends("alpha"), ["claude"])
        self.assertEqual(self.cfg.backends("beta"), ["claude", "codex"])

    def test_model_scalar_and_table(self):
        self.assertEqual(self.cfg.model_for("alpha", "claude"), "opus")
        self.assertEqual(self.cfg.model_for("beta", "claude"), "opus")
        self.assertEqual(self.cfg.model_for("beta", "codex"), "gpt-5-codex")

    def test_schedule_descriptors(self):
        sd = config.schedule_descriptor
        self.assertEqual(sd(self.cfg.daemon("alpha")["schedule"]), "interval 1200")
        self.assertEqual(sd(self.cfg.daemon("beta")["schedule"]), "minutes 17 47")
        self.assertEqual(sd(self.cfg.daemon("gamma")["schedule"]), "daily 13:02 UTC")

    def test_env_shell_quotes_spaced_values(self):
        # `cfg env` output is eval'd by run.sh, so values with spaces (e.g. a
        # Shortcut state "In Progress") must be shell-quoted or the eval breaks
        # and later DAIMON_INPUT_* vars never get exported.
        write(self.root / "daemons" / "alpha" / "daemon.toml", """
            [daemon]
            schedule = { interval = 1200 }
            command = "/alpha"
            [inputs]
            in_progress_state = "In Progress"
            ready_label = "auto-ready"
        """)
        buf = io.StringIO()
        with redirect_stdout(buf):
            config.main(["env", "alpha"])
        env = self._parse_env_output(buf.getvalue())
        self.assertEqual(env["DAIMON_INPUT_IN_PROGRESS_STATE"], "In Progress")
        self.assertEqual(env["DAIMON_INPUT_READY_LABEL"], "auto-ready")

    def _parse_env_output(self, output):
        # Mimic run.sh's eval: each line must be a single shell token (a
        # well-formed VAR=value), or word-splitting on a spaced value would
        # break the eval and drop later assignments.
        env = {}
        for line in filter(None, output.splitlines()):
            tokens = shlex.split(line)
            self.assertEqual(len(tokens), 1, f"line not shell-safe: {line!r}")
            key, _, value = tokens[0].partition("=")
            env[key] = value
        return env

    def test_render_skill_substitutes_inputs(self):
        out = config.render_skill(self.cfg, "alpha")
        self.assertIn("Repo me/alpha filter is:open.", out)
        self.assertNotIn("{{inputs", out)

    def test_render_plist_contains_label_and_slug(self):
        xml = config.render_plist(self.cfg, "alpha")
        self.assertIn("<string>com.testns.alpha</string>", xml)
        self.assertIn("<string>alpha</string>", xml)
        self.assertIn("StartInterval", xml)

    def test_validate_clean(self):
        self.assertEqual(config.validate(self.cfg), [])

    def test_validate_catches_bad_backend(self):
        write(self.root / "daemons" / "alpha" / "daemon.toml", """
            [daemon]
            backend = "gpt"
            schedule = { interval = 1200 }
            command = "/alpha"
        """)
        errs = config.validate(config.Config.load())
        self.assertTrue(any("backend must be one of" in e for e in errs))

    def test_validate_catches_missing_command(self):
        write(self.root / "daemons" / "alpha" / "daemon.toml", """
            [daemon]
            schedule = { interval = 1200 }
        """)
        errs = config.validate(config.Config.load())
        self.assertTrue(any("command" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
