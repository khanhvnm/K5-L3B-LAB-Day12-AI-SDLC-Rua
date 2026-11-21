"""Điều phối day v1.1; không sở hữu luật cá/quái/quán hoặc mua hàng.

Shop factory: ShopSim(tuning, scenario, streams, ids). scenario có stock,
money, earned, reputation, upgrades. Shop cung cấp snapshot(), step(InputState)
trả (name, data) theo §4.5, done, time_left_ticks, money, earned, reputation,
upgrades. Điều phối chỉ gọi step khi không pause. Tests có thể truyền factory riêng.
"""
import copy
import math

from .errors import BadInput
from .ids import IdAllocator
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def plans_for_days(tuning, overrides=None):
    plans = tuning.get("day_plan")
    if not isinstance(plans, list) or len(plans) != 5:
        raise BadInput("day cần preset day_plan 5 Ngày do chủ contract v1.1 cung cấp")
    by_day = {}
    if overrides is not None and not isinstance(overrides, list):
        raise BadInput("day.day_plan phải là mảng theo Ngày")
    for entries in (plans, overrides or []):
        seen = set()
        for p in entries:
            if (not isinstance(p, dict) or set(p) - {"day", "dishes", "ingredients"}
                    or type(p.get("day")) is not int or not 1 <= p["day"] <= 5 or p["day"] in seen):
                raise BadInput("day_plan ghi đè sai/trùng Ngày")
            seen.add(p["day"])
            by_day[p["day"]] = copy.deepcopy(p)
    for plan in by_day.values():
        dishes = plan.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput("day_plan.dishes phải là map khác rỗng")
        items = {}
        for dish, count in dishes.items():
            if dish not in tuning["menu"] or isinstance(count, bool) or not isinstance(count, int) or count <= 0:
                raise BadInput("món/số suất trong day_plan không hợp lệ")
            for kind, amount in tuning["menu"][dish]["recipe"].items():
                items[kind] = items.get(kind, 0) + amount * count
        if "ingredients" in plan:
            declared = plan["ingredients"]
            if not isinstance(declared, dict) or any(type(v) is not int for v in declared.values()) or declared != items:
                raise BadInput("day_plan.ingredients không khớp công thức × số suất")
        plan["dishes"] = dict(sorted(dishes.items()))
        plan["ingredients"] = dict(sorted(items.items()))
    return by_day


def validate_day(block, tuning):
    if not isinstance(block, dict) or set(block) - {"money", "earned", "reputation", "upgrades", "day_plan"}:
        raise BadInput("khối day có trường lạ hoặc không phải object")
    money, earned = block.get("money", 0), block.get("earned", 0)
    for value in (money, earned):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise BadInput("money/earned phải là số nguyên không âm")
    if money > earned or (("money" in block) != ("earned" in block)):
        raise BadInput("khai cả money và earned, cần 0 ≤ money ≤ earned")
    rep = block.get("reputation", tuning["quan"]["reputation_initial"])
    if (isinstance(rep, bool) or not isinstance(rep, (int, float))
            or not tuning["quan"]["reputation_min"] <= rep <= tuning["quan"]["reputation_max"]):
        raise BadInput("day.reputation ngoài khoảng hợp lệ")
    upgrades = block.get("upgrades", {})
    catalog = tuning.get("shop", {}).get("upgrades", {})
    if not isinstance(upgrades, dict):
        raise BadInput("day.upgrades phải là object")
    for kind, level in upgrades.items():
        if (kind not in catalog or isinstance(level, bool) or not isinstance(level, int)
                or level < 0 or level > max((r["level"] for r in catalog[kind]), default=0)):
            raise BadInput("cấp nâng cấp không hợp lệ")
    if "day_plan" in block and not isinstance(block["day_plan"], list):
        raise BadInput("day.day_plan phải là mảng theo Ngày")
    return plans_for_days(tuning, block.get("day_plan"))


def gather_tuning(tuning, upgrades, day):
    cfg = copy.deepcopy(tuning)
    for kind, level in upgrades.items():
        row = next((r for r in tuning["shop"]["upgrades"][kind] if r["level"] == level), {})
        for key in ("oxygen_max_s", "hp_max"):
            if key in row:
                cfg["gather"][key] = row[key]
    monsters = cfg["gather"].get("monsters", {})
    if "spawns" in monsters:
        monsters["spawns"] = [m for m in monsters["spawns"] if m["from_day"] <= day]
    return cfg


class DaySession:
    def __init__(self, tuning, scenario, seed, days=1, shop_factory=None):
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 5:
            raise BadInput("--days phải trong [1,5]")
        from .scenario import validate_day_scenario
        self.plans = validate_day_scenario(scenario, tuning)
        self.tuning, self.scenario = copy.deepcopy(tuning), copy.deepcopy(scenario)
        state = scenario.get("day", {})
        if "shop" not in tuning:
            raise BadInput("day cần preset shop của contract v1.1")
        if shop_factory is None:
            try:
                from .sim.shop import ShopSim
                shop_factory = ShopSim
            except ModuleNotFoundError as error:
                if error.name != f"{__package__}.sim.shop":
                    raise
                raise BadInput("Chưa tích hợp sim/shop.py của Khánh; xem giao diện trong chonoi/day.py") from error
        self.shop_factory = shop_factory
        self.mode, self.day, self.days, self.days_completed = "day", 1, days, 0
        self.tick = self.sim_tick = self.phase_tick = 0
        self.paused = self.done = False
        self.reason = None
        self.money, self.earned = state.get("money", 0), state.get("earned", 0)
        self.reputation = state.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = copy.deepcopy(state.get("upgrades", {}))
        self.streams, self.ids = Streams(seed), IdAllocator()
        self.dishes_sold = {}
        self._new_day()
        self.initial_events = self._start_events()

    def _row(self, name, data, phase=None):
        return {"type": "event", "tick": self.tick, "phase": phase or self.phase,
                "day": self.day, "name": name, "data": copy.deepcopy(data)}

    def _start_events(self):
        return [self._row("day_start", {}), self._row("day_plan", {
            "dishes": self.plan["dishes"], "ingredients": self.plan["ingredients"]}),
            self._row("phase_start", {})]

    def _new_day(self):
        self.active_upgrades = copy.deepcopy(self.upgrades)
        self.plan = self.plans[self.day]
        self.phase, self.phase_tick = "gather", 0
        self.phase_tuning = gather_tuning(self.tuning, self.active_upgrades, self.day)
        self.day_start_earned = self.earned
        self.day_start_reputation = self.reputation
        self.statistics = {"served": 0, "left": 0, "tips": 0}
        self.delivered = {}
        fixture = copy.deepcopy(self.scenario.get("gather", {}))
        # Fixture vẫn được giữ; khi không khai oxy/Máu thì sim dùng mức đầy theo cấp.
        self.sim = GatherSim(self.phase_tuning, fixture, self.streams, self.ids)
        self._carry()

    def _carry(self):
        self.sim.money, self.sim.earned, self.sim.reputation = self.money, self.earned, self.reputation

    def step(self, inp):
        if self.done:
            return []
        self.tick += 1
        rows = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            rows.append(self._row("paused" if self.paused else "resumed", {}))
        if self.paused:
            return rows
        self.sim_tick += 1
        self.phase_tick += 1
        old_phase = self.phase
        events = self.sim.step(inp)
        rows.extend(self._row(name, data, old_phase) for name, data in events)
        for name, data in events:
            if name == "served":
                self.statistics["served"] += 1
                counts = self.dishes_sold
                counts[data["dish_id"]] = counts.get(data["dish_id"], 0) + 1
            elif name == "paid":
                self.statistics["tips"] += data["tip"]
            elif name == "customer_left":
                self.statistics["left"] += 1
        self.money, self.earned, self.reputation = self.sim.money, self.sim.earned, self.sim.reputation
        if old_phase == "shop":
            self.upgrades = copy.deepcopy(self.sim.upgrades)
        if not self.sim.done:
            return rows
        if old_phase == "gather":
            inventory = self.sim.inventory_items()
            self.delivered = copy.deepcopy(inventory)
            cfg = copy.deepcopy(self.tuning)
            cfg["menu"] = {k: v for k, v in cfg["menu"].items() if k in self.plan["dishes"]}
            fixture = copy.deepcopy(self.scenario.get("quan", {}))
            fixture["reputation"] = self.reputation
            from .scenario import _validate_quan
            _validate_quan(fixture, cfg)
            self.sim = QuanSim(cfg, fixture, self.streams, self.ids, inventory=inventory)
            self._carry()
            self.phase = "quan"
        elif old_phase == "quan":
            self.sim = self.shop_factory(self.tuning, {"stock": copy.deepcopy(self.sim.stock),
                "money": self.money, "earned": self.earned, "reputation": self.reputation,
                "upgrades": copy.deepcopy(self.upgrades)}, self.streams, self.ids)
            self.phase = "shop"
        else:
            self.days_completed += 1
            if self.days_completed == self.days:
                self.done, self.reason = True, "days_complete"
                return rows
            self.day += 1
            self._new_day()
            rows.extend(self._start_events())
            return rows
        self.phase_tick = 0
        rows.append(self._row("phase_start", {}))
        return rows

    def snapshot(self):
        result = copy.deepcopy(self.sim.snapshot())
        result.update(type="snapshot", tick=self.tick, sim_tick=self.sim_tick, mode="day", phase=self.phase,
            phase_tick=self.phase_tick, day=self.day, day_plan=copy.deepcopy(self.plan),
            upgrades=copy.deepcopy(self.upgrades), active_upgrades=copy.deepcopy(self.active_upgrades),
            state="finished" if self.done else "paused" if self.paused else "playing",
            time_left_ticks=self.sim.time_left_ticks, money=self.money, earned=self.earned,
            reputation=self.reputation, score=self.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.reputation))
        return result

    def browser_details(self):
        """Dữ liệu cho màn giới thiệu/kết quả; không thay định dạng headless."""
        return {
            "delivered": self.delivered,
            "day_result": dict(self.statistics, earned=self.earned - self.day_start_earned,
                               reputation_delta=round(self.reputation - self.day_start_reputation, 6)),
            "dishes_sold": self.dishes_sold,
        }

    def end_row(self):
        snap = self.snapshot()
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": "day",
            "state": snap["state"], "reason": self.reason or "tick_limit", "days_completed": self.days_completed,
            **{k: snap[k] for k in ("money", "earned", "reputation", "score")}}

    def write_inventory_if_done(self, inventory_out):
        pass  # day bàn giao trong bộ nhớ; CLI cấm hai cờ file kho.
