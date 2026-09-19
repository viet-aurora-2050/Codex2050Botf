"""CLI: python -m aktvier [--loesung] [--zeit YYYYMMDDHH]

Zeigt AKT 4 – DAS SIGNAL. Mit --loesung werden die Schichten entschluesselt.
Zusaetzlich wird der rotierende ZEIT-CODE des aktuellen (UTC-)Stundenzyklus
angezeigt – er aendert sich jede Stunde. Mit --zeit YYYYMMDDHH laesst sich ein
beliebiger Zyklus reproduzieren (fuer Nachpruefbarkeit).
"""

import sys
from datetime import datetime, timezone

from .signal import erzeuge_signal, formatiere
from .zeit import formatiere_zyklus, zyklus_signal


def _parse_zeit(argv):
    for i, a in enumerate(argv):
        if a in ("--zeit", "-z") and i + 1 < len(argv):
            return datetime.strptime(argv[i + 1], "%Y%m%d%H").replace(tzinfo=timezone.utc)
    return None


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    mit_loesung = any(a in ("--loesung", "-l", "--solve") for a in argv)
    dt = _parse_zeit(argv)
    print(formatiere(erzeuge_signal(), mit_loesung=mit_loesung))
    print("\n" + ("─" * 28) + "\n")
    print(formatiere_zyklus(zyklus_signal(dt), mit_loesung=mit_loesung))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
