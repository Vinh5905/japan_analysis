# Database Schema

Tài liệu này mô tả schema hiện tại của crawler metadata. File init chính là
`docker/postgres/init/001_create_crawler_metadata.sql` và dùng để bootstrap
database mới. Database đã tồn tại dùng các SQL migration trong
`docker/postgres/migrations/`.

## Quy Ước Chung

- Source mặc định hiện tại là SUUMO với `source_id = 1`, `source_key = 'suumo'`,
  `base_url = 'https://suumo.jp'`, `robots_policy = 'allowed'`, và `notes = NULL`.
- URL trong `crawl_tasks.url` lưu dạng đã bỏ base URL khi URL thuộc SUUMO.
  Ví dụ `https://suumo.jp/chintai/...` được lưu thành `/chintai/...`.
- `url_hash` là SHA-256 dạng hex lowercase của URL sau khi normalize.
  `crawl_tasks` unique theo cặp `(run_id, url_hash)`.
- `content_hash`, `data_hash`, và `file_hash` đều là SHA-256 dạng hex lowercase.
- Raw payload được hash trên bytes gốc trước khi nén.
- Object đưa lên MinIO phải được nén trước khi upload nếu `compression = 'gzip'`.
- MinIO bucket mặc định là `suumo`, với các prefix chính:
  `page_source/`, `image/`, và `data/`.
- `storage_path`, `image_storage_path`, và `file_path` lưu logical path gồm bucket
  và object key, ví dụ `suumo/page_source/20260713/12/99.html.gz`.

## Enum

### `robots_policy_enum`

| Giá trị | Khi sử dụng |
| --- | --- |
| `allowed` | Source được crawl bình thường. SUUMO hiện dùng giá trị này. |
| `disallowed` | Source không được crawl. |
| `limited` | Source được crawl nhưng phải có giới hạn như delay, concurrency thấp, hoặc scope cố định. |
| `not_applicable` | Không áp dụng robots policy, ví dụ API, private source, hoặc nguồn không phải website public. |

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
| `robots_policy` | `robots_policy_enum` | Chính sách crawl của source. Mặc định `allowed`. |
| `notes` | `TEXT` | Ghi chú vận hành, có thể `NULL`. SUUMO mặc định để `NULL`. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm tạo source. |
| `updated_at` | `TIMESTAMPTZ` | Thời điểm cập nhật source gần nhất. |

## Bảng `crawl_runs`

Mỗi lần chạy spider `suumo_html` tạo một row trong bảng này ngay khi spider mở.
Run không lưu status riêng; trạng thái từng URL nằm trong `crawl_tasks.status`.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `run_id` | `BIGSERIAL` | Primary key của run. |
| `source_id` | `BIGINT` | FK tới `crawl_sources.source_id`. Mặc định `1` cho SUUMO. |
| `finished_at` | `TIMESTAMPTZ` | Lưu khi run kết thúc, dù thành công, lỗi, bị dừng, hoặc hết URL. |
| `total_urls` | `INTEGER` | Mặc định `0`; tăng thêm `1` khi một task đã bắt đầu xử lý và được update ra kết quả `pending` hoặc `failed`. |
| `created_by` | `run_created_by_enum` | Nguồn tạo run: `schedule` hoặc `manual`. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm tạo row run, dùng như thời điểm bắt đầu run. |

Số task thành công/lỗi được tính từ `crawl_tasks` theo `run_id` khi cần báo cáo,
không lưu trực tiếp trong `crawl_runs`.

## Bảng `raw_snapshots`

Lưu metadata của raw HTML/JSON đã được fetch và upload lên MinIO.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `raw_snapshot_id` | `BIGSERIAL` | Primary key của raw snapshot. |
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

`raw_snapshots` không lưu trực tiếp `source_id` hoặc `run_id`. Khi cần truy vết
source/run của raw payload, join qua `crawl_tasks.raw_snapshot_id`, rồi tới
`crawl_tasks.run_id` và `crawl_runs.source_id`.

Raw page source lưu theo format:

```text
suumo/page_source/{date}/{run_id}/{raw_snapshot_id}.html.gz
suumo/page_source/{date}/{run_id}/{raw_snapshot_id}.json.gz
```

`date` dùng ngày UTC từ `crawl_runs.created_at`, format `YYYYMMDD`, ví dụ
`20260713`.

## Bảng `crawl_tasks`

Lưu từng URL detail cần fetch và trạng thái xử lý của URL đó.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `task_id` | `BIGSERIAL` | Primary key của task. |
| `run_id` | `BIGINT` | FK tới run tạo task. |
| `url` | `TEXT` | URL đã bỏ base URL nếu thuộc source hiện tại. |
| `url_hash` | `TEXT` | SHA-256 của URL đã normalize. Unique trong phạm vi cùng `run_id`. |
| `method` | `http_method_enum` | HTTP method thực tế của request. |
| `status` | `crawl_task_status_enum` | Trạng thái task. |
| `error_type` | `TEXT` | Nhóm lỗi khi task lỗi. |
| `error_message` | `TEXT` | Nội dung lỗi khi task lỗi. |
| `scheduled_at` | `TIMESTAMPTZ` | Thời điểm bắt đầu crawl task. |
| `fetched_at` | `TIMESTAMPTZ` | Thời điểm raw payload đã lưu MinIO thành công. Null nếu fetch/lưu thất bại. |
| `raw_snapshot_id` | `BIGINT` | FK tới raw snapshot được tạo sau khi lưu MinIO thành công. |
| `batch_id` | `BIGINT` | FK tới `load_batches.batch_id` chứa parser record JSON của task này. Null nếu chưa parse/batch. |

`suumo_links` truncate file tmp ở đầu mỗi lần chạy, hash URL tìm được, so với
toàn bộ `crawl_tasks.url_hash`, và chỉ ghi URL chưa từng tồn tại trong
`crawl_tasks` vào tmp. Các case chạy lại URL cũ bị failed sẽ xử lý bằng flow
manual riêng sau này.

`suumo_html` đọc tmp đó và chỉ tạo một row `crawl_tasks` khi request thật sự bắt
đầu đi qua downloader. Row task đó được giữ nguyên cho toàn bộ retry trong cùng
run. Nếu retry sau đó fetch và upload MinIO thành công thì tạo `raw_snapshots` và
update task sang
`crawl_tasks.status = 'pending'`. Nếu retry hết vẫn lỗi thì update task sang
`crawl_tasks.status = 'failed'` với `raw_snapshot_id = NULL` và
`fetched_at = NULL`. Nếu spider bị đóng khi request đã bắt đầu nhưng chưa hoàn
tất, task đã claim được finalize thành `failed` khi spider đóng. Một `run_id` chỉ
có tối đa một task row cho cùng `url_hash`.

Parser spider chỉ đọc các task có `status = 'pending'` và `batch_id IS NULL`.

## JSON `parser_records`

`parser_records` không phải bảng PostgreSQL. Đây là schema của từng object JSON
nằm trong file batch `load_batches.file_path`. Spider `suumo_page` đọc
`crawl_tasks` đang `pending`, lấy raw snapshot từ MinIO, parse dữ liệu, validate,
giữ record trong bộ nhớ đệm, rồi flush thành một JSON array đã gzip lên
`suumo/data`. Điều kiện flush mặc định là đủ `100` record hoặc batch đã chạy quá
`5` phút; khi spider kết thúc thì flush phần còn lại nếu buffer còn dữ liệu.

Mỗi object JSON phải luôn có đủ các key trong schema. Field nào không có dữ liệu
thì để `null`, không được ẩn key.

| Key | Type | Mô tả |
| --- | --- | --- |
| `task_id` | `INTEGER` | ID của `crawl_tasks` được parse. |
| `image_public_url` | `TEXT` | URL public của ảnh nếu source cung cấp và ảnh public. Có thể null. |
| `image_storage_path` | `TEXT` | MinIO path ảnh đã lưu trong `suumo/image`. Có thể null. |
| Các key tiếng Nhật | `TEXT` | Dữ liệu raw đã parse từ SUUMO. Key không có dữ liệu phải là null. |
| `data_hash` | `TEXT` | SHA-256 của dữ liệu source đã parse. |
| `parsed_at` | `TEXT` | Timestamp ISO-8601 lúc parse record. |
| `is_valid` | `BOOLEAN` | True nếu record vượt qua validation đầu vào. |
| `error_type` | `TEXT` | Nhóm lỗi validation/parse nếu `is_valid = false`. |
| `error_message` | `TEXT` | Nội dung lỗi validation/parse nếu `is_valid = false`. |

Các cột dữ liệu tiếng Nhật hiện gồm:

```text
家賃
敷金
管理費_共益費
礼金
保証金
敷引_償却
電話番号
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
`task_id`, `image_storage_path`, `parsed_at`, `is_valid`, `error_type`, và
`error_message`.

Khi một file batch được upload thành công và row `load_batches` đã được tạo,
mọi `task_id` xuất hiện trong JSON array đó phải được cập nhật
`crawl_tasks.batch_id = load_batches.batch_id`. Hiện tại task được chuyển từ
`pending` sang `success` khi parser record đã nằm trong batch; kết quả validation
chi tiết nằm trong `is_valid`, `error_type`, và `error_message` của JSON record.

Ảnh lưu theo format:

```text
suumo/image/{date}/{run_id}/{task_id}.{extension}
```

`run_id` và `task_id` trong path ảnh lấy từ `crawl_tasks`.

## Bảng `load_batches`

Lưu metadata của file batch được tạo từ nhiều JSON `parser_records` trước khi
loader ghi dữ liệu vào bảng đích.

| Cột | Type | Mô tả |
| --- | --- | --- |
| `batch_id` | `BIGSERIAL` | Primary key của batch. |
| `source_id` | `BIGINT` | FK tới source. |
| `file_path` | `TEXT` | MinIO path file batch trong `suumo/data`. Unique. |
| `file_format` | `TEXT` | Format file, hiện parser ghi `json` dạng JSON array. |
| `compression` | `TEXT` | Thuật toán nén file batch, ví dụ `gzip`. |
| `row_count` | `INTEGER` | Số row parser record trong batch file. |
| `file_hash` | `TEXT` | SHA-256 của bytes file cuối cùng được upload lên MinIO, sau nén nếu có `compression`. |
| `status` | `load_batch_status_enum` | Trạng thái load batch. |
| `inserted_count` | `INTEGER` | Số row được insert mới. |
| `updated_count` | `INTEGER` | Số row update khi loader gặp record đích đã tồn tại nhưng dữ liệu thay đổi. |
| `skipped_count` | `INTEGER` | Số row bỏ qua vì `data_hash` giống hệt dữ liệu đã có. |
| `failed_count` | `INTEGER` | Số row lỗi không load được. |
| `error_message` | `TEXT` | Nội dung lỗi batch nếu load thất bại. |
| `created_at` | `TIMESTAMPTZ` | Thời điểm file batch đã được tạo, nén, upload lên MinIO, và metadata được ghi DB. |
| `started_loading_at` | `TIMESTAMPTZ` | Thời điểm loader bắt đầu load batch. |
| `finished_loading_at` | `TIMESTAMPTZ` | Thời điểm loader kết thúc, kể cả khi failed. |
| `loaded_at` | `TIMESTAMPTZ` | Thời điểm load thành công. Null nếu failed. |

Batch file lưu theo format:

```text
suumo/data/{timestamp}.json.gz
```

`timestamp` dùng UTC chi tiết tới microsecond, format
`YYYYMMDDTHHMMSSffffffZ`, để các batch tạo rất sát nhau vẫn không đè path.
