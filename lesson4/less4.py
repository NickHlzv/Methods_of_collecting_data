from lxml import html
import requests
from datetime import datetime
from pprint import pprint
from pymongo import MongoClient


def str_to_date(str):
    months = {'января': '01',
              'февраля': '02',
              'марта': '03',
              'апреля': '04',
              'мая': '05',
              'июня': '06',
              'июля': '07',
              'августа': '08',
              'сентября': '09',
              'октября': '10',
              'ноября': '11',
              'декабря': '12'}

    input_month = str.split()[2].lower()
    if input_month in months:
        str = str.replace(input_month, months[input_month])
        date = datetime.strptime(str, ' %H:%M %d %m %Y')
    else:
        str = str.split()[0]
        date = datetime.strptime(str, '%H:%M')
        date = date.strftime('%H:%M')
    return date


def get_news_lenta_ru():
    news = []

    link_lenta = 'https://lenta.ru/'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/92.0.4515.159 Safari/537.36 '
    }

    request = requests.get(link_lenta, headers=headers)
    root = html.fromstring(request.text)
    root.make_links_absolute(link_lenta)
    items = root.xpath('''(//section[@class="row b-top7-for-main js-top-seven"]//div[@class="first-item"]/h2 | 
                                //section[@class="row b-top7-for-main js-top-seven"]//div[@class="item"])''')
    for item in items:
        news_dict = {'title': item.xpath('./a/text()')[0].replace(u'\xa0', u' '), 'link': item.xpath('./a/@href')[0]}
        date = item.xpath('./a/time/@datetime')[0].replace(',', '')
        news_dict['time'] = str(str_to_date(date))
        news_dict['source'] = 'lenta.ru'
        news.append(news_dict)
        # pprint(news)
    return news


def get_time_and_source_mail(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/92.0.4515.159 Safari/537.36 '
    }
    under_request = requests.get(link, headers=headers)
    under_root = html.fromstring(under_request.text)
    # date = under_root.xpath('''//span[contains(@style, 'visibility: visible;')]/@datetime''')[0]
    date = under_root.xpath('''//span[contains(@class, 'js-ago')]/@datetime''')[0]
    date = datetime.strptime(date.replace('+03:00', ''), '%Y-%m-%dT%H:%M:%S')
    source = under_root.xpath('''//a[@class='link color_gray breadcrumbs__link']/@href''')[0]
    return date, source


def get_news_mail_ru():
    news = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/92.0.4515.159 Safari/537.36 '
    }

    link_mail_ru = 'https://news.mail.ru/'

    request = requests.get(link_mail_ru, headers=headers)
    root = html.fromstring(request.text)

    header_items = root.xpath('''//table[@class='daynews__inner']//a''')
    for item in header_items:
        header_news_dict = {'title': item.xpath('''.//span[contains(@class, 'photo__title')]/text()''')[0].replace(
            u'\xa0', u' '), 'link': item.xpath('./@href')[0]}
        time, header_news_dict['source'] = get_time_and_source_mail(item.xpath('./@href')[0])
        header_news_dict['time'] = str(time)
        news.append(header_news_dict)

    items = root.xpath('''//a[@class ='list__text']''')
    for item in items:
        news_dict = {'title': item.xpath('./text()')[0].replace(u'\xa0', u' '), 'link': item.xpath('./@href')[0]}
        time, news_dict['source'] = get_time_and_source_mail(item.xpath('./@href')[0])
        news_dict['time'] = str(time)
        flag = False
        for el in news:
            if el == news_dict:
                flag = True
        if not flag:
            news.append(news_dict)

    return news


def write_db(ip, port, db_name, collection_name, data):
    mongodb = MongoClient(ip, port)
    db = mongodb[db_name]
    collection = db[collection_name]
    for el in data:
        collection.update_one({'link': el['link']}, {'$set': el}, upsert=True)


pprint(get_news_lenta_ru())
pprint(get_news_mail_ru())
write_db('127.0.0.1', 27017, 'news', 'news_db', get_news_lenta_ru())
write_db('127.0.0.1', 27017, 'news', 'news_db', get_news_mail_ru())
