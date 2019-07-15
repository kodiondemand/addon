# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione01
# ------------------------------------------------------------

from core import servertools, httptools, tmdb, scrapertoolsV2, support
from core.item import Item
from platformcode import logger, config
from specials import autoplay

#URL che reindirizza sempre al dominio corrente
#host = "https://altadefinizione01.to"

__channel__ = "altadefinizione01"
host = config.get_channel_url(__channel__)

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'rapidvideo', 'streamcherry', 'megadrive']
list_quality = ['default']

checklinks = config.get_setting('checklinks', 'altadefinizione01')
checklinks_number = config.get_setting('checklinks_number', 'altadefinizione01')

headers = [['Referer', host]]
blacklist_categorie = ['Altadefinizione01', 'Altadefinizione.to']


def mainlist(item):
    support.log()

    itemlist =[]

    support.menu(itemlist, 'Al Cinema','peliculas',host+'/cinema/')
    support.menu(itemlist, 'Ultimi Film Inseriti','peliculas',host)
    support.menu(itemlist, 'Film Sub-ITA','peliculas',host+'/sub-ita/')
    support.menu(itemlist, 'Film Ordine Alfabetico ','AZlist',host+'/catalog/')
    support.menu(itemlist, 'Categorie Film','categories',host)
    support.menu(itemlist, 'Cerca...','search')
    
    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def categories(item):
    support.log(item)
    itemlist = support.scrape(item,'<li><a href="([^"]+)">(.*?)</a></li>',['url','title'],headers,'Altadefinizione01',patron_block='<ul class="kategori_list">(.*?)</ul>',action='peliculas')
    return support.thumb(itemlist)

def AZlist(item):
    support.log()
    return support.scrape(item,r'<a title="([^"]+)" href="([^"]+)"',['title','url'],headers,patron_block=r'<div class="movies-letter">(.*?)<\/div>',action='peliculas_list')


def newest(categoria):
    # import web_pdb; web_pdb.set_trace()
    support.log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    support.log(texto)
    item.url = "%s/index.php?do=search&story=%s&subaction=search" % (
        host, texto)
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    support.log()
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = r'<div class="cover_kapsul ml-mask".*?<a href="(.*?)">(.*?)<\/a>.*?<img .*?src="(.*?)".*?<div class="trdublaj">(.*?)<\/div>.(<div class="sub_ita">(.*?)<\/div>|())'
    matches = scrapertoolsV2.find_multiple_matches(data, patron)
    
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedquality, subDiv, subText, empty in matches:
        info = scrapertoolsV2.find_multiple_matches(data, r'<span class="ml-label">([0-9]+)+<\/span>.*?<span class="ml-label">(.*?)<\/span>.*?<p class="ml-cat".*?<p>(.*?)<\/p>.*?<a href="(.*?)" class="ml-watch">')
        infoLabels = {}
        for infoLabels['year'], duration, scrapedplot, checkUrl in info:
            if checkUrl == scrapedurl:
                break

        infoLabels['duration'] = int(duration.replace(' min', '')) * 60  # calcolo la durata in secondi
        scrapedthumbnail = host + scrapedthumbnail
        scrapedtitle = scrapertoolsV2.decodeHtmlentities(scrapedtitle)
        fulltitle = scrapedtitle
        if subDiv:
            fulltitle += support.typo(subText + ' _ () color limegreen')
        fulltitle += support.typo(scrapedquality.strip()+ ' _ [] color kod')

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType=item.contenType,
                 contentTitle=scrapedtitle,
                 contentQuality=scrapedquality.strip(),
                 plot=scrapedplot,
                 title=fulltitle,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 url=scrapedurl,
                 infoLabels=infoLabels,
                 thumbnail=scrapedthumbnail))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    support.nextPage(itemlist,item,data,'<span>[^<]+</span>[^<]+<a href="(.*?)">')

    return itemlist

def peliculas_list(item):
    support.log()
    item.fulltitle = ''
    block = r'<tbody>(.*)<\/tbody>'
    patron = r'<a href="([^"]+)" title="([^"]+)".*?> <img.*?src="([^"]+)".*?<td class="mlnh-3">([0-9]{4}).*?mlnh-4">([A-Z]+)'
    return support.scrape(item,patron, ['url', 'title', 'thumb', 'year', 'quality'], patron_block=block)



def findvideos(item):
    support.log()
    
    itemlist = support.server(item, headers=headers)

    return itemlist
