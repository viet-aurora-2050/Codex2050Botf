"""CLI: python -m traeger verlust=2 isolation=3 loyalitaet=1 erinnerung=3

Werte je Achse 0..3 (Selbstauskunft). Fehlende Achsen = 0.
"""

import re
import sys

from .protokoll import bewerte, formatiere

_ALIAS = {
    "verlust": "verlust", "v": "verlust",
    "isolation": "isolation", "i": "isolation",
    "loyalitaet": "loyalitaet", "loyalität": "loyalitaet", "l": "loyalitaet",
    "erinnerung": "erinnerung", "e": "erinnerung",
}
_PAAR = re.compile(r"([a-zA-Zä]+)\s*[=:]\s*([0-9.,]+)")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    text = " ".join(argv)
    if not text or text in ("-h", "--help", "help"):
        print("TRÄGER-PROTOKOLL // ∆1 (freiwilliger Selbst-Check)\n")
        print('  python -m traeger verlust=2 isolation=3 loyalitaet=1 erinnerung=3')
        print("\n  Werte 0..3 je Achse (0 = nie, 3 = fast immer).")
        return 0
    werte = {"verlust": 0.0, "isolation": 0.0, "loyalitaet": 0.0, "erinnerung": 0.0}
    for k, v in _PAAR.findall(text):
        key = _ALIAS.get(k.lower())
        if key:
            try:
                werte[key] = float(v.replace(",", "."))
            except ValueError:
                pass
    print(formatiere(bewerte(**werte)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
