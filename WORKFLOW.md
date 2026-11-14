# Quy trình vận hành v2: IQ cao nhất, tiết kiệm quota Claude gốc

## Thực tế model (đã xác nhận 2026-11-14)
| Nguồn | Model có thật | Quota |
| :--- | :--- | :--- |
| Claude Code gốc (`claude`, `claude-pro`) | Opus 5.5, Sonnet 5.5 | Anthropic, **khan hiếm** |
| Claude Code gốc (`claude-fable`, `claude-fable-design`) | Fable 5.2 | Hạn mức **riêng**, **rất đắt** |
| Proxy Antigravity (`claude-opus`, `claude-agy`) | Opus 4.6 Thinking, Sonnet 4.6, Gemini 3.8 Flash (low/medium/high/tiered), 3.5/3.1 Flash Lite | Antigravity, 2 tài khoản cân tải |
| Antigravity IDE | Orchestrator, Gemini 4 Hydrogen/Argon High, Gemini 3.8 Flash Medium | Antigravity |

Proxy tự ánh xạ `claude-opus-5-5` / `claude-sonnet-5-5` về bản 4.6, nên **5.5 thật chỉ có ở quota gốc**.

## Nguyên tắc: "soạn rẻ, kiểm đắt"
Token nặng (đọc repo, sinh code, vòng sửa lỗi) chạy trên 4.6/Gemini. 5.5 chỉ nhận **input nhỏ đã chuẩn bị sẵn** (PLAN.md, diff) và chạy một lần, không tool, trả lời ngắn. Một lượt 5.5 ở cổng chặn cho nhiều "IQ" hơn nhiều lượt 5.5 tương tác để làm việc thô.

## Luồng làm việc
| Bước | Công cụ | Quota |
| :--- | :--- | :--- |
| 0. *(Chỉ bài siêu nặng)* Soạn `BRIEF.md`: bài toán, ràng buộc, thứ đã thử, câu hỏi cần giải | `claude-opus` (Opus 4.6) | Antigravity |
| 0b. *(Chỉ bài siêu nặng)* Dựng phương án tổng + tìm kiếm -> `DESIGN.md` | `claude-fable-design` (Fable 5.2, một lần) | Fable riêng |
| 1. Soạn `PLAN.md` chi tiết (từ `DESIGN.md` nếu có); khảo sát thô có thể giao `claude-opus` trước | `claude` (Opus 5.5) | Gốc |
| 2. **Cổng 1**: phản biện kế hoạch | `claude-gate-plan` (Opus 5.5, một lần) | Gốc, rất ít |
| 3. Sửa PLAN theo phản biện (nếu REVISE) | `claude` (Opus 5.5) | Gốc |
| 4. Triển khai diện rộng | Antigravity IDE: Orchestrator / Gemini 4 Hydrogen High; hoặc `claude-agy` cho việc nhỏ | Antigravity |
| 5. Viết + chạy test | Antigravity IDE: Gemini 3.8 Flash Medium | Antigravity |
| 6. Pre-review, tự sửa lỗi dễ | `claude-prereview` (Opus 4.6) | Antigravity |
| 7. **Cổng 2**: duyệt diff cuối | `claude-gate-diff` (Opus 5.5, một lần) | Gốc, rất ít |
| 8. Sửa nếu FIX, rồi merge nhánh vào `main` | `claude-agy`; merge PR thủ công sau khi SHIP | Antigravity |

Bước 0/0b bỏ qua với việc thường ngày: vào thẳng bước 1.

Lặp bước 6 (miễn phí quota gốc) cho tới khi sạch **rồi mới** chạy bước 7; không dùng cổng 2 để "thử xem còn lỗi không".

## Khi nào mới dùng 5.5 tương tác (`claude` / `claude-pro`)
- Gỡ lỗi mà 4.6 đã thử 2 vòng không ra.
- Quyết định kiến trúc có hệ quả lớn, khó đảo ngược.
- Việc nhạy cảm về bảo mật.
Mở phiên mới, nêu rõ vấn đề + file liên quan, không để nó tự quét repo.

## Mẹo giảm tải quota gốc
- Giữ `CLAUDE.md` ngắn (nạp ở mọi phiên).
- `/clear` khi đổi việc; đừng giữ phiên dài.
- Cổng 5.5 đã chặn trần diff 300KB; vượt thì chia nhỏ hoặc chạy `claude-prereview` trước.
- Theo dõi quota proxy (2 tài khoản cân tải): `acc ui` hoặc `curl "http://localhost:8080/account-limits?format=table"`.

## Fable 5.2 (hạn mức riêng, rất đắt, không có trên proxy)
Chỉ dùng cho: logic siêu nặng, tìm kiếm/nghiên cứu, dựng phương án giải pháp tổng. Không dùng cho khảo sát repo, code, test, review thường (đã có 4.6/Gemini và cổng Opus 5.5).
- **Cách dùng chuẩn (rẻ nhất): `claude-fable-design`**: đọc `BRIEF.md` -> ghi `DESIGN.md`. Một lần, có tìm kiếm web + đọc repo, không sửa code, không lưu phiên. Đặt mức suy luận: `FABLE_EFFORT=max claude-fable-design` (mặc định `high`).
- Để Fable không tốn token vào việc thô: 4.6 soạn `BRIEF.md` (nêu rõ ràng buộc, thứ đã thử, câu hỏi cụ thể) trước, và Opus 5.5 chuyển `DESIGN.md` thành `PLAN.md` sau.
- Phiên tương tác: `claude-fable`; mở ngắn, hỏi hẹp, thoát khi có đáp án.
- Hai cổng 5.5 giữ Opus 5.5 (hạn mức khác Fable). Ép Fable vào cổng chỉ khi thật cần: `GATE_MODEL=claude-fable-5-2 claude-gate-diff`.

## Cấu trúc file
- `AGENTS.md`: giao thức + vai trò từng model (mọi agent đọc). `CLAUDE.md` import nó (`@AGENTS.md`). `.agent/rules/collaboration.md` trỏ Antigravity về nó.
- `.agent/templates/`: mẫu `BRIEF.md`, `DESIGN.md`, `PLAN.md`. File thật đặt ở root repo.
- `docs/`: hướng dẫn setup gốc (đã lỗi thời về model ID, giữ để tham khảo).

## Lệnh
Định nghĩa trong `~/.config/dual-harness/dual-harness.sh` (được `~/.bashrc` source). Gõ `dh-help` để xem nhanh.
`claude-opus`, `claude-agy`, `claude-pro`, `claude-prereview`, `claude-gate-plan`, `claude-gate-diff`, `claude-fable-design`, `claude-fable`.
`claude-opus` / `claude-agy` tự bật proxy nếu chưa chạy (vd sau khi khởi động lại WSL). Proxy: `acc start|status|ui|restart|stop`.
