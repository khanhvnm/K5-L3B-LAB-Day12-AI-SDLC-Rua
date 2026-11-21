# Ma trận truy vết Phase 2 (đang cập nhật)

Mã AC-P2-xx định nghĩa trong [kế hoạch Phase 2](../plan/phase-2.md). Chỉ ghi kết quả đã thực sự chạy.

| AC | Cách kiểm chứng | Kết quả |
|---|---|---|
| AC-P2-01 — contract v1.1, số chuẩn, 6 nguyên liệu, 6 món là dữ liệu | `tests/test_gather_v11.py::Contract`; `load_contract()` kiểm dải, `day_plan.ingredients` khớp công thức × suất | Đạt (Khánh, 2026-11-21) |
| AC-P2-02 — gather số chuẩn, N1–N6, bắt cá 3 loài | `test_gather_v11.py::Species`, `test_gather_rules.py` cũ (10/10) | Đạt |
| AC-P2-03 — cá bơi/phản xạ/sinh, `fish_spawned`, `random_fish:false`, `age_ticks` | `test_gather_v11.py::Fish` (14 test); headless gather 10.800 tick, seed 1: 4 lần sinh tới trần 12 | Đạt |
| AC-P2-07 — Shop (mua, buy_failed, đóng, cấp có hiệu lực) | `tests/test_shop_rules.py` (9 test) — luật độc lập; chưa nối vào `--mode day` | Luật đạt; tích hợp chờ lát D |
| AC-P2-04, 05, 06 (phần day_plan trong dữ liệu đạt), 08, 09, 10, 11 | Chưa làm / thuộc lát khác | Chưa |
| AC-P2-12 — regression P1 với số chuẩn | Full suite **90/90 pass** (`PYTHONPATH=tests:. python -m unittest discover -s tests`, ~52 s). Test P1 đổi vì số chuẩn: `test_snapshot_tick0_dung_truong` (4 bàn), `test_chon_mon_deu_theo_seed_va_tat_dinh` (6 món/6 nguyên liệu, 80 seed), `test_het_ban_thi_bo_luot` (4 bàn phải lấp đầy), `test_gather_snapshot_has_gather_fields` (8 đàn). Luật không bị nới. | Đạt |
