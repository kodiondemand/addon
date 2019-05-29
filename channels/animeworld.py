# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# ----------------------------------------------------------
import re
import time
import urllib
import urlparse

from core import httptools, scrapertoolsV2, servertools, tmdb, support, jsontools
from core.support import log
from core.item import Item
from platformcode import logger, config
from specials import autoplay, autorenumber

host = config.get_setting("channel_host", 'animeworld')
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'Italiano'}
list_language = IDIOMAS.values()
list_servers = ['diretto']
list_quality = []

checklinks = config.get_setting('checklinks', 'animeworld')
checklinks_number = config.get_setting('checklinks_number', 'animeworld')


def mainlist(item):
    log()
    
    itemlist =[]
    
    support.menu(itemlist, 'Anime bold', 'lista_anime', host+'/az-list')
    support.menu(itemlist, 'ITA submenu', 'build_menu', host + '/filter?', args=["anime", 'language[]=1'])
    support.menu(itemlist, 'Sub-ITA submenu', 'build_menu', host + '/filter?', args=["anime", 'language[]=0'])
    support.menu(itemlist, 'Archivio A-Z submenu', 'alfabetico', host+'/az-list', args=["tvshow","a-z"])
    support.menu(itemlist, 'In corso submenu', 'video', host+'/', args=["in sala"])
    support.menu(itemlist, 'Generi submenu', 'generi', host+'/')
    support.menu(itemlist, 'Ultimi Aggiunti bold', 'video', host+'/newest', args=["anime"])
    support.menu(itemlist, 'Ultimi Episodi bold', 'video', host+'/updated', args=["novita'"])
    support.menu(itemlist, 'Cerca...', 'search')
    support.aplay(item, itemlist, list_servers, list_quality)
    support.channel_config(item, itemlist)
    return itemlist

# Crea menu dei generi =================================================

def generi(item):
    log()
    itemlist = []
    patron_block = r'</i>\sGeneri</a>\s*<ul class="sub">(.*?)</ul>'
    patron = r'<a href="([^"]+)"\stitle="([^"]+)">'
    matches = support.match(item,patron, patron_block, headers)[0]

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(
            channel=item.channel,
            action="video",
            title=scrapedtitle,
            url="%s%s" % (host,scrapedurl)))

    return itemlist


# Crea Menu Filtro ======================================================

def build_menu(item):
    log()
    itemlist = []
    support.menu(itemlist, 'Tutti bold submenu', 'video', item.url+item.args[1])
    matches, data = support.match(item,r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> (.*?) <span.*?>(.*?)<\/ul>',r'<form class="filters.*?>(.*?)<\/form>')
    log('ANIME DATA =' ,data)
    for title, html in matches:
        if title not in 'Lingua Ordine':
            support.menu(itemlist, title + ' submenu bold', 'build_sub_menu', html, args=item.args)
            log('ARGS= ', item.args[0])
            log('ARGS= ', html)
    return itemlist

# Crea SottoMenu Filtro ======================================================

def build_sub_menu(item):
    log()
    itemlist = []
    matches = re.compile(r'<input.*?name="([^"]+)" value="([^"]+)"\s*>[^>]+>([^<]+)<\/label>', re.DOTALL).findall(item.url)
    for name, value, title in matches:
        support.menu(itemlist, support.typo(title, 'bold'), 'video', host + '/filter?' + '&' + name + '=' + value + '&' + item.args[1])     
    return itemlist

# Novità ======================================================

def newest(categoria):
    log()
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host + '/newest'
            item.action = "video"
            itemlist = video(item)

            if itemlist[-1].action == "video":
                itemlist.pop()
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# Cerca ===========================================================

def search(item, texto):
    log(texto)
    item.url = host + '/search?keyword=' + texto
    try:
        return video(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# Lista A-Z ====================================================

def alfabetico(item):
    return support.scrape(item, '<a href="([^"]+)" title="([^"]+)">', ['url', 'title'], patron_block=r'<span>.*?A alla Z.<\/span>.*?<ul>(.*?)<\/ul>', action='lista_anime')
    

def lista_anime(item):
    log()
    itemlist = []
    matches ,data = support.match(item, r'<div class="item"><a href="([^"]+)".*?src="([^"]+)".*?data-jtitle="([^"]+)".*?>([^<]+)<\/a><p>(.*?)<\/p>')
    for scrapedurl, scrapedthumb, scrapedoriginal, scrapedtitle, scrapedplot in matches:
        
        if scrapedoriginal == scrapedtitle:
            scrapedoriginal=''
        else:
            scrapedoriginal = support.typo(scrapedoriginal,' -- []')

        year = ''
        lang = ''
        infoLabels = {}
        if '(' in scrapedtitle:
            year = scrapertoolsV2.find_single_match(scrapedtitle, r'(\([0-9]+\))')
            lang = scrapertoolsV2.find_single_match(scrapedtitle, r'(\([a-zA-Z]+\))')

        infoLabels['year'] = year
        title = scrapedtitle.replace(year,'').replace(lang,'').strip()
        original = scrapedoriginal.replace(year,'').replace(lang,'').strip()
        if lang: lang = support.typo(lang,'_ color kod')
        title = '[B]' + title + '[/B]' + lang + original

        itemlist.append(
                Item(channel=item.channel,
                     extra=item.extra,
                     contentType="episode",
                     action="episodios",
                     title=title,
                     url=scrapedurl,
                     thumbnail=scrapedthumb,
                     fulltitle=title,
                     show=title,
                     infoLabels=infoLabels,
                     plot=scrapedplot,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)    
    autorenumber.renumber(itemlist)

    # Next page
    support.nextPage(itemlist, item, data, r'<a class="page-link" href="([^"]+)" rel="next"')

    return itemlist


def video(item):
    log()
    itemlist = []

    matches, data = support.match(item, r'<a href="([^"]+)" class="poster.*?> <img src="([^"]+)"(.*?)data-jtitle="([^"]+)" .*?>(.*?)<\/a>')

    for scrapedurl, scrapedthumb ,scrapedinfo, scrapedoriginal, scrapedtitle in matches:
        # Cerca Info come anno o lingua nel Titolo
        year = ''
        lang = ''
        if '(' in scrapedtitle:
            year = scrapertoolsV2.find_single_match(scrapedtitle, r'( \([0-9]+\))')
            lang = scrapertoolsV2.find_single_match(scrapedtitle, r'( \([a-zA-Z]+\))')
        
        # Rimuove Anno e Lingua nel Titolo
        title = scrapedtitle.replace(year,'').replace(lang,'').strip()
        original = scrapedoriginal.replace(year,'').replace(lang,'').strip()
        
        # Compara Il Titolo con quello originale
        if original == title:
            original=''
        else:
            original = support.typo(scrapedoriginal,'-- []')

        # cerca info supplementari
        ep = ''
        ep = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ep">(.*?)<')
        if  ep != '':
            ep = ' - ' + ep

        ova = ''
        ova = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ova">(.*?)<')
        if  ova != '':
            ova = ' - (' + ova + ')'
        
        ona = ''
        ona = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ona">(.*?)<')
        if  ona != '':
            ona = ' - (' + ona + ')'

        movie = ''
        movie = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="movie">(.*?)<')
        if  movie != '':
            movie = ' - (' + movie + ')'

        special = ''
        special = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="special">(.*?)<')
        if  special != '':
            special = ' - (' + special + ')'


        # Concatena le informazioni
        info = ep + lang + year + ova + ona + movie + special

        # Crea il title da visualizzare
        long_title = '[B]' + title + '[/B]' + info + original

        # Controlla se sono Episodi o Film
        if movie == '':
            contentType = 'episode'
            action = 'episodios'
        else:
            contentType = 'movie'
            action = 'findvideos'
        
        itemlist.append(
                Item(channel=item.channel,
                     contentType=contentType,
                     action=action,
                     title=long_title,
                     url=scrapedurl,
                     fulltitle=title,
                     show=title,
                     thumbnail=scrapedthumb,
                     context = autoplay.context))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    autorenumber.renumber(itemlist)

    # Next page
    support.nextPage(itemlist, item, data, r'<a\sclass="page-link"\shref="([^"]+)"\srel="next"\saria-label="Successiva')
    return itemlist


def episodios(item):
    log()
    itemlist = [] 

    data = httptools.downloadpage(item.url).data.replace('\n', '')
    data = re.sub(r'>\s*<', '><', data)
    block1 = scrapertoolsV2.find_single_match(data, r'<div class="widget servers".*?>(.*?)<div id="download"')
    block = scrapertoolsV2.find_single_match(block1,r'<div class="server.*?>(.*?)<div class="server.*?>')
   
    patron = r'<li><a.*?href="([^"]+)".*?>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(block)

    extra = {}
    extra['data'] = block1.replace('<strong>Attenzione!</strong> Non ci sono episodi in questa sezione, torna indietro!.','')

    for scrapedurl, scrapedtitle in matches:
        extra['episode'] = scrapedtitle
        scrapedtitle = '[B] Episodio ' + scrapedtitle + '[/B]'
        itemlist.append(
            Item(
                channel=item.channel,
                action="findvideos",
                contentType="episode",
                title=scrapedtitle,
                url=urlparse.urljoin(host, scrapedurl),
                fulltitle=scrapedtitle,
                show=scrapedtitle,
                plot=item.plot,
                fanart=item.thumbnail,
                extra=extra,
                thumbnail=item.thumbnail))
    
    autorenumber.renumber(itemlist, item,'bold')
    support.videolibrary(itemlist, item)

    return itemlist


def findvideos(item):
    log()

    itemlist = []
    episode = '1'

    if item.extra and item.extra['episode']:
        data = item.extra['data']
        episode = item.extra['episode']
    else:
        data = httptools.downloadpage(item.url,headers=headers).data

    block = scrapertoolsV2.find_single_match(data,r'data-target="\.widget\.servers.*?>(.*?)</div>')
    servers = scrapertoolsV2.find_multiple_matches(block,r'class="tab.*?data-name="([0-9]+)">([^<]+)</span')

    videolist = []
    videoData = ''

    for serverid, servername in servers:
        #recupero l'id del video per questo server
        block = scrapertoolsV2.find_single_match(data,r'<div class="server.*?data-id="'+serverid+'">(.*?)</ul>')
        id = scrapertoolsV2.find_single_match(block,r'<a\sdata-id="([^"]+)"\sdata-base="'+episode+'"')

        dataJson = httptools.downloadpage('%s/ajax/episode/info?id=%s&server=%s&ts=%s' % (host, id, serverid, int(time.time())), headers=[['x-requested-with', 'XMLHttpRequest']]).data
        json = jsontools.load(dataJson)

        videoData +='\n'+json['grabber']

        if serverid == '33':
            post = urllib.urlencode({'r': '', 'd': 'www.animeworld.biz'})
            dataJson = httptools.downloadpage(json['grabber'].replace('/v/','/api/source/'),headers=[['x-requested-with', 'XMLHttpRequest']],post=post).data
            json = jsontools.load(dataJson)
            log(json['data'])
            if json['data']:
                for file in json['data']:
                    itemlist.append(
                        Item(
                            channel=item.channel,
                            action="play",
                            title='diretto',
                            url=file['file'],
                            quality=file['label'],
                            server='directo',
                            show=item.show,
                            contentType=item.contentType,
                            folder=False))

        if serverid == '28':
            itemlist.append(
                Item(
                    channel=item.channel,
                    action="play",
                    title='diretto',
                    quality='',
                    url=json['grabber'],
                    server='directo',
                    show=item.show,
                    contentType=item.contentType,
                    folder=False))


    itemlist += servertools.find_video_items(item,videoData)
    return support.server(item,itemlist=itemlist)

