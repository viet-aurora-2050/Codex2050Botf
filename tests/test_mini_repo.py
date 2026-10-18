"""Das Mini-Repo-ZIP (scripts/build_mini_repo.py) muss sich bauen lassen und eigenstaendig bestehen."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SKRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_mini_repo.py"


def _lade():
    spec = importlib.util.spec_from_file_location("build_mini_repo", SKRIPT)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


class TestMiniRepo(unittest.TestCase):
    def test_zip_enthaelt_alles_und_besteht_eigenstaendig(self):
        with tempfile.TemporaryDirectory() as tmp:
            ziel = _lade().baue(Path(tmp))
            with zipfile.ZipFile(ziel) as z:
                self.assertIsNone(z.testzip())
                namen = set(z.namelist())
                z.extractall(Path(tmp) / "x")
            wurzel = "KI_Taktik_Repo_v2/"
            for pflicht in ("index.html", "README.md", "bonus_analyzer.py", "analyzer/scan.py", "analyzer/bonus.py",
                            "risiko/profil.py", "tests/test_scan.py", "tests/test_profil.py",
                            ".github/workflows/ci.yml"):
                self.assertIn(wurzel + pflicht, namen)
            self.assertFalse([n for n in namen if "__pycache__" in n or "sancho" in n.lower()])
            r = subprocess.run([sys.executable, "-W", "error", "-m", "unittest", "discover", "-s", "tests"],
                               cwd=Path(tmp) / "x" / "KI_Taktik_Repo_v2", capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr[-800:])


if __name__ == "__main__":
    unittest.main()
