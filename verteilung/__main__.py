"""CLI: python -m verteilung 5 "0:0.7, 2:0.2, 5:0.1"

Arg 1: Einsatz. Arg 2 (optional): Verteilung als "mult:P, mult:P".
Ohne Verteilung: Zielbetraege, aber „Probability unavailable".
"""

import sys

from .vert import Verteilung, multiplikator_analyse


def _parse(s: str):
    paare = []
    for t in (s or "").replace(";", ",").replace("\n", ",").split(","):
        if ":" in t:
            a, b = t.split(":", 1)
            try:
                paare.append((float(a.replace(",", ".")), float(b.replace(",", "."))))
            except ValueError:
                pass
    return Verteilung(paare) if paare else None


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print('python -m verteilung <einsatz> ["mult:P, mult:P"]')
        print('Beispiel: python -m verteilung 5 "0:0.7, 2:0.2, 5:0.1"')
        return 0
    einsatz = float(argv[0].replace(",", "."))
    v = _parse(argv[1]) if len(argv) > 1 else None
    r = multiplikator_analyse(v, einsatz)
    print("RETURN MULTIPLIER ANALYSIS · Einsatz", einsatz)
    print("Zielbetraege:", {f"{int(k)}x": b for k, b in r["betraege"].items()})
    if r["wahrscheinlichkeiten"] is None:
        print("Probability unavailable —", r["grund"])
    else:
        print(f"EV={r['ev']*100:.1f}% · Hausvorteil={r['hausvorteil']*100:.1f}% · SD={r['std']:.2f}")
        print("P(>=k):", {f"{int(k)}x": f"{p*100:.2f}%" for k, p in r["wahrscheinlichkeiten"].items()})
    print("Naechster Spin: NICHT VORHERSAGBAR. Mathematical scenario only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
