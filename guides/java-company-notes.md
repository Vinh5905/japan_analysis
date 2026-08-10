# Ghi Chú Học Java Từ Tài Liệu Công Ty

> File này sẽ được cập nhật dần theo từng trang slide bạn gửi.

## Mục Lục Tạm Thời

- [1.1 Introduce - Giới thiệu Java](#11-introduce---giới-thiệu-java)
- [1.2 Features of Java - Đặc tính của Java](#12-features-of-java---đặc-tính-của-java)
- [2. JDK, JRE and JVM](#2-jdk-jre-and-jvm)
- [3. Install](#3-install)
- [4. Class and Objects](#4-class-and-objects)
- [4.1 Relationship between a class and its object](#41-relationship-between-a-class-and-its-object)
- [4.2 Class - overview](#42-class---overview)
- [4.3 Class - example](#43-class---example)
- [4.4 Class - Internal structure](#44-class---internal-structure)
- [4.5 Access modifier](#45-access-modifier)
- [4.6 Objects](#46-objects)
- [5. Variables](#5-variables)
- [5.1 Variables - example](#51-variables---example)
- [5.2 Constructor](#52-constructor)
- [5.3 Methods](#53-methods)
- [5.4 Methods - types và static method](#54-methods---types-và-static-method)
- [5.5 Overloading of methods](#55-overloading-of-methods)
- [5.6 Difference between constructor and method](#56-difference-between-constructor-and-method)
- [5.7 Using `this` keyword](#57-using-this-keyword)
- [6. Data type and Operator](#6-data-type-and-operator)
- [6.1 Data type](#61-data-type)
- [6.2 Operator](#62-operator)

## Cách Đọc Ghi Chú

Tài liệu được trình bày theo cấu trúc:

- **Tóm tắt:** nội dung chính của slide.
- **Ý chính cần nhớ:** các điểm nên ghi nhớ khi học Java.
- **Ví dụ production:** cách kiến thức này thường xuất hiện trong code thật.
- **Lưu ý chương:** các lỗi dễ gặp, trade-off và best practice được gom ở cuối mỗi chương lớn.

## 1.1 Introduce - Giới Thiệu Java

### Tóm tắt

Java là một ngôn ngữ lập trình bậc cao, hướng đối tượng, mã nguồn mở, có cộng đồng lớn và có khả năng chạy trên nhiều nền tảng thông qua JVM. Java được sử dụng rộng rãi trong lập trình web/backend, thiết bị di động, game, hệ thống thương mại điện tử và các giải pháp doanh nghiệp.

### Ý chính cần nhớ

- **High-level programming language:** Java che bớt nhiều chi tiết cấp thấp như quản lý bộ nhớ thủ công, con trỏ trực tiếp, thao tác phần cứng. Lập trình viên tập trung nhiều hơn vào business logic.
- **Object-oriented language (OOP):** Java tổ chức chương trình quanh class, object, encapsulation, inheritance, polymorphism và abstraction.
- **Widely used OOP:** Java rất phổ biến trong hệ thống doanh nghiệp vì ổn định, có hệ sinh thái thư viện lớn và nhiều framework trưởng thành như Spring, Hibernate, Maven, Gradle.
- **Open source:** OpenJDK là bản triển khai mã nguồn mở của Java Platform. Nhiều công ty dùng OpenJDK hoặc các bản phân phối như Temurin, Corretto, Zulu.
- **Secured:** Java có nhiều cơ chế giúp viết phần mềm an toàn hơn như type safety, bytecode verification, classloader, quản lý bộ nhớ qua garbage collector. Tuy vậy, bảo mật ứng dụng vẫn phụ thuộc vào cách thiết kế authentication, authorization, validation, logging và quản lý dependency.
- **Cross-platforms:** Code Java thường được biên dịch thành bytecode và chạy trên JVM. Cùng một file `.jar` có thể chạy trên Windows, Linux hoặc macOS nếu có JVM phù hợp.
- **Community:** Cộng đồng Java lớn giúp dễ tìm tài liệu, thư viện, best practice và giải pháp cho lỗi production.
- **Ứng dụng thực tế:** Java thường gặp trong backend API, hệ thống ngân hàng, thương mại điện tử, xử lý đơn hàng, thanh toán, logistics, Android app, game server và internal enterprise tools.

### Ví dụ production

Trong một hệ thống thương mại điện tử, Java thường được dùng để xây dựng backend service xử lý đơn hàng. Ví dụ một API tạo đơn hàng bằng Spring Boot:

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
            @Valid @RequestBody CreateOrderRequest request) {
        OrderResponse response = orderService.createOrder(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
```

Trong ví dụ này:

- `OrderController` nhận request từ client qua HTTP.
- `OrderService` chứa business logic tạo đơn hàng.
- `CreateOrderRequest` và `OrderResponse` là object đại diện cho dữ liệu vào/ra.
- Annotation như `@RestController`, `@PostMapping`, `@Valid` giúp code ngắn gọn hơn nhưng vẫn rõ trách nhiệm.

Đây là cách OOP xuất hiện trong production: mỗi class có một vai trò rõ ràng, object truyền dữ liệu giữa các tầng, service xử lý nghiệp vụ, controller xử lý giao tiếp HTTP.

## 1.2 Features of Java - Đặc Tính Của Java

### Tóm tắt

Java có nhiều đặc tính giúp nó phù hợp với hệ thống production lớn: hướng đối tượng, đơn giản, bảo mật, độc lập nền tảng, robust, portable, architecture-neutral, dynamic, interpreted, high performance, multithreaded và distributed. Bộ slide cũng nhấn mạnh Java chạy thông qua JVM và các phiên bản LTS như Java 11, Java 17 thường được ưu tiên trong hệ thống doanh nghiệp vì có thời gian hỗ trợ dài hơn.

### Ý chính cần nhớ

- **Object-oriented:** Java tổ chức chương trình bằng class và object. Các khái niệm quan trọng gồm encapsulation, inheritance, polymorphism và abstraction.
- **Simple:** Java loại bỏ một số phần dễ gây lỗi trong C/C++ như con trỏ trực tiếp và quản lý bộ nhớ thủ công. Tuy vậy, viết Java tốt vẫn cần hiểu OOP, collection, exception, concurrency và JVM.
- **Secured:** Java có type safety, bytecode verification, classloader và không cho thao tác con trỏ trực tiếp như C/C++. Trong ứng dụng thật, security còn đến từ framework, validation, phân quyền, mã hóa, quản lý secret và cập nhật dependency.
- **Platform independent:** Code Java được compile từ `.java` sang bytecode `.class`, sau đó JVM trên từng hệ điều hành sẽ chạy bytecode đó. Ý tưởng nổi tiếng là “write once, run anywhere”.
- **Robust:** Java hỗ trợ strong typing, exception handling, garbage collection và compile-time checking, giúp giảm nhiều lỗi runtime nếu code được thiết kế cẩn thận.
- **Portable:** Chương trình Java dễ mang sang môi trường khác hơn vì kiểu dữ liệu primitive có kích thước được định nghĩa rõ, và bytecode chạy trên JVM.
- **Architecture-neutral:** Bytecode không phụ thuộc trực tiếp vào CPU cụ thể như Intel, AMD hay ARM. JVM chịu trách nhiệm chuyển bytecode thành lệnh phù hợp với máy đang chạy.
- **Dynamic:** Java có thể load class lúc runtime, dùng reflection, annotation, dependency injection. Các framework như Spring tận dụng mạnh đặc tính này.
- **Interpreted:** JVM có thể thông dịch bytecode, nhưng Java hiện đại không chỉ “chạy thông dịch”. JVM còn dùng JIT compiler để compile các đoạn code chạy nhiều thành native machine code nhằm tăng hiệu năng.
- **High performance:** Java thường đủ nhanh cho backend production nhờ JIT, GC tối ưu, thread pool, non-blocking I/O và hệ sinh thái thư viện tốt.
- **Multithreaded:** Java hỗ trợ lập trình đa luồng từ sớm qua `Thread`, `Runnable`, `ExecutorService`, `CompletableFuture`, concurrent collections và các primitive đồng bộ.
- **Distributed:** Java thường được dùng để xây dựng hệ thống phân tán như REST API, microservices, message queue consumers, batch jobs và service tích hợp với nhiều hệ thống khác.

### Java LTS trong production

Slide minh họa timeline Java 9 đến Java 17 và đánh dấu Java 11, Java 17 là Long-Term Support release. LTS là phiên bản được hỗ trợ lâu hơn, nên trong doanh nghiệp thường được ưu tiên hơn các bản non-LTS để giảm rủi ro nâng cấp liên tục.

Trong production, việc chọn version Java thường phụ thuộc vào:

- Chính sách công ty và cloud/runtime đang dùng.
- Framework có hỗ trợ version đó không, ví dụ Spring Boot version cụ thể yêu cầu Java version tối thiểu.
- Thời gian support bảo mật của bản JDK đang dùng.
- Khả năng nâng cấp dependency, build tool và CI/CD pipeline.

Ví dụ thực tế: nếu hệ thống đang chạy Spring Boot ổn định trên Java 17 LTS, team thường không nâng lên version mới chỉ vì “mới hơn”. Họ sẽ cân nhắc lợi ích hiệu năng, security patch, compatibility và chi phí regression test.

### Platform Independence và JVM

Luồng chạy cơ bản của Java:

```text
Source code (.java)
        |
        | javac
        v
Bytecode (.class)
        |
        | JVM trên Windows/Linux/macOS
        v
Machine code phù hợp với OS/CPU đang chạy
```

Ví dụ:

```java
public class Main {
    public static void main(String[] args) {
        System.out.println(1 + 2);
    }
}
```

Khi compile:

```bash
javac Main.java
java Main
```

`javac` tạo ra `Main.class`. File `.class` chứa bytecode, không phải machine code trực tiếp cho một CPU cụ thể. JVM sẽ đọc bytecode đó và thực thi trên máy hiện tại.

Trong production, ứng dụng Java thường được package thành `.jar`:

```bash
java -jar order-service.jar
```

Cùng một file `.jar` có thể chạy ở local Windows và server Linux nếu cùng version Java tương thích. Khi deploy bằng Docker, team thường cố định runtime để tránh lệch môi trường:

```dockerfile
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY target/order-service.jar app.jar
CMD ["java", "-jar", "app.jar"]
```

### Object-Oriented qua ví dụ Vehicle

Slide dùng sơ đồ `Vehicle`, `Wheeled Vehicle`, car, bicycle, boat để minh họa kế thừa. Ý tưởng là class cha giữ đặc điểm chung, class con mở rộng hoặc chuyên biệt hóa hành vi.

Ví dụ đơn giản:

```java
abstract class Vehicle {
    private final String registrationNumber;

    protected Vehicle(String registrationNumber) {
        this.registrationNumber = registrationNumber;
    }

    public String getRegistrationNumber() {
        return registrationNumber;
    }

    public abstract void move();
}

abstract class WheeledVehicle extends Vehicle {
    private final int numberOfWheels;

    protected WheeledVehicle(String registrationNumber, int numberOfWheels) {
        super(registrationNumber);
        this.numberOfWheels = numberOfWheels;
    }

    public int getNumberOfWheels() {
        return numberOfWheels;
    }
}

class Car extends WheeledVehicle {
    Car(String registrationNumber) {
        super(registrationNumber, 4);
    }

    @Override
    public void move() {
        System.out.println("Car is driving on the road");
    }
}

class Bicycle extends WheeledVehicle {
    Bicycle(String registrationNumber) {
        super(registrationNumber, 2);
    }

    @Override
    public void move() {
        System.out.println("Bicycle is moving by pedaling");
    }
}
```

Trong production, OOP thường không chỉ là vẽ cây kế thừa. Một ví dụ gần thực tế hơn là xử lý nhiều phương thức thanh toán:

```java
public interface PaymentProcessor {
    PaymentResult charge(PaymentRequest request);
}

@Service
public class CreditCardPaymentProcessor implements PaymentProcessor {
    @Override
    public PaymentResult charge(PaymentRequest request) {
        // Gọi cổng thanh toán thẻ, validate response, map lỗi nghiệp vụ.
        return PaymentResult.success(request.orderId());
    }
}

@Service
public class BankTransferPaymentProcessor implements PaymentProcessor {
    @Override
    public PaymentResult charge(PaymentRequest request) {
        // Tạo mã chuyển khoản hoặc kiểm tra trạng thái giao dịch ngân hàng.
        return PaymentResult.pending(request.orderId());
    }
}
```

Điểm quan trọng ở đây là code nghiệp vụ có thể phụ thuộc vào abstraction `PaymentProcessor`, còn từng cách thanh toán triển khai chi tiết riêng. Đây là polymorphism trong code thật.

### Security trong Java production

Java cung cấp nền tảng an toàn hơn ở mức runtime, nhưng ứng dụng production vẫn cần thiết kế security rõ ràng. Ví dụ trong Spring Boot:

```java
@RestController
@RequestMapping("/api/admin/users")
public class AdminUserController {
    private final UserService userService;

    public AdminUserController(UserService userService) {
        this.userService = userService;
    }

    @PreAuthorize("hasAuthority('USER_WRITE')")
    @PostMapping
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody CreateUserRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(userService.createUser(request));
    }
}
```

Trong ví dụ này:

- `@PreAuthorize` kiểm tra quyền trước khi cho tạo user.
- `@Valid` kích hoạt validation cho request body.
- Controller không tự xử lý password, token hay phân quyền phức tạp; các phần đó nên nằm ở service/security layer phù hợp.

Các lỗi security vẫn có thể xảy ra nếu:

- Ghép SQL bằng string thay vì dùng prepared statement hoặc ORM đúng cách.
- Không kiểm tra quyền theo từng resource, ví dụ user A xem được đơn hàng của user B.
- Log thông tin nhạy cảm như password, access token, refresh token, số thẻ.
- Dùng dependency có CVE nhưng không cập nhật.
- Tin tưởng dữ liệu từ client mà không validate.

### Lưu ý chương 1

- Java chạy đa nền tảng nhưng ứng dụng vẫn phụ thuộc vào JDK, timezone, charset, file path, permission, native library và cấu hình môi trường.
- Các cơ chế an toàn của Java không thay thế validation, phân quyền, quản lý secret, cập nhật dependency và kiểm tra lỗ hổng bảo mật.
- Trong thiết kế OOP, ưu tiên abstraction, interface và composition khi chúng làm mô hình đơn giản hơn; tránh cây kế thừa quá sâu.
- Hiệu năng cần được đánh giá bằng profiling, metric và benchmark, không nên tối ưu theo cảm giác.
- Multithreading có thể tạo race condition, deadlock và thread leak; shared mutable state phải được kiểm soát cẩn thận.
- Production thường ưu tiên phiên bản LTS tương thích với framework và còn nhận được bản vá bảo mật.
- Khi dùng thư viện mã nguồn mở, cần kiểm tra license, version, CVE và chính sách nâng cấp.

## 2. JDK, JRE and JVM

### Tóm tắt

Ba khái niệm này liên quan chặt chẽ nhưng dùng cho các mục đích khác nhau:

- **JVM (Java Virtual Machine):** máy ảo chạy bytecode Java.
- **JRE (Java Runtime Environment):** môi trường để chạy ứng dụng Java đã được biên dịch.
- **JDK (Java Development Kit):** bộ công cụ để phát triển, compile, test, debug và chạy ứng dụng Java.

Nói ngắn gọn: **JDK dùng để code và build**, **JRE dùng để chạy**, **JVM là thành phần thực thi bytecode**.

### Ý chính cần nhớ

- **JVM là abstract machine:** JVM không phải một máy vật lý, mà là một “máy ảo” định nghĩa cách bytecode Java được load, verify, execute và quản lý bộ nhớ.
- **JVM cung cấp runtime environment:** Khi chạy `java Main` hoặc `java -jar app.jar`, JVM chịu trách nhiệm class loading, bytecode verification, execution, garbage collection, thread management và runtime optimizations như JIT.
- **JRE = JVM + thư viện cần để chạy app:** JRE chứa JVM và các thư viện/runtime files cần thiết để chạy chương trình Java đã compile.
- **JDK = JRE + công cụ phát triển:** JDK bao gồm runtime và các tool như `javac`, `java`, `jar`, `javadoc`, `jshell`, `jdb`, `jcmd`, `jstack`, `jmap`.
- **Muốn develop Java thì cần JDK:** Vì cần `javac` để compile source code `.java` thành bytecode `.class`.
- **Muốn chỉ chạy app thì runtime là đủ:** Server production thường không cần toàn bộ tool development nếu app đã được build sẵn.

### Sơ đồ quan hệ

```text
JDK
├── Development tools
│   ├── javac
│   ├── jar
│   ├── javadoc
│   ├── jshell
│   └── debug/diagnostic tools
│
└── JRE
    ├── JVM
    └── Required libraries/runtime files
```

Một cách nhớ nhanh:

```text
JDK = JRE + tools để develop
JRE = JVM + libraries để run
JVM = engine chạy bytecode
```

### Ví dụ local development

Khi lập trình Java ở máy cá nhân, bạn thường cần JDK:

```java
public class HelloJava {
    public static void main(String[] args) {
        System.out.println("Hello Java");
    }
}
```

Compile và chạy:

```bash
javac HelloJava.java
java HelloJava
```

Ở đây:

- `javac` thuộc JDK, dùng để compile `HelloJava.java` thành `HelloJava.class`.
- `java` khởi động JVM để chạy bytecode trong file `.class`.
- Nếu chỉ có runtime mà không có compiler, bạn không thể dùng `javac`.

### Ví dụ production với Maven và Docker

Trong hệ thống production, quá trình build và run thường tách thành hai giai đoạn:

```dockerfile
FROM eclipse-temurin:17-jdk AS build
WORKDIR /src
COPY . .
RUN ./mvnw clean package -DskipTests

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /src/target/order-service.jar app.jar
CMD ["java", "-jar", "app.jar"]
```

Ý nghĩa:

- Stage `build` dùng **JDK** vì cần compile source code, chạy Maven/Gradle, tạo file `.jar`.
- Stage runtime dùng **JRE** vì chỉ cần chạy file `.jar` đã build xong.
- Image runtime nhỏ hơn, ít tool hơn, giảm bề mặt tấn công và thường deploy nhanh hơn.

Trong nhiều dự án hiện đại, bạn cũng có thể thấy image runtime ghi là `jre`, `jdk`, hoặc dùng custom runtime tạo bằng `jlink`. Dù cách đóng gói thay đổi theo version Java và vendor JDK, nguyên tắc vẫn vậy: **build cần tool development, run cần runtime phù hợp**.

### Ví dụ production trong CI/CD

Một pipeline Java điển hình:

```text
Developer commit code
        |
        v
CI dùng JDK để compile, test, package
        |
        v
Tạo artifact: order-service.jar
        |
        v
Deploy lên server/container có Java runtime
        |
        v
JVM chạy app.jar trong production
```

Ví dụ lệnh trong CI:

```bash
./mvnw clean verify
./mvnw package
java -jar target/order-service.jar
```

Trong đó:

- `clean verify` cần JDK vì test và compile source code.
- `package` tạo artifact `.jar`.
- `java -jar` chạy artifact bằng JVM.

### JDK, JRE, JVM trong lỗi thực tế

Một số lỗi production/local hay gặp liên quan trực tiếp đến phần này:

- **Sai `JAVA_HOME`:** IDE hoặc build tool trỏ nhầm Java version, ví dụ project cần Java 17 nhưng máy đang dùng Java 11.
- **Compile bằng version cao, chạy bằng version thấp:** Build bằng Java 17 nhưng server chạy Java 11 có thể gặp lỗi kiểu `UnsupportedClassVersionError`.
- **Thiếu compiler:** Docker image chỉ có runtime nhưng pipeline lại cố chạy Maven compile bên trong container runtime.
- **Khác vendor/runtime:** Local dùng một bản JDK, production dùng bản khác có cấu hình GC, timezone, certificate store hoặc crypto policy khác.
- **Thiếu certificate:** JVM không trust certificate của service bên ngoài, gây lỗi SSL khi gọi API.

Ví dụ lỗi thường gặp:

```text
java.lang.UnsupportedClassVersionError:
class file has wrong version 61.0, should be 55.0
```

Diễn giải:

- `61.0` tương ứng Java 17.
- `55.0` tương ứng Java 11.
- Nghĩa là code được compile bằng Java 17 nhưng đang chạy trên Java 11.

### Lưu ý chương 2

- Máy phát triển nên cài JDK vì cần compiler, test, debugger và build tool; môi trường chỉ chạy ứng dụng có thể dùng runtime image nhỏ hơn.
- Cố định Java version trong `pom.xml`/`build.gradle`, Dockerfile, CI và tài liệu setup để tránh lệch môi trường.
- `java -version` kiểm tra runtime, còn `javac -version` kiểm tra compiler.
- `UnsupportedClassVersionError` thường có nghĩa code được build bằng Java mới hơn runtime đang chạy.
- Từ Java 9, bản JRE cài riêng ít phổ biến hơn; tuy vậy vẫn cần hiểu JRE là phần môi trường runtime trong mô hình khái niệm.

## 3. Install

### Tóm tắt

Phần này nói về việc cài môi trường phát triển Java: JDK, IDE, database MySQL, Apache Tomcat và công cụ hỗ trợ như Eclipse.

### IDEs of Java

IDE là **Integrated Development Environment**, giúp lập trình viên viết code nhanh và ít lỗi hơn.

Các tính năng thường dùng:

- Gợi ý code/autocomplete.
- Báo lỗi compile ngay trong editor.
- Auto compile hoặc build project.
- Debug từng dòng code.
- Hỗ trợ GUI builder trong một số IDE.

IDE phổ biến:

- **IntelliJ IDEA:** rất phổ biến trong dự án Java/Spring Boot hiện đại.
- **Eclipse:** dùng nhiều trong môi trường enterprise hoặc dự án cũ.
- **NetBeans:** có hỗ trợ Java tốt, đặc biệt với GUI/Swing.
- **DrJava:** nhẹ, phù hợp học cơ bản, ít gặp trong production.

### Checklist cài đặt

- **JDK:** cài version phù hợp với dự án, thường ưu tiên bản LTS như Java 17 hoặc Java 21.
- **IDE:** chọn IntelliJ IDEA hoặc Eclipse tùy team/project.
- **MySQL:** cài MySQL Server/Client hoặc dùng Docker; MySQL Workbench là công cụ GUI để xem database.
- **Apache Tomcat:** cần nếu deploy ứng dụng Servlet/JSP hoặc file `.war`. Với Spring Boot hiện đại, Tomcat thường được embedded sẵn nên không cần cài riêng.
- **Eclipse:** nếu công ty yêu cầu dùng Eclipse thì cài theo hướng dẫn nội bộ.

### Lệnh kiểm tra sau khi cài

```bash
java -version
javac -version
```

Nếu dùng MySQL:

```bash
mysql --version
```

Lệnh trên slide:

```bash
sudo apt-get install mysql-server mysql-client libmysqlclient-dev
```

Lưu ý: đây là lệnh cho Ubuntu/Debian Linux. Trên Windows thường cài bằng installer, package manager như Chocolatey/Scoop, hoặc dùng Docker.

### Ví dụ production ngắn

Trong team thực tế, môi trường thường được chuẩn hóa bằng Docker hoặc file setup nội bộ để tránh mỗi máy dev một kiểu. Ví dụ database có thể chạy bằng Docker:

```bash
docker run --name mysql-dev -e MYSQL_ROOT_PASSWORD=secret -p 3306:3306 -d mysql:8
```

Điểm cần nhớ: **code Java cần JDK để build, IDE để làm việc hiệu quả, database/app server tùy loại dự án đang học hoặc đang làm**.

### Lưu ý chương 3

- Cài đúng JDK version mà dự án yêu cầu và kiểm tra cả `java` lẫn `javac` sau khi cài.
- Tomcat cài riêng chỉ cần cho một số ứng dụng Servlet/JSP hoặc file `.war`; Spring Boot thường dùng embedded server.
- Lệnh cài đặt phụ thuộc hệ điều hành. Với database, Docker giúp môi trường giữa các thành viên nhất quán hơn.
- IDE là công cụ hỗ trợ; Maven/Gradle và JDK mới là phần quyết định project build được hay không.

## 4. Class and Objects

### Tóm tắt

Trong Java, **class** là bản thiết kế, còn **object** là một thực thể cụ thể được tạo ra từ class đó. Class định nghĩa object có những **attributes** nào và có thể thực hiện những **behaviors** nào.

Ví dụ trên slide:

- `Vehicle` là class.
- `name`, `color` là attributes.
- `speed()` là behavior/method.
- Motorbike màu đen, bicycle màu hồng, horse màu nâu, car màu vàng là các object cụ thể.

### Ý chính cần nhớ

- **Class:** mô tả cấu trúc và hành vi chung của một nhóm object.
- **Object:** instance cụ thể của class, có dữ liệu riêng tại runtime.
- **Attribute/field:** dữ liệu thuộc về object, ví dụ `name`, `color`, `speedLimit`.
- **Behavior/method:** hành động object có thể thực hiện, ví dụ `start()`, `stop()`, `calculateShippingFee()`.
- **Constructor:** hàm đặc biệt dùng để khởi tạo object.
- **State:** trạng thái hiện tại của object, được biểu diễn bằng field.
- **Reference:** trong Java, biến object thường không chứa toàn bộ object, mà chứa reference trỏ đến object trong heap memory.

### Class và Object khác nhau thế nào?

```text
Class  = bản thiết kế chung
Object = thực thể cụ thể được tạo từ bản thiết kế đó
```

Ví dụ đời thường:

- `Vehicle` là class.
- `new Vehicle("Car", "Yellow", 120)` là một object cụ thể.
- `new Vehicle("Bicycle", "Pink", 10)` là object khác, có state khác.

Ví dụ Java:

```java
public class Vehicle {
    private final String name;
    private final String color;
    private final int speedLimit;

    public Vehicle(String name, String color, int speedLimit) {
        this.name = name;
        this.color = color;
        this.speedLimit = speedLimit;
    }

    public void printInfo() {
        System.out.println(name + " - " + color + " - " + speedLimit + "km/h");
    }

    public boolean canRunFasterThan(int speed) {
        return speedLimit > speed;
    }
}
```

Tạo object từ class:

```java
public class Main {
    public static void main(String[] args) {
        Vehicle motorbike = new Vehicle("Motorbike", "Black", 60);
        Vehicle bicycle = new Vehicle("Bicycle", "Pink", 10);
        Vehicle car = new Vehicle("Car", "Yellow", 120);

        motorbike.printInfo();
        bicycle.printInfo();
        car.printInfo();
    }
}
```

Ở đây:

- `Vehicle` là class.
- `motorbike`, `bicycle`, `car` là các biến reference.
- `new Vehicle(...)` tạo object thật trong memory.
- Mỗi object có `name`, `color`, `speedLimit` riêng.

### 4.1 Relationship between a class and its object

Slide minh họa `Vehicle` là class chung, còn `Vehicle 1`, `Vehicle 2` là các object cụ thể được tạo từ class đó.

```text
Class Vehicle
├── field: name  -> kiểu String
├── field: color -> kiểu String
└── method: speed() -> void

Object Vehicle 1
├── name: car
├── color: yellow
└── speed(): 120km/h

Object Vehicle 2
├── name: horse
├── color: brown
└── speed(): 80km/h
```

Điểm cần nhớ:

- Class định nghĩa **kiểu dữ liệu và hành vi**.
- Object chứa **giá trị cụ thể** tại runtime.
- Một class có thể tạo ra nhiều object.
- Các object được tạo từ cùng một class có cùng cấu trúc, nhưng state có thể khác nhau.

Ví dụ Java:

```java
public class Vehicle {
    private final String name;
    private final String color;
    private final int speedLimitKmh;

    public Vehicle(String name, String color, int speedLimitKmh) {
        this.name = name;
        this.color = color;
        this.speedLimitKmh = speedLimitKmh;
    }

    public void printSpeedLimit() {
        System.out.println(name + " speed limit: " + speedLimitKmh + "km/h");
    }
}
```

```java
Vehicle vehicle1 = new Vehicle("car", "yellow", 120);
Vehicle vehicle2 = new Vehicle("horse", "brown", 80);

vehicle1.printSpeedLimit();
vehicle2.printSpeedLimit();
```

Ở đây `vehicle1` và `vehicle2` là hai object khác nhau. Việc thay đổi object này không nên làm thay đổi object kia, trừ khi cả hai biến cùng trỏ đến một object như phần reference đã nói.

Một điểm quan trọng trong production:

```java
public class Vehicle {
    private String name;        // instance field: mỗi object có giá trị riêng
    private static int counter; // static field: thuộc về class, dùng chung
}
```

Không nên dùng `static` cho dữ liệu nghiệp vụ của từng user, từng order, từng request. Nếu lỡ để state dùng chung trong `static`, nhiều request khác nhau có thể ảnh hưởng lẫn nhau.

### 4.2 Class - overview

Class là template để tạo object. Một class thường gồm:

- **Fields:** định nghĩa state của object.
- **Methods:** định nghĩa behavior của object.
- **Constructors:** định nghĩa cách tạo object hợp lệ.
- **Access modifiers:** kiểm soát phạm vi truy cập, ví dụ `public`, `private`, `protected`.
- **Inheritance/interface:** dùng `extends` và `implements` khi cần tái sử dụng hoặc tuân theo abstraction.

Cú pháp tổng quát trên slide:

```java
<AccessModifier> class <ClassName>
        [extends <SuperClassName>]
        [implements <InterfaceName>] {
    // fields
    // constructors
    // methods
}
```

Ví dụ:

```java
public class Car extends Vehicle implements Movable {
    // ...
}
```

Ý nghĩa:

- `public`: class có thể được truy cập từ package khác.
- `class`: keyword để khai báo class.
- `Car`: tên class.
- `extends Vehicle`: `Car` kế thừa từ `Vehicle`.
- `implements Movable`: `Car` cam kết triển khai các method của interface `Movable`.

Lưu ý cú pháp:

- Java phân biệt hoa/thường: `String` đúng, `string` sai.
- Tên class nên viết PascalCase: `Vehicle`, `Car`, `OrderService`.
- Tên biến/method nên viết camelCase: `speedLimitKmh`, `printSpeedLimit()`.
- Một class chỉ `extends` được một class cha.
- Một class có thể `implements` nhiều interface.
- Nếu có cả `extends` và `implements`, `extends` đứng trước `implements`.

Ví dụ nhiều interface:

```java
public class Car extends Vehicle implements Movable, Insurable {
    // ...
}
```

### 4.3 Class - example

Slide đưa ví dụ class `Vehicle` gồm `name`, `color` và method `speed(float value)`.

Viết sát với slide:

```java
public class Vehicle {
    String name;
    String color;

    void speed(float value) {
        System.out.println("Speed: " + value + "km/h");
    }
}
```

Tuy nhiên trong code Java thực tế nên viết chặt hơn:

```java
public class Vehicle {
    private final String name;
    private final String color;
    private final float speedLimitKmh;

    public Vehicle(String name, String color, float speedLimitKmh) {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Vehicle name is required");
        }
        if (speedLimitKmh <= 0) {
            throw new IllegalArgumentException("Speed limit must be positive");
        }
        this.name = name;
        this.color = color;
        this.speedLimitKmh = speedLimitKmh;
    }

    public boolean canMoveAt(float speedKmh) {
        return speedKmh <= speedLimitKmh;
    }

    public String describe() {
        return name + " (" + color + "), speed limit " + speedLimitKmh + "km/h";
    }
}
```

Sử dụng:

```java
Vehicle car = new Vehicle("Car", "Yellow", 120);

System.out.println(car.describe());
System.out.println(car.canMoveAt(100)); // true
System.out.println(car.canMoveAt(150)); // false
```

Vì sao bản production-style tốt hơn?

- Field để `private` để bảo vệ state.
- Dùng `final` nếu field không nên thay đổi sau khi tạo object.
- Constructor validate dữ liệu đầu vào.
- Method `canMoveAt()` trả về ý nghĩa nghiệp vụ rõ ràng hơn `speed()`.
- Tên field `speedLimitKmh` rõ đơn vị hơn `speed`.

Ví dụ production gần backend hơn:

```java
public class DeliveryVehicle {
    private final String id;
    private final String plateNumber;
    private final int maxLoadKg;
    private boolean active;

    public DeliveryVehicle(String id, String plateNumber, int maxLoadKg) {
        if (maxLoadKg <= 0) {
            throw new IllegalArgumentException("Max load must be positive");
        }
        this.id = id;
        this.plateNumber = plateNumber;
        this.maxLoadKg = maxLoadKg;
        this.active = true;
    }

    public boolean canCarry(int packageWeightKg) {
        return active && packageWeightKg > 0 && packageWeightKg <= maxLoadKg;
    }

    public void deactivate() {
        this.active = false;
    }
}
```

Trong hệ thống logistics, object `DeliveryVehicle` có thể được dùng để quyết định xe nào đủ điều kiện nhận một đơn giao hàng. Đây là class/object gắn trực tiếp với business rule, không chỉ là nơi chứa dữ liệu.

### 4.4 Class - Internal structure

Một class Java có thể chứa nhiều thành phần bên trong:

- Package/import ở đầu file.
- Class declaration: access modifier, `class`, tên class, `extends`, `implements`.
- Field declarations: biến thuộc class hoặc object.
- Static initializer block.
- Instance initializer block, slide gọi là anonymous block.
- Constructor declarations.
- Method declarations.
- Inner class declarations.
- Nested interface declarations.

Cấu trúc tổng quát:

```java
public class Car extends Vehicle implements Movable {
    private static int totalCreated; // static field

    private final String plateNumber; // instance field

    static {
        // static initializer block
    }

    {
        // instance initializer block
    }

    public Car(String plateNumber) {
        this.plateNumber = plateNumber;
    }

    @Override
    public void move() {
        // method
    }
}
```

#### Static initializer block

Static initializer block chạy **một lần duy nhất** khi class được JVM initialize, thường là trước khi dùng class lần đầu.

Ví dụ:

```java
public class Demo {
    static double percentage;
    static int rank;

    static {
        percentage = 44.6;
        rank = 12;
        System.out.println("STATIC BLOCK");
    }

    public static void main(String[] args) {
        Demo demo = new Demo();
        System.out.println("MAIN METHOD");
        System.out.println("RANK: " + rank);
    }
}
```

Output chính:

```text
STATIC BLOCK
MAIN METHOD
RANK: 12
```

Ý nghĩa:

- `static` block chạy trước `main()` khi class `Demo` được initialize.
- Dữ liệu `static` thuộc về class, không thuộc về từng object.
- Dù tạo nhiều object `new Demo()`, static block vẫn chỉ chạy một lần cho classloader tương ứng.

Ví dụ production:

```java
public final class CurrencyCodes {
    public static final Set<String> SUPPORTED;

    static {
        SUPPORTED = Set.of("VND", "USD", "EUR", "JPY");
    }

    private CurrencyCodes() {
    }
}
```

Trong code hiện đại, nếu chỉ khởi tạo hằng số đơn giản thì thường viết trực tiếp:

```java
public static final Set<String> SUPPORTED = Set.of("VND", "USD", "EUR", "JPY");
```

Không nên đặt logic nặng trong static block như gọi database, gọi API, đọc file lớn hoặc khởi tạo dependency phức tạp. Trong production, các việc đó nên để framework/configuration quản lý để dễ test, dễ observe và dễ retry khi lỗi.

#### Instance initializer block

Slide gọi là `anonymous block`, nhưng thuật ngữ thường dùng trong Java là **instance initializer block**. Block này chạy mỗi lần tạo object, và chạy **trước constructor body**.

Ví dụ:

```java
public class Demo {
    {
        System.out.print("Object is created by the ");
    }

    public Demo() {
        System.out.println("default constructor");
    }

    public Demo(int n) {
        System.out.println("parameterized constructor");
    }
}
```

Khi chạy:

```java
Demo demo1 = new Demo();
Demo demo2 = new Demo(1);
```

Output:

```text
Object is created by the default constructor
Object is created by the parameterized constructor
```

Thứ tự khởi tạo cơ bản khi tạo object:

```text
1. Static field/static block của class, nếu class chưa được initialize
2. Instance field initializer
3. Instance initializer block
4. Constructor
```

Lưu ý thực tế:

- Instance initializer block ít dùng trong production Java thông thường.
- Nếu logic chỉ phục vụ khởi tạo object, constructor thường rõ ràng hơn.
- Nếu nhiều constructor có chung logic, có thể dùng private method hoặc constructor chaining thay vì instance initializer block.

Ví dụ nên dùng constructor chaining:

```java
public class Customer {
    private final String name;
    private final boolean active;

    public Customer(String name) {
        this(name, true);
    }

    public Customer(String name, boolean active) {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Name is required");
        }
        this.name = name;
        this.active = active;
    }
}
```

### 4.5 Access modifier

Access modifier kiểm soát nơi nào có thể truy cập class, field, constructor hoặc method.

| Modifier                | Trong cùng class | Cùng package | Subclass khác package | Ngoài package |
| ----------------------- | ----------------: | ------------: | ---------------------: | -------------: |
| `private`             |               Có |        Không |                 Không |         Không |
| default/package-private |               Có |           Có |                 Không |         Không |
| `protected`           |               Có |           Có |                    Có |         Không |
| `public`              |               Có |           Có |                    Có |            Có |

Trong Java, nếu không ghi modifier thì đó là **default access** hoặc **package-private**.

Ví dụ:

```java
public class User {
    private String passwordHash;
    String internalNote;
    protected String createdBy;
    public String username;
}
```

Ý nghĩa:

- `private passwordHash`: chỉ class `User` tự truy cập được.
- `internalNote`: chỉ các class cùng package truy cập được.
- `protected createdBy`: class cùng package hoặc subclass có thể truy cập.
- `public username`: mọi nơi truy cập được.

Lưu ý quan trọng:

- Top-level class chỉ có thể là `public` hoặc package-private. Không khai báo top-level class là `private` hoặc `protected`.
- `private` là mặc định tốt cho field.
- `public` nên dùng cho API thật sự cần lộ ra ngoài.
- `protected` không có nghĩa là “chỉ subclass ở mọi nơi truy cập thoải mái”; với subclass khác package, cách truy cập có thêm quy tắc liên quan đến inheritance.

Ví dụ production:

```java
public class Order {
    private OrderStatus status;

    public OrderStatus getStatus() {
        return status;
    }

    public void markPaid() {
        if (status != OrderStatus.CREATED) {
            throw new IllegalStateException("Only created order can be paid");
        }
        status = OrderStatus.PAID;
    }
}
```

Ở đây `status` để `private`, không cho code bên ngoài set trực tiếp:

```java
order.status = OrderStatus.PAID; // Không nên và sẽ không compile nếu status private
```

Thay vào đó, code bên ngoài phải gọi `markPaid()`, nơi business rule được kiểm tra. Đây là encapsulation trong code thật.

### 4.6 Objects

Object là **instance của class**. Object được tạo bằng keyword `new` và constructor.

Cú pháp:

```java
<ClassName> <objectName> = new <ConstructorName>(arguments);
```

Trong Java, constructor name phải trùng với class name:

```java
Vehicle object1 = new Vehicle();
Vehicle object2 = new Vehicle("Car", "yellow");
```

Ví dụ đầy đủ:

```java
public class Vehicle {
    private String name;
    private String color;

    public Vehicle() {
        this.name = "Unknown";
        this.color = "Unknown";
    }

    public Vehicle(String name, String color) {
        this.name = name;
        this.color = color;
    }

    public String describe() {
        return name + " - " + color;
    }
}
```

```java
Vehicle object1 = new Vehicle();
Vehicle object2 = new Vehicle("Car", "yellow");

System.out.println(object1.describe()); // Unknown - Unknown
System.out.println(object2.describe()); // Car - yellow
```

Điểm cần nhớ:

- `Vehicle object2`: khai báo biến reference kiểu `Vehicle`.
- `new Vehicle(...)`: tạo object trong heap.
- `Vehicle(...)`: gọi constructor.
- `object2` không chứa toàn bộ object, mà giữ reference đến object.
- Nếu không còn reference nào trỏ đến object, object có thể được garbage collector thu hồi.

Ví dụ production:

```java
CreateOrderRequest request = new CreateOrderRequest(customerId, items);
Order order = orderFactory.createFrom(request);
paymentService.confirmPayment(order.getId());
```

Trong code production, object thường không chỉ được tạo bằng `new` trực tiếp ở mọi nơi. Với framework như Spring:

- Object nghiệp vụ như `Order`, `Payment`, `Customer` thường được tạo trong service/factory.
- Object dependency như `PaymentService`, `OrderRepository` thường được Spring container tạo và inject.
- DTO object có thể được framework tạo từ JSON request.

Ví dụ Spring tạo object từ JSON:

```java
public record CreateVehicleRequest(String name, String color) {
}

@PostMapping("/vehicles")
public VehicleResponse createVehicle(@RequestBody CreateVehicleRequest request) {
    return vehicleService.create(request);
}
```

Client gửi JSON, framework map thành object `CreateVehicleRequest`. Đây cũng là object, dù bạn không trực tiếp viết `new CreateVehicleRequest(...)` trong controller.

### Liên hệ với OOP

Slide nhắc đến các phần chính của OOP:

- **Class:** khuôn mẫu để tạo object.
- **Object:** thực thể cụ thể trong chương trình.
- **Encapsulation:** đóng gói dữ liệu và hành vi liên quan vào cùng một class; che giấu field bằng `private`, mở thao tác cần thiết qua method.
- **Abstraction:** chỉ lộ ra phần cần dùng, che bớt chi tiết bên trong.
- **Inheritance:** class con tái sử dụng/mở rộng class cha.
- **Polymorphism:** cùng một interface/method nhưng nhiều cách triển khai khác nhau.

Ví dụ ngắn về encapsulation:

```java
public class BankAccount {
    private long balance;

    public BankAccount(long openingBalance) {
        if (openingBalance < 0) {
            throw new IllegalArgumentException("Opening balance must not be negative");
        }
        this.balance = openingBalance;
    }

    public void deposit(long amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        balance += amount;
    }

    public long getBalance() {
        return balance;
    }
}
```

Không để `balance` là `public`, vì nếu code bên ngoài sửa trực tiếp thì object có thể rơi vào trạng thái sai, ví dụ số dư âm không hợp lệ.

### Ví dụ production

Trong backend thực tế, class và object xuất hiện ở rất nhiều tầng: request DTO, response DTO, entity, domain model, service, repository.

Ví dụ class đại diện cho đơn hàng:

```java
public class Order {
    private final String id;
    private final String customerId;
    private OrderStatus status;
    private long totalAmount;

    public Order(String id, String customerId, long totalAmount) {
        if (totalAmount <= 0) {
            throw new IllegalArgumentException("Total amount must be positive");
        }
        this.id = id;
        this.customerId = customerId;
        this.totalAmount = totalAmount;
        this.status = OrderStatus.CREATED;
    }

    public void markPaid() {
        if (status != OrderStatus.CREATED) {
            throw new IllegalStateException("Only created order can be paid");
        }
        this.status = OrderStatus.PAID;
    }

    public boolean belongsTo(String customerId) {
        return this.customerId.equals(customerId);
    }

    public OrderStatus getStatus() {
        return status;
    }
}
```

```java
public enum OrderStatus {
    CREATED,
    PAID,
    CANCELLED
}
```

Trong ví dụ này:

- `Order` là class/domain object.
- `id`, `customerId`, `status`, `totalAmount` là state.
- `markPaid()` là behavior chứa business rule.
- Object tự bảo vệ trạng thái của nó, thay vì để code bên ngoài set status tùy tiện.

Code service sử dụng object:

```java
@Service
public class PaymentService {
    private final OrderRepository orderRepository;

    public PaymentService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public void confirmPayment(String orderId, String customerId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new OrderNotFoundException(orderId));

        if (!order.belongsTo(customerId)) {
            throw new AccessDeniedException("Cannot pay another customer's order");
        }

        order.markPaid();
        orderRepository.save(order);
    }
}
```

Đây là cách class/object giúp production code rõ hơn: business rule nằm gần dữ liệu liên quan, tránh việc service phải set field lung tung và khó kiểm soát trạng thái.

### Object reference trong Java

Một điểm quan trọng: biến object trong Java là reference.

```java
Vehicle car1 = new Vehicle("Car", "Yellow", 120);
Vehicle car2 = car1;
```

`car1` và `car2` cùng trỏ đến một object. Nếu object mutable và một biến thay đổi state, biến còn lại cũng nhìn thấy thay đổi đó.

Ví dụ:

```java
public class UserProfile {
    private String displayName;

    public UserProfile(String displayName) {
        this.displayName = displayName;
    }

    public void changeDisplayName(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }
}
```

```java
UserProfile profile1 = new UserProfile("An");
UserProfile profile2 = profile1;

profile2.changeDisplayName("Bình");

System.out.println(profile1.getDisplayName()); // Bình
```

Điều này rất quan trọng khi làm việc với object mutable, cache, session, collection hoặc shared state giữa nhiều thread.

### Lưu ý chương 4

- Class là định nghĩa, object là instance tồn tại khi chương trình chạy; biến object giữ reference chứ không chứa trực tiếp toàn bộ object.
- Field nên để `private`, còn việc thay đổi state nên đi qua method có kiểm tra business rule.
- Constructor nên tạo ra object hợp lệ ngay từ đầu, tránh phụ thuộc vào việc code khác sẽ bổ sung field bắt buộc sau đó.
- `static` block chạy khi class được khởi tạo; instance initializer chạy trước constructor mỗi lần tạo object. Trong code thông thường, ưu tiên constructor cho logic khởi tạo.
- Không lưu state theo request, user hoặc order trong `static` field. Shared mutable state đặc biệt nguy hiểm khi có nhiều thread.
- Object do framework tạo từ JSON hoặc database vẫn cần validation; framework không tự đảm bảo dữ liệu đúng nghiệp vụ.
- Access modifier chỉ nên mở ở mức cần thiết vì public API càng rộng thì càng khó thay đổi.
- Cẩn thận với object mutable: nhiều biến có thể cùng trỏ đến một object và cùng nhìn thấy thay đổi.
- Tên class và quan hệ kế thừa phải phản ánh đúng domain; không nên tạo mô hình chỉ vì các đối tượng có vài thuộc tính giống nhau.

## 5. Variables

### Tóm tắt

Variable là tên dùng để lưu trữ dữ liệu trong chương trình. Trong Java, variable luôn có **type** rõ ràng, ví dụ `int`, `String`, `boolean`, `Customer`. Dựa theo vị trí khai báo và vòng đời, có thể gặp ba nhóm hay dùng: **instance variable**, **static variable** và **local variable**.

### Cú pháp khai báo

Cú pháp tổng quát trên slide:

```java
[access_modifier] [static] [final] type fieldName [= initialValue];
```

Ví dụ:

```java
class Example {
    int data = 50;        // instance variable
    static int m = 100;   // static variable

    void method() {
        int n = 90;       // local variable
    }
}
```

### Các loại variable quan trọng

- **Instance variable:** thuộc về từng object. Mỗi object có bản dữ liệu riêng.
- **Static variable:** thuộc về class, được dùng chung giữa các object.
- **Local variable:** khai báo trong method/block/constructor, chỉ sống trong phạm vi block đó.
- **Parameter:** biến nhận dữ liệu truyền vào method hoặc constructor.

Ví dụ:

```java
public class Customer {
    private String email;              // instance variable
    private static int totalCreated;   // static variable

    public Customer(String email) {    // email là parameter
        this.email = email;
        totalCreated++;
    }

    public boolean hasEmail() {
        boolean valid = email != null && !email.isBlank(); // local variable
        return valid;
    }
}
```

### Instance variable

Instance variable nằm trong class nhưng ngoài method/constructor/block. Nó mô tả state của từng object.

```java
public class BankAccount {
    private String accountNumber;
    private long balance;
}
```

Mỗi object `BankAccount` có `accountNumber` và `balance` riêng.

```java
BankAccount accountA = new BankAccount();
BankAccount accountB = new BankAccount();
```

`accountA` và `accountB` là hai object khác nhau, nên balance của object này không tự động ảnh hưởng balance của object kia.

### Static variable

Static variable thuộc về class, không thuộc về từng object.

```java
public class AppConfig {
    public static final int MAX_LOGIN_ATTEMPTS = 5;
}
```

Cách gọi:

```java
int maxAttempts = AppConfig.MAX_LOGIN_ATTEMPTS;
```

Lưu ý production: `static` phù hợp cho hằng số hoặc dữ liệu thật sự dùng chung. Không nên dùng static variable để lưu dữ liệu theo user/request/order.

Ví dụ không nên:

```java
public class CurrentUserHolder {
    public static String currentUserId; // nguy hiểm trong web app nhiều request
}
```

Trong backend nhiều request chạy song song, biến static như trên có thể khiến user này đọc nhầm dữ liệu của user khác.

### Local variable

Local variable nằm trong method hoặc block, chỉ dùng được trong phạm vi đó.

```java
public long calculateTotal(long price, int quantity) {
    long total = price * quantity;
    return total;
}
```

Khác với field, local variable không có giá trị mặc định nếu chưa gán.

```java
public void printAge() {
    int age;
    System.out.println(age); // compile error: age chưa được khởi tạo
}
```

### `final` variable

`final` nghĩa là biến chỉ được assign một lần.

```java
final int maxRetry = 3;
```

Với object reference, `final` làm reference không trỏ sang object khác, nhưng object bên trong vẫn có thể mutable nếu class cho phép.

```java
final List<String> names = new ArrayList<>();
names.add("An");              // được
names = new ArrayList<>();    // không được
```

### 5.1 Variables - example

Slide đưa ví dụ class `Customer`:

```java
public class Customer {
    private String email;

    // no modifier = package access modifier
    String position;

    protected String name;
    public String city;
    public static String staticField1;
    public final String ID_EMP;
    public static final String NAME_COM = "Framgia";
}
```

Giải thích:

- `private String email`: chỉ class `Customer` truy cập được.
- `String position`: package-private, class cùng package truy cập được.
- `protected String name`: class cùng package và subclass có thể truy cập.
- `public String city`: mọi nơi truy cập được.
- `public static String staticField1`: biến thuộc class, dùng chung.
- `public final String ID_EMP`: instance field chỉ gán một lần, thường cần gán trong constructor.
- `public static final String NAME_COM`: hằng số class-level.

Phiên bản production-style hơn:

```java
public class Customer {
    public static final String COMPANY_NAME = "Framgia";

    private final String employeeId;
    private final String email;
    private String name;
    private String city;

    public Customer(String employeeId, String email, String name, String city) {
        if (employeeId == null || employeeId.isBlank()) {
            throw new IllegalArgumentException("Employee id is required");
        }
        if (email == null || email.isBlank()) {
            throw new IllegalArgumentException("Email is required");
        }
        this.employeeId = employeeId;
        this.email = email;
        this.name = name;
        this.city = city;
    }

    public String getEmail() {
        return email;
    }

    public void changeCity(String city) {
        this.city = city;
    }
}
```

Điểm tốt hơn:

- Hằng số dùng tên `UPPER_SNAKE_CASE`: `COMPANY_NAME`.
- Field để `private` để bảo vệ state.
- Dữ liệu bắt buộc dùng `final`.
- Constructor đảm bảo object tạo ra hợp lệ.
- Không public field lung tung; public method thể hiện hành vi rõ ràng.

## 5.2 Constructor

### Tóm tắt

Constructor là thành phần đặc biệt dùng để khởi tạo object. Constructor có tên trùng với tên class và **không có return type**, kể cả `void`.

Cú pháp:

```java
ClassName(parameters) {
    // initialization code
}
```

Ví dụ:

```java
public class Vehicle {
    private String name;
    private String color;
    private float speed;

    public Vehicle() {
    }

    public Vehicle(String name, String color, float speed) {
        this.name = name;
        this.color = color;
        this.speed = speed;
    }
}
```

### Default constructor và parameterized constructor

- **Default/no-argument constructor:** constructor không có parameter.
- **Parameterized constructor:** constructor có parameter.

Ví dụ:

```java
public class Test {
    private int number;

    public Test() {
    }

    public Test(int number) {
        this.number = number;
    }
}
```

Lưu ý rất quan trọng: nếu bạn không khai báo constructor nào, Java tự tạo một no-arg constructor mặc định. Nhưng nếu bạn đã khai báo bất kỳ constructor nào, Java sẽ không tự tạo no-arg constructor nữa.

```java
public class User {
    private final String email;

    public User(String email) {
        this.email = email;
    }
}
```

Code sau sẽ lỗi compile:

```java
User user = new User(); // không có constructor User()
```

### Constructor overloading và constructor chaining

Một class có thể có nhiều constructor, miễn là danh sách parameter khác nhau.

Ví dụ `Rectangle` trên slide:

```java
public class Rectangle {
    private int x, y;
    private int width, height;

    public Rectangle() {
        this(0, 0, 1, 1);
    }

    public Rectangle(int width, int height) {
        this(0, 0, width, height);
    }

    public Rectangle(int x, int y, int width, int height) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
    }
}
```

`this(...)` gọi constructor khác trong cùng class. Quy tắc: `this(...)` phải là câu lệnh đầu tiên trong constructor.

### Ví dụ production

```java
public class Money {
    private final long amount;
    private final String currency;

    public Money(long amount) {
        this(amount, "VND");
    }

    public Money(long amount, String currency) {
        if (amount < 0) {
            throw new IllegalArgumentException("Amount must not be negative");
        }
        if (currency == null || currency.isBlank()) {
            throw new IllegalArgumentException("Currency is required");
        }
        this.amount = amount;
        this.currency = currency;
    }
}
```

Trong production, constructor nên đảm bảo object hợp lệ ngay từ lúc tạo. Đừng để object được tạo ra với field bắt buộc bị `null`, sau đó hy vọng code khác set lại sau.

### Quy tắc constructor

- Constructor không có return type.
- Constructor name phải trùng class name.
- Constructor thường dùng để gán giá trị ban đầu cho field.
- Constructor có thể overload.
- Constructor không thể là `static`, `final` hoặc `abstract`.
- Constructor có thể có access modifier, ví dụ `private constructor` trong singleton/factory pattern.

## 5.3 Methods

### Tóm tắt

Method là function nằm trong class, dùng để biểu diễn behavior của object hoặc behavior thuộc class.

Ví dụ trong slide, `Car` có:

- Field: `name`, `color`.
- Method: `speed()`, `accelerate()`.

### Cú pháp khai báo method

```java
accessModifier returnType methodName(parameterList) {
    // method body
}
```

Ví dụ:

```java
public int sum(int a, int b) {
    return a + b;
}
```

Các phần chính:

- `public`: access modifier.
- `int`: return type.
- `sum`: method name.
- `(int a, int b)`: parameter list.
- `{ return a + b; }`: method body.

Nếu method không trả về dữ liệu, dùng `void`:

```java
public void printInfo() {
    System.out.println("Hello");
}
```

### Method naming rules

Tên method là Java identifier, nên:

- Không được là Java keyword, ví dụ `float()` sai vì `float` là keyword.
- Không được chứa khoảng trắng.
- Không được bắt đầu bằng chữ số.
- Có thể bắt đầu bằng chữ cái, `_`, hoặc `$`.

Ví dụ sai:

```java
void float() {}
void 1brake() {}
void car speed() {}
```

Ví dụ hợp lệ theo cú pháp:

```java
void brake() {}
void $brake() {}
void car_speed() {}
```

Nhưng trong code production, nên theo convention Java:

```java
void brake() {}
void calculateTotalAmount() {}
void sendVerificationEmail() {}
```

Không nên dùng `$` trong tên method tự viết. Dấu `$` thường xuất hiện trong code generated hoặc inner class compiled name.

### Method signature

Method signature trong Java gồm **method name + parameter types**. Return type không phải một phần đủ để overload.

```java
public int sum(int a, int b) {
    return a + b;
}
```

Signature ở mức compile là `sum(int, int)`.

Hai method sau không overload hợp lệ vì chỉ khác return type:

```java
public int getValue() {
    return 1;
}

public String getValue() {
    return "1";
}
```

### Ví dụ production

```java
public class ShippingFeeCalculator {
    public long calculateFee(long distanceKm, long weightKg) {
        if (distanceKm <= 0 || weightKg <= 0) {
            throw new IllegalArgumentException("Distance and weight must be positive");
        }
        return 10_000 + distanceKm * 1_000 + weightKg * 2_000;
    }
}
```

Method tốt nên:

- Có tên thể hiện rõ hành động.
- Parameter vừa đủ, không quá nhiều.
- Validate input quan trọng.
- Return type rõ ràng.
- Không làm quá nhiều việc cùng lúc.

## 5.4 Methods - types và static method

### Các loại method

Theo slide, Java methods có thể chia thành:

- **Standard Library methods:** method có sẵn trong JDK, ví dụ `Math.max()`, `String.isBlank()`, `List.add()`.
- **User-defined methods:** method do lập trình viên tự viết.
- **Static methods:** method thuộc về class.
- **Instance methods:** method thuộc về object, cần object để gọi.

Ví dụ standard library:

```java
int max = Math.max(10, 20);
boolean blank = " ".isBlank();
```

Ví dụ user-defined:

```java
public boolean isAdult(int age) {
    return age >= 18;
}
```

### Static method

Static method thuộc về class, thường gọi bằng class name:

```java
ClassName.methodName();
```

Ví dụ:

```java
public class TaxCalculator {
    public static long calculateVat(long amount) {
        return amount * 10 / 100;
    }
}
```

Gọi:

```java
long vat = TaxCalculator.calculateVat(1_000_000);
```

Đặc điểm:

- Không cần tạo object để gọi.
- Không dùng trực tiếp được `this` hoặc `super`.
- Truy cập trực tiếp được static field/static method.
- Không truy cập trực tiếp được instance field/instance method, vì không có object hiện tại.
- Vẫn có thể gọi instance method nếu có object cụ thể.

Ví dụ:

```java
public class Demo {
    private String name = "demo";

    public void printName() {
        System.out.println(name);
    }

    public static void main(String[] args) {
        // System.out.println(name); // lỗi: không truy cập trực tiếp instance field

        Demo demo = new Demo();
        demo.printName(); // được vì có object cụ thể
    }
}
```

### Khi nào dùng static method?

Nên dùng khi method:

- Không phụ thuộc vào state của object.
- Là utility/helper thuần tính toán.
- Là factory method đơn giản.
- Là entry point như `public static void main(String[] args)`.

Ví dụ production:

```java
public final class EmailNormalizer {
    private EmailNormalizer() {
    }

    public static String normalize(String email) {
        if (email == null) {
            throw new IllegalArgumentException("Email is required");
        }
        return email.trim().toLowerCase();
    }
}
```

Không nên biến mọi thứ thành static. Trong Spring/backend, service thường là instance bean để dễ inject dependency, mock khi test, cấu hình transaction, security và observability.

## 5.5 Overloading of methods

### Tóm tắt

Method overloading là khả năng trong cùng một class có nhiều method **cùng tên** nhưng khác parameter list.

Có thể overload bằng cách thay đổi:

- Số lượng parameter.
- Kiểu dữ liệu của parameter.
- Thứ tự kiểu dữ liệu của parameter.

Ví dụ trên slide:

```java
public void disp(char c) {
    System.out.println(c);
}

public void disp(int c) {
    System.out.println(c);
}

public void disp(char c, int num) {
    System.out.println(c + " " + num);
}

public void disp(int num, char c) {
    System.out.println("I'm the first");
}
```

Các method trên đều tên `disp`, nhưng signature khác nhau:

- `disp(char)`
- `disp(int)`
- `disp(char, int)`
- `disp(int, char)`

### Ví dụ production

```java
public class NotificationService {
    public void send(String email, String message) {
        send(email, message, false);
    }

    public void send(String email, String message, boolean urgent) {
        if (urgent) {
            // gửi qua kênh ưu tiên
        }
        // gửi email
    }

    public void send(List<String> emails, String message) {
        for (String email : emails) {
            send(email, message);
        }
    }
}
```

Overloading giúp API dễ dùng hơn, nhưng nếu lạm dụng sẽ làm code khó đọc.

### Quy tắc overloading

- Chỉ khác return type thì không phải overload hợp lệ.
- Chỉ khác tên parameter cũng không phải overload.
- Overloading được quyết định ở compile time.
- Cẩn thận với `null`, autoboxing, varargs vì có thể gây ambiguous method call.

Ví dụ không hợp lệ:

```java
public int parse(String value) {
    return Integer.parseInt(value);
}

public long parse(String value) {
    return Long.parseLong(value);
}
```

Ví dụ dễ ambiguous:

```java
public void print(String value) {}
public void print(Integer value) {}

print(null); // có thể gây khó hiểu hoặc lỗi nếu có nhiều overload phù hợp
```

Trong production, nên overload khi các method thật sự cùng ý nghĩa. Nếu hành vi khác nhau nhiều, hãy đặt tên khác rõ hơn.

## 5.6 Difference between constructor and method

| Tiêu chí         | Constructor                                                                                                | Method                                                    |
| ------------------ | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Tên               | Phải trùng tên class                                                                                    | Có thể là tên hợp lệ bất kỳ                       |
| Return type        | Không có return type                                                                                     | Bắt buộc có return type hoặc`void`                  |
| Cách gọi         | Được gọi khi tạo object bằng`new`, hoặc gọi constructor khác bằng `this(...)`/`super(...)` | Được gọi bởi lập trình viên hoặc framework       |
| Mục đích chính | Khởi tạo object                                                                                          | Thực thi hành vi/logic                                  |
| Kế thừa          | Không được kế thừa                                                                                   | Có thể được kế thừa/override nếu không bị chặn |
| Overloading        | Có thể overload                                                                                          | Có thể overload                                         |

Ví dụ:

```java
public class User {
    private final String email;

    public User(String email) {
        this.email = email;
    }

    public boolean hasCompanyEmail() {
        return email.endsWith("@company.com");
    }
}
```

Trong ví dụ:

- `User(String email)` là constructor.
- `hasCompanyEmail()` là method.

Lỗi phổ biến:

```java
public void User(String email) {
    this.email = email;
}
```

Đây không phải constructor vì có `void`. Nó là một method tên `User`, và thường là bug.

## 5.7 Using `this` keyword

### Tóm tắt

`this` là reference đến object hiện tại. Có thể dùng trong instance method hoặc constructor.

`this` thường dùng để:

- Phân biệt instance variable với local variable/parameter cùng tên.
- Gọi constructor khác trong cùng class.
- Gọi method hoặc truyền chính object hiện tại sang nơi khác.

### Phân biệt field và parameter

```java
public class Vehicle {
    private String name;
    private String color;

    public Vehicle(String name, String color) {
        this.name = name;
        this.color = color;
    }
}
```

Ở đây:

- `name` bên phải là parameter.
- `this.name` là field của object hiện tại.

Nếu không dùng `this`:

```java
public Vehicle(String name, String color) {
    name = name;
    color = color;
}
```

Code này không gán vào field như mong muốn. Nó chỉ gán parameter cho chính nó.

### Gọi constructor khác bằng `this(...)`

Ví dụ trên slide:

```java
public class Vehicle {
    private String name;
    private String color;

    public Vehicle(String name, String color) {
        this.name = name;
        this.color = color;
    }

    public Vehicle() {
        this("car", "yellow");
        System.out.println("Refer constructor");
    }
}
```

Quy tắc: `this(...)` phải là dòng đầu tiên trong constructor.

### Gọi method hiện tại

```java
public void methodOne() {
    System.out.println("Inside Method ONE");
}

public void methodTwo() {
    System.out.println("Inside Method TWO");
    this.methodOne();
}
```

Trong instance method, có thể gọi `methodOne()` trực tiếp; `this.methodOne()` chỉ làm rõ rằng method thuộc object hiện tại.

### Ví dụ production

```java
public class Order {
    private final String id;
    private OrderStatus status;

    public Order(String id) {
        this(id, OrderStatus.CREATED);
    }

    public Order(String id, OrderStatus status) {
        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("Order id is required");
        }
        this.id = id;
        this.status = status;
    }

    public void markPaid() {
        this.ensureCreated();
        this.status = OrderStatus.PAID;
    }

    private void ensureCreated() {
        if (this.status != OrderStatus.CREATED) {
            throw new IllegalStateException("Order is not in CREATED status");
        }
    }
}
```

Trong ví dụ này:

- `this(id, OrderStatus.CREATED)` tái sử dụng constructor chính.
- `this.id` và `this.status` phân biệt field với parameter.
- `this.ensureCreated()` gọi method của object hiện tại.

### Lưu ý chương 5

- Instance variable thuộc từng object; static variable thuộc class; local variable chỉ tồn tại trong block/method và phải được khởi tạo trước khi đọc.
- `final` ngăn gán lại biến. Với object reference, `final` không tự làm object trở thành immutable.
- Không dùng static field để giữ dữ liệu thay đổi theo request hoặc user trong ứng dụng backend.
- Java chỉ tự tạo no-argument constructor khi class chưa khai báo bất kỳ constructor nào.
- Constructor không có return type và nên bảo đảm object hợp lệ ngay khi được tạo.
- Static method không có `this`; muốn gọi instance method thì phải thông qua một object cụ thể.
- Overloading phải khác parameter list; chỉ đổi return type hoặc tên parameter là không đủ.
- `this(...)` phải là statement đầu tiên trong constructor và không thể xuất hiện cùng `super(...)` trong một constructor.
- Dùng `this.field = parameter` khi field và parameter trùng tên; không cần thêm `this` ở mọi chỗ nếu code đã rõ.

## 6. Data Type and Operator

Chương này trình bày hai nền tảng của biểu thức Java: **kiểu dữ liệu** xác định một giá trị có thể lưu gì, còn **toán tử** xác định cách xử lý các giá trị đó.

## 6.1 Data Type

### Tổng quan

Data type là một nhóm các giá trị có cùng cách biểu diễn và cùng nhóm phép toán hợp lệ. Java là ngôn ngữ **statically typed**: kiểu của biến được biết khi biên dịch và compiler sẽ chặn nhiều phép gán không hợp lệ.

Java chia kiểu dữ liệu thành hai nhóm:

- **Primitive type:** lưu trực tiếp một giá trị cơ bản. Java có đúng 8 primitive type: `boolean`, `char`, `byte`, `short`, `int`, `long`, `float`, `double`.
- **Reference type:** biến giữ một reference trỏ tới object. Các ví dụ gồm `String`, array, class, interface, enum và record.

```java
int quantity = 3;                    // primitive
String productName = "Keyboard";    // reference
Product product = new Product();     // reference
int[] stockByWarehouse = {10, 5};    // reference
```

### Tám primitive type

| Kiểu       |                  Kích thước/biểu diễn | Phạm vi hoặc ý nghĩa                           | Ví dụ                    |
| ----------- | -----------------------------------------: | -------------------------------------------------- | -------------------------- |
| `boolean` | JVM không quy định cố định là 1 bit | `true` hoặc `false`                           | `boolean active = true;` |
| `byte`    |                                      8 bit | -128 đến 127                                     | `byte retryCount = 3;`   |
| `short`   |                                     16 bit | -32.768 đến 32.767                               | `short year = 2026;`     |
| `int`     |                                     32 bit | -2.147.483.648 đến 2.147.483.647                 | `int quantity = 100;`    |
| `long`    |                                     64 bit | -2^63 đến 2^63 - 1                               | `long id = 3_200L;`      |
| `char`    |                                     16 bit | Một UTF-16 code unit,`\u0000` đến `\uFFFF`  | `char grade = 'A';`      |
| `float`   |                           IEEE 754, 32 bit | Số thực, độ chính xác khoảng 6-7 chữ số   | `float rate = 12.34F;`   |
| `double`  |                           IEEE 754, 64 bit | Số thực, độ chính xác khoảng 15-16 chữ số | `double score = 98.5;`   |

Giá trị mặc định như `0`, `false`, `'\u0000'` và `null` chỉ được Java tự gán cho **field** và phần tử array. Local variable phải được khởi tạo trước khi đọc.

```java
public class Counter {
    private int total; // field: mặc định là 0

    public void printNext() {
        int next;
        // System.out.println(next); // Lỗi compile: next chưa được khởi tạo
        next = total + 1;
        System.out.println(next);
    }
}
```

### Primitive type và reference type khi truyền tham số

Java **luôn pass-by-value**. Khi truyền primitive, method nhận bản sao của giá trị. Khi truyền object, method nhận bản sao của reference; hai reference tạm thời cùng trỏ tới một object nên method có thể làm thay đổi trạng thái object đó.

```java
static void increase(double price) {
    price += 5;
}

static void increase(Product product) {
    product.setPrice(product.getPrice() + 5);
}
```

```java
double price = 100;
increase(price);
System.out.println(price); // 100.0: bản gốc không đổi

Product product = new Product(100);
increase(product);
System.out.println(product.getPrice()); // 105.0: object bị thay đổi
```

Gán lại parameter reference bên trong method không thể làm biến của caller trỏ sang object mới:

```java
static void replace(Product product) {
    product = new Product(999);
}

Product product = new Product(100);
replace(product);
System.out.println(product.getPrice()); // Vẫn là 100.0
```

### Type casting - ép kiểu primitive

#### Widening conversion - chuyển kiểu mở rộng

Compiler thường tự chuyển từ kiểu có phạm vi nhỏ sang kiểu có phạm vi biểu diễn lớn hơn:

```text
byte -> short -> int -> long -> float -> double
char ---------> int -> long -> float -> double
```

```java
int quantity = 100;
long totalQuantity = quantity;
double measuredQuantity = totalQuantity;
```

`boolean` không thuộc chuỗi chuyển đổi số và không thể ép sang/từ numeric type. Ngoài ra, widening không phải lúc nào cũng giữ nguyên độ chính xác; ví dụ một `long` lớn chuyển sang `float` có thể bị làm tròn.

#### Narrowing conversion - chuyển kiểu thu hẹp

Chuyển từ kiểu lớn sang kiểu nhỏ hơn cần cast tường minh:

```java
double amount = 125.90;
int wholeAmount = (int) amount; // 125, phần thập phân bị cắt

int value = 130;
byte smallValue = (byte) value; // -126 do overflow
```

Cú pháp:

```java
TargetType result = (TargetType) sourceValue;
```

Cast chỉ yêu cầu compiler cho phép chuyển; nó không bảo đảm giá trị sau chuyển đổi còn đúng về nghiệp vụ.

### Ví dụ production: chọn kiểu cho dữ liệu thanh toán

Không nên dùng `float` hoặc `double` cho tiền vì số thực nhị phân có sai số biểu diễn. Production Java thường dùng `BigDecimal` hoặc lưu số đơn vị nhỏ nhất bằng `long`.

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

public record LineItem(BigDecimal unitPrice, int quantity) {
    public LineItem {
        if (unitPrice == null || unitPrice.signum() < 0) {
            throw new IllegalArgumentException("Unit price must be non-negative");
        }
        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }
    }

    public BigDecimal subtotal() {
        return unitPrice
                .multiply(BigDecimal.valueOf(quantity))
                .setScale(2, RoundingMode.HALF_UP);
    }
}
```

## 6.2 Operator

Operator là ký hiệu thực hiện một thao tác trên một hay nhiều operand. Các nhóm thường gặp:

| Nhóm             | Toán tử                                     | Ví dụ                                  |
| ----------------- | --------------------------------------------- | ---------------------------------------- |
| Số học          | `+`, `-`, `*`, `/`, `%`             | `subtotal = price * quantity`          |
| Gán              | `=`, `+=`, `-=`, `*=`, `/=`, `%=` | `stock -= soldQuantity`                |
| Một ngôi        | `+`, `-`, `++`, `--`, `!`           | `attempt++`, `!active`               |
| So sánh          | `==`, `!=`, `>`, `<`, `>=`, `<=`  | `quantity > 0`                         |
| Logic ngắn mạch | `&&`, `                                     |                                          |
| Bit               | `&`, `                                      | `, `^`, `~`, `<<`, `>>`, `>>>` |
| Ba ngôi          | `condition ? a : b`                         | `vip ? vipPrice : normalPrice`         |

### Toán tử số học và thứ tự ưu tiên

Với biểu thức trên slide:

```java
int result = 10 * 5 + 100 / 10 - 5 + 7 % 2;
System.out.println(result); // 56
```

`*`, `/`, `%` được tính trước `+`, `-`; các toán tử cùng mức thường được tính từ trái sang phải. Khi business rule có nhiều phép tính, nên dùng ngoặc để thể hiện chủ ý:

```java
int result = (10 * 5) + (100 / 10) - 5 + (7 % 2);
```

### Phép chia số nguyên và phép chia lấy dư

Nếu cả hai operand là số nguyên, Java trả về kết quả số nguyên và cắt phần thập phân:

```java
int result = 3 / 2;       // 1
double wrong = 3 / 2;     // 1.0, vì phép chia đã xảy ra trước khi gán
double correct = 3.0 / 2; // 1.5
```

Toán tử `%` trả về phần dư, thường dùng để kiểm tra chẵn/lẻ, chia trang hoặc quay vòng index:

```java
boolean isEven = orderNumber % 2 == 0;
```

Trong ví dụ phép toán trên slide, sau `result = result - 1` thì `result` bằng `2`; tiếp theo `result = result / 2` phải cho ra `1`, không phải `2`. Sau đó `1 % 7` cũng bằng `1`.

### Toán tử một ngôi

```java
int result = 0;
result++;              // 1
result = -result;      // -1

boolean success = false;
System.out.println(!success); // true
```

Phân biệt prefix và postfix khi giá trị của biểu thức được sử dụng:

```java
int a = 5;
int x = a++; // x = 5, sau đó a = 6

int b = 5;
int y = ++b; // b = 6, y = 6
```

Trong production, tránh ghép nhiều `++`/`--` vào một biểu thức phức tạp vì rất dễ đọc sai.

### Toán tử logic và short-circuit

```java
int value1 = 1;
int value2 = 2;

if (value1 == 1 && value2 == 2) {
    System.out.println("Cả hai điều kiện đúng");
}

if (value1 == 1 || value2 == 1) {
    System.out.println("Có ít nhất một điều kiện đúng");
}
```

- `a && b`: nếu `a` là `false`, Java không đánh giá `b`.
- `a || b`: nếu `a` là `true`, Java không đánh giá `b`.

Short-circuit giúp viết null check an toàn:

```java
if (customer != null && customer.isActive()) {
    sendPromotion(customer);
}
```

Đảo hai vế thành `customer.isActive() && customer != null` có thể gây `NullPointerException`.

### So sánh primitive và object

Với primitive, `==` so sánh giá trị. Với reference type, `==` kiểm tra hai reference có trỏ tới cùng object hay không; để so sánh nội dung thường dùng `equals()`.

```java
String expectedStatus = "PAID";
String actualStatus = new String("PAID");

System.out.println(expectedStatus == actualStatus);      // false
System.out.println(expectedStatus.equals(actualStatus)); // true
```

Khi giá trị có thể `null`, có thể dùng `Objects.equals(a, b)`:

```java
boolean sameEmail = Objects.equals(customerEmail, requestEmail);
```

### Ví dụ production: điều kiện áp dụng khuyến mãi

```java
public BigDecimal calculateDiscount(Order order, Customer customer) {
    if (order == null || customer == null) {
        throw new IllegalArgumentException("Order and customer are required");
    }

    boolean eligible = customer.isActive()
            && order.total().compareTo(new BigDecimal("1000000")) >= 0
            && !order.isCancelled();

    BigDecimal rate = eligible
            ? new BigDecimal("0.10")
            : BigDecimal.ZERO;

    return order.total().multiply(rate);
}
```

Ví dụ kết hợp null validation, `&&`, `!`, so sánh `BigDecimal` bằng `compareTo()` và toán tử ba ngôi. Không dùng `>`/`<` với object `BigDecimal`.

### Lưu ý chương 6

- `String` là reference type và immutable, không phải primitive type; Java luôn truyền tham số theo giá trị, kể cả khi giá trị được truyền là một reference.
- Reference có thể là `null`; unboxing một wrapper `null`, chẳng hạn `Integer` sang `int`, gây `NullPointerException`.
- Thường dùng `int` cho quantity/counter, `long` cho phạm vi lớn và `BigDecimal` cho tiền; tránh `float`/`double` trong tính toán tài chính.
- Narrowing cast có thể mất dữ liệu hoặc overflow. Khi cần kiểm tra, dùng API như `Math.toIntExact`, `Math.addExact`, `Math.multiplyExact`.
- Chia hai số nguyên sẽ cắt phần thập phân; chia số nguyên cho `0` gây `ArithmeticException`.
- `&&` và `||` short-circuit, còn `&` và `|` với boolean luôn đánh giá cả hai vế.
- Dùng ngoặc để làm rõ biểu thức dài và tránh phụ thuộc quá nhiều vào việc nhớ thứ tự ưu tiên.
- Với object, `==` so sánh reference; dùng `equals()` hoặc `Objects.equals()` để so sánh nội dung.
- Toán tử `+` có thể nối chuỗi: `"Total: " + 1 + 2` cho `"Total: 12"`, còn `"Total: " + (1 + 2)` cho `"Total: 3"`.
