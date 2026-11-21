# Bằng chứng UI Phase 1 — Phạm Duy Thành

Ngày kiểm tra ban đầu: 2026-11-21. Tích hợp vào `main` qua PR #3 (`e8c9541`); trạng thái hiện tại đã được rà lại trên `main` tại `fde0040`.

## Phạm vi

- Khôi phục gather.py và quan.py về main; xóa test/proof luật do agent tạo trước khi nhận phân công. Không đổi luật, contract hoặc tuning.
- Canvas đọc snapshot, gửi input qua API hiện có; bổ sung tên món, trạng thái bếp/khách, HUD, kết quả và thông báo sự kiện theo hợp đồng.
- Sửa giữ nhiều phím cùng hướng, mất focus, catch chỉ trong gather, kiểm HTTP status và thứ tự restart/input.
- Test tồn tại lâu dài: `tests/test_ui.js`, `tests/test_ui.py`. Không thêm dependency hoặc thư mục sản phẩm mới.

## Lệnh và kết quả

```powershell
node --test tests/test_ui.js
$env:PYTHONPATH='tests;.'
python3 -m unittest discover -s tests -v
git diff --check
```

- Node: 7/7 pass. Bao gồm phím trùng hướng/blur, trục quán/catch, tên món dạng object, dữ liệu sự kiện yield/free/required và chống lặp, thiếu trường tùy chọn, HTTP lỗi, restart chờ input đang gửi và bỏ hàng đợi cũ.
- Python: 33/33 pass, bao gồm wrapper chạy 7 test Node; không cộng hai con số thành 40 test độc lập. Nếu máy thiếu Node, wrapper báo skip và phải chạy Node riêng trên máy có runtime.
- Smoke hai tiến trình gather → kho → quan: pass qua `test_inv_01_gather_writes_inventory_quan_reads_it` trong bộ test hiện có, dùng Workdir/TemporaryDirectory tự dọn.
- `git diff --check`: không lỗi.

## Kiểm tra bằng Chrome headless thật

- Khởi động LiveServer cho gather và quan trên cổng ngẫu nhiên; chụp và xem ảnh ở 800×600 và 1280×720.
- HUD/trạng thái ban đầu, vùng chơi và hướng dẫn phím nằm trong màn hình; bếp hiển thị nhãn tiếng Việt.
- Ảnh và hồ sơ Chrome dùng thư mục tạm có tiền tố `chonoi-ui-` trong thư mục temp hệ điều hành; đã xóa sau khi xem ảnh. File ghi đường dẫn tạm trong repo cũng đã xóa.
- LiveServer luôn dừng trong finally. Không giữ tiến trình game nền.

## Giới hạn và bàn giao

- Chủ module chưa tích hợp luật: không tuyên bố đã chơi hoàn chỉnh thu hoạch/nấu/phục vụ. Các trạng thái nâng cao của UI hiện được kiểm bằng fixture JavaScript, không phải bằng gameplay thật.
- Hợp đồng mới dùng order_id/base_price/yield; UI không áp dụng giả định customer_id/amount của code luật cũ. Snapshot món object có dish_id hoặc chuỗi được hỗ trợ; dạng khác hiển thị chưa có dữ liệu, cần xác nhận khi tích hợp.
- Không đánh dấu toàn bộ Phase 1 đạt hoặc tự đặt mã AC khi repo chưa có PRD đầy đủ.
- Danh sách TEAM có 3 người đã được chấp thuận theo kế hoạch nhóm; script check_team vẫn yêu cầu 4–6. Đây là việc của Integrator, không sửa checker trong nhánh UI.
- Quy tắc thông báo thư mục và dọn thư mục tạm được ghi trong AGENTS.md repo và hướng dẫn cá nhân ~/.codex/AGENTS.md.

## Rà lại sau khi tích hợp vào main

- Chạy lại `node --test tests/test_ui.js` trên `main`: **7/7 pass**.
- Đã kiểm tra các thay đổi được tích hợp ở `chonoi/web/index.html`; bộ test bao phủ xử lý phím, hai trục mode quán/gather, hiển thị tên món và thông báo, HUD khi snapshot thiếu trường tùy chọn, lỗi HTTP và thứ tự restart/input.
- Chưa chạy lại toàn bộ Python unittest trong môi trường rà soát này vì PowerShell không tìm thấy lệnh `python3`. Kết quả toàn bộ 61/61 được ghi trước khi UI merge; cần chạy lại sau merge trên máy có Python.
- Smoke Chrome headless ở hai kích thước cho cả hai mode đã được ghi ở phần trên. Đây là kiểm tra bố cục/hiển thị ban đầu; không thay thế lượt chơi tay qua toàn bộ gameplay.
