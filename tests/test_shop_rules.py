"""Luật Shop v1.1: mua nâng cấp, buy_failed, thứ tự buy → shop_done → hết giờ."""

import unittest

from chonoi.contract import load_contract
from chonoi.sim.shop import ShopSim, active_stats

T = load_contract()["tuning"]


def shop(money=1000, earned=1000, upgrades=None):
    return ShopSim(T, money, earned, upgrades or {})


class ShopRules(unittest.TestCase):
    def test_buy_levels_in_order_and_keep_earned(self):
        s = shop(money=700, earned=900)
        self.assertEqual(s.step("oxygen"), [("bought", {"upgrade": "oxygen", "level": 1, "price": 200, "money": 500})])
        self.assertEqual(s.step("oxygen"), [("bought", {"upgrade": "oxygen", "level": 2, "price": 400, "money": 100})])
        self.assertEqual(s.step("oxygen"), [("buy_failed", {"action": "oxygen", "reason": "max_level"})])
        self.assertEqual((s.money, s.earned, s.upgrades), (100, 900, {"oxygen": 2}))

    def test_exact_price_buys_and_one_short_fails(self):
        s = shop(money=250)
        self.assertEqual(s.step("hp")[0][0], "bought")
        self.assertEqual(s.money, 0)
        s = shop(money=249)
        self.assertEqual(s.step("hp"), [("buy_failed", {"action": "hp", "reason": "funds"})])
        self.assertEqual((s.money, s.upgrades), (249, {}))

    def test_unknown_or_unsupported_command_fails(self):
        s = shop()
        for cmd in ("weapon", "net", "buy:ca_loc", "sell:ca_loc", "xyz"):
            self.assertEqual(s.step(cmd), [("buy_failed", {"action": cmd, "reason": "unknown"})], cmd)
        self.assertEqual(s.money, 1000)

    def test_empty_buy_does_nothing(self):
        self.assertEqual(shop().step(""), [])
        self.assertEqual(shop().step(None), [])

    def test_auto_close_after_600_active_ticks(self):
        s = shop()
        for i in range(599):
            self.assertEqual(s.step(), [], i)
        self.assertEqual(s.time_left_ticks, 1)
        self.assertEqual(s.step(), [("shop_end", {"reason": "time"})])
        self.assertTrue(s.done)
        self.assertEqual(s.step("hp"), [])  # đóng rồi thì bỏ qua

    def test_buy_before_done_on_same_tick_and_done_beats_time(self):
        s = shop()
        self.assertEqual([n for n, _ in s.step("hp", shop_done=True)], ["bought", "shop_end"])
        self.assertEqual(s.reason, "done")
        last = shop()
        last.time_left_ticks = 1
        self.assertEqual([n for n, _ in last.step("oxygen", shop_done=True)], ["bought", "shop_end"])
        self.assertEqual(last.reason, "done")

    def test_buy_on_final_timeout_tick_is_processed(self):
        s = shop()
        s.time_left_ticks = 1
        self.assertEqual([n for n, _ in s.step("oxygen")], ["bought", "shop_end"])
        self.assertEqual(s.reason, "time")

    def test_active_stats_follow_level(self):
        self.assertEqual(active_stats(T, {}), {"oxygen_max_s": 30, "hp_max": 3})
        self.assertEqual(active_stats(T, {"oxygen": 1, "hp": 2}), {"oxygen_max_s": 45, "hp_max": 5})
        self.assertEqual(active_stats(T, {"oxygen": 2}), {"oxygen_max_s": 60, "hp_max": 3})

    def test_snapshot_has_stock_and_time(self):
        s = ShopSim(T, 5, 9, {"hp": 1}, stock={"ca_loc": 1})
        snap = s.snapshot()
        self.assertEqual((snap["stock"], snap["time_left_ticks"], snap["upgrades"]), ({"ca_loc": 1}, 600, {"hp": 1}))


if __name__ == "__main__":
    unittest.main()
