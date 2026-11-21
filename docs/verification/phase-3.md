# Ma trận truy vết Phase 3

Mã AC-P3-xx định nghĩa trong [kế hoạch Phase 3](../plan/phase-3.md). Kết quả chạy trên bản tích hợp `p3/integrate` (= `main@376e56b` + `p3/schema`); commit bàn giao là commit gắn tag `phase-3`.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 — contract 1.2, `freshness` | `test_fresh_v12.py::Contract12` | — | Đạt |
| AC-P3-02 — schema kho cá thể; mã 2 cho kho đếm/sai schema/kind lạ/id trùng/fresh ngoài miền; ghi một lần, nguyên tử, theo id; ngất → `[]`; chạm `--ticks` giữ đích | `test_fresh_v12.py::InventoryFile`, `GatherFresh::test_tick_limit_before_end_keeps_destination`, `test_monsters`, `test_gather_rules` | [integration.md](../proof/phase-3/integration.md) §1 | Đạt |
| AC-P3-03 — gather: fresh 100, hao 0,5/s từ bước sau, `spoiled` một lần theo id, `lost` cá thể LIFO, `hold` cá thể | `test_fresh_v12.py::GatherFresh` (10 test) | [integration.md](../proof/phase-3/integration.md) §1, §3; [schema-gather.md](../proof/phase-3/schema-gather.md) | Đạt |
| AC-P3-04 — quán: hao 0,25/s kể cả hàng giữ, `spoiled stock`, giữ theo id tươi nhất, nhả/giữ lại khi vừa ươn | `test_fresh_quan.py` (13 test) | [integration.md](../proof/phase-3/integration.md) §2 | Đạt |
| AC-P3-05 — giá theo tươi, boa trên giá chốt, `cook_started.items` | `test_fresh_quan.py`, `test_quan_rules.py` | [integration.md](../proof/phase-3/integration.md) §2 (`base_price 29`) | Đạt |
| AC-P3-06 — scenario quán `stock`/`reserved`, mâu thuẫn → mã 2 | `test_fresh_quan.py`, `test_quan_rules.py::...fixture` | — | Đạt |
| AC-P3-07 — day: bàn giao cùng tick không hao thêm, Shop không hao, id xuyên Ngày, pause dừng hao | `test_day.py::test_v12_handoff_...`, `test_fresh_v12.py::DayIds`, `test_shop_rules.py` | [integration.md](../proof/phase-3/integration.md) §3 | Đạt |
| AC-P3-08 — HUD độ tươi/ươn | `tests/test_ui.js` (12/12: thanh tươi, nhãn ươn theo tuning, kho khả dụng) | [day-ui.md](../proof/phase-3/day-ui.md) | Đạt bằng test UI; chưa chơi tay |
| AC-P3-09 — smoke ticket (ngưỡng tick 1; bàn giao file → quán tick 0) | CLI | [integration.md](../proof/phase-3/integration.md) §1 | Đạt |
| AC-P3-10 — regression P1–P2 | Full suite **154/154 pass**, Node UI 12/12; day 1 Ngày 22.200 tick 0,69 s. Test cũ đổi chỉ vì schema, liệt kê trong `CHANGELOG.md` | [integration.md](../proof/phase-3/integration.md) §4 | Đạt |

## Ghi tác động và thứ tự tích hợp

Ghi trong [kế hoạch Phase 3](../plan/phase-3.md) (bảng module → file → test → người). Thực tế PR lát schema vào sau PR Quán/Day; cách ghép lại và các chỗ đã gỡ trùng ghi ở [integration.md](../proof/phase-3/integration.md) "Việc tích hợp" và [retro](../retro.md).

## Đánh giá DoD

- **Đạt:** kho cá thể qua file và trong day, kho đếm mã 2, id/độ tươi/ươn/giữ chỗ/giá/JSONL theo luật; HUD độ tươi; test ngưỡng, giữ lại khi vừa ươn, chốt giá, bàn giao; CHANGELOG breaking change; regression.
- **Hạn chế:** chưa có lượt chơi tay; rủi ro làm tròn fixture quán không bội 1/240 (clarify P3-05).
- **Không làm mở rộng** (dòng lũ, khách đặt trước); manifest không khai `extensions`.
