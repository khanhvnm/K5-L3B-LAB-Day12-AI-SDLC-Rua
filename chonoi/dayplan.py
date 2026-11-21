"""Kế hoạch ngày D1–D5 (Ticket-02 mục 2; Test Contract v1.1 mục 4.1, 4.3, 4.4).

`tuning.day_plan` là mảng 5 object {day, dishes, ingredients}. `dishes` là map id món -> số suất,
`ingredients` = tổng công thức × số suất, theo thứ tự xuất hiện khi duyệt món (khớp ví dụ event
`day_plan` của ticket). `ingredients` là mục tiêu thu gom, không giới hạn số món khách được gọi.

Dùng trong chế độ day (lát D):
    plans = resolve_day_plan(tuning, scenario.get("day", {}).get("day_plan"))  # kiểm + tính lại
    plan = plan_for_day(plans, day)                    # đầu Ngày
    events.append(day_plan_event(plan))                # sau day_start: ("day_plan", {dishes, ingredients})
    QuanSim(..., plan_dishes=plan["dishes"])           # quán trong day chỉ bán món trong kế hoạch
Sai dữ liệu -> BadInput (mã 2).
"""

from .errors import BadInput

MAX_DAYS = 5
ENTRY_KEYS = {"day", "dishes", "ingredients"}


def plan_ingredients(dishes: dict, menu: dict) -> dict:
    """Tổng công thức × số suất; khóa theo thứ tự xuất hiện khi duyệt `dishes`."""
    out = {}
    for dish_id, servings in dishes.items():
        for kind, qty in menu[dish_id]["recipe"].items():
            out[kind] = out.get(kind, 0) + qty * servings
    return out


def _check_entry(where, entry, menu, require_ingredients):
    if not isinstance(entry, dict) or set(entry) - ENTRY_KEYS:
        raise BadInput(f"{where} chỉ có các khóa {sorted(ENTRY_KEYS)}")
    dishes = entry.get("dishes")
    if not isinstance(dishes, dict) or not dishes:
        raise BadInput(f"{where}.dishes phải là map món -> số suất, không rỗng")
    for dish_id, n in dishes.items():
        if dish_id not in menu:
            raise BadInput(f"{where}.dishes: món ngoài thực đơn {dish_id!r}")
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            raise BadInput(f"{where}.dishes.{dish_id} phải là số nguyên dương")
    want = plan_ingredients(dishes, menu)
    if "ingredients" in entry:
        if entry["ingredients"] != want:
            raise BadInput(f"{where}.ingredients phải bằng tổng công thức × suất: {want}")
    elif require_ingredients:
        raise BadInput(f"{where} thiếu ingredients")
    return {"day": entry["day"], "dishes": dict(dishes), "ingredients": want}


def validate_day_plan(day_plan, menu) -> list:
    """Kiểm `tuning.day_plan`: đúng 5 Ngày theo thứ tự 1..5, có ingredients khớp công thức."""
    if not isinstance(day_plan, list) or len(day_plan) != MAX_DAYS:
        raise BadInput(f"tuning.day_plan phải là mảng đúng {MAX_DAYS} Ngày")
    out = []
    for i, entry in enumerate(day_plan, start=1):
        if not isinstance(entry, dict) or entry.get("day") != i:
            raise BadInput(f"tuning.day_plan[{i - 1}].day phải là {i}")
        out.append(_check_entry(f"tuning.day_plan[{i - 1}]", entry, menu, require_ingredients=True))
    return out


def resolve_day_plan(tuning: dict, overrides=None) -> list:
    """Kế hoạch 5 Ngày từ tuning, ghi đè theo `scenario.day.day_plan` (mỗi mục cần day + dishes,
    ingredients tùy chọn nhưng nếu khai phải khớp công thức)."""
    plans = validate_day_plan(tuning["day_plan"], tuning["menu"])
    if overrides is None:
        return plans
    if not isinstance(overrides, list):
        raise BadInput("day.day_plan phải là mảng")
    seen = set()
    for i, entry in enumerate(overrides):
        day = entry.get("day") if isinstance(entry, dict) else None
        if isinstance(day, bool) or not isinstance(day, int) or not 1 <= day <= MAX_DAYS:
            raise BadInput(f"day.day_plan[{i}].day phải là số nguyên trong [1, {MAX_DAYS}]")
        if day in seen:
            raise BadInput(f"day.day_plan: Ngày {day} khai hai lần")
        seen.add(day)
        plans[day - 1] = _check_entry(f"day.day_plan[{i}]", entry, tuning["menu"], require_ingredients=False)
    return plans


def plan_for_day(plans: list, day: int) -> dict:
    return plans[day - 1]


def day_plan_event(plan: dict):
    """Event đầu Ngày, phát sau day_start: ("day_plan", {"dishes", "ingredients"})."""
    return ("day_plan", {"dishes": dict(plan["dishes"]), "ingredients": dict(plan["ingredients"])})
