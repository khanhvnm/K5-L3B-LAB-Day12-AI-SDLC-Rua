"""Cá Sấu Năm Chèo, Máu và ngất (Ticket-02 §1.2, Test Contract v1.1 §4.3–§4.5; AC-P2-04). Lát B.

Phần lớn là test HỘP ĐEN qua headless_cmd; số liệu đọc từ game.contract.json.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_monsters -v
"""

import json
import math
import unittest

from helpers import Workdir, close, events, frames, kinds_of, make_items, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


T = tuning()
G = T["gather"]
MON = G["monsters"]
SP = MON["species"]["ca_sau"]
THR = SP["depths"][0]
INVULN = MON["invuln_ticks"]
RECOIL = SP["recoil_ticks"]


def run_gather(w, block, ticks, inputs=None, extra=()):
    """gather không cá (để cá không cản), snapshot mỗi tick; trả các dòng JSONL."""
    sc = {"random_fish": False, "fish": []}
    sc.update(block)
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
            "--scenario", write_json(w.path("sc.json"), {"gather": sc}), "--out", w.path("g.jsonl"), *extra]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(f"mã thoát {code}: {err}")
    return read_jsonl(w.path("g.jsonl"))


def croc(pos, **kw):
    """Cá Sấu fixture M1 tuần tra quanh `pos` (waypoint đầu là vị trí xuất phát)."""
    m = {"id": "M1", "kind": "ca_sau", "pos": pos, "waypoints": [pos, [pos[0] + 4, pos[1]]]}
    m.update(kw)
    return m


def hits(rows):
    return [(r["tick"], r["data"]) for r in events(rows, "monster_hit")]


def snap_by_tick(rows):
    return {r["tick"]: r for r in snapshots(rows)}


class Layout(unittest.TestCase):
    def test_gather_doc_lap_dung_bo_tri_ngay_1(self):
        with Workdir() as w:
            m = snapshots(run_gather(w, {}, 0))[0]["monsters"]
        want = [{"id": s["id"], "kind": s["kind"], "pos": s["pos"], "waypoints": s["waypoints"], "target_idx": 1,
                 "state": "patrol", "state_ticks_left": 0, "recoil_dir": None}
                for s in MON["spawns"] if s["from_day"] <= 1]
        self.assertEqual(m, want)

    def test_bo_tri_theo_ngay(self):
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim
        tu = load_contract()["tuning"]
        for day, want in ((1, ["M1"]), (2, ["M1"]), (3, ["M1", "M2"]), (5, ["M1", "M2"])):
            sim = GatherSim(tu, {"random_fish": False}, Streams(1), IdAllocator(), day=day)
            self.assertEqual([m["id"] for m in sim.monsters], want, day)


class Movement(unittest.TestCase):
    def test_tuan_tra_toi_waypoint_roi_doi_dich(self):
        m1 = next(s for s in MON["spawns"] if s["id"] == "M1")
        (a, b) = m1["waypoints"]
        span = math.dist(a, b)
        arrive = math.ceil(span / (SP["patrol_speed"] / 60))
        with Workdir() as w:
            s = snap_by_tick(run_gather(w, {}, arrive + 60))  # người chơi ở bến, trên mặt nước
        self.assertTrue(close(s[60]["monsters"][0]["pos"][0], a[0] + SP["patrol_speed"]), s[60]["monsters"][0])
        first_turn = min(t for t, r in s.items() if r["monsters"][0]["target_idx"] == 0)
        self.assertLessEqual(abs(first_turn - arrive), 2)
        self.assertTrue(close(s[arrive + 60]["monsters"][0]["pos"][0], b[0] - SP["patrol_speed"]))

    def test_nguoi_choi_nong_khong_bi_phat_hien_hay_cham(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, THR - 1]}, "monsters": [croc([51, THR])]}, 120)
        self.assertEqual(hits(rows), [])
        self.assertTrue(all(r["monsters"][0]["state"] == "patrol" for r in snapshots(rows)))

    def test_roi_chase_khi_len_nong_hoac_qua_xa(self):
        for player, want in (([50, THR - 5], "patrol"),                         # lên d < ngưỡng
                             ([50 + SP["exit_radius"] + 5, 20], "patrol"),       # cách > exit_radius
                             ([50 + SP["detect_radius"], 20], "chase")):         # vẫn trong tầm
            with Workdir() as w:
                s = snap_by_tick(run_gather(w, {"player": {"pos": player},
                                                "monsters": [croc([50, 20], state="chase")]}, 1))
            self.assertEqual(s[1]["monsters"][0]["state"], want, player)


class Hit(unittest.TestCase):
    START, PLAYER = [50, 20], [45, 20]
    HOLD = make_items(["ca_loc", "bong_sung", "ca_linh"])  # v1.2: kho cá thể

    def expected_hit_tick(self):
        gap = math.dist(self.START, self.PLAYER) - SP["hit_radius"]
        return math.ceil(gap / (SP["chase_speed"] / 60))

    def test_duoi_theo_roi_cham_mat_mau_rot_hang_lifo(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": self.PLAYER}, "hold": self.HOLD,
                                  "monsters": [croc(self.START)]}, self.expected_hit_tick() + 5)
        (tick, data), = hits(rows)
        self.assertLessEqual(abs(tick - self.expected_hit_tick()), 2)
        lost_n = math.floor(len(self.HOLD) * MON["loss_ratio"])
        self.assertEqual(data["monster_id"], "M1")
        self.assertEqual(data["hp"], G["hp_max"] - 1)
        self.assertEqual(kinds_of(data["lost"]), kinds_of(list(reversed(self.HOLD))[:lost_n]))
        self.assertEqual(data["pos"], self.PLAYER)
        s = snap_by_tick(rows)[tick]
        self.assertEqual(s["player"]["invuln_ticks"], INVULN)
        self.assertEqual(kinds_of(s["hold"]), kinds_of(self.HOLD[:len(self.HOLD) - lost_n]))
        m = s["monsters"][0]
        self.assertEqual((m["state"], m["state_ticks_left"]), ("recoil", RECOIL))
        self.assertTrue(close(m["recoil_dir"][0], 1, 0.01) and close(m["recoil_dir"][1], 0, 0.01), m)

    def test_recoil_lui_dung_quang_roi_tuan_tra_va_bat_tu_chan_hit(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": self.PLAYER}, "monsters": [croc(self.START)]},
                              self.expected_hit_tick() + INVULN + 80)
        ticks = [t for t, _ in hits(rows)]
        self.assertGreaterEqual(len(ticks), 2)
        self.assertGreaterEqual(ticks[1] - ticks[0], INVULN, "bất tử chặn hit")
        s = snap_by_tick(rows)
        h = ticks[0]
        x0 = s[h]["monsters"][0]["pos"][0]
        mid = s[h + RECOIL // 2]["monsters"][0]
        self.assertEqual((mid["state"], mid["state_ticks_left"]), ("recoil", RECOIL - RECOIL // 2))
        end = s[h + RECOIL]["monsters"][0]
        self.assertEqual((end["state"], end["recoil_dir"]), ("patrol", None))
        self.assertTrue(close(end["pos"][0] - x0, SP["recoil_dist"], 0.01), (x0, end))

    def test_dang_bat_tu_thi_khong_bi_cham(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": self.PLAYER, "invuln_ticks": 50},
                                  "monsters": [croc(self.PLAYER)]}, 60)
        self.assertEqual([t for t, _ in hits(rows)][:1], [50])

    def test_het_mau_vi_ca_sau_thi_ngat_kho_rong(self):
        hold = make_items(["ca_loc", "bong_sung", "ca_linh", "ca_keo"])  # v1.2: kho cá thể
        with Workdir() as w:
            inv = w.path("inv.json")
            rows = run_gather(w, {"player": {"pos": self.PLAYER, "hp": 1}, "hold": hold,
                                  "monsters": [croc(self.PLAYER)]}, 10, extra=("--inventory-out", inv))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})
        names = [(r["tick"], r["name"]) for r in events(rows)]
        self.assertEqual(names, [(1, "monster_hit"), (1, "faint"), (1, "gather_end")])
        ev = {r["name"]: r["data"] for r in events(rows)}
        self.assertEqual(kinds_of(ev["monster_hit"]["lost"]), ["ca_keo", "ca_linh"])
        self.assertEqual((ev["faint"]["cause"], kinds_of(ev["faint"]["lost"]), ev["faint"]["hp"]),
                         ("monster", ["bong_sung", "ca_loc"], 0))
        self.assertEqual(ev["gather_end"], {"reason": "fainted", "inventory": {"items": []}})
        self.assertEqual(rows[-1]["reason"], "fainted")
        self.assertEqual(snapshots(rows)[-1]["monsters"][0]["recoil_dir"], [1.0, 0.0], "trùng tâm dùng +x")


class Fixture(unittest.TestCase):
    def test_fixture_sai_ma_2(self):
        bad = [
            [croc([50, THR - 5])],                                 # ngoài dải độ sâu của loài
            [croc([50, 20], kind="ca_map")],
            [croc([50, 20], mood="doi")],
            [dict(croc([50, 20]), waypoints=[[50, 20]])],
            [croc([50, 20], target_idx=2)],
            [croc([50, 20], state="stunned", state_ticks_left=5)],  # chỉ có khi bật mở rộng Lao
            [croc([50, 20], state="recoil")],
            [croc([50, 20], state="recoil", state_ticks_left=5, recoil_dir=[1, 1])],
            [croc([50, 20], recoil_dir=[1, 0])],
            [croc([50, 20], state_ticks_left=5)],
            [croc([50, 20]), croc([60, 20])],                      # id trùng
            [{"id": "M9", "kind": "ca_sau"}],                       # không có spawn cùng id để lấy pos
        ]
        for monsters in bad:
            with Workdir() as w:
                sc = write_json(w.path("sc.json"), {"gather": {"monsters": monsters}})
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                       "--out", w.path("g.jsonl"))
                self.assertEqual(code, 2, monsters)

    def test_fixture_hop_le(self):
        with Workdir() as w:
            self.assertEqual(snapshots(run_gather(w, {"monsters": []}, 0))[0]["monsters"], [])
        with Workdir() as w:
            m = snapshots(run_gather(w, {"monsters": [{"id": "M1"}]}, 0))[0]["monsters"][0]
            self.assertEqual((m["pos"], m["state"]), (next(s["pos"] for s in MON["spawns"] if s["id"] == "M1"), "patrol"))
        with Workdir() as w:
            rows = run_gather(w, {"monsters": [croc([50, 20], state="recoil", state_ticks_left=3, recoil_dir=[0, 1])]}, 3)
            m = snap_by_tick(rows)[3]["monsters"][0]
            self.assertEqual(m["state"], "patrol")
            self.assertTrue(close(m["pos"][1], 20 + 3 * SP["recoil_dist"] / RECOIL, 0.001))


if __name__ == "__main__":
    unittest.main()
