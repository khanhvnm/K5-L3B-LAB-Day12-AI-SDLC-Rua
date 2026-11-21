"""Test Contract v1.2 — kho cá thể và độ tươi ở gather (lát S + G, TICKET-03)."""

import json
import os
import unittest
from fractions import Fraction

from helpers import (Workdir, close, events, frames, make_items, read_jsonl, run_headless, snapshots, write_json)

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.inventory import read_inventory, write_inventory
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

T = load_contract()["tuning"]
IDLE = InputState((0.0, 0.0), set(), set())
STEP = Fraction(1, 120)  # 0.5/s ÷ 60 tick


def press(*names):
    return InputState((0.0, 0.0), set(names), set(names))


def sim(scenario):
    base = {"random_fish": False, "monsters": [], "nodes": []}
    return GatherSim(T, dict(base, **scenario), Streams(1), IdAllocator())


def gather_cli(w, scenario, ticks=1, input_frames=(), inventory_out=True):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    args = ["--mode", "gather", "--seed", "1", "--scenario", sc, "--ticks", str(ticks),
            "--snapshot-every", "1", "--out", w.path("g.jsonl")]
    if input_frames:
        args += ["--inputs", write_json(w.path("in.json"), frames(*input_frames))]
    inv = w.path("inv.json")
    if inventory_out:
        args += ["--inventory-out", inv]
    code, err = run_headless(*args)
    return code, err, read_jsonl(w.path("g.jsonl")) if code == 0 else [], inv


class Contract12(unittest.TestCase):
    def test_version_and_freshness_block(self):
        c = load_contract()
        self.assertEqual(c["contract_version"], "1.2")
        self.assertEqual(c["tuning"]["freshness"],
                         {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})


class InventoryFile(unittest.TestCase):
    def test_read_rejects_count_schema_and_bad_items(self):
        bad = [
            {"items": {"ca_loc": 1}},                                              # kho đếm v1.0/v1.1
            {"items": [{"id": "I1", "kind": "ca_loc"}]},                           # thiếu fresh
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100, "x": 1}]},    # khóa lạ
            {"items": [{"id": "I1", "kind": "ca_map", "fresh": 100}]},            # kind lạ
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I1", "kind": "ca_linh", "fresh": 90}]},
            {"items": [{"id": "", "kind": "ca_loc", "fresh": 100}]},              # id rỗng
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.5}]},          # ngoài miền
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -1}]},
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": True}]},
            {"items": [], "extra": 1},
        ]
        with Workdir() as w:
            for i, data in enumerate(bad):
                inv = write_json(w.path(f"bad{i}.json"), data)
                out = w.path(f"q{i}.jsonl")
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", out)
                self.assertEqual(code, 2, (data, err))
                self.assertFalse(os.path.exists(out), "lỗi đầu vào không tạo output")
            with open(w.path("nan.json"), "w", encoding="utf-8") as f:
                f.write('{"items":[{"id":"I1","kind":"ca_loc","fresh":NaN}]}')
            self.assertRaises(BadInput, read_inventory, w.path("nan.json"))

    def test_empty_and_valid_files_are_accepted(self):
        with Workdir() as w:
            for data in ({"items": []}, {"items": [{"id": "I2", "kind": "ca_loc", "fresh": 97.5},
                                                    {"id": "I1", "kind": "ca_linh", "fresh": 0}]}):
                inv = write_json(w.path("inv.json"), data)
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                         "--out", w.path("q.jsonl"))
                self.assertEqual(code, 0, err)

    def test_write_sorted_by_id_and_round_trip_keeps_threshold_branch(self):
        near = Fraction(30) + Fraction(1, 240)   # vừa trên ngưỡng
        under = Fraction(30) - Fraction(1, 240)  # vừa dưới ngưỡng
        items = [{"id": "I10", "kind": "ca_loc", "fresh": near}, {"id": "I2", "kind": "ca_linh", "fresh": under},
                 {"id": "I3", "kind": "bong_sung", "fresh": Fraction(1, 3)}]
        with Workdir() as w:
            p = w.path("inv.json")
            write_inventory(p, items)
            with open(p, encoding="utf-8") as f:
                raw = json.load(f)
            self.assertEqual([i["id"] for i in raw["items"]], ["I2", "I3", "I10"])
            back = {i["id"]: i["fresh"] for i in read_inventory(p)}
            self.assertGreaterEqual(back["I10"], 30)
            self.assertLess(back["I2"], 30)
            self.assertTrue(close(float(back["I3"]), 1 / 3, 1e-12))
            self.assertEqual(sorted(os.listdir(os.path.dirname(p))), ["inv.json"], "không để lại file tạm")


class GatherFresh(unittest.TestCase):
    def test_ticket_threshold_fixture_spoils_on_first_step(self):
        """Ví dụ của ticket: fresh đúng 30, một bước không input -> spoiled tick 1."""
        with Workdir() as w:
            code, err, rows, _ = gather_cli(w, {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                                                "random_fish": False, "monsters": []}, inventory_out=False)
        self.assertEqual(code, 0, err)
        self.assertEqual([r for r in events(rows) if r["name"] == "spoiled"],
                         [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                           "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}])

    def test_ticket_handoff_smoke_file_matches_one_decay_step(self):
        """Ví dụ của ticket: fresh 100, interact ở frame 0 -> cập bến; file sau đúng một lần hao."""
        scene = {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}], "random_fish": False, "monsters": []}
        with Workdir() as w:
            code, err, rows, inv = gather_cli(w, scene, input_frames=({"tick": 0, "interact": True},))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, {"items": [{"id": "I1", "kind": "ca_linh", "fresh": float(100 - STEP)}]})
            end = events(rows, "gather_end")[0]["data"]
            self.assertEqual(end["reason"], "docked")
            self.assertTrue(close(end["inventory"]["items"][0]["fresh"], 100 - 1 / 120, 0.01))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)

    def test_spoiled_exactly_once_and_ordered_by_id(self):
        hold = [{"id": "I10", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "bong_sung", "fresh": 30},
                {"id": "I3", "kind": "ca_linh", "fresh": 31}]
        s = sim({"hold": hold, "player": {"pos": [20, 0]}})
        first = s.step(IDLE)
        self.assertEqual([d["item_id"] for n, d in first if n == "spoiled"], ["I2", "I10"])
        rest = []
        for _ in range(200):  # I3 xuống dưới 30 sau đúng 120 bước
            rest += [(s.phase_tick, d["item_id"]) for n, d in s.step(IDLE) if n == "spoiled"]
        self.assertEqual(rest, [(121, "I3")])

    def test_decay_clamps_at_zero(self):
        s = sim({"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 0.005}], "player": {"pos": [20, 0]}})
        s.step(IDLE)
        self.assertEqual(s.hold[0]["fresh"], 0)
        s.step(IDLE)
        self.assertEqual(s.hold[0]["fresh"], 0)

    def test_new_item_fresh_100_and_decays_from_next_step(self):
        node = {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}
        s = sim({"nodes": [node], "player": {"pos": [20, 0]}, "hold": [{"id": "I7", "kind": "ca_loc", "fresh": 50}]})
        s.step(press("interact"))
        self.assertEqual([(i["id"], i["fresh"]) for i in s.hold], [("I7", 50 - STEP), ("I8", 100)])
        s.step(IDLE)
        self.assertEqual(s.hold[1]["fresh"], 100 - STEP)

    def test_catch_creates_one_item_per_unit_with_increasing_ids(self):
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [20, 5], "heading_deg": 0}]
        s = sim({"fish": fish, "player": {"pos": [20, 5]}})
        s.step(press("catch"))
        self.assertEqual([(i["id"], i["kind"], i["fresh"]) for i in s.hold],
                         [(f"I{k}", "ca_linh", 100) for k in (1, 2, 3)])

    def test_snapshot_hold_in_pickup_order_and_json_floats(self):
        hold = [{"id": "I5", "kind": "ca_loc", "fresh": 80}, {"id": "I2", "kind": "bong_sung", "fresh": 90}]
        with Workdir() as w:
            code, err, rows, _ = gather_cli(w, {"hold": hold, "player": {"pos": [20, 0]}, "random_fish": False,
                                                "monsters": [], "nodes": []}, ticks=60, inventory_out=False)
        self.assertEqual(code, 0, err)
        last = snapshots(rows)[-1]["hold"]
        self.assertEqual([i["id"] for i in last], ["I5", "I2"], "giỏ giữ thứ tự vào giỏ")
        self.assertTrue(close(last[0]["fresh"], 79.5, 0.01) and close(last[1]["fresh"], 89.5, 0.01), last)

    def test_monster_hit_and_faint_lost_are_items_lifo(self):
        hold = make_items(["ca_loc", "bong_sung", "ca_linh", "ca_keo"])
        croc = {"id": "M1", "kind": "ca_sau", "pos": [45, 20], "waypoints": [[45, 20], [49, 20]]}
        s = sim({"hold": hold, "player": {"pos": [45, 20], "hp": 1}, "monsters": [croc]})
        ev = dict(s.step(IDLE))
        self.assertEqual([i["id"] for i in ev["monster_hit"]["lost"]], ["I4", "I3"])
        self.assertEqual([i["id"] for i in ev["faint"]["lost"]], ["I2", "I1"])
        self.assertTrue(all(isinstance(i["fresh"], float) for i in ev["faint"]["lost"]))
        self.assertEqual(ev["gather_end"]["inventory"], {"items": []})

    def test_tick_limit_before_end_keeps_destination(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            with open(inv, "w", encoding="utf-8") as f:
                f.write("giữ nguyên")
            code, err, _, _ = gather_cli(w, {"hold": make_items(["ca_loc"])}, ticks=5)
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(f.read(), "giữ nguyên")

    def test_scenario_hold_rejects_count_or_bad_items(self):
        with Workdir() as w:
            for hold in (["ca_loc"], [{"id": "I1", "kind": "ca_loc", "fresh": 101}],
                         [{"id": "I1", "kind": "ca_loc", "fresh": 1}, {"id": "I1", "kind": "ca_loc", "fresh": 2}]):
                code, err, _, _ = gather_cli(w, {"hold": hold}, inventory_out=False)
                self.assertEqual(code, 2, (hold, err))


class DayIds(unittest.TestCase):
    def test_hold_template_keeps_ids_on_day_one_and_gets_new_ids_later(self):
        from chonoi.day import DaySession
        sc = {"gather": {"hold": [{"id": "I4", "kind": "ca_loc", "fresh": 80}], "time_left_ticks": 1},
              "quan": {"time_left_ticks": 1}}
        s = DaySession(T, sc, 1, days=2)
        self.assertEqual([(i["id"], i["fresh"]) for i in s.snapshot()["hold"]], [("I4", 80.0)])
        while s.day == 1:
            s.step(press("shop_done"))
        self.assertEqual(s.phase, "gather")
        self.assertEqual([(i["id"], i["kind"], i["fresh"]) for i in s.snapshot()["hold"]], [("I5", "ca_loc", 80.0)])


if __name__ == "__main__":
    unittest.main()
