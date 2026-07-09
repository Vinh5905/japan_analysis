# 📚 DOCKER HANDBOOK CHO DATA ENGINEER

> *Bộ tài liệu toàn diện từ con số 0 đến production-ready — hiểu sâu bản chất, ứng dụng thực tế trong Data Engineering*

---

## 🗺️ MỤC LỤC TỔNG THỂ

**PHẦN 1: NỀN TẢNG VÀ TƯ DUY DOCKER**

- Chương 1: Docker là gì và vì sao Data Engineer cần hiểu Docker
- Chương 2: Các khái niệm nền tảng
- Chương 3: Docker hoạt động bên trong như thế nào?

**PHẦN 2: DOCKER CLI TỪ CƠ BẢN ĐẾN THÀNH THẠO**

- Chương 4: Nhóm lệnh quản lý container
- Chương 5: Nhóm lệnh quản lý image
- Chương 6: Nhóm lệnh hệ thống (volume, network, prune, stats, cp)

**PHẦN 3: DOCKERFILE TỪ CƠ BẢN ĐẾN NÂNG CAO**

- Chương 7: Các instruction cốt lõi
- Chương 8: So sánh sâu các cặp khái niệm dễ nhầm
- Chương 9: Viết Dockerfile thực tế (Python, FastAPI, ETL, dbt)
- Chương 10: Tối ưu Dockerfile (Multi-stage, BuildKit, security)

**PHẦN 4: VOLUME, BIND MOUNT VÀ DỮ LIỆU**

- Chương 11: Ephemeral filesystem và các loại mount
- Chương 12: Quản lý dữ liệu database trong Docker

**PHẦN 5: DOCKER NETWORKING**

- Chương 13: Các loại network và cơ chế hoạt động
- Chương 14: Service discovery, DNS, debug network

**PHẦN 6: DOCKER COMPOSE**

- Chương 15: Compose từ A-Z
- Chương 16: Compose patterns cho multi-service

**PHẦN 7: DOCKER CHO DATA ENGINEERING (TRỌNG TÂM)**

- Chương 17: Vì sao Data Engineer phải master Docker
- Chương 18: Container hóa ETL/ELT pipeline
- Chương 19: Airflow với Docker chi tiết
- Chương 20: Spark với Docker
- Chương 21: Kafka với Docker
- Chương 22: Database (PostgreSQL/MySQL) trong Docker
- Chương 23: dbt với Docker
- Chương 24: Data Lake local với MinIO
- Chương 25: Jupyter với Docker
- Chương 26: 🚀 Mini Project — Mini Data Platform hoàn chỉnh

**PHẦN 8: DOCKER NÂNG CAO**

- Chương 27: Image layer & build cache deep dive
- Chương 28: BuildKit, buildx, multi-platform
- Chương 29: Registry, tagging, security
- Chương 30: Resource limits, healthcheck, observability
- Chương 31: Debug như một chuyên gia

**PHẦN 9: PERFORMANCE VÀ OPTIMIZATION**

- Chương 32: Tối ưu image, build, runtime
- Chương 33: Trade-off và khi nào KHÔNG nên dùng Docker

**PHẦN 10: DOCKER TRONG CI/CD VÀ PRODUCTION**

- Chương 34: Build pipeline với Docker
- Chương 35: Compose vs Swarm vs Kubernetes
- Chương 36: Anti-patterns phổ biến

**PHẦN 11: LỘ TRÌNH HỌC**

- Chương 37: Roadmap 4-8 tuần chi tiết

---

## 🎓 CÁCH HỌC TÀI LIỆU NÀY HIỆU QUẢ

### 1. Đừng đọc lướt — hãy gõ lại mọi lệnh

Docker là kỹ năng thực hành. Đọc 10 trang lý thuyết không bằng gõ 10 lệnh `docker run`. Mỗi khi thấy đoạn code, hãy **mở terminal và gõ lại**. Quan sát output. Khi có lỗi, đừng vội Google — hãy đọc kỹ thông báo lỗi trước.

### 2. Học theo nguyên tắc "Why → What → How"

Với mỗi khái niệm, hãy đặt 3 câu hỏi:

- **Why:** Vì sao Docker đẻ ra cái này? Vấn đề nào nó giải quyết?
- **What:** Bản chất nó là gì? (không phải định nghĩa, mà là cơ chế bên trong)
- **How:** Cách dùng đúng và tối ưu là gì?

Nếu chỉ trả lời được "How" mà không trả lời được "Why" và "What", bạn chưa thực sự hiểu.

### 3. Áp dụng quy tắc "1 chương = 1 buổi = 1 demo"

Đừng vội. Mỗi chương đáng để dành 1–3 giờ. Sau khi đọc xong:

- Làm **bài tập cuối chương**
- Trả lời **câu hỏi tự kiểm tra**
- **Tự viết lại bằng lời mình** những gì đã học (kỹ thuật Feynman — cực hiệu quả)

### 4. Sử dụng môi trường thật

- **Mac/Windows:** Cài Docker Desktop
- **Linux:** Cài Docker Engine trực tiếp (ưu tiên — sát production)
- **Windows:** WSL2 + Docker Desktop là combo mạnh nhất

### 5. Học theo project-based

Đừng học Docker để "biết Docker". Hãy đặt mục tiêu:

> *"Sau 4 tuần, tôi sẽ build được một local data platform có Airflow + Postgres + MinIO + Spark chạy bằng Docker Compose."*

### 6. Cẩn thận với 3 cái bẫy phổ biến

- **Bẫy 1:** Copy-paste Dockerfile từ ChatGPT/Google mà không hiểu.
- **Bẫy 2:** Tin rằng "container = mini VM". Container **KHÔNG** phải VM.
- **Bẫy 3:** Bỏ qua phần "bản chất bên trong". Khi production crash lúc 3 giờ sáng, kiến thức này là thứ cứu bạn.

### 7. Mindset Data Engineer

Khác với Web Dev, Data Engineer dùng Docker để:

- Tạo môi trường **reproducible** cho data pipeline
- Chạy local stack mô phỏng production (Airflow, Spark, Kafka, Postgres...)
- Test data quality và pipeline logic
- Đóng gói transformation jobs
- CI/CD cho dbt, Airflow DAGs

---

## 📋 CHECKLIST CHUẨN BỊ TRƯỚC KHI HỌC

- [ ] Đã cài Docker Desktop (Mac/Win) hoặc Docker Engine (Linux)
- [ ] Đã chạy thành công `docker run hello-world`
- [ ] Đã có editor: VS Code + extension Docker + Dev Containers
- [ ] Đã có terminal quen tay (Bash/Zsh/PowerShell)
- [ ] Đã biết Linux cơ bản: `cd`, `ls`, `cat`, `grep`, `ps`, `kill`
- [ ] Đã biết Python cơ bản
- [ ] Có ít nhất 16GB RAM (Data stack ngốn RAM khủng)
- [ ] Có 30GB ổ cứng trống

---

# 📘 PHẦN 1: NỀN TẢNG VÀ TƯ DUY DOCKER

> *Đây là phần quan trọng nhất. Nếu bạn chỉ đọc 1 phần duy nhất, hãy đọc phần này.*

---

## 📖 CHƯƠNG 1: DOCKER LÀ GÌ VÀ VÌ SAO DATA ENGINEER CẦN HIỂU DOCKER

### 1.1. Câu chuyện trước khi có Docker

Hãy bắt đầu bằng một câu chuyện rất thật mà có lẽ bạn (hoặc đồng nghiệp bạn) đã từng trải qua.

**Năm 2012**, bạn là một Data Engineer mới vào công ty. Sếp giao: *"Em chạy thử pipeline ETL bằng Python 3.6 nhé."*

Bạn mở laptop, cài Python 3.6. Nhưng máy bạn đã có Python 3.10 sẵn cho project khác. Bạn loay hoay với `pyenv`, `virtualenv`, `conda`. Cuối cùng cũng cài được.

Bạn cài thêm thư viện: `pandas==0.23`, `psycopg2==2.7`, `pyspark==2.4`. Một số thư viện cần `libpq-dev`, `openjdk-8`, `gcc` ở system level. Bạn `apt install`, `brew install` tùm lum.

Sau 2 ngày, pipeline chạy được trên máy bạn.

Bạn gửi code cho đồng nghiệp. Họ chạy: **`ModuleNotFoundError`**. Họ chạy lại: **`Java version mismatch`**. Họ thử trên Windows: **`fcntl module not found`** (vì `fcntl` chỉ có trên Linux).

Sếp hỏi: *"Deploy lên server production được chưa?"*

Server production là Ubuntu 18.04, Python 3.6.5 (khác bản patch trên máy bạn). Đoán xem: lỗi tiếp.

Đây chính là **"It works on my machine"** problem — vấn đề kinh điển của software engineering.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Máy Dev       │      │   Máy QA        │      │   Production    │
│                 │      │                 │      │                 │
│ Python 3.6.9    │      │ Python 3.6.5    │      │ Python 3.6.0    │
│ pandas 0.23.1   │ ───▶ │ pandas 0.23.4   │ ───▶ │ pandas 0.22.0   │
│ Ubuntu 22.04    │      │ CentOS 7        │      │ Ubuntu 18.04    │
│ ✅ CHẠY OK      │      │ ⚠️  LỖI         │      │ ❌ CRASH        │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

**Vấn đề cốt lõi:** Phần mềm không chỉ là code. Phần mềm =

```
code + dependencies + system libraries + OS environment + config + data
```

Khi bạn copy code sang máy khác, bạn chỉ copy được phần "code", còn 5 phần còn lại thì... mỗi máy mỗi khác.

### 1.2. Docker là gì? — Định nghĩa thật sự

Hầu hết tài liệu định nghĩa: *"Docker là nền tảng container hóa..."* — nghe rất kêu nhưng người mới đọc xong vẫn không hiểu gì.

Hãy định nghĩa theo cách thực dụng:

> 💡 **Docker là công cụ giúp bạn đóng gói toàn bộ "phần mềm + dependencies + môi trường" vào một đơn vị duy nhất gọi là *container*, để nó chạy y hệt nhau ở bất kỳ đâu — máy bạn, máy đồng nghiệp, server production.**

Nói cách khác, Docker giải quyết bài toán **"môi trường không nhất quán"** bằng cách:

1. Đóng gói app + dependencies + OS libraries vào một **image** (như file ZIP đặc biệt)
2. Chạy image đó thành một **container** (như một process bị cô lập)
3. Đảm bảo container đó hành xử y hệt nhau trên mọi máy có Docker

#### Phép so sánh kinh điển: Container như "container hàng hóa"

Trước những năm 1950, vận chuyển hàng hóa quốc tế là ác mộng. Mỗi loại hàng có cách đóng gói riêng, cách xếp riêng. Sang cảng khác phải dỡ ra, xếp lại theo chuẩn cảng đó.

**Năm 1956**, Malcolm McLean phát minh ra **shipping container** (container chở hàng chuẩn). Mọi hàng hóa — dù là quần áo, máy móc, hay chuối — đều bỏ vào container chuẩn 20-foot hoặc 40-foot. Tàu, cẩu, xe tải, kho bãi đều thiết kế theo chuẩn này.

Kết quả: cách mạng vận tải toàn cầu. Chi phí vận chuyển giảm 95%.

**Docker container chính là "shipping container" cho phần mềm.** Dù bên trong là Python app, Java app, hay Spark cluster — đều được đóng gói chuẩn, chạy được trên bất kỳ "tàu" nào (máy có Docker Engine).

```mermaid
graph LR
    subgraph "Trước Docker"
        A1[App A: Python 3.6] --> M1[Máy A]
        A2[App B: Python 3.10] --> M1
        A3[Cài chồng chéo, xung đột!]
    end
    subgraph "Sau Docker"
        B1[Container A: Python 3.6] --> D[Docker Engine]
        B2[Container B: Python 3.10] --> D
        D --> M2[Máy duy nhất]
        B3[Không xung đột, cô lập!]
    end
```

### 1.3. So sánh chạy app truyền thống vs dùng Docker

#### Cách truyền thống

Để chạy một ETL Python job, bạn cần:

```bash
# Trên máy host (máy thật)
sudo apt update
sudo apt install python3.9 python3-pip libpq-dev gcc
pip install pandas psycopg2 sqlalchemy
# ... rồi cuối cùng:
python etl_job.py
```

**Hệ quả:**

- Cài đặt vào hệ thống → "ô nhiễm" máy host
- Nếu project khác cần Python 3.7, bạn phải dùng virtualenv (chỉ cách ly Python, không cách ly system libs)
- Đổi máy → cài lại từ đầu, mất nhiều giờ
- Đổi version Python toàn cục → các project khác hỏng

#### Cách dùng Docker

```bash
# Chỉ 1 lệnh duy nhất
docker run --rm -v $(pwd):/app -w /app python:3.9 python etl_job.py
```

**Hệ quả:**

- Không cài gì vào máy host
- Mọi dependencies nằm trong container
- Chạy xong, container biến mất (nếu dùng `--rm`)
- Sang máy khác: y hệt 1 lệnh, y hệt kết quả

#### Bảng so sánh

| Tiêu chí              | Truyền thống                            | Docker                       |
| ----------------------- | ----------------------------------------- | ---------------------------- |
| Cài đặt dependencies | Cài vào máy host                       | Đóng gói trong image      |
| Cách ly                | Yếu (virtualenv chỉ cách ly Python)    | Mạnh (namespaces + cgroups) |
| Reproducibility         | Thấp — phụ thuộc môi trường        | Rất cao — image bất biến |
| Khởi động app        | Phụ thuộc OS, có thể mất nhiều giờ | Vài giây                   |
| Đổi version           | Phức tạp, dễ hỏng                     | Chỉ đổi tag image         |
| Multi-app cùng máy    | Dễ xung đột                            | Cách ly hoàn toàn         |
| Clean up                | Khó (file rác khắp nơi)               | Dễ (`docker rm`)          |
| Production parity       | Thấp (dev khác prod)                    | Cao (cùng image)            |

### 1.4. Container khác gì Virtual Machine (VM)?

Đây là câu hỏi **bắt buộc phải hiểu** vì 80% người mới hiểu sai chỗ này.

#### Cấu trúc Virtual Machine

```
┌─────────────────────────────────────────┐
│            App A      App B             │
├─────────────────────────────────────────┤
│  Libraries    │    Libraries            │
├───────────────┼─────────────────────────┤
│   Guest OS    │     Guest OS            │  <- Mỗi VM có 1 OS đầy đủ
│  (Ubuntu 20)  │   (CentOS 7)            │     (kernel + userland)
├───────────────┴─────────────────────────┤
│           Hypervisor (VMware, KVM)      │  <- Tầng ảo hóa phần cứng
├─────────────────────────────────────────┤
│           Host OS (Linux/Windows)       │
├─────────────────────────────────────────┤
│           Hardware (CPU, RAM, Disk)     │
└─────────────────────────────────────────┘
```

VM là **một máy tính ảo hoàn chỉnh**: có CPU ảo, RAM ảo, ổ cứng ảo, BIOS ảo, và một **operating system riêng** (cả kernel riêng).

#### Cấu trúc Docker Container

```
┌─────────────────────────────────────────┐
│         App A          App B            │
├─────────────────────────────────────────┤
│ Libraries A         Libraries B         │  <- Mỗi container có lib riêng
├─────────────────────────────────────────┤
│         Docker Engine                   │  <- Quản lý containers
├─────────────────────────────────────────┤
│         Host OS Kernel                  │  <- DÙNG CHUNG kernel với host!
├─────────────────────────────────────────┤
│         Hardware                        │
└─────────────────────────────────────────┘
```

Container là **process (hoặc nhóm process) chạy trên host OS, được cô lập** bằng các tính năng của Linux kernel (namespaces, cgroups). Container **dùng chung kernel** với host, **không có OS riêng**.

#### Khoảnh khắc "Aha!" — Container chỉ là một process

> 🔑 **Container, ở mức bản chất nhất, chỉ là một process Linux bình thường, được kernel cô lập khỏi các process khác.**

Nó không phải "máy ảo nhẹ". Nó là **process**. Bạn có thể `ps aux` trên host và **nhìn thấy** process của container chạy trong danh sách.

#### Bảng so sánh chi tiết

| Tiêu chí                                | Virtual Machine                   | Container                                     |
| ----------------------------------------- | --------------------------------- | --------------------------------------------- |
| **Có OS riêng?**                  | Có (full kernel + userland)      | Không (dùng kernel host, chỉ có userland) |
| **Khởi động**                    | Phút (boot OS)                   | Mili-giây (chạy process)                    |
| **Kích thước**                   | GB (ISO image)                    | MB (rootfs)                                   |
| **RAM tiêu thụ**                  | GB                                | MB                                            |
| **Cô lập**                        | Hardware-level (mạnh)            | Process-level (yếu hơn nhưng đủ tốt)    |
| **Mật độ trên 1 host**          | 5-10 VM                           | 100-1000 container                            |
| **Có thể chạy OS khác kernel?** | Có (Windows VM trên Linux host) | Không (chỉ chạy app dùng Linux kernel)    |
| **Phù hợp cho**                   | Cách ly mạnh, multi-tenant      | Microservices, dev/test, data pipeline        |

#### Tại sao điều này quan trọng cho Data Engineer?

1. **Container "nhẹ" nên chạy được nhiều dịch vụ cùng lúc**: Bạn có thể chạy Airflow + Postgres + Spark + Kafka + MinIO trên 1 laptop. Với VM, chắc chắn không nổi.
2. **Container không có "OS thật"**: Khi bạn `docker exec` vào container, bạn KHÔNG vào một máy ảo. Bạn vào một process tree bị cô lập. Đừng cài systemd, đừng `sudo apt upgrade`, đừng coi nó như VM.
3. **Container chia sẻ kernel host**: Nghĩa là container Linux **không chạy được trên kernel Windows thật**. Docker Desktop trên Windows/Mac thực ra chạy một Linux VM nhỏ bên dưới, rồi container chạy trong VM đó.

### 1.5. Image khác Container thế nào?

```
Image     =  Class (trong OOP)     =  Bản thiết kế nhà
Container =  Object (instance)     =  Ngôi nhà được xây dựng từ bản vẽ
```

- **Image**: **Template bất biến (immutable)** — chứa filesystem + metadata + cấu hình mặc định. Image chỉ đọc.
- **Container**: **Instance đang chạy** của image — có thể chạy, dừng, ghi data tạm.

#### Ví dụ cụ thể

```bash
# Image: postgres:15 - bản thiết kế "PostgreSQL phiên bản 15"
docker pull postgres:15

# Container: instance đang chạy của postgres:15
docker run --name db1 -e POSTGRES_PASSWORD=secret -d postgres:15
docker run --name db2 -e POSTGRES_PASSWORD=secret -d postgres:15
# Từ 1 image, tạo ra 2 container chạy độc lập
```

```mermaid
graph TD
    I[Image: postgres:15<br/>Read-only template]
    I --> C1[Container: db1<br/>Running, writable layer]
    I --> C2[Container: db2<br/>Running, writable layer]
    I --> C3[Container: db3<br/>Stopped]
```

**Quan trọng:**

- Image **không chạy**, nó chỉ là file (tập hợp các layer được lưu trên đĩa).
- Container **chạy được**, nó có process, network, filesystem riêng.
- Khi bạn `docker run`, Docker **tạo một writable layer** trên top của image read-only, rồi khởi động process.

### 1.6. Vì sao Docker quan trọng trong Software Engineering nói chung?

#### a) Reproducibility — Tái lập được

Image là **bất biến**. Hash digest của image không bao giờ thay đổi. Nghĩa là:

> *Container chạy hôm nay y hệt container chạy 5 năm trước, nếu cùng image digest.*

Đây là tiền đề cho:

- **Deterministic builds**: Build hôm nay giống hôm qua
- **Bisect lỗi production**: Có thể "lùi thời gian" về image cũ để debug
- **Audit trail**: Biết chính xác phiên bản nào đang chạy

#### b) Isolation — Cách ly

Hai container không thấy nhau (nếu không cấu hình network share). App A crash không kéo App B chết. App A dùng Python 3.6, App B dùng Python 3.11 — không xung đột.

#### c) Portability — Chạy được mọi nơi

Image build trên Mac, chạy được trên Linux server, chạy được trong Kubernetes cluster trên AWS. **Build once, run anywhere** — nhưng cần lưu ý: kiến trúc CPU (ARM vs AMD64) vẫn phải match.

#### d) Efficiency — Hiệu quả tài nguyên

Container nhẹ → chạy nhiều container/server → tiết kiệm chi phí hạ tầng → dễ scale.

#### e) Speed — Tốc độ

- Build image: từ vài giây đến vài phút
- Khởi động container: mili-giây
- Deploy: push image, pull image, run — vài giây

### 1.7. Vì sao Docker đặc biệt quan trọng với Data Engineer?

#### a) Local data platform — Mô phỏng production trên laptop

Một data platform production thường gồm:

```
Airflow (orchestration)
  ├── PostgreSQL (metadata DB)
  ├── Redis (Celery broker)
  └── Workers
Spark (compute)
  ├── Master
  └── Workers
Kafka (streaming)
  └── Zookeeper / KRaft
MinIO / S3 (data lake)
PostgreSQL / MySQL (source DBs)
Trino / Presto (query engine)
dbt (transformation)
```

Cài tất cả những thứ này lên laptop bằng cách truyền thống? **Không khả thi.** Một số chỉ chạy được trên Linux. Một số xung đột port. Một số ngốn RAM. Một số phụ thuộc Java version khác nhau.

Với Docker Compose: **1 file `compose.yaml`, 1 lệnh `docker compose up`, và bạn có cả data platform chạy trên laptop.**

#### b) Reproducible pipeline — Pipeline tái lập được

Một ETL pipeline cần:

- Python version cụ thể
- Library version cụ thể (pandas 2.0 khác pandas 1.5 RẤT NHIỀU)
- System libraries (psycopg2 cần libpq)
- JDBC drivers (cho database connection)
- Spark version (Spark 3.3 khác Spark 3.5)

Đóng gói pipeline trong image → 5 năm sau pull image vẫn chạy giống y nguyên.

#### c) Onboarding nhanh

Junior mới vào, thay vì mất 1 tuần cài môi trường:

```bash
git clone repo
docker compose up
# Xong, code được luôn
```

#### d) Testing pipeline

Bạn cần test ETL job với PostgreSQL phiên bản giống production?

```bash
docker run -d --name test-pg -e POSTGRES_PASSWORD=test postgres:15.4
# Chạy test, xong rồi:
docker rm -f test-pg
```

Không "ô nhiễm" môi trường. Mỗi test bắt đầu từ trạng thái sạch.

#### e) CI/CD cho data pipeline

- Build image cho ETL job trong CI
- Run unit test trong container
- Push image lên registry
- Airflow/Argo trong production pull image về chạy

Image = đơn vị deploy chuẩn.

#### f) Dependency hell killer

Project A dùng `pandas 1.5 + numpy 1.23` (vì compatibility với pyspark 3.3).
Project B dùng `pandas 2.0 + numpy 1.25` (vì cần Arrow integration mới).

Trên cùng máy host: ác mộng.
Trong Docker: hai container, hai môi trường riêng biệt, zero conflict.

#### g) Vendor-neutral

Code chạy trên Docker → chạy được trên AWS ECS, GCP Cloud Run, Azure Container Apps, Kubernetes, on-prem. Không bị khóa vào vendor cụ thể.

---

### ✅ TÓM TẮT CHƯƠNG 1

#### Kiến thức cốt lõi

1. Docker giải quyết bài toán **"It works on my machine"** bằng cách đóng gói app + dependencies + môi trường vào container.
2. **Container ≠ VM**. Container chỉ là **process bị cô lập** bằng namespaces & cgroups; nó dùng chung kernel với host.
3. **Image = template bất biến**, **Container = instance đang chạy** từ image.
4. Docker quan trọng vì: **reproducibility, isolation, portability, efficiency, speed**.
5. Đặc biệt với Data Engineer: Docker là cách duy nhất khả thi để có local data platform mô phỏng production.

#### Câu hỏi tự kiểm tra

1. Giải thích "It works on my machine" problem và Docker giải quyết nó như thế nào?
2. Container và VM khác nhau ở điểm cốt lõi nào? (Gợi ý: cái gì được chia sẻ?)
3. Tại sao một container chỉ vài MB nhưng một VM nhỏ nhất cũng vài GB?
4. Nếu bạn có image `python:3.9`, có thể tạo bao nhiêu container từ nó?
5. Container có thể chạy Windows app trên Linux host không? Vì sao?
6. Liệt kê 3 lý do Data Engineer nên dùng Docker mà người mới chưa nghĩ tới.

#### Bài tập thực hành

**Bài 1:** Cài Docker trên máy bạn. Chạy:

```bash
docker run hello-world
```

Đọc kỹ output, nó kể bạn nghe Docker đã làm gì.

**Bài 2:** Chạy 2 container Python khác version cùng lúc:

```bash
docker run --rm python:3.8 python -c "import sys; print(sys.version)"
docker run --rm python:3.11 python -c "import sys; print(sys.version)"
```

Quan sát: trên máy bạn KHÔNG cài Python 3.8 hay 3.11 mà vẫn chạy được.

**Bài 3:** Chạy PostgreSQL trong Docker:

```bash
docker run -d --name mydb -e POSTGRES_PASSWORD=secret -p 5432:5432 postgres:15
docker ps
docker logs mydb
```

Dùng `psql` hoặc DBeaver kết nối tới `localhost:5432`. Quan sát: máy bạn không cài PostgreSQL nhưng vẫn có DB đầy đủ.

**Bài 4 (mở):** Viết bằng lời mình 1 đoạn 200-300 chữ giải thích Docker cho một người bạn không làm tech (ví dụ: mẹ của bạn). Đây là test Feynman — nếu bạn giải thích được, bạn đã hiểu.

#### Lỗi thường gặp ở Chương 1

| Lỗi                                                           | Nguyên nhân                             | Cách sửa                                                   |
| -------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------ |
| `docker: Cannot connect to the Docker daemon`                | Docker daemon chưa chạy                 | Khởi động Docker Desktop /`sudo systemctl start docker` |
| `permission denied while trying to connect to Docker socket` | User chưa thuộc group`docker` (Linux) | `sudo usermod -aG docker $USER`, logout/login lại         |
| `Error response from daemon: pull access denied`             | Image không tồn tại hoặc tên sai     | Kiểm tra tên trên Docker Hub                              |
| Chạy`docker run python` lâu lần đầu                     | Docker đang download image               | Bình thường, lần sau sẽ nhanh (đã cache)              |

#### Best Practices

- ✅ **Luôn dùng tag cụ thể**: `python:3.11-slim` thay vì `python` hoặc `python:latest`
- ✅ **Học cách đọc lỗi**: Docker error message thường rất rõ ràng
- ✅ **Hiểu trước khi gõ**: Đừng copy lệnh mà không hiểu
- ❌ **Đừng coi container như VM**: Đừng SSH vào, đừng cài đè dependencies runtime
- ❌ **Đừng dùng `latest` trong production**: `latest` hôm nay khác `latest` 1 tháng sau

---

## 📖 CHƯƠNG 2: CÁC KHÁI NIỆM NỀN TẢNG

Chương này định nghĩa **đầy đủ và chính xác** từng khái niệm. Bạn cần hiểu chắc chắn vì chúng sẽ xuất hiện xuyên suốt tài liệu.

### 2.1. Image

**Định nghĩa:** Image là một **read-only template** chứa filesystem + metadata để tạo container.

**Bản chất bên trong:**

- Image là **tập hợp các layer xếp chồng** (stacked layers), mỗi layer là một tarball các file thay đổi so với layer dưới.
- Image có một **manifest** (JSON) mô tả các layer, kiến trúc CPU, config mặc định (CMD, ENV, EXPOSE...).
- Image được định danh bởi **digest** (SHA256 hash) — bất biến — và có thể có **tag** (như `postgres:15`) — có thể đổi.

**Ví dụ:**

```bash
docker image ls
# REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
# postgres     15        a8c5edc8a3b1   2 weeks ago   379MB
# python       3.11      4a26b75b9e1c   1 week ago    1.01GB
```

**Demo: Inspect cấu trúc image**

```bash
docker pull alpine:3.19
docker image inspect alpine:3.19
# Sẽ thấy: Architecture, Os, Layers (mảng SHA256), Config (Cmd, Env, ...), RootFS
```

### 2.2. Container

**Định nghĩa:** Container là một **instance đang chạy (hoặc đã từng chạy)** của image, với một **writable layer** thêm vào.

**Bản chất bên trong:**

- Container = process(es) Linux bị cô lập + writable filesystem layer + cấu hình runtime (network, volume, env...).
- Khi container chạy, Docker tạo một **thin writable layer** trên top of image layers. Mọi thay đổi (write file, install package) đều ghi vào layer này.
- Khi container bị xóa, writable layer biến mất (trừ khi đã commit hoặc dùng volume).

**Ví dụ:**

```bash
docker run -d --name web nginx:1.25
docker ps
# CONTAINER ID   IMAGE        STATUS         NAMES
# 8c2d5f3a       nginx:1.25   Up 5 seconds   web
```

**Demo: Quan sát writable layer**

```bash
docker run -d --name test alpine:3.19 sleep 3600
docker exec test sh -c "echo 'hello' > /tmp/test.txt"
docker diff test
# A /tmp/test.txt   <- 'A' nghĩa là Added
```

### 2.3. Dockerfile

**Định nghĩa:** Dockerfile là **text file chứa các instruction** để Docker build image.

**Bản chất:** Mỗi instruction trong Dockerfile (hầu hết) tạo ra **một layer** trong image. Đây là lý do thứ tự instruction ảnh hưởng đến cache.

**Ví dụ tối giản:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

Chi tiết từng instruction sẽ ở **Chương 7**.

### 2.4. Layer

**Định nghĩa:** Layer là một **lớp filesystem** trong image, chứa các thay đổi (added/modified/deleted files) so với layer dưới.

**Bản chất bên trong:**

- Mỗi layer là một **tarball** chứa các file thay đổi.
- Các layer **xếp chồng** dùng OverlayFS (sẽ học ở Chương 3) để tạo thành filesystem hoàn chỉnh.
- Layer **bất biến**, có thể được **chia sẻ giữa nhiều image** → tiết kiệm dung lượng.

**Ví dụ:**

Hai image `python:3.11-slim` và `nginx:1.25` đều dựa trên `debian:bookworm-slim`. Layer của Debian được chia sẻ → bạn chỉ tốn dung lượng cho layer riêng của mỗi image.

```bash
docker history python:3.11-slim
# IMAGE          CREATED         CREATED BY                          SIZE
# 4a26b75b9e1c   2 weeks ago    /bin/sh -c #(nop) CMD ["python3"]   0B
# <missing>      2 weeks ago    /bin/sh -c set -eux; ...            45.2MB
# ...
```

### 2.5. Registry

**Định nghĩa:** Registry là **kho lưu trữ image** từ xa, hỗ trợ push/pull.

**Bản chất:** Registry là một HTTP API tuân thủ chuẩn OCI Distribution Spec. Bạn push image lên, pull image về.

**Các registry phổ biến:**

- **Docker Hub** (`docker.io`) — public, mặc định khi bạn không chỉ định
- **GitHub Container Registry** (`ghcr.io`) — tích hợp với GitHub
- **Amazon ECR** (`*.dkr.ecr.*.amazonaws.com`) — AWS
- **Google Artifact Registry** — GCP
- **Azure Container Registry** — Azure
- **Harbor**, **Nexus**, **JFrog Artifactory** — self-hosted (cho enterprise)

**Cấu trúc đầy đủ của image reference:**

```
[registry]/[namespace]/[repository]:[tag]@[digest]
```

Ví dụ:

- `postgres:15` → đầy đủ là `docker.io/library/postgres:15`
- `ghcr.io/myorg/myapp:v1.2.3`
- `123.dkr.ecr.us-east-1.amazonaws.com/etl-job:latest`

### 2.6. Volume

**Định nghĩa:** Volume là **cơ chế lưu trữ data bền vững (persistent)** ngoài lifecycle của container.

**Bản chất bên trong:**

- Container có filesystem **ephemeral** — xóa container = mất data.
- Volume là **thư mục được Docker quản lý** (`/var/lib/docker/volumes/...` trên Linux), mount vào container.
- Container xóa, volume vẫn còn → data sống sót.

**Ba loại mount:**

1. **Named volume**: Docker quản lý — `docker volume create mydata`
2. **Bind mount**: Mount thư mục/file trên host vào container — phổ biến cho dev
3. **tmpfs mount**: Mount vào RAM — cho data nhạy cảm, không lưu đĩa

Chi tiết ở **Phần 4**.

### 2.7. Network

**Định nghĩa:** Network là **mạng ảo** mà các container kết nối vào để giao tiếp với nhau hoặc ra ngoài.

**Bản chất bên trong:**

- Docker tạo các **bridge interface** trên host (như `docker0`).
- Mỗi container có **network namespace** riêng → có interface `eth0` ảo, gắn vào bridge.
- Container trên cùng network có thể gọi nhau qua **DNS service name**.

**Các loại network:**

- `bridge` (mặc định) — cô lập, NAT ra ngoài
- `host` — dùng chung network namespace với host (Linux only)
- `none` — không có network
- `overlay` — cho multi-host (Swarm/Kubernetes)

Chi tiết ở **Phần 5**.

### 2.8. Docker Engine

**Định nghĩa:** Docker Engine là **toàn bộ phần mềm chạy trên máy host**, bao gồm:

- **Docker daemon (`dockerd`)** — process chạy nền, quản lý containers, images, networks, volumes
- **Docker CLI (`docker`)** — công cụ dòng lệnh để gọi API của daemon
- **REST API** — giao thức giữa CLI và daemon

```mermaid
graph LR
    U[User] -->|docker run ...| CLI[Docker CLI]
    CLI -->|HTTP API| D[Docker Daemon]
    D -->|gRPC| CD[containerd]
    CD -->|exec| R[runc]
    R --> C[Container]
```

### 2.9. Docker CLI

**Định nghĩa:** Là chương trình `docker` bạn gõ trên terminal. Nó **không thực sự chạy container**, mà chỉ gửi HTTP request đến Docker daemon.

**Bài học quan trọng:** Khi bạn gõ `docker run`, daemon mới là người làm việc thực sự. Đây là lý do bạn có thể `DOCKER_HOST=tcp://remote:2375 docker run ...` để điều khiển Docker từ xa.

### 2.10. Docker Daemon

**Định nghĩa:** `dockerd` — process nền nhận request từ CLI, quản lý containers/images/networks/volumes.

**Quan trọng:**

- Daemon chạy với quyền **root** (trừ rootless mode).
- Daemon nói chuyện với **containerd** (container runtime cấp cao), containerd gọi **runc** (runtime cấp thấp) để tạo container.

### 2.11. Docker Compose

**Định nghĩa:** Công cụ định nghĩa và chạy **multi-container application** qua một file YAML.

**Ví dụ tối giản:**

```yaml
# compose.yaml
services:
  web:
    image: nginx:1.25
    ports:
      - "8080:80"
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
```

Chạy: `docker compose up -d`

Chi tiết ở **Phần 6**.

### 2.12. Build Context

**Định nghĩa:** Là **thư mục (hoặc URL) mà bạn truyền vào `docker build`**, chứa Dockerfile và các file mà Dockerfile có thể `COPY/ADD` vào image.

**Cực kỳ quan trọng:** Toàn bộ build context được **gửi lên Docker daemon** trước khi build bắt đầu. Nếu thư mục có file 10GB, daemon phải nhận 10GB → build cực chậm.

**Cách fix:** Dùng `.dockerignore` (Chương 10).

```bash
docker build -t myapp .
#                    ^
#                    | build context = thư mục hiện tại
```

### 2.13. Tag

**Định nghĩa:** Tag là **nhãn dễ đọc** gắn vào image, dạng `repository:tag`.

**Bản chất:** Tag chỉ là **alias trỏ tới digest**. Tag có thể đổi (push image mới đè lên), nhưng digest thì không.

**Ví dụ:**

```
postgres:15           <- tag '15' của repo 'postgres'
postgres:15.4         <- tag chi tiết hơn
postgres:15.4-alpine  <- variant Alpine
postgres:latest       <- tag 'latest' (NGUY HIỂM, sẽ giải thích)
```

**Tại sao `latest` nguy hiểm?**

- `latest` không phải "phiên bản mới nhất" — nó chỉ là tag mặc định.
- Hôm nay `latest` = 15.4, ngày mai có thể = 16.0 (breaking change).
- → **Đừng dùng `latest` trong production**.

### 2.14. Digest

**Định nghĩa:** Digest là **SHA256 hash của image manifest**, dạng `sha256:abc123...`.

**Bản chất:** Digest **bất biến** — nội dung image y hệt sẽ luôn cùng digest. Đây là cách duy nhất tham chiếu image **đáng tin cậy 100%**.

**Ví dụ:**

```bash
docker pull postgres:15
docker images --digests postgres
# REPOSITORY   TAG   DIGEST                              IMAGE ID
# postgres     15    sha256:a1b2c3d4...                  a8c5edc8a3b1

# Pull bằng digest - bất biến tuyệt đối:
docker pull postgres@sha256:a1b2c3d4...
```

**Best practice production:** Pin image bằng digest, không bằng tag.

```dockerfile
FROM postgres:15@sha256:a1b2c3d4...
```

---

### ✅ TÓM TẮT CHƯƠNG 2

#### Kiến thức cốt lõi

1. **Image** = template bất biến gồm các **layer** xếp chồng.
2. **Container** = instance đang chạy của image + writable layer.
3. **Dockerfile** = blueprint để build image.
4. **Registry** = kho image từ xa (Docker Hub, ECR, GHCR...).
5. **Volume** = data persistent ngoài lifecycle container.
6. **Network** = mạng ảo cho container giao tiếp.
7. **Docker Engine** = daemon + CLI + API.
8. **Tag** = nhãn dễ đọc; **Digest** = hash bất biến.
9. **Build context** = thư mục/URL chứa Dockerfile được gửi cho daemon.
10. **Compose** = công cụ chạy multi-container app từ YAML.

#### Câu hỏi tự kiểm tra

1. Sự khác nhau giữa image và container? Giải thích bằng phép so sánh OOP.
2. Layer là gì? Vì sao layer giúp tiết kiệm dung lượng?
3. Vì sao `latest` tag nguy hiểm trong production?
4. Build context khác Dockerfile thế nào?
5. Khi xóa container, volume có mất không? Vì sao?
6. Docker CLI và Docker daemon — ai làm việc thực sự?
7. Digest và tag — cái nào tin cậy hơn? Vì sao?

#### Bài tập thực hành

**Bài 1:** Pull 3 image và quan sát layer được chia sẻ:

```bash
docker pull python:3.11-slim
docker pull python:3.12-slim
docker images
docker history python:3.11-slim
docker history python:3.12-slim
```

**Bài 2:** Tạo 3 container từ cùng 1 image, quan sát chúng độc lập:

```bash
docker run -d --name c1 alpine sleep 1000
docker run -d --name c2 alpine sleep 1000
docker run -d --name c3 alpine sleep 1000
docker ps
docker exec c1 sh -c "echo 'I am c1' > /tmp/me.txt"
docker exec c2 ls /tmp/   # me.txt có ở c1, không có ở c2
docker exec c2 cat /tmp/me.txt   # No such file
```

**Bài 3:** Tìm digest của image và pull bằng digest:

```bash
docker pull alpine:3.19
docker inspect alpine:3.19 --format '{{.RepoDigests}}'
# Copy digest
docker pull alpine@sha256:<paste-digest-here>
```

#### Best Practices

- ✅ Luôn pin version cụ thể (`postgres:15.4-alpine` thay vì `postgres`)
- ✅ Trong production, dùng digest cho immutability tuyệt đối
- ✅ Hiểu rõ build context — dùng `.dockerignore` để giảm context
- ❌ Đừng dùng tag `latest` trong Dockerfile production
- ❌ Đừng lẫn lộn volume với bind mount

---

## 📖 CHƯƠNG 3: DOCKER HOẠT ĐỘNG BÊN TRONG NHƯ THẾ NÀO?

> *Đây là chương "đắt giá" nhất của Phần 1. Hầu hết developer dùng Docker cả năm mà không hiểu chương này. Người hiểu sẽ debug nhanh hơn 10 lần và thiết kế hệ thống tốt hơn nhiều.*

### 3.1. Bức tranh tổng thể: Container không phải là magic

Trước hết, hãy phá vỡ ảo tưởng: **Docker không phát minh ra container.** Docker chỉ là tool **đóng gói và sử dụng** các công nghệ đã có sẵn trong Linux kernel từ nhiều năm trước.

Các công nghệ cốt lõi:

1. **Linux Namespaces** (2002–2013): Cô lập view của process
2. **cgroups** (2007): Giới hạn tài nguyên (CPU, RAM, IO)
3. **Union/Overlay Filesystem** (2014): Layer filesystem
4. **Capabilities, Seccomp, AppArmor**: Bảo mật

Docker kết hợp những thứ này + một UX dễ dùng = cuộc cách mạng container.

```mermaid
graph TD
    D[Docker / Containerd]
    D --> NS[Linux Namespaces]
    D --> CG[cgroups]
    D --> OF[OverlayFS]
    D --> SEC[Capabilities + Seccomp]
    NS --> N1[PID, Mount, Network,<br/>UTS, IPC, User]
    CG --> C1[CPU, Memory, IO, PIDs]
    OF --> O1[Layered filesystem]
```

### 3.2. Linux Namespaces — Linh hồn của container

#### Namespace là gì?

**Namespace là một tính năng kernel Linux cho phép cô lập "tầm nhìn" của một process về một loại tài nguyên hệ thống.**

Hãy hiểu thế này: bình thường mọi process trên Linux đều **thấy** cùng một "thế giới" — cùng PID space, cùng filesystem, cùng network. Namespace cho phép tạo ra **những "thế giới song song"** — process trong namespace A chỉ thấy thế giới A, không thấy gì ngoài.

#### 6 loại namespace chính mà container dùng

| Namespace               | Cô lập gì                | Ý nghĩa                                                                            |
| ----------------------- | --------------------------- | ------------------------------------------------------------------------------------ |
| **PID**           | Process IDs                 | Process trong container chỉ thấy process của container, không thấy process host |
| **Mount (mnt)**   | Mount points                | Container có filesystem riêng                                                      |
| **Network (net)** | Network stack               | Container có interface, route, port riêng                                          |
| **UTS**           | Hostname, domain            | Container có hostname riêng                                                        |
| **IPC**           | Inter-Process Communication | Cô lập System V IPC, POSIX message queues                                          |
| **User**          | UID/GID mapping             | UID trong container map sang UID khác trên host                                    |

#### 3.2.1. PID Namespace — Cô lập process

**Bình thường:**

```bash
# Trên host
ps aux
# Thấy hàng trăm process: systemd, sshd, nginx, ...
```

**Trong PID namespace của container:**

```bash
docker run --rm -it alpine ps aux
# PID   USER     COMMAND
#   1   root     ps aux
```

Bên trong container, **process `ps aux` chính là PID 1**. Container không thấy bất kỳ process nào khác trên host.

**Bản chất:** Kernel maintain các bảng PID. Process trong PID namespace mới chỉ thấy các PID thuộc namespace đó. Một process có thể có PID 1 trong namespace của nó, nhưng PID 12345 trên host.

**Demo:**

```bash
# Terminal 1: chạy container sleep
docker run --rm --name sleeper alpine sleep 3000 &

# Terminal 2: xem trên host
ps aux | grep sleep
# Sẽ thấy 'sleep 3000' với PID lớn (ví dụ 28473)

# Xem trong container
docker exec sleeper ps aux
# PID 1: sleep 3000
```

**Bài học cho Data Engineer:**

- Trong container, PID 1 thường là process chính của bạn (ví dụ `python etl.py`).
- PID 1 có vai trò đặc biệt: nó nhận signal trực tiếp (SIGTERM khi `docker stop`).
- **Nếu app bạn không xử lý SIGTERM, `docker stop` sẽ kill nó sau 10s grace period** → có thể mất data đang ghi dở.

#### 3.2.2. Mount Namespace — Cô lập filesystem

**Container thấy filesystem riêng:**

```bash
docker run --rm alpine ls /
# bin   etc   home  lib   media mnt   ...
```

Đây là filesystem của Alpine image, **không phải filesystem host**.

**Bản chất:** Khi tạo container, Docker:

1. Tạo mount namespace mới
2. Mount image's rootfs làm root `/` trong namespace đó
3. Pivot root → container không "leo" ra host được

**Demo dễ hiểu:**

```bash
# Trên host
cat /etc/os-release
# Hiển thị: Ubuntu 22.04 / Mac / ... (OS thật)

# Trong container Alpine
docker run --rm alpine cat /etc/os-release
# NAME="Alpine Linux"
```

→ Container thấy `/etc/os-release` khác hoàn toàn host, vì nó dùng filesystem riêng từ image Alpine.

#### 3.2.3. Network Namespace — Cô lập mạng

**Container có:** interface riêng (`eth0`), route table riêng, iptables riêng, port riêng.

**Demo:**

```bash
docker run --rm alpine ip addr
# 1: lo: <LOOPBACK,UP,LOWER_UP> ...
# 2: eth0@if43: ...   <- interface ảo, IP riêng

ip addr   # trên host
# eth0, wlan0, docker0, ...   <- interface thật
```

**Hệ quả quan trọng:**

- Container nghe trên port 80 **trong namespace của nó** không xung đột với port 80 trên host.
- Để truy cập từ host vào port 80 container → cần **port mapping** (`-p 8080:80`).

#### 3.2.4. UTS Namespace — Hostname riêng

```bash
hostname   # trên host: my-laptop

docker run --rm --hostname=etl-worker alpine hostname
# etl-worker
```

#### 3.2.5. IPC Namespace — Cô lập IPC

Cô lập System V IPC (semaphore, shared memory) và POSIX message queues. Ít dùng trực tiếp nhưng quan trọng cho bảo mật.

#### 3.2.6. User Namespace — Map UID

Cho phép UID 0 (root) trong container = UID 100000 (user thường) trên host. **Tăng bảo mật mạnh** — nhưng ít dùng mặc định vì phức tạp.

#### Demo nhìn thấy namespaces

```bash
# Chạy container
docker run -d --name nstest alpine sleep 3000

# Lấy PID của container trên host
PID=$(docker inspect --format '{{.State.Pid}}' nstest)
echo $PID
# Ví dụ: 28473

# Xem namespaces của process này
ls -la /proc/$PID/ns/
# lrwxrwxrwx ... ipc -> 'ipc:[4026532183]'
# lrwxrwxrwx ... mnt -> 'mnt:[4026532181]'
# lrwxrwxrwx ... net -> 'net:[4026532186]'
# lrwxrwxrwx ... pid -> 'pid:[4026532184]'
# lrwxrwxrwx ... uts -> 'uts:[4026532182]'

# So sánh với namespace của shell hiện tại
ls -la /proc/self/ns/
# Số khác hoàn toàn -> chúng ở namespace khác nhau
```

Bạn vừa **thấy bằng mắt** rằng container chỉ là process với namespace khác. Đây là khoảnh khắc "Aha!".

### 3.3. cgroups — Giới hạn tài nguyên

**Namespace cô lập tầm nhìn**, nhưng nếu một container "ngốn" hết RAM host thì sao? → Đó là việc của **cgroups**.

#### cgroups là gì?

**Control Groups** là tính năng kernel để **giới hạn, đo, và phân bổ tài nguyên** (CPU, RAM, IO, network bandwidth, PIDs...) cho một nhóm process.

Khi tạo container, Docker tạo một cgroup và đặt process container vào đó. Nếu cgroup giới hạn RAM 512MB, container vượt → kernel **OOM kill** process.

#### Demo: Giới hạn memory

```bash
# Chạy container với giới hạn 256MB RAM
docker run -d --name memtest --memory=256m alpine sh -c "tail /dev/zero"
# tail /dev/zero sẽ đọc vô tận, ngốn RAM

# Sau vài giây, container bị OOM kill
docker ps -a
# STATUS: Exited (137) ...
# Exit code 137 = 128 + 9 (SIGKILL)
```

#### Demo: Giới hạn CPU

```bash
docker run --rm --cpus=0.5 alpine sh -c \
  "yes > /dev/null"
# yes() chạy vô tận, nhưng chỉ dùng 50% CPU
```

#### Các giới hạn phổ biến

```bash
docker run \
  --memory=2g \           # RAM tối đa 2GB
  --memory-swap=2g \      # Swap = memory (không cho swap)
  --cpus=1.5 \            # 1.5 CPU cores
  --pids-limit=100 \      # Tối đa 100 process
  --blkio-weight=500 \    # IO weight
  myimage
```

**Bài học cho Data Engineer:**

- Spark/Airflow worker có thể ngốn RAM khủng → **luôn set `--memory`** để tránh kéo cả host chết.
- Local dev: nếu compose toàn bộ stack, bạn nên set limit cho từng service để không bị nghẽn máy.

### 3.4. Union/OverlayFS — Phép màu của layer

#### Vấn đề: Image có nhiều layer, làm sao "ráp" thành 1 filesystem?

Image có thể có 10-20 layer. Mỗi layer là một tarball các file. Khi container chạy, nó cần thấy **1 filesystem hoàn chỉnh** — không phải 20 cái rời rạc.

→ Giải pháp: **Union Filesystem** (cụ thể nhất là OverlayFS).

#### OverlayFS hoạt động thế nào?

OverlayFS "đặt chồng" nhiều thư mục lên nhau, tạo ra **một view duy nhất**:

```
┌──────────────────────────┐
│ Upperdir (writable)      │  <- Container's writable layer
├──────────────────────────┤
│ Lowerdir N (read-only)   │  <- Image layer N (top)
├──────────────────────────┤
│ Lowerdir 2 (read-only)   │  <- Image layer 2
├──────────────────────────┤
│ Lowerdir 1 (read-only)   │  <- Image layer 1 (base)
└──────────────────────────┘
            ↓
┌──────────────────────────┐
│ Merged (what container   │  <- Container sees this
│  sees as /)              │
└──────────────────────────┘
```

**Quy tắc:**

- Đọc file: kernel tìm từ trên xuống dưới, lấy file đầu tiên gặp.
- Ghi file mới: ghi vào upperdir.
- Sửa file đã tồn tại ở lowerdir: **copy-up** — copy file lên upperdir rồi sửa (lowerdir không đổi).
- Xóa file lowerdir: tạo "whiteout file" ở upperdir để che.

#### Demo OverlayFS bằng tay (Linux only)

```bash
mkdir lower1 lower2 upper work merged
echo "from lower1" > lower1/a.txt
echo "from lower2 (override)" > lower2/a.txt
echo "only in lower2" > lower2/b.txt

sudo mount -t overlay overlay \
  -o lowerdir=lower2:lower1,upperdir=upper,workdir=work \
  merged

ls merged/
# a.txt  b.txt
cat merged/a.txt
# from lower2 (override)   <- lower2 ở trên, thắng

echo "new file" > merged/c.txt
ls upper/
# c.txt   <- ghi vào upperdir
```

→ Bạn vừa tự build "filesystem dạng image" bằng tay!

#### Tại sao điều này quan trọng cho Data Engineer?

1. **Image layer được chia sẻ**: 10 container cùng image → 10 writable layer + 1 bộ layer image. Tiết kiệm cực lớn.
2. **Build nhanh hơn**: Layer đã build sẽ cache lại. Lần build sau, nếu instruction không đổi, layer được reuse.
3. **Hiểu cache** → viết Dockerfile tối ưu (Chương 10).
4. **Container ephemeral**: Writable layer biến mất khi container bị xóa → **không lưu data quan trọng vào filesystem container**, dùng volume.

### 3.5. Container Runtime: containerd, runc, OCI

Bạn đã biết Docker daemon. Nhưng daemon **không trực tiếp** tạo container. Bên dưới có nhiều tầng.

```mermaid
graph TB
    CLI[docker CLI] -->|HTTP API| D[dockerd]
    D -->|gRPC| CD[containerd]
    CD -->|shim| RC[runc]
    RC -->|clone3, namespaces, cgroups syscalls| K[Linux Kernel]
    K --> C[Container Process]
```

#### Tầng 1: Docker daemon (`dockerd`)

- Quản lý high-level: images, networks, volumes, build
- Gọi xuống containerd

#### Tầng 2: containerd

- **Container runtime cấp cao (high-level runtime)**
- Quản lý lifecycle container: pull image, unpack, start, stop, exec
- Không trực tiếp tạo container — gọi xuống runc
- Cũng được Kubernetes dùng trực tiếp (không cần Docker)

#### Tầng 3: runc

- **Container runtime cấp thấp (low-level runtime)**
- Là executable nhỏ, **trực tiếp gọi syscall** của Linux để:
  - Tạo namespaces (`clone3`, `unshare`)
  - Set cgroups
  - Pivot root
  - Exec process container
- Là implementation tham chiếu của **OCI Runtime Spec**

#### OCI — Open Container Initiative

**OCI** là tổ chức đặt ra **chuẩn cho container**, gồm 2 spec chính:

1. **OCI Image Spec**: Cách image được tổ chức (manifest, layer, config). → Image build bởi Docker chạy được trên Podman, Kubernetes, ECS, GKE...
2. **OCI Runtime Spec**: Cách runtime (như runc) tạo container từ image. → Bạn có thể đổi runc bằng runtime khác (gVisor, Kata Containers...) mà container vẫn chạy.

**Bài học:** Docker không "độc quyền" container. Toàn ngành đã chuẩn hóa. Image bạn build hôm nay vẫn chạy được sau 10 năm trên mọi platform tuân thủ OCI.

### 3.6. Tổng hợp: Khi bạn `docker run`, điều gì xảy ra?

Hãy ghép tất cả lại:

```bash
docker run -d --name web -p 8080:80 nginx:1.25
```

**Diễn biến chi tiết:**

1. **CLI gửi request** đến daemon qua Unix socket `/var/run/docker.sock`.
2. **Daemon kiểm tra image** `nginx:1.25` có sẵn local không.
   - Không có → pull từ Docker Hub (manifest + layers).
3. **Daemon yêu cầu containerd** chuẩn bị container.
4. **containerd unpack** các layer (nếu chưa), set up rootfs với OverlayFS.
5. **containerd tạo OCI runtime spec** (JSON) mô tả namespace, cgroups, mount...
6. **containerd gọi runc** với spec đó.
7. **runc syscall vào kernel:**
   - `clone3()` với flags `CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET | ...` → tạo process mới trong namespace mới.
   - Set up cgroups (giới hạn tài nguyên).
   - `pivot_root` → đổi root filesystem sang rootfs container.
   - `execve()` → chạy command (`nginx -g 'daemon off;'`).
8. **Daemon set up network**:
   - Tạo veth pair (cặp interface ảo).
   - Một đầu vào bridge `docker0`, một đầu vào network namespace container (thành `eth0`).
   - Set up iptables rule cho port mapping (`8080:80`).
9. **Container chạy.** PID 1 trong container là `nginx`.

**Tất cả chỉ mất vài trăm millisecond.** Không có VM, không có boot OS, không có hypervisor. Đó là sức mạnh của container.

---

### ✅ TÓM TẮT CHƯƠNG 3

#### Kiến thức cốt lõi

1. **Container không phải magic** — là process bị cô lập bởi **namespaces + cgroups + OverlayFS**.
2. **Namespaces** cô lập "tầm nhìn" (PID, mount, network, UTS, IPC, user).
3. **cgroups** giới hạn tài nguyên (CPU, RAM, IO, PIDs).
4. **OverlayFS** xếp chồng các layer thành filesystem hợp nhất + writable layer.
5. Kiến trúc tầng: `docker` → `dockerd` → `containerd` → `runc` → kernel syscalls.
6. **OCI** là chuẩn hóa container → image/runtime tương thích chéo.

#### Câu hỏi tự kiểm tra

1. Container và VM khác nhau ở mức kernel như thế nào?
2. Process trong container có PID 1. PID này có phải PID 1 trên host không? Vì sao?
3. Vì sao container chỉ chiếm vài MB RAM (so với VM vài GB)?
4. cgroups khác namespaces như thế nào?
5. OverlayFS giải quyết vấn đề gì? Khi nào file được "copy-up"?
6. Khi `docker stop`, signal nào được gửi đến PID 1? Sau bao lâu sẽ SIGKILL?
7. Nếu Docker biến mất, image bạn build có còn chạy được không? (Gợi ý: OCI)

#### Bài tập thực hành

**Bài 1:** Quan sát namespaces của container:

```bash
docker run -d --name nstest alpine sleep 3000
PID=$(docker inspect --format '{{.State.Pid}}' nstest)
ls -la /proc/$PID/ns/
ls -la /proc/self/ns/
docker rm -f nstest
```

**Bài 2:** Demo OOM kill bằng giới hạn memory:

```bash
docker run --rm --memory=100m alpine sh -c "tail /dev/zero"
# Đợi vài giây, sẽ thấy Killed
echo $?   # 137 = SIGKILL
```

**Bài 3:** Đo CPU bị giới hạn:

```bash
docker run --rm --cpus=0.5 alpine sh -c \
  "time dd if=/dev/zero of=/dev/null bs=1M count=10000"
# So sánh với:
docker run --rm alpine sh -c \
  "time dd if=/dev/zero of=/dev/null bs=1M count=10000"
```

**Bài 4 (suy ngẫm):** Giải thích bằng lời mình: "Vì sao container không thể chạy Windows app trên Linux host?" Câu trả lời nằm ở chương này.

#### Lỗi thường gặp

| Lỗi                                            | Nguyên nhân                      | Cách xử lý                                  |
| ----------------------------------------------- | ---------------------------------- | ---------------------------------------------- |
| Container bị kill với exit code 137           | OOM — vượt memory limit         | Tăng`--memory` hoặc tối ưu app           |
| Container bị kill với exit code 143           | SIGTERM nhận từ`docker stop`   | Bình thường, hoặc app không exit kịp 10s |
| `docker stop` mất 10s mới dừng             | App không xử lý SIGTERM         | Trap signal trong app hoặc dùng tini         |
| Container đọc/ghi chậm                       | OverlayFS overhead trên Mac/Win   | Dùng named volume thay bind mount             |
| `Cannot allocate memory` khi nhiều container | Tổng memory limit vượt RAM host | Set limit hợp lý từng container             |

#### Best Practices

- ✅ **Hiểu PID 1**: App của bạn nên xử lý SIGTERM gracefully (đóng connection, flush data...).
- ✅ **Set resource limit**: `--memory`, `--cpus` cho container production để tránh "ngốn" host.
- ✅ **Dùng `tini` hoặc `dumb-init`** làm PID 1 cho app không tự xử lý signal/zombie process.
- ✅ **Tin tưởng OCI**: Image build từ Docker chạy được trên Podman, Kubernetes, ECS.
- ❌ **Đừng nghĩ container = mini-VM**: Đừng cài systemd, đừng update kernel trong container.
- ❌ **Đừng để container chạy không giới hạn**: Một container malicious/bug có thể kéo cả host chết.

---

## 🎯 KẾT THÚC PHẦN 1

Bạn vừa học:

- Docker là gì, giải quyết vấn đề gì
- Container bản chất là **process bị cô lập**, không phải VM
- Image vs Container vs Layer
- 14 khái niệm nền tảng
- Namespaces, cgroups, OverlayFS — cơ chế cốt lõi
- Kiến trúc tầng Docker daemon → containerd → runc → kernel

**Tiếp theo:** Phần 2 — Docker CLI thành thạo.

---

# 📘 PHẦN 2: DOCKER CLI TỪ CƠ BẢN ĐẾN THÀNH THẠO

> *Mục tiêu phần này: sau khi học xong, bạn không cần Google lệnh Docker nữa. 90% công việc hàng ngày bạn sẽ làm được bằng cơ bắp.*

CLI Docker có hàng trăm lệnh. Nhưng thực tế bạn chỉ dùng khoảng **30 lệnh thường xuyên**. Phần này tổ chức theo nhóm chức năng để dễ nhớ.

---

## 📖 CHƯƠNG 4: NHÓM LỆNH QUẢN LÝ CONTAINER

### 4.1. `docker run` — Lệnh quan trọng nhất

`docker run` là lệnh bạn sẽ gõ nhiều nhất. Hiểu sâu nó = hiểu nửa Docker.

#### Cú pháp đầy đủ

```bash
docker run [OPTIONS] IMAGE[:TAG|@DIGEST] [COMMAND] [ARG...]
```

#### Bản chất bên trong

`docker run` thực ra là **2 lệnh ghép lại**:

```bash
docker run = docker create + docker start
```

- `docker create`: Tạo container (chuẩn bị filesystem, network, cgroup) nhưng chưa chạy
- `docker start`: Khởi động process PID 1 trong container

Hiểu điều này giúp bạn debug: nếu container start xong rồi exit ngay, vấn đề ở **process**, không phải ở việc tạo container.

#### Các option quan trọng — hiểu sâu từng cái

**`-d` / `--detach`** — Chạy nền

```bash
docker run -d nginx:1.25
# Trả về container ID, terminal được giải phóng
# Container chạy nền
```

Không dùng `-d` → container chạy foreground, log đổ ra terminal, bạn `Ctrl+C` → container dừng.

**`-it` — Interactive + TTY**

`-i` (interactive): giữ STDIN mở.
`-t` (TTY): cấp phát terminal giả lập (để có prompt đẹp, color, tab completion).

```bash
docker run -it ubuntu bash
# Bạn vào shell tương tác trong container
```

**Quy tắc nhớ:**

- App service (nginx, postgres) → `-d`
- Tool tương tác (bash, python REPL) → `-it`
- Script chạy 1 lần xong thoát → không cần option nào (nhưng nên `--rm`)

**`--rm` — Auto cleanup**

```bash
docker run --rm alpine echo "hello"
# Container chạy xong sẽ tự xóa, không để lại "rác"
```

Nếu không có `--rm`, container "Exited" vẫn tồn tại. `docker ps -a` sẽ thấy đầy container chết. Dùng `--rm` cho mọi container ad-hoc.

**`--name` — Đặt tên container**

```bash
docker run -d --name webserver nginx
# Sau này có thể: docker stop webserver, docker logs webserver
```

Không đặt tên → Docker tự sinh tên ngẫu nhiên kiểu `clever_einstein`. Tên giúp bạn dễ tham chiếu, đặc biệt trong script.

**`-p` / `--publish` — Port mapping**

```bash
docker run -d -p 8080:80 nginx
#              ^    ^
#              |    +--- port trong container
#              +-------- port trên host
```

- `-p 8080:80` → host port 8080 forward vào container port 80
- `-p 127.0.0.1:8080:80` → chỉ bind localhost (an toàn hơn)
- `-p 80` → expose port, Docker tự chọn host port ngẫu nhiên
- `-P` (chữ hoa) → publish tất cả EXPOSE port trong image với host port ngẫu nhiên

**Lưu ý quan trọng:** Port mapping CHỈ có nghĩa khi container nói với host hoặc external network. **Hai container trên cùng network nói chuyện với nhau KHÔNG cần `-p`** — chúng dùng port trực tiếp.

**`-e` / `--env` — Environment variables**

```bash
docker run -e POSTGRES_PASSWORD=secret postgres
docker run -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=secret postgres

# Đọc từ file:
docker run --env-file .env postgres
```

`.env` format:

```
POSTGRES_USER=admin
POSTGRES_PASSWORD=secret
LOG_LEVEL=info
```

**`-v` / `--volume` — Mount volume/bind**

```bash
# Named volume
docker run -v pgdata:/var/lib/postgresql/data postgres

# Bind mount
docker run -v $(pwd)/code:/app python:3.11 python /app/main.py

# Read-only
docker run -v $(pwd)/config:/etc/app:ro myapp
```

Chi tiết ở Phần 4.

**`-w` / `--workdir` — Working directory**

```bash
docker run -w /app -v $(pwd):/app python:3.11 python main.py
# Tương đương `cd /app` trước khi chạy
```

**`--network` — Chọn network**

```bash
docker run --network=mynet myapp
# Mặc định: bridge network
```

**`--restart` — Restart policy**

```bash
docker run --restart=unless-stopped myapp
# - no: không restart (mặc định)
# - on-failure: restart khi exit code != 0
# - always: luôn restart
# - unless-stopped: restart trừ khi user stop bằng tay
```

Cho production service → `unless-stopped` hoặc `always`.

**`--memory`, `--cpus` — Resource limits**

```bash
docker run --memory=2g --cpus=1.5 myapp
```

Đã giải thích ở Chương 3.

**`--user` / `-u` — Chạy với user khác**

```bash
docker run -u 1000:1000 myapp
# Hoặc:
docker run -u $(id -u):$(id -g) myapp
```

Mặc định container chạy root → ghi file ra bind mount = file thuộc root → host user không xóa được. Fix bằng `-u`.

#### Ví dụ thực tế tổng hợp

```bash
docker run -d \
  --name etl-job \
  --restart=on-failure \
  --memory=4g \
  --cpus=2 \
  -e DB_HOST=postgres \
  -e DB_PASSWORD=secret \
  --env-file .env \
  -v $(pwd)/data:/data:ro \
  -v $(pwd)/logs:/logs \
  --network=data-net \
  myorg/etl-job:v1.2.3
```

**Đọc lệnh trên:** Chạy container ETL ngầm, tên `etl-job`, restart nếu fail, giới hạn 4GB RAM + 2 CPU, set vài env var, mount data read-only và logs writable, gắn vào network `data-net`.

#### Lỗi thường gặp với `docker run`

| Lỗi                                | Nguyên nhân                         | Cách sửa                           |
| ----------------------------------- | ------------------------------------- | ------------------------------------ |
| `port is already allocated`       | Port host đã có app khác chiếm   | Đổi port host hoặc kill app cũ   |
| Container exit ngay                 | App PID 1 crash hoặc command sai     | `docker logs <name>`, đọc lỗi   |
| `no such file or directory`       | Bind mount sai path                   | Dùng absolute path (`$(pwd)/...`) |
| Container chạy`bash` rồi thoát | Không`-it`                         | Thêm`-it`                         |
| `unable to find image`            | Tên image sai hoặc registry private | Check spelling, login registry       |
| `OCI runtime create failed`       | Command không tồn tại trong image  | Check command exec form đúng chưa |

### 4.2. `docker ps` — Xem container đang chạy

```bash
docker ps
# CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS   NAMES
```

**Options quan trọng:**

```bash
docker ps -a          # Show all (cả container đã dừng)
docker ps -q          # Chỉ ID (dùng cho scripting)
docker ps -aq         # ID của mọi container
docker ps -s          # Show size (writable layer size)
docker ps --filter "status=exited"
docker ps --filter "name=etl"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Pattern hữu ích:**

```bash
# Xóa tất cả container đã dừng
docker rm $(docker ps -aq --filter "status=exited")

# Stop tất cả container đang chạy
docker stop $(docker ps -q)
```

### 4.3. `docker exec` — Thực thi lệnh trong container đang chạy

```bash
docker exec [OPTIONS] CONTAINER COMMAND [ARG...]
```

**Use case phổ biến nhất: vào shell debug**

```bash
docker exec -it mydb bash
# Hoặc nếu image không có bash:
docker exec -it mydb sh
```

**Use case khác:**

```bash
# Chạy lệnh 1 lần
docker exec mydb psql -U postgres -c "SELECT version()"

# Kiểm tra process trong container
docker exec mydb ps aux

# Tail log
docker exec mydb tail -f /var/log/app.log
```

**Quan trọng:** `exec` chỉ chạy trên container **đang chạy**. Container đã exit → dùng `docker run` lại hoặc `docker start`.

**Lỗi thường gặp:**

| Lỗi                                | Nguyên nhân                               |
| ----------------------------------- | ------------------------------------------- |
| `executable file not found: bash` | Image alpine không có bash, dùng`sh`   |
| `Container is not running`        | Container đã exit, dùng`docker start`  |
| `the input device is not a TTY`   | Chạy`exec -it` từ script CI, bỏ `-t` |

### 4.4. `docker logs` — Xem log container

```bash
docker logs CONTAINER
```

**Options:**

```bash
docker logs -f mydb              # Follow (như tail -f)
docker logs --tail 100 mydb      # 100 dòng cuối
docker logs --since 1h mydb      # Log 1 giờ qua
docker logs --until 30m mydb     # Log trước 30 phút (kết hợp với --since)
docker logs --timestamps mydb    # Hiển thị timestamp
```

**Bản chất:** Docker capture STDOUT và STDERR của PID 1 trong container và lưu vào file JSON trên host (`/var/lib/docker/containers/<id>/<id>-json.log`). `docker logs` đọc file đó.

**Hệ quả thực tế:**

- Nếu app log ra file (không ra stdout/stderr) → `docker logs` không thấy.
- → **Best practice: app trong container phải log ra stdout/stderr**, không ra file.
- Một số image (như Nginx) symlink `/var/log/nginx/access.log` → `/dev/stdout` để tuân thủ điều này.

**Vấn đề log đầy đĩa:**
Mặc định, file log JSON không giới hạn → có thể đầy disk. Set log rotation:

```bash
docker run --log-opt max-size=10m --log-opt max-file=3 myapp
# Mỗi file log max 10MB, giữ 3 file (tổng max 30MB)
```

Hoặc cấu hình global trong `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### 4.5. `docker stop`, `docker start`, `docker restart`

#### `docker stop`

```bash
docker stop mydb
docker stop mydb --time=30   # Wait 30s trước khi SIGKILL (default 10s)
```

**Bản chất:**

1. Gửi `SIGTERM` cho PID 1 trong container.
2. Đợi 10 giây (default).
3. Nếu vẫn chạy, gửi `SIGKILL` (kill thẳng tay).

**Bài học cho Data Engineer:** Long-running job (Spark, ETL) cần xử lý SIGTERM để flush data, commit transaction, đóng connection. Nếu không, dữ liệu có thể mất.

```python
# Ví dụ Python: xử lý SIGTERM
import signal
import sys

def handler(signum, frame):
    print("Received SIGTERM, cleaning up...")
    # flush data, close connections...
    sys.exit(0)

signal.signal(signal.SIGTERM, handler)
```

#### `docker kill`

```bash
docker kill mydb              # Gửi SIGKILL ngay
docker kill --signal=SIGUSR1 mydb   # Gửi signal khác
```

Nhanh nhưng "bạo lực". Không có cleanup. Tránh dùng trừ khi cần.

#### `docker start`

```bash
docker start mydb        # Khởi động lại container đã dừng
docker start -a mydb     # Attach STDOUT/STDERR (thấy log)
```

Container giữ nguyên writable layer, network config, env... → khởi động lại y nguyên trạng thái khi dừng.

#### `docker restart`

```bash
docker restart mydb
# Tương đương: docker stop + docker start
```

### 4.6. `docker rm`, `docker rmi`

#### `docker rm` — Xóa container

```bash
docker rm mydb
docker rm -f mydb         # Force: stop + rm trong 1 lệnh
docker rm $(docker ps -aq --filter "status=exited")   # Xóa hàng loạt
```

**Lưu ý:** `docker rm` xóa **writable layer** của container. Volume KHÔNG bị xóa (an toàn cho data).

Nếu muốn xóa cả volume gắn anonymous: `docker rm -v <container>`.

#### `docker rmi` — Xóa image

```bash
docker rmi nginx:1.25
docker rmi $(docker images -q --filter "dangling=true")   # Xóa image "dangling" (không tag)
docker rmi -f nginx:1.25                                  # Force, ngay cả khi có container dùng
```

**Lưu ý:**

- Không xóa được image đang được container (chạy hoặc dừng) sử dụng.
- "Dangling image" = image không có tag, thường do build nhiều lần đè lên.

### 4.7. `docker inspect` — "Mổ xẻ" mọi thứ

`docker inspect` trả về JSON đầy đủ về container/image/network/volume.

```bash
docker inspect mydb
docker inspect mynet
docker inspect myvolume
docker inspect nginx:1.25
```

**Output JSON rất dài.** Dùng `--format` (Go template) để query field cụ thể:

```bash
# Lấy IP container
docker inspect --format '{{.NetworkSettings.IPAddress}}' mydb

# Lấy PID trên host
docker inspect --format '{{.State.Pid}}' mydb

# Lấy status
docker inspect --format '{{.State.Status}}' mydb

# Lấy environment variables
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' mydb

# Lấy mount info
docker inspect --format '{{json .Mounts}}' mydb | jq
```

**Use case Data Engineer thực tế:**

```bash
# Lấy IP của postgres container để app khác kết nối
PG_IP=$(docker inspect --format '{{.NetworkSettings.Networks.mynet.IPAddress}}' postgres)
echo $PG_IP
```

### 4.8. `docker stats` — Monitor realtime

```bash
docker stats                  # Tất cả container đang chạy
docker stats mydb            # Container cụ thể
docker stats --no-stream     # 1 lần, không refresh
```

Output:

```
CONTAINER ID   NAME    CPU %   MEM USAGE / LIMIT   MEM %   NET I/O   BLOCK I/O   PIDS
8c2d5f3a       mydb    2.1%    345MiB / 2GiB       16.8%   1.2kB     8.5MB       18
```

**Use case:** Debug Airflow worker ngốn RAM, Spark executor đang chạy bao nhiêu CPU, v.v.

### 4.9. `docker cp` — Copy file vào/ra container

```bash
# Host → Container
docker cp ./data.csv mydb:/tmp/data.csv

# Container → Host
docker cp mydb:/var/log/app.log ./

# Container → Container (qua trung gian)
docker cp c1:/file - | docker cp - c2:/file
```

**Use case:**

- Lấy log/output từ container đã dừng
- Copy dump file vào container DB để restore
- Debug nhanh không muốn rebuild image

**Lưu ý:** Đối với production, đừng dùng `docker cp` để deploy code. Đó là anti-pattern. Build image mới và redeploy.

---

### ✅ TÓM TẮT CHƯƠNG 4

#### Bảng cheat sheet

| Lệnh                                  | Use case                   |
| -------------------------------------- | -------------------------- |
| `docker run -d --name X -p H:C img`  | Chạy service nền         |
| `docker run --rm -it img bash`       | Vào shell một lần       |
| `docker ps -a`                       | Xem tất cả container     |
| `docker exec -it X bash`             | Vào container đang chạy |
| `docker logs -f X`                   | Theo dõi log              |
| `docker stop X` / `docker start X` | Dừng/khởi động         |
| `docker rm -f X`                     | Xóa container (force)     |
| `docker rmi img`                     | Xóa image                 |
| `docker inspect X`                   | Xem JSON metadata          |
| `docker stats`                       | Monitor tài nguyên       |
| `docker cp src dst`                  | Copy file                  |

#### Câu hỏi tự kiểm tra

1. `docker run` thực ra là tổ hợp của 2 lệnh nào?
2. Khác biệt giữa `-p 8080:80` và `-p 80`?
3. Vì sao `docker exec` không chạy được trên container đã exit?
4. Khi `docker stop`, signal nào được gửi đến container?
5. Vì sao log app nên ra stdout/stderr thay vì file?
6. `docker rm -v` khác `docker rm` thế nào?

#### Bài tập thực hành

**Bài 1:** Chạy PostgreSQL + cleanup đúng cách:

```bash
docker run -d --name pg-test \
  -e POSTGRES_PASSWORD=secret \
  -p 5432:5432 \
  --memory=512m \
  --restart=on-failure \
  postgres:15

docker logs -f pg-test    # Quan sát log khởi động (Ctrl+C để thoát)
docker exec -it pg-test psql -U postgres -c "SELECT version();"
docker stats --no-stream pg-test
docker stop pg-test
docker rm pg-test
```

**Bài 2:** Tạo 3 container alpine sleep, sau đó stop và remove hàng loạt:

```bash
for i in 1 2 3; do
  docker run -d --name c$i alpine sleep 1000
done

docker ps
docker stop $(docker ps -q --filter "name=^c")
docker rm $(docker ps -aq --filter "name=^c")
```

**Bài 3:** Lấy IP của container và dùng nó:

```bash
docker network create testnet
docker run -d --name nginx-test --network=testnet nginx:1.25
IP=$(docker inspect --format '{{.NetworkSettings.Networks.testnet.IPAddress}}' nginx-test)
echo "Nginx IP: $IP"
docker run --rm --network=testnet alpine wget -qO- http://$IP
# Hoặc gọi bằng tên service:
docker run --rm --network=testnet alpine wget -qO- http://nginx-test
docker rm -f nginx-test
docker network rm testnet
```

#### Best Practices

- ✅ Luôn dùng `--name` cho container có ý nghĩa
- ✅ Dùng `--rm` cho container ad-hoc
- ✅ Set `--restart` cho production service
- ✅ App phải log ra stdout/stderr
- ✅ Configure log rotation để tránh đầy disk
- ❌ Đừng dùng `docker kill` trừ khi bất đắc dĩ
- ❌ Đừng dùng `docker cp` để deploy code (build image mới)

---

## 📖 CHƯƠNG 5: NHÓM LỆNH QUẢN LÝ IMAGE

### 5.1. `docker pull` — Tải image về

```bash
docker pull postgres:15
docker pull postgres:15.4-alpine
docker pull postgres@sha256:a1b2c3...
docker pull ghcr.io/myorg/myapp:v1.0
```

**Bản chất:**

1. CLI hỏi daemon "pull image X".
2. Daemon liên hệ registry (default: Docker Hub).
3. Registry trả về manifest (JSON).
4. Daemon kiểm tra layer nào đã có local, chỉ tải layer còn thiếu.
5. Verify SHA256.
6. Lưu vào image storage.

**Options:**

```bash
docker pull --platform linux/amd64 postgres:15    # Pull image cho kiến trúc cụ thể
docker pull --all-tags postgres                  # Pull tất cả tag (rất nặng, ít dùng)
docker pull -q postgres:15                       # Quiet
```

### 5.2. `docker images` / `docker image ls` — Liệt kê image

```bash
docker images
# REPOSITORY   TAG     IMAGE ID       CREATED       SIZE
# postgres     15      a8c5edc8a3b1   2 weeks ago   379MB
# python       3.11    4a26b75b9e1c   1 week ago    1.01GB
```

**Options:**

```bash
docker images -a                                 # Cả intermediate image
docker images -q                                 # Chỉ ID
docker images --filter "dangling=true"          # Image không tag
docker images --filter "label=app=etl"          # Image có label
docker images --filter "since=postgres:14"      # Image tạo sau postgres:14
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker images --digests                          # Show digest
```

### 5.3. `docker build` — Build image từ Dockerfile

```bash
docker build -t myapp:v1.0 .
#             ^               ^
#             tag             build context
```

**Options quan trọng:**

```bash
docker build \
  -t myapp:v1.0 \
  -t myapp:latest \                # Multiple tags
  -f Dockerfile.prod \             # Dockerfile khác tên/path
  --build-arg PYTHON_VERSION=3.11 \  # ARG values
  --no-cache \                     # Bỏ qua cache (build sạch)
  --pull \                         # Luôn pull base image mới
  --platform linux/amd64 \         # Build cho platform cụ thể
  --target builder \               # Multi-stage: chỉ build đến stage này
  --progress=plain \               # Verbose output
  .
```

**Lưu ý quan trọng — build context:**

```bash
docker build -t myapp .
# "." là build context = thư mục hiện tại
# TOÀN BỘ thư mục này được gửi cho daemon!
```

Nếu thư mục có `node_modules/` 2GB hoặc `.git/` 500MB → build cực chậm. Dùng `.dockerignore`:

```
# .dockerignore
node_modules/
.git/
*.log
__pycache__/
.venv/
.env
```

Chi tiết về Dockerfile + build ở **Phần 3**.

### 5.4. `docker push` — Đẩy image lên registry

```bash
# Login trước (1 lần)
docker login                            # Docker Hub
docker login ghcr.io                    # GitHub Container Registry
docker login 123.dkr.ecr.us-east-1.amazonaws.com

# Tag image theo định dạng registry
docker tag myapp:v1.0 ghcr.io/myorg/myapp:v1.0

# Push
docker push ghcr.io/myorg/myapp:v1.0
```

**Pattern thực tế:**

```bash
# Build và push
docker build -t ghcr.io/myorg/etl-job:v1.2.3 .
docker push ghcr.io/myorg/etl-job:v1.2.3

# Cũng push tag latest
docker tag ghcr.io/myorg/etl-job:v1.2.3 ghcr.io/myorg/etl-job:latest
docker push ghcr.io/myorg/etl-job:latest
```

### 5.5. `docker tag` — Đặt tag mới cho image

```bash
docker tag myapp:v1.0 ghcr.io/myorg/myapp:v1.0
docker tag <image-id> myapp:rollback
```

**Bản chất:** Tag chỉ là alias trỏ tới image ID. Tag mới KHÔNG copy image — chỉ tạo "tên" mới.

### 5.6. `docker history` — Xem lịch sử layer

```bash
docker history nginx:1.25
# IMAGE          CREATED        CREATED BY                                       SIZE
# 8c2d5f3a       2 weeks ago    /bin/sh -c #(nop)  CMD ["nginx" "-g" "daemon...  0B
# <missing>      2 weeks ago    /bin/sh -c #(nop)  STOPSIGNAL SIGQUIT             0B
# <missing>      2 weeks ago    /bin/sh -c #(nop)  EXPOSE 80                       0B
# <missing>      2 weeks ago    /bin/sh -c set -x  && addgroup --system --gid... 65MB
# ...
```

**Use case:**

- Hiểu image base làm gì
- Tìm layer "to khủng" để optimize
- Debug build cache

```bash
docker history --no-trunc nginx:1.25     # Không cắt ngắn
docker history --format "{{.Size}}: {{.CreatedBy}}" nginx:1.25
```

### 5.7. `docker image inspect`

Đã giải thích ở 4.7. Khác `docker inspect` là chỉ nhắm image.

```bash
docker image inspect postgres:15
docker image inspect --format '{{.Config.Cmd}}' postgres:15
docker image inspect --format '{{.Config.ExposedPorts}}' postgres:15
docker image inspect --format '{{json .Config.Env}}' postgres:15 | jq
```

### 5.8. `docker save` / `docker load` — Export/Import image

Dùng để share image **không qua registry** (offline transfer).

```bash
# Export
docker save myapp:v1.0 -o myapp.tar
docker save myapp:v1.0 | gzip > myapp.tar.gz

# Transfer file (scp, USB, ...)

# Import
docker load -i myapp.tar
gunzip -c myapp.tar.gz | docker load
```

**Use case:** Air-gapped environment (mạng không kết nối internet), demo offline.

### 5.9. `docker import` / `docker export` — Filesystem export

Khác với `save/load`:

- `save/load`: Lưu cả image (manifest + layers + metadata).
- `export/import`: Lưu **filesystem flat** của container (mất metadata, mất layer).

```bash
# Export filesystem container thành tarball
docker export mycontainer > rootfs.tar

# Import tarball thành image (flat, 1 layer)
cat rootfs.tar | docker import - myimage:flat
```

Ít dùng. Chỉ dùng khi muốn "phẳng hóa" image hoặc convert filesystem ngoài thành image.

### 5.10. `docker prune` cho images

```bash
docker image prune              # Xóa dangling image
docker image prune -a           # Xóa cả unused image (nguy hiểm)
docker image prune --filter "until=24h"   # Image cũ hơn 24h
```

---

### ✅ TÓM TẮT CHƯƠNG 5

#### Bảng cheat sheet

| Lệnh                           | Use case             |
| ------------------------------- | -------------------- |
| `docker pull img:tag`         | Tải image           |
| `docker images`               | Liệt kê image      |
| `docker build -t img:tag .`   | Build từ Dockerfile |
| `docker push img:tag`         | Đẩy lên registry  |
| `docker tag old new`          | Đặt tag mới       |
| `docker history img`          | Xem layer history    |
| `docker image inspect img`    | Metadata image       |
| `docker save -o file.tar img` | Export image         |
| `docker load -i file.tar`     | Import image         |
| `docker image prune`          | Dọn dẹp            |

#### Câu hỏi tự kiểm tra

1. `docker pull` chỉ tải lại layer còn thiếu — tại sao có thể làm vậy?
2. Tag và Image ID khác nhau thế nào?
3. `.dockerignore` quan trọng vì lý do gì?
4. `docker save` khác `docker export` thế nào?
5. Khi nào dùng `--no-cache` khi build?

#### Bài tập thực hành

**Bài 1:** Build 1 image đơn giản, push lên Docker Hub:

```bash
mkdir myapp && cd myapp
cat > Dockerfile <<EOF
FROM alpine:3.19
RUN echo "Hello from Docker" > /msg.txt
CMD cat /msg.txt
EOF

docker build -t myapp:v1 .
docker run --rm myapp:v1

# Đăng ký Docker Hub trước, rồi:
docker tag myapp:v1 <yourusername>/myapp:v1
docker login
docker push <yourusername>/myapp:v1
```

**Bài 2:** Tìm "thủ phạm" làm image to:

```bash
docker pull python:3.11
docker history python:3.11 --format "table {{.Size}}\t{{.CreatedBy}}" --no-trunc
# Tìm layer > 100MB
```

**Bài 3:** Export image → transfer → import:

```bash
docker save alpine:3.19 -o alpine.tar
ls -lh alpine.tar
docker rmi alpine:3.19
docker load -i alpine.tar
docker images alpine
```

#### Best Practices

- ✅ Pin version cụ thể (`postgres:15.4-alpine`)
- ✅ Dùng `.dockerignore` cho mọi project
- ✅ Tag image theo SemVer hoặc git SHA (vd: `v1.2.3` hoặc `sha-abc1234`)
- ✅ Cleanup image định kỳ (`docker image prune`)
- ❌ Đừng push image chứa secret
- ❌ Đừng dùng `--no-cache` mặc định (chỉ khi cần build sạch)

---

## 📖 CHƯƠNG 6: NHÓM LỆNH HỆ THỐNG

### 6.1. `docker volume`

```bash
docker volume create mydata             # Tạo
docker volume ls                        # Liệt kê
docker volume inspect mydata           # Chi tiết
docker volume rm mydata                 # Xóa
docker volume prune                     # Xóa volume không dùng
```

**Inspect output:**

```json
[{
  "CreatedAt": "2024-...",
  "Driver": "local",
  "Labels": {},
  "Mountpoint": "/var/lib/docker/volumes/mydata/_data",
  "Name": "mydata",
  "Scope": "local"
}]
```

`Mountpoint` là path **thật** trên host (Linux). Bạn có thể `ls` để xem nội dung. Trên Docker Desktop (Mac/Win), mountpoint nằm trong VM Linux ẩn → không trực tiếp access được.

Chi tiết về volume ở **Phần 4**.

### 6.2. `docker network`

```bash
docker network create mynet                       # Tạo (bridge mặc định)
docker network create --driver=bridge mynet       # Chỉ rõ driver
docker network ls                                 # Liệt kê
docker network inspect mynet                      # Chi tiết
docker network rm mynet                           # Xóa
docker network prune                              # Xóa network không dùng

# Gắn container vào network sau khi đã chạy
docker network connect mynet mycontainer
docker network disconnect mynet mycontainer
```

Chi tiết ở **Phần 5**.

### 6.3. `docker system` — Quản lý toàn hệ thống

```bash
docker system df                  # Disk usage breakdown
# TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
# Images          25      5        12.3GB    9.8GB (79%)
# Containers      8       3        450MB     200MB (44%)
# Local Volumes   15      4        5.2GB     3.1GB (59%)
# Build Cache     0       0        0B        0B

docker system df -v               # Verbose, chi tiết từng item

docker system info                # Thông tin Docker installation
docker system events              # Stream events realtime
```

#### `docker system prune` — Dọn dẹp

```bash
docker system prune                    # Xóa: stopped containers, unused networks, dangling images, build cache
docker system prune -a                 # Thêm: tất cả unused image (image không có container)
docker system prune -a --volumes       # Thêm: cả unused volumes (⚠️ MẤT DATA!)
docker system prune --filter "until=24h"   # Chỉ xóa item cũ hơn 24h
```

**⚠️ Cẩn trọng:**

- `--volumes` có thể xóa volume chứa data DB → backup trước!
- `-a` xóa cả image không có container dùng — nếu đang build CI lâu, có thể xóa nhầm.

**Pattern an toàn:**

```bash
# Xem trước cái gì sẽ bị xóa
docker system df

# Xóa dangling thôi cho an toàn
docker system prune -f
```

### 6.4. `docker cp` — Đã giải thích ở 4.9

### 6.5. `docker top`, `docker port`

```bash
docker top mydb                # Xem process trong container (như ps)
docker port mydb               # Xem port mapping của container
```

### 6.6. `docker login` / `docker logout`

```bash
docker login                              # Docker Hub
docker login ghcr.io -u username -p token
docker logout ghcr.io
```

Credentials được lưu vào `~/.docker/config.json` (encoded). Trên Mac/Windows, có thể tích hợp với keychain hệ thống.

### 6.7. `docker version`, `docker info`

```bash
docker version                # Phiên bản client + server
docker info                   # Tổng quan: số container, image, storage driver, ...
```

H��u ích khi debug "version mismatch" hoặc check storage driver (`overlay2` là chuẩn).

---

### ✅ TÓM TẮT CHƯƠNG 6

#### Bảng cheat sheet

| Lệnh                                   | Use case                  |
| --------------------------------------- | ------------------------- |
| `docker volume create/ls/inspect/rm`  | Quản lý volume          |
| `docker network create/ls/inspect/rm` | Quản lý network         |
| `docker system df`                    | Xem disk usage            |
| `docker system prune`                 | Dọn dẹp                 |
| `docker system prune -a --volumes`    | Dọn sạch (cẩn trọng!) |
| `docker system events`                | Stream events             |
| `docker top X`                        | Process trong container   |
| `docker port X`                       | Port mapping              |
| `docker login REGISTRY`               | Auth registry             |
| `docker version` / `docker info`    | Thông tin                |

#### Câu hỏi tự kiểm tra

1. Vì sao `docker system prune --volumes` nguy hiểm?
2. `docker volume inspect` cho biết gì? Có dùng được path đó trên Mac không?
3. Khi cần share image qua registry private, cần làm gì trước khi push?

#### Bài tập thực hành

**Bài 1:** Quan sát disk usage và dọn dẹp:

```bash
docker system df
docker system df -v | head -30
docker system prune -f
docker system df    # So sánh trước/sau
```

**Bài 2:** Test workflow tạo volume → ghi data → xóa container → data còn:

```bash
docker volume create testdata
docker run --rm -v testdata:/data alpine sh -c "echo 'persistent' > /data/file.txt"
docker run --rm -v testdata:/data alpine cat /data/file.txt
# 'persistent'
docker volume rm testdata
```

#### Best Practices

- ✅ Dùng named volume thay anonymous
- ✅ Đặt tên network có ý nghĩa (`data-platform-net`)
- ✅ Định kỳ `docker system df` để theo dõi disk
- ✅ `docker system prune` thường xuyên (không dùng `-a` và `--volumes` trừ khi chắc)
- ❌ Đừng share Docker socket (`/var/run/docker.sock`) với container không tin cậy — đó là root access vào host

---

## 🎯 KẾT THÚC PHẦN 2

Bạn đã nắm được hầu hết lệnh CLI Docker dùng hàng ngày. Phần 3 sẽ chuyển sang **Dockerfile** — viết blueprint cho image của riêng bạn.

---

# 📘 PHẦN 3: DOCKERFILE TỪ CƠ BẢN ĐẾN NÂNG CAO

> *Dockerfile là "công thức nấu ăn" để tạo image. Viết Dockerfile tốt = image nhỏ, build nhanh, an toàn. Viết Dockerfile tệ = image 5GB, build 20 phút, rò rỉ secret.*

---

## 📖 CHƯƠNG 7: CÁC INSTRUCTION CỐT LÕI

### 7.1. Cấu trúc Dockerfile cơ bản

```dockerfile
# Comment bắt đầu bằng #

# 1. Base image (BẮT BUỘC, instruction đầu tiên)
FROM python:3.11-slim

# 2. Metadata (optional)
LABEL maintainer="data-team@example.com"

# 3. Environment setup
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 4. Working directory
WORKDIR /app

# 5. Copy dependencies first (cache-friendly)
COPY requirements.txt .

# 6. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy code
COPY . .

# 8. Expose port (chỉ documentation)
EXPOSE 8000

# 9. Default command
CMD ["python", "main.py"]
```

Bây giờ giải thích từng instruction.

### 7.2. `FROM` — Base image

```dockerfile
FROM <image>[:<tag>] [AS <name>]
```

**Quy tắc:**

- **PHẢI** là instruction đầu tiên (ngoại trừ `ARG` trước nó).
- Có thể có nhiều `FROM` trong 1 file (multi-stage build, Chương 10).
- `AS <name>` đặt tên stage để stage sau tham chiếu.

**Best practices chọn base image:**

| Loại                | Ví dụ                        | Khi dùng                                                                                    |
| -------------------- | ------------------------------ | -------------------------------------------------------------------------------------------- |
| **Full**       | `python:3.11` (~1GB)         | Khi cần đầy đủ tool, không lo size                                                     |
| **Slim**       | `python:3.11-slim` (~150MB)  | Production standard — balance tốt                                                          |
| **Alpine**     | `python:3.11-alpine` (~50MB) | Image nhỏ tối đa, nhưng dùng`musl libc` (có thể incompatible với một số package) |
| **Distroless** | `gcr.io/distroless/python3`  | Production cực bảo mật, chỉ có Python + ứng dụng, không có shell                    |
| **Scratch**    | `scratch`                    | Image trống — chỉ cho binary tĩnh (Go, Rust)                                             |

**Lưu ý Alpine với Python:**
Alpine dùng `musl libc` thay vì `glibc`. Nhiều package Python (pandas, numpy) phải compile từ source trên Alpine → chậm và to. **Cho Data Engineer, `slim` thường tốt hơn `alpine`**.

### 7.3. `WORKDIR` — Đặt working directory

```dockerfile
WORKDIR /app
```

Tương đương `cd /app`. Mọi instruction sau (`RUN`, `COPY`, `CMD`...) sẽ chạy trong `/app`.

**Bản chất:** Nếu `/app` chưa tồn tại, Docker tự tạo. Có thể có nhiều `WORKDIR` (đổi dir nhiều lần).

**Anti-pattern:**

```dockerfile
RUN cd /app && pip install -r requirements.txt
# ❌ Sai: `cd` chỉ ảnh hưởng layer này, các RUN sau không biết
```

**Đúng:**

```dockerfile
WORKDIR /app
RUN pip install -r requirements.txt
```

### 7.4. `COPY` — Copy file từ build context vào image

```dockerfile
COPY <src>... <dest>
COPY ["<src>",... "<dest>"]   # JSON form (cho path có space)
COPY --chown=user:group <src> <dest>
COPY --from=<stage> <src> <dest>   # Multi-stage
```

**Ví dụ:**

```dockerfile
COPY requirements.txt /app/
COPY . /app/
COPY src/*.py /app/src/
COPY --chown=app:app . /app/
```

**Lưu ý:**

- `<src>` là **relative path từ build context**, không phải từ máy bạn.
- `<dest>` thường để absolute path để rõ ràng.
- Nếu `<dest>` kết thúc bằng `/`, được coi là thư mục.
- Wildcard hỗ trợ (Go's `filepath.Match`).

### 7.5. `ADD` — Giống COPY nhưng có thêm "phép thuật"

```dockerfile
ADD <src> <dest>
```

**Khác COPY:**

- `ADD` có thể nhận URL: `ADD https://example.com/file.tar.gz /tmp/`
- `ADD` tự động extract tarball local: `ADD app.tar.gz /app/` → tự `tar xzf`

**Best practice:** **Luôn dùng `COPY`**, trừ khi thực sự cần extract tarball hoặc tải URL. `ADD` "magic" → khó dự đoán.

**Lý do dùng `RUN curl/wget` thay `ADD URL`:**

- `ADD URL` không kiểm tra HTTPS cert, không retry.
- `RUN curl -fsSL URL && verify checksum` an toàn hơn.

### 7.6. `RUN` — Chạy command khi build image

```dockerfile
RUN <command>                          # Shell form
RUN ["executable", "param1", "param2"] # Exec form
```

**Shell form:** Command chạy trong `/bin/sh -c`.

```dockerfile
RUN apt-get update && apt-get install -y curl
```

**Exec form:** Chạy trực tiếp executable, **không qua shell** → không có shell expansion, pipe, redirect.

```dockerfile
RUN ["apt-get", "install", "-y", "curl"]
```

**Best practice: Combine nhiều RUN thành 1 layer**

```dockerfile
# ❌ TỆ: 3 layer, image to
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y vim

# ✅ TỐT: 1 layer, image nhỏ
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        vim && \
    rm -rf /var/lib/apt/lists/*
```

**Vì sao quan trọng?**

- Mỗi `RUN` tạo 1 layer.
- Khi xóa file ở layer sau, file vẫn nằm ở layer trước → image vẫn to.
- `rm -rf /var/lib/apt/lists/*` ở cùng RUN → file không bao giờ "đóng băng" vào layer.

### 7.7. `CMD` — Default command khi container chạy

```dockerfile
CMD ["executable", "param1", "param2"]   # Exec form (ƯU TIÊN)
CMD command param1 param2                 # Shell form
CMD ["param1", "param2"]                  # Default args cho ENTRYPOINT
```

**Quy tắc:**

- Chỉ có **1 CMD** trong Dockerfile (nếu nhiều, cái cuối thắng).
- `CMD` có thể bị **override** bằng `docker run image <new command>`.

**Ví dụ:**

```dockerfile
CMD ["python", "main.py"]
```

```bash
docker run myapp                      # → python main.py
docker run myapp python script.py     # → python script.py (override)
```

### 7.8. `ENTRYPOINT` — Lệnh "cố định" khi container chạy

```dockerfile
ENTRYPOINT ["executable", "param1"]   # Exec form (ƯU TIÊN)
ENTRYPOINT command param1             # Shell form
```

**Khác CMD:**

- `ENTRYPOINT` **không bị override** bởi command line. Args truyền vào docker run sẽ **append** vào ENTRYPOINT.

**Ví dụ:**

```dockerfile
ENTRYPOINT ["python"]
CMD ["main.py"]
```

```bash
docker run myapp                  # → python main.py
docker run myapp script.py        # → python script.py
docker run myapp -c "print(1)"    # → python -c "print(1)"
```

**Use case ENTRYPOINT:**

- Khi container = "single-purpose tool" (như `docker run myimage` luôn chạy `python`)
- Tạo CLI wrapper

Chi tiết so sánh CMD vs ENTRYPOINT ở Chương 8.

### 7.9. `ENV` — Environment variable

```dockerfile
ENV KEY=value
ENV KEY1=value1 KEY2=value2
ENV KEY value         # Form cũ, tránh dùng
```

**Đặc điểm:**

- `ENV` set env var **trong image** — container nào chạy từ image này đều có.
- Có thể override bằng `docker run -e KEY=newvalue`.

**Ví dụ:**

```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/app/.venv/bin:$PATH"
```

**Best practice:**

- Set `PYTHONUNBUFFERED=1` cho Python → log ra stdout không bị buffer.
- Set `PYTHONDONTWRITEBYTECODE=1` → không tạo `.pyc` files.

### 7.10. `ARG` — Build-time variable

```dockerfile
ARG <name>[=<default>]
```

**Khác ENV:**

- `ARG` chỉ tồn tại **lúc build**, không có trong image.
- `ENV` tồn tại **cả build và runtime** trong image.

**Ví dụ:**

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ARG APP_VERSION
LABEL app.version="${APP_VERSION}"
```

Build:

```bash
docker build --build-arg PYTHON_VERSION=3.12 --build-arg APP_VERSION=1.0.0 -t myapp .
```

**Pitfall — ARG trước FROM:**

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim
# ARG PYTHON_VERSION đã "hết hạn" sau FROM
RUN echo $PYTHON_VERSION   # ❌ Empty!

# Fix: khai báo lại
ARG PYTHON_VERSION
RUN echo $PYTHON_VERSION   # ✅ OK
```

### 7.11. `EXPOSE` — Documentation only

```dockerfile
EXPOSE 8000
EXPOSE 5432/tcp 53/udp
```

**Quan trọng:** `EXPOSE` **KHÔNG** publish port. Chỉ là **metadata** cho người đọc Dockerfile biết port nào app dùng.

Để thực sự expose: `docker run -p 8000:8000` hoặc `docker run -P` (publish tất cả EXPOSE).

### 7.12. `USER` — Đổi user

```dockerfile
USER appuser
USER 1000
USER appuser:appgroup
USER 1000:1000
```

**Default:** Container chạy root. Đây là **lỗ hổng bảo mật** — nếu container bị compromise, attacker có root trong container, có thể leo ra host (nếu có misconfiguration).

**Best practice production:**

```dockerfile
RUN groupadd -r app && useradd -r -g app app
USER app
```

### 7.13. `VOLUME` — Khai báo mount point

```dockerfile
VOLUME ["/data", "/logs"]
VOLUME /var/lib/postgresql/data
```

**Tác dụng:**

- Báo cho Docker biết path này nên là volume.
- Nếu user không mount volume, Docker tự tạo anonymous volume.

**Pitfall:** Sau `VOLUME`, mọi thay đổi vào path đó trong các layer sau **sẽ bị bỏ qua** khi container chạy (vì volume đã được mount đè lên). Cẩn thận thứ tự!

### 7.14. `HEALTHCHECK` — Kiểm tra container có "khỏe"

```dockerfile
HEALTHCHECK [OPTIONS] CMD command
```

**Options:**

- `--interval=30s` — chạy mỗi 30s
- `--timeout=10s` — timeout
- `--start-period=60s` — grace period khi mới start
- `--retries=3` — số lần fail trước khi đánh "unhealthy"

**Ví dụ:**

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

**Exit code:**

- `0` — healthy
- `1` — unhealthy

Status hiển thị trong `docker ps`:

```
STATUS                   PORTS
Up 2 minutes (healthy)
Up 5 minutes (unhealthy)
```

**Use case Data Engineer:**

- Postgres: `CMD pg_isready`
- App: HTTP endpoint `/health`
- Kafka: kiểm tra broker connectivity

### 7.15. `LABEL` — Metadata

```dockerfile
LABEL key="value"
LABEL maintainer="data-team@example.com" \
      version="1.0.0" \
      description="ETL job for sales data"
```

Truy vấn:

```bash
docker images --filter "label=maintainer=data-team@example.com"
```

**OCI standard labels:**

```dockerfile
LABEL org.opencontainers.image.source="https://github.com/myorg/myrepo"
LABEL org.opencontainers.image.revision="abc123"
LABEL org.opencontainers.image.version="1.0.0"
```

### 7.16. `SHELL` — Đổi shell mặc định

```dockerfile
SHELL ["/bin/bash", "-c"]
```

Mặc định: `["/bin/sh", "-c"]` (Linux) hoặc `["cmd", "/S", "/C"]` (Windows).

Ít dùng. Chỉ cần khi dùng bash features (`set -o pipefail`):

```dockerfile
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -fsSL example.com | tar xz   # Nếu curl fail, RUN cũng fail
```

### 7.17. Các instruction ít dùng

- `STOPSIGNAL`: Signal gửi khi `docker stop`. Default: `SIGTERM`.
- `ONBUILD`: Trigger cho image kế thừa. Rất ít dùng.
- `MAINTAINER`: Deprecated, dùng `LABEL maintainer` thay.

---

### ✅ TÓM TẮT CHƯƠNG 7

#### Bảng tổng hợp các instruction

| Instruction     | Mục đích                  | Lưu ý                            |
| --------------- | ---------------------------- | ---------------------------------- |
| `FROM`        | Base image                   | BẮT BUỘC đầu tiên             |
| `WORKDIR`     | Set CWD                      | Tạo dir nếu chưa có            |
| `COPY`        | Copy file từ context        | Ưu tiên hơn ADD                 |
| `ADD`         | Copy + extract tarball + URL | Hạn chế dùng                    |
| `RUN`         | Chạy command lúc build     | Combine nhiều RUN thành 1        |
| `CMD`         | Default command              | Bị override bởi docker run args  |
| `ENTRYPOINT`  | Lệnh "cố định"           | Args được append                |
| `ENV`         | Env var (runtime)            | Có trong image                    |
| `ARG`         | Build-time var               | Không có trong image             |
| `EXPOSE`      | Documentation port           | KHÔNG publish                     |
| `USER`        | Đổi user                   | Bảo mật                          |
| `VOLUME`      | Khai báo mount point        | Anonymous volume nếu không mount |
| `HEALTHCHECK` | Kiểm tra container          | Hiển thị healthy/unhealthy       |
| `LABEL`       | Metadata                     | OCI standard labels                |
| `SHELL`       | Đổi shell                  | Hiếm khi cần                     |

---

## 📖 CHƯƠNG 8: SO SÁNH SÂU CÁC CẶP KHÁI NIỆM DỄ NHẦM

### 8.1. CMD vs ENTRYPOINT — Cặp khái niệm bị hiểu sai nhiều nhất

#### So sánh nhanh

| Tính năng                            | CMD                                     | ENTRYPOINT                      |
| -------------------------------------- | --------------------------------------- | ------------------------------- |
| Mục đích                            | Default command**có thể đổi** | Lệnh**cố định**       |
| Override bằng`docker run img <cmd>` | Có (toàn bộ bị thay)                | Không (args bị append)        |
| Use case                               | App "general purpose"                   | App "single-purpose" / CLI tool |

#### Bảng tổng hợp combo

| Dockerfile                                                 | `docker run img`          | `docker run img echo hello` |
| ---------------------------------------------------------- | --------------------------- | ----------------------------- |
| `CMD ["python", "app.py"]`                               | `python app.py`           | `echo hello`                |
| `ENTRYPOINT ["python"]`                                  | `python`                  | `python echo hello`         |
| `ENTRYPOINT ["python"]<br>``CMD ["app.py"]`              | `python app.py`           | `python echo hello`         |
| `ENTRYPOINT ["python", "app.py"]<br>``CMD ["--verbose"]` | `python app.py --verbose` | `python app.py echo hello`  |

#### Khi nào dùng cái nào?

**Dùng `CMD` khi:**

- Container có thể chạy nhiều command khác nhau
- Ví dụ: image `python:3.11` có `CMD ["python3"]` → user có thể `docker run python:3.11 pip install` cũng OK

**Dùng `ENTRYPOINT` (với CMD) khi:**

- Container là single-purpose tool
- Ví dụ: ETL job luôn chạy `python etl.py`, user chỉ cần truyền args

```dockerfile
# Best practice cho ETL job:
ENTRYPOINT ["python", "etl.py"]
CMD ["--mode=daily"]
```

```bash
docker run etl-job                          # python etl.py --mode=daily
docker run etl-job --mode=hourly            # python etl.py --mode=hourly
docker run etl-job --mode=backfill --date=2024-01-01
```

#### Shell form vs Exec form — Đừng nhầm!

**Shell form** (KHÔNG khuyến nghị):

```dockerfile
CMD python app.py
ENTRYPOINT python app.py
```

→ Chạy trong `/bin/sh -c "python app.py"`.
→ PID 1 là `sh`, **không phải `python`**.
→ `python` là PID 2.
→ SIGTERM tới `sh`, không tới `python` → app không nhận signal!

**Exec form** (KHUYẾN NGHỊ):

```dockerfile
CMD ["python", "app.py"]
ENTRYPOINT ["python", "app.py"]
```

→ Chạy trực tiếp.
→ PID 1 là `python`.
→ SIGTERM tới `python` → app có thể cleanup.

**Pitfall exec form:**

```dockerfile
# ❌ Không expand env var
CMD ["echo", "$HOME"]   # In ra literal "$HOME"

# ✅ Nếu cần shell expansion:
CMD ["sh", "-c", "echo $HOME"]
```

### 8.2. COPY vs ADD

| Tính năng                | COPY | ADD                |
| -------------------------- | ---- | ------------------ |
| Copy file local            | ✅   | ✅                 |
| Auto-extract tarball local | ❌   | ✅                 |
| Tải từ URL               | ❌   | ✅                 |
| Recommended                | ✅   | ❌ (chỉ khi cần) |

**Quy tắc:** **Luôn dùng `COPY`** trừ khi:

1. Cần auto-extract tarball local (`ADD app.tar.gz /app/`).
2. Cần tải URL — nhưng nên dùng `RUN curl` thay vì `ADD URL` để verify checksum và xử lý lỗi.

```dockerfile
# ❌ Magic, khó debug
ADD https://github.com/.../release.tar.gz /tmp/

# ✅ Rõ ràng, verify được
RUN curl -fsSL https://github.com/.../release.tar.gz -o /tmp/release.tar.gz && \
    echo "abc123  /tmp/release.tar.gz" | sha256sum -c - && \
    tar -xzf /tmp/release.tar.gz -C /opt && \
    rm /tmp/release.tar.gz
```

### 8.3. ARG vs ENV

| Tính năng                   | ARG                                    | ENV                                                           |
| ----------------------------- | -------------------------------------- | ------------------------------------------------------------- |
| Tồn tại lúc build          | ✅                                     | ✅                                                            |
| Tồn tại trong image         | ❌                                     | ✅                                                            |
| Override khi build            | `--build-arg KEY=val`                | `--build-arg` không được, dùng `-e KEY=val` lúc run |
| Override khi run              | ❌                                     | ✅ với`docker run -e KEY=val`                              |
| Bảo mật (đừng cho secret) | ARG vẫn hiện trong`docker history` | ENV vẫn hiện                                                |

**Pattern phổ biến:**

```dockerfile
ARG APP_VERSION=dev          # Default value
ENV APP_VERSION=${APP_VERSION}   # Forward vào image
```

```bash
docker build --build-arg APP_VERSION=1.2.3 -t myapp .
docker run myapp env | grep APP_VERSION   # APP_VERSION=1.2.3
```

**⚠️ KHÔNG dùng ARG/ENV cho secret:**

```dockerfile
# ❌ TUYỆT ĐỐI KHÔNG
ARG DB_PASSWORD
ENV DB_PASSWORD=${DB_PASSWORD}
# DB_PASSWORD sẽ hiện trong:
# - docker history
# - image manifest
# - layer cache
```

Dùng `--secret` của BuildKit cho secret (Chương 10).

### 8.4. Shell form vs Exec form (mở rộng)

```dockerfile
# Shell form:
RUN apt-get update && apt-get install -y curl
# Tương đương: /bin/sh -c "apt-get update && apt-get install -y curl"
# Hỗ trợ: pipe (|), redirect (>), variable ($VAR), && ||

# Exec form:
RUN ["apt-get", "install", "-y", "curl"]
# Chạy trực tiếp, KHÔNG qua shell
# Không hỗ trợ shell features
```

**Cho `RUN`**: Shell form thường tiện hơn (cần `&&`, `|`).
**Cho `CMD`/`ENTRYPOINT`**: **Luôn dùng exec form** cho signal handling đúng.

---

### ✅ TÓM TẮT CHƯƠNG 8

#### Decision matrix

| Câu hỏi                     | Trả lời                                   |
| ----------------------------- | ------------------------------------------- |
| Container nhiều purpose?     | CMD                                         |
| Container single-purpose CLI? | ENTRYPOINT + CMD (args)                     |
| Copy file local?              | COPY                                        |
| Tải file từ URL?            | RUN curl                                    |
| Variable lúc build?          | ARG                                         |
| Variable lúc runtime?        | ENV                                         |
| Secret?                       | KHÔNG dùng ARG/ENV, dùng BuildKit secret |
| Shell pipe trong RUN?         | Shell form                                  |
| CMD/ENTRYPOINT?               | Exec form (cho signal handling)             |

---

## 📖 CHƯƠNG 9: VIẾT DOCKERFILE THỰC TẾ

### 9.1. Dockerfile cho Python script đơn giản

**File: `app.py`**

```python
import sys
import platform

def main():
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Args: {sys.argv[1:]}")

if __name__ == "__main__":
    main()
```

**File: `Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY app.py .

CMD ["python", "app.py"]
```

**Build và chạy:**

```bash
docker build -t simple-py .
docker run --rm simple-py
docker run --rm simple-py arg1 arg2   # CMD bị override, không chạy
# → Sửa thành ENTRYPOINT để arg1 arg2 được forward:
```

**Dockerfile cải tiến (dùng ENTRYPOINT):**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
ENTRYPOINT ["python", "app.py"]
```

```bash
docker run --rm simple-py arg1 arg2
# → python app.py arg1 arg2
```

### 9.2. Dockerfile cho Python ETL job (production-grade)

**Cấu trúc project:**

```
etl/
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── etl/
│   ├── __init__.py
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── main.py
└── config/
    └── settings.yaml
```

**File: `requirements.txt`**

```
pandas==2.1.4
psycopg2-binary==2.9.9
sqlalchemy==2.0.25
pyyaml==6.0.1
boto3==1.34.0
```

**File: `.dockerignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.git/
.venv/
*.log
.env
tests/
docs/
```

**File: `Dockerfile`**

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base

# Best practices env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System packages (chỉ cài cái cần)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Tạo user không phải root (security)
RUN groupadd -r etl && useradd -r -g etl -d /app -s /sbin/nologin etl

WORKDIR /app

# Copy requirements TRƯỚC code (cache-friendly)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY etl/ ./etl/
COPY config/ ./config/

# Đổi quyền sở hữu
RUN chown -R etl:etl /app

USER etl

# Default command
ENTRYPOINT ["python", "-m", "etl.main"]
CMD ["--mode=daily"]
```

**Build và chạy:**

```bash
docker build -t etl-job:v1.0 .
docker run --rm \
  -e DB_HOST=postgres \
  -e DB_PASSWORD=secret \
  etl-job:v1.0 --mode=hourly
```

### 9.3. Dockerfile cho FastAPI service

**File: `main.py`**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"hello": "world"}
```

**File: `requirements.txt`**

```
fastapi==0.108.0
uvicorn[standard]==0.25.0
```

**File: `Dockerfile`**

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Tạo user non-root
RUN groupadd -r app && useradd -r -g app app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Test:**

```bash
docker build -t fastapi-demo .
docker run -d -p 8000:8000 --name api fastapi-demo
curl http://localhost:8000/health
docker ps   # Sẽ thấy "(healthy)"
docker rm -f api
```

### 9.4. Dockerfile cho dbt project

**Cấu trúc project:**

```
dbt-project/
├── Dockerfile
├── profiles.yml
├── dbt_project.yml
├── models/
│   └── ...
└── requirements.txt
```

**File: `requirements.txt`**

```
dbt-core==1.7.4
dbt-postgres==1.7.4
```

**File: `Dockerfile`**

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DBT_PROFILES_DIR=/app/profiles

WORKDIR /app

# dbt cần git để fetch packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy dbt project
COPY . .

# Install dbt packages (nếu có packages.yml)
RUN if [ -f packages.yml ]; then dbt deps; fi

ENTRYPOINT ["dbt"]
CMD ["run"]
```

**Chạy:**

```bash
docker build -t dbt-project .
docker run --rm \
  --network=data-net \
  -e DBT_HOST=postgres \
  -e DBT_PASSWORD=secret \
  dbt-project run

# Hoặc chạy lệnh khác:
docker run --rm dbt-project test
docker run --rm dbt-project docs generate
```

### 9.5. Dockerfile cho Spark job

Spark cần Java → image lớn hơn.

**File: `Dockerfile`**

```dockerfile
FROM apache/spark:3.5.0-python3

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài Python packages
USER root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy job code
COPY jobs/ ./jobs/

USER spark

# Default: chạy 1 job cụ thể
CMD ["/opt/spark/bin/spark-submit", \
     "--master", "local[*]", \
     "/app/jobs/my_job.py"]
```

---

### ✅ TÓM TẮT CHƯƠNG 9

#### Template Dockerfile cho Python Data Engineer

```dockerfile
# 1. Base image
FROM python:3.11-slim AS base

# 2. ENV settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 3. System packages (nếu cần)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 && \
    rm -rf /var/lib/apt/lists/*

# 4. Working dir
WORKDIR /app

# 5. Dependencies (TRƯỚC code, cache-friendly)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 6. Application code (SAU dependencies)
COPY . .

# 7. Non-root user
RUN useradd -r app && chown -R app:app /app
USER app

# 8. Health check
HEALTHCHECK CMD python -c "..." || exit 1

# 9. Entrypoint/CMD
ENTRYPOINT ["python", "-m", "myapp"]
CMD ["--default-args"]
```

#### Checklist Dockerfile chuẩn

- [ ] Pin version base image (`python:3.11-slim`, KHÔNG `python:latest`)
- [ ] Set `PYTHONUNBUFFERED=1` cho Python
- [ ] Combine `RUN` để giảm layer
- [ ] Cleanup apt cache (`rm -rf /var/lib/apt/lists/*`)
- [ ] Copy `requirements.txt` TRƯỚC code
- [ ] Có `.dockerignore`
- [ ] Chạy non-root user
- [ ] Healthcheck cho long-running service
- [ ] Exec form cho CMD/ENTRYPOINT
- [ ] Không có secret trong Dockerfile/ENV
- [ ] Có LABEL metadata
- [ ] Reproducible (pin tất cả version)

---

## 📖 CHƯƠNG 10: TỐI ƯU DOCKERFILE

### 10.1. Layer caching — Hiểu sâu

Docker cache mỗi layer dựa trên:

1. **Instruction text** (chính xác từng ký tự).
2. **Files được COPY/ADD** (nội dung và metadata).

Nếu instruction và inputs không đổi → reuse layer cache → build nhanh.

**Nếu instruction A đổi → tất cả layer SAU A bị invalidate.**

#### Pattern sai (cache không tốt):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .                              # Layer 3: copy tất cả code + requirements
RUN pip install -r requirements.txt   # Layer 4: install dependencies
```

**Vấn đề:** Đổi 1 dòng code → Layer 3 invalidate → Layer 4 phải rebuild → `pip install` lại từ đầu (có thể mất 5-10 phút).

#### Pattern đúng (cache tốt):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .               # Layer 3: chỉ copy requirements
RUN pip install -r requirements.txt   # Layer 4: install
COPY . .                              # Layer 5: copy code
```

**Lợi ích:** Đổi code → chỉ Layer 5 rebuild. `pip install` được cache, build sau vài giây.

**Nguyên tắc vàng:** **Sắp xếp instruction từ ít thay đổi → nhiều thay đổi.**

```
FROM (rất hiếm đổi)
↓
ENV, ARG (ít đổi)
↓
RUN apt-get install (ít đổi)
↓
COPY requirements.txt + RUN pip install (ít đổi)
↓
COPY . . (đổi mỗi commit)
```

### 10.2. `.dockerignore` — Giảm build context

```
# .dockerignore
**/__pycache__
**/*.pyc
.git/
.venv/
node_modules/
*.log
.env
.DS_Store
.idea/
.vscode/
tests/
docs/
*.md
Dockerfile*
.dockerignore
```

**Đo lường:**

```bash
docker build -t myapp .
# Khi build, sẽ thấy:
# [+] Building 0.5s (10/10) FINISHED
# => transferring context: 1.2MB    ← Nếu thấy >100MB là có vấn đề
```

### 10.3. Multi-stage build — Giảm image size

**Vấn đề:** Build cần compiler/tools (gcc, build-essential), nhưng runtime không cần. Image production không nên có những thứ này.

**Giải pháp:** Multi-stage build — build trong 1 stage, copy artifact sang stage gọn.

#### Ví dụ Python với C extensions

```dockerfile
# Stage 1: Builder
FROM python:3.11 AS builder

WORKDIR /build

# Cài build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev

# Build wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime (gọn)
FROM python:3.11-slim

# Chỉ cài runtime libs (libpq5), không cần dev (libpq-dev) hay gcc
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy wheels từ builder, install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY . .

CMD ["python", "main.py"]
```

**Kết quả:**

- Image builder ~1.5GB (có gcc, dev libs)
- Image runtime ~250MB (chỉ có Python + libs runtime)
- → Production chỉ deploy 250MB

#### Ví dụ Go binary

```dockerfile
# Stage 1: Build
FROM golang:1.21 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app

# Stage 2: Distroless (cực gọn)
FROM gcr.io/distroless/static
COPY --from=builder /app /app
CMD ["/app"]
```

Image cuối < 10MB.

### 10.4. Slim, Alpine, Distroless — Chọn loại nào?

| Loại                                                | Size   | Pros                        | Cons                      |
| ---------------------------------------------------- | ------ | --------------------------- | ------------------------- |
| **Full** (`python:3.11`)                     | ~1GB   | Đủ tool, dễ debug        | Nặng                     |
| **Slim** (`python:3.11-slim`)                | ~150MB | Cân bằng tốt             | Cần`apt install` thêm |
| **Alpine** (`python:3.11-alpine`)            | ~50MB  | Cực nhỏ                   | musl libc, compile chậm  |
| **Distroless** (`gcr.io/distroless/python3`) | ~50MB  | Bảo mật max, không shell | Khó debug                |
| **Scratch**                                    | 0MB    | Tối thiểu                 | Chỉ cho static binary    |

**Khuyến nghị cho Data Engineer:**

- **Dev/test:** `slim` — dễ debug
- **Production app:** `slim` — balance tốt
- **Production cực bảo mật:** `distroless`
- **Avoid Alpine với Python** vì compile pandas/numpy chậm

### 10.5. BuildKit — Build engine thế hệ mới

BuildKit là build engine mới của Docker (mặc định từ Docker 23+). Tính năng nổi bật:

- Parallel layer building
- Cache mount (`--mount=type=cache`)
- Secret mount (`--mount=type=secret`)
- SBOM generation
- Multi-platform build

#### Cache mount cho pip

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

# Cache pip downloads giữa các lần build
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

**Hiệu quả:** Lần build sau, dù invalidate layer này, pip không phải tải lại packages (đã ở cache).

#### Secret mount cho build-time secret

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

# Dùng SSH key để clone private repo, KHÔNG lưu vào image
RUN --mount=type=secret,id=github_token \
    TOKEN=$(cat /run/secrets/github_token) && \
    git clone https://$TOKEN@github.com/myorg/private-repo.git
```

Build:

```bash
docker build --secret id=github_token,src=$HOME/.github_token -t myapp .
```

Secret **KHÔNG bị lưu vào image layer**.

### 10.6. Pin dependencies

```dockerfile
FROM python:3.11.7-slim     # Pin patch version
```

```
# requirements.txt - dùng pip-compile để lock đầy đủ
pandas==2.1.4
psycopg2-binary==2.9.9
# ... tất cả dependencies với version chính xác
```

Hoặc dùng `pip freeze > requirements.txt` từ môi trường đã test, hoặc `pip-tools`:

```bash
# requirements.in
pandas
psycopg2-binary

# Compile thành requirements.txt với pin
pip-compile requirements.in
```

### 10.7. Reproducible build

```dockerfile
# Pin base image bằng digest
FROM python:3.11.7-slim@sha256:abc123def456...

# Pin packages OS
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5=15.4-0+deb12u1 && \
    rm -rf /var/lib/apt/lists/*
```

### 10.8. Security best practices

#### Non-root user

```dockerfile
RUN groupadd -r app && useradd -r -g app app
USER app
```

#### Đừng leak secret

❌ KHÔNG:

```dockerfile
ENV DB_PASSWORD=secret123
ARG API_KEY
```

✅ DÙNG:

- Runtime env: `docker run -e DB_PASSWORD=secret`
- Build secret: BuildKit `--mount=type=secret`

#### Scan vulnerabilities

```bash
docker scout cves myapp:v1.0       # Docker Scout
trivy image myapp:v1.0             # Trivy (popular open-source)
grype myapp:v1.0                   # Grype
```

#### Read-only filesystem

```bash
docker run --read-only --tmpfs /tmp myapp
```

#### Drop capabilities

```bash
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp
```

### 10.9. Dockerfile production-ready hoàn chỉnh

```dockerfile
# syntax=docker/dockerfile:1.6
ARG PYTHON_VERSION=3.11.7

# ============ Stage 1: Builder ============
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir /wheels -r requirements.txt

# ============ Stage 2: Runtime ============
FROM python:${PYTHON_VERSION}-slim

ARG APP_VERSION=dev
ARG GIT_SHA=unknown

LABEL org.opencontainers.image.title="ETL Job" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      org.opencontainers.image.source="https://github.com/myorg/etl"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION} \
    GIT_SHA=${GIT_SHA}

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates \
        tini && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r etl && useradd -r -g etl -d /app -s /sbin/nologin etl

WORKDIR /app

# Install from wheels (no compile)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy code
COPY --chown=etl:etl . .

USER etl

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import etl; etl.healthcheck()" || exit 1

# Use tini as PID 1 for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--", "python", "-m", "etl"]
CMD ["--mode=daily"]
```

---

### ✅ TÓM TẮT CHƯƠNG 10

#### Checklist tối ưu Dockerfile

**Size:**

- [ ] Dùng slim/distroless base image
- [ ] Multi-stage build
- [ ] Cleanup apt cache (`rm -rf /var/lib/apt/lists/*`)
- [ ] Combine RUN instructions

**Speed:**

- [ ] `.dockerignore` (build context nhỏ)
- [ ] COPY requirements trước code
- [ ] BuildKit cache mount cho pip/apt

**Security:**

- [ ] Non-root user
- [ ] Pin version (tag + digest cho production)
- [ ] Không hardcode secret
- [ ] Scan vulnerabilities định kỳ
- [ ] Drop unnecessary capabilities

**Reproducibility:**

- [ ] Pin tất cả version (base image, packages, deps)
- [ ] Có LABEL metadata (version, git SHA)
- [ ] CI/CD build deterministic

#### Câu hỏi tự kiểm tra

1. Vì sao COPY requirements.txt trước COPY . . ?
2. Multi-stage build giảm size như thế nào?
3. Khi nào nên dùng Alpine? Khi nào KHÔNG?
4. BuildKit cache mount khác layer cache như thế nào?
5. Vì sao không nên ENV DB_PASSWORD=...?

#### Bài tập thực hành

**Bài tập tổng hợp:** Build 1 Python ETL image production-ready, đo size, scan vulnerabilities:

```bash
# Build
docker build -t etl:v1 .

# Đo size
docker images etl
docker history etl:v1

# Scan
docker scout cves etl:v1
# Hoặc: trivy image etl:v1

# So sánh với base image full vs slim
```

---

## 🎯 KẾT THÚC PHẦN 3

Bạn đã master Dockerfile từ cơ bản đến production-ready. Tiếp theo: **Phần 4 — Volume & Data**.

---

# 📘 PHẦN 4: VOLUME, BIND MOUNT VÀ DỮ LIỆU

> *"Mọi data trong container đều ephemeral. Nếu bạn không học volume, sớm muộn bạn sẽ mất database production."*

---

## 📖 CHƯƠNG 11: EPHEMERAL FILESYSTEM VÀ CÁC LOẠI MOUNT

### 11.1. Container filesystem là ephemeral — Bằng chứng

```bash
docker run -d --name pgtest -e POSTGRES_PASSWORD=secret postgres:15
docker exec pgtest psql -U postgres -c "CREATE TABLE test(id INT);"
docker exec pgtest psql -U postgres -c "INSERT INTO test VALUES (1), (2), (3);"
docker exec pgtest psql -U postgres -c "SELECT * FROM test;"
# Thấy 3 dòng

# Bây giờ "xóa" container
docker rm -f pgtest

# Tạo lại
docker run -d --name pgtest -e POSTGRES_PASSWORD=secret postgres:15
docker exec pgtest psql -U postgres -c "SELECT * FROM test;"
# ERROR: relation "test" does not exist
# → Data đã MẤT
```

**Vì sao?**

- Container có **writable layer** trên top of image layers.
- `docker rm` xóa writable layer → mọi thay đổi mất.

**Giải pháp:** Volume — lưu data ngoài lifecycle container.

### 11.2. Ba loại mount

#### a) Named Volume (Docker quản lý)

```bash
docker volume create pgdata
docker run -d --name pg -v pgdata:/var/lib/postgresql/data postgres:15
```

- Docker tạo + quản lý storage (`/var/lib/docker/volumes/pgdata/_data` trên Linux).
- Bạn không quan tâm path thật.
- Tốt cho **database**, data persistent giữa container restart.

#### b) Bind Mount (Mount thư mục host)

```bash
docker run -v $(pwd)/code:/app python:3.11 python /app/main.py
```

- Mount thư mục host vào container.
- Thay đổi file ở host → container thấy ngay (và ngược lại).
- Tốt cho **development** (live reload), **share config**.

#### c) tmpfs Mount (RAM)

```bash
docker run --tmpfs /tmp myapp
docker run --mount type=tmpfs,destination=/cache,tmpfs-size=100m myapp
```

- Lưu vào RAM, không lưu đĩa.
- Mất khi container dừng.
- Tốt cho data **nhạy cảm** (key tạm) hoặc **tăng tốc IO** (cache tạm).

### 11.3. Cú pháp `-v` vs `--mount`

```bash
# -v / --volume (cú pháp cũ, gọn)
docker run -v pgdata:/var/lib/postgresql/data postgres
docker run -v $(pwd):/app:ro python

# --mount (cú pháp mới, rõ ràng hơn)
docker run --mount type=volume,source=pgdata,target=/var/lib/postgresql/data postgres
docker run --mount type=bind,source=$(pwd),target=/app,readonly python
docker run --mount type=tmpfs,target=/tmp postgres
```

**Khuyến nghị:** Dùng `--mount` cho production (rõ ràng, ít lỗi). Dùng `-v` cho ad-hoc.

### 11.4. Khi nào dùng cái nào?

| Use case                           | Loại mount            |
| ---------------------------------- | ---------------------- |
| Database data (Postgres, MySQL...) | Named volume           |
| Persistent app state               | Named volume           |
| Dev code (live edit)               | Bind mount             |
| Config file từ host               | Bind mount (read-only) |
| Shared data giữa container        | Named volume           |
| Cache tạm, không cần persistent | tmpfs                  |
| Secret tạm                        | tmpfs                  |
| Log output muốn xem từ host      | Bind mount             |

### 11.5. Permission issues — Lỗi kinh điển

**Vấn đề:** Container chạy root → ghi file ra bind mount → file ở host thuộc root → bạn (user thường) không xóa/sửa được.

**Demo:**

```bash
mkdir output
docker run --rm -v $(pwd)/output:/data alpine sh -c "echo 'hello' > /data/file.txt"
ls -la output/
# -rw-r--r--  1 root  root  6 May 18 10:00 file.txt
rm output/file.txt
# rm: Permission denied
```

**Cách fix:**

**Cách 1:** Chạy container với UID của bạn:

```bash
docker run --rm -u $(id -u):$(id -g) -v $(pwd)/output:/data alpine sh -c "echo 'hello' > /data/file.txt"
ls -la output/
# -rw-r--r--  1 user  user  6 May 18 10:00 file.txt
```

**Cách 2:** Tạo user trong Dockerfile khớp UID host:

```dockerfile
RUN groupadd -g 1000 app && useradd -u 1000 -g app -m app
USER app
```

**Cách 3:** Dùng named volume (Docker quản lý permission tự động).

### 11.6. Demo: PostgreSQL với volume

```bash
# Tạo volume
docker volume create pgdata

# Chạy Postgres với volume
docker run -d --name pg \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15

# Tạo data
docker exec pg psql -U postgres -c "CREATE TABLE test(id INT); INSERT INTO test VALUES (1),(2),(3);"

# Stop và xóa container
docker rm -f pg

# Tạo container mới với CÙNG volume
docker run -d --name pg \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15

# Data còn nguyên!
docker exec pg psql -U postgres -c "SELECT * FROM test;"
# 1
# 2
# 3
```

### 11.7. Backup/Restore volume

#### Backup

```bash
docker run --rm \
  -v pgdata:/source:ro \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/pgdata-$(date +%Y%m%d).tar.gz -C /source .
```

#### Restore

```bash
docker volume create pgdata-new
docker run --rm \
  -v pgdata-new:/target \
  -v $(pwd):/backup \
  alpine \
  sh -c "cd /target && tar xzf /backup/pgdata-20240518.tar.gz"
```

#### Backup PostgreSQL bằng `pg_dump` (chuẩn hơn):

```bash
docker exec pg pg_dump -U postgres mydb > backup.sql
# Restore:
docker exec -i pg psql -U postgres mydb < backup.sql
```

### 11.8. Mount file đơn lẻ

```bash
docker run -v $(pwd)/config.yaml:/app/config.yaml:ro myapp
```

**Pitfall:** Nếu host file không tồn tại, Docker tạo **thư mục** thay vì file → app bug.

### 11.9. Volume drivers (nâng cao)

Mặc định: `local` driver — lưu trên disk host.

Có thể dùng driver khác:

- `nfs` — NFS share
- `cifs` — Windows/Samba
- Cloud (AWS EBS, GCP PD) qua plugin
- Storage solution khác (GlusterFS, Ceph)

```bash
docker volume create --driver=local \
  --opt type=nfs \
  --opt o=addr=nfs-server,rw \
  --opt device=:/exports/data \
  nfs-volume
```

---

### ✅ TÓM TẮT CHƯƠNG 11

| Loại mount  | Use case           | Persistent? | Performance                | Quản lý |
| ------------ | ------------------ | ----------- | -------------------------- | --------- |
| Named volume | DB data, app state | ✅          | ⭐⭐⭐                     | Docker    |
| Bind mount   | Dev, config, log   | ✅          | ⭐⭐ (chậm trên Mac/Win) | User      |
| tmpfs        | Cache, secret tạm | ❌          | ⭐⭐⭐⭐⭐                 | RAM       |

#### Best Practices

- ✅ Database → Named volume (đừng bind mount Postgres data dir)
- ✅ Dev code → Bind mount với `:ro` cho file không cần ghi
- ✅ Production secret tạm → tmpfs
- ✅ Backup volume định kỳ
- ❌ Đừng để container ghi vào filesystem của container (không persistent)
- ❌ Đừng dùng bind mount Postgres data trên Mac/Windows (chậm + permission issues)

---

## 📖 CHƯƠNG 12: QUẢN LÝ DỮ LIỆU DATABASE TRONG DOCKER

### 12.1. PostgreSQL — Setup chuẩn

```bash
docker volume create pgdata
docker run -d --name postgres \
  --restart=unless-stopped \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=mydb \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15.4
```

**Các env quan trọng:**

- `POSTGRES_USER` (default `postgres`)
- `POSTGRES_PASSWORD` (BẮT BUỘC nếu không dùng trust auth)
- `POSTGRES_DB` (default = `POSTGRES_USER`)
- `PGDATA` — sub-directory trong volume (tránh "lost+found")

### 12.2. Init script

Image `postgres` chạy tất cả file `.sh`, `.sql`, `.sql.gz` trong `/docker-entrypoint-initdb.d/` **lần đầu khởi tạo** (volume rỗng).

```bash
mkdir initdb
cat > initdb/01_create_tables.sql <<EOF
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (email) VALUES ('alice@example.com'), ('bob@example.com');
EOF

cat > initdb/02_setup.sh <<EOF
#!/bin/bash
psql -U \$POSTGRES_USER -d \$POSTGRES_DB -c "CREATE INDEX ON users(email);"
EOF
chmod +x initdb/02_setup.sh

docker run -d --name pg-init \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata-new:/var/lib/postgresql/data \
  -v $(pwd)/initdb:/docker-entrypoint-initdb.d:ro \
  postgres:15

# Đợi init xong
docker logs -f pg-init
# Đợi đến khi thấy "database system is ready to accept connections"
```

**Lưu ý:** Init script CHỈ chạy khi volume **rỗng**. Nếu đã có data, init bị bỏ qua.

### 12.3. Backup/Restore PostgreSQL

#### Logical backup (pg_dump)

```bash
# Dump 1 database
docker exec postgres pg_dump -U admin mydb > mydb-$(date +%Y%m%d).sql

# Dump toàn bộ cluster
docker exec postgres pg_dumpall -U admin > cluster-$(date +%Y%m%d).sql

# Dump theo format custom (nén, restore parallel)
docker exec postgres pg_dump -U admin -Fc mydb > mydb.dump

# Restore
cat mydb.sql | docker exec -i postgres psql -U admin mydb
docker exec -i postgres pg_restore -U admin -d mydb < mydb.dump
```

#### Physical backup (file-level)

```bash
# Stop container, backup volume
docker stop postgres
docker run --rm \
  -v pgdata:/source:ro \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/pgdata-$(date +%Y%m%d).tar.gz -C /source .
docker start postgres
```

### 12.4. Tuning cơ bản

Postgres mặc định cấu hình rất conservative. Cho dev/test có thể tăng:

```bash
docker run -d --name pg-tuned \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  postgres:15 \
  postgres \
    -c shared_buffers=256MB \
    -c max_connections=200 \
    -c work_mem=16MB
```

Hoặc mount file `postgresql.conf` tùy biến:

```bash
docker run -d --name pg \
  -v pgdata:/var/lib/postgresql/data \
  -v $(pwd)/postgresql.conf:/etc/postgresql/postgresql.conf:ro \
  postgres:15 \
  postgres -c config_file=/etc/postgresql/postgresql.conf
```

### 12.5. MySQL — Setup

```bash
docker run -d --name mysql \
  -e MYSQL_ROOT_PASSWORD=secret \
  -e MYSQL_DATABASE=mydb \
  -e MYSQL_USER=admin \
  -e MYSQL_PASSWORD=adminpass \
  -v mysqldata:/var/lib/mysql \
  -p 3306:3306 \
  mysql:8.2

docker exec -it mysql mysql -u admin -p mydb
```

Init script: `/docker-entrypoint-initdb.d/` (giống Postgres).

Backup:

```bash
docker exec mysql mysqldump -u admin -padminpass mydb > mydb.sql
```

### 12.6. Database container — Dev/test vs Production

|                   | Dev/Test        | Production                                          |
| ----------------- | --------------- | --------------------------------------------------- |
| Run trong Docker? | ✅              | ⚠️ Cẩn trọng                                    |
| Resource limit    | Thấp           | Cao                                                 |
| Persistence       | Named volume OK | Managed service (RDS, Cloud SQL) thường tốt hơn |
| HA/Replication    | Không cần     | Cần                                                |
| Backup automation | Manual OK       | BẮT BUỘC                                          |

**Khuyến nghị production:**

- DB nhỏ, không critical → Docker với volume + backup script + monitoring.
- DB lớn, critical → managed service (AWS RDS, GCP Cloud SQL, Azure DB) — đỡ phải lo HA, backup, failover.

### 12.7. Common errors

| Lỗi                                          | Nguyên nhân           | Fix                                    |
| --------------------------------------------- | ----------------------- | -------------------------------------- |
| `password authentication failed`            | Sai password            | Check env, hoặc xóa volume tạo lại |
| `database "X" does not exist`               | DB chưa được tạo   | Set`POSTGRES_DB=X` hoặc init script |
| Init script không chạy                      | Volume đã có data    | Xóa volume tạo lại                  |
| Container exit code 1                         | Permission issue        | Check ownership volume                 |
| `could not access /var/lib/postgresql/data` | Bind mount + permission | Dùng named volume                     |

---

### ✅ TÓM TẮT CHƯƠNG 12

#### Checklist database trong Docker

- [ ] Named volume cho data (không bind mount)
- [ ] Pin version cụ thể
- [ ] Set strong password (KHÔNG hardcode)
- [ ] Init script idempotent
- [ ] Backup automation (cron + retention policy)
- [ ] Monitoring (`pg_isready`, health check)
- [ ] Resource limit (`--memory`)
- [ ] `restart=unless-stopped`

#### Bài tập

**Bài 1:** Setup Postgres với init script và test data persistence:

```bash
mkdir initdb
echo "CREATE TABLE t1(id INT); INSERT INTO t1 VALUES(1),(2),(3);" > initdb/01.sql

docker volume create testdb
docker run -d --name pg \
  -e POSTGRES_PASSWORD=secret \
  -v testdb:/var/lib/postgresql/data \
  -v $(pwd)/initdb:/docker-entrypoint-initdb.d:ro \
  postgres:15

sleep 5
docker exec pg psql -U postgres -c "SELECT * FROM t1;"
docker rm -f pg

# Tái tạo container, data còn?
docker run -d --name pg \
  -e POSTGRES_PASSWORD=secret \
  -v testdb:/var/lib/postgresql/data \
  postgres:15
sleep 3
docker exec pg psql -U postgres -c "SELECT * FROM t1;"
```

**Bài 2:** Backup + restore:

```bash
docker exec pg pg_dump -U postgres postgres > backup.sql
cat backup.sql

# Tạo container mới + restore
docker rm -f pg
docker volume rm testdb
docker volume create testdb
docker run -d --name pg \
  -e POSTGRES_PASSWORD=secret \
  -v testdb:/var/lib/postgresql/data \
  postgres:15
sleep 5
cat backup.sql | docker exec -i pg psql -U postgres
docker exec pg psql -U postgres -c "SELECT * FROM t1;"
```

---

## 🎯 KẾT THÚC PHẦN 4

Tiếp theo: **Phần 5 — Docker Networking**.

---

# 📘 PHẦN 5: DOCKER NETWORKING

> *Network là chỗ developer Docker bị "vấp" nhiều nhất. Hiểu sai network = pipeline không chạy được. Hiểu đúng = debug 5 giây.*

---

## 📖 CHƯƠNG 13: CÁC LOẠI NETWORK VÀ CƠ CHẾ HOẠT ĐỘNG

### 13.1. Bridge network — Default

Khi cài Docker, một bridge `docker0` được tạo trên host:

```bash
ip addr show docker0
# 3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500
#     inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
```

Đây là một virtual switch. Mọi container không chỉ định network sẽ gắn vào bridge này.

#### Cơ chế:

1. Container có **network namespace** riêng (Chương 3).
2. Docker tạo **veth pair** (cặp interface ảo).
3. Một đầu vào namespace container (thành `eth0`).
4. Đầu kia gắn vào bridge `docker0` trên host.
5. Container có IP trong subnet `172.17.0.0/16`.

```
Host                                          Container
┌─────────────────────────────────┐    ┌──────────────────────┐
│          docker0 (172.17.0.1)   │    │                      │
│              │                   │    │   eth0 (172.17.0.2)  │
│              ├──veth0──────veth1┼────┤        │              │
│              │                   │    │        app:80        │
└─────────────────────────────────┘    └──────────────────────┘
```

#### Default bridge vs Custom bridge

**Default bridge (`bridge`)** có nhược điểm:

- Container không thể gọi nhau bằng tên (chỉ IP).
- Cô lập kém.

**Custom bridge** (khuyến nghị):

```bash
docker network create mynet
docker run -d --name web --network=mynet nginx
docker run -d --name db --network=mynet postgres

# Container web có thể ping db bằng tên!
docker exec web ping db
# 64 bytes from db.mynet (172.18.0.3): icmp_seq=1 ...
```

→ **Luôn dùng custom bridge** thay default.

### 13.2. Host network (Linux only)

```bash
docker run -d --network=host nginx
```

Container **không** có network namespace riêng — dùng chung với host.

- App nghe port 80 trong container = port 80 trên host.
- Không cần `-p`.
- Nhanh hơn bridge (không qua NAT).

**Nhược điểm:**

- Mất isolation.
- Conflict port với host.
- Không hỗ trợ trên Docker Desktop (Mac/Win).

**Use case:** Performance-critical, monitoring agent, một số protocol đặc biệt.

### 13.3. None network

```bash
docker run --network=none alpine
```

Container không có network. Chỉ có `lo` (loopback). Hữu ích cho batch job không cần network, hoặc bảo mật max.

### 13.4. Overlay network

Cho multi-host (Docker Swarm, Kubernetes dùng cơ chế khác). Container ở host A có thể nói với container ở host B như cùng mạng.

```bash
docker swarm init   # Khởi tạo Swarm
docker network create --driver=overlay myoverlay
```

Ít dùng trực tiếp ngoài Swarm. Kubernetes có CNI plugin riêng.

### 13.5. Port mapping — `-p`

```bash
docker run -p 8080:80 nginx
#               ^   ^
#               |   +-- container port (80, nơi nginx nghe)
#               +------ host port (8080, từ host truy cập)
```

**Bản chất:** Docker tạo iptables NAT rule:

```bash
sudo iptables -t nat -L DOCKER
# DNAT       tcp  --  anywhere    anywhere   tcp dpt:8080 to:172.17.0.2:80
```

#### Bind chỉ localhost (an toàn):

```bash
docker run -p 127.0.0.1:8080:80 nginx
# Chỉ host truy cập được, không expose ra mạng ngoài
```

#### Port ngẫu nhiên:

```bash
docker run -p 80 nginx       # Docker chọn host port ngẫu nhiên
docker port <container>      # Xem mapping
```

### 13.6. DNS nội bộ và service discovery

Trong custom bridge, container có **DNS resolver nội bộ** map service name → IP.

```bash
docker network create datanet
docker run -d --name postgres --network=datanet -e POSTGRES_PASSWORD=s postgres:15
docker run -d --name app --network=datanet myapp

# Trong container app:
docker exec app cat /etc/resolv.conf
# nameserver 127.0.0.11   <- Docker DNS embedded

docker exec app nslookup postgres
# Server: 127.0.0.11
# Address: 172.18.0.2
```

→ App config: `DB_HOST=postgres` (KHÔNG dùng `localhost`, KHÔNG dùng IP).

### 13.7. Container alias

```bash
docker run -d --name pg-primary --network=datanet \
  --network-alias=postgres \
  --network-alias=primary-db \
  postgres:15
```

Container có nhiều tên gọi → dễ migration (đổi container thật mà alias không đổi).

### 13.8. Connect/disconnect runtime

```bash
docker network connect mynet existing-container
docker network disconnect mynet existing-container
```

Container có thể gắn vào nhiều network cùng lúc.

---

### ✅ TÓM TẮT CHƯƠNG 13

| Loại          | Use case                     | Performance | Isolation     |
| -------------- | ---------------------------- | ----------- | ------------- |
| Custom bridge  | Default cho mọi project     | Tốt        | Tốt          |
| Default bridge | Cũ, tránh dùng            | Tốt        | Yếu (no DNS) |
| Host           | Performance-critical (Linux) | Best        | Không        |
| None           | Batch job, security max      | N/A         | Max           |
| Overlay        | Multi-host                   | OK          | Tốt          |

---

## 📖 CHƯƠNG 14: SERVICE DISCOVERY, DNS, DEBUG NETWORK

### 14.1. Localhost trong container nghĩa là gì?

**Đây là source of confusion lớn nhất với người mới.**

```python
# Trong container app
import psycopg2
conn = psycopg2.connect(host="localhost", port=5432, ...)
# ❌ ERROR: Connection refused
```

**Vì sao?** `localhost` trong container = network namespace của container, **không phải host machine**. Postgres chạy ngoài container thì container không truy cập được qua `localhost`.

#### Giải pháp:

**A) Container đến container (cùng network):** Dùng service name.

```python
conn = psycopg2.connect(host="postgres", port=5432, ...)
```

**B) Container đến service trên host:**

```python
# Linux:
conn = psycopg2.connect(host="172.17.0.1", port=5432, ...)  # IP của docker0
# Hoặc với --network=host

# Mac/Win:
conn = psycopg2.connect(host="host.docker.internal", port=5432, ...)
# Linux (Docker 20.10+):
docker run --add-host=host.docker.internal:host-gateway ...
```

### 14.2. Debug network — Toolkit

#### Bước 1: Container nào network nào?

```bash
docker inspect <container> | grep -A 20 NetworkSettings
docker network inspect <network>
```

#### Bước 2: Container có ping được nhau không?

```bash
docker exec app ping postgres
docker exec app nslookup postgres
docker exec app getent hosts postgres
```

#### Bước 3: Port có mở không?

```bash
# Cài netcat/curl trong container
docker exec app nc -zv postgres 5432
docker exec app curl -v telnet://postgres:5432
```

#### Bước 4: Routing

```bash
docker exec app ip route
docker exec app traceroute postgres
```

#### Container debug toolbox

Tạo image với đầy đủ tool debug:

```dockerfile
FROM alpine:3.19
RUN apk add --no-cache curl netcat-openbsd bind-tools iputils busybox-extras tcpdump
CMD ["sh"]
```

```bash
docker build -t debug-tools .
docker run --rm -it --network=mynet debug-tools
# Trong container, dùng curl, nslookup, ping, tcpdump...
```

Hoặc dùng image có sẵn: `nicolaka/netshoot`.

```bash
docker run --rm -it --network=mynet nicolaka/netshoot
```

### 14.3. Debug case study: "App không kết nối được DB"

**Triệu chứng:**

```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Quy trình debug:**

```bash
# 1. App container có thấy DB container?
docker exec app ping db
# ✅ Reachable? → bug ở app config
# ❌ Unknown host? → cùng network không?

# 2. Cùng network không?
docker inspect app | jq '.[0].NetworkSettings.Networks'
docker inspect db | jq '.[0].NetworkSettings.Networks'

# Cả 2 phải cùng network. Nếu không:
docker network connect mynet app
docker network connect mynet db

# 3. DB có nghe đúng port không?
docker exec db ss -tlnp
# Hoặc:
docker exec db netstat -tlnp

# 4. Test connection từ app container:
docker exec app nc -zv db 5432
# Connection refused → DB chưa ready
# Time out → firewall hoặc DB không nghe interface đó

# 5. DB binding địa chỉ nào?
# Postgres default: chỉ listen 127.0.0.1
# Cần POSTGRES_HOST_AUTH_METHOD và config cho phép external
```

### 14.4. iptables interference

Docker manage iptables để NAT cho port mapping. Đôi khi xung đột với firewall.

```bash
sudo iptables -L DOCKER
sudo iptables -t nat -L DOCKER
```

Nếu có firewall (ufw, firewalld) → có thể chặn traffic. Cần config riêng (xem docs Docker).

### 14.5. Docker Compose networking

Khi dùng Compose:

```yaml
services:
  app:
    image: myapp
  db:
    image: postgres:15
```

Compose **tự tạo network mới** cho project. Service name = DNS name. Trong app:

```python
conn = psycopg2.connect(host="db", port=5432, ...)
```

Chi tiết ở Phần 6.

---

### ✅ TÓM TẮT CHƯƠNG 14

#### Network checklist cho Data pipeline

- [ ] Container cùng project → cùng custom network
- [ ] Dùng service name, KHÔNG dùng IP hay localhost
- [ ] Port mapping chỉ khi cần expose ra host
- [ ] Postgres listen trên `0.0.0.0` trong container OK (chỉ container network reach)
- [ ] Debug với `ping`, `nc`, `nslookup`

#### Câu hỏi tự kiểm tra

1. Vì sao `localhost` trong container không kết nối được DB chạy trên host?
2. Default bridge vs custom bridge khác nhau ở điểm nào?
3. Khi nào dùng `--network=host`?
4. Container nói chuyện qua service name dựa vào cơ chế gì?

#### Bài tập

**Bài 1:** Tạo network, chạy 2 container, ping nhau:

```bash
docker network create testnet
docker run -d --name srv1 --network=testnet nginx
docker run --rm -it --network=testnet alpine sh
# Trong container:
#   ping srv1
#   wget -qO- http://srv1
```

**Bài 2:** Test localhost trong container:

```bash
# Chạy app trên host, port 8000
python3 -m http.server 8000 &

# Container có truy cập được localhost host không?
docker run --rm alpine wget -qO- http://localhost:8000  # ❌ Fail
docker run --rm alpine wget -qO- http://host.docker.internal:8000  # Mac/Win
docker run --rm --network=host alpine wget -qO- http://localhost:8000  # Linux
```

---

## 🎯 KẾT THÚC PHẦN 5

Tiếp theo: **Phần 6 — Docker Compose**.

---

# 📘 PHẦN 6: DOCKER COMPOSE

> *Compose là công cụ Data Engineer dùng hàng ngày. Master Compose = đời sống dev local sướng gấp 10 lần.*

---

## 📖 CHƯƠNG 15: COMPOSE TỪ A-Z

### 15.1. Compose là gì?

**Docker Compose** là công cụ định nghĩa và chạy **multi-container application** qua một file YAML.

**Vấn đề mà Compose giải quyết:**

```bash
# Cách thủ công - phải nhớ thứ tự, args, network, volume...
docker network create datanet
docker volume create pgdata

docker run -d --name postgres --network=datanet \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:15

docker run -d --name app --network=datanet \
  -e DB_HOST=postgres -e DB_PASSWORD=secret \
  -p 8000:8000 \
  myapp:v1

docker run -d --name redis --network=datanet redis:7
# ... và nhiều container nữa
```

Mỗi lần restart cả stack: phải gõ lại. Onboard junior: phải copy script. Đổi config: phải sửa script.

**Với Compose:**

```yaml
# compose.yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data

  app:
    image: myapp:v1
    environment:
      DB_HOST: postgres
      DB_PASSWORD: secret
    ports:
      - "8000:8000"
    depends_on:
      - postgres

  redis:
    image: redis:7

volumes:
  pgdata:
```

```bash
docker compose up -d    # Lên cả stack
docker compose down     # Tắt cả stack
```

### 15.2. `docker compose` vs `docker-compose`

- **`docker-compose`** (cũ, v1, Python) — deprecated.
- **`docker compose`** (mới, v2, plugin Go) — chuẩn hiện nay.

Tài liệu này dùng `docker compose` (mới).

### 15.3. File `compose.yaml` — Cấu trúc

```yaml
# Top-level keys
name: my-project          # Tên project (default: tên thư mục)

services:
  # Định nghĩa các container
  service-name:
    # ... options
    ...

volumes:
  # Định nghĩa named volumes
  volume-name:
    ...

networks:
  # Định nghĩa networks
  network-name:
    ...

configs:
  # Static config files
  config-name:
    ...

secrets:
  # Secrets
  secret-name:
    ...
```

### 15.4. Tên file Compose

- `compose.yaml` / `compose.yml` — **chuẩn mới** (khuyến nghị)
- `docker-compose.yaml` / `docker-compose.yml` — cũ, vẫn nhận

Compose tự tìm theo thứ tự. Có thể override:

```bash
docker compose -f my-compose.yaml up
```

### 15.5. Các option của `services` — Chi tiết

#### `image` — Image dùng

```yaml
services:
  web:
    image: nginx:1.25-alpine
```

#### `build` — Build image từ Dockerfile

```yaml
services:
  app:
    build: .                          # Build từ thư mục hiện tại
    # Hoặc chi tiết hơn:
    build:
      context: ./app                  # Build context
      dockerfile: Dockerfile.prod     # Tên file Dockerfile
      args:                           # Build args
        PYTHON_VERSION: 3.11
      target: production              # Multi-stage target
      cache_from:                     # Cache source
        - myapp:cache
```

**Pattern phổ biến: vừa build vừa tag:**

```yaml
services:
  app:
    build: .
    image: myorg/myapp:dev    # Tag cho image vừa build
```

#### `command` — Override CMD

```yaml
services:
  app:
    image: python:3.11-slim
    command: python -m http.server 8000
    # Hoặc dạng list:
    command: ["python", "-m", "http.server", "8000"]
```

#### `entrypoint` — Override ENTRYPOINT

```yaml
services:
  app:
    image: myapp
    entrypoint: ["/custom-entrypoint.sh"]
    command: ["--mode=daily"]
```

#### `ports` — Port mapping

```yaml
services:
  web:
    image: nginx
    ports:
      - "8080:80"
      - "127.0.0.1:8443:443"     # Bind localhost only
      - "9000-9005:9000-9005"    # Range
      - target: 80                # Verbose form
        published: 8080
        protocol: tcp
        mode: host
```

#### `environment` — Env vars

```yaml
services:
  app:
    image: myapp
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_PASSWORD: ${DB_PASSWORD}    # Từ host env hoặc .env
      DEBUG: "true"                  # Quote nếu là string
```

Hoặc dạng list:

```yaml
    environment:
      - DB_HOST=postgres
      - DB_PASSWORD=${DB_PASSWORD}
```

#### `env_file` — Load env từ file

```yaml
services:
  app:
    image: myapp
    env_file:
      - .env
      - .env.local      # File sau override file trước
```

File `.env`:

```
DB_HOST=postgres
DB_PASSWORD=secret
LOG_LEVEL=info
```

**Lưu ý:** `.env` trong cùng thư mục compose **tự được load** cho variable substitution trong YAML (`${DB_PASSWORD}`). `env_file:` thì load vào container.

#### `volumes` — Mount

```yaml
services:
  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data          # Named volume
      - ./initdb:/docker-entrypoint-initdb.d:ro  # Bind mount, read-only
      - /tmp                                      # Anonymous volume
```

Định nghĩa named volume ở top level:

```yaml
volumes:
  pgdata:
    # External (đã tồn tại, không tạo mới)
    external: true
    # Hoặc driver options
    driver: local
    driver_opts:
      type: nfs
      device: ":/exports/data"
```

#### `networks` — Network

```yaml
services:
  app:
    image: myapp
    networks:
      - frontend
      - backend

networks:
  frontend:
  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```

#### `depends_on` — Thứ tự khởi động

**Dạng đơn giản:**

```yaml
services:
  app:
    image: myapp
    depends_on:
      - postgres
      - redis
```

**Pitfall:** `depends_on` chỉ đợi container **started**, KHÔNG đợi service **ready** bên trong. Postgres container start nhưng có thể chưa accept connection.

**Dạng nâng cao với healthcheck:**

```yaml
services:
  postgres:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    image: myapp
    depends_on:
      postgres:
        condition: service_healthy    # Đợi postgres HEALTHY
```

Conditions:

- `service_started` — chỉ đợi start (default)
- `service_healthy` — đợi healthcheck pass
- `service_completed_successfully` — đợi service exit 0

#### `healthcheck` — Health check container

```yaml
services:
  app:
    image: myapp
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

#### `restart` — Restart policy

```yaml
services:
  app:
    image: myapp
    restart: unless-stopped
    # no | on-failure | always | unless-stopped
```

#### `deploy.resources` — Limits

```yaml
services:
  app:
    image: myapp
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 512M
```

**Lưu ý:** `deploy.resources.limits` được Compose v2 honor. Nhưng nhiều docs viết theo cú pháp v1 (`mem_limit`, `cpus`) — cũng work.

```yaml
services:
  app:
    image: myapp
    mem_limit: 4g
    cpus: 2
```

#### `working_dir`, `user`, `hostname`

```yaml
services:
  app:
    image: python:3.11
    working_dir: /app
    user: "1000:1000"
    hostname: myapp-1
```

#### `profiles` — Optional services

```yaml
services:
  app:
    image: myapp
  
  debug-tools:
    image: nicolaka/netshoot
    profiles: ["debug"]
  
  test-runner:
    image: myapp
    command: pytest
    profiles: ["test"]
```

```bash
docker compose up                            # chỉ app
docker compose --profile debug up            # app + debug-tools
docker compose --profile test up             # app + test-runner
docker compose --profile debug --profile test up    # tất cả
```

**Use case:** Dev stack có optional service (debugger, metrics), test có thêm test runner.

### 15.6. Variable substitution

```yaml
services:
  app:
    image: myapp:${APP_VERSION:-latest}   # Default 'latest' nếu APP_VERSION không set
    environment:
      DB_HOST: ${DB_HOST}
      DB_PORT: ${DB_PORT:-5432}
      DB_PASSWORD: ${DB_PASSWORD:?error}  # Error nếu không set
```

`.env` file (tự được Compose load):

```
APP_VERSION=v1.2.3
DB_HOST=postgres
DB_PASSWORD=secret
```

### 15.7. Compose lifecycle commands

```bash
# Lên stack
docker compose up                # Foreground, log đổ ra terminal
docker compose up -d             # Background
docker compose up --build        # Force rebuild image trước
docker compose up --force-recreate    # Recreate container dù không đổi

# Tắt stack
docker compose down              # Stop + remove containers, networks
docker compose down -v           # ⚠️ Cũng xóa volumes
docker compose down --rmi all    # Cũng xóa images

# Stop nhưng không remove
docker compose stop
docker compose start

# Status
docker compose ps
docker compose ps -a

# Logs
docker compose logs              # Tất cả services
docker compose logs -f app       # Follow service 'app'
docker compose logs --tail 100   # Tail

# Exec
docker compose exec app bash
docker compose exec postgres psql -U postgres

# Run one-off (tạo container mới, không như exec)
docker compose run --rm app python script.py

# Build
docker compose build
docker compose build --no-cache

# Pull
docker compose pull              # Pull tất cả image
```

### 15.8. Override files

Pattern phổ biến: base file + override.

**`compose.yaml`** (base, dev defaults):

```yaml
services:
  app:
    image: myapp
    environment:
      LOG_LEVEL: debug
```

**`compose.prod.yaml`** (override cho prod):

```yaml
services:
  app:
    environment:
      LOG_LEVEL: warning
    deploy:
      resources:
        limits:
          memory: 8G
```

Chạy:

```bash
docker compose up                                    # Dev (compose.yaml)
docker compose -f compose.yaml -f compose.prod.yaml up    # Prod
```

Compose tự động đọc `compose.override.yaml` nếu có (không cần `-f`).

---

### ✅ TÓM TẮT CHƯƠNG 15

#### Compose file template

```yaml
name: my-project

services:
  service-name:
    image: nginx:1.25
    build:
      context: .
    container_name: my-app
    command: ["python", "main.py"]
    ports: ["8000:8000"]
    environment:
      KEY: value
    env_file: .env
    volumes:
      - data:/var/data
      - ./config:/etc/app:ro
    networks: [frontend, backend]
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1'

volumes:
  data:

networks:
  frontend:
  backend:
```

---

## 📖 CHƯƠNG 16: COMPOSE PATTERNS CHO MULTI-SERVICE

### 16.1. Pattern 1: Web app + Database

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: appdb
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  app:
    build: .
    environment:
      DATABASE_URL: postgresql://app:${DB_PASSWORD}@postgres:5432/appdb
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  pgdata:
```

`.env`:

```
DB_PASSWORD=mysecret
```

### 16.2. Pattern 2: App + DB + Cache + Worker

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  api:
    build: ./api
    environment:
      DB_HOST: postgres
      REDIS_HOST: redis
    ports: ["8000:8000"]
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }

  worker:
    build: ./worker
    environment:
      DB_HOST: postgres
      REDIS_HOST: redis
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    deploy:
      replicas: 3   # 3 worker instance

volumes:
  pgdata:
```

```bash
docker compose up -d --scale worker=5    # Override replicas
```

### 16.3. Pattern 3: Dev với hot reload

```yaml
services:
  app:
    build:
      context: .
      target: development     # Multi-stage target
    volumes:
      - ./src:/app/src       # Bind mount code
      - /app/node_modules    # Exclude node_modules
    ports: ["3000:3000"]
    environment:
      NODE_ENV: development
    command: npm run dev     # Dev server với hot reload
```

### 16.4. Pattern 4: Init container

Cần chạy migration trước app:

```yaml
services:
  postgres:
    image: postgres:15
    # ...
    healthcheck: ...

  migrate:
    build: .
    command: alembic upgrade head    # Migration tool
    environment:
      DATABASE_URL: postgresql://...@postgres:5432/db
    depends_on:
      postgres: { condition: service_healthy }
    restart: "no"

  app:
    build: .
    depends_on:
      migrate:
        condition: service_completed_successfully
    # ...
```

### 16.5. Pattern 5: Multiple environments

**`compose.yaml`** (chung):

```yaml
services:
  app:
    build: .
    image: myapp
    environment:
      LOG_LEVEL: ${LOG_LEVEL:-info}
```

**`compose.dev.yaml`**:

```yaml
services:
  app:
    volumes:
      - ./src:/app/src
    environment:
      LOG_LEVEL: debug
    command: python -m uvicorn main:app --reload
```

**`compose.prod.yaml`**:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G
    restart: always
```

```bash
# Dev
docker compose -f compose.yaml -f compose.dev.yaml up

# Prod
docker compose -f compose.yaml -f compose.prod.yaml up
```

---

### ✅ TÓM TẮT CHƯƠNG 16

#### Best Practices Compose

- ✅ Đặt tên file `compose.yaml` (chuẩn mới)
- ✅ Pin version image cụ thể
- ✅ Healthcheck cho service quan trọng
- ✅ `depends_on` với `condition: service_healthy`
- ✅ Variable substitution cho secret (không hardcode)
- ✅ `.env` cho default values
- ✅ Named volumes cho data persistent
- ✅ Override file cho dev/staging/prod
- ❌ Đừng dùng `docker compose up` mà không hiểu service nào sẽ start
- ❌ Đừng `docker compose down -v` trừ khi chắc muốn xóa data

#### Câu hỏi tự kiểm tra

1. `depends_on` với `condition: service_started` khác gì `service_healthy`?
2. `env_file` và `environment` khác gì nhau?
3. Khi nào dùng `command:` để override CMD?
4. `docker compose down -v` làm gì?
5. Profile có tác dụng gì?

#### Bài tập

**Bài 1:** Setup app FastAPI + Postgres với healthcheck:

```yaml
# compose.yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: secret
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s

  app:
    image: python:3.11-slim
    command: python -m http.server 8000
    ports: ["8000:8000"]
    depends_on:
      postgres: { condition: service_healthy }

volumes:
  pgdata:
```

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

---

## 🎯 KẾT THÚC PHẦN 6

Đến đây bạn đã có nền tảng vững. Tiếp theo là **Phần 7 — quan trọng nhất với Data Engineer**.

---

# 📘 PHẦN 7: DOCKER CHO DATA ENGINEERING

> *Đây là phần "đắt giá" nhất với Data Engineer. Bạn sẽ học cách container hóa toàn bộ data stack: Airflow, Spark, Kafka, Postgres, dbt, MinIO, Jupyter — và kết thúc bằng một mini data platform hoàn chỉnh.*

---

## 📖 CHƯƠNG 17: VÌ SAO DATA ENGINEER PHẢI MASTER DOCKER

### 17.1. Realities của Data Engineering

Data Engineering khác Software Engineering thông thường ở mấy điểm:

1. **Stack đa dạng kỳ lạ**: 1 dự án có thể dùng Python + Java + SQL + Bash, kèm 5-10 service (Airflow, Spark, Kafka, Postgres, S3, dbt...).
2. **Mỗi service "khó tính"**: Airflow cần Python version cụ thể, Spark cần Java cụ thể, Kafka cần Zookeeper hoặc KRaft, dbt cần adapter riêng cho từng DB.
3. **Pipeline cần reproducible**: Pipeline chạy hôm nay phải giống hôm qua, giống tháng sau. Nếu không, "data drift" → kết quả sai.
4. **Local ≠ Production**: Production thường là cloud (AWS EMR, Databricks, MWAA). Local cần mô phỏng được càng giống càng tốt.
5. **Test khó**: Test ETL job cần DB, cần data sample, cần message broker. Mỗi developer cần stack riêng.

→ **Docker giải quyết tất cả những vấn đề trên.**

### 17.2. Use cases cụ thể cho Data Engineer

#### a) Local data platform mô phỏng production

```yaml
# Một file compose, full data platform local
services:
  airflow-postgres: ...
  airflow-webserver: ...
  airflow-scheduler: ...
  airflow-worker: ...
  spark-master: ...
  spark-worker: ...
  kafka: ...
  minio: ...
  trino: ...
```

Junior mới vào: `git clone && docker compose up` — 5 phút sau có cả data platform.

#### b) Pipeline tái lập tuyệt đối

ETL job được đóng gói trong image với version pinned. 6 tháng sau pull lại image: chạy y nguyên kết quả.

#### c) Testing với DB thật

```python
# Trong pytest
def test_etl():
    # Spin up Postgres container trong test (testcontainers-python)
    with PostgresContainer("postgres:15") as pg:
        run_etl(pg.get_connection_url())
        assert validate_data()
```

#### d) CI/CD cho data pipeline

- Mỗi commit: build image ETL → run unit test trong container → push image lên registry.
- Airflow production pull image về để chạy task (KubernetesPodOperator).

#### e) Dependency isolation

Project A dùng pyspark 3.3 (pandas 1.5). Project B dùng pyspark 3.5 (pandas 2.0). Cùng máy: ác mộng. Docker: zero conflict.

#### f) Tránh "polluted host"

Không cài Postgres, Spark, Kafka trực tiếp lên máy → máy bạn sạch, dễ maintain.

### 17.3. Data Engineer cần biết Docker đến mức nào?

**Mức 1 — Sống còn (BẮT BUỘC):**

- Hiểu container, image, volume, network.
- Đọc và sửa được `compose.yaml`.
- Debug được "app không kết nối DB".
- Biết viết Dockerfile cho Python ETL job.

**Mức 2 — Productive (KHUYẾN NGHỊ):**

- Multi-stage build, tối ưu image.
- Compose patterns (profiles, healthcheck, override).
- Hiểu volume permission issues.
- Tự setup được Airflow/Spark/Kafka local.

**Mức 3 — Expert:**

- Build CI/CD pipeline build/push image.
- Tối ưu performance container (resource limits, network).
- Chuyển từ Docker Compose sang Kubernetes.
- Custom image cho production data pipeline.

Tài liệu này sẽ đưa bạn đến **Mức 3**.

---

## 📖 CHƯƠNG 18: CONTAINER HÓA ETL/ELT PIPELINE

### 18.1. Nguyên tắc thiết kế ETL container

#### Nguyên tắc 1: Stateless

ETL job nên **stateless** — không lưu state trong container. Nếu cần state (checkpoint, last-processed timestamp), lưu vào:

- DB (Postgres, Redis)
- Object storage (S3, MinIO)
- File system (qua volume)

#### Nguyên tắc 2: Idempotent

Chạy job nhiều lần với cùng input → cùng output. Đây là yêu cầu để retry an toàn.

#### Nguyên tắc 3: Config qua environment

```python
# Không hardcode
DB_HOST = "postgres"            # ❌
# Đọc từ env
DB_HOST = os.environ["DB_HOST"]  # ✅
```

→ Cùng image chạy được nhiều môi trường (dev/staging/prod) chỉ qua đổi env.

#### Nguyên tắc 4: Log ra stdout/stderr

```python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

logger.info("Job started")
# ✅ Docker capture được
```

```python
# Ghi log ra file:
logger.addHandler(logging.FileHandler("/app/log.txt"))
# ❌ Docker không thấy, file mất khi container die
```

#### Nguyên tắc 5: Exit code đúng

```python
import sys

def main():
    try:
        run_etl()
    except Exception as e:
        logger.error(f"ETL failed: {e}")
        sys.exit(1)    # ✅ Báo cho orchestrator biết fail
    sys.exit(0)
```

Airflow/Kubernetes dựa vào exit code để retry.

### 18.2. Demo: ETL job đầy đủ trong Docker

#### Cấu trúc project

```
etl-demo/
├── Dockerfile
├── .dockerignore
├── compose.yaml
├── requirements.txt
├── .env.example
├── data/
│   └── input.csv
└── etl/
    ├── __init__.py
    ├── main.py
    ├── extract.py
    ├── transform.py
    └── load.py
```

#### File: `requirements.txt`

```
pandas==2.1.4
psycopg2-binary==2.9.9
sqlalchemy==2.0.25
python-dotenv==1.0.0
```

#### File: `etl/extract.py`

```python
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def extract_csv(path: str) -> pd.DataFrame:
    logger.info(f"Extracting from {path}")
    df = pd.read_csv(path)
    logger.info(f"Extracted {len(df)} rows")
    return df
```

#### File: `etl/transform.py`

```python
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def transform(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming data")
    df = df.dropna(subset=['email'])
    df['email'] = df['email'].str.lower().str.strip()
    df['domain'] = df['email'].str.split('@').str[1]
    df['processed_at'] = pd.Timestamp.now()
    logger.info(f"After transform: {len(df)} rows")
    return df
```

#### File: `etl/load.py`

```python
import logging
import pandas as pd
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

def load_to_postgres(df: pd.DataFrame, conn_str: str, table: str):
    logger.info(f"Loading {len(df)} rows to {table}")
    engine = create_engine(conn_str)
    df.to_sql(table, engine, if_exists='replace', index=False)
    logger.info("Load complete")
```

#### File: `etl/main.py`

```python
import logging
import os
import sys
from etl.extract import extract_csv
from etl.transform import transform
from etl.load import load_to_postgres

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    input_path = os.environ.get("INPUT_PATH", "/data/input.csv")
    db_conn = os.environ["DATABASE_URL"]
    table = os.environ.get("OUTPUT_TABLE", "users_processed")
  
    try:
        df = extract_csv(input_path)
        df = transform(df)
        load_to_postgres(df, db_conn, table)
        logger.info("ETL completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"ETL failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### File: `Dockerfile`

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl/ ./etl/

RUN groupadd -r etl && useradd -r -g etl etl && \
    chown -R etl:etl /app
USER etl

ENTRYPOINT ["python", "-m", "etl.main"]
```

#### File: `compose.yaml`

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: etl
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: etldb
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U etl"]
      interval: 5s
      timeout: 5s
      retries: 10

  etl:
    build: .
    environment:
      DATABASE_URL: postgresql://etl:${DB_PASSWORD}@postgres:5432/etldb
      INPUT_PATH: /data/input.csv
      OUTPUT_TABLE: users
      LOG_LEVEL: INFO
    volumes:
      - ./data:/data:ro
    depends_on:
      postgres:
        condition: service_healthy
    restart: "no"

volumes:
  pgdata:
```

#### File: `.env`

```
DB_PASSWORD=secret123
```

#### File: `data/input.csv`

```csv
id,email,name
1,alice@example.com,Alice
2,BOB@example.COM ,Bob
3,charlie@example.org,Charlie
4,,David
5,eve@test.com,Eve
```

#### Chạy

```bash
docker compose up --build
# etl-1       | Extracting from /data/input.csv
# etl-1       | Extracted 5 rows
# etl-1       | Transforming data
# etl-1       | After transform: 4 rows (dropped null email)
# etl-1       | Loading 4 rows to users
# etl-1       | Load complete
# etl-1       | ETL completed successfully
# etl-1 exited with code 0

# Verify
docker compose exec postgres psql -U etl -d etldb -c "SELECT * FROM users;"
```

### 18.3. Pattern: ETL output → Volume

```yaml
services:
  etl:
    build: .
    volumes:
      - ./data:/data:ro          # Input read-only
      - ./output:/output         # Output writable
    environment:
      INPUT_PATH: /data/input.csv
      OUTPUT_PATH: /output/result.parquet
```

Output file xuất hiện ở host folder `./output`. Permission: dùng `USER` matching UID host hoặc `chown` trong entrypoint.

### 18.4. Pattern: ETL với secrets

❌ KHÔNG:

```yaml
services:
  etl:
    environment:
      AWS_SECRET_KEY: AKIAIOSFODNN7EXAMPLE   # Hardcoded
```

✅ DÙNG:

```yaml
services:
  etl:
    env_file: .env.secret   # File này KHÔNG commit
```

`.gitignore`:

```
.env.secret
.env.local
```

Hoặc dùng Docker secrets (Swarm) / external secret manager (Vault, AWS Secrets Manager).

---

### ✅ TÓM TẮT CHƯƠNG 18

#### Checklist ETL container

- [ ] Stateless: state lưu external
- [ ] Idempotent: chạy lại không phá data
- [ ] Config qua env, không hardcode
- [ ] Log ra stdout/stderr
- [ ] Exit code đúng (0 success, !=0 fail)
- [ ] Handle SIGTERM gracefully (flush data trước khi exit)
- [ ] Pin dependency versions
- [ ] Non-root user trong container
- [ ] Healthcheck nếu long-running
- [ ] Resource limits

---

## 📖 CHƯƠNG 19: AIRFLOW VỚI DOCKER

### 19.1. Kiến trúc Airflow

```mermaid
graph TB
    UI[Webserver UI] --> DB[(Metadata DB<br/>Postgres)]
    SCH[Scheduler] --> DB
    SCH --> Q[Queue<br/>Redis/RabbitMQ]
    Q --> W1[Worker 1]
    Q --> W2[Worker 2]
    Q --> W3[Worker N]
    W1 --> DB
    W2 --> DB
    W3 --> DB
    TR[Triggerer] --> DB
```

Components:

- **Webserver**: UI Flask (port 8080)
- **Scheduler**: Đọc DAG, schedule tasks
- **Worker**: Chạy task (Celery executor)
- **Triggerer**: Xử lý deferred operators (async)
- **Metadata DB**: Postgres (lưu DAG runs, task state)
- **Queue**: Redis (Celery broker)

### 19.2. Setup Airflow với Compose chính thức

Apache Airflow cung cấp `docker-compose.yaml` official. Tải về:

```bash
mkdir airflow-local && cd airflow-local
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
```

**Cấu trúc thư mục cần tạo:**

```bash
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

**Init DB lần đầu:**

```bash
docker compose up airflow-init
```

**Lên toàn stack:**

```bash
docker compose up -d
```

Truy cập: http://localhost:8080 (user: `airflow`, pass: `airflow`).

### 19.3. Compose Airflow tối giản (cho học)

```yaml
x-airflow-common:
  &airflow-common
  image: apache/airflow:2.8.1-python3.11
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      retries: 5

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        airflow db migrate
        airflow users create \
          --username admin --password admin \
          --firstname Admin --lastname User \
          --role Admin --email admin@example.com

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports: ["8080:8080"]
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-worker:
    <<: *airflow-common
    command: celery worker
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

volumes:
  postgres-db-volume:
```

### 19.4. Custom Airflow image — Cài thêm provider

Mặc định Airflow chỉ có core. Cần provider (Postgres, AWS, Spark...) → build custom image.

**File: `Dockerfile`**

```dockerfile
FROM apache/airflow:2.8.1-python3.11

# Cài provider packages
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres==5.10.0 \
    apache-airflow-providers-amazon==8.16.0 \
    apache-airflow-providers-apache-spark==4.6.0 \
    apache-airflow-providers-snowflake==5.2.1 \
    apache-airflow-providers-google==10.13.1
```

Sửa `compose.yaml`:

```yaml
x-airflow-common:
  &airflow-common
  build: .                      # Build từ Dockerfile
  image: myorg/airflow:2.8.1-custom
```

### 19.5. DAG mẫu — Postgres ETL

**File: `dags/example_etl.py`**

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract_from_postgres(**context):
    hook = PostgresHook(postgres_conn_id='postgres_default')
    df = hook.get_pandas_df("SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '1 day'")
    output_path = f"/opt/airflow/data/users_{context['ds']}.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")
    return output_path

def transform(**context):
    import pandas as pd
    ti = context['ti']
    input_path = ti.xcom_pull(task_ids='extract')
    df = pd.read_csv(input_path)
    df['email_domain'] = df['email'].str.split('@').str[1]
    output_path = input_path.replace('.csv', '_transformed.csv')
    df.to_csv(output_path, index=False)
    return output_path

with DAG(
    dag_id='example_etl',
    default_args=default_args,
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'etl'],
) as dag:
  
    t1 = PythonOperator(task_id='extract', python_callable=extract_from_postgres)
    t2 = PythonOperator(task_id='transform', python_callable=transform)
  
    t1 >> t2
```

### 19.6. Connect Airflow tới external service

**Qua env (recommended cho IaC):**

```yaml
environment:
  AIRFLOW_CONN_POSTGRES_DEFAULT: 'postgresql://user:pass@host:5432/db'
  AIRFLOW_CONN_AWS_DEFAULT: 'aws://AKIA...:secret@?region_name=us-east-1'
```

**Qua `airflow connections add` trong init container:**

```yaml
airflow-init:
  entrypoint: /bin/bash
  command:
    - -c
    - |
      airflow db migrate
      airflow connections add postgres_source \
        --conn-type postgres \
        --conn-host external-postgres \
        --conn-login user --conn-password pass \
        --conn-port 5432
```

### 19.7. Common errors với Airflow Docker

| Lỗi                          | Nguyên nhân                   | Fix                                                 |
| ----------------------------- | ------------------------------- | --------------------------------------------------- |
| Permission denied trên dags/ | `id -u` host ≠ UID container | `echo "AIRFLOW_UID=$(id -u)" >> .env`             |
| DAG không xuất hiện        | DAG có syntax error            | `docker compose exec scheduler airflow dags list` |
| Worker chạy không nổi      | RAM không đủ                 | Tăng Docker Desktop RAM                            |
| Postgres connection refused   | Healthcheck chưa pass          | Đợi, hoặc kiểm tra postgres logs                |
| Provider import error         | Chưa cài provider             | Build custom image với provider                    |

### 19.8. Best practices Airflow Docker

- ✅ Dùng `image: apache/airflow:VERSION-pythonX.Y` cụ thể.
- ✅ Mount `dags/`, `logs/`, `plugins/` qua bind mount cho dev.
- ✅ Production: bake DAGs vào image hoặc git-sync.
- ✅ Resource limits cho worker.
- ✅ Backup metadata DB định kỳ.
- ✅ Set `AIRFLOW__CORE__LOAD_EXAMPLES: 'false'`.
- ❌ Đừng commit `airflow.cfg` chứa secret.
- ❌ Đừng dùng `LocalExecutor` cho production scale lớn.

---

## 📖 CHƯƠNG 20: SPARK VỚI DOCKER

### 20.1. Spark standalone với Compose

```yaml
services:
  spark-master:
    image: bitnami/spark:3.5
    environment:
      SPARK_MODE: master
      SPARK_RPC_AUTHENTICATION_ENABLED: 'no'
      SPARK_RPC_ENCRYPTION_ENABLED: 'no'
      SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED: 'no'
      SPARK_SSL_ENABLED: 'no'
    ports:
      - "8081:8080"   # Master UI
      - "7077:7077"   # Master port
    volumes:
      - ./jobs:/opt/jobs
      - ./data:/opt/data

  spark-worker-1:
    image: bitnami/spark:3.5
    environment:
      SPARK_MODE: worker
      SPARK_MASTER_URL: spark://spark-master:7077
      SPARK_WORKER_MEMORY: 2G
      SPARK_WORKER_CORES: 2
    depends_on: [spark-master]
    volumes:
      - ./jobs:/opt/jobs
      - ./data:/opt/data

  spark-worker-2:
    image: bitnami/spark:3.5
    environment:
      SPARK_MODE: worker
      SPARK_MASTER_URL: spark://spark-master:7077
      SPARK_WORKER_MEMORY: 2G
      SPARK_WORKER_CORES: 2
    depends_on: [spark-master]
    volumes:
      - ./jobs:/opt/jobs
      - ./data:/opt/data
```

UI: http://localhost:8081

### 20.2. Submit PySpark job

**File: `jobs/wordcount.py`**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("WordCount").getOrCreate()

text = spark.read.text("/opt/data/input.txt")
counts = text.rdd.flatMap(lambda row: row.value.split()) \
    .map(lambda word: (word, 1)) \
    .reduceByKey(lambda a, b: a + b)

for word, count in counts.collect():
    print(f"{word}: {count}")

spark.stop()
```

Submit:

```bash
docker compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /opt/jobs/wordcount.py
```

### 20.3. Khi nào dùng Spark local Docker?

✅ **Phù hợp:**

- Dev và test job logic
- Test transformation nhỏ
- Học PySpark
- CI/CD test

❌ **KHÔNG phù hợp:**

- Production data lớn (TB+)
- High availability cần
- → Production: AWS EMR, Databricks, GCP Dataproc

### 20.4. Vấn đề performance Spark Docker

1. **Memory**: Spark ngốn RAM. Worker 2GB là tối thiểu cho dev.
2. **Shuffle**: Disk IO chậm trong Docker Desktop trên Mac/Win.
3. **Network**: Spark dùng RPC giữa nodes — overhead container > native.
4. **Concurrent jobs**: 1 job đã ngốn hết worker → queue.

**Best practices:**

- Set `SPARK_WORKER_MEMORY` rõ ràng.
- Set `--executor-memory`, `--driver-memory` khi submit.
- Volume Spark logs để debug.

---

## 📖 CHƯƠNG 21: KAFKA VỚI DOCKER

### 21.1. Kafka KRaft (không cần Zookeeper)

Từ Kafka 3.3+, có thể chạy không cần Zookeeper (KRaft mode):

```yaml
services:
  kafka:
    image: bitnami/kafka:3.6
    ports:
      - "9092:9092"
    environment:
      KAFKA_CFG_NODE_ID: 0
      KAFKA_CFG_PROCESS_ROLES: controller,broker
      KAFKA_CFG_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_CFG_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 0@kafka:9093
      KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
    volumes:
      - kafka-data:/bitnami/kafka

volumes:
  kafka-data:
```

### 21.2. Vấn đề `advertised.listeners` khét tiếng

Đây là **lỗi #1** với Kafka Docker. Hiểu rõ:

**Vấn đề:** Khi producer/consumer connect Kafka, Kafka response **danh sách advertised listeners**. Client dùng đó để kết nối broker thực sự.

→ Nếu `advertised.listeners` sai → client không reach được broker.

**Tình huống 1: Container nội bộ → Kafka cùng network**

```yaml
KAFKA_CFG_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
```

→ Client trong network nói "kafka:9092" → OK.

**Tình huống 2: Host → Kafka qua `localhost:9092`**

```yaml
KAFKA_CFG_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
```

→ Host gọi `localhost:9092` → OK. Nhưng container khác trong network gọi "localhost:9092" → fail.

**Tình huống 3 (PHỔ BIẾN NHẤT): Vừa internal vừa external**

Cần **2 listeners**:

```yaml
services:
  kafka:
    image: bitnami/kafka:3.6
    ports:
      - "9092:9092"
    environment:
      KAFKA_CFG_NODE_ID: 0
      KAFKA_CFG_PROCESS_ROLES: controller,broker
      KAFKA_CFG_LISTENERS: INTERNAL://:29092,EXTERNAL://:9092,CONTROLLER://:9093
      KAFKA_CFG_ADVERTISED_LISTENERS: INTERNAL://kafka:29092,EXTERNAL://localhost:9092
      KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 0@kafka:9093
      KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CFG_INTER_BROKER_LISTENER_NAME: INTERNAL
```

→ Container khác trong network → `kafka:29092` (INTERNAL).
→ App từ host → `localhost:9092` (EXTERNAL).

### 21.3. Producer/Consumer Python

**File: `producer.py`**

```python
from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers=['kafka:29092'],   # Nội bộ network
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

for i in range(100):
    event = {'id': i, 'value': f'event-{i}', 'timestamp': time.time()}
    producer.send('events', event)
    print(f"Sent: {event}")
    time.sleep(0.5)

producer.flush()
```

**File: `consumer.py`**

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'events',
    bootstrap_servers=['kafka:29092'],
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='my-group'
)

for msg in consumer:
    print(f"Received: {msg.value}")
```

### 21.4. Kafka UI (debug)

```yaml
services:
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports: ["8082:8080"]
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
    depends_on: [kafka]
```

→ http://localhost:8082

---

## 📖 CHƯƠNG 22: DATABASE TRONG DOCKER (DEEP DIVE)

### 22.1. Multiple databases trong 1 Postgres container

```bash
mkdir initdb
cat > initdb/01_create_dbs.sh <<'EOF'
#!/bin/bash
set -e
psql -U "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE source_db;
    CREATE DATABASE warehouse_db;
    CREATE DATABASE dbt_db;
    CREATE USER etl_user WITH PASSWORD 'etlpass';
    GRANT ALL PRIVILEGES ON DATABASE source_db TO etl_user;
    GRANT ALL PRIVILEGES ON DATABASE warehouse_db TO etl_user;
EOSQL
EOF
chmod +x initdb/01_create_dbs.sh
```

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - ./initdb:/docker-entrypoint-initdb.d:ro
      - pgdata:/var/lib/postgresql/data
```

### 22.2. Postgres với extension (pgvector, pg_cron)

```dockerfile
FROM postgres:15
RUN apt-get update && \
    apt-get install -y postgresql-15-pgvector postgresql-15-cron && \
    rm -rf /var/lib/apt/lists/*
```

```yaml
services:
  postgres:
    build: .
    command: postgres -c shared_preload_libraries=pg_cron
    environment:
      POSTGRES_PASSWORD: secret
```

### 22.3. Testing pattern với testcontainers

```python
# pip install testcontainers
from testcontainers.postgres import PostgresContainer

def test_etl():
    with PostgresContainer("postgres:15-alpine") as pg:
        conn_url = pg.get_connection_url()
        run_etl(conn_url)
        # Verify
    # Container tự tear down
```

---

## 📖 CHƯƠNG 23: DBT VỚI DOCKER

### 23.1. Dockerfile cho dbt project

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DBT_PROFILES_DIR=/dbt/profiles

WORKDIR /dbt

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    dbt-core==1.7.4 \
    dbt-postgres==1.7.4

COPY . .

RUN if [ -f packages.yml ]; then dbt deps; fi

ENTRYPOINT ["dbt"]
CMD ["run"]
```

### 23.2. profiles.yml

**File: `profiles/profiles.yml`**

```yaml
default:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('DBT_HOST', 'postgres') }}"
      port: 5432
      user: "{{ env_var('DBT_USER', 'dbt') }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
      dbname: "{{ env_var('DBT_DB', 'warehouse') }}"
      schema: analytics
      threads: 4
```

### 23.3. Compose cho dbt + Postgres

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: dbt
      POSTGRES_PASSWORD: dbtpass
      POSTGRES_DB: warehouse
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dbt"]

  dbt:
    build: .
    environment:
      DBT_HOST: postgres
      DBT_USER: dbt
      DBT_PASSWORD: dbtpass
      DBT_DB: warehouse
    volumes:
      - ./models:/dbt/models
      - ./profiles:/dbt/profiles:ro
      - ./tests:/dbt/tests
    depends_on:
      postgres:
        condition: service_healthy
    profiles: ["manual"]

volumes:
  pgdata:
```

```bash
docker compose up -d postgres
docker compose run --rm dbt run
docker compose run --rm dbt test
docker compose run --rm dbt docs generate
```

### 23.4. CI/CD dbt với Docker

```yaml
# .github/workflows/dbt.yml
name: dbt CI
on: [pull_request]
jobs:
  dbt-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build dbt image
        run: docker build -t dbt-ci .
      - name: Spin up Postgres
        run: |
          docker run -d --name pg \
            -e POSTGRES_PASSWORD=test \
            -p 5432:5432 \
            postgres:15
          sleep 5
      - name: Run dbt
        run: |
          docker run --rm --network host \
            -e DBT_HOST=localhost \
            -e DBT_PASSWORD=test \
            dbt-ci compile
          docker run --rm --network host \
            -e DBT_HOST=localhost \
            -e DBT_PASSWORD=test \
            dbt-ci test
```

---

## 📖 CHƯƠNG 24: DATA LAKE LOCAL VỚI MINIO

### 24.1. MinIO — S3 local

```yaml
services:
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"   # API S3
      - "9001:9001"   # Console UI
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: minio123
    volumes:
      - minio-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 5s

  minio-init:
    image: minio/mc:latest
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      mc alias set local http://minio:9000 admin minio123;
      mc mb local/raw-data || true;
      mc mb local/processed || true;
      mc mb local/curated || true;
      "

volumes:
  minio-data:
```

Console: http://localhost:9001

### 24.2. boto3 connect MinIO

```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='admin',
    aws_secret_access_key='minio123',
    region_name='us-east-1',
)

s3.upload_file('data.csv', 'raw-data', 'input/data.csv')
s3.download_file('raw-data', 'input/data.csv', 'local.csv')

for obj in s3.list_objects_v2(Bucket='raw-data').get('Contents', []):
    print(obj['Key'])
```

### 24.3. Spark đọc/ghi MinIO

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("S3Test") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minio123") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4") \
    .getOrCreate()

df = spark.read.csv("s3a://raw-data/input/data.csv", header=True)
df.write.parquet("s3a://processed/output/")
```

### 24.4. Pipeline mini: CSV → Parquet trên MinIO

**File: `pipeline.py`**

```python
import boto3
import pandas as pd
from io import BytesIO

s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='admin',
    aws_secret_access_key='minio123',
)

# Ingest CSV
df = pd.read_csv('/data/input.csv')
print(f"Loaded {len(df)} rows")

# Transform
df['processed'] = True
df['ingested_at'] = pd.Timestamp.now()

# Write Parquet to MinIO
buffer = BytesIO()
df.to_parquet(buffer, index=False)
buffer.seek(0)

s3.put_object(Bucket='processed', Key='users.parquet', Body=buffer.read())
print("Uploaded to MinIO")
```

---

## 📖 CHƯƠNG 25: JUPYTER VỚI DOCKER

### 25.1. Jupyter Lab cơ bản

```yaml
services:
  jupyter:
    image: jupyter/datascience-notebook:latest
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/home/jovyan/work
    environment:
      JUPYTER_ENABLE_LAB: 'yes'
      JUPYTER_TOKEN: 'mytoken'
```

→ http://localhost:8888 (token: mytoken)

**Image options:**

- `jupyter/base-notebook` — Python only
- `jupyter/scipy-notebook` — + scipy stack
- `jupyter/datascience-notebook` — + R + Julia
- `jupyter/pyspark-notebook` — + Spark
- `jupyter/all-spark-notebook` — + Spark + R

### 25.2. Custom image với dependencies

```dockerfile
FROM jupyter/scipy-notebook:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && rm -rf /var/lib/apt/lists/*

USER $NB_UID

RUN pip install --no-cache-dir \
    psycopg2-binary \
    pyspark==3.5.0 \
    boto3 \
    duckdb \
    great-expectations
```

### 25.3. Jupyter kết nối Postgres + MinIO

Trong Compose:

```yaml
services:
  jupyter:
    build: .
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/home/jovyan/work
    environment:
      JUPYTER_TOKEN: 'mytoken'
      DB_HOST: postgres
      MINIO_ENDPOINT: http://minio:9000
    depends_on:
      - postgres
      - minio
    networks: [data-net]
```

Trong notebook:

```python
# Connect Postgres
import psycopg2
import os

conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    user='etl',
    password='etlpass',
    dbname='warehouse'
)

# Connect MinIO
import boto3
s3 = boto3.client(
    's3',
    endpoint_url=os.environ['MINIO_ENDPOINT'],
    aws_access_key_id='admin',
    aws_secret_access_key='minio123'
)
```

### 25.4. PySpark trong Jupyter

```yaml
services:
  jupyter-pyspark:
    image: jupyter/pyspark-notebook:latest
    ports:
      - "8888:8888"
      - "4040:4040"   # Spark UI
    volumes:
      - ./notebooks:/home/jovyan/work
    environment:
      JUPYTER_TOKEN: 'mytoken'
      SPARK_MASTER: spark://spark-master:7077
    depends_on: [spark-master]
```

Trong notebook:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Jupyter") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

df = spark.read.csv("hdfs://...")
df.show()
```

---

## 📖 CHƯƠNG 26: 🚀 MINI PROJECT — MINI DATA PLATFORM HOÀN CHỈNH

> *Đây là project thực hành tổng hợp tất cả. Sau khi làm xong, bạn đã có một bộ skill thực tế applicable cho job interview và work thực tế.*

### 26.1. Kiến trúc

```mermaid
graph LR
    subgraph "Source"
        CSV[CSV files<br/>./data/raw/]
    end
    subgraph "Storage"
        PG[(Postgres<br/>OLTP source)]
        MIN[MinIO<br/>S3 Data Lake]
        WH[(Postgres<br/>Warehouse)]
    end
    subgraph "Processing"
        AIR[Airflow<br/>Scheduler]
        DBT[dbt<br/>Transform]
    end
    subgraph "Consumption"
        JUP[Jupyter<br/>Analytics]
    end
    CSV -->|Ingest DAG| AIR
    AIR -->|Load| PG
    AIR -->|Stage| MIN
    PG -->|Extract| MIN
    MIN -->|Load| WH
    WH -->|Transform| DBT
    DBT -->|Models| WH
    WH -->|Query| JUP
    MIN -->|Read| JUP
```

### 26.2. Cấu trúc project

```
mini-data-platform/
├── compose.yaml
├── .env
├── README.md
├── airflow/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── dags/
│   │   ├── ingest_csv_to_postgres.py
│   │   ├── postgres_to_minio.py
│   │   └── minio_to_warehouse.py
│   ├── logs/
│   └── plugins/
├── dbt/
│   ├── Dockerfile
│   ├── dbt_project.yml
│   ├── profiles/
│   │   └── profiles.yml
│   └── models/
│       ├── staging/
│       │   └── stg_users.sql
│       └── marts/
│           └── dim_users.sql
├── jupyter/
│   ├── Dockerfile
│   └── notebooks/
│       └── analysis.ipynb
├── data/
│   ├── raw/
│   │   └── users.csv
│   └── postgres-init/
│       └── 01_create_schemas.sql
└── scripts/
    └── generate_sample_data.py
```

### 26.3. File `compose.yaml` chính

```yaml
name: mini-data-platform

x-airflow-common: &airflow-common
  build: ./airflow
  image: mdp/airflow:latest
  environment:
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@airflow-db/airflow
    AIRFLOW_CONN_POSTGRES_SOURCE: 'postgresql://etl:${DB_PASSWORD}@source-db:5432/source_db'
    AIRFLOW_CONN_POSTGRES_WAREHOUSE: 'postgresql://etl:${DB_PASSWORD}@warehouse-db:5432/warehouse_db'
    MINIO_ENDPOINT: http://minio:9000
    MINIO_ACCESS_KEY: admin
    MINIO_SECRET_KEY: ${MINIO_PASSWORD}
  volumes:
    - ./airflow/dags:/opt/airflow/dags
    - ./airflow/logs:/opt/airflow/logs
    - ./airflow/plugins:/opt/airflow/plugins
    - ./data:/opt/airflow/data
  user: "${AIRFLOW_UID:-50000}:0"
  networks: [dataplatform]

services:
  # --------- Source Postgres ---------
  source-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: etl
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: source_db
    volumes:
      - source-pgdata:/var/lib/postgresql/data
      - ./data/postgres-init:/docker-entrypoint-initdb.d:ro
    ports: ["5433:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U etl"]
      interval: 5s
    networks: [dataplatform]

  # --------- Warehouse Postgres ---------
  warehouse-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: etl
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: warehouse_db
    volumes:
      - warehouse-pgdata:/var/lib/postgresql/data
    ports: ["5434:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U etl"]
      interval: 5s
    networks: [dataplatform]

  # --------- MinIO Data Lake ---------
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
    networks: [dataplatform]

  minio-init:
    image: minio/mc:latest
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: |
      /bin/sh -c '
      mc alias set local http://minio:9000 admin ${MINIO_PASSWORD};
      mc mb local/raw || true;
      mc mb local/staged || true;
      mc mb local/curated || true;
      echo "MinIO initialized"
      '
    networks: [dataplatform]

  # --------- Airflow Metadata DB ---------
  airflow-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - airflow-pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
    networks: [dataplatform]

  # --------- Airflow ---------
  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        airflow db migrate
        airflow users create \
          --username admin --password admin \
          --firstname Admin --lastname User \
          --role Admin --email admin@example.com
    depends_on:
      airflow-db: { condition: service_healthy }

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports: ["8080:8080"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
    depends_on:
      airflow-db: { condition: service_healthy }
      airflow-init: { condition: service_completed_successfully }

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    restart: unless-stopped
    depends_on:
      airflow-db: { condition: service_healthy }
      airflow-init: { condition: service_completed_successfully }

  # --------- dbt ---------
  dbt:
    build: ./dbt
    image: mdp/dbt:latest
    environment:
      DBT_HOST: warehouse-db
      DBT_USER: etl
      DBT_PASSWORD: ${DB_PASSWORD}
      DBT_DB: warehouse_db
    volumes:
      - ./dbt:/dbt
    depends_on:
      warehouse-db: { condition: service_healthy }
    profiles: ["manual"]   # Không tự chạy
    networks: [dataplatform]

  # --------- Jupyter ---------
  jupyter:
    build: ./jupyter
    image: mdp/jupyter:latest
    ports: ["8888:8888"]
    environment:
      JUPYTER_TOKEN: mytoken
      WAREHOUSE_HOST: warehouse-db
      WAREHOUSE_USER: etl
      WAREHOUSE_PASSWORD: ${DB_PASSWORD}
      MINIO_ENDPOINT: http://minio:9000
      MINIO_ACCESS_KEY: admin
      MINIO_SECRET_KEY: ${MINIO_PASSWORD}
    volumes:
      - ./jupyter/notebooks:/home/jovyan/work
    depends_on:
      - warehouse-db
      - minio
    networks: [dataplatform]

volumes:
  source-pgdata:
  warehouse-pgdata:
  airflow-pgdata:
  minio-data:

networks:
  dataplatform:
```

### 26.4. File `.env`

```
DB_PASSWORD=etlpass123
MINIO_PASSWORD=minio123secure
AIRFLOW_UID=50000
```

### 26.5. File `airflow/Dockerfile`

```dockerfile
FROM apache/airflow:2.8.1-python3.11

USER airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres==5.10.0 \
    apache-airflow-providers-amazon==8.16.0 \
    pandas==2.1.4 \
    boto3==1.34.0 \
    minio==7.2.0
```

### 26.6. File `airflow/dags/ingest_csv_to_postgres.py`

```python
"""DAG 1: CSV → Source Postgres"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import os

default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

def ingest_csv(**context):
    csv_path = '/opt/airflow/data/raw/users.csv'
    print(f"Reading {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Read {len(df)} rows")
  
    hook = PostgresHook(postgres_conn_id='postgres_source')
    engine = hook.get_sqlalchemy_engine()
    df.to_sql('users', engine, if_exists='replace', index=False)
    print(f"Loaded {len(df)} rows to source_db.users")

with DAG(
    dag_id='1_ingest_csv_to_postgres',
    default_args=default_args,
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ingest'],
) as dag:
  
    task_ingest = PythonOperator(
        task_id='ingest_csv',
        python_callable=ingest_csv,
    )
```

### 26.7. File `airflow/dags/postgres_to_minio.py`

```python
"""DAG 2: Postgres → MinIO (Parquet)"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import boto3
from io import BytesIO
import os

default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

def extract_and_upload(**context):
    hook = PostgresHook(postgres_conn_id='postgres_source')
    df = hook.get_pandas_df("SELECT * FROM users")
    print(f"Extracted {len(df)} rows")
  
    s3 = boto3.client(
        's3',
        endpoint_url=os.environ['MINIO_ENDPOINT'],
        aws_access_key_id=os.environ['MINIO_ACCESS_KEY'],
        aws_secret_access_key=os.environ['MINIO_SECRET_KEY'],
    )
  
    buf = BytesIO()
    df.to_parquet(buf, index=False)
    buf.seek(0)
  
    ds = context['ds']
    key = f'users/dt={ds}/data.parquet'
    s3.put_object(Bucket='staged', Key=key, Body=buf.read())
    print(f"Uploaded to s3://staged/{key}")

with DAG(
    dag_id='2_postgres_to_minio',
    default_args=default_args,
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['extract'],
) as dag:
  
    PythonOperator(
        task_id='extract_to_minio',
        python_callable=extract_and_upload,
    )
```

### 26.8. File `airflow/dags/minio_to_warehouse.py`

```python
"""DAG 3: MinIO → Warehouse Postgres"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import boto3
from io import BytesIO
import os

default_args = {
    'owner': 'data-team',
    'retries': 2,
}

def load_to_warehouse(**context):
    s3 = boto3.client(
        's3',
        endpoint_url=os.environ['MINIO_ENDPOINT'],
        aws_access_key_id=os.environ['MINIO_ACCESS_KEY'],
        aws_secret_access_key=os.environ['MINIO_SECRET_KEY'],
    )
  
    ds = context['ds']
    key = f'users/dt={ds}/data.parquet'
  
    obj = s3.get_object(Bucket='staged', Key=key)
    df = pd.read_parquet(BytesIO(obj['Body'].read()))
    print(f"Loaded {len(df)} rows from MinIO")
  
    df['loaded_at'] = pd.Timestamp.now()
  
    hook = PostgresHook(postgres_conn_id='postgres_warehouse')
    engine = hook.get_sqlalchemy_engine()
  
    # Create schema raw_data nếu chưa có
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS raw_data")
  
    df.to_sql('users', engine, schema='raw_data', if_exists='replace', index=False)
    print("Loaded to warehouse_db.raw_data.users")

with DAG(
    dag_id='3_minio_to_warehouse',
    default_args=default_args,
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['load'],
) as dag:
  
    PythonOperator(
        task_id='load_to_warehouse',
        python_callable=load_to_warehouse,
    )
```

### 26.9. dbt project

**File: `dbt/Dockerfile`**

```dockerfile
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 DBT_PROFILES_DIR=/dbt/profiles
WORKDIR /dbt
RUN pip install --no-cache-dir dbt-core==1.7.4 dbt-postgres==1.7.4
COPY . .
ENTRYPOINT ["dbt"]
CMD ["run"]
```

**File: `dbt/dbt_project.yml`**

```yaml
name: 'mdp'
version: '1.0.0'
config-version: 2
profile: 'default'

model-paths: ["models"]
test-paths: ["tests"]
seed-paths: ["seeds"]

target-path: "target"
clean-targets: ["target", "dbt_packages"]

models:
  mdp:
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: marts
```

**File: `dbt/profiles/profiles.yml`**

```yaml
default:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('DBT_HOST') }}"
      port: 5432
      user: "{{ env_var('DBT_USER') }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
      dbname: "{{ env_var('DBT_DB') }}"
      schema: analytics
      threads: 4
```

**File: `dbt/models/staging/stg_users.sql`**

```sql
{{ config(materialized='view') }}

SELECT
    id,
    LOWER(TRIM(email)) AS email,
    SPLIT_PART(email, '@', 2) AS email_domain,
    name,
    loaded_at
FROM raw_data.users
WHERE email IS NOT NULL
```

**File: `dbt/models/marts/dim_users.sql`**

```sql
{{ config(materialized='table') }}

SELECT
    id AS user_id,
    email,
    email_domain,
    name,
    CASE
        WHEN email_domain IN ('gmail.com', 'yahoo.com', 'hotmail.com') THEN 'personal'
        ELSE 'business'
    END AS user_type,
    loaded_at,
    CURRENT_TIMESTAMP AS dbt_updated_at
FROM {{ ref('stg_users') }}
```

### 26.10. Sample data

**File: `data/raw/users.csv`**

```csv
id,email,name
1,alice@gmail.com,Alice Smith
2,bob@yahoo.com,Bob Johnson
3,charlie@company.com,Charlie Brown
4,diana@business.org,Diana Prince
5,eve@personal.net,Eve Wilson
```

**File: `data/postgres-init/01_create_schemas.sql`**

```sql
-- Init script cho source_db
CREATE SCHEMA IF NOT EXISTS public;
```

### 26.11. Jupyter

**File: `jupyter/Dockerfile`**

```dockerfile
FROM jupyter/scipy-notebook:latest

RUN pip install --no-cache-dir \
    psycopg2-binary \
    sqlalchemy \
    boto3 \
    minio
```

### 26.12. Quy trình chạy demo

```bash
# 1. Tạo project
mkdir mini-data-platform && cd mini-data-platform
# (copy tất cả file ở trên vào)

# 2. Tạo folder
mkdir -p airflow/dags airflow/logs airflow/plugins
mkdir -p dbt/models/staging dbt/models/marts dbt/profiles
mkdir -p jupyter/notebooks data/raw data/postgres-init

# 3. Set permission cho Airflow
echo "AIRFLOW_UID=$(id -u)" >> .env

# 4. Build images
docker compose build

# 5. Lên stack
docker compose up -d
docker compose ps

# 6. Đợi tất cả healthy (~ 2 phút)
docker compose logs -f airflow-webserver
# Đợi: "Listening at: http://0.0.0.0:8080"

# 7. Mở UI và chạy DAG
# http://localhost:8080 (admin/admin)
# - Enable & trigger DAG '1_ingest_csv_to_postgres'
# - Đợi hoàn thành → trigger DAG '2_postgres_to_minio'
# - Đợi hoàn thành → trigger DAG '3_minio_to_warehouse'

# 8. Chạy dbt
docker compose run --rm dbt run
docker compose run --rm dbt test

# 9. Verify trong warehouse
docker compose exec warehouse-db psql -U etl -d warehouse_db -c "
SELECT * FROM analytics_marts.dim_users;
"

# 10. Mở Jupyter để analysis
# http://localhost:8888 (token: mytoken)
```

### 26.13. Kiểm tra kết quả

**Trong MinIO Console** (http://localhost:9001):

- Bucket `raw`, `staged`, `curated` đều tồn tại
- Bucket `staged` có file `users/dt=YYYY-MM-DD/data.parquet`

**Trong Source Postgres:**

```bash
docker compose exec source-db psql -U etl -d source_db -c "SELECT * FROM users;"
# 5 rows
```

**Trong Warehouse Postgres:**

```bash
docker compose exec warehouse-db psql -U etl -d warehouse_db -c "\dn"
# Schemas: raw_data, analytics_staging, analytics_marts

docker compose exec warehouse-db psql -U etl -d warehouse_db -c "
SELECT * FROM analytics_marts.dim_users;
"
# 5 rows với user_type được phân loại
```

### 26.14. Debug khi có lỗi

```bash
# Tổng quan service nào fail
docker compose ps
docker compose logs --tail 50 SERVICE_NAME

# Vào service debug
docker compose exec airflow-webserver bash

# Test connection từ Airflow tới Postgres
docker compose exec airflow-webserver \
  airflow connections test postgres_source

# Test MinIO
docker compose exec airflow-webserver \
  python -c "
import boto3, os
s3 = boto3.client('s3', endpoint_url=os.environ['MINIO_ENDPOINT'],
                  aws_access_key_id=os.environ['MINIO_ACCESS_KEY'],
                  aws_secret_access_key=os.environ['MINIO_SECRET_KEY'])
print(s3.list_buckets())
"

# Reset stack hoàn toàn
docker compose down -v   # ⚠️ Cũng xóa volume → mất data
docker compose up -d --build
```

### 26.15. Extensions cho bạn tự làm

1. **Thêm Kafka** cho streaming ingest
2. **Thêm Spark** cho transform data lớn hơn
3. **Thêm dbt tests** và `dbt docs`
4. **Thêm Great Expectations** cho data quality
5. **Thêm Trino/Presto** để query MinIO (Iceberg/Hudi format)
6. **CI/CD** GitHub Actions tự build/push image
7. **Metrics**: thêm Prometheus + Grafana monitor
8. **Add Redis** cho Airflow CeleryExecutor để scale worker

---

### ✅ TÓM TẮT CHƯƠNG 26

Bạn vừa build:

- 8 services chạy đồng thời
- Pipeline ETL end-to-end qua Airflow
- Data lake với MinIO (Parquet format)
- Data warehouse 3-tier (raw → staging → marts)
- Transform layer với dbt
- Analytics layer với Jupyter

**Đây là setup tương đương production của nhiều startup data team.**

---

## 🎯 KẾT THÚC PHẦN 7

Bạn đã đến được mốc quan trọng. Tiếp theo: Docker nâng cao, performance, CI/CD.

---

# 📘 PHẦN 8: DOCKER NÂNG CAO

> *Phần này là ranh giới giữa "biết dùng Docker" và "thật sự hiểu Docker". Đây là kiến thức giúp bạn debug production crash lúc 3 giờ sáng, tối ưu CI build từ 20 phút xuống 2 phút, và pass technical interview ở các công ty top.*

---

## 📖 CHƯƠNG 27: IMAGE LAYER & BUILD CACHE DEEP DIVE

### 27.1. Image structure — Mổ xẻ từng phần

Một Docker image **không phải** là một file duy nhất. Nó là một **tập hợp các file được tổ chức theo chuẩn OCI**.

#### Cấu trúc OCI Image

Một OCI image gồm:

```
┌─────────────────────────────────────────────┐
│ Image Manifest (JSON)                       │
│  - schemaVersion                            │
│  - mediaType                                │
│  - config: { digest, size, mediaType }      │
│  - layers: [ { digest, size, mediaType } ]  │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────────┐
        ▼           ▼               ▼
┌──────────┐  ┌──────────┐    ┌──────────┐
│ Config   │  │ Layer 1  │    │ Layer N  │
│ (JSON)   │  │ (tar.gz) │    │ (tar.gz) │
└──────────┘  └──────────┘    └──────────┘
```

#### Demo: xem cấu trúc image

```bash
docker pull alpine:3.19
docker save alpine:3.19 -o alpine.tar
mkdir alpine-extracted && tar xf alpine.tar -C alpine-extracted
cd alpine-extracted
ls
# blobs/  index.json  manifest.json  oci-layout  repositories

cat index.json | jq
# {
#   "schemaVersion": 2,
#   "manifests": [
#     {
#       "mediaType": "application/vnd.oci.image.manifest.v1+json",
#       "digest": "sha256:abc123...",
#       "size": 401
#     }
#   ]
# }

ls blobs/sha256/
# Mỗi file là 1 layer hoặc config
```

→ Bạn vừa **mở Docker image bằng tay** và thấy cấu trúc thật bên trong.

### 27.2. Image config — Metadata

```bash
docker inspect alpine:3.19 --format '{{json .Config}}' | jq
```

Chứa:

- `Cmd`, `Entrypoint`
- `Env`, `WorkingDir`, `User`
- `ExposedPorts`
- `Volumes`
- `Labels`
- `Architecture`, `Os`

Đây là metadata mà Docker daemon dùng để **chạy** container.

### 27.3. Layer caching — Cách Docker quyết định reuse

Docker quyết định cache layer dựa trên **2 tiêu chí**:

#### a) Instruction hash

Docker hash **toàn bộ text của instruction** + base image digest. Đổi 1 ký tự = cache miss.

```dockerfile
RUN apt-get install -y curl     # Hash A
RUN apt-get install -y  curl    # 2 spaces → Hash B (CACHE MISS)
```

#### b) File hash (cho COPY/ADD)

Docker hash **nội dung + metadata** của tất cả file được COPY/ADD. Đổi 1 byte trong file = cache miss.

```dockerfile
COPY requirements.txt .   # Hash dựa trên nội dung requirements.txt
```

#### Cascade invalidation — Hiệu ứng domino

**Quy tắc vàng:** Khi 1 layer invalidate, **TẤT CẢ layer sau** đều invalidate.

```dockerfile
FROM python:3.11-slim       # Layer 1
WORKDIR /app                # Layer 2
COPY requirements.txt .     # Layer 3 — nếu thay đổi
RUN pip install -r req...   # Layer 4 — bị invalidate
COPY . .                    # Layer 5 — bị invalidate
CMD ["python", "main.py"]   # Layer 6 — bị invalidate
```

Đổi requirements.txt → Layer 3, 4, 5, 6 đều rebuild. `pip install` chạy lại (có thể mất 5-10 phút).

#### Hệ quả thực tế — Thứ tự instruction quan trọng

**Sai (cache hiệu suất thấp):**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .                              # ❌ Mọi đổi code → invalidate
RUN pip install -r requirements.txt   # → pip install lại
CMD ["python", "main.py"]
```

**Đúng (cache hiệu suất cao):**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .              # ✅ Chỉ requirements
RUN pip install -r requirements.txt  # ✅ Cache nếu req không đổi
COPY . .                             # ✅ Code đổi không ảnh hưởng pip
CMD ["python", "main.py"]
```

### 27.4. Demo đo cache effectiveness

```bash
# Tạo project test
mkdir cache-test && cd cache-test
echo "pandas==2.1.4" > requirements.txt
echo "print('hello')" > app.py

# Bad Dockerfile
cat > Dockerfile.bad <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EOF

# Good Dockerfile
cat > Dockerfile.good <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EOF

# Build lần đầu
time docker build -f Dockerfile.bad -t bad:v1 .
time docker build -f Dockerfile.good -t good:v1 .

# Đổi code (không đổi requirements)
echo "print('hello v2')" > app.py

# Build lại
time docker build -f Dockerfile.bad -t bad:v2 .    # ~30s (pip install lại)
time docker build -f Dockerfile.good -t good:v2 .  # ~2s (cache hit)
```

Đo thực tế: Tốc độ chênh **10-50 lần** với project lớn.

### 27.5. Cache mount (BuildKit) — Vũ khí bí mật

Cache mount giữ **persistent cache giữa các lần build**, **kể cả khi layer invalidate**.

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .
```

**Cơ chế:** BuildKit mount một volume tạm vào `/root/.cache/pip` trong khi RUN. Sau build, volume vẫn còn (BuildKit lưu lại). Lần build sau, dù invalidate layer này, pip không tải lại packages từ Internet — đã có ở cache.

#### Apt cache mount

```dockerfile
# syntax=docker/dockerfile:1.6
FROM debian:bookworm-slim

# Disable auto-clean để dùng cache mount
RUN rm -f /etc/apt/apt.conf.d/docker-clean

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl
```

#### `sharing` modes

- `shared` (default) — nhiều build có thể đọc/ghi đồng thời
- `private` — mỗi build có cache riêng
- `locked` — chỉ 1 build dùng tại 1 thời điểm (cho apt vì apt lock)

### 27.6. Hidden file size — file bị "đóng băng" trong layer

```dockerfile
RUN apt-get install -y curl                  # +20MB
RUN rm -rf /var/lib/apt/lists/*              # ❌ -10MB nhưng file vẫn ở layer trước!
```

→ Image vẫn to 30MB (20 + 10) chứ không phải 20MB.

**Đúng:**

```dockerfile
RUN apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*              # ✅ Same layer, file không vào layer
```

#### Demo

```bash
# Bad
cat > Dockerfile.fat <<EOF
FROM alpine
RUN dd if=/dev/zero of=/big-file bs=1M count=100
RUN rm /big-file
EOF
docker build -f Dockerfile.fat -t fat .
docker images fat
# SIZE: ~107MB (file vẫn nằm trong layer 1)

# Good
cat > Dockerfile.thin <<EOF
FROM alpine
RUN dd if=/dev/zero of=/big-file bs=1M count=100 && rm /big-file
EOF
docker build -f Dockerfile.thin -t thin .
docker images thin
# SIZE: ~7MB (file không bao giờ vào layer)
```

### 27.7. Analyze image với `dive`

[dive](https://github.com/wagoodman/dive) là tool xem từng layer, phát hiện "fat layer":

```bash
# Cài dive (Linux/Mac)
brew install dive    # Mac
# Linux: download binary

dive python:3.11
# Interactive UI:
# - Bên trái: list layer
# - Bên phải: file thay đổi trong layer đó
# - Hiện "wasted space" (file đã xóa nhưng vẫn trong layer)
```

### 27.8. Squashing layers (KHÔNG khuyến nghị)

Có flag `--squash` để gộp tất cả layer thành 1. KHÔNG dùng vì:

- Mất cache giữa các project (mỗi project = 1 layer khổng lồ).
- Khó debug.

Thay vào đó: **multi-stage build** (Chương 10).

### 27.9. BuildKit history và cache export

```bash
# Xem build cache hiện tại
docker buildx du
# ID            RECLAIMABLE   SIZE
# abc123...     true          1.2GB

# Export cache ra registry (cho CI/CD share cache)
docker buildx build \
  --cache-to=type=registry,ref=myorg/myapp:cache \
  --cache-from=type=registry,ref=myorg/myapp:cache \
  -t myorg/myapp:v1 \
  --push .
```

→ CI/CD lần sau pull cache về, build nhanh hơn nhiều.

---

### ✅ TÓM TẮT CHƯƠNG 27

#### Quy tắc vàng cache

1. **Sắp xếp instruction từ ít thay đổi → nhiều thay đổi**
2. **COPY dependency files TRƯỚC code**
3. **Cleanup CÙNG layer với install** (`RUN install && cleanup`)
4. **Dùng cache mount cho pip/apt** (BuildKit)
5. **Dùng `.dockerignore`** giảm context size

#### Cheat sheet build optimization

| Vấn đề                               | Giải pháp                                  |
| --------------------------------------- | -------------------------------------------- |
| Build chậm vì re-install dependencies | COPY requirements trước, dùng cache mount |
| Image to vì file rác                  | Cleanup cùng RUN                            |
| Build context to                        | `.dockerignore`                            |
| CI cache không share giữa runs        | Export cache to registry                     |
| Image có vulnerabilities               | Slim base + scan thường xuyên             |

---

## 📖 CHƯƠNG 28: BUILDKIT, BUILDX, MULTI-PLATFORM

### 28.1. BuildKit là gì?

**BuildKit** là build engine thế hệ mới của Docker. Từ Docker Engine 23.0+, BuildKit là **default**.

So với legacy builder:

| Feature                | Legacy | BuildKit              |
| ---------------------- | ------ | --------------------- |
| Parallel layer build   | ❌     | ✅                    |
| Cache mount            | ❌     | ✅                    |
| Secret mount           | ❌     | ✅                    |
| SSH forwarding         | ❌     | ✅                    |
| Multi-platform         | ❌     | ✅                    |
| Inline frontend syntax | ❌     | ✅ (`# syntax=...`) |
| Better cache export    | ❌     | ✅                    |
| SBOM generation        | ❌     | ✅                    |

**Bật BuildKit (nếu cần):**

```bash
DOCKER_BUILDKIT=1 docker build ...
# Hoặc set permanent:
# /etc/docker/daemon.json
# { "features": { "buildkit": true } }
```

### 28.2. Frontend syntax — Mở rộng Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.6
```

Dòng đầu tiên của Dockerfile (comment đặc biệt). BuildKit hiểu dòng này và pull frontend version cụ thể → enable features mới.

Versions thông dụng:

- `docker/dockerfile:1` — latest stable
- `docker/dockerfile:1.6` — pin minor

### 28.3. Heredoc trong RUN (BuildKit 1.4+)

```dockerfile
# syntax=docker/dockerfile:1.6
FROM debian:bookworm-slim

RUN <<EOF
set -eux
apt-get update
apt-get install -y --no-install-recommends \
    curl \
    libpq5
rm -rf /var/lib/apt/lists/*
EOF
```

Cleaner hơn `RUN cmd1 && \ cmd2 && \ cmd3`.

### 28.4. `docker buildx` — CLI multi-builder

`buildx` là plugin CLI cho phép quản lý nhiều builder, build multi-platform, export sang nhiều format.

```bash
# Xem builders hiện tại
docker buildx ls

# Tạo builder mới
docker buildx create --name mybuilder --use

# Inspect
docker buildx inspect mybuilder
```

### 28.5. Multi-platform build

#### Vấn đề

- Máy bạn: Mac M1 (ARM64).
- Server production: x86_64 (AMD64).
- Build trên Mac → image ARM → không chạy được trên server x86.

#### Giải pháp: Cross-compile bằng QEMU

```bash
# Cài QEMU emulator
docker run --privileged --rm tonistiigi/binfmt --install all

# Build cho cả 2 platform
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myorg/myapp:v1 \
  --push .
```

BuildKit dùng QEMU để emulate platform khác, build cả 2 → push lên registry như **một image manifest list**.

Khi pull, Docker tự chọn platform phù hợp:

```bash
docker pull myorg/myapp:v1     # Tự chọn theo host
```

#### Verify manifest

```bash
docker buildx imagetools inspect myorg/myapp:v1
# Name:      docker.io/myorg/myapp:v1
# MediaType: application/vnd.docker.distribution.manifest.list.v2+json
# 
# Manifests:
#   Name:      myorg/myapp:v1@sha256:...
#   Platform:  linux/amd64
#   
#   Name:      myorg/myapp:v1@sha256:...
#   Platform:  linux/arm64
```

#### Build chỉ 1 platform khác máy

```bash
docker buildx build \
  --platform linux/amd64 \
  -t myapp:linux-amd64 \
  --load .   # Load vào local image store
```

### 28.6. ARM vs AMD64 — Pitfalls cho Data Engineer

#### a) Một số image **không có** ARM variant

```bash
docker pull mssql/server   # ❌ Chỉ có x86_64
```

Khi chạy trên Mac M1 → Docker emulate → **cực chậm**.

**Workaround:**

```bash
docker pull --platform linux/amd64 mssql/server
docker run --platform linux/amd64 mssql/server
```

Hoặc check trước:

```bash
docker manifest inspect IMAGE | grep architecture
```

#### b) Python package binary wheel

Nhiều package C-extension (pandas, numpy, psycopg2) có pre-built wheel cho cả AMD64 và ARM64. Nhưng một số ít chỉ có AMD64 → trên ARM phải compile từ source → chậm.

**Solutions:**

- Dùng `--platform linux/amd64` (emulation, chậm runtime)
- Dùng image ARM-native (nếu có)
- Build wheels từ source (slow build, fast runtime)

#### c) JVM (Spark, Kafka)

Java có ARM64 build từ lâu. Spark/Kafka đều chạy ARM64 native — performance tốt.

### 28.7. Cache export/import — CI/CD optimization

```bash
# Build với cache export
docker buildx build \
  --cache-to=type=registry,ref=myorg/myapp:buildcache,mode=max \
  --cache-from=type=registry,ref=myorg/myapp:buildcache \
  -t myorg/myapp:v1 \
  --push .
```

`mode=max` — export tất cả intermediate layer (cache lớn nhưng tận dụng tối đa).
`mode=min` — chỉ export final layer (cache nhỏ).

**CI/CD pattern điển hình:**

```yaml
# .github/workflows/build.yml
- uses: docker/setup-buildx-action@v3
- uses: docker/build-push-action@v5
  with:
    push: true
    tags: myorg/myapp:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

`type=gha` — GitHub Actions Cache (built-in, free).

### 28.8. Inline cache

```bash
docker buildx build \
  --cache-to=type=inline \
  -t myorg/myapp:v1 \
  --push .

# Pull về máy khác, dùng cache từ image:
docker buildx build \
  --cache-from=myorg/myapp:v1 \
  -t myorg/myapp:v2 \
  --push .
```

Cache được "nhúng" vào image manifest. Tiện nhưng cache nhỏ hơn `mode=max`.

### 28.9. Output types

BuildKit có thể output build ra nhiều format:

```bash
# Default: docker image
docker buildx build -t myapp .

# OCI tarball
docker buildx build -o type=oci,dest=myapp.tar .

# Filesystem extracted
docker buildx build -o type=local,dest=./output .

# Push to registry
docker buildx build -t myorg/myapp -o type=registry .
```

### 28.10. Multi-platform với Data Engineering

Cho data project, thường build dual-arch:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --cache-from=type=registry,ref=myorg/etl:cache \
  --cache-to=type=registry,ref=myorg/etl:cache,mode=max \
  -t myorg/etl:v1.2.3 \
  --push .
```

→ Engineer dùng Mac M1 dev, server x86 chạy production — same image tag.

---

### ✅ TÓM TẮT CHƯƠNG 28

#### Cheat sheet buildx

```bash
# Setup
docker buildx create --name builder --use

# Build single platform, load local
docker buildx build -t myapp:v1 --load .

# Build multi-platform, push registry
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:v1 --push .

# Build with registry cache
docker buildx build \
  --cache-from=type=registry,ref=myapp:cache \
  --cache-to=type=registry,ref=myapp:cache,mode=max \
  -t myapp:v1 --push .

# Inspect manifest
docker buildx imagetools inspect myapp:v1
```

#### Câu hỏi tự kiểm tra

1. BuildKit khác legacy builder ở những điểm nào?
2. Vì sao Mac M1 chạy MSSQL container chậm?
3. Cache mount khác layer cache thế nào?
4. `mode=max` vs `mode=min` cache export?
5. Khi nào dùng multi-platform build?

---

## 📖 CHƯƠNG 29: REGISTRY, TAGGING, SECURITY

### 29.1. Registry private — Tự host

#### Docker Registry official

```bash
# Chạy registry local
docker run -d -p 5000:5000 --name registry registry:2

# Tag image cho local registry
docker tag myapp:v1 localhost:5000/myapp:v1
docker push localhost:5000/myapp:v1

# Pull từ registry khác máy:
docker pull <host-ip>:5000/myapp:v1
```

Cho production, dùng:

- **Harbor** — open-source, có UI, vulnerability scan, RBAC
- **Nexus**, **JFrog Artifactory** — enterprise
- **Cloud**: AWS ECR, GCP Artifact Registry, Azure ACR
- **GitHub**: ghcr.io (free for public)

### 29.2. Docker login

```bash
# Docker Hub
docker login                       # username/password
docker login -u USER --password-stdin   # Từ env (an toàn hơn)

# GHCR
docker login ghcr.io -u USER -p TOKEN

# ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456.dkr.ecr.us-east-1.amazonaws.com

# GAR
gcloud auth configure-docker us-central1-docker.pkg.dev
```

Credentials lưu trong `~/.docker/config.json` (encoded). Trên Mac, có thể tích hợp keychain.

### 29.3. Tagging strategy — Cực quan trọng

#### ❌ Anti-pattern

```bash
docker push myorg/etl:latest      # Không reproducible
docker push myorg/etl:prod        # Vẫn không reproducible
```

#### ✅ Patterns tốt

**1. Semantic versioning (SemVer):**

```
myorg/etl:1.2.3       # Major.Minor.Patch
myorg/etl:1.2         # Latest 1.2.x
myorg/etl:1           # Latest 1.x.x
myorg/etl:latest      # Latest release
```

**2. Git SHA:**

```
myorg/etl:sha-abc1234       # Immutable, traceable
myorg/etl:main-abc1234      # Branch + SHA
```

**3. Timestamp:**

```
myorg/etl:20240518-153022   # Build time
```

**4. Combo (recommended for production):**

```bash
docker buildx build \
  -t myorg/etl:v1.2.3 \
  -t myorg/etl:v1.2 \
  -t myorg/etl:v1 \
  -t myorg/etl:sha-${GIT_SHA} \
  -t myorg/etl:latest \
  --push .
```

→ Có cả semantic version, cả git SHA, cả "latest".

### 29.4. Digest pinning — Reproducibility tuyệt đối

Tag có thể bị overwrite. Digest **không thể**.

```bash
# Pin trong Dockerfile
FROM python:3.11.7-slim@sha256:abc123def456...

# Pin trong compose:
services:
  postgres:
    image: postgres:15.4-alpine@sha256:abc...
```

**Tool: `crane`** để lấy digest:

```bash
crane digest postgres:15.4-alpine
# sha256:abc...
```

### 29.5. Image promotion — Dev → Staging → Prod

```
Dev build           → myorg/etl:sha-abc1234
                      myorg/etl:dev
Test pass           → tag thêm: myorg/etl:staging
Prod deploy approval → tag thêm: myorg/etl:v1.2.3, myorg/etl:prod
```

**Quy tắc:** **KHÔNG rebuild image khi promote** — chỉ retag.

```bash
docker pull myorg/etl:sha-abc1234
docker tag myorg/etl:sha-abc1234 myorg/etl:v1.2.3
docker push myorg/etl:v1.2.3
```

→ Image đi qua tất cả environment là **đúng image binary**, đảm bảo "build once, deploy anywhere".

### 29.6. SBOM — Software Bill of Materials

SBOM = danh sách tất cả thành phần (packages, dependencies, versions) trong image.

```bash
# Build với SBOM
docker buildx build --sbom=true -t myapp:v1 --push .

# Xem SBOM
docker sbom myapp:v1
# Hoặc:
docker buildx imagetools inspect myapp:v1 --format '{{ json .SBOM }}'
```

**Use case:**

- Audit (compliance: SOC2, ISO 27001)
- Vulnerability tracking (khi 1 lib có CVE, biết image nào affected)

Tool: `syft` (generate), `grype` (scan).

### 29.7. Vulnerability scanning

#### Docker Scout (built-in)

```bash
docker scout cves myapp:v1
# Hiển thị các CVE trong image

docker scout recommendations myapp:v1
# Đề xuất base image nâng cấp
```

#### Trivy (open-source, phổ biến nhất)

```bash
# Cài trivy:  https://aquasecurity.github.io/trivy/

trivy image myapp:v1
# Liệt kê vuln, severity, fixed version

trivy image --severity HIGH,CRITICAL myapp:v1
# Chỉ vuln nguy hiểm

trivy image --exit-code 1 --severity CRITICAL myapp:v1
# Fail CI nếu có CRITICAL
```

#### Grype

```bash
grype myapp:v1
grype myapp:v1 --fail-on critical
```

#### Pattern CI

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myorg/myapp:${{ github.sha }}
    exit-code: 1
    severity: CRITICAL,HIGH
```

### 29.8. Image signing — Đảm bảo image không bị "đánh tráo"

**Cosign** (Sigstore project):

```bash
# Generate keypair
cosign generate-key-pair

# Sign image
cosign sign --key cosign.key myorg/myapp:v1

# Verify
cosign verify --key cosign.pub myorg/myapp:v1
```

Production: integrate vào CI/CD, deploy chỉ pull signed images.

### 29.9. Secrets — Đừng để leak vào image

#### ❌ Anti-patterns

```dockerfile
# ❌ Hardcode
ENV API_KEY=sk-abc123

# ❌ Build args (vẫn lưu vào history)
ARG API_KEY
RUN curl -H "Auth: $API_KEY" ...

# ❌ COPY file secret
COPY .env /app/
```

Tất cả đều bị lộ qua `docker history` hoặc layer inspection.

#### ✅ BuildKit secret mount

```dockerfile
# syntax=docker/dockerfile:1.6
RUN --mount=type=secret,id=api_key \
    API_KEY=$(cat /run/secrets/api_key) && \
    curl -H "Auth: $API_KEY" https://api.example.com/setup
```

```bash
docker build --secret id=api_key,src=$HOME/.api_key -t myapp .
# Hoặc từ env:
docker build --secret id=api_key,env=API_KEY -t myapp .
```

Secret **không lưu vào layer**.

#### ✅ Runtime secrets

```bash
# Đơn giản
docker run -e API_KEY=$API_KEY myapp

# Compose
services:
  app:
    env_file: .env.secret   # Không commit
```

#### ✅ External secret managers

- **HashiCorp Vault**
- **AWS Secrets Manager** — app pull lúc startup
- **Kubernetes Secrets** (production K8s)
- **Doppler**, **1Password CLI** — dev workflow

### 29.10. Image attack surface

Layer của image có thể bị attacker đào:

```bash
# Attacker pull image, extract:
docker pull myorg/myapp:v1
docker save myorg/myapp:v1 -o app.tar
mkdir extracted && tar xf app.tar -C extracted
ls extracted/blobs/sha256/
# Mỗi blob có thể extract, đọc nội dung
```

→ **NHỚ:** image public = source code public. Đừng để secret nào trong image.

---

### ✅ TÓM TẮT CHƯƠNG 29

#### Security checklist trước khi push image

- [ ] Không có secret trong Dockerfile/ENV
- [ ] Không có file `.env`, `.aws/credentials`, `id_rsa` trong image
- [ ] Đã scan vulnerabilities (Trivy/Grype/Scout)
- [ ] Non-root user
- [ ] Pin version cụ thể
- [ ] Có tag SemVer + Git SHA
- [ ] (Optional) Signed image
- [ ] Có SBOM
- [ ] Resource limit khi run

#### Tagging strategy

```
v1.2.3 (immutable, prod)
v1.2 (rolling minor)
v1 (rolling major)
sha-abc1234 (immutable, ref)
latest (rolling, dev only)
```

---

## 📖 CHƯƠNG 30: RESOURCE LIMITS, HEALTHCHECK, OBSERVABILITY

### 30.1. Resource limits — Đừng bao giờ bỏ qua

#### Memory

```bash
docker run \
  --memory=2g \                # Hard limit 2GB
  --memory-reservation=1g \    # Soft limit (giảm khi host stress)
  --memory-swap=2g \           # Total memory + swap = 2g (không cho swap)
  --oom-kill-disable=false \   # Cho phép OOM kill (default)
  myapp
```

**Behavior khi vượt:**

- `--memory` đạt → kernel OOM kill PID 1 → container exit 137.
- `--memory-swap` = `--memory` → không swap, OOM nhanh.
- `--memory-swap` > `--memory` → cho phép swap (chậm nhưng không die).

#### CPU

```bash
docker run \
  --cpus=1.5 \                  # 1.5 cores
  --cpu-shares=512 \            # Relative weight (default 1024)
  --cpuset-cpus=0,2 \           # Chỉ chạy trên CPU 0 và 2
  myapp
```

**`--cpus` vs `--cpu-shares`:**

- `--cpus`: Hard cap. Container không vượt qua giới hạn này.
- `--cpu-shares`: Weight. Khi host stress, container có shares cao được nhiều CPU hơn.

#### PIDs

```bash
docker run --pids-limit=100 myapp
# Tối đa 100 process — phòng fork bomb
```

#### Block IO

```bash
docker run \
  --blkio-weight=500 \             # Weight 10-1000
  --device-read-bps=/dev/sda:1mb \  # Đọc max 1MB/s
  --device-write-bps=/dev/sda:1mb \
  myapp
```

### 30.2. Compose resource limits

```yaml
services:
  spark-worker:
    image: bitnami/spark:3.5
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

Hoặc cú pháp ngắn (Compose v2 cũng accept):

```yaml
    mem_limit: 4g
    mem_reservation: 2g
    cpus: 2
```

### 30.3. Quan sát resource usage

```bash
# Real-time
docker stats

# 1 lần
docker stats --no-stream

# Format
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# JSON cho parse
docker stats --no-stream --format "{{json .}}" | jq
```

### 30.4. Healthcheck — Đúng cách

#### Dockerfile

```dockerfile
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=60s \
            --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1
```

**Tham số:**

- `--interval` — Tần suất check (default 30s)
- `--timeout` — Timeout cho mỗi check (default 30s)
- `--start-period` — Grace period khi mới start (failed check trong period này không tính). Quan trọng cho app slow start (Java, Airflow).
- `--retries` — Số lần fail liên tiếp trước khi đánh "unhealthy"

#### Healthcheck đúng cho từng service

**Web app HTTP:**

```dockerfile
HEALTHCHECK CMD curl -fsS http://localhost:8000/health || exit 1
```

**PostgreSQL:**

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s
  timeout: 5s
  retries: 5
```

**MySQL:**

```yaml
healthcheck:
  test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
```

**Redis:**

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
```

**Kafka:**

```yaml
healthcheck:
  test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092 || exit 1"]
  interval: 30s
  start_period: 60s
```

#### Healthcheck SAI lầm phổ biến

❌ **Healthcheck chỉ kiểm tra process tồn tại:**

```dockerfile
HEALTHCHECK CMD ps aux | grep python || exit 1
```

→ Process có thể tồn tại nhưng deadlock, không serve được.

❌ **Healthcheck quá nặng:**

```dockerfile
HEALTHCHECK CMD curl http://localhost/expensive-query
```

→ Mỗi 30s gọi query expensive → tải DB không cần thiết.

✅ **Healthcheck endpoint nhẹ, kiểm tra connectivity quan trọng:**

```python
# /health endpoint trong app
def health():
    # Quick DB ping
    db.execute("SELECT 1")
    # Return 200
```

### 30.5. Exit codes — Hiểu mã thoát

| Exit code | Ý nghĩa                          |
| --------- | ---------------------------------- |
| 0         | Success                            |
| 1         | General error                      |
| 2         | Misuse of shell builtins           |
| 125       | Docker daemon error                |
| 126       | Container command not executable   |
| 127       | Container command not found        |
| 137       | SIGKILL (OOM hoặc`docker kill`) |
| 139       | SIGSEGV (segfault)                 |
| 143       | SIGTERM (`docker stop`)          |

**Use case:** Airflow operator nhận exit code → retry hay alert.

### 30.6. Logging

#### Log driver

Default: `json-file`. Log lưu vào `/var/lib/docker/containers/<id>/<id>-json.log`.

**Drivers khác:**

- `journald` — systemd journal (Linux)
- `syslog` — syslog server
- `fluentd` — fluentd forward
- `awslogs` — AWS CloudWatch
- `gcplogs` — GCP Logging
- `splunk`, `loki`, `gelf`

```bash
docker run --log-driver=json-file \
  --log-opt max-size=10m \
  --log-opt max-file=5 \
  myapp
```

#### Log rotation (BẮT BUỘC cho production)

`/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "10",
    "compress": "true"
  }
}
```

→ Restart Docker để áp dụng.

#### Centralized logging pattern

```yaml
services:
  app:
    image: myapp
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        loki-retries: "5"
        loki-batch-size: "400"

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
```

App log → Loki → Grafana visualize. Production pattern phổ biến.

### 30.7. Metrics & monitoring

#### Docker stats API

```bash
# Stats raw
docker stats --no-stream --format "{{json .}}" | jq

# Hoặc qua API
curl --unix-socket /var/run/docker.sock http://localhost/containers/CONTAINER/stats?stream=false | jq
```

#### cAdvisor — Google's container monitoring

```yaml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports: ["8080:8080"]
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
```

→ http://localhost:8080 — UI hiển thị CPU/RAM/Net/IO của từng container.

#### Prometheus + Grafana stack

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports: ["9090:9090"]

  cadvisor:
    image: gcr.io/cadvisor/cadvisor
    # ... (như trên)

  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]
```

`prometheus.yml`:

```yaml
scrape_configs:
  - job_name: cadvisor
    static_configs:
      - targets: [cadvisor:8080]
```

→ Prometheus scrape cAdvisor → Grafana dashboard.

### 30.8. Restart policies — Production essentials

```bash
docker run --restart=POLICY ...
```

| Policy             | Behavior                                          |
| ------------------ | ------------------------------------------------- |
| `no` (default)   | Không restart                                    |
| `on-failure[:N]` | Restart khi exit code != 0, max N lần            |
| `always`         | Luôn restart (kể cả khi Docker daemon restart) |
| `unless-stopped` | Restart trừ khi user`docker stop`              |

**Khuyến nghị:**

- Service production: `unless-stopped`
- Batch job: `on-failure:3` (retry vài lần rồi thôi)
- Dev container: `no`

### 30.9. Stop timeout

```bash
docker run --stop-timeout=30 ...
# Docker đợi 30s trước SIGKILL (default 10s)
```

Quan trọng cho long-running data job — đủ thời gian flush state.

---

### ✅ TÓM TẮT CHƯƠNG 30

#### Checklist production container

- [ ] Resource limits (`--memory`, `--cpus`)
- [ ] Healthcheck phù hợp với service
- [ ] Log rotation (max-size, max-file)
- [ ] Restart policy (`unless-stopped`)
- [ ] Non-root user
- [ ] Stop timeout cho graceful shutdown
- [ ] Monitoring (cAdvisor + Prometheus + Grafana)
- [ ] Centralized logging

---

## 📖 CHƯƠNG 31: DEBUG NHƯ MỘT CHUYÊN GIA

> *Đây là chương biến bạn từ "Google mỗi lỗi" thành "debug có hệ thống". Sau chương này, lỗi Docker với bạn là một cuộc đối thoại, không phải câu đố.*

### 31.1. Triết lý debug Docker

**Quy trình 4 bước:**

```
1. OBSERVE  →  Quan sát triệu chứng cụ thể
2. ISOLATE  →  Xác định layer/component có vấn đề
3. HYPOTHESIZE → Đoán nguyên nhân, validate
4. FIX     →  Sửa và verify
```

**Các "tầng" mà lỗi có thể xảy ra:**

```
1. Build time      ← Dockerfile, build context, registry
2. Image           ← Layer, dependencies, file content
3. Container start ← Command, ENTRYPOINT, image config
4. Runtime         ← App code, env vars, mounts, network
5. Network         ← DNS, port, firewall
6. Resource        ← OOM, CPU throttle, disk full
```

### 31.2. Debug container crash

#### Bước 1: Container exit gì?

```bash
docker ps -a
# CONTAINER ID   IMAGE   STATUS                       NAMES
# abc123        myapp   Exited (137) 2 minutes ago   myapp
```

**Exit code cho biết loại lỗi:**

- `0` — Success (nhưng container chạy xong → bình thường cho batch job)
- `1` — App error chung (Python exception, etc.)
- `137` — SIGKILL (thường là OOM)
- `139` — Segfault
- `143` — SIGTERM (`docker stop`)

#### Bước 2: Logs nói gì?

```bash
docker logs abc123
docker logs --tail 200 --timestamps abc123
docker logs abc123 2>&1 | grep -i error
```

#### Bước 3: Nếu logs không đủ → chạy lại với debug

```bash
# Chạy trực tiếp shell thay vì CMD app
docker run --rm -it --entrypoint sh IMAGE
# → Vào shell, manually chạy app, xem lỗi

# Hoặc keep container alive sau exit
docker run -d --name dead-app myapp
docker exec dead-app cat /var/log/...
```

#### Case study 1: OOM kill (exit 137)

**Triệu chứng:** Container exit 137, log thường không có gì rõ ràng (kernel kill, không phải app).

**Debug:**

```bash
# Check dmesg trên host
sudo dmesg | grep -i oom
# Sẽ thấy: "Out of memory: Killed process 12345 (python)"

# Check memory limit
docker inspect abc123 | grep -i memory
# Memory: 268435456  (256MB)
```

**Fix:**

- Tăng `--memory`
- Optimize app (giảm dataset, chunked processing)
- Add `--memory-swap` lớn hơn để cho phép swap

#### Case study 2: Container exit ngay, không log

```bash
docker run --name app myimage
docker ps -a
# Exited (127) 0 seconds ago
docker logs app
# /bin/sh: app.py: command not found
```

**Nguyên nhân:** Exit 127 = command not found. CMD/ENTRYPOINT trong Dockerfile sai.

**Fix:**

```bash
# Override entrypoint để debug
docker run --rm -it --entrypoint sh myimage
# Vào shell, kiểm tra:
ls /app
which python
echo $PATH
```

### 31.3. Debug image build fail

#### Pattern: Build fail ở layer cụ thể

```bash
docker build -t myapp .
# ...
# Step 5/10 : RUN pip install -r requirements.txt
# ERROR: Could not find a version that satisfies the requirement...
# The command '/bin/sh -c pip install -r requirements.txt' returned a non-zero code: 1
```

**Debug:**

**1. Inspect intermediate layer trước layer fail:**

BuildKit (default) không expose intermediate image trực tiếp. Workaround:

```bash
# Build đến trước layer fail
docker build --target STAGE_NAME -t debug:partial .

# Hoặc dùng `RUN` debug ngay trước
# Trong Dockerfile thêm tạm:
RUN ls -la /app
RUN cat /app/requirements.txt
# Rồi build lại
```

**2. Tách build context:**

```bash
docker run --rm -it -v $(pwd):/app -w /app python:3.11-slim sh
# Vào shell, manually thực hiện từng bước Dockerfile
# Xem chỗ nào fail
```

**3. Verbose build:**

```bash
docker build --progress=plain --no-cache -t myapp .
# --progress=plain hiển thị output đầy đủ (không bị truncate)
```

#### Case study: `pip install` fail trong build

```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Nguyên nhân thường gặp:**

1. Build chạy as non-root nhưng cài vào system path
2. Cache directory không writable

**Fix:**

```dockerfile
# Cài vào user dir
RUN pip install --user -r requirements.txt

# Hoặc cài system với root (trước USER directive):
USER root
RUN pip install -r requirements.txt
USER app
```

### 31.4. Debug permission issues

**Triệu chứng:** App trong container ghi file → error `Permission denied`.

**Phân tích:**

```bash
# Trong container
docker exec -it app sh
ls -la /data
# drwxr-xr-x  2 root root  4096 May 18 10:00 .
# App chạy as user 'app' (UID 1000) nhưng /data thuộc root
```

**Fix 1:** Chown trong Dockerfile:

```dockerfile
RUN mkdir /data && chown -R app:app /data
USER app
```

**Fix 2:** Chown khi mount volume (compose):

```yaml
services:
  app:
    image: myapp
    user: "1000:1000"
    volumes:
      - data:/data
```

**Fix 3 (bind mount):** UID match:

```bash
docker run -u $(id -u):$(id -g) -v $(pwd)/data:/data myapp
```

### 31.5. Debug port conflict

```bash
docker run -d -p 8080:80 nginx
# docker: Error response from daemon: driver failed programming external connectivity:
# Bind for 0.0.0.0:8080 failed: port is already allocated.
```

**Tìm thủ phạm:**

```bash
# Linux/Mac
sudo lsof -i :8080
# Hoặc:
sudo ss -tlnp | grep 8080
# Hoặc Docker:
docker ps --filter "publish=8080"
```

**Fix:**

- Đổi host port: `-p 8081:80`
- Kill app đang chiếm port
- Stop container Docker đang chiếm port

### 31.6. Debug DNS/network issue

#### Pattern: Container A không kết nối Container B

```bash
docker exec app ping db
# ping: bad address 'db'
```

**Debug systematic:**

```bash
# 1. Cùng network?
docker inspect app --format '{{json .NetworkSettings.Networks}}' | jq
docker inspect db --format '{{json .NetworkSettings.Networks}}' | jq
# Phải có network giống nhau

# 2. Container đang chạy?
docker ps | grep db

# 3. DNS resolve?
docker exec app nslookup db
docker exec app cat /etc/resolv.conf

# 4. Port mở?
docker exec app nc -zv db 5432
# OR:
docker exec app sh -c "timeout 2 bash -c '</dev/tcp/db/5432' && echo open || echo closed"
```

**Fix:**

```bash
# Đảm bảo cùng network
docker network connect mynet app
docker network connect mynet db

# Hoặc với compose: dùng cùng project, services tự chung network.
```

#### Pattern: Container không reach internet

```bash
docker run --rm alpine ping 8.8.8.8
# Timeout
```

**Debug:**

```bash
# Check default route
docker run --rm alpine ip route
# default via 172.17.0.1 dev eth0

# Check DNS
docker run --rm alpine nslookup google.com
# Nếu fail → DNS issue
```

**Fix:** Daemon config DNS:

```json
// /etc/docker/daemon.json
{
  "dns": ["8.8.8.8", "1.1.1.1"]
}
```

### 31.7. Debug volume mount issue

```bash
# Test volume mount
docker run --rm -v $(pwd)/data:/data alpine ls -la /data
```

**Common issues:**

| Triệu chứng                               | Nguyên nhân                     | Fix                                |
| ------------------------------------------- | --------------------------------- | ---------------------------------- |
| Path mount tạo thư mục thay vì file     | File host không tồn tại        | Tạo file trước khi mount        |
| File trong container không thấy host file | Path sai                          | Dùng absolute path`$(pwd)/...`  |
| Permission denied                           | UID mismatch                      | `-u $(id -u):$(id -g)`           |
| Empty mount (Mac)                           | Docker Desktop chưa share folder | Cấu hình File Sharing            |
| Mount chậm cực kỳ (Mac/Win)              | OverlayFS overhead                | Dùng named volume thay bind mount |

### 31.8. Debug bằng `docker inspect`

```bash
# Container đầy đủ
docker inspect CONTAINER | less

# Specific field
docker inspect --format '{{.State.Status}}' app
docker inspect --format '{{.State.Health.Status}}' app
docker inspect --format '{{json .HostConfig.Mounts}}' app | jq
docker inspect --format '{{json .NetworkSettings.Networks}}' app | jq

# Logs về health checks
docker inspect --format '{{json .State.Health}}' app | jq
# {
#   "Status": "unhealthy",
#   "Log": [
#     {"Start": "...", "ExitCode": 1, "Output": "..."}
#   ]
# }
```

### 31.9. Debug với `nsenter` (Linux only, advanced)

```bash
# Lấy PID container trên host
PID=$(docker inspect --format '{{.State.Pid}}' app)

# Vào network namespace của container (tools host)
sudo nsenter -t $PID -n bash
# Bây giờ shell host nhưng dùng network namespace của container
# tcpdump, ss, ip... có sẵn của host
tcpdump -i eth0
exit

# Vào tất cả namespaces:
sudo nsenter -t $PID -m -u -i -n -p bash
```

### 31.10. Debug với `tcpdump`

```bash
# Cài vào container có sẵn tcpdump (nicolaka/netshoot)
docker run --rm -it --network=container:app nicolaka/netshoot
# Trong netshoot:
tcpdump -i eth0 port 5432
# Quan sát traffic vào/ra DB

# Hoặc share network với host:
docker run --rm -it --network=host nicolaka/netshoot
tcpdump -i any port 8080
```

### 31.11. Disk full

```bash
docker system df
# TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
# Images          25      5        12.3GB    9.8GB (79%)
# Containers      8       3        450MB     200MB (44%)
# Local Volumes   15      4        5.2GB     3.1GB (59%)
# Build Cache     0       0        15.4GB    15.4GB (100%)

# Cleanup
docker system prune -a              # Stopped containers + unused image
docker volume prune                  # Unused volumes
docker buildx prune                  # Build cache
docker system prune -a --volumes     # ⚠️ Cẩn thận
```

### 31.12. Debug toolkit recommended

| Tool                  | Use case                     |
| --------------------- | ---------------------------- |
| `docker logs`       | Logs container               |
| `docker inspect`    | Metadata, config             |
| `docker stats`      | Resource usage               |
| `docker exec`       | Vào container debug         |
| `docker diff`       | File changes trong container |
| `nicolaka/netshoot` | Network debug toolkit        |
| `dive`              | Layer analysis               |
| `trivy`             | Vulnerability scan           |
| `ctop`              | Top-like UI cho containers   |
| `lazydocker`        | TUI manage Docker            |

### 31.13. Lab debug — Tự rèn luyện

#### Bài 1: Tạo lỗi OOM và debug

```bash
docker run --memory=50m alpine sh -c "yes | head -c 200M > /tmp/x"
# Container chết với 137
docker ps -a
docker logs <id>
sudo dmesg | grep -i oom
```

#### Bài 2: Tạo lỗi network và debug

```yaml
# Bad compose: 2 service không cùng network
services:
  app:
    image: alpine
    command: sh -c "while true; do nslookup db; sleep 2; done"
    networks: [net1]
  db:
    image: alpine
    networks: [net2]
networks:
  net1:
  net2:
```

→ `docker compose logs app` thấy `nslookup` fail → fix bằng cách đặt vào cùng network.

#### Bài 3: Tạo lỗi permission

```bash
mkdir testdir
docker run --rm -v $(pwd)/testdir:/data alpine sh -c "touch /data/file && ls -la /data"
ls -la testdir/file
# Owner: root
rm testdir/file
# Permission denied!

# Fix:
docker run --rm -u $(id -u):$(id -g) -v $(pwd)/testdir:/data alpine sh -c "touch /data/file2"
ls -la testdir/file2
# Owner: bạn (UID 1000)
```

---

### ✅ TÓM TẮT CHƯƠNG 31

#### Debug workflow chuẩn

```
1. docker ps -a              → Container status?
2. docker logs --tail 200    → Logs nói gì?
3. docker inspect            → Config đúng?
4. docker exec sh            → Vào container debug
5. docker stats              → Resource OK?
6. docker network inspect    → Network OK?
7. Recreate                  → Last resort
```

#### Lỗi → Diagnosis → Fix bảng cheat

| Triệu chứng                  | Tools                            | Fix phổ biến              |
| ------------------------------ | -------------------------------- | --------------------------- |
| Exit 137                       | `dmesg`, `docker stats`      | Tăng`--memory`           |
| Exit 127                       | `docker logs`                  | Sửa CMD/ENTRYPOINT         |
| Exit 1                         | `docker logs`                  | Đọc traceback app         |
| Port allocated                 | `lsof`, `docker ps`          | Đổi port, kill app        |
| Permission denied trên volume | `ls -la`                       | Chown hoặc`-u UID:GID`   |
| Container không reach DB      | `nslookup`, `nc`             | Cùng network, service name |
| Build chậm                    | `--progress=plain`             | Cache mount, đổi thứ tự |
| Disk full                      | `docker system df`             | `docker system prune -a`  |
| Container unhealthy            | `docker inspect .State.Health` | Sửa healthcheck command    |

#### Câu hỏi tự kiểm tra

1. Exit code 137 nghĩa là gì? Phân biệt với 143?
2. Khi container không kết nối được DB, debug step nào trước tiên?
3. Vì sao bind mount tạo thư mục thay vì file?
4. `docker diff` cho biết gì?
5. `nsenter` dùng để làm gì?

---

## 🎯 KẾT THÚC PHẦN 8

Phần 8 đã trang bị cho bạn kỹ năng "đào sâu" Docker — từ build cache deep dive, BuildKit advanced features, security hardening, đến debug systematic. Đây là kiến thức của senior engineer.

Phần 9 sẽ tập trung **Performance & Optimization** — biến container nhanh hơn, nhẹ hơn, tiết kiệm tài nguyên hơn.

---

# 📘 PHẦN 9: PERFORMANCE VÀ OPTIMIZATION

> *Container chạy được là một chuyện. Container chạy NHANH, NHẸ, hiệu quả tài nguyên là chuyện khác. Phần này dạy bạn cách biến Docker stack từ "lê lết" thành "bay".*

---

## 📖 CHƯƠNG 32: TỐI ƯU IMAGE, BUILD, RUNTIME

### 32.1. Triết lý tối ưu — "Đo trước, tối ưu sau"

**Quy tắc vàng:** **Đừng tối ưu trước khi đo.** Premature optimization là nguồn của bug và phức tạp không cần thiết.

**Quy trình:**

```
1. MEASURE   → Đo baseline (image size, build time, RAM, CPU)
2. PROFILE   → Tìm hot spot (layer nào to nhất, step nào chậm nhất)
3. OPTIMIZE  → Áp dụng kỹ thuật cụ thể
4. RE-MEASURE → Verify cải thiện
```

### 32.2. Đo image size

```bash
# Size tổng
docker images myapp
# REPOSITORY   TAG   IMAGE ID   SIZE
# myapp        v1    abc123     1.2GB

# Breakdown từng layer
docker history myapp:v1
# IMAGE     CREATED BY                    SIZE
# abc123    /bin/sh -c CMD ["python"...   0B
# <missing> /bin/sh -c pip install...     650MB    ← THỦ PHẠM
# <missing> /bin/sh -c apt-get install... 350MB    ← THỦ PHẠM
# ...

# Dùng dive cho deep analysis
dive myapp:v1
```

### 32.3. Tối ưu image size — Các kỹ thuật

#### a) Chọn base image nhỏ

| Base                          | Size   | Khi dùng                             |
| ----------------------------- | ------ | ------------------------------------- |
| `python:3.11`               | ~1GB   | Khi cần debug đầy đủ             |
| `python:3.11-slim`          | ~150MB | **Production standard**         |
| `python:3.11-alpine`        | ~50MB  | Khi compatible (cẩn thận musl libc) |
| `gcr.io/distroless/python3` | ~50MB  | Production max-secure                 |

```bash
# Demo so sánh
docker pull python:3.11 && docker images python | grep 3.11
# python   3.11   1010MB

docker pull python:3.11-slim && docker images python | grep slim
# python   3.11-slim   150MB

# Tiết kiệm 850MB chỉ bằng đổi tag!
```

#### b) Multi-stage build

```dockerfile
# Stage 1: Builder (lớn, có gcc, dev libs)
FROM python:3.11 AS builder
RUN apt-get update && apt-get install -y build-essential libpq-dev
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime (gọn, chỉ có runtime libs)
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY . /app
CMD ["python", "/app/main.py"]
```

**Kết quả thực tế:**

- Single stage: 1.5GB (full Python + build tools)
- Multi-stage: 250MB (chỉ runtime)
- Tiết kiệm: 1.25GB (83%)

#### c) Cleanup trong cùng RUN

```dockerfile
# ❌ TỆ
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*
# 3 layers, file rác đóng băng trong layer 1, 2

# ✅ TỐT
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
# 1 layer, không có rác
```

#### d) `--no-install-recommends`, `--no-cache-dir`

```dockerfile
# apt: bỏ recommended packages
RUN apt-get install -y --no-install-recommends curl libpq5

# pip: không cache wheel
RUN pip install --no-cache-dir -r requirements.txt
```

Tiết kiệm 30-100MB tùy package.

#### e) Squash với `--squash` — KHÔNG khuyến nghị

```bash
docker build --squash -t myapp .   # Cũ, không khuyến nghị
```

Mất cache giữa các project. Dùng multi-stage thay.

#### f) Strip unnecessary files

```dockerfile
# Sau khi build, xóa file không cần:
RUN find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -exec rm -rf {} + && \
    find /app -name "*.md" -delete && \
    find /app -name "tests" -type d -exec rm -rf {} +
```

#### g) Compiled binary cho language tĩnh

Go/Rust/C++ → 1 binary, dùng `scratch` hoặc `distroless`:

```dockerfile
FROM golang:1.21 AS builder
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /app

FROM scratch
COPY --from=builder /app /app
CMD ["/app"]
# Image cuối: < 10MB
```

### 32.4. Tối ưu Python image — Trường hợp cụ thể

#### Trước:

```dockerfile
FROM python:3.11

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
```

→ Image ~1.5GB, build cache không tốt.

#### Sau:

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir /wheels -r requirements.txt

# ---- Runtime ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY . .

RUN useradd -r app && chown -R app:app /app
USER app

CMD ["python", "main.py"]
```

→ Image ~250MB. Build chậm lần đầu, các lần sau nhanh nhờ cache mount.

### 32.5. Tối ưu build time

#### a) Sắp xếp instruction theo tần suất đổi

```
FROM            (gần như không đổi)
ENV, LABEL      (ít đổi)
RUN apt install (ít đổi)
COPY req + RUN pip   (ít đổi - chỉ khi requirements đổi)
COPY .          (đổi mỗi commit)
```

#### b) `.dockerignore` triệt để

```
# .dockerignore - giảm context size
.git/
.venv/
node_modules/
__pycache__/
**/*.pyc
**/*.log
**/.pytest_cache
.idea/
.vscode/
*.md
tests/
docs/
data/
notebooks/
.env*
```

Đo:

```bash
# Trước: tổng size 5GB
# Sau .dockerignore: tổng 50MB
# Build context transfer: 100 lần nhanh hơn
```

#### c) BuildKit cache mount

Đã giải thích Chương 27. Đây là **kỹ thuật quan trọng nhất** cho build CI:

```dockerfile
# syntax=docker/dockerfile:1.6
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

Build lần đầu: 5 phút (download packages).
Build lần 2 (cache miss layer này): 30s (pip dùng cache local).
**Tiết kiệm 4.5 phút/build.**

#### d) Parallel multi-stage

BuildKit tự build các stage không phụ thuộc nhau **song song**:

```dockerfile
FROM python:3.11 AS python-builder
# ...

FROM node:20 AS node-builder
# ...

FROM debian:bookworm-slim
COPY --from=python-builder ...
COPY --from=node-builder ...
```

→ Stages `python-builder` và `node-builder` build cùng lúc.

#### e) Inline cache cho CI

```bash
docker buildx build \
  --cache-from=type=registry,ref=myorg/myapp:cache \
  --cache-to=type=registry,ref=myorg/myapp:cache,mode=max \
  -t myorg/myapp:v1 \
  --push .
```

CI runners ephemeral (mỗi run máy mới) → không có local cache. Registry cache cứu nguy.

**GitHub Actions:**

```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### 32.6. Tối ưu Compose startup

#### Vấn đề: `docker compose up` mất 5 phút

```bash
docker compose up -d
docker compose ps
# postgres   (healthy)   ← 30s
# redis      (healthy)   ← 5s
# airflow-init   (running) ← 60s
# airflow-webserver  (starting) ← 90s
# airflow-scheduler  (starting) ← 90s
# ...
```

#### Optimizations

**a) Pre-pull image:**

```bash
docker compose pull
# Pull tất cả image trước, sau đó up nhanh
docker compose up -d
```

**b) Parallel build:**

```bash
docker compose build --parallel
```

**c) `depends_on` đúng cấp:**

```yaml
# ❌ Không cần: scheduler đợi webserver
depends_on:
  airflow-webserver:
    condition: service_healthy
```

`scheduler` và `webserver` đều phụ thuộc DB + init, không cần đợi nhau. → Tách dependency cho parallel.

**d) Healthcheck tốt:**

Healthcheck `interval: 30s` → tối thiểu 30s để biết healthy. Cho dev:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready"]
  interval: 2s          # Fast
  timeout: 2s
  retries: 30
  start_period: 5s
```

**e) Skip init khi đã có data:**

```yaml
airflow-init:
  command: |
    sh -c "
    if [ -f /opt/airflow/.initialized ]; then
      echo 'Already initialized, skipping'
      exit 0
    fi
    airflow db migrate && \
    airflow users create ... && \
    touch /opt/airflow/.initialized
    "
```

### 32.7. Tối ưu runtime — CPU & Memory

#### CPU optimization

**a) Set affinity nếu cần:**

```bash
docker run --cpuset-cpus=0-3 myapp
# Chỉ chạy trên CPU 0-3, tránh cache miss
```

**b) Đo CPU thực sự dùng:**

```bash
docker stats myapp --no-stream
# CPU %: 250%   ← Container dùng 2.5 cores
```

→ Nếu `--cpus=1` mà CPU dùng 100% liên tục → cần tăng giới hạn.

#### Memory optimization

**a) Set limit + reservation:**

```bash
docker run \
  --memory=2g \
  --memory-reservation=1g \
  myapp
```

**b) Theo dõi memory grow:**

```bash
watch -n 1 'docker stats --no-stream myapp'
# Nếu memory tăng dần không dừng → memory leak app
```

**c) Disable swap (cho data workload):**

```bash
docker run --memory=4g --memory-swap=4g myapp
# swap = memory → không swap → fail fast nếu OOM, không lê lết
```

### 32.8. Tối ưu cho Data Stack

#### Postgres

```yaml
services:
  postgres:
    image: postgres:15-alpine
    command: >
      postgres
      -c shared_buffers=512MB
      -c effective_cache_size=1536MB
      -c maintenance_work_mem=128MB
      -c work_mem=8MB
      -c max_connections=200
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
    deploy:
      resources:
        limits:
          memory: 2g
          cpus: '2'
```

**Rule of thumb cho Postgres:**

- `shared_buffers`: 25% RAM container
- `effective_cache_size`: 75% RAM container
- `work_mem`: tùy workload (8-64MB)

#### Airflow

```yaml
x-airflow-common: &airflow-common
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: '2'

services:
  airflow-scheduler:
    <<: *airflow-common
    environment:
      AIRFLOW__SCHEDULER__PARSING_PROCESSES: 2
      AIRFLOW__SCHEDULER__MAX_THREADS: 4
      AIRFLOW__CORE__PARALLELISM: 32
      AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG: 16

  airflow-worker:
    <<: *airflow-common
    environment:
      AIRFLOW__CELERY__WORKER_CONCURRENCY: 4
    deploy:
      resources:
        limits:
          memory: 8G       # Worker chạy task heavy
          cpus: '4'
```

#### Spark

```yaml
spark-worker:
  environment:
    SPARK_WORKER_MEMORY: 4G        # Tổng RAM worker
    SPARK_WORKER_CORES: 4
    SPARK_EXECUTOR_MEMORY: 2G      # RAM per executor
  deploy:
    resources:
      limits:
        memory: 5G                  # Slightly > worker memory
        cpus: '4'
```

**Memory bookkeeping:** Spark cần overhead 10-20% ngoài `worker_memory` cho JVM heap.

#### Kafka

```yaml
kafka:
  environment:
    KAFKA_HEAP_OPTS: "-Xmx2G -Xms2G"
    KAFKA_CFG_LOG_RETENTION_HOURS: 72
    KAFKA_CFG_LOG_SEGMENT_BYTES: 1073741824
  deploy:
    resources:
      limits:
        memory: 3g
        cpus: '2'
  volumes:
    - kafka-data:/bitnami/kafka
```

Kafka log retention quan trọng — đừng để data tăng vô hạn.

### 32.9. Network performance

#### Bridge vs Host

- Bridge: overhead nhẹ do NAT (~5-10% latency tăng).
- Host: zero overhead nhưng mất isolation.

→ Cho data pipeline trong dev: bridge OK. Production critical: cân nhắc.

#### Disable userland-proxy (Linux)

```json
// /etc/docker/daemon.json
{
  "userland-proxy": false
}
```

→ Port forwarding qua kernel iptables thay vì Docker userland proxy. Nhanh hơn nhưng có edge case (vd: bind privileged port).

### 32.10. Disk I/O performance

#### Storage driver

```bash
docker info | grep "Storage Driver"
# Storage Driver: overlay2     ← chuẩn, fast
```

Trên Linux, `overlay2` là chuẩn. Tránh các driver cũ (`devicemapper`, `aufs`).

#### Volume vs bind mount IO

Trên Mac/Windows (Docker Desktop), **bind mount cực chậm** do virtualization overhead:

```
Native Linux:        OverlayFS, native speed
Linux + Docker:      OverlayFS, native speed (~5% overhead)
Mac/Win + Docker:    9P/gRPC FUSE, ~50-90% chậm hơn
```

→ Trên Mac, **dùng named volume** cho Postgres data, **không bind mount**:

```yaml
# ❌ Mac/Win — chậm
volumes:
  - ./pgdata:/var/lib/postgresql/data

# ✅ Mac/Win
volumes:
  - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

#### Optimize bind mount Mac (nếu phải dùng)

Docker Desktop có settings:

- **VirtioFS** (mới, nhanh hơn) — bật trong Docker Desktop → Settings → General.
- **Mounting options**:
  - `:cached` — host là source of truth (đọc nhanh)
  - `:delegated` — container là source (ghi nhanh)
  - `:consistent` — strict sync (chậm nhất, default)

```yaml
volumes:
  - ./code:/app:cached
```

### 32.11. Đo và benchmark

#### Đo build time

```bash
time docker build -t myapp .
```

#### Đo image size

```bash
docker images myapp --format "{{.Size}}"
```

#### Đo startup time

```bash
time docker run --rm myapp echo done
```

#### Đo runtime resource

```bash
# Bench Postgres
docker exec postgres pgbench -i -s 10
docker exec postgres pgbench -c 10 -j 2 -t 1000
```

#### Đo IO

```bash
docker run --rm -v testdata:/data alpine sh -c \
  "dd if=/dev/zero of=/data/test bs=1M count=1000 conv=fdatasync"
# So sánh tốc độ write
```

### 32.12. Một case study tối ưu thực tế

**Initial state:**

- ETL Python job
- Image: `python:3.11` base
- Image size: 1.4GB
- Build time: 4 phút
- Cold start: 8s

**Optimization steps:**

1. Đổi sang `python:3.11-slim` → Image 800MB, save 600MB.
2. Multi-stage build → Image 280MB, save 520MB.
3. Cache mount cho pip → Build 1.5 phút, save 2.5 phút.
4. `.dockerignore` chuẩn → Build context từ 500MB → 5MB.
5. `--no-install-recommends` cho apt → Image 250MB.
6. Strip pyc/cache → Image 230MB.

**Final state:**

- Image: 230MB (-83%)
- Build time: 1.2 phút (-70%)
- Cold start: 1.5s (-81%)

→ Pipeline 10 lần chạy/ngày, 365 ngày → tiết kiệm hàng nghìn phút compute time, ổ cứng.

---

### ✅ TÓM TẮT CHƯƠNG 32

#### Checklist tối ưu image

- [ ] Slim base image
- [ ] Multi-stage build
- [ ] Cleanup cùng RUN
- [ ] `--no-install-recommends`, `--no-cache-dir`
- [ ] `.dockerignore` chuẩn
- [ ] Sắp xếp instruction theo cache
- [ ] BuildKit cache mount
- [ ] Strip unnecessary files

#### Checklist tối ưu runtime

- [ ] Resource limits hợp lý
- [ ] Healthcheck nhẹ
- [ ] Log rotation
- [ ] Storage driver = overlay2
- [ ] Named volume cho data IO heavy
- [ ] Tune service-specific (Postgres buffers, Spark memory...)

---

## 📖 CHƯƠNG 33: TRADE-OFF VÀ KHI NÀO KHÔNG NÊN DÙNG DOCKER

> *Docker không phải là "viên đạn bạc". Có những trường hợp Docker là sai lựa chọn. Senior engineer biết khi nào KHÔNG dùng Docker cũng quan trọng như biết dùng Docker.*

### 33.1. Trade-off của Docker

#### Pros (đã biết)

- Reproducibility
- Isolation
- Portability
- Dependency management
- Fast onboarding
- CI/CD friendly

#### Cons (ít người nói thẳng)

##### a) Performance overhead

| Resource               | Overhead                      |
| ---------------------- | ----------------------------- |
| CPU                    | ~1-3% (negligible)            |
| Memory                 | ~50-200MB cho Docker daemon   |
| Network                | ~5-10% (bridge NAT)           |
| Disk IO (Linux native) | ~5%                           |
| Disk IO (Mac/Win)      | **30-90%** (do FUSE/9P) |
| Cold start             | Vài giây extra              |

→ Workload nhạy CPU/network/disk có thể chậm hơn native.

##### b) Complexity tăng

Trước Docker:

```bash
python app.py
```

Sau Docker:

```bash
docker build -t myapp .
docker run --rm -v ... -p ... -e ... myapp
```

→ Cần học Dockerfile, Compose, network, volume, debug Docker-specific issues. Stack học thêm 1 layer.

##### c) Storage tích lũy

Image cũ, container chết, volume orphan, build cache → có thể tích lũy nhiều GB nếu không cleanup.

##### d) Security surface

Docker daemon chạy root. Mount socket = root access. Misconfigured network expose lộ ra ngoài.

##### e) Vendor lock-in nhẹ

Docker Compose syntax không phải standard 100% (so với Kubernetes manifests). Compose → K8s migration cần convert.

### 33.2. Khi nào KHÔNG nên dùng Docker

#### 1. App siêu đơn giản chạy local

```bash
# Tính tổng 2 số:
python -c "print(1+2)"
```

→ Không cần Docker. Overhead không xứng đáng.

**Rule of thumb:** Nếu script chạy < 1 phút và không có dependency phức tạp → chạy trực tiếp.

#### 2. Performance-critical workload

##### High-frequency trading, real-time gaming, low-latency networking

Mỗi mili-giây quý giá → overhead bridge network không chấp nhận được.

**Workaround:** `--network=host` (Linux) hoặc native deployment.

##### Massive disk IO (Mac/Win dev)

Database benchmark, video processing, ML training với dataset to → bind mount Mac chậm 50-90%.

**Workaround:**

- Dùng named volume thay bind mount
- Dev trên Linux/WSL2
- Dùng remote container (Dev Containers)

#### 3. GPU-heavy workload (cần config kỹ)

Docker hỗ trợ GPU (`--gpus all`) qua NVIDIA Container Toolkit, nhưng:

- Config phức tạp
- Driver version cần match
- Một số CUDA feature có edge case

**Khi cần thử nghiệm nhanh:** Chạy native Python với conda + CUDA. Dùng Docker khi đã stable workflow.

#### 4. Long-running stateful workload trên 1 máy duy nhất

Ví dụ: Postgres production trên 1 server vĩnh viễn.

**Trade-off:**

- Docker thêm 1 layer indirection
- `docker stop` có thể không graceful 100% (cần config)
- Backup/restore phức tạp hơn native

**Khi nào OK:** Có team Docker expertise + monitoring + backup automation.
**Khi nào KHÔNG OK:** 1 dev tự maintain Postgres production → native install có thể đơn giản hơn.

→ **Production critical DB:** dùng managed service (RDS, Cloud SQL) thay vì self-host Docker.

#### 5. Embedded/IoT với resource cực hạn chế

Device có 64MB RAM, 100MB flash → Docker overhead lớn hơn payload. Dùng native compile.

#### 6. App cần access full kernel features

- Cần load custom kernel module
- Cần raw network access (eBPF, packet sniffing)
- System administration tools

Docker container không thấy host kernel modules. Workaround: `--privileged` (mất hết isolation, không khuyến nghị).

#### 7. Khi compliance bắt buộc native

Một số chuẩn compliance (banking, healthcare) bắt buộc audit ở mức OS, không chấp nhận container. Hỏi compliance team trước khi container hóa.

### 33.3. Docker Desktop trên Mac/Windows — Pitfalls

#### Vấn đề kiến trúc

Docker Desktop trên Mac/Win KHÔNG chạy container natively. Nó:

1. Chạy 1 **Linux VM** ẩn (HyperKit/WSL2/Hyper-V).
2. Docker daemon chạy trong VM.
3. Container chạy trong VM đó.
4. Bind mount + network port forward qua VM boundary.

```
┌──────────────────────────────────┐
│        Mac/Windows               │
│  ┌────────────────────────────┐  │
│  │   Linux VM (hidden)        │  │
│  │   ┌──────────────────────┐ │  │
│  │   │  Container           │ │  │
│  │   └──────────────────────┘ │  │
│  └────────────────────────────┘  │
│  Bind mount: host ↔ VM ↔ container│
│                ↑ slow boundary    │
└──────────────────────────────────┘
```

#### Hệ quả

**a) Bind mount chậm**

Mỗi file IO bind mount: Mac → VM → container. Latency cao.

**Đo bench:**

```bash
# Mac native:    0.5s tạo 10000 files
# Linux native: 0.6s
# Mac + Docker bind mount: 30-60s
```

**Mitigation:**

- VirtioFS (Docker Desktop 4.6+, nhanh hơn 9P)
- Mutagen sync (third-party)
- Dev container trên WSL2 (Win)

**b) Resource sharing**

Docker Desktop config:

- RAM cấp cho VM (default 8GB hoặc 50% host)
- CPU
- Disk size

→ Stack data lớn (Airflow + Spark + Postgres + Kafka) cần tăng RAM VM:

```
Docker Desktop → Settings → Resources
- Memory: 12GB
- CPUs: 4-6
```

**c) Network localhost confusion**

Trên Mac/Win:

- `localhost` trên host → forward đến VM → forward đến container (qua `-p`).
- `localhost` trong container → namespace container, KHÔNG phải host.
- `host.docker.internal` → host machine từ container.

**d) File watcher không trigger**

Tool watch file (webpack, nodemon) trong container không nhận file change event qua bind mount Mac (inotify không propagate qua VM boundary).

→ Workaround: polling mode (`CHOKIDAR_USEPOLLING=true`).

### 33.4. Alternatives — Khi Docker không phù hợp

#### Podman

- Daemonless (không cần daemon root)
- CLI tương thích Docker (`alias docker=podman`)
- Rootless mode native
- Pods (multi-container unit, giống K8s)

#### nerdctl + containerd

- CLI cho containerd trực tiếp
- Khi đã có containerd (vd: K8s nodes)

#### Lima (Mac)

- Linux VM ngon hơn Docker Desktop cho dev
- Hỗ trợ containerd, nerdctl

#### Native install

- Đôi khi đơn giản nhất là cài thẳng. Đặc biệt cho long-running production DB trên dedicated server.

### 33.5. Cost analysis — Trade-off tài nguyên

#### Container vs VM vs Bare metal

| Aspect            | Bare Metal                | VM                     | Container          |
| ----------------- | ------------------------- | ---------------------- | ------------------ |
| Setup cost        | High (provision hardware) | Medium                 | Low                |
| Runtime overhead  | None                      | High (~10-15%)         | Low (~1-3%)        |
| Density           | 1 app/server              | 5-10/server            | 50-100/server      |
| Failure isolation | Per-server                | Per-VM                 | Per-container      |
| Boot time         | Minutes                   | Minutes                | Seconds            |
| Use case          | Specialized (HPC, DB)     | Multi-tenant, mixed OS | Microservices, dev |

#### Khi nào upgrade từ Compose → Kubernetes?

**Đừng vội.** Kubernetes có learning curve dốc.

**Tín hiệu cần K8s:**

- Multi-node cluster cần
- HA, auto-failover
- Auto-scaling (HPA)
- > 20-30 services
  >
- Multi-tenant với network policies
- Compliance/audit requirements

**Còn Compose là đủ:**

- Single-host setup
- < 20 services
- Dev/staging/single-tenant prod
- Đang prototype

### 33.6. "Đừng container hóa cái gì"

Anti-patterns thường gặp:

#### ❌ Container hóa cron host

```dockerfile
FROM debian
RUN apt install cron
COPY crontab /etc/cron.d/
CMD ["cron", "-f"]
```

→ Cron không phải app. Dùng Airflow/Argo Workflows nếu cần scheduling, hoặc systemd timers trên host.

#### ❌ "1 container = nhiều process"

Container nên là **1 process logical**. Đừng bỏ Postgres + Redis + Nginx vào 1 container.

→ Mỗi service riêng container, dùng Compose link lại.

#### ❌ Build image trong container (Docker-in-Docker)

```bash
docker run -v /var/run/docker.sock:/var/run/docker.sock myapp
# Container có thể control Docker daemon → root host
```

Security nightmare. Dùng Kaniko, BuildKit rootless, hoặc remote builder.

#### ❌ Container hóa GUI desktop apps

Có thể (qua X11 forwarding) nhưng phức tạp, ít lợi ích. Dùng native install.

#### ❌ "Docker == Microservices"

Container chạy được monolith, microservices, batch jobs, đủ thứ. **Container không bắt buộc phải microservices.**

### 33.7. Vì sao nhiều team "bỏ Docker"?

Một số team có rationale bỏ Docker cho 1 phần workload:

1. **Mac dev pain point**: Bind mount chậm → frustration → dev quay về native + virtualenv.
2. **Resource cost trên CI**: Docker layer build, push, pull tốn time CI → quay về native build cho fast feedback.
3. **Complexity vs payoff**: Stack 3-4 service nhỏ, team 2 người → overhead Compose không xứng.
4. **Production K8s native**: Đã có K8s + image build pipeline (Tekton/Argo) → không cần Docker CLI dev local.

**Bài học:** Đừng cargo-cult. Docker là tool, không phải religion. Đánh giá cho từng use case.

### 33.8. Quyết định framework

```
Có cần reproducibility tuyệt đối? ─┬─ Có → Docker
                                   └─ Không → Pythonic virtualenv OK

Stack có > 3 services? ────────────┬─ Có → Compose
                                   └─ Không → Có thể native

Cần CI/CD reproducible build? ─────┬─ Có → Docker
                                   └─ Không → Tùy chọn

Performance critical (sub-ms)? ────┬─ Có → Cân nhắc native
                                   └─ Không → Docker fine

Team Docker expertise? ────────────┬─ Có → Docker
                                   └─ Không → Train, OR avoid

Dev trên Mac/Win? ────────────────┬─ Có → Cẩn thận bind mount
                                   └─ Linux → Docker xuất sắc
```

---

### ✅ TÓM TẮT CHƯƠNG 33

#### Khi nên dùng Docker

- ✅ Reproducible environment quan trọng
- ✅ Multi-service stack (3+ services)
- ✅ Onboarding team
- ✅ CI/CD pipeline
- ✅ Dev-prod parity
- ✅ Dependency hell elimination

#### Khi cân nhắc KHÔNG dùng

- ⚠️ Performance critical (sub-millisecond)
- ⚠️ Heavy disk IO trên Mac/Win
- ⚠️ Stack nhỏ (< 3 services)
- ⚠️ Long-running production DB single-host (consider managed)
- ⚠️ Embedded/IoT siêu hạn chế
- ⚠️ GPU workload đang prototype

#### Câu hỏi tự kiểm tra

1. Liệt kê 3 trường hợp KHÔNG nên dùng Docker.
2. Docker Desktop trên Mac có pitfall nào với bind mount?
3. Khi nào nên migration từ Compose sang Kubernetes?
4. Vì sao container chạy `--privileged` là anti-pattern?
5. Trade-off giữa container và VM là gì?

---

## 🎯 KẾT THÚC PHẦN 9

Bạn vừa học một trong những phần **dày dạn nhất** của tài liệu:

- Tối ưu image size (10x smaller)
- Tối ưu build time (10x faster)
- Tối ưu runtime cho từng service data stack
- Hiểu trade-off, biết khi nào KHÔNG dùng Docker

Đến đây bạn đã có mindset của senior — vừa dùng Docker hiệu quả, vừa biết giới hạn của nó.

Tiếp theo: **Phần 10 — CI/CD và Production mindset**.

---

# 📘 PHẦN 10: DOCKER TRONG CI/CD VÀ PRODUCTION

> *Tới đây bạn đã biết cách build, chạy, debug Docker. Phần này dạy bạn dùng Docker trong workflow của team thật, ở scale thật, với mindset của một senior engineer chịu trách nhiệm production.*

---

## 📖 CHƯƠNG 34: BUILD PIPELINE VỚI DOCKER

### 34.1. Triết lý: Image là deployment artifact

Trong workflow production hiện đại:

```
Source code → Build → Test → Image → Registry → Deploy
                              ↑
                              └── Đơn vị deploy chuẩn
```

**Quy tắc vàng:**

- **Build 1 lần**, deploy nhiều môi trường (dev/staging/prod)
- **Cùng image binary** chạy mọi nơi
- **Promote bằng cách retag**, không rebuild

```
Image: myorg/etl:sha-abc1234
  ├── + tag: dev       → deploy dev
  ├── + tag: staging   → deploy staging
  └── + tag: v1.2.3    → deploy prod
```

Vi phạm quy tắc này = vi phạm reproducibility = production bug "magic" xuất hiện.

### 34.2. Anatomy của Docker CI/CD pipeline

```mermaid
graph LR
    A[Git Push] --> B[Lint + Test code]
    B --> C[Build Image]
    C --> D[Scan Vulnerabilities]
    D --> E[Run Container Tests]
    E --> F[Push to Registry]
    F --> G[Deploy to Dev]
    G --> H[Integration Tests]
    H --> I{Manual<br/>Approve}
    I -->|Yes| J[Promote to Prod]
```

**6 stages chính:**

1. **Lint** — `hadolint Dockerfile`, code linter
2. **Test code** — unit test trong dev environment
3. **Build** — `docker buildx build` với cache
4. **Scan** — `trivy image` cho vuln
5. **Container test** — chạy container, integration test
6. **Push + Deploy** — registry → environment

### 34.3. GitHub Actions — Pipeline mẫu hoàn chỉnh

File: `.github/workflows/build.yml`

```yaml
name: Build & Deploy

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ============ Stage 1: Lint ============
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint Dockerfile
        uses: hadolint/hadolint-action@v3
        with:
          dockerfile: Dockerfile
          failure-threshold: warning
      - name: Lint Python code
        run: |
          pip install ruff
          ruff check .

  # ============ Stage 2: Test (without Docker) ============
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install & test
        run: |
          pip install -r requirements.txt -r requirements-dev.txt
          pytest --cov

  # ============ Stage 3: Build + Scan + Push ============
  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      security-events: write
    steps:
      - uses: actions/checkout@v4

      # Set up Docker Buildx (BuildKit)
      - uses: docker/setup-buildx-action@v3

      # Login to GitHub Container Registry
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Auto-generate tags from git ref
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=sha-

      # Build with cache
      - name: Build image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          load: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            GIT_SHA=${{ github.sha }}
            APP_VERSION=${{ github.ref_name }}

      # Scan vulnerabilities
      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          format: sarif
          output: trivy-results.sarif
          severity: CRITICAL,HIGH
          exit-code: 0   # Don't fail, just report

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-results.sarif

      # Container integration test
      - name: Test container
        run: |
          docker run -d --name test-container \
            -e DATABASE_URL=postgresql://test:test@localhost:5432/test \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          sleep 5
          docker logs test-container
          docker exec test-container python -c "import etl; print(etl.__version__)"

      # Push only on main or tag
      - name: Push image
        if: github.event_name != 'pull_request'
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          platforms: linux/amd64,linux/arm64
```

**Hiểu pipeline trên:**

- **Trigger**: push lên `main`, tag `v*`, PR
- **Permissions**: `packages: write` để push GHCR; `security-events: write` để upload Trivy SARIF
- **`metadata-action`**: tự sinh tags chuẩn (semver, branch, sha)
- **Build with cache**: `cache-from/to: type=gha` dùng GitHub Actions Cache miễn phí
- **Trivy scan**: phát hiện CVE, upload kết quả lên GitHub Security tab
- **Container test**: smoke test image trước khi push
- **Conditional push**: PR không push, chỉ main và tag mới push
- **Multi-platform**: build cho cả AMD64 và ARM64

### 34.4. GitLab CI — Equivalent

File: `.gitlab-ci.yml`

```yaml
stages:
  - lint
  - test
  - build
  - scan
  - deploy

variables:
  IMAGE_NAME: $CI_REGISTRY_IMAGE
  DOCKER_BUILDKIT: 1

lint:
  stage: lint
  image: hadolint/hadolint:latest-alpine
  script:
    - hadolint Dockerfile

test:
  stage: test
  image: python:3.11-slim
  script:
    - pip install -r requirements.txt -r requirements-dev.txt
    - pytest

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: ""
  before_script:
    - echo $CI_REGISTRY_PASSWORD | docker login -u $CI_REGISTRY_USER --password-stdin $CI_REGISTRY
  script:
    - docker buildx create --use
    - |
      docker buildx build \
        --cache-from=type=registry,ref=$IMAGE_NAME:cache \
        --cache-to=type=registry,ref=$IMAGE_NAME:cache,mode=max \
        -t $IMAGE_NAME:$CI_COMMIT_SHA \
        -t $IMAGE_NAME:$CI_COMMIT_REF_SLUG \
        --push .

scan:
  stage: scan
  image: aquasec/trivy:latest
  script:
    - trivy image --severity CRITICAL,HIGH --exit-code 1 $IMAGE_NAME:$CI_COMMIT_SHA
  allow_failure: true

deploy_dev:
  stage: deploy
  environment: dev
  only: [main]
  script:
    - ./scripts/deploy.sh dev $IMAGE_NAME:$CI_COMMIT_SHA

deploy_prod:
  stage: deploy
  environment: production
  only:
    - tags
  when: manual    # Cần approve
  script:
    - ./scripts/deploy.sh prod $IMAGE_NAME:$CI_COMMIT_SHA
```

### 34.5. Build optimization cho CI

#### a) Cache aggressively

```bash
# Local dev
docker build -t myapp .   # BuildKit dùng local cache

# CI runners ephemeral → cần external cache:
docker buildx build \
  --cache-from=type=registry,ref=myorg/myapp:cache \
  --cache-to=type=registry,ref=myorg/myapp:cache,mode=max \
  -t myorg/myapp:v1 \
  --push .
```

**Cache backends:**

- `type=gha` — GitHub Actions Cache (free, fast)
- `type=registry` — push lên registry (cross-CI/dev share)
- `type=local` — local file (cho self-hosted runner)
- `type=s3` — S3 bucket (enterprise)

#### b) Parallel matrix builds

```yaml
strategy:
  matrix:
    platform: [linux/amd64, linux/arm64]
  fail-fast: false
```

→ Build 2 platform song song trên 2 runner.

#### c) Layer cache stable

Đảm bảo cache key stable:

```dockerfile
# Sai: APT mirror random → cache miss
RUN echo $RANDOM > /tmp/cache-buster
RUN apt-get update

# Đúng: Pin version + ordered
RUN apt-get update && apt-get install -y libpq5=15.4-0+deb12u1
```

### 34.6. Multi-environment promotion

#### Pattern: Promote by retag

```bash
# CI build:
docker buildx build -t myorg/etl:sha-abc1234 --push .

# Auto-deploy dev:
docker tag myorg/etl:sha-abc1234 myorg/etl:dev
docker push myorg/etl:dev
# Dev cluster pull: myorg/etl:dev

# Manual promote staging:
docker pull myorg/etl:sha-abc1234
docker tag myorg/etl:sha-abc1234 myorg/etl:staging
docker push myorg/etl:staging

# Manual promote prod (yêu cầu approval):
docker pull myorg/etl:sha-abc1234
docker tag myorg/etl:sha-abc1234 myorg/etl:v1.2.3
docker tag myorg/etl:sha-abc1234 myorg/etl:prod
docker push myorg/etl:v1.2.3
docker push myorg/etl:prod
```

→ **Cùng SHA**, cùng image binary, chạy qua các môi trường.

#### Pattern: Compose override per environment

```
compose.yaml           # Base
compose.dev.yaml       # Dev override
compose.staging.yaml   # Staging override
compose.prod.yaml      # Prod override
```

```bash
# Dev
docker compose -f compose.yaml -f compose.dev.yaml up

# Prod
docker compose -f compose.yaml -f compose.prod.yaml up
```

### 34.7. Run tests trong container

#### Unit tests

```bash
# Trong CI:
docker build --target test -t myapp:test .
docker run --rm myapp:test pytest
```

Dockerfile multi-stage with test target:

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY . .
RUN pytest

FROM base AS production
COPY . .
USER nobody
CMD ["python", "main.py"]
```

#### Integration tests with services

```yaml
# .github/workflows/test.yml
jobs:
  integration-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10
        ports: ['5432:5432']
  
      kafka:
        image: bitnami/kafka:3.6
        # ...
  
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/postgres
        run: |
          docker build -t myapp .
          docker run --rm --network host \
            -e DATABASE_URL=$DATABASE_URL \
            myapp pytest tests/integration/
```

#### Docker Compose for testing

```bash
# Dùng compose chạy stack test
docker compose -f compose.test.yaml up -d
docker compose -f compose.test.yaml run --rm test-runner pytest
docker compose -f compose.test.yaml down -v
```

### 34.8. testcontainers — Pattern xịn cho integration test

```python
# pip install testcontainers
from testcontainers.postgres import PostgresContainer
from testcontainers.kafka import KafkaContainer
import pytest

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:15-alpine") as pg:
        yield pg

@pytest.fixture(scope="session")
def kafka():
    with KafkaContainer("confluentinc/cp-kafka:latest") as k:
        yield k

def test_etl_pipeline(postgres, kafka):
    db_url = postgres.get_connection_url()
    kafka_url = kafka.get_bootstrap_server()
  
    # Run pipeline
    pipeline = ETLPipeline(db_url=db_url, kafka_url=kafka_url)
    pipeline.run()
  
    # Assert results...
```

**Lợi ích:**

- Mỗi test có DB/Kafka tạm
- Tự cleanup
- Chạy local + CI giống hệt
- Không cần Compose phụ trợ

### 34.9. Secret management trong CI

#### GitHub Actions Secrets

```yaml
steps:
  - name: Build
    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    run: docker build --secret id=aws,env=AWS_ACCESS_KEY_ID -t myapp .
```

#### OIDC (recommended for AWS/GCP/Azure)

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123:role/GitHubAction
      aws-region: us-east-1
  # Không cần access key, dùng short-lived token
```

#### Đừng làm điều này

```yaml
# ❌ Secret hardcode
env:
  API_KEY: sk-abc123

# ❌ Build arg
docker build --build-arg API_KEY=$API_KEY ...

# ❌ COPY .env vào image
```

---

### ✅ TÓM TẮT CHƯƠNG 34

#### CI/CD pipeline checklist

- [ ] Lint Dockerfile (hadolint)
- [ ] Unit tests trước build
- [ ] BuildKit + cache
- [ ] Scan vulnerabilities (Trivy)
- [ ] Container smoke test
- [ ] Multi-platform build
- [ ] Tag bằng SemVer + Git SHA
- [ ] Push lên registry
- [ ] Promote bằng retag (không rebuild)
- [ ] Secret qua OIDC hoặc CI secrets, KHÔNG trong image
- [ ] Audit log (ai deploy gì, khi nào)

#### Câu hỏi tự kiểm tra

1. Vì sao "build 1 lần, deploy nhiều môi trường"?
2. `cache-from: type=gha` khác `type=registry` thế nào?
3. testcontainers giải quyết vấn đề gì so với Compose?
4. Vì sao OIDC tốt hơn hardcoded secrets?
5. Multi-platform build có nhược điểm gì với CI time?

---

## 📖 CHƯƠNG 35: COMPOSE VS SWARM VS KUBERNETES

### 35.1. Phổ orchestration

```
Compose          →  Swarm           →  Kubernetes
Đơn giản            Vừa phải            Phức tạp
1 host              Multi-host          Multi-host, scale lớn
Dev/staging         Small prod          Enterprise prod
< 20 services       < 100 services      Vô hạn
```

### 35.2. Docker Compose — Khi đủ?

**Phù hợp:**

- Dev environment cá nhân/team
- CI pipeline (test stack)
- Single-host production nhỏ (startup, internal tool)
- Demo, prototype
- POC trước khi đầu tư K8s

**Giới hạn:**

- 1 host duy nhất
- Không auto-scaling
- Không tự failover (container restart nhưng host die → mất hết)
- Khó multi-tenant
- Network policy hạn chế

### 35.3. Docker Swarm — Middleground

Swarm là orchestrator built-in của Docker. Đơn giản hơn K8s rất nhiều.

```bash
# Init swarm
docker swarm init

# Deploy stack từ compose file
docker stack deploy -c compose.yaml mystack

# Scale
docker service scale mystack_web=5

# List services
docker service ls

# Update rolling
docker service update --image myapp:v2 mystack_web

# Drain node để bảo trì
docker node update --availability drain node-1
```

**Khác Compose:**

- Multi-host cluster
- Service abstraction (replicated containers)
- Built-in load balancer
- Rolling update
- Secret/config management
- Overlay network

**So với Kubernetes:**

- Simpler — học vài tiếng vs vài tháng
- Less features — không có HPA, network policy phức tạp
- Docker-native — không cần học YAML lạ

**Use case:**

- Team nhỏ (2-10 người)
- 5-50 services
- Không cần auto-scaling advanced
- Đang dùng Compose, muốn lên cluster mà không học K8s

**Hiện trạng (2025):**
Docker Swarm vẫn được maintain nhưng cộng đồng chuyển nhiều sang K8s. Adoption giảm. **Cân nhắc lựa chọn dài hạn.**

### 35.4. Kubernetes — Standard de facto

Kubernetes (K8s) là orchestrator phức tạp nhưng mạnh nhất, được toàn ngành adopt.

#### Core concepts

```
Pod          — Đơn vị nhỏ nhất, 1 hoặc nhiều container
Deployment   — Quản lý multiple replicas của Pod
Service      — Network endpoint cho Pod
ConfigMap    — Config từ file
Secret       — Sensitive data
PersistentVolume — Storage
Namespace    — Logical isolation
```

#### Ví dụ Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl-job
spec:
  replicas: 3
  selector:
    matchLabels:
      app: etl
  template:
    metadata:
      labels:
        app: etl
    spec:
      containers:
        - name: etl
          image: myorg/etl:v1.2.3
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: url
          resources:
            limits:
              memory: 2Gi
              cpu: '2'
            requests:
              memory: 1Gi
              cpu: '1'
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            periodSeconds: 30
```

#### Compose → K8s migration

Tool `kompose`:

```bash
kompose convert -f compose.yaml
# Tạo các file .yaml K8s từ compose
```

**Cảnh báo:** Convert không hoàn hảo. K8s mindset khác Compose. Cần học K8s rồi viết manifest từ đầu.

### 35.5. So sánh feature

| Feature                     | Compose        | Swarm            | K8s                                  |
| --------------------------- | -------------- | ---------------- | ------------------------------------ |
| **Setup**             | 5 phút        | 1 giờ           | 1 tuần (managed) — 1 tháng (self) |
| **Multi-host**        | ❌             | ✅               | ✅                                   |
| **Auto-scaling**      | ❌             | Limited          | ✅ (HPA, VPA)                        |
| **Self-healing**      | Container only | Container + node | Pod + node                           |
| **Rolling update**    | Manual         | ✅               | ✅                                   |
| **Service discovery** | DNS            | DNS              | DNS + Service                        |
| **Load balancing**    | Manual         | Built-in         | Built-in (Service)                   |
| **Secrets**           | Basic          | ✅               | ✅                                   |
| **Network policies**  | ❌             | Basic            | ✅ (CNI)                             |
| **Storage**           | Volume         | Volume           | PV/PVC, CSI                          |
| **Multi-tenancy**     | ❌             | Limited          | ✅ (Namespace, RBAC)                 |
| **Ecosystem**         | Small          | Small            | Massive (Helm, Operators)            |
| **Learning curve**    | 1 day          | 1 week           | 2-3 months                           |

### 35.6. Khi nào upgrade Compose → K8s?

**Đừng vội.** K8s có learning curve dốc + operational cost.

**Tín hiệu cần K8s:**

- ✅ > 20 services
- ✅ Multi-host cluster cần
- ✅ HA, auto-failover bắt buộc
- ✅ Auto-scaling theo load
- ✅ Multi-tenant (nhiều team share cluster)
- ✅ Compliance audit (SOC2, etc.) yêu cầu fine-grained RBAC
- ✅ Đã có DevOps team chuyên trách

**Compose vẫn đủ:**

- Single-host hoặc < 20 services
- Team nhỏ, không có DevOps chuyên trách
- Dev/staging/prototype
- Cost-sensitive (K8s managed cluster đắt, self-hosted phức tạp)

### 35.7. Kubernetes cho Data Engineer

#### Patterns phổ biến

**a) KubernetesPodOperator (Airflow):**

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

run_etl = KubernetesPodOperator(
    task_id='run_etl',
    name='etl-pod',
    image='myorg/etl:v1.2.3',
    env_vars={'DATABASE_URL': '...'},
    resources={'request_memory': '2Gi', 'limit_memory': '4Gi'},
    is_delete_operator_pod=True,
)
```

→ Mỗi task = 1 pod, isolation tốt, scale tốt.

**b) Spark on Kubernetes:**

```bash
spark-submit \
  --master k8s://https://k8s-api:6443 \
  --deploy-mode cluster \
  --conf spark.kubernetes.container.image=myorg/spark:v1 \
  s3://bucket/etl_job.py
```

**c) Argo Workflows / Argo CD:**

DAG-based workflow on K8s (alternative cho Airflow trong K8s-native).

**d) Strimzi (Kafka on K8s):**

Kafka operator quản lý Kafka cluster trên K8s.

**e) Trino on K8s:**

Helm chart cho Trino → distributed query engine cho data lake.

### 35.8. Managed K8s — Khi nào dùng?

Self-hosted K8s rất khó. Dùng managed:

| Provider     | Service                               |
| ------------ | ------------------------------------- |
| AWS          | EKS                                   |
| GCP          | GKE (xịn nhất theo nhiều ý kiến) |
| Azure        | AKS                                   |
| DigitalOcean | DOKS                                  |
| Linode       | LKE                                   |

**Trade-off:**

- Đắt hơn self-host
- Đơn giản hơn nhiều
- Provider lo control plane, upgrade, security patches

**Khuyến nghị:** Trừ khi có DevOps team mạnh, **luôn dùng managed K8s** cho production.

### 35.9. K3s, K0s — Lightweight K8s

Cho edge, dev local, single-node prod:

- **K3s** (Rancher) — full K8s, < 100MB, chạy được Raspberry Pi
- **K0s** (Mirantis) — alternative
- **Minikube, Kind** — local dev K8s

```bash
# K3s install (1 lệnh)
curl -sfL https://get.k3s.io | sh -

# Kind (K8s in Docker)
kind create cluster
```

### 35.10. Production deployment patterns

#### Blue/Green

```
Blue (v1)  → Active
Green (v2) → Deploy mới, test
            → Switch traffic → Green active, Blue standby
            → Rollback nhanh bằng switch lại
```

#### Canary

```
95% traffic → Stable
5% traffic  → New version
            → Monitor → Tăng dần %
            → Hoặc rollback
```

#### Rolling update

```
3 replicas v1 → Update 1 → 2 v1 + 1 v2 → ... → 3 v2
```

K8s Deployment hỗ trợ rolling update mặc định.

---

### ✅ TÓM TẮT CHƯƠNG 35

#### Decision matrix

| Trường hợp                | Khuyến nghị                 |
| ---------------------------- | ----------------------------- |
| Dev cá nhân                | Compose                       |
| CI/CD test                   | Compose                       |
| Startup MVP (1 server)       | Compose                       |
| Internal tool < 10 services  | Compose                       |
| Small team production        | Swarm hoặc Managed K8s       |
| Multi-team, compliance       | Managed K8s                   |
| Edge/IoT                     | K3s                           |
| Big data platform production | K8s + Spark/Airflow operators |

#### Câu hỏi tự kiểm tra

1. Compose, Swarm, K8s — phân biệt 3 cái?
2. Khi nào nên migrate từ Compose lên K8s?
3. K8s "Deployment" tương đương concept nào trong Compose?
4. KubernetesPodOperator của Airflow giải quyết vấn đề gì?
5. Blue/Green vs Canary deployment khác nhau thế nào?

---

## 📖 CHƯƠNG 36: ANTI-PATTERNS PHỔ BIẾN

> *"Smart people learn from their mistakes. Smarter people learn from others' mistakes." — Phần này tổng hợp 20+ anti-patterns thực tế.*

### 36.1. Image anti-patterns

#### ❌ AP1: Dùng tag `latest`

```dockerfile
FROM python:latest                # Tệ
FROM postgres:latest              # Tệ hơn (Postgres major upgrade phá backward compat)
```

**Vấn đề:** `latest` hôm nay khác `latest` 1 tháng sau. Production unpredictable.

**Fix:** Pin version cụ thể:

```dockerfile
FROM python:3.11.7-slim
FROM postgres:15.4-alpine
```

#### ❌ AP2: Không có `.dockerignore`

**Vấn đề:** Build context bao gồm `.git`, `node_modules`, data files → context 5GB, build chậm + image to.

**Fix:** Có `.dockerignore` chuẩn ngay từ đầu.

#### ❌ AP3: Run as root

```dockerfile
FROM python:3.11-slim
COPY . /app
CMD ["python", "/app/main.py"]
# Container chạy root!
```

**Vấn đề:** Container compromise → attacker có root, dễ leo ra host.

**Fix:**

```dockerfile
RUN groupadd -r app && useradd -r -g app app
USER app
CMD ["python", "/app/main.py"]
```

#### ❌ AP4: Cache không tốt

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt    # Mọi đổi code → pip install lại
```

**Fix:** Sắp xếp lại:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

#### ❌ AP5: Cài đè cleanup khác layer

```dockerfile
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*    # File đã "đóng băng" ở layer trên
```

**Fix:** Cùng RUN:

```dockerfile
RUN apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
```

#### ❌ AP6: Image quá to

Multi-GB Python image cho 1 script 100 dòng.

**Fix:** Slim base + multi-stage.

#### ❌ AP7: Secret trong image

```dockerfile
ENV DB_PASSWORD=secret    # ❌
COPY .env /app/           # ❌
```

**Fix:** Runtime env, BuildKit secret, external secret manager.

### 36.2. Container runtime anti-patterns

#### ❌ AP8: Không resource limit

```bash
docker run -d myapp    # Có thể ngốn hết RAM/CPU host
```

**Fix:**

```bash
docker run -d --memory=2g --cpus=1.5 myapp
```

#### ❌ AP9: Log ra file trong container

```python
logger.addHandler(FileHandler("/app/log.txt"))
# Container die → log mất; docker logs không thấy
```

**Fix:** Log ra stdout/stderr.

#### ❌ AP10: PID 1 không xử lý signal

```dockerfile
CMD python app.py    # Shell form → PID 1 là sh, không phải python
```

**Fix:** Exec form + xử lý SIGTERM trong app:

```dockerfile
CMD ["python", "app.py"]
```

```python
import signal
def handler(signum, frame): cleanup(); sys.exit(0)
signal.signal(signal.SIGTERM, handler)
```

#### ❌ AP11: Container "treat as VM"

```bash
docker exec -it container bash
apt-get install vim
# Edit config trong container
```

**Vấn đề:** Thay đổi mất khi container bị recreate. Không reproducible.

**Fix:** Sửa Dockerfile → rebuild → redeploy.

#### ❌ AP12: 1 container, nhiều process

```dockerfile
# Bỏ Postgres + Redis + Nginx vào 1 container
CMD ["/start-all.sh"]
```

**Vấn đề:** Vi phạm "1 container = 1 process logical". Khó scale, debug, monitor.

**Fix:** Mỗi service = 1 container. Compose link lại.

#### ❌ AP13: `docker exec` cho production change

```bash
docker exec prod-app pip install new-package
```

**Vấn đề:** Thay đổi không persistent, không versioned.

**Fix:** Build image mới, deploy.

### 36.3. Volume / Data anti-patterns

#### ❌ AP14: Bind mount Postgres data trên Mac

```yaml
volumes:
  - ./pgdata:/var/lib/postgresql/data   # Chậm + permission issues
```

**Fix:** Named volume.

#### ❌ AP15: Quên backup volume

Volume có data critical, không backup → 1 ngày kia `docker volume rm` nhầm → mất hết.

**Fix:** Cron job backup, retention policy.

#### ❌ AP16: `docker system prune -a --volumes` không nghĩ

```bash
docker system prune -a --volumes   # Xóa cả volume database!
```

**Fix:** Đọc kỹ trước khi prune. Backup volume quan trọng.

### 36.4. Network anti-patterns

#### ❌ AP17: Dùng default bridge

```bash
docker run nginx              # bridge default
docker run myapp              # bridge default
# myapp không gọi nginx được bằng tên!
```

**Fix:** Custom network:

```bash
docker network create mynet
docker run --network=mynet nginx
docker run --network=mynet myapp
```

#### ❌ AP18: Hardcode container IP

```python
DB_HOST = "172.17.0.3"    # IP có thể đổi
```

**Fix:** Service name:

```python
DB_HOST = "postgres"
```

#### ❌ AP19: Expose port không cần

```dockerfile
EXPOSE 80
EXPOSE 8080
EXPOSE 5432
EXPOSE 6379
# Quá nhiều port — image to spec, hint security
```

**Fix:** Chỉ EXPOSE port app thực sự dùng.

### 36.5. Compose anti-patterns

#### ❌ AP20: `depends_on` không healthcheck

```yaml
app:
  depends_on: [postgres]    # Đợi container start, không đợi service ready
```

**Vấn đề:** App start trước khi Postgres ready → crash.

**Fix:**

```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready"]

app:
  depends_on:
    postgres:
      condition: service_healthy
```

#### ❌ AP21: Hardcode secret trong compose

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: secret123    # ❌
```

**Fix:**

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

Với `.env` file (gitignored).

### 36.6. CI/CD anti-patterns

#### ❌ AP22: Build mỗi môi trường

```
Dev: build → push :dev tag
Staging: build → push :staging tag (image binary khác!)
Prod: build → push :prod tag (image binary khác!)
```

**Vấn đề:** Dev OK, staging OK, prod hỏng → "magic" bug.

**Fix:** Build 1 lần, retag cho từng môi trường.

#### ❌ AP23: Không scan vulnerabilities

Push image production mà không scan → có thể có CVE critical.

**Fix:** Tích hợp Trivy/Scout vào pipeline, fail nếu có CRITICAL.

#### ❌ AP24: Cache thrashing

Mỗi build cache miss layer đầu → invalidate hết. Mỗi build = 20 phút.

**Fix:** Sắp xếp instruction theo cache, dùng cache mount, registry cache.

### 36.7. Production anti-patterns

#### ❌ AP25: Không monitoring

Stack production chạy 6 tháng, không monitor → 1 ngày phát hiện đã crash 3 tuần.

**Fix:** Prometheus + Grafana + Alert. Healthcheck phải có.

#### ❌ AP26: Single point of failure

```yaml
postgres:
  image: postgres:15
  volumes: [pgdata:/var/lib/postgresql/data]
  # Chạy 1 instance, host die = mất hết
```

**Fix production critical:** Managed DB (RDS), hoặc PostgreSQL replication setup.

#### ❌ AP27: Update strategy thiếu suy nghĩ

```bash
docker compose down && docker compose up -d
# Downtime!
```

**Fix:** Rolling update (Swarm/K8s), hoặc blue/green với load balancer.

#### ❌ AP28: Không có rollback plan

Deploy v2 → bug → không biết rollback.

**Fix:** Tag và push v1 image vẫn còn. Rollback = `docker compose up` với tag v1.

#### ❌ AP29: Mount Docker socket vào container untrusted

```yaml
services:
  monitoring:
    image: random-image:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock   # ❌ ROOT EQUIVALENT
```

**Vấn đề:** Image compromise → control toàn bộ Docker daemon → root host.

**Fix:** Đừng mount socket trừ khi cực tin tưởng image. Dùng Docker Socket Proxy nếu cần.

### 36.8. Mindset anti-patterns

#### ❌ AP30: "Docker is magic"

Tin Docker auto fix mọi thứ. Không hiểu bên trong → debug 3 tiếng cho vấn đề 30 giây.

**Fix:** Học bản chất (Phần 1-3 của tài liệu này).

#### ❌ AP31: Cargo cult

Copy compose từ Stack Overflow, không hiểu config.

**Fix:** Hiểu từng option. Đọc docs official.

#### ❌ AP32: Over-engineering

Project 1 person, 2 services → set up K8s cluster + Helm + ArgoCD + Istio.

**Fix:** Đúng tool cho đúng scale. Bắt đầu Compose, upgrade khi cần.

#### ❌ AP33: Premature optimization

Tối ưu image từ 250MB → 50MB trong khi build chưa work xong.

**Fix:** Make it work → make it right → make it fast.

---

### ✅ TÓM TẮT CHƯƠNG 36

#### Top 10 anti-patterns DE thường gặp

1. Dùng `latest` tag
2. Không pin dependency version
3. Cache Dockerfile không tốt (COPY . . trước install)
4. Secret hardcode trong Dockerfile/Compose
5. Run as root
6. Bind mount Postgres trên Mac
7. `depends_on` không kèm healthcheck
8. Build image mỗi môi trường (thay vì retag)
9. Không scan vulnerabilities trước production
10. Container "treat as VM" (exec vào sửa thủ công)

#### Câu hỏi tự kiểm tra

1. Vì sao `depends_on` đơn giản không đủ?
2. Vì sao "build 1 lần, retag" là quy tắc vàng?
3. Mount Docker socket vào container không tin cậy là vấn đề gì?
4. Cache Dockerfile sai làm gì với CI time?
5. 3 mistake mindset hay gặp với Docker?

---

## 🎯 KẾT THÚC PHẦN 10

Phần 10 đóng khung tri thức Docker production:

- CI/CD pipeline hoàn chỉnh
- Trade-off Compose/Swarm/K8s
- 33 anti-patterns + fixes

**Sẵn sàng cho phần cuối:** Roadmap học có hệ thống.

---

# 📘 PHẦN 11: LỘ TRÌNH HỌC VÀ BÀI TẬP

> *Học có roadmap quan trọng hơn học chăm chỉ. Đây là kế hoạch 4-8 tuần được thiết kế cho Data Engineer biến từ "chưa biết Docker" thành "Docker proficient".*

---

## 📖 CHƯƠNG 37: ROADMAP 4-8 TUẦN

### 37.1. Tổng quan roadmap

```
Tuần 1: Nền tảng + tư duy           [Phần 1]
Tuần 2: Dockerfile + CLI            [Phần 2-3]
Tuần 3: Compose + Network + Volume  [Phần 4-6]
Tuần 4: Data Engineering stack      [Phần 7 P1: Ch 17-22]
Tuần 5: Airflow + Spark + Kafka     [Phần 7 P2: Ch 19-25]
Tuần 6: Mini project hoàn chỉnh     [Phần 7: Ch 26]
Tuần 7: Optimization + Security     [Phần 8-9]
Tuần 8: CI/CD + Production          [Phần 10]
```

**Phiên bản nhanh (4 tuần):** Mỗi tuần học 2 phần (cần dedicate full-time).
**Phiên bản chuẩn (8 tuần):** 1 phần/tuần, học part-time 5-10 giờ/tuần.
**Phiên bản chậm (12 tuần):** Phù hợp người vừa học vừa làm việc khác.

### 37.2. TUẦN 1: Nền tảng và tư duy Docker

#### Mục tiêu

Sau tuần này, bạn:

- Hiểu Docker giải quyết vấn đề gì
- Phân biệt rõ container vs VM
- Hiểu namespaces, cgroups, OverlayFS bản chất
- Đã chạy được hello-world, đơn giản

#### Lý thuyết (60-70%)

- Đọc Phần 1, Chương 1, 2, 3 của tài liệu này
- Bonus: video "Containers from Scratch" của Liz Rice (YouTube)
- Bonus: bài blog "What is a Container?" của Julia Evans

#### Thực hành (30-40%)

```bash
# Day 1: Cài Docker, chạy hello-world
docker run hello-world
docker version
docker info

# Day 2-3: Chạy nhiều container, hiểu lifecycle
docker run -d --name web nginx
docker ps
docker logs web
docker exec -it web bash
docker stop web && docker rm web

# Day 4: Quan sát namespaces (Linux)
docker run -d --name nstest alpine sleep 3000
PID=$(docker inspect --format '{{.State.Pid}}' nstest)
ls /proc/$PID/ns/

# Day 5: Demo OOM, CPU limits
docker run --memory=100m --rm alpine sh -c "tail /dev/zero"

# Day 6: Image, layer
docker pull python:3.11-slim
docker history python:3.11-slim
docker images

# Day 7: Tổng ôn
```

#### Bài tập cuối tuần

1. **Bài 1:** Chạy 5 container khác nhau (Postgres, Redis, Nginx, Python, Alpine). Quan sát chúng độc lập, port không xung đột.
2. **Bài 2:** Vẽ sơ đồ kiến trúc Docker (CLI → daemon → containerd → runc → kernel). Giải thích từng tầng làm gì.
3. **Bài 3:** Trên một paper, viết bằng lời mình: "Vì sao container không phải VM?" trong 300 chữ.

#### Tiêu chí đã hiểu

- [ ] Giải thích được "It works on my machine" và Docker fix nó như thế nào
- [ ] Phân biệt được image vs container
- [ ] Vẽ được sơ đồ Docker architecture
- [ ] Hiểu PID namespace, mount namespace bản chất
- [ ] Biết exit code 137 nghĩa là gì

---

### 37.3. TUẦN 2: Dockerfile và CLI

#### Mục tiêu

- Master 30+ lệnh CLI hay dùng
- Viết được Dockerfile production-ready cho Python app
- Hiểu cache, multi-stage build, security

#### Lý thuyết

- Phần 2 (Chương 4-6): CLI
- Phần 3 (Chương 7-10): Dockerfile

#### Thực hành

```bash
# Day 1-2: CLI mastery
# Tạo, list, exec, log, stop, rm tổng hợp
for i in 1 2 3 4 5; do
  docker run -d --name c$i alpine sleep 1000
done
docker ps
docker exec c1 sh -c "echo hello > /tmp/x"
docker diff c1
docker stop $(docker ps -q --filter "name=^c")
docker rm $(docker ps -aq --filter "name=^c")

# Day 3: Viết Dockerfile Python đơn giản
cat > app.py <<EOF
print("Hello from Docker")
EOF

cat > Dockerfile <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
EOF

docker build -t myapp:v1 .
docker run --rm myapp:v1

# Day 4: Multi-stage build
# (Theo Chương 10)

# Day 5: ENV, ARG, secrets
# Build với --build-arg, run với -e

# Day 6: Optimize image
# So sánh size: full vs slim vs alpine
docker images | grep myapp

# Day 7: Build production-ready
# Áp dụng tất cả best practices
```

#### Bài tập cuối tuần

1. **Bài 1:** Viết Dockerfile cho 1 Python script đọc CSV, in summary. Image phải < 200MB.
2. **Bài 2:** Multi-stage Dockerfile cho project Python + C extensions (psycopg2). Image production phải nhỏ hơn 50% so với single-stage.
3. **Bài 3:** Viết Dockerfile cho FastAPI app với:

   - Non-root user
   - HEALTHCHECK
   - Pin version
   - Multi-stage
   - `.dockerignore`

#### Tiêu chí đã hiểu

- [ ] Viết Dockerfile production từ trí nhớ
- [ ] So sánh CMD vs ENTRYPOINT, COPY vs ADD, ARG vs ENV
- [ ] Biết tại sao COPY requirements trước COPY .
- [ ] Áp dụng được multi-stage build
- [ ] Biết kiểm tra image size, dùng dive

---

### 37.4. TUẦN 3: Compose, Network, Volume

#### Mục tiêu

- Viết `compose.yaml` cho multi-service stack
- Debug network giữa containers
- Quản lý persistent data đúng cách

#### Lý thuyết

- Phần 4 (Volume)
- Phần 5 (Network)
- Phần 6 (Compose)

#### Thực hành

```bash
# Day 1: Volume
docker volume create mydata
docker run -v mydata:/data alpine sh -c "echo persistent > /data/file.txt"
docker run -v mydata:/data alpine cat /data/file.txt

# Day 2: Bind mount vs volume
mkdir host-data
docker run -v $(pwd)/host-data:/data alpine sh -c "echo bind > /data/file.txt"
ls host-data/
# Vấn đề permission

# Day 3: Custom network
docker network create datanet
docker run -d --name pg --network=datanet -e POSTGRES_PASSWORD=s postgres:15
docker run --rm --network=datanet alpine nslookup pg

# Day 4: Compose basic
# Tạo compose.yaml với 2-3 service

# Day 5: Compose advanced
# healthcheck, depends_on conditions, profiles

# Day 6: Debug network
# Tạo lỗi: 2 service không cùng network → debug

# Day 7: Tổng hợp
# Compose stack đầy đủ Postgres + Redis + App + Adminer
```

#### Bài tập cuối tuần

1. **Bài 1:** Viết Compose cho Python FastAPI + Postgres + Redis. App có healthcheck, đợi Postgres healthy trước khi start.
2. **Bài 2:** Volume backup/restore: dump Postgres data, xóa volume, restore.
3. **Bài 3:** Debug puzzle: cho 1 compose file có bug network (2 service khác network). Tự fix.

#### Tiêu chí đã hiểu

- [ ] Phân biệt named volume vs bind mount, biết khi nào dùng
- [ ] Compose service nói chuyện qua service name
- [ ] `depends_on: condition: service_healthy` vs basic
- [ ] Debug "app không kết nối DB" trong < 5 phút
- [ ] Backup volume Postgres

---

### 37.5. TUẦN 4: Data Engineering stack basics

#### Mục tiêu

- Setup được Postgres, MinIO, dbt với Docker
- Hiểu nguyên tắc container hóa ETL job

#### Lý thuyết

- Phần 7, Chương 17 (Why Docker for DE)
- Phần 7, Chương 18 (ETL container)
- Phần 7, Chương 22 (Database)
- Phần 7, Chương 23 (dbt)
- Phần 7, Chương 24 (MinIO)

#### Thực hành

```bash
# Day 1: Postgres production-grade
# Init script, healthcheck, backup

# Day 2: Container hóa Python ETL
# Stateless, env config, log stdout

# Day 3: dbt với Postgres
# profiles.yml qua env, dbt run trong container

# Day 4: MinIO + boto3
# Tạo bucket, upload/download

# Day 5-6: Combine
# ETL job: CSV → Python transform → Parquet to MinIO → load to Postgres

# Day 7: Integration test
# pytest + testcontainers
```

#### Bài tập cuối tuần

**Mini ETL Project:**

- Đọc CSV
- Transform với pandas
- Lưu Parquet vào MinIO
- Load vào Postgres
- dbt model transform thêm
- Tất cả qua Docker Compose

#### Tiêu chí đã hiểu

- [ ] Setup Postgres + init script + healthcheck
- [ ] Container ETL hoàn chỉnh (stateless, log stdout, exit code đúng)
- [ ] dbt run trong container, kết nối Postgres
- [ ] MinIO + boto3 (Python) hoặc s3a (Spark)

---

### 37.6. TUẦN 5: Airflow, Spark, Kafka

#### Mục tiêu

- Airflow stack chạy ổn định
- Hiểu Spark standalone với Compose
- Debug Kafka advertised.listeners

#### Lý thuyết

- Phần 7, Chương 19 (Airflow)
- Phần 7, Chương 20 (Spark)
- Phần 7, Chương 21 (Kafka)

#### Thực hành

```bash
# Day 1-2: Airflow production-like
# Custom image với providers
# DAG mẫu: Postgres → S3

# Day 3: Spark standalone
# Submit PySpark job, đọc/ghi MinIO

# Day 4-5: Kafka KRaft
# Producer/consumer Python
# Fix advertised.listeners

# Day 6: Combine
# DAG Airflow trigger Spark job qua SparkSubmitOperator

# Day 7: Debug
# Tạo lỗi cố ý → debug
```

#### Bài tập cuối tuần

1. **Bài 1:** Airflow DAG đầy đủ: extract từ Postgres → transform → load lên MinIO Parquet.
2. **Bài 2:** Spark job đọc Parquet từ MinIO, tính aggregation, ghi back MinIO.
3. **Bài 3:** Kafka producer/consumer Python chạy bằng Docker, message JSON.

#### Tiêu chí đã hiểu

- [ ] Airflow stack lên ổn định, DAG chạy không lỗi
- [ ] Submit PySpark job qua container
- [ ] Producer/consumer Kafka qua mạng container
- [ ] Hiểu vấn đề Kafka listeners

---

### 37.7. TUẦN 6: Mini Project hoàn chỉnh

#### Mục tiêu

Build Mini Data Platform (Chương 26):

- Airflow + Postgres + MinIO + dbt + Jupyter
- Pipeline end-to-end

#### Lý thuyết

- Phần 7, Chương 26 (đọc kỹ)

#### Thực hành

Toàn bộ project Chương 26.

**Lịch:**

- Day 1: Setup cấu trúc thư mục, viết compose.yaml
- Day 2: Build Airflow + Postgres + MinIO, lên stack
- Day 3: Viết DAG 1 (CSV → Postgres)
- Day 4: Viết DAG 2 + 3 (Postgres → MinIO → Warehouse)
- Day 5: dbt models (staging + marts)
- Day 6: Jupyter notebook analysis
- Day 7: Documentation, README, screenshot

#### Bài tập

**Project deliverables:**

1. GitHub repo với code đầy đủ
2. README có:
   - Diagram kiến trúc
   - Steps để chạy
   - Screenshot Airflow UI, MinIO console, dbt docs
3. Demo video 3-5 phút

#### Tiêu chí đã hiểu

- [ ] Project chạy end-to-end từ git clone
- [ ] DAGs hoàn thành success
- [ ] Data flow đúng các tier
- [ ] dbt models build success, test pass
- [ ] Có thể giải thích từng component khi được hỏi

---

### 37.8. TUẦN 7: Optimization + Security

#### Mục tiêu

- Tối ưu image (size, build time)
- Apply security best practices
- Debug Docker chuyên nghiệp

#### Lý thuyết

- Phần 8 (Chương 27-31)
- Phần 9 (Chương 32-33)

#### Thực hành

```bash
# Day 1: Image optimization
# Lấy 1 image trong project Tuần 6, tối ưu từ ~1GB → < 300MB

# Day 2: BuildKit cache mount
# Đo build time trước/sau

# Day 3: Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 --push -t ... .

# Day 4: Security scan
trivy image myimage:v1
# Fix CVE critical

# Day 5: Resource limits
# Set --memory --cpus cho tất cả service trong project

# Day 6: Debug exercises
# 5-10 bug cố ý → debug

# Day 7: Performance benchmark
# Đo trước/sau optimization
```

#### Bài tập cuối tuần

1. **Bài 1:** Image Optimization Challenge: lấy image trong Mini Project, giảm size 50%+.
2. **Bài 2:** Security scan tất cả image, fix CVE HIGH/CRITICAL.
3. **Bài 3:** Debug puzzle book: 10 lỗi cố ý, tự debug.

#### Tiêu chí đã hiểu

- [ ] Tối ưu image từ 1GB → 300MB
- [ ] Build time giảm 50% với cache mount
- [ ] Pass Trivy scan với severity HIGH/CRITICAL
- [ ] Debug được top 10 lỗi phổ biến

---

### 37.9. TUẦN 8: CI/CD + Production mindset

#### Mục tiêu

- Build CI/CD pipeline GitHub Actions cho project
- Tagging strategy chuẩn
- Hiểu deployment patterns

#### Lý thuyết

- Phần 10 (Chương 34-36)

#### Thực hành

```bash
# Day 1: GitHub Actions setup
# Workflow build + test + scan

# Day 2: Push to registry
# Tag SemVer + Git SHA

# Day 3: Multi-platform CI
# Build amd64 + arm64

# Day 4: Integration tests trong CI
# testcontainers

# Day 5: Promote pattern
# dev → staging → prod via retag

# Day 6: Anti-patterns audit
# Review project, tìm và fix anti-patterns

# Day 7: Final review
```

#### Bài tập cuối tuần

1. **Bài 1:** Add CI/CD vào project Mini Data Platform.
2. **Bài 2:** Tagging strategy: triển khai SemVer + Git SHA.
3. **Bài 3:** Anti-patterns audit: tìm 5 anti-patterns trong project và fix.

#### Tiêu chí đã hiểu

- [ ] CI/CD pipeline chạy mỗi PR
- [ ] Image được tag theo SemVer + SHA
- [ ] Scan vuln tích hợp
- [ ] Project pass audit không còn anti-pattern top 10

---

### 37.10. Sau roadmap — What's next?

Sau 8 tuần, bạn đã có:

- Solid foundation Docker
- Master Compose
- Build, ship, optimize image production-grade
- CI/CD đầy đủ
- Mini data platform working

**Hành trình tiếp theo:**

#### a) Kubernetes (3-6 tháng)

- "Kubernetes in Action" — Marko Lukša (book)
- "Kubernetes Up & Running" — Hightower (book)
- CKA, CKAD certification
- Hands-on: chuyển Mini Project lên K8s

#### b) Cloud platforms

- AWS ECS, EKS, EMR
- GCP GKE, Dataproc
- Azure AKS

#### c) Advanced Data Engineering

- Airflow on K8s (KubernetesExecutor)
- Spark on K8s
- Argo Workflows
- Kafka Operator (Strimzi)

#### d) Observability

- Prometheus + Grafana
- Loki + Tempo
- OpenTelemetry

#### e) Security hardening

- Falco (runtime security)
- OPA Gatekeeper (policy)
- Image signing (Cosign)
- Network policies

#### f) FinOps

- Cost analysis container workload
- Right-sizing
- Spot instances

### 37.11. Cộng đồng và resources

#### Books

- "Docker Deep Dive" — Nigel Poulton
- "Container Security" — Liz Rice
- "Designing Data-Intensive Applications" — Martin Kleppmann (foundation for DE)

#### Online courses

- Docker for Beginners — Bret Fisher (Udemy)
- KodeKloud Docker
- A Cloud Guru Docker

#### YouTube channels

- Bret Fisher
- DevOps Toolkit (Viktor Farcic)
- TechWorld with Nana
- Liz Rice (container internals)

#### Blogs

- iximiuz.com (Ivan Velichko) — container internals
- Julia Evans — zines & explanations
- Docker official blog

#### Practice platforms

- play-with-docker.com (free Docker playground)
- Katacoda (Docker scenarios)
- KillerCoda

---

### ✅ TÓM TẮT CHƯƠNG 37

#### Self-assessment cuối roadmap

Sau 8 tuần, bạn nên trả lời được:

**Conceptual:**

- [ ] Docker giải quyết vấn đề gì? (Story-tellable, 5 phút)
- [ ] Container khác VM bản chất ở đâu?
- [ ] Namespace + cgroups + OverlayFS làm gì?
- [ ] Image, container, layer, registry — relationship?

**Practical:**

- [ ] Viết Dockerfile production-ready từ blank (Python + Postgres client)
- [ ] Setup multi-service stack qua Compose với healthcheck
- [ ] Debug "app không kết nối DB" trong 5 phút
- [ ] Tối ưu image > 50% size
- [ ] CI/CD pipeline build + scan + push

**Data Engineering specific:**

- [ ] Setup Airflow stack production-like
- [ ] Container hóa ETL Python (stateless, idempotent)
- [ ] Spark job trong Docker
- [ ] Kafka producer/consumer working
- [ ] dbt run từ container
- [ ] Mini data platform end-to-end

**Production mindset:**

- [ ] Hiểu trade-offs (Compose vs K8s)
- [ ] Tagging strategy (SemVer + SHA)
- [ ] Security baseline (non-root, scan, secrets)
- [ ] Resource limits cho production
- [ ] Top 10 anti-patterns và fix

Nếu **trả lời được 80%+**, bạn đã đạt **Docker Proficient level** — sẵn sàng cho job DE/Platform Engineer với Docker requirement.

---

## 🎓 LỜI KẾT

Bạn đã hoàn thành tài liệu **~10,000+ dòng** Docker handbook chuyên sâu cho Data Engineer. Đây không phải tất cả về Docker — không tài liệu nào cover được tất cả — nhưng đủ để bạn:

1. **Hiểu sâu** bản chất container, không bị mù mờ "magic"
2. **Sử dụng thành thạo** Docker cho công việc Data Engineering hàng ngày
3. **Tự debug** các lỗi mà không cần Google mỗi lần
4. **Có framework** để học tiếp các topic nâng cao (K8s, cloud)

### Bạn đã đi qua

```
┌─────────────────────────────────────────────────────────────┐
│ PHẦN 1: Nền tảng và tư duy                                  │
│   - Vì sao Docker? Container vs VM? Bản chất bên trong      │
│                                                              │
│ PHẦN 2-3: CLI và Dockerfile                                  │
│   - 30+ lệnh CLI, Dockerfile production-ready               │
│                                                              │
│ PHẦN 4-6: Storage, Network, Compose                          │
│   - Volume, bind mount, custom network, multi-service       │
│                                                              │
│ PHẦN 7: Data Engineering ⭐                                  │
│   - Airflow, Spark, Kafka, Postgres, dbt, MinIO, Jupyter    │
│   - Mini Data Platform hoàn chỉnh                           │
│                                                              │
│ PHẦN 8-9: Advanced + Performance                             │
│   - BuildKit, multi-platform, security, debug, optimize     │
│                                                              │
│ PHẦN 10: CI/CD + Production                                  │
│   - GitHub Actions, Compose vs K8s, 33 anti-patterns        │
│                                                              │
│ PHẦN 11: Roadmap 4-8 tuần                                   │
└─────────────────────────────────────────────────────────────┘
```

### Nguyên tắc cuối cùng

Sau khi đọc xong tài liệu này, hãy nhớ **3 nguyên tắc** quan trọng nhất:

#### 1. Hiểu bản chất, không cargo cult

Mỗi khi gặp lệnh Docker, hỏi: **Why? What? How?** Hiểu rồi mới copy. Không hiểu mà copy → bug magic chờ bạn.

#### 2. Tool, không phải religion

Docker là **một tool** trong toolset Data Engineer. Có lúc dùng Docker là sai (Chương 33). Đừng "Dockerize everything".

#### 3. Production mindset từ ngày đầu

Code chạy local OK chưa đủ. Hỏi:

- Có monitoring chưa?
- Có resource limit chưa?
- Có secret management chưa?
- Có backup chưa?
- Có rollback plan chưa?

Đây là dấu hiệu của Senior Data Engineer.

### Lời chúc

**Chúc bạn thành công** trên hành trình Data Engineering. Docker chỉ là một bước — nhưng là bước nền tảng quan trọng. Master nó, bạn đã sẵn sàng cho Kubernetes, cloud platforms, và các topic nâng cao khác.

Đừng quên:

- **Practice > Theory** — Mỗi chương phải có hands-on
- **Build projects** — GitHub repo của bạn là CV thật
- **Help others** — Dạy lại là cách học nhanh nhất
- **Stay curious** — Docker, container ecosystem evolve nhanh, đọc blog, follow expert

---

> **Happy Dockerizing! 🐳**
>
> *Tài liệu này được viết với mục đích educational, dành tặng cộng đồng Data Engineer Việt Nam. Sao chép, chia sẻ, sửa đổi tự do. Nếu thấy hữu ích, hãy chia sẻ cho đồng nghiệp.*

---

## 📚 PHỤ LỤC: BẢNG CHEAT SHEET TỔNG HỢP

### Docker CLI

```bash
# Container
docker run -d --name X -p H:C img       # Run nền
docker run --rm -it img bash             # Shell tương tác
docker ps / docker ps -a                 # List
docker exec -it X bash                   # Vào shell
docker logs -f X                         # Tail logs
docker stop X / docker start X           # Stop/start
docker rm -f X                           # Remove force
docker inspect X                         # JSON metadata
docker stats                             # Resource usage

# Image
docker build -t img:tag .                # Build
docker push img:tag                      # Push registry
docker pull img:tag                      # Pull
docker images                            # List
docker rmi img                           # Remove
docker history img                       # Layer history

# Volume
docker volume create/ls/inspect/rm

# Network
docker network create/ls/inspect/rm

# System
docker system df                         # Disk usage
docker system prune -a                   # Cleanup

# Compose
docker compose up -d                     # Lên stack
docker compose down                      # Tắt stack
docker compose down -v                   # ⚠️ Cũng xóa volume
docker compose ps                        # Status
docker compose logs -f                   # Logs
docker compose exec X bash               # Exec
docker compose build                     # Build
docker compose pull                      # Pull images
docker compose run --rm X cmd            # One-off
```

### Dockerfile template (Python production)

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir /wheels -r requirements.txt

# Runtime
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 tini && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -r app && useradd -r -g app app

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY --chown=app:app . .
USER app

HEALTHCHECK CMD python -c "..." || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "python", "-m", "myapp"]
CMD ["--mode=daily"]
```

### Compose template (data stack)

```yaml
name: my-project

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s
    deploy:
      resources:
        limits:
          memory: 1g

  app:
    build: .
    environment:
      DB_HOST: postgres
      DB_PASSWORD: ${DB_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  pgdata:
```

### Exit codes

| Code | Meaning                |
| ---- | ---------------------- |
| 0    | Success                |
| 1    | General error          |
| 125  | Docker daemon error    |
| 126  | Command not executable |
| 127  | Command not found      |
| 137  | SIGKILL (OOM)          |
| 143  | SIGTERM                |

### Common ports

| Service           | Port |
| ----------------- | ---- |
| Airflow webserver | 8080 |
| Spark master UI   | 8081 |
| MinIO API         | 9000 |
| MinIO Console     | 9001 |
| Kafka             | 9092 |
| Postgres          | 5432 |
| MySQL             | 3306 |
| Redis             | 6379 |
| Jupyter           | 8888 |
| Grafana           | 3000 |
| Prometheus        | 9090 |

---

**HẾT — Chúc bạn thành công! 🚀**
