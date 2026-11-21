# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Phạm Duy Thành | Codex | UI/HUD, input, test tích hợp; dọn phần luật ngoài phân công, không commit | Không có số liệu token/chi phí | Code luật tạo trước phân công lệch hợp đồng mới, đã khôi phục để chủ module làm; UI theo hợp đồng đã pull. |
| 1 | phungtr | Claude Code (Claude Opus 5.5) | Viết `sim/quan` (lát 3–4), kiểm fixture quán (PRD-0 mục D), 19 test hộp đen `tests/test_quan_rules.py` | chưa đo | AI viết một test "tay đầy không lấy món" không thể xảy ra vì quán chỉ có 1 bàn; phát hiện khi rà fixture, thay bằng test bếp đang nấu bỏ lượt. Smoke test lỗi trên Windows vì không có `python3`. |
