"""CLI: python -m aktvier [--loesung]

Zeigt AKT 4 – DAS SIGNAL. Mit --loesung werden die vier Schichten entschluesselt.
"""

import sys

from .signal import erzeuge_signal, formatiere


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    mit_loesung = any(a in ("--loesung", "-l", "--solve") for a in argv)
    print(formatiere(erzeuge_signal(), mit_loesung=mit_loesung))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
