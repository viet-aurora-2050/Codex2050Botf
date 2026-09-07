"""CLI: python -m gewinner  – zeigt die dokumentierten Faelle + Lehre."""

from .faelle import formatiere


def main() -> int:
    print(formatiere())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
