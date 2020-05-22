# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# ----------------------------------------------------------

from core import  support, jsontools

host = support.config.get_channel_url()
headers = [['Referer', host]]

__channel__ = 'animeworld'

list_servers = ['directo', 'animeworld', 'vvvvid']
list_quality = ['default', '480p', '720p', '1080p']


def order():
    # Seleziona l'ordinamento dei risultati
    return str(support.config.get_setting("order", __channel__))


@support.menu
def mainlist(item):
    anime=['/filter?sort=',
           ('ITA',['/filter?language[]=1&sort=', 'menu', '1']),
           ('SUB-ITA',['/filter?language[]=0&sort=', 'menu', '0']),
           ('In Corso', ['/ongoing', 'peliculas','noorder']),
           ('Ultimi Episodi', ['/updated', 'peliculas', 'updated']),
           ('Nuove Aggiunte',['/newest', 'peliculas','noorder' ]),
           ('Generi',['','genres',])]
    return locals()

@support.scrape
def genres(item):
    action = 'peliculas'
    patronBlock = r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> Generi <span.[^>]+>(?P<block>.*?)</ul>'
    patronMenu = r'<input.*?name="(?P<name>[^"]+)" value="(?P<value>[^"]+)"\s*>[^>]+>(?P<title>[^<]+)<\/label>'
    def itemHook(item):
        item.url = host + '/filter?' + item.name + '=' + item.value + '&sort='
        return item
    return locals()


@support.scrape
def menu(item):
    action = 'submenu'
    patronBlock=r'<form class="filters.*?>(?P<block>.*?)</form>'
    patronMenu=r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> (?P<title>.*?) <span.[^>]+>(?P<url>.*?)</ul>'
    def itemlistHook(itemlist):
        item.title = support.typo('Tutti','bold')
        item.action = 'peliculas'
        itemlist.insert(0, item)
        return itemlist
    return locals()


@support.scrape
def submenu(item):
    action = 'peliculas'
    data = item.url
    patronMenu = r'<input.*?name="(?P<name>[^"]+)" value="(?P<value>[^"]+)"\s*>[^>]+>(?P<title>[^<]+)<\/label>'
    def itemHook(item):
        item.url = host + '/filter?' + item.name + '=' + item.value + '&language[]=' + item.args + '&sort='
        return item
    return locals()


def newest(categoria):
    support.log(categoria)
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host + '/updated'
            item.args = "updated"
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


def search(item, texto):
    support.log(texto)
    item.args = 'noorder'
    item.url = host + '/search?keyword=' + texto
    item.contentType = 'tvshow'
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
    anime=True
    if item.args == 'updated':
        item.contentType='episode'
        patron=r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?[^>]+>[^>]+>\s*<div class="ep">[^\d]+(?P<episode>\d+)[^<]*</div>'
        action='findvideos'
    else:
        if item.args != 'noorder' and not item.url[-1].isdigit(): item.url += order() # usa l'ordinamento di configura canale
        patron= r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<year>\d+)\) )?(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>(?:\s*<div class="dub">[^>]+>)?\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?'
        action='episodios'

    # Controlla la lingua se assente
    patronNext=r'href="([^"]+)" rel="next"'
    type_content_dict={'movie':['movie', 'special']}
    type_action_dict={'findvideos':['movie', 'special']}
    check_lang = item.url.replace('%5B0%5D','[]')
    def itemHook(item):
        if not item.contentLanguage:
            if 'language[]=1' in check_lang:
                item.contentLanguage = 'ITA'
                item.title += support.typo(item.contentLanguage,'_ [] color kod')
            else:
                item.contentLanguage = 'Sub-ITA'
                item.title += support.typo(item.contentLanguage,'_ [] color kod')
        return item
    return locals()


@support.scrape
def episodios(item):
    anime=True
    pagination = 50
    data = support.match(item, headers=headers).data
    if 'VVVVID' in data: patronBlock= r'<div class="server\s*active\s*"(?P<block>.*?)</ul>'
    else: patronBlock= r'server  active(?P<block>.*?)server  hidden '
    patron = r'<li><a [^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+" href="(?P<url>[^"]+)"[^>]+>(?P<episode>[^<]+)<'
    def itemHook(item):
        item.number = support.re.sub(r'\[[^\]]+\]', '', item.title)
        item.title += support.typo(item.fulltitle,'-- bold')
        return item
    action='findvideos'
    return locals()


def findvideos(item):
    import time
    support.log(item)
    itemlist = []
    matches = support.match(item, patron=r'data-name="([0-9]+)">', headers=headers)
    data = matches.data
    matches = matches.matches
    videoData = []

    for serverid in matches:
        if not item.number: item.number = support.match(item.title, patron=r'(\d+) -').match
        block = support.match(data, patron=r'data-id="' + serverid + r'">(.*?)<div class="server').match
        ID = support.match(block, patron=r'<a data-id="([^"]+)" data-base="' + (item.number if item.number else '1') + '"').match

        if serverid == '18':
            url = support.match('%s/ajax/episode/serverPlayer?id=%s' % (host, ID), patron=r'source src="([^"]+)"', debug=False).match
            itemlist.append(
                support.Item(
                    channel=item.channel,
                    action="play",
                    title='diretto',
                    quality='',
                    url=url,
                    server='directo',
                    fulltitle=item.fulltitle,
                    contentSerieName=item.contentSerieName,
                    contentTitle=item.contentTitle,
                    show=item.show,
                    contentType=item.contentType,
                    folder=False))

        elif serverid == '26':
            matches = support.match('%s/ajax/episode/serverPlayer?id=%s' % (host, item.url.split('/')[-1]), patron=r'<a href="([^"]+)"', ).matches
            for url in matches:
                videoData.append(url)
        else:
            try:
                dataJson = support.match('%s/ajax/episode/info?id=%s&server=%s&ts=%s' % (host, ID, serverid, int(time.time())), headers=[['x-requested-with', 'XMLHttpRequest']]).data
                json = jsontools.load(dataJson)
                support.log(json)
                videoData.append(json['grabber'])
            except:
                pass


    return support.server(item, videoData, itemlist)

