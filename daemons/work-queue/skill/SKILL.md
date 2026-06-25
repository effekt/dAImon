---
name: work-queue
description: Autonomously implement one ready story end-to-end on an isolated branch and open a pull request.
---

# work-queue

Pick up one ready story, implement it in isolation, verify it, and open a pull
request. Do exactly one story per run, then stop. The "Source" section below
explains how to find, read, and move stories.

## 1. Claim one story

Find stories labelled `{{inputs.ready_label}}` (see the Source section), excluding
any tagged `{{inputs.skip_label}}` or already in `{{inputs.in_progress_state}}`.
If any carry `{{inputs.priority_label}}`, pick one of those first; otherwise the
oldest. Read it in full, then **claim it** by moving it to
`{{inputs.in_progress_state}}` so a later run won't pick it up again. If there are
no ready stories, stop.

## 2. Pick the repository and isolate

You start in a directory that may contain several repositories. **Scope:**
restrict to these repositories: `{{inputs.repos}}` — if blank, any repository
under the directory is fair game. Determine which one the story targets and `cd`
into it (its `CLAUDE.md`, conventions, and `gh` context apply once inside). Never work in the main checkout — create a worktree
and branch off `{{inputs.base}}`, kept **inside** that repo (under `.worktrees/`)
so it stays within the trusted project. Exclude it locally so it never shows in
`git status`:

```bash
ROOT="$(git rev-parse --show-toplevel)"
EXCLUDE="$(git rev-parse --git-dir)/info/exclude"
grep -qxF '.worktrees/' "$EXCLUDE" 2>/dev/null || echo '.worktrees/' >> "$EXCLUDE"
git fetch origin {{inputs.base}}
git -C "$ROOT" worktree add ".worktrees/story-<id>" -b daimon/story-<id> "origin/{{inputs.base}}"
cd "$ROOT/.worktrees/story-<id>"
```

## 3. Implement

Implement the story within the worktree, following the repo's conventions and any
rules files. Keep the change scoped to the story.

## 4. Self-review

Re-read your diff against the story's description and acceptance criteria. Fix
anything missing before continuing.

## 5. Verify

Run the repository's own checks (tests, linter, type-check, build). Fix failures.
Do not open a PR with a broken build.

## 6. Open a pull request

Commit, push, and open a **draft** PR. `gh` targets the current repo
automatically — no need to name it. Put the story id and `app_url` in the body so
the story and PR are linked:

```bash
git add -A && git commit -m "<concise summary>"
git push -u origin daimon/story-<id>
gh pr create --base {{inputs.base}} --draft --title "<title>" \
  --body "Implements Shortcut story <id> — <app_url>

<what changed and why, and how it was verified>"
```

## 7. Finish

Remove the `{{inputs.ready_label}}` label (it's been picked up) and leave the
story in `{{inputs.in_progress_state}}`. Summarize: the story id, the branch, and
the PR URL. Stop — one story per run.
