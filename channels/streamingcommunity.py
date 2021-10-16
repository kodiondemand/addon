# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per StreamingCommunity
# ------------------------------------------------------------

import json, requests, sys
from channels.mediasetplay import Token
from core import support, channeltools
from platformcode import logger


def findhost(url):
    return 'https://' + support.match(url, patron='var domain\s*=\s*"([^"]+)').match


host = support.config.get_channel_url(findhost)
session = requests.Session()
headers = {}

def getHeaders():
    global headers
    global host
    # support.dbg()
    if not headers:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'}
        response = session.get(host, headers=headers)
        if response.status_code != 200 or response.url != host:
            host = support.config.get_channel_url(findhost, forceFindhost=True)
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
    # getHeaders()
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
    # getHeaders()
    logger.debug()

    global host
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
    title = support.cleantitle(title)
    if not lang:
        lang = 'ITA'
    itm = item.clone(title=support.typo(title,'bold') + support.typo(lang,'_ [] color kod bold'))
    itm.contentType = info['type'].replace('tv', 'tvshow')
    itm.language = lang
    itm.year = info['release_date'].split('-')[0]


    if itm.contentType == 'movie':
        # itm.contentType = 'movie'
        itm.fulltitle = itm.show = itm.contentTitle = title
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
    # getHeaders()
    logger.debug()
    itemlist = []

    js = json.loads(support.match(item.url, patron=r'seasons="([^"]+)').match.replace('&quot;','"'))

    for episodes in js:
        for it in episodes['episodes']:
            itemlist.append(
                support.Item(channel=item.channel,
                             title=support.typo(str(episodes['number']) + 'x' + str(it['number']).zfill(2) + ' - ' + support.cleantitle(it['name']), 'bold'),
                             episode = it['number'],
                             season=episodes['number'],
                             thumbnail=it['images'][0]['original_url'] if 'images' in it and 'original_url' in it['images'][0] else item.thumbnail,
                             fanart=item.fanart,
                             plot=it['plot'],
                             action='findvideos',
                             contentType='episode',
                             contentSerieName=item.fulltitle,
                             url=host + '/watch/' + str(episodes['title_id']),
                             episodeid= '?e=' + str(it['id'])))

    support.videolibrary(itemlist, item)
    support.download(itemlist, item)
    return itemlist


def findvideos(item):
    itemlist = [item.clone(title = channeltools.get_channel_parameters(item.channel)['title'], server='directo')]
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

    return [item.clone(title = channeltools.get_channel_parameters(item.channel)['title'], server='directo', url=url, manifest='hls')]
