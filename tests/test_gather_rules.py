"""Headless acceptance tests for Phase 1 gather rules (PRD-0, sections E-G)."""

import json
import unittest

from helpers import (Workdir, count_kinds, events, frames, kinds_of, make_items, read_jsonl, run_headless,
                     snapshots, write_json)


def gather_tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class GatherRules(unittest.TestCase):
    def run_case(self, workdir, scenario, input_frames=(), ticks=1, inventory_out=False):
        scenario_path = write_json(workdir.path("scenario.json"), {"gather": scenario})
        inputs_path = write_json(workdir.path("inputs.json"), frames(*input_frames))
        output_path = workdir.path("run.jsonl")
        args = ["--mode", "gather", "--seed", "42", "--scenario", scenario_path,
                "--inputs", inputs_path, "--ticks", str(ticks), "--snapshot-every", "1",
                "--out", output_path]
        inventory_path = None
        if inventory_out:
            inventory_path = workdir.path("inventory.json")
            args.extend(["--inventory-out", inventory_path])
        code, err = run_headless(*args)
        self.assertEqual(code, 0, err)
        return read_jsonl(output_path), inventory_path

    @staticmethod
    def quiet_scene(**overrides):
        scene = {"nodes": [], "fish": [], "random_fish": False}
        scene.update(overrides)
        return scene

    def test_oxygen_empty_when_diving(self):
        with Workdir() as w:
            rows, _ = self.run_case(
                w,
                self.quiet_scene(player={"pos": [20, 5], "oxygen_ticks": 1}),
            )

            empty = events(rows, "oxygen_empty")
            self.assertEqual(len(empty), 1)
            self.assertEqual(empty[0]["tick"], 1)
            self.assertEqual(empty[0]["data"], {"oxygen_ticks": 0})
            p = snapshots(rows)[-1]["player"]
            self.assertEqual(p["oxygen_ticks"], 0)
            self.assertEqual(p["zero_oxy_ticks"], 1)
            self.assertEqual(p["hp"], p["hp_max"])

    def test_surface_refills_oxygen_and_resets_choke_counter(self):
        with Workdir() as w:
            rows, _ = self.run_case(
                w,
                self.quiet_scene(player={
                    "pos": [20, 0.6], "oxygen_ticks": 0, "zero_oxy_ticks": 10,
                }),
                input_frames=({"tick": 0, "move": [0, -1]},),
                ticks=4,
            )

            surfaced = events(rows, "surface")
            self.assertEqual(len(surfaced), 1)
            self.assertEqual(surfaced[0]["tick"], 4)
            p = snapshots(rows)[-1]["player"]
            self.assertTrue(p["at_surface"])
            self.assertEqual(p["oxygen_ticks"], gather_tuning()["oxygen_refill_per_tick"])
            self.assertEqual(p["zero_oxy_ticks"], 0)
            self.assertEqual(p["hp"], p["hp_max"])

    def test_choke_faint_drops_hold_lifo_and_writes_empty_inventory(self):
        with Workdir() as w:
            lost_in_lifo_order = ["bong_dien_dien", "bong_sung", "ca_loc"]
            rows, inventory_path = self.run_case(
                w,
                self.quiet_scene(
                    player={"pos": [20, 5], "oxygen_ticks": 0,
                            "zero_oxy_ticks": 59, "hp": 1},
                    hold=make_items(list(reversed(lost_in_lifo_order))),
                ),
                inventory_out=True,
            )

            choke = events(rows, "choke")
            self.assertEqual(len(choke), 1)
            self.assertEqual(choke[0]["data"]["hp"], 0)
            faint = events(rows, "faint")
            self.assertEqual(len(faint), 1)
            data = faint[0]["data"]  # v1.2: kho cá thể
            self.assertEqual((data["cause"], kinds_of(data["lost"]), data["hp"]), ("choke", lost_in_lifo_order, 0))
            self.assertEqual([it["id"] for it in data["lost"]], ["I3", "I2", "I1"])
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "fainted")
            self.assertEqual(end[0]["data"]["inventory"], {"items": []})
            with open(inventory_path, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_harvest_selects_nearest_then_lowest_id_on_tie(self):
        with Workdir() as w:
            nodes = [
                {"id": "N1", "kind": "bong_dien_dien", "pos": [21, 0]},
                {"id": "N2", "kind": "bong_sung", "pos": [20.5, 0]},
                {"id": "N3", "kind": "bong_dien_dien", "pos": [19.5, 0]},
            ]
            rows, _ = self.run_case(
                w,
                self.quiet_scene(player={"pos": [20, 0]}, nodes=nodes),
                input_frames=({"tick": 0, "interact": True},),
            )

            gathered = events(rows, "gather")
            self.assertEqual(len(gathered), 1)
            self.assertEqual(gathered[0]["data"], {
                "node_id": "N2", "kind": "bong_sung", "amount": gather_tuning()["node_yield"],
            })
            s = snapshots(rows)[-1]
            self.assertEqual(kinds_of(s["hold"]), ["bong_sung"] * gather_tuning()["node_yield"])
            ready = {n["id"]: n["ready"] for n in s["nodes"]}
            self.assertFalse(ready["N2"])
            self.assertTrue(ready["N1"])
            self.assertTrue(ready["N3"])

    def test_regrown_node_can_be_harvested_in_same_tick(self):
        with Workdir() as w:
            node = {"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 1}
            rows, _ = self.run_case(
                w,
                self.quiet_scene(player={"pos": [20, 0]}, nodes=[node]),
                input_frames=({"tick": 0, "interact": True},),
            )

            self.assertEqual([e["name"] for e in events(rows)], ["node_regrown", "gather"])
            s = snapshots(rows)[-1]
            self.assertEqual(kinds_of(s["hold"]), ["bong_sung"] * gather_tuning()["node_yield"])
            n = s["nodes"][0]
            self.assertFalse(n["ready"])
            self.assertEqual(n["regrow_ticks"], round(gather_tuning()["regrow_s"] * 60))

    def test_harvest_with_full_hold_keeps_node_ready(self):
        with Workdir() as w:
            capacity = gather_tuning()["hold_capacity"]
            node = {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}
            rows, _ = self.run_case(
                w,
                self.quiet_scene(
                    player={"pos": [20, 0]},
                    hold=make_items(["ca_loc"] * capacity),
                    nodes=[node],
                ),
                input_frames=({"tick": 0, "interact": True},),
            )

            full = events(rows, "hold_full")
            self.assertEqual(len(full), 1)
            self.assertEqual(full[0]["data"], {
                "action": "gather", "node_id": "N1", "required": gather_tuning()["node_yield"], "free": 0,
            })
            s = snapshots(rows)[-1]
            self.assertEqual(kinds_of(s["hold"]), ["ca_loc"] * capacity)
            self.assertTrue(s["nodes"][0]["ready"])

    def test_fish_catch_uses_nearest_and_respects_cooldown(self):
        with Workdir() as w:
            cooldown = int(round(gather_tuning()["catch_cooldown_s"] * 60))
            fish = [
                {"id": "F1", "kind": "ca_linh", "pos": [20, 5]},
                {"id": "F2", "kind": "ca_loc", "pos": [21, 5]},
            ]
            input_frames = (
                {"tick": 0, "catch": True},
                {"tick": 1, "catch": False},
                {"tick": 2, "catch": True},  # cạnh lên trong hồi chiêu: bị bỏ qua
                {"tick": 3, "catch": False},
                {"tick": cooldown, "catch": True},
            )
            rows, _ = self.run_case(
                w,
                self.quiet_scene(player={"pos": [20, 5]}, fish=fish),
                input_frames=input_frames,
                ticks=cooldown + 1,
            )

            caught = events(rows, "fish_caught")
            self.assertEqual([e["tick"] for e in caught], [1, cooldown + 1])
            self.assertEqual([e["data"]["fish_id"] for e in caught], ["F1", "F2"])
            self.assertEqual([e["data"]["yield"] for e in caught], [
                gather_tuning()["fish_yield"]["ca_linh"],
                gather_tuning()["fish_yield"]["ca_loc"],
            ])
            s = snapshots(rows)[-1]
            expected_hold = (["ca_linh"] * gather_tuning()["fish_yield"]["ca_linh"]
                             + ["ca_loc"] * gather_tuning()["fish_yield"]["ca_loc"])
            self.assertEqual(kinds_of(s["hold"]), expected_hold)
            self.assertEqual(s["fish"], [])

    def test_catch_with_full_hold_keeps_fish_and_cooldown(self):
        with Workdir() as w:
            tuning = gather_tuning()
            capacity = tuning["hold_capacity"]
            required = tuning["fish_yield"]["ca_linh"]
            free = required - 1
            fish = [{"id": "F1", "kind": "ca_linh", "pos": [20, 5]}]
            rows, _ = self.run_case(
                w,
                self.quiet_scene(
                    player={"pos": [20, 5]},
                    hold=make_items(["ca_loc"] * (capacity - free)),
                    fish=fish,
                ),
                input_frames=({"tick": 0, "catch": True},),
            )

            full = events(rows, "hold_full")
            self.assertEqual(len(full), 1)
            self.assertEqual(full[0]["data"], {
                "action": "catch", "fish_id": "F1", "required": required, "free": free,
            })
            s = snapshots(rows)[-1]
            self.assertEqual(kinds_of(s["hold"]), ["ca_loc"] * (capacity - free))
            self.assertEqual([f["id"] for f in s["fish"]], ["F1"])
            self.assertEqual(s["player"]["catch_cd_ticks"], 0)

    def test_dock_interaction_takes_priority_over_harvest(self):
        with Workdir() as w:
            dock = gather_tuning()["dock_pos"]
            node = {"id": "N1", "kind": "bong_sung", "pos": list(dock)}
            rows, _ = self.run_case(
                w,
                self.quiet_scene(player={"pos": list(dock)}, nodes=[node]),
                input_frames=({"tick": 0, "interact": True},),
            )

            self.assertEqual(events(rows, "gather"), [])
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "docked")
            self.assertEqual(snapshots(rows)[-1]["hold"], [])

    def test_harvest_on_last_tick_is_in_time_end_inventory(self):
        with Workdir() as w:
            node = {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}
            rows, _ = self.run_case(
                w,
                self.quiet_scene(
                    player={"pos": [20, 0]}, nodes=[node], time_left_ticks=1,
                ),
                input_frames=({"tick": 0, "interact": True},),
            )

            self.assertEqual([e["name"] for e in events(rows)], ["gather", "gather_end"])
            end = events(rows, "gather_end")[-1]["data"]
            self.assertEqual(end["reason"], "time")
            self.assertEqual(count_kinds(end["inventory"]["items"]), {"bong_sung": gather_tuning()["node_yield"]})


if __name__ == "__main__":
    unittest.main()
