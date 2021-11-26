# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per StreamingCommunity
# ------------------------------------------------------------

import json, requests, sys
from core import support, channeltools, jsontools
from platformcode import config, logger
if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

def findhost(url):
    matches = support.match(url, patron='<a href="([^"]+)" target="_blank"').matches
    if matches:
        return matches[-1]

host = support.config.get_channel_url(findhost)
session = requests.Session()
headers = {}
perpage = config.getSetting('pagination', 'streamingcommunity', default=1) * 10 + 10

def getHeaders(forced=False):
    global headers
    global host
    if not headers:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'}
            response = session.get(host, headers=headers)
            if not response.url.startswith(host):
                host = support.config.get_channel_url(findhost, forceFindhost=True)
            csrf_token = support.match(response.text, patron='name="csrf-token" content="([^"]+)"').match
            headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14',
                        'content-type': 'application/json;charset=UTF-8',
                        'Referer': host,
                        'x-csrf-token': csrf_token,
                        'Cookie': '; '.join([x.name + '=' + x.value for x in response.cookies])}
        except:
            host = support.config.get_channel_url(findhost, forceFindhost=True)
            if not forced: getHeaders(True)

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
    support.thumb(itemlist, mode=True)
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
    videoType = 'movie' if item.contentType == 'movie' else 'tv'

    page = item.page if item.page else 0
    offset = page * perpage

    if type(item.args) == int:
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
        
    logger.debug(jsontools.dump(js))

    itemlist = makeItems(item, js)

    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if len(itemlist) == perpage:
        support.nextPage(itemlist, item, 'movies', page=page + 1)

    return itemlist


def makeItems(item, items):
    itemlist = []
    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(makeItem, n, it, item) for n, it in enumerate(items) if n < perpage]
        for res in futures.as_completed(itlist):
            if res.result():
                itemlist.append(res.result())
    itemlist.sort(key=lambda item: item.n)
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
    channelParams = channeltools.get_channel_parameters(item.channel)
    itemlist = [item.clone(title = channelParams['title'], server='directo',  thumbnail=channelParams["thumbnail"], forcethumb=True, action='play')]
    return support.server(item, itemlist=itemlist)

def play(item):
    from time import time
    from base64 import b64encode
    from hashlib import md5

    data = support.httptools.downloadpage(item.url + item.episodeid, headers=headers).data.replace('&quot;','"').replace('\\','')
    scws_id = support.match(data, patron=r'scws_id"\s*:\s*(\d+)').match

    if not scws_id:
        return []

    # Calculate Token
    client_ip = support.httptools.downloadpage('https://scws.xyz/videos/' + scws_id, headers=headers).json.get('client_ip')
    expires = int(time() + 172800)
    token = b64encode(md5('{}{} Yc8U6r8KjAKAepEA'.format(expires, client_ip).encode('utf-8')).digest()).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')

    url = 'https://scws.xyz/master/{}?token={}&expires={}&n=1'.format(scws_id, token, expires)

    return [item.clone(server='directo', url=url, manifest='hls')]