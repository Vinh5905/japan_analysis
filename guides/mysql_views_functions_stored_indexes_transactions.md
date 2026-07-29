# MySQL cốt lõi: Views, Functions, Stored Routines, Indexes và Transactions

> Tài liệu này được viết theo hướng hiểu **bản chất**, **trường hợp sử dụng**, **chi phí đánh đổi** và **quy trình thiết kế thực tế**.  
> Các ví dụ giả định MySQL 8.x và storage engine InnoDB.

---

## Mục lục

1. [Tư duy tổng quan](#1-tư-duy-tổng-quan)
2. [Views](#2-views)
3. [Functions](#3-functions)
4. [Stored routines](#4-stored-routines)
5. [Indexes](#5-indexes)
6. [Transactions](#6-transactions)
7. [Cách các thành phần phối hợp với nhau](#7-cách-các-thành-phần-phối-hợp-với-nhau)
8. [Bảng quyết định nhanh](#8-bảng-quyết-định-nhanh)

---

# 1. Tư duy tổng quan

Năm khái niệm trong tài liệu này giải quyết năm nhóm vấn đề khác nhau:

| Thành phần | Câu hỏi nó giải quyết |
|---|---|
| `VIEW` | Làm sao đóng gói một câu `SELECT` phức tạp thành một lớp dữ liệu dễ dùng? |
| Function | Làm sao tái sử dụng một phép tính trả về một giá trị? |
| Stored procedure | Làm sao đóng gói một quy trình gồm nhiều câu SQL? |
| Index | Làm sao tìm đúng dữ liệu nhanh hơn mà không quét toàn bộ bảng? |
| Transaction | Làm sao bảo đảm nhiều thay đổi thành công hoặc thất bại cùng nhau? |

Cách nhớ ngắn:

```text
VIEW
= lưu công thức đọc dữ liệu

FUNCTION
= lưu phép tính trả về một giá trị

PROCEDURE
= lưu một quy trình thao tác dữ liệu

INDEX
= cấu trúc phụ giúp tìm dữ liệu nhanh

TRANSACTION
= ranh giới của một công việc dữ liệu hoàn chỉnh
```

---

# 2. Views

## 2.1. View là gì?

`VIEW` là một **bảng ảo được định nghĩa bằng một câu `SELECT` đã lưu trong database**.

Ví dụ:

```sql
CREATE VIEW completed_orders AS
SELECT
    o.order_id,
    o.customer_id,
    o.total_amount,
    o.created_at
FROM orders AS o
WHERE o.status = 'completed';
```

Sau đó sử dụng gần giống một bảng:

```sql
SELECT *
FROM completed_orders;
```

Cách hiểu đúng:

```text
VIEW không phải bản sao của dữ liệu.

VIEW là tên gọi của một công thức SELECT.
```

---

## 2.2. Bản chất MySQL lưu gì?

Với view thông thường, MySQL chủ yếu lưu:

- tên view;
- câu `SELECT` định nghĩa view;
- danh sách cột;
- database chứa view;
- quyền và thông tin bảo mật;
- metadata liên quan đến character set và collation.

MySQL **không lưu cố định các dòng kết quả** của view.

Ví dụ:

```sql
CREATE VIEW active_users AS
SELECT
    user_id,
    full_name,
    email
FROM users
WHERE status = 'active';
```

Có thể hình dung database lưu:

```text
Tên view: active_users

Định nghĩa:
SELECT user_id, full_name, email
FROM users
WHERE status = 'active'
```

Dữ liệu thật vẫn nằm trong bảng `users`.

Khi bảng nguồn thay đổi:

```sql
UPDATE users
SET status = 'active'
WHERE user_id = 10;
```

thì lần tiếp theo chạy:

```sql
SELECT *
FROM active_users;
```

kết quả của view tự phản ánh dữ liệu mới.

Không cần sao chép lại dữ liệu và không cần refresh view thông thường.

---

## 2.3. View khác bảng thật như thế nào?

### Tạo một bảng sao chép

```sql
CREATE TABLE active_users_copy AS
SELECT *
FROM users
WHERE status = 'active';
```

`active_users_copy` là bảng thật, có dữ liệu riêng.

Nếu `users` thay đổi:

```text
users thay đổi
active_users_copy không tự thay đổi
```

### Tạo view

```sql
CREATE VIEW active_users AS
SELECT *
FROM users
WHERE status = 'active';
```

Nếu `users` thay đổi:

```text
users thay đổi
kết quả active_users thay đổi theo
```

So sánh:

| Đặc điểm | Table | View |
|---|---:|---:|
| Lưu dữ liệu vật lý riêng | Có | Không |
| Tự phản ánh bảng nguồn | Không | Có |
| Tạo index riêng | Có | Không |
| Dùng như nguồn trong `SELECT` | Có | Có |
| Có thể cập nhật trực tiếp | Có | Chỉ một số view |

---

## 2.4. `MERGE`, `TEMPTABLE` và `UNDEFINED`

Khi tạo view, MySQL có ba lựa chọn thuật toán:

```sql
CREATE ALGORITHM = MERGE VIEW ...
```

```sql
CREATE ALGORITHM = TEMPTABLE VIEW ...
```

```sql
CREATE ALGORITHM = UNDEFINED VIEW ...
```

Nếu không ghi `ALGORITHM`, có thể hiểu MySQL tự lựa chọn.

---

### 2.4.1. `MERGE`

Giả sử có view:

```sql
CREATE VIEW completed_orders AS
SELECT
    order_id,
    customer_id,
    total_amount
FROM orders
WHERE status = 'completed';
```

Truy vấn ngoài:

```sql
SELECT *
FROM completed_orders
WHERE customer_id = 100;
```

Với `MERGE`, MySQL có thể hiểu gần giống:

```sql
SELECT
    order_id,
    customer_id,
    total_amount
FROM orders
WHERE status = 'completed'
  AND customer_id = 100;
```

Điểm mạnh:

```text
View và truy vấn ngoài được nhìn như một bài toán chung.

Optimizer có thể:
- đẩy điều kiện xuống bảng gốc;
- chọn index dựa trên toàn bộ điều kiện;
- sắp xếp lại thứ tự JOIN;
- tránh đọc các dòng không cần thiết;
- tránh tạo bảng trung gian.
```

Có thể coi một view mergeable giống một “macro SQL”.

---

### 2.4.2. `TEMPTABLE`

Với cùng ví dụ, có thể hình dung MySQL làm:

```text
Bước 1:
Lấy toàn bộ completed order
→ tạo kết quả trung gian

Bước 2:
Từ kết quả trung gian
→ lọc customer_id = 100
```

Tương đương về ý tưởng:

```sql
CREATE TEMPORARY TABLE tmp_completed_orders AS
SELECT
    order_id,
    customer_id,
    total_amount
FROM orders
WHERE status = 'completed';

SELECT *
FROM tmp_completed_orders
WHERE customer_id = 100;
```

Đây chỉ là minh họa. Bảng tạm thật do MySQL tự quản lý.

Chi phí có thể gồm:

```text
Đọc bảng nguồn
→ ghi bảng tạm
→ đọc lại bảng tạm
→ lọc và JOIN tiếp
```

Nếu bảng tạm lớn, nó có thể gây thêm chi phí bộ nhớ hoặc disk.

---

### 2.4.3. Vì sao thường ưu tiên `MERGE`?

Vì `MERGE` thường:

- không cần materialize kết quả;
- không cần ghi rồi đọc lại bảng tạm;
- cho optimizer nhìn thấy toàn bộ các bảng và điều kiện;
- cho phép condition pushdown;
- dễ tận dụng composite index;
- có thể hỗ trợ view cập nhật được.

Ví dụ:

```sql
CREATE VIEW order_details AS
SELECT
    o.order_id,
    o.customer_id,
    oi.product_id,
    oi.quantity
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.order_id;
```

Truy vấn:

```sql
SELECT
    c.customer_name,
    od.product_id,
    od.quantity
FROM customers AS c
JOIN order_details AS od
    ON od.customer_id = c.customer_id
WHERE c.country = 'Vietnam';
```

Nếu merge được, optimizer có thể xem như:

```sql
SELECT
    c.customer_name,
    oi.product_id,
    oi.quantity
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.order_id
WHERE c.country = 'Vietnam';
```

Nó có thể chọn:

```text
Lọc customer ở Việt Nam trước
→ tìm order của họ
→ tìm order_items
```

Thay vì tạo toàn bộ `order_details` cho mọi quốc gia.

---

### 2.4.4. Khi nào view không merge được?

Các cấu trúc thường làm view phải materialize hoặc không merge trực tiếp được:

- `GROUP BY`;
- `HAVING`;
- `DISTINCT`;
- hàm tổng hợp như `SUM()`, `COUNT()`, `MAX()`;
- window function;
- `UNION` hoặc `UNION ALL`;
- `LIMIT`;
- một số subquery hoặc biểu thức phức tạp.

Ví dụ:

```sql
CREATE VIEW customer_order_summary AS
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY customer_id;
```

MySQL phải tính tổng hợp trước khi truy vấn ngoài sử dụng:

```sql
SELECT *
FROM customer_order_summary
WHERE total_spent > 10000000;
```

---

### 2.4.5. Nên chọn thuật toán nào?

Thông thường:

```text
Không ép thuật toán ngay từ đầu.

Dùng mặc định hoặc UNDEFINED
→ để optimizer chọn.
```

Chỉ ép `TEMPTABLE` hoặc `MERGE` khi:

- đã kiểm tra execution plan;
- có lý do rõ ràng;
- hiểu chi phí khóa, materialization và khả năng cập nhật;
- đã benchmark trên dữ liệu thực tế.

---

## 2.5. View có thể cập nhật được không?

Một số view đơn giản có thể `INSERT`, `UPDATE`, `DELETE`.

Ví dụ:

```sql
CREATE VIEW active_products AS
SELECT
    product_id,
    product_name,
    price,
    status
FROM products
WHERE status = 'active';
```

Có thể:

```sql
UPDATE active_products
SET price = 200000
WHERE product_id = 10;
```

Dữ liệu thật được cập nhật trong bảng `products`.

View thường cập nhật được khi mỗi dòng trong view ánh xạ rõ ràng đến đúng một dòng trong bảng nguồn.

Các cấu trúc thường khiến view không cập nhật được:

```text
GROUP BY
DISTINCT
SUM, COUNT, MAX...
HAVING
UNION
kết quả tổng hợp từ nhiều dòng
```

Ví dụ không cập nhật được:

```sql
CREATE VIEW customer_summary AS
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY customer_id;
```

Không thể xác định câu sau phải sửa những dòng nào trong `orders`:

```sql
UPDATE customer_summary
SET total_spent = 5000000
WHERE customer_id = 10;
```

---

## 2.6. `WITH CHECK OPTION`

View:

```sql
CREATE VIEW active_products AS
SELECT
    product_id,
    product_name,
    status
FROM products
WHERE status = 'active';
```

Nếu chạy:

```sql
UPDATE active_products
SET status = 'inactive'
WHERE product_id = 10;
```

dòng đó sẽ biến mất khỏi view.

Muốn ngăn việc cập nhật khiến dòng không còn thỏa điều kiện view:

```sql
CREATE VIEW active_products AS
SELECT
    product_id,
    product_name,
    status
FROM products
WHERE status = 'active'
WITH CHECK OPTION;
```

Khi đó MySQL từ chối thao tác làm dữ liệu không còn nằm trong phạm vi view.

---

## 2.7. Trường hợp sử dụng view

### 1. Tái sử dụng truy vấn phức tạp

```sql
CREATE VIEW completed_order_details AS
SELECT
    o.order_id,
    c.customer_name,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    oi.quantity * oi.unit_price AS line_total
FROM orders AS o
JOIN customers AS c
    ON c.customer_id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.order_id
JOIN products AS p
    ON p.product_id = oi.product_id
WHERE o.status = 'completed';
```

Sau đó:

```sql
SELECT *
FROM completed_order_details
WHERE line_total >= 1000000;
```

---

### 2. Chuẩn hóa logic nghiệp vụ dùng để đọc

```sql
CREATE VIEW valid_orders AS
SELECT *
FROM orders
WHERE payment_status = 'paid'
  AND order_status <> 'cancelled'
  AND total_amount > 0;
```

Mọi báo cáo dùng cùng định nghĩa “đơn hàng hợp lệ”.

---

### 3. Ẩn cột nhạy cảm

```sql
CREATE VIEW public_employees AS
SELECT
    employee_id,
    full_name,
    email
FROM employees;
```

Không đưa ra:

```text
salary
bank_account
password_hash
```

Sau đó chỉ cấp quyền đọc view.

---

### 4. Tạo lớp dữ liệu dễ dùng cho BI hoặc reporting

```sql
CREATE VIEW sales_report AS
SELECT
    o.order_id,
    o.created_at AS order_date,
    c.customer_name,
    p.product_name,
    oi.quantity,
    oi.quantity * oi.unit_price AS revenue
FROM orders AS o
JOIN customers AS c
    ON c.customer_id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.order_id
JOIN products AS p
    ON p.product_id = oi.product_id;
```

---

### 5. Tạo lớp tương thích cho hệ thống cũ

```sql
CREATE VIEW legacy_customers AS
SELECT
    customer_id,
    CONCAT(first_name, ' ', last_name) AS customer_name,
    email
FROM customers;
```

---

## 2.8. Khi không nên dùng view

Không nên dùng view chỉ vì muốn truy vấn tự động nhanh hơn.

```text
VIEW thường không phải cache.
VIEW không lưu sẵn kết quả.
```

Nếu câu `SELECT` gốc chậm, đặt tên nó thành view không tự làm nó nhanh.

Không nên:

- lồng view quá nhiều tầng;
- dùng view để che thiết kế bảng yếu;
- dùng view cho logic thay đổi liên tục và khó truy vết;
- dùng view như materialized view;
- kỳ vọng tạo index trực tiếp trên view.

---

## 2.9. Quy trình thiết kế view thực tế

Trước khi tạo view, bắt đầu bằng các câu hỏi:

### Câu hỏi 1: Có một câu `SELECT` đang bị lặp lại ở nhiều nơi không?

Nếu chỉ dùng một lần, CTE hoặc query thường có thể đủ.

```sql
WITH active_users AS (
    SELECT *
    FROM users
    WHERE status = 'active'
)
SELECT *
FROM active_users;
```

### Câu hỏi 2: View này giải quyết vấn đề gì?

Chọn một mục tiêu rõ ràng:

```text
Đơn giản hóa JOIN?
Chuẩn hóa logic đọc?
Ẩn cột?
Tạo lớp BI?
Tương thích hệ thống cũ?
```

Không nên tạo view chỉ vì “trông gọn hơn”.

### Câu hỏi 3: Kết quả cần luôn mới hay cần cache?

Nếu cần luôn mới:

```text
VIEW phù hợp
```

Nếu cần lưu sẵn kết quả để đọc nhanh:

```text
Bảng tổng hợp hoặc materialization tự xây phù hợp hơn
```

### Câu hỏi 4: View có cần cập nhật được không?

Nếu cần `INSERT`, `UPDATE`, `DELETE` qua view:

- tránh `GROUP BY`;
- tránh aggregate;
- tránh `DISTINCT`;
- cân nhắc `WITH CHECK OPTION`;
- kiểm tra ánh xạ một dòng view về một dòng bảng nguồn.

### Câu hỏi 5: Truy vấn ngoài có thêm điều kiện và JOIN không?

Nếu có, ưu tiên view mergeable để optimizer có không gian tối ưu rộng hơn.

### Câu hỏi 6: Các bảng nguồn đã có index phù hợp chưa?

Ví dụ view:

```sql
SELECT *
FROM orders
WHERE status = 'completed';
```

Truy vấn ngoài:

```sql
SELECT *
FROM completed_orders
WHERE customer_id = 100;
```

Có thể cần index:

```sql
CREATE INDEX idx_orders_customer_status
ON orders(customer_id, status);
```

### Câu hỏi 7: View có làm người dùng khó truy vết dữ liệu không?

Kiểm tra:

```text
View phụ thuộc view khác bao nhiêu tầng?
Tên cột có rõ không?
Logic nghiệp vụ có bị giấu quá sâu không?
```

### Câu hỏi 8: Đã kiểm tra execution plan chưa?

Dùng:

```sql
EXPLAIN
SELECT *
FROM your_view
WHERE ...;
```

Hoặc:

```sql
EXPLAIN ANALYZE
SELECT ...
```

### Quy trình đề xuất

```text
1. Thu thập các query bị lặp.
2. Xác định mục tiêu của view.
3. Viết SELECT gốc và kiểm tra đúng dữ liệu.
4. Kiểm tra index của bảng nguồn.
5. Tạo view với tên và cột rõ ràng.
6. Kiểm tra khả năng merge/materialize.
7. Chạy EXPLAIN với query thực tế gọi view.
8. Kiểm tra quyền truy cập.
9. Ghi tài liệu phụ thuộc bảng/view.
10. Theo dõi hiệu năng sau khi dữ liệu lớn lên.
```

---

# 3. Functions

## 3.1. Hai nhóm function cần phân biệt

Trong MySQL thường gặp:

```text
Built-in functions
= hàm có sẵn của MySQL

Stored functions
= hàm do người dùng tự tạo và lưu trong database
```

Ví dụ built-in:

```sql
SELECT COUNT(*);
SELECT CONCAT(first_name, ' ', last_name);
SELECT NOW();
SELECT CHARSET(name);
SELECT COLLATION(name);
```

Ví dụ stored function:

```sql
SELECT calculate_discount_price(price, 20);
```

---

## 3.2. Built-in functions

### Hàm chuỗi

```sql
SELECT CONCAT('Nguyen', ' ', 'An');
```

```sql
SELECT LOWER('ADMIN');
```

```sql
SELECT LENGTH('Hello');
```

### Hàm số

```sql
SELECT ROUND(123.456, 2);
```

```sql
SELECT ABS(-10);
```

### Hàm ngày giờ

```sql
SELECT NOW();
```

```sql
SELECT DATE(created_at)
FROM orders;
```

### Hàm tổng hợp

```sql
SELECT COUNT(*)
FROM orders;
```

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
GROUP BY customer_id;
```

### Hàm thông tin

```sql
SELECT DATABASE();
SELECT USER();
SELECT CHARSET('Hello');
SELECT COLLATION('Hello');
```

---

## 3.3. `CHARSET()` và `COLLATION()`

### Character set là gì?

Character set quyết định:

```text
Có thể biểu diễn những ký tự nào?
Ký tự được mã hóa thành byte như thế nào?
```

Ví dụ:

```text
utf8mb4
```

có thể lưu:

```text
Tiếng Việt
日本語
中文
emoji 😀
```

### Collation là gì?

Collation quyết định:

```text
Chuỗi được so sánh như thế nào?
Có phân biệt hoa thường không?
Có phân biệt dấu không?
ORDER BY sắp xếp theo quy tắc nào?
UNIQUE coi những chuỗi nào là trùng?
```

Cách nhớ:

```text
CHARSET
= cách biểu diễn ký tự

COLLATION
= cách so sánh và sắp xếp ký tự
```

Ví dụ:

```text
utf8mb4_0900_ai_ci
```

Trong đó:

```text
utf8mb4 = character set
ai      = accent-insensitive
ci      = case-insensitive
```

Do đó:

```text
'An' có thể được xem bằng 'an'
'a' có thể được xem bằng 'á'
```

Với:

```text
utf8mb4_0900_as_cs
```

thì:

```text
as = accent-sensitive
cs = case-sensitive
```

Do đó:

```text
'An' khác 'an'
'a' khác 'á'
```

---

### Ví dụ định nghĩa cột

```sql
CREATE TABLE users (
    username VARCHAR(100)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_0900_ai_ci
);
```

Tìm kiếm:

```sql
SELECT *
FROM users
WHERE username = 'admin';
```

có thể khớp với:

```text
Admin
ADMIN
admin
```

Collation cũng ảnh hưởng đến `UNIQUE`:

```sql
CREATE TABLE accounts (
    username VARCHAR(100)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_0900_ai_ci,

    UNIQUE KEY uk_accounts_username (username)
);
```

Sau khi chèn:

```sql
INSERT INTO accounts VALUES ('Admin');
```

việc chèn:

```sql
INSERT INTO accounts VALUES ('admin');
```

có thể bị coi là trùng.

---

### `CHARSET()` trả về gì?

```sql
SELECT CHARSET('Hello');
```

Ví dụ:

```text
utf8mb4
```

### `COLLATION()` trả về gì?

```sql
SELECT COLLATION('Hello');
```

Ví dụ:

```text
utf8mb4_0900_ai_ci
```

Hai hàm chỉ báo metadata của biểu thức, không chuyển đổi dữ liệu.

Với cột:

```sql
SELECT
    CHARSET(username),
    COLLATION(username)
FROM accounts;
```

kết quả dựa trên định nghĩa cột.

---

## 3.4. Stored function

Stored function là một routine:

- nhận tham số;
- tính toán;
- bắt buộc trả về đúng một giá trị bằng `RETURN`;
- có thể dùng trong `SELECT`, `WHERE`, `ORDER BY` hoặc biểu thức.

Ví dụ:

```sql
DELIMITER //

CREATE FUNCTION calculate_discount_price(
    p_price DECIMAL(10, 2),
    p_discount_percent DECIMAL(5, 2)
)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
BEGIN
    RETURN p_price * (1 - p_discount_percent / 100);
END //

DELIMITER ;
```

Sử dụng:

```sql
SELECT calculate_discount_price(1000, 20);
```

Kết quả:

```text
800
```

Dùng với bảng:

```sql
SELECT
    product_id,
    product_name,
    price,
    calculate_discount_price(price, 20) AS discounted_price
FROM products;
```

---

## 3.5. `DETERMINISTIC` là gì?

Một function deterministic nghĩa là:

```text
Cùng đầu vào
→ luôn cho cùng đầu ra
```

Ví dụ:

```text
calculate_discount_price(1000, 20)
→ luôn là 800
```

Các hàm phụ thuộc thời gian, dữ liệu thay đổi hoặc random thường không deterministic theo nghĩa chặt.

Ví dụ:

```sql
RETURN NOW();
```

không cho cùng kết quả ở mọi thời điểm.

---

## 3.6. Khi nên dùng function

Phù hợp khi:

- cần một phép tính dùng lại ở nhiều câu SQL;
- đầu vào nhỏ, đầu ra một giá trị;
- logic gắn chặt với dữ liệu;
- muốn dùng trực tiếp trong biểu thức SQL;
- phép tính tương đối ổn định.

Ví dụ:

```text
Tính thuế
Tính giá sau giảm
Chuẩn hóa mã
Tính điểm
Tạo nhãn phân loại đơn giản
```

---

## 3.7. Khi không nên dùng function

Không nên dùng function nếu:

- function phải xử lý workflow nhiều bước;
- cần trả nhiều result set;
- cần thay đổi nhiều bảng;
- cần gọi API hoặc thao tác file;
- function sẽ bị gọi trên hàng triệu dòng nhưng bên trong rất nặng;
- logic thay đổi liên tục và phù hợp hơn với application code.

Ví dụ có nguy cơ chậm:

```sql
SELECT expensive_function(order_id)
FROM orders;
```

Nếu `orders` có 10 triệu dòng, function có thể được đánh giá rất nhiều lần.

---

## 3.8. Quy trình thiết kế function thực tế

### Câu hỏi 1: Kết quả có phải đúng một giá trị không?

Nếu cần:

```text
Một scalar value
→ function phù hợp
```

Nếu cần:

```text
Nhiều bước cập nhật
Nhiều result set
Nhiều bảng
→ procedure phù hợp hơn
```

### Câu hỏi 2: Logic có thuần tính toán không?

Function tốt thường có dạng:

```text
Input
→ tính toán
→ Output
```

Ví dụ:

```text
price + discount_percent
→ discounted_price
```

### Câu hỏi 3: Function có bị gọi theo từng dòng không?

Kiểm tra query thực tế:

```sql
SELECT my_function(column)
FROM huge_table;
```

Hỏi:

```text
Bảng có bao nhiêu dòng?
Function có truy vấn bảng khác không?
Có thể thay bằng JOIN hoặc biểu thức SQL trực tiếp không?
```

### Câu hỏi 4: Có cần index trên kết quả function không?

Nếu thường lọc:

```sql
WHERE DATE(created_at) = '2026-07-21'
```

có thể cân nhắc:

- viết range query;
- generated column;
- functional index.

Không nhất thiết tạo stored function.

### Câu hỏi 5: Logic có phù hợp đặt trong database không?

Đặt trong database nếu:

- nhiều ứng dụng cần dùng chung;
- logic ổn định;
- phụ thuộc trực tiếp dữ liệu SQL.

Đặt trong application nếu:

- cần API;
- cần config bên ngoài;
- thay đổi thường xuyên;
- cần test nghiệp vụ phức tạp.

### Câu hỏi 6: Character set và collation của input/output có rõ không?

Đặc biệt với function xử lý chuỗi:

```text
Có phân biệt hoa thường?
Có phân biệt dấu?
Kết quả dùng để so sánh hay hiển thị?
```

### Quy trình đề xuất

```text
1. Xác định input và đúng một output.
2. Viết logic bằng biểu thức SQL đơn giản trước.
3. Ước tính số lần function được gọi.
4. Tránh query nặng bên trong function.
5. Khai báo kiểu trả về chính xác.
6. Khai báo thuộc tính deterministic khi phù hợp.
7. Test NULL, số âm, giá trị biên.
8. Benchmark trên tập dữ liệu thật.
9. So sánh với giải pháp application hoặc generated column.
10. Tài liệu hóa quy tắc nghiệp vụ.
```

---

# 4. Stored routines

## 4.1. Stored routine là gì?

Stored routine là một chương trình SQL được đặt tên và lưu trong database.

Gồm:

```text
Stored procedure
Stored function
```

Cách nhớ:

```text
PROCEDURE
= làm một công việc

FUNCTION
= tính và trả về một giá trị
```

---

## 4.2. Stored procedure

Procedure được gọi bằng:

```sql
CALL procedure_name(...);
```

Procedure có thể:

- nhận tham số;
- chạy nhiều câu SQL;
- đọc và cập nhật dữ liệu;
- dùng biến cục bộ;
- dùng `IF`, `CASE`, vòng lặp;
- mở transaction;
- trả result set;
- trả giá trị qua `OUT`;
- xử lý lỗi.

Ví dụ:

```sql
DELIMITER //

CREATE PROCEDURE increase_product_price(
    IN p_product_id BIGINT,
    IN p_amount DECIMAL(10, 2)
)
BEGIN
    UPDATE products
    SET price = price + p_amount
    WHERE product_id = p_product_id;
END //

DELIMITER ;
```

Gọi:

```sql
CALL increase_product_price(10, 100);
```

---

## 4.3. `DELIMITER` để làm gì?

Bên trong procedure có nhiều dấu `;`:

```sql
BEGIN
    UPDATE ...;
    SELECT ...;
END
```

MySQL client mặc định xem `;` là dấu kết thúc lệnh.

Do đó, khi tạo routine, tạm đổi delimiter:

```sql
DELIMITER //
```

Kết thúc toàn bộ định nghĩa bằng:

```sql
END //
```

Sau đó đổi lại:

```sql
DELIMITER ;
```

`DELIMITER` là chỉ dẫn cho client, không phải logic được lưu trong routine.

---

## 4.4. Tham số `IN`, `OUT`, `INOUT`

### `IN`

Đưa giá trị vào procedure:

```sql
DELIMITER //

CREATE PROCEDURE find_product(IN p_product_id BIGINT)
BEGIN
    SELECT *
    FROM products
    WHERE product_id = p_product_id;
END //

DELIMITER ;
```

Gọi:

```sql
CALL find_product(10);
```

---

### `OUT`

Procedure ghi giá trị ra ngoài:

```sql
DELIMITER //

CREATE PROCEDURE count_products(OUT p_total INT)
BEGIN
    SELECT COUNT(*)
    INTO p_total
    FROM products;
END //

DELIMITER ;
```

Gọi:

```sql
CALL count_products(@total);

SELECT @total;
```

Không cần:

```sql
DECLARE @total INT;
```

Vì `@total` là user-defined session variable. Khi dùng, MySQL tự tạo biến trong session hiện tại.

---

### `INOUT`

Vừa nhận giá trị vào, vừa ghi giá trị ra:

```sql
DELIMITER //

CREATE PROCEDURE add_ten(INOUT p_number INT)
BEGIN
    SET p_number = p_number + 10;
END //

DELIMITER ;
```

Gọi:

```sql
SET @number = 5;

CALL add_ten(@number);

SELECT @number;
```

Kết quả:

```text
15
```

---

## 4.5. Session variable và local variable

### Session variable

Có dấu `@`:

```sql
SET @total = 0;
SELECT @total;
```

Đặc điểm:

- không dùng `DECLARE`;
- thuộc session hiện tại;
- mất khi connection kết thúc;
- nếu chưa gán thường trả `NULL`.

### Local variable

Không có dấu `@`:

```sql
DECLARE v_total INT;
```

Chỉ dùng trong stored program hoặc block hợp lệ:

```sql
DELIMITER //

CREATE PROCEDURE show_count()
BEGIN
    DECLARE v_total INT;

    SELECT COUNT(*)
    INTO v_total
    FROM products;

    SELECT v_total;
END //

DELIMITER ;
```

Cách nhớ:

```text
@total
= biến session
= không DECLARE

v_total
= biến cục bộ
= phải DECLARE
```

---

## 4.6. Procedure có transaction và xử lý lỗi

Ví dụ tạo đơn hàng:

```sql
DELIMITER //

CREATE PROCEDURE create_order(
    IN p_customer_id BIGINT,
    IN p_product_id BIGINT,
    IN p_quantity INT
)
BEGIN
    DECLARE v_stock INT;
    DECLARE v_price DECIMAL(10, 2);
    DECLARE v_order_id BIGINT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT
        stock,
        price
    INTO
        v_stock,
        v_price
    FROM products
    WHERE product_id = p_product_id
    FOR UPDATE;

    IF v_stock < p_quantity THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Not enough stock';
    END IF;

    INSERT INTO orders (
        customer_id,
        total_amount,
        status
    )
    VALUES (
        p_customer_id,
        v_price * p_quantity,
        'created'
    );

    SET v_order_id = LAST_INSERT_ID();

    INSERT INTO order_items (
        order_id,
        product_id,
        quantity,
        unit_price
    )
    VALUES (
        v_order_id,
        p_product_id,
        p_quantity,
        v_price
    );

    UPDATE products
    SET stock = stock - p_quantity
    WHERE product_id = p_product_id;

    COMMIT;

    SELECT v_order_id AS order_id;
END //

DELIMITER ;
```

Gọi:

```sql
CALL create_order(100, 20, 2);
```

Nếu một câu SQL lỗi:

```text
EXIT HANDLER
→ ROLLBACK
→ RESIGNAL
```

---

## 4.7. Trường hợp sử dụng stored procedure

### 1. Nhiều câu SQL phải thành công cùng nhau

Ví dụ:

```text
Tạo order
Tạo order_items
Trừ stock
Ghi audit
```

### 2. Nhiều ứng dụng dùng cùng một thao tác

```text
Python backend
Java dashboard
Node.js internal tool
```

Tất cả gọi:

```sql
CALL create_order(...);
```

### 3. Giới hạn quyền truy cập

Không cấp quyền cập nhật trực tiếp bảng, chỉ cấp:

```sql
GRANT EXECUTE
ON PROCEDURE shop.create_order
TO 'app_user'@'%';
```

### 4. Giảm số lượt trao đổi client-server

Không dùng procedure:

```text
Client → SELECT
Client ← result
Client → INSERT
Client ← result
Client → UPDATE
Client ← result
```

Dùng procedure:

```text
Client → CALL procedure
Client ← result
```

### 5. Xử lý batch hoặc metadata

Ví dụ crawler:

```sql
CALL finalize_load_batch(500);
CALL retry_failed_tasks(1001);
CALL mark_crawl_run_completed(200);
```

---

## 4.8. Khi không nên dùng stored routine

Không nên đặt toàn bộ business logic vào database.

Các việc thường phù hợp hơn với application:

- gọi API;
- gửi email;
- upload file S3/MinIO;
- xử lý workflow dài;
- logic thay đổi liên tục;
- điều phối nhiều service;
- xử lý UI hoặc authorization phức tạp.

Không nên tạo procedure hàng nghìn dòng với quá nhiều:

```text
IF
LOOP
CURSOR
TEMPORARY TABLE
DYNAMIC SQL
```

Nó sẽ khó:

- version control;
- review;
- test;
- debug;
- deploy;
- migrate sang database khác.

---

## 4.9. Quy trình thiết kế stored routine thực tế

### Câu hỏi 1: Đây là phép tính hay một quy trình?

```text
Một giá trị
→ function

Nhiều bước
→ procedure
```

### Câu hỏi 2: Các bước có cần transaction chung không?

Nếu một phần thành công còn phần khác thất bại sẽ làm dữ liệu sai:

```text
Nên dùng procedure + transaction
```

### Câu hỏi 3: Logic có gắn chặt với dữ liệu SQL không?

Phù hợp:

```text
INSERT nhiều bảng
UPDATE trạng thái
Kiểm tra tồn kho
Ghi audit
Tổng hợp metadata
```

Không phù hợp:

```text
Gọi API thanh toán
Upload file
Gửi email
Chờ người dùng
```

### Câu hỏi 4: Nhiều ứng dụng có cần dùng chung không?

Nếu có, stored routine có thể là một API dữ liệu chung.

### Câu hỏi 5: Có cần giới hạn quyền không?

Hỏi:

```text
App có thực sự cần UPDATE trực tiếp bảng không?
Có thể chỉ cấp EXECUTE không?
```

### Câu hỏi 6: Routine có giữ lock lâu không?

Không đưa vào transaction:

- network call;
- sleep;
- thao tác CPU lâu;
- chờ input;
- upload file.

### Câu hỏi 7: Khi lỗi thì rollback đến đâu?

Xác định:

```text
Rollback toàn bộ?
Dùng SAVEPOINT?
Có lỗi nào cần retry?
Có deadlock không?
```

### Câu hỏi 8: Routine có idempotent không?

Nếu gọi lại sau timeout:

```text
Có tạo order trùng không?
Có tăng counter hai lần không?
Có nạp batch hai lần không?
```

Có thể cần:

- unique key;
- idempotency key;
- trạng thái xử lý;
- điều kiện `WHERE status = 'pending'`.

### Câu hỏi 9: Có cần trả result set, OUT hay mã lỗi?

Thiết kế contract rõ:

```text
Input là gì?
Output là gì?
Lỗi nào có thể xảy ra?
Caller retry khi nào?
```

### Quy trình đề xuất

```text
1. Viết rõ nghiệp vụ bằng các bước.
2. Xác định ranh giới transaction.
3. Xác định input, output và lỗi.
4. Đảm bảo các query bên trong có index phù hợp.
5. Thiết kế idempotency.
6. Viết handler ROLLBACK và RESIGNAL.
7. Giữ transaction ngắn.
8. Test concurrent calls.
9. Test deadlock và retry.
10. Version control file SQL.
11. Deploy bằng migration.
12. Theo dõi thời gian chạy và lock.
```

---

# 5. Indexes

## 5.1. Index là gì?

Index là một **cấu trúc dữ liệu phụ** được MySQL duy trì để tìm dòng nhanh hơn.

Ví dụ bảng có 10 triệu đơn hàng:

```sql
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT,
    status VARCHAR(20),
    total_amount DECIMAL(12, 2),
    created_at DATETIME
);
```

Truy vấn:

```sql
SELECT *
FROM orders
WHERE customer_id = 100;
```

Không có index:

```text
Kiểm tra từng dòng
→ full table scan
```

Có index:

```sql
CREATE INDEX idx_orders_customer_id
ON orders(customer_id);
```

MySQL có thể đi đến vùng chứa `customer_id = 100` thay vì đọc mọi dòng.

---

## 5.2. Bản chất index lưu gì?

Index không chỉ lưu metadata rằng “cột này đã được index”.

Nó là một cấu trúc dữ liệu thật, chiếm disk và memory.

Index B-tree có thể hình dung:

```text
                    [100 | 500]
                   /     |      \
             < 100      ...      > 500
```

Thực tế mỗi page chứa nhiều key, nhưng ý tưởng là MySQL tìm theo cây thay vì duyệt tuần tự.

---

## 5.3. Clustered index trong InnoDB

Trong InnoDB:

```text
PRIMARY KEY
= clustered index
```

Leaf page của clustered index chứa dữ liệu đầy đủ của dòng.

Ví dụ:

```sql
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT,
    status VARCHAR(20),
    total_amount DECIMAL(12, 2)
);
```

Có thể hình dung:

```text
order_id = 1001
├── customer_id = 50
├── status = completed
└── total_amount = 3000
```

Tìm bằng primary key:

```sql
SELECT *
FROM orders
WHERE order_id = 1001;
```

MySQL đi trực tiếp đến dòng dữ liệu trong clustered index.

Nếu không có primary key, InnoDB sẽ tìm unique non-null key phù hợp hoặc tạo key ẩn.

Do đó, mỗi bảng nên có primary key rõ ràng.

---

## 5.4. Secondary index

Ví dụ:

```sql
CREATE INDEX idx_orders_customer
ON orders(customer_id);
```

Secondary index InnoDB thường chứa:

```text
customer_id
+
primary key
```

Có thể hình dung:

| customer_id | order_id |
|---:|---:|
| 50 | 1001 |
| 50 | 1020 |
| 80 | 1002 |

Truy vấn:

```sql
SELECT *
FROM orders
WHERE customer_id = 50;
```

Có thể gồm hai bước:

```text
1. Tìm customer_id trong secondary index.
2. Lấy order_id rồi quay về clustered index lấy full row.
```

Do primary key nằm trong secondary index, primary key quá dài sẽ làm mọi secondary index lớn hơn.

---

## 5.5. Những trường hợp index thường hữu ích

### Cột trong `WHERE`

```sql
SELECT *
FROM users
WHERE email = 'an@example.com';
```

```sql
CREATE UNIQUE INDEX uk_users_email
ON users(email);
```

### Cột trong `JOIN`

```sql
SELECT
    o.order_id,
    c.customer_name
FROM orders AS o
JOIN customers AS c
    ON c.customer_id = o.customer_id;
```

Thường cần:

```text
customers.customer_id
→ PRIMARY KEY

orders.customer_id
→ secondary index
```

### Range query

```sql
SELECT *
FROM orders
WHERE created_at >= '2026-07-01'
  AND created_at <  '2026-08-01';
```

```sql
CREATE INDEX idx_orders_created_at
ON orders(created_at);
```

### `ORDER BY ... LIMIT`

```sql
SELECT *
FROM orders
ORDER BY created_at DESC
LIMIT 20;
```

Index phù hợp có thể tránh sort lớn.

### Kiểm tra tồn tại và chống trùng

```sql
CREATE UNIQUE INDEX uk_parsed_source_record
ON parsed_records(source_id, source_record_id);
```

---

## 5.6. Composite index

Composite index chứa nhiều cột:

```sql
CREATE INDEX idx_orders_customer_status
ON orders(customer_id, status);
```

Nó được sắp xếp theo:

```text
customer_id trước
→ trong cùng customer_id, sắp tiếp status
```

Ví dụ:

| customer_id | status |
|---:|---|
| 1 | cancelled |
| 1 | completed |
| 1 | pending |
| 2 | completed |
| 2 | pending |

---

## 5.7. Leftmost prefix

Với index:

```sql
INDEX(customer_id, status, created_at)
```

Các prefix từ trái:

```text
(customer_id)

(customer_id, status)

(customer_id, status, created_at)
```

Các truy vấn phù hợp:

```sql
WHERE customer_id = 10;
```

```sql
WHERE customer_id = 10
  AND status = 'completed';
```

```sql
WHERE customer_id = 10
  AND status = 'completed'
  AND created_at >= '2026-07-01';
```

Không phù hợp để lookup chính theo:

```sql
WHERE status = 'completed';
```

vì bỏ qua cột đầu `customer_id`.

---

## 5.8. Equality trước, range sau

Query:

```sql
SELECT *
FROM orders
WHERE customer_id = 100
  AND status = 'completed'
  AND created_at >= '2026-07-01';
```

Index thường hợp lý:

```sql
INDEX(customer_id, status, created_at)
```

Cách nghĩ:

```text
Các điều kiện equality trước
→ cột range sau
→ cột phục vụ ORDER BY hoặc covering nếu cần
```

Đây là nguyên tắc ban đầu, không phải luật tuyệt đối. Luôn kiểm tra `EXPLAIN`.

---

## 5.9. Covering index

Index:

```sql
CREATE INDEX idx_tasks_run_status_id
ON crawl_tasks(run_id, status, task_id);
```

Query:

```sql
SELECT task_id
FROM crawl_tasks
WHERE run_id = 1001
  AND status = 'failed';
```

Mọi cột query cần đều nằm trong index:

```text
run_id
status
task_id
```

MySQL có thể trả kết quả từ index mà không quay về đọc full row.

Không nên thêm mọi cột vào index chỉ để covering, vì index quá rộng sẽ:

- tốn disk;
- tốn buffer pool;
- làm ghi chậm;
- tăng maintenance cost.

---

## 5.10. Selectivity

Selectivity cao:

```text
email
order_id
source_record_id
content_hash
```

Một giá trị thường trả rất ít dòng.

Selectivity thấp:

```text
is_active
gender
status có vài giá trị
```

Ví dụ:

```text
TRUE  = 9.900.000 dòng
FALSE =   100.000 dòng
```

Index riêng trên `is_active` có thể không hữu ích khi tìm `TRUE`.

Nhưng cột selectivity thấp vẫn có thể hữu ích trong composite index:

```sql
INDEX(source_id, status, scheduled_at)
```

---

## 5.11. Chi phí của index

Mỗi lần:

```sql
INSERT
UPDATE
DELETE
```

MySQL phải duy trì các index liên quan.

Ví dụ bảng có:

```sql
PRIMARY KEY (task_id)
INDEX idx_status (status)
INDEX idx_run_status (run_id, status)
```

Khi chèn một dòng:

```text
Ghi clustered index
+ cập nhật idx_status
+ cập nhật idx_run_status
```

Index:

- làm đọc nhanh hơn;
- làm ghi tốn hơn;
- chiếm disk;
- chiếm RAM;
- tăng chi phí optimizer.

Không index mọi cột.

---

## 5.12. Khi index thường không hiệu quả

### Lấy phần lớn bảng

```sql
SELECT *
FROM orders
WHERE status <> 'deleted';
```

Nếu 99% dòng thỏa, full table scan có thể rẻ hơn.

### Dùng hàm trên cột

Có index:

```sql
CREATE INDEX idx_orders_created_at
ON orders(created_at);
```

Query:

```sql
WHERE DATE(created_at) = '2026-07-21'
```

Cách viết thường tốt hơn:

```sql
WHERE created_at >= '2026-07-21 00:00:00'
  AND created_at <  '2026-07-22 00:00:00'
```

### `LIKE` bắt đầu bằng `%`

Có thể dùng index tốt hơn:

```sql
WHERE name LIKE 'Nguyen%';
```

Khó dùng B-tree để lookup:

```sql
WHERE name LIKE '%Nguyen%';
```

### Kiểu dữ liệu JOIN không tương thích

Sai thiết kế:

```text
orders.customer_id BIGINT
customers.customer_id VARCHAR(20)
```

Các cột khóa nối nên cùng kiểu tương thích.

---

## 5.13. Các loại index thường gặp

### Primary key

```sql
PRIMARY KEY (order_id)
```

- duy nhất;
- không `NULL`;
- clustered index trong InnoDB.

### Unique index

```sql
UNIQUE KEY uk_users_email (email)
```

- tăng tốc;
- chống trùng.

### Normal index

```sql
INDEX idx_orders_customer (customer_id)
```

### Composite index

```sql
INDEX idx_tasks_run_status (run_id, status)
```

### Prefix index

```sql
CREATE INDEX idx_url_prefix
ON crawl_tasks(url(100));
```

### Functional index

```sql
CREATE INDEX idx_orders_created_date
ON orders ((DATE(created_at)));
```

### Full-text index

```sql
FULLTEXT INDEX ft_articles_content (title, content);
```

---

## 5.14. Kiểm tra index bằng `EXPLAIN`

```sql
EXPLAIN
SELECT *
FROM crawl_tasks
WHERE run_id = 1001
  AND status = 'failed';
```

Các cột quan trọng:

```text
possible_keys
= index có thể dùng

key
= index được chọn

rows
= số dòng ước tính phải xem

type
= kiểu truy cập

Extra
= thông tin bổ sung
```

Dùng số liệu thực tế:

```sql
EXPLAIN ANALYZE
SELECT ...
```

Xem index hiện có:

```sql
SHOW INDEX FROM crawl_tasks;
```

```sql
SHOW CREATE TABLE crawl_tasks;
```

---

## 5.15. Quy trình thiết kế index thực tế

Không bắt đầu bằng:

> Bảng có những cột nào để index?

Hãy bắt đầu bằng:

> Hệ thống thực sự chạy những query nào?

### Câu hỏi 1: Query quan trọng nhất là gì?

Ví dụ:

```sql
SELECT task_id, url
FROM crawl_tasks
WHERE run_id = ?
  AND status = 'pending'
ORDER BY scheduled_at
LIMIT 100;
```

### Câu hỏi 2: Cột nào nằm trong `WHERE`?

```text
run_id
status
```

### Câu hỏi 3: Điều kiện là equality hay range?

```text
run_id = ?
status = ?
scheduled_at có thể phục vụ ORDER BY
```

### Câu hỏi 4: Có `ORDER BY` và `LIMIT` không?

```text
ORDER BY scheduled_at
LIMIT 100
```

Index ban đầu:

```sql
CREATE INDEX idx_tasks_run_status_scheduled
ON crawl_tasks(run_id, status, scheduled_at);
```

### Câu hỏi 5: Query lấy ít dòng hay phần lớn bảng?

Nếu lấy 80–90% bảng, index có thể không giúp.

### Câu hỏi 6: Có cần unique constraint không?

Ví dụ:

```text
source_id + source_record_id
```

Nếu phải duy nhất:

```sql
CREATE UNIQUE INDEX ...
```

### Câu hỏi 7: Có thể tạo covering index không?

Chỉ cân nhắc cho query quan trọng, chạy nhiều và đọc nhiều lần.

### Câu hỏi 8: Index có trùng hoặc dư thừa không?

Nếu đã có:

```sql
INDEX(a, b)
```

thì index riêng:

```sql
INDEX(a)
```

có thể dư trong nhiều trường hợp, nhưng phải kiểm tra query thực tế trước khi xóa.

### Câu hỏi 9: Chi phí ghi có chấp nhận được không?

Hỏi:

```text
Bảng ghi nhiều hay đọc nhiều?
Cột được update thường xuyên không?
Index rộng bao nhiêu?
```

### Câu hỏi 10: Đã xác minh bằng execution plan chưa?

Không dừng ở “có vẻ đúng”.

### Quy trình đề xuất

```text
1. Thu thập slow query và query quan trọng.
2. Ghi lại WHERE, JOIN, ORDER BY, GROUP BY, LIMIT.
3. Phân loại equality và range.
4. Ước tính số dòng trả về.
5. Thiết kế composite index từ trái sang phải.
6. Kiểm tra leftmost prefix.
7. Cân nhắc unique và covering.
8. Chạy EXPLAIN.
9. Chạy EXPLAIN ANALYZE trên môi trường an toàn.
10. Đo read latency và write cost.
11. Xóa index trùng hoặc không dùng.
12. Theo dõi lại khi dữ liệu tăng trưởng.
```

---

# 6. Transactions

## 6.1. Transaction là gì?

Transaction là một nhóm thao tác database được xem như một đơn vị công việc duy nhất.

```text
Tất cả thành công
→ COMMIT

Có lỗi hoặc không muốn giữ
→ ROLLBACK
```

Ví dụ chuyển tiền:

```sql
START TRANSACTION;

UPDATE accounts
SET balance = balance - 500000
WHERE account_id = 1;

UPDATE accounts
SET balance = balance + 500000
WHERE account_id = 2;

COMMIT;
```

Không được để xảy ra:

```text
A đã bị trừ
B chưa được cộng
```

Nếu có lỗi:

```sql
ROLLBACK;
```

---

## 6.2. `autocommit`

MySQL thường bật:

```text
autocommit = 1
```

Do đó mỗi câu riêng lẻ là một transaction riêng:

```sql
UPDATE accounts
SET balance = balance - 500000
WHERE account_id = 1;
```

Câu này chạy xong có thể được commit ngay.

Nếu muốn gom nhiều câu:

```sql
START TRANSACTION;

UPDATE ...;
UPDATE ...;
INSERT ...;

COMMIT;
```

---

## 6.3. `COMMIT` và `ROLLBACK`

### `COMMIT`

```sql
COMMIT;
```

Có nghĩa:

```text
Xác nhận toàn bộ thay đổi của transaction.
```

### `ROLLBACK`

```sql
ROLLBACK;
```

Có nghĩa:

```text
Hủy các thay đổi chưa commit của transaction.
```

---

## 6.4. ACID

### Atomicity

```text
Tất cả hoặc không gì cả.
```

### Consistency

```text
Dữ liệu đi từ trạng thái hợp lệ
sang trạng thái hợp lệ khác.
```

Transaction không tự biết toàn bộ business rule. Vẫn cần:

- primary key;
- foreign key;
- unique;
- check constraint;
- kiểm tra trong code hoặc procedure.

### Isolation

Các transaction chạy đồng thời không được làm sai dữ liệu của nhau.

### Durability

Sau khi commit, dữ liệu phải được duy trì và có khả năng khôi phục sau sự cố theo cơ chế của InnoDB và cấu hình hệ thống.

---

## 6.5. Ví dụ tạo đơn hàng

```sql
START TRANSACTION;

SELECT
    stock,
    price
FROM products
WHERE product_id = 10
FOR UPDATE;

INSERT INTO orders (
    customer_id,
    total_amount,
    status
)
VALUES (
    100,
    500000,
    'created'
);

SET @order_id = LAST_INSERT_ID();

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    @order_id,
    10,
    2,
    250000
);

UPDATE products
SET stock = stock - 2
WHERE product_id = 10;

COMMIT;
```

Nếu có lỗi:

```sql
ROLLBACK;
```

---

## 6.6. `SELECT ... FOR UPDATE`

Một `SELECT` thường chỉ đọc:

```sql
SELECT stock
FROM products
WHERE product_id = 10;
```

Transaction khác có thể cập nhật dòng sau khi ta đọc.

Nếu quy trình là:

```text
Đọc
→ kiểm tra
→ cập nhật
```

có thể dùng:

```sql
SELECT stock
FROM products
WHERE product_id = 10
FOR UPDATE;
```

Dòng được khóa cho mục đích cập nhật đến khi transaction kết thúc.

Một cách khác là dùng update có điều kiện:

```sql
UPDATE products
SET stock = stock - 1
WHERE product_id = 10
  AND stock >= 1;
```

Sau đó kiểm tra:

```sql
SELECT ROW_COUNT();
```

Nếu `0`, có thể là không đủ stock hoặc không có sản phẩm.

---

## 6.7. Isolation levels

InnoDB hỗ trợ:

```text
READ UNCOMMITTED
READ COMMITTED
REPEATABLE READ
SERIALIZABLE
```

Hiểu khái quát:

| Isolation level | Ý nghĩa |
|---|---|
| `READ UNCOMMITTED` | Có thể đọc dữ liệu chưa commit |
| `READ COMMITTED` | Mỗi lần đọc thấy dữ liệu đã commit mới nhất |
| `REPEATABLE READ` | Các consistent read trong transaction thường dùng snapshot ổn định |
| `SERIALIZABLE` | Cô lập nghiêm ngặt hơn, concurrency thấp hơn |

Thiết lập cho transaction tiếp theo:

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

START TRANSACTION;

SELECT ...;

COMMIT;
```

Không tăng isolation chỉ vì nghĩ “cao hơn luôn tốt hơn”. Mức cao hơn có thể tăng chờ lock.

---

## 6.8. Lock và transaction dài

Các thao tác như:

```text
UPDATE
DELETE
SELECT ... FOR UPDATE
```

có thể giữ lock đến:

```sql
COMMIT;
```

hoặc:

```sql
ROLLBACK;
```

Không nên:

```text
START TRANSACTION
→ UPDATE
→ gọi API 30 giây
→ upload file
→ chờ người dùng
→ COMMIT
```

Transaction dài gây:

- lock lâu;
- transaction khác chờ;
- tăng deadlock;
- giữ version cũ lâu;
- khó vận hành.

---

## 6.9. Deadlock

Transaction A:

```sql
START TRANSACTION;

UPDATE accounts
SET balance = balance - 100
WHERE account_id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE account_id = 2;
```

Transaction B:

```sql
START TRANSACTION;

UPDATE accounts
SET balance = balance - 50
WHERE account_id = 2;

UPDATE accounts
SET balance = balance + 50
WHERE account_id = 1;
```

Tình trạng:

```text
A giữ account 1, chờ account 2
B giữ account 2, chờ account 1
```

InnoDB có thể rollback một transaction.

Ứng dụng phải có khả năng retry toàn bộ transaction.

Giảm deadlock bằng cách:

- cập nhật theo cùng thứ tự;
- giữ transaction ngắn;
- index đúng điều kiện update;
- khóa ít dòng nhất;
- retry khi gặp deadlock.

---

## 6.10. Một lỗi SQL không luôn rollback toàn bộ transaction

Ví dụ:

```sql
START TRANSACTION;

UPDATE products
SET stock = stock - 1
WHERE product_id = 10;

INSERT INTO users (email)
VALUES ('existing@example.com');
```

Nếu `INSERT` lỗi unique, trong nhiều trường hợp chỉ câu `INSERT` bị rollback.

`UPDATE` trước vẫn có thể còn trong transaction.

Ứng dụng cần:

```sql
ROLLBACK;
```

Mẫu:

```text
try:
    begin
    run SQL
    commit
except:
    rollback
    retry hoặc báo lỗi
```

---

## 6.11. `SAVEPOINT`

```sql
START TRANSACTION;

INSERT INTO orders (...)
VALUES (...);

SAVEPOINT order_created;

INSERT INTO optional_order_notes (...)
VALUES (...);
```

Nếu chỉ muốn hủy phần note:

```sql
ROLLBACK TO SAVEPOINT order_created;
```

Sau đó:

```sql
COMMIT;
```

Các lệnh:

```sql
SAVEPOINT savepoint_name;
ROLLBACK TO SAVEPOINT savepoint_name;
RELEASE SAVEPOINT savepoint_name;
```

---

## 6.12. DDL và implicit commit

Các lệnh như:

```text
CREATE TABLE
ALTER TABLE
DROP TABLE
CREATE INDEX
TRUNCATE TABLE
```

thường gây implicit commit.

Không nên kỳ vọng:

```sql
START TRANSACTION;

UPDATE products
SET price = 1000
WHERE product_id = 10;

ALTER TABLE products
ADD COLUMN note TEXT;

ROLLBACK;
```

sẽ rollback giống một nhóm DML thông thường.

Nên tách migration schema khỏi transaction nghiệp vụ.

---

## 6.13. Transaction không rollback được hệ thống bên ngoài

`ROLLBACK` không thể thu hồi:

- email đã gửi;
- file đã upload lên S3;
- API đã gọi;
- message đã publish sang hệ thống ngoài, trừ khi có cơ chế phối hợp riêng.

Ví dụ crawler:

```text
Upload file MinIO/S3
→ upload thành công
→ mở transaction DB ngắn
→ ghi storage_path và metadata
→ COMMIT
```

Nếu database rollback sau khi file đã upload, cần:

- cleanup;
- reconciliation;
- idempotency;
- trạng thái orphan;
- job kiểm tra định kỳ.

Các pattern thường dùng:

```text
Outbox pattern
Idempotency key
Retry
Saga
Compensating action
```

---

## 6.14. Trường hợp sử dụng transaction

### 1. Nhiều bảng thay đổi cùng nhau

```text
orders
order_items
products
payments
audit_logs
```

### 2. Chuyển tiền hoặc chuyển số lượng

```text
Trừ A
Cộng B
```

### 3. Đọc rồi kiểm tra rồi cập nhật

```text
Kiểm tra stock
→ bán hàng

Kiểm tra balance
→ trừ tiền

Kiểm tra pending
→ claim task
```

### 4. Claim task cho worker

```sql
START TRANSACTION;

SELECT task_id
FROM crawl_tasks
WHERE status = 'pending'
ORDER BY scheduled_at
LIMIT 1
FOR UPDATE SKIP LOCKED;

UPDATE crawl_tasks
SET
    status = 'running',
    worker_id = 'worker-01',
    started_at = NOW()
WHERE task_id = @task_id;

COMMIT;
```

### 5. Hoàn tất crawl run

```sql
START TRANSACTION;

UPDATE crawl_runs
SET
    status = 'completed',
    finished_at = NOW()
WHERE run_id = 1001;

INSERT INTO crawl_run_summaries (
    run_id,
    success_count,
    failed_count
)
SELECT
    run_id,
    SUM(status = 'success'),
    SUM(status = 'failed')
FROM crawl_tasks
WHERE run_id = 1001
GROUP BY run_id;

COMMIT;
```

### 6. Load batch

```sql
START TRANSACTION;

UPDATE load_batches
SET
    status = 'loading',
    started_loading_at = NOW()
WHERE batch_id = 500
  AND status = 'pending';

INSERT INTO suumo_rental_raw (...)
VALUES (...);

UPDATE load_batches
SET
    status = 'completed',
    finished_loading_at = NOW(),
    loaded_row_count = 1000
WHERE batch_id = 500;

COMMIT;
```

---

## 6.15. Quy trình thiết kế transaction thực tế

### Câu hỏi 1: Đơn vị nghiệp vụ hoàn chỉnh là gì?

Ví dụ:

```text
“Tạo đơn hàng”
không phải chỉ là INSERT orders.

Nó có thể gồm:
- order
- order_items
- stock
- payment state
- audit
```

### Câu hỏi 2: Thay đổi nào phải thành công hoặc thất bại cùng nhau?

Đưa đúng các thay đổi đó vào cùng transaction.

Không gom quá nhiều việc không liên quan.

### Câu hỏi 3: Có thao tác bên ngoài database không?

Nếu có:

```text
API
S3
email
message queue
```

không giữ transaction DB mở trong lúc chờ.

Thiết kế outbox, retry hoặc compensation.

### Câu hỏi 4: Có bước “đọc rồi quyết định cập nhật” không?

Nếu có, cần cân nhắc:

```text
SELECT ... FOR UPDATE
UPDATE có điều kiện
optimistic locking
unique constraint
```

### Câu hỏi 5: Những dòng nào sẽ bị khóa?

Hỏi:

```text
Điều kiện UPDATE có index không?
Có khóa nhiều dòng hơn dự kiến không?
Transaction khác sẽ chờ bao lâu?
```

### Câu hỏi 6: Isolation level mặc định có đủ không?

Không đổi isolation nếu chưa xác định anomaly cần ngăn.

### Câu hỏi 7: Transaction có thể deadlock không?

Xác định thứ tự:

```text
Luôn update table A trước table B
Luôn lock ID nhỏ trước ID lớn
```

### Câu hỏi 8: Khi lỗi thì rollback và retry như thế nào?

Phải có:

```text
try
commit
except
rollback
retry nếu lỗi tạm thời
```

### Câu hỏi 9: Transaction có idempotent không?

Nếu client timeout sau khi server commit nhưng chưa nhận response:

```text
Caller retry có tạo trùng không?
```

Dùng:

- idempotency key;
- unique index;
- trạng thái;
- request ID.

### Câu hỏi 10: Transaction có quá dài không?

Transaction tốt thường:

```text
Ngắn
Ít query
Có index
Không network call
Không chờ người dùng
```

### Quy trình đề xuất

```text
1. Viết rõ đơn vị nghiệp vụ.
2. Liệt kê mọi thay đổi dữ liệu.
3. Chọn thay đổi phải atomic.
4. Tách thao tác bên ngoài DB.
5. Chọn chiến lược concurrency.
6. Đảm bảo query khóa có index.
7. Xác định thứ tự lock.
8. Viết commit, rollback và error handling.
9. Thiết kế idempotency.
10. Test đồng thời nhiều session.
11. Test deadlock và retry.
12. Theo dõi lock wait và transaction duration.
```

---

# 7. Cách các thành phần phối hợp với nhau

Ví dụ hệ thống tạo đơn hàng:

```text
VIEW
→ tạo lớp đọc order/report dễ dùng

FUNCTION
→ tính discount hoặc tax

PROCEDURE
→ đóng gói quy trình create_order

INDEX
→ tìm product, customer, pending order nhanh

TRANSACTION
→ bảo đảm order, item và stock thay đổi cùng nhau
```

Ví dụ:

```sql
CREATE FUNCTION calculate_order_total(
    p_price DECIMAL(10, 2),
    p_quantity INT,
    p_discount_percent DECIMAL(5, 2)
)
RETURNS DECIMAL(12, 2)
DETERMINISTIC
RETURN p_price
       * p_quantity
       * (1 - p_discount_percent / 100);
```

Index:

```sql
CREATE INDEX idx_products_status
ON products(status);

CREATE INDEX idx_order_items_order
ON order_items(order_id);

CREATE INDEX idx_orders_customer_created
ON orders(customer_id, created_at DESC);
```

Procedure dùng transaction:

```sql
DELIMITER //

CREATE PROCEDURE create_order(
    IN p_customer_id BIGINT,
    IN p_product_id BIGINT,
    IN p_quantity INT,
    IN p_discount_percent DECIMAL(5, 2)
)
BEGIN
    DECLARE v_stock INT;
    DECLARE v_price DECIMAL(10, 2);
    DECLARE v_total DECIMAL(12, 2);
    DECLARE v_order_id BIGINT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT stock, price
    INTO v_stock, v_price
    FROM products
    WHERE product_id = p_product_id
    FOR UPDATE;

    IF v_stock < p_quantity THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Not enough stock';
    END IF;

    SET v_total = calculate_order_total(
        v_price,
        p_quantity,
        p_discount_percent
    );

    INSERT INTO orders (
        customer_id,
        total_amount,
        status,
        created_at
    )
    VALUES (
        p_customer_id,
        v_total,
        'created',
        NOW()
    );

    SET v_order_id = LAST_INSERT_ID();

    INSERT INTO order_items (
        order_id,
        product_id,
        quantity,
        unit_price
    )
    VALUES (
        v_order_id,
        p_product_id,
        p_quantity,
        v_price
    );

    UPDATE products
    SET stock = stock - p_quantity
    WHERE product_id = p_product_id;

    COMMIT;

    SELECT v_order_id AS order_id;
END //

DELIMITER ;
```

View phục vụ đọc:

```sql
CREATE VIEW order_summary AS
SELECT
    o.order_id,
    o.customer_id,
    o.total_amount,
    o.status,
    o.created_at,
    COUNT(oi.product_id) AS item_count
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.order_id
GROUP BY
    o.order_id,
    o.customer_id,
    o.total_amount,
    o.status,
    o.created_at;
```

Truy vấn:

```sql
SELECT *
FROM order_summary
WHERE customer_id = 100
ORDER BY created_at DESC;
```

---

# 8. Bảng quyết định nhanh

| Nhu cầu | Thành phần phù hợp |
|---|---|
| Tái sử dụng một câu `SELECT` | View |
| Tạo lớp dữ liệu cho báo cáo | View |
| Ẩn một số cột | View |
| Tính một giá trị trong biểu thức | Function |
| Chạy nhiều câu SQL theo quy trình | Procedure |
| Trả result set hoặc `OUT` value | Procedure |
| Tìm dòng nhanh hơn | Index |
| Chống trùng | Unique index |
| Lọc + sắp xếp hiệu quả | Composite index |
| Nhiều thay đổi phải đi cùng nhau | Transaction |
| Đọc rồi cập nhật an toàn | Transaction + locking |
| Chia rollback thành nhiều mốc | Savepoint |

---

# Checklist cuối cùng

## Khi định tạo view

```text
[ ] Query có bị lặp không?
[ ] Mục tiêu là đơn giản hóa, bảo mật hay reporting?
[ ] Có cần dữ liệu luôn mới không?
[ ] Có cần view cập nhật được không?
[ ] Bảng nguồn có index phù hợp chưa?
[ ] View có quá nhiều tầng không?
[ ] Đã chạy EXPLAIN chưa?
```

## Khi định tạo function

```text
[ ] Có đúng một giá trị trả về không?
[ ] Logic có thuần tính toán không?
[ ] Function bị gọi bao nhiêu lần?
[ ] Có query nặng bên trong không?
[ ] Có thể thay bằng biểu thức, JOIN hoặc generated column không?
[ ] Đã test NULL và giá trị biên chưa?
```

## Khi định tạo procedure

```text
[ ] Quy trình gồm những bước nào?
[ ] Ranh giới transaction ở đâu?
[ ] Input, output và error contract là gì?
[ ] Có gọi hệ thống ngoài không?
[ ] Có idempotency không?
[ ] Có handler rollback không?
[ ] Có index cho các query bên trong không?
[ ] Có test concurrent calls chưa?
```

## Khi định tạo index

```text
[ ] Query thực tế là gì?
[ ] WHERE và JOIN dùng cột nào?
[ ] Equality và range là gì?
[ ] Có ORDER BY và LIMIT không?
[ ] Query trả bao nhiêu phần trăm bảng?
[ ] Có cần unique không?
[ ] Leftmost prefix có đúng không?
[ ] Có index trùng không?
[ ] Đã chạy EXPLAIN ANALYZE chưa?
```

## Khi định dùng transaction

```text
[ ] Đơn vị nghiệp vụ hoàn chỉnh là gì?
[ ] Thay đổi nào phải atomic?
[ ] Có thao tác ngoài DB không?
[ ] Có bước đọc rồi cập nhật không?
[ ] Query khóa có index không?
[ ] Thứ tự lock có nhất quán không?
[ ] Có rollback và retry không?
[ ] Có idempotency không?
[ ] Transaction có đủ ngắn không?
```
