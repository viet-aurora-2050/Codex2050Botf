"""Tests fuer AKT 4 – Das Signal (finale Uebertragung + Ebene-2-Chiffren)."""

import unittest

from aktvier import (
    FINALE_ZITAT,
    IMPERATIV,
    SCHLUESSEL,
    SCHUTZ_ANKER,
    b64_decode,
    b64_encode,
    erzeuge_signal,
    formatiere,
    morse_decode,
    morse_encode,
    rot13,
    uhr_decode,
    uhr_encode,
)


class TestChiffren(unittest.TestCase):
    def test_morse_roundtrip(self):
        self.assertEqual(morse_decode(morse_encode(SCHLUESSEL)), SCHLUESSEL)
        self.assertEqual(morse_encode("SOS"), "... --- ...")

    def test_base64_roundtrip(self):
        self.assertEqual(b64_decode(b64_encode(FINALE_ZITAT)), FINALE_ZITAT)

    def test_rot13_selbstinvers(self):
        self.assertEqual(rot13(rot13(SCHUTZ_ANKER)), SCHUTZ_ANKER)
        self.assertNotEqual(rot13(SCHUTZ_ANKER), SCHUTZ_ANKER)

    def test_uhr_roundtrip(self):
        zeiten = uhr_encode(IMPERATIV)
        self.assertEqual(uhr_decode(zeiten), IMPERATIV)
        for z in zeiten:
            self.assertRegex(z, r"^\d{2}:\d{2}$")


class TestSignal(unittest.TestCase):
    def test_alle_schichten_dekodieren_korrekt(self):
        p = erzeuge_signal()
        self.assertEqual(p.entschluesselt["MORSE"], SCHLUESSEL)
        self.assertEqual(p.entschluesselt["BASE64"], FINALE_ZITAT)
        self.assertEqual(p.entschluesselt["ROT13"], SCHUTZ_ANKER)
        self.assertEqual(p.entschluesselt["UHRZEITEN"], IMPERATIV)

    def test_finale_zitat_aus_lore(self):
        self.assertIn("erinnert werden", FINALE_ZITAT)

    def test_ausgabe_ohne_loesung_verbirgt_klartext(self):
        text = formatiere(erzeuge_signal(), mit_loesung=False)
        self.assertNotIn("ENTSCHLUESSELT", text)
        self.assertIn("VERSCHLUESSELTES SIGNAL", text)
        self.assertIn("Kein Spielbefehl", text)

    def test_ausgabe_mit_loesung_zeigt_klartext(self):
        text = formatiere(erzeuge_signal(), mit_loesung=True)
        self.assertIn("ALEXANDRA", text)
        self.assertIn("Geh, wenn du gehen musst", text)


if __name__ == "__main__":
    unittest.main()
