# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSaturn
# ----------------------------------------------------------

from lib import js2py
from core import support
from platformcode import config

host = support.config.get_channel_url()
headers={'X-Requested-With': 'XMLHttpRequest'}

def get_data(item, head=[]):
    global headers
    jstr = ''
    for h in head:
        headers[h[0]] = h[1]
    if not item.count: item.count = 0
    matches = support.match(item, patron=r'<script>(.*?location.href=".*?(http[^"]+)";)</').match
    if matches:
        jstr, location = matches
        item.url=support.re.sub(r':\d+', '', location).replace('http://','https://')
    if not config.get_setting('key', item.channel) and jstr:
        jshe = 'var document = {}, location = {}'
        aesjs = str(support.match(host + '/aes.min.js').data)
        js_fix = 'window.toHex = window.toHex || function(){for(var d=[],d=1==arguments.length&&arguments[0].constructor==Array?arguments[0]:arguments,e="",f=0;f<d.length;f++)e+=(16>d[f]?"0":"")+d[f].toString(16);return e.toLowerCase()}'
        jsret =  'return document.cookie'
        key_data = js2py.eval_js( 'function (){ ' + jshe + '\n' + aesjs + '\n' + js_fix + '\n' + jstr + '\n' + jsret + '}' )()
        key = key_data.split(';')[0]

        # save Key in settings
        config.set_setting('key', key, item.channel)

    # set cookie
    headers['cookie'] = config.get_setting('key', item.channel)
    res = support.match(item, headers=headers, patron=r';\s*location.href=".*?(http[^"]+)"')
    if res.match:
        item.url= res.match.replace('http://','https://')
        data = support.match(item, headers=headers).data
    else:
        data = res.data


    #check that the key is still valid
    if 'document.cookie=' in data and item.count < 3:
        item.count += 1
        config.set_setting('key', '', item.channel)
        return get_data(item)
    return data


@support.menu
def mainlist(item):

    anime = ['/animelist?load_all=1&d=1',
             ('Più Votati',['/toplist','menu', 'top']),
             ('In Corso',['/animeincorso','peliculas','incorso']),
             ('Ultimi Episodi',['/fetch_pages.php?request=episodes&d=1','peliculas','updated'])]

    return locals()


def search(item, texto):
    support.log(texto)
    item.url = host + '/animelist?search=' + texto
    item.contentType = 'tvshow'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def newest(categoria):
    support.log()
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host + '/fetch_pages.php?request=episodes&d=1'
            item.args = "updated"
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist


@support.scrape
def menu(item):
    data=get_data(item)
    patronMenu = r'<div class="col-md-13 bg-dark-as-box-shadow p-2 text-white text-center">(?P<title>[^"<]+)<(?P<other>.*?)(?:"lista-top"|"clearfix")'
    action = 'peliculas'
    item.args = 'top'
    def itemHook(item2):
        item2.url = item.url
        return item2

    return locals()


@support.scrape
def peliculas(item):
    data = get_data(item)
    anime = True

    deflang= 'Sub-ITA'
    action = 'check'

    page = None
    post = "page=" + str(item.page if item.page else 1) if item.page > 1 else None

    if item.args == 'top':
        data = item.other
        patron = r'light">(?P<title2>[^<]+)</div>\s*(?P<title>[^<]+)[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)">(?:<a[^>]+>|\s*)<img.*?src="(?P<thumb>[^"]+)"'
    else:
        data = support.match(item, post=post, headers=headers).data
        if item.args == 'updated':
            page= support.match(data, patron=r'data-page="(\d+)" title="Next">').match
            patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>[^"(]+)(?:\s*\((?P<year>\d+)\))?(?:\s*\((?P<lang>[A-Za-z-]+)\))?"><img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s\s*(?P<type>[^\s]+)\s*(?P<episode>\d+)'
            typeContentDict = {'Movie':'movie', 'Episodio':'episode'} #item.contentType='episode'
            action = 'findvideos'
            def itemlistHook(itemlist):
                if page:
                    itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'),page= page, thumbnail=support.thumb()))
                    return itemlist
        else:
            pagination = ''
            if item.args == 'incorso':
                patron = r'<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^<(]+)(?:\s*\((?P<year>\d+)\))?(?:\s*\((?P<lang>[A-za-z-]+)\))?</a>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<img width="[^"]+" height="[^"]+" src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<'
            else:
                patron = r'<img src="(?P<thumb>[^"]+)" alt="(?P<title>[^"\(]+)(?:\((?P<lang>[Ii][Tt][Aa])\))?(?:\s*\((?P<year>\d+)\))?[^"]*"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a class="[^"]+" href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+><p[^>]+>(?:(?P<plot>[^<]+))?<'

    return locals()


def check(item):
    movie = support.match(get_data(item), patron=r'Episodi:</b> (\d*) Movie')
    if movie.match:
        episodes = episodios(item)
        if len(episodes) > 0:
            it = episodes[0].clone(contentType = 'movie', contentTitle=item.fulltitle, contentSerieName='')
        return findvideos(it)
    else:
        item.contentType = 'tvshow'
        return episodios(item)


@support.scrape
def episodios(item):
    data = get_data(item)
    if item.contentType != 'movie': anime = True
    patron = r'episodi-link-button">\s*<a href="(?P<url>[^"]+)"[^>]+>\s*(?P<title>[^<]+)</a>'
    return locals()


def findvideos(item):
    support.log()
    itemlist = []
    page_data = ''
    titles =['Primario', 'Secondario', 'Alternativo Primario', 'Alternativo Secondario']
    url = support.match(get_data(item), patron=r'<a href="([^"]+)">[^>]+>[^>]+>G', headers=headers).match
    urls = [url, url+'&extra=1', url+'&s=alt', url+'&s=alt&extra=1']
    links = []
    for i, url in enumerate(urls):
        data = support.match(url, headers=headers).data
        if not '&s' in url:
            link = support.match(data, patron=r'(?:<source type="[^"]+"\s*src=|file:\s*)"([^"]+)"', headers=headers).match
        else:
            link = support.match(data, headers=headers, patron=r'file:\s*"([^"]+)"').match
        if not link:
            page_data += data
        if link not in links:
            links.append(link)
            itemlist.append(item.clone(action="play", title=titles[i], url=link, server='directo'))
    return support.server(item, data=data, itemlist=itemlist)









