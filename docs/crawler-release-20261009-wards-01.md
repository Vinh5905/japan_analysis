# Release `20261009-wards-01` — 2026-10-09

Đã triển khai lên `thuevpsgiare`, `/opt/suumo-crawler`. Pipeline mỗi lượt một ward, dispatcher mỗi phút, mục tiêu ngày 10.000 URL / tối đa 5 lượt, hàng chờ Telegram bền vững tối đa một ward. Lịch tự động bắt đầu **2026-10-10 00:00:00 Asia/Ho_Chi_Minh**. Không chạy thử crawler hoặc VPN thật.

## Artifact và backup

- Image đa nền tảng: `kevinpham9257/suumo-crawler:20261009-wards-01`.
- Digest: `sha256:988d6ca8a74e3ab5d5aa7e2f8e97f816bc3e012519579ab8ba060ef3dd232b3d`.
- Host bundle gồm 22 file checksum: `tmp/releases/suumo-host-20261009-wards-01.tar.gz`.
- Bundle VPS: `/tmp/suumo-release-6abd33ae1b4f425385e75191e4dba2e0/release.tar.gz`.
- Backup deploy thành công: `/opt/suumo-crawler/.releases/20261009-wards-01-4bd4e920`; file/config theo `paths.json`, `crawler-db.sql`, SQLite nhất quán, HTML danh mục và SHA-256. Tất cả file chứa cấu hình/dữ liệu backup quyền 600, directory 700.
- Backup lần đầu trước migration: `/opt/suumo-crawler/.releases/20261009-wards-01-3bb2c3cf`; giữ lại để truy xuất schema trước 008.
- Log local: `/tmp/ward-final-tests.log`, `/tmp/ward-deploy-2.log`; kiểm chứng VPS: `tmp/ward-release/vps-verification.txt`. Script đọc/kiểm chứng ở `tmp/ward-release/verify_vps.py`, không gửi tin thử hoặc cập nhật offset.

## Đồng bộ danh mục và ngoại lệ HTTP 503

Lượt deploy đầu dừng do SUUMO trả HTTP 503 cho IP VPS; kiểm tra lại bằng User-Agent trình duyệt cũng trả 503. Installer rollback file/cấu hình/lịch và khôi phục bot; migration 008 additive đã hoàn tất, không rollback DB hoặc đổi tổng lịch sử. Crawler/VPN vẫn inactive.

Lượt deploy thứ hai dùng HTML **vừa tải lại từ URL SUUMO chính thức ở local**, chuyển qua `--catalog-html` với SHA-256 kiểm chứng trước apply. Nguồn: `https://suumo.jp/chintai/osaka/city/`; checksum HTML `a147e129533a9731d70604fa8d6b739489fa209034e7eafe97603fac84f73e02`. Cùng parser checkbox/validation/transaction DB, không hardcode catalog thành công hay bỏ qua kiểm tra. Kết quả sync: 0 thêm, 0 đổi mã, 24 giữ nguyên; `synced_at=2026-10-09 15:13:40.905593+07`.

`/refresh_areas` sau deploy vẫn tải trực tiếp từ SUUMO; nếu IP VPS tiếp tục nhận 503 thì bot báo thất bại và giữ nguyên danh mục. Không bật VPN để xử lý trong deploy này. Có thể dùng CLI cùng HTML mới khi cần refresh ngoài Telegram, hoặc thử bot khi kết nối SUUMO cho phép; không dùng lại HTML cũ để giả refresh thành công.

## Kiểm chứng

**130 test đạt**, không skip trong lần cuối gồm SQL PostgreSQL local. Test ward SQL tạo/xóa DB QA riêng, reporting dùng TEMP fixtures. Bao gồm migration fresh/upgrade/idempotent, backfill, thống kê, đổi chéo `sc` giữ ID/tên/lịch sử, thêm ward, rollback lỗi DB/HTML; target/max-run/manual override, ngày mới/midnight, queue/nonce/restart/shared lock, crash giữa intent và systemctl, recovery sau ba tick xác nhận shutdown, cleanup failure và đổi giờ nghỉ. Test installer kiểm tra backup DB/SQLite/HTML, rollback, áp riêng migration 008 và giờ bắt đầu ngày sau.

Kiểm tra code trong image local đã đạt: HTML dùng exact run và từ chối replay HTML đã đóng, parser không trộn hai run, file links theo context, rerun hai ward tạo hai row/report riêng. Không khởi động Scrapy network engine, không fetch listing/HTML thật, không VPN.

VPS kiểm chứng 22 checksum host; image digest và import spider/repository; chỉ image process import với network none, không chạy crawler. DB giữ **39 lượt / 65.551 URL**, 24 ward, 39 lượt cũ thuộc Yodogawa và trạng thái pipeline cũ NULL. Menu private chat đúng 9 lệnh, webhook trống; 8 màn hình đọc render qua API giả với dữ liệu VPS, HTML/callback phù hợp giới hạn Telegram; offset không đổi trong kiểm chứng (`738763747`). `.env` so với backup chỉ thay image tag.

Bot enabled/active, `NRestarts=0`; timer enabled/active, calendar thực tế `*-*-* *:*:00 Asia/Ho_Chi_Minh`, trỏ dispatcher. Các tick 15:16 và 15:17 đã thực thi dispatcher, `Result=success`, `ExecMainStatus=0`, báo **Chờ ngày bắt đầu lịch mới**. SQLite lưu `automatic_start_at=next_auto_at=2026-10-10T00:00:00+07:00`, queue trống. Crawler inactive/result success, OpenVPN inactive/MainPID=0; Postgres và MinIO healthy, credentials/volumes/VPN config giữ nguyên.

Runbook: [Crawl một ward và điều phối Telegram](crawler-ward-dispatch.md). Kiểm chứng crawl/VPN thật lần đầu thuộc lượt sử dụng sau deploy; release này chỉ kiểm tra bằng mocks, DB QA và thao tác đọc/import trên VPS.
