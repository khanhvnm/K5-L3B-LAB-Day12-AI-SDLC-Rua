# Bằng chứng benchmark có render — TICKET-04, contract v1.3

Lệnh (khai ở `bench_cmd` của `game.contract.json`):

```bash
python3 -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json
```

## Cách đo

- Cảnh: buổi sáng lõi (`LiveGame` mode `gather`, preset chuẩn v1.2: độ tươi, 8 đàn cá bơi/sinh, Cá Sấu M1, HUD và hiệu ứng mặc định), seed 42, không input — Út Sen đứng yên ở bến xuất phát `[2,0]`.
- Render: trang thật `chonoi/web/index.html` (Canvas 2D) trong Google Chrome headless, `--window-size=1280,720`, chế độ `?bench=30&warmup=3`. Làm nóng 3 s tính từ khung đầu tiên có snapshot, sau đó ghi thời gian từng khung bằng `requestAnimationFrame` trong 30 s.
- Headless chạy **không khóa vsync** (`--disable-gpu-vsync --disable-frame-rate-limit`) nên `avg_fps` đo khả năng render tối đa, không phải 60 Hz của màn hình; bản chơi thường trên trình duyệt có vsync bị giới hạn theo tần số màn hình.
- Python tính theo ticket: `avg_fps = frames / measured_s`; `p1_low_fps` = nghịch đảo thời gian trung bình (giây) của `max(1, ceil(0.01 × frames))` khung chậm nhất; `load_ms` = từ lúc khởi chạy lệnh tới khung đầu tiên của cảnh đo.

## Kết quả (Windows 11, AMD 16 luồng, Chrome 157.0.8103.80)

| Lần | avg_fps | p1_low_fps | frames | measured_s | load_ms |
|---|---|---|---|---|---|
| [bench.json](bench.json) | 1633.19 | 47.29 | 48 996 | 30.0 | 674 |
| [bench-run2.json](bench-run2.json) | 1798.59 | 52.61 | 53 958 | 30.0 | 636 |

So với mốc báo cáo: avg ≥ 60 FPS **đạt**, 1% low ≥ 30 FPS **đạt**, load ≤ 10 s **đạt** (≈ 0,65 s).

1% low thấp hơn nhiều so với trung bình vì khi không khóa khung, các khung bị chen bởi poll `/state` (50 ms) hoặc GC nổi rõ; vẫn trên ngưỡng 30.

## Kiểm thử

`tests/test_bench.py` (7 test): manifest 1.3 khai `bench_cmd`/`soak_cmd`; công thức `p1_low_fps` với dãy khung giả (ceil 1%, tối thiểu 1 khung); không có khung → lỗi; không tìm thấy trình duyệt → mã 1, không tạo file; tham số sai → mã 2; chạy thật 1 s qua `bench_cmd` khi máy có trình duyệt (bỏ qua nếu không), kiểm 5 trường và không để lại file tạm.

## Yêu cầu và giới hạn

- Cần một trình duyệt họ Chromium (Chrome, Chromium, Edge). Tìm theo `CHONOI_BROWSER`, rồi `chromium`, `chromium-browser`, `google-chrome(-stable)`, `chrome`, `microsoft-edge(-stable)`, `msedge` trong PATH và đường dẫn chuẩn macOS/Windows. Chạy root (container) tự thêm `--no-sandbox`.
- Không có trình duyệt → mã thoát 1, thông báo rõ, **không ghi số giả**.
