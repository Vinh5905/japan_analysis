# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from fake_useragent import UserAgent

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class RandomUserAgentMiddleware:
    """Assign a random browser-like User-Agent to each outgoing request."""

    def __init__(
        self,
        browsers,
        operating_systems,
        platforms,
        min_version,
        fallback_user_agent,
    ):
        """Store a configured fake-useragent generator and fallback User-Agent."""

        self.user_agent = UserAgent(
            browsers=browsers,
            os=operating_systems,
            platforms=platforms,
            min_version=min_version,
            fallback=fallback_user_agent,
        )
        self.fallback_user_agent = fallback_user_agent

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from Scrapy settings."""

        fallback_user_agent = crawler.settings.get(
            "FAKE_USER_AGENT_FALLBACK",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        )
        return cls(
            browsers=crawler.settings.getlist("FAKE_USER_AGENT_BROWSERS") or None,
            operating_systems=crawler.settings.getlist("FAKE_USER_AGENT_OS") or None,
            platforms=crawler.settings.getlist("FAKE_USER_AGENT_PLATFORMS") or None,
            min_version=crawler.settings.getfloat("FAKE_USER_AGENT_MIN_VERSION", 0.0),
            fallback_user_agent=fallback_user_agent,
        )

    def process_request(self, request):
        """Set User-Agent on the request before Scrapy sends it."""

        if request.headers.get("User-Agent"):
            return None

        # If fake-useragent cannot provide a value, keep the crawler working with fallback.
        request.headers["User-Agent"] = self.get_user_agent()
        return None

    def get_user_agent(self) -> str:
        """Return a random User-Agent, or fallback when generation fails."""

        try:
            return self.user_agent.random
        except Exception:
            return self.fallback_user_agent


class CrawlerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # matching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class CrawlerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
