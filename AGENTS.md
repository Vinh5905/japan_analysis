# Hướng dẫn cho agent trong japan_analysis

- Trước khi commit, chạy `make format` cho các file đang sửa và `make format-check`
  cùng phạm vi, rồi chạy `make format-staged` sau khi stage. Cài hook bằng
  `make format-setup` ở checkout mới. Không bỏ qua hook khi formatter báo lỗi.
  Style dùng 4 spaces, độ dài dòng mục tiêu 88; SQL dbt có Jinja dùng sqlfmt,
  SQL PostgreSQL dùng SQLFluff, Python dùng Ruff. Xem `docs/code-formatting.md`.

- Đọc `docs/agent_context.md` để nắm trạng thái project. Khi làm pipeline, đọc thêm `docs/pipeline-airflow-dbt.md`.
- Dự án dbt nằm ở `analytics/dbt`. Runtime hiện dùng dbt Core trong Docker Compose của `pipeline/`; kiểm tra `pipeline/Makefile` trước khi chạy lệnh.
- Các dbt skills của dbt Labs đã được cài theo phạm vi repository ở `.agents/skills/`. Với công việc dbt, chọn và đọc `SKILL.md` phù hợp với việc đang làm; xem danh sách và phiên bản nguồn tại `docs/dbt-agent-skills.md`.
- Các dbt Charts skills đã được cài theo phạm vi repository với prefix `dct-`. Khi bắt đầu công việc dashboard, đọc `dct-intro`, sau đó chọn `dct-board-design`, `dct-board-build` và skill review phù hợp. Xem nguồn, version và phạm vi cài đặt tại `docs/dbt-charts-agent-skills.md`.
- Các hướng dẫn upstream về dbt Cloud, MCP, Semantic Layer hoặc dbt Mesh chỉ áp dụng khi project đã cấu hình tính năng tương ứng. Hiện pipeline chính là batch → raw → staging → intermediate trên PostgreSQL.
