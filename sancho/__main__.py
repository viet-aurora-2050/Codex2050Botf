"""CLI: python -m sancho [anbieter] [einsatz]

Beispiele:
    python -m sancho betano
    python -m sancho "tipico games" 2
"""

import sys

from .spielplatz import erzeuge, formatiere


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    anbieter = argv[0] if argv else "generisch"
    einsatz = 1.0
    if len(argv) > 1:
        try:
            einsatz = float(argv[1].replace(",", "."))
        except ValueError:
            pass
    ergebnis = erzeuge(anbieter=anbieter, einsatz=einsatz)
    print(formatiere(ergebnis))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
