"""Tests für datenbank.anbieter_details (gesetzlicher Rahmen + Jackpotpiraten). Kein Netzwerk."""

import json
import tempfile
import unittest
from pathlib import Path

from datenbank import anbieter_details as d

# Ausschnitte im Wortlaut der GGL-Seiten (Stand Abruf 2026-10-07).
SCHUTZ = ("<html><body><h2>5 Sekunden Mindestdauer pro Spiel</h2><p>Zwischen diesen Spielen muss allerdings eine "
          "Mindestdauer von 5 Sekunden liegen.</p><p>Nach einer ununterbrochenen Spieldauer von 60 Minuten müssen "
          "Spielende aktiv ein Informationsfeld bestätigen. Eine weitere Teilnahme ist dann erst nach 5 Minuten nach "
          "Bestätigung der Kenntnisnahme möglich.</p><p>Ein automatischer Start der einzelnen Spiele ist bei "
          "Virtuellen Automatenspielen verboten.</p></body></html>")
LIMITS = ("<html><body><p>Es ist festgelegt, dass Spielende innerhalb eines Kalendermonats insgesamt nicht mehr als "
          "1.000 Euro anbieterübergreifend einzahlen dürfen.</p><p>Was hat sich bei der zulässigen Einsatzhöhe seit dem "
          "1. Juli 2026 geändert? Die Regelung sieht weiterhin einen Höchsteinsatz von 1 Euro als Regelfall vor. "
          "Es gilt eine generelle Altersgrenze von 21 Jahren. In der ersten Stufe kann der Höchsteinsatz auf bis zu 3 Euro "
          "erhöht werden. In der zweiten Stufe ist eine weitere Erhöhung auf bis zu 5 Euro möglich.</p></body></html>")


def _jp(n=6):
    zeilen = "".join(f"<tr><td>Studio{i}</td><td>{i * 10}</td><td>Titel {i}</td></tr>" for i in range(1, n + 1))
    zeilen += "<tr><td>Play’n GO</td><td>192</td><td>Book of Dead</td></tr>"
    return (f"<html><body><table>{zeilen}</table><p>Dir stehen 855 Spielautomaten zur Verfügung.</p>"
            "<p>Einsatzlimit: Für die Spielrunden gilt ein Einsatzlimit von 1 € pro Spielrunde. Höhere Spieleinsätze von "
            "bis zu 3 € beziehungsweise 5 € pro Spin sind nur unter bestimmten Voraussetzungen möglich.</p>"
            "<p>Es gilt ein monatliches Einzahlungslimit ( LUGAS Limit ) in Höhe von 1.000 € pro Spieler.</p></body></html>")


class TestRahmen(unittest.TestCase):
    def test_alle_werte_aus_dem_wortlaut(self):
        werte, fehlend = d.parse_rahmen(d._text(SCHUTZ), d._text(LIMITS))
        self.assertEqual(fehlend, [])
        self.assertEqual(werte["einsatz_regel_eur"], 1)
        self.assertEqual((werte["einsatz_stufe1_eur"], werte["einsatz_stufe2_eur"]), (3, 5))
        self.assertEqual(werte["einsatz_erhoeht_ab_alter"], 21)
        self.assertEqual(werte["einsatz_erhoeht_seit"], "1. Juli 2026")
        self.assertEqual(werte["einzahlung_monat_eur"], 1000)       # "1.000" -> 1000
        self.assertEqual(werte["min_sekunden_pro_spiel"], 5)
        self.assertEqual((werte["cooldown_nach_min"], werte["cooldown_pause_min"]), (60, 5))
        self.assertTrue(werte["autoplay_verboten"])

    def test_fehlendes_muster_wird_gemeldet_nicht_geraten(self):
        werte, fehlend = d.parse_rahmen(d._text(SCHUTZ), d._text("<p>Umbau der Seite</p>"))
        self.assertIn("einzahlung_monat_eur", fehlend)
        self.assertNotIn("einzahlung_monat_eur", werte)


class TestJackpotpirat(unittest.TestCase):
    def test_tabelle_limits_und_apostroph(self):
        jp = d.parse_jackpotpirat(_jp())
        self.assertEqual(jp["studios"]["Play'n GO"], 192)            # ’ -> '
        self.assertEqual(jp["studios_beliebtester_titel"]["Play'n GO"], "Book of Dead")
        self.assertEqual(jp["spielautomaten_angabe"], 855)
        self.assertEqual(jp["einsatz_pro_spin_eur"], 1)
        self.assertEqual(jp["einsatz_erhoeht_eur"], [3, 5])
        self.assertEqual(jp["einzahlung_monat_eur"], 1000)
        self.assertEqual(jp["summe_studios"], sum(jp["studios"].values()))

    def test_ohne_tabelle_keine_daten(self):
        self.assertIsNone(d.parse_jackpotpirat("<html>Wartung</html>"))
        self.assertIsNone(d.parse_jackpotpirat(_jp(2).replace("Studio3", "x")))   # zu wenige Zeilen


class TestMerge(unittest.TestCase):
    ALT = {"schema_version": "1.0", "anbieter": {"jackpotpirat": {
        "name": "JackpotPiraten", "betreiber": "KURATIERT", "limits": {"autoplay": False, "min_sekunden_pro_spin_durchschnitt": 5},
        "spiele_genannt": ["Book of Ra"], "quellen": []}}}

    def test_kuratiertes_bleibt_und_neues_kommt(self):
        rahmen = d.parse_rahmen(d._text(SCHUTZ), d._text(LIMITS))
        neu = d.aktualisiere(self.ALT, rahmen, d.parse_jackpotpirat(_jp()))
        jp = neu["anbieter"]["jackpotpirat"]
        self.assertEqual(jp["betreiber"], "KURATIERT")
        self.assertFalse(jp["limits"]["autoplay"])
        self.assertEqual(jp["limits"]["einsatz_erhoeht_eur"], [3, 5])
        self.assertIn("Book of Ra", jp["spiele_genannt"])
        self.assertIn("Book of Dead", jp["spiele_genannt"])
        self.assertEqual(neu["regulatorischer_rahmen"]["einsatz_regel_eur"], 1)
        self.assertIn("nicht anbieterspezifisch", neu["regulatorischer_rahmen"]["gilt_fuer"])
        self.assertIn("tipico", neu["betreiberseiten_hinweis"])

    def test_teilweise_extraktion_behaelt_alte_werte(self):
        rahmen = d.parse_rahmen(d._text(SCHUTZ), d._text(LIMITS))
        voll = d.aktualisiere({}, rahmen, None)
        teil = d.aktualisiere(voll, ({"min_sekunden_pro_spiel": 6}, ["einzahlung_monat_eur"]), None)
        self.assertEqual(teil["regulatorischer_rahmen"]["min_sekunden_pro_spiel"], 6)
        self.assertEqual(teil["regulatorischer_rahmen"]["einzahlung_monat_eur"], 1000)   # alter Wert bleibt
        self.assertEqual(teil["regulatorischer_rahmen"]["fehlend"], ["einzahlung_monat_eur"])

    def test_kein_rtp_erfunden(self):
        neu = d.aktualisiere(self.ALT, None, d.parse_jackpotpirat(_jp()))
        self.assertNotIn("rtp", neu["anbieter"]["jackpotpirat"])


class TestLauf(unittest.TestCase):
    def test_lauf_mit_seiten_ist_idempotent(self):
        seiten = {"schutz": SCHUTZ, "limits": LIMITS, "jp": _jp()}
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "anbieter.json"
            self.assertEqual(d.lauf(pfad, seiten=seiten), 0)
            erster = pfad.read_text(encoding="utf-8")
            self.assertEqual(d.lauf(pfad, seiten=seiten), 0)
            self.assertEqual(pfad.read_text(encoding="utf-8"), erster)       # nur Zeitstempel -> kein Rewrite

    def test_ausfall_einer_quelle_laesst_rest_zu(self):
        orig = d.abrufen
        d.abrufen = lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pfad = Path(tmp) / "anbieter.json"
                pfad.write_text('{"anbieter": {}, "x": 1}\n', encoding="utf-8")
                self.assertEqual(d.lauf(pfad, seiten={"jp": _jp()}), 0)     # GGL offline, JP vorhanden
                daten = json.loads(pfad.read_text(encoding="utf-8"))
                self.assertEqual(daten["x"], 1)
                self.assertNotIn("regulatorischer_rahmen", daten)
                self.assertIn("studios", daten["anbieter"]["jackpotpirat"])
        finally:
            d.abrufen = orig

    def test_seitenformat_geaendert_laesst_datei_unveraendert(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "anbieter.json"
            pfad.write_text('{"anbieter": {}}\n', encoding="utf-8")
            vorher = pfad.read_text(encoding="utf-8")
            d.lauf(pfad, seiten={"schutz": "<p>neu</p>", "limits": "<p>neu</p>", "jp": "<p>neu</p>"})
            daten = json.loads(pfad.read_text(encoding="utf-8")) if pfad.read_text(encoding="utf-8") != vorher else {}
            self.assertNotIn("regulatorischer_rahmen", daten)

    def test_dry_run_schreibt_nichts(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "anbieter.json"
            d.lauf(pfad, seiten={"schutz": SCHUTZ, "limits": LIMITS, "jp": _jp()}, dry_run=True)
            self.assertFalse(pfad.exists())


if __name__ == "__main__":
    unittest.main()
