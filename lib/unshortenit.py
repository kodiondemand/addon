#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, sys, json, time

if sys.version_info[0] >= 3:
    PY3 = True
    from urllib.parse import urlsplit, urlparse, parse_qs, urljoin, urlencode
    from urllib.request import urlopen
else:
    PY3 = False
    from urllib import urlencode, urlopen
    from urlparse import urlsplit, urlparse, parse_qs, urljoin

from base64 import b64decode

from core import httptools, scrapertools
from platformcode import config, logger

def find_in_text(regex, text, flags=re.IGNORECASE | re.DOTALL):
    rec = re.compile(regex, flags=flags)
    match = rec.search(text)
    if not match:
        return False
    return match.group(1)


class UnshortenIt(object):
    _adfly_regex = r'adf\.ly|j\.gs|q\.gs|u\.bb|ay\.gy|atominik\.com|tinyium\.com|microify\.com|threadsphere\.bid|clearload\.bid|activetect\.net|swiftviz\.net|briskgram\.net|activetect\.net|baymaleti\.net|thouth\.net|uclaut\.net|gloyah\.net|larati\.net|scuseami\.net'
    _linkbucks_regex = r'linkbucks\.com|any\.gs|cash4links\.co|cash4files\.co|dyo\.gs|filesonthe\.net|goneviral\.com|megaline\.co|miniurls\.co|qqc\.co|seriousdeals\.net|theseblogs\.com|theseforums\.com|tinylinks\.co|tubeviral\.com|ultrafiles\.net|urlbeat\.net|whackyvidz\.com|yyv\.co'
    _adfocus_regex = r'adfoc\.us'
    _lnxlu_regex = r'lnx\.lu'
    _shst_regex = r'sh\.st|shorte\.st|sh\.st|clkmein\.com|viid\.me|xiw34\.com|corneey\.com|gestyy\.com|cllkme\.com|festyy\.com|destyy\.com|ceesty\.com'
    _hrefli_regex = r'href\.li'
    _anonymz_regex = r'anonymz\.com'
    _shrink_service_regex = r'shrink-service\.it'
    _rapidcrypt_regex = r'rapidcrypt\.net'
    # _vcrypt_regex = r'vcrypt\.net|vcrypt\.pw'
    _linkup_regex = r'linkup\.pro|buckler.link|clicka\.cc'
    _linkhub_regex = r'linkhub\.icu'
    _swzz_regex = r'swzz\.xyz'
    _stayonline_regex = r'stayonline\.pro'
    _snip_regex = r'[0-9a-z]+snip\.|uprotector\.xyz'
    _linksafe_regex = r'linksafe\.cc'
    _protectlink_regex = r'(?:s\.)?protectlink\.stream'
    _uprot_regex = r'uprot\.net'
    # for services that only include real link inside iframe
    _simple_iframe_regex = r'cryptmango|xshield\.net|vcrypt\.club|isecure\.[a-z]+'
    # for services that only do redirects
    _simple_redirect = r'streamcrypt\.net/[^/]+|is\.gd|www\.vedere\.stream'
    _filecrypt_regex = r'filecrypt\.cc'

    listRegex = [_adfly_regex, _linkbucks_regex, _adfocus_regex, _lnxlu_regex, _shst_regex, _hrefli_regex, _anonymz_regex,
                 _shrink_service_regex, _rapidcrypt_regex, _simple_iframe_regex, _linkup_regex,
                 _swzz_regex, _stayonline_regex, _snip_regex, _linksafe_regex, _protectlink_regex, _uprot_regex, _simple_redirect,
                 ]
    folderRegex = [_filecrypt_regex, _linkhub_regex]

    _maxretries = 5

    _this_dir, _this_filename = os.path.split(__file__)
    _timeout = 10

    def unshorten(self, uri, type=None):
        code = 0
        originalUri = uri.replace('%0A', '\n')
        while True:
            uri = uri.strip()
            oldUri = uri
            domain = urlsplit(uri).netloc
            if not domain:
                return uri, "No domain found in URI!"
            had_google_outbound, uri = self._clear_google_outbound_proxy(uri)

            if re.search(self._adfly_regex, domain, re.IGNORECASE) or type == 'adfly':
                uri, code = self._unshorten_adfly(uri)
            if re.search(self._adfocus_regex, domain, re.IGNORECASE) or type == 'adfocus':
                uri, code = self._unshorten_adfocus(uri)
            if re.search(self._linkbucks_regex, domain, re.IGNORECASE) or type == 'linkbucks':
                uri, code = self._unshorten_linkbucks(uri)
            if re.search(self._lnxlu_regex, domain, re.IGNORECASE) or type == 'lnxlu':
                uri, code = self._unshorten_lnxlu(uri)
            if re.search(self._shrink_service_regex, domain, re.IGNORECASE):
                uri, code = self._unshorten_shrink_service(uri)
            if re.search(self._shst_regex, domain, re.IGNORECASE):
                uri, code = self._unshorten_shst(uri)
            if re.search(self._hrefli_regex, domain, re.IGNORECASE):
                uri, code = self._unshorten_hrefli(uri)
            if re.search(self._anonymz_regex, domain, re.IGNORECASE):
                uri, code = self._unshorten_anonymz(uri)
            if re.search(self._rapidcrypt_regex, domain, re.IGNORECASE):
                uri, code = self._unshorten_rapidcrypt(uri)
            if re.search(self._simple_iframe_regex, uri, re.IGNORECASE):
                uri, code = self._unshorten_simple_iframe(uri)
            # if re.search(self._vcrypt_regex, uri, re.IGNORECASE):
            #     uri, code = self._unshorten_vcrypt(uri)
            if re.search(self._linkup_regex, uri, re.IGNORECASE):
                uri, code = self._unshorten_linkup(uri)
            if re.search(self._swzz_regex, uri, re.IGNORECASE):
                uri, code = self._unshorten_swzz(uri)
            if re.search(self._stayonline_regex, uri, re.IGNORECASE):
                uri, code = self._unshorten_stayonline(uri)
            if re.search(self._snip_regex, uri, re.IGNORECASE):
                uri, code = self._unshorten_snip(uri)
            if re.search(self._linksafe_regex, uri, re.IGNORECASE):
                uri, code = self._unshorten_linksafe(uri)
            if re.search(self._protectlink_regex, uri, re.IGNORECASE):
                uri, code = self._unshorten_protectlink(uri)
            if re.search(self._uprot_regex, uri, re.IGNORECASE):
                uri, code = self._unshorten_uprot(uri)
            if re.search(self._simple_redirect, uri, re.IGNORECASE):
                p = httptools.downloadpage(uri)
                uri = p.url
                code = p.code

            if oldUri == uri:
                break

            logger.info(uri)

        if originalUri == uri and logger.testMode and code != 404:
            raise Exception('Not un-shortened link: ' + uri)
        return uri, code

    def expand_folder(self, uri):
        links = []
        if re.search(self._linkhub_regex, uri, re.IGNORECASE):
            links = self._unshorten_linkhub(uri)
        if re.search(self._filecrypt_regex, uri, re.IGNORECASE):
            links = self._unshorten_filecrypt(uri)
        return links

    def unwrap_30x(self, uri, timeout=10):
        def unwrap_30x(uri, timeout=10):

            domain = urlsplit(uri).netloc
            self._timeout = timeout

            try:
                # headers stop t.co from working so omit headers if this is a t.co link
                if domain == 't.co':
                    r = httptools.downloadpage(uri, timeout=self._timeout)
                    return r.url, r.code
                # p.ost.im uses meta http refresh to redirect.
                if domain == 'p.ost.im':
                    r = httptools.downloadpage(uri, timeout=self._timeout)
                    uri = re.findall(r'.*url\=(.*?)\"\.*', r.data)[0]
                    return uri, r.code

                retries = 0
                while True:
                    r = httptools.downloadpage(
                        uri,
                        timeout=self._timeout,
                        cookies=False,
                        follow_redirects=False)
                    if not r.success:
                        return uri, -1

                    if 'snip.' not in r.url and 'location' in r.headers and retries < self._maxretries:
                        r = httptools.downloadpage(
                            r.headers['location'],
                            cookies=False,
                            follow_redirects=False)
                        uri = r.url
                        retries += 1
                    else:
                        return r.url, r.code

            except Exception as e:
                return uri, str(e)

        uri, code = unwrap_30x(uri, timeout)

        if 'vcrypt' in uri and 'fastshield' in uri:
            # twince because of cookies
            httptools.downloadpage(
                uri,
                timeout=self._timeout,
                post='go=go')
            r = httptools.downloadpage(
                uri,
                timeout=self._timeout,
                post='go=go')
            return r.url, r.code

        return uri, code

    def _clear_google_outbound_proxy(self, url):
        '''
        So google proxies all their outbound links through a redirect so they can detect outbound links.
        This call strips them out if they are present.

        This is useful for doing things like parsing google search results, or if you're scraping google
        docs, where google inserts hit-counters on all outbound links.
        '''

        # This is kind of hacky, because we need to check both the netloc AND
        # part of the path. We could use urllib.parse.urlsplit, but it's
        # easier and just as effective to use string checks.
        if url.startswith("http://www.google.com/url?") or \
                url.startswith("https://www.google.com/url?"):

            qs = urlparse(url).query
            query = parse_qs(qs)

            if "q" in query:  # Google doc outbound links (maybe blogspot, too)
                return True, query["q"].pop()
            elif "url" in query:  # Outbound links from google searches
                return True, query["url"].pop()
            else:
                raise ValueError(
                    "Google outbound proxy URL without a target url ('%s')?" %
                    url)

        return False, url

    def _unshorten_adfly(self, uri):

        try:
            r = httptools.downloadpage(
                uri, timeout=self._timeout, cookies=False)
            html = r.data
            ysmm = re.findall(r"var ysmm =.*\;?", html)

            if len(ysmm) > 0:
                ysmm = re.sub(r'var ysmm \= \'|\'\;', '', ysmm[0])

                left = ''
                right = ''

                for c in [ysmm[i:i + 2] for i in range(0, len(ysmm), 2)]:
                    left += c[0]
                    right = c[1] + right

                # Additional digit arithmetic
                encoded_uri = list(left + right)
                numbers = ((i, n) for i, n in enumerate(encoded_uri) if str.isdigit(n))
                for first, second in zip(numbers, numbers):
                    xor = int(first[1]) ^ int(second[1])
                    if xor < 10:
                        encoded_uri[first[0]] = str(xor)

                decoded_uri = b64decode("".join(encoded_uri).encode())[16:-16].decode()

                if re.search(r'go\.php\?u\=', decoded_uri):
                    decoded_uri = b64decode(re.sub(r'(.*?)u=', '', decoded_uri)).decode()

                return decoded_uri, r.code
            else:
                return uri, 'No ysmm variable found'

        except Exception as e:
            return uri, str(e)

    def _unshorten_linkbucks(self, uri):
        '''
        (Attempt) to decode linkbucks content. HEAVILY based on the OSS jDownloader codebase.
        This has necessidated a license change.

        '''
        if config.is_xbmc():
            import xbmc

        r = httptools.downloadpage(uri, timeout=self._timeout)

        firstGet = time.time()

        baseloc = r.url

        if "/notfound/" in r.url or \
                "(>Link Not Found<|>The link may have been deleted by the owner|To access the content, you must complete a quick survey\.)" in r.data:
            return uri, 'Error: Link not found or requires a survey!'

        link = None

        content = r.data

        regexes = [
            r"<div id=\"lb_header\">.*?/a>.*?<a.*?href=\"(.*?)\".*?class=\"lb",
            r"AdBriteInit\(\"(.*?)\"\)",
            r"Linkbucks\.TargetUrl = '(.*?)';",
            r"Lbjs\.TargetUrl = '(http://[^<>\"]*?)'",
            r"src=\"http://static\.linkbucks\.com/tmpl/mint/img/lb\.gif\" /></a>.*?<a href=\"(.*?)\"",
            r"id=\"content\" src=\"([^\"]*)",
        ]

        for regex in regexes:
            if self.inValidate(link):
                link = find_in_text(regex, content)

        if self.inValidate(link):
            match = find_in_text(r"noresize=\"[0-9+]\" src=\"(http.*?)\"", content)
            if match:
                link = find_in_text(r"\"frame2\" frameborder.*?src=\"(.*?)\"", content)

        if self.inValidate(link):
            scripts = re.findall("(<script type=\"text/javascript\">[^<]+</script>)", content)
            if not scripts:
                return uri, "No script bodies found?"

            js = False

            for script in scripts:
                # cleanup
                script = re.sub(r"[\r\n\s]+\/\/\s*[^\r\n]+", "", script)
                if re.search(r"\s*var\s*f\s*=\s*window\['init'\s*\+\s*'Lb'\s*\+\s*'js'\s*\+\s*''\];[\r\n\s]+", script):
                    js = script

            if not js:
                return uri, "Could not find correct script?"

            token = find_in_text(r"Token\s*:\s*'([a-f0-9]{40})'", js)
            if not token:
                token = find_in_text(r"\?t=([a-f0-9]{40})", js)

            assert token

            authKeyMatchStr = r"A(?:'\s*\+\s*')?u(?:'\s*\+\s*')?t(?:'\s*\+\s*')?h(?:'\s*\+\s*')?K(?:'\s*\+\s*')?e(?:'\s*\+\s*')?y"
            l1 = find_in_text(r"\s*params\['" + authKeyMatchStr + r"'\]\s*=\s*(\d+?);", js)
            l2 = find_in_text(
                r"\s*params\['" + authKeyMatchStr + r"'\]\s*=\s?params\['" + authKeyMatchStr + r"'\]\s*\+\s*(\d+?);",
                js)

            if any([not l1, not l2, not token]):
                return uri, "Missing required tokens?"

            authkey = int(l1) + int(l2)

            p1_url = urljoin(baseloc, "/director/?t={tok}".format(tok=token))
            r2 = httptools.downloadpage(p1_url, timeout=self._timeout)

            p1_url = urljoin(baseloc, "/scripts/jquery.js?r={tok}&{key}".format(tok=token, key=l1))
            r2 = httptools.downloadpage(p1_url, timeout=self._timeout)

            time_left = 5.033 - (time.time() - firstGet)
            if config.is_xbmc():
                xbmc.sleep(max(time_left, 0) * 1000)
            else:
                time.sleep(5 * 1000)

            p3_url = urljoin(baseloc, "/intermission/loadTargetUrl?t={tok}&aK={key}&a_b=false".format(tok=token,
                                                                                                      key=str(authkey)))
            r3 = httptools.downloadpage(p3_url, timeout=self._timeout)

            resp_json = json.loads(r3.data)
            if "Url" in resp_json:
                return resp_json['Url'], r3.code

        return "Wat", "wat"

    def inValidate(self, s):
        # Original conditional:
        # (s == null || s != null && (s.matches("[\r\n\t ]+") || s.equals("") || s.equalsIgnoreCase("about:blank")))
        if not s:
            return True

        if re.search("[\r\n\t ]+", s) or s.lower() == "about:blank":
            return True
        else:
            return False

    def _unshorten_adfocus(self, uri):
        orig_uri = uri
        try:

            r = httptools.downloadpage(uri, timeout=self._timeout)
            html = r.data

            adlink = re.findall("click_url =.*;", html)

            if len(adlink) > 0:
                uri = re.sub('^click_url = "|"\;$', '', adlink[0])
                if re.search(r'http(s|)\://adfoc\.us/serve/skip/\?id\=', uri):
                    http_header = dict()
                    http_header["Host"] = "adfoc.us"
                    http_header["Referer"] = orig_uri

                    r = httptools.downloadpage(uri, headers=http_header, timeout=self._timeout)

                    uri = r.url
                return uri, r.code
            else:
                return uri, 'No click_url variable found'
        except Exception as e:
            return uri, str(e)

    def _unshorten_lnxlu(self, uri):
        try:
            r = httptools.downloadpage(uri, timeout=self._timeout)
            html = r.data

            code = re.findall('/\?click\=(.*)\."', html)

            if len(code) > 0:
                payload = {'click': code[0]}
                r = httptools.downloadpage(
                    'http://lnx.lu?' + urlencode(payload),
                    timeout=self._timeout)
                return r.url, r.code
            else:
                return uri, 'No click variable found'
        except Exception as e:
            return uri, str(e)

    def _unshorten_shst(self, uri):
        try:
            # act like a crawler
            r = httptools.downloadpage(uri, timeout=self._timeout, headers=[['User-Agent', '']])
            uri = r.url
            # html = r.data
            # session_id = re.findall(r'sessionId\:(.*?)\"\,', html)
            # if len(session_id) > 0:
            #     session_id = re.sub(r'\s\"', '', session_id[0])
            #
            #     http_header = dict()
            #     http_header["Content-Type"] = "application/x-www-form-urlencoded"
            #     http_header["Host"] = "sh.st"
            #     http_header["Referer"] = uri
            #     http_header["Origin"] = "http://sh.st"
            #     http_header["X-Requested-With"] = "XMLHttpRequest"
            #
            #     if config.is_xbmc():
            #         import xbmc
            #         xbmc.sleep(5 * 1000)
            #     else:
            #         time.sleep(5 * 1000)
            #
            #     payload = {'adSessionId': session_id, 'callback': 'c'}
            #     r = httptools.downloadpage(
            #         'http://sh.st/shortest-url/end-adsession?' +
            #         urlencode(payload),
            #         headers=http_header,
            #         timeout=self._timeout)
            #     response = r.data[6:-2].decode('utf-8')
            #
            #     if r.code == 200:
            #         resp_uri = json.loads(response)['destinationUrl']
            #         if resp_uri is not None:
            #             uri = resp_uri
            #         else:
            #             return uri, 'Error extracting url'
            #     else:
            #         return uri, 'Error extracting url'

            return uri, r.code

        except Exception as e:
            return uri, str(e)

    def _unshorten_hrefli(self, uri):
        try:
            # Extract url from query
            parsed_uri = urlparse(uri)
            extracted_uri = parsed_uri.query
            if not extracted_uri:
                return uri, 200
            # Get url status code
            r = httptools.downloadpage(
                extracted_uri,
                timeout=self._timeout,
                follow_redirects=False)
            return r.url, r.code
        except Exception as e:
            return uri, str(e)

    def _unshorten_anonymz(self, uri):
        # For the moment they use the same system as hrefli
        return self._unshorten_hrefli(uri)

    def _unshorten_shrink_service(self, uri):
        try:
            r = httptools.downloadpage(uri, timeout=self._timeout, cookies=False)
            html = r.data

            uri = re.findall(r"<input type='hidden' name='\d+' id='\d+' value='([^']+)'>", html)[0]

            from core import scrapertools
            uri = scrapertools.decodeHtmlentities(uri)

            uri = uri.replace("&sol;", "/") \
                .replace("&colon;", ":") \
                .replace("&period;", ".") \
                .replace("&excl;", "!") \
                .replace("&num;", "#") \
                .replace("&quest;", "?") \
                .replace("&lowbar;", "_")

            return uri, r.code

        except Exception as e:
            return uri, str(e)

    def _unshorten_rapidcrypt(self, uri):
        try:
            r = httptools.downloadpage(uri, timeout=self._timeout, cookies=False)
            html = r.data
            html = html.replace("'",'"')

            if 'embed' in uri:
                uri = re.findall(r'<a class="play-btn" href=(?:")?([^">]+)', html)[0]
            else:
                uri = re.findall(r'<a class="push_button blue" href=(?:")?([^">]+)', html)[0]
            return uri, r.code

        except Exception as e:
            return uri, 0

    def _unshorten_simple_iframe(self, uri):
        try:
            r = httptools.downloadpage(uri, timeout=self._timeout, cookies=False)
            html = r.data

            n_uri = re.findall(r'<iframe\s+src="([^"]+)', html)
            if not n_uri and 'Questo video è in conversione' in html:
                return uri, 404

            return n_uri[0], r.code

        except Exception as e:
            return uri, str(e)

    def _unshorten_vcrypt(self, uri):
        httptools.set_cookies({'domain': 'vcrypt.net', 'name': 'saveMe', 'value': '1'})
        httptools.set_cookies({'domain': 'vcrypt.pw', 'name': 'saveMe', 'value': '1'})
        try:
            headers = {}
            if 'myfoldersakstream.php' in uri or '/verys/' in uri:
                return uri, 0
            r = None

            if 'shield' in uri.split('/')[-2]:
                uri = decrypt_aes(uri.split('/')[-1], b"naphajU2usWUswec")
            else:
                spl = uri.split('/')
                spl[0] = 'http:'

                if 'sb/' in uri or 'akv/' in uri or 'wss/' in uri:
                    import datetime, hashlib
                    from base64 import b64encode
                    # ip = urlopen('https://api.ipify.org/').read()
                    ip = b'31.220.1.77'
                    day = datetime.date.today().strftime('%Y%m%d')
                    if PY3: day = day.encode()
                    headers = {
                        "Cookie": hashlib.md5(ip+day).hexdigest() + "=1;saveMe=1"
                    }
                    spl[3] += '1'
                    if spl[3] in ['wss1', 'sb1']:
                        spl[4] = b64encode(spl[4].encode('utf-8')).decode('utf-8')

                uri = '/'.join(spl)
                r = httptools.downloadpage(uri, timeout=self._timeout, headers=headers, follow_redirects=False, verify=False)
                if 'Wait 1 hour' in r.data:
                    uri = ''
                    logger.error('IP bannato da vcrypt, aspetta un ora')
                else:
                    uri = r.headers['location']
            return uri, r.code if r else 200
        except Exception as e:
            logger.error(e)
            return uri, 0

    def _unshorten_linkup(self, uri):
        try:
            r = None
            if '/tv/' in uri:
                uri = uri.replace('/tv/', '/tva/')
            elif 'delta' in uri:
                uri = uri.replace('/delta/', '/adelta/')
            elif '/ga/' in uri or '/ga2/' in uri:
                uri = b64decode(uri.split('/')[-1]).strip().decode()
            elif '/speedx/' in uri:
                uri = uri.replace('http://linkup.pro/speedx', 'http://speedvideo.net')
            else:
                r = httptools.downloadpage(uri, follow_redirects=True, timeout=self._timeout, cookies=False)
                uri = r.url
                link = re.findall("<iframe[^<>]*src=\\'([^'>]*)\\'[^<>]*>", r.data)
                # fix by greko inizio
                if not link:
                    link = re.findall('action="(?:[^/]+.*?/[^/]+/([a-zA-Z0-9_]+))">', r.data)
                if not link:
                    link = scrapertools.find_single_match(r.data, '\$\("a\.redirect"\)\.attr\("href",\s*"\s*(http[^"]+)')
                if link:
                    uri = link
            short = re.findall('^https?://.*?(https?://.*)', uri)
            if short:
                uri = short[0]
            if not r:
                r = httptools.downloadpage(uri, follow_redirects=False, timeout=self._timeout, cookies=False)
                uri = r.headers['location']
            if "snip." in uri:
                if 'out_generator' in uri:
                    uri = re.findall('url=(.*)$', uri)[0]
                elif '/decode/' in uri:
                    uri = httptools.downloadpage(uri, follow_redirects=True).url
            return uri, r.code

        except Exception as e:
            return uri, str(e)

    def _unshorten_linkhub(self, uri):
        try:
            r = httptools.downloadpage(uri, follow_redirect=True, timeout=self._timeout, cookies=False)
            if 'get/' in r.url:
                uri = 'https://linkhub.icu/view/' + re.search('\.\./view/([^"]+)', r.data).group(1)
                logger.info(uri)
                r = httptools.downloadpage(uri, follow_redirect=True, timeout=self._timeout, cookies=False)
            links = re.findall('<a href="(http[^"]+)', r.data)
            return links
        except Exception as e:
            return []

    def _unshorten_swzz(self, uri):
        try:
            r = httptools.downloadpage(uri)
            if r.url != uri:
                return r.url, r.code
            data = r.data
            if "link =" in data or 'linkId = ' in data:
                uri = scrapertools.find_single_match(data, 'link(?:Id)? = "([^"]+)"')
                if 'http' not in data:
                    uri = 'https:' + uri
            else:
                match = scrapertools.find_single_match(data, r'<meta name="og:url" content="([^"]+)"')
                match = scrapertools.find_single_match(data, r'URL=([^"]+)">') if not match else match

                if not match:
                    from lib import jsunpack

                    try:
                        data = scrapertools.find_single_match(data.replace('\n', ''),
                                                              r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>")
                        data = jsunpack.unpack(data)

                        logger.debug("##### play /link/ unpack ##\n%s\n##" % data)
                    except:
                        logger.debug("##### The content is yet unpacked ##\n%s\n##" % data)

                    uri = scrapertools.find_single_match(data, r'var link(?:\s)?=(?:\s)?"([^"]+)";')
                else:
                    uri = match
            if uri.startswith('/'):
                uri = "http://swzz.xyz" + uri
                if not "vcrypt" in data:
                    uri = httptools.downloadpage(data).data
            return uri, r.code
        except Exception as e:
            return uri, str(e)

    def _unshorten_stayonline(self, uri):
        # from core.support import dbg;dbg()
        try:
            id = uri.split('/')[-2]
            reqUrl = 'https://stayonline.pro/ajax/linkView.php'
            p = urlencode({"id": id, "ref": ""})
            time.sleep(1)
            r = httptools.downloadpage(reqUrl, post=p, headers={'Referer': uri})
            data = r.data
            try:
                import json
                uri = json.loads(data)['data']['value']
            except:
                uri = scrapertools.find_single_match(data, r'"value"\s*:\s*"([^"]+)"')
                uri = httptools.downloadpage(uri, only_headers=True).url
            return uri, r.code
        except Exception as e:
            return uri, str(e)

    def _unshorten_snip(self, uri):
        if 'out_generator' in uri:
            new_uri = re.findall('url=(.*)$', uri)[0]
            if not new_uri.startswith('http'):
                new_uri = httptools.downloadpage(uri, follow_redirects=False).headers['Location']
            uri = new_uri
        if '/decode/' in uri:
            uri = decrypt_aes(uri.split('/')[-1], b"whdbegdhsnchdbeh")

            # scheme, netloc, path, query, fragment = urlsplit(uri)
            # splitted = path.split('/')
            # splitted[1] = 'outlink'
            # r = httptools.downloadpage(uri, follow_redirects=False, post={'url': splitted[2]})
            # if 'location' in r.headers and r.headers['location']:
            #     new_uri = r.headers['location']
            # else:
            #     r = httptools.downloadpage(scheme + '://' + netloc + "/".join(splitted) + query + fragment,
            #                                follow_redirects=False, post={'url': splitted[2]})
            #     if 'location' in r.headers and r.headers['location']:
            #         new_uri = r.headers['location']
            # if new_uri and new_uri != uri:
            #     uri = new_uri
        return uri, 200

    def _unshorten_linksafe(self, uri):
        return b64decode(uri.split('?url=')[-1]).decode(), 200

    def _unshorten_protectlink(self, uri):
        if '?data=' in uri:
            return b64decode(uri.split('?data=')[-1]).decode(), 200
        else:
            return httptools.downloadpage(uri, only_headers=True, follow_redirects=False).headers.get('location', uri), 200

    def _unshorten_uprot(self, uri):
        for link in scrapertools.find_multiple_matches(httptools.downloadpage(uri, cloudscraper=True).data, '<a[^>]+href="([^"]+)'):
            if link.startswith('https://maxstream.video') or link.startswith('https://uprot.net') and link != uri:
                return link, 200
        return uri, 200

    def _unshorten_filecrypt(self, uri):
        import sys
        if sys.version_info[0] >= 3:
            from concurrent import futures
        else:
            from concurrent_py2 import futures
        links = []
        try:
            fc = FileCrypt(uri)
            # links = [fc.unshorten(f[2]) for f in fc.list_files()]
            with futures.ThreadPoolExecutor() as executor:
                unshList = [executor.submit(fc.unshorten, f[2]) for f in fc.list_files()]
                for link in futures.as_completed(unshList):
                    links.append(link.result())
        except:
            import traceback
            logger.error(traceback.format_exc())
        return links


def decrypt_aes(text, key):
    try:
        from Cryptodome.Cipher import AES
    except:
        from Crypto.Cipher import AES

    text = text.replace("_ppl_", "+").replace("_eqq_", "=").replace("_sll_", "/")
    iv = b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
    decoded = b64decode(text)
    decoded = decoded + b'\0' * (len(decoded) % 16)
    crypt_object = AES.new(key, AES.MODE_CBC, iv)
    decrypted = b''
    for p in range(0, len(decoded), 16):
        decrypted += crypt_object.decrypt(decoded[p:p + 16]).replace(b'\0', b'')
    return decrypted.decode('ascii')

def unwrap_30x_only(uri, timeout=10):
    unshortener = UnshortenIt()
    uri, status = unshortener.unwrap_30x(uri, timeout=timeout)
    return uri, status


def unshorten_only(uri, type=None, timeout=10):
    unshortener = UnshortenIt()
    uri, status = unshortener.unshorten(uri, type=type)
    return uri, status


def unshorten(uri, type=None, timeout=10):
    unshortener = UnshortenIt()
    # uri, status = unshortener.unwrap_30x(uri, timeout=timeout)
    uri, status = unshortener.unshorten(uri, type=type)
    if status == 200:
        uri, status = unshortener.unwrap_30x(uri, timeout=timeout)
    return uri, status


def findlinks(text):
    import sys
    if sys.version_info[0] >= 3:
        from concurrent import futures
    else:
        from concurrent_py2 import futures

    unshortener = UnshortenIt()
    matches = []

    # expand folders
    regex = '(?:https?://(?:[\w\d]+\.)?)?(?:'
    for rg in unshortener.folderRegex:
         regex += rg + '|'
    regex = regex[:-1] + ')/[a-zA-Z0-9_=/]+'
    for match in re.findall(regex, text):
        matches.append(match)

    with futures.ThreadPoolExecutor() as executor:
        unshList = [executor.submit(unshortener.expand_folder, match) for match in matches]
        for ret in futures.as_completed(unshList):
            text += '\n'.join(ret.result())
            text += '\n'

    # unshorten
    matches = []
    regex = '(?:https?://(?:[\w\d]+\.)?)?(?:'
    for rg in unshortener.listRegex:
         regex += rg + '|'
    regex = regex[:-1] + ')/[a-zA-Z0-9_=/]+'
    for match in re.findall(regex, text):
        matches.append(match)

    logger.info('matches=' + str(matches))
    if len(matches) == 1:
        text += '\n' + unshorten(matches[0])[0]
    elif matches:
        # non threaded for webpdb
        # for match in matches:
        #     sh = unshorten(match)[0]
        #     text += '\n' + sh
        with futures.ThreadPoolExecutor() as executor:
            unshList = [executor.submit(unshorten, match) for match in matches]
            for link in futures.as_completed(unshList):
                if link.result()[0] not in matches:
                    links = link.result()[0]
                    if type(links) == list:
                        for l in links:
                            text += '\n' + l
                    else:
                        text += '\n' + str(link.result()[0])
    return text


class FileCrypt:
    hostToFilter = ('https://nitroflare.com', 'http://easybytez.com', 'http://drop.download', 'https://rapidgator.net')
    extensionToFilter = ('rar',)

    def __init__(self, uri=None):
        self.uri = uri

    def find(self, data):
        _filecrypt_regex = r'https?://(?:\w+\.)?filecrypt\.cc/[a-zA-Z0-9_=/]+'
        return scrapertools.find_multiple_matches(data, _filecrypt_regex)

    def list_files(self):
        reg = """<td title="([^"]+).*?<a href="([^"]+).*?<button onclick="openLink\('([^']+)"""
        data = httptools.downloadpage(self.uri).data
        if 'Richiamo alla sicurezza' in data:  # captcha, try with gtranslate
            from lib import proxytranslate
            data = proxytranslate.process_request_proxy(self.uri).get('data', '')
        ret = scrapertools.find_multiple_matches(data, reg)
        return [r for r in ret if r[1] not in self.hostToFilter and r[0].split('.')[-1] not in self.extensionToFilter]

    def unshorten(self, link):
        link_data = httptools.downloadpage('https://filecrypt.cc/Link/' + link + '.html').data
        link_url = scrapertools.find_single_match(link_data, "location.href='([^']+)")
        if link_url:
            time.sleep(0.1)
            url = httptools.downloadpage(link_url, headers={'Referer': 'http://filecrypt.cc/'}, only_headers=True).url
            logger.info(url)
            return url
        else:
            return ''
