---
name: datadog-log-reviewer
description: Review recent Datadog error logs, cluster them by root cause, and file one Shortcut story per new cluster for triage.
---

# datadog-log-reviewer

Turn recent Datadog errors into tracked, actionable work. Each run: pull the
error logs, group them into root-cause clusters, and file **one Shortcut story
per new cluster** — which `story-reviewer` then assesses and `work-queue` can
implement. You run inside the service's repo, so you can look up the code a stack
trace points at.

This is **unattended** — never use AskUserQuestion and never stop waiting on
permission; you run with permissions skipped. Do the work within the bounds
below.

## 1. Pull the errors

Search Datadog for the window (see **Source: Datadog** below for the exact `pup`
command and clustering guidance):

```bash
pup logs search --query="{{inputs.log_query}}" --from="{{inputs.lookback}}" --output json
```

If the search returns nothing (auth lapsed, transient failure), stop — there is
nothing to file.

## 2. Cluster by root cause

Group the raw events into **clusters** by a stable signature (normalized message
+ `service` + error `type`/top stack frame — see the Source section). Record for
each cluster: a short title, the signature, occurrence count in the window, one
representative sample (message + stack + a couple of key attributes), the
service, and the environment.

## 3. Dedupe against what you've already filed

`$DAIMON_STATE_FILE` is your durable JSON memory: an array of
`{signature, story_id, title, last_seen}`. Read it first.

- A cluster whose signature you've already filed is **known** — do not file a
  second story. (Optionally note it recurred by updating `last_seen`; never open
  a duplicate.)
- A cluster with a new signature is a **candidate**.

## 4. File a story per new cluster

Process at most `{{inputs.max_new_stories}}` new clusters this run (highest
occurrence count first); leave the rest for the next run. For each:

1. **Investigate briefly.** The stack/source location usually names a file — open
   it in the repo and read enough to describe the likely cause. Do not attempt a
   fix here; that's `work-queue`'s job downstream.
2. **Create a Shortcut story** via `POST /api/v3/stories` (base URL + token header
   are in **Source: Shortcut** below; verify field names against the API). Set its
   workflow state to the triage state (`{{inputs.triage_state}}` — resolve its
   `workflow_state_id`) and give it **no** assessment label, so `story-reviewer`
   picks it up. Body:

   ```markdown
   {{inputs.bot_marker}} **Datadog error — <service> (<env>)**

   **Signature:** <normalized signature>
   **Occurrences:** <n> in the last {{inputs.lookback}}

   **Sample**
   ```
   <representative message + stack>
   ```

   **Likely cause:** <what you found in the code — file:line if identified>
   **Datadog:** <a link/query to view these logs>
   ```

   Keep the title short and specific: `<service>: <error type> in <area>`.

## 5. Finish

Append each filed cluster as `{signature, story_id, title, last_seen}` to
`$DAIMON_STATE_FILE`. Summarize briefly: each cluster, its occurrence count, and
the story you opened (or "known — skipped").
