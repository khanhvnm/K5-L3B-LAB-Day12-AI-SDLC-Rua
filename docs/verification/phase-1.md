# Ma trận truy vết Phase 1

## Cập nhật bằng chứng Gather (sau bộ 51 test ban đầu)

Khánh chạy bổ sung `tests/test_gather_rules.py`: **10/10 đạt** (2.301s). Sau đó chạy toàn bộ suite: **61/61 đạt** (33.568s). Kết quả chi tiết và phạm vi các case được ghi tại [gather-rules-tests.md](../proof/phase-1/gather-rules-tests.md).

Trạng thái được cập nhật: **G-P1-02, G-P1-03 và G-P1-04 đạt trong phạm vi các case headless này**. Các kiểm tra bao gồm oxy cạn/hồi oxy, ngạt và ngất làm rơi giỏ LIFO, hái cây/chọn nút/nút mọc lại/giỏ đầy, bắt cá/hồi chiêu/giỏ đầy. **UI/HUD vẫn chưa được kiểm chứng bằng lượt chơi trực tiếp.**

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả |
|---|---|---|---|
| TC-P1-01 — Bộ kiểm tra contract/starter và tính tất định | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` trên PowerShell tương đương; 51 test pass | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md) | Đạt trong phạm vi test hiện có |
| G-P1-01 — Di chuyển, chặn biên, hết giờ, cập bến và bàn giao kho | Các test `test_move_*`, `test_time_ends_gather_and_keeps_hold`, `test_inv_01_gather_writes_inventory_quan_reads_it`; smoke hai tiến trình | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md), [gather.jsonl](../proof/phase-1/gather.jsonl), [inventory.json](../proof/phase-1/inventory.json), [quan.jsonl](../proof/phase-1/quan.jsonl) | Đạt trong phạm vi các case đã chạy |
| Q-P1-01 — Luật quán theo fixture, khách, bếp, phục vụ và kết ca | `tests/test_quan_rules.py` trong bộ 51 test | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md) | Đạt trong phạm vi test hiện có |
| G-P1-02 — Oxy, lặn/nổi, ngạt, mất Máu, ngất và giỏ LIFO khi ngất | `tests/test_gather_rules.py`: oxy cạn, hồi oxy, ngạt/ngất, event lost theo LIFO và inventory rỗng | [gather-rules-tests.md](../proof/phase-1/gather-rules-tests.md) | Đạt trong phạm vi các case headless đã chạy |
| G-P1-03 — Hái cây, chọn nút, giỏ đầy và nút mọc lại | `tests/test_gather_rules.py`: chọn nút gần nhất/tie ID, hái, mọc lại rồi hái cùng tick, giỏ đầy giữ nguyên nút | [gather-rules-tests.md](../proof/phase-1/gather-rules-tests.md) | Đạt trong phạm vi các case headless đã chạy |
| G-P1-04 — Bắt cá, chọn đàn, giỏ đầy và hồi chiêu | `tests/test_gather_rules.py`: bắt cá gần nhất, cooldown, giỏ đầy giữ cá và không kích hoạt cooldown | [gather-rules-tests.md](../proof/phase-1/gather-rules-tests.md) | Đạt trong phạm vi các case headless đã chạy |
| UI-P1-01 — Điều khiển và HUD tối thiểu cho cả hai buổi | Chơi thử UI sau khi tích hợp module UI | Chưa có bằng chứng | Chưa kiểm chứng |

## Đánh giá ngắn

- **Đạt:** toàn bộ suite hiện tại pass 61/61; smoke chứng minh `gather` ghi inventory khi cập bến và `quan` đọc đúng stock. Ba nhóm luật Gather G-P1-02/03/04 có test headless trực tiếp.
- **Chưa kiểm chứng:** UI/HUD chưa có bằng chứng từ lượt chơi trực tiếp.
- **Điều chỉnh tiếp:** hoàn thiện và kiểm tra UI/HUD theo PRD-0; sau đó cập nhật bằng chứng trước khi kết luận DoD hoặc gắn tag `phase-1`.
Phần UI của Phạm Duy Thành: xem [bằng chứng UI](../proof/ui-p1.md). Test fixture UI và smoke giao diện ban đầu đã đạt; gameplay nâng cao chờ hai chủ module tích hợp. Chưa có đầy đủ mã AC từ PRD để chốt ma trận toàn phase.

- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
