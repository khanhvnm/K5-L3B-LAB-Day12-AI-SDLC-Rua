# Phạm Duy Thành — `thanhtey1234`

## Phase 1

- Vai: chủ module `client/ui`, QA hỗ trợ UI/tích hợp.
- Bằng chứng: [bằng chứng UI](../proof/ui-p1.md), [test UI JavaScript](../../tests/test_ui.js), [ma trận kiểm chứng Phase 1](../verification/phase-1.md).
- Lịch sử repo hiện có commit `549bf84` (`UI`) dưới Git author name `thanhtey1234`; merge PR #3 do người khác tạo.

## Phase 2

- Vai: chủ lát day/pause (D) và UI/HUD (E) trên `p2/day-ui`.
- Việc: `chonoi/day.py` (điều phối gather → quán → Shop, D1–D5), pause trong runner/inputs, CLI `--days`, menu/DayIntro/EveningIntro/DayResult/Shop/Summary và HUD trong `chonoi/web/index.html`; test `tests/test_day.py`, `tests/test_ui.js`.
- Commits: `5742593` (một commit gộp), merge `f3c8bbc`. Cần thêm commit có nội dung bằng tài khoản của mình để đủ ≥ 3.
- Bằng chứng: [day-ui.md](../proof/phase-2/day-ui.md). Thành tự bổ sung phần tự phản tư Phase 2.

## Phase 3

- Vai: chủ lát Day/HUD v1.2.
- Việc: bàn giao cá thể và id mẫu `hold` xuyên Ngày trong `chonoi/day.py`, Shop `stock` cá thể không hao, kho khả dụng trong `chonoi/live.py`, bảng độ tươi trong HUD; test `test_day`, `test_shop_rules`, `test_live`, `test_ui.js`.
- Commits: `000593e`; merge PR #9. Bằng chứng: [day-ui.md](../proof/phase-3/day-ui.md).

## Tự phản tư

Thành cần tự ghi phần đã review, điều học được và một lỗi AI đã phát hiện trước khi nộp retro cá nhân.
