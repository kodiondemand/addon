# -*- coding: utf-8 -*-
# -----------------------------------------------------------
# support functions that are needed by many channels, to no repeat the same code
import base64, inspect, os, re, sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
if PY3:
    from concurrent import futures
    from urllib.request import Request, urlopen
    import urllib.parse as urlparse
    from urllib.parse import urlencode
else:
    from concurrent_py2 import futures
    import urlparse
    from urllib2 import Request, urlopen
    from urllib import urlencode

from time import time
from core import httptools, scrapertools, servertools, tmdb, channeltools, autoplay
from core.item import Item
from lib import unshortenit
from platformcode import config, logger

channels_order = {'Rai 1': 1,
                  'Rai 2': 2,
                  'Rai 3': 3,
                  'Rete 4': 4,
                  'Canale 5': 5,
                  'Italia 1': 6,
                  'La7': 7,
                  'NOVE': 9,
                  '20': 20,
                  'Rai 4': 21,
                  'Iris': 22,
                  'Rai 5': 23,
                  'Rai Movie': 24,
                  'Rai Premium': 25,
                  'Paramount': 27,
                  'La7d': 29,
                  'La 5': 30,
                  'Real Time': 31,
                  'Food Network': 33,
                  'Cine34': 34,
                  'Focus': 35,
                  'Giallo': 38,
                  'Top Crime': 39,
                  'Boing': 40,
                  'K2': 41,
                  'Rai Gulp': 42,
                  'Rai Yoyo': 43,
                  'Frisbee': 44,
                  'Cartoonito': 46,
                  'Super': 46,
                  'Rai News 24': 48,
                  'Spike': 49,
                  'TGCom': 51,
                  'DMAX': 52,
                  'Rai Storia': 54,
                  'Mediaset Extra': 55,
                  'Home and Garden TV': 56,
                  'Rai Sport piu HD': 57,
                  'Rai Sport': 58,
                  'Motor Trend': 59,
                  'Italia 2': 66,
                  'VH1': 67,
                  'Rai Scuola': 146,
                  'Radio 105': 157,
                  'R101tv': 167,
                  'RMC': 256,
                  'Virgin Radio': 257,
                  'Rai Radio 2': 999,
                  }

########## MAIN FUNCTION ##########
class scrape:
    """https://github.com/kodiondemand/addon/wiki/decoratori#scrape"""

    # Legenda:
    # known_keys per i groups nei patron
    # known_keys = ['url', 'title', 'title2', 'season', 'episode', 'episode2', 'thumb', 'quality', 'year', 'plot', 'duration', 'genere', 'rating', 'type', 'lang', 'size', 'seed']
    # url = link relativo o assoluto alla pagina titolo film/serie
    # title = titolo Film/Serie/Anime/Altro
    # title2 = titolo dell'episodio Serie/Anime/Altro
    # season = stagione in formato numerico
    # episode = numero episodio, in formato numerico.
    # episode2 = numero episodio/i aggiuntivi, in formato numerico.
    # thumb = link realtivo o assoluto alla locandina Film/Serie/Anime/Altro
    # quality = qualità indicata del video
    # year = anno in formato numerico (4 cifre)
    # plot = plot del video
    # duration = durata del Film/Serie/Anime/Altro
    # genere = genere del Film/Serie/Anime/Altro. Es: avventura, commedia
    # rating = punteggio/voto in formato numerico
    # type = tipo del video. Es. movie per film o tvshow per le serie. Di solito sono discrimanti usati dal sito
    # lang = lingua del video. Es: ITA, Sub-ITA, Sub, SUB ITA.
    # size = dimensione del video
    # seed = seed del torrent
    # AVVERTENZE: Se il titolo è trovato nella ricerca TMDB/TVDB/Altro allora le locandine e altre info non saranno quelle recuperate nel sito.!!!!

    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        self.args = self.func(*args)
        self.function = self.func.__name__ if not 'actLike' in self.args else self.args['actLike']

        # self.args
        self.action = self.args.get('action', 'findvideos')
        self.search = self.args.get('search', '')
        self.lang = self.args.get('deflang', '')

        self.headers = self.args['headers'] if 'headers' in self.args else self.func.__globals__['headers'] if 'headers' in self.func.__globals__ else ''

        self.data = self.args.get('data', '')
        self.patronBlock = self.args.get('patronBlock', '')
        self.patron = self.args.get('patron', self.args.get('patronMenu', self.args.get('patronGenreMenu', '')))

        self.patronNext = self.args.get('patronNext', '')
        self.patronTotalPages = self.args.get('patronTotalPages', '')

        self.pagination = self.args.get('pagination', False)
        self.seasonPagination = self.args.get('seasonPagination', True)

        self.debug = self.args.get('debug', False)
        self.debugBlock = self.args.get('debugBlock', False)

        self.blacklist = self.args.get('blacklist', [])

        self.typeActionDict = self.args.get('typeActionDict', {})
        self.typeContentDict = self.args.get('typeContentDict', {})

        self.sceneTitle = self.args.get('sceneTitle')
        self.group = self.args.get('group', False)
        self.tmdbEnabled = self.args.get('tmdbEnabled', True)
        self.videlibraryEnabled = self.args.get('videlibraryEnabled', True)
        self.numerationEnabled = self.args.get('numerationEnabled', False)
        self.downloadEnabled = self.args.get('downloadEnabled', True)

        if self.args.get('disableAll', False):
            self.videlibraryEnabled = False
            self.downloadEnabled = False
            self.seasonPagination = False

        item = self.args['item']
        # variable
        self.pag = item.page if item.page else 1
        self.itemlist = []
        self.matches = []
        self.seasons = []
        self.known_keys = ['url', 'title', 'title2', 'season', 'episode', 'episode2', 'thumb', 'quality', 'year', 'plot', 'duration', 'genere', 'rating', 'type', 'lang', 'size', 'seed']

        # run scrape
        self._scrape(item)
        return self.itemlist

    def _scrape(self, item):

        if item.itemlist:
            scrapingTime = time()
            self.itemlist = itemlistdb()
            self.seasons = item.allSeasons
        else:
            for n in range(2):
                logger.debug('PATRON= ', self.patron)
                if not self.data:
                    page = httptools.downloadpage(item.url, headers=self.headers, ignore_response_code=True)
                    item.url = page.url  # might be a redirect
                    self.data = page.data
                self.data = html_uniform(self.data)
                scrapingTime = time()
                if self.patronBlock:
                    if self.debugBlock: regexDbg(item, self.patronBlock, self.headers, self.data)
                    blocks = scrapertools.find_multiple_matches_groups(self.data, self.patronBlock)
                    for bl in blocks:self._scrapeBlock(item, bl)

                elif self.patron:
                    self._scrapeBlock(item, self.data)

                if 'itemlistHook' in self.args:
                    try:
                        self.itemlist = self.args['itemlistHook'](self.itemlist)
                    except:
                        raise logger.ChannelScraperException

                # if url may be changed and channel has findhost to update
                if 'findhost' in self.func.__globals__ and not self.itemlist and n == 0:
                    logger.debug('running findhost ' + self.func.__module__)
                    ch = self.func.__module__.split('.')[-1]
                    try:
                        host = config.get_channel_url(self.func.__globals__['findhost'], ch, True)
                        parse = list(urlparse.urlparse(item.url))
                        parse[1] = scrapertools.get_domain_from_url(host)
                        item.url = urlparse.urlunparse(parse)
                    except:
                        raise logger.ChannelScraperException
                    self.data = None
                    self.itemlist = []
                    self.matches = []
                else:
                    break

            if not self.data:
                from platformcode.logger import WebErrorException
                raise WebErrorException(urlparse.urlparse(item.url)[1], item.channel)


            if self.group and item.grouped or self.args.get('groupExplode'):
                import copy
                nextargs = copy.copy(self.args)
                @scrape
                def newFunc():
                    return nextargs
                nextargs['item'] = nextPage(self.itemlist, item, self.function, data=self.data, patron=self.patronNext,  patron_total_pages=self.patronTotalPages)
                nextargs['group'] = False
                if nextargs['item']:
                    nextargs['groupExplode'] = True
                    self.itemlist.pop()  # remove next page just added
                    self.itemlist.extend(newFunc())
                else:
                    nextargs['groupExplode'] = False
                    nextargs['item'] = self.item
                    self.itemlist = newFunc()
                self.itemlist = [i for i in self.itemlist if i.action not in ['add_movie_to_library', 'add_serie_to_library']]

            if not self.group and not self.args.get('groupExplode') and ((self.pagination and len(self.matches) <= self.pag * self.pagination) or not self.pagination):  # next page with pagination
                if self.patronNext and inspect.stack()[1][3] not in ['newest'] and len(inspect.stack()) > 2 and inspect.stack()[2][3] not in ['get_channel_results']:
                    nextPage(self.itemlist, item, self.function, data=self.data, patron=self.patronNext,  patron_total_pages=self.patronTotalPages)

            if self.numerationEnabled and inspect.stack()[1][3] not in ['find_episodes']:
                from platformcode import autorenumber
                if self.function == 'episodios':
                    autorenumber.start(self.itemlist, self.item)

                    for i in self.itemlist:
                        if i.contentSeason and i.contentSeason not in self.seasons:
                            self.seasons.append(i.contentSeason)

                else: autorenumber.start(self.itemlist)


        if inspect.stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes']:
            if len(self.seasons) > 1 and self.seasonPagination:
                self.itemlist = season_pagination(self.itemlist, item, self.seasons, self.function)
            elif self.pagination:
                self.itemlist = pagination(self.itemlist, item, self.function)

        if self.action != 'play' and 'patronMenu' not in self.args and 'patronGenreMenu' not in self.args and self.tmdbEnabled and inspect.stack()[1][3] not in ['add_tvshow'] and self.function not in ['episodios', 'mainlist'] or (self.function in ['episodios'] and config.get_setting('episode_info')): # and function != 'episodios' and item.contentType in ['movie', 'tvshow', 'episode', 'undefined']
            tmdb.set_infoLabels_itemlist(self.itemlist, seekTmdb=True)

        if inspect.stack()[1][3] not in ['find_episodes', 'add_tvshow']:
            if self.videlibraryEnabled and (item.infoLabels["title"] or item.fulltitle):
                # item.fulltitle = item.infoLabels["title"]
                videolibrary(self.itemlist, item, function=self.function)
            if self.downloadEnabled and self.function == 'episodios' or self.function == 'findvideos':
                download(self.itemlist, item, function=self.function)

        if 'patronGenreMenu' in self.args and self.itemlist:
            self.itemlist = thumb(self.itemlist, mode='genre')
        if 'patronMenu' in self.args and self.itemlist:
            self.itemlist = thumb(self.itemlist)

        if 'fullItemlistHook' in self.args:
            try:
                self.itemlist = self.args['fullItemlistHook'](self.itemlist)
            except:
                raise logger.ChannelScraperException


        if config.get_setting('trakt_sync'):
            from core import trakt_tools
            trakt_tools.trakt_check(self.itemlist)
        logger.debug('scraping time: ', time()-scrapingTime)

    def _scrapeBlock(self, item, block):
        itemlist = []
        contents = []

        if type(block) == dict:
            if 'season' in block and block['season']: item.season = block['season']
            if 'lang' in block: item.contentLanguage = scrapeLang(block, item.contentLanguage)
            if 'quality' in block and block['quality']: item.quality = block['quality'].strip()
            block = block['block']

        if self.debug:
            regexDbg(item, self.patron, self.headers, block)

        matches = scrapertools.find_multiple_matches_groups(block, self.patron)
        logger.debug('MATCHES =', matches)

        for match in matches:
            self.itemParams = Item()
            for k, v in match.items():
                if v and k in ['url', 'thumb'] and 'http' not in v:
                    domain = ''
                    if v.startswith('//'):
                        domain = scrapertools.find_single_match(item.url, 'https?:')
                    elif v.startswith('/'):
                        domain = scrapertools.find_single_match(item.url, 'https?://[a-z0-9.-]+')
                    v = domain + v
                self.itemParams.__setattr__(k, v.strip() if type(v) == str else v)

            self.itemParams.title = cleantitle(self.itemParams.title)
            if self.group and self.itemParams.title in contents and not item.grouped:  # same title and grouping enabled
                continue
            if item.grouped and self.itemParams.title != item.fulltitle:  # inside a group different tvshow should not be included
                continue

            contents.append(self.itemParams.title)

            self.itemParams.title2 = cleantitle(self.itemParams.title2) if not self.group or item.grouped else ''
            self.itemParams.quality = self.itemParams.quality
            self.itemParams.plot = cleantitle(self.itemParams.plot)
            self.itemParams.language = scrapeLang(self.itemParams, self.lang)

            self.set_infolabels(item)
            if self.sceneTitle: self.set_sceneTitle()

            if not self.group or item.grouped:
                self.set_episodes(item)

            if self.itemParams.episode2: self.itemParams.second_episode = scrapertools.find_single_match(self.itemParams.episode2, r'(\d+)').split('x')
            if self.itemParams.season: self.itemParams.infoLabels['season'] = int(self.itemParams.season)
            if self.itemParams.episode: self.itemParams.infoLabels['episode'] = int(self.itemParams.episode)

            it = self.set_item(item, match)
            if it: itemlist.append(it)

        self.itemlist.extend(itemlist)
        self.matches.extend(matches)

    def set_infolabels(self, item):
        if item.infoLabels["title"] == self.itemParams.title:
            infolabels = item.infoLabels
        else:
            if self.function == 'episodios':
                infolabels = item.infoLabels
            else:
                infolabels = {}
            if self.itemParams.year:
                infolabels['year'] = self.itemParams.year
            if self.itemParams.plot:
                infolabels['plot'] = self.itemParams.plot
            if self.itemParams.duration:
                dur = scrapertools.find_multiple_matches(self.itemParams.duration, r'([0-9])\s*?(?:[hH]|:|\.|,|\\|\/|\||\s)\s*?([0-9]+)')
                for h, m in dur:
                    self.itemParams.duration = int(h) * 60 + int(m)
                if not dur:
                    self.itemParams.duration = scrapertools.find_single_match(self.itemParams.duration, r'(\d+)')
                try:
                    infolabels['duration'] = int(self.itemParams.duration) * 60
                except:
                    self.itemParams.duration = ''
            if self.itemParams.genre:
                genres = scrapertools.find_multiple_matches(self.itemParams.genre, '[A-Za-z]+')
                infolabels['genere'] = ", ".join(genres)
            if self.itemParams.rating:
                infolabels['rating'] = scrapertools.decodeHtmlentities(self.itemParams.rating)

        self.itemParams.infoLabels = infolabels

    def set_sceneTitle(self):
        from lib.guessit import guessit
        try:
            parsedTitle = guessit(self.itemParams.title)
            self.itemParams.title = parsedTitle.get('title', '')
            logger.debug('TITOLO',self.itemParams.title)
            if parsedTitle.get('source'):
                self.itemParams.quality = str(parsedTitle.get('source'))
                if parsedTitle.get('screen_size'):
                    self.itemParams.quality += ' ' + str(parsedTitle.get('screen_size', ''))
            if not self.itemParams.year:
                if type(parsedTitle.get('year', '')) == list:
                    self.itemParams.infoLabels['year'] = parsedTitle.get('year', '')[0]
                else:
                    self.itemParams.infoLabels['year'] = parsedTitle.get('year', '')
            if parsedTitle.get('episode') and parsedTitle.get('season'):
                if type(parsedTitle.get('season')) == list:
                    self.itemParams.season = str(parsedTitle.get('season')[0])
                elif parsedTitle.get('season'):
                    self.itemParams.season = str(parsedTitle.get('season'))

                if type(parsedTitle.get('episode')) == list:
                    self.itemParams.episode = str(parsedTitle.get('episode')[0])
                    self.itemParams.second_episode = str(parsedTitle.get('episode')[1:])
                else:
                    self.itemParams.infoLabels['episode'] = parsedTitle.get('episode')

            elif parsedTitle.get('season') and type(parsedTitle.get('season')) == list:
                self.itemParams.extraInfo = '{}: {}-{}'.format(config.get_localized_string(30140), parsedTitle.get('season')[0], parsedTitle.get('season')[-1])
            elif parsedTitle.get('season'):
                self.itemParams.season = str(parsedTitle.get('season'))
            if parsedTitle.get('episode_title'):
                self.itemParams.extraInfo += parsedTitle.get('episode_title')
        except:
            import traceback
            logger.error(traceback.format_exc())

    def set_episodes(self, item):
        ep = unifyEp(self.itemParams.episode) if self.itemParams.episode else ''
        se = self.itemParams.season if self.itemParams.season.isdigit() else ''
        if ep and se:
            self.itemParams.season = se
            if 'x' in ep:
                ep_list = ep.split('x')
                self.itemParams.episode = ep_list[0]
                self.itemParams.second_episode = ep_list[1:]
            else:
                self.itemParams.episode = ep

        elif item.season:
            self.itemParams.season = item.season
            if ep: self.itemParams.episode = int(scrapertools.find_single_match(self.itemParams.episode, r'(\d+)'))

        elif item.contentType == 'tvshow' and (self.itemParams.episode == '' and self.itemParams.season == '' and self.itemParams.season == ''):
            item.news = 'season_completed'

        else:
            try:
                if 'x' in ep:
                    ep_list = ep.split('x')
                    self.itemParams.episode = ep_list[1].strip()
                    self.itemParams.season = ep_list[0].strip()
                    if len(ep_list) > 2:
                        self.itemParams.second_episode = ep_list[2:]
                else:
                    self.itemParams.episode = ep
            except:
                logger.debug('invalid episode: ' + self.itemParams.episode)
                pass

    def set_item(self, item, match):
        AC = ''
        CT = ''
        if self.typeContentDict:
            for name, variants in self.typeContentDict.items():
                if str(self.itemParams.type).lower() in variants:
                    CT = name
                    break
                else: CT = item.contentType
        if self.typeActionDict:
            for name, variants in self.typeActionDict.items():
                if str(self.itemParams.type).lower() in variants:
                    AC = name
                    break
                else: AC = self.action
        if (not self.itemParams.title or self.itemParams.title not in self.blacklist) and (self.search.lower() in self.itemParams.title.lower()):

            it = item.clone(title=self.itemParams.title,
                                 fulltitle=self.itemParams.title,
                                 show=self.itemParams.title,
                                 infoLabels=self.itemParams.infoLabels,
                                 contentSeason= self.itemParams.infoLabels.get('season', ''),
                                 contentEpisodeNumber= self.itemParams.infoLabels.get('episode', ''),
                                 grouped = self.group,
                                 episode2 = self.itemParams.second_episode,
                                 extraInfo = self.itemParams.extraInfo,
                                 disable_videolibrary = not self.args.get('addVideolibrary', True),
                                 size = self.itemParams.size,
                                 seed = self.itemParams.seed)

            if self.itemParams.url: it.url = self.itemParams.url
            if self.function == 'episodios': it.fulltitle = it.show = self.itemParams.title
            if self.itemParams.quality: it.quality = self.itemParams.quality
            if self.itemParams.language: it.contentLanguage = self.itemParams.language
            if item.prevthumb: it.thumbnail = item.prevthumb
            elif self.itemParams.thumb: it.thumbnail = self.itemParams.thumb
            it.contentType = 'episode' if self.function == 'episodios' else CT if CT else item.contentType
            if it.contentType not in ['movie'] and self.function != 'episodios' or it.contentType in ['undefined']: it.contentSerieName = self.itemParams.title
            if self.function == 'peliculas': it.contentTitle= self.itemParams.title
            it.contentSeason= self.itemParams.infoLabels.get('season', ''),
            it.contentEpisodeNumber= self.itemParams.infoLabels.get('episode', ''),
            if self.itemParams.title2: it.title2 = self.itemParams.title2

            if self.itemParams.episode and self.group and not item.grouped:
                it.action = self.function
            elif AC:
                it.action = AC
            else:
                it.action=self.action

            if it.action == 'findvideos':
                it.window = True if item.window_type == 0 or (config.get_setting("window_type") == 0) else False
                if it.window: it.folder = False

            for lg in list(set(match.keys()).difference(self.known_keys)):
                it.__setattr__(lg, match[lg])

            if 'itemHook' in self.args:
                try:
                    it = self.args['itemHook'](it)
                except:
                    raise logger.ChannelScraperException

            if it.contentSeason and it.contentSeason not in self.seasons:
                self.seasons.append(it.contentSeason)

            return it


def regexDbg(item, patron, headers, data=''):
    if config.dev_mode():
        import json, webbrowser
        url = 'https://regex101.com'

        if not data:
            html = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data.replace("'", '"')
            html = html.replace('\n', ' ')
            html = html.replace('\t', ' ')
        else:
            html = data
        headers = {'content-type': 'application/json'}
        data = {
            'regex': patron if PY3 else patron.decode('utf-8'),
            'flags': 'gm',
            'testString': html if PY3 else html.decode('utf-8'),
            'delimiter': '"""',
            'flavor': 'python'
        }
        data = json.dumps(data).encode() if PY3 else json.dumps(data, encoding='latin1')
        r = Request(url + '/api/regex', data, headers=headers)
        r = urlopen(r).read()
        permaLink = json.loads(r)['permalinkFragment']
        webbrowser.open(url + "/r/" + permaLink)


def scrapeLang(scraped, lang):
    ##    Aggiunto/modificato per gestire i siti che hanno i video
    ##    in ita e subita delle serie tv nella stessa pagina
    # altrimenti dopo un sub-ita mette tutti quelli a seguire in sub-ita
    # e credo sia utile per filtertools
    language = ''
    lang = scraped.get('lang') if type(scraped) == dict else scraped.lang

    if lang:
        if 'ita' in lang.lower(): language = 'ITA'
        if 'sub' in lang.lower(): language = 'Sub-' + language

    if not language: language = lang
    # if language: longtitle += typo(language, '_ [] color kod')
    return language


def cleantitle(title):
    cleantitle = ''
    if title:
        if type(title) != str: title.decode('UTF-8')
        title = scrapertools.unescape(title)
        title = scrapertools.decodeHtmlentities(title)
        cleantitle = title.replace('"', "'").replace('×', 'x').replace('–', '-').strip()
    return cleantitle


def unifyEp(ep):
    # ep = re.sub(r'\s-\s|-|&#8211;|&#215;|×', 'x', scraped['episode'])
    ep = ep.replace('-', 'x')
    ep = ep.replace('&#8211;', 'x')
    ep = ep.replace('&#215;', 'x')
    ep = ep.replace('×', 'x')
    return ep


def html_uniform(data):
    """
        replace all ' with " and eliminate newline, so we don't need to worry about
    """
    return re.sub("='([^']+)'", '="\\1"', data.replace('\n', ' ').replace('\t', ' ').replace('&nbsp;', ' '))


# Debug

def dbg():
    if config.dev_mode():
        try:
            import web_pdb
            if not web_pdb.WebPdb.active_instance:
                import webbrowser
                webbrowser.open('http://127.0.0.1:5555')
            web_pdb.set_trace()
        except:
            pass


# Menu

def menuItem(itemlist, channel, title='', action='', url='', contentType='undefined', args=[], style=True):
    # Function to simplify menu creation

    # Call typo function
    if style:
        title = typo(title)

    itemlist.append(Item(
        channel = channel,
        title = title,
        action = action,
        url = url,
        args = args,
        contentType = contentType,
    ))


def menu(func):
    """https://github.com/kodiondemand/addon/wiki/decoratori#menu"""

    def wrapper(*args):
        args = func(*args)

        item = args['item']
        logger.debug(item.channel + ' menu start')
        host = func.__globals__['host']
        menuHost = args.get('host','')
        if menuHost: host = menuHost
        channel = func.__module__.split('.')[1]
        single_search = False
        # listUrls = ['film', 'filmSub', 'tvshow', 'tvshowSub', 'anime', 'animeSub', 'search', 'top', 'topSub']
        listUrls = ['top', 'film', 'tvshow', 'anime', 'search', 'host']
        names = {'film':config.get_localized_string(30122),
                 'tvshow':config.get_localized_string(30123),
                 'anime':config.get_localized_string(30124),
                 'doc':config.get_localized_string(30125),
                 'music':config.get_localized_string(30139)}
        listUrls_extra = []
        dictUrl = {}

        global_search = item.global_search

        # Main options
        itemlist = []

        for name in listUrls:
            dictUrl[name] = args.get(name, None)
            logger.debug(dictUrl[name])
            if name in names: title = names[name]

            if name == 'search' and dictUrl[name] is not None:
                single_search = True

            # Make TOP MENU
            elif name == 'top' and dictUrl[name] is not None:
                if not global_search:
                    for sub, var in dictUrl['top']:
                        menuItem(itemlist, channel,
                                 title = sub + '{italic bold}',
                                 url = host + var[0] if len(var) > 0 else '',
                                 action = var[1] if len(var) > 1 else 'peliculas',
                                 args=var[2] if len(var) > 2 else '',
                                 contentType= var[3] if len(var) > 3 else 'movie')

            # Make MAIN MENU
            elif dictUrl[name] is not None:
                if len(dictUrl[name]) == 0:
                    url = ''
                else:
                    url = dictUrl[name][0] if type(dictUrl[name][0]) is not tuple and len(dictUrl[name][0]) > 0 else ''

                if not global_search:
                    menuItem(itemlist, channel,
                             title + '{bullet bold}', 'peliculas',
                             host + url,
                             contentType='movie' if name == 'film' else 'tvshow')

                    if len(dictUrl[name]) > 0:
                        if type(dictUrl[name][0]) is not tuple and type(dictUrl[name]) is not str: dictUrl[name].pop(0)

                    if dictUrl[name] is not None and type(dictUrl[name]) is not str:
                        for sub, var in dictUrl[name]:
                            menuItem(itemlist, channel,
                                 title = sub + '{submenu}  {' + title + '}',
                                 url = host + var[0] if len(var) > 0 else '',
                                 action = var[1] if len(var) > 1 else 'peliculas',
                                 args=var[2] if len(var) > 2 else '',
                                 contentType= var[3] if len(var) > 3 else 'movie' if name == 'film' else 'tvshow')
                # add search menu for category
                if 'search' not in args: menuItem(itemlist, channel, config.get_localized_string(70741) % title + '… {submenu bold}', 'search', host + url, contentType='movie' if name == 'film' else 'tvshow', style=not global_search)

        # Make EXTRA MENU (on bottom)
        for name, var in args.items():
            if name not in listUrls and name != 'item':
               listUrls_extra.append(name)

        for name in listUrls_extra:
            dictUrl[name] = args.get(name, None)
            for sub, var in dictUrl[name]:
                # sub = scrapertools.unescape(sub)
                menuItem(itemlist, channel,
                             title = sub,
                             url = host + var[0] if len(var) > 0 else '',
                             action = var[1] if len(var) > 1 else 'peliculas',
                             args=var[2] if len(var) > 2 else '',
                             contentType= var[3] if len(var) > 3 else 'movie',)

        if single_search:
            menuItem(itemlist, channel, config.get_localized_string(70741).replace(' %s', '… {bold}'), 'search', host + dictUrl['search'], style=not global_search)

        if not global_search:
            channel_config(item, itemlist)

            # Apply auto Thumbnails at the menus
            thumb(itemlist)
        logger.debug(item.channel + ' menu end')
        return itemlist

    return wrapper


# Match

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

    def match_dbg(data, patron):
        import json, webbrowser
        url = 'https://regex101.com'
        headers = {'content-type': 'application/json'}
        data = {
            'regex': patron,
            'flags': 'gm',
            'testString': data,
            'delimiter': '"""',
            'flavor': 'python'
        }
        js = json.dumps(data).encode() if PY3 else json.dumps(data, encoding='latin1')
        r = Request(url + '/api/regex', js, headers=headers)
        r = urlopen(r).read()
        permaLink = json.loads(r)['permalinkFragment']
        webbrowser.open(url + "/r/" + permaLink)

    matches = []
    blocks = []
    response = None
    url = None

    # arguments allowed for scrape
    patron = args.get('patron', None)
    patronBlock = args.get('patronBlock', None)
    patronBlocks = args.get('patronBlocks', None)
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
    elif item_url_string.startswith('http'):
        url = item_url_string
    else :
        data = item_url_string

    # if there is a url, download the page
    if url:
        if args.get('ignore_response_code', None) is None:
            args['ignore_response_code'] = True
        response = httptools.downloadpage(url, **args)
        data = response.data

    # format page data
    data = html_uniform(data)

    # collect blocks of a page
    if patronBlock:
        blocks = [scrapertools.find_single_match(data, patronBlock)]
    elif patronBlocks:
        if type(patronBlocks) == str:
            patronBlocks = [patronBlocks]
        for p in patronBlocks:
            blocks += scrapertools.find_multiple_matches(data, p)
    else:
        blocks = [data]

    # match
    if patron:
        if type(patron) == str: 
            patron = [patron]
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
                match=matches[0] if len(matches) > 0 else '',
                response = response)

    return item


# pagination

def nextPage(itemlist, item, function_or_level=1, **kwargs):
    '''
    Function_level is useful if the function is called by another function.
    If the call is direct, leave it blank
    itemlist = list of item -> required
    item = item -> required
    function_or_level = function to call or level of monitored function, integer or string -> optional def:1

    OPTIONAL ARGS
    data = data of the page 
    patron = regex to find the next page
    patron_total_pages = regex to find number of total pages
    next_page = link to next page
    resub = list of 2 values for resub _next_page
    page = integer, the page for next page
    total_pages = integer, the number of total pages
    '''
    logger.debug()
    if 'channel_search' in [s[3] for s in inspect.stack()]:
        return itemlist

    # get optional args
    data = kwargs.get('data', '')
    patron = kwargs.get('patron', '')
    patron_total_pages = kwargs.get('patron_total_pages', '')
    next_page = kwargs.get('next_page', None)
    resub = kwargs.get('resub', [])
    page = kwargs.get('page', None)
    total_pages = kwargs.get('total_pages', None)

    # get next_page from data
    if data and patron:
        next_page = scrapertools.find_single_match(data, patron)

    # resub an host to url
    if next_page:
        if resub: next_page = re.sub(resub[0], resub[1], next_page)
        if 'http' not in next_page:
            if '/' in next_page:
                next_page = scrapertools.find_single_match(item.url, 'https?://[a-z0-9.-]+') + (next_page if next_page.startswith('/') else '/' + next_page)
            else:
                next_page = '/'.join(item.url.split('/')[:-1]) + '/' + next_page
        next_page = next_page.replace('&amp;', '&')
        item.url = next_page

    # get total pages from data
    if data and patron_total_pages:
        found = scrapertools.find_single_match(data, patron_total_pages).replace('.','').replace(',','')
        if found.isdigit():
            item.total_pages = int(found)

    # set total pages from value
    if total_pages:
        item.total_pages = total_pages

    # create Item
    if next_page or page:
        itemlist.append(item.clone(action = inspect.stack()[function_or_level][3] if type(function_or_level) == int else function_or_level,
                                   title=typo(config.get_localized_string(30992), 'color kod bold'),
                                   nextPage=True,
                                   page=page if page else item.page + 1 if item.page else 2,
                                   prevthumb = item.thumbnail,
                                   thumbnail=thumb()))
    return itemlist


def pagination(itemlist, item, function_level=1):
    if 'channel_search' in [s[3] for s in inspect.stack()]:
        return itemlist
    itemlistdb(itemlist)
    page = item.page if item.page else 1
    perpage = config.get_setting('pagination', default=20)
    action = function_level if type(function_level) == str else inspect.stack()[function_level][3]
    itlist = []
    for i, it in enumerate(itemlist):
        if perpage and (page - 1) * perpage > i: continue  # pagination
        if perpage and i >= page * perpage: break          # pagination
        itlist.append(it)
    if len(itemlist) >= page * perpage:
        itlist.append(
            item.clone(channel=item.channel,
                       action=action,
                       contentType=item.contentType,
                       title=typo(config.get_localized_string(30992), 'color kod bold'),
                       page=page + 1,
                       total_pages=round(len(itemlist)/perpage),
                       nextPage = True,
                       itemlist = True,
                       prevthumb = item.thumbnail,
                       thumbnail=thumb()))
    return itlist


def season_pagination(itemlist, item, seasons, function_level=1):
    if 'channel_search' in [s[3] for s in inspect.stack()]:
        return itemlist
    itemlistdb(itemlist)
    action = function_level if type(function_level) == str else inspect.stack()[function_level][3]
    itlist = []
    if itemlist and not seasons:
        seasons = []
        for it in itemlist:
            if it.contentSeason and it.contentSeason not in seasons:
                seasons.append(it.contentSeason)

    if seasons:
        seasons.sort()
        if not item.nextSeason: item.nextSeason = 0
        try:
            current = seasons[item.nextSeason]

            for it in itemlist:
                if it.contentSeason and it.contentSeason == current:
                    itlist.append(it)
                elif it.contentSeason and it.contentSeason > current:
                    break

            if item.nextSeason + 1 < len(seasons):
                itlist.append(
                    item.clone(action=action,
                               title=typo('Stagione Successiva [{}]'.format(seasons[item.nextSeason + 1]), 'bold'),
                               allSeasons = seasons,
                               nextSeason = item.nextSeason + 1,
                               itemlist = True,
                               prevthumb = item.thumbnail,
                               thumbnail=thumb()))
            itlist.append(
                    item.clone(action='gotoseason',
                               real_action=action,
                               title=typo('Vai alla stagione…', 'bold'),
                               allSeasons = seasons,
                               nextSeason = item.nextSeason + 1,
                               itemlist = True,
                               prevthumb = item.thumbnail,
                               thumbnail=thumb()))
            return itlist
        except:
            return itemlist


# Find servers

def server(item, data='', itemlist=[], headers='', AutoPlay=True, CheckLinks=True, Download=True, patronTag=None, Videolibrary=True):
    logger.debug()

    if not data and not itemlist:
        data = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data
    if data:
        itemList = servertools.find_video_items(data=str(data))
        itemlist = itemlist + itemList
    verifiedItemlist = []

    def getItem(videoitem):
        if not videoitem.video_urls:
            srv_param = servertools.get_server_parameters(videoitem.server.lower())
            if not srv_param:  # do not exists or it's empty
                findS = servertools.get_server_from_url(videoitem.url)
                logger.debug(findS)
                if not findS:
                    if item.channel == 'community':
                        findS= (config.get_localized_string(30137), videoitem.url, 'directo')
                    else:
                        videoitem.url = unshortenit.unshorten_only(videoitem.url)[0]
                        findS = servertools.get_server_from_url(videoitem.url)
                        if not findS:
                            logger.debug(videoitem, 'Non supportato')
                            return
                videoitem.server = findS[2]
                videoitem.serverName= findS[0]
                videoitem.url = findS[1]
                srv_param = servertools.get_server_parameters(videoitem.server.lower())
            else:
                videoitem.server = videoitem.server.lower()

        if videoitem.video_urls or srv_param.get('active', False):
            logger.debug(item)
            quality = videoitem.quality if videoitem.quality else item.quality if item.quality else ''
            # videoitem = item.clone(url=videoitem.url, serverName=videoitem.serverName, server=videoitem.server, action='play')
            videoitem.contentLanguage = videoitem.contentLanguage if videoitem.contentLanguage else item.contentLanguage if item.contentLanguage else 'ITA'
            videoitem.serverName = videoitem.title if videoitem.server == 'directo' else servertools.get_server_parameters(videoitem.server).get('name', videoitem.server.capitalize())
            # videoitem.title = item.contentTitle.strip() if item.contentType == 'movie' and item.contentTitle or (config.get_localized_string(30161) in item.fulltitle) else item.fulltitle
            videoitem.plot = typo(videoitem.title, 'bold') + (typo(quality, '_ [] bold') if quality else '')
            videoitem.channel = item.channel
            videoitem.fulltitle = item.fulltitle
            videoitem.show = item.show
            if not videoitem.video_urls:  videoitem.thumbnail = item.thumbnail
            videoitem.contentType = item.contentType
            videoitem.infoLabels = item.infoLabels
            videoitem.quality = quality
            videoitem.referer = item.referer if item.referer else item.url
            videoitem.action = "play"
            videoitem.videolibrary_id = item.videolibrary_id
            videoitem.from_library = item.from_library
            videoitem.fanart = item.fanart if item.contentType == 'movie' else item.thumbnail
            return videoitem

    # non threaded for webpdb
    # dbg()
    # thL = [getItem(videoitem) for videoitem in itemlist if videoitem.url or videoitem.video_urls]
    # for it in thL:
    #     if it and not config.get_setting("black_list", server=it.server.lower()):
    #         verifiedItemlist.append(it)

    with futures.ThreadPoolExecutor() as executor:
        thL = [executor.submit(getItem, videoitem) for videoitem in itemlist if videoitem.url or videoitem.video_urls]
        for it in futures.as_completed(thL):
            if it.result():
                verifiedItemlist.append(it.result())
    try:
        verifiedItemlist.sort(key=lambda it: int(re.sub(r'\D','',it.quality)))
    except:
        verifiedItemlist.sort(key=lambda it: it.quality, reverse=True)
    if patronTag:
        addQualityTag(item, verifiedItemlist, data, patronTag)

    # Check Links
    if not item.global_search and config.get_setting('checklinks') and CheckLinks and not config.get_setting('autoplay'):
        checklinks_number = config.get_setting('checklinks_number')
        verifiedItemlist = servertools.check_list_links(verifiedItemlist, checklinks_number)

    try:
        if AutoPlay and item.contentChannel not in ['downloads', 'videolibrary']:
            verifiedItemlist = autoplay.start(verifiedItemlist, item)
    except:
        import traceback
        logger.error(traceback.format_exc())
        pass

    verifiedItemlist = servertools.sort_servers(verifiedItemlist)

    if Videolibrary and item.contentChannel != 'videolibrary':
        videolibrary(verifiedItemlist, item)
    if Download:
        download(verifiedItemlist, item, function_level=3)

    return verifiedItemlist


# extra item

def videolibrary(itemlist, item, typography='', function_level=1, function=''):
    # Simply add this function to add video library support
    # Function_level is useful if the function is called by another function.
    # If the call is direct, leave it blank
    logger.debug()

    if item.contentType == 'movie':
        action = 'add_to_library'
        contentType = 'movie'
    else:
        action = 'add_to_library'
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
    contentSerieName=item.contentSerieName if item.contentSerieName else item.fulltitle if item.contentType != 'movie' else ''
    contentTitle=item.contentTitle if item.contentTitle else item.fulltitle if item.contentType == 'movie' else ''

    if (function == 'findvideos' and contentType == 'movie') \
        or (function == 'episodios' and contentType != 'movie'):
        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(
                item.clone(channel=item.channel,
                           title=title,
                           fulltitle=item.fulltitle,
                           show=item.fulltitle,
                           contentType=contentType,
                           contentTitle=contentTitle,
                           contentSerieName=contentSerieName,
                           url=item.url,
                           action=action,
                           from_action=item.action,
                           path=item.path,
                           thumbnail=thumb('add_to_videolibrary')
                    ))

    return itemlist


def download(itemlist, item, typography='', function_level=1, function=''):
    if config.get_setting('downloadenabled'):

        if not typography: typography = 'color kod bold'

        if item.contentType == 'movie':
            from_action = 'findvideos'
            title = typo(config.get_localized_string(60354), typography)
        elif item.contentType == 'episode':
            from_action = 'findvideos'
            title = typo(config.get_localized_string(60356), typography) + ' - ' + item.title
        elif item.contentType in 'tvshow':
            if item.channel == 'community' and config.get_setting('show_seasons', item.channel):
                from_action = 'season'
            else:
                from_action = 'episodios'
            title = typo(config.get_localized_string(60355), typography)
        elif item.contentType in 'season':
            from_action = 'get_seasons'
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
            if show and item.contentType != 'season':
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
                         thumbnail=thumb('download'),
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
                         thumbnail=thumb('download'),
                         downloadItemlist=downloadItemlist
                ))

        return itemlist


# utility


def filterLang(item, itemlist):
    # import channeltools
    list_language = channeltools.get_lang(item.channel)
    if len(list_language) > 1:
        from core import filtertools
        itemlist = filtertools.get_links(itemlist, item, list_language)
    return itemlist


def channel_config(item, itemlist):
    itemlist.append(
        Item(channel='setting',
             action="channel_config",
             title=typo(config.get_localized_string(60587), 'color kod bold'),
             config=item.channel,
             folder=False,
             thumbnail=thumb('setting'))
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
        # if PY3: qualityStr = qualityStr.encode('ascii', 'ignore')
        if not PY3: qualityStr = qualityStr.decode('unicode_escape').encode('ascii', 'ignore')

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
            itemlist.insert(0,Item(channel=item.channel,
                                   action="",
                                   title=typo(qualityStr, '[] color kod bold'),
                                   fulltitle=qualityStr,
                                   plot=descr,
                                   folder=False,
                                   thumbnail=thumb('info')))
        else:
            logger.debug('nessun tag qualità trovato')


def thumb(data=None, mode=None):
    '''
        data = str, item or itemlist
        mode = str, genre, live, quality
    '''

    if mode == 'live':
        if type(data) == list:
            for item in data:
                item.thumbnail = "https://raw.githubusercontent.com/kodiondemand/media/master/live/" + item.fulltitle.lower().replace(' ','_') + '.png'
        else:
            data.thumbnail = "https://raw.githubusercontent.com/kodiondemand/media/master/live/" + data.fulltitle.lower().replace(' ','_') + '.png'
        return data

    _movie = ['movie', 'movies', 'film', 'films']
    _tvshow = ['serie', 'tv', 'episodi', 'episodio', 'fiction', 'show', 'episode', 'episodes']
    _anime = ['anime']
    _documentary = ['documentario', 'documentari', 'documentary', 'documentaries', 'documentaristico']
    _music = ['musica', 'musicale', 'music', 'musical']
    _torrent = ['torrent']
    _live = ['corso', 'onda', 'diretta', 'dirette', 'progress', 'air', 'live']
    _year = ['anno', 'anni', 'year', 'years']
    _top = ['voto', 'voti', 'votato', 'votati', 'migliore', 'migliori', 'fortunato', 'classifica', 'classifiche', 'vote', 'voted', 'best', 'top', 'lucky', 'ranking', 'rating', 'charts']
    _popular = ['popolare', 'popolari', 'raccomandato', 'raccomandati', 'raccomandazione', 'raccomandazioni', 'momento', 'popular', 'recommended', 'recommendation', 'recommendations', 'moment']
    _all = ['tutto', 'tutta', 'tutti', 'tutte' 'all']
    _az = ['lettera', 'lettere', 'lista', 'liste', 'alfabetico', 'a-z', 'letter', 'letters', 'list', 'alphabetical']
    _news = ['novità', "novita'", 'aggiornamenti', 'nuovo', 'nuova', 'nuovi', 'nuove', 'ultimo', 'ultima', 'ultimi', 'ultime', 'notizia', 'notizie', 'new', 'newest', 'last', 'latest', 'news']
    _cinema = ['cinema', 'sala', 'theatre', 'theatres']
    _genre = ['genere', 'generi', 'categoria', 'categorie', 'genre', 'genres', 'category', 'categories']
    _sub = ['sub', 'sub-ita', 'sottotitolato', 'sottotitolata', 'sottotitolati', 'originale', 'subtitled', 'original']
    _ita = ['ita', 'italiano']
    _update = ['aggiorno', 'aggiorna', 'aggiorni', 'aggiornare', 'update', 'replay']
    _videolibrary = ['videoteca', 'videoteche', 'teca', 'teche', 'library', 'videolibrary']
    _info = ['informazione', 'informazioni', 'info', 'information', 'informations']
    _star = ['attore', 'attrice', 'attori', 'attrici', 'regista', 'registi', 'personaggio', 'personaggi', 'interprete', 'interpreti', 'star', 'stars', 'character', 'characters', 'performer', 'performers', 'staff', 'actor', 'actors', 'actress', 'actresses', 'director', 'directors']
    _winter = ['inverno', 'winter']
    _spring = ['primavera', 'spring'],
    _summer = ['estate', 'summer'],
    _autumn = ['autunno', 'autumn'],
    _teenager = ['ragazzo', 'ragazza', 'ragazzi', 'ragazze','teenager', 'teen']
    _learning = ['imparare', 'scuola', 'learn', 'learning', 'school']
    _animation = ['animazione', 'cartoni', 'animation', 'cartoon']
    _action = ['azione', 'marziali', 'action', 'martial', 'samurai']
    _adventure = ['avventura', 'adventure']
    _biographic = ['biografia',  'biografico', 'bio', 'biographic', 'biographical']
    _comedy = ['comico', 'commedia', 'parodia', 'demenziale', 'brillante', 'comic', 'comical', 'comedy', 'parody', 'demential']
    _adult = ['erotico', 'hentai', 'harem', 'ecchi', 'adult']
    _drama = ['dramma', 'drammatico', 'drama']
    _syfy = ['fantascienza', 'science fiction', 'syfy', 'sci', 'fi']
    _fantasy = ['fantastico', 'magia', 'fantasy', 'magic']
    _crime = ['polizia', 'poliziesco', 'poliziottesco', 'crimine', 'criminale', 'police', 'crime', 'gangster']
    _grotesque = ['grottesco', 'grotesque']
    _war = ['guerra', 'militare', 'militari', 'war', 'military']
    _children = ['bambino', 'bambina', 'bambini', 'bambine', 'child', 'children', 'kids', 'baby', 'babies', 'boy', 'girl']
    _horror = ['orrore', 'paura', 'horror', 'fear']
    _mistery = ['mistero', 'giallo', 'mystery']
    _noir = ['noir']
    _thriller = ['thriller']
    _western = ['western']
    _romance = ['romantico', 'sentimentale', 'romance', 'soap']
    _family = ['famiglia','famiglie', 'family']
    _historical = ['storia', 'storico', 'history', 'historical']
    _setting = ['impostazioni', 'settaggi', 'configura', 'configurare', 'gestire', 'gestisci', 'gestione', 'setting', 'config']
    _talk = ['talk']
    _reality = ['reality']
    _quality = ['qualità', 'risoluzione', 'risoluzioni', 'quality', 'resolution', 'resolutions']
    _cam = ['cam']
    _ts = ['ts']
    _md = ['md']
    _sd = ['sd']
    _hd = ['hd']
    _fhd = ['fullhd']
    _2k = ['2k']
    _4k = ['4k']

    main_dict = {'movie':_movie,
                 'tvshow':_tvshow,
                 'anime':_anime,
                 'documentary':_documentary,
                 'music':_music}

    icon_dict = {'torrent':_torrent,
                 'all':_all,
                 'az':_az,
                 'news':_news,
                 'cinema':_cinema,
                 'genre':_genre,
                 'popular':_popular,
                 'live':_live,
                 'year':_year,
                 'update':_update,
                 'videolibrary':_videolibrary,
                 'info':_info,
                 'star':_star,
                 'winter':_winter,
                 'spring':_spring,
                 'summer':_summer,
                 'autumn':_autumn,
                 'sub':_sub,
                 'top':_top,
                 'setting':_setting,
                 'children':_children,
                 'family':_family,
                 'teenager':_teenager,
                 'learning':_learning,
                 'quality':_quality,
                 'autoplay':[config.get_localized_string(60071)]
                }

    genre_dict = {'documentary':_documentary,
                  'teenager':_teenager,
                  'learning':_learning,
                  'animation':_animation,
                  'action':_action,
                  'adventure':_adventure,
                  'biographic':_biographic,
                  'comedy':_comedy,
                  'adult':_adult,
                  'drama':_drama,
                  'syfy':_syfy,
                  'fantasy':_fantasy,
                  'crime':_crime,
                  'grotesque':_grotesque,
                  'war':_war,
                  'children':_children,
                  'horror':_horror,
                  'music':_music,
                  'mistery':_mistery,
                  'noir':_noir,
                  'thriller':_thriller,
                  'western':_western,
                  'romance':_romance,
                  'family':_family,
                  'historical':_historical,
                  'news':_news,
                  'talk':_talk,
                  'reality':_reality,
                  'tvmovie':_movie}

    search = ['cerca', 'cercare', 'ricerca', 'ricercare', 'trova', 'trovare', 'search', 'searching', 'find', 'finding']

    suffix_dict = {'_cam':_cam,
                   '_ts':_ts,
                   '_md':_md,
                   '_sd':_sd,
                   '_hd':_hd,
                   '_fullhd':_fhd,
                   '_2k':_2k,
                   '_4k':_4k,
                   '_az':_az,
                   '_genre':_genre,
                   '_popular':_popular,
                   '_top':_top,
                   '_year':_year,
                   '_news':_news,
                   '_live':_live,
                   '_sub':_sub,
                   '_ita':_ita,
                   '_quality':_quality,
                   '_cinema':_cinema,
                   '_search':search}

    quality_dict = {'cam':_cam,
                    'ts':_ts,
                    'md':_md,
                    'sd':_sd,
                    'hd':_hd,
                    'fhd':_fhd,
                    '2k':_2k,
                    '4k':_4k}

    search_suffix ={'_year':_year,
                    '_top':_top,
                    '_music':_music,
                    '_star':_star,
                    '_genre':_genre,
                    '_top':_top}

    def autoselect_thumb(item, mode):
        searched_title = re.split(r'\.|\{|\}|\(|\)|/| ', scrapertools.unescape(re.sub('\[[^\]]*\]||\u2026|\u2022','', item.title.lower())))
        logger.debug('SEARCED', searched_title)
        thumb = ''
        if mode == 'genre':
            for t, titles in genre_dict.items():
                if any(word in searched_title for word in titles):
                    thumb = t
        elif mode == 'quality':
            for t, titles in quality_dict.items():
                if searched_title[0] in titles:
                    thumb = t
        else:
            if any(word in searched_title for word in _setting):
                thumb = 'setting'
            else:
                for t, titles in main_dict.items():
                    if any(word in searched_title for word in titles):
                        thumb = t
                        if thumb in main_dict.keys():
                            for suffix, titles in suffix_dict.items():
                                if any(word in searched_title for word in titles):
                                    thumb = t + suffix
            if not thumb:
                if any(word in searched_title for word in search):
                    thumb = 'search'
                    for suffix, titles in search_suffix.items():
                        if any(word in searched_title for word in titles):
                            thumb = thumb + suffix
            if not thumb:
                for t, titles in icon_dict.items():
                    if any(word in searched_title for word in titles):
                        thumb = t

        if thumb: item.thumbnail = get_thumb(thumb + '.png')
        item.title = re.sub(r'\s*\{[^\}]+\}','',item.title)
        return item

    if data:
        if type(data) == list:
            for item in data:
                autoselect_thumb(item, mode)
            return data

        elif type(data) == str:
            filename, file_extension = os.path.splitext(data)
            if not file_extension: data += '.png'
            return get_thumb(data)
        else:
            return autoselect_thumb(data, mode)

    else:
        return get_thumb('next.png')


def get_thumb(thumb_name, view="thumb_"):
    from core import filetools
    if thumb_name.startswith('http'):
        return thumb_name
    elif config.get_setting('enable_custom_theme') and config.get_setting('custom_theme') and filetools.isfile(config.get_setting('custom_theme') + view + thumb_name):
        media_path = config.get_setting('custom_theme')
    else:
        icon_pack_name = config.get_setting('icon_set', default="default")
        media_path = filetools.join("https://raw.githubusercontent.com/kodiondemand/media/master/themes/new", icon_pack_name)
    return filetools.join(media_path, thumb_name)


def color(text, color):
    return "[COLOR " + color + "]" + text + "[/COLOR]"


def typo(string, typography=''):

    kod_color = '0xFF65B3DA' #'0xFF0081C2'

    try: string = str(string)
    except: string = str(string.encode('utf8'))

    if config.get_localized_string(30992) in string:
        string = string + ' >'

    if int(config.get_setting('view_mode_channel').split(',')[-1]) in [0, 50, 55]:
       VLT = True
    else:
        VLT = False


    if not typography and '{' in string:
        typography = string.split('{')[1].strip(' }').lower()
        string = string.replace('{' + typography + '}','').strip()
    else:
        string = string
        typography.lower()

    if 'capitalize' in typography:
        string = string.capitalize()
        typography = typography.replace('capitalize', '')
    if 'uppercase' in typography:
        string = string.upper()
        typography = typography.replace('uppercase', '')
    if 'lowercase' in typography:
        string = string.lower()
        typography = typography.replace('lowercase', '')
    if '[]' in typography:
        string = '[' + string + ']'
        typography = typography.replace('[]', '')
    if '()' in typography:
        string = '(' + string + ')'
        typography = typography.replace('()', '')
    if 'submenu' in typography:
        if VLT: string = "•• " + string
        else: string = string
        typography = typography.replace('submenu', '')
    if 'color kod' in typography:
        string = '[COLOR ' + kod_color + ']' + string + '[/COLOR]'
        typography = typography.replace('color kod', '')
    elif 'color' in typography:
        color = scrapertools.find_single_match(typography, 'color ([a-zA-Z0-9]+)')
        string = '[COLOR ' + color + ']' + string + '[/COLOR]'
        typography = typography.replace('color ' + color, '')
    if 'bold' in typography:
        string = '[B]' + string + '[/B]'
        typography = typography.replace('bold', '')
    if 'italic' in typography:
        string = '[I]' + string + '[/I]'
        typography = typography.replace('italic', '')
    if '__' in typography:
        string = string + ' ' 
        typography = typography.replace('__', '')
    if '_' in typography:
        string = ' ' + string
        typography = typography.replace('_', '')
    if '--' in typography:
        string = ' - ' + string
        typography = typography.replace('--', '')
    if 'bullet' in typography:
        if VLT: string = '[B]' + "•" + '[/B] ' + string
        else: string = string
        typography = typography.replace('bullet', '')
    typography = typography.strip()
    if typography: string = string + '{' + typography + '}'
    return string


########## HD PASS ##########

def hdpass_get_servers(item, data=''):
    def get_hosts(url, quality):
        ret = []
        page = httptools.downloadpage(url, CF=False).data
        mir = scrapertools.find_single_match(page, patron_mir)

        for mir_url, srv in scrapertools.find_multiple_matches(mir, patron_option):
            mir_url = scrapertools.decodeHtmlentities(mir_url)
            logger.debug(mir_url)
            it = hdpass_get_url(item.clone(action='play', quality=quality, url=mir_url))[0]
            # it = item.clone(action="play", quality=quality, title=srv, server=srv, url= mir_url)
            # if not servertools.get_server_parameters(srv.lower()): it = hdpass_get_url(it)[0]   # do not exists or it's empty
            ret.append(it)
        return ret
    # Carica la pagina
    itemlist = []
    if 'hdpass' in item.url or 'hdplayer' in item.url: url = item.url
    else:
        if not data:
            data = httptools.downloadpage(item.url, CF=False).data.replace('\n', '')
        patron = r'<iframe(?: id="[^"]+")? width="[^"]+" height="[^"]+" src="([^"]+)"[^>]+><\/iframe>'
        url = scrapertools.find_single_match(data, patron)
        url = url.replace("&download=1", "")
        if 'hdpass' not in url and 'hdplayer' not in url: return itemlist
    if not url.startswith('http'): url = 'https:' + url
    item.referer = url

    data = httptools.downloadpage(url, CF=False).data
    patron_res = '<div class="buttons-bar resolutions-bar">(.*?)<div class="buttons-bar'
    patron_mir = '<div class="buttons-bar hosts-bar">(.*?)(?:<div id="main-player|<script)'
    patron_option = r'<a href="([^"]+?)"[^>]+>([^<]+?)</a'

    res = scrapertools.find_single_match(data, patron_res)

    # non threaded for webpdb
    # for res_url, res_video in scrapertools.find_multiple_matches(res, patron_option):
    #     res_url = scrapertools.decodeHtmlentities(res_url)
    #     itemlist.extend(get_hosts(res_url, res_video))
    #
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
    data = httptools.downloadpage(item.url, CF=False).data
    src = scrapertools.find_single_match(data, r'<iframe allowfullscreen custom-src="([^"]+)')
    if src: item.url = base64.b64decode(src)
    else: item.url = scrapertools.find_single_match(data, r'<iframe allowfullscreen src="([^"]+)')
    item.url, c = unshortenit.unshorten_only(item.url)
    return [item]

########## SEARCH ##########

def search(channel, item, texto):
    logger.debug(item.url + " search " + texto)
    item.url = channel.host + "/?s=" + texto
    try:
        return channel.peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
    return []

########## DOOPLAY ##########

def dooplay_get_links(item, host, paramList=[]):
    # get links from websites using dooplay theme and dooplay_player
    # return a list of dict containing these values: url, title and server
    if not paramList:
        data = httptools.downloadpage(item.url).data.replace("'", '"')
        patron = r'<li id="player-option-[0-9]".*?data-type="([^"]+)" data-post="([^"]+)" data-nume="([^"]+)".*?<span class="title".*?>([^<>]+)</span>(?:<span class="server">([^<>]+))?'
        matches = scrapertools.find_multiple_matches(data, patron)
    else:
        matches = paramList
    ret = []

    for type, post, nume, title, server in matches:
        postData = urlencode({
            "action": "doo_player_ajax",
            "post": post,
            "nume": nume,
            "type": type
        })
        dataAdmin = httptools.downloadpage(host + '/wp-admin/admin-ajax.php', post=postData,headers={'Referer': item.url}).data
        link = scrapertools.find_single_match(dataAdmin, r"<iframe.*src='([^']+)'")
        if not link: link = scrapertools.find_single_match(dataAdmin, r'"embed_url":"([^"]+)"').replace('\\','')
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
    # debug = True
    if item.args == 'searchPage':
        return dooplay_search_vars(item, blacklist)
    else:
        if item.contentType == 'movie':
            action = 'findvideos'
            patron = '<article id="post-[0-9]+" class="item movies">.*?<img src="(?!data)(?P<thumb>[^"]+)".*?(?:<span class="quality">(?P<quality>[^<>]+).*?)?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></h3>.*?(?:<span>[^<>]*(?P<year>[0-9]{4})</span>|</article>)'
        else:
            action = 'episodios'
            patron = '<article id="post-[0-9]+" class="item (?P<type>' + ('\w+' if mixed else 'tvshows') + ')">.*?<img src="(?!data)(?P<thumb>[^"]+)".*?(?:<span class="quality">(?P<quality>[^<>]+))?.*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></h3>.*?(?:<span>(?P<year>[0-9]{4})</span>|</article>).*?(?:<div class="texto">(?P<plot>[^<>]+)|</article>).*?(?:genres">(?P<genre>.*?)</div>|</article>)'
        patronNext = '<div class="pagination">.*?class="current".*?<a href="([^"]+)".*?<div class="resppages">'
        videlibraryEnabled = False

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


########## JWPLAYER ##########

def get_jwplayer_mediaurl(data, srvName, onlyHttp=False, dataIsBlock=False):
    from core import jsontools
    video_urls = []
    block = scrapertools.find_single_match(data, r'sources"?\s*:\s*(.*?}])') if not dataIsBlock else data
    if block:
        json = jsontools.load(block)
        if json:
            sources = []
            for s in json:
                if 'file' in s.keys():
                    src = s['file']
                else:
                    src = s['src']
                sources.append((src, s.get('label')))
        else:
            if 'file:' in block:
                sources = scrapertools.find_multiple_matches(block, r'file:\s*"([^"]+)"(?:,label:\s*"([^"]+)")?')
            elif 'src:' in block:
                sources = scrapertools.find_multiple_matches(block, r'src:\s*"([^"]+)",\s*type:\s*"[^"]+"(?:,[^,]+,\s*label:\s*"([^"]+)")?')
            else:
                sources =[(block.replace('"',''), '')]
        for url, quality in sources:
            quality = 'auto' if not quality else quality
            if url.split('.')[-1] != 'mpd':
                video_urls.append({'type':url.split('.')[-1], 'res':quality, 'url':url if not onlyHttp else url.replace('https://', 'http://')})

    return video_urls


########## ITEMLIST DB FOR PAGINATION ##########

def itemlistdb(itemlist=None):
    from core import db
    if itemlist:
        db['itemlist']['itemlist'] = itemlist
    else:
        itemlist = db['itemlist'].get('itemlist',[])
    db.close()
    return itemlist
