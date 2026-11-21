"""Thủy quái trong gather: Cá Sấu Năm Chèo (Ticket-02 §1.2; Test Contract v1.1 §4.3–§4.5). Lát B.

Số liệu đọc từ `tuning.gather.monsters` = {species: {kind: {...}}, spawns: [...], invuln_ticks, loss_ratio}.
Ngưỡng độ sâu của loài là `depths[0]` (Cá Sấu: d ≥ 10 mới bị phát hiện / bị chạm).

Mỗi bước, sau khi người chơi bơi, oxy và ngạt (gather.step gọi qua `_update_monsters`):
  1. Cập nhật từng quái theo id:
     - recoil: lùi recoil_dist / recoil_ticks mỗi bước theo `recoil_dir`, không phát hiện, không gây hit.
       Hết timer thì về patrol; con đó chỉ xét phát hiện / chạm từ bước kế.
     - patrol -> chase khi người chơi ở d ≥ ngưỡng và cách ≤ detect_radius.
       chase -> patrol khi cách > exit_radius hoặc người chơi lên d < ngưỡng.
     - patrol đi patrol_speed tới waypoint đích; tới nơi thì đổi đích cho bước sau.
       chase bơi về phía người chơi ở chase_speed.
     - Vị trí chặn theo biên map và dải độ sâu của loài.
  2. Xét tối đa MỘT hit: quái không recoil, cách ≤ hit_radius, người chơi ở d ≥ ngưỡng, hết bất tử.
     Chọn con gần nhất, hòa theo id. Người chơi -1 Máu, rơi floor(số đang mang × loss_ratio) theo LIFO,
     bất tử invuln_ticks. Con gây hit vào recoil recoil_ticks bước (tính từ bước sau), hướng xa người chơi
     chốt lúc chạm (trùng tâm dùng +x).
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id

TICK = 60.0
STATES = ("patrol", "chase", "recoil")
MONSTER_KEYS = ("id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir")


# --- dựng và kiểm fixture ------------------------------------------------------------
def spawns_for_day(cfg: dict, day: int) -> list:
    """Bố trí theo Ngày: M1 từ Ngày 1, M2 từ Ngày 3. Gather độc lập dùng Ngày 1."""
    return [s for s in cfg["spawns"] if s.get("from_day", 1) <= day]


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _in_band(name, pos, bounds, depths):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [x, d]")
    lo_x, hi_x = bounds["x"]
    lo_d, hi_d = max(bounds["d"][0], depths[0]), min(bounds["d"][1], depths[1])
    if not (lo_x <= pos[0] <= hi_x and lo_d <= pos[1] <= hi_d):
        raise BadInput(f"{name} nằm ngoài vùng của loài (x ∈ [{lo_x}, {hi_x}], d ∈ [{lo_d}, {hi_d}])")


def validate_monsters(fixture, gather_tuning):
    """Kiểm `scenario.gather.monsters[]` (id đã được kiểm trùng ở scenario). Sai -> BadInput (mã 2)."""
    cfg, bounds = gather_tuning["monsters"], gather_tuning["bounds"]
    spawns = {s["id"]: s for s in cfg["spawns"]}
    for m in fixture:
        mid = m["id"]
        extra = set(m) - set(MONSTER_KEYS)
        if extra:
            raise BadInput(f"monsters.{mid}: trường lạ/chưa hỗ trợ {sorted(extra)}")
        base = spawns.get(mid, {})
        kind = m.get("kind", base.get("kind"))
        if kind not in cfg["species"]:
            raise BadInput(f"monsters.{mid}.kind phải thuộc {sorted(cfg['species'])}")
        depths = cfg["species"][kind]["depths"]
        if "pos" not in m and not base:
            raise BadInput(f"monsters.{mid} thiếu pos")
        _in_band(f"monsters.{mid}.pos", m.get("pos", base.get("pos")), bounds, depths)
        wps = m.get("waypoints", base.get("waypoints"))
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"monsters.{mid}.waypoints phải có đúng 2 điểm")
        for i, wp in enumerate(wps):
            _in_band(f"monsters.{mid}.waypoints[{i}]", wp, bounds, depths)
        if m.get("target_idx", 1) not in (0, 1) or isinstance(m.get("target_idx"), bool):
            raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
        state = m.get("state", "patrol")
        if state not in STATES:
            raise BadInput(f"monsters.{mid}.state phải là một trong {STATES}")
        ticks = m.get("state_ticks_left", 0)
        if isinstance(ticks, bool) or not isinstance(ticks, int) or ticks < 0:
            raise BadInput(f"monsters.{mid}.state_ticks_left phải là số nguyên không âm")
        rd = m.get("recoil_dir")
        if state == "recoil":
            if ticks <= 0:
                raise BadInput(f"monsters.{mid}: recoil cần state_ticks_left > 0")
            if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)
                    and abs(math.hypot(*rd) - 1) <= 1e-6):
                raise BadInput(f"monsters.{mid}: recoil cần recoil_dir là vector đơn vị")
        elif ticks or rd is not None:
            raise BadInput(f"monsters.{mid}: {state} không có state_ticks_left / recoil_dir")


def build_monsters(gather_tuning: dict, fixture=None, day: int = 1) -> list:
    """Danh sách quái sắp theo id. `fixture` (scenario.gather.monsters) thay bố trí mặc định của Ngày;
    trường vắng lấy theo spawn cùng id trong tuning."""
    cfg = gather_tuning["monsters"]
    spawns = {s["id"]: s for s in cfg["spawns"]}
    src = fixture if fixture is not None else spawns_for_day(cfg, day)
    out = []
    for m in src:
        base = spawns.get(m["id"], {})
        rd = m.get("recoil_dir")
        out.append({"id": m["id"], "kind": m.get("kind", base.get("kind")),
                    "pos": [float(c) for c in m.get("pos", base.get("pos"))],
                    "waypoints": [[float(c) for c in wp] for wp in m.get("waypoints", base.get("waypoints"))],
                    "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                    "state_ticks_left": m.get("state_ticks_left", 0),
                    "recoil_dir": [float(c) for c in rd] if rd is not None else None})
    return sort_by_id(out)


def snapshot_monsters(monsters: list) -> list:
    return [{k: (list(m[k]) if k in ("pos", "recoil_dir") and m[k] is not None else
                 [list(wp) for wp in m[k]] if k == "waypoints" else m[k]) for k in MONSTER_KEYS}
            for m in monsters]


# --- một bước --------------------------------------------------------------------------
def _clamp(pos, bounds, depths):
    lo_d, hi_d = max(bounds["d"][0], depths[0]), min(bounds["d"][1], depths[1])
    return [min(max(pos[0], bounds["x"][0]), bounds["x"][1]), min(max(pos[1], lo_d), hi_d)]


def _toward(pos, target, step):
    """Đi `step` mét về phía `target`; tới nơi (còn ≤ step) thì đứng đúng tại đích. Trả (pos, đã_tới)."""
    dx, dd = target[0] - pos[0], target[1] - pos[1]
    dist = math.hypot(dx, dd)
    if dist <= step:
        return [float(target[0]), float(target[1])], True
    return [pos[0] + dx / dist * step, pos[1] + dd / dist * step], False


def update_monsters(monsters: list, player_pos, gather_tuning: dict) -> set:
    """Cập nhật mọi quái theo id. Trả tập id vừa hết recoil (chưa được xét chạm trong bước này)."""
    cfg, bounds = gather_tuning["monsters"], gather_tuning["bounds"]
    recovered = set()
    for m in monsters:
        sp = cfg["species"][m["kind"]]
        if m["state"] == "recoil":
            step = float(sp["recoil_dist"]) / int(sp["recoil_ticks"])
            m["pos"] = _clamp([m["pos"][0] + m["recoil_dir"][0] * step, m["pos"][1] + m["recoil_dir"][1] * step],
                              bounds, sp["depths"])
            m["state_ticks_left"] -= 1
            if m["state_ticks_left"] <= 0:
                m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                recovered.add(m["id"])
            continue
        deep = player_pos[1] >= sp["depths"][0]
        dist = math.dist(m["pos"], player_pos)
        if m["state"] == "patrol" and deep and dist <= sp["detect_radius"]:
            m["state"] = "chase"
        elif m["state"] == "chase" and (not deep or dist > sp["exit_radius"]):
            m["state"] = "patrol"
        if m["state"] == "chase":
            m["pos"], _ = _toward(m["pos"], player_pos, float(sp["chase_speed"]) / TICK)
        else:
            m["pos"], arrived = _toward(m["pos"], m["waypoints"][m["target_idx"]], float(sp["patrol_speed"]) / TICK)
            if arrived:
                m["target_idx"] = 1 - m["target_idx"]  # đích mới áp dụng từ bước sau
        m["pos"] = _clamp(m["pos"], bounds, sp["depths"])
    return recovered


def find_hit(monsters: list, player_pos, invuln_ticks: int, gather_tuning: dict, skip_ids=()):
    """Con gây hit trong bước này (gần nhất, hòa theo id) hoặc None."""
    if invuln_ticks > 0:
        return None
    species = gather_tuning["monsters"]["species"]
    best = None
    for m in monsters:
        sp = species[m["kind"]]
        if m["state"] == "recoil" or m["id"] in skip_ids or player_pos[1] < sp["depths"][0]:
            continue
        d = math.dist(m["pos"], player_pos)
        if d <= sp["hit_radius"] and (best is None or (d, id_key(m["id"])) < best[0]):
            best = ((d, id_key(m["id"])), m)
    return best[1] if best else None


def start_recoil(m: dict, player_pos, gather_tuning: dict):
    """Chốt hướng lùi xa người chơi lúc chạm (trùng tâm dùng +x); recoil chạy từ bước sau."""
    sp = gather_tuning["monsters"]["species"][m["kind"]]
    dx, dd = m["pos"][0] - player_pos[0], m["pos"][1] - player_pos[1]
    n = math.hypot(dx, dd)
    m["recoil_dir"] = [dx / n, dd / n] if n > 0 else [1.0, 0.0]
    m["state"] = "recoil"
    m["state_ticks_left"] = int(sp["recoil_ticks"])
