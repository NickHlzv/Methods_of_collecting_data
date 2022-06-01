from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from lesson7.lerua.spiders.lerua import LeruaSpider
from lesson7.lerua import settings
query = 'фотообои'
if __name__ == '__main__':

    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(LeruaSpider, query=query)
    process.start()
