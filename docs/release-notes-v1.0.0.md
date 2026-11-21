# Quán Ăn Chợ Nổi v1.0.0 — nhóm Rua

Bản phát hành cuối của Lab Day 12 (AI SDLC). Test Contract **v1.3**; gameplay, tuning, kho và JSONL theo v1.2.

## Điểm mới qua bốn phase

- **Phase 1 (v1.0):** lõi buổi sáng Lặn & Hái (bơi, oxy/ngạt, Máu/ngất, hái, bắt cá, cập bến) và buổi tối Mở Quán (khách, giữ chỗ, bếp, phục vụ, boa, uy tín); bàn giao kho hai tiến trình; HUD tối thiểu.
- **Phase 2 (v1.1):** số chuẩn; cá bơi/sinh theo seed; Cá Sấu Năm Chèo; 2 bếp, 4 bàn, 6 món; kế hoạch ngày D1–D5; Shop nâng cấp oxy/Máu; `--mode day`; pause; menu, DayIntro, EveningIntro, DayResult, Summary.
- **Phase 3 (v1.2, breaking):** kho cá thể `{id, kind, fresh}`; độ tươi hao ở giỏ/kho, hàng ươn; giữ chỗ theo id; giá theo độ tươi; HUD độ tươi.
- **Phase 4 (v1.3):** benchmark có render `bench_cmd`, soak headless `soak_cmd`, cảnh báo dễ nhận biết và chế độ tương phản cao, đóng gói chạy từ clone sạch.

## Cách chạy

Yêu cầu: Python ≥ 3.10 (chỉ thư viện chuẩn), một trình duyệt; bench cần Chrome/Chromium/Edge; test UI cần Node (tùy chọn).

```bash
git clone https://github.com/khanhvnm/K5-L3B-LAB-Day12-AI-SDLC-Rua.git
cd K5-L3B-LAB-Day12-AI-SDLC-Rua
python3 -m chonoi.live --mode day --days 5      # mở địa chỉ in ra
```

- Điều khiển: WASD/mũi tên di chuyển, E tương tác (cập bến, hái, bếp, bàn), Space bắt cá, Esc/P tạm dừng, R chơi lại.
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out out.jsonl`
- Benchmark: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json`
- Soak: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`

Bản đóng gói đính kèm: `chonoi-v1.0.0.zip` (mã nguồn tại commit phát hành, giải nén rồi chạy lệnh trên từ thư mục gốc).

## Giới hạn đã biết

- Không làm mở rộng của ticket (dòng lũ, khách đặt trước, leaderboard, phụ đề SFX, …) — nhóm 3 người.
- Benchmark cần trình duyệt họ Chromium; không có thì trả mã 1. Số đo headless không khóa vsync (xem `docs/proof/phase-4/bench.md`).
- Quán làm tròn `fresh` của fixture tới bội 1/240; fixture không biểu diễn chính xác có thể lệch nhánh ngưỡng ươn 1 tick (`docs/clarify.md` P3-05).
- JSONL làm tròn số thực 3 chữ số; file kho ghi đầy đủ.
- Chưa có lượt chơi tay đầy đủ 5 Ngày được ghi lại trong bằng chứng ngoài demo.

Chi tiết: [CHANGELOG.md](../CHANGELOG.md), ma trận kiểm chứng `docs/verification/phase-1..4.md`.
