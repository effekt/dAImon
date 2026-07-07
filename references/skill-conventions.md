# Conventions for comment-posting daemons

You post to a shared repository and run repeatedly. Two conventions keep that safe
and idempotent — they apply to every comment-posting daemon, so follow them even
where the steps above don't restate them.

## Mark every comment you post

Prefix every comment, review, or reply you post with `{{inputs.bot_marker}}`. This
is how other daemons — and you, on a later run — tell your automated comments from
a human's. The reply daemons (`reply-to-pr-comments`, `reply-to-story-comments`)
only act on replies to comments carrying this marker, and no daemon should ever
act on its own comments.

## Track what you've handled in `$DAIMON_STATE_FILE`

`$DAIMON_STATE_FILE` is your durable JSON memory across runs. Read it at the start
and skip any item already handled at its current commit/state; write the updated
record at the end. Key each record by the item **and** the commit or state it was
at, so an unchanged item is never reprocessed and a changed one always is.

It is an **absolute path outside the repo** (under the daemon's state dir), already
set in your environment. Read and write it exactly, always **expanding** the
variable — double-quote it so the shell substitutes the path:

```bash
echo "$DAIMON_STATE_FILE"          # confirm it's set to an absolute path first
cat "$DAIMON_STATE_FILE" 2>/dev/null || echo '[]'   # read
printf '%s' "$new_json" > "$DAIMON_STATE_FILE"       # write
```

You run inside a git repository. **Never write state anywhere inside it.** Do not
write to a single-quoted `'$DAIMON_STATE_FILE'` (that creates a file literally
named `$DAIMON_STATE_FILE` in the cwd), do not invent a `.daimon/` or `state/`
directory in the working tree, and do not name a file by date. If
`$DAIMON_STATE_FILE` is somehow empty, stop and report it — do not fall back to a
path in the repo. The only state file you touch is the one at `$DAIMON_STATE_FILE`.
