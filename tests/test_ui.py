"""Gắn kiểm thử UI Node vào lệnh unittest chung; không cài dependency."""
import pathlib
import shutil
import subprocess
import unittest


class UITest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Cần Node để chạy test UI JavaScript")
    def test_canvas_client(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        result = subprocess.run([shutil.which("node"), "--test", "tests/test_ui.js"],
                                cwd=root, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
