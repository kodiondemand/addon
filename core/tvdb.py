# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# tvdb
# ------------------------------------------------------------
# Scraper para el site thetvdb.com usando API v2.1
# Utilizado para obtener datos de series para la videoteca
# del addon y también Kodi.
# ------------------------------------------------------------

import re

import urllib2

from core import jsontools
from core import scrapertools
from core.item import InfoLabels
from platformcode import config, logger
from platformcode import platformtools

HOST = "https://api.thetvdb.com"
HOST_IMAGE = "http://thetvdb.com/banners/"

import xbmcaddon
addon = xbmcaddon.Addon('metadata.tvdb.com')

TOKEN = config.get_setting("tvdb_token", default="")
DEFAULT_LANG = addon.getSetting('language')
DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, application/vnd.thetvdb.v2.1.1',
    'Accept-Language': DEFAULT_LANG,
    'Authorization': 'Bearer ' + TOKEN,
}

# Traducciones - Inicio
DICT_STATUS = {'Continuing': 'En emisión', 'Ended': 'Finalizada'}
DICT_GENRE = {
    'Action': 'Acción',
    'Adventure': 'Aventura',
    'Animation': 'Animación',
    'Children': 'Niños',
    'Comedy': 'Comedia',
    'Crime': 'Crimen',
    'Documentary': 'Documental',
    # 'Drama': 'Drama',
    'Family': 'Familiar',
    'Fantasy': 'Fantasía',
    'Food': 'Comida',
    'Game Show': 'Concurso',
    'Home and Garden': 'Hogar y Jardín',
    # 'Horror': 'Horror', 'Mini-Series': 'Mini-Series',
    'Mystery': 'Misterio',
    'News': 'Noticias',
    # 'Reality': 'Telerrealidad',
    'Romance': 'Romántico',
    'Science-Fiction': 'Ciencia-Ficción',
    'Soap': 'Telenovela',
    # 'Special Interest': 'Special Interest',
    'Sport': 'Deporte',
    # 'Suspense': 'Suspense',
    'Talk Show': 'Programa de Entrevistas',
    # 'Thriller': 'Thriller',
    'Travel': 'Viaje',
    # 'Western': 'Western'
}
DICT_MPAA = {'TV-Y': 'Público pre-infantil: niños menores de 6 años', 'TV-Y7': 'Público infantil: desde 7 años',
             'TV-G': 'Público general: sin supervisión familiar', 'TV-PG': 'Guía paterna: Supervisión paternal',
             'TV-14': 'Mayores de 14 años', 'TV-MA': 'Mayores de 17 años'}
# Traducciones - Fin

otvdb_global = None


def find_and_set_infoLabels(item):
    logger.info()
    # logger.info("item es %s" % item)

    p_dialog = None
    if not item.contentSeason:
        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(60296), config.get_localized_string(60293))

    global otvdb_global
    tvdb_result = None

    title = item.contentSerieName
    # Si el titulo incluye el (año) se lo quitamos
    year = scrapertools.find_single_match(title, "^.+?\s*(\(\d{4}\))$")
    if year:
        title = title.replace(year, "").strip()
        item.infoLabels['year'] = year[1:-1]

    if not item.infoLabels.get("tvdb_id"):
        if not item.infoLabels.get("imdb_id"):
            otvdb_global = Tvdb(search=title, year=item.infoLabels['year'])
        else:
            otvdb_global = Tvdb(imdb_id=item.infoLabels.get("imdb_id"))

    elif not otvdb_global or otvdb_global.get_id() != item.infoLabels['tvdb_id']:
        otvdb_global = Tvdb(tvdb_id=item.infoLabels['tvdb_id'])

    if not item.contentSeason:
        p_dialog.update(50, config.get_localized_string(60296), config.get_localized_string(60295))
    results, info_load = otvdb_global.get_list_results()
    logger.debug("results es %s" % results)

    if not item.contentSeason:
        p_dialog.update(100, config.get_localized_string(60296), config.get_localized_string(60297) % len(results))
        p_dialog.close()

    if len(results) > 1:
        tvdb_result = platformtools.show_video_info(results, item=item, scraper=Tvdb,
                                                    caption=config.get_localized_string(60298) % title)
    elif len(results) > 0:
        tvdb_result = results[0]

    # todo revisar
    if isinstance(item.infoLabels, InfoLabels):
        logger.debug("es instancia de infoLabels")
        infoLabels = item.infoLabels
    else:
        logger.debug("NO ES instancia de infoLabels")
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
        Obtiene y fija (item.infoLabels) los datos extras de una serie, capitulo o pelicula.
        @param item: Objeto que representa un pelicula, serie o capitulo. El atributo infoLabels sera modificado
            incluyendo los datos extras localizados.
        @type item: Item


    """
    global otvdb_global

    def __leer_datos(otvdb_aux):
        item.infoLabels = otvdb_aux.get_infoLabels(item.infoLabels)
        if 'infoLabels' in item and 'thumbnail' in item.infoLabels:
            item.thumbnail = item.infoLabels['thumbnail']
        if 'infoLabels' in item and 'fanart' in item.infoLabels['fanart']:
            item.fanart = item.infoLabels['fanart']

    if 'infoLabels' in item and 'season' in item.infoLabels:
        try:
            int_season = int(item.infoLabels['season'])
        except ValueError:
            logger.debug("El numero de temporada no es valido")
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
                logger.debug("El número de episodio (%s) no es valido" % repr(item.infoLabels['episode']))
                item.contentType = item.infoLabels['mediatype']
                return -1 * len(item.infoLabels)

            # Tenemos numero de temporada y numero de episodio validos...
            # ... buscar datos episodio
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

                    # esperar q todos los hilos terminen
                    for x in l_hilo:
                        x.join()

                for e in list_episodes['data']:
                    if e['airedSeason'] == int_season and e['airedEpisodeNumber'] == int_episode:
                        _id = e['id']
                        break

                _next = list_episodes['links']['next']
                if type(_next) == int:
                    page = _next
                else:
                    break

            data_episode = otvdb_global.get_info_episode(otvdb_global.get_id(), int_season, int_episode, lang, _id)

            # todo repasar valores que hay que insertar en infoLabels
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

                # datos para nfo
                item.season_id = data_episode["airedSeasonID"]
                item.episode_id = data_episode["id"]

                return len(item.infoLabels)

        else:
            # Tenemos numero de temporada valido pero no numero de episodio...
            # ... buscar datos temporada
            item.infoLabels['mediatype'] = 'season'
            data_season = otvdb_global.get_images(otvdb_global.get_id(), "season", int_season)

            if data_season and 'image_season_%s' % int_season in data_season:
                item.thumbnail = HOST_IMAGE + data_season['image_season_%s' % int_season][0]['fileName']
                return len(item.infoLabels)

    # Buscar...
    else:
        # Busquedas por ID...
        if (not otvdb_global or otvdb_global.get_id() != item.infoLabels['tvdb_id']) and item.infoLabels['tvdb_id']:
            otvdb_global = Tvdb(tvdb_id=item.infoLabels['tvdb_id'])

        elif not otvdb_global and item.infoLabels['imdb_id']:
            otvdb_global = Tvdb(imdb_id=item.infoLabels['imdb_id'])

        elif not otvdb_global and item.infoLabels['zap2it_id']:
            otvdb_global = Tvdb(zap2it_id=item.infoLabels['zap2it_id'])

        # No se ha podido buscar por ID... se hace por título
        if otvdb_global is None:
            otvdb_global = Tvdb(search=item.infoLabels['tvshowtitle'])

        if otvdb_global and otvdb_global.get_id():
            __leer_datos(otvdb_global)
            # La busqueda ha encontrado un resultado valido
            return len(item.infoLabels)


def get_nfo(item):
    """
    Devuelve la información necesaria para que se scrapee el resultado en la videoteca de kodi,

    @param item: elemento que contiene los datos necesarios para generar la info
    @type item: Item
    @rtype: str
    @return:
    """

    if "season" in item.infoLabels and "episode" in item.infoLabels:
        info_nfo = "http://thetvdb.com/?tab=episode&seriesid=%s&seasonid=%s&id=%s\n" \
                   % (item.infoLabels['tvdb_id'], item.season_id, item.episode_id)
    else:
        info_nfo = ', '.join(item.infoLabels['url_scraper']) + "\n"

    return info_nfo


def completar_codigos(item):
    """
    Si es necesario comprueba si existe el identificador de tmdb y sino existe trata de buscarlo
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


class Tvdb:
    def __init__(self, **kwargs):

        self.__check_token()

        self.result = {}
        self.list_results = []
        self.lang = ""
        self.search_name = kwargs['search'] = \
            re.sub('\[\\\?(B|I|COLOR)\s?[^\]]*\]', '', kwargs.get('search', ''))
        self.list_episodes = {}
        self.episodes = {}

        if kwargs.get('tvdb_id', ''):
            # Busqueda por identificador tvdb
            self.__get_by_id(kwargs.get('tvdb_id', ''))
            if not self.list_results and config.get_setting("tvdb_retry_eng", "videolibrary"):
                from platformcode import platformtools
                platformtools.dialog_notification(config.get_localized_string(60299) % DEFAULT_LANG,
                                                  config.get_localized_string(60302), sound=False)
                self.__get_by_id(kwargs.get('tvdb_id', ''), "en")
                self.lang = "en"

        elif self.search_name:
            # Busqueda por texto
            self.__search(kwargs.get('search', ''), kwargs.get('imdb_id', ''), kwargs.get('zap2it_id', ''))
            if not self.list_results and config.get_setting("tvdb_retry_eng", "videolibrary"):
                from platformcode import platformtools
                platformtools.dialog_notification(config.get_localized_string(60299) % DEFAULT_LANG,
                                                  config.get_localized_string(60302))
                self.__search(kwargs.get('search', ''), kwargs.get('imdb_id', ''), kwargs.get('zap2it_id', ''), "en")
                self.lang = "en"

        if not self.result:
            # No hay resultados de la busqueda
            if kwargs.get('tvdb_id', ''):
                buscando = kwargs.get('tvdb_id', '')
            else:
                buscando = kwargs.get('search', '')
            msg = config.get_localized_string(70266) % buscando
            logger.debug(msg)

    @classmethod
    def __check_token(cls):
        # logger.info()
        if TOKEN == "":
            cls.__login()
        else:
            # si la fecha no se corresponde con la actual llamamos a refresh_token, ya que el token expira en 24 horas
            from time import gmtime, strftime
            current_date = strftime("%Y-%m-%d", gmtime())

            if config.get_setting("tvdb_token_date", "") != current_date:
                # si se ha renovado el token grabamos la nueva fecha
                if cls.__refresh_token():
                    config.set_setting("tvdb_token_date", current_date)

    @staticmethod
    def __login():
        # logger.info()
        global TOKEN

        apikey = "106B699FDC04301C"

        url = HOST + "/login"
        params = {"apikey": apikey}

        try:
            req = urllib2.Request(url, data=jsontools.dump(params), headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

        else:
            dict_html = jsontools.load(html)
            # logger.debug("dict_html %s" % dict_html)

            if "token" in dict_html:
                token = dict_html["token"]
                DEFAULT_HEADERS["Authorization"] = "Bearer " + token

                TOKEN = config.set_setting("tvdb_token", token)

    @classmethod
    def __refresh_token(cls):
        # logger.info()
        global TOKEN
        is_success = False

        url = HOST + "/refresh_token"

        try:
            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except urllib2.HTTPError, err:
            logger.error("err.code es %s" % err.code)
            # si hay error 401 es que el token se ha pasado de tiempo y tenemos que volver a llamar a login
            if err.code == 401:
                cls.__login()
            else:
                raise

        except Exception, ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

        else:
            dict_html = jsontools.load(html)
            # logger.error("tokencito %s" % dict_html)
            if "token" in dict_html:
                token = dict_html["token"]
                DEFAULT_HEADERS["Authorization"] = "Bearer " + token
                TOKEN = config.set_setting("tvdb_token", token)
                is_success = True

        return is_success

    def get_info_episode(self, _id, season=1, episode=1, lang=DEFAULT_LANG, id_episode=None):
        """
        Devuelve los datos de un episodio.
        @param _id: identificador de la serie
        @type _id: str
        @param season: numero de temporada [por defecto = 1]
        @type season: int
        @param episode: numero de episodio [por defecto = 1]
        @type episode: int
        @param lang: codigo de idioma para buscar
        @type lang: str
        @param id_episode: codigo del episodio.
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
        logger.info()
        if id_episode and self.episodes.get(id_episode):
            return self.episodes.get(id_episode)

        params = {"airedSeason": "%s" % season, "airedEpisode": "%s" % episode}

        try:
            import urllib
            params = urllib.urlencode(params)

            url = HOST + "/series/%s/episodes/query?%s" % (_id, params)
            DEFAULT_HEADERS["Accept-Language"] = lang
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

        else:
            dict_html = jsontools.load(html)

            if "data" in dict_html and "id" in dict_html["data"][0]:
                self.get_episode_by_id(dict_html["data"][0]["id"], lang)
                return dict_html["data"]

    def get_list_episodes(self, _id, page=1):
        """
        Devuelve el listado de episodios de una serie.
        @param _id: identificador de la serie
        @type _id: str
        @param page: numero de pagina a buscar [por defecto = 1]
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
        logger.info()

        try:
            url = HOST + "/series/%s/episodes?page=%s" % (_id, page)
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

        else:
            self.list_episodes[page] = jsontools.load(html)

            # logger.info("dict_html %s" % self.list_episodes)

            return self.list_episodes[page]

    def get_episode_by_id(self, _id, lang=DEFAULT_LANG, semaforo=None):
        """
        Obtiene los datos de un episodio
        @param _id: identificador del episodio
        @type _id: str
        @param lang: código de idioma
        @param semaforo: semaforo para multihilos
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
        logger.info()

        url = HOST + "/episodes/%s" % _id

        try:
            DEFAULT_HEADERS["Accept-Language"] = lang
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))
            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            if type(ex) == urllib2.HTTPError:
                logger.debug("code es %s " % ex.code)

            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

        else:
            dict_html = jsontools.load(html)
            dict_html = dict_html.pop("data")

            logger.info("dict_html %s" % dict_html)
            self.episodes[_id] = dict_html

        if semaforo:
            semaforo.release()

    def __search(self, name, imdb_id, zap2it_id, lang=DEFAULT_LANG):
        """
        Busca una serie a través de una serie de parámetros.
        @param name: nombre a buscar
        @type name: str
        @param imdb_id: codigo identificativo de imdb
        @type imdb_id: str
        @param zap2it_id: codigo identificativo de zap2it
        @type zap2it_id: str
        @param lang: código de idioma
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
        logger.info()

        try:

            params = {}
            if name:
                params["name"] = name
            elif imdb_id:
                params["imdbId"] = imdb_id
            elif zap2it_id:
                params["zap2itId"] = zap2it_id

            import urllib
            params = urllib.urlencode(params)

            DEFAULT_HEADERS["Accept-Language"] = lang
            url = HOST + "/search/series?%s" % params
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            if type(ex) == urllib2.HTTPError:
                logger.debug("code es %s " % ex.code)

            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

        else:
            dict_html = jsontools.load(html)

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

                logger.debug("resultado %s" % resultado)
                self.list_results = resultado
                self.result = resultado[index]

    def __get_by_id(self, _id, lang=DEFAULT_LANG, from_get_list=False):
        """
        Obtiene los datos de una serie por identificador.
        @param _id: código de la serie
        @type _id: str
        @param lang: código de idioma
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
        logger.info()
        resultado = {}

        url = HOST + "/series/%s" % _id

        try:
            DEFAULT_HEADERS["Accept-Language"] = lang
            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            if type(ex) == urllib2.HTTPError:
                logger.debug("code es %s " % ex.code)

            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

        else:
            dict_html = jsontools.load(html)

            if "errors" in dict_html and "invalidLanguage" in dict_html["errors"]:
                return {}
            else:
                resultado1 = dict_html["data"]
                if not resultado1 and from_get_list:
                    return self.__get_by_id(_id, "en")

                logger.debug("resultado %s" % dict_html)
                resultado2 = {"image_poster": [{'keyType': 'poster', 'fileName': 'posters/%s-1.jpg' % _id}]}
                resultado3 = {"image_fanart": [{'keyType': 'fanart', 'fileName': 'fanart/original/%s-1.jpg' % _id}]}

                resultado = resultado1.copy()
                resultado.update(resultado2)
                resultado.update(resultado3)

                logger.debug("resultado total %s" % resultado)
                self.list_results = [resultado]
                self.result = resultado

        return resultado

    def get_images(self, _id, image="poster", season=1, lang="en"):
        """
        Obtiene un tipo de imagen para una serie para un idioma.
        @param _id: identificador de la serie
        @type _id: str
        @param image: codigo de busqueda, ["poster" (por defecto), "fanart", "season"]
        @type image: str
        @type season: numero de temporada
        @param lang: código de idioma para el que se busca
        @type lang: str
        @return: diccionario con el tipo de imagenes elegidas.
        @rtype: dict

        """
        logger.info()

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

            import urllib
            params = urllib.urlencode(params)
            DEFAULT_HEADERS["Accept-Language"] = lang
            url = HOST + "/series/%s/images/query?%s" % (_id, params)
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error en: %s" % message)

            return {}

        else:
            dict_html = jsontools.load(html)

            dict_html["image_" + image] = dict_html.pop("data")
            self.result.update(dict_html)

            return dict_html

    def get_tvshow_cast(self, _id, lang=DEFAULT_LANG):
        """
        obtiene el casting de una serie
        @param _id: codigo de la serie
        @type _id: str
        @param lang: codigo idioma para buscar
        @type lang: str
        @return: diccionario con los actores
        @rtype: dict
        """
        logger.info()

        url = HOST + "/series/%s/actors" % _id
        DEFAULT_HEADERS["Accept-Language"] = lang
        logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

        req = urllib2.Request(url, headers=DEFAULT_HEADERS)
        response = urllib2.urlopen(req)
        html = response.read()
        response.close()

        dict_html = jsontools.load(html)

        dict_html["cast"] = dict_html.pop("data")
        self.result.update(dict_html)

    def get_id(self):
        """
        @return: Devuelve el identificador Tvdb de la serie cargada o una cadena vacia en caso de que no
            hubiese nada cargado. Se puede utilizar este metodo para saber si una busqueda ha dado resultado o no.
        @rtype: str
        """
        return str(self.result.get('id', ""))

    def get_list_results(self):
        """
        Devuelve los resultados encontramos para una serie.
        @rtype: list
        @return: lista de resultados
        """
        logger.info()
        list_results = []

        # TODO revisar condicion
        # si tenemos un resultado y tiene seriesName, ya tenemos la info de la serie, no hace falta volver a buscar
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
        @param infoLabels: Informacion extra de la pelicula, serie, temporada o capitulo.
        @type infoLabels: dict
        @param origen: Diccionario origen de donde se obtiene los infoLabels, por omision self.result
        @type origen: dict
        @return: Devuelve la informacion extra obtenida del objeto actual. Si se paso el parametro infoLables, el valor
        devuelto sera el leido como parametro debidamente actualizado.
        @rtype: dict
        """

        # TODO revisar
        if infoLabels:
            # logger.debug("es instancia de infoLabels")
            ret_infoLabels = InfoLabels(infoLabels)
        else:
            # logger.debug("NO ES instancia de infoLabels")
            ret_infoLabels = InfoLabels()
            # fix
            ret_infoLabels['mediatype'] = 'tvshow'

        # Iniciar listados
        l_castandrole = ret_infoLabels.get('castandrole', [])

        # logger.debug("self.result %s" % self.result)

        if not origen:
            origen = self.result

        # todo revisar
        # if 'credits' in origen.keys():
        #     dic_origen_credits = origen['credits']
        #     origen['credits_cast'] = dic_origen_credits.get('cast', [])
        #     origen['credits_crew'] = dic_origen_credits.get('crew', [])
        #     del origen['credits']

        items = origen.items()

        for k, v in items:
            if not v:
                continue

            if k == 'overview':
                ret_infoLabels['plot'] = v

            elif k == 'runtime':
                ret_infoLabels['duration'] = int(v) * 60

            elif k == 'firstAired':
                ret_infoLabels['year'] = int(v[:4])
                ret_infoLabels['premiered'] = v.split("-")[2] + "/" + v.split("-")[1] + "/" + v.split("-")[0]

            # todo revisar
            # elif k == 'original_title' or k == 'original_name':
            #     ret_infoLabels['originaltitle'] = v

            elif k == 'siteRating':
                ret_infoLabels['rating'] = float(v)

            elif k == 'siteRatingCount':
                ret_infoLabels['votes'] = v

            elif k == 'status':
                # se traduce los estados de una serie
                ret_infoLabels['status'] = DICT_STATUS.get(v, v)

            # no soy partidario de poner la cadena como studio pero es como lo hace el scraper de manera genérica
            elif k == 'network':
                ret_infoLabels['studio'] = v

            elif k == 'image_poster':
                # obtenemos la primera imagen de la lista
                ret_infoLabels['thumbnail'] = HOST_IMAGE + v[0]['fileName']

            elif k == 'image_fanart':
                # obtenemos la primera imagen de la lista
                ret_infoLabels['fanart'] = HOST_IMAGE + v[0]['fileName']

            # # no disponemos de la imagen de fondo
            # elif k == 'banner':
            #     ret_infoLabels['fanart'] = HOST_IMAGE + v

            elif k == 'id':
                ret_infoLabels['tvdb_id'] = v

            elif k == 'imdbId':
                ret_infoLabels['imdb_id'] = v
                # no se muestra
                # ret_infoLabels['code'] = v

            elif k in "rating":
                # traducimos la clasificación por edades (content rating system)
                ret_infoLabels['mpaa'] = DICT_MPAA.get(v, v)

            elif k in "genre":
                genre_list = ""
                for index, i in enumerate(v):
                    if index > 0:
                        genre_list += ", "

                    # traducimos los generos
                    genre_list += DICT_GENRE.get(i, i)

                ret_infoLabels['genre'] = genre_list

            elif k == 'seriesName':  # or k == 'name' or k == 'title':
                # if len(origen.get('aliases', [])) > 0:
                #     ret_infoLabels['title'] = v + " " + origen.get('aliases', [''])[0]
                # else:
                #     ret_infoLabels['title'] = v
                # logger.info("el titulo es %s " % ret_infoLabels['title'])
                ret_infoLabels['title'] = v

            elif k == 'cast':
                dic_aux = dict((name, character) for (name, character) in l_castandrole)
                l_castandrole.extend([(p['name'], p['role']) for p in v if p['name'] not in dic_aux.keys()])

            else:
                logger.debug("Atributos no añadidos: %s=%s" % (k, v))
                pass

        # Ordenar las listas y convertirlas en str si es necesario
        if l_castandrole:
            ret_infoLabels['castandrole'] = l_castandrole

        logger.debug("ret_infoLabels %s" % ret_infoLabels)

        return ret_infoLabels
