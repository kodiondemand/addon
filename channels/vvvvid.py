# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vvvvid
# ----------------------------------------------------------
import requests, sys, inspect
from core import support, tmdb
from platformcode import autorenumber, logger, config

host = support.config.get_channel_url()

# Creating persistent session
current_session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36'}

# Getting conn_id token from vvvvid and creating payload
login_page = host + '/user/login'
try:
    res = current_session.get(login_page, headers=headers)
    conn_id = res.json()['data']['conn_id']
    payload = {'conn_id': conn_id}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14', 'Cookie': res.headers['set-cookie']}
except:
    conn_id = ''


main_host = host
host += '/vvvvid/ondemand/'


@support.menu
def mainlist(item):
    if conn_id:
        anime = ['anime/',
                ('Popolari',['anime/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['anime/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['anime/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['anime/', 'peliculas', 'channel/10003/last/?filter='])
                ]
        film =  ['film/',
                ('Popolari',['film/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['film/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['film/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['film/', 'peliculas', 'channel/10003/last/?filter=']),
                ]
        tvshow = ['series/',
                ('Popolari',['series/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['series/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['series/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['series/', 'peliculas', 'channel/10003/last/?filter='])
                ]
        show = [('Show {bold} {tv}',['show/', 'peliculas', '', 'tvshow']),
                ('Popolari {submenu} {tv}',['show/', 'peliculas', 'channel/10002/last/', 'tvshow']),
                ('Nuove Uscite {submenu} {tv}',['show/', 'peliculas', 'channel/10007/last/', 'tvshow']),
                ('Generi {submenu} {tv}',['show/', 'peliculas', 'channel/10004/last/?category=', 'tvshow']),
                ('A-Z {submenu} {tv}',['show/', 'peliculas', 'channel/10003/last/?filter=', 'tvshow']),
                ('Cerca Show... {bold submenu} {tv}', ['show/', 'search', '', 'tvshow'])
                ]
        kids = [('Kids {bold}',['kids/', 'peliculas', '', 'tvshow']),
                ('Popolari {submenu} {kids}',['kids/', 'peliculas', 'channel/10002/last/', 'tvshow']),
                ('Nuove Uscite {submenu} {kids}',['kids/', 'peliculas', 'channel/10007/last/', 'tvshow']),
                ('Generi {submenu} {kids}',['kids/', 'peliculas', 'channel/10004/last/?category=', 'tvshow']),
                ('A-Z {submenu} {kids}',['kids/', 'peliculas', 'channel/10003/last/?filter=', 'tvshow']),
                ('Cerca Kids... {bold submenu} {kids}', ['kids/', 'search', '', 'tvshow'])
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
    if categoria == 'peliculas':
        item.contentType = 'movie'
        item.url = host + 'film/'
    if categoria == 'series':
        item.contentType = 'tvshow'
        item.url = host + 'series/'
    if categoria == 'anime':
        item.contentType = 'tvshow'
        item.url = host + 'anime/'
    return peliculas(item)


def peliculas(item):
    itemlist = []
    if not item.args:
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
        make_itemlist(itemlist, item, json_file)
    if 'category' in item.args:
        support.thumb(itemlist,genre=True)
    elif not 'filter' in item.args:
        if item.contentType != 'movie': autorenumber.start(itemlist)
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    itemlist = []
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    for i, block in enumerate(json_file['data']):
        if len(json_file['data']) > 1:
            prepend = str(i + 1) + 'x'
        else:
            prepend = 'Episodio '
        show_id = str(block['show_id'])
        season_id = str(block['season_id'])
        episodes = []
        support.info('SEASON ID= ',season_id)
        for episode in json_file['data']:
            episodes.append(episode['episodes'])
        for episode in episodes:
            for key in episode:
                if 'stagione' in encode(key['title']).lower():
                    season = support.match(encode(key['title']), patron=r'[Ss]tagione\s*(\d+)').match
                    episode = support.match(encode(key['title']), patron=r'[Ee]pisodio\s*(\d+)').match
                    if season and episode:
                        title = season + 'x' + episode + ' - ' + item.fulltitle
                    make_item = True
                elif int(key['season_id']) == int(season_id):
                    try:
                        title = prepend + key['number'] + ' - ' + key['title'].encode('utf8')
                    except:
                        title = prepend + key['number'] + ' - ' + key['title']
                    make_item = True
                else:
                    make_item = False
                if make_item == True:
                    if type(title) == tuple: title = title[0]
                    itemlist.append(
                        item.clone(title = title,
                                url=  host + show_id + '/season/' + str(key['season_id']),
                                action= 'findvideos',
                                video_id= key['video_id']))
    if inspect.stack()[1][3] not in ['find_episodes']:
        autorenumber.start(itemlist, item)
    if autorenumber.check(item) == True \
        or support.match(itemlist[0].title, patron=r"(\d+x\d+)").match:
        support.videolibrary(itemlist,item)
    return itemlist

def findvideos(item):
    from lib import vvvvid_decoder
    itemlist = []
    if item.contentType == 'movie':
        json_file = current_session.get(item.url, headers=headers, params=payload).json()
        item.url = host + str(json_file['data'][0]['show_id']) + '/season/' + str(json_file['data'][0]['episodes'][0]['season_id']) + '/'
        item.video_id = json_file['data'][0]['episodes'][0]['video_id']
    logger.info('url=',item.url)
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    for episode in json_file['data']:
        logger.info(episode)
        if episode['video_id'] == item.video_id:
            url = vvvvid_decoder.dec_ei(episode['embed_info'] or episode['embed_info_sd'])
            if 'youtube' in url: item.url = url
            item.url = url.replace('manifest.f4m','master.m3u8').replace('http://','https://').replace('/z/','/i/')
            if 'https' not in item.url:
                url = support.match('https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/playlist.m3u').data
                url = url.split()[-1]
                itemlist.append(
                    item.clone(action= 'play',
                               title=config.get_localized_string(30137),
                               url= 'https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/' + url,
                               server= 'directo')
                )
            else:
                key_url = 'https://www.vvvvid.it/kenc?action=kt&conn_id=' + conn_id + '&url=' + item.url.replace(':','%3A').replace('/','%2F')
                key = vvvvid_decoder.dec_ei(current_session.get(key_url, headers=headers, params=payload).json()['message'])

                itemlist.append(
                    item.clone(action= 'play',
                               title=config.get_localized_string(30137),
                               url= item.url + '?' + key,
                               server= 'directo')
                )

    return support.server(item, itemlist=itemlist, Download=False)

def make_itemlist(itemlist, item, data):
    search = item.search if item.search else ''
    infoLabels = {}
    for key in data['data']:
        if search.lower() in encode(key['title']).lower():
            infoLabels['year'] = key['date_published']
            infoLabels['title'] = infoLabels['tvshowtitle'] = key['title']
            title = encode(key['title'])
            itemlist.append(
                item.clone(title = support.typo(title, 'bold'),
                           fulltitle= title,
                           show= title,
                           url= host + str(key['show_id']) + '/seasons/',
                           action= 'findvideos' if item.contentType == 'movie' else 'episodios',
                           contentType = item.contentType,
                           contentSerieName= key['title'] if item.contentType != 'movie' else '',
                           contentTitle= title if item.contentType == 'movie' else '',
                           infoLabels=infoLabels))
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