# -*- coding: utf-8 -*-
# -*- Tools for trakt sync -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*

import os
from threading import Thread

import xbmc

from core import httptools
from core import jsontools
from core.item import Item
from platformcode import config
from platformcode import logger

client_id = "c40ba210716aee87f6a9ddcafafc56246909e5377b623b72c15909024448e89d"
client_secret = "999164f25832341f0214453bb11c915adb18e9490d6b5e9a707963a5a1bee43e"


def auth_trakt():
    item = Item()
    folder = (config.get_platform() == "plex")
    item.folder = folder
    # Autentificación de cuenta Trakt
    headers = {'Content-Type': 'application/json', 'trakt-api-key': client_id, 'trakt-api-version': '2'}
    try:
        post = {'client_id': client_id}
        post = jsontools.dump(post)
        # Se solicita url y código de verificación para conceder permiso a la app
        url = "http://api-v2launch.trakt.tv/oauth/device/code"
        data = httptools.downloadpage(url, post=post, headers=headers, replace_headers=True).data
        data = jsontools.load(data)
        item.verify_url = data["verification_url"]
        item.user_code = data["user_code"]
        item.device_code = data["device_code"]
        item.intervalo = data["interval"]
        if not item.folder:
            token_trakt(item)

        else:
            itemlist = []
            title = config.get_localized_string(60248) % item.verify_url
            itemlist.append(item.clone(title=title, action=""))
            title = config.get_localized_string(60249) % item.user_code
            itemlist.append(item.clone(title=title, action=""))
            title = config.get_localized_string(60250)
            itemlist.append(item.clone(title=title, action="token_trakt"))
            return itemlist
    except:
        import traceback
        logger.error(traceback.format_exc())


def token_trakt(item):
    from platformcode import platformtools

    headers = {'Content-Type': 'application/json', 'trakt-api-key': client_id, 'trakt-api-version': '2'}
    try:
        if item.extra == "renew":
            refresh = config.get_setting("refresh_token_trakt", "trakt")
            url = "http://api-v2launch.trakt.tv/oauth/device/token"
            post = {'refresh_token': refresh, 'client_id': client_id, 'client_secret': client_secret,
                    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 'grant_type': 'refresh_token'}
            post = jsontools.dump(post)
            data = httptools.downloadpage(url, post, headers, replace_headers=True).data
            data = jsontools.load(data)
        elif item.action == "token_trakt":
            url = "http://api-v2launch.trakt.tv/oauth/device/token"
            post = "code=%s&client_id=%s&client_secret=%s" % (item.device_code, client_id, client_secret)
            data = httptools.downloadpage(url, post, headers, replace_headers=True).data
            data = jsontools.load(data)
        else:
            import time
            dialog_auth = platformtools.dialog_progress(config.get_localized_string(60251),
                                                        config.get_localized_string(60252) % item.verify_url,
                                                        config.get_localized_string(60253)
                                                        % item.user_code,
                                                        config.get_localized_string(60254))

            # Generalmente cada 5 segundos se intenta comprobar si el usuario ha introducido el código
            while True:
                time.sleep(item.intervalo)
                try:
                    if dialog_auth.iscanceled():
                        config.set_setting("trakt_sync", False)
                        return

                    url = "http://api-v2launch.trakt.tv/oauth/device/token"
                    post = {'code': item.device_code, 'client_id': client_id, 'client_secret': client_secret}
                    post = jsontools.dump(post)
                    data = httptools.downloadpage(url, post, headers, replace_headers=True).data
                    data = jsontools.load(data)
                    if "access_token" in data:
                        # Código introducido, salimos del bucle
                        break
                except:
                    pass

            try:
                dialog_auth.close()
            except:
                pass

        token = data["access_token"]
        refresh = data["refresh_token"]

        config.set_setting("token_trakt", token, "trakt")
        config.set_setting("refresh_token_trakt", refresh, "trakt")
        if not item.folder:
            platformtools.dialog_notification(config.get_localized_string(60255), config.get_localized_string(60256))
            if config.is_xbmc():
                import xbmc
                xbmc.executebuiltin("Container.Refresh")
            return

    except:
        import traceback
        logger.error(traceback.format_exc())
        if not item.folder:
            return platformtools.dialog_notification(config.get_localized_string(60527), config.get_localized_string(60258))
        token = ""

    itemlist = []
    if token:
        itemlist.append(item.clone(config.get_localized_string(60256), action=""))
    else:
        itemlist.append(item.clone(config.get_localized_string(60260), action=""))

    return itemlist


def set_trakt_info(item):
    logger.info()
    import xbmcgui
    # Envia los datos a trakt
    try:
        info = item.infoLabels
        ids = jsontools.dump({'tmdb': info['tmdb_id'] , 'imdb': info['imdb_id'], 'slug': info['title']})
        xbmcgui.Window(10000).setProperty('script.trakt.ids', ids)
    except:
        pass

def get_trakt_watched(id_type, mediatype, update=False):
    logger.info()

    id_list = []
    id_dict = dict()

    token_auth = config.get_setting("token_trakt", "trakt")

    if token_auth:
        sync_path = os.path.join(config.get_data_path(), 'settings_channels', 'trakt')

        if os.path.exists(sync_path) and not update:
            trakt_node = jsontools.get_node_from_file('trakt', "TRAKT")
            if mediatype == 'shows':
                return trakt_node['shows']
            if mediatype == 'movies':
                return trakt_node['movies']

        else:
            token_auth = config.get_setting("token_trakt", "trakt")
            if token_auth:
                try:
                    token_auth = config.get_setting("token_trakt", "trakt")
                    headers = [['Content-Type', 'application/json'], ['trakt-api-key', client_id],
                               ['trakt-api-version', '2']]
                    if token_auth:
                        headers.append(['Authorization', "Bearer %s" % token_auth])
                        url = "https://api.trakt.tv/sync/watched/%s" % mediatype
                        data = httptools.downloadpage(url, headers=headers, replace_headers=True).data
                        watched_dict = jsontools.load(data)

                        if mediatype == 'shows':

                            dict_show = dict()
                            for item in watched_dict:
                                temp = []
                                id_ = str(item['show']['ids']['tmdb'])
                                season_dict = dict()
                                for season in item['seasons']:
                                    ep = []
                                    number = str(season['number'])
                                    # season_dict = dict()
                                    for episode in season['episodes']:
                                        ep.append(str(episode['number']))
                                    season_dict[number] = ep
                                    temp.append(season_dict)
                                dict_show[id_] = season_dict
                                id_dict = dict_show
                            return id_dict

                        elif mediatype == 'movies':
                            for item in watched_dict:
                                id_list.append(str(item['movie']['ids'][id_type]))
                except:
                    pass

    return id_list


def trakt_check(itemlist):
    id_result = ''
    # check = u'\u221a'
    check = 'v'
    synced = False
    try:
        for item in itemlist:
            info = item.infoLabels

            if info != '' and info['mediatype'] in ['movie', 'episode'] and item.channel != 'videolibrary':

                if not synced:
                    get_sync_from_file()
                    synced = True
                
                mediatype = 'movies'
                id_type = 'tmdb'

                if info['mediatype'] == 'episode':
                    mediatype = 'shows'

                if id_result == '':
                    id_result = get_trakt_watched(id_type, mediatype)
                if info['mediatype'] == 'movie':
                    if info[id_type + '_id'] in id_result:
                        item.title = '[COLOR limegreen][%s][/COLOR] %s' % (check, item.title)

                elif info['mediatype'] == 'episode':
                    if info[id_type + '_id'] in id_result:
                        id = info[id_type + '_id']
                        if info['season'] != '' and info['episode'] != '':
                            season = str(info['season'])

                            if season in id_result[id]:
                                episode = str(info['episode'])

                                if episode in id_result[id][season]:
                                    season_watched = id_result[id][season]

                                    if episode in season_watched:
                                        item.title = '[B][COLOR limegreen][[I]%s[/I]][/COLOR][/B] %s' % (check,
                                                                                                         item.title)
            else:
                break
    except:
        pass

    return itemlist


def get_sync_from_file():
    logger.info()
    sync_path = os.path.join(config.get_data_path(), 'settings_channels', 'trakt')
    trakt_node = {}
    if os.path.exists(sync_path):
        trakt_node = jsontools.get_node_from_file('trakt', "TRAKT")

    trakt_node['movies'] = get_trakt_watched('tmdb', 'movies')
    trakt_node['shows'] = get_trakt_watched('tmdb', 'shows')
    jsontools.update_node(trakt_node, 'trakt', 'TRAKT')


def update_trakt_data(mediatype, trakt_data):
    logger.info()

    sync_path = os.path.join(config.get_data_path(), 'settings_channels', 'trakt')
    if os.path.exists(sync_path):
        trakt_node = jsontools.get_node_from_file('trakt', "TRAKT")
        trakt_node[mediatype] = trakt_data
        jsontools.update_node(trakt_node, 'trakt', 'TRAKT')


def ask_install_script():
    logger.info()

    from platformcode import platformtools

    respuesta = platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(70521))
    if respuesta:
        xbmc.executebuiltin("InstallAddon(script.trakt)")
        return
    else:
        config.set_setting('install_trakt', False)
        return


def wait_for_update_trakt():
    logger.info()
    t = Thread(update_all)
    t.setDaemon(True)
    t.start()
    t.isAlive()

def update_all():
    from time import sleep
    logger.info()
    sleep(20)
    while xbmc.Player().isPlaying():
        sleep(20)
    for mediatype in ['movies', 'shows']:
        trakt_data = get_trakt_watched('tmdb', mediatype, True)
        update_trakt_data(mediatype, trakt_data)

