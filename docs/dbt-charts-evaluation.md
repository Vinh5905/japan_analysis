# Tìm hiểu và đánh giá dbt Charts cho Japan Analysis

> Tài liệu được kiểm tra theo tài liệu chính thức ngày **2026-09-26** và lấy
> **dbt Core 1.x** làm runtime của project. dbt Charts đang ở giai đoạn **beta, pre-1.0**,
> nên cú pháp và cách đóng gói có thể còn thay đổi.

## 0. Version runtime và dbt Charts

Hai sản phẩm có version độc lập:

| Tên                       | Version hiện tại khi kiểm tra            | Ý nghĩa                                              |
| ------------------------- | ---------------------------------------- | ---------------------------------------------------- |
| dbt Core                  | 1.11.15                                  | Runtime Python dùng để build/test/docs project       |
| dbt-postgres              | 1.11.0                                   | Adapter PostgreSQL tương thích dbt Core 1.x          |
| dbt Charts                | package `dbt-charts` 0.8.0, beta/pre-1.0 | Engine/CLI `dct` dùng để query và render board       |
| Runtime cũ của repository | dbt Core 1.8.9                           | Đã được nâng trong cùng environment lên Core 1.11.15 |

Wheel `dbt-charts==0.8.0` khai báo `dbt-core>=1.8,<2`; extra PostgreSQL khai
báo `dbt-postgres>=1.10,<2`. Vì project tiếp tục dùng dbt Core, `dbt`, adapter
và `dct` được pin chung trong `/opt/airflow/dbt_venv`. dbt Core tạo
`target/manifest.json`; `dct` đọc artifact đó để resolve `ref()` và dùng cùng
profile để query PostgreSQL.

### Repo tham khảo `i-test-dbt-platform`

Repo tham khảo dùng cách phù hợp là commit board YAML và các `dct-*` agent skill
cùng source code. Tuy nhiên README của repo ghi dbt Core 1.xx và cài cả
`dbt-postgres` lẫn `dbt-charts` bằng lệnh không khóa version; repo cũng không có
lockfile cho hai runtime. Do đó không thể xác định chính xác version CLI họ đã
chạy chỉ từ repository.

13 skill đã commit trong repo tham khảo khớp hoàn toàn với output cài agent của
wheel chính thức `dbt-charts==0.8.0`. Project này dùng snapshot skill đó, nhưng
pin version rõ ràng và dùng dbt Core 1.x tương thích với Charts. Chi tiết
provenance nằm tại `docs/dbt-charts-agent-skills.md`.

## 1. dbt Charts là gì?

dbt Charts là một lớp trực quan hóa khai báo bằng YAML do dbt Labs phát triển.
Trong một board, SQL mô tả dữ liệu cần lấy; YAML mô tả chart, filter, cách trình
bày và layout. Board được lưu trong Git cạnh project dbt và được CLI `dct`
biên dịch thành dashboard tương tác hoặc file tĩnh.

Luồng xử lý chính:

```text
dbt model / warehouse
        │
        ▼
SQL query trong board YAML
        │
        ▼
dct: validate → execute → render
        │
        ├── local dashboard qua dct serve
        └── HTML / PDF / PNG / SVG / JSON
```

dbt Charts có hai phần cần phân biệt:

| Phần                     | Vai trò                                                                       | Giấy phép / chi phí                                                                                   |
| ------------------------ | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `dbt-charts` + CLI `dct` | Engine, ngôn ngữ YAML, validate, query, render và local server                | Mã nguồn mở Apache 2.0                                                                                |
| dbt Charts Cloud         | Host board, kết nối Git/warehouse dùng chung, phân quyền, refresh và cộng tác | Dịch vụ hosted; gói Individual hiện miễn phí tối đa 3 cộng tác viên, Team chưa công bố giá hoàn chỉnh |

`dct serve` là server phát triển local. Nó không có đăng nhập hay phân quyền;
mọi người truy cập được địa chỉ server đều xem được mọi board đang serve. Khi
cần chia sẻ có quyền truy cập, lịch refresh và kết nối warehouse dùng chung thì
dùng Cloud hoặc tự triển khai đầu ra tĩnh theo nhu cầu của hệ thống.

### dbt Charts khác dbt Docs thế nào?

| Công cụ    | Câu hỏi nó trả lời                                                  |
| ---------- | ------------------------------------------------------------------- |
| dbt Docs   | Model nào tồn tại, column có ý nghĩa gì, lineage và catalog ra sao? |
| dbt Charts | Giá thuê, phân bố, benchmark và KPI kinh doanh đang như thế nào?    |

dbt Docs dùng artifact/index do dbt Core tạo để hiển thị documentation và
lineage. dbt Charts chạy query lên bảng/view đã build để tạo dashboard BI. Project
nên giữ cả hai: Docs cho cấu trúc dữ liệu; Charts cho phân tích dữ liệu.

## 2. Vì sao đáng cân nhắc cho project này?

### 2.1. Dashboard là code

Query, chart và layout là text nên có thể:

- lưu cùng repository với dbt model;
- review qua pull request và xem diff rõ ràng;
- thay model và board trong cùng branch;
- validate trong CI trước khi merge;
- tìm chart bị ảnh hưởng khi đổi cột bằng `dct impact`;
- quay lại phiên bản trước qua lịch sử Git.

Điều này hợp với project hiện tại vì logic dữ liệu đã được kiểm soát bằng dbt.
Chart có thể đọc các model `analytics` và `mart` đã test, thay vì tạo thêm một
lớp transformation khó truy vết trong một BI tool riêng.

### 2.2. Giữ đúng ranh giới giữa model và visualization

dbt tiếp tục chịu trách nhiệm cho grain, dimension, fact, benchmark, percentile
và test dữ liệu. Board chỉ chọn dữ liệu, lọc và trình bày. Với SUUMO, cách chia
này đặc biệt quan trọng vì:

- `analytics.rental_market_price_summary` chứa nhiều `market_level` chồng lên
  cùng population;
- median, P25 và P75 không được cộng hoặc lấy trung bình lại ở BI;
- station là quan hệ một-nhiều qua bridge;
- các cờ `has_reliable_*` quyết định một nhóm có đủ mẫu để diễn giải hay không.

YAML và SQL nằm trong Git giúp các quy tắc này được ghi ngay cạnh chart và được
review như code.

### 2.3. Phù hợp với workflow local và agent

CLI có các lệnh dành cho cả người và coding agent. Package còn cung cấp skill,
MCP server tùy chọn, tài liệu offline và lỗi validation có mã, file, dòng cùng
gợi ý sửa. Project có thể cài skill riêng bằng `dct init skills agents` vào
`.agents/skills/`.

### 2.4. Không khóa dữ liệu vào định dạng BI độc quyền

Board dùng YAML, SQL và Git. Engine mã nguồn mở có thể render local ra nhiều
định dạng. Nếu sau này không dùng dbt Charts Cloud, định nghĩa board vẫn còn và
có thể chạy bằng CLI.

## 3. Các thành phần cơ bản

### 3.1. Project config: `dbt_charts.yml`

File này nằm cạnh `dbt_project.yml` và chỉ chứa cấu hình engine như source,
server, timeout và số worker. Style/theme mặc định của board nằm trong
`charts/meta.yml`.

Ví dụ phù hợp với project:

```yaml
sources:
    warehouse:
        type: dbt_profile
        profile: japan_analysis
        target: dev

execution:
    max_workers: 4
    max_query_duration_seconds: 60
```

`type: dbt_profile` tái sử dụng `profiles.yml`; không cần lặp credentials trong
board. dbt Charts source là cấu hình kết nối, khác với resource `sources:` của
dbt dùng để khai báo raw table.

### 3.2. Board: `charts/*.yml`

Mỗi file YAML, YML hoặc Markdown dưới `charts/` trở thành một page. Thư mục con
trở thành path con. Một board thường có:

```yaml
title: "SUUMO rental market"
source: warehouse
theme: clarity

variables: {}
queries: {}
charts: {}
rows: []
```

Các board có thể import partial dùng chung. Convention chính thức là đặt partial
trong `charts/partials/` và bắt đầu tên bằng `_`.

### 3.3. Query

dbt Charts hiện hỗ trợ bốn loại query:

1. **SQL**: chạy trực tiếp trên warehouse; đây là loại chính của project.
2. **Values**: vài dòng dữ liệu đặt ngay trong YAML, phù hợp cho prototype và
   reference nhỏ.
3. **HTTP/API**: gọi endpoint JSON; chỉ chạy local, chưa hỗ trợ trên Cloud.
4. **Schema**: đọc metadata source/schema/table/column để làm catalog hoặc health
   board.

Một SQL query có thể tham chiếu model dbt:

```yaml
queries:
    market_by_ward:
        sql: |
            select
              ward,
              listing_count,
              median_rent_jpy
            from {{ ref('rental_market_price_summary') }}
            where market_level = 'ward'
            order by median_rent_jpy desc
```

`ref()` và `source()` được giải từ `target/manifest.json`, vì vậy phải chạy
`dbt parse`, `dbt run` hoặc `dbt build` sau khi clone project và trước khi render
board dùng `ref()`.

Nhiều chart có thể dùng chung một query; query chỉ chạy một lần. SQL query cũng
có thể dựng từ query khác bằng `{{ queries.query_name }}`. Kết quả từ hai source
khác nhau có thể join trong cache DuckDB qua `{{ queries.query_name.cache }}`.

### 3.4. Chart

Chart ánh xạ cột từ query vào các channel như `x`, `y`, `color`, `size`,
`theta`, `value`, `latitude` và `longitude`.

Các loại chart core được công bố hiện tại:

- bar, histogram, line, area, scatter và heatmap;
- pie và donut;
- KPI, table, callout và spark bar;
- point map, bubble map, choropleth map và geoshape.

Ngoài ra có các hình được ghép từ core chart như lollipop, bullet, slope, bump,
dot plot, stacked/normalized bar, streamgraph, funnel, target/reference line,
moving average, range và small multiples. Layered chart cho phép kết hợp bar với
line hoặc nhiều measure trên cùng chart.

Chart được render bằng Vega-Lite, nhưng board chỉ được dùng bề mặt YAML có type
của dbt Charts. Không thể chèn tùy ý một Vega-Lite spec, `mark`, `encoding`,
`transform` hoặc composition block thô.

### 3.5. Layout và nội dung

`rows` xếp nội dung theo chiều dọc; `cols` đặt cạnh nhau. Có thể lồng rows/cols,
chia tabs, thêm text/Markdown, ảnh, section có thể collapse và import header hoặc
KPI row dùng chung. Kích thước có thể điều khiển bằng width, height, aspect ratio
và frame width.

### 3.6. Variable và filter

Variable tạo control như:

- select hoặc multiselect;
- text/textarea;
- number/slider;
- date picker/date range;
- checkbox/radio.

Variable không tự lọc dữ liệu. Mỗi query phải chủ động nối nó vào `WHERE`:

```yaml
variables:
    ward:
        column: analytics.rental_listing_latest.ward
        input: multiselect

queries:
    listings:
        sql: |
            select *
            from {{ ref('rental_listing_latest') }}
            where {{ filter('ward', ward) }}
```

`filter()` và `filter_date_range()` bind parameter thay vì ghép string trực
tiếp, xử lý list, giá trị rỗng và giảm rủi ro SQL injection. Filter có thể lấy
option từ column, static list hoặc query. Có thể tạo filter phụ thuộc, đặt filter
qua URL, ẩn control và dùng link trên chart để drill down hoặc cập nhật filter.

Mặc định variable rỗng tạo điều kiện cho phép toàn bộ dữ liệu. Với board bắt
buộc scope, có thể dùng `none='deny'` để trả về zero row khi chưa có giá trị.

### 3.7. Style và theme

Có 5 theme dựng sẵn: `clarity`, `paper`, `vivid`, `neon` và `stark`. Có thể tạo
theme YAML riêng kế thừa theme gốc. Style hỗ trợ palette, màu theo category hoặc
gradient, format số/ngày, axis, legend, tooltip, nhãn giá trị, conditional
formatting, font, background và spacing.

Table hỗ trợ pagination, định dạng từng cột, link, sparkline, support table và
pivot. Với pivot và total, query phải trả sẵn grain và total; renderer không âm
thầm aggregate dữ liệu.

## 4. CLI `dct` được dùng như thế nào?

### 4.1. Cài đặt

Package hiện yêu cầu Python 3.10 đến 3.13. Project cài CLI trong cùng virtualenv
dbt Core của Airflow image:

```bash
pip install \
  "dbt-core==1.11.15" \
  "dbt-postgres==1.11.0" \
  "dbt-charts[postgresql]==0.8.0"
dct --version
```

Extra `postgresql` cài adapter để `dct` tự mở kết nối tới PostgreSQL. Ba package
được pin cùng nhau vì đều dùng dbt Core 1.x:

```text
dbt Core 1.11.15     → dbt build/test/docs, tạo manifest
dbt-postgres 1.11.0  → kết nối warehouse PostgreSQL
dbt Charts 0.8.0     → đọc manifest/profile và render board
```

### 4.2. Các lệnh chính

| Lệnh                            | Công dụng                                                                              |
| ------------------------------- | -------------------------------------------------------------------------------------- |
| `dct init`                      | Tạo `charts/`, config và board hướng dẫn                                               |
| `dct validate [PATH]`           | Kiểm tra schema YAML và reference; `--strict` biến warning thành failure               |
| `dct validate --warehouse`      | Kiểm tra query bằng cơ chế adapter; PostgreSQL dùng EXPLAIN và không trả output schema |
| `dct serve`                     | Chạy local server và hot reload                                                        |
| `dct render BOARD --format ...` | Render HTML, PDF, PNG, SVG, JSON hoặc data                                             |
| `dct query BOARD QUERY`         | Chạy một named query để debug                                                          |
| `dct search QUERY`              | Tìm board theo nội dung                                                                |
| `dct impact COLUMN`             | Tìm board tham chiếu cột sắp thay đổi                                                  |
| `dct describe`                  | Mô tả project/board theo metadata đã parse                                             |
| `dct docs [TOPIC]`              | Đọc YAML reference offline                                                             |
| `dct examples`                  | Xem board mẫu kèm package                                                              |
| `dct migrate`                   | Nâng file YAML cũ sang syntax hiện tại                                                 |
| `dct init ci`                   | Sinh GitHub Actions workflow để validate board                                         |
| `dct skills intro`              | Điểm bắt đầu cho coding agent                                                          |

`dct validate` không cần warehouse cho việc kiểm tra cấu trúc. `dct render` chạy
query thật và có thêm warning theo dữ liệu, ví dụ cột chart toàn null. Lỗi ở một
chart được hiển thị trong tile riêng để phần còn lại của board vẫn render.

### 4.3. Cache và chi phí query

Query result được cache; tài liệu hiện nêu TTL mặc định 24 giờ. Có thể đặt cache
ở project, source, board hoặc query và tắt bằng `cache: false`. Local có thể
restart server, dùng `--no-cache`, hoặc cấu hình TTL để refresh. Refresh theo
lịch local có thể dùng cron chạy `dct render`; Cloud có cơ chế refresh và cache
dùng chung cho viewer.

Nên aggregate ở dbt/SQL trước khi đưa sang chart, dùng query chung cho nhiều
chart, đặt row limit và query timeout. Các việc này vừa giảm thời gian render vừa
giảm tải cho warehouse.

## 5. CI, kiểm thử và tác động thay đổi

Một pipeline hợp lý có ba mức:

```text
dbt build/test
      ↓
dbt parse                 tạo target/manifest.json
      ↓
dct validate --strict     kiểm tra board không cần chạy full query
      ↓
dct validate --warehouse kiểm tra relation/cột với warehouse QA
      ↓
dct render                smoke test dữ liệu và kết quả render
```

`dct init ci` có thể sinh GitHub Actions workflow. Validation có thể chạy không
cần warehouse credential; `dbt parse` kiểm tra `ref()`/`source()` so với manifest.
Trước khi rename hoặc xóa cột, chạy `dct impact <column>` để tìm board chịu ảnh
hưởng.

Vì syntax còn pre-1.0, khi nâng `dbt-charts` cần đọc changelog, chạy
`dct migrate`, refresh agent skills và validate/render lại toàn bộ board.

## 6. Bảo mật và vận hành

- Board chỉ nên dùng credential read-only. Với PostgreSQL, engine có SQL
  allowlist nhưng quyền `SELECT` ở database mới là lớp bảo vệ chắc chắn.
- Đưa secret vào environment hoặc `profiles.yml`; không ghi password trong board,
  query hay output render.
- `dct serve` không có access control và không nên expose công khai.
- Filter helper dùng parameter binding; tránh ghép trực tiếp input người dùng vào
  SQL.
- Đặt `max_query_duration_seconds`, row/result limit và worker vừa phải.
- File render tĩnh có thể chứa dữ liệu đã query. Cần quản lý nó như một bản xuất
  dữ liệu, đặc biệt nếu chart dùng thông tin nhạy cảm.
- Cloud cần read-only warehouse user và hiện chỉ kết nối repository GitHub theo
  FAQ chính thức.

## 7. Giới hạn hiện tại cần biết

1. **Beta, pre-1.0:** cú pháp dự kiến còn thay đổi. Engine có migration tương
   thích ngược, nhưng project vẫn phải pin version và test khi nâng.
2. **Semantic Layer chưa có:** hiện chart dùng SQL trực tiếp; truy vấn dbt metric
   bằng tên mới nằm trong kế hoạch.
3. **Local server không phải portal BI nhiều người dùng:** không có login, role,
   publish workflow hay scheduled refresh hoàn chỉnh.
4. **Cloud là sản phẩm riêng:** hosting, permissions, visual editor và shared
   connections không phải tính năng của CLI mã nguồn mở.
5. **Không có email schedule dựng sẵn:** local và Cloud đều chưa có; muốn gửi PDF
   định kỳ phải ghép `dct render` với scheduler/mailer.
6. **Không có Vega-Lite escape hatch tùy ý:** chỉ các property có type của dbt
   Charts được chấp nhận.
7. **Chart không sửa grain sai:** renderer không thể cứu query trùng dòng hoặc
   percentile bị aggregate lại. Grain vẫn phải được bảo đảm ở dbt và SQL.
8. **Dashboard vẫn tạo tải lên warehouse:** filter hoặc render có thể chạy lại
   query. Cache, aggregate table và timeout vẫn cần được thiết kế.

## 8. Mức độ phù hợp với Japan Analysis

### 8.1. Tương thích kỹ thuật

| Hạng mục project                     | Mức phù hợp     | Ghi chú                                                     |
| ------------------------------------ | --------------- | ----------------------------------------------------------- |
| PostgreSQL 16                        | Tốt             | Có adapter `dbt-charts[postgresql]`                         |
| dbt Core 1.11.15                     | Tốt             | Build/test/docs và tạo manifest cho dbt Charts              |
| dbt-postgres 1.11.0                  | Tốt             | Thỏa extra PostgreSQL của dbt Charts 0.8.0                  |
| Model mart/analytics dạng table/view | Tốt             | Query SQL trực tiếp, không cần Semantic Layer               |
| Docker Compose local                 | Tốt             | Warehouse đã expose host port `15433`                       |
| Git workflow                         | Tốt             | Board, model và docs cùng repository                        |
| Airflow                              | Không phụ thuộc | Airflow tiếp tục build dbt; chart chỉ đọc kết quả sau build |
| BI production nhiều người            | Chưa quyết định | Cần đánh giá Cloud hoặc phương án host/export riêng         |

Khi chạy `dct` trên host, profile hiện tại cần các biến:

```bash
WAREHOUSE_POSTGRES_HOST=localhost
WAREHOUSE_POSTGRES_PORT=15433
WAREHOUSE_DB=japan_warehouse
PIPELINE_POSTGRES_USER=...
PIPELINE_POSTGRES_PASSWORD=...
```

Không dùng hostname `warehouse-postgres` trên host vì đó là DNS nội bộ của Docker
Compose. `target/manifest.json` do dbt Core tạo phải tồn tại trong `analytics/dbt`;
các lệnh dbt trong container bind-mount thư mục này nên artifact có thể dùng lại
ở host.

### 8.2. Board nên làm đầu tiên

#### A. `rental_market_overview.yml`

Nguồn chính: `rental_market_price_summary` và `rental_listing_latest`.

- KPI: latest listing, rent coverage, median rent, median rent/m²;
- bar: median rent theo ward, kèm sample size;
- interval/range hoặc table: P25–median–P75 theo ward;
- bar: listing count theo layout/area band;
- filter: ward, locality, layout, area band, building type.

Query từ summary phải cố định đúng một `market_level`. Nếu filter không khớp
grain đã tổng hợp, query lại `rental_listing_latest` thay vì cộng median cũ.

#### B. `rental_comparable_benchmark.yml`

Nguồn chính: `rental_listing_comparable_benchmark`.

- KPI số listing đủ peer sample;
- stacked/normalized bar cho `rent_position`;
- table chi tiết listing, rent, peer median, chênh lệch và peer tier;
- filter theo ward, locality, layout, area band và building type;
- conditional formatting để làm rõ listing thấp/cao hơn benchmark.

Board phải ghi chú rõ benchmark có bao gồm chính listing đang đánh giá và không
được diễn giải thành kết luận “hời”.

#### C. `rental_feature_pricing.yml`

Nguồn chính: `rental_feature_price_summary`.

- chọn `feature_group`;
- bar/dot plot của median rent hoặc median rent/m² theo `feature_value`;
- hiển thị sample size và coverage;
- chỉ dùng nhóm `has_reliable_rent_sample = true` trong chart kết luận;
- table phụ cho các nhóm chưa đủ mẫu để người đọc thấy giới hạn dữ liệu.

Đây là mô tả mối liên hệ sau khi giữ locality/layout/area band theo grain của
model, không phải quan hệ nhân quả.

#### D. `rental_data_quality.yml`

Nguồn chính: `rental_listing_latest`, `rental_price_mart_rejects` và dimension
quality.

- coverage của rent, area, address, building year, layout;
- phân bố `record_origin` giữa seed và operational;
- reject count theo lý do;
- bảng các nhóm có sample thấp hoặc parse partial.

#### E. Station board ở giai đoạn sau

Station là quan hệ một-nhiều qua `bridge_observation_station_access`. Khi nối
bridge vào fact/latest listing, một listing xuất hiện nhiều lần. Chart station
phải dùng `count(distinct observation_key)` hoặc một analytics model station đã
aggregate đúng grain. Không cộng rent/listing count sau join như thể mỗi row là
một listing.

## 9. Đề xuất áp dụng

Nên dùng dbt Charts cho **pilot local** của project này. Lý do chính là dữ liệu
đã có mart/analytics rõ grain, PostgreSQL được hỗ trợ, và workflow Git/YAML phù
hợp với cách project đang phát triển.

Trình tự triển khai:

1. pin dbt Core 1.11.15, dbt-postgres 1.11.0 và dbt Charts 0.8.0;
2. chạy lại toàn bộ dbt build/test và xác nhận output/grain không đổi;
3. thêm `dbt_charts.yml`, `charts/meta.yml` và Make target local;
4. validate structure, query và render bằng dữ liệu local;
5. duy trì năm board market, comparable, feature, station và quality;
6. sau khi người dùng thử local, mới chọn giữa dbt Charts Cloud và phương án
   tự host/export cho môi trường chia sẻ.

Không nên đưa Cloud hoặc server public vào bước đầu. Trước hết cần xác nhận ba
điểm bằng code thật: dbt Core mới build project PostgreSQL không đổi kết quả,
format/locale tiếng Nhật hiển thị đúng, và các filter không phá grain/percentile
của model analytics.

## 10. Nguồn chính thức

- [Quickstart for dbt Charts trên docs.getdbt.com](https://docs.getdbt.com/guides/dbt-charts)
- [dbt Docs](https://docs.getdbt.com/reference/commands/cmd-docs)
- [dbt Charts overview](https://docs.dbtcharts.com/)
- [Repository dbt-labs/dbt-charts](https://github.com/dbt-labs/dbt-charts)
- [Installation and setup](https://docs.dbtcharts.com/guides/installation/)
- [Sources and read-only posture](https://docs.dbtcharts.com/sources/)
- [Queries, filters and query composition](https://docs.dbtcharts.com/queries/)
- [Charts and chart types](https://docs.dbtcharts.com/charts/)
- [Variables and interactive filters](https://docs.dbtcharts.com/variables/)
- [dbt Charts Cloud](https://docs.dbtcharts.com/cloud/)
- [Official FAQ](https://docs.dbtcharts.com/faq/)
- [Current hosted pricing](https://dbtcharts.com/pricing/)
- [PyPI package `dbt-charts`](https://pypi.org/project/dbt-charts/)
