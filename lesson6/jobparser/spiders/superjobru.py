import scrapy
from scrapy.http import HtmlResponse
from lesson6.jobparser.items import JobparserItem


class SuperjobSpider(scrapy.Spider):
    name = 'superjobru'
    allowed_domains = ['superjob.ru']
    start_urls = ['https://www.superjob.ru/vacancy/search/?keywords=python&geo%5Bt%5D%5B0%5D=4&click_from=facet',
                  'https://spb.superjob.ru/vacancy/search/?keywords=python&click_from=facet']

    def parse(self, response: HtmlResponse):
        urls = response.xpath("//div[contains(@class, 'f-test-vacancy-item')]//a[@target='_blank']/@href").getall()
        next_page = response.xpath("//a[contains(@class, 'f-test-button-dalshe')]/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
        for url in urls:
            yield response.follow(url, callback=self.vacancy_parse)

    def vacancy_parse(self, response: HtmlResponse):
        vac_name = response.xpath("//h1/text()").get()
        vac_salary = response.xpath("//h1/../span/span/span/text()").getall()
        vac_url = response.url
        item = JobparserItem(name=vac_name, salary=vac_salary, url=vac_url)
        yield item

