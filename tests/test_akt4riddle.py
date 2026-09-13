"""Tests fuer Akt4GameRiddleDecoder – inkl. Anti-Zufall / Fehl-Match-Faelle."""

import unittest

from akt4riddle import (
    FALLBACK_GAMES,
    Game,
    clock_to_letter,
    decode_base64,
    decode_morse,
    decode_rot13,
    find_game_matches,
    match_chain,
    riddle_validation,
    sancho_check,
)
from akt4riddle.riddle import base_rate, clock_letter_minute, mehrdeutigkeit

TIMES = ["07:07", "05:05", "08:08"]


class TestDecoderEbenen(unittest.TestCase):
    def test_morse_alexandra(self):
        self.assertEqual(decode_morse(".- .-.. . -..- .- -. -.. .-. .-"), "ALEXANDRA")

    def test_base64_zitat(self):
        s = decode_base64("SWNoIHdvbGx0ZSBuaWUgZnJlaSBzZWluLiBJY2ggd29sbHRlIGVyaW5uZXJ0IHdlcmRlbi4=")
        self.assertIn("erinnert werden", s)

    def test_rot13_selbstinvers(self):
        msg = "Erinnert zu werden heisst nicht, gefangen zu bleiben. Geh, wenn du gehen musst."
        self.assertEqual(decode_rot13(decode_rot13(msg)), msg)

    def test_clock_alphabet_geh(self):
        self.assertEqual([clock_to_letter(t) for t in TIMES], ["G", "E", "H"])

    def test_clock_ungueltig(self):
        self.assertIsNone(clock_to_letter("30:00"))   # Stunde > 26
        self.assertIsNone(clock_to_letter("kaputt"))


class TestGameMatching(unittest.TestCase):
    def test_final_word_geh(self):
        self.assertEqual(riddle_validation(TIMES, FALLBACK_GAMES)["wort"], "GEH")

    def test_fuenf_falsche_matches_werden_nicht_akzeptiert(self):
        # 5 Games, deren Titel NICHT mit G beginnt -> kein Treffer fuer G
        falsch = [
            Game("Book of Ra", verified=True), Game("Starburst", verified=True),
            Game("Reactoonz", verified=True), Game("Money Train", verified=True),
            Game("Dead or Alive", verified=True),
        ]
        self.assertEqual(find_game_matches("G", falsch), [])

    def test_fehlende_game_daten_no_verified_match(self):
        ketten = match_chain(TIMES, [])
        for k in ketten:
            self.assertEqual(k.status, "NO VERIFIED MATCH")
            self.assertEqual(k.confidence, "UNKNOWN")

    def test_doppelte_treffer_kein_zufalls_pick(self):
        games = [Game("Gates of Olympus", verified=True, source="a"),
                 Game("Gonzo's Quest", verified=True, source="a")]
        k = match_chain(["07:07"], games)[0]
        self.assertEqual(k.status, "MULTIPLE CANDIDATES")
        self.assertEqual(len(k.matches), 2)          # beide gezeigt, keiner „gewinnt"
        self.assertEqual(k.confidence, "LOW")

    def test_unverifizierter_treffer_zaehlt_nicht(self):
        games = [Game("Gates of Olympus", verified=False)]
        self.assertEqual(match_chain(["07:07"], games)[0].status, "NO VERIFIED MATCH")

    def test_erfindet_keine_titel(self):
        # Kein Game mit 'Q' -> kein erfundener Titel, sondern leere Liste
        self.assertEqual(find_game_matches("Q", FALLBACK_GAMES), [])


class TestValidierungUndSancho(unittest.TestCase):
    def test_sieben_checks_vorhanden(self):
        c = riddle_validation(TIMES, FALLBACK_GAMES)["checks"]
        for i in range(1, 8):
            self.assertTrue(any(k.startswith(f"{i}_") for k in c), f"Check {i} fehlt")

    def test_sancho_unbekannt_ohne_daten(self):
        sc = sancho_check(TIMES, [])
        self.assertEqual(sc["game_title_verification"], "FAILED")
        self.assertEqual(sc["final_interpretation"], "GEH")   # Wort kommt aus der Uhr, nicht aus Games

    def test_keine_gluecksspiel_vorhersage(self):
        # Der gesamte Sancho-/Validierungs-Output enthaelt keine Vorhersage-Woerter
        blob = " ".join(str(v) for v in sancho_check(TIMES, FALLBACK_GAMES).values()).lower()
        for wort in ("gewinnt", "zahlt jetzt", "faellig", "spin", "jackpot"):
            self.assertNotIn(wort, blob)


class TestHaertung(unittest.TestCase):
    def test_grundrate_markiert_game_ebene_als_dekorativ(self):
        br = base_rate("E", FALLBACK_GAMES)
        self.assertGreaterEqual(br["treffer"], 2)      # mehrere Spiele mit E
        self.assertIn("dekorativ", br["beweiskraft"])

    def test_grundrate_kein_treffer(self):
        self.assertEqual(base_rate("Q", FALLBACK_GAMES)["treffer"], 0)

    def test_minute_lesart_alternative(self):
        self.assertEqual(clock_letter_minute("05:05"), "E")
        self.assertEqual(clock_letter_minute("07:19"), "S")   # Minute 19 -> S

    def test_mehrdeutigkeit_regel_noetig_wenn_stunde_ungleich_minute(self):
        m = mehrdeutigkeit(["07:19"])[0]
        self.assertTrue(m["regel_noetig"])                    # 07->G vs 19->S
        self.assertFalse(m["eindeutig"])

    def test_confidence_nie_high_bei_hoher_grundrate(self):
        sc = sancho_check(TIMES, FALLBACK_GAMES)
        self.assertNotEqual(sc["confidence"], "HIGH")
        self.assertIn("dekorativ", sc["game_beweiskraft"])

    def test_check7_zufall_bei_hoher_grundrate(self):
        self.assertTrue(riddle_validation(TIMES, FALLBACK_GAMES)["checks"]["7_moeglicherweise_zufall"])


if __name__ == "__main__":
    unittest.main()
