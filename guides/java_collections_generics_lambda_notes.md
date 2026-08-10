# Java Collections, Generics và Lambda Expressions

> Tài liệu tổng hợp từ đầu đến cuối ba phần: **Collections**, **Generics** và **Lambda Expressions**.
> Mục tiêu là hiểu bản chất, biết cách lựa chọn trong thực tế và tránh các lỗi thường gặp.

---

## Mục lục

1. [Collections Framework](#phần-i-collections-framework)
2. [Generics](#phần-ii-generics)
3. [Lambda Expressions](#phần-iii-lambda-expressions)
4. [Mối liên hệ giữa Collections, Generics và Lambda](#phần-iv-mối-liên-hệ-giữa-collections-generics-và-lambda)

---

# Phần I. Collections Framework

## 1. Collection trong Java thực chất là gì?

Hiểu đơn giản:

> **Collection là một cấu trúc dùng để quản lý một nhóm đối tượng trong bộ nhớ.**

Nhưng hiểu sâu hơn, **Java Collections Framework** không phải chỉ là một class. Nó là một hệ thống gồm:

1. **Interface**: quy định collection có khả năng làm gì.
2. **Implementation class**: quy định dữ liệu thực sự được lưu như thế nào.
3. **Thuật toán và utility**: sắp xếp, tìm kiếm, đảo thứ tự, lấy min/max...
4. **Quy ước**: cách so sánh phần tử, loại bỏ trùng lặp, duyệt dữ liệu...

Ví dụ:

```java
List<String> languages = new ArrayList<>();
```

Dòng này có bốn thành phần:

```text
List          <String>       languages       new ArrayList<>()
Interface     Kiểu dữ liệu   Biến tham chiếu Cách lưu thực tế
```

- `List`: hợp đồng mà đối tượng phải tuân theo.
- `String`: chỉ cho phép thêm `String`.
- `languages`: biến tham chiếu.
- `ArrayList`: implementation sử dụng mảng động bên trong.

Tư tưởng cốt lõi:

> **Interface mô tả hành vi, implementation quyết định cấu trúc dữ liệu và hiệu năng.**

---

## 2. Tại sao cần Collection khi đã có Array?

### 2.1 Array

```java
String[] languages = new String[3];

languages[0] = "Java";
languages[1] = "Spring";
languages[2] = "Hibernate";
```

Array có kích thước cố định:

```java
String[] languages = new String[3];
```

Sau khi tạo, nó luôn có đúng ba ô. Muốn chứa bốn phần tử, bạn phải tạo một array mới rồi sao chép dữ liệu.

### 2.2 ArrayList

```java
List<String> languages = new ArrayList<>();

languages.add("Java");
languages.add("Spring");
languages.add("Hibernate");
languages.add("SQL");
```

Bạn không cần định trước chính xác số lượng phần tử.

Bên trong `ArrayList` vẫn sử dụng một array. Khi array nội bộ không còn đủ chỗ, `ArrayList` tạo một array lớn hơn và sao chép dữ liệu sang.

### 2.3 So sánh cốt lõi

| Array | Collection |
|---|---|
| Kích thước cố định | Thường có thể thay đổi kích thước |
| Có thể chứa primitive | Chứa reference type |
| Truy cập bằng index | Tùy loại collection |
| Ít chức năng hỗ trợ | Có thêm, xóa, tìm kiếm, sắp xếp... |
| Cấu trúc đơn giản | Có nhiều cấu trúc phù hợp từng nhu cầu |

Collection không chứa primitive trực tiếp:

```java
List<int> numbers;      // Sai
List<Integer> numbers;  // Đúng
```

Nhưng Java có **autoboxing**:

```java
List<Integer> numbers = new ArrayList<>();
numbers.add(10);
```

Java tự chuyển `10` thành `Integer.valueOf(10)`.

---

## 3. Ba khái niệm dễ nhầm

### 3.1 `Collection`

Đây là một **interface**:

```java
java.util.Collection<E>
```

Nó quy định các hành vi chung:

```java
add()
remove()
contains()
size()
isEmpty()
clear()
iterator()
```

Không thể khởi tạo trực tiếp interface:

```java
Collection<String> data = new Collection<>(); // Sai
```

Phải dùng implementation:

```java
Collection<String> data = new ArrayList<>();
```

hoặc:

```java
Collection<String> data = new HashSet<>();
```

### 3.2 `Collections`

Đây là một **utility class**:

```java
java.util.Collections
```

Nó chứa các phương thức `static` xử lý collection:

```java
Collections.sort(list);
Collections.reverse(list);
Collections.shuffle(list);
Collections.min(list);
Collections.max(list);
```

Ví dụ:

```java
List<Integer> numbers = new ArrayList<>();

numbers.add(40);
numbers.add(10);
numbers.add(30);

Collections.sort(numbers);

System.out.println(numbers); // [10, 30, 40]
```

Phân biệt:

```text
Collection   = interface đại diện cho một nhóm phần tử
Collections  = class chứa các utility method
```

### 3.3 Collections Framework

Đây là tên gọi của toàn bộ hệ thống:

```text
Collection
List
Set
Queue
Deque
Map
ArrayList
LinkedList
HashSet
HashMap
TreeSet
TreeMap
Collections
...
```

---

## 4. Sơ đồ phân cấp quan trọng

```text
Iterable<E>
    │
    └── Collection<E>
          ├── List<E>
          ├── Set<E>
          └── Queue<E>
                └── Deque<E>


Map<K, V>
```

Điểm đặc biệt:

> `Map` thuộc Collections Framework nhưng không kế thừa `Collection`.

Lý do:

- `Collection` quản lý từng **element**.
- `Map` quản lý từng cặp **key-value**.

---

## 5. `Iterable` và vòng lặp `for-each`

`Collection` kế thừa `Iterable`:

```java
public interface Collection<E> extends Iterable<E>
```

Do đó, collection có phương thức:

```java
Iterator<E> iterator();
```

Và có thể dùng `for-each`:

```java
List<String> languages = new ArrayList<>();

languages.add("Java");
languages.add("Spring");
languages.add("Hibernate");

for (String language : languages) {
    System.out.println(language);
}
```

Về bản chất, `for-each` sử dụng `Iterator`:

```java
Iterator<String> iterator = languages.iterator();

while (iterator.hasNext()) {
    String language = iterator.next();
    System.out.println(language);
}
```

`Iterator` giúp code không cần biết dữ liệu bên trong được lưu bằng:

- Array
- Linked list
- Hash table
- Tree
- Heap

Đây là ví dụ điển hình của **abstraction**.

---

# 6. `List`

`List` phù hợp khi:

- Cần giữ thứ tự.
- Cần truy cập theo index.
- Cho phép phần tử trùng nhau.
- Cần biết phần tử đứng ở vị trí nào.

Ví dụ:

```java
List<String> languages = new ArrayList<>();

languages.add("Java");
languages.add("Spring");
languages.add("Java");

System.out.println(languages);
// [Java, Spring, Java]

System.out.println(languages.get(0));
// Java
```

### Các method thường dùng

```java
list.get(index);
list.set(index, value);
list.add(index, value);
list.remove(index);
list.indexOf(value);
list.lastIndexOf(value);
```

Ví dụ:

```java
List<String> courses = new ArrayList<>();

courses.add("Java");
courses.add("SQL");
courses.add("Spring");

courses.set(1, "MySQL");

System.out.println(courses);
// [Java, MySQL, Spring]
```

### Cạm bẫy `List<Integer>.remove()`

```java
List<Integer> numbers = new ArrayList<>();

numbers.add(10);
numbers.add(20);
numbers.add(30);

numbers.remove(1);
```

Kết quả:

```text
[10, 30]
```

Vì `remove(1)` được hiểu là xóa phần tử tại index `1`.

Muốn xóa giá trị `10`:

```java
numbers.remove(Integer.valueOf(10));
```

---

## 7. `ArrayList`

```java
List<String> names = new ArrayList<>();
```

Bên trong `ArrayList` là một **mảng có thể thay đổi dung lượng**.

```text
Internal array:

[Java][Spring][null][null]
          ↑
        size = 2
```

- `size`: số phần tử thực tế.
- `capacity`: số ô mà array nội bộ đang có.

### Ưu điểm

Truy cập theo index rất nhanh:

```java
names.get(500);
```

Vì có thể tính trực tiếp vị trí trong mảng.

### Nhược điểm

Thêm hoặc xóa ở giữa phải dịch chuyển phần tử.

```java
names.add(1, "SQL");
```

```text
Trước:
[Java][Spring][Hibernate]

Sau:
[Java][SQL][Spring][Hibernate]
             └───────┘
           phải dịch sang phải
```

Thông thường:

> Khi cần một `List`, hãy nghĩ đến `ArrayList` trước.

---

## 8. `LinkedList`

`LinkedList` dùng danh sách liên kết hai chiều:

```text
null ← [Java] ⇄ [Spring] ⇄ [Hibernate] → null
```

Mỗi node chứa:

```text
previous reference
element
next reference
```

Ví dụ:

```java
List<String> languages = new LinkedList<>();
```

### Vấn đề khi truy cập index

```java
languages.get(500);
```

`LinkedList` không thể nhảy trực tiếp đến index 500. Nó phải đi qua các node:

```text
node 0 → node 1 → node 2 → ... → node 500
```

Vì vậy truy cập ở giữa là `O(n)`.

### Hiểu lầm phổ biến

Nói `LinkedList` thêm/xóa luôn nhanh hơn `ArrayList` là không chính xác.

Muốn thêm vào giữa:

```text
Tìm node: O(n)
Nối lại reference: O(1)
Tổng thể: O(n)
```

`LinkedList` có lợi rõ hơn khi thao tác ở đầu hoặc cuối và đã có sẵn vị trí cần thao tác.

Trong thực tế, `ArrayList` thường nhanh hơn nhờ dữ liệu nằm gần nhau trong bộ nhớ và tận dụng CPU cache tốt hơn.

---

# 9. `Set`

`Set` phù hợp khi câu hỏi quan trọng nhất là:

> Phần tử này đã tồn tại chưa?

Ví dụ:

```java
Set<String> languages = new HashSet<>();

languages.add("Java");
languages.add("Spring");
languages.add("Java");

System.out.println(languages.size());
// 2
```

Lần thêm `"Java"` thứ hai không tạo thêm phần tử mới.

`add()` trả về boolean:

```java
boolean first = languages.add("Java");
boolean second = languages.add("Java");

System.out.println(first);  // true
System.out.println(second); // false
```

Ý nghĩa:

```text
true  = collection đã thay đổi
false = collection không thay đổi
```

### 9.1 `HashSet`

```java
Set<String> set = new HashSet<>();
```

- Không cho phép phần tử trùng.
- Tìm kiếm nhanh trung bình.
- Không đảm bảo thứ tự duyệt.
- Bên trong dựa trên hash table.

### 9.2 `LinkedHashSet`

```java
Set<String> set = new LinkedHashSet<>();
```

- Không trùng.
- Giữ encounter order, thường là thứ tự thêm vào.

### 9.3 `TreeSet`

```java
Set<Integer> numbers = new TreeSet<>();

numbers.add(30);
numbers.add(10);
numbers.add(20);

System.out.println(numbers);
// [10, 20, 30]
```

- Không trùng.
- Tự sắp xếp.
- Các thao tác cơ bản thường là `O(log n)`.

---

# 10. `Queue`

Queue thường được hình dung như hàng người xếp hàng:

```text
Vào hàng → A → B → C → Ra khỏi hàng
```

Phần tử vào trước thường được xử lý trước:

```text
FIFO: First In, First Out
```

Ví dụ:

```java
Queue<String> tasks = new ArrayDeque<>();

tasks.offer("Send email");
tasks.offer("Generate report");
tasks.offer("Backup database");

System.out.println(tasks.poll());
// Send email

System.out.println(tasks.poll());
// Generate report
```

Không phải mọi `Queue` đều FIFO. `PriorityQueue` xử lý theo độ ưu tiên.

### Ba nhóm method chính

| Mục đích | Ném exception | Trả giá trị đặc biệt |
|---|---|---|
| Thêm | `add(e)` | `offer(e)` |
| Lấy và xóa | `remove()` | `poll()` |
| Xem đầu hàng | `element()` | `peek()` |

Ví dụ queue rỗng:

```java
Queue<String> queue = new ArrayDeque<>();

System.out.println(queue.poll()); // null
System.out.println(queue.peek()); // null
```

Trong khi:

```java
queue.remove();
```

có thể ném `NoSuchElementException`.

Với queue, thường ưu tiên:

```java
offer()
poll()
peek()
```

---

## 11. `Deque`

`Deque` là **double-ended queue**:

```text
← thêm/xóa | A | B | C | thêm/xóa →
```

Ví dụ:

```java
Deque<String> deque = new ArrayDeque<>();

deque.addFirst("B");
deque.addFirst("A");
deque.addLast("C");

System.out.println(deque);
// [A, B, C]
```

Dùng như queue:

```java
deque.offerLast("Task 1");
String task = deque.pollFirst();
```

Dùng như stack:

```java
Deque<String> stack = new ArrayDeque<>();

stack.push("Java");
stack.push("Spring");
stack.push("Hibernate");

System.out.println(stack.pop());
// Hibernate
```

Stack hoạt động theo:

```text
LIFO: Last In, First Out
```

Trong Java hiện đại, thường nên dùng:

```java
Deque<E> stack = new ArrayDeque<>();
```

thay vì class cũ:

```java
Stack<E>
```

---

## 12. `PriorityQueue`

```java
Queue<Integer> queue = new PriorityQueue<>();

queue.offer(50);
queue.offer(10);
queue.offer(30);

System.out.println(queue.poll()); // 10
System.out.println(queue.poll()); // 30
System.out.println(queue.poll()); // 50
```

Phần tử nhỏ nhất được lấy ra trước theo natural ordering.

Bên trong `PriorityQueue` thường được hình dung là một **heap**, không phải danh sách đã được sắp xếp hoàn toàn.

Vì vậy:

```java
System.out.println(queue);
```

không nên được kỳ vọng là in toàn bộ phần tử theo thứ tự tăng dần.

Chỉ phần tử ở đầu queue được đảm bảo có độ ưu tiên cao nhất.

---

# 13. `Map`

`Map` lưu dữ liệu theo cặp:

```text
Key → Value
```

Ví dụ:

```text
"NV001" → "Nguyễn Văn An"
"NV002" → "Trần Thị Bình"
```

Code:

```java
Map<String, String> employees = new HashMap<>();

employees.put("NV001", "Nguyễn Văn An");
employees.put("NV002", "Trần Thị Bình");

String name = employees.get("NV001");

System.out.println(name);
// Nguyễn Văn An
```

### Key là duy nhất

```java
employees.put("NV001", "Nguyễn Văn An");
employees.put("NV001", "Lê Văn Cường");
```

Value cũ bị thay thế:

```java
System.out.println(employees.get("NV001"));
// Lê Văn Cường
```

### Value có thể trùng

```java
Map<String, String> roles = new HashMap<>();

roles.put("An", "Developer");
roles.put("Bình", "Developer");
```

### Duyệt Map

```java
for (Map.Entry<String, String> entry : employees.entrySet()) {
    System.out.println(
        entry.getKey() + " -> " + entry.getValue()
    );
}
```

Ba view quan trọng:

```java
map.keySet();   // Set<K>
map.values();   // Collection<V>
map.entrySet(); // Set<Map.Entry<K, V>>
```

---

## 14. Các implementation chính của `Map`

### 14.1 `HashMap`

```java
Map<String, Integer> scores = new HashMap<>();
```

- Tìm value nhanh theo key.
- Không đảm bảo thứ tự.
- `put()` và `get()` có thời gian hằng số trung bình.

Đây thường là lựa chọn mặc định cho `Map`.

### 14.2 `LinkedHashMap`

```java
Map<String, Integer> scores = new LinkedHashMap<>();
```

- Tìm kiếm dựa trên hash.
- Có encounter order xác định, thường là thứ tự thêm.

### 14.3 `TreeMap`

```java
Map<String, Integer> scores = new TreeMap<>();

scores.put("Charlie", 8);
scores.put("Alice", 10);
scores.put("Bob", 9);

System.out.println(scores);
// {Alice=10, Bob=9, Charlie=8}
```

- Key được sắp xếp.
- Các thao tác thường là `O(log n)`.

---

# 15. Các method chung của `Collection`

Giả sử:

```java
Collection<String> courses = new ArrayList<>();
```

### Thêm một phần tử

```java
courses.add("Java");
```

### Thêm nhiều phần tử

```java
Collection<String> newCourses =
        List.of("SQL", "Spring", "Hibernate");

courses.addAll(newCourses);
```

### Kiểm tra phần tử

```java
boolean hasJava = courses.contains("Java");
```

### Kiểm tra nhiều phần tử

```java
boolean containsAll =
        courses.containsAll(List.of("Java", "SQL"));
```

### Xóa một phần tử

```java
courses.remove("Java");
```

### Xóa toàn bộ phần tử thuộc collection khác

```java
courses.removeAll(List.of("SQL", "Spring"));
```

### Chỉ giữ lại phần giao nhau

```java
courses.retainAll(List.of("Java", "Hibernate"));
```

Ví dụ:

```java
List<String> a = new ArrayList<>(
        List.of("Java", "SQL", "Spring")
);

List<String> b = List.of("Java", "Spring", "Python");

a.retainAll(b);

System.out.println(a);
// [Java, Spring]
```

### Số lượng phần tử

```java
int size = courses.size();
```

### Kiểm tra rỗng

```java
boolean empty = courses.isEmpty();
```

Nên viết:

```java
if (courses.isEmpty()) {
    System.out.println("Không có khóa học");
}
```

thay vì:

```java
if (courses.size() == 0) {
}
```

### Xóa tất cả

```java
courses.clear();
```

---

## 16. Ý nghĩa giá trị `boolean`

Các method như:

```java
boolean add(...)
boolean remove(...)
boolean addAll(...)
boolean retainAll(...)
```

thường trả về:

> Collection có thực sự bị thay đổi sau thao tác không?

Ví dụ:

```java
Set<String> set = new HashSet<>();

System.out.println(set.add("Java")); // true
System.out.println(set.add("Java")); // false
```

Với `remove()`:

```java
System.out.println(set.remove("Java"));   // true
System.out.println(set.remove("Python")); // false
```

---

# 17. `equals()` và `hashCode()`

## 17.1 `equals()`

Khi viết:

```java
list.contains(object);
```

Java thường sử dụng logic `equals()`.

Ví dụ:

```java
String a = new String("Java");
String b = new String("Java");

System.out.println(a == b);      // false
System.out.println(a.equals(b)); // true
```

Do đó:

```java
List<String> list = new ArrayList<>();
list.add(a);

System.out.println(list.contains(b));
// true
```

## 17.2 `hashCode()` trong `HashSet` và `HashMap`

Có thể hình dung `HashMap` chia dữ liệu thành các bucket:

```text
Bucket 0: ...
Bucket 1: ...
Bucket 2: ...
Bucket 3: ...
```

Khi thêm object:

1. Java gọi `hashCode()`.
2. Từ hash xác định bucket.
3. Trong bucket, dùng `equals()` để phân biệt chính xác object.

Quy tắc bắt buộc:

```text
Nếu a.equals(b) là true
thì a.hashCode() phải bằng b.hashCode()
```

Chiều ngược lại không bắt buộc:

```text
Cùng hashCode chưa chắc equals
```

### Ví dụ class dùng trong `HashSet`

```java
import java.util.Objects;

public final class Student {
    private final int id;
    private final String name;

    public Student(int id, String name) {
        this.id = id;
        this.name = name;
    }

    @Override
    public boolean equals(Object object) {
        if (this == object) {
            return true;
        }

        if (!(object instanceof Student other)) {
            return false;
        }

        return id == other.id;
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
```

Sử dụng:

```java
Set<Student> students = new HashSet<>();

students.add(new Student(1, "An"));
students.add(new Student(1, "An khác"));

System.out.println(students.size());
// 1
```

### Không nên thay đổi dữ liệu dùng để tính hash

Nếu `id` được dùng trong `hashCode()`, không nên đổi `id` sau khi object đã vào `HashSet` hoặc làm key của `HashMap`.

Key nên là object bất biến như:

```java
String
Integer
UUID
enum
```

hoặc custom class có field khóa là `final`.

---

# 18. Các loại thứ tự

Không nên gộp tất cả thành một khái niệm “có thứ tự”.

### Thứ tự theo vị trí

```java
List
```

Có index:

```text
0, 1, 2, 3...
```

### Thứ tự thêm vào

```java
LinkedHashSet
LinkedHashMap
```

### Thứ tự sắp xếp

```java
TreeSet
TreeMap
```

Dựa vào:

```java
Comparable
```

hoặc:

```java
Comparator
```

### Không đảm bảo thứ tự

```java
HashSet
HashMap
```

Việc thấy chúng in ra giống thứ tự thêm trong một lần chạy không có nghĩa thứ tự đó được đảm bảo.

---

# 19. Xóa phần tử khi đang duyệt

Code dễ lỗi:

```java
List<String> names = new ArrayList<>(
        List.of("An", "Bình", "Cường")
);

for (String name : names) {
    if (name.equals("Bình")) {
        names.remove(name);
    }
}
```

Có thể ném:

```text
ConcurrentModificationException
```

### Cách 1: `Iterator.remove()`

```java
Iterator<String> iterator = names.iterator();

while (iterator.hasNext()) {
    String name = iterator.next();

    if (name.equals("Bình")) {
        iterator.remove();
    }
}
```

### Cách 2: `removeIf()`

```java
names.removeIf(name -> name.equals("Bình"));
```

---

# 20. Collection không cho phép sửa

## 20.1 `List.of()`

```java
List<String> languages =
        List.of("Java", "Spring", "Hibernate");
```

Danh sách này là unmodifiable:

```java
languages.add("SQL");
// UnsupportedOperationException
```

Muốn sửa:

```java
List<String> languages = new ArrayList<>(
        List.of("Java", "Spring", "Hibernate")
);

languages.add("SQL");
```

## 20.2 `Arrays.asList()`

```java
List<String> languages = Arrays.asList(
        "Java",
        "Spring",
        "Hibernate"
);
```

Danh sách này:

- Cho phép `set()`.
- Không cho phép thay đổi kích thước.
- Được backed bởi array ban đầu.

```java
languages.set(0, "Python"); // Được

languages.add("SQL");       // UnsupportedOperationException
languages.remove("Spring"); // UnsupportedOperationException
```

---

# 21. Độ phức tạp cần nhớ

| Cấu trúc | Thao tác | Độ phức tạp thường gặp |
|---|---|---:|
| `ArrayList` | `get(index)` | `O(1)` |
| `ArrayList` | thêm cuối | `O(1)` trung bình |
| `ArrayList` | thêm/xóa giữa | `O(n)` |
| `ArrayList` | `contains()` | `O(n)` |
| `LinkedList` | `get(index)` | `O(n)` |
| `LinkedList` | thêm/xóa đầu hoặc cuối | `O(1)` |
| `HashSet` | `add`, `contains`, `remove` | `O(1)` trung bình |
| `TreeSet` | `add`, `contains`, `remove` | `O(log n)` |
| `HashMap` | `put`, `get`, `remove` | `O(1)` trung bình |
| `TreeMap` | `put`, `get`, `remove` | `O(log n)` |
| `ArrayDeque` | thêm/xóa ở hai đầu | `O(1)` trung bình |
| `PriorityQueue` | `offer`, `poll` | `O(log n)` |

Ý nghĩa:

- `O(1)`: thời gian gần như không tăng theo số phần tử.
- `O(n)`: có thể phải đi qua toàn bộ collection.
- `O(log n)`: số phần tử tăng nhiều nhưng số bước tăng chậm.

---

# 22. Vì sao nên khai báo bằng interface?

Nên viết:

```java
List<String> names = new ArrayList<>();
```

thay vì luôn viết:

```java
ArrayList<String> names = new ArrayList<>();
```

Vì phần lớn code chỉ cần hành vi của `List`.

Sau này có thể đổi implementation:

```java
List<String> names = new LinkedList<>();
```

mà phần lớn code sử dụng không cần đổi.

Nguyên tắc:

> **Program to an interface, not an implementation.**

Ví dụ:

```java
public static void printNames(List<String> names) {
    for (String name : names) {
        System.out.println(name);
    }
}
```

Method nhận được cả:

```text
ArrayList<String>
LinkedList<String>
```

Nếu method chỉ cần duyệt, có thể tổng quát hơn:

```java
public static void printNames(Collection<String> names) {
    for (String name : names) {
        System.out.println(name);
    }
}
```

Nguyên tắc thực tế:

> Tham số nên dùng interface tổng quát nhất nhưng vẫn đủ khả năng cho công việc.

---

# 23. Ví dụ tổng hợp thực tế

Giả sử có hệ thống nhận tên khóa học mà học viên đăng ký.

### Bước 1: lưu toàn bộ đăng ký

```java
List<String> registrations = new ArrayList<>();

registrations.add("Java");
registrations.add("SQL");
registrations.add("Java");
registrations.add("Spring");
registrations.add("Java");
```

Dùng `List` vì:

- Cần lưu đầy đủ.
- Cho phép trùng.
- Giữ thứ tự đăng ký.

### Bước 2: lấy khóa học duy nhất

```java
Set<String> uniqueCourses =
        new HashSet<>(registrations);
```

Dùng `Set` vì không muốn trùng.

### Bước 3: đếm số lượt đăng ký

```java
Map<String, Integer> registrationCount = new HashMap<>();

for (String course : registrations) {
    int currentCount =
            registrationCount.getOrDefault(course, 0);

    registrationCount.put(course, currentCount + 1);
}
```

Về mặt nội dung:

```text
Java   → 3
SQL    → 1
Spring → 1
```

Dùng `Map` vì cần ánh xạ:

```text
Tên khóa học → số lượt đăng ký
```

### Bước 4: đưa khóa học vào hàng chờ xử lý

```java
Queue<String> processingQueue = new ArrayDeque<>();

processingQueue.offer("Java");
processingQueue.offer("SQL");
processingQueue.offer("Spring");

while (!processingQueue.isEmpty()) {
    String course = processingQueue.poll();

    System.out.println("Processing: " + course);
}
```

Tóm tắt:

```text
List  → lịch sử đăng ký
Set   → các khóa học duy nhất
Map   → số lượt của từng khóa học
Queue → thứ tự xử lý
```

---

# 24. Quy trình chọn Collection

### Có cần tra cứu bằng key không?

```text
Có → Map
```

Ví dụ:

```text
employeeId → Employee
username   → User
productId  → Product
```

### Có cần loại bỏ phần tử trùng không?

```text
Có → Set
```

- Không cần thứ tự: `HashSet`
- Giữ thứ tự thêm: `LinkedHashSet`
- Tự sắp xếp: `TreeSet`

### Có cần index và phần tử trùng không?

```text
Có → List
```

Mặc định thường dùng:

```java
ArrayList
```

### Dữ liệu có phải chờ xử lý không?

```text
Có → Queue
```

Mặc định thường dùng:

```java
ArrayDeque
```

### Cần thao tác ở cả đầu và cuối hoặc cần stack?

```text
Có → Deque
```

### Cần lấy phần tử có độ ưu tiên cao nhất?

```text
Có → PriorityQueue
```

---

# 25. Tổng kết Collections

```text
List  = chuỗi phần tử có vị trí
Set   = tập hợp không trùng
Queue = hàng chờ xử lý
Map   = ánh xạ key-value
```

Cấu trúc bên trong:

```text
ArrayList     = dynamic array
LinkedList    = doubly linked list
HashSet       = hash table
HashMap       = hash table key-value
TreeSet       = ordered tree
TreeMap       = ordered tree key-value
PriorityQueue = heap
ArrayDeque    = resizable double-ended array
```

Lựa chọn phổ biến:

```text
Cần truy cập index nhanh       → ArrayList
Cần kiểm tra tồn tại nhanh     → HashSet
Cần tìm value bằng key nhanh   → HashMap
Cần dữ liệu luôn được sắp xếp  → TreeSet / TreeMap
Cần xử lý đầu-cuối             → ArrayDeque
Cần xử lý theo độ ưu tiên      → PriorityQueue
```

Cốt lõi:

> Bạn không chọn collection chỉ vì nó “chứa được nhiều phần tử”, mà dựa vào cách dữ liệu cần được tổ chức, truy cập và xử lý.

---

# Phần II. Generics

## 1. Generics là gì?

Generics cho phép viết class, interface hoặc method mà **kiểu dữ liệu cụ thể sẽ được truyền vào sau**.

Ví dụ:

```java
List<String> names = new ArrayList<>();
List<Integer> numbers = new ArrayList<>();
```

`List` chỉ được viết một lần nhưng dùng được với nhiều kiểu:

```text
List<String>
List<Integer>
List<Student>
List<Product>
```

Có thể hiểu:

> Generic là cách biến “kiểu dữ liệu” thành một tham số.

Giống method nhận tham số giá trị:

```java
printName("An");
```

thì generic nhận tham số kiểu:

```java
List<String>
```

Trong đó `String` là kiểu được truyền vào `List`.

---

# 2. Vấn đề Generics giải quyết

## 2.1 Trước khi có Generics

```java
public class BoxOld {
    private Object value;

    public void set(Object value) {
        this.value = value;
    }

    public Object get() {
        return value;
    }
}
```

Vì mọi class đều kế thừa `Object`, có thể đưa bất cứ thứ gì vào:

```java
BoxOld box = new BoxOld();

box.set("Java");
box.set(100);
box.set(new Student());
```

Khi lấy ra phải ép kiểu:

```java
box.set("Java");

String value = (String) box.get();
```

Lỗi có thể chỉ xuất hiện khi chạy:

```java
box.set(100);

String value = (String) box.get();
// ClassCastException
```

## 2.2 Sử dụng Generics

```java
public class Box<T> {
    private T value;

    public void set(T value) {
        this.value = value;
    }

    public T get() {
        return value;
    }
}
```

Sử dụng:

```java
Box<String> box = new Box<>();

box.set("Java");

String value = box.get();
```

Compiler hiểu:

```text
T = String
```

Nếu viết:

```java
box.set(100);
```

compiler báo lỗi ngay.

Lợi ích cốt lõi:

1. **Type safety**
2. **Không cần ép kiểu thủ công**
3. **Tái sử dụng cùng một đoạn code cho nhiều kiểu**
4. **API thể hiện rõ kiểu nhận và trả về**

---

# 3. Generic class

```java
public class Box<T> {
    private T value;

    public T get() {
        return value;
    }

    public void set(T value) {
        this.value = value;
    }
}
```

`T` là **type parameter**.

Khi tạo:

```java
Box<String> stringBox = new Box<>();
```

thì:

```text
T = String
```

Khi tạo:

```java
Box<Integer> integerBox = new Box<>();
```

thì:

```text
T = Integer
```

### Nhiều type parameter

```java
public class Pair<K, V> {
    private K key;
    private V value;

    public Pair(K key, V value) {
        this.key = key;
        this.value = value;
    }

    public K getKey() {
        return key;
    }

    public V getValue() {
        return value;
    }
}
```

Sử dụng:

```java
Pair<String, Integer> studentScore =
        new Pair<>("Nguyen Van An", 9);

String name = studentScore.getKey();
Integer score = studentScore.getValue();
```

Ở đây:

```text
K = String
V = Integer
```

---

# 4. Tên type parameter

| Ký hiệu | Ý nghĩa thường dùng |
|---|---|
| `T` | Type |
| `E` | Element |
| `K` | Key |
| `V` | Value |
| `N` | Number |
| `R` | Result hoặc Return type |
| `S`, `U` | Kiểu thứ hai, thứ ba |

Ví dụ:

```java
public interface List<E>
```

```java
public interface Map<K, V>
```

Đây chỉ là convention, không phải từ khóa.

---

# 5. Diamond operator

Có thể viết:

```java
List<String> names = new ArrayList<String>();
```

Rút gọn:

```java
List<String> names = new ArrayList<>();
```

`<>` được gọi là **diamond operator**.

Không nên viết:

```java
List<String> names = new ArrayList(); // Raw type
```

Nên viết:

```java
List<String> names = new ArrayList<>();
```

---

# 6. Generic interface

```java
public interface Repository<T> {
    void save(T entity);

    T findById(long id);
}
```

Triển khai cho `User`:

```java
public class UserRepository implements Repository<User> {

    @Override
    public void save(User user) {
        System.out.println("Saving user: " + user);
    }

    @Override
    public User findById(long id) {
        return new User(id, "An");
    }
}
```

Triển khai cho `Product`:

```java
public class ProductRepository implements Repository<Product> {

    @Override
    public void save(Product product) {
        System.out.println("Saving product: " + product);
    }

    @Override
    public Product findById(long id) {
        return new Product(id, "Laptop");
    }
}
```

Ứng dụng thực tế:

```text
Repository<User>
Repository<Product>
Repository<Order>
```

Trong Spring Data:

```java
public interface UserRepository
        extends JpaRepository<User, Long> {
}
```

Trong đó:

```text
User = kiểu entity
Long = kiểu khóa chính
```

---

# 7. Generic method

Một method có thể tự khai báo type parameter:

```java
public static <T> T getFirst(List<T> list) {
    return list.get(0);
}
```

Vị trí `<T>`:

```java
public static <T> T getFirst(...)
              ↑   ↑
       khai báo T  kiểu trả về
```

Sử dụng:

```java
List<String> names = List.of("An", "Binh");
String firstName = getFirst(names);

List<Integer> numbers = List.of(10, 20);
Integer firstNumber = getFirst(numbers);
```

Compiler tự suy luận:

```text
getFirst(List<String>)  → T là String
getFirst(List<Integer>) → T là Integer
```

### Generic class và generic method

Generic class:

```java
public class Box<T> {
    public T get() {
        // ...
    }
}
```

`T` được xác định khi tạo object:

```java
Box<String> box = new Box<>();
```

Generic method:

```java
public static <T> T getFirst(List<T> list) {
    // ...
}
```

`T` được xác định ở từng lần gọi method.

---

# 8. Bounded type parameter

Thông thường:

```java
<T>
```

nghĩa là `T` có thể là bất cứ reference type nào.

Nếu cần giới hạn:

```java
public static <T extends Number> double sum(List<T> numbers) {
    double total = 0;

    for (T number : numbers) {
        total += number.doubleValue();
    }

    return total;
}
```

`T` chỉ có thể là `Number` hoặc kiểu con:

```text
Integer
Double
Long
Float
BigDecimal
...
```

Sử dụng:

```java
System.out.println(sum(List.of(1, 2, 3)));
System.out.println(sum(List.of(1.5, 2.5, 3.5)));
```

Không được:

```java
sum(List.of("1", "2", "3")); // Compile error
```

### `extends` cũng dùng với interface

```java
public static <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}
```

Đúng:

```java
<T extends Comparable<T>>
```

Sai:

```java
<T implements Comparable<T>>
```

### Nhiều giới hạn

```java
<T extends Number & Comparable<T>>
```

Nếu có class và interface, class phải đứng trước:

```java
<T extends SomeClass & InterfaceA & InterfaceB>
```

---

# 9. Vì sao cần Wildcard?

Quy tắc quan trọng:

```java
Integer extends Number
```

nhưng:

```java
List<Integer> không extends List<Number>
```

Đoạn sau sai:

```java
List<Integer> integers = new ArrayList<>();

List<Number> numbers = integers; // Compile error
```

Nếu Java cho phép:

```java
numbers.add(3.14);
```

thì một `List<Integer>` sẽ chứa `Double`.

Do đó generic trong Java mặc định là **invariant**:

```text
Integer là Number

nhưng

List<Integer> không phải List<Number>
```

Wildcard giúp method linh hoạt với nhiều generic type có quan hệ kế thừa.

---

# 10. Unbounded wildcard `<?>`

```java
public static void printList(List<?> list) {
    for (Object element : list) {
        System.out.println(element);
    }
}
```

Method nhận được:

```text
List<String>
List<Integer>
List<Student>
List<Product>
```

`?` có nghĩa:

> Một kiểu nào đó, nhưng method không biết chính xác là kiểu nào.

### `List<?>` khác `List<Object>`

`List<Object>` có element type chính xác là `Object`.

```java
List<Object> objects = new ArrayList<>();

objects.add("Java");
objects.add(10);
```

Nhưng không thể:

```java
List<String> strings = new ArrayList<>();

List<Object> objects = strings; // Sai
```

Trong khi:

```java
List<?> unknown = strings; // Đúng
```

Tóm tắt:

```text
List<Object> = danh sách có element type chính xác là Object
List<?>      = danh sách có một element type nào đó chưa biết
```

### Hạn chế của `List<?>`

Có thể đọc dưới dạng `Object`:

```java
Object value = list.get(0);
```

Không thể thêm giá trị cụ thể:

```java
list.add("Java"); // Sai
list.add(10);     // Sai
```

Vì compiler không biết danh sách thật là `List<String>`, `List<Integer>` hay kiểu khác.

---

# 11. Upper-bounded wildcard `? extends T`

Ví dụ:

```java
public static double sum(List<? extends Number> numbers) {
    double total = 0;

    for (Number number : numbers) {
        total += number.doubleValue();
    }

    return total;
}
```

Method nhận được:

```text
List<Integer>
List<Double>
List<Long>
List<Float>
```

`? extends Number` nghĩa là:

> Danh sách chứa một kiểu chưa biết, nhưng chắc chắn là `Number` hoặc kiểu con.

### Có thể đọc

```java
Number number = numbers.get(0);
```

### Không thể thêm giá trị cụ thể

```java
numbers.add(10);   // Sai
numbers.add(3.14); // Sai
```

Lý do: danh sách thật có thể là `List<Double>` hoặc `List<Integer>`.

Cốt lõi:

> `? extends T` phù hợp khi collection chủ yếu cung cấp dữ liệu để bạn đọc.

---

# 12. Lower-bounded wildcard `? super T`

```java
public static void addIntegers(List<? super Integer> list) {
    list.add(10);
    list.add(20);
}
```

Method nhận được:

```text
List<Integer>
List<Number>
List<Object>
```

`? super Integer` nghĩa là:

> Danh sách chứa `Integer` hoặc một kiểu cha của `Integer`.

### Có thể thêm `Integer`

```java
list.add(10);
```

Điều này luôn an toàn.

### Khi đọc chỉ đảm bảo `Object`

```java
Object value = list.get(0);
```

Không thể:

```java
Integer value = list.get(0); // Sai
```

Vì danh sách thật có thể là `List<Number>` và đã chứa `Double`.

Cốt lõi:

> `? super T` phù hợp khi collection nhận dữ liệu từ bạn.

---

# 13. PECS

PECS:

```text
Producer Extends
Consumer Super
```

Nhìn từ góc độ collection.

### Collection cung cấp dữ liệu

```java
List<? extends Number>
```

Dùng `extends`.

### Collection nhận dữ liệu

```java
List<? super Integer>
```

Dùng `super`.

### Ví dụ chuẩn

```java
public static <T> void copy(
        List<? extends T> source,
        List<? super T> destination
) {
    for (T item : source) {
        destination.add(item);
    }
}
```

Sử dụng:

```java
List<Integer> source = List.of(1, 2, 3);
List<Number> destination = new ArrayList<>();

copy(source, destination);

System.out.println(destination);
// [1, 2, 3]
```

Phân tích:

```text
source      → producer → extends
destination → consumer → super
```

---

# 14. Khi nào không dùng `extends` hoặc `super`?

Khi method cần vừa đọc vừa ghi đúng cùng một kiểu:

```java
public static <T> void replaceFirst(
        List<T> list,
        T newValue
) {
    T oldValue = list.get(0);
    list.set(0, newValue);

    System.out.println("Old: " + oldValue);
}
```

Quy tắc thực tế:

```text
Chỉ đọc                  → ? extends T
Chỉ ghi                  → ? super T
Vừa đọc vừa ghi đúng T   → T
Không quan tâm kiểu      → ?
```

---

# 15. Type parameter và wildcard

Hai method:

```java
public static <T> void print(List<T> list) {
}
```

```java
public static void print(List<?> list) {
}
```

Nếu chỉ in thì cả hai đều được.

Nhưng `<T>` đặt tên cho kiểu để dùng lại:

```java
public static <T> T getFirst(List<T> list) {
    return list.get(0);
}
```

Hoặc:

```java
public static <T> void addToList(
        List<T> list,
        T value
) {
    list.add(value);
}
```

Wildcard chỉ nói “một kiểu nào đó”:

```java
public static void print(List<?> list) {
}
```

Có thể nhớ:

> Cần liên kết cùng một kiểu ở nhiều vị trí thì dùng `<T>`. Chỉ cần nói “một kiểu nào đó” thì dùng `?`.

---

# 16. Lưu ý về nhãn trong slide

Đoạn:

```java
public static <T> boolean isEqual(
        GenericsType<T> g1,
        GenericsType<T> g2
)
```

- `<T>` sau `static` là **generic method type parameter**.
- `GenericsType<T>` không phải wildcard vì không có `?`.

Wildcard thật sự:

```java
GenericsType<?>
GenericsType<? extends Number>
GenericsType<? super Integer>
```

Tương tự:

```java
EntityDAO<T extends GenericDAO>
```

là **bounded type parameter**, không phải upper-bounded wildcard.

Upper-bounded wildcard phải là:

```java
EntityDAO<? extends GenericDAO>
```

---

# 17. Raw type

Raw type là sử dụng generic class mà không truyền type argument.

```java
List list = new ArrayList();
```

hoặc:

```java
Box box = new Box();
```

Thay vì:

```java
List<String> list = new ArrayList<>();
Box<String> box = new Box<>();
```

Raw type làm mất type safety:

```java
List list = new ArrayList();

list.add("Java");
list.add(10);
list.add(new Student());
```

Khi lấy ra:

```java
String value = (String) list.get(1);
```

có thể gặp:

```text
ClassCastException
```

Raw type chủ yếu để tương thích với code Java cũ.

Trong code mới nên tránh:

```java
List list;
Map map;
Box box;
```

Hãy dùng:

```java
List<String> list;
Map<String, User> map;
Box<Integer> box;
```

Nếu thật sự không biết kiểu và chỉ cần quan sát:

```java
List<?> list;
```

---

# 18. Generic không nhận primitive

Không được:

```java
List<int> numbers;
Box<double> box;
```

Phải dùng wrapper:

| Primitive | Wrapper |
|---|---|
| `int` | `Integer` |
| `long` | `Long` |
| `double` | `Double` |
| `float` | `Float` |
| `boolean` | `Boolean` |
| `char` | `Character` |
| `byte` | `Byte` |
| `short` | `Short` |

Ví dụ:

```java
List<Integer> numbers = new ArrayList<>();

numbers.add(10);
numbers.add(20);
```

Autoboxing:

```java
numbers.add(10);
```

gần tương đương:

```java
numbers.add(Integer.valueOf(10));
```

Unboxing:

```java
int number = numbers.get(0);
```

Cẩn thận với `null`:

```java
List<Integer> numbers = new ArrayList<>();
numbers.add(null);

int value = numbers.get(0);
// NullPointerException khi unboxing
```

---

# 19. Type erasure

Generics trong Java chủ yếu hoạt động ở compile time.

Sau khi compiler kiểm tra kiểu, phần lớn thông tin generic bị xóa khi tạo bytecode. Cơ chế này gọi là **type erasure**.

```java
List<String> strings = new ArrayList<>();
List<Integer> integers = new ArrayList<>();
```

Ở runtime, cả hai đều cơ bản là `ArrayList`.

```java
System.out.println(
        strings.getClass() == integers.getClass()
);
// true
```

### Hệ quả

#### Không thể `new T()`

```java
public class Box<T> {

    public T create() {
        return new T(); // Sai
    }
}
```

Có thể dùng factory:

```java
public static <T> T create(Supplier<T> factory) {
    return factory.get();
}
```

#### Không thể dùng `T.class`

```java
T.class // Sai
```

Thường truyền `Class<T>`:

```java
public class Mapper<T> {
    private final Class<T> type;

    public Mapper(Class<T> type) {
        this.type = type;
    }
}
```

#### Không thể `instanceof List<String>`

```java
if (object instanceof List<String>) {
    // Sai
}
```

Có thể:

```java
if (object instanceof List<?>) {
}
```

#### Không thể tạo generic array trực tiếp

```java
T[] values = new T[10]; // Sai
```

---

# 20. Generics dùng ở đâu trong thực tế?

## 20.1 Collections

```java
List<User> users;
Set<String> roles;
Map<Long, Product> products;
Queue<Order> orders;
```

## 20.2 Repository và DAO

```java
public interface Repository<T, ID> {
    T findById(ID id);

    void save(T entity);

    void deleteById(ID id);
}
```

Sử dụng:

```text
Repository<User, Long>
Repository<Product, Long>
Repository<Order, String>
```

## 20.3 API response

```java
public class ApiResponse<T> {
    private boolean success;
    private String message;
    private T data;
}
```

Sử dụng:

```java
ApiResponse<User> userResponse;
ApiResponse<List<Product>> productResponse;
ApiResponse<Order> orderResponse;
```

## 20.4 Phân trang

```java
public class Page<T> {
    private List<T> content;
    private int pageNumber;
    private int totalPages;
    private long totalElements;
}
```

## 20.5 Result

```java
public class Result<T> {
    private final T data;
    private final String error;
}
```

## 20.6 Mapper

```java
public interface Mapper<S, T> {
    T map(S source);
}
```

Ví dụ:

```java
public class UserMapper
        implements Mapper<UserEntity, UserDto> {

    @Override
    public UserDto map(UserEntity source) {
        return new UserDto(
                source.getId(),
                source.getName()
        );
    }
}
```

---

# 21. Wildcard trong code thực tế

### Method chỉ đọc

```java
public static double calculateTotal(
        List<? extends Product> products
) {
    double total = 0;

    for (Product product : products) {
        total += product.getPrice();
    }

    return total;
}
```

Nhận được:

```text
List<Product>
List<DigitalProduct>
List<PhysicalProduct>
```

### Method ghi dữ liệu

```java
public static void addDefaultUsers(
        List<? super User> users
) {
    users.add(new User("Admin"));
}
```

### Method không quan tâm kiểu

```java
public static boolean isEmpty(Collection<?> collection) {
    return collection.isEmpty();
}
```

---

# 22. Khi nào nên tự tạo generic class?

Nên dùng generic khi:

- Cùng logic nhưng hoạt động với nhiều kiểu.
- Kiểu truyền vào liên quan đến nhiều field hoặc method.
- Muốn giữ quan hệ kiểu giữa input và output.
- Muốn compiler bảo đảm dữ liệu cùng kiểu.

Ví dụ hợp lý:

```java
class Pair<K, V>
class ApiResponse<T>
class Page<T>
interface Repository<T, ID>
interface Mapper<S, T>
```

Không nên generic hóa vô lý:

```java
public class UserService<T> {
}
```

nếu class chỉ làm việc với `User`.

---

# 23. Bảng chọn nhanh Generics

| Nhu cầu | Cú pháp |
|---|---|
| Cần biết và dùng lại cùng một kiểu | `<T>` / `List<T>` |
| Không quan tâm kiểu cụ thể | `List<?>` |
| Chủ yếu đọc như kiểu `T` | `List<? extends T>` |
| Chủ yếu thêm kiểu `T` | `List<? super T>` |
| Vừa đọc vừa ghi đúng `T` | `List<T>` |

Ví dụ:

```java
void print(List<?> list)

double sum(List<? extends Number> list)

void addNumbers(List<? super Integer> list)

<T> void replace(List<T> list, T value)
```

---

# 24. Tổng kết Generics

Generics giải quyết:

```text
An toàn kiểu dữ liệu
Tái sử dụng code
Biểu diễn quan hệ giữa các kiểu
```

Các dạng cần nhớ:

```java
class Box<T>
```

```java
static <T> T getFirst(List<T> list)
```

```java
<T extends Number>
```

```java
List<?>
```

```java
List<? extends Number>
```

```java
List<? super Integer>
```

PECS:

```text
Producer Extends
Consumer Super
```

Raw type nên tránh:

```java
List list;
```

Nên dùng:

```java
List<String> list;
```

hoặc:

```java
List<?> list;
```

Trong thực tế dùng nhiều nhất:

```java
List<User>
Map<Long, Product>
ApiResponse<T>
Repository<T, ID>
```

Wildcard thường xuất hiện khi viết method dùng chung hoặc API cần nhận nhiều generic type có quan hệ kế thừa.

---

# Phần III. Lambda Expressions

## 1. Lambda expression là gì?

Lambda là cách viết ngắn gọn để **cung cấp phần triển khai cho một functional interface**.

Ví dụ:

```java
Test test = () -> {
    System.out.println("Setup environment");
};
```

Lambda:

```java
() -> {
    System.out.println("Setup environment");
}
```

không phải một function độc lập như JavaScript. Nó được Java hiểu là phần triển khai cho abstract method của interface `Test`.

Cốt lõi:

> Lambda cho phép truyền **một hành vi** như một giá trị.

Trước đây chủ yếu truyền dữ liệu:

```java
print("Java");
sum(10, 20);
```

Với lambda có thể truyền quy tắc xử lý:

```java
numbers.removeIf(number -> number < 0);
```

Lambda:

```java
number -> number < 0
```

nghĩa là:

> Nhận một số và trả về `true` nếu số đó nhỏ hơn 0.

---

# 2. Từ anonymous class đến lambda

Interface:

```java
public interface Test {

    void setup();

    default void run() {
        System.out.println("Hello Tester");
    }
}
```

Cách cũ:

```java
Test test = new Test() {

    @Override
    public void setup() {
        System.out.println("Setup environment");
    }
};
```

Lambda:

```java
Test test = () -> {
    System.out.println("Setup environment");
};
```

Rút gọn:

```java
Test test = () -> System.out.println("Setup environment");
```

Ba cách trên có cùng ý nghĩa chính.

### Lưu ý trong slide

Lambda đang triển khai:

```java
setup()
```

Nhưng nếu gọi:

```java
test.run();
```

thì chạy default method và in:

```text
Hello Tester
```

Muốn chạy lambda:

```java
test.setup();
```

Kết quả:

```text
Setup environment
```

Có thể gọi cả hai:

```java
test.setup();
test.run();
```

---

# 3. Functional interface

Lambda chỉ hoạt động với **functional interface**.

Functional interface có đúng **một abstract method**.

```java
@FunctionalInterface
public interface Printer {
    void print(String message);
}
```

Sử dụng:

```java
Printer printer = message -> System.out.println(message);

printer.print("Hello Java");
```

Compiler ghép lambda vào:

```java
void print(String message);
```

### `@FunctionalInterface`

```java
@FunctionalInterface
public interface Calculator {
    int calculate(int a, int b);
}
```

Nếu có hai abstract method:

```java
@FunctionalInterface
public interface Calculator {
    int add(int a, int b);
    int subtract(int a, int b);
}
```

compiler báo lỗi.

Annotation không bắt buộc, nhưng nên dùng.

### Default và static method không được tính

```java
@FunctionalInterface
public interface Test {

    void setup();

    default void run() {
        System.out.println("Running");
    }

    static void printInfo() {
        System.out.println("Test interface");
    }
}
```

Interface vẫn là functional interface vì chỉ có một abstract method.

---

# 4. Cấu trúc lambda

Cú pháp:

```java
(parameters) -> expression
```

hoặc:

```java
(parameters) -> {
    statements;
}
```

Lambda gồm:

```text
Tham số  ->  Phần thân
```

Ví dụ:

```java
(a, b) -> a + b
```

---

# 5. Các dạng cú pháp

## 5.1 Không có tham số

```java
@FunctionalInterface
public interface Task {
    void execute();
}
```

```java
Task task = () -> System.out.println("Executing task");

task.execute();
```

## 5.2 Một tham số

```java
@FunctionalInterface
public interface Printer {
    void print(String value);
}
```

Đầy đủ:

```java
Printer printer = (String value) -> {
    System.out.println(value);
};
```

Rút gọn:

```java
Printer printer = value -> System.out.println(value);
```

## 5.3 Nhiều tham số

```java
@FunctionalInterface
public interface Calculator {
    int calculate(int a, int b);
}
```

```java
Calculator addition = (a, b) -> a + b;
Calculator subtraction = (a, b) -> a - b;
```

Khi có nhiều tham số, dấu ngoặc là bắt buộc:

```java
(a, b) -> a + b
```

---

# 6. Lambda có hoặc không có `return`

Một biểu thức:

```java
Calculator addition = (a, b) -> a + b;
```

tương đương:

```java
Calculator addition = (a, b) -> {
    return a + b;
};
```

Nhiều câu lệnh:

```java
Calculator addition = (a, b) -> {
    System.out.println("Adding " + a + " and " + b);

    int result = a + b;

    return result;
};
```

Nếu functional method trả về `void`, không cần `return`.

---

# 7. Lambda không có kiểu độc lập

Lambda:

```java
value -> value.length()
```

tự nó chưa có kiểu cụ thể.

Kiểu phụ thuộc vào nơi được gán:

```java
Function<String, Integer> getLength =
        value -> value.length();
```

Java hiểu:

- `value` là `String`.
- Kết quả là `Integer`.

Lambda cần một **target type** là functional interface.

Không thể:

```java
var action = value -> value.length(); // Sai
```

Phải có target type:

```java
Function<String, Integer> action =
        value -> value.length();
```

---

# 8. Lambda thực chất tạo ra gì?

```java
Predicate<Integer> isEven =
        number -> number % 2 == 0;
```

`isEven` là object thực hiện `Predicate<Integer>`.

Gọi:

```java
boolean result = isEven.test(10);
```

Không gọi như function JavaScript:

```java
isEven(10); // Sai
```

Phải gọi method của functional interface.

Tên method thường gặp:

```text
Predicate<T>      → test()
Function<T, R>    → apply()
Consumer<T>       → accept()
Supplier<T>       → get()
Comparator<T>     → compare()
Runnable          → run()
```

---

# 9. Các functional interface quan trọng

Nằm trong:

```java
java.util.function
```

| Interface | Nhận | Trả về | Ý nghĩa |
|---|---|---|---|
| `Predicate<T>` | `T` | `boolean` | Kiểm tra điều kiện |
| `Function<T, R>` | `T` | `R` | Biến đổi dữ liệu |
| `Consumer<T>` | `T` | `void` | Tiêu thụ/xử lý dữ liệu |
| `Supplier<T>` | Không có | `T` | Cung cấp/tạo dữ liệu |
| `UnaryOperator<T>` | `T` | `T` | Biến đổi cùng kiểu |
| `BinaryOperator<T>` | `T, T` | `T` | Kết hợp hai giá trị cùng kiểu |

---

# 10. `Predicate<T>`

Cấu trúc rút gọn:

```java
@FunctionalInterface
public interface Predicate<T> {
    boolean test(T value);
}
```

Ví dụ:

```java
Predicate<Integer> isEven =
        number -> number % 2 == 0;
```

Gọi:

```java
System.out.println(isEven.test(10)); // true
System.out.println(isEven.test(7));  // false
```

### Ví dụ filter trong slide

```java
public static List<Integer> filterList(
        List<Integer> numbers,
        Predicate<Integer> predicate
) {
    List<Integer> filteredList = new ArrayList<>();

    for (Integer number : numbers) {
        if (predicate.test(number)) {
            filteredList.add(number);
        }
    }

    return filteredList;
}
```

Lọc số chẵn:

```java
List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6);

List<Integer> evenNumbers = filterList(
        numbers,
        number -> number % 2 == 0
);

System.out.println(evenNumbers);
// [2, 4, 6]
```

Lọc số lớn hơn 3:

```java
List<Integer> greaterThanThree = filterList(
        numbers,
        number -> number > 3
);
```

Lọc chia hết cho 3:

```java
List<Integer> divisibleByThree = filterList(
        numbers,
        number -> number % 3 == 0
);
```

Cùng một method nhưng truyền được nhiều quy tắc lọc khác nhau.

Đây là ý nghĩa:

> Truyền hành vi vào method.

---

# 11. Kết hợp `Predicate`

`Predicate` có:

```java
and()
or()
negate()
```

Ví dụ:

```java
Predicate<Integer> isPositive =
        number -> number > 0;

Predicate<Integer> isEven =
        number -> number % 2 == 0;
```

Vừa dương vừa chẵn:

```java
Predicate<Integer> isPositiveAndEven =
        isPositive.and(isEven);
```

Dương hoặc chẵn:

```java
Predicate<Integer> condition =
        isPositive.or(isEven);
```

Không chẵn:

```java
Predicate<Integer> isNotEven =
        isEven.negate();
```

Ví dụ thực tế:

```java
Predicate<User> isActive =
        user -> user.isActive();

Predicate<User> isAdult =
        user -> user.getAge() >= 18;

Predicate<User> canAccessSystem =
        isActive.and(isAdult);
```

---

# 12. `Consumer<T>`

Cấu trúc:

```java
@FunctionalInterface
public interface Consumer<T> {
    void accept(T value);
}
```

Ví dụ:

```java
Consumer<String> printer =
        value -> System.out.println(value);
```

Gọi:

```java
printer.accept("Java");
```

Dùng khi:

- In dữ liệu
- Gửi thông báo
- Ghi log
- Lưu object
- Cập nhật trạng thái

Ví dụ:

```java
Consumer<User> printUser =
        user -> System.out.println(user.getName());
```

---

# 13. Lambda với `forEach()`

Cách truyền thống:

```java
List<String> names =
        Arrays.asList("Java", "Spring", "Hibernate");

for (String name : names) {
    System.out.println(name);
}
```

Dùng lambda:

```java
names.forEach(name -> System.out.println(name));
```

`forEach()` nhận `Consumer`.

Có thể hình dung:

```java
public void forEach(Consumer<String> action) {
    for (String element : this) {
        action.accept(element);
    }
}
```

Nhiều câu lệnh:

```java
names.forEach(name -> {
    String upperName = name.toUpperCase();

    System.out.println("Original: " + name);
    System.out.println("Uppercase: " + upperName);
});
```

Nếu xử lý dài, nên tách method:

```java
names.forEach(name -> printNameInformation(name));
```

hoặc:

```java
names.forEach(MyClass::printNameInformation);
```

---

# 14. `Function<T, R>`

Cấu trúc:

```java
@FunctionalInterface
public interface Function<T, R> {
    R apply(T value);
}
```

- `T`: kiểu đầu vào.
- `R`: kiểu kết quả.

Ví dụ:

```java
Function<String, Integer> getLength =
        text -> text.length();
```

Gọi:

```java
Integer length = getLength.apply("Java");

System.out.println(length); // 4
```

Ví dụ:

```java
Function<User, String> getUserName =
        user -> user.getName();
```

Phân biệt:

```text
Predicate<T>   : T → boolean
Function<T, R> : T → R
```

### Mapper entity sang DTO

```java
Function<User, UserDto> toDto =
        user -> new UserDto(
                user.getId(),
                user.getName()
        );
```

---

# 15. `Supplier<T>`

Cấu trúc:

```java
@FunctionalInterface
public interface Supplier<T> {
    T get();
}
```

Không nhận tham số, trả về một giá trị.

```java
Supplier<String> messageSupplier =
        () -> "Hello Java";

String message = messageSupplier.get();
```

Tạo object:

```java
Supplier<ArrayList<String>> listFactory =
        () -> new ArrayList<>();
```

Ứng dụng:

- Tạo object khi cần
- Lazy initialization
- Giá trị mặc định
- Factory
- Tạo exception

Ví dụ:

```java
User user = userOptional.orElseThrow(
        () -> new IllegalArgumentException("User not found")
);
```

---

# 16. `UnaryOperator<T>` và `BinaryOperator<T>`

## 16.1 `UnaryOperator<T>`

Nhận một `T`, trả về `T`:

```java
UnaryOperator<Integer> doubleValue =
        number -> number * 2;
```

Là trường hợp đặc biệt của:

```java
Function<T, T>
```

Ví dụ:

```java
List<String> names =
        new ArrayList<>(List.of("java", "spring"));

names.replaceAll(name -> name.toUpperCase());

System.out.println(names);
// [JAVA, SPRING]
```

## 16.2 `BinaryOperator<T>`

Nhận hai `T`, trả về `T`:

```java
BinaryOperator<Integer> addition =
        (a, b) -> a + b;
```

Ứng dụng:

- Cộng tổng
- Tìm max/min
- Kết hợp object
- Reduce dữ liệu

---

# 17. Lambda với `Comparator`

Cách cũ:

```java
Comparator<Student> comparator =
        new Comparator<Student>() {
            @Override
            public int compare(Student first, Student second) {
                return Integer.compare(
                        first.getAge(),
                        second.getAge()
                );
            }
        };
```

Lambda:

```java
Comparator<Student> comparator =
        (first, second) ->
                Integer.compare(
                        first.getAge(),
                        second.getAge()
                );
```

Sắp xếp:

```java
students.sort(comparator);
```

Viết trực tiếp:

```java
students.sort(
        (first, second) ->
                Integer.compare(
                        first.getAge(),
                        second.getAge()
                )
);
```

Cách rõ hơn:

```java
students.sort(
        Comparator.comparingInt(Student::getAge)
);
```

Giảm dần:

```java
students.sort(
        Comparator.comparingInt(Student::getAge)
                  .reversed()
);
```

Theo tên rồi tuổi:

```java
students.sort(
        Comparator.comparing(Student::getName)
                  .thenComparingInt(Student::getAge)
);
```

---

# 18. Lambda với Collection

### Xóa theo điều kiện

```java
List<Integer> numbers =
        new ArrayList<>(List.of(1, -2, 3, -4, 5));

numbers.removeIf(number -> number < 0);

System.out.println(numbers);
// [1, 3, 5]
```

### Thay đổi từng phần tử

```java
List<String> names =
        new ArrayList<>(List.of("java", "spring"));

names.replaceAll(name -> name.toUpperCase());
```

### Sắp xếp

```java
names.sort(
        (first, second) ->
                first.compareToIgnoreCase(second)
);
```

### Duyệt

```java
names.forEach(
        name -> System.out.println(name)
);
```

Bốn method thường dùng:

```java
forEach()
removeIf()
replaceAll()
sort()
```

---

# 19. Lambda với Thread

Cách cũ:

```java
Thread thread = new Thread(
        new Runnable() {
            @Override
            public void run() {
                System.out.println("Task is running");
            }
        }
);
```

Lambda:

```java
Thread thread = new Thread(
        () -> System.out.println("Task is running")
);

thread.start();
```

Nhiều câu lệnh:

```java
Thread thread = new Thread(() -> {
    System.out.println("Task started");

    for (int i = 1; i <= 3; i++) {
        System.out.println("Processing: " + i);
    }

    System.out.println("Task completed");
});
```

Trong ứng dụng hiện đại thường dùng executor:

```java
ExecutorService executor =
        Executors.newFixedThreadPool(4);

executor.submit(() -> {
    System.out.println("Processing order");
});
```

---

# 20. Event listener

Ví dụ JavaFX:

```java
button.setOnAction(event -> {
    System.out.println("Button clicked");
});
```

Ý nghĩa:

> Khi button được nhấn, thực hiện đoạn code này.

Ứng dụng tương tự:

- Người dùng nhấn nút
- Request được gửi đến
- Message được nhận
- File upload hoàn thành
- Một tác vụ thất bại

---

# 21. Method reference

Method reference là cách rút gọn lambda khi lambda chỉ gọi một method có sẵn.

```java
names.forEach(name -> System.out.println(name));
```

Rút gọn:

```java
names.forEach(System.out::println);
```

Cú pháp:

```text
ClassName::methodName
object::methodName
ClassName::new
```

### Static method reference

```java
Function<String, Integer> parser =
        value -> Integer.parseInt(value);
```

Rút gọn:

```java
Function<String, Integer> parser =
        Integer::parseInt;
```

### Instance method của object cụ thể

```java
Printer printer = message -> logger.log(message);
```

Rút gọn:

```java
Printer printer = logger::log;
```

### Instance method của tham số

```java
Function<String, String> upper =
        value -> value.toUpperCase();
```

Rút gọn:

```java
Function<String, String> upper =
        String::toUpperCase;
```

### Constructor reference

```java
Supplier<ArrayList<String>> supplier =
        () -> new ArrayList<>();
```

Rút gọn:

```java
Supplier<ArrayList<String>> supplier =
        ArrayList::new;
```

---

# 22. Lambda và biến bên ngoài

Lambda có thể dùng biến ngoài:

```java
int minimumAge = 18;

Predicate<User> isAdult =
        user -> user.getAge() >= minimumAge;
```

Biến local được capture phải là `final` hoặc **effectively final**.

Hợp lệ:

```java
int minimumAge = 18;

Predicate<User> isAdult =
        user -> user.getAge() >= minimumAge;
```

Không hợp lệ:

```java
int minimumAge = 18;

minimumAge = 21;

Predicate<User> isAdult =
        user -> user.getAge() >= minimumAge;
```

Không thể tăng biến local:

```java
int count = 0;

names.forEach(name -> {
    count++; // Compile error
});
```

### Object có thể thay đổi trạng thái

```java
List<String> results = new ArrayList<>();

names.forEach(name -> {
    results.add(name.toUpperCase());
});
```

`results` không bị gán sang list khác, nhưng nội dung list được thay đổi.

Cần cẩn thận khi chạy song song.

---

# 23. `this` trong lambda

Trong anonymous class, `this` chỉ anonymous object.

Trong lambda, `this` vẫn chỉ object của class bên ngoài.

```java
public class UserService {

    private String serviceName = "User Service";

    public void execute() {
        Runnable task = () -> {
            System.out.println(this.serviceName);
        };

        task.run();
    }
}
```

Tóm tắt:

```text
Anonymous class → có this riêng
Lambda          → không tạo scope this riêng
```

---

# 24. Lambda không tự chạy

```java
Runnable task = () -> {
    System.out.println("Running");
};
```

Đến đây chưa có gì được in.

Phải gọi:

```java
task.run();
```

hoặc:

```java
new Thread(task).start();
```

Tương tự:

```java
Predicate<Integer> isEven =
        number -> number % 2 == 0;
```

Chưa kiểm tra số nào cho đến khi gọi:

```java
isEven.test(10);
```

Có thể nhớ:

> Lambda là “việc cần làm”, functional method là cách kích hoạt việc đó.

---

# 25. Lambda và Stream

Ví dụ:

```java
List<String> names =
        List.of("An", "Binh", "Cuong", "Anh");
```

Lấy tên bắt đầu bằng `A`, chuyển chữ hoa:

```java
List<String> result = names.stream()
        .filter(name -> name.startsWith("A"))
        .map(name -> name.toUpperCase())
        .toList();
```

Phân tích:

```java
.filter(name -> name.startsWith("A"))
```

là `Predicate<String>`:

```text
String → boolean
```

```java
.map(name -> name.toUpperCase())
```

là `Function<String, String>`:

```text
String → String
```

Tư tưởng:

```text
Lấy dữ liệu
→ lọc
→ biến đổi
→ thu kết quả
```

---

# 26. Ví dụ thực tế hoàn chỉnh

Class:

```java
public class Product {

    private final String name;
    private final double price;
    private final boolean active;

    public Product(String name, double price, boolean active) {
        this.name = name;
        this.price = price;
        this.active = active;
    }

    public String getName() {
        return name;
    }

    public double getPrice() {
        return price;
    }

    public boolean isActive() {
        return active;
    }

    @Override
    public String toString() {
        return name + " - " + price;
    }
}
```

Dữ liệu:

```java
List<Product> products = new ArrayList<>(List.of(
        new Product("Laptop", 1200, true),
        new Product("Mouse", 25, true),
        new Product("Keyboard", 70, false),
        new Product("Monitor", 300, true)
));
```

### Xóa sản phẩm không hoạt động

```java
products.removeIf(product -> !product.isActive());
```

### Sắp xếp theo giá

```java
products.sort(
        Comparator.comparingDouble(Product::getPrice)
);
```

### In sản phẩm

```java
products.forEach(System.out::println);
```

### Predicate

```java
Predicate<Product> isExpensive =
        product -> product.getPrice() >= 500;
```

### Function

```java
Function<Product, String> getProductName =
        product -> product.getName();
```

Tóm tắt ý nghĩa:

```text
Predicate → kiểm tra
Function  → chuyển đổi
Consumer  → xử lý
Supplier  → cung cấp
```

---

# 27. Khi nào nên dùng lambda?

Lambda phù hợp khi phần hành vi:

- Ngắn
- Chỉ dùng ở một nơi
- Dễ hiểu khi đọc trực tiếp
- Được truyền vào method như quy tắc xử lý

Ví dụ tốt:

```java
users.removeIf(user -> !user.isActive());
```

```java
users.sort(Comparator.comparing(User::getName));
```

```java
users.forEach(System.out::println);
```

```java
Predicate<User> isAdult =
        user -> user.getAge() >= 18;
```

---

# 28. Khi nào nên tách thành method?

Lambda quá dài:

```java
orders.forEach(order -> {
    // Validate
    // Tính giá
    // Cập nhật kho
    // Gửi email
    // Ghi log
});
```

Nên tách:

```java
orders.forEach(this::processOrder);
```

```java
private void processOrder(Order order) {
    validateOrder(order);
    calculatePrice(order);
    updateInventory(order);
    sendConfirmationEmail(order);
}
```

Lambda nên mô tả rõ ý định, không nên trở thành một method lớn giấu trong `{}`.

---

# 29. Các lỗi thường gặp

## 29.1 Nhầm lambda là method độc lập

```java
number -> number * 2
```

Phải gán vào functional interface:

```java
Function<Integer, Integer> doubleValue =
        number -> number * 2;
```

## 29.2 Interface có nhiều abstract method

```java
interface Calculator {
    int add(int a, int b);
    int subtract(int a, int b);
}
```

Không thể dùng một lambda cho interface này.

## 29.3 Thiếu `return`

Sai:

```java
Function<Integer, Integer> doubleValue = number -> {
    int result = number * 2;
};
```

Đúng:

```java
Function<Integer, Integer> doubleValue = number -> {
    int result = number * 2;
    return result;
};
```

Hoặc:

```java
Function<Integer, Integer> doubleValue =
        number -> number * 2;
```

## 29.4 Sửa biến local được capture

Sai:

```java
int total = 0;

numbers.forEach(number -> total += number);
```

Có thể dùng vòng lặp thường:

```java
int total = 0;

for (Integer number : numbers) {
    total += number;
}
```

Hoặc Stream:

```java
int total = numbers.stream()
        .mapToInt(Integer::intValue)
        .sum();
```

## 29.5 Dùng lambda dù khó hiểu hơn

Thay vì:

```java
users.sort((a, b) -> {
    int nameResult = a.getName().compareTo(b.getName());

    if (nameResult != 0) {
        return nameResult;
    }

    return Integer.compare(a.getAge(), b.getAge());
});
```

Nên:

```java
users.sort(
        Comparator.comparing(User::getName)
                  .thenComparingInt(User::getAge)
);
```

---

# 30. Cách đọc lambda nhanh

```java
user -> user.isActive()
```

> Nhận `user`, trả về trạng thái active.

```java
user -> user.getName()
```

> Nhận `user`, trả về tên.

```java
user -> System.out.println(user)
```

> Nhận `user`, rồi in ra.

```java
() -> new User()
```

> Không nhận gì, tạo và trả về `User`.

```java
(a, b) -> a + b
```

> Nhận `a`, `b`, trả về tổng.

---

# 31. Quy trình hiểu một lambda

Ví dụ:

```java
numbers.removeIf(number -> number < 0);
```

### Bước 1: xem method nhận interface nào

`removeIf()` nhận:

```java
Predicate<? super E>
```

### Bước 2: xem abstract method

```java
boolean test(T value);
```

### Bước 3: ghép lambda

```java
number -> number < 0
```

tương đương:

```java
boolean test(Integer number) {
    return number < 0;
}
```

Ví dụ:

```java
names.forEach(name -> System.out.println(name));
```

`forEach()` nhận `Consumer`, có method:

```java
void accept(T value);
```

Lambda tương đương:

```java
void accept(String name) {
    System.out.println(name);
}
```

Cách đọc tốt nhất khi mới học:

> Xem functional interface trước, sau đó ghép lambda vào abstract method của nó.

---

# 32. Tổng kết Lambda

Cốt lõi không phải chỉ là dấu:

```java
->
```

Mà là:

> Biểu diễn và truyền một hành vi thông qua functional interface.

Ví dụ:

```java
@FunctionalInterface
interface Task {
    void execute();
}
```

```java
Task task = () -> System.out.println("Running");
```

```java
task.execute();
```

Bốn interface quan trọng nhất:

```text
Predicate<T>   : T → boolean
Function<T, R> : T → R
Consumer<T>    : T → void
Supplier<T>    : () → T
```

Ứng dụng với collection:

```java
list.forEach(item -> ...)
list.removeIf(item -> ...)
list.replaceAll(item -> ...)
list.sort((a, b) -> ...)
```

Method reference:

```java
names.forEach(System.out::println);
```

Điểm quan trọng:

> Lambda không phải function đứng riêng. Lambda là phần triển khai cho một functional interface mà compiler suy luận từ ngữ cảnh.

---

# Phần IV. Mối liên hệ giữa Collections, Generics và Lambda

Ba phần kết hợp với nhau rất chặt chẽ.

## 1. Collection quản lý dữ liệu

```java
List<User> users = new ArrayList<>();
```

`List` quyết định:

- Dữ liệu có thứ tự.
- Có thể trùng.
- Có index.
- Có thể thêm/xóa.

## 2. Generics bảo đảm kiểu dữ liệu

```java
List<User>
```

Generics bảo đảm:

- Chỉ thêm `User`.
- Lấy ra không cần ép kiểu.
- Compiler kiểm tra lỗi sớm.

## 3. Lambda mô tả cách xử lý dữ liệu

```java
users.removeIf(user -> !user.isActive());
```

Phân tích:

- `users` là `List<User>`.
- `removeIf()` nhận `Predicate<? super User>`.
- Lambda nhận một `User`.
- Lambda trả về `boolean`.
- Phần tử nào trả về `true` sẽ bị xóa.

Ví dụ khác:

```java
users.sort(Comparator.comparing(User::getName));
```

- Collection: danh sách người dùng.
- Generics: tất cả phần tử là `User`.
- Lambda/method reference: quy tắc sắp xếp theo tên.

Ví dụ Stream:

```java
List<String> activeUserNames = users.stream()
        .filter(User::isActive)
        .map(User::getName)
        .toList();
```

Phân tích:

```text
Collection:
users là danh sách dữ liệu.

Generics:
Stream<User>, Predicate<User>, Function<User, String>, List<String>.

Lambda/method reference:
User::isActive dùng để lọc.
User::getName dùng để biến đổi.
```

---

# Checklist ghi nhớ

## Collections

```text
List  → có thứ tự, có index, cho phép trùng
Set   → không trùng
Queue → hàng chờ
Deque → thao tác hai đầu, stack/queue
Map   → key-value
```

Lựa chọn mặc định thường gặp:

```text
List  → ArrayList
Set   → HashSet
Map   → HashMap
Queue/Deque → ArrayDeque
```

## Generics

```text
<T>                  → khai báo type parameter
<?>                  → không biết kiểu
<? extends T>        → đọc
<? super T>          → ghi
PECS                  → Producer Extends, Consumer Super
Raw type             → nên tránh
```

## Lambda

```text
Predicate<T>   → kiểm tra điều kiện
Function<T,R>  → biến đổi
Consumer<T>    → xử lý không trả về
Supplier<T>    → cung cấp dữ liệu
```

Method collection thường dùng lambda:

```java
forEach()
removeIf()
replaceAll()
sort()
```

---

# Bài tập tự luyện

## Bài 1: List và Set

Cho danh sách:

```java
List<String> names = List.of(
        "An", "Bình", "An", "Cường", "Bình"
);
```

Yêu cầu:

1. Chuyển sang danh sách không trùng.
2. Giữ thứ tự xuất hiện ban đầu.
3. In từng tên bằng lambda.

Gợi ý:

```java
Set<String> uniqueNames = new LinkedHashSet<>(names);

uniqueNames.forEach(System.out::println);
```

---

## Bài 2: Map đếm tần suất

Cho:

```java
List<String> languages = List.of(
        "Java", "SQL", "Java", "Spring", "Java", "SQL"
);
```

Đếm số lần mỗi phần tử xuất hiện bằng `Map<String, Integer>`.

Gợi ý:

```java
Map<String, Integer> counts = new HashMap<>();

for (String language : languages) {
    counts.put(
            language,
            counts.getOrDefault(language, 0) + 1
    );
}
```

---

## Bài 3: Generic class

Tạo class:

```java
class Box<T>
```

Có:

```java
void set(T value)
T get()
```

Sử dụng với:

```java
Box<String>
Box<Integer>
Box<User>
```

---

## Bài 4: Generic method

Viết method:

```java
static <T> T getLast(List<T> list)
```

Ví dụ:

```java
String lastName = getLast(List.of("An", "Bình", "Cường"));
Integer lastNumber = getLast(List.of(10, 20, 30));
```

---

## Bài 5: Wildcard

Viết method tính tổng:

```java
static double sum(List<? extends Number> numbers)
```

Thử với:

```java
List<Integer>
List<Double>
List<Long>
```

---

## Bài 6: Lambda và Predicate

Cho:

```java
List<Integer> numbers =
        List.of(-5, -2, 0, 1, 4, 7, 10);
```

Viết method:

```java
static List<Integer> filter(
        List<Integer> numbers,
        Predicate<Integer> predicate
)
```

Dùng method để lọc:

1. Số dương.
2. Số chẵn.
3. Số lớn hơn 5.
4. Số vừa dương vừa chẵn.

---

## Bài 7: Product

Tạo class:

```java
class Product {
    String name;
    double price;
    boolean active;
}
```

Yêu cầu:

1. Dùng `removeIf()` xóa sản phẩm không active.
2. Dùng `sort()` sắp xếp giá tăng dần.
3. Dùng `forEach()` in sản phẩm.
4. Dùng Stream lấy tên sản phẩm có giá lớn hơn 100.

---

# Kết luận

Ba chủ đề này tạo thành nền tảng rất quan trọng của Java hiện đại:

```text
Collections → tổ chức dữ liệu
Generics    → bảo đảm kiểu dữ liệu
Lambda      → truyền hành vi xử lý
```

Khi kết hợp:

```java
List<User> users = new ArrayList<>();

users.removeIf(user -> !user.isActive());

users.sort(
        Comparator.comparing(User::getName)
);

users.forEach(System.out::println);
```

Bạn đang đồng thời sử dụng:

- `List` và `ArrayList` của Collections Framework.
- `User` làm generic type.
- Lambda và method reference để xử lý dữ liệu.

Đây là nền tảng trực tiếp để học tiếp:

```text
Comparable và Comparator
Stream API
Optional
Spring Data Repository
Functional programming trong Java
```
