# Docker Release

Tài liệu này mô tả cách đóng gói `suumo_source_crawler` thành Docker image để người khác chỉ cần pull image, chạy compose release, rồi gọi các lệnh crawler.

## Hai kiểu compose

`docker-compose.yml` ở root là môi trường dev/local. Nó bind-mount init SQL và dùng chung hạ tầng cho repo đang clone.

`docker-compose.release.yml` là môi trường release. Nó pull image `kevinpham9257/suumo-crawler:<tag>` và không mount source code vào container crawler. Code Python, command wrapper, `main.py`, init SQL và migrations đã được copy vào image lúc build.

## Publish multi-platform lên Docker Hub

Đăng nhập Docker Hub:

```bash
make docker-login
```

Build và push image cho cả VPS `linux/amd64` và máy Apple Silicon `linux/arm64`:

```bash
make docker-build-push-release tag=latest
```

Image được build từ root context bằng `suumo_source_crawler/Dockerfile.release` để Docker có thể copy cả crawler code lẫn `docker/postgres/init`.

Kiểm tra remote manifest sau khi push:

```bash
make docker-inspect-release tag=latest
```

Nếu muốn version rõ ràng:

```bash
make docker-build-push-release tag=2026.07.31
```

## Chạy từ image đã publish

Trên máy nhận image, tạo `.env` từ `.env.release.example`, rồi chạy:

```bash
make release-pull
make release-up
```

`release-up` sẽ start PostgreSQL và MinIO, sau đó chạy `crawler-init`. `crawler-init` làm hai việc:

- Tạo schema PostgreSQL từ `docker/postgres/init/001_create_crawler_metadata.sql` nếu DB chưa có bảng crawler.
- Chạy `main/main.py` để tạo bucket/prefix MinIO như `suumo/data/`, `suumo/page_source/`, `suumo/image/`.

`MINIO_DEFAULT_BUCKETS` là danh sách bucket ngăn cách bằng dấu phẩy, ví dụ `suumo,another_bucket`.

`crawler-init` không reset DB nếu schema đã tồn tại. Nếu thật sự muốn xóa và tạo lại metadata DB, chạy trực tiếp command có `--force-db-reset`.

## CLI crawler

Các command này chạy bằng one-shot container từ image release:

```bash
make release-crawl-links
make release-crawl-html
make release-crawl-page
```

Tool kiểm tra MinIO object:

```bash
make release-minio-preview path="suumo/page_source/20260729/1/1.html.gz"
make release-minio-preview path="suumo/data/20260729T120000000000Z.json.gz"
```

Manual rerun các task HTML failed:

```bash
make release-manual-rerun-failed-html
make release-manual-rerun-failed-html opts="--dry-run --limit 10"
```

Mở shell trong image:

```bash
make release-shell
```

## Dọn môi trường release local

Stop container nhưng giữ volume:

```bash
make release-down
```

Xóa cả volume PostgreSQL và MinIO:

```bash
make release-clean-volumes
```
