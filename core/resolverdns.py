# -*- coding: utf-8 -*-
import datetime, sys, ssl
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
from platformcode import logger
import requests
from core import scrapertools
from core import db

if 'PROTOCOL_TLS' in ssl.__dict__:
    protocol = ssl.PROTOCOL_TLS
elif 'PROTOCOL_SSLv23' in ssl.__dict__:
    protocol = ssl.PROTOCOL_SSLv23
else:
    protocol = ssl.PROTOCOL_SSLv3

current_date = datetime.datetime.now()


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
        self.ssl_context = CustomContext(protocol, domain)
        self.CF = CF  # if cloudscrape is in action
        self.cipherSuite = kwargs.pop('cipherSuite', DEFAULT_CIPHERS)

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    def flushDns(self, request, domain, **kwargs):
        del db['dnscache'][domain]
        return self.send(request, flushedDns=True, **kwargs)

    def getIp(self, domain):
        cache = db['dnscache'].get(domain, {})
        ip = None
        if type(cache) != dict or (cache.get('datetime') and
                                   current_date - cache.get('datetime') > datetime.timedelta(hours=1)):
            cache = None

        if not cache:  # not cached
            try:
                ip = doh.query(domain)[0]
                logger.info('Query DoH: ' + domain + ' = ' + str(ip))
                # IPv6 address
                if ':' in ip:
                    ip = '[' + ip + ']'
                self.writeToCache(domain, ip)
            except Exception:
                logger.error('Failed to resolve hostname, fallback to normal dns')
                import traceback
                logger.error(traceback.format_exc())
        else:
            ip = cache.get('ip')
        logger.info('Cache DNS: ' + domain + ' = ' + str(ip))
        return ip

    def writeToCache(self, domain, ip):
        db['dnscache'][domain] = {'ip': ip, 'datetime': current_date}

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
        if not scrapertools.find_single_match(domain, '\d+\.\d+\.\d+\.\d+') and ':' not in domain:
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
                # if 400 <= ret.status_code < 500:
                #     raise Exception
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as e:
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
