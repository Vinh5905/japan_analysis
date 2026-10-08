# SUUMO Rental BI Boards

Các board dùng dbt Charts 0.8.0 và đọc trực tiếp các model đã kiểm thử trong
`analytics`/`mart`. Mục tiêu là hỗ trợ quyết định về mặt bằng giá, định giá
listing, phân khúc sản phẩm, khả năng tiếp cận ga và chất lượng dữ liệu.

## Danh mục board

| Board | Người dùng chính | Câu hỏi quyết định |
| --- | --- | --- |
| `rental_market_overview.yml` | Portfolio/market manager | Thị trường hiện có quy mô, mặt bằng giá và cơ cấu nguồn cung ra sao? |
| `rental_pricing_opportunities.yml` | Pricing analyst/landlord | Listing nào lệch đáng kể so với peer group đủ mẫu? |
| `rental_feature_pricing.yml` | Product/asset manager | Tuổi nhà, tầng, hướng, kết cấu và loại nhà liên hệ với premium thế nào? |
| `rental_station_access.yml` | Location analyst | Ga/tuyến nào có nguồn cung sâu, mức giá và travel time đáng chú ý? |
| `rental_data_quality.yml` | Data/analytics engineer | Coverage và parse issue có đủ tốt để tin dashboard không? |

## Quy tắc grain

- `rental_listing_latest` có một dòng cho mỗi `(source_id, suumo_property_code)`.
- “Latest-known” chỉ là observation mới nhất trong warehouse, không chứng minh
  listing còn active ngoài thị trường.
- Median và percentile luôn được tính lại trên population sau filter. Không
  cộng hoặc lấy trung bình các median từ `rental_market_price_summary`.
- Comparable benchmark gồm chính listing đang chấm điểm và cần ít nhất năm mẫu.
- Feature premium giữ cố định locality, layout và area band; kết quả là mô tả,
  không phải quan hệ nhân quả.
- Station là quan hệ một-nhiều. Board dedup `(task_id, station_label_key)` trước
  khi tổng hợp từng ga; cùng listing vẫn có thể xuất hiện ở nhiều ga.
- Số tiền là asking price JPY, không phải doanh thu hay giá giao dịch.

## Insight của snapshot local ngày 2026-09-26

Các con số này dùng để giải thích vì sao board được thiết kế như hiện tại;
dashboard sẽ query lại dữ liệu mới khi mở.

- 17.395 listing latest-known, rent coverage 100%, median rent 79.000 JPY và
  median rent/m² khoảng 3.143 JPY.
- Population hiện tập trung hoàn toàn ở 淀川区, vì vậy dashboard so sánh
  `locality` thay vì tạo chart theo `ward` chỉ có một cột.
- 1K là layout lớn nhất với 7.712 listing và median 71.000 JPY; 1LDK đứng sau
  với 4.668 listing nhưng median 119.000 JPY.
- 67,6% listing nằm trong ±10% peer median, 19,0% thấp hơn ít nhất 10% và 13,3%
  cao hơn ít nhất 10%. 塚本, 新高 và 西中島 có tỷ trọng thấp hơn peer cao trong
  các locality đủ mẫu.
- Sau khi giữ locality/layout/area band, nhóm tuổi 0–5 năm có premium rent có
  trọng số khoảng +2,2%; nhóm 31+ năm khoảng -13,6%. Tầng 11+ khoảng +3,6%.
- Với ga có nhiều listing, 東三国 có median khoảng 80.000 JPY ở median 7 phút;
  新大阪 khoảng 81.000 JPY; 十三 trên 阪急神戸線 khoảng 75.500 JPY.
- Quality hiện tốt cho core fields: không có missing core/floor issue, có 28
  layout detail parse failures và một listing thiếu station access đầy đủ.

## Runtime và vận hành local

Image dùng `dbt-core==1.11.15`, `dbt-postgres==1.11.0` và
`dbt-charts[postgresql]==0.8.0` trong cùng `/opt/airflow/dbt_venv`. Virtualenv
này tách dependency dbt/Charts khỏi Python của Airflow. `fonts-noto-cjk` cung
cấp glyph tiếng Nhật cho PNG/PDF/SVG.

Từ root repository:

```bash
make -C pipeline dbt-build
make -C pipeline dbt-charts-validate
make -C pipeline dbt-charts-smoke
make -C pipeline dbt-charts-up
```

Mở `http://localhost:3000`. Xem log hoặc dừng server:

```bash
make -C pipeline dbt-charts-logs
make -C pipeline dbt-charts-down
```

Render một board ra HTML trong `analytics/dbt/renders/`:

```bash
make -C pipeline dbt-charts-render \
  board=charts/rental_market_overview.yml format=html
```

Đường dẫn trực tiếp của các board:

- `http://localhost:3000/rental_market_overview`
- `http://localhost:3000/rental_pricing_opportunities`
- `http://localhost:3000/rental_feature_pricing`
- `http://localhost:3000/rental_station_access`
- `http://localhost:3000/rental_data_quality`

`dbt-charts-validate` kiểm tra YAML và dùng PostgreSQL EXPLAIN, không thực thi
full query. PostgreSQL không trả result schema từ EXPLAIN, nên dct vẫn báo
`WARN-COLUMN-CHECK-UNAVAILABLE`; static analyzer cũng có thể báo không suy ra
cột do filter Jinja hoặc CTE/join. `dbt-charts-smoke` thực thi query read-only,
render JSON và kiểm tra tên cột/grain, population, bộ lọc, tỷ trọng peer,
empty state và distinct listing khi dùng bridge ga. Không insert dữ liệu test.

Sau khi Airflow build mart/analytics, server có thể còn dùng cache cũ tối đa
15 phút (quality board 5 phút). Có thể restart service Charts để xóa cache
in-memory khi cần xem ngay dữ liệu mới. Footer "Data as of" là thời điểm render,
không phải ngày observation nguồn; population hiện có observation từ
2026-07-27 đến 2026-08-09.

## Kiểm chứng ngày 2026-10-07

- Image build thành công với Core 1.11.15 / adapter 1.11.0 / Charts 0.8.0.
- dbt build đạt 111/111 nodes, 26 model, 83 data test và 2 unit test.
- Năm board (40 visualization) render PNG và HTML không có chart error.
- Smoke kiểm tra default của cả năm board; filter layout/locality, population
  không có dữ liệu, 5 phút tiếp cận ga và cả năm nhóm feature đều đạt.
- PNG đã review và sửa font Nhật, nhãn ga/locality bị cắt và mã listing bị
  auto-format. Mã listing hiển thị với prefix `nc_` để giữ nguyên các chữ số.
- Cả năm URL board, dbt docs và Airflow health trả HTTP 200. Airflow
  scheduler/webserver, dbt docs và Charts đã được tạo lại bằng image mới;
  scheduler/webserver healthy. Cấu hình hiện phục vụ local, chưa deploy Cloud/VPS.
- Kiểm tra trên trình duyệt: chọn layout `1K` đổi KPI từ 17.395 xuống 7.712,
  URL giữ filter `?layout=1K`; đã trả board về population mặc định sau kiểm tra.
