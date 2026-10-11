# Địa chỉ chi tiết và tọa độ building — local

Pipeline tìm bằng **tên tòa + chōme**, HTTP thuần. Chỉ nhận một địa điểm khớp
tên chuẩn hóa, đúng chōme, thêm block/số nhà, có Place ID và cặp tọa độ hợp lệ.
`building_poi` là điểm địa điểm provider, chưa xác minh độc lập mái tòa/thửa
đất. Không lấy dòng đầu hoặc fallback chōme; tên giả có thể trả tòa khác.

## Grain và dữ liệu

Input `int_suumo__building_lookup_candidates`: một dòng mỗi named building key,
không đọc cache. Python không tính lại các khóa. Cache
`raw.suumo_building_locations` khóa `(provider, query_version, building_key)`:
`google_maps_http` / `building_name_chome_v1`. Lưu query, raw response JSONB,
Place ID/URL và audit lần thử mới nhất tách riêng accepted result.

`dim_building` left join cache, thêm:

- building_full_address_raw, building_full_address, postal_code, address_block, address_house_number.
- latitude, longitude, coordinate_level.
- geocode_status, geocode_provider, geocode_matched_address, geocode_match_method, geocoded_at.
- google_place_id, google_maps_url.

Số nhà không phải số phòng/mã thửa. Địa chỉ SUUMO vẫn nguyên bản trong
staging/history và `int_suumo__address.address_raw`. Enrichment theo thông tin
mới nhất áp dụng cho các phiên bản cùng named candidate, không tham gia
attributes/hash SCD2. `geocoded_at` là ngày lookup, không phải bằng chứng vị trí
đã được biết ở ngày observation. Placeholder unresolved không nhận tọa độ
ngược từ tên xuất hiện sau.

Fact giữ FK building_version_key. Views history/latest lấy điểm từ building,
giữ tên/kiểu cột tọa độ nhưng **ý nghĩa chuyển từ chōme sang building POI**;
không khớp thì NULL dù cache GSI có điểm. Dim geography/cache GSI giữ legacy,
DAG ngừng gọi GSI. Không sửa charts, zoning/FAR hoặc VPS.

## Chạy local

Dừng scheduler và dbt writer trong bootstrap/backfill/QA. Không reset volume:

```sh
make -C pipeline build
make -C pipeline building-location-verify opts="--capture-baseline"
make -C pipeline building-location-init
make -C pipeline dbt-airflow-manifest
make -C pipeline dbt-build select="int_suumo__building_events+ stg_suumo__building_locations"
make -C pipeline building-location opts="--dry-run"
make -C pipeline building-location opts="--limit 30"
make -C pipeline dbt-build select="dim_building+ stg_suumo__building_locations"
make -C pipeline building-location-verify
```

Hoặc DAG `suumo_load_to_warehouse` với
`{"mode":"dbt_only","model":"dim_building"}` khi các input relations đã có.
Graph: candidates/quality gates → enrichment → cache/staging → dim → fact/views.
Chọn analytics dùng dim/cache sẵn có, không HTTP. Không có batch thành công
giữ skip. Test đọc cache không làm gate trước cache writer để tránh cycle.

Baseline được chụp trước thay đổi trên warehouse đã có mart. Warehouse mới
cần bootstrap mart trước khi chụp baseline cho lookup đầu tiên.

SUUMO_BUILDING_LOOKUP_LIMIT mặc định 30; CLI --limit ghi đè, cache hit không
chiếm lượt. Một worker, tối thiểu 3 giây/request, timeout 15 giây. Dry-run
không DDL/HTTP/ghi cache, cần init/input đã có. --force không bypass cooldown.

Matched tái sử dụng không refresh định kỳ; not-found retry sau 7 ngày;
timeout/5xx tối đa 3 request, backoff 2/4 giây, hết lượt retry đợt sau ≥1 giờ.
429 dừng lượt và cooldown ≥1 giờ/Retry-After; 403/CAPTCHA/consent dừng lượt
24 giờ. Cooldown đọc audit mọi query version và tồn tại qua restart; phần
còn lại deferred. Ambiguous/invalid input/response chờ sửa quy tắc hoặc force.
Refresh lỗi giữ accepted point; last_attempt_status/response lưu lỗi mới.
PostgreSQL advisory lock theo provider bảo đảm một worker giữa các DAG/CLI;
lock tồn tại qua commit từng địa chỉ và tự thả khi connection đóng. Lượt
khác gặp worker đang chạy sẽ defer lookup, cache hit vẫn dùng được.
API lỗi được ghi để mart dùng cache/NULL; lỗi code/warehouse làm task fail.
Không đưa JSON response vào XCom; không đổi proxy để vượt block.

## Dependencies, license và kiểm thử

Vendor MIT commit `3d01d6c5ee23cc5a0dcf088b6d379fb107a51908`, LICENSE/UPSTREAM
ở pipeline/vendor/google_maps. Chỉ lấy text-search/parser; không có nested
Git, browser, grid, reviews, email, SQLite hoặc proxy pool.

curl_cffi 0.16.3 cần cffi>=2, Airflow/Snowflake có cffi<2. Dockerfile tạo
**venv HTTP riêng** không đổi constraint Airflow. SUUMO_BUILDING_HTTP_PYTHON
chỉ Python worker; parent gửi JSON stdin và đọc JSON output. TLS verify bật.
MIT cấp quyền dùng code, không cấp quyền dùng dữ liệu Maps cho training/bulk.
Xem [Google Maps terms](https://www.google.com/help/terms_maps/).

```sh
make -C pipeline building-location-test
make -C pipeline building-location-cache-test
make -C pipeline dbt-airflow-check
```

Fixture kiểm tra normalization, hai tòa cùng chōme, fake/suffix/address mismatch,
ambiguity, malformed/nonfinite point/JSON, timeout/5xx/429/CAPTCHA, cache,
refresh preservation, dry-run, limit và cooldown. dbt checks grain, accepted
point contract, tọa độ views và số observation. Baseline bảo vệ fact, listing,
building SCD2, geography, raw records và lịch sử giá.
Audit/coverage/sample ở analytics/dbt/target/building_locations/ (Git ignored).
Coverage theo building và observation báo thực tế, không giả định 100%.
`make -C pipeline building-location-verify` tạo `coverage.json`, `report.md`
và `unmatched_observations.csv`; chỉ chạy khi các dbt writer đã dừng.

QA DAG thực tế trong image Linux dùng
`pipeline/tests/integration_dbt_airflow.py --scenario building-first`, sau đó
`--scenario building`, `--scenario analytics` và `--scenario empty`.
Lượt đầu cho phép metadata enrichment thay đổi nhưng bảo vệ các cột baseline;
lượt sau so sánh fingerprint toàn bộ relations và yêu cầu request_count=0.
Analytics-only yêu cầu task enrichment skipped. Các báo cáo/log ở
`analytics/dbt/target/airflow/qa/` (Git ignored).

## Kết quả local 2026-10-10

- Image Linux build và pip check đạt; 13 HTTP/matching/cache fixtures, 7 graph
  tests và 70 dbt data/unit checks trong nhánh bootstrap đạt.
- DAG building lookup thật: 4 ứng viên, 4 request, 4 matched; repeat 4 cache
  hit, 0 HTTP. Mỗi lượt chạy đúng 83 node và success. Analytics-only chạy
  đúng 44 node, enrichment skipped, fingerprint warehouse không đổi.
- No-batch success với 0 dbt node và enrichment skipped. Webserver/scheduler
  local đã recreate với image mới, health healthy; dbt docs đã khôi phục.
- 17.946 fact observations, 17.417 listing versions, 17.390 building versions,
  87 geography và các khóa/giá/diện tích/lịch sử giá giữ nguyên baseline.
- Coverage: 4/4 ứng viên đủ tên/chōme; 19/19 observation có tên; 19/17.946
  toàn bộ (0,1059%). 17.927 observation không có tên vẫn NULL.
- Ví dụ địa chỉ nhận được: 宮原5丁目5-16, 加島4丁目16-2,
  十三本町2丁目16-7, 西宮原1丁目7-51, đều thuộc 大阪府大阪市淀川区.
  Đây là kết quả khớp provider, chưa xác minh độc lập mái tòa.
