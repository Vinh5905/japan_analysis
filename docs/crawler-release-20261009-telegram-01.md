# Crawler release 20261009-telegram-01

Đã triển khai ngày 2026-10-09 lên VPS qua SSH alias `thuevpsgiare`, runtime `/opt/suumo-crawler`. Phạm vi gồm crawler release, deployment bundle, VPN cleanup và bot Telegram; không triển khai Airflow/dbt/warehouse.

## Bản phát hành

- Image: `kevinpham9257/suumo-crawler:20261009-telegram-01`, hỗ trợ `linux/amd64` và `linux/arm64`.
- Digest: `sha256:a443351a6600967ff77085fc7191d7ff42b6e55a07cf2f89a142916206f91d83`.
- Host bundle local: `tmp/releases/suumo-host-20261009-telegram-01.tar.gz`.
- Bundle đã cài cuối cùng: `/tmp/suumo-release-51ccbe96ec43499ba3699f2d95f19c1d/release.tar.gz` trên VPS; checksum mọi file managed đã đối chiếu.
- Backup trước lần cài cuối: `/opt/suumo-crawler/.releases/20261009-telegram-01-731d7e58`.
- Backup trước khi chuyển từ runtime cũ: `/opt/suumo-crawler/.releases/20261009-telegram-01-4b126df5`.

Installer không pull lại PostgreSQL/MinIO khi đúng image cấu hình đã có trên host. Lần deploy đầu bị registry từ chối pull MinIO, trước khi thay runtime; timer được khôi phục. Đã sửa installer, thêm test và deploy lại thành công. Vẫn pull image crawler release mới; infra thiếu image vẫn được pull trước khi thay file. Không thay cấu hình/image/volume hạ tầng để xử lý lỗi registry.

Kiểm chứng thực tế `/status` cũng dẫn đến sửa cách đọc OpenVPN inactive: `systemctl is-active` trả exit khác 0 cho trạng thái hợp lệ này, nên bot dùng `ActiveState` đã đọc để giữ nguyên trạng thái thay vì báo unknown. Bản sửa đã cài và kiểm chứng lại trên VPS.

## Trạng thái bàn giao

- `suumo-crawler-telegram.service`: enabled, active/running, `NRestarts=0`; bot `@suumo_crawler_bot`, menu đúng scope chat riêng; không có webhook.
- SQLite `state/telegram-control.sqlite3`: quyền `600`, giữ nguyên qua lần cập nhật bot.
- Crawler service: inactive/dead, kết quả gần nhất success. Unit mới có preflight, `--vpn-managed-by-systemd`, `ExecStopPost` cleanup và `TimeoutStopSec=10min`; `systemd-analyze verify` đạt.
- OpenVPN: inactive; deployment không yêu cầu start/stop VPN.
- Timer: enabled/active, giữ calendar cũ hàng ngày 00:00; timezone VPS `Asia/Ho_Chi_Minh`; lần kế tiếp `2026-10-10T00:00:00+07:00`.
- PostgreSQL/MinIO healthy, giữ nguyên container và named volumes. `.env` chỉ đổi image tag và thêm `TELEGRAM_CONTROL_ENABLED=true`; đã đối chiếu với backup, không ghi credentials vào báo cáo.
- Source 1: 39 lượt tải HTML, 65.551 URL đã xử lý trước và sau deploy; history đúng 5 lượt 39 → 35. `/status`, `/schedule`, `/history`, `/total` đã đọc thành công bằng code host trên VPS.

## Kiểm tra đã thực hiện

84 Python test đều đạt, gồm test SQL PostgreSQL local với fixtures TEMP. Image đã được build/push và pull trên VPS amd64; container `--network none` chỉ import Scrapy/extension và đọc settings, không chạy spider. Hash notifier trong image khớp source local/host; RepoDigest khớp digest đã publish. Không gửi test message thủ công, không chạy crawler, bootstrap hoặc migration và không thử cleanup VPN thật.

Người dùng sẽ tự kiểm chứng lượt chạy và đóng VPN. Mở bot, thử `/status`, `/schedule`, `/history`, `/total`; khi sẵn sàng chạy, `/run_crawl` rồi bấm xác nhận. Log dùng:

```bash
ssh thuevpsgiare 'journalctl -u suumo-crawler-telegram.service -n 50 --no-pager'
ssh thuevpsgiare 'journalctl -u suumo-crawler-pipeline.service -f'
```

Lịch cũ vẫn bật và sẽ chạy lượt kế tiếp theo calendar. Tham khảo [runbook Telegram](telegram-crawler-control.md) và [quy trình deploy](crawler-deployment.md) cho các lần cập nhật sau.
