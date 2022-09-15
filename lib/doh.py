# https://github.com/stamparm/python-doh
import json
import re
import socket
import ssl
import subprocess
import sys
from platformcode import logger

PY3 = sys.version_info >= (3, 0)

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context
    DOH_SERVER = "1.0.0.1"              # Note: to prevent potential blocking of service based on DNS name
else:
    DOH_SERVER = "cloudflare-dns.com"   # Alternative servers: doh.securedns.eu, doh-de.blahdns.com, doh-jp.blahdns.com

if PY3:
    import urllib.request
    _urlopen = urllib.request.urlopen
    _Request = urllib.request.Request
else:
    import urllib2
    _urlopen = urllib2.urlopen
    _Request = urllib2.Request

# ipv6 = ':' in _urlopen('https://api64.ipify.org/').read().decode()
ipv6 = False


def query(name, type='AAAA' if ipv6 else 'A', server=DOH_SERVER, path="/dns-query", fallback=True):
    """
    Returns domain name query results retrieved by using DNS over HTTPS protocol
    # Reference: https://developers.cloudflare.com/1.1.1.1/dns-over-https/json-format/
    >>> query("one.one.one.one", fallback=False)
    ['1.0.0.1', '1.1.1.1']
    >>> query("one", "NS")
    ['a.nic.one.', 'b.nic.one.', 'c.nic.one.', 'd.nic.one.']
    """

    retval = None

    try:
        req = _Request("https://%s%s?name=%s&type=%s" % (server, path, name, type), headers={"Accept": "application/dns-json"})
        content = _urlopen(req, timeout=2).read().decode()
        reply = json.loads(content)

        if "Answer" in reply:
            answer = json.loads(content)["Answer"]
            retval = [_["data"] for _ in answer]
        else:
            retval = []
    except Exception as ex:
        logger.error("Exception occurred: '%s'" % ex)

    if retval is None and fallback:
        if type == 'A':
            try:
                retval = socket.gethostbyname_ex(name)[2]
            except (socket.error, IndexError):
                pass

        if retval is None:
            process = subprocess.Popen(("nslookup", "-q=%s" % type, name), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            content = (process.communicate()[0] or "").decode().replace("\r", "")

            if "\n\n" in content and "can't" not in content.lower():
                answer = content.split("\n\n", 1)[-1]
                retval = re.findall(r"(?m)^%s.+= ([^=,\n]+)$" % re.escape(name), answer) or re.findall(r"Address: (.+)", answer)

                if not retval:
                    match = re.search(r"Addresses: ([\s\d.]+)", answer)
                    if match:
                        retval = re.split(r"\s+", match.group(1).strip())

    if not PY3 and retval:
        retval = [_.encode() for _ in retval]

    return retval