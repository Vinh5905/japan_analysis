# Release Docker VPN — 2026-10-09

Đã chuyển `/opt/suumo-crawler` trên `thuevpsgiare` sang image/bundle
`20261009-vpn-docker-01`. Digest multi-platform:
`sha256:9cc8a26a5dddff376aeafb3decf282fe5df0c89316bf1fca045e524604c2dc84`.
Image hỗ trợ amd64/arm64 và chứa OpenVPN, iproute2, iptables cùng supervisor.
Private `.ovpn` không nằm trong image hoặc host bundle.

## Thay đổi runtime

- OpenVPN client chạy trong service `vpn`, bridge network riêng với host.
- Links, HTML, parse và managed rerun dùng namespace của VPN; worker cap_drop ALL,
  sidecar chỉ thêm NET_ADMIN/TUN, không host network/privileged/socket/ports.
- Firewall chỉ cho tunnel, đúng endpoint VPN và IP/port PostgreSQL/MinIO;
  public DNS qua tunnel, IPv6/direct fallback bị chặn.
- Preflight chọn/kiểm chứng VPN bằng Docker; runner không recreate VPN/infra sau
  snapshot. Cleanup dừng worker trước, stop/remove sidecar, xác nhận host VPN cũ tắt.
- Bot status và dispatcher đọc backend Docker. Service vẫn ExecStartPre/ExecStart/
  ExecStopPost; instance `openvpn-client@japan.service` disabled/masked.

## Kiểm chứng

166 unit/SQL QA tests đạt, gồm rotation/fallback, cleanup hook ordering, Docker
inspection lỗi, shared lock, migration rollback và giữ schedule/queue. Local lab
VPN server TLS thật đạt namespace/HTTP, PostgreSQL/MinIO read-write, mất tun0 và
def1 routes, xóa sidecar khi worker còn sống, firewall DROP và host routes giữ nguyên.
Image HTTP QA đạt accounting pages/retry/redirect/cache/error, claim/context và
managed rerun theo ward/run. Không gọi SUUMO trong các bài kiểm tra.

QA VPN thật trên VPS trước deploy dùng staging/runtime riêng, tạm pause bot/timer
và giữ shared lock; không tạo crawl_run hoặc thay VPN stats:

| Kiểm tra | Kết quả |
|---|---|
| Profile 110.163.135.206:1194 | Chưa khỏe trong cửa sổ trial |
| Profile 115.179.206.241:443 | AUTH_FAILED, không cấp quyền chạy worker |
| Profile 115.36.204.213:1464 | Ba checks khỏe liên tiếp |
| IP worker / host | 115.36.204.213 / 103.249.116.192 |
| Worker đọc PostgreSQL và 64 byte object MinIO | Đạt |
| SSH mới không multiplex khi VPN bật | Đạt |
| PostgreSQL protocol qua SSH tunnel | Đạt |
| MinIO API health và console qua SSH tunnel | HTTP 200 |
| Xóa sidecar, worker vẫn giữ namespace | Direct Internet bị chặn |
| Host routing fingerprint | Giữ nguyên |
| Tổng run/URL, VPN stats, queue và giờ chạy | Giữ nguyên |

Kết quả QA giữ tại `/opt/suumo-crawler/tmp/docker-vpn-qa-70f4da7f61/result.json`;
private env/config QA đã xóa sau cleanup. Kết quả checksum/status tại local
`tmp/releases/20261009-vpn-docker-01-verification.json`.
Thử SSH từ máy/IP hiện tại; không giả lập đổi Wi-Fi/IP máy quản trị.

## Deploy và trạng thái sau deploy

Installer chạy `--apply --container-vpn` khi rảnh, không bật VPN/crawl/migration.
Backup private: `/opt/suumo-crawler/.releases/20261009-vpn-docker-01-053b0519`,
gồm DB dump, consistent SQLite, managed files/.env và enabled state VPN host.
Trạng thái host cũ trong backup: enabled; trạng thái sau deploy: masked/inactive.
Raw `japan.conf` không thay đổi.

Installer từ chối release mới trên backend host nếu thiếu `--container-vpn`,
trước khi pause service/pull/thay file. Khi đã chuyển sang Docker, các lần cập nhật
thông thường chỉ cần `--apply`; chốt này đã qua test và cập nhật riêng host bundle,
image giữ nguyên digest.
Backup cho cập nhật host bundle này: `.releases/20261009-vpn-docker-01-cb3ca0aa`;
backup chuyển backend/DB/state vẫn là `053b0519` ở trên.

25 host checksums và 7 source checksums trong image đạt; image digest, 23 file
VPN/DB hash và quyền 700/600, Telegram menu 9 lệnh, status Docker và systemd-analyze
verify đều đạt. PostgreSQL `172.18.0.3`, MinIO `172.18.0.2` healthy; bot/timer active,
dispatcher Result=success, pipeline và VPN rảnh sau cleanup.

Giữ 39 lượt / 65.551 URL, 24 ward, 23 VPN, tất cả request/activation counters
ban đầu bằng 0. Chỉ đổi image tag và backend trong `.env`. Queue vẫn rỗng;
`automatic_start_at` và `next_auto_at` vẫn `1791565200.0`, tương ứng
**2026-10-10 00:00 Asia/Ho_Chi_Minh**. Chưa chạy production pipeline SUUMO;
kiểm chứng hệ thống thật ở phạm vi tunnel, SSH, đọc dữ liệu và cleanup.

Vận hành/rollback: [runbook Docker VPN](crawler-docker-vpn.md).

## Hotfix URL mặc định và lượt production đầu tiên — 21:25 +07

Xác nhận Telegram Miyakojima lúc 21:16 được lưu bền vững, nhưng dispatcher
ValueError trước tạo run do SUUMO_SEARCH_URL rỗng. Host ward_url nay dùng đúng
URL/filter mặc định trong settings của spider khi cấu hình blank/missing;
non-empty URL sai vẫn bị từ chối. Thêm hai regression tests, **168 tests đạt**.
Chỉ thay host bundle, image/digest không đổi. Backup trước sửa:
`.releases/20261009-vpn-docker-01-f77c9037` gồm pg_dump/SQLite/files/unit state.
Checksum area_catalog local/VPS:
`3ad0a16689ed748695f05251745548e124a3ab67724c211b94fb75274d2c7f9e`.

Dispatcher tiếp tục chính key xác nhận cũ, tạo run **40** manual Miyakojima,
queue tiêu thụ khi DB tạo run. VPN chọn `vpngate_153.172.5.86_tcp_1232.ovpn`
sau các profile chưa khỏe; worker và VPN healthy. Links spider bắt đầu 21:24:25,
SUUMO trả HTTP200, phát hiện 41 trang và ba trang đầu có 498 links mới.
Đây là snapshot lúc crawl đang chạy, chưa phải kết quả cuối pipeline/cleanup;
số liệu lịch sử và stats=0 ở phần deploy phía trên thuộc thời điểm trước run40.
