# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione01
# ------------------------------------------------------------

from core import support

host = 'https://metalvideo.com'
headers = {'X-Requested-With': 'XMLHttpRequest'}


@support.scrape
def mainlist(item):
    item.url = host
    action = 'peliculas'
    patronBlock = r'<ul class="dropdown-menu(?P<block>.*?)</ul>\s*</div'
    patron = r'<a href="(?P<url>[^"]+)"(?: class="")?>(?P<title>[^<]+)<'
    def itemHook(item):
        item.thumbnail = support.thumb('music')
        item.contentType = 'music'
        return item
    def itemlistHook(itemlist):
        itemlist.pop(0)
        itemlist.append(
            support.Item(
                channel=item.channel,
                title=support.typo('Cerca...', 'bold'),
                contentType='music',
                url=item.url,
                action='search',
                thumbnail=support.thumb('search')))

        support.channel_config(item, itemlist)
        return itemlist
    return locals()

@support.scrape
def peliculas(item):
    action = 'findvideos'
    patron= r'<img src="[^"]+" alt="(?P<title>[^"]+)" data-echo="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)"'
    patronNext = r'<a href="([^"]+)">&raquo'
    typeContentDict = {'': 'music'}
    return locals()


def findvideos(item):
    return support.server(item, Videolibrary=False)


def search(item, text):
    support.info(text)
    item.url = host + '/search.php?keywords=' + text + '&video-id='
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []
