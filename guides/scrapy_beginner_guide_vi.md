# Hướng dẫn chi tiết Scrapy cho người mới: từ khởi tạo project đến spider, item, pipeline và export dữ liệu

> Cập nhật: 08/07/2026. Tài liệu này dựa trên Scrapy docs hiện tại, kèm đối chiếu một số bài viết mới năm 2025–2026. Khi học Scrapy, ưu tiên docs chính thức trước, bài blog dùng để tham khảo kinh nghiệm thực tế.

---

## 0. Scrapy là gì?

**Scrapy** là framework Python dùng để crawl/scrape website và trích xuất dữ liệu có cấu trúc. Thay vì tự viết `requests.get()`, tự quản lý queue URL, retry, logging, lưu file, giới hạn tốc độ..., Scrapy đã có sẵn kiến trúc:

```text
Spider -> Request -> Scheduler -> Downloader -> Response -> Spider -> Item -> Pipeline/Feed Export
```

Nói đơn giản:

- **Spider**: bạn viết logic vào URL nào, lấy dữ liệu gì, đi tiếp link nào.
- **Scheduler**: Scrapy tự quản lý hàng đợi request.
- **Downloader**: Scrapy tải HTML/API response.
- **Middleware**: chặn/sửa request hoặc response trước khi vào Downloader/Spider.
- **Item**: cấu trúc dữ liệu bạn muốn lấy.
- **Pipeline**: làm sạch, validate, loại trùng, lưu database.
- **Feed Export**: xuất nhanh ra JSON, JSONL, CSV, XML.

---

## 1. Cài đặt môi trường

### 1.1. Tạo thư mục project

```bash
mkdir scrapy_learning
cd scrapy_learning
```

### 1.2. Tạo virtual environment

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 1.3. Cài Scrapy

```bash
pip install scrapy
```

Kiểm tra:

```bash
scrapy version
```

Có thể kiểm tra benchmark cài đặt:

```bash
scrapy bench
```

> Ghi chú: Scrapy docs hiện yêu cầu Python 3.10+. Trên Windows, nếu `pip install scrapy` lỗi build dependency, cách dễ hơn là cài qua Conda:
>
> ```bash
> conda install -c conda-forge scrapy
> ```

---

## 2. Khởi tạo project Scrapy

Lệnh chính:

```bash
scrapy startproject quotes_project
```

Sau lệnh này, Scrapy tạo cấu trúc:

```text
quotes_project/
├── scrapy.cfg
└── quotes_project/
    ├── __init__.py
    ├── items.py
    ├── middlewares.py
    ├── pipelines.py
    ├── settings.py
    └── spiders/
        └── __init__.py
```

Vào project:

```bash
cd quotes_project
```

---

## 3. Ý nghĩa từng file trong project

### 3.1. `scrapy.cfg`

File cấu hình ở **project root**. Scrapy nhìn vào đây để biết settings mặc định nằm ở đâu.

Ví dụ:

```ini
[settings]
default = quotes_project.settings
```

Bạn thường ít sửa file này khi mới học.

---

### 3.2. `quotes_project/settings.py`

Nơi cấu hình toàn bộ crawler:

- tên bot;
- spider modules;
- bật/tắt robots.txt;
- delay giữa các request;
- concurrency;
- bật pipeline;
- cấu hình export;
- cấu hình middleware;
- log level.

Ví dụ cấu hình cơ bản:

```python
BOT_NAME = "quotes_project"

SPIDER_MODULES = ["quotes_project.spiders"]
NEWSPIDER_MODULE = "quotes_project.spiders"

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

ITEM_PIPELINES = {
    "quotes_project.pipelines.CleanQuotePipeline": 300,
    "quotes_project.pipelines.DuplicatesPipeline": 400,
}

FEEDS = {
    "data/quotes.jsonl": {
        "format": "jsonlines",
        "encoding": "utf8",
        "overwrite": True,
    }
}
```

Ý nghĩa nhanh:

| Setting                            | Ý nghĩa                                    |
| ---------------------------------- | -------------------------------------------- |
| `BOT_NAME`                       | Tên bot/crawler                             |
| `SPIDER_MODULES`                 | Scrapy tìm spider trong package nào        |
| `NEWSPIDER_MODULE`               | Lệnh`genspider` tạo spider vào đâu    |
| `ROBOTSTXT_OBEY`                 | Có tuân thủ`robots.txt` không          |
| `DOWNLOAD_DELAY`                 | Nghỉ bao lâu giữa các request            |
| `CONCURRENT_REQUESTS_PER_DOMAIN` | Số request đồng thời tới mỗi domain    |
| `ITEM_PIPELINES`                 | Bật pipeline nào, chạy theo thứ tự nào |
| `FEEDS`                          | Cấu hình xuất file tự động             |

---

### 3.3. `quotes_project/items.py`

Nơi định nghĩa **schema dữ liệu** bạn muốn lấy.

Ví dụ:

```python
import scrapy


class QuoteItem(scrapy.Item):
    text = scrapy.Field()
    author = scrapy.Field()
    tags = scrapy.Field()
    source_url = scrapy.Field()
```

Bạn có thể `yield dict` trực tiếp từ spider, nhưng dùng `Item` giúp:

- tránh sai tên field;
- dễ thống nhất schema;
- pipeline dễ xử lý;
- export ra CSV/JSON ổn định hơn.

---

### 3.4. `quotes_project/spiders/`

Thư mục chứa các spider. Mỗi spider thường crawl một website hoặc một nhóm URL cùng cấu trúc.

Ví dụ file:

```text
quotes_project/spiders/quotes.py
```

Spider là nơi bạn viết:

- bắt đầu từ URL nào;
- parse HTML/API response ra sao;
- lấy dữ liệu gì;
- có follow link tiếp hay không;
- callback nào xử lý trang tiếp theo.

---

### 3.5. `quotes_project/pipelines.py`

Nơi xử lý item sau khi spider đã lấy được dữ liệu.

Pipeline phù hợp để:

- làm sạch text;
- validate field bắt buộc;
- loại item trùng;
- chuẩn hoá kiểu dữ liệu;
- ghi database;
- gửi dữ liệu sang queue/data lake.

Pipeline **không nên** là nơi parse HTML chính. Parse HTML nên nằm trong spider.

---

### 3.6. `quotes_project/middlewares.py`

Nơi viết middleware nếu cần can thiệp vào request/response.

Ví dụ dùng middleware để:

- đổi User-Agent;
- thêm header;
- xử lý proxy;
- chặn request không hợp lệ;
- retry theo logic riêng;
- sửa response trước khi đưa vào spider.

Người mới có thể chưa cần sửa file này.

---

### 3.7. `__init__.py`

Đánh dấu thư mục là Python package. Thường không cần sửa.

---

## 4. Các lệnh Scrapy quan trọng

### 4.1. Xem trợ giúp

```bash
scrapy -h
scrapy crawl -h
scrapy genspider -h
```

---

### 4.2. Tạo project

```bash
scrapy startproject quotes_project
```

Cú pháp tổng quát:

```bash
scrapy startproject <project_name> [project_dir]
```

---

### 4.3. Tạo spider

```bash
scrapy genspider quotes quotes.toscrape.com
```

Sau lệnh này, Scrapy tạo file:

```text
quotes_project/spiders/quotes.py
```

Cú pháp:

```bash
scrapy genspider <spider_name> <domain_or_url>
```

Một số template:

```bash
scrapy genspider -l
scrapy genspider -t crawl quotes_crawl quotes.toscrape.com
```

- `basic`: spider cơ bản.
- `crawl`: dùng `CrawlSpider` + rules để follow link theo rule.
- `xmlfeed`, `csvfeed`: dùng cho XML/CSV feed.

---

### 4.4. Chạy spider

```bash
scrapy crawl quotes
```

Trong đó `quotes` là `name` của spider:

```python
class QuotesSpider(scrapy.Spider):
    name = "quotes"
```

---

### 4.5. Chạy spider và xuất file nhanh

Ghi đè file JSON:

```bash
scrapy crawl quotes -O data/quotes.json
```

Append file JSONL:

```bash
scrapy crawl quotes -o data/quotes.jsonl
```

Xuất CSV:

```bash
scrapy crawl quotes -O data/quotes.csv
```

Gợi ý:

- Dùng `-O` khi muốn **overwrite** file cũ.
- Dùng `-o` khi muốn **append**.
- Với append, nên dùng `.jsonl`, không nên append `.json` vì dễ làm file JSON invalid.

---

### 4.6. Truyền tham số vào spider

```bash
scrapy crawl quotes -a tag=humor -O data/humor_quotes.json
```

Trong spider có thể đọc:

```python
self.tag
```

---

### 4.7. Test selector bằng Scrapy shell

```bash
scrapy shell "https://quotes.toscrape.com/"
```

Trong shell:

```python
response.css("div.quote")
response.css("span.text::text").get()
response.css("div.tags a.tag::text").getall()
response.css("li.next a::attr(href)").get()
```

Lệnh shell rất quan trọng vì giúp bạn test CSS/XPath trước khi viết vào spider.

---

### 4.8. Xem spider hiện có

```bash
scrapy list
```

---

### 4.9. Debug parse callback

```bash
scrapy parse "https://quotes.toscrape.com/" --spider=quotes
```

---

### 4.10. Fetch URL bằng downloader của Scrapy

```bash
scrapy fetch "https://quotes.toscrape.com/"
```

Lệnh này hữu ích vì nó dùng downloader/middleware/settings của Scrapy, không giống hẳn `curl` hoặc browser.

---

### 4.11. Mở response trong browser

```bash
scrapy view "https://quotes.toscrape.com/"
```

---

### 4.12. Xem setting đang dùng

```bash
scrapy settings --get BOT_NAME
scrapy settings --get ROBOTSTXT_OBEY
scrapy settings --get DOWNLOAD_DELAY
```

---

## 5. Viết spider đầu tiên

Mở file:

```text
quotes_project/spiders/quotes.py
```

Code đầy đủ:

```python
import scrapy
from quotes_project.items import QuoteItem


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com/"]

    def parse(self, response):
        for quote in response.css("div.quote"):
            item = QuoteItem()
            item["text"] = quote.css("span.text::text").get()
            item["author"] = quote.css("small.author::text").get()
            item["tags"] = quote.css("div.tags a.tag::text").getall()
            item["source_url"] = response.url
            yield item

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
```

Chạy:

```bash
scrapy crawl quotes -O data/quotes.json
```

---

## 6. Giải thích spider từng dòng

```python
import scrapy
```

Import framework Scrapy.

```python
from quotes_project.items import QuoteItem
```

Import schema item đã định nghĩa trong `items.py`.

```python
class QuotesSpider(scrapy.Spider):
```

Tạo spider kế thừa từ `scrapy.Spider`.

```python
name = "quotes"
```

Tên spider. Khi chạy dùng:

```bash
scrapy crawl quotes
```

Tên này phải unique trong project.

```python
allowed_domains = ["quotes.toscrape.com"]
```

Giới hạn domain spider được phép crawl. Nếu bật OffsiteMiddleware, Scrapy sẽ không follow URL ngoài domain này.

```python
start_urls = ["https://quotes.toscrape.com/"]
```

Danh sách URL đầu tiên. Scrapy tự tạo request từ các URL này và gọi callback `parse`.

```python
def parse(self, response):
```

Callback mặc định. Mỗi khi Scrapy tải xong một URL, response sẽ được đưa vào hàm này.

```python
for quote in response.css("div.quote"):
```

Chọn tất cả block quote trong HTML bằng CSS selector.

```python
item["text"] = quote.css("span.text::text").get()
```

Lấy text đầu tiên match selector.

```python
item["tags"] = quote.css("div.tags a.tag::text").getall()
```

Lấy tất cả tag match selector, trả về list.

```python
yield item
```

Đưa item ra khỏi spider. Sau đó Scrapy sẽ gửi item qua pipeline hoặc feed exporter.

```python
next_page = response.css("li.next a::attr(href)").get()
```

Lấy link trang tiếp theo.

```python
yield response.follow(next_page, callback=self.parse)
```

Tạo request mới tới trang tiếp theo. Khi tải xong, Scrapy lại gọi `parse`.

---

## 7. CSS selector và XPath cơ bản

### 7.1. CSS selector hay dùng

```python
response.css("h1::text").get()
response.css("a::attr(href)").getall()
response.css("div.product")
response.css("div.product .price::text").get()
```

Ý nghĩa:

| Selector          | Ý nghĩa                                 |
| ----------------- | ----------------------------------------- |
| `h1::text`      | lấy text trong thẻ`h1`                |
| `a::attr(href)` | lấy thuộc tính`href` của thẻ `a` |
| `div.product`   | lấy các`div` có class `product`    |
| `.price::text`  | lấy text của element class`price`     |

### 7.2. XPath hay dùng

```python
response.xpath("//h1/text()").get()
response.xpath("//a/@href").getall()
response.xpath("//div[@class='product']")
```

### 7.3. `.get()` vs `.getall()`

```python
response.css("h1::text").get()
```

Lấy kết quả đầu tiên hoặc `None`.

```python
response.css("a::attr(href)").getall()
```

Lấy tất cả kết quả, trả về list.

---

## 8. Item là gì và khi nào dùng?

Bạn có thể yield dict:

```python
yield {
    "text": text,
    "author": author,
}
```

Nhưng project lớn nên dùng `Item` trong `items.py`:

```python
import scrapy


class QuoteItem(scrapy.Item):
    text = scrapy.Field()
    author = scrapy.Field()
    tags = scrapy.Field()
    source_url = scrapy.Field()
```

Ưu điểm:

```text
Spider parse HTML -> tạo QuoteItem -> yield item -> Pipeline xử lý -> Export/Database
```

Nếu bạn đang làm data engineering, hãy xem `Item` giống như **schema tạm ở tầng raw/bronze**.

---

## 9. Pipeline là gì?

Pipeline là chuỗi xử lý item sau khi spider `yield item`.

Ví dụ spider yield:

```python
yield item
```

Scrapy sẽ đưa item qua pipeline theo thứ tự cấu hình trong `settings.py`:

```python
ITEM_PIPELINES = {
    "quotes_project.pipelines.CleanQuotePipeline": 300,
    "quotes_project.pipelines.DuplicatesPipeline": 400,
    "quotes_project.pipelines.SQLitePipeline": 800,
}
```

Thứ tự chạy:

```text
Item từ Spider
  -> CleanQuotePipeline       # order 300
  -> DuplicatesPipeline       # order 400
  -> SQLitePipeline           # order 800
  -> Feed Export / kết thúc
```

Số nhỏ chạy trước. Số lớn chạy sau.

---

## 10. Viết pipeline làm sạch dữ liệu

Mở `quotes_project/pipelines.py`:

```python
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class CleanQuotePipeline:
    def process_item(self, item):
        adapter = ItemAdapter(item)

        text = adapter.get("text")
        author = adapter.get("author")

        if text:
            adapter["text"] = text.strip().replace("“", "").replace("”", "")

        if author:
            adapter["author"] = author.strip()

        tags = adapter.get("tags") or []
        adapter["tags"] = [tag.strip().lower() for tag in tags if tag.strip()]

        return item
```

Điểm quan trọng:

```python
return item
```

Nếu quên `return item`, item không đi tiếp pipeline sau.

---

## 11. Pipeline validate field bắt buộc

Thêm vào `pipelines.py`:

```python
class RequiredFieldsPipeline:
    required_fields = ["text", "author"]

    def process_item(self, item):
        adapter = ItemAdapter(item)

        for field in self.required_fields:
            if not adapter.get(field):
                raise DropItem(f"Missing required field: {field}")

        return item
```

Nếu item thiếu `text` hoặc `author`, pipeline raise `DropItem`, item bị loại và không đi tiếp pipeline sau.

---

## 12. Pipeline loại dữ liệu trùng

```python
class DuplicatesPipeline:
    def __init__(self):
        self.seen = set()

    def process_item(self, item):
        adapter = ItemAdapter(item)
        key = (adapter.get("text"), adapter.get("author"))

        if key in self.seen:
            raise DropItem(f"Duplicate item: {key}")

        self.seen.add(key)
        return item
```

Pipeline này chỉ chống trùng trong một lần chạy. Nếu muốn chống trùng qua nhiều lần chạy, dùng database hoặc lưu state bên ngoài.

---

## 13. Bật pipeline trong `settings.py`

```python
ITEM_PIPELINES = {
    "quotes_project.pipelines.CleanQuotePipeline": 300,
    "quotes_project.pipelines.RequiredFieldsPipeline": 350,
    "quotes_project.pipelines.DuplicatesPipeline": 400,
}
```

Luồng chạy:

```text
quotes.py
  yield QuoteItem
      |
      v
CleanQuotePipeline.process_item()
      |
      v
RequiredFieldsPipeline.process_item()
      |
      v
DuplicatesPipeline.process_item()
      |
      v
Feed Export / Database / Done
```

---

## 14. Pipeline lưu SQLite

Ví dụ lưu vào SQLite để thấy rõ `open_spider`, `process_item`, `close_spider`.

Trong `pipelines.py`:

```python
import sqlite3
from itemadapter import ItemAdapter


class SQLitePipeline:
    def open_spider(self):
        self.conn = sqlite3.connect("quotes.db")
        self.cur = self.conn.cursor()
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                author TEXT NOT NULL,
                tags TEXT,
                source_url TEXT
            )
            """
        )
        self.conn.commit()

    def close_spider(self):
        self.conn.commit()
        self.conn.close()

    def process_item(self, item):
        adapter = ItemAdapter(item)

        self.cur.execute(
            """
            INSERT INTO quotes (text, author, tags, source_url)
            VALUES (?, ?, ?, ?)
            """,
            (
                adapter.get("text"),
                adapter.get("author"),
                ",".join(adapter.get("tags") or []),
                adapter.get("source_url"),
            ),
        )
        self.conn.commit()
        return item
```

Bật trong `settings.py`:

```python
ITEM_PIPELINES = {
    "quotes_project.pipelines.CleanQuotePipeline": 300,
    "quotes_project.pipelines.RequiredFieldsPipeline": 350,
    "quotes_project.pipelines.DuplicatesPipeline": 400,
    "quotes_project.pipelines.SQLitePipeline": 800,
}
```

Chạy:

```bash
scrapy crawl quotes
```

Kiểm tra database:

```bash
sqlite3 quotes.db
SELECT * FROM quotes LIMIT 5;
.quit
```

> Lưu ý phiên bản: Scrapy docs mới dùng chữ ký method dạng `process_item(self, item)`, `open_spider(self)`, `close_spider(self)`. Một số project/blog cũ dùng `process_item(self, item, spider)`, `open_spider(self, spider)`, `close_spider(self, spider)`. Nếu bạn dùng bản Scrapy cũ và gặp lỗi số lượng tham số, hãy kiểm tra docs đúng với version bạn cài.

---

## 15. Feed Export: cách xuất dữ liệu nhanh không cần tự viết pipeline lưu file

Cách nhanh nhất:

```bash
scrapy crawl quotes -O data/quotes.json
scrapy crawl quotes -O data/quotes.csv
scrapy crawl quotes -O data/quotes.jsonl
scrapy crawl quotes -O data/quotes.xml
```

Hoặc cấu hình trong `settings.py`:

```python
FEEDS = {
    "data/quotes.jsonl": {
        "format": "jsonlines",
        "encoding": "utf8",
        "overwrite": True,
    },
    "data/quotes.csv": {
        "format": "csv",
        "encoding": "utf8",
        "overwrite": True,
        "fields": ["text", "author", "tags", "source_url"],
    },
}
```

Khi nào dùng Feed Export?

- Crawl nhỏ/vừa.
- Muốn xuất JSON/CSV nhanh.
- Chưa cần database.
- Dùng cho bước raw data landing.

Khi nào dùng Pipeline?

- Cần validate/làm sạch dữ liệu.
- Cần loại trùng.
- Cần lưu DB.
- Cần gọi API khác.
- Cần xử lý logic phức tạp.

Có thể dùng cả hai: pipeline làm sạch trước, feed export lưu file sau.

---

## 16. Luồng dữ liệu giữa các file trong Scrapy

Đây là phần quan trọng nhất nếu bạn muốn hiểu “file nào chạy trước, dữ liệu đi đâu”.

### 16.1. Luồng khi bạn chạy `scrapy crawl quotes`

```text
Terminal
  |
  | scrapy crawl quotes
  v
scrapy.cfg
  |
  | đọc default settings module
  v
quotes_project/settings.py
  |
  | biết SPIDER_MODULES, ITEM_PIPELINES, FEEDS, middleware...
  v
quotes_project/spiders/quotes.py
  |
  | tìm spider có name = "quotes"
  v
QuotesSpider.start_urls
  |
  | tạo initial Request
  v
Scheduler
  |
  | xếp request vào queue
  v
Downloader Middleware
  |
  | sửa/chặn request nếu cần
  v
Downloader
  |
  | tải HTML
  v
Downloader Middleware
  |
  | sửa/chặn response nếu cần
  v
QuotesSpider.parse(response)
  |
  | parse HTML bằng CSS/XPath
  | yield Item hoặc Request mới
  v
Nếu yield Request:
  quay lại Scheduler

Nếu yield Item:
  v
quotes_project/pipelines.py
  |
  | chạy các pipeline đã bật trong settings.py
  v
Feed Export / Database / File output
```

### 16.2. File không tự “gọi nhau” theo kiểu script bình thường

Người mới hay nghĩ:

```text
quotes.py gọi pipelines.py
pipelines.py gọi settings.py
```

Không đúng hoàn toàn.

Đúng hơn là:

```text
Scrapy Engine đọc settings -> load spider/pipeline/middleware -> điều phối dữ liệu qua từng component
```

Bạn viết các class trong file. Scrapy là người instantiate và gọi method đúng thời điểm.

---

## 17. Request và Response trong Scrapy

### 17.1. Request

Request là object đại diện cho một HTTP request.

Ví dụ:

```python
yield scrapy.Request(
    url="https://quotes.toscrape.com/page/2/",
    callback=self.parse,
)
```

Hoặc dùng `response.follow` cho link tương đối:

```python
yield response.follow("/page/2/", callback=self.parse)
```

### 17.2. Response

Response là kết quả Downloader tải về.

Trong callback:

```python
def parse(self, response):
    print(response.url)
    print(response.status)
    print(response.text[:100])
```

### 17.3. Truyền dữ liệu giữa callbacks

Ưu tiên dùng `cb_kwargs` cho dữ liệu nghiệp vụ:

```python
yield response.follow(
    detail_url,
    callback=self.parse_detail,
    cb_kwargs={"category": category_name},
)


def parse_detail(self, response, category):
    yield {
        "category": category,
        "title": response.css("h1::text").get(),
    }
```

Dùng `meta` khi bạn muốn truyền metadata liên quan tới request/middleware/debug.

---

## 18. Ví dụ spider nhiều callback: list page -> detail page

```python
import scrapy


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def parse(self, response):
        for book in response.css("article.product_pod"):
            title = book.css("h3 a::attr(title)").get()
            detail_url = book.css("h3 a::attr(href)").get()

            yield response.follow(
                detail_url,
                callback=self.parse_detail,
                cb_kwargs={"title": title},
            )

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_detail(self, response, title):
        yield {
            "title": title,
            "price": response.css("p.price_color::text").get(),
            "availability": response.css("p.instock.availability::text").getall(),
            "url": response.url,
        }
```

Luồng:

```text
parse list page
  -> lấy detail_url
  -> yield Request detail_url
  -> parse_detail detail page
  -> yield item
  -> pipeline/export
```

---

## 19. Middleware là gì?

Middleware nằm giữa các component chính. Có hai nhóm hay gặp:

### 19.1. Downloader Middleware

Nằm giữa Engine và Downloader.

```text
Engine -> Downloader Middleware -> Downloader -> Downloader Middleware -> Engine
```

Dùng khi cần:

- thêm/sửa header;
- đổi User-Agent;
- dùng proxy;
- xử lý retry đặc biệt;
- chặn request;
- sửa response trước khi spider nhận.

Ví dụ đơn giản:

```python
class CustomHeaderMiddleware:
    def process_request(self, request, spider):
        request.headers["X-My-Header"] = "Hello"
        return None
```

Bật trong `settings.py`:

```python
DOWNLOADER_MIDDLEWARES = {
    "quotes_project.middlewares.CustomHeaderMiddleware": 543,
}
```

### 19.2. Spider Middleware

Nằm giữa Engine và Spider.

```text
Engine -> Spider Middleware -> Spider -> Spider Middleware -> Engine
```

Dùng khi cần post-process output của spider callback, xử lý exception, thay đổi item/request trước khi về Engine.

Người mới thường chưa cần tự viết spider middleware.

---

## 20. Cấu hình lịch sự khi crawl

Trong `settings.py`:

```python
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
```

Gợi ý thực tế:

- Đọc Terms of Service và robots.txt của website.
- Không crawl quá nhanh.
- Cache hoặc lưu trạng thái nếu crawl lớn.
- Không crawl dữ liệu cá nhân/nhạy cảm nếu không có căn cứ hợp pháp.
- Với website render bằng JavaScript, Scrapy thuần có thể không thấy dữ liệu; cần tìm API thật trong DevTools hoặc dùng công cụ render phù hợp.

---

## 21. Debug Scrapy

### 21.1. Dùng Scrapy shell trước

```bash
scrapy shell "https://quotes.toscrape.com/"
```

Test:

```python
response.status
response.url
response.css("div.quote").get()
response.css("span.text::text").getall()
```

### 21.2. Giảm log noise

```bash
scrapy crawl quotes -s LOG_LEVEL=INFO
```

Hoặc trong `settings.py`:

```python
LOG_LEVEL = "INFO"
```

### 21.3. Lưu log ra file

```bash
scrapy crawl quotes -s LOG_FILE=logs/quotes.log
```

### 21.4. Kiểm tra request thật Scrapy tải

```bash
scrapy fetch "https://quotes.toscrape.com/"
```

### 21.5. Dùng `parse`

```bash
scrapy parse "https://quotes.toscrape.com/" --spider=quotes
```

---

## 22. Cấu trúc project nên dùng khi lớn hơn

```text
quotes_project/
├── scrapy.cfg
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── logs/
└── quotes_project/
    ├── __init__.py
    ├── items.py
    ├── middlewares.py
    ├── pipelines.py
    ├── settings.py
    ├── utils/
    │   ├── __init__.py
    │   └── text.py
    └── spiders/
        ├── __init__.py
        ├── quotes.py
        └── books.py
```

Ví dụ `requirements.txt`:

```text
scrapy
itemadapter
```

---

## 23. Mapping Scrapy với tư duy Data Engineering

| Scrapy                   | Data Engineering tương ứng     |
| ------------------------ | --------------------------------- |
| Spider                   | Extract job                       |
| Request queue/Scheduler  | Orchestration/queue mini          |
| Downloader               | Source connector                  |
| Item                     | Raw record/schema                 |
| Pipeline                 | Transform/validate/load mini step |
| Feed Export              | Raw file landing                  |
| SQLite/Postgres pipeline | Load to storage                   |
| Stats/logs               | Observability                     |
| JOBDIR                   | Resume state cho crawl dài       |

Nếu làm production, bạn có thể xem một crawl run như một batch:

```text
crawl_runs
  -> crawl_tasks/request logs
  -> raw_snapshots/html
  -> parsed_items
  -> load_batches
```

---

## 24. Checklist crawl một website mới

1. Mở website bằng browser.
2. Kiểm tra dữ liệu nằm trong HTML hay gọi API riêng bằng DevTools Network.
3. Kiểm tra robots.txt và điều khoản sử dụng.
4. Test URL trong Scrapy shell.
5. Viết selector cho 1 item.
6. Viết spider parse list page.
7. Viết spider follow detail/next page.
8. Định nghĩa Item schema.
9. Viết pipeline clean/validate/deduplicate.
10. Export JSONL trước để kiểm tra.
11. Sau đó mới lưu DB.
12. Thêm delay/concurrency/autothrottle.
13. Thêm logging và thống kê.
14. Chạy thử ít trang trước.
15. Chạy toàn bộ khi đã ổn.

---

## 25. Lỗi thường gặp

### 25.1. Spider không chạy vì sai tên

Chạy:

```bash
scrapy list
```

Kiểm tra `name` trong spider.

---

### 25.2. Selector trả về `None`

Nguyên nhân thường gặp:

- HTML khác browser vì dữ liệu render bằng JavaScript.
- Sai CSS/XPath.
- Website trả page chống bot/captcha/login.
- Bạn đang chọn nhầm element.

Cách xử lý:

```bash
scrapy shell "URL"
```

Sau đó test từng selector nhỏ.

---

### 25.3. Không follow trang tiếp theo

Kiểm tra:

```python
next_page = response.css("li.next a::attr(href)").get()
print(next_page)
```

Nếu link tương đối, dùng:

```python
yield response.follow(next_page, callback=self.parse)
```

---

### 25.4. Pipeline không chạy

Kiểm tra đã bật trong `settings.py` chưa:

```python
ITEM_PIPELINES = {
    "quotes_project.pipelines.CleanQuotePipeline": 300,
}
```

Kiểm tra đường import class đúng chưa.

---

### 25.5. Item bị mất sau pipeline

Trong `process_item`, phải `return item`.

```python
def process_item(self, item):
    # sửa item
    return item
```

---

### 25.6. Append JSON bị lỗi

Không nên append vào `.json` bằng `-o` nhiều lần. Dùng JSON Lines:

```bash
scrapy crawl quotes -o data/quotes.jsonl
```

Hoặc overwrite JSON:

```bash
scrapy crawl quotes -O data/quotes.json
```

---

## 26. Bài tập thực hành

### Bài 1: Crawl quotes cơ bản

Mục tiêu:

- Crawl `https://quotes.toscrape.com/`.
- Lấy `text`, `author`, `tags`, `source_url`.
- Follow tất cả page.
- Xuất `data/quotes.jsonl`.

Lệnh chạy:

```bash
scrapy crawl quotes -O data/quotes.jsonl
```

---

### Bài 2: Thêm pipeline clean text

Yêu cầu:

- Xoá dấu ngoặc kép cong `“”`.
- Strip khoảng trắng.
- Lowercase tags.

---

### Bài 3: Thêm pipeline chống trùng

Yêu cầu:

- Nếu `(text, author)` đã xuất hiện, drop item.

---

### Bài 4: Crawl list -> detail

Mục tiêu:

- Crawl `https://books.toscrape.com/`.
- Từ list page, follow detail page.
- Lấy title, price, availability, url.

---

## 27. Tóm tắt cực ngắn

```text
1. startproject tạo khung project.
2. genspider tạo spider trong spiders/.
3. Spider tạo Request và parse Response.
4. Spider yield Item hoặc Request mới.
5. Item đi qua Pipeline theo thứ tự trong settings.py.
6. Feed Export hoặc Pipeline lưu dữ liệu ra file/database.
7. settings.py là nơi bật/tắt pipeline, middleware, delay, export.
```

Lệnh nhớ nhất:

```bash
scrapy startproject myproject
cd myproject
scrapy genspider example example.com
scrapy shell "https://example.com"
scrapy crawl example -O data/items.jsonl
scrapy list
scrapy settings --get BOT_NAME
```

---

## 28. Nguồn đã đối chiếu

### Docs chính thức

- Scrapy documentation: https://docs.scrapy.org/en/latest/
- Installation guide: https://docs.scrapy.org/en/latest/intro/install.html
- Scrapy tutorial: https://docs.scrapy.org/en/latest/intro/tutorial.html
- Command line tool: https://docs.scrapy.org/en/latest/topics/commands.html
- Spiders: https://docs.scrapy.org/en/latest/topics/spiders.html
- Selectors: https://docs.scrapy.org/en/latest/topics/selectors.html
- Items: https://docs.scrapy.org/en/latest/topics/items.html
- Item Pipeline: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
- Feed exports: https://docs.scrapy.org/en/latest/topics/feed-exports.html
- Requests and Responses: https://docs.scrapy.org/en/latest/topics/request-response.html
- Settings: https://docs.scrapy.org/en/latest/topics/settings.html
- Architecture overview: https://docs.scrapy.org/en/latest/topics/architecture.html
- Downloader Middleware: https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
- Release notes: https://docs.scrapy.org/en/latest/news.html

### Bài viết mới dùng để tham khảo thêm

- Scrapfly, “Web Scraping With Scrapy: The Complete Guide in 2026”, 10/04/2026: https://scrapfly.io/blog/posts/web-scraping-with-scrapy
- GroupBWT, “Scrapy Framework for Large-Scale Web Scraping: Architecture and Best Practices”, 13/03/2026: https://groupbwt.com/blog/scrapy-tutorial/
- Medium, “Scrapy Data Export & Storage: Save Your Data Like a Pro”, 2025/2026: https://medium.com/@mikram2015/scrapy-data-export-storage-save-your-data-like-a-pro-98bf6180b7c2
