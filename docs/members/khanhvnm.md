# Vũ Nam Khánh — `khanhvnm`

> Nháp, Khánh tự soát trước khi nộp.

**Phần mình làm.** PO, Integrator, QA lead cả bốn phase: kế hoạch, AC, hợp đồng. Luật `gather` (P1); contract v1.1, cá bơi, Shop (`1c2e678`, `787fd22`); kho cá thể v1.2 (`35dbdea`); manifest v1.3 và bench (`e8f29c8`, `7f9a0f6`). Tích hợp PR #1–#13, gắn tag.

**Đã giúp ai.** Ghép lát schema với Quán của Trà và Day/HUD của Thành khi `main` đỏ (`e3e019b`), gỡ adapter và khối contract trùng. Review PR #5, #6, chạy smoke cho nhóm ([P2](../proof/phase-2/integration.md), [P3](../proof/phase-3/integration.md)).

**AI sai ở đâu.** Đặt tên import trùng biến cục bộ trong `day.py`. Chèn JS bench làm hỏng 12 test UI Node. Tự thêm `Co-Authored-By` vào commit. Phát hiện nhờ chạy lại full suite và đọc commit trước khi đẩy.

**Bài học.** PR đổi hợp đồng phải vào `main` trước PR phụ thuộc; Phase 3 mình để lát schema ngoài `main` nên hai bạn phải tự viết adapter. Chạy smoke ngay sau mỗi lần merge, không dồn cuối phase.
