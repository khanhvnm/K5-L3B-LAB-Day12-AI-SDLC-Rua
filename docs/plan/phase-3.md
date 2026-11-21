# Kế hoạch Phase 3 — TICKET-03 "Mùa Nước Nổi" (Test Contract v1.2)

**Mục tiêu:** Trước 2:30, chuyển kho đếm sang **kho cá thể có độ tươi** ở cả file và trong `day`, hao tươi/ươn, giữ chỗ theo id, giá theo tươi, HUD độ tươi. Gắn tag `phase-3` trên `main`.

**Phạm vi:** chỉ lõi. Nhóm 3 người **không làm mở rộng** (dòng lũ, khách đặt trước); manifest không khai `extensions`.

## Quyết định đổi schema (chốt phút 0–7)

- **Breaking change:** file kho, `gather_end.data.inventory`, `gather.hold`, `quan.stock`, `customers[].reserved`, `cook_started.items`, `lost` đổi từ đếm theo loại sang **mảng cá thể** `{id, kind, fresh}`. Kho rỗng `{"items":[]}`.
- **Không giữ hai phiên bản song song:** contract v1.2 từ chối file kho đếm (mã 2). Lý do: 35 phút, một đầu đọc/ghi duy nhất (`chonoi/inventory.py`) nên đổi một lần là đủ.
- **Biểu diễn trong sim:** độ tươi lưu nguyên **240 đơn vị/điểm** (`fresh_units`), gather −2/tick, quán −1/tick; ngưỡng ươn so `units < 30×240`. File/snapshot xuất `fresh = units / 240` (float, đủ chính xác khi đọc lại). Đọc file: `units = round(fresh × 240)` — fixture ticket (100, 97.5, 30) biểu diễn chính xác.
- **Id cá thể:** `IdAllocator` họ `I`, cấp theo thứ tự vào giỏ, **một allocator dùng chung xuyên pha và Ngày** trong `day` (đã có `self.ids` dùng chung). Ngày ≥ 2 cấp id mới cho mẫu `gather.hold`.
- **Thứ tự tích hợp để `main` luôn chạy:** (1) Khánh merge schema + adapter + contract 1.2 kèm sửa tối thiểu gather/quán để compile và test cũ được cập nhật → (2) Trà (quán) và Khánh (gather) làm luật tươi song song trên schema đã chốt → (3) Thành HUD + `day` → (4) smoke, regression, tag.

## Mã tiêu chí (AC-P3)

| AC | Nội dung |
|---|---|
| AC-P3-01 | `contract_version:"1.2"`, khối `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}` |
| AC-P3-02 | Schema kho cá thể: đọc/ghi file, mã 2 cho kho đếm/sai schema/kind lạ/id trùng/fresh ngoài [0,100]; ghi một lần khi `gather_end`, nguyên tử, sắp theo id; ngất ghi `{"items":[]}`; chạm `--ticks` giữ nguyên đích |
| AC-P3-03 | Gather: hàng mới fresh 100, hao 0.5/s từ bước sau, đầu bước; `spoiled {item_id, kind, location:"hold"}` đúng một lần theo id; LIFO `lost` là mảng cá thể; scenario `hold` là mảng cá thể |
| AC-P3-04 | Quán: hao 0.25/s kể cả hàng giữ; `spoiled location:"stock"`; giữ chỗ theo id (tươi nhất, hòa id); hàng vừa ươn → nhả toàn bộ phần giữ, thử giữ lại một lần theo `order_tick` rồi id bàn, thiếu → `unfulfillable` |
| AC-P3-05 | Giá: `base_price = floor(giá × trung bình fresh / 100)` khi bắt đầu nấu, tiêu đúng id đang giữ; boa trên giá đã chốt; `cook_started.items` mảng cá thể sắp theo kind rồi id |
| AC-P3-06 | Scenario quán: `stock` mảng cá thể, `reserved` mảng id; id duy nhất giữa các nơi chứa; phần giữ trỏ cá thể chưa ươn, đủ công thức, không dùng chung; thiếu `reserved` thì tự cấp; sai → mã 2 |
| AC-P3-07 | `day`: bàn giao trong cùng tick đổi pha không hao thêm; Shop `stock` mảng cá thể, không hao; id tăng xuyên Ngày; pause dừng hao |
| AC-P3-08 | HUD hiển thị độ tươi/ươn ở giỏ và kho quán |
| AC-P3-09 | Smoke ticket: fixture fresh 30 → `spoiled` tick 1; smoke bàn giao fresh 100 → quán tick 0 khớp id/kind/fresh (99.99166…) |
| AC-P3-10 | Regression P1–P2 còn hiệu lực đạt; test đổi ghi lý do |

## Phân tích tác động và phân việc

| Lát | Module | File cần đổi | Test bị ảnh hưởng | Phụ trách |
|---|---|---|---|---|
| **S** Schema/adapter (đi trước) | Contract, kho | `game.contract.json` (1.2, `freshness`), `chonoi/contract.py`, `chonoi/inventory.py` (cá thể, `units`↔`fresh`, đọc/ghi, kiểm), `chonoi/headless.py`, `chonoi/runner.py` (ghi kho), `docs/contracts/README.md` (mục 5) | Đổi: `test_smoke_p1` (bàn giao, file kho sai), `test_python_starter_units`. Thêm: `tests/test_inventory_v12.py` (schema, mã 2, round-trip ngưỡng 30) | **Khánh** (phút 0–12) |
| **G** Lặn | Gather | `chonoi/sim/gather.py` (hold cá thể, id `I`, hao đầu bước, `spoiled`, `lost` cá thể), `chonoi/sim/monsters.py` (rơi LIFO dùng cá thể — chỉ đổi kiểu phần tử), `chonoi/scenario.py` (gather.hold) | Đổi: `test_gather_rules` (lost/hold), `test_monsters` (lost), `test_gather_v11` (hold). Thêm: `tests/test_fresh_gather.py` (ngưỡng 30 tick 1, đúng một lần, nhiều cá thể theo id, LIFO) | **Khánh** (phút 12–25) |
| **Q** Quán | Quán | `chonoi/sim/quan.py` (stock cá thể, hao, `spoiled`, giữ theo id, nhả/giữ lại, giá theo tươi, `cook_started.items`), `chonoi/scenario.py` (quan.stock, reserved id, kiểm mâu thuẫn) | Đổi: phần lớn `test_quan_rules` (stock/reserved dạng mới; giá 60 → theo fresh). Thêm: `tests/test_fresh_quan.py` (ươn giữa ca, giữ lại thành công/thất bại, giá floor, boa trên giá chốt) | **Trà** (phút 5–25; dùng helper `inventory` của lát S, có thể viết test trước) |
| **D** Day + HUD | Day, UI | `chonoi/day.py` (bàn giao cá thể, id xuyên Ngày, mẫu `hold` Ngày ≥ 2 cấp id mới, Shop stock), `chonoi/sim/shop.py` (stock cá thể, không hao), `chonoi/web/index.html` (độ tươi: số/thanh, nhãn "ươn" ở giỏ và kho), `chonoi/live.py` nếu cần | Đổi: `test_day` (stock/hold), `test_shop_rules` (stock), `tests/test_ui.js` (HUD tươi). Thêm test: id tăng xuyên Ngày, bàn giao không hao thêm, pause dừng hao | **Thành** (phút 7–28) |
| **I** Tích hợp, QA, tag | QA | `CHANGELOG.md` (breaking change, cách cập nhật fixture), `docs/proof/phase-3/`, `docs/verification/phase-3.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md` | Full suite, smoke ticket, smoke `day` | **Khánh** (phút 25–35) |

Người dự phòng: Khánh đỡ Quán nếu Trà trễ ở phút 20; Trà đỡ `day` nếu Thành trễ; Thành kiểm HUD trên bản tích hợp.

## Lịch theo phút

| Phút | Việc | Ai |
|---|---|---|
| 0–7 | Đọc ticket, chốt quyết định schema ở trên, ghi `docs/clarify.md`; Khánh mở nhánh `p3/schema` | Cả nhóm; Khánh chốt |
| 7–12 | Khánh merge lát S (adapter + contract 1.2 + sửa tối thiểu để suite xanh). Trà/Thành viết test mới trên schema đã chốt trong lúc chờ | Khánh |
| 12–25 | Song song: G (Khánh, `p3/gather`), Q (Trà, `p3/quan`), D (Thành, `p3/day-ui`) | |
| 20 | Smoke bàn giao kho theo ticket trên `main` (gather fresh 100 → quan `--ticks 0`). Standup 3 phút | Khánh dẫn |
| 25–30 | Merge Q, D; smoke `day --days 2`, regression, bằng chứng `docs/proof/phase-3/` | Khánh; chủ lát sửa lỗi |
| 30–32 | CHANGELOG, verification, retro nhanh (điều rút ra từ lần đổi kho) | Khánh ghi, cả nhóm |
| 32–35 | Dự phòng; tag `phase-3` trên `main`, push trước 2:30 | Khánh |

## Quy ước

- Nhánh `p3/<lát>`, PR vào `main` (cần 1 approval + CI). Mỗi người ≥ 2 commit có nội dung trong phase này; **Thành ưu tiên commit nhỏ theo từng phần**.
- Số liệu tươi đọc từ `tuning.freshness`, không hard-code 0.5/0.25/30.
- Thứ tự trong tick theo ticket mục 1 "Thứ tự trong tick"; quán: đồng hồ → hao tươi + `spoiled` theo id → xử lý giữ chỗ bị ươn → món chín → di chuyển/tương tác → thanh toán/kiên nhẫn → khách mới.
- Không sửa test cho xanh khi luật sai; test đổi vì schema ghi lý do trong commit và `docs/verification/phase-3.md`.

## Câu hỏi ghi `docs/clarify.md`

1. Khách mới đến: dùng cá thể khả dụng tươi nhất — "khả dụng" có loại trừ hàng ươn (ngầm hiểu có)?
2. Món chỉ khả dụng cho khách chọn khi đủ cá thể **chưa ươn** chưa giữ — xác nhận.
3. `base_price` khi `fresh` trung bình làm floor ra 0 (hàng gần ươn không thể vì < 30 không nấu; tối thiểu 30% giá) — không cần xử lý đặc biệt.
4. Ngày ≥ 2 trong `day`: mẫu `gather.hold` cấp id mới "theo thứ tự mảng" — fresh lấy theo mẫu, không phải 100.
5. Hỏi lại P2-05 (bất tử 90 tick) nếu chưa hỏi.

## Rủi ro

- Đổi schema chạm gần như mọi test → lát S phải xong trước phút 12, nếu không cả nhóm bị chặn. Giảm rủi ro: Khánh chỉ đổi kiểu dữ liệu và sửa test tối thiểu, chưa thêm luật tươi.
- `test_quan_rules` lớn nhất, nhiều fixture `stock` dạng đếm: viết helper `items(kind=n, ...)` trong `tests/helpers.py` sinh mảng cá thể để sửa nhanh.
- Sai số float ở ngưỡng 30 và floor giá: bắt buộc dùng đơn vị nguyên (240/điểm).
- Hiệu năng: hao tươi mỗi tick trên ≤ vài chục cá thể, không đáng kể.
