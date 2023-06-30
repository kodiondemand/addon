# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ToonItalia
# ------------------------------------------------------------

from core import httptools, scrapertools, support
import inspect

host = support.config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    anime =['/category/anime',
            ('ITA',['/lista-anime-ita','peliculas',]),
            ('Sub-ITA',['/lista-anime-sub-ita', 'peliculas'])]
               # ('Film Animati',['/lista-anime-ita','peliculas', '', 'movie'])]
    search = ''
    return locals()


def search(item, text):
    support.info(text)
    # item.args='search'
    item.text = text
    item.url = item.url + '/?a=b&s=' + text.replace(' ', '+')

    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []



@support.scrape
def peliculas(item):
    anime = True
    action = 'check'

    deflang = 'ITA' if 'sub' not in item.url else 'Sub-ITA'
    if 'lista' in item.url:
        pagination = 20
        patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)'

    else:
        patronBlock = '<main[^>]+>(?P<block>.*)</main>'
        patron = r'(?i)<a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>(:?[^>]+>){3}(?:<img.*?src="(?P<thumb>[^"]+)")?.*?<p>(?P<plot>[^<]+)</p>.*?tag">.*?(?P<type>(?:film|serie|anime))(?P<cat>.*?)</span>'
        typeContentDict={'movie':['film']}
        typeActionDict={'findvideos':['film']}
        patronNext = '<a class="next page-numbers" href="([^"]+)">'

    def itemHook(item):
        support.info(item.title)
        if 'sub/ita' in item.cat.lower():
            item.title = item.title.replace('[ITA]', '[Sub-ITA]')
            item.contentLanguage = 'Sub-ITA'
        return item
    return locals()


def check(item):
    itemlist = episodios(item)
    if not itemlist:
        itemlist = findvideos(item)
    return itemlist


@support.scrape
def episodios(item):
    anime = True
    patron = r'>\s*(?:(?P<season>\d+)(?:&#215;|x|×))?(?P<episode>\d+)(?:\s+&#8211;\s+)?[ –]+(?P<title2>[^<]+)[ –]+<a (?P<data>.*?)(?:<br|</p)'
    return locals()


def findvideos(item):
    return support.server(item, data=item.data)


def clean_title(title):
    title = scrapertools.unescape(title)
    title = title.replace('_',' ').replace('–','-').replace('  ',' ')
    title = title.strip(' - ')
    return title
