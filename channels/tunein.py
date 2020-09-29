# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione01
# ------------------------------------------------------------

from core import support
from core.item import Item
from platformcode import config
from xml.dom import minidom

#impostati dinamicamente da findhost()


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
            item.clone(title=support.typo('Cerca...', 'bold color kod'), action='search', thumbnail=support.thumb('search')))
        support.channel_config(item, itemlist)
        return itemlist
    return locals()


def radio(item):
    support.info()
    itemlist = []
    data = support.match(item, patron= r'text="(?P<title>[^\("]+)(?:\((?P<location>[^\)]+)\))?" URL="(?P<url>[^"]+)" bitrate="(?P<quality>[^"]+)" reliability="[^"]+" guide_id="[^"]+" subtext="(?P<song>[^"]+)" genre_id="[^"]+" formats="(?P<type>[^"]+)" (?:playing="[^"]+" )?(?:playing_image="[^"]+" )?(?:show_id="[^"]+" )?(?:item="[^"]+" )?image="(?P<thumb>[^"]+)"')
    if data.matches:
        for title, location, url, quality, song, type, thumbnail in data.matches:
            itemlist.append(
                item.clone(title = support.typo(title, 'bold') + support.typo(quality + ' kbps','_ [] bold color kod'),
                           thumbnail = thumbnail,
                           url = url,
                           contentType = 'music',
                           plot = support.typo(location, 'bold') + '\n' + song,
                           action = 'findvideos'))
    else:
        matches = support.match(data.data, patron= r'text="(?P<title>[^\("]+)(?:\([^\)]+\))?" URL="(?P<url>[^"]+)" (?:guide_id="[^"]+" )?(?:stream_type="[^"]+" )?topic_duration="(?P<duration>[^"]+)" subtext="(?P<plot>[^"]+)" item="[^"]+" image="(?P<thumb>[^"]+)"').matches
        if matches:
            for title, url, duration, plot, thumbnail in matches:
                infoLabels={}
                infoLabels['duration'] = duration
                itemlist.append(
                    item.clone(title = support.typo(title, 'bold'),
                               thumbnail = thumbnail,
                               infolLbels = infoLabels,
                               url = url,
                               contentType = 'music',
                               plot = plot,
                               action = 'findvideos'))
        else:
            matches = support.match(data.data, patron= r'text="(?P<title>[^"]+)" URL="(?P<url>[^"]+)"').matches
            for title, url in matches:
                itemlist.append(
                    item.clone(channel = item.channel,
                               title = support.typo(title, 'bold'),
                               thumbnail = item.thumbnail,
                               url = url,
                               action = 'radio'))
    return itemlist


def findvideos(item):
    import xbmc
    itemlist = []
    item.action = 'play'
    urls = support.match(item.url).data.strip().split()
    for url in urls:
        item.url= url
        item.server = 'directo'
        itemlist.append(item)
    return itemlist


def search(item, text):
    support.info(text)
    item.url = host + '/Search.ashx?query=' +text
    try:
        return radio(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []
