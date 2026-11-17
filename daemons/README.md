# Your own daemons

This folder holds daemons that belong to you on this machine: ones you wrote
with `daimon scaffold <slug>` or `daimon new`, and private `<slug>.local`
daemons. Everything here except this README is gitignored, so it never
reaches dAImon's repo.

A daemon here is **ejected**: it is always active (unless listed in
`[daemons].disabled`) and takes precedence over a daemon with the same slug in
[`catalog/`](../catalog/) or a pack.

dAImon's shared daemons live in [`catalog/`](../catalog/); team daemons live in
a pack. See [docs/catalog.md](../docs/catalog.md).
