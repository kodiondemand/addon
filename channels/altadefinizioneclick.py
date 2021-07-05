# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizioneclick
# ----------------------------------------------------------
"""

    Eccezioni che non superano il test del canale:
       - indicare le eccezioni

    Novità. Indicare in quale/i sezione/i è presente il canale:
       - film
    
    Avvisi:
        - Eventuali avvisi per i tester

    Ulteriori info:


"""
from platformcode.logger import debug
from core import support
from core.item import Item
from platformcode import config

def findhost(url):
    data = support.httptools.downloadpage(url).data
    host = support.scrapertools.find_single_match(data, '<div class="elementor-button-wrapper">\s*<a href="([^"]+)"')
    return host

host = config.get_channel_url(findhost)
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = ['',
        ('Novità', ['/nuove-uscite/', 'peliculas', 'news']),
        ('Al Cinema', ['/al-cinema/', 'peliculas', 'cinema']),
        ('A-Z',['/lista-film/', 'genres', 'az']),
        ('Generi', ['', 'genres', 'genres']),
        ('Anni', ['', 'genres', 'years']),
        ('Qualità', ['', 'genres', 'quality']),
        ('Mi sento Fortunato',[ '', 'genres', 'lucky']),
        ('Sub-ITA', ['/sub-ita/', 'peliculas', 'sub'])
    ]

    tvshow = ['/serie-tv/']

    search = ''
    return locals()

@support.scrape
def peliculas(item):
    action = 'check'

    patron = r'<div class="wrapperImage">\s*(?:<span class="year">(?P<year>[^<]+)[^>]+>)?(?:<span class="hd">(?P<quality>[^<>]+))?.+?href="(?P<url>[^"]+)".+?src="(?P<thumb>[^"]+)".+?<h2 class="titleFilm">[^>]+>(?P<title>.+?)[ ]?(?:|\[(?P<lang>[^\]]+)\])?</a>.*?(?:IMDB\:</strong>[ ](?P<rating>.+?)<|</div>)'

    if item.args == 'az':
        patron = r'<img style="[^"]+" src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)" [^>]+>(?P<title>[^<\[]+)(?:\[(?P<lang>[^\]]+)\]\s*)?<'\
                 r'[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<year>\d{4})[^>]+>[^>]+>\s*(?P<quality>[^<]+).*?<span class="label">(?P<ratting>[^<]+)<'
        patronBlock =''

    elif item.args == 'search':
        patronBlock = r'<section id="lastUpdate">(?P<block>.*?)(?:<div class="row ismobile">|<section)'
        patron = r'<a href="(?P<url>[^"]+)">\s*<div class="wrapperImage">(?:\s*<span class="year">(?P<year>[^<]+)<\/span>)?(?:\s*<span class="hd">(?P<quality>[^<]+)<\/span>)?[^>]+>\s*<img[^s]+src="(?P<thumb>[^"]+)"(?:(?:[^>]+>){5}\s*(?P<rating>[^<]+))?(?:[^>]+>){4}(?P<title>[^<]+)'

    if not item.args:
        patronBlock = r'(?:ULTIMI INSERITI|Serie TV)(?P<block>.*?)</section'

    # nella pagina "CERCA", la voce "SUCCESSIVO" apre la maschera di inserimento dati
    patronNext = r'<a class="next page-numbers" href="([^"]+)">'

    return locals()

@support.scrape
def genres(item):
    action = 'peliculas'
    patronMenu = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'

    if item.args == 'genres':
        patronBlock = r'<ul class="listSubCat" id="Film">(?P<block>.*)<ul class="listSubCat" id="Anno">'
    elif item.args == 'years':
        patronBlock = r'<ul class="listSubCat" id="Anno">(?P<block>.*)<ul class="listSubCat" id="Qualita">'
    elif item.args == 'quality':
        patronBlock = r'<ul class="listSubCat" id="Qualita">(?P<block>.*)</li>\s*?</ul>\s*?</div>\s*?</div>\s*?</div>\s*?<a'
    elif item.args == 'lucky': # sono i titoli random nella pagina
        patronBlock = r'<h3 class="titleSidebox dado">FILM RANDOM</h3>(?P<block>.*)</section>'
        patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<[]+)(?:\[(?P<lang>.+?)\])?<'
        action = 'findvideos'
    elif item.args == 'az':
        blacklist = ['FILM 4K IN STREAMING']
        patron = r'<a title="(?P<title>[^"]+)" href="(?P<url>[^"]+)"'
        item.args = 'az'
    if not item.args == 'az':
        item.args = 'genres'

    return locals()

def search(item, texto):
    support.info("search ", texto)

    item.args = 'search'
    item.url = host + "?s=" + texto
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
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.args = 'news'
            item.contentType = 'movie'
            item.url = host + "/nuove-uscite/"
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            from platformcode import logger
            logger.error("{0}".format(line))
        return []

    return itemlist


def check(item):
    def get_season(pageData, seas_url, season):
        data = ''
        episodes = support.match(pageData if pageData else seas_url, patronBlock=patron_episode, patron=patron_option).matches
        for episode_url, episode in episodes:
            # episode_url = support.urlparse.urljoin(item.url, episode_url)
            # if '-' in episode: episode = episode.split('-')[0].zfill(2) + 'x' + episode.split('-')[1].zfill(2)
            title = season + "x" + episode.zfill(2) + ' - ' + item.fulltitle
            data += title + '|' + episode_url + '\n'
        return data

    patron_season = '<div class="[^"]+" id="seasonsModal"[^>]+>(.*?)</ul>'
    patron_episode = '<div class="[^"]+" id="episodesModal"[^>]+>(.*?)</ul>'
    patron_option = r'<a href="([^"]+?)".*?>(?:Stagione |Episodio )([^<]+?)</a>'

    url = support.match(item, patron=r'<iframe id="iframeVid" width="[^"]+" height="[^"]+" src="([^"]+)" allowfullscreen').match
    seasons = support.match(url, patronBlock=patron_season, patron=patron_option)
    if not seasons.match:
        item.contentType = 'tvshow'
        return findvideos(item)

    data = ''

    import sys
    if sys.version_info[0] >= 3: from concurrent import futures
    else: from concurrent_py2 import futures
    with futures.ThreadPoolExecutor() as executor:
        thL = []
        for i, season in enumerate(seasons.matches):
            thL.append(executor.submit(get_season, seasons.data if i == 0 else '', season[0], season[1]))
        for res in futures.as_completed(thL):
            if res.result():
                data += res.result()
    item.data = data
    return episodios(item)

@support.scrape
def episodios(item):
    data = item.data

    patron = r'(?P<season>\d+)x(?P<episode>\d+)\s*-\s*(?P<title>[^\|]+)\|(?P<url>[^ ]+)'
    action = 'findvideos'

    def itemlistHook(itemlist):
        itemlist.sort(key=lambda item: (item.infoLabels['season'], item.infoLabels['episode']))
        return itemlist

    return locals()

def findvideos(item):
    support.info('findvideos', item)
    return support.hdpass_get_servers(item)

def play(item):
    if 'hdpass' in item.url:
        return support.hdpass_get_url(item)
    return [item]
