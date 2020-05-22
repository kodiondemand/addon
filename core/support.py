# -*- coding: utf-8 -*-
# -----------------------------------------------------------
# support functions that are needed by many channels, to no repeat the same code
import base64
import inspect
import os
import re
import sys

from lib.guessit import guessit

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
if PY3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

try:
    import urllib.request as urllib
    import urllib.parse as urlparse
    from urllib.parse import urlencode
except ImportError:
    import urllib, urlparse
    from urllib import urlencode

from channelselector import thumb
from core import httptools, scrapertools, servertools, tmdb, channeltools
from core.item import Item
from lib import unshortenit
from platformcode import logger, config
from specials import autoplay

def hdpass_get_servers(item):
    def get_hosts(url, quality):
        ret = []
        page = httptools.downloadpage(url, CF=False).data
        mir = scrapertools.find_single_match(page, patron_mir)

        for mir_url, srv in scrapertools.find_multiple_matches(mir, patron_option):
            mir_url = scrapertools.decodeHtmlentities(mir_url)
            log(mir_url)
            it = Item(channel=item.channel,
                            action="play",
                            fulltitle=item.fulltitle,
                            quality=quality,
                            show=item.show,
                            thumbnail=item.thumbnail,
                            contentType=item.contentType,
                            title=srv,
                            server=srv,
                            url= mir_url)
            if not servertools.get_server_parameters(srv.lower()):  # do not exists or it's empty
                it = hdpass_get_url(it)[0]
            ret.append(it)
        return ret
    # Carica la pagina
    itemlist = []
    if 'hdpass' in item.url or 'hdplayer' in item.url:
        url = item.url
    else:
        data = httptools.downloadpage(item.url, CF=False).data.replace('\n', '')
        patron = r'<iframe(?: id="[^"]+")? width="[^"]+" height="[^"]+" src="([^"]+)"[^>]+><\/iframe>'
        url = scrapertools.find_single_match(data, patron)
        url = url.replace("&download=1", "")
        if 'hdpass' not in url and 'hdplayer' not in url:
            return itemlist
    if not url.startswith('http'):
        url = 'https:' + url

    data = httptools.downloadpage(url, CF=False).data
    patron_res = '<div class="buttons-bar resolutions-bar">(.*?)<div class="buttons-bar'
    patron_mir = '<div class="buttons-bar hosts-bar">(.*?)<div id="fake'
    patron_option = r'<a href="([^"]+?)".*?>([^<]+?)</a>'

    res = scrapertools.find_single_match(data, patron_res)

    with futures.ThreadPoolExecutor() as executor:
        thL = []
        for res_url, res_video in scrapertools.find_multiple_matches(res, patron_option):
            res_url = scrapertools.decodeHtmlentities(res_url)
            thL.append(executor.submit(get_hosts, res_url, res_video))
        for res in futures.as_completed(thL):
            if res.result():
                itemlist.extend(res.result())
    return server(item, itemlist=itemlist)

def hdpass_get_url(item):
    patron_media = r'<iframe allowfullscreen custom-src="([^"]+)'
    data = httptools.downloadpage(item.url, CF=False).data
    item.url = base64.b64decode(scrapertools.find_single_match(data, patron_media))
    return [item]

def color(text, color):
    return "[COLOR " + color + "]" + text + "[/COLOR]"


def search(channel, item, texto):
    log(item.url + " search " + texto)
    if 'findhost' in dir(channel):
        channel.findhost()
    item.url = channel.host + "/?s=" + texto
    try:
        return channel.peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
    return []


def dbg():
    if config.dev_mode():
        import web_pdb;
        if not web_pdb.WebPdb.active_instance:
            import webbrowser
            webbrowser.open('http://127.0.0.1:5555')
        web_pdb.set_trace()


def regexDbg(item, patron, headers, data=''):
    if config.dev_mode():
        import json, urllib2, webbrowser
        url = 'https://regex101.com'

        if not data:
            html = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data.replace("'", '"')
            html = re.sub('\n|\t', ' ', html)
        else:
            html = data
        headers = {'content-type': 'application/json'}
        data = {
            'regex': patron.decode('utf-8'),
            'flags': 'gm',
            'testString': html.decode('utf-8'),
            'delimiter': '"""',
            'flavor': 'python'
        }
        r = urllib2.Request(url + '/api/regex', json.dumps(data, encoding='latin1'), headers=headers)
        r = urllib2.urlopen(r).read()
        permaLink = json.loads(r)['permalinkFragment']
        webbrowser.open(url + "/r/" + permaLink)


def scrapeLang(scraped, lang, longtitle):
    ##    Aggiunto/modificato per gestire i siti che hanno i video
    ##    in ita e subita delle serie tv nella stessa pagina
    # altrimenti dopo un sub-ita mette tutti quelli a seguire in sub-ita
    # e credo sia utile per filtertools
    language = ''

    if scraped['lang']:
        if 'ita' in scraped['lang'].lower():
            language = 'ITA'
        if 'sub' in scraped['lang'].lower():
            language = 'Sub-' + language

    if not language: language = lang
    if language: longtitle += typo(language, '_ [] color kod')
    return language, longtitle

def cleantitle(title):
    if type(title) != str: title.decode('UTF-8')
    title = scrapertools.decodeHtmlentities(title)
    cleantitle = title.replace('"', "'").replace('×', 'x').replace('–', '-').strip()
    return cleantitle

def scrapeBlock(item, args, block, patron, headers, action, pagination, debug, typeContentDict, typeActionDict, blacklist, search, pag, function, lang, sceneTitle):
    itemlist = []
    log("scrapeBlock qui")
    if debug:
        regexDbg(item, patron, headers, block)
    matches = scrapertools.find_multiple_matches_groups(block, patron)
    log('MATCHES =', matches)

    known_keys = ['url', 'title', 'title2', 'season', 'episode', 'thumb', 'quality', 'year', 'plot', 'duration', 'genere', 'rating', 'type', 'lang', 'other', 'size', 'seed']
    # Legenda known_keys per i groups nei patron
    # known_keys = ['url', 'title', 'title2', 'season', 'episode', 'thumb', 'quality',
    #                'year', 'plot', 'duration', 'genere', 'rating', 'type', 'lang']
    # url = link relativo o assoluto alla pagina titolo film/serie
    # title = titolo Film/Serie/Anime/Altro
    # title2 = titolo dell'episodio Serie/Anime/Altro
    # season = stagione in formato numerico
    # episode = numero episodio, in formato numerico.
    # thumb = linkrealtivo o assoluto alla locandina Film/Serie/Anime/Altro
    # quality = qualità indicata del video
    # year = anno in formato numerico (4 cifre)
    # duration = durata del Film/Serie/Anime/Altro
    # genere = genere del Film/Serie/Anime/Altro. Es: avventura, commedia
    # rating = punteggio/voto in formato numerico
    # type = tipo del video. Es. movie per film o tvshow per le serie. Di solito sono discrimanti usati dal sito
    # lang = lingua del video. Es: ITA, Sub-ITA, Sub, SUB ITA.
    # AVVERTENZE: Se il titolo è trovato nella ricerca TMDB/TVDB/Altro allora le locandine e altre info non saranno quelle recuperate nel sito.!!!!

    stagione = '' # per quei siti che hanno la stagione nel blocco ma non nelle puntate
    for i, match in enumerate(matches):
        if pagination and (pag - 1) * pagination > i and not search: continue  # pagination
        if pagination and i >= pag * pagination and not search: break          # pagination
        # listGroups = match.keys()
        # match = match.values()

        # if len(listGroups) > len(match):  # to fix a bug
        #     match = list(match)
        #     match.extend([''] * (len(listGroups) - len(match)))

        scraped = {}
        for kk in known_keys:
            val = match[kk] if kk in match else ''
            # val = match[listGroups.index(kk)] if kk in listGroups else ''
            if val and (kk == "url" or kk == 'thumb') and 'http' not in val:
                val = scrapertools.find_single_match(item.url, 'https?://[a-z0-9.-]+') + (val if val.startswith('/') else '/' + val)
            scraped[kk] = val

        if scraped['season']:
            stagione = scraped['season']
            item.infoLabels['season'] = int(scraped['season'])
            item.infoLabels['episode'] = int(scraped['episode'])
            episode = str(int(scraped['season'])) +'x'+ str(int(scraped['episode'])).zfill(2)
        elif item.season:
            item.infoLabels['season'] = int(item.season)
            item.infoLabels['episode'] = int(scrapertools.find_single_match(scraped['episode'], r'(\d+)'))
            episode = item.season +'x'+ scraped['episode']
        elif item.contentType == 'tvshow' and (scraped['episode'] == '' and scraped['season'] == '' and stagione == ''):
            item.news = 'season_completed'
            episode = ''
        else:
            episode = re.sub(r'\s-\s|-|x|&#8211|&#215;|×', 'x', scraped['episode']) if scraped['episode'] else ''
            if 'x' in episode:
                ep = episode.split('x')
                episode = str(int(ep[0])).zfill(1) + 'x' + str(int(ep[1])).zfill(2)
                item.infoLabels['season'] = int(ep[0])
                item.infoLabels['episode'] = int(ep[1])
            second_episode = scrapertools.find_single_match(episode, r'x\d+x(\d+)')
            if second_episode: episode = re.sub(r'(\d+x\d+)x\d+',r'\1-', episode) + second_episode.zfill(2)

        #episode = re.sub(r'\s-\s|-|x|&#8211|&#215;', 'x', scraped['episode']) if scraped['episode'] else ''
        title = cleantitle(scraped['title']) if scraped['title'] else ''
        title2 = cleantitle(scraped['title2']) if scraped['title2'] else ''
        quality = scraped['quality'].strip() if scraped['quality'] else ''
        Type = scraped['type'] if scraped['type'] else ''
        plot = cleantitle(scraped["plot"]) if scraped["plot"] else ''

        # if title is set, probably this is a list of episodes or video sources
        # necessaria l'aggiunta di == scraped["title"] altrimenti non prende i gruppi dopo le categorie
        if item.infoLabels["title"] == scraped["title"]:
            infolabels = item.infoLabels
        else:
            if function == 'episodios':
                infolabels = item.infoLabels
            else:
                infolabels = {}
            if scraped['year']:
                infolabels['year'] = scraped['year']
            if scraped["plot"]:
                infolabels['plot'] = plot
            if scraped['duration']:
                matches = scrapertools.find_multiple_matches(scraped['duration'],r'([0-9])\s*?(?:[hH]|:|\.|,|\\|\/|\||\s)\s*?([0-9]+)')
                for h, m in matches:
                    scraped['duration'] = int(h) * 60 + int(m)
                if not matches:
                    scraped['duration'] = scrapertools.find_single_match(scraped['duration'], r'(\d+)')
                infolabels['duration'] = int(scraped['duration']) * 60
            if scraped['genere']:
                genres = scrapertools.find_multiple_matches(scraped['genere'], '[A-Za-z]+')
                infolabels['genere'] = ", ".join(genres)
            if scraped["rating"]:
                infolabels['rating'] = scrapertools.decodeHtmlentities(scraped["rating"])

        # make formatted Title [longtitle]
        s = ' - '
        title = episode + (s if episode and title else '') + title
        longtitle = title + (s if title and title2 else '') + title2 + '\n'

        if sceneTitle:
            try:
                parsedTitle = guessit(title)
                title = longtitle = parsedTitle.get('title', '')
                log('TITOLO',title)
                if parsedTitle.get('source'):
                    quality = str(parsedTitle.get('source'))
                    if parsedTitle.get('screen_size'):
                        quality += ' ' + str(parsedTitle.get('screen_size', ''))
                if not scraped['year']:
                    infolabels['year'] = parsedTitle.get('year', '')
                if parsedTitle.get('episode') and parsedTitle.get('season'):
                    longtitle = title + s

                    if type(parsedTitle.get('season')) == list:
                        longtitle += str(parsedTitle.get('season')[0]) + '-' + str(parsedTitle.get('season')[-1])
                    else:
                        longtitle += str(parsedTitle.get('season'))

                    if type(parsedTitle.get('episode')) == list:
                        longtitle += 'x' + str(parsedTitle.get('episode')[0]).zfill(2) + '-' + str(parsedTitle.get('episode')[-1]).zfill(2)
                    else:
                        longtitle += 'x' + str(parsedTitle.get('episode')).zfill(2)
                elif parsedTitle.get('season') and type(parsedTitle.get('season')) == list:
                    longtitle += s + config.get_localized_string(30140) + " " +str(parsedTitle.get('season')[0]) + '-' + str(parsedTitle.get('season')[-1])
                elif parsedTitle.get('season'):
                    longtitle += s + config.get_localized_string(60027) % str(parsedTitle.get('season'))
                if parsedTitle.get('episode_title'):
                    longtitle += s + parsedTitle.get('episode_title')
            except:
                log('Error')

        longtitle = typo(longtitle, 'bold')
        lang1, longtitle = scrapeLang(scraped, lang, longtitle)
        longtitle += typo(quality, '_ [] color kod') if quality else ''
        longtitle += typo(scraped['size'], '_ [] color kod') if scraped['size'] else ''
        longtitle += typo(scraped['seed'] + ' SEEDS', '_ [] color kod') if scraped['seed'] else ''

        AC = CT = ''
        if typeContentDict:
            for name, variants in typeContentDict.items():
                if str(scraped['type']).lower() in variants:
                    CT = name
                    break
                else: CT = item.contentType
        if typeActionDict:
            for name, variants in typeActionDict.items():
                if str(scraped['type']).lower() in variants:
                    AC = name
                    break
                else: AC = action
        if (scraped["title"] not in blacklist) and (search.lower() in longtitle.lower()):
            it = Item(
                channel=item.channel,
                action=AC if AC else action,
                contentType='episode' if function == 'episodios' else CT if CT else item.contentType,
                title=longtitle,
                fulltitle=item.fulltitle if function == 'episodios' else title,
                show=item.show if function == 'episodios' else title,
                quality=quality,
                url=scraped["url"],
                infoLabels=infolabels,
                thumbnail=item.thumbnail if function == 'episodios' or not scraped["thumb"] else scraped["thumb"],
                args=item.args,
                contentSerieName= item.contentSerieName if item.contentSerieName and function == 'peliculas' else title if 'movie' not in [item.contentType, CT] and function == 'episodios' else item.fulltitle,
                contentTitle=item.contentTitle if item.contentTitle and function == 'peliculas' else title if 'movie' in [item.contentType, CT] and function == 'peliculas' else '',
                contentLanguage = lang1,
                contentEpisodeNumber=episode if episode else '',
                news= item.news if item.news else '',
                other = scraped['other'] if scraped['other'] else ''
            )

            # for lg in list(set(listGroups).difference(known_keys)):
            #     it.__setattr__(lg, match[listGroups.index(lg)])
            for lg in list(set(match.keys()).difference(known_keys)):
                it.__setattr__(lg, match[lg])

            if 'itemHook' in args:
                it = args['itemHook'](it)
            itemlist.append(it)

    return itemlist, matches


def scrape(func):
    # args is a dict containing the foolowing keys:
    # patron: the patron to use for scraping page, all capturing group must match with listGroups
    # listGroups: a list containing the scraping info obtained by your patron, in order
    # accepted values are: url, title, thumb, quality, year, plot, duration, genre, rating, episode, lang

    # headers: values to pass to request header
    # blacklist: titles that you want to exclude(service articles for example)
    # data: if you want to pass data manually, maybe because you need some custom replacement
    # patronBlock: patron to get parts of the page (to scrape with patron attribute),
    #               if you need a "block inside another block" you can create a list, please note that all matches
    #               will be packed as string
    # patronNext: patron for scraping next page link
    # action: if you want results perform an action different from "findvideos", useful when scraping film by genres
    # addVideolibrary: if "add to videolibrary" should appear
    # example usage:
    #   import support
    #   itemlist = []
    #   patron = 'blablabla'
    #   headers = [['Referer', host]]
    #   blacklist = 'Request a TV serie!'
    #   return support.scrape(item, itemlist, patron, ['thumb', 'quality', 'url', 'title', 'year', 'plot', 'episode', 'lang'],
    #                           headers=headers, blacklist=blacklist)
    # 'type' is a check for typologies of content e.g. Film or TV Series
    # 'episode' is a key to grab episode numbers if it is separated from the title
    # IMPORTANT 'type' is a special key, to work need typeContentDict={} and typeActionDict={}

    def wrapper(*args):
        itemlist = []

        args = func(*args)
        function = func.__name__ if not 'actLike' in args else args['actLike']
        # log('STACK= ',inspect.stack()[1][3])

        item = args['item']

        action = args['action'] if 'action' in args else 'findvideos'
        anime = args['anime'] if 'anime' in args else ''
        addVideolibrary = args['addVideolibrary'] if 'addVideolibrary' in args else True
        search = args['search'] if 'search' in args else ''
        blacklist = args['blacklist'] if 'blacklist' in args else []
        data = args['data'] if 'data' in args else ''
        patron = args['patron'] if 'patron' in args else args['patronMenu'] if 'patronMenu' in args else ''
        if 'headers' in args:
            headers = args['headers']
        elif 'headers' in func.__globals__:
            headers = func.__globals__['headers']
        else:
            headers = ''
        patronNext = args['patronNext'] if 'patronNext' in args else ''
        patronBlock = args['patronBlock'] if 'patronBlock' in args else ''
        typeActionDict = args['typeActionDict'] if 'typeActionDict' in args else {}
        typeContentDict = args['typeContentDict'] if 'typeContentDict' in args else {}
        debug = args['debug'] if 'debug' in args else False
        debugBlock = args['debugBlock'] if 'debugBlock' in args else False
        if 'pagination' in args and inspect.stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes']: pagination = args['pagination'] if args['pagination'] else 20
        else: pagination = ''
        lang = args['deflang'] if 'deflang' in args else ''
        sceneTitle = args.get('sceneTitle')
        pag = item.page if item.page else 1  # pagination
        matches = []

        for n in range(2):
            log('PATRON= ', patron)
            if not data:
                page = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True)
                data = page.data.replace("'", '"')
                data = re.sub('\n|\t', ' ', data)
                data = re.sub(r'>\s+<', '> <', data)
                # replace all ' with " and eliminate newline, so we don't need to worry about

            if patronBlock:
                if debugBlock:
                    regexDbg(item, patronBlock, headers, data)
                blocks = scrapertools.find_multiple_matches_groups(data, patronBlock)
                block = ""
                for bl in blocks:
                    # log(len(blocks),bl)
                    if 'season' in bl and bl['season']:
                        item.season = bl['season']
                    blockItemlist, blockMatches = scrapeBlock(item, args, bl['block'], patron, headers, action, pagination, debug,
                                                typeContentDict, typeActionDict, blacklist, search, pag, function, lang, sceneTitle)
                    for it in blockItemlist:
                        if 'lang' in bl:
                            it.contentLanguage, it.title = scrapeLang(bl, it.contentLanguage, it.title)
                        if 'quality' in bl and bl['quality']:
                            it.quality = bl['quality'].strip()
                            it.title = it.title + typo(bl['quality'].strip(), '_ [] color kod')
                    itemlist.extend(blockItemlist)
                    matches.extend(blockMatches)
            elif patron:
                itemlist, matches = scrapeBlock(item, args, data, patron, headers, action, pagination, debug, typeContentDict,
                                       typeActionDict, blacklist, search, pag, function, lang, sceneTitle)

            if 'itemlistHook' in args:
                itemlist = args['itemlistHook'](itemlist)

            # if url may be changed and channel has findhost to update
            if 'findhost' in func.__globals__ and not itemlist:
                logger.info('running findhost ' + func.__module__)
                host = func.__globals__['findhost']()
                parse = list(urlparse.urlparse(item.url))
                from core import jsontools
                jsontools.update_node(host, func.__module__.split('.')[-1], 'url')
                parse[1] = scrapertools.get_domain_from_url(host)
                item.url = urlparse.urlunparse(parse)
                data = None
                itemlist = []
                matches = []
            else:
                break


        if (pagination and len(matches) <= pag * pagination) or not pagination: # next page with pagination
            if patronNext and inspect.stack()[1][3] != 'newest':
                nextPage(itemlist, item, data, patronNext, function)

        # next page for pagination
        if pagination and len(matches) > pag * pagination and not search:
            if inspect.stack()[1][3] not in ['newest','get_newest']:
                itemlist.append(
                    Item(channel=item.channel,
                         action = item.action,
                         contentType=item.contentType,
                         title=typo(config.get_localized_string(30992), 'color kod bold'),
                         fulltitle= item.fulltitle,
                         show= item.show,
                         url=item.url,
                         args=item.args,
                         page=pag + 1,
                         thumbnail=thumb()))

        if action != 'play' and function != 'episodios' and 'patronMenu' not in args and item.contentType in ['movie', 'tvshow', 'episode']:
            tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        from specials import autorenumber
        if anime:
            if function == 'episodios' or item.action == 'episodios': autorenumber.renumber(itemlist, item, 'bold')
            else: autorenumber.renumber(itemlist)
        # if anime and autorenumber.check(item) == False and len(itemlist)>0 and not scrapertools.find_single_match(itemlist[0].title, r'(\d+.\d+)'):
        #     pass
        # else:
        if addVideolibrary and (item.infoLabels["title"] or item.fulltitle):
            # item.fulltitle = item.infoLabels["title"]
            videolibrary(itemlist, item, function=function)
        if function == 'episodios' or function == 'findvideos':
            download(itemlist, item, function=function)

        if 'patronMenu' in args and itemlist:
            itemlist = thumb(itemlist, genre=True)

        if 'fullItemlistHook' in args:
            itemlist = args['fullItemlistHook'](itemlist)

        # itemlist = filterLang(item, itemlist)   # causa problemi a newest

        if config.get_setting('trakt_sync'):
            from core import trakt_tools
            trakt_tools.trakt_check(itemlist)

        return itemlist

    return wrapper


def dooplay_get_links(item, host):
    # get links from websites using dooplay theme and dooplay_player
    # return a list of dict containing these values: url, title and server

    data = httptools.downloadpage(item.url).data.replace("'", '"')
    patron = r'<li id="player-option-[0-9]".*?data-type="([^"]+)" data-post="([^"]+)" data-nume="([^"]+)".*?<span class="title".*?>([^<>]+)</span>(?:<span class="server">([^<>]+))?'
    matches = scrapertools.find_multiple_matches(data, patron)

    ret = []

    for type, post, nume, title, server in matches:
        postData = urlencode({
            "action": "doo_player_ajax",
            "post": post,
            "nume": nume,
            "type": type
        })
        dataAdmin = httptools.downloadpage(host + '/wp-admin/admin-ajax.php', post=postData,headers={'Referer': item.url}).data
        link = scrapertools.find_single_match(dataAdmin, "<iframe.*src='([^']+)'")
        ret.append({
            'url': link,
            'title': title,
            'server': server
        })

    return ret


@scrape
def dooplay_get_episodes(item):
    item.contentType = 'tvshow'
    patron = '<li class="mark-[0-9]+">.*?<img.*?(?:data-lazy-)?src="(?P<thumb>[^"]+).*?(?P<episode>[0-9]+ - [0-9]+).*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+).*?(?P<year>[0-9]{4})'
    actLike = 'episodios'

    return locals()


@scrape
def dooplay_peliculas(item, mixed=False, blacklist=""):
    actLike = 'peliculas'
    if item.args == 'searchPage':
        return dooplay_search_vars(item, blacklist)
    else:
        if item.contentType == 'movie':
            action = 'findvideos'
            patron = '<article id="post-[0-9]+" class="item movies">.*?<img src="(?!data)(?P<thumb>[^"]+)".*?<span class="quality">(?P<quality>[^<>]+).*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></h3>.*?(?:<span>[^<>]*(?P<year>[0-9]{4})</span>|</article>)'
        else:
            action = 'episodios'
            patron = '<article id="post-[0-9]+" class="item (?P<type>' + ('\w+' if mixed else 'tvshows') + ')">.*?<img src="(?!data)(?P<thumb>[^"]+)".*?(?:<span class="quality">(?P<quality>[^<>]+))?.*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></h3>.*?(?:<span>(?P<year>[0-9]{4})</span>|</article>).*?(?:<div class="texto">(?P<plot>[^<>]+)|</article>).*?(?:genres">(?P<genre>.*?)</div>|</article>)'
        patronNext = '<div class="pagination">.*?class="current".*?<a href="([^"]+)".*?<div class="resppages">'
        addVideolibrary = False

        if mixed:
            typeActionDict={'findvideos': ['movies'], 'episodios': ['tvshows']}
            typeContentDict={'film': ['movies'], 'serie': ['tvshows']}

        return locals()


@scrape
def dooplay_search(item, blacklist=""):
    return dooplay_search_vars(item, blacklist)


def dooplay_search_vars(item, blacklist):
    if item.contentType == 'list':  # ricerca globale
        type = '(?P<type>movies|tvshows)'
        typeActionDict = {'findvideos': ['movies'], 'episodios': ['tvshows']}
        typeContentDict = {'movie': ['movies'], 'tvshow': ['tvshows']}
    elif item.contentType == 'movie':
        type = 'movies'
        action = 'findvideos'
    else:
        type = 'tvshows'
        action = 'episodios'
    patron = '<div class="result-item">.*?<img src="(?P<thumb>[^"]+)".*?<span class="' + type + '">(?P<quality>[^<>]+).*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a>.*?<span class="year">(?P<year>[0-9]{4}).*?<div class="contenido"><p>(?P<plot>[^<>]+)'
    patronNext = '<a class="arrow_pag" href="([^"]+)"><i id="nextpagination"'

    return locals()


def dooplay_menu(item, type):
    patronMenu = '<a href="(?P<url>[^"#]+)"(?: title="[^"]+")?>(?P<title>[a-zA-Z0-9]+)'
    patronBlock = '<nav class="' + item.args + '">(?P<block>.*?)</nav>'
    action = 'peliculas'

    return locals()


def swzz_get_url(item):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:59.0) Gecko/20100101 Firefox/59.0'}
    # dbg()
    if "/link/" in item.url:
        data = httptools.downloadpage(item.url, headers=headers).data
        if "link =" in data:
            data = scrapertools.find_single_match(data, 'link = "([^"]+)"')
            if 'http' not in data:
                data = 'https:' + data
        elif 'linkId = ' in data:
            id = scrapertools.find_single_match(data, 'linkId = "([^"]+)"')
            data = stayonline(id)
        else:
            match = scrapertools.find_single_match(data, r'<meta name="og:url" content="([^"]+)"')
            match = scrapertools.find_single_match(data, r'URL=([^"]+)">') if not match else match

            if not match:
                from lib import jsunpack

                try:
                    data = scrapertools.find_single_match(data.replace('\n', ''), r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>")
                    data = jsunpack.unpack(data)

                    logger.debug("##### play /link/ unpack ##\n%s\n##" % data)
                except:
                    logger.debug("##### The content is yet unpacked ##\n%s\n##" % data)

                data = scrapertools.find_single_match(data, r'var link(?:\s)?=(?:\s)?"([^"]+)";')
                data, c = unshortenit.unwrap_30x_only(data)
            else:
                data = match
        if data.startswith('/'):
            data = urlparse.urljoin("http://swzz.xyz", data)
            if not "vcrypt" in data:
                data = httptools.downloadpage(data).data
        logger.debug("##### play /link/ data ##\n%s\n##" % data)

    elif 'stayonline.pro' in item.url:
        id = item.url.split('/')[-2]
        data = stayonline(id)
    else:
        data = item.url

    return data.replace('\\','')

def stayonline(id):
    reqUrl = 'https://stayonline.pro/ajax/linkView.php'
    p = urlencode({"id": id})
    data = httptools.downloadpage(reqUrl, post=p).data
    try:
        import json
        data = json.loads(data)['data']['value']
    except:
        data = scrapertools.find_single_match(data, r'"value"\s*:\s*"([^"]+)"')
    return data


def menuItem(itemlist, filename, title='', action='', url='', contentType='movie', args=[]):
    # Function to simplify menu creation

    # Call typo function
    title = typo(title)

    if contentType == 'movie': extra = 'movie'
    else: extra = 'tvshow'

    itemlist.append(Item(
        channel = filename,
        title = title,
        action = action,
        url = url,
        extra = extra,
        args = args,
        contentType = contentType
    ))

    # Apply auto Thumbnails at the menus
    from channelselector import thumb
    thumb(itemlist)
    return itemlist


def menu(func):
    def wrapper(*args):
        log()
        args = func(*args)

        item = args['item']
        host = func.__globals__['host']
        list_servers = func.__globals__['list_servers'] if 'list_servers' in func.__globals__ else ['directo']
        list_quality = func.__globals__['list_quality'] if 'list_quality' in func.__globals__ else ['default']
        log('LIST QUALITY', list_quality)
        filename = func.__module__.split('.')[1]
        global_search = False
        # listUrls = ['film', 'filmSub', 'tvshow', 'tvshowSub', 'anime', 'animeSub', 'search', 'top', 'topSub']
        listUrls = ['top', 'film', 'tvshow', 'anime', 'search']
        listUrls_extra = []
        dictUrl = {}


        # Main options
        itemlist = []

        for name in listUrls:
            dictUrl[name] = args[name] if name in args else None
            log(dictUrl[name])
            if name == 'film': title = 'Film'
            if name == 'tvshow': title = 'Serie TV'
            if name == 'anime': title = 'Anime'

            if name == 'search' and dictUrl[name] is not None:
                global_search = True

            # Make TOP MENU
            elif name == 'top' and dictUrl[name] is not None:
                for sub, var in dictUrl['top']:
                    menuItem(itemlist, filename,
                             title = sub + ' italic bold',
                             url = host + var[0] if len(var) > 0 else '',
                             action = var[1] if len(var) > 1 else 'peliculas',
                             args=var[2] if len(var) > 2 else '',
                             contentType= var[3] if len(var) > 3 else 'movie')

            # Make MAIN MENU
            elif dictUrl[name] is not None:
                if len(dictUrl[name]) == 0: url = ''
                else: url = dictUrl[name][0] if type(dictUrl[name][0]) is not tuple and len(dictUrl[name][0]) > 0 else ''
                menuItem(itemlist, filename,
                         title + ' bullet bold', 'peliculas',
                         host + url,
                         contentType='movie' if name == 'film' else 'tvshow')
                if len(dictUrl[name]) > 0:
                    if type(dictUrl[name][0]) is not tuple and type(dictUrl[name]) is not str: dictUrl[name].pop(0)
                if dictUrl[name] is not None and type(dictUrl[name]) is not str:
                    for sub, var in dictUrl[name]:
                        menuItem(itemlist, filename,
                             title = sub + ' submenu  {' + title + '}',
                             url = host + var[0] if len(var) > 0 else '',
                             action = var[1] if len(var) > 1 else 'peliculas',
                             args=var[2] if len(var) > 2 else '',
                             contentType= var[3] if len(var) > 3 else 'movie' if name == 'film' else 'tvshow')
                # add search menu for category
                if 'search' not in args: menuItem(itemlist, filename, config.get_localized_string(70741) % title + ' … submenu bold', 'search', host + url, contentType='movie' if name == 'film' else 'tvshow')

        # Make EXTRA MENU (on bottom)
        for name, var in args.items():
            if name not in listUrls and name != 'item':
               listUrls_extra.append(name)
        for name in listUrls_extra:
            dictUrl[name] = args[name] if name in args else None
            for sub, var in dictUrl[name]:
                menuItem(itemlist, filename,
                             title = sub + ' ',
                             url = host + var[0] if len(var) > 0 else '',
                             action = var[1] if len(var) > 1 else 'peliculas',
                             args=var[2] if len(var) > 2 else '',
                             contentType= var[3] if len(var) > 3 else 'movie',)

        if global_search:
            menuItem(itemlist, filename, config.get_localized_string(70741) % '… bold', 'search', host + dictUrl['search'])

        if 'get_channel_results' not in inspect.stack()[1][3]:
            autoplay.init(item.channel, list_servers, list_quality)
            autoplay.show_option(item.channel, itemlist)
        channel_config(item, itemlist)

        return itemlist

    return wrapper


def typo(string, typography=''):

    kod_color = '0xFF65B3DA' #'0xFF0081C2'
    try: string = str(string)
    except: string = str(string.encode('utf8'))

    if typography:
        string = string + ' ' + typography
    if config.get_localized_string(30992) in string:
        string = string + ' >'

    # If there are no attributes, it applies the default ones
    attribute = ['[]','()','submenu','color','bold','italic','_','--','[B]','[I]','[COLOR]']
    if int(config.get_setting('view_mode_channel').split(',')[-1]) in [0, 50, 55]:
       VLT = True
    else:
        VLT = False
    # Otherwise it uses the typographical attributes of the string
    # else:
    if 'capitalize' in string.lower():
        string = re.sub(r'\s*capitalize','',string).capitalize()
    if 'uppercase' in string.lower():
        string =  re.sub(r'\s*uppercase','',string).upper()
    if 'lowercase' in string.lower():
        string =  re.sub(r'\s*lowercase','',string).lower()
    if '[]' in string:
        string = '[' + re.sub(r'\s*\[\]','',string) + ']'
    if '()' in string:
        string = '(' + re.sub(r'\s*\(\)','',string) + ')'
    if 'submenu' in string:
        if VLT:
            string = "•• " + re.sub(r'\s*submenu','',string)
        else:
            string = re.sub(r'\s*submenu','',string)
    if 'color' in string:
        color = scrapertools.find_single_match(string, 'color ([a-z]+)')
        if color == 'kod' or '': color = kod_color
        string = '[COLOR '+ color +']' + re.sub(r'\scolor\s([a-z]+)','',string) + '[/COLOR]'
    if 'bold' in string:
        string = '[B]' + re.sub(r'\s*bold','',string) + '[/B]'
    if 'italic' in string:
        string = '[I]' + re.sub(r'\s*italic','',string) + '[/I]'
    if '_' in string:
        string = ' ' + re.sub(r'\s*_','',string)
    if '--' in string:
        string = ' - ' + re.sub(r'\s*--','',string)
    if 'bullet' in string:
        if VLT:
            string = '[B]' + "•" + '[/B] ' + re.sub(r'\s*bullet','',string)
        else:
            string = re.sub(r'\s*bullet','',string)
    if '{}' in string:
        string = re.sub(r'\s*\{\}','',string)

    return string


def match(item_url_string, **args):
    '''
    match is a function that combines httptools and scraper tools:

    supports all httptools and the following arggs:
        @param item_url_string: if it's a titem download the page item.url, if it's a URL download the page, if it's a string pass it to scrapertools
        @type  item_url_string: item or str
        @param string: force item_url_string to be a string
        @type  string: bool
        @param patronBlock: find first element in patron
        @type  patronBlock: str
        @param patronBloks: find multiple matches
        @type  patronBloks: str or list
        @param debugBlock: regex101.com for debug
        @type  debugBlock: bool
        @param patron: find multiple matches on block, blocks or data
        @type  patron: str or list
        @param debug: regex101.com for debug
        @type  debug: bool

    Return a item with the following key:
        data: data of the webpage
        block: first block
        blocks: all the blocks
        match: first match
        matches: all the matches
    '''

    matches = blocks = []
    url = None
    # arguments allowed for scrape
    patron = args.get('patron', None)
    patronBlock = args.get('patronBlock', None)
    patronBlocks = args.get('patronBlock', None)
    debug = args.get('debug', False)
    debugBlock = args.get('debugBlock', False)
    string = args.get('string', False)

    # remove scrape arguments
    args = dict([(key, val) for key, val in args.items() if key not in ['patron', 'patronBlock', 'patronBlocks', 'debug', 'debugBlock', 'string']])

    # check type of item_url_string
    if string:
        data = item_url_string
    elif isinstance(item_url_string, Item):
        # if item_url_string is an item use item.url as url
        url = item_url_string.url
    else:
        if item_url_string.startswith('http'): url = item_url_string
        else : data = item_url_string
    # else:
    #     # if item_url_string is an item use item.url as url
    #     url = item_url_string.url

    # if there is a url, download the page
    if url:
        if args.get('ignore_response_code', None) is None:
            args['ignore_response_code'] = True
        data = httptools.downloadpage(url, **args).data.replace("'", '"')

    # format page data
    data = re.sub(r'\n|\t', ' ', data)
    data = re.sub(r'>\s\s*<', '><', data)

    # collect blocks of a page
    if patronBlock:
        blocks = [scrapertools.find_single_match(data, patronBlock)]
    elif patronBlocks:
        if type(patronBlock) == str:  patron = [patronBlock]
        for p in patronBlock:
            blocks += scrapertools.find_multiple_matches(data, p)
    else:
        blocks = [data]

    # match
    if patron:
        if type(patron) == str:  patron = [patron]
        for b in blocks:
            for p in patron:
                matches += scrapertools.find_multiple_matches(b, p)

    # debug mode
    if config.dev_mode():
        if debugBlock:
            match_dbg(data, patronBlock)
        if debug:
            for block in blocks:
                for p in patron:
                    match_dbg(block, p)

    # create a item
    item = Item(data=data,
                blocks=blocks,
                block=blocks[0] if len(blocks) > 0 else '',
                matches=matches,
                match=matches[0] if len(matches) > 0 else '')

    return item


def match_dbg(data, patron):
    import json, urllib2, webbrowser
    url = 'https://regex101.com'
    headers = {'content-type': 'application/json'}
    data = {
        'regex': patron,
        'flags': 'gm',
        'testString': data,
        'delimiter': '"""',
        'flavor': 'python'
    }
    r = urllib2.Request(url + '/api/regex', json.dumps(data, encoding='latin1'), headers=headers)
    r = urllib2.urlopen(r).read()
    permaLink = json.loads(r)['permalinkFragment']
    webbrowser.open(url + "/r/" + permaLink)


def download(itemlist, item, typography='', function_level=1, function=''):
    if config.get_setting('downloadenabled'):
        if not typography: typography = 'color kod bold'

        if item.contentType == 'movie':
            from_action = 'findvideos'
            title = typo(config.get_localized_string(60354), typography)
        elif item.contentType == 'episode':
            from_action = 'findvideos'
            title = typo(config.get_localized_string(60356), typography) + ' - ' + item.title
        elif item.contentType == 'tvshow':
            from_action = 'episodios'
            title = typo(config.get_localized_string(60355), typography)
        else:  # content type does not support download
            return itemlist

        # function = function if function else inspect.stack()[function_level][3]

        contentSerieName=item.contentSerieName if item.contentSerieName else ''
        contentTitle=item.contentTitle if item.contentTitle else ''
        downloadItemlist = [i.tourl() for i in itemlist]

        if itemlist and item.contentChannel != 'videolibrary':
            show = True
            # do not show if we are on findvideos and there are no valid servers
            if from_action == 'findvideos':
                for i in itemlist:
                    if i.action == 'play':
                        break
                else:
                    show = False
            if show:
                itemlist.append(
                    Item(channel='downloads',
                         from_channel=item.channel,
                         title=title,
                         fulltitle=item.fulltitle,
                         show=item.fulltitle,
                         contentType=item.contentType,
                         contentSerieName=contentSerieName,
                         url=item.url,
                         action='save_download',
                         from_action=from_action,
                         contentTitle=contentTitle,
                         path=item.path,
                         thumbnail=thumb(thumb='downloads.png'),
                         downloadItemlist=downloadItemlist
                    ))
            if from_action == 'episodios':
                itemlist.append(
                    Item(channel='downloads',
                         from_channel=item.channel,
                         title=typo(config.get_localized_string(60357),typography),
                         fulltitle=item.fulltitle,
                         show=item.fulltitle,
                         contentType=item.contentType,
                         contentSerieName=contentSerieName,
                         url=item.url,
                         action='save_download',
                         from_action=from_action,
                         contentTitle=contentTitle,
                         download='season',
                         thumbnail=thumb(thumb='downloads.png'),
                         downloadItemlist=downloadItemlist
                ))

        return itemlist


def videolibrary(itemlist, item, typography='', function_level=1, function=''):
    # Simply add this function to add video library support
    # Function_level is useful if the function is called by another function.
    # If the call is direct, leave it blank
    log()

    if item.contentType == 'movie':
        action = 'add_pelicula_to_library'
        extra = 'findvideos'
        contentType = 'movie'
    else:
        action = 'add_serie_to_library'
        extra = 'episodios'
        contentType = 'tvshow'

    function = function if function else inspect.stack()[function_level][3]
    # go up until find findvideos/episodios
    while function not in ['findvideos', 'episodios']:
        function_level += 1
        try:
            function = inspect.stack()[function_level][3]
        except:
            break

    if not typography: typography = 'color kod bold'

    title = typo(config.get_localized_string(30161), typography)
    contentSerieName=item.contentSerieName if item.contentSerieName else ''
    contentTitle=item.contentTitle if item.contentTitle else ''

    if (function == 'findvideos' and contentType == 'movie') \
        or (function == 'episodios' and contentType != 'movie'):
        if config.get_videolibrary_support() and len(itemlist) > 0:
            from channelselector import get_thumb
            itemlist.append(
                Item(channel=item.channel,
                     title=title,
                     fulltitle=item.fulltitle,
                     show=item.fulltitle,
                     contentType=contentType,
                     contentTitle=contentTitle,
                     contentSerieName=contentSerieName,
                     url=item.url,
                     action=action,
                     extra=extra,
                     path=item.path,
                     thumbnail=get_thumb('add_to_videolibrary.png')
                    ))

    return itemlist

def nextPage(itemlist, item, data='', patron='', function_or_level=1, next_page='', resub=[]):
    # Function_level is useful if the function is called by another function.
    # If the call is direct, leave it blank
    action = inspect.stack()[function_or_level][3] if type(function_or_level) == int else function_or_level
    if next_page == '':
        next_page = scrapertools.find_single_match(data, patron)

    if next_page != "":
        if resub: next_page = re.sub(resub[0], resub[1], next_page)
        if 'http' not in next_page:
            next_page = scrapertools.find_single_match(item.url, 'https?://[a-z0-9.-]+') + (next_page if next_page.startswith('/') else '/' + next_page)
        next_page = re.sub('&amp;', '&',next_page)
        log('NEXT= ', next_page)
        itemlist.append(
            Item(channel=item.channel,
                 action = action,
                 contentType=item.contentType,
                 title=typo(config.get_localized_string(30992), 'color kod bold'),
                 url=next_page,
                 args=item.args,
                 thumbnail=thumb()))

    return itemlist

def pagination(itemlist, item, page, perpage, function_level=1):
    if len(itemlist) >= page * perpage:
        itemlist.append(
            Item(channel=item.channel,
                 action=inspect.stack()[function_level][3],
                 contentType=item.contentType,
                 title=typo(config.get_localized_string(30992), 'color kod bold'),
                 url=item.url,
                 args=item.args,
                 page=page + 1,
                 thumbnail=thumb()))
    return itemlist

def server(item, data='', itemlist=[], headers='', AutoPlay=True, CheckLinks=True, Download=True, patronTag=None, Videolibrary=True):
    log()
    if not data and not itemlist:
        data = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data
    if data:
        itemList = servertools.find_video_items(data=str(data))
        itemlist = itemlist + itemList
    verifiedItemlist = []

    def getItem(videoitem):
        if not servertools.get_server_parameters(videoitem.server.lower()):  # do not exists or it's empty
            findS = servertools.get_server_from_url(videoitem.url)
            log(findS)
            if not findS:
                if item.channel == 'community':
                    findS= ('Diretto', videoitem.url, 'directo')
                else:
                    videoitem.url = unshortenit.unshorten_only(videoitem.url)[0]
                    findS = servertools.get_server_from_url(videoitem.url)
                    if not findS:
                        log(videoitem, 'Non supportato')
                        return
            videoitem.server = findS[2]
            videoitem.title = findS[0]
            videoitem.url = findS[1]

        item.title = typo(item.contentTitle.strip(), 'bold') if item.contentType == 'movie' or (config.get_localized_string(30161) in item.title) else item.title

        quality = videoitem.quality if videoitem.quality else item.quality if item.quality else ''
        videoitem.title = (item.title if item.channel not in ['url'] else '') + (typo(videoitem.title, '_ color kod [] bold') if videoitem.title else "") + (typo(videoitem.quality, '_ color kod []') if videoitem.quality else "")
        videoitem.plot= typo(videoitem.title, 'bold') + (typo(quality, '_ [] bold') if quality else '')
        videoitem.channel = item.channel
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.contentType = item.contentType
        videoitem.infoLabels = item.infoLabels
        videoitem.quality = quality
        return videoitem

    with futures.ThreadPoolExecutor() as executor:
        thL = [executor.submit(getItem, videoitem) for videoitem in itemlist]
        for it in futures.as_completed(thL):
            if it.result():
                verifiedItemlist.append(it.result())
    try:
        verifiedItemlist.sort(key=lambda it: int(re.sub(r'\D','',it.quality)))
    except:
        verifiedItemlist.sort(key=lambda it: it.quality, reverse=True)
    if patronTag:
        addQualityTag(item, verifiedItemlist, data, patronTag)

    # Auto Play & Hide Links
    AP, HS = autoplay.get_channel_AP_HS(item)

    # Check Links
    if not AP and (config.get_setting('checklinks') or config.get_setting('checklinks', item.channel)):
        if config.get_setting('checklinks', item.channel):
            checklinks_number = config.get_setting('checklinks_number', item.channel)
        elif config.get_setting('checklinks'):
            checklinks_number = config.get_setting('checklinks_number')
        verifiedItemlist = servertools.check_list_links(verifiedItemlist, checklinks_number)

    if AutoPlay and not 'downloads' in inspect.stack()[3][1] or not 'downloads' in inspect.stack()[3][1] or not inspect.stack()[4][1]:
        autoplay.start(verifiedItemlist, item)

    if Videolibrary and item.contentChannel != 'videolibrary':
        videolibrary(verifiedItemlist, item, function_level=3)
    if Download:
        download(verifiedItemlist, item, function_level=3)

    if not AP or not HS:
        # for it in verifiedItemlist:
        #     log(it)
        return verifiedItemlist


def filterLang(item, itemlist):
    # import channeltools
    list_language = channeltools.get_lang(item.channel)
    if len(list_language) > 1:
        from specials import filtertools
        itemlist = filtertools.get_links(itemlist, item, list_language)
    return itemlist

def aplay(item, itemlist, list_servers='', list_quality=''):
    if inspect.stack()[1][3] == 'mainlist':
        autoplay.init(item.channel, list_servers, list_quality)
        autoplay.show_option(item.channel, itemlist)
    else:
        autoplay.start(itemlist, item)


def log(*args):
    # Function to simplify the log
    # Automatically returns File Name and Function Name
    string = ''
    for arg in args:
        string += ' '+str(arg)
    frame = inspect.stack()[1]
    filename = frame[0].f_code.co_filename
    filename = os.path.basename(filename)
    logger.info("[" + filename + "] - [" + inspect.stack()[1][3] + "] " + string)


def channel_config(item, itemlist):
    from  channelselector import get_thumb
    itemlist.append(
        Item(channel='setting',
             action="channel_config",
             title=typo(config.get_localized_string(60587), 'color kod bold'),
             config=item.channel,
             folder=False,
             thumbnail=get_thumb('setting_0.png'))
    )


def extract_wrapped(decorated):
    from types import FunctionType
    closure = (c.cell_contents for c in decorated.__closure__)
    return next((c for c in closure if isinstance(c, FunctionType)), None)

def addQualityTag(item, itemlist, data, patron):
    if itemlist:
        defQualVideo = {
            "CAM": "metodo di ripresa che indica video di bassa qualità",
            "TS": "questo metodo di ripresa effettua la ripresa su un tre piedi. Qualità sufficiente.",
            "TC": "abbreviazione di TeleCine. Il metodo di ripresa del film è basato su una macchina capace di riversare le Super-8, o 35mm. La qualità è superiore a quella offerta da CAM e TS.",
            "R5": "la qualità video di un R5 è pari a quella di un dvd, può contenere anche sottotitoli. Se è presente la dicitura LINE.ITALIAN è in italiano, altrimenti sarà disponibile in una lingua asiatica o russa.",
            "R6": "video proveniente dall’Asia.",
            "FS": "video a schermo pieno, cioè FullScreen, quindi con un rapporto di 4:3.",
            "WS": "video WideScreen, cioè rapporto 16:9.",
            "VHSSCR": "video estratto da una videocassetta VHS.",
            "DVDRIP": "la fonte video proviene da un DVD, la qualità è buona.",
            "DVDSCR": "la fonte video proviene da un DVD. Tali filmati, di solito, appartengono a copie promozionali.",
            "HDTVRIP": "video copiato e registrato da televisori in HD e che, per questo, restituiscono una qualità eccellente.",
            "PD": "video registrato da Tv satellitare, qualità accettabile.",
            "TV": "video registrato da Tv satellitare, qualità accettabile.",
            "SAT": "video registrato da Tv satellitare, qualità accettabile.",
            "DVBRIP": "video registrato da Tv satellitare, qualità accettabile.",
            "TVRIP": "ripping simile al SAT RIP, solo che, in questo caso, la qualità del vide può variare a seconda dei casi.",
            "VHSRIP": "video registrato da videocassetta. Qualità variabile.",
            "BRRIP": "indica che il video è stato preso da una fonte BluRay. Nella maggior parte dei casi, avremo un video ad alta definizione.",
            "BDRIP": "indica che il video è stato preso da una fonte BluRay. Nella maggior parte dei casi, avremo un video ad alta definizione.",
            "DTTRIP": "video registrato da un canale digitale terreste. Qualità sufficiente.",
            "HQ": "video in alta qualità.",
            "WEBRIP": "in questo caso, i film sono estratti da portali relativi a canali televisivi o di video sharing come YouTube. La qualità varia dall’SD al 1080p.",
            "WEB-DL": "si tratta di un 720p o 1080p reperiti dalla versione americana di iTunes americano. La qualità è paragonabile a quella di un BluRayRip e permette di fruire di episodi televisivi, senza il fastidioso bollo distintivo della rete che trasmette.",
            "WEBDL": "si tratta di un 720p o 1080p reperiti dalla versione americana di iTunes americano. La qualità è paragonabile a quella di un BluRayRip e permette di fruire di episodi televisivi, senza il fastidioso bollo distintivo della rete che trasmette.",
            "DLMux": "si tratta di un 720p o 1080p reperiti dalla versione americana di iTunes americano. La qualità è paragonabile a quella di un BluRayRip e permette di fruire di episodi televisivi, senza il fastidioso bollo distintivo della rete che trasmette.",
            "DVD5": "il film è in formato DVD Single Layer, nel quale vengono mantenute tutte le caratteristiche del DVD originale: tra queste il menu multilingue, i sottotitoli e i contenuti speciali, se presenti. Il video è codificato nel formato DVD originale MPEG-2.",
            "DVD9": "ha le stesse caratteristiche del DVD5, ma le dimensioni del file sono di un DVD Dual Layer (8,5 GB).",
            "HDTS": "viene utilizzata una videocamera professionale ad alta definizione posizionata in modo fisso. La qualità audio video è buona.",
            "DVDMUX": "indica una buona qualità video, l’audio è stato aggiunto da una sorgente diversa per una migliore qualità.",
        }

        defQualAudio = {
            "MD": "l’audio è stato registrato via microfono, quindi la qualità è scarsa.",
            "DTS": "audio ricavato dai dischi DTS2, quindi la qualità audio è elevata.",
            "LD": "l’audio è stato registrato tramite jack collegato alla macchina da presa, pertanto di discreta qualità.",
            "DD": "audio ricavato dai dischi DTS cinema. L’audio è di buona qualità, ma potreste riscontrare il fatto che non potrebbe essere più riproducibile.",
            "AC3": "audio in Dolby Digital puo' variare da 2.0 a 5.1 canali in alta qualità.",
            "MP3": "codec per compressione audio utilizzato MP3.",
            "RESYNC": "il film è stato lavorato e re sincronizzato con una traccia audio. A volte potresti riscontrare una mancata sincronizzazione tra audio e video.",
        }
        qualityStr = scrapertools.find_single_match(data, patron).strip().upper()
        if PY3:
            qualityStr = qualityStr.encode('ascii', 'ignore')
        else:
            qualityStr = qualityStr.decode('unicode_escape').encode('ascii', 'ignore')

        if qualityStr:
            try:
                video, audio, descr = None, None, ''
                for tag in defQualVideo:
                    if tag in qualityStr:
                        video = tag
                        break
                for tag in defQualAudio:
                    if tag in qualityStr:
                        audio = tag
                        break
                if video:
                    descr += typo(video + ': ', 'color kod') + defQualVideo.get(video, '') + '\n'
                if audio:
                    descr += typo(audio + ': ', 'color kod') + defQualAudio.get(audio, '') + '\n'
            except:
                descr = ''
            itemlist.insert(0,
                            Item(channel=item.channel,
                                 action="",
                                 title=typo(qualityStr, '[] color kod bold'),
                                 plot=descr,
                                 folder=False))
        else:
            log('nessun tag qualità trovato')

def get_jwplayer_mediaurl(data, srvName):
    video_urls = []
    block = scrapertools.find_single_match(data, r'sources: \[([^\]]+)\]')
    if 'file:' in block:
        sources = scrapertools.find_multiple_matches(block, r'file:\s*"([^"]+)"(?:,label:\s*"([^"]+)")?')
    elif 'src:' in block:
        sources = scrapertools.find_multiple_matches(data, r'src:\s*"([^"]+)",\s*type:\s*"[^"]+",[^,]+,\s*label:\s*"([^"]+)"')
    else:
        sources =[(block.replace('"',''), '')]
    for url, quality in sources:
        quality = 'auto' if not quality else quality
        if url.split('.')[-1] != 'mpd':
            video_urls.append(['.' + url.split('.')[-1] + ' [' + quality + '] [' + srvName + ']', url])

    video_urls.sort(key=lambda x: x[0].split()[1])
    return video_urls