"""Shop cuối Ngày (Test Contract v1.1, §2 và §4.5): mua nâng cấp bằng `money`, giữ `earned`/điểm.

Lát này chỉ chứa LUẬT (không đọc input/ghi file): bộ điều phối `day` gọi `step(buy, shop_done)` mỗi tick Shop
đang chạy (không gọi khi pause, nên timer 600 tick đứng yên). Số liệu đọc từ tuning['shop'].

Thứ tự mỗi bước: giảm giờ → xử lý tối đa MỘT lệnh `buy` → cạnh `shop_done` → hết giờ.
Bước cuối vừa có `buy` vừa có `shop_done`: buy được xử lý trước, rồi đóng bằng nút (`done`, thắng `time`).
Kho dư v1.2 giữ nguyên cá thể và độ tươi từ lúc quán đóng, bỏ khi sang Ngày.
"""

from copy import deepcopy

from ..ids import sort_by_id

UPGRADE_KINDS = ("oxygen", "hp")
LEVEL_VALUE = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


def active_stats(tuning, active_upgrades):
    """Oxy (giây) và Máu tối đa theo cấp ĐANG ÁP DỤNG; cấp 0 dùng số cơ sở của gather."""
    g, shop = tuning["gather"], tuning["shop"]["upgrades"]
    out = {"oxygen_max_s": g["oxygen_max_s"], "hp_max": g["hp_max"]}
    for kind, vk in LEVEL_VALUE.items():
        lv = active_upgrades.get(kind, 0)
        if lv > 0:
            out[vk] = shop[kind][lv - 1][vk]
    return out


class ShopSim:
    phase = "shop"

    def __init__(self, tuning, money, earned, upgrades, stock=None, day=1):
        self.t = tuning["shop"]
        self.day = day
        self.money = money
        self.earned = earned
        self.upgrades = dict(upgrades)  # cấp ĐÃ MUA (có hiệu lực từ Ngày kế)
        if stock is None:
            stock = [] if "freshness" in tuning else {}
        # Dùng snapshot quán, để Shop không cần biết biểu diễn fresh_units trong sim.
        self.stock = deepcopy(sort_by_id(stock)) if isinstance(stock, list) else dict(sorted(stock.items()))
        self.time_left_ticks = int(self.t["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {"money": self.money, "earned": self.earned, "upgrades": dict(self.upgrades),
                "stock": deepcopy(self.stock), "time_left_ticks": self.time_left_ticks}

    def step(self, buy=None, shop_done=False):
        """Một tick Shop. `buy`: chuỗi hoặc None/''; `shop_done`: cạnh lên của nút. Trả [(tên, dữ liệu)]."""
        events = []
        if self.done:
            return events
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if buy:
            events.append(self._buy(buy))
        if shop_done:
            self._end("done", events)
        elif self.time_left_ticks == 0:
            self._end("time", events)
        return events

    def _buy(self, action):
        levels = self.t["upgrades"].get(action) if action in UPGRADE_KINDS else None
        if levels is None:
            return ("buy_failed", {"action": action, "reason": "unknown"})
        owned = self.upgrades.get(action, 0)
        if owned >= len(levels):
            return ("buy_failed", {"action": action, "reason": "max_level"})
        nxt = levels[owned]
        if self.money < nxt["price"]:  # đủ đúng giá vẫn mua được
            return ("buy_failed", {"action": action, "reason": "funds"})
        self.money -= nxt["price"]
        self.upgrades[action] = nxt["level"]
        return ("bought", {"upgrade": action, "level": nxt["level"], "price": nxt["price"], "money": self.money})

    def _end(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))
