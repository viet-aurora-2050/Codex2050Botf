"""Der AGB-Scan in docs/index.html (JavaScript) muss dasselbe finden und rechnen wie analyzer.scan (Python).

Der Block zwischen den Markern AGB-SCAN-BEGIN / AGB-SCAN-ENDE wird mit Node geladen und gegen Python verglichen.
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from analyzer.scan import analysiere_text

HTML = Path(__file__).resolve().parents[1] / "docs" / "index.html"
NODE = shutil.which("node")

KORPUS = [
    ("Willkommensbonus: 100 % bis zu 200 € auf deine erste Einzahlung. Mindesteinzahlung 20 €. "
     "Der Bonus muss 35x umgesetzt werden (Bonusbetrag + Einzahlung). Frist: 30 Tage. "
     "Maximaler Einsatz pro Spin 5 €. Maximaler Gewinn 500 €.", {}),
    ("Willkommensbonus: 100 % bis zu 200 € auf deine erste Einzahlung. Mindesteinzahlung 20 €. Umsatz 35x in 30 Tagen.",
     {"einzahlung": 50, "rtp": 94, "einsatz": 2}),
    ("Bonus 100 % bis 100 €. Umsatz 30x innerhalb von 7 Tagen. An anderer Stelle: Bonus-Umsatz 35x, gültig 30 Tage.", {"einzahlung": 50}),
    ("Bonus 100 % bis 100 €. Umsatz 30x innerhalb von 3 Stunden.", {"einzahlung": 50}),
    ("Bonus 100 % bis 100 €. Umsatz 30x innerhalb von 2 Wochen.", {"einzahlung": 50}),
    ("Bonus 100 % bis zu 1.000 €. Umsatz 30x. Max. Einsatz 2,50 € pro Spin.", {"einzahlung": 100}),
    ("Bonus ohne Einzahlung: 10 € Bonusguthaben. Umsatz 40x.", {}),
    ("Bonus 100 % bis 100 €. Umsatz 45x. Slots zählen 100 %, Tischspiele zählen 10 % zum Umsatz. "
     "Maximaler Einsatz 5 € pro Spin, sonst gilt: Bonus verfällt.", {"einzahlung": 50}),
    ("Bonus 50 % bis 100 €. Mindesteinzahlung 10 € (Bonus bis 100 €). 25 Freispiele. Freispielgewinne 40x umsetzen. "
     "Umsatz 30x auf den Bonusbetrag. RTP 96,5 %.", {"einzahlung": 30}),
    ("Bonus 100 % bis 50 €. Umsatz 30x auf die Einzahlung. Umsatz 30x auf den Bonusbetrag.", {"einzahlung": 20}),
    ("Das Wetter ist heute schön.", {}),
    ("Bonus 100 % auf alles. Umsatz 30x.", {}),
    ("Umsatzbedingung 35x, sonst nichts Relevantes.", {}),
    ("Bonus 25 € Bonus geschenkt. Umsatz 20x. Max. Gewinn 100 €. Zeitlimit: 5 Tage.", {}),
    ("Detail Tabelle " + "Spalte Wert Zeile " * 14 + "Bonus 100 % bis 100 € Mindesteinzahlung 1 € Umsatz Bonus 40x Bonusbetrag "
     "Laufzeit 30 Tage " + "Zeile Ende " * 12, {}),
    ("Bonus 100 % bis 200 €. Umsatz 35x. Max. Einsatz 0,50 €. Maximaler Gewinn aus dem Bonus: 50 €. Frist 1 Tag.",
     {"einzahlung": 100, "einsatz": 0.5}),
]

JS_RUNNER = """
const fs=require('fs');
const html=fs.readFileSync(process.argv[2],'utf8');
const m=html.match(/\\/\\/ AGB-SCAN-BEGIN([\\s\\S]*?)\\/\\/ AGB-SCAN-ENDE/);
const api=new Function(m[1]+'; return {agbScan:agbScan,agbRechne:agbRechne};')();
const korpus=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const out=korpus.map(([text,opt])=>{
  try{const e=api.agbScan(text,opt);const r=api.agbRechne(e.sz);return {ok:true,e:e,r:r};}
  catch(err){return {ok:false,fehler:String(err.message)};}
});
console.log(JSON.stringify(out));
"""


@unittest.skipUnless(NODE, "node nicht installiert")
class TestAgbJsParitaet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp:
            runner, korpus = Path(tmp) / "run.js", Path(tmp) / "korpus.json"
            runner.write_text(JS_RUNNER, encoding="utf-8")
            korpus.write_text(json.dumps(KORPUS), encoding="utf-8")
            r = subprocess.run([NODE, str(runner), str(HTML), str(korpus)], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise AssertionError(r.stderr[-600:])
        cls.js = json.loads(r.stdout)

    def test_alle_faelle_gleich(self):
        for i, (text, opt) in enumerate(KORPUS):
            js = self.js[i]
            try:
                scan, erg = analysiere_text(text, **opt)
                py = True
            except ValueError:
                py = False
            self.assertEqual(js["ok"], py, f"Fall {i}: Fehler-Verhalten unterschiedlich ({js.get('fehler')})")
            if not py:
                continue
            e, r = js["e"], js["r"]
            self.assertEqual([(f["feld"], f["wert"], f["beleg"]) for f in e["funde"]],
                             [(f.feld, str(f.wert), f.beleg) for f in scan.funde], f"Fall {i}: Funde")
            self.assertEqual(len(e["annahmen"]), len(scan.annahmen), f"Fall {i}: Annahmen")
            self.assertEqual([a[:25] for a in e["annahmen"]], [a[:25] for a in scan.annahmen], f"Fall {i}: Annahmen-Text")
            self.assertEqual(e["hinweise"], scan.hinweise, f"Fall {i}: Hinweise")
            for feld_js, wert_py in (("bonus", erg.bonus), ("mindestumsatz", erg.mindestumsatz),
                                     ("erwarteter_verlust", erg.erwarteter_verlust),
                                     ("erwartungswert", erg.erwartungswert), ("spins", erg.benoetigte_spins),
                                     ("tage", erg.benoetigte_tage)):
                self.assertAlmostEqual(r[feld_js], wert_py, places=1, msg=f"Fall {i}: {feld_js}")
            self.assertEqual(r["empfehlung"], erg.empfehlung.value, f"Fall {i}: Empfehlung")
            self.assertEqual(r["machbar"], erg.zeit_machbar, f"Fall {i}: machbar")
            self.assertEqual(len(r["warnungen"]), len(erg.warnungen), f"Fall {i}: Warnungen")


if __name__ == "__main__":
    unittest.main()
