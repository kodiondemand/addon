# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ToonItalia
# ------------------------------------------------------------

from core import support
import sys
if sys.version_info[0] >= 3: from concurrent import futures
else: from concurrent_py2 import futures

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
    item.url = item.url + '/?%73=' + text.replace(' ', '+')

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

    if search:
        pagination = ''
        #patronBlock = '"lcp_catlist"[^>]+>(?P<block>.*)</ul>'
        patronBlock = '<main[^>]+>(?P<block>.*?)</ma'
        #patron = r'href="(?P<url>[^"]+)" title="(?P<title>[^"]+)"'
        patron = r'<a href="(?P<url>[^"]+)"[^>]*>(?P<title>[^<]+)<[^>]+>[^>]+><div'
    elif item.args == 'last':
        patronBlock = 'Aggiornamenti</h2>(?P<block>.*)</ul>'
        patron = r'<a href="(?P<url>[^"]+)">\s*<img[^>]+src[set]{0,3}="(?P<thumbnail>[^ ]+)[^>]+>\s*<span[^>]+>(?P<title>[^<]+)'
    else:
        patronBlock = '<main[^>]+>(?P<block>.*)</main>'
        # patron = r'<a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>[^>]+>[^>]+>[^>]+><img.*?src="(?P<thumb>[^"]+)".*?<p>(?P<plot>[^<]+)</p>.*?<span class="cat-links">Pubblicato in.*?.*?(?P<type>(?:[Ff]ilm|</artic))[^>]+>'
        patron = r'<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)</a>[^>]+>[^>]+>[^>]+><img.*?src="(?P<thumb>[^"]+)".*?<p>(?P<plot>[^<]+)</p>.*?tag">.*?(?P<type>(?:[Ff]ilm|</art|Serie Tv))'
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
    data = support.match(item, headers=headers).data
    if 'https://vcrypt.net' in data:
        patron = r'(?: /> |<p>)(?P<episode>\d+.\d+)?(?: &#8211; )?(?P<title>[^<]+)<a (?P<data>.*?)(?:<br|</p)'
    else:
        patron = r'<br />\s*<a href="(?P<url>[^"]+)" target="_blank" rel="noopener[^>]+>(?P<episode>\d+.\d+)?(?: &#8211; )?(?P<title>[^<]+)</a>'

    def itemHook(item):
        item.title = support.re.sub(r'\[B\]|\[/B\]', '', item.title)
        item.title = item.title.replace('_',' ').replace('–','-').replace('&#215;','x').replace('-','-').replace('  ',' ')
        item.title = support.re.sub(item.fulltitle + ' - ','',item.title)
        item.title = support.typo(item.title.strip(' -'),'bold')
        return item

    return locals()


def findvideos(item):
    return support.server(item, item.data if item.contentType != 'movie' else support.match(item.url, headers=headers).data )
