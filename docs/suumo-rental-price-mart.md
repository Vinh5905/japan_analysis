# SUUMO rental asking-price mart

## Grain và quyết định nghiệp vụ

Một fact = một task hợp lệ. Listing identity là `(source_id, suumo_property_code)`;
không suy diễn thành định danh căn hộ/tòa nhà vật lý. Giữ dimension listing rộng
với thuộc tính building, room và điều kiện thuê; không tách building/room.

| Task | Code | Giá | Hướng | Version |
| --- | --- | ---: | --- | --- |
| 101 | A | 80000 | Nam | 1 |
| 205 | A | 82000 | Nam | 1 |
| 390 | A | 82000 | Đông | 2 |
| 480 | A | 82000 | Nam | 3 |

`parsed_at_utc` là thời điểm xử lý, không phải thời điểm giá có hiệu lực ngoài
thị trường. `information_updated_at` được giữ ở intermediate, không đưa vào mart.
Không tạo periodic snapshot; không thay crawler hoặc backfill notebook.

## SCD2 và nạp lại

`int_suumo__mart_observations` chuẩn bị tập đủ identity/thời điểm, thuộc tính
chuẩn hóa và số đo. `int_suumo__listing_timeline` so sánh JSONB của các thuộc tính
mô tả liên tiếp trong mỗi identity, theo `(parsed_at_utc, task_id)`.

- Code mới: version 1.
- Task mới, chỉ đổi giá hoặc không đổi: thêm fact, dùng cùng version.
- Thuộc tính mô tả đổi: version mới, đóng version trước tại cùng cặp timestamp/task.
- A → B → A: ba phiên bản, không gộp hai đoạn A.
- Cùng task được nạp lại: raw upsert; fact luôn một dòng/task.
- Đến muộn: dựng lại chuỗi theo thời gian, cập nhật mapping fact.
- Sửa parser: restatement từ lịch sử hiện có; không ghi một sự kiện giả tại giờ chạy dbt.

Khóa version là MD5 của JSON array `[source_id, code, first_task_id]`; không dùng
version_number hoặc row_number làm surrogate key. Khóa ổn định khi rerun cùng
input. Khi sửa quá khứ làm đổi ranh giới, khóa có thể đổi; phải rebuild các
consumer cùng graph. `version_number` chỉ là thứ tự hiển thị.

Khoảng SCD là `[from, to)` so sánh cặp timestamp/task. Vì vậy hai phiên bản có thể
cùng timestamp nhưng khác task mà vẫn có thứ tự rõ ràng. Một identity có đúng một
version current. Ngày Nhật được tính trong `dim_date` từ timestamp UTC.

## Diện tích, phí và chất lượng

- Diện tích chính xác chỉ ở fact, giữ precision numeric của intermediate.
- Listing chứa area_band và area_band_sort: unknown, <20, 20-<30, 30-<40,
  40-<50, 50-<70, 70-<100, >=100. Cận dưới bao gồm, cận trên không bao gồm.
  Đây là mặc định phân khúc; thay ngưỡng sẽ restate lịch sử dimension.
- Diện tích đổi trong cùng band chỉ thay fact. Qua band mới tạo phiên bản listing.
- Chi tiết layout chỉ được xuất khi parse full; partial/missing giữ NULL để
  không suy diễn không có phòng/loft. Layout tổng quát vẫn được giữ.
- Tại biên mart, `未定` và dấu gạch của phí là NULL; `なし`, `無し`, `不要` là 0.
  Không sửa ngầm contract của intermediate cũ. Vì vậy số tiền ở mart có thể khác
  các helper notebook/intermediate trước đây ở nhóm sentinel.
- Brokerage: ưu tiên số tiền trực tiếp; nếu thiếu, dùng hệ số tháng × rent.
  Dimension ghi basis; không cộng hai cách biểu diễn phí với nhau.
- Không cộng bảo hiểm/parking vào base monthly cost. Không cộng tiền cọc,
  khấu trừ và các subtotal thành tổng chi phí vào ở chưa được định nghĩa.
- QA ở dimension riêng, không đưa cờ QA vào so sánh SCD. Việc sửa kết quả parse
  làm thay đổi descriptor vẫn có thể restate SCD.
- Thiếu identity hoặc thời điểm: reject view, test cảnh báo. Thiếu giá/diện tích
  vẫn giữ observation và cờ chất lượng; BI chọn mẫu hợp lệ theo measure.

## Ga và tổng hợp giá

Bridge giữ tất cả route, kể cả unparsed. Unparsed dùng station key toàn số 0;
không có route thì không sinh dòng giả. Station label không phải station master.
Không dùng trọng số 1/N. Dùng EXISTS hoặc DISTINCT task trước khi tính giá.

`AVG(rent / area)` và `SUM(rent) / SUM(area)` có nghĩa khác nhau. Phải dùng cùng
một tập dòng có rent hợp lệ và area > 0; chọn một observation/listing cho latest
hoặc as-of trước khi tính. Không cộng tất cả observation để đếm số căn.

## Model và vận hành

DBML: `docs/suumo-rental-price-star.dbml`. Bảy bảng mart: năm dimension,
một fact và một bridge. Ba view: observations (derived measures), latest known,
rejects. Hai helper table ở intermediate phục vụ lập phiên bản.

Models dùng dbt table materialization, dựng lại từ warehouse history mỗi lần.
Đây là lựa chọn rõ ràng để xử lý late arrival, source correction và rerun ở quy mô
hiện tại; chưa phải thuật toán incremental theo listing bị ảnh hưởng. Chi phí
build tăng theo tổng lịch sử. Khi cần incremental, phải giữ nguyên các invariant
SCD và cơ chế tái gắn khóa fact, không chỉ lọc theo timestamp lớn nhất.

```bash
make -C pipeline dbt-build
# Chỉ rebuild graph mart và các helper từ intermediate đã cập nhật:
make -C pipeline dbt-build select='int_suumo__mart_observations+ rental_price_mart_rejects'
```

Airflow chạy `dbt build` sau load, gồm model và tests, rồi `dbt test` toàn bộ. PK được bảo vệ bằng unique index; FK và
các invariant được kiểm tra bằng dbt tests, không tạo physical FK giữa các table
thường xuyên rebuild. Không dùng DBML như migration DDL.

Một dbt build không là transaction xuyên tất cả model. BI refresh phải chỉ chạy
sau khi toàn bộ build/tests thành công; không chạy hai writer dbt đồng thời.
Airflow đã có max_active_runs=1; lệnh chạy tay phải tránh trùng DAG. Chưa có cơ chế
publish schema nguyên tử cho BI truy vấn liên tục trong lúc rebuild.

## Truy vấn as-of và observed-in-period

```sql
-- Replace the literal cutoff; select population BEFORE filtering descriptors.
WITH population AS (
  SELECT DISTINCT ON (source_id, suumo_property_code) *
  FROM mart.rental_price_observations
  WHERE parsed_at_utc <= TIMESTAMPTZ '2026-09-01 00:00:00+09'
  ORDER BY source_id, suumo_property_code, parsed_at_utc DESC, task_id DESC
)
SELECT * FROM population;
```

Observed-in-period: lọc `[period_start, period_end)` trước DISTINCT ON, lấy một
observation cuối cùng mỗi listing trong kỳ. Latest known dùng view có sẵn.
Price changes dùng rental_price_observations rồi mới lọc kỳ; LAG đã tính trên
lịch sử đầy đủ. Các giao diện này không khẳng định listing còn hoạt động.

## Kiểm chứng

Tests bao gồm PK/FK, coverage và reject classification, SCD intervals/current,
consecutive versions, station route coverage, fee semantics, và fixture cho
new listing, price-only change, unchanged task, A→B→A, late-order input,
timestamp ties, NULL descriptor và cùng code thuộc hai nguồn khác nhau.


### Kết quả kiểm chứng local (2026-09-25)

- Trước raw seed, rebuild từ cùng input giữ nguyên fingerprint của 10 mart
  relations. Chạy lại bằng `make -C pipeline dbt-check-repeatability`; thao tác
  này thực sự rebuild mart.
- Sau raw seed và analytics, toàn graph đạt 111/111 nodes: 26 models, 83 data
  tests và 2 unit tests; seed có 5 tests riêng.
- Warehouse hiện có 17.946 observations, 17.395 latest-known listings,
  53.100 bridge routes và 0 rejects. `record_origin` phân biệt 17.927 notebook
  observations với 19 operational observations.
- DBML đã kiểm tra tĩnh 7 bảng / 6 reference và đối chiếu tên cột với code;
  chưa chạy parser chính thức của dbdiagram.
- Các kiểm chứng trên không phải kiểm thử tải production hoặc deploy lên VPS.


## Tọa độ địa chỉ chōme

GSI enrichment chạy bằng Python sau mart observations và trước dim geography; cache ở `raw.suumo_address_geocodes`. Tọa độ và metadata ở `dim_geography`, fact dùng `geography_key`; history/latest views xuất sẵn tọa độ. Không đổi hash/SCD2, không cập nhật Charts. Xem [runbook geocoding](suumo-geocoding.md) và notebook `03_geocode_addresses.ipynb` để chạy thử, bootstrap/backfill, retry và kiểm chứng coverage.
