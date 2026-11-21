"""TICKET-02: kiểm tích hợp vòng ngày với preset và Shop v1.1."""
import json
import os
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.day import DaySession
from chonoi.headless import main
from chonoi.inputs import BUTTONS_V11, InputPlayer, InputState
from chonoi.live import LiveGame
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def day_tuning(shop_ticks=2):
    tuning = load_contract()["tuning"]
    tuning["shop"]["max_ticks"] = shop_ticks
    return tuning


def input_state(*edges, buy=None):
    return InputState((0, 0), {}, set(edges), buy)


class DayTests(unittest.TestCase):
    def test_two_days_jsonl_pause_buy_order_and_handoff(self):
        tuning = day_tuning()
        scenario = {
            "day": {"money": 200, "earned": 200, "day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 2}}]},
            "gather": {"hold": ["ca_loc", "bong_sung"], "time_left_ticks": 1},
            "quan": {"time_left_ticks": 1},
        }
        with Workdir() as w, patch("chonoi.headless.load_contract", return_value={"tuning": tuning}):
            sc = write_json(w.path("scenario.json"), scenario)
            inputs = write_json(w.path("input.json"), frames(
                {"tick": 0, "interact": True, "shop_done": True},
                {"tick": 2, "pause": True, "buy": "oxygen"},
                {"tick": 3, "pause": False, "shop_done": False},
                {"tick": 4, "pause": True},
                {"tick": 5, "shop_done": True, "buy": "oxygen"},
            ))
            args = ["--mode", "day", "--days", "2", "--ticks", "100", "--seed", "1",
                    "--scenario", sc, "--inputs", inputs, "--snapshot-every", "80"]
            a, b = w.path("a.jsonl"), w.path("b.jsonl")
            self.assertEqual(main([*args, "--out", a]), 0)
            self.assertEqual(main([*args, "--out", b]), 0)
            with open(a, "rb") as first, open(b, "rb") as second:
                self.assertEqual(first.read(), second.read())
            rows = read_jsonl(a)
        self.assertEqual([r["name"] for r in rows[:3]], ["day_start", "day_plan", "phase_start"])
        self.assertEqual(rows[1]["data"]["ingredients"], {"ca_loc": 2})
        boundaries = [(r["tick"], r["day"], r["phase"], r["phase_tick"]) for r in snapshots(rows)]
        self.assertEqual(boundaries, [(0, 1, "gather", 0), (1, 1, "quan", 0), (2, 1, "shop", 0),
                                      (6, 2, "gather", 0), (7, 2, "quan", 0), (8, 2, "shop", 0), (10, 2, "shop", 2)])
        snapshot = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual(snapshot[1]["stock"], {"ca_loc": 1, "bong_sung": 1})
        self.assertEqual(snapshot[2]["active_upgrades"], {})
        self.assertEqual(snapshot[6]["active_upgrades"], {"oxygen": 1})
        self.assertEqual(snapshot[6]["player"]["oxygen_ticks"], 2700)
        self.assertEqual(snapshot[6]["sim_tick"], 4)
        self.assertEqual([(r["phase"], r["name"]) for r in events(rows) if r["tick"] == 1],
                         [("gather", "gather_end"), ("quan", "phase_start")])
        self.assertEqual([(r["phase"], r["name"]) for r in events(rows) if r["tick"] == 6],
                         [("shop", "bought"), ("shop", "shop_end"), ("gather", "day_start"),
                          ("gather", "day_plan"), ("gather", "phase_start")])
        self.assertEqual([r["tick"] for r in events(rows, "paused")], [3])
        self.assertEqual([r["tick"] for r in events(rows, "resumed")], [5])
        self.assertEqual([r["data"]["reason"] for r in events(rows, "shop_end")], ["done", "time"])
        self.assertEqual((rows[-1]["money"], rows[-1]["earned"], rows[-1]["days_completed"], rows[-1]["reason"]),
                         (0, 200, 2, "days_complete"))

    def test_faint_handoff_and_last_tick_shop(self):
        sc = {"day": {"money": 200, "earned": 200},
              "gather": {"hold": ["ca_loc"], "player": {"pos": [30, 10], "oxygen_ticks": 0,
                                                       "zero_oxy_ticks": 59, "hp": 1}},
              "quan": {"time_left_ticks": 1}}
        s = DaySession(day_tuning(1), sc, 1)
        rows = s.step(input_state("interact"))
        self.assertEqual([r["name"] for r in rows], ["choke", "faint", "gather_end", "phase_start"])
        self.assertEqual((s.snapshot()["phase_tick"], s.snapshot()["stock"]), (0, {}))
        s.step(input_state())
        before = s.snapshot()
        self.assertEqual([r["name"] for r in s.step(input_state("pause", "shop_done", buy="oxygen"))], ["paused"])
        self.assertEqual(s.snapshot(), dict(before, tick=before["tick"] + 1, state="paused"))
        rows = s.step(input_state("pause", "shop_done", buy="oxygen"))
        self.assertEqual([r["name"] for r in rows], ["resumed", "bought", "shop_end"])
        self.assertEqual(rows[-1]["data"], {"reason": "done"})
        self.assertEqual(s.end_row()["reason"], "days_complete")
        self.assertEqual(s.snapshot()["upgrades"], {"oxygen": 1})
        self.assertEqual(s.snapshot()["active_upgrades"], {})

    def test_bad_day_scenarios_do_not_publish_partial_output(self):
        with Workdir() as w:
            dest = w.path("out.jsonl")
            cases = [
                {"day": {"money": 1}},
                {"day": {"day_plan": [{"day": [], "dishes": {}}]}},
                {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": True}}]}},
                {"quan": {"stock": {}}},
                {"quan": {"reputation": 3}},
                {"gather": {"time_left_ticks": 1, "hold": ["ca_keo", "ca_keo"]},
                 "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong"}]}},
                {"gather": {"time_left_ticks": 1, "hold": ["ca_loc"]},
                 "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                         "reserved": {"ca_loc": 1}},]}},
            ]
            # Ca cuối có đủ kho trong fixture, nhưng ngất nên kho thật không đủ.
            cases[-1]["gather"]["player"] = {"pos": [30, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1}
            for data in cases:
                with self.subTest(data=data):
                    sc = write_json(w.path("scenario.json"), data)
                    self.assertEqual(main(["--mode", "day", "--seed", "1", "--ticks", "10",
                                           "--scenario", sc, "--out", dest]), 2)
                    self.assertFalse(os.path.exists(dest))
            self.assertEqual(sorted(os.listdir(os.path.dirname(dest))), ["scenario.json"])

    def test_plan_filters_menu_without_capping_sales(self):
        sc = {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}}]},
              "gather": {"hold": ["bong_sung", "bong_sung", "ca_loc", "ca_loc"], "time_left_ticks": 1}}
        tuning = day_tuning()
        s = DaySession(tuning, sc, 1)
        s.step(input_state())
        self.assertEqual(s.snapshot()["stock"], {"bong_sung": 2, "ca_loc": 2})
        close_tick = tuning["quan"]["first_customer_tick"] + s.sim.interval_ticks
        for _ in range(close_tick):
            s.step(input_state())
        self.assertEqual([c["dish_id"] for c in s.snapshot()["customers"]], ["ca_loc_nuong_trui"] * 2)

    def test_pause_standalone_keeps_timers_and_discards_actions(self):
        for mode in ("gather", "quan"):
            with Workdir() as w:
                inp = write_json(w.path("inputs.json"), frames(
                    {"tick": 0, "pause": True, "interact": True},
                    {"tick": 1, "pause": False},
                    {"tick": 2, "pause": True},
                ))
                dest = w.path("out.jsonl")
                self.assertEqual(main(["--mode", mode, "--seed", "1", "--ticks", "3", "--inputs", inp,
                                       "--snapshot-every", "1", "--out", dest]), 0)
                rows = read_jsonl(dest)
                first, paused, still_paused, resumed = snapshots(rows)
                self.assertEqual(paused, dict(first, tick=1, state="paused"))
                self.assertEqual(still_paused, dict(paused, tick=2))
                self.assertEqual((resumed["sim_tick"], resumed["phase_tick"], resumed["time_left_ticks"]),
                                 (1, 1, first["time_left_ticks"] - 1))
                self.assertEqual([r["name"] for r in events(rows)], ["paused", "resumed"])

    def test_buy_does_not_inherit(self):
        player = InputPlayer([{"tick": 0, "buy": "hp", "shop_done": True}], BUTTONS_V11)
        self.assertTrue(player.advance(0).pressed("shop_done"))
        following = player.advance(1)
        self.assertIsNone(following.buy)
        self.assertFalse(following.pressed("shop_done"))

    def test_live_screens_gate_the_clock_and_summary(self):
        sc = {"gather": {"hold": ["ca_loc"], "time_left_ticks": 1}, "quan": {"time_left_ticks": 1}}
        game = LiveGame("day", day_tuning(), sc, 42)

        def state():
            return json.loads(game.state_json())

        self.assertEqual(state()["screen"], "menu")
        first_id = state()["screen_id"]
        game.advance(first_id)
        game.advance(first_id)  # yêu cầu cũ không được bỏ qua màn kế
        for screen, tick in (("day_intro", 0), ("evening_intro", 1), ("day_result", 2)):
            game._tick_once()
            self.assertEqual((state()["screen"], state()["tick"]), (screen, tick))
            game.advance(state()["screen_id"])
            game._tick_once()
        game.set_input({"shop_done": True})
        game._tick_once()
        self.assertEqual((state()["screen"], state()["reason"]), ("summary", "days_complete"))
        game.menu()
        game.advance(state()["screen_id"])
        self.assertEqual((state()["screen"], state()["tick"]), ("day_intro", 0))

    def test_real_cli_five_days_with_default_monster_spawns(self):
        tuning = load_contract()["tuning"]
        with Workdir() as w:
            sc = write_json(w.path("scenario.json"), {"gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1}})
            output = w.path("day.jsonl")
            ticks = 5 * (2 + tuning["shop"]["max_ticks"])
            code, err = run_headless("--mode", "day", "--days", "5", "--seed", "1",
                                     "--ticks", str(ticks), "--scenario", sc, "--out", output)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(output)
        dawns = [row for row in snapshots(rows) if row["phase"] == "gather" and row["phase_tick"] == 0]
        self.assertEqual([row["day_plan"] for row in dawns], tuning["day_plan"])
        self.assertEqual([[m["id"] for m in row["monsters"]] for row in dawns],
                         [["M1"], ["M1"], ["M1", "M2"], ["M1", "M2"], ["M1", "M2"]])
        self.assertEqual([row["data"]["reason"] for row in events(rows, "shop_end")], ["time"] * 5)
        self.assertEqual((rows[-1]["ticks"], rows[-1]["days_completed"], rows[-1]["reason"]), (ticks, 5, "days_complete"))
