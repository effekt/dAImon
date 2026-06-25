"""Example programmatic daemon registration.

This is a SAMPLE, not your live config — `daimon sync` does NOT read it unless you
pass it explicitly: `daimon sync examples/daemons.py`. Doing so compiles each
registration into a daemons/<slug>/ folder, so use throwaway example-* slugs here
to avoid overwriting real daemons.
"""
from daimon import Daimon

app = Daimon()


@app.daemon(
    slug="example-review",
    backend="claude",
    schedule="20m",
    working_dir="~/code/example-repo",
    inputs={"filter": "review-requested:@me"},
)
def example_review(ctx) -> bool:
    return ctx.gh_count(ctx.inputs["filter"]) > 0


# One daemon per repo — drive many repositories from one definition.
REPOS = ["app", "api", "web"]

for _repo in REPOS:
    @app.daemon(
        slug=f"example-review-{_repo}",
        backend="claude",
        schedule="30m",
        working_dir=f"~/code/{_repo}",
        inputs={"filter": "review-requested:@me"},
    )
    def _review(ctx) -> bool:
        return ctx.gh_count(ctx.inputs["filter"]) > 0
