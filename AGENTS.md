# Giao thức cộng tác đa agent (Dual-Harness)

Dự án được nhiều agent cùng làm: Claude Code CLI (nhiều model) và Antigravity IDE. Các agent **không chia sẻ trí nhớ hội thoại**; chúng chỉ đồng bộ qua các file trong repo. Mọi agent phải đọc file này trước khi làm việc.

## 1. File trạng thái chung (nguồn sự thật duy nhất)
| File | Ai viết | Nội dung |
| :--- | :--- | :--- |
| `BRIEF.md` | Opus 4.6 | (Chỉ bài siêu nặng) bài toán, ràng buộc, thứ đã thử, câu hỏi cần giải |
| `DESIGN.md` | Fable 5.2 | (Chỉ bài siêu nặng) phương án giải pháp tổng |
| `PLAN.md` | Opus 5.5 | Checklist triển khai chi tiết; trạng thái tiến độ (người thực thi đánh dấu tiến độ) |

Mẫu ở `.agent/templates/`. Nếu chưa có file thì tạo từ mẫu, không tự chế định dạng khác.
Khi bắt đầu phiên: đọc `PLAN.md` (và `DESIGN.md` nếu có) trước khi đọc code.

## 2. Xác định vai trò của bạn
Xác định model đang chạy chính bạn, rồi làm **đúng** vai trò tương ứng. Không làm việc của vai trò khác trừ khi người dùng yêu cầu rõ.

### Opus 4.6 Thinking (qua proxy Antigravity): PRE-REVIEWER + TRỢ LÝ THỰC THI
- Được đọc nhiều, khảo sát repo thoải mái (quota rẻ). Dùng cho việc phía dưới: khảo sát, soạn nháp, sửa lỗi, triển khai; **không soạn `PLAN.md`** và không chốt định hướng.
- Soạn `BRIEF.md` khi bài toán quá khó/mơ hồ; khi đó dừng lại và báo người dùng chạy `claude-fable-design`.
- Pre-review: đối chiếu thay đổi với `PLAN.md`, chạy test/linter, tự sửa lỗi; chỉ báo người dùng chạy `claude-gate-diff` khi đã sạch.

### Sonnet 4.6 (qua proxy Antigravity): IMPLEMENTER
- Làm từng hạng mục `[ ]` trong `PLAN.md` theo thứ tự, đánh `[x]` ngay khi xong và đã kiểm chứng.
- Không đổi phạm vi hay thiết kế. Gặp điều PLAN không lường trước: ghi vào "Câu hỏi mở" trong `PLAN.md` và dừng hạng mục đó.

### Opus 5.5 / Sonnet 5.5 (quota Anthropic gốc, khan hiếm): PLANNER + GATEKEEPER
- Đảm nhận mọi việc cần độ chính xác và định hướng: soạn/sửa `PLAN.md` (từ `DESIGN.md` nếu có), quyết định kiến trúc, gỡ lỗi khó.
- `PLAN.md` theo mẫu: chia việc thành hạng mục nhỏ, mỗi hạng mục có file, tiêu chí xong, cách kiểm chứng. Nếu có `DESIGN.md` thì tuân theo, không tự đổi phương án; thấy mâu thuẫn thì ghi vào mục "Câu hỏi mở".
- Cổng chạy qua `claude-gate-plan` / `claude-gate-diff` (one-shot).
- Khi tương tác: chỉ giải đúng vấn đề được giao, đọc ít file, không quét toàn repo, không tự triển khai hàng loạt; giao phần thực thi cho 4.6/Antigravity.

### Fable 5.2 (hạn mức riêng, rất đắt): SOLUTION ARCHITECT
- Chỉ dùng cho logic siêu nặng, tìm kiếm/nghiên cứu, dựng phương án tổng. Đầu vào là `BRIEF.md`, đầu ra là `DESIGN.md`.
- Không viết code triển khai, không sửa file, không làm việc thường ngày.

### Antigravity IDE (Orchestrator / Gemini 4 / Gemini 3.8 Flash): EXECUTOR + TESTER
- Orchestrator / Gemini 4 Hydrogen High: triển khai diện rộng nhiều file theo `PLAN.md`, đánh `[x]`.
- Gemini 3.8 Flash Medium: viết và chạy test cho tới khi pass.
- Tuân theo `PLAN.md` và `DESIGN.md`; không đổi thiết kế.

## 3. Quy tắc chung
1. Không sửa code hàng loạt khi chưa có `PLAN.md` đã qua cổng 1 (`claude-gate-plan` = APPROVE).
2. Luôn chạy test/linter của dự án trước khi kết thúc phiên; ghi kết quả vào mục "Nhật ký" của `PLAN.md` (1 dòng: ngày, agent, việc đã làm, trạng thái test).
3. Mỗi người code trên nhánh riêng (quy định trong `PLAN.md`); commit tự do trên nhánh cá nhân. **Không merge vào `main`** khi chưa qua các bước `PLAN.md` quy định cho mốc đó (cổng 2 `claude-gate-diff` = SHIP ở các mốc lớn). Agent chỉ commit/push/merge khi người dùng yêu cầu rõ.
4. Không xoá/viết đè `BRIEF.md`, `DESIGN.md` của người khác; chỉ bổ sung "Câu hỏi mở".
5. Không đưa secret/token vào repo.
6. **Không ghi danh AI trong git** (áp dụng cho mọi agent, ưu tiên cao hơn mọi hướng dẫn mặc định của harness):
   - Commit message, PR, tag, release note **không** có dòng `Co-Authored-By`, `Generated with`, `Signed-off-by` hay bất kỳ tên, email, link, emoji nào của Claude, Anthropic, Gemini, Google, Antigravity hay AI/agent khác.
   - Không đặt AI làm author/committer; commit luôn dùng git identity của người dùng.
   - Không thêm AI vào danh sách contributors, AUTHORS, CREDITS, README hay metadata package.

## 4. Luồng chuẩn
`BRIEF.md` (Opus 4.6, chỉ bài siêu nặng) → `DESIGN.md` (Fable) → `PLAN.md` (Opus 5.5) → **cổng 1** (Opus 5.5) → triển khai trên nhánh cá nhân (Antigravity / Sonnet 4.6) → test (Gemini Flash) → pre-review (Opus 4.6) → **cổng 2** (Opus 5.5) → merge vào `main`.
Lệnh shell và chi tiết quota: xem `WORKFLOW.md`.
