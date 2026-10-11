# dbt Agent Skills cho repository

Bộ skill từ [dbt-labs/dbt-agent-skills](https://github.com/dbt-labs/dbt-agent-skills) được cài trong `.agents/skills/` ở commit `0d094169f56dedfece9bda1d0f2516036b2aee1e`. Đây là vị trí Codex tự quét khi mở repository; không cần cài vào tài khoản cá nhân. License Apache 2.0 của upstream nằm tại `.agents/skills/LICENSE`.

Đã cài toàn bộ 11 skill thuộc nhóm `skills/dbt/skills`:

| Skill                                           | Khi dùng                                    |
| ----------------------------------------------- | ------------------------------------------- |
| `using-dbt-for-analytics-engineering`           | Xây dựng, chỉnh sửa và debug model dbt      |
| `adding-dbt-unit-test`                          | Thêm unit test cho model                    |
| `maintaining-dbt-documentation`                 | Kiểm tra và bổ sung tài liệu model/cột      |
| `running-dbt-commands`                          | Chọn lệnh, selector và tham số dbt          |
| `fetching-dbt-docs`                             | Tra cứu tài liệu dbt                        |
| `using-dbt-state`                               | So sánh và chọn model theo state            |
| `troubleshooting-dbt-job-errors`                | Điều tra job dbt lỗi                        |
| `building-dbt-semantic-layer`                   | Xây Semantic Layer khi project bắt đầu dùng |
| `answering-natural-language-questions-with-dbt` | Truy vấn Semantic Layer khi đã cấu hình     |
| `working-with-dbt-mesh`                         | Quản trị nhiều project dbt khi cần          |
| `configuring-dbt-mcp-server`                    | Thiết lập MCP khi được yêu cầu              |

Các skill migration của upstream không được cài vì project chưa có yêu cầu chuyển nền tảng hoặc nâng cấp dbt. Khi cập nhật bộ skill, kiểm tra commit upstream mới và thay nội dung các thư mục tương ứng cùng file license; giữ các thay đổi project riêng trong `AGENTS.md` thay vì sửa bản vendored.
