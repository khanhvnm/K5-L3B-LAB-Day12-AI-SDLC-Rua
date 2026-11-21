# Phase 4 — Soak headless 10 Ngày (AC-P4-04)

Người chạy: Trà (lát Soak). Nhánh `p4/soak`, dựng trên `main` `f1cfbad`. Máy: Windows 11, Python 3.12.10 (lệnh `python` thay cho `python3`). Khánh chạy lại trên commit bàn giao trước khi gắn tag.

```bash
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

Kết quả: [soak.json](soak.json), mã thoát 0.

| Trường | Giá trị |
|---|---|
| `days` / `days_completed` | 10 / 10 |
| `crashes` | 0 |
| `results[9]` (Ngày 10) | `earned` 1664, `reputation` 5, `score` 2164 |
| `duration_s` | 4.739 (lần 1), 4.539 (lần 2) |

- **Tất định:** chạy hai lần cùng seed 7, bỏ `duration_s` thì toàn bộ JSON giống hệt (cũng kiểm trong `tests/test_soak.py::test_cung_seed_lap_lai_giong_het_tru_thoi_gian`).
- **Bot** (`chonoi/soak.py`, chỉ đọc snapshot của sim): sáng hái nút ở mặt nước và bắt cá ở d < 10 (ngoài tầm Cá Sấu), nổi lên khi oxy thấp, về bến kịp giờ; tối phục vụ món trên tay → lấy món chín → nấu đơn đang chờ; Shop thử mua `oxygen`, `hp` rồi `shop_done`. Tổng thu tăng mỗi Ngày, nên soak đi qua cả nấu, phục vụ, boa, uy tín và mua nâng cấp — không chỉ chuyển pha.
- **Kế hoạch lặp:** Ngày 6–10 dùng lại D1–D5 (`dayplan.plan_for_day`); Cá Sấu M2 có mặt từ Ngày 3 trở đi (`from_day ≤ day`).
- Test: `tests/test_soak.py` (7 test: đủ 10 Ngày qua `soak_cmd`, tất định, đếm lỗi, tham số sai mã 2, id cá thể tăng xuyên Ngày, kế hoạch lặp, headless vẫn giới hạn 5 Ngày). Full suite trên nhánh: 161/161.
