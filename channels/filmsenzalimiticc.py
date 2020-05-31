# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Filmsenzalimiti CC
# ------------------------------------------------------------
import re

try:
    import urlparse
except:
    import urllib.parse as urlparse

from core import scrapertools, servertools, httptools
from core import tmdb
from core.item import Item
from platformcode import config
from platformcode import logger
from specials import autoplay

# Necessario per Autoplay
host = config.get_channel_url()

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'vidlox', 'youtube']
list_quality = ['default']

# Necessario per Verifica Link
checklinks = config.get_setting('checklinks', 'filmsenzalimiticc')
checklinks_number = config.get_setting('checklinks_number', 'filmsenzalimiticc')

headers = [['Referer', host]]



def mainlist(item):
    logger.info('[filmsenzalimiticc.py] mainlist')
    
    autoplay.init(item.channel, list_servers, list_quality) # Necessario per Autoplay

    # Menu Principale
    itemlist = [Item(channel=item.channel,
                     action='video',
                     title='Film',
                     url=host,
                     contentType='movie',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='sottomenu_film',
                     title='Categorie Film',
                     url=host,
                     contentType='movie',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='video',
                     title='Serie TV',
                     url=host+'/serie-tv/',
                     contentType='tvshow',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='sottomenu_serie',
                     title='[B]Categorie Serie TV[/B]',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='search',
                     extra='tvshow',
                     title='[B]Cerca... (non funziona)[/B]',
                     thumbnail='')
                ]
    
    autoplay.show_option(item.channel, itemlist) # Necessario per Autoplay (Menu Configurazione)
    
    return itemlist
    
def search(item, texto):
    logger.info('[filmsenzalimiticc.py] search')

    item.url = host + '/?s=' + texto

    try:
        return video(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error('%s' % line)
        return []
        
def sottomenu_film(item):
    logger.info('[filmsenzalimiticc.py] sottomenu_film')
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti
    patron = "<li><a href='([^']+)'>(.*?)<"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=__channel__,
                 action='video',
                 contentType=item.contentType,
                 title=scrapedtitle,
                 url=scrapedurl))

    # Elimina le Serie al Sottomenù
    itemlist.pop(3)
    itemlist.pop(29)
    itemlist.pop(29)
    itemlist.pop(32)

    return itemlist
    
def sottomenu_serie(item):
    logger.info('[seriehd.py] sottomenu_serie')
    itemlist = [
                Item(channel=item.channel,
                     action='video',
                     title='Serie TV HD',
                     url=host+'/watch-genre/serie-altadefinizione/',
                     contentType='tvshow',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='video',
                     title='Miniserie',
                     url=host+'/watch-genre/miniserie/',
                     contentType='tvshow',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='video',
                     title='Programmi TV',
                     url=host+'/watch-genre/programmi-tv/',
                     contentType='tvshow',
                     thumbnail='')   
                ]
                
    return itemlist


def video(item):
    logger.info('[filmsenzalimiticc.py] video')
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data.replace('\n','').replace('\t','')

    # Estrae i contenuti 
    patron = r'<div class="mediaWrap mediaWrapAlt">.*?<a href="([^"]+)".*?src="([^"]+)".*?<p>([^"]+) (\(.*?)streaming<\/p>.*?<p>\s*(\S+).*?<\/p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedquality in matches:
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedyear = scrapertools.decodeHtmlentities(scrapedyear)
        scrapedquality = scrapertools.decodeHtmlentities(scrapedquality)

        year = scrapedyear.replace('(','').replace(')','')
        infolabels = {}
        if year:
            infolabels['year'] = year

        title = scrapedtitle + ' '+ scrapedyear +' [' + scrapedquality + ']'
        
        # Seleziona fra Serie TV e Film
        if item.contentType == 'movie':
            azione = 'findvideos'
            tipologia = 'movie'
        if item.contentType == 'tvshow':
            azione='episodios'
            tipologia = 'tv'
        
        itemlist.append(
            Item(channel=item.channel,
                 action=azione,
                 contentType=item.contentType,
                 title=title,
                 fulltitle=scrapedtitle,
                 text_color='azure',
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 infoLabels=infolabels,
                 show=scrapedtitle))

    # Next page
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink".*?href="([^"]+)">')

    if next_page != '':
        itemlist.append(
            Item(channel=item.channel,
                 action='film',
                 title='[COLOR lightgreen]' + config.get_localized_string(30992) + '[/COLOR]',
                 url=next_page,
                 contentType=item.contentType,
                 thumbnail='http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png'))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist



def findvideos(item): # Questa def. deve sempre essere nominata findvideos
    logger.info('[filmsenzalimiticc.py] findvideos')
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    
    # Aggira protectlink
    if 'protectlink' in data:
        urls = scrapertools.find_multiple_matches(data, r'<iframe src="[^=]+=(.*?)"')
        for url in urls:
            url= url.decode('base64')
            if '\t' in url:    #fix alcuni link presentano una tabulazione finale.
                url = url[:-1]
            data += '\t' + url
        if 'nodmca' in data:    #fix player Openload sezione Serie TV
            page = httptools.downloadpage(url, headers=headers).data
            data += '\t' + scrapertools.find_single_match(page,'<meta name="og:url" content="([^=]+)">')
            
           

    itemlist = servertools.find_video_items(data=data)    

    for videoitem in itemlist:
        videoitem.title = item.fulltitle + ' - [[COLOR limegreen]'+videoitem.title+'[/COLOR] ]'
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    # Link Aggiungi alla Libreria
    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findservers':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR lightblue][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     action='add_pelicula_to_library', extra='findservers', contentTitle=item.contentTitle))

    # Necessario per  FilterTools
    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Necessario per  AutoPlay
    autoplay.start(itemlist, item)
    
    
    
    return itemlist



def episodios(item): # Questa def. deve sempre essere nominata episodios
    logger.info('[filmsenzalimiticc.py] episodios')
    itemlist = []
    
    # Trova le Stagioni
    
    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti
    patron = r'<iframe src="([^"]+)".*?>'
    url = scrapertools.find_single_match(data, patron)

    # Carica la pagina 
    data = httptools.downloadpage(url).data.replace('\t', '').replace('\n', '')

    # Estrae i contenuti
    section_stagione = scrapertools.find_single_match(data, r'Stagioni<\/a>(.*?)<\/ul>')
    patron = r'<a href="([^"]+)" >.*?<\/i>\s(.*?)<\/a>'
    seasons = re.compile(patron, re.DOTALL).findall(section_stagione)

    for scrapedseason_url, scrapedseason in seasons:

        # Trova gli Episodi
        
        season_url = urlparse.urljoin(url, scrapedseason_url)
        
        # Carica la pagina 
        data = httptools.downloadpage(season_url).data.replace('\t', '').replace('\n', '')

        # Estrae i contenuti
        section_episodio = scrapertools.find_single_match(data, r'Episodio<\/a>(.*?)<\/ul>')
        patron = r'<a href="([^"]+)" >.*?<\/i>\s(.*?)<\/a>'
        episodes = re.compile(patron, re.DOTALL).findall(section_episodio)

        for scrapedepisode_url, scrapedepisode in episodes:
            episode_url = urlparse.urljoin(url, scrapedepisode_url)

            title = scrapedseason + 'x' + scrapedepisode.zfill(2)

            itemlist.append(
                Item(channel=item.channel,
                     action='findvideos',
                     contentType='episode',
                     title=title,
                     url=episode_url,
                     fulltitle=title + ' - ' + item.show,
                     show=item.show,
                     thumbnail=item.thumbnail))
    
    # Link Aggiungi alla Libreria
    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR lightblue][B]Aggiungi Serie alla videoteca[/B][/COLOR]',
                 url=item.url,
                 action='add_serie_to_library',
                 extra='episodios' + '###' + item.extra,
                 show=item.show))

    return itemlist



