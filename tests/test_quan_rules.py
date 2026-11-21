"""Luật quán (PRD-0 mục D, E, F) — test HỘP ĐEN qua headless_cmd, đọc số từ game.contract.json.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_rules -v
"""

import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


T = tuning()
Q, MENU = T["quan"], T["menu"]
STOVE = Q["stoves"][0]["pos"]
TABLE = Q["tables"][0]["pos"]
PATIENCE = int(round(Q["patience_s"] * 60))
EAT = int(round(Q["eat_s"] * 60))
FIRST = Q["first_customer_tick"]
INTERVAL = int(round(Q["customer_interval_s"] * 60))


def cook_ticks(dish):
    return int(round(MENU[dish]["cook_s"] * 60))


def tip_of(price):
    return math.floor(price * Q["tip_rate"] + 1e-9)


def run_quan(w, block, ticks, inputs=None, seed=1, every=None):
    """Chạy quan với scenario `block`; trả các dòng JSONL. Lỗi nếu mã thoát khác 0."""
    args = ["--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("q.jsonl")]
    if block is not None:
        args += ["--scenario", write_json(w.path("sc.json"), {"quan": block})]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if every:
        args += ["--snapshot-every", str(every)]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(f"mã thoát {code}: {err}")
    return read_jsonl(w.path("q.jsonl"))


def ev(rows, name):
    return [(r["tick"], r["data"]) for r in events(rows, name)]


def served_fixture(patience, dish="goi_bong_sung"):
    """Khách C1 ở T1 đã có món trên tay người chơi, người chơi đứng ngay tại bàn."""
    return {"player": {"pos": TABLE}, "random_customers": False,
            "hand": {"order_id": "C1", "dish_id": dish, "base_price": MENU[dish]["price"]},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish, "order_status": "assigned",
                           "patience_ticks_left": patience}]}


class Snapshot(unittest.TestCase):
    def test_snapshot_tick0_dung_truong(self):
        with Workdir() as w:
            s = snapshots(run_quan(w, {"stock": {"ca_loc": 1}}, 0))[0]
            self.assertEqual(s["mode"], "quan")
            self.assertEqual(set(s["player"]), {"pos", "vel"})
            self.assertEqual(s["stock"], {"ca_loc": 1})
            self.assertIsNone(s["hand"])
            self.assertEqual(set(s["stoves"][0]), {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"})
            self.assertEqual(s["stoves"][0]["state"], "idle")
            self.assertEqual(s["tables"], [{"id": "T1", "pos": TABLE, "customer_id": None}])
            self.assertEqual(s["customers"], [])
            self.assertEqual((s["money"], s["earned"], s["reputation"]), (0, 0, Q["reputation_initial"]))


class Customers(unittest.TestCase):
    def test_khach_den_dung_lich_chon_mon_nau_duoc_va_giu_cho(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1, "bong_sung": 1}}, FIRST)
            self.assertEqual(ev(rows, "customer_arrived"),
                             [(FIRST, {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})])
            s = snapshots(rows)[-1]
            c = s["customers"][0]
            self.assertEqual((c["order_tick"], c["state"], c["order_status"]), (FIRST, "waiting", "reserved"))
            self.assertEqual(c["reserved"], {"ca_loc": 1})
            self.assertEqual(c["patience_ticks_left"], PATIENCE)
            self.assertEqual(s["stock"], {"bong_sung": 1, "ca_loc": 1}, "stock là tồn vật lý, gồm phần giữ")
            self.assertEqual(s["tables"][0]["customer_id"], "C1")
        with Workdir() as w:
            self.assertEqual(ev(run_quan(w, {"stock": {"ca_loc": 1}}, FIRST - 1), "customer_arrived"), [])

    def test_no_dish_khi_khong_mon_nao_du_nguyen_lieu(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_linh": 2, "bong_sung": 1}}, FIRST)
            self.assertEqual(ev(rows, "no_dish"), [(FIRST, {})])
            self.assertEqual(snapshots(rows)[-1]["customers"], [])

    def test_het_ban_thi_bo_luot(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 5}}, FIRST + INTERVAL)
            self.assertEqual(len(ev(rows, "customer_arrived")), 1)
            self.assertEqual(ev(rows, "no_dish"), [])

    def test_khach_roi_nha_phan_giu_cho_khach_sau(self):
        """C1 giữ con cá lóc duy nhất rồi bỏ đi -> phần giữ được nhả, khách mới (id nối tiếp C2) gọi lại được."""
        with Workdir() as w:
            block = {"stock": {"ca_loc": 1}, "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 5}]}
            rows = run_quan(w, block, FIRST)
            self.assertEqual(ev(rows, "customer_left")[0][1]["reason"], "patience")
            # khách rời -> nhả phần giữ -> khách mới gọi được lại cá lóc
            self.assertEqual(ev(rows, "customer_arrived"),
                             [(FIRST, {"order_id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})])

    def test_chon_mon_deu_theo_seed_va_tat_dinh(self):
        stock = {"ca_loc": 9, "ca_linh": 9, "bong_dien_dien": 9, "bong_sung": 9}
        seen = set()
        for seed in range(1, 25):
            with Workdir() as w:
                a = ev(run_quan(w, {"stock": stock}, FIRST, seed=seed), "customer_arrived")
                b = ev(run_quan(w, {"stock": stock}, FIRST, seed=seed), "customer_arrived")
                self.assertEqual(a, b)
                seen.add(a[0][1]["dish_id"])
        self.assertEqual(seen, set(MENU))

    def test_het_kien_nhan_tru_uy_tin_va_bo_mon_dang_nau(self):
        with Workdir() as w:
            block = {"random_customers": False,
                     "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 100,
                                 "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                     "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                    "order_status": "assigned", "patience_ticks_left": 3}]}
            rows = run_quan(w, block, 5)
            want_rep = Q["reputation_initial"] + Q["left_reputation_delta"]
            self.assertEqual(ev(rows, "customer_left"),
                             [(3, {"order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": want_rep})])
            s = snapshots(rows)[-1]
            self.assertEqual(s["stoves"][0]["state"], "idle")
            self.assertIsNone(s["stoves"][0]["dish"])
            self.assertEqual(s["customers"], [])
            self.assertEqual(s["reputation"], want_rep)

    def test_giu_cho_thieu_hang_thanh_unfulfillable(self):
        """Giả định ghi trong docs/clarify.md: đơn reserved không khai reserved mà kho không đủ -> unfulfillable."""
        with Workdir() as w:
            block = {"random_customers": False,
                     "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
            c = snapshots(run_quan(w, block, 0))[0]["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"]), ("unfulfillable", {}))


class KitchenAndService(unittest.TestCase):
    def test_nau_bung_phuc_vu_tra_tien_tron_vong(self):
        dish = "goi_bong_sung"
        ck = cook_ticks(dish)
        dx, dz = TABLE[0] - STOVE[0], TABLE[1] - STOVE[1]
        n = math.hypot(dx, dz)
        walk = round(n / Q["walk_speed"] * 60)  # ramp lên + ramp xuống bù nhau
        pick, start, stop = ck + 1, ck + 2, ck + 2 + walk
        serve = stop + 20
        block = {"player": {"pos": STOVE}, "stock": {"bong_sung": 2}, "random_customers": False,
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish}]}
        inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                  {"tick": pick, "interact": True}, {"tick": start, "interact": False, "move": [dx / n, dz / n]},
                  {"tick": stop, "move": [0, 0]}, {"tick": serve, "interact": True}]
        with Workdir() as w:
            rows = run_quan(w, block, serve + 1 + EAT, inputs, every=1)
            price = MENU[dish]["price"]
            self.assertEqual(ev(rows, "cook_started"),
                             [(1, {"stove_id": "B1", "order_id": "C1", "dish_id": dish,
                                   "items": ["bong_sung", "bong_sung"], "base_price": price})])
            self.assertEqual(ev(rows, "dish_ready"), [(1 + ck, {"stove_id": "B1", "order_id": "C1", "dish_id": dish})])
            self.assertEqual(ev(rows, "dish_picked"), [(pick + 1, {"stove_id": "B1", "order_id": "C1", "dish_id": dish})])
            snap = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(snap[1]["stock"], {}, "nấu tiêu đúng phần giữ")
            self.assertEqual(snap[1]["customers"][0]["order_status"], "assigned")
            self.assertEqual(snap[pick + 1]["hand"], {"order_id": "C1", "dish_id": dish, "base_price": price})
            self.assertEqual(snap[pick + 1]["stoves"][0]["state"], "idle")
            tip = tip_of(price)
            self.assertEqual(ev(rows, "served"),
                             [(serve + 1, {"order_id": "C1", "table_id": "T1", "dish_id": dish,
                                           "patience_ticks_left": PATIENCE - serve - 1, "base_price": price, "tip": tip})])
            self.assertEqual(ev(rows, "paid"),
                             [(serve + 1 + EAT, {"order_id": "C1", "table_id": "T1", "base_price": price, "tip": tip,
                                                 "amount": price + tip, "reason": "finished_eating"})])
            last = snapshots(rows)[-1]
            rep = round(Q["reputation_initial"] + Q["tip_reputation"], 6)
            self.assertEqual((last["money"], last["earned"]), (price + tip, price + tip))
            self.assertAlmostEqual(last["reputation"], rep, places=2)
            self.assertEqual(last["score"], price + tip + T["score"]["reputation_multiplier"] * math.floor(rep))
            self.assertEqual(last["customers"], [])

    def test_boa_theo_ty_le_kien_nhan_sau_buoc_1(self):
        price = MENU["goi_bong_sung"]["price"]
        need = math.ceil(PATIENCE * Q["tip_min_patience_ratio"])  # kiên nhẫn sau bước 1 tối thiểu để có boa
        for start, tip in ((need + 1, tip_of(price)), (need, 0)):
            with Workdir() as w:
                rows = run_quan(w, served_fixture(start), EAT + 1, [{"tick": 0, "interact": True}])
                self.assertEqual(ev(rows, "served")[0][1]["tip"], tip, start)
                paid = ev(rows, "paid")
                self.assertEqual(paid[0][0], 1 + EAT)
                self.assertEqual(paid[0][1]["amount"], price + tip)
                want = Q["reputation_initial"] + (Q["tip_reputation"] if tip else 0)
                self.assertAlmostEqual(snapshots(rows)[-1]["reputation"], want, places=2)

    def test_phuc_vu_dung_tick_kien_nhan_ve_0_van_hop_le(self):
        with Workdir() as w:
            rows = run_quan(w, served_fixture(1), 2, [{"tick": 0, "interact": True}])
            self.assertEqual(ev(rows, "served")[0][1]["patience_ticks_left"], 0)
            self.assertEqual(ev(rows, "customer_left"), [])

    def test_uu_tien_bep_truoc_ban_khi_bang_khoang_cach_va_bo_luot(self):
        """Bếp và bàn cách đều: chọn bếp; bếp idle không có đơn reserved -> bỏ lượt, KHÔNG phục vụ bàn."""
        block = dict(served_fixture(PATIENCE), player={"pos": [6, 5]},
                     stoves=[{"id": "B1", "pos": [5, 5]}], tables=[{"id": "T1", "pos": [7, 5]}])
        with Workdir() as w:
            rows = run_quan(w, block, 2, [{"tick": 0, "interact": True}])
            self.assertEqual(ev(rows, "served"), [])
            self.assertEqual(ev(rows, "cook_started"), [])
        block["player"] = {"pos": [6.1, 5]}  # bàn gần hơn -> phục vụ
        with Workdir() as w:
            self.assertEqual(len(ev(run_quan(w, block, 2, [{"tick": 0, "interact": True}]), "served")), 1)

    def test_bep_dang_nau_thi_bo_luot(self):
        block = {"player": {"pos": STOVE}, "random_customers": False,
                 "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 50,
                             "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "assigned"}]}
        with Workdir() as w:
            rows = run_quan(w, block, 2, [{"tick": 0, "interact": True}], every=1)
            self.assertEqual([r["name"] for r in events(rows)], [])
            s = snapshots(rows)[-1]
            self.assertEqual((s["stoves"][0]["state"], s["stoves"][0]["cook_ticks_left"]), ("cooking", 48))
            self.assertIsNone(s["hand"])

    def test_bep_ready_tang_ready_ticks(self):
        block = {"random_customers": False,
                 "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 1,
                             "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "assigned"}]}
        with Workdir() as w:
            rows = run_quan(w, block, 4, every=1)
            self.assertEqual([t for t, _ in ev(rows, "dish_ready")], [1])
            snap = {r["tick"]: r["stoves"][0] for r in snapshots(rows)}
            self.assertEqual([snap[t]["ready_ticks"] for t in (1, 2, 4)], [0, 1, 3])


class Closing(unittest.TestCase):
    def test_het_ca_khach_dang_an_tra_ngay(self):
        block = {"time_left_ticks": 5, "random_customers": False,
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                                "order_status": "served", "eat_ticks_left": 100, "base_price": 40, "tip": 8}]}
        with Workdir() as w:
            rows = run_quan(w, block, 100)
            self.assertEqual(ev(rows, "paid"), [(5, {"order_id": "C1", "table_id": "T1", "base_price": 40, "tip": 8,
                                                     "amount": 48, "reason": "closing"})])
            rep = Q["reputation_initial"] + Q["tip_reputation"]
            (tick, end), = ev(rows, "quan_end")
            self.assertEqual(tick, 5)
            self.assertEqual({k: end[k] for k in ("reason", "money", "earned", "shift_earned")},
                             {"reason": "time", "money": 48, "earned": 48, "shift_earned": 48})
            self.assertAlmostEqual(end["reputation"], rep, places=2)
            last = rows[-1]
            self.assertEqual((last["type"], last["reason"], last["state"], last["ticks"]), ("end", "time", "finished", 5))
            self.assertEqual(last["score"], 48 + T["score"]["reputation_multiplier"] * math.floor(rep))

    def test_het_ca_khach_cho_roi_closing_khong_tru_uy_tin(self):
        block = {"time_left_ticks": 3, "stock": {"ca_loc": 1}, "random_customers": False,
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 3}]}
        with Workdir() as w:
            rows = run_quan(w, block, 10)
            self.assertEqual(ev(rows, "customer_left"),
                             [(3, {"order_id": "C1", "table_id": "T1", "reason": "closing",
                                   "reputation": Q["reputation_initial"]})])
            self.assertEqual(snapshots(rows)[-1]["stock"], {"ca_loc": 1}, "nhả phần giữ, tồn vật lý giữ nguyên")

    def test_ca_day_du_tat_dinh_tung_byte(self):
        stock = {"ca_loc": 3, "ca_linh": 6, "bong_dien_dien": 2, "bong_sung": 4}
        out = []
        for i in (1, 2):
            with Workdir() as w:
                run_quan(w, {"stock": stock}, 99999, seed=11)
                with open(w.path("q.jsonl"), "rb") as f:
                    out.append(f.read())
        self.assertEqual(out[0], out[1])
        last = json.loads(out[0].decode("utf-8").splitlines()[-1])
        self.assertEqual((last["reason"], last["ticks"]), ("time", int(Q["duration_s"] * 60)))


class FixtureErrors(unittest.TestCase):
    def test_fixture_mau_thuan_exit_2(self):
        c1 = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        loc = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        assigned = dict(c1, order_status="assigned")
        bad = [
            {"customers": [{"id": "C1", "table_id": "T1"}]},                                    # thiếu món
            {"customers": [dict(c1, dish_id="bun_rieu")]},                                      # món ngoài thực đơn
            {"customers": [dict(c1, mood="vui")]},                                              # trường lạ
            {"customers": [dict(c1, state="ngu")]},
            {"stock": {"ca_loc": 2}, "customers": [dict(c1, reserved={"ca_loc": 2})]},          # giữ khác công thức
            {"stock": {}, "customers": [dict(c1, reserved={"ca_loc": 1})]},                     # giữ quá tồn
            {"customers": [assigned]},                                                          # assigned không có món
            {"hand": loc, "stoves": [{"id": "B1", "state": "ready", "dish": loc}], "customers": [assigned]},
            {"hand": dict(loc, dish_id="goi_bong_sung"), "customers": [assigned]},              # món không khớp đơn
            {"hand": loc, "customers": [c1]},                                                   # tay giữ đơn reserved
            {"hand": dict(loc, order_id="C9"), "customers": [assigned]},                        # liên kết thiếu
            {"customers": [dict(c1, state="eating", order_status="served", eat_ticks_left=10)]},  # thiếu giá/tip
            {"customers": [dict(c1, eat_ticks_left=5)]},                                        # chờ mà đang ăn
            {"customers": [dict(c1, patience_ticks_left=PATIENCE + 1)]},
            {"customers": [dict(c1, order_tick=-1)]},
            {"stoves": [{"id": "B1", "dish": loc}], "hand": None, "customers": [assigned]},     # idle có món
            {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 0, "dish": loc}], "customers": [assigned]},
            {"stoves": [{"id": "B9", "pos": [1, 1]}]},
            {"tables": [{"id": "T1", "pos": [20, 1]}]},
            {"reputation": 9},
            {"random_customers": "khong"},
        ]
        for block in bad:
            with Workdir() as w:
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario",
                                       write_json(w.path("sc.json"), {"quan": block}), "--out", w.path("q.jsonl"))
                self.assertEqual(code, 2, block)

    def test_fixture_hop_le_exit_0(self):
        loc = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        good = [
            {"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                    "reserved": {"ca_loc": 1}}]},
            {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 10, "dish": loc}],
             "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}]},
            {"hand": loc, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                         "order_status": "assigned"}]},
            {"reputation": 4.5, "random_customers": False, "time_left_ticks": 60},
        ]
        for block in good:
            with Workdir() as w:
                run_quan(w, block, 1)


if __name__ == "__main__":
    unittest.main()
