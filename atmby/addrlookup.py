# coding: utf-8

import re
import logging

import sqlalchemy as sa

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .geocode import get_addresses_from_yandex

logger = logging.getLogger(__name__)

Base = declarative_base()
Session = sessionmaker()

# список районов: http://globus.tut.by/regions_ar.htm

addr_tuple = namedtuple('addr_tuple',
                        'kind adm_area locality street '
                        'premise_number latitude longitude')


class Address(Base):
    __tablename__ = 'addresses'
    id = sa.Column(sa.Integer, primary_key=True)
    addr_str = sa.Column(sa.Text, index=True, nullable=False)
    description = sa.Column(sa.Text)

    kind = sa.Column(sa.String(20))
    adm_area = sa.Column(sa.String(100))
    locality = sa.Column(sa.String(100))
    street = sa.Column(sa.String(100))
    premise_number = sa.Column(sa.String(30))
    latitude = sa.Column(sa.Integer)
    longitude = sa.Column(sa.Integer)
    verified = sa.Column(sa.Boolean)


class AddressLookup(object):
    def __init__(self, url):
        self.engine = sa.create_engine(url)
        Base.metadata.create_all(self.engine)

    def _preprocess_addr_str(self, addr_str):
        if not isinstance(addr_str, unicode):
            addr_str = addr_str.decode('utf-8')
        addr_str = re.sub(ur'(\s+)аг.', ur'\1пос.', addr_str, flags=re.U)
        addr_str = re.sub(ur'\b(могилев\b.*)(\bпушкина\b)', ur'\1пушкинский',
                          addr_str, flags=re.U)
        if u'могилев' in addr_str:
            addr_str = re.sub(ur'(\s+)пушкина', ur'\1пушкинский', addr_str)
        if u'беларусь' not in addr_str:
            addr_str = u'беларусь, ' + addr_str
        return addr_str

    def set_address(self, addr_str, description, addr_tuple, session=None):
        local_session = session is None
        if local_session:
            session = Session(bind=self.engine)

        session.add(Address(
            addr_str=addr_str, description=description,
            **addr_tuple._as_dict()))
        if local_session:
            session.commit()

    def get_address(self, addr_str, description):
        """
        :type addr_str: str
        :return: (lat, lon) tuple
        """
        preprocessed = self._preprocess_addr_str(addr_str)
        session = Session(bind=self.engine)
        entry = session.query(Address).filter(
            Address.addr_str == preprocessed
        ).first()
        if entry is None:
            fetched = self._fetch_address_from_yandex(preprocessed)
            if fetched is None:
                raise RuntimeError("Couldn't find addr: %s" % preprocessed)
            set_address
            entry = Address(
                addr_str=preprocessed,
                adm_area=fetched['adm_area'],
                locality=fetched['locality'],
                street=fetched['street'],
                premise_number=fetched['premise_number'],
                latitude=fetched['latitude'],
                longitude=fetched['longitude'],
                verified=False,
            )
            session.add(entry)
            session.commit()
        return entry

    @staticmethod
    def _fetch_address_from_yandex(addr_str):
        addrs = get_addresses_from_yandex(addr_str)
        if not addrs:
            return None
        for addr in addrs:
            if addr['kind'] == 'house':
                return addr
        logger.error("Couldn't find kind=house address for: %s", addr_str)
        return addrs[0]
