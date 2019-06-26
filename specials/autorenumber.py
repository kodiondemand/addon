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
    "label": "Abilita Rinumerazione Automatica", 
    "default": false, 
    "enabled": true, 
    "visible": true
},
{
    "id": "autorenumber_mode",
    "type": "bool",
    "label": "Sono presenti episodi speciali nella serie (Episodio 0 Escluso)?",
    "default": false,
    "enabled": true,
    "visible": "eq(-1,true)"
}
'''

import re, base64, json
from core import jsontools, tvdb, scrapertoolsV2
from core.support import typo, log
from platformcode import config, platformtools
from platformcode.config import get_setting

TAG_TVSHOW_RENUMERATE = "TVSHOW_AUTORENUMBER"
TAG_ID = "ID"
TAG_SEASON = "Season"
TAG_EPISODE = "Episode"
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
                     "action": "manual_config_item",
                     "channel": "autorenumber"}]

    return _context


def manual_config_item(item):
    # Configurazione Semi Automatica, utile in caso la numerazione automatica fallisca

    log(item)
    tvdb.find_and_set_infoLabels(item)
    item.channel = item.from_channel
    dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
    title = item.show
    
    # Trova l'ID dellla serie
    while not item.infoLabels['tvdb_id']:
        try:
            item.show = platformtools.dialog_input(default=item.show, heading=config.get_localized_string(30112))
            tvdb.find_and_set_infoLabels(item)
        except:
            heading = config.get_localized_string(70704)
            item.infoLabels['tvdb_id'] = platformtools.dialog_numeric(0, heading)

    
    if item.infoLabels['tvdb_id']:
        ID = item.infoLabels['tvdb_id']
        dict_renumerate = {TAG_ID: ID}
        dict_series[title] = dict_renumerate
        # Trova la Stagione
        if any( word in title.lower() for word in ['specials', 'speciali'] ):
            heading = config.get_localized_string(70686)
            season = platformtools.dialog_numeric(0, heading, '0')
            dict_renumerate[TAG_SEASON] = season
        elif RepresentsInt(title.split()[-1]):
            heading = config.get_localized_string(70686)
            season = platformtools.dialog_numeric(0, heading, title.split()[-1])
            dict_renumerate[TAG_SEASON] = season
        else:
            heading = config.get_localized_string(70686)
            season = platformtools.dialog_numeric(0, heading, '1')
            dict_renumerate[TAG_SEASON] = season
        # Richede se ci sono speciali nella stagione
        mode = platformtools.dialog_yesno(config.get_localized_string(70687), config.get_localized_string(70688), nolabel=config.get_localized_string(30023), yeslabel=config.get_localized_string(30022))
        if mode == 0: dict_renumerate[TAG_MODE] = False
        else: dict_renumerate[TAG_MODE] = True
        # Imposta la voce Episode
        dict_renumerate[TAG_EPISODE] = []
        # Scrive nel json
        jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]

    else:
        message = config.get_localized_string(60444)
        heading = item.show.strip()
        platformtools.dialog_notification(heading, message)
    


def config_item(item, itemlist=[], typography='', active=False):
    # Configurazione Automatica, Tenta la numerazione Automatica degli episodi
    log()
    title = item.fulltitle

    dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
    try:
        ID = dict_series[item.show.rstrip()][TAG_ID]
    except:
        ID = ''
    
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
            dict_renumerate[TAG_EPISODE] = []
            settings_node = jsontools.get_node_from_file(item.channel, 'settings')
            dict_renumerate[TAG_MODE] = settings_node['autorenumber_mode']
            jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
            return renumber(itemlist, item, typography)
        else:
            return itemlist

    else:
        return renumber(itemlist, item, typography)


def renumber(itemlist, item='', typography=''):
    # Seleziona la funzione Adatta, Menu Contestuale o Rinumerazione
    # import web_pdb; web_pdb.set_trace()
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
            return renumeration(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE)
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
                    item.context = context(exist) + context2
                else:
                    item.context = context(exist)
        
def renumeration (itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE):
    # import web_pdb; web_pdb.set_trace()
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
        log('EPISODE')
        EpisodeDict = json.loads(base64.b64decode(EPISODE))
        # Controlla che la lista egli Episodi sia della stessa lunghezza di Itemlist
        if EpisodeDict == 'none':
            return error(itemlist)
            log(len(EpisodeDict))
            log(len(itemlist))
        if len(EpisodeDict) == len(itemlist):
            for item in itemlist:
                number = scrapertoolsV2.find_single_match(item.title, r'\d+')
                item.title = typo(EpisodeDict[str(number)] + ' - ', typography) + item.title
        else:
            make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE) 

    else:
        make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE)

def make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE):
    log('RINUMERAZIONE')
    page = 1
    EpDict = {}
    EpDateList = []
    EpList = []
    EpisodeDict = {}
    exist = True
    item.infoLabels['tvdb_id'] = ID
    tvdb.set_infoLabels_item(item)
    ABS = 0
    ep = 1
    
    # Ricava Informazioni da TVDB
    while exist:
        data = tvdb.otvdb_global.get_list_episodes(ID,page)
        log('DATA= ',data)
        if data: page = page + 1
        else: exist = False
    
        if data:
            for episodes in data['data']:
                log(episodes)
                try: ABS = int(episodes['absoluteNumber'])
                except: ABS = ep
                EpDict[str(ABS)] = [str(episodes['airedSeason']) + 'x' + str(episodes['airedEpisodeNumber']), episodes['firstAired']]
                EpDateList.append(episodes['firstAired'])
                EpList.append([int(ABS), episodes['airedSeason'], episodes['airedEpisodeNumber']])
                ep = ep + 1        
    EpDateList.sort()
    EpList.sort()
    log(EpDateList)
    log(EpDict)
    log(EpList)
        
    # seleziona l'Episodio di partenza
    if int(SEASON) > 1:
        for name, episode in EpDict.items():
            if episode[0] == SEASON + 'x1':
                ep = int(name)-1
    else:
        ep = 0
        
    # rinumera gli episodi
    Break = False
    for item in itemlist:
        number = int(scrapertoolsV2.find_single_match(item.title, r'\d+'))
        episode = ep + number - 1
        if len(EpList) < episode: return error(itemlist)
        # Crea una lista di Episodi in base alla modalità di rinumerazione            
        if MODE == False and number != 0:
            while Break:
                log('Long= ',len(EpList))
                log('NUMBER= ',EpList[episode][1])
                log('Eisode= ',episode)
                episode = episode + 1 
                if EpList[episode][1] == 0 or len(EpList) <= episode: Break = True
                ep = ep + 1
        elif number == 0:
            episode = previous(EpDateList, EpDict, ep + 1)
        
        if config.get_localized_string(30161) not in item.title: 
            EpisodeDict[str(number)] = (str(EpList[episode][1]) + 'x' + str(EpList[episode][2]))            
            item.title = typo(str(EpList[episode][1]) + 'x' + str(EpList[episode][2]) + ' - ', typography) + item.title  

    # Scrive sul json
    EpisodeDict = base64.b64encode(json.dumps(EpisodeDict))
    dict_series[TITLE][TAG_EPISODE] = EpisodeDict
    jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
    
    return itemlist
    
    

def RepresentsInt(s):
    # Controllo Numro Stagione
    log()
    try: 
        int(s)
        return True
    except ValueError:
        return False

def previous(date_list, Dict, search):
    # Seleziona Eventuale Episodio 0
    log()
    P = None
    result = 0
    for ep, variants in Dict.items():
        if variants[1] == Dict[str(search)][1]:
         date = variants[1]
    for index, obj in enumerate(date_list):
        if obj == date:
            if index > 0:
                P = date_list[index - 1]
    for name, variants in Dict.items():
        log(variants[1], ' = ', P)
        if variants[1] == P:
            result = int(name)-1
    return result

def error(itemlist):
    message = config.get_localized_string(70713)
    heading = itemlist[0].fulltitle.strip()
    platformtools.dialog_notification(heading, message)
    return itemlist