# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Rai Play
# ------------------------------------------------------------

import requests
from core import support, jsontools
from platformcode import logger, config
typo = support.typo
session = requests.Session()
host = support.config.get_channel_url()

def getToken():
    token = config.get_setting('token', 'discoveryplus', None)
    if not token:
        token = session.get('https://disco-api.discoveryplus.it/token?realm=dplayit').json()['data']['attributes']['token']
        config.set_setting('token', token, 'discoveryplus')
    return token

token = getToken()

api = "https://disco-api.discoveryplus.it"
headers = {'User-Agent': 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
           'Referer': host,
           'Cookie' : 'st=' + token}

def Dict(item):
    global pdict
    pdict = session.get(api + '/cms/routes/{}?decorators=viewingHistory&include=default'.format(item.args), headers=headers).json()['included']


@support.menu
def mainlist(item):
    top =  [('Dirette {bold}', ['', 'live']),
            ('Programmi {bullet bold tv}', ['', 'peliculas'])]

    search = ''

    return locals()


def liveDict():
    livedict = {}
    for key in session.get(api + '/cms/routes/home?decorators=viewingHistory&include=default', headers=headers).json()['included']:
        if key['type'] == 'channel' and key.get('attributes',{}).get('hasLiveStream', '') and 'Free' in key.get('attributes',{}).get('packages', []):
            title = key['attributes']['name']
            livedict[title] = {}
            livedict[title]['plot'] = key['attributes']['description']
            livedict[title]['url'] = '{}/canali/{}'.format(host, key['attributes']['alternateId'])
            livedict[title]['id'] = key['id']
    return livedict


def search(item, text):
    itemlist = []
    support.info(text)
    item.search = text

    try:
        itemlist = peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)

    return itemlist


def live(item):
    logger.debug()
    itemlist =[]
    for name, values in liveDict().items():
        logger.debug(name)
        itemlist.append(item.clone(title=typo(name), fulltitle=name, plot=values['plot'], url=values['url'], id=values['id'], action='play', forcethumb=True, no_return=True))
    itemlist.sort(key=lambda item: int(item.id))
    return support.thumb(itemlist, live=True)


def peliculas(item):
    logger.debug()
    itemlist =[]
    pdict = session.get(api + '/cms/routes/free?decorators=viewingHistory&include=default', headers=headers).json()['included']
    images = list(filter(lambda x: x['type'] == 'image', pdict))

    for key in pdict:
        if key['type'] == 'show' and 'Free' in str(key.get('relationships',{}).get('contentPackages',{}).get('data',[])):
            logger.debug(key['attributes']['name'], key['type'], '\n', jsontools.dump(key))
            title = key['attributes']['name']
            if item.search.lower() in title.lower():
                plot = key['attributes']['description']
                url = '{}/programmi/{}'.format(host, key['attributes']['alternateId'])
                seasons = key['attributes']['seasonNumbers']
                thumbs = [image['attributes']['src'] for image in images if image['id'] == key['relationships']['images']['data'][0]['id']]
                thumb = thumbs[0] if thumbs else item.thumbnail
                fanarts = [image['attributes']['src'] for image in images if len(key['relationships']['images']['data']) > 1 and image['id'] == key['relationships']['images']['data'][1]['id']]
                fanart = fanarts[0] if fanarts else item.fanart
                itemlist.append(
                    item.clone(title=typo(title,'bold'),
                               fulltitle=title,
                               plot=plot,
                               url=url,
                               programid=key['attributes']['alternateId'],
                               id=key['id'],
                               seasons=seasons,
                               action='episodios',
                               thumbnail=thumb,
                               fanart=fanart,
                               contentType='tvshow'))

    return itemlist


def episodios(item):
    logger.debug()
    itemlist =[]
    pdict = session.get(api + '/cms/routes/programmi/{}?decorators=viewingHistory&include=default'.format(item.programid), headers=headers).json()['included']

    for key in pdict:
        if key['type'] == 'collection' and key.get('attributes',{}).get('component',{}).get('id', '') == 'tabbed-content':
            mandatory = key['attributes']['component']['mandatoryParams']
            for option in key['attributes']['component']['filters'][0]['options']:
                url = '{}/cms/collections/{}?decorators=viewingHistory&include=default&{}&{}'.format(api, key['id'], mandatory, option['parameter'])
                season = session.get(url, headers=headers).json()
                if season.get('included', {}):
                    for episode  in season['included']:
                        if episode['type'] == 'video':
                            title = '{}x{:02d} - {}'.format(option['id'], episode['attributes']['episodeNumber'], episode['attributes']['name'])
                            plot = episode['attributes']['description']
                            itemlist.append(
                                item.clone(title=typo(title,'bold'),
                                           fulltitle=title,
                                           plot=plot,
                                           id=episode['id'],
                                           action='play',
                                           contentType='episode',
                                           season=option['id'],
                                           episode=episode['attributes']['episodeNumber'],
                                           forcethumb=True,
                                           no_return=True))

    if itemlist: itemlist.sort(key=lambda it: (int(it.season), int(it.episode)))
    return itemlist

def play(item):
    if item.filter:
        item.id = liveDict()[item.filter]['id']
        item.fulltitle = item.filter
        item.forcethumb = True
        item.no_return = True
        support.thumb(item, live=True)
    if item.contentType == 'episode': data = session.get('{}/playback/v2/videoPlaybackInfo/{}?usePreAuth=true'.format(api, item.id), headers=headers).json().get('data',{}).get('attributes',{})
    else: data = session.get('{}/playback/v2/channelPlaybackInfo/{}?usePreAuth=true'.format(api, item.id), headers=headers).json().get('data',{}).get('attributes',{})
    if data['protection'].get('drm_enabled',True):
        url = data['streaming']['dash']['url']
        item.drm = 'com.widevine.alpha'
        item.license = data['protection']['schemes']['widevine']['licenseUrl'] + '|PreAuthorization=' + data['protection']['drmToken'] + '|R{SSM}|'
    else:
        url = data['streaming']['hls']['url']
    logger.debug(item.license)
    return support.servertools.find_video_items(item, data=url)