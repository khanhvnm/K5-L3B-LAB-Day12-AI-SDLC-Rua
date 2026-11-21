# Chạy sạch — Phase 4 / Thành

2026-11-21, Windows. Công cụ tái lập: `python3 tools/proof_clean_clone.py` (stdlib + Git). Thư mục `.p4-day-ui-check-*` nằm trong repo, được TemporaryDirectory tự dọn sau khi server dừng, kể cả lỗi.

Ba lệnh cho người chơi (không cài pip/npm):

```sh
git clone https://github.com/khanhvnm/K5-L3B-LAB-Day12-AI-SDLC-Rua.git
cd K5-L3B-LAB-Day12-AI-SDLC-Rua
python3 -m chonoi.live --mode day --days 5
```

Log đã chạy qua công cụ (dùng `--port 0` tránh xung đột; đúng executable Python đang chạy):

```text
CLEAN MAIN f2b0d1072ef1254c6652b74165518fcb0da2d438 HTTP 200: Canvas, menu Ngày 1, POST /advance -> day_intro; không cài pip/npm.
HANDOFF OVERLAY HTTP 200: Canvas, menu Ngày 1, POST /advance -> day_intro; không cài pip/npm.
TEMP cleaned on exit
```

Lượt đầu: clone `origin/main` trực tiếp, xác nhận `git status --porcelain` rỗng trước chạy. Lượt sau: chép riêng HTML/README/LICENSE/CREDITS chưa commit vào clone rồi chạy lại; lượt này **không phải clone sạch của commit phát hành**. Integrator chạy lại sau merge/tag. Linux/macOS chưa có máy để kiểm, không nhận là đã chạy trên hai nền tảng đó.

Windows nếu không có `python3` dùng `python`/`py -3`. Game chỉ cần Python và trình duyệt; Node/Chrome headless phục vụ kiểm chứng không phải dependency của lượt chơi thông thường.

ZIP chính thức phải tạo bằng `git archive` từ `phase-4` sau tích hợp (lệnh README). Bản `chonoi-v1.0.0-preview.zip` ở gốc workspace là snapshot file bàn giao để thử giải nén/chạy trước commit, không thay thế artifact Release từ tag.
