# coding: utf-8

import json
import logging

import requests

logger = logging.getLogger(__name__)


def get_addresses_from_yandex(geocode):
    resp = requests.get('https://geocode-maps.yandex.ru/1.x/',
                        params={'geocode': geocode,
                                'format': 'json',
                                'kind': 'house',
                                'lang': 'ru-RU'}).json()
    if 'error' in resp:
        raise RuntimeError(resp['error'])
    try:
        collection = resp['response']['GeoObjectCollection']
        meta = collection['metaDataProperty']['GeocoderResponseMetaData']
        found_count = int(meta['found'])

        res = []
        for x in collection['featureMember']:
            item = x['GeoObject']
            item_meta = item['metaDataProperty']['GeocoderMetaData']
            lon, lat = item['Point']['pos'].split()
            kind = item_meta['kind']
            precision = item_meta['precision']
            text = item_meta['text']

            to_parse = item_meta['AddressDetails']
            to_parse, country_name = _get_fields(
                to_parse, 'Country', 'CountryNameCode')
            to_parse, adm_area_name = _get_fields(
                to_parse, 'AdministrativeArea', 'AdministrativeAreaName')
            to_parse, subadm_area_name = _get_fields(
                to_parse, 'SubAdministrativeArea', 'SubAdministrativeAreaName')
            to_parse, locality_name = _get_fields(
                to_parse, 'Locality', 'LocalityName')
            to_parse, thoroughfare_name = _get_fields(
                to_parse, 'Thoroughfare', 'ThoroughfareName')
            to_parse, premise_number = _get_fields(
                to_parse, 'Premise', 'PremiseNumber')
            res.append({
                'adm_area': subadm_area_name or adm_area_name,
                'locality': locality_name,
                'street': thoroughfare_name,
                'premise_number': premise_number,
                'latitude': lat,
                'longitude': lon,
                'kind': kind,
                'precision': precision,
                'text': text
            })
    except Exception:
        logger.exception("Couldn't parse response: %s",
                         json.dumps(resp, indent=1, ensure_ascii=False))
        raise
    return res


def _get_fields(to_parse, item_name, *item_fields):
    try:
        item = to_parse[item_name]
    except KeyError:
        return (to_parse,) + (None,) * len(item_fields)
    return (item,) + tuple(item.get(field) for field in item_fields)
