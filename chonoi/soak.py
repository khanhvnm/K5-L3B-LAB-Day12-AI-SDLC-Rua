"""Soak headless (Ticket-04 mục 2): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày trong MỘT tiến trình bằng bot tất định (chỉ đọc snapshot của sim, không dùng đồng hồ hay RNG riêng).
Mỗi Ngày đi qua gather -> quan -> shop; kế hoạch D1–D5 lặp ở Ngày 6–10 (dayplan.plan_for_day); tiền, tổng thu,
uy tín, cấp nâng cấp, số Ngày và id cá thể đi tiếp xuyên suốt (DaySession).

soak.json: {days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s}
  - results ghi tại lúc Shop đóng mỗi Ngày.
  - Cùng seed và số Ngày -> các trường gameplay giống hệt; chỉ duration_s (giây thực) thay đổi.
Mã thoát: 0 đủ Ngày, không lỗi; 1 có lỗi chạy hoặc chưa đủ Ngày (soak.json vẫn được ghi); 2 tham số sai.
"""

import argparse
import json
import math
import os
import sys
import time
import traceback

from .contract import load_contract
from .day import DaySession
from .errors import BadInput
from .inputs import InputState

DAY_MAX_TICKS = 22_200   # một Ngày không pause dài tối đa 22.200 tick (Ticket-02)
TICK = 60.0
SAFE_DEPTH = 9.0         # bot chỉ lặn ở d < 10: Cá Sấu không phát hiện / không chạm được


def _toward(pos, target, slow=0.5):
    """Vector move hướng tới target, chậm dần trong `slow` mét cuối để dừng đúng chỗ."""
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    dist = math.hypot(dx, dy)
    if dist < 1e-9:
        return (0.0, 0.0)
    k = min(1.0, dist / slow) / dist
    return (dx * k, dy * k)


class Bot:
    """Bot tất định cho chế độ day. act(session) -> InputState của bước kế tiếp."""

    def __init__(self, tuning):
        self.t = tuning
        self._last = set()   # nút đã bấm ở bước trước: nhả một bước để tạo cạnh lên mới

    def act(self, sess) -> InputState:
        phase = sess.phase
        if phase == "gather":
            move, want, buy = self._gather(sess)
        elif phase == "quan":
            move, want, buy = self._quan(sess)
        else:
            move, want, buy = self._shop(sess)
        edges = {b for b in want if b not in self._last}
        self._last = edges
        return InputState(move, {b: b in edges for b in ("interact", "catch", "pause", "shop_done")}, edges, buy)

    # --- buổi sáng --------------------------------------------------------------------
    def _gather(self, sess):
        g = sess.sim.t
        s = sess.sim.snapshot()
        p = s["player"]
        pos = p["pos"]
        speed_tps = g["swim_speed"] / TICK
        dock = g["dock_pos"]
        # về bến: hết giờ (còn đủ thời gian bơi về + đệm), giỏ đầy, hoặc không còn gì cần lấy
        back_ticks = math.dist(pos, dock) / speed_tps + 120
        need = dict(sess.plan["ingredients"])
        for it in s["hold"]:
            if need.get(it["kind"], 0) > 0:
                need[it["kind"]] -= 1
        free = s["hold_capacity"] - s["hold_count"]
        target, action = None, None
        if sess.sim.time_left_ticks > back_ticks and free > 0:
            target, action = self._gather_target(s, g, need, free)
        if target is None:
            if math.dist(pos, dock) <= g["dock_radius"] * 0.8:
                return (0.0, 0.0), {"interact"}, None
            return _toward(pos, dock), set(), None
        # oxy: dưới nước mà không đủ để nổi lên an toàn thì nổi lên trước
        if not p["at_surface"] and p["oxygen_ticks"] < pos[1] / speed_tps + 120:
            return (0.0, -1.0), set(), None
        if action == "interact":
            radius = g["interact_radius"]
        else:
            radius = g["catch_radius"]
        if math.dist(pos, target) <= radius * 0.6:
            ready = action == "interact" or p["catch_cd_ticks"] == 0
            return _toward(pos, target), ({action} if ready else set()), None
        return _toward(pos, target), set(), None

    @staticmethod
    def _gather_target(s, g, need, free):
        """Mục tiêu gần nhất (hòa theo id): nút cần và đã mọc ở mặt nước, hoặc đàn cá cần ở vùng nông an toàn."""
        pos = s["player"]["pos"]
        cands = []
        for n in s["nodes"]:
            if n["ready"] and need.get(n["kind"], 0) > 0:
                cands.append((math.dist(pos, n["pos"]), n["id"], [n["pos"][0], 0.0], "interact"))
        for f in s["fish"]:
            if need.get(f["kind"], 0) > 0 and f["pos"][1] < SAFE_DEPTH and g["fish_yield"][f["kind"]] <= free:
                cands.append((math.dist(pos, f["pos"]), f["id"], list(f["pos"]), "catch"))
        if not cands:
            return None, None
        _, _, target, action = min(cands, key=lambda c: (c[0], c[1]))
        return target, action

    # --- buổi tối ---------------------------------------------------------------------
    def _quan(self, sess):
        s = sess.sim.snapshot()
        pos = s["player"]["pos"]
        radius = sess.sim.t["interact_radius"]
        target = None
        if s["hand"] is not None:
            c = next((c for c in s["customers"] if c["id"] == s["hand"]["order_id"]), None)
            if c is not None:
                target = next(tb["pos"] for tb in s["tables"] if tb["id"] == c["table_id"])
        if target is None:
            ready = [st for st in s["stoves"] if st["state"] == "ready"]
            if ready and s["hand"] is None:
                target = min(ready, key=lambda st: (math.dist(pos, st["pos"]), st["id"]))["pos"]
        if target is None and any(c["state"] == "waiting" and c["order_status"] == "reserved" for c in s["customers"]):
            idle = [st for st in s["stoves"] if st["state"] == "idle"]
            if idle:
                target = min(idle, key=lambda st: (math.dist(pos, st["pos"]), st["id"]))["pos"]
        if target is None:
            return (0.0, 0.0), set(), None
        # đứng sát mục tiêu (< 0.3 m) để nó chắc chắn là đối tượng gần nhất khi tương tác
        want = {"interact"} if math.dist(pos, target) <= min(0.3, radius) else set()
        return _toward(pos, target), want, None

    # --- Shop -------------------------------------------------------------------------
    @staticmethod
    def _shop(sess):
        """Bước 1 thử mua oxy, bước 2 thử mua áo phao (thiếu tiền -> buy_failed, vô hại), bước 3 đóng Shop."""
        k = sess.phase_tick
        if k == 0:
            return (0.0, 0.0), set(), "oxygen"
        if k == 1:
            return (0.0, 0.0), set(), "hp"
        return (0.0, 0.0), {"shop_done"}, None


def run_soak(tuning, seed: int, days: int) -> dict:
    t0 = time.perf_counter()
    results, crashes, sess = [], 0, None
    try:
        sess = DaySession(tuning, {}, seed, days, max_days=days)
        bot = Bot(tuning)
        mult = tuning["score"]["reputation_multiplier"]
        limit = days * (DAY_MAX_TICKS + 60)  # chặn vòng lặp nếu bot kẹt; không pause nên không vượt
        while not sess.done and sess.tick < limit:
            before = sess.days_completed
            sess.step(bot.act(sess))
            if sess.days_completed > before:  # Shop vừa đóng
                results.append({"day": sess.days_completed, "earned": sess.earned, "reputation": sess.reputation,
                                "score": sess.earned + mult * math.floor(sess.reputation)})
    except Exception:  # soak đếm lỗi chạy thay vì dừng im lặng
        crashes += 1
        traceback.print_exc(file=sys.stderr)
    return {"days": days, "days_completed": sess.days_completed if sess else 0, "crashes": crashes,
            "results": results, "duration_s": round(time.perf_counter() - t0, 3)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if a.days < 1:
        sys.stderr.write("đầu vào sai: --days phải >= 1\n")
        return 2
    try:
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    report = run_soak(tuning, a.seed, a.days)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    os.replace(tmp, a.out)
    ok = report["crashes"] == 0 and report["days_completed"] == report["days"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
