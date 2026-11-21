"""Gather theo số chuẩn Test Contract v1.1: cá bơi/sinh, loài mới, nút N5/N6, contract."""

import math
import unittest

from chonoi.contract import load_contract, plan_ingredients
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

T = load_contract()["tuning"]
G = T["gather"]
IDLE = InputState((0.0, 0.0), set(), set())


def press(*names):
    return InputState((0.0, 0.0), set(names), set(names))


def sim(scenario=None, seed=1):
    return GatherSim(T, scenario or {}, Streams(seed), IdAllocator())


def run(s, ticks):
    events = []
    for _ in range(ticks):
        events += s.step(IDLE)
    return events


def one_fish(kind="ca_loc", pos=(50, 14), heading=0, **extra):
    return dict({"id": "F1", "kind": kind, "pos": list(pos), "heading_deg": heading}, **extra)


class Contract(unittest.TestCase):
    def test_version_and_standard_numbers(self):
        self.assertIn(load_contract()["contract_version"], ("1.1", "1.2"))  # v1.2 giữ số chuẩn v1.1
        self.assertEqual((G["duration_s"], G["oxygen_max_s"], G["hold_capacity"]), (180, 30, 12))
        self.assertEqual(G["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual([(n["id"], n["kind"]) for n in G["nodes"]][4:], [("N5", "keo_neo"), ("N6", "keo_neo")])
        self.assertEqual(len(T["menu"]), 6)

    def test_spawn_table_has_36_pairs_30_geometric_points(self):
        pairs = {(k, x, d) for k, ds in G["fish_spawn_depths"].items() for x in G["fish_spawn_x"] for d in ds}
        points = {(x, d) for _, x, d in pairs}
        self.assertEqual((len(pairs), len(points)), (36, 30))

    def test_day_plan_matches_ticket(self):
        need = {1: 9, 2: 10, 3: 12, 4: 9, 5: 10}
        for p in T["day_plan"]:
            self.assertEqual(sum(p["ingredients"].values()), need[p["day"]])
            self.assertEqual(p["ingredients"], plan_ingredients(p["dishes"], T["menu"]))

    def test_shop_upgrades(self):
        up = T["shop"]["upgrades"]
        self.assertEqual([(lv["price"], lv["oxygen_max_s"]) for lv in up["oxygen"]], [(200, 45), (400, 60)])
        self.assertEqual([(lv["price"], lv["hp_max"]) for lv in up["hp"]], [(250, 4), (500, 5)])
        self.assertEqual(T["shop"]["max_ticks"], 600)


class Fish(unittest.TestCase):
    def test_initial_eight_schools_at_distinct_spawn_points(self):
        s = sim()
        self.assertEqual(len(s.fish), 8)
        self.assertEqual(len({tuple(f["pos"]) for f in s.fish}), 8)
        for f in s.fish:
            self.assertIn(f["pos"][0], G["fish_spawn_x"])
            self.assertIn(f["pos"][1], G["fish_spawn_depths"][f["kind"]])
        self.assertEqual([f["id"] for f in s.fish], [f"F{i}" for i in range(1, 9)])

    def test_same_seed_same_world_different_seed_differs(self):
        a, b, c = sim(seed=3), sim(seed=3), sim(seed=4)
        run(a, 400), run(b, 400), run(c, 400)
        self.assertEqual(a.snapshot()["fish"], b.snapshot()["fish"])
        self.assertNotEqual(a.snapshot()["fish"], c.snapshot()["fish"])

    def test_swim_speed_and_age(self):
        s = sim({"fish": [one_fish()]})
        run(s, 60)
        self.assertAlmostEqual(s.fish[0]["pos"][0], 51.5, places=6)
        self.assertEqual(s.fish[0]["age_ticks"], 60)

    def test_turn_on_swim_step_120_before_moving(self):
        s = sim({"fish": [one_fish()]})
        run(s, 119)
        self.assertEqual(s.fish[0]["heading_deg"], 0)
        run(s, 1)
        self.assertNotEqual(s.fish[0]["heading_deg"], 0)
        # bước 120 đã đi theo hướng mới: vị trí không còn nằm trên trục d = 14
        self.assertNotAlmostEqual(s.fish[0]["pos"][1], 14.0, places=6)

    def test_age_offset_from_scenario(self):
        s = sim({"fish": [one_fish(age_ticks=119)]})
        run(s, 1)
        self.assertNotEqual(s.fish[0]["heading_deg"], 0)

    def test_reflect_x_edge_keeps_leftover_distance(self):
        hix = G["fish_x"][1]
        s = sim({"fish": [one_fish(pos=(hix - 0.01, 14))]})
        run(s, 1)
        f = s.fish[0]
        self.assertAlmostEqual(f["pos"][0], hix - (1.5 / 60 - 0.01), places=9)
        self.assertAlmostEqual(f["heading_deg"], 180.0, places=9)

    def test_reflect_corner_flips_both(self):
        hix, lod = G["fish_x"][1], G["fish_depths"]["ca_loc"][0]
        s = sim({"fish": [one_fish(pos=(hix - 0.001, lod + 0.001), heading=315)]})
        run(s, 1)
        f = s.fish[0]
        self.assertAlmostEqual(f["heading_deg"], 135.0, places=9)  # 315° đảo cả hai thành phần
        self.assertTrue(f["pos"][0] <= hix and f["pos"][1] >= lod)

    def test_fish_stay_in_species_bands(self):
        s = sim(seed=7)
        for _ in range(2000):
            s.step(IDLE)
            for f in s.fish:
                lo, hi = G["fish_depths"][f["kind"]]
                self.assertTrue(G["fish_x"][0] <= f["pos"][0] <= G["fish_x"][1], f)
                self.assertTrue(lo <= f["pos"][1] <= hi, f)

    def test_spawn_every_360_up_to_cap_with_event(self):
        s = sim(seed=2)
        ticks = []
        for tick in range(1, 361):
            ticks += [(tick, d) for n, d in s.step(IDLE) if n == "fish_spawned"]
        self.assertEqual([t for t, _ in ticks], [360])
        self.assertEqual(len(s.fish), 9)
        new = s.fish[-1]
        self.assertEqual((new["id"], new["age_ticks"]), ("F9", 0))
        self.assertEqual(ticks[0][1], {"id": "F9", "kind": new["kind"], "pos": new["pos"]})
        run(s, 360 * 8)
        self.assertEqual(len(s.fish), G["fish_max"])

    def test_spawn_skips_species_without_valid_point(self):
        # mọi điểm kèo đã có đàn chiếm -> loài kèo bị loại, trọng số chuẩn hóa lại trên linh/lóc
        pts = [[float(x), float(d)] for x in G["fish_spawn_x"] for d in G["fish_spawn_depths"]["ca_keo"]]
        fish = [dict(one_fish("ca_keo", p), id=f"F{i}") for i, p in enumerate(pts, 1)]
        s = sim({"fish": fish})
        s.t = dict(s.t, fish_max=99)  # 12 đàn kèo đã chạm trần mặc định; nới trần để chỉ thử luật điểm hợp lệ
        s.phase_tick = 359
        ev = s.step(IDLE)
        new = [d for n, d in ev if n == "fish_spawned"]
        self.assertEqual(len(new), 1)
        self.assertNotEqual(new[0]["kind"], "ca_keo")
        for f in s.fish:
            if f["id"] != new[0]["id"]:
                self.assertGreater(math.dist(f["pos"], new[0]["pos"]), G["fish_spawn_clearance"])

    def test_random_fish_false_freezes_and_no_spawn(self):
        s = sim({"fish": [one_fish()], "random_fish": False})
        ev = run(s, 800)
        self.assertEqual(s.fish[0]["pos"], [50.0, 14.0])
        self.assertEqual(len(s.fish), 1)
        self.assertEqual([n for n, _ in ev if n == "fish_spawned"], [])
        self.assertEqual(len(sim({"random_fish": False}).fish), 0)

    def test_fixture_with_random_fish_true_replaces_initial_and_swims(self):
        s = sim({"fish": [one_fish("ca_linh", (50, 6))]})
        self.assertEqual(len(s.fish), 1)
        run(s, 30)
        self.assertNotEqual(s.fish[0]["pos"], [50.0, 6.0])

    def test_no_swim_after_time_ends(self):
        s = sim({"fish": [one_fish()], "time_left_ticks": 1})
        run(s, 1)
        self.assertTrue(s.done)
        self.assertEqual(s.fish[0]["age_ticks"], 0)


class Species(unittest.TestCase):
    def test_ca_keo_yield_two_and_full_hold_keeps_school(self):
        scene = {"fish": [one_fish("ca_keo", (30, 24))], "random_fish": False, "player": {"pos": [30, 24]}}
        s = sim(scene)
        ev = s.step(press("catch"))
        self.assertEqual([it["kind"] for it in s.hold], ["ca_keo", "ca_keo"])
        self.assertEqual([n for n, _ in ev], ["fish_caught"])
        full = sim(dict(scene, hold=[{"id": f"I{i}", "kind": "ca_loc", "fresh": 100} for i in range(1, 12)]))
        ev = full.step(press("catch"))
        self.assertEqual(len(full.fish), 1)
        self.assertEqual(ev[0][0], "hold_full")
        self.assertEqual(full.catch_cd_ticks, 0)

    def test_keo_neo_node_gathers_at_surface(self):
        s = sim({"player": {"pos": [76, 0]}})
        ev = s.step(press("interact"))
        self.assertEqual([it["kind"] for it in s.hold], ["keo_neo"])
        self.assertEqual(ev[0][1]["node_id"], "N5")


if __name__ == "__main__":
    unittest.main()
