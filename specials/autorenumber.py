# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# autorenumber - Rinomina Automaticamente gli Episodi
# --------------------------------------------------------------------------------

'''
USO:
1) utilizzare autorenumber.renumber(itemlist) nelle le funzioni peliculas e similari per aggiungere il menu contestuale
2) utilizzare autorenumber.renumber(itemlist, item, typography) nella funzione episodios

3) Aggiungere le seguinti stringhe nel json del canale (per attivare la configurazione di autonumerazione del canale)
{
    "id": "autorenumber", 
    "type": "bool", 
    "label": "@70712", 
    "default": false, 
    "enabled": true, 
    "visible": true
},
{
    "id": "autorenumber_mode",
    "type": "bool",
    "label": "@70688",
    "default": false,
    "enabled": true,
    "visible": "eq(-1,true)"
}
'''

try:
    import xbmcgui
except:
    xbmcgui = None

import re, base64, json, os
from core import jsontools, tvdb, scrapertoolsV2
from core.support import typo, log
from platformcode import config, platformtools,  logger
from platformcode.config import get_setting

TAG_TVSHOW_RENUMERATE = "TVSHOW_AUTORENUMBER"
TAG_ID = "ID"
TAG_SEASON = "Season"
TAG_EPISODE = "Episode"
TAG_SPECIAL = "Special"
TAG_MODE = "Mode"

__channel__ = "autorenumber"

def access():
    allow = False

    if config.is_xbmc():
        allow = True

    return allow

def context(exist):
    if access():
        modify = config.get_localized_string(70714) if exist else ''
        _context = [{"title": typo(modify + config.get_localized_string(70585), 'bold'),
                     "action": "semiautomatic_config_item",
                     "channel": "autorenumber"}]

    return _context

def semiautomatic_config_item(item):
    log()
    # Configurazione Semi Automatica, utile in caso la numerazione automatica fallisca

    tvdb.find_and_set_infoLabels(item)
    item.channel = item.from_channel
    dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
    title = item.show
    
    # Trova l'ID dellla serie
    while not item.infoLabels['tvdb_id']:
        try:
            item.show = platformtools.dialog_input(default=item.show, heading=config.get_localized_string(30112)) # <- Enter title to search
            tvdb.find_and_set_infoLabels(item)
        except:
            heading = config.get_localized_string(70704) # <- TMDB ID (0 to cancel)
            info = platformtools.dialog_numeric(0, heading)
            item.infoLabels['tvdb_id'] = '0' if info == '' else info

    
    if item.infoLabels['tvdb_id']:
        ID = item.infoLabels['tvdb_id']
        dict_renumerate = {TAG_ID: ID}
        dict_series[title] = dict_renumerate
        # Trova la Stagione
        if any( word in title.lower() for word in ['specials', 'speciali'] ):
            heading = config.get_localized_string(70686) # <- Enter the number of the starting season (for specials)
            season = platformtools.dialog_numeric(0, heading, '0')
            dict_renumerate[TAG_SEASON] = season
        elif RepresentsInt(title.split()[-1]):
            heading = config.get_localized_string(70686) # <- Enter the number of the starting season (for season > 1)
            season = platformtools.dialog_numeric(0, heading, title.split()[-1])
            dict_renumerate[TAG_SEASON] = season
        else:
            heading = config.get_localized_string(70686) # <- Enter the number of the starting season (for season 1)
            season = platformtools.dialog_numeric(0, heading, '1')
            dict_renumerate[TAG_SEASON] = season
        
        ########### PROVVISORIO ###################
        mode = platformtools.dialog_yesno(config.get_localized_string(70687), config.get_localized_string(70688), nolabel=config.get_localized_string(30023), yeslabel=config.get_localized_string(30022))
        if mode == 1:
            dict_renumerate[TAG_MODE] = False
            specials = []
            stop = False
            while not stop:
                heading = config.get_localized_string(70718) + str(specials)
                special = platformtools.dialog_numeric(0, heading, '')
                if special:
                    specials.append(int(special))
                    dict_renumerate[TAG_SPECIAL] = specials
                else: stop = True
        dict_renumerate[TAG_MODE] = False
        # Richede se ci sono speciali nella stagione
        # mode = platformtools.dialog_yesno(config.get_localized_string(70687), config.get_localized_string(70688), nolabel=config.get_localized_string(30023), yeslabel=config.get_localized_string(30022))
        # if mode == 0: dict_renumerate[TAG_MODE] = False
        # else: 
        #     select = platformtools.dialog_yesno(config.get_localized_string(70687), config.get_localized_string(70717), nolabel=config.get_localized_string(30023), yeslabel=config.get_localized_string(30022))
        #     if select == 0:
        #         dict_renumerate[TAG_MODE] = False
        #         specials = []
        #         stop = False
        #         while not stop:
        #             heading = config.get_localized_string(70718) + str(specials)
        #             special = platformtools.dialog_numeric(0, heading, '')
        #             if special:
        #                 specials.append(int(special))
        #                 dict_renumerate[TAG_SPECIAL] = specials
        #             else: stop = True
        #     else:
        #         dict_renumerate[TAG_MODE] = True
        ########### PROVVISORIO ###################


        # Imposta la voce Episode
        dict_renumerate[TAG_EPISODE] = ''
        # Scrive nel json
        jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]

    else:
        message = config.get_localized_string(60444)
        heading = item.show.strip()
        platformtools.dialog_notification(heading, message)
    


def config_item(item, itemlist=[], typography='', active=False):
    log()
    # Configurazione Automatica, Tenta la numerazione Automatica degli episodi
    title = item.fulltitle

    dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
    try: ID = dict_series[item.show.rstrip()][TAG_ID]
    except: ID = ''
  
    # Pulizia del Titolo    
    if any( word in title.lower() for word in ['specials', 'speciali']):
        item.show = re.sub(r'\sspecials|\sspeciali', '', item.show.lower())
        log('ITEM SHOW= ',item.show)
        tvdb.find_and_set_infoLabels(item)  
    elif not item.infoLabels['tvdb_id']:
            item.show = title.rstrip('123456789 ')
            tvdb.find_and_set_infoLabels(item)   

    if not ID and active:
        if item.infoLabels['tvdb_id']:
            ID = item.infoLabels['tvdb_id']
            dict_renumerate = {TAG_ID: ID}
            dict_series[title] = dict_renumerate
            # Trova La Stagione
            if any( word in title.lower() for word in ['specials', 'speciali']):
                dict_renumerate[TAG_SEASON] = '0'
            elif RepresentsInt(title.split()[-1]):
                dict_renumerate[TAG_SEASON] = title.split()[-1]
            else: dict_renumerate[TAG_SEASON] = '1'
            dict_renumerate[TAG_EPISODE] = ''
            settings_node = jsontools.get_node_from_file(item.channel, 'settings')
            dict_renumerate[TAG_MODE] = settings_node['autorenumber_mode']
            jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
            return renumber(itemlist, item, typography)
        else:
            return itemlist

    else:
        return renumber(itemlist, item, typography)


def renumber(itemlist, item='', typography=''):
    log()
    # Seleziona la funzione Adatta, Menu Contestuale o Rinumerazione
    if item:
        settings_node = jsontools.get_node_from_file(item.channel, 'settings')
        # Controlla se la Serie è già stata rinumerata 

        try:  
            dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
            TITLE = item.fulltitle.rstrip()
            ID = dict_series[TITLE][TAG_ID]
            
            exist = True        
        except:
            exist = False
           
        if exist:
            ID = dict_series[TITLE][TAG_ID]
            SEASON = dict_series[TITLE][TAG_SEASON]
            EPISODE = dict_series[TITLE][TAG_EPISODE]
            MODE = dict_series[TITLE][TAG_MODE]
            renumeration(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE)
        else:
            # se non è stata rinumerata controlla se è attiva la rinumerazione automatica
            if 'autorenumber' not in settings_node: return itemlist
            if settings_node['autorenumber'] == True:
                    config_item(item, itemlist, typography, True)
    else:
        for item in itemlist:
            try:
                dict_series = jsontools.get_node_from_file(itemlist[0].channel, TAG_TVSHOW_RENUMERATE)
                TITLE = item.show.rstrip()
                ID = dict_series[TITLE][TAG_ID]
                exist = True        
            except:
                exist = False
            if item.contentType != 'movie':
                if item.context:
                    context2 = item.context
                    item.show = TITLE
                    item.context = context(exist) + context2
                else:
                    item.show = TITLE
                    item.context = context(exist)
        
def renumeration (itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE):
    log()
    # Se ID è 0 salta la rinumerazione
    if ID == '0':
        return itemlist

    # Numerazione per gli Speciali
    elif SEASON == '0':
        EpisodeDict = {}
        for item in itemlist:
            number = scrapertoolsV2.find_single_match(item.title, r'\d+')
            item.title = typo('0x' + number + ' - ', typography) + item.title
            
    
    # Usa la lista degli Episodi se esiste nel Json
        
    elif EPISODE:
        EpisodeDict = json.loads(base64.b64decode(EPISODE))

        # Controlla che la lista egli Episodi sia della stessa lunghezza di Itemlist
        if EpisodeDict == 'none':
            return error(itemlist)
        if len(EpisodeDict) >= len(itemlist):
            for item in itemlist:
                number = scrapertoolsV2.find_single_match(item.title, r'\d+')
                item.title = typo(EpisodeDict[str(number)] + ' - ', typography) + item.title
        else:
            make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE) 

    else:
        make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE)

def make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE):
    log()
    page = 1
    EpList = []
    EpisodeDict = {}
    exist = True
    item.infoLabels['tvdb_id'] = ID
    tvdb.set_infoLabels_item(item)
    FirstOfSeason= 0
    try: SPECIAL = dict_series[TITLE][TAG_SPECIAL]
    except: SPECIAL = []
    
    # Ricava Informazioni da TVDB
    while exist:
        data = tvdb.otvdb_global.get_list_episodes(ID,page)
        if data: page = page + 1
        else: exist = False

        if data:
            for episodes in data['data']:
                EpList.append([episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']])
        EpList.sort()
        log(EpList)
    
    # Crea Dizionari per la numerazione
    if EpList:
        specials = []
        regular = {}
        complete = {}
        allep = 1
        ep = 1
        specialep = 0
        for episode in EpList:
            complete[allep] = [str(episode[1]) + 'x' + str(episode[2]), episode[0]]
            if episode[1] == 0:
                specials.append(allep)
                specialep = specialep + 1
            else:
                regular[ep] = [str(episode[1]) + 'x' + str(episode[2]), str(episode[0]), allep - 1]
                ep = ep + 1
            allep = allep + 1
            
        # seleziona l'Episodio di partenza
        if int(SEASON) > 1:
            for numbers, data in regular.items():
                if data[0] == SEASON + 'x1':
                    FirstOfSeason = numbers - 1

        if MODE == True: SPECIAL = specials
        log(SPECIAL)
        log(complete)
        log(regular)
    
        addiction = 0
        for item in itemlist:
            # Otiene Numerazione Episodi
            episode = int(scrapertoolsV2.find_single_match(item.title, r'\d+'))
            number = episode + FirstOfSeason - addiction
            count = number + addiction
            # find = episode + FirstOfSeason
            # log('FIND= ',find, ' ',str(episode) + ' ' + str(FirstOfSeason))
            # Crea Dizionario Episodi
            
            # log(episode, ' ', number, ' ', count)
            if episode == 0:
                EpisodeDict[str(episode)] = str(complete[regular[FirstOfSeason+1][2]][0])
            elif addiction < len(SPECIAL):
                if episode in SPECIAL:
                    season = complete[regular[count][2]][0]
                    EpisodeDict[str(episode)] = str(complete[regular[count][2]][0]) if season.startswith( '0' ) else '0x' + platformtools.dialog_numeric(0, item.title + '?', '')
                    addiction = addiction + 1
                else:
                    EpisodeDict[str(episode)] = str(regular[number][0])
            elif number <= len(regular):
                EpisodeDict[str(episode)] = str(regular[number][0])
            else:
                try: EpisodeDict[str(episode)] = str(complete[regular[number+2][2]][0])
                except: EpisodeDict[str(episode)] = '0x0'

            # Aggiunge numerazione agli Episodi
            
            item.title = typo(EpisodeDict[str(episode)] + ' - ', typography) + item.title

        # Scrive Dizionario Episodi sul json
        EpisodeDict = base64.b64encode(json.dumps(EpisodeDict))
        dict_series[TITLE][TAG_EPISODE] = EpisodeDict
        jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
    
    else:
        heading = config.get_localized_string(70704)
        ID = platformtools.dialog_numeric(0, heading)
        dict_series[TITLE][TAG_ID] = ID
        jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
        if ID == '0':
            return itemlist
        else:
            return make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE)

    # return itemlist
    
    

def RepresentsInt(s):
    # Controllo Numro Stagione
    log()
    try: 
        int(s)
        return True
    except ValueError:
        return False

def error(itemlist):
    message = config.get_localized_string(70713)
    heading = itemlist[0].fulltitle.strip()
    platformtools.dialog_notification(heading, message)
    return itemlist
