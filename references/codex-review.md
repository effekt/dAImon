# Second opinion (Codex)

This daemon runs with OpenAI **Codex** attached as a second reviewer, exposed
through the `mcp__codex__codex` MCP tool. Use it as an independent check on the
code you review or write — two models catch more than one, and a finding both
agents raise is high-signal.

## When to consult Codex

Whenever a step above has you **review a diff or finalize a code change** — a PR
review verdict, a pre-PR self-review, or a fix you are about to push — get a
Codex pass first, **unless** the change is INERT (only comments / strings / docs
/ tests, no logic). Skip Codex for INERT diffs; it is not worth the latency.

## How to run it

Call `mcp__codex__codex` **once**, with a read-only sandbox and a prompt that
hands Codex the diff and asks for findings:

- Prompt shape: "Review the diff below for correctness bugs, security issues, and
  clear quality problems. Report each finding as `file:line — [category] problem`,
  or `No findings.` Be conservative — only high-confidence issues. \<diff\>"
- Give it the same diff you reviewed (`gh pr diff <n>`, `git diff`, etc.).
- Sandbox **read-only**: Codex analyzes, never edits, fetches, or runs anything.

## Merging findings

Fold Codex's findings into your own before this skill's verdict/decision step:

- A finding **either** agent raises with high confidence stands — include it.
- A finding **both** raise is confirmed — weight it accordingly.
- Dedupe overlap (same `file:line` + issue) into one finding.
- You remain the decider: apply this skill's own severity and verdict rules to
  the merged set. Do not defer the final call to Codex.

## When Codex is unavailable (fallback)

Codex is a bonus, never a blocker.

- **Retry once** on a transient failure (empty result, timeout, network error).
- If it still fails — or the error mentions a **usage / quota limit**, which will
  not clear on retry — proceed with your own analysis alone. Do not defer,
  re-queue, or skip the item.
- When you post a review or PR that would normally carry a Codex pass but did
  not, note it briefly: `_Single-agent review — Codex unavailable this run._`
