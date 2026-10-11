# Tên tòa từ HTML và building SCD2 — local 2026-10-10

Địa chỉ chi tiết và tọa độ được bổ sung trực tiếp vào dim_building; không thuộc SCD2 hash. Xem [building locations](suumo-building-locations.md).

Parser mới trích tên tòa/số phòng; warehouse tách `dim_building` khỏi
`dim_rental_listing`. Fact giữ một dòng/task và liên kết cả hai phiên bản.
Thay đổi này chỉ áp dụng tại local, chưa triển khai VPS.

## HTML → parser → warehouse

Helper chung `crawler/building_identity.py` đọc H1
`h1.section_h1-header-title`, fallback `<title>` đúng mẫu `【SUUMO】...／...`.
Tên chung, tiêu đề tuyến tàu và trang lỗi trả NULL. Chỉ tách hậu tố phòng rõ ràng
như `203号室`; giữ `弐番館`, `1号棟`, `II`. Record JSON mới có:

- `listing_headline_raw`, `building_name_raw`, `room_number_raw`;
- `building_name_source`: `h1` hoặc `title`;
- `building_name_parse_status`: `parsed`, `generic_headline`, `missing_headline`;
- `data_hash_version=2`, hash gồm tên tòa/số phòng ngoài các trường v1.

Record cũ mặc định hash v1; không hash lại hoặc viết lại batch lịch sử.
Metadata trích tên không tự làm một trang thiếu detail trở thành record hợp lệ.
Loader giữ nguyên payload JSONB, nên các trường mới đi theo đường load hiện có.

Ví dụ snapshot **8**, listing **100500165888**, object
`suumo/page_source/20260727/1/8.html.gz`:

```text
H1: プレリスNEO大阪十三エルヴィオン 203号室
Tên: プレリスNEO大阪十三エルヴィオン
Phòng: 203
Địa chỉ nguồn: 大阪府大阪市淀川区十三本町２
```

Snapshot **16**, listing **100518469998**, object
`suumo/page_source/20260727/1/16.html.gz` có cùng tên trong H1, không có số phòng.
Preview có sẵn tại `suumo_source_crawler/crawler/tmp/minio_preview/page_source__20260727__1__16.html`,
H1 ở dòng 1260. Parser không tìm tên/địa chỉ bằng Google Maps trong bước này.

## Backfill local có audit

```bash
make -C pipeline building-init
make -C pipeline building-backfill opts='--dry-run --limit 5'
make -C pipeline building-backfill opts='--report /opt/airflow/pipeline/tmp/building_qa/html_backfill.csv'
make -C pipeline building-backfill
```

Lệnh đọc metadata source và HTML MinIO đã tồn tại. Bảng
`raw.suumo_building_name_backfill` khóa `(source_id, task_id)` giữ snapshot/path,
content hash, phiên bản parser, listing code, kết quả và thời điểm backfill.
Kiểm tra hash bytes HTML sau giải nén trước khi parse.

Chạy lại cùng content hash/parser version bỏ qua HTML đã xử lý. `--force` thử
lại, `--limit` giới hạn số task cần xử lý; `--dry-run` không DDL/ghi warehouse,
nhưng có thể xuất báo cáo local. Snapshot lỗi có trạng thái `snapshot_error` và
lý do; dùng `--force` để thử lại. Refresh lỗi không xóa tên đã thành công.
Lỗi code/warehouse khiến lệnh thất bại.

Staging ưu tiên metadata parser mới; parser cũ nhận backfill khi khớp source,
task và SUUMO code. Các cột raw giữ provenance ban đầu, còn `building_name`,
`room_number`, `name_source`, `name_parse_status`, `headline` là kết quả sau ghép.
Seed chưa có HTML tương ứng giữ NULL. Không sửa crawl status, parser timestamp,
raw record/hash, batch hoặc object MinIO gốc.

## Grain, identity và lịch sử

| Nơi lưu                        | Nội dung                                                                                                                          |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `dim_building`                 | Loại tòa, kết cấu, tổng tầng/căn, ngày xây dựng và precision, tên, geography, SCD2; địa chỉ chi tiết/điểm POI là enrichment riêng |
| `dim_rental_listing`           | Số phòng, tầng căn, hướng, layout và điều kiện thuê; identity vẫn source + listing code                                           |
| `fct_rental_price_observation` | Giá/diện tích, tuổi tòa được tin báo và cờ lower-bound, hai version FK, cờ xung đột tòa                                           |
| `dim_geography`                | Địa chỉ chōme, tọa độ GSI legacy; geography key không đổi, views dùng điểm building                                               |

Tên dùng NFKC, bỏ khoảng trắng và lowercase Latin. Tên chuẩn hóa + geography
đủ đến chōme + source tạo `named_candidate`. Không khẳng định đây là physical
building ID. Thiếu tên/địa chỉ dùng `unresolved_listing` riêng theo source/code;
không gom cả chōme vào một tòa. Không suy diễn số phòng thành physical room ID,
không gán ngược tên xuất hiện sau cho observation cũ thiếu bằng chứng. Tên đổi
có thể tạo candidate khác; chưa tự liên kết alias/đổi tên tòa.

Lịch sử building xếp theo `information_updated_at` tại nửa đêm Nhật; thiếu ngày
thì dùng `parsed_at_utc`. Tie-break bằng thời điểm quan sát rồi task. Khoảng
hiệu lực là `[from,to)` trên bộ ba **business time, observation time, task**;
không join chỉ bằng ngày. Fact nhận version qua mapping task → version.

NULL là chưa biết: giữ giá trị đã biết từ trước trong cùng candidate, không
lấy tương lai điền quá khứ. Thay đổi descriptor tạo version mới; A → B → A tạo
ba version. Surrogate là MD5 JSON array `[building_key, first_event_task_id]`.
Cùng ngày có giá trị đã biết khác nhau sẽ bật `building_attributes_conflict`
trên observation; không loại dữ liệu. Một identity có một current version;
“current” ở nhóm unresolved không chứng minh listing vẫn active.

Tuổi tòa là thông tin từng observation, không nằm trong building/listing SCD.
View lịch sử/latest giữ các cột nghiệp vụ cũ và xuất thêm tên, số phòng, building
keys/status. Không đổi charts. Xem `suumo-rental-price-star.dbml` cho quan hệ.

## Kiểm chứng local

- Parser thật chạy trên **19/19 HTML**, lấy **19 tên**, **4 ứng viên tòa**,
  **5 số phòng**. CSV: `pipeline/tmp/building_qa/parser_html.csv` và `html_backfill.csv`.
- Coverage toàn bộ warehouse: **19/17.946 observations = 0,1059%**; operational
  đạt **19/19**, còn notebook chưa có tên giữ NULL. Coverage JSON:
  `pipeline/tmp/building_qa/coverage.json`.
- **17.946 fact observations**, **17.395 latest listing**, **87 geography**;
  hash của giá/diện tích/lịch sử đổi giá/geography/raw record giữ nguyên baseline.
- `dim_building`: **17.390 phiên bản**, **17.384 identities** gồm **4 candidate
  có tên** và **17.380 placeholder theo listing**; đây không phải số tòa vật lý.
- Listing version: **17.415 → 17.417**. Ba code `100500165889`, `100500165896`,
  `100500165897` mỗi code tăng một version do số phòng từ NULL thành biết;
  code `100518658111` giảm một version khi bỏ thuộc tính building khỏi listing.
- Có **5 observation** bị cờ xung đột thuộc tính tòa trong cùng ngày.
- Build nhánh staging/downstream và các scenario đạt **127 nodes**, không lỗi;
  năm exposures là no-op. Fixture có late arrival, A→B→A, NULL carry-forward,
  missing date, tie/conflict, identity normalization và room/building separation.
- Rebuild giữ nguyên hàng và khóa của **11 relation mart**. Backfill lần hai
  **19 cache hit, 0 HTML được xử lý**. Năm scenario integration xác nhận cache,
  dry-run, failed refresh, code/warehouse error và source metadata không đổi.
- Fixture staging kiểm tra parser mới ưu tiên hơn audit, không lấy tên từ mã
  listing không khớp, không khôi phục tên cũ khi parser mới trả generic, và seed
  thiếu HTML giữ NULL.
- Bảy test graph Airflow đạt: cycle, building trước fact, selection và geography gate.

Chạy lại kiểm thử bằng `make -C pipeline building-test`, crawler unittest
`suumo_source_crawler/tests/test_building_parser.py`, và
`make -C pipeline dbt-check-repeatability`. Script
`pipeline/tests/verify_building_parser_html.py` kiểm tra HTML thật đã tải ở local
bằng runtime crawler có Scrapy, không có mạng. Refresh manifest sau đổi dbt:

```bash
make -C pipeline dbt-airflow-manifest
make -C pipeline dbt-airflow-check
```

Model dùng full rebuild để xử lý đến muộn/correction. Khi backfill hoặc thay
quy tắc identity/SCD phải build lại consumer; không kỳ vọng giữ surrogate cũ
nếu ranh giới phiên bản thay đổi. Dừng BI refresh đến khi build/test hoàn tất;
warehouse hiện chưa publish nguyên tử xuyên toàn bộ graph.
