# Airflow And dbt Pipeline

Tài liệu này mô tả pipeline sau crawler: Airflow chỉ load JSON batch đã có sẵn
từ MinIO vào warehouse Postgres, rồi chạy dbt. Airflow không chạy
`suumo_links`, `suumo_html`, hoặc `suumo_page`.

Toàn bộ Docker Compose, env mẫu và Makefile vận hành pipeline nằm trong
`pipeline/`; root Makefile không còn target pipeline.

## Kiến trúc

Source stack hiện tại vẫn giữ nguyên:

```text
suumo_page -> MinIO suumo/data/*.json.gz -> source DB load_batches.pending
```

Pipeline stack mới xử lý từ đó:

```text
load_batches.pending
-> Airflow DAG suumo_load_to_warehouse
-> raw.suumo_parser_records trong warehouse Postgres
-> dbt staging
-> dbt mart
```

Warehouse dùng Postgres container riêng, khác source Postgres. Trong container
warehouse có hai database:

- `airflow_metadata`: metadata nội bộ của Airflow.
- `japan_warehouse`: dữ liệu warehouse cho dbt và PowerBI sau này.

## Cấu hình pipeline

Copy env mẫu:

```bash
cp pipeline/.env.example pipeline/.env
nano pipeline/.env
```

Các giá trị quan trọng:

```env
SOURCE_DOCKER_NETWORK=crawler_shared_net
SOURCE_POSTGRES_HOST=postgres
SOURCE_POSTGRES_DB=japan_analysis
SOURCE_POSTGRES_USER=japan_analysis_user
SOURCE_POSTGRES_PASSWORD=japan_analysis_password_change_me
SOURCE_MINIO_ENDPOINT_URL=http://minio:9000
SOURCE_MINIO_ROOT_USER=minioadmin
SOURCE_MINIO_ROOT_PASSWORD=minioadmin_change_me

WAREHOUSE_DB=japan_warehouse
WAREHOUSE_POSTGRES_HOST_PORT=15433

AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=admin_change_me
SUUMO_LOAD_DAG_SCHEDULE=0 */3 * * *
SUUMO_LOAD_BATCH_LIMIT=20
```

`AIRFLOW_PYTHON_VERSION` nên để dạng major.minor như `3.12`. Nếu máy/base image
trả ra patch version như `3.12.9`, Dockerfile sẽ tự normalize về `3.12` khi tải
Airflow constraints.

Nếu chạy local, các biến `SOURCE_POSTGRES_DB`, `SOURCE_POSTGRES_USER`,
`SOURCE_POSTGRES_PASSWORD` phải khớp với `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD` trong root `.env`. Nếu chạy trên VPS release, source DB
thường là `suumo_crawler`, user thường là `suumo_user`; cần chỉnh theo `.env`
thật trên VPS.

Nếu pipeline chạy cạnh release compose trên VPS, source network thường là:

```env
SOURCE_DOCKER_NETWORK=suumo_crawler_release_release_net
```

Kiểm tra network source đang có:

```bash
docker network ls
```

## Start pipeline

Source stack phải chạy trước để pipeline join được source network:

```bash
make infra-up-d
```

Validate compose:

```bash
make -C pipeline config
```

Kiểm tra Airflow container có đăng nhập được source Postgres không:

```bash
make -C pipeline check-source-db
```

Nếu lỗi `password authentication failed`, sửa `SOURCE_POSTGRES_*` trong
`pipeline/.env` cho khớp source `.env`, rồi recreate Airflow service:

```bash
make -C pipeline recreate
```

Build Airflow image có dbt:

```bash
make -C pipeline build
```

Start warehouse Postgres và Airflow:

```bash
make -C pipeline up-d
```

`up-d` trong `pipeline/Makefile` phụ thuộc `build`, nên chạy `up-d` cũng sẽ
build image Airflow trước. Lệnh `build` riêng vẫn hữu ích khi muốn kiểm tra lỗi
cài dependency trước khi start service.

Mở Airflow UI:

```text
http://localhost:8080
```

Đăng nhập bằng `AIRFLOW_ADMIN_USERNAME` và `AIRFLOW_ADMIN_PASSWORD` trong
`pipeline/.env`.

## Event notify từ crawler

Airflow có fallback schedule, nhưng có thể trigger ngay khi `suumo_page` tạo batch
xong. Bật trong env của source crawler:

```env
AIRFLOW_NOTIFY_ENABLED=true
AIRFLOW_API_BASE_URL=http://airflow-webserver:8080
AIRFLOW_DAG_ID=suumo_load_to_warehouse
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin_change_me
AIRFLOW_NOTIFY_TIMEOUT_SECONDS=10
```

Notify là best-effort. Nếu Airflow API lỗi, crawler chỉ log warning và batch vẫn
ở `load_batches.status = 'pending'`; DAG schedule sau đó vẫn có thể load batch.

## Polling fallback

DAG `suumo_load_to_warehouse` chạy theo:

```env
SUUMO_LOAD_DAG_SCHEDULE=0 */3 * * *
```

Giá trị này nghĩa là mỗi 3 tiếng Airflow query source DB tìm
`load_batches.status = 'pending'`.

Nếu DAG được trigger bằng API với `conf.batch_id`, DAG chỉ xử lý batch đó nếu nó
còn `pending`. Nếu DAG chạy theo lịch, DAG xử lý tối đa
`SUUMO_LOAD_BATCH_LIMIT` batch pending theo thứ tự `created_at`.

## dbt

dbt project nằm ở:

```text
analytics/dbt
```

dbt được cài trong virtualenv riêng `/opt/airflow/dbt_venv` bên trong Airflow
image để tránh conflict dependency với Airflow. Dockerfile thêm virtualenv này
vào `PATH`, nên trong container vẫn gọi được lệnh `dbt` trực tiếp.

Các model v1:

- `raw.suumo_parser_records`: table do loader tạo và ghi dữ liệu JSONB.
- Loader chỉ ghi parser record có `is_valid = true` vào raw warehouse.
- Parser record có `is_valid = false` không được ghi vào warehouse và được tính
  vào `load_batches.failed_count`.
- `failed_count > 0` không tự làm batch failed; batch chỉ `failed` khi lỗi cấp
  file/hệ thống khiến loader không hoàn tất.
- `staging.stg_suumo_rentals`: view extract JSONB thành cột dễ dùng.
- `mart.mart_suumo_rentals_current`: table current record cho PowerBI.

Chạy thủ công:

```bash
make -C pipeline dbt-debug
make -C pipeline dbt-run
make -C pipeline dbt-test
```

## Lệnh vận hành

Xem trạng thái:

```bash
make -C pipeline ps
```

Xem log:

```bash
make -C pipeline logs
make -C pipeline logs service=airflow-scheduler
```

Stop pipeline, giữ volume:

```bash
make -C pipeline down
```

Xóa cả warehouse/Airflow metadata volume:

```bash
make -C pipeline clean-volumes
```

## Kiểm tra kết quả

Xem source batch pending/success:

```sql
SELECT batch_id, status, row_count, inserted_count, failed_count
FROM load_batches
ORDER BY batch_id DESC
LIMIT 20;
```

Xem warehouse raw:

```sql
SELECT count(*)
FROM raw.suumo_parser_records;
```

Xem mart cho PowerBI:

```sql
SELECT *
FROM mart.mart_suumo_rentals_current
LIMIT 20;
```
