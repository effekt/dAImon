import os
import sys
from pathlib import Path

from .gate import Ctx
from .sync import load_app


def _gate(slug: str) -> int:
    module_path = os.environ.get("DAIMON_DAEMONS_MODULE")
    if not module_path:
        print("DAIMON_DAEMONS_MODULE not set", file=sys.stderr)
        return 2
    app = load_app(Path(os.path.expanduser(module_path)))
    spec = app.specs.get(slug)
    if spec is None:
        print(f"no registered daemon: {slug}", file=sys.stderr)
        return 2
    return 0 if spec.fn(Ctx(spec.inputs)) else 1


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "gate":
        return _gate(argv[1])
    if argv and argv[0] == "sync":
        from .sync import main as sync_main
        return sync_main(argv[1:])
    print("usage: python -m daimon <gate <slug> | sync [module]>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
