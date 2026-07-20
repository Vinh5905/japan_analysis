# Hướng dẫn các mode của Cloudflare WARP trên macOS

Tài liệu này giải thích 7 lựa chọn mode trong Cloudflare WARP / Cloudflare One Client.

Hiểu nhanh:

- **DNS** = bước hỏi tên miền, ví dụ `suumo.jp` có địa chỉ IP nào.
- **Traffic** = dữ liệu web/app thật sự đi qua mạng sau khi đã biết IP.
- **WARP tunnel** = đường hầm mã hóa từ máy bạn tới mạng Cloudflare.

Một câu dễ nhớ:

> **DNS only** chỉ đổi cách hỏi địa chỉ.
> **Traffic and DNS** đưa cả DNS và traffic đi qua Cloudflare.
> **Traffic only** đưa traffic qua Cloudflare nhưng DNS vẫn do macOS xử lý.
> **Local proxy** chỉ app nào được cấu hình proxy mới đi qua WARP.

---

## Vùng 1 — DNS only: chỉ xử lý DNS, không tunnel traffic

Vùng này có **2 lựa chọn**:

### 1. DNS only (HTTPS)

Mode này chỉ gửi truy vấn DNS qua Cloudflare bằng **DNS-over-HTTPS**.

Nghĩa là khi bạn mở một trang web, máy sẽ hỏi Cloudflare địa chỉ IP của tên miền đó. Nhưng sau khi có IP rồi, kết nối web thật sự vẫn đi bằng mạng bình thường của bạn, không đi qua WARP tunnel.

Dễ hiểu hơn:

```text
DNS đi qua Cloudflare
Traffic web vẫn đi trực tiếp qua mạng của bạn
```

Dùng khi:

- Chỉ muốn DNS riêng tư hơn.
- Chỉ muốn DNS nhanh/sạch hơn.
- Không cần đổi đường đi của toàn bộ traffic.

Không phù hợp khi:

- Muốn vượt lỗi routing tới một website.
- Muốn traffic đi qua Cloudflare.
- Muốn thử vào các trang như `suumo.jp` khi mạng hiện tại không vào được.

### 2. DNS only (TLS)

Mode này cũng chỉ xử lý DNS, nhưng dùng **DNS-over-TLS**.

Khác với HTTPS ở chỗ DNS-over-TLS thường dùng cổng riêng cho DNS mã hóa. Về ý nghĩa sử dụng thì gần giống DNS only (HTTPS): chỉ DNS đi qua Cloudflare, còn traffic web không đi qua WARP tunnel.

Dễ hiểu hơn:

```text
DNS đi qua Cloudflare bằng TLS
Traffic web vẫn đi trực tiếp qua mạng của bạn
```

Dùng khi:

- Muốn DNS mã hóa theo kiểu DNS-over-TLS.
- Mạng của bạn không chặn DNS-over-TLS.

Không phù hợp khi:

- Cần tunnel toàn bộ traffic.
- Cần đổi đường đi mạng để vào website khó truy cập.

---

## Vùng 2 — Traffic and DNS: WARP đầy đủ, xử lý cả traffic và DNS

Vùng này có **3 lựa chọn**. Đây là nhóm nên dùng nếu bạn muốn WARP hoạt động đúng nghĩa như một tunnel cho toàn bộ máy.

### 3. Traffic and DNS (UDP)

Mode này đưa cả traffic và DNS đi qua Cloudflare, sử dụng UDP làm giao thức chính cho tunnel.

Dễ hiểu hơn:

```text
DNS đi qua Cloudflare
Traffic web/app cũng đi qua Cloudflare
Tunnel ưu tiên UDP
```

Dùng khi:

- Muốn hiệu năng tốt.
- Mạng hiện tại không chặn UDP.
- Muốn dùng WARP đầy đủ.

Nhược điểm:

- Một số Wi-Fi công ty, trường học, khách sạn hoặc mạng công cộng có thể chặn/hạn chế UDP.
- Nếu bật không ổn định, hãy thử HTTPS.

### 4. Traffic and DNS (HTTPS)

Mode này đưa cả traffic và DNS đi qua Cloudflare, còn phần DNS được mã hóa theo hướng HTTPS.

Đây là lựa chọn cân bằng và dễ dùng nhất trong nhiều trường hợp vì HTTPS thường ít bị mạng chặn hơn UDP hoặc TLS riêng.

Dễ hiểu hơn:

```text
DNS đi qua Cloudflare bằng HTTPS
Traffic web/app cũng đi qua Cloudflare
Phù hợp khi cần WARP đầy đủ nhưng muốn ổn định hơn
```

Dùng khi:

- Muốn WARP xử lý cả DNS và traffic.
- Muốn thử sửa lỗi không vào được website do DNS/routing.
- Đang dùng mạng có thể chặn UDP.
- Cần lựa chọn ổn định để truy cập `suumo.jp`.

Khuyến nghị:

```text
Để chạy với suumo.jp, dùng: Traffic and DNS (HTTPS)
```

### 5. Traffic and DNS (TLS)

Mode này cũng đưa cả traffic và DNS đi qua Cloudflare, nhưng phần DNS dùng DNS-over-TLS.

Dễ hiểu hơn:

```text
DNS đi qua Cloudflare bằng TLS
Traffic web/app cũng đi qua Cloudflare
```

Dùng khi:

- Muốn WARP đầy đủ.
- Muốn DNS mã hóa theo kiểu TLS.
- Mạng hiện tại không chặn DNS-over-TLS.

Nhược điểm:

- Có thể kém linh hoạt hơn HTTPS trên một số mạng.
- Nếu lỗi kết nối, nên thử Traffic and DNS (HTTPS).

---

## Vùng 3 — Mode đặc biệt: dùng khi có nhu cầu riêng

Vùng này có **2 lựa chọn**:

### 6. Traffic only

Mode này đưa traffic của máy qua WARP, nhưng DNS vẫn do macOS hoặc DNS hiện tại của bạn xử lý.

Dễ hiểu hơn:

```text
Traffic web/app đi qua Cloudflare
DNS không đi qua DNS proxy của WARP
```

Dùng khi:

- Muốn traffic đi qua WARP nhưng đang bị lỗi DNS proxy.
- Máy có phần mềm DNS riêng và bạn không muốn WARP can thiệp DNS.
- Muốn né lỗi kiểu `CF_DNS_PROXY_FAILURE` do xung đột DNS.

Nhược điểm:

- DNS vẫn phụ thuộc vào macOS/mạng hiện tại.
- Một số tính năng dựa trên DNS của Cloudflare có thể không hoạt động.
- Không phải lựa chọn tốt nhất nếu vấn đề nằm ở DNS.

### 7. Local proxy

Mode này không tự đưa toàn bộ máy qua WARP. Thay vào đó, WARP mở một proxy local trên máy, rồi app nào được cấu hình dùng proxy đó thì app đó mới đi qua WARP.

Dễ hiểu hơn:

```text
Toàn máy không tự đi qua WARP
Chỉ app nào cấu hình proxy mới đi qua WARP
```

Dùng khi:

- Chỉ muốn một trình duyệt hoặc một app cụ thể đi qua WARP.
- Làm dev/test proxy.
- Không muốn ảnh hưởng toàn bộ hệ thống.

Không phù hợp khi:

- Muốn bật WARP cho toàn bộ máy.
- Muốn cách dùng đơn giản.
- Không muốn cấu hình proxy thủ công trong từng app.

---

## Nên chọn mode nào?

| Nhu cầu                                            | Mode nên dùng         |
| --------------------------------------------------- | ----------------------- |
| Chỉ muốn đổi DNS                                | DNS only (HTTPS)        |
| Muốn WARP đầy đủ, ổn định                   | Traffic and DNS (HTTPS) |
| Muốn hiệu năng tốt, mạng không chặn UDP      | Traffic and DNS (UDP)   |
| Bị lỗi DNS proxy nhưng vẫn muốn tunnel traffic | Traffic only            |
| Chỉ muốn một app cụ thể đi qua WARP           | Local proxy             |

---

## Ghi chú cho suumo.jp

Để chạy với `suumo.jp`, nên dùng:

```text
Traffic and DNS (HTTPS)
```

Lý do:

- `DNS only` chỉ đổi DNS, không đổi đường đi traffic.
- `Traffic and DNS (HTTPS)` đưa cả DNS và traffic qua Cloudflare.
- HTTPS thường ổn định hơn trên nhiều loại mạng.
- Phù hợp hơn khi cần xử lý lỗi truy cập do DNS/routing.

Sau khi chọn mode này, nên làm:

```text
1. Disconnect WARP
2. Chọn Traffic and DNS (HTTPS)
3. Connect lại WARP
4. Mở lại suumo.jp bằng tab ẩn danh hoặc trình duyệt khác
```

Lưu ý: WARP không đảm bảo bạn có IP Nhật. Nếu `suumo.jp` chặn IP Cloudflare/WARP hoặc yêu cầu IP Nhật thật, bạn vẫn có thể cần VPN có server Nhật.
