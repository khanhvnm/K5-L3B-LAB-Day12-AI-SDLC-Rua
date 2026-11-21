# Bằng chứng lát S (schema/adapter) và G (gather) — TICKET-03, contract v1.2

Nền: nhánh `p3/schema` trên `main@e28b544`, Python 3.15, Windows (Git Bash). Chạy từ gốc repo.

## 1. Ngưỡng ươn (ví dụ của ticket)

```bash
python3 -m chonoi.headless --mode gather --seed 1 --scenario docs/proof/phase-3/spoil-scenario.json --ticks 1 --out docs/proof/phase-3/spoil-gather.jsonl
```

[spoil-scenario.json](spoil-scenario.json) (`I1 ca_linh fresh 30`) → [spoil-gather.jsonl](spoil-gather.jsonl) có đúng dòng của ticket:

```json
{"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}
```

## 2. Bàn giao file gather → quán

```bash
python3 -m chonoi.headless --mode gather --seed 1 --scenario docs/proof/phase-3/handoff-scenario.json --inputs docs/proof/phase-3/handoff-inputs.json --ticks 1 --out docs/proof/phase-3/handoff-gather.jsonl --inventory-out docs/proof/phase-3/handoff-inventory.json
python3 -m chonoi.headless --mode quan --seed 1 --inventory docs/proof/phase-3/handoff-inventory.json --ticks 0 --out docs/proof/phase-3/handoff-quan.jsonl
```

- Cả hai mã thoát `0`. `gather_end` tick 1, `reason: "docked"`.
- [handoff-inventory.json](handoff-inventory.json): `{"items":[{"id":"I1","kind":"ca_linh","fresh":99.99166666666666}]}` = 100 − 0,5/60 (đúng một lần hao ở bước gather, độ chính xác đầy đủ).
- `gather_end.data.inventory` trong JSONL cùng schema, `fresh` 99.992 (khung `jsonl.py` làm tròn 3 chữ số; trong dung sai ±0,01 của ticket).
- [handoff-quan.jsonl](handoff-quan.jsonl): quán đọc file v1.2 thành công. **Chưa đạt phần so id/fresh ở snapshot quán**: snapshot vẫn là `stock {"ca_linh":1}` qua adapter tạm trong `QuanSim` — lát Quán (Trà) chuyển `stock` sang mảng cá thể.

## 3. Kho đếm bị từ chối

```bash
python3 -m chonoi.headless --mode quan --seed 1 --inventory docs/proof/phase-3/count-inventory.json --ticks 0 --out docs/proof/phase-3/should-not-exist.jsonl
```

[count-inventory.json](count-inventory.json) `{"items":{"ca_loc":1}}` → mã thoát **2**, stderr `file kho items phải là mảng cá thể {id, kind, fresh} (contract v1.2; kho đếm không còn hợp lệ)`, không tạo file output.

## 4. Test tự động

- `tests/test_fresh_v12.py` (15 test): contract 1.2; file kho từ chối 11 dạng sai (kho đếm, thiếu/thừa khóa, kind lạ, id trùng/rỗng, fresh ngoài miền/NaN/boolean); ghi sắp theo id, nguyên tử, round-trip giữ nhánh ngưỡng 30; spoiled đúng một lần, nhiều cá thể theo id; kẹp đáy 0; hàng mới fresh 100 hao từ bước sau, id nối tiếp; bắt cá tạo một cá thể mỗi đơn vị; `lost` của `monster_hit`/`faint` là cá thể LIFO; chạm `--ticks` giữ nguyên file đích; scenario `hold` sai → mã 2; day Ngày 2 cấp id mới cho mẫu `hold`.
- Full suite: **138/138 pass** (`PYTHONPATH=tests:. python3 -m unittest discover -s tests`, ~50 s).
