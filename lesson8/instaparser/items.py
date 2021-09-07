# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaparserItem(scrapy.Item):
    # define the fields for your item here like:

    user_id = scrapy.Field()
    user_nick = scrapy.Field()
    full_name = scrapy.Field()
    picture = scrapy.Field()
    category = scrapy.Field()
    parent_name = scrapy.Field()
    full_data = scrapy.Field()
