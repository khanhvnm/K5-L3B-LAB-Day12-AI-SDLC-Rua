# Ma trận truy vết Phase 4

Mã AC-P4-xx định nghĩa trong [kế hoạch Phase 4](../plan/phase-4.md). Kết quả chạy trên `main@f186618` (đã gộp PR #11 soak, #12 bench/manifest, #13 cảnh báo/đóng gói); commit bàn giao là commit merge PR `p4/release` — chỉ đổi tài liệu và artifact bench, không đổi code. Tag `phase-4` và Release `v1.0.0` trỏ vào commit đó.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 — `contract_version:"1.3"`, `bench_cmd`, `soak_cmd`; gameplay v1.2 | `test_bench.py::Manifest`; full suite không đổi luật | `game.contract.json` | Đạt |
| AC-P4-02 — `bench_cmd` tạo `bench.json` 5 trường, công thức đúng | `test_bench.py` (7 test, gồm render thật 1 s) | [bench.md](../proof/phase-4/bench.md) | Đạt |
| AC-P4-03 — artifact bench seed 42, 30 s, 1280×720 | `python3 -m chonoi.bench --seed 42 --duration 30` trên `f186618`, hai lần | [bench.json](../proof/phase-4/bench.json): avg 1728,5 FPS, 1% low 50,7 FPS, load 632 ms; [bench-run2.json](../proof/phase-4/bench-run2.json) | Đạt (≥ 60 / ≥ 30 / ≤ 10 s) |
| AC-P4-04 — soak 10 Ngày | `python3 -m chonoi.soak --seed 7 --days 10` hai lần trên `f186618`: `days_completed` 10, `crashes` 0, 10 `results`, trùng nhau và trùng proof (bỏ `duration_s`); `test_soak.py` (7 test) | [soak.md](../proof/phase-4/soak.md), [soak.json](../proof/phase-4/soak.json) | Đạt |
| AC-P4-05 — 3 cảnh báo + tương phản cao | Node 16/16; Chrome fixture 3 cảnh ở tương phản cao | [day-ui.md](../proof/phase-4/day-ui.md), [contrast-monster.png](../proof/phase-4/contrast-monster.png), [contrast-oxygen.png](../proof/phase-4/contrast-oxygen.png), [contrast-patience.png](../proof/phase-4/contrast-patience.png) | Đạt bằng smoke tự động; chơi tay trong demo |
| AC-P4-06 — clone sạch ≤ 3 lệnh | `python3 tools/proof_clean_clone.py` trên `origin/main@f186618`: `CLEAN MAIN f186618… HTTP 200: Canvas, menu Ngày 1, POST /advance -> day_intro; không cài pip/npm`, thư mục tạm tự dọn | [clean-clone.md](../proof/phase-4/clean-clone.md) | Đạt trên Windows; Linux/macOS chưa kiểm (ghi trong release notes) |
| AC-P4-07 — README, CHANGELOG theo phase, CREDITS, LICENSE | README "Chạy nhanh", lệnh test/headless/bench/soak; CHANGELOG phase-1..4; `LICENSE` MIT; `CREDITS.md` không có asset ngoài | `README.md`, `CHANGELOG.md`, `LICENSE`, `CREDITS.md` | Đạt |
| AC-P4-08 — regression P1–P3 | Full suite **168/168 pass** (81 s), Node UI **16/16**; headless `day --days 1 --ticks 22200` kết thúc `days_complete` | — | Đạt |
| AC-P4-09 — tag `phase-4` + Release `v1.0.0` cùng commit, release notes, ZIP | [release notes](../release-notes-v1.0.0.md); ZIP `git archive` từ tag | — | Chờ gắn tag / tạo Release |
| AC-P4-10 — retro rà hành động P2/P3, lỗi AI; phản tư ≤ 200 từ mỗi người | [retro](../retro.md) (Trà điều phối, Khánh điền hành động P3); `docs/members/*.md` | — | Một phần: `khanhvnm.md` 169 từ (nháp, Khánh soát); `phungtr.md` 216 từ (cần rút gọn); `thanhtey1234.md` còn chỗ "do Thành tự viết" |

## Đánh giá DoD

- **Đạt:** contract 1.3, bench, soak, cảnh báo và tương phản, clone sạch ≤ 3 lệnh, regression, CHANGELOG, LICENSE/CREDITS.
- **Còn trước giờ chót:** Trà rút phản tư ≤ 200 từ, Thành viết phản tư; gắn tag `phase-4`, ZIP, Release `v1.0.0` cùng commit.
- **Không làm mở rộng** (leaderboard, phụ đề SFX); manifest không khai `extensions`.
