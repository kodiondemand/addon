# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeUnity
# ------------------------------------------------------------

import cloudscraper, json, copy, inspect
from core import jsontools, support, httptools, filetools
from platformcode import autorenumber, logger
import re
import xbmc


session = cloudscraper.create_scraper()

host = support.config.get_channel_url()
response = session.get(host + '/archivio')
csrf_token = support.match(response.text, patron='name="csrf-token" content="([^"]+)"').match
headers = {'content-type': 'application/json;charset=UTF-8',
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
    item.action = 'peliculas'
    ITA = copy.copy(item.args)
    ITA['title'] = '(ita)'
    InCorso = copy.copy(item.args)
    InCorso['status'] = 'In Corso'
    Terminato = copy.copy(item.args)
    Terminato['status'] = 'Terminato'
    itemlist = [item.clone(title=support.typo('Tutti','bold')),
                item.clone(title=support.typo('ITA','bold'), args=ITA),
                item.clone(title=support.typo('Genere','bold'), action='genres'),
                item.clone(title=support.typo('Anno','bold'), action='years')]
    if item.contentType == 'tvshow':
        itemlist += [item.clone(title=support.typo('In Corso','bold'), args=InCorso),
                     item.clone(title=support.typo('Terminato','bold'), args=Terminato)]
    itemlist +=[item.clone(title=support.typo('Cerca...','bold'), action='search', thumbnail=support.thumb('search'))]
    return itemlist


def genres(item):
    support.info()
    # support.dbg()
    itemlist = []

    genres = json.loads(support.match(response.text, patron='genres="([^"]+)').match.replace('&quot;','"'))

    for genre in genres:
        item.args['genres'] = [genre]
        itemlist.append(item.clone(title=support.typo(genre['name'],'bold'), action='peliculas'))
    return support.thumb(itemlist)

def years(item):
    support.info()
    itemlist = []

    from datetime import datetime
    current_year = datetime.today().year
    oldest_year = int(support.match(response.text, patron='anime_oldest_date="([^"]+)').match)

    for year in list(reversed(range(oldest_year, current_year + 1))):
        item.args['year']=year
        itemlist.append(item.clone(title=support.typo(year,'bold'), action='peliculas'))
    return itemlist


def search(item, text):
    support.info('search', item)
    if not item.args:
        item.args = {'title':text}
    else:
        item.args['title'] = text
    item.search = text

    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info('search log:', line)
        return []


def newest(categoria):
    support.info(categoria)
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
            support.info(line)
        return []

    return itemlist

def news(item):
    support.info()
    item.contentType = 'episode'
    itemlist = []
    import cloudscraper
    session = cloudscraper.create_scraper()

    fullJs = json.loads(support.match(session.get(item.url).text, headers=headers, patron=r'items-json="([^"]+)"').match.replace('&quot;','"'))
    js = fullJs['data']

    for it in js:
        itemlist.append(
            item.clone(title= support.typo(it['anime']['title'] + ' - EP. ' + it['number'], 'bold'),
                       fulltitle=it['anime']['title'],
                       thumbnail=it['anime']['imageurl'],
                       forcethumb = True,
                       video_url=it['scws_id'],
                       plot=it['anime']['plot'],
                       action='findvideos')
        )
    if 'next_page_url' in fullJs:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'),thumbnail=support.thumb(), url=fullJs['next_page_url']))
    return itemlist


def peliculas(item):
    support.info()
    itemlist = []

    page = item.page if item.page else 0
    item.args['offset'] = page * 30

    order = support.config.get_setting('order', item.channel)
    if order:
        order_list = [ "Standard", "Lista A-Z", "Lista Z-A", "Popolarità", "Valutazione" ]
        item.args['order'] = order_list[order]

    payload = json.dumps(item.args)
    records = session.post(host + '/archivio/get-animes', headers=headers, data=payload).json()['records']

    for it in records:
        logger.debug(jsontools.dump(it))
        lang = support.match(it['title'], patron=r'\(([It][Tt][Aa])\)').match
        title = support.re.sub(r'\s*\([^\)]+\)', '', it['title'])

        if 'ita' in lang.lower(): language = 'ITA'
        else: language = 'Sub-ITA'

        itm = item.clone(title=support.typo(title,'bold') + support.typo(language,'_ [] color kod') + (support.typo(it['title_eng'],'_ ()') if it['title_eng'] else ''))
        itm.contentLanguage = language
        itm.type = it['type']
        itm.thumbnail = it['imageurl']
        itm.plot = it['plot']
        itm.url = item.url

        if it['episodes_count'] == 1:
            itm.contentType = 'movie'
            itm.fulltitle = itm.show = itm.contentTitle = title
            itm.contentSerieName = ''
            itm.action = 'findvideos'
            itm.video_url = it['episodes'][0]['scws_id']

        else:
            itm.contentType = 'tvshow'
            itm.contentTitle = ''
            itm.fulltitle = itm.show = itm.contentSerieName = title
            itm.action = 'episodios'
            itm.episodes = it['episodes'] if 'episodes' in it else it['scws_id']
            itm.video_url = item.url

        itemlist.append(itm)

    autorenumber.start(itemlist)
    if len(itemlist) >= 30:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), thumbnail=support.thumb(), page=page + 1))

    return itemlist

def episodios(item):
    support.info()
    itemlist = []
    title = 'Parte ' if item.type.lower() == 'movie' else 'Episodio '
    for it in item.episodes:
        itemlist.append(
            item.clone(title=support.typo(title + it['number'], 'bold'),
                       episode = it['number'],
                       fulltitle=item.title,
                       show=item.title,
                       contentTitle='',
                       contentSerieName=item.contentSerieName,
                       thumbnail=item.thumbnail,
                       plot=item.plot,
                       action='findvideos',
                       contentType='episode',
                       video_url=it['scws_id']))

    if inspect.stack()[1][3] not in ['find_episodes']:
        autorenumber.start(itemlist, item)
    support.videolibrary(itemlist, item)
    support.download(itemlist, item)
    return itemlist


def findvideos(item):
    # def calculateToken():
    #     from time import time
    #     from base64 import b64encode as b64
    #     import hashlib
    #     o = 48
    #     n = support.match('https://au-1.scws-content.net/get-ip').data
    #     i = 'Yc8U6r8KjAKAepEA'
    #     t = int(time() + (3600 * o))
    #     l = '{}{} {}'.format(t, n, i)
    #     md5 = hashlib.md5(l.encode())
    #     s = '?token={}&expires={}'.format(b64(md5.digest()).decode().replace('=', '').replace('+', "-").replace('\\', "_"), t)
    #     return s
    # token = calculateToken()

    # url = 'https://streamingcommunityws.com/master/{}{}'.format(item.video_url, token)

    # # support.dbg()

    # m3u8_original = httptools.downloadpage(url, CF=False).data

    # m_video = re.search(r'\.\/video\/(\d+p)\/playlist.m3u8', m3u8_original)
    # video_res = m_video.group(1)
    # m_audio = re.search(r'\.\/audio\/(\d+k)\/playlist.m3u8', m3u8_original)
    # audio_res = m_audio.group(1)

    # # https://streamingcommunityws.com/master/5957?type=video&rendition=480p&token=wQLowWskEnbLfOfXXWWPGA&expires=1623437317
    # video_url = 'https://streamingcommunityws.com/master/{}{}&type=video&rendition={}'.format(item.video_url, token, video_res)
    # audio_url = 'https://streamingcommunityws.com/master/{}{}&type=audio&rendition={}'.format(item.video_url, token, audio_res)

    # m3u8_original = m3u8_original.replace( m_video.group(0),  video_url )
    # m3u8_original = m3u8_original.replace( m_audio.group(0),  audio_url )

    # file_path = 'special://temp/animeunity.m3u8'

    # filetools.write(xbmc.translatePath(file_path), m3u8_original, 'w')

    # return support.server(item, itemlist=[item.clone(title=support.config.get_localized_string(30137), url=file_path, manifest = 'hls', server='directo', action='play')])
    # item.url=item.video_url

    directLink = False
    if item.video_url == None:
        if item.extra == "tvshow":
            epnum = item.episode
            logger.info('it is a episode', epnum)
            episode = None
            for ep in item.episodes:
                if ep["number"] == epnum:
                    episode = ep
                    break
            if episode == None:
                logger.warn('cannot found episode')
            else:
                item.url = episode["link"]
                directLink = True




    if directLink:
        logger.info('try direct link')
        return support.server(item, itemlist=[item.clone(title=support.config.get_localized_string(30137), url=item.url, server='directo', action='play')])
    else:
        return support.server(item, itemlist=[item.clone(title=support.config.get_localized_string(30137), url=str(item.video_url), manifest = 'hls', server='streamingcommunityws', action='play')])




