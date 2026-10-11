# Định dạng code tự động

Project dùng indent **4 spaces**, độ dài dòng mục tiêu **88 ký tự**, UTF-8 và LF.
Makefile vẫn dùng tab ở recipe theo cú pháp của Make.

| Loại file                                         | Công cụ                              | Cấu hình           |
| ------------------------------------------------- | ------------------------------------ | ------------------ |
| Python                                            | Ruff format                          | `pyproject.toml`   |
| SQL trong `analytics/dbt`, gồm Jinja/macros/tests | sqlfmt                               | `pyproject.toml`   |
| SQL PostgreSQL bootstrap/migration                | SQLFluff, chỉ layout và keyword case | `.sqlfluff`        |
| YAML, JSON, Markdown, JS/TS, CSS, HTML            | Prettier                             | `.prettierrc.json` |

Prettier không có formatter Python/SQL tích hợp, nên dùng công cụ phù hợp cho
từng ngôn ngữ. Các phiên bản và dependency được khóa trong
`tools/format/requirements.txt` và `package-lock.json`. Chúng chỉ dùng ở máy
development, không thêm vào image Airflow/crawler/warehouse.

## Cài một lần cho mỗi checkout

Cần Python 3.12 trở lên và Node.js/npm. Chạy từ root repository:

```bash
make format-setup
```

Lệnh tạo `.venv-format`, cài dependency Python đã khóa, chạy `npm ci` và cài hook
`pre-commit` vào checkout hiện tại. Nếu cần chọn Python cụ thể:

```bash
make format-setup FORMAT_PYTHON=python3.12
```

## Các lệnh thường dùng

```bash
# Format toàn bộ source, gồm file mới chưa git add.
make format

# Chỉ kiểm tra, không sửa file; dùng được trong CI.
make format-check

# Format/kiểm tra riêng nhánh pipeline và dbt.
make format files="pipeline analytics/dbt"
make format-check files="pipeline analytics/dbt"

# Chạy hook với các file đã stage.
make format-staged

# Cài lại hook nếu checkout chưa có.
make format-hooks
```

Hook tự chạy khi `git commit`, chỉ xử lý các file trong commit. Nếu formatter
sửa file, pre-commit dừng commit để bạn đọc diff rồi `git add` lại những file
đã kiểm tra và commit lần nữa. Hook không tự stage file, không tạo commit và
không đưa các thay đổi khác đang ở working tree vào commit. pre-commit quản lý
phần sửa chưa stage khi file có cả thay đổi staged và unstaged.

Agent cũng phải chạy format/check cho các file đang sửa, rồi chạy hook trước
commit theo `AGENTS.md`.

## Phạm vi và cách viết

Không format cache/output/dbt packages, dữ liệu notebook, HTML snapshot, backup,
vendored code, guides và cấu hình charts. Notebook `.ipynb` giữ nguyên output;
formatter hiện không chạy vào notebook. Script dùng danh sách source từ Git và
quy tắc ignore, không quét dữ liệu runtime. Source SQL được xử lý trực tiếp,
không cần kết nối database hoặc chạy dbt để format.

88 ký tự là mục tiêu của formatter, không phải giới hạn cứng cho mọi literal.
Ruff giữ nội dung string/comment; nó không format SQL bên trong string Python.
Viết query dài thành triple-quoted string, chia cột, điều kiện và clause thành
dòng riêng, như `mlit_zoning_publication.py`. Thân hàm PL/pgSQL/dollar-quoted
cũng cần viết rõ với 4 spaces; formatter không sửa nội dung literal này.
SQLFluff báo những dòng SQL còn quá dài mà nó không tự sửa được để chỉnh rõ
ràng, thay vì che lỗi bằng cách bỏ qua kiểm tra.

Editor có hỗ trợ EditorConfig sẽ đọc `.editorconfig` để dùng đúng indent/LF.
Format khi lưu phụ thuộc editor và extension; hook trước commit vẫn chạy độc
lập với editor. Với VS Code, có thể bật format-on-save cho Python bằng extension
Ruff và cho YAML/JSON/Markdown bằng Prettier. SQL dbt dùng lệnh Makefile ở trên
để giữ cùng style với hook.

Tài liệu công cụ: [Ruff](https://docs.astral.sh/ruff/formatter/),
[sqlfmt](https://github.com/tconbeer/sqlfmt),
[SQLFluff](https://docs.sqlfluff.com/en/stable/configuration/layout.html),
[Prettier](https://prettier.io/docs/options),
[pre-commit](https://pre-commit.com/).
