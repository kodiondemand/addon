# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per StreamingCommunity
# ------------------------------------------------------------

import json, requests, sys
from core import support, channeltools
from platformcode import logger
if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

def findhost(url):
    return 'https://' + support.match(url, patron='var domain\s*=\s*"([^"]+)').match

host = support.config.get_channel_url(findhost)
session = requests.Session()
headers = {}

def getHeaders():
    global headers
    if not headers:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'}
        response = session.get(host, headers=headers)
        csrf_token = support.match(response.text, patron='name="csrf-token" content="([^"]+)"').match
        headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14',
                    'content-type': 'application/json;charset=UTF-8',
                    'Referer': host,
                    'x-csrf-token': csrf_token,
                    'Cookie': '; '.join([x.name + '=' + x.value for x in response.cookies])}
getHeaders()

@support.menu
def mainlist(item):
    film=['',
          ('Generi',['/film','genres']),
          ('Titoli del Momento',['/film','movies',0]),
          ('Novità',['/film','movies',1]),
          ('Popolari',['/film','movies',2])]
    tvshow=['',
            ('Generi',['/serie-tv','genres']),
            ('Titoli del Momento',['/serie-tv','movies',0]),
            ('Novità',['/serie-tv','movies',1]),
            ('Popolari',['/serie-tv','movies',2])]
    search=''
    return locals()


def genres(item):
    # getHeaders()
    logger.debug()
    itemlist = []
    data = support.scrapertools.decodeHtmlentities(support.match(item).data)
    args = support.match(data, patronBlock=r'genre-options-json="([^\]]+)\]', patron=r'name"\s*:\s*"([^"]+)').matches
    for arg in args:
        itemlist.append(item.clone(title=support.typo(arg, 'bold'), args=arg, action='movies'))
    support.thumb(itemlist, genre=True)
    return itemlist


def search(item, text):
    logger.debug('search', text)
    item.search = text

    try:
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error(line)
        return []


def newest(category):
    logger.debug(category)
    itemlist = []
    item = support.Item()
    item.args = 1
    if category == 'movie':
        item.contentType= 'movie'
        item.url = host + '/film'
    else:
        item.contentType= 'tvshow'
        item.url = host + '/serie-tv'

    try:
        itemlist = movies(item)

        if itemlist[-1].action == 'movies':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error(line)
        return []

    return itemlist



def movies(item):
    # getHeaders()
    logger.debug()
    itemlist = []
    recordlist = []
    videoType = 'movie' if item.contentType == 'movie' else 'tv'

    page = item.page if item.page else 0
    offset = page * 60
    if item.records:
        records = item.records
    elif type(item.args) == int:
        data = support.scrapertools.decodeHtmlentities(support.match(item).data)
        records = json.loads(support.match(data, patron=r'slider-title titles-json="(.*?)" slider-name="').matches[item.args])
    elif not item.search:
        payload = json.dumps({'type': videoType, 'offset':offset, 'genre':item.args})
        records = session.post(host + '/api/browse', headers=headers, data=payload).json()['records']
    else:
        payload = json.dumps({'q': item.search})
        records = session.post(host + '/api/search', headers=headers, data=payload).json()['records']

    if records and type(records[0]) == list:
        js = []
        for record in records:
            js += record
    else:
        js = records

    for i, it in enumerate(js):
        if i < 20:
            itemlist.append(makeItem(i, it, item))
        else:
            recordlist.append(it)

    itemlist.sort(key=lambda item: item.n)
    if recordlist:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), thumbnail=support.thumb(), page=page, records=recordlist))
    elif len(itemlist) >= 20:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), thumbnail=support.thumb(), records=[], page=page + 1))
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def makeItem(n, it, item):
    info = session.post(host + '/api/titles/preview/{}'.format(it['id']), headers=headers).json()
    title, lang = support.match(info['name'], patron=r'([^\[|$]+)(?:\[([^\]]+)\])?').match
    if not lang:
        lang = 'ITA'
    itm = item.clone(title=title, contentType = info['type'].replace('tv', 'tvshow'), contentLanguage = lang, year = info['release_date'].split('-')[0])


    if itm.contentType == 'movie':
        # itm.contentType = 'movie'
        itm.fulltitle = itm.show = itm.contentTitle = title
        itm.contentTitle = ''
        itm.action = 'findvideos'
        itm.url = host + '/watch/%s' % it['id']

    else:
        # itm.contentType = 'tvshow'
        itm.contentTitle = ''
        itm.fulltitle = itm.show = itm.contentSerieName = title
        itm.action = 'episodes'
        itm.season_count = info['seasons_count']
        itm.url = host + '/titles/%s-%s' % (it['id'], it['slug'])
    itm.n = n
    return itm

def episodes(item):
    # getHeaders()
    logger.debug()
    itemlist = []

    js = json.loads(support.match(item.url, patron=r'seasons="([^"]+)').match.replace('&quot;','"'))

    for episodes in js:
        for it in episodes['episodes']:
            itemlist.append(
                item.clone(
                             contentEpisodeNumber = it['number'],
                             contentSeason=episodes['number'],
                             thumbnail=it['images'][0]['original_url'] if 'images' in it and 'original_url' in it['images'][0] else item.thumbnail,
                             fanart=item.fanart,
                             plot=it['plot'],
                             action='findvideos',
                             contentType='episode',
                             contentTitle=support.cleantitle(it['name']),
                             url=host + '/watch/' + str(episodes['title_id']),
                             episodeid= '?e=' + str(it['id'])))

    support.videolibrary(itemlist, item)
    support.download(itemlist, item)
    return itemlist


def findvideos(item):
    video_urls = []
    data = support.match(item.url + item.episodeid, headers=headers).data.replace('&quot;','"').replace('\\','')
    url = support.match(data, patron=r'video_url"\s*:\s*"([^"]+)"').match

    def calculateToken():
        from time import time
        from base64 import b64encode as b64
        import hashlib
        o = 48
        n = support.match(host + '/client-address').data
        i = 'Yc8U6r8KjAKAepEA'
        t = int(time() + (3600 * o))
        l = '{}{} {}'.format(t, n, i)
        md5 = hashlib.md5(l.encode())
        s = '?token={}&expires={}'.format(b64(md5.digest()).decode().replace('=', '').replace('+', "-").replace('\\', "_"), t)
        return s
    token = calculateToken()


    def videourls(res):
        newurl = '{}/{}{}'.format(url, res, token)
        if requests.head(newurl, headers=headers).status_code == 200:
            video_urls.append({'type':'m3u8', 'res':res, 'url':newurl})

    with futures.ThreadPoolExecutor() as executor:
        for res in ['480p', '720p', '1080p']:
            executor.submit(videourls, res) 

    if not video_urls: video_urls = [{'type':'m3u8', 'url':url + token}]
    itemlist = [item.clone(title = channeltools.get_channel_parameters(item.channel)['title'], server='directo', video_urls=video_urls, thumbnail=channeltools.get_channel_parameters(item.channel)["thumbnail"], forcethumb=True)]
    return support.server(item, itemlist=itemlist)