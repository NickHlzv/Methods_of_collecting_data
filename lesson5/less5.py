from selenium import webdriver
from pymongo import MongoClient
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from pprint import pprint
import time

MONGO_IP = '127.0.0.1'
MONGO_PORT = 27017
MONGO_DATABASE = 'mvideo_db'

client = MongoClient(MONGO_IP, MONGO_PORT)
mongo_base = client[MONGO_DATABASE]
collection = mongo_base['new_stocks']

chrome_options = Options()
chrome_options.add_argument('start-maximized')

driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=chrome_options)

stocks = []
driver.get('https://www.mvideo.ru')
time.sleep(2)
close = driver.find_element_by_xpath("//div[@data-init='sticky']")
close.click()
time.sleep(1)
site = driver.find_element_by_tag_name('body')
for i in range(3):
    site.send_keys(Keys.PAGE_DOWN)
new_stocks_block = driver.find_element_by_xpath("//h2[contains(text(), 'Новинки')]/../../following-sibling::div")
time.sleep(0.5)
next_btn = new_stocks_block.find_element_by_xpath(".//a[contains(@class, 'next-btn')]")
cls_next_btn = next_btn.get_attribute('class')
while cls_next_btn == 'next-btn c-btn c-btn_scroll-horizontal c-btn_icon i-icon-fl-arrow-right':
    time.sleep(0.5)
    next_btn = new_stocks_block.find_element_by_xpath(".//a[contains(@class, 'next-btn')]")
    cls_next_btn = next_btn.get_attribute('class')
    time.sleep(0.5)
    next_btn.click()
stock_items = new_stocks_block.find_elements_by_xpath(".//a[contains(@class, 'fl-product-tile-title__link')]")
price_items = new_stocks_block.find_elements_by_xpath(".//span[@itemprop='price']")
index = 0
for item in stock_items:
    stock_dict = {}
    title = item.get_attribute('text').replace('\n', '').split()
    stock_dict['title'] = ' '.join(title)
    stock_dict['link'] = item.get_attribute('href')
    stocks.append(stock_dict)


# index = 0
# for price_item in price_items:
#    time.sleep(0.15)
#    price = price_item.text
#    stocks[index]['price'] = price_item.text
#    index += 1

def write_db(ip, port, db_name, collection_name, data):
    mongodb = MongoClient(ip, port)
    db = mongodb[db_name]
    collection = db[collection_name]
    for el in data:
        collection.update_one({'link': el['link']}, {'$set': el}, upsert=True)


write_db('127.0.0.1', 27017, 'stocks', 'stocks_db', stocks)
pprint(stocks)
