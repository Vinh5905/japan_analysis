# MySQL Syntax Reference  
## Views, Functions, Stored Procedures, Indexes và Transactions

> Tài liệu tập trung vào **cú pháp**, sau mỗi khối cú pháp đều có phần giải thích từng thành phần và ví dụ hoàn chỉnh.  
> Cú pháp được viết theo MySQL 8.x, đối chiếu với MySQL 8.4 Reference Manual.

---

# Mục lục

1. [Quy ước đọc cú pháp](#1-quy-ước-đọc-cú-pháp)
2. [View syntax](#2-view-syntax)
3. [Function syntax](#3-function-syntax)
4. [Stored procedure syntax](#4-stored-procedure-syntax)
5. [Các câu lệnh bên trong stored routine](#5-các-câu-lệnh-bên-trong-stored-routine)
6. [Index syntax](#6-index-syntax)
7. [Transaction syntax](#7-transaction-syntax)
8. [Mẫu hoàn chỉnh kết hợp các thành phần](#8-mẫu-hoàn-chỉnh-kết-hợp-các-thành-phần)
9. [Cheat sheet](#9-cheat-sheet)
10. [Nguồn chính thức](#10-nguồn-chính-thức)

---

# 1. Quy ước đọc cú pháp

Trong tài liệu MySQL, cú pháp thường được viết như sau:

```text
COMMAND [optional_part] {choice_a | choice_b} item [, item] ...
```

Ý nghĩa:

+ `COMMAND`: từ khóa bắt buộc phải viết.
+ `[optional_part]`: phần nằm trong ngoặc vuông là **không bắt buộc**.
+ `{choice_a | choice_b}`: phải chọn một trong các lựa chọn bên trong.
+ `|`: có nghĩa là “hoặc”.
+ `...`: có thể lặp lại phần đứng trước nó.
+ `item [, item] ...`: có thể có một hoặc nhiều `item`, ngăn cách bằng dấu phẩy.
+ `name`: tên do người dùng tự đặt.
+ `type`: kiểu dữ liệu như `INT`, `BIGINT`, `VARCHAR(100)`, `DECIMAL(10,2)`.
+ Dấu `;`: kết thúc một câu SQL.
+ Từ khóa SQL không phân biệt chữ hoa/thường, nhưng thường viết hoa để dễ đọc.

Ví dụ:

```text
DROP VIEW [IF EXISTS] view_name [, view_name] ...
```

Có thể viết tối thiểu:

```sql
DROP VIEW active_users;
```

Hoặc dùng đầy đủ hơn:

```sql
DROP VIEW IF EXISTS active_users, completed_orders;
```

---

# 2. View syntax

## 2.1. `CREATE VIEW` — cú pháp đầy đủ

```sql
CREATE
    [OR REPLACE]
    [ALGORITHM = {UNDEFINED | MERGE | TEMPTABLE}]
    [DEFINER = user]
    [SQL SECURITY {DEFINER | INVOKER}]
    VIEW view_name [(column_list)]
    AS select_statement
    [WITH [CASCADED | LOCAL] CHECK OPTION];
```

## Giải thích từng thành phần

+ `CREATE`: bắt đầu câu lệnh tạo một database object mới.

+ `OR REPLACE`: nếu view đã tồn tại thì thay định nghĩa cũ bằng định nghĩa mới. Nếu view chưa tồn tại thì tạo mới.

+ `ALGORITHM`: chỉ định cách MySQL xử lý view.

+ `ALGORITHM = UNDEFINED`: không ép thuật toán; để MySQL quyết định dùng `MERGE` hay materialization.

+ `ALGORITHM = MERGE`: cố gắng gộp câu `SELECT` của view vào truy vấn bên ngoài.

+ `ALGORITHM = TEMPTABLE`: xử lý kết quả của view như một bảng trung gian trước khi truy vấn ngoài tiếp tục.

+ `DEFINER = user`: chỉ định tài khoản được coi là người định nghĩa view, ví dụ `'admin'@'localhost'`.

+ `SQL SECURITY DEFINER`: kiểm tra quyền dựa trên quyền của tài khoản `DEFINER`.

+ `SQL SECURITY INVOKER`: kiểm tra quyền dựa trên tài khoản đang gọi view.

+ `VIEW`: khai báo object sắp tạo là một view.

+ `view_name`: tên của view.

+ `column_list`: danh sách tên cột của view do người tạo chủ động đặt. Số tên phải khớp với số cột mà `SELECT` trả về.

+ `AS`: nối tên view với câu truy vấn định nghĩa view.

+ `select_statement`: câu `SELECT` tạo ra dữ liệu mà view biểu diễn.

+ `WITH CHECK OPTION`: khi `INSERT` hoặc `UPDATE` qua view, bắt buộc dữ liệu sau thay đổi vẫn thỏa điều kiện của view.

+ `LOCAL CHECK OPTION`: chỉ kiểm tra điều kiện của view hiện tại.

+ `CASCADED CHECK OPTION`: kiểm tra cả điều kiện của view hiện tại và các view bên dưới mà nó phụ thuộc. Đây là cách xử lý mặc định khi chỉ ghi `WITH CHECK OPTION`.

---

## 2.2. Cú pháp tối thiểu thường dùng

```sql
CREATE VIEW view_name AS
SELECT column_1, column_2
FROM table_name
WHERE condition;
```

Giải thích:

+ `CREATE VIEW view_name`: tạo một view có tên `view_name`.

+ `AS`: bắt đầu phần định nghĩa view.

+ `SELECT column_1, column_2`: xác định các cột xuất hiện trong view.

+ `FROM table_name`: xác định bảng nguồn.

+ `WHERE condition`: chỉ lấy các dòng thỏa điều kiện.

---

## 2.3. Ví dụ tạo view đơn giản

```sql
CREATE VIEW active_users AS
SELECT
    user_id,
    full_name,
    email
FROM users
WHERE status = 'active';
```

Giải thích từng dòng:

+ `CREATE VIEW active_users AS`: tạo view tên `active_users`.

+ `SELECT`: bắt đầu câu truy vấn định nghĩa dữ liệu của view.

+ `user_id`: đưa cột mã người dùng vào view.

+ `full_name`: đưa tên người dùng vào view.

+ `email`: đưa email vào view.

+ `FROM users`: dữ liệu gốc được lấy từ bảng `users`.

+ `WHERE status = 'active'`: view chỉ chứa những dòng đang có trạng thái `active`.

Sử dụng view:

```sql
SELECT *
FROM active_users;
```

+ `SELECT *`: lấy toàn bộ cột mà view cung cấp.

+ `FROM active_users`: sử dụng view như một nguồn dữ liệu gần giống bảng.

---

## 2.4. Tạo view với danh sách tên cột riêng

```sql
CREATE VIEW product_summary (
    id,
    name,
    final_price
) AS
SELECT
    product_id,
    product_name,
    price * 0.9
FROM products;
```

Giải thích:

+ `product_summary (...)`: tạo view và đặt tên rõ cho các cột đầu ra.

+ `id`: tên mới của cột `product_id`.

+ `name`: tên mới của cột `product_name`.

+ `final_price`: tên của kết quả biểu thức `price * 0.9`.

+ Số phần tử trong danh sách `(id, name, final_price)` phải bằng số biểu thức trong `SELECT`.

Cách khác là đặt alias ngay trong `SELECT`:

```sql
CREATE VIEW product_summary AS
SELECT
    product_id AS id,
    product_name AS name,
    price * 0.9 AS final_price
FROM products;
```

---

## 2.5. Tạo hoặc thay thế view

```sql
CREATE OR REPLACE VIEW active_users AS
SELECT
    user_id,
    full_name,
    email,
    created_at
FROM users
WHERE status = 'active';
```

Giải thích:

+ `CREATE OR REPLACE VIEW`: tạo mới hoặc thay thế view đã có.

+ Không xóa dữ liệu trong bảng `users`.

+ Chỉ định nghĩa của view bị thay đổi.

---

## 2.6. View với `ALGORITHM`

```sql
CREATE ALGORITHM = UNDEFINED VIEW completed_orders AS
SELECT
    order_id,
    customer_id,
    total_amount
FROM orders
WHERE status = 'completed';
```

Giải thích:

+ `ALGORITHM = UNDEFINED`: để optimizer tự chọn cách xử lý.

+ `VIEW completed_orders`: tên view.

+ `AS SELECT ...`: định nghĩa dữ liệu của view.

Ví dụ ép `MERGE`:

```sql
CREATE ALGORITHM = MERGE VIEW completed_orders AS
SELECT
    order_id,
    customer_id,
    total_amount
FROM orders
WHERE status = 'completed';
```

Ví dụ ép `TEMPTABLE`:

```sql
CREATE ALGORITHM = TEMPTABLE VIEW completed_orders AS
SELECT
    order_id,
    customer_id,
    total_amount
FROM orders
WHERE status = 'completed';
```

---

## 2.7. View với `SQL SECURITY`

```sql
CREATE
    DEFINER = 'report_admin'@'localhost'
    SQL SECURITY DEFINER
    VIEW public_employees AS
SELECT
    employee_id,
    full_name,
    department_id
FROM employees;
```

Giải thích:

+ `DEFINER = 'report_admin'@'localhost'`: tài khoản sở hữu ngữ cảnh quyền của view.

+ `SQL SECURITY DEFINER`: khi người khác gọi view, MySQL kiểm tra quyền theo `report_admin`.

+ `public_employees`: chỉ công khai các cột được liệt kê.

+ Các cột nhạy cảm như `salary` hoặc `bank_account` không xuất hiện trong view.

Dùng quyền của người gọi:

```sql
CREATE
    SQL SECURITY INVOKER
    VIEW active_users AS
SELECT
    user_id,
    full_name
FROM users
WHERE status = 'active';
```

+ `SQL SECURITY INVOKER`: tài khoản gọi view phải có quyền cần thiết đối với dữ liệu phía dưới.

---

## 2.8. View với `WITH CHECK OPTION`

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

Giải thích:

+ `WHERE status = 'active'`: view chỉ hiển thị sản phẩm active.

+ `WITH CHECK OPTION`: không cho phép cập nhật qua view khiến dòng trở thành `inactive`.

Ví dụ có thể bị từ chối:

```sql
UPDATE active_products
SET status = 'inactive'
WHERE product_id = 10;
```

---

## 2.9. `ALTER VIEW`

### Cú pháp

```sql
ALTER
    [ALGORITHM = {UNDEFINED | MERGE | TEMPTABLE}]
    [DEFINER = user]
    [SQL SECURITY {DEFINER | INVOKER}]
    VIEW view_name [(column_list)]
    AS select_statement
    [WITH [CASCADED | LOCAL] CHECK OPTION];
```

Giải thích:

+ `ALTER VIEW`: thay đổi định nghĩa của một view đang tồn tại.

+ Các thành phần còn lại có ý nghĩa tương tự `CREATE VIEW`.

Ví dụ:

```sql
ALTER VIEW active_users AS
SELECT
    user_id,
    full_name,
    email,
    created_at
FROM users
WHERE status = 'active';
```

---

## 2.10. `DROP VIEW`

### Cú pháp đầy đủ

```sql
DROP VIEW [IF EXISTS]
    view_name [, view_name] ...
    [RESTRICT | CASCADE];
```

Giải thích:

+ `DROP VIEW`: xóa định nghĩa view.

+ `IF EXISTS`: không báo lỗi nghiêm trọng nếu view không tồn tại; MySQL sinh note/warning.

+ `view_name`: tên view cần xóa.

+ `[, view_name] ...`: có thể xóa nhiều view trong một câu.

+ `RESTRICT | CASCADE`: MySQL nhận cú pháp này nhưng hiện không dùng nó để thay đổi hành vi xóa view.

Ví dụ:

```sql
DROP VIEW IF EXISTS active_users;
```

Xóa nhiều view:

```sql
DROP VIEW IF EXISTS
    active_users,
    completed_orders,
    public_employees;
```

Lưu ý:

```text
DROP VIEW chỉ xóa view.
Nó không xóa bảng nguồn và không xóa dữ liệu trong bảng nguồn.
```

---

## 2.11. Xem định nghĩa view

```sql
SHOW CREATE VIEW active_users;
```

Giải thích:

+ `SHOW CREATE VIEW`: yêu cầu MySQL hiển thị câu lệnh có thể dùng để tạo lại view.

+ `active_users`: view cần xem.

Xem metadata:

```sql
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    VIEW_DEFINITION,
    CHECK_OPTION,
    IS_UPDATABLE,
    SECURITY_TYPE
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'shop'
  AND TABLE_NAME = 'active_users';
```

---

## 2.12. Kiểm tra view

```sql
CHECK TABLE active_users;
```

Giải thích:

+ `CHECK TABLE`: kiểm tra object có vấn đề hay không.

+ Hữu ích khi bảng hoặc cột nguồn đã bị đổi tên hoặc bị xóa.

---

# 3. Function syntax

## 3.1. Cú pháp gọi built-in function

Cú pháp tổng quát:

```sql
function_name(argument_1, argument_2, ...);
```

Giải thích:

+ `function_name`: tên hàm.

+ `argument_1`: đối số đầu tiên.

+ `argument_2`: đối số thứ hai.

+ `...`: hàm có thể nhận thêm đối số tùy loại.

Ví dụ:

```sql
SELECT CONCAT(first_name, ' ', last_name)
FROM users;
```

+ `CONCAT(...)`: nối nhiều chuỗi thành một chuỗi.

+ `first_name`: đối số thứ nhất.

+ `' '`: chuỗi khoảng trắng.

+ `last_name`: đối số cuối.

---

## 3.2. Hàm không có đối số

```sql
SELECT NOW();
```

+ `NOW()`: trả về ngày giờ hiện tại theo ngữ cảnh của MySQL session.

```sql
SELECT DATABASE();
```

+ `DATABASE()`: trả về database đang được chọn.

---

## 3.3. Aggregate function

Cú pháp phổ biến:

```sql
aggregate_function([DISTINCT] expression);
```

Ví dụ:

```sql
SELECT COUNT(*)
FROM orders;
```

+ `COUNT(*)`: đếm số dòng.

Ví dụ:

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

+ `DISTINCT`: loại giá trị trùng trước khi đếm.

Ví dụ nhóm dữ liệu:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY customer_id;
```

+ `SUM(total_amount)`: cộng tiền của các dòng trong từng nhóm.

+ `AS total_spent`: đặt tên cho kết quả.

+ `GROUP BY customer_id`: gom các order có cùng khách hàng.

---

## 3.4. `CHARSET()` và `COLLATION()`

### Cú pháp

```sql
CHARSET(string_expression)
```

```sql
COLLATION(string_expression)
```

Giải thích:

+ `CHARSET(...)`: trả về character set của biểu thức chuỗi.

+ `COLLATION(...)`: trả về collation của biểu thức chuỗi.

+ `string_expression`: một chuỗi, cột chuỗi hoặc biểu thức trả về chuỗi.

Ví dụ:

```sql
SELECT
    CHARSET('Hello') AS character_set_name,
    COLLATION('Hello') AS collation_name;
```

Ví dụ với cột:

```sql
SELECT
    CHARSET(username),
    COLLATION(username)
FROM accounts
LIMIT 1;
```

Chỉ định rõ charset/collation cho literal:

```sql
SELECT
    CHARSET(
        _utf8mb4'Hello'
        COLLATE utf8mb4_0900_as_cs
    ),
    COLLATION(
        _utf8mb4'Hello'
        COLLATE utf8mb4_0900_as_cs
    );
```

Giải thích:

+ `_utf8mb4'Hello'`: character-set introducer; nói literal này dùng `utf8mb4`.

+ `COLLATE utf8mb4_0900_as_cs`: ép biểu thức dùng collation phân biệt dấu và hoa thường.

---

## 3.5. `CREATE FUNCTION` — stored function

### Cú pháp tổng quát

```sql
CREATE
    [DEFINER = user]
    FUNCTION [IF NOT EXISTS] function_name (
        [parameter_name data_type [, parameter_name data_type] ...]
    )
    RETURNS return_data_type
    [characteristic ...]
    routine_body;
```

Các `characteristic` có thể là:

```sql
COMMENT 'string'
LANGUAGE SQL
DETERMINISTIC
NOT DETERMINISTIC
CONTAINS SQL
NO SQL
READS SQL DATA
MODIFIES SQL DATA
SQL SECURITY DEFINER
SQL SECURITY INVOKER
```

Giải thích:

+ `CREATE FUNCTION`: tạo stored function.

+ `DEFINER = user`: tài khoản định nghĩa function.

+ `IF NOT EXISTS`: tránh lỗi tạo trùng trong những phiên bản MySQL hỗ trợ cú pháp này.

+ `function_name`: tên function.

+ `parameter_name data_type`: tham số đầu vào và kiểu dữ liệu.

+ Function parameter không khai báo `IN`, `OUT`, `INOUT`; function chỉ nhận đầu vào và trả một giá trị bằng `RETURN`.

+ `RETURNS return_data_type`: bắt buộc khai báo kiểu dữ liệu trả về.

+ `COMMENT 'string'`: mô tả function.

+ `LANGUAGE SQL`: routine được viết bằng SQL; hiện đây là lựa chọn ngôn ngữ của stored routine.

+ `DETERMINISTIC`: cùng đầu vào được khai báo là cho cùng đầu ra.

+ `NOT DETERMINISTIC`: kết quả có thể thay đổi dù đầu vào giống nhau.

+ `CONTAINS SQL`: routine có câu SQL nhưng không được khai báo cụ thể là đọc hoặc sửa dữ liệu.

+ `NO SQL`: khai báo routine không chứa SQL truy cập dữ liệu.

+ `READS SQL DATA`: routine có đọc dữ liệu nhưng không sửa dữ liệu.

+ `MODIFIES SQL DATA`: routine có thể sửa dữ liệu.

+ `SQL SECURITY DEFINER`: chạy theo quyền của definer.

+ `SQL SECURITY INVOKER`: chạy theo quyền của caller.

+ `routine_body`: một câu SQL hợp lệ hoặc khối `BEGIN ... END`.

---

## 3.6. Function một dòng

```sql
CREATE FUNCTION calculate_tax(
    p_amount DECIMAL(12, 2)
)
RETURNS DECIMAL(12, 2)
DETERMINISTIC
RETURN p_amount * 0.08;
```

Giải thích từng dòng:

+ `CREATE FUNCTION calculate_tax`: tạo function tên `calculate_tax`.

+ `p_amount DECIMAL(12, 2)`: nhận số tiền đầu vào.

+ `RETURNS DECIMAL(12, 2)`: kết quả trả về là số thập phân.

+ `DETERMINISTIC`: cùng `p_amount` sẽ cho cùng kết quả.

+ `RETURN p_amount * 0.08`: trả về 8% của số tiền.

Gọi function:

```sql
SELECT calculate_tax(1000000);
```

Dùng với cột:

```sql
SELECT
    order_id,
    total_amount,
    calculate_tax(total_amount) AS tax
FROM orders;
```

---

## 3.7. Function dùng `BEGIN ... END`

```sql
DELIMITER //

CREATE FUNCTION calculate_discount_price(
    p_price DECIMAL(10, 2),
    p_discount_percent DECIMAL(5, 2)
)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
BEGIN
    DECLARE v_result DECIMAL(10, 2);

    SET v_result =
        p_price * (1 - p_discount_percent / 100);

    RETURN v_result;
END //

DELIMITER ;
```

Giải thích từng dòng:

+ `DELIMITER //`: tạm đổi dấu kết thúc câu lệnh của MySQL client thành `//`.

+ `CREATE FUNCTION calculate_discount_price`: tạo function.

+ `p_price`: giá gốc.

+ `p_discount_percent`: phần trăm giảm giá.

+ `RETURNS DECIMAL(10, 2)`: kiểu dữ liệu của giá sau giảm.

+ `DETERMINISTIC`: cùng giá và phần trăm giảm sẽ cho cùng kết quả.

+ `BEGIN`: bắt đầu compound statement.

+ `DECLARE v_result`: khai báo biến cục bộ.

+ `SET v_result = ...`: gán kết quả tính toán cho biến.

+ `RETURN v_result`: trả về giá trị cuối cùng.

+ `END //`: kết thúc function và dùng `//` để báo cho client rằng toàn bộ lệnh đã xong.

+ `DELIMITER ;`: khôi phục dấu kết thúc mặc định.

---

## 3.8. `ALTER FUNCTION`

### Cú pháp

```sql
ALTER FUNCTION function_name
    [characteristic ...];
```

Các characteristic có thể thay đổi:

```sql
COMMENT 'string'
LANGUAGE SQL
CONTAINS SQL
NO SQL
READS SQL DATA
MODIFIES SQL DATA
SQL SECURITY DEFINER
SQL SECURITY INVOKER
```

Ví dụ:

```sql
ALTER FUNCTION calculate_tax
COMMENT 'Calculate tax using the current fixed tax rate'
SQL SECURITY DEFINER;
```

Lưu ý:

```text
ALTER FUNCTION không sửa parameter hoặc body.
Muốn sửa logic, thường phải DROP và CREATE lại function.
```

---

## 3.9. Xóa function

```sql
DROP FUNCTION [IF EXISTS] function_name;
```

Giải thích:

+ `DROP FUNCTION`: xóa stored function.

+ `IF EXISTS`: tránh lỗi nếu function không tồn tại.

+ `function_name`: tên function cần xóa.

Ví dụ:

```sql
DROP FUNCTION IF EXISTS calculate_tax;
```

---

## 3.10. Xem định nghĩa function

```sql
SHOW CREATE FUNCTION calculate_tax;
```

+ Hiển thị định nghĩa có thể dùng để tạo lại function.

Xem danh sách:

```sql
SELECT
    ROUTINE_SCHEMA,
    ROUTINE_NAME,
    ROUTINE_TYPE,
    DATA_TYPE,
    IS_DETERMINISTIC,
    SQL_DATA_ACCESS,
    SECURITY_TYPE
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_TYPE = 'FUNCTION'
  AND ROUTINE_SCHEMA = 'shop';
```

---

# 4. Stored procedure syntax

## 4.1. `CREATE PROCEDURE` — cú pháp đầy đủ

```sql
CREATE
    [DEFINER = user]
    PROCEDURE [IF NOT EXISTS] procedure_name (
        [procedure_parameter [, procedure_parameter] ...]
    )
    [characteristic ...]
    routine_body;
```

Trong đó:

```sql
procedure_parameter:
    [IN | OUT | INOUT] parameter_name data_type
```

Các characteristic:

```sql
COMMENT 'string'
LANGUAGE SQL
DETERMINISTIC
NOT DETERMINISTIC
CONTAINS SQL
NO SQL
READS SQL DATA
MODIFIES SQL DATA
SQL SECURITY DEFINER
SQL SECURITY INVOKER
```

Giải thích:

+ `CREATE PROCEDURE`: tạo stored procedure.

+ `procedure_name`: tên procedure.

+ `IN`: tham số chỉ dùng để đưa giá trị vào.

+ `OUT`: procedure ghi kết quả ra tham số này.

+ `INOUT`: vừa nhận giá trị đầu vào vừa ghi giá trị mới ra.

+ `parameter_name`: tên tham số.

+ `data_type`: kiểu dữ liệu.

+ `routine_body`: một câu SQL hoặc một khối `BEGIN ... END`.

---

## 4.2. Procedure chỉ có `IN`

```sql
DELIMITER //

CREATE PROCEDURE find_product(
    IN p_product_id BIGINT
)
BEGIN
    SELECT
        product_id,
        product_name,
        price,
        stock
    FROM products
    WHERE product_id = p_product_id;
END //

DELIMITER ;
```

Giải thích:

+ `IN p_product_id BIGINT`: caller truyền product ID vào procedure.

+ `SELECT ...`: procedure trả result set cho client.

+ `WHERE product_id = p_product_id`: so sánh cột trong bảng với tham số.

Gọi:

```sql
CALL find_product(10);
```

+ `CALL`: gọi stored procedure.

+ `find_product`: tên procedure.

+ `10`: đối số được gán vào `p_product_id`.

---

## 4.3. Procedure có `OUT`

```sql
DELIMITER //

CREATE PROCEDURE count_products(
    OUT p_total INT
)
BEGIN
    SELECT COUNT(*)
    INTO p_total
    FROM products;
END //

DELIMITER ;
```

Giải thích:

+ `OUT p_total INT`: procedure sẽ ghi một số nguyên ra ngoài.

+ `SELECT COUNT(*)`: đếm sản phẩm.

+ `INTO p_total`: lưu kết quả vào tham số `OUT`.

Gọi:

```sql
CALL count_products(@total);

SELECT @total;
```

Giải thích:

+ `@total`: user-defined session variable.

+ Không cần `DECLARE @total`.

+ `CALL count_products(@total)`: procedure ghi kết quả vào biến session.

+ `SELECT @total`: đọc kết quả sau khi procedure chạy.

---

## 4.4. Procedure có `INOUT`

```sql
DELIMITER //

CREATE PROCEDURE add_ten(
    INOUT p_number INT
)
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

Giải thích:

+ `SET @number = 5`: tạo và gán giá trị ban đầu cho biến session.

+ `INOUT`: procedure đọc `5`, cộng thêm `10`, sau đó ghi `15` trở lại.

---

## 4.5. `CALL` — cú pháp

```sql
CALL procedure_name([argument [, argument] ...]);
```

Giải thích:

+ `CALL`: gọi procedure đã được tạo.

+ `procedure_name`: tên procedure.

+ `argument`: giá trị, biểu thức hoặc biến truyền vào tham số.

+ Với `OUT` và `INOUT`, ở cấp SQL thường truyền một biến để có nơi nhận kết quả.

Ví dụ:

```sql
CALL create_order(100, 20, 2);
```

---

## 4.6. Procedure có đặc tính bảo mật

```sql
CREATE
    DEFINER = 'order_admin'@'localhost'
    PROCEDURE create_order(
        IN p_customer_id BIGINT,
        IN p_product_id BIGINT,
        IN p_quantity INT
    )
    MODIFIES SQL DATA
    SQL SECURITY DEFINER
BEGIN
    -- procedure body
END;
```

Giải thích:

+ `DEFINER`: tài khoản định nghĩa procedure.

+ `MODIFIES SQL DATA`: mô tả rằng procedure có thể sửa dữ liệu.

+ `SQL SECURITY DEFINER`: procedure chạy theo quyền của definer.

---

## 4.7. `ALTER PROCEDURE`

### Cú pháp

```sql
ALTER PROCEDURE procedure_name
    [characteristic ...];
```

Ví dụ:

```sql
ALTER PROCEDURE create_order
COMMENT 'Create one order and deduct product stock'
SQL SECURITY DEFINER;
```

Lưu ý:

```text
ALTER PROCEDURE không thay đổi parameter hoặc procedure body.
Muốn sửa logic, DROP và CREATE lại procedure.
```

---

## 4.8. Xóa procedure

```sql
DROP PROCEDURE [IF EXISTS] procedure_name;
```

Ví dụ:

```sql
DROP PROCEDURE IF EXISTS create_order;
```

---

## 4.9. Xem định nghĩa procedure

```sql
SHOW CREATE PROCEDURE create_order;
```

Xem metadata:

```sql
SELECT
    ROUTINE_SCHEMA,
    ROUTINE_NAME,
    ROUTINE_TYPE,
    SQL_DATA_ACCESS,
    SECURITY_TYPE,
    CREATED,
    LAST_ALTERED
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_TYPE = 'PROCEDURE'
  AND ROUTINE_SCHEMA = 'shop';
```

---

# 5. Các câu lệnh bên trong stored routine

## 5.1. `BEGIN ... END`

### Cú pháp

```sql
[block_label:] BEGIN
    statement_list
END [block_label];
```

Giải thích:

+ `block_label`: tên tùy chọn cho block.

+ `BEGIN`: bắt đầu khối lệnh.

+ `statement_list`: một hoặc nhiều câu lệnh.

+ `END`: kết thúc block.

Ví dụ:

```sql
BEGIN
    SET v_total = 0;
    SELECT COUNT(*) INTO v_total FROM products;
    SELECT v_total;
END
```

Lưu ý:

```text
BEGIN ... END trong stored routine tạo khối lệnh.
Nó không đồng nghĩa với BEGIN transaction.
```

---

## 5.2. `DECLARE` biến cục bộ

### Cú pháp

```sql
DECLARE variable_name [, variable_name] ...
    data_type
    [DEFAULT default_value];
```

Giải thích:

+ `DECLARE`: khai báo local variable.

+ `variable_name`: tên biến.

+ Có thể khai báo nhiều biến cùng kiểu trong một câu.

+ `data_type`: kiểu dữ liệu.

+ `DEFAULT`: giá trị khởi tạo.

+ Nếu không có `DEFAULT`, giá trị ban đầu là `NULL`.

Ví dụ:

```sql
DECLARE v_stock INT DEFAULT 0;
DECLARE v_price DECIMAL(10, 2);
DECLARE v_order_id BIGINT;
```

Thứ tự khai báo trong block:

```text
1. Variable và condition
2. Cursor
3. Handler
4. Các câu lệnh thực thi
```

Không hợp lệ:

```sql
BEGIN
    SET v_total = 10;
    DECLARE v_total INT;
END
```

`DECLARE` phải nằm ở đầu block trước các câu thực thi.

---

## 5.3. `SET`

### Cú pháp

```sql
SET variable_name = expression;
```

Có thể gán nhiều biến:

```sql
SET
    variable_1 = expression_1,
    variable_2 = expression_2;
```

Ví dụ:

```sql
SET v_total = v_price * p_quantity;
```

Session variable:

```sql
SET @total = 0;
```

Khác nhau:

```text
v_total
= local variable
= phải DECLARE trong stored program

@total
= session variable
= không dùng DECLARE
```

---

## 5.4. `SELECT ... INTO`

### Cú pháp thực tế

```sql
SELECT
    expression_1,
    expression_2
INTO
    variable_1,
    variable_2
FROM table_name
WHERE condition;
```

Ví dụ:

```sql
SELECT
    stock,
    price
INTO
    v_stock,
    v_price
FROM products
WHERE product_id = p_product_id;
```

Giải thích:

+ `SELECT stock, price`: lấy hai giá trị.

+ `INTO v_stock, v_price`: lưu lần lượt vào hai biến.

+ Số biến phải tương ứng với số biểu thức được chọn.

+ Truy vấn nên trả đúng một dòng.

---

## 5.5. `IF`

### Cú pháp

```sql
IF condition THEN
    statement_list
[ELSEIF condition THEN
    statement_list] ...
[ELSE
    statement_list]
END IF;
```

Giải thích:

+ `IF condition THEN`: nếu điều kiện đúng thì chạy block ngay sau.

+ `ELSEIF`: kiểm tra điều kiện khác nếu điều kiện trước sai.

+ `ELSE`: chạy khi tất cả điều kiện trước đều sai.

+ `END IF`: kết thúc cấu trúc điều kiện.

Ví dụ:

```sql
IF v_stock < p_quantity THEN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Not enough stock';
ELSEIF p_quantity <= 0 THEN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Quantity must be positive';
ELSE
    SET v_total = v_price * p_quantity;
END IF;
```

---

## 5.6. `CASE`

### Dạng so sánh một biểu thức

```sql
CASE case_value
    WHEN when_value THEN statement_list
    [WHEN when_value THEN statement_list] ...
    [ELSE statement_list]
END CASE;
```

Ví dụ:

```sql
CASE p_status
    WHEN 'pending' THEN
        SET v_priority = 10;
    WHEN 'failed' THEN
        SET v_priority = 100;
    ELSE
        SET v_priority = 0;
END CASE;
```

### Dạng điều kiện độc lập

```sql
CASE
    WHEN condition THEN statement_list
    [WHEN condition THEN statement_list] ...
    [ELSE statement_list]
END CASE;
```

Ví dụ:

```sql
CASE
    WHEN p_amount < 0 THEN
        SET v_category = 'invalid';
    WHEN p_amount < 1000000 THEN
        SET v_category = 'small';
    ELSE
        SET v_category = 'large';
END CASE;
```

---

## 5.7. `WHILE`

### Cú pháp

```sql
[loop_label:] WHILE condition DO
    statement_list
END WHILE [loop_label];
```

Ví dụ:

```sql
SET v_counter = 1;

WHILE v_counter <= 10 DO
    INSERT INTO numbers(value)
    VALUES (v_counter);

    SET v_counter = v_counter + 1;
END WHILE;
```

Giải thích:

+ Kiểm tra điều kiện trước mỗi vòng.

+ Nếu điều kiện sai ngay từ đầu, block không chạy lần nào.

---

## 5.8. `REPEAT`

### Cú pháp

```sql
[loop_label:] REPEAT
    statement_list
UNTIL condition
END REPEAT [loop_label];
```

Ví dụ:

```sql
SET v_counter = 1;

REPEAT
    INSERT INTO numbers(value)
    VALUES (v_counter);

    SET v_counter = v_counter + 1;
UNTIL v_counter > 10
END REPEAT;
```

Giải thích:

+ Block chạy trước.

+ Điều kiện được kiểm tra sau.

+ Vì vậy `REPEAT` chạy ít nhất một lần.

---

## 5.9. `LOOP`, `LEAVE`, `ITERATE`

### Cú pháp

```sql
loop_label: LOOP
    statement_list
END LOOP loop_label;
```

Thoát loop:

```sql
LEAVE loop_label;
```

Bỏ phần còn lại của vòng hiện tại và sang vòng tiếp:

```sql
ITERATE loop_label;
```

Ví dụ:

```sql
SET v_counter = 0;

number_loop: LOOP
    SET v_counter = v_counter + 1;

    IF v_counter = 5 THEN
        ITERATE number_loop;
    END IF;

    IF v_counter > 10 THEN
        LEAVE number_loop;
    END IF;

    INSERT INTO numbers(value)
    VALUES (v_counter);
END LOOP number_loop;
```

---

## 5.10. `DECLARE ... HANDLER`

### Cú pháp

```sql
DECLARE handler_action HANDLER
    FOR condition_value [, condition_value] ...
    handler_statement;
```

`handler_action`:

```sql
CONTINUE
EXIT
UNDO
```

`condition_value`:

```sql
mysql_error_code
SQLSTATE 'sqlstate_value'
condition_name
SQLWARNING
NOT FOUND
SQLEXCEPTION
```

Giải thích:

+ `CONTINUE`: xử lý lỗi xong rồi tiếp tục chương trình.

+ `EXIT`: xử lý lỗi xong rồi thoát block chứa handler.

+ `UNDO`: có trong grammar nhưng MySQL không hỗ trợ hành động này.

+ `SQLEXCEPTION`: bắt nhóm lỗi SQL thông thường, trừ success, warning và not found.

+ `SQLWARNING`: bắt warning.

+ `NOT FOUND`: thường dùng khi cursor đã đọc hết hoặc `SELECT ... INTO` không có dòng.

Ví dụ rollback khi có lỗi:

```sql
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
    ROLLBACK;
    RESIGNAL;
END;
```

Giải thích:

+ `EXIT HANDLER`: khi lỗi xảy ra, chạy block rồi thoát routine/block.

+ `ROLLBACK`: hủy transaction.

+ `RESIGNAL`: ném lại lỗi cho caller biết thao tác thất bại.

---

## 5.11. `SIGNAL`

### Cú pháp phổ biến

```sql
SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'error message';
```

Giải thích:

+ `SIGNAL`: chủ động phát sinh một lỗi.

+ `SQLSTATE '45000'`: mã SQLSTATE thường dùng cho lỗi do ứng dụng/nghiệp vụ tự định nghĩa.

+ `MESSAGE_TEXT`: nội dung lỗi trả về.

Ví dụ:

```sql
IF p_quantity <= 0 THEN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Quantity must be greater than zero';
END IF;
```

---

## 5.12. `RESIGNAL`

```sql
RESIGNAL;
```

Giải thích:

+ Ném lại condition hiện tại.

+ Thường dùng trong handler sau khi đã cleanup hoặc rollback.

Ví dụ:

```sql
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
    ROLLBACK;
    RESIGNAL;
END;
```

---

## 5.13. Cursor

### Khai báo cursor

```sql
DECLARE cursor_name CURSOR
    FOR select_statement;
```

### Mở cursor

```sql
OPEN cursor_name;
```

### Đọc một dòng

```sql
FETCH cursor_name
INTO variable_1 [, variable_2] ...;
```

### Đóng cursor

```sql
CLOSE cursor_name;
```

Ví dụ đầy đủ:

```sql
DELIMITER //

CREATE PROCEDURE process_pending_tasks()
BEGIN
    DECLARE v_done BOOLEAN DEFAULT FALSE;
    DECLARE v_task_id BIGINT;

    DECLARE task_cursor CURSOR FOR
        SELECT task_id
        FROM crawl_tasks
        WHERE status = 'pending';

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET v_done = TRUE;

    OPEN task_cursor;

    task_loop: LOOP
        FETCH task_cursor INTO v_task_id;

        IF v_done THEN
            LEAVE task_loop;
        END IF;

        UPDATE crawl_tasks
        SET status = 'queued'
        WHERE task_id = v_task_id;
    END LOOP;

    CLOSE task_cursor;
END //

DELIMITER ;
```

Lưu ý:

```text
Cursor thường chậm hơn xử lý set-based.
Trước khi dùng cursor, hãy thử giải quyết bằng một câu UPDATE/INSERT/SELECT theo tập hợp.
```

---

# 6. Index syntax

## 6.1. `CREATE INDEX` — cú pháp đầy đủ

```sql
CREATE [UNIQUE | FULLTEXT | SPATIAL] INDEX index_name
    [USING {BTREE | HASH}]
    ON table_name (
        key_part [, key_part] ...
    )
    [index_option ...]
    [ALGORITHM = {DEFAULT | INPLACE | COPY}]
    [LOCK = {DEFAULT | NONE | SHARED | EXCLUSIVE}];
```

Trong đó:

```sql
key_part:
    column_name [(prefix_length)] [ASC | DESC]
    |
    (expression) [ASC | DESC]
```

Một số `index_option`:

```sql
KEY_BLOCK_SIZE = value
USING {BTREE | HASH}
WITH PARSER parser_name
COMMENT 'string'
VISIBLE
INVISIBLE
ENGINE_ATTRIBUTE = 'string'
SECONDARY_ENGINE_ATTRIBUTE = 'string'
```

Giải thích:

+ `CREATE INDEX`: tạo index trên bảng đã có.

+ `UNIQUE`: ngăn hai key trùng nhau theo quy tắc so sánh của cột.

+ `FULLTEXT`: index phục vụ tìm kiếm toàn văn.

+ `SPATIAL`: index cho dữ liệu không gian.

+ Nếu không ghi loại trên, tạo normal secondary index.

+ `index_name`: tên index.

+ `USING BTREE`: dùng cấu trúc B-tree nếu storage engine hỗ trợ.

+ `USING HASH`: dùng hash index nếu storage engine hỗ trợ; InnoDB normal index không được thiết kế như một hash index do người dùng chọn tùy ý.

+ `ON table_name`: bảng cần tạo index.

+ `key_part`: một cột, prefix của cột, hoặc biểu thức.

+ `ASC | DESC`: thứ tự của key part.

+ `VISIBLE`: optimizer được phép xét index.

+ `INVISIBLE`: optimizer mặc định không dùng index, nhưng index vẫn được duy trì.

+ `ALGORITHM`: ảnh hưởng phương pháp thay đổi cấu trúc bảng.

+ `LOCK`: mức khóa mong muốn trong quá trình tạo index.

---

## 6.2. Normal index

```sql
CREATE INDEX idx_orders_customer
ON orders(customer_id);
```

Giải thích:

+ `idx_orders_customer`: tên index.

+ `orders`: bảng chứa index.

+ `customer_id`: cột được index.

---

## 6.3. Unique index

```sql
CREATE UNIQUE INDEX uk_users_email
ON users(email);
```

Giải thích:

+ `UNIQUE`: không cho hai giá trị email được xem là giống nhau theo collation của cột.

+ `uk_`: chỉ là quy ước đặt tên, không phải từ khóa.

---

## 6.4. Composite index

```sql
CREATE INDEX idx_tasks_run_status_scheduled
ON crawl_tasks(
    run_id,
    status,
    scheduled_at
);
```

Giải thích:

+ Index có ba key part theo đúng thứ tự.

+ Dữ liệu được tổ chức trước theo `run_id`.

+ Trong cùng `run_id`, tổ chức tiếp theo `status`.

+ Trong cùng tổ hợp `run_id + status`, tổ chức tiếp theo `scheduled_at`.

Phù hợp với query:

```sql
SELECT task_id, url
FROM crawl_tasks
WHERE run_id = 1001
  AND status = 'pending'
ORDER BY scheduled_at
LIMIT 100;
```

---

## 6.5. Descending index

```sql
CREATE INDEX idx_runs_source_started_desc
ON crawl_runs(
    source_id ASC,
    started_at DESC
);
```

Giải thích:

+ `source_id ASC`: tổ chức source tăng dần.

+ `started_at DESC`: trong mỗi source, thời gian mới nhất đứng trước.

Hữu ích cho:

```sql
SELECT *
FROM crawl_runs
WHERE source_id = 'suumo'
ORDER BY started_at DESC
LIMIT 1;
```

---

## 6.6. Prefix index

```sql
CREATE INDEX idx_task_url_prefix
ON crawl_tasks(url(100));
```

Giải thích:

+ `url(100)`: chỉ index 100 ký tự đầu của cột URL.

+ Với nonbinary string, số prefix được hiểu theo ký tự trong cú pháp khai báo.

+ Prefix index nhỏ hơn full-column index.

+ MySQL có thể phải kiểm tra dữ liệu thật khi nhiều chuỗi có cùng prefix.

---

## 6.7. Functional index

```sql
CREATE INDEX idx_orders_created_date
ON orders((DATE(created_at)));
```

Giải thích:

+ Biểu thức cần thêm một cặp ngoặc riêng: `((DATE(created_at)))`.

+ Index lưu kết quả của biểu thức `DATE(created_at)`.

Có thể phục vụ:

```sql
SELECT *
FROM orders
WHERE DATE(created_at) = '2026-07-21';
```

Tuy nhiên, range query trên cột gốc thường vẫn nên được cân nhắc:

```sql
WHERE created_at >= '2026-07-21 00:00:00'
  AND created_at <  '2026-07-22 00:00:00'
```

---

## 6.8. Full-text index

```sql
CREATE FULLTEXT INDEX ft_articles_title_content
ON articles(title, content);
```

Truy vấn:

```sql
SELECT *
FROM articles
WHERE MATCH(title, content)
      AGAINST('mysql index');
```

Giải thích:

+ `FULLTEXT`: tạo index theo token/từ.

+ `MATCH(...)`: các cột tham gia tìm kiếm.

+ `AGAINST(...)`: nội dung cần tìm.

---

## 6.9. Invisible index

```sql
CREATE INDEX idx_orders_status
ON orders(status)
INVISIBLE;
```

Giải thích:

+ Index vẫn được tạo và cập nhật khi dữ liệu thay đổi.

+ Optimizer mặc định không xét index.

+ Hữu ích để thử xem hệ thống có thể hoạt động tốt nếu bỏ index hay không.

Đổi visibility:

```sql
ALTER TABLE orders
ALTER INDEX idx_orders_status VISIBLE;
```

```sql
ALTER TABLE orders
ALTER INDEX idx_orders_status INVISIBLE;
```

---

## 6.10. Tạo index trong `CREATE TABLE`

```sql
CREATE TABLE orders (
    order_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL,

    PRIMARY KEY (order_id),

    INDEX idx_orders_customer (
        customer_id
    ),

    INDEX idx_orders_status_created (
        status,
        created_at
    ),

    UNIQUE KEY uk_orders_external_id (
        external_id
    )
) ENGINE = InnoDB;
```

Giải thích:

+ `PRIMARY KEY`: khai báo primary key ngay khi tạo bảng.

+ `INDEX`: normal index.

+ `UNIQUE KEY`: unique index.

+ Tạo index cùng bảng thường giúp schema được mô tả đầy đủ trong một migration.

---

## 6.11. Thêm index bằng `ALTER TABLE`

```sql
ALTER TABLE orders
ADD INDEX idx_orders_customer_created (
    customer_id,
    created_at
);
```

Unique:

```sql
ALTER TABLE users
ADD UNIQUE INDEX uk_users_email(email);
```

Primary key:

```sql
ALTER TABLE orders
ADD PRIMARY KEY(order_id);
```

Lưu ý:

```text
CREATE INDEX không phải cú pháp thông thường để thêm PRIMARY KEY.
Dùng CREATE TABLE hoặc ALTER TABLE ... ADD PRIMARY KEY.
```

---

## 6.12. `DROP INDEX`

### Cú pháp

```sql
DROP INDEX index_name
ON table_name
[ALGORITHM = {DEFAULT | INPLACE | COPY}]
[LOCK = {DEFAULT | NONE | SHARED | EXCLUSIVE}];
```

Giải thích:

+ `DROP INDEX`: xóa index.

+ `index_name`: tên index.

+ `ON table_name`: bảng chứa index.

Ví dụ:

```sql
DROP INDEX idx_orders_status
ON orders;
```

Cách tương đương:

```sql
ALTER TABLE orders
DROP INDEX idx_orders_status;
```

Xóa primary key:

```sql
ALTER TABLE orders
DROP PRIMARY KEY;
```

---

## 6.13. Xem index

```sql
SHOW INDEX FROM orders;
```

Hoặc:

```sql
SHOW INDEX FROM orders
FROM shop;
```

Một số cột cần đọc:

+ `Key_name`: tên index.

+ `Column_name`: cột trong index.

+ `Seq_in_index`: vị trí cột trong composite index.

+ `Non_unique = 0`: unique index.

+ `Non_unique = 1`: nonunique index.

+ `Cardinality`: ước tính số giá trị phân biệt.

+ `Visible`: index visible hay invisible.

---

## 6.14. Cập nhật statistics

```sql
ANALYZE TABLE orders;
```

Giải thích:

+ Cập nhật statistics để optimizer ước tính execution plan tốt hơn.

+ Không có nghĩa là tự động tạo index mới.

---

## 6.15. `EXPLAIN`

### Cú pháp thực tế

```sql
EXPLAIN
SELECT ...;
```

Chọn format:

```sql
EXPLAIN FORMAT = TRADITIONAL
SELECT ...;
```

```sql
EXPLAIN FORMAT = JSON
SELECT ...;
```

```sql
EXPLAIN FORMAT = TREE
SELECT ...;
```

Giải thích:

+ `EXPLAIN`: hiển thị kế hoạch MySQL dự kiến dùng.

+ `FORMAT`: định dạng kết quả.

+ `TRADITIONAL`: dạng bảng truyền thống.

+ `JSON`: thông tin dạng JSON.

+ `TREE`: cây execution plan.

---

## 6.16. `EXPLAIN ANALYZE`

```sql
EXPLAIN ANALYZE
SELECT *
FROM crawl_tasks
WHERE run_id = 1001
  AND status = 'pending'
ORDER BY scheduled_at
LIMIT 100;
```

Giải thích:

+ `EXPLAIN ANALYZE` thực sự chạy query.

+ Trả thêm thời gian và số dòng thực tế.

+ Cần cẩn thận với query nặng vì nó không chỉ ước tính.

---

# 7. Transaction syntax

## 7.1. Cú pháp điều khiển transaction

```sql
START TRANSACTION
    [transaction_characteristic
        [, transaction_characteristic] ...];

BEGIN [WORK];

COMMIT [WORK]
    [AND [NO] CHAIN]
    [[NO] RELEASE];

ROLLBACK [WORK]
    [AND [NO] CHAIN]
    [[NO] RELEASE];

SET autocommit = {0 | 1};
```

`transaction_characteristic`:

```sql
WITH CONSISTENT SNAPSHOT
READ WRITE
READ ONLY
```

---

## 7.2. `START TRANSACTION`

```sql
START TRANSACTION;
```

Giải thích:

+ Bắt đầu một transaction rõ ràng.

+ Các thay đổi sau đó chưa được xác nhận vĩnh viễn cho đến `COMMIT`.

+ Có thể hủy bằng `ROLLBACK`.

---

## 7.3. `BEGIN`

```sql
BEGIN;
```

Hoặc:

```sql
BEGIN WORK;
```

Giải thích:

+ Ở cấp SQL thông thường, là alias của `START TRANSACTION`.

+ Trong stored program, `BEGIN` thường được parser hiểu là bắt đầu `BEGIN ... END` block.

+ Vì vậy khi cần bắt đầu transaction trong stored procedure, nên viết rõ `START TRANSACTION`.

---

## 7.4. `COMMIT`

```sql
COMMIT;
```

Giải thích đúng theo yêu cầu:

+ `COMMIT`: dùng để lưu lại và xác nhận các thay đổi của transaction hiện tại.

+ Sau `COMMIT`, các thay đổi được coi là đã hoàn tất.

+ Các lock của transaction được giải phóng theo cơ chế của storage engine.

Cú pháp mở rộng:

```sql
COMMIT AND CHAIN;
```

+ `AND CHAIN`: commit transaction hiện tại rồi bắt đầu ngay transaction mới với đặc tính tương ứng.

```sql
COMMIT AND NO CHAIN;
```

+ `NO CHAIN`: không tự bắt đầu transaction mới.

```sql
COMMIT RELEASE;
```

+ `RELEASE`: kết thúc transaction rồi ngắt session hiện tại.

---

## 7.5. `ROLLBACK`

```sql
ROLLBACK;
```

Giải thích:

+ `ROLLBACK`: hủy các thay đổi chưa commit của transaction hiện tại.

+ Dùng khi có lỗi hoặc khi nghiệp vụ không đủ điều kiện hoàn tất.

Cú pháp mở rộng:

```sql
ROLLBACK AND CHAIN;
```

+ Rollback transaction hiện tại rồi bắt đầu transaction mới.

```sql
ROLLBACK RELEASE;
```

+ Rollback rồi đóng connection.

---

## 7.6. `autocommit`

```sql
SET autocommit = 0;
```

Giải thích:

+ Tắt chế độ tự commit trong session hiện tại.

+ Sau đó các thay đổi trên transactional table cần `COMMIT` hoặc `ROLLBACK`.

Bật lại:

```sql
SET autocommit = 1;
```

Giải thích:

+ Bật chế độ mỗi câu độc lập được commit tự động khi không nằm trong explicit transaction.

+ Việc chuyển từ `0` sang `1` có thể kết thúc transaction đang chờ theo quy tắc implicit commit, vì vậy không nên thay đổi tùy tiện giữa workflow.

Kiểm tra:

```sql
SELECT @@session.autocommit;
```

---

## 7.7. Transaction cơ bản

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

Giải thích từng dòng:

+ `START TRANSACTION`: mở transaction.

+ `UPDATE ... account_id = 1`: trừ tiền tài khoản nguồn.

+ `UPDATE ... account_id = 2`: cộng tiền tài khoản đích.

+ `COMMIT`: chỉ xác nhận khi cả hai bước thành công.

Khi lỗi:

```sql
ROLLBACK;
```

---

## 7.8. `SAVEPOINT`

### Cú pháp

```sql
SAVEPOINT savepoint_name;
```

```sql
ROLLBACK [WORK] TO [SAVEPOINT] savepoint_name;
```

```sql
RELEASE SAVEPOINT savepoint_name;
```

Giải thích:

+ `SAVEPOINT`: tạo một mốc bên trong transaction.

+ `ROLLBACK TO SAVEPOINT`: hủy các thay đổi sau mốc nhưng không kết thúc toàn bộ transaction.

+ `RELEASE SAVEPOINT`: xóa mốc; không commit và cũng không rollback.

Ví dụ:

```sql
START TRANSACTION;

INSERT INTO orders(customer_id, status)
VALUES (100, 'created');

SAVEPOINT order_created;

INSERT INTO optional_order_notes(order_id, note)
VALUES (LAST_INSERT_ID(), 'Priority customer');

ROLLBACK TO SAVEPOINT order_created;

COMMIT;
```

Kết quả:

```text
Order được giữ.
Order note bị hủy.
```

---

## 7.9. Isolation level

### Cú pháp thực tế

Cho transaction tiếp theo:

```sql
SET TRANSACTION
ISOLATION LEVEL READ COMMITTED;
```

Cho session:

```sql
SET SESSION TRANSACTION
ISOLATION LEVEL REPEATABLE READ;
```

Cho mặc định global, cần quyền phù hợp:

```sql
SET GLOBAL TRANSACTION
ISOLATION LEVEL READ COMMITTED;
```

Các mức:

```sql
READ UNCOMMITTED
READ COMMITTED
REPEATABLE READ
SERIALIZABLE
```

Ví dụ:

```sql
SET TRANSACTION
ISOLATION LEVEL READ COMMITTED;

START TRANSACTION;

SELECT *
FROM orders
WHERE customer_id = 100;

COMMIT;
```

Giải thích:

+ `SET TRANSACTION`: đặt đặc tính cho transaction kế tiếp.

+ `ISOLATION LEVEL`: bắt đầu khai báo mức cô lập.

+ `READ COMMITTED`: mỗi consistent read nhìn dữ liệu đã commit theo quy tắc của mức này.

---

## 7.10. Transaction access mode

```sql
START TRANSACTION READ ONLY;
```

Giải thích:

+ Khai báo transaction chủ yếu chỉ đọc.

```sql
START TRANSACTION READ WRITE;
```

Giải thích:

+ Cho phép transaction thực hiện thao tác ghi theo quyền và trạng thái server.

Consistent snapshot:

```sql
START TRANSACTION WITH CONSISTENT SNAPSHOT;
```

Giải thích:

+ Yêu cầu tạo consistent read snapshot ngay khi bắt đầu trong trường hợp isolation/storage engine hỗ trợ ý nghĩa này.

---

## 7.11. `SELECT ... FOR UPDATE`

### Cú pháp thực tế

```sql
SELECT column_list
FROM table_name
WHERE condition
FOR UPDATE;
```

Giải thích:

+ `FOR UPDATE`: locking read dành cho các dòng mà transaction dự định cập nhật.

+ Lock được giữ đến `COMMIT` hoặc `ROLLBACK`.

Ví dụ:

```sql
START TRANSACTION;

SELECT stock
FROM products
WHERE product_id = 10
FOR UPDATE;

UPDATE products
SET stock = stock - 1
WHERE product_id = 10;

COMMIT;
```

---

## 7.12. `FOR SHARE`

```sql
SELECT column_list
FROM table_name
WHERE condition
FOR SHARE;
```

Giải thích:

+ Lấy shared lock trên các dòng đọc được.

+ Transaction khác có thể đọc, nhưng việc sửa dòng sẽ bị hạn chế/chờ cho đến khi lock được giải phóng.

Cú pháp cũ tương đương để tương thích:

```sql
SELECT ...
LOCK IN SHARE MODE;
```

---

## 7.13. `NOWAIT`

```sql
SELECT *
FROM products
WHERE product_id = 10
FOR UPDATE NOWAIT;
```

Giải thích:

+ Không chờ nếu dòng đang bị transaction khác khóa.

+ Trả lỗi ngay lập tức.

---

## 7.14. `SKIP LOCKED`

```sql
SELECT task_id
FROM crawl_tasks
WHERE status = 'pending'
ORDER BY scheduled_at
LIMIT 100
FOR UPDATE SKIP LOCKED;
```

Giải thích:

+ Bỏ qua các dòng đang bị khóa.

+ Không chờ các worker khác.

+ Phù hợp cho queue/worker pattern.

+ Không phù hợp cho mọi nghiệp vụ vì kết quả cố ý bỏ qua một phần dữ liệu đang bị lock.

---

## 7.15. Mẫu transaction trong stored procedure

```sql
DELIMITER //

CREATE PROCEDURE transfer_money(
    IN p_from_account_id BIGINT,
    IN p_to_account_id BIGINT,
    IN p_amount DECIMAL(15, 2)
)
BEGIN
    DECLARE v_balance DECIMAL(15, 2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT balance
    INTO v_balance
    FROM accounts
    WHERE account_id = p_from_account_id
    FOR UPDATE;

    IF v_balance < p_amount THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Insufficient balance';
    END IF;

    UPDATE accounts
    SET balance = balance - p_amount
    WHERE account_id = p_from_account_id;

    UPDATE accounts
    SET balance = balance + p_amount
    WHERE account_id = p_to_account_id;

    COMMIT;
END //

DELIMITER ;
```

Giải thích theo trình tự:

+ Khai báo input.

+ Khai báo biến local.

+ Khai báo error handler.

+ Mở transaction.

+ Lock và đọc tài khoản nguồn.

+ Kiểm tra số dư.

+ Trừ tiền.

+ Cộng tiền.

+ Commit khi tất cả thành công.

+ Nếu có exception: rollback và ném lại lỗi.

---

## 7.16. DDL và transaction

Các câu như:

```sql
CREATE TABLE
ALTER TABLE
DROP TABLE
CREATE INDEX
TRUNCATE TABLE
```

có thể gây implicit commit.

Không nên viết và kỳ vọng rollback nghiệp vụ như sau:

```sql
START TRANSACTION;

UPDATE products
SET price = 1000
WHERE product_id = 10;

ALTER TABLE products
ADD COLUMN note TEXT;

ROLLBACK;
```

Nên tách:

```text
Schema migration
khỏi
Business transaction
```

---

# 8. Mẫu hoàn chỉnh kết hợp các thành phần

## 8.1. Tạo bảng và index

```sql
CREATE TABLE products (
    product_id BIGINT NOT NULL AUTO_INCREMENT,
    product_name VARCHAR(200) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    stock INT NOT NULL,
    status VARCHAR(20) NOT NULL,

    PRIMARY KEY(product_id),

    INDEX idx_products_status(status)
) ENGINE = InnoDB;
```

```sql
CREATE TABLE orders (
    order_id BIGINT NOT NULL AUTO_INCREMENT,
    customer_id BIGINT NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL,

    PRIMARY KEY(order_id),

    INDEX idx_orders_customer_created(
        customer_id,
        created_at DESC
    ),

    INDEX idx_orders_status_created(
        status,
        created_at
    )
) ENGINE = InnoDB;
```

```sql
CREATE TABLE order_items (
    order_item_id BIGINT NOT NULL AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,

    PRIMARY KEY(order_item_id),

    INDEX idx_order_items_order(order_id),

    INDEX idx_order_items_product(product_id)
) ENGINE = InnoDB;
```

---

## 8.2. Tạo function

```sql
DELIMITER //

CREATE FUNCTION calculate_line_total(
    p_unit_price DECIMAL(12, 2),
    p_quantity INT
)
RETURNS DECIMAL(12, 2)
DETERMINISTIC
NO SQL
RETURN p_unit_price * p_quantity //

DELIMITER ;
```

---

## 8.3. Tạo procedure có transaction

```sql
DELIMITER //

CREATE PROCEDURE create_order(
    IN p_customer_id BIGINT,
    IN p_product_id BIGINT,
    IN p_quantity INT,
    OUT p_order_id BIGINT
)
MODIFIES SQL DATA
SQL SECURITY DEFINER
BEGIN
    DECLARE v_stock INT;
    DECLARE v_price DECIMAL(12, 2);
    DECLARE v_total DECIMAL(12, 2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_quantity <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Quantity must be greater than zero';
    END IF;

    START TRANSACTION;

    SELECT
        stock,
        price
    INTO
        v_stock,
        v_price
    FROM products
    WHERE product_id = p_product_id
      AND status = 'active'
    FOR UPDATE;

    IF v_stock < p_quantity THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Not enough stock';
    END IF;

    SET v_total =
        calculate_line_total(v_price, p_quantity);

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

    SET p_order_id = LAST_INSERT_ID();

    INSERT INTO order_items (
        order_id,
        product_id,
        quantity,
        unit_price
    )
    VALUES (
        p_order_id,
        p_product_id,
        p_quantity,
        v_price
    );

    UPDATE products
    SET stock = stock - p_quantity
    WHERE product_id = p_product_id;

    COMMIT;
END //

DELIMITER ;
```

Gọi:

```sql
CALL create_order(
    100,
    20,
    2,
    @new_order_id
);

SELECT @new_order_id;
```

---

## 8.4. Tạo view cho việc đọc

```sql
CREATE ALGORITHM = UNDEFINED VIEW order_summary AS
SELECT
    o.order_id,
    o.customer_id,
    o.total_amount,
    o.status,
    o.created_at,
    COUNT(oi.order_item_id) AS item_count
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

Kiểm tra plan:

```sql
EXPLAIN ANALYZE
SELECT *
FROM order_summary
WHERE customer_id = 100
ORDER BY created_at DESC;
```

---

# 9. Cheat sheet

## View

```sql
CREATE VIEW view_name AS
SELECT ...;
```

```sql
CREATE OR REPLACE VIEW view_name AS
SELECT ...;
```

```sql
ALTER VIEW view_name AS
SELECT ...;
```

```sql
DROP VIEW IF EXISTS view_name;
```

```sql
SHOW CREATE VIEW view_name;
```

---

## Stored function

```sql
CREATE FUNCTION function_name(parameters)
RETURNS data_type
DETERMINISTIC
RETURN expression;
```

```sql
SELECT function_name(arguments);
```

```sql
DROP FUNCTION IF EXISTS function_name;
```

```sql
SHOW CREATE FUNCTION function_name;
```

---

## Stored procedure

```sql
CREATE PROCEDURE procedure_name(
    IN input_parameter data_type,
    OUT output_parameter data_type,
    INOUT both_parameter data_type
)
BEGIN
    statements;
END;
```

```sql
CALL procedure_name(arguments);
```

```sql
DROP PROCEDURE IF EXISTS procedure_name;
```

```sql
SHOW CREATE PROCEDURE procedure_name;
```

---

## Local variable

```sql
DECLARE v_name data_type DEFAULT value;
```

```sql
SET v_name = expression;
```

```sql
SELECT column
INTO v_name
FROM table_name
WHERE condition;
```

---

## Handler

```sql
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
    ROLLBACK;
    RESIGNAL;
END;
```

---

## Index

```sql
CREATE INDEX index_name
ON table_name(column_name);
```

```sql
CREATE UNIQUE INDEX index_name
ON table_name(column_name);
```

```sql
CREATE INDEX index_name
ON table_name(column_1, column_2, column_3);
```

```sql
DROP INDEX index_name
ON table_name;
```

```sql
SHOW INDEX FROM table_name;
```

```sql
EXPLAIN ANALYZE
SELECT ...;
```

---

## Transaction

```sql
START TRANSACTION;
```

```sql
COMMIT;
```

```sql
ROLLBACK;
```

```sql
SAVEPOINT savepoint_name;
```

```sql
ROLLBACK TO SAVEPOINT savepoint_name;
```

```sql
RELEASE SAVEPOINT savepoint_name;
```

```sql
SELECT ...
FOR UPDATE;
```

```sql
SELECT ...
FOR UPDATE SKIP LOCKED;
```

---

# 10. Nguồn chính thức

- MySQL 8.4 — CREATE VIEW:  
  https://dev.mysql.com/doc/refman/8.4/en/create-view.html

- MySQL 8.4 — View syntax and processing:  
  https://dev.mysql.com/doc/refman/8.4/en/views.html

- MySQL 8.4 — Stored routines:  
  https://dev.mysql.com/doc/refman/8.4/en/stored-routines-syntax.html

- MySQL 8.4 — Local variables:  
  https://dev.mysql.com/doc/refman/8.4/en/declare-local-variable.html

- MySQL 8.4 — Condition handlers:  
  https://dev.mysql.com/doc/refman/8.4/en/declare-handler.html

- MySQL 8.4 — CREATE INDEX:  
  https://dev.mysql.com/doc/refman/8.4/en/create-index.html

- MySQL 8.4 — EXPLAIN:  
  https://dev.mysql.com/doc/refman/8.4/en/explain.html

- MySQL 8.4 — Transaction control:  
  https://dev.mysql.com/doc/refman/8.4/en/commit.html

- MySQL 8.4 — SAVEPOINT:  
  https://dev.mysql.com/doc/refman/8.4/en/savepoint.html

- MySQL 8.4 — Locking reads:  
  https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html
