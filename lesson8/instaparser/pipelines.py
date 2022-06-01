# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
import os
from urllib.parse import urlparse
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class InstaparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongobase = client.Instagram_friends

    def process_item(self, item, spider):
        collection = self.mongobase[item['category']]
        collection.update_one({'full_data': item['full_data']}, {'$set': item}, upsert=True)
        return item


class InstagramPhotosPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['picture']:
            try:
                yield scrapy.Request(item['picture'])
            except Exception as e:
                print(e)

    def item_completed(self, results, item, info):
        if results:
            item['picture'] = [itm[1] for itm in results if itm[0]]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        return f'{item["category"]}/{item["parent_name"]}/' + os.path.basename(urlparse(request.url).path)
