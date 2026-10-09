# Pool VPN cho crawler

Mỗi pipeline chọn một cấu hình VPN, dùng xuyên suốt links/HTML/parse và chỉ kết
thúc sau cleanup. Danh mục nằm trong PostgreSQL crawler; file chứa certificate/key
nằm riêng trên host, không đưa vào Git, Docker build context, image hoặc host bundle.

## Đồng bộ từ máy local

```bash
make -C suumo_source_crawler vpn-sync
make -C suumo_source_crawler vpn-sync opts="--dry-run"
```

Mặc định: SSH alias `thuevpsgiare`, source `suumo_source_crawler/vpn_config`,
runtime `/opt/suumo-crawler`, thư mục remote đọc từ `VPN_CONFIG_DIR` trong `.env`
hoặc mặc định `<runtime>/vpn_config`. Lệnh đầu thực sự upload và đăng ký DB.
Dry-run đọc inventory remote nhưng không upload, ghi DB hay thay cấu hình.

```bash
make -C suumo_source_crawler vpn-sync host=my-vps \
  vpn_source=/path/to/vpn_config remote_root=/opt/suumo-crawler

# Chuyển toàn bộ pool sang một thư mục khác trên host đã có runtime/schema.
make -C suumo_source_crawler vpn-sync vpn_dir=/srv/crawler-vpns
```

Chỉ gửi basename `.ovpn` chưa tồn tại. Tên đã có không bị ghi đè, kể cả checksum
local khác; kết quả có `different_content_skipped`. File remote thiếu dòng DB được
đăng ký lại từ file remote. Nếu upload xong nhưng DB lỗi, chạy lại hoàn tất đăng ký
mà không gửi lại file. Lỗi trả exit code 1; thành công báo `uploaded`,
`skipped_existing`, `registered`, `remote_files`.

File phải self-contained với inline ca/cert/key, một remote IPv4 và interface tun;
không có script hook hoặc credential tương tác. Thư mục remote quyền 700,
file quyền 600. Upload đồng thời dùng `state/vpn-sync.lock`; thêm file có thể làm
trong lúc crawl. Đổi thư mục gốc yêu cầu crawler/VPN rảnh, shared lock và đủ toàn bộ
file đã đăng ký với checksum cũ. Chỉ sau đó cập nhật `VPN_CONFIG_DIR`; ID và thống
kê được giữ nguyên. Thư mục cũ không bị xóa.

## Chọn và thử VPN

`crawl_vpns.enabled=true`, sắp `last_attempt_at ASC NULLS FIRST, filename ASC`.
Lần thử được ghi trước systemd, gồm cả cấu hình lỗi; vì vậy VPN lỗi xuống cuối
thứ tự lần sau. `last_used_at` chỉ cập nhật khi đã kết nối ổn định.

Mỗi cấu hình thử một lần, tối đa 60 giây cho activation; cần ba health check liên
tiếp cách nhau hai giây: service active, tun0 UP, hai route def1 qua tun0. Trước mỗi
lần đổi file phải xác nhận service/process/tunnel/IPv4+IPv6 routes đã tắt bằng
cleanup hiện có. Thời gian cleanup nằm ngoài 60 giây activation.

Runtime atomically tạo `/etc/openvpn/client/japan.conf`, chuẩn hóa `dev tun0` và
`redirect-gateway def1`, giữ inline certificate/key và route SSH qua `net_gateway`.
File gốc không đổi. SSH IPv4 hiện tại được lưu qua lần sync và đọc thêm từ kết nối
SSH hiện có/cấu hình cũ. Các route này dùng gateway trước VPN theo
[OpenVPN manual](https://openvpn.net/community-docs/community-articles/openvpn-2-6-manual.html).

Thử hết pool tạo một lượt `preflight_failed`, zero HTML URLs, tiêu một lượt/ngày.
Không xác nhận được shutdown thì chặn fallback và lượt sau. DB lỗi thì không bắt
đầu activation mới. Mất VPN giữa crawl không đổi cấu hình trong lượt đó; xử lý lỗi
và cleanup như pipeline hiện có. Khác tên cấu hình không bảo đảm khác IP công khai.

Restart không phát lại trial: attempt pending được đánh dấu interrupted khi cleanup
đã được xác nhận; không cộng vào thành công/thất bại vì chưa biết kết quả.

## Thống kê request

`total_requests` đếm từng lần HTTP downloader được khởi tạo cho `suumo.jp` và
subdomain: trang tìm kiếm/phân trang, HTML, redirect, retry và lỗi DNS/connect/tải.
Không đếm Telegram, MinIO, DB, scheduler duplicate, task bị claim loại hoặc cache hit.
Đây là số lần tải do crawler khởi tạo, không phải số packet hay số URL HTML.

Middleware chạy sau task claim và HTTP cache, ghi UUID mới cho mỗi lần tải trước
download handler; retry DB dùng cùng UUID. Function `record_crawl_vpn_request`
ghi journal và tăng counter trong một transaction, kiểm tra run đang running với
VPN đã activation success. Cách đặt middleware theo thứ tự được mô tả trong
[Scrapy downloader middleware](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html).

DB lỗi thì chặn download mới, đóng spider và để host fail pipeline kể cả Scrapy
exit 0. Context release thiếu hoặc đã đóng cũng bị chặn. Local direct crawl không
khai báo VPN được giữ hoạt động và không gán request cho VPN nào. Tổng và attempt
historical trước tính năng này không được suy đoán/backfill.

```sql
SELECT vpn_id, filename, relative_path, total_requests,
       activation_successes, activation_failures, last_attempt_at, last_used_at
FROM crawl_vpns ORDER BY last_attempt_at NULLS FIRST, filename;
```

Status/history và thông báo pipeline có tên file VPN, giữ địa chỉ ward/escape HTML.

## Rerun HTML trên VPS

```bash
cd /opt/suumo-crawler
python3 suumo_source_crawler/scripts/run_release_pipeline.py \
  --rerun-failed-html --area-id 23 --limit 10
```

Trên checkout có Makefile: `make release-manual-rerun-failed-html
opts="--area-id 23 --limit 10"`. Rerun một ward, tạo run trước preflight, chọn VPN,
HTML dùng lại run đó, parse task cùng run và cleanup. `--limit` áp dụng trong ward.
Tool container gọi trực tiếp trên release sẽ từ chối download khi thiếu context
đã xác nhận; dry-run của tool vẫn xem/report được mà không bật VPN.

## Phát hành lần đầu

```bash
make release-deploy host=thuevpsgiare tag=<new-tag> \
  opts="--apply --enable-vpn-pool"
```

Installer pause bot/timer khi crawler rảnh; backup DB, SQLite, .env/managed files
và japan.conf. Archive VPN riêng private được kiểm tra SHA-256, áp dụng riêng
migration 009, upload/register file trước khi resume dispatcher. Không bật VPN,
crawl thật hoặc reset `automatic_start_at`/`next_auto_at`; không dùng lại flag
`--enable-ward-dispatch` cho cập nhật này. Lần sau thêm file dùng `vpn-sync`.
