# VPN riêng cho crawler trong Docker

## Kiến trúc

OpenVPN client chạy trong service `vpn` trên Docker bridge `release_net`; links,
HTML, parse và `suumo-rerun-html` dùng `network_mode: service:vpn`. Các worker
không có capabilities; chỉ VPN có NET_ADMIN và `/dev/net/tun`, không dùng host
network, privileged, Docker socket hay published ports. PostgreSQL/MinIO giữ
network, volume và published ports hiện có; SSH/tunnel quản trị nằm trên host.

Pool/catalogue/counters giữ nguyên. Trước mỗi trial, controller chụp config và
IP PostgreSQL/MinIO hiện tại vào `state/vpn-runtime` (700; file 600). Chỉ config
được chọn mount read-only vào VPN; không đưa private configs vào image/bundle.
Tên nội bộ postgres/minio nằm trong hosts file riêng; DNS public dùng 1.1.1.1
và 8.8.8.8 qua tunnel, không dùng proxy DNS 127.0.0.11 của Docker cho public DNS.

## Firewall và lỗi tunnel

IPv4 OUTPUT mặc định DROP trước khi chạy OpenVPN. Chỉ cho loopback, tun0,
transport tới đúng IPv4/port của VPN, PostgreSQL IP:5432 và MinIO IP:9000.
Không có ngoại lệ ESTABLISHED tổng quát hoặc toàn bộ subnet private. IPv6 OUTPUT
và forwarding bị chặn; IPv6 trong namespace bị tắt. Worker không thể sửa rules.
Khi tunnel rớt/sidecar chết, worker còn sống vẫn giữ namespace với firewall DROP;
không tự quay về IP VPS. Không đổi VPN giữa một run.

## Preflight, systemd và cleanup

`SUUMO_VPN_BACKEND=docker` chuyển hook `ensure_openvpn.py` sang DockerVpn.
Pipeline service vẫn ExecStartPre → runner → ExecStopPost, kể cả lỗi preflight.
Preflight tạo run trước activation, chọn VPN xa nhất, xác nhận container cũ đã
stop/remove, freeze context, rồi tạo namespace mới. Mỗi trial tối đa 60s,
đạt ba checks liên tiếp: child OpenVPN còn sống, tun0 UP, hai def1 routes và
firewall đầy đủ. Chỉ lúc đó mới cho runner chạy worker với `--no-deps` để Compose
không tự khởi động lại/đổi namespace VPN. Runner không recreate infra sau snapshot.

Cleanup dừng/xác nhận tất cả worker (kể cả rerun) trước khi stop/remove sidecar;
ba quan sát xác nhận Docker VPN đã dừng. Cũng kiểm tra host VPN/tun0/routes đã
ngừng. Lỗi kiểm tra không được coi là cleanup thành công. Dispatcher/restart,
manual queue và giờ nghỉ cleanup + 1h giữ nguyên; status đọc Docker tunnel/firewall.
Container VPN restart=no và thuộc profile vpn/tasks, không tự bật khi boot.

## Chuyển VPS hiện có

```sh
make docker-build-push-release tag=<new-tag>
make release-deploy host=thuevpsgiare tag=<new-tag> opts="--apply --container-vpn"
```

Chỉ chạy khi crawler/cleanup/VPN rảnh. Installer pause bot/timer, kiểm tra image,
backup pg_dump/SQLite/.env/managed files và trạng thái enabled của host OpenVPN;
đổi backend, áp infra, disable/mask `openvpn-client@japan.service`, kiểm tra wiring
và địa chỉ nội bộ. Không bật VPN/crawl hoặc chạy migration/reset schedule trong
install. Lỗi restore managed files/backend và enabled/masked state cũ trước khi
resume bot/timer. Raw configs, counters, queue và lịch không reset.

Máy còn backend host phải truyền `--container-vpn`; thiếu cờ thì installer từ
chối trước mọi service/pull/thay file. Khi đã dùng backend Docker, cập nhật thường
với `--apply` giữ backend và host unit masked.

Không bật lại OpenVPN trên host khi dùng backend Docker. Để quay lại release cũ,
dừng worker/sidecar và timer/bot, khôi phục .env/managed files/units từ backup,
khôi phục enabled state theo `host-vpn-unit.json`, daemon-reload rồi resume các
service đã hoạt động. Không restore DB dump/SQLite lên dữ liệu mới khi chỉ rollback code.

## Kiểm tra local

```sh
docker build -f suumo_source_crawler/Dockerfile.release -t suumo-vpn-docker-qa:local .
python3 suumo_source_crawler/tests/integration_docker_vpn.py
SUUMO_WARD_DB_TESTS=1 SUUMO_TELEGRAM_DB_TESTS=1 SUUMO_VPN_DB_TESTS=1 \
  python3 -m unittest discover -s suumo_source_crawler/tests -q
```

Lab dùng project/volume/chứng chỉ QA riêng, VPN server TLS thật và HTTP fixture
trong tunnel; kiểm tra shared namespace, PostgreSQL/MinIO read-write, chặn đường
trực tiếp, tunnel down/def1 routes mất, sidecar removal với worker còn sống,
DROP counters và host routes giữ nguyên. Lab tự cleanup tài nguyên QA, không
gọi SUUMO hoặc ghi production. Kiểm tra VPS dùng IP-check endpoint và đọc DB/object;
không tạo crawl_run/HTML request, không thay production stats/queue/schedule.

Trên VPS có thể chạy `tests/verify_docker_vpn_vps.py` từ staging bundle đã
kiểm chứng, truyền `--stage <staging-root> --tag <image-tag>`. Script lấy lock,
tạm pause bot/timer và chỉ resume sau cleanup xác nhận; thử profile thật trong
runtime riêng, không ghi DB production. Khi in `VPN_ACTIVE`, chạy ở local:

```sh
python3 suumo_source_crawler/tests/verify_docker_vpn_ssh.py <qadir-trong-VPN_ACTIVE>
```

Probe mở SSH mới không multiplex, kiểm tra protocol PostgreSQL cùng MinIO
API/console qua tunnel và xác nhận host không có tun0; chỉ sau đó ghi acknowledgement.
QA không nhận được acknowledgement đúng hạn sẽ thất bại và vẫn cleanup.
Script `verify_docker_vpn_release.py --tag <tag> --digest <digest> --backup <basename>`
kiểm tra read-only release hiện tại; assertions số liệu/lịch là snapshot của lần
phát hành 09/10, cần cập nhật baseline nếu đã có crawl mới.

## Chẩn đoán

```sh
cd /opt/suumo-crawler
docker compose --env-file .env -f docker-compose.release.yml --profile tasks ps
journalctl -u suumo-crawler-pipeline.service -n 100 --no-pager
docker compose --env-file .env -f docker-compose.release.yml exec -T vpn \
  python /app/vpn/container_vpn.py --health
```

Khi VPN lỗi xem log service vpn; không in runtime config/context kèm credentials.
Thêm profile vẫn `make -C suumo_source_crawler vpn-sync`, giữ root portable
VPN_CONFIG_DIR. Xem [pool VPN](crawler-vpn-pool.md) cho chọn/counters và
[ward dispatcher](crawler-ward-dispatch.md) cho budget/ngày/queue.
