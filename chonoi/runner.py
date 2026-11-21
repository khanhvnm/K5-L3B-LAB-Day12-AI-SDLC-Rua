"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: sự kiện khởi đầu (day) -> snapshot tick 0 -> mỗi bước: sự kiện theo thứ tự,
rồi snapshot nếu tới lượt, đổi pha hoặc kết thúc -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math
import os
import tempfile

from .ids import IdAllocator
from .inputs import BUTTONS_V11, InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False
        self.initial_events = []

    @property
    def done(self) -> bool:
        return self.sim.done

    @property
    def reason(self):
        return self.sim.reason

    def snapshot(self) -> dict:
        s = _common(self.sim, self.tick, self.sim_tick, self.sim_tick, self.tuning,
                    "finished" if self.sim.done else "paused" if self.paused else "playing")
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        if self.done:
            return []
        self.tick += 1
        events = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            events.append(("paused" if self.paused else "resumed", {}))
        if not self.paused:
            events.extend(self.sim.step(inp))
            self.sim_tick += 1
        return [{"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}
                for name, data in events]

    def end_row(self) -> dict:
        sim = self.sim
        score = self.snapshot()["score"]
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
                "state": "finished" if sim.done else "paused" if self.paused else "playing",
                "reason": sim.reason if sim.done else "tick_limit",
                "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def create_session(mode, tuning, scenario, seed, inventory=None, days=1):
    if mode == "day":
        from .day import DaySession
        return DaySession(tuning, scenario, seed, days)
    return Session(mode, tuning, scenario, seed, inventory)


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None, days=1):
    sess = create_session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames, BUTTONS_V11)
    # Mâu thuẫn kho/đơn của day chỉ biết khi mở quán với kho thực. Chỉ công bố
    # JSONL sau khi toàn bộ lượt chạy hợp lệ; giữ nguyên file đích nếu fixture sai.
    tmp = None
    try:
        if mode == "day":
            fd, tmp = tempfile.mkstemp(prefix=".day-", suffix=".tmp", dir=os.path.dirname(os.path.abspath(out_path)))
            os.close(fd)
        _write_rows(sess, player, ticks, tmp or out_path, snapshot_every)
        if tmp is not None:
            os.replace(tmp, out_path)
            tmp = None
    finally:
        if tmp is not None:
            os.unlink(tmp)
    sess.write_inventory_if_done(inventory_out)
    return sess.sim


def _write_rows(sess, player, ticks, path, snapshot_every):
    w = JsonlWriter(path)
    try:
        for row in sess.initial_events:
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            rows = sess.step(inp)
            for row in rows:
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done or any(r["name"] == "phase_start" for r in rows):
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
