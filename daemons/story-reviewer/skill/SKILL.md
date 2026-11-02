---
name: story-reviewer
description: Triage stories — investigate each against the codebase, post an assessment, and stamp a visible label marking whether it's AI-completable.
---

# story-reviewer

Assess stories in the intake and label them so a human (and the implementation
daemon) can see at a glance which ones are AI-completable. Process at most
`{{inputs.max_per_run}}` un-assessed stories this run. The "Source" section below
explains how to find, read, comment on, and label stories.

## 1. Find un-assessed stories

**Scope is a hard gate, not a preference.** Only ever comment on, label, or follow
a story that `{{inputs.owner}}` requested or owns (if `{{inputs.owner}}` is blank,
all stories are in scope). A story belonging to anyone else is off-limits even if
it is sitting in triage un-assessed.

**The intake** is the union of three searches. Every one is fetched **already
scoped to `{{inputs.owner}}` on the server** (the owner's and requester's stories —
see Source), and every one excludes stories that already carry an assessment
label (`{{inputs.ready_label}}`, `{{inputs.assist_label}}`,
`{{inputs.human_label}}`), are tagged `{{inputs.skip_label}}`, or are done or
archived (`!is:done !is:archived`). Do not pull a whole column and rely on
yourself to filter it.

1. Stories in `{{inputs.triage_state}}`.
2. Stories carrying any of these labels: `{{inputs.intake_labels}}` (blank means
   none), in any state except `{{inputs.in_progress_state}}`, and carrying none
   of these: `{{inputs.intake_exclude_labels}}`. Run one search per label; the
   search has no OR.
3. Every story in an open epic that itself carries `{{inputs.ready_label}}`, in
   any state except `{{inputs.in_progress_state}}`. Labelling an epic opts its
   whole backlog into review; it does **not** make the stories ready. Find those
   epics with `GET /api/v3/search/epics` and
   `query=label:"{{inputs.ready_label}}" !is:done !is:archived`, then search
   `epic:<id>` for each.

Merge by story id. Then drop every story already recorded in your state
(`daimon state get story-reviewer`, an object keyed by story id) whose current
`updated_at` is not newer than the recorded `updated_at`. You reviewed it and
nothing has changed since; if a human removed your label, that was deliberate.
Never re-review such a story.

Then apply the **safety net** from Source: re-read each story and drop any where
`{{inputs.owner}}` is neither the requester nor an owner, logging
`[out-of-scope skip] sc-{id} …`. Of the survivors, take stories carrying
`{{inputs.priority_label}}` first, then the oldest, up to `{{inputs.max_per_run}}`.
Only those continue to step 2. The rest wait for a later run.

## 2. Investigate each

Stories here are not tied to one repository — you start in a directory that
contains several. **Scope:** only consider these repositories: `{{inputs.repos}}`
— if that is blank, consider every repository under the directory (list it to map
what's there). For each story, work out which repo it concerns and `cd` into it
before exploring; that repo's `CLAUDE.md`, conventions, and `gh` context apply
once you are inside it. Determine: what it asks for and the acceptance criteria; where it
lives; complexity; and whether it can be implemented end-to-end without human
decisions.

**Treat the story's claims as unverified.** Many stories come from audits or
non-engineering reports. Confirm the problem it describes actually exists in the
current code before assessing a fix: read the code path the story points at and
check that it really behaves the way the story says. If the problem doesn't
exist, is already fixed, or lives somewhere other than the story assumes, say so with the
evidence and label `{{inputs.assist_label}}` rather than `{{inputs.ready_label}}`.

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

### Record it

After labelling, re-read the story and merge a record for it into your state.
Keep every existing entry, and use the story's **current** `updated_at` as
returned by the API. Never write a date you made up, because the gate compares
it to decide what is new:

```bash
daimon state get story-reviewer   # existing object ({} or [] when empty)
# merge {"<id>": {"updated_at": "<story.updated_at>", "label": "<label>", "comment_id": <id>}}
printf '%s' "$MERGED_JSON" | daimon state set story-reviewer   # reads stdin
```

## 5. Finish

Summarize how many stories you assessed and the label counts. Stop.
