# Phase 4 — Thành / day-ui

Ngày kiểm: 2026-11-21. Nhánh `p4/day-ui`, nền `origin/main` = `f2b0d1072ef1254c6652b74165518fcb0da2d438` (fetch trước khi sửa, HEAD trùng main). Thay đổi chưa commit; integrator phải kiểm lại trên commit/tag bàn giao.

## Phạm vi

- `chonoi/web/index.html`: sửa starter để thêm cảnh báo chữ/⚠ và tương phản cao (H, nút menu/pause/Shop, localStorage, URL). Không đổi gameplay, kho, tuning, JSONL, bench hay soak.
- Oxy < 25% mức tối đa đang áp dụng: `⚠ Sắp hết hơi!`; bằng 0: `Hết hơi!`. Khách chưa ăn và kiên nhẫn < 25%: `⚠ Sắp giận!` cạnh bàn. Thủy quái giữ điều kiện vùng nguy hiểm từ snapshot và thêm ⚠; viền vàng dày khi tương phản cao.
- Nền đen, chữ trắng có viền đen, vật thể trắng/vàng, thanh có viền dày. Chọn tương phản là trạng thái client; H không gửi input gameplay hoặc chuyển DayIntro.

## Kiểm chứng đã chạy

| Lệnh | Kết quả |
|---|---|
| `node --test tests/test_ui.js` | 16/16 đạt; gồm biên 25%, oxy nâng cấp, khách đang ăn, quái xa, H/nút, storage bị chặn |
| `set PYTHONPATH=tests;.&& python3 -m unittest discover -s tests -v` (cmd) | Lượt cuối 168/168 đạt, 38.704 s; gồm regression P1–P3, bench Chrome thật 1 s, soak 10 ngày và Node UI; [log](day-ui-tests.txt) |
| `python3 tools/proof_day_ui.py` | 3 ảnh Chrome thật 1280×720; kiểm chữ được Canvas vẽ, pixel nền đen, H hai lần và localStorage |
| `python3 tools/proof_clean_clone.py` | clone remote main sạch + kiểm riêng overlay bàn giao đều chạy UI HTTP thành công; xem [clean-clone](clean-clone.md) |

Sau khi hoàn thiện bảng màu Canvas, đã chạy lại full suite 168/168, Node 16/16 và proof Chrome 3/3.

Ảnh dùng fixture được `load_scenario` kiểm hợp lệ, chạy một tick mô phỏng thật, giữ tick 1 để tái lập. Không sửa snapshot bằng JS. Đây là **smoke tự động qua Chrome**, không nhận là người chơi tay đã duyệt.

| Ảnh | Trạng thái |
|---|---|
| [contrast-oxygen.png](contrast-oxygen.png) | Oxy 399/1800 tick, vị trí [40,10], không quái |
| [contrast-monster.png](contrast-monster.png) | Vị trí [55,24], trong vùng M1 |
| [contrast-patience.png](contrast-patience.png) | T1 chờ món, kiên nhẫn 799/3600 tick |

Môi trường: Windows, Python qua `python3`, Node có WebSocket, Google Chrome. Profile/clone tạm tự dọn cả khi lỗi. Không đo lại bench 30 s/soak artifact thay chủ module.

## Rà lỗi AI và bàn giao

Rà ảnh phát hiện lần sửa bằng lệnh Python chưa ghi bảng màu Canvas như dự kiến: chữ/DOM đã đổi nhưng nước/sàn còn màu cũ. Sửa trực tiếp bằng patch, chụp lại và bổ sung kiểm pixel nền + kiểm chữ Canvas trong công cụ proof. Hai lần chọn pixel kiểm nhầm viền cảnh báo/viền sàn; chuyển sang khoảng trống (100,600), cả ba cảnh đạt. Không đổi luật để làm test xanh.

README, LICENSE (MIT), CREDITS và hướng dẫn ZIP đã bổ sung. Phản tư cá nhân để Thành tự viết; tag/Release/ZIP chính thức thuộc integrator, tạo sau merge bằng lệnh trong README.

`python3 tools/package_preview.py`: tạo ZIP preview, kiểm CRC và giải nén/chạy UI (menu → DayIntro), thành công. File `chonoi-v1.0.0-preview.zip` ở gốc workspace để bàn giao; không phải ZIP phát hành từ tag. Thư mục giải nén tạm được dọn.
