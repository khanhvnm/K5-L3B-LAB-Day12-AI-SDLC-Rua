# Kế hoạch Phase 1 — PRD-0

**Mục tiêu:** Trước 1:00, hoàn thiện lõi cả hai buổi `gather` và `quan`, HUD/điều khiển tối thiểu, Test Contract v1.0 và smoke hai tiến trình headless chứng minh nguyên liệu từ gather được quan nhận đúng. Tích hợp trên `main`, lưu bằng chứng và gắn tag `phase-1`.

## Việc, người và phụ thuộc

| Thời gian | Việc / đầu ra | Phụ trách | Phụ thuộc |
|---|---|---|---|
| 0–15′ | Chốt schema kho `{"items":{...}}`, mẫu kho, sự kiện và giao diện sim–UI; ghi vào `TEAM.md` và `docs/contracts/`. | Cả nhóm; Khánh điều phối, Thành ghi hợp đồng | Dùng đúng `game.contract.json`; thống nhất vai đã điền trong `TEAM.md` |
| 15–45′ | Hoàn thiện bơi, oxy/ngạt, Máu/ngất, giỏ; hái/bắt cá, hồi tài nguyên, cập bến và xuất kho. | Vũ Nam Khánh (`sim/gather`) | Hợp đồng kho; tuning trong `game.contract.json` |
| 15–45′ | Hoàn thiện khách/giữ chỗ/kiên nhẫn; bếp, bưng, phục vụ, thanh toán/boa, uy tín và kết ca. Dùng kho mẫu để phát triển độc lập. | Phùng Quang Trà (`sim/quan`) | Schema kho và preset/menu đã chốt |
| 15–45′ | Hoàn thiện điều khiển và HUD tối thiểu cho hai buổi; kiểm tra UI đọc snapshot chung, không đổi luật headless. | Phạm Duy Thành (`client/ui`) | Trường snapshot và lệnh input đã thống nhất |
| Trước 25′; 45–55′ | Thử xuất kho thật sớm; sau đó smoke hai tiến trình theo PRD (gather dock → `--inventory-out` → quan `--inventory`), tích hợp trên `main`, chạy test, ghi bằng chứng và ma trận AC → proof → kết quả. | Khánh điều phối/QA; Thành kiểm tra UI; Khánh/Trà xử lý lỗi theo module | Gather và quan có thể chạy headless; file kho theo hợp đồng |
| 55–60′ | Dự phòng lỗi cuối; xác nhận commit bàn giao trên `main` chạy được và gắn `phase-1` trước 1:00. | Khánh (Integrator/Release), QA cả nhóm | Smoke và ghi chép hoàn tất |

## Rủi ro

- Quy mô nhóm 3 người đã được chấp nhận; các vai quy trình kiêm nhiệm theo `TEAM.md`. Rủi ro còn lại là tải việc lớn, nên ưu tiên lõi và chuyển hỗ trợ theo standup.
- Phạm vi lõi lớn cho 60 phút; ưu tiên Test Contract, bàn giao kho và smoke hai mode trước HUD/ý tưởng sáng tạo. Dùng standup ngắn và chuyển người hỗ trợ lát bị vướng quá 10 phút.
- Thay schema hoặc tuning giữa chừng có thể làm hỏng tích hợp; chốt hợp đồng đầu phase, mọi giả định ghi `docs/clarify.md`, không thay số chuẩn nếu chưa thống nhất.
