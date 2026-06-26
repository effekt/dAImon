import sys

from .sync import main as sync_main


def main(argv: list[str]) -> int:
    if argv and argv[0] == "sync":
        return sync_main(argv[1:])
    print("usage: python -m daimon sync", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
