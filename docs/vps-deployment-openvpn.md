# VPS Deployment And OpenVPN Runbook

## Pool VPN hiện tại

Release `20261009-vpn-03` dùng 23 cấu hình dưới `/opt/suumo-crawler/vpn_config`
và PostgreSQL catalogue thay cho cấu hình cố định. `japan.conf` được sinh trước
mỗi activation khi tunnel cũ đã tắt, giữ route SSH. Thêm file bằng
`make -C suumo_source_crawler vpn-sync`; xem [runbook pool VPN](crawler-vpn-pool.md).
Các phần thiết lập OpenVPN ban đầu bên dưới giữ để tham khảo hạ tầng.

Tài liệu này mô tả quy trình từ lúc tạo SSH key để vào VPS, cài Docker, clone repo, chạy crawler release, rồi cấu hình OpenVPN theo cách B: VPN chạy trên host nhưng giữ SSH đi qua public gateway.

Các ví dụ dùng placeholder:

```text
VPS_USER=root
VPS_HOST=103.249.116.192
VPS_SSH_PORT=8686
LOCAL_SSH_IP=118.69.133.159
VPS_PUBLIC_GATEWAY=103.249.116.1
VPS_PUBLIC_INTERFACE=eth0
VPN_NAME=japan
```

Thay các giá trị này theo VPS thật. Riêng `LOCAL_SSH_IP` nên lấy từ `$SSH_CLIENT` trên VPS, vì đó là IP mà VPS đang thấy khi bạn SSH vào.

Các lệnh chạy trên VPS trong tài liệu này giả định bạn đang dùng user `root`, giống VPS hiện tại. Nếu dùng user thường như `ubuntu`, thêm `sudo` trước các lệnh quản trị như `apt`, `systemctl`, `cp` vào `/etc`, và `ip route`.

## 1. Tạo SSH key trên máy local

Chạy trên máy local:

```bash
ssh-keygen -t ed25519 -C "vps-suumo-crawler" -f ~/.ssh/suumo_vps
```

Lệnh này tạo một cặp key:

- `~/.ssh/suumo_vps`: private key, giữ bí mật trên máy local.
- `~/.ssh/suumo_vps.pub`: public key, có thể đưa lên VPS.

Set permission cho private key:

```bash
chmod 600 ~/.ssh/suumo_vps
```

Lệnh này đảm bảo chỉ user hiện tại đọc được private key. SSH thường từ chối key nếu permission quá mở.

## 2. Đưa public key lên VPS

Nếu VPS còn cho đăng nhập bằng password:

```bash
ssh-copy-id -i ~/.ssh/suumo_vps.pub -p VPS_SSH_PORT VPS_USER@VPS_HOST
```

Lệnh này thêm public key vào file `~/.ssh/authorized_keys` trên VPS. Sau đó bạn có thể SSH bằng private key thay vì password.

Nếu `ssh-copy-id` không có, copy thủ công:

```bash
cat ~/.ssh/suumo_vps.pub
```

Copy output public key, SSH vào VPS bằng password, rồi chạy trên VPS:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Các lệnh này tạo thư mục SSH, chỉnh permission đúng chuẩn, rồi mở file để dán public key.

## 3. SSH vào VPS

Chạy trên máy local:

```bash
ssh -i ~/.ssh/suumo_vps -p VPS_SSH_PORT VPS_USER@VPS_HOST
```

Ví dụ theo VPS hiện tại:

```bash
ssh -i ~/.ssh/suumo_vps -p 8686 root@103.249.116.192
```

`-i` chọn private key. `-p` chọn SSH port nếu VPS không dùng port mặc định `22`.

Tạo SSH config cho gọn:

```bash
nano ~/.ssh/config
```

Thêm:

```sshconfig
Host suumo-vps
    HostName 103.249.116.192
    User root
    Port 8686
    IdentityFile ~/.ssh/suumo_vps
```

Từ sau đó chỉ cần:

```bash
ssh suumo-vps
```

## 4. Chuẩn bị VPS cơ bản

Chạy trên VPS:

```bash
apt update
apt upgrade -y
```

`apt update` tải danh sách package mới nhất. `apt upgrade -y` cập nhật các package đã cài.

Cài tool nền:

```bash
apt install -y curl ca-certificates nano
```

- `curl`: kiểm tra IP public, tải script cài Docker.
- `ca-certificates`: giúp HTTPS certificate hoạt động đúng.
- `nano`: editor đơn giản để sửa `.env` và OpenVPN config.

## 5. Cài Docker Engine và Docker Compose plugin

Chạy trên VPS:

```bash
curl -fsSL https://get.docker.com | sh
```

Lệnh này tải script cài Docker chính thức và cài Docker Engine cùng Compose plugin.

Kiểm tra:

```bash
docker --version
docker compose version
```

Nếu đang dùng user không phải `root`, thêm user vào group `docker`:

```bash
usermod -aG docker $USER
```

Sau lệnh này cần thoát SSH rồi vào lại để group mới có hiệu lực:

```bash
exit
```

Nếu đang dùng `root`, thường không cần bước group này.

## 6. Chuẩn bị release folder trên VPS

Chạy trên VPS:

```bash
mkdir -p /opt/suumo-crawler
cd /opt/suumo-crawler
mkdir -p tmp
```

Folder `/opt/suumo-crawler` là nơi đặt file release runtime. Code crawler thật nằm trong Docker image `kevinpham9257/suumo-crawler:<tag>`. Host runtime được đồng bộ đủ file bằng `make release-deploy`, gồm runner, VPN preflight, shared lock, Telegram helper và systemd templates. Xem [quy trình deploy crawler](crawler-deployment.md).

Từ máy local, copy mẫu cấu hình lên VPS; chưa cần copy từng file Python:

```bash
scp -i ~/.ssh/suumo_vps -P VPS_SSH_PORT .env.release.example VPS_USER@VPS_HOST:/opt/suumo-crawler/
```

Nếu bạn đã có file `.env` riêng trên local, copy thẳng `.env` thay vì `.env.release.example`.

## 7. Tạo file `.env` cho release

Chạy trên VPS trong `/opt/suumo-crawler`:

```bash
cd /opt/suumo-crawler
cp .env.release.example .env
nano .env
```

`cp` tạo config runtime thật từ file mẫu. `nano` mở file để sửa password, tag image và hai biến Telegram:

```env
TELEGRAM_BOT_TOKEN=token_mới_từ_BotFather
TELEGRAM_CHAT_ID=chat_id_của_bạn
```

Không commit file `.env`. Nếu token từng được gửi qua chat hoặc commit vào Git, revoke token cũ và tạo token mới trước khi chạy production.

Sau khi đồng bộ runtime/pull image ở phần 9, test riêng kết nối Telegram, không cần khởi động PostgreSQL hoặc MinIO:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm --no-deps telegram-test
```

Lệnh trả exit code `0` khi Telegram nhận message; API lỗi, timeout hoặc thiếu biến sẽ trả exit code khác `0` nhưng không ảnh hưởng crawler đang chạy.

Sửa tối thiểu:

```env
SUUMO_CRAWLER_IMAGE=kevinpham9257/suumo-crawler
SUUMO_CRAWLER_TAG=20261009-01

POSTGRES_PASSWORD=change_this_postgres_password
MINIO_ROOT_PASSWORD=change_this_minio_password
CRAWLER_TMP_DIR=./tmp
```

Không commit `.env`. File này chứa secret runtime.

## 8. Publish image từ máy local

Chạy trên máy local, trong repo:

```bash
make docker-login
```

Lệnh này login Docker Hub để có quyền push image.

Build và push multi-platform:

```bash
make docker-build-push-release tag=20261009-01
```

Lệnh này dùng Docker Buildx để build image cho cả:

```text
linux/amd64
linux/arm64
```

VPS thường là `linux/amd64`, còn Mac Apple Silicon là `linux/arm64`. Nếu chỉ build/push theo platform của Mac, VPS có thể lỗi `no matching manifest for linux/amd64`.

Kiểm tra manifest trên Docker Hub:

```bash
make docker-inspect-release tag=20261009-01
```

Output cần có cả:

```text
Platform: linux/amd64
Platform: linux/arm64
```

## 9. Pull image và start release runtime trên VPS

Sau khi đã tạo `.env` trên VPS và publish image, chạy từ root repo local để đồng bộ đủ host files và pull image. Lệnh mặc định chỉ xem kế hoạch; `--apply` mới triển khai. Alias `suumo-vps` phải cấu hình user quản trị trong SSH config ở phần 3.

```bash
make release-deploy host=suumo-vps tag=20261009-01
make release-deploy host=suumo-vps tag=20261009-01 opts="--apply"
```

Installer tạo service và timer nhưng không tự enable timer hoặc chạy bootstrap/crawler. Tiếp tục bootstrap ở phần dưới sau khi infra đã lên. VPS cần Python >= 3.10; nếu thiếu, cài `python3` trước khi deploy. Các lệnh Docker thủ công dưới đây vẫn dùng được để kiểm tra và vận hành.

Chạy trên VPS trong `/opt/suumo-crawler`:

```bash
docker login
```

Lệnh này chỉ cần khi Docker Hub image là private hoặc Docker Hub yêu cầu authenticated pull. Nếu image public, có thể bỏ qua.

```bash
docker compose --env-file .env -f docker-compose.release.yml --profile tasks --profile tools pull
```

Lệnh này pull các image cần thiết: crawler image, PostgreSQL, MinIO.

Start PostgreSQL, MinIO và bootstrap:

```bash
docker compose --env-file .env -f docker-compose.release.yml up -d postgres minio
docker compose --env-file .env -f docker-compose.release.yml run --rm crawler-init
```

Hai lệnh này làm các việc:

- Start `postgres` container.
- Start `minio` container.
- Chạy `crawler-init` một lần.

`crawler-init` làm các việc:

- Đợi PostgreSQL sẵn sàng.
- Tạo schema crawler nếu DB chưa có bảng crawler.
- Chạy `main.py` để tạo MinIO bucket và prefixes như `suumo/data/`, `suumo/page_source/`, `suumo/image/`.

Kiểm tra container:

```bash
docker compose --env-file .env -f docker-compose.release.yml ps
```

Xem log:

```bash
docker compose --env-file .env -f docker-compose.release.yml logs -f
```

## 10. Chạy crawler trên VPS

Chạy theo thứ tự:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-links
```

Spider `suumo_links` lấy danh sách link mới và ghi vào `tmp/suumo_links.txt`.

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-html
```

Spider `suumo_html` đọc link mới, crawl HTML, gzip payload, upload lên MinIO `suumo/page_source`, và ghi metadata vào PostgreSQL.

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-page
```

Spider `suumo_page` đọc các task `pending`, tải raw HTML từ MinIO, parse dữ liệu, gzip JSON batch, upload lên MinIO `suumo/data`, rồi update `crawl_tasks.batch_id`.

## 11. Kết nối PostgreSQL và MinIO từ máy local

Cách khuyến nghị là dùng SSH tunnel. Máy local chỉ kết nối tới `localhost`, còn SSH sẽ chuyển traffic vào service đang chạy trên VPS. Cách này không cần mở trực tiếp PostgreSQL hoặc MinIO ra internet.

Trước hết kiểm tra service trên VPS:

```bash
cd /opt/suumo-crawler
docker compose --env-file .env -f docker-compose.release.yml ps
```

Kỳ vọng `postgres` và `minio` đang `Up` hoặc `healthy`.

Xem thông tin PostgreSQL trong `.env` trên VPS:

```bash
cd /opt/suumo-crawler
grep -E '^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_PORT)=' .env
```

Mở tunnel PostgreSQL từ máy local:

```bash
ssh -N -L 15432:127.0.0.1:5432 thuevpsgiare
```

Nếu không dùng SSH alias `thuevpsgiare`, dùng dạng đầy đủ:

```bash
ssh -i ~/.ssh/suumo_vps -p VPS_SSH_PORT -N -L 15432:127.0.0.1:5432 VPS_USER@VPS_HOST
```

Ý nghĩa `-L 15432:127.0.0.1:5432`:

```text
máy local localhost:15432
-> SSH tunnel
-> VPS 127.0.0.1:5432
-> PostgreSQL container
```

- `15432`: port trên máy local. Dùng `15432` để tránh đụng PostgreSQL local nếu máy bạn đang có service ở `5432`.
- `127.0.0.1`: địa chỉ nhìn từ phía VPS.
- `5432`: port PostgreSQL đang publish trên VPS. Nếu `.env` trên VPS đổi `POSTGRES_PORT`, thay số này theo giá trị đó.
- `-N`: không mở shell, chỉ giữ tunnel. Nếu bỏ `-N`, SSH sẽ vào shell bình thường nhưng tunnel vẫn chạy.

Khi tunnel PostgreSQL đang mở, cấu hình DBeaver như sau:

```text
Host: localhost
Port: 15432
Database: giá trị POSTGRES_DB trong /opt/suumo-crawler/.env
Username: giá trị POSTGRES_USER trong /opt/suumo-crawler/.env
Password: giá trị POSTGRES_PASSWORD trong /opt/suumo-crawler/.env
SSL: disable/default
```

Với `.env.release.example` mặc định thì là:

```text
Host: localhost
Port: 15432
Database: suumo_crawler
Username: suumo_user
Password: suumo_password_change_me
```

Xem thông tin MinIO trong `.env` trên VPS:

```bash
cd /opt/suumo-crawler
grep -E '^(MINIO_ROOT_USER|MINIO_ROOT_PASSWORD)=' .env
```

Mở tunnel MinIO Console từ máy local:

```bash
ssh -N -L 19001:127.0.0.1:9001 thuevpsgiare
```

Sau đó mở trình duyệt trên máy local:

```text
http://localhost:19001
```

Đăng nhập bằng:

```text
Username: giá trị MINIO_ROOT_USER trong /opt/suumo-crawler/.env
Password: giá trị MINIO_ROOT_PASSWORD trong /opt/suumo-crawler/.env
```

Nếu cần dùng cả MinIO API từ máy local, ví dụ tool S3 client, mở thêm port `9000`:

```bash
ssh -N -L 19001:127.0.0.1:9001 -L 19000:127.0.0.1:9000 thuevpsgiare
```

Khi đó cấu hình S3 client local:

```text
Endpoint: http://localhost:19000
Access key: MINIO_ROOT_USER
Secret key: MINIO_ROOT_PASSWORD
Bucket: suumo
Path style access: enabled
SSL: disabled
```

Giữ terminal chạy lệnh SSH tunnel trong lúc dùng DBeaver hoặc MinIO UI. Khi muốn đóng kết nối, nhấn `Ctrl + C` trong terminal đó.

## 12. Cấu hình tài nguyên và theo dõi VPS

VPS nhỏ `1 CPU / 2GB RAM` nên được cấu hình theo hướng giữ host ổn định trước. Crawler có thể fail và chạy lại, nhưng không nên để crawler kéo chết SSH, PostgreSQL, MinIO, hoặc OpenVPN.

### Thêm swap 4GB

Kiểm tra RAM/swap hiện tại:

```bash
free -h
swapon --show
```

- `free -h`: xem RAM và swap của toàn VPS bằng đơn vị dễ đọc.
- `swapon --show`: liệt kê các swap device/file đang bật. Nếu không có output nghĩa là chưa có swap.

Nếu `Swap` đang là `0B`, tạo swap file 4GB:

```bash
fallocate -l 4G /swapfile
```

Lệnh này tạo file `/swapfile` dung lượng 4GB. Nếu VPS không hỗ trợ `fallocate`, dùng cách chậm hơn:

```bash
dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
```

Set permission:

```bash
chmod 600 /swapfile
```

File swap có thể chứa dữ liệu memory, nên chỉ `root` được đọc/ghi.

Format file thành swap:

```bash
mkswap /swapfile
```

Bật swap ngay:

```bash
swapon /swapfile
```

Cho swap tự bật lại sau reboot:

```bash
echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
```

Kiểm tra lại:

```bash
free -h
swapon --show
```

Kỳ vọng `Swap` có khoảng `4.0Gi`.

Giảm xu hướng dùng swap quá sớm:

```bash
echo 'vm.swappiness=10' | tee /etc/sysctl.d/99-swappiness.conf
sysctl --system
```

`vm.swappiness` là mức Linux sẵn sàng đẩy memory từ RAM sang swap. Thang giá trị là `0` tới `100`; số càng cao càng dễ swap sớm. Với VPS này dùng `10` để swap đóng vai trò bảo hiểm khi RAM căng, không phải memory chính.

### Resource limit trong Docker Compose

Release compose đang có các limit mặc định:

```env
POSTGRES_MEM_LIMIT=384m
POSTGRES_CPUS=0.30
POSTGRES_PIDS_LIMIT=256

MINIO_MEM_LIMIT=512m
MINIO_CPUS=0.30
MINIO_PIDS_LIMIT=256

CRAWLER_MEM_LIMIT=512m
CRAWLER_CPUS=0.50
CRAWLER_PIDS_LIMIT=256
```

Ý nghĩa:

- `mem_limit`: RAM tối đa container được dùng. Nếu container vượt quá nhiều, container đó sẽ bị kill trước thay vì kéo cả VPS xuống.
- `cpus`: phần CPU tối đa container được dùng. VPS 1 CPU nên giới hạn để một container không ăn toàn bộ CPU.
- `pids_limit`: giới hạn số process/thread trong container, tránh lỗi sinh process quá nhiều.

Các giá trị này nằm trong `.env`, nên có thể chỉnh trên VPS bằng:

```bash
cd /opt/suumo-crawler
nano .env
```

Starting point cho VPS `1 CPU / 2GB RAM`:

```text
PostgreSQL: 384m RAM, 0.30 CPU
MinIO:      512m RAM, 0.30 CPU
Crawler:    512m RAM, 0.50 CPU
```

Nếu crawler bị exit `137` hoặc kernel log có OOM kill process `python`, tăng:

```env
CRAWLER_MEM_LIMIT=768m
```

Nếu MinIO lỗi upload hoặc bị restart, tăng:

```env
MINIO_MEM_LIMIT=768m
```

Nếu PostgreSQL healthcheck fail hoặc connection timeout nhưng host vẫn ổn, tăng:

```env
POSTGRES_MEM_LIMIT=512m
```

Sau khi đổi resource limit trong `.env` hoặc đổi `docker-compose.release.yml`, recreate service nền:

```bash
cd /opt/suumo-crawler
docker compose --env-file .env -f docker-compose.release.yml up -d --force-recreate postgres minio
```

Lệnh này recreate container `postgres` và `minio` để nhận config mới, nhưng không xóa volume nên data vẫn còn.

Crawler one-shot như `suumo-links`, `suumo-html`, `suumo-page` sẽ nhận limit mới ở lần chạy tiếp theo:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-html
```

`--rm` chỉ áp dụng cho container one-shot: chạy xong thì xóa container job. Không dùng `--rm` với `up -d postgres minio`.

### Theo dõi tài nguyên

Xem tài nguyên từng Docker container:

```bash
docker stats --no-stream
```

- `CPU %`: container đang dùng bao nhiêu CPU.
- `MEM USAGE / LIMIT`: RAM đang dùng so với limit.
- `MEM %`: phần trăm RAM container đang dùng trên limit.
- `NET I/O`: network in/out.
- `BLOCK I/O`: disk read/write.

`--no-stream` in một lần rồi thoát. Bỏ `--no-stream` nếu muốn xem realtime.

Xem RAM/swap toàn VPS:

```bash
free -h
```

Quan trọng nhất:

- `available`: RAM còn có thể cấp cho app.
- `Swap used`: swap đang được dùng bao nhiêu.

Nếu `available` thấp và `Swap used` tăng liên tục, VPS đang áp lực RAM. Nếu swap tăng vài GB và máy chậm, workload đã vượt cấu hình VPS.

Kiểm tra kernel có từng OOM kill process không:

```bash
dmesg -T | grep -i -E 'oom|killed process|out of memory'
```

Nếu có dòng như `Out of memory` hoặc `Killed process ... (python)`, kernel đã giết process vì thiếu RAM. Nếu kill `python` thì crawler bị giết; nếu kill `minio` hoặc `postgres`, có thể gây lỗi upload hoặc DB timeout.

Xem trạng thái container:

```bash
cd /opt/suumo-crawler
docker compose --env-file .env -f docker-compose.release.yml ps
```

Xem log pipeline:

```bash
journalctl -u suumo-crawler-pipeline.service -n 200 --no-pager
```

Xem log MinIO khi có lỗi upload:

```bash
docker logs suumo_crawler_release-minio-1 --tail 200
```

## 13. Cài OpenVPN client trên host

Cách B nghĩa là OpenVPN chạy trực tiếp trên VPS host. Cách này làm outbound traffic của VPS đi qua VPN Nhật, nhưng phải giữ route SSH riêng để không mất kết nối.

Chạy trên VPS:

```bash
apt install -y openvpn curl iproute2
```

- `openvpn`: client VPN.
- `curl`: kiểm tra public IP sau khi bật VPN.
- `iproute2`: có lệnh `ip route` để xem/thêm route.

Tạo thư mục config:

```bash
mkdir -p /etc/openvpn/client
```

Copy file `.ovpn` server Nhật vào VPS. Từ máy local:

```bash
scp -i ~/.ssh/suumo_vps -P VPS_SSH_PORT japan.ovpn VPS_USER@VPS_HOST:/tmp/japan.ovpn
```

Đưa vào đúng path service OpenVPN client:

```bash
cp /tmp/japan.ovpn /etc/openvpn/client/japan.conf
```

Service name sẽ là `openvpn-client@japan` vì file config tên `japan.conf`.

Nếu VPN cần username/password, tạo auth file:

```bash
printf "vpn\nvpn\n" > /etc/openvpn/client/auth.txt
chmod 600 /etc/openvpn/client/auth.txt
```

Mở config:

```bash
nano /etc/openvpn/client/japan.conf
```

Tìm dòng:

```text
auth-user-pass
```

Sửa thành:

```text
auth-user-pass /etc/openvpn/client/auth.txt
```

OpenVPN sẽ đọc username/password từ file này thay vì hỏi interactive.

## 14. Chuẩn bị route giữ SSH trước khi bật VPN

Lấy IP client SSH hiện tại trên VPS:

```bash
echo $SSH_CLIENT
```

Output dạng:

```text
118.69.133.159 64257 8686
```

Ý nghĩa:

- `118.69.133.159`: IP máy local đang SSH vào VPS.
- `64257`: source port từ máy local.
- `8686`: SSH port trên VPS.

Lấy default gateway public của VPS:

```bash
ip route show default
```

Output ví dụ:

```text
default via 103.249.116.1 dev eth0
```

Ý nghĩa:

- `103.249.116.1`: public gateway của VPS.
- `eth0`: network interface public của VPS.

Thêm route riêng cho IP máy local:

```bash
ip route replace 118.69.133.159/32 via 103.249.116.1 dev eth0
```

Lệnh này nói với VPS: mọi packet trả về `118.69.133.159` phải đi qua gateway public `103.249.116.1` trên `eth0`, kể cả khi OpenVPN đổi default route sang `tun0`.

Kiểm tra route riêng:

```bash
ip route show 118.69.133.159/32
```

Kỳ vọng:

```text
118.69.133.159 via 103.249.116.1 dev eth0
```

Kiểm tra route thực tế:

```bash
ip route get 118.69.133.159
```

Kỳ vọng:

```text
118.69.133.159 via 103.249.116.1 dev eth0 src 103.249.116.192
```

## 15. Persist route SSH trong OpenVPN config

Mở config:

```bash
nano /etc/openvpn/client/japan.conf
```

Thêm dòng này:

```text
route 118.69.133.159 255.255.255.255 net_gateway
```

`net_gateway` nghĩa là gateway gốc trước khi VPN thay route. Dòng này giúp OpenVPN tự tạo route giữ SSH mỗi lần service start.

Nếu IP mạng nhà bạn đổi, phải cập nhật lại dòng này theo IP mới.

## 16. Bật VPN với safety rollback

Không dùng `enable --now` ngay lần đầu. Trước tiên tạo rollback tự tắt OpenVPN sau 2 phút:

```bash
systemd-run --unit=openvpn-ssh-rollback --on-active=2min /bin/systemctl stop openvpn-client@japan
```

Lệnh này tạo một timer tạm thời. Nếu bạn bị mất SSH, sau 2 phút service OpenVPN sẽ tự bị stop và bạn có thể SSH lại.

Bật VPN:

```bash
systemctl start openvpn-client@japan
```

Kiểm tra status:

```bash
systemctl status openvpn-client@japan
```

Nếu SSH vẫn ổn, kiểm tra public IP:

```bash
curl -4 ifconfig.me
```

Nếu output là IP Nhật/VPN, ví dụ:

```text
219.100.37.239
```

thì outbound traffic của VPS đang đi qua VPN.

Kiểm tra route SSH vẫn đi public gateway:

```bash
ip route get 118.69.133.159
```

Nó vẫn nên đi qua `103.249.116.1 dev eth0`, không phải `tun0`.

Nếu mọi thứ ổn, hủy rollback:

```bash
systemctl stop openvpn-ssh-rollback.timer openvpn-ssh-rollback.service 2>/dev/null || true
```

Với pipeline hiện tại, không cần enable OpenVPN tự chạy riêng khi VPS reboot: unit crawler sẽ yêu cầu bật VPN ở đầu mỗi lượt và xác nhận đóng VPN ở cuối lượt. Chỉ enable timer crawler sau khi kiểm tra hoàn tất. Thay đổi này không tự disable OpenVPN nếu trước đó đã enable; cấu hình autostart hiện có vẫn cần kiểm tra lúc triển khai thực tế.

Không dùng `enable --now` trong lần đầu, vì `--now` vừa enable vừa start ngay, dễ tự khóa SSH nếu route chưa đúng.

## Trạng thái VPS hiện tại (2026-09-23)

VPS đã thay cấu hình OpenVPN bằng file local `vpn_config/vpngate_219.100.37.115_tcp_443.ovpn`. File đang được dùng tại:

```text
/etc/openvpn/client/japan.conf
```

Config mới kết nối tới `219.100.37.115:443`, dùng certificate/key nhúng trong `.ovpn` và không dùng username/password qua `auth-user-pass`. File trên VPS đã được đặt quyền `600`; không ghi certificate hoặc private key vào Git/docs.

Route SSH đã được chuẩn bị trước khi bật VPN:

```text
SSH client hiện tại: 113.161.73.167
VPS gateway: 103.249.116.1
Public interface: eth0
Persistent route: route 113.161.73.167 255.255.255.255 net_gateway
```

Route runtime đã được kiểm tra bằng `ip route get 113.161.73.167` và đi qua `103.249.116.1 dev eth0`. Preflight mới đã được deploy; lần test ngày 2026-09-23 tự bật VPN thành công ở lần `1/3`, xác nhận `tun0` và hai route redirect-gateway, đồng thời SSH vẫn giữ qua `eth0`. IP SSH là IP động, nên lần sau phải lấy IP đầu tiên từ `$SSH_CLIENT` và cập nhật route nếu khác giá trị trên.

## 17. Chạy crawler khi VPN host đang bật

Khi host đã đi qua VPN, Docker container mặc định cũng đi outbound qua NAT của host, nên crawler thường sẽ đi qua VPN.

Kiểm tra public IP bên trong crawler image:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-tools sh -lc 'curl -4 ifconfig.me'
```

Nếu output là IP Nhật/VPN, crawler outbound đang đi qua VPN.

Ưu tiên chạy đủ lượt bằng `systemctl start suumo-crawler-pipeline.service` hoặc host runner ở phần 18 để tự preflight và đóng/xác nhận VPN cuối lượt. Các lệnh Compose đơn lẻ bên dưới không tự đóng VPN; nếu dùng để vận hành thủ công, chạy host cleanup sau khi các lệnh đã kết thúc.

Chạy crawler:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-links
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-html
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-page
python3 suumo_source_crawler/scripts/stop_openvpn.py --compose-file docker-compose.release.yml --env-file .env
```

## 18. Tự động chạy pipeline bằng systemd timer

Nên dùng `systemd timer` thay vì cron vì dễ xem trạng thái, log, lần chạy kế tiếp, và có `Persistent=true` để chạy bù nếu VPS bị tắt đúng lịch.

Trước hết test pipeline runner thủ công trong `/opt/suumo-crawler`:

```bash
cd /opt/suumo-crawler
python3 suumo_source_crawler/scripts/run_release_pipeline.py \
  --compose-file /opt/suumo-crawler/docker-compose.release.yml \
  --env-file /opt/suumo-crawler/.env
```

Runner chạy đủ thứ tự:

```text
VPN preflight -> bootstrap -> suumo_links -> suumo_html -> suumo_page -> VPN shutdown + verification
```

Nếu một bước lỗi, runner dừng các bước tiếp theo, giữ exit code lỗi và gửi Telegram. Cleanup vẫn chạy để dừng task còn sót, đóng VPN và xác nhận đã đóng; không xác nhận được thì lượt chạy cũng failed. Runner dùng `--pull never` để lịch chạy chỉ dùng image đã pull sẵn và không phụ thuộc Docker Hub. Runner thủ công tự quản lý VPN; systemd truyền `--vpn-managed-by-systemd` vì dùng preflight/cleanup hooks riêng.

Tạo service:

```bash
nano /etc/systemd/system/suumo-crawler-pipeline.service
```

Dán nội dung:

```systemd
[Unit]
Description=Run SUUMO crawler release pipeline
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/suumo-crawler
Environment=PYTHONUNBUFFERED=1
TimeoutStartSec=infinity
TimeoutStopSec=10min
ExecStartPre=/usr/bin/python3 /opt/suumo-crawler/suumo_source_crawler/scripts/ensure_openvpn.py --env-file /opt/suumo-crawler/.env --service openvpn-client@japan --interface tun0 --restart-attempts 3 --checks-per-attempt 120 --required-consecutive-checks 3 --check-interval-seconds 2
ExecStart=/usr/bin/python3 /opt/suumo-crawler/suumo_source_crawler/scripts/run_release_pipeline.py --compose-file /opt/suumo-crawler/docker-compose.release.yml --env-file /opt/suumo-crawler/.env --vpn-managed-by-systemd
ExecStopPost=/usr/bin/python3 /opt/suumo-crawler/suumo_source_crawler/scripts/stop_openvpn.py --compose-file /opt/suumo-crawler/docker-compose.release.yml --env-file /opt/suumo-crawler/.env --service openvpn-client@japan --interface tun0
```

Giải thích:

- `Type=oneshot`: job chạy xong thì kết thúc, phù hợp crawler batch.
- `WorkingDirectory=/opt/suumo-crawler`: nơi có `.env`, `docker-compose.release.yml`, source của runner và thư mục `tmp`.
- `ExecStart=...run_release_pipeline.py`: gửi pipeline start, đảm bảo PostgreSQL/MinIO và schema sẵn sàng, sau đó chạy `suumo-links`, `suumo-html`, `suumo-page` tuần tự.
- `ExecStartPre=...ensure_openvpn.py`: gửi Telegram bắt đầu kiểm tra VPN, thông báo VPN đã bật/chưa bật, tự bật lại tối đa 3 lần và chỉ trả thành công khi tunnel khỏe. Nếu service đang `active`/`activating`, script cho OpenVPN tối đa 4 phút để tự reconnect trước khi ép restart. Mỗi lần có tối đa 120 lượt kiểm tra, cách nhau 2 giây; phải đạt 3 lượt khỏe liên tiếp mới cho crawler chạy.
- `TimeoutStartSec=infinity`: crawler có thể chạy nhiều giờ; giới hạn 20 phút trước đây khiến systemd gửi SIGTERM lúc job HTML đang chạy. Preflight VPN vẫn giới hạn bởi số lượt kiểm tra và tối đa 3 lần restart.
- `ExecStopPost=...stop_openvpn.py`: cleanup cuối lượt, chạy cả khi preflight/crawler thất bại hoặc service bị stop. Dừng/xác nhận container pipeline còn sót trước khi tắt VPN, rồi yêu cầu stop OpenVPN tối đa 3 lần. Mỗi lần có tối đa 30 kiểm tra cách nhau 2 giây, cần 3 kiểm tra liên tiếp xác nhận service không còn process, tun0 absent/DOWN và không còn route IPv4/IPv6 qua tunnel. Không kiểm tra được thì báo cleanup failed; không giả định lệnh stop thành công nghĩa là VPN đã tắt.
- `TimeoutStopSec=10min`: systemd chờ cleanup có giới hạn. Cleanup timeout/lỗi làm lượt chạy failed. Chỉ có thông báo Telegram VPN đã tắt sau khi xác nhận đủ điều kiện.
- Một lượt chỉ được coi là khỏe khi `openvpn-client@japan` là `active`, interface `tun0` đang `UP`, và cả route `0.0.0.0/1` lẫn `128.0.0.0/1` đều đi qua `tun0`.
- Nếu VPN vẫn không khỏe sau số lần retry, `ExecStartPre` trả exit code khác 0; systemd đánh dấu pipeline failed và không chạy crawler bằng IP public của VPS.
- `--env-file /opt/suumo-crawler/.env` cho phép preflight dùng cùng `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` với pipeline. Telegram lỗi hoặc thiếu biến không làm preflight crash; nhưng VPN không khỏe luôn chặn crawler.
- Mỗi spider gửi start/summary riêng. Pipeline gửi summary tổng hoặc failure của bước đầu tiên bị lỗi.
- `Requires=docker.service`: nếu Docker không chạy thì service không nên chạy.
- Preflight tự start/restart OpenVPN và xác nhận tunnel khỏe; unit không còn đặt `Wants/After` tới VPN. Vòng đời bật/tắt được quản lý bởi các script, tránh ràng buộc thứ tự dừng giữa pipeline đang cleanup và service VPN cần được stop.

Không đặt `docker compose pull` trong scheduled service. Nếu OpenVPN đang bật, VPS có thể không kết nối được Docker Hub registry và làm job fail trước khi crawl. Image nên được pull thủ công lúc deploy/update; runner dùng `--pull never` để job định kỳ chỉ chạy image local.

Preflight không tự hủy `openvpn-ssh-rollback.timer`. Rollback bảo vệ SSH là cơ chế dành cho lần test thủ công và chỉ được hủy sau khi người vận hành xác nhận route tới IP SSH hiện tại vẫn đi qua public gateway. Systemd không biết IP Wi-Fi tương lai của người vận hành, nên tự hủy rollback chỉ dựa trên trạng thái `tun0` là không an toàn.

`make release-deploy ... opts="--apply"` tự cài lại unit và reload systemd. Nếu đồng bộ thủ công, phải copy đủ cả runner, preflight, `scripts/stop_openvpn.py`, `scripts/runtime_lock.py`, `scripts/telegram_state.py`, package `__init__.py` và Telegram helper. Sau đó cài unit đã version-control:

```bash
install -m 0644 \
  /opt/suumo-crawler/suumo_source_crawler/deploy/systemd/suumo-crawler-pipeline.service \
  /etc/systemd/system/suumo-crawler-pipeline.service
systemctl daemon-reload
```

Có thể test riêng preflight mà chưa chạy crawler:

```bash
python3 /opt/suumo-crawler/suumo_source_crawler/scripts/ensure_openvpn.py \
  --service openvpn-client@japan \
  --interface tun0 \
  --restart-attempts 3 \
  --checks-per-attempt 120 \
  --required-consecutive-checks 3 \
  --check-interval-seconds 2
```

Chỉ test lệnh này từ SSH sau khi đã thêm route cho IP hiện tại và đặt safety rollback như phần 16. Cơ chế preflight đảm bảo crawler không chạy thiếu VPN, nhưng không thể tự giải quyết việc IP Wi-Fi của máy quản trị thay đổi.

Tạo timer:

```bash
nano /etc/systemd/system/suumo-crawler-pipeline.timer
```

Trước khi chọn giờ chạy, kiểm tra timezone của VPS:

```bash
timedatectl
```

`OnCalendar` dùng timezone hiện tại của VPS. Nếu muốn `19:00` là giờ Việt Nam:

```bash
timedatectl set-timezone Asia/Ho_Chi_Minh
```

Nếu muốn `19:00` là giờ Nhật:

```bash
timedatectl set-timezone Asia/Tokyo
```

Nếu muốn chạy mỗi ngày lúc 00:00, dùng:

```systemd
[Unit]
Description=Run SUUMO crawler pipeline every day at 00:00

[Timer]
OnCalendar=*-*-* 00:00:00
Persistent=true
Unit=suumo-crawler-pipeline.service

[Install]
WantedBy=timers.target
```

Nếu muốn chạy mỗi ngày lúc 19:00, đổi thành:

```systemd
OnCalendar=*-*-* 19:00:00
```

Nếu muốn chạy mỗi 2 ngày lúc 19:00, đổi thành:

```systemd
OnCalendar=*-*-01/2 19:00:00
```

Giải thích:

- `OnCalendar=*-*-* 00:00:00`: chạy mỗi ngày lúc 00:00.
- `OnCalendar=*-*-* 19:00:00`: chạy mỗi ngày lúc 19:00.
- `OnCalendar=*-*-01/2 19:00:00`: chạy lúc 19:00 các ngày 1, 3, 5, 7... trong tháng.
- `Persistent=true`: nếu VPS tắt đúng lúc tới lịch, lần boot tiếp theo systemd sẽ chạy bù.
- `Unit=suumo-crawler-pipeline.service`: timer này kích hoạt service pipeline.

Không dùng `OnBootSec` cho case này. Nếu VPS đã boot từ lâu rồi mới tạo timer, mốc boot có thể đã qua và timer có thể chạy ngay hoặc rất sớm. `OnCalendar` phù hợp hơn vì nó bám vào giờ cố định trong ngày.

Preview lịch chạy tiếp theo:

```bash
systemd-analyze calendar '*-*-* 00:00:00'
```

Reload systemd:

```bash
systemctl daemon-reload
```

Lệnh này bắt systemd đọc lại file service/timer mới tạo.

Bật timer:

```bash
systemctl enable --now suumo-crawler-pipeline.timer
```

`enable` giúp timer tự chạy sau reboot. `--now` start timer ngay, không chạy pipeline ngay lập tức trừ khi timer tới hạn.

Kiểm tra lịch chạy:

```bash
systemctl list-timers suumo-crawler-pipeline.timer
```

Chạy thử service ngay lập tức:

```bash
systemctl start suumo-crawler-pipeline.service
```

Xem log lần chạy:

```bash
journalctl -u suumo-crawler-pipeline.service -f
```

Xem log các lần gần nhất:

```bash
journalctl -u suumo-crawler-pipeline.service -n 200 --no-pager
```

Kiểm tra trạng thái service:

```bash
systemctl status suumo-crawler-pipeline.service
```

Tắt lịch chạy tự động:

```bash
systemctl disable --now suumo-crawler-pipeline.timer
```

Lệnh này tắt timer, nhưng không xóa file service/timer.

## 19. Lệnh cứu khi VPN làm mất SSH

Nếu mất SSH, vào web console/VNC/serial console của nhà cung cấp VPS, rồi chạy:

```bash
systemctl stop openvpn-client@japan
systemctl disable openvpn-client@japan
systemctl reset-failed openvpn-client@japan
```

Các lệnh này dừng VPN, tắt auto-start, và xóa trạng thái failed nếu có.

Nếu muốn chắc chắn service không tự bật lại:

```bash
mv /etc/openvpn/client/japan.conf /etc/openvpn/client/japan.conf.disabled
```

Sau đó kiểm tra route và IP:

```bash
ip route
curl -4 ifconfig.me
```

Rồi SSH lại từ máy local.

## 20. Cập nhật code/image sau này

Quy trình chính nằm ở [Deploy crawler SUUMO](crawler-deployment.md). Trên máy local, chọn tag mới và build image/host bundle từ cùng phiên bản source:

```bash
make docker-build-push-release tag=20261009-02
make release-deploy host=suumo-vps tag=20261009-02
make release-deploy host=suumo-vps tag=20261009-02 opts="--apply"
```

Lệnh mặc định chỉ in kế hoạch tại local. Với `--apply`, lệnh đồng bộ đầy đủ host runtime, pull image, cập nhật tag trong `.env`, cài service, reload systemd và áp dụng PostgreSQL/MinIO config. `.env` còn lại, tmp, VPN config và named volumes được giữ. Nếu crawler đang chạy, lệnh từ chối deploy; lịch timer hiện có không bị thay trừ khi truyền `--update-timer`.

Installer không chạy crawler, bootstrap hoặc migrations. Runner định kỳ vẫn dùng `--pull never`; container one-shot ở lần chạy sau dùng tag đã pull.

Nếu chỉ sửa host script, Compose hoặc service, có thể deploy lại với tag image hiện có. Sửa crawler/Telegram helper/dependencies/SQL thì build tag mới. Nếu sửa lịch trong file timer của repo:

```bash
make release-deploy host=suumo-vps tag=20261009-02 opts="--apply --update-timer"
```

Nếu VPN làm Docker Hub không truy cập được, installer giữ release cũ và khôi phục trạng thái timer. Installer không tự đổi VPN/route SSH. Chỉ khi crawler đã dừng và route SSH được kiểm tra theo phần 14–16, người vận hành có thể tạm tắt VPN để pull qua network public, rồi bật lại và xác nhận VPN khỏe trước khi cho lịch chạy tiếp:

```bash
systemctl stop openvpn-client@japan
# Chạy lại release-deploy --apply từ local khi network đã sẵn sàng.
systemctl start openvpn-client@japan
```

Setup VPS lần đầu hoặc khi DB/MinIO mới cần bootstrap:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm crawler-init
```

Đối với schema đã tồn tại, cập nhật bằng migration tường minh. Thay init SQL và chạy `crawler-init` mặc định không tự nâng cấp schema. Không dùng `--force-db-reset` hoặc xóa volume để cập nhật code.

## Bot Telegram điều khiển crawler (đã deploy 2026-10-09)

Menu `/run_crawl` (xác nhận 2 phút), `/status`, `/schedule`, `/history`, `/total` và các quy tắc nguồn dữ liệu nằm trong [runbook Telegram](telegram-crawler-control.md). Bot host mặc định tắt (`TELEGRAM_CONTROL_ENABLED=false`); deploy có `--enable-telegram-bot` mới kích hoạt bot mới. Cần image tag mới cùng host bundle; bundle gồm `telegram_control.py`, `telegram_state.py` và `suumo-crawler-telegram.service`. Giữ SQLite trong `state/` khi cập nhật. Đã deploy release `20261009-telegram-01` và bật bot trên VPS; menu và các lệnh xem đã kiểm chứng bằng code host, chưa chạy thử crawler/cleanup VPN thật. Xem [biên bản release](crawler-release-20261009-telegram-01.md).
