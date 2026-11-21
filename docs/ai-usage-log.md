# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | khanhvnm | Codex (GPT-6) | Rà PRD, soạn kế hoạch/TEAM/hợp đồng tích hợp, triển khai luật `gather`, tổng hợp bằng chứng test và smoke | chưa đo | Khánh rà output test 51/51 và smoke; các luật oxy/hái/bắt cá vẫn cần kiểm chứng trực tiếp. |
| 1 | Phạm Duy Thành | Codex | UI/HUD, input, test tích hợp; dọn phần luật ngoài phân công, không commit | Không có số liệu token/chi phí | Code luật tạo trước phân công lệch hợp đồng mới, đã khôi phục để chủ module làm; UI theo hợp đồng đã pull. |
| 1 | phungtr | Claude Code (Claude Opus 5.5) | Viết `sim/quan` (lát 3–4), kiểm fixture quán (PRD-0 mục D), 19 test hộp đen `tests/test_quan_rules.py` | chưa đo | AI viết một test "tay đầy không lấy món" không thể xảy ra vì quán chỉ có 1 bàn; phát hiện khi rà fixture, thay bằng test bếp đang nấu bỏ lượt. Smoke test lỗi trên Windows vì không có `python3`. |


Phase 1 — Khánh / Codex (GPT-6): bổ sung test headless cho luật Gather; Khánh chạy 10 test tập trung và toàn bộ 61 test, cả hai lượt đều pass. Khánh đã xem lại đầu ra; proof: `docs/proof/phase-1/gather-rules-tests.md`.

Phase 2 — Thành / Codex: đối chiếu TICKET-02 từ session trước, nối điều phối day/Pause với CLI và UI, kiểm JSONL, regression và Chrome headless. Shop và kế hoạch fixture chỉ kiểm giao diện tích hợp; xem [bằng chứng lát D/E](proof/phase-2/day-ui.md).

Phase 2 — Khánh / Claude Code (Claude Sonnet 5.5, Opus 5.5): chia lát và AC-P2 (`docs/plan/phase-2.md`); `game.contract.json` 1.1 và bộ kiểm; cá bơi/sinh trong gather; luật Shop; review `p2/quan` và `p2/day-ui`; smoke tích hợp và smoke day (`docs/proof/phase-2/integration.md`, `day-smoke.md`). AI sai: test sinh cá ban đầu thất bại vì fixture 12 đàn đã chạm trần `fish_max`; phát hiện khi chạy test, sửa fixture chứ không sửa luật. AI tự thêm dòng `Co-Authored-By` vào commit; Khánh yêu cầu bỏ và 3 commit chưa push được viết lại. Token: chưa đo.

Phase 2 — Trà: lát Cá Sấu, quán v1.1 và kế hoạch ngày (PR #5). Trà tự bổ sung công cụ/model và lỗi AI đã phát hiện.

Phase 3 — Khánh / Claude Code (Claude Opus 5.5): kế hoạch và phân tích tác động (`docs/plan/phase-3.md`); lát S (contract 1.2, `chonoi/inventory.py` kho cá thể, adapter tạm cho quán) và lát G (hao tươi, `spoiled`, id cá thể trong gather); di chuyển fixture test P1–P2; `tests/test_fresh_v12.py`; bằng chứng `docs/proof/phase-3/schema-gather.md`. AI sai: (1) đặt tên import `counts` trùng biến cục bộ trong `day.py` gây `UnboundLocalError`, phát hiện qua test day, đổi tên `count_items`; (2) so `gather_end.inventory` trong JSONL với file kho bằng `==` thất bại vì khung JSONL làm tròn 3 chữ số — sửa test so có dung sai thay vì đổi khung. Token: chưa đo.

Phase 3 (tích hợp) — Khánh / Claude Code (Claude Opus 5.5): phát hiện `p3/schema` chưa vào `main` (suite đỏ 5 test), ghép trên `p3/integrate`, giải 3 conflict, bỏ adapter/khối trùng, chạy smoke ticket, quán, day và đo hiệu năng (`docs/proof/phase-3/integration.md`). AI sai: lần đầu lấy `day.delivered` bằng bản sắp theo id, làm vỡ test của Thành vốn so đúng mảng `gather_end`; sửa bằng cách sao thẳng từ event. Lần đo hiệu năng đầu ghi ra `NUL` trên Windows làm runner lỗi tạo file tạm — đo lại bằng file thật.

Phase 2 — Trà / Claude Code (Claude Opus 5.5): lát C (quán 2 bếp/4 bàn, 6 món, `chonoi/dayplan.py` D1–D5, lọc menu theo kế hoạch) và lát B (`chonoi/sim/monsters.py` Cá Sấu, Máu, ngất), `tests/test_day_plan.py`, `tests/test_monsters.py`. AI sai: không ghi nhận lỗi luật sau khi chạy test; lần đầu lệnh commit gộp với `git diff --check` bị chặn vì dòng trống cuối `docs/clarify.md` (không thuộc lát) — tách lệnh, không sửa file người khác. Vướng môi trường (không phải lỗi AI): trên Windows `headless_cmd` gọi `python3` nên test hộp đen lỗi `WinError 2`; kiểm bằng bản sao đổi sang `python`, không sửa contract. Token: chưa đo.

Phase 3 — Trà / Claude Code (Claude Opus 5.5): lát Quán v1.2 (kho cá thể, hao tươi, `spoiled`, giữ chỗ theo id, giữ lại khi ươn, giá theo tươi), `tests/test_fresh_quan.py` (14 test), đổi `test_quan_rules` sang kho cá thể. AI sai: script đổi test hàng loạt ghi file xong nhưng lỗi in tiếng Việt trên console Windows (cp1252) — kiểm bằng grep thấy không còn fixture kho đếm. Token: chưa đo.

Phase 4 — Trà / Claude Code (Claude Opus 5.5): `chonoi/soak.py` (bot tất định, 10 Ngày, kế hoạch D1–D5 lặp), `tests/test_soak.py`, nháp retro Phase 4 với số liệu từ git. AI sai: bot đọc `time_left_ticks` từ snapshot riêng của sim (không có trường này) — lần soak đầu báo `crashes: 1` kèm traceback, sửa sang `sess.sim.time_left_ticks`. Token: chưa đo.
