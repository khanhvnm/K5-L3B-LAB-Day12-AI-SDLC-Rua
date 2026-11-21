# Vũ Nam Khánh — `khanhvnm`

## Phase 1

- Vai: PO, Integrator, QA lead, Scrum/Release.
- Module chính: `sim/gather`.
- Bằng chứng: [kế hoạch Phase 1](../plan/phase-1.md), [hợp đồng tích hợp](../contracts/README.md), [test Gather](../proof/phase-1/gather-rules-tests.md), [handoff kho](../proof/phase-1/test-and-handoff.md), [ma trận kiểm chứng](../verification/phase-1.md).
- Commits liên quan: `e491f20`, `1be7d1c`, `33f666d`, `e6128c0`. Các commit tài liệu/merge còn lại dùng nhiều Git author name; cần đối chiếu trang contributor của GitHub để xác nhận đầy đủ theo handle.

## Phase 2

- Vai: PO, Integrator, QA lead; chủ hợp đồng v1.1.
- Việc: kế hoạch và AC-P2 (`docs/plan/phase-2.md`); `game.contract.json` 1.1 và `chonoi/contract.py`; cá bơi/sinh trong `chonoi/sim/gather.py`; luật Shop `chonoi/sim/shop.py`; test `tests/test_gather_v11.py`, `tests/test_shop_rules.py`; review PR #5, #6; smoke tích hợp và smoke day; verification Phase 2.
- Commits: `1c2e678` (gather/contract), `787fd22` (shop), `62b35b8` (docs); merge PR #4, #6.
- Bằng chứng: [integration.md](../proof/phase-2/integration.md), [day-smoke.md](../proof/phase-2/day-smoke.md), [verification](../verification/phase-2.md).

## Phase 3

- Vai: PO, chủ hợp đồng v1.2, Integrator.
- Việc: kế hoạch và phân tích tác động (`docs/plan/phase-3.md`); lát S (`chonoi/inventory.py`, contract 1.2) và G (độ tươi gather); di chuyển fixture test P1–P2; `tests/test_fresh_v12.py`; tích hợp `p3/schema` với lát Quán/Day; smoke và verification Phase 3.
- Commits: `35dbdea`, `2a5c0f6`, `6368d06` (p3/schema) và commit tích hợp trên `p3/integrate`.
- Bằng chứng: [schema-gather.md](../proof/phase-3/schema-gather.md), [integration.md](../proof/phase-3/integration.md).

## Tự phản tư

Khánh cần tự ghi điều đã học, phần đã review và một lỗi AI đã phát hiện trước khi nộp retro cá nhân.
