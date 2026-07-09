# Contribution Workflow

File này mô tả workflow chung khi chuẩn bị pull request. Agent hoặc contributor làm việc trong repository này phải đọc và tuân theo workflow này trước khi tạo branch, commit, hoặc pull request.

## Nguyên tắc chung

- Mỗi branch nên tập trung vào một mục tiêu rõ ràng.
- Pull request phải mô tả ngắn gọn thay đổi đã làm, lý do liên quan, và issue được đóng nếu có.
- Commit message phải tuân theo `docs/git-commit-convention.md`.
- Không đưa secret thật, credential cá nhân, token, hoặc dữ liệu nhạy cảm vào commit.
- Không trộn refactor lớn với thay đổi tính năng nếu không cần thiết.
- Nếu có test hoặc validation phù hợp, chạy trước khi mở pull request và ghi lại kết quả.

## Tạo branch

Đặt tên branch ngắn, rõ, có type hoặc mục tiêu.

Ví dụ:

```text
feat/add-export-command
fix/handle-empty-response
docs/add-pr-workflow
config/update-docker-cache
```

## Trước khi tạo pull request

Kiểm tra các điểm sau:

- Branch chỉ chứa thay đổi liên quan đến mục tiêu của pull request.
- Commit message đúng convention.
- Không có file local/cache/log/env không cần thiết.
- Đã chạy test, lint, build, hoặc validation phù hợp nếu có.
- Tài liệu liên quan đã được cập nhật nếu thay đổi ảnh hưởng cách dùng hoặc workflow.

## Pull Request Template

Template chính thức nằm ở `.github/PULL_REQUEST_TEMPLATE.md`. Khi tạo pull request trên GitHub, nội dung template này sẽ được tự động đưa vào phần mô tả PR.

Không copy template trực tiếp vào file workflow này. File workflow chỉ giải thích cách viết từng mục để contributor và agent hiểu cách điền template.

## Cách viết từng mục trong pull request

### `Closes`

Mục này dùng để liên kết pull request với issue. Nếu PR giải quyết hoàn toàn issue, dùng `Closes #<issue-number>` để GitHub tự đóng issue khi merge.

Nếu PR chỉ xử lý một phần issue, không dùng `Closes`. Thay vào đó ghi:

```text
Related to #123
```

### `What Changed`

Mục này trả lời câu hỏi: branch này đã thay đổi gì?

Nên viết theo kết quả:

```markdown
- Added shared Docker infrastructure.
- Updated service commands to separate build and run steps.
```

Không nên viết quá chung:

```markdown
- Updated files.
- Fixed things.
```

### `Validation`

Mục này ghi lại cách đã kiểm tra thay đổi. Ưu tiên command thật và kết quả ngắn.

Ví dụ:

```markdown
- `make infra-config` passed.
- `make -C suumo_source_crawler config` passed.
```

Nếu không chạy được, phải ghi rõ:

```markdown
- Not run: Docker daemon was not available.
```

### `Notes For Other Contributors`

Mục này dành cho thông tin người review, contributor, hoặc agent sau cần biết nhưng không nằm gọn trong `What Changed`.

Nên ghi:

- Cách chạy mới.
- Config/env mới.
- Migration hoặc dữ liệu cần chuẩn bị.
- Giới hạn hiện tại.
- Follow-up đã biết.
- Lý do chọn một tradeoff quan trọng.

Nếu không có gì đặc biệt:

```markdown
- No special notes.
```

Ví dụ nội dung phù hợp:

```markdown
- Run `make infra-up-d` before starting dependent services.
- The new config is intentionally unpinned until runtime behavior is stable.
- Follow-up: add integration tests after the external service contract is finalized.
```

## Quy tắc bắt buộc cho agent

Agent mới khi đọc context của repository phải xem `docs/git-commit-convention.md` và file này là quy tắc bắt buộc. Khi được yêu cầu tạo commit, branch, PR description, hoặc tài liệu liên quan workflow, agent phải tuân theo hai file này.
