# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Search trailers from tmdb, youtube and mymovies...
# --------------------------------------------------------------------------------

from __future__ import division

# from builtins import str
import random
import sys

from channelselector import get_thumb

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


if PY3:
    # from future import standard_library
    # standard_library.install_aliases()
    import urllib.parse as urllib  # It is very slow in PY2. In PY3 it is native
    import urllib.parse as urlparse
    from concurrent import futures
else:
    import urllib  # We use the native of PY2 which is faster
    import urlparse
    from concurrent_py2 import futures


import re

from core import httptools, scrapertools, servertools
from core.support import match, thumb
from core.item import Item
from platformcode import config, logger, launcher
from platformcode import platformtools

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
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
    if item.contentType != "movie":
        tipo = "tv"
    else:
        tipo = "movie"

    # List of actions if run from context menu
    if item.action == "manual_search" and item.contextual:
        itemlist = manual_search(item, tipo)
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
            item.contentTitle = platformtools.dialog_input(default=contentTitle,
                                                           heading=config.get_localized_string(70505))
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
                url = url.replace("embed/", "watch?v=").replace('plugin://plugin.video.youtube/play/?video_id=', 'https://www.youtube.com/watch?v=')
            finded = servertools.findvideos(url)[0]
            title = finded[0]
            url = finded[1]
            server = finded[2]
            title = "Trailer  [" + server + "]"
            itemlist.append(item.clone(title=title, url=url, server=server, action="play"))
        try:
            for trailer in trailers:
                title = trailer['name'] + " [" + trailer['size'] + "p] (" + trailer['language'].replace("en", "ING").replace( "it", "ITA") + ")  [tmdb/youtube]"
                itemlist.append(item.clone(action="play", title=title, url=trailer['url'], server="youtube"))
        except:
            import traceback
            logger.error(traceback.format_exc())

        if multi_search(item, itemlist, tipo):
            return
    if not itemlist:
        itemlist.append(item.clone(title=config.get_localized_string(70501), title2=item.contentTitle,
                                   action="", thumbnail=get_thumb('nofolder.png'), text_color=""))

    from lib.fuzzy_match import algorithims
    itemlist.sort(key=lambda r: algorithims.trigram(item.contentTitle + ' trailer', r.title), reverse=True)

    if item.contextual:
        global window_select, result
        select = Select("DialogSelect.xml", config.get_runtime_path(), item=item, itemlist=itemlist,
                        caption=config.get_localized_string(70506) + item.contentTitle)
        window_select.append(select)
        select.doModal()

        if item.windowed: return result, window_select
    else:
        return itemlist


def multi_search(item, itemlist, tipo):
    ris = []
    dialog = platformtools.dialog_progress('Trailer', config.get_localized_string(70115))
    perc = 0
    canceled = False
    with futures.ThreadPoolExecutor() as executor:
        ris.append(executor.submit(tmdb_trailers, item, dialog, tipo))
        ris.append(executor.submit(mymovies_search, item))
        ris.append(executor.submit(youtube_search, item))

        for r in futures.as_completed(ris):
            if dialog.iscanceled():
                dialog.close()
                canceled = True
            perc += 33
            dialog.update(perc)
            itemlist.extend(r.result())
    dialog.close()
    return canceled


def manual_search(item, tipo):
    logger.debug()
    itemlist = []
    texto = platformtools.dialog_input(default=item.contentTitle, heading=config.get_localized_string(30112))
    if texto is not None:
        if multi_search(item.clone(contentTitle=texto), itemlist, tipo):
            return
    return itemlist


def tmdb_trailers(item, dialog, tipo="movie"):
    logger.debug()

    from core.tmdb import Tmdb
    itemlist = []
    tmdb_search = None
    if item.infoLabels['tmdb_id']:
        tmdb_search = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo, search_language=def_lang)
    elif item.infoLabels['year']:
        tmdb_search = Tmdb(searched_text=item.contentTitle, tipo=tipo, year=item.infoLabels['year'])

    if tmdb_search:
        found = False
        for vid in tmdb_search.get_videos():
            if vid['type'].lower() == 'trailer':
                title = vid['name']
                it = del_id(item.clone(action="play", title=title, title2="TMDB(youtube) - " + vid['language'].replace("en", "ING").replace("it", "ITA") + " [" + vid['size'] + "p]", url=vid['url'], server="youtube", window=True))
                itemlist.append(it)

                if vid['language'] == def_lang and not found:  # play now because lang is correct and TMDB is trusted
                    logger.debug('TMDB PLAY ITEM', it)
                    found = True
                    launcher.run(it)
                    dialog.close()
                    while platformtools.is_playing():
                        xbmc.sleep(100)

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
        httptools.set_cookies({'domain': 'youtube.com', 'name': 'CONSENT',
                               'value': 'YES+cb.20210328-17-p0.en+FX+' + str(random.randint(100, 999))})
        data = httptools.downloadpage("https://www.youtube.com/results?sp=EgIQAQ%253D%253D&search_query=" + title).data
    patron = r'thumbnails":\[\{"url":"(https://i.ytimg.com/vi[^"]+).*?'
    patron += r'text":"([^"]+).*?'
    patron += r'simpleText":"[^"]+.*?simpleText":"([^"]+).*?'
    patron += r'url":"([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, scrapedduration, scrapedurl in matches:
        scrapedtitle = scrapedtitle if PY3 else scrapedtitle.decode('utf8').encode('utf8')
        if item.contextual:
            scrapedtitle = "%s" % scrapedtitle
        url = urlparse.urljoin('https://www.youtube.com/', scrapedurl)
        itemlist.append(del_id(item.clone(title=scrapedtitle, title2='Youtube - ' + scrapedduration, action="play", server="youtube",
                                   url=url, thumbnail=scrapedthumbnail, window=True)))
    # next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"[^>]+><span class="yt-uix-button-content">')
    # if next_page != "":
    #     next_page = urlparse.urljoin("https://www.youtube.com", next_page)
    #     itemlist.append(item.clone(title=config.get_localized_string(30992), action="youtube_search", extra="youtube",
    #                                page=next_page, thumbnail=thumb('search'), text_color=""))

    return itemlist


def mymovies_search(item):
    logger.debug()
    import json

    title = item.contentTitle
    url = 'https://www.mymovies.it/ricerca/ricerca.php?limit=true&q=' + title
    try:
        js = json.loads(httptools.downloadpage(url).data)['risultati']['film']['elenco']
    except:
        return []

    itemlist = []
    with futures.ThreadPoolExecutor() as executor:
        ris = [executor.submit(search_links_mymovies, item.clone(title=it['titolo'], title2='MYmovies', thumbnail=it['immagine'].replace('\\', ''), url=it['url'].replace('\\', ''))) for it in js]
        for r in futures.as_completed(ris):
            if r.result():
                itemlist.append(r.result())

    return itemlist


def search_links_mymovies(item):
    global result
    logger.debug()
    trailer_url = match(item, patron=r'<source src="([^"]+)').match
    if trailer_url:
        it = del_id(item.clone(url=trailer_url, server='directo', action="play", window=True))
        return it


def del_id(it):
    """for not saving watch time"""
    if 'tmdb_id' in it.infoLabels:
        del it.infoLabels['tmdb_id']
    return it

try:
    import xbmcgui
    import xbmc


    class Select(xbmcgui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            self.item = kwargs.get('item')
            self.itemlist = kwargs.get('itemlist')
            self.caption = kwargs.get('caption')

        def onInit(self):
            try:
                self.control_list = self.getControl(6)
                self.getControl(5).setNavigation(self.getControl(7), self.getControl(7), self.control_list, self.control_list)
                self.getControl(7).setNavigation(self.getControl(5), self.getControl(5), self.control_list, self.control_list)
                self.getControl(8).setEnabled(0)
                self.getControl(8).setVisible(0)
            except:
                pass

            try:
                self.getControl(99).setVisible(False)
            except:
                pass
            self.getControl(1).setLabel("" + self.caption + "")
            if keyboard:
                self.getControl(5).setLabel(config.get_localized_string(70510))
            self.items = []
            for item in self.itemlist:
                item_l = xbmcgui.ListItem(item.title, item.title2)
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
            if id == 5 and keyboard:
                self.close()
                buscartrailer(self.item.clone(action="manual_search", extra="youtube"))

        def onAction(self, action):
            global window_select, result
            if action in [92, 110, 10]:
                result = "no_video"
                self.close()
                window_select.pop()
                if not window_select:
                    if not self.item.windowed:
                        del window_select
                else:
                    window_select[-1].doModal()

            try:
                if action in [7, 100] and self.getFocusId() == 6:
                    selectitem = self.control_list.getSelectedItem()
                    item = Item().fromurl(selectitem.getProperty("item_copy"))
                    if item.action == "play" and self.item.windowed:
                        video_urls, puede, motivo = servertools.resolve_video_urls_for_playing(item.server, item.url)
                        self.close()
                        xbmc.sleep(200)
                        if puede:
                            result = video_urls[-1][1]
                        else:
                            result = None
                    elif item.action == "play" and not self.item.windowed:
                        for window in window_select:
                            window.close()
                        retorna = platformtools.play_video(item, force_direct=True)
                        if not retorna:
                            while not xbmc.Player().isPlaying():
                                xbmc.sleep(10)
                            while xbmc.Player().isPlaying():
                                xbmc.sleep(100)
                                # if not xbmc.Player().isPlaying():
                                #     break
                        window_select[-1].doModal()
                    else:
                        self.close()
                        buscartrailer(item)
            except:
                import traceback
                logger.error(traceback.format_exc())
except:
    pass
