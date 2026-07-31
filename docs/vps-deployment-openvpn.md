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
apt install -y git curl ca-certificates nano
```

- `git`: clone repo từ GitHub.
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

## 6. Clone repo từ GitHub

Chạy trên VPS:

```bash
mkdir -p /opt
cd /opt
git clone https://github.com/Vinh5905/japan_analysis.git
cd japan_analysis
```

Repo được clone vào `/opt/japan_analysis`. Trong release flow, VPS cần repo chủ yếu để lấy `Makefile`, `docker-compose.release.yml`, `.env.release.example`, và docs. Code crawler thật chạy từ Docker image đã publish.

Nếu repo private, dùng SSH deploy key hoặc GitHub token thay vì HTTPS public clone.

## 7. Tạo file `.env` cho release

Chạy trên VPS trong `/opt/japan_analysis`:

```bash
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

Chạy trên VPS trong `/opt/japan_analysis`:

```bash
docker login
```

Lệnh này chỉ cần khi Docker Hub image là private hoặc Docker Hub yêu cầu authenticated pull. Nếu image public, có thể bỏ qua.

```bash
make release-pull
```

Lệnh này pull các image cần thiết: crawler image, PostgreSQL, MinIO.

Start PostgreSQL, MinIO và bootstrap:

```bash
make release-up
```

`release-up` làm các việc:

- Start `postgres` container.
- Start `minio` container.
- Chạy `crawler-init` một lần.

`crawler-init` làm các việc:

- Đợi PostgreSQL sẵn sàng.
- Tạo schema crawler nếu DB chưa có bảng crawler.
- Chạy `main.py` để tạo MinIO bucket và prefixes như `suumo/data/`, `suumo/page_source/`, `suumo/image/`.

Kiểm tra container:

```bash
make release-ps
```

Xem log:

```bash
make release-logs
```

## 10. Chạy crawler trên VPS

Chạy theo thứ tự:

```bash
make release-crawl-links
```

Spider `suumo_links` lấy danh sách link mới và ghi vào `tmp/suumo_links.txt`.

```bash
make release-crawl-html
```

Spider `suumo_html` đọc link mới, crawl HTML, gzip payload, upload lên MinIO `suumo/page_source`, và ghi metadata vào PostgreSQL.

```bash
make release-crawl-page
```

Spider `suumo_page` đọc các task `pending`, tải raw HTML từ MinIO, parse dữ liệu, gzip JSON batch, upload lên MinIO `suumo/data`, rồi update `crawl_tasks.batch_id`.

## 11. Cài OpenVPN client trên host

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

## 12. Chuẩn bị route giữ SSH trước khi bật VPN

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

## 13. Persist route SSH trong OpenVPN config

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

## 14. Bật VPN với safety rollback

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

## 15. Chạy crawler khi VPN host đang bật

Khi host đã đi qua VPN, Docker container mặc định cũng đi outbound qua NAT của host, nên crawler thường sẽ đi qua VPN.

Kiểm tra public IP bên trong crawler image:

```bash
docker compose --env-file .env -f docker-compose.release.yml run --rm suumo-tools sh -lc 'curl -4 ifconfig.me'
```

Nếu output là IP Nhật/VPN, crawler outbound đang đi qua VPN.

Chạy crawler:

```bash
make release-crawl-links
make release-crawl-html
make release-crawl-page
```

## 16. Lệnh cứu khi VPN làm mất SSH

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

## 17. Cập nhật code/image sau này

Trên máy local:

```bash
git pull
make docker-login
make docker-build-push-release tag=latest
make docker-inspect-release tag=latest
```

Trên VPS:

```bash
cd /opt/japan_analysis
git pull
make release-pull
make release-up
```

`git pull` lấy compose/docs/Makefile mới. `release-pull` lấy Docker image mới. `release-up` đảm bảo PostgreSQL, MinIO và bootstrap đang ở trạng thái sẵn sàng.
