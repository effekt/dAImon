## What & why

<!-- What does this change do, and what problem does it solve? -->

## How to verify

<!-- Steps a reviewer can run: commands, a daemon to `daimon run`, expected output. -->

## Checklist

- [ ] `make check` passes (test + lint + typecheck + docs/link checks)
- [ ] Reviewed the docs this change affects (README, CONTRIBUTING, `docs/`) and
      updated them; ran `make docs` if a daemon changed
- [ ] No secrets or machine-local config committed (`*.local.toml`, tokens, `.env`)
