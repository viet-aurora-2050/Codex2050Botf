"""∆1 // Datenbank – öffentlicher Spiele-Katalog (v3, generierter Snapshot).

Basissatz (veröffentlichte Studio-RTPs) + optionale öffentliche JSON-Feeds
(GAMES_SOURCES). Source-Adapter → Validation → Normalization → Dedup →
Katalog + Source-Health → docs/games.json. Keine Anbieter-API, keine Vorhersage.
"""

from .alternativen import aehnlichkeit, finde_alternativen, finde_nach_name
from .sources import (
    BASIS_QUELLE,
    SEED_GAMES,
    http_json_source,
    normalisiere,
    sammle,
)
from .update import SCHEMA_VERSION, baue, schreibe

__all__ = [
    "BASIS_QUELLE",
    "SCHEMA_VERSION",
    "SEED_GAMES",
    "aehnlichkeit",
    "baue",
    "finde_alternativen",
    "finde_nach_name",
    "http_json_source",
    "normalisiere",
    "sammle",
    "schreibe",
]
