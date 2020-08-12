# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeUnity
# ------------------------------------------------------------

import requests, json, copy
from core import support, jsontools
from specials import autorenumber

try: from lib import cloudscraper
except: from lib import cloudscraper


host = support.config.get_channel_url()

session=requests.Session()
response = session.get(host)
csrf_token = support.match(response.text, patron= 'name="csrf-token" content="([^"]+)"').match
headers = {'content-type': 'application/json;charset=UTF-8',
           'x-csrf-token': csrf_token,
           'Cookie' : '; '.join([x.name + '=' + x.value for x in response.cookies])}

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
    support.log()
    itemlist = []
    data = support.scrapertools.decodeHtmlentities(support.match(item).data)
    args = support.match(data, patronBlock=r'genre-options-json="([^\]]+)\]', patron=r'name"\s*:\s*"([^"]+)').matches
    for arg in args:
        itemlist.append(item.clone(title=support.typo(arg, 'bold'), args=arg, action='peliculas'))
    support.thumb(itemlist, genre=True)
    return itemlist


def search(item, text):
    support.log('search', item)
    item.search = text

    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []


def newest(category):
    support.log(category)
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
            support.log(line)
        return []

    return itemlist



def peliculas(item):
    support.log()
    itemlist = []
    videoType = 'movie' if item.contentType == 'movie' else 'tv'

    page = item.page if item.page else 0
    offset = page * 60

    if type(item.args) == int:
        data = support.scrapertools.decodeHtmlentities(support.match(item).data)
        records = json.loads(support.match(data, patron=r'slider-title titles-json="(.*?)" slider-name="').matches[item.args])
    elif not item.search:
        payload = json.dumps({'type': videoType, 'offset':offset, 'genre':item.args})
        records = json.loads(requests.post(host + '/infinite/browse', headers=headers, data=payload).json()['records'])
    else:
        records = requests.get(host + '/search?q=' + item.search + '&live=true', headers=headers).json()['records']

    if records and type(records[0]) == list:
        js = []
        for record in records:
            js += record
    else:
        js = records

    for it in js:
        title, lang = support.match(it['name'], patron=r'([^\[|$]+)(?:\[([^\]]+)\])?').match
        if not lang:
            lang = 'ITA'
        itm = item.clone(title=support.typo(title,'bold') + support.typo(lang,'_ [] color kod bold'))
        itm.type = it['type']
        itm.thumbnail = 'https://image.tmdb.org/t/p/w500' + it['images'][0]['url']
        itm.fanart = 'https://image.tmdb.org/t/p/w1280' + it['images'][2]['url']
        itm.plot = it['plot']
        itm.infoLabels['tmdb_id'] = it['tmdb_id']
        itm.language = lang


        if itm.type == 'movie':
            itm.contentType = 'movie'
            itm.fulltitle = itm.show = itm.contentTitle = title
            itm.contentSerieName = ''
            itm.action = 'findvideos'
            itm.url = host + '/watch/%s' % it['id']

        else:
            itm.contentType = 'tvshow'
            itm.contentTitle = ''
            itm.fulltitle = itm.show = itm.contentSerieName = title
            itm.action = 'episodios'
            itm.season_count = it['seasons_count']
            itm.url = host + '/titles/%s-%s' % (it['id'], it['slug'])

        itemlist.append(itm)

    if len(itemlist) >= 60:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), thumbnail=support.thumb(), page=page + 1))
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def episodios(item):
    support.log()
    itemlist = []

    js = json.loads(support.match(item.url, patron=r'seasons="([^"]+)').match.replace('&quot;','"'))
    support.log(js)

    for episodes in js:
        for it in episodes['episodes']:
            support.log(it)
            itemlist.append(
                support.Item(channel=item.channel,
                            title=support.typo(str(episodes['number']) + 'x' + str(it['number']).zfill(2) + ' - ' + it['name'], 'bold'),
                            episode = it['number'],
                            season=episodes['number'],
                            thumbnail='https://image.tmdb.org/t/p/w1280' + it['images'][0]['url'],
                            fanart='https://image.tmdb.org/t/p/w1280' + it['images'][0]['url'],
                            plot=it['plot'],
                            action='findvideos',
                            contentType='episode',
                            url=host + '/watch/' + str(episodes['title_id']) + '?e=' + str(it['id'])))

    support.videolibrary(itemlist, item)
    support.download(itemlist, item)
    return itemlist


def findvideos(item):
    support.log()
    itemlist=[]
    url = support.match(support.match(item).data.replace('&quot;','"').replace('\\',''), patron=r'video_url"\s*:\s*"([^"]+)"').match
    playlist = support.match(url, patron=r'\./([^.]+)').matches
    for res in playlist:
        itemlist.append(item.clone(title=support.config.get_localized_string(30137), server='directo', url=url.replace('playlist',res), quality=res, action='play'))
    return support.server(item, itemlist=itemlist)