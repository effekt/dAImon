# Second opinion (Codex)

This daemon runs with OpenAI **Codex** attached as a second reviewer, exposed
through the `mcp__codex__codex` MCP tool. Use it as an independent check on your
own conclusions — two models catch more than one, and a point both raise is
high-signal.

## When to consult Codex

Before you finalize the judgment this skill exists to produce — a PR review
verdict, a pre-PR self-review, a fix you are about to push, or a work-item
assessment/label — get a Codex pass first. Skip it only when the change is INERT
(comments / strings / docs / tests, no logic) or the item is trivial; it is not
worth the latency there.

## How to run it

Call `mcp__codex__codex` **once**, with a read-only sandbox, handing Codex the
same context you worked from and asking for an independent take:

- **Reviewing a change** — give it the diff (`gh pr diff <n>`, `git diff`) and
  ask: "Review this diff for correctness bugs, security issues, and clear quality
  problems. Report each as `file:line — [category] problem`, or `No findings.`
  Be conservative — only high-confidence issues."
- **Assessing a work item** — give it the item text and the code areas you found,
  and ask for its own read: feasibility, complexity, affected areas you may have
  missed, and whether it is fully specified or needs human input.

Sandbox **read-only**: Codex analyzes, never edits, fetches, or runs anything.

## Merging its take

Fold Codex's take into your own before this skill's verdict/label step:

- A finding **either** of you raises with high confidence stands — include it.
- A point **both** raise is confirmed — weight it accordingly.
- Dedupe overlap (same `file:line` + issue, or the same concern) into one.
- You remain the decider: apply this skill's own rules to the merged result. Do
  not defer the final call to Codex.

## When Codex is unavailable (fallback)

Codex is a bonus, never a blocker.

- **Retry once** on a transient failure (empty result, timeout, network error).
- If it still fails — or the error mentions a **usage / quota limit**, which will
  not clear on retry — proceed with your own analysis alone. Do not defer,
  re-queue, or skip the item.
- When you post something that would normally carry a Codex pass but did not, note
  it briefly: `_Single-agent — Codex unavailable this run._`
