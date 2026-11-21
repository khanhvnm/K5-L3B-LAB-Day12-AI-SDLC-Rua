"""Kế hoạch ngày D1–D5 và lọc menu theo kế hoạch (Ticket-02 mục 2, AC-P2-05/06).

Test mức Python (starter): chế độ day headless do lát D làm, nên ở đây gọi thẳng dayplan và QuanSim.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_day_plan -v
"""

import copy
import json
import unittest

from chonoi.contract import load_contract, validate_tuning
from chonoi.dayplan import day_plan_event, plan_for_day, plan_ingredients, resolve_day_plan
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

TUNING = load_contract()["tuning"]
FIRST = TUNING["quan"]["first_customer_tick"]
ALL_STOCK = {k: 9 for k in ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung", "ca_keo", "keo_neo")}
IDLE = InputState((0.0, 0.0), {}, set())

# Bảng D1–D5 chép từ Ticket-02 mục 2 (đúng thứ tự khóa của bảng)
EXPECTED = {
    1: ({"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, {"ca_loc": 3, "bong_sung": 6}),
    2: ({"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2}, {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2}),
    3: ({"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2},
        {"bong_sung": 4, "ca_loc": 2, "bong_dien_dien": 2, "ca_keo": 4}),
    4: ({"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1},
        {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1, "ca_loc": 2, "bong_sung": 2}),
    5: ({"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1},
        {"ca_linh": 5, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 2, "ca_loc": 1}),
}


class DayPlan(unittest.TestCase):
    def test_preset_khop_bang_ticket(self):
        plans = resolve_day_plan(TUNING)
        for day, (dishes, ingredients) in EXPECTED.items():
            p = plan_for_day(plans, day)
            self.assertEqual(p["day"], day)
            self.assertEqual(list(p["dishes"].items()), list(dishes.items()), day)
            self.assertEqual(list(p["ingredients"].items()), list(ingredients.items()), day)

    def test_event_d1_giong_vi_du_ticket(self):
        name, data = day_plan_event(plan_for_day(resolve_day_plan(TUNING), 1))
        self.assertEqual(name, "day_plan")
        self.assertEqual(json.dumps(data, separators=(",", ":")),
                         '{"dishes":{"ca_loc_nuong_trui":3,"goi_bong_sung":3},"ingredients":{"ca_loc":3,"bong_sung":6}}')

    def test_ingredients_la_cong_thuc_nhan_suat(self):
        self.assertEqual(plan_ingredients({"lau_mam": 2, "ca_keo_nuong": 1}, TUNING["menu"]),
                         {"ca_linh": 4, "ca_keo": 4, "keo_neo": 2, "bong_dien_dien": 2})

    def test_scenario_ghi_de_theo_ngay_va_tinh_lai(self):
        plans = resolve_day_plan(TUNING, [{"day": 2, "dishes": {"ca_keo_nuong": 1}},
                                          {"day": 4, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 2}}])
        self.assertEqual(plans[1], {"day": 2, "dishes": {"ca_keo_nuong": 1}, "ingredients": {"ca_keo": 2}})
        self.assertEqual(plans[3]["ingredients"], {"bong_sung": 2})
        self.assertEqual(plans[0]["dishes"], EXPECTED[1][0], "Ngày không ghi đè giữ preset")

    def test_scenario_ghi_de_sai_bao_loi(self):
        bad = [
            [{"day": 6, "dishes": {"lau_mam": 1}}],
            [{"day": 0, "dishes": {"lau_mam": 1}}],
            [{"day": 1, "dishes": {}}],
            [{"day": 1, "dishes": {"bun_rieu": 1}}],
            [{"day": 1, "dishes": {"lau_mam": 0}}],
            [{"day": 1, "dishes": {"lau_mam": 1}, "ingredients": {"ca_linh": 1}}],
            [{"day": 1, "dishes": {"lau_mam": 1}}, {"day": 1, "dishes": {"goi_bong_sung": 1}}],
            [{"day": 1, "dishes": {"lau_mam": 1}, "note": "x"}],
            {"day": 1, "dishes": {"lau_mam": 1}},
        ]
        for overrides in bad:
            with self.assertRaises(BadInput, msg=overrides):
                resolve_day_plan(TUNING, overrides)

    def test_contract_day_plan_sai_bao_loi(self):
        for mutate in (lambda t: t["day_plan"][0]["ingredients"].update(ca_loc=4),
                       lambda t: t["day_plan"].pop(),
                       lambda t: t["day_plan"][1].update(day=3),
                       lambda t: t["menu"]["lau_mam"]["recipe"].update(ca_la_lung=1)):
            t = copy.deepcopy(TUNING)
            mutate(t)
            with self.assertRaises(BadInput):
                validate_tuning(t)


def as_items(counts):
    """Kho đếm -> kho cá thể v1.2 (fresh ban đầu), id S1, S2, …"""
    out = []
    for kind, n in counts.items():
        for _ in range(n):
            out.append({"id": f"S{len(out) + 1}", "kind": kind, "fresh": TUNING["freshness"]["initial"]})
    return out


class QuanTheoKeHoach(unittest.TestCase):
    def first_customer(self, stock, plan, seed=1):
        sim = QuanSim(TUNING, {"stock": as_items(stock)}, Streams(seed), IdAllocator(), plan_dishes=plan)
        events = []
        for _ in range(FIRST):
            events += sim.step(IDLE)
        return events

    def test_quan_rieng_ban_ca_6_mon(self):
        sim = QuanSim(TUNING, {}, Streams(1), IdAllocator())
        self.assertEqual(sim.dish_pool, sorted(TUNING["menu"]))
        self.assertEqual(len(sim.dish_pool), 6)

    def test_loc_theo_ke_hoach_truoc_khi_loc_kho(self):
        """Kho đủ mọi món nhưng kế hoạch D1 chỉ có 2 món: khách chỉ gọi 2 món đó."""
        plan = EXPECTED[1][0]
        seen = set()
        for seed in range(1, 21):
            (name, data), = [e for e in self.first_customer(ALL_STOCK, plan, seed) if e[0] == "customer_arrived"]
            seen.add(data["dish_id"])
        self.assertEqual(seen, set(plan))

    def test_mon_du_hang_nhung_ngoai_ke_hoach_thi_no_dish(self):
        events = self.first_customer({"ca_keo": 2}, EXPECTED[1][0])
        self.assertEqual(events, [("no_dish", {})])

    def test_khach_fixture_goi_mon_ngoai_ke_hoach_ma_2(self):
        scenario = {"stock": as_items({"ca_keo": 2}),
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong"}]}
        with self.assertRaises(BadInput):
            QuanSim(TUNING, scenario, Streams(1), IdAllocator(), plan_dishes=EXPECTED[1][0])
        QuanSim(TUNING, scenario, Streams(1), IdAllocator(), plan_dishes=EXPECTED[3][0])  # D3 có cá kèo nướng


if __name__ == "__main__":
    unittest.main()
