# Retro nhóm

## Phase 2 (nhanh)
> Bản nháp do Khánh ghi từ lịch sử PR và bằng chứng; cả nhóm xác nhận/sửa trong buổi retro.
- Điều tốt: chốt contract v1.1 đầu phase nên ba lát (gather/Shop, Cá Sấu/quán/kế hoạch, day/UI) làm song song và ghép qua PR #4–#6 không xung đột lớn; mỗi lát có test riêng (cá 19, Shop 9, Cá Sấu 11, kế hoạch/quán, day 8, UI 10); full suite 123/123.
- Điều tệ: lát day/UI dồn thành một commit lớn ở cuối nên tích hợp muộn; smoke tích hợp phút 20 và bằng chứng preset thật chỉ làm sau khi ghép; chưa có lượt chơi tay trọn vòng ngày; câu hỏi bất tử 90 tick chưa hỏi PO.
- 1 hành động cho Phase 3: mỗi lát mở PR nhỏ ít nhất một lần trước phút 25 và chạy smoke tích hợp ngay khi PR vào `main` — **người nhận: Khánh** (nhắc ở standup phút 20); Thành commit theo từng phần nhỏ.

## Phase 3 (nhanh — điều rút ra từ lần đổi kho)
> Nháp do Khánh ghi; cả nhóm xác nhận.
- Điều tốt: chốt sớm schema cá thể và thứ tự tích hợp; mỗi lát tự viết test ngưỡng (gather 15, quán 13, day/HUD); sau khi ghép chỉ có 3 file conflict và suite về xanh 154/154.
- Điều tệ: PR lát schema (`p3/schema`) **không được merge trước** PR Quán và Day/UI dù kế hoạch ghi "S đi trước" — hai lát kia phải tự viết adapter tạm và tự thêm `freshness`, dẫn tới khối contract khai hai lần và hai chỗ cấp id cho mẫu `hold`. Phát hiện khi suite đỏ trên `main` (5 test).
- 1 hành động cho Phase 4: PR đổi hợp đồng/schema phải merge trước mọi PR phụ thuộc; người tích hợp kiểm `git merge-base --is-ancestor` trước khi merge PR lát — **người nhận: Khánh**.

## Phase 4 (cuối)
> Nháp do Trà (điều phối retro) tổng hợp từ `git log`, các PR đã merge và ghi chép trong repo; cả nhóm xác nhận/sửa trong buổi retro. Mốc phút tính từ lúc kế hoạch Phase 3 lên `main` (`e28b544`, 15:55).

### Rà lại hành động đã chốt
| Phase chốt | Hành động (người nhận) | Đã làm chưa | Bằng chứng / vì sao |
|---|---|---|---|
| P2 | Mỗi lát mở PR nhỏ ít nhất một lần trước phút 25 và chạy smoke tích hợp ngay khi PR vào `main` (Khánh nhắc ở standup) | **Một phần** | Lát Quán vào `main` ở phút 22 (PR #8). Day/UI vào ở phút 34 (PR #9). Lát schema S+G không có PR riêng vào `main`, chỉ được ghép ở `p3/integrate` phút 44 (`e3e019b`). Smoke tích hợp chỉ chạy sau lần ghép đó, nên `main` đỏ 5 test trong khoảng giữa PR #8 và lần ghép. |
| P2 | Thành commit theo từng phần nhỏ (Thành) | **Chưa** | Phase 3 Thành có 1 commit `000593e` ("p3"), Phase 2 có 1 commit lớn `5742593`. Cần nhóm hỏi Thành vướng gì (làm trên máy rồi đẩy một lần?). |
| P3 | PR đổi hợp đồng/schema phải merge trước mọi PR phụ thuộc; kiểm `git merge-base --is-ancestor` trước khi merge (Khánh) | Đánh giá cuối Phase 4 | Kế hoạch P4 đặt manifest 1.3 merge **trước tiên**; điền kết quả khi gắn tag `phase-4`. |

### Bằng chứng đóng góp (commit không tính merge, trên `main`)
| Người | P1 | P2 | P3 | Phần chính và bằng chứng |
|---|---|---|---|---|
| khanhvnm | 9 | 7 | 6 | PO/Integrator: kế hoạch và hợp đồng mỗi phase, `gather` (P1–P3), contract v1.1/v1.2, Shop, kho cá thể (`6368d06`), tích hợp PR #1–#10, verification/proof |
| phungtr | 1 | 5 | 2 | `sim/quan` P1 (`3420719`, PR #2); P2 quán 2 bếp/4 bàn, `day_plan`, Cá Sấu (`c739633`…`c3a5382`, PR #5); P3 quán độ tươi (`73722a7`, `8c23154`, PR #8); P4 `chonoi/soak.py` + test 10 Ngày |
| thanhtey1234 | 1 | 1 | 1 | UI/HUD P1 (`549bf84`, PR #3); điều phối `day`, pause, HUD (`5742593`, PR #6); HUD/day v1.2 (`000593e`, PR #9) |

- Đọc code của nhau: các PR đều do Khánh tích hợp; review chéo theo `TEAM.md` (Trà ↔ Khánh) chưa có dấu vết trong repo — nhóm bổ sung nếu đã review trực tiếp.
- Token theo người: chưa đo được (xem `docs/ai-usage-log.md`).

### Một lần AI sai và cách nhóm phát hiện
Phase 4, lát soak (Trà, Claude Code): bot đọc `time_left_ticks` từ snapshot riêng của sim, trong khi trường này chỉ có ở snapshot của phiên. Lần chạy soak đầu tiên báo `crashes: 1` kèm traceback `KeyError`, vì soak được thiết kế để đếm lỗi thay vì dừng im lặng. Đã sửa sang `sess.sim.time_left_ticks`; chạy lại 10 Ngày đạt (`test_soak`).

### Điều tốt / điều cần sửa / nếu làm lại (đề xuất, chờ nhóm chốt)
- Tốt: mỗi lát tự viết test hộp đen theo Test Contract (suite tăng từ 32 lên 160 test); hợp đồng ghi trong `docs/contracts/` trước khi build.
- Cần sửa: tích hợp dồn cuối phase; schema đi trước trên kế hoạch nhưng không đi trước khi merge; commit lớn một lần.
- Nếu làm lại: merge PR schema ngay khi xanh rồi mới mở PR phụ thuộc; chạy smoke ngay sau mỗi PR vào `main`; mỗi người đẩy ít nhất một commit nhỏ trước phút 20.
- Hành động tiếp theo: _(nhóm chốt trong buổi retro, ghi người nhận)_
