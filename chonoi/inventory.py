"""Kho Test Contract v1.2: kho CÁ THỂ có độ tươi.

File: {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}; kho rỗng {"items": []}.
Đọc: từ chối kho đếm v1.0/v1.1, sai schema, kind lạ, id trùng/rỗng, fresh không hữu hạn hoặc ngoài [0, 100]
(BadInput -> mã 2). Ghi: sắp theo id, qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định.

Trong sim, `fresh` là `fractions.Fraction` để so ngưỡng ươn và floor giá chính xác; ra file/snapshot dùng
`float` (repr đủ chữ số nên đọc lại giữ đúng nhánh ở ngưỡng 30). Cá thể nội bộ: {"id", "kind", "fresh"}.

`validate_items` (map loại -> số lượng) còn giữ cho fixture quán cũ tới khi lát Quán chuyển sang cá thể.
"""

import json
import math
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")  # v1.1: thêm ca_keo, keo_neo
KINDS = KINDS_P1  # tên dùng trong sim/quan, scenario, contract
ITEM_KEYS = {"id", "kind", "fresh"}


# --- độ tươi ---------------------------------------------------------------------------
def to_fresh(v) -> Fraction:
    """Số JSON -> Fraction chính xác theo biểu diễn thập phân (97.5 -> 195/2, 30 -> 30)."""
    return Fraction(repr(v)) if isinstance(v, float) else Fraction(v)


def decay_per_tick(tuning, where: str) -> Fraction:
    """Lượng tươi mất mỗi tick: `where` là 'gather' (giỏ) hoặc 'quan' (kho quán)."""
    f = tuning["freshness"]
    return to_fresh(f[f"{where}_decay_per_s"]) / int(tuning["tick_hz"])


def spoiled_below(tuning) -> Fraction:
    return to_fresh(tuning["freshness"]["spoiled_below"])


def decay(items, amount, threshold, location):
    """Giảm tươi mọi cá thể (kẹp đáy 0). Trả event `spoiled` theo id cho cá thể vừa đi từ ≥ ngưỡng xuống < ngưỡng."""
    events = []
    for it in sort_by_id(items):
        before = it["fresh"]
        it["fresh"] = max(Fraction(0), before - amount)
        if before >= threshold > it["fresh"]:
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": location}))
    return events


def is_spoiled(item, threshold) -> bool:
    return item["fresh"] < threshold


# --- cá thể <-> JSON ---------------------------------------------------------------------
def item_out(it) -> dict:
    return {"id": it["id"], "kind": it["kind"], "fresh": float(it["fresh"])}


def items_out(items, ordered=True) -> list:
    """Danh sách cá thể ra JSON; `ordered` sắp theo id (file, snapshot kho), False giữ thứ tự (giỏ, lost LIFO)."""
    return [item_out(it) for it in (sort_by_id(items) if ordered else items)]


def validate_individuals(items, kinds=KINDS, name="items") -> list:
    """Mảng cá thể JSON -> cá thể nội bộ (giữ thứ tự). Sai -> BadInput."""
    if not isinstance(items, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}} (contract v1.2; kho đếm không còn hợp lệ)")
    out, seen = [], set()
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != ITEM_KEYS:
            raise BadInput(f"{name}[{i}] phải có đúng các khóa {sorted(ITEM_KEYS)}")
        iid, kind, fresh = it["id"], it["kind"], it["fresh"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"{name}[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"{name}: id trùng {iid}")
        seen.add(iid)
        if kind not in kinds:
            raise BadInput(f"{name}[{i}]: nguyên liệu lạ {kind!r}")
        if (isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh)
                or not 0 <= fresh <= 100):
            raise BadInput(f"{name}[{i}].fresh phải là số hữu hạn trong [0, 100]")
        out.append({"id": iid, "kind": kind, "fresh": to_fresh(fresh)})
    return out


def counts(items, threshold=None) -> dict:
    """Cá thể -> map loại -> số lượng (bỏ hàng ươn nếu có `threshold`), sắp theo loại."""
    c = {}
    for it in items:
        if threshold is None or it["fresh"] >= threshold:
            c[it["kind"]] = c.get(it["kind"], 0) + 1
    return {k: c[k] for k in sorted(c)}


# --- kho đếm (fixture quán cũ) ---------------------------------------------------------------
def validate_items(items, kinds=KINDS):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


# --- file ---------------------------------------------------------------------------------
def read_inventory(path: str, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_individuals(data["items"], kinds, "file kho items")


def write_inventory(path: str, items: list):
    payload = {"items": items_out(items)}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
