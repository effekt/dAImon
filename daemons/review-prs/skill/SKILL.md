---
name: review-prs
description: Review open pull requests assigned to you and post actionable feedback.
---

# review-prs

Autonomously review pull requests that need your attention. You run inside the
target repo, so `gh` targets it automatically.

## 1. Discover

Find pull requests matching the filter `{{inputs.filter}}`:

```bash
gh pr list --search "{{inputs.filter}}" --json number,title,headRefName
```

Skip any PR you have already reviewed at its current head commit. Your durable
record is the JSON file at `$DAIMON_STATE_FILE` — read it at the start, skip PRs
whose number + head SHA you've already recorded, and write back the ones you
review this run. (Submitting a GitHub review also clears the `review-requested`
flag, so most already-done PRs simply won't appear.)

## 2. Review each PR

For every PR in the queue:

1. Read the diff (`gh pr diff <number>`).
2. Check it against the repository's conventions and any rules files in the repo.
3. Identify correctness bugs, security issues, and clear quality problems. Prefer
   a few high-confidence findings over many speculative ones.
4. Post findings as inline review comments. Re-resolve any earlier comment that the
   author has since fixed.

## 3. Finish

Append each reviewed PR (number + head SHA) to `$DAIMON_STATE_FILE` so the next
run skips it. Keep your summary short: which PRs were reviewed and how many
findings each got.
