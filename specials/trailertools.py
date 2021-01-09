# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Search trailers from youtube, filmaffinity, mymovies, vimeo, etc...
# --------------------------------------------------------------------------------

from __future__ import division
#from builtins import str
import sys

import xbmcaddon

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
from past.utils import old_div

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                             # It is very slow in PY2. In PY3 it is native
    import urllib.parse as urlparse
else:
    import urllib                                               # We use the native of PY2 which is faster
    import urlparse

import re

from core import httptools, jsontools, scrapertools, servertools
from core.support import match, thumb
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools

info_language = ["it", "en", "es", "fr", "de", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]

result = None
window_select = []
# To enable or disable the manual search option
if config.get_platform() != "plex":
    keyboard = True
else:
    keyboard = False


def buscartrailer(item, trailers=[]):
    logger.debug()

    # List of actions if run from context menu
    if item.action == "manual_search" and item.contextual:
        itemlist = manual_search(item)
        item.contentTitle = itemlist[0].contentTitle
    elif 'search' in item.action and item.contextual:
        itemlist = globals()[item.action](item)
    else:
        # Remove Trailer Search option from context menu to avoid redundancies
        if isinstance(item.context, str) and "buscar_trailer" in item.context:
            item.context = item.context.replace("buscar_trailer", "")
        elif isinstance(item.context, list) and "buscar_trailer" in item.context:
            item.context.remove("buscar_trailer")

        item.text_color = ""

        itemlist = []
        if item.search_title:
            item.contentTitle = urllib.unquote_plus(item.search_title)
        elif item.contentTitle != "":
            item.contentTitle = item.contentTitle.strip()
        elif keyboard:
            contentTitle = re.sub(r'\[\/*(B|I|COLOR)\s*[^\]]*\]', '', item.contentTitle.strip())
            item.contentTitle = platformtools.dialog_input(default=contentTitle, heading=config.get_localized_string(70505))
            if item.contentTitle is None:
                item.contentTitle = contentTitle
            else:
                item.contentTitle = item.contentTitle.strip()
        else:
            contentTitle = re.sub(r'\[\/*(B|I|COLOR)\s*[^\]]*\]', '', item.contentTitle.strip())
            item.contentTitle = contentTitle

        item.year = item.infoLabels['year']

        logger.debug("Search: %s" % item.contentTitle)
        logger.debug("Year: %s" % item.year)
        if item.infoLabels['trailer'] and not trailers:
            url = item.infoLabels['trailer']
            if "youtube" in url:
                url = url.replace("embed/", "watch?v=")
            title, url, server = servertools.findvideos(url)[0]
            title = "Trailer  [" + server + "]"
            itemlist.append(item.clone(title=title, url=url, server=server, action="play"))
        if item.show or item.infoLabels['tvshowtitle'] or item.contentType != "movie":
            tipo = "tv"
        else:
            tipo = "movie"
        try:
            if not trailers:
                itemlist.extend(tmdb_trailers(item, tipo))
            else:
                for trailer in trailers:
                    title = trailer['name'] + " [" + trailer['size'] + "p] (" + trailer['language'].replace("en", "ING").replace("it", "ITA") + ")  [tmdb/youtube]"
                    itemlist.append(item.clone(action="play", title=title, url=trailer['url'], server="youtube"))
        except:
            import traceback
            logger.error(traceback.format_exc())

        if item.contextual: title = "%s"
        else: title = "%s"

        itemlist.append(item.clone(title=title % config.get_localized_string(70507), action="youtube_search", thumbnail=thumb('search')))
        itemlist.append(item.clone(title=title % config.get_localized_string(70508), action="mymovies_search", thumbnail=thumb('search')))
        itemlist.append(item.clone(title=title % config.get_localized_string(70024), action="filmaffinity_search", thumbnail=thumb('search')))


    if item.contextual:
        global window_select, result
        select = Select("DialogSelect.xml", config.get_runtime_path(), item=item, itemlist=itemlist, caption=config.get_localized_string(70506) + item.contentTitle)
        window_select.append(select)
        select.doModal()

        if item.windowed: return result, window_select
    else:
        return itemlist


def manual_search(item):
    logger.debug()
    texto = platformtools.dialog_input(default=item.contentTitle, heading=config.get_localized_string(30112))
    if texto is not None:
        if item.extra == "mymovies":
            return mymovies_search(item.clone(contentTitle=texto))
        elif item.extra == "youtube":
            return youtube_search(item.clone(contentTitle=texto, page=""))
        elif item.extra == "filmaffinity":
            return filmaffinity_search(item.clone(contentTitle=texto, page="", year=""))


def tmdb_trailers(item, tipo="movie"):
    logger.debug()

    from core.tmdb import Tmdb
    itemlist = []
    tmdb_search = None
    if item.infoLabels['tmdb_id']:
        tmdb_search = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo, idioma_busqueda=def_lang)
    elif item.infoLabels['year']:
        tmdb_search = Tmdb(texto_buscado=item.contentTitle, tipo=tipo, year=item.infoLabels['year'])

    if tmdb_search:
        for result in tmdb_search.get_videos():
            title = result['name'] + " [" + result['size'] + "p] (" + result['language'].replace("en", "ING").replace("it", "ITA") + ")  [tmdb/youtube]"
            itemlist.append(item.clone(action="play", title=title, url=result['url'], server="youtube"))

    return itemlist


def youtube_search(item):
    logger.debug()
    itemlist = []
    title = item.contentTitle
    if item.extra != "youtube":
        title += " trailer"
    # Check if it is a zero search or comes from the Next option
    if item.page != "":
        data = httptools.downloadpage(item.page).data
    else:
        title = urllib.quote(title)
        title = title.replace("%20", "+")
        data = httptools.downloadpage("https://www.youtube.com/results?sp=EgIQAQ%253D%253D&q=" + title).data
    patron  = r'thumbnails":\[\{"url":"(https://i.ytimg.com/vi[^"]+).*?'
    patron += r'text":"([^"]+).*?'
    patron += r'simpleText":"[^"]+.*?simpleText":"([^"]+).*?'
    patron += r'url":"([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, scrapedduration, scrapedurl in matches:
        scrapedtitle = scrapedtitle if PY3 else scrapedtitle.decode('utf8').encode('utf8') + " (" + scrapedduration + ")"
        if item.contextual:
            scrapedtitle = "%s" % scrapedtitle
        url = urlparse.urljoin('https://www.youtube.com/', scrapedurl)
        itemlist.append(item.clone(title=scrapedtitle, action="play", server="youtube", url=url, thumbnail=scrapedthumbnail))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"[^>]+><span class="yt-uix-button-content">')
    if next_page != "":
        next_page = urlparse.urljoin("https://www.youtube.com", next_page)
        itemlist.append(item.clone(title=config.get_localized_string(30992), action="youtube_search", extra="youtube", page=next_page, thumbnail=thumb('search'), text_color=""))
    if not itemlist:
        itemlist.append(item.clone(title=config.get_localized_string(70501) % title, action="", thumbnail="", text_color=""))
    if keyboard:
        if item.contextual:
            title = "%s"
        else:
            title = "%s"
        itemlist.append(item.clone(title=title % config.get_localized_string(70510), action="manual_search", thumbnail=thumb('search'), extra="youtube"))
    return itemlist


def mymovies_search(item):
    logger.debug()
    import json

    title = item.contentTitle
    url = 'https://www.mymovies.it/ricerca/ricerca.php?limit=true&q=' + title
    js = json.loads(httptools.downloadpage(url).data)['risultati']['film']['elenco']


    itemlist = []
    for it in js:
        itemlist.append(item.clone(title=it['titolo'], thumbnail=it['immagine'].replace('\\',''), url=it['url'].replace('\\',''), action ='search_links_mymovies'))

    if not itemlist:
        itemlist.append(item.clone(title=config.get_localized_string(70501), action="", thumbnail="", text_color=""))

    if keyboard:
        if item.contextual: title = "%s"
        else: title = "%s"
        itemlist.append(item.clone(title=title % config.get_localized_string(70511), action="manual_search", thumbnail=thumb('search'),  extra="mymovies"))

    return itemlist


def search_links_mymovies(item):
    logger.debug()
    trailer_url = match(item, patron=r'<li class="bottone_playlist"[^>]+><a href="([^"]+)"').match
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if trailer_url:
        itemlist.append(item.clone(title=config.get_localized_string(60221) + ' ' + item.title, url=trailer_url, server='directo', action="play"))
        itemlist = servertools.get_servers_itemlist(itemlist)

    else:
        if keyboard:
            if item.contextual:
                title = "%s"
            else:
                title = "%s"
            itemlist.append(item.clone(title=title % config.get_localized_string(70513), action="manual_search", thumbnail=thumb('search'), extra="filmaffinity"))

    return itemlist


def filmaffinity_search(item):
    logger.debug()

    if item.filmaffinity:
        item.url = item.filmaffinity
        return search_links_filmaff(item)

    # Check if it is a zero search or comes from the Next option
    if item.page != "":
        data = httptools.downloadpage(item.page).data
    else:
        params = urllib.urlencode([('stext', item.contentTitle), ('stype%5B%5D', 'title'), ('country', ''), ('genre', ''), ('fromyear', item.year), ('toyear', item.year)])
        url = "http://www.filmaffinity.com/es/advsearch.php?%s" % params
        data = httptools.downloadpage(url).data

    itemlist = []
    patron = '<div class="mc-poster">.*?<img.*?src="([^"]+)".*?' \
             '<div class="mc-title"><a  href="/es/film(\d+).html"[^>]+>(.*?)<img'
    matches = scrapertools.find_multiple_matches(data, patron)
    # If there is only one result, search directly for the trailers, but list all the results
    if len(matches) == 1:
        item.url = "http://www.filmaffinity.com/es/evideos.php?movie_id=%s" % matches[0][1]
        item.thumbnail = matches[0][0]
        if not item.thumbnail.startswith("http"): item.thumbnail = "http://www.filmaffinity.com" + item.thumbnail
        itemlist = search_links_filmaff(item)
    elif len(matches) > 1:
        for scrapedthumbnail, id, scrapedtitle in matches:
            if not scrapedthumbnail.startswith("http"): scrapedthumbnail = "http://www.filmaffinity.com" + scrapedthumbnail
            scrapedurl = "http://www.filmaffinity.com/es/evideos.php?movie_id=%s" % id
            if PY3: scrapedtitle = unicode(scrapedtitle, encoding="utf-8", errors="ignore")
            scrapedtitle = scrapertools.htmlclean(scrapedtitle)
            itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action="search_links_filmaff", thumbnail=scrapedthumbnail))

        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)">&gt;&gt;</a>')
        if next_page != "":
            next_page = urlparse.urljoin("http://www.filmaffinity.com/es/", next_page)
            itemlist.append(item.clone(title=config.get_localized_string(30992), page=next_page, action="filmaffinity_search", thumbnail=thumb('search'), text_color=""))

    if not itemlist: itemlist.append(item.clone(title=config.get_localized_string(70501) % item.contentTitle, action="", thumbnail="", text_color=""))

    if keyboard:
        if item.contextual: title = "%s"
        else: title = "%s"
        itemlist.append(item.clone(title=title % config.get_localized_string(70513), action="manual_search", thumbnail=thumb('search'), extra="filmaffinity"))

    return itemlist


def search_links_filmaff(item):
    logger.debug()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    if not '<a class="lnkvvid"' in data:
        itemlist.append(item.clone(title=config.get_localized_string(70503), action="", text_color=""))
    else:
        patron = '<a class="lnkvvid".*?<b>(.*?)</b>.*?iframe.*?src="([^"]+)"'
        matches = scrapertools.find_multiple_matches(data, patron)
        for scrapedtitle, scrapedurl in matches:
            if not scrapedurl.startswith("http:"):
                scrapedurl = urlparse.urljoin("http:", scrapedurl)
            trailer_url = scrapedurl.replace("-nocookie.com/embed/", ".com/watch?v=")
            if "youtube" in trailer_url:
                server = "youtube"
                code = scrapertools.find_single_match(trailer_url, 'v=([A-z0-9\-_]+)')
                thumbnail = "https://img.youtube.com/vi/%s/0.jpg" % code
            else:
                server = ""
                thumbnail = item.thumbnail
            if PY3:
                scrapedtitle = unicode(scrapedtitle, encoding="utf-8", errors="ignore")
            scrapedtitle = scrapertools.htmlclean(scrapedtitle)
            scrapedtitle += "  [" + server + "]"
            if item.contextual:
                scrapedtitle = "%s" % scrapedtitle
            itemlist.append(item.clone(title=scrapedtitle, url=trailer_url, server=server, action="play", thumbnail=thumbnail))

    itemlist = servertools.get_servers_itemlist(itemlist)
    if keyboard:
        if item.contextual:
            title = "%s"
        else:
            title = "%s"
        itemlist.append(item.clone(title=title % config.get_localized_string(70513), action="manual_search", thumbnail="", extra="filmaffinity"))

    return itemlist



try:
    import xbmcgui
    import xbmc
    class Select(xbmcgui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            self.item = kwargs.get('item')
            self.itemlist = kwargs.get('itemlist')
            self.caption = kwargs.get('caption')
            self.result = None
        def onInit(self):
            try:
                self.control_list = self.getControl(6)
                self.getControl(5).setNavigation(self.control_list, self.control_list, self.control_list, self.control_list)
                self.getControl(3).setEnabled(0)
                self.getControl(3).setVisible(0)
            except:
                pass

            try:
                self.getControl(99).setVisible(False)
            except:
                pass
            self.getControl(1).setLabel("" + self.caption + "")
            self.getControl(5).setLabel(config.get_localized_string(60495))
            self.items = []
            for item in self.itemlist:
                item_l = xbmcgui.ListItem(item.title)
                item_l.setArt({'thumb': item.thumbnail})
                item_l.setProperty('item_copy', item.tourl())
                self.items.append(item_l)
            self.control_list.reset()
            self.control_list.addItems(self.items)
            self.setFocus(self.control_list)
        def onClick(self, id):
            global window_select, result
            # Cancel button y [X]
            if id == 7:
                window_select[-1].close()
            if id == 5:
                self.result = "_no_video"
                result = "no_video"
                self.close()
                window_select.pop()
                if not window_select:
                    if not self.item.windowed:
                        del window_select
                else:
                    window_select[-1].doModal()
        def onAction(self, action):
            global window_select, result
            if action == 92 or action == 110:
                self.result = "no_video"
                result = "no_video"
                self.close()
                window_select.pop()
                if not window_select:
                    if not self.item.windowed:
                        del window_select
                else:
                    window_select[-1].doModal()
            try:
                if (action == 7 or action == 100) and self.getFocusId() == 6:
                    selectitem = self.control_list.getSelectedItem()
                    item = Item().fromurl(selectitem.getProperty("item_copy"))
                    if item.action == "play" and self.item.windowed:
                        video_urls, puede, motivo = servertools.resolve_video_urls_for_playing(item.server, item.url)
                        self.close()
                        xbmc.sleep(200)
                        if puede:
                            result = video_urls[-1][1]
                            self.result = video_urls[-1][1]
                        else:
                            result = None
                            self.result = None
                    elif item.action == "play" and not self.item.windowed:
                        for window in window_select:
                            window.close()
                        retorna = platformtools.play_video(item, force_direct=True)
                        if not retorna:
                            while True:
                                xbmc.sleep(1000)
                                if not xbmc.Player().isPlaying():
                                    break
                        window_select[-1].doModal()
                    else:
                        self.close()
                        buscartrailer(item)
            except:
                import traceback
                logger.error(traceback.format_exc())
except:
    pass
