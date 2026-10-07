"""Zugriffskontrolle für den Telegram-Bot: Allowlist + Rate-Limit.

Bisher war `ALLOWED_USER_IDS` zwar dokumentiert, wurde aber nirgends geprüft, und
`RATE_LIMIT_PER_MINUTE` war ungenutzt. Dieses Modul schließt die Lücke an EINER Stelle:
ein Gate-Handler (Gruppe -1) läuft vor allen Befehlen.

Ehrlich:
  * Leere Allowlist = öffentlicher Bot (so war es gedacht). Ist dann zusätzlich eine KI
    konfiguriert, kann jeder Fremde über /analyse und /frage API-Kosten verursachen –
    deshalb gibt `warnung()` einen deutlichen Hinweis und das Rate-Limit begrenzt den Schaden.
  * Das Rate-Limit liegt im Arbeitsspeicher (ein Prozess); es ist kein Ersatz für eine Allowlist.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Callable, Deque, Dict, Iterable, Optional

FENSTER_SEKUNDEN = 60.0
MAX_BEKANNTE_NUTZER = 10_000      # Obergrenze, damit der Speicher nicht unbegrenzt wächst


class Zugriff:
    """Allowlist + gleitendes Zeitfenster pro Nutzer."""

    def __init__(self, erlaubte_ids: Iterable[int] = (), limit_pro_minute: int = 10,
                 uhr: Callable[[], float] = time.monotonic):
        self.erlaubt = frozenset(int(i) for i in erlaubte_ids)
        self.limit = max(0, int(limit_pro_minute))       # 0 = Rate-Limit aus
        self._uhr = uhr
        self._anfragen: Dict[int, Deque[float]] = {}
        self._gewarnt: Dict[int, float] = {}

    @classmethod
    def aus_config(cls, config) -> "Zugriff":
        return cls(getattr(config, "ALLOWED_USER_IDS", []) or [],
                   getattr(config, "RATE_LIMIT_PER_MINUTE", 10))

    def ist_erlaubt(self, user_id: int) -> bool:
        """Leere Allowlist = jeder darf; sonst nur gelistete IDs."""
        return not self.erlaubt or int(user_id) in self.erlaubt

    def zaehle_und_pruefe(self, user_id: int) -> bool:
        """Registriert eine Anfrage. True = innerhalb des Limits, False = gedrosselt."""
        if self.limit == 0:
            return True
        jetzt = self._uhr()
        q = self._anfragen.setdefault(int(user_id), deque())
        while q and jetzt - q[0] >= FENSTER_SEKUNDEN:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(jetzt)
        if len(self._anfragen) > MAX_BEKANNTE_NUTZER:
            self._aufraeumen(jetzt)
        return True

    def _aufraeumen(self, jetzt: float) -> None:
        for uid in [u for u, q in self._anfragen.items() if not q or jetzt - q[-1] >= FENSTER_SEKUNDEN]:
            del self._anfragen[uid]
            self._gewarnt.pop(uid, None)

    def warnung(self, ki_aktiv: bool) -> Optional[str]:
        """Hinweistext für das Log, wenn der Bot öffentlich ist und eine KI Kosten verursachen kann."""
        if self.erlaubt:
            return None
        if ki_aktiv:
            return ("ALLOWED_USER_IDS ist leer und eine KI ist aktiv: jeder Telegram-Nutzer kann "
                    "über /analyse und /frage API-Kosten verursachen. Bitte ALLOWED_USER_IDS setzen.")
        return "ALLOWED_USER_IDS ist leer: der Bot ist öffentlich (Rate-Limit aktiv)."

    async def gate(self, update, context) -> None:
        """Gate-Handler (Gruppe -1): blockiert Unerlaubte/Gedrosselte, bevor ein Befehl läuft."""
        from telegram.ext import ApplicationHandlerStop

        user = getattr(update, "effective_user", None)
        if user is None:                                  # z. B. Kanal-Updates: nichts zu tun
            raise ApplicationHandlerStop
        if not self.ist_erlaubt(user.id):
            raise ApplicationHandlerStop                  # still ignorieren, nichts verraten
        if not self.zaehle_und_pruefe(user.id):
            nachricht = getattr(update, "effective_message", None)
            jetzt = self._uhr()
            # Nur einmal pro Zeitfenster antworten – sonst wird der Bot selbst zum Spam-Verstärker.
            if nachricht is not None and jetzt - self._gewarnt.get(user.id, -FENSTER_SEKUNDEN) >= FENSTER_SEKUNDEN:
                self._gewarnt[user.id] = jetzt
                await nachricht.reply_text("⏳ Zu viele Anfragen – bitte kurz warten.")
            raise ApplicationHandlerStop
