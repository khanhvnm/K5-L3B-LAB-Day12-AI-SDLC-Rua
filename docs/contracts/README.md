# Hợp đồng tích hợp Phase 1 — v1.0

Hợp đồng này nối mô phỏng `gather`, mô phỏng `quan` và `client/ui`. Số liệu gameplay lấy từ `game.contract.json`; thay đổi schema hoặc giao diện phải được nhóm thống nhất trước và ghi lý do tại đây hoặc trong ADR.

## 1. Bàn giao file kho: gather → quan

File UTF-8 là một object JSON duy nhất, chỉ có khóa gốc `items`. `items` ánh xạ ID nguyên liệu sang số nguyên không âm. ID hợp lệ: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Nguyên liệu không có trong object được hiểu là 0; khi ghi, bỏ khóa có lượng 0. Kho không áp giới hạn sức chứa của giỏ.

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
