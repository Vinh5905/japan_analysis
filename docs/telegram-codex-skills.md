# Telegram skills cho Codex

Đã kiểm tra và cài hai skill ở phạm vi người dùng vào `~/.codex/skills` ngày 2026-10-09. Codex tự phát hiện từ lượt mới; trong lượt cài đặt đã đọc trực tiếp và áp dụng cho bot SUUMO.

| Skill | Nguồn đã kiểm tra | Revision đã cài | Phần áp dụng |
| --- | --- | --- | --- |
| `telegram-keyboard-design` | [Telegram Keyboard Designer](https://mcpmarket.com/tools/skills/telegram-keyboard-designer), repo `david-li0406/meta-skill-evloving` | `a864b5c287984f1fe1a04c9a91dc0c6a7b386735` | Menu gọn, tối đa hai nút mỗi hàng, hành động chính rõ, quay về menu, xác nhận và cập nhật tin hiện tại |
| `telegram-bot-builder` | [Telegram Bot Builder](https://www.aitmpl.com/component/skills/enterprise-communication/telegram-bot-builder), repo `davila7/claude-code-templates` | `46b4d8b1c051e9fd0f8fdd739b15f7f5e8942608` | Phản hồi callback trước truy vấn chậm, lỗi dễ hiểu, giảm tin trùng, tách giao diện khỏi vận hành |

Cài bằng helper chính thức `skill-installer` của Codex từ GitHub, không dùng installer Claude. Mỗi skill có `agents/openai.yaml`. Validator của `skill-creator` đạt cho cả hai. `telegram-bot-builder` đã chuyển trường `source` upstream sang `metadata.source` phù hợp Codex. Các file `.py` của skill keyboard thực chất là tài liệu Markdown, đã đổi sang `.md` và sửa link; link `flow-patterns.md` không tồn tại đã bỏ. Nội dung gốc được giữ tại `references/upstream.md` của từng skill.

Phần hướng dẫn Codex bổ sung yêu cầu giữ stack và quyền hiện có; kiểm tra callback theo giới hạn **64 byte UTF-8**, không phải 64 ký tự. Telegram quyết định chiều cao/màu nút theo client nên không áp dụng thông số pixel trong mẫu upstream. Python/Node SDK trong mẫu chỉ là ví dụ; bot SUUMO tiếp tục dùng Python chuẩn và long polling. Không áp dụng phần monetization, webhook hoặc thêm quyền dừng/sửa lịch.

Có thể gọi `$telegram-keyboard-design` để thiết kế menu hoặc `$telegram-bot-builder` để chỉnh luồng bot ở các lượt Codex tiếp theo. Khi cập nhật skill từ upstream, cần giữ các điều chỉnh Codex nêu trên. Quy tắc API xác minh theo [InlineKeyboardButton](https://core.telegram.org/bots/api#inlinekeyboardbutton) và [answerCallbackQuery](https://core.telegram.org/bots/api#answercallbackquery).

Các mẫu giao diện SUUMO nằm trong `suumo_source_crawler/scripts/telegram_ui.py`; controller kiểm tra quyền và điều phối trong `suumo_source_crawler/scripts/telegram_control.py`. Bản xem trước local: `tmp/telegram-skills/preview.html` (dữ liệu minh họa, nút không thực thi thao tác).
