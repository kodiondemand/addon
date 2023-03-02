# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vvvvid
# ----------------------------------------------------------
import re

import requests, sys, inspect
from core import support, tmdb, httptools
from platformcode import autorenumber, logger, config
import random, string
try:
    import urlparse
except:
    import urllib.parse as urlparse

host = 'https://www.vvvvid.it'

# Creating persistent session
current_session = requests.Session()
# current_session.request = functools.partial(current_session.request, timeout=httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT)
headers = {'User-Agent': httptools.random_useragent()}

# Getting conn_id token from vvvvid and creating payload
login_page = host + '/user/login'
try:
    res = current_session.get(login_page, headers=headers)
    conn_id = res.json()['data']['conn_id']
    payload = {'conn_id': conn_id}
    headers['Cookie'] = res.headers['set-cookie']
except:
    conn_id = ''


main_host = host + '/vvvvid/ondemand/'
pagination = 20


@support.menu
def mainlist(item):
    if conn_id:
        anime = ['/vvvvid/ondemand/anime/',
                ('Popolari',['/vvvvid/ondemand/anime/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['/vvvvid/ondemand/anime/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['/vvvvid/ondemand/anime/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['/vvvvid/ondemand/anime/', 'peliculas', 'channel/10003/last/?filter='])
                ]
        film =  ['/vvvvid/ondemand/film/',
                ('Popolari',['/vvvvid/ondemand/film/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['/vvvvid/ondemand/film/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['/vvvvid/ondemand/film/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['/vvvvid/ondemand/film/', 'peliculas', 'channel/10003/last/?filter=']),
                ]
        tvshow = ['/vvvvid/ondemand/series/',
                ('Popolari',['/vvvvid/ondemand/series/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['/vvvvid/ondemand/series/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['/vvvvid/ondemand/series/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['/vvvvid/ondemand/series/', 'peliculas', 'channel/10003/last/?filter='])
                ]
        show = [('Show {bold} {tv}',['/vvvvid/ondemand/show/', 'peliculas', '', 'tvshow']),
                ('Popolari {submenu} {tv}',['/vvvvid/ondemand/show/', 'peliculas', 'channel/10002/last/', 'tvshow']),
                ('Nuove Uscite {submenu} {tv}',['/vvvvid/ondemand/show/', 'peliculas', 'channel/10007/last/', 'tvshow']),
                ('Generi {submenu} {tv}',['/vvvvid/ondemand/show/', 'peliculas', 'channel/10004/last/?category=', 'tvshow']),
                ('A-Z {submenu} {tv}',['/vvvvid/ondemand/show/', 'peliculas', 'channel/10003/last/?filter=', 'tvshow']),
                ('Cerca Show... {bold submenu} {tv}', ['/vvvvid/ondemand/show/', 'search', '', 'tvshow'])
                ]
        kids = [('Kids {bold}',['/vvvvid/ondemand/kids/', 'peliculas', '', 'tvshow']),
                ('Popolari {submenu} {kids}',['/vvvvid/ondemand/kids/', 'peliculas', 'channel/10002/last/', 'tvshow']),
                ('Nuove Uscite {submenu} {kids}',['/vvvvid/ondemand/kids/', 'peliculas', 'channel/10007/last/', 'tvshow']),
                ('Generi {submenu} {kids}',['/vvvvid/ondemand/kids/', 'peliculas', 'channel/10004/last/?category=', 'tvshow']),
                ('A-Z {submenu} {kids}',['/vvvvid/ondemand/kids/', 'peliculas', 'channel/10003/last/?filter=', 'tvshow']),
                ('Cerca Kids... {bold submenu} {kids}', ['/vvvvid/ondemand/kids/', 'search', '', 'tvshow'])
                ]
    else:
        Top = [("Visibile solo dall'Italia {bold}",[])]
    return locals()


def search(item, text):
    support.info(text)
    itemlist = []
    if conn_id:
        if 'film' in item.url: item.contentType = 'movie'
        else: item.contentType = 'tvshow'
        item.search = text
        try:
            itemlist = peliculas(item)
        except:
            import sys
            for line in sys.exc_info():
                support.logger.error("%s" % line)
            return []
    return itemlist


def newest(categoria):
    item = support.Item()
    item.args = 'channel/10007/last/'
    item.newest = True
    if categoria == 'peliculas':
        item.contentType = 'movie'
        item.url = main_host + 'film/'
    if categoria == 'series':
        item.contentType = 'tvshow'
        item.url = main_host + 'series/'
    if categoria == 'anime':
        item.contentType = 'tvshow'
        item.url = main_host + 'anime/'
    return peliculas(item)


def peliculas(item):
    if not item.page:item.page = 1
    itemlist = []
    if not item.args:
        if not itemlist:
            json_file =loadjs(item.url + 'channel/10005/last/')
            support.logger.debug(json_file)
            make_itemlist(itemlist, item, json_file)

    elif ('=' not in item.args) and ('=' not in item.url):
        json_file=loadjs(item.url + item.args)
        make_itemlist(itemlist, item, json_file)

    elif '=' in item.args:
        json_file = current_session.get(item.url + 'channels', headers=headers, params=payload).json()
        Filter = support.match(item.args, patron=r'\?([^=]+)=').match
        keys = [i[Filter] for i in json_file['data'] if Filter in i][0]
        for key in keys:
            if key not in ['1','2']:
                itemlist.append(
                    item.clone(title = support.typo(key.upper() if Filter == 'filter' else key['name'], 'bold'),
                               url =  item.url + item.args + (key if Filter == 'filter' else str(key['id'])),
                               action = 'peliculas',
                               args = 'filters'))

    else :
        json_file=loadjs(item.url)
        item.args=''
        make_itemlist(itemlist, item, json_file)

    itlist = []
    if not item.newest:
        for i, it in enumerate(itemlist):
            if pagination and (item.page - 1) * pagination > i: continue  # pagination
            if pagination and i >= item.page * pagination: break  # pagination

            itlist.append(it)

        if pagination and len(itemlist) >= pagination:
            if inspect.stack(0)[1][3] != 'get_newest':
                itlist.append(
                    item.clone(action='peliculas',
                        title=support.typo(config.get_localized_string(30992), 'color kod bold'),
                        fulltitle=item.fulltitle,
                        show=item.show,
                        url=item.url,
                        args=item.args,
                        page=item.page + 1,
                        thumbnail=support.thumb()))
            itemlist = itlist

    if 'category' in item.args:
        support.thumb(itemlist,genre=True)
    elif not 'filter' in item.args:
        if item.contentType != 'movie': autorenumber.start(itemlist)
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    itemlist = []
    if item.episodes:
        episodes = item.episodes
        show_id = item.show_id 
        season_id = item.season_id
    else:
        json_file = current_session.get(item.url, headers=headers, params=payload).json()['data']
        if len(json_file) > 1:
            for key in json_file:
                itemlist.append(item.clone(title=support.typo(key['name'],'bold'), show_id = str(key['show_id']), season_id = str(key['season_id']), episodes = key['episodes']))
            return itemlist
        else:
            episodes = json_file[0]['episodes']
            show_id = str(json_file[0]['show_id'])
            season_id = str(json_file[0]['season_id'])

    for episode in episodes:
        try:
            title = 'Episodio ' + episode['number'] + ' - ' + episode['title'].encode('utf8')
        except:
            title = 'Episodio ' + episode['number'] + ' - ' + episode['title']

        if type(title) == tuple: title = title[0]
        itemlist.append(
            item.clone(title = support.typo(title, 'bold'),
                    url=  main_host + show_id + '/season/' + str(season_id),
                    action= 'findvideos',
                    video_id= episode['video_id']))

    if inspect.stack(0)[1][3] not in ['find_episodes']:
        autorenumber.start(itemlist, item)

    support.videolibrary(itemlist,item)
    return itemlist

def findvideos(item):
    from lib import vvvvid_decoder
    itemlist = []
    if item.contentType == 'movie':
        json_file = current_session.get(item.url, headers=headers, params=payload).json()
        item.url = main_host + str(json_file['data'][0]['show_id']) + '/season/' + str(json_file['data'][0]['episodes'][0]['season_id']) + '/'
        item.video_id = json_file['data'][0]['episodes'][0]['video_id']
    logger.info('url=',item.url)
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    for episode in json_file['data']:
        logger.info(episode)
        if episode['video_id'] == item.video_id:
            url = vvvvid_decoder.dec_ei(episode['embed_info'] or episode['embed_info_sd'])
            # if 'youtube' in url: item.url = url
            item.url = url.replace('manifest.f4m','master.m3u8').replace('http://','https://').replace('/z/','/i/')
            if 'youtube' in url:
                itemlist.append(
                    item.clone(action= 'play',
                               title= 'YouTube',
                               url= item.url,
                               server= 'youtube')
                )
            elif 'https' not in item.url:
                url = support.match('https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/playlist.m3u').data
                url = url.split()[-1]
                itemlist.append(
                    item.clone(action= 'play',
                               title=config.get_localized_string(30137),
                               url= 'https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/' + url,
                               server= 'directo')
                )
            if episode['video_type'] == 'video/dash':
                drm = ''
                license = ''
                if episode.get('drm'):
                    drm = 'com.widevine.alpha'
                    license= 'https://www.vvvvid.it/drm/license/widevine?content_id={drm}&conn_id={conn}|Accept=*/*&Content-Type=&User-Agent={ua}|R{{SSM}}|'.format(drm=urlparse.quote(episode['drm']), conn=conn_id, ua=headers['User-Agent'])
                itemlist.append(
                    item.clone(action= 'play',
                               title=config.get_localized_string(30137),
                               url= item.url + '|User-Agent=' + headers['User-Agent'],
                               drm=drm,
                               license=license,
                               server= 'directo',
                               manifest='mpd')
                )
            else:
                key_url = 'https://www.vvvvid.it/kenc?action=kt&conn_id=' + conn_id + '&url=' + item.url.replace(':','%3A').replace('/','%2F')
                key = vvvvid_decoder.dec_ei(current_session.get(key_url, headers=headers, params=payload).json()['message'])

                itemlist.append(
                    item.clone(action= 'play',
                               title=config.get_localized_string(30137),
                               url= item.url + '?' + key,
                               server= 'directo',
                               manifest='hls')
                )

    return support.server(item, itemlist=itemlist, Download=False)

def make_itemlist(itemlist, item, data):
    search = item.search if item.search else ''
    infoLabels = {}
    for key in data['data']:
        if search.lower() in encode(key['title']).lower():
            title = encode(key['title'])
            fulltitle=re.split(' - |\(', title)[0].strip()
            ct = key.get('show_type_name', '').lower()

            if ct == 'serie': contentType = 'tvshow'
            elif ct == 'film': contentType = 'movie'
            else: contentType = item.contentType

            infoLabels['title'] = fulltitle
            infoLabels['tvshowtitle'] = fulltitle
            infoLabels['mediatype'] = contentType
            infoLabels['year'] = key['date_published']

            it = item.clone(title = support.typo(title, 'bold'),
                            fulltitle= title,
                            show= title,
                            url= main_host + str(key['show_id']) + '/seasons/',
                            action= 'findvideos' if contentType == 'movie' else 'episodios',
                            infoLabels=infoLabels,
                            thumbnail=support.thumb(contentType),
                            videolibrary=False)

            itemlist.append(it)

    return itemlist


def loadjs(url):
    if '?category' not in url:
        url += '?full=true'
    support.info('Json URL;',url)
    json = current_session.get(url, headers=headers, params=payload).json()
    return json


def encode(text):
    if sys.version_info[0] >= 3:
        return text
    else:
        return text.encode('utf8')