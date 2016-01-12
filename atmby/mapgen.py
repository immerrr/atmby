
import folium
from csv import DictReader
import sys
import logging

from .items import AtmbyItem
from .addrlookup import AddressLookup

logger = logging.getLogger(__name__)

def read_items_from_csv(filename):
    with open(filename, 'r') as f:
        return [
            AtmbyItem(**d)
            for d in DictReader(f)
        ]


MINSK_COORDS = [53.902257, 27.561831]
POPUP_FMT = ('{city}, {address}<br/>{currencies}'
             '</br>{schedule}<br/>{description}')


def generate_map(dest_file, items,
                 addr_lookup_db='sqlite:///atmby-addrs.sqlite'):
    addr_lookup = AddressLookup(addr_lookup_db)

    atm_map = folium.Map(location=MINSK_COORDS)

    for i, item in enumerate(items):
        item_addr_str = '{city}, {address}'.format(**item)
        logger.info('Generating marker for item [%d/%d]: %s',
                    i + 1, len(items), item_addr_str)
        item_addr = addr_lookup.get_address(
            addr_str='{city}, {address}'.format(**item),
            description=item['description'])
        atm_map.simple_marker(
            [item_addr.latitude, item_addr.longitude],
            popup=POPUP_FMT.format(**item),
            clustered_marker=True)
    atm_map.create_map(dest_file)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s:' + logging.BASIC_FORMAT)
    (logging.getLogger('requests.packages.urllib3.connectionpool')
     .setLevel(logging.WARNING))
    items = read_items_from_csv('sbsatms.csv')
    for currency in ['BYR', 'EUR', 'USD']:
        generate_map('sbsatms_%s.html' % currency.lower(),
                     [i for i in items if currency in i['currencies']])


if __name__ == '__main__':
    sys.exit(main())
