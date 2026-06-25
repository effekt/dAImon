# TUI design

The control panel (`tui/`) follows established terminal-UI conventions. When
changing it, install one of these design skills and let it guide the work — they
are dev-time aids, not dependencies, so dAImon does not bundle them:

- [gfargo/tui-design-skill](https://github.com/gfargo/tui-design-skill) (MIT) —
  `/plugin marketplace add gfargo/tui-design-skill` then
  `/plugin install tui-design@tui-design-marketplace`.
- [hyperb1iss/hyperskills · tui-design](https://github.com/hyperb1iss/hyperskills/blob/main/skills/tui-design/SKILL.md).

## Principles the panel follows

- **Two fixed panes** — a left daemon list and a right detail panel, in fixed
  positions; rounded bordered, titled.
- **Focus shows in the border** — the focused pane's border switches to the accent
  colour.
- **Status by symbol + text, never colour alone** — list glyphs (`●` running,
  `▷` loaded, `◌` registered, `·` none) and detail rows (`✓`/`·`, `● running` /
  `— idle`) stay legible under `NO_COLOR`.
- **Semantic theme tokens** — colours come from Textual theme variables
  (`$accent`, `$surface-lighten-2`, …), not hardcoded hex, so the panel tracks the
  active theme.
- **Minimal footer + `m` menu** — only the primary actions sit in the footer; the
  rest live behind the manage menu while their hotkeys still fire globally.
