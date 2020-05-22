# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per SerieHD
# ------------------------------------------------------------


from core import support

host = support.config.get_channel_url()
headers = [['Referer', host]]


list_servers = ['mixdrop', 'vidoza', 'vcstream', 'gounlimited']
list_quality = ['1080p', '720p', '480p', '360']

@support.menu
def mainlist(item):

    tvshow = [('Genere', ['', 'menu', 'genre']),
              ('A-Z', ['', 'menu', 'a-z']),
              ('In Corso', ['/category/serie-tv-streaming/serie-in-corso', 'peliculas']),
              ('Complete', ['/category/serie-tv-streaming/serie-complete', 'peliculas']),
              ('Americane', ['/category/serie-tv-streaming/serie-tv-americane', 'peliculas']),
              ('Italiane', ['/category/serie-tv-streaming/serie-tv-italiane', 'peliculas']),
              ('Ultimi Episodi', ['/aggiornamenti', 'peliculas', 'last']),
              ('Evidenza', ['', 'peliculas', 'best'])]
    return locals()


def search(item, texto):
    support.log(texto)


    item.contentType = 'tvshow'
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def newest(categoria):
    support.log(categoria)

    itemlist = []
    item = support.Item()
    item.url = host + '/aggiornamenti'
    item.args = 'last'
    try:
        if categoria == "series":
            item.contentType = 'tvshow'
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist


@support.scrape
def peliculas(item):
    if item.args == 'last':
        action = 'findvideos'
        patron = r'singleUpdate">[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>\s*<h2>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>\s*(?P<season>\d+)\D+(?P<episode>\d+)(?:[^\(]*\()?(?P<lang>[^\)]+)?(?:\))?'
    elif item.args == 'best':
        action='episodios'
        patron = r'col-md-3">\s*<a href="(?P<url>[^"]+)">[^>]+>\s*<div class="infoVetrina">[^>]+>(?P<year>\d{4})[^>]+>[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)[^>]+>[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"'
    else:
        action='episodios'
        patron = r'<a href="(?P<url>[^"]+)">[^>]+>\s*<div class="infoSeries">\s*<h2>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)?[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>(?P<year>\d{4})'
        patronNext=r'next page-numbers" href="([^"]+)"'

    return locals()


@support.scrape
def episodios(item):
    def get_season(pageData, seas_url, season):
        data = ''
        episodes = support.match(pageData if pageData else seas_url, patronBlock=patron_episode, patron=patron_option).matches
        for episode_url, episode in episodes:
            episode_url = support.urlparse.urljoin(item.url, episode_url)
            if '-' in episode: episode = episode.split('-')[0].zfill(2) + 'x' + episode.split('-')[1].zfill(2)
            title = season + "x" + episode.zfill(2) + ' - ' + item.fulltitle
            data += title + '|' + episode_url + '\n'
        return data

    patron_season = '<div class="buttons-bar seasons">(.*?)<div class="buttons'
    patron_episode = '<div class="buttons-bar episodes">(.*?)<div class="buttons'
    patron_option = r'<a href="([^"]+?)".*?>([^<]+?)</a>'

    url = support.match(item, patron=r'<iframe id="iframeVid" width="[^"]+" height="[^"]+" src="([^"]+)" allowfullscreen').match
    seasons = support.match(url, patronBlock=patron_season, patron=patron_option)

    data = ''
    import sys
    if sys.version_info[0] >= 3:
        from concurrent import futures
    else:
        from concurrent_py2 import futures
    with futures.ThreadPoolExecutor() as executor:
        thL = []
        for i, season in enumerate(seasons.matches):
            thL.append(executor.submit(get_season, seasons.data if i == 0 else '', season[0], season[1]))
        for res in futures.as_completed(thL):
            if res.result():
                data += res.result()

    patron = r'(?P<title>[^\|]+)\|(?P<url>[^\n]+)\n'
    action = 'findvideos'

    def itemlistHook(itemlist):
        itemlist.sort(key=lambda item: int(support.re.sub(r'\[[^\]]+\]','',item.title).split('x')[0]))
        return itemlist

    return locals()


@support.scrape
def menu(item):
    if item.args == 'genre':
        patronMenu = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>'
    else:
        patronMenu = r'<a href="(?P<url>[^"]+)" class="">(?P<title>[^<]+)'

    blacklist = ['Serie TV Streaming','Serie TV Americane','Serie TV Italiane','Serie Complete','Serie in Corso','altadefinizione']
    action = 'peliculas'
    return locals()


def findvideos(item):
    item.url = item.url.replace('&amp;', '&')
    support.log(item)
    if item.args == 'last':
        url = support.match(item, patron = r'<iframe id="iframeVid" width="[^"]+" height="[^"]+" src="([^"]+)" allowfullscreen').match
        matches = support.match(url,patron=r'<a href="([^"]+)">(\d+)<', patronBlock=r'<h3>EPISODIO</h3><ul>(.*?)</ul>').matches
        if matches: item.url = support.urlparse.urljoin(url, matches[-1][0])
    return support.hdpass_get_servers(item)

def play(item):
    return support.hdpass_get_url(item)