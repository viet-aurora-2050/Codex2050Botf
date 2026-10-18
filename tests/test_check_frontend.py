"""Tests für scripts/check_frontend.py: die Prüfregeln müssen echte Fehler finden können."""

import importlib.util
import shutil
import unittest
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_frontend", WURZEL / "scripts" / "check_frontend.py")
cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf)


class TestA11yRegeln(unittest.TestCase):
    def test_findet_label_ohne_for_und_nackte_felder(self):
        kaputt = '<label>Budget</label><input id="b"><select id="s"></select><input>'
        befunde = " ".join(cf.pruefe_a11y(kaputt))
        self.assertIn("ohne zugehöriges label", befunde)
        self.assertIn("ohne id/aria-label", befunde)
        self.assertIn("aria-live", befunde)
        self.assertIn("Content-Security-Policy", befunde)

    def test_korrektes_markup_ist_sauber(self):
        gut = ('<label for="b">Budget</label><input id="b"><div aria-live="polite"></div>'
               '<meta http-equiv="Content-Security-Policy" content="x">')
        self.assertEqual(cf.pruefe_a11y(gut), [])


class TestEchteSeiten(unittest.TestCase):
    def test_streng_geprueft_seiten_sind_sauber(self):
        for name in sorted(cf.A11Y_STRENG):
            html = (WURZEL / "docs" / name).read_text(encoding="utf-8")
            self.assertEqual(cf.pruefe_a11y(html), [], name)

    def test_sancho_ist_bewusst_ausgenommen(self):
        self.assertNotIn("sancho.html", cf.A11Y_STRENG)

    @unittest.skipUnless(shutil.which("node"), "node nicht installiert")
    def test_alle_seiten_und_json_ohne_fehler(self):
        for pfad in sorted((WURZEL / "docs").glob("*.html")):
            self.assertEqual(cf.pruefe_html(pfad), [], pfad.name)
        for pfad in sorted((WURZEL / "docs").glob("*.json")):
            self.assertEqual(cf.pruefe_json(pfad), [], pfad.name)


if __name__ == "__main__":
    unittest.main()
