Có một cách học dbt dễ bị lệch: học `dbt run`, `ref()`, YAML, macro… như một tập hợp syntax. Cách đúng hơn với Data Engineer là hiểu **dbt đang giải quyết vấn đề gì trong kiến trúc ELT**, rồi mới học từng feature. Mình đã đối chiếu tài liệu dbt chính thức hiện tại, best practices của dbt Labs, hướng dẫn triển khai thực tế của GitLab Data Team và một số thảo luận từ cộng đồng Data Engineering. Điểm chung rất rõ: **dbt không đơn giản là “tool chạy SQL”; nó là framework để biến tầng transformation trong warehouse thành một software project có dependency, testing, documentation, version control và deployment workflow.** ([docs.getdbt.com](https://docs.getdbt.com/docs/introduction))

# 1. Trước hết: dbt nằm ở đâu trong Data Engineering?

Hãy nhìn pipeline truyền thống:

```text
Source
  │
  ├── Website / API
  ├── PostgreSQL / MySQL
  ├── SaaS
  └── Files
       │
       ▼
     Extract
       │
       ▼
     Transform
       │
       ▼
      Load
       │
       ▼
 Data Warehouse
```

Đây là **ETL**.

Trong modern data stack, thường chuyển thành:

```text
Source
   │
   │ Extract
   ▼
Ingestion
   │
   │ Load RAW
   ▼
┌───────────────────────────────┐
│         DATA WAREHOUSE        │
│                               │
│   raw                         │
│    │                          │
│    ▼                          │
│   staging                     │
│    │                          │
│    ▼                          │
│   intermediate               │
│    │                          │
│    ▼                          │
│   marts                       │
│                               │
└───────────────────────────────┘
         ▲
         │
        dbt
```

Đây là **ELT: Extract → Load → Transform**. Raw data được load vào warehouse trước, sau đó transformation chạy bằng compute engine của warehouse. dbt được thiết kế chính xác cho phần **T** này. ([getdbt.com](https://www.getdbt.com/blog/etl-vs-elt?utm_source=chatgpt.com))

![Image](https://www.getdbt.com/_next/image?q=75&url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fwl0ndo6t%2Fmain%2F3330189316953615f2c171496521aef3988ea084-1600x934.jpg%3Ffit%3Dmax%26auto%3Dformat&w=3840)

![Image](https://www.getdbt.com/_next/image?q=75&url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fwl0ndo6t%2Fmain%2F77067e8f50e89e4f32e115de8e930a11fbcf97e5-2560x1249.jpg%3Ffit%3Dmax%26auto%3Dformat&w=3840)

![Image](https://docs.getdbt.com/img/docs/terms/dag/mini_dag.png)

Điều này dẫn tới một kết luận rất quan trọng:

```text
dbt ≠ ingestion tool
dbt ≠ database
dbt ≠ data warehouse
dbt ≠ Airflow

dbt = transformation framework
      chạy transformation trong warehouse
```

Ví dụ pipeline crawl dữ liệu bất động sản:

```text
SUUMO
  │
  ▼
Crawler Python
  │
  ├── raw HTML -> MinIO
  │
  └── parsed records
          │
          ▼
     PostgreSQL / DW
          │
          │ raw.suumo_rental_raw
          ▼
         dbt
          │
          ├── staging
          ├── deduplicate
          ├── normalize
          ├── joins
          ├── dimensions
          ├── facts
          └── marts
          │
          ▼
    Analytics-ready DW
```

Ở đây **crawler/load pipeline kết thúc khi dữ liệu raw đã vào warehouse**. dbt bắt đầu từ đó.

---

# 2. Vậy nếu không có dbt thì chúng ta làm gì?

Giả sử warehouse có:

```text
raw.orders
raw.customers
raw.products
```

Bạn muốn tạo:

```text
analytics.customer_orders
```

Cách truyền thống có thể viết script:

```sql
DROP TABLE IF EXISTS analytics.customer_orders;

CREATE TABLE analytics.customer_orders AS
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS total_orders,
    SUM(o.amount) AS total_amount
FROM raw.customers c
LEFT JOIN raw.orders o
    ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id,
    c.name;
```

Sau đó cron:

```text
01_transform_orders.sql
02_transform_customer.sql
03_build_customer_orders.sql
04_build_daily_revenue.sql
...
```

Lúc đầu chưa có vấn đề.

Nhưng vài tháng sau:

```text
300 SQL files

01_x.sql
02_y.sql
03_fix_x.sql
03_fix_x_v2.sql
final_customer.sql
final_customer_new.sql
really_final_customer.sql
```

Và bắt đầu xuất hiện câu hỏi:

```text
customer_orders phụ thuộc table nào?

Nếu sửa orders thì dashboard nào bị ảnh hưởng?

Script nào phải chạy trước?

Nếu một script fail thì sao?

customer_id có duplicate không?

Column này có thể NULL không?

Logic total_revenue ở đâu?

Ai sửa query này?

Tại sao dashboard A và B tính revenue khác nhau?
```

dbt được sinh ra chủ yếu để giải quyết **complexity của transformation layer** này.

---

# 3. Bản chất cốt lõi của dbt: Model

Đây là khái niệm quan trọng nhất.

Trong dbt:

> **Một model về cơ bản là một `SELECT` statement được lưu trong một file SQL.**

Official docs mô tả SQL model là một `select` statement; khi chạy, dbt sẽ tự wrap nó bằng DDL/DML thích hợp để tạo table/view trong warehouse. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/sql-models))

Ví dụ:

```text
models/
└── customers.sql
```

```sql
select
    customer_id,
    first_name,
    last_name
from raw.customers
```

Bạn không cần viết:

```sql
DROP TABLE ...

CREATE TABLE ...

INSERT INTO ...

ALTER TABLE ...
```

Bạn chỉ khai báo:

```sql
select ...
```

dbt quyết định cách materialize nó.

Ví dụ nếu model được cấu hình:

```sql
{{ config(materialized='table') }}

select
    customer_id,
    first_name,
    last_name
from raw.customers
```

thì về ý tưởng dbt compile thành:

```sql
create table analytics.customers as (
    select
        customer_id,
        first_name,
        last_name
    from raw.customers
);
```

Điều này là một thay đổi tư duy khá lớn.

Trong ETL imperative, bạn nói:

```text
1. Drop table
2. Create table
3. Insert
4. Update
```

Trong dbt, bạn chủ yếu nói:

```text
Đây là dataset tôi muốn có.
```

Ví dụ:

```sql
select ...
```

rồi dbt lo việc **làm thế nào để tạo ra dataset đó**.

Đây là declarative approach.

---

# 4. dbt thực sự làm gì khi chạy?

Một mental model rất hữu ích:

```text
dbt project
     │
     ▼
Parse
     │
     ▼
Discover models
     │
     ▼
Discover ref() / source()
     │
     ▼
Construct DAG
     │
     ▼
Compile Jinja -> SQL
     │
     ▼
Determine execution order
     │
     ▼
Generate DDL / DML
     │
     ▼
Send SQL to Warehouse
     │
     ▼
Warehouse executes SQL
```

Điểm đặc biệt là:

> **dbt không lấy toàn bộ data về máy chạy dbt để transform.**

SQL vẫn chạy trong warehouse của bạn. Official docs nhấn mạnh models sử dụng SQL dialect của warehouse và data được xử lý trong chính warehouse. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/sql-models))

Ví dụ:

```text
Laptop / Airflow / dbt server

       dbt
        │
        │ SQL
        ▼
┌─────────────────────────┐
│       PostgreSQL        │
│                         │
│ SELECT                  │
│ JOIN                    │
│ GROUP BY                │
│ WINDOW FUNCTION         │
│ CREATE TABLE            │
│ MERGE                   │
│                         │
└─────────────────────────┘
```

dbt là **control + transformation logic layer**, còn compute chủ yếu là warehouse.

---

# 5. `ref()` — feature quan trọng bậc nhất của dbt

Giả sử:

```text
stg_customers
stg_orders
customer_orders
```

Thay vì:

```sql
select *
from analytics.stg_orders
```

dbt muốn bạn viết:

```sql
select *
from {{ ref('stg_orders') }}
```

Một dòng này làm **hai việc**.

Thứ nhất, dbt compile nó thành tên table/view thật:

```sql
select *
from dev_nicholas.stg_orders
```

hoặc production:

```sql
select *
from analytics.stg_orders
```

Thứ hai, quan trọng hơn nhiều:

```text
ref('stg_orders')
```

nói với dbt rằng:

```text
customer_orders DEPENDS ON stg_orders
```

Từ đó dbt tạo DAG. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/sql-models))

Ví dụ:

```text
raw.customers
      │
      ▼
stg_customers
      │
      │
      ├────────────┐
      │            │
raw.orders         │
      │            │
      ▼            │
stg_orders         │
      │            │
      └──────┬─────┘
             ▼
        int_orders
             │
             ▼
        fct_orders
             │
             ▼
      mart_customers
```

Đây chính là **data lineage**.

Không còn:

```text
01.sql
02.sql
03.sql
```

để biểu diễn thứ tự.

Dependency trong code tự quyết định thứ tự.

Nếu:

```sql
{{ ref('stg_orders') }}
```

thì dbt biết:

```text
stg_orders
    ↓
current model
```

Official docs nói `ref()` chính là thứ dbt dùng để xây DAG và xác định thứ tự thực thi. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/sql-models))

---

# 6. `source()` — điểm bắt đầu của DAG

Raw table không phải model của dbt.

Ví dụ warehouse đã có:

```text
raw.suumo_rental_raw
```

Table này được crawler/loader tạo.

Ta khai báo với dbt:

```yaml
sources:
  - name: suumo
    schema: raw

    tables:
      - name: suumo_rental_raw
```

Sau đó staging model:

```sql
select *
from {{ source('suumo', 'suumo_rental_raw') }}
```

Conceptually:

```text
external pipeline
      │
      ▼
raw.suumo_rental_raw
      │
    source()
      │
      ▼
stg_suumo__rental_listings
      │
     ref()
      ▼
int_...
      │
     ref()
      ▼
fct_...
```

Sự khác biệt:

```text
source()
    =
table do hệ thống bên ngoài dbt cung cấp

ref()
    =
resource/model được quản lý trong dbt DAG
```

Đây là distinction bạn nên thuộc rất chắc.

---

# 7. Kiến trúc transformation chuẩn: Staging → Intermediate → Marts

dbt Labs hiện vẫn khuyến nghị tư duy dữ liệu đi từ:

```text
source-conformed
        ↓
business-conformed
```

với ba lớp phổ biến:

```text
STAGING
   ↓
INTERMEDIATE
   ↓
MARTS
```

([docs.getdbt.com](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview))

Đây không phải luật bắt buộc của dbt. dbt không ép folder này. Đây là **data modeling convention**.

## Staging

Ví dụ raw:

```text
raw.suumo_rental_raw
```

có:

```text
id
rent
management_fee
area
station
created_at
```

Tạo:

```text
stg_suumo__rental_listings.sql
```

```sql
with source as (

    select *
    from {{ source('suumo', 'suumo_rental_raw') }}

),

renamed as (

    select
        id                           as listing_id,
        rent::numeric                as rent_yen,
        management_fee::numeric     as management_fee_yen,
        area::numeric                as area_m2,
        trim(station)                as station_name,
        created_at::timestamp        as fetched_at

    from source

)

select *
from renamed
```

Staging chủ yếu làm:

```text
rename
cast
standardize
basic cleanup
basic derived columns
```

Và thông thường **không nên join hay aggregate ở đây**, vì mục đích staging là tạo một representation sạch, nhất quán của từng source table. dbt Labs cũng khuyến nghị staging gần như quan hệ 1:1 với source table và thường materialize thành views. ([docs.getdbt.com](https://docs.getdbt.com/best-practices/how-we-structure/2-staging))

Mental model:

```text
RAW
Japanese field names
dirty types
weird nulls
source semantics

        ↓

STAGING

clean names
clean types
consistent conventions
```

---

# 8. Intermediate layer

Đây mới là nơi transformation bắt đầu thú vị.

Ví dụ:

```text
stg_suumo__rental_listings
stg_suumo__stations
stg_suumo__properties
```

Bạn cần:

```text
deduplicate listing
normalize station
join property
calculate rent_per_m2
```

Có thể tạo:

```text
int_rental_listings_deduplicated.sql

int_rental_listings_joined_stations.sql

int_rental_listings_enriched.sql
```

Ví dụ:

```sql
with listings as (

    select *
    from {{ ref('stg_suumo__rental_listings') }}

),

ranked as (

    select
        *,
        row_number() over (
            partition by listing_id
            order by fetched_at desc
        ) as row_num

    from listings

)

select *
from ranked
where row_num = 1
```

Intermediate là nơi phù hợp cho:

```text
join
pivot
deduplicate
complex calculation
re-graining
window functions
business transformations
```

dbt Labs mô tả intermediate models là các bước transformation có một mục đích rõ ràng để chuẩn bị dữ liệu cho marts; đây cũng thường là nơi tách logic phức tạp để mart cuối cùng dễ đọc và dễ test hơn. ([docs.getdbt.com](https://docs.getdbt.com/best-practices/how-we-structure/3-intermediate))

---

# 9. Mart layer

Mart là dữ liệu **business-facing**.

Ví dụ:

```text
dim_property
dim_station
fct_listing_observations
mart_tokyo_rental_market
```

Có thể theo Kimball:

```text
         dim_station
              │
              │
dim_property ─┼─ fct_listing
              │
              │
         dim_date
```

Hoặc wide table:

```text
mart_rental_listings
```

```text
listing_id
property_name
station_name
distance_to_station
rent_yen
management_fee
total_monthly_cost
area_m2
rent_per_m2
layout
building_age
...
```

Mart là thứ BI/dashboard/data scientist/application nên dùng.

Không nên để dashboard viết:

```sql
select ...
from raw.suumo_rental_raw
join raw.x
join raw.y
...
```

mà:

```sql
select *
from analytics.mart_rental_listings
```

Tức là business logic được centralize trong transformation layer.

---

# 10. Một dbt project thực tế sẽ trông như thế nào?

Ví dụ:

```text
suumo_dbt/
│
├── dbt_project.yml
│
├── packages.yml
│
│
├── models/
│   │
│   ├── staging/
│   │   └── suumo/
│   │       ├── _suumo__sources.yml
│   │       ├── stg_suumo__rental_listings.sql
│   │       ├── stg_suumo__stations.sql
│   │       └── stg_suumo__properties.sql
│   │
│   ├── intermediate/
│   │   ├── int_rental_listings_deduplicated.sql
│   │   ├── int_rental_listings_enriched.sql
│   │   └── int_property_station.sql
│   │
│   └── marts/
│       ├── core/
│       │   ├── dim_property.sql
│       │   ├── dim_station.sql
│       │   └── fct_listing_observations.sql
│       │
│       └── analytics/
│           └── mart_rental_market.sql
│
├── macros/
│   └── normalize_price.sql
│
├── tests/
│
├── snapshots/
│
└── seeds/
```

Điều quan trọng không phải tên folder chính xác.

Điều quan trọng là nhìn vào tree phải hiểu được:

```text
source
   ↓
clean
   ↓
transform
   ↓
business model
```

---

# 11. Materialization — model SQL cuối cùng trở thành cái gì?

Một model:

```sql
select ...
```

có thể trở thành nhiều loại database object khác nhau.

dbt hiện có các built-in materializations như `view`, `table`, `incremental`, `ephemeral` và `materialized_view`. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/sql-models))

| Materialization | Warehouse tạo gì | Dùng khi |
|---|---|---|
| `view` | SQL View | model nhẹ, staging |
| `table` | physical table | query nhiều, transformation nặng |
| `incremental` | table cập nhật từng phần | dataset lớn |
| `ephemeral` | không tạo relation riêng | helper/intermediate nhỏ |
| `materialized_view` | warehouse materialized view | tùy database/use case |

Một nguyên tắc thực dụng dbt Labs đưa ra là:

```text
Start with VIEW

      ↓ nếu query chậm

TABLE

      ↓ nếu build table quá lâu

INCREMENTAL
```

([docs.getdbt.com](https://docs.getdbt.com/best-practices/materializations/1-guide-overview))

Đây là nguyên tắc rất hay vì nhiều người vừa học dbt đã:

```text
incremental everything
```

và tự làm project phức tạp hơn mức cần thiết.

---

# 12. Incremental — cực kỳ quan trọng với Data Engineer

Giả sử:

```text
raw.events = 2 tỷ records
```

Bạn không muốn mỗi ngày:

```sql
select *
from raw.events
```

xử lý lại 2 tỷ records.

Ta dùng:

```sql
{{
    config(
        materialized='incremental',
        unique_key='event_id'
    )
}}

select
    event_id,
    user_id,
    event_time
from {{ source('app', 'events') }}

{% if is_incremental() %}

where event_time >= (
    select max(event_time)
    from {{ this }}
)

{% endif %}
```

Lần đầu:

```text
table chưa tồn tại

is_incremental() = false
```

→ process toàn bộ.

Sau đó:

```text
table tồn tại

is_incremental() = true
```

→ chỉ query data mới/thay đổi.

Official docs mô tả `is_incremental()` chỉ true khi model đã tồn tại dạng table, model được cấu hình incremental và không chạy `--full-refresh`. Với records update, `unique_key` rất quan trọng để tránh tạo duplicate. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/incremental-models))

Nhưng đây là điều rất dễ hiểu sai:

> **Incremental ≠ CDC.**

dbt không tự nhiên biết record nào thay đổi.

Bạn phải có strategy, ví dụ:

```text
updated_at
created_at
ingested_at
CDC log
partition
batch_id
```

và viết filter đúng.

Một production pattern tốt hơn thường có lookback:

```sql
where updated_at >= (
    select max(updated_at) - interval '3 day'
    from {{ this }}
)
```

Vì nếu record đến trễ:

```text
Ngày 1:
updated_at = 2026-08-01

Nhưng ingestion fail.

Ngày 3:
record mới tới warehouse.
```

Nếu chỉ:

```sql
updated_at > max(updated_at)
```

record đó có thể bị bỏ qua.

Đây là kiểu vấn đề Data Engineer phải suy nghĩ; dbt không thể giải quyết thay bạn.

---

# 13. Snapshot và Incremental hoàn toàn khác nhau

Đây là chỗ người mới học rất hay nhầm.

**Incremental** trả lời:

```text
Làm thế nào build table hiệu quả,
không phải process toàn bộ data?
```

**Snapshot** trả lời:

```text
Làm thế nào lưu lịch sử thay đổi
của dữ liệu mutable?
```

Ví dụ source hôm nay:

```text
listing_id | rent
-----------+--------
101        | 80,000
```

Ngày mai source bị overwrite:

```text
101 | 75,000
```

Nếu chỉ đọc current source:

```text
80,000 biến mất.
```

Snapshot có thể lưu:

```text
listing_id | rent   | valid_from | valid_to
-----------+--------+------------+----------
101        | 80000  | Aug 01     | Aug 06
101        | 75000  | Aug 06     | null
```

Đây chính là **SCD Type 2**. Official dbt docs định nghĩa snapshots là cơ chế implement Type-2 Slowly Changing Dimensions trên mutable source tables. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/snapshots))

Với dữ liệu bất động sản, snapshot có thể rất hữu ích để trả lời:

```text
Giá căn hộ này thay đổi thế nào?

Listing tồn tại từ khi nào tới khi nào?

Có giảm giá không?

Một listing được remove khi nào?
```

---

# 14. Testing — lý do dbt khác rất nhiều so với “folder SQL scripts”

Ví dụ model:

```text
dim_property
```

Bạn nghĩ:

```text
property_id phải unique.
property_id không được NULL.
```

Khai báo:

```yaml
models:

  - name: dim_property

    columns:

      - name: property_id

        data_tests:
          - unique
          - not_null
```

Chạy:

```bash
dbt test
```

dbt thực chất sẽ generate SQL tìm các record vi phạm.

Ví dụ `not_null` về bản chất giống:

```sql
select *
from dim_property
where property_id is null
```

Nếu:

```text
0 rows
```

→ PASS.

Nếu:

```text
15 rows
```

→ FAIL.

Official docs mô tả chính xác data test theo kiểu này: test query tìm những record vi phạm assertion; trả về zero failing rows thì test pass. dbt cung cấp sẵn `unique`, `not_null`, `accepted_values` và `relationships`. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/data-tests))

Ví dụ:

```yaml
- name: listings

  columns:

    - name: listing_id
      data_tests:
        - unique
        - not_null

    - name: property_type
      data_tests:
        - accepted_values:
            arguments:
              values:
                - apartment
                - house

    - name: station_id
      data_tests:
        - relationships:
            arguments:
              to: ref('dim_station')
              field: station_id
```

Bây giờ transformation pipeline không còn là:

```text
SQL chạy thành công = dữ liệu đúng
```

mà:

```text
SQL chạy thành công
       +
data assumptions được validate
```

Đây là khác biệt rất lớn.

---

# 15. `dbt build` quan trọng hơn việc nhớ từng command riêng

Bạn sẽ gặp:

```bash
dbt run
dbt test
dbt snapshot
dbt seed
```

Nhưng command rất đáng nhớ là:

```bash
dbt build
```

Vì dbt build thực thi models, tests, snapshots, seeds và các resources liên quan theo **DAG order**. ([docs.getdbt.com](https://docs.getdbt.com/reference/commands/build))

Tức là:

```text
source

 ↓

model A

 ↓

test A

 ↓

model B

 ↓

test B

 ↓

model C
```

Nếu dependency upstream fail, downstream có thể không được build.

Đó mới là một data pipeline đúng nghĩa.

---

# 16. Source freshness

Một vấn đề Data Engineer thường gặp:

```text
dbt chạy 08:00

nhưng crawler/load job từ 07:00 đã fail.
```

Nếu không biết:

```text
dbt transformation vẫn chạy
        ↓
dashboard trông bình thường
        ↓
nhưng data là của hôm qua
```

dbt cho phép định nghĩa freshness:

```yaml
sources:

  - name: suumo

    config:

      loaded_at_field: loaded_at

      freshness:
        warn_after:
          count: 2
          period: hour

        error_after:
          count: 6
          period: hour
```

Sau đó:

```bash
dbt source freshness
```

dbt kiểm tra timestamp mới nhất của source.

Ví dụ:

```text
latest loaded_at = 10:00

now = 11:00

lag = 1 hour

PASS
```

hoặc:

```text
latest = 01:00

now = 11:00

lag = 10 hours

ERROR
```

dbt docs hiện khuyến nghị freshness khi muốn theo dõi SLA nguồn và có thể dùng `warn_after` / `error_after`. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/sources))

Đây là cầu nối rất hay giữa:

```text
INGESTION
    ↓
TRANSFORMATION
```

---

# 17. Jinja — tại sao SQL trong dbt có `{{ }}`?

dbt SQL không hoàn toàn là SQL.

Nó là:

```text
SQL
+
Jinja templating
```

Ví dụ:

```sql
select *
from {{ ref('stg_orders') }}
```

Trước khi warehouse thấy câu SQL, dbt compile Jinja.

```text
Input
─────────────────────────

select *
from {{ ref('stg_orders') }}


          ↓ dbt compile


Output
─────────────────────────

select *
from analytics.stg_orders
```

Một điều rất quan trọng:

> Jinja chủ yếu chạy ở **compile time**, không phải chạy cho từng row giống SQL.

---

# 18. Macro = function tạo SQL

Bạn thấy logic này 20 lần:

```sql
rent_yen / 10000.0
```

Có thể tạo:

```text
macros/
└── yen_to_man.sql
```

```sql
{% macro yen_to_man(column_name) %}

    ({{ column_name }} / 10000.0)

{% endmacro %}
```

Sau đó:

```sql
select
    {{ yen_to_man('rent_yen') }} as rent_man
from ...
```

Compile thành:

```sql
select
    (rent_yen / 10000.0) as rent_man
from ...
```

Macros giống function trong programming language ở chỗ giúp reuse code, nhưng chúng thường **generate SQL**. Official dbt docs cũng mô tả macro như reusable code tương tự functions và compile chúng thành SQL. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/jinja-macros))

Tuy nhiên có một lời khuyên rất đáng nhớ:

```text
Don't turn everything into macros.
```

dbt Labs hiện còn khuyến nghị **ưu tiên readability hơn DRY tuyệt đối** khi dùng Jinja, bởi abstraction quá mạnh sẽ làm SQL khó debug. ([docs.getdbt.com](https://docs.getdbt.com/docs/build/jinja-macros))

Ví dụ này:

```sql
select
    order_id,
    customer_id,
    amount
from {{ ref('stg_orders') }}
```

rất dễ hiểu.

Đừng biến nó thành:

```sql
{{ create_super_dynamic_model(
    entity='order',
    dims=get_dims(...),
    fields=get_fields(...),
    filters=...
) }}
```

chỉ vì có thể làm được.

---

# 19. dbt không thay thế data modeling

Đây là điều mình muốn nhấn mạnh đặc biệt nếu bạn học theo hướng Data Engineer.

dbt có thể giúp bạn:

```text
build
dependency
testing
documentation
lineage
deployment
incremental processing
```

Nhưng dbt **không quyết định giúp bạn**:

```text
grain của fact table là gì?

natural key là gì?

surrogate key có cần không?

dimension nào nên SCD2?

fact transaction hay periodic snapshot?

join này có fanout không?

one-to-many hay many-to-many?

duplicate là bug hay business behavior?

late arriving dimension xử lý sao?
```

Ví dụ:

```text
fct_listing_observations
```

Bạn phải định nghĩa grain trước:

> Một row = một listing được quan sát trong một lần crawl.

Hay:

> Một row = current state của một listing.

Hai definition này sẽ tạo ra hai warehouse hoàn toàn khác nhau.

dbt chỉ giúp bạn **implement và maintain model đó tốt hơn**.

---

# 20. dbt và Airflow khác nhau ở đâu?

Một kiến trúc Data Engineer rất phổ biến:

```text
                AIRFLOW
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼

    Crawl        Load         dbt

     │            │            │
     ▼            ▼            ▼

Website ──► Landing DW ──► Transform
```

Airflow điều phối:

```text
task A
    ↓
task B
    ↓
task C
```

giữa nhiều hệ thống.

dbt điều phối dependency **bên trong transformation graph**:

```text
stg_a ─┐
       ├── int_ab ── fct_x
stg_b ─┘
```

Vì thế một architecture tốt thường là:

```text
Airflow

crawl_suumo
      ↓
parse_data
      ↓
load_warehouse
      ↓
run_dbt
      ↓
publish / notify
```

Chứ không nên bắt Airflow biết từng model:

```text
Airflow task: stg_orders
Airflow task: stg_customer
Airflow task: int_orders
Airflow task: dim_customer
Airflow task: fct_orders
...
```

Vì lúc đó bạn duplicate DAG:

```text
Airflow DAG
+
dbt DAG
```

dbt Labs cũng khuyến nghị khi kết hợp Airflow và dbt, thường nên để một dbt job chứa nhiều model càng thực tế càng tốt, vì chính dbt đã quản lý dependency và parallel execution giữa models. ([docs.getdbt.com](https://docs.getdbt.com/guides/airflow-and-dbt-cloud?step=1))

---

# 21. Một flow production tương đối chuẩn

Với crawler/data warehouse, mình sẽ hình dung:

```text
┌───────────────┐
│   Scheduler   │
│   / Airflow   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Crawl SUUMO   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Raw snapshot  │
│    MinIO      │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Parse / Load  │
│    raw DW     │
└───────┬───────┘
        │
        ▼
  source freshness
        │
        ▼
┌────────────────────┐
│     dbt build      │
│                    │
│ source             │
│   ↓                │
│ staging            │
│   ↓                │
│ intermediate       │
│   ↓                │
│ dimensions/facts   │
│   ↓                │
│ marts              │
│                    │
│ + tests            │
└──────────┬─────────┘
           │
           ▼
┌────────────────────┐
│ Analytics-ready DW │
└──────────┬─────────┘
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
     BI   ML    API
```

Đây mới là chỗ dbt trở thành **tool Data Engineering**, chứ không chỉ là tool analyst viết SQL.

---

# 22. Tại sao Data Engineer nên dùng dbt thay vì Python transform?

Không phải lúc nào cũng nên.

Ví dụ transformation:

```text
join
filter
aggregate
window function
type casting
dedupe
business metrics
dimension/fact construction
```

thì warehouse SQL thường cực kỳ phù hợp.

Ví dụ:

```sql
select
    station_id,
    date_trunc('month', fetched_at) as month,
    avg(rent_yen) as avg_rent,
    avg(rent_yen / area_m2) as avg_rent_per_m2
from {{ ref('fct_listing_observations') }}
group by
    station_id,
    date_trunc('month', fetched_at)
```

Không cần:

```text
Postgres
   ↓
download 100 GB
   ↓
pandas
   ↓
transform
   ↓
upload 100 GB
```

Warehouse vốn đã rất giỏi:

```text
scan
join
aggregate
sort
window
parallel execution
```

Đó là một trong những lý do ELT + dbt phát triển mạnh cùng cloud warehouses. ([getdbt.com](https://www.getdbt.com/blog/etl-tools-data-pipeline-architecture?utm_source=chatgpt.com))

Nhưng nếu là:

```text
image processing
web scraping
heavy ML
PDF parsing
API calls
complex Python libraries
raw file processing
```

thì đó thường không phải việc dbt SQL nên làm.

---

# 23. Điều làm dbt thực sự mạnh không phải SQL

Đây là chỗ cốt lõi nhất.

Bạn hoàn toàn có thể viết:

```sql
CREATE TABLE ...
```

không cần dbt.

Giá trị của dbt nằm ở lớp phía trên SQL:

```text
              SQL
               │
        ┌──────┴──────┐
        │             │
   Dependency       Testing
        │             │
      Lineage     Documentation
        │             │
      Git           CI/CD
        │             │
     Macros       Environments
        │             │
 Incremental     Data contracts
        │
        ▼
Reproducible transformation system
```

Nói cách khác:

> **dbt áp dụng software engineering principles vào analytics/transformation code.**

Đây cũng là định nghĩa mà tài liệu chính thức dùng: modularity, version control, testing, CI/CD và documentation trở thành một phần của analytics workflow. ([docs.getdbt.com](https://docs.getdbt.com/docs/introduction))

---

# 24. `dbt` thay đổi workflow của Data Engineer như thế nào?

Trước:

```text
Engineer

edit SQL
   ↓
SSH server
   ↓
run script
   ↓
hope nothing breaks
```

Sau:

```text
Engineer

Git branch
    ↓
edit model
    ↓
dbt build
    ↓
tests
    ↓
review DAG
    ↓
commit
    ↓
Pull Request
    ↓
CI
    ↓
merge
    ↓
production dbt build
```

Data transformation trở thành:

```text
code
```

thay vì:

```text
một trạng thái bí ẩn đang tồn tại trong database.
```

---

# 25. Một ví dụ hoàn chỉnh rất nhỏ

Source:

```text
raw.suumo_rental_raw
```

### Source definition

```yaml
sources:
  - name: suumo
    schema: raw

    tables:
      - name: suumo_rental_raw
```

### Staging

```sql
-- stg_suumo__rental_listings.sql

with source as (

    select *
    from {{ source('suumo', 'suumo_rental_raw') }}

),

cleaned as (

    select
        source_record_id as listing_id,

        rent_yen::numeric
            as rent_yen,

        management_fee_yen::numeric
            as management_fee_yen,

        area_m2::numeric
            as area_m2,

        fetched_at::timestamp
            as fetched_at

    from source

)

select *
from cleaned
```

### Intermediate

```sql
-- int_rental_listings_enriched.sql

with listings as (

    select *
    from {{ ref('stg_suumo__rental_listings') }}

)

select
    *,
    rent_yen
        + coalesce(management_fee_yen, 0)
        as monthly_cost_yen,

    rent_yen / nullif(area_m2, 0)
        as rent_per_m2

from listings
```

### Mart

```sql
-- fct_rental_listings.sql

{{
    config(
        materialized='table'
    )
}}

select
    listing_id,
    fetched_at,
    rent_yen,
    management_fee_yen,
    monthly_cost_yen,
    area_m2,
    rent_per_m2

from {{ ref('int_rental_listings_enriched') }}
```

### Tests

```yaml
models:

  - name: fct_rental_listings

    columns:

      - name: listing_id
        data_tests:
          - not_null

      - name: rent_yen
        data_tests:
          - not_null
```

DAG:

```text
raw.suumo_rental_raw
         │
         ▼
stg_suumo__rental_listings
         │
         ▼
int_rental_listings_enriched
         │
         ▼
fct_rental_listings
         │
         ▼
       tests
```

Đây chính là dbt ở dạng nhỏ nhất nhưng đã chứa mental model production.

---

# 26. Cách mình khuyên bạn học dbt

Đừng bắt đầu bằng macro hay Semantic Layer. Thứ tự học hiệu quả hơn là:

```text
ELT architecture
        ↓
dbt model
        ↓
source()
        ↓
ref()
        ↓
DAG / lineage
        ↓
staging
        ↓
intermediate
        ↓
marts
        ↓
materialization
        ↓
tests
        ↓
incremental
        ↓
snapshots
        ↓
Jinja / macros
        ↓
documentation
        ↓
Git + CI/CD
        ↓
Airflow / orchestration
        ↓
performance / production
```

Nếu sáu phần đầu hiểu rất chắc thì phần còn lại khá tự nhiên.

---

# 27. Các tài liệu mình khuyên đọc

| Tài liệu | Mức độ | Vì sao nên đọc |
|---|---|---|
| [What is dbt? — official docs](https://docs.getdbt.com/docs/introduction?utm_source=chatgpt.com) | Bắt đầu | Mental model chính thức, model/framework/engine |
| [SQL Models — official docs](https://docs.getdbt.com/docs/build/sql-models?utm_source=chatgpt.com) | Rất quan trọng | Hiểu model, compile, `ref()`, materialization |
| [How we structure our dbt projects](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview?utm_source=chatgpt.com) | **Phải đọc** | Staging → Intermediate → Marts và lý do thiết kế |
| [Materialization best practices](https://docs.getdbt.com/best-practices/materializations/1-guide-overview?utm_source=chatgpt.com) | Quan trọng | View/table/incremental và trade-off |
| [Data tests](https://docs.getdbt.com/docs/build/data-tests?utm_source=chatgpt.com) | Quan trọng | Data quality trong dbt |
| [Sources](https://docs.getdbt.com/docs/build/sources?utm_source=chatgpt.com) | Quan trọng | Raw source + freshness |
| [Incremental models](https://docs.getdbt.com/docs/build/incremental-models?utm_source=chatgpt.com) | Nâng cao | Cần cho warehouse lớn |
| [Snapshots](https://docs.getdbt.com/docs/build/snapshots?utm_source=chatgpt.com) | Nâng cao | SCD Type 2 |
| [Jinja and macros](https://docs.getdbt.com/docs/build/jinja-macros?utm_source=chatgpt.com) | Sau fundamentals | Reusable SQL, dynamic code |
| [GitLab Data Team dbt Guide](https://handbook.gitlab.com/handbook/enterprise-data/platform/dbt-guide/?utm_source=chatgpt.com) | **Rất đáng đọc** | Cách một công ty thật dùng dbt quy mô lớn |
| [What, exactly, is dbt?](https://www.getdbt.com/blog/what-exactly-is-dbt?utm_source=chatgpt.com) | Conceptual | Bài giải thích kinh điển về “tại sao dbt tồn tại” |

GitLab đặc biệt đáng đọc sau khi đã hiểu fundamentals. Họ công khai khá nhiều cách tổ chức transformation, style, development workflow và modeling thực tế; ngay cả cộng đồng Data Engineering cũng thường đề xuất project/guide của GitLab khi người học muốn chuyển từ tutorial sang production dbt. ([handbook.gitlab.com](https://handbook.gitlab.com/handbook/enterprise-data/platform/dbt-guide/?utm_source=chatgpt.com))

Một lưu ý về tài liệu hiện tại: dbt đang ở giai đoạn chuyển thế hệ engine. Official docs ngày 6/8/2026 mô tả **v2 là thế hệ hiện tại được khuyến nghị**, trong khi v1/Core Python vẫn được duy trì. Nhưng những khái niệm mình giải thích ở trên — model, `ref`, `source`, DAG, staging/intermediate/marts, tests, incremental, snapshots — là mental model nền tảng và không nên học phụ thuộc vào một version cụ thể. ([docs.getdbt.com](https://docs.getdbt.com/docs/introduction))

Nếu gắn thẳng vào pipeline Data Engineer hiện tại của bạn, kiến trúc hợp lý nhất sẽ là:

```text
Crawler
   ↓
MinIO raw snapshots
   ↓
Parser
   ↓
PostgreSQL landing/raw
   ↓
             ┌────────────────────────────┐
             │            dbt             │
             │                            │
             │ raw                        │
             │  ↓                         │
             │ staging                    │
             │  ↓                         │
             │ intermediate               │
             │  ↓                         │
             │ dim / fact                 │
             │  ↓                         │
             │ marts                      │
             └─────────────┬──────────────┘
                           ↓
                     Data Warehouse
```

Tức là **dbt chính là phần còn thiếu giữa dữ liệu crawler đã ingest và một warehouse được modeling tử tế**. Đây cũng là một project rất đẹp để học dbt vì bạn có dữ liệu thật, duplicate thật, lịch sử thay đổi listing thật, incremental thật và bài toán dimensional modeling thật — không phải chỉ Jaffle Shop tutorial.
