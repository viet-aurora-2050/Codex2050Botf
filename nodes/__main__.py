"""CLI: python -m nodes [node]

Beispiele:
    python -m nodes orpheus
    python -m nodes "node 7"
    python -m nodes            # ALEXANDRA (Standard)
    python -m nodes --alle     # alle Stimmen nacheinander
"""

import sys

from .transmission import NODES, formatiere, sende


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv and argv[0] in ("--alle", "-a", "all"):
        for key in NODES:
            print(formatiere(sende(key)))
            print()
        return 0
    node = " ".join(argv) if argv else "alexandra"
    print(formatiere(sende(node)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
