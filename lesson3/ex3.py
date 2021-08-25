from bs4 import BeautifulSoup as bs
from pprint import pprint
from pymongo import MongoClient
import re
import requests


# Класс парсера который работает с Mongo
class ParsingJob:

    def __init__(self, ip, port, db_name, collection_name):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
        }
        self.link_hh = 'https://hh.ru/search/vacancy'
        self.link_superjob = 'https://www.superjob.ru/vacancy/search/'

        self.mongodb = MongoClient(ip, port)
        self.db = self.mongodb[db_name]
        self.collection = self.db[collection_name]

    # Максимальная ЗП
    def print_salary_max_gt(self, salary):
        objects = self.collection.find({'salary_max': {'$gt': salary}})
        for obj in objects:
            pprint(obj)

    # Минимальная ЗП
    def print_salary_min_gt(self, salary):
        objects = self.collection.find({'salary_min': {'$gt': salary}})
        for obj in objects:
            pprint(obj)

    # Вызыватель суперпарсера
    def search_job(self, vacancy):
        self.parser_hh(vacancy)
        self.parser_superjob(vacancy)

    # Проверка на существование вакансии для исключения дублей
    def is_exists(self, name_tags, field):
        return bool(self.collection.find_one({name_tags: {"$in": [field]}}))

    # Парсер HH по страницам
    def parser_hh(self, vacancy):
        params = {
            'text': vacancy,
            'page': ''
        }

        html = requests.get(self.link_hh, params=params, headers=self.headers)

        if html.ok:
            parsed_html = bs(html.text, 'html.parser')

            page_block = parsed_html.find('div', {'data-qa': 'pager-block'})
            if not page_block:
                last_page = 1
            else:
                last_page = page_block.find_all('a', {'class': 'bloko-button'})
                last_page = int(last_page[len(last_page) - 2].find('span').getText())

        for page in range(0, last_page):
            params['page'] = page
            html = requests.get(self.link_hh, params=params, headers=self.headers)

            if html.ok:
                parsed_html = bs(html.text, 'html.parser')

                vacancy_items = parsed_html.find_all('div', {'class': 'vacancy-serp-item'})
                # Здесь вызывается функция и она парсит одну страницу, потом следующую и т.д
                for item in vacancy_items:
                    vacancy = self.parser_item_hh(item)
                    if self.is_exists('vacancy_link', vacancy['vacancy_link']):
                        self.collection.update_one({'vacancy_link': vacancy['vacancy_link']}, {'$set': vacancy})
                    else:
                        self.collection.insert_one(vacancy)

    # Парсер superjob по страницам
    def parser_superjob(self, vacancy):

        params = {
            'keywords': vacancy,
            'profession_only': '1',
            'geo[c][0]': '15',
            'geo[c][1]': '1',
            'geo[c][2]': '9',
            'page': ''
        }

        html = requests.get(self.link_superjob, params=params, headers=self.headers)

        if html.ok:
            parsed_html = bs(html.text, 'html.parser')

            page_block = parsed_html.find('a', {'class': 'f-test-button-dalshe'})
        if not page_block:
            last_page = 1
        else:
            last_page = int(page_block.previous_sibling.find_all('span')[-2].getText())

        for page in range(1, last_page + 1):
            params['page'] = page
            html = requests.get(self.link_superjob, params=params, headers=self.headers)

            if html.ok:
                parsed_html = bs(html.text, 'html.parser')
                vacancy_items = parsed_html.find_all('div', {'class': 'f-test-vacancy-item'})

                for item in vacancy_items:
                    vacancy = self.parser_item_superjob(item)
                    if vacancy is not None:
                        if self.is_exists('vacancy_link', vacancy['vacancy_link']):
                            self.collection.update_one({'vacancy_link': vacancy['vacancy_link']}, {'$set': vacancy})
                        else:
                            self.collection.insert_one(vacancy)

    # Распарсивание вакансии HH Из страницы
    def parser_item_hh(self, item):

        vacancy_data = {}

        vacancy_name = item.find('a', {'data-qa': 'vacancy-serp__vacancy-title'}) \
            .getText().replace(u'\xa0', u' ')

        vacancy_data['vacancy_name'] = vacancy_name

        company_name = item.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})

        if company_name:
            company_name = company_name.getText().replace(u'\xa0', u' ')
        vacancy_data['company_name'] = company_name

        city = item.find('span', {'data-qa': 'vacancy-serp__vacancy-address'}) \
            .getText() \
            .split(', ')[0]

        vacancy_data['city'] = city

        # salary
        salary = item.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
        if not salary:
            salary_min = None
            salary_max = None
            salary_currency = None
        else:
            salary = salary.getText().replace(u'\u202f', u'')
            salary = salary.replace('–', '')
            salary = re.split(r'\s', salary)

            if salary[0] == 'до':
                salary_min = None
                salary_max = int(salary[1])
            elif salary[0] == 'от':
                salary_min = int(salary[1])
                salary_max = None
            else:
                salary_min = int(salary[0])
                salary_max = int(salary[2])

            salary_currency = salary[len(salary) - 1]

        vacancy_data['salary_min'] = salary_min
        vacancy_data['salary_max'] = salary_max
        vacancy_data['salary_currency'] = salary_currency

        vacancy_link = item.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})['href']

        vacancy_data['vacancy_link'] = vacancy_link
        vacancy_data['site'] = 'hh.ru'

        return vacancy_data

    # Распарсивание вакансий SuperJob из страницы
    def parser_item_superjob(self, item):
        vacancy_dict = {}

        # vacancy_name
        vacancy_name = item.find_all('a')
        if len(vacancy_name) > 1:
            vacancy_name = vacancy_name[-2].getText()
        else:
            vacancy_name = vacancy_name[0].getText()

        # company_name
        company_name = item.find('span', {'class': 'f-test-text-vacancy-item-company-name'})

        if company_name:
            company_name = company_name.getText()
        else:
            company_name = None

        # city
        company_location = item.find('span', {'class': 'f-test-text-company-item-location'}) \
            .findChildren()[2] \
            .getText() \
            .split(',')

        # salary
        salary = item.find('span', {'class': 'f-test-text-company-item-salary'}) \
            .findChildren()
        if not salary:
            salary_min = None
            salary_max = None
            salary_currency = None
        else:
            salary_elems = salary[0].getText().replace(u'\xa0', u' ').split(' ')
            salary_currency = salary_elems[-1]
            is_check_salary = item.find('span', {'class': 'f-test-text-company-item-salary'}).getText()
            if is_check_salary != 'По договорённости':
                is_check_salary = is_check_salary.replace(u'\xa0', u' ').split(' ', 1)
                if is_check_salary[0] == 'до' or len(salary) == 2:
                    if salary_elems[1].isdigit() and salary_elems[2].isdigit():
                        salary_min = None
                        salary_max = int(salary_elems[1] + salary_elems[2])
                    elif salary_elems[1].isdigit() and not salary_elems[2].isdigit():
                        salary_max = int(salary_elems[1])
                elif is_check_salary[0] == 'от':
                    if salary_elems[1].isdigit() and salary_elems[2].isdigit():
                        salary_min = int(salary_elems[1] + salary_elems[2])
                    elif salary_elems[1].isdigit() and not salary_elems[2].isdigit():
                        salary_min = int(salary_elems[1])
                    salary_max = None
                else:
                    if len(salary_elems) > 3:
                        if salary_elems[1].isdigit():
                            salary_min = int(salary_elems[0] + salary_elems[1])
                        else:
                            salary_min = int(salary_elems[0])
                        if salary_elems[-2].isdigit() and salary_elems[-3].isdigit():
                            salary_max = int(salary_elems[-3] + salary_elems[-2])
                        else:
                            salary_max = int(salary_elems[-2])
                    else:
                        if salary_elems[1].isdigit():
                            salary_min = int(salary_elems[0] + salary_elems[1])
                            salary_max = int(salary_elems[0] + salary_elems[1])
                        else:
                            salary_min = int(salary_elems[0])
                            salary_max = int(salary_elems[0])
            else:
                salary_min = None
                salary_max = None
                salary_currency = None

        # link
        vacancy_link = item.find_all('a')

        if len(vacancy_link) > 1:
            vacancy_link = vacancy_link[-2]['href']
        else:
            vacancy_link = vacancy_link[0]['href']

        if company_name != vacancy_name:
            vacancy_dict['vacancy_name'] = vacancy_name
            vacancy_dict['company_name'] = company_name
            vacancy_dict['city'] = company_location[0]
            vacancy_dict['salary_min'] = salary_min
            vacancy_dict['salary_max'] = salary_max
            vacancy_dict['salary_currency'] = salary_currency
            vacancy_dict['vacancy_link'] = f'https://www.superjob.ru{vacancy_link}'
            vacancy_dict['site'] = 'www.superjob.ru'
            return vacancy_dict


vacancy_db = ParsingJob('127.0.0.1', 27017, 'vacancy',
                        'vacancy_db')  # Установка соединения с Mongo и создание коллекций

# Заполнение коллекции и вывод каждый
# Каждый вызов добавляет новые вакансии, дубли заменяются
vacancy = 'Python'
vacancy_db.search_job(vacancy)
objects = vacancy_db.collection.find().limit(2)
for obj in objects:
    pprint(obj)

print(' Ниже зарплаты \n')
vacancy_db.print_salary_max_gt(300000)  # Максимальная зп
# vacancy_db.print_salary_min_gt(300000) - минимальная ЗП
