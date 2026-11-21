# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả |
|---|---|---|---|
| TC-P1-01 — Bộ kiểm tra contract/starter và tính tất định | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` trên PowerShell tương đương; 51 test pass | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md) | Đạt trong phạm vi test hiện có |
| G-P1-01 — Di chuyển, chặn biên, hết giờ, cập bến và bàn giao kho | Các test `test_move_*`, `test_time_ends_gather_and_keeps_hold`, `test_inv_01_gather_writes_inventory_quan_reads_it`; smoke hai tiến trình | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md), [gather.jsonl](../proof/phase-1/gather.jsonl), [inventory.json](../proof/phase-1/inventory.json), [quan.jsonl](../proof/phase-1/quan.jsonl) | Đạt trong phạm vi các case đã chạy |
| Q-P1-01 — Luật quán theo fixture, khách, bếp, phục vụ và kết ca | `tests/test_quan_rules.py` trong bộ 51 test | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md) | Đạt trong phạm vi test hiện có |
| G-P1-02 — Oxy, lặn/nổi, ngạt, mất Máu, ngất và giỏ LIFO khi ngất | Cần test/scenario trực tiếp cho event và trạng thái | Chưa có bằng chứng | Chưa kiểm chứng |
| G-P1-03 — Hái cây, chọn nút, giỏ đầy và nút mọc lại | Cần test/scenario trực tiếp cho `gather`, `hold_full`, `node_regrown` | Chưa có bằng chứng | Chưa kiểm chứng |
| G-P1-04 — Bắt cá, chọn đàn, giỏ đầy và hồi chiêu | Cần test/scenario trực tiếp cho `fish_caught` và `hold_full` | Chưa có bằng chứng | Chưa kiểm chứng |
| UI-P1-01 — Điều khiển và HUD tối thiểu cho cả hai buổi | Chơi thử UI sau khi tích hợp module UI | Chưa có bằng chứng | Chưa kiểm chứng |

## Đánh giá ngắn

- **Đạt:** bộ test hiện có pass 51/51; smoke chứng minh `gather` ghi inventory khi cập bến và `quan` đọc đúng stock.
- **Chưa kiểm chứng:** oxy/ngạt/ngất, hái/mọc lại, bắt cá/hồi chiêu/giỏ đầy và UI/HUD chưa có bằng chứng trực tiếp trong output này.
- **Điều chỉnh tiếp:** bổ sung/chạy kiểm chứng tập trung cho các AC còn thiếu, hoàn thiện UI, rồi cập nhật bằng chứng trước khi kết luận DoD hoặc gắn tag `phase-1`.
