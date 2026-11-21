# Hợp đồng tích hợp — v1.1 (Phase 2; v1.0 của Phase 1 vẫn là nền)

Hợp đồng này nối mô phỏng `gather`, mô phỏng `quan` và `client/ui`. Số liệu gameplay lấy từ `game.contract.json`; thay đổi schema hoặc giao diện phải được nhóm thống nhất trước và ghi lý do tại đây hoặc trong ADR.

## 1. Bàn giao file kho: gather → quan

File UTF-8 là một object JSON duy nhất, chỉ có khóa gốc `items`. `items` ánh xạ ID nguyên liệu sang số nguyên không âm. ID hợp lệ: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo` (v1.1 thêm `ca_keo`, `keo_neo`). Nguyên liệu không có trong object được hiểu là 0; khi ghi, bỏ khóa có lượng 0. Kho không áp giới hạn sức chứa của giỏ.

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

Ví dụ mẫu: [`inventory.sample.json`](inventory.sample.json).

### Quyền và thời điểm đọc/ghi

- `gather` sở hữu dữ liệu giỏ và là bên duy nhất ghi file bằng `--inventory-out`.
- Chỉ ghi đúng một lần khi phát `gather_end`; file phải khớp `data.inventory` trong event đó. Kết thúc vì ngất (`fainted`) thì ghi kho rỗng.
- Nếu chạm `--ticks` trước khi gameplay kết thúc, không tạo hoặc ghi đè file kho.
- Ghi file tạm cùng thư mục rồi thay thế nguyên tử.
- `quan` đọc kho bằng `--inventory`. Nếu không có `--inventory` và không có `scenario.quan.stock`, kho đầu ca là rỗng. Không dùng đồng thời `--inventory` và `scenario.quan.stock`.
- Sai schema, ID lạ, lượng âm/không nguyên hoặc xung đột nguồn kho: báo lỗi đầu vào, mã thoát `2`, trước khi tạo output.

### Smoke test bàn giao

Tạo `dock.json`:

```json
{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}
```

Tạo `dock-inputs.json`:

```json
{"frames":[{"tick":0,"interact":true}]}
```

Chạy hai tiến trình riêng:

```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

Kết quả mong đợi: `catch.json` là `{"items":{"bong_sung":2,"ca_loc":1}}`; event `gather_end` có cùng inventory; snapshot tick 0 của `quan.jsonl` có `stock` bằng `{"bong_sung":2,"ca_loc":1}`.

## 2. Giao diện mô phỏng – UI

- UI chỉ đọc `GET /state`: snapshot theo trường headless, kèm `meta` và `events`; UI không tự sửa state hoặc chạy bản sao luật gameplay.
- UI gửi trạng thái điều khiển qua `POST /input`, ví dụ `{"move":[0,1],"interact":false,"catch":false}`. `move` có hai số trong `[-1,1]`; `gather` hiểu là `[x,d]`, `quan` là `[x,z]`. Nút là boolean và gameplay xử lý cạnh lên false→true. `catch` chỉ có tác dụng trong `gather`.
- UI có thể bỏ qua trường snapshot không dùng. Headless không phụ thuộc UI, GPU, render hay đồng hồ thực.

## 3. Sự kiện tích hợp

Mô phỏng phát event; runner/headless ghi vào JSONL theo thứ tự xử lý. UI nhận event qua `/state`; `gather_end` là điểm kết thúc và chốt dữ liệu kho.

| Pha | Event | Dữ liệu | Phát → nhận |
|---|---|---|---|
| `gather` | `dive`, `surface` | `pos` sau di chuyển | sim → runner/JSONL, UI |
| `gather` | `oxygen_empty`, `choke` | `oxygen_ticks: 0`; `hp` sau trừ | sim → runner/JSONL, UI |
| `gather` | `gather`, `node_regrown` | `node_id`, `kind`, `amount`; `node_id` | sim → runner/JSONL, UI |
| `gather` | `fish_caught` | `fish_id`, `kind`, `yield` | sim → runner/JSONL, UI |
| `gather` | `hold_full` | `action`, `node_id` hoặc `fish_id`, `required`, `free` | sim → runner/JSONL, UI |
| `gather` | `faint` | `cause: "choke"`, `lost`, `hp: 0` | sim → runner/JSONL, UI |
| `gather` | `gather_end` | `reason`, `inventory` | sim → runner/JSONL, UI; inventory được ghi file theo mục 1 |
| `quan` | `customer_arrived`, `no_dish` | `order_id`, `table_id`, `dish_id`; hoặc `{}` | sim → runner/JSONL, UI |
| `quan` | `cook_started` | `stove_id`, `order_id`, `dish_id`, `items`, `base_price` | sim → runner/JSONL, UI |
| `quan` | `dish_ready`, `dish_picked` | `stove_id`, `order_id`, `dish_id` | sim → runner/JSONL, UI |
| `quan` | `served` | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip` | sim → runner/JSONL, UI |
| `quan` | `paid` | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` | sim → runner/JSONL, UI |
| `quan` | `customer_left` | `order_id`, `table_id`, `reason`, `reputation` | sim → runner/JSONL, UI |
| `quan` | `quan_end` | `reason`, `money`, `earned`, `shift_earned`, `reputation` | sim → runner/JSONL, UI |

Tên event, tick phát và cấu trúc dữ liệu tuân theo mục E–G của PRD-0. Mảng thực thể sắp theo ID; cùng seed và đầu vào phải cho output giống từng byte.

## 4. Thay đổi v1.1 (Phase 2, TICKET-02)

Chủ hợp đồng: Khánh. Số liệu nằm ở `game.contract.json` (`contract_version: "1.1"`), `chonoi/contract.py` kiểm dải hợp lệ.

### 4.1 Khóa tuning thêm/đổi

| Phạm vi | Khóa | Giá trị chuẩn |
|---|---|---|
| `gather` | `fish_initial` (đổi từ mảng sang **số**) | `8` |
| `gather` | `fish_speed`, `fish_turn_ticks`, `fish_max`, `fish_spawn_ticks`, `fish_spawn_clearance` | `1.5`, `120`, `12`, `360`, `1.0` |
| `gather` | `fish_x` (miền x), `fish_spawn_x` (danh sách x) | `[4,96]`, `[15,30,45,60,75,90]` |
| `gather` | `fish_depths`, `fish_spawn_depths`, `fish_weights` (map theo loài) | linh `[3,12]`/`[5,10]`/40, lóc `[8,20]`/`[10,16]`/30, kèo `[22,28]`/`[24,27]`/30 |
| `gather` | `fish_yield` đủ 3 loài; `nodes` thêm N5, N6 (`keo_neo`) | linh 3, lóc 1, kèo 2; N5 `[76,0]`, N6 `[90,0]` |
| `gather.monsters` | `species.ca_sau`, `spawns[]` (M1 từ Ngày 1, M2 từ Ngày 3), `invuln_ticks: 90`, `loss_ratio: 0.5` | xem file. `recoil_dist` = quãng lùi tổng (m); mỗi bước lùi `recoil_dist / recoil_ticks` = 2/60 m |
| `quan`, `menu` | thêm B2, T2–T4; món `canh_chua_ca_loc`, `ca_keo_nuong`, `lau_mam` | dữ liệu, không hard-code |
| `day_plan` | 5 object `{day, dishes, ingredients}`; `ingredients` = Σ công thức × số suất (validator tính lại và so khớp) | D1–D5 theo ticket |
| `shop` | `{max_ticks: 600, upgrades: {oxygen[], hp[]}}`, mỗi cấp `{level, price, oxygen_max_s|hp_max}` | oxygen 200→45 s, 400→60 s; hp 250→4, 500→5 |

### 4.2 Gather: snapshot, sự kiện, thứ tự

- Snapshot thêm `monsters[]` (rỗng tới khi lát Cá Sấu ghép) và `fish[].age_ticks` (số bước đã bơi; cá mới sinh = 0).
- Event `fish_spawned {id, kind, pos}` khi sinh theo lịch (`phase_tick = 360·k`, sau khi cá bơi, còn dưới trần và có điểm cách mọi đàn đang sống > 1 m; hết điểm thì bỏ lượt).
- Mỗi tick (theo §4.5 ticket): đồng hồ/cooldown/nút mọc lại → bơi, oxy, ngạt → quái (`_update_monsters`) → tương tác (bến trước hái) → bắt cá (theo vị trí cá trước khi bơi) → hết giờ → nếu còn giờ: cá bơi → sinh cá.
- Cá bơi theo id: tăng `age_ticks`; bước thứ `120·k` đổi hướng theo luồng RNG `fish_swim` trước khi đi; chạm mép thì phản xạ phần quãng đường còn lại, đảo thành phần vuông góc với mép (chạm góc đảo cả hai).
- Sinh cá dùng luồng RNG `fish_spawn`: loài theo trọng số chuẩn hóa trên các loài còn điểm hợp lệ → chọn đều điểm của loài → hướng theo seed. Đàn đầu ca dùng cùng thủ tục (8 đàn, 8 điểm khác nhau).
- `random_fish: false`: cá fixture đứng yên, không sinh. Khai `fish` khi cờ bật: thay đàn đầu ca, vẫn bơi/sinh.

### 4.3 Shop (`chonoi/sim/shop.py`)

`ShopSim.step(buy, shop_done)` mỗi tick Shop chạy (bộ điều phối không gọi khi pause). Một `buy` được xử lý trước cạnh `shop_done`, kể cả bước cuối; `shop_done` thắng hết giờ. Event: `bought {upgrade, level, price, money}`, `buy_failed {action, reason: funds|max_level|unknown}`, `shop_end {reason: done|time}`. Mở rộng chưa bật (`weapon`, `net`, `buy:`, `sell:`) → `buy_failed unknown`. `active_stats(tuning, active_upgrades)` trả oxy/Máu theo cấp đang áp dụng; bộ điều phối chỉ sao `upgrades` → `active_upgrades` khi dựng Ngày mới.

### 4.4 Phần còn thuộc lát khác

Cá Sấu (`_update_monsters`), chế độ `day`/pause/khối scenario `day`, input `buy`/`shop_done`/`pause`, HUD: xem `docs/plan/phase-2.md`.

## 5. Thay đổi v1.2 (Phase 3, TICKET-03) — BREAKING

Chủ hợp đồng: Khánh. `game.contract.json`: `contract_version: "1.2"`, thêm `tuning.freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.

### 5.1 Kho cá thể (thay mục 1)

```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```

- Đúng khóa gốc `items`, giá trị là **mảng** cá thể có đúng ba khóa `{id, kind, fresh}`; kho rỗng `{"items":[]}`. `id` chuỗi khác rỗng, duy nhất; `kind` thuộc danh mục nguyên liệu; `fresh` số hữu hạn trong `[0, 100]`.
- Contract v1.2 **từ chối file kho đếm** (`{"items":{...}}`) và mọi sai schema → mã 2, trước khi tạo output. Không hỗ trợ song song v1.1.
- Ghi: đúng một lần khi `gather_end`, file tạm cùng thư mục rồi thay thế nguyên tử, **sắp theo id**, `fresh` là float đầy đủ chữ số (đọc lại giữ đúng nhánh ngưỡng 30). Ngất ghi `{"items":[]}`; chạm `--ticks` trước `gather_end` không đụng file đích. `gather_end.data.inventory` cùng schema (JSONL làm tròn 3 chữ số).
- Quán nhận nguyên số lượng, id và độ tươi, kể cả hàng ươn. Sức chứa chỉ áp lên giỏ.

### 5.2 API Python (`chonoi/inventory.py`) cho các lát

- Cá thể nội bộ `{"id", "kind", "fresh": Fraction}` — `Fraction` để so ngưỡng và floor giá chính xác. Không ghi `Fraction` ra JSON: dùng `item_out` / `items_out(items, ordered=True|False)`.
- `validate_individuals(arr, kinds, name)` (JSON → nội bộ), `read_inventory` / `write_inventory`, `decay(items, amount, threshold, location)` → event `spoiled` theo id, `decay_per_tick(tuning, "gather"|"quan")`, `spoiled_below(tuning)`, `is_spoiled`, `counts(items, threshold=None)`.
- Id cá thể họ `I` cấp bằng `IdAllocator.new("I")` theo thứ tự vào giỏ; trong `day` dùng **một allocator chung** nên id tăng xuyên pha và Ngày. `GatherSim(..., renew_hold_ids=True)` cấp id mới cho mẫu `gather.hold` ở Ngày ≥ 2 (giữ kind/fresh).

### 5.3 Gather

- `gather.hold` (scenario) và snapshot `hold`: mảng cá thể theo **thứ tự vào giỏ** (cuối mảng mới nhất). Hàng mới `fresh = initial`, hao từ bước sau.
- Đầu bước (cùng nhóm đồng hồ/cooldown/hồi nút): giỏ hao `gather_decay_per_s / tick_hz`, kẹp đáy 0; `spoiled {item_id, kind, location: "hold"}` đúng một lần khi đi từ ≥ 30 xuống < 30, nhiều cá thể theo id.
- `monster_hit.lost` và `faint.lost` là mảng cá thể theo thứ tự bỏ LIFO.

### 5.4 Chưa đổi (thuộc lát khác)

- Quán (Trà): `quan.stock`, `customers[].reserved`, snapshot `stock`, `cook_started.items`, hao 0.25/s, giữ theo id, giá theo tươi. **Tạm thời** `QuanSim` nhận kho cá thể qua adapter (đếm hàng chưa ươn) để `main` chạy được — xóa adapter khi lát Quán xong.
- Day/Shop/HUD (Thành): Shop `stock` cá thể, `delivered` (EveningIntro) hiện là số lượng theo loại, HUD độ tươi.
