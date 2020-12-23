# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Rai Play
# ------------------------------------------------------------

import requests, sys, inspect
from core import support
from platformcode import autorenumber, logger
if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures
current_session = requests.Session()
host = support.config.get_channel_url()
onair = host + '/palinsesto/onAir.json'


@support.menu
def mainlist(item):
    top =  [('Dirette {bold}', ['/dl/RaiPlay/2016/PublishingBlock-9a2ff311-fcf0-4539-8f8f-c4fee2a71d58.html?json', 'live']),
            ('Replay {bold}', ['/dl/RaiPlay/2016/PublishingBlock-9a2ff311-fcf0-4539-8f8f-c4fee2a71d58.html?json', 'replay_menu'])]

    menu = [('Film {bullet bold}', ['/film/index.json', 'menu']),
            ('Serie TV {bullet bold}', ['/serietv/index.json', 'menu']),
            ('Fiction {bullet bold}', ['/fiction/index.json', 'menu']),
            ('Documentari {bullet bold}', ['/documentari/index.json', 'menu']),
            ('Programmi TV{bullet bold}', ['/programmi/index.json', 'menu']),
            ('Programmi per Bambini {bullet bold}', ['/bambini/index.json', 'menu']),
            ('Teen {bullet bold}', ['/teen/index.json', 'learning']),
            ('Learning {bullet bold}', ['/learning/index.json', 'learning']),
            ('Teche Rai {bullet bold storia}', ['/techerai/index.json', 'menu']),
            ('Musica e Teatro {bullet bold}', ['/performing-arts/index.json', 'menu'])
           ]

    search = ''

    return locals()


def menu(item):
    support.info()
    itemlist = [item.clone(title = support.typo('Tutti','bullet bold'), action = 'peliculas'),
                item.clone(title = support.typo('Generi','submenu'), args = 'genre', action = 'submenu'),
                item.clone(title = support.typo('A-Z','submenu'), args = 'az', action = 'submenu'),
                item.clone(title = support.typo('Cerca','submenu'), action = 'search')]

    return support.thumb(itemlist)


def learning(item):
    support.info()
    itemlist =[]
    json = current_session.get(item.url).json()['contents']
    for key in json:
        itemlist.append(item.clone(title = support.typo(key['name'],'bold'), fulltitle = key['name'],
                                   show = key['name'], url = key['contents'], action = 'peliculas'))
    return itemlist


def submenu(item):
    support.info()
    itemlist = []
    json = current_session.get(item.url).json()['contents'][-1]['contents']
    if item.args == 'az':
        json_url = getUrl(json[-1]['path_id'])
        json = current_session.get(json_url).json()['contents']
        for key in json:
            itemlist.append(item.clone(title = support.typo(key,'bold'), fulltitle = key,
                                       show = key, url = json[key], action = 'peliculas'))
    else:
        for key in json:
            itemlist.append(item.clone(title = support.typo(key['name'],'bold'), fulltitle = key['name'], show = key['name'],
                                       thumbnail = getUrl(key['image']), url = getUrl(key['path_id']), action = 'peliculas'))
        itemlist.pop(-1)
    return support.thumb(itemlist)


def replay_menu(item):
    support.info()
    import datetime, xbmc

    # create day and month list
    days = []
    months = []
    days.append(xbmc.getLocalizedString(17))
    for day in range(11, 17): days.append(xbmc.getLocalizedString(day))
    for month in range(21, 33): months.append(xbmc.getLocalizedString(month))

    # make menu
    itemlist = []
    today = datetime.date.today()
    for d in range(7):
        day = today - datetime.timedelta(days=d)
        support.info(day)
        itemlist.append(item.clone(action = 'replay_channels', date = day.strftime("%d-%m-%Y"),
                                   title = support.typo(days[int(day.strftime("%w"))] + " " + day.strftime("%d") + " " + months[int(day.strftime("%m"))-1], 'bold')))
    return itemlist


def replay_channels(item):
    support.info()
    itemlist = []
    json = current_session.get(item.url).json()['dirette']
    for key in json:
        itemlist.append(item.clone(title = support.typo(key['channel'], 'bold'), fulltitle = key['channel'], show = key['channel'], plot = item.title, action = 'replay',
                                   thumbnail = key['transparent-icon'].replace("[RESOLUTION]", "256x-"), url = '%s/palinsesto/app/old/%s/%s.json' % (host, key['channel'].lower().replace(' ','-'), item.date)))
    return itemlist


def replay(item):
    support.info()
    itemlist = []
    json = current_session.get(item.url).json()[item.fulltitle][0]['palinsesto'][0]['programmi']
    for key in json:
        support.info('KEY=',key)
        if key and key['pathID']: itemlist.append(item.clone(thumbnail = getUrl(key['images']['landscape']), fanart = getUrl(key['images']['landscape']), url = getUrl(key['pathID']), fulltitle = key['name'], show = key['name'],
                                                             title = support.typo(key['timePublished'], 'color kod bold') + support.typo(' | ' + key['name'], ' bold'), plot = key['testoBreve'], action = 'findvideos'))
    return itemlist

def search(item, text):
    support.info()
    itemlist =[]
    try:
        if item.url != host:
            item.search = text
            itemlist = peliculas(item)
        else:
            json = current_session.get(host + '/dl/RaiTV/RaiPlayMobile/Prod/Config/programmiAZ-elenco.json').json()
            for key in json:
                for key in json[key]:
                    if 'PathID' in key and (text.lower() in key['name'].lower()):
                        itemlist.append(item.clone(title = support.typo(key['name'],'bold'), fulltitle = key['name'], show = key['name'], url = key['PathID'].replace('/?json', '.json'), action = 'Type',
                                                   thumbnail = getUrl(key['images']['portrait'] if 'portrait' in key['images'] else key['images']['portrait43'] if 'portrait43' in key['images'] else key['images']['landscape']),
                                                   fanart = getUrl(key['images']['landscape'] if 'landscape' in key['images'] else key['images']['landscape43'])))
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []
    return itemlist


def Type(item):
    logger.debug(item.url)
    json = current_session.get(item.url).json()
    if json['program_info']['layout'] == 'single':
        item.contentTitle = item.fulltitle
        item.contentType = 'movie'
        return findvideos(item)
    else:
        item.contentType = 'tvshow'
        return select(item)


def live(item):
    support.info()
    itemlist =[]
    info={}
    json = current_session.get(item.url).json()['dirette']
    onAir = current_session.get(onair).json()['on_air']
    support.info(onAir)
    for key in onAir:
        channel = key['channel']
        info[channel] = {}
        info[channel]['fanart'] = getUrl(key['currentItem']['image'])
        info[channel]['plot'] = support.typo(key['currentItem']['name'],'bold')+ '\n\n' + key['currentItem']['description']

    for i, key in enumerate(json):
        channel = key['channel']
        itemlist.append(item.clone(title = support.typo(channel, 'bold'), fulltitle = channel, show = channel, url = key['video']['contentUrl'],
                                   thumbnail = key['transparent-icon'].replace("[RESOLUTION]", "256x-"), forcethumb = True , fanart = info[channel]['fanart'],
                                   plot = info[channel]['plot'], action = 'play', no_return=True))
    return support.thumb(itemlist, live=True)


def peliculas(item):
    support.info()
    itemlist = []
    keys = []
    key_list = []

    # pagination options
    pag = item.page if item.page else 1
    pagination = 40 if not item.search else ''

    # load json
    if type(item.url) in [dict, list]:
        json = item.url
        for key in json:
            if item.search.lower() in key['name'].lower():
                keys.append(key)
    else:
        json = current_session.get(item.url).json()

        # load json for main menu item
        if not item.args:
            json_url = getUrl(json['contents'][-1]['contents'][-1]['path_id'])
            json = current_session.get(json_url).json()['contents']
        else:
            json = json['contents']
        for key in json:
            if len(json[key]) > 0:
                for key in json[key]:
                    keys.append(key)

    # load titles
    for i, key in enumerate(keys):
        if pagination and (pag - 1) * pagination > i: continue  # pagination
        if pagination and i >= pag * pagination: break 
        key_list.append(key)

    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(addinfo, key, item) for key in key_list]
        for res in futures.as_completed(itlist):
            if res.result():
                itemlist.append(res.result())
    itemlist = sorted(itemlist, key=lambda it: it.title)

    if len(keys) > pag * pagination and not item.search:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), page=pag + 1, thumbnail=support.thumb()))
    return itemlist


def select(item):
    support.info()
    itemlist = []
    # support.dbg()
    if type(item.url) in [list, dict]:
        json = item.url
    else:
        json = current_session.get(item.url).json()
    if 'blocks' in json:
        json = json['blocks']
        season = ''
        for key in json:
            if item.fulltitle in key['name']: season = key['name'].replace(item.fulltitle, '').strip()
            if not season.isdigit(): season = ''
            itemlist.append(item.clone(title = support.typo(key['name'],'bold'), season = season, url = key['sets'], action = 'select'))
        if len(itemlist) == 1:
            return select(itemlist[0])
    else:
        for key in item.url:
            itemlist.append(item.clone(title = support.typo(key['name'], 'bold'), data = getUrl(key['path_id']), url = getUrl(key['path_id']), contentType = 'tvshow', action = 'episodios'))
        if len(itemlist) == 1:
            return episodios(itemlist[0])
    return itemlist


def episodios(item):
    support.info()
    itemlist = []
    if type(item.url) in [list, dict] and len(item.url) > 1 and ('name' in item.url[0] and 'stagione' not in item.url[0]['name'].lower()):
        for key in item.url:
            itemlist.append(item.clone(title = support.typo(key['name'], 'bold'), url = getUrl(key['path_id']), contentType = 'tvshow', action = 'episodios'))

    elif type(item.url) in [list, dict]:
        for key in item.url:
            load_episodes(key, item)
        with futures.ThreadPoolExecutor() as executor:
            itlist = [executor.submit(load_episodes, key, item) for key in item.url]
            for res in futures.as_completed(itlist):
                if res.result():
                    itemlist += res.result()
        if itemlist and itemlist[0].VL:
            # itemlist.reverse()
            itemlist = sorted(itemlist, key=lambda it: it.order)
            item.action = 'episodios'
            support.videolibrary(itemlist, item)
        else:
            itemlist = sorted(itemlist, key=lambda it: it.title)

    else:
        date = ''
        if type(item.url) in [list, dict]: item.url = getUrl(item.url[0]['path_id'])
        json = current_session.get(item.url).json()['items']
        for key in json:
            ep = support.match(key['subtitle'], patron=r'(?:St\s*(\d+))?\s*Ep\s*(\d+)').match
            if ep:
                season = '1' if not ep[0] else ep[0]
                episode = ep[1].zfill(2)
                title = support.re.sub(r'(?:St\s*\d+)?\s*Ep\s*\d+','',key['subtitle'])
                title = season + 'x' + episode + (' - ' + title if not title.startswith(' ') else title if title else '')
            elif item.season and support.match(item.title.lower(), patron =r'(puntate)').match:
                title = key['subtitle'].strip()
                if not title: title = key['name']
                date = support.match(title, patron=r'(\d+/\d+/\d+)').match
                if date:
                    date = title.split('/')
                    date = date[2][-2] + '/' + date[1] + '/' + date[0]

            else:
                title = key['subtitle'].strip()
            if not title:
                title = key['name']
            itemlist.append(item.clone(title = support.typo(title, 'bold'), action = 'findvideos', VL=True if ep else False, plot = key['description'],
                                       fanart = getUrl(key['images']['landscape']), url = key['video_url'], contentType = 'episode', date=date))

        if item.season and support.match(item.title.lower(), patron =r'(puntate)').match:
            itemlist = sorted(itemlist, key=lambda it: it.date)
            for i, it in enumerate(itemlist):
                episode = str(i + 1)
                it.title = support.typo(item.season + 'x' + episode, 'bold') + (' - ' + it.title)

        if itemlist and itemlist[0].VL: support.videolibrary(itemlist, item)

    if itemlist and not support.match(itemlist[0].title, patron=r'[Ss]?(\d+)(?:x|_|\.|\s+)[Ee]?[Pp]?(\d+)').match and inspect.stack()[1][3] not in ['find_episodes']:
        autorenumber.start(itemlist, item)
    return itemlist


def findvideos(item):
    support.info()
    itemlist = []
    if item.url.endswith('json'):
        json = current_session.get(item.url).json()

        if 'first_item_path' in json:
            url = current_session.get(getUrl(json['first_item_path'])).json()['video']['content_url']
        else:
            url = json['video']['content_url']
    else:
        url = item.url

    itemlist.append(item.clone(server = 'directo', title = support.config.get_localized_string(30137), fanart = item.json, url = getUrl(url), action = 'play' ))
    return support.server(item, itemlist=itemlist, Download=False)


def getUrl(pathId):
    support.info()
    url = pathId.replace(" ", "%20")
    if url.startswith("/raiplay/"):
        url = url.replace("/raiplay/",host +'/')

    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = host + url

    # fix format of url for json
    if url.endswith(".html?json"):
        url = url.replace(".html?json", ".json")
    elif url.endswith("/?json"):
        url = url.replace("/?json","/index.json")
    elif url.endswith("?json"):
        url = url.replace("?json",".json")

    return url


def addinfo(key, item):
    support.info()
    info = current_session.get(getUrl(key['info_url'])).json()
    if not item.search or item.search.lower() in key['name'].lower():
        it = item.clone(title = support.typo(key['name'],'bold'), fulltitle = key['name'], show = key['name'],
                        thumbnail = getUrl(key['images']['portrait_logo'] if key['images']['portrait_logo'] else key['images']['landscape']),
                        fanart = getUrl(key['images']['landscape']), url = getUrl(key['path_id']), plot = info['description'])
        if 'layout' not in key or key['layout'] == 'single':
            it.action = 'findvideos'
            it.contentType = 'movie'
            it.contentTitle = it.fulltitle
        else:
            it.action = 'select'
            it.contentType = 'tvshow'
            it.contentSerieName = it.fulltitle
        return it


def load_episodes(key, item):
    support.info()
    itemlist = []
    json = current_session.get(getUrl(key['path_id'])).json()['items']
    order = 0
    for key in json:
        ep = support.match(key['subtitle'], patron=r'(?:St\s*(\d+))?\s*Ep\s*(\d+)').match
        if ep:
            season = '1' if not ep[0] else ep[0]
            episode = ep[1].zfill(2)
            title = season + 'x' + episode + support.re.sub(r'(?:St\s*\d+)?\s*Ep\s*\d+','',key['subtitle'])
            order = int(season + episode)
        else:
            title = key['subtitle'].strip()
        if not title:
            title = key['name']

        itemlist.append(item.clone(title = support.typo(title, 'bold'), url = key['video_url'], contentType = 'episode',
                                   fanart = getUrl(key['images']['landscape']), plot = key['description'],
                                   action = 'findvideos', VL=True if ep else False, order=order))
    return itemlist


