# Deploy crawler SUUMO

Crawler chạy từ Docker image; runner, VPN preflight và Telegram helper chạy trên host. `make release-deploy` gom toàn bộ host runtime thành một bundle có checksum, rồi đồng bộ qua SSH khi truyền `--apply`. Mặc định lệnh chỉ in kế hoạch tại local, không kết nối VPS.

OpenVPN hiện chạy trong service Docker `vpn`; worker links/HTML/parse/rerun
chia sẻ namespace của VPN, host giữ SSH và published ports PostgreSQL/MinIO.
Xem [runbook Docker VPN](crawler-docker-vpn.md). Chuyển từ backend host bằng
`opts="--apply --container-vpn"`: backup DB/SQLite/.env/units và enabled state
VPN host, đổi backend và mask instance cũ. Installer không bật VPN/crawl,
không chạy migration hoặc reset lịch; rollback phục hồi file và enabled state.

## Quy trình cập nhật

Pool VPN dùng [runbook riêng](crawler-vpn-pool.md). Lần đầu truyền
`--enable-vpn-pool` để backup DB/state/japan.conf, áp dụng riêng migration 009
và đồng bộ archive cấu hình private trước khi resume lịch hiện có. Thêm cấu hình
sau đó bằng `make -C suumo_source_crawler vpn-sync`; không chứa keys trong bundle.

Chạy từ root repository. Chọn một tag mới cho mỗi lần phát hành, ví dụ `20261009-01` hoặc commit SHA. Image và host bundle phải được tạo từ cùng một phiên bản source. Nếu thay đổi source sau khi build, build lại với tag mới; không ghi đè tag đã phát hành.

Một lệnh build/push image đa kiến trúc rồi deploy host bundle theo thứ tự:

```bash
make release-publish-deploy host=thuevpsgiare tag=20261010-telegram-retry-01
```

Lệnh này thực sự publish/deploy; trước build sẽ validate host/tag bằng dry-run
local, build lỗi thì không deploy. Cần Docker chạy và đã login Docker Hub.
Installer từ chối khi crawler/VPN/cleanup đang chạy; không tự hủy lượt hiện tại
hoặc đợi đến khi rảnh. Nếu image đã build/push thành công nhưng VPS còn bận,
chạy lại riêng `make release-deploy host=thuevpsgiare tag=<cùng-tag> opts="--apply"`
sau cleanup. Source build là working tree hiện tại, gồm cả thay đổi crawler
chưa commit; kiểm tra các thay đổi khác trước khi phát hành.
Backend Docker/lịch/queue hiện có được giữ, không cần cờ migration.

```bash
# Build/push image từ local khi đã sẵn sàng publish.
make docker-build-push-release tag=20261009-01

# Xem kế hoạch; KHÔNG gọi SSH, scp, Docker hoặc systemctl.
make release-deploy host=suumo-vps tag=20261009-01

# Khi đã sẵn sàng triển khai, lệnh này mới kết nối và thay đổi VPS.
make release-deploy host=suumo-vps tag=20261009-01 opts="--apply"
```

`suumo-vps` là alias trong `~/.ssh/config`, chứa hostname, user, SSH port và private key theo runbook. Installer chạy bằng user `root`; nếu dùng user khác, hiện cần chạy installer riêng với quyền quản trị, chưa tự thêm `sudo`. VPS cần Python >= 3.10, Docker Compose v2 hỗ trợ `up --wait`, systemd và cấu hình OpenVPN đã hoạt động. Thư mục mặc định là `/opt/suumo-crawler`; đổi bằng `DEPLOY_TARGET=/đường/dẫn` (không chứa khoảng trắng).

Có thể chỉ tạo gói trên local, không build image và không kết nối VPS:

```bash
make release-package tag=20261009-01
```

Output mặc định: `tmp/releases/suumo-host-20261009-01.tar.gz`. Thư mục này bị Git ignore. Bundle không chứa `.env`, VPN keys, dữ liệu tmp, `state/telegram-control.sqlite3` hay data volumes. Danh sách file chính xác nằm ở `HOST_FILES` trong `suumo_source_crawler/scripts/deploy_release.py`, gồm Compose release, runner, VPN preflight/shutdown, shared lock, Telegram helper, installer và service/timer templates. Không cần nhớ copy từng dependency nữa.

## Khi áp dụng, lệnh làm gì?

1. Upload bundle vào thư mục riêng trong `/tmp` trên VPS và kiểm tra checksum.
2. Lấy lock chung với runner, yêu cầu crawler service không đang chạy/khởi động/dừng và kiểm tra cả container crawler chạy thủ công theo Compose project. Timer và bot Telegram đang active được tạm dừng trong suốt quá trình cập nhật.
3. Dùng `.env` hiện có trên VPS, chỉ thay `SUUMO_CRAWLER_TAG` bằng tag yêu cầu; kiểm tra Compose, pull image crawler mới và chỉ pull PostgreSQL/MinIO nếu đúng image cấu hình chưa có trên host, trước khi thay file runtime.
4. Backup các file bị thay vào `.releases/<tag>-<id>/` trên VPS. Backup có thể chứa `.env`, nên được đặt quyền riêng tư.
5. Cài đủ host files và service; giữ lịch timer hiện tại. Nếu chưa có timer, cài template nhưng không tự enable timer.
6. Reload systemd; chạy `up -d --pull never --wait postgres minio`. Compose áp dụng cấu hình mới, chỉ recreate service cần thay đổi và giữ named volumes.
7. Thả lock rồi khôi phục bot/timer nếu trước deploy chúng đang active. Bot mới chỉ được kích hoạt với `--enable-telegram-bot`; SQLite được giữ nguyên.

Lệnh không gọi crawler, bootstrap, migration hay thay cấu hình VPN. Timer đang hoạt động được khôi phục có thể chạy bù một lịch đã lỡ do `Persistent=true`. Nếu muốn tự quyết định lúc chạy tiếp, tắt timer trước khi deploy; installer sẽ giữ trạng thái tắt đó.

Nếu pull lỗi, runtime files và tag cũ được giữ nguyên. Nếu cài file hoặc cập nhật infra lỗi, installer phục hồi file/tag cũ và thử áp dụng lại infra config cũ. Đây là rollback file/config, không phải rollback database hoặc một bảo đảm khôi phục khi máy mất điện/process bị kill. Bundle đã upload được giữ trong `/tmp` để kiểm tra.

VPN có thể làm Docker Hub không truy cập được. Installer **không tự tắt/bật VPN** vì liên quan đến route SSH. Khi gặp trường hợp này, xử lý kết nối theo runbook rồi chạy lại deploy. Registry pull không nằm trong job định kỳ.

## Lịch chạy

### Vòng đời VPN trong mỗi lượt crawl

Service systemd chạy preflight để xác nhận VPN khỏe trước khi crawl; `ExecStopPost` gọi `scripts/stop_openvpn.py` sau lượt chạy, kể cả khi crawler/preflight lỗi hoặc service bị stop. Hook cleanup này được [systemd thiết kế để chạy cả khi khởi động thất bại](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml). `TimeoutStopSec=10min` dành thời gian cho bước dọn dẹp; cleanup trả khác 0 hoặc timeout làm lượt service failed, không báo đóng VPN thành công.

Cleanup kiểm tra các container pipeline còn chạy trong đúng Compose project; nếu lượt chạy bị ngắt, dừng chúng trước khi đóng tunnel. PostgreSQL/MinIO được giữ. Nếu không xác nhận được container đã dừng, cleanup báo lỗi và giữ VPN để crawler chưa kết thúc không chuyển sang IP public.

Backend Docker stop/remove sidecar trong đúng Compose project, xác nhận ba
quan sát không còn container VPN chạy. Hook cũng yêu cầu instance host cũ
inactive/failed với MainPID=0 và không còn tunnel/routes. Docker inspection lỗi
chặn lượt tiếp theo. Backend host legacy vẫn giữ shutdown service/process/routes.
Telegram gửi thông báo đang tắt, đã xác nhận tắt hoặc cleanup thất bại; summary
toàn pipeline chỉ gửi sau cleanup đã xác nhận.

Chạy trực tiếp `python3 suumo_source_crawler/scripts/run_release_pipeline.py ...` cũng tự preflight và cleanup trong `finally`, kể cả khi crawl lỗi. Chỉ systemd unit dùng `--vpn-managed-by-systemd` vì đã có hooks; không dùng cờ này khi chạy thủ công. Các lệnh `docker compose run ...` đơn lẻ không có vòng đời VPN tự động này: ưu tiên service/runner cho lượt chạy đầy đủ.

Chuyển sang Docker VPN cần image mới chứa client/firewall/supervisor và host
bundle tương ứng. Preflight tạo namespace VPN mới trước mỗi lượt; cleanup dừng
worker rồi đóng sidecar. Container restart=no, không bật khi boot; host OpenVPN
instance masked. Unit không ràng buộc Wants/After với service VPN host.

Template `suumo_source_crawler/deploy/systemd/suumo-crawler-pipeline.timer`
đánh thức dispatcher mỗi phút; quyết định chạy/nghỉ nằm trong SQLite và DB.
Lịch hiện tại bắt đầu 2026-10-10 00:00 +07, cooldown cleanup + 1h. Sửa template rồi dùng:

```bash
make release-deploy host=suumo-vps tag=20261009-02 opts="--apply --update-timer"
```

Không truyền `--update-timer` thì giữ file lịch hiện có trên VPS. Khi setup lần đầu, chỉ enable timer sau khi VPN và pipeline đã được kiểm tra:

```bash
systemctl enable --now suumo-crawler-pipeline.timer
```

## Thay đổi nào cần image mới?

| Thay đổi | Cách cập nhật |
| --- | --- |
| Spider/parser/settings, dependencies, Dockerfile.release, wrapper, bootstrap, SQL | Build/push tag mới rồi deploy tag đó |
| Runner/preflight/Compose/service | Deploy bundle mới; có thể tái dùng tag image hiện tại nếu source trong image không thay đổi |
| Telegram helper | Dùng cả trên host và trong image: build/push tag mới rồi deploy |
| Timer | Deploy với `--update-timer` |
| Giá trị cấu hình đã được hỗ trợ | Sửa `.env` trên VPS; crawler tạo container mới sẽ đọc lại |
| SQL migration cho DB hiện có | Build image chứa migration, deploy, rồi chạy migration riêng có chủ đích |

Bootstrap mặc định không nâng cấp schema hiện có. Không dùng reset DB để cập nhật code. Đổi mật khẩu PostgreSQL trong `.env` cũng không tự đổi mật khẩu role đã tồn tại. Giữ ổn định Compose project name và đường dẫn dữ liệu trong các lần deploy.

## Các cấu hình crawler đọc từ `.env`

Mẫu ở `.env.release.example` và cả Compose local/release đã truyền các biến:

- `SUUMO_SEARCH_URL`: URL tìm kiếm HTTPS trên `suumo.jp`; rỗng giữ bộ lọc Osaka/Yodogawa cũ.
- `SUUMO_HTML_LINKS_FILE`: cùng đường dẫn cho spider links và HTML; dùng `tmp/...` để chia sẻ qua mount giữa container.
- `SUUMO_HTML_LINK_LIMIT`, `SUUMO_PAGE_TASK_LIMIT`: `0` để xử lý toàn bộ.
- `SUUMO_PAGE_BATCH_SIZE`, `SUUMO_PAGE_BATCH_SECONDS`: số record/thời gian flush batch, phải > 0.
- `SUUMO_SOURCE_ID`, `SUUMO_SOURCE_BASE_URL`, `SUUMO_RUN_CREATED_BY`.
- `SUUMO_CONCURRENT_REQUESTS`, `SUUMO_CONCURRENT_REQUESTS_PER_DOMAIN`.
- `SUUMO_AUTOTHROTTLE_START_DELAY`, `SUUMO_AUTOTHROTTLE_MAX_DELAY`, `SUUMO_AUTOTHROTTLE_TARGET_CONCURRENCY`.

Sau khi deploy phiên bản code hỗ trợ các biến này lần đầu, chỉnh giá trị không cần build image lại. Scrapy CLI `-s NAME=value` vẫn có độ ưu tiên cao hơn settings từ environment. Thay URL tìm kiếm không xóa dữ liệu lịch sử hoặc thay đổi cơ chế bỏ qua URL đã crawl. Nếu dùng source ID mới, phải tạo `crawl_sources` tương ứng trước.

## Kiểm tra local

```bash
python3 -m unittest discover -s suumo_source_crawler/tests -v
docker compose --env-file .env.release.example -f docker-compose.release.yml --profile tasks --profile tools config --quiet
```

Các test deploy/VPN mock SSH/Docker/systemd/ip, kiểm tra bundle, dry-run, checksum, shared lock, giữ secrets/tmp/lịch, thất bại pull, rollback config, xác nhận shutdown và cleanup sau lỗi. Ngày 2026-10-09: 46 test đạt, Compose local/release validate đạt và đã kiểm tra environment từ Compose vào settings; chưa thay thế kiểm chứng container/deploy thực tế trên VPS.

## Bot Telegram điều khiển

Xem [menu, số liệu và runbook Telegram](telegram-crawler-control.md). Bot mặc định tắt; triển khai có chủ đích dùng `opts="--apply --enable-telegram-bot"`. Tính năng này cần image tag mới và host bundle cùng source vì formatter dùng cả trên host và trong image. Giữ nguyên thư mục `state/` khi cập nhật.

Ngày 2026-10-09 đã deploy release `20261009-telegram-01` lên `thuevpsgiare` và bật bot. Installer đã được sửa để tái sử dụng image hạ tầng đúng tag sẵn có sau khi registry từ chối pull MinIO; không phụ thuộc việc pull lại MinIO cho mỗi release crawler. Xem [biên bản deploy](crawler-release-20261009-telegram-01.md).

## Release ward `20261009-wards-01`

Dùng `--enable-ward-dispatch` để backup DB/SQLite, áp riêng migration 008, khởi tạo danh mục và thay timer mỗi phút. Tự động bắt đầu 00:00 giờ Việt Nam ngày sau triển khai; không chạy crawler/VPN thật để kiểm tra. Xem [runbook](crawler-ward-dispatch.md).

Nếu SUUMO trả 503 cho IP VPS, tải HTML danh mục mới ở local và truyền `--catalog-html <file>`. Installer chuyển file cùng SHA-256, kiểm chứng trước apply và giữ HTML/checksum trong backup để truy xuất nguồn. Không dùng tùy chọn này để refresh bằng HTML cũ; bot refresh vẫn tải SUUMO trực tiếp, lỗi sẽ giữ danh mục trước.
