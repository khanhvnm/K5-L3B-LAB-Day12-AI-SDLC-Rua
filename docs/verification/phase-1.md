# Ma trận truy vết Phase 1

## Cập nhật bằng chứng Gather (sau bộ 51 test ban đầu)

Khánh chạy bổ sung `tests/test_gather_rules.py`: **10/10 đạt** (2.301s). Sau đó chạy toàn bộ suite: **61/61 đạt** (33.568s). Kết quả chi tiết và phạm vi các case được ghi tại [gather-rules-tests.md](../proof/phase-1/gather-rules-tests.md).

Trạng thái được cập nhật: **G-P1-02, G-P1-03 và G-P1-04 đạt trong phạm vi các case headless này**. Các kiểm tra bao gồm oxy cạn/hồi oxy, ngạt và ngất làm rơi giỏ LIFO, hái cây/chọn nút/nút mọc lại/giỏ đầy, bắt cá/hồi chiêu/giỏ đầy.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả |
|---|---|---|---|
| TC-P1-01 — Bộ kiểm tra contract/starter và tính tất định | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` trên PowerShell tương đương; 51 test pass | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md) | Đạt trong phạm vi test hiện có |
| G-P1-01 — Di chuyển, chặn biên, hết giờ, cập bến và bàn giao kho | Các test `test_move_*`, `test_time_ends_gather_and_keeps_hold`, `test_inv_01_gather_writes_inventory_quan_reads_it`; smoke hai tiến trình | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md), [gather.jsonl](../proof/phase-1/gather.jsonl), [inventory.json](../proof/phase-1/inventory.json), [quan.jsonl](../proof/phase-1/quan.jsonl) | Đạt trong phạm vi các case đã chạy |
| Q-P1-01 — Luật quán theo fixture, khách, bếp, phục vụ và kết ca | `tests/test_quan_rules.py` trong bộ 51 test | [test-and-handoff.md](../proof/phase-1/test-and-handoff.md) | Đạt trong phạm vi test hiện có |
| G-P1-02 — Oxy, lặn/nổi, ngạt, mất Máu, ngất và giỏ LIFO khi ngất | `tests/test_gather_rules.py`: oxy cạn, hồi oxy, ngạt/ngất, event lost theo LIFO và inventory rỗng | [gather-rules-tests.md](../proof/phase-1/gather-rules-tests.md) | Đạt trong phạm vi các case headless đã chạy |
| G-P1-03 — Hái cây, chọn nút, giỏ đầy và nút mọc lại | `tests/test_gather_rules.py`: chọn nút gần nhất/tie ID, hái, mọc lại rồi hái cùng tick, giỏ đầy giữ nguyên nút | [gather-rules-tests.md](../proof/phase-1/gather-rules-tests.md) | Đạt trong phạm vi các case headless đã chạy |
| G-P1-04 — Bắt cá, chọn đàn, giỏ đầy và hồi chiêu | `tests/test_gather_rules.py`: bắt cá gần nhất, cooldown, giỏ đầy giữ cá và không kích hoạt cooldown | [gather-rules-tests.md](../proof/phase-1/gather-rules-tests.md) | Đạt trong phạm vi các case headless đã chạy |
| UI-P1-01 — Điều khiển và HUD tối thiểu cho cả hai buổi | `node --test tests/test_ui.js` (7/7 pass); Chrome headless smoke tại 800×600 và 1280×720 cho cả hai mode | [ui-p1.md](../proof/ui-p1.md) | Đạt cho UI/HUD tối thiểu và các luồng input đã kiểm tra; gameplay đầy đủ chưa được xác nhận bằng chơi tay |

## Đánh giá ngắn

- **Đạt:** test suite đã pass 61/61 trước khi merge UI; Gather có test headless trực tiếp; UI/HUD có 7 test Node pass và smoke Chrome headless ở hai kích thước cho cả hai mode.
- **Còn cần xác nhận:** chạy lại toàn bộ Python unittest sau merge UI và chơi thử gameplay thực tế cho các tương tác quan trọng. Môi trường kiểm tra hiện tại không có `python3`, nên chưa xác nhận được suite tổng hợp sau merge.
- **Trước khi kết luận DoD/gắn tag:** đối chiếu toàn bộ PRD-0/phase-1 acceptance criteria và xác nhận kết quả full-suite mới nhất.
Phần UI của Phạm Duy Thành: xem [bằng chứng UI](../proof/ui-p1.md). UI đã được tích hợp và có test fixture/smoke giao diện; gameplay thực tế chưa được kiểm tra tay qua các tương tác chính. Ma trận hiện chưa ánh xạ đầy đủ mã AC từ PRD-0, nên chưa đủ cơ sở kết luận DoD toàn phase.

- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
