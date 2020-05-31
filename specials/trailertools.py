# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Search trailers from youtube, filmaffinity, abandomoviez, vimeo, etc...
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

from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
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
    logger.info()

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
            contentTitle = re.sub('\[\/*(B|I|COLOR)\s*[^\]]*\]', '', item.contentTitle.strip())
            item.contentTitle = platformtools.dialog_input(default=contentTitle, heading=config.get_localized_string(70505))
            if item.contentTitle is None:
                item.contentTitle = contentTitle
            else:
                item.contentTitle = item.contentTitle.strip()
        else:
            contentTitle = re.sub('\[\/*(B|I|COLOR)\s*[^\]]*\]', '', item.contentTitle.strip())
            item.contentTitle = contentTitle

        item.year = item.infoLabels['year']

        logger.info("Search: %s" % item.contentTitle)
        logger.info("Year: %s" % item.year)
        if item.infoLabels['trailer'] and not trailers:
            url = item.infoLabels['trailer']
            if "youtube" in url:
                url = url.replace("embed/", "watch?v=")
            titulo, url, server = servertools.findvideos(url)[0]
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

        if item.contextual:
            title = "%s"
        else:
            title = "%s"
        itemlist.append(item.clone(title=title % config.get_localized_string(70507), action="youtube_search"))
        itemlist.append(item.clone(title=title % config.get_localized_string(70024), action="filmaffinity_search"))
        # If it is a series, the option to search in Abandomoviez is not included
        if not item.show and not item.infoLabels['tvshowtitle']:
            itemlist.append(item.clone(title=title % config.get_localized_string(70508), action="abandomoviez_search"))

    if item.contextual:
        global window_select, result
        select = Select("DialogSelect.xml", config.get_runtime_path(), item=item, itemlist=itemlist, caption=config.get_localized_string(70506) + item.contentTitle)
        window_select.append(select)
        select.doModal()

        if item.windowed:
            return result, window_select
    else:
        return itemlist


def manual_search(item):
    logger.info()
    texto = platformtools.dialog_input(default=item.contentTitle, heading=config.get_localized_string(30112))
    if texto is not None:
        if item.extra == "abandomoviez":
            return abandomoviez_search(item.clone(contentTitle=texto, page="", year=""))
        elif item.extra == "youtube":
            return youtube_search(item.clone(contentTitle=texto, page=""))
        elif item.extra == "filmaffinity":
            return filmaffinity_search(item.clone(contentTitle=texto, page="", year=""))


def tmdb_trailers(item, tipo="movie"):
    logger.info()

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
    logger.info()
    itemlist = []
    titulo = item.contentTitle
    if item.extra != "youtube":
        titulo += " trailer"
    # Check if it is a zero search or comes from the Next option
    if item.page != "":
        data = httptools.downloadpage(item.page).data
    else:
        titulo = urllib.quote(titulo)
        titulo = titulo.replace("%20", "+")
        data = httptools.downloadpage("https://www.youtube.com/results?sp=EgIQAQ%253D%253D&q=" + titulo).data
    patron  = 'thumbnails":\[\{"url":"(https://i.ytimg.com/vi[^"]+).*?'
    patron += 'text":"([^"]+).*?'
    patron += 'simpleText":"[^"]+.*?simpleText":"([^"]+).*?'
    patron += 'url":"([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, scrapedduration, scrapedurl in matches:
        scrapedtitle = scrapedtitle.decode('utf8').encode('utf8')
        scrapedtitle = scrapedtitle + " (" + scrapedduration + ")"
        if item.contextual:
            scrapedtitle = "%s" % scrapedtitle
        url = urlparse.urljoin('https://www.youtube.com/', scrapedurl)
        itemlist.append(item.clone(title=scrapedtitle, action="play", server="youtube", url=url, thumbnail=scrapedthumbnail))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"[^>]+><span class="yt-uix-button-content">'
                                                     'Siguiente')
    if next_page != "":
        next_page = urlparse.urljoin("https://www.youtube.com", next_page)
        itemlist.append(item.clone(title=config.get_localized_string(70502), action="youtube_search", extra="youtube", page=next_page,
                                   thumbnail="", text_color=""))
    if not itemlist:
        itemlist.append(item.clone(title=config.get_localized_string(70501) % titulo,
                                   action="", thumbnail="", text_color=""))
    if keyboard:
        if item.contextual:
            title = "%s"
        else:
            title = "%s"
        itemlist.append(item.clone(title=title % config.get_localized_string(70510), action="manual_search",
                                   thumbnail="", extra="youtube"))
    return itemlist


def abandomoviez_search(item):
    logger.info()

    # Check if it is a zero search or comes from the Next option
    if item.page != "":
        data = httptools.downloadpage(item.page).data
    else:
        titulo = item.contentTitle.decode('utf-8').encode('iso-8859-1')
        post = urllib.urlencode({'query': titulo, 'searchby': '1', 'posicion': '1', 'orden': '1',
                                 'anioin': item.year, 'anioout': item.year, 'orderby': '1'})
        url = "http://www.abandomoviez.net/db/busca_titulo.php?busco2=%s" %item.contentTitle
        item.prefix = "db/"
        data = httptools.downloadpage(url, post=post).data
        if "No hemos encontrado ninguna" in data:
            url = "http://www.abandomoviez.net/indie/busca_titulo.php?busco2=%s" %item.contentTitle
            item.prefix = "indie/"
            data = httptools.downloadpage(url, post=post).data.decode("iso-8859-1").encode('utf-8')

    itemlist = []
    patron = '(?:<td width="85"|<div class="col-md-2 col-sm-2 col-xs-3">).*?<img src="([^"]+)"' \
             '.*?href="([^"]+)">(.*?)(?:<\/td>|<\/small>)'
    matches = scrapertools.find_multiple_matches(data, patron)
    # If there is only one result, search directly for the trailers, but list all the results
    if len(matches) == 1:
        item.url = urlparse.urljoin("http://www.abandomoviez.net/%s" % item.prefix, matches[0][1])
        item.thumbnail = matches[0][0]
        itemlist = search_links_abando(item)
    elif len(matches) > 1:
        for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
            scrapedurl = urlparse.urljoin("http://www.abandomoviez.net/%s" % item.prefix, scrapedurl)
            scrapedtitle = scrapertools.htmlclean(scrapedtitle)
            itemlist.append(item.clone(title=scrapedtitle, action="search_links_abando", url=scrapedurl, thumbnail=scrapedthumbnail))

        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)">Siguiente')
        if next_page != "":
            next_page = urlparse.urljoin("http://www.abandomoviez.net/%s" % item.prefix, next_page)
            itemlist.append(item.clone(title=config.get_localized_string(70502), action="abandomoviez_search", page=next_page, thumbnail="", text_color=""))

    if not itemlist:
        itemlist.append(item.clone(title=config.get_localized_string(70501), action="", thumbnail="", text_color=""))

        if keyboard:
            if item.contextual:
                title = "%s"
            else:
                title = "%s"
            itemlist.append(item.clone(title=title % config.get_localized_string(70511), action="manual_search", thumbnail="",  extra="abandomoviez"))

    return itemlist


def search_links_abando(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    itemlist = []
    if "Lo sentimos, no tenemos trailer" in data:
        itemlist.append(item.clone(title=config.get_localized_string(70503), action="", text_color=""))
    else:
        if item.contextual:
            progreso = platformtools.dialog_progress(config.get_localized_string(70512), config.get_localized_string(70504))
            progreso.update(10)
            i = 0
            message = config.get_localized_string(70504)
        patron = '<div class="col-md-3 col-xs-6"><a href="([^"]+)".*?' \
                 'Images/(\d+).gif.*?</div><small>(.*?)</small>'
        matches = scrapertools.find_multiple_matches(data, patron)
        if len(matches) == 0:
            trailer_url = scrapertools.find_single_match(data, '<iframe.*?src="([^"]+)"')
            if trailer_url != "":
                trailer_url = trailer_url.replace("embed/", "watch?v=")
                code = scrapertools.find_single_match(trailer_url, 'v=([A-z0-9\-_]+)')
                thumbnail = "https://img.youtube.com/vi/%s/0.jpg" % code
                itemlist.append(item.clone(title="Trailer  [youtube]", url=trailer_url, server="youtube",
                                           thumbnail=thumbnail, action="play"))
        else:
            for scrapedurl, language, scrapedtitle in matches:
                if language == "1":
                    idioma = " (ITA)"
                else:
                    idioma = " (V.O)"
                scrapedurl = urlparse.urljoin("http://www.abandomoviez.net/%s" % item.prefix, scrapedurl)
                scrapedtitle = scrapertools.htmlclean(scrapedtitle) + idioma + "  [youtube]"
                if item.contextual:
                    i += 1
                    message += ".."
                    progreso.update(10 + (old_div(90 * i, len(matches))), message)
                    scrapedtitle = "%s" % scrapedtitle
                data_trailer = httptools.downloadpage(scrapedurl).data
                trailer_url = scrapertools.find_single_match(data_trailer, 'iframe.*?src="([^"]+)"')
                trailer_url = trailer_url.replace("embed/", "watch?v=")
                code = scrapertools.find_single_match(trailer_url, 'v=([A-z0-9\-_]+)')
                thumbnail = "https://img.youtube.com/vi/%s/0.jpg" % code
                itemlist.append(item.clone(title=scrapedtitle, url=trailer_url, server="youtube", action="play",
                                           thumbnail=thumbnail))
        if item.contextual:
            progreso.close()
    if keyboard:
        if item.contextual:
            title = "%s"
        else:
            title = "%s"
        itemlist.append(item.clone(title=title % config.get_localized_string(70511),
                                   action="manual_search", thumbnail="", extra="abandomoviez"))
    return itemlist


def filmaffinity_search(item):
    logger.info()

    if item.filmaffinity:
        item.url = item.filmaffinity
        return search_links_filmaff(item)

    # Check if it is a zero search or comes from the Next option
    if item.page != "":
        data = httptools.downloadpage(item.page).data
    else:
        params = urllib.urlencode([('stext', item.contentTitle), ('stype%5B%5D', 'title'), ('country', ''),
                                   ('genre', ''), ('fromyear', item.year), ('toyear', item.year)])
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
        if not item.thumbnail.startswith("http"):
            item.thumbnail = "http://www.filmaffinity.com" + item.thumbnail
        itemlist = search_links_filmaff(item)
    elif len(matches) > 1:
        for scrapedthumbnail, id, scrapedtitle in matches:
            if not scrapedthumbnail.startswith("http"):
                scrapedthumbnail = "http://www.filmaffinity.com" + scrapedthumbnail
            scrapedurl = "http://www.filmaffinity.com/es/evideos.php?movie_id=%s" % id
            if PY3:
                scrapedtitle = unicode(scrapedtitle, encoding="utf-8", errors="ignore")
            scrapedtitle = scrapertools.htmlclean(scrapedtitle)
            itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action="search_links_filmaff", thumbnail=scrapedthumbnail))

        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)">&gt;&gt;</a>')
        if next_page != "":
            next_page = urlparse.urljoin("http://www.filmaffinity.com/es/", next_page)
            itemlist.append(item.clone(title=config.get_localized_string(70502), page=next_page, action="filmaffinity_search", thumbnail="", text_color=""))

    if not itemlist:
        itemlist.append(item.clone(title=config.get_localized_string(70501) % item.contentTitle, action="", thumbnail="", text_color=""))

        if keyboard:
            if item.contextual:
                title = "%s"
            else:
                title = "%s"
            itemlist.append(item.clone(title=title % config.get_localized_string(70513), action="manual_search", thumbnail="", extra="filmaffinity"))

    return itemlist


def search_links_filmaff(item):
    logger.info()

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
                self.getControl(5).setNavigation(self.control_list, self.control_list, self.control_list,
                                                 self.control_list)
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
            # Cancel button y [X]
            if id == 5:
                global window_select, result
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
