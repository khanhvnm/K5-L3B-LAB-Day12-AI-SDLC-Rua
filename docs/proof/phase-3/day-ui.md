# Phase 3 — Day + HUD (lát D)

Nhánh: `p3/day-ui`, nền `main@e28b544`. Phạm vi implementation hiện tại: giữ kho cá thể qua Day/Shop, cấp id mới cho mẫu hold từ ngày 2, tính kho khả dụng từ id giữ chỗ và hiển thị độ tươi trong HUD.

## Kiểm thử

- `PYTHONPATH=tests;. python3 -m unittest tests.test_day tests.test_shop_rules tests.test_live -v`: **21/21 pass**.
- `node --test tests/test_ui.js`: **12/12 pass**.
- `PYTHONPATH=tests;. python3 -m unittest discover -s tests -q`: **126/126 pass**.
- `git diff --check`: pass.

Test `test_v12_handoff_pause_shop_and_ids_with_individual_inventory` dùng Gather/Quan giả lập trong test để kiểm snapshot bàn giao cùng tick không hao thêm, pause dừng state, Shop giữ nguyên kho, id mẫu ngày kế nối tiếp allocator và không sửa fixture gốc. Test Shop kiểm thứ tự id, sao chép độc lập và không hao trong Shop. Test UI kiểm ngưỡng ươn theo tuning, thanh tươi, nhãn và kho khả dụng.

## Giới hạn tích hợp

Tại nền `main@e28b544`, `game.contract.json` vẫn là v1.1, chưa có `tuning.freshness`, inventory cá thể hoặc luật hao tươi trong Gather/Quan. Vì vậy test vòng ngày dùng schema v1.1 mặc định; kiểm luồng cá thể dùng tuning v1.2 và sim test adapter. Cần chạy lại smoke thật khi lát schema, Gather và Quán v1.2 được tích hợp. Kết quả này chưa xác nhận AC-P3-02–06 hoặc smoke AC-P3-09.
