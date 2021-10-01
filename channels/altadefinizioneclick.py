# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Altadefinizione Click
# ----------------------------------------------------------

from core import support
from platformcode import config, logger

def findhost(url):
    return support.match(url, patron=r'<div class="elementor-button-wrapper">\s*<a href="([^"]+)"').match

host = config.get_channel_url(findhost)
if host.endswith('/'):
        host = host[:-1]
headers = {'Referer': host, 'x-requested-with': 'XMLHttpRequest'}
order = ['', 'i_piu_visti', 'i_piu_votati', 'i_piu_votati_dellultimo_mese', 'titolo_az', 'voto_imdb_piu_alto'][config.get_setting('order', 'altadefinizionecommunity')]


@support.menu
def mainlist(item):
    logger.debug(item)

    film = ['/type/movie',
            ('Generi', ['/type/movie', 'genres', 'genres']),
            ('Anni', ['/type/movie', 'genres', 'year']),]

    tvshow = ['/serie-tv/tvshow',
              ('Generi', ['/serie-tv/tvshow', 'genres', 'genres']),
              ('Anni', ['/serie-tv/tvshow', 'genres', 'year'])]

    return locals()


def search(item, texto):
    logger.debug("search ", texto)

    item.args = 'search'
    item.url = host + "/search?s={}&f={}&page=1".format(texto, item.contentType)
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def genres(item):
    logger.debug(item)
    data = support.httptools.downloadpage(item.url, cloudscraper=True).data
    blacklist= ['Film', 'Serie TV']

    if item.args == 'genres':
        categories ={}
        res = support.match(host + '/cerca', patron=r'for="cat-(\d+)[^>]+>([^<]+)').matches
        for _id, name in res:
            categories[name] = _id

        patronBlock = r'{}<span></span>(?P<block>.*?)</ul>\s*</li'.format('Film' if item.contentType == 'movie' else 'Serie TV')
        patronMenu = r'<a href="[^"]+">(?P<title>[^<]+)'

        def itemHook(it):
            it.cat_id = categories[it.fulltitle]
            return it

    if item.args == 'year':
        patron = r'value="(?P<year_id>[^"]+)"[^>]*>(?P<title>\d+)'
        patronBlock = r'Anno</option>(?P<block>.*?</select>)'

    elif item.args == 'quality':
        patronMenu = r'quality/(?P<quality_id>[^"]+)">(?P<title>[^<]+)'
        patronBlock = r'Risoluzione(?P<block>.*?)</ul>'
    action = 'peliculas'
    return locals()


@support.scrape
def peliculas(item):
    item.quality = 'HD'
    json = {}
    params ={'type':item.contentType, 'anno':item.year_id, 'quality':item.quality_id, 'cat':item.cat_id, 'order':order}


    if item.contentType == 'movie':
        action = 'findvideos'
    else:
        action = 'episodios'
    if not item.page: item.page = 1
    try:
        # support.dbg()
        if item.args in ['search']:
            page = support.httptools.downloadpage(item.url, headers=headers)
            if page.json:
                data = "\n".join(page.json['data'])
            else:
                data = page.data
        else:
            params['page'] = item.page

            url = '{}/load-more-film?{}'.format(host, support.urlencode(params))
            json = support.httptools.downloadpage(url, headers=headers).json
            data = "\n".join(json['data'])
    except:
        data = ' '

    patron = r'wrapFilm">\s*<a href="(?P<url>[^"]+)">[^>]+>(?P<year>\d+)(?:[^>]+>){2}(?P<rating>[^<]+)(?:[^>]+>){4}\s*<img src="(?P<thumb>[^"]+)(?:[^>]+>){3}(?P<title>[^<[]+)(?:\[(?P<lang>[sSuUbBiItTaA-]+))?'
    # patron = r'wrapFilm">\s*<a href="(?P<url>[^"]+)">[^>]+>(?P<year>\d+)(?:[^>]+>){2}(?P<rating>[^<]+)(?:[^>]+>){2}(?P<quality>[^<]+)(?:[^>]+>){2}\s*<img src="(?P<thumb>[^"]+)(?:[^>]+>){3}(?P<title>[^<[]+)(?:\[(?P<lang>[sSuUbBiItTaA-]+))?'

    # paginazione
    if json.get('have_next') or 'have_next_film=true' in data:
        def fullItemlistHook(itemlist):
            cat_id = support.match(data, patron=r''''cat':"(\d+)"''').match
            if cat_id: item.cat_id = cat_id
            item.page += 1
            support.nextPage(itemlist, item, function_or_level='peliculas')
            return itemlist

    return locals()


@support.scrape
def episodios(item):
    logger.debug(item)
    # debug = True
    data = item.data
    patron = r'class="playtvshow "\s+data-href="(?P<url>[^"]+)'

    def itemHook(it):
        spl = it.url.split('/')[-2:]
        it.infoLabels['season'] = int(spl[0])+1
        it.infoLabels['episode'] = int(spl[1])+1
        it.url = it.url.replace('/watch-unsubscribed', '/watch-external')
        it.title = '{}x{:02d} - {}'.format(it.contentSeason, it.contentEpisodeNumber, it.fulltitle)
        return it

    return locals()


def findvideos(item):
    itemlist = []
    playWindow = support.match(item, patron='(?:playWindow|iframe)" (?:href|src)="([^"]+)').match
    if host in playWindow:
        url = support.match(playWindow, patron='allowfullscreen[^<]+src="([^"]+)"').match
    else:
        url = playWindow
    itemlist.append(item.clone(action='play', url=url, quality=''))


    return support.server(item, itemlist=itemlist)
