# -*- coding: utf-8 -*-
import os, sys, ssl
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
if PY3:
    import urllib.parse as urlparse
    import _ssl
    DEFAULT_CIPHERS = _ssl._DEFAULT_CIPHERS
else:
    import urlparse
    DEFAULT_CIPHERS = ssl._DEFAULT_CIPHERS

from lib.requests_toolbelt.adapters import host_header_ssl
from lib import doh
from platformcode import logger, config
import requests
from core import scrapertools

try:
    import _sqlite3 as sql
except:
    import sqlite3 as sql

db = os.path.join(config.get_data_path(), 'kod_db.sqlite')
if 'PROTOCOL_TLS' in ssl.__dict__:
    protocol = ssl.PROTOCOL_TLS
elif 'PROTOCOL_SSLv23' in ssl.__dict__:
    protocol = ssl.PROTOCOL_SSLv23
else:
    protocol = ssl.PROTOCOL_SSLv3


class CustomContext(ssl.SSLContext):
    def __init__(self, protocol, hostname, *args, **kwargs):
        self.hostname = hostname
        if PY3:
            super(CustomContext, self).__init__()
        else:
            super(CustomContext, self).__init__(protocol)
        self.verify_mode = ssl.CERT_NONE

    def wrap_socket(self, *args, **kwargs):
        kwargs['server_hostname'] = self.hostname
        self.verify_mode = ssl.CERT_NONE
        return super(CustomContext, self).wrap_socket(*args, **kwargs)


class CipherSuiteAdapter(host_header_ssl.HostHeaderSSLAdapter):

    def __init__(self, domain, CF=False, *args, **kwargs):
        self.conn = sql.connect(db)
        self.cur = self.conn.cursor()
        self.ssl_context = CustomContext(protocol, domain)
        self.CF = CF  # if cloudscrape is in action
        self.cipherSuite = kwargs.pop('cipherSuite', DEFAULT_CIPHERS)

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    def flushDns(self, request, domain, **kwargs):
        self.cur.execute('delete from dnscache where domain=?', (domain,))
        self.conn.commit()
        return self.send(request, flushedDns=True, **kwargs)

    def getIp(self, domain):
        ip = None
        try:
            self.cur.execute('select ip from dnscache where domain=?', (domain,))
            ip = self.cur.fetchall()[0][0]
            logger.info('Cache DNS: ' + domain + ' = ' + str(ip))
        except:
            pass
        if not ip:  # not cached
            try:
                ip = doh.query(domain)[0]
                logger.info('Query DoH: ' + domain + ' = ' + str(ip))
                self.writeToCache(domain, ip)
            except Exception:
                logger.error('Failed to resolve hostname, fallback to normal dns')
                import traceback
                logger.error(traceback.print_exc())
        return ip

    def writeToCache(self, domain, ip):
        try:
            self.cur.execute('insert into dnscache values(?,?)', (domain, ip))
        except:
            self.cur.execute("""CREATE TABLE IF NOT EXISTS dnscache(
                    "domain"	TEXT NOT NULL UNIQUE,
                    "ip"	TEXT NOT NULL,
                    PRIMARY KEY("domain")
                );""")
        self.conn.commit()

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)

    def send(self, request, flushedDns=False, **kwargs):
        try:
            parse = urlparse.urlparse(request.url)
        except:
            raise requests.exceptions.InvalidURL
        if parse.netloc:
            domain = parse.netloc
        else:
            raise requests.exceptions.URLRequired
        if not scrapertools.find_single_match(domain, '\d+\.\d+\.\d+\.\d+'):
            ip = self.getIp(domain)
        else:
            ip = None
        if ip:
            self.ssl_context = CustomContext(protocol, domain)
            if self.CF:
                self.ssl_context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
            self.ssl_context.set_ciphers(self.cipherSuite)
            self.init_poolmanager(self._pool_connections, self._pool_maxsize, block=self._pool_block)
            realUrl = request.url

            if request.headers:
                request.headers["Host"] = domain
            else:
                request.headers = {"Host": domain}
            ret = None
            tryFlush = False

            parse = list(parse)
            parse[1] = ip
            request.url = urlparse.urlunparse(parse)
            try:
                ret = super(CipherSuiteAdapter, self).send(request, **kwargs)
            except Exception as e:
                logger.info('Request for ' + domain + ' with ip ' + ip + ' failed')
                logger.info(e)
                # if 'SSLError' in str(e):
                #     # disabilito
                #     config.set_setting("resolver_dns", False)
                #     request.url = realUrl
                #     ret = super(CipherSuiteAdapter, self).send(request, **kwargs)
                # else:
                tryFlush = True
            if tryFlush and not flushedDns:  # re-request ips and update cache
                logger.info('Flushing dns cache for ' + domain)
                return self.flushDns(request, domain, **kwargs)
            ret.url = realUrl
        else:
            ret = super(host_header_ssl.HostHeaderSSLAdapter, self).send(request, **kwargs)
        return ret
