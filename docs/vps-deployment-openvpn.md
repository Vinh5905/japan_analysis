# VPS Deployment And OpenVPN Runbook

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

Folder `/opt/suumo-crawler` là nơi đặt file release runtime. VPS không cần source Python và không cần `Makefile`; code crawler thật nằm trong Docker image `kevinpham9257/suumo-crawler:<tag>`.

Từ máy local, copy file release lên VPS:

```bash
scp -i ~/.ssh/suumo_vps -P VPS_SSH_PORT docker-compose.release.yml .env.release.example VPS_USER@VPS_HOST:/opt/suumo-crawler/
```

Nếu bạn đã có file `.env` riêng trên local, copy thẳng `.env` thay vì `.env.release.example`.

## 7. Tạo file `.env` cho release

Chạy trên VPS trong `/opt/suumo-crawler`:

```bash
cd /opt/suumo-crawler
cp .env.release.example .env
nano .env
```

`cp` tạo config runtime thật từ file mẫu. `nano` mở file để sửa password và tag image.

Sửa tối thiểu:

```env
SUUMO_CRAWLER_IMAGE=kevinpham9257/suumo-crawler
SUUMO_CRAWLER_TAG=latest

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
make docker-build-push-release tag=latest
```

Lệnh này dùng Docker Buildx để build image cho cả:

```text
linux/amd64
linux/arm64
```

VPS thường là `linux/amd64`, còn Mac Apple Silicon là `linux/arm64`. Nếu chỉ build/push theo platform của Mac, VPS có thể lỗi `no matching manifest for linux/amd64`.

Kiểm tra manifest trên Docker Hub:

```bash
make docker-inspect-release tag=latest
```

Output cần có cả:

```text
Platform: linux/amd64
Platform: linux/arm64
```

## 9. Pull image và start release runtime trên VPS

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

Sau đó mới bật auto-start khi VPS reboot:

```bash
systemctl enable openvpn-client@japan
```

Không dùng `enable --now` trong lần đầu, vì `--now` vừa enable vừa start ngay, dễ tự khóa SSH nếu route chưa đúng.

## 17. Chạy crawler khi VPN host đang bật

Khi host đã đi qua VPN, Docker container mặc định cũng đi outbound qua NAT của host, nên crawler thường sẽ đi qua VPN.

Kiểm tra public IP bên trong crawler image:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-tools sh -lc 'curl -4 ifconfig.me'
```

Nếu output là IP Nhật/VPN, crawler outbound đang đi qua VPN.

Chạy crawler:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-links
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-html
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-page
```

## 18. Tự động chạy pipeline bằng systemd timer

Nên dùng `systemd timer` thay vì cron vì dễ xem trạng thái, log, lần chạy kế tiếp, và có `Persistent=true` để chạy bù nếu VPS bị tắt đúng lịch.

Trước hết test pipeline thủ công trong `/opt/suumo-crawler`:

```bash
cd /opt/suumo-crawler
docker compose --env-file .env -f docker-compose.release.yml up -d postgres minio
docker compose --env-file .env -f docker-compose.release.yml run --rm crawler-init
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-links
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-html
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-page
```

Lệnh này chạy đủ thứ tự:

```text
bootstrap -> suumo_links -> suumo_html -> suumo_page
```

Nếu một bước lỗi, shell/systemd sẽ dừng và không chạy bước tiếp theo.

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
ExecStartPre=/usr/bin/docker compose --env-file .env -f docker-compose.release.yml up -d postgres minio
ExecStartPre=/usr/bin/docker compose --env-file .env -f docker-compose.release.yml run --rm crawler-init
ExecStart=/usr/bin/docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-links
ExecStart=/usr/bin/docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-html
ExecStart=/usr/bin/docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-page
```

Giải thích:

- `Type=oneshot`: job chạy xong thì kết thúc, phù hợp crawler batch.
- `WorkingDirectory=/opt/suumo-crawler`: nơi có `.env`, `docker-compose.release.yml`, và thư mục `tmp`.
- `ExecStartPre=... up -d postgres minio`: đảm bảo PostgreSQL và MinIO đang chạy trước khi crawl.
- `ExecStartPre=... crawler-init`: đảm bảo DB schema và MinIO bucket/prefix đã sẵn sàng.
- Ba dòng `ExecStart`: chạy lần lượt `suumo-links`, `suumo-html`, rồi `suumo-page`. `Type=oneshot` cho phép nhiều dòng `ExecStart` chạy tuần tự.
- `Requires=docker.service`: nếu Docker không chạy thì service không nên chạy.
- `After=docker.service network-online.target`: đợi Docker và network sẵn sàng trước.

Không đặt `docker compose pull` trong scheduled service. Nếu OpenVPN đang bật, VPS có thể không kết nối được Docker Hub registry và làm job fail trước khi crawl. Image nên được pull thủ công lúc deploy/update, sau đó job định kỳ chỉ chạy crawler bằng image đã có sẵn.

Nếu muốn pipeline chỉ chạy khi host OpenVPN đã bật, có thể thêm vào phần `[Unit]`:

```systemd
Wants=openvpn-client@japan.service
After=openvpn-client@japan.service
```

Không dùng `Requires=openvpn-client@japan.service` nếu bạn chưa chắc VPN luôn ổn, vì VPN lỗi sẽ làm pipeline không chạy.

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

Nếu muốn chạy mỗi 2 ngày lúc 19:00, dùng:

```systemd
[Unit]
Description=Run SUUMO crawler pipeline every 2 days at 19:00

[Timer]
OnCalendar=*-*-01/2 19:00:00
Persistent=true
Unit=suumo-crawler-pipeline.service

[Install]
WantedBy=timers.target
```

Nếu muốn chạy mỗi 3 ngày lúc 19:00, đổi thành:

```systemd
OnCalendar=*-*-01/3 19:00:00
```

Nếu muốn chạy mỗi ngày lúc 19:00, đổi thành:

```systemd
OnCalendar=*-*-* 19:00:00
```

Giải thích:

- `OnCalendar=*-*-01/2 19:00:00`: chạy lúc 19:00 các ngày 1, 3, 5, 7... trong tháng.
- `OnCalendar=*-*-01/3 19:00:00`: chạy lúc 19:00 các ngày 1, 4, 7, 10... trong tháng.
- `OnCalendar=*-*-* 19:00:00`: chạy mỗi ngày lúc 19:00.
- `Persistent=true`: nếu VPS tắt đúng lúc tới lịch, lần boot tiếp theo systemd sẽ chạy bù.
- `Unit=suumo-crawler-pipeline.service`: timer này kích hoạt service pipeline.

Không dùng `OnBootSec` cho case này. Nếu VPS đã boot từ lâu rồi mới tạo timer, mốc boot có thể đã qua và timer có thể chạy ngay hoặc rất sớm. `OnCalendar` phù hợp hơn vì nó bám vào giờ cố định trong ngày.

Preview lịch chạy tiếp theo:

```bash
systemd-analyze calendar '*-*-01/2 19:00:00'
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

Trên máy local:

```bash
git pull
make docker-login
make docker-build-push-release tag=latest
make docker-inspect-release tag=latest
```

Trên VPS:

```bash
cd /opt/suumo-crawler
systemctl stop openvpn-client@japan
docker compose --env-file .env -f docker-compose.release.yml --profile tasks --profile tools pull
systemctl start openvpn-client@japan
```

`systemctl stop openvpn-client@japan` tạm tắt VPN để Docker Hub pull ổn định qua network public của VPS. Sau khi pull xong, `systemctl start openvpn-client@japan` bật lại VPN để crawler outbound đi qua Nhật.

Lệnh `pull` lấy Docker image mới. Nếu chỉ sửa Python crawler code hoặc Scrapy settings trong image, lần chạy one-shot tiếp theo như `suumo-html` sẽ dùng image mới đã pull.

Nếu `docker-compose.release.yml` thay đổi trong GitHub, copy file mới từ máy local lên VPS:

```bash
scp -i ~/.ssh/suumo_vps -P VPS_SSH_PORT docker-compose.release.yml VPS_USER@VPS_HOST:/opt/suumo-crawler/
```

Nếu thay đổi compose config cho service chạy nền, ví dụ `mem_limit`, `cpus`, `pids_limit`, recreate PostgreSQL và MinIO:

```bash
cd /opt/suumo-crawler
docker compose --env-file .env -f docker-compose.release.yml up -d --force-recreate postgres minio
```

Không cần chạy `crawler-init` cho mỗi lần update. Chỉ chạy lại khi setup VPS lần đầu, DB/MinIO volume mới hoặc rỗng, vừa xóa volume, hoặc vừa thay đổi logic bootstrap/schema init:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm crawler-init
```
