# Quy trình: tạo proof cho một phase

Dùng khi chạy hoặc ghi bằng chứng kiểm chứng cho một phase của Chợ Nổi.

1. Đọc ticket/PRD của phase, `game.contract.json`, `docs/contracts/README.md` và `docs/verification/phase-n.md`.
2. Chạy test tập trung trước, rồi full suite trên commit tích hợp. Trong PowerShell:

   ```powershell
   $env:PYTHONPATH = "tests;."
   python3 -m unittest discover -s tests -v
   ```

3. Chỉ ghi kết quả đã thực sự chạy; giữ lệnh, số test, thời gian, commit và môi trường nếu transcript có.
4. Lưu fixture/output cần bàn giao trong `docs/proof/phase-n/`; không chép đường dẫn máy cá nhân.
5. Cập nhật ma trận bằng link tương đối. Phân biệt test tự động, smoke giao diện và chơi tay.
6. Chạy `git diff --check`. Không stage, commit, push hoặc tạo tag nếu người dùng chưa yêu cầu.
