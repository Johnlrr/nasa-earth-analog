# Hướng dẫn Setup Kiến trúc Dual-Harness: Claude Code CLI + Antigravity

Tài liệu này hướng dẫn chi tiết cách thiết lập hệ thống kết hợp đa nguồn quota mà vẫn giữ nguyên **100% trí thông minh (IQ) và sức mạnh của từng Agent Harness**:
* **Claude Code CLI:** Chạy các model `Claude Opus 5.5 (Thinking)` và `Claude Sonnet 5.5 (Thinking)` (từ cả tài khoản chính chủ lẫn nguồn quota Antigravity thông qua `antigravity-claude-proxy`).
* **Antigravity (Native Harness):** Chạy độc lập các model `Orchestrator (Argon)`, `Gemini 4 Hydrogen High`, `Gemini 4 Argon High` và `Gemini 3.8 Flash Medium` đúng trên môi trường gốc của nó.

---

## 1. Sơ đồ kiến trúc tổng thể

```text
                  [ GIT REPO: CLAUDE.md + PLAN.md + DIFF ]
                         ▲                        ▲
         (1. Kiến trúc & Review)          (2. Thực thi diện rộng)
                         │                        │
        ┌────────────────┴────────┐      ┌────────┴────────────────┐
        │     CLAUDE CODE CLI     │      │   ANTIGRAVITY (NATIVE)  │
        │  • Opus 5.5 (Thinking)  │      │  • Orchestrator (Argon) │
        │  • Sonnet 5.5 (Thinking)│      │  • Gemini 4 Hydrogen/   │
        └────────┬───────┬────────┘      │    Argon High           │
                 │       │               │  • Gemini 3.8 Flash     │
     (Quota gốc) │       │ (Proxy :8080) └─────────────────────────┘
                 ▼       ▼
    [ Anthropic API ]  [ antigravity-claude-proxy ]
                                  │
                                  ▼
                       [ Antigravity Cloud Code ]
```

---

## 2. Yêu cầu hệ thống (Prerequisites)

Đảm bảo máy của bạn đã cài đặt các thành phần sau:
1. **Node.js:** Phiên bản `22.19.0` trở lên (`node -v`).
2. **Claude Code CLI:** Đã cài đặt bản chính thức qua npm:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
3. **Antigravity IDE / App:** Đã cài đặt và đăng nhập sẵn tài khoản trên máy.

> **Lưu ý bảo mật & tài khoản:** `antigravity-claude-proxy` sử dụng token phiên đăng nhập từ Antigravity để dịch sang chuẩn Anthropic API. Để an toàn tuyệt đối cho tài khoản Google chính, bạn nên dùng một tài khoản phụ (hoặc tài khoản trong nhóm Family) để kết nối với proxy.

---

## 3. Bước 1: Cài đặt & Khởi chạy `antigravity-claude-proxy`

### 3.1. Cài đặt Global
Mở terminal và cài đặt công cụ proxy (kèm lệnh viết tắt `acc`):

```bash
npm install -g antigravity-claude-proxy@latest
```

### 3.2. Khởi động Proxy chạy nền
Chạy lệnh sau để khởi tạo server tại cổng mặc định `http://localhost:8080` (tiến trình sẽ chạy ngầm ngay cả khi bạn đóng cửa sổ terminal):

```bash
acc start
```

### 3.3. Liên kết tài khoản Antigravity
* **Cách 1 (Tự động):** Nếu bạn đang mở và đăng nhập sẵn app Antigravity trên máy, proxy sẽ tự động nhận diện phiên đăng nhập cục bộ.
* **Cách 2 (Qua Web Dashboard - Khuyên dùng để quản lý nhiều tài khoản):**
  1. Mở trình duyệt truy cập: `http://localhost:8080`
  2. Chuyển sang tab **Accounts** $\rightarrow$ bấm **Add Account** và hoàn tất đăng nhập Google OAuth.

### 3.4. Kiểm tra trạng thái & danh sách Model ID
Chạy lệnh sau để xác nhận proxy hoạt động bình thường và xem chính xác tên Model ID mà proxy ánh xạ từ tài khoản của bạn:

```bash
# Kiểm tra sức khỏe server
curl http://localhost:8080/health

# Xem danh sách model khả dụng và hạn mức quota hiện tại
curl "http://localhost:8080/account-limits?format=table"
```

---

## 4. Bước 2: Cấu hình chạy song song 2 nguồn Quota trên Claude Code CLI

Thay vì sửa cứng file `~/.claude/settings.json` (làm mất khả năng dùng song song tài khoản Claude gốc), cách tối ưu nhất là **tạo các hàm Shell (Functions)** trong `~/.zshrc` (macOS/Linux) hoặc `~/.bashrc` (Ubuntu/WSL).

### 4.1. Bỏ qua màn hình Onboarding khi gọi qua Proxy
Mở file `~/.claude.json` và đảm bảo có thuộc tính `"hasCompletedOnboarding": true` để Claude Code không hỏi lại bước đăng nhập khi chuyển sang URL local:

```json
{
  "hasCompletedOnboarding": true
}
```

### 4.2. Thêm cấu hình định tuyến vào Shell Profile
Mở file `~/.zshrc` (hoặc `~/.bashrc`) bằng editor và dán đoạn cấu hình sau vào cuối file:

```bash
# ==============================================================================
# DUAL-HARNESS CLAUDE CODE CLI ROUTING
# ==============================================================================

# 1. Dùng quota Claude Code chính chủ (Mặc định)
alias claude-pro='ANTHROPIC_BASE_URL="https://api.anthropic.com" claude'

# 2. Dùng quota Antigravity với Claude Sonnet 5.5 (Thinking) - Coding hằng ngày
claude-agy() {
  ANTHROPIC_BASE_URL="http://localhost:8080" \
  ANTHROPIC_AUTH_TOKEN="antigravity-local" \
  ANTHROPIC_MODEL="claude-sonnet-5-5-thinking" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet-5-5-thinking" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="claude-opus-5-5-thinking" \
  claude "$@"
}

# 3. Dùng quota Antigravity với Claude Opus 5.5 (Thinking) - Kiến trúc & Review
claude-opus() {
  ANTHROPIC_BASE_URL="http://localhost:8080" \
  ANTHROPIC_AUTH_TOKEN="antigravity-local" \
  ANTHROPIC_MODEL="claude-opus-5-5-thinking" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="claude-opus-5-5-thinking" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet-5-5-thinking" \
  claude "$@"
}
```

*(Lưu ý: Nếu lệnh kiểm tra ở Bước 3.4 hiển thị tên ID model hơi khác, ví dụ `claude-opus-5-5` thay vì `claude-opus-5-5-thinking`, hãy cập nhật lại cho khớp).*

Áp dụng cấu hình ngay lập tức:
```bash
source ~/.zshrc   # hoặc source ~/.bashrc
```

**Kết quả:** Bạn có thể mở **Tab Terminal 1** gõ `claude` (chạy quota gốc), và mở **Tab Terminal 2** gõ `claude-opus` hoặc `claude-agy` (chạy quota Antigravity) hoàn toàn độc lập, không xung đột phiên làm việc.

---

## 5. Bước 3: Chuẩn hóa "Bộ nhớ chung" (`CLAUDE.md`) giữa 2 Harness

Để Claude Code CLI và Antigravity phối hợp mượt mà trên cùng một dự án mà không bị đứt mạch ngữ cảnh, hãy đặt file `CLAUDE.md` sau tại thư mục gốc của repository:

```markdown
# Project Collaboration Protocol (Dual-Harness)

## Architecture & State Sync
- Mọi kế hoạch triển khai tính năng lớn phải được ghi ra file `PLAN.md` ở root (hoặc `.agent/PLAN.md`) trước khi sửa code hàng loạt.
- File `PLAN.md` đóng vai trò là nguồn sự thật duy nhất (Single Source of Truth) để đồng bộ giữa **Claude Code CLI** (Architect/Reviewer) và **Antigravity** (Multi-file Executor).

## Workflow Rules
1. **Planning:** Phân tích codebase, liệt kê rõ các file cần tạo/sửa, schema dữ liệu và edge-cases vào `PLAN.md`.
2. **Execution:** Khi thực thi theo `PLAN.md`, đánh dấu `[x]` vào từng hạng mục đã hoàn thành.
3. **Verification:** Luôn chạy test/linter trước khi kết thúc phiên. Không tự ý `git commit` nếu chưa qua bước review diff cuối cùng.
```

---

## 6. Quy trình vận hành "IQ Cao Nhất" hằng ngày

| Giai đoạn | Công cụ & Model sử dụng | Thao tác thực tế |
| :--- | :--- | :--- |
| **1. Lên kiến trúc** | **Terminal (`claude-opus`)**<br>*Claude Opus 5.5 (Thinking)* | Yêu cầu khảo sát repo, thiết kế luồng xử lý và xuất kế hoạch chi tiết ra file `PLAN.md`. |
| **2. Triển khai diện rộng** | **Antigravity IDE**<br>*Orchestrator (Argon)* hoặc *Gemini 4 Hydrogen High* | Trỏ vào `@PLAN.md` để Antigravity điều phối đa luồng, sinh code đồng loạt trên nhiều file/module. |
| **3. Phủ Unit Test** | **Antigravity IDE**<br>*Gemini 3.8 Flash Medium* | Chuyển model trong dropdown Antigravity sang bản Flash để viết toàn bộ test case và chạy kiểm thử đến khi pass. |
| **4. Review & Chốt hạ** | **Terminal (`claude-opus`)**<br>*Claude Opus 5.5 (Thinking)* | Quay lại terminal, yêu cầu đối chiếu toàn bộ `git diff` với `PLAN.md`, vá các lỗ hổng logic sâu và thực hiện `git commit`. |

---

## 7. Bảng tra cứu lệnh quản lý Proxy nhanh

| Lệnh | Chức năng |
| :--- | :--- |
| `acc start` | Khởi chạy proxy chạy ngầm ở cổng `8080`. |
| `acc status` | Kiểm tra trạng thái hoạt động và PID của proxy. |
| `acc ui` | Mở nhanh giao diện Web Dashboard quản lý tài khoản & quota. |
| `acc start --log` | Chạy proxy trực tiếp trên terminal để xem log debug thời gian thực. |
| `acc restart` | Khởi động lại proxy sau khi cập nhật phiên bản mới. |
| `acc stop` | Tắt hoàn toàn proxy server. |