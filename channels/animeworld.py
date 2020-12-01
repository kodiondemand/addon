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

# def get_data(item, head=[]):
#     global headers
#     jstr = ''
#     for h in head:
#         headers[h[0]] = h[1]
#     if not item.count: item.count = 0
#     if not config.get_setting('key', item.channel):
#         matches = support.match(item, patron=r'<script>(.*?location.href=".*?(http[^"]+)";)</').match
#         if matches:
#             jstr, location = matches
#             item.url=support.re.sub(r':\d+', '', location).replace('http://','https://')
#         if jstr:
#             jshe = 'var document = {}, location = {}'
#             aesjs = str(support.match(host + '/aes.min.js').data)
#             js_fix = 'window.toHex = window.toHex || function(){for(var d=[],d=1==arguments.length&&arguments[0].constructor==Array?arguments[0]:arguments,e="",f=0;f<d.length;f++)e+=(16>d[f]?"0":"")+d[f].toString(16);return e.toLowerCase()}'
#             jsret =  'return document.cookie'
#             key_data = js2py.eval_js( 'function (){ ' + jshe + '\n' + aesjs + '\n' + js_fix + '\n' + jstr + '\n' + jsret + '}' )()
#             key = key_data.split(';')[0]

#             # save Key in settings
#             config.set_setting('key', key, item.channel)

#     # set cookie
#     headers['cookie'] = config.get_setting('key', item.channel)
#     res = support.match(item, headers=headers, patron=r';\s*location.href=".*?(http[^"]+)"')
#     if res.match:
#         item.url= res.match.replace('http://','https://')
#         data = support.match(item, headers=headers).data
#     else:
#         data = res.data


#     #check that the key is still valid
#     if 'document.cookie=' in data and item.count < 3:
#         item.count += 1
#         config.set_setting('key', '', item.channel)
#         return get_data(item)
#     return data


@support.menu
def mainlist(item):
    anime=['/filter?sort=',
           ('ITA',['/filter?dub=1&sort=', 'menu', '1']),
           ('SUB-ITA',['/filter?dub=0&sort=', 'menu', '0']),
           ('In Corso', ['/ongoing', 'peliculas','noorder']),
           ('Ultimi Episodi', ['/updated', 'peliculas', 'updated']),
           ('Nuove Aggiunte',['/newest', 'peliculas','noorder' ]),
           ('Generi',['/?d=1','genres',])]
    return locals()


@support.scrape
def genres(item):
    action = 'peliculas'
    # data = get_data(item)
    patronBlock = r'dropdown[^>]*>\s*Generi\s*<span.[^>]+>(?P<block>.*?)</ul>'
    patronMenu = r'<input.*?name="(?P<name>[^"]+)" value="(?P<value>[^"]+)"\s*>[^>]+>(?P<title>[^<]+)</label>'

    def itemHook(item):
        item.url = host + '/filter?' + item.name + '=' + item.value + '&sort='
        return item
    return locals()


@support.scrape
def menu(item):
    action = 'submenu'
    # data = get_data(item)
    patronMenu=r'<button[^>]+>\s*(?P<title>[A-Za-z0-9]+)\s*<span.[^>]+>(?P<other>.*?)</ul>'
    def itemlistHook(itemlist):
        itemlist.insert(0, item.clone(title=support.typo('Tutti','bold'), action='peliculas'))
        itemlist.append(item.clone(title=support.typo('Cerca...','bold'), action='search', search=True, thumbnail=support.thumb('search.png')))
        return itemlist
    return locals()


@support.scrape
def submenu(item):
    action = 'peliculas'
    data = item.other
    patronMenu = r'<input.*?name="(?P<name>[^"]+)" value="(?P<value>[^"]+)"\s*>[^>]+>(?P<title>[^<]+)<\/label>'
    def itemHook(item):
        item.url = host + '/filter?' + item.name + '=' + item.value + '&dub=' + item.args + ('&sort=' if item.name != 'sort' else '')
        return item
    return locals()


def newest(categoria):
    support.info(categoria)
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
    support.info(texto)
    if item.search:
        item.url = host + '/filter?dub=' + item.args + '&keyword=' + texto + '&sort='
    else:
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
    # debug =True
    if item.args not in ['noorder', 'updated'] and not item.url[-1].isdigit(): item.url += order() # usa l'ordinamento di configura canale
    # data = get_data(item)
    if item.args == 'updated':
        # data = get_data(item)
        item.contentType='episode'
        patron=r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img.*?src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?[^>]+>[^>]+>\s*<div class="ep">[^\d]+(?P<episode>\d+)[^<]*</div>'
        action='findvideos'
    else:
        patron= r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img.*?src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<year>\d+)\) )?(?:\((?P<lang>[^\)]+)\))?(?P<title2>[^"]+)?[^>]+>[^>]+>(?:\s*<div class="(?P<l>[^"]+)">[^>]+>)?\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?'
        action='episodios'

    # Controlla la lingua se assente
    patronNext=r'<a href="([^"]+)" class="[^"]+" id="go-next'
    typeContentDict={'movie':['movie', 'special']}
    typeActionDict={'findvideos':['movie', 'special']}
    def itemHook(item):
        if not item.contentLanguage:
            if 'dub=1' in item.url or item.l == 'dub':
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
    pagination = 25
    # data = get_data(item)
    patronBlock= r'<div class="server\s*active\s*"(?P<block>.*?)(?:<div class="server|<link)'
    patron = r'<li[^>]*>\s*<a.*?href="(?P<url>[^"]+)"[^>]*>(?P<episode>[^<]+)<'
    def itemHook(item):
        item.number = support.re.sub(r'\[[^\]]+\]', '', item.title)
        item.title += support.typo(item.fulltitle,'-- bold')
        return item
    action='findvideos'
    return locals()


def findvideos(item):
    import time
    support.info(item)
    itemlist = []
    urls = []
    # resp = support.match(get_data(item), headers=headers, patron=r'data-name="(\d+)">([^<]+)<')
    resp = support.match(item, headers=headers, patron=r'data-name="(\d+)">([^<]+)<')
    data = resp.data
    for ID, name in resp.matches:
        if not item.number: item.number = support.match(item.title, patron=r'(\d+) -').match
        match = support.match(data, patronBlock=r'data-name="' + ID + r'"[^>]+>(.*?)(?:<div class="(?:server|download)|link)', patron=r'data-id="([^"]+)" data-episode-num="' + (item.number if item.number else '1') + '"' + r'.*?href="([^"]+)"').match
        if match:
            epID, epurl = match
            if 'vvvvid' in name.lower():
                urls.append(support.match(host + '/api/episode/serverPlayer?id=' + epID, headers=headers, patron=r'<a.*?href="([^"]+)"').match)
            elif 'streamtape' in name.lower():
                urls.append(support.match(data, patron=r'<a href="(https://streamtape[^"]+)"').match)
            elif 'beta' in name.lower():
                urls.append(support.match(data, patron=r'<a href="(https://animeworld[^"]+)"').match)
            elif 'server 2' in name.lower():
                dataJson = support.match(host + '/api/episode/info?id=' + epID + '&alt=0', headers=headers).data
                json = jsontools.load(dataJson)
                title = support.match(json['grabber'], patron=r'server2.([^.]+)', string=True).match
                itemlist.append(item.clone(action="play", title=title, url=json['grabber'], server='directo'))
            elif 'animeworld' in name.lower():
                url = support.match(data, patron=r'href="([^"]+)"\s*id="alternativeDownloadLink"', headers=headers).match
                title = support.match(url, patron=r'http[s]?://(?:www.)?([^.]+)', string=True).match
                itemlist.append(item.clone(action="play", title=title, url=url, server='directo'))
    return support.server(item, urls, itemlist)
