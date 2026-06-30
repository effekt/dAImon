---
name: review-prs
description: Review open pull requests assigned to you and cast a risk-gated decision — approve, request changes, or comment.
---

# review-prs

Autonomously review pull requests that need your attention and cast a review
decision gated on risk. You run inside the target repo, so `gh` targets it
automatically.

## 1. Discover

Find pull requests matching the filter `{{inputs.filter}}`:

```bash
gh pr list --search "{{inputs.filter}}" --json number,title,headRefName,headRefOid
```

Skip any PR you have already reviewed at its current head commit. Your durable
record is the JSON array at `$DAIMON_STATE_FILE` (`[{number, headSha, verdict}]`)
— read it at the start, skip PRs whose number + head SHA you've already recorded,
and write back the ones you act on this run. (Submitting a review also clears the
`review-requested` flag, so most already-done PRs simply won't appear. A removed
entry — e.g. reply-to-comments cleared it after a reply — makes a PR reappear for
re-review even at an unchanged SHA.)

## 2. Review each PR

1. Read the diff (`gh pr diff <number>`).
2. **Check intent.** If the PR title or body references a story (an `sc-####` id
   or a Shortcut URL), read that story (see Source) and review the diff against
   its description and acceptance criteria — flag scope gaps and unmet criteria,
   not only code defects. Shortcut is **read-only** here: only `GET` a story to
   read it. Never comment on, label, or move a story — those sections in Source
   do not apply to you.
3. Check it against the repository's conventions and any rules files in the repo.
4. Identify correctness bugs, security issues, and clear quality problems. Prefer
   a few high-confidence findings over many speculative ones.

## 3. Classify risk

- **INERT** — every change is copy / strings / comments / markdown / test-only:
  no logic, imports, config, or schema.
- **HIGH** — the diff touches a sensitive area: any changed path
  (`gh pr diff <n> --name-only`) matching `{{inputs.high_risk_globs}}` (auth,
  payments, migrations, infra, secrets). Err toward not-HIGH; HIGH is the
  exception, for changes where a human sign-off genuinely adds value beyond
  automated checks.
- **LOW / MEDIUM** — everything else.

## 4. Cast one review decision

Submit **exactly one** review per PR (`gh pr review`, or the reviews API for
inline comments). Every comment you post is prefixed with `{{inputs.bot_marker}}`
so reply-to-comments can pick up responses.

- **Findings exist → `REQUEST_CHANGES`.** One inline comment per finding (problem
  + concrete fix); review body ≤140 chars summarizing. Re-resolve any earlier
  comment the author has since fixed.
- **Clean + HIGH → `COMMENT`** (not approve): `Automated review — no rule
  violations found. HIGH-risk change; human approval recommended. Verify: <areas>.`
- **Clean + INERT/LOW/MEDIUM →** if `{{inputs.auto_approve}}` is `1`, `APPROVE`
  with a ≤140-char note on what's good; if `0`, post `COMMENT` instead.

## 5. Finish

Record each acted-on PR as `{number, headSha, verdict}` in `$DAIMON_STATE_FILE`.
Keep the summary short: each PR, its verdict, and how many findings it got.
