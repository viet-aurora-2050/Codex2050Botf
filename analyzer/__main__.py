"""CLI: python -m analyzer "einzahlung=100 bonus=100% faktor=30 zeit=3 einsatz=1"

Funktioniert vollstaendig offline, ohne Telegram-Token oder API-Key.
"""

import sys

from .bonus import analysiere, formatiere
from .parser import parse

BEISPIEL = "einzahlung=100 bonus=100% faktor=30 basis=b rtp=0.96 zeit=3 einsatz=1"


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    text = " ".join(argv).strip()

    if not text or text in ("-h", "--help", "help"):
        print("Casino-Bonus- und Umsatz-Analytiker (CLI)\n")
        print("Nutzung:")
        print('  python -m analyzer "einzahlung=100 bonus=100% faktor=30 zeit=3 einsatz=1"\n')
        print("Parameter (Auszug):")
        print("  einzahlung=  bonus=(Betrag oder %)  faktor=  basis=b|db|d")
        print("  rtp=0.96  zeit=(Tage)  einsatz=  fs_gewinn=  fs_faktor=")
        print("  maxgewinn=  maxeinsatz=  deckel=  spins=  stunden=  waehrung=EUR\n")
        print(f"Beispiel:\n  python -m analyzer \"{BEISPIEL}\"")
        return 0 if not text else 0

    try:
        szenario, hinweise = parse(text)
    except ValueError as exc:
        print(f"Fehler: {exc}")
        print(f"Beispiel: python -m analyzer \"{BEISPIEL}\"")
        return 1

    ergebnis = analysiere(szenario)
    print(formatiere(ergebnis, szenario))
    if hinweise:
        print("\nHinweise zur Eingabe:")
        for h in hinweise:
            print(f"  - {h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
