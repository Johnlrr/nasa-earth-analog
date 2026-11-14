@AGENTS.md

## Riêng cho Claude Code
- Trả lời người dùng bằng tiếng Việt.
- Phiên qua proxy (`claude-opus`, `claude-agy`) là model 4.6; phiên gốc (`claude`, `claude-pro`, `claude-fable`) là 5.5/Fable. Tự xác định vai trò theo mục 2 của AGENTS.md.
- Phiên gốc 5.5/Fable: tiết kiệm token. Không dùng subagent quét repo, không đọc file lớn khi không cần, gợi ý `/clear` khi đổi việc.
- Khi xong một hạng mục, nhắc người dùng lệnh bước tiếp theo trong luồng (vd `claude-gate-plan`, `claude-prereview`, `claude-gate-diff`).
