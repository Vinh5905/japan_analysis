# Git Commit Convention

Tất cả commit trong repository nên dùng định dạng sau:

```text
<type>(<scope>): <short summary>
```

Ví dụ:

```text
feat(auth): add login form
fix(api): handle empty response
docs(readme): update setup guide
```

## Thành phần commit message

### `type`

`type` mô tả loại thay đổi chính của commit. Chỉ dùng một trong các giá trị sau:

| Type         | Ý nghĩa                                                                                            |
| ------------ | ---------------------------------------------------------------------------------------------------- |
| `feat`     | Thêm tính năng mới                                                                               |
| `fix`      | Sửa lỗi                                                                                            |
| `docs`     | Chỉ thay đổi tài liệu, không đổi hành vi hệ thống                                         |
| `style`    | Chỉ chỉnh format, khoảng trắng, dấu chấm phẩy, lint style; không đổi hành vi              |
| `refactor` | Thay đổi cấu trúc code nhưng không thêm tính năng và không sửa bug                       |
| `test`     | Thêm hoặc cập nhật test                                                                          |
| `chore`    | Việc phụ trợ như build, tooling, cleanup, dependency, script                                     |
| `config`   | Thay đổi cấu hình ứng dụng, môi trường, runtime, hoặc thiết lập hệ thống               |
| `content`  | Thay đổi dữ liệu nội dung, dữ liệu mẫu, tài nguyên, seed data, hoặc nội dung nghiệp vụ |
| `perf`     | Cải thiện hiệu năng                                                                              |

### `scope`

`scope` mô tả khu vực bị ảnh hưởng. Viết ngắn, chữ thường, dùng dấu gạch ngang nếu cần.

Ví dụ scope:

```text
api
auth
database
docker
docs
crawler
ui
tests
```

Nếu commit ảnh hưởng nhiều khu vực, chọn scope đại diện rõ nhất. Nếu thật sự không có scope phù hợp, dùng scope chung như `repo`, `core`, hoặc `infra`.

### `short summary`

`short summary` là mô tả ngắn gọn về thay đổi.

Quy tắc:

- Viết bằng tiếng Anh hoặc tiếng Việt đều được, nhưng nên thống nhất trong cùng repository.
- Dùng động từ ở dạng ngắn, trực tiếp.
- Không viết hoa chữ cái đầu nếu không phải tên riêng.
- Không kết thúc bằng dấu chấm.
- Giữ dưới khoảng 72 ký tự nếu có thể.
- Mô tả việc commit làm, không mô tả quá trình làm.

Ví dụ tốt:

```text
feat(crawler): add retry middleware
fix(database): handle missing migration table
docs(workflow): add pull request guide
chore(docker): update build cache settings
```

Ví dụ chưa tốt:

```text
update code
fix stuff
WIP
changes
feat: done
```

## Khi nào dùng từng type

### `feat`

Dùng khi commit thêm hành vi, tính năng, endpoint, màn hình, workflow, command, hoặc capability mới.

```text
feat(api): add export endpoint
```

### `fix`

Dùng khi commit sửa lỗi hoặc hành vi sai.

```text
fix(worker): retry failed jobs correctly
```

### `docs`

Dùng khi chỉ thay đổi tài liệu, comment hướng dẫn, README, convention, workflow.

```text
docs(convention): add commit message rules
```

### `style`

Dùng khi chỉ chỉnh định dạng code mà không đổi logic.

```text
style(ui): format component styles
```

### `refactor`

Dùng khi đổi cấu trúc code để dễ đọc, dễ bảo trì, giảm trùng lặp, nhưng không thêm tính năng và không sửa bug.

```text
refactor(service): split validation helpers
```

### `test`

Dùng khi thêm, sửa, hoặc tổ chức lại test.

```text
test(api): add coverage for error responses
```

### `chore`

Dùng cho công việc phụ trợ: tooling, script, dependency, cleanup, build setup, CI maintenance.

```text
chore(tooling): add lint command
```

### `config`

Dùng cho thay đổi cấu hình runtime, env, service, feature flag, Docker Compose, hoặc file config.

```text
config(docker): add shared network
```

### `content`

Dùng cho thay đổi dữ liệu nội dung hoặc tài nguyên mà hệ thống tiêu thụ: seed data, fixture, metadata, file nội dung, copy, taxonomy.

```text
content(seed): add default categories
```

### `perf`

Dùng khi mục tiêu chính là cải thiện tốc độ, giảm tài nguyên, tối ưu query, cache, hoặc throughput.

```text
perf(query): reduce duplicate database reads
```

## Body commit

Commit body là tùy chọn. Dùng body khi short summary chưa đủ giải thích lý do hoặc tác động.

Mẫu:

```text
fix(api): handle empty response

Return an empty list when the upstream response has no items instead of
raising an exception. This keeps the caller behavior consistent with
other empty-result cases.
```

Nên viết body khi:

- Commit có thay đổi hành vi đáng chú ý.
- Có migration, config, hoặc dữ liệu cần lưu ý.
- Có tradeoff hoặc quyết định kỹ thuật cần người sau hiểu.

## Breaking change

Nếu commit phá vỡ tương thích, thêm `!` sau type/scope và ghi rõ trong body.

```text
feat(api)!: change export response format

BREAKING CHANGE: export responses now return `items` instead of `data`.
Consumers must update parsing logic.
```

## Quy tắc bắt buộc cho agent

Agent khi tạo commit message phải đọc và tuân theo file này. Không dùng commit message chung chung như `update`, `fix`, `wip`, hoặc `changes`.
