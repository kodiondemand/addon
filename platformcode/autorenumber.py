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
import re, base64, json, inspect
from core import jsontools, tvdb, scrapertools, filetools
from core.support import typo
from platformcode import config, platformtools, logger

TAG_TVSHOW_RENUMERATE = "TVSHOW_AUTORENUMBER"
TAG_ID = "ID"
TAG_SEASON = "Season"
TAG_EPISODE = "Episode"
TAG_SPECIAL = "Special"
TAG_MODE = "Mode"
TAG_EPLIST = "EpList"
TAG_CHECK = "ReCheck"
TAG_SPLIST = "SpList"
TAG_TYPE = "Type"


def renumber(itemlist, item='', typography=''):
    logger.info()
    dict_series = load(itemlist[0]) if len(itemlist) > 0 else {}

    if item:
        item.channel = item.from_channel if item.from_channel else item.channel
        title = item.fulltitle.rstrip()
        try:
            already_renumbered = scrapertools.find_single_match(itemlist[0].title, r'(\d+\D\d+)')
        except:
            return
        if already_renumbered :
            return itemlist
        elif item.channel in item.channel_prefs and TAG_TVSHOW_RENUMERATE in item.channel_prefs[item.channel] and title not in dict_series:
            from core.videolibrarytools import check_renumber_options
            from specials.videolibrary import update_videolibrary
            check_renumber_options(item)
            update_videolibrary(item)

        elif inspect.stack()[2][3] == 'find_episodes':
            return itemlist

        elif title in dict_series and TAG_ID in dict_series[title]:
            ID = dict_series[title][TAG_ID]
            Episode = dict_series[title][TAG_EPISODE]
            Season = dict_series[title][TAG_SEASON] if TAG_SEASON in dict_series[title] else ''
            Mode = dict_series[title][TAG_MODE] if TAG_MODE in dict_series[title] else False
            Type = dict_series[title][TAG_TYPE] if TAG_TYPE in dict_series[title] else 'auto'

            renumeration(itemlist, item, typography, dict_series, ID, Season, Episode, Mode, title, Type)

        else:
            if config.get_setting('autorenumber', item.channel):
                config_item(item, itemlist, typography, True)
            else:
                return itemlist

    else:
        for item in itemlist:
            title = item.fulltitle.rstrip()
            if title in dict_series and TAG_ID in dict_series[title]:
                ID = dict_series[title][TAG_ID]
                exist = True
            else:
                exist = False

            if item.contentType != 'movie':
                if item.context:
                    context2 = item.context
                    item.show = item.fulltitle = title
                    item.context = context(exist) + context2
                else:
                    item.show = item.fulltitle = title
                    item.context = context(exist)


def config_item(item, itemlist=[], typography='', active=False):
    logger.info()
    # Configurazione Automatica, Tenta la numerazione Automatica degli episodi
    title = item.fulltitle.rstrip()

    dict_series = load(item)
    ID = dict_series[title][TAG_ID] if title in dict_series and TAG_ID in dict_series[title] else ''

    # Pulizia del Titolo
    if any( word in title.lower() for word in ['specials', 'speciali']):
        title = re.sub(r'\sspecials|\sspeciali', '', title.lower())
        tvdb.find_and_set_infoLabels(item)
    elif not item.infoLabels['tvdb_id']:
        item.contentSerieName= title.rstrip('123456789 ')
        tvdb.find_and_set_infoLabels(item)

    if not ID and active:
        if item.infoLabels['tvdb_id']:
            ID = item.infoLabels['tvdb_id']
            dict_renumerate = {TAG_ID: ID}
            dict_series[title] = dict_renumerate
            # Trova La Stagione
            if any(word in title.lower() for word in ['specials', 'speciali']):
                dict_renumerate[TAG_SEASON] = '0'
            elif RepresentsInt(title.split()[-1]):
                dict_renumerate[TAG_SEASON] = title.split()[-1]
            else: dict_renumerate[TAG_SEASON] = '1'
            dict_renumerate[TAG_EPISODE] = ''
            write(item, dict_series)
            return renumber(itemlist, item, typography)
        else:
            return itemlist

    else:
        return renumber(itemlist, item, typography)


def semiautomatic_config_item(item):
    logger.info()
    # Configurazione Semi Automatica, utile in caso la numerazione automatica fallisca
    tvdb.find_and_set_infoLabels(item)
    item.channel = item.from_channel if item.from_channel else item.channel
    dict_series = load(item)
    title = item.fulltitle.rstrip()

    # Trova l'ID della serie
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

        mode = platformtools.dialog_yesno(config.get_localized_string(70687), config.get_localized_string(70688), nolabel=config.get_localized_string(30023), yeslabel=config.get_localized_string(30022))
        if mode == True:
            dict_renumerate[TAG_MODE] = False

            if TAG_SPECIAL in dict_series[title]:
                specials = dict_renumerate[TAG_SPECIAL]
            else:
                specials = []

            write(item, dict_series)
            _list = []

            itemlist = find_episodes(item)
            for item in itemlist:
                Title = re.sub(r'\d+x\d+ - ', '', item.title)
                if item.action == 'findvideos':
                    _list.append(Title)

            selected = platformtools.dialog_multiselect(config.get_localized_string(70734), _list)
            # if len(selected) > 0:
            for select in selected:
                specials.append(int(scrapertools.find_single_match(_list[select], r'(\d+)')))
            dict_renumerate[TAG_SPECIAL] = specials

        dict_renumerate[TAG_MODE] = False

        dict_renumerate[TAG_TYPE] = 'auto'
        dict_renumerate[TAG_EPISODE] = ''
        write(item, dict_series)
        # xbmc.executebuiltin("Container.Refresh")

    else:
        message = config.get_localized_string(60444)
        heading = item.fulltitle.strip()
        platformtools.dialog_notification(heading, message)


def renumeration (itemlist, item, typography, dict_series, ID, Season, Episode, Mode, Title, Type):

    # Se ID è 0 salta la rinumerazione
    if ID == '0':
        return itemlist

    # Numerazione per gli Speciali
    elif Season == '0':
        EpisodeDict = {}
        for item in itemlist:
            if config.get_localized_string(30992) not in item.title:
                number = scrapertools.find_single_match(item.title, r'\d+')
                item.title = typo('0x' + number + ' - ', typography) + item.title


    # Usa la lista degli Episodi se esiste nel Json

    elif Episode:
        EpisodeDict = json.loads(base64.b64decode(Episode))

        # Controlla che la lista egli Episodi sia della stessa lunghezza di Itemlist
        if EpisodeDict == 'none':
            return error(itemlist)
        if Type == 'manual' and len(EpisodeDict) < len(itemlist):
            EpisodeDict = manual_renumeration(item, True)
        if len(EpisodeDict) >= len(itemlist) and scrapertools.find_single_match(itemlist[0].title, r'\d+') in EpisodeDict:
            for item in itemlist:
                if config.get_localized_string(30992) not in item.title:
                    number = scrapertools.find_single_match(item.title, r'\d+')
                    number = int(number) # if number !='0': number.lstrip('0')
                    item.title = typo(EpisodeDict[str(number)] + ' - ', typography) + item.title
        else:
            make_list(itemlist, item, typography, dict_series, ID, Season, Episode, Mode, Title)

    else:
        make_list(itemlist, item, typography, dict_series, ID, Season, Episode, Mode, Title)


def manual_renumeration(item, modify=False):
    logger.info()
    _list = []
    if item.from_channel: item.channel = item.from_channel
    title = item.fulltitle.rstrip()

    dict_series = load(item)

    if title not in dict_series: dict_series[title] = {}

    if TAG_EPISODE in dict_series[title] and dict_series[title][TAG_EPISODE]:
        EpisodeDict = json.loads(base64.b64decode(dict_series[title][TAG_EPISODE]))
        del dict_series[title][TAG_EPISODE]
    else: EpisodeDict = {}

    if TAG_EPLIST in dict_series[title]: del dict_series[title][TAG_EPLIST]
    if TAG_MODE in dict_series[title]: del dict_series[title][TAG_MODE]
    if TAG_CHECK in dict_series[title]: del dict_series[title][TAG_CHECK]
    if TAG_SEASON in dict_series[title]: del dict_series[title][TAG_SEASON]
    if TAG_SPECIAL in dict_series[title]: del dict_series[title][TAG_SPECIAL]
    dict_series[title][TAG_TYPE] = 'manual'
    write(item, dict_series)

    if TAG_ID not in dict_series[title] or (TAG_ID in dict_series[title] and not dict_series[title][TAG_ID]):
        tvdb.find_and_set_infoLabels(item)

        # Trova l'ID della serie
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

    itemlist = find_episodes(item)
    for it in itemlist:
        Title = re.sub(r'\d+x\d+ - ', '', it.title)
        if modify == True:
            ep = int(scrapertools.find_single_match(Title, r'(\d+)'))
            if it.action == 'findvideos' and str(ep) not in EpisodeDict:
                _list.append(Title)
        else:
            if it.action == 'findvideos':
                _list.append(Title)

    count = 1
    preselect = platformtools.dialog_select(config.get_localized_string(70732),[typo(config.get_localized_string(70518),'bold'),typo(config.get_localized_string(70519),'bold')])
    selection = []
    if preselect == 0:
        for i in _list:
            selection.append(_list.index(i))
    while len(_list) > 0:
        selected = platformtools.dialog_multiselect(config.get_localized_string(70734), _list, preselect=selection)
        if selected == None: break
        season = ''
        while not season:
            season = platformtools.dialog_numeric(0, config.get_localized_string(70733))
            count = int(platformtools.dialog_numeric(0, config.get_localized_string(70733).replace('Season','Episode').replace('della Stagione',"dell'Episodio")))

        for select in selected:
            ep = int(scrapertools.find_single_match(_list[select], r'(\d+)'))
            if season == '0':
                episode = ''
                while not episode:
                    episode = platformtools.dialog_numeric(0, config.get_localized_string(70735) % _list[select] )
                EpisodeDict[str(ep)] = '%sx%s' %(season, episode.zfill(2))
            else:
                EpisodeDict[str(ep)] = '%sx%s' %(season, str(count).zfill(2))
                count += 1

        for select in reversed(selected):
            del _list[select]


    dict_series[title][TAG_TYPE] = 'manual'
    EpisodeDict = base64.b64encode(json.dumps(EpisodeDict).encode())
    dict_series[title][TAG_EPISODE] = EpisodeDict.decode()
    write(item, dict_series)
    # xbmc.executebuiltin("Container.Refresh")
    if modify == True:
        return json.loads(base64.b64decode(EpisodeDict))


def delete_renumeration(item):
    logger.info()
    if item.from_channel: item.channel = item.from_channel
    title = item.fulltitle.rstrip()

    dict_series = load(item)
    if title in dict_series: del dict_series[title]
    write(item, dict_series)


def make_list(itemlist, item, typography, dict_series, ID, Season, Episode, Mode, title):
    logger.info()
    exist = True
    item.infoLabels['tvdb_id'] = ID
    tvdb.set_infoLabels_item(item)
    FirstOfSeason= 0

    EpisodeDict = json.loads(base64.b64decode(Episode)) if Episode else {}
    Special = dict_series[title][TAG_SPECIAL] if TAG_SPECIAL in dict_series[title] else []
    EpList = json.loads(base64.b64decode(dict_series[title][TAG_EPLIST])) if TAG_EPLIST in dict_series[title] else []
    Pages = dict_series[title][TAG_CHECK] if TAG_CHECK in dict_series[title] else [1]

    # Ricava Informazioni da TVDB
    checkpages = []
    check = True
    Page = Pages[-1]

    while exist:
        if check:
            for page in Pages:
                data = tvdb.otvdb_global.get_list_episodes(ID,page)
                logger.info('DATA',data)
                for episodes in data['data']:
                    if episodes['firstAired'] and [episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']] not in EpList:
                        EpList.append([episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']])
                    else:
                        if page not in checkpages:
                            checkpages.append(page)
        check = False

        data = tvdb.otvdb_global.get_list_episodes(ID,Page)
        if data:
            Page = Page + 1
            for episodes in data['data']:
                if episodes['firstAired'] and [episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']] not in EpList:
                    EpList.append([episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']])
        else:
            if page not in checkpages:
                checkpages.append(Page -1)
            exist = False

    EpList.sort()

    dict_series[title][TAG_CHECK] = checkpages
    EpList = base64.b64encode(json.dumps(EpList).encode())
    dict_series[title][TAG_EPLIST] = EpList.decode()
    write(item, dict_series)

    # Crea Dizionari per la numerazione
    if EpList:
        EpList = json.loads(base64.b64decode(dict_series[title][TAG_EPLIST]))
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
        if int(Season) > 1:
            for numbers, data in regular.items():
                if data[0] == Season + 'x1':
                    FirstOfSeason = numbers - 1

        if Mode == True: Special = specials

        addiction = 0
        for item in itemlist:
            # Otiene Numerazione Episodi
            scraped_ep = scrapertools.find_single_match(re.sub(r'\[[^\]]+\]','',item.title), r'\d+')
            if scraped_ep:
                episode = int(scraped_ep)
                number = episode + FirstOfSeason - addiction
                count = number + addiction
                # Crea Dizionario Episodi

                if episode == 0:
                    EpisodeDict[str(episode)] = str(complete[regular[FirstOfSeason+1][2]][0])
                elif addiction < len(Special):
                    if episode in Special:
                        try:
                            season = complete[regular[count][2]][0]
                            EpisodeDict[str(episode)] = str(complete[regular[count][2]][0]) if season.startswith( '0' ) else '0x' + platformtools.dialog_numeric(0, item.title + '?', '')

                        except:
                            EpisodeDict[str(episode)] = '0x' + platformtools.dialog_numeric(0, item.title + '?', '')
                        addiction = addiction + 1
                    elif number <= len(regular):
                        EpisodeDict[str(episode)] = str(regular[number][0])
                    else:
                        try: EpisodeDict[str(episode)] = str(complete[regular[number+2][2]][0])
                        except: EpisodeDict[str(episode)] = '0x0'
                elif number <= len(regular) and number in regular:
                    EpisodeDict[str(episode)] = str(regular[number][0])
                else:
                    try: EpisodeDict[str(episode)] = str(complete[regular[number+2][2]][0])
                    except: EpisodeDict[str(episode)] = '0x0'

                # Aggiunge numerazione agli Episodi

                item.title = typo(EpisodeDict[str(episode)] + ' - ', typography) + item.title

        # Scrive Dizionario Episodi sul json
        EpisodeDict = base64.b64encode(json.dumps(EpisodeDict).encode())
        dict_series[title][TAG_EPISODE] = EpisodeDict.decode()
        write(item, dict_series)

    else:
        heading = config.get_localized_string(70704)
        ID = platformtools.dialog_numeric(0, heading)
        dict_series[title][TAG_ID] = ID
        write(item, dict_series)
        if ID == '0':
            return itemlist
        else:
            return make_list(itemlist, item, typography, dict_series, ID, Season, Episode, Mode, title)


def check(item):
    logger.info()
    dict_series = load(item)
    title = item.fulltitle.rstrip()
    if title in dict_series: title = dict_series[title]
    return True if TAG_ID in title and TAG_EPISODE in title else False


def error(itemlist):
    message = config.get_localized_string(70713)
    heading = itemlist[0].fulltitle.strip()
    platformtools.dialog_notification(heading, message)
    return itemlist


def find_episodes(item):
    logger.info()
    ch = __import__('channels.' + item.channel, fromlist=["channels.%s" % item.channel])
    itemlist = ch.episodios(item)
    return itemlist


def RepresentsInt(s):
    # Controllo Numro Stagione
    logger.info()
    try:
        int(s)
        return True
    except ValueError:
        return False


def access():
    allow = False

    if config.is_xbmc():
        allow = True

    return allow


def context(exist):
    if access():
        modify = config.get_localized_string(70714) if exist else ''
        _context = [{"title": typo(modify + config.get_localized_string(70585), 'bold'),
                     "action": "select_type",
                     "channel": "autorenumber",}]

    return _context


def select_type(item):
    select = platformtools.dialog_select(config.get_localized_string(70730),[typo(config.get_localized_string(70731),'bold'), typo(config.get_localized_string(70732),'bold'), typo(config.get_localized_string(707433),'bold')])
    if select == 0: semiautomatic_config_item(item)
    elif select == 1: manual_renumeration(item)
    elif select == 2: return delete_renumeration(item)
    else: return


def filename(item):
    logger.info()
    name_file = item.channel + "_data.json"
    path = filetools.join(config.get_data_path(), "settings_channels")
    fname = filetools.join(path, name_file)

    return fname


def load(item):
    logger.info()
    try:
        json_file = open(filename(item), "r").read()
        json = jsontools.load(json_file)[TAG_TVSHOW_RENUMERATE]

    except:
        json = {}

    return json


def write(item, json):
    logger.info()
    json_file = open(filename(item), "r").read()
    js = jsontools.load(json_file)
    js[TAG_TVSHOW_RENUMERATE] = json
    with open(filename(item), "w") as file:
        file.write(jsontools.dump(js))
        file.close()
