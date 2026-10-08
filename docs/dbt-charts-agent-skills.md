# dbt Charts Agent Skills cho repository

## Version và nguồn

Bộ skill được cài theo phạm vi repository tại `.agents/skills/dct-*` để Codex
tự tìm thấy khi mở project.

| Thành phần | Giá trị đã kiểm chứng ngày 2026-09-26 |
| --- | --- |
| Bản dbt Charts phát hành mới nhất | `dbt-charts==0.8.0` |
| Ngày phát hành trên PyPI | 2026-09-15 |
| Wheel đã đối chiếu | `dbt_charts-0.8.0-py3-none-any.whl` |
| SHA-256 của wheel | `8c502aa77bd1e13fe9eb0e8bf5f0642dac4d3409fbd308ac1236b49e46e1876c` |
| Nguồn chính thức | `dbt-labs/dbt-charts` |
| Giấy phép | Apache-2.0 |

Thông báo bản quyền của bộ Charts nằm tại
`.agents/skills/NOTICE.dbt-charts`; toàn văn Apache-2.0 dùng chung nằm tại
`.agents/skills/LICENSE`.

Wheel 0.8.0 chứa 24 tài liệu skill: 13 workflow, 10 pattern và một workflow
thử nghiệm chỉ dành cho tool surface. Cơ chế `dct init skills agents` chỉ cài
13 workflow được công bố trên CLI. Repository này cài đúng tập đó; không tự đưa
pattern nội bộ vào danh sách skill cấp repository.

Các file đã render được lấy từ commit
`742262c701c05a172541f48881c8e856f45d0fd4` của repository tham khảo
`tunguyenn99/i-test-dbt-platform`. Nội dung frontmatter và body của cả 13 file
đã được đối chiếu với install surface trong wheel chính thức 0.8.0 và khớp hoàn
toàn. Repository tham khảo chỉ đóng vai trò cung cấp output đã render; version
chuẩn của bộ skill được xác định từ artifact chính thức.

## Các skill đã cài

| Skill | Dùng khi |
| --- | --- |
| `dct-intro` | Bắt đầu một yêu cầu dbt Charts và chọn workflow tiếp theo |
| `dct-analyst-runbook` | Xác định câu hỏi, grain, metric và cách bàn giao phân tích |
| `dct-data-exploration` | Khám phá source, table, column và quan hệ trước khi viết board |
| `dct-board-design` | Chọn chart, hierarchy, layout và màu |
| `dct-board-build` | Viết hoặc sửa board YAML, query, validate và render |
| `dct-board-replicate` | Dựng lại dashboard từ ảnh hoặc bản export |
| `dct-board-review` | Điều phối structural review và visual review |
| `dct-board-structural-review` | Review YAML, data shape, variable và layout mà chưa render |
| `dct-board-visual-review` | Review ảnh render về bố cục, độ đọc và format |
| `dct-report-design` | Thiết kế báo cáo có narrative thay vì dashboard theo dõi |
| `dct-troubleshooting` | Sửa lỗi validate, SQL, query, render và variable |
| `dct-cloud-setup` | Thiết lập dbt Charts Cloud khi người dùng yêu cầu deploy |
| `dct-mcp-setup` | Thiết lập MCP server khi project quyết định dùng MCP |

Workflow mặc định cho dashboard mới:

```text
dct-intro
  → dct-analyst-runbook
  → dct-data-exploration
  → dct-board-design
  → dct-board-build
  → dct-board-review
```

Skill hướng dẫn cách agent làm việc; runtime được pin riêng trong
`pipeline/airflow/dbt-requirements.txt`.

## Repo tham khảo dùng version nào?

Repository `tunguyenn99/i-test-dbt-platform` không khóa version runtime:

- README tự mô tả transformation runtime là **dbt Core 1.xx**;
- lệnh setup là `uv pip install ... dbt-postgres`, không chỉ định version;
- lệnh setup Charts là `uv tool install dbt-charts`, không chỉ định version;
- repository không có lockfile hoặc requirements file khóa hai package này.

Vì vậy không thể kết luận chính xác version dbt hoặc `dct` đã chạy chỉ từ
repository đó. Nội dung 13 skill đã commit khớp dbt Charts 0.8.0, nhưng đây là
bằng chứng về **skill snapshot**, không phải bằng chứng về runtime đang được cài
trên máy tác giả.

## Runtime dbt Core của project

Các package được pin trong cùng virtualenv dbt của Airflow image:

- `dbt-core==1.11.15` build/test model và tạo `target/manifest.json`;
- `dbt-postgres==1.11.0` kết nối warehouse;
- `dbt-charts[postgresql]==0.8.0` cung cấp CLI `dct`, đọc manifest/profile và render.

Metadata của wheel 0.8.0 khai báo `dbt-core>=1.8,<2`; extra PostgreSQL khai báo
`dbt-postgres>=1.10,<2`. Các version trên thỏa cùng constraint nên project
không cần dbt v2 hoặc hai environment dbt khác nhau.

## Cập nhật bộ skill

Khi có release dbt Charts mới:

1. kiểm tra version mới nhất và SHA-256 của wheel chính thức trên PyPI;
2. đọc changelog và kiểm tra tập workflow mà `dct init skills agents` xuất ra;
3. thay toàn bộ `.agents/skills/dct-*` bằng output của cùng release;
4. cập nhật bảng version trong tài liệu này;
5. kiểm tra mọi tên `dct-*` được tham chiếu trong skill đều tồn tại.

Nguồn:

- [dbt Charts trên PyPI](https://pypi.org/project/dbt-charts/)
- [Repository chính thức dbt-labs/dbt-charts](https://github.com/dbt-labs/dbt-charts)
- [Repository được tham khảo](https://github.com/tunguyenn99/i-test-dbt-platform)
