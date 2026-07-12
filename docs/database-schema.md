# Database Schema

Tài liệu này mô tả schema hiện tại của crawler metadata. File init chính là
`docker/postgres/init/001_create_crawler_metadata.sql` và được dùng để bootstrap
database mới.

## Quy ước chung

- Source mặc định hiện tại là SUUMO với `source_id = 1`, `source_key = 'suumo'`,
  `base_url = 'https://suumo.jp'`, và `robots_policy = 'limited'`.
- URL trong `crawl_tasks.url` lưu dạng đã bỏ base URL khi URL thuộc SUUMO.
  Ví dụ `https://suumo.jp/chintai/...` được lưu thành `/chintai/...`.
- `url_hash` là SHA-256 dạng hex lowercase của URL sau khi normalize.
- `content_hash`, `data_hash`, và `file_hash` đều là SHA-256 dạng hex lowercase.
- Raw payload được hash trên bytes gốc trước khi nén.
- Object đưa lên MinIO phải được nén trước khi upload nếu `compression = 'gzip'`.
- MinIO bucket mặc định là `suumo`, với các prefix chính:
  `page_source/`, `image/`, và `data/`.
- `storage_path`, `image_storage_path`, và `file_path` lưu logical path gồm bucket
  và object key, ví dụ `suumo/page_source/20260713T010203Z/12/99.html.gz`.

## Enum

### `robots_policy_enum`

| Giá trị | Khi sử dụng |
| --- | --- |
| `allowed` | Source được crawl bình thường. |
| `disallowed` | Source không được crawl. |
| `limited` | Source được crawl nhưng phải có giới hạn như delay, concurrency thấp, hoặc scope cố định. SUUMO hiện dùng giá trị này. |
| `not_applicable` | Không áp dụng robots policy, ví dụ API, private source, hoặc nguồn không phải website public. |

### `crawl_run_status_enum`

| Giá trị | Khi sử dụng |
| --- | --- |
| `running` | Run đã bắt đầu và chưa có `finished_at`. |
| `success` | Run kết thúc đầy đủ, các URL mới đã được tính và metadata liên quan đã được lưu. |
| `failed` | Run dừng vì lỗi không xử lý tiếp được. Vẫn phải ghi `finished_at`. |
| `cancelled` | Run bị dừng chủ động, ví dụ keyboard interrupt hoặc thao tác manual. Vẫn phải ghi `finished_at`. |

### `run_created_by_enum`

| Giá trị | Khi sử dụng |
| --- | --- |
| `schedule` | Run tạo bởi lịch chạy tự động. Đây là mặc định hiện tại. |
| `manual` | Run tạo thủ công bởi người vận hành. |

### `http_method_enum`

Các method hiện hỗ trợ: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`,
`OPTIONS`. Giá trị này lấy theo request thực tế trong code crawler.

### `crawl_task_status_enum`

| Giá trị | Khi sử dụng |
| --- | --- |
| `failed` | Task đang retry hoặc đã retry hết nhưng vẫn không fetch/lưu raw được. `fetched_at` để null khi chưa lưu MinIO thành công. |
| `cancelled` | Task đã được kiểm tra manual và xác định không thể hoặc không nên xử lý tiếp. |
| `pending` | HTML/JSON đã fetch xong và raw payload đã lưu MinIO thành công. Task đang chờ parser spider xử lý. |
| `success` | Parser đã tạo record hợp lệ và task đã hoàn tất. |

### `raw_content_type_enum`

| Giá trị | Khi sử dụng |
| --- | --- |
| `text/html` | Raw payload là HTML. |
| `application/json` | Raw payload là JSON. |

Nếu response header có charset, code chỉ lưu media type vào `content_type`; charset
được lưu ở `encoding`.

### `load_batch_status_enum`

| Giá trị | Khi sử dụng |
| --- | --- |
| `pending` | File batch đã được tạo, nén, upload lên `suumo/data`, và metadata file đã được ghi vào DB. |
| `loading` | Loader đang đọc batch file để ghi vào bảng đích. |
| `success` | Load hoàn tất thành công. `loaded_at` phải có giá trị. |
| `failed` | Load bị lỗi. `finished_loading_at` phải có giá trị, `loaded_at` để null. |

## Bảng `config`

Bảng singleton lưu cấu hình runtime chung.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `config_id` | `SMALLINT` | Primary key, luôn là `1`. |
| `max_retries` | `INTEGER` | Số lần retry tối đa cho crawl/fetch task. Mặc định `10`. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm tạo config. |
| `updated_at` | `TIMESTAMPTZ` | Thời điểm cập nhật config gần nhất. |

## Bảng `crawl_sources`

Lưu danh sách source crawler.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `source_id` | `BIGSERIAL` | Primary key của source. |
| `source_key` | `TEXT` | Key ổn định cho code, ví dụ `suumo`. Unique. |
| `source_name` | `TEXT` | Tên hiển thị của source. |
| `base_url` | `TEXT` | Base URL dùng để normalize URL task. |
| `crawl_frequency` | `TEXT` | Mô tả nhịp crawl hiện tại, ví dụ `schedule`. |
| `is_active` | `BOOLEAN` | Source còn được phép chạy hay không. |
| `robots_policy` | `robots_policy_enum` | Chính sách crawl của source. |
| `notes` | `TEXT` | Ghi chú vận hành. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm tạo source. |
| `updated_at` | `TIMESTAMPTZ` | Thời điểm cập nhật source gần nhất. |

## Bảng `crawl_runs`

Mỗi lần bấm chạy hoặc schedule chạy crawler tạo một row trong bảng này ngay lúc
bắt đầu.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `run_id` | `BIGSERIAL` | Primary key của run. |
| `source_id` | `BIGINT` | FK tới `crawl_sources.source_id`. Mặc định `1` cho SUUMO. |
| `started_at` | `TIMESTAMPTZ` | Lưu ngay khi bắt đầu run. |
| `finished_at` | `TIMESTAMPTZ` | Lưu khi run kết thúc, dù thành công, lỗi, bị dừng, hoặc hết URL. |
| `status` | `crawl_run_status_enum` | Trạng thái tổng của run. |
| `total_urls` | `INTEGER` | Số URL mới sau khi crawl hết page list, lấy link, hash URL, rồi so với `crawl_tasks.url_hash`. |
| `success_count` | `INTEGER` | Số task của run đã fetch raw và lưu MinIO thành công. |
| `failed_count` | `INTEGER` | Số task của run bị lỗi fetch/lưu raw. |
| `created_by` | `run_created_by_enum` | Nguồn tạo run: `schedule` hoặc `manual`. |
| `new_urls_file_path` | `TEXT` | Path file chứa các URL mới để bước xử lý sau đọc lại khi cần. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm tạo row run. |

## Bảng `raw_snapshots`

Lưu metadata của raw HTML/JSON đã được fetch và upload lên MinIO.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `raw_snapshot_id` | `BIGSERIAL` | Primary key của raw snapshot. |
| `source_id` | `BIGINT` | FK tới source. |
| `run_id` | `BIGINT` | FK tới crawl run tạo snapshot. |
| `url` | `TEXT` | URL request ban đầu, cùng chuẩn normalize với `crawl_tasks.url`. |
| `final_url` | `TEXT` | URL cuối sau redirect. Nếu giống URL ban đầu thì để null. |
| `http_status` | `INTEGER` | HTTP status của response, từ `100` đến `599`. |
| `content_type` | `raw_content_type_enum` | Media type của raw payload. |
| `content_length` | `BIGINT` | Độ dài bytes gốc trước khi nén. |
| `content_hash` | `TEXT` | SHA-256 của bytes gốc trước khi nén. |
| `storage_path` | `TEXT` | MinIO path của raw payload đã nén. |
| `compression` | `TEXT` | Thuật toán nén, hiện dùng `gzip`. |
| `encoding` | `TEXT` | Encoding/charset lấy từ response nếu có. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm ghi metadata snapshot. |

Raw page source lưu theo format:

```text
suumo/page_source/{datetime}/{run_id}/{raw_snapshot_id}.html.gz
suumo/page_source/{datetime}/{run_id}/{raw_snapshot_id}.json.gz
```

`datetime` dùng UTC compact format, ví dụ `20260713T010203Z`.

## Bảng `crawl_tasks`

Lưu từng URL detail cần fetch và trạng thái xử lý của URL đó.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `task_id` | `BIGSERIAL` | Primary key của task. |
| `run_id` | `BIGINT` | FK tới run tạo task. |
| `source_id` | `BIGINT` | FK tới source. |
| `url` | `TEXT` | URL đã bỏ base URL nếu thuộc source hiện tại. |
| `url_hash` | `TEXT` | SHA-256 của URL đã normalize. Unique để nhận diện URL mới/cũ. |
| `method` | `http_method_enum` | HTTP method thực tế của request. |
| `status` | `crawl_task_status_enum` | Trạng thái task. |
| `error_type` | `TEXT` | Nhóm lỗi khi task lỗi. |
| `error_message` | `TEXT` | Nội dung lỗi khi task lỗi. |
| `scheduled_at` | `TIMESTAMPTZ` | Thời điểm bắt đầu crawl task. |
| `fetched_at` | `TIMESTAMPTZ` | Thời điểm raw payload đã lưu MinIO thành công. Null nếu fetch/lưu thất bại. |
| `raw_snapshot_id` | `BIGINT` | FK tới raw snapshot được tạo sau khi lưu MinIO thành công. |

Parser spider chỉ đọc các task có `status = 'pending'`.

## Bảng `parser_records`

Parser spider đọc các `crawl_tasks` đang `pending`, lấy raw snapshot từ MinIO,
parse dữ liệu, validate, rồi ghi kết quả vào bảng này.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `record_id` | `BIGSERIAL` | Primary key của parser record. |
| `source_id` | `BIGINT` | FK tới source. |
| `task_id` | `BIGINT` | FK tới crawl task được parse. |
| `raw_snapshot_id` | `BIGINT` | FK tới raw snapshot đầu vào. |
| `source_record_id` | `TEXT` | ID record từ source nếu parse được. |
| `image_public_url` | `TEXT` | URL public của ảnh nếu source cung cấp và ảnh public. Có thể null. |
| `image_storage_path` | `TEXT` | MinIO path ảnh đã lưu trong `suumo/image`. Có thể null. |
| Các cột tiếng Nhật | `TEXT` | Dữ liệu raw đã parse từ SUUMO. |
| `data_hash` | `TEXT` | SHA-256 của dữ liệu source đã parse. |
| `parsed_at` | `TIMESTAMPTZ` | Thời điểm parse. |
| `is_valid` | `BOOLEAN` | True nếu record vượt qua validation đầu vào. |
| `error_type` | `TEXT` | Nhóm lỗi validation/parse nếu `is_valid = false`. |
| `error_message` | `TEXT` | Nội dung lỗi validation/parse nếu `is_valid = false`. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm tạo row. |

Các cột dữ liệu tiếng Nhật hiện gồm:

```text
敷金
管理費・共益費
礼金
保証金
敷引・償却
所在地
駅徒歩
間取り
専有面積
築年数
階
向き
建物種別
間取り詳細
構造
階建
築年月
エネルギー消費性能
目安光熱費
損保
駐車場
入居
条件
SUUMO物件コード
情報更新日
契約期間
仲介手数料
保証会社
ほか初期費用
ほか諸費用
取引態様
取り扱い店舗物件コード
総戸数
次回更新予定日
```

`data_hash` chỉ được tính từ `image_public_url` và các cột tiếng Nhật ở trên.
Không đưa các giá trị sinh bởi code hoặc trạng thái xử lý vào hash, ví dụ
`record_id`, `source_id`, `task_id`, `raw_snapshot_id`, `image_storage_path`,
`parsed_at`, `is_valid`, `error_type`, và `error_message`.

Nếu `is_valid = true`, parser phải cập nhật `crawl_tasks.status` từ `pending`
sang `success`. Nếu validation không đạt, ghi `error_type` và `error_message`
vào `parser_records`.

Ảnh lưu theo format:

```text
suumo/image/{datetime}/{run_id}/{record_id}.{extension}
```

## Bảng `load_batches`

Lưu metadata của file batch được tạo từ nhiều `parser_records` trước khi loader
ghi dữ liệu vào bảng đích.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `batch_id` | `BIGSERIAL` | Primary key của batch. |
| `source_id` | `BIGINT` | FK tới source. |
| `file_path` | `TEXT` | MinIO path file batch trong `suumo/data`. Unique. |
| `file_format` | `TEXT` | Format file, ví dụ `jsonl`, `csv`, hoặc `parquet`. |
| `compression` | `TEXT` | Thuật toán nén file batch, ví dụ `gzip`. |
| `row_count` | `INTEGER` | Số row parser record trong batch file. |
| `file_hash` | `TEXT` | SHA-256 của bytes file cuối cùng được upload lên MinIO, sau nén nếu có `compression`. |
| `status` | `load_batch_status_enum` | Trạng thái load batch. |
| `inserted_count` | `INTEGER` | Số row được insert mới. |
| `updated_count` | `INTEGER` | Số row update khi trùng `record_id` nhưng dữ liệu thay đổi. |
| `skipped_count` | `INTEGER` | Số row bỏ qua vì `data_hash` giống hệt dữ liệu đã có. |
| `failed_count` | `INTEGER` | Số row lỗi không load được. |
| `error_message` | `TEXT` | Nội dung lỗi batch nếu load thất bại. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm file batch đã được tạo, nén, upload lên MinIO, và metadata được ghi DB. |
| `started_loading_at` | `TIMESTAMPTZ` | Thời điểm loader bắt đầu load batch. |
| `finished_loading_at` | `TIMESTAMPTZ` | Thời điểm loader kết thúc, kể cả khi failed. |
| `loaded_at` | `TIMESTAMPTZ` | Thời điểm load thành công. Null nếu failed. |

Batch file lưu theo format:

```text
suumo/data/{datetime}/{batch_id}.{extension}.gz
```
