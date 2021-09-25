# -*- coding: utf-8 -*-
# -*- Tools for trakt sync -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*

import os, xbmc
from core import httptools, jsontools
from core.item import Item
from platformcode import config, logger
from threading import Thread
import sys
if sys.version_info[0] >= 3: from concurrent import futures
else: from concurrent_py2 import futures

host = 'https://api.trakt.tv'
client_id = '502bd1660b833c1ae69828163c0848e84e9850061e5529f30930e7356cae73b1'
client_secret = '1d30d5b24acf223a5e1ab6c61d08b69992d98ed5b0c7e26b052b5e6a592035a4'
token_auth = config.get_setting("token_trakt", "trakt")


def auth_trakt():
    item = Item()
    folder = (config.get_platform() == 'plex')
    item.folder = folder
    # Autentificación de cuenta Trakt
    headers = {'Content-Type': 'application/json', 'trakt-api-key': client_id, 'trakt-api-version': '2'}
    try:
        post = {'client_id': client_id}
        post = jsontools.dump(post)
        # Se solicita url y código de verificación para conceder permiso a la app
        url = host + '/oauth/device/code'
        data = httptools.downloadpage(url, post=post, headers=headers).json
        item.verify_url = data['verification_url']
        item.user_code = data['user_code']
        item.device_code = data['device_code']
        item.intervalo = data['interval']
        if not item.folder:
            token_trakt(item)

        else:
            itemlist = []
            title = config.get_localized_string(60248) % item.verify_url
            itemlist.append(item.clone(title=title, action=''))
            title = config.get_localized_string(60249) % item.user_code
            itemlist.append(item.clone(title=title, action=''))
            title = config.get_localized_string(60250)
            itemlist.append(item.clone(title=title, action='token_trakt'))
            return itemlist
    except:
        import traceback
        logger.error(traceback.format_exc())


def token_trakt(item):
    from platformcode import platformtools

    headers = {'Content-Type': 'application/json', 'trakt-api-key': client_id, 'trakt-api-version': '2'}
    try:
        if item.extra == 'renew':
            refresh = config.get_setting('refresh_token_trakt', 'trakt')
            url = host + '/oauth/device/token'
            post = {'refresh_token': refresh, 'client_id': client_id, 'client_secret': client_secret,
                    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 'grant_type': 'refresh_token'}
            post = jsontools.dump(post)
            data = httptools.downloadpage(url, post=post, headers=headers).data
            data = jsontools.load(data)
        elif item.action == 'token_trakt':
            url = host + '/oauth/device/token'
            post = 'code={}&client_id={}&client_secret={}'.format(item.device_code, client_id, client_secret)
            data = httptools.downloadpage(url, post=post, headers=headers).data
            data = jsontools.load(data)
        else:
            import time
            dialog_auth = platformtools.dialog_progress(config.get_localized_string(60251),
                                                        config.get_localized_string(60252) % item.verify_url + '\n' +
                                                        config.get_localized_string(60253) % item.user_code + '\n' +
                                                        config.get_localized_string(60254))

            # Generalmente cada 5 segundos se intenta comprobar si el usuario ha introducido el código
            while True:
                time.sleep(item.intervalo)
                try:
                    if dialog_auth.iscanceled():
                        config.set_setting('trakt_sync', False)
                        return

                    url = host + '/oauth/device/token'
                    post = {'code': item.device_code, 'client_id': client_id, 'client_secret': client_secret}
                    post = jsontools.dump(post)
                    data = httptools.downloadpage(url, post=post, headers=headers).data
                    data = jsontools.load(data)
                    if 'access_token' in data:
                        # Código introducido, salimos del bucle
                        break
                except:
                    pass

            try:
                dialog_auth.close()
            except:
                pass

        token = data['access_token']
        refresh = data['refresh_token']

        config.set_setting('token_trakt', token, 'trakt')
        config.set_setting('refresh_token_trakt', refresh, 'trakt')
        if not item.folder:
            platformtools.dialog_notification(config.get_localized_string(60255), config.get_localized_string(60256))
            if config.is_xbmc():
                import xbmc
                xbmc.executebuiltin('Container.Refresh')
            return

    except:
        import traceback
        logger.error(traceback.format_exc())
        if not item.folder:
            return platformtools.dialog_notification(config.get_localized_string(60527), config.get_localized_string(60258))
        token = ''

    itemlist = []
    if token:
        itemlist.append(item.clone(title=config.get_localized_string(60256), action=''))
    else:
        itemlist.append(item.clone(title=config.get_localized_string(60260), action=''))

    return itemlist


def set_trakt_info(item):
    logger.debug()
    import xbmcgui
    # Envia los datos a trakt
    try:
        info = item.infoLabels
        ids = jsontools.dump({'tmdb': info['tmdb_id'] , 'imdb': info['imdb_id'], 'slug': info['title']})
        xbmcgui.Window(10000).setProperty('script.trakt.ids', ids)
    except:
        pass


def get_trakt_watched(id_type, mediatype, update=False):
    logger.debug()

    id_list = []
    id_dict = dict()

    token_auth = config.get_setting('token_trakt', 'trakt')

    if token_auth:
        sync_path = os.path.join(config.get_data_path(), 'settings_channels', 'trakt')

        if os.path.exists(sync_path) and not update:
            trakt_node = jsontools.get_node_from_file('trakt', 'TRAKT')
            if mediatype == 'shows':
                return trakt_node['shows']
            if mediatype == 'movies':
                return trakt_node['movies']

        else:
            token_auth = config.get_setting('token_trakt', 'trakt')
            if token_auth:
                try:
                    token_auth = config.get_setting('token_trakt', 'trakt')
                    headers = [['Content-Type', 'application/json'], ['trakt-api-key', client_id],
                               ['trakt-api-version', '2']]
                    if token_auth:
                        headers.append(['Authorization', 'Bearer ' + token_auth])
                        url = host + '/sync/watched/' + mediatype
                        data = httptools.downloadpage(url, headers=headers).data
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
    if type(itemlist) != list:
        return
    def sync(item, id_result):
        info = item.infoLabels
        try:
            if info['mediatype'] == 'movie' and info['tmdb_id'] in id_result[info['mediatype']]:
                item.infoLabels['playcount'] = 1
            elif info['mediatype'] == 'episode' and info['tmdb_id'] in id_result[info['mediatype']]:
                id = info['tmdb_id']
                if info['season'] and info['episode'] and \
                    str(info['season']) in id_result[info['mediatype']][id] and \
                    str(info['episode']) in id_result[info['mediatype']][id][str(info['season'])]:
                    item.infoLabels['playcount'] = 1
        except:
            pass

    if itemlist and itemlist[0].channel != 'videolibrary' \
        and 'mediatype' in itemlist[0].infoLabels \
        and itemlist[0].infoLabels['mediatype'] in ['movie', 'episode']:

        id_result = {}
        id_result['movie'] = get_trakt_watched('tmdb', 'movies', True)
        id_result['episode'] = get_trakt_watched('tmdb', 'shows', True)

        with futures.ThreadPoolExecutor() as executor:
            [executor.submit(sync, it, id_result) for it in itemlist]

    return itemlist


def get_sync_from_file():
    logger.debug()
    sync_path = os.path.join(config.get_data_path(), 'settings_channels', 'trakt_data.json')
    trakt_node = {}
    if os.path.exists(sync_path):
        trakt_node = jsontools.get_node_from_file('trakt', 'TRAKT')

    trakt_node['movies'] = get_trakt_watched('tmdb', 'movies')
    trakt_node['shows'] = get_trakt_watched('tmdb', 'shows')
    jsontools.update_node(trakt_node, 'trakt', 'TRAKT')


def update_trakt_data(mediatype, trakt_data):
    logger.debug()

    sync_path = os.path.join(config.get_data_path(), 'settings_channels', 'trakt_data.json')
    if os.path.exists(sync_path):
        trakt_node = jsontools.get_node_from_file('trakt', 'TRAKT')
        trakt_node[mediatype] = trakt_data
        jsontools.update_node(trakt_node, 'trakt', 'TRAKT')


def ask_install_script():
    logger.debug()

    from platformcode import platformtools

    respuesta = platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(70521))
    if respuesta:
        xbmc.executebuiltin('InstallAddon(script.trakt)')
        return
    else:
        config.set_setting('install_trakt', False)
        return


def wait_for_update_trakt():
    logger.debug()
    t = Thread(target=update_all)
    t.setDaemon(True)
    t.start()
    t.is_alive()


def update_all():
    # from core.support import dbg;dbg()
    from time import sleep
    logger.debug()
    sleep(20)
    while xbmc.Player().isPlaying():
        sleep(20)
    for mediatype in ['movies', 'shows']:
        trakt_data = get_trakt_watched('tmdb', mediatype, True)
        update_trakt_data(mediatype, trakt_data)


def context(item):
    Type = item.contentType.replace("tv", "") + "s"
    item.action = 'traktResults'
    title = config.get_localized_string(30122 if item.contentType == 'movie' else 30123)
    context = []
    commands = []
    condition = "'tmdb': " + item.infoLabels["tmdb_id"] 
    try:
        result = execute(item.clone(url="/sync/watched/" + Type))
        post = {Type: [{"ids": {"tmdb": item.infoLabels["tmdb_id"]}}]}
        if condition in str(result):
            context.append(config.get_localized_string(60016 if item.contentType == 'movie' else 60020))
            commands.append(item.clone(url="/sync/history/remove", post=post))
        else:
            context.append(config.get_localized_string(60017 if item.contentType == 'movie' else 60021))
            commands.append(item.clone(url="/sync/history", post=post))
    except:
        pass

    try:
        from core.support import dbg;dbg()
        result = execute(item.clone(url="/sync/watchlist/" + Type))
        post = {Type: [{"ids": {"tmdb": item.infoLabels["tmdb_id"]}}]}
        if condition in str(result):
            context.append(config.get_localized_string(70343) % title)
            commands.append(item.clone(url="/sync/watchlist/remove", post=post))
        else:
            context.append(config.get_localized_string(70344) % title)
            commands.append(item.clone(url="/sync/watchlist", post=post))
    except:
        pass

    try:
        result = execute(item.clone(url="/sync/collection/" + Type))
        post = {Type: [{"ids": {"tmdb": item.infoLabels["tmdb_id"]}}]}
        if condition in str(result):
            context.append(config.get_localized_string(70345) % title)
            commands.append(item.clone(url="/sync/collection/remove", post=post))
        else:
            context.append(config.get_localized_string(70346) % title)
            commands.append(item.clone(url="/sync/collection", post=post))
    except:
        pass

    if context:
        import xbmcgui
        index = xbmcgui.Dialog().contextmenu(context)
        if index > -1:
            execute(commands[index])

def execute(item):
    from platformcode.platformtools import dialog_notification
    url = host + item.url

    headers = [['Content-Type', 'application/json'], ['trakt-api-key', client_id], ['trakt-api-version', '2']]
    if token_auth: headers.append(['Authorization', 'Bearer {}'.format(token_auth)])

    post = None
    if item.post: post = jsontools.dump(item.post)

    data = httptools.downloadpage(url, post=post, headers=headers).json

    if not post:
        return data
    else:
        if 'not_found' in data: return dialog_notification('Trakt', config.get_localized_string(70347))
        else: return dialog_notification('Trakt', config.get_localized_string(70348))