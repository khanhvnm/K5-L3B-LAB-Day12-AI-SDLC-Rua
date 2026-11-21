# Changelog
## Unreleased

## phase-4 / v1.0.0 — Test Contract v1.3
- Manifest `contract_version: "1.3"`, thêm `bench_cmd` (`python3 -m chonoi.bench`) và `soak_cmd` (`python3 -m chonoi.soak`); `run_cmd` mở vòng ngày 5 Ngày. Gameplay, tuning, kho, JSONL giữ v1.2.
- Benchmark có render: `chonoi/bench.py` + chế độ `?bench=` trong `chonoi/web/index.html`, Chrome/Chromium/Edge headless 1280×720, làm nóng 3 s, ghi `bench.json` 5 trường.
- Test đổi vì phiên bản (luật không đổi): `test_fresh_v12::test_version_and_freshness_block`, `test_gather_v11::test_version_and_standard_numbers` nhận thêm `"1.3"`.

## phase-3 — Test Contract v1.2 (BREAKING)
- **Kho cá thể:** file kho, `gather_end.inventory`, `gather.hold`, `lost` đổi từ đếm theo loại sang mảng `{id, kind, fresh}`; kho đếm cũ bị từ chối (mã 2). Kho rỗng `{"items":[]}`.
- **Độ tươi:** `tuning.freshness`; giỏ hao 0.5/s, kho quán 0.25/s (kể cả hàng giữ, không hao ở Shop/khi pause), event `spoiled {item_id, kind, location}` khi xuống dưới 30.
- **Quán:** `quan.stock` mảng cá thể, `customers[].reserved` mảng id; giữ chỗ lấy cá thể tươi nhất; hàng giữ vừa ươn → nhả và giữ lại một lần; `base_price` theo trung bình fresh; `cook_started.items` mảng cá thể.
- **Day/HUD:** id cá thể tăng xuyên pha/Ngày, Shop `stock` cá thể, HUD hiển thị độ tươi và hàng ươn.
- Cập nhật fixture quán: `"stock":{"ca_loc":1}` → `"stock":[{"id":"I1","kind":"ca_loc","fresh":100}]`; `"reserved":{"ca_loc":1}` → `"reserved":["I1"]`.
- **Cập nhật fixture:** `{"items":{"ca_loc":1}}` → `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`; `"hold":["ca_loc","bong_sung"]` → `"hold":[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"bong_sung","fresh":100}]`. Trong test dùng `helpers.make_items([...])`, so loại bằng `kinds_of`, đếm bằng `count_kinds`.
- Test P1–P2 đổi vì schema (luật không đổi): `test_gather_rules`, `test_monsters`, `test_smoke_p1`, `test_python_starter_units`, `test_gather_v11`, `test_day`, `test_quan_rules::test_mon_moi_v11_va_nguyen_lieu_moi` — chỉ đổi fixture/so sánh sang cá thể.

## phase-2 — Test Contract v1.1
- Số chuẩn v1.1; thêm `ca_keo`, `keo_neo`, nút N5/N6, 3 món mới, 2 bếp/4 bàn.
- Cá bơi/phản xạ/sinh theo lịch (`fish_spawned`); Cá Sấu M1/M2, `monster_hit`, ngất do quái.
- Kế hoạch ngày D1–D5, Shop (oxygen/hp), `--mode day --days N`, pause ở cả ba mode.
- UI: menu, DayIntro, EveningIntro, DayResult, Shop, Summary, pause, HUD v1.1.

## phase-1 — Test Contract v1.0
- Lõi gather và quán, bàn giao kho hai tiến trình, HUD tối thiểu.
