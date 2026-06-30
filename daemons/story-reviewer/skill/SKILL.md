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

**Scope is a hard gate, not a preference.** Only ever comment on, label, or follow
a story that `{{inputs.owner}}` requested or owns (if `{{inputs.owner}}` is blank,
all stories are in scope). A story belonging to anyone else is off-limits even if
it is sitting in triage un-assessed.

Get the un-assessed stories in `{{inputs.triage_state}}` that carry no assessment
label and are not tagged `{{inputs.skip_label}}`, fetched **already scoped to
`{{inputs.owner}}` on the server** (the owner's and requester's stories — see
Source). Do not pull the whole triage column and rely on yourself to filter it.

Then apply the **safety net** from Source: re-read each story and drop any where
`{{inputs.owner}}` is neither the requester nor an owner, logging
`[out-of-scope skip] sc-{id} …`. Only the survivors continue to step 2.

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

Comment on the story with a factual assessment, written per `{{inputs.verbosity}}`.
Keep every claim grounded in what you actually found in the code — do not invent
file paths or APIs.

- **`compact`** — affected files, a suggested approach, complexity, and open
  questions, in a few short paragraphs.
- **`full`** — a sectioned assessment:

  ```markdown
  ## Assessment: <story name>

  **Domain:** <frontend | backend | fullstack | infra | …>

  ### Affected areas
  - `path/to/file` — <what changes here and why>

  ### Approach
  <Which layers to touch, the pattern to follow, a similar existing implementation.>

  ### Patterns to follow
  - <existing implementation / component / service method to reuse, with its path>

  ### Dependencies & risks
  - <migrations, schema changes, other services, blockers>

  ### Suggested order
  1. <first step>  2. <next step>  …

  **Complexity:** <S | M | L | XL>

  ### Open questions
  - <anything that needs a human answer — these drive the label in §4>
  ```

Prefix the comment with `{{inputs.bot_marker}}` (see **Output conventions** for
voice — factual, no hedging, no AI/automation mentions).

## 4. Stamp the label

Add exactly one assessment label (read-modify-write the label set — see Source):

- `{{inputs.ready_label}}` — clearly specified, self-contained, no human judgment
  needed. This is the handoff to the implementation daemon, so be conservative.
- `{{inputs.assist_label}}` — needs clarification or a human decision first; say
  what's missing in the comment.
- `{{inputs.human_label}}` — requires product/design judgment; not for automation.

## 5. Finish

Summarize how many stories you assessed and the label counts. Stop.
