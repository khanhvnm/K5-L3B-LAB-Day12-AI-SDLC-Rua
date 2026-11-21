# Quy trình: rà hợp đồng tích hợp

Dùng trước khi sửa hoặc tích hợp schema, event, snapshot hay số liệu gameplay.

1. Đọc `docs/contracts/README.md`, PRD/ticket liên quan và `game.contract.json`.
2. Liệt kê producer/consumer bị ảnh hưởng: sim, runner, headless, live UI, fixture, test và luồng kho gather → quan.
3. Giữ tên trường, event, kiểu dữ liệu và thứ tự tick nhất quán. Số liệu gameplay lấy từ contract/data, không nhân bản thành hằng số trong luật.
4. Ghi yêu cầu chưa rõ và giả định vào `docs/clarify.md`; không tự đổi schema để làm test xanh.
5. Cập nhật test/fixture liên quan cùng implementation; chạy test tập trung và full suite nếu runtime sẵn có.
6. Cập nhật hợp đồng và proof cùng thay đổi. Thay đổi schema liên module cần được nhóm thống nhất trước khi tích hợp.
