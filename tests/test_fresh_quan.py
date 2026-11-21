"""Độ tươi ở quán — Ticket-03 "Mùa Nước Nổi" (Test Contract v1.2; AC-P3-04, 05, 06). Lát Quán.

Test HỘP ĐEN qua headless_cmd; số đọc từ game.contract.json (freshness, menu, quan).
Kho quán là mảng cá thể {id, kind, fresh}; độ tươi so ngưỡng bằng đơn vị nguyên 240/điểm.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_fresh_quan -v
"""

import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


T = tuning()
Q, MENU, FR = T["quan"], T["menu"], T["freshness"]
UNITS = 240
DECAY = round(FR["quan_decay_per_s"] * UNITS / 60)   # đơn vị mất mỗi tick ở quán
FIRST = Q["first_customer_tick"]
STOVE = Q["stoves"][0]["pos"]
TABLE = Q["tables"][0]["pos"]


def item(iid, kind, fresh):
    return {"id": iid, "kind": kind, "fresh": fresh}


def cust(cid, table, dish, **kw):
    c = {"id": cid, "table_id": table, "dish_id": dish}
    c.update(kw)
    return c


def run_quan(w, block, ticks, inputs=None, every=1):
    args = ["--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", str(every),
            "--scenario", write_json(w.path("sc.json"), {"quan": block}), "--out", w.path("q.jsonl")]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(f"mã thoát {code}: {err}")
    return read_jsonl(w.path("q.jsonl"))


def ev(rows, name):
    return [(r["tick"], r["data"]) for r in events(rows, name)]


def snap_at(rows, tick):
    return next(r for r in snapshots(rows) if r["tick"] == tick)


def fresh_after(fresh, ticks):
    return max(0, fresh * UNITS - DECAY * ticks) / UNITS


def fresh_price(price, units):
    return price * sum(units) // (len(units) * UNITS * 100)


class Decay(unittest.TestCase):
    def test_hao_moi_giay_ke_ca_hang_dang_giu(self):
        block = {"random_customers": False, "stock": [item("S1", "ca_loc", 100)],
                 "customers": [cust("C1", "T1", "ca_loc_nuong_trui", reserved=["S1"])]}
        with Workdir() as w:
            rows = run_quan(w, block, 240, every=60)
        for t in (60, 240):
            s = snap_at(rows, t)
            self.assertAlmostEqual(s["stock"][0]["fresh"], 100 - FR["quan_decay_per_s"] * t / 60, delta=0.01)
            self.assertEqual(s["customers"][0]["reserved"], ["S1"])

    def test_spoiled_dung_mot_lan_theo_id_va_hang_uon_van_trong_kho(self):
        just_above = FR["spoiled_below"] + 1 / UNITS   # còn đúng 1 đơn vị trên ngưỡng
        block = {"random_customers": False,
                 "stock": [item("S2", "bong_sung", 30), item("S1", "ca_loc", 30),
                           item("S3", "ca_linh", just_above), item("S4", "ca_keo", 10)]}
        with Workdir() as w:
            rows = run_quan(w, block, 20)
        self.assertEqual(ev(rows, "spoiled"),
                         [(1, {"item_id": "S1", "kind": "ca_loc", "location": "stock"}),
                          (1, {"item_id": "S2", "kind": "bong_sung", "location": "stock"}),
                          (2, {"item_id": "S3", "kind": "ca_linh", "location": "stock"})])
        last = snapshots(rows)[-1]["stock"]
        self.assertEqual([i["id"] for i in last], ["S1", "S2", "S3", "S4"], "ươn vẫn chiếm chỗ, xuất theo id")
        self.assertAlmostEqual(last[3]["fresh"], fresh_after(10, 20), delta=0.01)

    def test_hang_uon_khong_tinh_kha_dung(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": [item("S1", "ca_loc", 29)]}, FIRST, every=FIRST)
        self.assertEqual(ev(rows, "no_dish"), [(FIRST, {})])
        with Workdir() as w:
            rows = run_quan(w, {"stock": [item("S1", "ca_loc", 29), item("S2", "ca_loc", 31)]}, FIRST, every=FIRST)
        self.assertEqual(snapshots(rows)[-1]["customers"][0]["reserved"], ["S2"], "bỏ qua cá thể ươn dù id nhỏ hơn")


class Reserve(unittest.TestCase):
    def test_khach_moi_giu_ca_the_tuoi_nhat_hoa_theo_id(self):
        stock = [item("S1", "ca_loc", 50), item("S2", "ca_loc", 90), item("S3", "ca_loc", 90)]
        with Workdir() as w:
            rows = run_quan(w, {"stock": stock}, FIRST, every=FIRST)
        c = snapshots(rows)[-1]["customers"][0]
        self.assertEqual((c["dish_id"], c["reserved"]), ("ca_loc_nuong_trui", ["S2"]))

    def test_fixture_bo_reserved_tu_cap_theo_order_tick_roi_ban(self):
        stock = [item("S1", "ca_loc", 50), item("S2", "ca_loc", 90)]
        block = {"random_customers": False, "stock": stock,
                 "customers": [cust("C1", "T2", "ca_loc_nuong_trui"), cust("C2", "T1", "ca_loc_nuong_trui")]}
        with Workdir() as w:
            s = snapshots(run_quan(w, block, 0))[0]
        self.assertEqual({c["id"]: c["reserved"] for c in s["customers"]}, {"C1": ["S1"], "C2": ["S2"]})

    def test_phan_giu_vua_uon_nha_toan_bo_roi_giu_lai(self):
        stock = [item("S1", "ca_linh", 30), item("S2", "ca_linh", 100), item("S3", "ca_linh", 100),
                 item("S4", "ca_linh", 60), item("S5", "bong_dien_dien", 100)]
        block = {"random_customers": False, "stock": stock,
                 "customers": [cust("C1", "T1", "lau_ca_linh_dien_dien", reserved=["S1", "S2", "S3", "S5"])]}
        with Workdir() as w:
            rows = run_quan(w, block, 1)
        self.assertEqual(ev(rows, "spoiled"), [(1, {"item_id": "S1", "kind": "ca_linh", "location": "stock"})])
        c = snap_at(rows, 1)["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["S2", "S3", "S4", "S5"]))

    def test_phan_giu_vua_uon_khong_du_thi_unfulfillable_va_cho_toi_han(self):
        block = {"random_customers": False, "stock": [item("S1", "ca_loc", 30)],
                 "customers": [cust("C1", "T1", "ca_loc_nuong_trui", reserved=["S1"], patience_ticks_left=5)]}
        with Workdir() as w:
            rows = run_quan(w, block, 6)
        c = snap_at(rows, 1)["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("unfulfillable", []))
        (tick, left), = ev(rows, "customer_left")
        self.assertEqual((tick, left["reason"]), (5, "patience"))
        self.assertAlmostEqual(left["reputation"], Q["reputation_initial"] + Q["left_reputation_delta"], delta=0.01)

    def test_nhieu_don_dinh_uon_xu_ly_theo_order_tick_roi_id_ban(self):
        stock = [item("S1", "ca_loc", 30), item("S2", "ca_loc", 30), item("S3", "ca_loc", 90)]
        for ticks, winner, loser in (((0, 0), "C2", "C1"),    # cùng order_tick -> bàn T1 (C2) trước
                                     ((0, 5), "C1", "C2")):   # C1 gọi trước -> C1 trước
            block = {"random_customers": False, "stock": stock,
                     "customers": [cust("C1", "T2", "ca_loc_nuong_trui", reserved=["S1"], order_tick=ticks[0]),
                                   cust("C2", "T1", "ca_loc_nuong_trui", reserved=["S2"], order_tick=ticks[1])]}
            with Workdir() as w:
                s = snap_at(run_quan(w, block, 1), 1)
            got = {c["id"]: (c["order_status"], c["reserved"]) for c in s["customers"]}
            self.assertEqual(got, {winner: ("reserved", ["S3"]), loser: ("unfulfillable", [])}, ticks)


class Price(unittest.TestCase):
    def test_bat_dau_nau_tieu_dung_id_giu_va_chot_gia_theo_tuoi(self):
        dish = "goi_bong_sung"
        block = {"player": {"pos": STOVE}, "random_customers": False,
                 "stock": [item("S1", "bong_sung", 60), item("S2", "bong_sung", 75.5), item("S3", "bong_sung", 100)],
                 "customers": [cust("C1", "T1", dish, reserved=["S1", "S2"])]}
        with Workdir() as w:
            rows = run_quan(w, block, 1, [{"tick": 0, "interact": True}])
        units = [60 * UNITS - DECAY, int(75.5 * UNITS) - DECAY]   # đã hao ở bước 0 trước khi nấu
        price = fresh_price(MENU[dish]["price"], units)
        self.assertLess(price, MENU[dish]["price"])
        (tick, cs), = ev(rows, "cook_started")
        self.assertEqual((tick, cs["base_price"]), (1, price))
        self.assertEqual([i["id"] for i in cs["items"]], ["S1", "S2"])
        for i, u in zip(cs["items"], units):
            self.assertAlmostEqual(i["fresh"], u / UNITS, delta=0.01)
        s = snap_at(rows, 1)
        self.assertEqual([i["id"] for i in s["stock"]], ["S3"], "chỉ tiêu đúng các id đang giữ")
        self.assertEqual((s["customers"][0]["base_price"], s["stoves"][0]["dish"]["base_price"]), (price, price))

    def test_cook_started_items_sap_theo_kind_roi_id(self):
        dish = "lau_ca_linh_dien_dien"
        block = {"player": {"pos": STOVE}, "random_customers": False,
                 "stock": [item("S10", "ca_linh", 100), item("S2", "bong_dien_dien", 100),
                           item("S3", "ca_linh", 100), item("S9", "ca_linh", 100)],
                 "customers": [cust("C1", "T1", dish, reserved=["S10", "S2", "S3", "S9"])]}
        with Workdir() as w:
            (_, cs), = ev(run_quan(w, block, 1, [{"tick": 0, "interact": True}]), "cook_started")
        self.assertEqual([(i["kind"], i["id"]) for i in cs["items"]],
                         [("bong_dien_dien", "S2"), ("ca_linh", "S3"), ("ca_linh", "S9"), ("ca_linh", "S10")])
        self.assertEqual(cs["base_price"], fresh_price(MENU[dish]["price"], [100 * UNITS - DECAY] * 4))

    def test_boa_tinh_tren_gia_da_chot(self):
        locked = 27
        block = {"player": {"pos": TABLE}, "random_customers": False,
                 "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": locked},
                 "customers": [cust("C1", "T1", "goi_bong_sung", order_status="assigned")]}
        with Workdir() as w:
            rows = run_quan(w, block, 1 + round(Q["eat_s"] * 60), [{"tick": 0, "interact": True}], every=100)
        tip = math.floor(locked * Q["tip_rate"] + 1e-9)
        self.assertEqual((ev(rows, "served")[0][1]["base_price"], ev(rows, "served")[0][1]["tip"]), (locked, tip))
        self.assertEqual(ev(rows, "paid")[0][1]["amount"], locked + tip)


class FixtureV12(unittest.TestCase):
    def test_scenario_stock_reserved_sai_ma_2(self):
        loc = cust("C1", "T1", "ca_loc_nuong_trui")
        bad = [
            {"stock": {"ca_loc": 1}},                                                      # kho đếm cũ
            {"stock": [item("S1", "ca_loc", 100.5)]},                                      # fresh ngoài [0,100]
            {"stock": [item("S1", "ca_loc", -1)]},
            {"stock": [item("S1", "ca_loc", "tuoi")]},
            {"stock": [item("S1", "ca_loc", 90), item("S1", "bong_sung", 90)]},           # id trùng
            {"stock": [item("S1", "ca_la_lung", 90)]},                                     # kind lạ
            {"stock": [dict(item("S1", "ca_loc", 90), note="x")]},                         # khóa lạ
            {"stock": [{"id": "S1", "kind": "ca_loc"}]},                                   # thiếu fresh
            {"stock": [item("", "ca_loc", 90)]},                                           # id rỗng
            {"stock": [], "customers": [dict(loc, reserved=["S1"])]},                     # id không có trong kho
            {"stock": [item("S1", "ca_loc", 29.9)], "customers": [dict(loc, reserved=["S1"])]},   # giữ hàng ươn
            {"stock": [item("S1", "bong_sung", 90)], "customers": [dict(loc, reserved=["S1"])]},  # khác công thức
            {"stock": [item("S1", "ca_loc", 90)], "customers": [dict(loc, reserved=["S1", "S1"])]},
            {"stock": [item("S1", "ca_loc", 90)],                                          # dùng chung giữa 2 đơn
             "customers": [dict(loc, reserved=["S1"]), cust("C2", "T2", "ca_loc_nuong_trui", reserved=["S1"])]},
            {"stock": [item("S1", "ca_loc", 90)], "customers": [dict(loc, reserved={"ca_loc": 1})]},
            {"stock": [item("S1", "ca_loc", 90)],                                          # đơn assigned còn giữ
             "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
             "customers": [dict(loc, order_status="assigned", reserved=["S1"])]},
        ]
        for block in bad:
            with Workdir() as w:
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario",
                                       write_json(w.path("sc.json"), {"quan": block}), "--out", w.path("q.jsonl"))
                self.assertEqual(code, 2, block)

    def test_giu_ca_the_dung_nguong_30_hop_le(self):
        block = {"random_customers": False, "stock": [item("S1", "ca_loc", 30)],
                 "customers": [cust("C1", "T1", "ca_loc_nuong_trui", reserved=["S1"])]}
        with Workdir() as w:
            self.assertEqual(snapshots(run_quan(w, block, 0))[0]["customers"][0]["reserved"], ["S1"])


if __name__ == "__main__":
    unittest.main()
