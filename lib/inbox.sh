#!/usr/bin/env bash
# Inbox gate. Caller sets DAEMON_NAME, sources this; reads HAS_INBOX_MESSAGES.
# Messages live in runtime/inbox.json as {"messages": [{"to": "<slug>", ...}]}.

_inbox_file() { echo "$(runtime_dir)/inbox.json"; }

HAS_INBOX_MESSAGES="$(python3 - "$(_inbox_file)" "$DAEMON_NAME" <<'PY'
import json, sys
path, name = sys.argv[1], sys.argv[2]
try: msgs = json.load(open(path)).get("messages", [])
except Exception: msgs = []
print(sum(1 for m in msgs if m.get("to") == name))
PY
)"
