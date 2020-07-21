# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# thanks to fatshotty
# ----------------------------------------------------------

from core import support, jsontools
from platformcode import config
from lib import js2py

host = support.config.get_channel_url()
headers = {}

__channel__ = 'animeworld'


def order():
    # Seleziona l'ordinamento dei risultati
    return str(support.config.get_setting("order", __channel__))

def get_data(item, head=[]):
    global headers
    for h in head:
        headers[h[0]] = h[1]
    if not item.count: item.count = 0
    if not config.get_setting('KTVSecurity', item.channel):
        # resolve js for key
        jshe = 'var document = {}, location = {}'
        aesjs = str(support.match(host + '/aes.min.js').data)
        jstr = support.match(item.url, patron=r'<script>(.*?)</').match
        jsret =  'return { key: toHex(slowAES.decrypt(c,2,a,b)), loc: location.href}'
        key_data = js2py.eval_js( 'function (){ ' + jshe + '\n' + aesjs + '\n' + jstr + '\n' + jsret + '}' )
        key = key_data()['key']

        # save Key in settings
        config.set_setting('KTVSecurity', key, item.channel)

    # set cookie
    headers['cookie'] = 'KTVSecurity=' + config.get_setting('KTVSecurity', item.channel)
    res = support.match(item, headers=headers, patron=r'location.href="([^"]+)')
    if res.match: data = support.match(res.match.replace('http://','https://'), headers=headers).data
    else: data = res.data

    #check that the key is still valid
    if 'toHex(slowAES.decrypt(c,2,a,b))' in data and item.count < 3:
        item.count += 1
        config.set_setting('KTVSecurity', '', item.channel)
        return get_data(item)
    return data




@support.menu
def mainlist(item):
    anime=['/filter?sort=',
           ('ITA',['/filter?language[]=1&sort=', 'menu', '1']),
           ('SUB-ITA',['/filter?language[]=0&sort=', 'menu', '0']),
           ('In Corso', ['/ongoing', 'peliculas','noorder']),
           ('Ultimi Episodi', ['/updated', 'peliculas', 'updated']),
           ('Nuove Aggiunte',['/newest', 'peliculas','noorder' ]),
           ('Generi',['/?d=1','genres',])]
    return locals()

@support.scrape
def genres(item):
    action = 'peliculas'
    data = get_data(item)
    patronBlock = r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> Generi <span.[^>]+>(?P<block>.*?)</ul>'
    patronMenu = r'<input.*?name="(?P<name>[^"]+)" value="(?P<value>[^"]+)"\s*>[^>]+>(?P<title>[^<]+)<\/label>'

    def itemHook(item):
        item.url = host + '/filter?' + item.name + '=' + item.value + '&sort='
        return item
    return locals()


@support.scrape
def menu(item):
    action = 'submenu'
    data = get_data(item)
    patronBlock=r'<form class="filters.*?>(?P<block>.*?)</form>'
    patronMenu=r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> (?P<title>.*?) <span.[^>]+>(?P<other>.*?)</ul>'

    def itemlistHook(itemlist):
        item.title = support.typo('Tutti','bold')
        item.action = 'peliculas'
        itemlist.insert(0, item)
        return itemlist
    return locals()


@support.scrape
def submenu(item):
    action = 'peliculas'
    data = item.other
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
    data = get_data(item)
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
    item.url += '?d=1'
    data = get_data(item)
    support.log(data)
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
    # support.dbg()
    matches = support.match(get_data(item), patron=r'data-name="([0-9]+)">', headers=headers)
    data = matches.data
    matches = matches.matches
    videoData = []
    for serverid in matches:
        if not item.number: item.number = support.match(item.title, patron=r'(\d+) -').match
        block = support.match(data, patron=r'data-name="' + serverid + r'"[^>]+>(.*?)<div class="server').match
        match = support.match(block, patron=r'<a data-id="([^"]+)" data-base="' + (item.number if item.number else '1') + '"' + r'.*?href="([^"]+)"').match
        if match:
            ID, url = match

            if serverid == '18':
                url = support.match('%s/ajax/episode/serverPlayer?id=%s' % (host, ID), patron=r'source src="([^"]+)"', headers=headers).match
                itemlist.append(item.clone(action="play", title='Diretto', url=url, server='directo'))

            elif serverid == '26':
                matches = support.match('%s/ajax/episode/serverPlayer?id=%s' % (host, item.url.split('/')[-1]), patron=r'<a href="([^"]+)"', ).matches
                for url in matches:
                    videoData.append(url)
            elif serverid == '39':
                videoData.append(support.match(get_data(item.clone(url=host + url)), patron=r'href="([^"]+)" id="downloadLink"').match)
            else:
                try:
                    dataJson=get_data(item.clone(url='%s/ajax/episode/info?id=%s&server=%s&ts=%s' % (host, ID, serverid, int(time.time()))), head=[['x-requested-with', 'XMLHttpRequest']])
                    json = jsontools.load(dataJson)
                    support.log(json)
                    url = json['grabber']
                    if 'server2' in url:
                        itemlist.append(item.clone(action="play", title='AnimeWorld 2', url=url.split('=')[-1], server='directo'))
                    else:
                        videoData.append(url)
                except:
                    pass
    return support.server(item, videoData, itemlist)

