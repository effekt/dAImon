---
name: story-reviewer
description: Triage stories — investigate each against the codebase, post an assessment, and stamp a visible label marking whether it's AI-completable.
---

# story-reviewer

Assess stories sitting in triage and label them so a human (and the
implementation daemon) can see at a glance which ones are AI-completable. Process
each un-assessed story in the `{{inputs.triage_state}}` state this run. The
"Source" section below explains how to find, read, comment on, and label stories.

## 1. Find un-assessed stories

List stories in `{{inputs.triage_state}}` that carry no assessment label yet and
are not tagged `{{inputs.skip_label}}`. **Scope:** only stories owned or requested
by `{{inputs.owner}}` (if blank, all).

## 2. Investigate each

Stories here are not tied to one repository — you start in a directory that
contains several. **Scope:** only consider these repositories: `{{inputs.repos}}`
— if that is blank, consider every repository under the directory (list it to map
what's there). For each story, work out which repo it concerns and `cd` into it
before exploring; that repo's `CLAUDE.md`, conventions, and `gh` context apply
once you are inside it. Determine: what it asks for and the acceptance criteria; where it
lives; complexity; and whether it can be implemented end-to-end without human
decisions.

## 3. Post an assessment

Comment on the story with a concise, factual assessment: affected files, a
suggested approach, complexity, and open questions. Keep every claim grounded in
what you actually found in the code — do not invent file paths or APIs.

## 4. Stamp the label

Add exactly one assessment label (read-modify-write the label set — see Source):

- `{{inputs.ready_label}}` — clearly specified, self-contained, no human judgment
  needed. This is the handoff to the implementation daemon, so be conservative.
- `{{inputs.assist_label}}` — needs clarification or a human decision first; say
  what's missing in the comment.
- `{{inputs.human_label}}` — requires product/design judgment; not for automation.

## 5. Finish

Summarize how many stories you assessed and the label counts. Stop.
