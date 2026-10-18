"""Tests für die AGB-Datenbank (datenbank.agb_sammler): ohne Netzwerk, mit eingespeister Abruf-Funktion."""

import asyncio
import importlib
import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

from datenbank import agb_sammler as A

BONUS_SEITE = ("<html><body><nav>Menü</nav><main><h1>Bonus</h1>" + "<p>Allgemeine Infos zum Anbieter und seinen Angeboten.</p>" * 30 +
               "<p>Willkommensbonus 2026 im Detail Neue Spieler erhalten 100 % Bonus bis 100 € sowie 125 Freispiele. "
               "Die Mindesteinzahlung beträgt 1 €. Der Bonus muss 40x umgesetzt werden. Laufzeit 30 Tage. "
               "Umsatz Bonus 40x Bonusbetrag.</p>"
               "<p>" + "Füllsatz ohne Bezug. " * 60 + "</p>"
               "<p>Weitere Aktion: Montags 5 Freispiele ohne Einzahlung, Umsatz 99x.</p></main><footer>Impressum</footer></body></html>")
AGB_SEITE = ("<html><body><main>" + "<p>Allgemeine Regeln des Hauses gelten für alle Spieler dauerhaft.</p>" * 30 +
             "<p>Der maximale Gewinn aus Freispielen beträgt 200 €.</p><p>Das Bonusguthaben verfällt nach 7 Tagen.</p>"
             "<p>Stand: 06.03.2026</p></main></body></html>")
ROBOTS_OK = "User-agent: *\nAllow: /\n"

KONFIG = {"test": {"name": "Test", "host": "www.beispiel.test", "seiten": [
    {"id": "bonus", "titel": "Bonus", "url": "https://www.beispiel.test/bonus", "rolle": "bonus",
     "abschnitt": r"Willkommensbonus\s+\d{4}\s+im\s+Detail", "abschnitt_laenge": 800},
    {"id": "agb", "titel": "AGB", "url": "https://www.beispiel.test/agb", "rolle": "agb"}]}}


def fake(seiten, robots=ROBOTS_OK):
    aufrufe = []

    def hole(url):
        aufrufe.append(url)
        if url.endswith("/robots.txt"):
            return (200, robots, None) if robots is not None else (404, None, "HTTP 404")
        if url in seiten:
            v = seiten[url]
            return v if isinstance(v, tuple) else (200, v, None)
        return 404, None, "HTTP 404"
    hole.aufrufe = aufrufe
    return hole


SEITEN = {"https://www.beispiel.test/bonus": BONUS_SEITE, "https://www.beispiel.test/agb": AGB_SEITE}
T1 = datetime(2026, 10, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 10, 2, tzinfo=timezone.utc)


def baue(alt=None, seiten=None, jetzt=T1, robots=ROBOTS_OK, konfig=None):
    return A.baue(alt, hole_fn=fake(SEITEN if seiten is None else seiten, robots), konfig=konfig or KONFIG,
                  jetzt=jetzt, schlaf=lambda s: None)


class TestAuswertung(unittest.TestCase):
    def test_bonus_abschnitt_mit_belegen_und_beispielen(self):
        d = baue()
        bonus = d["anbieter"]["test"]["seiten"][0]
        self.assertEqual(bonus["status"], "ok")
        erg = bonus["ergebnis"]
        self.assertTrue(erg["abschnitt_gefunden"])
        werte = {f["feld"]: f["wert"] for f in erg["funde"]}
        self.assertEqual((werte["Umsatzfaktor"], werte["Bonus"], werte["Bonus-Deckel"], werte["Zeitlimit"]),
                         ("40x", "100 %", "100 €", "30 Tage"))
        self.assertNotIn("99x", json.dumps(erg))                       # anderes Angebot außerhalb des Abschnitts
        self.assertEqual(erg["freispiele_anzahl"], 125)
        b50 = next(b for b in erg["beispiele"] if b["einzahlung"] == 50)
        self.assertEqual(b50["mindestumsatz"], 2000.0)                 # 50 € Bonus x 40
        self.assertEqual(b50["erwartungswert"], -30.0)
        self.assertTrue(erg["annahmen"])                               # RTP/Einsatz stehen als Annahme da

    def test_agb_fundstellen_einzeln_nicht_zusammengefasst(self):
        s = baue()["anbieter"]["test"]["seiten"][1]
        self.assertEqual(s["stand_text"], "06.03.2026")
        f = {(x["feld"], x["wert"]) for x in s["ergebnis"]["fundstellen"]}
        self.assertIn(("Maximaler Gewinn/Auszahlung", "200 €"), f)
        self.assertIn(("Zeitlimit", "7 Tage"), f)

    def test_abschnitt_fehlt_wird_gemeldet(self):
        seiten = dict(SEITEN)
        seiten["https://www.beispiel.test/bonus"] = BONUS_SEITE.replace("im Detail", "ausfuehrlich")
        erg = baue(seiten=seiten)["anbieter"]["test"]["seiten"][0]["ergebnis"]
        self.assertFalse(erg["abschnitt_gefunden"])
        self.assertIn("nicht gefunden", erg["hinweise"][0])

    def test_speichert_keinen_volltext(self):
        text = json.dumps(baue())
        self.assertNotIn("Allgemeine Regeln des Hauses", text)
        def laengste(x):
            if isinstance(x, str):
                return len(x)
            if isinstance(x, dict):
                return max([laengste(v) for v in x.values()] + [0])
            if isinstance(x, list):
                return max([laengste(v) for v in x] + [0])
            return 0
        self.assertLess(laengste(json.loads(text)["anbieter"]), 400)


class TestSchutzregeln(unittest.TestCase):
    def test_robots_sperre_wird_beachtet(self):
        hole = fake(SEITEN, robots="User-agent: *\nDisallow: /agb\n")
        d = A.baue(None, hole_fn=hole, konfig=KONFIG, jetzt=T1, schlaf=lambda s: None)
        stati = {s["id"]: s["status"] for s in d["anbieter"]["test"]["seiten"]}
        self.assertEqual(stati, {"bonus": "ok", "agb": "robots_gesperrt"})
        self.assertNotIn("https://www.beispiel.test/agb", hole.aufrufe)

    def test_robots_fehler_5xx_liest_nichts(self):
        d = baue(robots=None, konfig=KONFIG) if False else A.baue(
            None, hole_fn=lambda u: (503, None, "HTTP 503") if u.endswith("robots.txt") else (200, BONUS_SEITE, None),
            konfig=KONFIG, jetzt=T1, schlaf=lambda s: None)
        self.assertTrue(all(s["status"] == "robots_gesperrt" for s in d["anbieter"]["test"]["seiten"]))

    def test_fehlende_robots_txt_erlaubt(self):
        d = baue(robots=None)
        self.assertEqual(d["anbieter"]["test"]["seiten"][0]["status"], "ok")

    def test_sperrseite_ist_nicht_lesbar(self):
        seiten = {"https://www.beispiel.test/bonus": "<html>No Service</html>", "https://www.beispiel.test/agb": (403, None, "HTTP 403")}
        d = baue(seiten=seiten)
        s0, s1 = d["anbieter"]["test"]["seiten"]
        self.assertEqual((s0["status"], s1["status"]), ("nicht_lesbar", "nicht_lesbar"))
        self.assertEqual(s1["http"], 403)
        self.assertNotIn("ergebnis", s0)

    def test_nur_https_und_fremder_host_abgelehnt(self):
        self.assertEqual(A.hole("http://www.beispiel.test/")[2], "nur https-URLs erlaubt")
        self.assertEqual(A.hole("ftp://x/")[0], None)


class TestAenderungsmonitor(unittest.TestCase):
    def test_hash_aendert_sich_nur_bei_relevantem_text(self):
        d1 = baue(jetzt=T1)
        d2 = baue(alt=d1, jetzt=T2)
        s = d2["anbieter"]["test"]["seiten"][0]
        self.assertNotIn("geaendert", s)
        self.assertEqual(s["erstmals_erfasst"], "2026-10-01")
        seiten = dict(SEITEN)
        seiten["https://www.beispiel.test/bonus"] = BONUS_SEITE.replace("40x umgesetzt", "45x umgesetzt")
        d3 = baue(alt=d2, seiten=seiten, jetzt=T2)
        s3 = d3["anbieter"]["test"]["seiten"][0]
        self.assertEqual(s3["geaendert"], "2026-10-02")
        self.assertEqual(s3["vorheriger_sha256"], s["sha256"])
        # unrelevanter Text (Navigation/Footer) ändert den Hash nicht
        seiten["https://www.beispiel.test/bonus"] = BONUS_SEITE.replace("Menü", "Anderes Menü")
        d4 = baue(alt=d1, seiten=seiten, jetzt=T2)
        self.assertNotIn("geaendert", d4["anbieter"]["test"]["seiten"][0])

    def test_ausfall_behaelt_letzten_befund(self):
        d1 = baue(jetzt=T1)
        d2 = baue(alt=d1, seiten={"https://www.beispiel.test/bonus": (503, None, "HTTP 503"),
                                  "https://www.beispiel.test/agb": AGB_SEITE}, jetzt=T2)
        s = d2["anbieter"]["test"]["seiten"][0]
        self.assertEqual(s["status"], "nicht_lesbar")
        self.assertEqual(s["letzter_erfolg"], "2026-10-01")
        self.assertIn("szenario", s["ergebnis"])                       # alter Befund bleibt sichtbar

    def test_start_seite_entdeckt_links_desselben_hosts(self):
        konfig = {"x": {"name": "X", "host": "www.beispiel.test",
                        "seiten": [{"id": "start", "titel": "Start", "url": "https://www.beispiel.test/", "rolle": "start"}]}}
        start = ("<html><body>" + "<p>Willkommen auf unserer Seite mit vielen Spielen und Aktionen.</p>" * 30 +
                 '<a href="/bonus">Bonus</a><a href="https://fremd.test/agb">Fremd</a><a href="/impressum">I</a>'
                 '<a href="/info/agb">AGB</a></body></html>')
        seiten = dict(SEITEN)
        seiten["https://www.beispiel.test/"] = start
        seiten["https://www.beispiel.test/info/agb"] = AGB_SEITE
        d = A.baue(None, hole_fn=fake(seiten), konfig=konfig, jetzt=T1, schlaf=lambda s: None)
        urls = [s["url"] for s in d["anbieter"]["x"]["seiten"]]
        self.assertEqual(urls, ["https://www.beispiel.test/", "https://www.beispiel.test/bonus",
                                "https://www.beispiel.test/info/agb"])


class TestSchreibenUndRechnen(unittest.TestCase):
    def test_schreibe_nur_bei_inhaltsaenderung(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = os.path.join(tmp, "agb.json")
            d1 = baue(jetzt=T1)
            self.assertTrue(A.schreibe(d1, pfad))
            self.assertFalse(A.schreibe(baue(alt=d1, jetzt=T2), pfad))   # gleicher Inhalt -> nur geprueft erneuert
            j = json.load(open(pfad, encoding="utf-8"))
            self.assertEqual(j["geprueft"][:10], "2026-10-02")
            vorher = open(pfad, encoding="utf-8").read()
            A.schreibe(baue(alt=d1, jetzt=T2), pfad)
            self.assertEqual(open(pfad, encoding="utf-8").read(), vorher)  # gleicher Tag -> Datei unveraendert

    def test_rechne_mit_eigenen_werten(self):
        bonus = baue()["anbieter"]["test"]["seiten"][0]
        text = A.rechne(bonus, einzahlung=100, rtp=94, einsatz=2)
        self.assertIn("Mindestumsatz", text)
        self.assertIn("Erwartungswert", text)
        with self.assertRaises(ValueError):
            A.rechne({"ergebnis": {"fehler": "kein Bonus"}})

    def test_szenario_rundreise(self):
        sz = baue()["anbieter"]["test"]["seiten"][0]["ergebnis"]["szenario"]
        self.assertEqual(A.szenario_dict(A.szenario_aus_dict(sz)), sz)

    def test_veroeffentlichte_datei_ist_gueltig(self):
        pfad = A._standard_pfad()
        if not pfad.exists():
            self.skipTest("docs/agb.json fehlt")
        d = json.loads(pfad.read_text(encoding="utf-8"))
        self.assertEqual(d["schema_version"], "1.0")
        self.assertIn("jackpotpirat", d["anbieter"])
        for a in d["anbieter"].values():
            for s in a["seiten"]:
                self.assertIn(s["status"], {"ok", "nicht_lesbar", "robots_gesperrt"})
                self.assertTrue(s["url"].startswith("https://"))


HAT_TELEGRAM = importlib.util.find_spec("telegram") is not None
HAT_FASTAPI = (importlib.util.find_spec("fastapi") is not None
               and importlib.util.find_spec("httpx") is not None)


class _Msg:
    def __init__(self):
        self.texte = []

    async def reply_text(self, text, **kwargs):
        self.texte.append(text)
        return self


class _Upd:
    def __init__(self):
        self.message = _Msg()


class _Ctx:
    def __init__(self, *args):
        self.args = list(args)


@unittest.skipUnless(HAT_TELEGRAM, "python-telegram-bot nicht installiert")
class TestBotAgb(unittest.TestCase):
    def _bot(self):
        from config import Config
        from bot.core import CasinoBonusBot
        c = Config()
        c.TELEGRAM_TOKEN = "123456:TEST-TOKEN-NICHT-ECHT"
        return CasinoBonusBot(c)

    def _lauf(self, *args):
        upd = _Upd()
        asyncio.run(self._bot().agb_command(upd, _Ctx(*args)))
        return upd.message.texte[-1]

    def test_registriert(self):
        app = self._bot().build_application()
        self.assertIn("agb", {c for g in app.handlers.values() for h in g for c in getattr(h, "commands", [])})

    def test_uebersicht_und_anbieter_und_rechnung(self):
        self.assertIn("AGB-Datenbank", self._lauf())
        self.assertIn("jackpotpirat", self._lauf())
        self.assertIn("Umsatzfaktor", self._lauf("jackpotpirat"))
        text = self._lauf("jackpotpirat", "einzahlung=50")
        self.assertIn("EMPFEHLUNG", text)
        self.assertLessEqual(len(text), 4000)

    def test_unbekannt(self):
        self.assertIn("❌", self._lauf("gibtsnicht"))


@unittest.skipUnless(HAT_FASTAPI, "fastapi/httpx nicht installiert")
class TestApiAgb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TELEGRAM_TOKEN", None)
            os.environ.pop("TELEGRAM_WEBHOOK_SECRET", None)
            import web.dashboard as dash
            cls.dash = importlib.reload(dash)
        cls.client = TestClient(cls.dash.app)

    def test_uebersicht_und_detail(self):
        r = self.client.get("/api/agb")
        self.assertEqual(r.status_code, 200)
        self.assertIn("jackpotpirat", r.json()["anbieter"])
        r = self.client.get("/api/agb", params={"anbieter": "jackpotpirat", "einzahlung": 50})
        self.assertEqual(r.status_code, 200)
        self.assertIn("EMPFEHLUNG", r.json()["report"])

    def test_fehler(self):
        self.assertEqual(self.client.get("/api/agb", params={"anbieter": "nix"}).status_code, 404)
        self.assertEqual(self.client.get("/api/agb", params={"anbieter": "jackpotpirat", "einzahlung": -5}).status_code, 422)
        self.assertEqual(self.client.get("/api/agb", params={"anbieter": "tipico", "einzahlung": 50}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
