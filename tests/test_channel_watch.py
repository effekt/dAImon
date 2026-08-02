import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location(
        "channel_watch_forward", ROOT / "daemons" / "slack-channel-watch" / "forward.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fwd = _load()


def _read(path):
    with open(path) as f:
        return json.load(f)


def _write(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


HUMAN_CMD = {"user": "U1", "ts": "2.0", "text": "?help"}
HUMAN_CHAT = {"user": "U1", "ts": "3.0", "text": "hello all"}
THREAD_REPLY = {"user": "U1", "ts": "4.0", "thread_ts": "2.0", "text": "?nested"}
BOT_MSG = {"user": "U9", "bot_id": "B1", "ts": "5.0", "text": "?bot"}


class SelectCommandsTest(unittest.TestCase):
    def test_selects_only_toplevel_human_prefixed(self):
        picked = fwd.select_commands([HUMAN_CMD, HUMAN_CHAT, THREAD_REPLY, BOT_MSG], "?")
        self.assertEqual(picked, [HUMAN_CMD])


class ForwardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = os.path.join(self.tmp.name, "state.json")
        self.inbox = os.path.join(self.tmp.name, "inbox.json")
        os.environ.update(
            SLACK_TOKEN="xoxp-test",
            DAIMON_INPUT_WATCH_CHANNELS="C1 C2",
            DAIMON_INPUT_TRIGGER_PREFIX="?",
            DAIMON_INPUT_TARGET="engine",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_forwards_commands_and_advances_state(self):
        fetched = {"C1": [HUMAN_CMD, HUMAN_CHAT], "C2": []}
        count = fwd.forward(self.state, self.inbox, fetch=lambda t, c, o: fetched[c])
        self.assertEqual(count, 1)
        inbox = _read(self.inbox)
        self.assertEqual(inbox["messages"][0]["command"], "help")
        self.assertEqual(inbox["messages"][0]["to"], "engine")
        self.assertEqual(inbox["messages"][0]["thread_ts"], "2.0")
        self.assertEqual(_read(self.state)["last_ts"], {"C1": "3.0"})

    def test_quiet_channels_write_no_inbox(self):
        count = fwd.forward(self.state, self.inbox, fetch=lambda t, c, o: [])
        self.assertEqual(count, 0)
        self.assertFalse(os.path.exists(self.inbox))

    def test_preserves_other_daemons_messages(self):
        os.makedirs(os.path.dirname(self.inbox), exist_ok=True)
        _write(self.inbox, {"messages": [{"to": "other", "command": "x"}]})
        fwd.forward(self.state, self.inbox, fetch=lambda t, c, o: [HUMAN_CMD] if c == "C1" else [])
        inbox = _read(self.inbox)
        self.assertEqual([m["to"] for m in inbox["messages"]], ["other", "engine"])


if __name__ == "__main__":
    sys.exit(unittest.main())
