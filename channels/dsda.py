# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per documentaristreamingda
# ------------------------------------------------------------

from core import support
from core.item import Item
from platformcode import logger, config

host = config.get_channel_url()

@support.menu
def mainlist(item):
    docu = [('Documentari {bullet bold}',('/elenco-documentari','peliculas')),
            ('Categorie {submenu documentary}',('','menu')),
            ('Cerca... {bullet bold documentary}',('','search')),]
    return locals()


@support.scrape
def menu(item):
    action = 'peliculas'
    patronMenu = r'<li class="menu-item menu-item-type-taxonomy[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)<'
    def fullItemlistHook(itemlist):
        item_list = []
        title_list = []
        for item in itemlist:
            if item.title not in title_list:
                item_list.append(item)
                title_list.append(item.title)
        itemlist = item_list
        return itemlist
    return locals()

def newest(categoria):
    logger.debug()
    item = Item()
    try:
        if categoria == "documentales":
            item.url = host + "/elenco-documentari"
            item.action = "peliculas"
            return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def search(item, texto):
    logger.debug(texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def peliculas(item):
    blacklist = ['GUIDA PRINCIPIANTI Vedere film e documentari streaming gratis', 'Guida Dsda']
    data = support.match(item).data
    # debug =True
    if item.args == 'collection':
        if 'class="panel"' in data:
            item.args = 'raccolta'
            patron = r'class="title-episodio">(?P<title>[^<]+)<(?P<url>.*?)<p'
            # patron = r'<a (?:style="[^"]+" )?href="(?P<url>[^"]+)"[^>]+>(?:[^>]+><strong>)?(?P<title>[^<]+)(?:</a>)?</strong'
        else:
            patron = r'<div class="cover-racolta">\s*<a href="(?P<url>[^"]+)"[^>]+>\s*<img width="[^"]+" height="[^"]+" src="(?P<thumb>[^"]+)".*?<p class="title[^>]+>(?P<title>[^<]+)<'
    else:
        patron = r'<article[^>]+>[^>]+>[^>]+>(?:<img width="[^"]+" height="[^"]+" src="(?P<thumb>[^"]+)"[^>]+>)?.*?<a href="(?P<url>[^"]+)"[^>]*>\s*(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<p>(?P<plot>[^<]+)<'
        patronNext = r'<a class="page-numbers next" href="([^"]+)">'

    # select category
    def itemHook(item):
        title = support.re.sub(r'(?:[Ss]erie\s*|[Ss]treaming(?:\s*[Dd][Aa])?\s*|[Cc]ollezione\s*|[Rr]accolta\s*|[Dd]ocumentari(?:o)?\s*)?','',item.fulltitle).strip()
        if 'serie' in item.fulltitle.lower():
            item.contentType = 'tvshow'
            item.action = 'episodios'
            item.contentSerieName = title
            item.contentTitle = ''
        elif 'collezion' in item.fulltitle.lower() or \
             'raccolt' in item.fulltitle.lower() or \
             'filmografia' in item.fulltitle.lower():
            item.args = 'collection'
            item.action = 'peliculas'
            item.contentTitle = title
            item.contentSerieName = ''
        else:
            item.contentTitle = title
            item.contentSerieName = ''

        item.title = support.typo(title,'bold')
        item.fulltitle = item.show = title
        return item
    # remove duplicates
    def fullItemlistHook(itemlist):
        item_list = []
        title_list = []
        for item in itemlist:
            if item.title not in title_list:
                item_list.append(item)
                title_list.append(item.title)
        itemlist = item_list
        return itemlist
    return locals()

@support.scrape
def episodios(item):
    html = support.match(item, patron=r'class="title-episodio">(\d+x\d+)')
    data = html.data
    if html.match:
        patron = r'class="title-episodio">(?P<episode>[^<]+)<(?P<url>.*?)<p'
    else:
        patron = r'class="title-episodio">(?P<title>[^<]+)<(?P<url>.*?)<p'

        # def itemlistHook(itemlist):
        #     counter = 0
        #     for item in itemlist:
        #         episode = support.match(item.title, patron=r'\d+').match
        #         if episode == '1':
        #             counter += 1
        #         item.title = support.typo(str(counter) + 'x' + episode.zfill(2) + support.re.sub(r'\[[^\]]+\](?:\d+)?','',item.title),'bold')
        #     return itemlist
    return locals()


def findvideos(item):
    logger.debug()
    if item.args == 'raccolta' or item.contentType == 'episode':
        return support.server(item, item.url)
    else:
        return support.server(item)