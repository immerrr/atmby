# coding: utf-8

import json
import logging
import re

import sqlalchemy as sa

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .geocode import get_addresses_from_yandex

logger = logging.getLogger(__name__)

Base = declarative_base()
Session = sessionmaker()

# список районов: http://globus.tut.by/regions_ar.htm


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
        addr_str = _to_unicode(addr_str).lower()
        if u'беларусь' not in addr_str:
            addr_str = u'беларусь, ' + addr_str
        addr_str = re.sub(ur'\bаг.', ur'пос.', addr_str, flags=re.U)
        addr_str = re.sub(ur'\b(могилев\b.*)(\bпушкина\b)', ur'\1пушкинский',
                          addr_str, flags=re.U)
        addr_str = re.sub(ur'\b(минск\b.*)(\bаэропорт\s+минск.*\b2\b)',
                          ur'\1национальный аэропорт минск',
                          addr_str, flags=re.U)
        return addr_str

    def get_address(self, addr_str, description):
        """
        :type addr_str: str
        :return: (lat, lon) tuple
        """
        preprocessed = self._preprocess_addr_str(addr_str)
        description = _to_unicode(description)
        session = Session(bind=self.engine)
        entry = session.query(Address).filter(
            Address.addr_str == preprocessed
        ).first()
        if entry is None:
            fetched = self._fetch_address_from_yandex(
                preprocessed, description)
            if fetched is None:
                fetched = {}
            logger.info("Address %s (%s) was resolved to: %s",
                        preprocessed, description,
                        json.dumps(fetched, indent=1, ensure_ascii=False))
            entry = Address(
                addr_str=preprocessed,
                description=description,

                kind=fetched.get('kind'),
                adm_area=fetched.get('adm_area'),
                locality=fetched.get('locality'),
                street=fetched.get('street'),
                premise_number=fetched.get('premise_number'),
                latitude=fetched.get('latitude'),
                longitude=fetched.get('longitude'),
                verified=False,
            )
            session.add(entry)
            session.commit()
        return entry

    @staticmethod
    def _fetch_address_from_yandex(addr_str, description):
        addrs = get_addresses_from_yandex(addr_str)
        for addr in addrs:
            if addr['kind'] in ('house', 'airport', 'railway'):
                return addr
        addrs = get_addresses_from_yandex(addr_str + ', ' + description)
        for addr in addrs:
            if addr['kind'] in ('house', 'airport', 'railway'):
                return addr
        logger.error("Couldn't find kind=house address for: %s\n%s",
                     addr_str, json.dumps(addrs, indent=1, ensure_ascii=False))
        if not addrs:
            return None
        return addrs[0]


def _to_unicode(text, encoding='utf-8'):
    if isinstance(text, unicode):
        return text
    if isinstance(text, bytes):
        return text.decode(encoding)
    raise TypeError("Text must be unicode or bytes")
