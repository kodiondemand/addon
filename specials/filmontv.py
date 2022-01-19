# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# ------------------------------------------------------------

import re
try:
    import urllib.parse as urllib
except ImportError:
    import urllib
from core import httptools, scrapertools, support, tmdb, filetools
from core.item import Item
from platformcode import logger, config, platformtools

host = "https://www.superguidatv.it"

TIMEOUT_TOTAL = 60


def mainlist(item):
    logger.debug(" mainlist")
    itemlist = [#Item(channel="search", action='discover_list', title=config.get_localized_string(70309),
               #search_type='list', list_type='movie/now_playing',
               #          thumbnail=get_thumb("now_playing.png")),
               #Item(channel="search", action='discover_list', title=config.get_localized_string(70312),
               #          search_type='list', list_type='tv/on_the_air', thumbnail=get_thumb("on_the_air.png")),
            Item(title=support.typo('Canali live', 'bold'),
                 channel=item.channel,
                 action='live',
                 thumbnail=support.thumb('tvshow_on_the_air')),
            Item(channel=item.channel,
                     title=config.get_setting("film1", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("film2", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/premium/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("film3", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-intrattenimento/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("film4", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-cinema/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("film5", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-primafila/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now1", channel="filmontv"),
                     action="now_on_misc",
                     url="%s/ora-in-onda/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now2", channel="filmontv"),
                     action="now_on_misc",
                     url="%s/ora-in-onda/premium/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now3", channel="filmontv"),
                     action="now_on_misc",
                     url="%s/ora-in-onda/sky-intrattenimento/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now4", channel="filmontv"),
                     action="now_on_misc",
                     url="%s/ora-in-onda/sky-doc-e-lifestyle/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now5", channel="filmontv"),
                     action="now_on_misc_film",
                     url="%s/ora-in-onda/sky-cinema/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                    title="Personalizza Oggi in TV",
                    action="server_config",
                    config="filmontv",
                    folder=False,
                    thumbnail=item.thumbnail)]

    return itemlist

def server_config(item):
    return platformtools.show_channel_settings(channelpath=filetools.join(config.get_runtime_path(), "specials", item.config))

def now_on_misc_film(item):
    logger.debug("filmontv tvoggi")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    patron = r'table-cell[;" ]*alt="([^"]+)".*?backdrop" alt="([^"]+)"[ ]*src="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedchannel, scrapedtitle, scrapedthumbnail in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        #infoLabels["year"] = ""
        infoLabels['title'] = "movie"
        itemlist.append(
            Item(channel=item.channel,
                 action="new_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel,
                 fulltitle=scrapedtitle,
                 mode='all',
                 search_text=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail.replace("?width=320", "?width=640"),
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def now_on_misc(item):
    logger.debug("filmontv tvoggi")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    patron = r'table-cell[;" ]*alt="([^"]+)".*?backdrop" alt="([^"]+)"[ ]*src="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedchannel, scrapedtitle, scrapedthumbnail in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = ""
        infoLabels['tvshowtitle'] = scrapedtitle
        itemlist.append(
            Item(channel=item.channel,
                 action="new_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'tvshow',
                 title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel,
                 fulltitle=scrapedtitle,
                 mode='all',
                 search_text=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail.replace("?width=320", "?width=640"),
                 contentTitle=scrapedtitle,
                 contentType='tvshow',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def now_on_tv(item):
    logger.debug("filmontv tvoggi")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data.replace('\n','')
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    patron = r'<img class="sgtvfullfilmview_logo[^>]+alt="([^"]+)".*?spanMovieDuration">([^<]+).*?spanTitleMovie">([^<]+).*?GenresMovie">([^<]*).*?data-src="([^"]+).*?Year">[^<]+([0-9]{4})'
    matches = re.compile(patron, re.DOTALL).findall(data)
    # support.regexDbg(item, patron, {}, data)
    for scrapedchannel, scrapedduration, scrapedtitle, scrapedgender, scrapedthumbnail, scrapedyear in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = scrapedyear
        itemlist.append(
            Item(channel=item.channel,
                 action="new_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel + " - " + scrapedduration,
                 fulltitle="[B]" + scrapedtitle + "[/B] - " + scrapedchannel+ " - " + scrapedduration,
                 url=scrapedurl,
                 mode='all',
                 search_text=scrapedtitle,
                 thumbnail=scrapedthumbnail.replace("?width=240", "?width=480"),
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def primafila(item):
    logger.debug("filmontv tvoggi")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ]*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?=]*)'
    patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedtitle, scrapedgender, scrapedthumbnail, scrapedyear in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = scrapedyear
        itemlist.append(
            Item(channel=item.channel,
                 action="new_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 mode='all',
                 search_text=scrapedtitle,
                 thumbnail=scrapedthumbnail.replace("?width=240", "?width=480"),
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def new_search(item):
    from specials import search
    return search.new_search(item)


def live(item):
    import sys
    import channelselector

    if sys.version_info[0] >= 3: from concurrent import futures
    else: from concurrent_py2 import futures

    itemlist = []
    channels_dict = {}
    channels = channelselector.filterchannels('live')

    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(load_live, ch.channel) for ch in channels]
        for res in futures.as_completed(itlist):
            if res.result():
                channel_name, itlist = res.result()
                channels_dict[channel_name] = itlist

    # default order
    channel_list = ['raiplay', 'mediasetplay', 'la7', 'discoveryplus']

    # add channels not in list
    for ch in channels:
        if ch.channel not in channel_list:
            channel_list.append(ch.channel)

    # make itemlist
    for ch in channel_list:
        itemlist += channels_dict[ch]
    itemlist.sort(key=lambda it: support.channels_order.get(it.fulltitle, 1000))
    return itemlist


def load_live(channel_name):
    try:
        channel = __import__('%s.%s' % ('channels', channel_name), None, None, ['%s.%s' % ('channels', channel_name)])
        itemlist = channel.live(channel.mainlist(Item())[0])
    except:
        itemlist = []
    return channel_name, itemlist
