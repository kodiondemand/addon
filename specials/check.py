# -*- coding: utf-8 -*-
# -*- Scritto per KOD -*-
# versione: 0.1

##import sys
##import os
##import json
##import xbmc
##import xbmcaddon, xbmcgui
import kdicc
##
##from core import channeltools, scrapertools
##from platformcode import logger, config, platformtools
##from core.item import Item


"""
    Abbinato allo script kdicc permette di modificare gli url del file channels_active.json ( poi channels.json ):
        1. riscrivere l'url in caso di redirect
        2.
            a. disattivare il canale in caso di problemi al sito
            b. riattivare il canale quando l'url viene raggiunto nuovamente

    quando far partire il check?
    1. all'inizio per controllare i file nel channels_not_active (pochi)
    2. durante l'apertura del canale
    3. nelle varie ricerche globali

    Problematiche:

    1. i redirect sono gestiti in locale
    2. se il canale viene disattivato bisogna scrivere nel json:
        a. del canale per disattivarlo
        b. inserire il canale nel channels_not_active
"""

class CheckHost(object):

    def __init__(self):
        pass

    def http_code():
        pass

def checkHost(item, itemlist):
    # nel caso non ci siano risultati puo essere che l'utente abbia cambiato manualmente l'host, pertanto lo riporta
    # al valore di default (fixa anche il problema del cambio di host da parte nostra)
    if len(itemlist) == 0:
        # trovo il valore di default

        defHost = None
        for s in channeltools.get_channel_json(item.channel)['settings']:
            if s['id'] == 'channel_host':
                defHost = s['default']
                break
        # lo confronto con quello attuale
        if config.get_setting('channel_host', item.channel) != defHost:
            config.set_setting('channel_host', defHost, item.channel)

##
##def host_check(itemlist, item=None):
##    """
##        se item == None allora siamo nello start()
##
##    :param itemlist:
##    :param item:
##    :return:
##    """
##    #import web_pdb; web_pdb.set_trace()
##    logger.info("host_check item, itemlist : %s %s " % (item, itemlist))
##
##    if not item:
##        logger.info("%s %s " % (item, itemlist))
##        check_host(itemlist = '', item=None)
##    else:
##        pass
##
##
##def check_host(itemlist, item=None):
##    #import web_pdb; web_pdb.set_trace()
##    if not item:
##        logger.info("ITEM : %s " % (item))
##        channel_path = os.path.join(config.get_runtime_path(), "")
##        file = 'channel_not_active.json'
##        # leggo dal file channel_not_active
##        with open(channel_path+file, 'r') as json_file:
##            data = ''
##            try:
##                data = json.load(json_file)
##                logger.info("Json data : %s " % (data))
##            except:
##                logger.info("Json except : %s " % (data))
##        if len(data) !=0:
##            logger.info("IF len(data) : %s " % len(data))
##            for canale in data:
##                url_org = str(data[canale])
##
##
##        # X debug, da togliere
##        else:
##            logger.info("ELSE len(data) : %s " % len(data))
##
##    else:
##        logger.info()
##
##        channel_path = os.path.join(config.get_runtime_path(), "")
##        file = 'channels.json'
##        #logger.info("canale Json data : %s " % canale)
##        new_domain = []
##        error_domain = []
##        nonraggiungibile_domain = []
##        code_error = []
##        with open(channel_path+file, 'r') as json_file:
##            data = json.load(json_file)
##            logger.info("Json data : %s " % (data))#, data['settings']))
##
##        for canale in data:
##            url_org = str(data[canale])
##            try:
##                res = requests.get(url_org)
##                url = str(res.url)
##                logger.info("Canale : %s " % canale)
##                logger.info("R = %s" % res.status_code)
##                logger.info("siamo qui data[canale]: %s " % url_org) # contiene l'url nuovo se c'è link
##                logger.info("siamo qui res.url: %s " % url) # contiene l'url nuovo se c'è link
##
##                if url.endswith('/') == True:
##                    url = url[:-1]
##
##                logger.info("url_org -> %s" % url_org)
##                logger.info("url -> %s" % url)
##                logger.info("################")
##
##                if url_org != url:
##                    new_domain.append((canale, url_org, url))
##                if res.status_code == 200:
##                    pass
##                elif res.status_code == 301:
##                    code_error.append(res.status_code)
##                elif str(res.status_code).startswith('5'):
##                    code_error.append(res.status_code)
##                    logger.info("res.code 5XX: %s " % res.status_code)
##    ##            elif res.status_code ==
##    ##            if res.code == 503:
##    ##                # disabilitare il canale
##    ##                logger.info("res.code non è 200: %s " % res.code)
##    ##                error_domain.append((canale, data[canale]))
##    ##            if res.code == 200 and 'link' in res.headers:
##    ##                logger.info("res.code è 200 and 'link': %s " % res.code)
##    ##                host_red = res.headers['link']
##    ##                pat = r'<([a-zA-Z0-9-\.\/:]+)/wp-json/>;'
##    ##                host_red = scrapertools.find_single_match(host_red, pat)
##    ##                logger.info("host_red: %s " % host_red)
##    ##                # confronto i 2 link, se non sono uguali c'è un redirect
##    ##                if host_red != data[canale]:
##    ##                    logger.info("host_red host_link: %s - %s " % (host_red, data[canale]))
##    ##                    new_domain.append((canale, host_red))
##    ##                    logger.info("data modificato link: %s " % canale)
##    ##
##    ##            logger.info("fuori dagli if': %s " % res.code)
##            except requests.RequestException as e:
##                """
##                    Il sito risulta non raggiungibile per qualche motivo
##                    quindi verrà disabilitato
##                """
##                logger.info("DICT: %s " % dict(error=e.message))
##                logger.info("Canale : %s " % canale)
##                logger.info("siti non raggiungibili: %s %s" % (url_org, res.status_code))
##                logger.info("################")
##                nonraggiungibile_domain.append((canale, url_org))
##
##        logger.info("new_domain: %s " % new_domain)
##        logger.info("code_error: %s " % code_error)
##        logger.info("error_domain: %s " % error_domain)
##        logger.info("nonraggiungibile_domain: %s " % nonraggiungibile_domain)
