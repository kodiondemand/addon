# -*- coding: utf-8 -*-

from builtins import range
import xbmcgui
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import platformtools

lang = 'it'

class Recaptcha(xbmcgui.WindowXMLDialog):
    def Start(self, key, referer):
        self.referer = referer
        self.key = key
        self.headers = {'Referer': self.referer}

        api_js = httptools.downloadpage("https://www.google.com/recaptcha/api.js?hl=" + lang).data
        version = scrapertools.find_single_match(api_js, 'po.src\s*=\s*\'(.*?)\';').split("/")[5]
        self.url = "https://www.google.com/recaptcha/api/fallback?k=" + self.key + "&hl=" + lang + "&v=" + version + "&t=2&ff=true"
        self.doModal()
        # Reload
        if self.result == {}:
            self.result = Recaptcha("Recaptcha.xml", config.get_runtime_path()).Start(self.key, self.referer)

        return self.result

    def update_window(self):
        data = httptools.downloadpage(self.url, headers=self.headers).data
        self.message = scrapertools.find_single_match(data,
                                                      '<div class="rc-imageselect-desc[a-z-]*">(.*?)(?:</label>|</div>)').replace(
            "<strong>", "[B]").replace("</strong>", "[/B]")
        self.token = scrapertools.find_single_match(data, 'name="c" value="([^"]+)"')
        self.image = "https://www.google.com/recaptcha/api2/payload?k=%s&c=%s" % (self.key, self.token)
        self.result = {}
        self.getControl(10020).setImage(self.image)
        self.getControl(10000).setText(self.message)
        self.setFocusId(10005)

    def __init__(self, *args, **kwargs):
        self.mensaje = kwargs.get("mensaje")
        self.imagen = kwargs.get("imagen")

    def onInit(self):
        #### Kodi 18 compatibility ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)
        self.update_window()

    def onClick(self, control):
        if control == 10003:
            self.result = None
            self.close()

        elif control == 10004:
            self.result = {}
            self.close()

        elif control == 10002:
            self.result = [int(k) for k in range(9) if self.result.get(k, False)]
            post = {
                "c": self.token,
                "response": self.result
            }

            data = httptools.downloadpage(self.url, post=post, headers=self.headers).data
            from platformcode import logger
            logger.info(data)
            self.result = scrapertools.find_single_match(data, '<div class="fbc-verification-token">.*?>([^<]+)<')
            if self.result:
                platformtools.dialog_notification("Captcha corretto", "Verifica conclusa")
                self.close()
            else:
                self.result = {}
                self.close()
        else:
            self.result[control - 10005] = not self.result.get(control - 10005, False)
