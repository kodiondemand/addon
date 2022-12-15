from platformcode import config, logger, autorenumber
from core import httptools, scrapertools, support, tmdb, jsontools
from inspect import stack

import sys
if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

host = config.get_channel_url()
sort = ['views', 'title', 'episodeNumber', 'startDate', 'endDate', 'createdDate'][config.get_setting('sort', 'aniplay')]
order = 'asc' if config.get_setting('order', 'aniplay') else 'desc'
perpage = [10, 20, 30 ,40, 50, 60, 70, 80, 90][config.get_setting('perpage', 'aniplay')]


@support.menu
def mainlist(item):
    anime=['/api/anime/advanced-search',
           ('A-Z', ['/api/anime/advanced-search', 'submenu_az', '']),
           ('Anno', ['', 'submenu_year', '']),
           ('Top', ['', 'submenu_top', '']),
           ('Ultimi aggiunti', ['', 'latest_added', ''])]
    return locals()


def submenu_az(item):
    itemlist = []
    for letter in ['0-9'] + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        itemlist.append(item.clone(title = support.typo(letter, 'bold'),
                                url= host + '/api/anime/find-by-char',
                                action= 'peliculas',
                                variable= '&character=' + letter,
                                thumbnail=support.thumb('az')))
    return itemlist


def submenu_year(item):
    itemlist = []
    from datetime import date
    current = date.today().year
    first = int(httptools.downloadpage('{}/api/anime/advanced-search?page=0&size=1&sort=startDate,asc&sort=id'.format(host)).json[0]['startDate'].split('-')[0]) -1
    for year in range(current, first, -1):
        itemlist.append(item.clone(title = support.typo(year, 'bold'),
                                action= 'submenu_season',
                                variable= year,
                                thumbnail=support.thumb('year')))
    return itemlist


def submenu_top(item):
    itemlist = []
    links = {'Top del giorno':'daily-top', 'Top della settimana':'weekly-top', 'Top del mese':'monthly-top'}
    for label in links:
        link = links[label]
        itemlist.append(item.clone(title = support.typo(label, 'bold'),
                                action= 'submenu_top_of',
                                variable= link))
    return itemlist


def submenu_season(item):
    itemlist = []
    seasons = {'winter':'Inverno', 'spring':'Primavera', 'summer':'Estate', 'fall':'Autunno'}
    url= '{}/api/seasonal-view?page=0&size=36&years={}'.format(host, item.variable)
    js = httptools.downloadpage(url).json[0]['seasonalAnime']
    for season in js:
        s = season['season'].split('.')[-1]
        title = seasons[s]
        itemlist.append(item.clone(title=title,
                                   url = '{}/api/seasonal-view/{}-{}'.format(host, s, item.variable),
                                   thumbnail = support.thumb(s),
                                   action = 'peliculas',
                                   variable=''))
    return itemlist


def submenu_top_of(item):
    itemlist = []
    url= '{}/api/home/{}'.format(host, item.variable)
    js = httptools.downloadpage(url).json
    for anime in js:
        fulltitle = anime['animeTitle']
        title = fulltitle.split('(')[0].strip()
        scrapedlang = scrapertools.find_single_match(fulltitle, r'\(([^\)]+)')
        lang = scrapedlang.upper() if scrapedlang else 'Sub-ITA'
        long_title = support.typo(title, 'bold') + support.typo(lang, '_ [] color kod')

        itemlist.append(item.clone(title=long_title,
                                   url = '{}/anime/{}'.format(host, anime['animeId']),
                                   video_url = '{}/api/anime/{}'.format(host, anime['animeId']),
                                   thumbnail = get_thumbnail(anime, 'animeHorizontalImages'),
                                   action = 'episodios',
                                   variable=anime['animeId']))
    return itemlist


def search(item, texto):
    support.info(texto)
    item.url = host + '/api/anime/advanced-search'
    item.variable = '&query=' + texto

    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def newest(categoria):
    support.info(categoria)
    item = support.Item()
    try:
        if categoria == "anime":
            return latest_added(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


def latest_added(item):
    itemlist = []
    page = item.page if item.page else 0
    url= '{}/api/home/latest-episodes?page={}'.format(host, page)
    js = httptools.downloadpage(url).json

    for episode in js:
        title = episode['title'] if episode['title'] else ''
        animeTitle, lang =  get_lang(episode['animeTitle'])
        quality = 'Full HD' if episode['fullHd'] else 'HD'
        long_title = support.typo('{}. {}{}'.format(int(float(episode['episodeNumber'])), title + ' - ' if title else '', animeTitle), 'bold') + support.typo(lang, '_ [] color kod') + support.typo(quality, '_ [] color kod')
        image = get_thumbnail(episode, 'episodeImages')

        itemlist.append(item.clone(title=long_title,
                                   fulltitle=title,
                                   url='{}/play/{}'.format(host, episode['id']),
                                   contentType = 'episode',
                                   contentTitle = title,
                                   contentSerieName = animeTitle,
                                   contentLanguage = lang,
                                   quality = quality,
                                   contentEpisodeNumber = int(float(episode['episodeNumber'])),
                                   video_url = '{}/api/episode/{}'.format(host, episode['id']),
                                   thumbnail = image,
                                   fanart = image,
                                   action = 'findvideos'))

    if stack()[1][3] not in ['newest']:
        support.nextPage(itemlist, item.clone(page = page + 1))

    return itemlist


def peliculas(item):
    logger.debug()

    itemlist = []
    page = item.page if item.page else 0
    js = httptools.downloadpage('{}?page={}&size={}{}&sort={},{}&sort=id'.format(item.url, page, perpage, item.variable, sort, order)).json

    for it in js:
        logger.debug(jsontools.dump(js))
        title, lang = get_lang(it['title'])

        long_title = support.typo(title, 'bold') + support.typo(lang, '_ [] color kod')

        itemlist.append(item.clone(title = long_title,
                                   fulltitle = title,
                                   show = title,
                                   contentLanguage = lang,
                                   contentType = 'movie' if it['type'] == 'Movie' else 'tvshow',
                                   contentTitle = title,
                                   contentSerieName = title if it['type'] == 'Serie' else '',
                                   action ='findvideos' if it['type'] == 'Movie' else 'episodios',
                                   plot = it['storyline'],
                                   url = '{}/anime/{}'.format(host, it['id']),
                                   video_url = '{}/api/anime/{}'.format(host, it.get('animeId', it.get('id'))),
                                   thumbnail = get_thumbnail(it),
                                   fanart = get_thumbnail(it, 'horizontalImages')))

    autorenumber.start(itemlist)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if len(itemlist) == perpage:
        support.nextPage(itemlist, item.clone(page = page + 1))
    return itemlist


def episodios(item):
    logger.debug()
    itemlist = []
    if not item.video_url:
        item.video_url = item.url.replace('/anime/', '/api/anime/')
    # url = '{}/api/anime/{}'.format(host, item.id)
    json = httptools.downloadpage(item.video_url, CF=False ).json

    if type(json) == list:
        item.show_renumber = False
        itemlist = list_episodes(item, json)

    elif json.get('seasons'):
        seasons = json['seasons']
        seasons.sort(key=lambda s: s['episodeStart'])

        for it in seasons:
            title = it['name']

            itemlist.append(item.clone(title = title,
                                       video_url = '{}/api/anime/{}/season/{}'.format(host, it['animeId'], it['id']),
                                       contentType = 'season',
                                       action = 'list_episodes',
                                       plot = json['storyline'],
                                       year = it['yearStart'],
                                       show_renumber = True))

        # If the call come from the videolibrary or autorenumber, shows the episodes
        if stack()[1][3] in ['add_tvshow', 'get_episodes', 'update', 'find_episodes']:
            itlist = []
            with futures.ThreadPoolExecutor() as executor:
                eplist = []
                for ep in itemlist:
                    ep.show_renumber = False
                    eplist.append(executor.submit(list_episodes, ep))
                for res in futures.as_completed(eplist):
                    if res.result():
                        itlist.extend(res.result())
            itemlist = itlist
    elif json.get('episodes'):
        itemlist = list_episodes(item, json)

    # add renumber option
    if stack()[1][3] not in ['find_episodes'] and itemlist and itemlist[0].contentType == 'episode':
        autorenumber.start(itemlist, item)

    # add add to videolibrary menu
    if stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes']:
        support.videolibrary(itemlist, item)

    return itemlist


def list_episodes(item, json=None):
    itemlist = []

    if not json:
        json = httptools.downloadpage(item.video_url, CF=False ).json

    episodes = json['episodes'] if 'episodes' in json else json
    episodes.sort(key=lambda ep: int(ep['episodeNumber'].split('.')[0]))

    for it in episodes:
        quality = 'Full HD' if it['fullHd'] else 'HD'

        if item.contentSeason:
            episode = '{}x{:02d}'.format(item.contentSeason, int(it['episodeNumber'].split('.')[0]))
        else:
            episode = '{:02d}'.format(int(it['episodeNumber'].split('.')[0]))

        title = support.typo('{}. {}'.format(episode, it['title']), 'bold')
        image = get_thumbnail(it, 'episodeImages')

        itemlist.append(item.clone(title = title,
                                   url= '{}/play/{}'.format(host, it['id']),
                                   video_url= '{}/api/episode/{}'.format(host, it['id']),
                                   contentType = 'episode',
                                   contentEpisodeNumber = int(it['episodeNumber'].split('.')[0]),
                                   contentSeason = item.contentSeason if item.contentSeason else '',
                                   action = 'findvideos',
                                   quality = quality,
                                   thumbnail = image,
                                   fanart= image))

    # Renumber episodes only if shown in the menu
    if item.show_renumber:
        autorenumber.start(itemlist, item)

    return itemlist


def findvideos(item):
    logger.debug()

    res = httptools.downloadpage(item.video_url, CF=False ).json

    if res.get('episodes', []):
        res = httptools.downloadpage('{}/api/episode/{}'.format(host, res['episodes'][0]['id'])).json

    item.url = res['videoUrl']
    item.server = 'directo'

    if '.m3u' in item.url:
        item.manifest = 'hls'

    return support.server(item, itemlist=[item])


def get_thumbnail(data, prop = 'verticalImages', key = 'full'):
    """
    " Returns the vertical image as per given key and prop
    " possibile key values are:
    " - small
    " - full
    " - blurred
    " - medium
    " possibile prop values are:
    " - verticalImages
    " - animeHorizontalImages
    " - animeVerticalImages
    " - horizontalImages
    " - episodeImages
    """
    value = None
    verticalImages = data.get(prop, [])
    if verticalImages:
        first = verticalImages[0]
        if first:
            value = first.get('image' + key.capitalize(), '')
    return value


def get_lang(value):
    title = value.split('(')[0] if value else ''
    scrapedlang = scrapertools.find_single_match(value, r'\(([^\)]+)')
    lang = scrapedlang.upper() if scrapedlang else 'Sub-ITA'
    return title, lang
