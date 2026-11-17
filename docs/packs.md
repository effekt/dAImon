# Packs: share a team's setup

dAImon's own repo holds generic daemons. A team's real setup (its private
daemons, the settings everyone shares, its Slack runbooks) belongs in a repo the
team owns, not in gitignored `*.local.toml` files on one machine. A **pack** is
that repo: a folder dAImon loads alongside its own.

```toml
# ~/.config/daimon/daimon.toml
[packs]
paths = ["~/work/daimon-team"]
```

## Layout

Every folder is optional.

```
daimon-team/
  daemons/<slug>/       whole daemons, exactly like dAImon's daemons/<slug>
  overrides/<slug>.toml team settings for any daemon: [daemon] and [inputs]
  profiles/<name>.toml  team [defaults] for a source profile
  commands/*.md         slack-commands runbooks
  .gitignore            *.local.toml
```

## How settings layer

Last wins:

- **Daemon:** `daemon.toml` → `overrides/<slug>.toml` (each pack, in `paths`
  order) → `daemon.local.toml`.
- **Profile:** `profile.toml` → `profiles/<name>.toml` → `profile.local.toml`.

Put what everyone on the team shares in the pack: the log query, the epic,
labels, the `role`. Keep what is yours (your member ID, your schedule) in
`daemon.local.toml`. For a pack daemon that file sits beside its `daemon.toml`,
gitignored by the pack.

## Daemons in a pack

- A slug defined in two places (dAImon and a pack, or two packs) is a validation
  error.
- `disabled` works the same.
- State and logs are keyed by slug, so moving a daemon into a pack keeps its
  history.
- A pack daemon's gate can't reach dAImon's libraries with a relative path.
  `run.sh` exports `DAIMON_INSTALL_ROOT` and `DAIMON_DAEMON_DIR`:

  ```bash
  source "$DAIMON_INSTALL_ROOT/lib/common.sh"
  source "$DAIMON_INSTALL_ROOT/profiles/shortcut/lib.sh"
  source "$DAIMON_DAEMON_DIR/lib.sh"
  ```

- In a skill, `{{daemon_dir}}` renders as the daemon's absolute folder, for
  scripts it ships.

## Adding a daemon to a pack

`daimon new --pack` (Claude interviews you) or `daimon scaffold <slug> --pack`
(a skeleton) creates it in the first pack's `daemons/`; give `--pack <dir>` to
pick another. The skeleton's gate already sources dAImon's libraries through
`$DAIMON_INSTALL_ROOT`, and skips every run until you write it. Commit it in the
pack's repo, and teammates get it on their next `daimon sync`. It runs on a
machine only once someone registers it there.

A pack daemon can ship `doctor.sh` for its own needs
([writing a daemon](writing-a-daemon.md#4-doctorsh-optional)). A pack is kept
current by `daimon sync`, which runs hourly through `daimon update` when
`[update] auto` is on.

## Runbooks

slack-commands reads `commands/` in every pack, after its shared runbooks and
before your `commands.local/`. Scaffold one into a pack with
`daimon command new <name> --pack <dir>`.

## Commands

- `daimon packs` lists each pack and what it adds.
- `daimon sync` fast-forwards each pack that is a clean git checkout, then
  re-renders as usual. It never loads a daemon that wasn't registered, so a pack
  adding daemons doesn't start anything until you choose them (`daimon init`, or
  `r` in the TUI).
