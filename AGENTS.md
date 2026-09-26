# Hướng dẫn cho agent trong japan_analysis

- Đọc `docs/agent_context.md` để nắm trạng thái project. Khi làm pipeline, đọc thêm `docs/pipeline-airflow-dbt.md`.
- Dự án dbt nằm ở `analytics/dbt`. Runtime hiện dùng dbt Core trong Docker Compose của `pipeline/`; kiểm tra `pipeline/Makefile` trước khi chạy lệnh.
- Các dbt skills của dbt Labs đã được cài theo phạm vi repository ở `.agents/skills/`. Với công việc dbt, chọn và đọc `SKILL.md` phù hợp với việc đang làm; xem danh sách và phiên bản nguồn tại `docs/dbt-agent-skills.md`.
- Các hướng dẫn upstream về dbt Cloud, MCP, Semantic Layer hoặc dbt Mesh chỉ áp dụng khi project đã cấu hình tính năng tương ứng. Hiện pipeline chính là batch → raw → staging → intermediate trên PostgreSQL.
