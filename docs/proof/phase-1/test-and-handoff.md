# Phase 1 — test suite và smoke bàn giao kho

Kết quả do Khánh gửi sau khi gộp `p1/quan` vào `main`. Khi rà lại, `main` đang ở commit `86f2f25` (merge `p1/quan`). Transcript gốc do người chạy giữ; báo cáo này ghi lại kết quả cần truy vết mà không chép đường dẫn máy cục bộ.

## Bộ test

PowerShell:

```powershell
$env:PYTHONPATH = "tests;."
python3 -m unittest discover -s tests -v
```

Kết quả: **Ran 51 tests in 29.851s — OK**.

Các test gồm luật quan trong `tests/test_quan_rules.py`, deterministic output, kiểm lỗi contract/scenario, di chuyển và biên, hết giờ, cùng test inventory gather → quan.

## Smoke hai tiến trình

Chạy `gather` với fixture `dock.json` và input tương tác tick 0, sau đó chạy `quan` đọc file inventory vừa tạo. Cả hai lệnh headless hoàn tất không báo lỗi.

Lệnh đã chạy trong PowerShell:

```powershell
python3 -m chonoi.headless --mode gather --seed 42 --scenario "$proof/dock.json" --inputs "$proof/dock-inputs.json" --ticks 1 --out "$proof/gather.jsonl" --inventory-out "$proof/inventory.json"
python3 -m chonoi.headless --mode quan --seed 42 --inventory "$proof/inventory.json" --ticks 0 --out "$proof/quan.jsonl"
```

- Event cuối của gather: tick `1`, `gather_end`, reason `docked`.
- File [inventory.json](inventory.json): `{"items":{"bong_sung":2,"ca_loc":1}}`.
- Snapshot tick 0 trong [quan.jsonl](quan.jsonl): `stock` là `{"bong_sung":2,"ca_loc":1}`.
- Fixture: [dock.json](dock.json), [dock-inputs.json](dock-inputs.json).
- JSONL gather: [gather.jsonl](gather.jsonl).

## Giới hạn bằng chứng

Output này xác nhận contract/test suite và bàn giao kho. Nó không kiểm chứng trực tiếp luật oxy/ngạt/ngất, hái/mọc lại, bắt cá/hồi chiêu/giỏ đầy hoặc HUD/UI; các mục đó vẫn cần bằng chứng riêng.

## Bổ sung kiểm chứng Gather

Phần giới hạn trên mô tả trạng thái tại thời điểm ghi smoke ban đầu. Sau đó, Khánh chạy bộ test headless trực tiếp cho các luật Gather và toàn bộ suite; kết quả mới nhất là **10/10 test Gather** và **61/61 test toàn bộ**, đều pass. Chi tiết: [gather-rules-tests.md](gather-rules-tests.md). UI/HUD vẫn chưa được kiểm chứng trực tiếp.
