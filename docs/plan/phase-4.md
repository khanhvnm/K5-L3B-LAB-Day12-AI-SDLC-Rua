# Kế hoạch Phase 4 — TICKET-04 "Phát hành v1.0.0" (Test Contract v1.3)

**Mục tiêu:** Trước 3:00, `contract_version:"1.3"` với `bench_cmd` + `soak_cmd`; bench có render tạo `bench.json`; soak 10 Ngày; ba cảnh báo + chế độ tương phản cao; clone sạch chạy ≤ 3 lệnh; retro + phản tư cá nhân; tag `phase-4` và GitHub Release `v1.0.0` **cùng một commit** trên `main`.

**Phạm vi:** chỉ lõi. Nhóm 3 người **không làm mở rộng** (leaderboard, phụ đề SFX). Gameplay/tuning/kho/JSONL giữ nguyên v1.2.

## Quyết định kỹ thuật (chốt phút 0–3)

- **Bench có render = trình duyệt thật.** UI hiện là Canvas trong `chonoi/web/index.html` phục vụ bởi `chonoi.live`. `chonoi/bench.py` sẽ: dựng `LiveGame` mode `gather` seed 42 (Út Sen đứng yên ở bến, cá bơi, Cá Sấu, độ tươi mặc định), mở **Chrome/Edge/Chromium headless** cửa sổ 1280×720 vào trang `?bench=<duration>`; trang đo thời gian từng khung bằng `requestAnimationFrame` (làm nóng 3 s, đo N s) rồi `POST /bench`; Python tính `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms` (từ lúc khởi chạy tới khung đầu của cảnh đo) và ghi `bench.json`.
  - Tìm trình duyệt theo `CHONOI_BROWSER` → `chromium`/`google-chrome`/`chrome`/Edge trong PATH và đường dẫn chuẩn macOS/Linux/Windows.
  - Headless Chrome có thể giới hạn rAF; dùng cờ `--disable-gpu-vsync --disable-frame-rate-limit` và ghi rõ trong proof đây là số đo trên máy nào.
  - **Không có trình duyệt** → mã 1 kèm thông báo rõ (không bịa số). Ghi giới hạn trong release notes.
- **Soak:** `chonoi/soak.py` chạy `DaySession` 10 Ngày trong một tiến trình với **bot tất định** (không scenario): sáng bơi theo kịch bản cố định rồi về bến, tối đứng yên/thao tác tối thiểu, Shop `shop_done` ngay. Kế hoạch D1–D5 lặp ở Ngày 6–10 → cần `day.py` nhận `days` tới 10 cho soak (chỉ nội bộ, CLI `--days` của headless giữ [1,5]) và `plan_for_day` lấy `(day-1) % 5`. Mỗi Shop đóng ghi `results[] {day, earned, reputation, score}`; bắt mọi exception → `crashes`. `duration_s` là thời gian thực (bỏ qua khi so).
- **Cảnh báo:** đã có chữ "Thủy quái!" + viền tím, "Hết hơi!", kiên nhẫn đổi màu < 25%. Bổ sung: **"Sắp hết hơi!"** khi oxy < 25% (chữ + biểu tượng, không chỉ màu), **biểu tượng + chữ "Sắp giận!"** cạnh bàn khi kiên nhẫn < 25%, biểu tượng ⚠ cho thủy quái. Thêm **chế độ tương phản cao** (phím `H` + nút trong menu/pause, nhớ bằng `localStorage`, có thể bật bằng `?contrast=high`): nền đen, chữ trắng/vàng, viền dày, không dựa vào màu.
- **Đóng gói:** chỉ cần Python 3.10+ (stdlib) và một trình duyệt. Ba lệnh: `git clone … && cd …` / `python3 -m chonoi.live --mode day --days 5`. Bản đóng gói Release: `chonoi-v1.0.0.zip` (`git archive` của commit tag) đính kèm Release.

## Mã tiêu chí (AC-P4)

| AC | Nội dung |
|---|---|
| AC-P4-01 | `contract_version:"1.3"`, `bench_cmd`, `soak_cmd` ở gốc manifest; gameplay/JSONL v1.2 không đổi |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json` tạo đúng 5 trường; công thức `avg_fps`, `p1_low_fps` đúng (test đơn vị với dãy frame giả) |
| AC-P4-03 | Artifact bench từ commit nộp trong `docs/proof/phase-4/` (báo cáo mốc 60/30 FPS, load ≤ 10 s) |
| AC-P4-04 | `soak_cmd --seed 7 --days 10 --out soak.json`: `days_completed = days`, `crashes = 0`, `results` đủ 10 mục, hai lần chạy trùng trường gameplay |
| AC-P4-05 | Ba cảnh báo có chữ/biểu tượng; chế độ tương phản cao; chơi thử cả ba ở tương phản cao (ảnh chụp) |
| AC-P4-06 | Clone sạch → chạy UI ≤ 3 lệnh theo README (thử trong thư mục tạm, ghi log) |
| AC-P4-07 | README: yêu cầu môi trường, điều khiển, test, headless, bench, soak; CHANGELOG theo phase; CREDITS + LICENSE |
| AC-P4-08 | Regression P1–P3 đạt trên commit bàn giao |
| AC-P4-09 | Tag `phase-4` + Release `v1.0.0` cùng commit trên `main`, có release notes và bản đóng gói |
| AC-P4-10 | Retro rà hành động P2/P3, một lỗi AI và cách xác minh; `docs/members/<handle>.md` ≤ 200 từ cho cả 3 người |

## Phân việc

| Vai / lát | Việc | File | Test / bằng chứng | Phụ trách |
|---|---|---|---|---|
| **Bench/QA** | `chonoi/bench.py` + chế độ `?bench` trong trang; manifest 1.3; chạy bench, lưu `bench.json`; regression; `docs/verification/phase-4.md` | `chonoi/bench.py`, `chonoi/live.py` (route `/bench`), `chonoi/web/index.html` (đo rAF), `game.contract.json` | `tests/test_bench.py` (công thức p1-low, schema bench.json, lỗi khi không có trình duyệt); `docs/proof/phase-4/bench.json` | **Khánh** |
| **Soak** | `chonoi/soak.py`, bot tất định, lặp kế hoạch Ngày 6–10 | `chonoi/soak.py`, `chonoi/day.py` (`(day-1) % 5`, cho phép tới 10 Ngày nội bộ), `chonoi/dayplan.py` | `tests/test_soak.py` (10 Ngày đạt, tất định, id cá thể tăng xuyên Ngày); `docs/proof/phase-4/soak.json` | **Trà** |
| **Cảnh báo + tương phản** | "Sắp hết hơi!", "Sắp giận!", biểu tượng ⚠, chế độ tương phản cao; chơi thử 3 cảnh báo ở tương phản cao | `chonoi/web/index.html` | `tests/test_ui.js` (ngưỡng hiện cảnh báo, chế độ tương phản); ảnh chụp `docs/proof/phase-4/contrast-*.png` | **Thành** |
| **Đóng gói** | Thử clone sạch ≤ 3 lệnh (macOS/Linux, ghi lại Windows), README "Chạy nhanh", LICENSE (MIT), rà CREDITS, `chonoi-v1.0.0.zip` | `README.md`, `LICENSE`, `CREDITS.md` | `docs/proof/phase-4/clean-clone.md` | **Thành** (sau cảnh báo) |
| **Release/Integrator** | CHANGELOG theo phase, release notes, kiểm commit bàn giao, tag `phase-4`, GitHub Release `v1.0.0` + đính zip | `CHANGELOG.md`, `docs/release-notes-v1.0.0.md` | Tag + Release cùng commit | **Khánh** |
| **Điều phối retro** | Rà hành động P2 ("PR nhỏ trước phút 25", Thành commit nhỏ) và P3 ("PR schema merge trước"); tổng hợp bằng chứng đóng góp (`git shortlog`) | `docs/retro.md` | — | **Trà** |
| **Phản tư cá nhân** | Mỗi người tự viết ≤ 200 từ: phần mình làm, đã giúp ai, AI sai ở đâu, bài học, dẫn commit | `docs/members/<handle>.md` | — | **Mỗi người tự viết** |

Người dự phòng: Trà đỡ bench nếu Khánh vướng trình duyệt headless; Khánh đỡ soak; Trà kiểm UI tương phản.

## Lịch theo phút

| Phút | Việc | Ai |
|---|---|---|
| 0–3 | Chốt quyết định trên, manifest 1.3 (Khánh merge sớm để mọi nhánh cùng nền) | Khánh |
| 3–15 | Song song: bench (Khánh), soak (Trà), cảnh báo + tương phản (Thành) | |
| 15–20 | Thành thử clone sạch + README; Khánh chạy bench trên `main`, regression; Trà soak 10 Ngày | |
| 20 | Standup 2 phút; điều người đã xong sang lát trễ | Khánh |
| 20–25 | Retro (Trà điều phối) + mỗi người viết `docs/members/<handle>.md`; Khánh CHANGELOG, release notes, verification | Cả nhóm |
| 25–28 | Merge cuối, chạy lại full suite + bench + soak trên commit bàn giao, cập nhật số trong verification | Khánh |
| 28–30 | Tag `phase-4`, tạo Release `v1.0.0` từ tag, đính zip; kiểm cả hai trỏ cùng commit | Khánh |

## Quy ước

- Nhánh `p4/<lát>`, PR vào `main`. **PR manifest 1.3 merge trước** mọi PR khác (hành động retro P3).
- Không đổi gameplay/tuning/kho/JSONL; mọi thứ mới (bench, tương phản) không ảnh hưởng headless.
- Mỗi người ≥ 1 commit có nội dung trong phase này bằng tài khoản của mình; phản tư cá nhân do chính người đó viết.

## Câu hỏi ghi `docs/clarify.md`

1. Máy chấm có trình duyệt Chromium không? Nếu không, bench trả mã 1 — chấp nhận? (Hỏi Anh Năm.)
2. Bot soak buổi tối có cần phục vụ khách để `earned` > 0, hay chỉ cần đi qua đủ pha?
3. Kế hoạch Ngày 6–10 lặp D1–D5: M2 (từ Ngày 3) vẫn có mặt ở Ngày 6–7 — giả định có (`from_day ≤ day`).

## Rủi ro

- **Bench headless** phụ thuộc trình duyệt và có thể bị khóa 60 FPS/vsync → ghi số thật kèm máy đo; đây là phần rủi ro cao nhất, làm đầu tiên.
- Release cần quyền tạo Release trên GitHub; máy này không có `gh` → tạo trên web (Releases → Draft new release → chọn tag `phase-4`... đặt tên `v1.0.0`) hoặc cài `gh`. **Tag `v1.0.0` và `phase-4` phải trỏ cùng commit.**
- Thời gian 30 phút: cắt hẳn mở rộng; nếu trễ, ưu tiên manifest + bench + soak + tag/Release trước, retro/phản tư viết song song.
