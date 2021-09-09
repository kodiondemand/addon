# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per tunein
# ------------------------------------------------------------

from core import scrapertools, support, config
from platformcode import logger

host = 'http://api.radiotime.com'
headers = [['Referer', host]]


@support.scrape
def mainlist(item):
    item.url = host
    action = 'radio'
    patron = r'text="(?P<title>[^"]+)" URL="(?P<url>[^"]+)"'
    def itemHook(item):
        item.thumbnail = support.thumb('music')
        item.contentType = 'music'
        return item
    def itemlistHook(itemlist):
        itemlist.append(
            item.clone(title=support.typo(config.get_localized_string(70741) % 'Musica… ', 'bold'), action='search', thumbnail=support.thumb('search')))
        support.channel_config(item, itemlist)
        return itemlist
    return locals()


def radio(item):
    logger.debug()
    itemlist = []
    data = support.match(item, patron= r'text="(?P<title>[^\("]+)(?:\((?P<location>[^\)]+)\))?" URL="(?P<url>[^"]+)" bitrate="(?P<quality>[^"]+)" reliability="[^"]+" guide_id="[^"]+" subtext="(?P<song>[^"]+)" genre_id="[^"]+" formats="(?P<type>[^"]+)" (?:playing="[^"]+" )?(?:playing_image="[^"]+" )?(?:show_id="[^"]+" )?(?:item="[^"]+" )?image="(?P<thumb>[^"]+)"')
    if data.matches:
        for title, location, url, quality, song, type, thumbnail in data.matches:
            title = scrapertools.decodeHtmlentities(title)
            itemlist.append(
                item.clone(contentTitle = title,
                           quality= quality, 
                           thumbnail = thumbnail,
                           url = url,
                           contentType = 'music',
                           plot = support.typo(location, 'bold') + '\n' + song,
                           action = 'findvideos'))
    else:
        matches = support.match(data.data, patron= r'text="(?P<title>[^\("]+)(?:\([^\)]+\))?" URL="(?P<url>[^"]+)" (?:guide_id="[^"]+" )?(?:stream_type="[^"]+" )?topic_duration="(?P<duration>[^"]+)" subtext="(?P<plot>[^"]+)" item="[^"]+" image="(?P<thumb>[^"]+)"').matches
        if matches:
            for title, url, duration, plot, thumbnail in matches:
                title = scrapertools.unescape(title)
                infoLabels={}
                infoLabels['duration'] = duration
                itemlist.append(
                    item.clone(contentTitle = title,
                               thumbnail = thumbnail,
                               infolLbels = infoLabels,
                               url = url,
                               contentType = 'music',
                               plot = plot,
                               action = 'findvideos'))
        else:
            matches = support.match(data.data, patron= r'text="(?P<title>[^"]+)" URL="(?P<url>[^"]+)"').matches
            for title, url in matches:
                title = scrapertools.unescape(title)
                itemlist.append(
                    item.clone(channel = item.channel,
                               contentTitle = title,
                               thumbnail = item.thumbnail,
                               url = url,
                               action = 'radio'))
    support.nextPage(itemlist, item, data=data.data, patron=r'(?P<url>[^"]+)" key="nextStations')
    return itemlist


def findvideos(item):
    import xbmc
    itemlist = []
    item.action = 'play'
    urls = support.match(item.url).data.strip().split()
    for url in urls:
        item.title = 'TuneIn'
        item.url= url
        item.server = 'directo'
        itemlist.append(item)
    return support.server(item, itemlist=itemlist)


def search(item, text):
    logger.debug(text)
    item.url = host + '/Search.ashx?query=' +text
    try:
        return radio(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
