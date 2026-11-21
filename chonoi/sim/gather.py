"""Buổi sáng — Lặn & Hái (`gather`).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Một tick xử lý timer/nút mọc lại, di chuyển và oxy, quái, tương tác bến/hái, bắt cá, hết giờ; nếu còn giờ
thì cá bơi rồi sinh thêm theo lịch (v1.1, §4.5 của ticket).
Thời gian, số lượng và bán kính đều lấy từ tuning; runner sở hữu việc ghi file kho.
"""

import math

from ..ids import sort_by_id
from ..inventory import decay, decay_per_tick, items_out, spoiled_below, to_fresh, validate_individuals
from .monsters import build_monsters, find_hit, snapshot_monsters, start_recoil, update_monsters
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1):
        """`day`: Ngày hiện tại trong chế độ day (bố trí Cá Sấu theo from_day); gather độc lập dùng Ngày 1.
        Mẫu `gather.hold` của Ngày ≥ 2 được `day.py` cấp id mới trước khi dựng sim."""
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.phase_tick = 0
        # v1.2: giỏ là mảng cá thể {id, kind, fresh} theo thứ tự vào giỏ (cuối mảng là mới nhất, LIFO khi mất)
        self.fresh_initial = to_fresh(tuning["freshness"]["initial"])
        self.fresh_decay = decay_per_tick(tuning, "gather")
        self.spoiled_below = spoiled_below(tuning)
        self.hold = validate_individuals(scenario.get("hold", []), name="gather.hold")
        for it in self.hold:
            ids.reserve(it["id"])
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # random_fish=false: cá fixture đứng yên, không sinh thêm. Mặc định cá bơi và sinh theo lịch.
        self.fish_dynamic = scenario.get("random_fish", True)
        self._swim_rng = streams.get("fish_swim")
        self._spawn_rng = streams.get("fish_spawn")
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)}
                     for f in scenario.get("fish", [])]
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        if "fish" not in scenario and self.fish_dynamic:
            for _ in range(int(t["fish_initial"])):
                self._spawn_fish()
        # lát B (Cá Sấu): scenario.gather.monsters thay bố trí mặc định của Ngày
        self.monsters = build_monsters(t, scenario.get("monsters"), day)
        for m in self.monsters:
            ids.reserve(m["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> list:
        """Cá thể trong giỏ (bản sao, sắp theo id khi ghi file/bàn giao)."""
        return [dict(it) for it in self.hold]

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": items_out(self.hold, ordered=False), "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": snapshot_monsters(self.monsters),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. Đồng hồ và timer: nút vừa mọc lại được phép hái trong tick này.
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # Độ tươi hàng có sẵn ở đầu bước (hàng mới nhặt trong bước này chỉ hao từ bước sau).
        events.extend(decay(self.hold, self.fresh_decay, self.spoiled_below, "hold"))

        # 2. Di chuyển, phát sự kiện đổi phía mặt nước, rồi cập nhật oxy theo vị trí cuối tick.
        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if was_at_surface and not at_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_at_surface and at_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
        else:
            oxygen_before = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if oxygen_before > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        lost = items_out(reversed(self.hold), ordered=False)
                        self.hold.clear()
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # 2b. Quái (lát B) cập nhật theo id rồi xét tối đa một hit; Máu về 0 thì kết thúc ngay.
        if self._update_monsters(events):
            return events

        # 3. Interact: bến luôn được xét trước nút hái.
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if at_surface:
                self._gather_node(events)

        # 4. Bắt cá; nếu giỏ thiếu chỗ thì giữ nguyên đàn và không kích hoạt hồi chiêu.
        if inp.pressed("catch"):
            self._catch_fish(events)

        # 5. Hết giờ sau tương tác để hành động hợp lệ ở tick cuối vẫn được tính.
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 6. Còn giờ: cá bơi, rồi sinh thêm theo lịch (cá mới chỉ bơi từ bước sau).
        if self.fish_dynamic:
            self._swim_fish()
            if self.phase_tick % int(self.t["fish_spawn_ticks"]) == 0 and len(self.fish) < int(self.t["fish_max"]):
                fish = self._spawn_fish()
                if fish is not None:
                    events.append(("fish_spawned", {"id": fish["id"], "kind": fish["kind"], "pos": list(fish["pos"])}))
        return events

    # --- cá bơi và sinh ----------------------------------------------------------
    def _update_monsters(self, events) -> bool:
        """Cá Sấu (lát B): cập nhật quái theo id rồi xét tối đa một hit (chonoi/sim/monsters.py).
        Trả True nếu người chơi ngất vì quái (đã phát monster_hit, faint, gather_end)."""
        if not self.monsters:
            return False
        recovered = update_monsters(self.monsters, self.pos, self.t)
        m = find_hit(self.monsters, self.pos, self.invuln_ticks, self.t, recovered)
        if m is None:
            return False
        cfg = self.t["monsters"]
        lost = items_out([self.hold.pop() for _ in range(math.floor(len(self.hold) * cfg["loss_ratio"]))],
                         ordered=False)  # LIFO
        self.hp -= 1
        self.invuln_ticks = int(cfg["invuln_ticks"])
        start_recoil(m, self.pos, self.t)
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
        if self.hp <= 0:
            rest = items_out(reversed(self.hold), ordered=False)
            self.hold.clear()
            events.append(("faint", {"cause": "monster", "lost": rest, "hp": 0}))
            self._finish("fainted", events)
            return True
        return False

    def _swim_fish(self):
        """Mỗi đàn (theo id): tăng age; ở bước thứ k·fish_turn_ticks đổi hướng theo seed trước khi đi.
        Chạm mép thì phản xạ phần quãng đường còn lại và đảo thành phần vuông góc với mép (góc đảo cả hai)."""
        t = self.t
        step = float(t["fish_speed"]) / TICK
        lox, hix = t["fish_x"]
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % int(t["fish_turn_ticks"]) == 0:
                f["heading_deg"] = self._swim_rng.uniform(0.0, 360.0)
            lod, hid = t["fish_depths"][f["kind"]]
            h = math.radians(f["heading_deg"])
            x = f["pos"][0] + math.cos(h) * step
            d = f["pos"][1] + math.sin(h) * step
            heading = f["heading_deg"]
            if x < lox or x > hix:
                x = 2 * (lox if x < lox else hix) - x
                heading = 180.0 - heading
            if d < lod or d > hid:
                d = 2 * (lod if d < lod else hid) - d
                heading = -heading
            f["pos"] = [min(max(x, lox), hix), min(max(d, lod), hid)]
            f["heading_deg"] = heading % 360.0

    def _spawn_fish(self):
        """Sinh một đàn: loài theo trọng số (chuẩn hóa trên các loài còn điểm hợp lệ), điểm chọn đều, hướng theo seed.
        Điểm hợp lệ cách mọi đàn đang sống > fish_spawn_clearance. Hết điểm thì bỏ lượt (trả None)."""
        t = self.t
        clear = float(t["fish_spawn_clearance"])
        cand = {}
        for kind in sorted(t["fish_spawn_depths"]):
            pts = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]]
            ok = [pt for pt in pts if all(math.dist(pt, f["pos"]) > clear for f in self.fish)]
            if ok:
                cand[kind] = ok
        if not cand:
            return None
        kinds = sorted(cand)
        kind = self._spawn_rng.choices(kinds, weights=[t["fish_weights"][k] for k in kinds])[0]
        pos = self._spawn_rng.choice(cand[kind])
        fish = {"id": self.ids.new("F"), "kind": kind, "pos": pos,
                "heading_deg": self._spawn_rng.uniform(0.0, 360.0), "age_ticks": 0}
        self.fish.append(fish)
        return fish

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _gather_node(self, events):
        radius = float(self.t["interact_radius"])
        node = min(
            (n for n in sort_by_id(self.nodes)
             if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= radius),
            key=lambda n: math.dist(self.pos, n["pos"]),
            default=None,
        )
        if node is None:
            return

        amount = int(self.t["node_yield"])
        free = int(self.t["hold_capacity"]) - len(self.hold)
        if free < amount:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                          "required": amount, "free": free}))
            return

        self._pick(node["kind"], amount)
        node["regrow_ticks"] = int(round(float(self.t["regrow_s"]) * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))

    def _catch_fish(self, events):
        if self._at_surface() or self.catch_cd_ticks > 0:
            return

        radius = float(self.t["catch_radius"])
        fish = min(
            (f for f in sort_by_id(self.fish) if math.dist(self.pos, f["pos"]) <= radius),
            key=lambda f: math.dist(self.pos, f["pos"]),
            default=None,
        )
        if fish is None:
            return

        amount = int(self.t["fish_yield"][fish["kind"]])
        free = int(self.t["hold_capacity"]) - len(self.hold)
        if free < amount:
            events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                          "required": amount, "free": free}))
            return

        self._pick(fish["kind"], amount)
        self.fish.remove(fish)
        self.catch_cd_ticks = int(round(float(self.t["catch_cooldown_s"]) * TICK))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": amount}))

    def _pick(self, kind, amount):
        """Mỗi đơn vị là một cá thể mới: id I1, I2, … theo thứ tự vào giỏ (xuyên pha/Ngày), fresh = initial."""
        for _ in range(amount):
            self.hold.append({"id": self.ids.new("I"), "kind": kind, "fresh": self.fresh_initial})

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": items_out(self.hold)}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
