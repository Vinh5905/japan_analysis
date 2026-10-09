# Crawl một ward và điều phối Telegram

Từ release `20261009-vpn-03`, mỗi lượt chọn VPN theo lần thử xa nhất, fallback
trước crawl và giữ VPN suốt lượt; counters gồm pages/HTML/retry/redirect.
Xem [pool VPN](crawler-vpn-pool.md) cho upload, paths portable, thống kê và rerun.

Mỗi pipeline chạy đúng một ward Osaka City. Mục tiêu 10.000 URL **đã xử lý** mỗi ngày (HTML thành công + thất bại); tối đa 5 lượt tự động, tính cả thủ công và lỗi trước HTML. Lượt Telegram được chạy vượt mục tiêu/hạn mức; khi vượt, tự động nghỉ đến ngày mới. Mọi lượt tính theo `crawl_runs.created_at` tại `Asia/Ho_Chi_Minh`; lượt qua nửa đêm vẫn thuộc ngày bắt đầu.

## Danh mục và schema

Migration duy nhất của release này: `docker/postgres/migrations/008_crawl_areas_and_pipeline.sql`. Bootstrap fresh có cùng schema. `crawl_areas.area_id` là định danh ổn định, độc lập với mã `sc`. Địa chỉ gồm prefecture/district/municipality/ward tiếng Nhật; district Osaka City là NULL. 24 tên tiếng Anh nằm riêng trong danh mục. Không reset sequences hoặc xóa lịch sử khi đồng bộ.

`crawl_area_catalogs` ghi phạm vi `osaka_city`, URL nguồn và `synced_at`. Lần đầu chưa có sync thành công sẽ tải HTML checkbox từ https://suumo.jp/chintai/osaka/city/. Sau đó khởi động/dispatcher bỏ qua tải lại. Đồng bộ kiểm tra đủ 24 ward gốc, mã đúng định dạng và không trùng; transaction khóa bảng, upsert theo địa chỉ ổn định, chỉ cập nhật `sc`, giữ tên/địa chỉ/ID và lịch sử. Cho phép đổi chéo mã nhờ unique constraint deferred. HTML không hợp lệ hoặc lỗi DB rollback toàn bộ, kể cả timestamp. Khu vực bổ sung chưa có tên Anh dùng tên hiển thị riêng `Osaka ward <sc>` để cập nhật thủ công sau.

Lịch sử cũ source SUUMO được gán **Yodogawa / 淀川区** theo xác nhận, không đổi `total_urls`, không đoán trạng thái pipeline. Thống kê ward query `COUNT(*)`, `MAX(created_at)` trực tiếp.

`crawl_runs` mới có `area_id`, `pipeline_key` unique, `search_url`, `area_snapshot`, `pipeline_status`, `pipeline_finished_at` và `cleanup_confirmed_at`. Row được tạo **trước VPN**, lỗi preflight vẫn có 0 URL và tiêu một lượt. `finished_at` tiếp tục chỉ là thời điểm kết thúc HTML. Trạng thái pipeline: running/completed/preflight_failed/crawl_failed/cleanup_failed/interrupted; lượt cũ NULL.

## Điều phối và recovery

Timer `suumo-crawler-pipeline.timer` đánh thức **`suumo-crawler-dispatch.service` mỗi phút**. Telegram và cleanup cũng gọi dispatcher nonblocking. Timer không trực tiếp chạy crawler. Dispatcher giữ `.release.lock`, kiểm tra systemd, container và DB trước start. Lượt đang chạy/cleanup tiếp tục bình thường.

Chọn ward chưa thử hôm nay trước; trong nhóm đó ưu tiên số lượt lịch sử thấp nhất, thời điểm gần nhất xa nhất (NULL trước), rồi mã `sc`. URL giữ tham số cấu hình và chỉ còn đúng một `sc`, bỏ page cũ. Context được chụp tại launch, gồm địa chỉ và URL; refresh không thay lượt đang chạy. File links `tmp/runs/<pipeline_key>/links.txt`; HTML dùng lại exact DB run, không tự tạo row; parse trong pipeline chỉ đọc `SUUMO_RUN_ID` hiện tại.

SQLite `state/telegram-control.sqlite3` lưu hàng chờ tối đa **một** ward, intent launch, lịch nghỉ và offset. Nút dùng một lần trong 120 giây; consume nonce và ghi hàng chờ cùng transaction. Yêu cầu đã nhận không hết hạn và không bị yêu cầu mới thay thế. Chỉ gỡ hàng chờ khi preflight tạo được DB run; lúc chờ chưa tiêu lượt ngày. Lệnh `/run_crawl` chưa tiếp nhận quá 5 phút vẫn bị từ chối.

Intent/key được lưu trước systemctl. Crash trước systemctl: dispatcher thử lại **cùng key**; DB unique chống row trùng. Crash sau tạo row: không crawl lại. Cleanup thiếu xác nhận chặn lượt mới; nếu host restart bỏ lỡ hook, dispatcher chỉ recovery sau **ba tick cách nhau ít nhất 30 giây** xác nhận OpenVPN inactive/failed, MainPID=0, tunnel absent/DOWN và không còn route IPv4/IPv6 qua tunnel. Không tự bật/tắt VPN để recovery này. Run chưa hoàn tất thành interrupted; run cleanup_failed giữ kết quả lỗi, bổ sung xác nhận shutdown. Hàng chờ cùng key đã thực thi được gỡ; ward khác vẫn chờ.

Cleanup ghi kết quả DB và SQLite, hẹn tự động **cleanup hoàn tất + 1 giờ**. Thủ công trong thời gian nghỉ thay hẹn cũ: xong 10:50 thì sớm nhất 11:50 dù trước đó hẹn 11:00. DB lỗi chặn khởi động và giữ queue; cleanup ghi DB lỗi cũng chặn đến recovery. Đạt 5 lượt nhưng dưới 10.000 gửi thiếu hụt một lần/ngày. Ngày mới tính lại budget; vẫn tôn trọng một giờ nghỉ nếu lượt qua nửa đêm.

## Telegram và CLI

- `/run_crawl`: danh sách 5 ward/trang, tên Anh, số lượt và ngày `dd/mm/yyyy` hoặc Chưa chạy; chọn → địa chỉ/phạm vi → xác nhận. Khi bận vẫn có thể xếp một ward chờ.
- `/areas`: cùng danh mục, không tạo yêu cầu.
- `/refresh_areas`: service nền một bản, gửi số thêm/cập nhật/giữ nguyên; khi đang sync báo tiến độ.
- `/status`: ward, bước, VPN, queue và tiến độ ngày.
- `/schedule`: timer calendar thực tế + quyết định dispatcher, thời điểm dự kiến hoặc lý do chờ.
- `/history`: 5 pipeline gần nhất, ward và kết quả, gồm lỗi VPN/cleanup.
- `/total`: tổng lịch sử + hôm nay và số lượt / 5.
- `/start`, `/help`: menu và quy tắc mới.

Giữ auth owner/private, escape HTML, redaction secret, ack callback trước query, chống update trùng. Mọi lifecycle có địa chỉ lượt. Không có lệnh sửa/bật/tắt lịch trong bot.

CLI đồng bộ (không gửi Telegram):

```bash
PYTHONPATH=suumo_source_crawler python3 -m scripts.area_catalog \
  --env-file .env --compose-file docker-compose.release.yml --refresh
```

Runner host trực tiếp chọn ward theo quy tắc hoặc nhận `--area-id <id>`, chạy manual với cùng preflight/cleanup. Để thao tác trên VPS ưu tiên bot. Các lệnh HTML độc lập cần DB run đã chuẩn bị trong `SUUMO_RUN_ID`; không chạy command HTML cũ rồi để spider tạo lượt không có ward. Công cụ `manual-rerun-failed-html` chia failed tasks theo ward gốc, reserve exact run từng ward, file links riêng và report `area_id`; đây là công cụ HTML-only, không có pipeline_key/VPN lifecycle. Row HTML-only không đoán trạng thái pipeline, nhưng vẫn tính budget ngày.

## Deploy và kiểm tra

Build image mới và host bundle cùng source. Crawler phải rảnh; installer dừng bot/timer, kiểm tra lại container, backup file/config, pg_dump DB và SQLite nhất quán, áp **chỉ migration 008**, sync lần đầu rồi enable bot/timer. `--enable-ward-dispatch` thay timer và đặt `automatic_start_at` bằng 00:00 Việt Nam **ngày sau triển khai**; không chạy crawler/VPN để thử.

```bash
python3 suumo_source_crawler/scripts/deploy_release.py deploy \
  --tag 20261009-wards-01 --host thuevpsgiare --apply \
  --enable-telegram-bot --enable-ward-dispatch
```

Nếu IP VPS bị SUUMO trả HTTP 503, tải HTML danh mục mới ở local rồi thêm `--catalog-html <file>` khi deploy. File được chuyển cùng SHA-256, kiểm chứng trước apply, parse/transaction giống tải trực tiếp và lưu nguồn HTML/checksum trong backup. Không bật VPN trong deploy. `/refresh_areas` sau đó vẫn tải trực tiếp; 503 sẽ báo lỗi và giữ danh mục.

Backup riêng tư ở `.releases/<tag>-<suffix>/`, gồm `crawler-db.sql`, SQLite và ánh xạ file `paths.json`. Rollback file không rollback DB additive; không import DB dump đang chạy. Giữ nguyên credentials, volumes, VPN config và SSH route.

```bash
python3 -m unittest discover -s suumo_source_crawler/tests -v
SUUMO_WARD_DB_TESTS=1 SUUMO_TELEGRAM_DB_TESTS=1 \
  python3 -m unittest discover -s suumo_source_crawler/tests -v
```

Test PostgreSQL ward tạo/xóa DB QA riêng; test reporting dùng TEMP fixtures. `integration_ward_crawler.py` chạy trong release image với DB QA local để kiểm chứng repository/spider/rerun, không khởi động Scrapy network engine. Kiểm tra VPS: checksum bundle, image digest/import, schema/backfill, menu, render đọc bằng API giả, bot/timer active, crawler/VPN inactive, `automatic_start_at` đúng ngày sau deploy. Xem biên bản release riêng.
