from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from lesson8.instaparser.spiders.instaparser import InstaparserSpider
from lesson8.instaparser import settings

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(InstaparserSpider)

    process.start()
