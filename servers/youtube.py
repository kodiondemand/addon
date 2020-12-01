# s-*- coding: utf-8 -*-

from core import httptools, scrapertools, filetools
from platformcode import config, logger, platformtools

name = 'plugin.video.youtube'

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data or "Video non disponibile" in data:
        return False, config.get_localized_string(70449) % "YouTube"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    import xbmc
    from xbmcaddon import Addon
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []

    if not page_url.startswith("http"):
        page_url = "http://www.youtube.com/watch?v=%s" % page_url
        logger.debug(" page_url->'%s'" % page_url)

    video_id = scrapertools.find_single_match(page_url, '(?:v=|embed/)([A-z0-9_-]{11})')
    inputstream = platformtools.install_inputstream()
    # from core.support import dbg;dbg()
    try:
        __settings__ = Addon(name)
        if inputstream: __settings__.setSetting('kodion.video.quality.mpd', 'true')
        else: __settings__.setSetting('kodion.video.quality.mpd', 'false')
        video_urls = [['con YouTube', 'plugin://plugin.video.youtube/play/?video_id=' + video_id ]]
    except:
        if filetools.exists(xbmc.translatePath('special://profile/addons/' + name)):
            if platformtools.dialog_yesno(config.get_localized_string(70784), config.get_localized_string(70818)):
                xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "' + name + '", "enabled": true }}')
            else: return [['','']]
        else:
            xbmc.executebuiltin('InstallAddon(' + name + ')', wait=True)
            try: Addon(name)
            except: return [['','']]

        return get_video_url(page_url)
    return video_urls

