# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Plugin
# Canale  per cineblog01 - anime
# ------------------------------------------------------------

from core import support

host = support.config.get_channel_url() + '/cb01-anime-cartoon'

Blacklist = ['AVVISO IMPORTANTE – CB01.ROCKS', 'Lista Alfabetica Completa Anime/Cartoon', 'CB01.UNO ▶ TROVA L’INDIRIZZO UFFICIALE','Lista Richieste Up &amp; Re-Up']


headers = [['Referer', host]]

@support.menu
def mainlist(item):
    anime = [('Genere',['','menu', '2']),
             ('Per Lettera',['','menu', '1']),
             ('Per Anno',['','menu', '3']),
             ('Ultimi Anime Aggiornati',['','peliculas', 'newest'])]
    return locals()


@support.scrape
def menu(item):
    blacklist = ['Anime per Genere', 'Anime per Anno', 'Anime per Lettera']
    patronBlock = r'<select name="select%s"(?P<block>.*?)</select>' % item.args
    patronMenu = r'<option value="(?P<url>[^"]+)">(?P<title>[^<]+)</option>'
    action = 'peliculas'
    def itemHook(item):
        item.url = item.url.replace('cb01-anime/','cb01-anime-cartoon/')
        return item
    return locals()


def search(item, texto):
    support.info(texto)
    item.url = host + "/search/" + texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            support.info('search log:', line)
        return []


def newest(categoria):
    support.info(categoria)
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host
            item.args = 'newest'
            itemlist = peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist

@support.scrape
def peliculas(item):
    # debug=True
    blacklist = Blacklist
    item.contentType = 'tvshow'
    if item.args == 'newest':
        patron = r'<div id="blockvids">\s*<ul>\s*<li>\s*<a href="(?P<url>[^"]+)"[^>]+><img[^>]+src="(?P<thumb>[^"]+)"[^>]*>(?:[^>]+>){4}(?P<title>[^\[]+)\[(?P<lang>[^\]]+)\]'
    else:
        patron = r'<div class="span4">\s*<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)"[^>]+><\/a>(?:[^>]+>){7}\s*<h1>(?P<title>[^<\[]+)(?:\[(?P<lang>[^\]]+)\])?</h1></a>.*?-->(?:.*?<br(?: /)?>)?\s*(?P<plot>[^<]+)'
        patronNext = r'<link rel="next" href="([^"]+)"'
    action = 'check'
    return locals()

def check(item):
    # support.dbg()
    item.url = support.match(item, patron=r'(?:<p>|/>)(.*?)(?:<br|</td>|</p>)', patronBlock=r'Streaming:(.*?)</tr>').matches
    if 'Episodio' in str(item.url):
        item.contentType = 'tvshow'
        item.action ='episodios'
        return episodios(item)
    else:
        item.contentType = 'movie'
        item.action = 'findvideos'
        return findvideos(item)

@support.scrape
def episodios(item):
    support.info('EPISODIOS ', item.data)
    data = ''
    matches = item.data
    season = 1
    s = 1
    e = 0
    sp = 0

    for match in item.url:
        if 'stagione' in match.lower():
            find_season = support.match(match, patron=r'Stagione\s*(\d+)').match
            season = int(find_season) if find_season else season + 1 if 'prima' not in match.lower() else season
        else:
            try: title = support.match(match, patron=r'<a[^>]+>([^<]+)</a>').match
            except: title = ''
            if title:
                if 'episodio' in title.lower():
                    ep = support.match(match, patron=r'Episodio ((?:\d+.\d|\d+|\D+))').match
                    check = ep.isdigit()
                    if check or '.' in ep:
                        if '.' in ep:
                            sp += 1
                            title = '0' + 'x' + str(sp).zfill(2) + ' - ' + title
                        else:
                            ep = int(ep)
                            if season > s and ep > 1:
                                s += 1
                                e = ep - 1
                            title = str(season) + 'x' + str(ep-e).zfill(2) + ' - ' + title
                        data += title + '|' + match + '\|'
                    else:
                        title += ' #movie'
                        data += title + '|' + match + '\|'
    def itemHook(item):
        if '#movie' in item.title:
            item.contentType='movie'
            item.title = item.title.replace(' #movie','')
        return item

    patron = r'(?P<title>[^\|]+)\|(?P<url>[^\|]+)\|'
    action = 'findvideos'
    return locals()

def findvideos(item):
    return support.server(item, item.url)

