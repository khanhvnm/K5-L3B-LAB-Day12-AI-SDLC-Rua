# Bằng chứng tích hợp Phase 3 — contract v1.2 trên bản ghép

Nền: nhánh `p3/integrate` = `main@376e56b` (lát Quán PR #8, Day/HUD PR #9) + `p3/schema` (lát S/G), Python 3.15, Windows. Chạy từ gốc repo.

## Việc tích hợp

- `p3/schema` chưa vào `main` khi PR #8, #9 được merge; hai lát kia làm trên nền cũ với adapter riêng. Ghép lại: giữ `chonoi/sim/quan.py` và test của Trà/Thành, bỏ adapter tạm của lát S trong `QuanSim`, bỏ khối `freshness` bị khai hai lần trong `game.contract.json`.
- Cấp id mới cho mẫu `gather.hold` ở Ngày ≥ 2 chỉ còn ở `chonoi/day.py` (bản của Thành); bỏ cờ `renew_hold_ids` trùng trong `GatherSim`.
- `day.delivered` lấy đúng `gather_end.inventory.items` (cùng schema kho v1.2).
- Gỡ nhánh nhận kho **đếm** trong `QuanSim._items_from` vì mọi đầu vào v1.2 (file, `quan.stock`, bàn giao day) đều là mảng cá thể và đã bị kiểm schema.
- `test_smoke_p1::test_inv_01_...` so snapshot quán với file theo id/kind/fresh (trước đây so kho đếm).

## 1. Smoke của ticket

| Lệnh | Kết quả |
|---|---|
| `gather --scenario spoil-scenario.json --ticks 1` | [spoil-gather.jsonl](spoil-gather.jsonl): `{"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}` — trùng dòng ticket |
| `gather --scenario handoff-scenario.json --inputs handoff-inputs.json --ticks 1 --inventory-out handoff-inventory.json` | `gather_end docked`; [handoff-inventory.json](handoff-inventory.json) `{"items":[{"id":"I1","kind":"ca_linh","fresh":99.99166666666666}]}` (đúng một lần hao) |
| `quan --inventory handoff-inventory.json --ticks 0` | [handoff-quan.jsonl](handoff-quan.jsonl) snapshot tick 0 `stock [{"id":"I1","kind":"ca_linh","fresh":99.992}]` — cùng id, kind; fresh trong dung sai ±0,01 (JSONL làm tròn 3 chữ số) |
| `quan --inventory count-inventory.json --ticks 0` | mã **2**, không tạo output |

## 2. Quán: giữ theo id, giá theo tươi, ươn giữa ca

```bash
python3 -m chonoi.headless --mode quan --seed 1 --scenario docs/proof/phase-3/quan-fresh-scenario.json --inputs docs/proof/phase-3/quan-fresh-inputs.json --ticks 5 --snapshot-every 1 --out docs/proof/phase-3/quan-fresh.jsonl
```

[quan-fresh-scenario.json](quan-fresh-scenario.json): `I1 ca_loc 50`, `I2 ca_loc 30.0125`, `I3 bong_sung 100`, khách C1 gọi cá lóc nướng, không khai `reserved`, người chơi đứng ở bếp B1.

- Snapshot tick 0: C1 `reserved ["I1"]` — cá thể chưa ươn **tươi nhất** của loại.
- Tick 1 `cook_started items [{"id":"I1","kind":"ca_loc","fresh":49.996}], base_price 29` = floor(60 × 49,9958/100).
- Tick 4 `spoiled {"item_id":"I2","kind":"ca_loc","location":"stock"}`: 30,0125 − 4 × 0,25/60 = 29,9958 < 30 (tick 3 còn đúng 30,0000). File: [quan-fresh.jsonl](quan-fresh.jsonl).

## 3. Day: bàn giao, pause, Shop, id xuyên Ngày

```bash
python3 -m chonoi.headless --mode day --days 2 --seed 1 --scenario docs/proof/phase-3/day-scenario.json --inputs docs/proof/phase-3/day-inputs.json --ticks 2000 --snapshot-every 1 --out docs/proof/phase-3/day2-fresh.jsonl
```

| Tick | Quan sát | Luật |
|---|---|---|
| 0 → 2 | `I1` 100 → 99.983, `I2` 31 → 30.983 | giỏ hao 0,5/s |
| 3 → 12 | `paused` … `resumed` ở 13; `sim_tick` và fresh đứng yên ở 2 / 99.983 | pause dừng hao tươi |
| 15 | `gather_end time` inventory 99.958 / 30.958; snapshot quán cùng tick `phase_tick 0` cùng giá trị | bàn giao cùng tick, không hao thêm |
| 16 | 99.954 / 30.954 | quán hao 0,25/s từ bước sau |
| 20 → 619 | Shop `stock` giữ 99.938 / 30.938 suốt 600 tick | hàng ở Shop không hao |
| 625 | Ngày 2 `gather_end` cá thể `I3`, `I4` (mẫu `hold` cấp id mới, kind/fresh như mẫu) | id tăng xuyên Ngày |
| end | `ticks 1230`, `sim_tick 1220`, `days_complete`, `days_completed 2` | |

File: [day-scenario.json](day-scenario.json), [day-inputs.json](day-inputs.json), [day2-fresh.jsonl](day2-fresh.jsonl).

## 4. Hiệu năng và regression

- `day --days 1 --ticks 22200` (preset thật, seed 1): `days_complete` đúng tick 22.200; **0,44 s** với `--snapshot-every 600` ([day1-seed1.jsonl](day1-seed1.jsonl)), **0,69 s** với snapshot mặc định. Ngưỡng ≤ 20 s.
- Full suite **154/154 pass** (`PYTHONPATH=tests:. python3 -m unittest discover -s tests`, ~60 s), gồm `test_fresh_v12` (15), `test_fresh_quan` (13), `test_day` (9); Node UI **12/12**.
