## Source: Shortcut — writing (triage/implementation)

These operations **change** stories. They apply only to daemons that triage or
implement stories; a read-only daemon never uses them.

Assessment is conveyed by **labels** (visible as chips in Shortcut), not by moving
the story:

- `{{inputs.ready_label}}` — AI-completable, ready for autonomous implementation.
- `{{inputs.assist_label}}` — needs human input first.
- `{{inputs.human_label}}` — needs a human; not for automation.
- `{{inputs.priority_label}}` — process before anything else.
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

The search `query` supports `state:"…"`, `label:"…"`, `team:"…"`, `owner:`, and
negation with `!`. Each result has `id`, `name`, `description`, `app_url`, and its
current `labels`.

### Scope — only act on the owner's stories

A story is in scope only if `{{inputs.owner}}` is its requester **or** one of its
owners. If `{{inputs.owner}}` is blank, every story is in scope. Anything where
`{{inputs.owner}}` is neither requester nor in `owner_ids` belongs to someone
else — never comment on, label, or follow it.

Fetch already scoped on the server — do not pull the whole triage column and trust
yourself to filter it down. `owner:`/`requester:` take the member's @mention name,
not the id, so resolve it once (`GET /api/v3/members/{{inputs.owner}}` →
`profile.mention_name`), then run two searches and merge by story id:

```bash
MENTION=$(curl -s "https://api.app.shortcut.com/api/v3/members/{{inputs.owner}}" \
  -H "Shortcut-Token: $TOKEN" | python3 -c "import sys,json;print((json.load(sys.stdin).get('profile') or {}).get('mention_name',''))")
for op in owner requester; do
  curl -s -G https://api.app.shortcut.com/api/v3/search/stories \
    --data-urlencode "query=$op:$MENTION state:\"{{inputs.triage_state}}\" !label:\"{{inputs.skip_label}}\"" \
    -H "Shortcut-Token: $TOKEN"
done
```

**Safety net — re-check before every write.** Even with the scoped queries above,
before you comment on, label, or otherwise touch a story, re-read it and confirm
`requested_by_id == {{inputs.owner}}` OR `{{inputs.owner}}` is in `owner_ids`
(these are member ids, so the check is exact). If not, skip it and log
`[out-of-scope skip] sc-{id} requester={…} owners={…}` — do not write anything.

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

### Move a story between states (claim / hand off)

Look up the numeric `workflow_state_id` for a state name via
`GET /api/v3/workflows`, then `PUT /api/v3/stories/{id}` with
`{"workflow_state_id": <id>}`.

### Create a story

`POST /api/v3/stories` with `{"name", "description", "workflow_state_id"}` (resolve
the id for `{{inputs.triage_state}}` from `GET /api/v3/workflows`). Leave off any
assessment label so a triage daemon still picks it up. Set `group_id`/`team` and
`requested_by_id` if your workflow needs them.

```bash
STATE=$(curl -s https://api.app.shortcut.com/api/v3/workflows -H "Shortcut-Token: $TOKEN" \
  | python3 -c "import sys,json;print(next(s['id'] for w in json.load(sys.stdin) for s in w['states'] if s['name']=='{{inputs.triage_state}}'))")
curl -s -X POST https://api.app.shortcut.com/api/v3/stories -H "Shortcut-Token: $TOKEN" \
  -H "Content-Type: application/json" -d "{\"name\":\"…\",\"description\":\"…\",\"workflow_state_id\":$STATE}"
```
