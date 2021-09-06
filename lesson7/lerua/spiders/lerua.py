import scrapy
from scrapy.http import HtmlResponse
from lesson7.lerua.items import LeruaparserItem
from scrapy.loader import ItemLoader


class LeruaSpider(scrapy.Spider):
    name = 'lerua'
    allowed_domains = ['leroymerlin.ru']
    start_urls = ['http://leroymerlin.ru/']

    def __init__(self, query, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = [f'https://leroymerlin.ru/search/?q={query}']

    def parse(self, response: HtmlResponse):
        links = response.xpath("//div[contains(@class, 'Card')]/a/@href").getall()
        next_page = response.xpath("//a[contains(@aria-label, 'Следующая страница')]/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
        for link in links:
            yield response.follow(link, callback=self.parse_ads)

    def parse_ads(self, response: HtmlResponse):
        specs = {}
        loader = ItemLoader(item=LeruaparserItem(), response=response)
        loader.add_xpath('name', '//h1/text()')
        loader.add_xpath('price', "//meta[@itemprop='price']/@content")
        loader.add_xpath('photos', "//img[@slot='thumbs']/@src")
        spec_names = response.xpath("//dt/text()").getall()
        spec_params = response.xpath("//dd/text()").getall()
        for i in range(len(spec_names)):
            spec_params[i] = spec_params[i].replace('\n', '').replace(' ', '')
            try:
                spec_params[i] = float(spec_params[i])
            except TypeError and ValueError:
                pass
            specs[spec_names[i]] = spec_params[i]
        loader.add_value('specs', specs)
        loader.add_value('url', response.url)
        yield loader.load_item()
