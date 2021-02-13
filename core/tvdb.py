# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# tvdb
# ------------------------------------------------------------
# Scraper for thetvdb.com using API v2.1
# Used to obtain series data for the video library
# ------------------------------------------------------------

import sys
if sys.version_info[0] >= 3: PY3 = True
else: PY3 = False

from future import standard_library
standard_library.install_aliases()
from future.builtins import object

import urllib.request, urllib.error, urllib.parse

import re, requests

from core import jsontools
from core import scrapertools
from core.item import InfoLabels
from platformcode import config, logger
from platformcode import platformtools

HOST = "https://api.thetvdb.com"
HOST_IMAGE = "http://thetvdb.com/banners/"

TOKEN = config.get_setting("tvdb_token", default="")
info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
DEFAULT_LANG = info_language[config.get_setting("info_language", "videolibrary")]
DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, application/vnd.thetvdb.v2.1.1',
    'Accept-Language': DEFAULT_LANG,
    'Authorization': 'Bearer ' + TOKEN,
}

# # Traducciones - Inicio
# DICT_STATUS = {'Continuing': 'En emisión', 'Ended': 'Finalizada'}
# DICT_GENRE = {
#     'Action': 'Acción',
#     'Adventure': 'Aventura',
#     'Animation': 'Animación',
#     'Children': 'Niños',
#     'Comedy': 'Comedia',
#     'Crime': 'Crimen',
#     'Documentary': 'Documental',
#     # 'Drama': 'Drama',
#     'Family': 'Familiar',
#     'Fantasy': 'Fantasía',
#     'Food': 'Comida',
#     'Game Show': 'Concurso',
#     'Home and Garden': 'Hogar y Jardín',
#     # 'Horror': 'Horror', 'Mini-Series': 'Mini-Series',
#     'Mystery': 'Misterio',
#     'News': 'Noticias',
#     # 'Reality': 'Telerrealidad',
#     'Romance': 'Romántico',
#     'Science-Fiction': 'Ciencia-Ficción',
#     'Soap': 'Telenovela',
#     # 'Special Interest': 'Special Interest',
#     'Sport': 'Deporte',
#     # 'Suspense': 'Suspense',
#     'Talk Show': 'Programa de Entrevistas',
#     # 'Thriller': 'Thriller',
#     'Travel': 'Viaje',
#     # 'Western': 'Western'
# }
# DICT_MPAA = {'TV-Y': 'Público pre-infantil: niños menores de 6 años', 'TV-Y7': 'Público infantil: desde 7 años',
#              'TV-G': 'Público general: sin supervisión familiar', 'TV-PG': 'Guía paterna: Supervisión paternal',
#              'TV-14': 'Mayores de 14 años', 'TV-MA': 'Mayores de 17 años'}
# # Traducciones - Fin

otvdb_global = None


def find_and_set_infoLabels(item):
    logger.debug()
    # from core.support import dbg;dbg()
    # logger.debug("item es %s" % item)

    p_dialog = None
    if not item.contentSeason:
        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(60296), config.get_localized_string(60293))

    global otvdb_global
    tvdb_result = None

    title = item.contentSerieName
    # If the title includes the (year) we will remove it
    year = scrapertools.find_single_match(title, r"^.+?\s*(\(\d{4}\))$")
    if year:
        title = title.replace(year, "").strip()
        item.infoLabels['year'] = year[1:-1]

    if item.infoLabels.get("tvdb_id", '') in ['', 'None']:
        if item.infoLabels['year']:
            otvdb_global = Tvdb(search=title, year=item.infoLabels['year'])
        elif item.infoLabels.get("imdb_id"):
            otvdb_global = Tvdb(imdb_id=item.infoLabels.get("imdb_id"))
        else:
            otvdb_global = Tvdb(search=title)

    elif not otvdb_global or otvdb_global.get_id() != item.infoLabels['tvdb_id']:
        otvdb_global = Tvdb(tvdb_id=item.infoLabels['tvdb_id'])

    if not item.contentSeason:
        p_dialog.update(50, config.get_localized_string(60296) + '\n' + config.get_localized_string(60295))
    results, info_load = otvdb_global.get_list_results()
    logger.debug("results: %s" % results)

    if not item.contentSeason:
        p_dialog.update(100, config.get_localized_string(60296) + '\n' + config.get_localized_string(60297) % len(results))
        p_dialog.close()

    if len(results) > 1:
        tvdb_result = platformtools.show_video_info(results, item=item, scraper=Tvdb, caption=config.get_localized_string(60298) % title)
        # if not tvdb_result:
        #     res =  platformtools.dialog_info(item, 'tvdb')
        #     if not res.exit: return find_and_set_infoLabels(res)
    elif len(results) > 0:
        tvdb_result = results[0]

    # else:
    #     res =  platformtools.dialog_info(item, 'tvdb')
    #     if not res.exit: return find_and_set_infoLabels(res)

    # todo revisar
    if isinstance(item.infoLabels, InfoLabels):
        logger.debug("is an instance of infoLabels")
        infoLabels = item.infoLabels
    else:
        logger.debug("NOT an instance of infoLabels")
        infoLabels = InfoLabels()

    if tvdb_result:
        infoLabels['tvdb_id'] = tvdb_result['id']
        infoLabels['url_scraper'] = ["http://thetvdb.com/index.php?tab=series&id=%s" % infoLabels['tvdb_id']]
        if not info_load:
            if otvdb_global.get_id() != infoLabels['tvdb_id']:
                otvdb_global = Tvdb(tvdb_id=infoLabels['tvdb_id'])
            otvdb_global.get_images(infoLabels['tvdb_id'], image="poster")
            otvdb_global.get_images(infoLabels['tvdb_id'], image="fanart")
            otvdb_global.get_tvshow_cast(infoLabels['tvdb_id'])

        item.infoLabels = infoLabels
        set_infoLabels_item(item)

        return True

    else:
        item.infoLabels = infoLabels
        return False


def set_infoLabels_item(item):
    """
        Gets and sets (item.infoLabels) the extra data of a series, chapter or movie.
        @param item: Object that represents a movie, series or chapter. The infoLabels attribute will be modified including the extra localized data.
        @type item: Item
    """
    global otvdb_global

    def __leer_datos(otvdb_aux):
        item.infoLabels = otvdb_aux.get_infoLabels(item.infoLabels)
        if 'infoLabels' in item and 'thumbnail' in item.infoLabels:
            item.thumbnail = item.infoLabels['thumbnail']
        if 'infoLabels' in item and 'fanart' in item.infoLabels['fanart']:
            item.fanart = item.infoLabels['fanart']

    if 'infoLabels' in item and 'season' in item.infoLabels and item.contentType != 'tvshow':
        try:
            int_season = int(item.infoLabels['season'])
        except ValueError:
            logger.debug("The season number is not valid")
            item.contentType = item.infoLabels['mediatype']
            return -1 * len(item.infoLabels)

        if not otvdb_global or \
                (item.infoLabels['tvdb_id'] and otvdb_global.get_id() != item.infoLabels['tvdb_id']) \
                or (otvdb_global.search_name and otvdb_global.search_name != item.infoLabels['tvshowtitle']):
            if item.infoLabels['tvdb_id']:
                otvdb_global = Tvdb(tvdb_id=item.infoLabels['tvdb_id'])
            else:
                otvdb_global = Tvdb(search=item.infoLabels['tvshowtitle'])

            __leer_datos(otvdb_global)

        if item.infoLabels['episode']:
            try:
                int_episode = int(item.infoLabels['episode'])
            except ValueError:
                logger.debug("The episode number (%s) is not valid" % repr(item.infoLabels['episode']))
                item.contentType = item.infoLabels['mediatype']
                return -1 * len(item.infoLabels)

            # We have a valid season number and episode number ...
            # ... search episode data
            item.infoLabels['mediatype'] = 'episode'

            lang = DEFAULT_LANG
            if otvdb_global.lang:
                lang = otvdb_global.lang

            page = 1
            _id = None
            while not _id:
                list_episodes = otvdb_global.list_episodes.get(page)
                if not list_episodes:
                    list_episodes = otvdb_global.get_list_episodes(otvdb_global.get_id(), page)
                    import threading
                    semaforo = threading.Semaphore(20)
                    l_hilo = list()

                    for e in list_episodes["data"]:
                        t = threading.Thread(target=otvdb_global.get_episode_by_id, args=(e["id"], lang, semaforo))
                        t.start()
                        l_hilo.append(t)

                    # wait for all the threads to end
                    for x in l_hilo:
                        x.join()

                for e in list_episodes['data']:
                    if e['airedSeason'] == int_season and e['airedEpisodeNumber'] == int_episode:
                        _id = e['id']
                        break

                _next = list_episodes['links']['next']
                if isinstance(_next, int):
                    page = _next
                else:
                    break

            data_episode = otvdb_global.get_info_episode(otvdb_global.get_id(), int_season, int_episode, lang, _id)

            # all go over values ​​to insert into infoLabels
            if data_episode:
                item.infoLabels['title'] = data_episode['episodeName']
                # fix en casos que el campo desde la api era null--> None
                if data_episode["overview"] is not None:
                    item.infoLabels['plot'] = data_episode["overview"]

                item.thumbnail = HOST_IMAGE + data_episode.get('filename', "")

                item.infoLabels["rating"] = data_episode.get("siteRating", "")
                item.infoLabels['director'] = ', '.join(sorted(data_episode.get('directors', [])))
                item.infoLabels['writer'] = ', '.join(sorted(data_episode.get("writers", [])))

                if data_episode["firstAired"]:
                    item.infoLabels['premiered'] = data_episode["firstAired"].split("-")[2] + "/" + \
                                                   data_episode["firstAired"].split("-")[1] + "/" + \
                                                   data_episode["firstAired"].split("-")[0]
                    item.infoLabels['aired'] = item.infoLabels['premiered']

                guest_stars = data_episode.get("guestStars", [])
                l_castandrole = item.infoLabels.get("castandrole", [])
                l_castandrole.extend([(p, '') for p in guest_stars])
                item.infoLabels['castandrole'] = l_castandrole

                # data for nfo
                item.season_id = data_episode["airedSeasonID"]
                item.episode_id = data_episode["id"]

                return len(item.infoLabels)

        else:
            # We have a valid season number but no episode number ...
            # ... search season data
            item.infoLabels['mediatype'] = 'season'
            data_season = otvdb_global.get_images(otvdb_global.get_id(), "season", int_season)

            if data_season and 'image_season_%s' % int_season in data_season:
                item.thumbnail = HOST_IMAGE + data_season['image_season_%s' % int_season][0]['fileName']
                return len(item.infoLabels)

    # Search...
    else:
        # Search by ID ...
        if (not otvdb_global or otvdb_global.get_id() != item.infoLabels['tvdb_id']) and item.infoLabels['tvdb_id']:
            otvdb_global = Tvdb(tvdb_id=item.infoLabels['tvdb_id'])

        elif not otvdb_global and item.infoLabels['imdb_id']:
            otvdb_global = Tvdb(imdb_id=item.infoLabels['imdb_id'])

        elif not otvdb_global and item.infoLabels['zap2it_id']:
            otvdb_global = Tvdb(zap2it_id=item.infoLabels['zap2it_id'])

        # Unable to search by ID ... done by title
        if otvdb_global is None:
            otvdb_global = Tvdb(search=item.infoLabels['tvshowtitle'])

        if otvdb_global and otvdb_global.get_id():
            __leer_datos(otvdb_global)
            # The search has found a valid result
            return len(item.infoLabels)


def get_nfo(item, search_groups=False):
    """
    Returns the information necessary for the result to be scraped into the kodi video library,

    @param item: element that contains the data necessary to generate the info
    @type item: Item
    @rtype: str
    @return:
    """

    if "season" in item.infoLabels and "episode" in item.infoLabels:
        info_nfo = "http://thetvdb.com/?tab=episode&seriesid=%s&seasonid=%s&id=%s\n" % (item.infoLabels['tvdb_id'], item.season_id, item.episode_id)
    else:
        info_nfo = ', '.join(item.infoLabels['url_scraper']) + "\n"

    return info_nfo


def completar_codigos(item):
    """
    If necessary, check if the tmdb identifier exists and if it does not exist try to find it
    @param item: tipo item
    @type item: Item
    """
    if not item.infoLabels['tmdb_id']:
        listsources = [(item.infoLabels['tvdb_id'], "tvdb_id")]
        if item.infoLabels['imdb_id']:
            listsources.append((item.infoLabels['imdb_id'], "imdb_id"))

        from core.tmdb import Tmdb
        ob = Tmdb()

        for external_id, external_source in listsources:
            ob.search_by_id(id=external_id, source=external_source, tipo='tv')

            item.infoLabels['tmdb_id'] = ob.get_id()
            if item.infoLabels['tmdb_id']:
                url_scraper = "https://www.themoviedb.org/tv/%s" % item.infoLabels['tmdb_id']
                item.infoLabels['url_scraper'].append(url_scraper)
                break


class Tvdb(object):
    def __init__(self, **kwargs):

        self.__check_token()

        self.result = {}
        self.list_results = []
        self.lang = ""
        self.search_name = kwargs['search'] = \
            re.sub(r'\[\\\?(B|I|COLOR)\s?[^\]]*\]', '', kwargs.get('search', ''))
        self.list_episodes = {}
        self.episodes = {}

        if kwargs.get('tvdb_id', ''):
            # Search by tvdb identifier
            self.__get_by_id(kwargs.get('tvdb_id', ''))
            if not self.list_results and config.get_setting("tvdb_retry_eng", "videolibrary"):
                from platformcode import platformtools
                platformtools.dialog_notification(config.get_localized_string(60299) % DEFAULT_LANG, config.get_localized_string(60302), sound=False)
                self.__get_by_id(kwargs.get('tvdb_id', ''), "en")
                self.lang = "en"

        elif self.search_name:
            # BUsqueda by text
            self.__search(kwargs.get('search', ''), kwargs.get('imdb_id', ''), kwargs.get('zap2it_id', ''))
            if not self.list_results and config.get_setting("tvdb_retry_eng", "videolibrary"):
                from platformcode import platformtools
                platformtools.dialog_notification(config.get_localized_string(60299) % DEFAULT_LANG, config.get_localized_string(60302))
                self.__search(kwargs.get('search', ''), kwargs.get('imdb_id', ''), kwargs.get('zap2it_id', ''), "en")
                self.lang = "en"

        if not self.result:
            # No search results
            if kwargs.get('tvdb_id', ''):
                buscando = kwargs.get('tvdb_id', '')
            else:
                buscando = kwargs.get('search', '')
            msg = config.get_localized_string(70266) % buscando
            logger.debug(msg)

    @classmethod
    def __check_token(cls):
        # logger.debug()
        if TOKEN == "":
            cls.__login()
        else:
            # if the date does not correspond to the current one we call refresh_token, since the token expires in 24 hours
            from time import gmtime, strftime
            current_date = strftime("%Y-%m-%d", gmtime())

            if config.get_setting("tvdb_token_date", "") != current_date:
                # if the token has been renewed we save the new date
                if cls.__refresh_token():
                    config.set_setting("tvdb_token_date", current_date)

    @staticmethod
    def __login():
        # logger.debug()
        global TOKEN

        apikey = "106B699FDC04301C"

        url = HOST + "/login"
        params = {"apikey": apikey}
        if PY3: params = jsontools.dump(params).encode()
        else: params = jsontools.dump(params)

        try:
            dict_html = requests.post(url, data=params, headers=DEFAULT_HEADERS).json()

        except Exception as ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error: %s" % message)

        else:
            if "token" in dict_html:
                token = dict_html["token"]
                DEFAULT_HEADERS["Authorization"] = "Bearer " + token

                TOKEN = config.set_setting("tvdb_token", token)

    @classmethod
    def __refresh_token(cls):
        # logger.debug()
        global TOKEN
        is_success = False

        url = HOST + "/refresh_token"
        try:
            req = requests.get(url, headers=DEFAULT_HEADERS)


        except req as err:
            logger.error("err.code %s" % err.status_code)
            # if there is error 401 it is that the token has passed the time and we have to call login again
            if err.status_code == 401:
                cls.__login()
            else:
                raise

        except Exception as ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error: %s" % message)

        else:
            dict_html = req.json()
            # logger.error("tokencito %s" % dict_html)
            if "token" in dict_html:
                token = dict_html["token"]
                DEFAULT_HEADERS["Authorization"] = "Bearer " + token
                TOKEN = config.set_setting("tvdb_token", token)
                is_success = True
            else:
                cls.__login()

        return is_success

    def get_info_episode(self, _id, season=1, episode=1, lang=DEFAULT_LANG, id_episode=None):
        """
        Returns the data of an episode.
        @param _id: series identifier
        @type _id: str
        @param season: season number [default = 1]
        @type season: int
        @param episode: episode number [default = 1]
        @type episode: int
        @param lang: language code to search
        @type lang: str
        @param id_episode: episode code.
        @type id_episode: int
        @rtype: dict
        @return:
        "data": {
                    "id": 0,
                    "airedSeason": 0,
                    "airedEpisodeNumber": 0,
                    "episodeName": "string",
                    "firstAired": "string",
                    "guestStars": [
                        "string"
                    ],
                    "director": "string", # deprecated
                    "directors": [
                        "string"
                    ],
                    "writers": [
                        "string"
                    ],
                    "overview": "string",
                    "productionCode": "string",
                    "showUrl": "string",
                    "lastUpdated": 0,
                    "dvdDiscid": "string",
                    "dvdSeason": 0,
                    "dvdEpisodeNumber": 0,
                    "dvdChapter": 0,
                    "absoluteNumber": 0,
                    "filename": "string",
                    "seriesId": "string",
                    "lastUpdatedBy": "string",
                    "airsAfterSeason": 0,
                    "airsBeforeSeason": 0,
                    "airsBeforeEpisode": 0,
                    "thumbAuthor": 0,
                    "thumbAdded": "string",
                    "thumbWidth": "string",
                    "thumbHeight": "string",
                    "imdbId": "string",
                    "siteRating": 0,
                    "siteRatingCount": 0
                },
        "errors": {
            "invalidFilters": [
                "string"
            ],
            "invalidLanguage": "string",
            "invalidQueryParams": [
                "string"
            ]
        }
        """
        logger.debug()
        if id_episode and self.episodes.get(id_episode):
            return self.episodes.get(id_episode)

        params = {"airedSeason": "%s" % season, "airedEpisode": "%s" % episode}

        try:
            params = urllib.parse.urlencode(params)

            url = HOST + "/series/%s/episodes/query?%s" % (_id, params)
            DEFAULT_HEADERS["Accept-Language"] = lang
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            req = requests.get(url, headers=DEFAULT_HEADERS)

        except Exception as ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error: %s" % message)

        else:
            dict_html = req.json()
            if 'Error' in dict_html:
                logger.debug("code %s " % dict_html['Error'])
            if "data" in dict_html and "id" in dict_html["data"][0]:
                self.get_episode_by_id(dict_html["data"][0]["id"], lang)
                return dict_html["data"]

    def get_list_episodes(self, _id, page=1):
        """
        Returns the list of episodes of a series.
        @param _id: series identifier
        @type _id: str
        @param page: page number to search [default = 1]
        @type page: int
        @rtype: dict
        @return:
        {
            "links": {
                "first": 0,
                "last": 0,
                "next": 0,
                "previous": 0
              },
            "data": [
                {
                    "absoluteNumber": 0,
                    "airedEpisodeNumber": 0,
                    "airedSeason": 0,
                    "dvdEpisodeNumber": 0,
                    "dvdSeason": 0,
                    "episodeName": "string",
                    "id": 0,
                    "overview": "string",
                    "firstAired": "string",
                    "lastUpdated": 0
                }
            ],
            "errors": {
                "invalidFilters": [
                  "string"
                ],
                "invalidLanguage": "string",
                "invalidQueryParams": [
                  "string"
                ]
            }
        }
        """
        logger.debug()


        url = HOST + "/series/%s/episodes?page=%s" % (_id, page)
        logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))
        js = requests.get(url, headers=DEFAULT_HEADERS).json()
        self.list_episodes[page] = js if 'Error' not in js else {}
        return self.list_episodes[page]

    def get_episode_by_id(self, _id, lang=DEFAULT_LANG, semaforo=None):
        """
        Get the data of an episode
        @param _id: episode identifier
        @type _id: str
        @param lang: language code
        @param semaforo: semaphore for multihilos
        @type semaforo: threading.Semaphore
        @type lang: str
        @rtype: dict
        @return:
        {
            "data": {
                "id": 0,
                "airedSeason": 0,
                "airedEpisodeNumber": 0,
                "episodeName": "string",
                "firstAired": "string",
                "guestStars": [
                  "string"
                ],
                "director": "string",
                "directors": [
                  "string"
                ],
                "writers": [
                  "string"
                ],
                "overview": "string",
                "productionCode": "string",
                "showUrl": "string",
                "lastUpdated": 0,
                "dvdDiscid": "string",
                "dvdSeason": 0,
                "dvdEpisodeNumber": 0,
                "dvdChapter": 0,
                "absoluteNumber": 0,
                "filename": "string",
                "seriesId": "string",
                "lastUpdatedBy": "string",
                "airsAfterSeason": 0,
                "airsBeforeSeason": 0,
                "airsBeforeEpisode": 0,
                "thumbAuthor": 0,
                "thumbAdded": "string",
                "thumbWidth": "string",
                "thumbHeight": "string",
                "imdbId": "string",
                "siteRating": 0,
                "siteRatingCount": 0
            },
            "errors": {
            "invalidFilters": [
              "string"
            ],
            "invalidLanguage": "string",
            "invalidQueryParams": [
              "string"
            ]
            }
        }
        """
        if semaforo:
            semaforo.acquire()
        logger.debug()

        url = HOST + "/episodes/%s" % _id

        # from core.support import dbg;dbg()

        try:
            DEFAULT_HEADERS["Accept-Language"] = lang
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))
            req = requests.get(url, headers=DEFAULT_HEADERS)

        except Exception as ex:
            # if isinstance(ex, urllib).HTTPError:
            logger.debug("code %s " % ex)
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

        else:
            dict_html = req.json()
            # logger.debug("dict_html %s" % dict_html)
            self.episodes[_id] = dict_html.pop("data") if 'Error' not in dict_html else {}

        if semaforo:
            semaforo.release()

    def __search(self, name, imdb_id, zap2it_id, lang=DEFAULT_LANG):
        """
        Search for a series through a series of parameters.
        @param name: name to search
        @type name: str
        @param imdb_id: imdb identification code
        @type imdb_id: str
        @param zap2it_id: zap2it identification code
        @type zap2it_id: str
        @param lang: language code
        @type lang: str

        data:{
          "aliases": [
            "string"
          ],
          "banner": "string",
          "firstAired": "string",
          "id": 0,
          "network": "string",
          "overview": "string",
          "seriesName": "string",
          "status": "string"
        }
        """
        logger.debug()

        params = {}
        if name:
            params["name"] = name
        elif imdb_id:
            params["imdbId"] = imdb_id
        elif zap2it_id:
            params["zap2itId"] = zap2it_id

        params = urllib.parse.urlencode(params)

        DEFAULT_HEADERS["Accept-Language"] = lang
        url = HOST + "/search/series?%s" % params
        logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

        dict_html =  requests.get(url, headers=DEFAULT_HEADERS).json()


        if 'Error' in dict_html:
            # if isinstance(ex, urllib.parse).HTTPError:
            logger.debug("code %s " % dict_html['Error'])

        else:

            if "errors" in dict_html and "invalidLanguage" in dict_html["errors"]:
                # no hay información en idioma por defecto
                return

            else:
                resultado = dict_html["data"]

                # todo revisar
                if len(resultado) > 1:
                    index = 0
                else:
                    index = 0

                logger.debug("result %s" % resultado)
                self.list_results = resultado
                self.result = resultado[index]

    def __get_by_id(self, _id, lang=DEFAULT_LANG, from_get_list=False):
        """
        Gets the data for a string by identifier.
        @param _id: series code
        @type _id: str
        @param lang: language code
        @type lang: str
        @rtype: dict
        @return:
        {
        "data": {
            "id": 0,
            "seriesName": "string",
            "aliases": [
              "string"
            ],
            "banner": "string",
            "seriesId": 0,
            "status": "string",
            "firstAired": "string",
            "network": "string",
            "networkId": "string",
            "runtime": "string",
            "genre": [
              "string"
            ],
            "overview": "string",
            "lastUpdated": 0,
            "airsDayOfWeek": "string",
            "airsTime": "string",
            "rating": "string",
            "imdbId": "string",
            "zap2itId": "string",
            "added": "string",
            "siteRating": 0,
            "siteRatingCount": 0
        },
        "errors": {
            "invalidFilters": [
              "string"
            ],
            "invalidLanguage": "string",
            "invalidQueryParams": [
              "string"
            ]
            }
        }
        """
        logger.debug()
        resultado = {}

        url = HOST + "/series/%s" % _id

        try:
            DEFAULT_HEADERS["Accept-Language"] = lang
            req = requests.get(url, headers=DEFAULT_HEADERS)
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

        except Exception as ex:
            # if isinstance(ex, urllib).HTTPError:
            logger.debug("code %s " % ex)

            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error: %s" % message)

        else:
            dict_html = req.json()
            if "Error" in dict_html and "invalidLanguage" in dict_html["Error"]:
                return {}
            resultado1 = dict_html["data"]
            if not resultado1 and from_get_list:
                return self.__get_by_id(_id, "en")

            logger.debug("Result %s" % dict_html)
            resultado2 = {"image_poster": [{'keyType': 'poster', 'fileName': 'posters/%s-1.jpg' % _id}]}
            resultado3 = {"image_fanart": [{'keyType': 'fanart', 'fileName': 'fanart/original/%s-1.jpg' % _id}]}

            resultado = resultado1.copy()
            resultado.update(resultado2)
            resultado.update(resultado3)

            logger.debug("total result %s" % resultado)
            self.list_results = [resultado]
            self.result = resultado

        return resultado

    def get_images(self, _id, image="poster", season=1, lang="en"):
        """
        Gets an image type for a string for a language.
        @param _id: series identifier
        @type _id: str
        @param image: search code, ["poster" (default), "fanart", "season"]
        @type image: str
        @type season: season number
        @param lang: language code for which you are searching
        @type lang: str
        @return: dictionary with the type of images chosen.
        @rtype: dict

        """
        logger.debug()

        if self.result.get('image_season_%s' % season):
            return self.result['image_season_%s' % season]

        params = {}
        if image == "poster":
            params["keyType"] = "poster"
        elif image == "fanart":
            params["keyType"] = "fanart"
            params["subKey"] = "graphical"
        elif image == "season":
            params["keyType"] = "season"
            params["subKey"] = "%s" % season
            image += "_%s" % season

        try:

            params = urllib.parse.urlencode(params)
            DEFAULT_HEADERS["Accept-Language"] = lang
            url = HOST + "/series/%s/images/query?%s" % (_id, params)
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            res = requests.get(url, headers=DEFAULT_HEADERS)

        except Exception as ex:
            # if isinstance(ex, urllib).HTTPError:
            logger.debug("code %s " % ex)

            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error: %s" % message)


        else:
            dict_html = res.json()
            if 'Error' in dict_html:
                # if isinstance(ex, urllib.parse).HTTPError:
                logger.debug("code %s " % dict_html['Error'])
            else:
                dict_html["image_" + image] = dict_html.pop("data")
                self.result.update(dict_html)

                return dict_html

    def get_tvshow_cast(self, _id, lang=DEFAULT_LANG):
        """
        gets casting for a series
        @param _id: series code
        @type _id: str
        @param lang: language code to search
        @type lang: str
        @return: dictionary with actors
        @rtype: dict
        """
        logger.debug()

        url = HOST + "/series/%s/actors" % _id
        DEFAULT_HEADERS["Accept-Language"] = lang
        logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))
        try:
            req = requests.get(url, headers=DEFAULT_HEADERS)
        except Exception as ex:
            logger.debug("code %s " % ex)
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)
        else:
            dict_html = req.json()
        if 'Error' in dict_html:
            logger.debug("code %s " % dict_html['Error'])
        else:
            dict_html["cast"] = dict_html.pop("data")
        self.result.update(dict_html)

    def get_id(self):
        """
        @return: Returns the Tvdb identifier of the loaded string or an empty string in case nothing was loaded.
        You can use this method to find out if a search has been successful or not.
        @rtype: str
        """
        return str(self.result.get('id', ""))

    def get_list_results(self):
        """
        Returns the results we found for a series.
        @rtype: list
        @return: list of results
        """
        logger.debug()
        list_results = []

        # if we have a result and it has seriesName, we already have the info of the series, it is not necessary to search again
        if len(self.list_results) == 1 and "seriesName" in self.result:
            list_results.append(self.result)
            info_load = True
        else:
            import threading
            semaforo = threading.Semaphore(20)
            l_hilo = list()
            r_list = list()

            def sub_thread(_id, i):
                semaforo.acquire()
                ret = self.__get_by_id(_id, DEFAULT_LANG, True)
                semaforo.release()
                r_list.append((ret, i))

            for index, e in enumerate(self.list_results):
                t = threading.Thread(target=sub_thread, args=(e["id"], index))
                t.start()
                l_hilo.append(t)

            for x in l_hilo:
                x.join()

            r_list.sort(key=lambda i: i[1])
            list_results = [ii[0] for ii in r_list]
            info_load = False
        return list_results, info_load

    def get_infoLabels(self, infoLabels=None, origen=None):
        """
        @param infoLabels: Extra information about the movie, series, season or chapter.
        @type infoLabels: dict
        @param origen: Diccionario origen de donde se obtiene los infoLabels, por omision self.result
        @type origen: dict
        @return: Returns the extra information obtained from the current object. If the infoLables parameter was passed,
        the value returned will be read as a parameter duly updated.
        @rtype: dict
        """

        if infoLabels:
            # logger.debug("es instancia de infoLabels")
            ret_infoLabels = InfoLabels(infoLabels)
        else:
            # logger.debug("NO ES instancia de infoLabels")
            ret_infoLabels = InfoLabels()
            # fix
            ret_infoLabels['mediatype'] = 'tvshow'

        # Start Listings
        l_castandrole = ret_infoLabels.get('castandrole', [])

        # logger.debug("self.result %s" % self.result)

        if not origen:
            origen = self.result

        ret_infoLabels['title'] = origen['seriesName']
        ret_infoLabels['tvdb_id'] = origen['id']
        thumbs = requests.get(HOST + '/series/' + str(origen['id']) + '/images/query?keyType=poster').json()
        if 'data' in thumbs:
            ret_infoLabels['thumbnail'] = HOST_IMAGE + thumbs['data'][0]['fileName']
        elif 'poster' in origen and origen['poster']:
            ret_infoLabels['thumbnail'] = HOST_IMAGE + origen['poster']
        fanarts = requests.get(HOST + '/series/' + str(origen['id']) + '/images/query?keyType=fanart').json()
        if 'data' in fanarts:
            ret_infoLabels['fanart'] = HOST_IMAGE + fanarts['data'][0]['fileName']
        elif 'fanart' in origen and origen['fanart']:
            ret_infoLabels['fanart'] = HOST_IMAGE + origen['fanart']
        if 'overview' in origen and origen['overview']:
            ret_infoLabels['plot'] = origen['overview']
        if 'duration' in origen and origen['duration']:
            ret_infoLabels['duration'] = int(origen['duration']) * 60
        if 'firstAired' in origen and origen['firstAired']:
            ret_infoLabels['year'] = int(origen['firstAired'][:4])
            ret_infoLabels['premiered'] = origen['firstAired'].split("-")[2] + "/" + origen['firstAired'].split("-")[1] + "/" + origen['firstAired'].split("-")[0]
        if 'siteRating' in origen and origen['siteRating']:
            ret_infoLabels['rating'] = float(origen['siteRating'])
        if 'siteRatingCount' in origen and origen['siteRatingCount']:
            ret_infoLabels['votes'] = origen['siteRatingCount']
        if 'status' in origen and origen['status']:
            ret_infoLabels['status'] = origen['status']
        if 'network' in origen and origen['network']:
            ret_infoLabels['studio'] = origen['network']
        if 'imdbId' in origen and origen['rating']:
            ret_infoLabels['imdb_id'] = origen['imdbId']
        if 'rating' in origen and origen['rating']:
            ret_infoLabels['mpaa'] = origen['rating']
        if 'genre' in origen and origen['genre']:
            for genre in origen['genre']:
                genre_list = ""
                genre_list += genre + ', '
                ret_infoLabels['genre'] = genre_list.rstrip(', ')
        if 'cast' in origen and origen['cast']:
            dic_aux = dict((name, character) for (name, character) in l_castandrole)
            l_castandrole.extend([(p['name'], p['role']) for p in origen['cast'] if p['name'] not in list(dic_aux.keys())])
            ret_infoLabels['castandrole'] = l_castandrole


        return ret_infoLabels
