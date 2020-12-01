# -*- coding: utf-8 -*-


from core import httptools
from core import jsontools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "Page not found" in data or "File was deleted" in data:
        return False,  config.get_localized_string(70449) % "vidoza"
    elif "processing" in data:
        return False, config.get_localized_string(70449) % "Vidoza"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    global data
    video_urls = []

    s = scrapertools.find_single_match(data, r'sourcesCode\s*:\s*(\[\{.*?\}\])')
    s = s.replace('src:', '"src":').replace('file:', '"file":').replace('type:', '"type":').replace('label:', '"label":').replace('res:', '"res":')
    try:
        data = jsontools.load(s)
        for enlace in data:
            if 'src' in enlace or 'file' in enlace:
                url = enlace['src'] if 'src' in enlace else enlace['file']
                tit = ''
                if 'label' in enlace: tit += ' [%s]' % enlace['label']
                if 'res' in enlace: tit += ' [%s]' % enlace['res']
                if tit == '' and 'type' in enlace: tit = enlace['type']
                if tit == '': tit = '.mp4'

                video_urls.append(["%s [Vidoza]" % tit, url])
    except:
        logger.debug('No se detecta json %s' % s)
        pass

    video_urls.reverse()

    return video_urls
