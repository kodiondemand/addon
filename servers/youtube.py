# s-*- coding: utf-8 -*-
import xbmc, xbmcaddon, sys, re
from core import httptools, scrapertools, filetools, support
from platformcode import config, logger, platformtools

name = 'plugin.video.youtube'

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data or "Video non disponibile" in data:
        return False, config.getLocalizedString(70449) % "YouTube"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    import xbmc
    from xbmcaddon import Addon
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []

    video_id = scrapertools.find_single_match(page_url, '(?:v=|embed/)([A-z0-9_-]{11})')
    inputstream = platformtools.installInputstream()

    try:
        __settings__ = Addon(name)
        if inputstream: __settings__.setSetting('kodion.video.quality.mpd', 'true')
        else: __settings__.setSetting('kodion.video.quality.mpd', 'false')
        # videoUrls = [['con YouTube', 'plugin://plugin.video.youtube/play/?video_id=' + video_id ]]
    except:
        path = xbmc.translatePath('special://home/addons/' + name)
        if filetools.exists(path):
            if platformtools.dialogYesNo(config.getLocalizedString(70784), config.getLocalizedString(70818)):
                xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "' + name + '", "enabled": true }}')
            else: return [['','']]
        else:
            xbmc.executebuiltin('InstallAddon(' + name + ')', wait=True)
            try: Addon(name)
            except: return [['','']]
    my_addon = xbmcaddon.Addon('plugin.video.youtube')
    addon_dir = xbmc.translatePath( my_addon.getAddonInfo('path') )
    sys.path.append(filetools.join( addon_dir, 'resources', 'lib' ) )
    from youtube_resolver import resolve
    try:
        for stream in resolve(page_url):
            r,t = scrapertools.find_single_match(stream['title'], r'(\d+p)[^\(]+\(([^;]+)')
            if r:
                videoUrls.append({'type':t, 'res':r, 'url':stream['url']})
        # videoUrls.sort(key=lambda it: int(it[0].split("p", 1)[0]))
    except:
        pass

    return videoUrls

