# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Paramount Network
# ------------------------------------------------------------
import inspect
from core import support, jsontools
from platformcode import autorenumber, logger
from collections import OrderedDict

from specials import videolibrary

host = support.config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    top = [('Dirette {bold}', ['', 'live'])]
    film = ['/film']
    tvshow = ['/programmi']
    return locals()

@support.scrape
def menu(item):
    action='peliculas'
    blacklist=['Tutti']
    patronMenu = r'<a data-display-name="Link" href="(?P<url>[^"]+)" class="[^"]+">(?P<title>[^<]+)'
    return locals()


def search(item, text):
    logger.info(text)

    item.text = text
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def liveDict():
    livedict = OrderedDict({})
    urls=[]
    matches = support.match(host, patron=r'(/diretta-tv/[^"]+)"[^>]+>([^ ]+)').matches
    from datetime import date
    today = date.today()
    channels = jsontools.load(support.match(host + '/api/more/tvschedule/' + str(today.year) + str(today.month) + str(today.day)).data)['channels']

    for channel in channels:
        title = channel['label']
        livedict[title] = {}
        livedict[title]['id'] = channel['channelId']
    for url, title in matches:
        if url not in urls:
            urls.append(url)
            livedict[title]['url'] = host + url
            info = jsontools.load(support.match(host +'/api/on-air?channelId=' + livedict[title]['id']).data)
            livedict[title]['plot']= '[B]' + info['seriesTitle'] +'[/B]\n' + info['description'] if 'seriesTitle' in info else ''
    return livedict

def live(item):
    logger.debug()
    itemlist=[]
    for key, value in liveDict().items():
        itemlist.append(item.clone(title=support.typo(key,'bold'), contentTitle=key, fulltitle=key, show=key, url=value['url'], plot=value['plot'], action='findvideos', forcethumb=True, no_return=True))
    return support.thumb(itemlist, live=True)


def peliculas(item):
    logger.debug()
    def load_more(url):
        second_url = host if url.startswith('/') else '' + url.replace('\u002F','/').replace('\\u002F','/').replace('%5C','/')
        new_data = support.match(host + second_url).data.replace('\x01','l').replace('\x02','a')
        return jsontools.load(new_data)['items']

    itemlist = []
    data = []
    page_data = support.match(item.url).data
    more = support.match(page_data, patron=r'loadingTitle":[^,]+,"url":"([^"]+)"').match
    data = jsontools.load(support.scrapertools.decodeHtmlentities(support.match(page_data, patron=[r'"nextPageUrl":[^,]+,"items":(.*?),"customContainerClass"', r'Streaming"},"items":(.*?),"isGrid"']).match))

    if data:
        if more:
            new_data = load_more(more)
            data += new_data
        for it in data:
            try:
                title = it['meta']['header']['title']
            except:
                continue
            if item.text.lower() in title.lower():
                itemlist.append(
                    item.clone(title=support.typo(title,'bold'),
                               fulltitle = title,
                               show = title,
                               contentTitle = title if item.contentType == 'movie' else '',
                               contentSerieName = title if item.contentType != 'movie' else '',
                               url = host + it['url'] if it['url'].startswith('/') else it['url'],
                               thumbnail = it['media']['image']['url'],
                               fanart = it['media']['image']['url'],
                               plot = it['meta']['description'],
                               action = 'findvideos' if item.contentType == 'movie' else 'episodios'))
    return itemlist


def episodios(item):
    logger.debug()
    reEp = r'"isEpisodes":[^,]+,"items":(.*?])'
    def load_more(url):
        second_url = host if url.startswith('/') else '' + url.replace('\u002F','/').replace('%5C','/')
        new_data = support.match(host + second_url).data
        match = support.scrapertools.decodeHtmlentities(support.match(new_data, headers=headers, patron=r'"items":([^\]]+])').match.replace('\x01','l').replace('\x02','a'))
        return jsontools.load(match)

    itemlist = []
    page_data = support.match(item.url).data
    seasons = support.match(page_data, patron=r'href="([^"]+)"[^>]+>Stagione\s*\d+').matches
    more = support.match(page_data, patron=r'loadingTitle":[^,]+,"url":"([^"]+)"').match
    data = jsontools.load(support.scrapertools.decodeHtmlentities(support.match(page_data, patron=reEp).match))

    if data:
        if more:
            data += load_more(more)
        if seasons:
            for url in seasons:
                new_data = support.match(host + url).data
                data += jsontools.load(support.scrapertools.decodeHtmlentities(support.match(new_data, patron=reEp).match.replace('\x01','l').replace('\x02','a')))
                match = support.match(new_data, patron=r'loadingTitle":[^,]+,"url":"([^"]+)"').match
                if match and match != load_more:
                    data += load_more(match)

        for it in data:
            if 'text' in it['meta']['header']['title']:
                se = it['meta']['header']['title']['text']
                s = support.match(se, patron=r'S\s*(?P<season>\d+)').match
                e = support.match(se, patron=r'E\s*(?P<episode>\d+)').match
                if not e: e = support.match(it['meta']['subHeader'], patron=r'(\d+)').match
                title = support.typo((s + 'x' if s else 'Episodio ') + e.zfill(2) + ' - ' + it['meta']['subHeader'],'bold')
            else:
                s = e = '0'
                title = support.typo(it['meta']['header']['title'],'bold')
            itemlist.append(
                item.clone(title=title,
                        season=int(s) if s else '',
                        episode=int(e),
                        url=host + it['url'] if it['url'].startswith('/') else it['url'],
                        thumbnail=it['media']['image']['url'],
                        fanart=it['media']['image']['url'],
                        plot=it['meta']['description'],
                        contentType='episode',
                        action='findvideos'))

    itemlist.sort(key=lambda item: (item.season, item.episode))
    if inspect.stack(0)[1][3] not in ['find_episodes']:
        autorenumber.start(itemlist, item)
    return support.videolibrary(itemlist, item)


def findvideos(item):
    logger.debug()
    logger.debug()
    item.manifest = 'hls'
    mgid = support.match(item.url, patron=r'uri":"([^"]+)"').match
    url = 'https://media.mtvnservices.com/pmt/e1/access/index.html?uri=' + mgid + '&configtype=edge&ref=' + item.url
    ID, rootUrl = support.match(url, patron=[r'"id":"([^"]+)",',r'brightcove_mediagenRootURL":"([^"]+)"']).matches
    item.url = jsontools.load(support.match(rootUrl.replace('&device={device}','').format(uri = ID)).data)['package']['video']['item'][0]['rendition'][0]['src']
    return support.server(item, itemlist=[item.clone(title='Paramount', server='directo', action='play')], Download=False, Videolibrary=False)


# def play(item):
#     logger.debug()
#     item.manifest = 'hls'
#     mgid = support.match(item.url, patron=r'uri":"([^"]+)"').match
#     url = 'https://media.mtvnservices.com/pmt/e1/access/index.html?uri=' + mgid + '&configtype=edge&ref=' + item.url
#     ID, rootUrl = support.match(url, patron=[r'"id":"([^"]+)",',r'brightcove_mediagenRootURL":"([^"]+)"']).matches
#     item.url = jsontools.load(support.match(rootUrl.replace('&device={device}','').format(uri = ID)).data)['package']['video']['item'][0]['rendition'][0]['src']


#     return [item]