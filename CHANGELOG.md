# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `daimon init [slug ...]` — choose which daemons run on this machine (the rest go to
  `[daemons].disabled`) and scaffold their machine-local config from the tracked
  `*.example` files. Bare invocation prompts interactively.
- `daemon.local.toml.example` for every daemon and `profiles/shortcut/profile.local.toml.example`.
- Configurable output for the review/reply daemons: `review_mode`
  (`approve` | `request_changes` | `comment`) and `verbosity` (`full` | `compact`),
  a shared `references/output-conventions.md` (severity tiers, tone, reply taxonomy),
  and structured review bodies with a findings table.
- Contributor scaffolding: `CONTRIBUTING.md`, issue/PR templates, README badges,
  a Prerequisites section, and a macOS-only note.

### Changed
- `review-prs`: `review_mode` replaces `auto_approve`; non-blocking suggestions no
  longer force `REQUEST_CHANGES`.
- `doctor` now reports the platform and prints config-validation errors inline.
- TUI config editor and detail view now separate daemon-owned inputs from
  profile-provided fields; editing a profile field writes to the shared
  `profiles/<name>/profile.local.toml` instead of the daemon's local file.

### Fixed
- TUI config save no longer copies profile defaults (owner, team, labels…) into
  each daemon's `daemon.local.toml`, which caused per-daemon divergence.
- `story-reviewer` now marks its comments with the bot marker, so
  `reply-to-story-comments` can find and reply to them.

## [0.1.0]

Initial release — the launchd-scheduled daemon runner, the `claude` backend, the
Textual TUI, and the reference daemons (`pr-manager`, `review-prs`, `work-queue`,
`story-reviewer`, `reply-to-pr-comments`, `reply-to-story-comments`).
