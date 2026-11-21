# Smoke `--mode day` Phase 2 (preset và Shop thật)

Nền: `main@d4d2d2f` (đã ghép lát A–E), Python 3.15, Windows. Snapshot thưa để file proof gọn.

## 1. Một Ngày đầy đủ, không input

```bash
python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --snapshot-every 600 --out docs/proof/phase-2/day1-seed1.jsonl
```

- Kết thúc đúng tick **22.200**: gather 10.800 + quán 10.800 + Shop tự đóng 600, `reason: "days_complete"`, `days_completed: 1`.
- Thời gian **0,41 s** (đo bằng `time.perf_counter` quanh tiến trình, gồm khởi động CLI). Với `--snapshot-every 10` mặc định, lát D đo được 1,54 s ([day-ui.md](day-ui.md)). Ngưỡng ticket: ≤ 20 s.
- Đầu file: `day_start` → `day_plan {dishes:{ca_loc_nuong_trui:3, goi_bong_sung:3}, ingredients:{ca_loc:3, bong_sung:6}}` → `phase_start` (gather), đúng ví dụ ticket.
- File: [day1-seed1.jsonl](day1-seed1.jsonl).

## 2. Năm Ngày, mua nâng cấp và pause trong Shop

Ca rút ngắn bằng scenario [day5-scenario.json](day5-scenario.json) (`time_left_ticks: 5` cho gather và quán, tiền đầu kỳ 1.200); input [day5-inputs.json](day5-inputs.json).

```bash
python3 -m chonoi.headless --mode day --days 5 --seed 1 --scenario docs/proof/phase-2/day5-scenario.json \
  --inputs docs/proof/phase-2/day5-inputs.json --ticks 5000 --snapshot-every 1000 --out docs/proof/phase-2/day5-seed1.jsonl
```

| Tick | Ngày | Sự kiện | Kiểm |
|---|---|---|---|
| 12, 13 | 1 | `bought oxygen L1 (200)`, `bought hp L1 (250)` → money 750 | mua trừ `money`, giữ `earned` 1.200 |
| 14 | 1 | `shop_end done` → `day_start` D2 cùng tick | Ngày chốt khi Shop đóng |
| 14 | 2 | snapshot gather `active_upgrades {oxygen:1,hp:1}`, `oxygen_max_ticks 2700`, `hp_max 4` | cấp có hiệu lực từ Ngày kế |
| 26, 27 | 2 | `bought oxygen L2 (400)`, rồi `buy_failed max_level` | tối đa cấp 2, tiền giữ nguyên |
| 28 | 3 | gather `oxygen_max_ticks 3600`, quái `M1, M2` | M2 từ Ngày 3 |
| 41 → 51 | 3 | `paused` … `resumed`, `shop_end done` ở 52 | Shop đứng yên khi pause |
| 662, 1272 | 4, 5 | `shop_end time` (600 tick hoạt động) | tự đóng |
| end | — | `ticks 1272`, `sim_tick 1262`, `days_completed 5`, `days_complete`, money 350, earned 1.200, score 1.500 | 10 tick pause không tính vào `sim_tick` |

File: [day5-seed1.jsonl](day5-seed1.jsonl).

## 3. Ngất trong day vẫn mở quán với kho rỗng

Scenario [day-faint-scenario.json](day-faint-scenario.json): người chơi cạnh M1, Máu 1, giỏ 3 món.

```bash
python3 -m chonoi.headless --mode day --days 1 --seed 1 --scenario docs/proof/phase-2/day-faint-scenario.json --ticks 30 --snapshot-every 30 --out docs/proof/phase-2/day-faint.jsonl
```

Tick 11: `monster_hit {hp:0, lost:["bong_sung"]}` → `faint {cause:"monster", lost:["bong_sung","ca_loc"], hp:0}` → `gather_end fainted, items {}` → `phase_start` (quán) cùng tick; snapshot quán `phase_tick 0` có `stock {}`. File: [day-faint.jsonl](day-faint.jsonl).
