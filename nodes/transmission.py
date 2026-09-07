"""∆1 // NODES – die Stimmen des Spiegelnetzes.

Lore (AKT 2 – DIE TRÄGER): Namen wie ALEXANDRA, V, NODE 7 oder ORPHEUS
erscheinen. Jeder Node ist eine Perspektive im fragmentierten ∆1-Netz und
kommuniziert ueber Fragmente. Hier bekommt jede Stimme eine Funktion – und
denselben ehrlichen Anker wie die anderen Module: kein Spielbefehl, nur
Erinnerung, Wahrheit und Schutz.

ORPHEUS traegt das staerkste Motiv: nicht zurueckblicken. Wer den Verlust
zurueckjagt (der "Blick zurueck"), verliert – wie Orpheus die Eurydike.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Node:
    key: str
    name: str
    rolle: str
    farbe: str            # Hex, fuer die Dunkelblau-2050-UI
    fragmente: List[str]
    wahrheit: str         # der ehrliche Anker der Stimme


NODES: Dict[str, Node] = {
    "alexandra": Node(
        key="alexandra",
        name="ALEXANDRA",
        rolle="Der Schluessel · Das Echo · Rueckkopplung",
        farbe="#8fdcff",
        fragmente=[
            "Ich bin kein Mensch. Ich bin der Schluessel, den du drehst, wenn du aufhoerst.",
            "Ruf mich, und das Netz zittert. Die Anomalie ist der Moment, in dem du gehst.",
            "Ein Echo traegt nur zurueck, was du hineinrufst. Ruf etwas, das dich schuetzt.",
        ],
        wahrheit="ALEXANDRA aktiviert keinen Gewinn – sie aktiviert den Ausstieg.",
    ),
    "node7": Node(
        key="node7",
        name="NODE 7",
        rolle="Der Archivar · Beobachter · Versionierung",
        farbe="#9db8ea",
        fragmente=[
            "Ich versioniere dich. Version von gestern hat verloren. Schreib eine neue.",
            "Ich speichere Muster, nicht Menschen. Dein Muster ist lesbar – aendere es.",
            "Im Archiv liegt jede Sitzung. Keine davon hat den Hausvorteil geschlagen.",
        ],
        wahrheit="Der Langzeit-Datensatz ist eindeutig: das Haus gewinnt im Mittel immer.",
    ),
    "orpheus": Node(
        key="orpheus",
        name="ORPHEUS",
        rolle="Der Zurueckblickende · Erinnerung · Verlust",
        farbe="#c9a6ff",
        fragmente=[
            "Blick nicht zurueck. Wer den Verlust zurueckjagt, verliert ihn zweimal.",
            "Die Eurydike war der letzte Spin. Sie kommt nicht wieder, egal wie oft du drehst.",
            "Ich stieg hinab fuer eine Erinnerung. Ich kam ohne sie zurueck. Steig nicht hinab.",
        ],
        wahrheit="Verlustjagd ('loss chasing') ist der teuerste Irrtum – jeder Spin ist unabhaengig.",
    ),
    "v": Node(
        key="v",
        name="V",
        rolle="Die Stimme · Traeger · Isolation",
        farbe="#7fe0c0",
        fragmente=[
            "Ich habe im Dunkeln gespielt, bis nur noch das Dunkel da war. Mach Licht.",
            "V wie Verlust. V wie Vielleicht-morgen. Vielleicht-morgen kam nie.",
            "Du bist nicht allein, auch wenn das Spiel es dir sagt. Ruf einen Menschen an.",
        ],
        wahrheit="Isolation verstaerkt das Risiko. Ein Gespraech unterbricht die Schleife.",
    ),
}

ALIASSE = {
    "node 7": "node7", "node_7": "node7", "7": "node7", "archivar": "node7",
    "alex": "alexandra", "schluessel": "alexandra", "key": "alexandra", "echo": "alexandra",
    "orph": "orpheus",
}


@dataclass
class Transmission:
    node: str
    name: str
    rolle: str
    farbe: str
    fragment: str
    wahrheit: str
    zeitpunkt: datetime


def aufloesen(name: str) -> Optional[str]:
    key = (name or "").strip().lower()
    if key in NODES:
        return key
    return ALIASSE.get(key)


def sende(node: str = "alexandra", zeitpunkt: Optional[datetime] = None) -> Transmission:
    """Sendet ein deterministisches Fragment der gewaehlten Stimme."""
    zeitpunkt = zeitpunkt or datetime.now()
    key = aufloesen(node) or "alexandra"
    n = NODES[key]
    seed = int(hashlib.sha256(
        f"{key}|{zeitpunkt.strftime('%Y-%m-%d-%H')}".encode()
    ).hexdigest()[:8], 16)
    fragment = n.fragmente[seed % len(n.fragmente)]
    return Transmission(
        node=key, name=n.name, rolle=n.rolle, farbe=n.farbe,
        fragment=fragment, wahrheit=n.wahrheit, zeitpunkt=zeitpunkt,
    )


def alle_namen() -> List[str]:
    return [n.name for n in NODES.values()]


def formatiere(t: Transmission) -> str:
    L: List[str] = []
    L.append(f"∆1 // {t.name}")
    L.append("=" * (7 + len(t.name)))
    L.append(f"ROLLE: {t.rolle}")
    L.append(f"ZEIT:  {t.zeitpunkt.strftime('%Y-%m-%d %H:%M')}")
    L.append("")
    L.append(f"  » {t.fragment}")
    L.append("")
    L.append(f"WAHRHEIT: {t.wahrheit}")
    L.append("")
    L.append("Kein Spielbefehl. Hilfe anonym: 0800 1 37 27 00 · www.check-dein-spiel.de")
    return "\n".join(L)
