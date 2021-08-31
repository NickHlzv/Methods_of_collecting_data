# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re


# useful for handling different item types with a single interface
from pymongo import MongoClient


class JobparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongobase = client.vacanciesScrapy

    def process_item(self, item, spider):
        if spider.name == 'hhru':
            item['salary_min'], item['salary_max'], item['salary_cur'] = self.process_salary_hh(item['salary'])
        elif spider.name == 'superjobru':
            item['salary_min'], item['salary_max'], item['salary_cur'] = self.process_salary_superjob(item['salary'])
        del item['salary']
        item['site'] = spider.allowed_domains[0]
        collection = self.mongobase[spider.name]
        collection.update_one({'url': item['url']}, {'$set': item}, upsert=True)
        return item

    def process_salary_hh(self, salary):
        salary = salary.replace('\xa0', '').split()
        salary_cur = salary[-1]
        if salary[0] == 'от' and salary[2] == 'до':
            salary_min = int(salary[1])
            salary_max = int(salary[3])
        elif len(salary) < 4 and salary[0] == 'от':
            salary_min = int(salary[1])
            salary_max = None
        elif salary[0] == 'до':
            salary_min = None
            salary_max = int(salary[1])
        else:
            salary_min = None
            salary_max = None
            salary_cur = None
        return salary_min, salary_max, salary_cur

    def process_salary_superjob(self, salary):
        index = 0
        for el in salary:
            salary[index] = el.replace('\xa0', '')
            index += 1
        if salary:
            if len(salary) > 4:
                salary_min = int(salary[0])
                salary_max = int(salary[1])
                salary_cur = salary[-2]
            elif salary[0] == 'от':
                salary_und = re.split(r'(\d+)', salary[2])
                salary_min = int(salary_und[1])
                salary_cur = salary_und[-1]
                salary_max = None
            elif salary[0] == 'до':
                salary_height = re.split(r'(\d+)', salary[2])
                salary_cur = salary_height[-1]
                salary_max = int(salary_height[1])
                salary_min = None
            elif len(salary) < 5 and salary[0].isdigit():
                salary_min = int(salary[0])
                salary_max = int(salary[0])
                salary_cur = salary[-2]
        else:
            salary_min = None
            salary_max = None
            salary_cur = None
        return salary_min, salary_max, salary_cur


