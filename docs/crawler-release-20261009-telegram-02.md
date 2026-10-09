# Cập nhật giao diện Telegram 20261009-telegram-02

Đã triển khai ngày 2026-10-09 lên `thuevpsgiare`, thư mục `/opt/suumo-crawler`. Bot `@suumo_crawler_bot` đã dùng giao diện mới. Không chạy crawler hoặc thử đóng VPN thật; người dùng tự kiểm chứng phần đó.

## Thay đổi

Áp dụng hai [skill Telegram đã cài cho Codex](telegram-codex-skills.md). `/start` mở menu inline, nút chính Chạy crawler riêng một hàng; các nút xem tối đa hai nút mỗi hàng. Có Cập nhật/Menu ở màn hình xem. Callback được trả lời trước truy vấn, rồi sửa tin hiện tại; nếu Telegram báo tin không đổi thì không gửi trùng. Tin đã xóa/không sửa được có fallback gửi thẻ mới.

Thẻ trạng thái, lịch, lịch sử, tổng và hướng dẫn dùng tiêu đề đậm, emoji thống nhất, bố cục chia nhóm và giờ Việt Nam. Số liệu nhóm hàng nghìn; lịch chuyển ngày giờ và thời gian chờ thành dạng dễ đọc. Lịch sử tách năm lượt, tổng giải thích cách tính bằng ngôn ngữ thông thường. Xác nhận có nút chính riêng và Hủy; vẫn giữ TTL hai phút, một lần dùng, auth private/owner, busy check/shared lock và nguồn manual bền vững. Lifecycle crawler tiếp tục gửi tin riêng từng bước theo bản 01.

## Artifact

- Host bundle: `tmp/releases/suumo-host-20261009-telegram-02.tar.gz`, có 15 file managed, thêm `scripts/telegram_ui.py`.
- Remote bundle: `/tmp/suumo-release-3e13acf6c3cf45fd8f410e6d74c8c81d/release.tar.gz`.
- Backup: `/opt/suumo-crawler/.releases/20261009-telegram-02-c3102375`; file đánh số và `paths.json` ánh xạ tới đường dẫn gốc. Có credentials nên giữ quyền riêng tư.
- Image: `kevinpham9257/suumo-crawler:20261009-telegram-02`, cùng digest `sha256:a443351a6600967ff77085fc7191d7ff42b6e55a07cf2f89a142916206f91d83` với bản 01. Lần này chỉ sửa code host nên publish tag mới bằng manifest đã kiểm chứng, không build lại crawler.
- Bản xem trước bố cục: `tmp/telegram-skills/preview.html` (dữ liệu minh họa). Đã xem trên trình duyệt ở khung thẻ rộng khoảng 330px.
- Log kiểm chứng local: `/tmp/telegram-ui-db-tests.log`; VPS: `tmp/telegram-skills/vps-verification.txt`.

## Kiểm chứng và trạng thái

96 test đạt, gồm hai test PostgreSQL local. Có kiểm tra mới cho navigation/auth, nút chạy chỉ mở xác nhận, update trùng, trả callback trước query, lỗi query sửa đúng tin, fallback edit lỗi, không gửi lại khi message không đổi, Hủy, HTML/secret, giới hạn byte callback và hiển thị lịch/timezone. Hai skill đạt validator chính thức của Codex.

Đối chiếu checksum 15 file host, menu chat riêng đúng bảy lệnh và không có webhook. Render qua controller đã deploy với dữ liệu VPS cho sáu màn hình đọc; dùng API giả để không gửi tin thử hoặc thay offset. SQLite giữ inode `1610692`, offset `738763724` trong hai lần đối chiếu và quyền `600`. Cấu hình so với backup chỉ khác image tag.

Bot enabled, active/running, `NRestarts=0`. Crawler inactive/dead, result gần nhất success; OpenVPN inactive. Timer enabled/active, calendar thực tế `*-*-* 00:00:00`, timezone `Asia/Ho_Chi_Minh`, lần kế tiếp `2026-10-10T00:00:00+07:00`. PostgreSQL/MinIO tiếp tục healthy. Source 1 vẫn 39 lượt/65.551 URL; history đúng 39, 38, 37, 36, 35. Không bootstrap, migration hoặc thay lịch/VPN config.

Để sử dụng, mở bot và gửi `/start`; menu cũ có thể được thay bằng tin mới này. Khi muốn kiểm thử crawler thật, dùng Chạy crawler → Xác nhận chạy.
