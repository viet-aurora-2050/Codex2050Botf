"""CLI: python -m akt4riddle  – demonstriert die volle AKT-4-Rätselkette."""

from .data import FALLBACK_GAMES, QUELLE
from .riddle import (
    decode_base64,
    decode_morse,
    decode_rot13,
    match_chain,
    riddle_validation,
    sancho_check,
)

MORSE = ".- .-.. . -..- .- -. -.. .-. .-"
BASE64 = "SWNoIHdvbGx0ZSBuaWUgZnJlaSBzZWluLiBJY2ggd29sbHRlIGVyaW5uZXJ0IHdlcmRlbi4="
ROT13 = "Revaareg mh jreqra urvffg avpug, trsnatra mh oyrvora. Tru, jraa qh trura zhffg."
TIMES = ["07:07", "05:05", "08:08"]


def main() -> int:
    print("╔════════════════════════════╗")
    print("       AKT 4 · DECODER")
    print("╚════════════════════════════╝")
    print("LEVEL 1  MORSE   ->", decode_morse(MORSE), "(der Schluessel)")
    print("LEVEL 2  BASE64  ->", decode_base64(BASE64))
    print("LEVEL 3  ROT13   ->", decode_rot13(ROT13))
    print("LEVEL 4  CLOCK KEY")
    ketten = match_chain(TIMES, FALLBACK_GAMES)
    for k in ketten:
        print(f"         {k.time} -> {k.time.split(':')[0]} -> {k.letter or '?'}")
    print("LEVEL 5  GAME KEY   (Quelle:", QUELLE + ")")
    for k in ketten:
        if k.matches:
            titel = ", ".join(g.title for g in k.matches)
            print(f"         {k.letter} -> {titel}   [{k.status} · {k.confidence}]")
        else:
            print(f"         {k.letter} -> NO VERIFIED MATCH")
    v = riddle_validation(TIMES, FALLBACK_GAMES)
    print("FINAL WORD ->", v["wort"])
    print()
    print("GRUNDRATE (Anti-Zufall)")
    for g in v["grundraten"]:
        print(f"  {g['letter']}: {g['treffer']}/{g['total']} Titel ({g['quote']*100:.1f}%) -> {g['beweiskraft']}")
    print("MEHRDEUTIGKEIT")
    for m in v["mehrdeutigkeit"]:
        print(f"  {m['time']}: Stunde={m['stunde_letter']} Minute={m['minute_letter']} "
              f"-> {'Regel noetig' if m['regel_noetig'] else 'beide Lesarten gleich'}")
    print()
    print("SANCHO CHECK")
    for kk, vv in sancho_check(TIMES, FALLBACK_GAMES).items():
        print(f"  {kk}: {vv}")
    print()
    print("Hinweis: linguistisches Rätsel. KEINE Glücksspiel-Vorhersage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
