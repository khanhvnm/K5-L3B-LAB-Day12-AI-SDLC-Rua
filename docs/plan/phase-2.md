# Kế hoạch Phase 2 — TICKET-02 "Một ngày ở chợ nổi"

**Mục tiêu:** Trước 1:55, chơi trọn vòng ngày (menu → DayIntro → gather → quán → DayResult → Shop, D1–D5) với số chuẩn Test Contract v1.1, `--mode day` chạy headless, smoke tích hợp có bằng chứng, tag `phase-2` trên `main`.

**Phạm vi:** chỉ lõi (mục 1–2 của ticket). Nhóm 3 người nên **không làm mở rộng** (lao xua, vợt, rắn, cháy món, Chợ Chú Sáu, Cá Hô, settings); chỉ làm khi lõi đã đúng và còn giờ, ghi trong README.

## Mã tiêu chí (AC-P2)

| AC | Nội dung | Lát |
|---|---|---|
| AC-P2-01 | `contract_version: "1.1"`, `game.contract.json` + preset theo số chuẩn (1.1, 1.3), 6 nguyên liệu, 6 món là dữ liệu | A |
| AC-P2-02 | Gather: vùng nước 100×30, nút N1–N6, oxy 30 s, bơi/hái/bắt theo số chuẩn | A |
| AC-P2-03 | Cá bơi (đổi hướng mỗi 120 bước, phản xạ mép), sinh cá theo lịch 360·k, `fish_spawned`, `random_fish:false`, `age_ticks` | A |
| AC-P2-04 | Cá Sấu M1/M2 (patrol/chase/recoil), hit, bất tử 90 tick, `monster_hit`, `faint cause:"monster"`, ngất vẫn mở quán với kho rỗng | B |
| AC-P2-05 | Quán 2 bếp, 4 bàn, khách 120+900k, 6 món, boa/uy tín/điểm theo số chuẩn; lọc menu theo `day_plan` khi chạy day | C |
| AC-P2-06 | `day_plan` D1–D5 đúng bảng, `ingredients` tính từ công thức × suất, event `day_plan` | C |
| AC-P2-07 | Shop: oxygen/hp, `bought`/`buy_failed`, `shop_done`, tự đóng 600 tick, `shop_end`, cấp có hiệu lực từ Ngày sau | D |
| AC-P2-08 | `--mode day --days N`: đổi pha đúng thứ tự (§4.5), snapshot có `day`, `day_plan`, `upgrades`, `active_upgrades`, `days_completed`, `reason:"days_complete"`, tối đa 22.200 tick/Ngày, ≤ 20 s | D |
| AC-P2-09 | Pause (`pause` cả 3 mode): `paused`/`resumed`, đóng băng mọi timer kể cả Shop | D |
| AC-P2-10 | Scenario: khối `day`, `gather.monsters[]`, `gather.fish[]`, cấm `quan.stock`/`quan.reputation` khi day, mã 2 khi mâu thuẫn | D (+ A, B, C phần của mình) |
| AC-P2-11 | UI: menu chính, DayIntro, EveningIntro, DayResult, Summary, pause, HUD sáng/tối đủ trường, chữ ≥ 18 px ở 1280×720, ≥ 30 FPS | E |
| AC-P2-12 | Regression P1 với số chuẩn; test cũ đổi phải ghi lý do | Cả nhóm |

## Phân việc

| Lát | Việc | Phụ trách | Người dự phòng |
|---|---|---|---|
| **A** Gather số chuẩn + cá | `sim/gather.py`: số chuẩn 1.1, nút N5/N6, cá bơi/phản xạ/sinh theo seed, `fish_spawned` | **Khánh** | Trà |
| **B** Cá Sấu, Máu, ngất | `sim/gather.py` (hoặc `sim/monsters.py`): M1/M2, patrol/chase/recoil, hit/LIFO/bất tử, faint | **Trà** từ phút 20 (sau lát C); Khánh tạo sẵn móc `monsters[]` ở lát A để ghép | Khánh |
| **C** Quán + kế hoạch ngày | `sim/quan.py` + preset: B2, T2–T4, 3 món, 2 nguyên liệu mới; `day_plan` D1–D5 từ công thức; lọc menu theo kế hoạch | **Trà** (phút 0–20) | Thành |
| **D** Day, Shop, pause | Chế độ `day` ở `headless`/`runner`/`scenario`: máy trạng thái pha, `sim/shop.py`, pause, khối `day`, output v1.1 | **Thành** (khung + pause), **Khánh** (hợp đồng v1.1, Shop luật khi xong lát A) | Khánh |
| **E** UI/HUD | `chonoi/web/index.html`, `live.py`: menu, các màn intro/result/summary, pause, HUD đủ trường, kiểm FPS | **Thành** (sau khung D, từ phút 25) | Trà |
| **I** Tích hợp, QA, tag | Hợp đồng `docs/contracts/` v1.1, smoke, `docs/verification/phase-2.md`, retro, tag | **Khánh** | — |

Lát D là đường găng: Thành dựng khung day với fixture cố định ngay từ phút 5 (gather/quan hiện có), rồi thay dần bằng lát A/B/C.

## Lịch theo phút (bám ticket)

| Phút | Việc | Ai |
|---|---|---|
| 0–5 | Chốt giao diện chuyển pha, tên khóa v1.1, mã AC; ghi `docs/clarify.md` | Cả nhóm; Khánh chốt |
| 5–20 | Khánh: sửa `game.contract.json` + hợp đồng v1.1 **đầu tiên** (mọi người phụ thuộc), rồi lát A. Trà: lát C. Thành: khung D + pause. | Khánh, Trà, Thành |
| 20 | Smoke `gather --inventory-out` → `quan --inventory`, so kho tick 0, lưu `docs/proof/phase-2/integration.*`. Standup 3 phút, điều người sang lát trễ. | Khánh dẫn |
| 20–35 | Khánh: hoàn thiện A, viết luật Shop. Trà: lát B. Thành: hoàn thiện D, bắt đầu E. | |
| 35–45 | Smoke `day --days 1`, nhiều Ngày kiểm cấp nâng cấp, regression P1 | Cả nhóm; Khánh ghi |
| 45–50 | Retro nhanh trong `docs/retro.md` (một hành động có người nhận) | Cả nhóm |
| 50–55 | Dự phòng, đẩy `phase-2` | Khánh |

## Quy ước làm việc

- Mỗi người một nhánh `p2/<lát>`, PR vào `main`; Khánh tích hợp. Mỗi lát một agent, đưa cho agent đúng đoạn ticket của lát và hợp đồng v1.1.
- Chỉ Khánh sửa `game.contract.json` và `docs/contracts/` (đã báo cả nhóm: đây là thay đổi bắt buộc của v1.1). Các số không hard-code trong luật, đọc từ contract/dữ liệu.
- RNG chỉ qua `Streams`; thứ tự xử lý theo §4.5 của ticket.
- Test cũ phải đổi vì số chuẩn thì ghi lý do trong commit; không sửa test để xanh khi luật sai.
- Mỗi người ≥ 3 commit có nội dung trong phase này (Thành và Trà còn thiếu ở Phase 1); làm cặp thì ghi `Co-authored-by:`.
- Bằng chứng ở `docs/proof/phase-2/`; ma trận AC → proof → kết quả ở `docs/verification/phase-2.md`.

## Câu hỏi cần ghi `docs/clarify.md` (hỏi Anh Năm nếu bí)

1. Q1–Q6 của Phase 1 (khách `reserved`, `base_price`/`tip`, `stoves[].dish`, `paid.reason`, chọn đều, làm tròn uy tín) còn đúng với số chuẩn v1.1 không.
2. Khi ngất (kho rỗng) thì EveningIntro và quán vẫn chạy 180 s với `no_dish` — xác nhận.
3. "Tự đóng sau 600 tick hoạt động" của Shop: pause có tính vào 600 tick không (theo ticket thì không).
4. Ngày 5 sau Shop: `days_complete` phát cùng tick `shop_end`.

## Rủi ro

- Phạm vi lớn cho 55 phút với 3 người: ưu tiên (1) hợp đồng + số chuẩn, (2) `day` chạy được dù dùng gather/quan cũ, (3) Cá Sấu, (4) HUD đẹp. Cắt mở rộng hoàn toàn.
- Lát D phụ thuộc mọi lát khác: dùng fixture cố định để tích hợp sớm, tránh dồn tích hợp vào phút 35.
- Đổi số chuẩn làm vỡ test Phase 1: sửa test theo số mới và ghi lý do, không nới luật.
- Hiệu năng `day` ≤ 20 s cho 22.200 tick: tránh quét O(n²) trong cá/quái từng tick.
