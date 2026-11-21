# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| UI-01 | 2026-11-21 | Ưu tiên giao diện Phase 1? | Người dùng chọn HUD tối thiểu: giữ Canvas, hoàn thiện điều khiển/HUD/thông báo theo hợp đồng hiện có, không thêm framework/asset ngoài. | Phạm Duy Thành |
| UI-02 | 2026-11-21 | Xử lý luật gather/quán đã viết trước khi có phân công? | Khôi phục về main và loại các test/proof của phần luật khỏi nhánh p1/ui; Khánh làm gather, Trà làm quán. Các giả định cũ không được dùng thay hợp đồng vừa cập nhật. | Phạm Duy Thành |
| UI-03 | 2026-11-21 | Snapshot món trên bếp/tay chưa mô tả đầy đủ trong hợp đồng? | UI đọc chuỗi dish_id hoặc object có dish_id; dữ liệu khác hiển thị chưa có dữ liệu. Event bám order_id/base_price/yield theo hợp đồng; chờ chủ module xác nhận snapshot thực tế khi tích hợp. | Ghi chú tích hợp, chờ chủ module |
| Q1 | 2026-11-21 P1 | Đơn `reserved` trong fixture không khai `reserved` mà kho khả dụng không đủ thì sao? | Giả định: cấp theo (order_tick, id bàn); đơn nào không đủ hàng thành `unfulfillable`, `reserved: {}` (không báo mã 2). Khai `reserved` mà vượt tồn hoặc khác công thức thì mã 2. | Trà (giả định, chờ PO hỏi Anh Năm) |
| Q2 | 2026-11-21 P1 | `base_price`, `tip` của khách trước khi chốt? | Giả định: `null` tới lúc chốt (giá chốt khi `cook_started`, boa chốt khi `served`). | Trà (giả định) |
| Q3 | 2026-11-21 P1 | `stoves[].dish` có dạng gì? | Giả định: cùng payload với `hand`: `{order_id, dish_id, base_price}`. | Trà (giả định) |
| Q4 | 2026-11-21 P1 | Khách ăn xong đúng tick hết ca: `paid.reason` là gì? | Giả định: `finished_eating` (luật "ăn xong trả tiền" xét trước); khách còn đang ăn khác trả với `closing`. | Trà (giả định) |
| Q5 | 2026-11-21 P1 | "Chọn đều theo seed" làm thế nào? | Luồng RNG `customers` (`Streams`), `randrange` trên danh sách món đủ nguyên liệu khả dụng, sắp theo id món (mã Unicode). | Trà |
| Q6 | 2026-11-21 P1 | Sai số float của uy tín (3.0 + 0.2 + …) làm lệch `floor` trong điểm? | Làm tròn uy tín 6 chữ số sau mỗi lần đổi, sau khi kẹp `[reputation_min, reputation_max]`. | Trà |
| P2-01 | 2026-11-21 | `recoil_dist` của Cá Sấu: tổng quãng hay tốc độ? | Giả định: tổng quãng lùi (m); mỗi bước lùi `recoil_dist / recoil_ticks` = 2/60 m, khớp ticket. Ghi trong `docs/contracts/README.md` 4.1. | Khánh (giả định) |
| P2-02 | 2026-11-21 | "8 điểm khác nhau" lúc đầu ca: khác cặp loài–điểm hay khác vị trí hình học? | Giả định: khác vị trí hình học (cách nhau > `fish_spawn_clearance`), dùng cùng thủ tục với sinh theo lịch; cặp linh/lóc cùng `[x,10]` không cùng xuất hiện. | Khánh (giả định) |
| P2-03 | 2026-11-21 | Hướng mới khi đổi hướng ở bước 120·k lấy phân bố nào? | Giả định: đều trên [0°, 360°) từ luồng RNG `fish_swim`, mỗi đàn một lần rút theo thứ tự id. Test không ghi cứng giá trị. | Khánh (giả định) |
| P2-04 | 2026-11-21 | Shop: lệnh `buy` ngoài oxygen/hp (mở rộng chưa bật) xử lý thế nào? | `buy_failed` với `reason: "unknown"`, tiền và cấp giữ nguyên, theo §4.2 ticket. | Khánh |
| P2-UI-01 | Phase 2 | Khi nào rời EveningIntro và DayResult? | Ticket chỉ nêu thời gian tự chuyển cho DayIntro (4 giây). Nhánh UI dùng nút hoặc phím để tiếp tục ở hai màn còn lại; các màn chỉ dừng vòng tick trên trình duyệt. | Giả định lát UI, chờ PO xác nhận |
| P2-D-01 | Phase 2 | Kiểm mâu thuẫn fixture quán khi kho thật chỉ có ở cuối gather? | Kiểm cấu trúc trước, kiểm món theo kế hoạch và kho thật khi mở quán. CLI trả mã 2 và giữ nguyên file đích nếu có lỗi muộn. | TICKET-02 §4.3; điều phối Thành |
