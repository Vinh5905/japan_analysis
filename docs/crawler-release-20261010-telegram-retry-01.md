# Release Telegram retry — 2026-10-10

Đã deploy `20261010-telegram-retry-01` lên `thuevpsgiare:/opt/suumo-crawler`
lúc 08:06 +07. Source runtime là commit `74158d041e98`, export bằng Git archive
vào thư mục riêng để loại các thay đổi building/parser/dbt chưa commit và guides.
Commit này cùng commit Docker VPN `d9814ce` đã push lên `origin/main`.

## Thay đổi

Notifier dùng chung host/image gửi một lần đầu và tối đa ba retry khi lỗi
mạng/TLS/timeout hoặc Telegram 5xx. Backoff 2/4/8 giây; thành công dừng ngay.
429 tôn trọng retry_after, bỏ retry nếu server yêu cầu chờ quá 30 giây; lỗi
400/401/403 không retry. Hết retry ghi warning và để crawler tiếp tục.
Chưa có outbox phát lại qua restart; timeout sau khi server nhận tin có thể
tạo bản gửi trùng. Xem [runbook retry](telegram-crawler-control.md).

Root Makefile thêm `release-publish-deploy`: validate local, build/push image,
rồi deploy host bundle tuần tự; build lỗi không deploy. Trong lần phát hành
này chạy từ source đã export, không build từ working tree đang có thay đổi khác.
Xem [lệnh deploy](crawler-deployment.md).

## Kiểm chứng

- Local: 177 test crawler được chạy, 164 đạt và 13 opt-in dependency/DB skip;
  test building riêng thuộc thay đổi khác được loại khỏi lượt kiểm tra.
  Compose release validate và diff check đạt. Source export không chứa VPN
  private, nên test đếm 23 profile không chạy được trên bản export; inventory
  này được kiểm tra trong lượt test tại workspace trước khi phát hành.
- Build/push linux/amd64 và linux/arm64 đạt; VPS pull đúng digest
  `sha256:20a3b6dd29d6ef68067fab47a0ac355e65edcb43e489becec807c353c82b19c7`.
- 25 host checksums khớp source commit; notifier trong image khớp host.
  QA image trên VPS với network none/read-only/cap-drop ALL và HTTP mock đạt:
  timeout → network error → HTTP503 → thành công lần thứ tư, hết retry và
  lỗi403. Không bật VPN, crawl SUUMO hoặc gửi Telegram thật để thử.
- Pipeline idle/success, host VPN inactive/masked, không có container worker
  hoặc VPN. Bot active, timer mỗi phút enabled/active, dispatcher success.
  Menu private owner có đủ 9 lệnh; PostgreSQL và MinIO healthy, container IDs
  không bị recreate. Cấu hình .env giữ nguyên mọi giá trị ngoài image tag.
- DB có 41 run/74.112 URL, 24 ward và 23 VPN; không chạy migration/bootstrap.
  Queue rỗng; run41 Fukushima completed và cleanup_confirmed=true, cleanup
  07:45:42 +07. Hôm nay 1 run/4.505 URL; giờ chạy bù vẫn **08:45:43 +07**,
  không reset cooldown hoặc lịch khi deploy.

Backup private runtime/config tại
`/opt/suumo-crawler/.releases/20261010-telegram-retry-01-1a1dd135`.
QA snapshot nằm ở `.releases/telegram-retry-qa-after.json`, bundle upload được
giữ tại `/tmp/suumo-release-3754fd4c31ac4163a7e529c6382498a6` để kiểm tra.
