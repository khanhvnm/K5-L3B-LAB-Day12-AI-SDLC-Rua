# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Chạy nhanh (≤ 3 lệnh)

Cần **Python 3.10+** (chỉ thư viện chuẩn), Git để clone, và trình duyệt hiện đại để chơi. Không cần pip/npm install. Trên Windows nếu không có `python3`, thay bằng `python` hoặc `py -3`.

```bash
git clone https://github.com/khanhvnm/K5-L3B-LAB-Day12-AI-SDLC-Rua.git
cd K5-L3B-LAB-Day12-AI-SDLC-Rua
python3 -m chonoi.live --mode day --days 5
```

Mở địa chỉ HTTP in ở terminal (mặc định `http://127.0.0.1:8000/`), chọn **Chơi**. Ctrl+C tại terminal để dừng. Nếu cổng bận, thêm `--port 0`. Bản ZIP: giải nén, mở terminal tại thư mục chứa `game.contract.json`, chạy lệnh cuối. [Bằng chứng Windows](docs/proof/phase-4/clean-clone.md).

| Điều khiển | Tác dụng |
|---|---|
| WASD / mũi tên | Bơi buổi sáng, đi lại trong quán |
| E | Hái/cập bến; tương tác bếp/bàn |
| Space | Bắt cá khi lặn |
| Esc / P | Tạm dừng / tiếp tục |
| H | Bật/tắt tương phản cao, nhớ trên trình duyệt |
| R | Chơi lại |
| Tab, Enter | Chọn/kích hoạt nút menu và Shop |

Tương phản cao cũng có nút trong menu/pause/Shop hoặc mở `?contrast=high`. Nền đen, chữ trắng, vật thể vàng/trắng và viền dày; các cảnh báo có chữ/biểu tượng: **⚠ Sắp hết hơi!** khi oxy < 25%, **⚠ Sắp giận!** khi khách chờ còn < 25% kiên nhẫn, **⚠ Thủy quái!** khi ở vùng nguy hiểm. Oxy bằng 0 hiển thị **Hết hơi!**. Bảng độ tươi ghi số và nhãn **Ươn**; không chỉ dựa vào màu.

## Kiểm thử, headless và hiệu năng

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
node --test tests/test_ui.js
python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out day.jsonl
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

PowerShell dùng `$env:PYTHONPATH='tests;.'; python3 -m unittest discover -s tests -v`; cmd dùng `set PYTHONPATH=tests;.&& python3 -m unittest discover -s tests -v`. Test UI cần Node.js; unittest tự chạy test này nếu có Node, thiếu sẽ báo skip. Gameplay/UI không cần Node.

Bench cần Chrome/Chromium/Edge; tự tìm trình duyệt hoặc đặt `CHONOI_BROWSER` tới executable. Không tìm thấy thì trả mã 1, không tạo số liệu giả. Bench render thật 1280×720, làm nóng 3 giây; FPS phụ thuộc máy/cờ headless, xem [proof](docs/proof/phase-4/bench.md). Soak dùng bot tất định qua 10 ngày; CLI chơi/headless vẫn giới hạn 1–5 ngày. Chế độ tương phản chỉ ở client, không ảnh hưởng headless/JSONL. Chi tiết contract và starter: [STARTER](docs/STARTER.md).

## Đóng gói bàn giao

Integrator chạy trên commit phát hành sau khi tích hợp và gắn tag:

```bash
git archive --format=zip --prefix=chonoi-v1.0.0/ --output=chonoi-v1.0.0.zip phase-4
```

Đính ZIP vào GitHub Release `v1.0.0`; `phase-4` và tag phát hành phải cùng commit trên `main`. Không tạo ZIP từ nhánh chưa commit để tránh bỏ sót thay đổi. Giấy phép [MIT](LICENSE); nguồn tài sản và công cụ: [CREDITS](CREDITS.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Sáng tạo và mở rộng của nhóm Rua

- **Mở rộng (Ticket-02 mục 3):** chưa làm mục nào — nhóm 3 người không bắt buộc; `game.contract.json` không khai `extensions`.
- **Sáng tạo của nhóm:** chưa có. Mọi bổ sung sau này phải tắt ở headless và kèm bằng chứng lõi vẫn đúng.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
