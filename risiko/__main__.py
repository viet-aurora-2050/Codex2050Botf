"""CLI: python -m risiko budget=100 einsatz=1 spins=500 rtp=0.96 vola=mittel"""

import re
import sys

from .analyse import RisikoSzenario, Volatilitaet, analysiere, formatiere

_VOLA = {"niedrig": Volatilitaet.NIEDRIG, "low": Volatilitaet.NIEDRIG,
         "mittel": Volatilitaet.MITTEL, "mid": Volatilitaet.MITTEL,
         "hoch": Volatilitaet.HOCH, "high": Volatilitaet.HOCH}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    text = " ".join(argv)
    if not text or text in ("-h", "--help", "help"):
        print("PERSONAL-RISIKO-ANALYSE (aus oeffentlichen Fakten)\n")
        print("  python -m risiko budget=100 einsatz=1 spins=500 rtp=0.96 vola=mittel")
        print("\n  vola = niedrig | mittel | hoch")
        return 0
    s = RisikoSzenario()
    for k, v in re.findall(r"([a-zA-Z]+)\s*[=:]\s*([\w.,]+)", text):
        k = k.lower()
        try:
            if k in ("budget", "guthaben"):
                s.budget = float(v.replace(",", "."))
            elif k in ("einsatz", "bet"):
                s.einsatz = float(v.replace(",", "."))
            elif k in ("spins", "runden"):
                s.spins = int(float(v))
            elif k == "rtp":
                r = float(v.replace(",", "."))
                s.rtp = r / 100 if r > 1.5 else r
            elif k in ("vola", "volatilitaet", "volatility"):
                s.volatilitaet = _VOLA.get(v.lower(), s.volatilitaet)
        except ValueError:
            pass
    print(formatiere(analysiere(s), s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
