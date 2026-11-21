# Ma trận truy vết Phase 3 (đang cập nhật)

Mã AC-P3-xx định nghĩa trong [kế hoạch Phase 3](../plan/phase-3.md). Chỉ ghi kết quả đã chạy.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 — contract 1.2, `freshness` | `test_fresh_v12.py::Contract12` | — | Đạt (Khánh) |
| AC-P3-02 — schema kho cá thể, mã 2 cho kho đếm/sai schema, ghi nguyên tử theo id, ngất → rỗng, chạm `--ticks` giữ đích | `test_fresh_v12.py::InventoryFile`, `::GatherFresh::test_tick_limit_before_end_keeps_destination`, `test_monsters`, `test_gather_rules` | [schema-gather.md](../proof/phase-3/schema-gather.md) §2–3 | Đạt |
| AC-P3-03 — gather: fresh 100, hao 0.5/s từ bước sau, `spoiled` một lần theo id, `lost` cá thể LIFO, scenario `hold` cá thể | `test_fresh_v12.py::GatherFresh` | [schema-gather.md](../proof/phase-3/schema-gather.md) §1 | Đạt |
| AC-P3-04, 05, 06 — quán (hao, spoiled stock, giữ theo id, giá theo tươi, scenario) | Lát Quán (Trà) | — | Chưa; quán đang dùng adapter tạm |
| AC-P3-07 — day (bàn giao cá thể, id xuyên Ngày, Shop) | `test_fresh_v12.py::DayIds` (id mới cho mẫu `hold` Ngày 2) | — | Một phần; phần còn lại lát Thành |
| AC-P3-08 — HUD độ tươi | Lát Thành | — | Chưa |
| AC-P3-09 — smoke ticket | Ngưỡng: đạt. Bàn giao: file đạt, so id/fresh ở snapshot quán chờ lát Quán | [schema-gather.md](../proof/phase-3/schema-gather.md) | Một phần |
| AC-P3-10 — regression P1–P2 | Full suite **138/138 pass** trên `p3/schema`; test đổi chỉ vì schema, liệt kê trong `CHANGELOG.md` | — | Đạt |
