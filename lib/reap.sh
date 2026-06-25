#!/usr/bin/env bash
# Graceful-first teardown of an agent tmux session, reaping the FULL descendant
# tree so MCP servers spawned as grandchildren can't reparent to pid 1 and leak.

_descendants() {  # pid -> all descendant pids, leaves first, root last
  local pid="$1"; [ -z "$pid" ] && return
  local k
  for k in $(pgrep -P "$pid" 2>/dev/null); do _descendants "$k"; done
  echo "$pid"
}

reap_session() {  # session_name
  local sess="$1"
  tmux has-session -t "$sess" 2>/dev/null || return 0
  local pane_pid tree
  pane_pid=$(tmux list-panes -t "$sess" -F '#{pane_pid}' 2>/dev/null | head -1)
  tree=$(_descendants "$pane_pid")

  tmux send-keys -t "$sess" Escape 2>/dev/null; sleep 0.3
  tmux send-keys -t "$sess" "/exit" 2>/dev/null; sleep 0.3
  tmux send-keys -t "$sess" Enter 2>/dev/null
  local i
  for i in $(seq 1 16); do
    tmux has-session -t "$sess" 2>/dev/null || break
    sleep 0.5
  done

  local p alive=""
  for p in $tree; do kill -0 "$p" 2>/dev/null && alive="$alive $p"; done
  if [ -n "$alive" ]; then
    kill $alive 2>/dev/null; sleep 1
    for p in $alive; do kill -0 "$p" 2>/dev/null && kill -9 "$p" 2>/dev/null; done
  fi
  tmux kill-session -t "$sess" 2>/dev/null
}
