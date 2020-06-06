# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ToonItalia
# ------------------------------------------------------------

from core import support

host = support.config.get_channel_url()

headers = [['Referer', host]]

list_servers = ['wstream', 'openload', 'streamango']
list_quality = ['HD', 'default']


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


def search(item, texto):
    support.log(texto)
    item.args='search'
    item.contentType='tvshow'
    item.url = host + '/?s=' + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def newest(categoria):
    support.log(categoria)
    item = support.Item()
    try:
        item.contentType = 'tvshow'
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
    pagination = ''
    anime = True
    # debug = True
    blacklist = ['-Film Animazione disponibili in attesa di recensione ']

    if item.args == 'search':
        patron = r'<h2 class="entry-title"><a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>.*?<p>(?P<plot>[^<]+)</p>.*?<span class="cat-links">Pubblicato in.*?.*?(?P<type>(?:[Ff]ilm|</artic))[^>]+>'
        typeContentDict={'movie':['film']}
        typeActionDict={'findvideos':['film']}
        patronNext = r'<a href="([^"]+)"\s*>Articoli meno recenti'
    elif item.args == 'last':
        patronBlock = 'Aggiornamenti</h2>(?P<block>.*)</ul>'
        patron = r'<a href="(?P<url>[^"]+)">\s*<img[^>]+src(?:set)?="(?P<thumbnail>[^ ]+)[^>]+>\s*<span[^>]+>(?P<title>[^<]+)'
    # elif item.args == 'most_view':
    #     patronBlock = 'I piu visti</h2>(?P<block>.*)</ul>'
    #     patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)"'
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
        support.log(item.title)
        item.title = support.re.sub(' (?:- )?[Ss]erie [Tt][Vv]', '', item.title)
        if item.args == 'sub':
            #corregge l'esatta lang per quelle pagine in cui c'è
            #solo sub-ita
            item.title = item.title.replace('[ITA]','[Sub-ITA]')
            item.contentLanguage = 'Sub-ITA'
        return item

    action = 'findvideos' if item.contentType == 'movie' else 'episodios'

    return locals()


@support.scrape
def episodios(item):
    anime = True
    data = support.match(item, headers=headers).data
    if 'https://vcrypt.net' in data:
        patron = r'(?: /> |<p>)(?P<title>[^<]+)<a (?P<url>.*?)(?:<br|</p)'
    else:
        patron = r'<br />\s*<a href="(?P<url>[^"]+)" target="_blank" rel="noopener[^>]+>(?P<title>[^<]+)</a>'

    def itemHook(item):
        item.title = support.re.sub(r'\[B\]|\[/B\]', '', item.title)
        item.title = item.title.replace('_',' ').replace('–','-').replace('&#215;','x').replace('-','-').replace('  ',' ')
        item.title = support.re.sub(item.fulltitle + ' - ','',item.title)
        item.title = support.typo(item.title.strip(' -'),'bold')
        return item

    return locals()


def findvideos(item):
    return support.server(item, item.url if item.contentType != 'movie' else support.httptools.downloadpage(item.url, headers=headers).data )
