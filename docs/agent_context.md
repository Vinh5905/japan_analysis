
# Japan Analysis - Agent Context

## Mục tiêu hiện tại

Dự án này là nền tảng local cho Data Engineer phát triển nhiều crawler/pipeline. PostgreSQL và MinIO nằm ở root để dùng chung, còn Python runtime của từng crawler nằm trong folder crawler tương ứng.

## Những gì đã thiết lập

- `docker-compose.yml`: orchestration root cho hạ tầng dùng chung gồm `postgres`, `minio`, và `minio-init`.
- `docker-compose.release.yml`: orchestration release all-in-one cho máy chỉ pull image. File này chạy PostgreSQL, MinIO, `crawler-init`, và các one-shot crawler services từ image `kevinpham9257/suumo-crawler:<tag>`; không bind-mount source code crawler. Release compose có resource limits mặc định cho VPS nhỏ: Postgres `384m/0.30 CPU`, MinIO `512m/0.30 CPU`, crawler `512m/0.50 CPU`, chỉnh được qua `.env`.
- `pipeline/docker-compose.yml`: orchestration local riêng cho Airflow/dbt pipeline, không áp resource limit để thử tính năng. Stack này dùng warehouse Postgres riêng, join vào source Docker network để đọc source DB/MinIO, và không chạy crawler. Airflow chỉ load `load_batches.pending` vào warehouse rồi chạy dbt. `pipeline/docker-compose.production.yml` là override chỉ dùng với `pipeline/.env.production`, áp giới hạn RAM/CPU/PID cho VPS.
- `Makefile`: shortcut root cho hạ tầng dùng chung và release runtime. Các lệnh crawler nằm trong `suumo_source_crawler/Makefile`; các lệnh pipeline nằm trong `pipeline/Makefile`.
- Root `Makefile` cũng có nhóm lệnh release: build/push image Docker Hub, start release runtime, chạy crawler release, preview MinIO, và manual rerun failed HTML.
- `pipeline/Makefile`: shortcut local dùng `pipeline/.env` và Compose cơ sở; các target `production-*` dùng `pipeline/.env.production` cùng Compose override production.
- `pipeline/docker-compose.yml` có service `dbt-docs` theo profile `docs`; `make -C pipeline dbt-docs-up` tạo catalog và phục vụ dbt docs tại `http://localhost:8081`, `dbt-docs-down` để dừng. Airflow UI chạy tại `http://localhost:8080` khi webserver/scheduler được bật.
- `.dockerignore`: root build context cho release image, loại bỏ env/local cache/guides/tmp để không đưa ghi chú hoặc runtime artifact vào image.
- `.env.release.example`: mẫu cấu hình cho người chỉ chạy release compose từ image đã publish.
- `pipeline/.env.example` và `pipeline/.env.production.example`: mẫu cấu hình local và production riêng cho Airflow/dbt pipeline; file `.env.production` thật bị Git ignore. Root `.env.production` không được pipeline đọc tự động.
- `.env`: file demo root có biến cấu hình chung cho PostgreSQL, MinIO, Docker network và biến runtime crawler. Dùng `CRAWLER_COMPOSE_PROJECT_NAME` cho crawler để không override compose project của hạ tầng root.
- `docker/postgres/init/001_create_crawler_metadata.sql`: init fresh schema metadata crawler gồm `config`, `crawl_sources`, `crawl_runs`, `raw_snapshots`, `crawl_tasks`, và `load_batches`. Parser records là JSON object trong batch file, không phải bảng DB. File này là schema mới nhất cho database bootstrap mới.
- `docker/postgres/migrations/`: SQL migrations cho database đã tồn tại. Chạy một file bằng `make db-migrate file=<path>` hoặc chạy toàn bộ bằng `make db-migrate-all`. Hiện có migration seed SUUMO source với `robots_policy = 'allowed'` và `notes = NULL`, migration để `crawl_tasks` quản lý raw snapshot, migration xóa `crawl_runs.status`/`started_at`, migration scope `url_hash` theo run, migration thay `parser_records` table bằng `crawl_tasks.batch_id -> load_batches`, và migration xóa `load_batches.updated_count/skipped_count`.
- `docs/database-schema.md`: tài liệu schema hiện tại, mô tả từng bảng/cột/type, enum, quy tắc URL hash, data hash, và MinIO storage path.
- `docs/pipeline-airflow-dbt.md`: tài liệu vận hành pipeline Airflow/dbt, bao gồm source network, start stack, event notify, polling fallback, dbt command, và kiểm tra kết quả.
- `docs/vps-deployment-openvpn.md`: runbook triển khai VPS từ SSH key, Docker setup, copy release files, chạy release compose, kết nối PostgreSQL/MinIO từ máy local qua SSH tunnel, cấu hình swap/resource limit/monitoring cho VPS nhỏ, cấu hình systemd timer, và cấu hình OpenVPN host theo cách B với route giữ SSH.
- Trạng thái VPS OpenVPN đã cập nhật ngày 2026-09-23: file `vpn_config/vpngate_219.100.37.115_tcp_443.ovpn` đang được dùng tại `/etc/openvpn/client/japan.conf`. Config dùng remote `219.100.37.115:443`, certificate/key nhúng trong file và không có `auth-user-pass`. File trên VPS đã đặt quyền `600`; không ghi hoặc commit nội dung certificate/private key.
- Route giữ SSH hiện tại là `113.161.73.167/32 via 103.249.116.1 dev eth0`, và dòng persistent trong `japan.conf` là `route 113.161.73.167 255.255.255.255 net_gateway`. IP SSH có thể thay đổi; agent phải lấy IP thật từ `$SSH_CLIENT` trước mỗi lần bật VPN, không dùng cứng IP cũ trong ví dụ.
- Ngày 2026-09-23 đã deploy preflight có Telegram lên VPS và chạy thử thành công ở lần tự bật `1/3`: `openvpn-client@japan` active, `tun0` UP, hai route `0.0.0.0/1` và `128.0.0.0/1` đi qua `tun0`, SSH vẫn đi qua `eth0`. Khi test lại vẫn nên dùng rollback `systemd-run --unit=openvpn-ssh-rollback --on-active=2min /bin/systemctl stop openvpn-client@japan` nếu route SSH chưa được xác nhận.
- VPS release cần `docker-compose.release.yml`, `.env`, và `suumo_source_crawler` trong `/opt/suumo-crawler`. Systemd gọi host-side `scripts/run_release_pipeline.py`; runner gửi Telegram, gọi Docker Compose tuần tự và vẫn chạy crawler từ image release, không bind-mount source vào container.
- `docker/minio/create-buckets.sh`: tạo sẵn bucket MinIO từ biến `MINIO_DEFAULT_BUCKETS`.
- Release không dùng service `minio-init`; command `crawler-init` chạy `main.py`, và `main.py` tự tạo bucket/prefix MinIO.
- `suumo_source_crawler/docker-compose.yml`: orchestration riêng cho Python service của crawler SUUMO, join vào shared network.
- `suumo_source_crawler/Makefile`: shortcut riêng cho Python service của crawler SUUMO.
- `suumo_source_crawler/Dockerfile`: Python runtime dev cố định theo image `python:3.12.4-slim-bookworm`, cài dependencies crawler/data cơ bản từ `requirements.txt`, dùng BuildKit cache mount cho `apt` và `pip`, có các wrapper command `crawl-links`, `crawl-html`, `crawl-page`, `crawler-init`, `minio-preview`, `manual-rerun-failed-html`, và `telegram-test`.
- `suumo_source_crawler/Dockerfile.release`: release image build từ root context, copy crawler code, `main.py`, init SQL, migrations, healthcheck và wrapper command vào image để chạy không cần clone source trong container.
- `suumo_source_crawler/requirements.txt`: bộ thư viện nền cho crawler gồm Scrapy, parser, HTTP client, dotenv, MinIO client, PostgreSQL client, SQLAlchemy và pandas.
- `suumo_source_crawler/main/main.py`: script khởi tạo MinIO bucket/prefix cho crawler. Mặc định dùng bucket `suumo` và tạo các prefix `data/`, `page_source/`, `image/` nếu chưa tồn tại; không xóa hoặc ghi đè dữ liệu có sẵn.
- `suumo_source_crawler/crawler/tools/release_bootstrap.py`: command `crawler-init` dùng trong release. Script chờ PostgreSQL, tạo schema từ full init SQL chỉ khi DB chưa có bảng crawler, có option `--force-db-reset` cho reset có chủ đích, và chạy `main.py` để tạo MinIO prefixes.
- `suumo_source_crawler/crawler/crawler/storage.py`: helper chuẩn hóa URL task, tạo SHA-256 hash, build MinIO path page/image theo format `suumo/{prefix}/{date}/{run_id}/{id}.{ext}` và data batch theo `suumo/data/{timestamp}.json.gz`, gzip payload trước khi upload, và tính `data_hash` từ `image_public_url` cộng các field tiếng Nhật của SUUMO.
- `suumo_source_crawler/crawler/crawler/airflow_notify.py`: helper optional để `suumo_page` trigger Airflow REST API sau khi tạo `load_batches.pending`; notify mặc định tắt và là best-effort.
- `suumo_source_crawler/crawler/crawler/telegram_notifier.py` và `telegram_extension.py`: gửi lifecycle Telegram theo kiểu fail-open, chỉ tổng hợp ERROR/CRITICAL khi job kết thúc, đồng thời ghi summary từng spider để host-side pipeline runner tổng hợp.
- `suumo_source_crawler/scripts/run_release_pipeline.py`: runner chạy release theo thứ tự bootstrap → links → html → page, dùng image local với `--pull never`, giữ log ở stdout/journald và gửi Telegram khi pipeline bắt đầu, hoàn thành hoặc lỗi.
- `suumo_source_crawler/scripts/ensure_openvpn.py`: preflight host-side cho systemd pipeline. Script đọc cùng `.env` production, gửi Telegram khi bắt đầu kiểm tra, VPN đã bật/chưa bật, từng lần tự bật và kết quả cuối; xác nhận service OpenVPN active, `tun0` UP và hai route `redirect-gateway def1` đi qua tunnel. Service đang active/activating được chờ tối đa 4 phút để tự reconnect, sau đó reset/restart non-blocking tối đa 3 lần, và phải đạt 3 health check liên tiếp trước khi cho pipeline chạy. Unit `suumo-crawler-pipeline.service` gọi script bằng `ExecStartPre`; `TimeoutStartSec=infinity` để crawl dài không bị systemd cắt sau 20 phút. VPN không khỏe thì crawler không được chạy. Script cố ý không tự hủy SSH rollback vì IP Wi-Fi quản trị là động.
- `suumo_source_crawler/crawler/crawler/spiders/suumo_links.py`: Scrapy spider `suumo_links` dùng để crawl toàn bộ page kết quả SUUMO và ghi listing URLs vào `suumo_source_crawler/crawler/tmp/suumo_links.txt`. File output được truncate mỗi lần spider chạy; trước khi ghi link, spider hash URL rồi bỏ qua URL đã có trong `crawl_tasks.url_hash`.
- `suumo_source_crawler/crawler/crawler/spiders/suumo_html.py`: Scrapy spider `suumo_html` đọc tmp links mới, tạo `crawl_runs` khi mở spider, claim một `crawl_tasks` row qua downloader middleware khi request thật sự bắt đầu, upload HTML gzip lên MinIO, ghi `raw_snapshots`, update task sang `pending` hoặc `failed`, tăng `crawl_runs.total_urls` khi task ra kết quả, finalize task đang dở thành `failed` khi spider đóng, và ghi `finished_at`. Trong một run, cùng `url_hash` chỉ có một task.
- `suumo_source_crawler/crawler/crawler/spiders/suumo_page.py`: Scrapy spider `suumo_page` đọc `crawl_tasks.status = 'pending'` và `batch_id IS NULL`, tải raw HTML từ MinIO, parse thành JSON parser record đủ key/null, buffer mặc định 100 record hoặc 300 giây, upload JSON array gzip lên `suumo/data`, tạo `load_batches`, rồi update các task sang batch đó.
- `pipeline/loaders/suumo_batch_loader.py`: loader Airflow claim `load_batches.pending`, kiểm tra hash gzip/row count/record/task ID, rồi upsert record `is_valid = true` vào `raw.suumo_parser_records` trong một transaction. Record invalid tăng `failed_count`; lỗi file/ghi làm cả batch failed. `pipeline/loaders/recover_batch.py` đưa batch failed hoặc loading quá hạn về pending bằng thao tác thủ công (`make -C pipeline recover-batch batch_id=...`).
- `pipeline/airflow/dags/suumo_load_to_warehouse.py`: DAG Airflow `suumo_load_to_warehouse`; nhận event `conf.batch_id` từ crawler hoặc polling mỗi vài tiếng để load pending batches, rồi dùng Cosmos 1.15.1 LOCAL/subprocess chạy riêng 27 model cùng 95 data test và 3 unit test. Graph nằm trong manifest riêng `analytics/dbt/target/airflow/manifest.json`; refresh qua `make -C pipeline dbt-airflow-manifest` (up-d/recreate/production-up-d tự gọi). `dbt_only` chạy raw hiện có, `model` tên chính xác chọn model + downstream; kiểm tra relation upstream trước khi tái sử dụng. Task ngoài lựa chọn skipped. Seed chỉ test trên relation đã bootstrap, không reload. Clear run/test + downstream để rerun, hoặc chỉ test nếu model đã đúng. Task cuối all_done kiểm tra cả batch và failed/upstream_failed task. Giữ max_active_runs=1, retries=0, concurrency cấu hình `SUUMO_DBT_CONCURRENCY` mặc định 4, mỗi dbt invocation 1 thread. Artifacts riêng theo run/task/attempt ở Airflow logs. Không chạy `dbt deps` trong DAG runtime; bước dependency thuộc build/setup môi trường.
- `pipeline/airflow/Dockerfile`: build image Airflow local cho pipeline. Runtime loader deps được cài theo Airflow constraints; dbt được cài riêng trong `/opt/airflow/dbt_venv` và thêm vào `PATH` để tránh conflict dependency với Airflow.
- `analytics/dbt`: dbt project cho warehouse Postgres. `raw.suumo_parser_records_seed` bootstrap 17.927 notebook records; staging union với raw operational và ưu tiên operational theo `task_id`. `record_origin` đi qua history 112 cột và fact. Bảy view intermediate parse theo chủ đề; station detail giữ mọi route. Mart SCD2 nằm ở models/marts. Tầng analytics có latest detail, market price summary, comparable benchmark và feature-price summary; xem docs/suumo-rental-analytics.md.
- `docs/suumo-rental-price-star.dbml`: thiết kế khớp mart đã triển khai: dim_rental_listing SCD2 rộng, dim_date/geography/observation_quality/station_label, fact một task và bridge mọi route. Exact area chỉ ở fact; area_band ở listing. Hai helper intermediate dựng lại consecutive versions từ parsed_at_utc/task_id, hash key ổn định khi rerun cùng input, hỗ trợ late arrival. Có view observations, latest_known và rejects; không source_updated_date trong mart, không snapshot/backfill notebook. Mart fee sentinel chưa biết được NULL hóa riêng, layout partial không suy diễn false/zero. Xem docs/suumo-rental-price-mart.md về full rebuild, BI refresh sau build và giới hạn publish không nguyên tử.
- Mart/analytics kiểm chứng local ngày 2026-09-25: seed 17.927 + operational 19 tạo 17.946 observations, 17.395 latest listings và 53.100 routes. `make -C pipeline dbt-build` đạt 111/111 nodes (83 data tests, 2 unit tests, 26 models). Analytics có 1.079 market segments, 17.395 comparable rows và 4.768 feature segments. Chưa deploy VPS hoặc kiểm thử tải production.
- `docs/dbt-charts-evaluation.md`: đánh giá dbt Charts beta theo tài liệu chính thức ngày 2026-09-26. Runtime đích là dbt Core 1.11.15 + dbt-postgres 1.11.0 + dbt Charts 0.8.0 trong cùng `/opt/airflow/dbt_venv`; project không chuyển sang dbt v2. Config và năm board BI nằm trong `analytics/dbt/charts/`: market overview, pricing opportunities, feature pricing, station access và data quality. Station dedup listing-ga trước khi aggregate nhưng một listing vẫn có thể thuộc nhiều ga.
- `.agents/skills/`: có 11 dbt Agent Skills và 13 dbt Charts workflow skills ở phạm vi repository để các phiên Codex sau tự tìm thấy. Bộ Charts khớp install surface của `dbt-charts==0.8.0`; xem `docs/dbt-agent-skills.md` và `docs/dbt-charts-agent-skills.md`.
- BI đã kiểm chứng ngày 2026-10-07: runtime Core 1.11.15/postgres 1.11.0/Charts 0.8.0 build thành công; dbt build đạt 111/111. Năm board render PNG/HTML (40 visualization), font Nhật Noto CJK và nhãn dài đã sửa; integration read-only `make -C pipeline dbt-charts-smoke` kiểm tra population, filter, peer shares, empty state, station distinct count và mọi nhóm feature. Cả năm board local port 3000, dbt docs port 8081 và Airflow health port 8080 trả HTTP 200. Airflow scheduler/webserver, dbt docs và Charts đã được tạo lại bằng image mới, Airflow healthy; filter layout `1K` kiểm tra trên trình duyệt trả đúng 7.712 listing. Năm exposures trong `models/exposures.yml` nối lineage BI vào dbt docs. Xem `docs/suumo-rental-bi.md`; render artifacts bị Git ignore. Warehouse validation có warning vì PostgreSQL EXPLAIN không trả schema và static analysis không suy ra filter Jinja; dùng smoke/render để kiểm tra thực tế. Chart cache tối đa 15 phút sau dbt build.
- `notebook`: workflow EDA/clean hiện chạy bằng `.ipynb` self-contained, không còn helper `.py`. `01_pull_and_cache_overview.ipynb` kéo raw parser records từ source PostgreSQL/MinIO về `notebook/data/suumo_parser_records_raw.csv`; `02_column_eda.ipynb` profile từng cột/giá trị, ghi quyết định xử lý, chạy sanity checks inline, rồi xuất `suumo_parser_records_clean.csv`, `suumo_rentals_current.csv`, `suumo_station_access.csv`, `suumo_station_access_current.csv`, và `suumo_clean_report.json`.
- `suumo_source_crawler/crawler/tools/minio_preview.py`: helper tải `storage_path` từ MinIO, tự giải nén `.gz`, pretty print JSON hoặc ghi HTML ra `tmp/minio_preview`. HTML preview tự inject `<base href="https://suumo.jp/">` để CSS/image relative load được khi mở bằng live server; dùng `--raw-html` nếu cần đúng bytes HTML gốc sau giải nén. Có thể sửa hằng `STORAGE_PATH` trong file hoặc truyền path qua CLI.
- `suumo_source_crawler/crawler/tools/manual_rerun_failed_html.py`: helper manual chọn những URL hash có latest `crawl_tasks.status = 'failed'`, ghi URL vào tmp riêng, chạy lại spider `suumo_html` với `created_by = manual`, rồi ghi JSON report và file `.txt` chứa original `task_id` nào vẫn failed sau rerun vào `tmp/manual_rerun_reports`. Nếu URL đã rerun thành `pending` hoặc `success` ở task mới hơn thì failed task cũ sẽ không bị chọn lại.
- `suumo_source_crawler/docker/python/healthcheck.py`: healthcheck Python service bằng cách kiểm tra kết nối PostgreSQL và MinIO.

## Kiểm chứng task graph Airflow ngày 2026-10-08

Full `dbt_only` đạt đúng 26 model + 88 data test + 2 unit test; chọn address đạt
18 model + 76 data test + 2 unit test, tám upstream model skipped. Count/hash của
28 relation không đổi; smoke BI năm board đạt. Lỗi SQL/test chặn consumer và làm
DAG failed; Clear trên run cũ phục hồi, giữ nguyên task upstream đã đạt. Năm
trường hợp loader dùng summary giả lập và 10 unittest graph/loader đều đạt.
Script/kết quả QA được mô tả trong `docs/pipeline-airflow-dbt.md`. Runtime
LocalExecutor dùng interpreter mới cho mỗi task; task dbt đồng thời tối đa bốn.
Webserver/scheduler local đã recreate, health healthy và DAG unpaused; Graph/Grid
và log UI đã kiểm tra. Smoke qua scheduler thật `qa_local_cosmos_live` chọn một
model analytics đạt đúng 19 node model/test, dữ liệu khớp baseline.
Chưa deploy thay đổi này lên VPS.

## Services

| Service        | Image/Build                                  | Port local         | Vai trò                                                        |
| -------------- | -------------------------------------------- | ------------------ | --------------------------------------------------------------- |
| `postgres`   | `postgres:16.3-bookworm`                   | `5432`           | Database cho metadata, structured records, crawler run tracking |
| `minio`      | `minio/minio:RELEASE.2024-07-16T23-46-41Z` | `9000`, `9001` | Object storage và MinIO Console UI                             |
| `minio-init` | `minio/mc:RELEASE.2024-07-15T17-46-06Z`    | none               | One-shot job tạo buckets                                       |
| `python`     | build từ`suumo_source_crawler/Dockerfile` | `8000`           | Runtime cho crawler/ETL SUUMO                                   |

MinIO UI chạy qua MinIO Console tại `http://localhost:9001`.

## Volumes và network

- `postgres_data`: lưu dữ liệu PostgreSQL.
- `minio_data`: lưu object MinIO.
- `python_cache`: cache Python/pip trong container crawler.
- `crawler_shared_net`: bridge network dùng chung để các crawler/pipeline truy cập PostgreSQL và MinIO.

## Health checks

- PostgreSQL: dùng `pg_isready` theo database/user trong `.env`.
- MinIO: dùng `mc ready local` trong container MinIO. Console UI port `9001` vẫn được expose nhưng không dùng làm healthcheck dependency.
- Python: chạy script `python-healthcheck`, kiểm tra dependency PostgreSQL và MinIO đã reachable.
- `minio-init`: phụ thuộc MinIO healthy và kết thúc thành công sau khi tạo bucket.

## Cách chạy local

```bash
make infra-up-d
make -C suumo_source_crawler up-d
```

Hoặc dùng Makefile:

```bash
make help
make infra-ps
make infra-logs service=postgres
make -C suumo_source_crawler ps
make -C suumo_source_crawler logs
```

Các Makefile export `DOCKER_BUILDKIT=1` và `COMPOSE_DOCKER_CLI_BUILD=1`, nên build lại image Python sẽ tái sử dụng cache package của BuildKit thay vì tải lại toàn bộ wheel/source package khi layer `pip install` phải chạy lại.

`make -C suumo_source_crawler up` và `up-d` chỉ start service bằng image đã build sẵn. Khi cần build lại rồi start, dùng `make -C suumo_source_crawler up-build` hoặc `up-build-d`.

Khi đứng trong `suumo_source_crawler`, có thể chạy Python local bằng `make python3 <script>`, ví dụ `make python3 main/main.py`. Nếu muốn chạy bên trong container Python, dùng `make python3-container <script>`. Với argument bắt đầu bằng `-`, dùng biến `args`, ví dụ `make python3-container args="-m scrapy startproject crawler"` vì `make` sẽ tự parse `-m` như option của Makefile nếu viết trực tiếp. Với Scrapy project, chạy trong thư mục có `scrapy.cfg`, ví dụ `make python3-container workdir=/app/crawler args="-m scrapy crawl suumo_links"`.

Preview MinIO object:
`make -C suumo_source_crawler python3-container workdir=/app/crawler args="tools/minio_preview.py suumo/data/20260723T165050155977Z.json.gz"`.
Shortcut tương đương:
`make -C suumo_source_crawler minio-preview path="suumo/data/20260723T165050155977Z.json.gz"`.

Manual rerun failed HTML tasks:
`make -C suumo_source_crawler manual-rerun-failed-html`.
Dry run:
`make -C suumo_source_crawler manual-rerun-failed-html opts="--dry-run --limit 10"`.

## Cách build/chạy release image

Build và push image multi-platform cho VPS:
`make docker-login`, sau đó `make docker-build-push-release tag=latest`. Lệnh này dùng `docker buildx build --platform linux/amd64,linux/arm64 --push` để VPS amd64 và máy Apple Silicon arm64 đều pull được cùng tag.

Chạy từ image đã publish:
`make release-pull`, `make release-up`, rồi chạy lần lượt `make release-crawl-links`, `make release-crawl-html`, `make release-crawl-page`.

`make release-up` start PostgreSQL/MinIO và chạy `crawler-init`. `crawler-init` idempotent: nếu schema đã đủ bảng crawler thì bỏ qua full init SQL; MinIO bucket/prefixes vẫn được kiểm tra/tạo lại bằng `main.py`.

Sau khi chạy:

- PostgreSQL: `localhost:5432`
- MinIO API: `http://localhost:9000`
- MinIO UI: `http://localhost:9001`
- Python service: `http://localhost:8000`

## Lưu ý cho agent sau

- Bắt buộc đọc và tuân theo `docs/git-commit-convention.md` khi viết commit message.
- Bắt buộc đọc và tuân theo `docs/workflow.md` khi tạo branch, pull request description, hoặc hướng dẫn workflow cho contributor.
- Khi viết hoặc sửa Python code, mỗi hàm cần có docstring/comment ngắn nói rõ hàm dùng để làm gì. Những điểm quan trọng, dễ gây hiểu nhầm, hoặc có rủi ro như không xóa/không ghi đè dữ liệu cũng phải có comment tại chỗ.
- Không commit secret thật vào `.env`; file hiện tại chỉ là demo local.
- Khi thêm crawler code SUUMO, ưu tiên đặt source dưới `suumo_source_crawler/src/` và mount sẵn qua volume `.:/app`.
- Khi cần hiểu hoặc chỉnh schema database, đọc `docs/database-schema.md` trước. Cập nhật cả init SQL cho database mới và thêm SQL migration cho database đã tồn tại.
- Khi cần thêm bucket MinIO, cập nhật `MINIO_DEFAULT_BUCKETS` trong `.env`.
- File này là tài liệu context sống. Sau mỗi yêu cầu hoàn tất, cập nhật lại phần liên quan để agent sau nắm trạng thái mới nhất.

## Ghi chú về `.env`

Docker Compose tự động đọc file `.env` nằm cùng thư mục với `docker-compose.yml` để nội suy các biến dạng `${VAR}` trong compose file. Root `Makefile` truyền rõ `--env-file .env`; `suumo_source_crawler/Makefile` truyền `--env-file ../.env` để dùng chung cấu hình hạ tầng.

Nếu cần inject toàn bộ biến `.env` vào runtime container ngoài các biến đã khai báo trong `environment`, có thể thêm `env_file: .env` cho service tương ứng. Hiện tại compose chỉ truyền các biến cần thiết một cách tường minh để tránh đưa thừa cấu hình vào container.


## Geocoding chōme — 2026-10-08

Notebook `03_geocode_addresses.ipynb` self-contained bổ sung điểm GSI theo địa chỉ chōme, cache/output local riêng. Loader `pipeline/loaders/suumo_geocoder.py` quản lý source cache `raw.suumo_address_geocodes`; tạo source bằng `make -C pipeline geocode-init` trước khi chạy DAG trên warehouse đã tồn tại. Cosmos gate `enrich_geographies_cache` chờ mart observations và address-side quality tests, rồi cho source cache/staging/dim geography chạy. Nhánh analytics-only không gọi HTTP. Tọa độ ở dim, fact dùng FK geography_key giữ nguyên; views history/latest có tọa độ. Không sửa charts. Xem `docs/suumo-geocoding.md`. Test graph lấy số node từ manifest thay vì hardcode số cũ.
