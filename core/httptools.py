# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# httptools
# --------------------------------------------------------------------------------


# Fix para error de validación del certificado del tipo:
# [downloadpage] Response code: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:661)>
# [downloadpage] Response error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:661)
# Fix desde la página: https://stackoverflow.com/questions/27835619/urllib-and-ssl-certificate-verify-failed-error
#-----------------------------------------------------------------------
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context
#-----------------------------------------------------------------------


import inspect
import cookielib
import gzip
import os
import time
import urllib
import urllib2
import urlparse
from StringIO import StringIO
from threading import Lock

from platformcode import config, logger
from platformcode.logger import WebErrorException

## Obtiene la versión del addon
__version = config.get_addon_version()

cookies_lock = Lock()

cj = cookielib.MozillaCookieJar()
ficherocookies = os.path.join(config.get_data_path(), "cookies.dat")

# Headers por defecto, si no se especifica nada
default_headers = dict()
default_headers["User-Agent"] = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3163.100 Safari/537.36"
default_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
default_headers["Accept-Language"] = "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3,it-IT,it;q=0.8"
default_headers["Accept-Charset"] = "UTF-8"
default_headers["Accept-Encoding"] = "gzip"

# Tiempo máximo de espera para downloadpage, si no se especifica nada
HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = config.get_setting('httptools_timeout', default=15)
if HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT == 0: HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = None
    
# Uso aleatorio de User-Agents, si no se especifica nada
HTTPTOOLS_DEFAULT_RANDOM_HEADERS = False

def get_user_agent():
    # Devuelve el user agent global para ser utilizado cuando es necesario para la url.
    return default_headers["User-Agent"]

def get_url_headers(url):
    domain_cookies = cj._cookies.get("." + urlparse.urlparse(url)[1], {}).get("/", {})

    if "|" in url or not "cf_clearance" in domain_cookies:
        return url

    headers = dict()
    headers["User-Agent"] = default_headers["User-Agent"]
    headers["Cookie"] = "; ".join(["%s=%s" % (c.name, c.value) for c in domain_cookies.values()])

    return url + "|" + "&".join(["%s=%s" % (h, headers[h]) for h in headers])


def load_cookies(alfa_s=False):
    cookies_lock.acquire()
    if os.path.isfile(ficherocookies):
        if not alfa_s: logger.info("Reading cookies File")
        try:
            cj.load(ficherocookies, ignore_discard=True)
        except:
            if not alfa_s: logger.info("The cookie file exists but is illegible. Deleted")
            os.remove(ficherocookies)
    cookies_lock.release()


def save_cookies(alfa_s=False):
    cookies_lock.acquire()
    if not alfa_s: logger.info("Saving cookies...")
    cj.save(ficherocookies, ignore_discard=True)
    cookies_lock.release()


load_cookies()


def downloadpage(url, post=None, headers=None, timeout=None, follow_redirects=True, cookies=True, replace_headers=False,
                 add_referer=False, only_headers=False, bypass_cloudflare=True, count_retries=0, count_retries_tot=1, random_headers=False, ignore_response_code=False, alfa_s=False, proxy=True, proxy_web=False, proxy_addr_forced=None,forced_proxy=None, proxy_retries=1):
    """
    Abre una url y retorna los datos obtenidos

    @param url: url que abrir.
    @type url: str
    @param post: Si contiene algun valor este es enviado mediante POST.
    @type post: str
    @param headers: Headers para la petición, si no contiene nada se usara los headers por defecto.
    @type headers: dict, list
    @param timeout: Timeout para la petición.
    @type timeout: int
    @param follow_redirects: Indica si se han de seguir las redirecciones.
    @type follow_redirects: bool
    @param cookies: Indica si se han de usar las cookies.
    @type cookies: bool
    @param replace_headers: Si True, los headers pasados por el parametro "headers" sustituiran por completo los headers por defecto.
                            Si False, los headers pasados por el parametro "headers" modificaran los headers por defecto.
    @type replace_headers: bool
    @param add_referer: Indica si se ha de añadir el header "Referer" usando el dominio de la url como valor.
    @type add_referer: bool
    @param only_headers: Si True, solo se descargarán los headers, omitiendo el contenido de la url.
    @type only_headers: bool
    @param random_headers: Si True, utiliza el método de seleccionar headers aleatorios.
    @type random_headers: bool
    @param ignore_response_code: Si es True, ignora el método para WebErrorException para error como el error 404 en veseriesonline, pero es un data funcional
    @type ignore_response_code: bool
    @return: Resultado de la petición
    @rtype: HTTPResponse

            Parametro               Tipo    Descripción
            ----------------------------------------------------------------------------------------------------------------
            HTTPResponse.sucess:    bool   True: Peticion realizada correctamente | False: Error al realizar la petición
            HTTPResponse.code:      int    Código de respuesta del servidor o código de error en caso de producirse un error
            HTTPResponse.error:     str    Descripción del error en caso de producirse un error
            HTTPResponse.headers:   dict   Diccionario con los headers de respuesta del servidor
            HTTPResponse.data:      str    Respuesta obtenida del servidor
            HTTPResponse.time:      float  Tiempo empleado para realizar la petición

    """

    response = {}

    # Headers por defecto, si no se especifica nada
    request_headers = default_headers.copy()

    # Headers pasados como parametros
    if headers is not None:
        if not replace_headers:
            request_headers.update(dict(headers))
        else:
            request_headers = dict(headers)

    if add_referer:
        request_headers["Referer"] = "/".join(url.split("/")[:3])
        
    if random_headers or HTTPTOOLS_DEFAULT_RANDOM_HEADERS:
        request_headers['User-Agent'] = random_useragent()

    url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    #Si la descarga requiere que se haga a través de un servicio Proxy o ProxyWeb, se prepara la url
    proxy_retries_counter = 0
    url_save = url
    post_save = post
    while proxy_retries_counter <= proxy_retries:
        # Handlers init
        handlers = [urllib2.HTTPHandler(debuglevel=False)]
        
        proxy_retries_counter += 1
        proxy_stat = ''
        proxy_addr = ''
        proxy_CF_addr = ''
        proxy_web_name = ''
        proxy_log = ''
        
        try:
            if (proxy or proxy_web) and (forced_proxy or proxy_addr_forced or channel_proxy_list(url, forced_proxy=forced_proxy)):
                import proxytools
                proxy_addr, proxy_CF_addr, proxy_web_name, proxy_log = proxytools.get_proxy_addr(url, post=post, forced_proxy=forced_proxy)
                if proxy_addr_forced and proxy_log:
                    import scrapertools
                    proxy_log = scrapertools.find_single_match(str(proxy_addr_forced), "{'http.*':\s*'(.*?)'}")
            
                if proxy and proxy_addr:
                    if proxy_addr_forced: proxy_addr = proxy_addr_forced
                    handlers.append(urllib2.ProxyHandler(proxy_addr))
                    proxy_stat = ', Proxy Direct ' + proxy_log
                elif proxy and proxy_CF_addr:
                    if proxy_addr_forced: proxy_CF_addr = proxy_addr_forced
                    handlers.append(urllib2.ProxyHandler(proxy_CF_addr))
                    proxy_stat = ', Proxy CF ' + proxy_log
                elif proxy and proxy_addr_forced:
                    proxy_addr = proxy_addr_forced
                    handlers.append(urllib2.ProxyHandler(proxy_addr))
                    proxy_stat = ', Proxy Direct ' + proxy_log
                elif proxy and not proxy_addr and not proxy_CF_addr and not proxy_addr_forced:
                    proxy = False
                    if not proxy_web_name:
                        proxy_addr, proxy_CF_addr, proxy_web_name, proxy_log = proxytools.get_proxy_addr(url, forced_proxy='Total')
                    if proxy_web_name:
                        proxy_web = True
                    else:
                        proxy_web = False
                        if proxy_addr:
                            proxy = True
                            handlers.append(urllib2.ProxyHandler(proxy_addr))
                            proxy_stat = ', Proxy Direct ' + proxy_log

                if proxy_web and proxy_web_name:
                    if post: proxy_log = '(POST) ' + proxy_log
                    url, post, headers_proxy, proxy_web_name = proxytools.set_proxy_web(url, proxy_web_name, post=post)
                    if proxy_web_name:
                        proxy_stat = ', Proxy Web ' + proxy_log
                        if headers_proxy:
                            request_headers.update(dict(headers_proxy))
                if proxy_web and not proxy_web_name:
                    proxy_web = False
                    proxy_addr, proxy_CF_addr, proxy_web_name, proxy_log = proxytools.get_proxy_addr(url, forced_proxy='Total')
                    if proxy_CF_addr:
                        proxy = True
                        handlers.append(urllib2.ProxyHandler(proxy_CF_addr))
                        proxy_stat = ', Proxy CF ' + proxy_log
                    elif proxy_addr:
                        proxy = True
                        handlers.append(urllib2.ProxyHandler(proxy_addr))
                        proxy_stat = ', Proxy Direct ' + proxy_log
        except:
            import traceback
            logger.error(traceback.format_exc())
            proxy = ''
            proxy_web = ''
            proxy_stat = ''
            proxy_addr = ''
            proxy_CF_addr = ''
            proxy_web_name = ''
            proxy_log = ''
            url = url_save
            
        # Limitar tiempo de descarga si no se ha pasado timeout y hay un valor establecido en la variable global
        if timeout is None and HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT is not None: timeout = HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT
        if timeout == 0: timeout = None

        if not alfa_s:
            logger.info("----------------------------------------------")
            logger.info("downloadpage KOD: %s" %__version)
            logger.info("----------------------------------------------")
            logger.info("Timeout: %s" % timeout)
            logger.info("URL: " + url)
            logger.info("Domain: " + urlparse.urlparse(url)[1])
            if post:
                logger.info("Request: POST" + proxy_stat)
            else:
                logger.info("Request: GET" + proxy_stat)
                logger.info("Use  Cookies: %s" % cookies)
                logger.info("Download Page: %s" % (not only_headers))
                logger.info("Cookie File: " + ficherocookies)
            logger.info("Headers:")
            for header in request_headers:
                logger.info("- %s: %s" % (header, request_headers[header]))

        # Handlers
        if not follow_redirects:
            handlers.append(NoRedirectHandler())

        if cookies:
            handlers.append(urllib2.HTTPCookieProcessor(cj))

        opener = urllib2.build_opener(*handlers)

        if not alfa_s:
            logger.info("Making Request")

        # Contador
        inicio = time.time()

        req = urllib2.Request(url, post, request_headers)

        try:
            if urllib2.__version__ == "2.4":
                import socket
                deftimeout = socket.getdefaulttimeout()
                if timeout is not None:
                    socket.setdefaulttimeout(timeout)
                handle = opener.open(req)
                socket.setdefaulttimeout(deftimeout)
            else:
                handle = opener.open(req, timeout=timeout)

        except urllib2.HTTPError, handle:
            response["sucess"] = False
            response["code"] = handle.code
            response["error"] = handle.__dict__.get("reason", str(handle))
            response["headers"] = handle.headers.dict
            if not only_headers:
                response["data"] = handle.read()
            else:
                response["data"] = ""
            response["time"] = time.time() - inicio
            response["url"] = handle.geturl()

        except Exception, e:
            response["sucess"] = False
            response["code"] = e.__dict__.get("errno", e.__dict__.get("code", str(e)))
            response["error"] = e.__dict__.get("reason", str(e))
            response["headers"] = {}
            response["data"] = ""
            response["time"] = time.time() - inicio
            response["url"] = url

        else:
            response["sucess"] = True
            response["code"] = handle.code
            response["error"] = None
            response["headers"] = handle.headers.dict
            if not only_headers:
                response["data"] = handle.read()
            else:
                response["data"] = ""
            response["time"] = time.time() - inicio
            response["url"] = handle.geturl()

        if not alfa_s:
            logger.info("Finished in %.2f seconds" % (response["time"]))
            logger.info("Response sucess: %s" % (response["sucess"]))
            logger.info("Response code: %s" % (response["code"]))
            logger.info("Response error: %s" % (response["error"]))
            logger.info("Response data length: %s" % (len(response["data"])))
            logger.info("Response headers:")
        server_cloudflare = ""
        for header in response["headers"]:
            if not alfa_s:
                logger.info("- %s: %s" % (header, response["headers"][header]))
            if "cloudflare" in response["headers"][header]:
                server_cloudflare = "cloudflare"

        is_channel = inspect.getmodule(inspect.currentframe().f_back)
        # error 4xx o 5xx se lanza excepcion (menos para servidores)
        # response["code"] = 400  # linea de código para probar
        is_channel = str(is_channel).replace("/servers/","\\servers\\")  # Para sistemas operativos diferente a Windows la ruta cambia
        if type(response["code"]) ==  int and "\\servers\\" not in str(is_channel) and not ignore_response_code and not proxy_stat:
            if response["code"] > 399 and (server_cloudflare == "cloudflare" and response["code"] != 503):
                raise WebErrorException(urlparse.urlparse(url)[1])

        if cookies:
            save_cookies(alfa_s=alfa_s)

        if not alfa_s:
            logger.info("Encoding: %s" % (response["headers"].get('content-encoding')))

        if response["headers"].get('content-encoding') == 'gzip':
            if not alfa_s:
                logger.info("Decompressing...")
            data_alt = response["data"]
            try:
                response["data"] = gzip.GzipFile(fileobj=StringIO(response["data"])).read()
                if not alfa_s:
                    logger.info("Decompressed")
            except:
                if not alfa_s:
                    logger.info("Could not decompress with gzip.  Trying with zlib")
                response["data"] = data_alt
                try:
                    import zlib
                    response["data"] = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(response["data"])
                except:
                    if not alfa_s:
                        logger.info("Could not decompress with zlib")
                    response["data"] = data_alt
        

        # Anti Cloudflare
        
        if bypass_cloudflare and count_retries < count_retries_tot:
            from core.cloudflare import Cloudflare
            cf = Cloudflare(response)
            if cf.is_cloudflare:
                count_retries += 1
                if not alfa_s:
                    logger.info("CloudFlare detected, waiting %s seconds..." % cf.wait_time)
                auth_url = cf.get_url()
                if not alfa_s:
                    logger.info("Authorizing... attempt %d url: %s" % (count_retries, auth_url))
                tt = downloadpage(auth_url, headers=request_headers, replace_headers=True, count_retries=count_retries, ignore_response_code=True, count_retries_tot=count_retries_tot, proxy=proxy, proxy_web=proxy_web, forced_proxy=forced_proxy, proxy_addr_forced=proxy_addr_forced, alfa_s=alfa_s)
                if tt.code == 403:
                    tt = downloadpage(url, headers=request_headers, replace_headers=True, count_retries=count_retries, ignore_response_code=True, count_retries_tot=count_retries_tot, proxy=proxy, proxy_web=proxy_web, forced_proxy=forced_proxy, proxy_addr_forced=proxy_addr_forced, alfa_s=alfa_s)
                if tt.sucess:
                    if not alfa_s:
                        logger.info("Correct authorization, downloading page")
                    resp = downloadpage(url=response["url"], post=post, headers=headers, timeout=timeout,
                                        follow_redirects=follow_redirects, count_retries=count_retries, 
                                        cookies=cookies, replace_headers=replace_headers, add_referer=add_referer, proxy=proxy, proxy_web=proxy_web, count_retries_tot=count_retries_tot, forced_proxy=forced_proxy, proxy_addr_forced=proxy_addr_forced, alfa_s=alfa_s)
                    response["sucess"] = resp.sucess
                    response["code"] = resp.code
                    response["error"] = resp.error
                    response["headers"] = resp.headers
                    response["data"] = resp.data
                    response["time"] = resp.time
                    response["url"] = resp.url
                else:
                    if not alfa_s:
                        logger.info("Unable to authorize")
                        logger.info("try to use CloudScrape")
                        try:
                            from lib import cloudscraper
                            scraper = cloudscraper.CloudScraper()
                            data = scraper.get(url).content
                            response["data"] = data
                        except:
                            logger.info("Unable to Scrape")
    
        # Si hay errores usando un Proxy, se refrescan el Proxy y se reintenta el número de veces indicado en proxy_retries
        try:
            if ', Proxy Web' in proxy_stat:
                response["data"] = proxytools.restore_after_proxy_web(response["data"], proxy_web_name, url_save)
                if response["data"] == 'ERROR':
                    response['sucess'] = False
            
            if proxy_stat and response['sucess'] == False and proxy_retries_counter <= proxy_retries and count_retries_tot > 1:
                if ', Proxy Direct' in proxy_stat:
                    proxytools.get_proxy_list_method(proxy_init='ProxyDirect')
                elif ', Proxy CF' in proxy_stat:
                    proxytools.get_proxy_list_method(proxy_init='ProxyCF')
                    url = url_save
                elif ', Proxy Web' in proxy_stat:
                    proxytools.get_proxy_list_method(proxy_init='ProxyWeb')
                    url = url_save
                    post = post_save
            else:
                break
        except:
            import traceback
            logger.error(traceback.format_exc())
            break

    return type('HTTPResponse', (), response)


def random_useragent():
    """
    Based on code from https://github.com/theriley106/RandomHeaders
    
    Python Method that generates fake user agents with a locally saved DB (.csv file).

    This is useful for webscraping, and testing programs that identify devices based on the user agent.
    """
    
    import random

    UserAgentPath = os.path.join(config.get_runtime_path(), 'tools', 'UserAgent.csv')
    if os.path.exists(UserAgentPath):
        UserAgentIem = random.choice(list(open(UserAgentPath))).strip()
        if UserAgentIem:
            return UserAgentIem
    
    return default_headers["User-Agent"]
    
    
def channel_proxy_list(url, forced_proxy=None):
    import base64
    import ast
    import scrapertools
    
    try:
        proxy_channel_bloqued_str = base64.b64decode(config.get_setting('proxy_channel_bloqued')).decode('utf-8')
        proxy_channel_bloqued = dict()
        proxy_channel_bloqued = ast.literal_eval(proxy_channel_bloqued_str)
    except:
        logger.debug('Proxytools not initialized correctly')
        return False

    if not url.endswith('/'):
        url += '/'
    if scrapertools.find_single_match(url, '(?:http.*:\/\/)?([^\?|\/]+)(?:\?|\/)') in proxy_channel_bloqued:
        if forced_proxy:
            return True
        if 'ON' in proxy_channel_bloqued[scrapertools.find_single_match(url, '(?:http.*:\/\/)?([^\?|\/]+)(?:\?|\/)')]:
            return True
    
    return False


class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302
    

