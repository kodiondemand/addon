# -*- coding: utf-8 -*-
# -*- Channel Altadefinizione01C Film -*-
# -*- Riscritto per KOD -*-
# -*- By Greko -*-
# -*- last change: 04/05/2019


from core import channeltools, servertools, support
from core.item import Item
from platformcode import config, logger
from specials import autoplay

__channel__ = "altadefinizione01_club"
host = config.get_channel_url(__channel__)

# ======== Funzionalità =============================

checklinks = config.get_setting('checklinks', __channel__)
checklinks_number = config.get_setting('checklinks_number', __channel__)

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream','openload','supervideo','rapidvideo','streamango'] # per l'autoplay
list_quality = ['default']


# =========== home menu ===================

def mainlist(item):
    """
    Creo il menu principale del canale
    :param item:
    :return: itemlist []
    """
    logger.info("%s mainlist log: %s" % (__channel__, item)) 
    itemlist = []

    # Menu Principale
    support.menu(itemlist, 'Film Ultimi Arrivi bold', 'peliculas', host, args='pellicola')
    support.menu(itemlist, 'Genere', 'categorie', host, args='genres')
    support.menu(itemlist, 'Per anno submenu', 'categorie', host, args=['Film per Anno','years'])
    support.menu(itemlist, 'Per lettera', 'categorie', host + '/catalog/a/', args=['Film per Lettera','orderalf'])
    support.menu(itemlist, 'Al Cinema bold', 'peliculas', host + '/cinema/', args='pellicola')
    support.menu(itemlist, 'Sub-ITA bold', 'peliculas', host + '/sub-ita/', args='pellicola')
    support.menu(itemlist, 'Cerca film submenu', 'search', host, args = 'search')

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    support.channel_config(item, itemlist)
    
    return itemlist

# ======== def in ordine di menu ===========================
# =========== def per vedere la lista dei film =============

def peliculas(item):
    logger.info("%s mainlist peliculas log: %s" % (__channel__, item))
    itemlist = []

    patron_block = r'<div id="dle-content">(.*?)<div class="page_nav">'
    if item.args == "search":
        patron_block = r'</table> </form>(.*?)<div class="search_bg">'
    patron = r'<h2>.<a href="(.*?)".*?src="(.*?)".*?(?:|<div class="sub_ita">(.*?)</div>)[ ]</div>.*?<p class="h4">(.*?)</p>'

    listGroups = ['url', 'thumb', 'lang', 'title', 'year']

    patronNext =  '<span>[^<]+</span>[^<]+<a href="(.*?)">'
    
    itemlist = support.scrape(item, patron=patron, listGroups=listGroups,
                          headers= headers, patronNext=patronNext,patron_block=patron_block,
                          action='findvideos')    
    
    return itemlist

# =========== def pagina categorie ======================================

def categorie(item):
    logger.info("%s mainlist categorie log: %s" % (__channel__, item))
    itemlist = []

    # da qui fare le opportuni modifiche
    patron = r'<li><a href="(.*?)">(.*?)</a>'
    action = 'peliculas'
    if item.args == 'genres':
        bloque = r'<ul class="kategori_list">(.*?)</ul>'
    elif item.args[1] == 'years':
        bloque = r'<ul class="anno_list">(.*?)</ul>'
    elif item.args[1] == 'orderalf':
        bloque = r'<div class="movies-letter">(.*)<div class="clearfix">'
        patron = r'<a title=.*?href="(.*?)"><span>(.*?)</span>'
        action = 'orderalf'

    listGroups = ['url', 'title']
    patronNext = ''
       
    itemlist = support.scrape(item, patron=patron, listGroups=listGroups,
                          headers= headers, patronNext=patronNext, patron_block = bloque,
                          action=action)

    return itemlist

# =========== def pagina lista alfabetica ===============================

def orderalf(item):
    logger.info("%s mainlist orderalf log: %s" % (__channel__, item))
    itemlist = []

    listGroups = ['url', 'title', 'thumb', 'year', 'lang']
    patron = r'<td class="mlnh-thumb"><a href="(.*?)".title="(.*?)".*?src="(.*?)".*?mlnh-3">(.*?)<.*?"mlnh-5">.<(.*?)<td' #scrapertools.find_single_match(data, '<td class="mlnh-thumb"><a href="(.*?)".title="(.*?)".*?src="(.*?)".*?mlnh-3">(.*?)<.*?"mlnh-5">.<(.*?)<td')
    patronNext = r'<span>[^<]+</span>[^<]+<a href="(.*?)">'
    
    itemlist = support.scrape(item, patron=patron, listGroups=listGroups,
                          headers= headers, patronNext=patronNext,
                          action='findvideos')

    return itemlist

# =========== def pagina del film con i server per verderlo =============

def findvideos(item):
    logger.info("%s mainlist findvideos_film log: %s" % (__channel__, item))
    itemlist = []
    return support.server(item, headers=headers)

# =========== def per cercare film/serietv =============
#http://altadefinizione01.link/index.php?do=search&story=avatar&subaction=search
def search(item, text):
    logger.info("%s mainlist search log: %s %s" % (__channel__, item, text))
    itemlist = []
    text = text.replace(" ", "+")
    item.url = host + "/index.php?do=search&story=%s&subaction=search" % (text)
    #item.extra = "search"
    try:
        return peliculas(item)
    # Cattura la eccezione così non interrompe la ricerca globle se il canale si rompe!
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s Sono qua: %s" % (__channel__, line))
        return []

# =========== def per le novità nel menu principale =============

def newest(categoria):
    logger.info("%s mainlist newest log: %s" % (__channel__, categoria))
    itemlist = []
    item = Item()
    try:
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
