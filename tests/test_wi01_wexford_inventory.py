import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "wi01_wexford_inventory.py"

class TestWI01(unittest.TestCase):
    def test_readonly_inventory_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "data"
            folder = root / "erw-pdf-sources" / "project"
            folder.mkdir(parents=True)
            source = folder / "test.pdf"
            source.write_bytes(b"%PDF-1.4\ntest\n%%EOF")
            output = Path(d) / "inventory.json"
            cmd = [sys.executable, str(SCRIPT), "--data-root", str(root), "--output", str(output)]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            item = json.loads(output.read_text())["files"][0]
            self.assertEqual(item["bytes"], source.stat().st_size)
            self.assertEqual(len(item["sha256"]), 64)
            self.assertEqual(source.read_bytes(), b"%PDF-1.4\ntest\n%%EOF")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_disallow_writing_into_live_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "data"
            root.mkdir()
            out = root / "inventory.json"
            cmd = [sys.executable, str(SCRIPT), "--data-root", str(root), "--output", str(out)]
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(out.exists())

if __name__ == "__main__":
    unittest.main()
