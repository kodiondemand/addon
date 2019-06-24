# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# autorenumber - Rinomina Automaticamente gli Episodi
# --------------------------------------------------------------------------------

try:
    import xbmcgui
except:
    xbmcgui = None

from core import jsontools, tvdb, scrapertoolsV2
from core.support import typo, log
from platformcode import config
from platformcode import platformtools
# from datetime import datetime

TAG_TVSHOW_RENUMERATE = "TVSHOW_AUTORENUMBER"
TAG_ID = "ID"
TAG_SEASON = "Season"
__channel__ = "autorenumber"

def access():
    allow = False

    if config.is_xbmc():
        allow = True

    return allow


def context():
    if access():
        _context = [{"title": config.get_localized_string(70585),
                     "action": "config_item",
                     "channel": "autorenumber"}]

    return _context


def config_item(item):
    log(item)
    tvdb.find_and_set_infoLabels(item)
    data = []
    title = item.show
    count = 0
    
    while not item.infoLabels['tvdb_id']:
        try:
            item.show = platformtools.dialog_input(default=item.show, heading=config.get_localized_string(30112))
            tvdb.find_and_set_infoLabels(item)
            count = count + 1
        except:
            heading = config.get_localized_string(70704)
            item.infoLabels['tvdb_id'] = platformtools.dialog_numeric(0, heading)
    data.append(item.infoLabels['tvdb_id'])
    if item.infoLabels['tvdb_id'] != '':
        write_data(item.from_channel, title, item.infoLabels['tvdb_id'])
    else:
        message = config.get_localized_string(60444)
        heading = item.show.strip()
        platformtools.dialog_notification(heading, message)





def write_data(channel, show, ID):
    log()
    dict_series = jsontools.get_node_from_file(channel, TAG_TVSHOW_RENUMERATE)
    tvshow = show.strip()

    if ID:       
        dict_renumerate = {TAG_ID: ID}
        dict_series[tvshow] = dict_renumerate
    else:
        dict_series.pop(tvshow, None)

    # Cerca di individuare la serie dal titolo
    if any( word in show.lower() for word in ['special', 'specials', 'speciali', 'speciale'] ):
        heading = config.get_localized_string(70686)
        season = platformtools.dialog_numeric(0, heading, '0')
        dict_renumerate[TAG_SEASON] = season
    elif RepresentsInt(show.split()[-1]):
        heading = config.get_localized_string(70686)
        season = platformtools.dialog_numeric(0, heading, show.split()[-1])
        dict_renumerate[TAG_SEASON] = season
    else: dict_renumerate[TAG_SEASON] = '1'
    
    
    result = jsontools.update_node(dict_series, channel, TAG_TVSHOW_RENUMERATE)[0]

    if result:
        if ID:
            message = config.get_localized_string(60446)
        else:
            message = config.get_localized_string(60444)
    else:
        message = config.get_localized_string(70593)
 
    heading = show.strip()
    platformtools.dialog_notification(heading, message)



def renumber(itemlist, item='', typography=''):
    log()

    if item:
        try:  
            dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
            ID = dict_series[item.show.rstrip()]['ID']
            SEASON = dict_series[item.show.rstrip()]['Season']

            page = 1
            epDict = {}
            epList = []
            exist = True
            item.infoLabels['tvdb_id'] = ID
            tvdb.set_infoLabels_item(item)
            ep = 1
        
            while exist:
                data = tvdb.otvdb_global.get_list_episodes(ID,page)
                log(data)
                if data:
                    for episodes in data['data']:
                        log(episodes)
                        if hasattr(episodes,'absoluteNumber'): ABS = episodes['absoluteNumber']
                        else: ABS = str(ep)
                        epDict[str(ABS)] = [str(episodes['airedSeason']) + 'x' + str(episodes['airedEpisodeNumber']), episodes['firstAired']]
                        epList.append(episodes['firstAired'])
                        ep = ep + 1
                        
                    page = page + 1
                else:
                    exist = False
            log(epDict)
            epList.sort()
            log(epList)    
            
            if SEASON:
                for name, episode in epDict.items():
                    if episode[0] == SEASON + 'x1':
                        ep = int(name)-1
            else:
                ep = 0
                
            if SEASON != '0':
                for item in itemlist:
                    number = int(scrapertoolsV2.find_single_match(item.title, r'\d+'))
                    episode = str(ep + number)
                    if number == 0:
                        episode = previous(epList, epDict, str(ep + 1))                    
                    item.title = typo(epDict[episode][0] + ' - ', typography) + item.title
            else:
                for item in itemlist:
                    number = scrapertoolsV2.find_single_match(item.title, r'\d+')
                    item.title = typo('0x' + number + ' - ', typography) + item.title

        except:
            return itemlist
    else:
        for item in itemlist:
            if item.contentType != 'movie':
                if item.context:
                    context2 = item.context
                    item.context = context() + context2
                else:
                    item.context = context()

    return itemlist


def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def previous(date_list, Dict, search):
    log('Start')
    P = None
    for ep, variants in Dict.items():
        if variants[1] == Dict[search][1]:
         date = variants[1]
    for index, obj in enumerate(date_list):
        if obj == date:
            if index > 0:
                P = date_list[index - 1]
    for name, variants in Dict.items():
        log(variants[1], ' = ', P)
        if variants[1] == P:
            result = name
    log(result)
    return result