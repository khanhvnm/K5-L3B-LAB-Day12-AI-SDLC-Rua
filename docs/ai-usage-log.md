# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | khanhvnm | Codex (GPT-6) | Rà PRD, soạn kế hoạch/TEAM/hợp đồng tích hợp, triển khai luật `gather`, tổng hợp bằng chứng test và smoke | chưa đo | Khánh rà output test 51/51 và smoke; các luật oxy/hái/bắt cá vẫn cần kiểm chứng trực tiếp. |
| 1 | Phạm Duy Thành | Codex | UI/HUD, input, test tích hợp; dọn phần luật ngoài phân công, không commit | Không có số liệu token/chi phí | Code luật tạo trước phân công lệch hợp đồng mới, đã khôi phục để chủ module làm; UI theo hợp đồng đã pull. |
| 1 | phungtr | Claude Code (Claude Opus 5.5) | Viết `sim/quan` (lát 3–4), kiểm fixture quán (PRD-0 mục D), 19 test hộp đen `tests/test_quan_rules.py` | chưa đo | AI viết một test "tay đầy không lấy món" không thể xảy ra vì quán chỉ có 1 bàn; phát hiện khi rà fixture, thay bằng test bếp đang nấu bỏ lượt. Smoke test lỗi trên Windows vì không có `python3`. |


Phase 1 — Khánh / Codex (GPT-6): bổ sung test headless cho luật Gather; Khánh chạy 10 test tập trung và toàn bộ 61 test, cả hai lượt đều pass. Khánh đã xem lại đầu ra; proof: `docs/proof/phase-1/gather-rules-tests.md`.

Phase 2 — Thành / Codex: đối chiếu TICKET-02 từ session trước, nối điều phối day/Pause với CLI và UI, kiểm JSONL, regression và Chrome headless. Shop và kế hoạch fixture chỉ kiểm giao diện tích hợp; xem [bằng chứng lát D/E](proof/phase-2/day-ui.md).
