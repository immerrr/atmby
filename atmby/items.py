# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AtmbyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    city = scrapy.Field()
    address = scrapy.Field()
    description = scrapy.Field()
    currencies = scrapy.Field()
    schedule = scrapy.Field()
    status = scrapy.Field()
