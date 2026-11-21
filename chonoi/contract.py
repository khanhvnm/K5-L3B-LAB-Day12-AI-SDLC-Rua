"""Đọc game.contract.json và kiểm dải hợp lệ của tuning P1 (PRD mục 13.2, Test Contract)."""

import json
import os

from .errors import BadInput
from .dayplan import plan_ingredients, validate_day_plan  # noqa: F401 (plan_ingredients giữ để tương thích import cũ)
from .inventory import KINDS

FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    validate_tuning(c.get("tuning"))
    return c


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if (not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos)):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_gather(g):
    """Dải hợp lệ P1 theo PRD mục 13.2."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or set(fy) != set(FISH_KINDS):
        raise BadInput(f"tuning.gather.fish_yield phải có đúng {list(FISH_KINDS)}")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {list(NODE_KINDS)}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != set(NODE_KINDS):
        raise BadInput(f"tuning.gather.nodes phải có ít nhất một nút mỗi loại {list(NODE_KINDS)}")
    _validate_fish(g, b, fy)
    _validate_monsters(g, b)


def _range_in(name, r, lo, hi):
    if not (isinstance(r, list) and len(r) == 2 and all(_num(c) for c in r) and lo <= r[0] <= r[1] <= hi):
        raise BadInput(f"tuning.{name} phải là [min, max] nằm trong [{lo}, {hi}]")


def _validate_fish(g, b, fy):
    """Cá bơi/sinh theo v1.1: số lượng đầu ca, tốc độ, miền bơi và điểm sinh theo loài."""
    _int_between("gather.fish_max", g.get("fish_max"), 1, 100)
    _int_between("gather.fish_initial", g.get("fish_initial"), 0, g["fish_max"])
    _between("gather.fish_speed", g.get("fish_speed"), 0, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    _range_in("gather.fish_x", g.get("fish_x"), *b["x"])
    xs = g.get("fish_spawn_x")
    if not (isinstance(xs, list) and xs and all(_num(x) and g["fish_x"][0] <= x <= g["fish_x"][1] for x in xs)):
        raise BadInput("tuning.gather.fish_spawn_x phải là mảng số nằm trong fish_x")
    for key in ("fish_depths", "fish_spawn_depths", "fish_weights"):
        if not isinstance(g.get(key), dict) or set(g[key]) != set(fy):
            raise BadInput(f"tuning.gather.{key} phải có đúng các loài {sorted(fy)}")
    for k in fy:
        _range_in(f"gather.fish_depths.{k}", g["fish_depths"][k], g["surface_depth"], b["d"][1])
        lo, hi = g["fish_depths"][k]
        ds = g["fish_spawn_depths"][k]
        if not (isinstance(ds, list) and ds and all(_num(d) and lo <= d <= hi for d in ds)):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là mảng độ sâu trong fish_depths.{k}")
        _between(f"gather.fish_weights.{k}", g["fish_weights"][k], 0.001, 1000)
    if g["fish_initial"] > len(xs) * sum(len(v) for v in g["fish_spawn_depths"].values()):
        raise BadInput("tuning.gather.fish_initial vượt số điểm sinh")


def _validate_monsters(g, b):
    m = g.get("monsters")
    if not isinstance(m, dict) or not isinstance(m.get("species"), dict) or not isinstance(m.get("spawns"), list):
        raise BadInput("tuning.gather.monsters phải có species và spawns")
    _int_between("gather.monsters.invuln_ticks", m.get("invuln_ticks"), 0, 10_000)
    _between("gather.monsters.loss_ratio", m.get("loss_ratio"), 0, 1)
    for sid, sp in m["species"].items():
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"gather.monsters.species.{sid}.{key}", sp.get(key), 0, 1000)
        _int_between(f"gather.monsters.species.{sid}.recoil_ticks", sp.get("recoil_ticks"), 1, 10_000)
        _range_in(f"gather.monsters.species.{sid}.depths", sp.get("depths"), *b["d"])
    seen = set()
    for s in m["spawns"]:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or s["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi quái cần id duy nhất")
        seen.add(s["id"])
        if s.get("kind") not in m["species"]:
            raise BadInput(f"tuning.gather.monsters.spawns.{s['id']}: kind phải thuộc species")
        _int_between(f"gather.monsters.spawns.{s['id']}.from_day", s.get("from_day"), 1, 99)
        wps = s.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"tuning.gather.monsters.spawns.{s['id']}.waypoints phải có đúng 2 điểm")
        for i, wp in enumerate(wps):
            _pos_in(f"gather.monsters.spawns.{s['id']}.waypoints[{i}]", wp, b, ("x", "d"))
        if s.get("pos") != wps[0]:
            raise BadInput(f"tuning.gather.monsters.spawns.{s['id']}.pos phải trùng waypoint đầu")


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ P1 (PRD mục 13.2)
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null ở Phase 1")
    # TODO(nhóm): bổ sung kiểm các khóa còn lại nếu muốn chặt hơn (bếp/bàn, uy tín, ...).
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        recipe = d.get("recipe")
        if not isinstance(recipe, dict) or not recipe:
            raise BadInput(f"menu.{dish_id}.recipe phải là map nguyên liệu -> số lượng")
        for kind, qty in recipe.items():
            if kind not in KINDS:
                raise BadInput(f"menu.{dish_id}.recipe: nguyên liệu lạ {kind!r}")
            _int_between(f"menu.{dish_id}.recipe.{kind}", qty, 1, 99)
    _validate_day(t, menu)
    _validate_freshness(t.get("freshness"))


def _validate_day(t, menu):
    """day_plan (5 ngày, kiểm ở chonoi/dayplan.py — một nguồn duy nhất) và shop (nâng cấp theo cấp) — có từ v1.1."""
    validate_day_plan(t.get("day_plan"), menu)
    shop = t.get("shop")
    if not isinstance(shop, dict):
        raise BadInput("thiếu tuning.shop")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 1_000_000)
    up = shop.get("upgrades")
    if not isinstance(up, dict) or not {"oxygen", "hp"} <= set(up):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    value_key = {"oxygen": "oxygen_max_s", "hp": "hp_max"}
    for kind, levels in up.items():
        vk = value_key.get(kind)
        if vk is None or not isinstance(levels, list) or not levels:
            raise BadInput(f"tuning.shop.upgrades.{kind} phải là mảng cấp không rỗng (kind hỗ trợ: oxygen, hp)")
        for i, lv in enumerate(levels, start=1):
            if lv.get("level") != i:
                raise BadInput(f"tuning.shop.upgrades.{kind}: cấp phải đánh số 1, 2, … theo thứ tự")
            _int_between(f"shop.upgrades.{kind}[{i}].price", lv.get("price"), 1, 10**9)
            _between(f"shop.upgrades.{kind}[{i}].{vk}", lv.get(vk), 1, 10_000)


def _validate_freshness(f):
    """Độ tươi v1.2: initial ∈ (0, 100], tốc độ hao ≥ 0, ngưỡng ươn ∈ [0, initial]."""
    if not isinstance(f, dict) or set(f) != {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"}:
        raise BadInput("tuning.freshness phải có đúng initial, gather_decay_per_s, quan_decay_per_s, spoiled_below")
    _between("freshness.initial", f["initial"], 0.001, 100)
    _between("freshness.gather_decay_per_s", f["gather_decay_per_s"], 0, 100)
    _between("freshness.quan_decay_per_s", f["quan_decay_per_s"], 0, 100)
    _between("freshness.spoiled_below", f["spoiled_below"], 0, f["initial"])
