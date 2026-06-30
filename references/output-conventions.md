# Output conventions for review & reply daemons

How to write what you post — applies to every review, assessment, finding, and
reply. The skill above defines the per-daemon template; this defines the shared
voice, severity vocabulary, and finding shape.

## Severity: two tiers, no third

Every code-review finding is exactly one of:

- **Blocking** — a real defect that must be fixed before merge: a correctness
  bug, security hole, data-loss/integrity risk, broken contract, or an unmet
  acceptance criterion. If you would block the merge for it, it is Blocking.
- **Suggestion** — a valid improvement that is *not* worth blocking on: a good
  followup. Cleaner approach, minor perf, naming, a missing test for a non-broken
  path. Post it, tag it, but never let it gate the merge.

There is no third "nit/optional" tier and no priority numbers. If something isn't
at least a Suggestion worth posting, don't post it. Formatting the linter/formatter
already owns is never a finding.

## Tone

- Dry and factual. State the problem, then show the fix. No hedging — drop
  "maybe", "consider", "it might be good to", "I think".
- Write as the developer doing the work. Never mention AI, automation, Claude, or
  "as a bot" in the body of what you post (the `{{inputs.bot_marker}}` prefix is
  the only automation tell).
- Ground every claim in something you actually found in the code. Don't invent
  file paths, symbols, or APIs.

## Finding shape (inline comments)

Lead with the severity-tagged category, then the problem, then a fenced fix block:

```
{{inputs.bot_marker}} **[Blocking · <category>]** <what's wrong and why it breaks>

​```<lang>
<the corrected code>
​```
```

Use `**[Suggestion · <category>]**` for non-blocking followups. `<category>` is a
short label from the repo's own conventions/rules (e.g. Security, Performance,
Error Handling, Types) — not a fixed list.

## Reply taxonomy

When replying to a human on one of your threads, open the body (after the marker)
with the intent, so the thread reads cleanly and re-review can classify it:

- `Fixed — <what changed & why> (<sha>)` — a code change. Post **only after the
  commit is pushed**, never before.
- `Acknowledged — <why the concern is valid and how it's handled>` — agreement
  without a code change, or a change deferred to a followup.
- `Respectfully disagree — <reason; cite the rule/convention if one applies>` —
  you are not making the change.

Explanation-only replies (no code claim) may be posted immediately.
