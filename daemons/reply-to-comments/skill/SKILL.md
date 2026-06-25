---
name: reply-to-comments
description: Watch for human replies to your bot comments and respond to each.
---

# reply-to-comments

Respond to humans who replied to comments you previously posted. You run inside
the target repo, so `gh` targets it automatically.

## 1. Discover

Find comment threads where:

- a comment you authored carries the bot marker `{{inputs.bot_marker}}`, and
- a human has replied **after** your last comment in that thread.

Track the last comment id you processed per thread in `$DAIMON_STATE_FILE` (JSON)
so re-runs only pick up genuinely new replies.

## 2. Respond to each thread

For every thread with a new human reply:

1. Read the full thread for context.
2. If the reply asks a question or requests a change, address it directly — make
   the change if it is within scope, or explain clearly why not.
3. Post your response, prefixed with the bot marker `{{inputs.bot_marker}}` so the
   next run can tell your comments apart from human ones.

## 3. Finish

Write the latest processed comment id per thread back to `$DAIMON_STATE_FILE`.
Summarize how many threads you replied to.
