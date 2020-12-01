# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Paramount Network
# ------------------------------------------------------------

from core import support, jsontools
from platformcode import autorenumber

# host = support.config.get_channel_url()
host = 'https://www.paramountnetwork.it'
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    top = [('Dirette {bold}', ['/dl/RaiPlay/2016/PublishingBlock-9a2ff311-fcf0-4539-8f8f-c4fee2a71d58.html?json', 'live'])]
    film = []
    tvshow = []
    return locals()

@support.scrape
def menu(item):
    action='peliculas'
    blacklist=['Tutti']
    patronMenu = r'<a data-display-name="Link" href="(?P<url>[^"]+)" class="[^"]+">(?P<title>[^<]+)'
    return locals()


def search(item, text):
    support.info(text)

    item.search = text.replace(' ','+')
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def live(item):
    itemlist=[]
    urls=[]
    matches = support.match(host, patron=r'(/diretta-tv/[^"]+)"[^>]+>([^ ]+)').matches
    from datetime import date
    today = date.today()
    channels = jsontools.load(support.match(host + '/api/more/tvschedule/' + str(today.year) + str(today.month) + str(today.day)).data)['channels']
    ch_dict = {}
    for channel in channels:
        ch_dict[channel['label']] = channel['channelId']
    for url, title in matches:
        if url not in urls:
            urls.append(url)
            info = jsontools.load(support.match(host +'/api/on-air?channelId=' + ch_dict[title]).data)
            support.info(info)
            plot= '[B]' + info['seriesTitle'] +'[/B]\n' + info['description'] if 'seriesTitle' in info else ''
            itemlist.append(item.clone(title=support.typo(title,'bold'), contentTitle=title, url=host+url, plot=plot, action='findvideos'))
    return itemlist


def peliculas(item):
    itemlist = []
    if item.contentType == 'movie':
        Type = 'Movie'
        action = 'findvideos'
    else:
        Type = 'Series'
        action = 'episodios'
    if not item.page: item.page = 1
    pagination_values = [20, 40, 60, 80, 100]
    pagination = pagination_values[support.config.get_setting('pagination','paramount')]
    item.url = host + '/api/search?activeTab=' + Type + '&searchFilter=site&pageNumber=0&rowsPerPage=10000'
    data = jsontools.load(support.match(item).data)['response']['items']
    titles = []
    for it in data:
        title = it['meta']['header']['title']
        if title not in titles:
            titles.append(title)
            d = it['meta']['date'].split('/') if it['meta']['date'] else ['0000','00','00']
            date = int(d[2] + d[1] + d[0])
            if item.search.lower() in title.lower() \
                and 'stagione' not in it['url'] \
                and 'season' not in it['url'] \
                and title not in ['Serie TV']:
                itemlist.append(
                    item.clone(title=support.typo(title,'bold'),
                            action=action,
                            fulltitle=title,
                            show=title,
                            contentTitle=title if it['type'] == 'movie' else '',
                            contentSerieName=title if it['type'] != 'movie' else '',
                            plot= it['meta']['description'] if 'description' in it['meta'] else '',
                            url=host + it['url'],
                            date=date,
                            thumbnail='https:' + it['media']['image']['url'] if 'url' in it['media']['image'] else item.thumbnail))
    itemlist.sort(key=lambda item: item.fulltitle)
    if not item.search:
        itlist = []
        for i, it in enumerate(itemlist):
            if pagination and (item.page - 1) * pagination > i and not item.search: continue  # pagination
            if pagination and i >= item.page * pagination and not item.search: break          # pagination
            itlist.append(it)
        if pagination and len(itemlist) >= item.page * pagination and not item.search:
            itlist.append(item.clone(channel=item.channel, action = 'peliculas', title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), page=item.page + 1, thumbnail=support.thumb()))
        itemlist = itlist
    autorenumber.renumber(itemlist, item, 'bold')
    return itemlist


def episodios(item):
    def load_more(url):
        second_url = host if url.startswith('/') else '' + url.replace('\u002F','/').replace('%5C','/')
        new_data = support.match(host + second_url).data
        match = support.scrapertools.decodeHtmlentities(support.match(new_data, headers=headers, patron=r'"items":([^\]]+])').match.replace('\x01','l').replace('\x02','a'))
        return jsontools.load(match)

    itemlist = []
    data = []
    page_data = support.match(item.url).data
    seasons = support.match(page_data, patron=r'href="([^"]+)"[^>]+>Stagione\s*\d+').matches
    more = support.match(page_data, patron=r'loadingTitle":[^,]+,"url":"([^"]+)"').match
    data = jsontools.load(support.scrapertools.decodeHtmlentities(support.match(page_data, patron=r'"isEpisodes":[^,]+,"items":(.*?),"as"').match))

    if data:
        if more:
            data += load_more(more)
        if seasons:
            for url in seasons:
                new_data = support.match(host + url).data
                data += jsontools.load(support.scrapertools.decodeHtmlentities(support.match(new_data, patron=r'isEpisodes":[^,]+,"items":(.*?),"as"').match.replace('\x01','l').replace('\x02','a')))
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
    autorenumber.renumber(itemlist, item, 'bold')
    return support.videolibrary(itemlist, item)


def findvideos(item):
    itemlist = []
    qualities = []

    mgid = support.match(item, patron=r'uri":"([^"]+)"').match
    url = 'https://media.mtvnservices.com/pmt/e1/access/index.html?uri=' + mgid + '&configtype=edge&ref=' + item.url
    ID, rootUrl = support.match(url, patron=[r'"id":"([^"]+)",',r'brightcove_mediagenRootURL":"([^"]+)"']).matches
    url = jsontools.load(support.match(rootUrl.replace('&device={device}','').format(uri = ID)).data)['package']['video']['item'][0]['rendition'][0]['src']
    video_urls = support.match(url, patron=r'RESOLUTION=(\d+x\d+).*?(http[^ ]+)').matches
    for quality, url in video_urls:
        if quality not in qualities:
            qualities.append(quality)
            itemlist.append(item.clone(title=support.config.get_localized_string(30137), server='directo', action='play', url=url, quality=quality, focusOnVideoPlayer=True))
    itemlist.sort(key=lambda item: item.quality)
    return support.server(item, itemlist=itemlist, Download=False)
