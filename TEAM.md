# TEAM

**Tên nhóm:** Rua  **Số người:** 3  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Vũ Nam Khánh | khanhvnm | `sim/gather` | PO · Integrator · QA lead · Scrum/Release | `sim/quan`, `client/ui` |
| Phùng Quang Trà | phungtr | `sim/quan` | QA hỗ trợ (logic quán) | `sim/gather` |
| Phạm Duy Thành | thanhtey1234 | `client/ui` | QA hỗ trợ (UI/tích hợp) | `sim/quan`, kiểm tra HUD |

**Vai quy trình:** Khánh làm PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`), Integrator (giữ `docs/contracts/`, tích hợp và gắn tag), QA lead (giữ ma trận/bằng chứng kiểm chứng) và Scrum/Release (theo dõi mốc, ghi release). Trà và Thành hỗ trợ kiểm tra chéo theo module.

## Thỏa thuận làm việc nhóm

- Kênh liên lạc: discord
- Khi bất đồng về thiết kế: trao đổi tối đa 2 phút; nếu chưa thống nhất, Khánh chốt hướng tạm thời và ghi lý do trong `docs/clarify.md` hoặc ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trên Discord; Khánh rà phụ thuộc, người dự phòng pair hoặc nhận phần nhỏ để gỡ tắc.
- Giờ standup giữa phase: rà tiến độ ở phút 20 và 45, tối đa 3 phút/người: đã xong, sắp làm, đang vướng.
- Cách đọc code của nhau: Trà review logic gather, Khánh review logic quán; Thành kiểm tra HUD/input với snapshot và smoke UI. Lỗi theo module do chủ module sửa.
- Cách làm việc với Git: mỗi người dùng nhánh ngắn cho lát việc, mở PR hoặc nhờ review trực tiếp; Khánh tích hợp lên `main`, chạy kiểm chứng rồi gắn tag phase.
