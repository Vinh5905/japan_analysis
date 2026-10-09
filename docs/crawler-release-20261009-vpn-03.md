# Release pool VPN — 2026-10-09

Đã triển khai image/bundle **20261009-vpn-03** lên `thuevpsgiare`, runtime
`/opt/suumo-crawler`. Digest multi-platform:
`sha256:21cb803aa1b1dcca4c7cb924b001631c9009278704ea7cc62eadbad78b588a90`.

## Thay đổi

- Migration 009: crawl_vpns, crawl_vpn_attempts, crawl_vpn_requests,
  crawl_runs.vpn_id/vpn_snapshot và function ghi request atomically/idempotently.
- Pool 23 cấu hình; chọn last_attempt_at cũ nhất, chưa thử trước; một trial/VPN/run,
  60 giây activation, ba lần kiểm tra ổn định. Fallback cần shutdown đã xác nhận.
- Failed trial cập nhật thứ tự; success/failure counter chỉ ghi một lần;
  restart pending ghi interrupted. Toàn bộ fallback giữ một crawl_run/day-budget.
- Request accounting sau task claim/cache: pages/HTML/retry/redirect/lỗi tải;
  DB/context lỗi đóng spider và host fail-fast kể cả exit zero/mất summary.
- `make -C suumo_source_crawler vpn-sync`: chỉ gửi tên mới, skip tên cũ,
  đăng ký bổ sung file remote; đường dẫn tương đối + VPN_CONFIG_DIR portable.
- Rerun VPS qua host runner, một ward, cùng VPN/run và LIMIT riêng trong ward.
- Status/history/lifecycle có tên file VPN; không chứa private config trong image/bundle.

## Kiểm chứng

- Suite cuối: 154 test gồm PostgreSQL QA; Docker/systemd/VPN được mock cho activation.
- HTTP server localhost trong image arm64 (Scrapy 2.17) và amd64 (Scrapy 2.19):
  9 downloads pages/redirect/retry/lỗi; cache/dedupe/internal không đếm;
  task claim thêm đúng 1; context đóng chặn trước HTTP. QA DB riêng tự drop.
- Repository/spider/rerun QA: HTML reuse run, parser scope, links riêng,
  rerun tách ward; managed rerun reuse preflight run và limit trong đúng ward.
- VPS: 24 host checksums, 6 image source checksums, digest/import, 23 file/DB
  checksums/quyền 700/600, migration function, menu 9 lệnh, status/history card,
  catalogue 24 ward và dispatcher Result=success.
- Stats VPN ban đầu đều 0, last_attempt/last_used NULL. Tổng cũ **39 run/65.551 URL**
  giữ nguyên; không suy đoán lịch sử VPN.
- Chạy thật lệnh sync lần nữa: new=0, skipped_existing=23, uploaded=0,
  registered=0, different_content_skipped=[]; không overwrite hoặc duplicate DB.
- `japan.conf` SHA-256 trước/sau:
  `c95075bb458f395a8132bf1cc60cafbe04245f352949d4191f138acca423d4ef`.
  Không bật OpenVPN/crawl SUUMO để kiểm thử deploy.

Bot/timer active; crawler/OpenVPN inactive. Giữ `automatic_start_at` và
`next_auto_at` = **2026-10-10 00:00 +07**, queue trống.

## Backup và cập nhật host

Initial rollout backup `/opt/suumo-crawler/.releases/20261009-vpn-03-c9a3878b`:
private pg_dump, SQLite snapshot, managed files/.env và japan.conf. Chỉ migration
009 được áp dụng; không chạy lại migration 008/khởi tạo lịch ward.

Kiểm tra CLI qua SSH phát hiện Compose exec -T vẫn đọc stdin và làm mất tar stream
trước receive. Đã sửa `host_command` dùng DEVNULL, thêm regression với stdin child
thật, redeploy host bundle cùng image tag (không đổi source image/migrate DB).
Backup managed files bổ sung `.releases/20261009-vpn-03-7759abb7`.
Lệnh sync và checksum acceptance đã chạy thành công sau sửa.

Raw configs ở `/opt/suumo-crawler/vpn_config`; archive private riêng nằm trong
thư mục deploy `/tmp` quyền 700, không thuộc host bundle. Xem
[runbook pool VPN](crawler-vpn-pool.md) cho sync, relocation, stats và rerun.
