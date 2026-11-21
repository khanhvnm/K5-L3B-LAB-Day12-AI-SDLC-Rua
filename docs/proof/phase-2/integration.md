# Smoke tích hợp Phase 2 — gather → quán (số chuẩn v1.1)

Nền: `main@d4d2d2f`, Python 3.15, Windows (Git Bash). Chạy từ gốc repo.

```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-2/integration-dock.json \
  --inputs docs/proof/phase-2/integration-inputs.json --ticks 1 --snapshot-every 1 \
  --out docs/proof/phase-2/integration-gather.jsonl --inventory-out docs/proof/phase-2/integration-inventory.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-2/integration-inventory.json \
  --ticks 0 --out docs/proof/phase-2/integration-quan.jsonl
```

- Fixture [integration-dock.json](integration-dock.json): giỏ có cả hai nguyên liệu mới (`ca_keo`, `keo_neo`), đứng ở bến; [integration-inputs.json](integration-inputs.json) nhấn `interact` ở tick 0.
- Cả hai lệnh mã thoát `0`.
- [integration-gather.jsonl](integration-gather.jsonl): `gather_end` tick 1, `reason: "docked"`, `inventory.items = {"bong_sung":2,"ca_keo":2,"ca_loc":1,"keo_neo":1}`.
- [integration-inventory.json](integration-inventory.json) trùng từng khóa với `gather_end.inventory`.
- [integration-quan.jsonl](integration-quan.jsonl) snapshot tick 0: `stock` bằng đúng kho trên, quán có 2 bếp (B1, B2) và 4 bàn (T1–T4).

Kết luận: bàn giao kho hai tiến trình đạt với 6 nguyên liệu v1.1.
