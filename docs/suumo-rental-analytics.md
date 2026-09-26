# SUUMO rental analytics layer

Tầng `analytics` dùng dữ liệu latest-known từ mart để cung cấp bảng chi tiết và
ba data product đầu tiên cho DA/BI. Nó không thay mart và không xác nhận listing
còn hoạt động trên SUUMO.

## Bảng dùng chung

`analytics.rental_listing_latest` có một dòng cho mỗi
`(source_id, suumo_property_code)`. Bảng nối đúng phiên bản SCD2 của observation
được chọn và giữ `record_origin` để phân biệt dữ liệu vận hành với snapshot
notebook.

## Nhóm 1: mặt bằng giá

`analytics.rental_market_price_summary` có các mức `market_level`:

- `overall`
- `ward`
- `locality`
- `locality_layout_area`
- `locality_layout_area_building`

Mỗi dòng có số listing, sample size, coverage, P25/median/P75 rent, rent trung
bình, median base monthly cost và median rent/m². Dashboard phải lọc đúng một
`market_level` trước khi cộng `listing_count`; các mức là các phép tổng hợp chồng
lên cùng một population.

Median và percentile không được tổng hợp lại bằng SUM/AVG ở BI. Khi filter tùy ý
không khớp grain có sẵn, tính measure từ `rental_listing_latest`.

## Nhóm 2: listing tương đương

`analytics.rental_listing_comparable_benchmark` giữ một dòng mỗi listing và chọn
tier hẹp nhất có ít nhất 5 listing biết rent:

1. locality + layout + area band + building type;
2. ward + layout + area band + building type;
3. ward + layout + area band;
4. không đủ mẫu.

Peer median hiện bao gồm chính listing đang chấm điểm. Đây là benchmark phân
khúc, không phải định giá độc lập. `rent_position` chia thành thấp hơn median ít
nhất 10%, trong khoảng ±10%, cao hơn ít nhất 10%, hoặc chưa chấm được. “Thấp hơn”
không đồng nghĩa với “hời” vì dữ liệu chưa chứa đầy đủ tình trạng nội thất và
điều kiện thuê.

## Nhóm 3: đặc điểm và giá

`analytics.rental_feature_price_summary` đưa dữ liệu về dạng dài theo năm nhóm:

- tuổi nhà;
- tầng;
- hướng;
- kết cấu;
- loại nhà.

Phép so sánh giữ cố định locality, layout và area band. Mỗi feature group được
so median với median toàn stratum. `has_reliable_rent_sample` chỉ true khi feature
có ít nhất 5 rent và stratum có ít nhất 10 rent. Kết quả là mối liên hệ mô tả,
không chứng minh quan hệ nhân quả.

## Snapshot CSV làm raw seed

`analytics/dbt/seeds/suumo_parser_records_seed.csv` là bản sao raw 17.927 record
từ notebook, không phải file clean. dbt nạp nó thành
`raw.suumo_parser_records_seed`. Staging union seed với
`raw.suumo_parser_records` vận hành và ưu tiên operational khi trùng `task_id`,
vì vậy một task chỉ xuất hiện một lần.

Seed này là bootstrap local để có population đủ lớn cho analytics. File khoảng
18 MB nên không phù hợp làm cơ chế ingest production dài hạn. Không thêm các file
CSV mới vào seed mỗi kỳ; dữ liệu mới tiếp tục qua loader raw hiện có.

```bash
make -C pipeline dbt-seed-notebook
make -C pipeline dbt-build
```

Sau lần seed đầu, `make -C pipeline dbt-build` loại seed khỏi build thường xuyên
nhưng vẫn xây các model/test sau khi relation seed đã tồn tại. Warehouse mới phải
chạy `dbt-seed-notebook` trước lần build hoặc DAG đầu tiên.

Kết quả local ngày 2026-09-25: 17.927 seed observations và 19 operational
observations tạo thành 17.946 observation; các task không trùng nhau. Latest-known
có 17.395 listing vì một số property code lặp qua các lần quan sát/nguồn.
