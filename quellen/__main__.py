"""CLI: python -m quellen "Behauptung ..."  – prüft auf Marketing-Reizwörter."""

import sys

from .prinzip import Quellenkette, formatiere


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print('python -m quellen "Slot XY zahlt jetzt und ist heiss"')
        return 0
    print(formatiere(Quellenkette(behauptung=" ".join(argv))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
