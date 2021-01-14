# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per StreamingCommunity
# ------------------------------------------------------------

import json, requests, sys
from core import support
from platformcode import logger
if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

host = support.config.get_channel_url()
session = requests.Session()
headers = {}

def getHeaders():
    global headers
    if not headers:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'}
        response = session.get(host)
        csrf_token = support.match(response.text, patron='name="csrf-token" content="([^"]+)"').match
        headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14',
                    'content-type': 'application/json;charset=UTF-8',
                    'Referer': host,
                    'x-csrf-token': csrf_token,
                    'Cookie': '; '.join([x.name + '=' + x.value for x in response.cookies])}


@support.menu
def mainlist(item):
    film=['',
          ('Generi',['/film','genres']),
          ('Titoli del Momento',['/film','peliculas',0]),
          ('Novità',['/film','peliculas',1]),
          ('Popolari',['/film','peliculas',2])]
    tvshow=['',
            ('Generi',['/serie-tv','genres']),
            ('Titoli del Momento',['/serie-tv','peliculas',0]),
            ('Novità',['/serie-tv','peliculas',1]),
            ('Popolari',['/serie-tv','peliculas',2])]
    search=''
    return locals()


def genres(item):
    getHeaders()
    logger.debug()
    itemlist = []
    data = support.scrapertools.decodeHtmlentities(support.match(item).data)
    args = support.match(data, patronBlock=r'genre-options-json="([^\]]+)\]', patron=r'name"\s*:\s*"([^"]+)').matches
    for arg in args:
        itemlist.append(item.clone(title=support.typo(arg, 'bold'), args=arg, action='peliculas'))
    support.thumb(itemlist, genre=True)
    return itemlist


def search(item, text):
    logger.debug('search', text)
    item.search = text

    try:
        return peliculas(item)
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
    if category == 'peliculas':
        item.url = host + '/film'
    else:
        item.url = host + '/serie-tv'

    try:
        itemlist = peliculas(item)

        if itemlist[-1].action == 'peliculas':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error(line)
        return []

    return itemlist



def peliculas(item):
    getHeaders()
    logger.debug()
    itemlist = []
    videoType = 'movie' if item.contentType == 'movie' else 'tv'

    page = item.page if item.page else 0
    offset = page * 60

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

    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(makeItem, i, it, item) for i, it in enumerate(js)]
        for res in futures.as_completed(itlist):
            itemlist.append(res.result())

    itemlist.sort(key=lambda item: item.n)

    if len(itemlist) >= 60:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), thumbnail=support.thumb(), page=page + 1))
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def makeItem(n, it, item):
    info = session.post(host + '/api/titles/preview/{}'.format(it['id']), headers=headers).json()
    title, lang = support.match(info['name'], patron=r'([^\[|$]+)(?:\[([^\]]+)\])?').match
    if not lang:
        lang = 'ITA'
    itm = item.clone(title=support.typo(title,'bold') + support.typo(lang,'_ [] color kod bold'))
    itm.contentType = info['type'].replace('tv', 'tvshow')
    itm.language = lang
    itm.year = info['release_date'].split('-')[0]


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
        itm.action = 'episodios'
        itm.season_count = info['seasons_count']
        itm.url = host + '/titles/%s-%s' % (it['id'], it['slug'])
    itm.n = n
    return itm

def episodios(item):
    getHeaders()
    logger.debug()
    itemlist = []

    js = json.loads(support.match(item.url, patron=r'seasons="([^"]+)').match.replace('&quot;','"'))

    for episodes in js:
        for it in episodes['episodes']:
            itemlist.append(
                support.Item(channel=item.channel,
                             title=support.typo(str(episodes['number']) + 'x' + str(it['number']).zfill(2) + ' - ' + it['name'], 'bold'),
                             episode = it['number'],
                             season=episodes['number'],
                             thumbnail=it['images'][0]['original_url'] if 'images' in it and 'original_url' in it['images'][0] else item.thumbnail,
                             fanart=item.fanart,
                             plot=it['plot'],
                             action='findvideos',
                             contentType='episode',
                             contentSerieName=item.fulltitle,
                             url=host + '/watch/' + str(episodes['title_id']) + '?e=' + str(it['id'])))

    support.videolibrary(itemlist, item)
    support.download(itemlist, item)
    return itemlist


def findvideos(item):
    getHeaders()
    logger.debug()
    itemlist=[]
    url = support.match(support.match(item).data.replace('&quot;','"').replace('\\',''), patron=r'video_url"\s*:\s*"([^"]+)"').match
    for res in ['480p', '720p', '1080p']:
        newurl = '{}/{}'.format(url, res)
        if session.head(newurl, headers=headers).status_code == 200:
            itemlist += [item.clone(title=support.config.get_localized_string(30137), server='directo', url=newurl, quality=res, action='play')]
    return support.server(item, itemlist=itemlist)