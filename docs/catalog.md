# The catalog: choosing your daemons

dAImon is the shell: the framework, backends, source profiles, TUI and skills.
Daemons come from a **catalog**, and each machine picks the ones it runs.

## Where daemons come from

| Folder | What it holds | In git |
|--------|---------------|--------|
| `catalog/` in the dAImon install | dAImon's own generic daemons ([index](../catalog/README.md)) | yes, tested by dAImon's CI |
| `daemons/` in each [pack](packs.md) | a team's daemons | in the pack's repo |
| `daemons/` in the dAImon install | your own daemons, and private `<slug>.local` ones | no (only its README) |

dAImon's `catalog/` and every pack's `daemons/` are catalogs: they offer daemons
you can install. The install's own `daemons/` is different: a daemon there is
yours, active as soon as it exists, and takes precedence over a catalog daemon of
the same slug (an **ejected** copy).

Team-specific daemons (a team's systems, channels, IDs, workflow) belong in a
pack, never in `catalog/`.

## Installed, registered, active

- **Installed:** listed in `[daemons].installed` in `~/.config/daimon/daimon.toml`.
- **Active:** installed, plus your own daemons in `daemons/`, minus
  `[daemons].disabled`. Active daemons are what `daimon sync` renders, `daimon
  validate` checks, and `daimon daemons` / the TUI list.
- **Registered:** has a launchd plist, so launchd schedules it. Installing never
  registers: select the daemon in `daimon tui` and press `r`.

A daemon found in two catalogs (dAImon and a pack, or two packs) is a validation
error unless you have your own copy in `daemons/`, which settles it. An installed
slug that no catalog offers is a validation error too: `daimon remove` it.

## Commands

```bash
daimon catalog                 # every daemon you can install: source, state, description
daimon add <slug>…             # install: add to `installed`, scaffold personal settings, sync
daimon remove <slug>…          # unregister (asks first if loaded; --yes skips) and uninstall
daimon init [slug…]            # choose the whole set at once (multi-select without slugs)
daimon scaffold <slug>         # write a new daemon of your own into daemons/
```

`daimon add` copies the daemon's `daemon.local.toml.example` (and its source
profiles' `profile.local.toml.example`) to `~/.config/daimon/` when you have no
settings file yet; edit `working_dir` and any inputs there. It edits
`daimon.toml` in place, keeping your comments and other settings. `daimon remove`
keeps your personal settings, so adding the daemon back picks them up again.

## Installs from before the catalog

dAImon's daemons used to live in `daemons/`, and every one of them was active
unless listed in `disabled`. With no `installed` key, dAImon still behaves that
way: every catalog daemon not in `disabled` counts as installed. So a scheduled
job that fires between an update's `git merge` and its migration runs exactly as
before.

`daimon install` (which every self-update runs) and `daimon init` then run
`daimon migrate`, which:

- writes `installed` as that active set, once, leaving `disabled` as it is;
- moves the gitignored `daemon.local.toml` files the move left in
  `daemons/<slug>/` to `~/.config/daimon/daemons/<slug>.toml`, and your
  slack-commands runbooks from `daemons/slack-commands/commands.local/` to
  `~/.config/daimon/commands/`;
- removes a `daemons/<slug>/` folder left holding only migration stubs and caches.

Slugs, state, logs and launchd plists don't change, so registered jobs keep
running. Private `daemons/<slug>.local` daemons were already where your own
daemons live, and keep working unchanged.
