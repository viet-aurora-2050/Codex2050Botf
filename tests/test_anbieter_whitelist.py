"""Tests für den GGL-Whitelist-Abgleich (datenbank.anbieter_whitelist). Kein Netzwerk."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from datenbank import anbieter_whitelist as w


def _li(name, suchwoerter, arten):
    h3 = "".join(f'<h3 class="uk-text-bold">{a}</h3><table></table>' for a in arten)
    return (f'<li gglwhitelist-g-ids="6" gglwhitelist-r-ids="2" gglwhitelist-search-words="{suchwoerter}">'
            f'<a class="uk-accordion-title" href><span class="ggl-wl-check-to-highlight">{name}</span></a>'
            f'<div class="uk-accordion-content">{h3}</div></li>')


FIXTURE = (
    "<html><body><ul uk-accordion>"
    + _li("DGGS Deutsche Gesellschaft für Glücksspiel mbH",
          "DGGS Berlin Deutschland länderübergreifend bingbong.de 27.04.2022 jackpotpiraten.de",
          ["Virtuelle Automatenspiele"])
    + _li("Tipico Games Limited",
          "Tipico Games Limited Tower, Vjal Portomaso St. Julian&#8216;s Malta games.tipico.de 06.10.2022 goldrummel.de",
          ["Virtuelle Automatenspiele"])
    + _li("Betkick Sportsbetting Limited",
          "Betkick Malta online betano.de 19.02.2021 16.12.2022 31.05.2023",
          ["Sportwetten", "Virtuelle Automatenspiele"])
    + _li("Lotto24 AG", "Lotto24 Hamburg lotto24.de 01.01.2020", ["Lotterien"])
    + "</ul><h3>Footer-Ueberschrift darf nicht zugeordnet werden</h3></body></html>"
)


class TestParser(unittest.TestCase):
    def test_eintraege_und_felder(self):
        e = w.parse_whitelist(FIXTURE)
        self.assertEqual(len(e), 4)
        dggs = e[0]
        self.assertEqual(dggs["betreiber"], "DGGS Deutsche Gesellschaft für Glücksspiel mbH")
        self.assertEqual(dggs["erlaubnisarten"], ["Virtuelle Automatenspiele"])
        self.assertIn("jackpotpiraten.de", dggs["domains"])
        self.assertEqual(dggs["daten"], ["27.04.2022"])

    def test_mehrere_erlaubnisarten_und_daten_sortiert(self):
        betano = w.parse_whitelist(FIXTURE)[2]
        self.assertEqual(betano["erlaubnisarten"], ["Sportwetten", "Virtuelle Automatenspiele"])
        self.assertEqual(betano["daten"], ["19.02.2021", "16.12.2022", "31.05.2023"])

    def test_footer_h3_wird_nicht_dem_letzten_eintrag_zugeordnet(self):
        lotto = w.parse_whitelist(FIXTURE)[3]
        self.assertEqual(lotto["erlaubnisarten"], ["Lotterien"])

    def test_html_entities_und_abwesende_domains(self):
        tip = w.parse_whitelist(FIXTURE)[1]
        self.assertIn("games.tipico.de", tip["domains"])
        self.assertNotIn("julian", " ".join(tip["domains"]))


class TestAbgleich(unittest.TestCase):
    def setUp(self):
        self.res = w.abgleich(w.parse_whitelist(FIXTURE))

    def test_gefunden_per_domain(self):
        self.assertTrue(self.res["jackpotpirat"]["gefunden"])
        self.assertTrue(self.res["tipico"]["gefunden"])
        self.assertTrue(self.res["betano"]["gefunden"])

    def test_nicht_gefunden_wird_ausdruecklich_gemeldet(self):
        self.assertFalse(self.res["n1"]["gefunden"])
        self.assertEqual(self.res["n1"]["eintraege"], [])
        self.assertFalse(self.res["stargames"]["gefunden"])   # nicht im Fixture

    def test_name_regex_trifft_ganzes_wort(self):
        e = [{"betreiber": "N1 Interactive Ltd", "erlaubnisarten": [], "domains": [], "daten": []},
             {"betreiber": "Kn12 Group", "erlaubnisarten": [], "domains": [], "daten": []}]
        res = w.abgleich(e)["n1"]
        self.assertEqual([x["betreiber"] for x in res["eintraege"]], ["N1 Interactive Ltd"])


class TestAktualisieren(unittest.TestCase):
    def _alt(self):
        return {"schema_version": "1.0", "abgerufen": "2026-01-01",
                "anbieter": {"jackpotpirat": {"name": "JackpotPiraten", "betreiber": "KURATIERT",
                                              "limits": {"einsatz_pro_spin_eur": 1}, "quellen": []}}}

    def test_kuratierte_felder_bleiben_und_fehlende_profile_entstehen(self):
        neu = w.aktualisiere(self._alt(), w.parse_whitelist(FIXTURE))
        jp = neu["anbieter"]["jackpotpirat"]
        self.assertEqual(jp["betreiber"], "KURATIERT")
        self.assertEqual(jp["limits"]["einsatz_pro_spin_eur"], 1)
        self.assertTrue(jp["whitelist"]["gefunden"])
        self.assertIn("n1", neu["anbieter"])
        self.assertFalse(neu["anbieter"]["n1"]["whitelist"]["gefunden"])
        self.assertIn("keine deutsche", neu["anbieter"]["n1"]["whitelist"]["hinweis"].lower())

    def test_quelle_nur_einmal_eingetragen(self):
        e = w.parse_whitelist(FIXTURE)
        neu = w.aktualisiere(w.aktualisiere(self._alt(), e), e)
        urls = [q["url"] for q in neu["anbieter"]["jackpotpirat"]["quellen"]]
        self.assertEqual(urls.count(w.WHITELIST_URL), 1)

    def test_kein_rtp_wird_erfunden(self):
        neu = w.aktualisiere({}, w.parse_whitelist(FIXTURE))
        for p in neu["anbieter"].values():
            self.assertNotIn("rtp", p)
            self.assertIn("rtp_hinweis", p)


class TestSchreiben(unittest.TestCase):
    def test_nur_zeitstempel_aenderung_schreibt_nicht(self):
        e = w.parse_whitelist(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "anbieter.json"
            t1 = datetime(2026, 10, 7, 4, 0, tzinfo=timezone.utc)
            t2 = datetime(2026, 10, 8, 4, 0, tzinfo=timezone.utc)
            self.assertTrue(w.schreibe(w.aktualisiere({}, e, t1), pfad))
            self.assertFalse(w.schreibe(w.aktualisiere(json.loads(pfad.read_text(encoding="utf-8")), e, t2), pfad))

    def test_inhaltliche_aenderung_schreibt(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "anbieter.json"
            self.assertTrue(w.schreibe(w.aktualisiere({}, w.parse_whitelist(FIXTURE)), pfad))
            ohne_jp = [x for x in w.parse_whitelist(FIXTURE) if "DGGS" not in x["betreiber"]]
            alt = json.loads(pfad.read_text(encoding="utf-8"))
            self.assertTrue(w.schreibe(w.aktualisiere(alt, ohne_jp), pfad))


class TestAusfall(unittest.TestCase):
    def test_zu_wenige_eintraege_lassen_datei_unveraendert(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "anbieter.json"
            pfad.write_text('{"anbieter": {}, "abgerufen": "2026-01-01"}\n', encoding="utf-8")
            vorher = pfad.read_text(encoding="utf-8")
            self.assertEqual(w.lauf(pfad, seite="<html>Wartungsseite</html>"), 0)
            self.assertEqual(pfad.read_text(encoding="utf-8"), vorher)

    def test_abruffehler_lassen_datei_unveraendert(self):
        original = w.abrufen
        w.abrufen = lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pfad = Path(tmp) / "anbieter.json"
                pfad.write_text('{"anbieter": {}}\n', encoding="utf-8")
                self.assertEqual(w.lauf(pfad), 0)
                self.assertEqual(pfad.read_text(encoding="utf-8"), '{"anbieter": {}}\n')
        finally:
            w.abrufen = original

    def test_lauf_mit_fixture_schreibt_bei_gesenkter_schwelle(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "anbieter.json"
            self.assertEqual(w.lauf(pfad, seite=FIXTURE, min_eintraege=1), 0)
            self.assertTrue(json.loads(pfad.read_text(encoding="utf-8"))["anbieter"]["betano"]["whitelist"]["gefunden"])

    def test_dry_run_schreibt_nichts(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "anbieter.json"
            w.lauf(pfad, seite=FIXTURE, dry_run=True, min_eintraege=1)
            self.assertFalse(pfad.exists())


if __name__ == "__main__":
    unittest.main()
