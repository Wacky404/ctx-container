"""
ctx __main__ hook
"""

from ctx.cli import ctx


def main() -> None:
    ctx()


if __name__ == "__main__":
    main()
