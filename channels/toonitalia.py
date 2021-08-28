# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ToonItalia
# ------------------------------------------------------------

from core import scrapertools, support
import sys

host = support.config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    top = [('Novità',['', 'peliculas', 'new', 'tvshow']),
           ('Aggiornamenti', ['', 'peliculas', 'last', 'tvshow'])]
    tvshow = ['/category/serie-tv/']
    anime =['/category/anime/',
               ('Sub-Ita',['/category/anime-sub-ita/', 'peliculas', 'sub']),
               ('Film Animati',['/category/film-animazione/','peliculas', '', 'movie'])]
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


def newest(categoria):
    support.info(categoria)
    item = support.Item()
    try:
        item.contentType = 'undefined'
        item.url= host
        item.args= 'new'
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


@support.scrape
def peliculas(item):
    # debugBlock = True
    # debug = True
    # search = item.text
    if item.contentType != 'movie': anime = True
    action = 'findvideos' if item.contentType == 'movie' else 'episodios'
    blacklist = ['-Film Animazione disponibili in attesa di recensione ']

    if item.action == 'search':
        pagination = ''
        #patronBlock = '"lcp_catlist"[^>]+>(?P<block>.*)</ul>'
        patronBlock = '<main[^>]+>(?P<block>.*?)</ma'
        #patron = r'href="(?P<url>[^"]+)" title="(?P<title>[^"]+)"'
        patron = r'<a href="(?P<url>[^"]+)"[^>]*>(?P<title>[^<]+)<[^>]+>[^>]+>\s*<div'
    elif item.args == 'last':
        patronBlock = '(?:Aggiornamenti|Update)</h2>(?P<block>.*?)</ul>'
        patron = r'<a href="(?P<url>[^"]+)">\s*<img[^>]+src[set]{0,3}="(?P<thumbnail>[^ ]+)[^>]+>\s*<span[^>]+>(?P<title>[^<]+)'
    else:
        patronBlock = '<main[^>]+>(?P<block>.*)</main>'
        # patron = r'<a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>[^>]+>[^>]+>[^>]+><img.*?src="(?P<thumb>[^"]+)".*?<p>(?P<plot>[^<]+)</p>.*?<span class="cat-links">Pubblicato in.*?.*?(?P<type>(?:[Ff]ilm|</artic))[^>]+>'
        patron = r'<a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>(:?[^>]+>){3}(?:<img.*?src="(?P<thumb>[^"]+)")?.*?<p>(?P<plot>[^<]+)</p>.*?tag">.*?(?P<type>(?:[Ff]ilm|</art|Serie Tv))'
        typeContentDict={'movie':['film']}
        typeActionDict={'findvideos':['film']}
        patronNext = '<a class="next page-numbers" href="([^"]+)">'

    def itemHook(item):
        support.info(item.title)
        if item.args == 'sub':
            item.title += support.typo('Sub-ITA', 'bold color kod _ []')
            item.contentLanguage = 'Sub-ITA'
        return item
    return locals()


@support.scrape
def episodios(item):
    anime = True
    # debug = True
    patron = r'>\s*(?:(?P<season>\d+)(?:&#215;|x|×))?(?P<episode>\d+)(?:\s+&#8211;\s+)?[ –]+(?P<title2>[^<]+)[ –]+<a (?P<data>.*?)(?:<br|</p)'
    # data = ''
    # match = support.match(item, headers=headers, patron=r'(?: /> |<p>)(?:(?P<season>\d+)&#215;)?(?P<episode>\d+)(?:\s+&#8211;\s+)?(?P<title>[^<]+)<a (?P<data>.*?)(?:<br|</p)').matches
    # if match:
    #     for m in match:
    #         data += '{}{:02d}|{}|{}|'.format(m[0]+'x' if m[0] else '', int(m[1]), clean_title(m[2]), m[3])
    #
    # patron = r'(?P<episode>[^|]+)\|(?P<title>[^|]+)\|(?P<data>[^|]+)\|'

    return locals()


def findvideos(item):
    return support.server(item, item.data if item.contentType != 'movie' else support.match(item.url, headers=headers).data )


def clean_title(title):
    title = scrapertools.unescape(title)
    title = title.replace('_',' ').replace('–','-').replace('  ',' ')
    title = title.strip(' - ')
    return title