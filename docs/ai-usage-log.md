# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | khanhvnm | Codex (GPT-6) | Rà PRD, soạn kế hoạch/TEAM/hợp đồng tích hợp, triển khai luật `gather`, tổng hợp bằng chứng test và smoke | chưa đo | Khánh rà output test 51/51 và smoke; các luật oxy/hái/bắt cá vẫn cần kiểm chứng trực tiếp. |
| 1 | phungtr | Claude Code (Claude Opus 5.5) | Viết `sim/quan` (lát 3–4), kiểm fixture quán (PRD-0 mục D), 19 test hộp đen `tests/test_quan_rules.py` | chưa đo | AI viết một test "tay đầy không lấy món" không thể xảy ra vì quán chỉ có 1 bàn; phát hiện khi rà fixture, thay bằng test bếp đang nấu bỏ lượt. Smoke test lỗi trên Windows vì không có `python3`. |
