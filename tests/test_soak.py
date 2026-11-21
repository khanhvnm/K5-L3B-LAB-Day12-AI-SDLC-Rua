"""Soak headless 10 Ngày (Ticket-04 mục 2, Test Contract v1.3). Lát soak — Trà.

Chạy `soak_cmd` khai trong game.contract.json (chưa khai thì dùng `python -m chonoi.soak`), đọc soak.json.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_soak -v
"""

import copy
import json
import math
import os
import shlex
import subprocess
import sys
import unittest

from helpers import ROOT, Workdir

from chonoi.contract import load_contract
from chonoi.day import DaySession
from chonoi.dayplan import plan_for_day, resolve_day_plan
from chonoi.errors import BadInput
from chonoi.soak import run_soak

TUNING = load_contract()["tuning"]
MULT = TUNING["score"]["reputation_multiplier"]


def soak_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        c = json.load(f)
    return shlex.split(c["soak_cmd"]) if "soak_cmd" in c else [sys.executable, "-m", "chonoi.soak"]


def run_cli(*args):
    p = subprocess.run([*soak_cmd(), *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stderr


class Soak(unittest.TestCase):
    def test_soak_10_ngay_du_ngay_khong_loi(self):
        with Workdir() as w:
            code, err = run_cli("--seed", "7", "--days", "10", "--out", w.path("soak.json"))
            self.assertEqual(code, 0, err)
            with open(w.path("soak.json"), encoding="utf-8") as f:
                rep = json.load(f)
        self.assertEqual(set(rep), {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertEqual((rep["days"], rep["days_completed"], rep["crashes"]), (10, 10, 0))
        self.assertIsInstance(rep["duration_s"], (int, float))
        self.assertEqual([r["day"] for r in rep["results"]], list(range(1, 11)))
        for r in rep["results"]:
            self.assertEqual(set(r), {"day", "earned", "reputation", "score"})
            self.assertEqual(r["score"], r["earned"] + MULT * math.floor(r["reputation"]))
        earned = [r["earned"] for r in rep["results"]]
        self.assertEqual(earned, sorted(earned), "tổng thu đi tiếp xuyên Ngày, không reset")
        self.assertGreater(earned[-1], 0, "bot thực sự nấu và phục vụ")

    def test_cung_seed_lap_lai_giong_het_tru_thoi_gian(self):
        a, b = run_soak(TUNING, 7, 10), run_soak(TUNING, 7, 10)
        for rep in (a, b):
            rep.pop("duration_s")
        self.assertEqual(a, b)

    def test_loi_chay_duoc_dem_va_van_tra_bao_cao(self):
        broken = copy.deepcopy(TUNING)
        del broken["day_plan"]
        rep = run_soak(broken, 7, 2)
        self.assertEqual((rep["crashes"], rep["days_completed"], rep["results"]), (1, 0, []))

    def test_tham_so_sai_ma_2(self):
        with Workdir() as w:
            out = w.path("soak.json")
            for args in (("--seed", "7", "--days", "0", "--out", out),
                         ("--seed", "bay", "--days", "10", "--out", out),
                         ("--seed", "7", "--days", "10")):
                self.assertEqual(run_cli(*args)[0], 2, args)
            self.assertFalse(os.path.exists(out))


class Continuity(unittest.TestCase):
    def test_id_ca_the_tang_xuyen_ngay(self):
        """Bot chạy 3 Ngày: id cá thể bàn giao ở gather_end không trùng và Ngày sau luôn lớn hơn Ngày trước."""
        from chonoi.ids import id_key
        from chonoi.soak import Bot
        sess, bot = DaySession(TUNING, {}, 7, 3, max_days=3), Bot(TUNING)
        per_day = []
        while not sess.done:
            for row in sess.step(bot.act(sess)):
                if row["name"] == "gather_end":
                    per_day.append([it["id"] for it in row["data"]["inventory"]["items"]])
        self.assertEqual(len(per_day), 3)
        nonempty = [ids for ids in per_day if ids]
        self.assertGreaterEqual(len(nonempty), 2, per_day)
        flat = [i for ids in per_day for i in ids]
        self.assertEqual(len(flat), len(set(flat)), "id không lặp lại xuyên Ngày")
        for prev, nxt in zip(nonempty, nonempty[1:]):
            self.assertLess(max(map(id_key, prev)), min(map(id_key, nxt)), (prev, nxt))


class PlanCycle(unittest.TestCase):
    def test_ke_hoach_d1_d5_lap_o_ngay_6_10(self):
        plans = resolve_day_plan(TUNING)
        for day in range(6, 11):
            self.assertEqual(plan_for_day(plans, day), plan_for_day(plans, day - 5), day)

    def test_headless_day_van_gioi_han_5_ngay(self):
        with self.assertRaises(BadInput):
            DaySession(TUNING, {}, 1, 6)
        DaySession(TUNING, {}, 1, 10, max_days=10)


if __name__ == "__main__":
    unittest.main()
