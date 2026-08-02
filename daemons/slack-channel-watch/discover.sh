#!/usr/bin/env bash
# Discovery gate for slack-channel-watch. There is no bash-side Slack
# credential to poll with, so the session itself is the check — launch on
# every tick (the daemon runs a small model and exits fast when the channel
# is quiet).
exit 0
