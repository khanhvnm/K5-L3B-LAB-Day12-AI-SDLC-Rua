# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| Q1 | 2026-11-21 P1 | Đơn `reserved` trong fixture không khai `reserved` mà kho khả dụng không đủ thì sao? | Giả định: cấp theo (order_tick, id bàn); đơn nào không đủ hàng thành `unfulfillable`, `reserved: {}` (không báo mã 2). Khai `reserved` mà vượt tồn hoặc khác công thức thì mã 2. | Trà (giả định, chờ PO hỏi Anh Năm) |
| Q2 | 2026-11-21 P1 | `base_price`, `tip` của khách trước khi chốt? | Giả định: `null` tới lúc chốt (giá chốt khi `cook_started`, boa chốt khi `served`). | Trà (giả định) |
| Q3 | 2026-11-21 P1 | `stoves[].dish` có dạng gì? | Giả định: cùng payload với `hand`: `{order_id, dish_id, base_price}`. | Trà (giả định) |
| Q4 | 2026-11-21 P1 | Khách ăn xong đúng tick hết ca: `paid.reason` là gì? | Giả định: `finished_eating` (luật "ăn xong trả tiền" xét trước); khách còn đang ăn khác trả với `closing`. | Trà (giả định) |
| Q5 | 2026-11-21 P1 | "Chọn đều theo seed" làm thế nào? | Luồng RNG `customers` (`Streams`), `randrange` trên danh sách món đủ nguyên liệu khả dụng, sắp theo id món (mã Unicode). | Trà |
| Q6 | 2026-11-21 P1 | Sai số float của uy tín (3.0 + 0.2 + …) làm lệch `floor` trong điểm? | Làm tròn uy tín 6 chữ số sau mỗi lần đổi, sau khi kẹp `[reputation_min, reputation_max]`. | Trà |
