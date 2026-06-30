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
        write(
            root / "config" / "daimon.toml",
            f"""
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
        """,
        )
        write(
            root / "daemons" / "alpha" / "daemon.toml",
            """
            [daemon]
            schedule = { interval = 1200 }
            command = "/alpha"
            stuck_after = 600
            [inputs]
            repo = "me/alpha"
            filter = "is:open"
        """,
        )
        write(
            root / "daemons" / "alpha" / "skill" / "SKILL.md",
            "---\nname: alpha\ndescription: a\n---\nRepo {{inputs.repo}} filter {{inputs.filter}}.\n",
        )
        write(
            root / "daemons" / "beta" / "daemon.toml",
            """
            [daemon]
            backend = "claude"
            model = { claude = "opus", default = "sonnet" }
            schedule = { minutes = [17, 47] }
            command = "/beta"
        """,
        )
        write(
            root / "daemons" / "beta" / "skill" / "SKILL.md",
            "---\nname: beta\ndescription: b\n---\nHi.\n",
        )
        write(
            root / "daemons" / "gamma" / "daemon.toml",
            """
            [daemon]
            schedule = { daily = "13:02", tz = "UTC" }
            command = "/gamma"
        """,
        )
        write(
            root / "daemons" / "gamma" / "skill" / "SKILL.md",
            "---\nname: gamma\ndescription: c\n---\nHi.\n",
        )
        write(
            root / "daemons" / "delta" / "daemon.toml",
            """
            [daemon]
            schedule = { interval = 900 }
            command = "/delta"
        """,
        )
        write(
            root / "daemons" / "delta" / "skill" / "SKILL.md",
            "---\nname: delta\ndescription: d\n---\nHi.\n",
        )
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
        self.assertEqual(self.cfg.backends("beta"), ["claude"])

    def test_model_scalar_and_table(self):
        self.assertEqual(self.cfg.model_for("alpha", "claude"), "opus")
        self.assertEqual(self.cfg.model_for("beta", "claude"), "opus")
        self.assertEqual(self.cfg.model_for("beta", "other"), "sonnet")

    def test_env_shell_quotes_spaced_values(self):
        # `cfg env` output is eval'd by run.sh, so values with spaces (e.g. a
        # Shortcut state "In Progress") must be shell-quoted or the eval breaks
        # and later DAIMON_INPUT_* vars never get exported.
        write(
            self.root / "daemons" / "alpha" / "daemon.toml",
            """
            [daemon]
            schedule = { interval = 1200 }
            command = "/alpha"
            [inputs]
            in_progress_state = "In Progress"
            ready_label = "auto-ready"
        """,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            config.main(["env", "alpha"])
        env = self._parse_env_output(buf.getvalue())
        self.assertEqual(env["DAIMON_INPUT_IN_PROGRESS_STATE"], "In Progress")
        self.assertEqual(env["DAIMON_INPUT_READY_LABEL"], "auto-ready")

    def test_daemon_env_bundles_all_launch_fields(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            config.main(["daemon-env", "alpha"])
        env = self._parse_env_output(buf.getvalue())
        d = self.cfg.daemon("alpha")
        self.assertEqual(env["DAIMON_D_COMMAND"], d["command"])
        self.assertEqual(env["DAIMON_D_DANGER"], "1")
        self.assertEqual(env["DAIMON_D_STUCK_AFTER"], str(d["stuck_after"]))
        self.assertEqual(env["DAIMON_D_WORKING_DIR"], d["working_dir"])
        self.assertEqual(env["DAIMON_D_BACKENDS"], "claude")
        self.assertEqual(env["DAIMON_READY_TIMEOUT"], "20")
        self.assertEqual(env["DAIMON_D_MODEL_CLAUDE"], self.cfg.model_for("alpha", "claude"))

    def test_discover_memoized_and_invalidated_on_write(self):
        first = self.cfg.discover()
        self.assertIs(first, self.cfg.discover())
        self.cfg.update_daemon_field("alpha", "command", "/alpha2")
        self.assertIsNot(first, self.cfg.discover())
        self.assertEqual(self.cfg.daemon("alpha")["command"], "/alpha2")

    def test_validate_inputs_flags_empty_required(self):
        write(
            self.root / "daemons" / "alpha" / "daemon.toml",
            """
            [daemon]
            schedule = { interval = 1200 }
            command = "/alpha"
            required_inputs = ["ready_label", "skip_label"]
            [inputs]
            ready_label = "auto-ready"
            skip_label = "   "
        """,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = config.main(["validate-inputs", "alpha"])
        self.assertEqual(rc, 1)
        self.assertEqual(buf.getvalue().strip(), "skip_label")

    def test_validate_inputs_passes_when_all_present(self):
        write(
            self.root / "daemons" / "alpha" / "daemon.toml",
            """
            [daemon]
            schedule = { interval = 1200 }
            command = "/alpha"
            required_inputs = ["ready_label"]
            [inputs]
            ready_label = "auto-ready"
        """,
        )
        self.assertEqual(config.main(["validate-inputs", "alpha"]), 0)

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

    def test_render_skill_appends_learning_protocol(self):
        write(self.root / "references" / "learning.md", "LEARNING PROTOCOL BODY\n")
        out = config.render_skill(self.cfg, "alpha")
        self.assertIn("LEARNING PROTOCOL BODY", out)

    def test_render_skill_learning_opt_out(self):
        write(self.root / "references" / "learning.md", "LEARNING PROTOCOL BODY\n")
        write(
            self.root / "daemons" / "alpha" / "daemon.toml",
            """
            [daemon]
            schedule = { interval = 1200 }
            command = "/alpha"
            learning = false
            [inputs]
            repo = "me/alpha"
        """,
        )
        out = config.render_skill(config.Config.load(), "alpha")
        self.assertNotIn("LEARNING PROTOCOL BODY", out)

    def test_render_plist_contains_label_and_slug(self):
        xml = config.render_plist(self.cfg, "alpha")
        self.assertIn("<string>com.testns.alpha</string>", xml)
        self.assertIn("<string>alpha</string>", xml)
        self.assertIn("StartInterval", xml)

    def test_validate_clean(self):
        self.assertEqual(config.validate(self.cfg), [])

    def test_validate_catches_bad_backend(self):
        write(
            self.root / "daemons" / "alpha" / "daemon.toml",
            """
            [daemon]
            backend = "gpt"
            schedule = { interval = 1200 }
            command = "/alpha"
        """,
        )
        errs = config.validate(config.Config.load())
        self.assertTrue(any("backend must be one of" in e for e in errs))

    def test_validate_catches_empty_required_input(self):
        write(
            self.root / "daemons" / "alpha" / "daemon.toml",
            """
            [daemon]
            schedule = { interval = 1200 }
            command = "/alpha"
            required_inputs = ["repo", "token"]
            [inputs]
            repo = "me/alpha"
            token = ""
        """,
        )
        errs = config.validate(config.Config.load())
        self.assertTrue(any("required input 'token'" in e for e in errs))
        self.assertFalse(any("required input 'repo'" in e for e in errs))

    def test_validate_catches_missing_command(self):
        write(
            self.root / "daemons" / "alpha" / "daemon.toml",
            """
            [daemon]
            schedule = { interval = 1200 }
        """,
        )
        errs = config.validate(config.Config.load())
        self.assertTrue(any("command" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
