# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
import logging
from urllib.parse import urlparse
from decimal import Decimal

from redis import StrictRedis
from msgpack import packb, unpackb
from lxml import etree

from trytond.config import config
from trytond.cache import BaseCache
# from trytond.pool import Pool
from trytond.transaction import Transaction

logger = logging.getLogger(__name__)

__version__ = '0.4'
__all__ = ['RedisCache']


def encode_hook(o):
    from trytond.model import Model
    if isinstance(o, Decimal):
        return {
            '__decimal__': True,
            'data': str(o)
        }
    if isinstance(o, datetime.datetime):
        return {
            '__datetime__': True,
            'data': (o.year, o.month, o.day, o.hour, o.minute, o.second,
                o.microsecond)
        }
    if isinstance(o, datetime.date):
        return {
            '__date__': True,
            'data': (o.year, o.month, o.day)
        }
    if isinstance(o, datetime.time):
        return {
            '__time__': True,
            'data': (o.hour, o.minute, o.second, o.microsecond)
        }
    if isinstance(o, datetime.timedelta):
        return {
            '__timedelta__': True,
            'data': o.total_seconds()
        }
    if isinstance(o, set):
        return {
            '__set__': True,
            'data': tuple(o)
        }
    if isinstance(o, etree._Element):
        return {
            '__etree_Element__': True,
            'data': etree.tostring(o)
        }
    if isinstance(o, Model):
        return {
            '__tryton_model__': True,
            'data': str(o)
        }
    return o


def decode_hook(o):
    if '__decimal__' in o:
        return Decimal(o['data'])
    elif '__datetime__' in o:
        return datetime.datetime(*o['data'])
    elif '__date__' in o:
        return datetime.date(*o['data'])
    elif '__time__' in o:
        return datetime.time(*o['data'])
    elif '__timedelta__' in o:
        return datetime.timedelta(o['data'])
    elif '__set__' in o:
        return set(o['data'])
    elif '__etree_Element__' in o:
        return etree.fromstring(o['data'])
    elif '__tryton_model__' in o:
        model, id = o['data'].split(',')
#        return Pool().get(model)(int(id))
    return o


class RedisCache(BaseCache):
    "Redis Cache implementation for trytond"
    _client = None

    def __init__(self, name, size_limit=1024, duration=None, context=True):
        super(RedisCache, self).__init__(name, size_limit, duration, context)
        self.init_client()

    @classmethod
    def init_client(cls):
        redis_url = config.get('cache', 'uri',
            default='redis://127.0.0.1:6379/0')
        url = urlparse(redis_url)
        if cls._client is None:
            assert url.scheme == 'redis', ('invalid redis uri, it should use'
                'the redis schema')
            host = url.hostname
            port = url.port
            db = url.path.strip('/')
            cls._client = StrictRedis(host=host, port=port, db=db)

    def _namespace(self, dbname=None):
        if dbname is None:
            dbname = Transaction().database.name
        return '%s:%s' % (dbname, self._name)

    def get(self, key, default=None):        
        namespace = self._namespace()
        
        if self._name != "modelview.fields_view_get":
            key = self._key(key)

        #key = '|'.join(str(v) for v in key)
        result = self._client.hget(namespace, str(key))
        
        if result is None:
            return default
        else:
            # Maybe we should allow to configure it or avoid the dependency
            return unpackb(result, object_hook=decode_hook)

    def set(self, key, value):
        namespace = self._namespace()
        
        if self._name != "modelview.fields_view_get":
            key = self._key(key)
            
        #key = '|'.join(str(v) for v in key)
        value = packb(value, use_bin_type=True, default=encode_hook)
        self._client.hset(namespace, str(key), value)

    def clear(self, force=False):
        namespace = self._namespace()

        if self._name == "modelview.fields_view_get" and not force:
            return

        self._client.delete(namespace)

    @classmethod
    def clean(cls, dbname):
        pass

    @classmethod
    def resets(cls, dbname):
        pass
    
    @classmethod
    def sync(cls, transaction):
        pass
    
    @classmethod
    def sync_since(self, value):
        pass

    @classmethod
    def commit(cls, transaction):
        pass

    @classmethod
    def rollback(cls, transaction):
        pass

    @classmethod
    def drop(cls, dbname):
        # Ensure we have connection to redis
        # cls.init_client()
        for inst in cls._cache_instance:
            cls._client.delete(inst._namespace(dbname))

    @classmethod
    def refresh_pool(cls, transaction):
        pass
