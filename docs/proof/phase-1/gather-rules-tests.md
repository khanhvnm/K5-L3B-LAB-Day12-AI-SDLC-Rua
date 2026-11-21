# Phase 1 — headless Gather rules

## Kết quả do Khánh chạy

Môi trường: PowerShell, repo `K5-L3B-LAB-Day12-AI-SDLC-Rua`.

Lệnh kiểm tra tập trung:

```powershell
$env:PYTHONPATH = "tests;."
python3 -m unittest discover -s tests -p "test_gather_rules.py" -v
```

Kết quả: **Ran 10 tests in 2.301s — OK**.

Các case kiểm tra oxy cạn, hồi oxy khi lên mặt nước, ngạt/ngất và mất giỏ theo LIFO; chọn nút gần nhất và tie-break theo ID; mọc lại rồi hái cùng tick; giỏ đầy khi hái/bắt cá; bắt cá gần nhất và cooldown; ưu tiên cập bến; hành động hợp lệ ở tick cuối.

Kiểm tra hồi quy toàn bộ:

```powershell
python3 -m unittest discover -s tests -v
```

Kết quả: **Ran 61 tests in 33.568s — OK**.

## Phạm vi

Đây là kiểm chứng logic headless bằng fixture, không xác nhận trải nghiệm điều khiển hoặc HUD trên giao diện. Kết quả trên do người dùng cung cấp ngày 2026-11-21.
