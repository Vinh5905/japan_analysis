# Java Threads

> Tài liệu tổng hợp phần **Thread trong Java**: khái niệm, cách tạo thread, vòng đời, đồng bộ hóa, race condition, lock, thread pool và virtual thread.

---

## Mục lục

1. Thread là gì?
2. Process và Thread
3. Concurrency và Parallelism
4. `start()` và `run()`
5. Vòng đời Thread
6. Các cách tạo Thread
7. `sleep()`, `join()`, `interrupt()`
8. Race Condition
9. `synchronized`
10. `Lock` và `ReentrantLock`
11. `wait()`, `notify()`, Deadlock
12. `volatile` và Atomic
13. Thread-safe Collections
14. `ExecutorService`, `Callable`, `Future`
15. Virtual Threads
16. Ví dụ thực tế
17. Tổng kết

---

# 1. Thread là gì?

Thread là một **luồng thực thi** bên trong một chương trình.

Một ứng dụng Java có thể có nhiều thread cùng tồn tại:

```text
Java Application Process
│
├── Main thread
├── Worker thread 1
├── Worker thread 2
└── Garbage Collector thread
```

Ví dụ một ứng dụng bán hàng:

```text
Thread 1 → nhận request
Thread 2 → đọc database
Thread 3 → gửi email
Thread 4 → ghi log
```

Cốt lõi:

> **Thread là một đường thực thi độc lập bên trong cùng một process.**

---

# 2. Process và Thread

## Process

Process là một chương trình đang chạy.

Ví dụ:

- IntelliJ IDEA
- Chrome
- Spotify
- Một ứng dụng Java

Mỗi process thường có:

- Không gian bộ nhớ riêng
- Heap riêng
- Tài nguyên riêng
- Một hoặc nhiều thread

## Thread

Các thread trong cùng process chia sẻ:

- Heap
- Object
- Static field
- File
- Connection
- Các tài nguyên dùng chung

Nhưng mỗi thread có stack riêng:

```text
Thread 1 stack:
methodA()
methodB()
local variables

Thread 2 stack:
methodX()
methodY()
local variables
```

Vì các thread chia sẻ object trong heap nên có thể xảy ra race condition.

---

# 3. Main Thread

Khi chạy:

```java
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
```

JVM đã có sẵn một thread chạy method `main()`.

Lấy thread hiện tại:

```java
public class Main {
    public static void main(String[] args) {
        Thread current = Thread.currentThread();

        System.out.println("Name: " + current.getName());
        System.out.println("ID: " + current.threadId());
        System.out.println("State: " + current.getState());
    }
}
```

Tên thread thường là:

```text
main
```

---

# 4. Concurrency và Parallelism

## Concurrency

Nhiều công việc cùng tiến triển trong một khoảng thời gian.

```text
Thời gian →

Task A: chạy ── dừng ── chạy ───── dừng
Task B:      chạy ── dừng ── chạy
```

CPU có thể chuyển đổi rất nhanh:

```text
Thread A → Thread B → Thread A → Thread B
```

## Parallelism

Nhiều công việc thực sự chạy cùng lúc trên nhiều CPU core:

```text
Core 1 → Thread A
Core 2 → Thread B
```

Ghi nhớ:

```text
Concurrency = nhiều công việc cùng tiến triển
Parallelism = nhiều công việc chạy cùng thời điểm
```

---

# 5. Vì sao dùng nhiều Thread?

Một thread:

```text
Task 1 → chờ database → Task 1 → chờ file → Task 2
```

Hai thread:

```text
Thread 1: Task 1 → chờ database ─────────→ Task 1
Thread 2:          Task 2 → xử lý ───────→ Task 2
```

Thread hữu ích cho:

- Web server xử lý nhiều request
- Gọi database hoặc API
- Download nhiều file
- Gửi email nền
- Giữ GUI không bị đứng
- Xử lý nhiều kết nối

Nhưng nhiều thread không luôn nhanh hơn. Quá nhiều thread gây:

- Context switching
- Tốn bộ nhớ stack
- Tranh chấp tài nguyên
- Khó đồng bộ
- Hiệu năng giảm

---

# 6. `start()` và `run()`

```java
Thread thread = new Thread(() -> {
    System.out.println(
            "Running in: " +
            Thread.currentThread().getName()
    );
});
```

## `start()`

```java
thread.start();
```

`start()` yêu cầu JVM tạo hoặc lên lịch một thread mới, rồi thread mới thực hiện `run()`.

```text
main thread
    │
    └── start()
           │
           └── new thread executes run()
```

## `run()`

```java
thread.run();
```

Đây chỉ là gọi method bình thường trên thread hiện tại.

Ví dụ:

```java
public class StartVsRunDemo {
    public static void main(String[] args) {
        Thread thread = new Thread(() -> {
            System.out.println(
                    "Task: " +
                    Thread.currentThread().getName()
            );
        });

        System.out.println(
                "Main: " +
                Thread.currentThread().getName()
        );

        thread.run();
    }
}
```

Kết quả:

```text
Main: main
Task: main
```

Đổi thành:

```java
thread.start();
```

Kết quả thường là:

```text
Main: main
Task: Thread-0
```

Ghi nhớ:

```text
start() → tạo/lên lịch thread mới
run()   → gọi method bình thường
```

Một object `Thread` chỉ được `start()` một lần.

---

# 7. Vòng đời Thread

Java có sáu trạng thái:

```text
NEW
RUNNABLE
BLOCKED
WAITING
TIMED_WAITING
TERMINATED
```

## `NEW`

Đã tạo nhưng chưa gọi `start()`:

```java
Thread thread = new Thread(() -> {
    System.out.println("Running");
});

System.out.println(thread.getState());
// NEW
```

## `RUNNABLE`

Sau khi gọi `start()`.

Bao gồm:

- Đang chạy trên CPU
- Sẵn sàng chạy nhưng chờ scheduler

## `BLOCKED`

Đang chờ monitor lock của `synchronized`.

```java
synchronized (lock) {
    // critical section
}
```

## `WAITING`

Chờ vô thời hạn:

```java
object.wait();
thread.join();
```

## `TIMED_WAITING`

Chờ có thời hạn:

```java
Thread.sleep(2000);
object.wait(2000);
thread.join(2000);
```

## `TERMINATED`

Method `run()` đã kết thúc hoặc thread dừng do exception.

Sơ đồ:

```text
       new Thread(...)
              │
              ▼
             NEW
              │ start()
              ▼
          RUNNABLE
          /   |   \
         /    |    \
        ▼     ▼     ▼
    BLOCKED WAITING TIMED_WAITING
        \      |      /
         \     |     /
          └─ RUNNABLE
              │
              ▼
         TERMINATED
```

---

# 8. Tạo Thread bằng cách kế thừa `Thread`

```java
public class DownloadThread extends Thread {

    @Override
    public void run() {
        System.out.println(
                getName() + " is downloading..."
        );
    }
}
```

Sử dụng:

```java
public class Main {
    public static void main(String[] args) {
        DownloadThread thread = new DownloadThread();

        thread.setName("download-thread");
        thread.start();
    }
}
```

Ưu điểm:

- Dễ hiểu khi mới học
- Dùng trực tiếp method của `Thread`

Hạn chế:

- Java chỉ cho kế thừa một class
- Gắn chặt task với thread

---

# 9. Tạo Thread bằng `Runnable`

`Runnable` là functional interface:

```java
@FunctionalInterface
public interface Runnable {
    void run();
}
```

Tạo task:

```java
public class DownloadTask implements Runnable {

    @Override
    public void run() {
        System.out.println(
                Thread.currentThread().getName()
                + " is downloading..."
        );
    }
}
```

Đưa task vào thread:

```java
public class Main {
    public static void main(String[] args) {
        Runnable task = new DownloadTask();

        Thread thread = new Thread(
                task,
                "download-thread"
        );

        thread.start();
    }
}
```

Tách biệt:

```text
DownloadTask → công việc
Thread       → phương tiện chạy công việc
```

Cách này thường được ưu tiên hơn kế thừa `Thread`.

---

# 10. Tạo Thread bằng Lambda

```java
Thread thread = new Thread(() -> {
    System.out.println(
            Thread.currentThread().getName()
            + " is running"
    );
});

thread.start();
```

Đặt tên:

```java
Thread thread = new Thread(
        () -> System.out.println("Processing order"),
        "order-worker"
);

thread.start();
```

---

# 11. Constructor thường dùng

```java
new Thread()
```

```java
new Thread(Runnable task)
```

```java
new Thread(String name)
```

```java
new Thread(Runnable task, String name)
```

Ví dụ:

```java
Runnable task = () -> {
    System.out.println("Processing...");
};

Thread thread = new Thread(task, "payment-worker");

thread.start();
```

---

# 12. Một số lỗi thường gặp

## `Runnable` không phải `Thread`

Sai:

```java
public class IOTask implements Runnable {
    @Override
    public void run() {
    }
}

Thread t2 = new IOTask(); // Sai
```

Đúng:

```java
Runnable task = new IOTask();
Thread t2 = new Thread(task);

t2.start();
```

## `this.getName()` trong `Runnable`

Trong `Runnable`, `this` là object task, không phải `Thread`.

Sai:

```java
this.getName()
```

Đúng:

```java
Thread.currentThread().getName()
```

## Main không tự chờ worker

```java
worker.start();

System.out.println("main finished");
```

Main có thể in xong trước worker.

Muốn chờ:

```java
worker.start();
worker.join();

System.out.println("main finished");
```

---

# 13. `sleep()`

```java
Thread.sleep(2000);
```

Làm thread hiện tại dừng tạm khoảng hai giây.

```java
public class SleepDemo {
    public static void main(String[] args) {
        System.out.println("Start");

        try {
            Thread.sleep(2000);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
        }

        System.out.println("Finish");
    }
}
```

Nên viết:

```java
Thread.sleep(2000);
```

không nên gọi qua object vì `sleep()` là static method.

---

# 14. `interrupt()` và `InterruptedException`

Không nên dùng:

```java
thread.stop();
```

Nên dừng theo kiểu hợp tác bằng `interrupt()`.

```java
public class Worker implements Runnable {

    @Override
    public void run() {
        while (!Thread.currentThread().isInterrupted()) {
            System.out.println("Working...");

            try {
                Thread.sleep(1000);
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        System.out.println("Worker stopped safely");
    }
}
```

Main:

```java
public class Main {
    public static void main(String[] args)
            throws InterruptedException {

        Thread worker = new Thread(
                new Worker(),
                "worker"
        );

        worker.start();

        Thread.sleep(3000);

        worker.interrupt();
        worker.join();
    }
}
```

`interrupt()` không giết thread ngay. Nó gửi tín hiệu yêu cầu thread dừng hoặc xử lý interruption.

Không nên nuốt exception:

```java
catch (InterruptedException exception) {
    // Không làm gì
}
```

Nên:

```java
catch (InterruptedException exception) {
    Thread.currentThread().interrupt();
    return;
}
```

---

# 15. `join()`

Không có `join()`:

```java
worker.start();

System.out.println("Main finished");
```

Main có thể kết thúc trước worker.

Có `join()`:

```java
worker.start();
worker.join();

System.out.println("Main finished");
```

Kết quả:

```text
Worker started
Worker finished
Main finished
```

`join()` làm thread hiện tại chờ thread mục tiêu kết thúc.

---

# 16. Thread Priority

```java
Thread.MIN_PRIORITY  // 1
Thread.NORM_PRIORITY // 5
Thread.MAX_PRIORITY  // 10
```

Ví dụ:

```java
Thread low = new Thread(task, "low");
Thread high = new Thread(task, "high");

low.setPriority(Thread.MIN_PRIORITY);
high.setPriority(Thread.MAX_PRIORITY);
```

Priority chỉ là gợi ý cho scheduler.

Không được dùng priority để đảm bảo thứ tự chạy.

---

# 17. Shared Mutable Data

```java
public class Counter {
    private int count = 0;

    public void increment() {
        count++;
    }

    public int getCount() {
        return count;
    }
}
```

Hai thread cùng tăng:

```java
Counter counter = new Counter();

Runnable task = () -> {
    for (int i = 0; i < 100_000; i++) {
        counter.increment();
    }
};

Thread first = new Thread(task);
Thread second = new Thread(task);

first.start();
second.start();

first.join();
second.join();

System.out.println(counter.getCount());
```

Kỳ vọng `200000`, nhưng có thể nhỏ hơn.

Lý do `count++` gồm nhiều bước:

```text
1. Đọc count
2. Tăng 1
3. Ghi lại count
```

Hai thread có thể cùng đọc giá trị cũ rồi ghi đè kết quả của nhau.

---

# 18. Race Condition

Race condition xảy ra khi kết quả phụ thuộc vào thứ tự các thread truy cập dữ liệu chung.

Ví dụ:

```text
Thread A rút $80
Thread B rút $50
Số dư ban đầu: $100
```

Critical section:

```java
if (balance >= amount) {
    balance -= amount;
}
```

Toàn bộ phần kiểm tra và cập nhật phải được bảo vệ cùng nhau.

---

# 19. `synchronized`

Java dùng monitor để đồng bộ hóa.

```java
synchronized (lock) {
    // critical section
}
```

Cốt lõi:

> `synchronized` khóa monitor của một object cụ thể.

Tại một thời điểm chỉ một thread giữ được cùng một monitor lock.

---

# 20. `synchronized` Instance Method

```java
public class SynchronizedCounter {
    private int count;

    public synchronized void increment() {
        count++;
    }

    public synchronized int getCount() {
        return count;
    }
}
```

Gần tương đương:

```java
public void increment() {
    synchronized (this) {
        count++;
    }
}
```

Instance synchronized method dùng lock:

```java
this
```

Hai object khác nhau có hai lock khác nhau.

---

# 21. `synchronized` Block

Khóa toàn bộ method:

```java
public synchronized void addName(String name) {
    validate(name);
    lastName = name;
    nameCount++;
    nameList.add(name);
    writeLog(name);
}
```

Chỉ khóa critical section:

```java
public void addName(String name) {
    validate(name);

    synchronized (this) {
        lastName = name;
        nameCount++;
    }

    nameList.add(name);
    writeLog(name);
}
```

Lợi ích:

- Giữ lock ngắn hơn
- Giảm tranh chấp
- Tăng khả năng chạy đồng thời

Nhưng mọi shared mutable data liên quan vẫn phải được bảo vệ đúng cách.

---

# 22. Dùng đúng cùng một Lock

```java
private final Object lock = new Object();
```

```java
public void increment() {
    synchronized (lock) {
        count++;
    }
}
```

```java
public int getCount() {
    synchronized (lock) {
        return count;
    }
}
```

Sai:

```java
public void increment() {
    synchronized (new Object()) {
        count++;
    }
}
```

Mỗi lần gọi tạo một lock mới nên các thread không chặn nhau.

---

# 23. Nhiều Lock cho dữ liệu độc lập

```java
public class TwoCounters {
    private long count1;
    private long count2;

    private final Object lock1 = new Object();
    private final Object lock2 = new Object();

    public void incrementFirst() {
        synchronized (lock1) {
            count1++;
        }
    }

    public void incrementSecond() {
        synchronized (lock2) {
            count2++;
        }
    }
}
```

Hai dữ liệu độc lập có thể dùng hai lock khác nhau để chạy song song.

---

# 24. `static synchronized`

```java
public class Screen {
    private static Screen instance;

    public static synchronized Screen getInstance() {
        if (instance == null) {
            instance = new Screen();
        }

        return instance;
    }
}
```

Static synchronized method khóa:

```java
Screen.class
```

Tương đương:

```java
public static Screen getInstance() {
    synchronized (Screen.class) {
        if (instance == null) {
            instance = new Screen();
        }

        return instance;
    }
}
```

Phân biệt:

```text
instance synchronized → khóa this
static synchronized   → khóa ClassName.class
```

---

# 25. `Lock` và `ReentrantLock`

Sai:

```java
private Lock lock = new Lock();
```

Vì `Lock` là interface.

Đúng:

```java
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

private final Lock lock = new ReentrantLock();
```

Sử dụng:

```java
public class Counter {
    private final Lock lock = new ReentrantLock();
    private int count;

    public int incrementAndGet() {
        lock.lock();

        try {
            return ++count;
        } finally {
            lock.unlock();
        }
    }
}
```

Phải `unlock()` trong `finally` để luôn nhả lock kể cả khi có exception.

---

# 26. `synchronized` hay `ReentrantLock`

Dùng `synchronized` khi:

- Critical section đơn giản
- Chỉ cần mutual exclusion
- Muốn tự động nhả lock

Dùng `ReentrantLock` khi cần:

- `tryLock()`
- Timeout
- Interruptible locking
- Fairness
- Nhiều `Condition`

Ví dụ:

```java
if (lock.tryLock()) {
    try {
        // critical section
    } finally {
        lock.unlock();
    }
}
```

---

# 27. `wait()`, `notify()`, `notifyAll()`

Các method này thuộc `Object`:

```java
object.wait();
object.notify();
object.notifyAll();
```

Phải giữ monitor trước khi gọi:

```java
synchronized (lock) {
    lock.wait();
}
```

Khi gọi `wait()`:

1. Thread vào wait set
2. Nhả monitor
3. Chờ `notify()` hoặc `notifyAll()`
4. Tranh lấy lại monitor
5. Tiếp tục chạy

Mẫu đúng:

```java
synchronized (lock) {
    while (!conditionIsTrue()) {
        lock.wait();
    }

    useSharedResource();
}
```

Trong thực tế thường ưu tiên abstraction cao hơn như `BlockingQueue`.

---

# 28. Deadlock

```text
Thread A giữ lock1 và chờ lock2
Thread B giữ lock2 và chờ lock1
```

Ví dụ:

```java
synchronized (lock1) {
    synchronized (lock2) {
        // ...
    }
}
```

Nơi khác:

```java
synchronized (lock2) {
    synchronized (lock1) {
        // ...
    }
}
```

Cách tránh:

- Luôn lấy lock theo cùng thứ tự
- Giữ ít lock nhất có thể
- Không gọi code ngoài khi giữ lock
- Dùng `tryLock()` với timeout
- Dùng abstraction concurrent cấp cao hơn

---

# 29. Memory Visibility và `volatile`

```java
public class StopFlag {
    private boolean running = true;

    public void runLoop() {
        while (running) {
            // work
        }
    }

    public void stop() {
        running = false;
    }
}
```

Thread loop có thể không thấy giá trị mới ngay.

Dùng:

```java
private volatile boolean running = true;
```

`volatile` phù hợp với cờ đơn giản.

Nhưng:

```java
private volatile int count;

count++;
```

vẫn không atomic.

---

# 30. Atomic Classes

```java
import java.util.concurrent.atomic.AtomicInteger;

public class Counter {
    private final AtomicInteger count =
            new AtomicInteger();

    public void increment() {
        count.incrementAndGet();
    }

    public int getCount() {
        return count.get();
    }
}
```

Một số class atomic:

```text
AtomicInteger
AtomicLong
AtomicBoolean
AtomicReference
```

---

# 31. Thread-safe Collections

Không thread-safe mặc định:

```java
ArrayList
HashMap
HashSet
```

Concurrent collections:

```java
ConcurrentHashMap
CopyOnWriteArrayList
BlockingQueue
ConcurrentLinkedQueue
```

Ví dụ:

```java
Map<String, User> cache =
        new ConcurrentHashMap<>();
```

Producer-consumer:

```java
BlockingQueue<Order> queue =
        new LinkedBlockingQueue<>();
```

Producer:

```java
queue.put(order);
```

Consumer:

```java
Order order = queue.take();
```

---

# 32. `ExecutorService`

Trong bài học:

```java
new Thread(task).start();
```

Trong ứng dụng thật thường dùng:

```java
ExecutorService executor =
        Executors.newFixedThreadPool(4);

executor.submit(() -> {
    System.out.println(
            "Processing in " +
            Thread.currentThread().getName()
    );
});

executor.shutdown();
```

Lợi ích:

- Tái sử dụng worker thread
- Giới hạn số thread
- Quản lý shutdown
- Hỗ trợ Future
- Tách task khỏi thread

---

# 33. `Runnable`, `Callable`, `Future`

## `Runnable`

Không trả về kết quả:

```java
executor.submit(() -> {
    System.out.println("Saving data");
});
```

## `Callable<T>`

Trả về kết quả:

```java
Callable<Integer> task = () -> {
    return 10 + 20;
};
```

## `Future<T>`

Nhận kết quả sau:

```java
Future<Integer> future = executor.submit(() -> {
    return 10 + 20;
});

Integer result = future.get();

System.out.println(result); // 30
```

`future.get()` sẽ chờ nếu task chưa xong.

---

# 34. Virtual Threads

Virtual thread nhẹ hơn platform thread và phù hợp với số lượng lớn tác vụ blocking I/O.

```java
Thread thread = Thread.startVirtualThread(() -> {
    System.out.println(
            "Virtual: " +
            Thread.currentThread().isVirtual()
    );
});
```

Hoặc:

```java
Thread thread = Thread.ofVirtual()
        .name("request-handler")
        .start(() -> processRequest());
```

Executor virtual thread:

```java
try (ExecutorService executor =
             Executors.newVirtualThreadPerTaskExecutor()) {

    for (int i = 0; i < 10_000; i++) {
        executor.submit(() -> callRemoteApi());
    }
}
```

Phù hợp:

- Database
- REST API
- File I/O
- Network
- Nhiều request độc lập

Không đặc biệt có lợi cho CPU-intensive task.

---

# 35. Chọn công cụ trong thực tế

| Nhu cầu | Công cụ |
|---|---|
| Học nguyên lý | `new Thread(task)` |
| Worker CPU-bound | Fixed thread pool |
| Nhiều tác vụ I/O | Virtual threads |
| Task trả kết quả | `Callable`, `Future` |
| Async pipeline | `CompletableFuture` |
| Producer-consumer | `BlockingQueue` |
| Counter đơn giản | `AtomicInteger` |
| Map dùng chung | `ConcurrentHashMap` |
| Lock đơn giản | `synchronized` |
| Lock có timeout | `ReentrantLock` |

---

# 36. Ví dụ hoàn chỉnh

## `Runnable`, `sleep()`, `join()`

```java
public final class IOTask implements Runnable {

    @Override
    public void run() {
        Thread current = Thread.currentThread();

        System.out.println(
                current.getName() + " started"
        );

        try {
            Thread.sleep(2000);
        } catch (InterruptedException exception) {
            current.interrupt();

            System.out.println(
                    current.getName() + " interrupted"
            );

            return;
        }

        System.out.println(
                current.getName() + " finished"
        );
    }
}
```

Main:

```java
public class Main {

    public static void main(String[] args) {
        Thread mainThread = Thread.currentThread();

        System.out.println(
                mainThread.getName() + " started"
        );

        Thread worker = new Thread(
                new IOTask(),
                "io-worker"
        );

        worker.start();

        try {
            worker.join();
        } catch (InterruptedException exception) {
            mainThread.interrupt();
            return;
        }

        System.out.println(
                mainThread.getName() + " finished"
        );
    }
}
```

## Tài khoản ngân hàng thread-safe

```java
public final class BankAccount {
    private long balance;

    public BankAccount(long initialBalance) {
        if (initialBalance < 0) {
            throw new IllegalArgumentException(
                    "Initial balance cannot be negative"
            );
        }

        this.balance = initialBalance;
    }

    public synchronized boolean withdraw(long amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException(
                    "Amount must be positive"
            );
        }

        if (balance < amount) {
            return false;
        }

        balance -= amount;
        return true;
    }

    public synchronized long getBalance() {
        return balance;
    }
}
```

Chạy:

```java
public class Main {
    public static void main(String[] args)
            throws InterruptedException {

        BankAccount account = new BankAccount(100);

        Runnable withdrawTask = () -> {
            boolean success = account.withdraw(80);

            System.out.println(
                    Thread.currentThread().getName()
                    + ": "
                    + success
            );
        };

        Thread first =
                new Thread(withdrawTask, "customer-1");

        Thread second =
                new Thread(withdrawTask, "customer-2");

        first.start();
        second.start();

        first.join();
        second.join();

        System.out.println(
                "Balance: " + account.getBalance()
        );
    }
}
```

Một thread thành công, một thread thất bại, số dư vẫn đúng.

---

# 37. Cách tư duy khi thiết kế đa luồng

Trước khi tạo thread, hỏi:

## Công việc CPU-bound hay I/O-bound?

```text
CPU-bound:
- Tính toán
- Nén dữ liệu
- Xử lý ảnh
- Mã hóa

I/O-bound:
- Database
- HTTP
- File
- Network
```

## Có thật sự cần đa luồng không?

Nếu code đơn luồng đủ nhanh và đơn giản, không cần thêm concurrency.

## Có chia sẻ mutable state không?

Ưu tiên:

- Immutable object
- Local variable
- Message passing
- Thread-safe collection
- Task sở hữu dữ liệu riêng

## Invariant là gì?

Ví dụ:

```text
balance không được âm
```

Toàn bộ kiểm tra và cập nhật phải nằm trong cùng critical section.

## Lock nào bảo vệ field nào?

Có thể ghi:

```java
// Guarded by accountLock
private long balance;
```

## Thread dừng bằng cách nào?

Ưu tiên:

```java
interrupt()
```

Không dùng:

```java
Thread.stop()
```

---

# 38. Tổng kết

```text
Thread = một luồng thực thi bên trong process
```

Phân biệt:

```java
thread.start();
```

Tạo hoặc lên lịch thread mới.

```java
thread.run();
```

Chỉ gọi method trên thread hiện tại.

Trạng thái:

```text
NEW
RUNNABLE
BLOCKED
WAITING
TIMED_WAITING
TERMINATED
```

Cách tạo cơ bản:

```java
class MyThread extends Thread
```

```java
class MyTask implements Runnable
```

Trong thực tế thường tách task:

```java
Runnable task = ...
new Thread(task).start();
```

hoặc:

```java
executor.submit(task);
```

Các rủi ro chính:

```text
Race condition
Lost update
Visibility problem
Deadlock
```

Công cụ thường dùng:

```text
synchronized
ReentrantLock
volatile
AtomicInteger
ConcurrentHashMap
BlockingQueue
ExecutorService
Virtual Thread
```

Nguyên tắc quan trọng nhất:

> **Đừng bắt đầu bằng câu hỏi “làm sao tạo nhiều thread?”. Hãy bắt đầu bằng câu hỏi “công việc nào có thể chạy độc lập, dữ liệu nào đang được chia sẻ, và ai chịu trách nhiệm đồng bộ nó?”.**
