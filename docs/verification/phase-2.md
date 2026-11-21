# Ma trận truy vết Phase 2 (đang cập nhật)

Mã AC-P2-xx định nghĩa trong [kế hoạch Phase 2](../plan/phase-2.md). Kết quả tích hợp lấy từ working tree ghép `p2/day-ui` với `main@d5c4b54`; xem [bằng chứng và lệnh chạy](../proof/phase-2/day-ui.md).

| AC | Cách kiểm chứng | Kết quả |
|---|---|---|
| AC-P2-01 — contract v1.1, số chuẩn, 6 nguyên liệu, 6 món là dữ liệu | `tests/test_gather_v11.py::Contract`; `load_contract()` kiểm dải, `day_plan.ingredients` khớp công thức × suất | Đạt (Khánh, 2026-11-21) |
| AC-P2-02 — gather số chuẩn, N1–N6, bắt cá 3 loài | `test_gather_v11.py::Species`, `test_gather_rules.py` cũ (10/10) | Đạt |
| AC-P2-03 — cá bơi/phản xạ/sinh, `fish_spawned`, `random_fish:false`, `age_ticks` | `test_gather_v11.py::Fish` (14 test); headless gather 10.800 tick, seed 1: 4 lần sinh tới trần 12 | Đạt |
| AC-P2-04 — Cá Sấu, hit/ngất, bố trí theo Ngày | `test_monsters.py` và smoke day D1–D5 (M2 từ D3) | Qua |
| AC-P2-05–06 — Quán và kế hoạch ngày | `test_quan_rules.py`, `test_day_plan.py`, `test_day.py`: quán trong day lọc món và không giới hạn số lượt gọi theo số suất; kế hoạch chuẩn D1–D5 | Qua |
| AC-P2-07 — Shop (mua, buy_failed, đóng, cấp có hiệu lực) | `test_shop_rules.py`, JSONL hai ngày qua Shop thật, mua và đóng cùng tick cuối | Qua |
| AC-P2-08–09 — vòng ngày và pause | `test_day.py`, headless v1.1 22.200 tick trong 1,541 s | Qua trên máy thử |
| AC-P2-10 — scenario | `test_day.py`, `test_monsters.py`, `test_gather_v11.py` | Qua; mâu thuẫn kho trả mã 2, giữ file đích |
| AC-P2-11 — UI/HUD | Node và Chrome headless 1280×720 với Shop thật và ca rút ngắn | Qua vòng UI; 110,8 FPS Gather, 119,8 FPS Quán trên máy thử |
| AC-P2-12 — regression P1 với số chuẩn | Full suite **123/123 pass** (~40 s). Test P1 đổi vì số chuẩn: `test_snapshot_tick0_dung_truong` (4 bàn), `test_chon_mon_deu_theo_seed_va_tat_dinh` (6 món/6 nguyên liệu, 80 seed), `test_het_ban_thi_bo_luot` (4 bàn phải lấp đầy), `test_gather_snapshot_has_gather_fields` (8 đàn). Luật không bị nới. | Qua |
