"""Buổi tối — Mở Quán (`quan`). Luật theo PRD-0 mục D (fixture), E (event/snapshot), F (một bước).

Nhà bè nhìn từ trên xuống: vị trí `[x, z]`, `z` hướng bắc.

Một bước k -> k+1 (PRD-0 mục F, "Quán"):
  1. đồng hồ: phase_tick + 1; giảm timer ca, nấu, ăn, kiên nhẫn; tăng ready_ticks của món đã ready từ đầu bước
  2. bếp theo id: nấu xong -> ready (ready_ticks = 0), phát dish_ready
  3. di chuyển, rồi tối đa MỘT interact, chọn theo (khoảng cách, bếp trước bàn, id); không dùng được thì bỏ lượt
  4. theo id bàn: khách ăn xong trả tiền (paid) rồi rời bàn; còn giờ: khách chờ hết kiên nhẫn rời (patience);
     hết giờ: khách đang ăn trả ngay, khách chờ rời (closing), phát quan_end và dừng
  5. còn giờ: lượt khách mới theo lịch (first_customer_tick, rồi mỗi customer_interval_s × 60 tick)

Contract v1.1: 2 bếp, 4 bàn, 6 món đọc từ tuning; trong chế độ day chỉ bán món thuộc kế hoạch Ngày.
Món (trên bếp hoặc trên tay) là payload {order_id, dish_id, base_price}, order_id = id khách.

Contract v1.2 (Ticket-03 "Mùa Nước Nổi"), lát Quán:
  - Kho là mảng CÁ THỂ {id, kind, fresh}, gồm cả hàng đang giữ và hàng ươn (ươn vẫn chiếm chỗ, không dùng nấu).
  - Độ tươi lưu bằng số nguyên UNITS = 240 đơn vị/điểm: quán hao 0.25/s = 1 đơn vị/tick, ngưỡng ươn 30 = 7200
    -> so ngưỡng và floor giá chính xác. Xuất ra fresh = units / 240.
  - Bước 1b (sau đồng hồ, trước món chín): hao tươi mọi cá thể, phát `spoiled` theo id khi đi từ ≥ 30 xuống < 30,
    rồi đơn nào có phần giữ vừa ươn thì nhả toàn bộ và thử giữ lại đúng một lần (theo order_tick rồi id bàn);
    không đủ -> unfulfillable.
  - Giữ chỗ theo id: mỗi loại trong công thức lấy cá thể khả dụng (chưa ươn, chưa ai giữ) tươi nhất, hòa theo id.
  - Bắt đầu nấu: tiêu đúng các id đang giữ, base_price = floor(giá niêm yết × trung bình fresh / 100).
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60
UNITS = 240  # đơn vị nguyên mỗi điểm tươi (Ticket-03 gợi ý): ngưỡng 30 và floor giá không lệch vì float
STOVE_FIELDS = ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")


def _units(fresh) -> int:
    return int(round(float(fresh) * UNITS))


def _item_out(it) -> dict:
    return {"id": it["id"], "kind": it["kind"], "fresh": it["units"] / UNITS}


def _ticks(seconds) -> int:
    return int(round(seconds * TICK))


def _exact(x) -> Fraction:
    """Số cấu hình -> phân số đúng như viết trong JSON (0.2 -> 1/5): floor/so sánh không lệch vì sai số float."""
    return Fraction(str(x))


def _clean_items(items) -> dict:
    return {k: items[k] for k in sorted(items) if items[k] > 0}


def _payload(p):
    if p is None:
        return None
    return {"order_id": p["order_id"], "dish_id": p["dish_id"], "base_price": p["base_price"]}


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, plan_dishes=None):
        """`plan_dishes`: map/danh sách id món trong kế hoạch Ngày (chế độ day). None = quán chạy riêng,
        bán cả thực đơn. Trong day, lọc menu theo kế hoạch TRƯỚC khi lọc nguyên liệu khả dụng (v1.1 §4.5)."""
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        # ứng viên món duyệt theo thứ tự cố định: id món theo mã Unicode
        self.dish_pool = sorted(d for d in self.menu if plan_dishes is None or d in plan_dishes)
        self.rng = streams
        self.ids = ids
        self.patience_full = _ticks(t["patience_s"])
        self.eat_full = _ticks(t["eat_s"])
        self.interval_ticks = _ticks(t["customer_interval_s"])
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # độ tươi (v1.2): số đọc từ tuning.freshness, đổi sang đơn vị nguyên
        fr = tuning["freshness"]
        self.initial_units = _units(fr["initial"])
        self.spoil_units = Fraction(str(fr["spoiled_below"])) * UNITS
        decay = Fraction(str(fr["quan_decay_per_s"])) * UNITS / TICK
        if decay.denominator != 1:
            raise BadInput("freshness.quan_decay_per_s phải ứng với số nguyên đơn vị tươi mỗi tick")
        self.decay_units = int(decay)
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2); thiếu cả hai -> kho rỗng
        self.items = self._items_from(inventory if inventory is not None else scenario.get("stock", []))
        self.hand = _payload(scenario.get("hand"))
        self.phase_tick = 0
        self.time_left_ticks = scenario.get("time_left_ticks", _ticks(t["duration_s"]))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.random_customers = scenario.get("random_customers", True)
        self.stoves = [{"id": s["id"], "pos": [float(c) for c in s["pos"]], "state": s.get("state", "idle"),
                        "dish": _payload(s.get("dish")), "cook_ticks_left": s.get("cook_ticks_left", 0),
                        "ready_ticks": s.get("ready_ticks", 0)}
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = [{"id": tb["id"], "pos": [float(c) for c in tb["pos"]]}
                       for tb in self._merge(t["tables"], scenario.get("tables", []))]
        self.customers = [self._customer_from_fixture(c) for c in scenario.get("customers", [])]
        for c in self.customers:
            ids.reserve(c["id"])
        self._check_fixture()
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- dựng fixture (PRD-0 mục D) ------------------------------------------------
    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _customer_from_fixture(self, c):
        return {"id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                "order_tick": c.get("order_tick", 0), "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", self.patience_full),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": c.get("order_status", "reserved"),
                "reserved": list(c["reserved"]) if "reserved" in c else None,
                "base_price": c.get("base_price"), "tip": c.get("tip")}

    def _items_from(self, src) -> list:
        """Kho cá thể nội bộ {id, kind, units}, sắp theo id; id được giữ chỗ trong IdAllocator (họ I tăng tiếp)."""
        if isinstance(src, dict):
            # TẠM, chờ lát S/G: đầu đọc/gather cũ còn trả kho ĐẾM -> cấp cá thể mới, fresh ban đầu.
            out = [{"id": self.ids.new("I"), "kind": k, "units": self.initial_units}
                   for k in sorted(src) for _ in range(src[k])]
        else:
            out = [{"id": it["id"], "kind": it["kind"],
                    "units": it["units"] if "units" in it else _units(it["fresh"])} for it in src]
            for it in out:
                self.ids.reserve(it["id"])
        return sort_by_id(out)

    def _recipe(self, dish_id) -> dict:
        return _clean_items(self.menu[dish_id]["recipe"])

    def _spoiled(self, it) -> bool:
        return it["units"] < self.spoil_units

    def _pick(self, dish_id):
        """Giữ chỗ theo id: mỗi loại lấy cá thể chưa ươn, chưa ai giữ, tươi nhất rồi id nhỏ.
        Trả mảng id (sắp theo id) hoặc None nếu không đủ."""
        held = {i for c in self.customers for i in (c["reserved"] or [])}
        taken = []
        for kind, n in self._recipe(dish_id).items():
            cands = sorted((it for it in self.items
                            if it["kind"] == kind and it["id"] not in held and not self._spoiled(it)),
                           key=lambda it: (-it["units"], id_key(it["id"])))
            if len(cands) < n:
                return None
            taken += [it["id"] for it in cands[:n]]
        return sorted(taken, key=id_key)

    def _check_fixture(self):
        """Mâu thuẫn giữa các thực thể -> BadInput (mã 2) trước khi ghi đầu ra."""
        by_id = {c["id"]: c for c in self.customers}
        holders = {}  # order_id -> nơi đang giữ món
        for s in self.stoves:
            if s["state"] == "idle":
                if s["dish"] is not None or s["cook_ticks_left"] or s["ready_ticks"]:
                    raise BadInput(f"bếp {s['id']} idle không được có món hay timer")
                continue
            if s["dish"] is None:
                raise BadInput(f"bếp {s['id']} {s['state']} phải có món")
            if s["state"] == "cooking":
                full = _ticks(self.menu[s["dish"]["dish_id"]]["cook_s"])
                if not (0 < s["cook_ticks_left"] <= full) or s["ready_ticks"]:
                    raise BadInput(f"bếp {s['id']} cooking cần cook_ticks_left trong [1, {full}] và ready_ticks 0")
            elif s["cook_ticks_left"]:
                raise BadInput(f"bếp {s['id']} ready không còn cook_ticks_left")
            holders.setdefault(s["dish"]["order_id"], []).append(s["dish"])
        if self.hand is not None:
            holders.setdefault(self.hand["order_id"], []).append(self.hand)
        for oid, dishes in holders.items():
            c = by_id.get(oid)
            if c is None:
                raise BadInput(f"món của đơn {oid} không có khách tương ứng")
            if len(dishes) > 1:
                raise BadInput(f"đơn {oid}: bếp và tay giữ cùng một đơn")
            dish = dishes[0]
            if c["order_status"] != "assigned" or dish["dish_id"] != c["dish_id"]:
                raise BadInput(f"đơn {oid}: món không khớp đơn")
            if c["base_price"] is None:
                c["base_price"] = dish["base_price"]
            elif c["base_price"] != dish["base_price"]:
                raise BadInput(f"đơn {oid}: base_price khác giá đã chốt trên món")
        missing = []
        by_item = {it["id"]: it for it in self.items}
        held = set()
        for c in sort_by_id(self.customers):
            if c["dish_id"] not in self.dish_pool:
                raise BadInput(f"khách {c['id']}: món {c['dish_id']} không thuộc kế hoạch Ngày")
            st, status = c["state"], c["order_status"]
            if (st == "eating") != (status == "served"):
                raise BadInput(f"khách {c['id']}: eating phải đi cùng order_status served")
            if st == "eating":
                if c["eat_ticks_left"] <= 0 or c["base_price"] is None or c["tip"] is None:
                    raise BadInput(f"khách {c['id']} eating cần eat_ticks_left > 0, base_price và tip")
            elif c["eat_ticks_left"]:
                raise BadInput(f"khách {c['id']} chưa ăn thì eat_ticks_left phải là 0")
            if status == "assigned" and c["id"] not in holders:
                raise BadInput(f"đơn assigned {c['id']} phải có đúng một món ở bếp hoặc tay")
            if status != "reserved":
                if c["reserved"]:
                    raise BadInput(f"đơn {c['id']} ({status}) không được giữ nguyên liệu")
                c["reserved"] = []
            elif c["reserved"] is None:
                missing.append(c)
            else:
                # v1.2: phần giữ trỏ tới cá thể chưa ươn trong kho, đủ công thức, không dùng chung với đơn khác
                kinds = {}
                for iid in c["reserved"]:
                    it = by_item.get(iid)
                    if it is None:
                        raise BadInput(f"đơn {c['id']}: phần giữ trỏ tới cá thể {iid} không có trong kho")
                    if self._spoiled(it):
                        raise BadInput(f"đơn {c['id']}: phần giữ trỏ tới cá thể đã ươn {iid}")
                    if iid in held:
                        raise BadInput(f"cá thể {iid} bị giữ hai lần")
                    held.add(iid)
                    kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
                if _clean_items(kinds) != self._recipe(c["dish_id"]):
                    raise BadInput(f"đơn {c['id']}: phần giữ khác công thức {c['dish_id']}")
                c["reserved"] = sorted(c["reserved"], key=id_key)
        # Đơn reserved bỏ `reserved`: cấp theo order_tick rồi id bàn, tươi nhất rồi id nhỏ.
        # Giả định (clarify Q1 Phase 1): không đủ hàng khả dụng thì đơn thành unfulfillable.
        for c in sorted(missing, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            picked = self._pick(c["dish_id"])
            if picked is None:
                c["reserved"] = []
                c["order_status"] = "unfulfillable"
            else:
                c["reserved"] = picked

    # --- giao diện cho runner -------------------------------------------------------
    def stock_items(self) -> list:
        """Kho cá thể v1.2 [{id, kind, fresh}] theo id, gồm hàng đang giữ và hàng ươn (Shop/day dùng)."""
        return [_item_out(it) for it in self.items]

    @property
    def stock(self) -> dict:
        """Đếm theo loại (kể cả hàng ươn). TẠM cho day -> Shop kiểu v1.1, tới khi lát D dùng stock_items()."""
        counts = {}
        for it in self.items:
            counts[it["kind"]] = counts.get(it["kind"], 0) + 1
        return {k: counts[k] for k in sorted(counts)}

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel)},
            "stock": self.stock_items(),
            "hand": _payload(self.hand),
            "stoves": [{k: (_payload(s[k]) if k == "dish" else s[k]) for k in STOVE_FIELDS} for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": list(tb["pos"]), "customer_id": occupied.get(tb["id"])}
                       for tb in self.tables],
            "customers": [dict(c, reserved=list(c["reserved"])) for c in sort_by_id(self.customers)],
        }

    # --- một bước -------------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và các timer
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            elif s["state"] == "ready":  # chỉ món đã ready từ đầu bước
                s["ready_ticks"] += 1
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # 1b. (v1.2) hao tươi kho thô, phát hết spoiled theo id, rồi mới xử lý giữ chỗ bị ươn
        just_spoiled = self._decay(events)
        if just_spoiled:
            self._rereserve(just_spoiled)
        # 2. bếp theo id: nấu xong -> ready
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", self._dish_data(s)))
        # 3. di chuyển rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 4. thanh toán / rời bàn theo id bàn; hết giờ thì dọn quán
        closing = self.time_left_ticks <= 0
        for tb in self.tables:
            c = self._customer_at(tb["id"])
            if c is None:
                continue
            if c["state"] == "eating":
                if c["eat_ticks_left"] == 0:
                    self._pay(c, "finished_eating", events)
                elif closing:
                    self._pay(c, "closing", events)
            elif closing:
                self._leave(c, "closing", events)
            elif c["patience_ticks_left"] == 0:
                self._leave(c, "patience", events)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. lượt khách mới
        if self.random_customers and self._customer_due():
            self._spawn_customer(events)
        return events

    # --- độ tươi (v1.2) ---------------------------------------------------------------
    def _decay(self, events) -> set:
        """Mọi cá thể trong kho (kể cả đang giữ) giảm decay_units, kẹp 0. Phát spoiled theo id đúng một lần
        khi đi từ ≥ ngưỡng xuống < ngưỡng. Trả tập id vừa ươn."""
        just = set()
        for it in self.items:  # self.items luôn sắp theo id
            before = it["units"]
            it["units"] = max(0, before - self.decay_units)
            if before >= self.spoil_units > it["units"]:
                just.add(it["id"])
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
        return just

    def _rereserve(self, just_spoiled):
        """Đơn có phần giữ vừa ươn: theo order_tick rồi id bàn, nhả toàn bộ phần giữ rồi thử giữ lại đúng một lần.
        Không đủ -> unfulfillable, khách vẫn chờ tới hết kiên nhẫn."""
        hit = [c for c in self.customers
               if c["order_status"] == "reserved" and any(i in just_spoiled for i in c["reserved"])]
        for c in sorted(hit, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            c["reserved"] = []
            picked = self._pick(c["dish_id"])
            if picked is None:
                c["order_status"] = "unfulfillable"
            else:
                c["reserved"] = picked

    # --- interact: bếp / bàn ---------------------------------------------------------
    def _interact(self, events):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append(((d, 0, id_key(s["id"])), s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append(((d, 1, id_key(tb["id"])), tb))
        if not cands:
            return
        (_, kind, _), target = min(cands, key=lambda x: x[0])
        if kind == 0:
            self._use_stove(target, events)
        else:
            self._use_table(target, events)

    def _use_stove(self, s, events):
        if s["state"] == "idle":
            orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
            if not orders:
                return  # không có đơn để nấu: bỏ lượt
            c = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
            dish = self.menu[c["dish_id"]]
            # v1.2: tiêu đúng các id đang giữ, chốt giá theo trung bình độ tươi (số nguyên, floor chính xác)
            use = set(c["reserved"])
            used = [it for it in self.items if it["id"] in use]
            self.items = [it for it in self.items if it["id"] not in use]
            price = dish["price"] * sum(it["units"] for it in used) // (len(used) * UNITS * 100)
            items = [_item_out(it) for it in sorted(used, key=lambda it: (it["kind"], id_key(it["id"])))]
            c["reserved"] = []
            c["order_status"] = "assigned"
            c["base_price"] = price
            s["state"] = "cooking"
            s["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": price}
            s["cook_ticks_left"] = _ticks(dish["cook_s"])
            s["ready_ticks"] = 0
            events.append(("cook_started", dict(self._dish_data(s), items=items, base_price=price)))
        elif s["state"] == "ready" and self.hand is None:  # carry_limit = 1
            data = self._dish_data(s)
            self.hand = s["dish"]
            self._clear_stove(s)
            events.append(("dish_picked", data))
        # bếp đang nấu, hoặc tay đã đầy: bỏ lượt

    def _use_table(self, tb, events):
        c = self._customer_at(tb["id"])
        if c is None or c["state"] != "waiting" or self.hand is None or self.hand["order_id"] != c["id"]:
            return  # bàn không nhận món này: bỏ lượt
        base = self.hand["base_price"]
        ratio = Fraction(c["patience_ticks_left"], self.patience_full)
        tip = math.floor(base * _exact(self.t["tip_rate"])) if ratio >= _exact(self.t["tip_min_patience_ratio"]) else 0
        c["state"] = "eating"
        c["eat_ticks_left"] = self.eat_full
        c["order_status"] = "served"
        c["base_price"] = base
        c["tip"] = tip
        self.hand = None
        events.append(("served", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": base, "tip": tip}))

    # --- khách: trả tiền, rời quán, đến quán -----------------------------------------
    def _pay(self, c, reason, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self._add_reputation(self.t["tip_reputation"])
        self.customers.remove(c)
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                                "tip": c["tip"], "amount": amount, "reason": reason}))

    def _leave(self, c, reason, events):
        if reason == "patience":
            self._add_reputation(self.t["left_reputation_delta"])
        # nhả phần giữ (đi cùng khách), bỏ món của đơn trên bếp hoặc trên tay; nguyên liệu đã dùng không hoàn
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                self._clear_stove(s)
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        self.customers.remove(c)
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))

    def _customer_due(self) -> bool:
        first = self.t["first_customer_tick"]
        return self.phase_tick >= first and (self.phase_tick - first) % self.interval_ticks == 0

    def _spawn_customer(self, events):
        free = [tb for tb in self.tables if self._customer_at(tb["id"]) is None]
        if not free:
            return  # không còn bàn: bỏ lượt
        table = free[0]  # self.tables đã sắp theo id
        # món đủ cá thể khả dụng (chưa ươn, chưa ai giữ); trong day đã lọc theo kế hoạch ở dish_pool
        cands = [d for d in self.dish_pool if self._pick(d) is not None]
        if not cands:
            events.append(("no_dish", {}))
            return
        dish_id = cands[self.rng.get("customers").randrange(len(cands))]
        reserved = self._pick(dish_id)
        cid = self.ids.new("C")
        self.customers.append({"id": cid, "table_id": table["id"], "dish_id": dish_id,
                               "order_tick": self.phase_tick, "state": "waiting",
                               "patience_ticks_left": self.patience_full, "eat_ticks_left": 0,
                               "order_status": "reserved", "reserved": reserved,
                               "base_price": None, "tip": None})
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    # --- tiện ích ---------------------------------------------------------------------
    def _customer_at(self, table_id):
        return next((c for c in self.customers if c["table_id"] == table_id), None)

    def _add_reputation(self, delta):
        r = min(max(self.reputation + delta, self.t["reputation_min"]), self.t["reputation_max"])
        self.reputation = round(r, 6)  # tránh 3.4000000000000004 làm lệch floor của điểm

    @staticmethod
    def _dish_data(s) -> dict:
        return {"stove_id": s["id"], "order_id": s["dish"]["order_id"], "dish_id": s["dish"]["dish_id"]}

    @staticmethod
    def _clear_stove(s):
        s["state"] = "idle"
        s["dish"] = None
        s["cook_ticks_left"] = 0
        s["ready_ticks"] = 0

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
