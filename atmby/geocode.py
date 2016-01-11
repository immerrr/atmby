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
    collection = resp['response']['GeoObjectCollection']
    meta = collection['metaDataProperty']['GeocoderResponseMetaData']
    found_count = int(meta['found'])

    res = []
    try:
        for x in collection['featureMember']:
            item = x['GeoObject']
            item_meta = item['metaDataProperty']['GeocoderMetaData']
            lon, lat = item['Point']['pos'].split()
            kind = item_meta['kind']
            precision = item_meta['precision']
            text = item_meta['text']
            country = item_meta['AddressDetails']['Country']
            country_name = country['CountryNameCode']
            adm_area = country['AdministrativeArea']
            adm_area_name = adm_area['AdministrativeAreaName']
            try:
                subadm_area = adm_area['SubAdministrativeArea']
            except KeyError:
                subadm_area = subadm_area_name = None
                locality = adm_area['Locality']
            else:
                subadm_area_name = subadm_area['SubAdministrativeAreaName']
                locality = subadm_area['Locality']

            locality_name = locality.get('LocalityName')
            try:
                thoroughfare = locality['Thoroughfare']
            except KeyError:
                thoroughfare = thoroughfare_name = None
                premise_number = None
            else:
                thoroughfare_name = thoroughfare['ThoroughfareName']
                premise_number = (thoroughfare.get('Premise', {})
                                  .get('PremiseNumber', None))
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
                         json.dumps(collection, indent=1, ensure_ascii=False))
        raise
    return res
