#!/usr/bin/env python3
"""Scripted channel watcher: read watched Slack channels since last_ts,
select trigger-prefixed command messages, append them to the target daemon's
inbox, and update per-channel state. Stdlib only — runs from discover.sh so
no agent has to launch just to poll.

usage: forward.py <state_file> <inbox_file>
env:   SLACK_TOKEN, DAIMON_INPUT_WATCH_CHANNELS (space-separated ids),
       DAIMON_INPUT_TRIGGER_PREFIX, DAIMON_INPUT_TARGET
Prints the number of commands forwarded."""

import json
import os
import sys
import urllib.parse
import urllib.request


def fetch_history(token: str, channel: str, oldest: str) -> list[dict]:
    query = {"channel": channel, "limit": 50}
    if oldest:
        query["oldest"] = oldest
    url = f"https://slack.com/api/conversations.history?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    if not data.get("ok"):
        raise RuntimeError(f"{channel}: slack api error: {data.get('error')}")
    return data.get("messages", [])


def select_commands(messages: list[dict], prefix: str) -> list[dict]:
    """Top-level human messages whose text starts with the trigger prefix."""
    return [
        m
        for m in messages
        if m.get("user")
        and not m.get("bot_id")
        and not m.get("thread_ts")
        and m.get("text", "").startswith(prefix)
    ]


def to_inbox_entry(msg: dict, channel: str, prefix: str, target: str) -> dict:
    return {
        "to": target,
        "command": msg["text"][len(prefix) :].strip(),
        "channel": channel,
        "thread_ts": msg["ts"],
        "user": msg["user"],
        "via": "channel",
    }


def load_json(path: str, default: dict) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def dump_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def forward(state_file: str, inbox_file: str, fetch=fetch_history) -> int:
    token = os.environ["SLACK_TOKEN"]
    channels = os.environ["DAIMON_INPUT_WATCH_CHANNELS"].split()
    prefix = os.environ.get("DAIMON_INPUT_TRIGGER_PREFIX", "?")
    target = os.environ.get("DAIMON_INPUT_TARGET", "slack-commands")

    state = load_json(state_file, {})
    last_ts = state.get("last_ts", {})
    inbox = load_json(inbox_file, {"messages": []})
    forwarded = 0

    for channel in channels:
        messages = fetch(token, channel, last_ts.get(channel, ""))
        for msg in select_commands(messages, prefix):
            inbox.setdefault("messages", []).append(to_inbox_entry(msg, channel, prefix, target))
            forwarded += 1
        if messages:
            last_ts[channel] = max(m["ts"] for m in messages)

    if forwarded:
        dump_json(inbox_file, inbox)
    state["last_ts"] = last_ts
    dump_json(state_file, state)
    return forwarded


if __name__ == "__main__":
    print(forward(sys.argv[1], sys.argv[2]))
