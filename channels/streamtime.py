# -*- coding: utf-8 -*-
from core import support, httptools, scrapertools
from core.item import Item
from platformcode import config, logger


"""
Nota per i tester: questo non è un canale 'tradizionale', essendo un canale telegram, i cui contenuti (film/serie) sono mischiati tra loro (ed a volte ci sono messaggi sponsor),
la lista delle pagine non sarà affatto 'uniforme' (a seconda di come viene presentata la preview)
"""

host = config.get_channel_url()
headers = [['Referer', 'org.telegram.messenger']]



downPrefix = 'https://stsh.ml/Down-'

@support.menu
def mainlist(item):
    film = ['?q=%23Film']
    tvshow = ['?q=%23SerieTv']
    return locals()


@support.scrape
def peliculas(item):
    patron = """tgme_widget_message_photo_wrap.*?image:url\("(?P<thumbnail>[^"]+).*?//telegram\.org/img/emoji/40/(?:F09F8EAC|F09F8EA5)\.png"\)">.*?</i>\s?(?:<b>)?(?P<title>[^<]+).*?(?:Audio(?:</b>)?: (?P<lang>.*?<br>))?.*?Anno(?:</b>)?: (?P<year>[0-9]{4}).*?(?:<b>Stream</b>|Risoluzione|<b>Tipo</b>|Tipo|Stream): (?P<quality>[^<]+).*?tgme_widget_message_inline_button url_button" href="(?P<url>[^"]+)"""
    def itemlistHook(itemlist):
        retItemlist = []
        # filtro per tipo
        for i in itemlist:
            if '/Film/' in i.url or 'Stream-' in i.url:
                i.contentType = 'movie'
            if '/SerieTv/' in i.url:
                i.contentType = 'tvshow'
                i.action = 'episodios'
            if item.contentType == i.contentType or item.contentType == 'list':  # list = ricerca globale quando c'è un solo tipo di risultato
                retItemlist.append(i)
        # rimuovo duplicati
        if item.contentType != 'movie' and not item.cercaSerie:
            nonDupl = []
            for i in retItemlist:
                for nd in nonDupl:
                    if i.fulltitle == nd.fulltitle:
                        break
                else:
                    nonDupl.append(i)
            retItemlist = nonDupl
        return retItemlist[::-1]
    # debug = True
    # nella ricerca faccio finta che non ci siano "pagine successive", sarebbe un casino gestirle (ed è piuttosto improbabile)
    if item.action != 'search' and item.action:
        patronNext = 'tgme_widget_message_photo_wrap blured" href="([^"]+)'

        # trovo l'id dell'ultimo messaggio e nella pagina successiva ci metto il link per prendere i 20 msg precedenti
        def fullItemlistHook(itemlist):
            msgId = int(itemlist[-1].url.split('/')[-1])
            itemlist[-1].url = host + '?before=' + str(msgId) + '&after=' + str(msgId-20)
            return itemlist

    # necessario per togliere html vario dal titolo (operazione fatta solo su fulltitle)
    # def itemHook(item):
    #     item.contentTitle = item.fulltitle
    #     item.show = item.fulltitle
    #     return item

    if item.contentType == 'tvshow':
        action = 'episodios'
    return locals()


def search(item, texto):
    item.url = host + "/?q=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
    return []


def newest(categoria):
    item = Item()
    if categoria == "series":
        item.contentType = 'tvshow'
        item.url = host + '?q=%23SerieTv'
    else:
        item.contentType = 'movie'
        item.url = host + '?q=%23Film'
    return peliculas(item)


# cerco il titolo, così mi escono fuori tutti i messaggi contenenti puntate singole o serie
def episodios(item):
    url = item.url
    item.cercaSerie = True
    itemlist = search(item, item.fulltitle.replace("'", ""))
    stagioni = {}

    for i in itemlist[:-1]:
        spl1 = i.url.split('-')
        if len(spl1) > 3:
            st = spl1[1] + '-' + spl1[2]
        else:
            st = spl1[-2]
        nEp = int(spl1[-1])
        if st not in stagioni.keys():
            stagioni[st] = nEp
        elif nEp > stagioni[st]:
            stagioni[st] = nEp

    itemlist = []
    domain, id = scrapertools.find_single_match(url, r'(https?://[a-z0-9.-]+)/[^/]+/([^-/]+)')
    for st in sorted(stagioni.keys()):
        season = st[1:]
        episode = stagioni[st]
        for n in range(1, int(episode)):
            url = domain + '/play_s.php?s=' + id + '-S' + season + '&e=' + str(n)
            if '-' in season:  # vedi https://stpgs.ml/SerieTv/Atypical-S01-8-8.html
                season = season.split('-')[0]
            itemlist.append(
                item.clone(action="findvideos",
                           title=str(int(season)) + 'x' + str(n) + support.typo(item.quality, '-- [] color kod'),
                           url=url,
                           contentType='episode',
                           folder=True,
                           args={'id': id, 'season': season, 'episode': episode}))

    support.videolibrary(itemlist, item)
    return itemlist


def findvideos(item):
    # support.dbg()
    domain = scrapertools.find_single_match(item.url, 'https?://[a-z0-9.-]+')
    if item.contentType == 'movie':
        id = item.url.split('/')[-1]
        url = domain + '/play_f.php?f=' + id
    else:
        url = item.url
        id = item.args['id']
        season = str(item.args['season'])
        episode = str(item.args['episode'])
    res = support.match(url, patron='src="([^"]+)"[^>]*></video>', headers=[['Referer', domain]]).match
    itemlist = []

    if res:
        itemlist.append(
            item.clone(action="play", title='contentful', url=res, server='directo'))
    else:
        # google drive...
        pass
    return support.server(item, itemlist=itemlist)
