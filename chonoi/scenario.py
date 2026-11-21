"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
QUAN_STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
QUAN_TABLE_KEYS = {"id", "pos"}
QUAN_CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                      "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}
STOVE_STATES = ("idle", "cooking", "ready")
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])


def _pos_int(v):
    return not isinstance(v, bool) and isinstance(v, int) and v > 0


def _payload(name, p, menu):
    """Payload món {order_id, dish_id, base_price} hoặc null (PRD-0 mục D)."""
    if p is None:
        return
    if not isinstance(p, dict) or set(p) != PAYLOAD_KEYS:
        raise BadInput(f"{name} phải là {{order_id, dish_id, base_price}} hoặc null")
    if not isinstance(p["order_id"], str) or not p["order_id"]:
        raise BadInput(f"{name}.order_id phải là id khách")
    if p["dish_id"] not in menu:
        raise BadInput(f"{name}.dish_id ngoài thực đơn: {p['dish_id']!r}")
    if not _pos_int(p["base_price"]):
        raise BadInput(f"{name}.base_price phải là số nguyên dương")


def _validate_quan(b, tuning):
    """Kiểm từng trường của khối quan. Mâu thuẫn giữa các thực thể kiểm tiếp trong QuanSim._check_fixture."""
    q, menu = tuning["quan"], tuning["menu"]
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = q["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    if "hand" in b:
        _payload("hand", b["hand"], menu)
    stove_ids = {s["id"] for s in q["stoves"]}
    for s in b.get("stoves", []):
        if set(s) - QUAN_STOVE_KEYS:
            raise BadInput(f"stoves.{s['id']}: trường lạ {sorted(set(s) - QUAN_STOVE_KEYS)}")
        if s["id"] not in stove_ids:
            raise BadInput(f"id bếp không tồn tại: {s['id']}")
        if "pos" in s:
            _pos(f"stoves.{s['id']}.pos", s["pos"], qb, axes=("x", "z"))
        if "state" in s and s["state"] not in STOVE_STATES:
            raise BadInput(f"stoves.{s['id']}.state phải là một trong {STOVE_STATES}")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"stoves.{s['id']}.{key}", s[key])
        if "dish" in s:
            _payload(f"stoves.{s['id']}.dish", s["dish"], menu)
    table_known = {t["id"] for t in q["tables"]}
    for tb in b.get("tables", []):
        if set(tb) - QUAN_TABLE_KEYS:
            raise BadInput(f"tables.{tb['id']}: trường lạ {sorted(set(tb) - QUAN_TABLE_KEYS)}")
        if tb["id"] not in table_known:
            raise BadInput(f"id bàn không tồn tại: {tb['id']}")
        if "pos" in tb:
            _pos(f"tables.{tb['id']}.pos", tb["pos"], qb, axes=("x", "z"))
    patience_full = int(round(q["patience_s"] * 60))
    eat_full = int(round(q["eat_s"] * 60))
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    for c in b.get("customers", []):
        cid = c["id"]
        if set(c) - QUAN_CUSTOMER_KEYS:
            raise BadInput(f"customers.{cid}: trường lạ {sorted(set(c) - QUAN_CUSTOMER_KEYS)}")
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in table_known:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        if c.get("dish_id") not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải là món trong thực đơn")
        if "state" in c and c["state"] not in CUSTOMER_STATES:
            raise BadInput(f"customers.{cid}.state phải là một trong {CUSTOMER_STATES}")
        if "order_status" in c and c["order_status"] not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}.order_status phải là một trong {ORDER_STATUSES}")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if key in c:
                _nonneg_int(f"customers.{cid}.{key}", c[key])
        if c.get("patience_ticks_left", 0) > patience_full:
            raise BadInput(f"customers.{cid}.patience_ticks_left vượt kiên nhẫn tối đa {patience_full}")
        if c.get("eat_ticks_left", 0) > eat_full:
            raise BadInput(f"customers.{cid}.eat_ticks_left vượt thời gian ăn {eat_full}")
        if "reserved" in c:
            validate_items(c["reserved"])
        if c.get("base_price") is not None and not _pos_int(c["base_price"]):
            raise BadInput(f"customers.{cid}.base_price phải là số nguyên dương hoặc null")
        if c.get("tip") is not None:
            _nonneg_int(f"customers.{cid}.tip", c["tip"])
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
