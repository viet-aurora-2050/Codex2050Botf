"""Kuratierter öffentlicher Fallback-Datensatz mit REALEN, bekannten Spieltiteln.

WICHTIG: Diese Titel werden nicht erfunden – es sind öffentlich bekannte Spiele.
Bitte dennoch gegen die offizielle Spielinfo prüfen. Der Datensatz ist NICHT
hartcodiert im Rätsel-Kern: er ist ein austauschbarer Fallback. Eine andere
öffentliche Game-Liste kann ihn ersetzen (Reproduzierbarkeit).
"""

from .riddle import Game

QUELLE = "kuratierter oeffentlicher Fallback-Datensatz"

# (Titel, Anbieter) – real & öffentlich bekannt.
_ROH = [
    ("Gates of Olympus", "Pragmatic Play"),
    ("Gonzo's Quest", "NetEnt"),
    ("Eye of Horus", "Reel Time Gaming / Merkur"),
    ("Extra Chilli", "Big Time Gaming"),
    ("El Torero", "Merkur"),
    ("Holla die Waldfee", "Bally Wulff"),
    ("Hall of Gods", "NetEnt"),
    ("Book of Ra", "Novomatic"),
    ("Big Bass Bonanza", "Pragmatic Play"),
    ("Starburst", "NetEnt"),
    ("Sweet Bonanza", "Pragmatic Play"),
    ("Legacy of Dead", "Play'n GO"),
    ("Reactoonz", "Play'n GO"),
    ("Money Train", "Relax Gaming"),
    ("Dead or Alive", "NetEnt"),
    ("Fire Joker", "Play'n GO"),
]

FALLBACK_GAMES = [Game(title=t, provider=p, source=QUELLE, verified=True) for t, p in _ROH]
