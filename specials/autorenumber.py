# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# autorenumber - Rinomina Automaticamente gli Episodi
# --------------------------------------------------------------------------------

try:
    import xbmcgui
except:
    xbmcgui = None

from core import jsontools, tvdb
from core.support import typo, log
from platformcode import config
from platformcode import platformtools

TAG_TVSHOW_RENUMERATE = "TVSHOW_AUTORENUMBER"
TAG_SEASON_EPISODE = "season_episode"
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
    data = ''
    data = add_season(data)
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
    if item.infoLabels['tvdb_id'] != 0:
        write_data(item.from_channel, title, data)
    else:
        message = config.get_localized_string(60444)
        heading = item.show.strip()
        platformtools.dialog_notification(heading, message)



def add_season(data=None):
    log("data= ", data)
    heading = config.get_localized_string(70686)
    season = platformtools.dialog_numeric(0, heading)
    
    if season != "":
        heading = config.get_localized_string(70687)
        episode = platformtools.dialog_numeric(0, heading)

        if episode == "0":
            heading = config.get_localized_string(70688)
            special = platformtools.dialog_numeric(0, heading)
            return [int(season), int(episode), int(special)]
        elif episode != '':
            return [int(season), int(episode), '']


def write_data(channel, show, data):
    log()
    dict_series = jsontools.get_node_from_file(channel, TAG_TVSHOW_RENUMERATE)
    tvshow = show.strip()
    # list_season_episode = dict_series.get(tvshow, {}).get(TAG_SEASON_EPISODE, [])

    if data:       
        dict_renumerate = {TAG_SEASON_EPISODE: data}
        dict_series[tvshow] = dict_renumerate
    else:
        dict_series.pop(tvshow, None)

    result = jsontools.update_node(dict_series, channel, TAG_TVSHOW_RENUMERATE)[0]

    if result:
        if data:
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
            SERIES = dict_series[item.show.rstrip()]['season_episode']
            S = SERIES[0]
            E = SERIES[1]
            SP = SERIES[2]
            ID = SERIES[3]

            page = 1
            epList = []
            exist = True
            item.infoLabels['tvdb_id'] = ID
            tvdb.set_infoLabels_item(item)
            
            while exist:
                data = tvdb.otvdb_global.get_list_episodes(ID,page)
                if data:
                    for episodes in data['data']:
                        if episodes['airedSeason'] >= S:
                            if E == 0: 
                                epList.append([0, SP])
                                E = 1
                            if episodes['airedEpisodeNumber'] >= E or episodes['airedSeason'] > S:
                                epList.append([episodes['airedSeason'], episodes['airedEpisodeNumber']])
                    page = page + 1
                else:
                    exist = False

            epList.sort()
            ep = 0
            
            for item in itemlist:
                s = str(epList[ep][0])
                e = str(epList[ep][1])
                item.title = typo(s + 'x'+ e + ' - ', typography) + item.title
                ep = ep + 1

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



