# Telegram điều khiển crawler SUUMO

Runbook hiện tại: [Crawl một ward và điều phối Telegram](crawler-ward-dispatch.md).

Bot dùng long polling, private chat/owner và cùng token lifecycle. Quy tắc menu/hàng chờ/hạn mức/lịch đã được thay bằng release ward; xem runbook mới và biên bản release.

Các release trước: [telegram-01](crawler-release-20261009-telegram-01.md), [telegram-02](crawler-release-20261009-telegram-02.md).

## Retry thông báo lifecycle — local 2026-10-10

Notifier dùng chung trên host và trong image gửi một lần đầu, rồi tối đa ba
retry khi lỗi mạng/TLS/timeout hoặc Telegram 5xx. Khoảng chờ tăng 2/4/8 giây,
timeout mỗi request vẫn 5 giây. Thành công dừng ngay; hết lượt retry ghi warning
vào journald và để crawler tiếp tục. Không retry lỗi 400/401/403 vì gửi lại không
sửa được markup, token hoặc quyền chat.

HTTP 429 dùng `parameters.retry_after` theo
[Telegram Bot API](https://core.telegram.org/bots/api#responseparameters), chờ ít
nhất thời gian Telegram yêu cầu. Nếu phải chờ hơn 30 giây thì dừng retry của
thông báo đó để không giữ pipeline quá lâu; không thử lại trước hạn server.
Timeout sau khi server đã nhận tin có thể tạo bản gửi trùng khi retry;
sendMessage không cung cấp khóa chống gửi trùng. Chưa có outbox phát lại qua restart.

Phạm vi là thông báo VPN/job/pipeline; các callback/menu của bot vẫn giữ logic
hiện có. Đã deploy `20261010-telegram-retry-01` từ commit `74158d0` với image
mới và host bundle cùng source; xem [biên bản release](crawler-release-20261010-telegram-retry-01.md)
và [lệnh deploy một bước](crawler-deployment.md).
