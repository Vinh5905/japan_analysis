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
-> dbt staging.stg_suumo_parser_records (một dòng theo source task_id)
-> dbt intermediate.int_suumo__dates/costs/building/parking/address/contract/layout
   (mỗi view một dòng theo task_id)
-> dbt intermediate.int_suumo_rentals_history (lịch sử theo task_id)
   và intermediate.int_suumo__station_access (nhiều dòng theo task_id)
```

Warehouse dùng Postgres container riêng, khác source Postgres. Trong container
warehouse có hai database:

- `airflow_metadata`: metadata nội bộ của Airflow.
- `japan_warehouse`: dữ liệu warehouse cho dbt và PowerBI sau này.

## Cấu hình local và production

Để thử tính năng trên máy local, dùng Compose cơ sở và `pipeline/.env`:

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
DBT_DOCS_PORT=8081
SUUMO_LOAD_DAG_SCHEDULE=0 */3 * * *
SUUMO_LOAD_BATCH_LIMIT=20
SUUMO_DBT_CONCURRENCY=4
```

`AIRFLOW_PYTHON_VERSION` nên để dạng major.minor như `3.12`. Nếu máy/base image
trả ra patch version như `3.12.9`, Dockerfile sẽ tự normalize về `3.12` khi tải
Airflow constraints. Compose local không áp `mem_limit`, `cpus`, `pids_limit`
cho warehouse, Airflow webserver hoặc scheduler; Airflow dùng số worker mặc
định. Các biến resource limit cũ trong `pipeline/.env` không còn tác dụng và
có thể xóa.

`DBT_CHARTS_PORT` mặc định là `3000` cho local. Production example dùng port
riêng `13000`; service Charts chỉ chạy khi bật Compose profile `charts`.

Production dùng `pipeline/.env.production` và Compose override riêng:

```bash
cp pipeline/.env.production.example pipeline/.env.production
nano pipeline/.env.production
make -C pipeline production-config
make -C pipeline production-up-d
```

File production mẫu có Compose project và host ports riêng để không đụng local,
đồng thời chứa giới hạn RAM/CPU/PID cho VPS. Đổi credentials và source network
theo máy production trước khi chạy. `pipeline/.env.production` bị Git ignore;
root `.env.production` là file khác và không được pipeline tự đọc. Không dùng
lệnh `make -C pipeline up-d` để khởi động production vì lệnh đó luôn đọc
`pipeline/.env` và chỉ dùng Compose local.

Nếu chạy local, các biến `SOURCE_POSTGRES_DB`, `SOURCE_POSTGRES_USER`,
`SOURCE_POSTGRES_PASSWORD` phải khớp với `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD` trong root `.env`. Nếu chạy trên VPS release, source DB
thường là `suumo_crawler`, user thường là `suumo_user`; cần chỉnh theo `.env`
thật trên VPS.

Nếu pipeline chạy cạnh release compose trên VPS, source network production thường là:

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

`up-d` và `recreate` build image rồi sinh manifest Airflow bằng `dbt parse`
trước khi bật scheduler/webserver. Luồng `production-up-d` cũng làm bước này.
Manifest riêng nằm ở `analytics/dbt/target/airflow/manifest.json`, thay thế nguyên tử
và có fingerprint của model, macro, test, seed, cấu hình và warehouse environment.
Scheduler chỉ đọc manifest, không gọi dbt hoặc warehouse lúc parse DAG.
Nếu sửa dbt code/config, chạy `make -C pipeline dbt-airflow-manifest`; task từ chối
thực thi khi fingerprint cũ. Manifest Charts/docs tại `target/manifest.json` được giữ riêng. Lệnh `build` riêng vẫn hữu ích khi muốn kiểm tra lỗi
cài dependency trước khi start service.

Mở Airflow UI:

```text
http://localhost:8080
```

Đăng nhập bằng `AIRFLOW_ADMIN_USERNAME` và `AIRFLOW_ADMIN_PASSWORD` trong
`pipeline/.env`.

Trong Airflow, mở DAG `suumo_load_to_warehouse` rồi chọn **Graph** để xem thứ
tự task, hoặc **Grid** để xem từng lần chạy và log. Nếu DAG đang ở trạng thái
paused, bật công tắc của DAG trước khi chờ lịch chạy. Có thể dùng **Trigger DAG**
để chạy ngay; khi không truyền `conf.batch_id`, DAG chỉ lấy các batch `pending`.

## Xem dbt docs

Sau khi warehouse đã chạy và các model đã được build, bật web server dbt docs:

```bash
make -C pipeline dbt-docs-up
```

Mở `http://localhost:8081` (hoặc cổng `DBT_DOCS_PORT` trong `pipeline/.env`).
Service chạy `dbt docs generate` trước khi phục vụ trang, nên catalog và lineage
phản ánh các relation đang có tại lúc khởi động. Trong trang docs, chọn
**Lineage Graph** để xem nhánh station riêng và các view theo chủ đề. Khi schema
model thay đổi, dừng rồi bật lại service để tạo catalog mới.

```bash
make -C pipeline dbt-docs-down
```

## Xem dashboard dbt Charts

Runtime dbt trong Airflow image pin chung ba package tương thích:

```text
dbt-core==1.11.15
dbt-postgres==1.11.0
dbt-charts[postgresql]==0.8.0
```

Project tiếp tục dùng dbt Core 1.x; không cần dbt v2 hoặc virtualenv Charts
riêng. Board và config nằm trong `analytics/dbt/charts/` và
`analytics/dbt/dbt_charts.yml`.

Sau khi mart/analytics đã build thành công, validate YAML và EXPLAIN query:

```bash
make -C pipeline dbt-charts-validate
make -C pipeline dbt-charts-smoke
```

Bật local server:

```bash
make -C pipeline dbt-charts-up
```

Mở `http://localhost:3000` hoặc port `DBT_CHARTS_PORT` trong
`pipeline/.env`. Xem log và dừng service:

```bash
make -C pipeline dbt-charts-logs
make -C pipeline dbt-charts-down
```

Render một board ra file HTML trong `analytics/dbt/renders/`:

```bash
make -C pipeline dbt-charts-render \
  board=charts/rental_market_overview.yml format=html
```

Các board query warehouse bằng profile `japan_analysis`. Chúng dùng hostname
`warehouse-postgres` trong container và đọc `target/manifest.json` do dbt Core
tạo để resolve `ref()`.

Smoke test thực thi query read-only và kiểm tra population/filter/empty state,
grain KPI và distinct count station. EXPLAIN của PostgreSQL không trả result
schema nên warehouse validation vẫn có warning về column check; render/smoke
là bước kiểm tra thực tế. Xem `docs/suumo-rental-bi.md` về ý nghĩa các board,
insight, cache refresh và kết quả kiểm chứng. Image có `fonts-noto-cjk` để xuất
nhãn tiếng Nhật đúng trong PNG/PDF.

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

dbt và dbt Charts được cài trong virtualenv riêng `/opt/airflow/dbt_venv` bên
trong Airflow image để tránh conflict dependency với Airflow. Dockerfile thêm
virtualenv này vào `PATH`, nên trong container gọi trực tiếp được cả `dbt` và
`dct`.

Các thành phần hiện tại:

- `raw.suumo_parser_records`: table do loader tạo và ghi dữ liệu JSONB.
- Loader chỉ ghi parser record có `is_valid = true` vào raw warehouse.
- Parser record có `is_valid = false` không được ghi vào warehouse và được tính
  vào `load_batches.failed_count`.
- `failed_count > 0` không tự làm batch failed; batch chỉ `failed` khi lỗi cấp
  file/hệ thống khiến loader không hoàn tất.
- Loader kiểm tra SHA-256 của file gzip, `row_count`, cấu trúc record và
  `task_id` trước khi ghi. Các record hợp lệ được upsert trong một transaction;
  lỗi ghi làm cả batch `failed`.
- `staging.stg_suumo_parser_records`: view một dòng mỗi `task_id`, trích JSON,
  đổi tên sang tiếng Anh, ép kiểu và chuẩn hóa text phục vụ parse. Các text nguồn
  vẫn được giữ để truy vết; staging không join hay aggregate.
- Bảy view `intermediate.int_suumo__dates`, `__costs`, `__building`, `__parking`,
  `__address`, `__contract`, `__layout` xử lý theo chủ đề. Mỗi view chỉ xuất
  `task_id` và các cột phát sinh của mình; `__layout` tổng hợp `layout_detail`
  thành cột, không tăng số dòng. Phí parking nằm trong `__parking`.
- `intermediate.int_suumo__station_access` là table chi tiết, một dòng cho
  mỗi dòng access không rỗng/không phải sentinel. Khóa là
  `(task_id, access_order)`; `raw_line` giữ text trước NFKC, `parse_status`
  là `parsed` hoặc `unparsed`. Dòng lỗi vẫn tồn tại, các trường ga đã parse
  là `NULL`. Bảng này độc lập với history; không chọn một ga chính.
- `intermediate.int_suumo_rentals_history` là table lịch sử 112 cột, một dòng
  mỗi `task_id`. Nó giữ `station_access` dạng text để truy vết nhưng không join
  bảng ga. `quality_issue_count` đếm ba cờ: thiếu rent/diện tích, tầng vượt
  số tầng tòa nhà và lỗi parse layout. Các cột `DEFERRED/SKIP` chỉ là raw text.
- History hiện là đầu ra nội bộ để kiểm tra và làm đầu vào cho mart về sau;
  mart SCD2 và latest-known view đã được triển khai; cột `record_origin` phân
  biệt operational với notebook seed. Chưa có bảng layout nhiều dòng.

Với warehouse đã từng chạy các model cũ, sau khi bảng lịch sử mới chạy thành
công, đối chiếu đủ cột/giá trị và test đạt, xóa riêng các relation cũ theo thứ
tự phụ thuộc, không dùng `CASCADE`:

```sql
DROP VIEW IF EXISTS intermediate.int_suumo_features;
DROP VIEW IF EXISTS intermediate.int_suumo_station;
DROP VIEW IF EXISTS intermediate.int_suumo_layout_detail;
DROP VIEW IF EXISTS staging.int_suumo_source;
DROP TABLE IF EXISTS staging.stg_suumo_rentals;
DROP TABLE IF EXISTS mart.mart_suumo_rentals_current;
```

Chạy thủ công:

```bash
make -C pipeline dbt-debug
make -C pipeline dbt-run
make -C pipeline dbt-test
```

Nếu batch `failed`, hoặc `loading` quá 60 phút, kiểm tra lỗi và file nguồn rồi
đưa lại về `pending` thủ công:

```bash
make -C pipeline recover-batch batch_id=123
make -C pipeline recover-batch batch_id=123 opts="--stale-minutes 120"
```

Lệnh từ chối batch `success`, `pending` hoặc `loading` chưa quá hạn. Không có
retry tự động. DAG vẫn chạy dbt cho batch thành công trong cùng lượt, sau đó
báo thất bại nếu có batch load lỗi.

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

Xem staging và intermediate history:

```sql
SELECT count(*) FROM staging.stg_suumo_parser_records;
SELECT * FROM intermediate.int_suumo_rentals_history LIMIT 20;
SELECT task_id, access_order, raw_line, parse_status, station_line,
       station_name, access_mode, total_travel_minutes
FROM intermediate.int_suumo__station_access
ORDER BY task_id, access_order LIMIT 20;
```

## Rental price mart

Mart SCD2, DBML, quy tắc giá/diện tích, late arrival và truy vấn as-of được mô tả
trong [suumo-rental-price-mart.md](suumo-rental-price-mart.md).
DAG dùng Cosmos 1.15.1 `LOCAL`/subprocess để chạy từng model và test riêng,
giữ dependency theo manifest. Lệnh full build thủ công vẫn là
`make -C pipeline dbt-build`.
BI chỉ refresh sau khi DAG thành công; dbt không publish nguyên tử toàn schema.

## Notebook raw seed và analytics

Snapshot notebook 17.927 record được copy vào dbt seed
`raw.suumo_parser_records_seed`. Chạy bootstrap một lần bằng
`make -C pipeline dbt-seed-notebook`; staging union seed với raw vận hành và ưu
tiên operational khi trùng `task_id`. DAG tái sử dụng relation seed đã có, chỉ chạy các test seed;
không reload file 18 MB sau mỗi batch. Warehouse mới phải seed trước lần DAG
đầu tiên. Chi tiết ba data product BI nằm ở
[`suumo-rental-analytics.md`](suumo-rental-analytics.md).

## Task graph và chạy lại dbt

DAG ID vẫn là `suumo_load_to_warehouse`. Nhóm `dbt.models` gồm `staging`,
`intermediate`, `marts`, `analytics`: 26 model, mỗi model có `run` và các data
test riêng gom vào `test` nếu có. Hai unit test chạy trước model tương ứng.
Cosmos dùng `AFTER_EACH` với detached multi-parent tests. Test liên model có
một task duy nhất, chờ tất cả input và chặn consumer chung khi các input đã là
ancestor của consumer. Ba scenario test không có `ref()` nằm trong
`standalone_tests`; raw và seed giữ đầy đủ test. Full run thực thi đúng 88 data
test và 2 unit test, không chạy test lại sau toàn graph.

Trigger DAG với JSON mặc định `{"mode": "load_and_transform", "model": null}`
để load pending batches rồi transform. Không có batch thành công thì nhánh dbt
skipped; batch lỗi làm task cuối `report_batch_failures` failed. Nếu có cả batch
thành công và lỗi, dbt vẫn xử lý dữ liệu thành công trước khi task cuối báo lỗi.
Lỗi loader không trả summary hoặc lỗi model/test cũng làm task cuối failed.

Chạy toàn graph trên raw hiện có, không đọc/claim source batch:

```json
{"mode": "dbt_only"}
```

Chạy từ address và toàn bộ downstream:

```json
{"mode": "dbt_only", "model": "int_suumo__address"}
```

`model` chỉ nhận tên model enabled chính xác, chỉ dùng với `dbt_only`; không
nhận selector hay SQL. Graph vẫn hiển thị đầy đủ và giữ task ID ổn định, các
model ngoài lựa chọn skipped. Trước khi chạy, `prepare_transform` kiểm tra
relation upstream tái sử dụng và báo rõ tên relation bị thiếu. Raw và seed
phải được bootstrap; upstream không được build lại trong lần chạy từng phần.
Task chọn dùng `none_failed`, cho phép upstream chủ động skipped nhưng vẫn
chặn lỗi thực sự. Test liên quan đến bất kỳ model được chọn cũng được chạy.

Trong **Grid/Graph**, lỗi SQL thuộc task `run`; lỗi chất lượng dữ liệu thuộc
`test` hoặc `unit_*`. Sau khi sửa lỗi và refresh manifest nếu sửa dbt code,
chọn **Clear** model/test lỗi với **Downstream**, gồm `report_batch_failures`,
để chạy lại phần phụ thuộc trên run cũ. Nếu lỗi data test, có thể Clear riêng
`test` và downstream mà không rebuild model đã đạt. Nếu cần rebuild model,
Clear **run + test + downstream**; unit test failed phải Clear cả unit task.
Nếu sửa SQL của model có unit test, Clear cả unit task hoặc chọn Clear toàn
TaskGroup của model để kiểm chứng lại unit test trước build.
Các task ID tổng hợp `dbt_run`/`dbt_test` chỉ thuộc lịch sử trước thay đổi.

Mỗi task gọi `/opt/airflow/dbt_venv/bin/dbt` với một thread. Cosmos nằm trong
Python Airflow 2.10.5; Core 1.11.15/postgres 1.11.0/Charts 0.8.0 vẫn ở venv
riêng. `SUUMO_DBT_CONCURRENCY` mặc định 4 giới hạn số task đồng thời trong DAG;
`max_active_runs=1`, retries mặc định 0. Không chạy writer dbt thủ công đồng
thời với DAG vì publish warehouse chưa nguyên tử.
LocalExecutor tạo interpreter mới cho mỗi task để không kế thừa connection
metadata PostgreSQL từ process cha; cấu hình này cũng được dùng trong QA song song.

Log task ghi node và command. SQL compile, `run_results.json`, `dbt.log` và
`command.json` được lưu vào volume `pipeline/airflow/logs/dbt_artifacts/`, theo
DAG ID/run ID/task ID/attempt (ID được URL-encode). Artifacts được copy trước
khi Cosmos xóa thư mục tạm, kể cả invocation lỗi; compilation failure có thể
không tạo `run_results.json` nhưng log/command vẫn được giữ. Chúng không ghi
đè artifacts của task khác hoặc manifest Charts/docs.

Kiểm tra graph và logic vận hành bằng:

```bash
make -C pipeline dbt-airflow-manifest
make -C pipeline dbt-airflow-check
```

Khi triển khai local, pause DAG và chờ mọi run hết running/queued trước khi
recreate scheduler/webserver; giữ warehouse/metadata volumes. Không dùng
`clean-volumes` khi cập nhật graph. Production cần refresh manifest qua
`production-up-d` hoặc cùng lệnh module `dbt_airflow.manifest` với production
env. Thay đổi này chưa deploy VPS.

### Nghiệm thu local ngày 2026-10-08

- Import graph không có cycle; đủ 26 task model và 88 data test + 2 unit test,
  mỗi test xuất hiện đúng một lần. Cả 10 unittest graph/loader đạt.
- Full `dbt_only` thực thi đúng 116 node. Address thực thi 18 model,
  76 data test và 2 unit test; tám model upstream skipped, không build lại.
  LocalExecutor đạt tối đa bốn task dbt đồng thời, mỗi invocation một thread.
- Đối chiếu count và hash toàn bộ hàng của 28 relation model/raw/seed trước và
  sau full/address/Clear đều khớp. Raw có 19 record, history 17.946,
  latest 17.395 listing và bridge 53.100 route. Smoke BI năm board đạt.
- Lỗi SQL address và lỗi data test liên model history được gây trong bản sao
  tạm: task tương ứng failed, consumer upstream_failed, task cuối/DAG failed.
  Artifacts lỗi giữ command, log, run results và SQL compile. Clear phần lỗi
  cùng downstream trên chính run cũ hoàn tất; task upstream đã đạt giữ nguyên
  trạng thái và số attempt. Clear riêng test không rebuild model đã đạt.
- Run không có batch mới skipped toàn nhánh dbt và success. Năm trường hợp
  điều phối loader (không batch, thành công, toàn lỗi, hỗn hợp, lỗi không summary)
  dùng summary giả lập để kiểm tra trạng thái DAG; kiểm tra transaction/upsert
  của loader nằm trong unittest riêng. Không claim hay sửa batch source khi QA.
- Webserver/scheduler local đã recreate với image mới, DAG unpaused và health
  healthy. Graph/Grid hiển thị bốn tầng, 26 run operator và test riêng; log UI
  ghi command cùng đường dẫn artifacts. Run scheduler thật `qa_local_cosmos_live`
  chọn `rental_market_price_summary` đạt đúng 19 node model/test, dữ liệu khớp
  baseline; run polling không có batch đạt success với nhánh dbt skipped.

Script QA nằm ở `pipeline/tests/integration_dbt_airflow.py` và
`integration_dbt_airflow_load_cases.py`; dừng scheduler và mọi writer dbt trước
khi dùng script. Kết quả JSON/baseline nằm trong
`analytics/dbt/target/airflow/qa/`, log ở `pipeline/airflow/logs/dbt_airflow_qa/`
(đều Git ignored). Run QA lỗi được giữ trong lịch sử metadata; không xóa lịch sử
để làm sạch Grid.
