# Bằng chứng lát Day/Pause/UI — TICKET-02

Phạm vi: working tree `p2/day-ui` trên nền `06fac33`. Gather và Quán chạy từ repo; kế hoạch ngày và Shop chỉ là fixture trong `tests/test_day.py`. Branch vẫn dùng manifest v1.0.

```powershell
$env:PYTHONPATH='tests;.'
python3 -m unittest discover -s tests -v
node --test tests/test_ui.js
git diff --check
```

- Python **69/69** (đã gồm wrapper Node); Node **10/10** chạy riêng. Test day kiểm hai lần JSONL trùng từng byte, kho bàn giao tại snapshot đổi pha, ngất, pause/resume và input cùng bước, mua/đóng đúng tick cuối qua giao diện Shop, nâng cấp áp dụng ngày sau, fixture xung đột trả mã 2 và không để lại JSONL dở.
- Headless: chạy `runner.run("day", day_tuning(600), {}, 1, [], 22200, out, 10)` với `mock_shop()` và `Workdir()`: **22.200 tick trong 0,232 giây**, kết thúc `days_complete`. Đây là phép đo khung điều phối với luật Gather/Quán hiện có.
- Chrome headless thật, viewport 1280×720: bấm Chơi → DayIntro → Gather → Esc/tiếp tục → E cập bến → EveningIntro → Quán → DayResult → Shop → mua oxy/đóng → Summary. Kiểm đồng hồ và `sim_tick` không đổi trong 280 ms pause, nhận đúng một cá lóc tại quán và Summary có `days_complete`. Đo `requestAnimationFrame` trong khoảng 1 giây mỗi cảnh: **108,8 FPS** Gather, **119,8 FPS** Quán trên máy thử. Các test Node kiểm thêm tự chuyển DayIntro sau 4 s và cỡ chữ Canvas ≥ 18 px. Hồ sơ Chrome và thư mục dữ liệu test đã dọn.
- Smoke kho hai tiến trình Gather → Quán vẫn qua test `test_inv_01_gather_writes_inventory_quan_reads_it` trên v1.0.

Bàn giao: `DaySession` nhận `tuning.day_plan`, `tuning.shop` và `chonoi.sim.shop.ShopSim(tuning, scenario, streams, ids)`. Shop sở hữu luật mua rồi đóng và phát `bought`/`buy_failed`/`shop_end`. Runner giữ thứ tự event của Shop. Cần chạy lại smoke D1–D5, regression và đo hiệu năng với preset/Shop thật cùng các lát cá, Cá Sấu và Quán v1.1 trước khi nghiệm thu Phase 2.

## Kiểm lại khi ghép main v1.1

Nền ghép: `p2/day-ui@5742593` và `main@d5c4b54`. Điều phối dùng `ShopSim.step(buy, shop_done)`, `active_stats`, module `dayplan`, `GatherSim(..., day=...)` và `QuanSim(..., plan_dishes=...)`. Các kết quả dưới đây dùng preset và Shop thật; kết quả phía trên là lịch sử trước khi ghép.

- `python3 -m unittest tests.test_day -v`: **8/8**, bao gồm CLI D1–D5, M2 xuất hiện từ D3, mua/đóng cùng tick cuối, chuyển cấp oxy sang Ngày sau, pause và JSONL tất định. Chuẩn bị `$env:PYTHONPATH='tests;.'` trước khi chạy.
- `python3 -m unittest discover -s tests`: **123/123** trong **39,935 giây**, đã gồm wrapper Node. `node --test tests/test_ui.js` chạy riêng: **10/10**.
- `python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out out.jsonl`: kết thúc `days_complete` đúng tick **22.200** trong **1,541 giây**, gồm khởi động CLI và ghi JSONL.
- Chrome headless 1280×720, ca sáng/tối rút ngắn bằng scenario: đi hết menu → DayIntro → gather/pause → EveningIntro → quán → DayResult → Shop thật (mua Bình oxy) → Summary. Đo **110,8 FPS** Gather và **119,8 FPS** Quán bằng `requestAnimationFrame` trên máy thử. Server dừng và hồ sơ tạm đã dọn.
