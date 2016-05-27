from lxml import etree

from csv import DictReader
import sys
import logging
import io

from .items import AtmbyItem
from .addrlookup import AddressLookup

logger = logging.getLogger(__name__)

def read_items_from_csv(filename):
    with open(filename, 'r') as f:
        return [
            AtmbyItem(**{k: v.decode('utf-8') for k, v in d.items()})
            for d in DictReader(f)
        ]


MINSK_COORDS = [53.902257, 27.561831]
POPUP_FMT = (u'{city}, {address}<br/>{currencies}'
             '</br>{schedule}<br/>{description}')


def generate_kml(dest_file, items,
                 addr_lookup_db='sqlite:///atmby-addrs.sqlite'):
    addr_lookup = AddressLookup(addr_lookup_db)

    root = etree.Element('kml', nsmap={None: "http://www.opengis.net/kml/2.2"})
    doc = etree.SubElement(root, 'Document')
    etree.SubElement(doc, 'name').text = 'SBS ATMs ' + dest_file

    for i, item in enumerate(items):
        item_addr_str = u'{city}, {address}'.format(**item)
        logger.info('Generating marker for item [%d/%d]: %s',
                    i + 1, len(items), item_addr_str)
        item_addr = addr_lookup.get_address(
            addr_str=u'{city}, {address}'.format(**item),
            description=item['description'])

        placemark = etree.SubElement(doc, 'Placemark')
        etree.SubElement(placemark, 'name').text = (
            u'#{id} {city}, {address} ({currencies})'.format(
                id=item_addr.id, **item))
        etree.SubElement(placemark, 'description').text = etree.CDATA(
            POPUP_FMT.format(**item))
        point = etree.SubElement(placemark, 'Point')
        etree.SubElement(point, 'coordinates').text = (
            u'{longitude},{latitude}'.format(**item_addr.__dict__))
    with open(dest_file, 'w') as of:
        of.write(etree.tostring(root, encoding='utf-8', method='xml',
                                xml_declaration=True))


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s:' + logging.BASIC_FORMAT)
    (logging.getLogger('requests.packages.urllib3.connectionpool')
     .setLevel(logging.WARNING))
    items = read_items_from_csv('sbsatms.csv')
    for currency in ['BYR', 'EUR', 'USD']:
        generate_kml('sbsatms_%s.kml' % currency.lower(),
                     [i for i in items if currency in i['currencies']])


if __name__ == '__main__':
    sys.exit(main())
