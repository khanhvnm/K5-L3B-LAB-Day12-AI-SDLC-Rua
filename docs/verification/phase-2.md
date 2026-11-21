# Ma trận truy vết Phase 2

Mã AC-P2-xx định nghĩa trong [kế hoạch Phase 2](../plan/phase-2.md). Kết quả tích hợp lấy từ working tree ghép `p2/day-ui` với `main@d5c4b54`; xem [bằng chứng và lệnh chạy](../proof/phase-2/day-ui.md).

| AC | Cách kiểm chứng | Kết quả |
|---|---|---|
| AC-P2-01 — contract v1.1, số chuẩn, 6 nguyên liệu, 6 món là dữ liệu | `tests/test_gather_v11.py::Contract`; `load_contract()` kiểm dải, `day_plan.ingredients` khớp công thức × suất | Đạt (Khánh, 2026-11-21) |
| AC-P2-02 — gather số chuẩn, N1–N6, bắt cá 3 loài | `test_gather_v11.py::Species`, `test_gather_rules.py` cũ (10/10) | Đạt |
| AC-P2-03 — cá bơi/phản xạ/sinh, `fish_spawned`, `random_fish:false`, `age_ticks` | `test_gather_v11.py::Fish` (14 test); headless gather 10.800 tick, seed 1: 4 lần sinh tới trần 12 | Đạt |
| AC-P2-04 — Cá Sấu, hit/ngất, bố trí theo Ngày | `test_monsters.py` (11 test); [day-smoke.md](../proof/phase-2/day-smoke.md) §2 (M2 từ D3), §3 (ngất do quái → quán kho rỗng) | Đạt |
| AC-P2-05–06 — Quán và kế hoạch ngày | `test_quan_rules.py`, `test_day_plan.py`, `test_day.py`: quán trong day lọc món và không giới hạn số lượt gọi theo số suất; kế hoạch chuẩn D1–D5 | Qua |
| AC-P2-07 — Shop (mua, buy_failed, đóng, cấp có hiệu lực) | `test_shop_rules.py` (9 test), `test_day.py`; [day-smoke.md](../proof/phase-2/day-smoke.md) §2: mua L1/L2, `max_level`, đóng `done`/`time`, cấp áp từ Ngày kế | Đạt |
| AC-P2-08–09 — vòng ngày và pause | `test_day.py`; [day-smoke.md](../proof/phase-2/day-smoke.md) §1: 1 Ngày đúng 22.200 tick, 0,41 s (1,54 s với snapshot mỗi 10 tick); §2: 5 Ngày `days_complete`, pause trong Shop giữ `sim_tick` | Đạt trên máy thử |
| AC-P2-10 — scenario | `test_day.py`, `test_monsters.py`, `test_gather_v11.py` | Qua; mâu thuẫn kho trả mã 2, giữ file đích |
| AC-P2-11 — UI/HUD | Node và Chrome headless 1280×720 với Shop thật và ca rút ngắn | Qua vòng UI; 110,8 FPS Gather, 119,8 FPS Quán trên máy thử |
| AC-P2-12 — regression P1 với số chuẩn | Full suite **123/123 pass** (48 s, `main@d4d2d2f` + thay đổi bàn giao) và Node UI **10/10**. Test P1 đổi vì số chuẩn: `test_snapshot_tick0_dung_truong` (4 bàn), `test_chon_mon_deu_theo_seed_va_tat_dinh` (6 món/6 nguyên liệu, 80 seed), `test_het_ban_thi_bo_luot` (4 bàn phải lấp đầy), `test_gather_snapshot_has_gather_fields` (8 đàn). Luật không bị nới. | Qua |
| Smoke tích hợp gather → quán (ticket phút 20) | Hai tiến trình `--inventory-out` → `--inventory`, 6 nguyên liệu v1.1; [integration.md](../proof/phase-2/integration.md) | Đạt |

## Đánh giá DoD

- **Đạt:** contract 1.1 và số chuẩn; cá bơi/sinh, Cá Sấu, Máu/ngất, 2 bếp/4 bàn; `--mode day` công bố D1–D5, chốt Ngày khi Shop đóng, áp oxygen/hp từ Ngày kế; pause; smoke tích hợp; regression P1 (test đổi có ghi lý do ở trên).
- **Còn hạn chế:** UI chỉ được kiểm bằng test Node và Chrome headless với ca rút ngắn; **chưa có lượt chơi tay trọn 5 Ngày** được ghi lại. FPS đo trên một máy thử, không phải máy chấm.
- **Không làm mở rộng** (nhóm 3 người không bắt buộc); manifest không khai `extensions`.
- Giả định còn mở: `docs/clarify.md` P2-01..P2-07 (đặc biệt P2-05, cách đếm 90 tick bất tử).
- Commit bàn giao: commit gắn tag `phase-2` (ghi hash khi gắn tag).
