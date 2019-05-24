# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Cloudflare decoder
# --------------------------------------------------------------------------------

import re
import time
import urllib

import urlparse

from platformcode import logger


class Cloudflare:
    def __init__(self, response):
        self.timeout = 5
        self.domain = urlparse.urlparse(response["url"])[1]
        self.protocol = urlparse.urlparse(response["url"])[0]
        self.js_data = {}
        self.header_data = {}
        if not "var s,t,o,p,b,r,e,a,k,i,n,g,f" in response["data"] or "chk_jschl" in response["url"]:
            return
        try:
            self.js_data["data"] = response["data"]
            self.js_data["auth_url"] = \
                re.compile('<form id="challenge-form" action="([^"]+)" method="get">').findall(response["data"])[0]
            self.js_data["params"] = {}
            self.js_data["params"]["jschl_vc"] = \
                re.compile('<input type="hidden" name="jschl_vc" value="([^"]+)"/>').findall(response["data"])[0]
            self.js_data["params"]["pass"] = \
                re.compile('<input type="hidden" name="pass" value="([^"]+)"/>').findall(response["data"])[0]
            self.js_data["wait"] = int(re.compile("\}, ([\d]+)\);", re.MULTILINE).findall(response["data"])[0]) / 1000
            self.js_data["params"]["s"] = \
                re.compile('<input type="hidden" name="s" value="([^"]+)"').findall(response["data"])[0]
        except:
            logger.debug("Metodo #1 (javascript): NO disponible")
            self.js_data = {}
        if "refresh" in response["headers"]:
            try:
                self.header_data["wait"] = int(response["headers"]["refresh"].split(";")[0])
                self.header_data["auth_url"] = response["headers"]["refresh"].split("=")[1].split("?")[0]
                self.header_data["params"] = {}
                self.header_data["params"]["pass"] = response["headers"]["refresh"].split("=")[2]
            except:
                logger.debug("Metodo #2 (headers): NO disponible")
                self.header_data = {}

    def solve_cf(self, body, domain):
        js = re.search(
            r"setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n",
            body
        ).group(1)

        js = re.sub(r"a\.value = ((.+).toFixed\(10\))?", r"\1", js)
        js = re.sub(r'(e\s=\sfunction\(s\)\s{.*?};)', '', js, flags=re.DOTALL|re.MULTILINE)
        js = re.sub(r"\s{3,}[a-z](?: = |\.).+", "", js).replace("t.length", str(len(domain)))
        js = js.replace('; 121', '')
        js = re.sub(r"[\n\\']", "", js)
        jsEnv = """
        var t = "{domain}";
        var g = String.fromCharCode;
        o = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
        e = function(s) {{
            s += "==".slice(2 - (s.length & 3));
            var bm, r = "", r1, r2, i = 0;
            for (; i < s.length;) {{
                bm = o.indexOf(s.charAt(i++)) << 18 | o.indexOf(s.charAt(i++)) << 12 | (r1 = o.indexOf(s.charAt(i++))) << 6 | (r2 = o.indexOf(s.charAt(i++)));
                r += r1 === 64 ? g(bm >> 16 & 255) : r2 === 64 ? g(bm >> 16 & 255, bm >> 8 & 255) : g(bm >> 16 & 255, bm >> 8 & 255, bm & 255);
            }}
            return r;
        }};
        function italics (str) {{ return '<i>' + this + '</i>'; }};
        var document = {{
            getElementById: function () {{
                return {{'innerHTML': '{innerHTML}'}};
            }}
        }};
        {js}
        """
        innerHTML = re.search('<div(?: [^<>]*)? id="([^<>]*?)">([^<>]*?)<\/div>', body , re.MULTILINE | re.DOTALL)
        innerHTML = innerHTML.group(2).replace("'", r"\'") if innerHTML else ""
        import js2py
        from jsc import jsunc
        js = jsunc(jsEnv.format(domain=domain, innerHTML=innerHTML, js=js))
        def atob(s):
            return base64.b64decode('{}'.format(s)).decode('utf-8')
        js2py.disable_pyimport()
        context = js2py.EvalJs({'atob': atob})
        result = context.eval(js)
        return float(result)


    @property
    def wait_time(self):
        if self.js_data.get("wait", 0):
            return self.js_data["wait"]
        else:
            return self.header_data.get("wait", 0)

    @property
    def is_cloudflare(self):
        return self.header_data.get("wait", 0) > 0 or self.js_data.get("wait", 0) > 0

    def get_url(self):
        # Metodo #1 (javascript)
        if self.js_data.get("wait", 0):
            self.js_data["params"]["jschl_answer"] =  self.solve_cf(self.js_data["data"], self.domain)
            response = "%s://%s%s?%s" % (
                self.protocol, self.domain, self.js_data["auth_url"], urllib.urlencode(self.js_data["params"]))
            time.sleep(self.js_data["wait"])
            return response
