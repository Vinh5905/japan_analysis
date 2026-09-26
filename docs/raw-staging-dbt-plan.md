# Hoàn thiện luồng batch → raw → staging bằng dbt

## Tóm tắt

Chuyển các rule xử lý đang dùng trong `02_column_eda.ipynb` sang dbt cho **lịch sử listing**. Raw giữ JSON gốc để truy vết; staging đổi tên cột sang tiếng Anh, lọc cột theo Bước 4 của notebook và tạo các cột đã xử lý. Từ ngày 2026-09-25, snapshot 17.927 record được nạp thành raw seed riêng để bootstrap analytics; raw operational vẫn do loader quản lý.

**Bước đầu tiên khi bắt đầu thực hiện:** ghi nguyên kế hoạch này vào `docs/raw-staging-dbt-plan.md` trước khi sửa code.

## Thay đổi

- **Nạp batch vào raw:** giữ schema `raw.suumo_parser_records` và quy tắc chỉ nạp record `is_valid = true`. Kiểm tra hash của file gzip, `row_count`, cấu trúc record và `task_id` trước khi ghi. Ghi các record hợp lệ trong một transaction; lỗi ghi khiến cả batch thất bại, còn record `is_valid = false` được tính vào `failed_count` như hiện tại. Giữ upsert theo `task_id` để chạy lại an toàn.
- **Phục hồi batch:** thêm lệnh vận hành đưa một batch `failed`, hoặc batch `loading` đã quá hạn, về `pending` sau khi kiểm tra trạng thái. Không tự retry batch lỗi. Airflow tiếp tục chạy dbt cho các batch nạp thành công trong cùng lượt, nhưng báo DAG thất bại nếu có batch load thất bại.
- **Staging dbt:** thay model test hiện tại bằng `staging.stg_suumo_rentals` dạng table, một dòng cho mỗi `task_id`. Dùng các model trung gian và SQL macro PostgreSQL để tái tạo rule notebook: chuẩn hóa NFKC và sentinel theo từng cột; parse tiền, ngày, hợp đồng, địa chỉ, ga, layout, diện tích, tầng, bảo hiểm và parking; tính chi phí, giá/m² và cờ chất lượng. Kết quả giữ 41 cột được chọn ở Bước 4 cùng 77 cột phát sinh trong clean history; các trường `DEFERRED/SKIP` chỉ giữ raw text, không tạo chỉ số phân tích.
- **Model test cũ:** xóa model mart hiện tại và test của nó. Sau khi staging mới được xác nhận, xóa riêng table `mart.mart_suumo_rentals_current` cũ để tránh dùng nhầm dữ liệu test. Cập nhật tài liệu pipeline và agent context theo luồng mới.

## Kiểm thử và nghiệm thu

- Test loader với file đúng, sai hash, sai số record, record không hợp lệ, lỗi ghi warehouse và chạy lại batch; xác nhận trạng thái và số đếm ở source DB.
- Test dbt bằng dữ liệu mẫu cho từng nhóm rule, nhất là giá trị thiếu, ký tự fullwidth, khoảng tầng, năm xây chỉ có năm, nhiều tuyến ga và layout parse một phần.
- Database QA tạm vẫn dùng để đối chiếu parser. Ngoài ra, raw CSV đã được copy thành dbt seed phục vụ local analytics; staging giữ `record_origin` và ưu tiên operational nếu trùng task.
- Chạy lại `dbt run` để xác nhận kết quả ổn định, rồi kiểm tra tài liệu và `git diff --check`.

## Giả định đã chốt

- Notebook hiện tại là nguồn chuẩn cho quy tắc xử lý; không tự thêm rule cho các cột đã đánh dấu `DEFERRED/SKIP`.
- Raw warehouse vẫn chỉ lưu parser record hợp lệ. Dữ liệu local hiện có đủ cho smoke test; snapshot notebook dùng để kiểm tra độ khớp, không phải yêu cầu backfill.
- Batch lỗi được đưa về `pending` bằng thao tác thủ công có kiểm tra. Mart/current và bảng chi tiết một-nhiều sẽ làm ở đợt sau.

## Cập nhật kiến trúc sau nghiệm thu

Kế hoạch trên ghi lại yêu cầu của đợt triển khai ban đầu. Sau khi rà soát lại
vai trò tầng dbt, bảng lịch sử được chuyển sang
`intermediate.int_suumo_rentals_history`. View
`staging.stg_suumo_parser_records` là entry point một-một từ raw; các phép
parse, tổng hợp và join nằm ở intermediate. Xem `docs/pipeline-airflow-dbt.md`
cho kiến trúc và lệnh vận hành hiện tại.
