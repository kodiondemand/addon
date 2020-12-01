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
    tvshow = ['/lista-serie-tv/']
    anime =['/lista-anime-2/',
               ('Sub-Ita',['/lista-anime-sub-ita/', 'peliculas', 'sub']),
               ('Film Animati',['/lista-film-animazione/','peliculas', '', 'movie'])]
    search = ''
    return locals()


def search(item, text):
    support.info(text)
    # item.args='search'
    item.text = text
    itemlist = []
    
    try:
        # item.url = host + '/lista-serie-tv/'
        # item.contentType = 'tvshow'
        # itemlist += peliculas(item)
        with futures.ThreadPoolExecutor() as executor:
            for par in [['/lista-serie-tv/', 'tvshow', ''],['/lista-anime-2/', 'tvshow', ''], ['/lista-anime-sub-ita/', 'tvshow', 'sub'], ['/lista-film-animazione/', 'movie', '']]:
                item.url = host + par[0]
                item.contentType = par[1]
                item.args = par[2]
                itemlist += executor.submit(peliculas, item).result()
        return itemlist
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
    search = item.text
    pagination = ''
    anime = True
    action = 'findvideos' if item.contentType == 'movie' else 'episodios'
    blacklist = ['-Film Animazione disponibili in attesa di recensione ']

    if item.args == 'search':
        action = 'check'
        data = support.match(item).data.replace('\\','')
        patron = r'"title":"(?P<title>[^"]+)","url":"(?P<url>[^"]+)'
    elif item.args == 'last':
        patronBlock = 'Aggiornamenti</h2>(?P<block>.*)</ul>'
        patron = r'<a href="(?P<url>[^"]+)">\s*<img[^>]+src(?:set)?="(?P<thumbnail>[^ ]+)[^>]+>\s*<span[^>]+>(?P<title>[^<]+)'
    elif item.args == 'new':
        patronBlock = '<main[^>]+>(?P<block>.*)</main>'
        patron = r'<a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>[^>]+>[^>]+>[^>]+><img.*?src="(?P<thumb>[^"]+)".*?<p>(?P<plot>[^<]+)</p>.*?<span class="cat-links">Pubblicato in.*?.*?(?P<type>(?:[Ff]ilm|</artic))[^>]+>'
        patronNext = '<a class="next page-numbers" href="([^"]+)">'
        typeContentDict={'movie':['film']}
        typeActionDict={'findvideos':['film']}
    else:
        patronBlock = '"lcp_catlist"[^>]+>(?P<block>.*)</ul>'
        patron = r'<li ><a href="(?P<url>[^"]+)" title="[^>]+">(?P<title>[^<|\(]+)?(?:\([^\d]*(?P<year>\d+)\))?[^<]*</a>'

    def itemHook(item):
        support.info(item.title)
        item.title = support.re.sub(' (?:- )?[Ss]erie [Tt][Vv]', '', item.title)
        if item.args == 'sub':
            #corregge l'esatta lang per quelle pagine in cui c'è
            #solo sub-ita
            item.title = item.title.replace('[ITA]','[Sub-ITA]')
            item.contentLanguage = 'Sub-ITA'
        return item
    return locals()

def check(item):
    if support.match(item, headers=headers, patron=r'(category tag">Film)').match:
        item.contentType = 'movie'
        return findvideos(item)
    else:
        item.contentType = 'tvshow'
        return episodios(item)

@support.scrape
def episodios(item):
    anime = True
    data = support.match(item, headers=headers).data
    if 'https://vcrypt.net' in data:
        patron = r'(?: /> |<p>)(?P<episode>\d+.\d+)?(?: &#8211; )?(?P<title>[^<]+)<a (?P<url>.*?)(?:<br|</p)'
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
    return support.server(item, item.url if item.contentType != 'movie' else support.httptools.downloadpage(item.url, headers=headers).data )
