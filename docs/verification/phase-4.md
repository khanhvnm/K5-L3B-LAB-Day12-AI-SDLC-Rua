# Ma trận truy vết Phase 4 (đang cập nhật)

Mã AC-P4-xx định nghĩa trong [kế hoạch Phase 4](../plan/phase-4.md). Chỉ ghi kết quả đã chạy; commit bàn giao là commit gắn tag `phase-4` / Release `v1.0.0`.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 — `contract_version:"1.3"`, `bench_cmd`, `soak_cmd`; gameplay v1.2 | `test_bench.py::Manifest`; full suite không đổi luật | `game.contract.json` | Đạt (Khánh) |
| AC-P4-02 — `bench_cmd` tạo `bench.json` 5 trường, công thức đúng | `test_bench.py::Metrics`, `::Cli` (gồm chạy render thật 1 s) | [bench.md](../proof/phase-4/bench.md) | Đạt |
| AC-P4-03 — artifact bench (seed 42, 30 s, 1280×720) | `python3 -m chonoi.bench --seed 42 --duration 30` | [bench.json](../proof/phase-4/bench.json): avg 1633 FPS, 1% low 47 FPS, load 674 ms | Đạt (máy thử Windows; cần chạy lại trên commit bàn giao) |
| AC-P4-04 — soak 10 Ngày | Lát Trà | — | Chưa |
| AC-P4-05 — 3 cảnh báo + tương phản cao | Node 16/16; Chrome fixture 3 cảnh, H/storage | [day-ui.md](../proof/phase-4/day-ui.md), ảnh `contrast-*.png` | Đạt smoke tự động; chờ người chơi tay xác nhận |
| AC-P4-06 — clone sạch ≤ 3 lệnh | Clone remote main + smoke HTTP, kiểm riêng overlay | [clean-clone.md](../proof/phase-4/clean-clone.md) | Đạt trên Windows; chạy lại sau merge; Linux/macOS chưa kiểm |
| AC-P4-07 — README, CHANGELOG theo phase, CREDITS, LICENSE | CHANGELOG có phase-1..4 (Khánh); README/LICENSE/CREDITS hoàn tất (Thành) | `README.md`, `LICENSE`, `CREDITS.md`, `CHANGELOG.md` | Đạt ở nhánh bàn giao |
| AC-P4-08 — regression P1–P3 | Full suite **168/168 pass**, Node UI 16/16 trên `p4/day-ui` | [day-ui.md](../proof/phase-4/day-ui.md) | Đạt (chạy lại trên commit bàn giao) |
| AC-P4-09 — tag `phase-4` + Release `v1.0.0` cùng commit, release notes, zip | [release notes](../release-notes-v1.0.0.md) (nháp) | — | Chưa |
| AC-P4-10 — retro + phản tư cá nhân | Trà điều phối; mỗi người tự viết | — | Chưa |
