"""CLI: python -m melde anbieter="Beispiel" lizenz=keine einzahlung=300 verlust=300 rtp=0.96

Erzeugt eine faktische Beschwerde/Anzeige an die GGL inkl. mathematischer
Einordnung. Nur wahrheitsgemaesse Angaben verwenden.
"""

import re
import sys

from .anzeige import Lizenz, MeldeSzenario, erstelle, formatiere

_LIZ = {"unbekannt": Lizenz.UNBEKANNT, "keine": Lizenz.KEINE,
        "gueltig": Lizenz.GUELTIG, "gültig": Lizenz.GUELTIG, "valid": Lizenz.GUELTIG}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    text = " ".join(argv)
    if not text or text in ("-h", "--help", "help"):
        print("MELDE-ASSISTENT – Mathematik + Beschwerde/Anzeige an die GGL\n")
        print('  python -m melde anbieter="Name" lizenz=keine einzahlung=300 '
              'verlust=300 rtp=0.96 von=2022-01-01 bis=2022-06-30')
        print("\n  lizenz = unbekannt | keine | gueltig")
        print("  Nur WAHRHEITSGEMAESSE Angaben. Keine Rechtsberatung.")
        return 0
    s = MeldeSzenario()
    # anbieter kann Leerzeichen enthalten -> in Anfuehrungszeichen
    m = re.search(r'anbieter\s*[=:]\s*"([^"]+)"', text)
    if m:
        s.anbieter = m.group(1)
    for k, v in re.findall(r'([a-zA-Zä]+)\s*[=:]\s*([^\s"]+)', text):
        k = k.lower()
        try:
            if k == "anbieter" and not s.anbieter:
                s.anbieter = v
            elif k == "lizenz":
                s.lizenz = _LIZ.get(v.lower(), Lizenz.UNBEKANNT)
            elif k in ("einzahlung", "einzahlung_gesamt"):
                s.einzahlung_gesamt = float(v.replace(",", "."))
            elif k == "verlust":
                s.verlust = float(v.replace(",", "."))
            elif k == "rtp":
                r = float(v.replace(",", ".")); s.rtp = r / 100 if r > 1.5 else r
            elif k in ("von", "zeitraum_von"):
                s.zeitraum_von = v
            elif k in ("bis", "zeitraum_bis"):
                s.zeitraum_bis = v
            elif k == "name":
                s.name = v
            elif k == "ort":
                s.ort = v
            elif k == "einsatz":
                s.einsatz = float(v.replace(",", "."))
            elif k == "spins":
                s.spins = int(float(v))
        except ValueError:
            pass
    print(formatiere(erstelle(s)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
