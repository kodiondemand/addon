# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animealtadefinizione
# ----------------------------------------------------------

from core import support

host = support.config.get_channel_url()
headers = [['Referer', host]]

perpage_list = ['20','30','40','50','60','70','80','90','100']
perpage = perpage_list[support.config.get_setting('perpage' , 'animealtadefinizione')]
epPatron = r'<td>\s*(?P<title>[^<]+)[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>\s*<img[^>]+/Streaming'


@support.menu
def mainlist(item):
    anime=['/anime/',
           ('Tipo',['', 'menu', 'Anime']),
           ('Anno',['', 'menu', 'Anno']),
           ('Genere', ['', 'menu','Genere']),
           ('Ultimi Episodi',['', 'peliculas', 'last'])]
    return locals()


@support.scrape
def menu(item):
    action = 'peliculas'
    patronBlock= r'<a href="' + host + r'/category/' + item.args.lower() + r'/">' + item.args + r'</a>\s*<ul class="sub-menu">(?P<block>.*?)</ul>'
    patronMenu = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'
    return locals()


def search(item, texto):
    support.info(texto)
    item.search = texto
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
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host
            item.args = "last"
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


@support.scrape
def peliculas(item):
    if '/movie/' in item.url:
        item.contentType = 'movie'
        action='findvideos'
    elif item.args == 'last':
        item.contentType = 'episode'
        action='episodios'
    else:
        item.contentType = 'tvshow'
        action='episodios'
    if item.search:
        query = 's'
        searchtext = item.search
    else:
        query='category_name'
        searchtext = item.url.split('/')[-2]
    if not item.pag: item.pag = 1
    # debug = True
    anime = True
    data = support.match(host + '/wp-admin/admin-ajax.php', post='action=itajax-sort&loop=main+loop&location=&thumbnail=1&rating=1sorter=recent&columns=4&numarticles='+perpage+'&paginated='+str(item.pag)+'&currentquery%5B'+query+'%5D='+searchtext).data.replace('\\','')
    patron = r'<a href="(?P<url>[^"]+)"><img width="[^"]+" height="[^"]+" src="(?P<thumb>[^"]+)" class="[^"]+" alt="" title="(?P<title>[^"]+?)\s+(?P<type>Movie)?\s*(?P<lang>Sub Ita|Ita)?\s*[sS]treaming'
    typeContentDict = {'movie':['movie']}
    typeActionDict = {'findvideos':['movie']}

    def itemHook(item):
        item.url = support.re.sub('episodio-[0-9-]+', '', item.url)
        return item

    def itemlistHook(itemlist):
        if item.search:
            itemlist = [ it for it in itemlist if ' Episodio ' not in it.title ]
        if len(itemlist) == int(perpage):
            item.pag += 1
            itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), action='peliculas'))
        return itemlist
    return locals()


@support.scrape
def episodios(item):
    anime = True
    # debug = True
    pagination = int(perpage)
    patron = epPatron
    return locals()


def findvideos(item):
    itemlist = []
    if item.contentType == 'movie':
        matches = support.match(item, patron=epPatron).matches
        for title, url in matches:
            # support.dbg()
            get_video_list(item, url, title, itemlist)
    else:
        get_video_list(item, item.url, support.config.get_localized_string(30137), itemlist)
    return support.server(item, itemlist=itemlist)


def get_video_list(item, url, title, itemlist):
    if 'vvvvid' in url:
        itemlist.append(item.clone(title='VVVVID', url=url, server='vvvvid', action='play'))
    else:
        from requests import get
        if not url.startswith('http'): url = host + url

        url = support.match(get(url).url, string=True, patron=r'file=([^$]+)').match
        if 'http' not in url: url = 'http://' + url
        itemlist.append(item.clone(title=title, url=url, server='directo', action='play'))

    return itemlist