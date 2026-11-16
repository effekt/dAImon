## Source: Shortcut — writing (triage/implementation)

These operations **change** stories. They apply only to daemons that triage or
implement stories; a read-only daemon never uses them.

Assessment is conveyed by **labels** (visible as chips in Shortcut), not by moving
the story:

- `{{inputs.ready_label}}` — AI-completable, ready for autonomous implementation.
- `{{inputs.assist_label}}` — needs human input first.
- `{{inputs.human_label}}` — needs a human; not for automation.
- `{{inputs.priority_label}}` — process before unlabelled stories (see
  **Priority order**).
- `{{inputs.skip_label}}` — never auto-process.

Workflow states: triage = `{{inputs.triage_state}}`, in-progress =
`{{inputs.in_progress_state}}`, done = `{{inputs.done_state}}`. Team:
`{{inputs.team}}`.

### Find stories

```bash
TOKEN="${SHORTCUT_API_TOKEN:-$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.config/shortcut-cli/config.json')))['token'])")}"
curl -s -G https://api.app.shortcut.com/api/v3/search/stories \
  --data-urlencode 'query=label:"{{inputs.ready_label}}" !label:"{{inputs.skip_label}}"' \
  -H "Shortcut-Token: $TOKEN"
```

The search `query` supports `state:"…"`, `label:"…"`, `team:"…"`, `owner:`,
`epic:<id>`, `objective:<id>`, state types (`is:backlog`, `is:unstarted`,
`is:started`, `is:done`), and negation with `!`. Each result has `id`, `name`, `description`,
`app_url`, and its current `labels`.

### Priority order

When choosing among in-scope stories, order them:

1. Stories requested by a member in `{{inputs.priority_requesters}}` (member ids;
   blank means none) — check `requested_by_id`. When several members are listed,
   earlier members come first.
2. Then stories carrying `{{inputs.priority_label}}`.
3. Then the oldest first.

### Out-of-scope epics, objectives and labels

**Excluded epics:** `{{inputs.exclude_epics}}` — blank means none are excluded.
**Excluded objectives:** `{{inputs.exclude_objectives}}` — blank means none.
**Excluded labels:** `{{inputs.exclude_labels}}` — blank means none.

A story carrying an excluded label is out of scope wherever it lives. Shortcut
matches a label term against each word of a label name, so append one
`!label:"<name>"` term per excluded label to every search, and drop any story
whose label names include an excluded label as a whole word (`milestone` covers
`milestone:x:y`).

Any epic listed there, and every epic in a listed objective, is **out of scope**:
another process owns it. Append one `!epic:<id>` term per epic id and one
`!objective:<id>` term per objective id to every search, and drop any story whose
`epic_id` is in the list, or whose epic belongs to a listed objective
(`GET /api/v3/epics/{epic_id}` → `objective_ids`), even if it reaches you another
way. This is scope, not preference — never
comment on, label, or implement a story belonging to an excluded epic.

### Scope — only act on the owner's stories

A story is in scope only if `{{inputs.owner}}` is one of its owners — or, when
**requester counts** (`{{inputs.include_requested}}`) is True, its requester. If
`{{inputs.owner}}` is blank, every story is in scope. Anything else belongs to
someone else — never comment on, label, or follow it.

Fetch already scoped on the server — do not pull the whole triage column and trust
yourself to filter it down. `owner:`/`requester:` take the member's @mention name,
not the id, so resolve it once (`GET /api/v3/members/{{inputs.owner}}` →
`profile.mention_name`), then search `owner:` — plus `requester:` when requester
counts — and merge by story id:

```bash
MENTION=$(curl -s "https://api.app.shortcut.com/api/v3/members/{{inputs.owner}}" \
  -H "Shortcut-Token: $TOKEN" | python3 -c "import sys,json;print((json.load(sys.stdin).get('profile') or {}).get('mention_name',''))")
for op in owner requester; do   # drop requester when requester doesn't count
  curl -s -G https://api.app.shortcut.com/api/v3/search/stories \
    --data-urlencode "query=$op:$MENTION state:\"{{inputs.triage_state}}\" !label:\"{{inputs.skip_label}}\"" \
    -H "Shortcut-Token: $TOKEN"
done
```

**Safety net — re-check before every write.** Even with the scoped queries above,
before you comment on, label, or otherwise touch a story, re-read it and confirm
`{{inputs.owner}}` is in `owner_ids` (or, when requester counts,
`requested_by_id == {{inputs.owner}}`). These are member ids, so the check is
exact. If not, skip it and log
`[out-of-scope skip] sc-{id} requester={…} owners={…}` — do not write anything.

**Status field.** When `{{inputs.status_field}}` is set, also drop any story
whose `{{inputs.status_field}}` custom field holds a value other than these
(blank entries ignored): `{{inputs.status_ready}}`, `{{inputs.status_assist}}`,
`{{inputs.status_claimed}}`, `{{inputs.status_done}}`. Another process drives
that story through the field; log `[status skip] sc-{id} status=<value>` and
write nothing. An unset field is in scope. Searches can't filter on the value,
so this check is yours.

### Comment on a story

`POST /api/v3/stories/{id}/comments` with `{"text": "..."}`.

### Add or remove a label

A story update **replaces** the entire `labels` set — it does not merge. So
read-modify-write: fetch the story's current labels, add (or drop) the one you
want, and PUT the full list. Labels may be given by name.

```bash
# add {{inputs.ready_label}} without losing existing labels:
existing=$(curl -s "https://api.app.shortcut.com/api/v3/stories/<id>" -H "Shortcut-Token: $TOKEN" \
  | python3 -c "import sys,json;print(json.dumps([{'name':l['name']} for l in json.load(sys.stdin)['labels']]))")
# append {"name":"{{inputs.ready_label}}"} to that array, then:
curl -s -X PUT "https://api.app.shortcut.com/api/v3/stories/<id>" -H "Shortcut-Token: $TOKEN" \
  -H "Content-Type: application/json" -d "{\"labels\": <new array>}"
```

### Set the status field

Only when `{{inputs.status_field}}` is non-empty and the value to write is
non-empty. Never write any other value of the field: other processes may act on
it. Resolve ids once from `GET /api/v3/custom-fields` (the field whose `name` is
`{{inputs.status_field}}`; its `values[]` carry `id` and `value`). A story
update **replaces** `custom_fields` too, so read-modify-write: keep every other
`{field_id, value_id}` pair from the story and replace or add this field's pair.

```bash
curl -s -X PUT "https://api.app.shortcut.com/api/v3/stories/<id>" -H "Shortcut-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"custom_fields": [<other pairs…>, {"field_id": "<field id>", "value_id": "<value id>"}]}'
```

### Move a story between states (claim / hand off)

Look up the numeric `workflow_state_id` for a state name via
`GET /api/v3/workflows`, then `PUT /api/v3/stories/{id}` with
`{"workflow_state_id": <id>}`.

### Create a story

`POST /api/v3/stories` with `{"name", "description", "workflow_state_id"}` (resolve
the id for `{{inputs.triage_state}}` from `GET /api/v3/workflows`). Leave off any
assessment label so a triage daemon still picks it up. When `{{inputs.epic_id}}`
is non-empty, set `epic_id` to it so filed stories group under that epic. Set
`group_id`/`team` and `requested_by_id` if your workflow needs them.

```bash
STATE=$(curl -s https://api.app.shortcut.com/api/v3/workflows -H "Shortcut-Token: $TOKEN" \
  | python3 -c "import sys,json;print(next(s['id'] for w in json.load(sys.stdin) for s in w['states'] if s['name']=='{{inputs.triage_state}}'))")
curl -s -X POST https://api.app.shortcut.com/api/v3/stories -H "Shortcut-Token: $TOKEN" \
  -H "Content-Type: application/json" -d "{\"name\":\"…\",\"description\":\"…\",\"workflow_state_id\":$STATE}"
```
