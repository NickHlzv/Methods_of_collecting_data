# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
#from itemadapter import ItemAdapter
from pymongo import MongoClient


class JobparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongobase = client.vacanciesScrapy

    def process_item(self, item, spider):
        item['salary_min'], item['salary_max'], item['salary_cur'] = self.process_salary(item['salary'])
        del item['salary']
        item['site'] = spider.allowed_domains
        collection = self.mongobase[spider.name]
        collection.update_one({'url': item['url']}, {'$set': item}, upsert=True)
        return item

    def process_salary(self, salary):
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
