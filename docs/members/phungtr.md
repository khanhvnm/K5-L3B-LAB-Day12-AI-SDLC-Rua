# Phùng Quang Trà — `phungtr`

## Phase 1

- Vai: chủ module `sim/quan`, QA hỗ trợ logic quán.
- Bằng chứng: [ma trận kiểm chứng Phase 1](../verification/phase-1.md), [test luật quán](../../tests/test_quan_rules.py), [handoff kho](../proof/phase-1/test-and-handoff.md).
- Lịch sử repo hiện có commit `3420719` (`quan`) và merge commit `86f2f25` dưới Git author name `phungtr`.

## Phase 2

- Vai: chủ lát Cá Sấu (B) và quán v1.1/kế hoạch ngày (C).
- Việc: `chonoi/sim/monsters.py` và tích hợp vào gather; `chonoi/dayplan.py`; quán 2 bếp/4 bàn, lọc menu theo kế hoạch; test `tests/test_monsters.py`, `tests/test_day_plan.py`, test quán v1.1.
- Commits: `c739633`, `78942f6`, `1debbf0`, `eb660a7`, `c3a5382`; merge PR #5.
- Trà tự bổ sung phần tự phản tư Phase 2.

## Phase 3

- Vai: chủ lát Quán v1.2.
- Việc: kho cá thể trong `chonoi/sim/quan.py` (đơn vị 240/điểm), hao tươi, `spoiled`, giữ chỗ theo id, nhả/giữ lại khi hàng vừa ươn, giá theo tươi; kiểm `quan.stock`/`reserved` trong `chonoi/scenario.py`; `tests/test_fresh_quan.py` và chuyển `test_quan_rules` sang cá thể.
- Commits: `73722a7`, `8c23154`; merge PR #8.

## Tự phản tư

Trà cần tự ghi phần đã review, điều học được và một lỗi AI đã phát hiện trước khi nộp retro cá nhân.
