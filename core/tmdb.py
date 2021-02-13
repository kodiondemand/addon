# -*- coding: utf-8 -*-

# from future import standard_library
# standard_library.install_aliases()
# from builtins import str
import datetime
import sys, requests
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                               # It is very slow in PY2. In PY3 it is native
else:
    import urllib                                               # We use the native of PY2 which is faster

from future.builtins import range
from future.builtins import object

import ast, copy, re, time

from core import filetools, httptools, jsontools, scrapertools
from core.item import InfoLabels
from platformcode import config, logger, platformtools

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]

# ------------------------------------------------- -------------------------------------------------- --------
# Set of functions related to infoLabels.
# version 1.0:
# Initial version
#
# Include:
#  - set_infoLabels (source, seekTmdb, search_language): Gets and sets (item.infoLabels) the extra data of one or several series, chapters or movies.
#  - set_infoLabels_item (item, seekTmdb, search_language): Gets and sets (item.infoLabels) the extra data of a series, chapter or movie.
#  - set_infoLabels_itemlist (item_list, seekTmdb, search_language): Gets and sets (item.infoLabels) the data extras from a list of series, chapters or movies.
#  - infoLabels_tostring (item): Returns a str with the list ordered with the item's infoLabels
#
# Usage:
#  - tmdb.set_infoLabels (item, seekTmdb = True)
#
# Get basic data from a movie:
# Before calling the set_infoLabels method the title to search for must be in item.contentTitle and the year in item.infoLabels ['year'].
#
# Obtain basic data from a series:
# Before calling the set_infoLabels method the title to search for must be in item.show or in item.contentSerieName.
#
# Get more data from a movie or series:
# After obtaining the basic data in item.infoLabels ['tmdb'] we will have the code of the series or movie.
# We could also directly set this code, if known, or use the corresponding code of:
# IMDB (in item.infoLabels ['IMDBNumber'] or item.infoLabels ['code'] or item.infoLabels ['imdb_id']), TVDB (only series, in item.infoLabels ['tvdb_id']),
# Freebase (series only, on item.infoLabels ['freebase_mid']), TVRage (series only, on item.infoLabels ['tvrage_id'])
#
# Get data from a season:
# Before calling the set_infoLabels method the series title must be in item.show or in item.contentSerieName,
# the series TMDB code must be in item.infoLabels ['tmdb'] (it can be set automatically by the basic data query)
# and the season number must be in item.infoLabels ['season'].
#
# Get data from an episode:
# Before calling the set_infoLabels method the series title must be in item.show or in item.contentSerieName,
# the TMDB code of the series must be in item.infoLabels ['tmdb'] (it can be set automatically using the basic data query),
# the season number must be in item.infoLabels ['season'] and the episode number must be in item.infoLabels ['episode'].
# ------------------------------------------------- -------------------------------------------------- -----------

otmdb_global = None
from core import db


# The function name is the name of the decorator and receives the function that decorates.
def cache_response(fn):
    logger.debug()

    # import time
    # start_time = time.time()

    def wrapper(*args, **kwargs):
        def check_expired(saved_date):
            valided = False

            cache_expire = config.get_setting("tmdb_cache_expire", default=0)
            current_date = datetime.datetime.now()
            elapsed = current_date - saved_date

            # 1 day
            if cache_expire == 0:
                if elapsed > datetime.timedelta(days=1):
                    valided = False
                else:
                    valided = True
            # 7 days
            elif cache_expire == 1:
                if elapsed > datetime.timedelta(days=7):
                    valided = False
                else:
                    valided = True

            # 15 days
            elif cache_expire == 2:
                if elapsed > datetime.timedelta(days=15):
                    valided = False
                else:
                    valided = True

            # 1 month - 30 days
            elif cache_expire == 3:
                # we do not take into account February or months with 31 days
                if elapsed > datetime.timedelta(days=30):
                    valided = False
                else:
                    valided = True
            # no expire
            elif cache_expire == 4:
                valided = True

            return valided

        result = {}
        try:

            # cache is not active
            if not config.get_setting("tmdb_cache", default=False) or not kwargs.get('cache', True):
                logger.debug('no cache')
                result = fn(*args)
            else:

                url = re.sub('&year=-', '', args[0])
                if PY3: url = str.encode(url)

                row = db['tmdb_cache'].get(url)

                if row and check_expired(row[1]):
                    result = row[0]

                # si no se ha obtenido información, llamamos a la funcion
                if not result:
                    result = fn(*args)
                    db['tmdb_cache'][url] = [result, datetime.datetime.now()]

            # elapsed_time = time.time() - start_time
            # logger.debug("TARDADO %s" % elapsed_time)

        # error getting data
        except Exception as ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error in: %s" % message)

        return result

    return wrapper


def set_infoLabels(source, seekTmdb=True, idioma_busqueda=def_lang, forced=False):
    """
    Depending on the data type of source, it obtains and sets (item.infoLabels) the extra data of one or more series, chapters or movies.

    @param source: variable that contains the information to set infoLabels
    @type source: list, item
    @param seekTmdb: if it is True, it searches www.themoviedb.org to obtain the data, otherwise it obtains the data of the Item itself.
    @type seekTmdb: bool
    @param idioma_busqueda: set the language value in case of search at www.themoviedb.org
    @type idioma_busqueda: str
    @return: a number or list of numbers with the result of the calls to set_infoLabels_item
    @rtype: int, list
    """

    if not config.get_setting('tmdb_active') and not forced:
        return

    start_time = time.time()
    if type(source) == list:
        ret = set_infoLabels_itemlist(source, seekTmdb, idioma_busqueda)
        logger.debug("The data of %i links were obtained in %f seconds" % (len(source), time.time() - start_time))
    else:
        ret = set_infoLabels_item(source, seekTmdb, idioma_busqueda)
        logger.debug("The data were obtained in %f seconds" % (time.time() - start_time))
    return ret


def set_infoLabels_itemlist(item_list, seekTmdb=False, idioma_busqueda=def_lang, forced=False):
    """
    Concurrently, it gets the data of the items included in the item_list.

    The API has a limit of 40 requests per IP every 10 '' and that is why the list should not have more than 30 items to ensure the proper functioning of this function.

    @param item_list: list of Item objects that represent movies, series or chapters. The infoLabels attribute of each Item object will be modified including the extra localized data.
    @type item_list: list
    @param seekTmdb: If it is True, it searches www.themoviedb.org to obtain the data, otherwise it obtains the data of the Item itself if they exist.
    @type seekTmdb: bool
    @param idioma_busqueda: Language code according to ISO 639-1, in case of search at www.themoviedb.org.
    @type idioma_busqueda: str

    @return: A list of numbers whose absolute value represents the number of elements included in the infoLabels attribute of each Item. This number will be positive if the data has been obtained from www.themoviedb.org and negative otherwise.
    @rtype: list
    """

    if not config.get_setting('tmdb_active') and not forced:
        return
    import threading

    threads_num = config.get_setting("tmdb_threads", default=20)
    semaforo = threading.Semaphore(threads_num)
    lock = threading.Lock()
    r_list = list()
    i = 0
    l_hilo = list()

    def sub_thread(_item, _i, _seekTmdb):
        semaforo.acquire()
        ret = set_infoLabels_item(_item, _seekTmdb, idioma_busqueda, lock)
        # logger.debug(str(ret) + "item: " + _item.tostring())
        semaforo.release()
        r_list.append((_i, _item, ret))

    for item in item_list:
        t = threading.Thread(target=sub_thread, args=(item, i, seekTmdb))
        t.start()
        i += 1
        l_hilo.append(t)

    # wait for all the threads to end
    for x in l_hilo:
        x.join()

    # Sort results list by call order to keep the same order q item_list
    r_list.sort(key=lambda i: i[0])

    # Rebuild and return list only with results of individual calls
    return [ii[2] for ii in r_list]


def set_infoLabels_item(item, seekTmdb=True, idioma_busqueda=def_lang, lock=None):
    """
    Gets and sets (item.infoLabels) the extra data of a series, chapter or movie.

    @param item: Item object that represents a movie, series or chapter. The infoLabels attribute will be modified including the extra localized data.
    @type item: Item
    @param seekTmdb: If it is True, it searches www.themoviedb.org to obtain the data, otherwise it obtains the data of the Item itself if they exist.
    @type seekTmdb: bool
    @param idioma_busqueda: Language code according to ISO 639-1, in case of search at www.themoviedb.org.
    @type idioma_busqueda: str
    @param lock: For use of threads when calling the 'set_infoLabels_itemlist' method
    @return: A number whose absolute value represents the number of elements included in the item.infoLabels attribute. This number will be positive if the data has been obtained from www.themoviedb.org and negative otherwise.
    @rtype: int
    """
    global otmdb_global

    def __leer_datos(otmdb_aux):
        item.infoLabels = otmdb_aux.get_infoLabels(item.infoLabels)
        if item.infoLabels['thumbnail']:
            item.thumbnail = item.infoLabels['thumbnail']
        if item.infoLabels['fanart']:
            item.fanart = item.infoLabels['fanart']

    if seekTmdb:
        def search(otmdb_global, tipo_busqueda):
            if item.infoLabels['season']:
                try:
                    numtemporada = int(item.infoLabels['season'])
                except ValueError:
                    logger.debug("The season number is not valid.")
                    return -1 * len(item.infoLabels)

                if lock:
                    lock.acquire()

                if not otmdb_global or (item.infoLabels['tmdb_id'] and str(otmdb_global.result.get("id")) != item.infoLabels['tmdb_id']) \
                        or (otmdb_global.texto_buscado and otmdb_global.texto_buscado != item.infoLabels['tvshowtitle']):
                    if item.infoLabels['tmdb_id']:
                        otmdb_global = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo_busqueda,
                                            idioma_busqueda=idioma_busqueda)
                    else:
                        otmdb_global = Tmdb(texto_buscado=item.infoLabels['tvshowtitle'], tipo=tipo_busqueda,
                                            idioma_busqueda=idioma_busqueda, year=item.infoLabels['year'])

                    __leer_datos(otmdb_global)

                # 4l3x87 - fix for overlap infoLabels if there is episode or season
                # if lock and lock.locked():
                #     lock.release()

                if item.infoLabels['episode']:
                    try:
                        episode = int(item.infoLabels['episode'])
                    except ValueError:
                        logger.debug("The episode number (%s) is not valid" % repr(item.infoLabels['episode']))
                        return -1 * len(item.infoLabels)

                    # We have valid season number and episode number...
                    # ... search episode data
                    item.infoLabels['mediatype'] = 'episode'
                    episodio = otmdb_global.get_episodio(numtemporada, episode)

                    if episodio:
                        # Update data
                        __leer_datos(otmdb_global)
                        item.infoLabels['title'] = episodio['episodio_titulo']
                        if episodio['episodio_sinopsis']:
                            item.infoLabels['plot'] = episodio['episodio_sinopsis']
                        if episodio['episodio_imagen']:
                            item.infoLabels['poster_path'] = episodio['episodio_imagen']
                            item.thumbnail = item.infoLabels['poster_path']
                        if episodio['episodio_air_date']:
                            item.infoLabels['aired'] = episodio['episodio_air_date']
                        if episodio['episodio_vote_average']:
                            item.infoLabels['rating'] = episodio['episodio_vote_average']
                            item.infoLabels['votes'] = episodio['episodio_vote_count']

                        # 4l3x87 - fix for overlap infoLabels if there is episode or season
                        if lock and lock.locked():
                            lock.release()

                        return len(item.infoLabels)

                else:
                    # We have a valid season number but no episode number...
                    # ... search season data
                    item.infoLabels['mediatype'] = 'season'
                    temporada = otmdb_global.get_temporada(numtemporada)
                    if not isinstance(temporada, dict):
                        temporada = ast.literal_eval(temporada.decode('utf-8'))

                    if temporada:
                        # Update data
                        __leer_datos(otmdb_global)
                        item.infoLabels['title'] = temporada['name'] if 'name' in temporada else ''
                        if 'overview' in temporada and temporada['overview']:
                            item.infoLabels['plot'] = temporada['overview']
                        if 'air_date' in temporada and temporada['air_date']:
                            date = temporada['air_date'].split('-')
                            item.infoLabels['aired'] = date[2] + "/" + date[1] + "/" + date[0]
                        if 'poster_path' in temporada and temporada['poster_path']:
                            item.infoLabels['poster_path'] = 'https://image.tmdb.org/t/p/original' + temporada['poster_path']
                            item.thumbnail = item.infoLabels['poster_path']

                        # 4l3x87 - fix for overlap infoLabels if there is episode or season
                        if lock and lock.locked():
                            lock.release()

                        return len(item.infoLabels)

                # 4l3x87 - fix for overlap infoLabels if there is episode or season
                if lock and lock.locked():
                    lock.release()

            # Search...
            else:
                otmdb = copy.copy(otmdb_global)
                # Search by ID...
                if item.infoLabels['tmdb_id']:
                    # ...Search for tmdb_id
                    otmdb = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo_busqueda,
                                 idioma_busqueda=idioma_busqueda)

                elif item.infoLabels['imdb_id']:
                    # ...Search by imdb code
                    otmdb = Tmdb(external_id=item.infoLabels['imdb_id'], external_source="imdb_id", tipo=tipo_busqueda,
                                 idioma_busqueda=idioma_busqueda)

                elif tipo_busqueda == 'tv':  # bsearch with other codes
                    if item.infoLabels['tvdb_id']:
                        # ...Search for tvdb_id
                        otmdb = Tmdb(external_id=item.infoLabels['tvdb_id'], external_source="tvdb_id",
                                     tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda)
                    elif item.infoLabels['freebase_mid']:
                        # ...Search for freebase_mid
                        otmdb = Tmdb(external_id=item.infoLabels['freebase_mid'], external_source="freebase_mid",
                                     tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda)
                    elif item.infoLabels['freebase_id']:
                        # ...Search by freebase_id
                        otmdb = Tmdb(external_id=item.infoLabels['freebase_id'], external_source="freebase_id",
                                     tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda)
                    elif item.infoLabels['tvrage_id']:
                        # ...Search by tvrage_id
                        otmdb = Tmdb(external_id=item.infoLabels['tvrage_id'], external_source="tvrage_id",
                                     tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda)

                # if otmdb is None:
                if not item.infoLabels['tmdb_id'] and not item.infoLabels['imdb_id'] and not item.infoLabels['tvdb_id']\
                    and not item.infoLabels['freebase_mid'] and not item.infoLabels['freebase_id'] and not item.infoLabels['tvrage_id']:
                    # Could not search by ID ...
                    # do it by title
                    if tipo_busqueda == 'tv':
                        # Serial search by title and filtering your results if necessary
                        otmdb = Tmdb(texto_buscado=item.infoLabels['tvshowtitle'], tipo=tipo_busqueda,
                                     idioma_busqueda=idioma_busqueda, filtro=item.infoLabels.get('filtro', {}),
                                     year=item.infoLabels['year'])
                    else:
                        # Movie search by title ...
                        # if item.infoLabels['year'] or item.infoLabels['filtro']:
                        # ...and year or filter
                        searched_title = item.contentTitle if item.contentTitle else item.fulltitle
                        otmdb = Tmdb(texto_buscado=searched_title, tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda,
                                     filtro=item.infoLabels.get('filtro', {}), year=item.infoLabels['year'])
                    if otmdb is not None:
                        if otmdb.get_id() and config.get_setting("tmdb_plus_info", default=False):
                            # If the search has been successful and you are not looking for a list of items,
                            # carry out another search to expand the information
                            otmdb = Tmdb(id_Tmdb=otmdb.result.get("id"), tipo=tipo_busqueda,
                                         idioma_busqueda=idioma_busqueda)

                if lock and lock.locked():
                    lock.release()

                if otmdb is not None and otmdb.get_id():
                    # The search has found a valid result
                    __leer_datos(otmdb)
                    return len(item.infoLabels)

        # title might contain - or : --> try to search only second title
        def splitTitle():
            if '-' in item.fulltitle:
                item.infoLabels['tvshowtitle'] = item.fulltitle.split('-')[1]
                item.infoLabels['title'] = item.infoLabels['tvshowtitle']
            elif ':' in item.fulltitle:
                item.infoLabels['tvshowtitle'] = item.fulltitle.split(':')[1]
                item.infoLabels['title'] = item.infoLabels['tvshowtitle']
            else:
                return False
            return True
        # We check what type of content it is...
        if item.contentType == 'movie':
            tipo_busqueda = 'movie'
        elif item.contentType == 'undefined':  # don't know
            def detect():
                # try movie first
                results = search(otmdb_global, 'movie')
                if results:
                    item.contentType = 'movie'
                infoMovie = item.infoLabels
                if infoMovie['title'] == item.fulltitle:  # exact match -> it's probably correct
                    return results

                # try tvshow then
                item.infoLabels = {'tvshowtitle': item.infoLabels['tvshowtitle']}  # reset infolabels
                results = search(otmdb_global, 'tv')
                if results:
                    item.contentType = 'tvshow'
                else:
                    item.infoLabels = infoMovie

                return results

            results = detect()
            if not results:
                if splitTitle():
                    results = detect()
            return results
        else:
            tipo_busqueda = 'tv'

        ret = search(otmdb_global, tipo_busqueda)
        if not ret:
            if splitTitle():
                ret = search(otmdb_global, tipo_busqueda)
        return ret
    # Search in tmdb is deactivated or has not given result
    # item.contentType = item.infoLabels['mediatype']
    return -1 * len(item.infoLabels)


def find_and_set_infoLabels(item):
    logger.debug()

    global otmdb_global
    tmdb_result = None

    if item.contentType == "movie":
        tipo_busqueda = "movie"
        tipo_contenido = config.get_localized_string(60247)
        title = item.contentTitle
    else:
        tipo_busqueda = "tv"
        tipo_contenido = config.get_localized_string(60298)
        title = item.contentSerieName

    # If the title includes the (year) we will remove it
    year = scrapertools.find_single_match(title, "^.+?\s*(\(\d{4}\))$")
    if year:
        title = title.replace(year, "").strip()
        item.infoLabels['year'] = year[1:-1]

    if not item.infoLabels.get("tmdb_id") or not item.infoLabels.get("tmdb_id")[0].isdigit():
        if not item.infoLabels.get("imdb_id"):
            otmdb_global = Tmdb(texto_buscado=title, tipo=tipo_busqueda, year=item.infoLabels['year'])
        else:
            otmdb_global = Tmdb(external_id=item.infoLabels.get("imdb_id"), external_source="imdb_id", tipo=tipo_busqueda)
    elif not otmdb_global or str(otmdb_global.result.get("id")) != item.infoLabels['tmdb_id']:
        otmdb_global = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo_busqueda, idioma_busqueda=def_lang)

    results = otmdb_global.get_list_resultados()
    if len(results) > 1:
        tmdb_result = platformtools.show_video_info(results, item=item, caption= tipo_contenido % title)
    elif len(results) > 0:
        tmdb_result = results[0]

    if isinstance(item.infoLabels, InfoLabels):
        infoLabels = item.infoLabels
    else:
        infoLabels = InfoLabels()

    if tmdb_result:
        infoLabels['tmdb_id'] = tmdb_result['id']
        # all look if it can be removed and get only from get_nfo ()
        infoLabels['url_scraper'] = ["https://www.themoviedb.org/%s/%s" % (tipo_busqueda, infoLabels['tmdb_id'])]
        if infoLabels['tvdb_id']:
            infoLabels['url_scraper'].append("http://thetvdb.com/index.php?tab=series&id=%s" % infoLabels['tvdb_id'])
        item.infoLabels = infoLabels
        set_infoLabels_item(item)

        return True

    else:
        item.infoLabels = infoLabels
        return False


def get_nfo(item, search_groups=False):
    """
    Returns the information necessary for the result to be scraped into the kodi video library, for tmdb it works only by passing it the url.
    @param item: element that contains the data necessary to generate the info
    @type item: Item
    @rtype: str
    @return:
    """

    if search_groups:
        from platformcode.autorenumber import RENUMBER, GROUP
        path = filetools.join(config.get_data_path(), "settings_channels", item.channel + "_data.json")
        if filetools.exists(path): 
            g = jsontools.load(filetools.read(path)).get(RENUMBER,{}).get(item.fulltitle.strip(),{}).get(GROUP,'')
            if g: return g + '\n'

        groups = get_groups(item)

        if groups:
            Id = select_group(groups)
            if Id:
                info_nfo = 'https://www.themoviedb.org/tv/{}/episode_group/{}\n'.format(item.infoLabels['tmdb_id'], Id)
                return info_nfo
            else: return

    if "season" in item.infoLabels and "episode" in item.infoLabels:
        info_nfo = "https://www.themoviedb.org/tv/%s/season/%s/episode/%s\n" % (item.infoLabels['tmdb_id'], item.contentSeason, item.contentEpisodeNumber)
    else:
        info_nfo = ', '.join(item.infoLabels['url_scraper']) + "\n"

    return info_nfo

def get_groups(item):
    url = 'https://api.themoviedb.org/3/tv/{}/episode_groups?api_key=a1ab8b8669da03637a4b98fa39c39228&language={}'.format(item.infoLabels['tmdb_id'], def_lang)
    groups = requests.get(url).json().get('results',[])
    return groups

def select_group(groups):
    selected = -1
    selections = []
    ids = []
    for group in groups:
        name = '[B]{}[/B] Seasons: {} Episodes: {}'.format(group.get('name',''), group.get('group_count',''), group.get('episode_count',''))
        description = group.get('description','')
        if description:
            name = '{}\n{}'.format(name, description)
        ID = group.get('id','')
        if ID:
            selections.append(name)
            ids.append(ID)
    if selections and ids:
        selected = platformtools.dialog_select_group(config.get_localized_string(70831), selections)
    if selected > -1:
        return ids[selected]
    return ''

def get_group(Id):
    url = 'https://api.themoviedb.org/3/tv/episode_group/{}?api_key=a1ab8b8669da03637a4b98fa39c39228&language={}'.format(Id, def_lang)
    group = requests.get(url).json().get('groups',[])
    return group

def completar_codigos(item):
    """
    If necessary, check if the tvdb identifier exists and if it does not exist try to find it
    """
    if item.contentType != "movie" and not item.infoLabels['tvdb_id']:
        # Launch search for imdb_id on tvdb
        from core.tvdb import Tvdb
        ob = Tvdb(imdb_id=item.infoLabels['imdb_id'])
        item.infoLabels['tvdb_id'] = ob.get_id()
    if item.infoLabels['tvdb_id']:
        url_scraper = "http://thetvdb.com/index.php?tab=series&id=%s" % item.infoLabels['tvdb_id']
        if url_scraper not in item.infoLabels['url_scraper']:
            item.infoLabels['url_scraper'].append(url_scraper)


def discovery(item, dict_=False, cast=False):
    from core.item import Item

    if dict_:
        listado = Tmdb(discover = dict_, cast=cast)

    elif item.search_type == 'discover':
        listado = Tmdb(discover={'url':'discover/%s' % item.type, 'with_genres':item.list_type, 'language':def_lang, 'page':item.page})

    elif item.search_type == 'list':
        if item.page == '':
            item.page = '1'
        listado = Tmdb(discover={'url': item.list_type, 'language':def_lang, 'page':item.page})

    return listado

def get_genres(type):
    lang = def_lang
    genres = Tmdb(tipo=type)

    return genres.dic_generos[lang]


# Auxiliary class
class ResultDictDefault(dict):
    # Python 2.4
    def __getitem__(self, key):
        try:
            return super(ResultDictDefault, self).__getitem__(key)
        except:
            return self.__missing__(key)

    def __missing__(self, key):
        """
        default values ​​in case the requested key does not exist
        """
        if key in ['genre_ids', 'genre', 'genres']:
            return list()
        elif key == 'images_posters':
            posters = dict()
            if 'images' in list(super(ResultDictDefault, self).keys()) and 'posters' in super(ResultDictDefault, self).__getitem__('images'):
                posters = super(ResultDictDefault, self).__getitem__('images')['posters']
                super(ResultDictDefault, self).__setattr__("images_posters", posters)

            return posters

        elif key == "images_backdrops":
            backdrops = dict()
            if 'images' in list(super(ResultDictDefault, self).keys()) and 'backdrops' in super(ResultDictDefault, self).__getitem__('images'):
                backdrops = super(ResultDictDefault, self).__getitem__('images')['backdrops']
                super(ResultDictDefault, self).__setattr__("images_backdrops", backdrops)

            return backdrops

        elif key == "images_profiles":
            profiles = dict()
            if 'images' in list(super(ResultDictDefault, self).keys()) and 'profiles' in super(ResultDictDefault, self).__getitem__('images'):
                profiles = super(ResultDictDefault, self).__getitem__('images')['profiles']
                super(ResultDictDefault, self).__setattr__("images_profiles", profiles)

            return profiles

        else:
            # The rest of the keys return empty strings by default
            return ""

    def __str__(self):
        return self.tostring(separador=',\n')

    def tostring(self, separador=',\n'):
        ls = []
        for i in list(super(ResultDictDefault, self).items()):
            i_str = str(i)[1:-1]
            if isinstance(i[0], str):
                old = i[0] + "',"
                new = i[0] + "':"
            else:
                old = str(i[0]) + ","
                new = str(i[0]) + ":"
            ls.append(i_str.replace(old, new, 1))

        return "{%s}" % separador.join(ls)


# ---------------------------------------------------------------------------------------------------------------
# class Tmdb:
# Scraper for the API based addon from https://www.themoviedb.org/
# version 1.4:
# - Documented limitation of API use (see below).
# - Added get_temporada () method
# version 1.3:
# - Fixed error when returning None the path_poster and backdrop_path
# - Fixed a bug that caused the list of genres to accumulate from one call to another
# - Added get_generos () method
# - Added optional parameters alternative_language to the get_sinopsis () method
#
#
# Usage:
# Construction methods:
# Tmdb (search_text, type)
# Parameters:
# searched_text: (str) Text or part of the text to search
# type: ("movie" or "tv") Type of result searched for movies or series. Default "movie"
# (optional) language_search: (str) language code according to ISO 639-1
# (optional) include_adult: (bool) Adult content is included in the search or not. Default
# 'False'
# (optional) year: (str) Release year.
# (optional) page: (int) When there are many results for a search these are organized by pages.
# We can load the page we want, although by default it is always the first page.
# Return:
# This call returns a Tmdb object containing the first page of the search result 'search_text'
# on the themoviedb.org website. The more optional parameters are included, the more precise the search will be.
# Also the object is initialized with the first result of the first page of results.
# Tmdb (id_Tmdb, type)
# Parameters:
# id_Tmdb: (str) Identifier code of a certain movie or series at themoviedb.org
# type: ("movie" or "tv") Type of result searched for movies or series. Default "movie"
# (optional) language_search: (str) language code according to ISO 639-1
# Return:
# This call returns a Tmdb object that contains the result of searching for a movie or series with the
# identifier id_Tmd
# on the themoviedb.org website.
# Tmdb (external_id, external_source, type)
# Parameters:
# external_id: (str) Identifier code of a certain movie or series on the web referenced by
# 'external_source'.
# external_source: (For series: "imdb_id", "freebase_mid", "freebase_id", "tvdb_id", "tvrage_id"; For
# movies: "imdb_id")
# type: ("movie" or "tv") Type of result searched for movies or series. Default "movie"
# (optional) language_search: (str) language code according to ISO 639-1
# Return:
# This call returns a Tmdb object that contains the result of searching for a movie or series with the
# identifier 'external_id' of
# the website referenced by 'external_source' on the themoviedb.org website.
#
# Main methods:
# get_id (): Returns a str with the Tmdb identifier of the loaded movie or series or an empty string if there were no
# nothing loaded.
# get_sinopsis (alternate_language): Returns a str with the synopsis of the series or movie loaded.
# get_poster (response_type, size): Get the poster or a list of posters.
# get_backdrop (response_type, size): Get a background image or a list of background images.
# get_temporada (season): Get a dictionary with season-specific data.
# get_episodio (season, episode): Get a dictionary with specific data of the episode.
# get_generos (): Returns a str with the list of genres to which the movie or series belongs.
#
#
# Other methods:
# load_resultado (result, page): When the search returns several results we can select which result
# concrete and from which page to load the data.
#
# Limitations:
# The use of the API imposes a limit of 20 simultaneous connections (concurrency) or 30 requests in 10 seconds per IP
# Information about the api: http://docs.themoviedb.apiary.io
# -------------------------------------------------------------------------------------------------------------------


class Tmdb(object):
    # Class attribute
    dic_generos = {}
    '''
    dic_generos={"id_idioma1": {"tv": {"id1": "name1",
                                       "id2": "name2"
                                      },
                                "movie": {"id1": "name1",
                                          "id2": "name2"
                                          }
                                }
                }
    '''
    dic_country = {"AD": "Andorra", "AE": "Emiratos Árabes Unidos", "AF": "Afganistán", "AG": "Antigua y Barbuda",
                   "AI": "Anguila", "AL": "Albania", "AM": "Armenia", "AN": "Antillas Neerlandesas", "AO": "Angola",
                   "AQ": "Antártida", "AR": "Argentina", "AS": "Samoa Americana", "AT": "Austria", "AU": "Australia",
                   "AW": "Aruba", "AX": "Islas de Åland", "AZ": "Azerbayán", "BA": "Bosnia y Herzegovina",
                   "BD": "Bangladesh", "BE": "Bélgica", "BF": "Burkina Faso", "BG": "Bulgaria", "BI": "Burundi",
                   "BJ": "Benín", "BL": "San Bartolomé", "BM": "Islas Bermudas", "BN": "Brunéi", "BO": "Bolivia",
                   "BR": "Brasil", "BS": "Bahamas", "BT": "Bhután", "BV": "Isla Bouvet", "BW": "Botsuana",
                   "BY": "Bielorrusia", "BZ": "Belice", "CA": "Canadá", "CC": "Islas Cocos (Keeling)", "CD": "Congo",
                   "CF": "República Centroafricana", "CG": "Congo", "CH": "Suiza", "CI": "Costa de Marfil",
                   "CK": "Islas Cook", "CL": "Chile", "CM": "Camerún", "CN": "China", "CO": "Colombia",
                   "CR": "Costa Rica", "CU": "Cuba", "CV": "Cabo Verde", "CX": "Isla de Navidad", "CY": "Chipre",
                   "CZ": "República Checa", "DE": "Alemania", "DJ": "Yibuti", "DK": "Dinamarca", "DZ": "Algeria",
                   "EC": "Ecuador", "EE": "Estonia", "EG": "Egipto", "EH": "Sahara Occidental", "ER": "Eritrea",
                   "ES": "España", "ET": "Etiopía", "FI": "Finlandia", "FJ": "Fiyi", "FK": "Islas Malvinas",
                   "FM": "Micronesia", "FO": "Islas Feroe", "FR": "Francia", "GA": "Gabón", "GB": "Gran Bretaña",
                   "GD": "Granada", "GE": "Georgia", "GF": "Guayana Francesa", "GG": "Guernsey", "GH": "Ghana",
                   "GI": "Gibraltar", "GL": "Groenlandia", "GM": "Gambia", "GN": "Guinea", "GP": "Guadalupe",
                   "GQ": "Guinea Ecuatorial", "GR": "Grecia", "GS": "Islas Georgias del Sur y Sandwich del Sur",
                   "GT": "Guatemala", "GW": "Guinea-Bissau", "GY": "Guyana", "HK": "Hong kong",
                   "HM": "Islas Heard y McDonald", "HN": "Honduras", "HR": "Croacia", "HT": "Haití", "HU": "Hungría",
                   "ID": "Indonesia", "IE": "Irlanda", "IM": "Isla de Man", "IN": "India",
                   "IO": "Territorio Británico del Océano Índico", "IQ": "Irak", "IR": "Irán", "IS": "Islandia",
                   "IT": "Italia", "JE": "Jersey", "JM": "Jamaica", "JO": "Jordania", "JP": "Japón", "KG": "Kirgizstán",
                   "KH": "Camboya", "KM": "Comoras", "KP": "Corea del Norte", "KR": "Corea del Sur", "KW": "Kuwait",
                   "KY": "Islas Caimán", "KZ": "Kazajistán", "LA": "Laos", "LB": "Líbano", "LC": "Santa Lucía",
                   "LI": "Liechtenstein", "LK": "Sri lanka", "LR": "Liberia", "LS": "Lesoto", "LT": "Lituania",
                   "LU": "Luxemburgo", "LV": "Letonia", "LY": "Libia", "MA": "Marruecos", "MC": "Mónaco",
                   "MD": "Moldavia", "ME": "Montenegro", "MF": "San Martín (Francia)", "MG": "Madagascar",
                   "MH": "Islas Marshall", "MK": "Macedônia", "ML": "Mali", "MM": "Birmania", "MN": "Mongolia",
                   "MO": "Macao", "MP": "Islas Marianas del Norte", "MQ": "Martinica", "MR": "Mauritania",
                   "MS": "Montserrat", "MT": "Malta", "MU": "Mauricio", "MV": "Islas Maldivas", "MW": "Malawi",
                   "MX": "México", "MY": "Malasia", "NA": "Namibia", "NE": "Niger", "NG": "Nigeria", "NI": "Nicaragua",
                   "NL": "Países Bajos", "NO": "Noruega", "NP": "Nepal", "NR": "Nauru", "NU": "Niue",
                   "NZ": "Nueva Zelanda", "OM": "Omán", "PA": "Panamá", "PE": "Perú", "PF": "Polinesia Francesa",
                   "PH": "Filipinas", "PK": "Pakistán", "PL": "Polonia", "PM": "San Pedro y Miquelón",
                   "PN": "Islas Pitcairn", "PR": "Puerto Rico", "PS": "Palestina", "PT": "Portugal", "PW": "Palau",
                   "PY": "Paraguay", "QA": "Qatar", "RE": "Reunión", "RO": "Rumanía", "RS": "Serbia", "RU": "Rusia",
                   "RW": "Ruanda", "SA": "Arabia Saudita", "SB": "Islas Salomón", "SC": "Seychelles", "SD": "Sudán",
                   "SE": "Suecia", "SG": "Singapur", "SH": "Santa Elena", "SI": "Eslovenia",
                   "SJ": "Svalbard y Jan Mayen",
                   "SK": "Eslovaquia", "SL": "Sierra Leona", "SM": "San Marino", "SN": "Senegal", "SO": "Somalia",
                   "SV": "El Salvador", "SY": "Siria", "SZ": "Swazilandia", "TC": "Islas Turcas y Caicos", "TD": "Chad",
                   "TF": "Territorios Australes y Antárticas Franceses", "TG": "Togo", "TH": "Tailandia",
                   "TJ": "Tadjikistán", "TK": "Tokelau", "TL": "Timor Oriental", "TM": "Turkmenistán", "TN": "Tunez",
                   "TO": "Tonga", "TR": "Turquía", "TT": "Trinidad y Tobago", "TV": "Tuvalu", "TW": "Taiwán",
                   "TZ": "Tanzania", "UA": "Ucrania", "UG": "Uganda",
                   "UM": "Islas Ultramarinas Menores de Estados Unidos",
                   "UY": "Uruguay", "UZ": "Uzbekistán", "VA": "Ciudad del Vaticano",
                   "VC": "San Vicente y las Granadinas",
                   "VE": "Venezuela", "VG": "Islas Vírgenes Británicas", "VI": "Islas Vírgenes de los Estados Unidos",
                   "VN": "Vietnam", "VU": "Vanuatu", "WF": "Wallis y Futuna", "WS": "Samoa", "YE": "Yemen",
                   "YT": "Mayotte", "ZA": "Sudáfrica", "ZM": "Zambia", "ZW": "Zimbabue", "BB": "Barbados",
                   "BH": "Bahrein",
                   "DM": "Dominica", "DO": "República Dominicana", "GU": "Guam", "IL": "Israel", "KE": "Kenia",
                   "KI": "Kiribati", "KN": "San Cristóbal y Nieves", "MZ": "Mozambique", "NC": "Nueva Caledonia",
                   "NF": "Isla Norfolk", "PG": "Papúa Nueva Guinea", "SR": "Surinám", "ST": "Santo Tomé y Príncipe",
                   "US": "EEUU"}

    def __init__(self, **kwargs):
        self.page = kwargs.get('page', 1)
        self.index_results = 0
        self.cast = kwargs.get('cast', False)
        self.results = []
        self.result = ResultDictDefault()
        self.total_pages = 0
        self.total_results = 0

        self.temporada = {}
        self.texto_buscado = kwargs.get('texto_buscado', '')

        self.busqueda_id = kwargs.get('id_Tmdb', '')
        self.busqueda_texto = re.sub('\[\\\?(B|I|COLOR)\s?[^\]]*\]', '', self.texto_buscado).strip()
        self.busqueda_tipo = kwargs.get('tipo', '')
        self.busqueda_idioma = kwargs.get('idioma_busqueda', def_lang)
        # self.busqueda_include_adult = kwargs.get('include_adult', False)
        self.busqueda_year = kwargs.get('year', '')
        self.busqueda_filtro = kwargs.get('filtro', {})
        self.discover = kwargs.get('discover', {})

        # Refill gender dictionary if necessary
        if (self.busqueda_tipo == 'movie' or self.busqueda_tipo == "tv") and (self.busqueda_idioma not in Tmdb.dic_generos or self.busqueda_tipo not in Tmdb.dic_generos[self.busqueda_idioma]):
            self.rellenar_dic_generos(self.busqueda_tipo, self.busqueda_idioma)

        if not self.busqueda_tipo:
            self.busqueda_tipo = 'movie'

        if self.busqueda_id:
            #Search by tmdb identifier
            self.__by_id()

        elif self.busqueda_texto:
            # Busqueda por texto
            self.__search(page=self.page)

        elif 'external_source' in kwargs and 'external_id' in kwargs:
            # Search by external identifier according to type.
            # TV Series: imdb_id, freebase_mid, freebase_id, tvdb_id, tvrage_id
            # Movies: imdb_id
            if (self.busqueda_tipo == 'movie' and kwargs.get('external_source') == "imdb_id") or (self.busqueda_tipo == 'tv' and kwargs.get('external_source') in ("imdb_id", "freebase_mid", "freebase_id", "tvdb_id", "tvrage_id")):
                self.busqueda_id = kwargs.get('external_id')
                self.__by_id(source=kwargs.get('external_source'))

        elif self.discover:
            self.__discover()

        else:
            logger.debug("Created empty object")

    @staticmethod
    @cache_response
    def get_json(url, cache=True):
        try:
            result = httptools.downloadpage(url, cookies=False, ignore_response_code=True)

            res_headers = result.headers
            dict_data = jsontools.load(result.data)
            #logger.debug("result_data es %s" % dict_data)

            if "status_code" in dict_data:
                #logger.debug("\nError de tmdb: %s %s" % (dict_data["status_code"], dict_data["status_message"]))

                if dict_data["status_code"] == 25:
                    while "status_code" in dict_data and dict_data["status_code"] == 25:
                        wait = int(res_headers['retry-after'])
                        #logger.error("Limit reached, we wait to call back on ...%s" % wait)
                        time.sleep(wait)
                        # logger.debug("RE Call #%s" % d)
                        result = httptools.downloadpage(url, cookies=False)

                        res_headers = result.headers
                        # logger.debug("res_headers es %s" % res_headers)
                        dict_data = jsontools.load(result.data)
                        # logger.debug("result_data es %s" % dict_data)

        # error getting data
        except Exception as ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error in: %s" % message)
            dict_data = {}

        return dict_data

    @classmethod
    def rellenar_dic_generos(cls, tipo='movie', idioma=def_lang):
        # Fill dictionary of genres of the type and language passed as parameters
        if idioma not in cls.dic_generos:
            cls.dic_generos[idioma] = {}

        if tipo not in cls.dic_generos[idioma]:
            cls.dic_generos[idioma][tipo] = {}
            url = ('http://api.themoviedb.org/3/genre/%s/list?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s' % (tipo, idioma))
            try:
                logger.debug("[Tmdb.py] Filling in dictionary of genres")

                resultado = cls.get_json(url)
                if not isinstance(resultado, dict):
                    resultado = ast.literal_eval(resultado.decode('utf-8'))
                lista_generos = resultado["genres"]

                for i in lista_generos:
                    cls.dic_generos[idioma][tipo][str(i["id"])] = i["name"]
            except:
                logger.error("Error generating dictionaries")
                import traceback
                logger.error(traceback.format_exc())

    def __by_id(self, source='tmdb'):

        if self.busqueda_id:
            if source == "tmdb":
                # http://api.themoviedb.org/3/movie/1924?api_key=a1ab8b8669da03637a4b98fa39c39228&language=es
                #   &append_to_response=images,videos,external_ids,credits&include_image_language=es,null
                # http://api.themoviedb.org/3/tv/1407?api_key=a1ab8b8669da03637a4b98fa39c39228&language=es
                #   &append_to_response=images,videos,external_ids,credits&include_image_language=es,null
                url = ('http://api.themoviedb.org/3/%s/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s'
                       '&append_to_response=images,videos,external_ids,credits&include_image_language=%s,null' %
                       (self.busqueda_tipo, self.busqueda_id, self.busqueda_idioma, self.busqueda_idioma))
                buscando = "id_Tmdb: %s" % self.busqueda_id
            else:
                # http://api.themoviedb.org/3/find/%s?external_source=imdb_id&api_key=a1ab8b8669da03637a4b98fa39c39228
                url = ('http://api.themoviedb.org/3/find/%s?external_source=%s&api_key=a1ab8b8669da03637a4b98fa39c39228'
                       '&language=%s' % (self.busqueda_id, source, self.busqueda_idioma))
                buscando = "%s: %s" % (source.capitalize(), self.busqueda_id)

            logger.debug("[Tmdb.py] Searching %s:\n%s" % (buscando, url))
            resultado = self.get_json(url)
            if not isinstance(resultado, dict):
                resultado = ast.literal_eval(resultado.decode('utf-8'))

            if resultado:
                if source != "tmdb":
                    if self.busqueda_tipo == "movie":
                        resultado = resultado["movie_results"][0]
                    else:
                        if resultado["tv_results"]:
                            resultado = resultado["tv_results"][0]
                        else:
                            resultado = resultado['tv_episode_results'][0]

                self.results = [resultado]
                self.total_results = 1
                self.total_pages = 1
                self.result = ResultDictDefault(resultado)

            else:
                # No search results
                msg = "The search of %s gave no results" % buscando
                logger.debug(msg)

    def __search(self, index_results=0, page=1):
        self.result = ResultDictDefault()
        results = []
        text_simple = self.busqueda_texto.lower()
        text_quote = urllib.quote(text_simple)
        total_results = 0
        total_pages = 0
        buscando = ""

        if self.busqueda_texto:
            # http://api.themoviedb.org/3/search/movie?api_key=a1ab8b8669da03637a4b98fa39c39228&query=superman&language=es
            # &include_adult=false&page=1
            url = ('http://api.themoviedb.org/3/search/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&query=%s&language=%s'
                   '&include_adult=%s&page=%s' % (self.busqueda_tipo, text_quote, self.busqueda_idioma, True, page))

            if self.busqueda_year:
                if self.busqueda_tipo == 'tv':
                    url += '&first_air_date_year=%s' % self.busqueda_year
                else:
                    url += '&year=%s' % self.busqueda_year

            buscando = self.busqueda_texto.capitalize()
            logger.debug("[Tmdb.py] Searching %s on page %s:\n%s" % (buscando, page, url))
            resultado = self.get_json(url)
            if not isinstance(resultado, dict):
                resultado = ast.literal_eval(resultado.decode('utf-8'))

            total_results = resultado.get("total_results", 0)
            total_pages = resultado.get("total_pages", 0)

            if total_results > 0:
                results = resultado["results"]

            if self.busqueda_filtro and total_results > 1:
                for key, value in list(dict(self.busqueda_filtro).items()):
                    for r in results[:]:
                        if not r[key]:
                            r[key] = str(r[key])
                        if key not in r or value not in r[key]:
                            results.remove(r)
                            total_results -= 1

        if results:
            if index_results >= len(results):
                # A higher number of results has been requested than those obtained
                logger.error(
                    "The search for '%s' gave %s results for the page %s \n It is impossible to show the result number %s"
                    % (buscando, len(results), page, index_results))
                return 0

            # We sort result based on fuzzy match to detect most similar
            if len(results) > 1:
                from lib.fuzzy_match import algorithims
                results.sort(key=lambda r: algorithims.trigram(text_simple, r['title'] if self.busqueda_tipo == 'movie' else r['name']), reverse=True)

            # We return the number of results of this page
            self.results = results
            self.total_results = total_results
            self.total_pages = total_pages
            self.result = ResultDictDefault(self.results[index_results])
            return len(self.results)

        else:
            # No search results
            msg = "The search for '%s' gave no results for page %s" % (buscando, page)
            logger.error(msg)
            return 0


    def __discover(self, index_results=0):
        self.result = ResultDictDefault()
        results = []
        total_results = 0
        total_pages = 0

        # Ejemplo self.discover: {'url': 'discover/movie', 'with_cast': '1'}
        # url: API method to run
        # rest of keys: Search parameters concatenated to the url
        type_search = self.discover.get('url', '')
        if type_search:
            params = []
            for key, value in list(self.discover.items()):
                if key != "url":
                    params.append(key + "=" + str(value))
            # http://api.themoviedb.org/3/discover/movie?api_key=a1ab8b8669da03637a4b98fa39c39228&query=superman&language=es
            url = ('http://api.themoviedb.org/3/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&%s'
                   % (type_search, "&".join(params)))

            logger.debug("[Tmdb.py] Searcing %s:\n%s" % (type_search, url))
            resultado = self.get_json(url, cache=False)
            if not isinstance(resultado, dict):
                resultado = ast.literal_eval(resultado.decode('utf-8'))

            total_results = resultado.get("total_results", -1)
            total_pages = resultado.get("total_pages", 1)

            if total_results > 0 or self.cast:
                if self.cast:
                    results = resultado[self.cast]
                    total_results = len(results)
                else:
                    results = resultado["results"]
                if self.busqueda_filtro and results:
                    # TODO documentar esta parte
                    for key, value in list(dict(self.busqueda_filtro).items()):
                        for r in results[:]:
                            if key not in r or r[key] != value:
                                results.remove(r)
                                total_results -= 1
            elif total_results == -1:
                results = resultado

            if index_results >= len(results):
                logger.error(
                    "The search for '%s' did not give %s results" % (type_search, index_results))
                return 0

        # We return the number of results of this page
        if results:
            self.results = results
            self.total_results = total_results
            self.total_pages = total_pages
            if total_results > 0:
                self.result = ResultDictDefault(self.results[index_results])

            else:
                self.result = results
            return len(self.results)
        else:
            # No search results
            logger.error("The search for '%s' gave no results" % type_search)
            return 0

    def load_resultado(self, index_results=0, page=1):
        # If there are no results, there is only one or if the number of results on this page is less than the index sought to exit
        self.result = ResultDictDefault()
        num_result_page = len(self.results)

        if page > self.total_pages:
            return False

        if page != self.page:
            num_result_page = self.__search(index_results, page)

        if num_result_page == 0 or num_result_page <= index_results:
            return False

        self.page = page
        self.index_results = index_results
        self.result = ResultDictDefault(self.results[index_results])
        return True

    def get_list_resultados(self, num_result=20):
        # logger.debug("self %s" % str(self))
        res = []

        if num_result <= 0:
            num_result = self.total_results
        num_result = min([num_result, self.total_results])

        cr = 0
        for p in range(1, self.total_pages + 1):
            for r in range(0, len(self.results)):
                try:
                    if self.load_resultado(r, p):
                        result = self.result.copy()

                        result['thumbnail'] = self.get_poster(size="w300")
                        result['fanart'] = self.get_backdrop()

                        res.append(result)
                        cr += 1

                        if cr >= num_result:
                            return res
                except:
                    continue

        return res

    def get_generos(self, origen=None):
        """
        :param origen: Source dictionary where the infoLabels are obtained, by default self.result
        :type origen: Dict
        :return: Returns the list of genres to which the movie or series belongs.
        :rtype: str
        """
        genre_list = []

        if not origen:
            origen = self.result

        if "genre_ids" in origen:
            # Search list of genres by IDs
            for i in origen.get("genre_ids"):
                try:
                    genre_list.append(Tmdb.dic_generos[self.busqueda_idioma][self.busqueda_tipo][str(i)])
                except:
                    pass

        elif "genre" in origen or "genres" in origen:
            # Search genre list (object list {id, name})
            v = origen["genre"]
            v.extend(origen["genres"])
            for i in v:
                genre_list.append(i['name'])

        return ', '.join(genre_list)

    def search_by_id(self, id, source='tmdb', tipo='movie'):
        self.busqueda_id = id
        self.busqueda_tipo = tipo
        self.__by_id(source=source)

    def get_id(self):
        """
        :return: Returns the Tmdb identifier of the loaded movie or series or an empty string in case nothing was loaded. You can use this method to find out if a search has been successful or not.
        :rtype: str
        """
        return str(self.result.get('id', ""))

    def get_sinopsis(self, idioma_alternativo=""):
        """

        :param idioma_alternativo: Language code, according to ISO 639-1, if there is no synopsis in the language set for the search.
            By default, the original language is used. If None is used as the alternative_language, it will only search in the set language.
        :type idioma_alternativo: str
        :return: Returns the synopsis of a movie or series
        :rtype: str
        """
        ret = ""

        if 'id' in self.result:
            ret = self.result.get('overview')
            if ret == "" and str(idioma_alternativo).lower() != 'none':
                # Let's launch a search for id and reread the synopsis again
                self.busqueda_id = str(self.result["id"])
                if idioma_alternativo:
                    self.busqueda_idioma = idioma_alternativo
                else:
                    self.busqueda_idioma = self.result['original_language']

                url = ('http://api.themoviedb.org/3/%s/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s' % (self.busqueda_tipo, self.busqueda_id, self.busqueda_idioma))

                resultado = self.get_json(url)
                if not isinstance(resultado, dict):
                    resultado = ast.literal_eval(resultado.decode('utf-8'))

                if 'overview' in resultado:
                    self.result['overview'] = resultado['overview']
                    ret = self.result['overview']

        return ret

    def get_poster(self, tipo_respuesta="str", size="original"):
        """

        @param tipo_respuesta: Data type returned by this method. Default "str"
        @type tipo_respuesta: list, str
        @param size: ("w45", "w92", "w154", "w185", "w300", "w342", "w500", "w600", "h632", "w780", "w1280", "original")
            Indicates the width (w) or height (h) of the image to download. Default "original"
        @return: If the response_type is "list" it returns a list with all the urls of the poster images of the specified size.
            If the response_type is "str" ​​it returns the url of the poster image, most valued, of the specified size.
            If the specified size does not exist, the images are returned to the original size.
        @rtype: list, str
        """
        ret = []
        if size not in ("w45", "w92", "w154", "w185", "w300", "w342", "w500", "w600", "h632", "w780", "w1280"):
            size = "original"

        if self.result["poster_path"] is None or self.result["poster_path"] == "":
            poster_path = ""
        else:
            poster_path = 'https://image.tmdb.org/t/p/' + size + self.result["poster_path"]

        if tipo_respuesta == 'str':
            return poster_path
        elif not self.result["id"]:
            return []

        if len(self.result['images_posters']) == 0:
            # We are going to launch a search by id and reread again
            self.busqueda_id = str(self.result["id"])
            self.__by_id()

        if len(self.result['images_posters']) > 0:
            for i in self.result['images_posters']:
                imagen_path = i['file_path']
                if size != "original":
                    # We cannot order sizes larger than the original
                    if size[1] == 'w' and int(imagen_path['width']) < int(size[1:]):
                        size = "original"
                    elif size[1] == 'h' and int(imagen_path['height']) < int(size[1:]):
                        size = "original"
                ret.append('https://image.tmdb.org/t/p/' + size + imagen_path)
        else:
            ret.append(poster_path)

        return ret

    def get_backdrop(self, tipo_respuesta="str", size="original"):
        """
        Returns the images of type backdrop
        @param tipo_respuesta: Data type returned by this method. Default "str"
        @type tipo_respuesta: list, str
        @param size: ("w45", "w92", "w154", "w185", "w300", "w342", "w500", "w600", "h632", "w780", "w1280", "original")
            Indicates the width (w) or height (h) of the image to download. Default "original"
        @type size: str
        @return: If the response_type is "list" it returns a list with all the urls of the backdrop images of the specified size.
            If the response_type is "str" ​​it returns the url of the backdrop type image, most valued, of the specified size.
            If the specified size does not exist, the images are returned to the original size.
        @rtype: list, str
        """
        ret = []
        if size not in ("w45", "w92", "w154", "w185", "w300", "w342", "w500", "w600", "h632", "w780", "w1280"):
            size = "original"

        if self.result["backdrop_path"] is None or self.result["backdrop_path"] == "":
            backdrop_path = ""
        else:
            backdrop_path = 'https://image.tmdb.org/t/p/' + size + self.result["backdrop_path"]

        if tipo_respuesta == 'str':
            return backdrop_path
        elif self.result["id"] == "":
            return []

        if len(self.result['images_backdrops']) == 0:
            # Let's launch a search by id and reread everything
            self.busqueda_id = str(self.result["id"])
            self.__by_id()

        if len(self.result['images_backdrops']) > 0:
            for i in self.result['images_backdrops']:
                imagen_path = i['file_path']
                if size != "original":
                    # We cannot order sizes larger than the original
                    if size[1] == 'w' and int(imagen_path['width']) < int(size[1:]):
                        size = "original"
                    elif size[1] == 'h' and int(imagen_path['height']) < int(size[1:]):
                        size = "original"
                ret.append('https://image.tmdb.org/t/p/' + size + imagen_path)
        else:
            ret.append(backdrop_path)

        return ret

    def get_temporada(self, numtemporada=1):
        # --------------------------------------------------------------------------------------------------------------------------------------------
        # Parameters:
        # season number: (int) Season number. Default 1.
        # Return: (Dec)
        # Returns a dictionary with data about the season.
        # You can get more information about the returned data at:
        # http://docs.themoviedb.apiary.io/#reference/tv-seasons/tvidseasonseasonnumber/get
        # http://docs.themoviedb.apiary.io/#reference/tv-seasons/tvidseasonseasonnumbercredits/get
        # --------------------------------------------------------------------------------------------------------------------------------------------
        if not self.result["id"] or self.busqueda_tipo != "tv":
            return {}

        numtemporada = int(numtemporada)
        if numtemporada < 0:
            numtemporada = 1

        if not self.temporada.get(numtemporada, {}):
            # If there is no information about the requested season, check the website

            # http://api.themoviedb.org/3/tv/1407/season/1?api_key=a1ab8b8669da03637a4b98fa39c39228&language=es&
            # append_to_response=credits
            url = "http://api.themoviedb.org/3/tv/%s/season/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s" \
                  "&append_to_response=credits" % (self.result["id"], numtemporada, self.busqueda_idioma)

            buscando = "id_Tmdb: " + str(self.result["id"]) + " season: " + str(numtemporada) + "\nURL: " + url
            logger.debug("[Tmdb.py] Searcing " + buscando)
            try:
                self.temporada[numtemporada] = self.get_json(url)
                if not isinstance(self.temporada[numtemporada], dict):
                    self.temporada[numtemporada] = ast.literal_eval(self.temporada[numtemporada].decode('utf-8'))

            except:
                logger.error("Unable to get the season")
                self.temporada[numtemporada] = {"status_code": 15, "status_message": "Failed"}
                self.temporada[numtemporada] = {"episodes": {}}

            if "status_code" in self.temporada[numtemporada]:
                # An error has occurred
                msg = config.get_localized_string(70496) + buscando + config.get_localized_string(70497)
                msg += "\nTmdb error: %s %s" % (
                self.temporada[numtemporada]["status_code"], self.temporada[numtemporada]["status_message"])
                logger.debug(msg)
                self.temporada[numtemporada] = {}

        return self.temporada[numtemporada]

    def get_episodio(self, numtemporada=1, capitulo=1):
        # --------------------------------------------------------------------------------------------------------------------------------------------
        # Parameters:
        # season number (optional): (int) Season number. Default 1.
        # chapter: (int) Chapter number. Default 1.
        # Return: (Dec)
        # Returns a dictionary with the following elements:
        # "season_name", "season_synopsis", "season_poster", "season_num_ episodes" (int),
        # "season_air_date", "episode_vote_count", "episode_vote_average",
        # "episode_title", "episode_synopsis", "episode_image", "episode_air_date",
        # "episode_crew" and "episode_guest_stars",
        # With chapter == -1 the dictionary will only have the elements referring to the season
        # --------------------------------------------------------------------------------------------------------------------------------------------
        if not self.result["id"] or self.busqueda_tipo != "tv":
            return {}

        try:
            capitulo = int(capitulo)
            numtemporada = int(numtemporada)
        except ValueError:
            logger.debug("The episode or season number is not valid")
            return {}

        temporada = self.get_temporada(numtemporada)
        if not isinstance(temporada, dict):
            temporada = ast.literal_eval(temporada.decode('utf-8'))
        if not temporada:
            # An error has occurred
            return {}

        if len(temporada["episodes"]) == 0 or len(temporada["episodes"]) < capitulo:
            # An error has occurred
            logger.error("Episode %d of the season %d not found." % (capitulo, numtemporada))
            return {}

        ret_dic = dict()
        # Get data for this season
        ret_dic["temporada_nombre"] = temporada["name"]
        ret_dic["temporada_sinopsis"] = temporada["overview"]
        ret_dic["temporada_num_episodios"] = len(temporada["episodes"])
        if temporada["air_date"]:
            date = temporada["air_date"].split("-")
            ret_dic["temporada_air_date"] = date[2] + "/" + date[1] + "/" + date[0]
        else:
            ret_dic["temporada_air_date"] = ""
        if temporada["poster_path"]:
            ret_dic["temporada_poster"] = 'https://image.tmdb.org/t/p/original' + temporada["poster_path"]
        else:
            ret_dic["temporada_poster"] = ""
        dic_aux = temporada.get('credits', {})
        ret_dic["temporada_cast"] = dic_aux.get('cast', [])
        ret_dic["temporada_crew"] = dic_aux.get('crew', [])
        if capitulo == -1:
            # If we only look for season data, include the technical team that has intervened in any chapter
            dic_aux = dict((i['id'], i) for i in ret_dic["temporada_crew"])
            for e in temporada["episodes"]:
                for crew in e['crew']:
                    if crew['id'] not in list(dic_aux.keys()):
                        dic_aux[crew['id']] = crew
            ret_dic["temporada_crew"] = list(dic_aux.values())

        # Obtain chapter data if applicable
        if capitulo != -1:
            episodio = temporada["episodes"][capitulo - 1]
            ret_dic["episodio_titulo"] = episodio.get("name", "")
            ret_dic["episodio_sinopsis"] = episodio["overview"]
            if episodio["air_date"]:
                date = episodio["air_date"].split("-")
                ret_dic["episodio_air_date"] = date[2] + "/" + date[1] + "/" + date[0]
            else:
                ret_dic["episodio_air_date"] = ""
            ret_dic["episodio_crew"] = episodio["crew"]
            ret_dic["episodio_guest_stars"] = episodio["guest_stars"]
            ret_dic["episodio_vote_count"] = episodio["vote_count"]
            ret_dic["episodio_vote_average"] = episodio["vote_average"]
            if episodio["still_path"]:
                ret_dic["episodio_imagen"] = 'https://image.tmdb.org/t/p/original' + episodio["still_path"]
            else:
                ret_dic["episodio_imagen"] = ""

        return ret_dic

    def get_list_episodes(self):
        url = 'https://api.themoviedb.org/3/tv/{id}?api_key=a1ab8b8669da03637a4b98fa39c39228&language={lang}'.format(id=self.busqueda_id, lang=self.busqueda_idioma)
        results = requests.get(url).json().get('seasons', [])
        return results if 'Error' not in results else []

    def get_videos(self):
        """
        :return: Returns an ordered list (language / resolution / type) of Dict objects in which each of its elements corresponds to a trailer, teaser or clip from youtube.
        :rtype: list of Dict
        """
        ret = []
        if self.result['id']:
            if self.result['videos']:
                self.result["videos"] = self.result["videos"]['results']
            else:
                # First video search in the search language
                url = "http://api.themoviedb.org/3/%s/%s/videos?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s" \
                      % (self.busqueda_tipo, self.result['id'], self.busqueda_idioma)

                dict_videos = self.get_json(url)
                if not isinstance(dict_videos, dict):
                    dict_videos = ast.literal_eval(dict_videos.decode('utf-8'))

                if dict_videos['results']:
                    dict_videos['results'] = sorted(dict_videos['results'], key=lambda x: (x['type'], x['size']))
                    self.result["videos"] = dict_videos['results']

            # If the search language is not English, do a second video search in English
            if self.busqueda_idioma != 'en':
                url = "http://api.themoviedb.org/3/%s/%s/videos?api_key=a1ab8b8669da03637a4b98fa39c39228" % (self.busqueda_tipo, self.result['id'])

                dict_videos = self.get_json(url)
                if not isinstance(dict_videos, dict):
                    dict_videos = ast.literal_eval(dict_videos.decode('utf-8'))

                if dict_videos['results']:
                    dict_videos['results'] = sorted(dict_videos['results'], key=lambda x: (x['type'], x['size']))
                    self.result["videos"].extend(dict_videos['results'])

            # If the searches have obtained results, return a list of objects
            for i in self.result['videos']:
                if i['site'] == "YouTube":
                    ret.append({'name': i['name'],
                                'url': "https://www.youtube.com/watch?v=%s" % i['key'],
                                'size': str(i['size']),
                                'type': i['type'],
                                'language': i['iso_639_1']})

        return ret

    def get_infoLabels(self, infoLabels=None, origen=None):
        """
        :param infoLabels: Extra information about the movie, series, season or chapter.
        :type infoLabels: Dict
        :param origen: Source dictionary where the infoLabels are obtained, by default self.result
        :type origen: Dict
        :return: Returns the extra information obtained from the current object. If the infoLables parameter was passed, the returned value will be read as a duly updated parameter.
        :rtype: Dict
        """

        if infoLabels:
            ret_infoLabels = InfoLabels(infoLabels)
        else:
            ret_infoLabels = InfoLabels()

        # Start Listings
        l_country = [i.strip() for i in ret_infoLabels['country'].split(',') if ret_infoLabels['country']]
        l_director = [i.strip() for i in ret_infoLabels['director'].split(',') if ret_infoLabels['director']]
        l_writer = [i.strip() for i in ret_infoLabels['writer'].split(',') if ret_infoLabels['writer']]
        l_castandrole = ret_infoLabels.get('castandrole', [])

        if not origen:
            origen = self.result

        if 'credits' in list(origen.keys()):
            dic_origen_credits = origen['credits']
            origen['credits_cast'] = dic_origen_credits.get('cast', [])
            origen['credits_crew'] = dic_origen_credits.get('crew', [])
            del origen['credits']

        items = list(origen.items())

        # Season / episode information
        if ret_infoLabels['season'] and self.temporada.get(ret_infoLabels['season']):
            # If there is data loaded for the indicated season
            episodio = -1
            if ret_infoLabels['episode']:
                episodio = ret_infoLabels['episode']

            items.extend(list(self.get_episodio(ret_infoLabels['season'], episodio).items()))

        # logger.debug("ret_infoLabels" % ret_infoLabels)

        for k, v in items:
            if not v:
                continue
            elif isinstance(v, str):
                v = re.sub(r"\n|\r|\t", "", v)
                # fix
                if v == "None":
                    continue

            if k == 'overview':
                if origen:
                    ret_infoLabels['plot'] = v
                else:
                    ret_infoLabels['plot'] = self.get_sinopsis()

            elif k == 'runtime':                                # Duration for movies
                ret_infoLabels['duration'] = int(v) * 60

            elif k == 'episode_run_time':                       # Duration for episodes
                try:
                    for v_alt in v:                             # It comes as a list (?!)
                        ret_infoLabels['duration'] = int(v_alt) * 60
                except:
                    pass

            elif k == 'release_date':
                ret_infoLabels['year'] = int(v[:4])
                ret_infoLabels['release_date'] = v.split("-")[2] + "/" + v.split("-")[1] + "/" + v.split("-")[0]

            elif k == 'first_air_date':
                ret_infoLabels['year'] = int(v[:4])
                ret_infoLabels['aired'] = v.split("-")[2] + "/" + v.split("-")[1] + "/" + v.split("-")[0]
                ret_infoLabels['premiered'] = ret_infoLabels['aired']

            elif k == 'original_title' or k == 'original_name':
                ret_infoLabels['originaltitle'] = v

            elif k == 'vote_average':
                ret_infoLabels['rating'] = float(v)

            elif k == 'vote_count':
                ret_infoLabels['votes'] = v

            elif k == 'poster_path':
                ret_infoLabels['thumbnail'] = 'https://image.tmdb.org/t/p/original' + v

            elif k == 'backdrop_path':
                ret_infoLabels['fanart'] = 'https://image.tmdb.org/t/p/original' + v

            elif k == 'id':
                ret_infoLabels['tmdb_id'] = v

            elif k == 'imdb_id':
                ret_infoLabels['imdb_id'] = v

            elif k == 'external_ids':
                if 'tvdb_id' in v:
                    ret_infoLabels['tvdb_id'] = v['tvdb_id']
                if 'imdb_id' in v:
                    ret_infoLabels['imdb_id'] = v['imdb_id']

            elif k in ['genres', "genre_ids", "genre"]:
                ret_infoLabels['genre'] = self.get_generos(origen)

            elif k == 'name' or k == 'title':
                ret_infoLabels['title'] = v

            elif k == 'production_companies':
                ret_infoLabels['studio'] = ", ".join(i['name'] for i in v)

            elif k == 'credits_cast' or k == 'temporada_cast' or k == 'episodio_guest_stars':
                dic_aux = dict((name, character) for (name, character) in l_castandrole)
                l_castandrole.extend([(p['name'], p.get('character', '') or p.get('character_name', '')) \
                                      for p in v if p['name'] not in list(dic_aux.keys())])

            elif k == 'videos':
                if not isinstance(v, list):
                    v = v.get('result', [])
                for i in v:
                    if i.get("site", "") == "YouTube":
                        ret_infoLabels['trailer'] = "https://www.youtube.com/watch?v=" + v[0]["key"]
                        break

            elif k == 'production_countries' or k == 'origin_country':
                if isinstance(v, str):
                    l_country = list(set(l_country + v.split(',')))

                elif isinstance(v, list) and len(v) > 0:
                    if isinstance(v[0], str):
                        l_country = list(set(l_country + v))
                    elif isinstance(v[0], dict):
                        # {'iso_3166_1': 'FR', 'name':'France'}
                        for i in v:
                            if 'iso_3166_1' in i:
                                pais = Tmdb.dic_country.get(i['iso_3166_1'], i['iso_3166_1'])
                                l_country = list(set(l_country + [pais]))

            elif k == 'credits_crew' or k == 'episodio_crew' or k == 'temporada_crew':
                for crew in v:
                    if crew['job'].lower() == 'director':
                        l_director = list(set(l_director + [crew['name']]))

                    elif crew['job'].lower() in ('screenplay', 'writer'):
                        l_writer = list(set(l_writer + [crew['name']]))

            elif k == 'created_by':
                for crew in v:
                    l_writer = list(set(l_writer + [crew['name']]))

            elif isinstance(v, str) or isinstance(v, int) or isinstance(v, float):
                ret_infoLabels[k] = v

            else:
                # logger.debug("Atributos no añadidos: " + k +'= '+ str(v))
                pass

        # Sort the lists and convert them to str if necessary
        if l_castandrole:
            ret_infoLabels['castandrole'] = sorted(l_castandrole, key=lambda tup: tup[0])
        if l_country:
            ret_infoLabels['country'] = ', '.join(sorted(l_country))
        if l_director:
            ret_infoLabels['director'] = ', '.join(sorted(l_director))
        if l_writer:
            ret_infoLabels['writer'] = ', '.join(sorted(l_writer))

        return ret_infoLabels
