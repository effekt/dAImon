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
