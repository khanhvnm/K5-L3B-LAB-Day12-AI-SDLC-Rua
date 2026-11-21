# Changelog
## Unreleased

## phase-3 — Test Contract v1.2 (BREAKING)
- **Kho cá thể:** file kho, `gather_end.inventory`, `gather.hold`, `lost` đổi từ đếm theo loại sang mảng `{id, kind, fresh}`; kho đếm cũ bị từ chối (mã 2). Kho rỗng `{"items":[]}`.
- **Độ tươi:** `tuning.freshness`; giỏ hao 0.5/s, event `spoiled` khi xuống dưới 30.
- **Cập nhật fixture:** `{"items":{"ca_loc":1}}` → `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`; `"hold":["ca_loc","bong_sung"]` → `"hold":[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"bong_sung","fresh":100}]`. Trong test dùng `helpers.make_items([...])`, so loại bằng `kinds_of`, đếm bằng `count_kinds`.
- Test P1–P2 đổi vì schema (luật không đổi): `test_gather_rules`, `test_monsters`, `test_smoke_p1`, `test_python_starter_units`, `test_gather_v11`, `test_day`, `test_quan_rules::test_mon_moi_v11_va_nguyen_lieu_moi` — chỉ đổi fixture/so sánh sang cá thể.

## phase-2 — Test Contract v1.1
- Số chuẩn v1.1; thêm `ca_keo`, `keo_neo`, nút N5/N6, 3 món mới, 2 bếp/4 bàn.
- Cá bơi/phản xạ/sinh theo lịch (`fish_spawned`); Cá Sấu M1/M2, `monster_hit`, ngất do quái.
- Kế hoạch ngày D1–D5, Shop (oxygen/hp), `--mode day --days N`, pause ở cả ba mode.
- UI: menu, DayIntro, EveningIntro, DayResult, Shop, Summary, pause, HUD v1.1.

## phase-1 — Test Contract v1.0
- Lõi gather và quán, bàn giao kho hai tiến trình, HUD tối thiểu.
