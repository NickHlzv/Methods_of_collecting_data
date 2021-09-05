from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess

from lesson6.jobparser import settings
from lesson6.jobparser.spiders.hhru import HhruSpider
from lesson6.jobparser.spiders.superjobru import SuperjobSpider

if __name__ == '__main__':

    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    process = CrawlerProcess(crawler_settings)
    process.crawl(HhruSpider)
    process.crawl(SuperjobSpider)

    process.start()
