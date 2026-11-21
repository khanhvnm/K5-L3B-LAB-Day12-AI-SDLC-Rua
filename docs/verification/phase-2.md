# Kiểm chứng Phase 2

Phạm vi hiện tại: lát D/E trên `p2/day-ui`. Xem [lệnh và bằng chứng](../proof/phase-2/day-ui.md).

| AC | Bằng chứng hiện có | Kết quả |
|---|---|---|
| AC-P2-01–04 | Preset, lịch cá, Cá Sấu | Chờ lát A/B và hợp đồng v1.1. |
| AC-P2-05–06 | `test_plan_filters_menu_without_capping_sales`, `test_two_days_jsonl_pause_buy_order_and_handoff` | Qua lọc menu, tính nguyên liệu và event với fixture; chờ thực đơn và kế hoạch chuẩn do Trà cung cấp. |
| AC-P2-07 | `test_faint_handoff_and_last_tick_shop`, JSONL hai ngày | Qua giao diện Shop và hiệu lực vào ngày sau với fixture; chờ luật Shop thật. |
| AC-P2-08–09 | JSONL hai ngày, pause hai mode độc lập và Shop, benchmark 22.200 tick | Qua với fixture; chờ đo lại trên bản tích hợp v1.1. |
| AC-P2-10 | `test_bad_day_scenarios_do_not_publish_partial_output` | Qua xác thực khối day và mâu thuẫn kho; cần chạy fixture quái/cá với sim v1.1. |
| AC-P2-11 | Node + Chrome headless 1280×720 | Qua vòng UI và mốc FPS trên máy thử bằng fixture. |
| AC-P2-12 | Full suite và smoke kho hai tiến trình | Qua với preset v1.0. Điều chỉnh test từ chối `day` chỉ áp dụng cho manifest v1.0 vì v1.1 bổ sung mode này. |
