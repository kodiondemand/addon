# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeUnity
# ------------------------------------------------------------

import cloudscraper, json, copy, inspect
from core import jsontools, support, config
from core.httptools import downloadpage
from platformcode import autorenumber, logger

session = cloudscraper.create_scraper()

host = support.config.get_channel_url()
response = session.get(host + '/archivio')
csrf_token = support.match(response.text, patron='name="csrf-token" content="([^"]+)"').match
headers = {'content-type': 'application/json;charset=UTF-8',
           'Referer': host,
           'x-csrf-token': csrf_token,
           'Cookie' : '; '.join([x.name + '=' + x.value for x in response.cookies])}

@support.menu
def mainlist(item):
    top =  [('Ultimi Episodi', ['', 'news'])]

    menu = [('Anime {bullet bold}',['', 'menu', {}, 'tvshow']),
            ('Film {submenu}',['', 'menu', {'type': 'Movie'}]),
            ('TV {submenu}',['', 'menu', {'type': 'TV'}, 'tvshow']),
            ('OVA {submenu} {tv}',['', 'menu', {'type': 'OVA'}, 'tvshow']),
            ('ONA {submenu} {tv}',['', 'menu', {'type': 'ONA'}, 'tvshow']),
            ('Special {submenu} {tv}',['', 'menu', {'type': 'Special'}, 'tvshow'])]
    search =''
    return locals()


def menu(item):
    item.action = 'movies'
    ITA = copy.copy(item.args)
    ITA['title'] = '(ita)'
    InCorso = copy.copy(item.args)
    InCorso['status'] = 'In Corso'
    Terminato = copy.copy(item.args)
    Terminato['status'] = 'Terminato'
    itemlist = [item.clone(title=support.typo('Tutti','bold')),
                item.clone(title='ITA', args=ITA),
                item.clone(title='Genere', action='genres'),
                item.clone(title='Anno', action='years')]
    if item.contentType == 'tvshow':
        itemlist += [item.clone(title='In Corso', args=InCorso),
                     item.clone(title='Terminato', args=Terminato)]
    itemlist +=[item.clone(title=support.typo(config.getLocalizedString(70741).replace(' %s', '…'),'bold'), action='search', thumbnail=support.thumb('search'))]
    return itemlist


def genres(item):
    logger.debug()
    itemlist = []

    genres = json.loads(support.match(response.text, patron='genres="([^"]+)').match.replace('&quot;','"'))

    for genre in genres:
        item.args['genres'] = [genre]
        itemlist.append(item.clone(title=genre['name'], action='movies'))
    return support.thumb(itemlist)

def years(item):
    logger.debug()
    itemlist = []

    from datetime import datetime
    current_year = datetime.today().year
    oldest_year = int(support.match(response.text, patron='anime_oldest_date="([^"]+)').match)

    for year in list(reversed(range(oldest_year, current_year + 1))):
        item.args['year']=year
        itemlist.append(item.clone(title=year, action='movies'))
    return itemlist


def search(item, text):
    logger.debug(text)
    if not item.args:
        item.args = {'title':text}
    else:
        item.args['title'] = text
    item.search = text

    try:
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.debug('search log:', line)
        return []


def newest(category):
    logger.debug(category)
    itemlist = []
    item = support.Item()
    item.url = host

    try:
        itemlist = news(item)

        if itemlist[-1].action == 'news':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.debug(line)
        return []

    return itemlist

def news(item):
    logger.debug()
    item.contentType = 'episode'
    itemlist = []
    import cloudscraper
    session = cloudscraper.create_scraper()

    fullJs = json.loads(support.match(session.get(item.url).text, headers=headers, patron=r'items-json="([^"]+)"').match.replace('&quot;','"'))
    # logger.debug(jsontools.dump(fullJs))
    js = fullJs['data']

    for it in js:
        itemlist.append(
            item.clone(title=it['anime']['title'],
                       contentTitle = it['anime']['title'],
                       contentEpisodeNumber = int(it['number']),
                       fulltitle=it['anime']['title'],
                       thumbnail=it['anime']['imageurl'],
                       forcethumb = True,
                       videoUrl=it['scws_id'],
                       plot=it['anime']['plot'],
                       action='findvideos')
        )
    if fullJs.get('next_page_url'):
        support.nextPage(itemlist, item, 'news', next_page=fullJs['next_page_url'], total_pages=int(fullJs['last_page_url'].split('=')[-1]))
    return itemlist


def movies(item):
    logger.debug()
    itemlist = []

    page = item.page if item.page else 0
    item.args['offset'] = page * 30

    order = support.config.getSetting('order', item.channel)
    if order:
        order_list = [ "Standard", "Lista A-Z", "Lista Z-A", "Popolarità", "Valutazione" ]
        item.args['order'] = order_list[order]

    payload = json.dumps(item.args)
    js = session.post(host + '/archivio/get-animes', headers=headers, data=payload).json()
    records = js['records']
    total_pages = int(js['tot'] / 30)

    for it in records:
        logger.debug(jsontools.dump(it))
        lang = support.match(it['title'], patron=r'\(([It][Tt][Aa])\)').match
        title = support.re.sub(r'\s*\([^\)]+\)', '', it['title'])

        if 'ita' in lang.lower(): language = 'ITA'
        else: language = 'Sub-ITA'

        itm = item.clone(title=title,
                         contentLanguage = language,
                         type = it['type'],
                         thumbnail = it['imageurl'],
                         plot = it['plot'],
                         url = '{}/{}-{}'.format(item.url, it['id'], it['slug'])
                         )
        # itm.contentLanguage = language
        # itm.type = it['type']
        # itm.thumbnail = it['imageurl']
        # itm.plot = it['plot']
        # itm.url = item.url

        if it['episodes_count'] == 1:
            itm.contentType = 'movie'
            itm.fulltitle = itm.show = itm.contentTitle = title
            itm.contentSerieName = ''
            itm.action = 'play'
            item.forcethumb=True
            itm.videoUrl = it['episodes'][0]['scws_id']

        else:
            itm.contentType = 'tvshow'
            itm.contentTitle = ''
            itm.fulltitle = itm.show = itm.contentSerieName = title
            itm.action = 'episodes'
            itm.episodes = it['episodes'] if 'episodes' in it else it['scws_id']
            # itm.videoUrl = item.url

        itemlist.append(itm)

    autorenumber.start(itemlist)
    if len(itemlist) == 30:
        support.nextPage(itemlist, item, 'movies', page=page + 1, total_pages=total_pages)

    return itemlist

def episodes(item):
    logger.debug()
    itemlist = []
    # title = 'Parte ' if item.type.lower() == 'movie' else 'Episodio '
    for it in item.episodes:

        episode2 = it['number'].split('.')[-1]
        episode = it['number'].split('.')[0]
        itemlist.append(
            item.clone(episodes = [],
                       contentEpisodeNumber=int(float(it['number'])),
                       episodeExtra = '.' + it['number'].split('.')[-1] if '.' in it['number'] else '',
                       action='play',
                       contentType='episode',
                       forcethumb=True,
                       videoUrl=it['scws_id']))

    if inspect.stack()[1][3] not in ['find_episodes']:
        autorenumber.start(itemlist, item)
    support.videolibrary(itemlist, item)
    support.download(itemlist, item)
    return itemlist


def play(item):
    from time import time
    from base64 import b64encode
    from hashlib import md5

    # Calculate Token
    client_ip = support.httptools.downloadpage('https://scws.xyz/videos/{}'.format(item.videoUrl), headers=headers).json.get('client_ip')
    expires = int(time() + 172800)
    token = b64encode(md5('{}{} Yc8U6r8KjAKAepEA'.format(expires, client_ip).encode('utf-8')).digest()).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')

    url = 'https://scws.xyz/master/{}?token={}&expires={}&n=1'.format(item.videoUrl, token, expires)

    return [item.clone(server='directo', url=url,  manifest='hls')]

