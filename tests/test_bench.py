"""Test Contract v1.3 — manifest và benchmark có render (TICKET-04, lát Bench)."""

import json
import math
import os
import shlex
import subprocess
import unittest
from unittest.mock import patch

from helpers import ROOT, Workdir

from chonoi import bench
from chonoi.contract import load_contract

KEYS = {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}


def manifest():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


class Manifest(unittest.TestCase):
    def test_v13_declares_bench_and_soak_commands(self):
        m = manifest()
        self.assertEqual(m["contract_version"], "1.3")
        self.assertEqual(shlex.split(m["bench_cmd"])[-2:], ["-m", "chonoi.bench"])
        self.assertEqual(shlex.split(m["soak_cmd"])[-2:], ["-m", "chonoi.soak"])
        self.assertIn("freshness", load_contract()["tuning"], "gameplay/kho giữ nguyên v1.2")


class Metrics(unittest.TestCase):
    def test_formula_matches_ticket(self):
        # 198 khung 10 ms + 2 khung 50 ms: ceil(1% × 200) = 2 khung chậm nhất -> 1 / 0.05 s = 20 FPS
        frames = [10.0] * 198 + [50.0, 50.0]
        m = bench.compute_metrics(frames, sum(frames), first_frame_epoch_ms=12_345.0, start_epoch_s=10.0)
        self.assertEqual(set(m), KEYS)
        self.assertEqual(m["frames"], 200)
        self.assertEqual(m["measured_s"], 2.08)
        self.assertEqual(m["avg_fps"], round(200 / 2.08, 2))
        self.assertEqual(m["p1_low_fps"], 20.0)
        self.assertEqual(m["load_ms"], 2345)

    def test_at_least_one_slow_frame_and_ceil(self):
        m = bench.compute_metrics([16.0, 16.0, 40.0], 72.0, 0.0, 0.0)
        self.assertEqual(m["p1_low_fps"], 25.0)  # max(1, ceil(0.03)) = 1 khung: 40 ms
        frames = [10.0] * 150 + [30.0, 20.0]     # ceil(1.52) = 2 khung: (30 + 20) / 2 = 25 ms -> 40 FPS
        self.assertEqual(bench.compute_metrics(frames, sum(frames), 0.0, 0.0)["p1_low_fps"], 40.0)
        self.assertEqual(math.ceil(0.01 * 152), 2)

    def test_no_frames_is_an_error(self):
        with self.assertRaises(bench.BenchError):
            bench.compute_metrics([], 0, 0, 0)


class Cli(unittest.TestCase):
    def test_missing_browser_exits_1_without_output(self):
        with Workdir() as w, patch.dict(os.environ, {"CHONOI_BROWSER": "khong-co-trinh-duyet-nay"}):
            out = w.path("bench.json")
            self.assertEqual(bench.main(["--seed", "42", "--duration", "1", "--out", out]), 1)
            self.assertFalse(os.path.exists(out))

    def test_bad_args_exit_2(self):
        with Workdir() as w:
            self.assertEqual(bench.main(["--seed", "x", "--duration", "1", "--out", w.path("b.json")]), 2)
            self.assertEqual(bench.main(["--seed", "1", "--duration", "0", "--out", w.path("b.json")]), 2)

    def test_real_render_short_run_when_browser_available(self):
        """Chạy thật qua bench_cmd (1 s đo) nếu máy có Chromium/Chrome/Edge; không có thì bỏ qua."""
        try:
            bench.find_browser()
        except bench.BenchError as e:
            self.skipTest(str(e))
        with Workdir() as w:
            out = w.path("bench.json")
            cmd = shlex.split(manifest()["bench_cmd"])
            if cmd[0] == "python3" and os.name == "nt":
                cmd[0] = "python"
            p = subprocess.run([*cmd, "--seed", "42", "--duration", "1", "--out", out], cwd=ROOT,
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(set(data), KEYS)
            self.assertGreater(data["frames"], 0)
            self.assertTrue(0.9 <= data["measured_s"] <= 1.5, data)
            self.assertTrue(abs(data["avg_fps"] - data["frames"] / data["measured_s"]) <= 0.01 * data["avg_fps"] + 0.5)
            self.assertLessEqual(data["p1_low_fps"], data["avg_fps"] + 0.01)
            self.assertGreater(data["load_ms"], 0)
            self.assertEqual(os.listdir(os.path.dirname(out)), ["bench.json"], "không để lại file tạm")


if __name__ == "__main__":
    unittest.main()
