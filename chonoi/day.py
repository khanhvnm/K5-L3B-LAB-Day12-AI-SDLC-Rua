"""Điều phối gather → quan → shop, chuyển trạng thái giữa các Ngày theo §4.5."""
import copy
import math

from .errors import BadInput
from .dayplan import MAX_DAYS, day_plan_event, plan_for_day, resolve_day_plan
from .ids import IdAllocator
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim
from .sim.shop import ShopSim, active_stats


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
    return resolve_day_plan(tuning, block.get("day_plan"))


def gather_tuning(tuning, upgrades):
    return dict(tuning, gather=dict(tuning["gather"], **active_stats(tuning, upgrades)))


class DaySession:
    def __init__(self, tuning, scenario, seed, days=1):
        if type(days) is not int or not 1 <= days <= MAX_DAYS:
            raise BadInput(f"--days phải trong [1,{MAX_DAYS}]")
        from .scenario import validate_day_scenario
        self.plans = validate_day_scenario(scenario, tuning)
        self.tuning, self.scenario = copy.deepcopy(tuning), copy.deepcopy(scenario)
        state = scenario.get("day", {})
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
        return [self._row("day_start", {}), self._row(*day_plan_event(self.plan)),
            self._row("phase_start", {})]

    def _new_day(self):
        self.active_upgrades = copy.deepcopy(self.upgrades)
        self.plan = plan_for_day(self.plans, self.day)
        self.phase, self.phase_tick = "gather", 0
        self.phase_tuning = gather_tuning(self.tuning, self.active_upgrades)
        self.day_start_earned = self.earned
        self.day_start_reputation = self.reputation
        self.statistics = {"served": 0, "left": 0, "tips": 0}
        self.delivered = [] if "freshness" in self.tuning else {}
        fixture = copy.deepcopy(self.scenario.get("gather", {}))
        if "freshness" in self.tuning:
            for item in fixture.get("hold", []):
                if self.day == 1:
                    self.ids.reserve(item["id"])
                else:
                    # Mỗi Ngày tạo cá thể mới, giữ độ tươi và thứ tự LIFO của mẫu.
                    item["id"] = self.ids.new("I")
        # Fixture vẫn được giữ; khi không khai oxy/Máu thì sim dùng mức đầy theo cấp.
        self.sim = GatherSim(self.phase_tuning, fixture, self.streams, self.ids, day=self.day)
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
        if old_phase == "shop":
            events = self.sim.step(buy=inp.buy, shop_done=inp.pressed("shop_done"))
            self.upgrades = self.sim.upgrades.copy()
        else:
            events = self.sim.step(inp)
            self.reputation = self.sim.reputation
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
        self.money, self.earned = self.sim.money, self.sim.earned
        if not self.sim.done:
            return rows
        if old_phase == "gather":
            # Cùng bàn giao kho đã chốt ở gather_end; không bước Quán trong tick này.
            inventory = self.sim.inventory_items()
            self.delivered = copy.deepcopy(inventory)
            planned = self.plan["dishes"]
            fixture_tuning = dict(self.tuning, menu={key: self.tuning["menu"][key] for key in planned})
            fixture = copy.deepcopy(self.scenario.get("quan", {}))
            fixture["reputation"] = self.reputation
            from .scenario import _validate_quan
            _validate_quan(fixture, fixture_tuning)
            self.sim = QuanSim(self.tuning, fixture, self.streams, self.ids, inventory=inventory, plan_dishes=planned)
            self._carry()
            self.phase = "quan"
        elif old_phase == "quan":
            stock = self.sim.snapshot()["stock"]
            self.sim = ShopSim(self.tuning, self.money, self.earned, self.upgrades, stock=stock, day=self.day)
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
