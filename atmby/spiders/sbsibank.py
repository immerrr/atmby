# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from scrapy.shell import inspect_response

from six.moves.urllib.parse import urlparse, urljoin

from atmby.items import AtmbyItem

class SbsibankSpider(scrapy.Spider):
    name = "sbsibank"
    allowed_domains = ["www.sbsibank.by"]
    start_urls = [
        'https://www.sbsibank.by/atmcity.asp?dev=A'
    ]

    def parse(self, response):
        for anchor in response.xpath('//a[contains(@href, "atms.asp")]'):
            href = anchor.xpath('@href').extract_first()
            text = anchor.xpath('text()').extract_first()
            if text.lower() == u'все города':
                yield Request(callback=self.parse_all_cities,
                              url=urljoin(response.request.url, href))

    def parse_all_cities(self, response):
        for tr in response.xpath(
                '//table[@class="mainfnt"]/tr[position() > 1]'):
            texts = tr.xpath('td/*|td/text()').extract()
            yield AtmbyItem(
                city=texts[0],
                address=texts[1],
                description=texts[2],
                currencies=texts[3],
                schedule=texts[4],
                status=texts[5],
            )
