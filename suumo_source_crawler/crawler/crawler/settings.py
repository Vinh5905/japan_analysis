# Scrapy settings for crawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os


def env_int(name, default, minimum=0):
    """Read and validate a numeric runtime knob before a crawl starts."""
    value = int(os.environ.get(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def env_float(name, default, minimum=0):
    """Read and validate a throttling value from the runtime environment."""
    value = float(os.environ.get(name, str(default)))
    if not minimum <= value < float("inf"):
        raise ValueError(f"{name} must be finite and >= {minimum}")
    return value


BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "crawler (+http://www.yourdomain.com)"

# Obey robots.txt rules. This crawler targets a fixed public listing URL and keeps
# request volume low through delay/concurrency settings.
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
CONCURRENT_REQUESTS = env_int("SUUMO_CONCURRENT_REQUESTS", 2, minimum=1)
CONCURRENT_REQUESTS_PER_DOMAIN = env_int("SUUMO_CONCURRENT_REQUESTS_PER_DOMAIN", 1, minimum=1)

# AutoThrottle owns request pacing. DOWNLOAD_DELAY is intentionally unset because
# Scrapy treats it as a fixed minimum delay even when AutoThrottle is enabled.
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = env_float("SUUMO_AUTOTHROTTLE_START_DELAY", 3)
AUTOTHROTTLE_MAX_DELAY = env_float("SUUMO_AUTOTHROTTLE_MAX_DELAY", 15)
AUTOTHROTTLE_TARGET_CONCURRENCY = env_float("SUUMO_AUTOTHROTTLE_TARGET_CONCURRENCY", 0.5)
if AUTOTHROTTLE_MAX_DELAY < AUTOTHROTTLE_START_DELAY:
    raise ValueError("SUUMO_AUTOTHROTTLE_MAX_DELAY must be >= start delay")
if AUTOTHROTTLE_TARGET_CONCURRENCY <= 0:
    raise ValueError("SUUMO_AUTOTHROTTLE_TARGET_CONCURRENCY must be > 0")
AUTOTHROTTLE_DEBUG = False

# Keep SUUMO responses on the desktop HTML layout that current selectors parse.
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}
FAKE_USER_AGENT_BROWSERS = ["Chrome"]
FAKE_USER_AGENT_OS = ["Windows", "Mac OS X", "Linux"]
FAKE_USER_AGENT_PLATFORMS = ["desktop"]
FAKE_USER_AGENT_MIN_VERSION = 120.0
FAKE_USER_AGENT_FALLBACK = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

# Parser reads pending crawl_tasks and writes compressed JSON arrays to suumo/data.
SUUMO_PAGE_TASK_LIMIT = env_int("SUUMO_PAGE_TASK_LIMIT", 0)
SUUMO_PAGE_BATCH_SIZE = env_int("SUUMO_PAGE_BATCH_SIZE", 100, minimum=1)
SUUMO_PAGE_BATCH_SECONDS = env_int("SUUMO_PAGE_BATCH_SECONDS", 300, minimum=1)
SUUMO_SOURCE_BASE_URL = os.environ.get("SUUMO_SOURCE_BASE_URL", "https://suumo.jp")
SUUMO_SEARCH_URL = os.environ.get("SUUMO_SEARCH_URL") or (
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/"
    "?ar=060&bs=040&ta=27&sc=27123&cb=0.0&ct=9999999&et=9999999"
    "&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="
)

# HTML crawler reads every new tmp link by default. Set SUUMO_HTML_LINK_LIMIT=1
# when only one page should be fetched for a local smoke check.
SUUMO_HTML_LINKS_FILE = os.environ.get("SUUMO_HTML_LINKS_FILE", "tmp/suumo_links.txt")
SUUMO_HTML_LINK_LIMIT = env_int("SUUMO_HTML_LINK_LIMIT", 0)
SUUMO_SOURCE_ID = env_int("SUUMO_SOURCE_ID", 1, minimum=1)
SUUMO_RUN_CREATED_BY = os.environ.get("SUUMO_RUN_CREATED_BY", "schedule")

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "crawler.middlewares.CrawlerSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "crawler.middlewares.RandomUserAgentMiddleware": 400,
    "crawler.middlewares.SuumoHtmlTaskClaimMiddleware": 410,
    "crawler.vpn_accounting.VpnRequestAccounting": 950,
}

# Enable lifecycle notifications and summary collection. The extension becomes
# a no-op for Telegram delivery when its two environment variables are absent.
EXTENSIONS = {
    "crawler.telegram_extension.TelegramNotificationExtension": 500,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "crawler.pipelines.CrawlerPipeline": 300,
#}

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
