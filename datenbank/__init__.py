"""∆1 // Datenbank – tägliche Erzeugung der öffentlichen Spiele-Liste.

Basissatz (veröffentlichte Studio-RTPs) + optionale öffentliche JSON-Feeds
(GAMES_SOURCES). Keine Anbieter-API, keine Vorhersage.
"""

from .sources import (
    BASIS_QUELLE,
    SEED_GAMES,
    http_json_source,
    normalisiere,
    sammle,
)
from .update import baue, schreibe

__all__ = [
    "BASIS_QUELLE",
    "SEED_GAMES",
    "http_json_source",
    "normalisiere",
    "sammle",
    "baue",
    "schreibe",
]
