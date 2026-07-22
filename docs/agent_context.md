
# Japan Analysis - Agent Context

## Mục tiêu hiện tại

Dự án này là nền tảng local cho Data Engineer phát triển nhiều crawler/pipeline. PostgreSQL và MinIO nằm ở root để dùng chung, còn Python runtime của từng crawler nằm trong folder crawler tương ứng.

## Những gì đã thiết lập

- `docker-compose.yml`: orchestration root cho hạ tầng dùng chung gồm `postgres`, `minio`, và `minio-init`.
- `Makefile`: shortcut root chỉ cho hạ tầng dùng chung. Các lệnh crawler nằm trong `suumo_source_crawler/Makefile`.
- `.env`: file demo root có biến cấu hình chung cho PostgreSQL, MinIO, Docker network và biến runtime crawler. Dùng `CRAWLER_COMPOSE_PROJECT_NAME` cho crawler để không override compose project của hạ tầng root.
- `docker/postgres/init/001_create_crawler_metadata.sql`: init fresh schema metadata crawler gồm `config`, `crawl_sources`, `crawl_runs`, `raw_snapshots`, `crawl_tasks`, `parser_records`, và `load_batches`. Schema hiện gom trực tiếp vào init cho database mới.
- `docs/database-schema.md`: tài liệu schema hiện tại, mô tả từng bảng/cột/type, enum, quy tắc URL hash, data hash, và MinIO storage path.
- `docker/minio/create-buckets.sh`: tạo sẵn bucket MinIO từ biến `MINIO_DEFAULT_BUCKETS`.
- `suumo_source_crawler/docker-compose.yml`: orchestration riêng cho Python service của crawler SUUMO, join vào shared network.
- `suumo_source_crawler/Makefile`: shortcut riêng cho Python service của crawler SUUMO.
- `suumo_source_crawler/Dockerfile`: Python runtime cố định theo image `python:3.12.4-slim-bookworm`, cài dependencies crawler/data cơ bản từ `requirements.txt`, dùng BuildKit cache mount cho `apt` và `pip`.
- `suumo_source_crawler/requirements.txt`: bộ thư viện nền cho crawler gồm Scrapy, parser, HTTP client, dotenv, MinIO client, PostgreSQL client, SQLAlchemy và pandas.
- `suumo_source_crawler/main/main.py`: script khởi tạo MinIO bucket/prefix cho crawler. Mặc định dùng bucket `suumo` và tạo các prefix `data/`, `page_source/`, `image/` nếu chưa tồn tại; không xóa hoặc ghi đè dữ liệu có sẵn.
- `suumo_source_crawler/crawler/crawler/storage.py`: helper chuẩn hóa URL task, tạo SHA-256 hash, build MinIO path theo format `suumo/{prefix}/{datetime}/{run_id}/{id}.{ext}`, gzip payload trước khi upload, và tính `data_hash` từ `image_public_url` cộng các field tiếng Nhật của SUUMO.
- `suumo_source_crawler/crawler/crawler/spiders/suumo_links.py`: Scrapy spider `suumo_links` dùng để crawl toàn bộ page kết quả SUUMO và ghi listing URLs vào `suumo_source_crawler/crawler/tmp/suumo_links.txt`. File output được truncate mỗi lần spider chạy để parser sau đọc link mới.
- `suumo_source_crawler/docker/python/healthcheck.py`: healthcheck Python service bằng cách kiểm tra kết nối PostgreSQL và MinIO.

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
- Khi cần hiểu hoặc chỉnh schema database, đọc `docs/database-schema.md` trước. Schema hiện được gom vào init để bootstrap database mới.
- Khi cần thêm bucket MinIO, cập nhật `MINIO_DEFAULT_BUCKETS` trong `.env`.
- File này là tài liệu context sống. Sau mỗi yêu cầu hoàn tất, cập nhật lại phần liên quan để agent sau nắm trạng thái mới nhất.

## Ghi chú về `.env`

Docker Compose tự động đọc file `.env` nằm cùng thư mục với `docker-compose.yml` để nội suy các biến dạng `${VAR}` trong compose file. Root `Makefile` truyền rõ `--env-file .env`; `suumo_source_crawler/Makefile` truyền `--env-file ../.env` để dùng chung cấu hình hạ tầng.

Nếu cần inject toàn bộ biến `.env` vào runtime container ngoài các biến đã khai báo trong `environment`, có thể thêm `env_file: .env` cho service tương ứng. Hiện tại compose chỉ truyền các biến cần thiết một cách tường minh để tránh đưa thừa cấu hình vào container.
