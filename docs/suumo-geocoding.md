# Bổ sung tọa độ địa chỉ SUUMO

## Mức dữ liệu và vị trí lưu

`notebook/03_geocode_addresses.ipynb` đọc CSV current của notebook 02, chạy GSI AddressSearch cho từng địa chỉ chōme duy nhất, rồi ghép tọa độ cho listing bằng merge `many_to_one`. Các hàm nằm trực tiếp trong cell để đọc được cách chuẩn hóa địa chỉ, encode URL, kiểm tra JSON và chọn điểm.

Địa chỉ hiện tại chỉ đến chōme. `coordinate_level = chome` nghĩa là điểm tìm kiếm của địa chỉ đó, **không phải tọa độ chính xác của tòa nhà và không khẳng định là centroid hình học**. Cùng chōme dùng chung tọa độ. Không dùng kết quả cấp quận/thành phố để thay cho chōme; địa chỉ mơ hồ hoặc không hợp lệ giữ tọa độ NULL.

GSI trả `coordinates = [longitude, latitude]`; latitude/longitude lưu dạng số thập phân. Provider hiện tại là `gsi_address_search`, quy tắc `chome_v1`. Điểm phải có địa chỉ khớp sau NFKC và chuẩn hóa riêng số trước hậu tố 丁目; chữ số trong tên địa danh như 東三国 được giữ nguyên. Sanity check Nhật: latitude 20–46, longitude 122–154. Không tự thêm prefecture hoặc số nhà thiếu.

## Chạy notebook

1. Chạy notebook 01/02 nếu chưa có `notebook/data/suumo_rentals_current.csv`.
2. Mở notebook 03 bằng môi trường `notebook/.venv`; chạy từng cell theo thứ tự.
3. Xem request/JSON của địa chỉ mẫu, kiểm tra 5 địa chỉ trước khi chạy toàn bộ.
4. Đọc coverage và các địa chỉ chưa khớp trước khi dùng output train.

Outputs local, được Git ignore:

- `suumo_address_geocodes_cache.json`: phản hồi đầy đủ, provider/policy, lịch retry và audit refresh; ghi nguyên tử sau từng địa chỉ.
- `suumo_address_geocodes.csv`: một dòng cho mỗi địa chỉ, không chứa JSON phản hồi.
- `suumo_rentals_current_geocoded.csv`: tất cả listing nguồn cùng tọa độ và trạng thái; CSV nguồn không bị ghi đè.
- `suumo_geocode_report.json`: coverage theo địa chỉ/listing, cache hits/lookups và danh sách chưa khớp.

Kết quả kiểm chứng local ngày 2026-10-08: CSV có 17.380 listing và 87 địa chỉ duy nhất, 87/87 địa chỉ matched; 17.380/17.380 listing có tọa độ, số dòng/khóa giữ nguyên. Đây là kết quả snapshot đó, không phải cam kết coverage cho batch sau.

## Cache warehouse và refresh

`raw.suumo_address_geocodes` là source do Python loader quản lý, PK `(provider, query_version, address_query)`. dbt đọc qua `stg_suumo__address_geocodes`; không gọi HTTP trong SQL. `attempt_count` đếm lượt xử lý địa chỉ, mỗi lượt có thể gồm tối đa 3 HTTP retry. `raw_response` giữ phản hồi của kết quả hiện tại; `last_attempt_status/last_attempt_response` lưu lần refresh gần nhất.

- `matched`: dùng lại vô thời hạn trong v1, trừ khi chạy `--force`.
- `request_error`: đủ điều kiện thử lại sau ít nhất 1 giờ.
- `not_found`: thử lại sau 7 ngày.
- `ambiguous`, `invalid_response`, `invalid_input`: chờ sửa rule hoặc force.
- Đầu vào thiếu thành phần không có query hợp lệ: không gọi HTTP và dim ghi `invalid_input`.
- Force thất bại giữ nguyên điểm đã matched, ghi lỗi/lần thử mới; không xóa điểm cũ.

Request chạy tuần tự, tối thiểu 1 giây giữa mọi request, timeout 15 giây; HTTP 429/5xx và lỗi mạng có backoff, tối đa 3 retry và tôn trọng Retry-After. Lỗi API theo địa chỉ được lưu rồi tiếp tục. Lỗi DB/cấu hình/code làm task thất bại.

Không chạy loader/dbt thủ công đồng thời với DAG. DAG giữ `max_active_runs=1`; quy trình publish mart hiện vẫn không nguyên tử. Cache giúp build SQL không phụ thuộc API. Khi geocoder ngừng đáp ứng, địa chỉ đã có cache vẫn sử dụng được, địa chỉ mới giữ NULL và retry theo lịch.

## Bootstrap và chạy thủ công

Các lệnh chạy từ root repository, dùng Compose local:

```sh
make -C pipeline geocode-init
make -C pipeline geocode opts="--dry-run"
make -C pipeline geocode opts="--limit 5"
make -C pipeline geocode
make -C pipeline dbt-build select="+dim_geography+"
```

`geocode-init` tạo source cache idempotent cho warehouse đã tồn tại, không reset volume, không gọi HTTP. Fresh warehouse cũng tạo bảng khi chạy warehouse-init. Loader đọc relation mart observations từ manifest, nên cần bootstrap seed/raw và build upstream trước lần enrichment đầu tiên. `--dry-run` chỉ đọc; không tạo bảng, không gọi HTTP và không ghi cache.

Nếu sửa model/config dbt, refresh manifest **trước khi** dùng DAG/loader:

```sh
make -C pipeline dbt-airflow-manifest
make -C pipeline geocode-test
make -C pipeline dbt-airflow-check
```

Có thể import kết quả matched từ cache notebook bằng CLI `--import-cache /path/in/container/cache.json`. File phải có trong container. Loader kiểm tra lại identity, JSON, địa chỉ và điểm trước khi nhập; chỉ thêm địa chỉ chưa có cache warehouse, không ghi đè kết quả đang có.

## Airflow và dim/fact

Thứ tự: load batch → dbt address/mart observations và quality gates phía địa chỉ → `enrich_geographies_cache` → cache source/staging → dim geography → fact/views/analytics.

- `{"mode":"dbt_only","model":"dim_geography"}` backfill địa chỉ từ mart observations đã có rồi dựng lại dim và downstream; task ngoài selection được skip.
- Full `dbt_only` hoặc nhánh `int_suumo__address` cũng chạy enrichment.
- Nhánh chỉ analytics dùng dim/cache đã có, không gọi geocoder.
- Không có batch load thành công: giữ hành vi skip transform hiện tại; địa chỉ cần retry có thể xử lý ở đợt load tiếp theo hoặc manual dbt_only.

Tọa độ và metadata ở `dim_geography`. `fct_rental_price_observation` chỉ dùng FK `geography_key`. Views `rental_price_observations`, `rental_prices_latest_known` và bảng `rental_listing_latest` xuất sẵn tọa độ. `geocode_status = not_requested` khi chưa có cache; status khác matched có latitude/longitude NULL. Không thêm tọa độ vào hash geography hay thuộc tính SCD2 listing, không làm charts trong đợt này.

## Kiểm chứng

Python tests dùng fixture HTTP: normalization, chọn kết quả, thứ tự kinh/vĩ độ, malformed/mơ hồ, retry/rate limit, lịch cache, force giữ điểm cũ và parity notebook. dbt kiểm tra query Python/SQL bằng scenarios, contract điểm, uniqueness/grain và unit test join giữ geography thiếu cache. Test Cosmos kiểm tra đầy đủ coverage/dependency, enrichment gate, cycle, selection và lỗi.

`pipeline/tests/verify_geocode_warehouse.py --capture` lưu fingerprint các cột nghiệp vụ trước khi bổ sung; chạy lại không có `--capture` so sánh cùng tập cột, bao gồm fact, dim listing, geography cũ, history/latest và raw. Baseline phải được capture trước lần build đầu tiên; sau đó không capture lại để tránh che mất regression.


Acceptance DAG local (scheduler tạm dừng) bằng `pipeline/tests/integration_geocoding.py --cache-miss --log-file <path>`: tạm bỏ một cache row đã sao lưu để mô phỏng query chưa có cache; DAG `dbt_only` nhánh geography tự gọi GSI, 1 lookup/1 matched và 86 cache hits, upstream ngoài nhánh không rebuild. Nếu test thất bại row được phục hồi. Chạy lại không có `--cache-miss` kiểm tra 87 cache hits/0 lookup; `--executor` dùng LocalExecutor hiện tại. Không thêm record giả vào nguồn listing. Cần capture business baseline trước đợt build đầu tiên và dừng scheduler khi chạy QA.

Kết quả acceptance local 2026-10-08: nhánh geography chạy 9 model, 59 data test và 2 unit test, tất cả thành công và mỗi node xuất hiện một lần. Cả lần cache miss và lần chạy lại qua LocalExecutor đều success; lần thứ hai 87 cache hits/0 lookup. Fingerprint 8 relation theo bộ cột nghiệp vụ trước bổ sung giữ nguyên. Warehouse có 17.946 fact observations, 17.415 listing versions, 87 geography, 17.395 latest listings và 53.100 station routes; tất cả latest listings có tọa độ chōme. Fixture geocoder 6 test và graph 6 test đạt; bootstrap cache idempotent đã chạy thử. Scheduler local được khởi động lại sau QA.
